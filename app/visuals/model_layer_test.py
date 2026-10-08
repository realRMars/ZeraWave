"""Original generated glTF/GLB, real mesh rendering on the existing GL context."""
from pathlib import Path
import json,struct,threading,uuid,time
import numpy as np,moderngl
from model_layer import load_model
from media_registry import inspect
from composition import defaults,new_layer
from image_layers import ImageLayers

def fixture(path):
    vertices=np.array([[-.7,-.7,0],[.7,-.7,0],[0,.7,0]],'<f4');raw=vertices.tobytes()
    doc=dict(asset={'version':'2.0','generator':'Original ZeraWave technical fixture'},buffers=[{'byteLength':len(raw)}],bufferViews=[{'buffer':0,'byteLength':len(raw)}],accessors=[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'}],materials=[{'pbrMetallicRoughness':{'baseColorFactor':[.2,.7,.3,1.],'metallicFactor':0.,'roughnessFactor':.8},'extensions':{'KHR_materials_unlit':{}}}],meshes=[{'primitives':[{'attributes':{'POSITION':0},'material':0}]}],nodes=[{'mesh':0}],scenes=[{'nodes':[0]}],scene=0)
    payload=json.dumps(doc,separators=(',',':')).encode();payload+=b' '*(len(payload)*-1%4);binary=raw+b'\0'*(len(raw)*-1%4);size=12+8+len(payload)+8+len(binary)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,size)+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary)
    return doc

def run():
    root=Path(__file__).resolve().parents[2];out=root/'work/media-composition-20261007';path=out/'original-triangle.glb';fixture(path);model=load_model(path);assert model['metadata']['vertices']==3
    asset=inspect(str(path),threading.Event());asset['id']=uuid.uuid4().hex;scene=defaults();scene['assets']=[asset];row=new_layer('Model',asset['id']);scene['layers']=[row]
    ctx=moderngl.create_standalone_context(require=330);target=ctx.simple_framebuffer((192,128),components=4);target.use();ctx.viewport=(0,0,192,128)
    class Proxy:
        raw=ctx;screen=target
        def __getattr__(self,n):return getattr(ctx,n)
    vertices=ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());stage=ImageLayers(Proxy(),vertices)
    def apply(revision):
        stage.request(scene,revision,'model-fixture');end=time.perf_counter()+4
        while stage.pending and time.perf_counter()<end:stage.poll();time.sleep(.005)
        assert not stage.error,stage.snapshot();target.clear(.1,.1,.1,1);stage.draw((192,128));assert not stage.error,stage.snapshot();assert ctx.viewport==(0,0,192,128)
        return np.frombuffer(target.read(components=4),np.uint8).reshape(128,192,4).copy()
    try:
        a=apply(1);assert a[64,96,1]>a[64,96,0]+30
        row['model']['yaw']=60.;b=apply(2);assert not np.array_equal(a,b)
        bad=out/'animated-model.gltf';doc=fixture(out/'unused-static.glb');doc['animations']=[{}];bad.write_text(json.dumps(doc))
        try:load_model(bad);raise AssertionError('Rig/animation silently accepted')
        except ValueError as exc:assert 'static' in str(exc)
        (out/'model-gpu.json').write_text(json.dumps(dict(gpu=ctx.info['GL_RENDERER'],source='Original generated unlit triangle GLB; actual mesh and rotation',metadata=model['metadata'],bounds='200k vertices / 64 primitives / 64 MiB dependencies / 32 MiB decoded textures'),indent=2));print('Static GLB validation, actual existing-context mesh/material/orientation rendering, unsupported animation rejection and cleanup passed')
    finally:stage.close();vertices.release();target.release();ctx.release()

if __name__=='__main__':run()
