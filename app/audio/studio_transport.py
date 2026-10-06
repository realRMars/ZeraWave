"""Studio's single audio owner. Captured input is never sent to an output.

Files and listening share a bounded 48 kHz stereo PCM bus. File output and
renderer analysis consume that PCM; the visual clock never drives this owner.
No device or stream opens merely by importing this module or opening Studio.
"""
from collections import deque
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import queue
import socket
import struct
import threading
import time
import uuid
import wave
import numpy as np

RATE = 48000
BLOCK = 2048
MODES = ('Device Listening', 'Audio File')


class Decoder:
    """Bounded block reader, canonical stereo PCM with continuous resampling.

The linear sample-rate conversion retains its neighbour across block borders;
no independent decoding clock or whole-song sample array is retained.
"""
    def __init__(self, path):
        self.path = str(Path(path).resolve())
        if not Path(self.path).is_file():raise ValueError('Audio file does not exist.')
        extension = Path(self.path).suffix.lower()
        if extension not in ('.wav', '.mp3'):raise ValueError('Choose a WAV or MP3 file.')
        self.handle = None
        try:
            if importlib.util.find_spec('soundfile'):
                import soundfile
                self.handle = soundfile.SoundFile(self.path, mode='r')
                self.rate, self.channels, self.frames = self.handle.samplerate, self.handle.channels, len(self.handle)
                self.soundfile = True
            else:
                if extension == '.mp3':raise ValueError('MP3 decoding unavailable; SoundFile is not installed.')
                self.handle = wave.open(self.path, 'rb')
                self.rate, self.channels, self.frames = self.handle.getframerate(), self.handle.getnchannels(), self.handle.getnframes()
                self.width = self.handle.getsampwidth();self.soundfile = False
                if self.width not in (1, 2, 3, 4):raise ValueError('Unsupported PCM WAV sample width.')
            if not 8000 <= self.rate <= 192000 or self.channels not in (1, 2) or self.frames <= 0:
                raise ValueError('Audio must be nonempty mono/stereo, 8–192 kHz.')
            self.duration = self.frames / self.rate
            self.rewind()
        except Exception:
            self.close();raise

    def rewind(self):
        if self.soundfile:self.handle.seek(0)
        else:self.handle.rewind()
        self.buffer = np.empty((0, 2), dtype=np.float32)
        self.base = self.output_index = 0;self.eof = False

    def raw(self, count):
        if self.soundfile:return self.handle.read(count, dtype='float32', always_2d=True)
        data = self.handle.readframes(count)
        if self.width == 1:pcm = (np.frombuffer(data, np.uint8).astype(np.float32) - 128) / 128
        elif self.width == 2:pcm = np.frombuffer(data, '<i2').astype(np.float32) / 32768
        elif self.width == 4:pcm = np.frombuffer(data, '<i4').astype(np.float32) / 2147483648
        else:
            b = np.frombuffer(data, np.uint8).reshape(-1, 3).astype(np.int32)
            n = b[:, 0] | b[:, 1] << 8 | b[:, 2] << 16
            pcm = ((n ^ 0x800000) - 0x800000).astype(np.float32) / 8388608
        return pcm.reshape(-1, self.channels)

    def read(self):
        total = int(np.ceil(self.frames * RATE / self.rate))
        count = min(BLOCK, total - self.output_index)
        if count <= 0:return np.empty((0, 2), dtype=np.float32)
        positions = (self.output_index + np.arange(count)) * self.rate / RATE
        need = min(self.frames, int(positions[-1]) + 2)
        while self.base + len(self.buffer) < need and not self.eof:
            raw = self.raw(BLOCK)
            if not len(raw):self.eof = True;break
            if self.channels == 1:raw = np.repeat(raw, 2, axis=1)
            if not np.isfinite(raw).all():raise ValueError('Decoded audio contains nonfinite samples.')
            self.buffer = np.concatenate((self.buffer, raw.astype(np.float32)), axis=0)
        if not len(self.buffer):return np.empty((0, 2), dtype=np.float32)
        grid = self.base + np.arange(len(self.buffer))
        pcm = np.column_stack([np.interp(positions, grid, self.buffer[:, c]) for c in range(2)]).astype(np.float32)
        self.output_index += count
        discard = max(0, min(len(self.buffer) - 1, int(self.output_index * self.rate / RATE) - self.base))
        self.buffer = self.buffer[discard:];self.base += discard
        return pcm

    def close(self):
        if self.handle is not None:self.handle.close();self.handle = None


def receive(sock, count):
    data = bytearray()
    while len(data) < count:
        part = sock.recv(count - len(data))
        if not part:raise EOFError('Audio owner disconnected.')
        data.extend(part)
    return bytes(data)


class AudioOwner:
    def __init__(self, capture_factory=None, output_factory=None, enumerator=None):
        from capture import SourceEnumerator
        self.capture_factory = capture_factory;self.output_factory = output_factory
        self.enumerator = enumerator or SourceEnumerator(poll_seconds=5.)
        self.enumerator.request()
        self.lock = threading.RLock();self.wake = threading.Condition(self.lock)
        self.commands = queue.Queue(32);self.packets = deque(maxlen=8);self.peaks = deque(maxlen=256)
        self.state = dict(mode=MODES[0], device=None, path='', status='Stopped', error='',
            playing=False, repeat=False, mute=False, playhead=0., duration=None,
            generation=0, sequence=0, pcm_frames=0, pcm_wall=None, rms=None, dropped=0,
            output=False, pending=False, decoder='SoundFile' if importlib.util.find_spec('soundfile') else 'PCM WAV only')
        self.capture = self.decoder = self.output = self.output_stack = None;self.blocked = False
        self.output_release_error = None
        self.closed = threading.Event();self.token = uuid.uuid4().hex
        self.listener = socket.socket();self.listener.bind(('127.0.0.1', 0));self.listener.listen(1);self.listener.settimeout(.2)
        self.address = self.listener.getsockname();self.client = None
        self.worker = threading.Thread(target=self.run, name='Studio audio owner', daemon=True)
        self.server = threading.Thread(target=self.serve, name='Studio PCM handoff', daemon=True)
        self.worker.start();self.server.start()

    def environment(self):return json.dumps(dict(port=self.address[1], token=self.token))

    def snapshot(self):
        enumeration = self.enumerator.snapshot() or {}
        with self.lock:
            return dict(self.state, devices=enumeration.get('sources', []), device_error=enumeration.get('error'),
                waveform=list(self.peaks), session_seconds=self.state['pcm_frames'] / RATE,
                stale=self.state['pcm_wall'] is None or time.perf_counter() - self.state['pcm_wall'] > 1.5)

    def submit(self, op, **values):
        if self.closed.is_set():raise ValueError('Audio owner is closed.')
        if not self.worker.is_alive():raise ValueError('Audio worker is unavailable; restart Studio. '+self.state['error'])
        if op not in ('source', 'device', 'open', 'play', 'pause', 'stop', 'repeat', 'mute', 'refresh'):
            raise ValueError('Unsupported audio action.')
        if op == 'source' and values.get('value') not in MODES:raise ValueError('Unknown audio source.')
        if op in ('repeat', 'mute') and type(values.get('value')) is not bool:raise ValueError('Expected an explicit audio switch state.')
        if op == 'device':
            device = values.get('value')
            if device not in self.snapshot()['devices']:raise ValueError('Listening device is no longer available. Refresh devices.')
        try:self.commands.put_nowait((op, values))
        except queue.Full:raise ValueError('Audio controls are busy; try again.')
        with self.lock:self.state['pending'] = True

    def change(self, **values):
        with self.lock:self.state.update(values)

    def boundary(self):
        with self.lock:
            self.state['generation'] += 1;self.packets.clear();self.peaks.clear();self.state['pcm_wall'] = None
            self.wake.notify_all()

    def release_output(self):
        if self.output_release_error is not None:
            raise RuntimeError('Output release unconfirmed; restart Studio: ' + str(self.output_release_error))
        if self.output_stack is not None:
            # Clear ownership only after the backend confirms its context exit.
            try:self.output_stack.close()
            except Exception as exc:
                self.output_release_error=exc;self.blocked=True;self.change(playing=False,status='Release unconfirmed');raise
            self.output_stack = self.output = None
        self.change(output=False)

    def stop_capture(self):
        if self.capture is not None:
            try:self.capture.stop()
            except Exception:
                self.blocked=True;self.change(playing=False,status='Release unconfirmed');raise
            self.capture = None

    def release_source(self):
        error = None
        try:self.release_output()
        except Exception as exc:error = exc
        try:self.stop_capture()
        except Exception as exc:error = error or exc
        if self.decoder is not None:
            try:self.decoder.close();self.decoder = None
            except Exception as exc:error = error or exc
        if error:raise error
        self.blocked = False

    def start_capture(self):
        from capture import AudioCapture
        from capture_stream import CaptureStream
        device = self.state['device']
        if not device:raise ValueError('Select a listening device to begin analysis-only capture.')
        cap = self.capture_factory(device) if self.capture_factory else AudioCapture(
            device_name=device['id'], source_kind=device['kind'], exact_id=True, owner_generation=self.state['generation'])
        self.capture = CaptureStream(cap, lambda pcm:pcm, capacity=8, generation=self.state['generation'])
        self.capture.start();self.change(playing=True, status='Listening • analysis only')

    def start_output(self):
        if self.output is not None:return
        stack = ExitStack()
        try:
            if self.output_factory:manager = self.output_factory()
            else:
                import soundcard
                speaker = soundcard.default_speaker()
                if speaker is None:raise ValueError('No audio output device is available.')
                manager = speaker.player(samplerate=RATE, channels=2, blocksize=BLOCK)
            self.output = stack.enter_context(manager);self.output_stack = stack;self.change(output=True)
        except Exception:stack.close();raise

    def act(self, op, values):
        if op == 'refresh':self.enumerator.request();return
        if op in ('mute', 'repeat'):self.change(**{op:values['value']});return
        if op == 'source' and values['value'] == self.state['mode']:return
        if op == 'device' and values['value'] == self.state['device'] and self.capture is not None and not self.blocked:return
        if self.blocked and op not in ('stop','source','device','open'):
            raise ValueError('Previous audio release is unconfirmed; stop it before playback.')
        if op in ('source', 'device', 'open'):
            # Validate/open the proposed file before releasing a working source.
            candidate = Decoder(values['path']) if op == 'open' else None
            try:self.release_source()
            except Exception:
                if candidate:candidate.close()
                raise
            self.boundary();self.change(playing=False, error='', status='Stopped', playhead=0.)
            if op == 'open':
                self.decoder = candidate
                self.change(mode=MODES[1], path=candidate.path, duration=candidate.duration, status='Ready')
            elif op == 'device':
                self.change(mode=MODES[0], device=values['value']);self.start_capture()
            else:
                self.change(mode=values['value'])
                if self.state['mode'] == MODES[0] and self.state['device']:self.start_capture()
                elif self.state['mode'] == MODES[1] and self.state['path']:
                    self.decoder = Decoder(self.state['path']);self.change(duration=self.decoder.duration, status='Ready')
        elif op == 'play':
            if self.state['mode'] != MODES[1]:raise ValueError('Play is for Audio File only.')
            if not self.decoder:raise ValueError('Open an audio file first.')
            if self.decoder.output_index >= int(np.ceil(self.decoder.frames * RATE / self.decoder.rate)):
                self.decoder.rewind();self.boundary();self.change(playhead=0.)
            self.start_output();self.change(playing=True, status='Playing', error='');self.next_file = time.perf_counter()
        elif op == 'pause':
            if self.state['mode'] != MODES[1]:raise ValueError('Pause is for Audio File only.')
            self.release_output();self.change(playing=False, status='Paused');self.boundary()
        elif op == 'stop':
            self.release_output()
            self.stop_capture()
            if self.decoder:self.decoder.rewind()
            self.blocked=False;self.change(playing=False, playhead=0., status='Stopped', error='');self.boundary()

    def publish(self, pcm):
        pcm = np.asarray(pcm, dtype=np.float32)
        if pcm.ndim == 1:pcm = np.repeat(pcm[:, None], 2, axis=1)
        if pcm.shape != (len(pcm), 2) or not 0 < len(pcm) <= BLOCK or not np.isfinite(pcm).all():
            raise ValueError('Invalid PCM from audio source.')
        pcm = np.ascontiguousarray(pcm, dtype='<f4')
        with self.lock:
            self.state['pcm_frames'] += len(pcm);self.state['sequence'] += 1;self.state['pcm_wall'] = time.perf_counter()
            self.state['rms'] = float(np.sqrt(np.mean(pcm * pcm)))
            if self.state['mode'] == MODES[0]:self.state['playhead'] += len(pcm) / RATE
            self.peaks.extend([[float(g.min()), float(g.max())] for g in np.array_split(pcm, min(32, len(pcm)))])
            meta = self.metadata();meta.update(frames=len(pcm), sequence=self.state['sequence'])
            header = json.dumps(meta, separators=(',', ':')).encode();data = pcm.tobytes()
            if len(self.packets) == self.packets.maxlen:self.state['dropped'] += 1
            self.packets.append(struct.pack('<II', len(header), len(data)) + header + data)
            self.wake.notify_all()

    def metadata(self):
        return {k:self.state[k] for k in ('generation', 'mode', 'device', 'path', 'playhead', 'pcm_frames', 'playing', 'status')}

    def run(self):
        from capture import backend_thread
        try:
            with backend_thread():
                while not self.closed.is_set():
                    try:
                        for _ in range(8):
                            try:op, values = self.commands.get_nowait()
                            except queue.Empty:break
                            try:self.act(op, values)
                            except Exception as exc:
                                # Invalid imports/selections must leave the last
                                # working source intact. Backend close failures
                                # retain ownership and therefore block replacement.
                                self.change(error=str(exc)[:240])
                        self.change(pending=not self.commands.empty())
                        if self.capture and not self.blocked:
                            for stamp, pcm in self.capture.drain():self.publish(pcm)
                            health = self.capture.health()
                            if health['last_packet_at'] is None and time.perf_counter() - health['started_at'] > 5.:
                                raise ValueError('Listening device did not deliver PCM within five seconds.')
                            if health['last_packet_at'] is not None and time.perf_counter() - health['last_packet_at'] > 2.:
                                raise ValueError('Listening device stopped delivering PCM.')
                        elif self.decoder and not self.blocked and self.state['playing'] and time.perf_counter() >= self.next_file:
                            pcm = self.decoder.read()
                            if not len(pcm):
                                if self.state['repeat']:
                                    self.decoder.rewind();self.boundary();self.change(playhead=0.)
                                else:
                                    self.release_output();self.change(playing=False, status='Ended')
                            else:
                                # Modest fixed output gain; mute never modifies analysis PCM.
                                self.output.play(np.zeros_like(pcm) if self.state['mute'] else np.clip(pcm * .2, -1., 1.))
                                self.change(playhead=min(self.decoder.duration, self.decoder.output_index / RATE))
                                self.publish(pcm)
                                self.next_file = max(self.next_file + len(pcm) / RATE, time.perf_counter())
                    except Exception as exc:
                        self.boundary();self.change(playing=False, pending=False, status='Unavailable', error=str(exc)[:240])
                        try:self.release_source()
                        except Exception as release:
                            self.blocked=True;self.change(error=('Audio release unconfirmed; replacement blocked: ' + str(release))[:240])
                    delay = .01 if self.capture else .02
                    if self.decoder and self.state['playing'] and not self.blocked:
                        delay = max(0., min(.02, self.next_file - time.perf_counter()))
                    self.closed.wait(delay)
        except Exception as exc:self.change(status='Unavailable', error=str(exc)[:240])
        finally:
            try:self.release_source()
            except Exception as exc:self.change(error='Audio release unconfirmed: ' + str(exc)[:180])

    def serve(self):
        while not self.closed.is_set():
            try:
                client, _ = self.listener.accept();client.settimeout(.5)
            except (socket.timeout, OSError):continue
            try:
                if receive(client, 32).decode() != self.token:continue
                with self.lock:self.client = client;self.packets.clear()
                while not self.closed.is_set():
                    with self.wake:
                        if not self.packets:self.wake.wait(.1)
                        if self.packets:packet = self.packets.popleft()
                        else:
                            header = json.dumps(dict(self.metadata(), frames=0)).encode()
                            packet = struct.pack('<II', len(header), 0) + header
                    client.sendall(packet)
            except (OSError, EOFError, UnicodeError):pass
            finally:
                client.close()
                with self.lock:self.client = None

    def close(self):
        self.closed.set();self.enumerator.close();self.listener.close()
        with self.wake:
            self.wake.notify_all()
            if self.client:
                try:self.client.shutdown(socket.SHUT_RDWR)
                except OSError:pass
        self.worker.join(3.);self.server.join(1.)
        if self.worker.is_alive():raise RuntimeError('Audio cleanup pending; replacement owner must not start.')
        if self.capture is not None or self.output_stack is not None:raise RuntimeError('Audio resource release was not confirmed.')


class HubStream:
    """One renderer consumer; bounded analysis mailbox, never a device owner."""
    def __init__(self, environment, analyze):
        self.endpoint = json.loads(environment);self.analyze = analyze
        self.lock = threading.Lock();self.frames = deque(maxlen=8)
        self.stop_event = threading.Event();self.error = None;self.latest = {};self.generation = -1
        self.worker = self.sock = None
        self.first_frame = True

    def start(self):
        self.worker = threading.Thread(target=self.run, name='Studio PCM analysis', daemon=True);self.worker.start()

    def run(self):
        try:
            self.sock = socket.create_connection(('127.0.0.1', int(self.endpoint['port'])), timeout=2.)
            self.sock.settimeout(2.);self.sock.sendall(self.endpoint['token'].encode())
            while not self.stop_event.is_set():
                size, count = struct.unpack('<II', receive(self.sock, 8))
                if not 0 < size <= 16384 or not 0 <= count <= BLOCK * 8:raise ValueError('Invalid PCM bus packet size.')
                meta = json.loads(receive(self.sock, size));data = receive(self.sock, count) if count else b''
                with self.lock:
                    if meta['generation'] < self.generation:continue
                    changed = meta['generation'] != self.generation
                    if changed:self.generation = meta['generation'];self.frames.clear();self.first_frame = True
                    self.latest = meta
                if not count:continue
                if count != meta['frames'] * 8:raise ValueError('Invalid PCM bus frame count.')
                pcm = np.frombuffer(data, '<f4').reshape(-1, 2).copy()
                result = self.analyze(pcm)
                # Preserve analyzer histories across boundaries; discard cross-source
                # onset events on the first frame rather than clearing its history.
                if self.first_frame:
                    result.impact = result.bass_onset = result.mids_onset = result.highs_onset = 0.
                    result.beat_tick = False
                    self.first_frame = False
                result.audio_source = dict(meta)
                with self.lock:self.frames.append((time.perf_counter(), (pcm, result)))
        except Exception as exc:
            if not self.stop_event.is_set():self.error = exc
        finally:
            if self.sock:self.sock.close()

    def drain(self):
        if self.error:raise RuntimeError('Studio audio handoff failed: ' + str(self.error)) from self.error
        with self.lock:
            frames = [row for row in self.frames if row[1][1].audio_source['generation']==self.generation]
            self.frames.clear();return frames

    def stop(self):
        self.stop_event.set()
        if self.sock:
            try:self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        if self.worker:
            self.worker.join(2.5)
            if self.worker.is_alive():raise RuntimeError('PCM analysis close pending.')
