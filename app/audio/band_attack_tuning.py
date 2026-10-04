"""Optional bounded FFT attack weights; no PCM, FFT or capture.

The old comparison selects the exact caller-supplied 20-250 Hz mean.
A target may supply its own persisted authored baseline for OFF.
This tunes measurement only, never output filtering.
"""
from collections import deque
from copy import deepcopy
import math
import threading
import time
from spectral_listening import listening_defaults,listening_bounds,validate_listening,listening_choices
STAR_WINDOWS=('flux','sparkle','impact')

BASELINE=dict(enabled=True,low_weight=1.,body_weight=1.,upper_weight=1.,extension=0.,sensitivity=1.)
BOUNDS=dict(low_weight=(0.,2.),body_weight=(0.,2.),upper_weight=(0.,2.),extension=(0.,1.),sensitivity=(.5,2.))
RANGES=((20.,40.),(40.,160.),(160.,250.),(250.,315.))
WINDOW_BASELINE=dict(enabled=True,mode='window',start_hz=20.,end_hz=250.,weight=1.,sensitivity=1.)
WINDOW_BOUNDS=dict(start_hz=(20.,315.),end_hz=(20.,315.),weight=(0.,2.),sensitivity=(.5,2.))
# Pass-through presentation fields. Measurement ignores them; visuals map them.
PRESENTATION_BOUNDS={key:(0.,2.) for key in ('chorus_light','chorus_presence','chorus_twinkle','legacy_wake','flux_clock','sparkle_clock')}

def validate(settings):
    if not isinstance(settings,dict):raise ValueError('Unknown star tuning settings')
    range_keys=set(listening_defaults(STAR_WINDOWS))
    extended=range_keys<=set(settings)
    core=set(settings)-range_keys if extended else set(settings)
    presentation=core==set(WINDOW_BASELINE)|set(PRESENTATION_BOUNDS)
    window=(core==set(WINDOW_BASELINE) or presentation) and settings.get('mode')=='window'
    if not window and set(settings)!=set(BASELINE):raise ValueError('Unknown star tuning settings')
    if type(settings['enabled']) is not bool:raise ValueError('Invalid tuning bypass')
    clean={'enabled':settings['enabled']}
    if window:clean['mode']='window'
    selected=dict(WINDOW_BOUNDS,**PRESENTATION_BOUNDS) if presentation else WINDOW_BOUNDS if window else BOUNDS
    if extended:
        if not presentation or set(settings)!=core|range_keys:raise ValueError('Unknown star listening settings')
        validate_listening(settings,STAR_WINDOWS);selected=dict(selected,**listening_bounds(STAR_WINDOWS))
        clean.update({key:settings[key] for key in range_keys if key.endswith('_enabled')})
    for key,(low,high) in selected.items():
        v=settings[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high:raise ValueError('Invalid '+key)
        clean[key]=float(v)
    if window and clean['start_hz']>=clean['end_hz']:raise ValueError('Start Hz must be below End Hz')
    return clean

def effective(settings,authored=None):return settings if settings['enabled'] else (authored or BASELINE)

def window_settings(settings):
    """Represent legacy coefficients only when they are one contiguous plateau."""
    c=validate(settings)
    if c.get('mode')=='window':return c
    gains=[c['low_weight'],c['body_weight'],c['upper_weight'],c['upper_weight']*c['extension']]
    selected=[i for i,g in enumerate(gains) if g>0.]
    result=dict(WINDOW_BASELINE,enabled=c['enabled'],sensitivity=c['sensitivity'])
    if not selected:return dict(result,weight=0.)
    if selected!=list(range(selected[0],selected[-1]+1)) or len({gains[i] for i in selected})!=1:return None
    return dict(result,start_hz=RANGES[selected[0]][0],end_hz=RANGES[selected[-1]][1],weight=gains[selected[0]])

def curve_weights(frequencies,settings,authored=None):
    """Actual coefficients, one per FFT bin; both legacy and window packets."""
    import numpy as np
    f=np.asarray(frequencies);c=effective(validate(settings),authored);w=np.zeros(len(f))
    if c.get('mode')=='window':
        w[(f>=c['start_hz'])&(f<c['end_hz'])]=c['weight']
    else:
        gains=[c['low_weight'],c['body_weight'],c['upper_weight'],c['upper_weight']*c['extension']]
        for (low,high),gain in zip(RANGES,gains):w[(f>=low)&(f<high)]=gain
    return w

def valid_selection(summary,settings):
    if settings.get('mode')=='window' and settings['start_hz']==20. and settings['end_hz']==250. and settings['weight']==1.:
        return True # Exact reviewed reset remains valid on short/unresolved packets.
    return settings.get('mode')!='window' or any(settings['start_hz']<=f<settings['end_hz'] for f in summary['frequencies'])

def weighted(summary,settings,authored=None):
    c=effective(settings,authored)
    if c.get('mode')=='window':
        if c['start_hz']==20. and c['end_hz']==250. and c['weight']==1.:return summary['baseline']
        denominator=sum(summary['counts'][:3])
        if denominator==0:return 0.
        return float(sum(m*w for m,w in zip(summary['magnitudes'],curve_weights(summary['frequencies'],c)))/denominator)
    if all(c[k]==BASELINE[k] for k in BOUNDS if k!='sensitivity'):return summary['baseline']
    sums=summary['sums'];counts=summary['counts'];denominator=sum(counts[:3])
    if denominator==0:return 0.
    return (sums[0]*c['low_weight']+sums[1]*c['body_weight']+
            sums[2]*c['upper_weight']+sums[3]*c['upper_weight']*c['extension'])/denominator

class BandAttackTuning:
    def __init__(self,clock=time.perf_counter,authored=None):
        self.authored=validate(authored or BASELINE);self.explicit_authored=authored is not None
        initial=dict(self.authored,enabled=False) if self.explicit_authored else dict(BASELINE)
        self.clock=clock;self.lock=threading.Lock();self.pending=(0,initial)
        self.revision=0;self.settings=dict(initial);self.previous=None;self.source=None
        self.cache_key=None;self.masks=None;self.latest=None;self.frames=0;self.positive_packets=0
        self.last_completion=None;self.intervals=deque(maxlen=64);self.control_received=None
        self.apply_received=None;self.last_control_latency=None
        self.peak=0.;self.peak_sample=None;self.last_status=-math.inf;self.last_analysis_seconds=None
        self.interval_positive_packets=0;self.last_accepted_events=0
        self.rejected_revision=None;self.error=None

    def listening_settings(self):
        with self.lock:
            c=dict(listening_defaults(STAR_WINDOWS),**effective(self.settings,self.authored))
            return self.revision,listening_choices(c,STAR_WINDOWS)

    def submit(self,revision,settings,authored=None):
        clean=validate(settings)
        new_authored=None if authored is None else validate(authored)
        if new_authored is not None and (new_authored.get('mode')!='window' or not new_authored['enabled']):
            raise ValueError('Invalid authored baseline')
        if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid tuning revision')
        with self.lock:
            if revision>self.pending[0]:
                candidate_authored=new_authored or self.authored
                if not clean['enabled'] and self.explicit_authored:clean=dict(candidate_authored,enabled=False)
                if self.previous is not None and (not valid_selection(self.previous,effective(clean,candidate_authored)) or
                        (new_authored is not None and not valid_selection(self.previous,new_authored))):
                    self.rejected_revision=revision;self.error='Selected window contains no actual FFT bins';return False
                self.pending=(revision,clean) if new_authored is None else (revision,clean,new_authored)
                self.control_received=self.clock()
                self.rejected_revision=None;self.error=None
        return True

    def measure(self,frame,baseline):
        import numpy as np
        f=frame.spectrum_frequencies;m=frame.spectrum_magnitudes
        key=(len(f),float(f[1]-f[0]) if len(f)>1 else 0.,float(f[-1]) if len(f) else 0.)
        if key!=self.cache_key:
            self.masks=[(f>=low)&(f<high) for low,high in RANGES];self.cache_key=key
        supported=(f>=20.)&(f<315.)
        return dict(baseline=baseline,sums=[float(np.sum(m[mask])) for mask in self.masks],
                    counts=[int(mask.sum()) for mask in self.masks],
                    frequencies=tuple(float(v) for v in f[supported]),magnitudes=tuple(float(v) for v in m[supported]))

    def apply_without_detector(self):
        """Render ACK for pilot-OFF presentation edits; measurement is inactive."""
        with self.lock:
            revision,settings=self.pending[:2]
            self.revision=revision;self.settings=dict(settings)
            if len(self.pending)==3:self.authored=dict(self.pending[2])
            self.latest=None

    def apply(self,frame,baseline,detector,source):
        summary=self.measure(frame,baseline)
        with self.lock:
            revision,settings=self.pending[:2]
            authored=self.pending[2] if len(self.pending)==3 else self.authored
            if (not valid_selection(summary,effective(settings,authored)) or
                    (len(self.pending)==3 and not valid_selection(summary,authored))):
                self.rejected_revision=revision;self.error='Selected window contains no actual FFT bins'
                revision,settings=self.revision,self.settings;authored=self.authored
                self.pending=(revision,dict(settings));self.control_received=None
            changed=revision!=self.revision
            self.revision=revision;self.settings=dict(settings);self.authored=dict(authored)
            self.apply_received=self.control_received if changed else None
            if changed:self.control_received=None
        if changed and self.previous is not None and source==self.source:
            # Re-evaluate the preceding packet under the new weights. A knob
            # movement cannot itself create a false rise. Preserve sample clock.
            detector.previous=weighted(self.previous,settings,self.authored)
        self.previous=summary;self.source=source
        return weighted(summary,settings,self.authored),effective(settings,self.authored)['sensitivity'],summary

    def completed(self,payload,summary):
        now=self.clock()
        with self.lock:
            self.frames+=1
            if self.last_completion is not None:self.intervals.append(max(0.,now-self.last_completion))
            self.last_completion=now
            if self.apply_received is not None:self.last_control_latency=max(0.,now-self.apply_received)*1000.
            strength=payload['bass_attack']
            if strength>=.10:self.positive_packets+=1;self.interval_positive_packets+=1
            if strength>self.peak:self.peak=strength;self.peak_sample=payload['sample_seconds']
            baseline=effective(self.settings,self.authored)==BASELINE or effective(self.settings,self.authored)==WINDOW_BASELINE
            self.latest=dict(revision=self.revision,settings=dict(self.settings),effective=dict(effective(self.settings,self.authored)),authored=dict(self.authored),
                state='authored baseline' if not self.settings['enabled'] and self.explicit_authored else 'tuning bypassed' if not self.settings['enabled'] else 'reviewed baseline' if baseline else 'tuned detector',
                sample_seconds=payload['sample_seconds'],analysis_frames=self.frames,positive_packets=self.positive_packets,
                attack=strength,baseline_level=summary['baseline'],weighted_level=payload['low_band_level'],
                band_means=[total/count if count else 0. for total,count in zip(summary['sums'],summary['counts'])],
                band_bins=summary['counts'],analysis_wall_interval_ms=(self.intervals[-1]*1000.) if self.intervals else None,
                packet_audio_ms=None if self.last_analysis_seconds is None else (payload['sample_seconds']-self.last_analysis_seconds)*1000.,
                applied_wall=now,control_to_analysis_ms=self.last_control_latency)
            self.latest['detector_response']=deepcopy(payload.get('detector_response'))
            self.last_analysis_seconds=payload['sample_seconds']

    def status(self,accepted_events,flight_phase):
        now=self.clock()
        with self.lock:
            if now-self.last_status<.10:return None
            previous_status=self.last_status;self.last_status=now
            data=deepcopy(self.latest) if self.latest else dict(state='waiting for analysis',settings=dict(self.settings),effective=dict(effective(self.settings,self.authored)),authored=dict(self.authored),revision=self.revision)
            data.update(interval_peak=self.peak,peak_sample=self.peak_sample,accepted_events=accepted_events,
                rejected_revision=self.rejected_revision,error=self.error,
                interval_positive_packets=self.interval_positive_packets,
                interval_accepted_events=max(0,accepted_events-self.last_accepted_events),
                flight_phase=flight_phase,analysis_age_seconds=None if self.last_completion is None else max(0.,now-self.last_completion),
                snapshot_wall_interval_ms=None if not math.isfinite(previous_status) else (now-previous_status)*1000.,
                peakhold_window_ms=None if not math.isfinite(previous_status) else (now-previous_status)*1000.,
                analysis_wall_window_ms=list(self.intervals)[-16:])
            self.peak=0.;self.peak_sample=None
            self.interval_positive_packets=0;self.last_accepted_events=accepted_events
            return data

    def reset_view(self,accepted_events):
        # Display bookkeeping only; detector and flight history are untouched.
        with self.lock:
            self.peak=0.;self.peak_sample=None;self.interval_positive_packets=0
            self.last_accepted_events=accepted_events;self.last_status=-math.inf
