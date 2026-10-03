"""Final bounded cleanup/transport checks; fake backend, no device/GL/focus."""
import sys
from types import SimpleNamespace
def forbidden(*a,**kw):raise AssertionError('Real audio call forbidden')
sys.modules['soundcard']=SimpleNamespace(all_microphones=forbidden,default_speaker=forbidden)
import contextlib,json,threading,time,tempfile
from pathlib import Path
from unittest.mock import Mock,patch
import player
import player_runtime as runtime
import player_capture_recovery_test as recovery
import capture
from capture_stream import CaptureStream
from wasapi_cleanup import WasapiCleanup
sys.path.insert(0,str(Path(__file__).parent/'audio'))
import wasapi_cleanup_test as cleanup_test

def run(out):
    evidence=[]
    # Use the actual AudioCapture + actual worker + actual cleanup adapter,
    # with controlled fake COM vtables/read packets and endpoint objects.
    for partial in (False,True):
        recorder,ffi,audio,client=cleanup_test.fixture(1,RuntimeError('release uncertain') if partial else None)
        entered=threading.Event();finish=threading.Event()
        recorder.__enter__=lambda:None
        def read(**kw):entered.set();assert finish.wait(2.);return []
        recorder.record=read
        mic=SimpleNamespace(id='headset-exact',name='Blue headset',isloopback=True,recorder=lambda **kw:recorder)
        cap=capture.AudioCapture('headset-exact',exact_id=True)
        with patch('capture.sc.all_microphones',return_value=[mic]),patch('capture.owned_cleanup',side_effect=lambda r:WasapiCleanup(r,ffi)):
            stream=CaptureStream(cap,lambda pcm:pcm);stream.start();assert entered.wait(2.)
            stream.request_stop();finish.set();stream.worker.join(2.)
        h=stream.health();assert not h['alive'] and h['released']==(not partial)
        assert not stream.frames and all(t!=threading.get_ident() for _,t in audio.calls+client.calls)
        # Repeated owner close after a partial release cannot double-free.
        before=len(audio.calls),len(client.calls)
        try:cap.cleanup.close()
        except RuntimeError as exc:assert 'owning worker' in str(exc)
        else:raise AssertionError('Foreign-thread close allowed')
        assert before==(len(audio.calls),len(client.calls))
        evidence.append(dict(case='actual worker late-read/cancel',partial=partial,health={k:str(v) if isinstance(v,Exception) else v for k,v in h.items()},cleanup=cap.cleanup_report))
    # Waiting capture on Start gently renders; Pause alone freezes; blocked
    # owner cannot be replaced by reselect/Start and Stop cancels future opens.
    with recovery.Harness() as h:
        h.factory.plans=[dict(blocked=True,close_error=RuntimeError('release uncertain'))]
        old=h.start();old.error=RuntimeError('device lost');h.tick()
        h.session.stop();h.tick();h.session.select_source(recovery.B);h.watch.change([recovery.B])
        before=(h.renderer.director_current,h.renderer.director_target,h.session.playback.index)
        h.session.start();count=len(h.renders);clock=h.session.clock
        for _ in range(10):assert h.tick(.1)
        assert len(h.renders)>count and h.session.clock>clock and len(h.factory.created)==1
        assert (h.renderer.director_current,h.renderer.director_target,h.session.playback.index)==before
        notice=h.session.snapshot()['restart_notice'];assert notice==runtime.RESTART_NOTICE
        h.session.command(dict(op='pause'));count=len(h.renders);clock=h.session.clock
        h.tick(10.);assert len(h.renders)==count and h.session.clock==clock
        h.session.command(dict(op='pause'));assert h.tick(.01)  # unavailable Resume remains quiet/fresh
        assert h.renderer.parameters.impact==0. and not h.renderer.parameters.beat_tick
        h.session.stop();h.tick(20.);assert not h.session.playback.running and len(h.factory.created)==1
        evidence.append(dict(case='waiting idle vs explicit Pause; no progression/replacement',notice=notice,state=h.session.snapshot()))
    # A Stop failure can still prove reference cleanup; confirmation alone is
    # insufficient until the old worker has actually exited.
    with recovery.Harness() as h:
        old=h.working();old.blocked=True;h.session.select_source(recovery.B);h.watch.change([recovery.B])
        old.released=True;h.tick();assert len(h.factory.created)==1
        old.alive=False;h.tick();assert len(h.factory.created)==2
        h.session.stop();h.tick(30.);assert not h.session.playback.running
    # New ACK path preserves command serial and before/after bounded state.
    with recovery.Harness() as h:
        h.working();s=h.session
        controls=[]
        for serial,op in enumerate(('pause','pause','stop'),21):
            value=dict(serial=serial,op=op)
            runtime.dispatch_control(s,value)
            event=h.events[-1];ack=event['control_ack']
            sink=Mock();player.journal_runtime_event(sink,s.session_id,7654,event)
            record=sink.record.call_args.kwargs
            assert record['runtime_session']==s.session_id and record['PID']==7654
            assert 'state' not in record['payload'] and record['payload']['control_ack']==ack
            assert ack['command']['serial']==serial and 'owner_health' in ack['after']
            controls.append(ack)
        assert controls[0]['after']['paused'] and not controls[1]['after']['paused'] and not controls[2]['after']['running']
        evidence.append(dict(case='correlated control shape',ACKs=controls))
    app=recovery.panel();app.send=player.Player.send.__get__(app);app.outgoing=player.queue.Queue(maxsize=64);app.serial=0
    app.send('stop');message=app.outgoing.get_nowait();assert message['serial']==1 and message['op']=='stop'
    app.log.record.assert_called_once();assert app.log.record.call_args.args[0]=='command_submitted'
    app.state.update(restart_notice=runtime.RESTART_NOTICE);app.refreshing=False
    app.receive_sources([recovery.A,recovery.B]);assert app.status.get()==runtime.RESTART_NOTICE
    assert app.devices.options['state']=='readonly'
    evidence.append(dict(case='existing-area notice survives Refresh; inline stays live',notice=app.status.get()))
    # Actual hidden Tk status presentation; all enumeration/control remains fake.
    import tkinter as tk
    import player_inline_source_test as inline
    with tempfile.TemporaryDirectory(prefix='cleanup-hidden-') as folder,patch('player.SourceEnumerator',inline.OfflineEnumerator):
        root=tk.Tk();root.withdraw();panel=player.Player(root,folder)
        try:
            panel.state['restart_notice']=runtime.RESTART_NOTICE
            panel.receive_sources([recovery.A,recovery.B]);root.update_idletasks()
            assert panel.status.get()==runtime.RESTART_NOTICE and root.winfo_ismapped()==0
            assert str(panel.devices['state'])=='readonly'
            evidence.append(dict(case='actual hidden Tk restart status',text=panel.status.get(),mapped=root.winfo_ismapped(),source_state=str(panel.devices['state'])))
        finally:panel.close()
    out.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print('PASS: actual worker/adapter late cancellation, release proof+worker exit, idle/Pause/Stop, correlated ACK shape and persistent existing-area notice')

if __name__=='__main__':run(Path(sys.argv[1]))
