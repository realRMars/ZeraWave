"""CPU-only pilot checks. Exact AST functions; no renderer/capture/UI imports."""
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
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'app/audio'))
from analyzer import AudioAnalyzer
from audio_frame import AudioFrame
from signal_processor import SignalProcessor, VisualSignalConditioner
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from planet_canvas_dsp import PlanetCanvasDSP, held_planet, smoothstep
import preview_layers as layers
import world_catalog as catalog
import transition_catalog as transitions
import color_controls as colors
import cymatics_session


def tree(path):
    return ast.parse(Path(path).read_text(encoding='utf-8'))


def functions(path, names, env):
    nodes = [n for n in tree(path).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)
    return env


def audio_env(path):
    return functions(path, ['analyze_samples'], dict(AudioFrame=AudioFrame))['analyze_samples']


def audio_state():
    return (AudioAnalyzer(), SignalProcessor(smoothing=.5),
            VisualSignalConditioner(quiet_threshold=.06),
            {k:OnsetDetector(threshold=.2) for k in ('bass','mids','highs')})


def payload(t, spread=0., fullness=0., confidence=1., valid=True):
    return dict(version=1,valid=valid,analyzed_seconds=t,
                signal_confidence=confidence,spectral_spread=spread,fullness=fullness)


def renderer_type():
    source = tree(ROOT/'app/visuals/renderer.py')
    cls = next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    names = ('planet_dsp_eligible','reset_planet_dsp','accept_planet_audio','planet_spatial_amounts')
    methods = [n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(methods)==4, 'Duplicate renderer methods'
    node = ast.ClassDef(name='CPUPlane',bases=[],keywords=[],body=methods,decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[]))
    env={};exec(compile(module,'renderer-pilot-methods','exec'),env)
    # Execute the exact uniform assignment and its gate, with a mocked uniform.
    render=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='render')
    matches=[i for i,n in enumerate(render.body) if isinstance(n,ast.Assign)
             and "self.program['u_spatial_treatments'].value" in ast.unparse(n.targets[0])]
    assert len(matches)==1
    i=matches[0]
    start=next(j for j in range(i) if isinstance(render.body[j],ast.Assign)
               and ast.unparse(render.body[j].targets[0])=='spatial_amounts')
    assert 'treatment_weights' in ast.unparse(render.body[start].value)
    assert any("self.program['u_planet_spatials'].value" in ast.unparse(n) for n in render.body[start:i])
    routing=ast.Module(body=render.body[start:i+1],type_ignores=[])
    routing_code=compile(routing,'renderer-spatial-uniform','exec')
    def draw(self,seconds,rewound=False):
        self.seconds=seconds
        exec(routing_code,dict(self=self,current_time=seconds,rewound=rewound,studio_audio=None,
                               treatment_weights=layers.treatment_weights,
                               SPATIAL_TREATMENTS=layers.SPATIAL_TREATMENTS))
    def create(self):
        self.planet_dsp_pilot=False;self.planet_dsp=None;self.debug_state=5
        self.debug_sequence=();self.transition_sequence=False
        self.transition_settings=transitions.validate_settings()
        self.layer_profiles={};self.seconds=0.
        self.program={key:SimpleNamespace(value=(0.,0.,0.)) for key in ('u_spatial_treatments','u_planet_spatials')}
    cls=env['CPUPlane'];cls.__init__=create;cls.draw=draw
    cls.state_at=lambda self,t:self.debug_state
    return cls


def mapping_checks(CPUPlane):
    # Thresholds, monotonicity, confidence and asymmetrical analytic easing.
    for low,high in ((.04,.35),(.10,.65)):
        values=[smoothstep(low,high,x) for x in np.linspace(0.,1.,101)]
        assert values==sorted(values) and values[0]==0. and values[-1]==1.
        assert smoothstep(low,high,low)==0. and smoothstep(low,high,high)==1.
    def run(spread,fullness,confidence=1.,step=.02):
        m=PlanetCanvasDSP()
        for i in range(1,round(4./step)+1):m.observe(payload(i*step,spread,fullness,confidence))
        return m
    sparse=run(0.,0.);b=(.65,.55,.37)
    assert np.allclose(sparse.ratios,(.6+.4*math.exp(-4./1.2),.5+.5*math.exp(-4./1.2)),atol=1e-12)
    for x in np.linspace(0.,1.,31):
        m=run(float(x),float(x));a=m.apply(b)
        assert .6*b[0]<=a[0]<=b[0] and .5*b[1]<=a[1]<=b[1] and a[2]==b[2]
        assert m.apply((0.,0.,.37))==(0.,0.,.37)
    assert run(1.,1.).ratios==(1.,1.)
    assert run(0.,0.,0.).ratios==(1.,1.)
    assert sparse.ratios[0]<run(0.,0.,.5).ratios[0]<1.
    assert np.allclose(run(0.,0.,step=.01).ratios,sparse.ratios,atol=1e-12)
    prior=sparse.ratios
    for _ in range(200):sparse.observe(payload(4.,1.,1.));sparse.apply(b)
    assert sparse.ratios==prior
    # A fresh invalid snapshot releases to neutral, ignoring fading features.
    sparse.observe(payload(4.1,0.,0.,valid=False))
    assert np.allclose(sparse.ratios,[v+(1.-v)*-math.expm1(-.1/.7) for v in prior])
    for bad in (None,{},dict(payload(4.2),version=2),dict(payload(4.2),version=True),
                dict(payload(4.2),fullness=float('nan')),dict(payload(4.2),spectral_spread=2.)):
        m=run(0.,0.);m.observe(bad);assert m.apply(b)==b
    m=run(0.,0.);m.observe(payload(1.));assert m.apply(b)==b # rewind
    m=run(0.,0.);m.observe(payload(5.));assert m.apply(b)==b # gap
    m=run(0.,0.);m.reset();assert m.apply(b)==b # EOF/source change
    m=PlanetCanvasDSP()
    for i in range(1,101):m.observe(payload(i*.02),source_id='A')
    m.observe(payload(.02),source_id='B')
    fresh=PlanetCanvasDSP();fresh.observe(payload(.02),source_id='B')
    assert m.ratios==fresh.ratios and m.last_time==fresh.last_time
    # Actual renderer methods + uniform statement: manual ceilings and contexts.
    r=CPUPlane();base=(.65,.55,0.)
    assert r.planet_spatial_amounts(base) is base and r.planet_dsp is None
    r.planet_dsp_pilot=True
    for i in range(1,101):r.accept_planet_audio(SimpleNamespace(descriptors=payload(i*.02)))
    ratios=r.planet_dsp.ratios
    newbase=(.20,.80,.10);assert r.planet_spatial_amounts(newbase)==(newbase[0]*ratios[0],newbase[1]*ratios[1],.10)
    for state,seq,tr,pair in ((0,(),False,None),(36,(),False,None),(5,(5,),False,None),
                              (5,(5,7),True,[5,7]),(5,(),False,[7,5]),(7,(),False,None)):
        r.debug_state=state;r.debug_sequence=seq;r.transition_sequence=tr
        r.transition_settings=transitions.validate_settings(dict(pair=pair or []))
        assert not r.planet_dsp_eligible()
        assert r.planet_spatial_amounts(base) is base and r.planet_dsp.ratios==(1.,1.)
        r.accept_planet_audio(SimpleNamespace(descriptors=payload(.02)))
        r.debug_state=5;r.debug_sequence=();r.transition_sequence=False
        r.transition_settings=transitions.validate_settings()
        assert r.planet_spatial_amounts(base)==base # no re-entry stale signal
    r.layer_profiles={'cosmic':dict(mode='meld',seconds=22.,items=[
        dict(id='elastic_lenses',enabled=True,amount=.65),
        dict(id='braided_flow',enabled=True,amount=.55),
        dict(id='artifacts',enabled=True),dict(id='ink_archipelago',enabled=True),
        dict(id='stars',enabled=True),dict(id='shooting_stars',enabled=True)])}
    original=deepcopy(r.layer_profiles)
    for i in range(1,100):r.accept_planet_audio(SimpleNamespace(descriptors=payload(i*.02)))
    before=r.planet_dsp.ratios
    for t in np.linspace(0.,90.,100):r.draw(float(t))
    assert r.planet_dsp.ratios==before and r.layer_profiles==original
    assert r.program['u_spatial_treatments'].value==r.planet_dsp.apply(base)
    r.draw(0.,True);assert r.program['u_spatial_treatments'].value==base
    r.layer_profiles={};r.draw(1.);assert r.program['u_spatial_treatments'].value==(0.,0.,0.)
    return dict(sparse_after_four_seconds=list(sparse.ratios),bounds=[.6,.5,1.],context_cases=6)


def analysis_checks(analyze):
    baseline=audio_env(ROOT/'work/planet-canvas-dsp-pilot-01/baseline/live_visual_test.py')
    old=audio_state();off=audio_state();on=audio_state()
    # Fail loudly if flag-off ever attempts additional analysis.
    off[0].describe_samples=lambda *a,**k:(_ for _ in ()).throw(AssertionError('off DSP call'))
    rng=np.random.default_rng(2917);legacy=0
    for i in range(120):
        pcm=(rng.normal(0.,.04,(2048,2))*min(1.,i/20.)).astype(np.float32)
        a=baseline(pcm,*old);b=analyze(pcm,*off);c=analyze(pcm,*on,descriptors=True,source_id='fixture')
        for k,v in a.__dict__.items():
            if k=='descriptors':assert b.descriptors is None;continue
            if isinstance(v,np.ndarray):assert np.array_equal(v,getattr(b,k)) and np.array_equal(v,getattr(c,k))
            else:assert v==getattr(b,k)==getattr(c,k),(k,i)
        legacy+=1
    assert not hasattr(off[0],'_descriptors')
    # Antiphase stereo has zero downmix but nonzero channel power.
    tone=.1*np.sin(np.arange(2048)*2.*np.pi*440./48000.)
    stereo=np.column_stack((tone,-tone));s=audio_state()
    frame=analyze(stereo,*s,descriptors=True,source_id='antiphase')
    assert frame.energy==0. and frame.descriptors['valid'] and frame.descriptors['intensity']>0.
    assert frame.descriptors==AudioAnalyzer().describe_samples(stereo,48000,'antiphase').to_dict()
    assert not AudioAnalyzer().describe_samples(stereo.mean(axis=1),48000).valid
    # Established descriptor math at equal sample endpoints, different partitions.
    pcm=np.tile(stereo,(8,1));a=AudioAnalyzer();b=AudioAnalyzer()
    x=a.describe_samples(pcm,48000,'A').to_dict()
    for start in range(0,len(pcm),256):y=b.describe_samples(pcm[start:start+256],48000,'A').to_dict()
    assert x==y
    reset=b.describe_samples(stereo,48000,'B').to_dict()
    assert reset==AudioAnalyzer().describe_samples(stereo,48000,'B').to_dict()
    b.reset_descriptors();assert not b._descriptors.snapshot.valid
    return dict(exact_legacy_frames=legacy,antiphase_intensity=frame.descriptors['intensity'],partition_endpoint=True)


def studio_env():
    env=dict(json=json,math=math,Path=Path,sys=sys,deepcopy=deepcopy,ROOT=ROOT,
             validate_cymatics=cymatics_session.validate,cymatics_defaults=cymatics_session.defaults)
    env.update(vars(layers));env.update(vars(catalog))
    env.update(validate_settings=transitions.validate_settings,compatible=transitions.compatible,
               RECIPES=transitions.RECIPES,transition_description=transitions.description,
               validate_colors=colors.validate_colors,scene_colors=colors.scene_colors,targets_for=colors.targets_for)
    constants={'BLEND_FORMS','AIR_FORMS','EARTH_FORMS','FOG_FORMS','PLASMA_FORMS','LIVE_FORMS'}
    nodes=[n for n in tree(ROOT/'app/visuals/renderer.py').body if isinstance(n,ast.Assign)
           and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'roster','exec'),env)
    constants={'SPEEDS','SOURCES','PLANET_PALETTES','DEFAULTS','STUDIO_TREES'}
    nodes=[n for n in tree(ROOT/'app/visuals/studio.py').body if isinstance(n,ast.Assign)
           and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'studio-constants','exec'),env)
    functions(ROOT/'app/visuals/studio.py',('selection_scope','selected_node','selection_states',
              'path_for_state','validate_session','validate_isolation','preview_profiles',
              'color_scope_for_states','command','session_states'),env)
    return env


def session_checks():
    e=studio_env();validate=e['validate_session'];command=e['command']
    a=json.loads((ROOT/'work/planet-canvas-dsp-pilot-01/review-A.json').read_text())
    b=json.loads((ROOT/'work/planet-canvas-dsp-pilot-01/review-B.json').read_text())
    copy=deepcopy(b);assert a==dict(b,planet_dsp_pilot=False)
    va=validate(a);vb=validate(b)
    ca=command(va,Path('output'));cb=command(vb,Path('output'))
    assert cb==ca+['--planet-dsp-pilot'] or [x for x in cb if x!='--planet-dsp-pilot']==ca
    assert '--planet-dsp-pilot' not in ca and '--planet-dsp-pilot' in cb
    assert b==copy
    for version in (1,2,3):
        data=deepcopy(a);data['version']=version;data.pop('planet_dsp_pilot')
        assert not validate(data).get('planet_dsp_pilot',False)
    for bad in ('true',1,None):
        try:validate(dict(b,planet_dsp_pilot=bad))
        except ValueError:pass
        else:raise AssertionError('Malformed session pilot accepted')
    for selection in ([],['cosmic','galaxy'],['elements','water']):
        v=validate(dict(b,selection=selection))
        # The saved choice is deliberately promoted in Main Studio; renderer
        # endpoint gates still prevent Planet modulation on other worlds.
        assert ('--planet-dsp-pilot' in command(v,Path('output')))==(v['selection_scope']=='main')
    v=validate(dict(b,transitions=dict(pair=[5,7])));assert '--planet-dsp-pilot' in command(v,Path('output'))
    try:command(validate(dict(b,source='Synthetic preview')),Path('output'))
    except ValueError:pass
    else:raise AssertionError('Synthetic pilot has no descriptors')
    # Parse the actual CLI declarations only, excluding imports/startup/actions.
    for file in ('live_visual_test.py','replay_test.py'):
        nodes=tree(ROOT/'app/visuals'/file).body
        main=(next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name=='main')
              if file=='replay_test.py' else
              next(n for n in nodes if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)))
        stop=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Name) and t.id=='args' for t in n.targets))
        code=compile(ast.Module(body=main.body[:stop+1],type_ignores=[]),'cli','exec')
        for on in (False,True):
            env=dict(argparse=argparse,Path=Path,LIVE_STATES=catalog.LIVE_STATES,
                     parse_settings=transitions.parse_settings,parse_layers=layers.parse_layers,parse_colors=colors.parse_colors)
            previous=sys.argv
            try:
                sys.argv=[file]+(['fixture.wav'] if file=='replay_test.py' else [])+(['--planet-dsp-pilot'] if on else [])
                exec(code,env);assert env['args'].planet_dsp_pilot is on
            finally:sys.argv=previous
    return dict(session_versions=[1,2,3],matched_presets=True,cli_defaults=False)


def replay_checks(analyze,CPUPlane):
    # Run the actual replay orchestration with numerical PCM and fake window.
    class CPUReplay(CPUPlane):
        instances=[]
        def __init__(self,**kwargs):
            super().__init__();self.parameters=SimpleNamespace();self.frames=[]
            self.echo_weight=0.;self.shockwaves=[];self.blast_events=[]
            self.planet_visits=0;self.flow_rate=.35
            self.instances.append(self)
        def set_galaxy_start(self,*a):pass
        def configure_transitions(self,cfg):
            self.transition_settings=transitions.validate_settings(cfg)
            self.transition_sequence=bool(self.transition_settings['pair'])
        def create(self):pass
        def consume_pcm(self,pcm):pass
        def should_close(self):return False
        def render(self,elapsed_time):
            self.draw(elapsed_time);self.frames.append((elapsed_time,self.program['u_spatial_treatments'].value))
        def swap_buffers(self):pass
        def poll_events(self):pass
        def close(self):pass
    pcm=(.1*np.sin(np.arange(2048*48)*2.*np.pi*440./48000.))
    raw=np.column_stack((pcm,-pcm)).__mul__(32767).astype(np.int16).tobytes()
    class PCMFile:
        def __enter__(self):self.offset=0;return self
        def __exit__(self,*a):pass
        def getframerate(self):return 48000
        def getnchannels(self):return 2
        def getsampwidth(self):return 2
        def readframes(self,n):
            result=raw[self.offset:self.offset+n*4];self.offset+=len(result);return result
    env=dict(np=np,math=math,time=SimpleNamespace(perf_counter=lambda:0.,sleep=lambda t:None),
             wave=SimpleNamespace(open=lambda *a:PCMFile()),Renderer=CPUReplay,AudioAnalyzer=AudioAnalyzer,
             SignalProcessor=SignalProcessor,VisualSignalConditioner=VisualSignalConditioner,
             OnsetDetector=OnsetDetector,VisualParameterMapper=VisualParameterMapper,
             analyze_samples=analyze,LIVE_STATES=catalog.LIVE_STATES,
             validate_layers=layers.validate_layers,layers_at=layers.layers_at,
             configure_colors=lambda *a:None)
    replay=functions(ROOT/'app/visuals/replay_test.py',['replay'],env)['replay']
    cfg={'cosmic':dict(mode='together',seconds=22.,items=[dict(id=k,enabled=True,amount=.65)
          for k in ('elastic_lenses','braided_flow')])}
    for on,state,states,pair in ((False,'canvas',None,None),(True,'canvas',None,None),
                                 (True,'blend',None,None),(True,'canvas',['canvas'],None),
                                 (True,'canvas',None,[5,7]),(True,'galaxy',None,None)):
        replay(Path('antiphase.wav'),speed=0.,state=state,layers=cfg,planet_dsp_pilot=on,
               states=states,transitions=dict(pair=pair or []))
        r=CPUReplay.instances[-1]
        eligible=on and state=='canvas' and not states and not pair
        if eligible:
            assert r.planet_dsp is not None and r.frames[-1][1][0]<.65
            assert r.planet_dsp.ratios==(1.,1.) # EOF cleanup
        else:assert r.planet_dsp is None
    return dict(mocked_replay_contexts=6,actual_orchestration=True)


def live_checks(analyze,CPUPlane):
    # Actual live owner function, with supplied PCM and a fake stream module.
    # No backend import, device access, capture thread or window is involved.
    instances=[]
    tone=.1*np.sin(np.arange(2048)*2.*np.pi*440./48000.)
    pcm=np.column_stack((tone,-tone))
    class SuppliedCapture:
        def __init__(self,**kwargs):pass
        def find_device(self):return 'CPU fixture, not an audio device'
    class SuppliedStream:
        def __init__(self,capture,analyze):
            self.analyze=analyze;self.worker=SimpleNamespace(is_alive=lambda:False)
        def start(self):pass
        def stop(self):pass
        def drain(self):return [(0.,self.analyze(pcm))]
    class LiveCPU(CPUPlane):
        def __init__(self,**kwargs):
            super().__init__();self.parameters=SimpleNamespace();self.polls=0
            instances.append(self)
        def set_galaxy_start(self,*a):pass
        def configure_transitions(self,cfg):
            self.transition_settings=transitions.validate_settings(cfg)
            self.transition_sequence=bool(self.transition_settings['pair'])
        def create(self):pass
        def should_close(self):return self.polls>=12
        def consume_pcm(self,*a):pass
        def render(self):self.draw(self.polls*2048./48000.)
        def swap_buffers(self):pass
        def poll_events(self):self.polls+=1
        def close(self):pass
    env=dict(time=SimpleNamespace(perf_counter=lambda:0.,sleep=lambda t:None),
             AudioCapture=SuppliedCapture,AudioAnalyzer=AudioAnalyzer,
             SignalProcessor=SignalProcessor,VisualSignalConditioner=VisualSignalConditioner,
             VisualParameterMapper=VisualParameterMapper,Renderer=LiveCPU,
             OnsetDetector=OnsetDetector,LIVE_STATES=catalog.LIVE_STATES,
             validate_layers=layers.validate_layers,configure_colors=lambda *a:None,
             analyze_samples=analyze)
    main=functions(ROOT/'app/visuals/live_visual_test.py',['main'],env)['main']
    previous=sys.modules.get('capture_stream')
    try:
        sys.modules['capture_stream']=SimpleNamespace(CaptureStream=SuppliedStream)
        for on,state in ((False,'canvas'),(True,'canvas'),(True,'blend'),(True,'galaxy')):
            with redirect_stdout(io.StringIO()):main(state=state,quiet=True,planet_dsp_pilot=on)
            r=instances[-1]
            assert (r.planet_dsp is not None)==(on and state=='canvas')
            if r.planet_dsp is not None:assert r.planet_dsp.ratios==(1.,1.)
    finally:
        if previous is None:sys.modules.pop('capture_stream',None)
        else:sys.modules['capture_stream']=previous
    return dict(mocked_live_contexts=4,actual_owner_function=True,capture_threads=0)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');CPUPlane=renderer_type()
    report=dict(evidence_class='offline numerical and AST-isolated mocked routing; no GPU/capture/UI',
                analysis=analysis_checks(analyze),mapping=mapping_checks(CPUPlane),
                sessions=session_checks(),replay=replay_checks(analyze,CPUPlane),
                live=live_checks(analyze,CPUPlane))
    assert not any(k in sys.modules for k in ('glfw','moderngl','capture','soundcard','tkinter'))
    if args.output:args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));print('Planet Canvas DSP CPU checks PASS')


if __name__=='__main__':main()
