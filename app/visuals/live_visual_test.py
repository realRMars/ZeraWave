import sys
from pathlib import Path

AUDIO_PATH = Path(__file__).resolve().parent.parent / "audio"

if str(AUDIO_PATH) not in sys.path:
    sys.path.insert(0, str(AUDIO_PATH))

from analyzer import AudioAnalyzer
from audio_frame import AudioFrame
from capture import AudioCapture
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from renderer import Renderer
from signal_processor import SignalProcessor, VisualSignalConditioner


def make_bar(value, width=30):
    filled = int(value * width)

    return "█" * filled + "░" * (width - filled)


def main():
    capture = AudioCapture()
    analyzer = AudioAnalyzer()
    processor = SignalProcessor(smoothing=0.5)
    # Wider quiet dead-zone than the class default (0.03): gives the
    # visual room to sit still at low signal instead of twitching on
    # every small fluctuation, per the "more threshold to breathe" ask.
    conditioner = VisualSignalConditioner(quiet_threshold=0.06)
    mapper = VisualParameterMapper()
    renderer = Renderer()

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
    print("Listening until the window closes...")
    print()

    try:
        renderer.create()
        capture.start()

        while not renderer.should_close():
            samples = capture.read(numframes=2048)

            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            frequencies, magnitudes = analyzer.spectrum(
                samples,
                samplerate=48000,
            )

            flux_processed = conditioner.condition(
                "flux",
                processor.process(
                    "flux",
                    # Provisional scale: 10s live sample showed raw
                    # flux mean ~40, max ~344; 90 avoids near-constant
                    # saturation while still reaching 1.0 on real spikes.
                    analyzer.spectral_flux(magnitudes),
                    0.0,
                    90.0,
                ),
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

            # Recalibrated ceilings: the previous values (10.0/1.5/0.6)
            # were saturating to 1.0 almost constantly during real
            # playback, leaving no room to breathe between quiet and
            # loud. Raised ~50-65% so typical loud passages sit below
            # the ceiling instead of pinning it -- verify by ear and
            # retune further if it still saturates too easily.
            bass_processed = processor.process(
                "bass",
                bass,
                0.0,
                16.0,
            )

            mids_processed = processor.process(
                "mids",
                mids,
                0.0,
                2.4,
            )

            highs_processed = processor.process(
                "highs",
                highs,
                0.0,
                1.0,
            )

            bass_processed = conditioner.condition(
                "bass",
                bass_processed,
            )
            mids_processed = conditioner.condition(
                "mids",
                mids_processed,
            )
            highs_processed = conditioner.condition(
                "highs",
                highs_processed,
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

            frame = AudioFrame(
                bass_processed,
                mids_processed,
                highs_processed,
                bass_onset,
                mids_onset,
                highs_onset,
                flux=flux_processed,
            )
            result = mapper.map_frame(frame)

            renderer.parameters.scale = result["scale"]
            renderer.parameters.movement = result["movement"]
            renderer.parameters.sparkle = result["sparkle"]
            renderer.parameters.impact = result["impact"]
            renderer.parameters.flux = frame.flux
            renderer.render()
            renderer.swap_buffers()
            renderer.poll_events()

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
                f"Bass     {bass_processed:.2f}\n"
                f"Mids     {mids_processed:.2f}\n"
                f"Highs    {highs_processed:.2f}\n"
                f"Flux     {frame.flux:.2f}\n"
                "\n"
                "PEAKS\n"
                f"Scale    {peaks['scale']:.2f}\n"
                f"Movement {peaks['movement']:.2f}\n"
                f"Sparkle  {peaks['sparkle']:.2f}\n"
                f"Impact   {peaks['impact']:.2f}\n"
            )

    finally:
        try:
            capture.stop()
        finally:
            renderer.close()

    print("\nTest complete.")
    print("\nFinal Peaks:")

    for name, value in peaks.items():
        print(f"{name:8} -> {value:.2f}")


if __name__ == "__main__":
    main()