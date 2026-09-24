import time

import numpy as np

from capture import AudioCapture


def main():
    print("DreamWave AudioCapture Test")
    print("---------------------------")

    capture = AudioCapture()

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
            data = capture.read(numframes=2048)

            level = np.sqrt(np.mean(data**2))
            bars = int(min(level * 80, 40))

            print(
                f"\rSignal: {'█' * bars:<40} {level:.4f}",
                end="",
                flush=True,
            )

    finally:
        capture.stop()

    print("\nTest complete.")


if __name__ == "__main__":
    main()