"""Bounded mineral descriptors and artistic spring response; no audio analysis.

Cache owns 8x24 cells, eight RGBA32F texels each (24 KiB). Stable recipes use
integer hashing; streaming changes only when travel crosses a cell. Renderer
owns texture and cleanup. Spring propagates analytically for held input;
four source-triggered fronts expire after six seconds. No physical solver claim.
"""
from functools import lru_cache
import math
import numpy as np

def seed(x,z,salt):
    n=((int(x)*73856093)^(int(z)*19349663)^(salt*83492791))&0xffffffff
    n^=n>>16;n=(n*2246822519)&0xffffffff;n^=n>>13
    return (n&0xffffff)/16777216.

def cavern_knot(index):
    return (seed(0,index,73)*2.-1.)*4.6

def cavern_path(z):
    """Seeded straight legs with C2 rounded bends; bounded chamber center."""
    span=14.;radius=2.8;index=math.floor(float(z)/span+.5);d=float(z)-index*span
    x=cavern_knot(index);left=(x-cavern_knot(index-1))/span;right=(cavern_knot(index+1)-x)/span
    if d<=-radius:return x+left*d,left
    if d>=radius:return x+right*d,right
    u=(d+radius)/(2*radius)
    return x-radius*left+2*radius*(left*u+(right-left)*(u**3-.5*u**4)),left+(right-left)*(3*u*u-2*u**3)

def cavern_axis(z):return cavern_path(z)[0]

@lru_cache(maxsize=512)
def formation(x,z):
    s=seed(x,z,31);cx=(x+.5)*2.8;axis=cavern_axis((z+.5)*2.8)
    roof=.6+math.sqrt(max(.1,19.36-((cx-axis)*.8)**2))+.18
    row=[(s,.45+seed(x,z,47)**1.4*2.6,.22+.55*seed(x,z,14),roof),
         ((seed(x,z,2)-.5)*.65,(seed(x,z,9)-.5)*.65,.12*math.sin(s*19),.10*math.cos(s*31))]
    for i in range(3):
        individual=seed(x,z,i*17+63);a=s*math.tau+i*2.1+(individual-.5)*.8
        # Authored leader/companions: intergrowth, not three repeated towers.
        quartz=.27<=s<=.66
        height=(1.3+individual*2.35)*(1.,.56,.34)[i] if quartz else .62+individual*1.35
        radius=(.18+.21*seed(x,z,i+82)) if quartz else .29+.22*seed(x,z,i+82)
        spread=(.08,.40,.65)[i] if quartz else (.06,.35,.53)[i]
        row.extend([(math.cos(a),math.sin(a),.075*math.sin(a*3),.075*math.cos(a*2)),
                    (height,radius,individual,spread)])
    return tuple(row)

class FormationCache:
    def __init__(self):self.origin=None;self.uploads=0
    def update(self,travel):
        origin=(-4,math.floor(travel/2.8)-2)
        if origin==self.origin:return None
        self.origin=origin;self.uploads+=1
        data=np.empty((24,64,4),dtype='f4')
        for z in range(24):
            for x in range(8):data[z,x*8:(x+1)*8]=formation(origin[0]+x,origin[1]+z)
        return data.tobytes()

class MineralResponse:
    def __init__(self):self.reset()
    def reset(self):
        self.time=0.;self.phase=0.;self.x=0.;self.v=0.;self.sustain=0.;self.armed=True;self.serial=0;self.events=[];self.last_hit=-1000.
    def advance(self,seconds,dt,bass,movement,highs,impact,travel,active=True):
        if seconds<self.time:self.reset()
        self.time=seconds;dt=max(0.,float(dt));self.events=[e for e in self.events if 0<=seconds-e[0]<6.]
        if impact<.08:self.armed=True
        level=max(0.,min(1.,.65*movement+.35*bass)) if active else 0.
        hit=active and impact>.24 and self.armed and seconds-self.last_hit>.25
        if hit:
            self.serial+=1;self.last_hit=seconds;self.armed=False
            self.v=min(.95,self.v+impact*.8)
            # Choose an existing forward formation; anchor remains in world space.
            z=math.floor((travel+7.)/2.8);axis=cavern_axis((z+.5)*2.8)
            candidates=[x for x in range(-4,4) if formation(x,z)[0][0]>=.27
                        and abs((x+.5)*2.8-axis)>1.1]
            if not candidates:
                z+=1;axis=cavern_axis((z+.5)*2.8)
                candidates=[x for x in range(-4,4) if formation(x,z)[0][0]>=.27
                            and abs((x+.5)*2.8-axis)>1.1]
            # Prefer the near chamber banks so the selected cluster stays trackable.
            candidates.sort(key=lambda x:abs((x+.5)*2.8-axis))
            candidates=candidates[:2]
            x=candidates[(self.serial-1)%len(candidates)] if candidates else -2
            self.events=(self.events+[(seconds,(z+.5)*2.8,min(1.,impact),(x+.5)*2.8)])[-4:]
        self.sustain+=(level-self.sustain)*(1.-math.exp(-dt/(.38 if level>self.sustain else 2.4)))
        self.phase+=dt*(.04+.72*level+.18*max(0.,min(1.,highs)))
        beta=2.4;omega=7.;wd=math.sqrt(omega*omega-beta*beta);target=.075*self.sustain
        y=self.x-target;c=math.cos(wd*dt);s=math.sin(wd*dt);e=math.exp(-beta*dt)
        self.x=target+e*(y*c+(self.v+beta*y)*s/wd)
        self.v=e*(self.v*c-(beta*self.v+omega*omega*y)*s/wd)
        self.x=max(-.16,min(.18,self.x));self.v=max(-1.,min(1.,self.v))
        return (self.x,self.phase,self.sustain,min(1.,abs(self.v)*1.2))
    def fronts(self):return self.events+[(-1000.,0.,0.,0.)]*(4-len(self.events))
