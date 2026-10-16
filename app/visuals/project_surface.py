"""Timeline adapter for the existing renderer-owned ImageLayers compositor.

The context owner calls render at authored dimensions, then presents/readbacks
the same output. Prepared snapshots are immutable; this owns no codec or clock.
"""
from copy import deepcopy
import time,json
from composition import defaults,new_layer,transform,validate_scene
from project_text import TextSurface

class TargetContext:
 def __init__(self,context):self.raw=context;self.screen=None
 def __getattr__(self,name):return getattr(self.raw,name)

def scene_for(result):
 plan=result['plan'];settings=plan['settings'];w,h=settings['width'],settings['height'];scene=defaults();scene['canvas']=[w,h];brightness={};active={key:t for t in plan.get('transitions',[]) for key in (t['left'],t['right'])};groups={};root_order=0
 for order,item in enumerate(plan['visual']):
  c=item['clip'];image=result['images'][c['id']];layout=c['layout'];x,y,bw,bh=layout['bounds'];crop=list(layout.get('crop',[0.,0.,1.,1.]));base_crop=list(crop);iw=image['width']*image['pixel_aspect']*(crop[2]-crop[0]);ih=image['height']*(crop[3]-crop[1])
  if layout['fit']=='Fit':
   scale=min(bw*w/iw,bh*h/ih);fw,fh=iw*scale/w,ih*scale/h;x+=(bw-fw)/2;y+=(bh-fh)/2;bw,bh=fw,fh
  elif layout['fit']=='Fill':
   scale=max(bw*w/iw,bh*h/ih);cw,ch=bw*w/(iw*scale),bh*h/(ih*scale);crop=[base_crop[0]+(1-cw)/2*(base_crop[2]-base_crop[0]),base_crop[1]+(1-ch)/2*(base_crop[3]-base_crop[1]),base_crop[0]+(1+cw)/2*(base_crop[2]-base_crop[0]),base_crop[1]+(1+ch)/2*(base_crop[3]-base_crop[1])]
  masks=[dict(m,mode='Cut' if m['mode']=='Remove' else 'Keep') for m in layout['masks']]
  row=new_layer('Image',c['id'],(c['name'].strip() or 'Clip')[:128]);row.update(id=c['id'],order=order,fit='Stretch',transform=transform(x=x+bw/2-.5,y=y+bh/2-.5,scale=bw,scale_y=bh,rotation=layout['rotation'],aspect=w/h),opacity=layout['opacity'],crop=crop,masks=masks,blend=layout['blend']);row['_project_effects']=deepcopy(layout.get('effects',[]));transition=active.get(c['id'])
  if transition:
   key='project-dissolve-'+transition['id']
   if key not in groups:
    group=new_layer('Group',name='Dissolve');group.update(id=key,order=root_order);root_order+=1;scene['layers'].append(group);groups[key]=group;brightness[key]=1.
   phase=(plan['frame']-transition['start'])/transition['duration'];row.update(parent=key,order=0 if c['id']==transition['left'] else 1,_project_mix_sum=True);row['opacity']*=1.-phase if c['id']==transition['left'] else phase
  else:row['order']=root_order;root_order+=1
  scene['layers'].append(row);brightness[c['id']]=layout['brightness']
  # These are immutable evaluated source instances, consumed directly below;
  # this transient renderer adapter never owns/deletes or saves their files.
  scene['assets'].append(dict(id=c['id'],kind='Images',path=item['asset']['location']['path'],name=row['name'],managed=True,internal=True,provenance='Timeline evaluated immutable source instance; no file ownership'))
 # Saved composition validation intentionally strips runtime fields. Add only
 # these project-owner-derived render instructions AFTER that boundary; never
 # fabricate cut_alignment or persist renderer handles into authored sessions.
 runtime={r['id']:{key:deepcopy(value) for key,value in r.items() if key.startswith('_project_')} for r in scene['layers']}
 scene=validate_scene(scene)
 for row in scene['layers']:row.update(runtime.get(row['id'],{}))
 return scene,brightness

class ProjectSurface:
 def __init__(self,context):
  from renderer import EditorSurface
  from image_layers import ImageLayers
  self.text=TextSurface();self.context=context;self.adapter=TargetContext(context);self.host=EditorSurface(self.adapter,layer_type=ImageLayers);self.host._draw=self._draw;self.layers=self.host.layers;self.fbo=None;self.texture=None;self.size=None;self.frames={};self.last_plan=None;self.source_metadata={};self.closed=False;self.stats={};self.error=''
 def render(self,result,target):
  if result.get('error'):raise ValueError(result['error'])
  size=(result['plan']['settings']['width'],result['plan']['settings']['height'])
  return self.host.draw(result,size,None,target)
 def _draw(self,result,size,projection,target):
  if result is None:return self.present(target)
  import moderngl
  from image_layers import asset_key
  began=time.perf_counter();original=result;result=self.text.augment(result);layers=self.layers;plan=result['plan'];signature=(plan['project'],plan['epoch'],plan['revision'],size,tuple((r['clip']['id'],result['images'][r['clip']['id']]['width'],result['images'][r['clip']['id']]['height'],result['images'][r['clip']['id']]['pixel_aspect'],json.dumps(r['clip']['layout'],sort_keys=True)) for r in plan['visual']),json.dumps(plan.get('transitions',[]),sort_keys=True),plan['frame'] if plan.get('transitions') else None)
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
  if not original.get('_transient'):
   self.last_plan=deepcopy(original['plan']);self.source_metadata={key:{k:v for k,v in frame.items() if k!='data'} for key,frame in original['images'].items()}
  self.stats=dict(layers.snapshot(),**self.text.stats,render_ms=(time.perf_counter()-began)*1000,frame=result['plan']['frame'],revision=result['plan']['revision'],native_size=list(size),unaccepted_transform_preview=bool(original.get('_transient')));return self.texture
 def recompose(self,change,target=None):
  if self.last_plan is None:return
  plan=deepcopy(self.last_plan)
  if change:
   key,layout=change
   for item in plan['visual']:
    if item['clip']['id']==key:item['clip']['layout']=deepcopy(layout)
   for item in plan['text']:
    if item['recipe']['id']==key:item['recipe']['style'].update({field:deepcopy(layout[field]) for field in ('bounds','rotation','opacity')})
  return self._draw(dict(plan=plan,images=self.source_metadata,error='',_transient=True),(plan['settings']['width'],plan['settings']['height']),None,target)
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
  self.frames.clear();self.last_plan=None;self.source_metadata.clear();self.stats=dict(self.text.stats,closed=True,textures=0,texture_bytes=0,composition_target_bytes=0)

class ReferenceSurface:
 """Same CPU projection, with explicitly counted copied materialized planes.

 Current QImages own their bytes after the Media reader is released. They enable
 transform-only recomposition without retaining borrowed/native snapshots. Old
 copies retire before replacement materialization; close releases all of them.
 """
 def __init__(self):
  from cpu_projection import Projection
  self.projection=Projection();self.text=TextSurface();self.image=None;self.stats={};self.sources={};self.source_metadata={};self.last_plan=None;self.raw_plan=None;self.materialized_bytes=0
 def render(self,result):
  import numpy as np
  from PySide6.QtGui import QImage
  if result.get('error'):raise ValueError(result['error'])
  raw_plan=deepcopy(result['plan']);result=self.text.augment(result);scene,brightness=scene_for(result);images={};self.sources.clear();self.source_metadata.clear();self.last_plan=self.raw_plan=None;self.materialized_bytes=0
  for key,frame in result['images'].items():
   pixels=np.frombuffer(frame['data'],np.uint8).reshape(frame['height'],frame['width'],4)[::-1].copy();factor=brightness[key]
   if factor!=1.:pixels[:,:,:3]=np.minimum(pixels[:,:,:3].astype(np.float32)*factor,pixels[:,:,3:4]).astype(np.uint8)
   effects=next((item['clip']['layout'].get('effects',[]) for item in result['plan']['visual'] if item['clip']['id']==key),[])
   if any(e['enabled'] for e in effects):
    alpha=pixels[:,:,3:4].astype(np.float32);rgb=np.divide(pixels[:,:,:3].astype(np.float32),alpha,out=np.zeros_like(pixels[:,:,:3],dtype=np.float32),where=alpha!=0)
    for effect in effects:
     if not effect['enabled']:continue
     rgb=np.clip(rgb*effect['amount'] if effect['kind']=='Brightness' else (rgb-.5)*effect['amount']+.5,0.,1.)
    pixels[:,:,:3]=np.rint(rgb*alpha).astype(np.uint8)
   images[key]=QImage(pixels.tobytes(),frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).convertToFormat(QImage.Format_ARGB32_Premultiplied)
  # Existing32 active visual/8MP per-source admission bounds this collection.
  # Report its actual copied bytes separately from decoder leases/region cache.
  self.sources=images;self.source_metadata={key:{k:frame[k] for k in ('width','height','pixel_aspect')} for key,frame in result['images'].items()};self.materialized_bytes=sum(image.sizeInBytes() for image in images.values());self.last_plan=deepcopy(result['plan']);self.raw_plan=raw_plan;return self.compose(self.last_plan,False)
 def recompose(self,change):
  if self.last_plan is None:return
  plan=deepcopy(self.last_plan)
  if change:
   key,layout=change
   if any(item['recipe']['id']==key for item in self.raw_plan['text']):
    # Text resizing must reflow at native resolution, matching its eventual
    # accepted recipe; a stretched old glyph plane is not the same result.
    import numpy as np
    from PySide6.QtGui import QImage
    raw=deepcopy(self.raw_plan);text_ids={r['recipe']['id'] for r in raw['text']}
    for item in raw['text']:
     if item['recipe']['id']==key:item['recipe']['style'].update({field:deepcopy(layout[field]) for field in ('bounds','rotation','opacity')})
    augmented=self.text.augment(dict(plan=raw,images={},error=''));images={key:value for key,value in self.sources.items() if key not in text_ids};metadata={key:value for key,value in self.source_metadata.items() if key not in text_ids};draft_bytes=0
    for text_id,frame in augmented['images'].items():
     pixels=np.frombuffer(frame['data'],np.uint8).reshape(frame['height'],frame['width'],4)[::-1].copy();image=QImage(pixels.tobytes(),frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).convertToFormat(QImage.Format_ARGB32_Premultiplied);images[text_id]=image;metadata[text_id]={k:frame[k] for k in ('width','height','pixel_aspect')};draft_bytes+=image.sizeInBytes()
    output=self.compose(augmented['plan'],True,images,metadata);self.stats['transient_text_materialized_bytes']=draft_bytes;return output
   for item in plan['visual']:
    if item['clip']['id']==key:item['clip']['layout']=deepcopy(layout)
  return self.compose(plan,bool(change))
 def compose(self,plan,transient,sources=None,metadata=None):
  import numpy as np
  from types import SimpleNamespace
  from PySide6.QtGui import QImage,QPainter,QColor
  from composition import asset_matrix,world_matrix
  from studio_composition import masked_image
  scene,_=scene_for(dict(plan=plan,images=self.source_metadata if metadata is None else metadata));w,h=scene['canvas'];images=dict(self.sources if sources is None else sources)
  background=new_layer('Image','project-background');background.update(id='project-background',order=-1,fit='Stretch');scene['layers'].insert(0,background);base=QImage(1,1,QImage.Format_ARGB32_Premultiplied);base.fill(QColor(plan['settings']['background']));images[background['id']]=base
  canvas=SimpleNamespace(editor=SimpleNamespace(config=scene,images=images,pending_paint=None),canvas_size=(w,h),stroke=None,mask_image=masked_image,source_matrix=lambda row:world_matrix(scene,row['id']) if row['type']=='Group' else asset_matrix(scene,row,(w,h),(images[row['id']].width(),images[row['id']].height())))
  projection=np.array([[w,0,w/2],[0,h,h/2],[0,0,1.]])
  began=time.perf_counter();art=self.projection.render(canvas,w,h,projection);image=QImage(w,h,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(plan['settings']['background']));p=QPainter(image);p.drawImage(0,0,art);p.end();self.image=image;self.stats=dict(self.projection.stats,**self.text.stats,render_ms=(time.perf_counter()-began)*1000,frame=plan['frame'],revision=plan['revision'],native_size=[w,h],backend='Qt CPU reference',materialized_source_bytes=self.materialized_bytes,materialized_source_images=len(self.sources),unaccepted_transform_preview=transient);return image
 def close(self):
  self.sources.clear();self.source_metadata.clear();self.last_plan=self.raw_plan=None;self.materialized_bytes=0;self.text.close();self.image=None;self.projection.cache.clear();self.projection.latest.clear();self.projection.scratch.clear();self.projection.output=None;self.projection.bytes=0;self.projection.scratch_bytes=0;self.projection.stats.update(cache_bytes=0,scratch_bytes=0,closed=True);self.stats=dict(self.projection.stats,**self.text.stats,materialized_source_bytes=0,materialized_source_images=0)
