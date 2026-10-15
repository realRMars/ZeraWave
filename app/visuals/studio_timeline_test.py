"""Real Studio owner, synthetic Qt pointer/key timeline operations; no physical claim."""
from pathlib import Path
from copy import deepcopy
import sys,os,time,uuid,json,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QDialog,QDoubleSpinBox,QComboBox,QWidget
from PySide6.QtCore import Qt,QPoint,QTimer
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_api import call
app=QApplication([]);shell=None;checks=[];rows=[]
def pump(seconds=.03):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:app.processEvents();time.sleep(.001)
def wait(test,seconds=25):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:
  pump()
  if test():return
 raise AssertionError('Qt/owner did not settle: '+w.notice.text()+'; '+w.preview.status.text())
def doc():return deepcopy(w.document())
def idle():wait(lambda:w.pending is None and shell.client.edit_count==0)
def api(op,**args):
 s=call(endpoint,dict(op='state'))['state'];request=dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args);r=call(endpoint,request);assert r['ok'],r
 while r['outcome']['status'] in ('preparing','saving'):
  pump();r=call(endpoint,dict(op='operation_status',operation_id=request['operation_id']));assert r['ok'],r
 assert r['outcome']['status'] in ('accepted','durable'),r;wait(lambda:w.state().get('revision')==r['state']['revision']);return r
def drag(key,dx,edge=None,track=None):
 canvas=w.timeline.canvas;wait(lambda:('clips',key) in canvas.rects);r=canvas.rects[('clips',key)];x=round(r.left()+2 if edge=='left' else r.right()-2 if edge=='right' else r.center().x());y=round(r.center().y());start=QPoint(x,y);end=QPoint(x+dx,y if track is None else canvas.ruler_height+track*canvas.row_height+20);before=doc();began=time.perf_counter();QTest.mousePress(canvas,Qt.LeftButton,pos=start);QTest.mouseMove(canvas,end,10);pump(.02);assert doc()==before,'Preview became an edit before release';QTest.mouseRelease(canvas,Qt.LeftButton,pos=end);idle();rows.append(dict(kind=edge or 'move',gesture_to_reconciled_ms=(time.perf_counter()-began)*1000,revision=w.state()['revision']));pump(.06)
try:
 shell=Shell(layout_path=out/'layout.json',control_log_path=out/'owner.log');shell.resize(1800,1100);shell.show();wait(lambda:shell.client is not None);w=shell.project_workspace;endpoint=w.state()['endpoint'];legacy=deepcopy(shell.owner.values());shell.panels['project'].toggleView(True);shell.panels['project'].setAsCurrentTab();pump(.1)
 fixture=Path(__file__).resolve().parents[2]/'work/video-editor-20261013-1791942063889153000/increment-A-correction1/bound/formats/fixture.mp4';assert fixture.exists();a,t,second,audio,c,ac,link=[uuid.uuid4().hex for _ in range(7)]
 api('new',name='Qt timeline');api('batch',label='Shared video/audio timeline',changes=[dict(op='media.add',id=a,name='fixture',kind='Video',location=dict(kind='external',path=str(fixture))),dict(op='track.add',id=t,name='Picture',kind='video',order=0),dict(op='track.add',id=second,name='Other picture',kind='video',order=1),dict(op='track.add',id=audio,name='Linked source sound',kind='audio',order=2),dict(op='clip.add',id=c,asset=a,track=t,start=10,duration=50,link_id=link),dict(op='clip.add',id=ac,asset=a,track=audio,start=10,duration=50,link_id=link)])
 wait(lambda:w.preview.presented and w.preview.presented[:2]==(w.state()['epoch'],w.state()['revision']) and len(w.timeline.canvas.rects)==2);assert w.preview.view.surface.image.width()==1280
 checks.append('Shared API-created clips visible in real Qt timeline; native authored CPU preview; scoped bin separate from global Library')
 w.timeline.canvas.snap=False;before=doc();drag(c,30);moved=doc();assert {r['start'] for r in moved['clips']}=={20};assert [r['source_in'] for r in moved['clips']]==[r['source_in'] for r in before['clips']];w.submit('undo');idle();assert doc()==before;w.submit('redo');idle();assert doc()==moved
 checks.append('Complete Qt press/move/release moves linked clips once; preview leaves document unchanged; exact Undo/Redo')
 drag(c,-18,'right');trimmed=doc();assert {r['duration'] for r in trimmed['clips']}=={44};assert all(r['audio_window']['duration']==50 for r in trimmed['clips']);drag(c,0,track=1);assert next(r for r in doc()['clips'] if r['id']==c)['track']==second and next(r for r in doc()['clips'] if r['id']==ac)['track']==audio
 checks.append('Right trim handles preserve linked timing and envelope origin; moving between compatible picture tracks preserves linked audio track')
 # Capture a gesture then let the API edit its document: stale release applies nothing.
 canvas=w.timeline.canvas;rect=canvas.rects[('clips',c)];point=QPoint(round(rect.center().x()),round(rect.center().y()));QTest.mousePress(canvas,Qt.LeftButton,pos=point);QTest.mouseMove(canvas,point+QPoint(30,0),10);api('batch',label='Intervening API edit',changes=[dict(op='project.rename',name='Intervening edit')]);after=doc();wait(lambda:canvas.gesture is None);assert QWidget.mouseGrabber() is not canvas;QTest.mouseRelease(canvas,Qt.LeftButton,pos=point+QPoint(30,0));pump(.2);assert doc()==after and QWidget.mouseGrabber() is not canvas
 checks.append('Intervening API edit invalidates an in-progress Qt gesture without overwriting manual/API state')
 rect=canvas.rects[('clips',c)];point=QPoint(round(rect.center().x()),round(rect.center().y()));before=doc();QTest.mousePress(canvas,Qt.LeftButton,pos=point);assert QWidget.mouseGrabber() is canvas;QTest.keyClick(canvas,Qt.Key_Escape);assert canvas.gesture is None and QWidget.mouseGrabber() is not canvas;QTest.mouseRelease(canvas,Qt.LeftButton,pos=point);assert doc()==before
 checks.append('Real owner/Qt stale revision immediately releases capture; Escape and subsequent gesture cancel preserve exact document')
 scrub_revision=w.state()['revision']
 for frame in (1,8,30,12,42):w.transport('seek',frame)
 wait(lambda:w.transport_future is None and w.transport_desired is None);wait(lambda:w.transport_state().get('frame')==42 and w.preview.presented and w.preview.presented[-1]==42);assert w.state()['revision']==scrub_revision
 checks.append('Latest queued scrub wins, bounded owner commands and prepared preview agree at exact frame 42')
 revision=w.state()['revision'];w.transport('play');wait(lambda:w.transport_state().get('playing'));pump(.25);w.transport('pause');wait(lambda:not w.transport_state().get('playing'));assert w.state()['revision']==revision;assert w.transport_state()['active'];w.transport('stop');wait(lambda:not w.transport_state().get('active'));assert w.transport_state()['frame']==0 and shell.owner.values()==legacy
 checks.append('Play/pause/stop use ephemeral shared owner transport, leave project history/artistic layer session intact and release legacy clock ownership')
 w.transport('seek',35);wait(lambda:w.transport_future is None and w.transport_state().get('frame')==35);canvas.select('clips',c);QTest.keyClick(canvas,Qt.Key_S);idle();assert len(doc()['clips'])==4;w.submit('undo');idle();assert len(doc()['clips'])==2
 QTest.keyClick(canvas,Qt.Key_Right);wait(lambda:w.transport_future is None and w.transport_state().get('frame')==36);canvas.select('clips',c);QTest.keyClick(canvas,Qt.Key_Delete);idle();assert not doc()['clips'];w.submit('undo');idle();assert len(doc()['clips'])==2
 checks.append('Scoped timeline keyboard split, frame step, linked remove and Undo restore exact clip content')
 # Exercise the actual modal controls and submit the captured values through the
 # owner, then verify exact history. This is Qt-synthetic, not physical input.
 before_layout=doc();item=w.trees['clips'].topLevelItem(0);w.trees['clips'].setCurrentItem(item);selected=item.data(0,Qt.UserRole)
 def accept_layout():
  dialog=app.activeModalWidget();assert isinstance(dialog,QDialog)
  for box in dialog.findChildren(QDoubleSpinBox):
   if box.accessibleName()=='Opacity':box.setValue(.6)
   elif box.accessibleName()=='Rotation':box.setValue(12)
  for box in dialog.findChildren(QComboBox):
   if box.accessibleName()=='Fit':box.setCurrentText('Fill')
  dialog.accept()
 QTimer.singleShot(30,accept_layout);w.spatial_edit();idle();layout=next(r for r in doc()['clips'] if r['id']==selected)['layout'];assert layout['opacity']==.6 and layout['rotation']==12 and layout['fit']=='Fill'
 w.submit('undo');idle();assert doc()==before_layout;w.submit('redo');idle();assert next(r for r in doc()['clips'] if r['id']==selected)['layout']==layout
 checks.append('Spatial layout dialog acceptance captures correct opacity/rotation/fit into owner history, with exact Undo/Redo')
 final=doc();api('save',path=str(out/'qt-timeline.zwv'));rect=canvas.rects[('clips',c)];point=QPoint(round(rect.center().x()),round(rect.center().y()));QTest.mousePress(canvas,Qt.LeftButton,pos=point);api('close');wait(lambda:canvas.gesture is None);assert QWidget.mouseGrabber() is not canvas;wait(lambda:w.preview.wanted is None and w.preview.media.metrics.get('decoders')==0);assert w.preview.view.surface.image is None;api('open',path=str(out/'qt-timeline.zwv'));assert doc()['clips']==final['clips'] and doc()['tracks']==final['tracks'];wait(lambda:w.preview.presented is not None)
 checks.append('Real owner portable Save/Close/Open reconstructs stable editable tracks/clip mappings and preview')
 shell.close();wait(lambda:shell.closing,40);assert w.exited() and shell.client.process.returncode==0 and not shell.client.reader.is_alive();checks.append('Normal Qt close observes media worker, owner process and reader exit')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,gesture_samples=rows,submission_callback_samples=w.callback_samples,seek_samples=w.preview.seek_samples,render_samples=w.preview.render_samples,classification=__doc__,protocol_errors=shell.client.protocol_error_count),indent=2),'utf8');assert not shell.client.protocol_error_count;print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if shell and not shell.closing:
  w.close_resources();w.preview.media.thread.join(5);shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
