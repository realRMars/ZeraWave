import soundcard as sc


class AudioCapture:
    def __init__(self, device_name=None, samplerate=48000, channels=2):
        self.device_name = device_name
        self.samplerate = samplerate
        self.channels = channels

        self.loopback = None
        self.recorder = None

    def find_device(self):
        loopbacks = sc.all_microphones(include_loopback=True)

        if self.device_name is None:
            speaker = sc.default_speaker()
            target_name = speaker.name
        else:
            target_name = self.device_name

        self.loopback = next(
            (
                mic
                for mic in loopbacks
                if target_name in mic.name
            ),
            None,
        )

        if self.loopback is None:
            raise RuntimeError(
                f"Loopback device not found: {target_name}"
            )

        return self.loopback

    def start(self):
        if self.loopback is None:
            self.find_device()

        self.recorder = self.loopback.recorder(
            samplerate=self.samplerate,
            channels=self.channels,
        )

        self.recorder.__enter__()

    def read(self, numframes=2048):
        if self.recorder is None:
            raise RuntimeError("Audio capture has not been started")

        return self.recorder.record(numframes=numframes)

    def stop(self):
        if self.recorder is not None:
            self.recorder.__exit__(None, None, None)
            self.recorder = None