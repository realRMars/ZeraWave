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
SPEEDS=(1.,2.,4.,6.,12.)


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

    def rewind(self):self.seek(0.)

    def seek(self, seconds):
        if type(seconds) not in (int,float) or not np.isfinite(seconds) or not 0<=seconds<=self.duration:
            raise ValueError('Seek position is outside the audio file.')
        position=min(int(np.ceil(self.frames*RATE/self.rate)),round(seconds*RATE))
        self.position(min(self.frames,int(position*self.rate/RATE)))
        self.output_index=position

    def position(self, frame):
        if self.soundfile:self.handle.seek(frame)
        else:self.handle.setpos(frame)
        self.buffer=np.empty((0,2),dtype=np.float32);self.base=frame;self.eof=False

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

    def read(self, speed=1.):
        if type(speed) not in (int,float) or abs(speed) not in SPEEDS:raise ValueError('Unsupported audio playback speed.')
        total=int(np.ceil(self.frames*RATE/self.rate));step=abs(speed)
        remaining=total-self.output_index if speed>0 else self.output_index
        count=min(BLOCK,int(np.ceil(remaining/step)))
        if count<=0:return np.empty((0,2),dtype=np.float32)
        canonical=self.output_index+np.arange(count)*step if speed>0 else self.output_index-(np.arange(count)+1)*step
        positions=np.maximum(0.,canonical)*self.rate/RATE
        low=min(self.frames-1,int(positions.min()));need=min(self.frames,int(positions.max())+2)
        # Reverse/seek reads are bounded source slabs; normal forward conversion
        # retains the previous block neighbour exactly as before.
        if low<self.base or low>self.base+len(self.buffer):self.position(low)
        while self.base+len(self.buffer)<need and not self.eof:
            raw=self.raw(BLOCK)
            if not len(raw):self.eof=True;break
            if self.channels==1:raw=np.repeat(raw,2,axis=1)
            if not np.isfinite(raw).all():raise ValueError('Decoded audio contains nonfinite samples.')
            self.buffer=np.concatenate((self.buffer,raw.astype(np.float32)),axis=0)
        if not len(self.buffer):return np.empty((0,2),dtype=np.float32)
        grid=self.base+np.arange(len(self.buffer))
        pcm=np.column_stack([np.interp(positions,grid,self.buffer[:,c]) for c in range(2)]).astype(np.float32)
        self.output_index=max(0.,min(total,self.output_index+count*speed))
        if speed>0:
            discard=max(0,min(len(self.buffer)-1,int(self.output_index*self.rate/RATE)-self.base))
            self.buffer=self.buffer[discard:];self.base+=discard
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
        self.latest_seek_id=None;self.commands = queue.Queue(32);self.packets = deque(maxlen=8);self.peaks = deque(maxlen=256)
        self.analyzer_enabled=False;self.analyzer_at=-1.;self.analyzer_packet=None;self.analyzer_error=''
        from band_display import AnalyzerSpectrum
        self.analyzer_spectrum=AnalyzerSpectrum()
        self.state = dict(mode=MODES[0], device=None, path='', status='Stopped', error='',
            playing=False, speed=1., file_revision=0,last_seek_id=None, repeat=False, mute=False, volume=1., raw_waveform=False, drive_revision=0, playhead=0., duration=None,
            generation=0, sequence=0, pcm_frames=0, pcm_wall=None, rms=None, peak=None, source_clipped=0, output_rms=None, output_peak=None, output_clipped=0, dropped=0,
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
                stale=self.state['pcm_wall'] is None or time.perf_counter() - self.state['pcm_wall'] > 1.5,
                band_analyzer=self.analyzer_packet,analyzer_enabled=self.analyzer_enabled,analyzer_error=self.analyzer_error)

    def analyzer_snapshot(self):
        """Small read-only telemetry projection, never another audio owner."""
        with self.lock:
            return dict(generation=self.state['generation'],playing=self.state['playing'],status=self.state['status'],
                band_analyzer=self.analyzer_packet,analyzer_enabled=self.analyzer_enabled,analyzer_error=self.analyzer_error)

    def submit(self, op, **values):
        if self.closed.is_set():raise ValueError('Audio owner is closed.')
        if not self.worker.is_alive():raise ValueError('Audio worker is unavailable; restart Studio. '+self.state['error'])
        if op not in ('source', 'device', 'open', 'play', 'pause', 'stop', 'repeat', 'mute', 'refresh', 'volume', 'raw_waveform', 'seek', 'speed', 'analyzer'):
            raise ValueError('Unsupported audio action.')
        if op == 'source' and values.get('value') not in MODES:raise ValueError('Unknown audio source.')
        if op in ('seek','speed') and 'file_revision' in values and (type(values['file_revision']) is not int or values['file_revision']<0):raise ValueError('Invalid audio file identity.')
        if op=='seek' and 'seek_id' in values and (not isinstance(values['seek_id'],str) or not 1<=len(values['seek_id'])<=64):raise ValueError('Invalid seek identity.')
        if op=='seek' and (type(values.get('seconds')) not in (int,float) or not np.isfinite(values['seconds']) or values['seconds']<0):raise ValueError('Invalid audio seek position.')
        if op=='speed' and (type(values.get('value')) not in (int,float) or abs(values['value']) not in SPEEDS):raise ValueError('Choose 1×, 2×, 4×, 6× or 12× playback.')
        if op=='speed' and 'play' in values and type(values['play']) is not bool:raise ValueError('Invalid playback state.')
        if op == 'volume' and (type(values.get('value')) not in (int,float) or not np.isfinite(values['value']) or not 0<=values['value']<=1):raise ValueError('Output volume must be 0..100%.')
        if op in ('repeat', 'mute', 'raw_waveform', 'analyzer') and type(values.get('value')) is not bool:raise ValueError('Expected an explicit audio switch state.')
        if op == 'device':
            device = values.get('value')
            if device not in self.snapshot()['devices']:raise ValueError('Listening device is no longer available. Refresh devices.')
        with self.lock:
            try:self.commands.put_nowait((op,values))
            except queue.Full:raise ValueError('Audio controls are busy; try again.')
            if op=='seek' and values.get('seek_id'):self.latest_seek_id=values['seek_id']
            elif op in ('stop','open','source','device'):self.latest_seek_id=None
            self.state['pending']=True

    def change(self, **values):
        with self.lock:self.state.update(values)

    def boundary(self,hold_analyzer=False):
        with self.lock:
            self.state['generation'] += 1;self.packets.clear();self.peaks.clear();self.state['pcm_wall'] = None
            self.analyzer_packet=(dict(self.analyzer_packet,held=True,
                origin_generation=self.analyzer_packet.get('origin_generation',self.analyzer_packet['generation']),
                generation=self.state['generation']) if hold_analyzer and self.analyzer_packet else None)
            self.analyzer_at=-1.;self.analyzer_error=''
            self.analyzer_spectrum.reset()
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
        self.change(output=False,output_rms=None,output_peak=None,output_clipped=0)

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
            output = stack.enter_context(manager)
            if not self.output_factory:
                from wasapi_output import FrameOutput
                output = FrameOutput(output)
            self.output = output;self.output_stack = stack;self.change(output=True)
        except Exception:
            try:stack.close()
            except Exception as exc:
                self.output_stack=stack;self.output_release_error=exc;self.blocked=True
            raise

    def act(self, op, values):
        if op=='analyzer':
            with self.lock:
                self.analyzer_enabled=values['value'];self.analyzer_packet=None;self.analyzer_at=-1.;self.analyzer_error=''
                self.analyzer_spectrum.reset()
            return
        if op == 'refresh':self.enumerator.request();return
        if op in ('mute', 'repeat', 'volume'):self.change(**{op:values['value']});return
        if op == 'raw_waveform':
            if self.state['raw_waveform'] != values['value']:self.change(raw_waveform=values['value'],drive_revision=self.state['drive_revision']+1)
            return
        if op == 'source' and values['value'] == self.state['mode']:return
        if op == 'device' and values['value'] == self.state['device'] and self.capture is not None and not self.blocked:return
        if self.blocked and op not in ('stop','source','device','open'):
            raise ValueError('Previous audio release is unconfirmed; stop it before playback.')
        if op in ('seek','speed'):
            if self.state['mode']!=MODES[1] or self.decoder is None:raise ValueError('Open an audio file first.')
            if values.get('file_revision',self.state['file_revision'])!=self.state['file_revision']:raise ValueError('Audio file changed; gesture cancelled.')
            if op=='seek' and values.get('seek_id'):
                with self.lock:
                    if values['seek_id']!=self.latest_seek_id:return
            if op=='seek' and not 0<=values['seconds']<=self.decoder.duration:raise ValueError('Seek position is outside the audio file.')
            playing=self.state['playing'] if op=='seek' else values.get('play',self.state['playing'])
            if op=='speed' and self.state['speed']==values['value'] and self.state['playing']==playing:return
            # Flush already submitted native audio on a discontinuity. If close
            # is unconfirmed, existing ownership blocks replacement.
            self.release_output()
            try:
                if op=='seek':
                    self.decoder.seek(values['seconds']);self.change(last_seek_id=values.get('seek_id'))
                else:self.change(speed=float(values['value']))
                self.boundary();self.change(playhead=min(self.decoder.duration,self.decoder.output_index/RATE),playing=False,error='',status='Paused')
                if playing:
                    self.start_output();self.change(playing=True,status='Playing');self.next_file=time.perf_counter()
            except Exception:
                self.change(playing=False,status='Unavailable');raise
            return
        if op in ('source', 'device', 'open'):
            # Validate/open the proposed file before releasing a working source.
            candidate = Decoder(values['path']) if op == 'open' else None
            try:self.release_source()
            except Exception:
                if candidate:candidate.close()
                raise
            self.boundary();self.change(playing=False,speed=1.,file_revision=self.state['file_revision']+1,last_seek_id=None,error='',status='Stopped',playhead=0.)
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
            if self.state['speed']!=1.:
                self.release_output();self.boundary()
            self.start_output();self.change(speed=1.,playing=True, status='Playing', error='');self.next_file = time.perf_counter()
        elif op == 'pause':
            if self.state['mode'] != MODES[1]:raise ValueError('Pause is for Audio File only.')
            self.release_output();self.change(playing=False, status='Paused');self.boundary(hold_analyzer=True)
        elif op == 'stop':
            self.release_output()
            self.stop_capture()
            if self.decoder:self.decoder.rewind()
            self.blocked=False;self.change(speed=1.,playing=False,playhead=0.,status='Stopped',error='');self.boundary()

    def publish(self, pcm, output_metrics=None):
        pcm = np.asarray(pcm, dtype=np.float32)
        if pcm.ndim == 1:pcm = np.repeat(pcm[:, None], 2, axis=1)
        if pcm.shape != (len(pcm), 2) or not 0 < len(pcm) <= BLOCK or not np.isfinite(pcm).all():
            raise ValueError('Invalid PCM from audio source.')
        pcm = np.ascontiguousarray(pcm, dtype='<f4')
        # The view follows PCM block cadence (normally 23.4 Hz), capped at
        # 33 Hz. A short upper and bounded longer bass window live only here.
        now=time.perf_counter();spectrum=None
        if self.analyzer_enabled:self.analyzer_spectrum.append(pcm,RATE)
        if self.analyzer_enabled and now-self.analyzer_at>=.03:
            self.analyzer_at=now
            try:
                spectrum=self.analyzer_spectrum.snapshot()
                spectrum.update(stamp=now,generation=self.state['generation'],sequence=self.state['sequence']+1,playhead=self.state['playhead'])
                self.analyzer_error=''
            except Exception as exc:
                with self.lock:self.analyzer_error=str(exc)[:160];self.analyzer_packet=None
        with self.lock:
            if spectrum is not None:self.analyzer_packet=spectrum
            if output_metrics:self.state.update(output_metrics)
            self.state['pcm_frames'] += len(pcm);self.state['sequence'] += 1;self.state['pcm_wall'] = time.perf_counter()
            self.state['rms'] = float(np.sqrt(np.mean(pcm * pcm)))
            self.state['peak'] = float(np.max(np.abs(pcm)));self.state['source_clipped']=int(np.count_nonzero(np.abs(pcm)>1.))
            if self.state['mode'] == MODES[0]:self.state['playhead'] += len(pcm) / RATE
            self.peaks.extend([[float(g.min()), float(g.max())] for g in np.array_split(pcm, min(32, len(pcm)))])
            meta = self.metadata();meta.update(frames=len(pcm), sequence=self.state['sequence'])
            header = json.dumps(meta, separators=(',', ':')).encode();data = pcm.tobytes()
            if len(self.packets) == self.packets.maxlen:self.state['dropped'] += 1
            self.packets.append(struct.pack('<II', len(header), len(data)) + header + data)
            self.wake.notify_all()

    def metadata(self):
        return {k:self.state[k] for k in ('generation', 'mode', 'device', 'path', 'playhead', 'pcm_frames', 'playing', 'status', 'raw_waveform', 'drive_revision', 'volume', 'mute', 'speed', 'file_revision')}

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
                            pcm = self.decoder.read(self.state['speed'])
                            if not len(pcm):
                                if self.state['repeat']:
                                    self.decoder.seek(0. if self.state['speed']>0 else self.decoder.duration);self.boundary();self.change(playhead=0. if self.state['speed']>0 else self.decoder.duration)
                                else:
                                    if hasattr(self.output,'drain'):self.output.drain()
                                    self.release_output();self.change(playing=False, status='Ended')
                            else:
                                # Output-only gain; original PCM continues to analysis and raw drive.
                                audible=pcm*self.state['volume']
                                clipped=0 if self.state['mute'] else int(np.count_nonzero(np.abs(audible)>1.))
                                audible=np.zeros_like(pcm) if self.state['mute'] else np.clip(audible,-1.,1.)
                                self.output.play(audible)
                                output_metrics=dict(output_rms=float(np.sqrt(np.mean(audible*audible))),output_peak=float(np.max(np.abs(audible))),output_clipped=clipped)
                                self.change(playhead=min(self.decoder.duration, self.decoder.output_index / RATE))
                                self.publish(pcm,output_metrics)
                                self.next_file = time.perf_counter() if getattr(self.output,'paces_audio',False) else max(self.next_file + len(pcm) / RATE, time.perf_counter())
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
        from waveform_drive import WaveformDrive
        self.drive=WaveformDrive();self.drive_revision=-1

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
                result = self.drive.select(self.analyze(pcm),pcm,meta)
                revision=meta.get('drive_revision',0)
                drive_changed=revision!=self.drive_revision;self.drive_revision=revision
                # Preserve analyzer histories across boundaries; discard cross-source
                # onset events on the first frame rather than clearing its history.
                if self.first_frame or drive_changed:
                    result.impact = result.bass_onset = result.mids_onset = result.highs_onset = 0.
                    result.beat_tick = False
                    if meta.get('raw_waveform'):result.rhythmic_activity=0.
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
            frames = [row for row in self.frames if row[1][1].audio_source['generation']==self.generation and row[1][1].audio_source.get('drive_revision',0)==self.latest.get('drive_revision',0)]
            self.frames.clear();return frames

    def stop(self):
        self.stop_event.set()
        if self.sock:
            try:self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        if self.worker:
            self.worker.join(2.5)
            if self.worker.is_alive():raise RuntimeError('PCM analysis close pending.')
