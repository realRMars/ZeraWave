"""Production Layers/owner reconciliation; synthetic Qt input, no physical acceptance."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,time,json,hashlib,traceback,uuid,faulthandler
ROOT=Path(os.environ.get('ZERAWAVE_TEST_ROOT',r'C:\ZeraWave'))
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtCore import Qt,QTimer,QPoint,QPointF,QEvent
from PySide6.QtGui import QImage,QColor,QMouseEvent,QDrag,QWheelEvent
from PySide6.QtWidgets import QApplication,QMessageBox,QMenu
from PySide6.QtTest import QTest
from shiboken6 import isValid,delete as delete_qt
import studio_qt
from composition import lookup,world_matrix
from layer_ordering import siblings

def run(folder):
 out=Path(folder);out.mkdir(parents=True,exist_ok=False);checks=[];states=[];errors=[];app=QApplication([])
 diagnostic=(out/'threads.log').open('w');faulthandler.dump_traceback_later(40,repeat=True,file=diagnostic)
 os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
 original=studio_qt.Shell.error
 def error(self,*a,**k):
  with patch.object(studio_qt,'ROOT',out):return original(self,*a,**k)
 studio_qt.Shell.error=error
 def hook(t,v,tb):errors.append(''.join(traceback.format_exception(t,v,tb)))
 sys.excepthook=hook
 print('construct',flush=True);shell=studio_qt.Shell(out/'layout.json',out/'owner.log');shell.resize(1100,760);shell.show();e=shell.image_editor;print('constructed',flush=True)
 def pump(seconds=.03):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:app.processEvents();time.sleep(.001)
 def wait(fn,seconds=25):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:
   pump(.01)
   if fn():return
  raise AssertionError('Timeout '+e.status.text())
 def idle():wait(lambda:not e.art_jobs and not e.edit_jobs and e.binding==(shell.client.snapshot['media_control']['session'],shell.client.snapshot['media_control']['revision']))
 def request(a,**k):
  f=shell.client.submit(a,**k);wait(f.done);return f.result()
 def image_sha(image):
  if hasattr(image,'to_qimage'):image=image.to_qimage()
  return hashlib.sha256(bytes(image.constBits())).hexdigest()
 def capture(label):
  idle();e.reveal();pump();owner=deepcopy(shell.client.snapshot['values']['media']);gui=deepcopy(e.config);nodes=[]
  def visit(parent):
   for i in range(parent.childCount()):
    node=parent.child(i);identity=node.data(0,Qt.UserRole);nodes.append((identity,node.parent().data(0,Qt.UserRole) if node.parent() else None));visit(node)
  visit(e.tree.invisibleRootItem());assert len(nodes)==len(gui['layers'])==len(owner['layers'])
  assert set(k for k,p in nodes)==set(lookup(gui))==set(lookup(owner))
  assert dict(nodes)=={r['id']:r['parent'] for r in owner['layers']}
  assert gui['layers']==owner['layers'],label
  assert all(isValid(n) and n.treeWidget() is e.tree for n in e.row_items.values())
  assert all(isValid(w) and e.tree.itemWidget(e.row_items[k],0) is w for k,w in e.row_widgets.items())
  for parent in {r['parent'] for r in gui['layers']}:
   n=e.row_items[parent] if parent else e.tree.invisibleRootItem()
   assert [n.child(i).data(0,Qt.UserRole) for i in range(n.childCount())]==[r['id'] for r in siblings(gui,parent)]
  pixels={}
  for r in gui['layers']:
   if r['type'] in ('Image','Artwork','Paint','Video'):
    try:wait(lambda r=r:e.canvas.source_image(r) is not None)
    except Exception:
     (out/'missing-source.json').write_text(json.dumps(dict(row=r,snapshot=shell.client.snapshot,image_errors=e.image_errors,image_keys=list(e.images)),indent=2),encoding='utf8');raise
    pixels[r['id']]=image_sha(e.canvas.source_image(r))
  e.canvas.repaint();pump();e.canvas.grab().save(str(out/(str(len(states))+'-canvas.png')))
  composite=getattr(e.canvas,'composite_image',None)
  state=dict(label=label,revision=e.binding[1],owner=owner,gui=gui,tree=nodes,pixels=pixels,composite=image_sha(composite) if composite is not None else None,history=shell.client.snapshot['media_control']['history'])
  states.append(state);(out/'states.json').write_text(json.dumps(states,indent=2),encoding='utf8');assert not errors,errors;return state
 def global_blank():
  print('global blank',e.binding,flush=True)
  class Menu(QMenu):
   def exec(menu,*a):next(a for a in menu.actions() if a.text()=='New Layer').trigger()
  with patch('studio_composition.QMenu',Menu):e.add_menu()
  idle();return e.selected
 def internal_drop(ids,anchor,placement):e.drop_layers(ids,anchor,placement);idle()
 result='FAIL';failure=None;drag_probe=[]
 try:
  print('initial wait',flush=True);wait(lambda:not shell.client.snapshot['media_library']['loading']);print('resize',flush=True);e.resize_canvas((64,48),False);idle();print('resized',flush=True)
  a=global_blank();e.edit('name','Root A','Fixture label');idle();b=global_blank();e.edit('name','Root B','Fixture label');idle()
  e.select(a);e.blank_child(a);idle();child=e.selected
  e.select(child);root=global_blank();assert lookup(e.config)[root]['parent'] is None
  e.select(child);e.blank_layer(True);idle();grand=e.selected;assert lookup(e.config)[grand]['parent']==child
  e.select(None);root2=global_blank();assert lookup(e.config)[root2]['parent'] is None
  first=capture('root and explicit child creation');checks.append('Global + New Layer root with root/nested/no selection; explicit row child/Inside retained')
  # Actual Qt painting on same own raster, including size512 and color changes.
  e.select(a);e.choose_tool('Brush');e.brush['size']=512.;e.brush_color=QColor('#cc2255');e.brush['flow']=1.;e.brush['hardness']=1.;e.brush['opacity']=1.
  e.reveal();pump(.1);point=e.canvas.rect().center()
  for kind,pos,button,buttons in [(QEvent.MouseButtonPress,point,Qt.LeftButton,Qt.LeftButton),(QEvent.MouseMove,point+QPoint(8,2),Qt.NoButton,Qt.LeftButton),(QEvent.MouseButtonRelease,point+QPoint(8,2),Qt.LeftButton,Qt.NoButton)]:
   app.sendEvent(e.canvas,QMouseEvent(kind,QPointF(pos),QPointF(e.canvas.mapToGlobal(pos)),button,buttons,Qt.NoModifier))
  idle()
  painted=capture('large brush accepted');assert painted['pixels'][a]!=first['pixels'][a];checks.append('Actual Qt large Brush/color path changes accepted own pixels')
  # Real image/video imports extend the blank and painted raster hierarchy.
  from media_foundation_test import fixture
  video_path=fixture(out);image_path=out/'authored-image.png'
  image=QImage(64,48,QImage.Format_RGBA8888);image.fill(QColor('#22ba77'));assert image.save(str(image_path))
  request('media_import',paths=[str(image_path),str(video_path)])
  wait(lambda:len(shell.client.snapshot['media_library']['assets'])>=2 and not shell.client.snapshot['media_library']['pending'])
  assets={r['path']:r for r in shell.client.snapshot['media_library']['assets']}
  e.add_asset(assets[str(image_path)]);idle();image_id=e.selected
  e.add_asset(assets[str(video_path)],kind='Video');idle();video_id=e.selected
  wait(lambda:e.canvas.source_image(lookup(e.config)[video_id]) is not None)
  capture('mixed raster image video hierarchy')
  # Opacity uses the live identity-bound row control after reordering.
  e.select(a);pump();slider=e.row_widgets[a].opacity
  for kind,pos,button,buttons in [(QEvent.MouseButtonPress,QPoint(slider.width()//3,13),Qt.LeftButton,Qt.LeftButton),(QEvent.MouseMove,QPoint(slider.width()//2,13),Qt.NoButton,Qt.LeftButton),(QEvent.MouseButtonRelease,QPoint(slider.width()//2,13),Qt.LeftButton,Qt.NoButton)]:
   app.sendEvent(slider,QMouseEvent(kind,QPointF(pos),QPointF(slider.mapToGlobal(pos)),button,buttons,Qt.NoModifier));pump()
  wait(lambda:e.slider_before is None);idle();opacity=capture('row opacity drag');assert 0<lookup(e.config)[a]['opacity']<1
  slider=e.row_widgets[a].opacity;p=QPointF(slider.rect().center());old=lookup(e.config)[a]['opacity']
  app.sendEvent(slider,QWheelEvent(p,slider.mapToGlobal(p.toPoint()),QPoint(),QPoint(0,-120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False));pump(.25);wait(lambda:e.slider_before is None);idle();capture('row opacity wheel');assert lookup(e.config)[a]['opacity']<old
  checks.append('Identity-bound row opacity press/drag/release and immediate wheel retain accepted values')
  # Model-backed production commit operations, every outcome checked, mixed branches.
  for label,ids,anchor,placement in [('sibling above',[a],b,'above'),('sibling below',[a],b,'below'),('nest root',[b],a,'inside'),('out to root',[b],root,'above'),('branch move',[a],root2,'inside'),('image reorder',[image_id],b,'above'),('image nest',[image_id],a,'inside'),('video nest',[video_id],image_id,'inside'),('video out',[video_id],root,'above'),('mixed branch reorder',[a],root,'above')]:
   before=capture('before '+label);wm={k:world_matrix(e.config,k).tolist() for k in ids};internal_drop(ids,anchor,placement);after=capture(label)
   assert before['pixels']==after['pixels'];import numpy as np
   assert all(np.allclose(wm[k],world_matrix(e.config,k)) for k in ids)
   e.history(False,'layers');undone=capture('undo '+label);assert undone['gui']['layers']==before['gui']['layers'] and undone['pixels']==before['pixels']
   e.history(True,'layers');redone=capture('redo '+label);assert redone['gui']['layers']==after['gui']['layers'] and redone['pixels']==after['pixels']
  checks.append('Sibling reorder, nest, move-out, subtree transforms, every owner/GUI/tree/pixel outcome and exact Undo/Redo')
  for ids,anchor,placement in [([a],a,'inside'),([a],grand,'inside'),([a],'missing-parent','inside'),([a],b,'invalid'),([a],video_id,'inside')]:
   before=capture('before invalid');internal_drop(ids,anchor,placement);after=capture('invalid intact');assert after['gui']==before['gui'];assert after['history']['commands']==before['history']['commands']
  for _ in range(4):
   internal_drop([b],root,'inside');capture('repeated nest');internal_drop([b],root2,'above');capture('repeated out')
  checks.append('Self/descendant/missing/invalid drops preserve complete document and history; repeated operations')
  # Up/Down production buttons retain boundary no-ops and exact siblings.
  e.select(b);pump();parent=lookup(e.config)[b]['parent']
  for button in (e.order_up,e.order_down):
   for _ in range(8):
    before=capture('before arrow');enabled=button.isEnabled();QTest.mouseClick(button,Qt.LeftButton);after=capture('arrow')
    assert lookup(e.config)[b]['parent']==parent and after['pixels']==before['pixels']
    if not enabled:assert after['gui']==before['gui'] and after['history']['commands']==before['history']['commands']
  checks.append('Production Up/Down Qt buttons and disabled boundary no-ops preserve descendants and pixels')
  # Owner submission survives a view-install failure, without releasing accepted work.
  e.select(b);before=capture('before view failure')
  with patch.object(e,'populate',side_effect=RuntimeError('controlled row display failure')):e.edit('name','Root B recovered','View admission recovery')
  after=capture('accepted despite view failure');assert lookup(e.config)[b]['name']=='Root B recovered' and after['pixels']==before['pixels']
  e.history(False,'layers');restored=capture('undo accepted display failure');assert restored['gui']['layers']==before['gui']['layers']
  checks.append('A controlled row installation exception does not reject or dispose of an already submitted owner edit')
  # Continuous scrub and exact Ctrl-wheel source frames are unchanged by row moves.
  e.select(video_id);e.reveal();pump(.1);v=e.video
  def displayed():
   state=shell.client.snapshot['media_frames'].get(video_id,{});shown=getattr(e,'media_presented',{}).get(video_id,{})
   return shown if shown.get('generation')==state.get('generation') and not state.get('seek_pending') else None
  def settled():wait(lambda:not v.pending and (v.future is None or v.future.done()));idle();wait(displayed)
  def seek_point(f):return QPoint(round(8+f*(v.seek.width()-16)),v.seek.height()//2)
  observed=[];QTest.mousePress(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.2));pump(.15)
  for f in (.65,.3,.75,.4):
   began=time.perf_counter();QTest.mouseMove(v.seek,seek_point(f));target=v.seek.value()/10000*v.source_duration()
   wait(lambda:displayed() and 0<=target-displayed()['pts']<1/24+1e-6,5)
   observed.append(dict(pts=displayed()['pts'],pixels=image_sha(e.images[video_id]),fraction=f,wall=time.perf_counter(),wait_ms=(time.perf_counter()-began)*1000))
  QTest.mouseRelease(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.4));settled();assert len({r['pts'] for r in observed})>=3 and len({r['pixels'] for r in observed})>=3,observed
  v.queue('scrub',dict(position=2.5,final=True,resume=False));settled();assert abs(displayed()['pts']-2.5)<1e-6
  for count,target in ((1,2.5+1/24),(-1,2.5)):
   p=QPointF(v.seek.rect().center());app.sendEvent(v.seek,QWheelEvent(p,v.seek.mapToGlobal(p.toPoint()),QPoint(),QPoint(0,120*count),Qt.NoButton,Qt.ControlModifier,Qt.NoScrollPhase,False));settled();assert abs(displayed()['pts']-target)<1e-6
  capture('video scrub and Ctrl wheel');(out/'scrub.json').write_text(json.dumps(observed,indent=2),encoding='utf8');checks.append('Qt video scrub changes pixels during drag and Ctrl wheel retains exact adjacent source-frame stepping')
  def save_reopen(name):
   saved=capture('before '+name);key=uuid.uuid4().hex;path=out/(name+'.json');request('save',path=str(path),save_id=key)
   wait(lambda:any(s['id']==key and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves']))
   request('load',path=str(path));e.refresh(True);e.reveal()
   if any(r['type']=='Video' for r in e.config['layers']):
    wait(lambda:not shell.client.snapshot['media_library']['pending']);request('media_transport',media_session=e.binding[0],layer=video_id,op='seek',value=2.5)
    wait(lambda:displayed() and displayed()['pts']==2.5)
   reopened=capture('reopen '+name);assert reopened['gui']['layers']==saved['gui']['layers'];assert reopened['pixels']==saved['pixels']
  save_reopen('mixed-hierarchy-save');checks.append('Durable mixed image/video/painted/blank hierarchy Save As and exact accepted pixel reopen')
  # Full Qt platform drag lifecycle, not direct drop callback. Cancellation is
  # bounded; acceptance is mandatory when this probe is selected.
  if os.environ.get('ZERAWAVE_QT_FULL_DRAG')=='1':
   for collapsed in (False,True):
    (e.collapsed.add if collapsed else e.collapsed.discard)(root2);e.populate();e.select(b);pump();source=e.row_items[b];target=e.row_items[root2];p=e.tree.visualItemRect(target).center();start=e.tree.visualItemRect(source).center()
    before=capture('before full Qt drag');calls=[];original=e.tree.dropEvent
    def drop(event):calls.append(dict(source=event.source() is e.tree,placement=e.tree.drop_intent(event.position().toPoint())));return original(event)
    e.tree.dropEvent=drop
    QTest.mousePress(e.tree.viewport(),Qt.LeftButton,Qt.NoModifier,start)
    QTimer.singleShot(60,lambda:QTest.mouseMove(e.tree.viewport(),p));QTimer.singleShot(150,lambda:QTest.mouseRelease(e.tree.viewport(),Qt.LeftButton,Qt.NoModifier,p));QTimer.singleShot(800,QDrag.cancel)
    motion=start+QPoint(24,0);app.sendEvent(e.tree.viewport(),QMouseEvent(QEvent.MouseMove,QPointF(motion),QPointF(e.tree.viewport().mapToGlobal(motion)),Qt.NoButton,Qt.LeftButton,Qt.NoModifier));pump(1.)
    e.tree.dropEvent=original;after=capture('full Qt drag');drag_probe.append(dict(calls=calls,collapsed=collapsed,platform=app.platformName(),accepted=lookup(e.config)[b]['parent']==root2))
    assert calls and lookup(e.config)[b]['parent']==root2,drag_probe
    internal_drop([b],root,'above')
   checks.append('Complete production Qt QDrag enter/move/drop/return and asynchronous owner reconciliation')
  # Heal invalid cached items left by an earlier failed Qt move, same revision.
  old=e.row_items[b];delete_qt(old);e.refresh();capture('invalid cache recovered at same revision');checks.append('Deleted C++ row cache heals without another document edit')
  # Actual delete-confirmation policy, intercepted only in disposable test.
  for repetition in range(3):
   before=capture('before delete all');e.tree.selectAll()
   with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):assert e.delete()
   empty=capture('delete all');assert not empty['owner']['layers'] and not empty['tree']
   created=global_blank();fresh=capture('add after empty');assert len(fresh['owner']['layers'])==1 and lookup(e.config)[created]['parent'] is None
   e.history(False,'layers');capture('undo fresh');e.history(False,'layers');idle()
   if video_id in lookup(e.config):
    request('media_transport',media_session=e.binding[0],layer=video_id,op='seek',value=2.5);wait(lambda:getattr(e,'media_presented',{}).get(video_id,{}).get('pts')==2.5)
   restored=capture('undo deletion');assert restored['gui']['layers']==before['gui']['layers'] and restored['pixels']==before['pixels']
   e.history(True,'layers');capture('redo deletion');e.history(True,'layers');capture('redo fresh')
  checks.append('Delete-all then global add repeated three times; exact creation/deletion Undo/Redo and usable empty scene')
  save_reopen('saved')
  native_drag=os.environ.get('ZERAWAVE_NATIVE_DRAG_SAVE')
  if native_drag:
   request('load',path=native_drag);e.refresh(True);reopened=capture('Windows drag save reopen');assert len(reopened['owner']['layers'])==3 and not any(r['parent'] for r in reopened['owner']['layers'])
  checks.append('Revision-pinned durable Save As and reopen retain IDs/hierarchy/renderable exact accepted pixels')
  result='PASS'
 except Exception:failure=traceback.format_exc();print(failure)
 finally:
  print('cleanup',flush=True);e.timer.stop();shell.timer.stop();e.reader.close();e.web_sources.close();e.pool.shutdown(wait=True)
  shell.client.gui_thread=None;shell.client.close(mode='discard');shell.closing=True;shell.close();pump();faulthandler.cancel_dump_traceback_later();diagnostic.close()
  report=dict(result=result,checks=checks,failure=failure,errors=errors,drag_probe=drag_probe,owner_exit=shell.client.process.poll(),platform=app.platformName(),limits='Qt-dispatched synthetic input/CPU canvas; separate Windows Computer Use trace; not Robert physical acceptance')
  (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report));assert result=='PASS',failure
if __name__=='__main__':run(sys.argv[1])
