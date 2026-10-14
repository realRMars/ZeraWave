"""Exact zero-leaf optimization and incomplete required-row future regression."""
from pathlib import Path
import sys,os,time,json,hashlib,importlib.util
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(os.environ.get('ZERAWAVE_TEST_ROOT',str(Path(__file__).resolve().parents[2])));OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False);baseline=Path(sys.argv[2]);sys.path[:0]=[str(ROOT/'app/visuals')]
import numpy as np,moderngl
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from native_raster import backend
from cpu_projection import Projection
from artwork_export import FrozenCanvas
from composition import defaults,new_layer,transform
from scene_surfaces import SurfaceStage,cavern_row
app=QApplication([]);spec=importlib.util.spec_from_file_location('projection_reference',baseline/'app/visuals/cpu_projection.py');reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
checks=[];records=[];z=QImage(32,24,QImage.Format_ARGB32_Premultiplied);z.fill(0);zero=backend().storage().from_image(z);assert zero.transparent_zero();dot=QImage(1,1,QImage.Format_ARGB32_Premultiplied);dot.fill(QColor('#ff3300'));nonzero=zero.patch((17,12,1,1),dot);assert not nonzero.transparent_zero() and zero.transparent_zero()
for count in (1,8,30,32):
 scene=defaults();scene['canvas']=[32,24];images={};metadata={}
 for i in range(count):
  row=new_layer('Image',str(i),str(i));row.update(order=i,opacity=.71,fit='Stretch',transform=transform(0.,0.,.9,1.,17. if i%2 else 0.),blend=('Normal','Multiply','Screen','Add','Difference')[i%5],blend_strength=.65)
  if count>=8 and i%2:row['parent']=scene['layers'][-1]['id']
  scene['layers'].append(row);images[row['id']]=nonzero if i==0 else zero;metadata[row['id']]=dict(width=32,height=24)
 adapter=FrozenCanvas(scene,images,metadata,(32,24));matrix=np.array([[120.,0.,70.],[0.,85.,50.],[0.,0.,1.]])
 before=reference.Projection();after=Projection()
 for i in range(4):
  scene['layers'][0]['opacity']=.2+i*.13;a=before.render(adapter,140,100,matrix);b=after.render(adapter,140,100,matrix);assert bytes(a.constBits())==bytes(b.constBits());records.append(dict(layers=count,index=i,pixels=hashlib.sha256(bytes(b.constBits())).hexdigest()))
checks.append('Immutable all-channel zero fact preserves changed versions, nested transforms and five blend modes:16 exact comparisons')
ctx=moderngl.create_standalone_context(require=330);stage=SurfaceStage(ctx,cavern=False)
class Incomplete:
 done_value=False;calls=0
 def done(self):return self.done_value
 def result(self):
  assert self.done_value,'Required row attempted to block on incomplete future';self.calls+=1;return cavern_row(-2)
future=Incomplete();stage.pending[-2]=future
try:
 start=time.perf_counter();stage.prepare_cavern(0.);elapsed=(time.perf_counter()-start)*1000
 assert future.calls==0 and stage.metrics['required_inline_pending_rows']==1 and len(stage.row_buffers)==24 and len(stage.pending)==1
 assert stage.row_buffers[-2].read()==cavern_row(-2).tobytes()
 future.done_value=True;stage.warm_rows(0.);assert future.calls==1 and -2 not in stage.ready and len(stage.pending)<=2
 checks.append('Incomplete helper never awaited; exact local row published; completed redundant result consumed without retention; resident/prefetch bounds unchanged')
 report=dict(result='PASS',checks=checks,records=records,required_inline_ms=elapsed,metrics=dict(stage.metrics),device=ctx.info,source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'app/visuals/scene_surfaces.py',ROOT/'app/visuals/cpu_projection.py',ROOT/'app/visuals/native_raster.py']},helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
finally:stage.release();ctx.release()
(OUT/'RESULT.json').write_text(json.dumps(report,indent=2));print('PASS',len(checks),flush=True)
