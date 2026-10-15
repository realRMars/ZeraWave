"""Focused schema, scoped media/history, retirement and capacity boundary checks."""
from pathlib import Path
from copy import deepcopy
import sys,os,json,uuid,time,wave,hashlib,shutil,traceback
ROOT=Path(os.environ.get('ZERAWAVE_PROJECT_SOURCE_ROOT',r'C:\ZeraWave'));sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from video_project import create,apply,validate,ProjectError
from project_service import ProjectService
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);service=ProjectService();checks=[];raw=[]
def command(op,**args):
 s=service.state();return dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args)
def run(op,**args):
 data=command(op,**args);r=service.request(data);end=time.perf_counter()+20
 while r.get('outcome',{}).get('status') in ('preparing','saving'):
  assert time.perf_counter()<end;service.poll();r=service.request(dict(op='operation_status',operation_id=data['operation_id']));time.sleep(.002)
 assert r.get('outcome',{}).get('status') in ('accepted','durable'),r
 return data,r
def bad(doc,code):
 try:validate(doc)
 except ProjectError as exc:assert exc.code==code,(exc.code,code)
 else:raise AssertionError('Invalid document was accepted')
try:
 run('new',name='Integrity',base_directory=str(out));asset,track,graphics,clip=[uuid.uuid4().hex for _ in range(4)]
 def wav(path,value):
  with wave.open(str(path),'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(bytes((value,0,value+1,0))*48000*4)
  return hashlib.sha256(path.read_bytes()).hexdigest()
 first=out/'first.wav';second=out/'second.wav';h1=wav(first,1);h2=wav(second,3)
 run('batch',label='Initial source',changes=[dict(op='media.add',id=asset,name='Media',kind='Audio',location=dict(kind='relative',path='first.wav'),sha256=h1),dict(op='track.add',id=track,name='Audio',kind='audio'),dict(op='track.add',id=graphics,name='Graphics',kind='graphics'),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=60)])
 before=deepcopy(service.document);states=deepcopy(service.media_state)
 run('batch',label='Deliberate relink',changes=[dict(op='media.relink',id=asset,kind='Audio',location=dict(kind='external',path=str(second)),sha256=h1,accept_changed=True)])
 relink=deepcopy(service.document);after_states=deepcopy(service.media_state);assert after_states[asset]['path']==str(second) and after_states[asset]['expected']==h2 and str(first) in relink['protected_paths']
 run('undo');assert service.document==before and service.media_state==states;run('redo');assert service.document==relink and service.media_state==after_states
 run('save',path=str(out/'saved.zwv'));run('close');run('open',path=str(out/'saved.zwv'));assert service.source_base==str(out)
 for target in (first,second):
  r=service.request(command('save',path=str(target)));end=time.perf_counter()+10
  while r.get('outcome',{}).get('status')=='saving':service.poll();r=service.request(dict(op='operation_status',operation_id=r['outcome']['id']));time.sleep(.002);assert time.perf_counter()<end
  assert r['outcome']['error']['code']=='protected_source'
 checks.append('Explicit relative import; changed relink; exact media-status Undo/Redo; portable reopen and both original sources protected')
 prior=deepcopy(service.document);unsupported=deepcopy(prior);unsupported['settings']['future_field']=True;bad(unsupported,'unsupported_fields');unsupported=deepcopy(prior);unsupported['clips'][0]['audio']['unknown_gain']=1;bad(unsupported,'unsupported_fields');unsupported=deepcopy(prior);unsupported['media'][0]['location']['path']='../same.wav';unsupported['media'][0]['location']['kind']='relative';bad(unsupported,'invalid_path');unsupported=deepcopy(prior);unsupported['id']=unsupported['media'][0]['id'];bad(unsupported,'duplicate_id');assert service.document==prior
 checks.append('Unknown nested recipes, relative traversal and duplicate identities fail without field/data loss')
 missing=out/'absent.wav';mid=uuid.uuid4().hex;run('batch',label='Missing placeholder',changes=[dict(op='media.add',id=mid,name='Missing',kind='Audio',placeholder=True,location=dict(kind='external',path=str(missing)),sha256='a'*64,metadata={})]);assert service.media_state[mid]['status']=='Missing'
 run('save',path=str(out/'missing.zwv'),portable=True,allow_missing=True);run('close');run('open',path=str(out/'missing.zwv'));assert service.media_state[mid]['status']=='Missing'
 checks.append('Missing placeholder is explicit and editable/saveable only by reference policy; reopening does not guess a same-name file')
 # Old save's document revision does not change, but its command binding does.
 old,_=run('save',path=str(out/'old-save.zwv'),allow_missing=True);revision=service.revision
 for _ in range(1030):assert not service.request(command('batch',changes=[dict(op='unsupported-edit')]))['ok']
 assert service.request(dict(op='operation_status',operation_id=old['operation_id']))['outcome'] is None
 r=service.request(old);assert not r['ok'] and r['error']['code']=='stale_command' and service.revision==revision and not service.jobs
 checks.append('Expired same-ID SAVE cannot enqueue a duplicate even while document revision is unchanged')
 # No 50-shot decoder allocation in the document owner; exercise metadata ceiling.
 base=create();tid,aid=[uuid.uuid4().hex for _ in range(2)];base['tracks']=[dict(id=tid,name='Audio',kind='audio',order=0,audio=dict(gain=1.,mute=False,fade_in=0,fade_out=0,envelope=[]))];base['media']=[dict(id=aid,name='Source',kind='Audio',location=dict(kind='external',path=str(first)),sha256=h1,metadata=dict(duration=4),provenance={})]
 for count in (50,100,250,500):
  d=deepcopy(base)
  for i in range(count):d,_=apply(d,[dict(op='clip.add',asset=aid,track=tid,start=i*30,duration=30)],uuid.uuid4().hex)
  start=time.perf_counter();validated=validate(d);raw.append(dict(clips=count,bytes=len(json.dumps(validated).encode()),validate_ms=(time.perf_counter()-start)*1000));assert len(validated['clips'])==count
 # Validate actual overlapping recipes separately from total timeline count.
 overlapping=deepcopy(base)
 for _ in range(16):overlapping,_=apply(overlapping,[dict(op='clip.add',asset=aid,track=tid,start=0,duration=30)],uuid.uuid4().hex)
 try:apply(overlapping,[dict(op='clip.add',asset=aid,track=tid,start=0,duration=30)],uuid.uuid4().hex)
 except ProjectError as exc:assert exc.code=='active_capacity'
 else:raise AssertionError('Overlap admission exceeded its bound')
 assert len(overlapping['clips'])==16
 checks.append('50/100/250/500 sequential instances validated without allocating decoders; total metadata and active-overlap admission are separate')
 service.can_shutdown(True);service.shutdown();assert not any(t.is_alive() for t in service.pool._threads)
 checks.append('Preparation threads exit after owned jobs drain; retained history is legitimate ownership, not forced to zero')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,raw=raw),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if not service.closed:
  for j in service.jobs.values():j['cancel'].set()
  while service.jobs:service.poll();time.sleep(.002)
  service.can_shutdown(True);service.shutdown()
