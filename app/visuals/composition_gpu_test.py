"""Bounded real-GL/shared video integration and component cost, no audio/world.

Uses a visible GLFW window with swap interval 1. Query arm holds decoded pixels;
ordinary arm has live silent decoding and no queries/readbacks. Swap returns are
not measured scanout. The completed world is a fixed colour technical backdrop.
"""
from pathlib import Path
from copy import deepcopy
import json,time,threading,uuid,hashlib,os
import numpy as np,moderngl,glfw
from composition import defaults,new_layer,transform
from media_registry import inspect
from media_frames import MediaFrames
from image_layers import ImageLayers

def stats(values):
    a=np.asarray(values,float)
    return dict(n=len(a),mean=float(a.mean()),median=float(np.median(a)),p95=float(np.percentile(a,95)),p99=float(np.percentile(a,99)),maximum=float(a.max()),over_50ms=int(sum(a>50)))

def run():
    root=Path(__file__).resolve().parents[2];out=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(root/'work/media-composition-20261007')));stamp=str(time.time_ns());report=dict(evidence='Actual GPU + ordinary visible GLFW swap returns; technical backdrop, no world/audio/scanout',source={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('image_layers.py'),Path(__file__).with_name('media_frames.py'),Path(__file__).with_name('composition.py')]})
    assets=[]
    for name in ('Xeraphina.jpg','Bobs Mock up.jpg','Xeraphina_video.mp4'):
        asset=inspect(str(root/'images n vids'/name),threading.Event());asset['id']=uuid.uuid4().hex;assets.append(asset)
    assert glfw.init();glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3);glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3);glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
    window=glfw.create_window(1280,720,'ZeraWave composition component check',None,None);assert window;glfw.make_context_current(window);glfw.swap_interval(1)
    ctx=moderngl.create_context(require=330);vertices=ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());stage=ImageLayers(ctx,vertices);owner=MediaFrames();size=glfw.get_framebuffer_size(window);ctx.viewport=(0,0,*size);revision=0;report.update(gpu=ctx.info['GL_RENDERER'],window=glfw.get_window_size(window),framebuffer=size,internal=size,viewport=ctx.viewport,swap_interval=1,refresh_hz=glfw.get_video_mode(glfw.get_primary_monitor()).refresh_rate,background_load='No other Python sessions in preceding process inventory; thermal/power state uncontrolled')
    scene=defaults();scene['assets']=assets[:2]
    for i,asset in enumerate(assets[:2]):row=new_layer(asset=asset['id']);row.update(order=i,opacity=.55,transform=transform((i-.5)*.25,0.,.65));scene['layers'].append(row)
    def apply():
        nonlocal revision
        owner.sync(scene,{a['id']:a for a in assets});revision+=1;stage.request(dict(scene,runtime=owner.snapshot()),revision,'component-check');end=time.perf_counter()+10
        while stage.pending and time.perf_counter()<end:stage.poll();time.sleep(.01)
        assert not stage.error,stage.snapshot()
    def draw():ctx.screen.use();ctx.viewport=(0,0,*size);ctx.screen.clear(.04,.08,.12,1.);stage.runtime=owner.snapshot();stage.draw(size);assert not stage.error,stage.snapshot()
    def measure(label,moving=False):
        if moving:owner.command(video['id'],'play')
        for i in range(20):draw();glfw.swap_buffers(window);glfw.poll_events()
        submit=[];interval=[];upload=[];sequence=[];decode=[];last_frame=None;began=time.perf_counter();last=began
        while time.perf_counter()-began<2.4:
            t=time.perf_counter();draw();submit.append((time.perf_counter()-t)*1000);upload.append(stage.upload_ms);glfw.swap_buffers(window);now=time.perf_counter();interval.append((now-last)*1000);last=now;glfw.poll_events()
            if moving:
                sequence.append(deepcopy(stage.frames.last));state=owner.snapshot()[video['id']];assert not state['error']
                frame=state.get('frame') or {};identity=(frame.get('generation'),frame.get('pts'))
                if identity!=last_frame and frame:decode.append(frame['decode_ms']);last_frame=identity
        if moving:owner.command(video['id'],'pause')
        draw();gpu=[];queries=[]
        for i in range(24):
            ctx.screen.clear(.04,.08,.12,1.);t=time.perf_counter()
            with ctx.query(time=True) as q:stage.draw(size)
            gpu.append(q.elapsed/1e6);queries.append((time.perf_counter()-t)*1000)
        # Capture excluded from all distributions.
        draw();from PySide6.QtGui import QImage
        data=ctx.screen.read(components=4,alignment=1);image=QImage(data,*size,QImage.Format_RGBA8888).mirrored(False,True);assert image.save(str(out/(label+'-'+stamp+'.png')))
        nonzero_upload=[u for u in upload if u>0]
        result=dict(ordinary_swap_interval_ms=stats(interval),ordinary_cpu_draw_ms=stats(submit),upload_call_ms=stats(nonzero_upload) if nonzero_upload else None,observed_changed_frame_decode_ms=stats(decode) if decode else None,timing_scope='Upload is CPU wall around texture write/allocation; decode is worker get+conversion for observed changed publications; CPU draw includes driver backpressure, not isolated CPU cost.',gpu_resident_compositor_ms=stats(gpu),query_arm_call_including_wait_ms=stats(queries),ordinary_seconds=last-began,swap_return_rate=len(interval)/(last-began),stage=stage.snapshot(),animation=owner.snapshot(),presented_shared_sequences=sequence,passes='root copy + one fullscreen blend per layer/group + final copy; isolated ping-pong targets per group depth')
        report[label]=result
    try:
        apply();measure('two-stills')
        group=new_layer('Group');group.update(order=0,opacity=.75,transform=transform(.05,0.,.9));group['masks']=[dict(mode='Keep',enabled=True,points=[[.05,.05],[.95,.05],[.95,.95],[.05,.95]])]
        for row in scene['layers']:row['parent']=group['id']
        scene['layers'].append(group);video=new_layer('Video',assets[2]['id']);video.update(order=1,transform=transform(.05,.05,.65));video['media'].update(loop='Ping-pong',start=.2,end=1.6);scene['layers'].append(video);scene['assets']=assets
        apply();measure('group-and-video',True)
        assert len({json.dumps(x,sort_keys=True) for x in report['group-and-video']['presented_shared_sequences']})>10
        scene['presentation']='World only';apply();draw();assert not stage.animated and not stage.frames.maps
        report['world_only_cleanup']='Animated GPU/shared-reader resources released; stack retained'
        (out/('component-cost-'+stamp+'.json')).write_text(json.dumps(report,indent=2));print('PASS',out/('component-cost-'+stamp+'.json'),flush=True)
    except Exception:
        import traceback
        report['failure']=traceback.format_exc();(out/('component-failure-'+stamp+'.json')).write_text(json.dumps(report,indent=2));raise
    finally:stage.close();assert owner.close();vertices.release();ctx.release();glfw.destroy_window(window);glfw.terminate()

if __name__=='__main__':run()
