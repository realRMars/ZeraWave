"""Seeded celestial descriptors and continuous camera routes; no graphics/audio.

Stable hierarchical identities, bounded descriptor cache and local scale bridges
can be reused by later worlds. This authors a visual journey, not an astronomical
simulation or literally infinite stored universe.
"""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import math
import colorsys

PERIOD = 74.
SYSTEM_SCALE = .004
OVERVIEW_FRACTION = .18
PHASES = ((0.,14.,'survey'),(14.,18.,'acquire'),(18.,23.,'approach'),
          (23.,59.,'system'),(59.,63.,'lock'),(63.,74.,'warp'))

def child_seed(seed, *path):
    """Versioned identity independent of Python's randomized hash/random state."""
    payload='cosmos-v1/'+str(int(seed))+'/'+'/'.join(map(str,path))
    return int.from_bytes(hashlib.blake2s(payload.encode(),digest_size=8).digest(),'little')

def unit(seed, role):
    return (child_seed(seed,role)&0xffffffff)/4294967296.

def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def mix(a,b,s):return tuple(x+(y-x)*s for x,y in zip(a,b))
def length(a):return math.sqrt(sum(x*x for x in a))
def normalize(a):return mul(a,1./max(length(a),1e-12))
def ease(x):
    x=max(0.,min(1.,x));return x*x*x*(x*(x*6.-15.)+10.)
def bezier(a,b,c,d,u):
    return add(add(mul(a,(1-u)**3),mul(b,3*u*(1-u)**2)),
               add(mul(c,3*u*u*(1-u)),mul(d,u**3)))

@dataclass(frozen=True)
class Destination:
    seed: int
    index: int
    galaxy: tuple
    anchor: tuple
    planets: tuple
    direction: tuple
    entry: tuple
    star_kind: float
    traits: tuple
    stars: tuple
    visits: tuple
    architecture: str

@lru_cache(maxsize=12)
def destination(seed, index):
    ident=child_seed(seed,'galaxy',index)
    system=child_seed(ident,'system',int(unit(ident,'chosen-system')*4096))
    arms=2+(index%3)
    pitch=4.2+unit(ident,'pitch')*2.3
    radius=.58+unit(system,'radius')*.25
    theta=(-pitch*math.log(radius+.16)+2*math.pi*(system%arms))/arms
    anchor=(math.cos(theta)*radius,.18,math.sin(theta)*radius)
    # Deterministic contrasting architecture itinerary; every five destinations
    # includes all counts, with fresh nested bodies/layouts rather than a fixed tour.
    family=(child_seed(seed,'architecture-v2')%5+index)%5
    count=(0,1,2,4,8)[family]
    planets=[];traits=[]
    rare=(child_seed(system,'rare-pulsar')%13==0)
    primary=.26 if rare else .90+unit(system,'primary-size')*.20
    binary=count==0 or unit(system,'binary')>.52
    companion=primary*(.24+unit(system,'companion-size')*.26) if binary else 0.
    separation=2.15+unit(system,'separation')*.45
    stars=(primary,companion,separation,unit(system,'star-phase')*math.tau)
    previous_outer=separation+companion if binary else primary
    for i in range(count):
        body=child_seed(system,'body-v3',i)
        kind=(int(unit(body,'material')*7)+index*3+i)%7
        size=.13+unit(body,'size')*(.21 if kind in (2,3) else .15)
        if count==1:size=min(.42,size*1.4)
        extent=size*(2.45 if kind==3 else 1.04)
        eccentricity=unit(body,'eccentricity')*.055
        orbit=max(4.6,(previous_outer+extent+1.05+unit(body,'gap')*.7)/(1.-eccentricity))
        previous_outer=orbit*(1.+eccentricity)+extent
        planets.append((orbit,size,unit(body,'phase')*math.tau,float(kind)))
        traits.append(((unit(body,'tilt')-.5)*(.30+.28*unit(system,'tilt')),
                       eccentricity,unit(body,'pigment'),.65+unit(body,'texture')*2.1))
    # Feature actual generated bodies, emphasizing silhouettes without imposing
    # ocean/rock/giant types. Every available body is visited in one/two-body worlds.
    visits=tuple(sorted(range(count),key=lambda i:unit(child_seed(system,'body-v2',i),'visit'),reverse=True)[:3])
    az=unit(ident,'entry')*math.tau
    entry=(math.cos(az)*1.8,1.1,math.sin(az)*1.8)
    heading=unit(ident,'next-heading')*math.tau
    direction=normalize((math.cos(heading),.18+unit(ident,'next-height')*.32,math.sin(heading)))
    return Destination(ident,index,(float(arms),pitch,float(ident%997),.72+.17*(index%3)),
        anchor,tuple(planets),direction,entry,(.97 if rare else unit(system,'star-kind')*.89),
        tuple(traits),stars,visits,('Stellar Cradle','Solitary World','Twin Orbits','Tilted Quartet','Crowded Clockwork')[family])

def planet_position(spec, clock, traits=(0.,0.,0.,1.)):
    orbit,_,phase,_=spec;inclination,eccentricity,_,_=traits
    angle=phase+clock*.12/(orbit**1.5)
    radius=orbit*(1.-eccentricity**2)/(1.+eccentricity*math.cos(angle))
    bend=1.5*(1.-1./(1.+radius*radius*.9))
    return (math.cos(angle)*radius,bend+math.sin(angle)*radius*math.sin(inclination),
            math.sin(angle)*radius*math.cos(inclination))

def companion_position(d, clock):
    phase=d.stars[3]+clock*.14;radius=d.stars[2]
    bend=1.5*(1.-1./(1.+radius*radius*.9))
    return (math.cos(phase)*radius,bend+.18*math.sin(phase*.7),math.sin(phase)*radius)

def system_pose(d, u, clock):
    """Adaptive feature visits with smooth above-plane transfers. Empty systems
    explore their stellar subjects, never nonexistent planet indices."""
    subjects=d.visits if d.planets else tuple(range(2 if d.stars[1]>0 else 1))
    def visit(slot, v):
        i=subjects[slot]
        if d.planets:
            target=planet_position(d.planets[i],clock,d.traits[i]);radius=d.planets[i][1]
            sun_angle=math.atan2(target[2],target[0]);angle=sun_angle-.10+ease(v)*.20+(d.traits[i][2]-.5)*.04
            distance=radius*(6.5 if d.planets[i][3]==3 else 3.6)
        else:
            target=(0.,0.,0.) if i==0 else companion_position(d,clock)
            radius=d.stars[i];distance=radius*(6.0+.8*math.sin(v*math.pi));angle=.35+ease(v)*2.4+d.star_kind*2.
        elevation=target[1]/max(.1,length((target[0],target[2]))) if d.planets else .60+.15*math.sin(v*math.pi)
        offset=(math.cos(angle)*distance,distance*elevation,math.sin(angle)*distance)
        eye=add(target,offset)
        # Smooth screen-space avoidance: push viewpoint around a foreground body
        # intersecting the sightline, rather than accepting a hidden destination.
        if d.planets:
            for other,spec in enumerate(d.planets):
                if other==i:continue
                center=planet_position(spec,clock,d.traits[other])
                sight=normalize(tuple(a-b for a,b in zip(target,eye)))
                delta=tuple(a-b for a,b in zip(center,eye));along=sum(a*b for a,b in zip(delta,sight))
                relative=tuple(a-b for a,b in zip(center,target))
                behind=sum(a*b for a,b in zip(relative,sight))
                if along>0. and behind<0.:
                    perpendicular=tuple(a-along*b for a,b in zip(delta,sight))
                    coverage=spec[1]*2.2
                    proximity=math.exp(-length(perpendicular)**2/(coverage*coverage))
                    # Above-plane lift provides consistent direction even for
                    # a perfectly centered occluder, with no discrete choice.
                    eye=add(eye,(0.,proximity*coverage*2.8,0.))
        return eye,target,-.08+.16*ease(v)
    overview=(6.2,3.6,7.);base=(4.8,2.5,5.2)
    if u<OVERVIEW_FRACTION:return mix(overview,base,ease(u/OVERVIEW_FRACTION)),(0.,0.,0.),0.
    span=(1.-OVERVIEW_FRACTION)/len(subjects);slot=min(len(subjects)-1,int((u-OVERVIEW_FRACTION)/span))
    v=((u-OVERVIEW_FRACTION)/span-slot)
    if v<.28:
        before=(base,(0.,0.,0.),0.) if slot==0 else visit(slot-1,1.)
        after=visit(slot,0.);blend=ease(v/.28)
        lift=1.5 if d.planets else .65
        eye=bezier(before[0],add(before[0],(0.,lift,0.)),add(after[0],(0.,lift,0.)),after[0],blend)
        return eye,mix(before[1],after[1],ease(v/.10) if d.planets else blend),before[2]+(after[2]-before[2])*blend
    return visit(slot,min(1.,(v-.28)/.72))



def camera_basis(eye,target,bank=0.):
    forward=normalize(tuple(a-b for a,b in zip(target,eye)))
    right=normalize((-forward[2],0.,forward[0]))
    up=(right[1]*forward[2]-right[2]*forward[1],right[2]*forward[0]-right[0]*forward[2],right[0]*forward[1]-right[1]*forward[0])
    return add(mul(right,math.cos(bank)),mul(up,math.sin(bank))),add(mul(up,math.cos(bank)),mul(right,-math.sin(bank))),forward


def frame_primary(d,eye,target,bank):
    """Conservative perspective sphere fit at4:3 or wider, including1.11
    musical swell and visible corona. Pull along authored viewing direction;
    retain target/bank/energy. Outward body visits keep the primary behind the foreground world; full fit retains both subjects.
    No dynamic resize-dependent camera or audio-induced camera movement."""
    if d.star_kind>.95:return eye,target,bank  # retain accepted compact pulsar exploration
    right,up,forward=camera_basis(eye,target,bank)
    radius=d.stars[0]*1.75
    delta=mul(eye,-1.)
    x=sum(a*b for a,b in zip(delta,right));y=sum(a*b for a,b in zip(delta,up));z=sum(a*b for a,b in zip(delta,forward))
    # p ranges +/-aspect*.5 horizontally and +/-.5 vertically; ray p*.95.
    # .37 margin and .30 corona radius limit are stricter than the actual frame edges.
    setback=max(0.,radius+max((abs(x)+radius)/(.37*.95*4/3),(abs(y)+radius)/(.37*.95),radius/(.30*.95))-z)
    return add(eye,mul(forward,-setback)),target,bank




def survey_pose(d, u):
    az=math.atan2(d.entry[2],d.entry[0])
    elevation=1.1-.32*ease((u*14.-4.)/7.)
    eye=(math.cos(az)*1.8,elevation,math.sin(az)*1.8)
    return eye,(0.,0.,0.),0.


def inward_anchor(d, age):
    """Authored inward stellar arc, shared by acquisition, bridge and system."""
    u=ease((age-14.)/9.);angle=.18*u;radius=1.-.22*u
    x,y,z=d.anchor
    return ((x*math.cos(angle)-z*math.sin(angle))*radius,y+.025*u,
            (x*math.sin(angle)+z*math.cos(angle))*radius)

def journey(seed, seconds, clock=None):
    """Pure random-access route. Exact replay/seek, bounded work, no retained
    itinerary. Warp's next descriptor is the subsequent survey's descriptor."""
    seconds=max(0.,float(seconds));clock=seconds if clock is None else clock
    index=int(seconds//PERIOD);age=seconds-index*PERIOD
    d=destination(int(seed),index);n=destination(int(seed),index+1)
    anchor=inward_anchor(d,age)
    phase=next(i for i,(a,b,_) in enumerate(PHASES) if a<=age<b)
    start,end,name=PHASES[phase];u=(age-start)/(end-start)
    if phase==0:eye,target,bank=survey_pose(d,u)
    elif phase==1:
        eye,_,_=survey_pose(d,1.)
        target=mix((0.,0.,0.),anchor,ease(u));bank=0.
    elif phase==2:
        first,_,_=survey_pose(d,1.)
        entry_eye,_,_=frame_primary(d,(6.2,3.6,7.),(0.,0.,0.),0.)
        last=add(anchor,mul(entry_eye,SYSTEM_SCALE))
        # Log-distance bridge retains the selected sun at the same world point.
        first_offset=tuple(x-y for x,y in zip(first,anchor))
        last_offset=tuple(x-y for x,y in zip(last,anchor))
        radius=math.exp(math.log(length(first_offset))*(1.-ease(u))+math.log(length(last_offset))*ease(u))
        direction=normalize(mix(normalize(first_offset),normalize(last_offset),ease(u)))
        eye=add(anchor,mul(direction,radius));target=anchor;bank=0.
    else:
        local_eye,local_target,bank=system_pose(d,1. if phase>=4 else u,clock)
        # Continuous local camera exclusion, including transfer paths.
        for i,spec in enumerate(d.planets):
            center=planet_position(spec,clock,d.traits[i])
            delta=tuple(a-b for a,b in zip(local_eye,center));distance=length(delta)
            if distance<spec[1]*2.:local_eye=add(local_eye,mul(normalize(delta),spec[1]*2.-distance))
        for i,radius in enumerate(d.stars[:2]):
            if radius<=0:continue
            center=(0.,0.,0.) if i==0 else companion_position(d,clock)
            delta=tuple(a-b for a,b in zip(local_eye,center));distance=length(delta)
            if distance<radius*5.:local_eye=add(local_eye,mul(normalize(delta),radius*5.-distance))
        floor=-.18+1.5*(1.-1./(1.+(local_eye[0]**2+local_eye[2]**2)*.9))
        if not d.planets:local_eye=(local_eye[0],max(local_eye[1],floor+.52),local_eye[2])
        local_eye,local_target,bank=frame_primary(d,local_eye,local_target,bank)
        eye=add(anchor,mul(local_eye,SYSTEM_SCALE));target=add(anchor,mul(local_target,SYSTEM_SCALE))
        if phase>=4:
            look=add(eye,mul(d.direction,SYSTEM_SCALE*12.))
            target=mix(target,look,ease(u) if phase==4 else 1.)
            bank*=1.-(ease(u) if phase==4 else 1.)
    return dict(index=index,phase=phase,name=name,fraction=u,eye=eye,target=target,bank=bank,
                current=d,next=n,anchor=anchor,system_scale=SYSTEM_SCALE)

def uniforms(seed,seconds,clock=None):
    state=journey(seed,seconds,clock);d=state['current'];n=state['next']
    return dict(u_journey_eye=state['eye'],u_journey_target=state['target'],u_journey_bank=state['bank'],
        u_journey=(float(state['phase']),state['fraction'],float(state['index']%65536),d.star_kind),
        u_journey_galaxy=d.galaxy,u_journey_anchor=(*state['anchor'],SYSTEM_SCALE),
        u_journey_planets=d.planets+((1.,0.,0.,-1.),)*(8-len(d.planets)),
        u_journey_traits=d.traits+((0.,0.,0.,1.),)*(8-len(d.traits)),
        u_journey_count=len(d.planets),u_journey_stars=d.stars,u_journey_heading=d.direction,
        u_journey_centers=tuple(planet_position(p,seconds if clock is None else clock,d.traits[i]) for i,p in enumerate(d.planets))+((0.,0.,0.),)*(8-len(d.planets)),
        u_journey_companion_center=companion_position(d,seconds if clock is None else clock),
        u_journey_next=n.galaxy,u_journey_next_eye=n.entry)


def visit_signature(seed,index):
    """No palette repeats within12 previous visits, by a coprime13-slot walk.
    Other axes and continuous local recipes remain seeded; not13 fixed worlds."""
    return ((child_seed(seed,'architecture-v2')%5+index)%5,
            (child_seed(seed,'pigment-order-v3')%13+index*5)%13,
            (child_seed(seed,'material-order-v3')%7+index*3)%7)

def entry_phase(seed,index):
    return (0.,18.8,24.,39.,63.4)[(child_seed(seed,'entry-phase-v3')%5+index)%5]

@lru_cache(maxsize=12)
def authored_pigments(seed,index):
    """Local artistic source roles, not a whole-screen synchronized hue wash."""
    ident=child_seed(seed,'pigments-v3',index);_,family,_=visit_signature(seed,index)
    hue=(family/13.+(unit(ident,'hue')-.5)*.035)%1.
    role=0
    def color(h,s,v):
        nonlocal role
        saturation=min(.95,s*(.80+.28*unit(ident,'saturation/'+str(role))))
        value=v*(.84+.16*unit(ident,'value/'+str(role)));role+=1
        return '#'+''.join(f'{round(c*255):02X}' for c in colorsys.hsv_to_rgb(h%1.,saturation,value))
    star_hue=(.035,.10,.54,.67,.90)[int(unit(ident,'star-spectrum')*5)]
    structure=(color(star_hue,.38,1.),color(hue,.70,.86),color(hue+.10,.54,.17),
               color(hue+.48,.26,.96),color(hue+.38,.82,.97),color(hue+.68,.76,.88))
    system=(color(star_hue,.48,1.),color(hue+.16,.58,.56),color(hue+.53,.79,.72),
            color(hue+.84,.66,.78),color(hue+.35,.35,.92),color(hue+.63,.48,.96),
            color(hue+.08,.73,.70),color(hue+.40,.78,1.))
    return structure,system
