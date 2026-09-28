"""Conservative onset-grid confidence; no song-section or downbeat claims."""
from collections import deque
import math


class BeatTracker:
    def __init__(self):
        self.flux_levels = deque(maxlen=192)
        self.flux_count = 0
        self.grid_lag = 0
        self.grid_offset = 0
        self.grid_stable = 0
        self.grid_confidence = 0.
        self.last_phase = 0.
        self.flux_dt = None

    def update_flux(self, strength, dt, energy):
        """Autocorrelation of recent spectral activity, independent of visual slew limits."""
        import numpy as np
        if (not math.isfinite(dt) or dt <= 0 or dt > .5 or
                (self.flux_dt is not None and abs(dt-self.flux_dt) > .001)):
            self.__init__()
            return dict(beat_confidence=0.,beat_phase=0.,beat_tick=False,tempo=0.)
        self.flux_dt=dt
        self.flux_levels.append(max(0.,float(strength)))
        self.flux_count+=1
        if self.flux_count % 8 == 0 and len(self.flux_levels) >= 96:
            x=np.array(self.flux_levels)
            # Remove steady activity; retain transient structure without touching
            # any existing normalized audio parameter.
            x=np.maximum(0.,x-np.median(x))
            lags=list(range(max(2,round(60/185/dt)),min(len(x)//3,round(60/55/dt))+1))
            scores=[]
            for lag in lags:
                a,b=x[:-lag],x[lag:]
                scores.append(float(np.dot(a,b)/max(1e-12,np.linalg.norm(a)*np.linalg.norm(b))))
            best=int(np.argmax(scores)); lag=lags[best]; score=scores[best]
            self.grid_stable=self.grid_stable+1 if abs(lag-self.grid_lag)<=1 else 0
            self.grid_lag=lag
            contrast=max(0.,score-float(np.median(scores)))
            self.grid_confidence=min(1.,max(0.,(score-.30)/.45))*min(1.,contrast/.18)*min(1.,self.grid_stable/3.)
            # Phase is the strongest recurring activity within the inferred grid.
            start=self.flux_count-len(x)+1
            bins=np.zeros(lag)
            for j,value in enumerate(x):bins[(start+j)%lag]+=value
            self.grid_offset=int(np.argmax(bins))
        confidence=self.grid_confidence if energy>.02 and max(list(self.flux_levels)[-12:],default=0.)>1e-6 else 0.
        phase=((self.flux_count-self.grid_offset)%self.grid_lag)/self.grid_lag if self.grid_lag else 0.
        tick=confidence>=.65 and phase<self.last_phase
        self.last_phase=phase
        return dict(beat_confidence=confidence,beat_phase=phase,beat_tick=tick,
                    tempo=60/(self.grid_lag*dt) if confidence>=.65 else 0.)
