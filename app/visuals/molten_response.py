"""Bounded artistic current pressure, vent selection and cooling; no audio analysis."""
import math
import numpy as np
from magnetic_response import FluxMemory
from color_controls import PALETTE_FAMILIES

class MoltenMemory(FluxMemory):
    def reset(self):
        super().reset();self.pressure=0.;self.shear=0.;self.temperature=0.;self.development=0.;self.cooling=[]
    @staticmethod
    def center(y):return .65*math.sin(y*.34)+.28*math.sin(y*.77)
    def advance(self,t,dt,bass,mids,highs,flux,impact,present):
        previous=self.serial;rewound=t<self.time
        super().advance(t,dt,bass,mids,highs,flux,impact,present)
        dt=max(0.,float(dt));self.cooling=[e for e in self.cooling if 0<=t-e[0]<18.]
        for name,target,attack,release in (('pressure',min(1.,max(0.,bass*.68+flux*.32)) if present else 0.,.65,3.4),('shear',min(1.,max(0.,mids)) if present else 0.,.6,2.),('temperature',self.energy,4.5,8.)):
            value=getattr(self,name);setattr(self,name,value+(target-value)*(1-math.exp(-dt/(attack if target>value else release))))
        if present:self.development=min(1.,self.development+dt*(.018+.045*self.pressure))
        if self.serial and (rewound or self.serial!=previous):
            # Original two vents remain in the authored route, with four additional river sites.
            y=(1.2,-.9,-3.,3.6,-6.,-8.)[(self.serial+self.seed+self.visit)%6]
            event=(t,self.center(y),y,min(1.,max(0.,impact)))
            self.cooling=(self.cooling+[event])[-4:];self.events[-1]=event
        return self.pressure,self.shear,self.high,self.temperature
    def deposits(self):return self.cooling+[(-1000.,0.,0.,0.)]*(4-len(self.cooling))

class MoltenPalette:
    def __init__(self):
        self.families=np.array([[[int(h[k:k+2],16)/255. for k in (1,3,5)] for h in colors] for colors in PALETTE_FAMILIES['molten.palette'].values()])
    def sample(self,memory):
        phase=memory.phase*.007+max(0,memory.visit-1)*.19;family=int(phase)%3
        f=max(0.,min(1.,((phase%1)-.8)/.2));f=f*f*(3-2*f)
        return tuple(map(tuple,self.families[family]*(1-f)+self.families[(family+1)%3]*f))
