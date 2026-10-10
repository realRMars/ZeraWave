"""Captured-path batch parity and input-gesture boundaries, standalone."""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import sys,json,ctypes as C,math,time
import numpy as np
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage,QColor
from composition import new_layer,defaults,transform
from native_raster import backend
from artwork import brush_stroke,constrained_edit,edit_coverage
from raster_edit import segment,path
from stroke_input import MouseHistory
from cpu_projection import Projection
from artwork_export import FrozenCanvas
def raw(im):
 q=im.convertToFormat(QImage.Format_ARGB32_Premultiplied);return bytes(q.constBits())
def run(out,baseline):
 out.mkdir(parents=True,exist_ok=False);app=QApplication([]);checks=[];samples=[]
 image=QImage(128,96,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(50,100,170,150));row=new_layer('Image');row['crop']=[.07,.07,.93,.93];row['masks']=[dict(mode='Keep',enabled=True,shape='Rectangle',points=[[.1,.1],[.9,.1],[.9,.9],[.1,.9]])]
 paths={
  'circle':[(64+30*math.cos(i*math.tau/63),48+30*math.sin(i*math.tau/63)) for i in range(64)],
  'corner-reversal':[(15,15),(100,15),(100,70),(80,70),(100,70),(30,30)],
  'straight':[(10,40),(30,40),(70,40),(110,40)]}
 for tool in ('Brush','Pencil','Eraser'):
  for label,vertices in paths.items():
   brush=dict(size=4.,opacity=.6,flow=.5,hardness=.8,shape='Round' if tool!='Pencil' else 'Square');base=backend().storage().from_image(image) if backend().available else image
   work=dict(image=base.private_view() if backend().available else base.copy(),base=base,preview=base.private_view() if backend().available else base.copy(),target=row,selection=None,brush=brush,color=QColor('#f6c490'),tool=tool,last=vertices[0])
   if backend().available:
    seq=deepcopy({k:v for k,v in work.items() if k not in ('image','base','preview')});seq.update(image=base.private_view(),base=base,preview=base.private_view());segment(seq,vertices[0]);segment(work,vertices[0]);begin=time.perf_counter()
    for vertex in vertices[1:]:segment(seq,vertex);seq['last']=vertex
    sequential_ms=(time.perf_counter()-begin)*1000;begin=time.perf_counter();path(work,vertices[1:]);batched_ms=(time.perf_counter()-begin)*1000;assert raw(seq['preview'])==raw(work['preview']), (tool,label);samples.append(dict(tool=tool,path=label,captured_vertices=len(vertices),sequential_ms=sequential_ms,batched_ms=batched_ms))
   else:
    full=base.copy();brush_stroke(full,vertices[0],vertices[0],brush,work['color'],tool)
    for a,b in zip(vertices,vertices[1:]):brush_stroke(full,a,b,brush,work['color'],tool)
    preview=constrained_edit(base,full,row,opacity=brush['opacity']);assert preview.width()==128
   checks.append(tool+' '+label+' pixel policy / corners / reversal')
 # Size-one clicks are source cells, not a degenerate Qt ellipse.
 for shape in ('Round','Square'):
  for flow in (1.,.5):
   cell_image=QImage(7,5,QImage.Format_ARGB32_Premultiplied);cell_image.fill(0)
   brush_stroke(cell_image,(.5,.5),(.5,.5),dict(size=1.,shape=shape,flow=flow),QColor('#c9284b'),'Pencil')
   a=np.frombuffer(cell_image.constBits(),np.uint8).reshape(5,7,4)
   assert np.argwhere(a[:,:,3]>0).tolist()==[[0,0]]
   assert cell_image.pixelColor(0,0).alpha()==(255 if flow==1. else 128)
  checks.append(shape+' size-one Pencil exactly one pixel; opaque and unchanged half-flow meaning')
 # Simulate the actual bounded WinAPI return shape, not cursor motion invention.
 class Move(C.Structure):_fields_=[('x',C.c_int),('y',C.c_int),('time',C.c_ulong),('extra',C.c_size_t)]
 class Point(C.Structure):_fields_=[('x',C.c_long),('y',C.c_long)]
 class API:
  records=[(130,3,3),(120,2,2),(110,1,1),(100,0,0),(90,-1,-1)]
  def GetSystemMetrics(self,n):return {76:0,77:0,78:1920,79:1080}[n]
  def ClientToScreen(self,h,p):return True
  def ScreenToClient(self,h,p):return True
  def GetMouseMovePointsEx(self,size,query,buf,count,res):
   for i,(t,x,y) in enumerate(self.records[:count]):buf[i]=Move(x,y,t,0)
   return min(len(self.records),count)
 def event(t,x,y):return SimpleNamespace(timestamp=lambda:t,spontaneous=lambda:True,position=lambda:QPointF(x,y))
 c=SimpleNamespace(devicePixelRatioF=lambda:1.,winId=lambda:0);history=MouseHistory(c,SimpleNamespace(timestamp=lambda:100,spontaneous=lambda:False,position=lambda:QPointF(0,0)));history.api=API();history.Move=Move;history.Point=Point;history.hwnd=0;history.key=(100,0,0)
 points,_,gap=history.samples(event(130,3,3));assert [(p.x(),p.y()) for p in points]==[(1,1),(2,2),(3,3)] and not gap
 assert history.samples(event(130,3,3))[0]==[]
 history.api.records=[(150,1,1),(140,2,2),(130,3,3),(120,2,2)];points,_,_=history.samples(event(150,1,1));assert [(p.x(),p.y()) for p in points]==[(2,2),(1,1)];checks.append('WinAPI-shape gesture window ordering, exact duplicate dedup and reversal retained')
 history.last=QPointF(0,0);history.stamp=history.start=100;history.api.records=[(90,0,0)];history.pin_boundary();assert history.key==(90,0,0)
 history.api.records=[(100,3,3),(100,2,2),(100,1,1),(90,0,0),(80,-1,-1)];points,_,_=history.samples(event(100,3,3));assert [(p.x(),p.y()) for p in points]==[(1,1),(2,2),(3,3)];assert history.samples(event(100,3,3))[0]==[];checks.append('press pins actual preceding OS record; equal-millisecond captured moves preserved once')
 # Compare exact Qt projection after the prefix optimization, including changes
 # to earlier siblings and nested masks/blends. Baseline class is frozen source.
 import importlib.util
 spec=importlib.util.spec_from_file_location('baseline_projection',baseline/'app/visuals/cpu_projection.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 scene=defaults();scene['canvas']=[128,96];ims={};meta={}
 for i in range(8):
  r=new_layer('Image',asset=str(i),name=str(i));r['order']=i;r['fit']='Stretch';r['opacity']=.2+i*.08;r['transform']=transform((i%3-1)*.03,0,.85,.9,i*7);r['blend']=('Normal','Multiply','Screen','Add','Difference')[i%5];r['blend_strength']=.35 if i%2 else 1;scene['layers'].append(r);im=image.copy();im.fill(QColor(10+i*28,150-i*12,60+i*15,120+i*13));ims[r['id']]=backend().storage().from_image(im) if backend().available else im;meta[r['id']]=dict(width=128,height=96)
 adapter=FrozenCanvas(scene,ims,meta,(128,96));projection=__import__('numpy').array([[128,0,64],[0,96,48],[0,0,1.]])
 optimized=Projection();old=module.Projection()
 if backend().available:
  for changed in (None,7,7,2,0,6):
   if changed is not None:
    identity=scene['layers'][changed]['id'];part=QImage(4,4,QImage.Format_ARGB32_Premultiplied);part.fill(QColor(245,80+changed,40,175));ims[identity]=ims[identity].patch((30+changed,40,4,4),part)
   assert raw(optimized.render(adapter,128,96,projection))==raw(old.render(adapter,128,96,projection))
  checks.append('exact old/new reference pixels with 8 transformed mixed-blend/strength siblings and front/back mutations')
 (out/'result.json').write_text(json.dumps(dict(checks=checks,samples=samples,native=backend().status()),indent=2),'utf8');print('passed',len(checks),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
