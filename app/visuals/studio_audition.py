"""One bounded in-process pair audition, with explicit source save/reset/return.

No capture, renderer, window or queue is created here. The existing preview
registers its decoded-source callback; live input cannot promise a repeatable
passage and therefore rejects a matched audition.
"""
from copy import deepcopy
from transition_catalog import validate_settings,compatible,RECIPES

PREFIXES=('director_','flow_','star_','galaxy_','planet_','echo_','air_','firescape_','blast_','shockwave_','stellar_','_planet_')
EXCLUDE={'planet_dsp','planet_star_flight','planet_audio_tuning','planet_monitor','star_tuning','star_spectrum','echo_resources','echo_parked','enveloper_stage','planet_dsp_pilot','planet_star_attack_pilot','planet_audio_active'}
MODELS=('molten_memory','marsh_response','tower_cadence','mineral_response','planet_dsp','planet_star_flight')
FIELDS=('debug_state','debug_sequence','transition_sequence','transition_settings','blend_values','impact_envelope','last_render_time')

def listening_history(renderer,analyzer,action,snapshot=None):
    """Reset/restore numerical FFT histories without copying controller locks.

    Configuration callbacks and authored/revision state remain at their owners.
    A changed window is re-primed by the existing configuration comparison.
    """
    from spectral_listening import SpectralListening
    from planet_listening import ListeningState
    processors={}
    artifact=getattr(analyzer,'_artifact_listening',None)
    if artifact is not None:processors['artifact']=artifact
    hub=getattr(analyzer,'_planet_listening',None)
    if hub is not None:processors.update(hub.processors)
    planet=getattr(renderer,'planet_audio_tuning',None)
    art=getattr(renderer,'artifact_tuning',None)
    star=getattr(renderer,'star_tuning',None)
    star_keys=('previous','source','cache_key','masks','latest')
    if action=='save':
        return dict(processors={key:deepcopy({k:v for k,v in vars(p).items() if k!='configuration'}) for key,p in processors.items()},
            planet=None if planet is None else deepcopy(planet.listening),
            artifact=None if art is None else deepcopy(art.listening_state),
            star=None if star is None else (star.revision,{key:deepcopy(getattr(star,key)) for key in star_keys}))
    for key,p in processors.items():
        callback=p.configuration
        state=vars(SpectralListening(callback)) if action=='reset' else dict(snapshot['processors'][key],configuration=callback)
        vars(p).clear();vars(p).update(state)
    if planet is not None:
        planet.listening={t:ListeningState(planet.clock) for t in planet.listening} if action=='reset' else snapshot['planet']
        planet.selected.clear();planet.listening_details.clear();planet.packed.clear()
    if art is not None:
        art.listening_state=ListeningState(art.clock) if action=='reset' else snapshot['artifact']
        art.measurement=deepcopy(art.listening_state.measurement);art.selected=None
    if star is not None:
        with star.lock:
            restore_star=action=='restore' and snapshot['star'][0]==star.revision
            for key in star_keys:setattr(star,key,deepcopy(snapshot['star'][1][key]) if restore_star else None)

def listening_history(renderer,analyzer,action,snapshot=None):
    """Reset/restore numerical FFT histories without copying controller locks.

    Configuration callbacks and authored/revision state remain at their owners.
    A changed window is re-primed by the existing configuration comparison.
    """
    from spectral_listening import SpectralListening
    from planet_listening import ListeningState
    processors={}
    artifact=getattr(analyzer,'_artifact_listening',None)
    if artifact is not None:processors['artifact']=artifact
    hub=getattr(analyzer,'_planet_listening',None)
    if hub is not None:processors.update(hub.processors)
    planet=getattr(renderer,'planet_audio_tuning',None)
    art=getattr(renderer,'artifact_tuning',None)
    star=getattr(renderer,'star_tuning',None)
    star_keys=('previous','source','cache_key','masks','latest')
    if action=='save':
        return dict(processors={key:deepcopy({k:v for k,v in vars(p).items() if k!='configuration'}) for key,p in processors.items()},
            planet=None if planet is None else deepcopy(planet.listening),
            artifact=None if art is None else deepcopy(art.listening_state),
            star=None if star is None else (star.revision,{key:deepcopy(getattr(star,key)) for key in star_keys}))
    for key,p in processors.items():
        callback=p.configuration
        state=vars(SpectralListening(callback)) if action=='reset' else dict(snapshot['processors'][key],configuration=callback)
        vars(p).clear();vars(p).update(state)
    if planet is not None:
        planet.listening={t:ListeningState(planet.clock) for t in planet.listening} if action=='reset' else snapshot['planet']
        planet.selected.clear();planet.listening_details.clear();planet.packed.clear()
    if art is not None:
        art.listening_state=ListeningState(art.clock) if action=='reset' else snapshot['artifact']
        art.measurement=deepcopy(art.listening_state.measurement);art.selected=None
    if star is not None:
        with star.lock:
            restore_star=action=='restore' and snapshot['star'][0]==star.revision
            for key in star_keys:setattr(star,key,deepcopy(snapshot['star'][1][key]) if restore_star else None)

def scalar_tree(v):
    if v is None or type(v) in (bool,int,float,str):return True
    if isinstance(v,(tuple,list)):return len(v)<=1024 and all(scalar_tree(x) for x in v)
    return isinstance(v,dict) and len(v)<=1024 and all(scalar_tree(x) for x in v.values())

def capture(renderer):
    state={key:deepcopy(value) for key,value in vars(renderer).items() if key not in EXCLUDE and (key in FIELDS or key.startswith(PREFIXES)) and scalar_tree(value)}
    models={name:deepcopy(vars(getattr(renderer,name))) for name in MODELS if getattr(renderer,name,None) is not None}
    rng=renderer.director_rng.getstate() if hasattr(renderer,'director_rng') else None
    if hasattr(renderer,'fractal_motions'):
        models['fractal_motions']={form:deepcopy(vars(clock)) for form,clock in renderer.fractal_motions.items()}
        models['fractal_visible']=tuple(renderer.fractal_visible)
    return state,models,rng

def restore(renderer,snapshot):
    state,models,rng=snapshot
    for key in tuple(vars(renderer)):
        if key not in EXCLUDE and (key in FIELDS or key.startswith(PREFIXES)) and scalar_tree(vars(renderer)[key]) and key not in state:delattr(renderer,key)
    for key,value in state.items():setattr(renderer,key,deepcopy(value))
    for name in MODELS:
        model=getattr(renderer,name,None)
        if name in models and model is not None:vars(model).clear();vars(model).update(deepcopy(models[name]))
        elif model is not None and hasattr(model,'reset'):model.reset()
    if rng is not None:renderer.director_rng.setstate(rng)
    if 'fractal_motions' in models:
        from fractals import FractalMotion
        renderer.fractal_motions={form:FractalMotion() for form in models['fractal_motions']}
        for form,values in models['fractal_motions'].items():vars(renderer.fractal_motions[form]).update(deepcopy(values))
        renderer.fractal_visible=set(models['fractal_visible'])
    elif hasattr(renderer,'fractal_motions'):
        for clock in renderer.fractal_motions.values():clock.reset()
        renderer.fractal_visible=set()

class PreviewAudition:
    def __init__(self,renderer):
        self.renderer=renderer;self.initial=capture(renderer);self.saved=None;self.source=None;self.source_snapshot=None
        self.active=False;self.config=None;self.error=None;self.revision=0;self.seconds=0.;self.offset=0.;self.started=None;self.trial_started=None

    def register_source(self,source):self.source=source

    def poll(self,raw_seconds):
        command=self.renderer.color_inbox.take_audition()
        if command is not None:
            revision,action,config=command;self.revision=revision;self.error=None
            try:
                if action=='return':self.return_live(raw_seconds)
                else:self.start(config,raw_seconds)
            except (ValueError,RuntimeError,OSError) as exc:
                self.error=str(exc)
                if self.saved is not None:
                    try:self.return_live(raw_seconds)
                    except (ValueError,RuntimeError,OSError) as restore_error:
                        self.error+=' Return failed; original snapshot retained: '+str(restore_error)
        self.seconds=max(0.,raw_seconds-self.trial_started) if self.active else max(0.,raw_seconds-self.offset)
        return self.seconds

    def start(self,config,raw_seconds):
        if getattr(self.renderer,'fractal_only',False):raise ValueError('Stop the Fractals preview and start a Main preview before auditioning a Main pair.')
        if self.source is None:raise ValueError('Matched pair audition requires a decoded Test track or synthetic preview; live capture remains running unchanged.')
        cfg=validate_settings(config);pair=cfg['pair'];key=cfg['isolate'].get('pair')
        if not pair or key not in RECIPES or not compatible(key,*pair):raise ValueError('Choose an explicit compatible recipe and two different Main forms.')
        if self.saved is None:
            snapshot=capture(self.renderer);source_snapshot=self.source('save')
            self.saved=snapshot;self.source_snapshot=source_snapshot;self.started=raw_seconds
        self.source('reset',None);restore(self.renderer,self.initial)
        self.renderer.debug_sequence=tuple(pair);self.renderer.configure_transitions(cfg)
        self.config=cfg;self.active=True;self.seconds=0.;self.trial_started=raw_seconds
        self._reset_shared()

    def return_live(self,raw_seconds):
        if self.saved is None:self.active=False;return
        snapshot,source=self.saved,self.source_snapshot
        # Keep the snapshot until source restoration succeeds, so errors never
        # silently discard the original destination.
        self.source('restore',source);restore(self.renderer,snapshot)
        self.offset+=max(0.,raw_seconds-self.started)
        self.saved=self.source_snapshot=None;self.active=False;self.config=None;self.started=None
        self._reset_shared()

    def _reset_shared(self):
        r=self.renderer
        if getattr(r,'studio_audio',None) is not None:r.studio_audio.history_owner=None
        if getattr(r,'echo_resources',None) is not None:
            for fbo in r.echo_resources[1]:fbo.clear()
        if getattr(r,'enveloper_stage',None) is not None:r.enveloper_stage.reset()

    def status(self):
        return dict(active=self.active,revision=self.revision,error=self.error,pair=None if self.config is None else self.config['pair'],recipe=None if self.config is None else self.config['isolate']['pair'],
            reset='Same existing decoded passage, seed/settings and fresh mapped history per repeat. Single preview process.',
            available=self.source is not None,return_available=self.saved is not None)
