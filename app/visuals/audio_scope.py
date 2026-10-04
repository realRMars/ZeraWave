"""Run/session/form/target identities for the existing Studio tuning transport.

No renderer, capture, storage or UI ownership. Callers validate actual target
settings and explicitly choose storage destinations after acknowledgement checks.
"""
from dataclasses import dataclass
from copy import deepcopy
import hashlib,json,math,time
from transition_catalog import SCENES,RECIPES

FORMS=tuple(SCENES)
TRANSITION_FORM=0
MAX_REVISION=2**31
MAX_AGE_SECONDS=1.

def token(value):
    return type(value) is str and 1<=len(value)<=128 and value.isascii() and all(c.isalnum() or c in '-_.' for c in value)

@dataclass(frozen=True)
class Scope:
    run:str
    session:str
    form:int
    target:str
    revision:int

    @classmethod
    def read(cls,data):
        if not isinstance(data,dict):raise ValueError('Missing audio scope')
        run,session,form,target,revision=(data.get(k) for k in ('run','session','form','target','revision'))
        if not token(run) or not token(session):raise ValueError('Invalid run/session identity')
        if type(form) is not int or form not in FORMS+(TRANSITION_FORM,):raise ValueError('Unsupported audio form')
        if type(target) is not str or not 1<=len(target)<=160 or not all(c.isalnum() or c in '._-' for c in target):raise ValueError('Invalid audio target')
        if form==TRANSITION_FORM and (not target.startswith('transition.') or target.removeprefix('transition.') not in (*RECIPES,'director')):raise ValueError('Unsupported transition target')
        if type(revision) is not int or not 0<=revision<MAX_REVISION:raise ValueError('Invalid audio revision')
        return cls(run,session,form,target,revision)

    @property
    def owner(self):return self.run,self.session,self.form,self.target

    def packet(self):return dict(run=self.run,session=self.session,form=self.form,target=self.target,revision=self.revision)

def digest(settings):
    return hashlib.sha256(json.dumps(settings,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class ScopeMailbox:
    """One latest complete command per declared target; caller holds its IO lock."""
    def __init__(self,run,session,validate):
        if not token(run) or not token(session):raise ValueError('Invalid mailbox identity')
        self.run,self.session,self.validate=run,session,validate
        self.revisions={};self.pending={};self.authored={}

    def accept(self,message):
        scope=Scope.read(message.get('scope') if isinstance(message,dict) else None)
        if (scope.run,scope.session)!=(self.run,self.session):raise ValueError('Audio command belongs to another run/session')
        key=(scope.form,scope.target)
        if scope.revision<=self.revisions.get(key,-1):return False
        settings=self.validate(scope.form,scope.target,message.get('settings'))
        authored=self.validate(scope.form,scope.target,message['authored']) if 'authored' in message else None
        if authored is not None and authored.get('enabled') is not True:raise ValueError('Invalid authored audio values')
        # Coalescing a later drag must not lose an explicit authored promotion.
        if authored is not None:self.authored[key]=deepcopy(authored)
        author=deepcopy(self.authored.get(key))
        self.revisions[key]=scope.revision;self.pending[key]=(scope,deepcopy(settings),author)
        return True

    def take(self):
        values=list(self.pending.values());self.pending.clear();return values

@dataclass(frozen=True)
class SaveTicket:
    scope:Scope
    settings_digest:str

    @classmethod
    def acknowledged(cls,scope,settings,ack,received,clock=time.perf_counter):
        if Scope.read(ack.get('scope'))!=scope:raise ValueError('Audio acknowledgement belongs to another scope/revision')
        if ack.get('error') or ack.get('rejected_revision')==scope.revision:raise ValueError('Audio revision was rejected')
        now=clock()
        if type(received) not in (int,float) or not math.isfinite(received) or not 0.<=now-received<=MAX_AGE_SECONDS:raise ValueError('Current audio acknowledgement required')
        if digest(settings)!=digest(ack.get('effective')):raise ValueError('Audio values are not acknowledged')
        return cls(scope,digest(settings))

    def verify(self,current_scope,settings):
        if self.scope!=current_scope or self.settings_digest!=digest(settings):raise ValueError('Save destination or acknowledged values changed')

def endpoints(renderer,seconds):
    """Actual director/pair endpoints; unavailable experimental forms stay absent."""
    state=renderer.state_at(seconds)
    if getattr(renderer,'transition_sequence',False):
        config=renderer.transition_settings;seq=renderer.debug_sequence;span=config['hold']+config['duration']
        index=int(max(0.,seconds)//span);age=max(0.,seconds)%span
        source=seq[index%len(seq)];target=seq[(index+1)%len(seq)]
        phase=max(0.,min(1.,(age-config['hold'])/config['duration']))
        if state!=0:target=None
    elif state==0:
        source=getattr(renderer,'director_current',None);target=getattr(renderer,'director_target',None)
        phase=renderer.transition_progress() if target is not None else 0.
        phase=phase if phase is not None else 0.
    else:
        source=state;target=None;phase=0.
        # Existing authored family cycles use u_drift_time == render seconds.
        # They expose the same canonical form owners; no cycle is redesigned.
        import math
        def smooth(low,high,x):
            x=max(0.,min(1.,(x-low)/(high-low)));return x*x*(3.-2.*x)
        cycles={6:((7,8,9,10,13),28.,.68),23:((19,20,21,22),36.,.65),
                27:((24,25,26),36.,.65),31:((28,29,30),38.,.70),35:((32,33,34),36.,.68)}
        if state in cycles:
            ids,hold,start=cycles[state];position=max(0.,seconds)/hold
            index=int(position)%len(ids);phase=smooth(start,1.,position%1.)
            source=ids[index];target=ids[(index+1)%len(ids)] if phase>0. else None
        elif state==1:
            phase=smooth(.35,.65,.5+.5*math.sin(seconds*.04-1.8))
            source=11 if phase<1. else 12;target=12 if 0.<phase<1. else None
        elif state==16:
            age=max(0.,seconds)%84.
            if age<28.:source=14;phase=smooth(19.,28.,age);target=15 if phase>0. else None
            elif age<56.:source=15;phase=smooth(47.,56.,age);target=17 if phase>0. else None
            else:source=17;phase=smooth(75.,84.,age);target=14 if phase>0. else None
    available=tuple(f for f in (source,target) if f in FORMS)
    if target not in FORMS:target=None
    if source not in FORMS:source=None
    return dict(outgoing=source,incoming=target,progress=phase,recipe=getattr(renderer,'director_recipe',None) if target is not None else None,
        active=list(dict.fromkeys(available)),primary=target if target is not None and phase>=.5 else source,
        experimental_unavailable=state not in FORMS+(0,1,6,16,23,27,31,35))
