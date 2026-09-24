import math

from renderer import Renderer


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
    main()