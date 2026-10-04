"""CPU-only current-preview controls, FFT overlap and musical-proxy checks."""
import argparse
import ast
from copy import deepcopy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work/planet-star-live-tuning-01'
sys.path.insert(0,str(ROOT/'app/audio'))
from band_attack_tuning import BASELINE,BOUNDS,RANGES,BandAttackTuning,validate,weighted
from low_band_attack import LowBandAttack
from planet_star_attack import PlanetStarFlight
from planet_canvas_dsp_test import audio_env,audio_state,tree,functions
from planet_star_attack_test import fixtures,simulate
from planet_star_attack_test import star_renderer_type
from planet_canvas_dsp_test import renderer_type
from starfield_tuning import decode,PREFIX
from studio_color_link import ColorInbox,ColorLink

def controls_checks():
    for k,(low,high) in BOUNDS.items():
        for value in [low,high]:assert validate(dict(BASELINE,**{k:value}))[k]==value
        for value in [low-.01,high+.01,float('nan'),True,'1']:
            try:validate(dict(BASELINE,**{k:value}))
            except ValueError:pass
            else:raise AssertionError((k,value))
    # Deliberately place bins exactly on40,160,250 and315 edges.
    f=np.array([20.,30.,40.,80.,159.,160.,220.,249.,250.,300.,315.]);m=np.arange(1.,12.)
    frame=SimpleNamespace(spectrum_frequencies=f,spectrum_magnitudes=m)
    baseline=float(m[(f>=20)&(f<250)].mean());detector=LowBandAttack();tune=BandAttackTuning()
    level,sensitivity,summary=tune.apply(frame,baseline,detector,'A')
    assert level==baseline and sensitivity==1. and sum(summary['counts'])==10
    assert np.all(np.sum(tune.masks,axis=0)<=1) and not any(mask[-1] for mask in tune.masks)
    c=dict(BASELINE,low_weight=0.,body_weight=2.,upper_weight=.5,extension=1.)
    tune.submit(1,c);level,sensitivity,summary=tune.apply(frame,baseline,detector,'A')
    expected=(2.*sum(m[2:5])+.5*sum(m[5:8])+.5*sum(m[8:10]))/8
    assert level==expected and detector.previous==expected
    # Same spectrum under changed weights is a zero rise, not a knob-triggered hit.
    p=detector.process(level,2048,'A');tune.completed(p,summary)
    tune.submit(2,dict(BASELINE,sensitivity=2.,extension=1.,upper_weight=2.))
    level,sens,summary=tune.apply(frame,baseline,detector,'A');p=detector.process(level,2048,'A',sens)
    assert p['bass_attack']==0. and p['sample_seconds']==4096/48000.
    tune.completed(p,summary)
    tune.submit(3,dict(BASELINE));level,sens,summary=tune.apply(frame,baseline,detector,'A')
    assert level==baseline and detector.previous==baseline and sens==1.
    p=detector.process(level,2048,'A',sens);assert p['bass_attack']==0.
    tune.completed(p,summary);assert tune.latest['settings']==BASELINE and tune.latest['revision']==3
    tune.submit(4,dict(BASELINE,enabled=False,body_weight=0.,sensitivity=2.))
    assert tune.apply(frame,baseline,detector,'A')[:2]==(baseline,1.)
    return dict(disjoint_edges=True,exact_baseline=True,exact_reset=True,no_control_rise=True,
                no_sample_clock_reset=True,bypass_exact=True,clamps=True)

def exact_baseline_checks():
    # Execute the reviewed detector source, not a reconstruction of its formula.
    env={};exec(compile((OUT/'baseline/low_band_attack.py').read_text(),'reviewed-detector','exec'),env)
    old=env['LowBandAttack']();new=LowBandAttack();rng=np.random.default_rng(3207)
    for i in range(1200):
        value=float(rng.uniform(0.,60.));expected=old.process(value,2048,'same');actual=new.process(value,2048,'same')
        assert expected=={key:actual[key] for key in expected}
        assert set(actual)-set(expected)=={'detector_response'}
    analyzed=audio_env(ROOT/'app/visuals/live_visual_test.py');a=audio_state();b=audio_state()
    b[0]._planet_star_tuning=BandAttackTuning();count=120
    for i in range(count):
        pcm=rng.normal(0.,.06,(2048,2)).astype(np.float32)
        f=analyzed(pcm,*a,star_attack=True,descriptors=True,source_id='A')
        g=analyzed(pcm,*b,star_attack=True,descriptors=True,source_id='A')
        def equal(x,y):
            if isinstance(x,np.ndarray):return np.array_equal(x,y)
            if isinstance(x,dict):return x.keys()==y.keys() and all(equal(x[k],y[k]) for k in x)
            return x==y
        assert equal(f.__dict__,g.__dict__)
    return dict(reviewed_detector_packets_exact=1200,complete_audio_frames_exact=count,legacy_DSP_unchanged=True)

def fixture_checks():
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');waves,expected=fixtures();rate=48000
    seconds=len(next(iter(waves.values())))/rate;t=np.arange(int(seconds*rate))/rate
    # Explicit synthetic voice-like syllables; never record a call/person.
    voice=np.zeros_like(t);picked=np.zeros_like(t)
    for beat in np.arange(1.,7.51,.5):
        age=np.maximum(0.,t-beat);mask=t>=beat
        env=mask*np.minimum(1.,age/.025)*np.exp(-age/.18)
        voice+=env*(.35*np.sin(2*np.pi*125*age)+.20*np.sin(2*np.pi*350*age)+.15*np.sin(2*np.pi*950*age))
        picked+=mask*np.minimum(1.,age/.004)*np.exp(-age/.25)*(.4*np.sin(2*np.pi*82*age)+.14*np.sin(2*np.pi*164*age))
    waves.update(synthetic_speechlike=voice,picked_bass=picked)
    report={}
    for name in ['consecutive125ms','sustained_bass','picked_bass','mid_attacks_louder','high_attacks_louder','synthetic_speechlike']:
        _,rows,events=simulate(waves[name],analyze)
        if name=='consecutive125ms':assert len(events)==23 and all(1.<=r['rate']<=1.75 for r in rows)
        if name in ('sustained_bass','mid_attacks_louder','high_attacks_louder'):assert not events
        report[name]=dict(accepted_proxy_events=len(events),peak_envelope=max(r['envelope'] for r in rows),
            expected_kicks=23 if name=='consecutive125ms' else None,
            interpretation='Potential false positives; explicit synthetic speechlike negative, not instrument separation' if name=='synthetic_speechlike' else 'Proxy response, not instrument labels')
    return report

def protocol_checks():
    inbox=ColorInbox.__new__(ColorInbox);inbox.lock=threading.Lock();inbox.closed=False
    inbox.pending_star_tuning=None;inbox.star_tuning_revision=-1;inbox.pending_star_view=None
    inbox.accept(json.dumps(dict(kind='star-tuning',revision=1,settings=BASELINE)).encode())
    altered=dict(BASELINE,extension=.4,sensitivity=1.3)
    inbox.accept(json.dumps(dict(kind='star-tuning',revision=2,settings=altered)).encode())
    assert inbox.take_star_tuning()==(2,altered) and inbox.take_star_tuning() is None
    inbox.accept(b'{"kind":"star-tuning-view","enabled":true}');assert inbox.take_star_view() is True
    # Execute exact renderer command-consumption block against the real inbox.
    cls=next(n for n in tree(ROOT/'app/visuals/renderer.py').body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    render=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='render')
    block=next(n for n in render.body if isinstance(n,ast.If) and ast.unparse(n.test)=='self.star_tuning is not None and self.color_inbox')
    flight=PlanetStarFlight();flight.phase=123.;flight.envelope=.25;tune=BandAttackTuning()
    r=SimpleNamespace(star_tuning=tune,color_inbox=inbox,star_tuning_visible=False,planet_star_flight=flight)
    inbox.accept(json.dumps(dict(kind='star-tuning',revision=3,settings=altered)).encode())
    inbox.accept(b'{"kind":"star-tuning-view","enabled":true}')
    exec(compile(ast.Module(body=[block],type_ignores=[]),'actual-renderer-control','exec'),dict(self=r))
    assert tune.pending==(3,altered) and r.star_tuning_visible and flight.phase==123. and flight.envelope==.25
    return dict(latest_control_only=True,actual_inbox_and_render_control=True,flight_phase_untouched=True)

def live_owner_checks(settings_sequence=None,star_enabled=True,artifact_sequence=None,planet_sequence=None,star_presentation_sequence=None):
    """Real pipes/worker + exact live owner; synthetic capture and CPU graphics."""
    import preview_layers as layers
    import world_catalog as catalog
    from analyzer import AudioAnalyzer
    from signal_processor import SignalProcessor,VisualSignalConditioner
    from onset_detector import OnsetDetector
    from parameter_mapper import VisualParameterMapper
    from collections import deque
    control_r,control_w=os.pipe();status_r,status_w=os.pipe()
    inbox=ColorInbox(control_r);status_out=os.fdopen(status_w,'wb',buffering=0)
    class Log(io.StringIO):
        def close(self):self.saved=self.getvalue()
    log=Log();link=ColorLink(SimpleNamespace(stdin=os.fdopen(control_w,'wb',buffering=0),stdout=os.fdopen(status_r,'rb',buffering=0)),log)
    Surface=renderer_type();Star=star_renderer_type();instances=[];captures=[];acks=[];errors=[]
    sequence=settings_sequence or [dict(BASELINE,body_weight=1.5,upper_weight=.6,extension=.4,sensitivity=1.2),dict(BASELINE)]
    cls=next(n for n in tree(ROOT/'app/visuals/renderer.py').body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    render=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='render')
    control=next(n for n in render.body if isinstance(n,ast.If) and ast.unparse(n.test)=='self.star_tuning is not None and self.color_inbox')
    output=next(n for n in render.body if isinstance(n,ast.If) and ast.unparse(n.test)=='self.star_tuning is not None and self.star_tuning_visible')
    route=compile(ast.Module(body=[control],type_ignores=[]),'actual-render-control','exec')
    ai=next(i for i,n in enumerate(render.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='artifact')
    aj=next(i for i,n in enumerate(render.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=="self.program['u_artifacts_listening_inputs'].value")
    artifact_route=compile(ast.Module(body=render.body[ai:aj+1],type_ignores=[]),'actual-artifact-uniform-route','exec')
    pi=next(i for i,n in enumerate(render.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='planet_active')-1
    pj=next(i for i,n in enumerate(render.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='clock_sparkle_gain')
    planet_route=compile(ast.Module(body=render.body[pi:pj+1],type_ignores=[]),'actual-planet-tuning-route','exec')
    publication=compile(ast.Module(body=[output],type_ignores=[]),'actual-render-status','exec')
    class Window(Surface,Star):
        def __init__(self,**kw):
            Surface.__init__(self);self.cosmos_seed=7301;self.color_overrides={};self.color_inbox=inbox
            self.parameters=SimpleNamespace(scale=0.,movement=0.,flux=0.,sparkle=0.,impact=0.);self.impact_envelope=0.;
            self.program={key:SimpleNamespace(value=None) for key in ('u_artifacts_audio','u_artifacts_tuning_on','u_artifacts_shape_audio','u_artifacts_listening_on','u_artifacts_listening_inputs','u_planet_audio','u_planet_audio_on')}
            self.planet_star_flight=None;self.planet_star_attack_pilot=False
            self.star_tuning=None;self.star_tuning_visible=False;self.planet_monitor=None
            self.star_time=0.;self.previous=None;self.started=time.perf_counter();self.phases=[]
            self.echo_weight=0.;self.enveloper_failed=False
            instances.append(self)
        def configure_transitions(self,cfg):self.transition_settings=cfg or {};self.transition_sequence=False
        def set_galaxy_start(self,*a):pass
        def create(self):pass
        def should_close(self):return time.perf_counter()-self.started>max(3.8,len(planet_sequence or [])*.30+.8)
        def consume_pcm(self,*a):pass
        def render(self):
            now=time.perf_counter()-self.started;dt=0. if self.previous is None else now-self.previous
            self.previous=now;self.star_time+=dt;self.impact_envelope=self.parameters.impact
            env=dict(self=self,delta_time=dt,rewound=False,layers_at=layers.layers_at,current_time=now);exec(planet_route,env)
            self.clock_gain_inputs=(env['clock_flux_gain'],env['clock_sparkle_gain'])
            self.program['u_planet_audio'].value=env['planet_audio_rows'];self.program['u_planet_audio_on'].value=env['planet_audio_on']
            exec(artifact_route,env)
            exec(route,dict(self=self));v=self.planet_star_motion(dt);self.phases.append(v[1])
            exec(publication,dict(env,self=self,math=math,json=json,time=time,current_time=now,mode=0,mask=0,
                material_mix=(1.,0.,0.),new_materials=(0.,0.,0.),spatial_amounts=(0.,0.,0.),weights=(0.,0.,0.),shooting_stars=1.,
                print=lambda text,flush=False:status_out.write((text+'\n').encode())))
        def swap_buffers(self):pass
        def poll_events(self):pass
        def close(self):inbox.close();status_out.close()
    class Capture:
        def __init__(self,**kw):
            self.resolved=dict(kind='synthetic CPU fixture',name='No real device');self.offset=0;self.starts=self.stops=self.reads=0
            captures.append(self)
        def find_device(self):return 'supplied synthetic PCM; no device'
        def start(self):self.starts+=1
        def stop(self):self.stops+=1
        def read(self,numframes):
            time.sleep(numframes/48000.)
            t=(np.arange(numframes)+self.offset)/48000.;age=np.maximum(0.,(t-.3)% .125)
            pcm=.35*np.minimum(age/.001,1.)*np.exp(-age/.035)*np.sin(2*np.pi*65*age)
            self.offset+=numframes;self.reads+=1;return np.column_stack((pcm,pcm)).astype(np.float32)
    def driver():
        try:
            link.submit_star_view(True)
            if star_presentation_sequence:
                from band_attack_tuning import PRESENTATION_BOUNDS
                from planet_audio_tuning import STAR_INDEX
                for c in star_presentation_sequence:
                    time.sleep(.12);revision=link.submit_star_tuning(c);deadline=time.perf_counter()+1.2
                    while time.perf_counter()<deadline:
                        latest=link.get_star_tuning();p=latest[0] if latest else None
                        if p and p['revision']==revision:
                            assert p['settings']==c and not p['pilot_active'] and p['presentation_active']
                            rows=instances[0].program['u_planet_audio'].value
                            for i,key in enumerate(list(PRESENTATION_BOUNDS)[:4]):assert rows[STAR_INDEX*2][i]==c[key]
                            assert instances[0].clock_gain_inputs==(c['flux_clock'],c['sparkle_clock'])
                            acks.append(p);break
                        time.sleep(.02)
                    else:raise AssertionError('No pilot-OFF presentation ACK')
                return
            if planet_sequence:
                from planet_audio_tuning import INDEX,SPECS
                for target,c in planet_sequence:
                    time.sleep(.08);revision=link.submit_planet_tuning(target,c);deadline=time.perf_counter()+1.2
                    while time.perf_counter()<deadline:
                        latest=link.get_star_tuning();p=latest[0].get('planet_tuning',{}).get(target) if latest else None
                        if p and p['revision']==revision:
                            assert p['settings']==c and p['active']
                            r=instances[0];values=list(r.planet_audio_tuning.gains(target))
                            rows=r.program['u_planet_audio'].value
                            for i,v in enumerate(values):assert rows[INDEX[target]*2+i//4][i%4]==v
                            acks.append(latest[0]);break
                        time.sleep(.02)
                    else:raise AssertionError('No target ACK '+target)
                return
            if artifact_sequence:
                for command in artifact_sequence:
                    c,a=command if isinstance(command,tuple) else (command,None)
                    time.sleep(.45);revision=link.submit_artifact_tuning(c,a);deadline=time.perf_counter()+1.2
                    while time.perf_counter()<deadline:
                        latest=link.get_star_tuning();target=latest[0].get('artifact_tuning') if latest else None
                        if target and target['revision']==revision:
                            if any(row['enabled'] and not row['ready'] for row in target.get('listening',{}).values()):
                                time.sleep(.02);continue
                            expected=c if c['enabled'] else dict(target['authored'],enabled=False)
                            assert target['settings']==expected and target['active']
                            if a is not None:assert target['authored']==a
                            r=instances[0]
                            assert tuple(target['gains'])==r.program['u_artifacts_audio'].value
                            assert target['uniform_on']==r.program['u_artifacts_tuning_on'].value
                            assert tuple(target['shape_gains'])==r.program['u_artifacts_shape_audio'].value
                            assert tuple(target['listening_on'])==r.program['u_artifacts_listening_on'].value
                            assert all(0.<=v<=1. for v in r.program['u_artifacts_listening_inputs'].value)
                            acks.append(latest[0]);break
                        time.sleep(.02)
                    else:raise AssertionError('No Living Artifacts ACK '+str(revision))
                return
            if not star_enabled:
                deadline=time.perf_counter()+1.2
                while time.perf_counter()<deadline:
                    latest=link.get_star_tuning()
                    if latest and latest[0].get('spectrum'):
                        assert not latest[0]['pilot_active'];acks.append(latest[0]);return
                    time.sleep(.02)
                raise AssertionError('No pilot-OFF spectrum through actual owner')
            for command in sequence:
                settings,author=command if isinstance(command,tuple) else (command,None)
                time.sleep(.45);revision=link.submit_star_tuning(settings,author);deadline=time.perf_counter()+1.2
                while time.perf_counter()<deadline:
                    latest=link.get_star_tuning()
                    if latest and latest[0].get('revision')==revision:
                        expected=settings if settings['enabled'] else dict(latest[0]['authored'],enabled=False)
                        assert latest[0]['settings']==expected and latest[0]['pilot_active']
                        if author is not None:assert latest[0]['authored']==author
                        assert latest[0].get('spectrum') is not None
                        acks.append(latest[0]);break
                    time.sleep(.02)
                else:raise AssertionError('No actual analysis acknowledgement '+str(revision))
        except Exception as exc:errors.append(repr(exc))
    thread=threading.Thread(target=driver,name='Owned CPU tuning controls');thread.start()
    env=dict(np=np,time=time,json=json,Renderer=Window,AudioCapture=Capture,AudioAnalyzer=AudioAnalyzer,
        SignalProcessor=SignalProcessor,VisualSignalConditioner=VisualSignalConditioner,
        OnsetDetector=OnsetDetector,VisualParameterMapper=VisualParameterMapper,
        LIVE_STATES=catalog.LIVE_STATES,validate_layers=layers.validate_layers,
        analyze_samples=audio_env(ROOT/'app/visuals/live_visual_test.py'),configure_colors=lambda *a:None)
    main=functions(ROOT/'app/visuals/live_visual_test.py',['main'],env)['main']
    from contextlib import redirect_stdout
    try:
        with redirect_stdout(io.StringIO()):main(state='canvas',quiet=True,color_input=True,planet_dsp_pilot=True,planet_star_attack_pilot=star_enabled)
        thread.join(2.);link.close()
        r=instances[0];capture=captures[0]
        assert not errors and len(acks)==(len(star_presentation_sequence) if star_presentation_sequence else len(planet_sequence) if planet_sequence else len(artifact_sequence) if artifact_sequence else len(sequence) if star_enabled else 1),(errors,acks)
        assert capture.starts==capture.stops==1 and len(captures)==1
        assert all(y>=x for x,y in zip(r.phases,r.phases[1:]))
        if planet_sequence:
            assert r.planet_audio_tuning is not None and all(r.planet_audio_tuning.state[target]['revision']==1 for target,c in planet_sequence)
        elif artifact_sequence:
            assert r.artifact_tuning.revision==len(artifact_sequence)
        elif star_enabled:
            final=sequence[-1][0] if isinstance(sequence[-1],tuple) else sequence[-1]
            expected=final if final['enabled'] else dict(r.star_tuning.authored,enabled=False)
            assert r.star_tuning.latest['settings']==expected and r.star_tuning.latest['revision']==len(sequence)
            assert r.planet_star_flight.phase is None # Normal owner's final cleanup.
        else:assert r.star_tuning.frames==0 and r.planet_star_flight is None
        assert PREFIX not in log.saved
        return dict(classification='Exact live main + real CaptureStream/ColorInbox/ColorLink threads and pipes; mocked synthetic capture/graphics, no device or GPU',
            revisions=[p['revision'] for p in acks],settings=[p['settings'] for p in acks],
            control_to_analysis_ms=[p.get('control_to_analysis_ms') for p in acks],
            sample_seconds=[p.get('sample_seconds') for p in acks],reads=capture.reads,
            spectrum_bins=[len(p['spectrum']['db']) for p in acks],
            packet_bytes=[len(json.dumps(p,separators=(',',':')).encode()) for p in acks],
            pilot_active=star_enabled,bypass_spectrum=True,
            analyzed_frames=r.star_tuning.frames,capture_starts=capture.starts,capture_stops=capture.stops,
            positive_phase=True,settings_reset_exact=True,normal_cleanup=True,telemetry_not_logged=True,
            artifact_ACKs=[p.get('artifact_tuning') for p in acks])
    finally:
        if not status_out.closed:status_out.close()
        inbox.close();link.close();os.close(control_r)

def view_checks():
    # The frequency-window view replaces the earlier fixed-band view; retain
    # these regressions through the shared constructor/callback CPU checks.
    from spectrum_tuning_test import view_checks as check_view
    return check_view()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args()
    report=dict(classification='CPU synthetic PCM + exact AST routing; no GPU/UI/device/call recording',
        controls=controls_checks(),baseline=exact_baseline_checks(),fixtures=fixture_checks(),protocol=protocol_checks(),live_owner=live_owner_checks(),view=view_checks())
    assert not any(n in sys.modules for n in ['glfw','moderngl','soundcard','tkinter','capture'])
    if args.output:args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));print('Starfield tuning CPU checks PASS')

if __name__=='__main__':main()
