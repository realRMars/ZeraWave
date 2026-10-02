"""Standalone checks of named relationships, saved controls and return budgets."""
import math,json,random
from pathlib import Path
from transition_catalog import RECIPES,SCENES,compatible,select_recipe,validate_settings,reprise_budgets,recipe_uniforms
from preview_layers import EFFECTS,BITS,TRANSITION_IDS,profile_at,layers_at,material_weights,default_profile,validate_layers
from renderer import Renderer,LIVE_FORMS
from studio import WORLD_TREE,DEFAULTS,command,validate_session,selection_states,effect_section

def run():
    assert set(SCENES)==set(LIVE_FORMS)
    assert 'transition' not in WORLD_TREE
    assert selection_states(['experimental','transition_study'])==['transition']
    for version in (1,2,3):
        saved=dict(DEFAULTS,version=version,state='transition',selection=['transition'])
        assert validate_session(saved)['selection']==['experimental','transition_study']
    for key in TRANSITION_IDS:
        assert BITS[key]==0 and effect_section(key)=='Transitions'
    base=default_profile('blend');mixed=dict(base,items=base['items']+[dict(id='tr_river',enabled=True),dict(id='tr_mist',enabled=True)])
    for seconds in (0.,6.,22.,43.,84.):
        assert layers_at({'blend':base},0,seconds)==layers_at({'blend':mixed},0,seconds)
        assert material_weights({'blend':base},0,seconds)==material_weights({'blend':mixed},0,seconds)
    assert profile_at({'earth':dict(mode='cycle',seconds=5.,items=[dict(id='tr_facet',enabled=True)])},26)==default_profile('earth')
    selected=dict(mode='cycle',seconds=12.,items=[dict(id=k,enabled=True) for k in ('tr_aperture','tr_mist','tr_facet','tr_river')])
    assert [select_recipe(random.Random(1),26,22,selected,index=i)[2] for i in range(4)]==['tr_aperture','tr_facet','tr_river','tr_aperture']
    assert compatible('tr_planet',11,5) and not compatible('tr_planet',26,5)
    from renderer import world_family
    layout=(.7,.11,-.04,.37)
    fade=recipe_uniforms('tr_fade',.5,11,5,layout,world_family)
    planet=recipe_uniforms('tr_planet',.5,11,5,layout,world_family)
    native=recipe_uniforms('tr_plasma',.5,32,34,layout,world_family)
    assert fade!=planet and fade['u_main_transition']==(-1.,.5,11.,5.)
    assert planet=={'u_handoff':(0.,.5,world_family(11),world_family(5)),'u_world_warp':0.}
    assert native=={'u_handoff':(0.,.5,world_family(32),world_family(34)),'u_world_warp':0.}
    for recipe,pair in (('tr_fade',[11,5]),('tr_planet',[11,5]),('tr_plasma',[32,34])):
        cfg=validate_settings(json.loads(json.dumps(dict(pair=pair,isolate={'pair':recipe},hold=4.,duration=6.))))
        restored=validate_session(dict(DEFAULTS,version=3,selection=[],source='Synthetic preview',transitions=cfg))
        assert restored['transitions']==cfg
        renderer=Renderer(seed=42);renderer.configure_transitions(restored['transitions']);renderer.update_blend(7.,.1)
        for uniform,value in recipe_uniforms(recipe,.5,*pair,renderer.blend_values.get('u_main_layout',layout),world_family).items():
            if uniform!='u_main_layout':assert renderer.blend_values[uniform]==value

    assert compatible('tr_mist',26,29) and not compatible('tr_mist',22,29)
    assert compatible('tr_induction',22,32) and not compatible('tr_induction',22,38)
    observed=set()
    for source in SCENES:
        for target in SCENES:
            if source==target:continue
            for i in range(30):
                style,layout,key=select_recipe(random.Random(i),source,target)
                assert compatible(key,source,target) and all(math.isfinite(x) for x in layout)
                observed.add(key)
    assert observed==set(RECIPES)-{'tr_material','tr_study'}
    cfg=dict(pair=[26,22],isolate={'blend':'tr_facet'},hold=4.,duration=3.)
    saved=dict(DEFAULTS,version=3,selection=[],source='Synthetic preview',transitions=cfg,layers={'blend':mixed})
    restored=validate_session(saved);assert restored['transitions']==cfg
    args=command(restored,Path('unused-review-check'));assert '--transitions' in args and '--states' in args
    for module in ('live_visual_test','shader_test','replay_test'):
        import importlib,inspect
        entry=getattr(importlib.import_module(module),'replay' if module=='replay_test' else 'main')
        assert 'transitions' in inspect.signature(entry).parameters
    r=Renderer(seed=42);r.configure_transitions(cfg)
    assert r.state_at(3.9)==26 and r.state_at(4.1)==0 and r.state_at(7.)==22
    r.update_blend(5.5,.1);assert r.blend_values['u_main_transition']==(2.,.5,26.,22.)
    r.update_blend(12.5,.1);assert r.blend_values['u_main_transition']==(2.,.5,22.,26.)
    legacy=Renderer(seed=42);legacy.debug_state=35;legacy.configure_transitions();assert not legacy.transition_sequence and legacy.state_at(900)==35
    native=Renderer(seed=42);native.debug_state=35;native.layer_profiles={'plasma':dict(mode='cycle',seconds=12.,items=[dict(id='tr_facet',enabled=True)])};native.configure_transitions();assert native.debug_sequence==(32,33,34)
    isolated=Renderer(seed=42);isolated.debug_state=35;isolated.configure_transitions(dict(isolate={'plasma':'tr_facet'}));assert isolated.debug_sequence==(32,33,34) and isolated.transition_sequence
    from color_controls import targets_for
    exp={t.id for t in targets_for('experimental')};main={t.id for t in targets_for('blend')}
    assert {'magnetic.bloom','arcs.asterism','auroral.veil'}<=exp and not {'magnetic.bloom','arcs.asterism','auroral.veil'}&main
    from studio import color_scope_for_states
    assert color_scope_for_states(['lodestone_experimental','stormglass_experimental','folded_aurora_experimental','transition'])=='experimental'
    # Controlled genuine A->B->A director selection, not a shader callback.
    r=Renderer(seed=20);visits=iter((26,22,26,7));r.choose_world=lambda *args:next(visits)
    r.update_blend(0,0);r.director_min_hold=0;r.director_max_hold=0;r.update_blend(1,1)
    r.update_blend(12,11);first=(r.director_min_hold,r.director_max_hold);assert not r.director_reprise
    r.director_min_hold=0;r.director_max_hold=0;r.update_blend(13,1);assert r.director_target==26 and r.director_reprise
    r.update_blend(24,11);second=(r.director_min_hold,r.director_max_hold)
    assert 6.24<=second[0]<=9.88 and 16<=second[1]<=24 and r.director_history[-1]['reprise']
    r.update_blend(50,26);assert r.director_target==7
    for bad in (dict(pair=[26,26]),dict(pair=[38,22]),dict(hold=float('nan')),dict(duration=0)):
        try:validate_settings(bad)
        except ValueError:pass
        else:raise AssertionError(bad)
    try:select_recipe(random.Random(1),26,22,isolate='tr_mist')
    except ValueError:pass
    else:raise AssertionError('Incompatible isolation accepted')
    # New river development grows only during the correctly routed present state.
    from molten_response import MoltenMemory
    m=MoltenMemory();assert m.development==0
    for i in range(40):m.advance(i,1.,.5,.4,.3,.2,0.,True)
    assert 0<m.development<=1
    grown=m.development
    m.advance(42,2.,0.,0.,0.,0.,0.,False);assert m.development==grown
    m.advance(0,0.,0.,0.,0.,0.,0.,True);assert m.development==0
    result=dict(transition_recipes=len(RECIPES),eligible_observed=sorted(observed),session_versions=[1,2,3],visual_fx_order_preserved=True,pair_and_native_routes=True,actual_reprise_first=first,actual_reprise_short=second,onward_state=7,limits='Numeric/configuration checks; not GPU, rendered soak or continuous listening.')
    print('PASS',json.dumps(result));return result
if __name__=='__main__':run()
