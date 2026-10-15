"""Focused synthetic Qt missing-source Save choice and empty-project controls."""
from pathlib import Path
import sys,os,time,uuid,json,traceback
from unittest.mock import patch
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog
from PySide6.QtTest import QTest
from studio_qt import Shell
app=QApplication([]);shell=Shell(out/'layout.json',out/'owner.log');w=shell.project_workspace;shell.show();shell.panels['project'].toggleView(True);shell.panels['project'].setAsCurrentTab();checks=[]
def wait(fn):
 end=time.perf_counter()+25
 while time.perf_counter()<end:
  app.processEvents();time.sleep(.005)
  if fn():return
 raise AssertionError(w.notice.text())
try:
 w.refresh();assert all(not b.isEnabled() for b in w.controls[2:]);assert all(b.isEnabled() for b in w.controls[:2]);checks.append('No-project controls are explicit; New/Open remain usable')
 w.submit('new',name='Missing media fixture');wait(lambda:w.pending is None);aid=uuid.uuid4().hex;w.batch('Explicit missing reference',[dict(op='media.add',id=aid,name='Missing narration',kind='Audio',placeholder=True,sha256='a'*64,location=dict(kind='external',path=str(out/'missing.wav')),metadata=dict(duration=2))]);wait(lambda:w.pending is None);assert w.state()['media'][aid]['status']=='Missing'
 with patch.object(QMessageBox,'question',return_value=QMessageBox.No):w.save(True)
 assert w.pending is None and w.state()['dirty'];checks.append('Declining missing-reference save leaves accepted work open and unsaved')
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes),patch.object(QFileDialog,'getSaveFileName',return_value=(str(out/'missing.zwv'),'')):
  QTest.mouseClick(w.controls[3],Qt.LeftButton,pos=w.controls[3].rect().center());wait(lambda:w.pending is None)
 assert w.last_outcome['status']=='durable' and w.last_outcome['result']['warnings'] and not w.state()['dirty'];assert w.trees['media'].topLevelItem(0).text(2)=='Missing'
 checks.append('Explicit Yes secures editable metadata, reports unresolved content and preserves the Missing row')
 w.grab().save(str(out/'project-workspace.png'));shell.close();wait(lambda:shell.closing);assert shell.client.process.returncode==0;checks.append('Normal Qt close joins the actual owner after the explicit missing-reference save')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,classification=__doc__),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if not shell.closing:
  shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
