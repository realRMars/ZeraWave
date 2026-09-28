from beat_tracker import BeatTracker
import numpy as np


def main():
    dt=2048/48000.
    for bpm in (72,120,165):
        tracker=BeatTracker(); confident=[]
        for i in range(900):
            phase=(i*dt*bpm/60)%1.
            value=np.exp(-(min(phase,1-phase)/.06)**2)
            state=tracker.update_flux(value,dt,.5)
            if i>200:confident.append(state['beat_confidence'])
        assert np.mean(np.array(confident)>=.65)>.5,(bpm,np.mean(confident))
        assert min(abs(state['tempo']-bpm),abs(state['tempo']*2-bpm))<12,(bpm,state)
        for _ in range(100):state=tracker.update_flux(0.,dt,0.)
        assert state['tempo']==0 and not state['beat_tick'] and state['beat_confidence']==0.
    tracker=BeatTracker();rng=np.random.default_rng(19);confident=[]
    for _ in range(1000):
        state=tracker.update_flux(float(rng.random()),dt,.4);confident.append(state['beat_confidence'])
    assert np.mean(np.array(confident)>=.65)<.1
    assert tracker.update_flux(1.,2.,.5)['beat_confidence']==0.
    print('PASS: spectral periodicity, tempo tolerance, random activity, silence and discontinuity fallback')

if __name__=='__main__':main()
