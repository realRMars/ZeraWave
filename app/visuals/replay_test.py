"""Development-only offline replay of a decoded WAV through the live pipeline."""

import argparse
import csv
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
from live_visual_test import analyze_samples
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from renderer import Renderer
from signal_processor import SignalProcessor, VisualSignalConditioner


def replay(path, speed=12.0, max_seconds=None, metrics_path=None):
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
        renderer = Renderer(title="DreamWave WAV Replay")
        rows = []
        chunk = 2048
        song_time = 0.0

        try:
            renderer.create()
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
                renderer.render(elapsed_time=song_time)
                renderer.swap_buffers()
                renderer.poll_events()
                rows.append({"seconds": song_time, "bass": frame.bass, "mids": frame.mids,
                             "highs": frame.highs, "flux": frame.flux, **result})
                song_time += len(samples) / rate
                if speed > 0:
                    time.sleep(min(0.02, (len(samples) / rate) / speed))
        finally:
            renderer.close()

    if metrics_path:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with metrics_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys()) if rows else None
            if writer:
                writer.writeheader()
                writer.writerows(rows)
    return song_time, rows


def main():
    parser = argparse.ArgumentParser(description="Replay a decoded WAV through DreamWave without audio playback.")
    parser.add_argument("wav", type=Path)
    parser.add_argument("--speed", type=float, default=12.0, help="Playback pacing multiplier (0 = no pacing).")
    parser.add_argument("--max-seconds", type=float, default=None)
    parser.add_argument("--metrics", type=Path, default=None)
    args = parser.parse_args()
    seconds, rows = replay(args.wav, args.speed, args.max_seconds, args.metrics)
    print(f"Replay complete: {seconds:.1f}s song time, {len(rows)} analyzed frames")


if __name__ == "__main__":
    main()
