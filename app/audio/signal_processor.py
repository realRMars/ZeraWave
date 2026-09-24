class SignalProcessor:
    def __init__(self, smoothing=0.5):
        self.smoothing = smoothing
        self.previous = {}

    def smooth(self, name, value):
        previous = self.previous.get(name, 0.0)

        result = (
            previous * self.smoothing
            + value * (1.0 - self.smoothing)
        )

        self.previous[name] = result

        return result

    def normalize(self, value, minimum, maximum):
        if maximum <= minimum:
            return 0.0

        result = (value - minimum) / (maximum - minimum)

        return max(0.0, min(1.0, result))

    def process(self, name, value, minimum, maximum):
        normalized = self.normalize(
            value,
            minimum,
            maximum,
        )

        return self.smooth(
            name,
            normalized,
        )