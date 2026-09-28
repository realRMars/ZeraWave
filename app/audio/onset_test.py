from onset_detector import OnsetDetector


def test_shared_analysis_onsets():
    """Exercise real FFT/normalization/conditioning, not detector-only values."""
    import sys
    from pathlib import Path
    import numpy as np

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "visuals"))
    from live_visual_test import analyze_samples
    from analyzer import AudioAnalyzer
    from signal_processor import SignalProcessor, VisualSignalConditioner

    bands = ("bass", "mids", "highs")
    # Exact FFT bins keep each tone within its intended band.
    for band, bin_index in zip(bands, (4, 42, 342)):
        for stereo in (False, True):
            analyzer = AudioAnalyzer()
            processor = SignalProcessor(smoothing=0.5)
            conditioner = VisualSignalConditioner(quiet_threshold=0.06)
            detectors = {name: OnsetDetector(threshold=0.2) for name in bands}
            tone = .9 * np.sin(2 * np.pi * bin_index * np.arange(2048) / 2048)

            def analyze(amplitude):
                samples = tone * amplitude
                if stereo:
                    samples = np.column_stack((samples, samples))
                return analyze_samples(samples, analyzer, processor, conditioner, detectors)

            quiet = [analyze(0.) for _ in range(16)]
            first = [analyze(1.) for _ in range(40)]
            release = [analyze(0.) for _ in range(120)]
            second = [analyze(1.) for _ in range(40)]
            assert all(frame.impact == 0. for frame in quiet), (band, 'Silent onset')
            for attack in (first, second):
                assert getattr(attack[0], band + '_onset') > .2, (band, 'Attack lost before mapping')
                assert all(frame.impact == 0. for frame in attack[10:]), (band, 'Sustain retriggered')
            assert all(frame.impact == 0. for frame in release), (band, 'Release onset')
            assert getattr(release[-1], band) < .001, (band, 'Did not settle')
            previous = {name: 0. for name in bands}
            for frame in quiet + first + release + second:
                assert 0. <= frame.impact <= 1. and 0. <= frame.flux <= 1.
                for name in bands:
                    value = getattr(frame, name)
                    assert 0. <= value <= 1.
                    assert abs(value - previous[name]) <= .120000001, (name, 'Continuous limiter changed')
                    previous[name] = value
                    if name != band:
                        assert getattr(frame, name + '_onset') == 0., (band, name, 'Cross-band onset')
    print('PASS: Shared analysis onsets for three bands, mono/stereo, silence, '
          'two attacks, sustain and release; continuous slew bounds preserved.')


def main():
    test_shared_analysis_onsets()
    detector = OnsetDetector(threshold=0.2)

    values = [
        0.1,
        0.1,
        0.15,
        0.8,
        0.85,
        0.9,
        0.2,
        0.2,
        0.7,
        0.75,
        0.1,
    ]

    print("ZeraWave Onset Detection Test")
    print("--------------------------------")

    for value in values:
        onset = detector.detect(value)

        print(
            f"Input: {value:.2f} -> "
            f"Onset: {onset:.2f}"
        )


if __name__ == "__main__":
    main()
