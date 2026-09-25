import time

from analyzer import AudioAnalyzer
from capture import AudioCapture


def main():
    capture = AudioCapture()
    analyzer = AudioAnalyzer()

    print("DreamWave Live Raw Spectral Flux Test")
    print("--------------------------------------")

    print("Finding audio loopback device...")
    device = capture.find_device()

    print(f"Using: {device}")
    print("Play music in Opera.")
    print("Listening for 10 seconds...")
    print()

    capture.start()

    minimum = None
    maximum = None
    total = 0.0
    count = 0

    try:
        start = time.perf_counter()
        last_print = start

        while time.perf_counter() - start < 10:
            samples = capture.read(numframes=2048)

            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            _, magnitudes = analyzer.spectrum(
                samples,
                samplerate=48000,
            )

            raw_flux = analyzer.spectral_flux(magnitudes)

            if minimum is None or raw_flux < minimum:
                minimum = raw_flux

            if maximum is None or raw_flux > maximum:
                maximum = raw_flux

            total += raw_flux
            count += 1

            now = time.perf_counter()
            if now - last_print >= 1.0:
                print(f"raw_flux = {raw_flux:.3f}")
                last_print = now

    finally:
        capture.stop()

    print("\nSummary")
    print("-------")
    print(f"Samples: {count}")

    if count > 0:
        print(f"Min:     {minimum:.3f}")
        print(f"Max:     {maximum:.3f}")
        print(f"Mean:    {total / count:.3f}")


if __name__ == "__main__":
    main()
