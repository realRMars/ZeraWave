from parameter_mapper import VisualParameterMapper


def main():
    mapper = VisualParameterMapper()

    scenarios = [
        (
            "Quiet",
            0.1,
            0.1,
            0.1,
            0.0,
            0.0,
            0.0,
        ),
        (
            "Normal",
            0.5,
            0.4,
            0.3,
            0.2,
            0.1,
            0.0,
        ),
        (
            "Impact",
            0.9,
            0.7,
            0.5,
            0.8,
            0.4,
            0.6,
        ),
    ]

    print("DreamWave Visual Parameter Mapper Test")
    print("---------------------------------------")

    for (
        name,
        bass,
        mids,
        highs,
        bass_onset,
        mids_onset,
        highs_onset,
    ) in scenarios:
        result = mapper.map(
            bass,
            mids,
            highs,
            bass_onset,
            mids_onset,
            highs_onset,
        )

        print(f"\n{name}")

        for parameter, value in result.items():
            print(
                f"{parameter:8} -> "
                f"{value:.2f}"
            )


if __name__ == "__main__":
    main()