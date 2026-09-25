import numpy as np

from analyzer import AudioAnalyzer


def test_spectral_flux():
    analyzer = AudioAnalyzer()

    a = np.array([1.0, 2.0, 3.0])
    b = np.array([1.0, 5.0, 3.0])
    c = np.array([1.0, 2.0, 3.0])

    first_frame = analyzer.spectral_flux(a)
    assert first_frame == 0.0

    no_change = analyzer.spectral_flux(a)
    assert no_change == 0.0

    positive_change = analyzer.spectral_flux(b)
    assert positive_change == 3.0

    decrease_only = analyzer.spectral_flux(c)
    assert decrease_only == 0.0

    mismatched = AudioAnalyzer()
    mismatched.spectral_flux(np.array([1.0, 2.0]))
    mismatch_flux = mismatched.spectral_flux(
        np.array([1.0, 2.0, 3.0])
    )
    assert mismatch_flux == 0.0

    sequence = [a, a, b, c]
    first_run = AudioAnalyzer()
    second_run = AudioAnalyzer()
    first_results = [first_run.spectral_flux(s) for s in sequence]
    second_results = [second_run.spectral_flux(s) for s in sequence]
    assert first_results == second_results

    print("Spectral flux assertions passed.")


def main():
    test_spectral_flux()

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