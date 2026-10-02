"""Forced linear gravity-capillary basin modes, not Faraday or full fluids.

Metres/seconds, ideal impermeable walls and sliding90deg contact-line cosine
basis. Exact sample-held LTI propagation; optical scale is a separate control.
"""
from dataclasses import dataclass,asdict
import math
import numpy as np
RATE=48000
@dataclass(frozen=True)
class BasinConfig:
    width: float=.10
    length: float=.07
    depth: float=.005
    modes: int=24
    viscosity: float=.000001
    damping: float=.35
    wall_loss: float=.25
    excitation: float=.025
    actuator_x: float=.31
    actuator_y: float=.43
    actuator_radius: float=.003
    optical_gain: float=120.
    diagnostic: str='envelope'
    routing_band: int=-1
    routing_strength: float=0.
def validate(data=None):
    c=BasinConfig(**(data or {}))
    for key,a,b in (('width',.025,.5),('length',.025,.5),('depth',.001,.05),('viscosity',.0000001,.0001),('damping',.01,3.),('wall_loss',0.,3.),('excitation',0.,.2),('actuator_x',0.,1.),('actuator_y',0.,1.),('actuator_radius',.0002,.02),('optical_gain',1.,600.),('routing_strength',0.,1.)):
        value=getattr(c,key)
        if not isinstance(value,(int,float)) or not math.isfinite(value) or not a<=value<=b:raise ValueError('Invalid basin '+key)
    if type(c.modes) is not int or not 1<=c.modes<=36:raise ValueError('Mode cap36')
    if c.diagnostic not in ('envelope','height','nodes','normals'):raise ValueError('Unknown Water diagnostic')
    if type(c.routing_band) is not int or not -1<=c.routing_band<12:raise ValueError('Unknown routing band')
    return c
class Basin:
    def __init__(self,data=None):
        self.settings=validate(data);c=self.settings
        # Cap axis index6: >=~21samples per shortest wavelength on128side,
        # rather than claiming audio bands correspond to these modes.
        candidates=[(m,n) for m in range(7) for n in range(7) if m+n>0]
        candidates.sort(key=lambda v:(v[0]/c.width)**2+(v[1]/c.length)**2)
        self.indices=np.array(candidates[:c.modes],dtype=float)
        k=np.sqrt((self.indices[:,0]*math.pi/c.width)**2+(self.indices[:,1]*math.pi/c.length)**2)
        self.omega=np.sqrt((9.81*k+.072/1000.*k**3)*np.tanh(k*c.depth))
        self.z=np.zeros(c.modes,dtype=np.complex128);self.sample_index=0
        self._coefficients()
    def _coefficients(self):
        c=self.settings;k=np.sqrt((self.indices[:,0]*math.pi/c.width)**2+(self.indices[:,1]*math.pi/c.length)**2)
        self.gamma=c.damping+c.wall_loss+2*c.viscosity*k*k
        if np.any(self.gamma>=self.omega*.95):raise ValueError('Damping exceeds supported underdamped regime')
        self.wd=np.sqrt(self.omega**2-self.gamma**2);self.lam=-self.gamma+1j*self.wd
        self.step=-1j/self.wd*np.expm1(self.lam/RATE)/self.lam
        self.weights=np.exp(self.lam[:,None]*np.arange(2048)[None,:]/RATE)
        self.coupling=np.cos(self.indices[:,0]*math.pi*c.actuator_x)*np.cos(self.indices[:,1]*math.pi*c.actuator_y)*np.exp(-.5*(k*c.actuator_radius)**2)
    def update(self,data):
        c=validate(data);old=self.settings
        if c==old:return self,False
        structural=any(getattr(c,k)!=getattr(old,k) for k in ('width','length','depth','modes','viscosity'))
        if structural:return Basin(asdict(c)),True
        trial=Basin(asdict(c));q=self.z.real;v=-self.wd*self.z.imag-self.gamma*q
        trial.z=self.z.copy() if np.array_equal(trial.gamma,self.gamma) else q-1j*(v+trial.gamma*q)/trial.wd;trial.sample_index=self.sample_index
        return trial,False
    def advance(self,pcm,band_level=0.):
        pcm=np.asarray(pcm,dtype=float)
        if pcm.ndim!=1 or len(pcm)>2048 or not np.all(np.isfinite(pcm)):raise ValueError('Invalid canonical PCM block')
        n=len(pcm)
        if not n:return
        gain=self.settings.excitation*(1.+self.settings.routing_strength*float(np.clip(band_level,0.,1.)))
        self.z=np.exp(self.lam*n/RATE)*self.z+self.step*self.coupling*gain*(self.weights[:,:n]@pcm[::-1])
        if not np.all(np.isfinite(self.z)) or np.max(np.abs(self.z))>1.:raise RuntimeError('Basin outside bounded linear regime')
        self.sample_index+=n
    def field(self,x,y):
        basis=np.cos(self.indices[:,0]*math.pi*x)*np.cos(self.indices[:,1]*math.pi*y)
        return complex(np.sum(self.z*basis))
    def uniforms(self):
        c=self.settings
        modes=[(float(m),float(n),float(z.real),float(z.imag)) for (m,n),z in zip(self.indices,self.z)]
        return dict(u_cym_depth=c.depth,u_cym_modes=modes+[(0.,0.,0.,0.)]*(36-len(modes)),u_cym_count=len(modes),u_cym_basin=(c.width,c.length,c.optical_gain,float(('envelope','height','nodes','normals').index(c.diagnostic))),u_cym_actuator=(c.actuator_x,c.actuator_y))
    def report(self):
        return dict(mode_hz=(self.omega/math.tau).tolist(),damped_hz=(self.wd/math.tau).tolist(),gamma=self.gamma.tolist(),indices=self.indices.tolist(),amplitude_m=float(np.max(np.abs(self.z))),sample_index=self.sample_index,model='forced standing gravity-capillary modes; sliding90deg ideal walls; quadrature envelope display, not measured Faraday onset')
