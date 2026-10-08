"""Standalone GPU two-layer alpha/transform/lifecycle contracts, no audio."""
from pathlib import Path
import tempfile,time,threading,json,uuid,os
import numpy as np,moderngl
from PySide6.QtGui import QImage,QColor
from media_registry import defaults,inspect
from image_layers import ImageLayers,bounds
from composition import new_layer,transform,blend_rgba

def run():
    root=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(Path(__file__).resolve().parents[2]/'work/media-composition-20261007')));root.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='gpu-fixture-',dir=root) as temp:
        assets=[]
        for name,color in (('red.png',QColor(255,0,0,128)),('blue.png',QColor(0,0,255,255)),('green.png',QColor(0,255,0,255))):
            path=Path(temp)/name;image=QImage(4,4,QImage.Format_RGBA8888);image.fill(color);assert image.save(str(path))
            asset=inspect(str(path),threading.Event());asset['id']=uuid.uuid4().hex;assets.append(asset)
        ctx=moderngl.create_standalone_context(require=330);target=ctx.simple_framebuffer((32,24),components=4);target.use();ctx.viewport=(0,0,32,24)
        class Proxy:
            screen=target;fail=False;raw=ctx;uploads=0
            def __getattr__(self,name):return getattr(ctx,name)
            def texture(self,*args,**kwargs):
                if self.fail:raise MemoryError('Injected texture allocation failure')
                self.uploads+=1
                return ctx.texture(*args,**kwargs)
        proxy=Proxy();vertices=ctx.buffer(np.asarray([(-1,-1),(1,-1),(-1,1),(1,1)],dtype='f4').tobytes());stage=ImageLayers(proxy,vertices)
        config=defaults();config['assets']=assets[:2]
        config['layers']=[new_layer(asset=a['id']) for a in assets[:2]]
        for i,row in enumerate(config['layers']):row['order']=i
        for row,asset in zip(config['layers'],assets):row.update(asset=asset['id'],enabled=True,fit='Fill')
        config['layers'][1]['opacity']=.5
        revision=0
        def apply(value):
            nonlocal revision
            revision+=1;stage.request(value,revision,'fixture-session')
            end=time.perf_counter()+5.
            while stage.pending and time.perf_counter()<end:stage.poll();time.sleep(.005)
            assert not stage.pending,stage.snapshot()
        def frame():
            target.clear(.1,.2,.3,1.);stage.draw((32,24));assert ctx.viewport==(0,0,32,24)
            return np.frombuffer(target.read(components=4,alignment=1),np.uint8).reshape(24,32,4).copy()
        baseline=frame()
        try:
            apply(config);first=frame();pixel=first[12,16,:3]/255
            expected=(np.array([.1,.2,.3])*(1-128/255)+np.array([128/255,0,0]))*.5+np.array([0,0,.5])
            assert np.max(abs(pixel-expected))<2/255,(pixel,expected)
            config['layers'][0]['order']=1;config['layers'][1]['order']=0;apply(config);second=frame();assert not np.array_equal(first,second)
            assert stage.snapshot()['textures']==2 and stage.snapshot()['texture_bytes']==128
            # Isolated overlapping children receive group opacity exactly once.
            from copy import deepcopy
            original=deepcopy(config);group=new_layer('Group');group.update(opacity=.4,order=0)
            config['layers'].append(group)
            for row in config['layers'][:2]:row['parent']=group['id']
            apply(config);grouped=frame()[12,16]/255
            child=blend_rgba([0,0,.5,.5],[128/255,0,0,128/255]);want=blend_rgba([.1,.2,.3,1.],child*.4)
            assert np.max(abs(grouped-want))<3/255,(grouped,want)
            group['transform']=transform(.25,0.,.5);group['masks']=[dict(mode='Keep',enabled=True,points=[[0.,0.],[.5,0.],[.5,1.],[0.,1.]])]
            apply(config);masked=frame();assert masked[12,21,2]>baseline[12,21,2] and np.array_equal(masked[12,26],baseline[12,26])
            group['flip_x']=True;apply(config);flipped=frame();assert not np.array_equal(flipped,masked)
            assert stage.snapshot()['mask_texture_bytes']==32*24
            old_applied=stage.applied;group['masks'][0]['points'][1][0]=.6;proxy.fail=True;apply(config)
            assert stage.error and stage.applied==old_applied and np.array_equal(frame(),flipped);proxy.fail=False
            apply(config);assert not stage.error
            config=deepcopy(original)
            config['layers'][0]['masks']=[dict(mode='Cut',enabled=True,points=[[0.,0.],[1.,0.],[1.,1.],[0.,1.]])]
            apply(config);cut=frame();assert cut[12,16,0]<first[12,16,0]
            config=deepcopy(original)
            for mode in ('Multiply','Screen','Add','Difference'):
                config['layers'][0]['blend']=mode;apply(config);pixel=frame()[12,16]/255
                want=blend_rgba(blend_rgba([.1,.2,.3,1.],[0,0,.5,.5]),[128/255,0,0,128/255],mode)
                assert np.max(abs(pixel-want))<3/255,(mode,pixel,want)
            config=deepcopy(original);apply(config)
            # Artwork has a separately visible source and editable children.
            config['layers'][0].update(type='Artwork',source_visible=False)
            config['layers'][1]['parent']=config['layers'][0]['id'];apply(config);hidden_original=frame();assert hidden_original[12,16,0]<first[12,16,0]
            config['layers'][0]['source_visible']=True;apply(config);shown=frame();assert not np.array_equal(hidden_original,shown)
            config['canvas']=[24,32];apply(config);portrait=frame();assert np.array_equal(portrait[12,1],baseline[12,1]) and not np.array_equal(portrait[12,16],baseline[12,16])
            config=deepcopy(original);config['layers'][0].update(blend='Add',blend_strength=0.);apply(config);zero=frame();config['layers'][0]['blend']='Normal';apply(config);assert np.array_equal(zero,frame())
            config['layers'][0].update(blend='Add',blend_strength=1.);apply(config);full=frame();config['layers'][0]['blend_strength']=.5;apply(config);half=frame();assert np.max(abs(half.astype(float)-(zero.astype(float)+full.astype(float))/2))<3
            config=deepcopy(original);apply(config)
            uploads=proxy.uploads
            config['layers'][0].update(transform=transform(.25,.25,.5),fit='Fit');config['layers'][1]['enabled']=False;apply(config);transformed=frame()
            assert proxy.uploads==uploads # static transform changes do not decode/upload again
            assert np.array_equal(transformed[1,1,:3],baseline[1,1,:3])
            assert transformed[6,24,0]>100
            assert bounds((100,50),(10,20),dict(fit='Fit',scale=1.,x=0.,y=0.))==(37.5,0.,25.,50.)
            assert bounds((100,50),(10,20),dict(fit='Fill',scale=1.,x=0.,y=0.))==(0.,-75.,100.,200.)
            # A file/upload failure keeps the complete last working composition.
            working=frame();old_applied=stage.applied;config['assets']=[assets[2]];config['layers'][0]['asset']=assets[2]['id'];config['layers']=config['layers'][:1]
            proxy.fail=True;apply(config);assert stage.error and stage.applied==old_applied and np.array_equal(working,frame());proxy.fail=False
            apply(config);assert not stage.error and stage.applied==revision
            config['presentation']='Layers only';apply(config);only=frame();assert np.array_equal(only[1,1,:3],np.zeros(3,dtype='u1'))
            for row in config['layers']:row['enabled']=False
            config['presentation']='World + Layers';apply(config);blank=frame();assert np.array_equal(blank,baseline) and stage.snapshot()['textures']==0
            # Old commands cannot overwrite the latest texture-free state.
            stage.request(dict(config,presentation='Layers only'),revision-1,'fixture-session');assert stage.config['presentation']=='World + Layers'
            stage.invalidate('new-session',revision+1);assert stage.session=='new-session' and not stage.pending
            # An old, uninterruptible decode completion cannot cross session boundaries.
            import image_layers
            from unittest.mock import patch
            entered=threading.Event();release=threading.Event();original=image_layers.decode_image
            def delayed(path,cancel,**kwargs):
                value=original(path,threading.Event(),**kwargs);entered.set();assert release.wait(2.);return value
            config['assets']=[assets[0]];config['layers'][0].update(asset=assets[0]['id'],enabled=True)
            with patch.object(image_layers,'decode_image',side_effect=delayed):
                stage.request(config,revision+2,'new-session');assert entered.wait(2.)
                stage.invalidate('third-session',revision+3);release.set();time.sleep(.06);stage.poll()
                assert stage.snapshot()['textures']==0 and not stage.pending and stage.session=='third-session'
            try:stage.request(config,revision+20,'fixture-session')
            except ValueError:pass
            else:raise AssertionError('Old session command accepted after invalidation')
            stage.invalidate('old-session',revision);assert stage.session=='third-session'
            resized=ctx.simple_framebuffer((43,17),components=4);proxy.screen=resized;resized.use();ctx.viewport=(0,0,43,17);stage.draw((43,17));assert ctx.viewport==(0,0,43,17);resized.release();proxy.screen=target
            print('PASS: GPU',ctx.info['GL_RENDERER'],'premultiplied alpha/order, Fit/Fill/transforms, isolated groups/translated masks/flips, W3C blends, Layers only, disabled byte preservation, injected allocation failure retains composition, revisions/session invalidation, resize and release. No audio.')
            (root/'image-layer-gpu.json').write_text(json.dumps(dict(gpu=ctx.info['GL_RENDERER'],pixels=[32,24],dpr='offscreen physical pixels',evidence='GPU synthetic colors/contracts; no presentation/listening',texture_bytes_two_4x4=128),indent=2),encoding='utf-8')
        finally:
            stage.close();assert not stage.worker.is_alive() and not stage.textures;vertices.release();target.release();ctx.release()

if __name__=='__main__':run()
