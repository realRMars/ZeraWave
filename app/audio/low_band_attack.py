"""Optional attack proxy from an existing low-band measurement, no new FFT.

This names a fresh low-frequency rise, not a classified kick. The caller supplies
the existing20..250Hz mean magnitude and PCM sample count. Legacy normalization,
band signals and onset detectors are untouched.
"""
import math


class LowBandAttack:
    def __init__(self):
        self.reset()

    def reset(self):
        self.source_id = None
        self.seconds = 0.
        self.previous = None

    def process(self, level, sample_count, source_id=None, sensitivity=1.):
        if type(sensitivity) not in (int,float) or not math.isfinite(sensitivity) or not .5<=sensitivity<=2.:
            raise ValueError('Sensitivity must be finite in .5..2')
        if source_id != self.source_id:
            self.reset()
            self.source_id = source_id
        self.seconds += sample_count/48000.
        strength = 0.
        rise=0.;floor=6./sensitivity;fraction=0.
        valid = type(level) in (int,float) and math.isfinite(level) and level >= 0.
        if valid and self.previous is not None:
            rise = max(0.,level-self.previous)
            floor=6./sensitivity
            fraction = rise/max(floor,level)
            if level >= floor and rise >= 4./sensitivity:
                q = max(0.,min(1.,(fraction-.22/sensitivity)/(.48/sensitivity)))
                strength = q*q*(3.-2.*q)
        self.previous = level if valid else None
        return dict(version=1,sample_seconds=self.seconds,bass_attack=strength,
                    detector_response=dict(rise=rise,level_floor=floor,rise_floor=4./sensitivity,
                        fraction=fraction,fraction_floor=.22/sensitivity,fraction_span=.48/sensitivity,
                        sensitivity=sensitivity),
                    low_band_level=level if valid else 0.)
