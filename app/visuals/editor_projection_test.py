"""Exact retained CPU reference versus renderer-owned GPU editor passes."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import sys,json,uuid,hashlib,importlib.util
import numpy as np,moderngl
from PySide6.QtWidgets import QApplication,QComboBox,QLabel
from PySide6.QtGui import QImage,QColor,QPainter
from PySide6.QtCore import QPointF
from composition import defaults,new_layer,transform
from native_raster import backend
from renderer import EditorSurface
from studio_composition import Canvas

def run(out,reference):
 out=Path(out);out.mkdir(parents=True,exist_ok=False)
 spec=importlib.util.spec_from_file_location('editor_cpu_reference',Path(reference)/'app/visuals/studio_composition.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 app=QApplication([]);rng=np.random.default_rng(22);arrays=[];images=[]
 for i in range(3):
  data=rng.integers(0,256,(257,389,4),dtype=np.uint8);data[:,:,:3]=np.minimum(data[:,:,:3],data[:,:,3,None]);arrays.append(data);images.append(QImage(data.tobytes(),389,257,QImage.Format_ARGB32_Premultiplied).copy())
 natives=[backend().storage().from_image(im) for im in images]
 scene=defaults();scene['canvas']=[389,257];scene['presentation']='Layers only';refs=[dict(id=uuid.uuid4().hex,kind='Images',name='exact',path='C:/ZeraWave/images n vids/Xeraphina.jpg') for _ in range(3)];scene['assets']=refs
 for i,ref in enumerate(refs):row=new_layer('Image',ref['id']);row.update(fit='Stretch',order=i);scene['layers'].append(row)
 def create(native):
  e=SimpleNamespace(config=deepcopy(scene),canvas_size=(389,257),images={ref['id']:natives[i] if native else images[i] for i,ref in enumerate(refs)},selected=None,editor_tools=QComboBox(),status=QLabel())
  e.metadata=lambda row:dict(width=389,height=257);e.selected_row=lambda:None;e.sync_tool_ui=lambda:None;e.cancel_preview=lambda:None
  c=(Canvas if native else old.Canvas)(e);e.canvas=c;c.resize(451,315);c.zoom=1.;c.pan=QPointF();c.show();return e,c
 left,cpu=create(False);right,canvas=create(True);ctx=moderngl.create_standalone_context(require=330);surface=EditorSurface(ctx);checks=[];hashes=[]
 def projection():
  v=canvas.view();w,h=canvas.canvas_size;return np.array([[v.m11(),0.,v.dx()],[0.,v.m22(),v.dy()],[0.,0.,1.]])@np.array([[w,0,w*.5],[0,h,h*.5],[0,0,1.]])
 def check(name):
  cpu.update();app.processEvents();texture=surface.layers.render_editor(canvas,(canvas.width(),canvas.height()),projection());data=texture.read(alignment=1)
  gpu=np.frombuffer(data,np.uint8).reshape(texture.height,texture.width,4)[::-1][:,:,[2,1,0,3]].copy();expected=np.frombuffer(cpu.composite_image.constBits(),np.uint8).reshape(texture.height,texture.width,4)
  if not np.array_equal(gpu,expected):
   np.savez(out/(name+'-difference.npz'),gpu=gpu,expected=expected,inputs=arrays)
   cpu.composite_image.save(str(out/(name+'-cpu.png')));QImage(gpu.tobytes(),texture.width,texture.height,QImage.Format_ARGB32_Premultiplied).save(str(out/(name+'-gpu.png')));raise AssertionError((name,int(np.count_nonzero(gpu!=expected)),int(np.max(abs(gpu.astype(int)-expected.astype(int)))),surface.layers.stats))
  hashes.append(dict(case=name,sha256=hashlib.sha256(gpu.tobytes()).hexdigest(),route=surface.layers.stats['route']));checks.append(name)
 try:
  for mode in ('Normal','Multiply','Screen','Add','Difference'):
   for strength in (0.,.37,.73,1.):
    for opacity in (0.,.57,1.):
     for e in (left,right):e.config['layers'][1].update(blend=mode,blend_strength=strength,opacity=opacity)
     check(mode+str(strength)+'-'+str(opacity))
  # Full-resolution soft pixel coverage is the same mask in exact Qt and GPU display.
  from pixel_selection import encode
  yy,xx=np.mgrid[:257,:389];coverage=np.where(((xx-140)**2+(yy-120)**2)<70**2,255,np.where((xx%37<12)&(yy%29<9),123,0)).astype(np.uint8);pixel_mask=encode(coverage)
  for mode in ('Normal','Multiply','Screen','Add','Difference'):
   for e in (left,right):e.config['layers'][1].update(masks=[pixel_mask],blend=mode,blend_strength=.73,opacity=.57)
   check('full-resolution-pixel-mask-'+mode)
  for e in (left,right):e.config['layers'][1]['transform']=transform(.07,-.05,.8,1.1,21)
  check('transformed-pixel-mask-exact-filter-reference')
  for e in (left,right):e.config=deepcopy(scene)
  # Masks and nested own-content/group isolation, then transformed exact fallback.
  mask=dict(enabled=True,mode='Keep',shape='Ellipse',points=[[.07,.08],[.91,.94]],handles=[])
  group=new_layer('Group');group.update(order=3,opacity=.64)
  for e in (left,right):e.config['layers'][1].update(blend='Add',blend_strength=.73,opacity=.57,masks=[mask]);e.config['layers'].append(deepcopy(group));e.config['layers'][1]['parent']=group['id'];e.config['layers'][2]['parent']=e.config['layers'][1]['id']
  check('nested-own-mask-isolation')
  part=images[1].copy(127,127,7,5);part.fill(QColor('#c2448099'));edited=natives[1].patch((127,127,7,5),part);expected=images[1].copy();p=QPainter(expected);p.setCompositionMode(QPainter.CompositionMode_Source);p.drawImage(127,127,part);p.end();left.images[refs[1]['id']]=expected;right.images[refs[1]['id']]=edited;check('changed-corner-masked-source')
  assert surface.layers.stats['damage_pixels']<451*315
  for i in range(40):
   x,y=(i*31)%382,(i*17)%250;part.fill(QColor.fromHsv(i*7%360,170,220));edited=edited.patch((x,y,7,5),part);p=QPainter(expected);p.setCompositionMode(QPainter.CompositionMode_Source);p.drawImage(x,y,part);p.end();right.images[refs[1]['id']]=edited;check('repeated-edit-'+str(i))
  assert surface.layers.stats['source_bytes']<4*389*257*4 and surface.layers.stats['readback_bytes']==0
  for e in (left,right):
   e.config=deepcopy(scene);e.config['layers'][1].update(blend='Add',blend_strength=.73,opacity=.57)
  left.images[refs[2]['id']]=images[1];right.images[refs[2]['id']]=natives[1]
  check('different-revisions-same-family')
  right.images[refs[0]['id']]=images[0];check('QImage-source-native-view')
  moved=images[0].copy();p=QPainter(moved);p.setCompositionMode(QPainter.CompositionMode_Source);p.fillRect(35,40,31,23,QColor('#b7406090'));p.end()
  left.images[refs[0]['id']]=moved;right.images[refs[0]['id']]=moved;check('changed-QImage-frame-same-geometry')
  assert surface.layers.stats['damage_pixels']==451*315
  left.images[refs[0]['id']]=images[0];right.images[refs[0]['id']]=natives[0]
  for e in (left,right):e.config['layers'][1]['transform']=transform(.1,-.05,.8,.9,23);e.config['layers'][-1]['masks']=[dict(mask,mode='Cut')]
  check('transformed-group-Qt-filter-reference')
  for c in (cpu,canvas):c.resize(403,287);c.zoom=.67;c.pan=QPointF(7,-9)
  check('resize-filtered-reference')
  assert not surface.layers.buffers
  # The editor clips at the canvas boundary even when a layer extends past it.
  from PySide6.QtCore import QRectF
  right.config['layers'][0]['transform']=transform(.4,.2,1.,1.,0.);left.config=deepcopy(right.config);check('layer-outside-canvas-reference')
  target=ctx.simple_framebuffer((403,287),components=4);target.clear(0.,0.,0.,0.);surface.draw(canvas,(403,287),projection(),target)
  data=target.read(components=4,alignment=1);gpu=np.frombuffer(data,np.uint8).reshape(287,403,4)[::-1][:,:,[2,1,0,3]].copy()
  clipped=QImage(403,287,QImage.Format_ARGB32_Premultiplied);clipped.fill(0);p=QPainter(clipped);p.setRenderHint(QPainter.Antialiasing);p.setClipRect(cpu.view().mapRect(QRectF(0,0,*cpu.canvas_size)));p.drawImage(0,0,cpu.composite_image);p.end()
  assert np.array_equal(gpu,np.frombuffer(clipped.constBits(),np.uint8).reshape(287,403,4)),'Canvas display clip changed pixels';target.release();checks.append('GPU-display-canvas-clip-exact')
  assert surface.layers.read_pixel(110,130)==cpu.composite_image.pixelColor(110,130);assert surface.layers.stats['readback_bytes']==4;checks.append('explicit-sampler-four-byte-readback')
  before=dict(surface.layers.stats);surface.layers.render_editor(canvas,(403,287),projection());assert surface.layers.stats['readback_bytes']==before['readback_bytes'] and surface.layers.stats['upload_bytes']==before['upload_bytes'];checks.append('cached-presentation-no-readback')
  # Fail staging and preserve the previous complete display.
  old_texture=surface.layers.result_texture;old_signature=surface.layers.signature;old_upload=surface.layers.upload_sources
  def fail(*args):raise MemoryError('injected editor staging failure')
  surface.layers.upload_sources=fail
  for e in (left,right):e.config=deepcopy(scene)
  for c in (cpu,canvas):c.resize(451,315);c.zoom=1.;c.pan=QPointF()
  assert surface.layers.render_editor(canvas,(451,315),projection()) is old_texture and surface.layers.signature==old_signature;checks.append('failed-upload-retains-complete-editor-display');surface.layers.upload_sources=old_upload
  report=dict(checks=checks,hashes=hashes,stats=surface.layers.stats,gpu=ctx.info['GL_RENDERER'],reference=str(reference));(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(checks=len(checks),gpu=report['gpu'],stats=report['stats'])))
 finally:surface.close();assert not surface.layers.textures and not surface.layers.buffers and not surface.layers.texture_frames and surface.layers.source_spare is None and surface.layers.display_spare is None;ctx.release();cpu.close();canvas.close();app.processEvents()
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
