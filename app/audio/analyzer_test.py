import numpy as np

from analyzer import AudioAnalyzer


def main():
    analyzer = AudioAnalyzer()

    silent = np.zeros(2048)
    loud = np.ones(2048) * 0.5

    silent_level = analyzer.rms(silent)
    loud_level = analyzer.rms(loud)

    print("DreamWave AudioAnalyzer Test")
    print("----------------------------")
    print(f"Silent RMS: {silent_level:.4f}")
    print(f"Loud RMS:   {loud_level:.4f}")


if __name__ == "__main__":
    main()