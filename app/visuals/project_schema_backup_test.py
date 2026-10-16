from pathlib import Path
from copy import deepcopy
import sys,time,json,threading,hashlib,os,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[]
from project_service import read_project,write_project,schema_backup
from video_project import apply,create,new_id,validate,ProjectError,VERSION
from media_registry import decode_image
source=Path(sys.argv[2]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cancel=threading.Event()
try:
 asset,track,clip=[new_id() for _ in range(3)];meta,_=decode_image(str(source),pixels=False);d,_=apply(create('Legacy upgrade'),[dict(op='media.add',id=asset,name='Marker',kind='Image',location=dict(kind='external',path=str(source)),sha256=sha(source),metadata=meta),dict(op='track.add',id=track,kind='video'),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=30)],new_id());d['version']=1;d.pop('buses',None);d.pop('master',None);d=validate(d);path=out/'legacy [literal].zwv';write_project(d,7,None,path,True,cancel);legacy_bytes=path.read_bytes();loaded,revision,states,_=read_project(path,cancel);assert revision==7 and all(s['status']=='Ready' for s in states.values())
 upgraded,_=apply(loaded,[dict(op='track.edit',id=track,values=dict(locked=True))],new_id());assert upgraded['version']==VERSION
 prior=os.environ.get('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE');os.environ['ZERAWAVE_PROJECT_TEST_WRITE_FAILURE']='1'
 try:
  try:write_project(upgraded,8,None,path,True,cancel)
  except OSError:pass
  else:raise AssertionError('Actual protected write failure did not occur')
 finally:
  if prior is None:os.environ.pop('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE',None)
  else:os.environ['ZERAWAVE_PROJECT_TEST_WRITE_FAILURE']=prior
 assert path.read_bytes()==legacy_bytes;checks.append('Controlled failure at the real atomic-write boundary retains exact prior schema1 bytes and accepted upgraded document')
 result=write_project(upgraded,8,None,path,True,cancel);backup=Path(result['schema_backup']);assert backup.parent==path.parent and backup.read_bytes()==legacy_bytes;old,old_revision,old_states,_=read_project(backup,cancel);new,new_revision,new_states,_=read_project(path,cancel);assert old_revision==7 and old['version']==1 and new_revision==8 and new['version']==VERSION and new['tracks'][0]['locked'];assert all(s['status']=='Ready' for s in old_states.values()) and all(s['status']=='Ready' for s in new_states.values());checks.append('Current-schema replacement first secures exact same-directory schema1 backup; both reopen with valid relative managed dependencies')
 # A real schema2 baseline also receives an exact backup before schema3.
 v2=deepcopy(loaded);v2['version']=2;v2.pop('buses',None);v2.pop('master',None);v2=validate(v2);path2=out/'schema2.zwv';write_project(v2,3,None,path2,True,cancel);v2_bytes=path2.read_bytes();v3,_=apply(v2,[dict(op='track.edit',id=track,values=dict(visible=False))],new_id());result2=write_project(v3,4,None,path2,True,cancel);assert Path(result2['schema_backup']).read_bytes()==v2_bytes and read_project(path2,cancel)[0]['version']==VERSION
 # Undo may restore an exact old document. A compatible current runtime saves
 # that requested revision with a protected backup of the newer-schema file.
 prior3=path2.read_bytes();undo_save=write_project(v2,5,None,path2,True,cancel);assert Path(undo_save['schema_backup']).read_bytes()==prior3 and read_project(path2,cancel)[0]['version']==2
 checks.append('Schema2-to-current and exact Undo-to-schema2 saves both protect prior bytes and relative dependencies')
 for name,raw in [('corrupt.zwv',b'not JSON'),('unsupported.zwv',json.dumps(dict(format='zerawave-video-project-file',version=1,revision=0,document=dict(new,unknown_future_content=True))).encode())]:
  target=out/name;target.write_bytes(raw)
  try:write_project(upgraded,8,None,target,True,cancel)
  except ProjectError:pass
  else:raise AssertionError('Unsupported existing destination overwritten')
  assert target.read_bytes()==raw
 checks.append('Corrupt and unknown-content existing destinations fail protected, without overwriting or discarding their bytes')
 try:schema_backup(path,'0'*64,cancel)
 except ProjectError as exc:assert exc.code=='destination_changed'
 else:raise AssertionError('Destination change accepted')
 assert sha(source)==d['media'][0]['sha256'];checks.append('Destination identity mismatch rejects, and the original source image remains unchanged')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,backup=str(backup),backup_sha256=sha(backup),project_sha256=sha(path),classification='Worker/pure persistence on disposable files; no native UI or physical timing claim'),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
