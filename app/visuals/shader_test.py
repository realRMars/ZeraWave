import math
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import glfw
import moderngl

from renderer import Renderer, VERTEX_SHADER


def capture(output, seconds, profile="standard"):
    """Save a reproducible synthetic frame and GPU-evaluated state weights."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=640, height=360, title="DreamWave capture")
    source = (Path(__file__).parent / "shaders/dream.frag").read_text(encoding="utf-8")
    values = dict(u_time=seconds * .75, u_drift_time=seconds,
                  u_resolution=(640., 360.), u_scale=.3, u_flux=.2,
                  u_sparkle=.2, u_impact=.05, u_intensity=1., u_distortion=1.)
    if profile == "quiet":
        values.update(u_scale=.05, u_flux=.02, u_sparkle=.05, u_impact=0.)
    elif profile == "active":
        values.update(u_scale=.45, u_flux=.45, u_sparkle=.25, u_impact=.25)
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.render()
        for name, value in values.items():
            renderer.program[name].value = value
        renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
        pixels = np.frombuffer(renderer.ctx.screen.read(components=3),
                               dtype=np.uint8).reshape(360, 640, 3)
        stem = output / f"frame-{seconds:g}"
        stem.with_suffix(".ppm").write_bytes(
            b"P6\n640 360\n255\n" + pixels[::-1].tobytes())
        weights = {}
        anchor = "fragColor = vec4(color, 1.0);"
        assert source.count(anchor) == 1
        for name in ("organic", "tunnel", "fractal", "geometric", "cosmic", "horizon"):
            probe = renderer.ctx.program(vertex_shader=VERTEX_SHADER,
                fragment_shader=source.replace(anchor,
                    f"fragColor = vec4({name}_weight / weight_sum, 0.0, 0.0, 1.0);"))
            vao = None
            try:
                vao = renderer.ctx.simple_vertex_array(probe, renderer.vertices, "in_position")
                for uniform, value in values.items():
                    if uniform in probe:
                        probe[uniform].value = value
                vao.render(mode=moderngl.TRIANGLE_STRIP)
                weights[name] = renderer.ctx.screen.read(components=3)[0] / 255.
            finally:
                if vao is not None:
                    vao.release()
                probe.release()
        metadata = dict(uniforms=values, normalized_weights_8bit=weights,
                        shader_sha256=hashlib.sha256(source.encode()).hexdigest(),
                        gpu=renderer.ctx.info.get("GL_RENDERER"),
                        note="Synthetic fixed inputs; not recorded live audio. Weights quantized to 1/255.")
        stem.with_suffix(".json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        print(f"Saved {stem}; weights: {weights}")
    finally:
        renderer.close()


def sweep(output):
    """Render fixed inputs/times on the real GPU; no audio capture involved."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=320, height=180, title="DreamWave diagnostic")
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.render()
        results = []
        for level in (0.3, 0.7, 1.0):
            for seconds in range(0, 241, 4):
                for name, value in {
                    "u_time": seconds * 0.75, "u_drift_time": seconds,
                    "u_scale": level, "u_flux": level,
                    "u_sparkle": level, "u_impact": 0.2,
                }.items():
                    renderer.program[name].value = value
                renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
                pixels = np.frombuffer(renderer.ctx.screen.read(components=3),
                                       dtype=np.uint8).reshape(180, 320, 3)
                contrast = float(pixels.astype(float).std(axis=(0, 1)).mean())
                results.append((contrast, level, seconds))
                if seconds in (48, 64, 80, 108) or contrast < 1.0:
                    path = output / f"level-{level}-time-{seconds}.ppm"
                    path.write_bytes(b"P6\n320 180\n255\n" + pixels[::-1].tobytes())
        print("Lowest spatial contrast (8-bit RGB standard deviation):")
        for result in sorted(results)[:15]:
            print(result)
        (output / "metrics.csv").write_text(
            "contrast,level,seconds\n" + "".join(
                f"{c},{l},{s}\n" for c, l, s in results), encoding="utf-8")
        # These high-input states previously produced near-uniform or solid
        # frames. This guards the reproduced defect, not aesthetic quality.
        for contrast, level, seconds in results:
            if level == 1.0 and seconds in (80, 132, 196, 204):
                assert contrast > 5.0, (
                    f"Spatial structure lost at {seconds}s: {contrast:.3f}"
                )
        print(f"Rendered {len(results)} frames; diagnostics: {output}")
    finally:
        renderer.close()


def main():
    renderer = Renderer(
        width=1280,
        height=720,
        title="DreamWave - Parameter Test",
    )

    try:
        renderer.create()

        while not renderer.should_close():
            current_time = renderer.get_time()

            renderer.parameters.intensity = 0.5 + 0.5 * math.sin(
                current_time * 1.5
            )

            renderer.parameters.movement = 2.0
            renderer.parameters.distortion = 2.0
            renderer.parameters.scale = 2.0
            renderer.render()
            renderer.swap_buffers()
            renderer.poll_events()

    finally:
        renderer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", type=Path)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--seconds", type=float, default=100.)
    parser.add_argument("--profile", choices=("standard", "quiet", "active"), default="standard")
    args = parser.parse_args()
    if args.capture:
        capture(args.capture, args.seconds, args.profile)
    elif args.sweep:
        sweep(args.sweep)
    else:
        main()
