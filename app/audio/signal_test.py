from signal_processor import SignalProcessor, VisualSignalConditioner


def test_visual_conditioner():
    values = [
        0.0,
        0.02,
        1.0,
        0.0,
        0.0,
        0.2,
        0.4,
        0.6,
        1.0,
    ]
    conditioner = VisualSignalConditioner()
    outputs = [
        conditioner.condition("band", value)
        for value in values
    ]

    assert outputs[1] < 0.01
    assert outputs[2] <= 0.12
    assert outputs[3] < outputs[2]
    assert outputs[4] < outputs[3]
    assert outputs[5] > outputs[4]
    assert outputs[6] > outputs[5]
    assert all(0.0 <= value <= 1.0 for value in outputs)

    first = VisualSignalConditioner()
    second = VisualSignalConditioner()
    first_outputs = [first.condition("band", value) for value in values]
    second_outputs = [second.condition("band", value) for value in values]
    assert first_outputs == second_outputs

    sustained = VisualSignalConditioner()
    sustained_outputs = [
        sustained.condition("band", 1.0)
        for _ in range(40)
    ]
    assert sustained_outputs[-1] <= 1.0
    assert sustained_outputs[-1] > 0.99

    print("Visual conditioner assertions passed.")


def main():
    test_visual_conditioner()
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

    print("ZeraWave Multi-Band Signal Test")
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