"""Real owner/Qt first-input race: cached display rows versus newer authoritative state."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,json,time,uuid,hashlib,traceback
root=Path(__file__).resolve().parents[2]
if len(sys.argv)!=3:raise SystemExit('Usage: studio_project_inspector_test.py NEW_EVIDENCE_DIRECTORY DISPOSABLE_F1_PROJECT')
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);fixture=Path(sys.argv[2]).resolve();sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QPoint,QPointF,QObject,QEvent
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_api import call
app=QApplication([]);shell=None;expect_reject=True
def pump():app.processEvents();time.sleep(.002)
def wait(fn,seconds=30):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if fn():return
 raise AssertionError('Timeout '+w.notice.text())
def settle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired)

class Painted(QObject):
 def __init__(self):super().__init__();self.count=0
 def eventFilter(self,obj,event):
  if event.type()==QEvent.Paint:self.count+=1
  return False

def painted_contexts():
 # ADS temporarily disables ancestor updates during reparent/layout. Preserve
 # the body's explicit ownership flag, not inherited effective disablement.
 before=deepcopy(w.document());revision=w.state()['revision'];contexts=[]
 assets={a['id']:a for a in before['media']};pictures=next(r for r in before['clips'] if assets[r['asset']]['kind']=='Image');audio=next(r for r in before['clips'] if next(t['kind'] for t in before['tracks'] if t['id']==r['track'])=='audio')
 for category,item,field in [('clips',pictures,'x'),('clips',audio,'gain'),('captions',before['captions'][0],'text'),('graphics',before['graphics'][0],'text'),('clips',pictures,'x')]:
  shell.setUpdatesEnabled(False)
  try:c.select(category,item['id']);ins.version=None;ins.refresh()
  finally:shell.setUpdatesEnabled(True)
  widget=ins.text if field=='text' else ins.fields[field];probe=Painted();widget.installEventFilter(probe);scroll=ins.findChild(__import__('PySide6.QtWidgets',fromlist=['QScrollArea']).QScrollArea);scroll.ensureWidgetVisible(widget);widget.update()
  for _ in range(10):pump()
  row=dict(category=category,id=item['id'],body_updates=ins.body.updatesEnabled(),body_explicit_disabled=ins.body.testAttribute(Qt.WA_ForceUpdatesDisabled),layout_enabled=ins.form.isEnabled(),field_visible=widget.isVisible(),geometry=[widget.x(),widget.y(),widget.width(),widget.height()],paint_events=probe.count);contexts.append(row);(out/'PAINT_STATES.json').write_text(json.dumps(contexts,indent=2),encoding='utf8');shell.grab().save(str(out/('paint-'+str(len(contexts))+'.png')));assert row['body_updates'] and not row['body_explicit_disabled'] and row['layout_enabled'] and row['field_visible'] and row['paint_events']>0,row;widget.removeEventFilter(probe)
 # A deliberately disabled local body must remain disabled across refresh.
 ins.body.setUpdatesEnabled(False);ins.version=None;ins.refresh();assert ins.body.testAttribute(Qt.WA_ForceUpdatesDisabled);ins.body.setUpdatesEnabled(True);ins.version=None;ins.refresh();pump();assert w.document()==before and w.state()['revision']==revision
 return contexts
try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;c=w.timeline.canvas;ins=shell.video_panels.inspector;w.open(str(fixture));settle();wait(lambda:w.preview.presented is not None);paint_contexts=painted_contexts();assets={a['id']:a for a in w.document()['media']};clip=next(r for r in w.document()['clips'] if assets[r['asset']]['kind']=='Image');key=clip['id'];c.select('clips',key);ins.version=None;ins.refresh();pump();old_bounds=list(ins.rows[0]['layout']['bounds']);display_version=ins.version;original_refresh=ins.refresh;ins.refresh=lambda:None
 s=w.state();external=[.13,.17,.47,.53];request=dict(op='batch',operation_id=uuid.uuid4().hex,**w.binding(),changes=[dict(op='clip.layout',id=key,values=dict(bounds=external))],label='Newer external bounds before first Inspector input');reply=call(w.client.snapshot['project']['endpoint'],request);(out/'EXTERNAL_REPLY.json').write_text(json.dumps(reply,indent=2),encoding='utf8');assert reply['ok'],reply;wait(lambda:w.state()['revision']==s['revision']+1);assert ins.version==display_version and ins.rows[0]['layout']['bounds']==old_bounds;before=deepcopy(w.document());revision=w.state()['revision'];box=ins.fields['x'];box.setFocus();box.lineEdit().selectAll();QTest.keyClicks(box.lineEdit(),'25');QTest.keyClick(box.lineEdit(),Qt.Key_Return);settle();until=time.monotonic()+.5
 while time.monotonic()<until:pump()
 actual=next(r['layout']['bounds'] for r in w.document()['clips'] if r['id']==key);rejected=w.document()==before and w.state()['revision']==revision;retained=deepcopy(ins.retained_property);ins.refresh=original_refresh;ins.version=None;ins.refresh();result=dict(classification=__doc__,painted_contexts=paint_contexts,expect_reject=expect_reject,display_version=display_version,newer_authoritative_revision=revision,old_display_bounds=old_bounds,newer_authoritative_bounds=external,typed_x_percent=25,actual_bounds=actual,rejected_without_edit=rejected,retained_input=retained,source_sha256=hashlib.sha256((root/'app/visuals/studio_project_inspector.py').read_bytes()).hexdigest());w.save(path=str(out/'observed-state.zwv'));settle()
 if not rejected:w.submit('undo');settle();assert w.document()==before
 ins.version=None;ins.refresh();pump();wheel_before=deepcopy(w.document());wheel_revision=w.state()['revision'];spin=ins.fields['rotation'];w.notice.setFocus();pump();assert not spin.hasFocus();wheel_revisions=[]
 for number in (1,2):
  local=QPointF(10,10);event=QWheelEvent(local,spin.mapToGlobal(local.toPoint()),QPoint(),QPoint(0,-120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False);QApplication.sendEvent(spin,event);until=time.monotonic()+.7
  while time.monotonic()<until:pump()
  settle();wheel_revisions.append(w.state()['revision'])
 result['unfocused_wheel_revisions']=wheel_revisions;result['unfocused_wheel_before_revision']=wheel_revision;result['two_wheels_accepted']=wheel_revisions==[wheel_revision+1,wheel_revision+2]
 for _ in range(w.state()['revision']-wheel_revision):w.submit('undo');settle()
 assert w.document()==wheel_before
 w.save(path=str(out/'preserved-newer-work.zwv'));settle();shell.close();wait(lambda:shell.closing,45);assert w.exited() and shell.client.process.returncode==0;result.update(owner_exit=0,workers_exited=True,exact_newer_work_preserved=True);(out/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');assert rejected and retained and result['two_wheels_accepted'] if expect_reject else not rejected and actual[1:]!=external[1:];print('PASS cached-display binding, two unfocused wheel transactions, exact Undo/Save and owner cleanup',out,flush=True)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if shell and not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();end=time.monotonic()+40
   while not shell.closing and time.monotonic()<end:pump()
