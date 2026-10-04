"""Standalone CPU-only selective-starflight checks; no GPU, UI or capture."""
import argparse
import ast
from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'work/planet-canvas-star-attack-01'
sys.path.insert(0,str(ROOT/'app/audio'))
from planet_canvas_dsp_test import audio_env,audio_state,functions,studio_env,tree,renderer_type
from analyzer import AudioAnalyzer
from signal_processor import SignalProcessor,VisualSignalConditioner
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
import preview_layers as layers
import world_catalog as catalog
import transition_catalog as transitions
from planet_star_attack import PlanetStarFlight,attach_bass_attack

def fixtures():
    env={'np':np}
    nodes=[n for n in tree(OUT/'probe_existing_bass_onset.py').body if
        isinstance(n,ast.FunctionDef) and n.name=='kicks' or
        isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in
        ('rate','seconds','t','beats','fixtures') for x in n.targets)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'controlled-fixtures','exec'),env)
    waves=env['fixtures'];beats={n:env['beats'].copy() for n in waves if n.startswith(('sub','round','tight','high_bass','kick_'))}
    for name,period in (('consecutive250ms',.25),('consecutive125ms',.125)):
        env['beats']=np.arange(1.,3.76,period)
        waves[name]=env['kicks'](65,decay=.035)
        beats[name]=env['beats'].copy()
    return waves,beats

def simulate(pcm,analyze,enabled=True):
    state=audio_state();frames=[]
    for start in range(0,len(pcm),2048):
        frame=analyze(pcm[start:start+2048].astype(np.float32),*state,star_attack=enabled,source_id='fixture')
        frames.append(frame)
    flight=PlanetStarFlight();rows=[];events=[];i=0;previous=0
    for tick in range(round(len(pcm)/48000.*120)+1):
        now=tick/120.
        while i<len(frames) and (i+1)*2048/48000.<=now+1e-8:
            f=frames[i];flight.observe(f.planet_star_audio,'fixture');i+=1
            if flight.event_count!=previous:events.append(f.planet_star_audio['sample_seconds']);previous=flight.event_count
        value=flight.advance(0. if tick==0 else 1./120.,now)
        rows.append(dict(time=now,phase=value[1],envelope=value[2],rate=flight.rate))
    return frames,rows,events

def selective_checks():
    waves,beats=fixtures();analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');report={}
    for name,pcm in waves.items():
        frames,rows,events=simulate(pcm,analyze)
        expected=beats.get(name,[])
        phases=np.array([r['phase'] for r in rows]);envelopes=np.array([r['envelope'] for r in rows])
        assert np.all(np.diff(phases)>=0.) and all(1.<=r['rate']<=1.75 for r in rows)
        peaks=[];valleys=[]
        for beat in expected:
            period=float(expected[1]-expected[0]) if len(expected)>1 else .5
            candidates=[r for r in rows if beat<=r['time']<=beat+min(.16,period-.001)]
            peak=max(candidates,key=lambda r:r['envelope']);peaks.append(dict(beat=float(beat),peak=peak['envelope'],delay=peak['time']-beat))
            valleys.append(min(r['envelope'] for r in rows if beat+.09<=r['time']<=beat+period))
        if len(expected):
            assert len(events)==len(expected),(name,len(events),len(expected),events)
            assert all(any(0.<=e-b<=.09 for e in events) for b in expected),name
            assert all(p['peak']>.35 for p in peaks),(name,peaks)
            assert all(0.<=p['delay']<=.13 for p in peaks),name
            assert np.mean(valleys)<np.mean([p['peak'] for p in peaks])*.9,(name,valleys)
        elif name in ('mid_attacks_louder','high_attacks_louder','silence'):
            assert not events and float(envelopes.max())==0.,(name,events)
        elif name in ('sustained_bass','slow_bass'):
            assert not events and float(envelopes.max())==0.,(name,events)
        report[name]=dict(rms=float(np.sqrt(np.mean(pcm*pcm))),expected=len(expected),events=events,
            max_envelope=float(envelopes.max()),peaks=peaks,mean_valley=float(np.mean(valleys)) if valleys else None,
            legacy_flux_max=max(f.flux for f in frames),legacy_global_onset_max=max(f.impact for f in frames),
            legacy_bass_max=max(f.bass for f in frames),trace=rows)
    assert report['mid_attacks_louder']['rms']>report['round65']['rms']
    assert report['high_attacks_louder']['rms']>report['round65']['rms']
    return report

def reset_checks():
    def payload(t,onset=.5):return dict(version=1,sample_seconds=t,bass_attack=onset)
    f=PlanetStarFlight()
    for i in range(1,11):f.observe(payload(i*.04,0.),'A');f.advance(.04,i*.04)
    f.observe(payload(.44),'A');f.advance(.04,.44);assert f.event_count==1 and f.envelope>0
    before=(f.phase,f.event_count);f.observe(payload(.44),'A');f.advance(0.,.44)
    assert (f.phase,f.event_count)==before
    for _ in range(120):f.advance(1./120.,.44)
    assert f.envelope<.03  # No input/recovery cannot hold a stale attack.
    phase=f.phase;f.observe(payload(.04),'B');assert f.envelope==0. and f.phase==phase
    f.observe(payload(3.),'B');assert f.envelope==0. and f.phase==phase
    for bad in (None,{},payload(float('nan')),dict(version=2,sample_seconds=1.,bass_attack=.5),payload(1.,2.)):
        f.observe(bad,'B');assert f.envelope==0. and f.phase==phase
    value=f.advance(2.,8.);assert value[1]==phase and value[2]==0.
    value=f.advance(.01,8.,True);assert value[1]==phase
    for _ in range(10000):
        old=f.phase;v=f.advance(.02,8.);assert v[1]>old and math.isfinite(v[1]) and v[2]==0.
    f.reset();assert f.phase is None and f.rate==1.
    analyzer=SimpleNamespace();frame=SimpleNamespace(bass_onset=.4)
    attach_bass_attack(frame,analyzer,2048,'A',10.);first=deepcopy(frame.planet_star_audio)
    attach_bass_attack(frame,analyzer,2048,'A',10.);assert frame.planet_star_audio['sample_seconds']==first['sample_seconds']*2.
    attach_bass_attack(frame,analyzer,2048,'B',10.);assert frame.planet_star_audio==first
    return dict(repeated_frames='PASS',source_gap_invalidity='PASS',no_input_release='PASS',positive_phase_steps=10000)

def star_renderer_type():
    names=('planet_star_attack_eligible','reset_planet_star_attack','accept_planet_star_audio','planet_star_motion')
    cls=next(n for n in tree(ROOT/'app/visuals/renderer.py').body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    nodes=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
    module=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='CPU',bases=[],keywords=[],body=nodes,decorator_list=[])],type_ignores=[]))
    env={};exec(compile(module,'renderer-route','exec'),env)
    return env['CPU']

def route_checks():
    r=star_renderer_type()();r.planet_star_attack_pilot=True;r.planet_star_flight=None;r.debug_state=5
    r.debug_sequence=();r.transition_sequence=False;r.transition_settings={'pair':[]};r.star_time=12.
    r.accept_planet_star_audio(SimpleNamespace(planet_star_audio=dict(version=1,sample_seconds=.04,bass_attack=0.)),'A')
    assert r.planet_star_motion(0.)==(1.,12.,0.)
    for state,seq,tr,pair in ((0,(),False,[]),(36,(),False,[]),(5,(5,),False,[]),(5,(),False,[5,7]),(5,(),True,[])):
        r.debug_state=state;r.debug_sequence=seq;r.transition_sequence=tr;r.transition_settings={'pair':pair}
        assert not r.planet_star_attack_eligible() and r.planet_star_motion(.04)==(0.,12.,0.)
    r.debug_state=5;r.debug_sequence=();r.transition_sequence=False;r.transition_settings={'pair':[]}
    r.planet_star_attack_pilot=False
    assert r.planet_star_motion(.04)==(0.,12.,0.)
    e=studio_env();base=json.loads((OUT/'star-original-session.json').read_text());candidate=json.loads((OUT/'star-candidate-session.json').read_text())
    assert base==dict(candidate,planet_star_attack_pilot=False)
    for source in ('Test track','Live system audio'):
        for data,on in ((base,False),(candidate,True)):
            data=dict(data,source=source);v=e['validate_session'](data);args=e['command'](v,OUT/'not-launched')
            assert ('--planet-star-attack-pilot' in args)==on
            assert '--planet-dsp-pilot' in args
    for selection in ([],['cosmic','galaxy']):
        data=dict(candidate,selection=selection,state='blend',source='Live system audio')
        v=e['validate_session'](data)
        assert ('--planet-star-attack-pilot' in e['command'](v,OUT/'not-launched'))==(v['selection_scope']=='main')
    for name in ('live_visual_test.py','replay_test.py'):
        t=tree(ROOT/'app/visuals'/name)
        fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==('main' if name.startswith('live') else 'replay'))
        assert fn.args.args[-1].arg=='planet_star_attack_pilot' and isinstance(fn.args.defaults[-1],ast.Constant) and fn.args.defaults[-1].value is False
    # All sample-domain legacy results are identical when the optional field is added.
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');old=audio_env(OUT/'baseline/live_visual_test.py')
    rng=np.random.default_rng(42);states=[audio_state() for _ in range(3)]
    for _ in range(120):
        samples=rng.normal(0.,.04,(2048,2)).astype(np.float32)
        a=old(samples,*states[0]);b=analyze(samples,*states[1]);c=analyze(samples,*states[2],star_attack=True,source_id='A')
        def values(frame):return {k:v for k,v in vars(frame).items() if k!='planet_star_audio'}
        for k,v in values(a).items():
            assert np.array_equal(v,values(b)[k]) and np.array_equal(v,values(c)[k]),k
        assert not hasattr(b,'planet_star_audio') and not hasattr(states[1][0],'_planet_star_attack')
    return dict(context_guards=6,studio_preset_routing='PASS',CLI_defaults=False,exact_legacy_frames=120)

def owner_checks():
    Surface=renderer_type();Star=star_renderer_type();instances=[];streams=[]
    pcm=fixtures()[0]['round65'][:2048*64].astype(np.float32)
    stereo=np.column_stack((pcm,pcm));raw=(stereo*32767).astype('<i2').tobytes()
    class Window(Surface,Star):
        def __init__(self,**kw):
            Surface.__init__(self);self.parameters=SimpleNamespace();self.planet_star_attack_pilot=False
            self.planet_star_flight=None;self.star_time=0.;self.polls=0;self.previous=None
            self.program['u_planet_star_flight']=SimpleNamespace(value=(0.,0.,0.));self.flight_values=[]
            self.echo_weight=0.;self.shockwaves=[];self.blast_events=[];self.planet_visits=0;self.flow_rate=.35
            instances.append(self)
        def set_galaxy_start(self,*a):pass
        def configure_transitions(self,cfg):
            self.transition_settings=transitions.validate_settings(cfg);self.transition_sequence=bool(self.transition_settings['pair'])
        def create(self):pass
        def should_close(self):return self.polls>=64
        def consume_pcm(self,*a):pass
        def render(self,elapsed_time=None):
            now=self.polls*2048/48000. if elapsed_time is None else elapsed_time
            self.draw(now);dt=0. if self.previous is None else now-self.previous
            self.star_time+=dt;self.previous=now
            self.program['u_planet_star_flight'].value=self.planet_star_motion(dt)
            self.flight_values.append(self.program['u_planet_star_flight'].value)
        def swap_buffers(self):pass
        def poll_events(self):self.polls+=1
        def close(self):pass
    class PCMFile:
        def __enter__(self):self.offset=0;return self
        def __exit__(self,*a):pass
        def getframerate(self):return 48000
        def getnchannels(self):return 2
        def getsampwidth(self):return 2
        def readframes(self,n):
            part=raw[self.offset:self.offset+n*4];self.offset+=len(part);return part
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py')
    env=dict(np=np,math=math,time=SimpleNamespace(perf_counter=lambda:0.,sleep=lambda _:None),
        wave=SimpleNamespace(open=lambda *a:PCMFile()),Renderer=Window,AudioAnalyzer=AudioAnalyzer,
        SignalProcessor=SignalProcessor,VisualSignalConditioner=VisualSignalConditioner,
        OnsetDetector=OnsetDetector,VisualParameterMapper=VisualParameterMapper,analyze_samples=analyze,
        LIVE_STATES=catalog.LIVE_STATES,validate_layers=layers.validate_layers,layers_at=layers.layers_at,
        configure_colors=lambda *a:None)
    replay=functions(ROOT/'app/visuals/replay_test.py',['replay'],dict(env))['replay']
    for on,state,seq,pair in ((False,'canvas',None,[]),(True,'canvas',None,[]),
                              (True,'blend',None,[]),(True,'galaxy',None,[]),
                              (True,'canvas',['canvas'],[]),(True,'canvas',None,[5,7])):
        replay(Path('supplied-PCM.wav'),speed=0.,state=state,states=seq,transitions=dict(pair=pair),
               planet_dsp_pilot=True,planet_star_attack_pilot=on)
        r=instances[-1];eligible=on and state=='canvas' and not seq and not pair
        assert (r.planet_star_flight is not None)==eligible
        if eligible:
            assert max(v[2] for v in r.flight_values)>.35 and r.planet_star_flight.phase is None
        else:assert all(v[0]==0. for v in r.flight_values)
    class Capture:
        def __init__(self,**kw):pass
        def find_device(self):return 'supplied CPU PCM, not device'
    class Stream:
        def __init__(self,capture,analyze):
            self.analyze=analyze;self.offset=0;self.starts=self.stops=0
            self.worker=SimpleNamespace(is_alive=lambda:False);streams.append(self)
        def start(self):self.starts+=1
        def stop(self):self.stops+=1
        def drain(self):
            part=stereo[self.offset:self.offset+2048];self.offset+=len(part)
            return [(0.,self.analyze(part))] if len(part) else []
    env.update(AudioCapture=Capture)
    main=functions(ROOT/'app/visuals/live_visual_test.py',['main'],env)['main'];previous=sys.modules.get('capture_stream')
    try:
        sys.modules['capture_stream']=SimpleNamespace(CaptureStream=Stream)
        for on,state in ((False,'canvas'),(True,'canvas'),(True,'blend'),(True,'galaxy')):
            before=len(streams)
            with redirect_stdout(io.StringIO()):main(state=state,quiet=True,planet_dsp_pilot=True,planet_star_attack_pilot=on)
            assert len(streams)==before+1 and streams[-1].starts==streams[-1].stops==1
            r=instances[-1];eligible=on and state=='canvas'
            assert (r.planet_star_flight is not None)==eligible
            if eligible:assert max(v[2] for v in r.flight_values)>.35 and r.planet_star_flight.phase is None
    finally:
        if previous is None:sys.modules.pop('capture_stream',None)
        else:sys.modules['capture_stream']=previous
    return dict(actual_replay_orchestration_mocked=6,actual_live_owner_mocked=4,streams_per_live_run=1,capture_threads=0,EOF_Stop_cleanup='PASS')

def preservation_checks():
    path=ROOT/'app/visuals/shaders/dream.frag';before=(OUT/'baseline/dream.frag').read_text();after=path.read_text()
    # Later authorized gain adapters retain the reviewed attack-flight route.
    # Undo their source delta before comparing this historical route baseline.
    from planet_audio_tuning_test import remove_coverage_shader
    after=remove_coverage_shader(after)
    def function(source,start,end):return source[source.index(start):source.index(end,source.index(start))]
    assert function(before,'vec3 shooting_star_radiance(','// Shared star sheets')==function(after,'vec3 shooting_star_radiance(','// Shared star sheets')
    old=function(before,'vec3 cosmic_star_layer(','// Galaxy Odyssey:');new=function(after,'vec3 cosmic_star_layer(','// Galaxy Odyssey:')
    block='''    // Held Planet pilot changes only sheet travel/wakes. Shared star time,
    // shooting births, twinkle, presence, pigments and light remain legacy.
    bool attack_flight = u_planet_star_flight.x > .5 && abs(u_debug_state-5.) < .1;
    float flight_clock = attack_flight ? u_planet_star_flight.y : u_star_time;
    float wake = attack_flight ? u_planet_star_flight.z : chorus;
'''
    normalized=new.replace(block,'').replace('wake * wake','chorus * chorus').replace('heading * flight_clock','heading * u_star_time')
    assert normalized==old  # No brightness/pigment/presence/twinkle/heading edits.
    def shared_star(source):return function(source,'        # Star motion has its own positive','        # Galaxy alone remembers')
    from rollout_source_test_helpers import pre_rollout_source
    clock=pre_rollout_source('app/visuals/renderer.py',(ROOT/'app/visuals/renderer.py').read_text(encoding='utf8')).replace("star_local['flux']*clock_flux_gain",'self.parameters.flux').replace("star_local['sparkle']*clock_sparkle_gain",'self.parameters.sparkle')
    assert shared_star((OUT/'baseline/renderer.py').read_text())==shared_star(clock)
    # Execute the actual old and new shared clock, including the Galaxy branch.
    # Disabled windows return these legacy inputs; enabled windows only substitute
    # the two named inputs and keep the integration, easing and brightness limits.
    def run_clock(source,flux,sparkle,state,dt,local=None):
        owner=SimpleNamespace(parameters=SimpleNamespace(flux=flux,sparkle=sparkle,scale=.43),
            blend_values={},state_at=lambda t:state,star_rate=1.17,star_time=8.25)
        env=dict(self=owner,current_time=3.,delta_time=dt,movement=.38,math=math,
            clock_flux_gain=1.,clock_sparkle_gain=1.,star_local=local or dict(flux=flux,sparkle=sparkle),studio_audio=None)
        import textwrap
        exec(compile(textwrap.dedent(shared_star(source)),'actual-star-clock','exec'),env)
        return owner.star_rate,owner.star_time,env['star_drive']
    old_clock=(OUT/'baseline/renderer.py').read_text()
    current_clock=(ROOT/'app/visuals/renderer.py').read_text()
    cases=0
    for state in (5,36):
        for flux in (0.,.2,.85,1.):
            for sparkle in (0.,.3,1.):
                for dt in (0.,1/60,.2):
                    assert run_clock(old_clock,flux,sparkle,state,dt)==run_clock(current_clock,flux,sparkle,state,dt)
                    cases+=1
    assert run_clock(current_clock,.1,.2,5,.02,dict(flux=.9,sparkle=.8))==run_clock(old_clock,.9,.8,5,.02)
    assert (OUT/'baseline/planet_canvas_dsp.py').read_bytes()==(ROOT/'app/visuals/planet_canvas_dsp.py').read_bytes()
    return dict(shooting_births_and_shared_star_clock='PASS normalized neutral gain source equivalence; clocks and births retained',
        exact_window_OFF_clock_cases=cases,local_clock_named_inputs='PASS actual clock block',surface_mapping='PASS unchanged',shader_disabled_branch='PASS normalized source equivalence; GPU pixel check pending')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args()
    report=dict(evidence_class='CPU controlled synthetic PCM and exact AST-isolated routing; no GPU, live capture or listening',
        selective=selective_checks(),resets=reset_checks(),routing=route_checks(),owners=owner_checks(),preservation=preservation_checks())
    assert not any(n in sys.modules for n in ('glfw','moderngl','soundcard','tkinter','capture'))
    if args.output:args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps({n:{k:v for k,v in r.items() if k!='trace'} for n,r in report['selective'].items()},indent=2));print('Planet star-attack CPU checks PASS')

if __name__=='__main__':main()
