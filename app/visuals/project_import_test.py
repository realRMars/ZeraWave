"""Focused real preparation/owner tests; controlled cancellation is identified."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,uuid,threading,shutil,traceback
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from project_service import ProjectService,prepare_changes,read_project
from project_import import Progress,counts
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);inputs=Path(sys.argv[2]);os.environ['ZERAWAVE_PROJECT_RECOVERY']=str(out/'recovery');s=ProjectService();checks=[];samples=[]

def request(op,**values):
 d=dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s.epoch,expected_revision=s.revision,expected_project=s.document['id'] if s.document else None,expected_command=s.command_revision,**values);return d,s.request(d)
def settle(d):
 end=time.monotonic()+30
 while time.monotonic()<end:
  t=time.perf_counter();s.poll();samples.append((time.perf_counter()-t)*1000);row=s.outcomes[d['operation_id']]
  if row['status'] not in ('preparing','saving'):return deepcopy(row)
  time.sleep(.002)
 raise AssertionError('Owner did not settle')
def run(op,**values):
 d,r=request(op,**values);assert r['ok'],r;row=settle(d);assert row['status'] in ('accepted','durable'),row;return d,row
try:
 run('new',name='Import test');paths=[str((inputs/n).resolve()) for n in ('Shot-1.mp4','Music.wav','Still.png','Still.png')];before=deepcopy(s.document);began=time.perf_counter();d,row=run('import_media',paths=paths,label='Mixed references');elapsed=time.perf_counter()-began;assert counts(row['files'])==dict(accepted=3,skipped=1);assert len(s.document['media'])==3 and not s.document['clips'];assert [a['kind'] for a in s.document['media']]==['Video','Audio','Image'];assert [r['path'] for r in row['files']]==paths
 for a in s.document['media']:assert a['provenance']['import_path']==a['location']['path'] and len(a['sha256'])==64
 accepted=deepcopy(s.document);assert s.request(d)['outcome']==row and s.document==accepted;run('undo');assert s.document==before;run('redo');assert s.document==accepted
 checks.append('Mixed verified Video/Audio/Image + duplicate:3 accepted,1 skipped, exact order/provenance, zero clips, same-ID replay and exact Undo/Redo')
 rev=s.revision;_,row=run('import_media',paths=paths);assert counts(row['files'])==dict(reused=3,skipped=1) and s.document==accepted and s.revision==rev
 checks.append('Matching Ready identities reused, duplicate skipped, no new references/history')
 bad=out/'bad.wav';bad.write_bytes(b'corrupt audio');unsupported=out/'bad.txt';unsupported.write_text('unsupported');fresh=out/'fresh.png';shutil.copyfile(inputs/'Still.png',fresh)
 for invalid in (bad,unsupported):
  d,r=request('import_media',paths=[str(fresh),str(invalid)]);assert r['ok'];row=settle(d);assert row['status']=='failed' and [r['status'] for r in row['files']]==['not_accepted','failed'];assert s.document==accepted
 checks.append('Corrupt and unsupported mixed groups reject atomically; verified earlier row is explicitly not accepted')
 changed=out/'changed.png';shutil.copyfile(inputs/'Still.png',changed);run('import_media',paths=[str(changed)]);retained=deepcopy(s.document);changed.write_bytes(b'changed bytes');d,r=request('import_media',paths=[str(changed)]);row=settle(d);assert row['error']['code']=='changed_media' and s.document==retained
 run('undo');assert s.document==accepted
 checks.append('Changed recorded path identity rejected; existing reference/document retained; explicit Undo removes prior import')
 entered=threading.Event();release=threading.Event()
 def slow(changes,base,cancel):
  entered.set()
  while not release.wait(.002):
   if cancel.is_set():raise InterruptedError('Controlled slow import cancelled')
  return prepare_changes(changes,base,cancel)
 with patch('project_service.prepare_changes',slow):
  d,r=request('import_media',paths=[str(fresh),paths[0]]);assert r['ok'] and entered.wait(5);assert s.document==accepted
  s.poll();assert s.outcomes[d['operation_id']]['files'][0]['status']=='preparing';s.request(dict(op='cancel',operation_id=d['operation_id']));row=settle(d);assert row['error']['code']=='cancelled' and all(r['status']=='cancelled' for r in row['files']) and s.document==accepted;release.set()
 checks.append('Controlled delayed worker: visible preparing, cancellation before acceptance; prior accepted references/history intact')
 from concurrent.futures import Future
 pending=Future();s.jobs['test-full']=dict(kind='save',future=pending,cancel=threading.Event())
 # Guard the actual unchanged16-job admission without running extra decoders.
 for i in range(15):s.jobs['test-'+str(i)]=dict(s.jobs['test-full'])
 d,r=request('import_media',paths=paths);assert not r['ok'] and r['error']['code']=='busy';s.jobs.clear()
 from project_service import summary
 rows=[dict(path=str(i),status='queued') for i in range(128)];compact=summary(dict(files=rows,status='preparing'));assert len(compact['files'])==4 and compact['file_count']==128 and compact['files_truncated']==124 and compact['file_counts']==dict(queued=128)
 p=Progress();p.publish(rows);p.publish(rows[:1]);assert len(p.take())==1 and p.take() is None
 checks.append('Existing16-job guard and128-file input/summary bounds; one latest progress snapshot,4-row publication/full outcome separate')
 run('save',path=str(out/'portable.zwv'),portable=True);doc,rev,states,_=read_project(out/'portable.zwv',threading.Event());assert [a['id'] for a in doc['media']]==[a['id'] for a in accepted['media']] and all(a['status']=='Ready' for a in states.values()) and not doc['clips'];run('open',path=str(out/'portable.zwv'));assert s.document==doc
 checks.append('Normal pinned portable Save and owner reopen preserve stable references/hashes and zero clips')
 s.shutdown();assert all(not t.is_alive() for t in s.pool._threads)
 ordered=sorted(samples);report=dict(classification=__doc__,checks=checks,import_seconds=elapsed,owner_poll_ms=dict(count=len(samples),median=ordered[len(ordered)//2],p95=ordered[min(len(ordered)-1,int(len(ordered)*.95))],maximum=max(samples)),pool_workers=2,owner_jobs=16,import_paths_max=128,workers_exited=True);(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 release.set() if 'release' in locals() else None
 if not s.closed:s.shutdown()
