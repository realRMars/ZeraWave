"""Synthetic offscreen Qt pointer/key/dialog controls with a real Studio owner.

No physical drag, native compositor, preview/playback or listening claim.
"""
from pathlib import Path
import sys,os,time,json,wave,uuid,traceback
from copy import deepcopy
from unittest.mock import patch
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);failure=out/'write-failure.flag';os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_TEST_WRITE_FAILURE=str(failure))
from PySide6.QtCore import Qt,QTimer,QPoint
from PySide6.QtWidgets import QApplication,QDialog,QDialogButtonBox,QPlainTextEdit,QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox,QMessageBox,QFileDialog
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_api import call
app=QApplication([]);shell=None;checks=[];errors=[];timings=[]
def pump(seconds=.01):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:app.processEvents();time.sleep(.001)
def wait(fn,seconds=25):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:
  pump()
  if fn():return
 raise AssertionError('Qt did not settle: '+(w.notice.text() if shell else 'startup'))
def idle():wait(lambda:w.pending is None and shell.client.edit_count==0)
def doc():return deepcopy(w.document())
def button(text,key=None):
 if key:
  if key=='media':shell.video_panels.scope.setCurrentIndex(0);shell.panels['media'].toggleView(True)
  else:shell.panels['project_data'].toggleView(True);shell.panels['project_data'].setAsCurrentTab();w.tabs.setCurrentWidget(w.pages[key][0])
  pump(.02)
 buttons=w.controls if key is None else w.pages[key][0].findChildren(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton)
 return next(b for b in buttons if b.text()==text)
def click(b):
 start=time.perf_counter();QTest.mouseClick(b,Qt.LeftButton,pos=b.rect().center());timings.append(dict(control=b.text(),gesture_ms=(time.perf_counter()-start)*1000));pump();idle()
def edit(b,values,check_typing=False):
 def fill():
  try:
   dialog=app.activeModalWidget();assert isinstance(dialog,QDialog)
   for name,value in values.items():
    widget=next(q for q in dialog.findChildren(__import__('PySide6.QtWidgets',fromlist=['QWidget']).QWidget) if q.accessibleName()==name)
    if isinstance(widget,QComboBox):widget.setCurrentText(value)
    elif isinstance(widget,(QSpinBox,QDoubleSpinBox)):widget.setValue(value)
    elif isinstance(widget,QPlainTextEdit):
     dialog.activateWindow();widget.setFocus();pump(.02);QTest.keyClick(widget,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(widget,value)
     if check_typing:
      revision=w.state()['revision'];QTest.keyClick(widget,Qt.Key_Z,Qt.ControlModifier);assert w.state()['revision']==revision;QTest.keyClick(widget,Qt.Key_Z,Qt.ControlModifier|Qt.ShiftModifier);assert widget.toPlainText()==value,(widget.toPlainText(),value)
    elif isinstance(widget,QLineEdit):widget.setFocus();QTest.keyClick(widget,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(widget,value)
   box=dialog.findChild(QDialogButtonBox);QTest.mouseClick(box.button(QDialogButtonBox.Ok),Qt.LeftButton)
  except BaseException:errors.append(traceback.format_exc());app.activeModalWidget().reject()
 QTimer.singleShot(30,fill);click(b);assert not errors,errors
try:
 source=out/'source.wav'
 with wave.open(str(source),'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(b'\x01\0\x02\0'*48000*4)
 shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;shell.panels['project'].toggleView(True);shell.panels['project'].setAsCurrentTab();pump(.2)
 wait(lambda:not shell.client.snapshot['media_library']['loading']);baseline=deepcopy(shell.owner.values());edit(button('New video'),{'Name':'Qt editable fixture'})
 assert doc()['name']=='Qt editable fixture' and not shell.client.snapshot['media_library']['assets']
 edit(button('Add track…','tracks'),{'Name':'Narration','Kind':'audio'});edit(button('Add track…','tracks'),{'Name':'Captions','Kind':'graphics'})
 with patch.object(QFileDialog,'getOpenFileName',return_value=(str(source),'')):edit(button('Import…','media'),{'Type':'Audio'})
 assert len(doc()['media'])==1 and w.trees['media'].topLevelItemCount()==1
 click(button('Place selected…','media'));wait(lambda:w.timeline.placement is None and not w.pending and len(doc()['clips'])==1);assert doc()['clips'][0]['duration']==120;clip_id=doc()['clips'][0]['id'];original=doc()
 edit(button('Trim…','clips'),{'Start frame':10,'End frame (exclusive)':60});trimmed=doc();r=trimmed['clips'][0];assert r['id']==clip_id and r['duration']==50 and r['source_in']==[1,3] and r['audio_window']['offset']==10
 edit(button('Volume…','clips'),{'Linear gain (1 = unity)':.4});assert doc()['clips'][0]['audio']['gain']==.4 and doc()['clips'][0]['audio_window']['offset']==10
 edit(button('Move…','clips'),{'New start frame':100});moved=doc();assert moved['clips'][0]['start']==100
 click(w.undo);assert doc()['clips'][0]['start']==10;click(w.redo);assert doc()==moved
 checks.append('Real owner receives synthetic Qt import/place/trim/volume/move controls; stable source mapping and retained fade origin; exact Undo/Redo')
 edit(button('Add caption…','captions'),{'Graphics track':'Captions','Text':'Starting caption','Start frame':100,'Duration frames':40},True);caption_id=doc()['captions'][0]['id'];edit(button('Edit caption…','captions'),{'Text':'Corrected editable caption','Start frame':101,'Duration frames':39},True);corrected=doc();assert corrected['captions'][0]['text']=='Corrected editable caption' and corrected['captions'][0]['id']==caption_id
 w.tabs.setCurrentWidget(w.pages['captions'][0]);shell.activateWindow();pump(.03);QTest.mouseClick(w.trees['captions'].viewport(),Qt.LeftButton,pos=QPoint(20,10));pump(.02);assert app.focusWidget() is w.trees['captions'],str(app.focusWidget());QTest.keyClick(w.trees['captions'],Qt.Key_Z,Qt.ControlModifier);idle();assert doc()['captions'][0]['text']=='Starting caption';QTest.keyClick(w.trees['captions'],Qt.Key_Y,Qt.ControlModifier);idle();assert doc()==corrected
 assert shell.owner.values()==baseline
 checks.append('Caption correction and scoped keyboard Undo/Redo; text-field Undo stays local; legacy artistic session unchanged')
 # Keyboard activation must not trigger the live-world BONK/Hold route.
 w.undo.setFocus();QTest.keyClick(w.undo,Qt.Key_Space);idle();assert doc()['captions'][0]['text']=='Starting caption';click(w.redo);assert doc()==corrected
 checks.append('Space activates a project button without triggering legacy world transport')
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(out/'qt.zwv'),'')):click(button('Save As…'))
 assert w.last_outcome['status']=='durable' and not w.state()['dirty'];saved=doc()
 click(button('Close project'));assert w.state()['document'] is None
 with patch.object(QFileDialog,'getOpenFileName',return_value=(str(out/'qt.zwv'),'')):click(button('Open video…'))
 assert doc()['clips']==saved['clips'] and doc()['captions']==saved['captions'] and w.trees['clips'].topLevelItemCount()==1 and w.trees['captions'].topLevelItemCount()==1
 checks.append('Qt portable Save As / project Close / Open restores exact editable clips, captions, scoped displayed rows')
 edit(button('Edit caption…','captions'),{'Text':'Pending close correction'});accepted=doc();failure.write_text('fail')
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Save),patch.object(QFileDialog,'getSaveFileName',return_value=(str(out/'close-save.zwv'),'')):
  shell.close();wait(lambda:shell.close_request is None)
 assert shell.isVisible() and shell.client.process.poll() is None and doc()==accepted and w.state()['dirty'];failure.unlink()
 with patch.object(QFileDialog,'getSaveFileName',return_value=(str(out/'recovered-close.zwv'),'')):click(button('Save As…'))
 assert w.last_outcome['status']=='durable' and not w.state()['dirty']
 checks.append('Real Qt close state machine stays open after controlled project-save failure; same owner retains accepted caption and recovers via Save As')
 # Normal clean close should join owner/readers/GUI pools rather than disappear.
 shell.close();wait(lambda:shell.closing,35);assert shell.client.process.returncode==0 and shell.client.closed and not shell.client.reader.is_alive();assert not Path(w.state().get('endpoint','no-endpoint')).exists()
 checks.append('Qt normal clean close waits for actual owner/readers and owned pools before closing')
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,control_samples=timings,submission_samples=w.callback_samples,protocol_errors=shell.client.protocol_error_count),indent=2),'utf8');assert shell.client.protocol_error_count==0;print('PASS',len(checks))
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,timings=timings,errors=errors),indent=2),'utf8');raise
finally:
 if shell and not shell.closing:
  if failure.exists():failure.unlink()
  shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
