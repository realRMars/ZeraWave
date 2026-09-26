from pathlib import Path
import time

import glfw
import moderngl
import math

from parameters import VisualParameters

VERTEX_SHADER = """
#version 330

in vec2 in_position;

void main()
{
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


class Renderer:
    # River Flow: bounds/smoothing for the animation rate driven by
    # the movement parameter (see render()).
    FLOW_FLOOR = 0.35
    FLOW_CEILING = 1.15
    FLOW_SMOOTHING_SECONDS = 0.6

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
        self.last_render_time = None
        self.impact_envelope = 0.0
        self.flow_time = 0.0
        self.flow_rate = self.FLOW_FLOOR
        self.parameters = VisualParameters()
        self.debug_state = 0

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

    def render(self, elapsed_time=None):
        if self.window is None:
            raise RuntimeError("Renderer has not been created")

        width, height = glfw.get_framebuffer_size(self.window)

        self.ctx.viewport = (0, 0, width, height)

        # Replay advances in song time; live callers retain the wall clock.
        current_time = (
            time.perf_counter() - self.start_time
            if elapsed_time is None else elapsed_time
        )
        if self.last_render_time is None:
            delta_time = 0.0
        else:
            delta_time = max(0.0, current_time - self.last_render_time)

        self.impact_envelope = max(
            self.parameters.impact,
            self.impact_envelope * math.exp(-delta_time * 6.0),
        )
        self.last_render_time = current_time

        # River Flow: movement sets a target current speed within a
        # bounded range, eased toward, then integrated over time.
        # Saturated movement is the strongest current, not a runaway clock.
        movement = max(0.0, min(1.0, self.parameters.movement))
        target_rate = (
            self.FLOW_FLOOR
            + (self.FLOW_CEILING - self.FLOW_FLOOR) * movement
        )

        if delta_time <= 0.0:
            ease = 1.0
        else:
            ease = 1.0 - math.exp(
                -delta_time / self.FLOW_SMOOTHING_SECONDS
            )

        self.flow_rate += (target_rate - self.flow_rate) * ease
        self.flow_time += delta_time * self.flow_rate
        visual_time = self.flow_time

        self.program["u_time"].value = visual_time
        self.program["u_drift_time"].value = current_time
        self.program["u_resolution"].value = (
            float(width),
            float(height),
        )
        self.program["u_intensity"].value = self.parameters.intensity
        self.program["u_distortion"].value = self.parameters.distortion
        self.program["u_scale"].value = self.parameters.scale
        self.program["u_sparkle"].value = self.parameters.sparkle
        self.program["u_impact"].value = self.impact_envelope
        self.program["u_flux"].value = self.parameters.flux
        self.program["u_debug_state"].value = float(self.debug_state)
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

    def should_close(self):
        return glfw.window_should_close(self.window)

    def poll_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def get_time(self):
        if self.start_time is None:
            return 0.0

        return time.perf_counter() - self.start_time

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
