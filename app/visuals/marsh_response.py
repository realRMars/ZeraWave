"""Bounded individual ghostlight interpretation; shared audio and FluxMemory unchanged."""
import math
import numpy as np
from magnetic_response import FluxMemory
from color_controls import PALETTE_FAMILIES

class MarshResponse(FluxMemory):
    def advance(self,t,dt,bass,mids,highs,flux,impact,travel,present):
        serial=self.serial;rewound=t<self.time
        values=super().advance(t,dt,bass,mids,highs,flux,impact,present)
        if self.serial and (rewound or self.serial!=serial):
            cell=math.floor(travel/8)+1+(self.serial+self.seed+self.visit)%2
            side=-1. if (self.serial+self.seed+self.visit)%2 else 1.
            self.events[-1]=(t,float(cell),side,min(1.,impact))
        return values

class LampCache:
    """Seven roadside cells/two lamps each,42 vec4 values/672B; one frame retained."""
    def __init__(self):self.origin=0;self.data=np.zeros((42,4),dtype='f4')
    @staticmethod
    def seed(cell,side):
        value=math.sin((cell%127)*27.13+(side%127)*91.71)*4375.83
        return value-math.floor(value)
    @staticmethod
    def position(cell,side,seed,phase,heat=0.,age=0.):
        dart=(.5+.5*math.sin(phase*.71+2.))**6
        return (side*(1.05+.32*math.sin(phase*.8)+.12*dart*math.sin(phase*5.)),
                -.65+.7*(.5+.5*math.sin(phase*.63))+.45*dart+.12*heat*math.sin(age*7)*math.exp(-max(0.,age)*1.2),
                cell*8+4+2.7*math.sin(phase))
    def build(self,memory,t,visual_time,travel,amount=1.):
        self.origin=math.floor(travel/8)-1;positions=[];meta=[];wakes=[]
        energy=memory.energy*amount;high=memory.high*amount
        for cell in range(self.origin,self.origin+7):
            for side in (-1.,1.):
                seed=self.seed(cell,side);phase=visual_time*(.95+seed*.3)+seed*19+memory.phase*.12+max(0,memory.visit-1)*.23
                selected=[event for event in memory.events if event[1]==cell and event[2]==side]
                age=t-selected[-1][0] if selected else 1000.;power=selected[-1][3]*amount if selected else 0.
                heat=power*math.exp(-age*.65);radius=min(6.,max(0.,age*.65));wake=power*math.exp(-age*.7)
                pulse=.5+.5*math.sin(visual_time*(.7+seed*.4)+seed*23+memory.phase*.07)
                # A resting ember is always legible; energy breathes, a selected event blooms locally.
                light=(.34+.66*pulse*pulse)*(.24+.78*energy+.38*high)+heat*1.10
                positions.append((*self.position(cell,side,seed,phase,heat,age),light))
                meta.append((heat,radius,high,seed))
                wakes.append((*self.position(cell,side,seed,phase-.42),wake))
        self.data[:14]=positions;self.data[14:28]=meta;self.data[28:]=wakes
        return tuple(map(tuple,self.data[:14])),tuple(map(tuple,self.data[14:28])),tuple(map(tuple,self.data[28:]))

class MarshPalette:
    def __init__(self):
        self.families=np.array([[[int(h[k:k+2],16)/255. for k in (1,3,5)] for h in colors] for colors in PALETTE_FAMILIES['marsh.palette'].values()])
    def sample(self,memory):
        phase=memory.phase*.065+memory.time*.014+max(0,memory.visit-1)*.27;family=int(phase)%3
        f=max(0.,min(1.,((phase%1)-.12)/.88));f=f*f*(3-2*f)
        return tuple(map(tuple,self.families[family]*(1-f)+self.families[(family+1)%3]*f))
