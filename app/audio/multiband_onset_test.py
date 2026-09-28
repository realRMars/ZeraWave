from onset_detector import OnsetDetector


def main():
    detectors = {
        "bass": OnsetDetector(threshold=0.2),
        "mids": OnsetDetector(threshold=0.2),
        "highs": OnsetDetector(threshold=0.2),
    }

    signals = [
        ("bass", 0.1),
        ("mids", 0.1),
        ("highs", 0.1),

        ("bass", 0.8),
        ("mids", 0.15),
        ("highs", 0.15),

        ("bass", 0.85),
        ("mids", 0.7),
        ("highs", 0.2),

        ("bass", 0.3),
        ("mids", 0.75),
        ("highs", 0.8),

        ("bass", 0.3),
        ("mids", 0.3),
        ("highs", 0.3),
    ]

    print("ZeraWave Multi-Band Onset Test")
    print("--------------------------------")

    for name, value in signals:
        onset = detectors[name].detect(value)

        print(
            f"{name:5} | "
            f"Input: {value:.2f} -> "
            f"Onset: {onset:.2f}"
        )


if __name__ == "__main__":
    main()