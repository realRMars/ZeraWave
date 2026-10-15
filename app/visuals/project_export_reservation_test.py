"""Real owner admission/history with controlled held exports; no output mutation."""
from pathlib import Path
from copy import deepcopy
import sys,os,json,hashlib,threading,time,uuid,shutil,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ['ZERAWAVE_ARTWORK_STORE']=str(out/'artwork')
import project_export,project_service
from project_service import ProjectService
checks=[];source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app/audio','app/visuals') for p in (ROOT/folder).glob('*.py')};(out/'SOURCE.json').write_text(json.dumps(source,indent=2),'utf8');s=ProjectService();release=threading.Event();entered=threading.Event();original_export=project_export.export_project;original_prepare=project_service.prepare_changes;prep_release=threading.Event();prep_entered=threading.Event()
def fake(doc,*args,**kw):entered.set();release.wait(15);raise ValueError('Controlled held export without publication')
def data(op,**args):
 state=s.state();return dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['project_id'],expected_command=state['command_revision'],**args)
def run(op,wait=True,**args):
 r=s.request(data(op,**args));key=r['outcome']['id'];end=time.perf_counter()+12
 while wait and key in s.jobs and time.perf_counter()<end:s.poll();time.sleep(.003)
 return deepcopy(s.outcomes[key])
def drain():
 end=time.perf_counter()+12
 while s.jobs and time.perf_counter()<end:s.poll();time.sleep(.003)
 assert not s.jobs
try:
 destination=out/'prior-good.mp4';shutil.copy2(ROOT/'work/video-editor-20261013-1791942063889153000/increment-E/checks-1792015309912662300/export/frozen.mp4',destination);prior=hashlib.sha256(destination.read_bytes()).hexdigest();alias=out/'alias.mp4';os.link(destination,alias);other=out/'other.mp4';shutil.copy2(destination,other);run('new');t=uuid.uuid4().hex;assert run('batch',changes=[dict(op='track.add',id=t,kind='graphics'),dict(op='caption.add',track=t,start=0,duration=30,text='Reserved')])['status']=='accepted';project_export.export_project=fake
 e=run('export',wait=False,path=str(destination));assert entered.wait(2);before=deepcopy(s.document)
 for path in (destination,alias):
  for edit in (dict(op='media.add',name='Pending output',kind='Video',location=dict(kind='external',path=str(path))),dict(op='project.protect',paths=[str(path)]),dict(op='media.add',name='Safe media but protected provenance',kind='Video',location=dict(kind='external',path=str(other)),provenance=dict(original_path=str(path)))):
   r=run('batch',changes=[edit]);assert r['status']=='rejected' and r['error']['code']=='reserved_destination',r;assert s.document==before
 assert run('batch',changes=[dict(op='project.rename',name='Unrelated edit permitted')])['status']=='accepted';after=deepcopy(s.document);assert run('undo')['status']=='accepted' and s.document==before;assert run('redo')['status']=='accepted' and s.document==after;checks.append('Exact destination/hardlink and import/protect/provenance conflicts reject atomically; unrelated edits and exact Undo/Redo remain available')
 release.set();drain();assert hashlib.sha256(destination.read_bytes()).hexdigest()==prior
 # Protect destinations retained only in redo history.
 assert run('batch',changes=[dict(op='media.add',name='Prior output',kind='Video',location=dict(kind='external',path=str(destination)))])['status']=='accepted';run('undo');assert not s.document['media'];r=run('export',path=str(destination));assert r['status']=='rejected' and r['error']['code']=='protected_source';checks.append('Export cannot overwrite a source retained only in Undo/Redo history')
 # An edit accepted for preparation before export must settle first.
 def slow_prepare(changes,base,cancel):prep_entered.set();prep_release.wait(10);return original_prepare(changes,base,cancel)
 project_service.prepare_changes=slow_prepare;pending=run('batch',wait=False,changes=[dict(op='media.add',name='Pending source',kind='Video',location=dict(kind='external',path=str(other)))]);assert prep_entered.wait(2);r=run('export',wait=False,path=str(out/'new.mp4'));assert r['status']=='rejected' and r['error']['code']=='busy';prep_release.set();drain();project_service.prepare_changes=original_prepare;checks.append('Preexisting source preparation blocks export admission until actual commit/exit; pending prepared destination cannot escape reservation')
 # Recheck at async commit if a new hardlink alias appears AFTER preflight.
 race=out/'race.mp4';shutil.copy2(other,race);release.clear();entered.clear();run('export',wait=False,path=str(race));assert entered.wait(2);prep_entered.clear();prep_release.clear();project_service.prepare_changes=slow_prepare;fresh=out/'changed-alias.mp4';shutil.copy2(other,fresh);saved=deepcopy(s.document);r=run('batch',wait=False,changes=[dict(op='media.add',name='Becomes alias',kind='Video',location=dict(kind='external',path=str(fresh)))]);assert prep_entered.wait(2);fresh.unlink();os.link(race,fresh);prep_release.set();end=time.perf_counter()+8
 while r['id'] in s.jobs and time.perf_counter()<end:s.poll();time.sleep(.003)
 outcome=s.outcomes[r['id']];assert outcome['status']=='failed' and outcome['error']['code']=='reserved_destination' and s.document==saved;release.set();drain();checks.append('Actual async import preparation/commit alias race rejects before owner installation while export remains pinned')
 assert hashlib.sha256(destination.read_bytes()).hexdigest()==prior and all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in source.items());(out/'RESULT.json').write_text(json.dumps(dict(result='PASS',checks=checks,source_unchanged=True,classification=__doc__),indent=2),'utf8');print('PASS reservation',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 release.set();prep_release.set();drain();s.shutdown();project_export.export_project=original_export;project_service.prepare_changes=original_prepare
