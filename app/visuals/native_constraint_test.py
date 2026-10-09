"""Exact float32 reference certification for the optional ABI-1 region kernel."""
import os,sys,json,time,hashlib
from pathlib import Path
import numpy as np
from PySide6.QtGui import QImage
from artwork import constrained_edit
from native_raster import native_constrained,backend

def run(out):
 out=Path(out);out.mkdir(exist_ok=False,parents=True);assert backend().status()['constraint_kernel'];records=[]
 # Every pair of input channel bytes and every coverage byte. Bounded 1MP
 # blocks exercise raw arithmetic, including all valid premultiplied values.
 aa=np.repeat(np.arange(256,dtype=np.uint8),256);bb=np.tile(np.arange(256,dtype=np.uint8),256)
 def image(v):return QImage(v.tobytes(),2048,512,QImage.Format_ARGB32_Premultiplied).copy()
 av=np.tile(np.stack([aa,255-aa,aa,aa],axis=1),(16,1)).reshape(512,2048,4);bv=np.tile(np.stack([bb,bb,255-bb,bb],axis=1),(16,1)).reshape(512,2048,4);a=image(av);b=image(bv)
 opacities=(0.,.001,1/255.,.1,.37,.5,.65,.73,.8,.999,1.)
 for first in range(0,256,16):
  masks=np.zeros((16,65536,4),np.uint8);masks[:,:,3]=np.arange(first,first+16,dtype=np.uint8)[:,None];mask=image(masks.reshape(512,2048,4))
  for opacity in opacities:
   begin=time.perf_counter();got=native_constrained(a,b,mask,opacity);native_ms=(time.perf_counter()-begin)*1000
   begin=time.perf_counter();expected=constrained_edit(a,b,{},opacity=opacity,coverage=mask);reference_ms=(time.perf_counter()-begin)*1000
   x=np.frombuffer(got.constBits(),np.uint8);y=np.frombuffer(expected.constBits(),np.uint8);assert np.array_equal(x,y),(first,opacity,int(np.count_nonzero(x!=y)))
   records.append(dict(mask_first=first,opacity=opacity,native_ms=native_ms,reference_ms=reference_ms,sha256=hashlib.sha256(x).hexdigest()))
 # Invalid buffers/opacity report structured errors and never enter storage.
 for opacity in (-.1,1.1,float('nan')):
  try:native_constrained(a,b,mask,opacity);raise AssertionError('invalid opacity accepted')
  except ValueError:pass
 report=dict(checks=len(records),channel_comparisons=len(records)*2048*512*4,records=records,backend=backend().status(),limits='Bounded synthetic arithmetic; native tool/mask/ordered stroke tests remain separate')
 (out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(checks=len(records),channel_comparisons=report['channel_comparisons'])))
if __name__=='__main__':run(sys.argv[1])
