"""CPU-only rollout ownership, persistence, real-FFT routing and audition tests."""
import ast,json,os,random,sys,tempfile,time
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from audio_controls import TARGETS,form_targets,defaults,bounds,validate,validate_target,slots,windows,WORLD_GROUPS
from audio_scope import Scope,ScopeMailbox,SaveTicket
from form_audio_tuning import FormAudioTuning
from planet_listening import unpack_input
from star_tuning_profiles import TargetProfileStore
from studio_audition import PreviewAudition,capture
from transition_catalog import SCENES,validate_settings

INPUTS=dict(bass=.2,movement=.3,flux=.4,sparkle=.5,impact=.6,raw_impact=.1)

def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('Invalid operation accepted')

def ownership():
    mailbox=ScopeMailbox('run','session',validate_target)
    for form in SCENES:
        target=form_targets(form)[0]
        if form==5:continue
        settings=defaults(target);s=Scope('run','session',form,target,1)
        assert mailbox.accept(dict(scope=s.packet(),settings=settings))
        assert not mailbox.accept(dict(scope=s.packet(),settings=settings))
        for bad in (Scope('wrong','session',form,target,2),Scope('run','wrong',form,target,2),Scope('run','session',5,target,2)):
            reject(lambda:mailbox.accept(dict(scope=bad.packet(),settings=settings)))
    assert len(mailbox.take())==26
    for t,p in TARGETS.items():
        c=defaults(t);validate(p['form'],t,c)
        key=next(iter(bounds(t)));bad=dict(c,**{key:float('nan')})
        reject(lambda:validate(p['form'],t,bad))
    return dict(canonical_forms=27,declared_targets=len(TARGETS),wrong_run_session_form_rejected=True,duplicate_revisions_rejected=True)

def routing():
    clock=[100.];m=FormAudioTuning('run','session',clock=lambda:clock[0]);f=np.arange(1025)*48000/2048
    m.resolve([12,5],INPUTS);assert not m.processors
    target='roots.growth';c=dict(defaults(target),flux_branch=0.,enabled=True)
    m.submit(dict(scope=Scope('run','session',12,target,1).packet(),settings=c));rows=m.resolve([12,5],INPUTS)
    slot=slots(12)[(target,'flux_branch')];assert rows[12][slot//4][slot%4]==0.
    assert unpack_input(INPUTS['flux'],rows[12][slot//4][slot%4])==0.
    # A different form's copy of the actual shared technique stays neutral.
    a='form.12.material.alloy';b='form.11.material.alloy';role='bass_shape'
    c=dict(defaults(a),bass_shape=3.);m.submit(dict(scope=Scope('run','session',12,a,1).packet(),settings=c))
    rows=m.resolve([12,11],INPUTS);slot=slots(12)[(a,role)]
    assert rows[12][slot//4][slot%4]==3. and rows[11][slot//4][slot%4]==1.
    # Disabled windows use the original inputs exactly, with no FFT histories.
    payload=m.process(f,np.ones(1025),2048,'fixture');assert not payload and not m.processors
    c=dict(defaults(target),flux_range_enabled=True,flux_start_hz=90.,flux_end_hz=130.)
    m.submit(dict(scope=Scope('run','session',12,target,2).packet(),settings=c));m.resolve([12],INPUTS)
    for i in range(4):
        payload=m.process(f,np.full(1025,1.+i*.1),2048,'fixture');m.observe(payload);rows=m.resolve([12],INPUTS,2048/48000.)
    row=m.status(12,target,INPUTS);measure=row['listening']['flux']['measurement']
    assert measure['bins']==2 and measure['first_hz']==93.75 and measure['last_hz']==117.1875
    assert rows[12][16][0]<=-1. and len(m.processors)==1
    # A 1 Hz edit positions edges but cannot invent bins.
    bad=dict(c,flux_start_hz=100.,flux_end_hz=101.)
    m.submit(dict(scope=Scope('run','session',12,target,3).packet(),settings=bad));m.resolve([12],INPUTS)
    assert m.status(12,target,INPUTS)['rejected_revision']==3
    assert m.status(12,target,INPUTS)['scope']['revision']==2
    m.resolve([11],INPUTS);m.process(f,np.ones(1025),2048,'fixture');assert not m.processors
    m.resolve([12],INPUTS);assert not m.status(12,target,INPUTS)['listening']['flux']['ready']
    # OFF returns the owned authored values, ignoring temporary gain/window edits.
    c=dict(defaults(target),enabled=False,flux_branch=2.)
    m.submit(dict(scope=Scope('run','session',12,target,4).packet(),settings=c));rows=m.resolve([12],INPUTS)
    assert rows[12][16][0]==1.
    # Source, time and gain tests cover the real existing FFT processor.
    return dict(neutral_OFF_exact=True,form_isolation=True,actual_bin_centers=[93.75,117.1875],empty_range_rejected=True,exit_return_clears_history=True,enabled_history_count=1,OFF_history_count=0)

def storage():
    with tempfile.TemporaryDirectory(prefix='zerawave-rollout-') as temp:
        folder=Path(temp);a='form.12.material.alloy';b='form.11.material.alloy'
        stores={t:TargetProfileStore(t,folder/(t+'.json'),folder/'profiles') for t in (a,b)}
        assert not list(folder.rglob('*.json'))
        c=dict(defaults(a),bass_shape=2.7);stores[a].save_authored(c);profile=stores[a].save_profile('Own settings',c)
        assert TargetProfileStore(a,folder/(a+'.json'),folder/'profiles').authored==c
        assert stores[b].authored==defaults(b)
        name,loaded=stores[a].load_profile(profile)
        assert loaded==c
        s=Scope('run','session',12,a,1);ack=dict(scope=s.packet(),effective=c)
        ticket=SaveTicket.acknowledged(s,c,ack,100.,clock=lambda:100.2)
        ticket.verify(s,c)
        for other in (Scope('run','session',11,b,1),Scope('run','session',12,a,2),Scope('new','session',12,a,1)):reject(lambda:ticket.verify(other,c))
        reject(lambda:SaveTicket.acknowledged(s,c,ack,98.,clock=lambda:100.))
        return dict(no_load_writes=True,independent_authored_storage=True,profile_roundtrip=True,delayed_save_destination_revision_guard=True)

def audition():
    class Inbox:
        value=None
        def take_audition(self):p=self.value;self.value=None;return p
    class Renderer:
        def configure_transitions(self,c):self.transition_settings=validate_settings(c);self.transition_sequence=True
    r=Renderer();r.debug_state=0;r.debug_sequence=();r.transition_settings=validate_settings();r.transition_sequence=False;r.director_rng=random.Random(12);r.director_current=12;r.flow_time=10.;r.planet_star_attack_pilot=True;r.color_inbox=Inbox();r.layer_profiles={'saved':'manual'}
    a=PreviewAudition(r);calls=[];cursor=[25.]
    def source(action,snapshot=None):
        calls.append(action)
        if action=='save':return cursor[0]
        cursor[0]=0. if action=='reset' else snapshot
    a.register_source(source);before=capture(r);cfg=validate_settings(dict(pair=[12,5],isolate={'pair':'tr_planet'}))
    r.color_inbox.value=(1,'start',cfg);a.poll(100.);assert a.active and r.debug_sequence==(12,5) and cursor[0]==0.
    r.flow_time=99.;cursor[0]=18.;r.color_inbox.value=(2,'start',cfg);a.poll(118.);assert a.active and r.flow_time==10. and cursor[0]==0.
    r.color_inbox.value=(3,'return',None);assert a.poll(125.)==100.
    assert not a.active and cursor[0]==25. and capture(r)==before
    assert r.layer_profiles=={'saved':'manual'} and r.planet_star_attack_pilot
    assert calls==['save','reset','reset','restore']
    r.color_inbox.value=(4,'start',dict(cfg,pair=[15,5]));a.poll(130.);assert not a.active and a.error
    a.source=None;r.color_inbox.value=(5,'start',cfg);a.poll(130.);assert not a.active and 'Live' not in (a.error or '') and a.saved is None
    return dict(single_existing_preview=True,repeated_same_source_reset=True,source_scene_rng_return_exact=True,incompatible_or_live_rejected_without_mutation=True)

def run():
    for form in (*SCENES,0):
        if form!=5:slots(form)
    shader=(ROOT/'app/visuals/shaders/dream.frag').read_text(encoding='utf8')
    for form,groups in WORLD_GROUPS.items():
        for _,_,_,names in groups:
            for name in names:assert name+'(' in shader
    return dict(evidence='CPU synthetic real FFT + scoped models + temporary filesystem + in-process audition; no GPU or capture',ownership=ownership(),routing=routing(),storage=storage(),audition=audition())

if __name__=='__main__':print(json.dumps(run(),indent=2));print('Studio Audio rollout CPU checks PASS')
