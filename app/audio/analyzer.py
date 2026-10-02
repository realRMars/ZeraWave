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