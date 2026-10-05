"""Named scene relationships. No graphics resources or parallel playback engine."""
import json,math
SCENES={11:'Membrane',12:'Root blossoms',2:'Geometric corridor',5:'Planet Canvas',7:'Sea',8:'Dyes',9:'Rain',10:'Waterfall',13:'Currents',14:'Fire',15:'Molten',17:'Firescape',18:'Aftershock',19:'Windstreams',20:'Stormfront',21:'Vortex',22:'Citadel',24:'Dunes',25:'Strata',26:'Crystal Cavern',28:'Nebula',29:'Marsh',30:'Pressure',32:'Magnetic Bloom',33:'Arc Constellation',34:'Auroral Veil',36:'Galaxy Odyssey'}
FAMILIES=((11,12),(7,8,9,10,13),(14,15,17,18),(19,20,21,22),(24,25,26),(28,29,30),(32,33,34))
SCENES.update({41:'Tidal Strata',42:'Recursive Atrium',43:'Honeycomb Garden'})
# label, shader style, compatible source/target sets; None means all Main scenes.
RECIPES={
 'tr_fade':('Optical crossfade',0,None),
 'tr_warp':('World warp',0,None),
 'tr_planet':('Planet Canvas pull / absorb',0,((11,12,2),(5,))),
 'tr_thermal':('Thermal exchange',0,((15,),(7,8,9,10,13))),
 'tr_discharge':('Weather discharge',0,((20,21),(32,33,34))),
 'tr_mist':('Mineral mist',0,((24,25,26),(28,29,30))),
 'tr_induction':('Citadel induction',0,((22,),(32,))),
 'tr_river':('River Carry',1,None),
 'tr_facet':('Facet Relay',2,None),
 'tr_aperture':('Depth Aperture',3,None),
 'tr_branch_iris':('Branching Iris',4,None),
 'tr_flow_fold':('Flowing Fold',5,None),
}
for name,label,forms in zip(('organic','water','fire','air','earth','fog','plasma'),('Organic form meld','Water flow meld','Fire coverage meld','Sky territory meld','Earth territory meld','Fog front meld','Plasma charge meld'),FAMILIES):
    RECIPES['tr_'+name]=(label,0,(forms,forms))
RECIPES['tr_material']=('Material meld (within a scene)',0,())
RECIPES['tr_study']=('Legacy transition study (demo)',0,())
KINDS={'tr_thermal':1,'tr_discharge':2,'tr_mist':3,'tr_induction':4}
def compatible(key,source,target):
    if key not in RECIPES or source==target or source not in SCENES or target not in SCENES:return False
    pair=RECIPES[key][2]
    return pair is None or bool(pair and ((source in pair[0] and target in pair[1]) or (target in pair[0] and source in pair[1])))
def description(key):
    pair=RECIPES[key][2]
    if pair is None:return 'Any two Main scenes.'
    if not pair:return 'Within-scene material playback.' if key=='tr_material' else 'Preserved standalone transition demonstration.'
    return ' / '.join(', '.join(SCENES[s] for s in forms) for forms in pair)+'; either direction.'
def validate_settings(data=None):
    if data is None:data={}
    if not isinstance(data,dict):raise ValueError('Invalid transition settings.')
    pair=data.get('pair',[]); isolate=data.get('isolate',{})
    if not isinstance(pair,list) or (pair and (len(pair)!=2 or any(type(s) is not int or s not in SCENES for s in pair) or pair[0]==pair[1])):raise ValueError('Choose two different original scenes for the transition preview.')
    if not isinstance(isolate,dict) or any(w not in ('pair','blend','organic','geometric','cosmic','water','fire','air','earth','fog','plasma','transition','fractal_landscape','fractal_atrium','fractal_bloom') or key not in RECIPES or key in ('tr_material','tr_study') for w,key in isolate.items()):raise ValueError('Unknown isolated scene transition.')
    out=dict(pair=list(pair),isolate=dict(isolate))
    for key,default,lo,hi in (('hold',12.,1.,300.),('duration',6.,1.,20.)):
        value=data.get(key,default)
        if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:raise ValueError(f'Transition {key} must be between {lo:g} and {hi:g} seconds.')
        out[key]=float(value)
    return out
def parse_settings(text):return validate_settings(json.loads(text))
def eligible_recipes(source,target,profile=None):
    configured=[r['id'] for r in (profile or {}).get('items',[]) if r['enabled'] and r['id'] in RECIPES and compatible(r['id'],source,target)]
    return configured or [k for k in RECIPES if compatible(k,source,target)]

def select_recipe(rng,source,target,profile=None,isolate=None,index=0,recent=()):
    if isolate:
        if not compatible(isolate,source,target):raise ValueError(RECIPES[isolate][0]+' is incompatible with this scene pair. '+description(isolate))
        key=isolate
    else:
        configured=[r['id'] for r in (profile or {}).get('items',[]) if r['enabled'] and r['id'] in RECIPES and compatible(r['id'],source,target)]
        keys=eligible_recipes(source,target,profile)
        if configured and profile['mode']=='cycle':key=keys[index%len(keys)]
        else:
            weights=[(1.55 if RECIPES[k][2] else .90 if RECIPES[k][1] else .72)*(.18 if k in recent[-4:] else .55 if k in recent[-8:] else 1.) for k in keys]
            key=rng.choices(keys,weights=weights,k=1)[0]
    layout=(rng.uniform(-math.pi,math.pi),rng.uniform(-.16,.16),rng.uniform(-.10,.10),rng.random())
    return RECIPES[key][1],layout,key
def recipe_uniforms(key,p,source,target,layout,family):
    style=RECIPES[key][1]
    # Negative style selects endpoint-image compositing; zero retains native melds.
    if key=='tr_fade':return {'u_main_transition':(-1.,p,float(source),float(target)),'u_main_layout':layout,'u_handoff':(0.,0.,0.,0.),'u_world_warp':0.}
    if style:return {'u_main_transition':(float(style),p,float(source),float(target)),'u_main_layout':layout,'u_handoff':(0.,0.,0.,0.),'u_world_warp':0.}
    return {'u_handoff':(float(KINDS.get(key,0)),p,float(family(source)),float(family(target))),'u_world_warp':math.sin(math.pi*p) if key=='tr_warp' else 0.}
def reprise_budgets(minimum,maximum,is_reprise):
    return (minimum*.52,maximum*.50) if is_reprise else (minimum,maximum)
