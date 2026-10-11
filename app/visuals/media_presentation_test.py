"""Actual context-owned media upload failures, retries and source retirement."""
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
import sys,time,json,struct,uuid
import numpy as np,moderngl
from image_layers import ImageLayers
from composition import defaults,new_layer
from media_frames import HEADER

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    ctx=moderngl.create_standalone_context(require=330);target=ctx.simple_framebuffer((64,48),components=4);target.use();vertices=ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());fault=dict(create=False,write=False)
    class Texture:
        def __init__(self,raw):object.__setattr__(self,'raw',raw)
        def __getattr__(self,k):return getattr(self.raw,k)
        def __setattr__(self,k,v):setattr(self.raw,k,v)
        def write(self,*a,**k):
            if fault['write']:fault['write']=False;raise OSError('Controlled upload write failure')
            return self.raw.write(*a,**k)
    class Context:
        screen=target
        def __getattr__(self,k):return getattr(ctx,k)
        def texture(self,*a,**k):
            if fault['create']:fault['create']=False;raise OSError('Controlled texture allocation failure')
            return Texture(ctx.texture(*a,**k))
    stage=ImageLayers(Context(),vertices);width,height=32,24;capacity=width*height*4;shm=SharedMemory(create=True,size=HEADER+capacity*2);checks=[];report=dict(evidence=__doc__,gpu=ctx.info['GL_RENDERER'],checks=checks)
    try:
        asset=dict(id=uuid.uuid4().hex,kind='Video',name='Controlled native upload',status='Ready',path=str(out/'controlled-shared-frame.mp4'),metadata=dict(width=width,height=height));row=new_layer('Video',asset['id']);identity=row['id'];scene=defaults();scene.update(presentation='Layers only',canvas=[width,height],assets=[asset],layers=[row]);stage.request(scene,1,'b3-upload-test');until=time.perf_counter()+4
        while stage.pending and time.perf_counter()<until:stage.poll();time.sleep(.005)
        assert not stage.pending and not stage.error,stage.snapshot()
        def publish(sequence,rgba,generation=11):
            data=bytes(rgba)*width*height;slot=(sequence//2)%2;struct.pack_into('<Q',shm.buf,0,sequence-1);shm.buf[HEADER+slot*capacity:HEADER+slot*capacity+capacity]=data;struct.pack_into('<QIId',shm.buf,8,generation,width,height,sequence/24);struct.pack_into('<Q',shm.buf,0,sequence)
            desc=dict(name=shm.name,generation=generation,capacity=capacity,pixel_aspect=1.,pts=sequence/24);stage.runtime={identity:dict(frame=desc,state='paused',held=False,lag_seconds=0.,error='')};return data
        red=publish(2,(255,0,0,255));stage.draw((64,48));assert stage.animated[identity].read(alignment=1)==red
        green=publish(4,(0,255,0,255));fault['create']=True;stage.draw((64,48));assert stage.animated[identity].read(alignment=1)==red;assert stage.snapshot()['error'];assert shm.name not in stage.frames.last
        stage.draw((64,48));assert stage.animated[identity].read(alignment=1)==green;assert not stage.snapshot()['error'];assert stage.snapshot()['animated_spare_bytes']==capacity
        blue=publish(6,(0,0,255,255));fault['write']=True;stage.draw((64,48));assert stage.animated[identity].read(alignment=1)==green;assert stage.snapshot()['error'];assert shm.name not in stage.frames.last
        stage.draw((64,48));assert stage.animated[identity].read(alignment=1)==blue;assert not stage.snapshot()['error'];checks.append('Creation/write failures leave active native texture bytes unchanged; same immutable publication can retry; failures clear only after successful upload')
        stage.runtime[identity]['frame']['generation']=12;stage.draw((64,48));assert identity not in stage.animated
        white=publish(8,(255,255,255,255),12);stage.draw((64,48));assert stage.animated[identity].read(alignment=1)==white
        stage.runtime={identity:dict(frame=None,state='failed',error='Actual decoder error',held=False,lag_seconds=None)};stage.draw((64,48));assert not stage.animated and not stage.animated_spares and not stage.frames.maps;assert 'Actual decoder error' in stage.snapshot()['error'];checks.append('New source generation cannot display old texture; missing current frame drops active/spare/reader handles and exposes decoder failure')
        report['resources']=stage.snapshot();report['result']='PASS'
    finally:stage.close();shm.close();shm.unlink();vertices.release();target.release();ctx.release();(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS',out,checks)

if __name__=='__main__':run()
