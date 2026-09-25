from signal_processor import SignalProcessor


def main():
    fixed = SignalProcessor(smoothing=0.0)
    adaptive = SignalProcessor(smoothing=0.0, adaptive_window=20)

    phases = [
        ("Warmup", [
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0,
        ]),
        ("Dense", [7.0, 8.0, 9.0, 10.0] * 6),
        ("Outlier", [100.0]),
        ("Return", [7.0, 8.0, 9.0]),
        ("Silence", [0.0] * 4),
        ("Recovery", [7.0, 8.0, 9.0]),
    ]

    print("DreamWave Signal Normalization Test")
    print("-----------------------------------")
    print("Input  | Fixed | Adaptive")

    dense_fixed = []
    dense_adaptive = []
    silence_adaptive = []
    recovery_adaptive = []

    for name, values in phases:
        print(f"\n{name}")

        for value in values:
            fixed_result = fixed.process(
                "band",
                value,
                0.0,
                10.0,
            )
            adaptive_result = adaptive.process_adaptive(
                "band",
                value,
                0.0,
                10.0,
            )

            if name == "Dense":
                dense_fixed.append(fixed_result)
                dense_adaptive.append(adaptive_result)
            elif name == "Silence":
                silence_adaptive.append(adaptive_result)
            elif name == "Recovery":
                recovery_adaptive.append(adaptive_result)

            print(
                f"{value:5.1f}  | {fixed_result:.2f}   | "
                f"{adaptive_result:.2f}"
            )

    assert max(dense_adaptive) - min(dense_adaptive) > (
        max(dense_fixed) - min(dense_fixed)
    )
    assert silence_adaptive == [0.0] * len(silence_adaptive)
    assert all(0.0 <= value <= 1.0 for value in recovery_adaptive)

    print("\nAdaptive range assertions passed.")


if __name__ == "__main__":
    main()
