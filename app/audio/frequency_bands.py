"""Additive twelve-band summaries from the existing FFT; magnitude, not power."""
import numpy as np
DEFAULT_EDGES=(20.,40.,80.,160.,315.,630.,1250.,2500.,4000.,6300.,10000.,14000.,20000.)
def validate(data=None):
    c=dict(edges=list(DEFAULT_EDGES),gain=1.,floor=.0001,ceiling=.12,attack=.05,release=.30)
    if data:c.update(data)
    if set(c)!=set(('edges','gain','floor','ceiling','attack','release')):raise ValueError('Unknown band setting')
    e=np.asarray(c['edges'],float)
    if e.shape!=(13,) or not np.all(np.isfinite(e)) or e[0]<0 or e[-1]>24000 or np.any(np.diff(e)<=0):raise ValueError('Need13 increasing finite band edges in0..24000Hz')
    for key,low,high in (('gain',0.,16.),('floor',0.,1.),('ceiling',.00001,1.),('attack',.001,5.),('release',.001,10.)):
        if not np.isfinite(c[key]) or not low<=c[key]<=high:raise ValueError('Invalid band '+key)
    if c['ceiling']<=c['floor']:raise ValueError('Band ceiling must exceed floor')
    return c
class FrequencyBands:
    def __init__(self,data=None):self.settings=validate(data);self.levels=np.zeros(12)
    def summarize(self,frequencies,magnitudes,count,samplerate=48000):
        c=self.settings;edges=np.minimum(c['edges'],samplerate/2.);raw=[];bins=[]
        for low,high in zip(edges,edges[1:]):
            selected=(frequencies>=low)&(frequencies<high);bins.append(int(selected.sum()));raw.append(float(np.mean(magnitudes[selected])) if selected.any() else 0.)
        raw=np.array(raw);normalized=np.clip((raw*(2./max(count,1))*c['gain']-c['floor'])/(c['ceiling']-c['floor']),0.,1.)
        times=np.where(normalized>self.levels,c['attack'],c['release']);self.levels+=(normalized-self.levels)*(-np.expm1(-(count/samplerate)/times))
        self.levels=np.where(np.array(bins)>0,self.levels,0.)
        resolution=samplerate/max(count,1)
        return dict(ids=[f'frequency.{i:02}' for i in range(12)],edges=edges.tolist(),raw=raw.tolist(),normalized=normalized.tolist(),levels=self.levels.tolist(),bins=bins,unresolved=[bool(n<2 or b-a<resolution) for n,a,b in zip(bins,edges,edges[1:])],resolution_hz=resolution,units='mean FFT magnitude; normalized by2/N; not physical power')
