"""CPU routing, target/mode/profile isolation and optional hidden native layout."""
import argparse,ast,hashlib,json,os,sys,tempfile,time
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from planet_audio_tuning import *
from band_attack_tuning import BandAttackTuning,PRESENTATION_BOUNDS,weighted
from star_tuning_profiles import TargetProfileStore,StarProfileStore,SHIPPED,LEGACY_SHIPPED,document,validate_document
from starfield_tuning import StarfieldTuningWindow,TARGETS,decode,MAX_PACKET,TARGET,ART_TARGET,STAR_BOUNDS
from star_profiles_test import install_widgets,restore_widgets,rejects
from spectrum_tuning_test import Widget,fft_frame

def remove_coverage_shader(s):
    if 'uniform ivec2 u_audio_forms;' in s:
        from rollout_source_test_helpers import pre_rollout_source
        s=pre_rollout_source('app/visuals/shaders/dream.frag',s)
    # Reverse this batch's explicit local-input additions before the historical
    # coverage reconstruction. Counts keep the unrelated-source equality strong.
    branch='    // [-2,-1] slots carry already-scaled local inputs, never authored gains.\n    if(gain<=-1.)return clamp(-1.-gain,0.,1.);\n'
    added='''    if(u_artifacts_listening_on.z==1) {
        art_bass=u_artifacts_listening_inputs.z;
        art_radial_pressure=art_bass*art_bass;
    }
    if(u_artifacts_listening_on.w==1)art_impact=u_artifacts_listening_inputs.w;
'''
    replacements_local=((branch,''),(added,''),('uniform ivec4 u_artifacts_listening_on;','uniform ivec2 u_artifacts_listening_on;'),
        ('uniform vec4 u_artifacts_listening_inputs;','uniform vec2 u_artifacts_listening_inputs;'),
        ('art_impact=clamp(art_impact*u_artifacts_audio.y','art_impact=clamp(impact*u_artifacts_audio.y'),
        ('art_bass=clamp(art_bass*u_artifacts_shape_audio.x','art_bass=clamp(bass_pressure*u_artifacts_shape_audio.x'),
        ('art_radial_pressure=clamp(art_radial_pressure*u_artifacts_shape_audio.y','art_radial_pressure=clamp(pressure*u_artifacts_shape_audio.y'))
    for new,old in replacements_local:
        assert s.count(new)==1,(new,s.count(new));s=s.replace(new,old,1)
    replacements=json.loads((ROOT/'work/planet-audio-coverage-01/shader-replacements.json').read_text())
    for row in reversed(replacements):
        if not row['new']:
            s=s.replace('    if(u_spatial_treatments.x>0.) {',row['old']+'    if(u_spatial_treatments.x>0.) {',1);continue
        assert s.count(row['new'])==row['count'];s=s.replace(row['new'],row['old'])
    return s

def shader_checks():
    p=ROOT/'app/visuals/shaders/dream.frag';current=p.read_text(encoding='utf8');s=remove_coverage_shader(current)
    original=(ROOT/'work/planet-audio-coverage-01/baseline/app/visuals/shaders/dream.frag').read_text(encoding='utf8')
    assert s==original
    assert f'uniform vec4 u_planet_audio[{UNIFORM_ROWS}];' in current
    # Every declared role is connected to a shader expression, not just telemetry.
    import re
    for target,rs in SPECS.items():
        if target.startswith('planet.enveloper.') or target.endswith('echo_weave'):continue
        for i,r in enumerate(rs):
            if target=='planet.surface_response' and i>=2:continue # Bound in actual Renderer clock below.
            assert re.search(r'planet_audio\([^;\n]*,'+str(INDEX[target])+','+str(i)+r'\)',current),(target,r)
    echo=(ROOT/'app/visuals/shaders/echo_weave.frag').read_text()
    for i in range(4):assert ',%d)'%i in echo
    env=(ROOT/'app/visuals/shaders/envelopers.frag').read_text()
    assert 'tuned(energy,0)' in env and 'tuned(energy,1)' in env
    assert 'exp(-delta/(.00001+.18*amount))' in env
    assert 'u_drift_time * (0.6 + sparkle * 1.2)' in current # Honest untuned phase.
    assert 'if (u_layer_mode == 1) return enabled;' in current
    # Neutral arithmetic is exact even on existing out-of-range intermediates.
    def gpu(v,g):return v if g==1. else clip(v*g)
    for v in (-.1,0.,.01,.2,.5,1.,1.4):assert gpu(v,1.)==v
    for v in (0.,.1,.4,1.):
        assert gpu(v,0.)==0. and 0.<=gpu(v,2.)<=1.
    return dict(exact_inverse_source=True,scoped_replacements=30,every_declared_role_bound=True,
        neutral_exact=True,ceilings=True,clocks_history_palette_geometry_preserved=True,
        limitations='No GLSL compilation or pixels; source and scalar expression checks only')

def model_checks(folder):
    assert set(t.target_id for t in TARGETS)=={TARGET,ART_TARGET,*SPECS} and len(TARGETS)==24
    tune=PlanetAudioTuning();on,rows=tune.resolve(True)
    assert on==0 and len(rows)==UNIFORM_ROWS and all(v==1. for row in rows for v in row)
    cases=0;files=set()
    for target,rs in SPECS.items():
        base=baseline(target);tune=PlanetAudioTuning()
        store=TargetProfileStore(target,folder/(target+'.json'),folder/'profiles');assert store.error is None and store.authored==base
        for i,r in enumerate(rs):
            c=dict(base,**{r['key']:0.});assert tune.submit(target,i+1,c)
            on,rows=tune.resolve(True);assert on==1
            changed=[(a,b,v) for a,row in enumerate(rows) for b,v in enumerate(row) if v!=1.]
            assert changed==[(INDEX[target]*2+i//4,i%4,0.)]
            assert tune.resolve(False)[0]==0 # Held/return isolation.
            for mode in (0,1,2):
                packet=tune.status(True,dict(bass=.2,flux=.3,sparkle=.4,impact=.5,raw_impact=.6),mode)[target]
                assert packet['role_active'][r['key']]==role_active(r,mode)
                if role_active(r,mode):assert packet['audio_terms'][r['key']]==0.
            for v in (-.01,r['bounds'][1]+.01,float('nan'),float('inf'),True,'1'):
                rejects(lambda v=v:validate(target,dict(base,**{r['key']:v})))
            cases+=1
        tuned=dict(base,**{rs[0]['key']:1.5})
        path=store.save_profile('Same title',tuned);files.add(path)
        assert store.load_profile(path)[1]==tuned and store.authored==base and not store.authored_path.exists()
        other=next(k for k in SPECS if k!=target);rejects(lambda:TargetProfileStore(other,folder/(other+'other.json')).load_profile(path))
        store.save_authored(tuned);assert TargetProfileStore(target,store.authored_path).authored==tuned
        tune.submit(target,100,tuned,tuned);tune.submit(target,101,dict(base,enabled=False));tune.resolve(True)
        assert tune.gains(target)[0]==1.5 and tune.state[target]['settings']==dict(tuned,enabled=False)
        assert not tune.submit(target,100,base)
    assert len(files)==22
    # Version1 Starfield files migrate neutrally in memory, without rewriting.
    legacy=dict(version=1,target=TARGET,kind='authored',name='Authored',values={k:v for k,v in LEGACY_SHIPPED.items() if k!='enabled'})
    path=folder/'star.json';path.write_text(json.dumps(legacy));before=path.read_bytes()
    assert StarProfileStore(path).authored==SHIPPED and path.read_bytes()==before
    for key in PRESENTATION_BOUNDS:
        c=dict(SHIPPED,**{key:0.});bt=BandAttackTuning(authored=SHIPPED);bt.submit(1,c);bt.apply_without_detector()
        assert bt.settings==c and bt.revision==1 and bt.previous is None
    from studio_color_link import ColorInbox
    inbox=object.__new__(ColorInbox);import threading
    inbox.closed=False;inbox.lock=threading.Lock();inbox.pending_planet_tuning={};inbox.planet_tuning_revisions={}
    for target in SPECS:
        for revision in range(1,101):inbox.accept(json.dumps(dict(kind='planet-tuning',target=target,revision=revision,settings=baseline(target))).encode())
    pending=inbox.take_planet_tuning();assert len(pending)==22 and all(p[1]==100 for p in pending) and not inbox.pending_planet_tuning
    packet=dict(version=1,pilot_active=False,settings=SHIPPED,planet_tuning=PlanetAudioTuning().status(True,dict(bass=.1,flux=.2,sparkle=.3,impact=.4,raw_impact=.5),2))
    text=json.dumps(packet,separators=(',',':'));assert decode(text) and len(text.encode())<MAX_PACKET
    return dict(targets=24,roles=cases,bounds_cases=cases*6,target_slots_isolated=True,context_OFF_neutral=True,
        mode_inactive_roles=True,profile_files=len(files),same_name_isolation=True,wrong_target_rejected=True,
        authored_reset_relaunch=True,legacy_star_migration_no_rewrite=True,pending22_bounded=True,packet_bytes=len(text.encode()),packet_limit=MAX_PACKET)

def stage_checks():
    """Execute actual postprocess draw with inert graphics resources."""
    class Program(dict):
        def __missing__(self,key):v=SimpleNamespace(value=None);self[key]=v;return v
    tree=ast.parse((ROOT/'app/visuals/envelopers.py').read_text())
    fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='draw')
    env=dict(moderngl=SimpleNamespace(TRIANGLE_STRIP=2));exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-Enveloper-draw','exec'),env)
    no=lambda *a,**kw:None
    p=Program();records=[];resets=[]
    s=SimpleNamespace(resize=no,last_time=None,last_state=None,reset=lambda:resets.append(1),
        targets=[SimpleNamespace(use=no)]*3,textures=[SimpleNamespace(use=no)]*3,
        ctx=SimpleNamespace(viewport=None,screen=SimpleNamespace(use=no)),size=(320,180),index=0,valid=False,program=p,
        vao=SimpleNamespace(render=lambda **kw:records.append({k:v.value for k,v in p.items()})))
    audio=SimpleNamespace(scale=.2,flux=.3,sparkle=.4)
    for mode in range(3):
        weights=[0.]*3;weights[mode]=.7
        gains=((1.5,),(1.,.5),(.4,1.7))
        env['draw'](s,Program(),SimpleNamespace(render=no),(640,360),mode*.1,5,weights,audio,{},gains)
        row=records[-2]
        assert row['mode']==mode+1 and row['audio_gains']==(gains[mode]+(1.,1.))[:2]
        assert row['audio_tuning_on']==1 and row['energy']==.45*.2+.35*.3+.20*.4
    assert not resets and s.valid
    env['draw'](s,Program(),SimpleNamespace(render=no),(640,360),.4,5,(1.,0.,0.),audio,{})
    assert records[-2]['audio_tuning_on']==0 and records[-2]['audio_gains']==(1.,1.) and not resets
    # Actual Echo history method with preallocated inert resources.
    tree=ast.parse((ROOT/'app/visuals/renderer.py').read_text())
    fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='update_echo')
    e=dict(moderngl=SimpleNamespace(TRIANGLE_STRIP=2));exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-Echo-update','exec'),e)
    tuning=PlanetAudioTuning();c=dict(baseline('planet.material.echo_weave'),impact_injection=0.,flux_advection=1.5)
    tuning.submit('planet.material.echo_weave',1,c);tuning.resolve(True)
    ep=Program();calls=[]
    echo=SimpleNamespace(program=Program(),ctx=SimpleNamespace(fbo=SimpleNamespace(use=no),screen=SimpleNamespace(use=no),viewport=(0,0,640,360)),
        echo_resources=([SimpleNamespace(use=no)]*2,[SimpleNamespace(use=no,clear=lambda:calls.append('clear'))]*2,ep,SimpleNamespace(render=lambda **kw:calls.append('draw'))),
        echo_last_time=0.,echo_remainder=0.,echo_clock=0.,parameters=SimpleNamespace(scale=.2,flux=.3,sparkle=.4,impact=.7),
        planet_audio_tuning=tuning,planet_audio_active=True)
    e['update_echo'](echo,.1,.8)
    assert ep['audio'].value==(.2,.3,.4,.7) and ep['audio_gains'].value==(1.,1.5,1.,0.)
    assert ep['audio_tuning_on'].value==1 and calls.count('draw')==6 and 'clear' not in calls
    echo.planet_audio_active=False;e['update_echo'](echo,.2,.8)
    assert ep['audio_gains'].value==(1.,)*4 and ep['audio_tuning_on'].value==0 and 'clear' not in calls
    return dict(actual_Enveloper_draw=True,leading_mode_gains=True,caller_default_neutral=True,no_edit_history_reset=True,
        actual_Echo_update=True,raw_impact_retained=True,existing60Hz_history_steps=True,inactive_context_neutral=True,evidence='Actual methods with inert preallocated graphics resources; no GPU')

def flow_checks():
    import math
    def extract(path):
        tree=ast.parse(path.read_text(encoding='utf8'))
        fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='render')
        a=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='movement')
        b=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='visual_time')
        return compile(ast.Module(body=fn.body[a:b+1],type_ignores=[]),'actual-flow-clock','exec')
    before=extract(ROOT/'work/planet-audio-coverage-01/baseline/app/visuals/renderer.py');after=extract(ROOT/'app/visuals/renderer.py')
    def run(code,movement,flux,bass,impact,delta,tuning=None,active=True):
        r=SimpleNamespace(parameters=SimpleNamespace(movement=movement,flux=flux,scale=bass),impact_envelope=impact,
            FLOW_FLOOR=.35,FLOW_CEILING=1.15,FLOW_SMOOTHING_SECONDS=.6,flow_rate=.6,flow_time=12.,update_firescape_travel=lambda *a:None)
        inputs=dict(movement=movement,flux=flux,bass=bass,impact=impact,raw_impact=impact,sparkle=0.)
        if tuning is not None:tuning.resolve(active,inputs=inputs)
        exec(code,dict(self=r,delta_time=delta,math=math,planet_tuning=tuning,planet_active=active,flow_local=inputs,studio_audio=None,rewound=False))
        return r.flow_rate,r.flow_time
    cases=0
    for movement in (0.,.2,.7,1.):
        for flux in (0.,.3,1.):
            for bass in (0.,.5,1.):
                for impact in (0.,.7,1.,1.2):
                    for delta in (0.,.016,.2):
                        args=(movement,flux,bass,impact,delta)
                        assert run(before,*args)==run(after,*args,tuning=PlanetAudioTuning());cases+=1
    for key in ('movement_clock','audio_clock','impact_clock'):
        tuning=PlanetAudioTuning();c=dict(baseline('planet.surface_response'),**{key:0.})
        tuning.submit('planet.surface_response',1,c);tuning.resolve(True)
        args=(.6,.6,.6,.6,.1)
        assert run(after,*args,tuning=tuning)[0]<run(before,*args)[0]
        assert run(after,*args,tuning=tuning,active=False)==run(before,*args)
        assert run(after,*args,tuning=tuning)[1]>12.
    return dict(exact_legacy_cases=cases,three_named_contributions=True,integrated_positive_clock=True,inactive_context_exact=True,
        original_speed_floor_ceiling_and_easing=True,evidence='Actual AST-isolated flow clock vs own pre-task baseline, numeric inputs; no GPU/motion pixels')

def view_checks(folder,native=False):
    if native:
        import tkinter as tk
        root=tk.Tk();root.withdraw();real=tk.Toplevel
        class HiddenClient(tk.Frame):
            """Native pack/place at fixed client dimensions; WM remains withdrawn."""
            def __init__(self,*a,**kw):
                self.host=real(*a,**kw);self.host.withdraw()
                super().__init__(self.host)
            def title(self,text):self.host.title(text)
            def geometry(self,size):
                width,height=map(int,size.split('x'));self.place(x=0,y=0,width=width,height=height)
            def protocol(self,*a):self.host.protocol(*a)
            def state(self):return self.host.state()
        def hidden(*a,**kw):return HiddenClient(*a,**kw)
        factory=patch('tkinter.Toplevel',side_effect=hidden);factory.start()
    else:saved=install_widgets();root=Widget()
    try:
        star=StarProfileStore(folder/'star-missing.json',folder/'profiles')
        from artifacts_audio_tuning import BASELINE as ART_BASE
        artifact=TargetProfileStore(ART_TARGET,folder/'artifact-missing.json',folder/'profiles')
        backend=PlanetAudioTuning();submitted=[]
        def submit(c,a=None,target=TARGET):
            submitted.append((target,c,a));revision=len(submitted)
            if target in SPECS:backend.submit(target,revision,c,a);backend.resolve(True)
            return revision
        v=StarfieldTuningWindow(root,submit,lambda on:None,store=star,artifact_store=artifact)
        for target in SPECS:v.stores[target]=TargetProfileStore(target,folder/(target+'ui.json'),folder/'profiles')
        full=dict(version=1,pilot_active=True,presentation_active=True,rendered_wall=time.perf_counter(),
            settings=dict(SHIPPED,enabled=False),effective=SHIPPED,authored=SHIPPED,revision=0,analysis_age_seconds=0.,
            planet_tuning=backend.status(True,dict(bass=.2,flux=.3,sparkle=.4,impact=.5,raw_impact=.6),2))
        from artifacts_audio_tuning import ArtifactsAudioTuning,BOUNDS as ART_BOUNDS
        full['artifact_tuning']=ArtifactsAudioTuning().status(True,(.2,.3,.4),0.,True,bass=.2)
        layouts=[]
        for target in TARGETS:
            full['artifact_tuning']['rendered_wall']=time.perf_counter()
            v.target_var.set(target.label);v.select_target();v.refresh((full,time.perf_counter()),True)
            expected=STAR_BOUNDS if target.target_id==TARGET else ART_BOUNDS if target.target_id==ART_TARGET else bounds(target.target_id)
            assert list(v.vars)==list(expected) and len(v.sliders)==max(len(STAR_BOUNDS),len(ART_BOUNDS),*(len(bounds(t)) for t in SPECS))
            if target.target_id in SPECS:
                key=next(iter(expected));v.vars[key].set(1.25);v.changed(key);v.send()
                full['planet_tuning']=backend.status(True,dict(bass=.2,flux=.3,sparkle=.4,impact=.5,raw_impact=.6),2)
                v.refresh((full,time.perf_counter()),True);assert v.vars[key].get()==1.25
                assert v.target_packet()['revision']==v.revision
                # Reset applies target authored neutral while sibling settings survive.
                prior=deepcopy(backend.state);v.reset();v.send()
                assert backend.gains(target.target_id)==tuple(1. for r in SPECS[target.target_id])
                assert all(backend.state[k]==p for k,p in prior.items() if k!=target.target_id)
            if native:
                v.window.update_idletasks()
                assert v.window.state()=='withdrawn'
                for i in range(len(expected)):
                    v.focus_changed(i);v.window.update_idletasks()
                    y=v.sliders[i].winfo_rooty()-v.viewport.winfo_rooty();h=v.viewport.winfo_height()
                    layouts.append(dict(target=target.target_id,control=list(expected)[i],y=y,height=h,scale_height=v.sliders[i].winfo_height()))
                    assert 0<=y and y+v.sliders[i].winfo_height()<=h,(target.target_id,i,y,h)
        v.target_var.set(TARGETS[0].label);v.select_target()
        assert list(v.vars)[:4]==['start_hz','end_hz','weight','sensitivity']
        from band_attack_tuning import BASELINE as LEGACY
        # A representable legacy curve upgrades without changing its window.
        v.display_settings(LEGACY);v.vars['chorus_light'].set(1.25);v.changed('chorus_light')
        c=v.settings();assert c['mode']=='window' and c['start_hz']==20. and c['end_hz']==250. and c['weight']==1. and c['chorus_light']==1.25
        if v.pending is not None:v.window.after_cancel(v.pending);v.pending=None
        v.revision=None;v.last_applied_revision=None;v.refresh((full,time.perf_counter()),True)
        full.update(pilot_active=False,rendered_wall=time.perf_counter());v.refresh((full,time.perf_counter()),True)
        assert all(v.sliders[i].instate(['disabled']) for i in range(4))
        assert all(not v.sliders[i].instate(['disabled']) for i in range(4,10))
        full.update(pilot_active=True,rendered_wall=time.perf_counter());v.refresh((full,time.perf_counter()),True)
        assert v.sliders[7].instate(['disabled']) # Legacy wakes inactive with attack-flight pilot.
        if native:
            full['rendered_wall']=time.perf_counter();full['analysis_age_seconds']=0.;v.refresh((full,time.perf_counter()),True)
            # Actual native virtual dispatch on all original rows; no foreground/focus_force.
            taps=[]
            for i,key in enumerate(list(STAR_BOUNDS)[:4]):
                v.vars[key].set(100. if key.endswith('_hz') else 1.)
                v.focus_changed(i);before=v.vars[key].get()
                v.sliders[i].event_generate('<<NextChar>>');v.window.update_idletasks();v.keyboard.release('Right')
                step=1. if key.endswith('_hz') else .01
                assert v.vars[key].get()==before+step
                taps.append(dict(control=key,before=before,after=v.vars[key].get(),step=step))
            geometry=dict(width=v.window.winfo_width(),height=v.window.winfo_height(),state=v.window.state())
            assert geometry['width']==900 and geometry['height']==860
        else:taps=[];geometry=None
        v.close()
        return dict(single_window24_targets=True,actual_ACK_callbacks=True,reset_target_isolation=True,
            original_four_star_controls_retained=True,native_hidden=native,geometry=geometry,reachable_native_rows=layouts,native_virtual_taps=taps,
            limitations='Hidden native pack/place geometry at exact 900x860 client dimensions; WM withdrawn. No foreground focus, hardware input, screenshot or AV.')
    finally:
        if native:factory.stop();root.destroy()
        else:restore_widgets(saved)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--native-hidden',action='store_true');p.add_argument('--owner',action='store_true');a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='zerawave-planet-coverage-') as tmp:
        folder=Path(tmp)
        result=dict(evidence_class='CPU source/numerical/transport/persistence and inert UI; optional hidden native Tk; no GPU/capture/device',
            shader=shader_checks(),model=model_checks(folder),stages=stage_checks(),flow=flow_checks(),view=view_checks(folder,a.native_hidden))
    if a.owner:
        from starfield_tuning_test import live_owner_checks
        sequence=[(target,dict(baseline(target),**{SPECS[target][0]['key']:1.25})) for target in SPECS]
        result['actual_live_owner']=live_owner_checks(star_enabled=False,planet_sequence=sequence)
        result['star_presentation_owner']=live_owner_checks(star_enabled=False,star_presentation_sequence=[dict(SHIPPED,legacy_wake=0.,chorus_light=1.5),dict(SHIPPED,flux_clock=.5,sparkle_clock=0.)])
    if a.output:a.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2));print('Planet audio coverage CPU checks PASS')
if __name__=='__main__':main()
