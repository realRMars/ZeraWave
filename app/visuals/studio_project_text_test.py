"""Real owner/API with synthetic offscreen Qt text/style controls; no hardware input."""
from pathlib import Path
from copy import deepcopy
import sys,os,time,json,uuid,hashlib,traceback
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QDialog,QPlainTextEdit,QDoubleSpinBox,QLineEdit
from PySide6.QtCore import Qt,QTimer
from studio_qt import Shell
from project_api import call
app=QApplication([]);shell=None;checks=[]
def pump():app.processEvents();time.sleep(.003)
def wait(fn,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if fn():return
 raise AssertionError(w.notice.text()+'; '+w.preview.status.text())
def idle():wait(lambda:w.pending is None and shell.client.edit_count==0)
def api(op,**args):
 s=call(endpoint,dict(op='state'))['state'];r=call(endpoint,dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args));assert r['ok'],r
 while r['outcome']['status'] in ('preparing','saving'):pump();r=call(endpoint,dict(op='operation_status',operation_id=r['outcome']['id']))
 assert r['outcome']['status'] in ('accepted','durable'),r;wait(lambda:w.state()['revision']==r['state']['revision']);return r
try:
 file=out/'input.srt';file.write_text('1\n00:00:00,000 --> 00:00:02,000\nOriginal café caption\n\n2\n00:00:02,000 --> 00:00:04,000\nSecond editable cue\n','utf8');shell=Shell(layout_path=out/'layout.json',control_log_path=out/'owner.log');shell.show();wait(lambda:shell.client is not None);w=shell.project_workspace;endpoint=w.state()['endpoint'];art=deepcopy(shell.owner.values());api('new',name='Qt editable text');t,g=uuid.uuid4().hex,uuid.uuid4().hex;api('batch',changes=[dict(op='track.add',id=t,kind='graphics')]);api('import_captions',path=str(file),track=t);w.tabs.setCurrentWidget(w.pages['captions'][0]);wait(lambda:w.trees['captions'].topLevelItemCount()==2);w.trees['captions'].setCurrentItem(w.trees['captions'].topLevelItem(0));before=deepcopy(w.document())
 def correct():
  dialog=app.activeModalWidget();assert isinstance(dialog,QDialog);dialog.findChild(QPlainTextEdit).setPlainText('Corrected café — 日本語');dialog.accept()
 QTimer.singleShot(30,correct);w.caption(True);idle();changed=deepcopy(w.document());assert changed['captions'][0]['text']=='Corrected café — 日本語' and changed['captions'][0]['id']==before['captions'][0]['id'];w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==changed;checks.append('Real Qt caption correction uses owner/history with exact stable-ID Undo/Redo')
 revision=w.state()['revision'];QTimer.singleShot(30,lambda:app.activeModalWidget().accept());w.text_style('captions');idle();assert w.state()['revision']==revision and w.document()==changed;checks.append('Untouched style OK preserves full saved values and creates no phantom operation')
 def style():
  dialog=app.activeModalWidget();next(x for x in dialog.findChildren(QDoubleSpinBox) if x.accessibleName()=='Size').setValue(32);next(x for x in dialog.findChildren(QLineEdit) if x.accessibleName()=='Text RGB / ARGB').setText('#ffe8b2');dialog.accept()
 QTimer.singleShot(30,style);w.text_style('captions');idle();styled=deepcopy(w.document());assert styled['captions'][0]['style']['size']==32 and styled['captions'][0]['style']['color']=='#ffe8b2';wait(lambda:w.preview.presented is not None and w.preview.presented[1]==w.state()['revision']);assert w.preview.view.surface.image.save(str(out/'styled-preview.png'));checks.append('Qt font/color style updates visible CPU-reference pixels at native authored output')
 api('batch',changes=[dict(op='graphic.add',id=g,track=t,start=0,duration=120,text='{elapsed} / {duration}',dynamic='counter',style={'size':20,'padding':2,'bounds':[.05,.1,.8,.06],'background':'#00000000'})]);wait(lambda:w.trees['graphics'].topLevelItemCount()==1);w.transport('seek',75);wait(lambda:w.transport_state()['frame']==75 and w.preview.presented is not None and w.preview.presented[3]==75);details=w.preview.view.surface.text.stats['text_details'];assert any(d['id']==g for d in details);checks.append('Actual owner seek drives editable timed-title evaluation and displayed title rows')
 saved=deepcopy(w.document());api('save',path=str(out/'text.zwv'));api('close');api('open',path=str(out/'text.zwv'));assert w.document()==saved and shell.owner.values()==art;checks.append('Portable Save/Close/Open restores text/styles/graphics/IDs and unrelated artistic controls')
 shell.close();wait(lambda:shell.closing,30);assert shell.client.process.returncode==0 and w.exited() and not shell.client.reader.is_alive() and shell.client.protocol_error_count==0;checks.append('Normal Qt close confirms owner/media/reader/text resource exit')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,classification=__doc__,submission_samples=w.callback_samples,render_samples=w.preview.render_samples),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if shell and not shell.closing:
  w.close_resources();w.preview.media.thread.join(5);shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
