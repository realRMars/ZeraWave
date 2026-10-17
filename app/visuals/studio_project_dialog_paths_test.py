"""Noninteractive Qt dialog arguments,confirmed folder memory and real owner Save/Open.

No native foreground,picture export,playback or user-session takeover.
"""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import sys,os,json,time,traceback,wave,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);failure=out/'write-failure.flag';barrier=out/'save-barrier.flag';os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_TEST_WRITE_FAILURE=str(failure),ZERAWAVE_PROJECT_TEST_SAVE_BARRIER=str(barrier))
from PySide6.QtWidgets import QApplication,QFileDialog,QMessageBox
from studio_qt import Shell
from studio_project import ProjectWorkspace
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;checks=[];calls=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def wait(fn,seconds=35):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  app.processEvents();time.sleep(.002)
  if fn():return
 raise AssertionError('Owner/UI did not settle: '+w.notice.text())
def idle():
 wait(lambda:w.pending is None and shell.client.edit_count==0 and not w.transport_future and not w.transport_desired);w.refresh()
def snapshot():return dict(binding=w.binding(),document=deepcopy(w.state().get('document')),path=w.state().get('path'),saved=w.state().get('saved_revision'),prefs=deepcopy(shell.preferences),pending=w.pending,submissions=len(w.callback_samples))
def probe(method,expected,**kw):
 before=snapshot();picker='getOpenFileName' if method=='open' else 'getSaveFileName'
 with patch.object(QFileDialog,picker,return_value=('','')) as mock,patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
  getattr(w,method)(**kw);assert mock.call_count==1;args=mock.call_args.args;assert Path(args[2])==expected,(method,args,expected);calls.append(dict(action=method,start=args[2],filter=args[3],cancel=True))
 assert snapshot()==before,method+' cancel changed state/defaults or submitted work'
def close_shell():
 global shell
 shell.close();wait(lambda:shell.closing);assert shell.client.process.returncode==0 and w.exited();shell=None
try:
 # Memory admission is driven only by confirmed owner fields,not file selection.
 fake=SimpleNamespace(shell=SimpleNamespace(preferences={}));good_project=out/'project-a'/'A.zwv';exports=out/'exports';exports.mkdir();good_project.parent.mkdir()
 for status in ('preparing','saving','exporting','failed','rejected','accepted'):
  ProjectWorkspace.remember_dialog_folders(fake,dict(path=None,saved_revision=None,operations=[dict(id='not-durable',op='export',status=status,result=dict(path=str(exports/'never.mp4')))]));assert not fake.shell.preferences
 ProjectWorkspace.remember_dialog_folders(fake,dict(path=str(good_project),saved_revision=0,operations=[dict(id='done',op='export',status='exported',result=dict(path=str(exports/'finished.mp4')))]));assert fake.shell.preferences['video_dialog_folders']==dict(project=str(good_project.parent),export=str(exports));ProjectWorkspace.remember_dialog_folders(fake,dict(path=None,saved_revision=None,operations=[dict(id='failed-later',op='export',status='failed',result=dict(path=str(out/'wrong'/'failed.mp4')))]));assert fake.shell.preferences['video_dialog_folders']['export']==str(exports)
 checks.append('Synthetic owner-summary unit cases:only confirmed project path/saved revision and exported MP4 receipt promote folders;pending/failed/rejected/cancel-compatible states do not')
 shell=Shell(out/'layout.json',out/'owner-a.log');w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));assert not w.state().get('document');probe('open',root/'work');w.submit('new',name='Dialog paths',settings=dict(width=16,height=16));idle();probe('save',root/'work'/'video.zwv');probe('save',root/'work'/'video.zwv',save_as=True);checks.append('Fresh Open/new Save/SaveAs use existing root/work with original video.zwv suggestion;cancel leaves document,binding,preferences and operations exact')
 source=out/'source.wav'
 with wave.open(str(source),'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(b'\x00\x20'*4800)
 from video_project import new_id
 track=new_id();asset=new_id();clip=new_id();w.batch('Small disposable media',[dict(op='track.add',id=track,name='Audio',kind='audio'),dict(op='media.add',id=asset,name='Original',kind='Audio',location=dict(kind='external',path=str(source))),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=3)]);idle();initial=deepcopy(w.document());source_hash=sha(source)
 # Alternate selection remains the sole save destination;no sidecar/config write.
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(good_project),'')) as picker:w.save();assert picker.call_count==1
 idle();assert w.last_outcome['status']=='durable' and Path(w.state()['path'])==good_project and shell.preferences['video_dialog_folders']['project']==str(good_project.parent);assert w.document()==initial;before_hash=sha(good_project);probe('open',good_project.parent);probe('save',good_project.parent/'video.zwv',save_as=True);probe('export_video',good_project.parent/'video.mp4',crf=18);checks.append('Real chosen alternate new Save is durable;Open/SaveAs/first Export then start in its confirmed folder;artwork/history unchanged by dialogs')
 with patch.object(QFileDialog,'getSaveFileName',side_effect=AssertionError('Ordinary Save must not choose another path')):w.save()
 idle();assert Path(w.state()['path'])==good_project and sha(good_project)==before_hash
 target_b=out/'project-b'/'B.zwv';barrier.write_text('controlled delay');w.save(save_as=True,path=str(target_b));wait(lambda:any(o['id']==w.last_save and o['status']=='saving' for o in w.state().get('operations',[])));assert Path(w.state()['path'])==good_project and shell.preferences['video_dialog_folders']['project']==str(good_project.parent);barrier.unlink();idle();assert w.last_outcome['status']=='durable' and Path(w.state()['path'])==target_b and shell.preferences['video_dialog_folders']['project']==str(target_b.parent);assert sha(good_project)==before_hash and sha(source)==source_hash;checks.append('Ordinary Save targets current path without picker;pending SaveAs does not promote requested folder,then real durable alternate SaveAs does')
 failed=out/'failed-target'/'never.zwv';failure.write_text('controlled');prefs=deepcopy(shell.preferences['video_dialog_folders']);w.save(save_as=True,path=str(failed));idle();failure.unlink();assert w.last_outcome['status']=='failed' and not failed.exists() and Path(w.state()['path'])==target_b and shell.preferences['video_dialog_folders']==prefs;probe('open',target_b.parent);probe('save',target_b.parent/'video.zwv',save_as=True)
 bad=out/'bad-open'/'corrupt.zwv';bad.parent.mkdir();bad.write_text('not a project');w.open(path=str(bad));idle();assert w.last_outcome['status']=='failed' and Path(w.state()['path'])==target_b and shell.preferences['video_dialog_folders']==prefs;checks.append('Actual controlled write failure and corrupt Open retain confirmed current/default folders,accepted document and good prior checkpoint;nonexistent targets never promoted')
 with patch.object(QFileDialog,'getOpenFileName',side_effect=AssertionError('Explicit path must bypass chooser')):w.open(path=str(target_b))
 idle();opened=deepcopy(w.document());assert all(opened[k]==initial[k] for k in ('id','tracks','clips','captions','graphics','settings'));assert opened['media'][0]['sha256']==source_hash and sha(Path(opened['media'][0]['location']['path']))==source_hash;assert shell.preferences['video_dialog_folders']['project']==str(target_b.parent)
 with patch.object(QFileDialog,'getOpenFileName',return_value=(str(good_project),'')):w.open()
 idle();assert Path(w.state()['path'])==good_project and shell.preferences['video_dialog_folders']['project']==str(good_project.parent);w.open(path=str(target_b));idle();checks.append('Explicit paths bypass chooser;user-selected alternate Open and normal portable reopen retain IDs,managed media hashes and original source bytes')
 from project_cli import request as owner_request
 import uuid
 agent_project=out/'agent-review'/'Reviewed.zwv';response=owner_request(Path(w.state()['endpoint']),dict(op='save',operation_id=uuid.uuid4().hex,**w.binding(),path=str(agent_project),portable=True));assert response['ok'] and response['outcome']['status']=='durable';wait(lambda:w.state().get('path')==str(agent_project));w.refresh();assert w.pending is None and shell.preferences['video_dialog_folders']['project']==str(agent_project.parent);probe('open',agent_project.parent);w.open(path=str(target_b));idle();checks.append('Actual existing owner-API save without Qt pending updates observed successful folder;agent-created review project is reachable from ordinary Open default without relocating assets')
 # Export argument check ONLY:do not run a movie worker for a path-only change.
 shell.preferences['video_dialog_folders']['export']=str(exports);alternate=out/'chosen-export'/'other.mp4';before=snapshot()
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(alternate),'')) as picker,patch.object(w,'submit',return_value='synthetic-export-only') as submit:
  assert w.export_video(crf=21,range_frames=[0,3])=='synthetic-export-only';assert Path(picker.call_args.args[2])==exports/'video.mp4';assert submit.call_args.args==('export',) and submit.call_args.kwargs==dict(binding=before['binding'],path=str(alternate),crf=21,range=[0,3])
 assert snapshot()==before and not alternate.exists();probe('export_video',exports/'video.mp4',crf=18)
 with patch.object(w,'dialog',return_value=False),patch.object(QFileDialog,'getSaveFileName',side_effect=AssertionError('Cancelled quality dialog must not choose output')):w.export_video()
 assert snapshot()==before;checks.append('Synthetic Export chooser/request capture preserves actual selected path,quality/range/binding;file/quality Cancel changes nothing,no movie export executed')
 # Existing preferences file handles restart;no new settings UI or extra writer.
 close_shell();stored=json.loads((out/'layout.json').read_text());assert stored['controls']['video_dialog_folders']==dict(project=str(target_b.parent),export=str(exports));shell=Shell(out/'layout.json',out/'owner-b.log');w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));assert shell.preferences['video_dialog_folders']==dict(project=str(target_b.parent),export=str(exports));probe('open',target_b.parent);w.submit('new',name='Unstored new project');idle();probe('save',target_b.parent/'video.zwv');probe('save',target_b.parent/'video.zwv',save_as=True)
 original=deepcopy(shell.preferences['video_dialog_folders']);shell.preferences['video_dialog_folders']=dict(project=str(out/'missing'),export=17);assert w.dialog_directory('project')==root/'work' and w.dialog_directory('export')==root/'work';shell.preferences['video_dialog_folders']='malformed legacy value';assert w.dialog_directory('project')==root/'work';shell.preferences['video_dialog_folders']=original;w.submit('close',discard=True);idle();close_shell();checks.append('Normal isolated Qt layout persistence/restart restores both successful folders;new project reuses remembered location and unavailable/malformed preferences safely fall back without directory creation')
 (out/'DIALOG_ARGUMENTS.json').write_text(json.dumps(calls,indent=2),encoding='utf8');(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,owner_exits=[0,0],source_unchanged=sha(source)==source_hash,no_movie_export=True,native_dialogs='UNVERIFIED;all pickers are noninteractive Qt stubs,Robert live window untouched',first_fallback=str(root/'work')),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 failure.unlink(missing_ok=True);barrier.unlink(missing_ok=True)
 if shell and not shell.closing:
  shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
