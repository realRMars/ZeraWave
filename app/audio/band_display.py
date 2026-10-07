"""Additive display-only band energy; legacy artistic FFT metrics stay intact."""
import numpy as np
from frequency_bands import DEFAULT_EDGES

def power_spectrum(pcm, window):
    count=len(pcm)
    fft=np.fft.rfft(pcm*window[:,None],axis=0)
    power=np.mean(np.abs(fft)**2,axis=1)*2/(count*np.sum(window**2))
    power[0]*=.5
    if count%2==0:power[-1]*=.5
    return power


class AnalyzerSpectrum:
    """Display-only dual-resolution PCM spectrum; no engine normalization.

    An 8192-frame window improves bass/narrow-band detail; a 2048-frame
    window for broad upper bands retains fast response. Fractional bin overlap integrates
    narrow bands without artificial empty-bin gaps. Such bands are estimates,
    not independent resolved measurements or certified octave filters.
    """
    capacity=8192
    def __init__(self):self.cache={};self.reset()
    def reset(self):self.buffer=None;self.position=0;self.count=0;self.rate=None
    def append(self,samples,samplerate=48000):
        pcm=np.asarray(samples,dtype=float)
        if pcm.ndim==1:pcm=pcm[:,None]
        if pcm.ndim!=2 or not 1<=len(pcm)<=2048 or not 1<=pcm.shape[1]<=16 or not np.isfinite(pcm).all():raise ValueError('Spectrum needs 1..2048 finite PCM frames.')
        if not np.isfinite(samplerate) or samplerate<=0:raise ValueError('Invalid spectrum sample rate.')
        if self.buffer is None or self.rate!=samplerate or self.buffer.shape[1]!=pcm.shape[1]:
            self.reset();self.buffer=np.zeros((self.capacity,pcm.shape[1]));self.rate=samplerate
        end=self.position+len(pcm);first=min(len(pcm),self.capacity-self.position)
        self.buffer[self.position:self.position+first]=pcm[:first]
        if first<len(pcm):self.buffer[:len(pcm)-first]=pcm[first:]
        self.position=end%self.capacity;self.count=min(self.capacity,self.count+len(pcm))
    def latest(self,count):
        start=(self.position-count)%self.capacity
        if start+count<=self.capacity:return self.buffer[start:start+count]
        return np.concatenate((self.buffer[start:],self.buffer[:self.position]))
    def geometry(self,count):
        key=(count,self.rate)
        if key not in self.cache:
            spacing=self.rate/count;frequencies=np.fft.rfftfreq(count,1/self.rate)
            lower=np.maximum(0,frequencies-spacing/2);upper=np.minimum(self.rate/2,frequencies+spacing/2)
            widths=np.maximum(upper-lower,1e-12);groups={}
            for size in (31,63):
                if size==31:
                    centers=1000*10.**(np.arange(-17,14)/10.)
                    edges=np.r_[20.,np.sqrt(centers[:-1]*centers[1:]),20000.]
                else:
                    edges=np.geomspace(20.,20000.,size+1);centers=np.sqrt(edges[:-1]*edges[1:])
                band_indices=[];bin_indices=[];fractions=[];bins=[]
                for index,(lo,hi) in enumerate(zip(edges,edges[1:])):
                    weights=np.maximum(0,np.minimum(hi,upper)-np.maximum(lo,lower))/widths
                    selected=np.flatnonzero(weights)
                    band_indices.extend([index]*len(selected));bin_indices.extend(selected);fractions.extend(weights[selected])
                    bins.append(int(np.count_nonzero((frequencies>=lo)&(frequencies<hi))))
                groups[str(size)]=dict(edges=edges.tolist(),centers=centers.tolist(),bins=bins,
                    unresolved=((np.asarray(bins)<2)|(np.diff(edges)<2*spacing)).tolist(),
                    band_indices=np.asarray(band_indices,dtype=np.intp),bin_indices=np.asarray(bin_indices,dtype=np.intp),fractions=np.asarray(fractions))
            self.cache[key]=(np.hanning(count) if count>2 else np.ones(count),groups)
            while len(self.cache)>8:self.cache.pop(next(iter(self.cache)))
        return self.cache[key]
    def transform(self,pcm):
        window,geometry=self.geometry(len(pcm));power=power_spectrum(pcm,window);output={}
        for key,group in geometry.items():
            energy=np.bincount(group['band_indices'],weights=power[group['bin_indices']]*group['fractions'],minlength=int(key))
            output[key]={name:group[name] for name in ('edges','centers','bins','unresolved')};output[key]['power']=energy.tolist()
        return output
    def snapshot(self):
        if not self.count:raise ValueError('No PCM for spectrum.')
        high_count=min(2048,self.count);high=self.transform(self.latest(high_count))
        low=high if high_count==self.count else self.transform(self.latest(self.count))
        output={}
        for key,group in high.items():
            # Avoid switching windows in the middle of a narrow Hann main
            # lobe. Broad upper groups can use the short, responsive window.
            use_low=(np.asarray(group['centers'])<250)|(np.diff(group['edges'])<4*self.rate/high_count)
            output[key]=dict(edges=group['edges'],centers=group['centers'])
            for field in ('power','bins','unresolved'):
                output[key][field]=[low[key][field][i] if selected else group[field][i] for i,selected in enumerate(use_low)]
            output[key]['resolution_hz']=[self.rate/self.count if selected else self.rate/high_count for selected in use_low]
        return dict(version=2,groups=output,resolution_hz=self.rate/high_count,low_resolution_hz=self.rate/self.count,
            frames=high_count,low_frames=self.count,samplerate=self.rate,range_hz=[20.,20000.],
            units='Channel-mean RMS dBFS; Hann energy correction; fractional-bin band estimates; source PCM before output gain/mute')
    def summarize(self,samples,samplerate=48000):self.append(samples,samplerate);return self.snapshot()

class BandDisplay:
    def __init__(self):self.levels=np.zeros(12)
    def summarize(self, samples, samplerate=48000):
        pcm=np.asarray(samples,dtype=float)
        if pcm.ndim==1:pcm=pcm[:,None]
        count=len(pcm)
        if count<1 or not np.isfinite(pcm).all():raise ValueError('Display needs finite PCM with at least one frame.')
        window=np.hanning(count) if count>2 else np.ones(count)
        power=power_spectrum(pcm,window)
        frequencies=np.fft.rfftfreq(count,1/samplerate)
        rms=np.array([np.sqrt(np.sum(power[(frequencies>=lo)&(frequencies<hi)])) for lo,hi in zip(DEFAULT_EDGES,DEFAULT_EDGES[1:])])
        dbfs=20*np.log10(np.maximum(rms,1e-12))
        normalized=np.clip((dbfs+60)/60,0,1)
        times=np.where(normalized>self.levels,.05,.30)
        self.levels+=(normalized-self.levels)*(-np.expm1(-(count/samplerate)/times))
        bins=[int(np.sum((frequencies>=lo)&(frequencies<hi))) for lo,hi in zip(DEFAULT_EDGES,DEFAULT_EDGES[1:])]
        return dict(rms=rms.tolist(),dbfs=dbfs.tolist(),normalized=normalized.tolist(),levels=self.levels.tolist(),floor_dbfs=-60.,ceiling_dbfs=0.,bins=bins,
            unresolved=[n<2 or hi-lo<2*samplerate/count for n,lo,hi in zip(bins,DEFAULT_EDGES,DEFAULT_EDGES[1:])],
            units='channel-mean band power RMS dBFS; Hann energy correction; -60..0 dBFS display')
