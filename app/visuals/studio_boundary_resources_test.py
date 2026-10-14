"""Native/fallback allocation aliases and projection pins; no widget construction."""
from pathlib import Path
import sys,os,json,uuid,threading,time
from PySide6.QtGui import QImage,QColor
from native_raster import backend
from raster_resources import Resources,snapshot,release

def run(folder):
 out=Path(folder);out.mkdir(parents=True,exist_ok=False);r=Resources(out/'store');barrier=threading.Event();r.barrier=barrier
 pixels=QImage(16,16,QImage.Format_ARGB32_Premultiplied);pixels.fill(QColor('#35a7d0'));native=backend().storage().from_image(pixels) if backend().available else pixels
 desc,producer=snapshot(native);ids=[uuid.uuid4().hex for _ in range(2)]
 try:
  assets=[dict(id=k,kind='Images',managed=True,name='Alias',path=str(out/(k+'.png')),metadata=dict(width=16,height=16),runtime=desc) for k in ids]
  r.admit(assets)
  for k in ids:r.persist(k)
  projection=r.ownership({ids[0]},{ids[0],ids[1]},{7:set(ids)})
  assert projection['unique_allocation_bytes']==sum(r.usage().values())==1024
  assert projection['alias_references']==2*projection['allocation_count']
  assert all(row['job'] for row in projection['resources'])
  assert sum(row['document'] for row in projection['resources'])==1
  assert all(row['history'] and row['publications']==[7] for row in projection['resources'])
  before=r.projection_token();barrier.set()
  end=time.perf_counter()+20
  while any(not f.done() for f in r.jobs.values()) and time.perf_counter()<end:time.sleep(.002)
  r.poll();assert not r.failures and r.projection_token()!=before
  after=r.ownership({ids[0]},set(ids),{})
  assert after['unique_allocation_bytes']==projection['unique_allocation_bytes'] and not any(row['job'] for row in after['resources'])
  assert r.retain(set(ids)) is None # retained history is legitimate ownership
  assert len(r.rows)==2
  # Read-only projection pressure: metadata aliases must not explode a packet.
  try:
   for i in range(254):
    key='projection-'+str(i);r.rows[key]=dict(r.rows[ids[0]],id=key);r.allocations[key]=r.allocations[ids[0]]
   pressure=r.ownership(set(),set(r.rows),{})
   assert pressure['alias_references']==256*pressure['allocation_count'] and pressure['alias_detail_truncated']
   assert all(len(a['resources'])<=8 for a in pressure['allocations'])
   assert len(json.dumps(pressure))<262144
  finally:
   for i in range(254):r.rows.pop('projection-'+str(i),None);r.allocations.pop('projection-'+str(i),None)
  (out/'result.json').write_text(json.dumps(dict(backend=backend().status(),before=projection,after=after,state=r.state(),metadata_pressure=pressure,checks=['Aliases count unique allocation once','Document/history/publication pins projected independently','Pending jobs retain leases','Quiescence preserves legitimate history ownership','256 alias metadata projection stays bounded; totals remain complete']),indent=2),encoding='utf8')
 finally:
  barrier.set();r.close(discard=True);release(producer)
 print(json.dumps(dict(passed=5,out=str(out))))
if __name__=='__main__':run(sys.argv[1])
