"""CPU clock/control/transport bounds and truthful report checks, no GL/capture."""
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
from preview_playback import PreviewPlayback
from session_performance import Distribution,process_resources


def run():
    clock=[100.]
    renderer=SimpleNamespace(debug_state=0,debug_sequence=(),transition_sequence=False,transition_settings={'hold':12.,'duration':6.},
        director_target=None,parameters=SimpleNamespace(impact=1.,beat_tick=True),player=None)
    with patch.dict(sys.modules,renderer=SimpleNamespace(LIVE_FORMS=(2,5,12))):
        controls=PreviewPlayback(renderer,'run',lambda:clock[0])
    controls.ready=True
    serial=[0]
    def send(op,**values):
        serial[0]+=1
        controls.command(dict(run='run',serial=serial[0],op=op,**values))
    with redirect_stdout(io.StringIO()):
        send('pause',active=True);clock[0]=110.;assert controls.drawing_time()==100.
        send('pause',active=False);assert controls.drawing_time()==100.
        clock[0]=111.;assert controls.drawing_time()==101.
        assert renderer.parameters.impact==0. and not renderer.parameters.beat_tick
        assert controls.resume_after==110.
        send('hold',owner='studio.Shift_L',active=True);assert controls.playback.held
        send('release');assert not controls.playback.held
        send('bonk',mode='instant');assert controls.playback.bonk_pending and controls.playback.bonk_pending_mode=='instant'
        send('pause',active=True);assert not controls.can_bonk() and not controls.playback.bonk_pending
        send('pause',active=False)
        renderer.debug_state=5;assert not controls.can_bonk()
        renderer.debug_sequence=(12,5);renderer.transition_sequence=True
        controls.route_time(0.)
        send('hold',owner='studio.mouse',active=True)
        assert controls.route_time(8.)==0. and controls.drawing_time()==101.
        send('bonk',mode='instant');assert controls.route==12.
        assert controls.route_time(8.25)==18.
        assert controls.route_rate==1. and controls.route_time(9.)==18.
        send('release');assert controls.route_time(10.)==19.
        before=controls.snapshot()
        try:controls.command(dict(run='old',serial=999,op='stop'))
        except ValueError:pass
        else:raise AssertionError('Wrong run accepted')
        assert controls.snapshot()==before
        send('stop');assert not controls.playback.running and not controls.playback.held
    # Actual pipe mailbox coalesces into bounded slots, rejects arbitrary owners.
    from studio_color_link import ColorInbox
    read_fd,write_fd=os.pipe()
    with patch.dict(os.environ,{'ZERAWAVE_PREVIEW_RUN':'test'}):inbox=ColorInbox(read_fd)
    try:
        with redirect_stdout(io.StringIO()):
            for n in range(500):inbox.accept(json.dumps(dict(kind='preview-control',run='test',serial=n,op='hold',owner='studio.mouse',active=bool(n%2))))
            for n in range(30):inbox.accept(json.dumps(dict(kind='preview-control',run='test',serial=n,op='hold',owner='other'+str(n),active=True)))
        assert len(inbox.pending_controls)==1
        assert inbox.take_controls()[0]['serial']==499
    finally:
        inbox.close();os.close(write_fd);inbox.thread.join(timeout=1.);os.close(read_fd)
    d=Distribution()
    assert d.packet()['p50_ms'] is None
    for value in (.001,.01,.02,.2,2.):d.add(value)
    result=d.packet()
    assert result['samples']==5 and result['over_50_ms']==2 and result['max_ms']==2000.
    assert len(d.bins)==10001 and result['p95_ms']==1000.
    resources=process_resources()
    assert resources['process_working_set_bytes'] is None or resources['process_working_set_bytes']>0
    print(json.dumps(dict(evidence='CPU explicit clocks, Player state, actual bounded pipe and process counters; no GPU/capture',
        pause_clock_freezes=True,resume_rejects_stale_before=110.,hold_parks_route_not_drawing=True,
        instant_sequence_arrival_seconds=.25,held_form_bonk_unavailable=True,
        wrong_run_rejected=True,mailbox_after_500_commands=1,arbitrary_hold_owners_rejected=True,
        histogram_samples=result['samples'],working_set_available=resources['process_working_set_bytes'] is not None),indent=2))
    print('Preview playback CPU checks PASS')


if __name__=='__main__':run()
