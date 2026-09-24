class SignalProcessor:
    def __init__(self, smoothing=0.5):
        self.smoothing = smoothing
        self.previous = 0.0

    def smooth(self, value):
        result = (
            self.previous * self.smoothing
            + value * (1.0 - self.smoothing)
        )

        self.previous = result

        return result
