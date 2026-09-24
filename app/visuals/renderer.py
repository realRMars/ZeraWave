from pathlib import Path
import time

import glfw
import moderngl


VERTEX_SHADER = """
#version 330

in vec2 in_position;

void main()
{
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


class Renderer:
    def __init__(self, width=1280, height=720, title="DreamWave"):
        self.width = width
        self.height = height
        self.title = title

        self.window = None
        self.ctx = None
        self.program = None
        self.vertices = None
        self.vao = None

        self.start_time = None

    def create(self):
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

        self.window = glfw.create_window(
            self.width,
            self.height,
            self.title,
            None,
            None,
        )

        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")

        glfw.make_context_current(self.window)

        self.ctx = moderngl.create_context()

        shader_path = Path(__file__).parent / "shaders" / "dream.frag"
        fragment_shader = shader_path.read_text(encoding="utf-8")

        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=fragment_shader,
        )

        self.vertices = self.ctx.buffer(
            data=(
                b"\x00\x00\x80\xbf\x00\x00\x80\xbf"
                b"\x00\x00\x80\x3f\x00\x00\x80\xbf"
                b"\x00\x00\x80\xbf\x00\x00\x80\x3f"
                b"\x00\x00\x80\x3f\x00\x00\x80\x3f"
            )
        )

        self.vao = self.ctx.simple_vertex_array(
            self.program,
            self.vertices,
            "in_position",
        )

        self.start_time = time.perf_counter()

    def render(self):
        if self.window is None:
            raise RuntimeError("Renderer has not been created")

        width, height = glfw.get_framebuffer_size(self.window)

        self.ctx.viewport = (0, 0, width, height)

        current_time = time.perf_counter() - self.start_time

        self.program["u_time"].value = current_time
        self.program["u_resolution"].value = (
            float(width),
            float(height),
        )

        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

    def should_close(self):
        return glfw.window_should_close(self.window)

    def poll_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def close(self):
        if self.vao is not None:
            self.vao.release()

        if self.vertices is not None:
            self.vertices.release()

        if self.program is not None:
            self.program.release()

        if self.ctx is not None:
            self.ctx.release()

        if self.window is not None:
            glfw.destroy_window(self.window)

        glfw.terminate()