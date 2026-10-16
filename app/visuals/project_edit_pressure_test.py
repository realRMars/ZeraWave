"""Actual owner saturation and 500-clip edits; no physical timing/AV claim."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,time,json,uuid,threading,traceback,os,statistics
root=Path(__file__).resolve().parents[2] if Path(__file__).parent.name=='visuals' else Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
import project_service
from project_service import ProjectService,read_project
from video_project import validate,ProjectError
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);fixture=Path(sys.argv[2]);s=ProjectService();checks=[];samples=[];gate=threading.Event()
def bind():return dict(expected_epoch=s.epoch,expected_revision=s.revision,expected_project=s.document['id'] if s.document else None,expected_command=s.command_revision)
def req(op,ok=True,**args):
 data=dict(op=op,operation_id=uuid.uuid4().hex,**bind(),**args);began=time.perf_counter();result=s.request(data);samples.append(dict(op=op,ms=(time.perf_counter()-began)*1000));assert result['ok']==ok,result;return data,result
def drain():
 end=time.monotonic()+60
 while s.jobs:
  s.poll();assert time.monotonic()<end;time.sleep(.002)
try:
 req('open',path=str(fixture));drain();assert len(s.document['clips'])==500 and len(s.document['tracks'])==12;before=deepcopy(s.document);key=s.document['clips'][0]['id'];old=next(r for r in s.document['clips'] if r['id']==key);video=next(t for t in s.document['tracks'] if t['id']==old['track'])
 for i in range(12):
  req('batch',label='Bounded large edit',changes=[dict(op='items.move',ids=[key],delta=1,mode='Normal')]);assert next(r for r in s.document['clips'] if r['id']==key)['start']==old['start']+1;req('undo');assert s.document==before
 req('batch',changes=[dict(op='track.move',id=video['id'],order=11)]);assert next(t for t in s.document['tracks'] if t['id']==video['id'])['order']==11;req('undo');assert s.document==before
 checks.append('500 clips/12 tracks: twelve accepted move/exact Undo pairs plus stable-ID track reorder/Undo through actual owner; native output dimensions unchanged')
 original=project_service.write_project
 def delayed(*args,**kwargs):
  while not gate.wait(.01):
   if args[5].is_set():raise InterruptedError('Controlled queued save cancelled')
  return original(*args,**kwargs)
 pinned=[];pinned_revision=s.revision
 with patch.object(project_service,'write_project',delayed):
  for i in range(16):pinned.append(req('save',path=str(out/f'pinned-{i}.zwv'),portable=False)[0])
  assert len(s.jobs)==16;data,result=req('save',ok=False,path=str(out/'unadmitted.zwv'),portable=False);assert result['error']['code']=='busy' and len(s.jobs)==16
  request,result=req('batch',label='Accepted while saves pending',changes=[dict(op='items.move',ids=[key],delta=1)]);accepted=deepcopy(s.document);revision=s.revision;replay=s.request(request);assert replay['ok'] and s.document==accepted and s.revision==revision
  assert s.request(dict(op='operation_status',operation_id=request['operation_id']))['outcome']['status']=='accepted';unknown=s.request(dict(op='operation_status',operation_id=uuid.uuid4().hex));assert not unknown['ok'] and s.revision==revision
  s.request(dict(op='cancel',operation_id=pinned[-1]['operation_id']));gate.set();drain()
 assert s.outcomes[pinned[-1]['operation_id']]['status']=='failed';assert all(s.outcomes[p['operation_id']]['status']=='durable' for p in pinned[:-1]);assert s.document==accepted and s.saved_revision!=s.revision
 for p in pinned[:-1]:
  reopened,rev,states,_=read_project(p['path'],threading.Event());assert reopened['clips']==before['clips'] and rev==pinned_revision and all(v['status']=='Ready' for v in states.values())
 checks.append('Actual16-job queue saturates/rejects17th without loss; edits continue under pinned saves, replay/reconciliation cannot duplicate; queued cancel and15 exact older-revision writes drain with later work still dirty')
 flag=out/'controlled-write-failure.flag';flag.write_text('fail');prior=os.environ.get('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE');os.environ['ZERAWAVE_PROJECT_TEST_WRITE_FAILURE']=str(flag)
 try:failed,_=req('save',path=str(out/'failed-save.zwv'),portable=False);drain();assert s.outcomes[failed['operation_id']]['status']=='failed' and s.document==accepted
 finally:
  flag.unlink()
  if prior is None:os.environ.pop('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE',None)
  else:os.environ['ZERAWAVE_PROJECT_TEST_WRITE_FAILURE']=prior
 req('undo');assert s.document==before;req('redo');assert s.document==accepted
 saved,_=req('save',path=str(out/'recovered.zwv'),portable=False);drain();assert s.outcomes[saved['operation_id']]['status']=='durable' and s.saved_revision==s.revision
 expected=deepcopy(s.document);req('close');req('open',path=str(out/'recovered.zwv'));drain();assert s.document['clips']==expected['clips'] and s.document['tracks']==expected['tracks'];validate(s.document)
 checks.append('Real failed-write boundary retains accepted500-clip work; same-service Undo/Redo, new Save As/close/reopen recover exact content, with valid retained history before replacement')
 history=dict(bytes=s.history_bytes,limit=s.history_limit);s.shutdown();assert not any(t.is_alive() for t in s.pool._threads)
 values=sorted(x['ms'] for x in samples if x['op']=='batch');stats=dict(count=len(values),median=statistics.median(values),p95=values[int(.95*(len(values)-1))],p99=values[int(.99*(len(values)-1))],maximum=max(values),stalls_over_250=sum(v>250 for v in values));(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,samples=samples,batch_timing=stats,post_close_history=history,resources=dict(jobs=len(s.jobs),threads_alive=sum(t.is_alive() for t in s.pool._threads))),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 gate.set()
 if not s.closed:
  for job in s.jobs.values():job['cancel'].set()
  drain();s.can_shutdown(True);s.shutdown()
