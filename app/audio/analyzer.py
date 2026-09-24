import numpy as np


class AudioAnalyzer:
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