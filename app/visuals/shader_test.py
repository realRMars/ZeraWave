import math
import argparse
from preview_layers import parse_layers, validate_layers, layers_at
import hashlib
import json
import struct
import zlib
from pathlib import Path

import numpy as np
import glfw
import moderngl

from renderer import Renderer, VERTEX_SHADER

STATES = {"blend": 0, "organic": 1, "geometric": 2, "cosmic": 3, "transition": 4, "canvas": 5, "water": 6, "sea": 7, "dyes": 8, "rain": 9, "waterfall": 10, "membrane": 11, "roots": 12, "currents": 13}


def save_png(path, pixels):
    """Write RGB captures using the standard library; no image dependency."""
    height, width, _ = pixels.shape
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\x00' + row.tobytes() for row in pixels)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def capture(output, seconds, profile="standard", debug_state=0, layers=None):
    """Save a reproducible synthetic frame and GPU-evaluated state weights."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=640, height=360, title="DreamWave capture")
    source = (Path(__file__).parent / "shaders/dream.frag").read_text(encoding="utf-8")
    values = dict(u_time=seconds * .75, u_star_time=seconds, u_drift_time=seconds,
                  u_resolution=(640., 360.), u_scale=.3, u_flux=.2,
                  u_sparkle=.2, u_impact=.05, u_intensity=1., u_distortion=1.,
                  u_debug_state=float(debug_state))
    layer_mode, layer_mask = layers_at(validate_layers(layers or {}), debug_state, seconds)
    values.update(u_layer_mode=layer_mode, u_layer_mask=layer_mask)
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
        # Isolated Cosmic/Water own the scene; shared-field weights do not
        # describe world visibility (Water still inherits the source material).
        for name in (() if debug_state == 3 or debug_state >= 6 else ("organic", "tunnel", "fractal", "geometric", "cosmic", "horizon", "root_mix", "cosmic_takeover")):
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


def water_test(output):
    """Synthetic GPU coverage: structure, headroom, motion and audio response."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=640, height=360, title="Water verification")
    results = []
    def frame(seconds, scale=.05, flux=.02, sparkle=.05, impact=0.):
        for name, value in dict(u_time=seconds*.75, u_star_time=seconds,
                u_drift_time=seconds, u_debug_state=6., u_scale=scale,
                u_flux=flux, u_sparkle=sparkle, u_impact=impact,
                u_intensity=1., u_distortion=1.).items():
            renderer.program[name].value = value
        renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
        return np.frombuffer(renderer.ctx.screen.read(components=3),
            dtype=np.uint8).reshape(360, 640, 3).copy()
    def difference(a, b):
        return float(np.abs(a.astype(float) - b.astype(float)).mean())
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.render()
        captures = []
        for name, values in (
                ('silence', (0., 0., 0., 0.)),
                ('quiet', (.05, .02, .05, 0.)),
                ('active', (.45, .45, .25, .25)),
                ('chorus', (.85, .95, .8, .55))):
            for seconds in (0., 8., 18., 32., 67., 100., 180., 240., 600.):
                pixels = frame(seconds, *values)
                contrast = float(pixels.astype(float).std(axis=(0, 1)).mean())
                dark = float((pixels.max(axis=2) < 35).mean())
                clipped = float((pixels.max(axis=2) >= 250).mean())
                assert contrast > 4., (name, seconds, 'Lost structure', contrast)
                assert dark > .08, (name, seconds, 'Lost dark water', dark)
                assert clipped < .005, (name, seconds, 'Clipping', clipped)
                results.append((name, seconds, contrast, dark, clipped))
                if seconds in (18., 67., 180.):
                    save_png(output / f'{name}-{seconds:g}.png', pixels[::-1])
                    captures.append(pixels[::-1])
        base = frame(18.)
        responses = {}
        for name, values in (
                ('bass', (.85, .02, .05, 0.)),
                ('flux', (.05, .9, .05, 0.)),
                ('sparkle', (.05, .02, .9, 0.)),
                ('impact', (.05, .02, .05, .9))):
            changed = frame(18., *values)
            responses[name] = difference(base, changed)
            assert responses[name] > .10, (name, 'Unresponsive', responses[name])
            save_png(output / f'only-{name}.png', changed[::-1])
        quiet_motion = difference(frame(18., 0., 0., 0., 0.), frame(20., 0., 0., 0., 0.))
        assert quiet_motion > .1, ('Frozen silence', quiet_motion)
        step_delta = difference(frame(18.), frame(18. + 1./60.))
        assert step_delta < 3., ('Discontinuous motion', step_delta)
        # Check an actual renderer-integrated passage, including attack/release.
        renderer.debug_state = 6
        renderer.last_render_time = None
        renderer.flow_time = renderer.star_time = 0.
        previous = None
        max_step = 0.
        for index in range(181):
            seconds = index / 60.
            energy = .5 - .5 * math.cos(seconds * math.pi / 1.5)
            renderer.parameters.scale = energy * .85
            renderer.parameters.movement = energy
            renderer.parameters.flux = energy * .95
            renderer.parameters.sparkle = energy * .8
            renderer.parameters.impact = .8 if index == 60 else 0.
            renderer.render(elapsed_time=seconds)
            pixels = np.frombuffer(renderer.ctx.screen.read(components=3), dtype=np.uint8).copy()
            if previous is not None:
                max_step = max(max_step, difference(previous, pixels))
            previous = pixels
        assert max_step < 18., ('Excessive full-frame jump', max_step)
        # Render into sized targets to test aspect handling without resizing
        # the desktop. Timings measure GPU draw work, not live capture latency.
        resolutions = []
        for width, height in ((1280, 720), (1920, 1080), (720, 1280), (2560, 1080)):
            target = renderer.ctx.simple_framebuffer((width, height), components=3)
            try:
                target.use()
                renderer.ctx.viewport = (0, 0, width, height)
                renderer.program['u_resolution'].value = (float(width), float(height))
                renderer.program['u_scale'].value = .85
                renderer.program['u_flux'].value = .95
                renderer.program['u_sparkle'].value = .8
                renderer.program['u_impact'].value = .55
                milliseconds = []
                for index in range(90):
                    seconds = 18. + index / 60.
                    renderer.program['u_time'].value = seconds * .75
                    renderer.program['u_drift_time'].value = seconds
                    query = renderer.ctx.query(time=True)
                    with query:
                        renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
                    if index >= 10:
                        milliseconds.append(query.elapsed / 1e6)
                pixels = np.frombuffer(target.read(components=3, alignment=1),
                    dtype=np.uint8).reshape(height, width, 3)
                assert pixels.std() > 4, (width, height, 'Blank resized surface')
                assert (pixels.max(axis=2) >= 250).mean() < .005
                save_png(output / f'water-{width}x{height}.png', pixels[::-1])
                resolutions.append(dict(width=width, height=height,
                    median_gpu_ms=float(np.median(milliseconds)),
                    p95_gpu_ms=float(np.percentile(milliseconds, 95))))
            finally:
                renderer.ctx.screen.use()
                target.release()
        sheet = np.concatenate([np.concatenate(captures[i:i+3], axis=1)
            for i in (0, 3, 6, 9)], axis=0)
        save_png(output / 'contact-sheet.png', sheet)
        report = dict(samples=results, audio_pixel_deltas=responses,
            silence_motion=quiet_motion, fixed_input_frame_delta=step_delta,
            integrated_max_frame_delta=max_step,
            resolutions=resolutions, gpu=renderer.ctx.info.get('GL_RENDERER'),
            note='Synthetic GPU evidence; not live music or aesthetic acceptance.')
        (output / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('PASS: Water structure/headroom (36 frames), four independent audio responses, '
              f'silence motion and 181 integrated frames; {output}')
        print(json.dumps({k: v for k, v in report.items() if k != 'samples'}, indent=2))
    finally:
        renderer.close()


def water_comparison(baseline_path, output, preserve_waves=False):
    """Compare calm appearance or preserve accepted waves through world edits."""
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=640, height=360, title="Water before/after")
    resources = []
    measurements = []
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.render()
        sources = (baseline_path.read_text(encoding='utf-8-sig'),
            (Path(__file__).parent / 'shaders/dream.frag').read_text(encoding='utf-8'))
        programs = []
        probes = []
        for source in sources:
            for target, shader in ((programs, source), (probes,
                    source.replace('void main()', 'void original_main()') + '''
void main() {
    vec2 position = (gl_FragCoord.xy / u_resolution - 0.5) * vec2(16.0, 12.0);
    float height = water_height(position);
    fragColor = vec4(vec3(0.5 + height * 0.4), 1.0);
}
''')):
                program = renderer.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=shader)
                vao = renderer.ctx.simple_vertex_array(program, renderer.vertices, 'in_position')
                resources.append((program, vao))
                target.append((program, vao))

        def frame(pair, seconds, values):
            program, vao = pair
            scale, flux, sparkle, impact = values
            for name, value in dict(u_time=seconds*.75, u_star_time=seconds,
                    u_drift_time=seconds, u_resolution=(640.,360.), u_debug_state=6.,
                    u_scale=scale, u_flux=flux, u_sparkle=sparkle, u_impact=impact,
                    u_intensity=1., u_distortion=1.).items():
                if name in program: program[name].value = value
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(renderer.ctx.screen.read(components=3), dtype=np.uint8).reshape(360,640,3).copy()

        for name, values in (('quiet', (.05,.02,.05,0.)),
                ('moderate', (.45,.45,.25,.25)), ('chorus', (.85,.95,.8,.55))):
            for seconds in (18.,67.,180.):
                before, after = [frame(pair, seconds, values) for pair in programs]
                maximum = int(np.abs(before.astype(int)-after.astype(int)).max())
                if not preserve_waves and name != 'chorus':
                    assert maximum <= 1, (name,seconds,'Accepted calm water changed',maximum)
                heights = [frame(pair, seconds, values)[:,:,0].astype(float) for pair in probes]
                later = [frame(pair, seconds+1./30., values)[:,:,0].astype(float) for pair in probes]
                amplitudes = [float(h.std()) for h in heights]
                motion = [float(np.abs(a-b).mean()) for a,b in zip(heights,later)]
                if preserve_waves:
                    # No scene-camera changes can conceal a wave retune.
                    assert np.array_equal(heights[0], heights[1]), (name, seconds, 'Accepted wave height changed')
                    assert np.array_equal(later[0], later[1]), (name, seconds, 'Accepted wave movement changed')
                    assert maximum > 1, (name, seconds, 'World composition not applied')
                elif name == 'chorus':
                    assert amplitudes[1] > amplitudes[0]*2., ('No larger swells',seconds,amplitudes)
                    assert motion[1] > motion[0]*2., ('No faster wave travel',seconds,motion)
                save_png(output/f'{name}-{seconds:g}-before.png',before[::-1])
                save_png(output/f'{name}-{seconds:g}-after.png',after[::-1])
                measurements.append(dict(profile=name,seconds=seconds,maximum_pixel_change=maximum,
                    height_std_before_after=amplitudes, height_motion_before_after=motion))
        # The rough-sea entrance must approach the calm state continuously.
        a = frame(programs[1], 18., (.55-.00001,)*3 + (0.,))
        b = frame(programs[1], 18., (.55+.00001,)*3 + (0.,))
        boundary = float(np.abs(a.astype(float)-b.astype(float)).mean())
        assert boundary < 1., ('Rough-sea threshold discontinuity',boundary)
        if preserve_waves:
            quiet = frame(programs[1], 18., (.05,.02,.05,0.))
            loud = frame(programs[1], 18., (.85,.95,.8,.55))
            sky_delta = int(np.abs(quiet[300:].astype(int)-loud[300:].astype(int)).max())
            assert sky_delta <= 1, ('Audio distorts distant world', sky_delta)
            assert float(np.abs(quiet[:180].astype(float)-loud[:180].astype(float)).mean()) > 1.
        (output/'comparison.json').write_text(json.dumps(dict(samples=measurements,
            boundary_mean_pixel_delta=boundary,
            note='GPU height/motion probes and pixel comparisons; not subjective live acceptance.'),indent=2))
        label = ('9 accepted-wave height/motion comparisons and stable distant sky'
            if preserve_waves else '6 calm/moderate comparisons, 3 chorus height/motion comparisons')
        print(f'PASS: {label}; threshold delta {boundary:.5f}; {output}')
        print(json.dumps([m for m in measurements if m['profile']=='chorus'],indent=2))
    finally:
        for program, vao in resources:
            vao.release()
            program.release()
        renderer.close()


def water_family_test(baseline_path, output, waterfall_refinement=False):
    """GPU regression for held forms, morph boundaries and live integration."""
    output.mkdir(parents=True,exist_ok=True)
    renderer=Renderer(width=640,height=360,title="Water family verification")
    baseline=vao=None
    records=[]
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
        renderer.create();renderer.render()
        baseline=renderer.ctx.program(vertex_shader=VERTEX_SHADER,
            fragment_shader=baseline_path.read_text(encoding='utf-8-sig'))
        vao=renderer.ctx.simple_vertex_array(baseline,renderer.vertices,'in_position')
        def frame(state,seconds,level,old=False):
            program,geometry=(baseline,vao) if old else (renderer.program,renderer.vao)
            for name,value in dict(u_time=seconds*.75,u_star_time=seconds,u_drift_time=seconds,
                    u_resolution=(640.,360.),u_debug_state=float(state),u_scale=level,u_flux=level,
                    u_sparkle=level,u_impact=level*.3,u_intensity=1.,u_distortion=1.).items():
                if name in program:program[name].value=value
            geometry.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(360,640,3).copy()
        preserved=0
        # Existing isolated worlds and the accepted sea retain their actual pixels.
        states = (0,1,2,3,4,5,7,8,9) if waterfall_refinement else (0,1,2,3,4,5,7)
        for state in states:
            for seconds in (18.,67.,100.,180.):
                for level in (.05,.45,.95):
                    before=frame(6 if state==7 and not waterfall_refinement else state,seconds,level,True)
                    after=frame(state,seconds,level)
                    delta=int(np.abs(before.astype(int)-after.astype(int)).max())
                    assert delta<=1, ('Preservation',state,seconds,level,delta)
                    preserved+=1
        for state in (6,7,8,9,10):
            for level in (.05,.45,.95):
                for seconds in (18.,43.,71.,99.):
                    pixels=frame(state,seconds,level)
                    contrast=float(pixels.astype(float).std(axis=(0,1)).mean())
                    dark=float((pixels.max(axis=2)<35).mean())
                    clipped=float((pixels.max(axis=2)>=250).mean())
                    assert contrast>2 and dark>.10 and clipped<.01, (state,level,seconds,contrast,dark,clipped)
                    records.append(dict(state=state,seconds=seconds,level=level,contrast=contrast,dark=dark,clipped=clipped))
                    if level==.45:save_png(output/f'state-{state}-{seconds:g}.png',pixels[::-1])
        worst=0.
        live_points=(116,126,144,158,256,266,284,298)
        if waterfall_refinement:live_points += (411.04,420,424,438)
        for state,points in ((6,(19.04,28,47.04,56,75.04,84,103.04,112)),
                             (0,live_points)):
            for seconds in points:
                before=frame(state,seconds-1./120.,.65)
                after=frame(state,seconds+1./120.,.65)
                delta=float(np.abs(before.astype(float)-after.astype(float)).mean())
                original_a=frame(state,seconds-1./120.,.65,True)
                original_b=frame(state,seconds+1./120.,.65,True)
                original_delta=float(np.abs(original_a.astype(float)-original_b.astype(float)).mean())
                print('Boundary',state,seconds,'new',round(delta,4),'baseline',round(original_delta,4),flush=True)
                assert delta<max(3.,original_delta+.25),('Handoff discontinuity',state,seconds,delta,original_delta)
                worst=max(worst,delta)
        # Main blend must actually admit Water, then restore the old world.
        for seconds in (121.,135.,151.):
            a=frame(0,seconds,.45,True);b=frame(0,seconds,.45)
            if waterfall_refinement:
                assert int(np.abs(a.astype(int)-b.astype(int)).max())<=1
            else:
                assert float(np.abs(a.astype(float)-b.astype(float)).mean())>1.
            save_png(output/f'blend-{seconds:g}.png',b[::-1])
        for seconds in (0.,115.,159.,164.,255.,299.):
            a=frame(0,seconds,.45,True);b=frame(0,seconds,.45)
            assert int(np.abs(a.astype(int)-b.astype(int)).max())<=1, ('Outside Water',seconds)
        if waterfall_refinement:
            # Inspect the whole push toward/below the lip, not only a still at
            # either end. Check a quiet and a dense musical profile.
            camera_steps=[]
            for level in (.05,.85):
                previous=None
                for seconds in np.linspace(84.,124.,2401):
                    pixels=frame(10,float(seconds),level)
                    if previous is not None:
                        delta=float(np.abs(pixels.astype(float)-previous.astype(float)).mean())
                        assert delta<3.,('Camera jump',seconds,level,delta)
                        camera_steps.append(delta)
                    previous=pixels
                    if abs(seconds-round(seconds))<.00001 and int(round(seconds)) in (84,92,96,98,103,112,124):
                        save_png(output/f'falls-{level}-{seconds:g}.png',pixels[::-1])
            for seconds in (420.,424.,430.):
                save_png(output/f'falls-blend-{seconds:g}.png',frame(0,seconds,.45)[::-1])
            # Real GPU hit classifications prove the river/sky give way to an
            # uninterrupted falling face. Every bottom-center ray hits the fall.
            source=(Path(__file__).parent/'shaders/dream.frag').read_text()
            probe=renderer.ctx.program(vertex_shader=VERTEX_SHADER,
                fragment_shader=source.replace('void main()', 'void original_main()')+"""
void main() {
    vec2 p=gl_FragCoord.xy/u_resolution-.5;
    p.x*=u_resolution.x/u_resolution.y;
    FallsSurface surface=waterfall_surface(p);
    fragColor=vec4(surface.kind*.4,surface.position.y<0.0 ? 1.0 : 0.0,0.0,1.0);
}
""")
            probe_vao=None
            try:
                probe_vao=renderer.ctx.simple_vertex_array(probe,renderer.vertices,'in_position')
                probe['u_resolution'].value=(640.,360.)
                for seconds in (84.,103.):
                    probe['u_drift_time'].value=seconds
                    probe_vao.render(mode=moderngl.TRIANGLE_STRIP)
                    kinds=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(360,640,3)
                    if seconds==84.:
                        assert (kinds[:,:,0]==0).mean()>.1, 'No distant sky'
                        assert (kinds[:,:,0]==102).mean()>.1, 'No river between horizons'
                    else:
                        assert (kinds[:,:,0]==204).mean()>.98, 'Close view still shows river/sky'
                    assert (kinds[0,280:360,0]==204).all(), 'Bottom is not an infinite fall'
                print(f'PASS: 4802 camera frames, maximum step {max(camera_steps):.4f}; GPU river/sky/fall coverage.')
            finally:
                if probe_vao is not None:probe_vao.release()
                probe.release()
        (output/'family.json').write_text(json.dumps(dict(samples=records,
            preserved_cases=preserved,worst_boundary_delta=worst,
            camera_max_step=max(camera_steps) if waterfall_refinement else None),indent=2))
        print(f'PASS: {preserved} preserved-world/sea cases, {len(records)} family samples, '
              f'{8+len(live_points)} morph/live boundaries (max {worst:.4f}), live entry/exit.')
    finally:
        if vao is not None:vao.release()
        if baseline is not None:baseline.release()
        renderer.close()


def preservation_test(baseline_path):
    """Compare accepted shader pixels, rather than assuming isolation from code."""
    renderer = Renderer(width=320, height=180, title="Accepted-world preservation")
    baseline = geometry = None
    count = 0
    maximum = 0
    try:
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        renderer.create()
        renderer.render()
        baseline = renderer.ctx.program(vertex_shader=VERTEX_SHADER,
            fragment_shader=baseline_path.read_text(encoding='utf-8-sig'))
        geometry = renderer.ctx.simple_vertex_array(baseline, renderer.vertices, 'in_position')
        for state in range(6):
            for level in (.05, .45, .95):
                for seconds in (18., 67., 100., 180.):
                    frames = []
                    for program, vao in ((baseline, geometry), (renderer.program, renderer.vao)):
                        for name, value in dict(u_time=seconds*.75, u_star_time=seconds,
                                u_drift_time=seconds, u_resolution=(320., 180.),
                                u_debug_state=float(state), u_scale=level, u_flux=level,
                                u_sparkle=level, u_impact=level*.5, u_intensity=1., u_distortion=1.).items():
                            program[name].value = value
                        vao.render(mode=moderngl.TRIANGLE_STRIP)
                        frames.append(np.frombuffer(renderer.ctx.screen.read(components=3), dtype=np.uint8).copy())
                    delta = int(np.abs(frames[0].astype(int)-frames[1].astype(int)).max())
                    maximum = max(maximum, delta)
                    assert delta <= 1, (state, level, seconds, 'Accepted-world change', delta)
                    count += 1
        print(f'PASS: {count} accepted-world comparisons / {count*2} GPU frames; '
              f'maximum channel difference {maximum}/255.')
    finally:
        if geometry is not None: geometry.release()
        if baseline is not None: baseline.release()
        renderer.close()


def layer_test(baseline_path, output, water_expansion=False):
    """Real GPU preservation plus visible effect isolation, including Water."""
    from preview_layers import BITS
    output.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(width=480, height=270, title='Form and effect isolation')
    baseline = vao = None
    try:
        glfw.init(); glfw.window_hint(glfw.VISIBLE, glfw.FALSE); renderer.create()
        baseline = renderer.ctx.program(vertex_shader=VERTEX_SHADER,
            fragment_shader=baseline_path.read_text(encoding='utf-8-sig'))
        vao = renderer.ctx.simple_vertex_array(baseline, renderer.vertices, 'in_position')
        def frame(state, seconds=67., level=.85, mode=0, mask=0, before=False):
            program, geometry = (baseline, vao) if before else (renderer.program, renderer.vao)
            for name, value in dict(u_time=seconds*.75, u_star_time=seconds,
                    u_drift_time=seconds, u_resolution=(480.,270.), u_debug_state=float(state),
                    u_scale=level, u_flux=level, u_sparkle=level, u_impact=level*.6,
                    u_intensity=1., u_distortion=1., u_layer_mode=mode, u_layer_mask=mask).items():
                if name in program: program[name].value=value
            geometry.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(renderer.ctx.screen.read(components=3), dtype=np.uint8).reshape(270,480,3)[::-1].copy()
        preserved=0; maximum=0
        for state in (tuple(s for s in range(13) if s != 6) if water_expansion else range(11)):
            for level in (.05,.45,.95):
                for seconds in (18.,67.,100.,140.):
                    # Water integration intentionally changes its own main-blend
                    # visits; water_integration_test checks the joins and coverage.
                    if water_expansion and state == 0 and seconds >= 116. and 4. < (seconds-112.) % 140. < 46.:
                        continue
                    a=frame(state,seconds,level,before=True); b=frame(state,seconds,level)
                    delta=int(np.abs(a.astype(int)-b.astype(int)).max())
                    assert delta<=1,(state,seconds,level,delta)
                    maximum=max(maximum,delta); preserved+=1
        forms=[frame(state,mode=1) for state in (11,12,2,5)]
        assert all(p.std()>4 for p in forms), 'Empty effect list removed the form'
        assert np.abs(forms[0].astype(float)-forms[1]).mean()>4, 'Organic forms not distinct'
        save_png(output/'base-forms.png',np.concatenate(forms,axis=1))
        targets={'artifacts':(2,5,11,7),'sparkles':(2,5,11),'flecks':(2,5,11),
                 'beams':(2,5,11),'tunnel':(2,5,11),'fractal':(2,5,11),
                 'horizon':(2,5,11),'blossoms':(12,), 'glyphs':(2,),
                 'stars':(3,5),'rings':(3,5),'moons':(3,5),
                 'water_rain':(9,7),'water_ripples':(9,7),
                 'water_foam':(7,10),'water_mist':(7,10),
                 'water_glints':(7,10)}
        if water_expansion:
            targets['water_rain'] += (13,)
            targets['water_ripples'] += (13,)
            targets['water_glints'] += (13,)
            targets['artifacts'] += (13,)
        records=[]
        for effect, states in targets.items():
            for state in states:
                best=(-1,None,None,None)
                for seconds in (18.,38.,67.,100.,180.):
                    base=frame(state,seconds,mode=1)
                    enabled=frame(state,seconds,mode=1,mask=BITS[effect])
                    delta=float(np.abs(base.astype(float)-enabled).mean())
                    if delta>best[0]: best=(delta,seconds,base,enabled)
                delta,seconds,base,enabled=best
                assert delta>.001,(effect,state,'Effect never visible',delta)
                assert enabled.std()>3,(effect,state,'Lost structure')
                records.append(dict(effect=effect,state=state,seconds=seconds,mean_pixel_change=delta))
                if state==states[0]:
                    save_png(output/f'{effect}.png',np.concatenate([base,enabled],axis=1))
        (output/'layers.json').write_text(json.dumps(dict(preserved_cases=preserved,
            max_default_channel_delta=maximum,effects=records),indent=2),encoding='utf-8')
        print(f'PASS: {preserved} default preservation cases (max {maximum}/255), held Organic forms, '
              f'{len(records)} visible effect/world combinations. Evidence: {output}')
    finally:
        if vao is not None: vao.release()
        if baseline is not None: baseline.release()
        renderer.close()


def currents_test(baseline_path, output):
    """Existing forms stay intact; the new flow stays alive, bounded and continuous."""
    layer_test(baseline_path, output/'preservation', water_expansion=True)
    renderer=Renderer(width=640,height=360,title='Currents verification')
    records=[]; captures=[]
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);renderer.create()
        def frame(seconds, values=(.05,.02,.05,0.), state=13):
            for name,value in dict(u_time=seconds*.75,u_star_time=seconds,u_drift_time=seconds,
                    u_resolution=(640.,360.),u_debug_state=float(state),u_scale=values[0],
                    u_flux=values[1],u_sparkle=values[2],u_impact=values[3],
                    u_intensity=1.,u_distortion=1.,u_layer_mode=0,u_layer_mask=0).items():
                renderer.program[name].value=value
            renderer.vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(360,640,3)[::-1].copy()
        def delta(a,b):return float(np.abs(a.astype(float)-b.astype(float)).mean())
        for name,values in (('silence',(0.,0.,0.,0.)),('quiet',(.05,.02,.05,0.)),
                            ('active',(.45,.45,.25,.25)),('chorus',(.85,.95,.8,.55))):
            for seconds in (0.,18.,67.,100.,180.,300.,600.):
                pixels=frame(seconds,values)
                contrast=float(pixels.astype(float).std(axis=(0,1)).mean())
                dark=float((pixels.max(axis=2)<35).mean())
                clipped=float((pixels.max(axis=2)>=250).mean())
                assert contrast>5 and dark>.08 and clipped<.005,(name,seconds,contrast,dark,clipped)
                records.append(dict(profile=name,seconds=seconds,contrast=contrast,dark=dark,clipped=clipped))
                if seconds in (18.,67.,180.):
                    save_png(output/f'{name}-{seconds:g}.png',pixels);captures.append(pixels)
        response={}
        base=frame(18.)
        for name,values in (('bass',(.85,.02,.05,0.)),('flux',(.05,.9,.05,0.)),
                            ('sparkle',(.05,.02,.9,0.)),('impact',(.05,.02,.05,.9))):
            response[name]=delta(base,frame(18.,values))
            assert response[name]>.10,(name,'No visible response',response[name])
        silence_motion=delta(frame(18.,(0.,0.,0.,0.)),frame(20.,(0.,0.,0.,0.)))
        assert silence_motion>.1,('Frozen silence',silence_motion)
        assert delta(base,frame(18.,state=8))>5.,'Currents duplicates Liquid dyes'
        # Both ends of each eased boundary, including the new fall/current/sea joins.
        boundaries=[]
        for cycle in (0.,140.):
            for start in (19.04,28.,47.04,56.,75.04,84.,103.04,112.,131.04,140.):
                seconds=cycle+start
                step=delta(frame(seconds-1/120.,(.65,)*4,state=6),frame(seconds+1/120.,(.65,)*4,state=6))
                assert step<3.,('Cycle jump',seconds,step)
                boundaries.append(step)
        # Actual integrated renderer clocks with independent bounded audio envelopes.
        renderer.debug_state=13; previous=None; motion=[]
        for i in range(361):
            seconds=i/60.;energy=.5-.5*math.cos(seconds*math.pi/3.)
            renderer.parameters.scale=energy*.85;renderer.parameters.movement=energy
            renderer.parameters.flux=energy*.95;renderer.parameters.sparkle=energy*.8
            renderer.parameters.impact=max(0.,1.-abs(seconds-3.)*5.)*.6
            renderer.render(elapsed_time=seconds)
            pixels=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).copy()
            if previous is not None:motion.append(delta(previous,pixels))
            previous=pixels
        assert max(motion)<3.,('Integrated jump',max(motion))
        save_png(output/'contact-sheet.png',np.concatenate([np.concatenate(captures[i:i+3],axis=1) for i in (0,3,6,9)],axis=0))
        report=dict(samples=records,audio_response=response,silence_motion=silence_motion,
            max_boundary_delta=max(boundaries),max_integrated_delta=max(motion))
        (output/'currents.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('PASS: Currents structure/headroom, independent audio responses, quiet motion, '
              '20 cycle boundaries and 361 integrated GPU frames.',flush=True)
        print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
    finally:renderer.close()


def water_integration_test(baseline_path, output):
    """Preserve isolated worlds/outside Water; prove five distinct main visits."""
    output.mkdir(parents=True,exist_ok=True)
    renderer=Renderer(width=640,height=360,title='Complete Water integration')
    baseline=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);renderer.create()
        baseline=renderer.ctx.program(vertex_shader=VERTEX_SHADER,
            fragment_shader=baseline_path.read_text(encoding='utf-8-sig'))
        vao=renderer.ctx.simple_vertex_array(baseline,renderer.vertices,'in_position')
        def frame(state,seconds,level=.45,old=False):
            program,geometry=(baseline,vao) if old else (renderer.program,renderer.vao)
            for name,value in dict(u_time=seconds*.75,u_star_time=seconds,u_drift_time=seconds,
                    u_resolution=(640.,360.),u_debug_state=float(state),u_scale=level,u_flux=level,
                    u_sparkle=level,u_impact=level*.4,u_intensity=1.,u_distortion=1.,
                    u_layer_mode=0,u_layer_mask=0).items():
                program[name].value=value
            geometry.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(360,640,3)[::-1].copy()
        preserved=0
        for state in range(1,14):
            for seconds in (18.,67.,100.,140.):
                for level in (.05,.45,.95):
                    delta=int(np.abs(frame(state,seconds,level).astype(int)-frame(state,seconds,level,True).astype(int)).max())
                    assert delta<=1,('Held/Studio regression',state,seconds,level,delta)
                    preserved+=1
        outside=[0.,60.,100.,115.]
        for visit in range(6):outside.extend([158.+140.*visit,180.+140.*visit,255.+140.*visit])
        for seconds in outside:
            for level in (.05,.45,.95):
                delta=int(np.abs(frame(0,seconds,level).astype(int)-frame(0,seconds,level,True).astype(int)).max())
                assert delta<=1,('Outside Water regression',seconds,level,delta)
                preserved+=1
        # At full entrance each of five visits must match a different held form.
        held=(7,13,10,9,8);names=('Sea','Currents','Waterfall','Rain','Liquid dyes')
        boundaries=[];images=[];boundary_records=[]
        for visit,(state,name) in enumerate(zip(held,names)):
            seconds=126.+140.*visit
            for level in (.05,.45,.95):
                pixels=frame(0,seconds,level)
                delta=int(np.abs(pixels.astype(int)-frame(state,seconds,level).astype(int)).max())
                assert delta<=1,('Form coverage',visit,name,level,delta)
            pixels=frame(0,seconds);images.append(pixels)
            save_png(output/f'visit-{visit+1}-{name.replace(" ","-")}.png',pixels)
            for point in (116.,126.,135.8,144.,147.,158.):
                t=point+140.*visit
                for level in (.05,.65,.95):
                    before=frame(0,t-1/120.,level);after=frame(0,t+1/120.,level)
                    step=float(np.abs(before.astype(float)-after.astype(float)).mean())
                    original=float(np.abs(frame(0,t-1/120.,level,True).astype(float)-frame(0,t+1/120.,level,True).astype(float)).mean())
                    assert step<max(3.,original+.25),('Main Water discontinuity',t,level,step,original)
                    boundaries.append(step)
                    boundary_records.append(dict(seconds=t,level=level,mean_delta=step,baseline_delta=original))
        save_png(output/'five-visits.png',np.concatenate(images,axis=0))
        report=dict(preserved_cases=preserved,visit_forms=names,
            boundary_cases=len(boundaries),max_boundary_delta=max(boundaries),
            worst_boundary=max(boundary_records,key=lambda row:row['mean_delta']))
        (output/'integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('PASS: '+json.dumps(report),flush=True)
    finally:
        if vao is not None:vao.release()
        if baseline is not None:baseline.release()
        renderer.close()


def main(debug_state=0, states=None, layers=None):
    renderer = Renderer(
        width=1280,
        height=720,
        title="DreamWave - " + next(name for name, value in STATES.items() if value == debug_state),
    )
    print(f"State preview active: {debug_state}", flush=True)

    try:
        renderer.create()
        renderer.debug_state = debug_state
        renderer.debug_sequence = tuple(STATES[name] for name in (states or ()))
        renderer.layer_profiles = validate_layers(layers or {})

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
    parser.add_argument("--layer-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--currents-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--water-integration-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--handoff-test", type=Path)
    parser.add_argument("--geometric-test", type=Path)
    parser.add_argument("--water-test", type=Path)
    parser.add_argument("--waterfall-test", nargs=2,type=Path,metavar=("BASELINE","OUTPUT"))
    parser.add_argument("--water-family-test", nargs=2,type=Path,metavar=("BASELINE","OUTPUT"))
    parser.add_argument("--water-comparison", nargs=2, type=Path, metavar=('BASELINE', 'OUTPUT'))
    parser.add_argument("--water-world-test", nargs=2, type=Path, metavar=('BASELINE', 'OUTPUT'))
    parser.add_argument("--preservation-test", type=Path, help="Accepted dream.frag to compare on GPU")
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--seconds", type=float, default=100.)
    parser.add_argument("--profile", choices=("standard", "quiet", "active", "chorus"), default="standard")
    parser.add_argument("--state", choices=tuple(STATES), default="blend")
    parser.add_argument("--states", nargs="+", choices=tuple(STATES), help="Development cycle: hold each state for 28 seconds.")
    parser.add_argument("--layers", type=parse_layers, default={}, help="Development per-world effect settings as JSON.")
    args = parser.parse_args()
    if args.water_integration_test:
        water_integration_test(*args.water_integration_test)
    elif args.currents_test:
        currents_test(*args.currents_test)
    elif args.layer_test:
        layer_test(*args.layer_test)
    elif args.waterfall_test:
        water_family_test(*args.waterfall_test,waterfall_refinement=True)
    elif args.water_family_test:
        water_family_test(*args.water_family_test)
    elif args.water_world_test:
        water_comparison(*args.water_world_test, preserve_waves=True)
    elif args.water_comparison:
        water_comparison(*args.water_comparison)
    elif args.water_test:
        water_test(args.water_test)
    elif args.preservation_test:
        preservation_test(args.preservation_test)
    elif args.geometric_test:
        geometric_test(args.geometric_test)
    elif args.handoff_test:
        handoff_test(args.handoff_test)
    elif args.capture:
        capture(args.capture, args.seconds, args.profile,
                STATES[args.state], args.layers)
    elif args.sweep:
        sweep(args.sweep)
    else:
        main(STATES[args.state], args.states, args.layers)
