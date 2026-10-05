"""Main promotion migration, real target profiles and scoped pigment isolation."""
import hashlib,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
import numpy as np
from studio import DEFAULTS,validate_session
from renderer import LIVE_FORMS
from transition_catalog import compatible
from preview_layers import EFFECTS,FRACTAL_WORLDS,validate_layers
from color_controls import TARGETS,color_uniforms,targets_for,STATE_COLOR_SCENE
from audio_controls import TARGETS as AUDIO,defaults,form_targets,slots
from audio_scope import Scope,SaveTicket
from star_tuning_profiles import TargetProfileStore

def run():
    authored={p:p.read_bytes() for p in (ROOT/'app').rglob('*.json')}
    assert len(LIVE_FORMS)==30 and not {37,38,39,40}&set(LIVE_FORMS)
    for form in (0,)+LIVE_FORMS:slots(form)
    for recipe,start in (('tr_branch_iris',80),('tr_flow_fold',84)):
        target='transition.'+recipe;roles=AUDIO[target]['roles']
        assert {r['source'] for r in roles}=={'timer','bass','flux','movement','impact'}
        assert [r['slot'] for r in roles if r['source']!='timer']==list(range(start,start+4))
        assert sum(compatible(recipe,a,b) for a in LIVE_FORMS for b in LIVE_FORMS)==870
        assert all(world in EFFECTS[recipe][2] for world in FRACTAL_WORLDS)
    migrated=[]
    for form,leaf,world,target,role in ((41,'landscape','fractal_landscape','fractal.landscape.terrain','body'),(42,'atrium','fractal_atrium','fractal.atrium.stone','body'),(43,'bloom','fractal_bloom','fractal.bloom.honey','wax')):
        assert len(form_targets(form))==3
        layers=validate_layers({world:dict(mode='cycle',seconds=12.,items=[dict(id='mineral_lamellae',enabled=True,amount=.7),dict(id='tr_branch_iris',enabled=True)])})
        colors={target:{role:dict(color='#35AB87')}}
        session=dict(version=3,**dict(DEFAULTS,selection=['fractals',leaf],selection_scope='experimental',studio_selections=dict(main=['cosmic','canvas'],experimental=['fractals',leaf]),layers=layers,color_overrides=colors,transitions=dict(isolate={world:'tr_branch_iris'})))
        clean=validate_session(session)
        assert clean['selection_scope']=='main' and clean['selection']==['fractals',leaf]
        assert clean['studio_selections']['main']==['fractals',leaf] and clean['studio_selections']['experimental']==['cymatics','water']
        assert clean['layers']==layers and clean['color_overrides']==colors
        assert validate_session(dict(version=3,**clean))==clean
        ids=[t.id for t in targets_for(STATE_COLOR_SCENE[form])]
        all_values=color_uniforms(colors,ids,31.)
        scoped=color_uniforms(colors,ids,31.,only=ids)
        assert scoped and all(value==all_values[key] for key,value in scoped.items())
        main_uniform=next(t.uniform for t in TARGETS if t.id=='roots.ridge')
        assert main_uniform not in scoped and main_uniform+'_on' not in scoped
        migrated.append(form)
    frequencies=np.arange(1025)*48000/2048
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
        folder=Path(folder);paths=[]
        for target in ('transition.tr_branch_iris','transition.tr_flow_fold','fractal.41.landscape','fractal.42.recursion','fractal.43.growth'):
            store=TargetProfileStore(target,authored_path=folder/(target+'.json'),profile_dir=folder/'profiles')
            c=dict(defaults(target),enabled=True,bass_response=.65,bass_range_enabled=True,bass_start_hz=80.,bass_end_hz=300.)
            path=store.save_profile('Same artistic name',c,frequencies);paths.append(path)
            assert store.load_profile(path,frequencies)==('Same artistic name',c)
            store.save_authored(c,frequencies);assert store.reload_authored()==c
            scope=Scope('run','session',AUDIO[target]['form'],target,1)
            ticket=SaveTicket.acknowledged(scope,c,dict(scope=scope.packet(),effective=c),1.,clock=lambda:1.1)
            ticket.verify(scope,c)
            try:ticket.verify(Scope('run','session',scope.form,target,2),c)
            except ValueError:pass
            else:raise AssertionError('Stale save accepted')
        assert len(set(paths))==5
    assert all(p.read_bytes()==b for p,b in authored.items())
    print('PASS Main30/Fractal migration, exact scoped pigments, 870 pairs each, all-form slots, new controls, independent profile/authored roundtrip and stale-save rejection; CPU, no GPU/foreground/listening')
if __name__=='__main__':run()
