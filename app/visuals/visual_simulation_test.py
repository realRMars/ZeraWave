import math
import time

from parameter_mapper import VisualParameterMapper


def make_bar(value, width=30):
    filled = int(value * width)

    return "█" * filled + "░" * (width - filled)


def main():
    mapper = VisualParameterMapper()

    print("DreamWave Visual Simulation Test")
    print("---------------------------------")
    print("Simulating reactive visual parameters...")
    print("Press Ctrl+C to stop.")
    print()

    start = time.perf_counter()

    try:
        while True:
            elapsed = time.perf_counter() - start

            bass = (math.sin(elapsed * 2.0) + 1.0) / 2.0
            mids = (math.sin(elapsed * 3.5) + 1.0) / 2.0
            highs = (math.sin(elapsed * 7.0) + 1.0) / 2.0

            bass_onset = max(
                0.0,
                math.sin(elapsed * 2.0),
            )

            mids_onset = max(
                0.0,
                math.sin(elapsed * 3.5),
            )

            highs_onset = max(
                0.0,
                math.sin(elapsed * 7.0),
            )

            result = mapper.map(
                bass=bass,
                mids=mids,
                highs=highs,
                bass_onset=bass_onset,
                mids_onset=mids_onset,
                highs_onset=highs_onset,
            )

            print(
                "\033[H\033[J"
                "DreamWave Visual Simulation\n"
                "---------------------------\n"
                f"Scale    [{make_bar(result['scale'])}] "
                f"{result['scale']:.2f}\n"
                f"Movement [{make_bar(result['movement'])}] "
                f"{result['movement']:.2f}\n"
                f"Sparkle  [{make_bar(result['sparkle'])}] "
                f"{result['sparkle']:.2f}\n"
                f"Impact   [{make_bar(result['impact'])}] "
                f"{result['impact']:.2f}\n"
            )

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nSimulation stopped.")


if __name__ == "__main__":
    main()