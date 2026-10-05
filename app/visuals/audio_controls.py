"""Authored form/target/role contracts for normal Studio audio tuning.

Each declaration names an actual consumer. Defaults are neutral multipliers;
saved Planet numbers are never used to author another form's controls.
"""
from pathlib import Path
import math
from spectral_listening import listening_defaults,listening_bounds,validate_listening
from planet_listening import names_for_roles,titles as window_titles,INGREDIENTS
from transition_catalog import SCENES,RECIPES
from development_forms import INSPECTION_FORMS,FRACTAL_FORMS

def validate_target(form,target,settings):
    if form==5:
        from star_tuning_profiles import TARGET
        from artifacts_audio_tuning import TARGET as ART,validate as artifact_validate
        from planet_audio_tuning import SPECS,validate as planet_validate
        if target==TARGET:
            from band_attack_tuning import validate as star_validate
            return star_validate(settings)
        if target==ART:return artifact_validate(settings)
        if target in SPECS:return planet_validate(target,settings)
    return validate(form,target,settings)

def form_targets(form):
    if form==5:
        from star_tuning_profiles import TARGET
        from artifacts_audio_tuning import TARGET as ART
        from planet_audio_tuning import SPECS
        return (TARGET,ART)+tuple(SPECS)
    keys=targets(form)
    return tuple(t for t in keys if 'shared' not in TARGETS[t] and '.material.artifacts' not in t)+tuple(t for t in keys if 'shared' in TARGETS[t] or '.material.artifacts' in t)

def role(key,label,source,code,scope,high=2.,curve=None):
    return dict(key=key,label=label,source=source,code=code,scope=scope,bounds=(0.,high),default=1.,curve=curve)

# First contrasting form: actual Root network, ridge accents and blossom light.
# These are independently authored contracts, not Planet profile copies.
TARGETS={
 'roots.growth':dict(form=12,label='Root growth',scope='Connected Root branches; lifecycle remains time-driven.',roles=[
    role('flux_branch','Flux -> branch flex','flux','dream.frag::root_network(activity), scene_frame root_distance','Root branch bend after smoothstep(.08,.65); fixed resting bend retained.',curve=(.08,.65))]),
 'roots.ridge':dict(form=12,label='Root ridge light',scope='Root share of the Organic ridge; pigments and base ridge remain.',roles=[
    role('sparkle_ridge','Sparkle -> ridge light','sparkle','dream.frag::scene_frame membrane_color ridge accents','Root share of .35 high-frequency ridge increment.'),
    role('impact_ridge','Impact -> ridge event light','impact','dream.frag::scene_frame membrane_color ridge accents','Root share of .15 impact increment, including manual Root ridge pigment.')]),
 'roots.blossoms':dict(form=12,label='Root blossoms',scope='Blossom detail requires enabled Root blossoms; bud/bloom lifecycle is a pure timer.',roles=[
    role('sparkle_blossom','Sparkle -> blossom light','sparkle','dream.frag::scene_frame blossom','Blossom .35 sparkle contribution; .35 quiet base retained.'),
    role('impact_blossom','Impact -> blossom event light','impact','dream.frag::scene_frame blossom','Blossom .30 impact contribution; lifecycle and petal shape retained.')]),
}

def targets(form):return tuple(key for key,value in TARGETS.items() if value['form']==form)
def windows(target):return names_for_roles([r for r in TARGETS[target]['roles'] if r['source'] in INGREDIENTS])
def defaults(target):return dict(enabled=True,**{r['key']:r['default'] for r in TARGETS[target]['roles']},**listening_defaults(windows(target)))
def bounds(target):return dict({r['key']:r['bounds'] for r in TARGETS[target]['roles']},**listening_bounds(windows(target)))
def titles(target):return dict({r['key']:r['label'] for r in TARGETS[target]['roles']},**window_titles(windows(target)))
def authored_path(target):return Path(__file__).with_name('audio_form_'+str(TARGETS[target]['form'])+'_'+target.replace('.','_')+'_authored.json')
def validate(form,target,settings):
    if target not in TARGETS or TARGETS[target]['form']!=form or form not in (*INSPECTION_FORMS,0):raise ValueError('Unknown form audio target')
    if not isinstance(settings,dict) or set(settings)!=set(defaults(target)):raise ValueError('Unknown form audio fields')
    if type(settings['enabled']) is not bool:raise ValueError('Invalid live override flag')
    validate_listening(settings,windows(target));clean=dict(settings)
    for key,(low,high) in bounds(target).items():
        value=settings[key]
        if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:raise ValueError('Invalid '+key)
        clean[key]=float(value)
    return clean

def slots(form):
    result={};index=0
    for target in targets(form):
        for r in TARGETS[target]['roles']:result[(target,r['key'])]=index;index+=1
    result={key:TARGETS[key[0]]['roles'][next(i for i,r in enumerate(TARGETS[key[0]]['roles']) if r['key']==key[1])].get('slot',value) for key,value in result.items()}
    if len(set(result.values()))!=len(result) or any(not 0<=i<128 for i in result.values()):raise ValueError('Form exceeds or collides with bounded audio uniform capacity')
    return result

# A shared technique has one authored namespace per form. These declarations
# reuse the working technique's role definition, never a saved Planet profile.
# Slot numbers are an explicit shader/CPU interface, independent of UI ordering.
from planet_audio_tuning import SPECS as SHARED_SPECS
SHARED_OFFSETS={};_slot=0
for _planet,_roles in list(SHARED_SPECS.items())[:18]:
    SHARED_OFFSETS[_planet]=_slot;_slot+=len(_roles)
for _form,_name in SCENES.items():
    if _form==5 or _form in FRACTAL_FORMS:continue
    for _planet,_roles in list(SHARED_SPECS.items())[:18]:
        _suffix=_planet.removeprefix('planet.');_key='form.'+str(_form)+'.'+_suffix
        _items=[]
        for _i,_r in enumerate(_roles):
            _item=role(_r['key'],_r['label'],_r['source'],
                'dream.frag::planet_audio shared '+_suffix if '.enveloper.' not in _planet and '.echo_weave' not in _planet else 'renderer.py::update_echo / EnveloperStage.draw '+_suffix,
                'Shared technique contribution on this form; actual selection, mask and playback mode govern availability.',high=_r['bounds'][1])
            _item.update(slot=SHARED_OFFSETS[_planet]+_i,modes=_r['modes']);_items.append(_item)
        TARGETS[_key]=dict(form=_form,label=_suffix.replace('.',' / ').replace('_',' ').title(),roles=_items,
            scope='Form-owned gains on the existing shared '+_suffix+'. Material coordinates depend on the shared source canvas; elapsed-time phase and manual selection stay separate.',
            shared=_planet,kind='CPU submission' if '.enveloper.' in _planet or '.echo_weave' in _planet else 'shader input',
            dependency=_suffix)
    _artifact_sources=('flux','impact','sparkle','bass','pressure','sparkle')
    _artifact_keys=('flux_stretch','impact_facets','sparkle_light','bass_cells','bass_radial','sparkle_presence')
    TARGETS['form.'+str(_form)+'.material.artifacts']=dict(form=_form,label='Living Artifacts',scope='Shared material; six existing local contributions, selection and cells remain authored.',dependency='material.artifacts',kind='shader input',roles=[
        dict(role(k,k.replace('_',' ').title(),source,'dream.frag::scene_frame Living Artifacts','Existing local Artifacts contribution.'),slot=50+i) for i,(k,source) in enumerate(zip(_artifact_keys,_artifact_sources))])

for _key,_p in tuple(TARGETS.items()):
    if _key.startswith('roots.'):
        for _r in _p['roles']:_r['slot']=64+list(('flux_branch','sparkle_ridge','impact_ridge','sparkle_blossom','impact_blossom')).index(_r['key'])

# Named authored consumer groups. A role controls all occurrences of its source
# within the named function; coupled contributions are explicitly one group.
SOURCE_UNIFORMS=dict(bass='u_scale',flux='u_flux',sparkle='u_sparkle',impact='u_impact')
WORLD_GROUPS={
 2:[('corridor','Corridor geometry and inlay',('flux','sparkle','impact'),('isolated_geometric_scene',))],
 7:[('surface','Shared water surface',('bass','flux','sparkle','impact'),('water_height','water_storm','water_current')),('light','Sea reflections',('sparkle',),('isolated_water_scene',))],
 8:[('surface','Shared water surface',('bass','flux','sparkle','impact'),('water_height','water_storm','water_current')),('light','Dye body and reflections',('bass','flux','sparkle'),('isolated_water_scene',))],
 9:[('surface','Shared water surface',('bass','flux','sparkle','impact'),('water_height','water_storm','water_current')),('light','Rain and reflected light',('sparkle',),('isolated_water_scene',))],
 10:[('surface','Shared water surface',('bass','flux','sparkle','impact'),('water_height','water_storm','water_current')),('falls','Falls fold and light',('bass','flux','sparkle'),('water_falls',))],
 13:[('surface','Shared water surface',('bass','flux','sparkle','impact'),('water_height','water_storm','water_current')),('current','Current shear and event warp',('bass','flux','impact'),('currents_domain',)),('light','Current reflections',('sparkle',),('isolated_water_scene',))],
 14:[('flame','Flame surge, heat and light',('bass','flux','sparkle','impact'),('isolated_fire_scene',))],
 15:[('river','Molten river, glow and sparks',('bass','flux','sparkle','impact'),('isolated_molten_scene','molten_ground'))],
 17:[('fire','Firescape flames, coals and ash',('bass','flux','sparkle','impact'),('isolated_firescape_scene',))],
 18:[('rings','Blast ring tongues',('flux',),('blast_ring',))],
}
for _form in (19,20,21,22):
    WORLD_GROUPS[_form]=[('air','Sky, cloud and local event response',('bass','flux','sparkle','impact'),('air_scene',))]
WORLD_GROUPS[22].append(('lanterns','Citadel lantern light',('bass','flux','sparkle'),('air_citadel',)))
for _form in (24,25,26):
    WORLD_GROUPS[_form]=[('land','Land shading and minerals',('bass','flux','sparkle','impact'),('earth_scene',)),('camera','Surface bank',('flux',),('earth_surface',))]
WORLD_GROUPS[24].append(('dunes','Dune bend',('bass',),('earth_dune',)))
WORLD_GROUPS[25].append(('strata','Strata cliff bend',('bass',),('earth_map',)))
# Cavern's normal cached mesh has no live Bass bend input. The dormant legacy
# earth_map fallback is deliberately not exposed as a working Main control.
for _form in (28,29,30):
    WORLD_GROUPS[_form]=[('vapor','Vapor motion and internal light',('bass','flux','sparkle','impact'),('fog_scene',)),('density','Vapor opening and pressure',('bass',) if _form!=30 else ('bass','impact'),('fog_density',))]
WORLD_GROUPS[29].append(('lamps','Uncached ghostlight response',('bass','sparkle','impact'),('fog_lamp_light',)))
for _form in (32,33,34):
    WORLD_GROUPS[_form]=[('field','Field body, filaments and event light',('bass','flux','sparkle','impact'),('plasma_scene',)),('stars','Plasma sky and wakes',('bass','flux','sparkle','impact'),('plasma_stars',))]
WORLD_GROUPS[32].append(('loops','Original loop shape',('bass','flux','impact'),('plasma_loop','magnetic_core_position')))
WORLD_GROUPS[33].append(('nodes','Arc node orbit width',('bass',),('plasma_node',)))
WORLD_GROUPS[36]=[
 ('stars','Cosmic stars, shoal and sails',('flux','sparkle','impact'),('cosmic_star_layer','parallax_shoal','stellar_sails')),
 ('journey','Galaxy clouds and arm depth',('bass','flux','sparkle'),('journey_galaxy','journey_arm_depth')),
 ('bodies','Planet pressure, surfaces and field waves',('bass','flux','sparkle','impact'),('journey_pressure','journey_surface','journey_system')),
 ('warp','Warp trail light',('impact',),('journey_warp',))]

for _form,_groups in WORLD_GROUPS.items():
    for _g,(_slug,_label,_sources,_functions) in enumerate(_groups):
        _key='form.'+str(_form)+'.'+_slug
        TARGETS[_key]=dict(form=_form,label=_label,functions=_functions,kind='shader input',
            scope='Existing '+_label.lower()+'. Each source controls its coupled uses within the named consumer; quiet bases, pigments, timers and masks remain.',
            dependency='Shared physical surface across contributing water forms.' if _slug=='surface' else 'Original function and its material/detail enable controls.',
            roles=[dict(role(source+'_response',source.title()+' -> '+_label.lower(),source,'dream.frag::'+' / '.join(_functions),'All named-function uses of this source; bounded normalized input.'),slot=64+4*_g+list(SOURCE_UNIFORMS).index(source)) for source in _sources])

TARGETS['form.11.membrane']=dict(form=11,label='Membrane flex and ridge',scope='Membrane share only; Root projection uses the unchanged shared domain.',dependency='Organic membrane share.',kind='shader input',roles=[
 dict(role('bass_tension','Bass -> surface tension','bass','dream.frag::scene_frame membrane_q','Local membrane frequency/tension.'),slot=64),
 dict(role('flux_flex','Flux -> local flex','flux','dream.frag::scene_frame membrane_activity','Local .16 flex amplitude.'),slot=65),
 dict(role('sparkle_ridge','Sparkle -> ridge light','sparkle','dream.frag::scene_frame membrane_color','Local .35 ridge-light contribution.'),slot=66),
 dict(role('impact_fold','Impact -> fold and ridge','impact','dream.frag::scene_frame membrane_event','Local phase .35 and ridge .15 contributions.'),slot=67)])

CPU_GROUPS={
 15:('memory','Current Memory',('bass','movement','sparkle','flux','raw_impact'),'MoltenMemory.advance'),
 29:('memory','Ghostlight Memory',('bass','movement','sparkle','flux','raw_impact'),'MarshResponse.advance'),
 22:('cadence','Tower Cadence',('bass','movement','sparkle','raw_impact'),'TowerCadence.advance'),
 26:('resonance','Mineral Resonance',('bass','movement','sparkle','raw_impact'),'MineralResponse.advance'),
 17:('travel','Firescape travel clock',('bass','movement','sparkle'),'Renderer.update_firescape_travel'),
 18:('births','Blast and shockwave qualification',('raw_impact',),'Renderer.update_blasts / update_shockwaves'),
 36:('events','Nursery qualification and release memory',('bass','flux','sparkle','raw_impact'),'Renderer.render stellar event and afterglow mapping')}
for _form,(_slug,_label,_sources,_code) in CPU_GROUPS.items():
    TARGETS['form.'+str(_form)+'.'+_slug]=dict(form=_form,label=_label,kind='CPU submission',dependency='Existing effect enable and form presence; bounded history resets on exit/seek.',
        scope='Existing CPU mapping inputs to '+_code+'. Internal thresholds, quiet bases, event limits, smoothing and timing stay authored; source gains are applied once before that mapping.',
        roles=[dict(role(source+'_response',source.replace('_',' ').title()+' -> '+_label,source,'renderer.py::'+_code,'Actual argument/input to existing CPU mapping.'),slot=96+i) for i,source in enumerate(_sources)])

def timer(key,label,default,bounds,slot,code):
    return dict(key=key,label=label,source='timer',default=default,bounds=bounds,slot=slot,code=code,scope='Timer/threshold configuration; not a detected musical feature.')

TARGETS['transition.director']=dict(form=0,label='Main opportunity and beat qualification',kind='CPU submission',dependency='Automatic Main director only; separate from visual warp and pair audition timers.',
    scope='Shared Main decision dependency. Bass/Movement/Flux feed the existing .7s/8s energy comparison; onset qualifies a strong-hit opportunity. Beat confidence/tick qualify an existing opportunity. Timer controls scale the existing authored hold budgets, without changing the queue or Galaxy full-route requirement.',roles=[
      dict(role('bass_response','Bass -> opportunity energy','bass','renderer.py::update_blend energy','Existing .45 Bass energy ingredient.'),slot=0),
      dict(role('movement_response','Movement -> opportunity energy','movement','renderer.py::update_blend energy','Existing .35 Movement energy ingredient.'),slot=1),
      dict(role('flux_response','Flux -> opportunity energy','flux','renderer.py::update_blend energy','Existing .20 Flux energy ingredient.'),slot=2),
      dict(role('raw_impact_response','Onset -> strong-hit qualification','raw_impact','renderer.py::update_blend impact','Existing fresh onset qualification, not a duration trigger.'),slot=3),
      timer('energy_difference','Lift / release energy difference',.12,(.04,.4),4,'renderer.py::update_blend lift/release'),
      timer('hit_threshold','Strong-hit threshold',.35,(.15,.8),5,'renderer.py::update_blend hit'),
      timer('beat_confidence','Beat qualification confidence',.65,(.5,1.),6,'renderer.py::update_blend beat confidence'),
      timer('beat_wait','Beat wait deadline (seconds)',.8,(.1,2.),7,'renderer.py::update_blend pending deadline'),
      timer('min_hold_scale','Minimum authored hold budget (x)',1.,(.5,2.),8,'renderer.py::update_blend age/minimum'),
      timer('max_hold_scale','Maximum authored hold budget (x)',1.,(.5,2.),9,'renderer.py::update_blend breathing interval')])
for _i,(_recipe,(_label,_,_pair)) in enumerate(RECIPES.items()):
    if _recipe in ('tr_material','tr_study'):continue
    TARGETS['transition.'+_recipe]=dict(form=0,label=_label,kind='CPU submission',dependency='Compatible scene pairs only. Duration is sampled/applied when a handoff begins; pair audition uses its separate hold/duration settings.',
        scope='Existing '+_label+' transition. Duration scale is a pure timer applied to the authored sampled Main duration at the next opportunity; endpoint form controls remain independent.',roles=[
        timer('duration_scale','Next Main handoff duration (x)',1.,(.25,2.),16+_i,'renderer.py::update_blend director_duration')])
TARGETS['transition.tr_warp']['roles'] += [
    dict(role('bass_response','Bass -> visual warp amplitude','bass','dream.frag::scene_frame warp','Existing Bass ingredient in bounded warp amplitude.'),slot=64),
    dict(role('flux_response','Flux -> visual warp amplitude','flux','dream.frag::scene_frame warp','Existing Flux ingredient in bounded warp amplitude.'),slot=65)]

for _key in ('tr_branch_iris','tr_flow_fold'):
    TARGETS['transition.'+_key].update(kind='CPU timer + shader inputs',
        dependency='Any two different canonical Main forms; visual response only while this recipe is active. Configure/save while inactive. Duration applies at the next automatic opportunity; audition has its own explicit timer.',
        scope='Independent recipe shape/deformation controls; endpoint shading/pigments/tuning remain independently owned.')
    TARGETS['transition.'+_key]['roles'] += [
        dict(role(source+'_response',label,source,'dream.frag::main_region/main_carry '+_key,
                  'Bounded structural '+label+' contribution; resting pattern and pure duration stay separate.'),slot=80+i+4*(_key=='tr_flow_fold'))
        for i,(source,label) in enumerate((('bass','Bass -> opening relief'),('flux','Flux -> branching/fold detail'),('movement','Movement -> spatial flow'),('impact','Impact -> structural pulse')))]

# Experimental consumers have their own declarations, never Main eligibility.
for _form,_label in FRACTAL_FORMS.items():
    _group={41:'landscape',42:'recursion',43:'growth'}[_form]
    _labels={41:('Bass -> ridge relief','Movement -> flowing contours','Flux -> ridge intricacy','Sparkle -> crest glints','Impact -> ridge pulse'),
             42:('Bass -> portal aperture','Movement -> traversal','Flux -> recursive fold','Sparkle -> seam light','Impact -> portal wave'),
             43:('Bass -> petal opening','Movement -> growth flow','Flux -> bud variation','Sparkle -> pollen shimmer','Impact -> opening wave')}[_form]
    TARGETS['fractal.'+str(_form)+'.'+_group]=dict(form=_form,label=_label.removesuffix(' (Experimental)'),kind='shader input',scope='Form-owned structural and light contributions. Authored quiet shape remains; growth/traversal lifecycle is labelled separately.',roles=[
        dict(role(_source+'_response',_title,_source,'fractals.frag::'+_group+' slot '+str(64+_i),'Bounded '+_title+' contribution; no musical classification.'),slot=64+_i) for _i,(_source,_title) in enumerate(zip(('bass','movement','flux','sparkle','impact'),_labels))])
    TARGETS['form.'+str(_form)+'.material.lamellae']=dict(form=_form,label='Mineral Lamellae',kind='shader input',dependency='Enabled Mineral Lamellae treatment on this form.',scope='Fine layered mineral etching; detail and color preserve the form silhouette.',roles=[
        dict(role('flux_etch','Flux -> etched strata','flux','fractals.frag::lamellae','Etch width modulation, authored fine relief remains.'),slot=72),
        dict(role('sparkle_grain','Sparkle -> mineral grains','sparkle','fractals.frag::lamellae','Bounded grains on the existing local surface.'),slot=73)])
    TARGETS['form.'+str(_form)+'.spatial.recursive_pulse']=dict(form=_form,label='Recursive Pulse',kind='shader input',dependency='Enabled Recursive Pulse treatment on this form.',scope='Nested local deformation, quiet flow retained; no global flash.',roles=[
        dict(role('flux_fold','Flux -> nested fold','flux','fractals.frag::recursive_pulse','Bounded repeated local displacement.'),slot=74),
        dict(role('impact_wave','Impact -> nested wave','impact','fractals.frag::recursive_pulse','Bounded transient rings; existing release envelope.'),slot=75)])

# Traversal/growth are CPU-integrated uniform consumers; describe that path
# explicitly instead of implying a direct shader read for every movement role.
for _form in FRACTAL_FORMS:
    _target='fractal.'+str(_form)+'.'+{41:'landscape',42:'recursion',43:'growth'}[_form]
    for _r in TARGETS[_target]['roles']:
        if _r['source']=='movement':
            _r['consumer']='fractals.py::FractalMotion.advance slot 65 -> fractals.frag u_motion; '+('landscape contour amplitude' if _form==41 else 'atrium traversal' if _form==42 else 'garden growth')
            _r['note']='Bounded eased travel/growth rate; authored quiet rate remains. Landscape also tunes its contour amplitude.'
        elif _r['source']=='flux' and _form==43:
            _r['consumer']='fractals.py::FractalMotion.advance slot 66 and fractals.frag::growth bud twist'
