from pathlib import Path
import time

import glfw
import moderngl


WIDTH = 1280
HEIGHT = 720


VERTEX_SHADER = """
#version 330

in vec2 in_position;

void main()
{
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


def main():
    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)

    window = glfw.create_window(
        WIDTH,
        HEIGHT,
        "DreamWave - First Dream",
        None,
        None,
    )

    if not window:
        glfw.terminate()
        raise RuntimeError("Failed to create GLFW window")

    glfw.make_context_current(window)

    ctx = moderngl.create_context()

    shader_path = Path(__file__).parent / "shaders" / "dream.frag"
    fragment_shader = shader_path.read_text(encoding="utf-8")

    program = ctx.program(
        vertex_shader=VERTEX_SHADER,
        fragment_shader=fragment_shader,
    )

    vertices = ctx.buffer(
        data=(
            b"\x00\x00\x80\xbf\x00\x00\x80\xbf"
            b"\x00\x00\x80\x3f\x00\x00\x80\xbf"
            b"\x00\x00\x80\xbf\x00\x00\x80\x3f"
            b"\x00\x00\x80\x3f\x00\x00\x80\x3f"
        )
    )

    vao = ctx.simple_vertex_array(
        program,
        vertices,
        "in_position",
    )

    start_time = time.perf_counter()

    while not glfw.window_should_close(window):
        width, height = glfw.get_framebuffer_size(window)

        ctx.viewport = (0, 0, width, height)

        current_time = time.perf_counter() - start_time

        program["u_time"].value = current_time
        program["u_resolution"].value = (float(width), float(height))

        vao.render(mode=moderngl.TRIANGLE_STRIP)

        glfw.swap_buffers(window)
        glfw.poll_events()

    vao.release()
    vertices.release()
    program.release()
    ctx.release()

    glfw.destroy_window(window)
    glfw.terminate()


if __name__ == "__main__":
    main()