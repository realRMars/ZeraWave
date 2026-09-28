import time

from analyzer import AudioAnalyzer
from capture import AudioCapture


def main():
    print("ZeraWave Live Audio Analysis Test")
    print("----------------------------------")

    capture = AudioCapture()
    analyzer = AudioAnalyzer()

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
            level = analyzer.rms(samples)

            bars = int(min(level * 80, 40))

            print(
                f"\rRMS: {'█' * bars:<40} {level:.4f}",
                end="",
                flush=True,
            )

    finally:
        capture.stop()

    print("\nTest complete.")


if __name__ == "__main__":
    main()