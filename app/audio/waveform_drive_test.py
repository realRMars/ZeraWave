"""Original PCM amplitude selection; no devices, playback or normalization."""
from types import SimpleNamespace
import numpy as np
from waveform_drive import WaveformDrive, LEVELS


def run():
    drive=WaveformDrive()
    original=SimpleNamespace(**{key:.9 for key in LEVELS},band12={'sentinel':1},tempo=120.)
    for frequency in (80.,1000.,10000.):
        t=np.arange(4800)/48000.
        left=.25*np.sin(2*np.pi*frequency*t)
        pcm=np.column_stack((left,-left)) # Stereo cancellation must not erase amplitude.
        raw=drive.select(original,pcm,dict(generation=1,raw_waveform=True,volume=0.,mute=True))
        assert np.isclose(raw.bass,.25/np.sqrt(2)) and np.isclose(raw.highs,.25)
        assert raw.bass==raw.mids and raw.band12==original.band12
        assert raw.analyzed_levels['bass']==.9 and original.bass==.9
        assert raw.beat_tick is False and raw.tempo==0.
    raw=drive.select(original,np.zeros((2048,2)),dict(generation=1,raw_waveform=True))
    assert raw.bass==raw.highs==raw.flux==raw.impact==0. and raw.is_silent
    raw=drive.select(original,np.ones((2048,2))*.5,dict(generation=1,raw_waveform=True))
    assert raw.bass==raw.highs==raw.flux==raw.impact==.5
    raw=drive.select(original,np.ones((2048,2))*.75,dict(generation=2,raw_waveform=True))
    assert raw.bass==.75 and raw.impact==raw.flux==0. # Source boundary is no onset.
    raw=drive.select(original,np.ones((2048,2))*1.25,dict(generation=2,raw_waveform=True))
    assert raw.source_levels['rms']==1.25 and raw.source_levels['clipped_samples']==4096
    assert raw.bass==raw.highs==1. # Existing graphics domain only; truthful measured overs.
    for volume,mute in ((0.,False),(.2,False),(1.,True)):
        frame=SimpleNamespace(**{key:.9 for key in LEVELS})
        selected=drive.select(frame,np.ones((2048,2))*.125,dict(generation=2,raw_waveform=False,volume=volume,mute=mute))
        assert selected is frame and all(getattr(selected,key)==.9 for key in LEVELS)
    print('PASS: direct RMS/peak, anti-phase stereo, frequency independence, silence/rise/overs, source-boundary suppression, untouched analyzed fields, volume/mute independent.')


if __name__=='__main__':run()
