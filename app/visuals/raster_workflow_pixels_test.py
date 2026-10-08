"""Source-bound offscreen Qt/actual GPU complementary-cut parity and cost."""
import os,sys,time,json,threading,uuid
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import numpy as np,moderngl
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor,QPainter
from composition import *
from artwork import masked
from studio_composition import Canvas
from media_registry import inspect
from image_layers import ImageLayers

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);images={};assets=[]
    for name in ('back','source'):
        image=QImage(320,180,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(25,45,65) if name=='back' else QColor(70,160,200,140))
        if name=='source':
            p=QPainter(image)
            for x in range(320):p.fillRect(x,0,1,180,QColor(x%256,100,220,80+x//2))
            p.end()
        path=out/(name+'.png');image.save(str(path));ref=inspect(str(path),threading.Event());ref['id']=uuid.uuid4().hex;assets.append(ref);images[ref['id']]=image
    scene=defaults();scene.update(assets=assets,canvas=[320,180],presentation='Layers only');back=new_layer(asset=assets[0]['id']);back['fit']='Stretch';parent=new_layer(asset=assets[1]['id']);parent['order']=1;scene['layers']=[back,parent]
    editor=SimpleNamespace(config=scene,canvas_size=(320,180),images=images,selected_row=lambda:None,metadata=lambda r:dict(width=320,height=180),cancel_preview=lambda:None,sync_tool_ui=lambda:None,pending_paint=None)
    canvas=Canvas(editor);canvas.resize(320,180);canvas.zoom=1;canvas.show();app.processEvents()
    ctx=moderngl.create_standalone_context(require=330);target=ctx.simple_framebuffer((320,180),components=4);target.use();ctx.viewport=(0,0,320,180)
    class Proxy:
        screen=target
        def __getattr__(self,k):return getattr(ctx,k)
    vertices=ctx.buffer(np.asarray([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());stage=ImageLayers(Proxy(),vertices);revision=0;results=[]
    def gpu(config,size=(320,180)):
        nonlocal revision
        revision+=1;stage.request(config,revision,'cut-parity');deadline=time.monotonic()+10
        while stage.pending and time.monotonic()<deadline:stage.poll();time.sleep(.005)
        assert not stage.pending and not stage.error,stage.snapshot();target.use();target.clear(0,0,0,0);stage.draw(size);assert not stage.error,stage.snapshot();return np.frombuffer(target.read(components=4,alignment=1),np.uint8).reshape(size[1],size[0],4)[::-1].copy()
    def qt(config):
        editor.config=config;canvas.update();app.processEvents();image=canvas.grab().toImage().convertToFormat(QImage.Format_RGBA8888);return np.frombuffer(image.constBits(),np.uint8).reshape(image.height(),image.bytesPerLine())[:,:image.width()*4].reshape(image.height(),image.width(),4).copy()
    def split(config,identity,operation):
        p=lookup(config)[identity];own=masked(images[p['asset']],p['masks']);piece=masked(own,[operation]);path=out/(uuid.uuid4().hex+'.png');piece.save(str(path));ref=inspect(str(path),threading.Event());ref['id']=uuid.uuid4().hex;images[ref['id']]=piece;config['assets'].append(ref);child=new_layer(asset=ref['id']);child.update(piece_geometry(p));child.update(parent=p['id'],order=0,cut_alignment=dict(parent=p['id'],geometry=piece_geometry(p),asset=ref['id']));p['masks'].append(dict(operation,mode='Cut'));config['layers'].append(child);return child
    try:
        for shape in ('Rectangle','Ellipse','Path','Curve'):
            for mode in BLENDS:
                config=deepcopy(scene);p=config['layers'][1];p.update(transform=transform(.035,-.035,.85,.75,23),flip_x=True,crop=[.08,.12,.93,.88],opacity=.57,blend=mode)
                a=gpu(config);qa=qt(config);op=dict(mode='Keep',enabled=True,shape=shape,points=[[.23,.2],[.77,.2],[.77,.78],[.23,.78]],handles=[])

                if shape=='Curve':op['handles']=[[[.16,.28],[.34,.1]],[[.67,.1],[.86,.32]],[[.86,.68],[.66,.87]],[[.32,.87],[.14,.65]]]
                c=split(config,p['id'],op);b=gpu(config);qb=qt(config);delta=abs(a.astype(int)-b.astype(int));qdelta=abs(qa.astype(int)-qb.astype(int));parity=abs(qb.astype(int)-b.astype(int));inner=np.s_[2:-2,2:-2,:3];baseline_parity=abs(qa.astype(int)-a.astype(int))
                record=dict(shape=shape,mode=mode,baseline_parity_max=int(baseline_parity[inner].max()),baseline_parity_mean=float(baseline_parity[inner].mean()),gpu_cut_max=int(delta.max()),gpu_cut_mean=float(delta.mean()),qt_cut_max=int(qdelta.max()),qt_cut_mean=float(qdelta.mean()),parity_max=int(parity[inner].max()),parity_mean=float(parity[inner].mean()));results.append(record)

                loc=np.unravel_index(delta.argmax(),delta.shape);record['max_location']=list(map(int,loc));record['before_pixel']=a[loc[:2]].tolist();record['after_pixel']=b[loc[:2]].tolist()
                assert delta.max()<=3 and delta.mean()<.12,record
                assert qdelta.max()<=3 and qdelta.mean()<.12,record
                assert parity[inner].mean()<.6,record
                assert abs(float(parity[inner].mean()-baseline_parity[inner].mean()))<.05,record
        # Nested split and own/branch visibility must reach actual output.
        config=deepcopy(scene);op=dict(mode='Keep',enabled=True,shape='Rectangle',points=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]],handles=[]);a=gpu(config);c=split(config,parent['id'],op);d=split(config,c['id'],dict(op,points=[[.3,.3],[.6,.3],[.6,.6],[.3,.6]]));b=gpu(config);assert abs(a.astype(int)-b.astype(int)).max()<=3
        lookup(config)[parent['id']]['source_visible']=False;own_hidden=gpu(config);lookup(config)[parent['id']]['enabled']=False;branch_hidden=gpu(config);assert not np.array_equal(own_hidden,branch_hidden)
        costs=[]
        target.release();target=ctx.simple_framebuffer((1280,720),components=4);Proxy.screen=target;stage.ctx.screen=target
        for depth in (0,3,6):
            config=deepcopy(scene);config['canvas']=[1280,720];p=config['layers'][1];p['fit']='Stretch'
            for _ in range(depth):p=split(config,p['id'],op)
            gpu(config,(1280,720));samples=[]
            for _ in range(12):
                target.use();began=time.perf_counter();stage.draw((1280,720));ctx.finish();samples.append((time.perf_counter()-began)*1000)
            costs.append(dict(canvas=[1280,720],depth=depth,layers=len(config['layers']),draw_finish_median_ms=float(np.median(samples)),draw_finish_max_ms=max(samples),resources=stage.snapshot()))
        report=dict(evidence=__doc__,gpu=ctx.info['GL_RENDERER'],cases=results,costs=costs);(out/'RESULT.json').write_text(json.dumps(report,indent=2));print('PASS',out,results,costs,flush=True)
    except Exception:
        import traceback
        (out/'FAILURE.json').write_text(json.dumps(dict(cases=results,error=traceback.format_exc()),indent=2));raise
    finally:canvas.close();stage.close();vertices.release();target.release();ctx.release()
if __name__=='__main__':run()
