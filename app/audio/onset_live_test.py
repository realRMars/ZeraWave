import time

import numpy as np

from analyzer import AudioAnalyzer
from capture import AudioCapture
from onset_detector import OnsetDetector
from signal_processor import SignalProcessor


def main():
    capture = AudioCapture()
    analyzer = AudioAnalyzer()
    processor = SignalProcessor(smoothing=0.5)

    detectors = {
        "bass": OnsetDetector(threshold=0.2),
        "mids": OnsetDetector(threshold=0.2),
        "highs": OnsetDetector(threshold=0.2),
    }

    print("ZeraWave Live Multi-Band Onset Test")
    print("-------------------------------------")

    print("Finding audio loopback device...")
    device = capture.find_device()

    print(f"Using: {device}")
    print("Play music in Opera.")
    print("Listening for 10 seconds...")
    print()

    capture.start()

    try:
        start = time.perf_counter()

        while time.perf_counter() - start < 10:
            samples = capture.read(numframes=2048)

            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            frequencies, magnitudes = analyzer.spectrum(
                samples,
                samplerate=48000,
            )

            bass = analyzer.band_energy(
                frequencies,
                magnitudes,
                20,
                250,
            )

            mids = analyzer.band_energy(
                frequencies,
                magnitudes,
                250,
                4000,
            )

            highs = analyzer.band_energy(
                frequencies,
                magnitudes,
                4000,
                16000,
            )

            bass_processed = processor.process(
                "bass",
                bass,
                0.0,
                10.0,
            )

            mids_processed = processor.process(
                "mids",
                mids,
                0.0,
                1.5,
            )

            highs_processed = processor.process(
                "highs",
                highs,
                0.0,
                0.6,
            )

            bass_onset = detectors["bass"].detect(
                bass_processed
            )

            mids_onset = detectors["mids"].detect(
                mids_processed
            )

            highs_onset = detectors["highs"].detect(
                highs_processed
            )

            if (
                bass_onset > 0.0
                or mids_onset > 0.0
                or highs_onset > 0.0
            ):
                print(
                    f"Bass {bass_onset:.2f} | "
                    f"Mids {mids_onset:.2f} | "
                    f"Highs {highs_onset:.2f}"
                )

    finally:
        capture.stop()

    print("\nTest complete.")


if __name__ == "__main__":
    main()