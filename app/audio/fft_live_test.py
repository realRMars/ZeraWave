import time

import numpy as np

from analyzer import AudioAnalyzer
from capture import AudioCapture


def main():
    capture = AudioCapture()
    analyzer = AudioAnalyzer()

    print("DreamWave Live FFT Test")
    print("-----------------------")

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
                samples = np.mean(samples, axis=1)

            frequencies, magnitudes = analyzer.spectrum(
                samples,
                samplerate=48000,
            )

            peak_index = np.argmax(magnitudes)
            peak_frequency = frequencies[peak_index]

            print(
                f"\rPeak frequency: {peak_frequency:7.1f} Hz",
                end="",
                flush=True,
            )

    finally:
        capture.stop()

    print("\nTest complete.")


if __name__ == "__main__":
    main()