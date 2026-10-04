"""Bounded, sample-clock DSP measurements; no artistic or semantic mapping.

Opt-in through AudioAnalyzer.describe_samples. See docs/AUDIO_DESCRIPTORS.md
for units, windows, smoothing, reset requirements and heuristic limitations.
"""
from dataclasses import asdict, dataclass
import math

import numpy as np
from frequency_bands import DEFAULT_EDGES


@dataclass(frozen=True)
class MusicalDescriptors:
    version: int = 1
    valid: bool = False
    signal_confidence: float = 0.0
    analyzed_seconds: float = 0.0
    pending_seconds: float = 0.0
    rms_dbfs: float = -120.0
    intensity: float = 0.0
    fullness: float = 0.0
    transient_activity: float = 0.0
    brightness: float = 0.0
    spectral_spread: float = 0.0
    spectral_flatness: float = 0.0
    tonal_concentration: float = 0.0

    def to_dict(self):
        """Plain finite JSON-compatible values; versioned separately from sessions."""
        return asdict(self)


class DescriptorAnalysis:
    WINDOW_SECONDS = 2048 / 48000
    NOISE_DBFS = -75.0
    MIN_RATE = 8000
    MAX_RATE = 96000
    MAX_CHANNELS = 8
    # Seconds, at each fixed analysis hop; no call-count smoothing.
    TIMES = dict(intensity=(.06, .30), fullness=(.15, .40),
                 transient_activity=(.04, .35), brightness=(.12, .30),
                 spectral_spread=(.12, .30), spectral_flatness=(.12, .30),
                 tonal_concentration=(.12, .30))

    def __init__(self):
        self.reset()

    def reset(self):
        """Call on end, seek, restart or a source discontinuity at the same format."""
        self.format = None
        self.buffer = None
        self.filled = 0
        self.total_samples = 0
        self.window_end = 0
        self.previous_shape = None
        self.previous_rms = None
        self.values = {name: 0.0 for name in self.TIMES}
        self.snapshot = MusicalDescriptors()

    def _configure(self, samplerate, channels, source_id):
        self.reset()
        self.format = (samplerate, channels, source_id)
        self.size = 2 * round(samplerate * self.WINDOW_SECONDS / 2)
        self.hop = self.size // 2
        self.buffer = np.empty((self.size, channels), dtype=np.float64)
        self.window = np.hanning(self.size)[:, None]
        frequencies = np.fft.rfftfreq(self.size, 1 / samplerate)
        self.selected = (frequencies >= DEFAULT_EDGES[0]) & (frequencies < min(DEFAULT_EDGES[-1], samplerate / 2))
        self.frequencies = frequencies[self.selected]
        self.limit = min(DEFAULT_EDGES[-1], samplerate / 2)
        self.band_masks = [(self.frequencies >= low) & (self.frequencies < high)
                           for low, high in zip(DEFAULT_EDGES, DEFAULT_EDGES[1:])]
        self.band_masks = [mask for mask in self.band_masks if mask.any()]

    def process(self, samples, samplerate=48000, source_id=None):
        """Consume normalized float PCM (frames or frames x channels), return latest.

        Rate/channel/source changes reset automatically. Empty packets advance
        no time. Invalid inputs are rejected before any state changes. Explicit
        reset is required for gaps/endings: wall-clock time is deliberately unused.
        """
        if isinstance(samplerate, bool) or not isinstance(samplerate, (int, np.integer)) or not self.MIN_RATE <= samplerate <= self.MAX_RATE:
            raise ValueError('Descriptor samplerate must be an integer in 8000..96000 Hz')
        if source_id is not None and (not isinstance(source_id, str) or len(source_id) > 256):
            raise ValueError('Descriptor source_id must be a string of at most 256 characters or None')
        pcm = np.asarray(samples)
        if pcm.dtype.kind not in 'fiu' or pcm.ndim not in (1, 2):
            raise ValueError('Need finite normalized PCM with shape (frames,) or (frames, channels)')
        channels = 1 if pcm.ndim == 1 else pcm.shape[1]
        if not 1 <= channels <= self.MAX_CHANNELS or not np.isfinite(pcm).all():
            raise ValueError('Need finite PCM with 1..8 channels')
        if pcm.size and np.max(np.abs(pcm.astype(np.float64, copy=False))) > 1.0:
            raise ValueError('PCM must be normalized to -1..1; integer PCM needs explicit scaling')
        if self.format != (samplerate, channels, source_id):
            self._configure(int(samplerate), channels, source_id)
        pcm = pcm.reshape(-1, channels)
        offset = 0
        while offset < len(pcm):
            count = min(self.size - self.filled, len(pcm) - offset)
            self.buffer[self.filled:self.filled + count] = pcm[offset:offset + count]
            self.filled += count
            self.total_samples += count
            offset += count
            if self.filled == self.size:
                self._measure(samplerate)
                self.buffer[:self.hop] = self.buffer[self.hop:]
                self.filled = self.hop
        data = self.snapshot.to_dict()
        data['pending_seconds'] = (self.total_samples - self.window_end) / samplerate
        return MusicalDescriptors(**data)

    def _measure(self, samplerate):
        # Channel power averaging avoids antiphase cancellation. DC is excluded.
        centered = self.buffer - np.mean(self.buffer, axis=0)
        rms = float(np.sqrt(np.mean(centered * centered)))
        dbfs = max(-120.0, 20 * math.log10(max(rms, 1e-6)))
        active = dbfs > self.NOISE_DBFS
        targets = {name: 0.0 for name in self.TIMES}
        confidence = 0.0
        if active:
            spectrum = np.fft.rfft(centered * self.window, axis=0)
            power = np.mean(np.abs(spectrum[self.selected]) ** 2, axis=1)
            total = float(power.sum())
            if total > 1e-20:
                shape = power / total
                band_power = np.array([power[mask].sum() for mask in self.band_masks]) / total
                entropy = -float(np.sum(band_power * np.log(np.maximum(band_power, 1e-20))))
                fullness = (math.exp(entropy) - 1) / max(1, len(band_power) - 1)
                centroid = float(np.dot(shape, self.frequencies))
                spread = math.sqrt(float(np.dot(shape, (self.frequencies - centroid) ** 2)))
                flatness = math.exp(float(np.mean(np.log(np.maximum(power, total * 1e-20))))) / float(np.mean(power))
                peaks = np.partition(shape, max(0, len(shape) - 12))[-12:]
                novelty = 0.0
                if self.previous_shape is not None:
                    # Broad occupancy change suppresses random per-bin noise
                    # fluctuation; neither this nor RMS rise proves a beat.
                    shape_change = float(np.maximum(0.0, band_power - self.previous_shape).sum())
                    rise = max(0.0, (rms - self.previous_rms) / max(rms, 10 ** (self.NOISE_DBFS / 20)))
                    novelty = min(1.0, max(shape_change / .35, rise / .5))
                self.previous_shape = band_power
                targets.update(fullness=fullness, brightness=centroid / self.limit,
                               spectral_spread=spread / (self.limit / 2),
                               spectral_flatness=flatness, tonal_concentration=float(peaks.sum()),
                               transient_activity=novelty)
                confidence = min(1.0, max(0.0, (dbfs - self.NOISE_DBFS) / 15))
            targets['intensity'] = min(1.0, max(0.0, (dbfs + 75) / 75))
        else:
            # Releases cannot become new positive spectral events. A later
            # onset after silence is legitimate; the first source window isn't.
            self.previous_shape = None
        if active and self.previous_rms is not None and self.previous_shape is not None and self.previous_rms <= 10 ** (self.NOISE_DBFS / 20):
            targets['transient_activity'] = 1.0
        self.previous_rms = rms
        dt = (self.size if self.window_end == 0 else self.hop) / samplerate
        for name, (attack, release) in self.TIMES.items():
            target = min(1.0, max(0.0, targets[name]))
            tau = attack if target > self.values[name] else release
            self.values[name] += (target - self.values[name]) * -math.expm1(-dt / tau)
        self.window_end = self.total_samples
        self.snapshot = MusicalDescriptors(valid=active and confidence > 0,
                                           signal_confidence=confidence,
                                           analyzed_seconds=self.window_end / samplerate,
                                           rms_dbfs=dbfs, **self.values)
