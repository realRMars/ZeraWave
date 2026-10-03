"""Offline inline/COM/enumeration/logging checks. No real audio API calls."""
import ast
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Must precede imports: even SoundCard's real module initializer is excluded.
def forbidden_audio(*args, **kw):
    raise AssertionError('Offline test attempted a real audio backend operation')
sys.modules['soundcard'] = SimpleNamespace(all_microphones=forbidden_audio, default_speaker=forbidden_audio)
import player
import capture
from capture import SourceEnumerator, AudioCapture, backend_thread
from player_log import SessionLog, MAX_BYTES, MAX_SESSIONS, source_binding
import player_capture_recovery_test as recovery

A = dict(kind='loopback', id='output-headset', name='Shared headset')
M = dict(kind='microphone', id='input-headset', name='Shared headset')
B = dict(kind='loopback', id='output-monitor', name='Monitor output')
CHECKS = []


def wait_for(condition, seconds=2.):
    limit=time.perf_counter()+seconds
    while not condition():
        if time.perf_counter()>limit:raise AssertionError('Offline completion timeout')
        time.sleep(.005)


def check(name, fn):
    started=time.perf_counter();fn()
    CHECKS.append(dict(name=name,result='PASS',seconds=time.perf_counter()-started,
                       evidence_class='offline widgets/fake endpoint backend; no live audio/GPU'))
    print('PASS:',name)


class OfflineEnumerator:
    def __init__(self):self.token=0;self.result=None;self.closed=False
    def request(self):self.token+=1;return self.token
    def snapshot(self):return self.result
    def complete(self,sources,error=None,token=None):self.result=dict(token=self.token if token is None else token,sources=sources,error=error)
    def close(self):self.closed=True


class Root:
    def __init__(self):self.scheduled=[]
    def after(self,*args):self.scheduled.append(args)


def panel():
    app=recovery.panel();app.desired_source=dict(A);app.options={};app.enumerator=OfflineEnumerator()
    app.enum_token=app.enum_seen=0;app.enumeration_notice=None;app.root=Root()
    app.log.last_error=None;app.started_at=None
    return app


def inline_rules():
    assert player.source_label(A).startswith('System audio (loopback)')
    assert player.source_label(M).startswith('Microphone')
    for running,paused in [(True,False),(True,True),(False,False)]:
        app=panel();app.state.update(running=running,paused=paused,capture_owner=running)
        old=dict(app.settings),dict(app.state)
        app.receive(dict(sources=[A,M,B]));app.send.assert_not_called()
        assert len(app.devices.options['values'])==3 and app.devices.options['state']=='readonly'
        app.refresh();app.refresh();app.enumerator.complete([A,M,B]);app.drain_enumeration()
        app.set_selected_source(M);app.source_changed();app.set_selected_source(A)
        app.device.set(next(k for k,v in app.options.items() if v==B))
        app.source_changed(None)  # Quiet/programmatic index change is not a commit.
        assert app.desired_source==A and not app.send.called
        app.source_changed(SimpleNamespace(widget=object()))
        assert not app.send.called
        app.source_changed(SimpleNamespace(widget=app.devices))
        app.send.assert_called_once_with('switch_source',source=B)
        assert app.desired_source==B and app.settings==old[0] and app.state==old[1]
        app.persist.assert_not_called()
        app.receive(dict(source_working=A,generation=5));app.persist.assert_not_called()
        app.receive(dict(source_working=B,generation=5));app.persist.assert_called_once()
        assert app.settings['source']==B
    app=panel();app.receive(dict(sources=[M,B]))
    assert app.selected_source()==A and '(unavailable)' in app.device.get()
    assert app.settings['source']==recovery.A and not app.send.called
    app.desired_source=None;app.receive(dict(sources=[A,M,B]))
    assert not app.device.get() and app.selected_source() is None and not app.send.called
    app=panel();app.receive(dict(sources=[A,B]));app.send.return_value=False
    app.device.set(next(k for k,v in app.options.items() if v==B));app.source_changed(SimpleNamespace(widget=app.devices))
    assert app.selected_source()==A and app.settings['source']==recovery.A
    assert 'not submitted' in app.status.get()
    app=panel();app.initializing=True;app.outgoing=player.queue.Queue(maxsize=64);app.serial=0
    assert player.Player.send(app,'switch_source',source=B)
    assert app.outgoing.get_nowait()['op']=='switch_source'
    assert not player.Player.send(app,'start')
    app=panel();app.state.update(capture_state='exhausted',capture_owner=False,paused=True)
    app.update_controls();assert app.start_button.options['text']=='Retry'
    app.start();app.send.assert_called_once_with('retry');assert app.state['paused']


def reliable_gui_delivery():
    app=panel();app.receive(dict(sources=[A,B]));before=dict(app.options)
    app.refresh();app.enumerator.complete([],error='COM initialization failed: fake HRESULT')
    app.drain_enumeration();assert app.options==before and 'failed' in app.status.get()
    app.log.record.assert_any_call('enumeration_error',runtime_session=None,error='COM initialization failed: fake HRESULT',token=1)
    app.refresh();app.enumerator.complete([]);app.drain_enumeration()
    assert 'No available' in app.status.get() and app.desired_source==A
    app=panel();app.refresh();old=app.enum_token;app.refresh();app.enumerator.complete([M],token=old)
    app.drain_enumeration();assert app.enum_seen==0 and app.refreshing
    app.enumerator.complete([A,M,B]);app.drain_enumeration();assert app.enum_seen==app.enum_token
    # Fill the normal queue. Enumeration never goes through that queue.
    app=panel();app.refresh()
    for _ in range(128):app.events.put_nowait(dict(ignored=True))
    app.enumerator.complete([A,M,B]);app.poll()
    assert len(app.options)==3 and not app.refreshing and not app.send.called
    assert app.root.scheduled and app.root.scheduled[-1][0]==80
    app=panel();app.events.put(dict(broken=True));app.events.put(dict(good=True))
    original=app.receive;seen=[]
    def receive(value):
        if 'broken' in value:raise RuntimeError('Injected widget receiver failure')
        seen.append(value);original(value)
    app.receive=receive;app.poll()
    assert seen==[dict(good=True)] and app.root.scheduled
    app.log.record.assert_any_call('gui_receiver_error',runtime_session=None,error='Injected widget receiver failure',keys=['broken'])
    app=panel();app.refresh();app.enumerator.complete([dict(kind='bad')]);app.poll()
    assert 'update failed' in app.status.get() and app.root.scheduled
    app.closing=True;count=len(app.root.scheduled);app.enumerator.complete([B]);app.poll()
    assert len(app.root.scheduled)==count and not app.send.called


def enum_ownership_and_com():
    entered=threading.Event();finish=threading.Event();calls=[];ownership=[]
    @contextlib.contextmanager
    def owned_context():
        ownership.append(('init',threading.get_ident()))
        try:yield
        finally:ownership.append(('close',threading.get_ident()))
    def enum():
        calls.append(threading.get_ident())
        if len(calls)==1:entered.set();assert finish.wait(2.);return [M]
        return [A,M,B]
    worker=SourceEnumerator(enum,owned_context)
    token=worker.request();assert entered.wait(2.)
    for _ in range(30):token=worker.request()
    assert worker.worker.is_alive() and len(calls)==1
    finish.set();wait_for(lambda:worker.snapshot() is not None and worker.snapshot()['token']==token)
    assert worker.snapshot()['sources']==[A,M,B] and len(calls)==2
    worker.close();worker.worker.join(2.)
    assert len(ownership)==2 and ownership[0][1]==ownership[1][1] and len(set(calls))==1
    entered.clear();finish.clear()
    def late_enum():entered.set();assert finish.wait(2.);return [A]
    worker=SourceEnumerator(late_enum,owned_context);worker.request();assert entered.wait(2.)
    worker.close();finish.set();worker.worker.join(2.);assert worker.snapshot() is None
    worker=SourceEnumerator(lambda:(_ for _ in ()).throw(RuntimeError('fake enumerate failure')),contextlib.nullcontext)
    worker.request();wait_for(lambda:worker.snapshot() is not None)
    assert worker.snapshot()['sources']==[] and worker.snapshot()['error']=='fake enumerate failure'
    worker.close();worker.worker.join(2.)
    attempts=[]
    @contextlib.contextmanager
    def flaky_context():
        attempts.append(threading.get_ident())
        if len(attempts)==1:raise RuntimeError('fake COM startup failure')
        yield
    worker=SourceEnumerator(lambda:[A],flaky_context);worker.request()
    wait_for(lambda:worker.snapshot() is not None)
    assert worker.snapshot()['error']=='fake COM startup failure' and worker.worker.is_alive()
    token=worker.request();wait_for(lambda:worker.snapshot()['token']==token and not worker.snapshot()['error'])
    assert worker.snapshot()['sources']==[A] and len(set(attempts))==1
    worker.close();worker.worker.join(2.)
    for hr in (0,1,0x80004005):
        ole=SimpleNamespace(CoInitializeEx=Mock(return_value=hr),CoUninitialize=Mock())
        with patch('capture.ctypes.WinDLL',return_value=ole):
            try:
                with backend_thread():pass
            except RuntimeError:
                assert hr==0x80004005
            else:assert hr in (0,1)
        ole.CoInitializeEx.assert_called_once_with(None,0)
        assert ole.CoUninitialize.call_count==int(hr in (0,1))


def resolved_identity_and_config():
    mic=SimpleNamespace(id=M['id'],name=M['name'],isloopback=False)
    output=SimpleNamespace(id=A['id'],name=A['name'],isloopback=True)
    with patch('capture.sc.all_microphones',return_value=[mic,output]) as listing, patch.object(capture.sc,'default_speaker',side_effect=forbidden_audio):
        c=AudioCapture(A['id'],source_kind='loopback',exact_id=True)
        assert c.find_device() is output and c.resolved==A
        c=AudioCapture(M['id'],source_kind='microphone',exact_id=True)
        assert c.find_device() is mic and c.resolved==M
        for endpoint,kind in [(A['id'],'microphone'),(M['id'],'loopback'),('Shared headset','loopback')]:
            try:AudioCapture(endpoint,source_kind=kind,exact_id=True).find_device()
            except RuntimeError:pass
            else:raise AssertionError('Wrong kind/friendly-name fallback')
        recorder=SimpleNamespace(__enter__=Mock(),record=Mock(return_value=[]),__exit__=Mock())
        output.recorder=Mock(return_value=recorder)
        c=AudioCapture(A['id'],source_kind='loopback',exact_id=True,owner_generation=7);c.start();c.read();c.stop()
        output.recorder.assert_called_once_with(samplerate=48000,channels=2)
        recorder.record.assert_called_once_with(numframes=2048)
        recorder.__exit__.assert_called_once()
        assert c.resolved==A


def bounded_session_history():
    with tempfile.TemporaryDirectory(prefix='zerawave-inline-logs-') as folder:
        root=Path(folder);legacy=root/'player.log';legacy.write_bytes(b'preserve physical failure\n')
        first=SessionLog(root,'1'*32);first.record('requested',source=M);first.close()
        first_path=first.path;first_bytes=first.path.read_bytes()
        second=SessionLog(root,'2'*32);second.record('requested',source=A);second.close()
        assert first_path.read_bytes()==first_bytes and legacy.read_bytes()==b'preserve physical failure\n'
        rows=[json.loads(x) for x in second.path.read_text(encoding='utf-8').splitlines()]
        assert {x['session'] for x in rows}=={'2'*32} and any(x['event']=='requested' for x in rows)
        assert all(x['PID']==os.getpid() and x['UTC'].endswith('+00:00') for x in rows)
        third=SessionLog(root,'3'*32)
        for i in range(100):assert third.record('offline_rotation',ordinal=i,text='色'*2400)
        paths=[third.path]+[Path(str(third.path)+f'.{i}') for i in (1,2)]
        assert all(p.stat().st_size<=MAX_BYTES for p in paths if p.exists())
        assert len([p for p in paths if p.exists()])==3
        with patch.object(third.handler,'emit',side_effect=OSError('fake log IO failure')):
            assert not third.record('failed') and third.last_error=='fake log IO failure'
        third.close()
        for i in range(5):log=SessionLog(root);log.record('session',ordinal=i);log.close()
        assert len(log.bases())<=MAX_SESSIONS and legacy.read_bytes()==b'preserve physical failure\n'
        # Live lease deletion must fail on Windows, preventing cross-process prune races.
        active=SessionLog(root)
        try:active.lease_path.unlink()
        except PermissionError:pass
        else:raise AssertionError('Live log lease was deletable')
        active.close()
        # Four live owners are retained; the fifth must not exceed the bound.
        owners=[SessionLog(root) for _ in range(MAX_SESSIONS)]
        try:
            try:SessionLog(root)
            except RuntimeError as exc:assert 'busy' in str(exc)
            else:raise AssertionError('Fifth active session was admitted')
            assert len(owners[0].bases())==MAX_SESSIONS
        finally:
            for log in owners:log.close()
        # The allocation lock is nonblocking, even across independent owners.
        from player_log import allocation_lock
        with allocation_lock(root/'logs'):
            try:SessionLog(root)
            except RuntimeError as exc:assert 'another player' in str(exc)
            else:raise AssertionError('Concurrent allocator ignored the lock')
        # An abandoned lease without its base still consumes a discoverable slot.
        abandoned=root/'logs'/('session-20000101T000000000000Z-'+'0'*32+'.jsonl.lease')
        abandoned.write_text('crashed fake owner',encoding='utf-8')
        next_log=SessionLog(root)
        assert not abandoned.exists() and len(next_log.bases())<=MAX_SESSIONS
        next_log.close()
        if len(sys.argv)>1:
            (Path(sys.argv[1])/'synthetic-session-history.json').write_text(json.dumps(dict(
                class_='actual local SessionLog files with synthetic endpoint events, no player/audio runtime',
                legacy_preserved=True,first_session=[json.loads(x) for x in first_bytes.decode('utf-8').splitlines()],
                second_session=rows,max_bytes_per_file=MAX_BYTES,max_session_sets=MAX_SESSIONS),indent=2),encoding='utf-8')
    binding=source_binding(player.ROOT,['app/player.py'],{'Player.source_changed':player.Player.source_changed})
    assert len(binding['loaded_functions']['Player.source_changed'])==64


def offline_tk_evidence(out):
    """Actual Tk, fake enumeration/commands. Hidden window, no focus or capture."""
    import tkinter as tk
    with tempfile.TemporaryDirectory(prefix='zerawave-offline-inline-ui-') as folder, patch('player.SourceEnumerator',OfflineEnumerator):
        config=dict(player.defaults(player.LIVE_FORMS),source=A)
        player.save_settings(Path(folder)/'settings.json',config)
        root=tk.Tk();root.withdraw();app=player.Player(root,folder)
        app.root.title('ZeraWave · Offline inline-source evidence')
        calls=[];app.send=lambda op,**kw:(calls.append(dict(op=op,**kw)) or True)
        try:
            app.enumerator.complete([A,M,B]);app.poll();root.update_idletasks()
            assert len(app.devices['values'])==3 and str(app.devices['state'])=='readonly'
            assert not calls and app.selected_source()==A
            before=list(app.devices['values'])
            app.set_selected_source(M);app.set_selected_source(A);root.update();assert not calls
            app.state.update(running=True,paused=True,held=True,capture_owner=True)
            app.process=object()  # Simulated active child; send is an offline collector.
            app.update_controls()
            app.device.set(next(k for k,v in app.options.items() if v==B))
            # Actual Tk binding delivery; this is a simulated commit, not physical input.
            app.devices.event_generate('<<ComboboxSelected>>');root.update()
            assert calls==[dict(op='switch_source',source=B)] and app.state['paused']
            assert player.load_settings(Path(folder)/'settings.json')['source']==A
            app.refresh();app.enumerator.complete([A,M,B]);app.poll();root.update_idletasks()
            assert len(calls)==1
            widgets=[dict(class_=w.winfo_class(),text=str(w.cget('text')) if 'text' in w.keys() else '') for w in app.box.winfo_children()]
            evidence=dict(class_='actual hidden Tk widgets + offline endpoints/commands; no device/GPU/focus/physical input',
                          values=before,selected_after_commit=app.device.get(),desired=app.desired_source,
                          saved=player.load_settings(Path(folder)/'settings.json')['source'],paused=app.state['paused'],
                          commands=calls,source_state=str(app.devices['state']),refresh_state=str(app.refresh_button['state']),
                          mapped=root.winfo_ismapped(),extra_dialog_buttons=hasattr(app,'change_button'),widgets=widgets)
            (out/'offline-ui.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
            # Export a clearly labelled schematic using the observed widget values.
            import html
            labels=''.join(f'<text x="22" y="{95+i*32}" fill="#e3eaf4" font-family="Segoe UI" font-size="16">{html.escape(v)}</text>' for i,v in enumerate(before))
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="250"><rect width="920" height="250" fill="#141a28"/><text x="22" y="35" fill="#e3eaf4" font-family="Segoe UI" font-size="23">Offline inline chooser — observed Tk values</text><text x="22" y="62" fill="#a6b7ce" font-size="13">Schematic export; hidden widgets, fake endpoints, no desktop/audio capture</text>{labels}<text x="22" y="220" fill="#a6b7ce" font-size="14">Simulated user commit to monitor; Pause retained; saved source unchanged</text></svg>'
            (out/'offline-inline.svg').write_text(svg,encoding='utf-8')
        finally:
            app.process=None
            app.close()
            (out/'offline-ui-session.jsonl').write_bytes(app.log.path.read_bytes())


if __name__=='__main__':
    out=Path(sys.argv[1]) if len(sys.argv)>1 else None
    check('inline labels, zero-capture quiet operations, deliberate commits and preserved prefs/intent',inline_rules)
    check('dedicated completion slot/full queue, errors/empty/stale results and resilient GUI poll',reliable_gui_delivery)
    check('one coalescing worker, balanced mocked COM ABI, errors and late teardown',enum_ownership_and_com)
    check('resolved kind/ID vs same friendly name, no fallback, unchanged recording configuration',resolved_identity_and_config)
    check('two-session preservation, UTF-8 byte rotation, four-set history and live lease protection',bounded_session_history)
    if out:
        check('actual hidden Tk inline population and simulated selection path with offline data',lambda:offline_tk_evidence(out))
        (out/'inline-checks.json').write_text(json.dumps(CHECKS,indent=2),encoding='utf-8')
