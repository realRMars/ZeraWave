"""Development-only offline replay of a decoded WAV through the live pipeline."""

import argparse
import csv
import json
import math
import sys
import time
import wave
from pathlib import Path

import numpy as np

VISUALS_PATH = Path(__file__).resolve().parent
AUDIO_PATH = VISUALS_PATH.parent / "audio"
for path in (VISUALS_PATH, AUDIO_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from analyzer import AudioAnalyzer
from live_visual_test import LIVE_STATES, analyze_samples
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from renderer import Renderer
from preview_layers import parse_layers, validate_layers, layers_at
from signal_processor import SignalProcessor, VisualSignalConditioner


def replay(path, speed=12.0, max_seconds=None, metrics_path=None, state="blend",
           capture_dir=None, capture_interval=15.0, states=None, layers=None, seed=None):
    if not math.isfinite(speed) or speed < 0:
        raise ValueError("Speed must be finite and nonnegative")
    if max_seconds is not None and (not math.isfinite(max_seconds) or max_seconds <= 0):
        raise ValueError("Duration must be finite and positive")
    if capture_dir is not None:
        if capture_interval <= 0:
            raise ValueError("Capture interval must be positive")
        from shader_test import save_png
        capture_dir.mkdir(parents=True, exist_ok=True)
    captures = []
    next_capture = 0.0
    debug_state = LIVE_STATES[state]
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        if rate != 48000 or width != 2:
            raise ValueError(f"Expected 48 kHz 16-bit WAV, got {rate} Hz / {width * 8}-bit")

        analyzer = AudioAnalyzer()
        processor = SignalProcessor(smoothing=0.5)
        conditioner = VisualSignalConditioner(quiet_threshold=0.06)
        mapper = VisualParameterMapper()
        detectors = {name: OnsetDetector(threshold=0.2) for name in ("bass", "mids", "highs")}
        renderer = Renderer(title="DreamWave WAV Replay", seed=seed)
        renderer.debug_state = debug_state
        renderer.debug_sequence = tuple(LIVE_STATES[name] for name in (states or ()))
        renderer.layer_profiles = validate_layers(layers or {})
        rows = []
        chunk = 2048
        song_time = 0.0

        try:
            renderer.create()
            replay_start = time.perf_counter()
            while not renderer.should_close() and song_time < (max_seconds or float("inf")):
                raw = audio.readframes(chunk)
                if not raw:
                    break
                samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                if channels > 1:
                    samples = samples.reshape(-1, channels)
                frame = analyze_samples(samples, analyzer, processor, conditioner, detectors)
                result = mapper.map_frame(frame)
                renderer.parameters.scale = result["scale"]
                renderer.parameters.movement = result["movement"]
                renderer.parameters.sparkle = result["sparkle"]
                renderer.parameters.impact = result["impact"]
                renderer.parameters.flux = frame.flux
                active_state = states[int(song_time // 28.) % len(states)] if states else state
                layer_mode, layer_mask = layers_at(renderer.layer_profiles, LIVE_STATES[active_state], song_time)
                renderer.render(elapsed_time=song_time)
                if capture_dir is not None and song_time >= next_capture:
                    width, height = renderer.ctx.screen.size
                    pixels = np.frombuffer(renderer.ctx.screen.read(components=3, alignment=1),
                        dtype=np.uint8).reshape(height, width, 3)
                    filename = f"frame-{song_time:08.3f}.png"
                    save_png(capture_dir / filename, pixels[::-1])
                    captures.append(dict(file=filename, seconds=song_time,
                        state=active_state, flow_rate=renderer.flow_rate, planet_visits=renderer.planet_visits, blast_events=list(renderer.blast_events), world_mix=renderer.blend_values, material_mix=list(renderer.program["u_material_mix"].value), shockwaves=list(renderer.shockwaves), layer_mode=layer_mode, layer_mask=layer_mask, bass=frame.bass, mids=frame.mids, highs=frame.highs,
                        flux=frame.flux, **result,
                        contrast=float(pixels.astype(float).std(axis=(0, 1)).mean()),
                        dark_fraction=float((pixels.max(axis=2) < 35).mean()),
                        clipped_fraction=float((pixels.max(axis=2) >= 250).mean())))
                    next_capture += capture_interval
                renderer.swap_buffers()
                renderer.poll_events()
                rows.append({"seconds": song_time, "state": active_state, "shockwave_count": len(renderer.shockwaves), "blast_count": len(renderer.blast_events), "planet_visits": renderer.planet_visits, "flow_rate": renderer.flow_rate, "layer_mode": layer_mode, "layer_mask": layer_mask, "bass": frame.bass, "mids": frame.mids,
                             "highs": frame.highs, "flux": frame.flux, **result})
                song_time += len(samples) / rate
                if speed > 0:
                    # Pace against song time, including drawing/capture overhead.
                    # Never drop analysis chunks; slower GPUs simply run behind.
                    delay = replay_start + song_time / speed - time.perf_counter()
                    if delay > 0:
                        time.sleep(delay)
        finally:
            renderer.close()

    if metrics_path:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with metrics_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys()) if rows else None
            if writer:
                writer.writeheader()
                writer.writerows(rows)
    if capture_dir is not None:
        (capture_dir / "captures.json").write_text(json.dumps(dict(
            source=str(path), state=state, states=states, layers=renderer.layer_profiles, song_seconds=song_time,
            analyzed_frames=len(rows), captures=captures,
            director_seed=renderer.director_seed, director_history=renderer.director_history,
            note="Decoded music through the real analysis and GPU pipeline; no audible playback."),
            indent=2), encoding="utf-8")
    return song_time, rows


def main():
    parser = argparse.ArgumentParser(description="Replay a decoded WAV through DreamWave without audio playback.")
    parser.add_argument("wav", type=Path)
    parser.add_argument("--speed", type=float, default=12.0, help="Playback pacing multiplier (0 = no pacing).")
    parser.add_argument("--max-seconds", type=float, default=None)
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--state", choices=tuple(LIVE_STATES), default="blend")
    parser.add_argument("--capture-dir", type=Path, help="Optional song-time PNG captures and input metadata.")
    parser.add_argument("--capture-interval", type=float, default=15., help="Song seconds between captures.")
    parser.add_argument("--states", nargs="+", choices=tuple(LIVE_STATES), help="Development cycle: hold each state for 28 song seconds.")
    parser.add_argument("--layers", type=parse_layers, default={}, help="Development per-world effect settings as JSON.")
    parser.add_argument("--seed", type=int, help="Repeatable visual choices for development replay.")
    args = parser.parse_args()
    seconds, rows = replay(args.wav, args.speed, args.max_seconds, args.metrics, args.state,
                           args.capture_dir, args.capture_interval, args.states, args.layers, args.seed)
    print(f"Replay complete: {seconds:.1f}s song time, {len(rows)} analyzed frames")


if __name__ == "__main__":
    main()
