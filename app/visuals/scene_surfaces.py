"""Bounded full-resolution Cavern/Citadel surface buffers owned by Renderer.

Rasterizes their authored surfaces; the existing dream shader owns material,
lighting, audio presentation and overlays. No separate playback/scene engine.
"""
import math
from functools import lru_cache
import numpy as np
import moderngl
from concurrent.futures import Future
from collections import OrderedDict
import subprocess,sys,json,threading,os
from pathlib import Path
from mineral_resonance import formation,cavern_axis,cavern_path

VERTEX='''#version 330
in vec3 in_position,in_normal;
in vec4 in_motion;
in float in_kind,in_tag;
uniform vec3 u_eye,u_forward,u_right,u_up;
uniform vec2 u_size,u_range;
uniform float u_focal,u_bank,u_scene,u_origin;
uniform vec4 u_mineral,u_tower;
uniform float u_amount,u_time;
out vec3 point,normal;
flat out float kind;
vec3 ring_pose(vec3 q,float tag){
 float survey=u_tower.z*.42+u_time*.055,tilt=.28*sin(survey*.7)+.10*u_tower.x;
 if(tag>2.5){q.yz=mat2(.82,-.57,.57,.82)*q.yz;q.xz=mat2(cos(survey),-sin(survey),sin(survey),cos(survey))*q.xz;}
 q.yz=mat2(cos(tilt),-sin(tilt),sin(tilt),cos(tilt))*q.yz;return q;
}
void main(){
 vec3 world=in_position;normal=in_normal;kind=in_kind;
 if(u_scene<.5){
  world.z+=u_origin;
  if(in_tag>.5){float life=(u_mineral.x*.62+sin(u_mineral.y*1.7+in_motion.w*9.)*.028*u_mineral.z)*u_amount;
   world.xz-=in_motion.xy*life*in_motion.z;normal.y+=dot(in_motion.xy,normal.xz)*life;}
 }else if(in_tag>1.5){vec3 center=vec3(0.,1.74,.13);world=center+ring_pose(world-center,in_tag);normal=ring_pose(normal,in_tag);}
 point=world-u_eye;vec3 view=vec3(dot(point,u_right),dot(point,u_up),dot(point,u_forward));
 vec2 projected=view.xy/u_focal;
 projected=mat2(cos(u_bank),-sin(u_bank),sin(u_bank),cos(u_bank))*projected;
 projected.y+=u_scene>.5?.09*view.z:0.;
 float near=u_range.x,far=u_range.y;
 gl_Position=vec4(projected.x*2.*u_size.y/u_size.x,projected.y*2.,((far+near)*view.z-2.*far*near)/(far-near),view.z);
}
'''
FRAGMENT='''#version 330
in vec3 point,normal;
flat in float kind;
uniform float u_scene;
layout(location=0) out vec4 position;
layout(location=1) out vec4 orientation;
void main(){float distance=length(point);if(distance>(u_scene<.5?55.:4.9))discard;position=vec4(point,kind);orientation=vec4(normalize(normal),1.);}
'''

def norm(v):
 a=np.asarray(v,dtype='f8');return a/max(1e-12,np.linalg.norm(a))

def citadel_focal(eye,forward,up):
 # Tangent to the two rings' unchanged .34m bounding sphere. Widen only
 # enough for a .02 screen-height headroom, continuously through orbit.
 center=np.array((0.,1.74,.13))-eye;y=float(np.dot(center,up));z=float(np.dot(center,forward));r=.34
 slope=(y*z+r*math.sqrt(max(0.,z*z+y*y-r*r)))/max(1e-6,z*z-r*r)
 return max(1.13,slope/(.48-.09))

class Mesh:
 def __init__(self):self.rows=[];self.chunks=[]
 def poly(self,points,normal=None,kind=1.,motion=None,tag=0.):
  points=np.asarray(points,dtype='f8')
  if len(points)<3:return
  n=norm(np.cross(points[1]-points[0],points[2]-points[0])) if normal is None else np.asarray(normal,dtype='f8')
  moves=np.zeros((len(points),4)) if motion is None else np.asarray(motion)
  if moves.ndim==1:moves=np.tile(moves,(len(points),1))
  for i in range(1,len(points)-1):
   for j in (0,i,i+1):self.rows.append((*points[j],*n,*moves[j],kind,tag))
 def data(self):return np.concatenate([np.asarray(self.rows,dtype='f4').reshape(-1,12),*self.chunks])
 def grid(self,points,normals,kind,tag=0.,motion=None):
  h,w=points.shape[:2];ids=np.arange(h*w).reshape(h,w);a=ids[:-1,:-1].ravel();b=ids[:-1,1:].ravel();c=ids[1:,1:].ravel();d=ids[1:,:-1].ravel();indices=np.stack((a,b,c,a,c,d),axis=1).ravel()
  data=np.zeros((len(indices),12),dtype='f4');data[:,:3]=points.reshape(-1,3)[indices];data[:,3:6]=normals.reshape(-1,3)[indices];data[:,10]=kind;data[:,11]=tag
  if motion is not None:data[:,6:10]=motion.reshape(-1,4)[indices]
  self.chunks.append(data)
 def box(self,center,half,kind=1.,angle=0.):
  c=np.asarray(center);h=np.asarray(half);rot=np.array(((math.cos(angle),0,-math.sin(angle)),(0,1,0),(math.sin(angle),0,math.cos(angle))))
  for axis in range(3):
   a,b=[v for v in range(3) if v!=axis]
   for sign in (-1,1):
    points=[]
    for x,y in ((-1,-1),(1,-1),(1,1),(-1,1)):
     q=np.zeros(3);q[axis]=sign*h[axis];q[a]=x*h[a];q[b]=y*h[b];points.append(c+rot@q)
    n=np.zeros(3);n[axis]=sign;self.poly(points,rot@n,kind)
 def cylinder(self,center,radius,low,high,kind=1.,segments=48,top_radius=None,inner=None):
  cx,cz=center;rt=radius if top_radius is None else top_radius
  for i in range(segments):
   a=i*math.tau/segments;b=(i+1)*math.tau/segments
   q=[(cx+radius*math.cos(a),low,cz+radius*math.sin(a)),(cx+radius*math.cos(b),low,cz+radius*math.sin(b)),(cx+rt*math.cos(b),high,cz+rt*math.sin(b)),(cx+rt*math.cos(a),high,cz+rt*math.sin(a))]
   self.poly(q,norm((math.cos((a+b)/2),(radius-rt)/max(.001,high-low),math.sin((a+b)/2))),kind)
   self.poly([q[0],q[1],(cx,low,cz)],(0,-1,0),kind)
   self.poly([q[2],q[3],(cx,high,cz)],(0,1,0),kind)
   if inner is not None:
    innerA=(cx+inner*math.cos(a),high,cz+inner*math.sin(a));innerB=(cx+inner*math.cos(b),high,cz+inner*math.sin(b))
    self.poly([q[3],q[2],innerB,innerA],(0,1,0),kind)
 def torus(self,center,major,minor,tag,plane='xz'):
  for i in range(64):
   for j in range(10):
    def point(ii,jj):
     a=ii*math.tau/64;b=jj*math.tau/10
     q=np.array(((major+minor*math.cos(b))*math.cos(a),minor*math.sin(b),(major+minor*math.cos(b))*math.sin(a)))
     n=np.array((math.cos(b)*math.cos(a),math.sin(b),math.cos(b)*math.sin(a)))
     if plane=='xy':q=q[[0,2,1]];n=n[[0,2,1]]
     return np.asarray(center)+q,n
    values=[point(i,j),point(i+1,j),point(i+1,j+1),point(i,j+1)]
    # Smooth vertex normals for these small tubes.
    for indices in ((0,1,2),(0,2,3)):
     for k in indices:
      p,n=values[k];self.rows.append((*p,*n,0.,0.,0.,0.,2.,tag))

@lru_cache(maxsize=1)
def citadel_mesh():
 m=Mesh();m.box((0,.25,.48),(.5,.25,.065));m.box((-.48,.25,0),(.065,.25,.5));m.box((.48,.25,0),(.065,.25,.5))
 m.box((-.31,.25,-.48),(.19,.25,.065));m.box((.31,.25,-.48),(.19,.25,.065));m.box((0,.45,-.48),(.12,.05,.065))
 # Arch voussoirs around the actual doorway, with a fitted recessed gate.
 for i in range(16):
  a=i*math.pi/16;b=(i+1)*math.pi/16
  for z in (-.545,-.415):m.poly([(math.cos(a)*.12,.28+math.sin(a)*.12,z),(math.cos(b)*.12,.28+math.sin(b)*.12,z),(math.cos(b)*.17,.28+math.sin(b)*.17,z),(math.cos(a)*.17,.28+math.sin(a)*.17,z)],(0,0,-1 if z<-.48 else 1))
 m.box((0,.18,-.515),(.105,.18,.018),3.)
 for i in range(7):
  center=((-1 if i%2==0 else 1)*.48,(-1 if i<2 else 1)*.48) if i<4 else ((-.23 if i==4 else .23),-.49) if i<6 else (0.,.13)
  h=.98 if i==6 else .78 if i<2 else .64 if i<4 else .84;radius=.205 if i==6 else .13 if i<2 else .11
  m.cylinder(center,radius,0,h)
  if i<6:
   m.cylinder(center,radius+.022,h-.035,h+.035,segments=48)
   for j in range(10):
    a=j*math.tau/10;m.box((center[0]+math.cos(a)*radius,h+.065,center[1]+math.sin(a)*radius),(.028,.03,.030),angle=a)
  if i<2:m.cylinder(center,.15,h,h+.24,2.,top_radius=0.)
  if i==6:
   m.cylinder(center,.235,h,h+.40,2.,top_radius=0.)
   m.torus((0.,h+.76,.13),.315,.014,2.);m.torus((0.,h+.76,.13),.31,.012,3.,'xy')
 for x in (-.255,.255):m.box((x,.62,.13),(.024,.31,.038),angle=0.)
 for i in range(9):m.box((-.44+i*.11,.535,-.48),(.032,.04,.07))
 # The accepted tapered rocky island; fine material/weathering remains in dream.
 for j in range(12):
  y=-.50+j*.52/12;yy=-.50+(j+1)*.52/12
  for i in range(96):
   a=i*math.tau/96;b=(i+1)*math.tau/96
   def point(v,angle):
    radius=.94+v*.95
    for _ in range(3):
     x=radius*math.cos(angle);z=radius*math.sin(angle);weight=1. if v<=-.15 else max(0.,min(1.,(-.01-v)/.14));weight=weight*weight*(3-2*weight)
     noise=(.025*math.sin(x*19)*math.sin(z*17)+.034*math.sin(angle*7+v*8))*weight;radius=.94+v*.95-noise
    return (radius*math.cos(angle),v,radius*math.sin(angle))
   points=[point(y,a),point(y,b),point(yy,b),point(yy,a)];m.poly(points,norm((math.cos((a+b)/2),-.95,math.sin((a+b)/2))),4.)
 m.cylinder((0,0),.959,.015,.02,4.,segments=96)
 return m.data()

def clip_face(points,extent):
 normal=np.array((.22,1.,.13));result=[];crossings=[]
 for a,b in zip(points,points[1:]+points[:1]):
  fa=float(np.dot(a,normal)-extent);fb=float(np.dot(b,normal)-extent)
  if fa<=0:result.append(a)
  if (fa<=0)!=(fb<=0):q=a+(b-a)*fa/(fa-fb);result.append(q);crossings.append(q)
 return result,crossings

def specimen(m,cell,desc,foot,rot,crystal):
 seed=desc[0];height,radius,individual,spread=crystal
 if individual<=.18:return
 axisX=np.array((rot[0],-rot[1]));axisZ=np.array((rot[1],rot[0]));direction=axisX*rot[1]-axisZ*rot[0]
 center=(np.array(cell)+.5)*2.8+np.array(rot[:2])*spread+np.array(foot[:2]);lean=np.array(rot[2:])
 def transform(q):
  xz=axisX*(q[0]-lean[0]*q[1])+axisZ*(q[2]-lean[1]*q[1])+center
  return (xz[0],q[1]-2.5,xz[1])
 def polygon(points,n):
  n=np.asarray(n);horizontal=axisX*n[0]+axisZ*n[2];normal=(horizontal[0],n[1]+np.dot(lean,n[[0,2]]),horizontal[1])
  m.poly([transform(q) for q in points],normal,2.5 if seed<.27 else 1.+seed,[(direction[0],direction[1],q[1],seed) for q in points],1.)
 if seed<.27:
  y=np.linspace(0,height,13)[:,None];angle=np.linspace(0,math.tau,17)[None,:];co=np.broadcast_to(np.cos(angle),(13,17));si=np.broadcast_to(np.sin(angle),(13,17));yy=np.broadcast_to(y,(13,17))
  rad=np.maximum(0.,(.22+.43*individual)*(1-y/height)**1.4-.012*np.sin(y*18+seed*math.tau));derivative=-1.4*(.22+.43*individual)/height*(1-y/height)**.4-.216*np.cos(y*18+seed*math.tau)
  x=rad*co-lean[0]*yy;z=rad*si-lean[1]*yy;points=np.stack((axisX[0]*x+axisZ[0]*z+center[0],yy-2.5,axisX[1]*x+axisZ[1]*z+center[1]),axis=-1)
  horizontalX=axisX[0]*co+axisZ[0]*si;horizontalZ=axisX[1]*co+axisZ[1]*si;ny=np.broadcast_to(-derivative,(13,17))+lean[0]*co+lean[1]*si;normals=np.stack((horizontalX,ny,horizontalZ),axis=-1)
  motion=np.stack((np.full_like(yy,direction[0]),np.full_like(yy,direction[1]),yy,np.full_like(yy,seed)),axis=-1);m.grid(points,normals,2.5,1.,motion)
  return
 sides=4 if seed>.66 else 6;cap=(.10+.18*individual) if seed>.66 else (.32+.42*individual);broken=.12+.24*((individual*7.1)%1) if individual>.62 else .015
 angles=[i*math.tau/sides+(math.pi/4 if sides==4 else 0) for i in range(sides)];rad=radius/math.cos(math.pi/sides)
 base=[np.array((rad*math.cos(a),0.,rad*math.sin(a))) for a in angles];shoulder=[q+np.array((0,height-cap,0)) for q in base];tip=np.array((0.,height,0.));faces=[]
 faces.append((base,np.array((0,-1,0))))
 for i in range(sides):
  j=(i+1)%sides;a=(angles[i]+math.pi/sides);n=np.array((math.cos(a),0,math.sin(a)))
  faces.extend([( [base[i],base[j],shoulder[j],shoulder[i]],n),([shoulder[i],shoulder[j],tip],n+np.array((0,radius/cap,0)))])
 cuts=[]
 for points,n in faces:
  points,crossings=clip_face(points,height-broken);cuts.extend(crossings)
  if len(points)>=3:polygon(points,n)
 if cuts:
  unique={tuple(np.round(q,8)):q for q in cuts};points=list(unique.values());c=np.mean(points,axis=0);points.sort(key=lambda q:math.atan2(q[2]-c[2],q[0]-c[0]));polygon(points,(.22,1,.13))

@lru_cache(maxsize=64)
def cavern_row(z):
 m=Mesh();offset=z*2.8
 # Inner chamber shell, smooth rounded normals. World sampling stays fixed on rows.
 v=np.linspace(offset,offset+2.8,5)[:,None];angle=np.linspace(0,math.tau,65)[None,:];axis=np.array([cavern_axis(z) for z in v[:,0]])[:,None];slope=np.array([cavern_path(z)[1] for z in v[:,0]])[:,None];radius=np.full((5,65),4.4)
 for _ in range(5):
  x=axis+radius/.8*np.cos(angle);y=.6+radius*np.sin(angle);radius=4.4+.18*np.sin(v*.7+y*1.6)*np.sin(x*1.7)
 x=axis+radius/.8*np.cos(angle);y=.6+radius*np.sin(angle);zz=np.broadcast_to(v,x.shape);points=np.stack((x,y,zz),axis=-1)
 phase=v*.7+y*1.6;common=np.cos(phase)*np.sin(x*1.7);nx=-(x-axis)*.64/radius+.306*np.sin(phase)*np.cos(x*1.7);ny=-(y-.6)/radius+.288*common;nz=(x-axis)*.64*slope/radius+.126*common
 m.grid(points,np.stack((nx,ny,nz),axis=-1),0.)
 for j in range(4):
  a=offset+j*.7;b=offset+(j+1)*.7;xa=cavern_axis(a);xb=cavern_axis(b);m.poly([(xa-5.6,-2.5,a),(xa+5.6,-2.5,a),(xb+5.6,-2.5,b),(xb-5.6,-2.5,b)],(0,1,0),0.)
 for x in range(-4,4):
  cell=(x,z);values=formation(x,z);desc,foot=values[:2]
  # Rooted hanging mineral cones; retains every authored seed and proportion.
  if desc[0]>.16:
   down=np.linspace(0,desc[1],11)[:,None];angle=np.linspace(0,math.tau,17)[None,:];co=np.broadcast_to(np.cos(angle),(11,17));si=np.broadcast_to(np.sin(angle),(11,17));yy=np.broadcast_to(down,(11,17));rad=desc[2]*(1-down/desc[1])**1.5;derivative=-1.5*desc[2]/desc[1]*(1-down/desc[1])**.5
   points=np.stack(((x+.5)*2.8+foot[0]-foot[2]*yy+rad*co,desc[3]-yy,(z+.5)*2.8+foot[1]-foot[3]*yy+rad*si),axis=-1);normals=np.stack((co,np.broadcast_to(derivative,(11,17))-foot[2]*co-foot[3]*si,si),axis=-1);m.grid(points,normals,2.5)
  if abs((x+.5)*2.8-cavern_axis((z+.5)*2.8))>1.1:
   for i in range(3):specimen(m,cell,desc,foot,values[2+i*2],values[3+i*2])
 data=m.data();data[:,2]-=offset;return data

class SurfaceRows:
 """One owned CPU helper; two requested rows, no GL context or audio access."""
 def __init__(self):
  self.futures={};self.lock=threading.Lock()
  # Run the installed base interpreter directly, using this environment's
  # existing import paths. On Windows the venv executable is a redirector;
  # direct ownership ensures timeout cleanup terminates the actual helper.
  env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(str(p) for p in sys.path)
  self.process=subprocess.Popen([getattr(sys,'_base_executable',sys.executable),'-B',str(Path(__file__).resolve()),'--surface-rows'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
  self.reader=threading.Thread(target=self.read,name='ZeraWave surface rows',daemon=True);self.reader.start()
 def read(self):
  try:
   while True:
    line=self.process.stdout.readline()
    if not line:break
    z,n=json.loads(line);data=bytearray()
    while len(data)<n:
     part=self.process.stdout.read(n-len(data))
     if not part:raise RuntimeError('Surface cache helper ended during a row')
     data.extend(part)
    with self.lock:future=self.futures.pop(z)
    future.set_result(np.frombuffer(data,dtype='f4').reshape(-1,12))
  finally:
   with self.lock:
    for f in self.futures.values():f.set_exception(RuntimeError('Owned surface cache helper ended'))
    self.futures.clear()
 def submit(self,z):
  f=Future()
  with self.lock:self.futures[z]=f
  self.process.stdin.write((json.dumps(z)+'\n').encode());self.process.stdin.flush();return f
 def shutdown(self):
  try:self.process.stdin.close();self.process.wait(2.)
  except (OSError,subprocess.TimeoutExpired):self.process.terminate();self.process.wait(2.)
  self.reader.join(2.);self.process.stdout.close()
  if self.reader.is_alive():raise RuntimeError('Owned surface cache reader did not stop')

def surface_rows_worker():
 for line in sys.stdin.buffer:
  z=json.loads(line);a=cavern_row(z);sys.stdout.buffer.write((json.dumps([z,a.nbytes])+'\n').encode());sys.stdout.buffer.write(a.tobytes());sys.stdout.buffer.flush()

class SurfaceStage:
 def __init__(self,ctx,cavern=True):
  self.ctx=ctx;self.program=ctx.program(vertex_shader=VERTEX,fragment_shader=FRAGMENT);self.targets={};self.size=None;self.cavern_origin=None;self.buffers={};self.vaos={};self.metrics={}
  self.pending={};self.ready=OrderedDict();self.row_buffers={};self.row_vaos={};self.row_counts={};self.worker=None
  self.upload('citadel',citadel_mesh())
  if cavern:self.prepare_cavern(0.);self.warm_rows(0.)
 def upload(self,name,data):
  if name in self.vaos:self.vaos.pop(name).release();self.buffers.pop(name).release()
  buffer=self.ctx.buffer(data.tobytes());self.buffers[name]=buffer;self.vaos[name]=self.ctx.vertex_array(self.program,[(buffer,'3f 3f 4f 1f 1f','in_position','in_normal','in_motion','in_kind','in_tag')]);self.metrics[name+'_vertices']=len(data)
 def prepare_cavern(self,travel):
  origin=math.floor(travel/2.8)-2
  if origin==self.cavern_origin:return
  for z in range(origin,origin+24):
   if z in self.row_buffers:continue
   a=self.ready.pop(z,None)
   if a is None:a=self.pending.pop(z).result() if z in self.pending else cavern_row(z)
   retired=next((key for key in self.row_buffers if not origin<=key<origin+24),None)
   if retired is not None:
    buffer=self.row_buffers.pop(retired);vao=self.row_vaos.pop(retired);self.row_counts.pop(retired);buffer.orphan(a.nbytes);buffer.write(a.tobytes())
   else:
    buffer=self.ctx.buffer(a.tobytes());vao=self.ctx.vertex_array(self.program,[(buffer,'3f 3f 4f 1f 1f','in_position','in_normal','in_motion','in_kind','in_tag')])
   self.row_buffers[z]=buffer;self.row_vaos[z]=vao;self.row_counts[z]=len(a)
  self.cavern_origin=origin;self.metrics['cavern_vertices']=sum(self.row_counts.values());self.metrics['cavern_gpu_rows']=len(self.row_buffers)
 def warm_rows(self,travel):
  if self.worker is None:self.worker=SurfaceRows()
  origin=math.floor(travel/2.8)-2
  for z,future in list(self.pending.items()):
   if future.done():self.ready[z]=future.result();del self.pending[z]
  self.ready=OrderedDict((z,a) for z,a in self.ready.items() if origin<=z<origin+32)
  for z in range(origin,origin+26):
   if len(self.pending)>=2:break
   if z not in self.row_buffers and z not in self.ready and z not in self.pending:self.pending[z]=self.worker.submit(z)
  self.metrics['row_cache_max']=64;self.metrics['pending_rows']=len(self.pending);self.metrics['ready_rows']=len(self.ready);self.metrics['cache_worker_pid']=self.worker.process.pid
 def resize(self,size):
  if size==self.size:return
  for items in self.targets.values():
   for item in items:item.release()
  self.targets={};self.size=size
  self.metrics['surface_bytes']=0
 def park_targets(self):
  for items in self.targets.values():
   for item in items:item.release()
  self.targets={};self.metrics['surface_bytes']=0
 def target(self,name):
  if name not in self.targets:
   size=self.size;point=self.ctx.texture(size,4,dtype='f4');normal=self.ctx.texture(size,4,dtype='f2');depth=self.ctx.depth_renderbuffer(size)
   for texture in (point,normal):texture.filter=(moderngl.NEAREST,moderngl.NEAREST);texture.repeat_x=texture.repeat_y=False
   fbo=self.ctx.framebuffer(color_attachments=(point,normal),depth_attachment=depth);self.targets[name]=(fbo,point,normal,depth)
   self.metrics['surface_bytes']=size[0]*size[1]*28*len(self.targets)
  return self.targets[name]
 def draw(self,renderer,size,cavern,citadel,inputs=None):
  self.resize(size);self.ctx.enable(moderngl.DEPTH_TEST);self.ctx.disable(moderngl.CULL_FACE|moderngl.BLEND)
  p=self.program;time=renderer.flow_time;clock=renderer.last_render_time;travel=(time*3+clock*.035)*1.35
  # Renderer already owns these values; avoid synchronous GL uniform readback.
  # Optional fallback keeps standalone surface tools compatible.
  mineral,tower,amount=inputs if inputs is not None else (renderer.program['u_mineral_motion'].value,renderer.program['u_tower_motion'].value,renderer.program['u_mineral_amount'].value)
  p['u_size'].value=size;p['u_mineral'].value=mineral;p['u_tower'].value=tower;p['u_amount'].value=amount;p['u_time'].value=time
  for name,present in (('cavern',cavern),('citadel',citadel)):
   if not present:
    for item in self.targets.pop(name,()):item.release()
    continue
   if name=='cavern':
    flux=renderer.audio_input(26,'camera','flux',renderer.parameters.flux) if getattr(renderer,'studio_audio',None) is not None else renderer.parameters.flux
    self.prepare_cavern(travel);eye=np.array((cavern_axis(travel),.1,travel));forward=norm((cavern_path(travel)[1],.03,1));right=norm(np.cross((0,1,0),forward));up=np.cross(forward,right);focal=1.45;bank=.045*cavern_path(travel)[1]*(1+flux*1.6);limits=(.04,55.);origin=self.cavern_origin*2.8
   else:
    orbit=.35+time*.015+clock*.0035;approach=2.8+.20*math.sin(clock*.055);eye=np.array((approach*math.sin(orbit),1.35+.08*math.sin((time*.22+clock*.025)*.23),-approach*math.cos(orbit)));forward=norm(np.array((0,.54,0))-eye);right=norm(np.cross(forward,(0,1,0)));up=np.cross(right,forward);focal=citadel_focal(eye,forward,up);renderer.program['u_citadel_focal'].value=focal;bank=0.;limits=(1.2,4.9);origin=0.
   for k,v in {'u_eye':tuple(eye),'u_forward':tuple(forward),'u_right':tuple(right),'u_up':tuple(up),'u_focal':focal,'u_bank':bank,'u_range':limits,'u_scene':float(name=='citadel'),'u_origin':origin}.items():p[k].value=v
   fbo,point,normal,depth=self.target(name);fbo.use();fbo.clear(depth=1.);self.ctx.viewport=(0,0,*size)
   if name=='cavern':
    for z in range(self.cavern_origin,self.cavern_origin+24):p['u_origin'].value=z*2.8;self.row_vaos[z].render(moderngl.TRIANGLES,vertices=self.row_counts[z])
   else:self.vaos[name].render(moderngl.TRIANGLES)
  self.ctx.disable(moderngl.DEPTH_TEST);self.ctx.screen.use();self.ctx.viewport=(0,0,*size)
  for name,unit in (('cavern',9),('citadel',11)):
   if name not in self.targets:continue
   _,point,normal,_=self.targets[name];point.use(unit);normal.use(unit+1);renderer.program['u_'+name+'_surface'].value=unit;renderer.program['u_'+name+'_normal'].value=unit+1
  renderer.program['u_cavern_surface_on'].value=int(cavern);renderer.program['u_citadel_surface_on'].value=int(citadel)
  self.metrics['surface_bytes']=size[0]*size[1]*28*len(self.targets)
 def release(self):
  if self.worker is not None:self.worker.shutdown();self.worker=None
  self.pending={};self.ready=OrderedDict()
  for items in self.targets.values():
   for item in items:item.release()
  for item in self.vaos.values():item.release()
  for item in self.buffers.values():item.release()
  for item in self.row_vaos.values():item.release()
  for item in self.row_buffers.values():item.release()
  self.row_vaos={};self.row_buffers={};self.row_counts={}
  self.program.release();self.targets={};self.vaos={};self.buffers={};self.size=None

if __name__=='__main__' and '--surface-rows' in sys.argv:surface_rows_worker()
