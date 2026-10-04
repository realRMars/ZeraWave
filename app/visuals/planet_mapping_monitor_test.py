"""Standalone CPU routing/telemetry tests; no Tk, graphics or real capture."""
import argparse
import ast
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app/audio'))
from planet_canvas_dsp_test import audio_env,audio_state,tree
from planet_mapping_monitor import PlanetMonitor,decode,meter,rows,PREFIX,MAX_PACKET,configure
from studio_color_link import ColorInbox,ColorLink
import numpy as np

def submissions():
    return dict(u_scale=.2,u_sparkle=.3,u_impact=.4,u_flux=.5,u_star_time=12.,
        u_planet_star_flight=(1.,15.,.6),background_star_rate=1.45,
        u_shooting_stars=1.,u_spatial_treatments=(.4,.3,0.),u_material_mix=(.7,.3,0.),
        u_new_materials=(0.,0.,0.),u_echo_weave=0.,envelopers=(0.,0.,0.),enveloper_failed=False)

def controls():return dict(surface_pilot=True,star_pilot=True,spatial_base=(.65,.55,0.),color_revision=3)

def frame():
    f=SimpleNamespace(**{k:.2 for k in ('bass','mids','highs','flux','bass_onset','mids_onset','highs_onset','tempo','beat_confidence')})
    f.band12=dict(edges=list(range(13)),levels=[i/12. for i in range(12)],unresolved=[False]*12)
    f.descriptors=dict(version=1,valid=True,analyzed_seconds=.1,signal_confidence=.7,spectral_spread=.3,fullness=.4)
    f.planet_star_audio=dict(sample_seconds=.1,bass_attack=.8,low_band_level=17.)
    return f

def telemetry_checks():
    clock=[0.];m=PlanetMonitor('LIVE','resolved endpoint',{'surface':True},clock=lambda:clock[0])
    f=frame();before=deepcopy(f.__dict__);s=submissions();c=controls();original=deepcopy((s,c))
    m.observe(f,2048,7.);assert m.audio is None and m.packet(0.,s,c) is None
    m.enable(True);m.observe(f,2048,8.);p=decode(m.packet(.1,s,c));assert p
    assert p['mode']=='LIVE' and p['source']=='resolved endpoint' and p['audio']['frame']==2
    assert p['config']==m.config and p['run']==m.run and p['submitted']['u_impact']==.4
    assert p['interval_attack_peak']==.8 and p['peak_frame']==2
    assert f.__dict__==before and (s,c)==original
    assert m.packet(.11,s,c) is None
    clock[0]=.21;f.planet_star_audio['bass_attack']=0.;m.observe(f,2048)
    p2=decode(m.packet(.21,s,c));assert p2['interval_attack_peak']==0. and p2['peak_frame'] is None
    clock[0]=2.;stale=decode(m.packet(2.,s,c));assert stale['audio_age_seconds']>1.
    m.enable(False);assert m.audio is None and m.packet(2.,s,c) is None
    m.enable(True);assert decode(m.packet(2.,s,c))['audio'] is None
    assert m.samples==6144 and m.sequence==3
    replay=PlanetMonitor('REPLAY','file.wav',{'surface':False},clock=lambda:clock[0]);assert replay.config!=m.config and replay.run!=m.run
    replay.enable(True);q=decode(replay.packet(0.,s,c));assert q['mode']=='REPLAY'
    assert meter(-1.)==0. and meter(3.)==1. and meter(1.375,1.,1.75)==.5
    assert meter(None) is None and meter(float('nan')) is None
    assert decode('x'*(MAX_PACKET+1)) is None and decode('{') is None
    for field,value in [('mode','fake'),('run',None),('audio',{'frame':-1}),('submitted',{}),('config',None)]:
        bad=deepcopy(p);bad[field]=value;assert decode(json.dumps(bad)) is None
    bad=deepcopy(p);bad['submitted']['u_scale']=float('nan');assert decode(json.dumps(bad)) is None
    route={label:(driver,value,bar) for label,driver,value,bar in rows(p)}
    assert route['Elastic amount'][1]==.4 and 'Spread' in route['Elastic amount'][0]
    assert route['Background star rate'][1]==1.45 and route['Background wake envelope'][1]==.6
    assert 'Manual/list/time' in route['Shooting star enable'][0]
    assert route['Fullness'][1]==.4 and len(route)==28
    invalid=deepcopy(p);invalid['audio']['descriptors']['valid']=False
    assert all(value is None and bar is None for label,driver,value,bar in rows(invalid)
               if label in ('Spectral spread','Fullness'))
    return dict(binding='run/source/config/input frame/render clock PASS',clamps='PASS',pulse_hold='PASS',
                missing_stale='PASS',modes='LIVE/REPLAY PASS',rows=len(route))

def pipe_checks():
    inbox=ColorInbox.__new__(ColorInbox);inbox.closed=False;inbox.lock=threading.Lock();inbox.pending_monitor=None
    inbox.accept(b'{"kind":"planet-monitor","enabled":true}')
    inbox.accept(b'{"kind":"planet-monitor","enabled":false}')
    assert inbox.take_monitor() is False and inbox.take_monitor() is None
    class Log(io.StringIO):
        def close(self):self.saved=self.getvalue()
    m=PlanetMonitor('LIVE','endpoint',{},clock=lambda:1.);m.enable(True);m.observe(frame(),2048)
    packet=m.packet(1.,submissions(),controls())
    log=Log();link=ColorLink.__new__(ColorLink);link.condition=threading.Condition();link.status={};link.monitor_latest=None
    link.process=SimpleNamespace(stdout=io.BytesIO(('hello\n'+PREFIX+packet+'\n'+PREFIX+'bad\n'+
             'ZERAWAVE_COLOR {"applied":3}\n').encode()));link.log=log
    link._read();latest=link.get_monitor();assert latest[0]['audio']['frame']==1 and link.status=={'applied':3}
    latest[0]['source']='changed';assert link.get_monitor()[0]['source']=='endpoint'
    assert PREFIX not in log.saved and 'hello' in log.saved and 'applied' in log.saved
    link.closed=False;link.pending_monitor=None;link.submit_monitor(False);assert link.monitor_latest is None
    assert link.pending_monitor=={'kind':'planet-monitor','enabled':False}
    return dict(latest_only=True,telemetry_not_logged=True,color_ack_preserved=True,independent_toggle=True)

def analysis_preservation():
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');off=audio_state();on=audio_state()
    m=PlanetMonitor('LIVE','supplied PCM',{},clock=lambda:1.);m.enable(True)
    rng=np.random.default_rng(8271);count=120
    for i in range(count):
        pcm=rng.normal(0.,.08,(2048,2)).astype(np.float32)
        a=analyze(pcm,*off,descriptors=True,star_attack=True,source_id='fixture')
        b=analyze(pcm,*on,descriptors=True,star_attack=True,source_id='fixture')
        before=deepcopy(b.__dict__);m.observe(b,len(pcm),i)
        def equal(x,y):
            if isinstance(x,np.ndarray):return np.array_equal(x,y)
            if isinstance(x,dict):return x.keys()==y.keys() and all(equal(x[k],y[k]) for k in x)
            return x==y
        assert equal(a.__dict__,b.__dict__) and equal(before,b.__dict__)
    return dict(existing_analysis_frames_each=count,exact_frame_equality=True,monitor_mutations=0)

def submission_checks():
    cls=next(n for n in tree(ROOT/'app/visuals/renderer.py').body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    render=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='render')
    node=next(n for n in render.body if isinstance(n,ast.If) and 'self.planet_monitor.enabled' in ast.unparse(n.test))
    # Running the real telemetry submission block must never get GPU uniforms.
    class Program:
        def __getitem__(self,key):raise AssertionError('GPU getter '+key)
    m=PlanetMonitor('LIVE','fixture',{},clock=lambda:1.);m.enable(True);m.observe(frame(),2048)
    r=SimpleNamespace(planet_monitor=m,program=Program(),parameters=SimpleNamespace(scale=.2,sparkle=.3,flux=.5),
        impact_envelope=.4,star_time=12.,star_rate=1.,planet_star_flight=SimpleNamespace(rate=1.45),
        echo_weight=.0,enveloper_failed=False,layer_profiles={},color_inbox=SimpleNamespace(revision=3),
        _color_applied_revision=3,
        planet_dsp_eligible=lambda:True,planet_star_attack_eligible=lambda:True)
    env=dict(self=r,current_time=1.,star_flight=(1.,15.,.6),shooting_stars=1.,spatial_amounts=(.4,.3,0.),
        material_mix=(.7,.3,0.),new_materials=(0.,0.,0.),weights=(0.,0.,0.),state=5,
        treatment_weights=lambda *a:(.65,.55,0.),SPATIAL_TREATMENTS=())
    from contextlib import redirect_stdout
    out=io.StringIO()
    with redirect_stdout(out):exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-renderer-telemetry','exec'),env)
    p=decode(out.getvalue()[len(PREFIX):]);assert p['submitted']==json.loads(json.dumps(submissions()))
    # Held-only configuration guard does not allocate a monitor elsewhere.
    for state,sequence,pair in ((0,(),[]),(36,(),[]),(5,(5,),[]),(5,(),[5,7])):
        r=SimpleNamespace(debug_state=state,debug_sequence=sequence,transition_sequence=False,transition_settings={'pair':pair})
        configure(r,'LIVE','source');assert not hasattr(r,'planet_monitor')
    return dict(actual_submission_binding=True,GPU_getters=0,held_only=True)

def view_checks():
    # Run the real window refresh adapter with inert widgets; no Tk import/window.
    cls=next(n for n in tree(ROOT/'app/visuals/planet_mapping_monitor.py').body if isinstance(n,ast.ClassDef) and n.name=='MonitorWindow')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='refresh')
    from planet_mapping_monitor import rows,meter,STALE_SECONDS
    env=dict(time=time,rows=rows,meter=meter,STALE_SECONDS=STALE_SECONDS)
    exec(compile(ast.Module(body=[method],type_ignores=[]),'actual-monitor-view','exec'),env)
    class Var:
        def __init__(self,v=''):self.v=v
        def set(self,v):self.v=v
        def get(self):return self.v
    class Label:
        def configure(self,**kw):self.text=kw['text']
    class Table:
        def __init__(self):self.items={}
        def exists(self,i):return i in self.items
        def insert(self,*a,**kw):self.items[kw['iid']]=kw
        def item(self,i,**kw):self.items[i]=kw
    view=SimpleNamespace(enabled=Var(True),status=Var(),identity=Var(),band_labels=[Label() for _ in range(12)],
                         band_bars=[{} for _ in range(12)],table=Table())
    m=PlanetMonitor('REPLAY','file.wav',{});m.enable(True);m.observe(frame(),2048)
    p=decode(m.packet(1.,submissions(),controls()));refresh=env['refresh']
    refresh(view,(p,time.perf_counter()),True);assert 'REPLAY — current' in view.status.get()
    assert 'frame 1' in view.identity.get() and len(view.table.items)==28
    before=deepcopy(view.table.items);view.enabled.set(False);refresh(view,None,False)
    assert 'PAUSED' in view.status.get() and view.table.items==before
    view.enabled.set(True);refresh(view,(p,time.perf_counter()-2.),True);assert 'STALE' in view.status.get()
    refresh(view,None,False);assert 'Stopped / unavailable' in view.status.get()
    return dict(actual_adapter=True,modes=True,pause_preserves_values=True,stale=True,stopped=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args()
    report=dict(evidence_class='CPU isolated actual routing and supplied PCM; no GPU/UI/capture/listening',
        telemetry=telemetry_checks(),pipe=pipe_checks(),analysis=analysis_preservation(),submission=submission_checks(),view=view_checks())
    assert not any(n in sys.modules for n in ('glfw','moderngl','soundcard','tkinter','capture'))
    if args.output:args.output.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));print('Planet mapping monitor CPU checks PASS')

if __name__=='__main__':main()
