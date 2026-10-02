"""Auroral material palette; bounded musical history reuses the existing FluxMemory."""
import numpy as np
from color_controls import PALETTE_FAMILIES
from magnetic_response import FluxMemory

class VeilPalette:
    def __init__(self):
        self.families=np.array([[[int(h[k:k+2],16)/255. for k in (1,3,5)] for h in colors] for colors in PALETTE_FAMILIES['auroral.veil'].values()])
    def sample(self,memory):
        phase=memory.phase*.012+max(0,memory.visit-1)*.31;family=int(phase)%3
        f=max(0.,min(1.,((phase%1.)-.68)/.32));f=f*f*(3.-2.*f)
        return tuple(map(tuple,self.families[family]*(1-f)+self.families[(family+1)%3]*f))
