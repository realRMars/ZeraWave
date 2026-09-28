import numpy as np

from analyzer import AudioAnalyzer


def main():
    analyzer = AudioAnalyzer()

    samplerate = 48000
    duration = 1.0
    frequency = 440.0

    time_axis = np.arange(
        int(samplerate * duration)
    ) / samplerate

    samples = np.sin(
        2 * np.pi * frequency * time_axis
    )

    frequencies, magnitudes = analyzer.spectrum(
        samples,
        samplerate=samplerate,
    )

    peak_index = np.argmax(magnitudes)
    peak_frequency = frequencies[peak_index]

    print("ZeraWave FFT Test")
    print("------------------")
    print(f"Expected frequency: {frequency:.1f} Hz")
    print(f"Detected frequency:  {peak_frequency:.1f} Hz")


if __name__ == "__main__":
    main()