"""Focused free-player config, control, queue, live-loop and Tk checks."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import time
import tkinter as tk
import numpy as np
import player
from player_state import Playback, defaults, validate_config
from player_runtime import LiveSession, install_keys
import glfw
from renderer import Renderer, LIVE_FORMS
from audio_frame import AudioFrame
from capture import AudioCapture


def config(queue, **kw):
    return dict(defaults(LIVE_FORMS), queue=queue, **kw)


def fails(value):
    try:
        validate_config(value, LIVE_FORMS)
    except ValueError:
        return
    raise AssertionError('Invalid settings accepted')


def model_tests():
    assert len(LIVE_FORMS) == 27 and 36 in LIVE_FORMS
    assert not set((37, 38, 39, 40)) & set(LIVE_FORMS)
    for q in ([], [37], [38], [True], [7]*51):
        fails(config(q))
    for key in ('shuffle', 'loop', 'tips', 'recent_history'):
        fails(dict(config([7]), **{key: 'yes'}))
    assert len(validate_config(config([7]*50), LIVE_FORMS)['queue']) == 50
    p = Playback(config([7, 7, 26], shuffle=False, loop=False), LIVE_FORMS)
    assert p.initial(lambda q: q[0]) == 7
    p.start()
    p.hold('panel.Shift_L', True)
    p.pause()
    p.bonk()
    assert p.paused and not p.bonk_pending
    p.pause()
    assert p.resume_fresh and p.held and p.running
    p.bonk()
    assert p.bonk_pending
    assert p.next(7, lambda q: q[0]) == 7 and p.held
    assert p.next(7, lambda q: q[0]) == 26
    assert p.next(26, lambda q: q[0]) is None and not p.running
    p.start();p.pause();p.stop()
    assert not p.running and not p.paused and not p.bonk_pending
    p.release_focus('panel')
    assert not p.held
    p = Playback(config([26], shuffle=True, loop=False), LIVE_FORMS)
    p.start();assert p.initial(lambda q: q[0]) == 26
    for _ in range(100):
        assert p.next(26, lambda q: q[0]) == 26 and p.running
    p.configure(config([36, 7], shuffle=False, loop=True), 26)
    assert p.config['queue'] == [26]
    assert p.next(26, lambda q: q[0]) == 36
    assert p.next(36, lambda q: q[0]) == 7
    assert p.next(7, lambda q: q[0]) == 36
    print('PASS: config/cap/exclusions, duplicates/order/end/loop, shuffle without loop, solo/subset, Hold/Bonk/Pause/Stop, boundary edits')


class FakeStream:
    def __init__(self):
        self.frames = []
        self.analyzed = 0
        self.stopped = False
        self.generation = 0
        self.last_packet_at = None
    def drain(self):
        frames = self.frames;self.frames = [];return frames
    def stop(self):
        self.stopped = True
    def request_stop(self):
        self.stop()
        self.frames = []
    def health(self):
        return dict(alive=not self.stopped, released=self.stopped, close_error=None,
                    last_packet_at=self.last_packet_at, last_read_at=self.last_packet_at)
    def feed(self, level, hit=False):
        frame = AudioFrame(level, level*.7, level*.5, int(hit), int(hit), int(hit), flux=level)
        frame.beat_tick = hit;frame.beat_confidence = .8
        self.analyzed += 1
        self.last_packet_at = time.perf_counter()
        self.frames.append((self.last_packet_at, (np.zeros((2048, 2)), frame)))


def runtime_tests():
    renderer = Renderer(seed=6)
    renders = []
    def render(clock):
        old = renderer.last_render_time
        renderer.update_blend(clock, 0. if old is None else clock-old)
        renderer.last_render_time = clock
        renders.append((clock, renderer.parameters.impact))
    renderer.render = render
    renderer.swap_buffers = lambda: None
    source = dict(kind='loopback', id='fake-out', name='Fake output')
    s = LiveSession(renderer, config([26, 7, 7], shuffle=False, loop=False, source=source))
    s.watch = SimpleNamespace(snapshot=lambda: (1, [source], None))
    stream = FakeStream();s.stream = stream;s.playback.start()
    s.last_wall = 0.
    stream.feed(.3);s.tick(1.)
    assert renderer.director_current == 26
    before = len(renders), s.clock, renderer.director_time, renderer.director_current
    s.command(dict(op='pause'))
    for wall in (2., 3., 100.):
        stream.feed(.9, True);assert not s.tick(wall)
    assert (len(renders), s.clock, renderer.director_time, renderer.director_current) == before
    assert stream.analyzed == 4 and not stream.frames
    s.command(dict(op='hold', owner='panel.Shift_L', active=True))
    s.command(dict(op='bonk'));assert not s.playback.bonk_pending
    stream.feed(.99, True)  # packet queued before Resume must be discarded
    s.command(dict(op='pause'))
    clock = s.clock;count = len(renders)
    s.tick(100.01)
    assert s.clock == clock and len(renders) == count
    stream.feed(.2, True);s.tick(100.02)
    assert renderer.parameters.scale == .2 and renderer.parameters.impact == 0 and not renderer.parameters.beat_tick
    assert renders[-1][0] < 1.1 and renderer.director_current == 26
    s.command(dict(op='bonk'));stream.feed(.4);s.tick(100.04)
    assert renderer.director_target == 7 and s.playback.held
    stream.feed(.5);s.tick(112.)
    assert renderer.director_current == 7 and renderer.director_target is None and s.playback.held
    held_time = renderer.director_time
    stream.feed(.8, True);s.tick(200.)
    assert renderer.director_current == 7 and renderer.director_time == held_time
    s.command(dict(op='pause'));s.command(dict(op='stop'))
    assert stream.stopped and not s.playback.paused and s.capture_state == 'releasing'
    s.tick(200.01)
    assert s.stream is None
    state = renderer.director_current
    before = renderer.parameters.scale
    s.tick(201.)
    assert renderer.director_current == state and renderer.parameters.scale < before
    # Stop in a transition freezes its current ownership rather than selecting
    # or snapping to a different world.
    renderer = Renderer(seed=5)
    p = Playback(config([26, 7], shuffle=False), LIVE_FORMS);renderer.player = p;p.start()
    renderer.update_blend(0., 0.)
    p.bonk();renderer.update_blend(.1, .1);renderer.update_blend(1., .9)
    before = dict(renderer.blend_values), renderer.director_current, renderer.director_target
    p.stop();renderer.update_blend(10., 9.)
    assert (renderer.blend_values, renderer.director_current, renderer.director_target) == before
    print('PASS: mocked live-loop Pause while analysis advances, no catch-up/current-audio Resume, Bonk held arrival, Stop from Pause/transition and gentle parameter settling')


def capture_tests():
    mic = SimpleNamespace(id='mic', name='Shared', isloopback=False)
    output = SimpleNamespace(id='out', name='Shared', isloopback=True)
    with patch('capture.sc.all_microphones', return_value=[mic, output]):
        assert AudioCapture('mic', source_kind='microphone').find_device() is mic
        assert AudioCapture('out').find_device() is output
        for device, kind in [('missing', 'loopback'), ('mic', 'loopback'), ('out', 'microphone')]:
            try:
                AudioCapture(device, source_kind=kind).find_device()
            except RuntimeError:
                pass
            else:
                raise AssertionError('Wrong or missing source accepted')
    callbacks = {}
    renderer = Renderer(seed=6)
    renderer.window = object()
    session = LiveSession(renderer, config([26,7],shuffle=False))
    session.playback.start()
    with patch('player_runtime.glfw.set_key_callback', side_effect=lambda window, fn: callbacks.update(key=fn)), patch('player_runtime.glfw.set_window_focus_callback', side_effect=lambda window, fn: callbacks.update(focus=fn)):
        install_keys(renderer, session)
    key = callbacks['key'];window=renderer.window
    key(window,glfw.KEY_LEFT_SHIFT,0,glfw.PRESS,0)
    assert session.playback.held
    key(window,glfw.KEY_SPACE,0,glfw.PRESS,0)
    assert session.playback.bonk_pending
    session.playback.bonk_pending=False
    key(window,glfw.KEY_SPACE,0,glfw.REPEAT,0)
    key(window,glfw.KEY_SPACE,0,glfw.PRESS,0)
    assert not session.playback.bonk_pending
    callbacks['focus'](window,False)
    assert not session.playback.held
    session.playback.pause()
    key(window,glfw.KEY_SPACE,0,glfw.PRESS,0)
    assert not session.playback.bonk_pending
    with patch('player_runtime.emit') as emit:
        key(window,glfw.KEY_ENTER,0,glfw.PRESS,glfw.MOD_CONTROL)
        emit.assert_called_once_with(action='start_request')
    key(window,glfw.KEY_S,0,glfw.PRESS,glfw.MOD_CONTROL)
    assert not session.playback.running and not session.playback.paused
    print('PASS: mocked focused GLFW key/focus callbacks, repeat debounce, paused Bonk rejection and Ctrl+S Stop')
    print('PASS: exact source identity and explicit loopback/microphone distinction, no fallback')


def ui_tests():
    source = dict(kind='loopback', id='out', name='Headphones')
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        path = folder/'settings.json'
        assert player.load_settings(path) == defaults(LIVE_FORMS)
        player.save_settings(path, dict(config([7, 7, 26], shuffle=False, loop=False), source=source))
        assert player.load_settings(path)['queue'] == [7, 7, 26]
        path.write_text('{invalid', encoding='utf-8')
        assert player.load_settings(path)['queue'] == []
        path.write_text('{"device":"old-id"}', encoding='utf-8')
        assert player.load_settings(path)['source']['id'] == 'old-id'
        with patch('capture.list_sources', return_value=[source]), patch.object(player.Player, 'refresh'):
            root = tk.Tk();root.withdraw();app = player.Player(root, folder)
            try:
                app.receive(dict(sources=[source]))
                assert app.selected_source()['id'] == 'old-id' and 'unavailable' in app.status.get()
                app.device.set(next(iter(app.options)))
                app.source_changed(SimpleNamespace(widget=app.devices))
                app.show_panel()
                assert app.tips.get() is False and not app.tip_label.winfo_ismapped()
                app.queue_ids = [7, 7, 26];app.shuffle.set(False);app.loop.set(False)
                assert app.apply_queue()
                assert player.load_settings(path)['queue'] == [7, 7, 26]
                app.clear_queue();assert not app.apply_queue() and '1–50' in app.status.get()
                app.receive(dict(sources=[]));assert app.selected_source()['id'] == 'out'
                app.start();assert app.process is None and '1–50' in app.status.get()
                with patch.object(app, 'send') as send:
                    app.text_focus = lambda: False
                    e = SimpleNamespace(keysym='space', state=0)
                    app.key_press(e);app.key_press(e)
                    assert send.call_count == 1
                    app.key_release(e)
                    app.text_focus = lambda: True
                    app.key_press(e);assert send.call_count == 1
                    app.text_focus = lambda: False
                    e.keysym = 'Shift_L';app.key_press(e);app.key_release(e)
                    assert send.call_args.kwargs['active'] is False
                    with patch.object(root, 'focus_displayof', return_value=None):
                        app.focus_check()
                    assert send.call_args.kwargs['owner'] == 'panel'
                with patch.object(app, 'start') as start:
                    app.receive(dict(action='start_request'))
                    start.assert_called_once()
                assert len(player.WORLDS) == 27 and player.BY_ID[26]['subcategory'] == 'Earth'
                # The shortcut tag runs before ttk's Space-to-invoke binding.
                root.deiconify();root.update();app.keys_down.clear()
                with patch.object(app, 'send') as send, patch.object(app, 'start') as start:
                    app.text_focus = lambda: False
                    app.start_button.configure(state='normal', command=start)
                    app.start_button.event_generate('<KeyPress-space>')
                    app.start_button.event_generate('<KeyRelease-space>')
                    root.update()
                    assert send.call_count == 1 and send.call_args.args == ('bonk',)
                    start.assert_not_called()
                app.receive(dict(error='Selected endpoint lost',device_lost=True))
                assert app.selected_source()['id'] == 'out'
            finally:
                app.close()
    print('PASS: actual Tk widgets/mocked source chooser, missing source, settings migration/reload, invalid queue, focused key debounce/text exemption/focus loss, shared taxonomy')


def bonk_restart_tests():
    """Actual Start/command/tick/director route with fake PCM and no device/UI/GL."""
    from contextlib import ExitStack
    import json
    results = []
    with ExitStack() as guards:
        for target in ('renderer.Renderer.create', 'capture.AudioCapture.__init__',
                       'player_runtime.DeviceWatch.__init__', 'player.subprocess.Popen'):
            guards.enter_context(patch(target, side_effect=AssertionError('Offline test attempted '+target)))
        for restart_mode in ('normal', 'instant'):
            renderer = Renderer(seed=6)
            source = dict(kind='loopback', id='offline-restart', name='Offline restart fixture')
            session = LiveSession(renderer, config([26, 7], shuffle=False, loop=False, source=source))
            wall = [0.]
            def render(clock):
                before = renderer.last_render_time
                renderer.update_blend(clock, 0. if before is None else clock-before)
                renderer.last_render_time = clock
            renderer.render = render; renderer.swap_buffers = lambda: None
            def fake_capture(now):
                session.playback.available = True
                frame = AudioFrame(.3, .2, .1, 0, 0, 0, flux=.1)
                return [(now, (np.zeros((2048, 2)), frame))]
            def pump(delta):
                wall[0] += delta; session.tick(wall[0])
            with patch.object(session, 'retry'), patch.object(session, 'service_capture', side_effect=fake_capture), \
                 patch('player_runtime.time.perf_counter', side_effect=lambda: wall[0]):
                # Exact reported route: non-looping ordered queue -> Instant ->
                # finish queue -> choose Normal (or keep Instant) -> Start.
                session.command(dict(op='start')); pump(0.)
                assert renderer.director_current == 26 and session.playback.index == 0
                session.command(dict(op='bonk', mode='instant')); pump(.01)
                assert renderer.director_target == 7 and renderer.director_duration == .35
                pump(.36)
                assert renderer.director_current == 7 and session.snapshot()['transition_progress'] == 1.
                renderer.director_min_hold = renderer.director_max_hold = 0.
                pump(.01)
                assert not session.playback.running and session.playback.index == 2
                assert renderer.director_target is None and renderer.director_current == 7
                session.command(dict(op='bonk_mode', mode=restart_mode))
                session.command(dict(op='start')); pump(.01)
                duration = renderer.director_duration
                print('Restart case:', json.dumps(dict(selected_mode=restart_mode, restart_duration=duration,
                                                      current=renderer.director_current, target=renderer.director_target)))
                assert renderer.director_target == 26 and 6. <= duration <= 9., 'Internal queue restart inherited stale Instant mode'
                assert session.playback.bonk_mode == restart_mode
                assert not session.playback.bonk_pending and session.playback.bonk_pending_mode == 'normal'
                pump(duration+.01)
                assert renderer.director_current == 26 and session.playback.index == 0
                session.command(dict(op='hold', owner='test', active=True))
                for _ in range(100): session.command(dict(op='bonk', mode='instant'))
                pump(.01)
                assert renderer.director_target == 7 and renderer.director_duration == .35
                assert session.playback.bonk_pending_mode == 'normal' and not session.playback.bonk_pending
                progress = [session.snapshot()['transition_progress']]
                for _ in range(18):
                    session.command(dict(op='bonk')); pump(.02)
                    progress.append(session.snapshot()['transition_progress'])
                assert progress == sorted(progress) and progress[-1] == 1.
                assert renderer.director_current == 7 and renderer.director_target is None
                assert session.playback.index == 1 and session.playback.held
                pump(1.); assert renderer.director_current == 7 and renderer.director_target is None
                session.command(dict(op='bonk')); assert session.playback.bonk_pending_mode == 'instant'
                session.command(dict(op='pause'))
                assert not session.playback.bonk_pending and session.playback.bonk_pending_mode == 'normal'
                session.command(dict(op='bonk')); session.command(dict(op='pause')); pump(.01)
                assert renderer.director_target is None  # no Resume backlog
                session.command(dict(op='bonk')); session.command(dict(op='stop'))
                assert not session.playback.bonk_pending and session.playback.bonk_pending_mode == 'normal'
                assert not session.playback.bonk_expedite and session.playback.bonk_mode == 'instant'
                results.append(dict(restart_mode=restart_mode, internal_restart_duration=duration,
                                    subsequent_manual_duration=.35, manual_progress=progress))
        # Consuming a same-world/solo request also cleans transient mode state.
        p = Playback(config([26], shuffle=False), LIVE_FORMS); p.start(); p.initial(lambda q:q[0])
        p.bonk(mode='instant'); assert p.next(26, lambda q:q[0]) == 26
        assert p.bonk_pending_mode == 'normal' and not p.bonk_pending and p.bonk_mode == 'instant'
    print('PASS: exact ordered non-looping queue restart Normal for either selected mode; subsequent manual Instant .35; '
          'handled/canceled transient mode reset, coalescing/progress100, held arrival/Pause/Stop/order/solo. Actual runtime/director, mocked capture; no UI/GPU/device.')
    return results


def instant_bonk_tests():
    """Controlled director clocks and withdrawn/mocked UI; no real GL or audio."""
    import json
    import runpy
    from contextlib import ExitStack
    from renderer import INSTANT_BONK_SECONDS
    from transition_catalog import compatible

    def scene(queue=(26, 7, 14), mode='normal', held=False):
        r = Renderer(seed=6)
        p = Playback(config(list(queue), shuffle=False, loop=True), LIVE_FORMS)
        r.player = p; p.start(); p.set_bonk_mode(mode)
        r.update_blend(0., 0.)
        p.hold('panel.button', held)
        return r, p

    def step(r, delta):
        r.update_blend(r.director_time+delta, delta)

    # Byte-bound pre-delta renderer proves the Normal route, timings, RNG and
    # actual blend uniforms match, rather than just checking a duration range.
    baseline = player.ROOT/'work/studio-organization-01/instant-bonk-delta/baseline/app/visuals/renderer.py'
    if baseline.is_file():
        Before = runpy.run_path(str(baseline))['Renderer']
        old = Before(seed=6); old.player = Playback(config([26, 7, 14], shuffle=False), LIVE_FORMS)
        old.player.start(); old.update_blend(0., 0.)
        normal, p = scene()
        old.player.bonk(); p.bonk()
        elapsed = 0.
        for delta in (0., .01, .1, .5, 1., 2., 3., 8., 20., 35., 40.):
            elapsed += delta
            old.update_blend(elapsed, delta); normal.update_blend(elapsed, delta)
            assert old.blend_values == normal.blend_values
            for field in ('director_current', 'director_target', 'director_duration', 'director_transition',
                          'director_since', 'director_min_hold', 'director_max_hold', 'director_history'):
                assert getattr(old, field) == getattr(normal, field), field
            assert old.director_rng.getstate() == normal.director_rng.getstate()
    normal, p = scene(); p.bonk(); step(normal, 0.)
    assert 6. <= normal.director_duration <= 9.
    p.bonk(True); assert not p.bonk_pending and not p.bonk_expedite

    instant, p = scene(mode='instant', held=True)
    for _ in range(100): p.bonk()
    step(instant, 0.)
    assert instant.director_target == 7 and instant.director_duration == INSTANT_BONK_SECONDS
    assert compatible(instant.director_recipe, 26, 7) and p.held
    assert instant.director_pending is None and instant.director_time == 0.
    progress = [instant.transition_progress()]
    for _ in range(18):
        p.bonk(instant.director_target is not None)
        step(instant, .02); progress.append(instant.transition_progress())
    assert progress == sorted(progress) and progress[-1] == 1.
    assert instant.director_current == 7 and instant.director_target is None
    assert p.index == 1 and len(instant.director_history) == 2 and p.held
    # The repeat on the final active tick is consumed, never a hidden next-world
    # request. Held arrival remains the existing world with frozen director time.
    held_time = instant.director_time; step(instant, 20.)
    assert instant.director_time == held_time and instant.director_current == 7
    p.hold('panel.button', False)
    instant.director_min_hold = instant.director_max_hold = 0.
    step(instant, .01)
    assert instant.director_target == 14 and 6. <= instant.director_duration <= 9.
    assert not instant.director_bonk_expedited  # Instant selection never changes automatic timing.
    step(instant, 10.); p.bonk(mode='normal'); step(instant, 0.)
    assert instant.director_target == 26 and 6. <= instant.director_duration <= 9.

    active, p = scene(); p.bonk(); step(active, 0.)
    step(active, active.director_duration*.4)
    before = active.transition_progress(), dict(active.blend_values), active.director_recipe, active.director_target
    for _ in range(100): p.bonk(True, mode='instant')
    step(active, 0.)
    assert abs(active.transition_progress()-before[0]) < 1e-12
    for key, value in before[1].items(): assert np.allclose(active.blend_values[key], value, atol=1e-12)
    assert active.director_recipe == before[2] and active.director_target == before[3]
    assert abs((1.-active.transition_progress())*active.director_duration-INSTANT_BONK_SECONDS) < 1e-12
    retimed = active.director_duration, active.director_transition
    samples = [active.transition_progress()]
    for _ in range(18):
        p.bonk(True)
        step(active, .02); samples.append(active.transition_progress())
        assert (active.director_duration, active.director_transition) == retimed
    assert samples == sorted(samples) and samples[-1] == 1.
    assert active.director_current == 7 and p.index == 1 and len(active.director_history) == 2
    assert not p.bonk_pending and not p.bonk_expedite
    tail, p = scene(); p.bonk(); step(tail, 0.); step(tail, tail.director_duration*.99)
    unchanged = tail.director_duration, tail.director_transition
    p.bonk(True, mode='instant'); step(tail, 0.)
    assert (tail.director_duration, tail.director_transition) == unchanged  # never lengthen a short tail

    paused, p = scene(held=True, mode='instant'); p.bonk(); p.pause()
    assert not p.bonk_pending and not p.bonk_expedite
    p.bonk(); p.pause(); step(paused, 0.)
    assert paused.director_target is None and paused.director_current == 26
    p.bonk(); step(paused, 0.); duration = paused.director_duration
    p.bonk(True); p.pause(); assert not p.bonk_expedite
    p.pause(); step(paused, 0.); assert paused.director_duration == duration
    p.stop(); p.bonk(True)
    frozen = paused.director_current, paused.director_target, dict(paused.blend_values), paused.transition_progress()
    step(paused, 10.)
    assert (paused.director_current, paused.director_target, paused.blend_values, paused.transition_progress()) == frozen
    assert not p.bonk_pending and not p.bonk_expedite

    solo, p = scene(queue=(26,), mode='instant'); p.bonk(); step(solo, 0.)
    assert solo.director_target is None and solo.director_current == 26 and p.running
    duplicate, p = scene(queue=(26, 26, 7), mode='instant')
    p.bonk(); step(duplicate, 0.); assert duplicate.director_target is None and p.index == 1
    p.bonk(); step(duplicate, 0.); assert duplicate.director_target == 7 and p.index == 2
    p.configure(config([14, 5], shuffle=False), 26)
    p.bonk(True); step(duplicate, .36)
    assert duplicate.director_current == 7 and p.pending_config is not None
    p.bonk(); step(duplicate, 0.); assert duplicate.director_target == 14 and p.pending_config is None
    shuffle = Renderer(seed=8); p = Playback(config([7, 26, 36]), LIVE_FORMS)
    shuffle.player = p; p.start(); p.set_bonk_mode('instant'); step(shuffle, 0.)
    for _ in range(12):
        p.bonk(); step(shuffle, 0.); step(shuffle, .36)
        assert shuffle.director_current in {7, 26, 36} and len(shuffle.director_history) <= 64
    galaxy, p = scene(queue=(36, 7), mode='instant')
    galaxy.director_min_hold = galaxy.director_max_hold = 0.
    step(galaxy, 73.9); assert galaxy.director_current == 36 and galaxy.director_target is None
    step(galaxy, .2); assert galaxy.director_target == 7 and 6. <= galaxy.director_duration <= 9.
    unavailable, p = scene(mode='instant'); p.available = False; p.bonk()
    assert not p.bonk_pending; step(unavailable, 50.)
    assert unavailable.director_current == 26 and unavailable.director_target is None

    # Test the real runtime command/snapshot surface without service_capture.
    r = Renderer(seed=6); s = LiveSession(r, config([26, 7], shuffle=False))
    s.playback.available = True; s.playback.start(); step(r, 0.)
    s.command(dict(op='bonk_mode', mode='instant')); s.command(dict(op='bonk')); step(r, 0.)
    assert s.snapshot()['bonk_mode'] == 'instant' and s.snapshot()['transition_progress'] == 0.
    step(r, .36)
    completed = s.snapshot()
    assert completed['transition_complete'] and completed['transition_progress'] == 1. and completed['current'] == 7
    assert 'bonk_mode' not in s.playback.config
    callbacks = {}
    with patch('glfw.set_key_callback', side_effect=lambda window, fn: callbacks.update(key=fn)), \
         patch('glfw.set_window_focus_callback', side_effect=lambda window, fn: callbacks.update(focus=fn)):
        install_keys(r, s)
    with patch.object(s.playback, 'bonk', wraps=s.playback.bonk) as bonk:
        callbacks['key'](None, glfw.KEY_SPACE, 0, glfw.PRESS, 0)
        callbacks['key'](None, glfw.KEY_SPACE, 0, glfw.REPEAT, 0)
        callbacks['key'](None, glfw.KEY_SPACE, 0, glfw.PRESS, 0)
        assert bonk.call_count == 1
    s.playback.pause(); assert not s.playback.bonk_pending and not s.playback.bonk_expedite

    with ExitStack() as guard, tempfile.TemporaryDirectory() as temporary:
        for target in ('renderer.Renderer.create', 'capture.AudioCapture.__init__',
                       'capture.list_sources', 'capture.SourceEnumerator.request', 'player.subprocess.Popen'):
            guard.enter_context(patch(target, side_effect=AssertionError('Offline check attempted '+target)))
        guard.enter_context(patch.object(player.Player, 'refresh'))
        root = tk.Tk(); root.withdraw(); app = player.Player(root, Path(temporary))
        try:
            root.update(); assert root.state() == 'withdrawn' and app.bonk_mode.get() == 'Normal'
            assert tuple(app.bonk_mode_box['values']) == ('Normal', 'Instant')
            source = dict(kind='loopback', id='offline-fixture', name='Offline fixture')
            app.receive_sources([source]); app.set_selected_source(source)
            app.bonk_mode.set('Instant')
            with patch('player.subprocess.Popen'), patch('player.threading.Thread'):
                app.start()
                initial = app.outgoing.get_nowait()
                assert initial['bonk_mode'] == 'instant' and initial['source'] == source
                assert 'bonk_mode' not in app.settings
                assert str(app.bonk_mode_box['state']) == 'disabled'
            app.process = None; app.outgoing = None; app.initializing = False
            app.bonk_mode.set('Normal')
            app.process = SimpleNamespace()  # marks UI ready; no child exists
            state = dict(completed, target=26, current=7, transition_complete=False,
                         transition_progress=.4, transition_id=r.director_recipe)
            app.receive(dict(state=state)); assert str(app.bonk_button['state']) == 'disabled'
            settings_before = dict(app.settings)
            with patch.object(app, 'send') as send:
                app.bonk_mode.set('Instant'); app.change_bonk_mode()
                assert send.call_args.args == ('bonk_mode',) and send.call_args.kwargs['mode'] == 'instant'
                assert str(app.bonk_button['state']) == 'normal'
                app.bonk_button.invoke()
                assert send.call_args.args == ('bonk',) and send.call_args.kwargs['mode'] == 'instant'
                app.text_focus = lambda: False
                event = SimpleNamespace(keysym='space', state=0)
                send.reset_mock(); app.key_press(event); app.key_press(event)
                assert send.call_count == 1 and send.call_args.kwargs['mode'] == 'instant'
                app.key_release(event); app.text_focus = lambda: True; app.key_press(event)
                assert send.call_count == 1
                with patch.object(root, 'focus_displayof', return_value=None): app.focus_check()
                assert send.call_args.args == ('release_focus',)
            assert app.settings == settings_before and 'bonk_mode' not in player.load_settings(Path(temporary)/'settings.json')
            app.receive(dict(state=dict(state, transition_progress=.9999)))
            assert '99%' in app.phase.get() and '100%' not in app.phase.get()
            app.receive(dict(state=completed)); assert '100%' in app.phase.get()
            app.receive(dict(state=dict(completed, paused=True))); assert str(app.bonk_button['state']) == 'disabled'
            app.receive(dict(state=dict(completed, running=False))); assert str(app.bonk_button['state']) == 'disabled'
            app.initializing = True; app.update_controls()
            assert str(app.bonk_button['state']) == str(app.bonk_mode_box['state']) == 'disabled'
            assert root.state() == 'withdrawn'
        finally:
            app.process = None; app.close()
    baseline_label = 'Normal baseline/RNG/recipe/uniform equality' if baseline.is_file() else 'Normal duration range (baseline file absent)'
    print('PASS: '+baseline_label+'; Instant .35s; active retiming without progress jump; '
          'monotonic completion100, bounded repeats, held arrival/Pause/Stop, solo/duplicate/subset/queue, '
          'automatic/Galaxy74 preserved, runtime/output/panel controls, session-only mode. No real GPU/audio/UI/device use.')
    return dict(evidence_class='controlled-clock/director and withdrawn/mocked UI',
                baseline_compared=baseline.is_file(), instant_target_seconds=INSTANT_BONK_SECONDS,
                new_handoff_progress=progress, expedited_handoff_progress=samples,
                expedite_start_progress=before[0], retimed_duration=retimed[0], retimed_origin=retimed[1],
                remaining_tail_target_seconds=INSTANT_BONK_SECONDS,
                completed_progress=completed['transition_progress'], completion_indicator='100%',
                shader_readiness_tested=False, actual_gpu_audio_tested=False)


if __name__ == '__main__':
    import sys
    if '--bonk-restart-test' in sys.argv:
        bonk_restart_tests()
    elif '--instant-bonk-test' in sys.argv:
        instant_bonk_tests()
    else:
        model_tests();runtime_tests();capture_tests();ui_tests()
