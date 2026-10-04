"""Opt-in selected-bin measurements from a caller's existing bounded FFT.

Independent histories; no capture, FFT, shared normalization or onset edits.
The configuration callback supplies named window choices, not visual mapping.
"""
import numpy as np
from signal_processor import SignalProcessor,VisualSignalConditioner
from onset_detector import OnsetDetector
import math

DEFAULT_RANGES=dict(bass=(20.,250.),movement=(250.,4000.),flux=(0.,24000.),
                    sparkle=(4000.,16000.),impact=(20.,16000.))

def listening_defaults(names):
    result={}
    for name in names:
        low,high=DEFAULT_RANGES[name]
        result.update({name+'_range_enabled':False,name+'_start_hz':low,name+'_end_hz':high})
        if name=='impact':result['impact_sensitivity']=1.
    return result

def listening_bounds(names):
    result={key:(0.,24000.) for key in listening_defaults(names) if key.endswith('_hz')}
    if 'impact' in names:result['impact_sensitivity']=(.5,2.)
    return result

def validate_listening(settings,names):
    for name in names:
        if type(settings[name+'_range_enabled']) is not bool:raise ValueError('Invalid '+name+' range flag')
        low,high=settings[name+'_start_hz'],settings[name+'_end_hz']
        if any(type(v) not in (int,float) or not math.isfinite(v) or not 0.<=v<=24000. for v in (low,high)) or low>=high:
            raise ValueError(name+' Start Hz must be below End Hz in 0..24000')
    if 'impact' in names:
        v=settings['impact_sensitivity']
        if type(v) not in (int,float) or not math.isfinite(v) or not .5<=v<=2.:raise ValueError('Invalid impact sensitivity')

def listening_choices(settings,names):
    return {name:(settings[name+'_range_enabled'],settings[name+'_start_hz'],settings[name+'_end_hz'])+
            ((settings['impact_sensitivity'],) if name=='impact' else ()) for name in names}

def require_listening_bins(settings,names,frequencies):
    validate_listening(settings,names)
    for name in names:
        if settings[name+'_range_enabled'] and (frequencies is None or not any(settings[name+'_start_hz']<=f<settings[name+'_end_hz'] for f in frequencies)):
            raise ValueError(name+' listening window contains no actual FFT bins')


class SpectralListening:
    def __init__(self,configuration):
        self.configuration=configuration;self.source=None;self.grid=None;self.previous=None
        self.specs={};self.processor=SignalProcessor(smoothing=.5)
        self.conditioner=VisualSignalConditioner(quiet_threshold=.06);self.seconds=0.
        self.detectors={}

    def process(self,frequencies,magnitudes,count,source=None,samplerate=48000,_validated=False):
        f=np.asarray(frequencies);m=np.asarray(magnitudes)
        if not 2<=count<=2048 or len(f)!=count//2+1 or len(m)!=len(f):raise ValueError('Invalid listening FFT size')
        if not _validated and (not np.isfinite(m).all() or np.any(m<0) or not np.allclose(f,np.arange(len(f))*samplerate/count,rtol=0.,atol=1e-8)):
            raise ValueError('Invalid listening FFT metadata')
        grid=(count,samplerate)
        if source!=self.source or grid!=self.grid:
            self.source=source;self.grid=grid;self.previous=None;self.specs={};self.seconds=0.
            self.processor=SignalProcessor(smoothing=.5);self.conditioner=VisualSignalConditioner(quiet_threshold=.06)
            self.detectors={}
        revision,choices=self.configuration();channels={};self.seconds+=count/samplerate
        if not any(spec[0] for spec in choices.values()):
            self.previous=None;self.specs=dict(choices)
            return dict(revision=revision,channels={},sample_seconds=self.seconds,source=source,
                sample_count=count,sample_rate=samplerate,bin_spacing_hz=samplerate/count)
        for name,spec in choices.items():
            enabled,low,high=spec[:3];mask=(f>=low)&(f<high);centers=f[mask]
            changed=self.specs.get(name)!=spec
            if changed:
                self.processor.previous.pop(name,None);self.processor.adaptive_history.pop(name,None)
                self.conditioner.values.pop(name,None);self.specs[name]=spec
                self.detectors.pop(name,None)
            raw=level=0.
            if enabled and len(centers):
                if name=='flux':
                    raw=float(np.maximum(0.,m[mask]-self.previous[mask]).sum()) if self.previous is not None else 0.
                    level=self.conditioner.condition(name,self.processor.process_adaptive(name,raw,0.,180.))
                elif name=='sparkle':
                    raw=float(m[mask].mean())
                    level=self.conditioner.condition(name,self.processor.process(name,raw,0.,1.))
                elif name in ('bass','movement','impact'):
                    raw=float(m[mask].mean())
                    processed=(self.processor.process(name,raw,0.,16.) if name=='bass' else
                               self.processor.process_adaptive(name,raw,0.,4.))
                    if name=='impact':
                        detector=self.detectors.setdefault(name,OnsetDetector(threshold=.2/spec[3]))
                        previous=detector.previous
                        if changed:detector.previous=processed
                        level=detector.detect(processed)
                        response=dict(processed=processed,rise=0. if changed else max(0.,processed-previous),
                                      threshold=detector.threshold,primed=not changed,sensitivity=spec[3])
                    else:level=self.conditioner.condition(name,processed)
                else:raise ValueError('Unknown listening measurement')
            channels[name]=dict(spec=list(spec),bins=int(len(centers)),first_hz=float(centers[0]) if len(centers) else None,
                last_hz=float(centers[-1]) if len(centers) else None,raw=raw,level=level)
            if name=='impact' and enabled and len(centers):channels[name]['detector_response']=response
        self.previous=np.array(m,copy=True)
        return dict(revision=revision,channels=channels,sample_seconds=self.seconds,source=source,
            sample_count=count,sample_rate=samplerate,bin_spacing_hz=samplerate/count)


class ListeningHub:
    """Fixed target processors using one caller-supplied FFT; no extra FFT/PCM."""
    def __init__(self,configurations):
        self.processors={target:SpectralListening(callback) for target,callback in configurations.items()}

    def process(self,frequencies,magnitudes,count,source=None,samplerate=48000):
        f=np.asarray(frequencies);m=np.asarray(magnitudes)
        if not 2<=count<=2048 or len(f)!=count//2+1 or len(m)!=len(f) or not np.isfinite(m).all() or np.any(m<0) or not np.allclose(f,np.arange(len(f))*samplerate/count,rtol=0.,atol=1e-8):
            raise ValueError('Invalid listening FFT metadata')
        return {target:processor.process(f,m,count,source,samplerate,_validated=True)
                for target,processor in self.processors.items()}
