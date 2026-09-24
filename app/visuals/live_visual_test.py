import sys
import time
from pathlib import Path

AUDIO_PATH = Path(__file__).resolve().parent.parent / "audio"

if str(AUDIO_PATH) not in sys.path:
    sys.path.insert(0, str(AUDIO_PATH))

from analyzer import AudioAnalyzer
from capture import AudioCapture
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from signal_processor import SignalProcessor


def make_bar(value, width=30):
    filled = int(value * width)

    return "█" * filled + "░" * (width - filled)


def main():
    capture = AudioCapture()
    analyzer = AudioAnalyzer()
    processor = SignalProcessor(smoothing=0.5)
    mapper = VisualParameterMapper()

    detectors = {
        "bass": OnsetDetector(threshold=0.2),
        "mids": OnsetDetector(threshold=0.2),
        "highs": OnsetDetector(threshold=0.2),
    }

    peaks = {
        "scale": 0.0,
        "movement": 0.0,
        "sparkle": 0.0,
        "impact": 0.0,
    }

    print("DreamWave Live Visual Test")
    print("--------------------------")
    print("Finding audio loopback device...")

    device = capture.find_device()

    print(f"Using: {device}")
    print("Play music in Opera.")
    print("Listening for 20 seconds...")
    print()

    capture.start()

    try:
        start = time.perf_counter()

        while time.perf_counter() - start < 20:
            samples = capture.read(numframes=2048)

            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            frequencies, magnitudes = analyzer.spectrum(
                samples,
                samplerate=48000,
            )

            bass = analyzer.band_energy(
                frequencies,
                magnitudes,
                20,
                250,
            )

            mids = analyzer.band_energy(
                frequencies,
                magnitudes,
                250,
                4000,
            )

            highs = analyzer.band_energy(
                frequencies,
                magnitudes,
                4000,
                16000,
            )

            bass_processed = processor.process(
                "bass",
                bass,
                0.0,
                10.0,
            )

            mids_processed = processor.process(
                "mids",
                mids,
                0.0,
                1.5,
            )

            highs_processed = processor.process(
                "highs",
                highs,
                0.0,
                0.6,
            )

            bass_onset = detectors["bass"].detect(
                bass_processed
            )

            mids_onset = detectors["mids"].detect(
                mids_processed
            )

            highs_onset = detectors["highs"].detect(
                highs_processed
            )

            result = mapper.map(
                bass=bass_processed,
                mids=mids_processed,
                highs=highs_processed,
                bass_onset=bass_onset,
                mids_onset=mids_onset,
                highs_onset=highs_onset,
            )

            for name, value in result.items():
                peaks[name] = max(
                    peaks[name],
                    value,
                )

            print(
                "\033[H\033[J"
                "DreamWave Live Visualizer\n"
                "=========================\n"
                f"Scale    [{make_bar(result['scale'])}] "
                f"{result['scale']:.2f}\n"
                f"Movement [{make_bar(result['movement'])}] "
                f"{result['movement']:.2f}\n"
                f"Sparkle  [{make_bar(result['sparkle'])}] "
                f"{result['sparkle']:.2f}\n"
                f"Impact   [{make_bar(result['impact'])}] "
                f"{result['impact']:.2f}\n"
                "\n"
                f"Bass     {bass_onset:.2f}\n"
                f"Mids     {mids_onset:.2f}\n"
                f"Highs    {highs_onset:.2f}\n"
                "\n"
                "PEAKS\n"
                f"Scale    {peaks['scale']:.2f}\n"
                f"Movement {peaks['movement']:.2f}\n"
                f"Sparkle  {peaks['sparkle']:.2f}\n"
                f"Impact   {peaks['impact']:.2f}\n"
            )

            time.sleep(0.05)

    finally:
        capture.stop()

    print("\nTest complete.")
    print("\nFinal Peaks:")

    for name, value in peaks.items():
        print(f"{name:8} -> {value:.2f}")


if __name__ == "__main__":
    main()