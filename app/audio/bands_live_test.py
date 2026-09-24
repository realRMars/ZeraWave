import time

from analyzer import AudioAnalyzer
from capture import AudioCapture


def main():
    capture = AudioCapture()
    analyzer = AudioAnalyzer()

    print("DreamWave Live Frequency Band Test")
    print("----------------------------------")

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

            print(
                f"\rBass: {bass:7.2f} | "
                f"Mids: {mids:7.2f} | "
                f"Highs: {highs:7.2f}",
                end="",
                flush=True,
            )

    finally:
        capture.stop()

    print("\nTest complete.")


if __name__ == "__main__":
    main()