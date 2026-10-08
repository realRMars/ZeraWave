"""Owned Qt and isolated service regression checks for reviewed proof failures."""
import json,tempfile,time,os
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import Qt,QEvent
from PySide6.QtGui import QCloseEvent,QColor,QKeyEvent
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog,QColorDialog
from studio_qt import Shell,ROOT
from color_controls import resolved_slots,rgb_hex
import PySide6QtAds as ads

def run():
 app=QApplication([]);checks=[]
 out=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(ROOT/'work/qt-studio-proof/corrections-01')));out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='zerawave-proof-corrections-') as temp:
  layout=Path(temp)/'layout.json';session=Path(temp)/'session.json'
  shell=Shell(layout);shell.show();app.processEvents();shell.timer.stop()
  try:
   default=bytes(shell.default);original=json.dumps(shell.owner.values(),sort_keys=True)
   shell.client.request('form',form=41);shell.refresh_tuning(True)
   key='bass_response';binding=shell.view.binding();shell.view.edit(key,1.07,binding)
   assert json.dumps(shell.owner.values(),sort_keys=True)==original
   assert shell.client.snapshot['tuning_dirty']
   event=QCloseEvent()
   with patch.object(QMessageBox,'question',return_value=QMessageBox.Cancel) as question:shell.closeEvent(event)
   assert question.called and not event.isAccepted() and not shell.client.closed
   assert shell.view.vars[key].get()==1.07;checks.append('tuning-only close Cancel preserves actual isolated draft')
   event=QCloseEvent()
   with patch.object(QMessageBox,'question',return_value=QMessageBox.Save),patch.object(QFileDialog,'getSaveFileName',return_value=('','')):shell.closeEvent(event)
   assert not event.isAccepted() and shell.client.snapshot['tuning_dirty'];checks.append('Save picker cancellation keeps draft and window')
   with patch.object(QFileDialog,'getSaveFileName',return_value=(str(session),'')):shell.save_session()
   stored=json.loads(session.read_text());assert stored['qt_tuning_drafts'][0]['settings'][key]==1.07
   assert stored['qt_tuning_drafts'][0]['binding']==binding and not shell.client.snapshot['tuning_dirty']
   checks.append('Save stores exact destination metadata and tuning without authored writes')
   shell.client.request('form',form=42);assert stored['qt_tuning_drafts'][0]['target']=='fractal.41.landscape'
   shell.nine_panels();shell.panels['monitor'].toggleView(False);shell.save_layout()
   assert bytes(shell.default)==default;checks.append('authored default immutable after layout changes')
   floating=shell.manager.addDockWidgetFloating(shell.panels['colors']);app.processEvents()
   floating.move(-100000,-100000);shell.recover();app.processEvents()
   assert any(screen.availableGeometry().contains(floating.frameGeometry().topLeft()) for screen in app.screens())
   shell.manager.addDockWidget(ads.RightDockWidgetArea,shell.panels['colors'],shell.panels['preview'].dockAreaWidget())
   checks.append('off-screen floating geometry recovery API; no actual monitor/DPI change')
   editor=shell.owner.color_editor;target=editor.target();role=target.slots[0].id
   expected=rgb_hex(resolved_slots(target,shell.owner.color_overrides)[0][0]);colors=json.dumps(shell.owner.color_overrides,sort_keys=True)
   with patch.object(QColorDialog,'getColor',return_value=QColor()) as dialog:shell.color_edit(target.id,role)
   assert dialog.call_args.args[0].name().upper()==expected.upper()
   assert json.dumps(shell.owner.color_overrides,sort_keys=True)==colors;checks.append('color dialog resolved pigment and Cancel')
   with patch.object(QColorDialog,'getColor',return_value=QColor('#445566')):shell.color_edit(target.id,role)
   assert '#445566' in json.dumps(shell.owner.color_overrides).upper();checks.append('color Commit uses captured target')
   shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True)
   with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
   reopened=Shell(layout);reopened.show();app.processEvents();reopened.timer.stop()
   try:
    assert reopened.panels['monitor'].isClosed()
    before=json.dumps(reopened.owner.values(),sort_keys=True);reopened.reset_layout();app.processEvents()
    assert not reopened.panels['monitor'].isClosed() and not reopened.manager.floatingWidgets()
    assert json.dumps(reopened.owner.values(),sort_keys=True)==before
    assert bytes(reopened.default)==default;checks.append('reopen custom layout then Reset restores immutable default only')
    reopened.client.request('load',path=str(session));reopened.client.request('form',form=41)
    assert not reopened.client.snapshot['tuning_dirty']
    reopened.client.request('restore_draft',binding=reopened.view.binding())
    assert reopened.view.vars[key].get()==1.07,(reopened.view.vars[key].get(),reopened.client.snapshot['tuning_drafts'])
    assert reopened.view.binding()[0][:2]==['offline','offline'];checks.append('explicit compatible restore binds new owner, retains original saved scope')
    reopened.refresh_tuning(True);control=next(w for w in reopened.numerics if w.key==key)
    # Offline controls correctly remain disabled; this unit event exercises
    # numeric stepping and IPC binding, not live availability or OS injection.
    control.setEnabled(True);control.spin.setEnabled(True)
    old=control.spin.value();QApplication.sendEvent(control.spin,QKeyEvent(QEvent.KeyPress,Qt.Key_Up,Qt.NoModifier))
    assert abs(control.spin.value()-old-.01)<1e-6;checks.append('numeric keyboard fine step .01 reaches bound owner')
    serial=reopened.client.serial;control.spin.lineEdit().setFocus();app.processEvents();serial=reopened.client.serial
    QApplication.sendEvent(control.spin.lineEdit(),QKeyEvent(QEvent.KeyPress,Qt.Key_Space,Qt.NoModifier))
    assert reopened.client.serial==serial;checks.append('text input does not send global BONK')
    reopened.screen().grabWindow(int(reopened.winId())).save(str(out/'shell.png'))
    event=QCloseEvent()
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):reopened.closeEvent(event)
    assert event.isAccepted() and reopened.client.closed;checks.append('tuning-only Discard closes without changing saved session')
    assert json.loads(session.read_text())==stored
   finally:
    if not reopened.client.closed:
     with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):reopened.close()
  finally:
   if not shell.client.closed:
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
  saved_close=Shell(Path(temp)/'save-close-layout.json');saved_close.show();saved_close.timer.stop()
  try:
   saved_close.client.request('form',form=41);saved_close.view.edit(key,1.12,saved_close.view.binding())
   saved_path=Path(temp)/'saved-by-close.json';event=QCloseEvent()
   with patch.object(QMessageBox,'question',return_value=QMessageBox.Save),patch.object(QFileDialog,'getSaveFileName',return_value=(str(saved_path),'')):saved_close.closeEvent(event)
   assert event.isAccepted() and saved_close.client.closed
   assert json.loads(saved_path.read_text())['qt_tuning_drafts'][0]['settings'][key]==1.12
   checks.append('tuning-only Save from actual close persists draft and closes')
  finally:
   if not saved_close.client.closed:
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):saved_close.close()
 (out/'cpu-result.json').write_text(json.dumps({'result':'PASS','evidence':'actual Qt widgets and separate Tk service; direct key event unit checks, no OS mouse gestures','checks':checks},indent=2))
 print('PASS',json.dumps(checks),flush=True)
if __name__=='__main__':run()
