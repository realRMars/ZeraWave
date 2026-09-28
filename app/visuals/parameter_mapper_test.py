import sys
from pathlib import Path

AUDIO_PATH = Path(__file__).resolve().parent.parent / "audio"

if str(AUDIO_PATH) not in sys.path:
    sys.path.insert(0, str(AUDIO_PATH))

from audio_frame import AudioFrame
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

    print("ZeraWave Visual Parameter Mapper Test")
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

        frame = AudioFrame(
            bass,
            mids,
            highs,
            bass_onset,
            mids_onset,
            highs_onset,
        )
        assert mapper.map_frame(frame) == result

    print("\nmap_frame parity assertions passed.")


if __name__ == "__main__":
    main()