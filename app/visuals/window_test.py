import glfw
import moderngl


WIDTH = 1280
HEIGHT = 720


def main():
    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")

    window = glfw.create_window(
        WIDTH,
        HEIGHT,
        "DreamWave - GPU Test",
        None,
        None,
    )

    if not window:
        glfw.terminate()
        raise RuntimeError("Failed to create GLFW window")

    glfw.make_context_current(window)

    ctx = moderngl.create_context()

    print("DreamWave GPU window started")
    print(f"OpenGL version: {ctx.version_code}")
    print(f"OpenGL vendor: {ctx.info.get('GL_VENDOR')}")
    print(f"OpenGL renderer: {ctx.info.get('GL_RENDERER')}")

    while not glfw.window_should_close(window):
        ctx.clear(0.02, 0.02, 0.03, 1.0)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.destroy_window(window)
    glfw.terminate()


if __name__ == "__main__":
    main()