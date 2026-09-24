from renderer import Renderer


def main():
    renderer = Renderer(
        width=1280,
        height=720,
        title="DreamWave - First Dream",
    )

    try:
        renderer.create()

        while not renderer.should_close():
            renderer.render()
            renderer.swap_buffers()
            renderer.poll_events()

    finally:
        renderer.close()


if __name__ == "__main__":
    main()