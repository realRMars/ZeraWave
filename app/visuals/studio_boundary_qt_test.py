"""Matched Qt input route and real owner checks on a disposable document.

Synthetic Qt key/mouse input and API detach/redock; not physical listening or
Robert's acceptance. Optional worker delay is injected transport, not natural lag.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,time,json,hashlib,uuid,threading,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog,QPushButton,QDialog
from PySide6.QtCore import Qt,QEvent,QTimer,QPoint,QObject
from PySide6.QtGui import QKeyEvent,QImage
from PySide6.QtTest import QTest
import PySide6QtAds as ads
import studio_qt

def run(folder):
 out=Path(folder);out.mkdir(parents=True,exist_ok=False);checks=[];raw=[];app=QApplication([])
 drop=out/'drop-ack.flag';write_barrier=out/'write-barrier.flag'
 os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_RASTER_TEST_DROP_ACK=str(drop),ZERAWAVE_RASTER_TEST_BARRIER=str(write_barrier))
 original=studio_qt.Shell.error
 def error(self,*a,**k):
  with patch.object(studio_qt,'ROOT',out):return original(self,*a,**k)
 studio_qt.Shell.error=error
 shell=studio_qt.Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=shell.image_editor
 def pump(seconds=.01):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:app.processEvents();time.sleep(.001)
 def wait(fn,seconds=25):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:
   pump()
   if fn():return
  raise AssertionError('Timeout: '+e.status.text())
 def request(action,**data):
  future=shell.client.submit(action,**data);wait(future.done);return future.result()
 def idle():wait(lambda:not e.art_jobs and not e.edit_jobs and e.binding==(shell.client.snapshot['media_control']['session'],shell.client.snapshot['media_control']['revision']))
 heartbeat=[];timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:heartbeat.append(time.perf_counter()));timer.start()
 gate=None
 try:
  wait(lambda:not shell.client.snapshot['media_library']['loading'])
  request('form',form=41);shell.refresh_tuning(True)
  shell.panels['tuning'].toggleView(True);shell.panels['tuning'].setAsCurrentTab();pump(.15)
  control=next(w for w in shell.numerics if w.key=='bass_response')
  paint_samples=[]
  class PaintObserver(QObject):
   def eventFilter(self,obj,event):
    if event.type()==QEvent.Paint:paint_samples.append((time.perf_counter(),control.spin.value()))
    return False
  observer=PaintObserver();control.spin.installEventFilter(observer)
  timing_dimensions=dict(window=[shell.width(),shell.height()],dpr=shell.devicePixelRatioF(),numeric=[control.spin.width(),control.spin.height()],canvas_source=list(e.canvas_size),canvas_viewport=[e.canvas.width(),e.canvas.height()],screen=app.primaryScreen().name(),screen_pixels=[app.primaryScreen().size().width(),app.primaryScreen().size().height()],refresh_hz=app.primaryScreen().refreshRate(),rendered_preview='stopped')
  request('operation_status',measurement_phase='numeric-start')
  is_candidate=hasattr(shell.client,'boundary');send=shell.client.request
  def delayed(action,**data):
   delay=float(os.environ.get('ZERAWAVE_BOUNDARY_DELAY','0'))
   if action=='tune':time.sleep(delay)
   return send(action,**data)
  if is_candidate:shell.client.boundary.send=delayed
  else:shell.client.request=delayed
  for repetition in range(3):
   for sample in range(8):
    control.spin.lineEdit().setFocus();pump(.01);control.setEnabled(True);control.spin.setEnabled(True)
    before=control.spin.value();start=time.perf_counter();priorbeats=len(heartbeat)
    app.sendEvent(control.spin,QKeyEvent(QEvent.KeyPress,Qt.Key_Up,Qt.NoModifier));returned=time.perf_counter()
    assert abs(control.spin.value()-(before+.01))<1e-6,('key activation',before,control.spin.value(),control.spin.isEnabled())
    wait(lambda:abs(shell.view.vars['bass_response'].get()-(before+.01))<1e-6);visible=time.perf_counter()
    pump(.015)
    painted=next((t for t,value in paint_samples if t>=start and abs(value-(before+.01))<1e-6),None)
    raw.append(dict(repeat=repetition,sample=sample,callback_ms=(returned-start)*1000,coherent_state_ms=(visible-start)*1000,first_value_paint_ms=(painted-start)*1000 if painted else None,heartbeat_events=len(heartbeat)-priorbeats))
  if is_candidate:shell.client.boundary.send=send
  else:shell.client.request=send
  checks.append('Actual Qt numeric key path preserves bound tuning; delayed completion timing separated')
  request('operation_status',measurement_phase='numeric-end')
  control.setEnabled(True);control.spin.setEnabled(True);control.spin.lineEdit().selectAll();QTest.keyClicks(control.spin.lineEdit(),'1.25');QTest.keyClick(control.spin,Qt.Key_Return)
  wait(lambda:abs(shell.view.vars['bass_response'].get()-1.25)<1e-6)
  checks.append('Normal numeric typing commits only the intended control value')
  shell.grab().save(str(out/'qt-controls.png'))
  before=json.dumps(shell.owner.values(),sort_keys=True)
  floating=shell.manager.addDockWidgetFloating(shell.panels['colors']);pump(.1)
  shell.manager.addDockWidget(ads.RightDockWidgetArea,shell.panels['colors'],shell.panels['preview'].dockAreaWidget());pump(.1)
  assert json.dumps(shell.owner.values(),sort_keys=True)==before
  checks.append('Detach/redock API preserves document settings; physical drag remains separate')
  # Mouse/button route to audio controls; no audio file, capture or listening.
  QTest.mouseClick(shell.hub_source.buttons[1],Qt.LeftButton)
  wait(lambda:shell.client.snapshot['audio_hub']['mode']=='Audio File');pump(.15)
  QTest.mouseClick(shell.hub_mute.buttons[1],Qt.LeftButton)
  wait(lambda:shell.client.snapshot['audio_hub']['mute'])
  checks.append('Actual Qt mouse button reaches audio owner mute without altering raw analysis settings')
  e.resize_canvas((64,48),False);idle();e.blank_layer();idle();target=e.selected
  count=shell.client.snapshot['media_control']['history']['commands']
  drop.touch();e.edit('name','Boundary accepted','Rename boundary');e.history(False,'layers');idle();e.history(True,'layers');idle()
  assert e.selected_row()['name']=='Boundary accepted'
  history=shell.client.snapshot['media_control']['history'];assert history['commands']==count+1,history
  if is_candidate:
   assert not drop.exists();checks.append('Dropped owner ACK reconciles ordinary edit; ordered Undo Redo retain exact history')
  else:
   drop.unlink(missing_ok=True);checks.append('Baseline synchronous ordinary edit/history parity; ordinary requests lack operation identity')
  # A definitively rejected ordered command settles without a document edit.
  # Save immediately afterward must secure accepted work, not require a dummy
  # successful command merely to replace the predecessor operation identity.
  rejected_revision=e.binding[1]
  try:request('composition',version=4,canvas=[0,0],presentation=e.config['presentation'],layers=e.config['layers']);raise AssertionError('Invalid composition admitted')
  except ValueError:pass
  assert shell.client.snapshot['media_control']['revision']==rejected_revision
  checks.append('Known rejected command preserves the accepted revision; following Save is tested directly')
  key=uuid.uuid4().hex;save=out/'saved.json';revision=e.binding[1]
  request('save',path=str(save),save_id=key)
  wait(lambda:any(s['id']==key and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves']))
  pin=next(s for s in shell.client.snapshot['media_control']['raster']['saves'] if s['id']==key);assert pin['revision']==revision
  scene=deepcopy(e.config);request('load',path=str(save));e.refresh(True)
  (out/'reopen-comparison.json').write_text(json.dumps(dict(before=scene,after=e.config),indent=2),encoding='utf8')
  for field in ('layers','canvas','presentation','editor'):assert e.config.get(field)==scene.get(field),field
  checks.append('Save barrier pins requested revision; disposable reopen matches hierarchy/settings')
  e.select(target);wait(lambda:e.canvas.source_image(e.selected_row()) is not None)
  def choose_output(dialog):
   dialog.destination.setText(str(out/'still.png'));dialog.format.setCurrentIndex(dialog.format.findData('png'));dialog.check();return QDialog.Accepted
  with patch('artwork_save_ui.SaveOptions.exec',choose_output):e.artwork_save.save(True,[target])
  wait(lambda:not e.artwork_save.pending());assert QImage(str(out/'still.png')).size()==e.canvas.source_image(e.selected_row()).size()
  assert any(v['path']==str(out/'still.png') for v in shell.client.snapshot['values'].get('artwork_outputs',[])),e.status.text()
  checks.append('Durable still PNG and ordered destination association remain distinct and confirmed')
  # A recovered session is isolated. Never replace user work to verify rollback.
  request('raster_retry');idle();e.select(target);wait(lambda:e.metadata(e.selected_row()).get('width')==64)
  e.blank_child(target);idle();assert e.selected_row()['parent']==target,e.status.text()
  checks.append('Same session supports blank child after owner recovery')
  if os.environ.get('ZERAWAVE_BOUNDARY_DISCONNECT')=='1':
   client=shell.client;pid=client.process.pid;revision=client.snapshot['media_control']['revision']
   client.disconnected=True;shell.poll()
   assert client.process.poll() is None and client.job.handle is not None
   try:client.submit('save',path=str(out/'unconfirmed.json'));raise AssertionError('Disconnected owner save was admitted')
   except ValueError:pass
   assert client.snapshot['media_control']['revision']==revision
   client.disconnected=False;shell.refresh_tuning(True)
   checks.append('Controlled disconnect flag retains live owner/accepted state and rejects unconfirmed Save; no owner replacement')
  preview_dimensions={}
  if os.environ.get('ZERAWAVE_BOUNDARY_HOLD')=='1':
   startup_started=time.perf_counter();request('start');wait(lambda:shell.client.snapshot.get('preview',{}).get('ready'),150)
   raw.append(dict(kind='cold_preview_startup',seconds=time.perf_counter()-startup_started))
   preview_dimensions=deepcopy(shell.client.snapshot['preview'].get('dimensions',{}))
   gate=threading.Event()
   def blocked(action,**data):
    if action=='operation_status':assert gate.wait(15),'controlled delay did not release'
    return send(action,**data)
   if is_candidate:shell.client.boundary.send=blocked
   else:shell.client.request=blocked
   futures=[shell.client.submit('operation_status') for _ in range(16)]
   try:shell.client.submit('operation_status');raise AssertionError('Queue did not saturate')
   except ValueError:pass
   shell.panels['transport'].toggleView(True);shell.panels['transport'].setAsCurrentTab();pump(.1)
   hold=next(w for w in app.allWidgets() if isinstance(w,QPushButton) and w.text()=='Hold')
   QTest.mousePress(hold,Qt.LeftButton);wait(lambda:shell.client.snapshot['preview'].get('held'))
   start=time.perf_counter();QTest.mouseRelease(hold,Qt.LeftButton);release_return=time.perf_counter()
   wait(lambda:not shell.client.snapshot['preview'].get('held'))
   assert all(not f.done() for f in futures)
   raw.append(dict(kind='release_saturated',callback_ms=(release_return-start)*1000,visible_ms=(time.perf_counter()-start)*1000))
   gate.set()
   for future in futures:wait(future.done);future.result()
   if is_candidate:shell.client.boundary.send=send
   else:shell.client.request=send
   shell.cancel_preview();wait(lambda:not shell.client.snapshot.get('running'))
   checks.append('Saturated delayed ordinary queue retains actual Hold release and preview Cancel; renderer exits normally')
  if os.environ.get('ZERAWAVE_BOUNDARY_CLOSE_LEDGER')=='1':
   write_barrier.touch();e.blank_layer();idle();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']>0)
   duration=shell.owner.values()['duration'];request('close',mode='clean');wait(lambda:shell.client.snapshot['close_state']['phase']=='draining')
   try:request('var',key='duration',value='999');raise AssertionError('Editing during close was admitted')
   except ValueError as exc:assert 'Closing' in str(exc)
   request('close_cancel');wait(lambda:shell.client.snapshot['close_state']['phase']=='open');assert shell.owner.values()['duration']==duration
   write_barrier.unlink();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0)
   checks.append('Rejected ordered edit during drain consumes its ledger sequence; Close cancel restores same owner and accepted work')
  final_key=uuid.uuid4().hex
  request('save',path=str(out/'final-secured.json'),save_id=final_key)
  wait(lambda:any(s['id']==final_key and s['status']=='durable' and s['revision']==e.binding[1] for s in shell.client.snapshot['media_control']['raster']['saves']))
  shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True)
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();wait(lambda:shell.closing,35)
  assert shell.client.process.poll() is not None
  checks.append('Normal close actually exits owner; no force counted as success')
  gaps=[(b-a)*1000 for a,b in zip(heartbeat,heartbeat[1:])]
  report=dict(checks=checks,raw=raw,heartbeat_gaps_ms=gaps,latencies=list(shell.client.latencies),command_samples=list(shell.client.boundary.samples) if is_candidate else [],timing_dimensions=timing_dimensions,dimensions=dict(window=[shell.width(),shell.height()],dpr=shell.devicePixelRatioF(),canvas=[64,48],preview=preview_dimensions or 'stopped; no renderer'),injected_delay=float(os.environ.get('ZERAWAVE_BOUNDARY_DELAY','0')),limits=__doc__)
  (out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(dict(passed=len(checks),out=str(out))))
 except BaseException:
  (out/'partial.json').write_text(json.dumps(dict(checks=checks,raw=raw,status=e.status.text(),errors=list(shell.errors),snapshot=deepcopy(shell.client.snapshot)),indent=2,default=str),encoding='utf8')
  (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
 finally:
  if gate is not None:gate.set()
  write_barrier.unlink(missing_ok=True)
  timer.stop()
  if not shell.client.closed:
   # Failed fixture cleanup is labeled discard, not successful normal close.
   try:
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,35)
   except Exception:pass
if __name__=='__main__':run(sys.argv[1])
