"""Artistic field memory and bounded projected paths, independent of audio analysis."""
import math
import numpy as np

class FluxMemory:
    def __init__(self,seed=7301):self.seed=int(seed);self.reset()
    def reset(self):
        self.time=0.;self.energy=0.;self.high=0.;self.phase=0.;self.strain=0.;self.armed=True;self.last_hit=-100.;self.serial=0;self.visit=0;self.present=False;self.events=[]
    def advance(self,t,dt,bass,mids,highs,flux,impact,present):
        if t<self.time:self.reset()
        self.time=t;dt=max(0.,float(dt))
        if present and not self.present:self.visit+=1
        self.present=bool(present);self.events=[e for e in self.events if 0<=t-e[0]<6.]
        drive=min(1.,max(0.,bass*.50+mids*.30+flux*.20)) if present else 0.
        light=min(1.,max(0.,highs)) if present else 0.
        self.energy+=(drive-self.energy)*(1.-math.exp(-dt/(.55 if drive>self.energy else 2.2)))
        self.high+=(light-self.high)*(1.-math.exp(-dt/(.25 if light>self.high else 1.4)))
        self.phase+=dt*(.065+.62*self.energy);self.strain*=math.exp(-dt*1.6)
        if impact<.08:self.armed=True
        if present and self.armed and impact>.27 and t-self.last_hit>.32:
            self.serial+=1;self.last_hit=t;self.armed=False;self.strain=min(1.,self.strain+impact)
            self.events=(self.events+[(t,float((self.serial*5+self.seed+self.visit*3)%8),min(1.,impact),(self.serial*31+self.seed+self.visit*13)%97/97.)])[-4:]
        return self.energy,self.high,self.phase,self.strain
    def fronts(self):return self.events+[(-1000.,0.,0.,0.)]*(4-len(self.events))

class FieldPaths:
    """12x49 projected vertices/96 conservative segment-group bounds; one frame only."""
    def __init__(self,seed=7301):
        self.seed=int(seed);self.f=np.linspace(0.,1.,49);self.ids=np.arange(8.)[:,None]
        self.last_cpu_ms=0.;self.data=None
        self.group_indices=np.arange(8)[:,None]*6+np.arange(7)[None,:]
    def build(self,memory,t,amount=1.):
        phase=memory.phase;f=self.f[None,:];ids=self.ids
        yaw=.56+.18*math.sin(phase*.021);tilt=.30+.10*math.sin(phase*.037)
        c,s=math.cos(yaw),math.sin(yaw);ct,st=math.cos(tilt),math.sin(tilt)
        rot=np.array([[ct*c,st,-ct*s],[-st*c,ct,st*s],[s,0,c]],dtype=np.float64)
        petals=.88+.13*np.sin(ids*2.1+self.seed*.01)
        energy=memory.energy*amount
        spread=(1.32+.58*energy)*petals
        radial=.075+spread*np.sin(np.pi*f)**1.7
        angle=ids*np.pi/4.+.24*np.sin(f*5.+phase*.18+ids)*( .3+energy)
        y=(.47+.60*np.sin(np.pi*f)**1.5)*np.cos(np.pi*f)+np.zeros_like(ids)
        for event in memory.events:
            age=t-event[0];lobe=int(event[1]);front=min(1.,max(0.,(age-.1)/1.65))
            radial[lobe]+=.13*amount*event[2]*np.exp(-((self.f-front)/.14)**2)*math.sin(age*4.)*math.exp(-age*.55)
            companion=(lobe+1)%8;angle[companion]+=.10*amount*event[2]*np.exp(-((self.f-(1.-front))/.18)**2)*math.exp(-age*.5)
        world=np.stack((radial*np.cos(angle),y,radial*np.sin(angle)),axis=-1)
        paths=np.zeros((12,49,3),dtype=np.float64);paths[:8]=world;active=np.zeros(12,dtype=bool);active[:8]=True
        for i,event in enumerate(memory.events):
            age=t-event[0]
            if amount>0. and .60<age<2.7:
                lobe=int(event[1]);a=world[lobe,24];b=world[(lobe+1)%8,24]
                paths[8+i]=a[None,:]*(1-self.f[:,None])+b[None,:]*self.f[:,None]
                paths[8+i,:,1]+=.22*np.sin(np.pi*self.f)*math.sin(age*2.)
                active[8+i]=True
        view=paths@rot.T;view[:,:,2]+=4.1
        projected=view[:,:,:2]/view[:,:,2:3]*1.35
        data=np.empty((12,49,4),dtype='f4');data[:,:,:2]=projected;data[:,:,2]=1./view[:,:,2];data[:,:,3]=self.f
        bounds=np.concatenate((projected.min(axis=1),projected.max(axis=1)),axis=-1)
        q=projected[:,self.group_indices,:]
        groups=np.concatenate((q.min(axis=2),q.max(axis=2)),axis=-1)
        bounds[~active]=1000.;groups[~active]=1000.
        bounds=tuple(map(tuple,bounds));groups=tuple(map(tuple,groups.reshape(96,4)))
        self.data=data
        return data.tobytes(),tuple(bounds),tuple(groups),tuple(rot.T.ravel())
