from signal_processor import SignalProcessor


def main():
    processor = SignalProcessor(smoothing=0.5)

    values = [0.0, 1.0, 1.0, 0.0, 0.0]

    print("DreamWave Signal Smoothing Test")
    print("--------------------------------")

    for value in values:
        result = processor.smooth(value)
        print(f"Input: {value:.2f} -> Output: {result:.2f}")


if __name__ == "__main__":
    main()
