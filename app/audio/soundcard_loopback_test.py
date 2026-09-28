import time

import numpy as np
import soundcard as sc


def main():
    print("ZeraWave SoundCard Loopback Test")
    print("---------------------------------")

    speaker = sc.default_speaker()
    print(f"Speaker: {speaker}")

    loopbacks = sc.all_microphones(include_loopback=True)

    loopback = next(
        (
            mic
            for mic in loopbacks
            if "MSI AG321CQR" in mic.name
        ),
        None,
    )

    if loopback is None:
        raise RuntimeError("MSI loopback device not found")

    print(f"Loopback: {loopback}")
    print("Play music in Opera during this test.")
    print("Listening for 10 seconds...")
    print()

    with loopback.recorder(
        samplerate=48000,
        channels=2,
    ) as recorder:

        start = time.perf_counter()

        while time.perf_counter() - start < 10:
            data = recorder.record(numframes=2048)

            level = np.sqrt(np.mean(data**2))
            bars = int(min(level * 80, 40))

            print(
                f"\rSignal: {'█' * bars:<40} {level:.4f}",
                end="",
                flush=True,
            )

    print("\nTest complete.")


if __name__ == "__main__":
    main()