"""Standalone bounded recovery/write-failure/owner tests; no live session replaced."""
from pathlib import Path
from tempfile import TemporaryDirectory
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os,time,uuid,json,threading,hashlib
import video_project as v
from project_recovery import Recovery,publish,read_snapshot,recover_copy,catalogue,MAX_FILES
from project_service import ProjectService,read_project

def run(folder):
 folder=Path(folder);root=folder/'recovery';pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='Recovery regression');clock=[0.];manager=Recovery(pool,root,lambda:clock[0]);checks=[];doc=v.create('Recover accepted metadata');uid=lambda:uuid.uuid4().hex;original=folder/'last-good.zwv';original.write_text('Preserved original bytes',encoding='utf8');unrelated=root/'unrelated.txt';root.mkdir(exist_ok=True);unrelated.write_text('Unrelated user work',encoding='utf8')
 def drain():
  end=time.monotonic()+10
  while manager.future:
   manager.poll();assert time.monotonic()<end;time.sleep(.001)
 def observe(revision):
  manager.observe(doc,'epoch',revision,0,str(original));clock[0]+=32;manager.poll();drain()
 try:
  drain();manager.observe(doc,'epoch',1,0,str(original));clock[0]=1.;manager.poll();assert not list(root.glob('*.zwvr'));clock[0]=32.;manager.poll();drain();assert manager.last['revision']==1 and original.read_text()=='Preserved original bytes';first=deepcopy(manager.last);assert read_snapshot(root,first['path'],first['sha256'])[0]['project']['document']==doc;checks.append('Only accepted metadata is durably snapshotted after interval/quiet; original project/source references retained and project Save remains separate')
  for revision in range(2,11):observe(revision)
  assert len(list(root.glob('*.zwvr')))==4 and manager.last['revision']==10;assert unrelated.read_text()=='Unrelated user work';checks.append('Ten publications rotate only four exact owner-bound slots; no other session or unrelated file pruned')
  before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.zwvr')};os.environ['ZERAWAVE_PROJECT_TEST_RECOVERY_FAILURE']='1'
  try:observe(11)
  finally:os.environ.pop('ZERAWAVE_PROJECT_TEST_RECOVERY_FAILURE',None)
  assert manager.error and {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.zwvr')}==before;assert manager.last['revision']==10;clock[0]+=32;manager.poll();drain();assert not manager.error and manager.last['revision']==11;checks.append('Actual write failure before replace preserves every prior slot; accepted revision remains available and same manager recovers without dropping work')
  snapshot=deepcopy(manager.last);target=folder/'recovered-copy.zwv';result=recover_copy(root,snapshot['path'],snapshot['sha256'],target,threading.Event());assert read_project(target,threading.Event())[:2]==(doc,11) and original.read_text()=='Preserved original bytes'
  for destination in (target,original):
   prior=destination.read_bytes()
   try:recover_copy(root,snapshot['path'],snapshot['sha256'],destination,threading.Event());raise AssertionError('Existing project replaced')
   except v.ProjectError:pass
   assert destination.read_bytes()==prior
  try:recover_copy(root,snapshot['path'],'0'*64,folder/'stale.zwv',threading.Event());raise AssertionError('Stale recovery admitted')
  except v.ProjectError as error:assert error.code=='recovery_changed'
  cancel=threading.Event();cancel.set()
  try:recover_copy(root,snapshot['path'],snapshot['sha256'],folder/'cancelled.zwv',cancel);raise AssertionError('Cancelled recovery published')
  except v.ProjectError as error:assert error.code=='cancelled'
  assert not (folder/'cancelled.zwv').exists();checks.append('Recovery writes a new standard editable copy with exact document/revision; existing/original/stale/cancelled destinations cannot be replaced')
  continuous_clock=[0.];continuous=Recovery(pool,folder/'continuous',lambda:continuous_clock[0])
  while continuous.future:continuous.poll();time.sleep(.001)
  for revision in range(1,41):continuous_clock[0]=float(revision);continuous.observe(doc,'continuous',revision,0,None);continuous.poll()
  while continuous.future:continuous.poll();time.sleep(.001)
  assert continuous.last and continuous.last['revision']>=35;continuous.closed=True;checks.append('Continuous accepted editing cannot postpone autosave indefinitely: maximum5second quiet deferral after30second interval captures an accepted revision while editing continues')
  # Fill the shared bound with other owner identities. Failure must preserve all
  # files, including a valid externally modified owned slot.
  for index in range(MAX_FILES-4):publish(root,uid(),0,None,doc,'other',index,0,None)
  before={p.name:p.read_bytes() for p in root.glob('*.zwvr')}
  try:publish(root,uid(),0,None,doc,'other',99,0,None);raise AssertionError('Global recovery count unbounded')
  except v.ProjectError as error:assert error.code=='recovery_capacity'
  assert before=={p.name:p.read_bytes() for p in root.glob('*.zwvr')};checks.append('32-file shared store capacity rejects explicitly while preserving every other owner; no cap raise or automatic broad cleanup')
  store=folder/'owner-store';os.environ['ZERAWAVE_PROJECT_RECOVERY']=str(store);service=ProjectService()
  def req(op,**args):
   key=uid();state=service.state();request=dict(op=op,operation_id=key,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['project_id'],expected_command=state['command_revision'],**args);reply=service.request(request);assert reply['ok'],reply;end=time.monotonic()+10
   while key in service.jobs:service.poll();assert time.monotonic()<end;time.sleep(.001)
   assert service.outcomes[key]['status'] in ('accepted','durable'),service.outcomes[key];return request
  try:
   req('new',name='Current unsaved work');service.recovery.observe(service.document,service.epoch,service.revision,service.saved_revision,service.path)
   while service.recovery.future:service.poll();time.sleep(.001)
   service.recovery.offer()
   while service.recovery.future:service.poll();time.sleep(.001)
   snap=service.recovery.last;req('batch',changes=[dict(op='project.rename',name='Newer accepted revision')]);live=deepcopy(service.document);revision=service.revision;history=deepcopy(service.undo);path=service.path;saved=service.saved_revision
   request=req('recover_copy',snapshot=snap['path'],snapshot_sha256=snap['sha256'],path=str(folder/'owner-recovered.zwv'));assert service.document==live and service.revision==revision and service.undo==history and service.path==path and service.saved_revision==saved
   replay=service.request(request);assert replay['ok'] and replay['outcome']['status']=='durable' and service.document==live
   req('open',path=str(folder/'owner-recovered.zwv'),discard=True);assert service.document['name']=='Current unsaved work';checks.append('Real owner can create an older recovery copy while newer accepted work/history/path stay exact; idempotent replay does not replace live state; explicit open verifies the new copy')
  finally:
   while service.jobs:service.poll();time.sleep(.001)
   service.shutdown();os.environ.pop('ZERAWAVE_PROJECT_RECOVERY',None)
  return dict(classification=__doc__,checks=checks)
 finally:
  manager.closed=True;pool.shutdown(wait=True);manager.poll()

if __name__=='__main__':
 with TemporaryDirectory(prefix='zerawave-recovery-') as folder:result=run(folder)
 print(json.dumps(result,indent=2))
