from signal_processor import SignalProcessor


def main():
    processor = SignalProcessor()

    values = [-5.0, 0.0, 5.0, 10.0, 15.0]

    print("DreamWave Signal Normalization Test")
    print("-----------------------------------")

    for value in values:
        result = processor.normalize(value, 0.0, 10.0)
        print(f"Input: {value:.2f} -> Output: {result:.2f}")


if __name__ == "__main__":
    main()
