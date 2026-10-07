"""Form-local settings and existing-FFT inputs for the normal Studio dialog."""
from copy import deepcopy
import threading,time
from audio_controls import TARGETS,targets,defaults,windows,validate,slots
from audio_scope import Scope,ScopeMailbox
from spectral_listening import listening_choices,require_listening_bins,SpectralListening
from planet_listening import ListeningState,derived,INGREDIENTS,pack_input

UNIFORM_ROWS=32

class FormAudioTuning:
    def __init__(self,run,session,authored=None,clock=time.perf_counter):
        self.run,self.session,self.clock=run,session,clock;self.lock=threading.Lock()
        self.indices={form:slots(form) for form in {p['form'] for p in TARGETS.values()}}
        self.targets_by_form={form:targets(form) for form in self.indices}
        self.target_windows={target:windows(target) for target in TARGETS}
        self.frequencies=None
        self.mailbox=ScopeMailbox(run,session,validate);self.active=set();self.state={};self.selected={};self.packed={}
        self.listening={target:ListeningState(clock) for target in TARGETS}
        for target,p in TARGETS.items():
            c=validate(p['form'],target,(authored or {}).get(target,defaults(target)))
            self.state[target]=dict(authored=c,settings=dict(c,enabled=False),revision=0,error=None,rejected_revision=None)
        self.processors={};self.mode=0;self.raw_waveform=False

    def analysis_settings(self,target):
        with self.lock:
            p=self.state[target];c=p['settings'] if p['settings']['enabled'] else p['authored']
            choices=listening_choices(c,self.target_windows[target])
            if TARGETS[target]['form'] not in self.active:choices={name:(False,)+spec[1:] for name,spec in choices.items()}
            return p['revision'],choices

    def process(self,f,m,count,source):
        import numpy as np
        f=np.asarray(f);m=np.asarray(m)
        if not 2<=count<=2048 or len(f)!=count//2+1 or len(m)!=len(f) or not np.isfinite(m).all() or np.any(m<0) or not np.allclose(f,np.arange(len(f))*48000/count,rtol=0.,atol=1e-8):raise ValueError('Invalid listening FFT metadata')
        with self.lock:
            self.frequencies=tuple(float(v) for v in f);config={}
            for form in self.active:
                for target in self.targets_by_form.get(form,()):
                    p=self.state[target];c=p['settings'] if p['settings']['enabled'] else p['authored'];choices=listening_choices(c,self.target_windows[target])
                    if any(v[0] for v in choices.values()):config[target]=(p['revision'],choices)
        # Only enabled windows on contributing endpoints allocate histories.
        # OFF targets cost no per-window FFT scan; exit destroys their state.
        for target in tuple(self.processors):
            if target not in config:del self.processors[target]
        result={}
        for target,spec in config.items():
            processor=self.processors.get(target)
            if processor is None:
                processor=SpectralListening(lambda:None);self.processors[target]=processor
            processor.configuration=lambda s=spec:s
            result[target]=processor.process(f,m,count,source,_validated=True)
        return result

    def observe(self,payload):
        with self.lock:
            for target in {t for form in self.active for t in self.targets_by_form.get(form,())}:self.listening[target].observe((payload or {}).get(target))

    def submit(self,message):
        with self.lock:return self.mailbox.accept(message)

    def resolve(self,active,inputs,delta=0.,rewound=False,mode=0,raw_waveform=False):
        with self.lock:
            self.raw_waveform=raw_waveform;prior=self.active;self.active=set(active);self.mode=mode;legacy=derived(inputs)
            for form in prior-self.active:
                for target in self.targets_by_form.get(form,()):self.listening[target]=ListeningState(self.clock);self.selected.pop(target,None);self.packed.pop(target,None)
            for scope,c,a in self.mailbox.take():
                p=self.state[scope.target]
                try:
                    require_listening_bins(c,self.target_windows[scope.target],self.frequencies)
                    if a is not None:require_listening_bins(a,self.target_windows[scope.target],self.frequencies)
                except ValueError as exc:
                    p.update(error=str(exc),rejected_revision=scope.revision);continue
                if a is not None:p['authored']=a
                p.update(settings=c if c['enabled'] else dict(p['authored'],enabled=False),revision=scope.revision,error=None,rejected_revision=None)
            arrays={form:[1.]*128 for form in active}
            for target in (t for form in self.active for t in self.targets_by_form.get(form,())):
                p=self.state[target]
                form=TARGETS[target]['form'];on=form in self.active;c=p['settings'] if p['settings']['enabled'] else p['authored']
                if rewound:self.listening[target].reset_impact()
                local,details=self.listening[target].select(c,self.target_windows[target],legacy,on,delta)
                if raw_waveform:local=dict(legacy)
                self.selected[target]=local;packed=[]
                for r in TARGETS[target]['roles']:
                    if r['source']=='timer':packed.append(c[r['key']]);continue
                    from planet_audio_tuning import role_active
                    enabled=role_active(dict(modes=r.get('modes','all')),mode)
                    gain=c[r['key']] if on and enabled and not raw_waveform else 1.;source=r['source']
                    slot=pack_input(local.get(source,0.),gain) if on and enabled and not raw_waveform and any(details[n]['enabled'] for n in INGREDIENTS[source]) else gain
                    packed.append(slot)
                    if on:arrays[form][self.indices[form][(target,r['key'])]]=slot
                self.packed[target]=tuple(packed)
            return {form:[tuple(values[i:i+4]) for i in range(0,128,4)] for form,values in arrays.items()}

    def packed_gains(self,form,suffix):
        target='form.'+str(form)+'.'+suffix
        with self.lock:return self.packed.get(target,(1.,)*len(TARGETS[target]['roles'])) if target in TARGETS else (1.,1.,1.,1.)

    def value(self,form,target,key,legacy):
        from planet_listening import unpack_input
        with self.lock:
            if self.raw_waveform:return legacy
            index=next(i for i,r in enumerate(TARGETS[target]['roles']) if r['key']==key)
            return unpack_input(legacy,self.packed.get(target,(1.,)*len(TARGETS[target]['roles']))[index])

    def effective(self,target):
        with self.lock:
            p=self.state[target];return deepcopy(p['settings'] if p['settings']['enabled'] else p['authored'])

    def status(self,form,target,inputs,available=True):
        from planet_audio_tuning import role_active
        with self.lock:
            p=self.state[target];c=p['settings'] if p['settings']['enabled'] else p['authored'];local=self.selected.get(target,derived(inputs))
            return dict(scope=Scope(self.run,self.session,form,target,p['revision']).packet(),settings=deepcopy(p['settings']),authored=deepcopy(p['authored']),effective=deepcopy(c),
                active=form in self.active,available=bool(available),error=p['error'],rejected_revision=p['rejected_revision'],rendered_wall=self.clock(),
                listening=self.listening[target].details(c,windows(target),form in self.active),inputs=derived(inputs),local_inputs=local,
                role_active={r['key']:r['source']=='timer' or role_active(dict(modes=r.get('modes','all')),self.mode) for r in TARGETS[target]['roles']},
                submissions={r['key']:dict(source=r['source'],input=c[r['key']] if r['source']=='timer' else local.get(r['source'],0.),gain=1. if self.raw_waveform and r['source']!='timer' else c[r['key']],slot=self.packed.get(target,(1.,)*len(TARGETS[target]['roles']))[i],consumer=r['code'],scope=r['scope']) for i,r in enumerate(TARGETS[target]['roles'])})
