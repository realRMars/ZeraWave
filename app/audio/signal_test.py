from signal_processor import SignalProcessor


def main():
    processor = SignalProcessor(smoothing=0.5)

    signals = [
        ("bass", 1.0),
        ("mids", 0.0),
        ("highs", 0.0),
        ("bass", 1.0),
        ("mids", 1.0),
        ("highs", 1.0),
        ("bass", 0.0),
        ("mids", 0.0),
        ("highs", 0.0),
    ]

    print("DreamWave Multi-Band Signal Test")
    print("---------------------------------")

    for name, value in signals:
        result = processor.process(
            name,
            value,
            0.0,
            1.0,
        )

        print(
            f"{name:5} | "
            f"Input: {value:.2f} -> "
            f"Output: {result:.2f}"
        )


if __name__ == "__main__":
    main()