"""Standalone synthetic recovery/ownership/UI-contract checks; no device or GL opens."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import json
import contextlib
import io
import threading
import time
import sys
import tempfile

import numpy as np
import player
import player_runtime as runtime
from player_state import defaults
from renderer import Renderer, LIVE_FORMS
from audio_frame import AudioFrame
from capture_stream import CaptureStream

A = dict(kind='loopback', id='headset-exact', name='Blue headset')
B = dict(kind='loopback', id='other-exact', name='Other output')
CHECKS = []
TRACE = []


def check(name, function):
    started = time.perf_counter()
    function()
    CHECKS.append(dict(name=name, result='PASS', seconds=time.perf_counter()-started,
                       evidence_class='synthetic/fake backend; no audio device or GPU'))
    print('PASS:', name)


class Clock:
    def __init__(self): self.now = 1000.
    def advance(self, seconds=.05): self.now += seconds


class Watch:
    def __init__(self): self.revision=0; self.sources=[A]; self.error=None; self.refreshes=0
    def snapshot(self): return self.revision, list(self.sources), self.error
    def refresh(self): self.revision+=1; self.refreshes+=1
    def change(self, sources, error=None): self.sources=sources; self.error=error; self.revision+=1
    def close(self): pass


class Stream:
    def __init__(self, factory, generation, error=None, blocked=False, close_error=None):
        self.factory=factory; self.generation=generation; self.error=error
        self.blocked=blocked; self.close_error=close_error; self.alive=False
        self.released=False; self.frames=[]; self.analyzed=0; self.last_packet=None
        self.last_read=None; self.stop_requested=False
    def start(self):
        assert not any(x.alive or not x.released for x in self.factory.created[:-1]), 'Second capture owner'
        self.alive=True
    def request_stop(self):
        self.stop_requested=True; self.frames=[]
        if not self.blocked:
            self.alive=False; self.released=self.close_error is None
    def drain(self):
        if self.error: raise RuntimeError('Fake capture failed') from self.error
        rows=self.frames; self.frames=[]; return rows
    def health(self):
        return dict(alive=self.alive,released=self.released,close_error=self.close_error,
                    last_packet_at=self.last_packet,last_read_at=self.last_read)
    def feed(self, clock, level=.3, hit=False, stamp=None):
        frame=AudioFrame(level,level*.7,level*.5,int(hit),int(hit),int(hit),flux=level)
        frame.beat_tick=hit; frame.beat_confidence=.8
        self.last_read=self.last_packet=clock.now if stamp is None else stamp
        self.frames.append((self.last_packet,(np.zeros((2048,2)),frame))); self.analyzed+=1


class Factory:
    def __init__(self): self.created=[]; self.plans=[]; self.sources=[]
    def __call__(self,capture,analyze,**kw):
        self.sources.append(capture)
        assert capture['exact_id'] is True
        plan=self.plans.pop(0) if self.plans else {}
        stream=Stream(self,kw['generation'],**plan); self.created.append(stream); return stream


class Harness:
    def __enter__(self):
        self.clock=Clock(); self.watch=Watch(); self.factory=Factory(); self.events=[]
        self.patches=[patch('player_runtime.time.perf_counter',side_effect=lambda:self.clock.now),
                      patch('player_runtime.DeviceWatch',return_value=self.watch),
                      patch('player_runtime.AudioCapture',side_effect=lambda **kw:kw),
                      patch('player_runtime.CaptureStream',side_effect=self.factory),
                      patch('player_runtime.emit',side_effect=lambda **kw:self.events.append(kw))]
        for p in self.patches:p.start()
        self.renderer=Renderer(seed=6); self.renders=[]
        def render(clock):
            old=self.renderer.last_render_time
            self.renderer.update_blend(clock,0. if old is None else clock-old)
            self.renderer.last_render_time=clock
            self.renders.append((clock,self.renderer.parameters.impact))
        self.renderer.render=render; self.renderer.swap_buffers=lambda:None
        config=dict(defaults(LIVE_FORMS),queue=[26,7,7],shuffle=False,loop=False,source=A)
        self.session=runtime.LiveSession(self.renderer,config)
        self.session.tick(self.clock.now)  # Existing renderer creates its opening world once.
        return self
    def __exit__(self,*args):
        TRACE.append(dict(events=self.events[-32:], event_count=len(self.events), final_state=self.session.snapshot(),
                          capture_instances=len(self.factory.created),
                          opened_sources=self.factory.sources,
                          enum_refreshes=self.watch.refreshes,
                          class_='synthetic; fake endpoint snapshots/clock/capture, CPU director'))
        for p in reversed(self.patches):p.stop()
    def tick(self,seconds=.05): self.clock.advance(seconds); return self.session.tick(self.clock.now)
    def start(self):
        self.session.start(); self.tick(); return self.factory.created[-1]
    def working(self,level=.3):
        stream=self.start(); stream.feed(self.clock,level); self.tick(); return stream


def same_identity_and_silence():
    with Harness() as h:
        s=h.session; stream=h.working(0.)
        assert s.source_verified and s.playback.available and s.capture_state=='capturing'
        for _ in range(100): stream.feed(h.clock,0.); h.tick(.2)
        assert len(h.factory.created)==1 and not stream.stop_requested
        s.playback.hold('panel.Shift_L',True)
        s.playback.configure(dict(s.playback.config,queue=[7,26]),26)
        s.playback.bonk_pending=True
        before=(h.renderer.director_current,h.renderer.director_target,h.renderer.director_time,
                s.playback.index,s.playback.pending_config,s.playback.bonk_pending)
        h.watch.change([]); h.tick()
        assert s.playback.running and s.playback.held and not s.playback.available
        for _ in range(10):h.tick(.1)
        assert (h.renderer.director_current,h.renderer.director_target,h.renderer.director_time,
                s.playback.index,s.playback.pending_config,s.playback.bonk_pending)==before
        assert h.renderer.parameters.scale==0.
        wrong_id=dict(A,id='new-profile'); wrong_kind=dict(A,kind='microphone')
        h.watch.change([wrong_id,wrong_kind]); h.tick(5.)
        assert len(h.factory.created)==1 and s.capture_state=='unavailable'
        h.watch.change([A]); h.tick()
        replacement=h.factory.created[-1]
        assert replacement is not stream and stream.released
        replacement.feed(h.clock,0.); h.tick()
        assert s.playback.available and s.source==A and s.playback.held
        assert h.watch.refreshes>=2


def pause_recovery_and_fresh_resume():
    with Harness() as h:
        s=h.session; old=h.working()
        s.command(dict(op='hold',owner='custom',active=True))
        # Freeze an in-flight transition, not only a held opening world.
        s.command(dict(op='bonk')); old.feed(h.clock); h.tick()
        assert h.renderer.director_target==7
        s.command(dict(op='pause'))
        before=(len(h.renders),s.clock,h.renderer.director_time,h.renderer.director_current,
                h.renderer.director_target,dict(h.renderer.blend_values),s.playback.index)
        old.error=RuntimeError('Endpoint invalidated'); h.tick()
        h.tick(20.)
        replacement=h.factory.created[-1]
        replacement.feed(h.clock,.9,True); h.tick()
        assert s.playback.paused and s.playback.held and s.playback.running
        assert (len(h.renders),s.clock,h.renderer.director_time,h.renderer.director_current,
                h.renderer.director_target,dict(h.renderer.blend_values),s.playback.index)==before
        replacement.feed(h.clock,.99,True)  # Before Resume; must never be presented.
        h.clock.advance(.1); s.command(dict(op='pause')); h.tick()
        assert len(h.renders)==before[0]
        replacement.feed(h.clock,.2,True); h.tick(.02)
        assert len(h.renders)==before[0]+1 and s.clock-before[1]<.03
        assert h.renderer.parameters.scale==.2 and h.renderer.parameters.impact==0.
        assert not h.renderer.parameters.beat_tick and s.playback.held


def error_starvation_deadworker_and_budget():
    for problem in ('error','dead','starve','open'):
        with Harness() as h:
            stream=h.start() if problem=='open' else h.working()
            if problem=='error':stream.error=RuntimeError('read failed')
            elif problem=='dead':stream.alive=False;stream.released=True
            elif problem=='starve':
                h.tick(.2); assert not stream.stop_requested  # Empty drain is normal.
            h.tick(5.1 if problem=='open' else 2.1)
            assert stream.stop_requested and h.session.playback.running
            assert h.session.capture_error and not h.session.playback.available
    with Harness() as h:
        h.factory.plans=[dict(error=RuntimeError('open failed')) for _ in range(6)]
        h.start()
        for _ in range(80): h.tick(.5)
        assert len(h.factory.created)==5 and h.session.capture_state=='exhausted'
        h.watch.refresh(); h.tick(10.)
        assert len(h.factory.created)==5  # Enumeration alone never resets exhaustion.
        h.session.playback.pause(); h.session.retry(); h.tick()
        assert len(h.factory.created)==6 and h.session.playback.paused
    with Harness() as h:
        h.factory.plans=[dict(error=RuntimeError('open failed')) for _ in range(5)]
        h.start()
        for _ in range(80):h.tick(.5)
        h.watch.change([]);h.tick();h.watch.change([A]);h.tick()
        assert len(h.factory.created)==6  # Later genuine absent → present remains recognizable.
    with Harness() as h, patch('player_runtime.AudioCapture',side_effect=RuntimeError('constructor failed')):
        h.session.start()
        for _ in range(80):h.tick(.5)
        assert not h.factory.created and h.session.capture_state=='exhausted'
        assert h.session.playback.running and h.session.attempts==5


def cancellation_and_single_owner():
    with Harness() as h:
        h.factory.plans=[dict(blocked=True)]
        old=h.start(); h.session.stop(); stopped_generation=h.session.generation
        assert h.session.capture_state=='releasing' and not h.session.playback.running
        h.watch.change([A]);h.tick(30.)
        assert len(h.factory.created)==1 and h.session.stream is old
        # A late open/read completion after Stop cannot publish or restart.
        old.feed(h.clock,.99,True);old.alive=False;old.released=True
        h.tick();assert h.session.stream is None and h.session.capture_state=='stopped'
        assert h.session.generation==stopped_generation and not h.session.source_verified
        assert not any('source_working' in event for event in h.events)
    with Harness() as h:
        old=h.working();old.blocked=True;old.error=RuntimeError('blocked recorder')
        h.tick();h.tick(10.);h.session.retry();h.tick(10.)
        h.session.select_source(B);h.watch.change([B]);h.tick(10.)
        assert len(h.factory.created)==1 and h.session.stream is old
        assert 'unconfirmed' in h.session.capture_detail
        old.alive=False;old.released=True;h.tick()
        assert len(h.factory.created)==2 and h.factory.created[-1].generation==h.session.generation
        new=h.factory.created[-1];new.feed(h.clock,.2);h.tick()
        assert h.session.source==B and h.session.playback.available
    with Harness() as h:
        old=h.working();old.close_error=RuntimeError('context exit failed')
        h.session.select_source(B);h.watch.change([B]);h.tick(30.)
        assert len(h.factory.created)==1 and h.session.capture_state=='releasing'
        assert 'release failed' in h.session.capture_detail
    with Harness() as h:
        old=h.working();old.error=RuntimeError('read failed');h.tick();h.tick()
        h.session.stop();h.tick(60.)
        assert len(h.factory.created)==1 and not h.session.playback.running
    with Harness() as h:
        h.watch.refresh=lambda:None  # Enumeration is pending, then completes after Stop.
        h.session.start();h.tick();h.session.stop();h.watch.change([A]);h.tick()
        assert not h.factory.created and not h.session.playback.running


class Value:
    def __init__(self,*args,value='',**kw): self.value=value
    def get(self):return self.value
    def set(self,value):self.value=value


class Widget:
    def __init__(self,*args,**kw):self.options=kw;self.destroyed=False
    def configure(self,**kw):self.options.update(kw)
    def pack(self,*args,**kw):pass
    def bind(self,*args,**kw):pass
    def title(self,*args):pass
    def geometry(self,*args):pass
    def transient(self,*args):pass
    def protocol(self,*args):pass
    def destroy(self):self.destroyed=True


class ImmediateThread:
    def __init__(self,target,**kw):self.target=target
    def start(self):self.target()
    def is_alive(self):return False


def panel():
    app=player.Player.__new__(player.Player)
    app.initializing=False;app.refreshing=False;app.closing=False
    app.desired_source=dict(A);app.active_source=dict(A);app.enumeration_notice=None
    app.enum_token=app.enum_seen=0;app.runtime_session=None;app.log=Mock()
    app.root=object();app.options={'a':A};app.device=Value(value='a');app.status=Value()
    app.settings=dict(defaults(LIVE_FORMS),queue=[26,7],source=A)
    app.state=dict(running=True,paused=False,held=True,listening=True,capture_owner=True,generation=1)
    app.queue_ids=[26,7];app.process=object();app.events=player.queue.Queue(maxsize=128)
    for name in ('devices','start_button','stop_button','pause_button','hold_button','bonk_button','refresh_button','change_button','retry_button'):
        setattr(app,name,Widget())
    app.persist=Mock();app.send=Mock(return_value=True)
    return app


def inline_selection_and_preferences():
    for running,paused in [(True,False),(True,True),(False,False)]:
        app=panel();app.state.update(running=running,paused=paused,capture_owner=running)
        before=dict(app.settings),dict(app.state)
        app.receive(dict(sources=[A,B]));app.send.assert_not_called()
        app.set_selected_source(B);app.source_changed();app.send.assert_not_called()
        app.set_selected_source(A)
        app.device.set(next(k for k,v in app.options.items() if v==B))
        app.source_changed(SimpleNamespace(widget=app.devices))
        assert app.selected_source()==B and app.state==before[1] and app.settings['source']==A
        app.send.assert_called_once_with('switch_source',source=B);app.persist.assert_not_called()
        app.receive(dict(source_working=A,generation=2));app.persist.assert_not_called()
        app.receive(dict(source_working=B,generation=0));app.persist.assert_not_called()
        app.receive(dict(source_working=B,generation=2));app.persist.assert_called_once()
        assert app.settings['source']==B
    app=panel();app.receive(dict(sources=[A,B]));app.send.return_value=False
    app.device.set(next(k for k,v in app.options.items() if v==B))
    app.source_changed(SimpleNamespace(widget=app.devices))
    assert app.selected_source()==A and app.settings['source']==A
    app=panel();app.receive(dict(sources=[dict(A,id='same-name-new-id'),dict(A,kind='microphone')]))
    assert app.selected_source()==A and '(unavailable)' in app.device.get()
    with tempfile.TemporaryDirectory(prefix='zerawave-recovery-prefs-') as folder:
        path=Path(folder)/'settings.json';app=panel()
        player.save_settings(path,app.settings)
        app.persist=lambda:player.save_settings(path,app.settings)
        app.set_selected_source(B);assert player.load_settings(path)['source']==A
        app.receive(dict(source_working=B,generation=2));assert player.load_settings(path)['source']==B
        app.device.set('')
        relaunched=panel();relaunched.settings=player.load_settings(path);relaunched.desired_source=relaunched.settings['source'];relaunched.options={};relaunched.device.set('')
        relaunched.receive(dict(sources=[A,B]));assert relaunched.selected_source()==B
    for running,paused in [(True,False),(True,True),(False,False)]:
        with Harness() as h:
            old=h.working();s=h.session;s.playback.paused=paused
            if not running:s.stop();h.tick()
            identity=(h.renderer.director_current,h.renderer.director_target,s.playback.index,s.playback.held)
            s.select_source(B);h.watch.change([B]);h.tick();h.tick()
            assert s.playback.running==running and s.playback.paused==paused
            assert (h.renderer.director_current,h.renderer.director_target,s.playback.index,s.playback.held)==identity
            if not running:assert len(h.factory.created)==1 and s.stream is None
            else:
                new=h.factory.created[-1];new.error=RuntimeError('replacement failed');h.tick()
                assert s.source==B and s.playback.running and s.playback.paused==paused


def actual_worker_cancel_and_close():
    # Real Python worker concurrency, fake recorder, no audio backend/device.
    entered=threading.Event();release=threading.Event()
    def blocked_read(**kw):
        entered.set();assert release.wait(1.);return np.zeros((2048,2))
    capture=SimpleNamespace(start=lambda:None,read=blocked_read,stop=Mock())
    stream=CaptureStream(capture,lambda pcm:pcm,generation=9);stream.start()
    assert entered.wait(1.)
    started=time.perf_counter();stream.request_stop()
    assert time.perf_counter()-started<.1 and stream.health()['alive']
    release.set();stream.worker.join(1.)
    assert not stream.health()['alive'] and stream.health()['released'] and not stream.frames
    capture.stop.assert_called_once()
    # The worker's recorder open can complete after Stop. It must close without a read.
    opening=threading.Event();complete=threading.Event()
    def late_open():opening.set();assert complete.wait(1.)
    capture=SimpleNamespace(start=late_open,read=Mock(),stop=Mock())
    stream=CaptureStream(capture,lambda pcm:pcm);stream.start();assert opening.wait(1.)
    stream.request_stop();complete.set();stream.worker.join(1.)
    assert stream.health()['released'] and not stream.health()['alive']
    capture.read.assert_not_called();capture.stop.assert_called_once()
    capture=SimpleNamespace(start=lambda:None,read=lambda **kw:(_ for _ in ()).throw(RuntimeError('read error')),stop=Mock(side_effect=RuntimeError('close error')))
    stream=CaptureStream(capture,lambda pcm:pcm);stream.start();stream.worker.join(1.)
    assert not stream.health()['alive'] and not stream.health()['released']
    assert str(stream.health()['close_error'])=='close error'


def bounded_watch_and_logs():
    with Harness() as h:
        old=h.working();old.feed(h.clock,.99,True)
        h.session.generation+=1;h.tick()
        assert old.stop_requested and not h.session.playback.available
        assert h.renderer.parameters.impact==0.
        h.tick();assert len(h.factory.created)==2
        late_events=io.StringIO()
        with contextlib.redirect_stderr(late_events):
            for i in range(600):h.session.status('synthetic',str(i))
        assert len(h.session.capture_history)==128 and h.session.capture_log_count>=600
        assert late_events.getvalue().count('CAPTURE STATE ')==600
    # Exercise the actual watcher thread against a blocked fake enumeration.
    entered=threading.Event();finish=threading.Event()
    def enumerate_fake():entered.set();assert finish.wait(1.);return [A]
    with patch('player_runtime.list_sources',side_effect=enumerate_fake) as enumeration, patch('player_runtime.backend_thread',contextlib.nullcontext):
        watch=runtime.DeviceWatch();watch.refresh();assert entered.wait(1.)
        for _ in range(20):watch.refresh()
        assert watch.snapshot()[0]==0 and enumeration.call_count==1
        watch.close();finish.set();watch.thread.join(1.)
        assert not watch.thread.is_alive() and enumeration.call_count==1
        assert watch.snapshot()[1]==[]  # Late result after close is deliberately discarded.


if __name__=='__main__':
    check('exact-ID return, wrong ID/kind refusal, valid silence, Hold/queue/world retention',same_identity_and_silence)
    check('Pause/recovery/transition preservation and fresh Resume without catch-up',pause_recovery_and_fresh_resume)
    check('read/open errors, worker exit, packet starvation, retry exhaustion and genuine return',error_starvation_deadworker_and_budget)
    check('Stop during open/backoff, stale packets, blocked/failed shutdown and single ownership',cancellation_and_single_owner)
    check('Inline user selection vs quiet population, running/paused/stopped, failed switch and successful-only prefs',inline_selection_and_preferences)
    check('real worker with fake backend: nonblocking cancellation and failed release',actual_worker_cancel_and_close)
    check('stale-generation rejection, bounded logs/history and single blocked enumeration worker',bounded_watch_and_logs)
    if len(sys.argv)>1:
        out=Path(sys.argv[1]);out.write_text(json.dumps(CHECKS,indent=2),encoding='utf-8')
        out.with_name('synthetic-state-trace.json').write_text(json.dumps(TRACE,indent=2),encoding='utf-8')
