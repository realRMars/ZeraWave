"""GPU regression: opaque moon centers and planetary occlusion over full orbits."""
import math
from pathlib import Path
import glfw
import moderngl
import numpy as np
from renderer import Renderer, VERTEX_SHADER

def material(normal, index, time):
    """Independent CPU reference for the three sphere-space albedos."""
    def mix(a, b, t):
        return np.array(a) * (1-t) + np.array(b) * t
    def smooth(a, b, v):
        x = np.clip((v-a)/(b-a), 0, 1)
        return x*x*(3-2*x)
    spin = time * .12
    x, y, z = normal
    q = np.array([math.cos(spin)*x+math.sin(spin)*z, y,
                  -math.sin(spin)*x+math.cos(spin)*z])
    drift = time * .18
    fold = math.sin(q[1]*5 + math.sin(q[2]*4+drift))
    dye = .5 + .5*math.sin(q[0]*5+fold*2+drift)
    if index == 0:
        ink = mix([.08,.85,.95], [.95,.08,.55], dye)
        vein = (.5+.5*math.sin(q[1]*9+fold*3-drift))**8
        return mix(ink, [.85,1,.62], vein*.65)
    if index == 1:
        heat = .5+.5*math.sin(q[1]*7+fold*2-drift*2)
        flame = mix([.95,.08,.015], [1,.50,.04], heat)
        flame = mix(flame, [.08,.40,1], smooth(.45,.78,heat))
        return mix(flame, [.85,.96,1], smooth(.78,1,heat))
    layers = np.linalg.norm(q[:2]+[.22,-.18])*3+q[2]*.35-time*.10
    return .52+.46*np.cos(6.2831853*(layers+np.array([0,.33,.67])))

def main():
    renderer = Renderer(width=640, height=360)
    source = (Path(__file__).parent / "shaders/dream.frag").read_text(encoding="utf-8")
    marker = "for (int i = 0; i < 3; i++)"
    assert source.count(marker) == 1
    angle, opening = .28, .40
    u = np.array([math.cos(angle), math.sin(angle), 0.])
    v = np.array([-math.sin(angle)*opening, math.cos(angle)*opening, -math.sqrt(1-opening**2)])
    light = np.array([-.5, .65, 1.])
    light /= np.linalg.norm(light)
    visible = hidden = 0
    baseline = vao = None
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        baseline = renderer.ctx.program(vertex_shader=VERTEX_SHADER,
            fragment_shader=source.replace(marker, "for (int i = 0; i < 0; i++)"))
        vao = renderer.ctx.simple_vertex_array(baseline, renderer.vertices, "in_position")
        for seconds in np.linspace(0, 30, 61):
            frames = []
            for program, geometry in ((renderer.program, renderer.vao), (baseline, vao)):
                program["u_debug_state"].value = 3.
                program["u_drift_time"].value = float(seconds)
                program["u_resolution"].value = (640., 360.)
                renderer.ctx.viewport = (0, 0, 640, 360)
                geometry.render(mode=moderngl.TRIANGLE_STRIP)
                frames.append(np.frombuffer(renderer.ctx.screen.read(components=3), dtype=np.uint8).reshape(360,640,3))
            for i in range(3):
                phase = seconds*(.42+i*.11)+i*2.1
                center = (.43+i*.09)*(u*math.cos(phase)+v*math.sin(phase))
                radius = .025+i*.006
                col, row = int(center[0]*360+320), int(center[1]*360+180)
                p = np.array([(col+.5-320)/360, (row+.5-180)/360])
                depth = center[2]+math.sqrt(radius**2-np.sum((p-center[:2])**2))
                planet_d = .3**2-np.dot(p,p)
                if planet_d > 0 and math.sqrt(planet_d) > depth:
                    # A hidden moon must leave precisely the underlying scene.
                    assert np.array_equal(frames[0][row,col], frames[1][row,col]), (seconds,i,"occlusion")
                    hidden += 1
                else:
                    normal = (np.array([p[0],p[1],depth])-center)/radius
                    diffuse = max(np.dot(normal,light),0)
                    toward = np.dot(-center,light)
                    miss = np.linalg.norm(center+light*max(toward,0))
                    x = np.clip((miss-.28)/.04,0,1)
                    eclipse = x*x*(3-2*x) if toward>0 else 1.
                    expected = material(normal, i, seconds)*(.12+.88*diffuse*eclipse)*255
                    assert np.max(np.abs(frames[0][row,col].astype(float)-expected)) < 2, (seconds,i,"opacity or lighting")
                    visible += 1
        assert visible > 50 and hidden > 5, (visible,hidden)
        print(f"PASS: 61 Cosmic times / 122 GPU frames; {visible} opaque lit moon centers, {hidden} hidden moon centers.")
    finally:
        if vao is not None: vao.release()
        if baseline is not None: baseline.release()
        renderer.close()

if __name__ == "__main__":
    main()
