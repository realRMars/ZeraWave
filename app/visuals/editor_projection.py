"""Editor passes owned by renderer.py, reusing ImageLayers resource ownership.

No document policy or world playback lives here. Integer-aligned source pixels
use GPU projection and encoded integer composition. Other sampling phases use
the retained Qt reference projection, uploaded only when dependencies change.
GPU reads exist only in explicit sampling/testing, never the display loop.
"""
import ctypes,json,math,time
from functools import lru_cache
import moderngl
import numpy as np
from PySide6.QtGui import QImage,QPainter,QColor
from image_layers import ImageLayers,FULL_VERTEX
from composition import ordered_children,is_branch,effective,partition_aligned
from native_raster import NativeImage

EDITOR_FRAGMENT='''#version 330
uniform sampler2D image,backdrop; uniform mat3 inverse_pixels;
uniform ivec2 output_size; uniform ivec4 source_crop; uniform int group_source,mode,coverage,strength;
out vec4 color;
uvec4 div255(uvec4 x){return (x+(x>>8u)+128u)>>8u;}
uvec4 fetch8(sampler2D t,ivec2 p){return uvec4(round(texelFetch(t,p,0)*255.));}
uvec4 over(uvec4 b,uvec4 s){return s+div255(b*(255u-s.a));}
void main(){ivec2 at=ivec2(gl_FragCoord.xy);uvec4 b=fetch8(backdrop,at),s=uvec4(0);
 if(group_source==1)s=fetch8(image,at);
 else {vec2 xy=(inverse_pixels*vec3(float(at.x)+.5,float(output_size.y-at.y)-.5,1.)).xy;
  ivec2 p=ivec2(floor(xy)),sz=textureSize(image,0);
  if(all(greaterThanEqual(p,source_crop.xy))&&all(lessThan(p,source_crop.zw)))s=fetch8(image,ivec2(p.x,sz.y-1-p.y));}
 uvec4 result=b;uint ca=uint(coverage);
 if(mode==0){s=div255(s*ca);result=over(b,s);}
 else if(mode==5){result=div255(min(b+s,uvec4(255))*ca+b*(255u-ca));}
 else if(mode==3||strength<255){
  s=div255(s*ca);uvec4 normal=over(b,s),mixed=normal;
  uint mixed_alpha=255u-div255(uvec4((255u-s.a)*(255u-b.a))).a;
  if(mode==3){mixed.rgb=b.rgb+s.rgb-((max(s.a*b.rgb,b.a*(s.a-s.rgb))-b.a*(s.a-s.rgb)+127u)/255u);mixed.a=s.a+(b.a*(255u-s.a)+127u)/255u;}
  if(mode==1)mixed=uvec4(div255(uvec4(b.rgb*s.rgb+s.rgb*(255u-b.a)+b.rgb*(255u-s.a),0)).rgb,mixed_alpha);
  if(mode==2)mixed=uvec4(255u-div255(uvec4((255u-b.rgb)*(255u-s.rgb),0)).rgb,mixed_alpha);
  if(mode==4)mixed=uvec4(b.rgb+s.rgb-div255(uvec4(2u*min(s.rgb*b.a,b.rgb*s.a),0)).rgb,mixed_alpha);
  result=(normal*(255u-uint(strength))+mixed*uint(strength)+127u)/255u;
 }else{
  uint alpha=255u-div255(uvec4((255u-s.a)*(255u-b.a))).a;uvec4 mixed=uvec4(0,0,0,alpha);
  if(mode==1)mixed.rgb=div255(uvec4(b.rgb*s.rgb+s.rgb*(255u-b.a)+b.rgb*(255u-s.a),0)).rgb;
  if(mode==2)mixed.rgb=255u-div255(uvec4((255u-b.rgb)*(255u-s.rgb),0)).rgb;
  if(mode==4)mixed.rgb=b.rgb+s.rgb-div255(uvec4(2u*min(s.rgb*b.a,b.rgb*s.a),0)).rgb;
  result=div255(mixed*ca+b*(255u-ca));
 }
 color=vec4(min(result,uvec4(255)))/255.;
}'''
PRESENT_FRAGMENT='''#version 330
uniform sampler2D image,clip_image;in vec2 uv;out vec4 color;
void main(){color=texture(image,uv)*texture(clip_image,uv).a;}'''

@lru_cache(maxsize=512)
def opacity_coverage(opacity,mode):
    # Installed Qt's 256/255 fast/raster opacity paths differ. Query the
    # software reference once per parameter, not via GPU readback.
    value=QImage(1,1,QImage.Format_ARGB32_Premultiplied);value.fill(0)
    source=QImage(1,1,QImage.Format_ARGB32_Premultiplied);source.fill(0xffffffff)
    p=QPainter(value);p.setOpacity(opacity);p.setCompositionMode({'Normal':QPainter.CompositionMode_SourceOver,'Multiply':QPainter.CompositionMode_Multiply,'Screen':QPainter.CompositionMode_Screen,'Difference':QPainter.CompositionMode_Difference,'Plus':QPainter.CompositionMode_Plus}[mode]);p.drawImage(0,0,source);p.end();return value.pixelColor(0,0).alpha()

class EditorProjection(ImageLayers):
    def __init__(self,ctx,vertices):
        super().__init__(ctx,vertices)
        resources=[]
        try:
            self.editor_program=ctx.program(vertex_shader=FULL_VERTEX,fragment_shader=EDITOR_FRAGMENT);resources.append(self.editor_program)
            self.editor_vao=ctx.simple_vertex_array(self.editor_program,vertices,'in_position');resources.append(self.editor_vao)
            self.present_program=ctx.program(vertex_shader=FULL_VERTEX,fragment_shader=PRESENT_FRAGMENT);resources.append(self.present_program)
            self.present_vao=ctx.simple_vertex_array(self.present_program,vertices,'in_position');resources.append(self.present_vao)
        except BaseException:
            for r in reversed(resources):r.release()
            super().close();raise
        self.source_stamps={};self.row_sources={};self.result_texture=None;self.signature=None;self.structure_signature=None;self.reference=None
        self.stats=dict(route='initializing',upload_bytes=0,reused_tiles=0,changed_tiles=0,recomposited_pixels=0,source_bytes=0,target_bytes=0,readback_bytes=0,draw_ms=0.,sampling_reference=False)
        self.clip_texture=None;self.clip_signature=None;self.geometry_signature=None;self.geometry=None
        self.texture_frames={};self.source_spare=None;self.display_spare=None
    @staticmethod
    def tile_ids(im):
        # Versions are immutable; avoid rebuilding their ID tuple for each row
        # and pass. This metadata holds no ancestor versions or native readers.
        if not hasattr(im,'_editor_tile_ids'):im._editor_tile_ids=tuple(t.id for t in im.tiles())
        return im._editor_tile_ids
    def frame(self,texture):
        if texture not in self.texture_frames:self.texture_frames[texture]=self.ctx.framebuffer((texture,))
        return self.texture_frames[texture]
    def drop(self,texture):
        frame=self.texture_frames.pop(texture,None)
        if frame is not None:frame.release()
        texture.release()
    def retire_source(self,texture):
        if self.source_spare is not None:self.drop(self.source_spare)
        self.source_spare=texture
    def sources(self,canvas):
        found={}
        for row in canvas.editor.config['layers']:
            im=canvas.editor.images.get(row['id']) or canvas.editor.images.get(row['asset'])
            if canvas.stroke and row['id']==canvas.stroke['row']:im=canvas.stroke['preview']
            elif getattr(canvas.editor,'pending_paint',None) and row['id']==canvas.editor.pending_paint['row']:im=canvas.editor.pending_paint['image']
            found[row['id']]=im
        return found
    def source_key(self,im,row):
        identity=(im.family,self.tile_ids(im)) if isinstance(im,NativeImage) else im.cacheKey()
        return identity,json.dumps(row['masks'],sort_keys=True)
    def prepare(self,canvas,size,projection):
        scene=canvas.editor.config;images=self.sources(canvas);matrices={};direct=True
        stamps=[]
        for row in scene['layers']:
            im=images[row['id']]
            stamps.append((row['id'],(im.family,self.tile_ids(im)) if isinstance(im,NativeImage) else im.cacheKey() if im is not None else None))
        structure=[]
        for row in scene['layers']:
            r=dict(row);im=images[row['id']];r['asset']=im.family if isinstance(im,NativeImage) else row['asset'];r['_size']=(im.width(),im.height()) if im is not None else None;structure.append(r)
        structure_signature=json.dumps([structure,scene.get('canvas'),list(projection.flat),list(size)],sort_keys=True)
        signature=(structure_signature,tuple(stamps))
        if structure_signature==self.geometry_signature:
            matrices,direct=self.geometry;return scene,images,matrices,direct,signature,structure_signature
        for row in scene['layers']:
            im=images[row['id']]
            if row['type']=='Group':
                if row['masks'] or row['crop']!=[0.,0.,1.,1.]:direct=False
                continue
            if im is None:continue
            c=row['crop'];crop=np.array([[1/(c[2]-c[0]),0.,-c[0]/(c[2]-c[0])-.5],[0.,1/(c[3]-c[1]),-c[1]/(c[3]-c[1])-.5],[0.,0.,1.]])
            flip=np.diag([-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1,1.])
            matrix=projection@canvas.source_matrix(row)@flip@crop@np.diag([1/im.width(),1/im.height(),1.])
            matrices[row['id']]=matrix
            step=matrix[:2,:2];origin=matrix[:2,2]
            if not np.allclose(abs(step),np.eye(2),atol=1e-9) or not np.allclose(origin,np.rint(origin),atol=1e-9):direct=False
            # Source/crop boundaries must align with pixel cells for exactness.
            if any(abs(v-round(v))>1e-9 for v in (c[0]*im.width(),c[1]*im.height(),c[2]*im.width(),c[3]*im.height())):direct=False
        self.geometry_signature=structure_signature;self.geometry=(matrices,direct)
        return scene,images,matrices,direct,signature,structure_signature
    def upload_sources(self,canvas,scene,images):
        selected={};candidates={};new_stamps={};upload=changed=reused=0
        try:
            for row in scene['layers']:
                im=images[row['id']]
                if im is None or row['type']=='Group' or not effective(scene,row,'enabled'):continue
                key=self.source_key(im,row)
                if key in selected:continue
                ids=self.tile_ids(im) if isinstance(im,NativeImage) else (im.cacheKey(),)
                previous=self.textures.get(key);before=self.source_stamps.get(key)
                if previous is not None and before==ids:selected[key]=previous;reused+=len(ids);new_stamps[key]=ids;continue
                predecessor=self.row_sources.get(row['id'])
                if predecessor is not None and predecessor[1]==key[1] and isinstance(im,NativeImage) and predecessor[0][0]==im.family:
                    previous=self.textures.get(predecessor);before=self.source_stamps.get(predecessor)
                size=(im.width(),im.height())
                spare=self.source_spare;self.source_spare=None
                if spare is not None and spare.size!=size:self.drop(spare);spare=None
                cost=sum(t.width*t.height*4 for t in self.textures.values())+sum(t.width*t.height*4 for t in candidates.values())+size[0]*size[1]*4
                if cost>256*1024*1024:
                    if spare is not None:self.drop(spare)
                    raise MemoryError('Editor source residency/staging exceeds 256 MiB; previous display retained')
                texture=spare or self.ctx.texture(size,4,alignment=1);texture.filter=(moderngl.NEAREST,moderngl.NEAREST);texture.repeat_x=texture.repeat_y=False;candidates[key]=texture
                if previous is not None:
                    self.ctx.copy_framebuffer(self.frame(texture),self.frame(previous))
                masked=canvas.mask_image(im,row) if row['masks'] else None
                if isinstance(im,NativeImage):
                    for i,t in enumerate(im.tiles()):
                        if before is not None and i<len(before) and before[i]==t.id:reused+=1;continue
                        if masked is None:data=ctypes.string_at(t.data,t.length)
                        else:
                            canonical=masked.copy(t.x,im.height()-t.y-t.height,t.width,t.height).convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True);data=bytes(canonical.constBits())
                        texture.write(data,viewport=(t.x,t.y,t.width,t.height),alignment=1);upload+=t.length;changed+=1
                else:
                    pixels=masked or im;canonical=pixels.convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True);texture.write(canonical.constBits(),alignment=1);upload+=canonical.sizeInBytes();changed+=1
                selected[key]=texture;new_stamps[key]=ids
        except BaseException:
            for t in candidates.values():self.drop(t)
            raise
        return selected,candidates,new_stamps,dict(upload_bytes=upload,changed_tiles=changed,reused_tiles=reused)
    def render_editor(self,canvas,size,projection):
        begin=time.perf_counter()
        try:scene,images,matrices,direct,signature,structure_signature=self.prepare(canvas,size,projection)
        except Exception as exc:
            self.stats['error']=str(exc)[:180]
            if self.result_texture is None:raise
            return self.result_texture
        if signature==self.signature and self.result_texture is not None:
            self.stats['route']='GPU cached presentation';return self.result_texture
        raw=getattr(self.ctx,'raw',self.ctx);saved=raw.viewport
        if self.target_size!=tuple(size):
            for pair in self.buffers.values():
                for t,f in pair:f.release();t.release()
            self.buffers.clear()
        self.target_size=tuple(size)
        selected=candidates={};stamps={};used_levels=set()
        try:
            if not direct:
                from cpu_projection import Projection
                if self.reference is None:self.reference=Projection()
                pixels=self.reference.render(canvas,*size,projection)
                canonical=pixels.convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True)
                if size[0]*size[1]*4>128*1024*1024:raise MemoryError('Editor reference staging exceeds 128 MiB')
                if self.source_spare is not None:self.drop(self.source_spare);self.source_spare=None
                if sum(t.width*t.height*4 for t in self.textures.values())+size[0]*size[1]*4>256*1024*1024:raise MemoryError('Editor reference residency/staging exceeds 256 MiB; previous display retained')
                texture=self.ctx.texture(size,4,canonical.constBits(),alignment=1);texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
                selected={('reference',):texture};candidates=dict(selected);metrics=dict(upload_bytes=canonical.sizeInBytes(),changed_tiles=1,reused_tiles=0)
                result=texture;self.stats['route']='GPU presentation / exact Qt reference sampling';self.stats['sampling_reference']=True
            else:
                selected,candidates,stamps,metrics=self.upload_sources(canvas,scene,images)
                damage=(0,0,*size)
                if structure_signature==self.structure_signature and self.result_texture is not None and self.result_texture.size==size:
                    points=[]
                    for row in scene['layers']:
                        im=images[row['id']]
                        # Moving/decoded QImages have no immutable tile IDs.
                        # A changed frame requires full composition, even when
                        # its dimensions, asset identity and view stay fixed.
                        if im is not None and not isinstance(im,NativeImage) and row['type']!='Group' and self.row_sources.get(row['id'])!=self.source_key(im,row):
                            points=None;break
                        if not isinstance(im,NativeImage) or row['id'] not in matrices:continue
                        key=self.row_sources.get(row['id']);before=self.source_stamps.get(key)
                        for i,t in enumerate(im.tiles()):
                            if before is not None and i<len(before) and before[i]==t.id:continue
                            y=im.height()-t.y-t.height
                            points.extend((matrices[row['id']]@np.array([x,py,1.]))[:2] for x in (t.x,t.x+t.width) for py in (y,y+t.height))
                    if points is None:damage=(0,0,*size)
                    elif points:
                        x=max(0,math.floor(min(p[0] for p in points))-2);y=max(0,math.floor(min(p[1] for p in points))-2);right=min(size[0],math.ceil(max(p[0] for p in points))+2);bottom=min(size[1],math.ceil(max(p[1] for p in points))+2)
                        damage=(x,size[1]-bottom,max(0,right-x),max(0,bottom-y))
                    else:damage=(0,0,0,0)
                passes=0
                # Each level uses the existing bounded ImageLayers target pair.
                # Retain an independent final display until every pass succeeds.
                p=self.editor_program;p['image'].value=0;p['backdrop'].value=1;p['output_size'].value=size
                def children(parent,level):
                    nonlocal passes
                    used_levels.add(level)
                    pair=self.framebuffer_pair(level,size);index=0
                    if level==0 and damage!=(0,0,*size) and self.result_texture is not None:
                        previous_frame=self.frame(self.result_texture)
                        for texture,frame in pair:self.ctx.copy_framebuffer(frame,previous_frame)
                    pair[0][1].clear(0.,0.,0.,0.,viewport=damage)
                    for row in ordered_children(scene,parent):
                        if not effective(scene,row,'enabled') or not is_branch(scene,row) and not row['source_visible']:continue
                        group=is_branch(scene,row);im=images.get(row['id'])
                        source=children(row['id'],level+1) if group else selected.get(self.source_key(im,row)) if im is not None else None
                        if source is None:continue
                        strength=row.get('blend_strength',1.);mode='Normal' if strength==0 else row['blend'];partition=not row.get('_own') and partition_aligned(scene,row)
                        mode_id=5 if partition and (mode=='Normal' or mode!='Add' and strength>=1.) else ('Normal','Multiply','Screen','Add','Difference').index(mode)
                        prepared=mode=='Add' or mode!='Normal' and strength<1.
                        p['mode'].value=mode_id;p['strength'].value=round(strength*255);p['coverage'].value=opacity_coverage(row['opacity'],'Normal' if prepared else 'Plus' if mode_id==5 else mode)
                        p['group_source'].value=int(group);p['inverse_pixels'].write((np.eye(3) if group else np.linalg.inv(matrices[row['id']])).T.astype('f4').tobytes())
                        p['source_crop'].value=(0,0,0,0) if group else tuple(round(v*(im.width() if i%2==0 else im.height())) for i,v in enumerate(row['crop']))
                        source.use(0);pair[index][0].use(1)
                        with self.ctx.scope(framebuffer=pair[1-index][1],enable_only=0):
                            raw.viewport=damage
                            if damage[2] and damage[3]:self.editor_vao.render(moderngl.TRIANGLE_STRIP);passes+=1
                        index=1-index
                    return pair[index][0]
                composed=children(None,0);result=self.display_spare;self.display_spare=None
                if result is not None and result.size!=size:self.drop(result);result=None
                if result is None:result=self.ctx.texture(size,4,alignment=1);result.filter=(moderngl.NEAREST,moderngl.NEAREST)
                try:self.ctx.copy_framebuffer(self.frame(result),self.buffers[0][0 if composed is self.buffers[0][0][0] else 1][1])
                except BaseException:self.drop(result);raise
                self.stats['route']='GPU exact integer projection/composition';self.stats['sampling_reference']=False
                self.stats.update(damage_pixels=damage[2]*damage[3],passes=passes,drawn_pixels=passes*damage[2]*damage[3])
            old=self.textures;self.textures=selected;self.source_stamps=stamps
            self.row_sources={row['id']:self.source_key(images[row['id']],row) for row in scene['layers'] if images[row['id']] is not None and row['type']!='Group'} if direct else {}
            for level in list(self.buffers):
                if level not in used_levels:
                    for t,f in self.buffers.pop(level):f.release();t.release()
            for key,t in old.items():
                if key not in selected or selected[key] is not t:self.retire_source(t)
            previous=self.result_texture;self.result_texture=result;self.signature=signature;self.structure_signature=structure_signature
            if previous is not None and previous is not result and previous not in old.values():
                if self.display_spare is not None:self.drop(self.display_spare)
                self.display_spare=previous
            elif previous is not None and previous is not result and previous in old.values() and previous in selected.values():pass
            self.stats.update(metrics,source_bytes=sum(t.width*t.height*4 for t in self.textures.values()),source_spare_bytes=self.source_spare.width*self.source_spare.height*4 if self.source_spare is not None else 0,display_bytes=result.width*result.height*4,display_spare_bytes=self.display_spare.width*self.display_spare.height*4 if self.display_spare is not None else 0,target_bytes=sum(t.width*t.height*8 for pair in self.buffers.values() for t,f in pair),recomposited_pixels=self.stats['recomposited_pixels']+damage[2]*damage[3] if direct else self.stats['recomposited_pixels']+size[0]*size[1],draw_ms=(time.perf_counter()-begin)*1000,error='')
            return result
        except Exception as exc:
            for t in candidates.values():
                if t not in self.textures.values():self.drop(t)
            self.stats['error']=str(exc)[:180]
            if self.result_texture is None:raise
            return self.result_texture
        finally:raw.viewport=saved
    def present(self,target,texture,clip=None):
        raw=getattr(self.ctx,'raw',self.ctx);saved=raw.viewport
        try:
            signature=(target.size,clip)
            if signature!=self.clip_signature:
                from PySide6.QtCore import QRectF
                mask=QImage(*target.size,QImage.Format_RGBA8888_Premultiplied);mask.fill(0);q=QPainter(mask)
                if clip is not None:q.setClipRect(QRectF(*clip))
                q.fillRect(mask.rect(),QColor('white'));q.end();canonical=mask.mirrored(False,True)
                candidate=self.ctx.texture(target.size,4,canonical.constBits(),alignment=1);candidate.filter=(moderngl.NEAREST,moderngl.NEAREST)
                previous=self.clip_texture;self.clip_texture=candidate;self.clip_signature=signature
                if previous is not None:previous.release()
            texture.use(0);self.clip_texture.use(1);self.present_program['image'].value=0;self.present_program['clip_image'].value=1
            with self.ctx.scope(framebuffer=target,enable_only=moderngl.BLEND):
                raw.viewport=(0,0,*target.size);raw.blend_func=(moderngl.ONE,moderngl.ONE_MINUS_SRC_ALPHA);self.present_vao.render(moderngl.TRIANGLE_STRIP)
        finally:raw.viewport=saved
    def read_pixel(self,x,y):
        if self.result_texture is None:return None
        if not 0<=x<self.result_texture.width or not 0<=y<self.result_texture.height:return None
        data=self.frame(self.result_texture).read(viewport=(x,self.result_texture.height-1-y,1,1),components=4,alignment=1);self.stats['readback_bytes']+=4
        return QImage(data,1,1,QImage.Format_RGBA8888_Premultiplied).pixelColor(0,0)
    def close(self):
        if self.closed:return
        result=self.result_texture;shared=result in self.textures.values();self.result_texture=None
        for frame in self.texture_frames.values():frame.release()
        self.texture_frames.clear()
        super().close()
        if result is not None and not shared:result.release()
        for texture in (self.source_spare,self.display_spare):
            if texture is not None:texture.release()
        self.source_spare=self.display_spare=None
        if self.clip_texture is not None:self.clip_texture.release();self.clip_texture=None
        for resource in (self.editor_vao,self.editor_program,self.present_vao,self.present_program):resource.release()
        self.reference=None;self.source_stamps.clear();self.row_sources.clear();self.signature=None
        self.geometry=None;self.geometry_signature=None
        self.stats.update(source_bytes=0,source_spare_bytes=0,display_bytes=0,display_spare_bytes=0,target_bytes=0,closed=True)
