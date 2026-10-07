"""Select visual input from unchanged analyzed PCM or direct channel RMS/peak.

No capture/output, auto gain, frequency replacement or analysis-history reset.
"""
from copy import copy
import numpy as np

LEVELS=('bass','mids','highs','flux','energy','impact','bass_onset','mids_onset','highs_onset')
class WaveformDrive:
    def __init__(self):self.previous_rms=self.previous_peak=0.;self.generation=None
    def select(self,frame,pcm,metadata):
        samples=np.asarray(pcm,dtype=np.float64)
        if not len(samples) or not np.isfinite(samples).all():raise ValueError('Waveform drive needs finite PCM.')
        rms=float(np.sqrt(np.mean(samples*samples)));peak=float(np.max(np.abs(samples)))
        fresh=metadata.get('generation')!=self.generation
        rise=0. if fresh else max(0.,peak-self.previous_peak)
        flux=0. if fresh else max(0.,rms-self.previous_rms)
        self.generation=metadata.get('generation');self.previous_rms=rms;self.previous_peak=peak
        result=copy(frame) if metadata.get('raw_waveform',False) else frame
        result.analyzed_levels={k:float(getattr(frame,k,0.)) for k in LEVELS}
        result.source_levels=dict(rms=rms,peak=peak,rms_dbfs=20*float(np.log10(max(rms,1e-12))),peak_dbfs=20*float(np.log10(max(peak,1e-12))),clipped_samples=int(np.count_nonzero(np.abs(samples)>1.)))
        result.visual_drive='Raw waveform' if metadata.get('raw_waveform',False) else 'Analyzed'
        if metadata.get('raw_waveform',False):
            # Direct linear amplitude. Clamp only to the graphics input domain.
            result.bass=result.mids=min(1.,rms);result.highs=min(1.,peak)
            result.energy=(result.bass+result.mids+result.highs)/3.;result.is_silent=rms<=.02
            result.flux=min(1.,flux);result.bass_onset=result.mids_onset=result.highs_onset=min(1.,rise)
            result.impact=result.rhythmic_activity=min(1.,rise)
            result.tempo=result.beat_confidence=result.beat_phase=0.;result.beat_tick=False
        return result
