from collections import deque


class SignalProcessor:
    def __init__(self, smoothing=0.5, adaptive_window=20):
        self.smoothing = smoothing
        self.adaptive_window = adaptive_window
        self.previous = {}
        self.adaptive_history = {}

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

    def adaptive_normalize(self, name, value, minimum, maximum):
        if maximum <= minimum:
            return 0.0

        history = self.adaptive_history.setdefault(
            name,
            deque(maxlen=self.adaptive_window),
        )
        history.append(value)

        if len(history) < 8:
            return self.normalize(value, minimum, maximum)

        ordered = sorted(history)
        lower_index = (len(ordered) - 1) * 0.05
        upper_index = (len(ordered) - 1) * 0.95

        lower = ordered[int(lower_index)]
        upper = ordered[int(upper_index)]

        if upper - lower <= (maximum - minimum) * 0.05:
            return self.normalize(value, minimum, maximum)

        result = (value - lower) / (upper - lower)

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

    def process_adaptive(self, name, value, minimum, maximum):
        normalized = self.adaptive_normalize(
            name,
            value,
            minimum,
            maximum,
        )

        return self.smooth(
            name,
            normalized,
        )


class VisualSignalConditioner:
    """Condition fixed normalized signals for stable visual control."""

    def __init__(
        self,
        quiet_threshold=0.03,
        attack_rate=0.35,
        release_rate=0.08,
        max_delta=0.12,
    ):
        self.quiet_threshold = quiet_threshold
        self.attack_rate = attack_rate
        self.release_rate = release_rate
        self.max_delta = max_delta
        self.values = {}

    def condition(self, name, value):
        value = max(0.0, min(1.0, value))

        if value <= self.quiet_threshold:
            target = 0.0
        else:
            target = (
                (value - self.quiet_threshold)
                / (1.0 - self.quiet_threshold)
            )

        previous = self.values.get(name, 0.0)

        if target >= previous:
            step = (target - previous) * self.attack_rate
        else:
            step = (target - previous) * self.release_rate

        step = max(-self.max_delta, min(self.max_delta, step))
        result = max(0.0, min(1.0, previous + step))

        self.values[name] = result

        return result