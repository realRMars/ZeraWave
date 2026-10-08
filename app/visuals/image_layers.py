"""Dynamic media composition on the existing renderer's completed target.

Qt decode on one cancellable worker; all GL allocation/drawing/release stays on
the renderer thread. Premultiplied alpha in existing display-encoded RGB keeps
untagged/tagged-sRGB images and the baseline world presentation consistent.
"""
from copy import deepcopy
import threading
import moderngl
import numpy as np
from composition import asset_matrix,world_matrix,effective,ancestors,BLENDS,is_branch,ordered_children,partition_aligned
from media_frames import FrameReader
from media_registry import validate_scene,decode_image

VERTEX='''#version 330
in vec2 in_position; uniform vec2 canvas; uniform vec4 bounds; out vec2 uv;
void main(){uv=(in_position+1.)*.5;vec2 pixel=bounds.xy+uv*bounds.zw;
gl_Position=vec4(pixel/canvas*2.-1.,0.,1.);}'''
FRAGMENT='''#version 330
uniform sampler2D image,backdrop,mask_image;uniform float opacity,blend_strength;uniform vec2 canvas_fit;uniform int mode,use_mask;
uniform mat3 inverse_transform,mask_inverse;uniform vec4 crop,group_crop;uniform vec2 flips;uniform int group_layer;
in vec2 uv;out vec4 color;
vec4 own_sample(vec2 src){
 // Interpolate premasked texels, matching the extracted native raster. Sampling
 // color and coverage separately multiplies two interpolants and makes halos.
 ivec2 size=textureSize(image,0);vec2 pixel=src*vec2(size)-.5;
 ivec2 base=ivec2(floor(pixel));vec2 f=fract(pixel);vec4 value=vec4(0.);
 for(int y=0;y<2;y++)for(int x=0;x<2;x++){
  ivec2 at=clamp(base+ivec2(x,y),ivec2(0),size-1);
  float weight=(x==0?1.-f.x:f.x)*(y==0?1.-f.y:f.y);
  value+=texelFetch(image,at,0)*(use_mask==1?texelFetch(mask_image,at,0).r:1.)*weight;
 }return value;
}
void main(){vec2 p=vec2(uv.x-.5,.5-uv.y);vec2 local=(inverse_transform*vec3(p,1.)).xy+.5;
 vec4 s=vec4(0.);if(all(greaterThanEqual(local,vec2(0.)))&&all(lessThanEqual(local,vec2(1.)))){
 local=mix(local,1.-local,flips);vec2 src=mix(crop.xy,crop.zw,local);src.y=1.-src.y;
 s=(group_layer==0&&(use_mask==1||mode==5)?own_sample(src):texture(image,src))*opacity;}
 if(group_layer==1){vec2 q=(mask_inverse*vec3(p,1.)).xy+.5;
 if(any(lessThan(q,group_crop.xy))||any(greaterThan(q,group_crop.zw)))s=vec4(0.);
 if(use_mask==1)s*=texture(mask_image,vec2(q.x,1.-q.y)).r;}
 if(any(greaterThan(abs(p),canvas_fit*.5)))s=vec4(0.);
 vec4 b=texture(backdrop,uv);if(mode==5){color=min(s+b,vec4(1.));return;}if(mode==0){color=s+b*(1.-s.a);return;}
 vec3 cs=s.a>0.?s.rgb/s.a:vec3(0.);vec3 cb=b.a>0.?b.rgb/b.a:vec3(0.);vec3 m=cs;
 if(mode==1)m=cs*cb;if(mode==2)m=cs+cb-cs*cb;if(mode==3)m=min(vec3(1.),cs+cb);if(mode==4)m=abs(cb-cs);
 color=vec4((1.-s.a)*b.rgb+(1.-b.a)*s.rgb+s.a*b.a*mix(cs,clamp(m,0.,1.),blend_strength),s.a+b.a*(1.-s.a));}'''
FULL_VERTEX='''#version 330
in vec2 in_position;out vec2 uv;void main(){uv=(in_position+1.)*.5;gl_Position=vec4(in_position,0.,1.);}'''

def group_visible(scene,row):return is_branch(scene,row) or row['source_visible']

def asset_key(asset):
    meta=asset.get('metadata',{})
    key=(asset['id'],asset['path'],meta.get('bytes'),meta.get('mtime_ns'))
    if asset.get('kind')=='Models':
        import hashlib,json
        key+=(hashlib.sha256(json.dumps(meta.get('dependencies',{}),sort_keys=True).encode()).hexdigest(),)
    return key
def bounds(size,image,layer):
    width,height=size;iw,ih=image
    ratio=(min if layer['fit']=='Fit' else max)(width/iw,height/ih)*layer['scale']
    w,h=iw*ratio,ih*ratio
    return ((.5+layer['x'])*width-w/2,(.5-layer['y'])*height-h/2,w,h)

class ImageLayers:
    def __init__(self,ctx,vertices):
        self.ctx,self.vertices=ctx,vertices;self.program=self.vao=None;self.textures={}
        self.config=None;self.desired=None;self.revision=-1;self.session=None;self.applied=-1;self.error='';self.pending=False
        self.condition=threading.Condition();self.task=None;self.result=None;self.cancel=None;self.closed=False;self.generation=0
        self.worker=threading.Thread(target=self.decode,name='Renderer still-image decode',daemon=True);self.worker.start()
        self.frames=FrameReader();self.animated={};self.runtime={};self.buffers={};self.masks={};self.upload_ms=0.;self.target_size=None
    def request(self,config,revision,session):
        if type(revision) is not int or revision<0 or not isinstance(session,str) or not session or len(session)>64:raise ValueError('Invalid image-layer revision/session.')
        if self.closed:return
        if self.session is not None and session!=self.session:raise ValueError('Image edit belongs to an obsolete session.')
        if session==self.session and revision<=self.revision:return
        clean=validate_scene(config);assets={a['id']:a for a in config['assets']}
        needed={row['asset'] for row in clean['layers'] if effective(clean,row,'enabled') and row['type'] in ('Image','Artwork','Paint','Model') and row['asset'] is not None and clean['presentation']!='World only'}
        selected={}
        for identity in needed:
            asset=assets[identity]
            if asset.get('status')!='Ready' and asset_key(asset) not in self.textures:continue
            if not isinstance(asset.get('metadata'),dict):raise ValueError('Image metadata is unavailable.')
            selected[asset_key(asset)]=deepcopy(asset)
        same_assets=self.desired is not None and self.desired[1]==selected and session==self.session
        self.revision,self.session=revision,session;self.error='';self.desired=(clean,selected);self.runtime=deepcopy(config.get('runtime',{}))
        if all(key in self.textures for key in selected):
            with self.condition:
                if self.cancel:self.cancel.set()
                self.generation+=1;self.task=self.result=None
            self.commit(clean,selected,{});return
        if same_assets and self.pending:return # transform edits do not restart decoding
        with self.condition:
            if self.cancel:self.cancel.set()
            self.generation+=1;self.cancel=threading.Event();self.result=None
            missing={key:asset for key,asset in selected.items() if key not in self.textures}
            self.task=(self.generation,missing,self.cancel);self.pending=True;self.condition.notify()
    def decode(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.closed or self.task is not None)
                if self.closed:return
                generation,missing,cancel=self.task;self.task=None
            images={};error=''
            try:
                for key,asset in missing.items():
                    meta=asset['metadata'];expected={k:meta[k] for k in ('bytes','mtime_ns')}
                    if asset['kind']=='Models':
                        from model_layer import load_model
                        from media_registry import signature
                        if signature(asset['path'])!=expected:raise ValueError('Model changed; Refresh it before use.')
                        model=load_model(asset['path'],cancel)
                        if model['metadata']['dependencies']!=meta.get('dependencies'):raise ValueError('Model dependencies changed; Refresh it before use.')
                        images[key]=(meta,model)
                    else:images[key]=decode_image(asset['path'],cancel,expected=expected)
                    cost=0
                    for meta,value in images.values():
                        cost+=sum(p['vertices'].nbytes+p['indices'].nbytes for p in value['primitives'])+sum(w*h*4 for w,h,b in value['images']) if isinstance(value,dict) else len(value)
                    if cost>128*1024*1024:raise ValueError('Static image/model CPU staging exceeds 128 MiB; hide a source before adding another.')
            except Exception as exc:error=str(exc)[:240];images={}
            with self.condition:
                if not self.closed and generation==self.generation and not cancel.is_set():self.result=(generation,images,error)
            images={} # the result mailbox owns staging; do not retain an idle CPU cache
    def invalidate(self,session,revision):
        if not isinstance(session,str) or not session or len(session)>64 or type(revision) is not int or revision<0:raise ValueError('Invalid image session boundary.')
        if revision<=self.revision:return
        with self.condition:
            if self.cancel:self.cancel.set()
            self.generation+=1;self.task=self.result=None;self.pending=False
        self.session=session;self.revision=revision;self.desired=None
        self.runtime={};self.frames.close()
        for texture in self.animated.values():texture.release()
        self.animated.clear()
    def poll(self):
        with self.condition:result,self.result=self.result,None
        if result is None or result[0]!=self.generation:return
        if result[2]:self.error=result[2];self.pending=False;return
        self.commit(*self.desired,result[1])
    def commit(self,config,selected,images):
        candidates={};mask_candidates={}
        try:
            if self.target_size and config['presentation']!='World only' and config['layers']:
                depth=max(len(ancestors(config,r['id']))+is_branch(config,r) for r in config['layers'])
                if self.target_size[0]*self.target_size[1]*16*(depth+1)>256*1024*1024:raise ValueError('Isolated groups exceed 256 MiB at the current output resolution; previous composition retained.')
                # Preallocate required group targets before accepting the edit.
                for level in range(depth+1):self.framebuffer_pair(level,self.target_size)
            mask_cost=0
            source_meta={r['id']:r.get('metadata',{}) for r in selected.values()}
            source_meta.update({r['id']:r.get('metadata',{}) for r in (self.desired[1].values() if self.desired else [])})
            for row in config['layers']:
                if not row['masks'] or not effective(config,row,'enabled') or config['presentation']=='World only':continue
                meta=source_meta.get(row['asset'],{})
                if row['type']=='Group':dimensions=self.target_size
                elif row['type']=='Model':dimensions=(1024,1024)
                else:
                    frame=self.runtime.get(row['id'],{}).get('frame') or {}
                    dimensions=(frame.get('width',meta.get('width',0)),frame.get('height',meta.get('height',0)))
                if dimensions:mask_cost+=dimensions[0]*dimensions[1]
            if mask_cost>64*1024*1024:raise ValueError('Layer masks exceed the 64 MiB mask texture budget; previous composition retained.')
            cost=sum(getattr(t,'byte_size',t.width*t.height*4) for t in self.textures.values())
            for meta,value in images.values():cost+=sum(p['vertices'].nbytes+p['indices'].nbytes for p in value['primitives'])+sum(w*h*4*4//3 for w,h,b in value['images']) if isinstance(value,dict) else len(value)
            cost+=sum(1024*1024*4 for r in config['layers'] if r['type']=='Model')
            if cost>256*1024*1024:raise ValueError('Image/model residency and staging exceed 256 MiB.')
            if selected and self.program is None:
                program=self.ctx.program(vertex_shader=FULL_VERTEX,fragment_shader=FRAGMENT)
                try:vao=self.ctx.simple_vertex_array(program,self.vertices,'in_position')
                except Exception:program.release();raise
                self.program,self.vao=program,vao
            limit=self.ctx.info.get('GL_MAX_TEXTURE_SIZE',8192)
            for key,(meta,data) in images.items():
                if isinstance(data,dict):
                    from model_layer import ModelResource
                    candidates[key]=ModelResource(self.ctx,data);continue
                size=(meta['width'],meta['height'])
                if max(size)>limit:raise ValueError('Image exceeds this device texture limit: '+str(limit))
                texture=self.ctx.texture(size,4,data,alignment=1);candidates[key]=texture
                texture.filter=(moderngl.LINEAR,moderngl.LINEAR);texture.repeat_x=texture.repeat_y=False
            if sum(getattr(t,'byte_size',t.width*t.height*4) for t in list(self.textures.values())+list(candidates.values()))>256*1024*1024:raise ValueError('Texture/model staging exceeds 256 MiB.')
            if any(key not in self.textures and key not in candidates for key in selected):raise ValueError('Image staging is incomplete.')
            resources={key[0]:texture for key,texture in {**self.textures,**candidates}.items()}
            for row in config['layers']:
                if not row['masks'] or not effective(config,row,'enabled') or config['presentation']=='World only':continue
                resource=resources.get(row['asset']);frame=self.runtime.get(row['id'],{}).get('frame') or {}
                dimensions=self.target_size if row['type']=='Group' else (1024,1024) if row['type']=='Model' else resource.size if resource is not None else (frame.get('width',0),frame.get('height',0))
                if not dimensions or not all(dimensions):continue # First animated pixels are not available yet.
                key=self.mask_key(row,dimensions);old_mask=self.masks.get(row['id'])
                if old_mask and old_mask[0]==key:continue
                if sum(t.width*t.height for k,t in list(self.masks.values())+list(mask_candidates.values()))+dimensions[0]*dimensions[1]>64*1024*1024:raise ValueError('Mask texture allocation/staging exceeds 64 MiB.')
                mask_candidates[row['id']]=(key,self.make_mask(row,dimensions))
        except Exception as exc:
            for texture in candidates.values():texture.release()
            for key,texture in mask_candidates.values():texture.release()
            self.error='Image upload failed; previous layers retained: '+str(exc)[:180];self.pending=False;return
        old=self.textures;self.textures={key:old[key] if key in old else candidates[key] for key in selected}
        for key,texture in old.items():
            if key not in self.textures:texture.release()
        self.config=config;self.applied=self.revision;self.pending=False;self.error=''
        for identity,pair in mask_candidates.items():
            previous=self.masks.get(identity)
            if previous:previous[1].release()
            self.masks[identity]=pair
        for key,resource in self.textures.items():
            if hasattr(resource,'retain'):resource.retain({r['id'] for r in config['layers'] if r['asset']==key[0]})
        ids={r['id'] for r in config['layers']}
        for identity in list(self.masks):
            if identity not in ids or not any(r['id']==identity and r['masks'] for r in config['layers']):self.masks.pop(identity)[1].release()
        if self.target_size:
            depth=max((len(ancestors(config,r['id']))+is_branch(config,r) for r in config['layers']),default=0) if config['presentation']!='World only' else -1
            for level in list(self.buffers):
                if level>depth:
                    for t,f in self.buffers.pop(level):f.release();t.release()
    def framebuffer_pair(self,level,size):
        if level in self.buffers and self.buffers[level][0][0].size==size:return self.buffers[level]
        if sum(size[0]*size[1]*16 for _ in range(level+1))>256*1024*1024:raise ValueError('Isolated groups exceed the 256 MiB composition target budget at this resolution.')
        pair=[]
        try:
            for _ in range(2):
                t=self.ctx.texture(size,4,dtype='f2');t.filter=(moderngl.LINEAR,moderngl.LINEAR);t.repeat_x=t.repeat_y=False
                try:f=self.ctx.framebuffer(color_attachments=(t,))
                except Exception:t.release();raise
                pair.append((t,f))
        except Exception:
            for t,f in pair:f.release();t.release()
            raise
        old=self.buffers.get(level);self.buffers[level]=pair
        if old:
            for t,f in old:f.release();t.release()
        return pair
    @staticmethod
    def mask_key(row,size):
        import json
        return (row['id'],tuple(size),json.dumps(row['masks'],sort_keys=True))
    def mask_texture(self,row,size):
        key=self.mask_key(row,size);old=self.masks.get(row['id'])
        if old and old[0]==key:return old[1]
        if sum(t.width*t.height for k,t in self.masks.values())+size[0]*size[1]>64*1024*1024:raise ValueError('Mask texture allocation/staging exceeds 64 MiB; prior output retained where available.')
        texture=self.make_mask(row,size)
        if old:old[1].release()
        self.masks[row['id']]=(key,texture);return texture
    def make_mask(self,row,size):
        from PySide6.QtGui import QImage,QPainter,QPainterPath,QColor
        # QPainter alpha operations need an alpha-bearing surface.
        alpha=QImage(*size,QImage.Format_ARGB32_Premultiplied);alpha.fill(0xffffffff)
        for mask in row['masks']:
            if not mask['enabled']:continue
            shape=QImage(*size,QImage.Format_ARGB32_Premultiplied);shape.fill(0);p=QPainter(shape);p.setRenderHint(QPainter.Antialiasing)
            from artwork import selection_path
            p.fillPath(selection_path(mask,size),QColor('white'));p.end();p=QPainter(alpha);p.setCompositionMode(QPainter.CompositionMode_DestinationIn if mask['mode']=='Keep' else QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,shape);p.end()
        a=np.frombuffer(alpha.constBits(),np.uint8).reshape(size[1],alpha.bytesPerLine())[:,3::4].copy()[::-1]
        texture=self.ctx.texture(size,1,a.tobytes(),alignment=1);texture.filter=(moderngl.LINEAR,moderngl.LINEAR);texture.repeat_x=texture.repeat_y=False
        return texture
    def draw(self,size):
        self.target_size=tuple(size)
        self.upload_ms=0.
        self.poll()
        if self.config is None:return
        if self.config['presentation']=='World only':
            self.frames.close()
            for texture in self.animated.values():texture.release()
            self.animated.clear();return
        from time import perf_counter
        names=set()
        for identity,state in self.runtime.items():
            descriptor=state.get('frame')
            if not descriptor:
                row=next((r for r in self.config['layers'] if r['id']==identity),None)
                if row and row['type']=='Web' and row['web']['offline']=='Hide' and identity in self.animated:self.animated.pop(identity).release()
                continue
            names.add(descriptor['name'])
            try:
                frame=self.frames.read(descriptor)
                if frame:
                    began=perf_counter();old=self.animated.get(identity);dimensions=(frame['width'],frame['height'])
                    if old is not None and old.size==dimensions:old.write(frame['data'],alignment=1)
                    else:
                        texture=self.ctx.texture(dimensions,4,frame['data'],alignment=1);texture.filter=(moderngl.LINEAR,moderngl.LINEAR);texture.repeat_x=texture.repeat_y=False
                        self.animated[identity]=texture
                        if old is not None:old.release()
                    self.upload_ms=(perf_counter()-began)*1000
            except Exception as exc:self.error='Frame upload: '+str(exc)[:180]
        self.frames.retain(names)
        wanted={r['id'] for r in self.config['layers'] if r['type'] in ('Video','GIF','Sprite','Web') and effective(self.config,r,'enabled')}
        for identity in list(self.animated):
            if identity not in wanted:self.animated.pop(identity).release()
        if not self.textures and not self.animated:return
        if self.program is None:
            self.program=self.ctx.program(vertex_shader=FULL_VERTEX,fragment_shader=FRAGMENT);self.vao=self.ctx.simple_vertex_array(self.program,self.vertices,'in_position')
        assets={key[0]:texture for key,texture in self.textures.items()}
        raw=getattr(self.ctx,'raw',self.ctx)
        saved_viewport=raw.viewport
        try:
            output=self.ctx.screen
            root=self.framebuffer_pair(0,size);self.ctx.copy_framebuffer(root[0][1],output)
            if self.config['presentation']=='Layers only':root[0][1].clear(0.,0.,0.,1.)
            self.program['image'].value=0;self.program['backdrop'].value=1;self.program['mask_image'].value=2
            logical=self.config.get('canvas') or size;ratio=min(size[0]/logical[0],size[1]/logical[1]);canvas_fit=(logical[0]*ratio/size[0],logical[1]*ratio/size[1]);self.program['canvas_fit'].value=canvas_fit
            def children(parent,level):
                pair=self.framebuffer_pair(level,size);index=0
                if parent is not None:pair[0][1].clear(0.,0.,0.,0.)
                rows=ordered_children(self.config,parent)
                for row in rows:
                    if not effective(self.config,row,'enabled') or row['opacity']<=0 or not group_visible(self.config,row):continue
                    group=is_branch(self.config,row)
                    texture=children(row['id'],level+1) if group else self.animated.get(row['id']) if row['type'] in ('Video','GIF','Sprite','Web') else assets.get(row['asset'])
                    if texture is None:continue
                    if row['type']=='Model':texture=texture.render(row)
                    frame=(self.runtime.get(row['id'],{}).get('frame') or {});sar=frame.get('pixel_aspect',1.)
                    inverse=np.eye(3) if group else np.linalg.inv(asset_matrix(self.config,row,size,(texture.width*sar,texture.height)))
                    self.program['inverse_transform'].write(inverse.T.astype('f4').tobytes());self.program['crop'].value=(0.,0.,1.,1.) if group else tuple(row['crop']);self.program['flips'].value=(0.,0.) if group else (float(row['flip_x']),float(row['flip_y']))
                    self.program['group_layer'].value=int(row['type']=='Group');self.program['group_crop'].value=tuple(row['crop']);self.program['mask_inverse'].write((np.linalg.inv(np.diag([*canvas_fit,1.])@world_matrix(self.config,row['id'])) if row['type']=='Group' else np.eye(3)).T.astype('f4').tobytes())
                    use_mask=bool(row['masks']) and (not group or row['type']=='Group');self.program['use_mask'].value=int(use_mask)
                    if use_mask:self.mask_texture(row,texture.size).use(2)
                    self.program['opacity'].value=row['opacity'];self.program['blend_strength'].value=row['blend_strength'];self.program['mode'].value=5 if not row.get('_own') and partition_aligned(self.config,row) else BLENDS.index(row['blend']);texture.use(0);pair[index][0].use(1)
                    with self.ctx.scope(framebuffer=pair[1-index][1],enable_only=0):
                        raw.viewport=(0,0,*size);self.vao.render(moderngl.TRIANGLE_STRIP)
                    index=1-index
                return pair[index][0]
            result=children(None,0);final=next(f for t,f in root if t is result);self.ctx.copy_framebuffer(output,final)
        except Exception as exc:self.error='Composition retained where available: '+str(exc)[:180]
        finally:
            raw.blend_func=(moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA)
            raw.viewport=saved_viewport
    def snapshot(self):
        return dict(session=self.session,revision=self.revision,applied_revision=self.applied,pending=self.pending,error=self.error,
            textures=len(self.textures),texture_bytes=sum(getattr(t,'byte_size',t.width*t.height*4) for t in self.textures.values()),
            resident=[list(key) for key in self.textures],
            animated_textures=len(self.animated),animated_texture_bytes=sum(t.width*t.height*4 for t in self.animated.values()),mask_texture_bytes=sum(t.width*t.height for k,t in self.masks.values()),upload_ms=self.upload_ms,composition_target_bytes=sum(t.width*t.height*8 for pair in self.buffers.values() for t,f in pair),
            presentation=(self.config or {}).get('presentation','World + Layers'))
    def close(self):
        with self.condition:
            self.closed=True;self.task=self.result=None
            if self.cancel:self.cancel.set()
            self.condition.notify()
        self.worker.join(timeout=2.)
        self.frames.close()
        for texture in self.animated.values():texture.release()
        self.animated.clear()
        for key,texture in self.masks.values():texture.release()
        self.masks.clear()
        for pair in self.buffers.values():
            for t,f in pair:f.release();t.release()
        self.buffers.clear()
        for texture in self.textures.values():texture.release()
        self.textures.clear()
        for resource in (self.vao,self.program):
            if resource is not None:resource.release()
        self.vao=self.program=None
