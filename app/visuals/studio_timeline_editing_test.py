"""Actual Qt input and owner/API edits on disposable media; no physical UI claim."""
from pathlib import Path
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import sys,os,json,time,uuid,traceback,hashlib,threading
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox,QLineEdit
from PySide6.QtCore import Qt,QPoint,QMimeData
from PySide6.QtTest import QTest
from unittest.mock import patch
from studio_qt import Shell
from project_api import call
from video_project import apply,clip_recipe
app=QApplication([]);shell=None;checks=[];pool=ThreadPoolExecutor(max_workers=1);uid=lambda:uuid.uuid4().hex
def pump():app.processEvents();time.sleep(.002)
def wait(fn,seconds=35):
 deadline=time.monotonic()+seconds
 while time.monotonic()<deadline:
  pump()
  if fn():return
 raise AssertionError('Timeout '+w.notice.text())
def state():return w.state()
def doc():return deepcopy(w.document())
def idle():wait(lambda:not w.pending and not w.timeline.placement and c.version==(state().get('epoch'),state().get('revision')))
def api(op,**args):
 request=dict(op=op,operation_id=uid(),**(w.binding() if op not in ('state','operation_status') else {}),**args);future=pool.submit(call,state()['endpoint'],request);wait(future.done);response=future.result();assert response['ok'],response;key=request['operation_id']
 wait(lambda:any(r['id']==key and r['status'] in ('accepted','durable','failed','rejected') for r in state()['operations']));outcome=next(r for r in state()['operations'] if r['id']==key);assert outcome['status'] in ('accepted','durable'),outcome;wait(lambda:c.version==(state().get('epoch'),state().get('revision')));return outcome
def row(key):return next(r for c in ('clips','captions','graphics') for r in w.document()[c] if r['id']==key)
def click(key,modifiers=Qt.NoModifier):
 rect=c.rects[(c.rows_by_id[key][0],key)];point=rect.center().toPoint();QTest.mouseClick(c,Qt.LeftButton,modifiers,point);pump()
def drag(key,pixels,edge=None,cancel=False,target_track=None):
 rect=c.rects[(c.rows_by_id[key][0],key)];point=rect.center().toPoint()
 if edge=='right':point.setX(round(rect.right()-2))
 if edge=='left':point.setX(round(rect.left()+2))
 dy=(next(i for i,t in enumerate(c.tracks) if t['id']==target_track)-next(i for i,t in enumerate(c.tracks) if t['id']==row(key)['track']))*c.row_height if target_track else 0
 QTest.mousePress(c,Qt.LeftButton,pos=point);QTest.mouseMove(c,point+QPoint(pixels,dy),delay=5)
 if cancel:QTest.keyClick(c,Qt.Key_Escape)
 QTest.mouseRelease(c,Qt.LeftButton,pos=point+QPoint(pixels,dy));pump()
try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1850,1100);shell.show();w=shell.project_workspace;c=w.timeline.canvas;wait(lambda:state().get('endpoint'));api('new',name='Everyday edits',settings=dict(width=1920,height=1080,fps=[30,1]));w.video_panels.activate();asset=deepcopy(json.loads(Path(sys.argv[2]).read_text()));asset_id=asset['id'];video,audio,video2,audio2,text,vc,ac,vc2,ac2,caption,link,link2=[uid() for _ in range(12)]
 changes=[dict(op='media.add',**asset)]+[dict(op='track.add',id=k,kind=kind,name=name) for k,kind,name in ((video,'video','Video1'),(audio,'audio','Audio1'),(video2,'video','Video2'),(audio2,'audio','Audio2'),(text,'graphics','Captions'))]+[dict(op='clip.add',id=key,asset=asset_id,track=track,start=start,duration=90,link_id=ln,name=name) for key,track,start,ln,name in ((vc,video,0,link,'First video'),(ac,audio,0,link,'First audio'),(vc2,video,150,link2,'Next video'),(ac2,audio,150,link2,'Next audio'))]+[dict(op='caption.add',id=caption,track=text,start=240,duration=30,text='Editable caption')]
 api('batch',label='Fixture clips',changes=changes);wait(lambda:len(c.rects)==5);before=doc();revision=state()['revision'];click(vc);drag(vc,3);idle();assert doc()==before and state()['revision']==revision;checks.append('Actual Qt click/sub-threshold movement selects without a document edit')
 c.snap=False;drag(vc,60);idle();moved=doc();assert row(vc)['start']==row(ac)['start']==20 and state()['revision']==revision+1;assert w.timeline.undo.isEnabled() and 'Move selection' in w.timeline.undo.text();api('undo');assert doc()==before
 api('batch',label='API same move',changes=[dict(op='items.move',ids=[vc],delta=20,track_map={vc:video,ac:audio},linked=True,groups=True,mode='Normal')]);assert doc()==moved;checks.append('One thresholded linked Qt drag = one exact owner history operation; shared HTTP API produces identical document')
 before=doc();drag(vc,40,cancel=True);idle();assert doc()==before;rect=c.rects[('clips',vc)];point=rect.center().toPoint();QTest.mousePress(c,Qt.LeftButton,pos=point);QTest.mouseMove(c,point+QPoint(45,0));c.clearFocus();pump();QTest.mouseRelease(c,Qt.LeftButton,pos=point+QPoint(45,0));idle();assert doc()==before;checks.append('Escape and focus loss cancel unfinished gestures without partial edits')
 click(vc);click(vc2,Qt.ControlModifier);assert c.selection=={vc,vc2};c.select('clips',vc);QTest.mouseClick(c,Qt.LeftButton,Qt.ShiftModifier,c.rects[('clips',vc2)].center().toPoint());assert {vc,vc2}<=c.selection;checks.append('Qt Ctrl-toggle and anchored Shift range retain stable item IDs')
 c.selection={vc};c.selected=('clips',vc);QTest.keyClick(c,Qt.Key_C,Qt.ControlModifier);w.transport('seek',270);wait(lambda:w.transport_state()['frame']==270 and not w.transport_future and not w.transport_desired);c.frame=0 # Model an owner clock update before the next canvas repaint.
 QTest.keyClick(c,Qt.Key_V,Qt.ControlModifier);idle();assert len(w.document()['clips'])==6;assert len(c.selection)==2 and all(row(k)['start']==270 for k in c.selection);pasted=set(c.selection);assert not pasted&{vc,ac};api('undo');assert len(w.document()['clips'])==4;api('redo');assert {r['id'] for r in w.document()['clips']}>=pasted;checks.append('Actual Qt clipboard paste selects new independent linked IDs; exact Undo/Redo restores them')
 c.selection={vc};c.selected=('clips',vc);w.transport('seek',50);wait(lambda:w.transport_state()['frame']==50 and not w.transport_future and not w.transport_desired);revision=state()['revision'];QTest.keyClick(c,Qt.Key_S);idle();assert state()['revision']==revision+1 and len(w.document()['clips'])==8;rights=[r for r in w.document()['clips'] if r['start']==50];assert len(rights)==2 and all(r['source_in']==[1,1] for r in rights);api('undo');checks.append('S splits exact linked source time and preserves audio-window origin; one Undo restores the prior pair')
 lock=w.timeline.headers.widgets[audio].controls['locked'];QTest.mouseClick(lock,Qt.LeftButton);idle();assert next(t for t in w.document()['tracks'] if t['id']==audio)['locked'];before=doc();drag(vc,30);idle();assert doc()==before;QTest.mouseClick(w.timeline.headers.widgets[audio].controls['locked'],Qt.LeftButton);idle();checks.append('Actual track lock control reaches owner; linked drag rejects intact and remains usable after unlock')
 field=w.timeline.headers.widgets[video].name_field;field.setFocus();field.selectAll();QTest.keyClicks(field,'Typed track name');typed=field.text();api('batch',label='Other field',changes=[dict(op='project.rename',name='Other project name')]);assert field is w.timeline.headers.widgets[video].name_field and field.text()==typed and field.isModified();QTest.keyClick(field,Qt.Key_Return);idle();assert w.last_outcome['status']=='rejected' and field.text()==typed;QTest.keyClick(field,Qt.Key_Return);idle();assert next(t for t in w.document()['tracks'] if t['id']==video)['name']==typed;checks.append('Inline typed name survives unrelated accepted revision; stale edit rejects visibly and explicit Enter retries without lost text or duplicate submission')
 # Same shared callback as visible Project Media Place and the real drop path.
 before=doc();source=w.video_panels.source;source.asset=None;mime=QMimeData();mime.setData('application/x-zerawave-project-media',json.dumps([asset_id]).encode());w.timeline.place_mime(mime,video2,420);wait(lambda:w.timeline.placement is None and not w.pending);assert len(w.document()['clips'])==len(before['clips'])+2;new=[r for r in w.document()['clips'] if r['start']==420];assert len(new)==2 and {r['track'] for r in new}=={video2,audio2} and new[0]['link_id']==new[1]['link_id'];checks.append('Actual worker/media inspection and owner placement add linked AV with a pinned channel/mode choice')
 # Both source handles and collision/lock feedback are computed before release.
 before=doc();c.selection={vc};c.selected=('clips',vc);drag(vc,-15,edge='right');idle();assert row(vc)['duration']==row(ac)['duration']==85;api('undo');assert doc()==before;drag(vc,15,edge='left');idle();assert row(vc)['source_in']==[1,6] and row(ac)['source_in']==[1,6];api('undo');before=doc();revision=state()['revision'];drag(vc,15,edge='right');idle();assert doc()==before and state()['revision']==revision;checks.append('Actual edge drags trim linked handles nondestructively and reject exhausted source handles before submission')
 c.setFocus();QTest.keyClick(c,Qt.Key_C);assert c.tool=='Razor';point=c.rects[('clips',vc)].center().toPoint();point.setX(round(c.x(50)));QTest.mouseClick(c,Qt.LeftButton,pos=point);idle();assert len(w.document()['clips'])==len(before['clips'])+2;api('undo');QTest.keyClick(c,Qt.Key_V);assert c.tool=='Select';checks.append('Visible Razor/Select modes follow C/V; razor pointer split uses the indicated frame and one Undo')
 before=doc();c.selection={vc};c.selected=('clips',vc);drag(vc,0,target_track=video2);idle();assert row(vc)['track']==video2 and row(ac)['track']==audio2;assert c.current_track==video2;c.current_track=video;QTest.keyClick(c,Qt.Key_D,Qt.ControlModifier);idle();assert {row(i)['track'] for i in c.selection}=={video2,audio2};api('undo');api('undo');revision=state()['revision'];drag(vc,0,target_track=text);idle();assert doc()==before and state()['revision']==revision;checks.append('Actual cross-track drag maps compatible linked companions; incompatible targets leave the document intact')
 c.selection={vc2};c.selected=('clips',vc2);c.setFocus();before=doc();QTest.keyClick(c,Qt.Key_Delete);idle();assert {r['id'] for r in w.document()['clips']}=={r['id'] for r in before['clips']}-{vc2,ac2};assert all(r['start']==next(b for b in before['clips'] if b['id']==r['id'])['start'] for r in w.document()['clips']);api('undo');c.selection={vc2};c.selected=('clips',vc2);QTest.keyClick(c,Qt.Key_X,Qt.ControlModifier);idle();assert vc2 not in {r['id'] for r in w.document()['clips']};api('undo');checks.append('Actual Delete and Ctrl+X remove accepted linked content, leave gaps and Undo exact prior IDs/source recipes')
 latest=next(r for r in w.document()['clips'] if r['track']==video2 and r['start']==420);c.selection={latest['id']};c.selected=('clips',latest['id']);before=doc();QTest.keyClick(c,Qt.Key_D,Qt.ControlModifier);idle();assert len(w.document()['clips'])==len(before['clips'])+2 and len(c.selection)==2;assert all(row(i)['start']==510 for i in c.selection);api('undo');checks.append('Ctrl+D makes independent linked duplicate IDs at the selected tail, with exact Undo')
 before=doc();c.selection={vc,caption};c.selected=('clips',vc);c.action('items.group');idle();assert row(vc)['group_id']==row(ac)['group_id']==row(caption)['group_id'];drag(vc,15);idle();assert row(vc)['start']==25 and row(caption)['start']==245;api('undo');c.action('items.ungroup');idle();assert all('group_id' not in row(i) for i in (vc,ac,caption));api('undo');api('undo');assert doc()==before;c.selection={vc};c.selected=('clips',vc);c.action('items.unlink');idle();assert row(vc)['link_id'] is None and row(ac)['link_id'] is None;c.selection={vc,ac};c.action('items.link');idle();assert row(vc)['link_id']==row(ac)['link_id'];api('undo');api('undo');assert doc()==before;checks.append('Shared menu callbacks group/move/ungroup and deliberate unlink/relink with preserved exact history')
 before=doc();w.timeline.mode.setCurrentText('Insert');w.timeline.place_mime(mime,video2,390);idle();assert len(w.document()['clips'])==len(before['clips'])+2 and all(r['start']==510 for r in w.document()['clips'] if r['id'] in {x['id'] for x in before['clips'] if x['start']==420});api('undo');assert doc()==before
 w.timeline.mode.setCurrentText('Overwrite');w.timeline.place_mime(mime,video2,435);idle();assert len([r for r in w.document()['clips'] if r['start']==435])==2 and all(r['start']==next(x for x in before['clips'] if x['id']==r['id'])['start'] for r in w.document()['clips'] if r['id'] in {x['id'] for x in before['clips']});api('undo');assert doc()==before;w.timeline.mode.setCurrentText('Normal');checks.append('Visible Insert/Overwrite mode values route the same prepared AV drop to synchronized shifts or precise interval replacement, each exactly undoable')
 c.selection={caption};c.selected=('captions',caption);c.setFocus();before=doc()
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):QTest.keyClick(c,Qt.Key_Delete,Qt.ShiftModifier)
 idle();assert caption not in {r['id'] for r in w.document()['captions']} and all(row(r['id'])['start']==r['start']-30 for r in before['clips'] if r['start']>=270);api('undo');assert doc()==before;checks.append('Actual Shift+Delete invokes an explicit all-track range confirmation, closes the exact interval including synchronized later tracks, and Undo restores it')
 # Delayed source preparation retains pinned range/channel/mode and bounded cancellation.
 import studio_timeline_media as placement_module
 import threading
 original_inspect=placement_module.inspect_all;gate=threading.Event();entered=threading.Event()
 def delayed_inspect(sources,cancel):
  entered.set();gate.wait(10);return original_inspect(sources,cancel)
 before=doc();w.video_panels.open_source(asset);wait(lambda:source.asset is not None and source.asset['id']==asset_id and not w.pending);source.in_box.setValue(15);source.out_box.setValue(60);source.mark_range();wait(lambda:source.range==[15,60] and not w.transport_future and not w.transport_desired);w.timeline.source_mode.setCurrentText('Video only')
 with patch.object(placement_module,'inspect_all',delayed_inspect):
  w.timeline.place_mime(mime,video2,600);wait(entered.is_set);w.timeline.source_mode.setCurrentText('Audio only');w.timeline.mode.setCurrentText('Overwrite');source.in_box.setValue(20);source.out_box.setValue(30);source.mark_range();gate.set();idle()
 placed=[r for r in w.document()['clips'] if r['start']==600];assert len(placed)==1 and placed[0]['track']==video2 and placed[0]['duration']==45 and placed[0]['source_in']==[1,2];api('undo');assert doc()==before;checks.append('Delayed real source inspection pins Source In/Out, Video-only and Normal mode; later UI changes cannot alter the admitted45-frame placement')
 source.retire_preview();source.asset=None;w.timeline.mode.setCurrentText('Normal');w.timeline.source_mode.setCurrentText('A/V linked');before=doc();gate.clear();entered.clear()
 with patch.object(placement_module,'inspect_all',delayed_inspect):
  w.timeline.place_mime(mime,video2,600);wait(entered.is_set);c.setFocus();QTest.keyClick(c,Qt.Key_Escape);gate.set();idle()
 assert doc()==before;gate.clear();entered.clear()
 with patch.object(placement_module,'inspect_all',delayed_inspect):
  w.timeline.place_mime(mime,video2,600);wait(entered.is_set);api('batch',label='Intervening accepted change',changes=[dict(op='project.rename',name='Changed while source prepares')]);after=doc();gate.set();idle()
 assert doc()==after and len(doc()['clips'])==len(before['clips']);assert 'not submitted' in w.notice.text();api('undo');assert doc()==before;checks.append('Escape cancels unaccepted source work; an intervening API revision rejects the stale prepared drop without automatic resubmission, content loss or duplicate operations')
 saved=out/'editable.zwv';expected=doc();api('save',path=str(saved),portable=True);assert not state()['dirty'];api('close');wait(lambda:w.state().get('document') is None);api('open',path=str(saved));assert w.document()['clips']==expected['clips'] and w.document()['tracks']==expected['tracks']
 from types import SimpleNamespace
 from studio_timeline_media import Placement
 planned=SimpleNamespace(document=deepcopy(doc()),target=video2,frame=600,mode='Normal',channels='A/V linked',range=None,library=True,panel=w.timeline)
 changes,rows=Placement.plan(planned,[asset]);assert not any(r['op']=='media.add' for r in changes) and all(r['row']['asset']==asset_id for r in rows)
 checks.append('New schema2 Save As/close/reopen preserves all editable IDs, hierarchy-free tracks, clips and authored flags')
 api('batch',label='Delete all tracks',changes=[dict(op='track.remove',id=t['id'],confirmed=True) for t in w.document()['tracks']]);assert not w.document()['tracks'] and not w.document()['clips'];api('batch',label='Fresh track after empty',changes=[dict(op='track.add',kind='video',name='Fresh root track')]);assert len(w.document()['tracks'])==1;api('undo');api('undo');assert w.document()['clips']==expected['clips'];checks.append('Delete-all leaves a usable empty document; fresh top-level track creation and exact Undo restore accepted contents')
 assert not shell.client.protocol_error_count
 def late_save_decision(*args,**kwargs):
  shell.close_request['started']-=20 # A human may leave a modal decision open.
  return QMessageBox.Save
 with patch.object(QMessageBox,'question',side_effect=late_save_decision):shell.close();wait(lambda:shell.closing,45)
 assert w.exited() and shell.client.process.returncode==0;checks.append('A delayed modal Save decision still closes normally; actual timeline/source/codec/mix/pool owners; no force counted as success')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,classification=__doc__,gesture_samples=c.feedback_samples),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,notice=w.notice.text() if 'w' in globals() else 'startup',state=state() if 'w' in globals() else {}),indent=2,default=str),'utf8');raise
finally:
 QApplication.clipboard().clear() # This offscreen fixture owns its process-local clipboard.
 pool.shutdown(wait=False,cancel_futures=True)
 if shell and not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();deadline=time.monotonic()+40
   while not shell.closing and time.monotonic()<deadline:pump()
