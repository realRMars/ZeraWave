"""Remaining R1: actual preparation pool, guard/publication/cancel/retirement.

Controlled thread interleavings; not a physical window/device test.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,json,time,uuid,threading,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
import project_service
from project_service import ProjectService
from video_project import ProjectError
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];evidence=[];services=[]
def binding(service):
 s=service.state();return dict(expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'])
def req(service,op,**args):
 d=dict(op=op,operation_id=uuid.uuid4().hex,**binding(service),**args);r=service.request(d);assert r.get('ok'),r;return d,r
def wait(fn):
 end=time.perf_counter()+15
 while time.perf_counter()<end:
  if fn():return
  time.sleep(.002)
 raise AssertionError('Preparation did not settle')
def source():return dict(op='media.add',name='Missing placeholder',kind='Audio',placeholder=True,sha256='a'*64,location=dict(kind='external',path=str(out/'absent.wav')))
def new():
 s=ProjectService();services.append(s);req(s,'new',name='Before preparation');return s
def rejected_close(s,captured,discard):
 try:s.can_shutdown(discard,binding=captured)
 except ProjectError as exc:assert exc.code=='stale_revision';return str(exc)
 else:raise AssertionError('Stale close discarded newly accepted revision')
def drain(s):
 while s.jobs:s.poll();time.sleep(.002)
try:
 # Exact Reviewer PREPARED_CLOSE reproduction, using the real preparation pool.
 for discard in (False,True):
  s=new();d,r=req(s,'batch',changes=[source()]);wait(lambda:s.jobs[d['operation_id']]['future'].done());captured=binding(s);assert captured['expected_revision']==0;message=rejected_close(s,captured,discard);assert s.revision==1 and len(s.document['media'])==1 and not s.jobs and s.outcomes[d['operation_id']]['status']=='accepted';evidence.append(dict(case='completed preparation',discard=discard,captured=captured,after=binding(s),outcome=s.outcomes[d['operation_id']],close_error=message));req(s,'batch',label='Continue after stale close',changes=[dict(op='project.rename',name='Same owner recovered')]);req(s,'undo');req(s,'redo');save,_=req(s,'save',path=str(out/('recovered-'+str(discard)+'.zwv')),allow_missing=True);drain(s);assert s.outcomes[save['operation_id']]['status']=='durable' and s.can_shutdown(False,binding=binding(s));s.shutdown();assert not any(t.is_alive() for t in s.pool._threads)
 checks.append('Completed imports reconcile before both clean/discard captured guards; newer accepted work stays in the same service, edits/Undo/Redo/new Save recover and actual threads exit')
 # A worker stays blocked while clean close is checked: no cancellation/admission.
 for discard in (False,True):
  s=new();entered=threading.Event();release=threading.Event();original=project_service.prepare_changes
  def slow(changes,base,cancel):entered.set();release.wait(10);return original(changes,base,cancel)
  with patch.object(project_service,'prepare_changes',slow):d,r=req(s,'batch',changes=[source()]);wait(entered.is_set);captured=binding(s);assert not s.can_shutdown(discard,binding=captured);assert s.jobs[d['operation_id']]['cancel'].is_set()==discard;before=deepcopy(s.document);release.set();wait(lambda:s.jobs[d['operation_id']]['future'].done());s.poll()
  if discard:assert s.document==before and s.outcomes[d['operation_id']]['status']=='failed' and s.outcomes[d['operation_id']]['error']['code']=='cancelled'
  else:assert s.revision==1 and s.outcomes[d['operation_id']]['status']=='accepted';rejected_close(s,captured,False)
  req(s,'batch',label='Continue after pressure',changes=[dict(op='project.rename',name='Running preparation resolved')]);s.can_shutdown(True,binding=binding(s));s.shutdown();assert not any(t.is_alive() for t in s.pool._threads);evidence.append(dict(case='running preparation',discard=discard,outcome=s.outcomes[d['operation_id']]))
 checks.append('Still-running clean close waits without cancelling; explicit discard cancels unaccepted preparation accurately, preserves document and resumes editing/retirement')
 # Finish AFTER reconciliation but before the guard. The job still owns it;
 # there is no second poll publishing after the validated close decision.
 for discard in (False,True):
  s=new();entered=threading.Event();release=threading.Event();original=project_service.prepare_changes
  def slow(changes,base,cancel):entered.set();release.wait(10);return original(changes,base,cancel)
  with patch.object(project_service,'prepare_changes',slow):d,r=req(s,'batch',changes=[source()]);wait(entered.is_set);captured=binding(s);guard=s._guard
  def complete_at_guard(data,command=True):release.set();wait(lambda:s.jobs[d['operation_id']]['future'].done());return guard(data,command)
  s._guard=complete_at_guard;assert not s.can_shutdown(discard,binding=captured);assert s.revision==0 and d['operation_id'] in s.jobs;s._guard=guard;s.poll()
  if discard:assert s.revision==0 and s.outcomes[d['operation_id']]['status']=='failed'
  else:assert s.revision==1 and s.outcomes[d['operation_id']]['status']=='accepted';rejected_close(s,captured,False)
  s.can_shutdown(True,binding=binding(s));s.shutdown();assert not any(t.is_alive() for t in s.pool._threads);evidence.append(dict(case='future finishes between reconcile and guard',discard=discard,outcome=s.outcomes[d['operation_id']]))
 checks.append('Future completion between reconcile/guard cannot publish past the guard; both modes report accurate terminal outcomes with complete owned retirement')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,evidence=evidence,classification=__doc__),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 for s in services:
  if not s.closed:
   for j in s.jobs.values():j['cancel'].set()
   drain(s);s.can_shutdown(True);s.shutdown()
