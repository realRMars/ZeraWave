"""Paused seeks reconcile without claiming, replacing or stopping legacy output."""
from pathlib import Path
import sys,time,json,uuid
from contextlib import contextmanager
import numpy as np,soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'visuals'))
from studio_transport import AudioOwner
from video_project import create,apply
from project_evaluator import Evaluator
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
class Enumeration:
 def request(self):pass
 def snapshot(self):return dict(sources=[],error=None)
 def close(self):pass
class Sink:
 paces_audio=False; padding=0
 def __init__(self):self.opens=0;self.live=0
 @contextmanager
 def context(self):
  self.opens+=1;self.live+=1
  try:yield self
  finally:self.live-=1
 def play(self,pcm):pass
 def snapshot(self):return dict(backend='Controlled legacy output; no hardware')
 def drain(self):pass
def wait(fn):
 end=time.monotonic()+5
 while time.monotonic()<end:
  if fn():return
  time.sleep(.002)
 raise AssertionError('Owner did not settle')
t=uuid.uuid4().hex;doc=apply(create(),[dict(op='track.add',id=t,kind='graphics'),dict(op='caption.add',track=t,start=0,duration=60,text='Paused ruler')],uuid.uuid4().hex)[0];rows=[]
for legacy in (False,True):
 sink=Sink();owner=AudioOwner(enumerator=Enumeration(),output_factory=sink.context)
 try:
  if legacy:
   path=out/'legacy.wav';sf.write(path,np.full((48000*3,2),.1,np.float32),48000,subtype='FLOAT');owner.submit('open',path=str(path));wait(lambda:owner.snapshot()['mode']=='Audio File');owner.submit('play');wait(lambda:owner.snapshot()['output']);decoder=owner.decoder;context=owner.output
  for generation,frame in [(1,20),(2,35)]:
   owner.offer_project(Evaluator(doc,'paused',1),dict(epoch='paused',revision=1,generation=generation,discontinuity=generation,project=doc['id'],frame=frame,sample=frame*1600,active=True,playing=False));wait(lambda:owner.project_snapshot().get('requested_serial')==generation and not owner.project_snapshot().get('transition_pending'));r=owner.project_snapshot();assert r['status']=='Paused' and not r['active'] and r['parked_legacy'] and r['requested_outcome']=='applied' and r['requested_binding']==r['applied_binding'] and r['requested_sample']==frame*1600;assert owner.project_saved is None and owner.project_spec is None
   if legacy:assert owner.decoder is decoder and owner.output is context and sink.opens==1 and sink.live==1 and owner.snapshot()['playing']
   else:assert sink.opens==0 and owner.output is None
   rows.append(dict(legacy=legacy,frame=frame,runtime=r))
 finally:owner.close();assert not owner.worker.is_alive() and not owner.server.is_alive() and owner.project_lane.exited() and sink.live==0
(out/'RESULT.json').write_text(json.dumps(dict(checks=4,rows=rows,classification=__doc__),indent=2),'utf8');print('PASS paused seek reconciliation 4')
