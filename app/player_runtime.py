"""Owned free-player live loop using the existing renderer and audio analysis."""
from collections import deque
import json
import math
import os
import queue
import sys
import threading
import time

from player_state import Playback, validate_config
from live_visual_test import (AudioAnalyzer, AudioCapture, OnsetDetector,
                              SignalProcessor, VisualSignalConditioner, analyze_samples)
from capture_stream import CaptureStream
from capture import list_sources, SourceEnumerator, backend_thread
from wasapi_cleanup import WasapiCleanup, BACKEND_SHA256
from player_log import source_binding
from pathlib import Path
from parameter_mapper import VisualParameterMapper
from renderer import Renderer, LIVE_FORMS
from world_catalog import main_entries
import glfw

PREFIX = 'ZERAWAVE_PLAYER '
RESTART_NOTICE = ('Capture could not restart. Close this ZeraWave player completely (player panel and visual output), '
                  'then reopen it and reselect your audio source. A closed window alone does not confirm native release.')


def command_summary(value):
    return {k: value[k] for k in ('op', 'serial', 'source', 'owner', 'active', 'mode') if k in value}


def capture_controls(state):
    return {k: state.get(k) for k in ('running', 'listen_requested', 'listening', 'paused', 'held', 'generation',
            'capture_state', 'capture_owner', 'owner_health', 'waiting_for_fresh', 'source', 'active_source', 'restart_notice')}


def emit(**value):
    if 'error' in value:
        print('PLAYER ERROR: ' + str(value['error']), file=sys.stderr, flush=True)
    print(PREFIX + json.dumps(value), flush=True)


def dispatch_control(session, value):
    """The runtime's actual bounded, serial-correlated command/ACK path."""
    before = capture_controls(session.snapshot())
    session.command(value)
    after = session.snapshot()
    emit(ack=value.get('serial'), state=after,
         control_ack=dict(session=session.session_id, command=command_summary(value),
                          before=before, after=capture_controls(after)))


class Commands:
    def __init__(self):
        self.items = queue.Queue(maxsize=64)
        self.closed = False
        threading.Thread(target=self.read, name='Player commands', daemon=True).start()

    def read(self):
        try:
            for line in sys.stdin:
                try:
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError('Command must be an object')
                    self.items.put(value)
                except ValueError as exc:
                    emit(error=str(exc))
        finally:
            self.closed = True

    def drain(self):
        values = []
        while True:
            try:
                values.append(self.items.get_nowait())
            except queue.Empty:
                return values


class DeviceWatch:
    """Same owned enumerator as the inline chooser, plus a two-second watch."""
    def __init__(self):
        self.enumerator = SourceEnumerator(enumerate_sources=list_sources,
                                           context_factory=backend_thread, poll_seconds=2.)
        self.enumerator.request()
        self.thread = self.enumerator.worker

    def refresh(self):
        self.enumerator.request()

    def owner_health(self):
        if self.stream is None:
            return dict(alive=False, released=True, close_error=None)
        health = self.stream.health()
        return dict(alive=bool(health['alive']), released=bool(health['released']),
                    close_error=str(health['close_error']) if health['close_error'] else None,
                    cleanup=getattr(getattr(self.stream, 'capture', None), 'cleanup_report', None))

    def restart_notice(self):
        health = self.owner_health()
        return RESTART_NOTICE if (self.capture_state == 'exhausted' or
            self.releasing_since is not None and (health['close_error'] or
            time.perf_counter() - self.releasing_since >= self.RELEASE_NOTICE)) else None

    def snapshot(self):
        result = self.enumerator.snapshot()
        return (result['token'], list(result['sources']), result['error']) if result else (0, [], None)

    def close(self):
        self.enumerator.close()


class LiveSession:
    MAX_ATTEMPTS = 5
    BACKOFF = (1., 2., 4., 8., 8.)
    OPEN_TIMEOUT = 5.
    PACKET_TIMEOUT = 2.
    RELEASE_NOTICE = 2.
    HEALTHY_RESET = 10.

    def __init__(self, renderer, config):
        self.renderer = renderer
        self.playback = Playback(config, LIVE_FORMS)
        self.playback.available = False
        renderer.player = self.playback
        for name in ('scale', 'movement', 'sparkle', 'flux', 'impact'):
            setattr(renderer.parameters, name, 0.)
        for state in config.get('recent', []):
            renderer.director_last_seen[state] = 0.
        self.source = config['source']
        self.session_id = config.get('_runtime_session', 'offline')
        self.stream = None
        self.watch = None
        self.capture_error = None
        self.clock = 0.
        self.last_wall = time.perf_counter()
        self.analysis_total = 0
        self.source_verified = False
        self.resuming = False
        self.resume_wait = False
        self.resume_after = 0.
        self.last_audio_at = None
        self.generation = 0
        self.capture_state = 'stopped'
        self.capture_detail = 'Not listening'
        self.attempts = 0
        self.next_attempt = 0.
        self.required_revision = 0
        self.enumeration_requested_at = None
        self.last_present = None
        self.opened_at = self.healthy_since = None
        self.releasing_since = None
        self.fresh_capture = False
        self.capture_history = deque(maxlen=128)
        self.capture_log_count = 0

    def status(self, state, detail):
        if (state, detail) == (self.capture_state, self.capture_detail):
            return
        self.capture_state, self.capture_detail = state, detail
        event = dict(UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                     state=state, detail=detail, generation=self.generation,
                     attempt=self.attempts, error=self.capture_error,
                     session=self.session_id, PID=os.getpid(), requested=self.source,
                     owner_source=self.owner_source())
        self.capture_history.append(event)
        # The parent session journal rotates by bytes; keep late retries/errors.
        print('CAPTURE STATE ' + json.dumps(event), file=sys.stderr, flush=True)
        self.capture_log_count += 1
        emit(capture_event=event)

    def refresh_endpoints(self):
        if self.watch is None:
            self.watch = DeviceWatch()
        self.required_revision = self.watch.snapshot()[0] + 1
        self.enumeration_requested_at = time.perf_counter()
        self.watch.refresh()

    def start(self):
        if not self.source:
            raise ValueError('Select one audio source explicitly.')
        if self.playback.running:
            self.retry()
            return
        completed = self.playback.index >= len(self.playback.config['queue'])
        self.playback.start()
        if completed and not self.playback.config['shuffle']:
            self.playback.index = -1
            self.playback.bonk_pending = True
            # Internal queue restart is a normal boundary, independent of the
            # user's session-only manual Bonk choice or any consumed request.
            self.playback.bonk_pending_mode = 'normal'
        self.resuming = True
        self.resume_wait = False
        self.resume_after = time.perf_counter()
        self.retry()

    def retry(self):
        if not self.playback.running:
            return
        self.generation += 1
        self.attempts = 0
        self.next_attempt = time.perf_counter()
        self.last_present = None
        self.capture_error = None
        self.begin_release()
        self.refresh_endpoints()
        if self.stream is None:
            self.status('checking', 'Checking selected endpoint identity')

    def begin_release(self):
        self.playback.available = False
        self.source_verified = False
        self.healthy_since = None
        if self.stream is not None and self.releasing_since is None:
            self.releasing_since = time.perf_counter()
            self.stream.request_stop()
            self.status('releasing', 'Releasing previous capture; no replacement can open yet')

    def stop(self, reason=None):
        self.generation += 1
        self.playback.stop(reason or 'Stopped · current world is settling')
        self.begin_release()
        if self.stream is None:
            self.status('stopped', 'Not listening')
        self.renderer.parameters.impact = 0.
        self.renderer.parameters.beat_tick = False
        self.resuming = self.resume_wait = False

    def select_source(self, source):
        selected = validate_config(dict(self.playback.config, source=source), LIVE_FORMS)['source']
        if selected is None:
            raise ValueError('Select one audio source explicitly.')
        self.source = selected
        self.generation += 1
        self.begin_release()
        self.attempts = 0
        self.next_attempt = time.perf_counter()
        self.last_present = None
        self.capture_error = None
        if self.playback.running:
            self.refresh_endpoints()
            if self.stream is None:
                self.status('checking', 'Checking explicitly selected replacement')
        elif self.stream is None:
            self.status('stopped', 'Source selected · Start when ready')

    def command(self, value):
        op = value.get('op')
        if op == 'start':
            self.start()
        elif op == 'retry':
            self.retry()
        elif op == 'stop':
            self.stop()
        elif op == 'pause':
            was = self.playback.paused
            self.playback.pause()
            self.resuming = was and not self.playback.paused
            self.resume_wait = self.resuming
            if self.resuming:
                self.resume_after = time.perf_counter()
        elif op == 'hold':
            self.playback.hold(str(value.get('owner', 'panel'))[:32], bool(value.get('active')))
        elif op == 'release_focus':
            self.playback.release_focus(str(value.get('owner', 'panel'))[:32])
        elif op == 'bonk':
            self.playback.bonk(self.renderer.director_target is not None, value.get('mode'))
        elif op == 'bonk_mode':
            self.playback.set_bonk_mode(value['mode'])
        elif op == 'configure':
            self.playback.configure(value['config'], self.renderer.director_current)
        elif op in ('source', 'switch_source'):
            self.select_source(value['source'])
        elif op != 'close':
            raise ValueError('Unknown player command')

    def failed(self, message, wall):
        self.capture_error = message
        self.generation += 1
        self.next_attempt = wall + self.BACKOFF[min(max(0, self.attempts - 1), len(self.BACKOFF) - 1)]
        self.begin_release()
        self.refresh_endpoints()
        if self.stream is None:
            self.status('retrying', 'Capture open failed · bounded retry pending: ' + message)
        emit(capture_error=message, capture_failed=True)

    def service_capture(self, wall):
        if self.releasing_since is not None:
            health = self.stream.health()
            if not health['alive'] and health['released']:
                self.analysis_total += self.stream.analyzed
                self.stream = None
                self.releasing_since = None
                self.status('checking' if self.playback.running else 'stopped',
                            'Previous capture released' if self.playback.running else 'Not listening')
            else:
                if health['close_error'] is not None:
                    self.status('releasing', 'Capture release failed: ' + str(health['close_error']) + '. ' + RESTART_NOTICE)
                elif wall - self.releasing_since >= self.RELEASE_NOTICE:
                    self.status('releasing', 'Capture release unconfirmed after 2s; replacement blocked. ' + RESTART_NOTICE)
                return []
        if not self.playback.running:
            if self.stream is not None:
                self.begin_release()
            return []
        if self.watch is None:
            return []
        revision, sources, error = self.watch.snapshot()
        if revision < self.required_revision:
            if self.stream is None:
                waiting = self.enumeration_requested_at is not None and wall - self.enumeration_requested_at >= self.OPEN_TIMEOUT
                self.status('checking', 'Endpoint enumeration pending after 5s; no capture opened' if waiting else
                            'Waiting for refreshed endpoint enumeration')
            return []
        present = any(x['id'] == self.source['id'] and x['kind'] == self.source['kind'] for x in sources)
        if error or not present:
            if not error:
                self.last_present = False
            if self.stream is not None:
                self.failed(error or 'Selected endpoint unavailable', wall)
            else:
                self.status('unavailable', 'Endpoint enumeration failed: ' + error if error else
                            'Selected endpoint unavailable · watching exact ID; Change source if its ID changed')
            return []
        if self.last_present is False:
            self.attempts = 0  # A newly observed absent → present edge, not another open error.
        self.last_present = True
        if self.stream is None:
            if self.attempts >= self.MAX_ATTEMPTS:
                self.status('exhausted', 'Five open attempts exhausted · Retry capture or Change source: ' + str(self.capture_error or 'No capture'))
                return []
            if wall < self.next_attempt:
                self.status('retrying', 'Waiting for bounded retry backoff: ' + str(self.capture_error or 'Capture unavailable'))
                return []
            self.attempts += 1
            self.opened_at = wall
            self.last_audio_at = None
            self.fresh_capture = True
            try:
                analyzer = AudioAnalyzer()
                processor = SignalProcessor(smoothing=.5)
                conditioner = VisualSignalConditioner(quiet_threshold=.06)
                detectors = {k: OnsetDetector(threshold=.2) for k in ('bass', 'mids', 'highs')}
                capture = AudioCapture(device_name=self.source['id'], source_kind=self.source['kind'], exact_id=True, owner_generation=self.generation)
                self.stream = CaptureStream(capture, lambda samples: (samples, analyze_samples(samples, analyzer, processor, conditioner, detectors)), generation=self.generation)
                self.stream.start()
                self.status('opening', 'Opening exact selected endpoint')
            except Exception as exc:
                self.failed(str(exc), wall)
                return []
        try:
            if self.stream.generation != self.generation:
                self.begin_release()
                return []
            incoming = self.stream.drain()
            health = self.stream.health()
            if not health['alive']:
                raise RuntimeError('Capture worker exited')
            if health['last_packet_at'] is None:
                if wall - self.opened_at > self.OPEN_TIMEOUT:
                    raise RuntimeError('Capture open/first packet stalled for 5s')
            elif wall - health['last_packet_at'] > self.PACKET_TIMEOUT:
                read_stale = health['last_read_at'] is None or wall - health['last_read_at'] > self.PACKET_TIMEOUT
                raise RuntimeError(('Capture read' if read_stale else 'Analysis packet') + ' progress stalled for 2s')
            if incoming:
                self.last_audio_at = incoming[-1][0]
                self.playback.available = True
                if not self.source_verified:
                    self.source_verified = True
                    self.capture_error = None
                    self.healthy_since = wall
                    working = self.owner_source() or self.source
                    emit(source_working=working, generation=self.generation)
                    self.status('capturing', 'Listening to ' + ('System audio (loopback)' if working['kind'] == 'loopback' else 'Microphone') + ' · ' + working['name'])
                if wall - self.healthy_since >= self.HEALTHY_RESET:
                    self.attempts = 0
            return incoming
        except Exception as exc:
            self.failed(str(exc.__cause__ or exc), wall)
            return []

    def tick(self, wall=None):
        wall = time.perf_counter() if wall is None else wall
        dt = max(0., wall - self.last_wall)
        self.last_wall = wall
        incoming = self.service_capture(wall)
        if self.playback.paused:
            return False  # Analysis/recovery proceeds; image and all visual clocks stay frozen.
        if self.resuming:
            incoming = [row for row in incoming if row[0] >= self.resume_after]
        p = self.renderer.parameters
        p.impact = 0.
        p.beat_tick = False
        if incoming and self.playback.running:
            stamp, (samples, frame) = incoming[-1]
            result = VisualParameterMapper().map_frame(frame)
            for name in ('scale', 'movement', 'sparkle'):
                setattr(p, name, result[name])
            p.flux = frame.flux
            p.beat_confidence = frame.beat_confidence
            if not self.resuming and not self.playback.resume_fresh and not self.fresh_capture:
                p.impact = max(VisualParameterMapper().map_frame(row[1][1])['impact'] for row in incoming)
                p.beat_tick = any(row[1][1].beat_tick for row in incoming)
            self.renderer.consume_pcm(samples)
            self.resuming = self.resume_wait = self.playback.resume_fresh = self.fresh_capture = False
        elif not self.playback.available or (self.last_audio_at is not None and wall - self.last_audio_at > .25):
            for name in ('scale', 'movement', 'sparkle', 'flux'):
                setattr(p, name, getattr(p, name) * math.exp(-dt / .8))
        if self.resuming and self.resume_wait and self.playback.available:
            return False  # Explicit healthy Resume waits for new packets, never backlog.
        self.clock += dt
        self.renderer.render(self.clock)
        self.renderer.swap_buffers()
        if not self.playback.running and self.stream is not None and self.releasing_since is None:
            self.stop(self.playback.end_reason)
        return True

    def owner_source(self):
        return getattr(getattr(self.stream, 'capture', None), 'resolved', None) if self.stream else None

    def owner_health(self):
        if self.stream is None:
            return dict(alive=False, released=True, close_error=None)
        health = self.stream.health()
        return dict(alive=bool(health['alive']), released=bool(health['released']),
                    close_error=str(health['close_error']) if health['close_error'] else None,
                    cleanup=getattr(getattr(self.stream, 'capture', None), 'cleanup_report', None))

    def restart_notice(self):
        health = self.owner_health()
        return RESTART_NOTICE if (self.capture_state == 'exhausted' or
            self.releasing_since is not None and (health['close_error'] or
            time.perf_counter() - self.releasing_since >= self.RELEASE_NOTICE)) else None

    def snapshot(self):
        r = self.renderer
        return dict(self.playback.snapshot(), current=r.director_current,
                    target=r.director_target, transition_id=r.director_recipe if r.transition_progress() is not None else None,
                    transition_progress=r.transition_progress(), transition_complete=r.director_transition_complete,
                    scene_seconds=self.clock, analysis_frames=self.analysis_total + (self.stream.analyzed if self.stream else 0),
                    listening=self.playback.available, listen_requested=self.playback.running,
                    capture_state=self.capture_state, capture_detail=self.capture_detail,
                    capture_error=self.capture_error,
                    capture_owner=self.stream is not None, attempts=self.attempts,
                    generation=self.generation, source=self.source,
                    active_source=self.owner_source() if self.playback.available else None,
                    owner_source=self.owner_source(), runtime_session=self.session_id,
                    owner_health=self.owner_health(), waiting_for_fresh=self.resuming, restart_notice=self.restart_notice())


def install_keys(renderer, session):
    down = set()
    def key(window, code, scan, action, mods):
        if action == glfw.REPEAT:
            return
        if action == glfw.RELEASE:
            down.discard(code)
            if code in (glfw.KEY_LEFT_SHIFT, glfw.KEY_RIGHT_SHIFT):
                session.playback.hold('output' + str(code), False)
            return
        if code in down:
            return
        down.add(code)
        if code in (glfw.KEY_LEFT_SHIFT, glfw.KEY_RIGHT_SHIFT):
            session.playback.hold('output' + str(code), True)
        elif code == glfw.KEY_SPACE:
            session.playback.bonk(renderer.director_target is not None)
        elif code == glfw.KEY_ENTER and mods & glfw.MOD_CONTROL:
            # Panel owns the current chooser/draft. Route focused output Start
            # through it rather than listening to a stale pre-edit endpoint.
            emit(action='start_request')
        elif code == glfw.KEY_S and mods & glfw.MOD_CONTROL:
            session.stop()
        elif code == glfw.KEY_P and mods & glfw.MOD_CONTROL:
            session.command(dict(op='pause'))
        elif code == glfw.KEY_F11:
            monitor = glfw.get_window_monitor(window)
            if monitor:
                x, y, w, h = renderer._player_windowed
                glfw.set_window_monitor(window, None, x, y, w, h, 0)
            else:
                renderer._player_windowed = (*glfw.get_window_pos(window), *glfw.get_window_size(window))
                monitor = glfw.get_primary_monitor()
                mode = glfw.get_video_mode(monitor)
                glfw.set_window_monitor(window, monitor, 0, 0, mode.size.width, mode.size.height, mode.refresh_rate)
        elif code == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)
    def focus(window, active):
        if not active:
            down.clear()
            session.playback.release_focus('output')
    glfw.set_key_callback(renderer.window, key)
    glfw.set_window_focus_callback(renderer.window, focus)


def main():
    emit(runtime_pid=os.getpid())
    raw_config = json.loads(sys.stdin.readline())
    config = validate_config(raw_config, LIVE_FORMS)
    config['_runtime_session'] = str(raw_config.get('session_id', 'unbound'))
    binding = source_binding(Path(__file__).resolve().parents[1],
        ['app/player_runtime.py', 'app/audio/wasapi_cleanup.py', 'app/audio/capture.py', 'app/audio/capture_stream.py', 'app/player_state.py', 'app/visuals/renderer.py'],
        {'LiveSession.start': LiveSession.start, 'LiveSession.select_source': LiveSession.select_source,
         'LiveSession.service_capture': LiveSession.service_capture, 'CaptureStream._run': CaptureStream._run,
         'AudioCapture.find_device': AudioCapture.find_device, 'AudioCapture.start': AudioCapture.start,
         'AudioCapture.stop': AudioCapture.stop, 'WasapiCleanup.close': WasapiCleanup.close,
         'dispatch_control': dispatch_control,
         'Renderer.update_blend': Renderer.update_blend})
    emit(runtime_identity=dict(session=config['_runtime_session'], PID=os.getpid(), python=sys.version, binding=binding, backend_abi_sha256=BACKEND_SHA256))
    commands = Commands()
    renderer = Renderer(title='ZeraWave')
    renderer.startup_callback = lambda phase: emit(startup=dict(phase=phase))
    session = LiveSession(renderer, config)
    session.playback.set_bonk_mode(raw_config.get('bonk_mode', 'normal'))
    try:
        renderer.create()
        session.last_wall = time.perf_counter()
        # Initialize a truthful idle frame/actual world before listening starts.
        session.tick()
        install_keys(renderer, session)
        emit(state=session.snapshot())
        session.start()
        last_status = 0.
        while not renderer.should_close() and not commands.closed:
            close = False
            for value in commands.drain():
                try:
                    if value.get('op') == 'close':
                        close = True
                        break
                    dispatch_control(session, value)
                except Exception as exc:
                    emit(error=str(exc), ack=value.get('serial'), control_ack=dict(session=session.session_id, command=command_summary(value), error=str(exc), after=capture_controls(session.snapshot())))
            if close:
                break
            session.tick()
            renderer.poll_events()
            now = time.perf_counter()
            if now-last_status >= .15:
                emit(state=session.snapshot())
                last_status = now
            # Event/capture servicing continues while exact-image Pause skips GL.
            if session.playback.paused:
                time.sleep(.01)
            else:
                time.sleep(.001)
    except Exception as exc:
        emit(error=str(exc), fatal=True)
        raise
    finally:
        try:
            session.stop()
            emit(runtime_shutdown=dict(session=session.session_id, owner_unconfirmed=session.stream is not None, requested=session.source))
            if session.watch:
                session.watch.close()
        finally:
            renderer.close()
            emit(closed=True)
