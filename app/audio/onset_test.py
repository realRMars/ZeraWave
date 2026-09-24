from onset_detector import OnsetDetector


def main():
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

    print("DreamWave Onset Detection Test")
    print("--------------------------------")

    for value in values:
        onset = detector.detect(value)

        print(
            f"Input: {value:.2f} -> "
            f"Onset: {onset:.2f}"
        )


if __name__ == "__main__":
    main()