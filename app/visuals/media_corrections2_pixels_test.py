"""Synthetic Qt/GPU parity and real-image magnetic attribution, no presentation claim."""
import sys,os,time,json,threading,uuid
from pathlib import Path
from types import SimpleNamespace
import numpy as np,moderngl
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from composition import defaults,new_layer,BLENDS
from media_registry import inspect
from artwork import magnetic_point
from studio_composition import Canvas
from image_layers import ImageLayers

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);assets=[];images={}
    for name,color in (('back',QColor(35,115,185)),('front',QColor(235,75,110,160))):
        image=QImage(320,180,QImage.Format_ARGB32_Premultiplied);image.fill(color);path=out/(name+'.png');assert image.save(str(path));asset=inspect(str(path.resolve()),threading.Event());asset['id']=uuid.uuid4().hex;assets.append(asset);images[asset['id']]=image
    scene=defaults();scene.update(presentation='Layers only',canvas=[320,180],assets=assets);scene['layers']=[new_layer(asset=a['id']) for a in assets]
    for i,row in enumerate(scene['layers']):row.update(order=i,fit='Stretch')
    scene['layers'][1]['opacity']=.7
    editor=SimpleNamespace(config=scene,canvas_size=(320,180),images=images,selected_row=lambda:None,metadata=lambda row:dict(width=320,height=180),cancel_preview=lambda:None,sync_tool_ui=lambda:None)
    canvas=Canvas(editor);canvas.resize(320,180);canvas.zoom=1;canvas.show();app.processEvents()
    ctx=moderngl.create_standalone_context(require=330);target=ctx.simple_framebuffer((320,180),components=4);target.use();ctx.viewport=(0,0,320,180)
    class Proxy:
        screen=target
        def __getattr__(self,key):return getattr(ctx,key)
    vertices=ctx.buffer(np.asarray([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());stage=ImageLayers(Proxy(),vertices);report=dict(gpu=ctx.info['GL_RENDERER'],evidence=__doc__,blends=[]);revision=0
    try:
        for mode in BLENDS:
            for strength in (1.,.35):
                scene['layers'][1].update(blend=mode,blend_strength=strength);revision+=1;stage.request(scene,revision,'parity');deadline=time.monotonic()+5
                while stage.pending and time.monotonic()<deadline:stage.poll();time.sleep(.005)
                assert not stage.error and not stage.pending,stage.snapshot();target.use();target.clear(0,0,0,0);stage.draw((320,180));data=target.read(components=4,alignment=1);gpu=np.frombuffer(data,np.uint8).reshape(180,320,4)[90,160]
                canvas.update();app.processEvents();qt=canvas.grab().toImage().pixelColor(160,90);pixel=np.array(qt.getRgb());delta=int(np.max(abs(gpu.astype(int)-pixel)));assert delta<=2,(mode,strength,gpu,pixel)
                report['blends'].append(dict(mode=mode,strength=strength,opacity=.7,qt=pixel.tolist(),gpu=gpu.tolist(),max_byte_delta=delta))
        # Overlapping same-parent order really changes the sample in both paths.
        scene['layers'][1].update(blend='Normal',blend_strength=1);scene['layers'][0]['order']=1;scene['layers'][1]['order']=0;canvas.update();app.processEvents();assert canvas.grab().toImage().pixelColor(160,90)==QColor(35,115,185)
        scene['layers'][0]['order']=0;scene['layers'][1]['order']=1;canvas.update();app.processEvents();assert canvas.grab().toImage().pixelColor(160,90)!=QColor(35,115,185);report['sibling_order']='Distinct front/back output with identical parent'
        native=QImage(str(Path(__file__).resolve().parents[2]/'images n vids/Xeraphina.jpg'));gray=native.convertToFormat(QImage.Format_Grayscale8);w,h=gray.width(),gray.height();a=np.frombuffer(gray.constBits(),np.uint8).reshape(h,gray.bytesPerLine())[:,:w].astype(float);gy,gx=np.gradient(a);gradient=np.hypot(gx,gy);cases=[]
        for y in range(20,h-20,13):
            for x in range(20,w-20,13):
                uv=[x/w,y/h];snapped=magnetic_point(native,uv);sx,sy=round(snapped[0]*w),round(snapped[1]*h)
                if len(cases)<1 and gradient[sy,sx]>50 and gradient[sy,sx]>gradient[y,x]*3:cases.append(dict(kind='contrast edge',pointer=[x,y],snapped=[sx,sy],gradient_before=gradient[y,x],gradient_after=gradient[sy,sx]))
                if len(cases)==1 and np.max(gradient[y-13:y+14,x-13:x+14])<3:
                    assert snapped==uv;cases.append(dict(kind='flat region',pointer=[x,y],snapped=snapped));break
            if len(cases)==2:break
        assert len(cases)==2,cases;report['magnetic']=cases
        (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('PASS',out,report,flush=True)
    finally:canvas.close();stage.close();vertices.release();target.release();ctx.release()

if __name__=='__main__':run()
