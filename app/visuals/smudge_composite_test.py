"""Regional automatic Smudge artwork compositor vs existing broad Qt projection.
CPU fixtures; no physical pointer or artistic acceptance claim.
"""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import sys,json
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor,QPainter
from composition import defaults,new_layer,transform,asset_matrix,BLENDS
from cpu_projection import Projection,render_artwork_region
from editor_colors import pixel_frame,pin_pickup,pickup_tile
from studio_composition import masked_image,add_image
from native_raster import backend

def run(folder):
 out=Path(folder);out.mkdir(parents=True,exist_ok=False);app=QApplication.instance() or QApplication([]);checks=[];observations=[]
 w,h=96,64;scene=defaults();scene['canvas']=[w,h]
 back=new_layer(asset='back');back['fit']='Stretch';group=new_layer('Group');group['order']=1;top=new_layer(asset='top');top.update(parent=group['id'],fit='Stretch',opacity=.57);target=new_layer(asset='blank');target.update(order=2,fit='Stretch')
 a=QImage(w,h,QImage.Format_ARGB32_Premultiplied);a.fill(QColor(220,40,60,170));b=QImage(w,h,QImage.Format_ARGB32_Premultiplied);b.fill(QColor(30,80,210,140));p=QPainter(b);p.fillRect(30,5,30,50,QColor(210,180,20,190));p.end();blank=QImage(w,h,QImage.Format_ARGB32_Premultiplied);blank.fill(0)
 scene['layers']=[back,group,top,target];images={'back':a,'top':b,'blank':blank};editor=SimpleNamespace(config=scene,images=images,pending_paint=None)
 canvas=SimpleNamespace(editor=editor,canvas_size=(w,h),stroke=None,source_matrix=lambda row:asset_matrix(scene,row,(w,h),(w,h)),mask_image=masked_image)
 projection=np.array([[w,0,w/2],[0,h,h/2],[0,0,1.]],float);x,y,rw,rh=24,14,28,26;regional=projection.copy();regional[:2,2]-=(x,y)
 def data(im):return np.frombuffer(im.constBits(),np.uint8).reshape(im.height(),im.bytesPerLine())[:,:im.width()*4].reshape(im.height(),im.width(),4).copy()
 for transformed in (False,True):
  group.update(opacity=.68 if transformed else 1.,transform=transform(.04,-.03,.9,1.1,18) if transformed else transform())
  top.update(crop=[.05,.1,.95,.9] if transformed else [0.,0.,1.,1.],flip_x=transformed,flip_y=transformed)
  top['masks']=[dict(mode='Keep',enabled=True,shape='Ellipse',points=[[.1,.1],[.9,.1],[.9,.9],[.1,.9]],handles=[])] if transformed else []
  group['masks']=[dict(mode='Keep',enabled=True,shape='Rectangle',points=[[.04,.04],[.96,.04],[.96,.96],[.04,.96]],handles=[])] if transformed else []
  for blend in BLENDS:
   top['blend']=blend
   for strength in (0.,.43,1.):
    top['blend_strength']=strength
    frames={r['id']:pixel_frame(canvas,r,images[r['asset']]) for r in scene['layers'] if r['type']!='Group'}
    actual=render_artwork_region(scene,{r['id']:images[r['asset']] for r in scene['layers'] if r['type']!='Group'},frames,regional,rw,rh,target['id'],blank)
    # B1's canvas uses the same Qt Add reference when no native kernel exists.
    from unittest.mock import patch
    with patch('cpu_projection.native_add',side_effect=add_image) if not backend().available else __import__('contextlib').nullcontext():reference=Projection().render(canvas,w,h,projection).copy(x,y,rw,rh)
    aa,bb=data(actual).astype(int),data(reference).astype(int);difference=abs(aa-bb);peak=int(difference.max());changed=int((difference>0).any(axis=2).sum());observations.append(dict(transformed=transformed,blend=blend,strength=strength,peak_channel_difference=peak,changed_pixels=changed))
    assert peak<=2,(transformed,blend,strength,peak,changed)
 checks.append('30 regional cases cover order, all blends/strength, opacity, rotated/flipped/nonuniform Group, crop and exact masks; comparison retains Qt filtering/rounding differences <=2 channels')
 # Available pinned decoded frames include video/GIF/sprite raster images; missing
 # visible frame is an explicit rejection, hidden frame never contributes.
 source_images={r['id']:images[r['asset']] for r in scene['layers'] if r['type']!='Group'};frames={r['id']:pixel_frame(canvas,r,images[r['asset']]) for r in scene['layers'] if r['type']!='Group'}
 top['enabled']=False;hidden=render_artwork_region(scene,source_images,frames,regional,rw,rh,target['id'],blank);del source_images[top['id']];assert np.array_equal(data(hidden),data(render_artwork_region(scene,source_images,frames,regional,rw,rh,target['id'],blank)))
 top['enabled']=True
 try:render_artwork_region(scene,source_images,frames,regional,rw,rh,target['id'],blank);raise AssertionError('missing visible source omitted')
 except ValueError as exc:assert 'readable frame' in str(exc)
 checks.append('Hidden unavailable sources excluded; visible unavailable source rejects explicitly')
 class RegionalOnly:
  def __init__(self,image):self.im=image;self.reads=[]
  def width(self):return self.im.width()
  def height(self):return self.im.height()
  def region(self,bounds):self.reads.append(bounds);return self.im.copy(*bounds)
 large=QImage(4096,2048,QImage.Format_ARGB32_Premultiplied);large.fill(QColor('red'));large_source=RegionalOnly(large);one=defaults();one['canvas']=[4096,2048];row=new_layer(asset='large');row['fit']='Stretch';one['layers']=[row];frame=np.array([[1/4096,0,-.5],[0,1/2048,-.5],[0,0,1.]]);proj=np.array([[4096,0,2048-100],[0,2048,1024-100],[0,0,1.]])
 result=render_artwork_region(one,{row['id']:large_source},{row['id']:frame},proj,24,24);assert large_source.reads and max(b[2]*b[3]*4 for b in large_source.reads)<4096;assert result.pixelColor(10,10)==QColor('red')
 try:render_artwork_region(one,{row['id']:large_source},{row['id']:frame},proj,2048,2048);raise AssertionError('oversized sample accepted')
 except ValueError as exc:assert 'capacity' in str(exc)
 checks.append('4096x2048 source sampled only in <=28x28 regional footprint; oversized composite rejects before allocation')
 if backend().available:
  from editor_pixels import clear,translated,materialize,digest
  source=QImage(258,130,QImage.Format_ARGB32_Premultiplied);source.fill(QColor(70,120,210,180));mask=QImage(258,130,QImage.Format_ARGB32_Premultiplied);mask.fill(0);p=QPainter(mask);p.fillRect(5,8,35,40,QColor(255,255,255,127));p.end();native=backend().storage().from_image(source);original=digest(source)
  deleted=clear(native,mask);moved=translated(native,mask,(9,5));assert digest(deleted)==digest(clear(source,mask)) and digest(moved)==digest(translated(source,mask,(9,5))) and digest(materialize(native))==original
  assert deleted.stamp((200,60,10,10))==native.stamp((200,60,10,10));assert moved.stamp((200,60,10,10))==native.stamp((200,60,10,10));checks.append('Native fractional clear/overlapping pixel move exactly matches B1 reference; immutable source and unchanged tiles shared')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,observations=observations,limits='CPU Qt region semantics; <=2 per-channel filtering/rounding bound, not exact transformed sampling certificate'),indent=2),encoding='utf8');print('PASS',json.dumps(checks),flush=True)
if __name__=='__main__':run(sys.argv[1])
