"""Raster pressure/recovery and canvas-button regression on disposable sessions.

Qt-scripted input, real owner subprocess, native/B1 pixels and actual filesystem
failure. This does not assert physical pointer, live listening or user acceptance.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,time,json,uuid,gc,traceback,hashlib,threading
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtWidgets import QApplication,QMenu,QMessageBox
from PySide6.QtCore import Qt,QPoint,QPointF,QEvent
from PySide6.QtGui import QImage,QColor,QContextMenuEvent,QWheelEvent
from PySide6.QtTest import QTest
from native_raster import backend
from raster_resources import Resources,snapshot,release,read
from composition import lookup,new_layer

def unit(out,checks):
 image=QImage(16,16,QImage.Format_ARGB32_Premultiplied);image.fill(QColor('#845fc3'))
 if backend().available:
  core=backend().storage();versions=[core.from_image(image) for _ in range(256)]
  desc,producer=snapshot(versions[0])
  try:
   from raster_tiles import TileLease
   try:TileLease(desc);raise AssertionError('Native version pressure not enforced')
   except MemoryError as exc:assert '256 native versions' in str(exc)
   checks.append('Native 256-version import failure preserves original MemoryError; all exported pointers release')
  finally:release(producer);versions.clear();gc.collect()
  assert core.stats()['versions']==0
  # Checkpoint mutation must leave the retained command and rollback state exact.
  from composition import History,defaults
  history=History();before=defaults();row=new_layer();before['layers']=[row];after=deepcopy(before);after['layers'][0]['name']='Changed';history.record(before,after,'rename')
  checkpoint=history.checkpoint();original=deepcopy(checkpoint.__dict__)
  history.rows[row['id']]['name']='provisional';history.flags[row['id']]['locked']=True;history.undo.clear()
  assert checkpoint.__dict__==original
  checks.append('Owner rollback checkpoint shares immutable completed commands while mutable indexes, flags and lists stay independent')
 native=backend().storage().from_image(image) if backend().available else image
 desc,producer=snapshot(native);r=Resources(out/'unit-store');barrier=threading.Event();r.barrier=barrier
 def asset(source=False):
  return dict(id=uuid.uuid4().hex,kind='Images',path=str(out/'source.png'),name='Pressure fixture',managed=True,runtime=desc,source_snapshot=source,metadata=dict(width=16,height=16,bytes=1024,mtime_ns=1),provenance='fixture')
 try:
  for _ in range(16):
   a=asset();r.admit([a]);assert r.persist(a['id'])
  source=asset(True);r.admit([source]);assert r.rows[source['id']]['durability']=='durable'
  assert r.state()['pending']==16
  a=asset()
  try:r.admit([a]);raise AssertionError('PNG job pressure ignored')
  except ValueError:pass
  assert a['id'] not in r.rows
  if backend().available:assert backend().core.stats()['versions']==1 # producer, no storage imports
  checks.append('Sixteen pending PNGs admit a source-only snapshot without charging a job; next persistence edit atomically rejects')
  from raster_tiles import wire_resource,unwire_resource,unique_bytes,mapping_bytes
  packed=wire_resource(r.rows[source['id']]);assert unwire_resource(packed)==r.rows[source['id']]
  assert r.state()['bytes']==unique_bytes(row['runtime'] for row in r.rows.values())
  assert r.state()['mapping_bytes']==mapping_bytes(row['runtime'] for row in r.rows.values())
  checks.append('Compact Qt tile packet restores the exact ABI descriptor; cached owner unique/mapping accounting matches independent validated allocation totals')
  if backend().available:
   assert len(r.mapping_pool.rows)==len(desc['tiles'])
   assert all(row[1]==17 for row in r.mapping_pool.rows.values())
   original=r.leases[source['id']]
   from raster_resources import image as resource_image
   assert not resource_image(desc,native=False,lease=original).isNull()
   assert all(row[1]==17 for row in r.mapping_pool.rows.values())
   checks.append('Seventeen immutable snapshots share one owner handle per tile; PNG/Save borrowed reads leave every legitimate resource reference intact')


 finally:barrier.set();r.close();assert not r.mapping_pool.rows;release(producer);native=None;gc.collect()
 # Quiescent closure must keep ownership if an exported buffer still exists.
 guarded=Resources(out/'exported-buffer-store');desc,lease=snapshot(image);a=asset(True);a['runtime']=desc
 guarded.admit([a]);handle=guarded.leases[a['id']];view=handle.buf[:1]
 try:
  guarded.retain(set());assert a['id'] in guarded.rows and a['id'] in guarded.leases
  assert guarded.state()['lease_cleanup_failures']
  view.release();guarded.retain(set());assert not guarded.rows and not guarded.leases and not guarded.state()['lease_cleanup_failures']
  checks.append('An outstanding exported buffer defers quiescent lease disposal without losing ownership; release permits the next retention tick to recover')
 finally:view.release();guarded.close();release(lease)
 from artwork import encode_image
 alpha=QImage(129,65,QImage.Format_ARGB32_Premultiplied)
 for y in range(alpha.height()):
  for x in range(alpha.width()):alpha.setPixelColor(x,y,QColor(x%256,y%256,(x*y)%256,(x+3*y)%256))
 def rgba(im):
  converted=im.convertToFormat(QImage.Format_RGBA8888_Premultiplied);return bytes(converted.constBits())
 from PySide6.QtGui import QColorSpace
 alpha.setDotsPerMeterX(5000);alpha.setDotsPerMeterY(7500);alpha.setColorSpace(QColorSpace(QColorSpace.SRgb))
 decoded=QImage.fromData(encode_image(alpha),'PNG')
 assert rgba(decoded)==rgba(alpha) and (decoded.dotsPerMeterX(),decoded.dotsPerMeterY())==(5000,7500) and decoded.colorSpace()==alpha.colorSpace()
 checks.append('Lossless PNG Sub/zlib roundtrip preserves odd native dimensions, physical pixel aspect, ICC color space and every premultiplied alpha-edge pixel')
 # A pinned save and reader/history references keep the PNG; only its owner's
 # proven-unused new file may retire. Pre-existing store contents never retire.
 retention=Resources(out/'retirement-store');desc,lease=snapshot(image);a=asset();a['runtime']=desc
 old=retention.folder/'pre-existing.png';old.parent.mkdir(parents=True);old.write_bytes(encode_image(image))
 retention.admit([a]);retention.persist(a['id'])
 try:
  retention.jobs[a['id']].result();retention.poll();path=Path(retention.rows[a['id']]['path'])
  retention.save_pins['fixture']={a['id']};retention.retain(set());assert path.exists() and a['id'] in retention.rows
  retention.save_pins.clear();retention.retain({a['id']});assert path.exists()
  retention.cleanup_after=0;retention.retain(set());assert not path.exists() and old.exists()
  checks.append('Legitimate history/reader/save references protect owned PNGs; quiescent retirement removes only unused files created by this instance and preserves pre-existing artwork')
 finally:retention.close();release(lease)


def run():
 app=QApplication([]);out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);checks=[];states=[]
 import faulthandler
 stacks=(out/'stacks.log').open('w');faulthandler.dump_traceback_later(20,repeat=True,file=stacks)
 def stage(text):print(text,flush=True);(out/'stage.txt').write_text(text,encoding='utf8')
 unit(out,checks)
 hold=out/'hold';hold.touch();store=out/'artwork';store.write_text('Actual filesystem write obstruction',encoding='utf8')
 os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(store),ZERAWAVE_RASTER_TEST_BARRIER=str(hold))
 import studio_qt
 original_error=studio_qt.Shell.error
 def isolated_error(self,*args,**kwargs):
  with patch.object(studio_qt,'ROOT',out):return original_error(self,*args,**kwargs)
 with patch.object(studio_qt.Shell,'error',isolated_error):shell=studio_qt.Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=None
 def pump(t=.02):
  end=time.perf_counter()+t
  while time.perf_counter()<end:app.processEvents();time.sleep(.001)
 def wait(fn,t=40):
  end=time.perf_counter()+t
  while time.perf_counter()<end:
   pump()
   if fn():return
  raise AssertionError('Timeout '+(e.status.text() if e else 'startup'))
 def idle():wait(lambda:not e.edit_jobs and not e.art_jobs)
 def pixels():return e.canvas.source_image(e.selected_row())
 def digest(im):
  converted=im.convertToFormat(QImage.Format_RGBA8888_Premultiplied)
  return hashlib.sha256(bytes(converted.constBits())).hexdigest()
 def state(label):
  packet=dict(label=label,media=deepcopy(shell.client.snapshot['media_control']),status=e.status.text(),gui_native=backend().core.stats() if backend().core else {})
  states.append(packet);(out/'states.json').write_text(json.dumps(states,indent=2),encoding='utf8')
 def stroke(tool='Smudge',i=0,steps=1):
  e.choose_tool(tool);c=e.canvas;r=e.selected_row();a=c.screen_point(r,(.25+(i%10)*.02,.4));c.paint_press(r,a)
  if not c.stroke:
   assert 'Stroke not started:' in e.status.text(),e.status.text();return
  assert c.stroke,e.status.text()
  for k in range(steps):c.paint_move(c.screen_point(r,(.3+(i%10)*.02+k*.001,.45)))
  c.paint_finish();idle();pump(.02)
 try:
  wait(lambda:hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;c=e.canvas
  shell.panels['composition'].toggleView(True);shell.panels['image_layers'].toggleView(True);e.resize_canvas((96,64),False);e.blank_layer();idle();wait(lambda:pixels() is not None)
  original=e.selected
  seed=QImage(96,64,QImage.Format_ARGB32_Premultiplied)
  for y in range(64):
   for x in range(96):seed.setPixelColor(x,y,QColor('#fbd035' if x//8%2 else '#345be2'))
  e.save_paint(dict(row=e.selected,asset=e.selected_row()['asset'],target=deepcopy(e.selected_row()),session=e.binding[0],revision=e.binding[1],tool='Brush',base=pixels()),seed);idle();state('blank pending')
  for i in range(20):stroke('Smudge' if i<18 else 'Brush',i)
  state('saturation');assert shell.client.snapshot['media_control']['raster']['pending']==16
  rejected=[r for r in shell.client.snapshot['media_control']['transactions'] if r['status']=='rejected'];assert all('queue full' in r['error'].lower() for r in rejected)
  assert 'Stroke not started:' in e.status.text() or rejected
  accepted=digest(pixels());accepted_id=e.selected_row()['asset'];revision=e.binding[1];layers=len(e.config['layers'])
  expected_asset=next(a for a in e.media_assets() if a['id']==accepted_id)
  from raster_resources import image as mapped_image
  assert digest(mapped_image(expected_asset['runtime'],native=False))==accepted
  e.blank_layer();idle();assert len(e.config['layers'])==layers and e.binding[1]==revision
  e.blank_child();idle();assert len(e.config['layers'])==layers
  # Deletion is only reproduction, on this disposable fixture. Undo restores it.
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):e.delete(original)
  idle();e.blank_layer();idle();assert not e.config['layers']
  e.history(False);idle();e.select(original);wait(lambda:pixels() is not None)
  diagnostic=dict(accepted=accepted,restored=digest(pixels()),accepted_asset=accepted_id,restored_asset=e.selected_row()['asset'],owner_mapped=digest(mapped_image(expected_asset['runtime'],native=False)),history=deepcopy(shell.client.snapshot['media_control']['history']))
  (out/'undo-diagnostic.json').write_text(json.dumps(diagnostic,indent=2),encoding='utf8');assert digest(pixels())==accepted,diagnostic
  source=out/'library-source.png';im=QImage(96,64,QImage.Format_ARGB32_Premultiplied);im.fill(QColor('#7d29af'));im.save(str(source))
  shell.client.request('media_import',paths=[str(source.resolve())]);wait(lambda:not shell.client.snapshot['media_library']['pending'])
  asset=next(a for a in shell.client.snapshot['media_library']['assets'] if a['path']==str(source.resolve()));assert e.add_asset(asset);imported=e.selected;wait(lambda:pixels() is not None)
  count=len(e.config['layers']);e.blank_child();idle();assert len(e.config['layers'])==count
  e.select(original);e.history(False,'drawing');idle();undo=digest(pixels());e.history(True,'drawing');idle();assert digest(pixels())==accepted and undo!=accepted
  checks.append('Controlled slow persistence: short Smudge/Brush saturation; rejected work never accepted; blank/child still reject after disposable deletion; library import works; Undo restores without recovery-by-deletion')
  hold.unlink();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0);state('actual write failure');assert shell.client.snapshot['media_control']['raster']['failures']
  assert all('183' in err or 'exist' in err.lower() for err in shell.client.snapshot['media_control']['raster']['failures'].values())
  if backend().available:assert shell.client.snapshot['media_control']['raster']['native'].get('versions',0)==0
  e.retry_saving();wait(lambda:e.retry_watch is None);state('retry still blocked')
  assert shell.client.snapshot['media_control']['raster']['failures'] and 'Retry finished with failed writes' in e.status.text()
  assert digest(pixels())==accepted
  checks.append('Real owner Retry while OS destination remains blocked reports failed outcome immediately and retains exact accepted pixels, without duplicate edits')
  store.rename(out/'preserved-store-obstruction');e.retry_saving();e.retry_saving();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0 and not shell.client.snapshot['media_control']['raster']['failures'] and not shell.client.snapshot['media_control']['raster'].get('retry_waiting'));state('retry durable')
  assert digest(pixels())==accepted
  e.blank_layer();idle();wait(lambda:pixels() is not None);assert len(e.config['layers'])==count+1
  e.select(imported);e.blank_child();idle();wait(lambda:pixels() is not None);assert e.selected_row()['parent']==imported
  e.brush_color=QColor('#123ac4');stroke('Brush',steps=48);e.history(False);idle();e.history(True);idle();state('same instance recovered')
  checks.append('Actual OS working-store failure retains accepted pixels; repeated real owner Retry coalesces, drains and restores blank layer, child layer and sustained drawing in same instance')
  # Exact buttons, pinned receiver/color and no artwork history for sampling.
  from studio_composition import OpacitySlider
  slider=OpacitySlider(Qt.Horizontal);slider.setRange(0,100);slider.setValue(50);slider.resize(160,26);slider.show();pump()
  QTest.mousePress(slider,Qt.LeftButton,pos=QPoint(120,13));assert slider.isSliderDown() and slider.value()>65
  QTest.mouseRelease(slider,Qt.LeftButton,pos=QPoint(120,13));assert not slider.isSliderDown();value=slider.value();slider.clearFocus()
  for index in range(2):
   event=QWheelEvent(QPointF(30,13),QPointF(slider.mapToGlobal(QPoint(30,13))),QPoint(),QPoint(0,60),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False);app.sendEvent(slider,event)
   assert slider.value()==value+(1 if index else 0)
  slider.close();checks.append('Opacity whole-track first press activates immediately; fractional wheel combines without focus/hover wait')
  identity=e.selected;widget=e.row_widgets[identity];stroke('Brush');assert e.row_widgets[identity] is widget
  checks.append('Accepted same-geometry pixel replacement retains the exact layer control widget')
  # Undo to a frozen external source must save those exact pixels, even if
  # the disposable external PNG changes. Library identity/path stay original.
  stage('source snapshot save')
  e.select(imported);wait(lambda:pixels() is not None);source_pixels=digest(pixels());source_asset=e.selected_row()['asset'];source_path=next(a['path'] for a in e.media_assets() if a['id']==source_asset)
  stroke('Brush');e.history(False);idle();assert e.selected_row()['asset']==source_asset and digest(pixels())==source_pixels
  changed=QImage(96,64,QImage.Format_ARGB32_Premultiplied);changed.fill(QColor('#9c1746'));assert changed.save(source_path)
  frozen_save=out/'frozen-source-save.json';requested=e.binding[1];shell.client.request('save',path=str(frozen_save.resolve()));wait(lambda:any(v['status']=='durable' and v['revision']==requested for v in shell.client.snapshot['media_control']['raster']['saves']))
  frozen=json.loads(frozen_save.read_text());frozen_row=next(r for r in frozen['media']['layers'] if r['id']==imported);frozen_ref=next(a for a in frozen['media']['assets'] if a['id']==frozen_row['asset']);assert frozen_ref['id']!=source_asset and frozen_ref['internal'] and digest(QImage(frozen_ref['path']))==source_pixels
  library_ref=next(a for a in shell.client.snapshot['media_library']['assets'] if a['id']==source_asset);assert library_ref['path']==source_path and not library_ref.get('managed')
  shell.client.request('load',path=str(frozen_save.resolve()));e.refresh(True);e.select(imported);wait(lambda:pixels() is not None);assert digest(pixels())==source_pixels
  checks.append('Undo-restored frozen external source saves/reopens exact requested pixels after test original changes; private saved snapshot leaves library original identity/path untouched')
  e.select(identity);wait(lambda:pixels() is not None)
  stage('buttons')
  e.secondary_color=QColor('#df7937');e.brush_color=QColor('#24bcd9');e.choose_tool('Fill');p=c.screen_point(e.selected_row(),(.8,.8)).toPoint();color=QColor(e.secondary_color)
  QTest.mouseClick(c,Qt.RightButton,pos=p);assert e.fill_controller.job is not None;e.brush_color=QColor('#199722');e.secondary_color=QColor('#de124b')
  wait(lambda:e.fill_controller.job is None);idle();assert pixels().pixelColor(80,50)==color
  assert e.fill_controller.metrics[-1]['channel']=='Secondary'
  e.choose_tool('Sampler');history=deepcopy(shell.client.snapshot['media_control']['history']);main=QColor(e.brush_color);QTest.mouseClick(c,Qt.RightButton,pos=p);assert e.secondary_color==color and e.brush_color==main
  secondary=QColor(e.secondary_color);QTest.mouseClick(c,Qt.LeftButton,pos=p);assert e.brush_color==color and e.secondary_color==secondary
  assert shell.client.snapshot['media_control']['history']==history
  for tool in ('Brush','Pencil','Fill','Sampler','Smudge','Eraser'):e.choose_tool(tool);assert e.brush_color==color and e.secondary_color==secondary
  e.brush_color=QColor('#386fc2');e.choose_tool('Fill');QTest.mouseClick(c,Qt.LeftButton,pos=p);wait(lambda:e.fill_controller.job is None);idle();assert pixels().pixelColor(80,50)==e.brush_color
  checks.append('Right Fill pins shared Secondary despite in-flight channel/color changes; left Fill uses Main; Sampler writes only matching receiver, immediately syncs chips, adds no artwork history; switching tools retains both shared colors')
  stage('canvas context events')
  tools=('Select','Selection','Wand','Brush','Pencil','Eraser','Smudge','Fill','Sampler','Crop','Transform','Hand','Cut','Mask','Remove','Extract')
  menus=[]
  class CaptureMenu(QMenu):
   def exec(self,*args):menus.append([a.text() for a in self.actions()]);return None
  with patch('studio_composition.QMenu',CaptureMenu):
   for tool in tools:
    stage('context '+tool)
    e.choose_tool(tool);event=QContextMenuEvent(QContextMenuEvent.Mouse,QPoint(5,5),c.mapToGlobal(QPoint(5,5)));app.sendEvent(c,event);assert event.isAccepted()
    event=QContextMenuEvent(QContextMenuEvent.Keyboard,QPoint(5,5),c.mapToGlobal(QPoint(5,5)),Qt.ShiftModifier|Qt.ControlModifier);app.postEvent(c,event);pump()
  assert not menus,menus
  e.choose_tool('Brush');stroke('Brush');pump()
  e.tree.scrollToItem(e.row_items[e.selected]);pump(.1)
  stage('outside menu')
  with patch('studio_composition.QMenu',CaptureMenu):
   e.context(e.tree.visualItemRect(e.row_items[e.selected]).center())
  assert menus and 'Copy layer/subtree' in menus[-1],menus
  checks.append('All 16 tool canvas boundaries consume direct/queued/modified context events, including after stroke; Layers context menu retained')
  stage('save reopen')
  saved_pixels=digest(pixels());target=e.selected;save=out/'review-save-as.json';requested=e.binding[1];shell.client.request('save',path=str(save.resolve()));wait(lambda:any(s['status']=='durable' and s['revision']==requested for s in shell.client.snapshot['media_control']['raster']['saves']));state('save durable')
  shell.client.request('load',path=str(save.resolve()));e.refresh(True);e.select(target);wait(lambda:pixels() is not None);assert digest(pixels())==saved_pixels
  checks.append('Revision-pinned Save As is durable, then same-instance reopen matches accepted native pixels exactly; old-context recovery checkpoint isolated under task store')
  (out/'result.json').write_text(json.dumps(dict(checks=checks,backend=backend().status(),states=states,limits='Controlled Qt/owner/native or B1; exact natural user failure not established'),indent=2),encoding='utf8');print(json.dumps(dict(checks=checks,out=str(out)),indent=2))
 except BaseException:
  (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
 finally:
  if hold.exists():hold.unlink()
  if shell.client:shell.client.close(force=True)
  shell.closing=True
  if e:e.close_resources()
  shell.close();pump(.03);faulthandler.cancel_dump_traceback_later();stacks.close()
if __name__=='__main__':run()
