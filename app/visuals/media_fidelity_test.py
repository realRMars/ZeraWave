"""Native source/shared-frame/texture/output fidelity; actual GPU, no audio."""
from pathlib import Path
import json,time,threading,uuid,hashlib,os
from types import SimpleNamespace
import numpy as np,moderngl,av
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from studio_composition import Canvas
from composition import defaults,new_layer
from media_registry import inspect,decode_image
from media_frames import MediaFrames,FrameReader
from image_layers import ImageLayers

def run():
    root=Path(__file__).resolve().parents[2];out=Path(os.environ['ZERAWAVE_MEDIA_EVIDENCE'])/('native-gpu-'+str(time.time_ns()));out.mkdir()
    app=QApplication([]);ctx=moderngl.create_standalone_context(require=330);vertices=ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());report=dict(evidence=__doc__,gpu=ctx.info['GL_RENDERER'],runs=[])
    for name in ('Xeraphina.jpg','Bobs Mock up.jpg','Xeraphina_video.mp4'):
        path=root/'images n vids'/name;asset=inspect(str(path),threading.Event());asset['id']=uuid.uuid4().hex;meta=asset['metadata'];size=(meta['width'],meta['height']);target=ctx.simple_framebuffer(size,components=4);target.use();ctx.viewport=(0,0,*size)
        class Proxy:
            screen=target
            def __getattr__(self,key):return getattr(ctx,key)
        stage=ImageLayers(Proxy(),vertices);owner=MediaFrames();reader=FrameReader();scene=defaults();scene.update(canvas=list(size),presentation='Layers only',assets=[asset]);row=new_layer('Video' if asset['kind']=='Video' else 'Image',asset['id']);scene['layers']=[row]
        try:
            frame=None
            if asset['kind']=='Video':
                owner.sync(scene,{asset['id']:asset});owner.command(row['id'],'seek',2.);end=time.perf_counter()+8
                while time.perf_counter()<end:
                    state=owner.snapshot()[row['id']];desc=state['frame'];frame=reader.read(desc) if desc else None
                    if frame:break
                    time.sleep(.01)
                assert frame,state;expected=frame['data'];scene['runtime']=owner.snapshot()
                # Independent FFmpeg reference at the actual published PTS.
                with av.open(str(path)) as container:
                    stream=container.streams.video[0];container.seek(int(frame['pts']/float(stream.time_base)),stream=stream,backward=True)
                    original=next(f for f in container.decode(stream) if f.pts is not None and abs(float(f.pts*stream.time_base)-frame['pts'])<.00001)
                    reference=original.to_ndarray(format='rgba')[::-1].tobytes();assert reference==expected
            else:_,expected=decode_image(path)
            stage.request(scene,1,'native-fidelity');end=time.perf_counter()+8
            while stage.pending and time.perf_counter()<end:stage.poll();time.sleep(.005)
            assert not stage.error and not stage.pending,stage.snapshot();target.clear(0,0,0,1)
            with ctx.query(time=True) as query:stage.draw(size)
            gpu_ms=query.elapsed/1e6;actual=target.read(components=4,alignment=1);delta=np.abs(np.frombuffer(actual,np.uint8).astype('i2')-np.frombuffer(expected,np.uint8).astype('i2'));assert delta.max()<=1,(name,delta.max())
            QImage(actual,*size,QImage.Format_RGBA8888).flipped().save(str(out/(name+'-output.png')))
            QImage(expected,*size,QImage.Format_RGBA8888).flipped().save(str(out/(name+'-reference.png')))
            textures=list(stage.animated.values()) if frame else list(stage.textures.values());assert any(t.size==size for t in textures)
            native=QImage(expected,*size,QImage.Format_RGBA8888_Premultiplied).flipped().convertToFormat(QImage.Format_ARGB32_Premultiplied);editor=SimpleNamespace(config=scene,canvas_size=size,images={asset['id']:native},metadata=lambda row:meta,selected_row=lambda:None,cancel_preview=lambda:None,sync_tool_ui=lambda:None);canvas=Canvas(editor);canvas.resize(*size);canvas.zoom=1.;canvas.show();app.processEvents();image=canvas.grab().toImage().convertToFormat(QImage.Format_ARGB32_Premultiplied);width=min(400,size[0]-4);height=min(400,size[1]-4);x=(size[0]-width)//2;y=(size[1]-height)//2;detail=image.copy(x,y,width,height);reference=native.copy(x,y,width,height);detail.save(str(out/(name+'-editor-detail.png')));assert bytes(detail.constBits())==bytes(reference.constBits());dpr=canvas.devicePixelRatioF();canvas.close()
            report['runs'].append(dict(file=name,input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=meta,decoded=list(size),editor_cache=list(size),editor_viewport=list(size),editor_zoom=1.,editor_dpr=dpr,editor_detail_max_difference=0,texture=list(size),internal=list(size),output=list(size),source_pts=frame['pts'] if frame else None,maximum_byte_difference=int(delta.max()),mean_byte_difference=float(delta.mean()),gpu_draw_ms=gpu_ms,measurement='Single query instrumented native technical output; no FPS/scanout claim'))
        finally:reader.close();assert owner.close();stage.close();target.release()
    vertices.release();ctx.release();(out/'RESULT.json').write_text(json.dumps(report,indent=2));print('PASS',out,report,flush=True)

if __name__=='__main__':run()
