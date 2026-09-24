import numpy as np

from analyzer import AudioAnalyzer


def main():
    analyzer = AudioAnalyzer()

    samplerate = 48000
    duration = 1.0

    time_axis = np.arange(
        int(samplerate * duration)
    ) / samplerate

    bass = np.sin(2 * np.pi * 100 * time_axis)
    mids = np.sin(2 * np.pi * 1000 * time_axis)
    highs = np.sin(2 * np.pi * 8000 * time_axis)

    samples = bass + mids + highs

    frequencies, magnitudes = analyzer.spectrum(
        samples,
        samplerate=samplerate,
    )

    bass_energy = analyzer.band_energy(
        frequencies,
        magnitudes,
        20,
        250,
    )

    mid_energy = analyzer.band_energy(
        frequencies,
        magnitudes,
        250,
        4000,
    )

    high_energy = analyzer.band_energy(
        frequencies,
        magnitudes,
        4000,
        16000,
    )

    print("DreamWave Frequency Band Test")
    print("------------------------------")
    print(f"Bass energy: {bass_energy:.2f}")
    print(f"Mid energy:  {mid_energy:.2f}")
    print(f"High energy: {high_energy:.2f}")


if __name__ == "__main__":
    main()