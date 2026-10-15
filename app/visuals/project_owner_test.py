"""Actual Studio owner and authenticated CLI/API; no preview/device/foreground.

Supplementary queue barrier/fault/abandoned socket checks are identified as such.
No synthetic result is called a physical UI or listening test.
"""
from pathlib import Path
import sys,os,json,time,uuid,wave,socket,hashlib,subprocess,queue,threading,traceback
from copy import deepcopy
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from studio_control_client import ControlClient
from project_api import call,Server
from project_cli import request as cli
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];samples=[];client=None
barrier=out/'save-barrier.flag';failure=out/'write-failure.flag';os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_TEST_SAVE_BARRIER=str(barrier),ZERAWAVE_PROJECT_TEST_WRITE_FAILURE=str(failure))
def wait(fn,seconds=20):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:
  result=fn()
  if result:return result
  time.sleep(.005)
 raise AssertionError('Owner/API did not settle')
def state():return call(endpoint,dict(op='state'))['state']
def make(op,**args):
 s=state();return dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args)
def run(op,wait=True,**args):
 data=make(op,**args);began=time.perf_counter();result=cli(endpoint,data,wait,30);samples.append(dict(op=op,round_trip_ms=(time.perf_counter()-began)*1000));assert result.get('ok'),result;return data,result
def terminal(key):
 r=call(endpoint,dict(op='operation_status',operation_id=key));o=r.get('outcome');return o if o and o['status'] not in ('saving','preparing') else None
try:
 path=out/'source.wav'
 with wave.open(str(path),'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(b'\x01\0\x02\0'*48000*20)
 source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
 client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);assert endpoint.is_relative_to(out)
 run('new',name='API editable episode');aid,tid,gid=[uuid.uuid4().hex for _ in range(3)]
 changes=[dict(op='media.add',id=aid,name='Stereo source',kind='Audio',location=dict(kind='external',path=str(path)),sha256=source_hash),dict(op='track.add',id=tid,name='Narration',kind='audio'),dict(op='track.add',id=gid,name='Captions',kind='graphics')]+[dict(op='clip.add',name='Shot '+str(i+1),asset=aid,track=tid,start=i*10,duration=10) for i in range(50)]
 changes+=[dict(op='caption.add',track=gid,start=i*5,duration=5,text='Cue '+str(i)+' — 测试') for i in range(70)]
 assert len(changes)<=128;request,result=run('batch',changes=changes,label='Agent assembly');assembled=state()['document'];assert len(assembled['clips'])==50 and len(assembled['captions'])==70 and len(assembled['media'])==1
 assert len(client.snapshot['media_library']['assets'])==0
 duplicate=cli(endpoint,request);assert duplicate['outcome']['revision']==1 and state()['revision']==1
 checks.append('CLI/API atomically assemble 50 clip instances and 70 Unicode captions from one scoped source; global Library unchanged; duplicate creates nothing')
 stale=deepcopy(request);stale['operation_id']=uuid.uuid4().hex;assert not call(endpoint,stale)['ok'];assert state()['document']==assembled
 batch_file=out/'request.json';batch_file.write_text(json.dumps(make('batch',label='CLI caption correction',changes=[dict(op='caption.edit',id=assembled['captions'][0]['id'],values=dict(text='Corrected caption — ✓'))])),'utf8')
 p=subprocess.run([sys.executable,'-B',str(ROOT/'app/visuals/project_cli.py'),'--endpoint',str(endpoint),'--request',str(batch_file)],capture_output=True,text=True,encoding='utf8');(out/'cli-stdout.json').write_text(p.stdout,'utf8');assert p.returncode==0,p.stderr
 correction=state()['document'];run('undo');assert state()['document']==assembled;run('redo');assert state()['document']==correction
 checks.append('Actual installed CLI corrects text; owner Undo/Redo exact; stale agent request cannot overwrite manual-equivalent changes')
 data=make('batch',label='Abandoned reply',changes=[dict(op='project.rename',name='Lost reply applied once')]);endpoint_data=json.loads(endpoint.read_text())
 with socket.create_connection(('127.0.0.1',endpoint_data['port'])) as sock:sock.sendall(json.dumps(dict(token=endpoint_data['token'],request=data)).encode()+b'\n')
 wait(lambda:terminal(data['operation_id']));revision=state()['revision'];assert cli(endpoint,data)['outcome']['revision']==revision and state()['revision']==revision
 checks.append('Abandoned real socket reply reconciles SAME operation ID without duplicate revision/history')
 forged=out/'wrong-token.json';forged.write_text(json.dumps(dict(endpoint_data,token='invalid')));assert not call(forged,dict(op='state'))['ok'];assert state()['revision']==revision
 checks.append('Authenticated endpoint rejects wrong token without mutation')
 # The detailed receipt is bounded; saves do not change document revision.
 old,_=run('undo');run('redo')
 for i in range(1030):
  wrong=make('batch',label='Retire invalid receipt',changes=[dict(op='unsupported-edit')]);assert not call(endpoint,wrong)['ok']
 assert call(endpoint,dict(op='operation_status',operation_id=old['operation_id']))['outcome'] is None
 assert not call(endpoint,old)['ok'];assert state()['revision']==revision+2
 checks.append('1030 rejected commands retire detailed receipts; old exact ID cannot reapply after retirement')
 run('save',path=str(out/'good.zwv'));good_hash=hashlib.sha256((out/'good.zwv').read_bytes()).hexdigest();assert not state()['dirty']
 barrier.write_text('held');jobs=[]
 for i in range(16):data,_=run('save',wait=False,path=str(out/f'pending-{i}.zwv'));jobs.append(data['operation_id'])
 overflow=call(endpoint,make('save',path=str(out/'overflow.zwv')));assert not overflow['ok'] and overflow['error']['code']=='busy'
 run('batch',label='Edit during pinned saves',changes=[dict(op='project.rename',name='Newer accepted work')]);later=state()['document']
 try:client.submit('close',mode='clean').result(5)
 except ValueError:pass
 else:raise AssertionError('Closed with pinned jobs')
 assert client.process.poll() is None
 for key in jobs:call(endpoint,dict(op='cancel',operation_id=key))
 barrier.unlink();outcomes=[wait(lambda key=key:terminal(key)) for key in jobs];assert all(o['status']=='failed' and o['error']['code']=='cancelled' for o in outcomes)
 assert state()['document']==later and state()['dirty'];assert hashlib.sha256((out/'good.zwv').read_bytes()).hexdigest()==good_hash
 checks.append('Controlled slow saves fill 16-job admission; overflow rejected, owner remains live, newer edits exact, cancellation releases jobs and prior durable file intact')
 failure.write_text('fail');failed=cli(endpoint,make('save',path=str(out/'good.zwv')));assert not failed['ok'] and failed['outcome']['status']=='failed';assert state()['document']==later and state()['dirty'];assert hashlib.sha256((out/'good.zwv').read_bytes()).hexdigest()==good_hash
 failure.unlink();saved,result=run('save',path=str(out/'recovered.zwv'));assert result['outcome']['revision']==state()['revision'] and not state()['dirty']
 call(endpoint,dict(op='cancel',operation_id=saved['operation_id']));assert terminal(saved['operation_id'])['status']=='durable'
 run('close');run('open',path=str(out/'recovered.zwv'));reopened=state()['document'];assert reopened['clips']==later['clips'] and reopened['captions']==later['captions'] and reopened['name']==later['name']
 alias=out/'original-alias.wav';os.link(path,alias);protected=cli(endpoint,make('save',path=str(alias)));assert not protected['ok'] and protected['outcome']['error']['code']=='protected_source';assert hashlib.sha256(path.read_bytes()).hexdigest()==source_hash
 checks.append('Actual owner write failure/retry, portable Save/reopen, late cancel durable-wins, original-source hardlink protection')
 legacy=client.submit('load',path=str(out/'recovered.zwv'))
 try:legacy.result(5)
 except ValueError as exc:assert 'Open video project' in str(exc)
 else:raise AssertionError('Legacy session load accepted video fields')
 assert state()['document']==reopened
 checks.append('Legacy Open session rejects video-project fields and preserves both document routes')
 before_fault=client.protocol_error_count;assert before_fault==0,(client.protocol_errors,client.snapshot.get('control_boundary'))
 endpoint_path=endpoint;run('close');client.close();assert client.process.returncode==0 and not endpoint_path.exists() and not client.reader.is_alive() and not client.notifier.is_alive()
 checks.append('No projection sequence gaps/protocol faults; normal owner exit removes endpoint and joins its client readers/writers')
 # Supplement: deliberately full queue, without an executing owner.
 q=queue.Queue(maxsize=1);q.put({'occupied':True});server=Server(q,out/'facade-pressure')
 try:
  r=call(server.path,dict(op='state'));assert not r['ok'] and 'not admitted' in r['error']['message']
 finally:server.close()
 assert not server.thread.is_alive() and not server.clients and not server.threads and not server.path.exists()
 checks.append('Supplementary full owner-queue facade explicitly rejects admission and retires API readers/endpoint')
 report=dict(classification='Real owner/stdlib socket/installed CLI; controlled pressure/failure supplements; no physical/UI/device claims',checks=checks,samples=samples,source_sha256=source_hash,protocol_errors=before_fault,owner_exit=client.process.returncode)
 (out/'RESULT.json').write_text(json.dumps(report,indent=2),'utf8');print('PASS',len(checks))
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,samples=samples),indent=2),'utf8');raise
finally:
 if barrier.exists():barrier.unlink()
 if client and not client.closed:client.close(mode='discard',project_mode='discard')
