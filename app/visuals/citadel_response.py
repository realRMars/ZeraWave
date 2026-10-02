"""Bounded visual tower memory and wind interpretation; no audio analysis."""
import math
class TowerCadence:
    def __init__(self,seed=7301):self.seed=int(seed);self.reset()
    def reset(self):
        self.time=0.;self.phase=0.;self.wind=0.;self.light=0.;self.settle=0.;self.armed=True;self.serial=0;self.events=[];self.visit=0;self.present=False;self.last_hit=-100.
    def advance(self,t,dt,bass,mids,highs,impact,present):
        if t<self.time:self.reset()
        dt=max(0.,float(dt));self.time=t
        if present and not self.present:self.visit+=1
        self.present=bool(present);self.events=[e for e in self.events if 0<=t-e[0]<5.]
        wind=max(0.,min(1.,mids*.7+bass*.3)) if present else 0.
        light=max(0.,min(1.,highs*.55+mids*.45)) if present else 0.
        self.wind+=(wind-self.wind)*(1.-math.exp(-dt/(.6 if wind>self.wind else 2.4)))
        self.light+=(light-self.light)*(1.-math.exp(-dt/(.3 if light>self.light else 1.8)))
        self.phase+=dt*(.045+.6*self.wind)
        self.settle*=math.exp(-dt*2.1)
        if impact<.08:self.armed=True
        if present and impact>.28 and self.armed and t-self.last_hit>.35:
            self.armed=False;self.last_hit=t;self.serial+=1;self.settle=min(1.,self.settle+impact)
            tower=(self.serial*3+self.seed+self.visit)%4
            variant=(self.serial*37+self.seed+self.visit*11)%97/97.
            self.events=(self.events+[(t,float(tower),min(1.,impact),variant)])[-4:]
        return (self.wind,self.light,self.phase,self.settle)
    def fronts(self):return self.events+[(-1000.,0.,0.,0.)]*(4-len(self.events))
