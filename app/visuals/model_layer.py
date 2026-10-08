"""Original bounded static glTF 2 / GLB reader and existing-context mesh stage.

Triangles, node TRS/matrices, base-colour factors/textures, metallic/roughness
factors, unlit and OPAQUE/MASK. No skins, animations, morphs, Draco/KTX,
normal maps or material extensions are silently approximated: reject with advice.
"""
from pathlib import Path
import base64,json,struct,math,hashlib
import numpy as np
import moderngl

MAX_BYTES=64*1024*1024
MAX_VERTICES=200000
MAX_PRIMITIVES=64
def quaternion(values):
    x,y,z,w=values;n=math.sqrt(x*x+y*y+z*z+w*w)
    if n<1e-9:raise ValueError('Invalid model quaternion.')
    x,y,z,w=x/n,y/n,z/n,w/n
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),0],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),0],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),0],[0,0,0,1.]])
def load_model(path,cancel=None):
    path=Path(path).resolve();dependencies={};total=0
    def file(p):
        nonlocal total
        p=p.resolve()
        if not p.is_relative_to(path.parent):raise ValueError('Model references must stay inside its asset folder.')
        size=p.stat().st_size
        if total+size>MAX_BYTES:raise ValueError('Model source/dependencies exceed 64 MiB.')
        if cancel is not None and cancel.is_set():raise InterruptedError('Model load cancelled.')
        data=p.read_bytes();total+=len(data);dependencies[str(p)]=hashlib.sha256(data).hexdigest();return data
    data=file(path);binary=None
    if path.suffix.lower()=='.glb':
        if len(data)<20 or struct.unpack_from('<4sII',data)!=(b'glTF',2,len(data)):raise ValueError('Invalid GLB v2 header.')
        offset=12;chunks=[]
        while offset<len(data):
            length,kind=struct.unpack_from('<II',data,offset);offset+=8
            if offset+length>len(data):raise ValueError('Truncated GLB chunk.')
            chunks.append((kind,data[offset:offset+length]));offset+=length
        if not chunks or chunks[0][0]!=0x4e4f534a:raise ValueError('GLB JSON chunk missing.')
        document=json.loads(chunks[0][1]);binary=next((b for k,b in chunks if k==0x004e4942),None)
    else:
        if len(data)>8*1024*1024:raise ValueError('glTF JSON exceeds 8 MiB.')
        document=json.loads(data)
    if document.get('asset',{}).get('version')!='2.0':raise ValueError('Export glTF 2.0 / GLB from Blender or the source tool.')
    if document.get('skins') or document.get('animations'):raise ValueError('This pass supports static glTF. Export a static pose; rig/animation support requires its defined extension.')
    if any(ext!='KHR_materials_unlit' for ext in document.get('extensionsRequired',[])):raise ValueError('Required compressed/material glTF extensions are unsupported; export standard uncompressed glTF.')
    def uri(value):
        nonlocal total
        if value.startswith('data:'):
            if ';base64,' not in value or len(value)>MAX_BYTES*2:raise ValueError('Invalid/oversized model data URI.')
            b=base64.b64decode(value.split(',',1)[1],validate=True);total+=len(b)
            if total>MAX_BYTES:raise ValueError('Model data exceeds 64 MiB.')
            return b
        from urllib.parse import unquote,urlsplit
        if urlsplit(value).scheme or value.startswith(('/','\\')):raise ValueError('Only relative local model dependencies are supported.')
        return file(path.parent/unquote(value))
    buffers=[]
    for b in document.get('buffers',[]):
        raw=uri(b['uri']) if 'uri' in b else binary
        if raw is None or len(raw)<b['byteLength']:raise ValueError('Missing/truncated model buffer.')
        buffers.append(raw)
    def accessor(index):
        a=document['accessors'][index]
        if a.get('sparse') or 'bufferView' not in a:raise ValueError('Sparse/model accessors without buffers are unsupported; export dense geometry.')
        count=a['count'];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}.get(a['type']);dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}.get(a['componentType'])
        if not components or not dtype or type(count) is not int or not 0<count<=MAX_VERTICES*6:raise ValueError('Invalid/oversized mesh accessor.')
        view=document['bufferViews'][a['bufferView']];buffer=buffers[view['buffer']];item=np.dtype(dtype).itemsize;stride=view.get('byteStride',item*components);offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        if stride<item*components or offset+(count-1)*stride+item*components>min(len(buffer),view.get('byteOffset',0)+view['byteLength']):raise ValueError('Model accessor exceeds its buffer view.')
        values=np.ndarray((count,components),dtype=dtype,buffer=buffer,offset=offset,strides=(stride,item)).copy()
        if a.get('normalized'):
            limit=np.iinfo(values.dtype);values=np.maximum(-1.,values.astype('f4')/limit.max)
        if not np.isfinite(values).all():raise ValueError('Non-finite model geometry.')
        return values
    images=[]
    from PySide6.QtGui import QImage,QColorSpace
    for image in document.get('images',[]):
        if len(images)>=8:raise ValueError('At most 8 model textures.')
        if 'uri' in image:raw=uri(image['uri'])
        else:v=document['bufferViews'][image['bufferView']];raw=buffers[v['buffer']][v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
        im=QImage.fromData(raw)
        if im.isNull() or im.width()*im.height()>4*1024*1024 or max(im.width(),im.height())>4096:raise ValueError('Model texture must decode to at most 4 megapixels / 4096 per side.')
        if im.colorSpace().isValid():im=im.convertedToColorSpace(QColorSpace(QColorSpace.SRgb))
        im=im.convertToFormat(QImage.Format_RGBA8888).mirrored(False,True);images.append((im.width(),im.height(),bytes(im.constBits())))
        if sum(w*h*4 for w,h,b in images)>32*1024*1024:raise ValueError('Model decoded textures exceed 32 MiB.')
    primitives=[];vertex_count=0;nodes=document.get('nodes',[])
    if len(nodes)>256:raise ValueError('Model supports at most 256 nodes.')
    def visit(index,parent,seen):
        nonlocal vertex_count
        if index in seen or len(seen)>32:raise ValueError('Cyclic/deep model node tree.')
        n=nodes[index]
        if 'matrix' in n:m=np.asarray(n['matrix'],float).reshape(4,4).T
        else:
            m=quaternion(n.get('rotation',[0,0,0,1]));m[:3,:3]=m[:3,:3]@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
        m=parent@m
        if not np.isfinite(m).all() or abs(np.linalg.det(m))<1e-9:raise ValueError('Invalid/singular model node transform.')
        if 'mesh' in n:
            for primitive in document['meshes'][n['mesh']]['primitives']:
                if len(primitives)>=MAX_PRIMITIVES or primitive.get('mode',4)!=4 or primitive.get('targets') or primitive.get('extensions'):raise ValueError('Use at most 64 uncompressed triangle primitives without morph targets.')
                attrs=primitive['attributes'];positions=accessor(attrs['POSITION']).astype('f4');vertex_count+=len(positions)
                if any(k not in ('POSITION','NORMAL','TEXCOORD_0','TANGENT') for k in attrs):raise ValueError('Export static geometry with POSITION, NORMAL and TEXCOORD_0; vertex colours/additional UVs are not supported.')
                if positions.shape[1]!=3 or vertex_count>MAX_VERTICES:raise ValueError('Model exceeds 200,000 triangle vertices.')
                positions=(np.c_[positions,np.ones(len(positions))]@m.T)[:,:3].astype('f4')
                indices=accessor(primitive['indices']).reshape(-1).astype('u4') if 'indices' in primitive else np.arange(len(positions),dtype='u4')
                if len(indices)%3 or np.max(indices)>=len(positions):raise ValueError('Invalid triangle indices.')
                normals=accessor(attrs['NORMAL']).astype('f4') if 'NORMAL' in attrs else np.zeros_like(positions)
                if 'NORMAL' in attrs:normals=normals@np.linalg.inv(m[:3,:3])
                else:
                    for triangle in indices.reshape(-1,3):
                        a,b,c=positions[triangle];normal=np.cross(b-a,c-a);normals[triangle]+=normal
                normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-9);uv=accessor(attrs['TEXCOORD_0']).astype('f4') if 'TEXCOORD_0' in attrs else np.zeros((len(positions),2),'f4')
                if normals.shape!=positions.shape or uv.shape!=(len(positions),2):raise ValueError('Model normal/UV accessor dimensions do not match geometry.')
                material=document.get('materials',[])[primitive['material']] if 'material' in primitive else {};pbr=material.get('pbrMetallicRoughness',{})
                if any(k in material for k in ('normalTexture','occlusionTexture','emissiveTexture')) or any(material.get('emissiveFactor',[0,0,0])) or pbr.get('metallicRoughnessTexture') or any(k!='KHR_materials_unlit' for k in material.get('extensions',{})):raise ValueError('Use base-colour textures and metallic/roughness factors; extra material maps/extensions are unsupported in this static layer.')
                if material.get('alphaMode','OPAQUE') not in ('OPAQUE','MASK'):raise ValueError('Static model materials support OPAQUE/MASK; export transparent BLEND geometry as an image layer for this pass.')
                factor=pbr.get('baseColorFactor',[1,1,1,1]);texture=None;sampler={}
                if len(factor)!=4 or any(not math.isfinite(v) or not 0<=v<=1 for v in factor):raise ValueError('Invalid model base-colour factor.')
                for k,default in (('metallicFactor',1.),('roughnessFactor',1.)):
                    if not math.isfinite(pbr.get(k,default)) or not 0<=pbr.get(k,default)<=1:raise ValueError('Invalid metallic/roughness factor.')
                if 'baseColorTexture' in pbr:
                    t=pbr['baseColorTexture']
                    if t.get('texCoord',0)!=0 or t.get('extensions'):raise ValueError('Use untransformed TEXCOORD_0 model textures.')
                    tex=document['textures'][t['index']];texture=tex['source'];sampler=document.get('samplers',[])[tex['sampler']] if 'sampler' in tex else {}
                    if not 0<=texture<len(images) or 'TEXCOORD_0' not in attrs:raise ValueError('Base-colour texture requires a valid image and TEXCOORD_0.')
                    if any(sampler.get(k,10497) not in (10497,33071) for k in ('wrapS','wrapT')):raise ValueError('Model textures support repeat/clamp; mirrored-repeat samplers are unsupported.')
                    if sampler.get('magFilter',9729) not in (9728,9729) or sampler.get('minFilter',9729) not in (9728,9729,9984,9985,9986,9987):raise ValueError('Invalid model texture filter.')
                primitives.append(dict(vertices=np.c_[positions,normals,uv].astype('f4'),indices=indices,factor=factor,texture=texture,sampler=sampler,metallic=float(pbr.get('metallicFactor',1.)),roughness=float(pbr.get('roughnessFactor',1.)),unlit='KHR_materials_unlit' in material.get('extensions',{}),alpha=material.get('alphaMode','OPAQUE'),cutoff=float(material.get('alphaCutoff',.5)),double=bool(material.get('doubleSided',False))))
        for child in n.get('children',[]):visit(child,m,seen|{index})
    scenes=document.get('scenes',[])
    if not scenes:raise ValueError('Model has no scene.')
    for index in scenes[document.get('scene',0)].get('nodes',[]):visit(index,np.eye(4),set())
    if not primitives:raise ValueError('Model has no supported triangle geometry.')
    all_positions=np.concatenate([p['vertices'][:,:3] for p in primitives]);minimum=all_positions.min(0);maximum=all_positions.max(0);centre=(minimum+maximum)/2;radius=max(np.max(maximum-minimum)/2,1e-6)
    return dict(primitives=primitives,images=images,centre=centre,radius=radius,metadata=dict(width=1024,height=1024,vertices=vertex_count,primitives=len(primitives),textures=len(images),dependencies=dependencies,supported='Static glTF 2 triangles, node transforms, base-colour texture/factor, metallic/roughness factors, unlit; no rigging/animation/extra maps'))

VERTEX='''#version 330
in vec3 position,normal;in vec2 texcoord;uniform mat4 model;out vec3 n,p;out vec2 uv;
void main(){vec4 v=model*vec4(position,1.);p=v.xyz;n=mat3(model)*normal;uv=vec2(texcoord.x,1.-texcoord.y);gl_Position=vec4(v.x/1.8,v.y/1.8,(v.z+3.)/8.,1.);}'''
FRAGMENT='''#version 330
uniform sampler2D base;uniform vec4 factor;uniform float metallic,roughness,cutoff;uniform int textured,unlit,alpha_mode;
in vec3 n,p;in vec2 uv;out vec4 color;
void main(){vec4 b=factor;if(textured==1){vec4 t=texture(base,uv);b*=vec4(pow(t.rgb,vec3(2.2)),t.a);}
 if(alpha_mode==0)b.a=1.;if(alpha_mode==1&&b.a<cutoff)discard;
 vec3 c=b.rgb;if(unlit==0){vec3 N=normalize(n),L=normalize(vec3(-.4,.7,1.)),V=normalize(vec3(0.,0.,4.)-p),H=normalize(L+V);
 float nl=max(dot(N,L),0.),nv=max(dot(N,V),.001),nh=max(dot(N,H),0.),vh=max(dot(V,H),0.);
 float a=max(.04,roughness*roughness),a2=a*a,d=a2/(3.14159*pow(nh*nh*(a2-1.)+1.,2.));float k=pow(roughness+1.,2.)/8.;float g=nl/(nl*(1.-k)+k)*nv/(nv*(1.-k)+k);
 vec3 f0=mix(vec3(.04),c,metallic),F=f0+(1.-f0)*pow(1.-vh,5.);c=.18*c+nl*((1.-F)*(1.-metallic)*c/3.14159+d*g*F/max(4.*nl*nv,.001));}
 c=pow(max(c,vec3(0.)),vec3(1./2.2));color=vec4(c*b.a,b.a);}'''

class ModelResource:
    def __init__(self,ctx,data):
        self.ctx=ctx;self.data=data;self.resources=[];self.meshes=[];self.textures=[];self.views={};self.program=None
        try:
            self.program=ctx.program(vertex_shader=VERTEX,fragment_shader=FRAGMENT);self.resources.append(self.program)
            for w,h,pixels in data['images']:
                texture=ctx.texture((w,h),4,pixels,alignment=1);self.textures.append(texture);self.resources.append(texture);texture.build_mipmaps();texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
            for p in data['primitives']:
                v=ctx.buffer(p['vertices'].tobytes());self.resources.append(v);i=ctx.buffer(p['indices'].tobytes());self.resources.append(i);vao=ctx.vertex_array(self.program,[(v,'3f 3f 2f','position','normal','texcoord')],i,index_element_size=4);self.resources.append(vao);self.meshes.append((p,vao))
        except Exception:self.close();raise
    @property
    def size(self):return (1024,1024)
    @property
    def width(self):return 1024
    @property
    def height(self):return 1024
    @property
    def byte_size(self):return sum(p['vertices'].nbytes+p['indices'].nbytes for p in self.data['primitives'])+sum(w*h*4*4//3 for w,h,b in self.data['images'])+len(self.views)*1024*1024*4
    def retain(self,identities):
        for identity in list(self.views):
            if identity not in identities:self.views.pop(identity)[1].release()
    def render(self,row):
        identity=row['id'];settings=tuple(row.get('model',{}).get(k,0.) for k in ('yaw','pitch','roll'));old=self.views.get(identity)
        if old and old[0]==settings:return old[1]
        texture=depth=fbo=None
        try:
            texture=self.ctx.texture((1024,1024),4);depth=self.ctx.depth_renderbuffer((1024,1024));fbo=self.ctx.framebuffer(color_attachments=(texture,),depth_attachment=depth)
            m=np.eye(4);m[:3,3]=-self.data['centre'];m[:3,:3]/=self.data['radius'];m[:3,3]/=self.data['radius']
            for axis,angle in zip((1,0,2),settings):
                r=np.eye(4);a=math.radians(angle);i,j=((2,0) if axis==1 else (1,2) if axis==0 else (0,1));r[i,i]=r[j,j]=math.cos(a);r[i,j]=-math.sin(a);r[j,i]=math.sin(a);m=r@m
            with self.ctx.scope(framebuffer=fbo,enable_only=moderngl.DEPTH_TEST|moderngl.BLEND):
                raw=getattr(self.ctx,'raw',self.ctx);raw.viewport=(0,0,1024,1024);raw.blend_func=(moderngl.ONE,moderngl.ONE_MINUS_SRC_ALPHA);fbo.clear(0,0,0,0,depth=1.);self.program['model'].write(m.T.astype('f4').tobytes());self.program['base'].value=0
                for p,vao in self.meshes:
                    if p['double']:raw.disable(moderngl.CULL_FACE)
                    else:raw.enable(moderngl.CULL_FACE);raw.front_face='ccw';raw.cull_face='back'
                    self.program['factor'].value=tuple(p['factor']);self.program['metallic'].value=p['metallic'];self.program['roughness'].value=p['roughness'];self.program['unlit'].value=int(p['unlit']);self.program['textured'].value=int(p['texture'] is not None);self.program['alpha_mode'].value={'OPAQUE':0,'MASK':1,'BLEND':2}[p['alpha']];self.program['cutoff'].value=p['cutoff']
                    if p['texture'] is not None:
                        t=self.textures[p['texture']];sampler=p['sampler'];t.repeat_x=sampler.get('wrapS',10497)==10497;t.repeat_y=sampler.get('wrapT',10497)==10497;t.filter=(sampler.get('minFilter',9729),sampler.get('magFilter',9729));t.use(0)
                    vao.render(moderngl.TRIANGLES)
            if old:old[1].release()
            self.views[identity]=(settings,texture);return texture
        except Exception:
            if texture is not None:texture.release()
            raise
        finally:
            if fbo is not None:fbo.release()
            if depth is not None:depth.release()
    def release(self):self.close()
    def close(self):
        for _,t in self.views.values():t.release()
        self.views.clear()
        for resource in reversed(self.resources):resource.release()
        self.resources=[]
