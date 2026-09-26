import math
import argparse
from pathlib import Path

import numpy as np
import glfw
import moderngl

from renderer import Renderer


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
    args = parser.parse_args()
    if args.sweep:
        sweep(args.sweep)
    else:
        main()
