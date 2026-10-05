"""Musical/history-aware Main selection and bounded spatial handoff recipes.

Trait descriptions are authored visual metadata, not a genre or mood classifier.
"""
import math

# energy preference, family, composition, representative authored pigment.
TRAITS={
 11:(.25,'organic','organic',(.34,.51,.75)),12:(.40,'organic','branch',(.42,.38,.63)),
 2:(.75,'geometry','corridor',(.25,.68,.72)),5:(.65,'cosmic','radial',(.70,.33,.51)),
 7:(.65,'water','landscape',(.16,.43,.62)),8:(.30,'water','organic',(.63,.30,.54)),9:(.25,'water','vertical',(.31,.53,.67)),10:(.55,'water','vertical',(.36,.67,.64)),13:(.25,'water','flow',(.30,.45,.72)),
 14:(.70,'fire','vertical',(.93,.35,.07)),15:(.50,'fire','landscape',(.95,.24,.025)),17:(.80,'fire','landscape',(.65,.25,.12)),18:(.90,'fire','radial',(.73,.28,.37)),
 19:(.30,'air','flow',(.36,.53,.66)),20:(.75,'air','corridor',(.35,.41,.66)),21:(.85,'air','radial',(.48,.35,.72)),22:(.60,'air','architecture',(.39,.58,.68)),
 24:(.30,'earth','landscape',(.67,.43,.24)),25:(.65,'earth','landscape',(.63,.39,.41)),26:(.70,'earth','architecture',(.27,.55,.51)),
 28:(.40,'fog','organic',(.37,.30,.61)),29:(.25,'fog','landscape',(.25,.70,.49)),30:(.85,'fog','corridor',(.31,.41,.62)),
 32:(.65,'plasma','radial',(.65,.43,.32)),33:(.90,'plasma','branch',(.34,.55,.88)),34:(.35,'plasma','vertical',(.41,.78,.69)),
 36:(.65,'cosmic','journey',(.36,.53,.92)),
 41:(.35,'fractal','landscape',(.45,.52,.68)),42:(.75,'fractal','architecture',(.28,.65,.76)),43:(.55,'fractal','radial',(.95,.65,.10))}
PIGMENT_TARGETS={36:('galaxy.structure','arms'),15:('molten.palette','heat'),22:('citadel.lantern','beacon'),26:('cavern.land','crystals'),29:('marsh.palette','cool'),32:('magnetic.field','loops'),33:('arcs.charge','arcs'),34:('auroral.curtains','sheets')}
TRANSITIONS={0:'Selective callback / dissolve',1:'River Carry',2:'Facet Relay',3:'Depth Aperture'}

def pigment(state,overrides):
    authored=TRAITS[state][3];target,role=PIGMENT_TARGETS.get(state,('', ''))
    value=overrides.get(target,{}).get(role,{}) if isinstance(overrides,dict) else {}
    color=value.get('color') if isinstance(value,dict) else None
    if isinstance(color,str) and len(color)==7 and color.startswith('#'):
        try:return tuple(int(color[k:k+2],16)/255. for k in (1,3,5))
        except ValueError:pass
    return authored

def candidate_scores(pool,current,energy,lift,now,last_seen,pairs,priorities,overrides):
    energy=max(0.,min(1.,energy));source=TRAITS.get(current);rows=[]
    for state in pool:
        if state==current:continue
        preference,family,composition,color=TRAITS[state]
        age=240. if state not in last_seen else max(0.,now-last_seen[state])
        fit=.18+math.exp(-((energy-preference)/.30)**2)
        recency=.07+.93*(1-math.exp(-age/65.))
        coverage=1.+min(age,360.)/120.
        repeated=sum(1 for a,b in pairs if (a,b)==(current,state) or (a,b)==(state,current))
        pair=max(.08,.28**repeated)
        family_contrast=1. if source is None else (1.25 if family!=source[1] else .83)
        composition_contrast=1. if source is None else (1.22 if composition!=source[2] else .88)
        palette_contrast=1. if source is None else 1.+.28*min(1.,math.dist(pigment(current,overrides),pigment(state,overrides)))
        # Related spatial grammars remain useful without monopolizing the itinerary.
        affinity=1.12 if source and (source[1],family) in (('earth','fog'),('fog','earth'),('fire','water'),('water','fire')) else 1.
        fresh_priority=.80+.40*priorities.get(state,.5)
        lift_fit=1.+(.12 if lift and preference>.55 else 0.)
        factors=dict(musical_fit=fit,recency=recency,coverage=coverage,recent_pair=pair,family_contrast=family_contrast,composition_contrast=composition_contrast,palette_contrast=palette_contrast,transition_affinity=affinity,shuffled_priority=fresh_priority,lift=lift_fit)
        rows.append({'state':state,'score':math.prod(factors.values()),'factors':factors})
    return rows

def choose_transition(rng,source,target,reason,recent_styles,related=False):
    # Selective existing callbacks/dissolves remain, rather than being a default.
    if rng.random() < (.22 if related else .07):return 0,(0.,0.,0.,0.),'related callback' if related else 'quiet optical dissolve'
    a,b=TRAITS[source],TRAITS[target];scores=[1.25 if 'landscape' in (a[2],b[2]) else 1.,1.35 if 'architecture' in (a[2],b[2]) or 'branch' in (a[2],b[2]) else 1.,1.4 if 'radial' in (a[2],b[2]) or reason=='release' else 1.]
    for i in range(3):scores[i]*=.48 if i+1 in recent_styles[-2:] else 1.
    style=rng.choices((1,2,3),weights=scores,k=1)[0]
    layout=(rng.uniform(-math.pi,math.pi),rng.uniform(-.16,.16),rng.uniform(-.10,.10),rng.random())
    return style,layout,'regional ownership with '+TRANSITIONS[style]

def transition_uniforms(style,progress,source,target,layout):
    if style<=0:return {}
    return {'u_main_transition':(float(style),max(0.,min(1.,progress)),float(source),float(target)),'u_main_layout':tuple(layout),'u_handoff':(0.,0.,0.,0.),'u_world_warp':0.}

def transition_sample(style,progress,x,y,aspect,layout):
    """CPU equation reference for endpoint/bound/monotonic checks; not a GPU claim."""
    angle,cx,cy,salt=layout;axis=(math.cos(angle),math.sin(angle));extent=abs(axis[0])*aspect*.5+abs(axis[1])*.5
    qx,qy=x*axis[0]+y*axis[1],-x*axis[1]+y*axis[0]
    if style==1:field=.5+qx/max(extent,.001)*.39+.065*math.sin(qy*7.+salt*6.28)+.025*math.sin(qy*13.-salt*3.)
    elif style==2:
        cell=(math.floor(x*5.),math.floor(y*5.));noise=math.sin(cell[0]*37.1+cell[1]*91.7+salt*19.)*4375.3;noise-=math.floor(noise)
        field=.5+qx/max(extent,.001)*.36+(noise-.5)*.18
    else:field=.08+.80*math.hypot((x-cx)*.82,y-cy)/max(math.hypot((aspect*.5+abs(cx))*.82,.5+abs(cy)),.001)
    field=max(.07,min(.93,field));f=max(0.,min(1.,(progress-field+.028)/.056));return f*f*(3.-2*f)
