import numpy as np


class AudioAnalyzer:
    def rms(self, samples):
        return float(np.sqrt(np.mean(samples**2)))