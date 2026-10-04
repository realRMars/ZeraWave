import numpy as np
from frequency_bands import FrequencyBands
from beat_tracker import BeatTracker


class AudioAnalyzer:
    def __init__(self):
        self.previous_magnitudes = None
        self.beat_tracker = BeatTracker()
        self.frequency_bands = FrequencyBands()

    def rms(self, samples):
        return float(np.sqrt(np.mean(samples**2)))

    def spectrum(self, samples, samplerate=48000):
        spectrum = np.fft.rfft(samples)
        frequencies = np.fft.rfftfreq(
            len(samples),
            d=1.0 / samplerate,
        )

        magnitudes = np.abs(spectrum)

        return frequencies, magnitudes

    def band_energy(self, frequencies, magnitudes, low, high):
        mask = (frequencies >= low) & (frequencies < high)

        if not np.any(mask):
            return 0.0

        return float(np.mean(magnitudes[mask]))

    def spectral_flux(self, magnitudes):
        previous = self.previous_magnitudes

        if (
            previous is None
            or len(previous) != len(magnitudes)
        ):
            self.previous_magnitudes = magnitudes
            return 0.0

        flux = float(
            np.sum(np.maximum(0.0, magnitudes - previous))
        )
        self.previous_magnitudes = magnitudes

        return flux

    def describe_samples(self, samples, samplerate=48000, source_id=None):
        """Opt-in standalone descriptors; leaves all legacy analysis state alone."""
        if not hasattr(self, '_descriptors'):
            from musical_descriptors import DescriptorAnalysis
            self._descriptors = DescriptorAnalysis()
        return self._descriptors.process(samples, samplerate, source_id)

    def reset_descriptors(self):
        """End/seek/restart only the opt-in measurements, never legacy state."""
        if hasattr(self, '_descriptors'):
            self._descriptors.reset()
