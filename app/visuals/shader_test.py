import math
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

import numpy as np
import glfw
import moderngl

from renderer import Renderer, VERTEX_SHADER

STATES = {"blend": 0, "organic": 1, "geometric": 2, "cosmic": 3, "transition": 4, "canvas": 5}


def save_png(path, pixels):
    """Write RGB captures using the standard library; no image dependency."""
    height, width, _ = pixels.shape
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\x00' + row.tobytes() for row in pixels)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def capture(output, seconds, profile="standard", debug_state=0):
    """Save a reproducible synthetic frame and GPU-evaluated state weights."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=640, height=360, title="DreamWave capture")
    source = (Path(__file__).parent / "shaders/dream.frag").read_text(encoding="utf-8")
    values = dict(u_time=seconds * .75, u_star_time=seconds, u_drift_time=seconds,
                  u_resolution=(640., 360.), u_scale=.3, u_flux=.2,
                  u_sparkle=.2, u_impact=.05, u_intensity=1., u_distortion=1.,
                  u_debug_state=float(debug_state))
    if profile == "quiet":
        values.update(u_scale=.05, u_flux=.02, u_sparkle=.05, u_impact=0.)
    elif profile == "active":
        values.update(u_scale=.45, u_flux=.45, u_sparkle=.25, u_impact=.25)
    elif profile == "chorus":
        values.update(u_scale=.85, u_flux=.95, u_sparkle=.80, u_impact=.55)
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
        save_png(stem.with_suffix('.png'), pixels[::-1])
        weights = {}
        anchor = "fragColor = vec4(color, 1.0);"
        assert source.count(anchor) == 1
        # Cosmic returns before the blend weights exist; do not label its
        # rendered RGB as a state-weight probe.
        for name in (() if debug_state == 3 else ("organic", "tunnel", "fractal", "geometric", "cosmic", "horizon", "root_mix", "cosmic_takeover")):
            expression = name if name in ("root_mix", "cosmic_takeover") else f"{name}_weight / weight_sum"
            probe = renderer.ctx.program(vertex_shader=VERTEX_SHADER,
                fragment_shader=source.replace(anchor,
                    f"fragColor = vec4({expression}, 0.0, 0.0, 1.0);"))
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
                    "u_time": seconds * 0.75, "u_star_time": seconds, "u_drift_time": seconds,
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


def geometric_test(output):
    """Guard isolated corridor visibility through both turn directions."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=320, height=180, title="Geometric surface test")
    results = []
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.render()
        renderer.program['u_debug_state'].value = 2.0
        for profile, scale, flux, sparkle, impact in (
            ('quiet', .05, .02, .05, 0.),
            ('active', .45, .45, .25, .25),
            ('chorus', .85, .95, .80, .55),
        ):
            for seconds in np.arange(0., 70.01, .5):
                for name, value in dict(u_time=float(seconds * .75),
                        u_star_time=float(seconds), u_drift_time=float(seconds),
                        u_scale=scale, u_flux=flux, u_sparkle=sparkle,
                        u_impact=impact, u_intensity=1., u_distortion=1.).items():
                    renderer.program[name].value = value
                renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
                pixels = np.frombuffer(renderer.ctx.screen.read(components=3),
                    dtype=np.uint8).reshape(180, 320, 3)
                contrast = float(pixels.astype(float).std(axis=(0, 1)).mean())
                results.append((profile, float(seconds), contrast))
                if seconds in (18., 30., 32., 33., 64., 66., 67.) or contrast < 2.:
                    save_png(output / f'{profile}-{seconds:g}.png', pixels[::-1])
                assert contrast > 2., (profile, seconds, 'Corridor lost', contrast)
        (output / 'verification.json').write_text(json.dumps(dict(
            frames=len(results), minimum_contrast=min(r[2] for r in results),
            samples=results, note='Synthetic GPU visibility, not motion/aesthetic acceptance.'),
            indent=2), encoding='utf-8')
        print(f'PASS: {len(results)} isolated Geometric frames; '
              f'minimum spatial contrast {min(r[2] for r in results):.3f}; {output}')
    finally:
        renderer.close()


def handoff_test(output):
    """Exercise the actual transition branch, including boundaries and hold."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=640, height=360, title="Cosmic handoff test")
    def frame(seconds):
        renderer.render(elapsed_time=seconds)
        return np.frombuffer(renderer.ctx.screen.read(components=3),
            dtype=np.uint8).reshape(360, 640, 3).copy()
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.debug_state = 4
        renderer.parameters.intensity = 1.0
        renderer.parameters.distortion = 1.0
        renderer.parameters.scale = .45
        renderer.parameters.movement = .45
        renderer.parameters.sparkle = .25
        renderer.parameters.flux = .45
        # Reset renderer time integration for independent reproducible samples.
        captures = []
        for seconds in (0., 7., 11., 18., 24., 29., 35., 40., 47.):
            renderer.last_render_time = 0.0
            renderer.flow_time = 0.0
            renderer.star_time = 0.0
            renderer.star_rate = 1.0
            pixels = frame(seconds)
            assert pixels.std() > 3, f'Blank frame at {seconds}'
            save_png(output / f'stage-{seconds:g}.png', pixels[::-1])
            captures.append(pixels[::-1])
            if seconds in (11.,18.,24.):
                # During hold the original foreground cannot fill deep space.
                corner = pixels[:60, :60]
                assert (corner.max(axis=2) < 12).mean() > .8, 'Foreground leaks into space'
        sheet = np.concatenate([np.concatenate(captures[i:i+3], axis=1)
            for i in (0,3,6)], axis=0)
        save_png(output / 'contact-sheet.png', sheet)
        jumps = []
        for boundary in (3., 11., 24., 35., 40.):
            renderer.last_render_time = 0.0
            renderer.flow_time = 0.0
            renderer.star_time = 0.0
            renderer.star_rate = 1.0
            # Probe the boundary limit (2 ms apart), not ordinary animation
            # motion: the fractal source can change rapidly over a whole frame.
            a = frame(boundary - .001)
            b = frame(boundary + .001)
            delta = float(np.abs(a.astype(float)-b.astype(float)).mean())
            assert delta < 4., f'Transition discontinuity at {boundary}s: {delta}'
            jumps.append((boundary, delta))
        (output / 'verification.json').write_text(json.dumps(dict(
            boundary_mean_pixel_deltas=jumps, frames=19,
            note='Synthetic GPU transition test; not live audio or aesthetic acceptance.'), indent=2))
        print(f'PASS: 19 transition GPU frames, space isolation and boundary continuity; {output}')
    finally:
        renderer.close()


def main(debug_state=0):
    renderer = Renderer(
        width=1280,
        height=720,
        title="DreamWave - " + next(name for name, value in STATES.items() if value == debug_state),
    )
    print(f"State preview active: {debug_state}", flush=True)

    try:
        renderer.create()
        renderer.debug_state = debug_state

        while not renderer.should_close():
            current_time = renderer.get_time()

            renderer.parameters.intensity = 1.0
            renderer.parameters.movement = 0.45
            renderer.parameters.distortion = 1.0
            renderer.parameters.scale = 0.45
            renderer.parameters.sparkle = 0.25
            renderer.parameters.flux = 0.45
            renderer.render()
            renderer.swap_buffers()
            renderer.poll_events()

    finally:
        renderer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sweep", type=Path)
    parser.add_argument("--handoff-test", type=Path)
    parser.add_argument("--geometric-test", type=Path)
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--seconds", type=float, default=100.)
    parser.add_argument("--profile", choices=("standard", "quiet", "active", "chorus"), default="standard")
    parser.add_argument("--state", choices=tuple(STATES), default="blend")
    args = parser.parse_args()
    if args.geometric_test:
        geometric_test(args.geometric_test)
    elif args.handoff_test:
        handoff_test(args.handoff_test)
    elif args.capture:
        capture(args.capture, args.seconds, args.profile,
                STATES[args.state])
    elif args.sweep:
        sweep(args.sweep)
    else:
        main(STATES[args.state])
