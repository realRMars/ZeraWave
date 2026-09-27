import argparse
import sys
from pathlib import Path

VISUALS_PATH = Path(__file__).resolve().parent
AUDIO_PATH = VISUALS_PATH.parent / "audio"

for path in (VISUALS_PATH, AUDIO_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from analyzer import AudioAnalyzer
from audio_frame import AudioFrame
from capture import AudioCapture
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from renderer import Renderer
from preview_layers import parse_layers, validate_layers
from signal_processor import SignalProcessor, VisualSignalConditioner

LIVE_STATES = {"blend": 0, "organic": 1, "geometric": 2, "cosmic": 3,
               "transition": 4, "canvas": 5, "water": 6, "sea": 7,
               "dyes": 8, "rain": 9, "waterfall": 10, "membrane": 11, "roots": 12, "currents": 13, "fire": 14, "molten": 15, "fire_cycle": 16, "firescape": 17, "aftershock": 18, "windstreams": 19, "stormfront": 20, "vortex": 21, "citadel": 22, "air": 23, "dunes": 24, "strata": 25, "cavern": 26, "earth": 27}


def make_bar(value, width=30):
    filled = int(value * width)

    return "█" * filled + "░" * (width - filled)


def analyze_samples(samples, analyzer, processor, conditioner, detectors):
    """Shared live/replay analysis; detect events before visual slew limiting."""
    if samples.ndim > 1:
        samples = samples.mean(axis=1)

    frequencies, magnitudes = analyzer.spectrum(
        samples,
        samplerate=48000,
    )

    flux_processed = conditioner.condition(
        "flux",
        processor.process_adaptive(
            "flux",
            # Provisional scale: 10s live sample showed raw
            # flux mean ~40, max ~344; 180 gives ordinary passages
            # room below the ceiling while preserving headroom for spikes.
            analyzer.spectral_flux(magnitudes),
            0.0,
            180.0,
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
    # loud. Raised the mids ceiling further after replay evidence
    # showed persistent saturation in ordinary passages.
    bass_processed = processor.process(
        "bass",
        bass,
        0.0,
        16.0,
    )

    mids_processed = processor.process_adaptive(
        "mids",
        mids,
        0.0,
        4.0,
    )

    highs_processed = processor.process(
        "highs",
        highs,
        0.0,
        1.0,
    )

    # Detect normalized transients before visual conditioning caps each rise
    # at 0.12, below the existing onset threshold of 0.2. Continuous controls
    # still use exactly the same normalization, smoothing and conditioning.
    bass_onset = detectors["bass"].detect(bass_processed)
    mids_onset = detectors["mids"].detect(mids_processed)
    highs_onset = detectors["highs"].detect(highs_processed)

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

    frame = AudioFrame(
        bass_processed,
        mids_processed,
        highs_processed,
        bass_onset,
        mids_onset,
        highs_onset,
        flux=flux_processed,
    )
    return frame


def main(state="blend", states=None, layers=None):
    capture = AudioCapture()
    analyzer = AudioAnalyzer()
    processor = SignalProcessor(smoothing=0.5)
    # Wider quiet dead-zone than the class default (0.03): gives the
    # visual room to sit still at low signal instead of twitching on
    # every small fluctuation, per the "more threshold to breathe" ask.
    conditioner = VisualSignalConditioner(quiet_threshold=0.06)
    mapper = VisualParameterMapper()
    renderer = Renderer(title=f"DreamWave - live {state}")
    renderer.debug_state = LIVE_STATES[state]
    renderer.debug_sequence = tuple(LIVE_STATES[name] for name in (states or ()))
    renderer.layer_profiles = validate_layers(layers or {})

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
    print(f"Live state: {state}. Play music through your default audio output.")
    print("Listening until the window closes...")
    print()

    try:
        renderer.create()
        capture.start()

        while not renderer.should_close():
            samples = capture.read(numframes=2048)

            frame = analyze_samples(samples, analyzer, processor, conditioner, detectors)
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
                f"Live state: {state}\n"
                f"Scale    [{make_bar(result['scale'])}] "
                f"{result['scale']:.2f}\n"
                f"Movement [{make_bar(result['movement'])}] "
                f"{result['movement']:.2f}\n"
                f"Sparkle  [{make_bar(result['sparkle'])}] "
                f"{result['sparkle']:.2f}\n"
                f"Impact   [{make_bar(result['impact'])}] "
                f"{result['impact']:.2f}\n"
                "\n"
                f"Bass     {frame.bass:.2f}\n"
                f"Mids     {frame.mids:.2f}\n"
                f"Highs    {frame.highs:.2f}\n"
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
    parser = argparse.ArgumentParser(description="DreamWave with live system audio.")
    parser.add_argument("--state", choices=tuple(LIVE_STATES), default="blend",
                        help="blend: normal flow; canvas: hold planet; transition: 40-second diagnostic cycle; water: isolated liquid world")
    parser.add_argument("--states", nargs="+", choices=tuple(LIVE_STATES), help="Development cycle: hold each state for 28 seconds.")
    parser.add_argument("--layers", type=parse_layers, default={}, help="Development per-world effect settings as JSON.")
    args = parser.parse_args()
    main(args.state, args.states, args.layers)
