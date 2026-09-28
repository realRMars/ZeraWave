import math
import argparse
from preview_layers import parse_layers, validate_layers, layers_at, materials_at
import hashlib
import json
import struct
import zlib
from pathlib import Path

import numpy as np
import glfw
import moderngl

from renderer import Renderer, VERTEX_SHADER, blend_uniforms, blend_chapter, BLEND_FORMS

STATES = {"blend": 0, "organic": 1, "geometric": 2, "cosmic": 3, "transition": 4, "canvas": 5, "water": 6, "sea": 7, "dyes": 8, "rain": 9, "waterfall": 10, "membrane": 11, "roots": 12, "currents": 13, "fire": 14, "molten": 15, "fire_cycle": 16, "firescape": 17, "aftershock": 18, "windstreams": 19, "stormfront": 20, "vortex": 21, "citadel": 22, "air": 23, "dunes": 24, "strata": 25, "cavern": 26, "earth": 27, "nebula": 28, "marsh": 29, "pressure": 30, "fog": 31, "magnetic": 32, "arcs": 33, "auroral": 34, "plasma": 35}


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
    renderer = Renderer(width=640, height=360, title="ZeraWave capture")
    source = (Path(__file__).parent / "shaders/dream.frag").read_text(encoding="utf-8")
    values = dict(u_time=seconds * .75, u_star_time=seconds, u_drift_time=seconds,
                  u_resolution=(640., 360.), u_scale=.3, u_flux=.2,
                  u_sparkle=.2, u_impact=.05, u_intensity=1., u_distortion=1.,
                  u_debug_state=float(debug_state))
    layer_mode, layer_mask = layers_at(validate_layers(layers or {}), debug_state, seconds)
    values.update(u_layer_mode=layer_mode, u_layer_mask=layer_mask,
                  u_material_mix=materials_at(layers or {},debug_state,seconds),u_event_blasts=0)
    from preview_layers import earth_details_at
    values['u_earth_details']=earth_details_at(layers or {},debug_state,seconds)
    from preview_layers import fog_details_at
    values['u_fog_details']=fog_details_at(layers or {},debug_state,seconds)
    from preview_layers import plasma_details_at
    values['u_plasma_details']=plasma_details_at(layers or {},debug_state,seconds)
    values.update(blend_uniforms(seconds, debug_state == 0 and layer_mode != 0))
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
    renderer = Renderer(width=320, height=180, title="ZeraWave diagnostic")
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


def choreography_test(baseline_path, output):
    """Preserve held worlds and verify bidirectional Main handoff continuity."""
    from renderer import world_uniforms
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270,seed=42);old=mesh=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        source=(Path(__file__).parent/'shaders/dream.frag').read_text()
        baseline=baseline_path.read_text()
        assert baseline[baseline.index('float effect('):baseline.index('void main()')].strip()==source[source.index('float effect('):source.index('// Main-only physical handoffs.')].strip(), 'Accepted world helpers changed'
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline)
        mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t=16.,energy=.65,hit=0.,weights=None,previous=False,details=(1.,1.,1.),mask=2147483647,mode=0,material=(1.,0.,0.),signals=None):
            pr,vao=(old,mesh) if previous else (r.program,r.vao)
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),u_scale=energy,u_flux=energy,
                u_sparkle=energy,u_impact=hit,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),u_event_blasts=0,
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=material,u_air_flash_id=2.,u_air_afterglow=hit,
                u_daddy_long_legs=0.,u_earth_details=(1.,1.,1.,1.),u_fog_details=(1.,1.,1.),u_plasma_details=details,**world_uniforms(weights or {},enabled=weights is not None))
            values.update(signals or {})
            for k,v in values.items():
                if k in pr:pr[k].value=v
            pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            pr['u_air_trails'].value=[(0.,0.)]*3
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        checks=0
        for state in range(36):
            for mode in (0,2):
                delta=np.abs(frame(state,mode=mode).astype(float)-frame(state,mode=mode,previous=True))
                assert delta.mean()<.05 and (delta>2).mean()<.0025,('held changed',state,mode,delta.mean())
                checks+=1
        print('Held preservation passed:',checks,flush=True)
        from renderer import handoff_kind,world_family
        pairs=((7,15),(8,15),(20,33),(21,34),(24,29),(26,28),(22,32))
        continuity=[]
        for first,second in pairs:
            for a,b in ((first,second),(second,first)):
                tiles=[]
                def transition(x,previous=False):
                    return frame(0,weights={a:1.-x,b:x},mode=2,previous=previous,
                        signals=dict(u_world_warp=0.,u_handoff=(handoff_kind(a,b),x,world_family(a),world_family(b))))
                for x in (0.,.2,.4,.5,.6,.8,1.):
                    pixels=transition(x)
                    near=transition(min(1.,x+.0001))
                    delta=float(np.abs(pixels.astype(float)-near).mean())
                    assert delta<2.,('discontinuity',a,b,x,delta)
                    assert pixels.std()>2.,('blank',a,b,x)
                    if x in (0.,1.):
                        error=np.abs(pixels.astype(float)-transition(x,True))
                        assert error.mean()<.05,('endpoint',a,b,x,error.mean())
                    continuity.append(delta);tiles.append(pixels)
                save_png(output/f'pair-{a}-{b}.png',np.concatenate(tiles,axis=1))
        report=dict(held_checks=checks,pair_frames=len(continuity),max_continuity_delta=max(continuity))
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        if mesh is not None:mesh.release()
        if old is not None:old.release()
        r.close()


def plasma_test(baseline_path, output,accepted_path=None):
    """GPU preservation, musical expression, opacity, isolation and regional handoffs."""
    from renderer import world_uniforms
    from preview_layers import BITS
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270,seed=42);old=mesh=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        source=(Path(__file__).parent/'shaders/dream.frag').read_text()
        baseline=baseline_path.read_text()
        assert baseline[baseline.index('float effect('):baseline.index('void main()')].strip()==source[source.index('float effect('):source.index('// Plasma keeps')].strip(), 'Earlier world helpers changed'
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline)
        mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t=16.,energy=.65,hit=0.,weights=None,previous=False,details=(1.,1.,1.),mask=2147483647,mode=0,material=(1.,0.,0.),signals=None):
            pr,vao=(old,mesh) if previous else (r.program,r.vao)
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),u_scale=energy,u_flux=energy,
                u_sparkle=energy,u_impact=hit,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),u_event_blasts=0,
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=material,u_air_flash_id=2.,u_air_afterglow=hit,
                u_daddy_long_legs=0.,u_earth_details=(1.,1.,1.,1.),u_fog_details=(1.,1.,1.),u_plasma_details=details,**world_uniforms(weights or {},enabled=weights is not None))
            values.update(signals or {})
            for k,v in values.items():
                if k in pr:pr[k].value=v
            pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            pr['u_air_trails'].value=[(0.,0.)]*3
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        precision=[]
        for state in range(32):
            for mode in (0,2):
                delta=np.abs(frame(state,mode=mode).astype(float)-frame(state,mode=mode,previous=True))
                assert delta.mean()<.05 and (delta>2).mean()<.0025,('old world changed',state,mode,delta.max(),delta.mean())
                precision.append(dict(state=state,mode=mode,mean=float(delta.mean()),outlier_fraction=float((delta>2).mean())))
        if accepted_path is not None:
            mesh.release();old.release()
            old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=accepted_path.read_text())
            mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
            for state in (32,33,34):
                for t in (4.,16.):
                    for energy in (.025,.85):
                        delta=np.abs(frame(state,t=t,energy=energy,details=(1.,1.,0.)).astype(float)-frame(state,t=t,energy=energy,details=(1.,1.,0.),previous=True))
                        assert delta.mean()<.05 and (delta>2).mean()<.0025,('Plasma foreground changed',state,t,energy,delta.mean())
        for state in (32,33,34):
            quiet=frame(state,energy=.025);active=frame(state,energy=.85,hit=.65)
            assert quiet.std()>2 and active.std()>3,('blank',state)
            assert np.abs(quiet.astype(float)-active).mean()>1.,('unreactive',state)
            assert (active.min(axis=2)>250).mean()<.02,('white glare',state)
            save_png(output/f'form-{state}.png',np.concatenate((quiet,active),axis=1))
            for i in range(3):
                details=[1.,1.,1.];details[i]=0.
                off=frame(state,energy=.85,hit=.65,details=tuple(details))
                assert np.abs(active.astype(float)-off).mean()>.005,('inactive detail',state,i)
            resting=frame(state,energy=.08)
            for channel in ('u_scale','u_flux','u_sparkle','u_impact'):
                responding=frame(state,energy=.08,signals={channel:.9})
                assert np.abs(resting.astype(float)-responding).mean()>.02,('audio channel inactive',state,channel)
            tiles=[]
            for material,key in (((1.,0.,0.),'artifacts'),((0.,1.,0.),'alloy'),((0.,0.,1.),'lattice')):
                plain=frame(state,mode=1,mask=BITS[key],material=material)
                folded=frame(state,mode=1,mask=BITS[key]+BITS['fractal']+BITS['tunnel'],material=material)
                assert np.abs(plain.astype(float)-folded).mean()>.02,('material folds missing',state,key)
                tiles.extend((plain,folded))
            save_png(output/f'materials-{state}.png',np.concatenate(tiles,axis=1))
            motion=[frame(state,t=t) for t in (0.,4.,8.,12.)]
            assert all(np.abs(a.astype(float)-b).mean()>.5 for a,b in zip(motion,motion[1:]))
            save_png(output/f'motion-{state}.png',np.concatenate(motion,axis=1))
        handoffs=0
        for a in (32,33,34):
            for b in (2,5,7,18,21,22,24,26,28,29,30,32,33,34):
                if a==b:continue
                tiles=[]
                for x in (0.,.25,.5,.75,1.):
                    pixels=frame(0,weights={a:1.-x,b:x},mode=2)
                    near=frame(0,weights={a:1.-min(1.,x+.0001),b:min(1.,x+.0001)},mode=2)
                    assert np.abs(pixels.astype(float)-near).mean()<2.,('handoff discontinuity',a,b,x)
                    assert pixels.std()>2.,('empty handoff',a,b,x)
                    handoffs+=1;tiles.append(pixels)
                if (a,b) in ((32,33),(33,34),(34,32),(32,5),(34,28)):
                    save_png(output/f'pair-{a}-{b}.png',np.concatenate(tiles,axis=1))
        for t in (36.,72.,108.):
            assert np.abs(frame(35,t=t-.0001).astype(float)-frame(35,t=t+.0001)).mean()<1.,('cycle seam',t)
        probe_source=source.replace('void main()', 'void unused_main()')
        probe_source=probe_source.replace('vec3 color=vec3(.003,.005,.014)+plasma_stars(p,form)*u_plasma_details.z;', 'vec3 color=vec3(u_test_background,0.,u_test_background);')
        probe_source=probe_source.replace('uniform float u_time;', 'uniform float u_time;\nuniform float u_test_background;')
        probe_source+='''
void main() {
    vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;
    fragColor=vec4(plasma_scene(p,vec3(.2),0),1.);
}
'''
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=probe_source)
        probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        try:
            for k,v in dict(u_resolution=(480.,270.),u_time=9.,u_drift_time=12.,u_star_time=12.,u_scale=.2,u_flux=.2,u_sparkle=.2,u_impact=0.,u_plasma_details=(1.,1.,1.)).items():
                if k in probe:probe[k].value=v
            tiles=[]
            for background in (0.,1.):
                probe['u_test_background'].value=background;probe_mesh.render(mode=moderngl.TRIANGLE_STRIP)
                tiles.append(np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy())
            assert np.array_equal(tiles[0][128:142,233:247],tiles[1][128:142,233:247]),'Background leaked through opaque core'
            assert np.abs(tiles[0].astype(float)-tiles[1]).mean()>10.,'Core probe did not change background'
            save_png(output/'opaque-core.png',np.concatenate(tiles,axis=1))
        finally:probe_mesh.release();probe.release()
        sky_source=source.replace('void main()', 'void unused_main()')+'''
void main() {
    vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;
    fragColor=vec4(plasma_stars(p,int(u_debug_state)),1.);
}
'''
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=sky_source)
        probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        try:
            for k,v in dict(u_resolution=(480.,270.),u_scale=.75,u_flux=.7,u_sparkle=.8,u_impact=.5).items():
                if k in probe:probe[k].value=v
            skies=[]
            for form in range(3):
                probe['u_debug_state'].value=float(form);tiles=[]
                for t in (0.,8.,16.):
                    probe['u_star_time'].value=t;probe_mesh.render(mode=moderngl.TRIANGLE_STRIP)
                    pixels=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
                    assert pixels.mean()>.05 and (pixels.max(axis=2)<20).mean()>.85,('sky empty or excessive',form,t)
                    tiles.append(pixels)
                assert all(np.abs(a.astype(float)-b).mean()>.1 for a,b in zip(tiles,tiles[1:])),('static sky',form)
                save_png(output/f'sky-{form}.png',np.concatenate(tiles,axis=1));skies.append(tiles[1])
            assert all(np.abs(skies[a].astype(float)-skies[b]).mean()>.05 for a,b in ((0,1),(1,2),(0,2))), 'Sky identities collapsed'
        finally:probe_mesh.release();probe.release()
        last=-1.
        for i in range(150):
            r.debug_state=32+(i//50)%3
            r.parameters.scale=r.parameters.flux=r.parameters.movement=.85 if i%50>20 else .03
            r.render(elapsed_time=i/30.)
            assert r.flow_time>last;last=r.flow_time
        (output/'precision.json').write_text(json.dumps(precision,indent=2))
        report=dict(preserved_frames=64,foreground_checks=12 if accepted_path else 0,handoff_checks=handoffs,renderer_frames=150,opaque_core=True,sky_motion_frames=9)
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        if mesh is not None:mesh.release()
        if old is not None:old.release()
        r.close()


def fog_test(baseline_path,output,accepted_path=None):
    """Volume compositing, real solid occlusion, musical response and old worlds."""
    from renderer import world_uniforms
    from preview_layers import BITS
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270,seed=42);old=mesh=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        source=(Path(__file__).parent/'shaders/dream.frag').read_text()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text())
        mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t=16.,energy=.7,hit=0.,weights=None,previous=False,details=(1.,1.,1.),mask=2147483647,mode=0,material=(1.,0.,0.),signals=None):
            pr,vao=(old,mesh) if previous else (r.program,r.vao)
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),u_scale=energy,u_flux=energy,
                u_sparkle=energy,u_impact=hit,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),u_event_blasts=0,
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=material,u_air_flash_id=2.,u_air_afterglow=hit,
                u_daddy_long_legs=0.,u_earth_details=(1.,1.,1.,1.),u_fog_details=details,**world_uniforms(weights or {},enabled=weights is not None))
            values.update(signals or {})
            for k,v in values.items():
                if k in pr:pr[k].value=v
            pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            pr['u_air_trails'].value=[(0.,0.)]*3
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        # Keep every earlier world helper byte-for-byte, in addition to image comparisons.
        old_source=baseline_path.read_text()
        before=old_source[old_source.index('float effect('):old_source.index('void main()')].strip()
        after=source[source.index('float effect('):source.index('// Fog/Gas uses')].strip()
        assert before==after, 'Earlier world helper source changed'
        preserved=0
        precision=[]
        for state in range(28):
            for mode in (0,2):
                delta=np.abs(frame(state,mode=mode).astype(float)-frame(state,mode=mode,previous=True))
                # Larger shaders can shift procedural threshold edges through GPU floating-point codegen.
                # Reject broad appearance changes; retain the source-identity guard above.
                assert delta.mean()<.05 and (delta>2).mean()<.0025,('old world changed',state,mode,delta.max(),delta.mean())
                precision.append(dict(state=state,mode=mode,maximum=float(delta.max()),mean=float(delta.mean()),outlier_fraction=float((delta>2).mean())))
                preserved+=1
        if accepted_path is not None:
            mesh.release();old.release()
            old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=accepted_path.read_text())
            mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
            for t in (0.,16.,32.):
                for energy in (.025,.85):
                    for state in (28,30):
                        delta=np.abs(frame(state,t=t,energy=energy).astype(float)-frame(state,t=t,energy=energy,previous=True))
                        assert delta.mean()<.05 and (delta>2).mean()<.0025,('accepted Fog state changed',state,t,energy,delta.mean())
        for state in (28,29,30):
            quiet=frame(state,energy=.025);active=frame(state,energy=.85,hit=.65)
            assert quiet.std()>2 and active.std()>3,('blank',state)
            assert np.abs(quiet.astype(float)-active).mean()>1.,('unreactive',state)
            assert (active.min(axis=2)>250).mean()<.02,('white glare',state)
            save_png(output/f'form-{state}.png',np.concatenate((quiet,active),axis=1))
            for i in range(3):
                details=[1.,1.,1.];details[i]=0.
                off=frame(state,energy=.85,hit=.65,details=tuple(details))
                assert np.abs(active.astype(float)-off).mean()>.02,('inactive detail',state,i)
            resting=frame(state,energy=.08)
            for channel in ('u_scale','u_flux','u_sparkle','u_impact'):
                responding=frame(state,energy=.08,signals={channel:.9})
                assert np.abs(resting.astype(float)-responding).mean()>.03,('audio channel inactive',state,channel)
            tiles=[]
            for material,key in (((1.,0.,0.),'artifacts'),((0.,1.,0.),'alloy'),((0.,0.,1.),'lattice')):
                plain=frame(state,mode=1,mask=BITS[key],material=material)
                folded=frame(state,mode=1,mask=BITS[key]+BITS['fractal']+BITS['tunnel'],material=material)
                assert np.abs(plain.astype(float)-folded).mean()>.03,('material folds missing',state,key)
                tiles.extend((plain,folded))
            save_png(output/f'materials-{state}.png',np.concatenate(tiles,axis=1))
            motion=[frame(state,t=t) for t in (0.,4.,8.,12.)]
            assert all(np.abs(a.astype(float)-b).mean()>.5 for a,b in zip(motion,motion[1:]))
            save_png(output/f'motion-{state}.png',np.concatenate(motion,axis=1))
        handoffs=0
        for a in (28,29,30):
            for b in (2,5,7,18,19,21,22,24,25,26,28,29,30):
                if a==b:continue
                tiles=[]
                for x in (0.,.25,.5,.75,1.):
                    pixels=frame(0,weights={a:1.-x,b:x},mode=2)
                    near=frame(0,weights={a:1.-min(1.,x+.0001),b:min(1.,x+.0001)},mode=2)
                    assert np.abs(pixels.astype(float)-near).mean()<2.,('handoff discontinuity',a,b,x)
                    assert pixels.std()>2.,('empty handoff',a,b,x)
                    handoffs+=1;tiles.append(pixels)
                if (a,b) in ((28,29),(29,30),(30,28),(28,5),(29,24)):
                    save_png(output/f'pair-{a}-{b}.png',np.concatenate(tiles,axis=1))
        for t in (38.,76.,114.):
            assert np.abs(frame(31,t=t-.0001).astype(float)-frame(31,t=t+.0001)).mean()<1.,('cycle seam',t)
        # Swap only the distant background in a diagnostic shader. Opaque foreground must not change.
        probe_source=source.replace('void main()', 'void unused_main()')
        probe_source=probe_source.replace('vec3 background=form==1 ? vec3(.013,.023,.035) : vec3(.006,.010,.025);','vec3 background=vec3(u_test_background,0.,u_test_background);')
        probe_source=probe_source.replace('uniform float u_time;','uniform float u_time;\nuniform float u_test_background;')
        probe_source+='''
void main() {
    vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;
    fragColor=vec4(fog_scene(p,vec3(.2),1),1.);
}
'''
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=probe_source)
        probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        try:
            for k,v in dict(u_resolution=(480.,270.),u_time=0.,u_drift_time=0.,u_scale=.2,u_flux=.2,u_sparkle=.2,u_impact=0.,u_fog_details=(0.,1.,1.)).items():
                if k in probe:probe[k].value=v
            tiles=[]
            for background in (0.,1.):
                probe['u_test_background'].value=background;probe_mesh.render(mode=moderngl.TRIANGLE_STRIP)
                tiles.append(np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy())
            assert np.array_equal(tiles[0][-65:],tiles[1][-65:]),'Background leaked through solid ground'
            assert np.abs(tiles[0].astype(float)-tiles[1]).mean()>10.,'Occlusion probe did not change background'
            save_png(output/'opaque-ground.png',np.concatenate(tiles,axis=1))
        finally:probe_mesh.release();probe.release()
        # Sample moving lamp clearance against actual terrain, and bound the curved route slope.
        clearance_source=source.replace('void main()', 'void unused_main()')+'''
void main() {
    float cell=floor(gl_FragCoord.x)-240.,side=gl_FragCoord.y<135. ? -1. : 1.;
    vec3 lamp=fog_lamp(cell,side);
    float clearance=fog_terrain(lamp).x;
    float z=cell*.37+u_time;
    float slope=length(fog_pressure_path(z+.01)-fog_pressure_path(z-.01))/.02;
    fragColor=vec4(clearance<.15 ? 1. : 0.,slope>1. ? 1. : 0.,0.,1.);
}
'''
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=clearance_source)
        probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        try:
            for t in np.linspace(0.,80.,25):
                probe['u_time'].value=float(t);probe_mesh.render(mode=moderngl.TRIANGLE_STRIP)
                pixels=np.frombuffer(r.ctx.screen.read(components=3),np.uint8)
                assert pixels.max()==0,('lamp intersects terrain or route too steep',t)
        finally:probe_mesh.release();probe.release()
        last=-1.
        for i in range(150):
            r.debug_state=28+(i//50)%3
            r.parameters.scale=r.parameters.flux=r.parameters.movement=.85 if i%50>20 else .03
            r.render(elapsed_time=i/30.)
            assert r.flow_time>last;last=r.flow_time
        (output/'precision.json').write_text(json.dumps(precision,indent=2))
        report=dict(preserved_frames=preserved,nebula_checks=6 if accepted_path else 0,pressure_checks=6 if accepted_path else 0,handoff_checks=handoffs,renderer_frames=150,opaque_ground=True,lamp_clearance_samples=24000)
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        if mesh is not None:mesh.release()
        if old is not None:old.release()
        r.close()


def earth_test(baseline_path,output):
    """Earth GPU integration, preserved worlds, effects and reversible handoffs."""
    from renderer import world_uniforms
    from preview_layers import BITS
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270,seed=42);old=mesh=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text())
        mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t=32.,energy=.7,hit=0.,weights=None,previous=False,details=(1.,1.,1.,1.),mask=2147483647,mode=0,material=(1.,0.,0.)):
            pr,vao=(old,mesh) if previous else (r.program,r.vao)
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),u_scale=energy,u_flux=energy,
                u_sparkle=energy,u_impact=hit,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),u_event_blasts=0,
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=material,u_air_flash_id=2.,u_air_afterglow=hit,
                u_daddy_long_legs=0.,u_earth_details=details,**world_uniforms(weights or {},enabled=weights is not None))
            for k,v in values.items():
                if k in pr:pr[k].value=v[:pr[k].dimension] if k=='u_earth_details' else v
            pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            pr['u_air_trails'].value=[(0.,0.)]*3
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        preserved=0
        for state in range(24):
            for mode in (0,2):
                a=frame(state,mode=mode);b=frame(state,mode=mode,previous=True)
                delta=np.abs(a.astype(float)-b)
                assert delta.max()<=1 and delta.mean()<.005,('old world changed',state,mode,delta.max(),delta.mean())
                preserved+=1
        for state in (24,25):
            stars=frame(state,t=16.,mode=1,mask=BITS['stars'])
            no_stars=frame(state,t=16.,mode=1,mask=0)
            assert np.abs(stars.astype(float)-no_stars).sum()>60,('Earth sky stars missing',state)
        effects=0
        for state in (24,25,26):
            quiet=frame(state,energy=.025);active=frame(state,energy=.85,hit=.65)
            assert quiet.std()>5 and active.std()>5,('blank',state)
            assert np.abs(quiet.astype(float)-active).mean()>1.,('unreactive',state)
            assert (active.min(axis=2)>250).mean()<.02,('white glare',state)
            save_png(output/f'form-{state}.png',np.concatenate((quiet,active),axis=1))
            base=frame(state,hit=.65)
            for i in range(3):
                detail=[1.,1.,1.,1.];detail[i]=0.
                disabled=frame(state,hit=.65,details=tuple(detail))
                difference=np.abs(base.astype(float)-disabled).sum()
                if i==2:
                    # Sparse world-attached glints need not occupy one fixed camera view.
                    for sample in (36.,40.):
                        on=frame(state,t=sample,hit=.65)
                        off=frame(state,t=sample,hit=.65,details=tuple(detail))
                        difference+=np.abs(on.astype(float)-off).sum()
                assert difference>60,('detail inactive',state,i)
                effects+=1
            tiles=[]
            for material,key in (((1.,0.,0.),'artifacts'),((0.,1.,0.),'alloy'),((0.,0.,1.),'lattice')):
                base=frame(state,mode=1,mask=BITS[key],material=material)
                pixels=frame(state,mode=1,mask=BITS[key]+BITS['fractal']+BITS['tunnel'],material=material)
                assert np.abs(base.astype(float)-pixels).mean()>.05,('material fold absent',state,key)
                tiles.extend((base,pixels));effects+=1
            save_png(output/f'effects-{state}.png',np.concatenate(tiles,axis=1))
            motion=[frame(state,t=t) for t in (0.,8.,16.,24.)]
            assert all(np.abs(a.astype(float)-b).mean()>.5 for a,b in zip(motion,motion[1:])),('no travel',state)
            save_png(output/f'motion-{state}.png',np.concatenate(motion,axis=1))
        # The creature must breach, disappear below opaque sand, and relocate.
        worm_frames=[]
        for t in (0.,8.,16.,24.,32.,40.,46.,54.,62.,70.,78.,86.):
            travel_time=t*(.75*.9+.035)/(.75*3.+.035)
            visible=frame(24,t=travel_time)
            absent=frame(24,t=travel_time,details=(1.,1.,1.,0.))
            difference=np.abs(visible.astype(float)-absent)
            if t in (0.,40.,46.,86.):
                assert difference.max()==0,('worm remains above sand at reset',t)
            if t in (16.,24.,62.,70.):
                assert difference.sum()>500,('worm failed to breach',t)
            worm_frames.append(visible)
        save_png(output/'worm-lifecycle.png',np.concatenate([
            np.concatenate(worm_frames[i:i+4],axis=1) for i in (0,4,8)],axis=0))
        checks=0
        for a in (24,25,26):
            for b in (2,5,7,18,19,21,22,24,25,26):
                if a==b:continue
                tiles=[]
                for x in (0.,.25,.5,.75,1.):
                    pixels=frame(0,weights={a:1.-x,b:x},mode=2)
                    near=frame(0,weights={a:1.-min(1.,x+.0001),b:min(1.,x+.0001)},mode=2)
                    assert np.abs(pixels.astype(float)-near).mean()<2.,('handoff discontinuity',a,b,x)
                    assert pixels.std()>2.,('empty handoff',a,b,x)
                    tiles.append(pixels);checks+=1
                if (a,b) in ((24,25),(25,26),(26,24),(24,7),(26,22)):
                    save_png(output/f'pair-{a}-{b}.png',np.concatenate(tiles,axis=1))
        # Native cycle boundaries and the wrap must stay continuous.
        for t in (36.,72.,108.):
            assert np.abs(frame(27,t=t-.0001).astype(float)-frame(27,t=t+.0001)).mean()<1.,('cycle seam',t)
        # The cave must actually enclose the view, including its ceiling and walls.
        probe_source=(Path(__file__).parent/'shaders/dream.frag').read_text()
        probe_source=probe_source.replace('void main()', 'void unused_main()')+"""
void main() {
    vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;
    EarthSurface s=earth_surface(p,2);
    fragColor=vec4(float(s.distance<90.),clamp(s.distance/55.,0.,1.),0.,1.);
}
"""
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=probe_source)
        probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        try:
            probe['u_resolution'].value=(480.,270.)
            for t in (0.,16.,32.,64.):
                for k,v in dict(u_time=t*.75,u_drift_time=t,u_scale=.7,u_flux=.7).items():
                    if k in probe:probe[k].value=v
                probe_mesh.render(mode=moderngl.TRIANGLE_STRIP)
                pixels=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)
                solid=pixels[:,:,0]>250
                assert solid.mean()>.93,('cave not enclosed',t,solid.mean())
                assert solid[-50:].mean()>.98,('missing ceiling',t)
                assert solid[:,:50].mean()>.98 and solid[:,-50:].mean()>.98,('missing walls',t)
        finally:
            probe_mesh.release();probe.release()
        last=-1.
        for i in range(120):
            r.debug_state=24+(i//40)%3;r.parameters.scale=.8;r.parameters.flux=.7
            r.parameters.impact=.7 if i%20==0 else 0.
            r.render(elapsed_time=i/30.)
            assert r.star_time>last;last=r.star_time
        # Real renderer integration: sustained energy accelerates, release coasts.
        previous=r.flow_time
        rates=[]
        for i in range(150):
            loud=40<=i<110
            r.parameters.movement=.9 if loud else .02
            r.parameters.scale=.85 if loud else .02
            r.parameters.flux=.8 if loud else .02
            r.parameters.impact=0.
            r.render(elapsed_time=4.+i/30.)
            assert r.flow_time>previous
            previous=r.flow_time
            rates.append(r.flow_rate)
        assert rates[100]>rates[35]*2.,('Earth failed to accelerate',rates[35],rates[100])
        assert rates[110]>rates[149]>0.,('Earth failed to coast',rates[110],rates[149])
        report=dict(preserved_frames=preserved,detail_material_checks=effects,handoff_checks=checks,renderer_frames=120)
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        if mesh is not None:mesh.release()
        if old is not None:old.release()
        r.close()


def air_test(baseline_path, output):
    """GPU preservation, isolated Air details, musical response and handoffs."""
    from renderer import world_uniforms
    from preview_layers import BITS
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270,seed=42);old=mesh=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text())
        mesh=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t=40.,energy=.7,hit=0.,weights=None,previous=False,disabled=None,flash_id=2.,afterglow=None,trails=None,experiment=0.,material=(1.,0.,0.),layer_mask=None):
            pr,vao=(old,mesh) if previous else (r.program,r.vao)
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),
                u_scale=energy,u_flux=energy,u_sparkle=energy,u_impact=hit,
                u_intensity=1.,u_distortion=1.,u_debug_state=float(state),u_event_blasts=0,
                u_layer_mode=0 if disabled is None else 1,
                u_layer_mask=2147483647 if disabled is None else 2147483647^BITS.get(disabled,0),
                u_material_mix=material,u_air_flash_id=flash_id,u_air_afterglow=hit if afterglow is None else afterglow,u_daddy_long_legs=experiment,
                **world_uniforms(weights or {},enabled=weights is not None))
            if layer_mask is not None:values.update(u_layer_mode=1,u_layer_mask=layer_mask)
            for key,value in values.items():
                if key in pr:pr[key].value=value
            if 'u_shockwaves' in pr:pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            if 'u_air_trails' in pr:pr['u_air_trails'].value=trails or [(0.,0.)]*3
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        preserved=0
        # Air integration preserves all authored held forms, including Vortex.
        for state in range(23):
            for t in (17.,83.):
                a=frame(state,t);b=frame(state,t,previous=True)
                delta=np.abs(a.astype(float)-b)
                assert delta.max()<=1 and delta.mean()<.005,('existing scene changed',state,t,delta.max(),delta.mean())
                preserved+=1
        # Custom non-Air worlds must also remain unchanged.
        for state in (2,5,7,8,9,10,13,14,15,17,18):
            a=frame(state,layer_mask=2147483647)
            b=frame(state,layer_mask=2147483647,previous=True)
            assert np.array_equal(a,b),('custom non-Air changed',state)
            preserved+=1
        effect_checks=0
        details=sum(BITS[k] for k in ('air_clouds','air_balloons','air_lightning','air_citadel','stars'))
        for state in (19,20,21,22):
            tiles=[]
            for material,key in (((1.,0.,0.),'artifacts'),((0.,1.,0.),'alloy'),((0.,0.,1.),'lattice')):
                mask=details+BITS[key]
                base=frame(state,material=material,layer_mask=mask)
                row=[base]
                for spatial in ('tunnel','fractal','horizon'):
                    pixels=frame(state,material=material,layer_mask=mask+BITS[spatial])
                    delta=float(np.abs(pixels.astype(float)-base).mean())
                    assert delta>.03,('Air effect invisible',state,key,spatial,delta)
                    assert (pixels.min(axis=2)>250).mean()<.015,('Air effect glare',state,key,spatial)
                    row.append(pixels);effect_checks+=1
                tiles.append(np.concatenate(row,axis=1))
            save_png(output/f'effects-{state}.png',np.concatenate(tiles,axis=0))
        for state in (19,20,21,22):
            tiles=[]
            for energy,hit in ((.03,0.),(.8,0.),(.8,.7)):
                a=frame(state,energy=energy,hit=hit);assert a.std()>4,(state,'blank')
                assert (a.min(axis=2)>250).mean()<.01,(state,'white wash')
                if state==20:
                    assert (a.max(axis=2)==0).mean()<.05,('storm invalid/black coverage',energy,hit)
                tiles.append(a)
            save_png(output/f'form-{state}.png',np.concatenate(tiles,axis=1))
            assert np.abs(tiles[0].astype(float)-tiles[2]).mean()>.3,(state,'unreactive')
        for state,key in ((19,'air_balloons'),(19,'air_clouds'),(19,'stars'),(20,'air_lightning'),(22,'air_citadel'),(22,'stars')):
            a=frame(state,hit=.7);b=frame(state,hit=.7,disabled=key)
            assert np.abs(a.astype(float)-b).sum()>100,(state,key,'isolation ineffective')
        assert np.abs(frame(20,hit=.7,flash_id=2.).astype(float)-frame(20,hit=.7,flash_id=3.)).mean()>.2
        assert np.abs(frame(21,afterglow=.6).astype(float)-frame(21)).mean()>.2
        assert np.array_equal(frame(21,disabled='air_lightning',afterglow=.6),
            frame(21,disabled='air_lightning',afterglow=0.))
        history=[(1.,.8),(0.,.3),(0.,0.)]
        assert np.abs(frame(21,trails=history).astype(float)-frame(21)).mean()>.2
        assert np.array_equal(frame(21,disabled='air_lightning',trails=history),
            frame(21,disabled='air_lightning'))
        assert np.abs(frame(21,disabled='air_lightning',experiment=1.).astype(float)
            -frame(21,disabled='air_lightning')).mean()>.2
        # Probe Air before shared material/spatial compositing can move pixels.
        source=(Path(__file__).parent/'shaders/dream.frag').read_text()
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source.split('\nvoid main()',1)[0]+'''
void main(){vec2 p=(gl_FragCoord.xy/u_resolution-.5)*vec2(u_resolution.x/u_resolution.y,1.);
fragColor=vec4(air_scene(p,vec3(.2,.1,.3),vec4(0.,0.,1.,0.)),1.);}
''')
        probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        saved_program,saved_vao=r.program,r.vao
        r.program,r.vao=probe,probe_mesh
        try:
            yy,xx=np.mgrid[:270,:480]
            for t in (1.,3.,5.,7.,11.,17.,23.,29.):
                clock=t*.1275
                eye_x=.05*np.sin(clock*.21);eye_y=.045*np.cos(clock*.17)
                # Match the original bolts' .08 inner exclusion, not the old
                # oversized .20 disk that also excluded the visible inner rim.
                eye=((xx+.5-240.)/270.-eye_x)**2+((269.5-yy)/270.-.5-eye_y)**2 < .075**2
                for energy in (.03,.8):
                    lit=frame(21,t=t,energy=energy)
                    unlit=frame(21,t=t,energy=energy,disabled='air_lightning')
                    assert np.array_equal(lit[eye],unlit[eye]),('lightning crosses eye',t,energy)
        finally:
            r.program,r.vao=saved_program,saved_vao
            probe_mesh.release();probe.release()
        # Closed gate, solid wall and empty former bridge space, probed from shader geometry.
        source=(Path(__file__).parent/'shaders/dream.frag').read_text()
        if 'air_castle_map' in source:
            probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source.split('\nvoid main()',1)[0]+'''
void main(){int i=int(gl_FragCoord.x);vec3 p=i==0 ? vec3(0.,.15,-.515) :
(i==1 ? vec3(.40,.25,-.48) : vec3(0.,.08,-.90));
fragColor=vec4(vec3(.5+air_castle_map(p).x),1.);}
''')
            probe_mesh=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
            target=r.ctx.simple_framebuffer((3,1),components=3);target.use()
            probe_mesh.render(mode=moderngl.TRIANGLE_STRIP)
            distances=np.frombuffer(target.read(components=3),np.uint8).reshape(3,3)[:,0]
            # Positive/negative sign denotes empty/solid; conservative distance
            # scaling for displaced rock intentionally changes the magnitude.
            assert distances[0]<127 and distances[1]<127 and distances[2]>128,distances
            r.ctx.screen.use();target.release();probe_mesh.release();probe.release()
        for state in (19,20,21,22):
            sequence=[frame(state,t=t) for t in (3.,7.,11.,15.)]
            assert all(np.abs(a.astype(float)-b).mean()>.5 for a,b in zip(sequence,sequence[1:])),('static scene',state)
            save_png(output/f'motion-{state}.png',np.concatenate(sequence,axis=1))
        for state in (19,20,21):
            assert np.array_equal(frame(state,disabled='none'),frame(state,disabled='air_citadel')),('castle remains',state)
        checks=0
        for a in (19,20,21,22):
            for b in (2,5,7,18,19,20,21,22):
                if a==b:continue
                tiles=[]
                for x in (0.,.25,.5,.75,1.):
                    pixels=frame(0,weights={a:1.-x,b:x});tiles.append(pixels)
                    near=frame(0,weights={a:1.-min(1.,x+.0001),b:min(1.,x+.0001)})
                    assert np.abs(pixels.astype(float)-near).mean()<2.,('handoff jump',a,b,x)
                    checks+=1
                if (a,b) in ((19,20),(20,21),(21,22),(22,5)):
                    save_png(output/f'pair-{a}-{b}.png',np.concatenate(tiles,axis=1))
        # Real render path uploads the new state/uniforms and preserves forward clocks.
        last=-1.
        for i in range(240):
            r.debug_state=19+(i//60)%4;r.parameters.scale=.8;r.parameters.flux=.7
            r.parameters.impact=.7 if i%30==0 else 0.
            r.render(elapsed_time=i/30.)
            assert r.star_time>last;last=r.star_time
        # The surface residue outlives the sharp flash, then clears without new hits.
        r.parameters.impact=.8;r.render(elapsed_time=8.)
        r.parameters.impact=0.;r.render(elapsed_time=8.25)
        assert r.air_afterglow>r.impact_envelope>0.
        old_seed=r.air_flash_id
        r.parameters.impact=.8;r.render(elapsed_time=8.3)
        assert r.air_flash_id==old_seed+1 and r.air_trails[0][0]==old_seed
        assert r.air_trails[0][1]>0. and r.air_afterglow>0.
        r.parameters.impact=0.;r.render(elapsed_time=16.)
        assert r.air_afterglow<.01
        assert all(strength<.01 for _,strength in r.air_trails)
        report=dict(preserved_frames=preserved,effect_checks=effect_checks,handoff_checks=checks,renderer_frames=244,
            note='Synthetic GPU and production-renderer tests; real music replay separate.')
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        if mesh is not None:mesh.release()
        if old is not None:old.release()
        r.close()


def fire_expression_test(output):
    from renderer import world_uniforms
    output.mkdir(parents=True,exist_ok=True)
    # Sustained bass with little spectral change must keep scenery travelling.
    coast=Renderer(seed=42);coast.parameters.scale=.9
    coast.parameters.movement=.1;coast.parameters.sparkle=.1;coast.flow_rate=.5
    for _ in range(120):coast.update_firescape_travel(1./60.)
    assert coast.firescape_rate>2.7 and coast.firescape_travel>.2
    fast=coast.firescape_rate;travel=coast.firescape_travel
    coast.parameters.scale=0.;coast.parameters.movement=0.;coast.parameters.sparkle=0.
    for _ in range(30):coast.update_firescape_travel(1./60.)
    assert coast.firescape_rate>fast*.8 and coast.firescape_travel>travel
    for _ in range(900):coast.update_firescape_travel(1./60.)
    assert coast.firescape_rate<.4,('never settles',coast.firescape_rate)
    # Cooldown/queued hits must never create a flash between onsets or in silence.
    timing=Renderer(seed=42);timing.debug_state=18
    for t,impact,expected in ((0.,0.,0),(.1,.8,1),(.2,0.,1),
            (.4,.25,1),(.5,0.,1),(.7,.25,1),(.8,0.,1),
            (1.,.25,1),(1.1,0.,1),(1.7,0.,1),(10.,0.,1),
            (10.1,.25,2),(12.,.25,2),(12.1,0.,2),(12.4,.8,3)):
        timing.parameters.impact=impact;timing.update_blasts(t)
        assert timing.blast_serial==expected,('off-onset birth',t,impact,timing.blast_serial)
    # Real event update logic under synthetic onsets; spacing stays bounded.
    events=Renderer(seed=42);events.debug_state=18;minimum=100.;births=0
    for i in range(2401):
        t=i*.05;events.parameters.impact=.8 if i%10==0 else 0.
        old=events.blast_serial;events.update_blasts(t);events.update_shockwaves(t)
        assert len(events.blast_events)<=8 and len(events.shockwaves)<=8
        if events.blast_serial!=old:
            assert events.parameters.impact>=.20,('birth between hits',t)
            births+=1;x,z=events.blast_events[-1][2:]
            for e in events.blast_events[:-1]:minimum=min(minimum,math.hypot(x-e[2],z-e[3]))
    assert births>35 and minimum>5.,(births,minimum)
    r=Renderer(width=480,height=270,seed=42);records=[]
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        def frame(state,energy,t=40.,mix=None):
            values=dict(u_time=t,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),
                u_scale=energy,u_flux=energy,u_sparkle=energy,u_impact=energy*.55,
                u_intensity=1.,u_distortion=1.,u_debug_state=float(state),u_layer_mode=2,
                u_layer_mask=134217727,u_material_mix=(1.,0.,0.),u_event_blasts=1,
                **world_uniforms(mix or {state:1.},enabled=mix is not None))
            for key,value in values.items():
                if key in r.program:r.program[key].value=value
            r.program['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            r.program['u_blast_events'].value=[(t-3.,0.,-8.,t*.3+25.),(t-9.,1.,12.,t*.3+40.)]+[(-1000.,-1.,0.,0.)]*6
            r.vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        for state in (14,15,17,18):
            tiles=[]
            for energy in (0.,.5,1.):
                pixels=frame(state,energy);tiles.append(pixels)
                coverage=float((pixels.max(axis=2)>35).mean())
                clipped=float((pixels.min(axis=2)>245).mean())
                assert clipped<.02,(state,energy,'white glare',clipped)
                records.append(dict(state=state,energy=energy,coverage=coverage,mean=float(pixels.mean())))
            save_png(output/f'form-{state}.png',np.concatenate(tiles,axis=1))
        flame=[x for x in records if x['state']==14]
        assert flame[0]['coverage']<.10 and flame[-1]['coverage']>.55,flame
        molten=[x for x in records if x['state']==15]
        assert molten[-1]['mean']>molten[0]['mean']*1.2,molten
        checks=0
        for a in (14,15,17,18):
            for b in (14,15,17,18):
                if a==b:continue
                tiles=[]
                for x in (0.,.25,.5,.75,1.):
                    pixels=frame(0,.8,mix={a:1.-x,b:x});tiles.append(pixels)
                    near=frame(0,.8,mix={a:1.-min(1.,x+.0001),b:min(1.,x+.0001)})
                    assert np.abs(pixels.astype(float)-near).mean()<2.,(a,b,x)
                    checks+=1
                if (a,b) in ((14,15),(15,17),(17,18)):
                    save_png(output/f'handoff-{a}-{b}.png',np.concatenate(tiles,axis=1))
        report=dict(samples=records,births=births,minimum_site_distance=minimum,handoff_checks=checks)
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:r.close()


def water_meld_test(baseline_path, output):
    """All Water pairs on the GPU; held forms and reverse handoffs included."""
    from renderer import world_uniforms
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=320,height=180);old=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text())
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(a,b,x,energy=.7,previous=False):
            pr,mesh=(old,vao) if previous else (r.program,r.vao)
            weights={a:1.-x,b:x} if a!=b else {a:1.}
            values=dict(u_time=60.,u_star_time=80.,u_drift_time=80.,u_resolution=(320.,180.),
                u_scale=energy,u_flux=energy*.8,u_sparkle=.4,u_impact=.1,
                u_intensity=1.,u_distortion=1.,u_debug_state=0.,u_layer_mode=2,
                u_layer_mask=134217727,u_material_mix=(1.,0.,0.),u_event_blasts=0,
                **world_uniforms(weights))
            for key,value in values.items():
                if key in pr:pr[key].value=value
            pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            mesh.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(180,320,3)[::-1].copy()
        states=(7,8,9,10,13);preserved=0;checks=0;max_delta=0.;rows={}
        for energy in (.05,.85):
            for a in states:
                assert np.array_equal(frame(a,a,0.,energy),frame(a,a,0.,energy,True)),('held changed',a,energy)
                preserved+=1
                for b in states:
                    if a==b:continue
                    for x in (0.,.2,.5,.8,1.):
                        pixels=frame(a,b,x,energy);assert pixels.std()>2,(a,b,x,'blank')
                        near=frame(a,b,min(1.,x+.0001),energy)
                        delta=float(np.abs(pixels.astype(float)-near).mean());max_delta=max(max_delta,delta)
                        assert delta<2.,('discontinuous',a,b,x,delta)
                        checks+=1
                        if energy>.8 and (a,b) in ((7,8),(8,13),(9,10),(10,13)):
                            before=frame(a,b,x,energy,True)
                            rows.setdefault((a,b),[]).append(np.concatenate((before,pixels),axis=1))
        for (a,b),tiles in rows.items():save_png(output/f'pair-{a}-{b}.png',np.concatenate(tiles,axis=0))
        report=dict(held_exact=preserved,handoff_checks=checks,max_progress_delta=max_delta,
            note='Synthetic GPU progress sweep, not audible real-time validation.')
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def musical_color_test(baseline_path, output):
    """Compare identical inputs on GPU, isolating pigment changes from animation."""
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270);old=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text())
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        records=[];preserved=0
        for state in (1,2,3,5,7,8,9,10,11,12,13,14,15,17,18):
            for profile,scale,flux,hit in (('quiet',.05,.02,0.),('body',.8,.7,0.),('hit',.8,.7,.6)):
                t=77.
                values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(480.,270.),
                    u_scale=scale,u_flux=flux,u_sparkle=.3,u_impact=hit,u_intensity=1.,u_distortion=1.,
                    u_debug_state=float(state),u_layer_mode=2,u_layer_mask=134217727,
                    u_material_mix=(1.,0.,0.),u_event_blasts=0,**blend_uniforms(t,False))
                images=[]
                for pr,mesh in ((old,vao),(r.program,r.vao)):
                    for key,value in values.items():
                        if key in pr:pr[key].value=value
                    pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
                    mesh.render(mode=moderngl.TRIANGLE_STRIP)
                    images.append(np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3).copy())
                a,b=images;delta=np.abs(a.astype(float)-b)
                if profile=='quiet' or state in (3,5,14,15,17,18):
                    assert delta.max()<=1 and np.count_nonzero(delta)<=12,(state,profile,'preservation',delta.max(),np.count_nonzero(delta))
                    preserved+=1
                peak=b.max(axis=2);old_peak=a.max(axis=2)
                dark=old_peak<=6
                assert not dark.any() or float(peak[dark].mean())<=float(old_peak[dark].mean())+1.,(state,profile,'dark lift')
                clipped=float((peak>=250).mean());old_clipped=float((old_peak>=250).mean())
                assert clipped<=old_clipped+.005,(state,profile,'highlight clipping',clipped,old_clipped)
                lit=(old_peak>30)&(old_peak<225)
                saturation=lambda im: (im.max(axis=2).astype(float)-im.min(axis=2))/np.maximum(im.max(axis=2),1)
                records.append(dict(state=state,profile=profile,delta=float(delta.mean()),
                    peak_gain=float((peak.astype(float)-old_peak)[lit].mean()) if lit.any() else 0.,
                    saturation_gain=float((saturation(b)-saturation(a))[lit].mean()) if lit.any() else 0.,clipped=clipped))
                if profile=='hit':save_png(output/f'state-{state}.png',np.concatenate((a[::-1],b[::-1]),axis=1))
        for state in (2,7,8,9,10,11,12,13):
            body=next(x for x in records if x['state']==state and x['profile']=='body')
            hit=next(x for x in records if x['state']==state and x['profile']=='hit')
            assert hit['delta']>body['delta'],(state,'no accent',body,hit)
        report=dict(preserved=preserved,comparisons=len(records),samples=records)
        (output/'checks.json').write_text(json.dumps(report,indent=2))
        print('Musical color passed:',{k:v for k,v in report.items() if k!='samples'},flush=True)
        print('Hit gains:',[x for x in records if x['profile']=='hit'],flush=True)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def director_test():
    """Exercise production selection with synthetic parameters, without graphics."""
    from renderer import handoff_kind, world_family
    def run(seed,profile,duration=600.,fps=20):
        r=Renderer(seed=seed);previous=None;target=None;events=[]
        for i in range(int(duration*fps)+1):
            t=i/fps
            energy=(.12 if profile=='quiet' else .85 if profile=='heavy'
                else (.15 if t%48<20 else .9))
            r.parameters.scale=r.parameters.movement=r.parameters.flux=energy
            r.parameters.impact=.8 if profile!='quiet' and i%(fps//2)==0 else 0.
            r.update_blend(t,0. if i==0 else 1/fps)
            v=r.blend_values;w=np.array(v['u_world_mix'])
            style,phase,source,target_family=v['u_handoff']
            if style:
                assert r.director_target is not None
                assert style==handoff_kind(r.director_current,r.director_target)
                assert (source,target_family)==(world_family(r.director_current),world_family(r.director_target))
                assert 0.<=phase<=1.
            assert (w>=0).all() and w.sum()<=1.000001
            assert sum(w>0)<=2,('stacked takeovers',t,w)
            assert abs(sum(v['u_water_mix'])+v['u_current_mix']-(1. if w[2]>0 else 0.))<1e-6
            assert abs(sum(v['u_fire_mix'])-(1. if w[3]>0 else 0.))<1e-6
            effective=np.append(w,(v['u_air_weight'],v['u_earth_weight'],v['u_fog_weight'],v['u_plasma_weight']))
            assert effective.sum()<=1.000001 and (effective>=0).all()
            if previous is not None:assert np.abs(effective-previous).max()<.03
            if target is not None and r.director_target is not None:
                assert target==r.director_target,('handoff interrupted',t)
            target=r.director_target;previous=effective
        events=r.director_history
        assert all(a['state']!=b['state'] for a,b in zip(events,events[1:]))
        assert all(b['seconds']-a['seconds']>=12. for a,b in zip(events,events[1:]))
        return r,events
    quiet,q=run(42,'quiet');heavy,h=run(42,'heavy');music,m=run(42,'sections')
    assert m==run(42,'sections')[1], 'Seeded replay not repeatable'
    assert [e['state'] for e in q]!=[e['state'] for e in h], 'Audio does not affect choices'
    assert len(h)>len(q), 'Quiet passages do not breathe longer'
    assert any(e['reason'] in ('energy lift','release') for e in m)
    assert {2,5}.issubset({e['state'] for e in h if e['seconds']<180.}), 'Favorite anchors starved'
    openings={run(seed,'sections',duration=0.)[1][0]['state'] for seed in range(16)}
    assert len(openings)>=5,openings
    # Same sampled section/onset pattern at two frame rates should pick the same forms.
    higher=run(42,'sections',fps=40)[1]
    assert [e['state'] for e in m]==[e['state'] for e in higher]
    assert max(abs(a['seconds']-b['seconds']) for a,b in zip(m,higher))<.5
    before=music.director_time;history=list(music.director_history)
    music.update_blend(900.,300.,False)
    assert music.director_time==before and music.director_history==history
    assert music.blend_values['u_directed']==0
    report=dict(quiet_visits=len(q),heavy_visits=len(h),section_visits=len(m),
        openings=sorted(openings),section_history=m)
    print('Director CPU checks passed:',report,flush=True)
    return report


def ownership_test(baseline_path, output):
    """Real GPU preservation and normalized, continuous regional coverage."""
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270);resources=[]
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        source=Path(__file__).with_name('shaders').joinpath('dream.frag').read_text()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text());resources.append(old)
        oldvao=r.ctx.simple_vertex_array(old,r.vertices,'in_position');resources.append(oldvao)
        def set_values(pr,values):
            for key,value in values.items():
                if key in pr:pr[key].value=value
        def frame(weights,previous=False):
            pr,vao=(old,oldvao) if previous else (r.program,r.vao)
            r.ctx.screen.use()
            values=dict(u_time=105.,u_star_time=140.,u_drift_time=140.,
                u_resolution=(480.,270.),u_directed=1,u_debug_state=0.,
                u_world_mix=tuple(weights),u_world_warp=0.,u_scale=.75,u_flux=.6,
                u_sparkle=.5,u_impact=.15,u_intensity=1.,u_distortion=1.,
                u_layer_mode=2,u_layer_mask=134217727,u_material_mix=(1.,0.,0.),
                u_water_mix=(1.,0.,0.,0.),u_current_mix=0.,u_fire_mix=(0.,0.,1.,0.),
                u_root_mix=0.,u_event_blasts=0)
            set_values(pr,values);pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)[::-1].copy()
        worlds=np.concatenate((np.zeros((1,4)),np.eye(4)))
        for w in worlds:assert np.array_equal(frame(w),frame(w,True)),('held world changed',w)
        main="""void main(){vec2 p=gl_FragCoord.xy/u_resolution-.5;
        p.x*=u_resolution.x/u_resolution.y;fragColor=world_coverage(u_world_mix,p);}"""
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source[:source.index('void main()')]+main);resources.append(probe)
        vao=r.ctx.simple_vertex_array(probe,r.vertices,'in_position');resources.append(vao)
        fbo=r.ctx.simple_framebuffer((64,36),components=4,dtype='f4');resources.append(fbo)
        probes=0;midpoints=[]
        for a in range(5):
            for b in range(a+1,5):
                previous=None
                for t in np.linspace(0.,1.,101):
                    w=worlds[a]*(1.-t)+worlds[b]*t
                    fbo.use();set_values(probe,dict(u_resolution=(64.,36.),u_drift_time=140.,u_world_mix=tuple(w)))
                    vao.render(mode=moderngl.TRIANGLE_STRIP)
                    d=np.frombuffer(fbo.read(components=4,dtype='f4'),np.float32).reshape(36,64,4).copy()
                    home=1.-d.sum(axis=2,keepdims=True);all_weights=np.concatenate((home,d),axis=2)
                    assert np.isfinite(d).all() and d.min()>=0. and home.min()>-1e-6
                    if previous is not None:
                        assert (all_weights[:,:,b]>=previous[:,:,b]-1e-6).all(),('nonmonotonic',a,b,t)
                        assert np.abs(all_weights-previous).max()<.10,('abrupt coverage',a,b,t)
                    if abs(t-.5)<1e-6:midpoints.append(float((all_weights.max(axis=2)>.8).mean()))
                    previous=all_weights;probes+=1
        # At equal global weight, substantial regions must belong to one world;
        # a uniform crossfade would leave every pixel at 50/50.
        assert min(midpoints)>.30,('coverage is still uniform',midpoints)
        for a,b,name in ((0,1,'organic-corridor'),(1,2,'corridor-planet'),(2,3,'planet-sea'),(3,4,'sea-firescape'),(4,2,'firescape-planet')):
            rows=[]
            for t in (.15,.35,.5,.65,.85):
                w=worlds[a]*(1.-t)+worlds[b]*t
                rows.append(np.concatenate((frame(w,True),frame(w)),axis=1))
            save_png(output/f'{name}.png',np.concatenate(rows,axis=0))
        # Supplemental Planet can overlap two scheduled worlds.
        for w in ((.2,.35,.45,0.),(0.,.3,.3,.4),(.25,.25,.25,.25)):
            pixels=frame(w);assert pixels.std()>2
        report=dict(held_exact=5,coverage_probes=probes,midpoint_dominant_fractions=midpoints,
            note='Synthetic GPU captures; visual review required, not live audio acceptance.')
        (output/'checks.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
    finally:
        for item in reversed(resources):item.release()
        r.close()


def corridor_clearance_test(baseline_path,output):
    """Probe physical hit distance: image contrast alone misses flat-wall clipping."""
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270);resources=[]
    # Reconstructed from Warbot Jazz's actual mapped audio/clock at 130.005s.
    fixture=dict(u_time=191.33928449385124,u_star_time=130.21263867972164,
        u_drift_time=130.00533333332754,u_scale=.9999999932109299,
        u_flux=.44514636959664877,u_sparkle=.9434865190292586,
        u_impact=.40443898880256096,u_intensity=1.,u_distortion=1.,
        u_debug_state=0.,u_layer_mode=2,u_layer_mask=134217727,
        u_material_mix=(.8334501385688782,0.,.16654987633228302),
        u_event_blasts=0,u_directed=1,u_world_mix=(1.,0.,0.,0.),
        u_water_mix=(0.,0.,0.,0.),u_current_mix=0.,u_fire_mix=(0.,0.,0.,0.),
        u_root_mix=0.,u_world_warp=0.,u_resolution=(480.,270.))
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        source=Path(__file__).with_name('shaders').joinpath('dream.frag').read_text()
        baseline=baseline_path.read_text()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline);resources.append(old)
        old_vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position');resources.append(old_vao)
        def set_values(program,values):
            for key,value in values.items():
                if key in program:program[key].value=value
        frames=[]
        for program,vao in ((old,old_vao),(r.program,r.vao)):
            r.ctx.screen.use();set_values(program,fixture)
            program['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            frames.append(np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3).copy())
        save_png(output/'recorded-failure-before-after.png',np.concatenate([x[::-1] for x in frames],axis=1))
        main="""void main(){vec2 p=gl_FragCoord.xy/u_resolution-.5;
        p.x*=u_resolution.x/u_resolution.y;GeometricSurface s=geometric_surface(p);
        fragColor=vec4(s.distance,s.kind,s.height,1.);}"""
        fbo=r.ctx.simple_framebuffer((64,36),components=4,dtype='f4');resources.append(fbo)
        probes=[]
        for text in (baseline,source):
            program=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=text[:text.index('void main()')]+main)
            resources.append(program);vao=r.ctx.simple_vertex_array(program,r.vertices,'in_position');resources.append(vao)
            probes.append((program,vao))
        def distances(pair,values):
            program,vao=pair;fbo.use();set_values(program,dict(values,u_resolution=(64.,36.)))
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(fbo.read(components=4,dtype='f4'),np.float32).reshape(36,64,4)[:,:,0].copy()
        old_distance=float(np.median(distances(probes[0],fixture)))
        new_distance=float(np.median(distances(probes[1],fixture)))
        assert old_distance<.03 and new_distance>1.0,(old_distance,new_distance)
        minimum=100.;count=0;worst=None
        for scale,flux,impact in ((.05,.02,0.),(.45,.45,.25),(1.,.45,.8),(1.,1.,1.)):
            for seconds in np.arange(0.,600.01,.25):
                values=dict(fixture,u_time=float(seconds*.75),u_drift_time=float(seconds),
                    u_scale=scale,u_flux=flux,u_impact=impact)
                d=distances(probes[1],values);median=float(np.median(d));count+=1
                if median<minimum:minimum=median;worst=(float(seconds),scale,flux,impact)
                assert np.isfinite(d).all() and median>.20,(seconds,scale,flux,impact,median)
        report=dict(recorded_old_median=old_distance,recorded_new_median=new_distance,
            sweep_frames=count,minimum_median=minimum,worst=worst)
        (output/'checks.json').write_text(json.dumps(report,indent=2))
        print('Corridor clearance passed:',report,flush=True)
    finally:
        for item in reversed(resources):item.release()
        r.close()


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
        renderer.program['u_directed'].value = 0
        renderer.program['u_layer_mode'].value = 0
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


def fire_test(baseline_path, output, molten_expansion=False, firescape_expansion=False):
    """Real GPU preservation, Fire headroom, layers and continuous-clock checks."""
    from preview_layers import BITS
    output.mkdir(parents=True, exist_ok=True)
    renderer=Renderer(width=320,height=180,title='Fire foundation checks')
    baseline=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);renderer.create()
        baseline=renderer.ctx.program(vertex_shader=VERTEX_SHADER,
            fragment_shader=baseline_path.read_text(encoding='utf-8'))
        vao=renderer.ctx.simple_vertex_array(baseline,renderer.vertices,'in_position')
        def frame(state, seconds, level=.4, mode=0, mask=0, overrides=None, old=False):
            program=baseline if old else renderer.program
            values=dict(u_time=seconds*.75,u_star_time=seconds,u_drift_time=seconds,
                u_resolution=(320.,180.),u_scale=level,u_flux=level,u_sparkle=level,
                u_impact=level*.3,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),
                u_layer_mode=mode,u_layer_mask=mask)
            values.update(overrides or {})
            for key,value in values.items():
                if key in program:program[key].value=value
            (vao if old else renderer.vao).render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(180,320,3).copy()
        preserved=0
        for state in range(16 if firescape_expansion else 15 if molten_expansion else 14):
            for seconds in (0.,42.,126.,147.,266.,686.):
                for level in (.05,.5,.95):
                    for mode,mask in ((0,0),(1,1)):
                        a=frame(state,seconds,level,mode,mask)
                        b=frame(state,seconds,level,mode,mask,old=True)
                        assert np.array_equal(a,b),(state,seconds,level,mode,np.abs(a.astype(float)-b).max())
                        preserved+=1
        samples=[];pictures=[]
        for level in (0.,.45,1.):
            for seconds in (0.,13.,42.,87.,160.,300.):
                pixels=frame(14,seconds,level)
                contrast=float(pixels.astype(float).std(axis=(0,1)).mean())
                dark=float((pixels.max(axis=2)<35).mean())
                clipped=float((pixels.max(axis=2)>=250).mean())
                assert contrast>12 and .25<dark<.97 and clipped<.001,(level,seconds,contrast,dark,clipped)
                samples.append(dict(level=level,seconds=seconds,contrast=contrast,dark=dark,clipped=clipped))
                if seconds==42.:
                    save_png(output/f'level-{level}.png',pixels[::-1]);pictures.append(pixels[::-1])
        save_png(output/'profiles.png',np.concatenate(pictures,axis=0))
        response={}
        base=frame(14,42.,0.)
        for key in ('u_scale','u_flux','u_sparkle','u_impact'):
            pixels=frame(14,42.,0.,overrides={key:1.})
            response[key]=float(np.abs(pixels.astype(float)-base).mean())
            assert response[key]>.02,(key,response[key])
        quiet_motion=float(np.abs(frame(14,44.,0.).astype(float)-base).mean())
        assert quiet_motion>.2,quiet_motion
        effects={}
        for key in ('artifacts','fire_coals','fire_embers','fire_seams'):
            differences=[]
            for seconds in (13.,42.,87.):
                off=frame(14,seconds,.7,1,0)
                on=frame(14,seconds,.7,1,BITS[key])
                differences.append(float(np.abs(on.astype(float)-off).mean()))
            effects[key]=max(differences)
            assert effects[key]>.005,(key,differences)
        # Below the flames, the lava bed must move but ignore abrupt audio.
        calm=frame(14,42.,0.)[:8]
        loud=frame(14,42.,1.,overrides={'u_impact':1.})[:8]
        assert np.array_equal(calm,loud), 'Lava bed twitches with audio'
        lava_motion=float(np.abs(frame(14,44.,0.)[:8].astype(float)-calm).mean())
        assert lava_motion>.05,lava_motion
        # Real onset amplitudes peak near .5; inspect its exponential cooling.
        cooling=[];cooling_metrics=[]
        for delay in (0.,.08,.5):
            pixels=frame(14,42.+delay,.45,overrides={'u_impact':.5*math.exp(-6.*delay)})
            cooling.append(pixels[::-1])
            foot=pixels[24:48].astype(float)
            cooling_metrics.append(dict(delay=delay,blue=float(foot[:,:,2].mean()),
                pale_pixels=int(((foot.min(axis=2)>150)&(foot.max(axis=2)-foot.min(axis=2)<65)).sum())))
        assert cooling_metrics[0]['pale_pixels']>50,cooling_metrics
        assert cooling_metrics[1]['blue']>cooling_metrics[2]['blue']+10,cooling_metrics
        assert cooling_metrics[2]['pale_pixels']<cooling_metrics[0]['pale_pixels'],cooling_metrics
        save_png(output/'cooling.png',np.concatenate(cooling,axis=0))
        if molten_expansion:
            molten_samples=[];molten_images=[]
            for level in (0.,.45,1.):
                for seconds in (0.,13.,42.,87.,160.,300.):
                    pixels=frame(15,seconds,level)
                    contrast=float(pixels.astype(float).std(axis=(0,1)).mean())
                    dark=float((pixels.max(axis=2)<35).mean())
                    clipped=float((pixels.max(axis=2)>=250).mean())
                    assert contrast>12 and .25<dark<.95 and clipped<.001,(level,seconds,contrast,dark,clipped)
                    molten_samples.append(dict(level=level,seconds=seconds,contrast=contrast,dark=dark,clipped=clipped))
                    if seconds==42.:molten_images.append(pixels[::-1])
            save_png(output/'molten-profiles.png',np.concatenate(molten_images,axis=0))
            molten_response={};base=frame(15,42.,0.)
            for key in ('u_scale','u_flux','u_sparkle','u_impact'):
                pixels=frame(15,42.,0.,overrides={key:1.})
                molten_response[key]=float(np.abs(pixels.astype(float)-base).mean())
                assert molten_response[key]>.02,(key,molten_response[key])
            molten_motion=float(np.abs(frame(15,44.,0.).astype(float)-base).mean())
            assert molten_motion>.2,molten_motion
            molten_effects={}
            for key in ('artifacts','fire_coals','fire_embers','fire_seams'):
                off=frame(15,42.,.7,1,0);on=frame(15,42.,.7,1,BITS[key])
                molten_effects[key]=float(np.abs(on.astype(float)-off).mean())
                assert molten_effects[key]>.005,(key,molten_effects[key])
            for seconds,state in ((0.,14),(10.,14),(28.,15),(40.,15),(56.,17),(68.,17),(84.,14),(94.,14)):
                assert np.array_equal(frame(16,seconds),frame(state,seconds)),(seconds,state)
            joins=[]
            for level in (.05,.5,.95):
                for seconds in (19.,28.,47.,56.,75.,84.,103.,112.):
                    delta=float(np.abs(frame(16,seconds+.01,level).astype(float)-frame(16,seconds-.01,level)).mean())
                    assert delta<2.,(level,seconds,delta)
                    joins.append(delta)
            steps=[];meld_images=[]
            for start in (19.,47.,75.):
                previous=None
                for i in range(271):
                    seconds=start+i/30.
                    pixels=frame(16,seconds,.6)
                    if previous is not None:
                        step=float(np.abs(pixels.astype(float)-previous).mean())
                        assert step<3.,(seconds,step)
                        steps.append(step)
                    previous=pixels.astype(float)
                    if i in (0,135,270):meld_images.append(pixels[::-1])
            save_png(output/'meld.png',np.concatenate(meld_images,axis=0))
            # A whole orbit must keep lava visible and the distant silhouette
            # stable; fixed elapsed-time tests include the far side of the river.
            orbit=[];orbit_images=[]
            for seconds in (0.,98.,196.,294.,392.,490.,588.,686.,784.):
                pixels=frame(15,seconds,.45)
                bright=float((pixels.max(axis=2)>70).mean())
                assert bright>.015,(seconds,bright)
                orbit.append(dict(seconds=seconds,bright_fraction=bright))
                orbit_images.append(pixels[::-1])
                delta=float(np.abs(frame(15,seconds+.02,.45).astype(float)-pixels).mean())
                assert delta<3.,(seconds,delta)
            save_png(output/'orbit.png',np.concatenate([
                np.concatenate(orbit_images[i:i+3],axis=1) for i in (0,3,6)],axis=0))
            # Inspect the actual shader's channel mask with the camera removed:
            # branching must change over time and remain connected to its parent.
            source=(Path(__file__).parent/'shaders/dream.frag').read_text(encoding='utf-8')
            probe_source=source.replace('fragColor = vec4(color, 1.0);',
                'fragColor = vec4(vec3(1.-smoothstep(.78,1.22,molten_channel((uv-.5)*vec2(16.,24.)).x/.76)),1.);')
            probe=renderer.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=probe_source)
            probe_vao=renderer.ctx.simple_vertex_array(probe,renderer.vertices,'in_position')
            masks=[];branch_counts=[]
            try:
                for seconds in (0.,42.,100.,170.):
                    for name,value in dict(u_drift_time=seconds,u_resolution=(320.,180.),u_debug_state=15.).items():
                        if name in probe:probe[name].value=value
                    probe_vao.render(mode=moderngl.TRIANGLE_STRIP)
                    mask=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(180,320,3)[:,:,0]>100
                    counts=(mask[:,1:] & ~mask[:,:-1]).sum(axis=1)
                    assert counts.max()>=3,(seconds,counts.max())
                    # Flood from a central parent pixel across the entire mask.
                    reached=np.zeros_like(mask);y,x=np.argwhere(mask)[len(np.argwhere(mask))//2];reached[y,x]=True
                    while True:
                        expanded=reached.copy()
                        expanded[1:]|=reached[:-1];expanded[:-1]|=reached[1:]
                        expanded[:,1:]|=reached[:,:-1];expanded[:,:-1]|=reached[:,1:]
                        expanded &= mask
                        if np.array_equal(expanded,reached):break
                        reached=expanded
                    assert reached.sum()/mask.sum()>.98,(seconds,reached.sum(),mask.sum())
                    masks.append(mask);branch_counts.append(int(counts.max()))
                changed=int(np.count_nonzero(masks[1]!=masks[2]))
                assert changed>100,changed
                save_png(output/'branches.png',np.concatenate([
                    np.repeat((m.astype(np.uint8)*255)[:,:,None],3,axis=2)[::-1] for m in masks],axis=1))
            finally:probe_vao.release();probe.release()
            molten_report=dict(samples=molten_samples,audio_response=molten_response,
                effect_response=molten_effects,quiet_motion=molten_motion,
                cycle_endpoint_checks=8,cycle_boundary_checks=len(joins),max_join=max(joins),
                meld_frames=813,max_meld_step=max(steps),orbit=orbit,
                max_row_channels=branch_counts,changed_channel_pixels=changed)
            (output/'molten.json').write_text(json.dumps(molten_report,indent=2),encoding='utf-8')
            print('PASS Molten: '+json.dumps(molten_report),flush=True)
        if firescape_expansion:
            wild_samples=[];wild_images=[]
            for level in (0.,.45,1.):
                for seconds in (0.,13.,42.,87.,160.,300.):
                    pixels=frame(17,seconds,level)
                    contrast=float(pixels.astype(float).std(axis=(0,1)).mean())
                    dark=float((pixels.max(axis=2)<35).mean())
                    clipped=float((pixels.max(axis=2)>=250).mean())
                    assert contrast>15 and .15<dark<.9 and clipped<.001,(level,seconds,contrast,dark,clipped)
                    wild_samples.append(dict(level=level,seconds=seconds,contrast=contrast,dark=dark,clipped=clipped))
                    if seconds==42.:wild_images.append(pixels[::-1])
            save_png(output/'firescape-profiles.png',np.concatenate(wild_images,axis=0))
            wild_effects={}
            for key in ('artifacts','fire_coals','fire_embers','fire_seams','fire_ash'):
                a=frame(17,42.,.7,1,0);b=frame(17,42.,.7,1,BITS[key])
                wild_effects[key]=float(np.abs(a.astype(float)-b).mean())
                assert wild_effects[key]>.005,(key,wild_effects[key])
            base=frame(17,42.,.45,overrides={'u_impact':0.})
            hit=frame(17,42.,.45,overrides={'u_impact':.5})
            brightness=float(hit.mean()-base.mean())
            assert brightness>2.,brightness
            assert (hit.max(axis=2)>=250).mean()<.001
            save_png(output/'beat.png',np.concatenate([base[::-1],hit[::-1]],axis=1))
            # Fixed world/time with a later integrated color phase must change hue.
            later=frame(17,42.,.45,overrides={'u_time':42.*.75+6.,'u_impact':0.})
            hue_change=float(np.abs(later.astype(float)-base).mean())
            assert hue_change>5.,hue_change
            # Actual scenery functions, fixed seed and camera: independently
            # verify sprouting, maturity, burning, collapse and an empty reset.
            source=(Path(__file__).parent/'shaders/dream.frag').read_text(encoding='utf-8')
            probe_source=source.replace('fragColor = vec4(color, 1.0);',
                'vec2 life_shape = uv.x < .5 ? firescape_tree(vec2((uv.x*2.-.5)*1.8,(uv.y-.1)*1.5),.37,fract(u_drift_time/64.)) : firescape_building(vec2(((uv.x-.5)*2.-.5)*1.2,(uv.y-.1)*1.2),.37,fract(u_drift_time/64.)); fragColor = vec4(life_shape,0.,1.);')
            probe=renderer.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=probe_source)
            probe_vao=renderer.ctx.simple_vertex_array(probe,renderer.vertices,'in_position')
            life_images=[];life_metrics=[]
            try:
                for age in (0.,.08,.20,.38,.56,.70,.84,.94,.999):
                    for name,value in dict(u_drift_time=age*64.,u_resolution=(320.,180.),u_debug_state=17.).items():
                        if name in probe:probe[name].value=value
                    probe_vao.render(mode=moderngl.TRIANGLE_STRIP)
                    pixels=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(180,320,3).copy()
                    tree=pixels[:,:160,0]>100;building=pixels[:,160:,0]>100
                    life_metrics.append(dict(age=age,tree_pixels=int(tree.sum()),building_pixels=int(building.sum()),
                        building_height=int(np.argwhere(building)[:,0].max()) if building.any() else 0))
                    # Neutral silhouettes plus hot edges for readable evidence.
                    display=np.repeat(pixels[:,:,0:1],3,axis=2).astype(float)*.65
                    display[:,:,0]+=pixels[:,:,1]*.65;display[:,:,1]+=pixels[:,:,1]*.2
                    life_images.append(np.clip(display,0,255).astype(np.uint8)[::-1])
            finally:probe_vao.release();probe.release()
            assert life_metrics[0]['tree_pixels']==life_metrics[0]['building_pixels']==0
            assert life_metrics[-1]['tree_pixels']==life_metrics[-1]['building_pixels']==0
            for key in ('tree_pixels','building_pixels'):
                assert 0<life_metrics[1][key]<life_metrics[2][key]<life_metrics[3][key],(key,life_metrics)
                assert life_metrics[6][key]<life_metrics[3][key],(key,life_metrics)
            assert life_metrics[7]['building_height']<life_metrics[3]['building_height']*.35,life_metrics
            save_png(output/'life-cycle.png',np.concatenate([
                np.concatenate(life_images[i:i+3],axis=1) for i in (0,3,6)],axis=0))
            # A pixel shift tracking the foreground camera must keep the hill
            # rooted to the same world position. Test via a GPU hill probe.
            scroll_source=source.replace('fragColor = vec4(color, 1.0);',
                'fragColor = vec4(vec3(firescape_hill(screen_p.x+firescape_scroll(1.55),2.)+.5),1.);')
            probe=renderer.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=scroll_source)
            probe_vao=renderer.ctx.simple_vertex_array(probe,renderer.vertices,'in_position')
            scroll_images=[]
            try:
                for seconds in (0.,(1./180.)/(.014*1.55)):
                    for name,value in dict(u_drift_time=seconds,u_resolution=(320.,180.),u_debug_state=17.).items():
                        if name in probe:probe[name].value=value
                    probe_vao.render(mode=moderngl.TRIANGLE_STRIP)
                    scroll_images.append(np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).reshape(180,320,3).copy())
                assert np.array_equal(scroll_images[0][:,1:],scroll_images[1][:,:-1]), 'Foreground terrain slides away from its world coordinate'
            finally:probe_vao.release();probe.release()
            wrap_steps=[]
            for seconds in (63.99,64.,64.01,127.99,128.):
                delta=float(np.abs(frame(17,seconds+.01,.45).astype(float)-frame(17,seconds-.01,.45)).mean())
                assert delta<3.,(seconds,delta)
                wrap_steps.append(delta)
            wild_report=dict(samples=wild_samples,effect_response=wild_effects,
                beat_brightness_increase=brightness,phase_color_change=hue_change,
                lifecycle=life_metrics,max_wrap_step=max(wrap_steps))
        # Actual renderer integration: rise, impact and release, no clock reset.
        renderer.debug_state=14
        previous=None;max_step=0.;hit_step=0.;last_clock=-1.;last_star=-1.
        for index in range(361):
            seconds=index/60.
            level=.5-.5*math.cos(seconds*math.pi/3.)
            renderer.parameters.scale=level;renderer.parameters.flux=level
            renderer.parameters.sparkle=level;renderer.parameters.movement=level
            renderer.parameters.impact=.6 if index==180 else 0.
            renderer.render(elapsed_time=seconds)
            assert renderer.flow_time>last_clock and renderer.star_time>last_star
            last_clock,last_star=renderer.flow_time,renderer.star_time
            pixels=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).astype(float)
            if previous is not None:
                step=float(np.abs(pixels-previous).mean())
                if index==180:hit_step=step
                else:max_step=max(max_step,step)
            previous=pixels
        assert max_step<3.,max_step
        assert hit_step<12.,hit_step  # Deliberate onset flash, not ordinary motion.
        if firescape_expansion:
            # Actual renderer: the same monotonic clock must settle to a faster
            # hue rate with stronger mids, without a jump/reset on the change.
            renderer.debug_state=17;rate_samples=[];previous_time=renderer.flow_time
            previous_pixels=None;wild_step=0.
            for index in range(360):
                renderer.parameters.movement=0. if index<180 else 1.
                renderer.parameters.scale=.45;renderer.parameters.flux=.35
                renderer.parameters.sparkle=.45;renderer.parameters.impact=0.
                renderer.render(elapsed_time=6.+(index+1)/60.)
                delta=renderer.flow_time-previous_time
                assert 0.<delta<.02,delta
                if index in (179,359):rate_samples.append(delta*60.)
                previous_time=renderer.flow_time
                pixels=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8).astype(float)
                if previous_pixels is not None:wild_step=max(wild_step,float(np.abs(pixels-previous_pixels).mean()))
                previous_pixels=pixels
            assert rate_samples[1]>rate_samples[0]*2.5,rate_samples
            assert wild_step<3.,wild_step
            wild_report.update(color_clock_rates=rate_samples,integrated_frames=360,max_step=wild_step)
            (output/'firescape.json').write_text(json.dumps(wild_report,indent=2),encoding='utf-8')
            print('PASS Firescape: '+json.dumps(wild_report),flush=True)
        report=dict(preserved_cases=preserved,samples=samples,audio_response=response,
            quiet_motion=quiet_motion,effect_response=effects,integrated_frames=361,max_step=max_step,
            lava_motion=lava_motion,cooling=cooling_metrics,hit_step=hit_step)
        (output/'fire.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('PASS Fire: '+json.dumps(report),flush=True)
    finally:
        if vao is not None:vao.release()
        if baseline is not None:baseline.release()
        renderer.close()


def main(debug_state=0, states=None, layers=None):
    renderer = Renderer(
        width=1280,
        height=720,
        title="ZeraWave - " + next(name for name, value in STATES.items() if value == debug_state),
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


def aftershock_test(baseline_path, output):
    """GPU preservation and persistent, bounded musical blast events."""
    output.mkdir(parents=True, exist_ok=True)
    r=Renderer(width=320,height=180)
    r.debug_state=18
    r.parameters.impact=.35;r.update_shockwaves(5.);assert not r.shockwaves
    # Sustained input creates one ring; new onsets require rearming/cooldown.
    r.parameters.impact=.8;r.update_shockwaves(5.)
    r.update_shockwaves(7.);assert len(r.shockwaves)==1
    r.parameters.impact=0.;r.update_shockwaves(7.1)
    r.parameters.impact=.7;r.update_shockwaves(8.2)
    assert len(r.shockwaves)==2
    for i in range(100):
        t=9.+i*.2;r.parameters.impact=.9 if i%2 else 0.;r.update_shockwaves(t)
        assert len(r.shockwaves)<=3
        assert all(b[0]-a[0]>=3.0 for a,b in zip(r.shockwaves,r.shockwaves[1:]))
        assert all(0<=t-e[0]<8 for e in r.shockwaves)
    r.parameters.impact=0.;r.update_shockwaves(50.);assert not r.shockwaves
    r.debug_state=14;r.parameters.impact=1.;r.update_shockwaves(51.);assert not r.shockwaves
    r.debug_state=18
    old=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text(encoding='utf-8'))
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t,level=.4,previous=False,events=(),mask=None):
            pr=old if previous else r.program
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(320.,180.),
                u_scale=level,u_flux=level,u_sparkle=level,u_impact=level*.5,
                u_intensity=1.,u_distortion=1.,u_debug_state=float(state),
                u_layer_mode=int(mask is not None),u_layer_mask=mask or 0)
            for k,v in values.items():
                if k in pr:pr[k].value=v
            if 'u_shockwaves' in pr:pr['u_shockwaves'].value=list(events)+[(-1000.,0.,0.,0.)]*(8-len(events))
            (vao if previous else r.vao).render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(180,320,3).copy()
        count=0
        for state in range(18):
            for t in (5.,28.,51.,79.,147.,266.):
                for level in (.05,.9):
                    assert np.array_equal(frame(state,t,level),frame(state,t,level,True)),(state,t,level)
                    count+=1
        images=[]
        for t in (5.03,7.,12.,24.,42.,49.,58.,77.04,90.):
            events=[(t-1.,float(max(0,math.floor((t-5.)/36.))),.9,0.),(t-2.5,float(max(0,math.floor((t-5.)/36.))),.8,0.)]
            pixels=frame(18,t,events=events)
            assert pixels.max()<250 and pixels.std()>8,(t,pixels.max(),pixels.std())
            images.append(pixels[::-1])
        save_png(output/'timeline.png',np.concatenate([np.concatenate(images[i:i+3],axis=1) for i in (0,3,6)],axis=0))
        silent=frame(18,24.)
        one=frame(18,24.,events=[(23.,0.,1.,0.)])
        two=frame(18,24.,events=[(23.,0.,1.,0.),(21.,0.,1.,0.)])
        assert np.abs(one.astype(float)-silent).mean()>.05
        assert np.abs(two.astype(float)-one).mean()>.05
        assert np.array_equal(silent,frame(18,24.,events=[(15.,0.,1.,0.)]))
        for bit,t in ((2097152,5.04),(4194304,8.),(8388608,8.),(16777216,24.)):
            assert np.abs(frame(18,t,mask=bit).astype(float)-frame(18,t,mask=0)).mean()>.03,(bit,t)
        flash_area=[]
        for t in (5.02,5.15,7.1):
            delta=np.abs(frame(18,t,mask=2097152).astype(float)-frame(18,t,mask=0))
            flash_area.append(int((delta.max(axis=2)>10).sum()))
        assert 0<flash_area[0]<flash_area[1] and flash_area[2]==0,flash_area
        assert np.abs(frame(18,5.8,mask=2097152).astype(float)-frame(18,5.8,mask=0)).mean()>1.
        source=(Path(__file__).parent/'shaders/dream.frag').read_text(encoding='utf-8')
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source.replace(
            'fragColor = vec4(color, 1.0);','fragColor = vec4(blast_cloud_order(u_drift_time)/255.,1.);'))
        probe_vao=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        try:
            for t,expected in ((120.,(2,3,1)),(156.,(2,4,3)),(192.,(5,4,3))):
                probe['u_drift_time'].value=t
                probe_vao.render(mode=moderngl.TRIANGLE_STRIP)
                assert tuple(r.ctx.screen.read(components=3)[:3])==expected,(t,expected)
        finally:
            probe_vao.release();probe.release()
        # Fixed site hues must differ, and the flash must invert source RGB.
        for expression,expected in (
                ('blast_material_negative(vec3(.5,.25,0.))',(51,153,255)),
                ('blast_material_negative(vec3(0.,.25,.5))',(255,153,51))):
            check=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source.replace(
                'fragColor = vec4(color, 1.0);',f'fragColor = vec4({expression},1.);'))
            check_vao=r.ctx.simple_vertex_array(check,r.vertices,'in_position')
            try:
                check_vao.render(mode=moderngl.TRIANGLE_STRIP)
                actual=tuple(r.ctx.screen.read(components=3)[:3])
                assert all(abs(a-b)<=1 for a,b in zip(actual,expected)),actual
            finally:
                check_vao.release();check.release()
        tint=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source.replace(
            'fragColor = vec4(color, 1.0);','fragColor = vec4(blast_plume_tint(floor(u_drift_time)),1.);'))
        tint_vao=r.ctx.simple_vertex_array(tint,r.vertices,'in_position')
        try:
            colors=[]
            for i in range(6):
                tint['u_drift_time'].value=float(i)
                tint_vao.render(mode=moderngl.TRIANGLE_STRIP)
                colors.append(np.array(tuple(r.ctx.screen.read(components=3)[:3]),dtype=float))
            assert all(np.linalg.norm(a-b)>90 for a,b in zip(colors,colors[1:]))
        finally:
            tint_vao.release();tint.release()
        unbent=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=source.replace('bend=.045*','bend=0.*'))
        unbent_vao=r.ctx.simple_vertex_array(unbent,r.vertices,'in_position')
        bending=[]
        try:
            for t in (5.8,24.):
                normal=frame(18,t)
                for key in unbent:
                    if key.startswith('u_') and key in r.program:
                        unbent[key].value=r.program[key].value
                unbent_vao.render(mode=moderngl.TRIANGLE_STRIP)
                straight=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(180,320,3)
                bending.append(float(np.abs(normal.astype(float)-straight).mean()))
            assert bending[0]>.05 and bending[1]<.01,bending
        finally:
            unbent_vao.release();unbent.release()
        # Real renderer path uploads history and maintains both continuous clocks.
        r.shockwaves=[];r.shockwave_armed=True;r.last_shockwave=-1000.
        for i in range(600):
            r.parameters.impact=.8 if i%45==0 else 0.
            before=(r.flow_time,r.star_time);r.render(i/60.+5.)
            assert r.flow_time>=before[0] and r.star_time>=before[1]
        assert len(r.shockwaves)>1
        glfw.set_window_size(r.window,1280,720);r.poll_events();r.render(50.)
        query=r.ctx.query(time=True)
        with query:
            for i in range(60):r.render(50.+(i+1)/60.)
        r.ctx.finish()
        gpu_ms=query.elapsed/1e6/60.
        report=dict(preserved_frames=count,renderer_frames=660,gpu_ms_720p=gpu_ms,event_history='passed',
            independent_rings='passed',expiry='passed',effects='passed',gpu=r.ctx.info['GL_RENDERER'])
        (output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(report)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def materials_test(baseline_path, output):
    """Real GPU preservation, material isolation, and cross-world meld checks."""
    from preview_layers import BITS, WORLDS, material_trio_profile, world_for_state
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=320,height=180);old=vao=None
    trio={world:material_trio_profile(world) for world in WORLDS}
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text(encoding='utf-8'))
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(state,t,level=.4,mode=0,mask=0,weights=None,previous=False):
            pr=old if previous else r.program
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,u_resolution=(320.,180.),
                u_scale=level,u_flux=level,u_sparkle=level,u_impact=level*.3,
                u_intensity=1.,u_distortion=1.,u_debug_state=float(state),
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=weights or (1.,0.,0.))
            for key,value in values.items():
                if key in pr:pr[key].value=value
            if 'u_shockwaves' in pr:pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            (vao if previous else r.vao).render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(180,320,3).copy()
        preserved=0;rounding=[]
        for state in range(19):
            for t in (0.,42.,83.9,126.,147.,266.):
                for mode,mask in ((0,0),(1,1)):
                    current=frame(state,t,mode=mode,mask=mask)
                    accepted=frame(state,t,mode=mode,mask=mask,previous=True)
                    delta=np.abs(current.astype(float)-accepted)
                    # Additional shader paths can change final 8-bit rounding.
                    # Bound this to single channel steps in at most eight samples;
                    # any visible/math regression still fails the comparison.
                    assert delta.max()<=1 and np.count_nonzero(delta)<=8,(state,t,mode,delta.max(),np.count_nonzero(delta),delta.mean())
                    if delta.any():rounding.append(dict(state=state,time=t,mode=mode,channels=int(np.count_nonzero(delta))))
                    preserved+=1
        responses=[];pictures=[]
        for state in range(19):
            if state==3:continue # Geometry study has no inherited-material canvas.
            off=frame(state,42.,mode=1)
            for key in ('alloy','lattice'):
                pixels=frame(state,42.,mode=1,mask=BITS[key])
                delta=float(np.abs(pixels.astype(float)-off).mean())
                assert delta>.001,(state,key,delta)
                responses.append(dict(state=state,material=key,response=delta))
            if state in (12,2,5,7,10,14,15,17,18):
                pictures.append(np.concatenate([frame(state,42.,mode=1,mask=BITS[k])[::-1]
                    for k in ('artifacts','alloy','lattice')],axis=1))
        save_png(output/'world-materials.png',np.concatenate(pictures,axis=0))
        # Freeze the world while fading materials: no illumination spike or cut.
        max_steps=[]
        for state in (0,2,5,7,10,12,14,15,17,18):
            _,mask=layers_at(trio,state,0.)
            for pair in ((0,1),(1,2),(2,0)):
                previous=None;largest=0.
                for i in range(61):
                    w=[0.,0.,0.];x=i/60.;x=x*x*(3.-2.*x)
                    w[pair[0]]=1.-x;w[pair[1]]=x
                    pixels=frame(state,42.,mode=2,mask=mask,weights=tuple(w)).astype(float)
                    if previous is not None:largest=max(largest,float(np.abs(pixels-previous).mean()))
                    previous=pixels
                assert largest<2.,(state,pair,largest)
                max_steps.append(largest)
        # Existing world entrances/releases with the independent material clock.
        joins=[]
        for state,times in ((0,(24.,44.,88.,112.,116.,126.,144.,158.,266.,284.,298.)),
                            (6,(19.04,28.,47.04,56.,75.04,84.,103.04,112.,131.04,140.)),
                            (16,(19.,28.,47.,56.,75.,84.))):
            for t in times:
                images=[]
                for seconds in (t-.01,t+.01):
                    mode,mask=layers_at(trio,state,seconds)
                    images.append(frame(state,seconds,mode=mode,mask=mask,
                        weights=materials_at(trio,state,seconds)).astype(float))
                delta=float(np.abs(images[1]-images[0]).mean())
                if delta>=3.:
                    legacy=float(np.abs(frame(state,t+.01,previous=True).astype(float)-frame(state,t-.01,previous=True)).mean())
                    control=float(np.abs(frame(state,t+.01,mode=2,mask=mask,weights=(1.,0.,0.)).astype(float)-frame(state,t-.01,mode=2,mask=mask,weights=(1.,0.,0.))).mean())
                    save_png(output/f'boundary-{state}-{t}.png',np.concatenate([im.astype(np.uint8)[::-1] for im in images],axis=1))
                    print('World boundary diagnostic',state,t,'new',delta,'accepted',legacy,'same-mode Living',control,flush=True)
                assert delta<3.,(state,t,delta)
                joins.append(delta)
        # Real renderer: material progression continues across diagnostic world switches.
        r.layer_profiles=trio;r.debug_sequence=(12,2,5,7,10,14,15,17,18,0)
        last=(-1.,-1.)
        for i in range(561):
            t=i*.5;r.render(t)
            assert r.flow_time>last[0] and r.star_time>last[1]
            assert np.allclose(r.program['u_material_mix'].value,materials_at(trio,r.state_at(t),t))
            last=(r.flow_time,r.star_time)
        report=dict(preserved_frames=preserved,quantization_differences=rounding,material_responses=responses,
            fixed_world_meld_frames=len(max_steps)*61,max_material_step=max(max_steps),
            world_boundary_checks=len(joins),max_world_boundary_step=max(joins),renderer_frames=561)
        (output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(report)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def blend_test(baseline_path, output, changed_states=()):
    """Main-default coverage, GPU handoffs and accepted held-world preservation."""
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270,seed=42); old=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text(encoding='utf-8'))
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        def frame(seconds,state=0,previous=False,authored=False,material=None):
            pr=old if previous else r.program
            mode,mask=layers_at({},state,seconds)
            if authored:mode,mask=0,0
            values=dict(u_time=seconds*.75,u_star_time=seconds,u_drift_time=seconds,
                u_resolution=(480.,270.),u_scale=.45,u_flux=.45,u_sparkle=.35,
                u_impact=.12,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=materials_at({},state,seconds))
            values.update(blend_uniforms(seconds,state==0 and not authored))
            if material is not None:
                from preview_layers import BITS
                values.update(u_layer_mode=1,u_layer_mask=BITS[material])
            for key,value in values.items():
                if key in pr:pr[key].value=value
            if 'u_shockwaves' in pr:pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            (vao if previous else r.vao).render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3).copy()
        # Corridor must recur and survive the supplemental Planet scheduler.
        for chapter in range(8):
            ids,spans=blend_chapter(chapter)
            assert ids.count(2)==4 and ids[1]==2
            assert all(a!=b for a,b in zip(ids,ids[1:]))
            if chapter:assert blend_chapter(chapter-1)[0][-1]!=ids[0]
        # Live Main uses the audio director; fixed chapters above are fixtures.
        director_test()
        differences=[];preserved=0
        for state in range(19):
            if state in changed_states:continue # Explicitly changed forms tested by the calling suite.
            for t in (0.,26.,77.,126.,177.,266.):
                a=frame(t,state,authored=True);b=frame(t,state,previous=True,authored=True)
                delta=np.abs(a.astype(float)-b)
                assert delta.max()<=1 and np.count_nonzero(delta)<=8,(state,t,delta.max(),np.count_nonzero(delta))
                preserved+=1
                if delta.any():differences.append((state,t,int(np.count_nonzero(delta))))
        seams=[];captures=[];tiles=[];coverage=set();holds=[]
        for chapter in range(3):
            ids,spans=blend_chapter(chapter)
            assert set(ids)==set(BLEND_FORMS)
            if chapter: assert blend_chapter(chapter-1)[0][-1]!=ids[0]
            start=chapter*360.
            for i,(state,span) in enumerate(zip(ids,spans)):
                coverage.add(state);holds.append(span)
                if chapter==0:
                    t=start+span*.3
                    pixels=frame(t)
                    assert pixels.std()>2,(state,t)
                    name=f'form-{state}-{t:.2f}.png';save_png(output/name,pixels[::-1])
                    tiles.append(pixels[::-1]);captures.append(dict(file=name,state=state,seconds=t,**blend_uniforms(t)))
                # Transition starts, midpoint, end; actual 20ms frame difference.
                for fraction in ((.68 if i%4==3 else .52),.8,1.):
                    t=start+span*fraction
                    a=frame(t-.01);b=frame(t+.01)
                    delta=float(np.abs(a.astype(float)-b).mean())
                    seams.append(dict(seconds=t,delta=delta))
                    if delta>=4.:
                        save_png(output/f'seam-{t:.2f}.png',np.concatenate((a[::-1],b[::-1]),axis=1))
                    # Fine procedural structure can move several pixel levels in
                    # 20ms. A true cut does not shrink when the interval shrinks;
                    # require convergence at 1ms instead of treating motion as a cut.
                    if delta>=4.:
                        near_a=frame(t-.0005);near_b=frame(t+.0005)
                        near_delta=float(np.abs(near_a.astype(float)-near_b).mean())
                        seams[-1]['delta_1ms']=near_delta
                        print('Transition motion',state,t,delta,'1ms',near_delta,flush=True)
                        assert near_delta < max(.15,delta*.2),(state,t,delta,near_delta)
                start+=span
        save_png(output/'overview.png',np.concatenate([np.concatenate(tiles[i:i+3]+[np.zeros_like(tiles[0])]*(3-len(tiles[i:i+3])),axis=1) for i in range(0,len(tiles),3)],axis=0))
        # New materials move with fixed audio, without changing geometry selection.
        motion={}
        for key in ('alloy','lattice'):
            a=frame(42.,12,material=key);b=frame(44.,12,material=key)
            motion[key]=float(np.abs(a.astype(float)-b).mean())
            assert motion[key]>1.
        # Default settings, same path as the live launcher; no preset required.
        r.layer_profiles={};r.debug_state=0
        last=(-1.,-1.);seen_materials=set();rings=0
        for i in range(721):
            t=i*.5;r.parameters.impact=.8 if i%8==0 else 0.;r.render(t)
            assert r.flow_time>last[0] and r.star_time>last[1]
            last=(r.flow_time,r.star_time)
            mix=r.program['u_material_mix'].value
            assert np.allclose(mix,materials_at({},0,t)) and abs(sum(mix)-1.)<1e-5
            assert r.program['u_directed'].value==1
            seen_materials.add(int(np.argmax(mix)))
            rings=max(rings,len(r.shockwaves))
        assert seen_materials=={0,1,2} and rings>0
        report=dict(preserved_frames=preserved,rounding=differences,covered_forms=sorted(coverage),
            transition_checks=len(seams),max_transition_delta=max(x['delta'] for x in seams),
            hold_range=[min(holds),max(holds)],material_motion=motion,renderer_frames=721,
            max_aftershock_rings=rings,transitions=seams,captures=captures)
        (output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print({k:v for k,v in report.items() if k not in ('captures','transitions')},flush=True)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def motion_test(baseline_path, output):
    """Hold composition/audio amplitude fixed to measure clock-driven travel."""
    from preview_layers import material_trio_profile
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=640,height=360);old=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text(encoding='utf-8'))
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        _,mask=layers_at({'blend':material_trio_profile('blend')},0,0.)
        def draw(t,clock,material,previous=False):
            pr=old if previous else r.program
            values=dict(u_time=clock,u_drift_time=t,u_star_time=t,u_resolution=(640.,360.),
                u_scale=.4,u_flux=.35,u_sparkle=.25,u_impact=.1,u_intensity=1.,u_distortion=1.,
                u_debug_state=0.,u_layer_mode=2,u_layer_mask=mask,
                u_material_mix=tuple(float(i==material) for i in range(3)),**blend_uniforms(t))
            for key,value in values.items():
                if key in pr:pr[key].value=value
            pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            (vao if previous else r.vao).render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(360,640,3).copy()
        rows=[];tiles=[]
        for state,t in ((11,8.),(13,37.),(2,90.),(10,259.),(5,287.)):
            for material in range(3):
                measures={}
                for previous in (True,False):
                    base=draw(t,30.,material,previous)
                    for name,rate in (('quiet',.35),('full',1.15)):
                        moved=draw(t,30.+.10*rate,material,previous)
                        measures[('before_' if previous else '')+name]=float(np.abs(moved.astype(float)-base).mean())
                assert measures['full']>measures['quiet']*1.15,(state,material,measures)
                rows.append(dict(state=state,material=material,**measures))
            if state in (13,10):
                tiles.append(np.concatenate([draw(t,30.,i)[::-1] for i in range(3)],axis=1))
        # The restored material travel must be measurable, not just a clock edit.
        currents=[row for row in rows if row['state']==13]
        assert all(row['full']>row['before_full']*1.15 for row in currents),currents
        save_png(output/'materials.png',np.concatenate(tiles,axis=0))
        # Same GPU, resolution, uniforms and sample count, no replay running.
        costs=[]
        for t in (8.,37.,90.,259.,287.):
            for previous in (True,False):
                draw(t,30.,1,previous)
                r.ctx.finish()
                mesh=vao if previous else r.vao
                with r.ctx.query(time=True) as query:
                    for i in range(30):mesh.render(mode=moderngl.TRIANGLE_STRIP)
                costs.append(dict(time=t,previous=previous,gpu_ms=query.elapsed/30/1e6))
        report=dict(motion=rows,gpu_costs_640x360=costs)
        (output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(report,flush=True)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def response_test(baseline_path, output):
    """Actual renderer musical scheduling, bounded event clouds and GPU coverage."""
    output.mkdir(parents=True,exist_ok=True)
    # CPU event checks: scheduling is independent of GPU throughput.
    r=Renderer();quiet=Renderer();visits=[];previous=0;births=[];serial=0;max_sites=0
    r.debug_state=18
    for i in range(1201):
        t=i*.05
        r.parameters.impact=.85 if i%10==0 else 0.
        r.update_blasts(t)
        max_sites=max(max_sites,len(r.blast_events))
        assert len(r.blast_events)<=8 and all(0<=t-e[0]<20 for e in r.blast_events)
        if r.blast_serial!=serial:births.append(t);serial=r.blast_serial
    assert len(births)>12 and max_sites==8 and min(np.diff(births))>=1.5-1e-8
    held=Renderer();held.debug_state=18;held.parameters.impact=1.
    for i in range(100):held.update_blasts(i*.05)
    assert held.blast_serial==1 and held.blast_hits<=1
    director_test()
    visits=[] # Visit cadence is now audio-selected rather than a fixed timer.
    old=vao=None;r=Renderer(width=480,height=270)
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline_path.read_text(encoding='utf-8'))
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        # Fixed uniforms preserve untouched held forms, independently of faster clock.
        preserved=0
        for state in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,17,18):
            for t in (26.,77.):
                values=dict(u_time=t*.75,u_drift_time=t,u_star_time=t,u_resolution=(480.,270.),
                    u_scale=.4,u_flux=.3,u_sparkle=.2,u_impact=.1,u_intensity=1.,u_distortion=1.,
                    u_debug_state=float(state),u_layer_mode=0,u_layer_mask=0,u_material_mix=(1.,0.,0.),u_event_blasts=0,
                    **blend_uniforms(t,False))
                images=[]
                for pr,mesh in ((old,vao),(r.program,r.vao)):
                    for key,value in values.items():
                        if key in pr:pr[key].value=value
                    pr['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
                    mesh.render(mode=moderngl.TRIANGLE_STRIP)
                    images.append(np.frombuffer(r.ctx.screen.read(components=3),np.uint8).copy())
                delta=np.abs(images[0].astype(float)-images[1])
                assert delta.max()<=1 and np.count_nonzero(delta)<=12,(state,t,delta.max(),np.count_nonzero(delta))
                preserved+=1
        # Real uniforms/clock: low energy remains slow, strong energy accelerates.
        frames=[];rate_quiet=0.;peak_rate=0.;last=(-1.,-1.);seen_visit=False
        for i in range(1201):
            t=i*.05;energy=0. if t<3. else .9
            r.parameters.scale=energy;r.parameters.movement=energy;r.parameters.flux=energy
            r.parameters.sparkle=energy*.7;r.parameters.impact=.7 if i%10==0 and t>3. else 0.
            r.render(t)
            assert r.flow_time>=last[0] and r.star_time>=last[1]
            last=(r.flow_time,r.star_time);peak_rate=max(peak_rate,r.flow_rate)
            if i==59:rate_quiet=r.flow_rate
            seen_visit|=r.planet_visits>0
            if i in (600,960,1100):
                pixels=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)
                save_png(output/f'main-{t:g}.png',pixels[::-1])
        assert rate_quiet<.36 and peak_rate>3.,(rate_quiet,peak_rate)
        # Force eight overlapping events and exercise the real depth-sorted shader.
        r.debug_state=18
        r.blast_events=[(60.+i*1.8,float(i),(-1 if i%2 else 1)*(2.+i*1.8),32.+i*5.) for i in range(8)]
        r.blast_serial=8;r.last_blast=72.6
        r.render(74.)
        pixels=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)
        assert pixels.std()>5
        save_png(output/'eight-sites.png',pixels[::-1])
        with r.ctx.query(time=True) as query:
            for i in range(20):r.vao.render(mode=moderngl.TRIANGLE_STRIP)
        cost=query.elapsed/20/1e6
        # Rotating molten shot and both colored siblings through actual renderer.
        from preview_layers import material_trio_profile
        r.debug_state=15;r.layer_profiles={'fire':material_trio_profile('fire')}
        r.render(80.)
        pixels=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3)
        save_png(output/'molten.png',pixels[::-1])
        report=dict(preserved_frames=preserved,planet_visits=visits,blast_births=births,max_sites=max_sites,
            quiet_rate=rate_quiet,peak_rate=peak_rate,renderer_frames=1203,eight_cloud_gpu_ms_480x270=cost)
        (output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(report,flush=True)
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def color_test(baseline,output):
    """Compare actual composite chroma/headroom, not just palette constants."""
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270);old=vao=None
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline.read_text())
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        results=[]
        for t in (8.,15.,30.,45.,62.,90.,125.,165.):
            mode,mask=layers_at({},0,t)
            values=dict(u_time=t*.75,u_star_time=t,u_drift_time=t,
                u_resolution=(480.,270.),u_scale=.45,u_flux=.45,u_sparkle=.25,
                u_impact=.12,u_intensity=1.,u_distortion=1.,u_debug_state=0.,
                u_layer_mode=mode,u_layer_mask=mask,u_material_mix=materials_at({},0,t),u_event_blasts=0)
            values.update(blend_uniforms(t))
            frames=[]
            for program,geometry in ((old,vao),(r.program,r.vao)):
                for key,value in values.items():
                    if key in program:program[key].value=value
                program['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
                geometry.render(mode=moderngl.TRIANGLE_STRIP)
                frames.append(np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3).copy())
            before,after=[x.astype(float)/255. for x in frames]
            lit=(before.max(2)>.06)&(after.max(2)>.06)
            saturation=[]
            for pixels in (before,after):
                peak=pixels.max(2)
                saturation.append(float(((peak-pixels.min(2))/np.maximum(peak,1e-6))[lit].mean()))
            clipped=float((after.max(2)>.99).mean())
            assert clipped<.03,(t,clipped)
            results.append(dict(seconds=t,before=saturation[0],after=saturation[1],clipped=clipped))
            save_png(output/f'compare-{t:.0f}.png',np.concatenate([x[::-1] for x in frames],axis=1))
        gain=float(np.mean([row['after']-row['before'] for row in results]))
        assert gain>.015,gain
        (output/'checks.json').write_text(json.dumps(dict(mean_saturation_gain=gain,frames=results),indent=2))
        print('Color checks passed; mean saturation gain',gain,'maximum clipping',max(x['clipped'] for x in results))
    finally:
        if vao is not None:vao.release()
        if old is not None:old.release()
        r.close()


def spatial_test(output):
    """GPU material/detail participation and continuous shared spatial envelopes."""
    from preview_layers import BITS, EFFECTS, WORLDS
    for key in ('tunnel','fractal','horizon'):
        assert EFFECTS[key][2] == WORLDS
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=480,height=270)
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        def frame(state,material,spatial,seconds=26.,mode=1):
            mask=sum(BITS[k] for k in EFFECTS if k not in
                ('artifacts','alloy','lattice','tunnel','fractal','horizon'))
            mask+=BITS[material]+sum(BITS[k] for k in spatial)
            values=dict(u_time=seconds*.75,u_star_time=seconds,u_drift_time=seconds,
                u_resolution=(480.,270.),u_scale=.6,u_flux=.65,u_sparkle=.45,
                u_impact=.1,u_intensity=1.,u_distortion=1.,u_debug_state=float(state),
                u_layer_mode=mode,u_layer_mask=mask,
                u_material_mix=tuple(float(k==material) for k in ('artifacts','alloy','lattice')))
            values.update(blend_uniforms(seconds,False))
            for key,value in values.items():
                if key in r.program:r.program[key].value=value
            r.program['u_event_blasts'].value=0
            r.program['u_shockwaves'].value=[(-1000.,0.,0.,0.)]*8
            r.vao.render(mode=moderngl.TRIANGLE_STRIP)
            return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(270,480,3).copy()
        # Read actual shader envelopes: every minute must contain unmistakable
        # full-strength Tunnel/Fractal holds, with bounded gaps between visits.
        source=Path(__file__).with_name('shaders').joinpath('dream.frag').read_text()
        probe=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=
            source[:source.index('void main()')]+"void main(){fragColor=vec4(spatial_weights(),1.);}")
        probe_vao=r.ctx.simple_vertex_array(probe,r.vertices,'in_position')
        schedule=[]
        try:
            for key,value in dict(u_directed=1,u_layer_mode=2,
                u_layer_mask=BITS['tunnel']|BITS['fractal']|BITS['horizon'],
                u_scale=.45,u_flux=.45).items():
                if key in probe:probe[key].value=value
            for second in range(181):
                probe['u_drift_time'].value=float(second)
                probe_vao.render(mode=moderngl.TRIANGLE_STRIP)
                schedule.append(tuple(r.ctx.screen.read(components=3)[:3]))
            for channel in (0,1):
                strong=np.array(schedule)[:,channel]>230
                for start in (0,60,120):assert strong[start:start+60].sum()>=20
                gap=0
                for present in strong:
                    gap=0 if present else gap+1
                    assert gap<=23,(channel,gap)
        finally:
            probe_vao.release();probe.release()
        results=[]
        for state in (2,5,7,8,9,10,12,13,14,15,17,18):
            tiles=[]
            for material in ('artifacts','alloy','lattice'):
                base=frame(state,material,())
                images=[base]
                for effect in ('tunnel','fractal','horizon'):
                    pixels=frame(state,material,(effect,))
                    delta=float(np.abs(pixels.astype(float)-base).mean())
                    assert delta>.08,(state,material,effect,delta)
                    assert pixels.std()>2,(state,material,effect)
                    results.append(dict(state=state,material=material,effect=effect,delta=delta))
                    images.append(pixels)
                tiles.append(np.concatenate([im[::-1] for im in images],axis=1))
            save_png(output/f'state-{state}.png',np.concatenate(tiles,axis=0))
        # Adjacent overlapping envelopes must converge even after an hour of travel.
        continuity=[]
        for state in (5,8,10,13):
            for t in (21.,65.,110.,3600.):
                a=frame(state,'alloy',('tunnel','fractal','horizon'),t-.01,2)
                b=frame(state,'alloy',('tunnel','fractal','horizon'),t+.01,2)
                delta=float(np.abs(a.astype(float)-b).mean())
                near_a=frame(state,'alloy',('tunnel','fractal','horizon'),t-.0005,2)
                near_b=frame(state,'alloy',('tunnel','fractal','horizon'),t+.0005,2)
                near=float(np.abs(near_a.astype(float)-near_b).mean())
                finest=None
                if near>=max(.25,delta*.25):
                    # At long elapsed times float32 clock steps approach 1ms.
                    # Distinguish steep procedural motion from a real cut with
                    # another convergence sample, rather than accepting the jump.
                    fa=frame(state,'alloy',('tunnel','fractal','horizon'),t-.0001,2)
                    fb=frame(state,'alloy',('tunnel','fractal','horizon'),t+.0001,2)
                    finest=float(np.abs(fa.astype(float)-fb).mean())
                    assert near<delta*.35 and finest<max(.08,near*.3),(state,t,delta,near,finest)
                continuity.append(dict(state=state,seconds=t,delta=delta,near=near,finest=finest))
        report=dict(participation=results,continuity=continuity,spatial_schedule=schedule)
        (output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('Spatial GPU checks passed:',len(results),'material/effect/world combinations;',len(continuity),'handoffs')
    finally:r.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--spatial-test", type=Path)
    parser.add_argument("--corridor-clearance-test", nargs=2,type=Path)
    parser.add_argument("--color-test", nargs=2, type=Path)
    parser.add_argument("--response-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--motion-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--blend-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--materials-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--aftershock-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--firescape-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--molten-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
    parser.add_argument("--fire-test", nargs=2, type=Path, metavar=("BASELINE", "OUTPUT"))
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
    parser.add_argument("--ownership-test", nargs=2, type=Path)
    parser.add_argument("--director-test", action="store_true")
    parser.add_argument("--choreography-test", nargs=2, type=Path)
    parser.add_argument("--musical-color-test", nargs=2, type=Path)
    parser.add_argument("--water-meld-test", nargs=2, type=Path)
    parser.add_argument("--fire-expression-test", type=Path)
    parser.add_argument("--plasma-reference", type=Path)
    parser.add_argument("--plasma-test", nargs=2, type=Path)
    parser.add_argument("--fog-test", nargs=2, type=Path)
    parser.add_argument("--fog-reference", type=Path, help="Accepted Fog shader for Nebula/Pressure preservation checks.")
    parser.add_argument("--earth-test", nargs=2, type=Path)
    parser.add_argument("--air-test", nargs=2, type=Path)
    args = parser.parse_args()
    if args.choreography_test:
        choreography_test(*args.choreography_test)
        raise SystemExit(0)
    if args.plasma_test:
        plasma_test(*args.plasma_test,accepted_path=args.plasma_reference)
        raise SystemExit(0)
    if args.fog_test:
        fog_test(*args.fog_test,accepted_path=args.fog_reference)
        raise SystemExit(0)
    if args.earth_test:
        earth_test(*args.earth_test)
        raise SystemExit(0)
    if args.air_test:
        air_test(*args.air_test)
        raise SystemExit(0)
    if args.fire_expression_test:
        fire_expression_test(args.fire_expression_test)
        raise SystemExit(0)
    if args.water_meld_test:
        water_meld_test(*args.water_meld_test)
        raise SystemExit(0)
    if args.musical_color_test:
        musical_color_test(*args.musical_color_test)
        raise SystemExit(0)
    if args.director_test:
        director_test()
        raise SystemExit(0)
    if args.ownership_test:
        ownership_test(*args.ownership_test)
        raise SystemExit(0)
    if args.corridor_clearance_test:
        corridor_clearance_test(*args.corridor_clearance_test)
        raise SystemExit(0)
    if args.color_test:
        color_test(*args.color_test)
        raise SystemExit(0)
    if args.spatial_test:
        spatial_test(args.spatial_test)
        raise SystemExit(0)
    if args.response_test:
        response_test(*args.response_test)
        blend_test(args.response_test[0],args.response_test[1]/'transitions',changed_states=(15,16))
    elif args.motion_test:
        motion_test(*args.motion_test)
    elif args.blend_test:
        blend_test(*args.blend_test)
    elif args.materials_test:
        materials_test(*args.materials_test)
    elif args.aftershock_test:
        aftershock_test(*args.aftershock_test)
    elif args.firescape_test:
        fire_test(*args.firescape_test,molten_expansion=True,firescape_expansion=True)
    elif args.molten_test:
        fire_test(*args.molten_test,molten_expansion=True)
    elif args.fire_test:
        fire_test(*args.fire_test)
    elif args.water_integration_test:
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
