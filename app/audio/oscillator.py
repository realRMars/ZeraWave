"""Deterministic engine-owned PCM source. No capture, device or visual ownership."""
from dataclasses import dataclass, asdict, replace
import math,time
import numpy as np

RATE=48000
@dataclass(frozen=True)
class OscillatorConfig:
    frequency: float=2.4
    amplitude: float=.35
    waveform: str='sine'
    phase: float=0.
    sweep_end: float=2.4
    sweep_seconds: float=0.
    sweep_log: bool=False

def config(data=None):
    c=OscillatorConfig(**(data or {}))
    for key,low,high in (('frequency',.2,8000.),('amplitude',0.,.8),('phase',-math.tau*100,math.tau*100),('sweep_end',.2,8000.),('sweep_seconds',0.,600.)):
        v=getattr(c,key)
        if not isinstance(v,(float,int)) or not math.isfinite(v) or not low<=v<=high:raise ValueError('Invalid oscillator '+key)
    if c.waveform not in ('sine','triangle','square','saw') or type(c.sweep_log) is not bool:raise ValueError('Invalid oscillator waveform/sweep')
    return c

class Oscillator:
    version='pcm-oscillator-1'
    def __init__(self,data=None):self.settings=config(data);self.reset()
    def reset(self):
        self.index=0;self.epoch=0;self.origin=self.settings.phase;self.paused=False
        self.amp_origin=0.;self.amp_epoch=0;self.old_wave=self.settings.waveform;self.wave_epoch=-RATE
        self.phase_shift=0.;self.phase_target=0.;self.phase_epoch=0
    def frequency_at(self,indices):
        c=self.settings;t=np.maximum(0.,(np.asarray(indices)-self.epoch)/RATE)
        u=np.minimum(t/max(c.sweep_seconds,1e-12),1.) if c.sweep_seconds else np.zeros_like(t)
        return c.frequency*np.exp(np.log(c.sweep_end/c.frequency)*u) if c.sweep_log else c.frequency+(c.sweep_end-c.frequency)*u
    def phase_at(self,indices):
        c=self.settings;t=np.maximum(0.,(np.asarray(indices)-self.epoch)/RATE);span=c.sweep_seconds
        if span:
            inside=np.minimum(t,span);tail=np.maximum(0.,t-span)
            rate=math.log(c.sweep_end/c.frequency)/span if c.sweep_log else (c.sweep_end-c.frequency)/span
            cycles=c.frequency*np.expm1(rate*inside)/rate if c.sweep_log and abs(rate)>1e-12 else c.frequency*inside+.5*rate*inside**2
            cycles+=c.sweep_end*tail
        else:cycles=c.frequency*t
        shift=self.phase_shift+(self.phase_target-self.phase_shift)*np.clip((np.asarray(indices)-self.phase_epoch)/(RATE*.02),0.,1.)
        return self.origin+math.tau*cycles+shift
    def amplitude_at(self,indices):return self.amp_origin+(self.settings.amplitude-self.amp_origin)*np.clip((np.asarray(indices)-self.amp_epoch)/(RATE*.02),0.,1.)
    def apply(self,data):
        c=config(data);phase=float(self.phase_at(self.index));amp=float(self.amplitude_at(self.index));old=self.settings
        shift=self.phase_shift+(self.phase_target-self.phase_shift)*np.clip((self.index-self.phase_epoch)/(RATE*.02),0.,1.)
        changed=any(getattr(c,k)!=getattr(old,k) for k in ("frequency","sweep_end","sweep_seconds","sweep_log"))
        if changed:self.origin=phase;self.epoch=self.index;shift=0.
        self.phase_shift=shift;self.phase_target=shift+(c.phase-old.phase+math.pi)%math.tau-math.pi;self.phase_epoch=self.index
        self.amp_origin=amp;self.amp_epoch=self.index;self.old_wave=old.waveform;self.wave_epoch=self.index;self.settings=c
    def wave(self,phase,name):
        if name=='sine':return np.sin(phase)
        cap=min(63,int((RATE*.49)/(max(self.settings.frequency,self.settings.sweep_end)+25.)))
        result=np.zeros_like(phase)
        for h in range(1,cap+1):
            if name in ('square','triangle') and h%2==0:continue
            gain=4./math.pi/h if name=='square' else 8./math.pi**2*((-1)**((h-1)//2))/h**2 if name=='triangle' else 2./math.pi*((-1)**(h+1))/h
            result+=gain*np.sin(phase*h)
        return result
    def read(self,count):
        if type(count) is not int or not 0<=count<=2048:raise ValueError('PCM block must be 0..2048 samples')
        if self.paused:return np.zeros(0,dtype=np.float64)
        indices=np.arange(self.index,self.index+count);phase=self.phase_at(indices)
        u=np.clip((indices-self.wave_epoch)/(RATE*.02),0.,1.)
        pcm=self.wave(phase,self.settings.waveform)
        if np.any(u<1.):pcm=pcm*u+self.wave(phase,self.old_wave)*(1.-u)
        pcm*=self.amplitude_at(indices);self.index+=count
        return pcm
    def metadata(self):return dict(version=self.version,sample_index=self.index,sample_rate=RATE,seconds=self.index/RATE,frequency=float(self.frequency_at(self.index)),phase_offset_rate_hz=(self.phase_target-self.phase_shift)/(math.tau*.02) if self.index-self.phase_epoch<RATE*.02 else 0.,phase=float(self.phase_at(self.index)%math.tau),waveform=self.settings.waveform)

class Monitor:
    """Optional bounded output, a consumer of PCM, never the source clock."""
    def __init__(self,backend=None):
        import queue
        self.queue=queue.Queue(maxsize=8);self.backend=backend;self.enabled=False;self.closed=False;self.error='';self.gain=0.;self.target=0.;self.overruns=0;self.underruns=0;self.thread=None
    def enable(self,gain=.02):
        if not 0<=gain<=.05:raise ValueError('Monitor gain must be 0..0.05')
        if self.thread and self.thread.is_alive():return
        self.thread=None
        self.clear_queue();self.gain=0.;self.error=""
        import threading
        self.target=gain;self.enabled=True;self.closed=False
        self.thread=threading.Thread(target=self._run,daemon=True,name='Cymatics optional monitor');self.thread.start()
    def clear_queue(self):
        import queue
        while True:
            try:self.queue.get_nowait()
            except queue.Empty:break
    def submit(self,pcm):
        if not self.enabled:return
        import queue
        try:self.queue.put_nowait(np.array(pcm,dtype=np.float32,copy=True))
        except queue.Full:
            self.overruns+=1
            try:self.queue.get_nowait()
            except queue.Empty:pass
            try:self.queue.put_nowait(np.array(pcm,dtype=np.float32,copy=True))
            except queue.Full:self.overruns+=1
    def limited(self,pcm):
        count=len(pcm);step=1./(RATE*.02)
        gains=self.gain+np.clip(np.arange(1,count+1)*step,0.,1.)*(self.target-self.gain)
        self.gain=float(gains[-1]) if count else self.gain
        return (.05*np.tanh(pcm*gains/.05)).astype(np.float32).reshape(-1,1)
    def _run(self):
        import queue
        try:
            if self.backend is None:
                import soundcard
                speaker=soundcard.default_speaker()
                if speaker is None:raise RuntimeError('No monitor output device')
                manager=speaker.player(samplerate=RATE,channels=1,blocksize=2048)
            else:manager=self.backend()
            with manager as player:
                last=0.
                while not self.closed:
                    try:pcm=self.queue.get(timeout=.05)
                    except queue.Empty:self.underruns+=1;pcm=np.linspace(last,0.,2048)
                    player.play(self.limited(pcm));last=float(pcm[-1]) if len(pcm) else 0.
                self.target=0.;player.play(self.limited(np.full(2048,last)))
        except Exception as exc:self.error=str(exc)
        finally:self.enabled=False
    def drain(self,seconds=.35):
        deadline=time.monotonic()+min(.35,max(0.,seconds))
        while self.enabled and not self.queue.empty() and time.monotonic()<deadline:time.sleep(.005)
    def stop(self):
        self.target=0.;self.closed=True
        if self.thread:self.thread.join(timeout=1.)
        if self.thread and self.thread.is_alive():self.error="Output close pending; do not reopen"
        else:self.thread=None;self.clear_queue()
        self.enabled=False
