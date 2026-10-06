"""CPU contracts for canonical category BONK and direct destination ownership."""
import contextlib,io,json
from copy import deepcopy
from renderer import Renderer,LIVE_FORMS,INSTANT_BONK_SECONDS
from preview_playback import PreviewPlayback
from studio_scope import playback_scope,leaf_destination,validate_scope
from studio_resources import resource_text

def run():
    cases=[[],['fractals'],['organic'],['geometric'],['cosmic'],['elements'],['elements','plasma']]
    checks=[]
    for path in cases:
        scope=playback_scope('main',path,LIVE_FORMS)
        assert set(scope['forms'])<=set(LIVE_FORMS)
        for mode in ('normal','instant'):
            r=Renderer(seed=7301);p=PreviewPlayback(r,'run',clock=lambda:10.)
            p.apply_destination(scope,scope['forms'][0],1);p.ready=True
            history=deepcopy(r.director_history);time=r.director_time
            with contextlib.redirect_stdout(io.StringIO()):p.command(dict(run='run',serial=1,op='bonk',mode=mode))
            if len(scope['forms'])==1:
                assert not p.can_bonk() and not p.playback.bonk_pending
                assert r.director_history==history and r.director_time==time
            else:
                r.update_blend(10.,.03)
                assert r.director_target in scope['forms'] and r.director_target!=r.director_current,(path,r.director_target)
                assert (r.director_duration==INSTANT_BONK_SECONDS)==(mode=='instant')
            checks.append((path,mode))
    organic=playback_scope('main',['organic'],LIVE_FORMS)
    assert set(organic['forms'])=={11,12}
    cosmic=playback_scope('main',['cosmic'],LIVE_FORMS);assert set(cosmic['forms'])=={5,36}
    plasma=playback_scope('main',['elements','plasma'],LIVE_FORMS);assert set(plasma['forms'])=={32,33,34}
    assert leaf_destination('main',['organic','roots'],organic,LIVE_FORMS)==(organic,12)
    adopted,form=leaf_destination('main',['elements','plasma','arcs'],organic,LIVE_FORMS)
    assert adopted==plasma and form==33
    exp,form=leaf_destination('experimental',['experimental','stormglass'],organic,LIVE_FORMS)
    assert exp['namespace']=='experimental' and form==39 and 39 not in LIVE_FORMS
    bad=deepcopy(organic);bad['forms'].append(39)
    try:validate_scope(bad,LIVE_FORMS)
    except ValueError:pass
    else:raise AssertionError('Experimental form leaked into Main')
    r=Renderer(seed=7301);p=PreviewPlayback(r,'run',clock=lambda:10.)
    p.apply_destination(organic,11,1);p.ready=True;r.director_time=8.;r.star_time=4.;r.flow_time=3.;r.echo_clock=2.
    p.playback.paused=True;p.output_keys.add(42);p.playback.holds.add('studio.mouse')
    p.apply_destination(organic,12,3)
    assert p.playback.paused and not p.playback.holds and not p.output_keys
    assert (r.director_time,r.star_time,r.flow_time,r.echo_clock)==(8.,4.,3.,2.)
    assert r.director_target is None and r.director_current==12
    saved=deepcopy(r.director_history);assert not p.apply_destination(organic,11,2)
    assert p.apply_destination(organic,12,4) and r.director_history==saved
    assert not p.apply_destination(organic,11,4) and r.director_current==12
    import os
    from unittest.mock import patch
    with patch.dict(os.environ,{'ZERAWAVE_PLAYBACK_SCOPE':json.dumps(organic),'ZERAWAVE_PLAYBACK_FORM':'12','ZERAWAVE_DESTINATION_REVISION':'7'}):
        initial=PreviewPlayback(Renderer(seed=7301),'new run')
    assert initial.committed_scope==organic and initial.renderer.director_current==12 and initial.destination_revision==7
    text=resource_text(dict(resources={},running=False),now=10.)
    assert 'warming up' in text and 'stopped' in text and 'not scanout FPS' in text
    stale=resource_text(dict(resources=dict(wall=0.,processes={'1':dict(roles=['Qt GUI'],pid=1,process_cpu_percent=0.)}),running=True),now=10.)
    assert 'Stale / unavailable' in stale and 'CPU 0.0' not in stale
    missing=resource_text(dict(resources=dict(wall=10.,processes={'1':dict(roles=['Qt GUI','control owner'],pid=1,process_working_set_bytes=None)}),running=False),now=10.)
    assert 'Sum of available distinct PID working sets: unavailable' in missing and 'PID 1' in missing
    from session_performance import SessionPerformance,ResourceSampler
    from collections import deque
    metrics=SessionPerformance.__new__(SessionPerformance);metrics.enabled=True
    metrics.sampler=ResourceSampler();metrics.sampler.enabled.clear()
    try:
        sample=dict(wall=10.,process_cpu_percent=12.,sampling_owner='control owner')
        with patch.dict(os.environ,{'ZERAWAVE_OWNER_TELEMETRY':'1'}):
            metrics.owner_sample(sample);metrics.owner_sample(sample)
            assert metrics.sampler.snapshot()==sample and metrics.sampler.samples==1
            metrics.enabled=False;metrics.owner_sample(dict(wall=11.))
            assert metrics.sampler.samples==1 and not metrics.sampler.enabled.is_set()
    finally:metrics.sampler.close()
    assert metrics.sampler.samples==1  # waking an idle collector for Close must not sample
    print('PASS',json.dumps(dict(category_modes=checks,direct_scope_clock_pause_latest=True,telemetry_freshness=True)))

if __name__=='__main__':run()
