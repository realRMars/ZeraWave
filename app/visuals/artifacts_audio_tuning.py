"""Local gains and optional FFT-window inputs for Living Artifacts.

Uses the existing FFT; original analysis, shared clocks and authored bases remain.
"""
from copy import deepcopy
import math
import threading
import time
from spectral_listening import listening_defaults,listening_bounds,validate_listening,listening_choices,require_listening_bins as require_window_bins
from planet_listening import ListeningState,titles as listening_titles

TARGET='planet.material.artifacts'
BASELINE=dict(enabled=True,flux_stretch=1.,impact_facets=1.,sparkle_light=1.)
LEGACY_BASELINE=dict(BASELINE)
BASELINE.update(bass_cells=1.,bass_radial=1.,sparkle_presence=1.)
BOUNDS={key:(0.,2.) for key in BASELINE if key!='enabled'}
GAIN_KEYS=tuple(BOUNDS)
BASELINE.update(flux_range_enabled=False,flux_start_hz=0.,flux_end_hz=24000.)
BASELINE.update(sparkle_range_enabled=False,sparkle_start_hz=4000.,sparkle_end_hz=16000.)
BOUNDS.update(flux_start_hz=(0.,24000.),flux_end_hz=(0.,24000.))
BOUNDS.update(sparkle_start_hz=(0.,24000.),sparkle_end_hz=(0.,24000.))
TITLES=dict(flux_stretch='Flux -> stretch contribution',impact_facets='Impact -> facet contribution',
            sparkle_light='Sparkle -> light contribution',bass_cells='Bass -> artifact cell scale',
            bass_radial='Bass -> local radial displacement',sparkle_presence='Sparkle -> cell presence')
TITLES.update(flux_start_hz='Flux listening start (Hz)',flux_end_hz='Flux listening end (Hz)')
TITLES.update(sparkle_start_hz='Sparkle listening start (Hz)',sparkle_end_hz='Sparkle listening end (Hz)')
PRE_LISTENING_BASELINE=dict(BASELINE)
WINDOWS=('flux','sparkle','bass','impact')
BASELINE.update(listening_defaults(('bass','impact')))
BOUNDS.update(listening_bounds(('bass','impact')))
TITLES.update(listening_titles(('bass','impact')))

def validate(settings):
    if isinstance(settings,dict) and set(settings)==set(LEGACY_BASELINE):settings=dict(BASELINE,**settings)
    if isinstance(settings,dict) and set(settings)==set(PRE_LISTENING_BASELINE):settings=dict(BASELINE,**settings)
    if not isinstance(settings,dict) or set(settings)!=set(BASELINE):raise ValueError('Unknown Living Artifacts settings')
    if type(settings['enabled']) is not bool:raise ValueError('Invalid Living Artifacts override flag')
    clean={'enabled':settings['enabled']}
    for name in WINDOWS:
        key=name+'_range_enabled'
        if type(settings[key]) is not bool:raise ValueError('Invalid '+name+' range flag')
        clean[key]=settings[key]
    for key,(low,high) in BOUNDS.items():
        v=settings[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high:raise ValueError('Invalid '+key)
        clean[key]=float(v)
    validate_listening(clean,WINDOWS)
    for name in WINDOWS:
        if clean[name+'_start_hz']>=clean[name+'_end_hz']:raise ValueError(name+' Start Hz must be below End Hz')
    return clean

def mapped_inputs(inputs,gains):
    """Exact normalized local channel scaling used by the shader branch."""
    return tuple(max(0.,min(1.,value*gain)) for value,gain in zip(inputs,gains))

class ArtifactsAudioTuning:
    def __init__(self,authored=BASELINE,clock=time.perf_counter):
        self.authored=validate(authored);self.settings=dict(self.authored,enabled=False)
        self.clock=clock;self.lock=threading.Lock();self.pending=None;self.revision=0;self.applied_wall=None
        self.measurement=None;self.rejected_revision=None;self.error=None
        self.listening_state=ListeningState(clock);self.selected=None

    @staticmethod
    def choices(c):
        return listening_choices(c,WINDOWS)

    def analysis_settings(self):
        with self.lock:
            c=self.settings if self.settings['enabled'] else self.authored
            return self.revision,self.choices(c)

    def observe(self,payload):
        with self.lock:self.measurement=deepcopy(payload);self.listening_state.observe(payload)

    def submit(self,revision,settings,authored=None):
        c=validate(settings);a=None if authored is None else validate(authored)
        if a is not None and not a['enabled']:raise ValueError('Invalid Living Artifacts authored baseline')
        if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid audio tuning revision')
        with self.lock:
            if revision<=max(self.revision,self.pending[0] if self.pending else -1):return False
            if a is None and self.pending is not None:a=self.pending[2]
            baseline=a or self.authored
            if not c['enabled']:c=dict(baseline,enabled=False)
            if self.measurement is not None:
                n=self.measurement['sample_count'];rate=self.measurement['sample_rate']
                bins=tuple(i*rate/n for i in range(n//2+1))
                try:
                    require_listening_bins(c if c['enabled'] else baseline,bins)
                    if a is not None:require_listening_bins(a,bins)
                except ValueError as exc:
                    self.rejected_revision=revision;self.error=str(exc);return False
            self.rejected_revision=None;self.error=None
            self.pending=(revision,c,a)
        return True

    def resolve(self,active,inputs=None,delta=0.,rewound=False,raw_waveform=False):
        with self.lock:
            self.raw_waveform=raw_waveform
            if rewound:self.listening_state.reset_impact()
            if self.pending is not None:
                self.revision,self.settings,authored=self.pending;self.pending=None
                if authored is not None:self.authored=authored
                self.applied_wall=self.clock()
            c=self.settings if self.settings['enabled'] else self.authored
            self.selected,_=self.listening_state.select(c,WINDOWS,inputs or {},active,delta)
            if raw_waveform:self.selected=dict(inputs or {})
            gains=tuple(c[key] for key in LEGACY_BASELINE if key!='enabled') if active and not raw_waveform else (1.,1.,1.)
            on=active and not raw_waveform and any(c[key]!=1. for key in GAIN_KEYS)
        return int(on),gains

    def shape_gains(self,active):
        with self.lock:
            c=self.settings if self.settings['enabled'] else self.authored
            return tuple(c[key] for key in ('bass_cells','bass_radial','sparkle_presence')) if active and not getattr(self,'raw_waveform',False) else (1.,1.,1.)

    def _listening(self,c,active):
        if getattr(self,'raw_waveform',False):return (0,0,0,0),(0.,0.,0.,0.),self.listening_state.details(c,WINDOWS,active)
        flags=[];values=[]
        details=self.listening_state.details(c,WINDOWS,active)
        for name,row in details.items():
            flag=row['enabled'];ready=row['ready']
            value=(self.selected or {}).get(name,0.) if name=='impact' and self.selected is not None else row['measurement']['level'] if row['measurement'] else 0.
            flags.append(int(flag));values.append(value if flag and ready else 0.)
        return tuple(flags),tuple(values),details

    def listening(self,active):
        with self.lock:
            c=self.settings if self.settings['enabled'] else self.authored
            return self._listening(c,active)[:2]

    def status(self,active,inputs,render_seconds,input_present=False,bass=0.):
        with self.lock:
            c=self.settings if self.settings['enabled'] else self.authored
            gains=tuple(c[key] for key in LEGACY_BASELINE if key!='enabled') if active and not getattr(self,'raw_waveform',False) else (1.,1.,1.)
            flags,values,details=self._listening(c,active)
            selected=(values[0] if flags[0] else inputs[0],values[3] if flags[3] else inputs[1],values[1] if flags[1] else inputs[2])
            local=mapped_inputs(selected,gains)
            shape=tuple(c[key] if active and not getattr(self,'raw_waveform',False) else 1. for key in ('bass_cells','bass_radial','sparkle_presence'))
            presence=max(0.,min(1.,selected[2]*shape[2]));reveal=max(0.,min(1.,(presence-.65)/.35))
            selected_bass=values[2] if flags[2] else bass
            return dict(target=TARGET,version=2,active=bool(active),revision=self.revision,
                rejected_revision=self.rejected_revision,error=self.error,
                settings=deepcopy(self.settings),authored=deepcopy(self.authored),effective=deepcopy(c),
                inputs=dict(zip(('flux','impact','sparkle'),inputs)),local_inputs=dict(zip(('flux','impact','sparkle'),local)),
                listening=details,listening_on=list(flags),listening_inputs=list(values),
                audio_terms=dict(stretch=local[0]*1.2,facets=local[1]*.6,light=local[2]*.55,
                    cell_scale_increment=max(0.,min(1.,selected_bass*shape[0]))*1.6,
                    radial_displacement=max(0.,min(1.,selected_bass*selected_bass*shape[1]))*.25,
                    presence_reveal=reveal*reveal*(3.-2.*reveal)),
                gains=list(gains),shape_gains=list(shape),
                uniform_on=int(active and not getattr(self,'raw_waveform',False) and any(c[key]!=1. for key in GAIN_KEYS)),render_seconds=render_seconds,
                rendered_wall=self.clock(),applied_wall=self.applied_wall,input_present=bool(input_present))


def require_listening_bins(settings,frequencies):
    c=validate(settings)
    require_window_bins(c,WINDOWS,frequencies)
