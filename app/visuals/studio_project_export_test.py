"""Actual Qt controls/single owner export with synthetic offscreen input; no physical claim."""
from pathlib import Path
from copy import deepcopy
import sys,os,time,json,uuid,traceback,hashlib
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);barrier=out/'held.flag';os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_TEST_EXPORT_BARRIER=str(barrier))
from PySide6.QtWidgets import QApplication,QPushButton,QSpinBox,QDialog
from PySide6.QtCore import QTimer
from studio_qt import Shell
from project_service import read_project
app=QApplication([]);shell=None;checks=[]
def wait(fn,seconds=30):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  app.processEvents();time.sleep(.003)
  if fn():return
 raise AssertionError(w.notice.text()+' '+w.export_notice.text())
def idle():wait(lambda:w.pending is None and shell.client.edit_count==0)
try:
 source={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app/audio','app/visuals') for p in (root/folder).glob('*.py')};(out/'SOURCE.json').write_text(json.dumps(source,indent=2),'utf8')
 shell=Shell(layout_path=out/'layout.json',control_log_path=out/'owner.log');shell.show();wait(lambda:shell.client is not None);w=shell.project_workspace;art=deepcopy(shell.owner.values());w.submit('new',name='Qt Export controls');idle();track=uuid.uuid4().hex;w.batch('Editable title',[dict(op='track.add',id=track,kind='graphics'),dict(op='graphic.add',track=track,start=0,duration=30,text='Native export',style=dict(size=18,bounds=[.05,.5,.9,.5]))]);idle()
 def settings():
  d=app.activeModalWidget();assert isinstance(d,QDialog);next(v for v in d.findChildren(QSpinBox) if v.accessibleName()=='Width').setValue(384);next(v for v in d.findChildren(QSpinBox) if v.accessibleName()=='Height').setValue(216);d.accept()
 QTimer.singleShot(20,settings);w.project_settings();idle();assert w.document()['settings']['width']==384;before=deepcopy(w.document());revision=w.state()['revision'];barrier.write_text('hold');key=w.export_video(path=str(out/'qt.mp4'),crf=18);wait(lambda:w.export_id==key and w.pending is None);assert w.cancel_button.isEnabled() is False and w.export_cancel.isEnabled()
 w.batch('Edit while Qt export runs',[dict(op='project.rename',name='Later manual edits')]);idle();assert w.state()['revision']==revision+1 and w.export_id==key;checks.append('Qt project settings and export submit nonblocking through same owner; newer edit remains separate; export-specific cancel targets correct ID')
 w.cancel_export();wait(lambda:any(v['id']==key and v['status']=='failed' for v in w.state()['operations']) and not w.export_cancel.isEnabled() and 'retained' in w.export_notice.text());assert not (out/'qt.mp4').exists();barrier.unlink();checks.append('Qt Cancel video export reconciles actual worker exit, retains authored work and truthful failed status')
 key=w.export_video(path=str(out/'qt-recovery.mp4'),crf=18);wait(lambda:any(v['id']==key and v['status']=='exported' for v in w.state()['operations']) and 'exported' in w.export_notice.text().lower());assert w.state()['saved_revision'] is None;checks.append('Qt export retry completes without marking project saved; native encoder/context/readers retire')
 w.save(path=str(out/'qt.zwv'));idle();saved=deepcopy(w.document());w.close_project();idle();w.open(str(out/'qt.zwv'));idle();assert w.document()==saved and shell.owner.values()==art;shell.close();wait(lambda:shell.closing,30);assert shell.client.process.returncode==0 and w.exited() and shell.client.protocol_error_count==0;checks.append('Qt project Save/close/reopen and normal application close preserve document/artistic settings independently of Export')
 assert all(hashlib.sha256((root/r).read_bytes()).hexdigest()==h for r,h in source.items());(out/'RESULT.json').write_text(json.dumps(dict(result='PASS',checks=checks,callbacks=w.callback_samples,classification=__doc__),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if barrier.exists():barrier.unlink()
 if shell and not shell.closing:
  w.close_resources();w.preview.media.thread.join(5);shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
