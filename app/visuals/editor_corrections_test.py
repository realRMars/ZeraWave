"""B2 correction fixtures: exact bucket pixels, QTest widgets and owner recovery.
Automated events/pixel readbacks do not establish physical-input user acceptance.
"""
from pathlib import Path
from copy import deepcopy
import sys,os,json,time,traceback,threading,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtCore import Qt,QTimer,QPointF
from PySide6.QtGui import QImage,QColor
from PySide6.QtWidgets import QApplication,QLineEdit,QMessageBox,QToolButton,QMenu
from PySide6.QtTest import QTest
from composition import new_layer,lookup,transform
from editor_fill import bucket
from pixel_selection import encode

def data(image):return bytes(image.constBits())
def fixture():
 im=QImage(96,64,QImage.Format_ARGB32_Premultiplied);im.fill(QColor('black'))
 from PySide6.QtGui import QPainter
 p=QPainter(im);p.fillRect(5,5,30,40,QColor('#205080'));p.fillRect(55,5,30,40,QColor('#205080'));p.end();return im

def pixels():
 checks=[];row=new_layer();im=fixture();red=QColor(220,40,80,128)
 a=bucket(im,row,None,(10,10),red,0);assert a.pixelColor(10,10).alpha()==128 and a.pixelColor(60,10)==im.pixelColor(60,10) and a.pixelColor(0,0)==im.pixelColor(0,0)
 b=bucket(im,row,None,(10,10),red,0,False);assert b.pixelColor(60,10)==a.pixelColor(10,10);checks.append('enclosed region, adjacent background and disconnected identical islands; explicit all-matching option')
 for value in (QColor('white'),QColor(0,0,0,0)):
  blank=QImage(64,64,QImage.Format_ARGB32_Premultiplied);blank.fill(value);result=bucket(blank,row,None,(25,25),red,32);assert result.pixelColor(0,0).alpha()==128 and result.pixelColor(63,63)==result.pixelColor(0,0);assert bucket(result,row,None,(0,0),red,0) is None
 checks.append('uniform opaque and transparent layers, paint alpha and unchanged/no-op detection')
 threshold=QImage(8,2,QImage.Format_ARGB32_Premultiplied);threshold.fill(QColor(100,100,100));threshold.setPixelColor(1,0,QColor(132,100,100));threshold.setPixelColor(2,0,QColor(133,100,100));threshold.setPixelColor(3,0,QColor(100,100,100,222));result=bucket(threshold,row,None,(0,0),QColor('red'),32);assert result.pixelColor(1,0)==QColor('red') and result.pixelColor(2,0)==threshold.pixelColor(2,0) and result.pixelColor(3,0)==threshold.pixelColor(3,0)
 semi=QImage(8,2,QImage.Format_ARGB32_Premultiplied);semi.fill(QColor(60,120,180,128));result=bucket(semi,row,None,(0,0),red,0);assert result.pixelColor(0,0).alpha()==128;checks.append('inclusive RGBA threshold 32/33, alpha difference and semi-transparent seed')
 # Disconnected permitted islands in otherwise identical pixels may not flood through excluded gap.
 blank=QImage(96,64,QImage.Format_ARGB32_Premultiplied);blank.fill(Qt.transparent);coverage=np.zeros((64,96),np.uint8);coverage[5:45,5:35]=255;coverage[5:45,55:85]=255;coverage[5:45,5]=128;selection=encode(coverage)
 result=bucket(blank,row,selection,(10,10),QColor('red'));assert result.pixelColor(60,10).alpha()==0 and result.pixelColor(5,10).alpha()==128 and result.pixelColor(0,0).alpha()==0
 row['crop']=[.1,.1,.9,.9];row['masks']=[selection];result=bucket(blank,row,None,(15,15),QColor('blue'));assert result.pixelColor(60,10).alpha()==0 and result.pixelColor(5,10).alpha()==0
 shape=dict(shape='Ellipse',points=[[.1,.1],[.4,.1],[.4,.8],[.1,.8]],handles=[],mode='Keep',enabled=True);row['masks']=[];result=bucket(blank,row,shape,(24,24),QColor('green'));assert result.pixelColor(24,24).alpha()==255 and result.pixelColor(15,10).alpha()<255 and result.pixelColor(70,30).alpha()==0;checks.append('exact pixel/shaped selection, fractional edges, masks/crop and traversal constrained before final write')
 group=new_layer('Group');group['masks']=[selection];blank.fill(Qt.transparent);result=bucket(blank,new_layer(),None,(10,10),QColor('red'),groups=[(group,np.eye(3))]);assert result.pixelColor(60,10).alpha()==0 and result.pixelColor(5,10).alpha()==128;checks.append('projected Group masks constrain traversal and feathered writes')
 from native_raster import backend
 if backend().available:
  base=backend().storage().from_image(im);native=bucket(base,new_layer(),None,(10,10),red,0);assert data(native)==data(a);checks.append('native tiled result exact versus QImage fallback; unchanged native tile sharing')
 rng=np.random.default_rng(24);islands=rng.integers(0,2,(1024,1024),dtype=np.uint8);raw=np.repeat((islands*255)[:,:,None],4,axis=2);raw[:,:,3]=255;noise=QImage(raw.data,1024,1024,4096,QImage.Format_ARGB32_Premultiplied).copy()
 try:encode(islands*255);raise AssertionError('fixture should exceed saved-mask encoding budget')
 except ValueError:pass
 result=bucket(noise,new_layer(),None,(0,0),red,0,False);assert result is not None;checks.append('transient noisy matching region exceeds saved-mask encoding budget and still fills at full resolution')
 from editor_fill import prepare
 from raster_resources import snapshot as allocate
 from raster_tiles import allocations
 from multiprocessing.shared_memory import SharedMemory
 from unittest.mock import patch
 source=QImage(64,64,QImage.Format_ARGB32_Premultiplied);source.fill(Qt.transparent);args=(source,new_layer(),None,(0,0),red,32,True,threading.Event(),())
 prepared=prepare(args,True);names=list(allocations(prepared.source[0]))+list(allocations(prepared.transfer[0]));prepared.discard();prepared.discard()
 for name in names:
  try:lease=SharedMemory(name=name);lease.close();raise AssertionError('discarded Fill mapping leaked')
  except FileNotFoundError:pass
 captured=[]
 def failure(image):
  if captured:raise MemoryError('Injected Fill transfer allocation failure')
  pair=allocate(image);captured.append(pair[0]);return pair
 with patch('raster_resources.snapshot',side_effect=failure):
  try:prepare(args,True);raise AssertionError('allocation failure was ignored')
  except MemoryError:pass
 for name in allocations(captured[0]):
  try:lease=SharedMemory(name=name);lease.close();raise AssertionError('failed Fill preparation leaked original mapping')
  except FileNotFoundError:pass
 checks.append('worker-prepared source/result leases retire on discarded completion and partial allocation failure')
 # Exhaust every byte pair/coverage combination before relying on integer math.
 for alpha_value in range(256):
  before=np.arange(256,dtype=np.uint16)[:,None];paint=np.arange(256,dtype=np.uint16)[None,:];f=np.float32(alpha_value)/np.float32(255)
  expected=np.rint(before.astype(np.float32)*(1-f)+paint.astype(np.float32)*f).astype(np.uint8)
  actual=((before*(255-alpha_value)+paint*alpha_value+127)//255).astype(np.uint8);assert np.array_equal(actual,expected)
 checks.append('all 16777216 byte/coverage combinations match existing float32 nearest-even replacement exactly')
 from native_raster import connected_region,FillCancel
 from collections import deque
 if backend().status().get('fill_kernel'):
  for trial in range(80):
   permitted=rng.random((32,47))<(.2+(trial%6)*.14);seed=(trial%47,trial%32);expected=np.zeros_like(permitted);todo=deque([seed])
   while todo:
    x,y=todo.popleft()
    if not 0<=x<47 or not 0<=y<32 or expected[y,x] or not permitted[y,x]:continue
    expected[y,x]=True;todo.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
   original=permitted.copy();actual=connected_region(permitted,seed,threading.Event(),30);assert np.array_equal(actual,expected) and np.array_equal(permitted,original)
  for event in (threading.Event(),FillCancel()):
   event.set()
   try:connected_region(np.ones((16,16),bool),(0,0),event,30);raise AssertionError('cancel ignored')
   except ValueError as exc:assert 'cancelled' in str(exc)
  # Cancel during released-GIL native traversal and retire its bounded scratch.
  for event in (threading.Event(),FillCancel()):
   permitted=np.ones((2048,4096),bool);answer=[]
   def work():
    try:answer.append(connected_region(permitted,(1000,1000),event,30))
    except Exception as exc:answer.append(exc)
   thread=threading.Thread(target=work);thread.start();time.sleep(.005);event.set();thread.join(5);assert not thread.is_alive() and isinstance(answer[0],ValueError) and 'cancelled' in str(answer[0])
  try:connected_region(np.ones((16,16),bool),(999,0),FillCancel(),30);raise AssertionError('invalid seed accepted')
  except ValueError:pass
  checks.append('80 random fragmented connected components match independent four-neighbor oracle; input immutable; Event/native cancellation before/during work and invalid seed')
 return checks

def run():
 out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_RASTER_TEST_BARRIER=str(out/'hold-png'),ZERAWAVE_RASTER_TEST_FAIL_WRITE=str(out/'fail-write'))
 import faulthandler
 faulthandler.dump_traceback_later(40,repeat=True)
 app=QApplication([])
 from PySide6.QtGui import QFontDatabase,QFont
 QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf');app.setFont(QFont('Segoe UI',9));checks=pixels();from studio_qt import Shell
 shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1200,800);shell.show();e=None;metrics={}
 def pump():app.processEvents();time.sleep(.002)
 def wait(fn,seconds=45):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:
   pump()
   if fn():return
  raise AssertionError('timeout: '+(e.status.text() if e else 'startup'))
 def done():wait(lambda:not e.art_jobs and not e.edit_jobs and e.selected_row() and e.canvas.source_image(e.selected_row()) is not None)
 def install(im):
  target=deepcopy(e.selected_row());e.save_paint(dict(row=target['id'],asset=target['asset'],target=target,session=e.binding[0],revision=e.binding[1],tool='Fixture',base=e.canvas.source_image(target)),im);done()
 def fill(uv):
  e.choose_tool('Fill');QTest.mouseClick(c,Qt.LeftButton,pos=c.screen_point(e.selected_row(),uv).toPoint());wait(lambda:e.fill_controller.job is None);done()
 def output_pixels():
  import moderngl
  from image_layers import ImageLayers
  from cpu_projection import Projection
  ctx=moderngl.create_standalone_context(require=330);texture=ctx.texture((96,64),4);fbo=ctx.framebuffer([texture]);vertices=ctx.buffer(np.array([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes())
  class Proxy:
   screen=fbo
   def __getattr__(self,key):return getattr(ctx,key)
  gpu=ImageLayers(Proxy(),vertices)
  try:
   records={a['id']:a for a in e.media_assets()};scene=deepcopy(e.config);scene['assets']=[records[a['id']] for a in scene['assets']];scene['presentation']='Layers only'
   with ctx:gpu.request(scene,e.binding[1],e.binding[0])
   wait(lambda:not gpu.pending)
   # Qt pumping binds its own Canvas context. Rebind this independent GPU
   # fixture before publication/drawing/readback; retain exact pixel equality.
   with ctx:
    assert not gpu.error,gpu.snapshot();fbo.use();fbo.clear(0,0,0,0);ctx.viewport=(0,0,96,64);gpu.draw((96,64));actual=np.frombuffer(fbo.read(components=4,alignment=1),np.uint8).reshape(64,96,4)[::-1][:,:,[2,1,0,3]].copy()
   expected=Projection().render(c,96,64,np.array([[96,0,48],[0,64,32],[0,0,1]],float))
   from PySide6.QtGui import QPainter
   presented=QImage(96,64,QImage.Format_ARGB32_Premultiplied);presented.fill(QColor('black'));painter=QPainter(presented);painter.drawImage(0,0,expected);painter.end()
   if actual.tobytes()!=data(presented):np.savez(out/'fill-output-difference.npz',actual=actual,expected=np.frombuffer(presented.constBits(),np.uint8).reshape(64,96,4))
   assert actual.tobytes()==data(presented)
   return hashlib.sha256(actual.tobytes()).hexdigest()
  finally:
   with ctx:gpu.close();vertices.release();fbo.release();texture.release()
   ctx.release()
 try:
  wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;c=e.canvas;e.reveal();e.resize_canvas((96,64),False);e.blank_layer();done();parent=e.selected;install(fixture())
  view=e.editor_view;state=deepcopy(e.config);tool=c.tool;history=deepcopy(shell.client.snapshot['media_control']['history'])
  assert not any(hasattr(view,key) for key in ('details_area','details_button','details_close','info','undo_action','redo_action'))
  assert not any(hasattr(e,key) for key in ('backend_status','projection_status','target_status'))
  assert not view.menuBar().actions() and any(a.text().replace('&','')=='Edit' for a in shell.menu_bar.actions())
  assert not hasattr(e.selection_controls,'mode')
  for _ in range(5):e.sync_tool_ui();e.frames();e.refresh(True);pump()
  assert e.config==state and c.tool==tool and shell.client.snapshot['media_control']['history']==history;checks.append('local Edit/Details and selection-method dropdown removed; main Edit, decoding/refresh/history retain working actions')
  cursors={}
  for method in ('Select','Lasso','Wand','Brush','Pencil','Eraser','Sampler','Smudge','Fill','Crop','Transform','Hand'):
   QTest.mouseClick(e.direct_buttons[method],Qt.LeftButton);pump();assert c.cursor_method()==method
   assert [k for k,b in e.direct_buttons.items() if b.isChecked()]==[method]
   for dpr in (1.,1.5,2.):
    cursor=c.tool_cursor(dpr);pix=cursor.pixmap();assert cursor.hotSpot()==QPointF(4,4).toPoint() and abs(pix.devicePixelRatioF()-dpr)<.001 and pix.width()==round(42*dpr)
   cursors[method]=hashlib.sha256(data(c.tool_cursor(1.).pixmap().toImage())).hexdigest()
   assert c.cursor().hotSpot()==c.tool_cursor().hotSpot()
   c.drag=('pan',QPointF(),QPointF());c.apply_tool_cursor();assert c.cursor().shape()==Qt.ClosedHandCursor;c.cancel_drag();assert c.cursor().pixmap().cacheKey()==c.tool_cursor().pixmap().cacheKey()
   e.quick_colors.size.setFocus();pump();c.setFocus();pump();assert c.cursor_method()==method and c.cursor().pixmap().cacheKey()==c.tool_cursor().pixmap().cacheKey()
  assert len(set(cursors.values()))==12;assert e.quick_colors.size.lineEdit().cursor().shape()!=Qt.BitmapCursor
  for key,method in ((Qt.Key_V,'Select'),(Qt.Key_M,'Select'),(Qt.Key_L,'Lasso'),(Qt.Key_W,'Wand')):
   QTest.keyClick(c,key);pump();assert c.cursor_method()==method and e.direct_buttons[method].isChecked()
  view.grab().save(str(out/'direct-tools-no-details.png'));metrics['cursor_hashes']=cursors;checks.append('12 distinct vector cursors at DPR1/1.5/2 with logical hotspot4,4; pan/cancel/focus restore; direct states and V/M/L/W agree; controls retain normal cursor')
  for tool in ('Brush','Pencil','Eraser','Smudge','Sampler','Select','Crop','Fill'):
   QTest.mouseClick(e.direct_buttons[tool],Qt.LeftButton);pump();assert c.tool==tool
   for _ in range(2):QTest.mouseDClick(e.direct_buttons[tool],Qt.LeftButton);pump();assert not e.palettes and e.color_toolbar.isVisible()
   e.tool_settings(tool);assert not e.palettes
  q=e.quick_colors;e.choose_tool('Brush');e.tool_value('Brush','size',17.123456);e.tool_value('Brush','hardness',.73123456);e.tool_value('Brush','flow',.421234);assert abs(q.size.value()-17.123456)<1e-9
  q.fields['flow'].setValue(63.125);assert e.brush['flow']==.63125;e.choose_tool('Pencil');q.size.setValue(3.25);e.choose_tool('Brush');assert e.brush['size']==17.123456 and e.tool_states['Pencil']['brush']['size']==3.25
  e.apply_brush_preset('Brush',48,.2);assert q.size.value()==48 and q.fields['hardness'].value()==20
  c.setFocus();QTest.keyClick(c,Qt.Key_BracketRight);assert abs(q.size.value()-57.6)<1e-8;QTest.keyClick(c,Qt.Key_4);assert q.opacity.value()==40
  field=q.size.lineEdit();field.setFocus();field.selectAll();QTest.keyClicks(field,'21.75');before_text=field.text();e.sync_tool_ui();assert field.text()==before_text;QTest.keyClick(field,Qt.Key_Return);assert e.brush['size']==21.75
  assert len(e.settings_widgets['Brush'])==6;checks.append('tool buttons/hotkeys, double-click/settings share sidebar; exact independent fields, presets, hotkeys and uninterrupted typing')
  # Saved-toolbar state roundtrip and short/narrow scroll reachability (Qt API, not physical dragging).
  from PySide6.QtCore import QByteArray
  saved=view.saveState();view.removeToolBar(e.color_toolbar);view.addToolBar(Qt.RightToolBarArea,e.color_toolbar);assert view.restoreState(saved);assert view.toolBarArea(e.color_toolbar)==Qt.LeftToolBarArea
  e.choose_tool('Select');shell.resize(900,600);pump();scroll=e.tool_scroll.verticalScrollBar();scroll.setValue(scroll.maximum());pump();assert q.selection_host.isVisible() and not q.boundary_actions.isVisible();checks.append('saved-layout toolbar redock and selection actions in shared sidebar; physical float/drag remains Robert review')
  c.discard();e.choose_tool('Fill');q.set_color(QColor(220,40,80,128));before_asset=e.selected_row()['asset'];count=shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count'];assert c.tool=='Fill' and e.selected_row()['asset']==before_asset
  hold=out/'hold-png';hold.touch();before=data(c.source_image(e.selected_row()));fill((.1,.2));after=data(c.source_image(e.selected_row()));assert before!=after and c.source_image(e.selected_row()).pixelColor(60,12).name()=='#205080';assert shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count']==count+1
  runtime=next(a for a in e.media_assets() if a['id']==e.selected_row()['asset']);assert not Path(runtime['path']).exists() and shell.client.snapshot['media_control']['raster']['pending']>0;paint_output=output_pixels()
  e.history(False,'drawing');done();assert data(c.source_image(e.selected_row()))==before;e.history(True,'drawing');done();assert data(c.source_image(e.selected_row()))==after;assert output_pixels()==paint_output;hold.unlink();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0);checks.append('Fill accepted and Canvas/output pixels equal before delayed PNG durability; late PNG after Undo/Redo preserves current revision')
  count=shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count'];fill((.1,.2));assert shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count']==count;checks.append('activation does not fill; successful click one drawing history operation; exact Undo/Redo and no-op omission')
  # Actual Fill PNG failure preserves accepted pixels and explicit Save As recovery.
  fail=out/'fail-write';fail.touch();before_failure=data(c.source_image(e.selected_row()));fill((.65,.2));failed_pixels=data(c.source_image(e.selected_row()));assert failed_pixels!=before_failure
  wait(lambda:bool(shell.client.snapshot['media_control']['raster']['failures']));failed_id=e.selected_row()['asset'];failed_output=output_pixels();recovery=out/'fill-failure-recovery.json';shell.client.request('save',path=str(recovery),save_id='fill-failure-recovery');wait(lambda:recovery.exists() and not shell.client.snapshot['media_control']['raster']['failures']);assert e.selected_row()['asset']==failed_id and data(c.source_image(e.selected_row()))==failed_pixels and output_pixels()==failed_output;fail.unlink()
  e.history(False,'drawing');done();assert data(c.source_image(e.selected_row()))==before_failure
  checks.append('actual Fill failed PNG retains accepted pixels/history/output; Save As secures revision without reinstall; exact Undo after recovery')
  # transformed target click through native source UV and own crop/flips/parent placement.
  before_config=deepcopy(e.config);e.selected_row().update(transform=transform(.04,-.02,.75,1.15,21),flip_x=True,flip_y=True,crop=[.05,.05,.95,.95]);e.commit('Transformed Fill fixture',before_config);done();fill((.65,.2));assert c.source_image(e.selected_row()).pixelColor(60,12).alpha()==128;checks.append('rotated/nonuniform scale/flipped/cropped click targets native source pixels')
  e.row_flag(parent,'locked');state=deepcopy(e.config);fill((.2,.3));assert e.config==state;e.row_flag(parent,'locked');e.row_flag(parent,'enabled');state=deepcopy(e.config);fill((.2,.3));assert e.config==state;e.row_flag(parent,'enabled');checks.append('locked and hidden target reject without history/artwork mutation')
  group=new_layer('Group');group.update(transform=transform(.1,.05,.8,1.1,17),crop=[0.,0.,.5,1.]);before_config=deepcopy(e.config);e.selected_row().update(parent=group['id'],transform=transform(),flip_x=False,flip_y=False,crop=[0.,0.,1.,1.]);e.config['layers'].append(group);e.commit('Group Fill coverage fixture',before_config);done()
  blank=QImage(96,64,QImage.Format_ARGB32_Premultiplied);blank.fill(Qt.transparent);install(blank);fill((.2,.2));assert c.source_image(e.selected_row()).pixelColor(10,12).alpha()==128 and c.source_image(e.selected_row()).pixelColor(80,12).alpha()==0
  e.row_flag(group['id'],'locked');state=deepcopy(e.config);fill((.2,.2));assert e.config==state;e.row_flag(group['id'],'locked');e.row_flag(group['id'],'enabled');state=deepcopy(e.config);fill((.2,.2));assert e.config==state;e.row_flag(group['id'],'enabled');checks.append('actual rotated/scaled parent Group crop and Group lock/visibility protect selected child')
  state=deepcopy(e.config);e.select(group['id']);e.fill_controller.click(QPointF(c.rect().center()));assert e.config==state and e.fill_controller.job is None;e.select(None);e.fill_controller.click(QPointF(c.rect().center()));assert e.config==state and e.fill_controller.job is None;e.select(parent)
  from unittest.mock import patch
  with patch.object(c,'source_image',return_value=None):e.fill_controller.click(QPointF(c.rect().center()));assert e.config==state and e.fill_controller.job is None
  checks.append('incompatible Group, absent target and unavailable source reject before work/history')
  # Controlled completion delay: tool switch, target switch, Undo and session changes must all reject.
  from unittest.mock import patch
  import editor_fill
  original=editor_fill.bucket
  for action in ('tool','target','undo','session'):
   e.select(parent);e.choose_tool('Fill');started=threading.Event();release=threading.Event()
   def delayed(*args):started.set();release.wait(10);return original(*args)
   with patch('editor_fill.bucket',delayed):
    e.fill_controller.click(c.screen_point(e.selected_row(),(.2,.2)));wait(started.is_set)
    if action=='tool':e.choose_tool('Brush')
    elif action=='target':e.select(None)
    elif action=='undo':e.history(False,'drawing');done()
    else:e.binding=('stale-test',e.binding[1])
    release.set();state=deepcopy(e.config);wait(lambda:e.fill_controller.job is None);assert e.config==state
    if action=='session':e.refresh(True)
  checks.append('blocked-worker stale completion after tool/target/Undo/session changes cannot mutate document')
  e.select(parent);c.discard();e.choose_tool('Brush');state=deepcopy(e.config);before=data(c.source_image(e.selected_row()));z=c.view().m11();QTest.mouseClick(view.zoom_buttons[0],Qt.LeftButton);assert abs(c.zoom-z*1.25)<1e-8;QTest.mouseClick(view.zoom_buttons[1],Qt.LeftButton);assert abs(c.zoom-z)<1e-8;assert 'Zoom' not in e.direct_buttons;QTest.keyClick(c,Qt.Key_Z);assert c.tool=='Brush';assert e.config==state and data(c.source_image(e.selected_row()))==before;checks.append('magnifier factors preserved; obsolete Zoom button/hotkey removed; zoom changes only view')
  from PySide6.QtCore import QPoint
  from PySide6.QtGui import QWheelEvent
  c.setFocus();z=c.view().m11();event=QWheelEvent(QPointF(c.rect().center()),QPointF(c.mapToGlobal(c.rect().center())),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.ScrollUpdate,False);app.sendEvent(c,event);assert abs(c.zoom-max(.02,min(8,z*1.15)))<1e-8
  c.zoom=1.;zoom_state=deepcopy(e.config);zoom_history=deepcopy(shell.client.snapshot['media_control']['history'])
  for delta,modifier,factor in ((120,Qt.ControlModifier,1.02),(-120,Qt.ControlModifier,1/1.02),(60,Qt.ControlModifier,1.02**.5),(-60,Qt.ControlModifier,1.02**-.5),(120,Qt.NoModifier,1.15),(-120,Qt.NoModifier,1/1.15)):
   previous=c.zoom;event=QWheelEvent(QPointF(c.rect().center()),QPointF(),QPoint(),QPoint(0,delta),Qt.NoButton,modifier,Qt.ScrollUpdate,False);app.sendEvent(c,event);assert abs(c.zoom-previous*factor)<1e-10
  event=QWheelEvent(QPointF(c.rect().center()),QPointF(),QPoint(0,60),QPoint(),Qt.NoButton,Qt.ControlModifier,Qt.ScrollUpdate,False);app.sendEvent(c,event);assert abs(c.zoom-1.02**.5)<1e-10
  c.zoom=1.
  assert abs(c.zoom-1.)<1e-10 and e.config==zoom_state and shell.client.snapshot['media_control']['history']==zoom_history
  checks.append('ordinary15% and Ctrl-wheel2%, both directions and half notches without drift; view-only with unchanged selection/pixels/history')
  origin=QPointF(c.pan);centre=c.rect().center();QTest.mousePress(c,Qt.MiddleButton,pos=centre);QTest.mouseMove(c,centre+QPoint(10,20));QTest.mouseRelease(c,Qt.MiddleButton,pos=centre+QPoint(10,20));assert c.pan!=origin
  origin=QPointF(c.pan);QTest.keyPress(c,Qt.Key_Space);QTest.mousePress(c,Qt.LeftButton,pos=centre);QTest.mouseMove(c,centre+QPoint(5,7));QTest.mouseRelease(c,Qt.LeftButton,pos=centre+QPoint(5,7));QTest.keyRelease(c,Qt.Key_Space);assert c.pan!=origin and not c.space_pan
  view.fit();view.actual();assert e.config==state and data(c.source_image(e.selected_row()))==before;checks.append('wheel factor/limit, middle/Space panning, Fit/native-detail preserve artwork and scene')
  c.discard();before_scene=deepcopy(e.config);branch=new_layer('Group',name='Delete root');nested=new_layer('Group',name='Nested');nested['parent']=branch['id'];leaf=deepcopy(lookup(e.config)[parent]);leaf.update(id=__import__('uuid').uuid4().hex,parent=nested['id'],name='Deep artwork',order=0);branch['order']=max(r['order'] for r in e.config['layers'] if r['parent'] is None)+1;e.config['layers'] += [branch,nested,leaf];assert e.commit('Deep deletion fixture',before_scene);done();e.select(branch['id']);before_scene=deepcopy(e.config);before_history=deepcopy(shell.client.snapshot['media_control']['history'])
  with patch.object(QMessageBox,'question',return_value=QMessageBox.No) as confirm:
   assert not e.delete(branch['id']);assert confirm.call_args.args[2]=='Everything within layer will be deleted' and confirm.call_args.args[3]==QMessageBox.Yes|QMessageBox.No and confirm.call_args.args[4]==QMessageBox.No
  assert e.config==before_scene and shell.client.snapshot['media_control']['history']==before_history
  # Exercise the actual Delete button and a real No modal, not only the API.
  from PySide6.QtWidgets import QPushButton
  with patch.object(QMessageBox,'question',return_value=QMessageBox.No) as confirm:
   QTest.mouseClick(next(b for b in e.findChildren(QPushButton) if b.text()=='Delete'),Qt.LeftButton);assert confirm.called
  print('CHECK: begin real No modal',flush=True)
  def cancel_modal():
   dialog=app.activeModalWidget();assert dialog.standardButtons()==QMessageBox.Yes|QMessageBox.No and dialog.defaultButton()==dialog.button(QMessageBox.No);dialog.done(QMessageBox.No)
  QTimer.singleShot(10,cancel_modal);assert not e.delete(branch['id']);assert e.config==before_scene and shell.client.snapshot['media_control']['history']==before_history
  e.row_flag(leaf['id'],'locked');wait(lambda:not e.edit_jobs);locked=deepcopy(e.config)
  with patch.object(QMessageBox,'question') as confirm:assert not e.delete(branch['id']);assert not confirm.called
  assert e.config==locked;e.row_flag(leaf['id'],'locked');wait(lambda:not e.edit_jobs);before_scene=deepcopy(e.config)
  def mutate(*args):e.binding=('changed-during-confirmation',e.binding[1]);return QMessageBox.Yes
  with patch.object(QMessageBox,'question',side_effect=mutate):assert not e.delete(branch['id'])
  assert e.config==before_scene;e.refresh(True);e.select(branch['id']);before_scene=deepcopy(e.config)
  print('CHECK: real No modal complete; revision callback',flush=True)
  def change_revision(*args):e.row_flag(leaf['id'],'locked');return QMessageBox.Yes
  with patch.object(QMessageBox,'question',side_effect=change_revision):assert not e.delete(branch['id'])
  wait(lambda:not e.edit_jobs);assert lookup(e.config)[leaf['id']]['locked'] and branch['id'] in lookup(e.config)
  # Locks are existing retained flags, intentionally outside semantic Undo.
  e.row_flag(leaf['id'],'locked');wait(lambda:not e.edit_jobs);assert e.config==before_scene;e.select(branch['id']);e.tree.blockSignals(True);e.row_items[parent].setSelected(True);e.tree.blockSignals(False)
  print('CHECK: revision rejection complete; context delete',flush=True)
  class ScriptMenu(QMenu):
   def exec(self,*args):
    action=next(a for a in self.actions() if a.text()=='Delete layer/subtree');action.trigger();return action
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes),patch('studio_composition.QMenu',ScriptMenu):e.context(e.tree.visualItemRect(e.row_items[branch['id']]).center())
  print('CHECK: context delete returned',flush=True)
  wait(lambda:not e.edit_jobs);assert not {branch['id'],nested['id'],leaf['id']}&set(lookup(e.config)) and parent in lookup(e.config)
  e.history(False,'editor');wait(lambda:not e.edit_jobs);assert e.config==before_scene
  e.history(True,'editor');wait(lambda:not e.edit_jobs);assert not {branch['id'],nested['id'],leaf['id']}&set(lookup(e.config)) and parent in lookup(e.config)
  e.history(False,'editor');wait(lambda:not e.edit_jobs);assert e.config==before_scene
  branch_save=out/'branches.json';shell.client.request('save',path=str(branch_save),save_id='branch-review');wait(lambda:branch_save.exists() and shell.client.snapshot['media_control']['raster']['pending']==0);old_session=e.binding[0];shell.client.request('load',path=str(branch_save));wait(lambda:e.binding[0]!=old_session);assert e.config['layers']==before_scene['layers'] and e.config['editor']==before_scene['editor'] and e.config['canvas']==before_scene['canvas'];e.select(parent);done();checks.append('Delete button/row-context and real No modal; exact Yes/No defaultNo message; complete deep closure; protected child rejects whole branch; modal session/revision/protection change rejected; explicit row excludes unrelated selected sibling; Undo/Redo and Save/reopen preserve full hierarchy/settings')
  # Bounded large-image compute on the existing worker, with event-loop heartbeat.
  large=QImage(4096,2048,QImage.Format_ARGB32_Premultiplied);large.fill(Qt.transparent);beats=[];timer=QTimer();timer.setInterval(10);timer.timeout.connect(lambda:beats.append(time.perf_counter()));timer.start();began=time.perf_counter();job=e.pool.submit(bucket,large,new_layer(),None,(200,200),QColor(20,80,160,200));wait(job.done,60);elapsed=time.perf_counter()-began;timer.stop();result=job.result();assert result.width()==4096 and result.height()==2048 and result.pixelColor(4095,2047).alpha()==200 and len(beats)>2;metrics['large_compute']=dict(dimensions=[4096,2048],elapsed_ms=elapsed*1000,heartbeat_count=len(beats),max_heartbeat_gap_ms=max(np.diff(beats))*1000 if len(beats)>1 else None);checks.append('4096x2048 native-resolution fill computation with concurrent Qt heartbeat; no saved-mask encoding')
  # Accept a complete supported 8 MP Fill through real owner/PNG path as well.
  large_path=out/'large-transparent.png';assert large.save(str(large_path));shell.client.request('media_import',paths=[str(large_path)]);wait(lambda:any(a.get('path')==str(large_path) and a.get('status')=='Ready' for a in e.media_assets()));large_asset=next(a for a in e.media_assets() if a.get('path')==str(large_path));assert e.add_asset(large_asset);parent=e.selected;done();assert c.source_image(e.selected_row()).width()==4096;before_config=deepcopy(e.config);e.selected_row().update(transform=transform(),flip_x=False,flip_y=False,crop=[0.,0.,1.,1.]);e.commit('Large Fill identity fixture',before_config);done()
  e.choose_tool('Fill');q.set_color(QColor(20,80,160,200));beats=[];timer.start();began=time.perf_counter();fill((.5,.5));accepted_ms=(time.perf_counter()-began)*1000;timer.stop();assert c.source_image(e.selected_row()).pixelColor(4095,2047).alpha()==200
  wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0);metrics['large_acceptance']=dict(dimensions=[4096,2048],click_to_observed_acceptance_ms=accepted_ms,click_to_observed_durability_ms=(time.perf_counter()-began)*1000,heartbeat_count=len(beats),max_heartbeat_gap_ms=max(np.diff(beats))*1000 if len(beats)>1 else None);before=data(c.source_image(e.selected_row()));checks.append('4096x2048 actual Fill acceptance, heartbeat gaps and separate PNG durability measured')
  save=out/'review.json';shell.client.request('save',path=str(save),save_id='b2-correction-review');wait(lambda:save.exists() and shell.client.snapshot['media_control']['raster']['pending']==0);stored=json.loads(save.read_text());asset=lookup(stored['media'])[parent]['asset'];assert asset;old_session=e.binding[0];shell.client.request('load',path=str(save));wait(lambda:e.binding[0]!=old_session);e.select(parent);done();assert data(c.source_image(e.selected_row()))==before;checks.append('Save As/reopen exact accepted raster pixels through portable PNG durability')
  metrics['fills']=e.fill_controller.metrics;(out/'RESULT.json').write_text(json.dumps(dict(checks=checks,metrics=metrics,evidence='QTest/widget API, CPU/native pixel fixtures; no physical Computer Use acceptance'),indent=2));print('PASS',checks)
 except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc());raise
 finally:
  hold=out/'hold-png'
  if hold.exists():hold.unlink()
  if shell.client:shell.client.close(force=True)
  shell.closing=True
  if e:e.close_resources()
  shell.close();app.processEvents()
if __name__=='__main__':run()
