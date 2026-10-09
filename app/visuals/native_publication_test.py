"""Existing renderer tile upload/reuse, pinned encoding and native history churn."""
from pathlib import Path
import sys,os,json,gc,uuid,threading
from copy import deepcopy
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from PySide6.QtCore import QBuffer,QIODevice
from native_raster import backend
from raster_resources import snapshot,release,Resources,read
from composition import History,defaults,new_layer
from image_layers import ImageLayers
import moderngl

def run(out):
    app=QApplication.instance() or QApplication([]);out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=[];source=QImage(513,387,QImage.Format_ARGB32_Premultiplied);source.fill(QColor(33,115,187,183));a=backend().storage().from_image(source);d1,l1=snapshot(a);part=QImage(3,3,QImage.Format_ARGB32_Premultiplied);part.fill(QColor('magenta'));b=a.patch((127,258,3,3),part);d2,l2=snapshot(b)
    def encode(version):
        buf=QBuffer();buf.open(QIODevice.WriteOnly);assert version.save(buf,'PNG');return bytes(buf.data())
    expected={a.handle:encode(a),b.handle:encode(b)};fail=[]
    def save(version):
        for _ in range(16):
            if encode(version)!=expected[version.handle]:fail.append(version.handle)
    threads=[threading.Thread(target=save,args=(v,)) for v in (a,b)]
    for t in threads:t.start()
    for t in threads:t.join()
    assert not fail;checks.append('Concurrent older/newer family PNG encoding stays revision-pinned')
    ctx=moderngl.create_standalone_context(require=330);device=ctx.info.get('GL_RENDERER');vertices=ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],dtype='f4').tobytes());gpu=ImageLayers(ctx,vertices);leases=[l1,l2]
    def scene(desc):
        identity=uuid.uuid4().hex;asset=dict(id=identity,kind='Images',name='fixture',path=str(out/(identity+'.png')),managed=True,provenance='fixture',runtime=desc,status='Ready',metadata=dict(width=desc['width'],height=desc['height'],bytes=desc['bytes'],mtime_ns=0));row=new_layer('Image',identity);return dict(defaults(),assets=[asset],layers=[row]),asset
    try:
        s1,r1=scene(d1);s2,r2=scene(d2);gpu.request(s1,1,'test');assert not gpu.error,gpu.error;gpu.request(s2,2,'test');assert not gpu.error,gpu.error
        actual=next(iter(gpu.textures.values())).read(alignment=1);assert actual==read(d2)[1];upload=dict(gpu.tile_upload);assert 0<upload['upload_bytes']<d2['bytes'] and upload['reused_tiles']>0;checks.append('Existing GPU framebuffer clone + changed tile upload exact; unchanged tile reuse')
        prior=gpu.applied;texture=next(iter(gpu.textures.values()));bad=deepcopy(d2);bad['tiles'][0]['name']='zw_raster_missing_fixture';s3,_=scene(bad);gpu.request(s3,3,'test');assert gpu.error and gpu.applied==prior and next(iter(gpu.textures.values())) is texture;checks.append('Failed tile upload retains applied GPU resources and revision')
        gpu.invalidate('next',4);gpu.close();vertices.release();ctx.release()
    finally:
        if not gpu.closed:gpu.close();vertices.release();ctx.release()
    resources=Resources(out/'history-artwork');history=History();history.resource_cost=resources.history_bytes;scene0=defaults();row=new_layer('Image');scene0['layers']=[row];current=a
    try:
        for i in range(76):
            part.fill(QColor.fromHsv(i*4%360,180,200));current=current.patch((250,250,3,3),part);desc,lease=snapshot(current);leases.append(lease);s,asset=scene(desc);resources.admit([asset]);before=deepcopy(scene0);row=scene0['layers'][0];row['asset']=asset['id'];scene0['assets']=[{k:v for k,v in asset.items() if k in ('id','kind','name','path','managed','provenance')}];history.resource_sizes[asset['id']]=513*387*4;history.record(before,scene0,'stroke',row['id'],row['id'],'drawing',row['id']);refs={a['id'] for item in history.undo+history.redo for version in (item['before'],item['after']) for a in version['assets']}|{asset['id']};resources.retain(refs)
            release(leases.pop());assert len(history.undo)<=64
        assert history.raster_bytes<64*513*387*4 and history.raster_bytes<8*1024*1024;checks.append('76 native versions/history churn: shared tiles charged once, 64-command trimming and lease retirement')
        before=deepcopy(scene0);scene0['layers'][0]['name']='management later';history.record(before,scene0,'rename');restored=history.step(False,scene0,'drawing',row['id']);assert restored['layers'][0]['name']=='management later';history.record(restored,scene0,'branch',scope='drawing',target=row['id']);assert history.item(True,'drawing',row['id']) is None;checks.append('Mixed management/drawing recovery and drawing branch clear independently')
        state=resources.state();report=dict(checks=checks,upload=upload,history=history.snapshot(),resource_bytes=state['bytes'],native=state['native'],gpu=device)
        (out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    finally:
        resources.close()
        for lease in leases:release(lease)
if __name__=='__main__':run(sys.argv[1])
