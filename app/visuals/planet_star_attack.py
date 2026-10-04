"""Opt-in Planet background flight from the low-band attack proxy."""
import math
from planet_canvas_dsp import held_planet


def attach_bass_attack(frame, analyzer, sample_count, source_id, low_band_level):
    """Transport a fresh sample clock; do not change FFT or normalization."""
    if not hasattr(analyzer, '_planet_star_attack'):
        from low_band_attack import LowBandAttack
        analyzer._planet_star_attack = LowBandAttack()
    tuning=getattr(analyzer,'_planet_star_tuning',None)
    if tuning is not None:
        level,sensitivity,summary=tuning.apply(frame,low_band_level,analyzer._planet_star_attack,source_id)
        frame.planet_star_audio=analyzer._planet_star_attack.process(level,sample_count,source_id,sensitivity)
        tuning.completed(frame.planet_star_audio,summary)
    else:
        frame.planet_star_audio = analyzer._planet_star_attack.process(low_band_level,sample_count,source_id)
    frame.planet_star_audio['legacy_bass_onset'] = frame.bass_onset


class PlanetStarFlight:
    """Bounded attack response and independent positive integrated flight phase.

    bass_attack is a low-frequency rise proxy, not universal kick classification.
    An80ms duplicate-packet guard, .09s audio release, .015/.07s display rise/fall.
    Original motion bounds: cruise1..1.75, shader wake .0012..095.
    Repeated audio frames cannot retrigger; repeated render times cannot advance.
    Source/gap/invalidity clears response but preserves an existing trajectory.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = None
        self.clear_audio()

    def clear_audio(self):
        self.source_id = None
        self.last_audio_time = None
        self.primed_until = 0.
        self.last_attack = -math.inf
        self.sample_pulse = self.target = self.envelope = 0.
        self.rate = 1.
        self.fresh = False
        self.event_count = 0

    def observe(self, payload, source_id=None):
        valid = (isinstance(payload, dict) and type(payload.get('version')) is int
                 and payload['version'] == 1
                 and all(type(payload.get(k)) in (int,float) and math.isfinite(payload[k])
                         for k in ('sample_seconds','bass_attack'))
                 and payload['sample_seconds'] >= 0. and 0. <= payload['bass_attack'] <= 1.)
        if not valid:
            self.clear_audio()
            return
        seconds = payload['sample_seconds']
        if source_id != self.source_id or self.last_audio_time is None:
            self.clear_audio()
            self.source_id = source_id
            self.last_audio_time = seconds
            self.primed_until = seconds + .12
            return
        dt = seconds-self.last_audio_time
        if dt < 0. or dt > .25:
            self.clear_audio()
            self.source_id = source_id
            self.last_audio_time = seconds
            self.primed_until = seconds + .12
            return
        if dt == 0.:
            return
        self.last_audio_time = seconds
        self.sample_pulse *= math.exp(-dt/.09)
        strength = payload['bass_attack']
        if strength >= .10 and seconds >= self.primed_until and seconds-self.last_attack >= .08:
            self.sample_pulse = max(self.sample_pulse,strength)
            self.last_attack = seconds
            self.event_count += 1
        self.fresh = True

    def advance(self, dt, legacy_clock, discontinuity=False):
        dt = max(0.,dt)
        if discontinuity or dt > .25:
            self.clear_audio()
            dt = 0.
        initial = self.phase is None
        if initial:
            self.phase = legacy_clock  # Match the existing position on entry.
        if self.fresh:
            self.target = self.sample_pulse
            self.fresh = False
        else:
            self.target *= math.exp(-dt/.09)
        tau = .015 if self.target > self.envelope else .07
        self.envelope += (self.target-self.envelope)*-math.expm1(-dt/tau)
        self.envelope = max(0.,min(1.,self.envelope))
        self.rate = 1.+.75*self.envelope
        if not initial:
            self.phase += dt*self.rate
        return (1.,self.phase,self.envelope)
