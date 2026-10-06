"""Scoped normal-Studio coordination for existing target adapters and FFT feed.

The renderer retains lifecycle/resources; the analyzer retains its single FFT.
Telemetry describes CPU submissions, never inferred pixel output.
"""
from copy import deepcopy
import json,os,time
from audio_scope import Scope,endpoints
from audio_controls import TARGETS,form_targets,validate_target
from form_audio_tuning import FormAudioTuning
from star_tuning_profiles import TargetProfileStore,TARGET as STAR
from artifacts_audio_tuning import TARGET as ART
from planet_audio_tuning import SPECS
from development_forms import INSPECTION_FORMS
from transition_catalog import compatible

PREFIX='ZERAWAVE_AUDIO '
MAX_PACKET=131072

def configure(renderer,analyzer):
    run,session=os.environ.get('ZERAWAVE_AUDIO_RUN'),os.environ.get('ZERAWAVE_AUDIO_SESSION')
    if not run or not session or renderer.debug_state in (37,38,39,40):return None
    if renderer.color_inbox is None or renderer.color_inbox.audio_mailbox is None:return None
    stores={target:TargetProfileStore(target) for target in TARGETS}
    model=FormAudioTuning(run,session,{t:s.authored for t,s in stores.items()})
    owner=StudioAudio(renderer,run,session,model);renderer.studio_audio=owner
    analyzer._form_listening=model
    analyzer.preview_waveform=(lambda:owner.visible) if os.environ.get('ZERAWAVE_WORKSPACE_HOST') else False
    return owner

def decode(text,run,session):
    if len(text.encode('utf8'))>MAX_PACKET:return None
    try:
        p=json.loads(text)
        if p.get('version')!=2 or p.get('identity')!=dict(run=run,session=session):return None
        for target,row in p.get('audio_targets',{}).items():
            s=Scope.read(row.get('scope'))
            if (s.run,s.session)!=(run,session) or s.target!=target:return None
            for key in ('settings','effective','authored'):validate_target(s.form,s.target,row[key])
        return p
    except (ValueError,TypeError,KeyError,RecursionError):return None

class StudioAudio:
    def __init__(self,renderer,run,session,model,clock=time.perf_counter):
        self.renderer,self.run,self.session,self.model,self.clock=renderer,run,session,model,clock
        self.view_form=5;self.view_target=STAR;self.pin=False;self.visible=False;self.last=-1000.
        self.endpoint=dict(active=[],primary=None,outgoing=None,incoming=None,progress=0.,recipe=None)
        self.rows={};self.inputs={};self.rejections={};self.mode=0
        self.history_owner=None
        self.audio=None;self.audio_at=None;self.audio_frames=0
        from studio_audition import PreviewAudition
        self.audition=PreviewAudition(renderer)
        self.last_audition_ack=-1
        self.contributions={};self.dependency_notes={}
        self.source_mode='UNSPECIFIED';self.source_identity=''
        self.report_pending={}

    def availability(self,mode,mask,materials,new_materials,echo,spatials,envelopers,shooting,failed,dependencies=None):
        # Availability is monitor metadata. Recompute at its snapshot cadence,
        # never at the render cadence; command processing/ACKs remain per frame.
        from planet_audio_tuning import contribution_state
        shared=contribution_state(mode,mask,materials,new_materials,echo,spatials,envelopers,shooting,failed)
        self.contributions={};self.dependency_notes={}
        for target,p in TARGETS.items():
            active=p['form'] in self.endpoint['active']
            if p['form']==0:
                current=self.renderer.state_at(getattr(self,'seconds',0.))==0
                if target=='transition.director':
                    active=current and not self.renderer.transition_sequence
                else:
                    recipe=self.renderer.director_recipe
                    outgoing,incoming=self.endpoint['outgoing'],self.endpoint['incoming']
                    # Main holds have no recipe; validate before forming its target ID.
                    valid=(isinstance(recipe,str) and type(outgoing) is int and type(incoming) is int
                           and compatible(recipe,outgoing,incoming))
                    active=current and valid and target=='transition.'+recipe
            dependency=p.get('shared')
            if dependency:
                active=active and shared[dependency]
                if p.get('kind')=='CPU submission':active=active and p['form']==self.endpoint['primary']
            elif '.material.artifacts' in target:active=active and materials[0]>0.
            if dependencies and target in dependencies:active=active and dependencies[target]
            self.contributions[target]=active
            self.dependency_notes[target]=p.get('dependency',p.get('scope',''))
        self.contributions.update({t:5 in self.endpoint['active'] and on for t,on in shared.items()})
        self.contributions[ART]=5 in self.endpoint['active'] and materials[0]>0.
        from preview_layers import BITS
        self.contributions[STAR]=5 in self.endpoint['active'] and (mode==0 or bool(mask & BITS['stars']))

    def observe(self,frame,count,stamp=None):
        if not self.visible:return
        self.audio_frames+=1;self.audio_at=self.clock() if stamp is None else stamp
        self.audio=dict(legacy={key:float(getattr(frame,key)) for key in ('bass','mids','highs','flux','bass_onset','mids_onset','highs_onset','tempo','beat_confidence')},
            band12=deepcopy(getattr(frame,'band12',None)),descriptors=deepcopy(getattr(frame,'descriptors',None)),frame=self.audio_frames,
            waveform=deepcopy(getattr(frame,'preview_waveform',None)))

    def prepare(self,seconds):
        r=self.renderer;self.seconds=seconds;self.endpoint=endpoints(r,seconds)
        view=r.color_inbox.take_audio_view()
        if view is not None:
            s,self.pin,self.visible=view;self.view_form,self.view_target=s.form,s.target
            r.star_spectrum.enable(self.visible)
        for s,c,a in r.color_inbox.take_audio():
            try:
                if s.form!=5:
                    message=dict(scope=s.packet(),settings=c)
                    if a is not None:message['authored']=a
                    accepted=self.model.submit(message)
                elif s.target==STAR:accepted=r.star_tuning.submit(s.revision,c,a)
                elif s.target==ART:accepted=r.artifact_tuning.submit(s.revision,c,a)
                else:accepted=r.planet_audio_tuning.submit(s.target,s.revision,c,a)
                if accepted is not False:self.report_pending[s.target]=s
            except ValueError as exc:self.rejections[(s.form,s.target)]=(s.revision,str(exc))
        if not self.pin and self.endpoint['primary'] is not None and self.endpoint['primary']!=self.view_form:
            self.view_form=self.endpoint['primary'];choices=form_targets(self.view_form)
            self.view_target=choices[0] if choices else None

    def report_applied_edits(self,seconds):
        performance=getattr(self.renderer,'performance',None)
        if performance is None:return
        r=self.renderer
        for target,scope in list(self.report_pending.items()):
            adapter=self.model if scope.form!=5 else r.star_tuning if target==STAR else r.artifact_tuning if target==ART else r.planet_audio_tuning
            with adapter.lock:
                state=adapter.state[target] if scope.form!=5 or target not in (STAR,ART) else vars(adapter)
                state={key:deepcopy(state.get(key)) for key in ('revision','settings','authored','rejected_revision')}
            revision=state['revision']
            if revision==scope.revision:
                performance.record_applied_edit('audio',scope.packet(),state['settings'],seconds,state['authored'])
                del self.report_pending[target]
            elif revision>scope.revision or state.get('rejected_revision')==scope.revision:
                del self.report_pending[target]

    def resolve(self,inputs,delta,rewound,mode):
        self.inputs=dict(inputs);self.mode=mode
        transition_active=[0] if self.renderer.state_at(getattr(self,'seconds',0.))==0 else []
        self.rows=self.model.resolve(self.endpoint['active']+transition_active,inputs,delta,rewound,mode)
        ids=(self.endpoint['active']+[0,0])[:2]
        neutral=[(1.,1.,1.,1.)]*32
        return tuple(ids),self.rows.get(ids[0],neutral),self.rows.get(ids[1],neutral)

    def shared_gains(self,suffix):
        form=self.endpoint['primary']
        if form==5:return self.renderer.planet_audio_tuning.packed_gains('planet.'+suffix,True)
        return self.model.packed_gains(form,suffix)

    def guard_history(self,rewound=False):
        # These effects are authored on the final composition. They have one
        # explicit owner (primary endpoint plus pair), not hidden per-row copies.
        owner=(self.endpoint['primary'],tuple(self.endpoint['active']))
        if rewound or owner!=self.history_owner:
            r=self.renderer
            if getattr(r,'echo_resources',None) is not None:
                for fbo in r.echo_resources[1]:fbo.clear()
                r.echo_last_time=None;r.echo_clock=r.echo_remainder=0.
            if getattr(r,'enveloper_stage',None) is not None:r.enveloper_stage.reset()
            if 5 not in self.endpoint['active']:r.reset_planet_star_attack();r.reset_planet_dsp()
            self.history_owner=owner

    def snapshot(self,seconds):
        if not self.snapshot_due():return None
        self.last_audition_ack=self.audition.revision
        self.last=self.clock();r=self.renderer;target=self.view_target;rows={}
        active=5 in self.endpoint['active']
        if target in TARGETS:
            rows[target]=self.model.status(self.view_form,target,self.inputs)
            if self.view_form==0:rows[target]['active']=r.state_at(seconds)==0 and (target=='transition.director' and not r.transition_sequence or target=='transition.'+str(r.director_recipe) and r.director_target is not None)
        elif self.view_form==5 and target:
            if target==STAR:
                from band_attack_tuning import effective
                with r.star_tuning.lock:
                    row=dict(settings=deepcopy(r.star_tuning.settings),authored=deepcopy(r.star_tuning.authored),effective=deepcopy(effective(r.star_tuning.settings,r.star_tuning.authored)),revision=r.star_tuning.revision,error=r.star_tuning.error,rejected_revision=r.star_tuning.rejected_revision)
                    if r.star_tuning.latest is not None:row.update(deepcopy(r.star_tuning.latest))
                row.update(pilot_active=r.planet_star_attack_eligible(),presentation_active=active,active=active,
                    listening=r.planet_audio_tuning.listening[STAR].details(row['effective'],('flux','sparkle','impact'),active),
                    scope_note='Planet sky; independent mapped sky clock; flight resets on exit/return.',state='normal Studio Planet sky')
            elif target==ART:
                row=r.artifact_tuning.status(active,tuple(self.inputs[k] for k in ('flux','impact','sparkle')),seconds,
                    r.star_spectrum.meta is not None,bass=self.inputs['bass'])
                row['scope_note']='Living Artifacts local contributions; only while material contributes.'
            else:
                row=r.planet_audio_tuning.status(active,self.inputs,self.mode)[target]
                row['scope_note']=row.pop('scope')
                gains=r.planet_audio_tuning.packed_gains(target,active)
                row['submissions']={role['key']:dict(source=role['source'],input=row.get('local_inputs',{}).get(role['source'],self.inputs.get(role['source'],0.)),gain=row['effective'][role['key']],slot=gains[i],consumer='Existing '+target+' role '+role['key'],scope='CPU uniform input; GPU shading has not been read back.') for i,role in enumerate(SPECS[target])}
            row.update(scope=Scope(self.run,self.session,5,target,row['revision']).packet(),rendered_wall=self.clock(),available=True)
            rows[target]=row
        rejection=self.rejections.get((self.view_form,target))
        if rejection and target in rows:rows[target].update(rejected_revision=rejection[0],error=rejection[1])
        if target in rows:
            row=rows[target]
            row['contributing']=row['active'] and self.contributions.get(target,True)
            row['dependency']=self.dependency_notes.get(target,row.get('scope_note',''))
            row['availability_note']='CPU selection/weight/endpoint eligibility; a contributing target may still have no visible pixels. Shared final-composition history follows the primary endpoint.'
        spectrum=r.star_spectrum.snapshot()
        return dict(version=2,identity=dict(run=self.run,session=self.session),endpoints=deepcopy(self.endpoint),
            source_mode=self.source_mode,source_identity=self.source_identity,
            editing_form=self.view_form,editing_target=target,pin=self.pin,audio_targets=rows,spectrum=spectrum,
            rendered_wall=self.clock(),seconds=seconds,
            audio=deepcopy(self.audio),audio_age_seconds=None if self.audio_at is None else max(0.,self.clock()-self.audio_at),
            director=dict(current=r.director_current,target=r.director_target,reason=(r.director_history[-1].get('reason') if r.director_history else None),pending=r.director_pending,fast=r.director_fast,slow=r.director_slow,min_hold=r.director_min_hold,max_hold=r.director_max_hold,duration=r.director_duration,beat_tick=r.parameters.beat_tick,beat_confidence=r.parameters.beat_confidence),
            shared_owner=self.history_owner,
            audition=self.audition.status(),
            evidence='Current analyzer spectrum + CPU consumer submissions. No GPU readback or pixel inference.')

    def snapshot_due(self):
        return (self.visible or self.audition.revision!=self.last_audition_ack) and self.clock()-self.last>=.2
