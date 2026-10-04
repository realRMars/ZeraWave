"""Two bounded, opt-in Planet Canvas treatment mappings; no audio analysis."""
import math


def held_planet(enabled, state, sequence=(), transition_sequence=False, transitions=None):
    """Exclude Main and every sequence/transition, including held endpoints."""
    return (enabled is True and state == 5 and not sequence
            and not transition_sequence and not (transitions or {}).get('pair'))


def smoothstep(low, high, value):
    q = max(0., min(1., (value-low)/(high-low)))
    return q*q*(3.-2.*q)


class PlanetCanvasDSP:
    """Sample-clock ratios, independent of mutable authored/manual amounts.

    Missing/malformed payloads hard-clear; valid-format silent snapshots ease
    toward neutral. Repeated window timestamps never advance the easing.
    Call reset on explicit discontinuity/EOF/context exit. A rewound timestamp
    also resets. Caller packets remain bounded; a >250ms sample jump is a gap.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.ratios = (1., 1.)
        self.last_time = 0.
        self.source_id = None

    @staticmethod
    def _number(value):
        return type(value) in (int, float) and math.isfinite(value)

    def observe(self, payload, source_id=None):
        if source_id != self.source_id:
            self.reset()
            self.source_id = source_id
        if (not isinstance(payload, dict) or type(payload.get('version')) is not int
                or payload['version'] != 1 or type(payload.get('valid')) is not bool
                or not self._number(payload.get('analyzed_seconds'))
                or payload['analyzed_seconds'] < 0.):
            self.reset()
            return
        time = payload['analyzed_seconds']
        target = (1., 1.)
        if payload['valid']:
            fields = ('signal_confidence', 'spectral_spread', 'fullness')
            if any(not self._number(payload.get(k)) or not 0. <= payload[k] <= 1. for k in fields):
                self.reset()
                return
            confidence = payload['signal_confidence']
            target = (1.-confidence*.40*(1.-smoothstep(.04,.35,payload['spectral_spread'])),
                      1.-confidence*.50*(1.-smoothstep(.10,.65,payload['fullness'])))
        dt = time-self.last_time
        if dt < 0. or dt > .25:
            self.reset()
            self.last_time = time
            self.source_id = source_id
            return
        if dt == 0.:
            # Invalidity overrides a previously valid snapshot even if its
            # timestamp repeats; do not reuse a stale signal.
            if not payload['valid']:
                self.ratios = (1., 1.)
            return
        self.last_time = time
        # Stronger amount uses .7s; relaxed amount uses 1.2s.
        self.ratios = tuple(value+(goal-value)*-math.expm1(-dt/(.7 if goal>value else 1.2))
                            for value, goal in zip(self.ratios, target))

    def apply(self, base):
        """Resolve current ceilings without modifying profiles or sample state."""
        return (base[0]*self.ratios[0], base[1]*self.ratios[1], base[2])
