class OnsetDetector:
    def __init__(self, threshold=0.2):
        self.threshold = threshold
        self.previous = 0.0

    def detect(self, value):
        change = value - self.previous

        self.previous = value

        if change <= self.threshold:
            return 0.0

        return min(1.0, change)