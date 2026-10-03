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


if __name__ == '__main__':
    model_tests();runtime_tests();capture_tests();ui_tests()
