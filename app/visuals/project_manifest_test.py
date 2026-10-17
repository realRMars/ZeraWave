"""Real existing Studio API/helper with bounded synthetic transport supplements."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,uuid,traceback,subprocess,shutil,threading,queue
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);inputs=Path(sys.argv[2]);narration=inputs.parent/'narration-48017.wav';os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_PROJECT_TEST_WRITE_FAILURE=str(out/'write-failure.flag'))
from studio_control_client import ControlClient
from project_api import call,MAX_BYTES
from project_cli import request as cli
import project_manifest as pm
checks=[];samples=[];client=None;manifest=None
def state():return pm.read_state(endpoint)
def op(action,**values):
 s=state();r=cli(endpoint,dict(op=action,operation_id=uuid.uuid4().hex,**pm.binding(s),**values));assert r.get('ok'),r;return r
def run(plan,name,**kw):
 folder=out/name
 with pm.journal_lock(folder):
  j=pm.Journal(folder,plan);result=pm.apply_plan(endpoint,j,**kw)
 return result,j
def resume(name,**kw):
 folder=out/name
 with pm.journal_lock(folder):
  j=pm.Journal(folder);result=pm.apply_plan(endpoint,j,**kw)
 return result,j
def base():
 s=state();ns=uuid.uuid4().hex;media=[]
 for key,kind,path in [('shot','Video',inputs/'Shot-1.mp4'),('narration','Audio',narration),('still','Image',inputs/'Still.png')]:media.append(dict(key=key,name=key,kind=kind,path=str(path.resolve()),sha256=pm.file_hash(path)))
 ref=lambda s:dict(ref=s)
 return dict(format=pm.FORMAT,version=1,id=ns,project_id=s['project_id'],settings=deepcopy(s['document']['settings']),media=media,sections=[dict(key='routing',label='Workflow: named tracks and bus',items=[dict(category='buses',key='mix',values=dict(name='Mix',gain=.8)),dict(category='tracks',key='picture',values=dict(name='Picture',kind='video',order=0)),dict(category='tracks',key='voice',values=dict(name='Voice',kind='audio',order=1,output=ref('buses:mix'))),dict(category='tracks',key='text',values=dict(name='Captions',kind='graphics',order=2))]),dict(key='sequence',label='Workflow: editable sequence',items=[dict(category='clips',key='picture',values=dict(asset=ref('media:shot'),track=ref('tracks:picture'),start=0,duration=360)),dict(category='clips',key='voice',values=dict(asset=ref('media:narration'),track=ref('tracks:voice'),start=0,duration='natural',audio=dict(gain=.734,fade_in=0,fade_out=0,pan=-.123,envelope=[[0,1.],[30,1.]]))),dict(category='captions',key='cue',values=dict(track=ref('tracks:text'),start=0,duration=360,text='Editable — 测试'))])],save=dict(path=str((out/'assembled.zwv').resolve()),portable=True))
def next_caption(key):
 m=deepcopy(manifest);m['sections'].append(dict(key=key,label='Section '+key,items=[dict(category='captions',key=key,values=dict(track=dict(ref='tracks:text'),start=0,duration=30,text=key))]));return m
try:
 client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);op('new',name='Manifest test',settings=dict(width=1920,height=1080,fps=[30,1]));manifest=base();initial=state();plan=pm.compile_plan(endpoint,manifest);assert pm.stamp(state())==pm.stamp(initial) and len(plan['steps'])==4 and [r['action'] for r in plan['sources']]==['create']*3;assert all(s['change_count']<=128 and s['wire_bytes']==pm.wire_bytes(endpoint,s['request'])<=MAX_BYTES for s in plan['steps']);assert all(pm.stable(manifest['id'],cat,key)==i for name,i in plan['ids'].items() for cat,key in [name.split(':',1)])
 (out/'PLAN.json').write_text(json.dumps(plan,indent=2),encoding='utf8');checks.append('Read-only dry plan names owner/project,sources,deterministic entities,sections/Undo,actualUTF8 envelope+auth+newline bytes; no accepted command')
 result,j=run(plan,'partial',stop_after=1);assert result['status']=='partial' and len(state()['document']['media'])==3 and not state()['document']['clips'];partial=state();op('batch',label='Manual work between sections',changes=[dict(op='project.rename',name='Manual name retained')]);manual=state()['document']
 try:resume('partial');raise AssertionError('Rebased manual edit')
 except pm.Conflict:pass
 assert state()['document']==manual and len(state()['document']['media'])==3
 plan=pm.compile_plan(endpoint,manifest);assert all(a['action']=='reuse' for a in plan['sources']);result,j=run(plan,'replanned');assert result['status']=='complete';assembled=state()['document'];assert len(assembled['media'])==3 and len(assembled['clips'])==2 and assembled['name']=='Manual name retained';assert next(c for c in assembled['clips'] if c['id']==plan['ids']['clips:voice'])['duration']==31;assert assembled['tracks'][1]['output']==plan['ids']['buses:mix'];op('undo');undone=state()['document'];assert not undone['clips'] and not undone['captions'];op('redo');assert state()['document']==assembled
 checks.append('Partial media acceptance/manual command stops dependent sections; explicit new plan reuses3Ready identities,no duplicate sources; named section exact UndoRedo,natural31frame audio/fractions/bus route')
 plan=pm.compile_plan(endpoint,manifest);assert len(plan['steps'])==1 and all(r['action']=='already applied' for r in plan['entities']);run(plan,'checkpoint');saved=state()['document'];op('close');op('open',path=manifest['save']['path']);assert state()['document']['clips']==saved['clips'] and state()['document']['buses']==saved['buses'];checks.append('Stable-ID rerun identifies all applied entities; only pinned normal portable Save remains; actual-owner Close/Open retains editable media/clips/buses')
 # Fresh plans after reopen bind its new epoch explicitly; no silent rebase.
 m=next_caption('before');plan=pm.compile_plan(endpoint,m);calls=[]
 def lost_before(ep,request):
  calls.append(deepcopy(request))
  if request['op']=='batch':raise RuntimeError('Controlled lost response before transport admission')
  return call(ep,request)
 prior=pm.stamp(state())
 try:run(plan,'lost-before',send=lost_before);raise AssertionError('No uncertainty')
 except pm.Uncertain:pass
 assert pm.stamp(state())==prior;result,j=resume('lost-before');assert result['status']=='complete';assert j.value['records'][0]['request']==calls[0];manifest=m
 checks.append('Controlled lost reply before send: exact request/ID/hash/binding fsynced first; same pre-command boundary permits exact replay,one accepted item')
 m=next_caption('after');plan=pm.compile_plan(endpoint,m);sent=[]
 def lost_after(ep,request):
  sent.append(deepcopy(request));r=call(ep,request)
  if request['op']=='batch':raise RuntimeError('Controlled lost reply after real owner acceptance')
  return r
 try:run(plan,'lost-after',send=lost_after);raise AssertionError('No uncertainty')
 except pm.Uncertain:pass
 revision=state()['revision'];result,j=resume('lost-after');assert result['status']=='complete' and state()['revision']==revision;assert len(state()['document']['captions'])==3;manifest=m;exact=sent[0];assert call(endpoint,exact)['outcome']['revision']==revision;bad=deepcopy(exact);bad['label']='Different content sameID';r=call(endpoint,bad);assert not r['ok'] and r['error']['code']=='operation_conflict'
 checks.append('Controlled lost reply after actual acceptance: same-ID status confirms once,no duplicate revision/items; exact replay safe,changed payload conflicts')
 m=next_caption('unknown');plan=pm.compile_plan(endpoint,m)
 try:run(plan,'unknown',send=lost_after);raise AssertionError('No uncertainty')
 except pm.Uncertain:pass
 accepted=state()['document'];sends=[]
 def unknown(ep,request):
  sends.append(request['op'])
  return dict(ok=False,outcome=None,error=dict(code='outcome_unknown')) if request['op']=='operation_status' else call(ep,request)
 try:resume('unknown',send=unknown);raise AssertionError('Unknown outcome assumed rejected')
 except pm.Uncertain:pass
 assert sends==['operation_status'] and state()['document']==accepted;manifest=m;plan=pm.compile_plan(endpoint,manifest);assert len(plan['steps'])==1;run(plan,'unknown-explicit-new-plan');checks.append('Controlled unknown/retired detailed result with advanced actual command boundary blocks resubmission; explicit new plan recognizes accepted entity,no duplicate; natural1024-retention behavior reused from existing owner test')
 plan=pm.compile_plan(endpoint,manifest);before=state();request=deepcopy(plan['steps'][0]['request'])
 for field,badvalue in [('expected_epoch',uuid.uuid4().hex),('expected_project',uuid.uuid4().hex),('expected_revision',before['revision']-1),('expected_command',before['command_revision']-1)]:
  d=deepcopy(request);d[field]=badvalue;d['operation_id']=uuid.uuid4().hex;r=call(endpoint,d);assert not r['ok'] and state()['document']==before['document']
 checks.append('Actual owner rejects stale epoch,project,revision and command; accepted document retained')
 # A user's edit is a conflict, never implicit regeneration.
 cue=pm.stable(manifest['id'],'captions','cue');op('batch',label='Manual caption override',changes=[dict(op='caption.edit',id=cue,values=dict(text='Manual words'))]);manual=deepcopy(state()['document'])
 try:pm.compile_plan(endpoint,manifest);raise AssertionError('Manual override erased')
 except pm.Conflict:pass
 assert state()['document']==manual
 edits=deepcopy(manifest);edits['sections'][1]['items']=[r for r in edits['sections'][1]['items'] if r['category']!='captions'];row=next(r for r in manual['captions'] if r['id']==cue);edits['sections'].append(dict(key='deliberate',label='Deliberate guarded caption edit',items=[],edits=[dict(change=dict(op='caption.edit',id=cue,values=dict(text='Deliberately replaced')),expect=pm.digest(row))]));plan=pm.compile_plan(endpoint,edits);run(plan,'guarded-edit');assert next(r for r in state()['document']['captions'] if r['id']==cue)['text']=='Deliberately replaced';checks.append('Manual override blocks regeneration; deliberate idempotent setter requires exact prior entity hash and is an ordinary named owner edit')
 # Missing/changed/malformed plans do not submit any commands.
 base_state=pm.stamp(state());bad=deepcopy(edits);bad['media'][0]['path']=str((out/'missing.mp4').resolve())
 for invalid in [bad,dict(edits,version=2),dict(edits,sections=[dict(key='recipe',label='Unsupported',items=[],recipes=[dict(kind='unknown')])])]:
  try:pm.compile_plan(endpoint,invalid);raise AssertionError('Invalid plan accepted')
  except (ValueError,OSError):pass
  assert pm.stamp(state())==base_state
 changed=out/'changed.png';shutil.copyfile(inputs/'Still.png',changed);wrong=deepcopy(edits);wrong['media'][2]['path']=str(changed);changed.write_bytes(b'not original')
 try:pm.compile_plan(endpoint,wrong);raise AssertionError('Changed hash accepted')
 except ValueError:pass
 assert pm.stamp(state())==base_state;checks.append('Missing/changed source,malformed version and unsupported recipe block read-only planning; no accepted work lost')
 later=out/'changed-after-plan.png';shutil.copyfile(inputs/'Still.png',later);m=deepcopy(edits);m['media'].append(dict(key='later',name='Later',kind='Image',path=str(later.resolve()),sha256=pm.file_hash(later)));plan=pm.compile_plan(endpoint,m);later.write_bytes(b'Changed after dry-run')
 try:run(plan,'changed-after-plan');raise AssertionError('Changed planned source submitted')
 except pm.Conflict:pass
 assert pm.stamp(state())==base_state;checks.append('Source identity signals rechecked before every deliberate send; changed bytes after a dry-run block submission and retain prior accepted sections')
 # More than128 independent safe items; valid document remains below its cap.
 bulk=deepcopy(edits);bulk['sections'].append(dict(key='bulk',label='Bulk bounded captions',items=[dict(category='captions',key='bulk'+str(i),values=dict(track=dict(ref='tracks:text'),start=i,duration=1,text='b'+str(i))) for i in range(130)]));plan=pm.compile_plan(endpoint,bulk);parts=[r for r in plan['steps'] if r['section']=='bulk'];assert [p['change_count'] for p in parts]==[128,2] and all('part' in p['request']['label'] for p in parts);run(plan,'bulk');checks.append('Actual130-entity section splits128+2 at safe boundaries; each part has named Undo, no cross-part atomicity claim')
 # Lower only the planner's TEST envelope ceiling to force byte-first splitting
 # on real ordinary commands. Product512KiB/server/client constants are unchanged.
 tiny=deepcopy(bulk);tiny['sections'].append(dict(key='utf8',label='UTF8 byte parts',items=[dict(category='captions',key='utf'+str(i),values=dict(track=dict(ref='tracks:text'),start=i,duration=1,text='测'*100)) for i in range(10)]))
 with patch.object(pm,'MAX_BYTES',1600):
  plan=pm.compile_plan(endpoint,tiny);parts=[r for r in plan['steps'] if r['section']=='utf8'];assert len(parts)>1 and all(p['wire_bytes']<=1600 and p['change_count']<128 for p in parts)
 assert pm.MAX_BYTES==MAX_BYTES==524288;run(plan,'utf8-byte-parts');checks.append('Controlled lower1600-byte planner gate proves byte-first UTF8/auth/newline splitting before128edits; actual product cap remains524288 and all real requests measured')
 # Strict size arithmetic at the literal production boundary, without claiming
 # these deliberately oversized dummy fields are valid document edits.
 r=deepcopy(plan['steps'][0]['request']);r['padding']='';n=MAX_BYTES-pm.wire_bytes(endpoint,r);r['padding']='x'*n;assert pm.wire_bytes(endpoint,r)==MAX_BYTES;r['padding']+='x';assert pm.wire_bytes(endpoint,r)==MAX_BYTES+1
 token=json.loads(endpoint.read_text())['token'];assert all(token not in p.read_text(encoding='utf8') for p in out.rglob('journal.json'));checks.append('Literal524288/524289 wire arithmetic includes newline; endpoint token never retained in plan/journals; one ordered client')
 # A durable save failure retains accepted work and a new explicit checkpoint
 # can recover; same failed ID is never silently cloned by resume.
 good=Path(tiny['save']['path']);goodhash=pm.file_hash(good);(out/'write-failure.flag').write_text('controlled');plan=pm.compile_plan(endpoint,tiny)
 try:run(plan,'failed-save');raise AssertionError('Write failure not reported')
 except pm.Conflict:pass
 assert pm.file_hash(good)==goodhash;(out/'write-failure.flag').unlink();plan=pm.compile_plan(endpoint,tiny);run(plan,'save-recovered');checks.append('Actual controlled write failure protects last good checkpoint/accepted edits; explicit new pinned checkpoint succeeds in same owner')
 # Journal CAS and lock protect later task edits; no live document rollback.
 plan=pm.compile_plan(endpoint,tiny);folder=out/'journal-guard'
 with pm.journal_lock(folder):
  j=pm.Journal(folder,plan);j.path.write_text(j.path.read_text()+' ',encoding='utf8')
  try:j.save();raise AssertionError('Overwrote later journal edit')
  except pm.Conflict:pass
 checks.append('Journal guarded atomic replacement refuses later edits; accepted document remains owner-controlled')
 script=root/'app/visuals/project_manifest_cli.py';mf=out/'cli-manifest.json';mf.write_text(json.dumps(tiny),encoding='utf8');pf=out/'cli-plan.json'
 def invoke(*args):
  r=subprocess.run([sys.executable,'-B','-X','utf8',str(script),'--endpoint',str(endpoint),*map(str,args)],capture_output=True,text=True,encoding='utf8');(out/('cli-'+str(time.time_ns())+'.log')).write_text(r.stdout+'\n'+r.stderr,encoding='utf8');return r
 r=invoke('--plan','--manifest',mf,'--plan-file',pf);assert r.returncode==0,r.stdout+r.stderr;op('batch',label='Manual work after dry-run',changes=[dict(op='project.rename',name='Between plan and Apply')]);before=state();r=invoke('--apply','--plan-file',pf,'--journal',out/'cli-old-journal');assert r.returncode==2 and pm.stamp(state())==pm.stamp(before)
 pf=out/'cli-plan-new.json';r=invoke('--plan','--manifest',mf,'--plan-file',pf);assert r.returncode==0;r=invoke('--apply','--plan-file',pf,'--journal',out/'cli-journal');assert r.returncode==0,r.stdout+r.stderr;r=invoke('--resume','--journal',out/'cli-journal');assert r.returncode==0,r.stdout+r.stderr;checks.append('Installed CLI dry-run saves exact plan; manual change before Apply blocks without recompiling; explicit new plan Apply/Resume secure pinned revision')
 # Supplement: existing owner-service + existing real socket facade, with a
 # worker-only preparation barrier. No product server or hook is added.
 from project_service import ProjectService,prepare_changes
 from project_api import Server
 svc=ProjectService();svc.request(dict(op='new',operation_id=uuid.uuid4().hex,**pm.binding(svc.state()),name='Delayed manifest',settings=dict(width=1920,height=1080,fps=[30,1])));q=queue.Queue(16);server=Server(q,out/'delayed-api');delayed=base();delayed['project_id']=svc.document['id'];delayed['save']['path']=str((out/'delayed.zwv').resolve());entered=threading.Event();release=threading.Event();observed=[];answer={}
 def slow(changes,base,cancel):
  if threading.current_thread().name.startswith('Video project preparation'):
   entered.set()
   while not release.wait(.002):
    if cancel.is_set():raise InterruptedError('Controlled test cancellation')
  return prepare_changes(changes,base,cancel)
 def helper():
  try:
   plan=pm.compile_plan(server.path,delayed)
   with pm.journal_lock(out/'delayed-journal'):answer['result']=pm.apply_plan(server.path,pm.Journal(out/'delayed-journal',plan))
  except BaseException:answer['error']=traceback.format_exc()
 try:
  with patch('project_service.prepare_changes',slow):
   thread=threading.Thread(target=helper,name='Manifest test client');thread.start();began=time.monotonic();held=None
   while thread.is_alive():
    assert time.monotonic()-began<35
    try:message=q.get(timeout=.002);message['_api_reply'].set_result(svc.request(message['data']['request']))
    except queue.Empty:pass
    svc.poll()
    if entered.is_set() and not release.is_set():
     if held is None:held=time.monotonic()
     observed.append(dict(revision=svc.revision,jobs=len(svc.jobs),statuses=[r['status'] for r in svc.outcomes.values()]));assert not svc.document['media'] and not svc.document['clips']
     if time.monotonic()-held>=.15:release.set()
   thread.join();assert not answer.get('error'),answer;assert answer['result']['status']=='complete' and len(observed)>1 and len(svc.document['media'])==3;checks.append('Controlled real worker delay through existing owner-service/socket components:preparation stays unaccepted,ordered helper awaits it,then dependent sections/save complete once')
 finally:
  release.set();server.close()
  for job in svc.jobs.values():job['cancel'].set()
  until=time.monotonic()+15
  while svc.jobs and time.monotonic()<until:svc.poll();time.sleep(.002)
  svc.shutdown()
 (out/'DELAY.json').write_text(json.dumps(dict(observed=observed,result=answer),indent=2),encoding='utf8');op('close');client.close();assert client.process.returncode==0 and not client.reader.is_alive() and not client.notifier.is_alive();(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,limits=plan['limits'],owner_exit=0,protocol_errors=client.protocol_error_count,unverified='No physical input,GPU,audio device/listening or broad playback gate; byte-first splitting uses a clearly lowered test gate plus literal production sizing. Controlled unknown result supplements prior real owner retirement evidence.'),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks),indent=2),encoding='utf8');raise
finally:
 (out/'write-failure.flag').unlink(missing_ok=True)
 if client and not client.closed:client.close(mode='discard',project_mode='discard')
