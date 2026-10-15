"""Delayed native output outcomes cannot replace newer seek/pause/Stop intent."""
from pathlib import Path
from contextlib import contextmanager
import sys,threading,time,json,uuid,hashlib,traceback
import numpy as np,soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'visuals'))
from studio_transport import AudioOwner
from project_evaluator import Evaluator
from video_project import create,apply
class Enumeration:
 def request(self):pass
 def snapshot(self):return dict(sources=[],error=None)
 def close(self):pass
class Sink:
 paces_audio=False; padding=0
 def __init__(self,fail=False):self.entered=threading.Event();self.release=threading.Event();self.first=True;self.fail=fail;self.contexts=0
 @contextmanager
 def context(self):
  self.contexts+=1
  try:yield self
  finally:
   if self.fail:raise RuntimeError('Controlled native release unconfirmed')
 def play(self,pcm):
  if self.first:
   self.first=False;self.entered.set();assert self.release.wait(10)
   if self.fail:raise RuntimeError('Controlled original submission failure')
 def snapshot(self):return dict(backend='Controlled sink; no hardware',device_position=None)
 def drain(self):pass
def wait(predicate):
 end=time.monotonic()+10
 while time.monotonic()<end:
  if predicate():return
  time.sleep(.002)
 raise RuntimeError('Audio owner did not settle')
def run(out):
 out.mkdir(parents=True,exist_ok=False);path=out/'source.wav';sf.write(path,np.full((96000,2),.1,np.float32),48000,subtype='FLOAT');a,t,c=[uuid.uuid4().hex for _ in range(3)]
 doc=apply(create(),[dict(op='media.add',id=a,name='Source',kind='Audio',location=dict(kind='external',path=str(path)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=dict(duration=2)),dict(op='track.add',id=t,kind='audio'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=60)],uuid.uuid4().hex)[0];evaluator=Evaluator(doc,'report-test',1);rows=[]
 def transport(generation,mode):return dict(project=doc['id'],epoch='report-test',revision=1,generation=generation,discontinuity=generation,frame=20 if generation==2 else 0,sample=32000 if generation==2 else 0,playing=mode=='seek',active=mode!='Stop')
 for mode in ('seek','Pause','Stop','failure'):
  sink=Sink(mode=='failure');owner=AudioOwner(output_factory=sink.context,enumerator=Enumeration());observed=threading.Event();release_report=threading.Event();row={'case':mode};change=owner.change
  def intercept(**kwargs):
   change(**kwargs);value=kwargs.get('project_audio',{})
   if not observed.is_set() and (value.get('binding') or [None]*3)[2]==1 and owner.project_desired['binding'][2]==2 and value.get('status') in ('Playing','Release unconfirmed'):
    row['late_report']=owner.project_snapshot();observed.set();assert release_report.wait(10)
  owner.change=intercept
  try:
   owner.offer_project(evaluator,transport(1,'seek'));wait(sink.entered.is_set);owner.offer_project(evaluator,transport(2,'seek' if mode=='failure' else mode));row['offered']=owner.project_snapshot();sink.release.set();wait(observed.is_set)
   late=row['late_report'];assert late['requested_binding'][2]==2 and late['requested_serial']==2 and late['transition_pending'] and late['requested_outcome']=='pending',late;assert late['applied_binding'][2]==1 and late['applied_serial']==1,late
   if mode!='failure':assert late['last_submitted_binding'][2]==1 and late['last_submitted_sample']==2048,late
   else:assert 'original submission failure' in late['error'] and 'release unconfirmed' in late['error'],late
   release_report.set();wait(lambda:owner.project_snapshot().get('requested_serial')==2 and not owner.project_snapshot().get('transition_pending'))
   final=owner.project_snapshot();row['settled']=final;assert final['requested_binding'][2]==2
   if mode=='failure':assert final['requested_outcome']=='failed' and owner.blocked and sink.contexts==1
   else:assert final['applied_binding'][2]==2 and final['requested_outcome']=='applied';assert final['status'] in {'seek':'Buffering','Pause':'Paused','Stop':'Stopped'}.values() or final['status']=='Playing'
  finally:
   sink.release.set();release_report.set();
   try:owner.close()
   except RuntimeError:assert mode=='failure' and owner.output_release_error
   row['worker_exited']=not owner.worker.is_alive() and not owner.server.is_alive();row['preparation_exited']=owner.project_lane.exited();assert row['worker_exited'] and row['preparation_exited'];rows.append(row)
 (out/'RESULT.json').write_text(json.dumps(dict(checks=len(rows),rows=rows,classification='Real AudioOwner/native preparation; controlled delayed output and release; no device/listening',source_sha256=hashlib.sha256(Path(__file__).with_name('project_output.py').read_bytes()).hexdigest()),indent=2),'utf8');print('PASS delayed reporting',len(rows))
if __name__=='__main__':run(Path(sys.argv[1]))
