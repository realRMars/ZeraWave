"""Timeline adapter for the existing renderer-owned ImageLayers compositor.

The context owner calls render at authored dimensions, then presents/readbacks
the same output. Prepared snapshots are immutable; this owns no codec or clock.
"""
from copy import deepcopy
import time
from composition import defaults,new_layer,transform,validate_scene
from project_text import TextSurface

class TargetContext:
 def __init__(self,context):self.raw=context;self.screen=None
 def __getattr__(self,name):return getattr(self.raw,name)

def scene_for(result):
 plan=result['plan'];settings=plan['settings'];w,h=settings['width'],settings['height'];scene=defaults();scene['canvas']=[w,h];brightness={}
 for order,item in enumerate(plan['visual']):
  c=item['clip'];image=result['images'][c['id']];layout=c['layout'];x,y,bw,bh=layout['bounds'];crop=[0.,0.,1.,1.];iw=image['width']*image['pixel_aspect'];ih=image['height']
  if layout['fit']=='Fit':
   scale=min(bw*w/iw,bh*h/ih);fw,fh=iw*scale/w,ih*scale/h;x+=(bw-fw)/2;y+=(bh-fh)/2;bw,bh=fw,fh
  elif layout['fit']=='Fill':
   scale=max(bw*w/iw,bh*h/ih);cw,ch=bw*w/(iw*scale),bh*h/(ih*scale);crop=[(1-cw)/2,(1-ch)/2,(1+cw)/2,(1+ch)/2]
  masks=[dict(m,mode='Cut' if m['mode']=='Remove' else 'Keep') for m in layout['masks']]
  row=new_layer('Image',c['id'],(c['name'].strip() or 'Clip')[:128]);row.update(id=c['id'],order=order,fit='Stretch',transform=transform(x=x+bw/2-.5,y=y+bh/2-.5,scale=bw,scale_y=bh,rotation=layout['rotation'],aspect=w/h),opacity=layout['opacity'],crop=crop,masks=masks,blend=layout['blend']);scene['layers'].append(row);brightness[c['id']]=layout['brightness']
  # These are immutable evaluated source instances, consumed directly below;
  # this transient renderer adapter never owns/deletes or saves their files.
  scene['assets'].append(dict(id=c['id'],kind='Images',path=item['asset']['location']['path'],name=row['name'],managed=True,internal=True,provenance='Timeline evaluated immutable source instance; no file ownership'))
 return validate_scene(scene),brightness

class ProjectSurface:
 def __init__(self,context):
  from renderer import EditorSurface
  from image_layers import ImageLayers
  self.text=TextSurface();self.context=context;self.adapter=TargetContext(context);self.host=EditorSurface(self.adapter,layer_type=ImageLayers);self.host._draw=self._draw;self.layers=self.host.layers;self.fbo=None;self.texture=None;self.size=None;self.frames={};self.closed=False;self.stats={};self.error=''
 def render(self,result,target):
  if result.get('error'):raise ValueError(result['error'])
  size=(result['plan']['settings']['width'],result['plan']['settings']['height'])
  return self.host.draw(result,size,None,target)
 def _draw(self,result,size,projection,target):
  if result is None:return self.present(target)
  import moderngl
  from image_layers import asset_key
  began=time.perf_counter();result=self.text.augment(result);layers=self.layers;plan=result['plan'];signature=(plan['project'],plan['epoch'],plan['revision'],size,tuple((r['clip']['id'],result['images'][r['clip']['id']]['width'],result['images'][r['clip']['id']]['height'],result['images'][r['clip']['id']]['pixel_aspect']) for r in plan['visual']))
  if signature!=getattr(self,'scene_signature',None):self.scene,self.brightness=scene_for(result);self.scene_signature=signature
  scene,brightness=self.scene,self.brightness
  if size!=self.size:
   texture=self.context.texture(size,4);texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
   try:fbo=self.context.framebuffer(color_attachments=(texture,))
   except Exception:texture.release();raise
   if self.fbo:self.fbo.release();self.texture.release()
   self.texture,self.fbo,self.size=texture,fbo,size
  # Fully stage replacements before committing; keep only metadata identities,
  # never a hidden CPU snapshot that prevents lease/resource retirement.
  selected={};uploads={};fingerprints={};existing=layers.textures;candidate_cost=0
  for item in result['plan']['visual']:
   c=item['clip'];frame=result['images'][c['id']];a=item['asset'];fingerprint=(a['sha256'],a['location']['path'],frame.get('pts'),frame['width'],frame['height']);fingerprints[c['id']]=fingerprint
   key=(c['id'],a['location']['path'],a['sha256'],frame.get('pts'));asset=dict(id=c['id'],kind='Images',path=a['location']['path'],status='Ready',metadata=dict(width=frame['width'],height=frame['height'],bytes=a['sha256'],mtime_ns=frame.get('pts')));selected[key]=asset
   if key not in existing:uploads[key]=(asset['metadata'],frame['data']);candidate_cost+=len(frame['data'])
  resident=sum(t.width*t.height*4 for t in existing.values())
  if resident+candidate_cost>256*1024*1024:raise MemoryError('Native texture replacement exceeds 256 MiB; requested frame was not presented.')
  layers.target_size=size;layers.desired=(scene,selected);layers.error='';layers.brightness=brightness;layers.session=plan['epoch'];layers.revision=plan['revision']
  layers.commit(scene,selected,uploads)
  if layers.error:raise ValueError(layers.error)
  self.frames=fingerprints;self.adapter.screen=self.fbo
  color=result['plan']['settings']['background'];rgb=tuple(int(color[i:i+2],16)/255 for i in (1,3,5));self.fbo.clear(*rgb,1.)
  layers.draw(size)
  if layers.error:raise ValueError(layers.error)
  if target is not None:self.present(target)
  self.stats=dict(layers.snapshot(),**self.text.stats,render_ms=(time.perf_counter()-began)*1000,frame=result['plan']['frame'],revision=result['plan']['revision'],native_size=list(size));return self.texture
 def read(self):return self.fbo.read(components=4,alignment=1)
 def present(self,target):
  import moderngl
  from image_layers import FULL_VERTEX
  if not hasattr(self,'present_program'):
   self.present_program=self.context.program(vertex_shader=FULL_VERTEX,fragment_shader='#version 330\nuniform sampler2D image;in vec2 uv;out vec4 color;void main(){color=texture(image,uv);}')
   self.present_vao=self.context.simple_vertex_array(self.present_program,self.host.vertices,'in_position')
  tw,th=target.size;w,h=self.size;scale=min(tw/w,th/h);vw,vh=max(1,round(w*scale)),max(1,round(h*scale));old=self.context.viewport
  try:
   target.clear(.035,.05,.06,1.);self.texture.use(0);self.present_program['image'].value=0
   with self.context.scope(framebuffer=target,enable_only=0):
    self.context.viewport=((tw-vw)//2,(th-vh)//2,vw,vh);self.present_vao.render(moderngl.TRIANGLE_STRIP)
  finally:self.context.viewport=old
 def close(self):
  if self.closed:return
  self.closed=True
  if hasattr(self,'present_program'):self.present_vao.release();self.present_program.release()
  self.text.close();self.host.close()
  if self.layers.worker.is_alive():raise RuntimeError('Project compositor preparation worker has not exited.')
  if self.fbo:self.fbo.release();self.texture.release();self.fbo=self.texture=None
  self.frames.clear();self.stats=dict(self.text.stats,closed=True,textures=0,texture_bytes=0,composition_target_bytes=0)

class ReferenceSurface:
 """Supported Qt CPU projection, adapting the same saved spatial recipes."""
 def __init__(self):
  from cpu_projection import Projection
  self.projection=Projection();self.text=TextSurface();self.image=None;self.stats={}
 def render(self,result):
  import numpy as np
  from types import SimpleNamespace
  from PySide6.QtGui import QImage,QPainter,QColor
  from composition import asset_matrix
  from studio_composition import masked_image
  if result.get('error'):raise ValueError(result['error'])
  result=self.text.augment(result);scene,brightness=scene_for(result);w,h=scene['canvas'];images={}
  for key,frame in result['images'].items():
   pixels=np.frombuffer(frame['data'],np.uint8).reshape(frame['height'],frame['width'],4)[::-1].copy();factor=brightness[key]
   if factor!=1.:pixels[:,:,:3]=np.minimum(pixels[:,:,:3].astype(np.float32)*factor,pixels[:,:,3:4]).astype(np.uint8)
   images[key]=QImage(pixels.tobytes(),frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).convertToFormat(QImage.Format_ARGB32_Premultiplied)
  background=new_layer('Image','project-background');background.update(id='project-background',order=-1,fit='Stretch');scene['layers'].insert(0,background);base=QImage(1,1,QImage.Format_ARGB32_Premultiplied);base.fill(QColor(result['plan']['settings']['background']));images[background['id']]=base
  canvas=SimpleNamespace(editor=SimpleNamespace(config=scene,images=images,pending_paint=None),canvas_size=(w,h),stroke=None,mask_image=masked_image,source_matrix=lambda row:asset_matrix(scene,row,(w,h),(images[row['id']].width(),images[row['id']].height())))
  # Canvas coordinates are normalized about the centre, positive y down.
  projection=np.array([[w,0,w/2],[0,h,h/2],[0,0,1.]])
  began=time.perf_counter();art=self.projection.render(canvas,w,h,projection);image=QImage(w,h,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(result['plan']['settings']['background']));p=QPainter(image);p.drawImage(0,0,art);p.end();self.image=image;self.stats=dict(self.projection.stats,**self.text.stats,render_ms=(time.perf_counter()-began)*1000,frame=result['plan']['frame'],revision=result['plan']['revision'],native_size=[w,h],backend='Qt CPU reference');return image
 def close(self):
  self.text.close();self.image=None;self.projection.cache.clear();self.projection.latest.clear();self.projection.scratch.clear();self.projection.output=None;self.projection.bytes=0;self.projection.scratch_bytes=0;self.projection.stats.update(cache_bytes=0,scratch_bytes=0,closed=True);self.stats=dict(self.projection.stats,**self.text.stats)
