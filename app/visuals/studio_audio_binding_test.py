"""Current consumer-slot/source and bounded active-FFT CPU cost checks."""
import ast,json,math,re,sys,time
from types import SimpleNamespace
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from audio_controls import TARGETS,WORLD_GROUPS,CPU_GROUPS,SOURCE_UNIFORMS,slots,defaults,windows,SHARED_OFFSETS
from form_audio_tuning import FormAudioTuning
from audio_scope import Scope

def body(shader,name):
    # Wrapped consumers establish/save their original endpoint context.
    actual='audio_owned_'+name if 'audio_owned_'+name+'(' in shader else name
    match=re.search(r'\b'+actual+r'\([^;{}]*\)\s*\{',shader);assert match,name
    start=match.end();depth=1;end=start
    while depth:
        depth+=(shader[end]=='{')-(shader[end]=='}');end+=1
    return shader[start:end-1]

def bindings():
    shader=(ROOT/'app/visuals/shaders/dream.frag').read_text(encoding='utf8')
    renderer=(ROOT/'app/visuals/renderer.py').read_text(encoding='utf8')
    checked=[]
    for form,groups in WORLD_GROUPS.items():
        for group,(slug,label,sources,functions) in enumerate(groups):
            target='form.'+str(form)+'.'+slug
            for source in sources:
                slot=slots(form)[(target,source+'_response')];uniform=SOURCE_UNIFORMS[source]
                consumers=[]
                for name in functions:
                    code=body(shader,name)
                    dynamic={19:'audio_context',20:'audio_context',21:'audio_context',22:'audio_context',24:'24+form',25:'24+form',26:'24+form',28:'28+form',29:'28+form',30:'28+form',32:'32+form',33:'32+form',34:'32+form'}.get(form)
                    direct=any('form_audio('+uniform+','+owner+','+str(slot)+')' in code for owner in (str(form),dynamic,'audio_context') if owner)
                    water_group=1 if slug=='light' else group
                    water='water_audio('+uniform+','+str(water_group)+','+str(list(SOURCE_UNIFORMS).index(source))+')' in code and form in (7,8,9,10,13)
                    if direct or water:consumers.append(name)
                assert consumers,(target,source,slot)
                checked.append(dict(target=target,source=source,slot=slot,functions=consumers))
    for form,(slug,label,sources,code) in CPU_GROUPS.items():
        for source in sources:
            assert "self.audio_input("+str(form)+",'"+slug+"','"+source+"'" in renderer,(form,source)
    # Copied shared metadata must land on the exact existing technique offsets.
    for target,p in TARGETS.items():
        if p.get('shared'):
            for i,role in enumerate(p['roles']):assert role['slot']==SHARED_OFFSETS[p['shared']]+i
    assert "audio_input(26,'camera','flux'" in (ROOT/'app/visuals/scene_surfaces.py').read_text(encoding='utf8')
    assert 'form.26.cavern' not in TARGETS and 'form.25.strata' in TARGETS
    return dict(named_shader_sources=len(checked),actual_CPU_groups=len(CPU_GROUPS),independent_shared_slots=True,cached_surface_bank_matches_shader=True,unused_Cavern_bend_not_exposed=True,bindings=checked)

def cost():
    model=FormAudioTuning('run','session');inputs=dict(bass=.3,movement=.4,flux=.2,sparkle=.1,impact=.2,raw_impact=.2)
    f=np.arange(1025)*48000/2048.;m=np.random.default_rng(19).uniform(0.,.1,1025)
    model.resolve([12,11],inputs);model.process(f,m,2048,'fixture')
    results=[]
    for mode in ('OFF','one_window','all_active_windows'):
        if mode!='OFF':
            for target,p in TARGETS.items():
                if p['form'] not in (12,11) or (mode=='one_window' and target!='roots.growth'):continue
                c=defaults(target)
                for name in windows(target):c[name+'_range_enabled']=True
                model.submit(dict(scope=Scope('run','session',p['form'],target,1 if mode=='one_window' else 2).packet(),settings=c))
            model.resolve([12,11],inputs)
        samples=[]
        for _ in range(40):
            start=time.perf_counter();payload=model.process(f,m,2048,'fixture');model.observe(payload);model.resolve([12,11],inputs,2048/48000.,False,0)
            samples.append((time.perf_counter()-start)*1000.)
        results.append(dict(mode=mode,p50_ms=float(np.median(samples)),p95_ms=float(np.percentile(samples,95)),enabled_target_processors=len(model.processors),active_forms=2,samples=len(samples)))
    model.resolve([2],inputs);model.process(f,m,2048,'fixture');assert not model.processors
    return dict(conditions='2048-bin 48kHz existing-FFT arrays; two contributing forms; process+observe+resolve; CPU only, excludes FFT/capture/render/Tk/IPC',measurements=results,exit_releases_processors=True)

def clocks():
    from planet_audio_tuning import PlanetAudioTuning,baseline
    tree=ast.parse((ROOT/'app/visuals/renderer.py').read_text(encoding='utf8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='render')
    start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='movement')
    end=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.AugAssign) and ast.unparse(n.target)=='self.star_time')
    code=compile(ast.Module(body=fn.body[start:end+1],type_ignores=[]),'actual-normal-clock-routing','exec')
    outputs=[]
    for gain in (1.,.15):
        tuning=PlanetAudioTuning();c=dict(baseline('planet.surface_response'),movement_clock=gain,audio_clock=gain,impact_clock=gain)
        tuning.submit('planet.surface_response',1,c)
        r=SimpleNamespace(parameters=SimpleNamespace(movement=.65,flux=.9,scale=.7,sparkle=.9),impact_envelope=.6,
            FLOW_FLOOR=.35,FLOW_CEILING=1.15,FLOW_SMOOTHING_SECONDS=.6,flow_rate=.6,flow_time=12.,star_rate=1.1,star_time=8.25,blend_values={},state_at=lambda t:12,update_firescape_travel=lambda *a:None)
        inputs=dict(movement=.65,flux=.9,bass=.7,sparkle=.9,impact=.6,raw_impact=.6)
        for i in range(30):
            tuning.resolve(True,inputs=inputs)
            exec(code,dict(self=r,current_time=i/60.,delta_time=1/60.,math=math,planet_tuning=tuning,planet_active=True,flow_local=inputs,star_local=inputs,clock_flux_gain=gain,clock_sparkle_gain=gain,studio_audio=object(),rewound=False))
        outputs.append((r.flow_rate,r.flow_time,r.star_rate,r.star_time,r._planet_flow_time,r._planet_star_time))
    assert outputs[0][:4]==outputs[1][:4]
    assert outputs[0][4]>outputs[1][4] and outputs[0][5]>outputs[1][5]
    return dict(actual_render_clock_blocks=True,Planet_changes_do_not_change_shared_Root_clocks=True,Planet_owned_clocks_respond=True,steps=30)

def run():return dict(evidence='Current GLSL source binding + actual clock blocks + CPU numerical cost; no GLSL compilation/GPU/pixels',bindings=bindings(),clocks=clocks(),cost=cost())
if __name__=='__main__':
    result=run();print(json.dumps(result,indent=2));print('Studio Audio consumer binding CPU checks PASS')
