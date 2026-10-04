"""Bounded target-local substitutions for existing Planet audio contributions.

Window metadata is analysis configuration; colors and role interpretation live
here. Custom impact is an onset of one selected magnitude mean, not the legacy
maximum of three normalized band onsets. Its visual release remains exp(-6 dt).
"""
from copy import deepcopy
import math
import time
from spectral_listening import listening_choices

STYLES=dict(flux=('#f9bf62',(),'Flux (gold)'),sparkle=('#72a9ff',(6,3),'Sparkle (blue)'),
            bass=('#d69bff',(3,2),'Bass (violet)'),impact=('#ff8c8c',(8,2,2,2),'Impact (coral)'),
            movement=('#8ce3ac',(2,4),'Movement (green)'))
INGREDIENTS=dict(bass=('bass',),pressure=('bass',),flux=('flux',),sparkle=('sparkle',),
                 impact=('impact',),raw_impact=('impact',),movement=('movement',),
                 energy=('bass','flux','sparkle'),surface=('bass','flux','sparkle'),
                 flow_drive=('movement','flux','bass'))

def clip(value):return max(0.,min(1.,value))

def derived(values):
    v=dict(values);v['pressure']=clip(v.get('bass',0.))**2
    v['energy']=clip(.45*v.get('bass',0.)+.35*v.get('flux',0.)+.20*v.get('sparkle',0.))
    q=clip((v['energy']-.08)/(.65-.08));v['surface']=q*q*(3.-2.*q)
    v['flow_drive']=clip(.45*v.get('movement',0.)+.35*v.get('flux',0.)+.20*v.get('bass',0.))
    return v

def names_for_roles(roles):
    sources={name for role in roles for name in INGREDIENTS[role['source']]}
    return tuple(name for name in STYLES if name in sources)

def titles(names):
    result={}
    for name in names:
        result[name+'_start_hz']=name.capitalize()+' listening start (Hz)'
        result[name+'_end_hz']=name.capitalize()+' listening end (Hz)'
        if name=='impact':result['impact_sensitivity']='Custom-window onset sensitivity (x)'
    return result

def pack_input(value,gain):
    """Negative uniform slot means an already-scaled local value; gains >=0.

    Keeps the established 45-row uniform allocation and target/role ordering.
    [-2,-1] decodes to [1,0]; ordinary [0,4] slots retain legacy gain semantics.
    Never persisted or displayed as a user gain.
    """
    return -1.-clip(value*gain)

def unpack_input(value,slot):
    if slot<=-1.:return clip(-1.-slot)
    return value if slot==1. else clip(value*slot)

class ListeningState:
    def __init__(self,clock=time.perf_counter):
        self.clock=clock;self.measurement=None;self.observed=None
        self.impact=0.;self.impact_stamp=None;self.impact_spec=None
        self.suppressed_stamp=None

    def reset_impact(self):
        """A render rewind must not replay the last analysis onset."""
        self.impact=0.;self.impact_stamp=None
        self.suppressed_stamp=((self.measurement or {}).get('source'),(self.measurement or {}).get('sample_seconds'))

    def observe(self,payload):
        old=self.measurement or {}
        if payload is None or payload.get('source')!=old.get('source') or payload.get('sample_seconds',0.)<old.get('sample_seconds',0.):
            self.impact=0.;self.impact_stamp=None
        self.measurement=deepcopy(payload);self.observed=self.clock()

    def details(self,settings,names,active):
        choices=listening_choices(settings,names);channels=(self.measurement or {}).get('channels',{})
        current=self.observed is not None and self.clock()-self.observed<=1.
        return {name:dict(enabled=bool(active and spec[0]),ready=bool(current and channels.get(name) and
                channels[name]['spec']==list(spec) and channels[name]['bins']>0),
                measurement=deepcopy(channels.get(name)) if current and channels.get(name) and channels[name]['spec']==list(spec) else None)
                for name,spec in choices.items()}

    def select(self,settings,names,values,active,dt=0.):
        details=self.details(settings,names,active);selected=dict(values)
        for name,row in details.items():
            if row['enabled']:
                level=row['measurement']['level'] if row['ready'] else 0.
                if name=='impact':
                    stamp=((self.measurement or {}).get('source'),(self.measurement or {}).get('sample_seconds'))
                    if stamp==self.suppressed_stamp:level=0.
                    spec=listening_choices(settings,('impact',))['impact']
                    if spec!=self.impact_spec:self.impact=0.;self.impact_stamp=None;self.impact_spec=spec
                    fresh=level if stamp!=self.impact_stamp else 0.
                    self.impact_stamp=stamp
                    self.impact=max(fresh,self.impact*math.exp(-6.*max(0.,dt))) if row['ready'] else 0.
                    selected['raw_impact']=level;selected['impact']=self.impact
                else:selected[name]=level
            elif name=='impact':self.impact=0.;self.impact_stamp=None;self.impact_spec=None
        return derived(selected),details
