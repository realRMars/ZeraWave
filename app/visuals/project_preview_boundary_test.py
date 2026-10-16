"""Actual media/Qt-widget/GL callbacks with controlled interleavings, no scanout claim."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import os,sys,time,json,uuid,hashlib,traceback
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QWidget,QLabel
from PySide6.QtCore import Qt,QPoint,QEvent
from PySide6.QtGui import QImage,QColor
from PySide6.QtTest import QTest
from video_project import create,apply
from project_evaluator import Evaluator
from project_surface import ProjectSurface
from studio_project_preview import ProjectPreview,GPUView
from studio_timeline import Timeline
from media_registry import decode_image
import glfw,moderngl,numpy as np
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);checks=[];rows=[];window=None;ctx=None;surface=None;preview=None
source_binding={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app/visuals').glob('*.py')};(out/'SOURCE.json').write_text(json.dumps(source_binding,indent=2),'utf8')
class Workspace:
 def __init__(self,d):self.current=dict(document=d,epoch='old',revision=1);self.transport=dict(frame=0,generation=1,playing=False);self.notice=QLabel();self.trees={};self.pending=None;self.timeline=SimpleNamespace(decorations=None,cancel_placement=lambda:None);self.shell=SimpleNamespace(statusBar=lambda:SimpleNamespace(showMessage=lambda text:None))
 def state(self):return self.current
 def transport_state(self):return self.transport
 def binding(self):return dict(expected_epoch=self.current['epoch'],expected_revision=self.current['revision'])
def demand(document,epoch,revision):
 serial=preview.media.submit(Evaluator(document,epoch,revision).at(0));end=time.monotonic()+10
 while not preview.media.ready():assert time.monotonic()<end;time.sleep(.002)
 result=preview.media.take();assert result and not result['error'];binding=(epoch,revision,workspace.transport['generation'],0);preview.requested=preview.wanted=binding;preview.presented=None;preview.serial=serial;view.consume(result);return result,binding
def center():
 target=surface.host.target_for(view.defaultFramebufferObject(),(64,64));data=np.frombuffer(target.read(components=4,alignment=1),np.uint8).reshape(target.size[1],target.size[0],4);return data[target.size[1]//2,target.size[0]//2].tolist()
try:
 assets=[]
 for name,color in [('red','#ff0000'),('blue','#0000ff')]:
  path=out/(name+'.png');image=QImage(64,64,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(color));assert image.save(str(path));metadata,_=decode_image(str(path));assets.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=metadata))
 a,t,c=[uuid.uuid4().hex for _ in range(3)];document=apply(create(settings=dict(width=64,height=64)),[dict(op='media.add',id=a,name='Fixture',kind='Image',location=dict(kind='external',path=assets[0]['path']),sha256=assets[0]['sha256'],metadata=assets[0]['metadata']),dict(op='track.add',id=t,kind='video'),dict(op='clip.add',id=c,asset=a,track=t,start=10,duration=20)],uuid.uuid4().hex)[0]
 # Minimal Qt reproduction: each cancellation releases only this widget's grab.
 workspace=Workspace(document);timeline=Timeline(workspace);timeline.set_document(document,('old',1));timeline.show();app.processEvents()
 def press():
  rect=timeline.rects[('clips',c)];pos=QPoint(round(rect.center().x()),round(rect.center().y()));QTest.mousePress(timeline,Qt.LeftButton,pos=pos);assert timeline.gesture and QWidget.mouseGrabber() is timeline;return pos
 for case in ('revision','escape','hide','deactivate','replacement','close'):
  timeline.show();timeline.set_document(document,(workspace.current['epoch'],workspace.current['revision']));app.processEvents();pos=press();before=deepcopy(document)
  if case=='revision':workspace.current['revision']+=1;timeline.set_document(document,('old',workspace.current['revision']))
  elif case=='escape':QTest.keyClick(timeline,Qt.Key_Escape)
  elif case=='hide':timeline.hide()
  elif case=='deactivate':app.sendEvent(timeline,QEvent(QEvent.WindowDeactivate))
  elif case=='replacement':workspace.current['epoch']='replacement';timeline.set_document(document,('replacement',workspace.current['revision']))
  else:timeline.close()
  assert timeline.gesture is None and QWidget.mouseGrabber() is not timeline;QTest.mouseRelease(timeline,Qt.LeftButton,pos=pos);assert document==before and QWidget.mouseGrabber() is not timeline;rows.append(dict(cancel=case,immediate_capture_released=True,no_edit=True))
 timeline.show();app.processEvents();pos=press();QTest.keyClick(timeline,Qt.Key_Escape);other=QWidget();other.show();other.grabMouse();timeline.cancel_gesture();assert QWidget.mouseGrabber() is other;other.releaseMouse();other.close();timeline.close();workspace.current.update(epoch='destroy',revision=9);dying=Timeline(workspace);dying.set_document(document,('destroy',9));dying.show();app.processEvents();rect=dying.rects[('clips',c)];QTest.mousePress(dying,Qt.LeftButton,pos=QPoint(round(rect.center().x()),round(rect.center().y())));assert QWidget.mouseGrabber() is dying;dying.deleteLater();app.sendPostedEvents(dying,QEvent.DeferredDelete);assert QWidget.mouseGrabber() is None;checks.append('Actual Qt widget revision/Escape/hide/deactivate/replacement/close/destruction cancellation releases own capture immediately; repeated subsequent presses and other-widget grab preserved')
 # Native GL consumption with actual codec owner and snapshot leases.
 document['clips'][0]['start']=0;workspace=Workspace(document);preview=ProjectPreview(workspace);preview.timer.stop();preview.view.release();view=GPUView(preview);view.setMinimumSize(0,0);view.resize(64,64);preview.view=view
 assert glfw.init();glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3);glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3);glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE);glfw.window_hint(glfw.VISIBLE,False);window=glfw.create_window(64,64,'ZeraWave B pending-frame correction',None,None);assert window;glfw.make_context_current(window);ctx=moderngl.create_context(require=330);surface=ProjectSurface(ctx);view.surface=surface
 release=preview.media.release;releases=[]
 def counted(serial):releases.append(serial);release(serial)
 preview.media.release=counted
 for case in ('revision','replacement','project_id','close','seek','newer_status','same_frame_new_generation'):
  workspace.current=dict(document=document,epoch='old',revision=1);workspace.transport=dict(frame=0,generation=1,playing=False);result,binding=demand(document,'old',1);count=len(preview.render_samples);calls=len(releases)
  newer=None
  if case=='revision':workspace.current['revision']=2
  elif case=='replacement':workspace.current['epoch']='new-project'
  elif case=='project_id':workspace.current['document']=deepcopy(document);workspace.current['document']['id']=uuid.uuid4().hex
  elif case=='close':workspace.current=dict(document=None,epoch='closed-project',revision=0)
  else:workspace.transport['generation']=2
  if case in ('newer_status','same_frame_new_generation'):
   newer=('old',1,2,0);preview.requested=preview.wanted=newer;preview.status.setText('Newer request is preparing')
  view.paintGL();assert len(preview.render_samples)==count and preview.presented is None and preview.media.leased is None and len(releases)==calls+1 and releases[-1]==result['serial'];assert center()!=[255,0,0,255]
  if newer:
   assert preview.requested==newer and preview.status.text()=='Newer request is preparing'
   preview.version=('old',1);preview.evaluator=Evaluator(document,'old',1);preview.poll();assert preview.serial is not None and preview.serial>result['serial']
   end=time.monotonic()+10
   while view.pending is None:assert time.monotonic()<end;preview.poll();time.sleep(.002)
   view.paintGL();assert preview.presented==newer and preview.valid_presented() and preview.media.leased is None
  rows.append(dict(interleaving=case,stale_render_callbacks=0,release_count=1,center=center(),newer_preserved=bool(newer)))
  # A correct new demand in the same Media instance recovers and presents blue.
  current=deepcopy(document);current['media'][0].update(location=dict(kind='external',path=assets[1]['path']),sha256=assets[1]['sha256'],metadata=assets[1]['metadata']);workspace.current=dict(document=current,epoch='current',revision=3);workspace.transport=dict(frame=0,generation=3,playing=False);result,binding=demand(current,'current',3);view.paintGL();assert center()==[0,0,255,255] and preview.valid_presented() and preview.presented==binding and preview.media.leased is None
 checks.append('Pending actual GPU callback rejects revision/replacement/close/paused-seek/same-frame-new-generation before draw; own immutable binding pinned, reader released once, newer status retained, same-worker/current blue recovery')
 # Retained redraw is also guarded against an incoming seek before preview poll.
 workspace.transport['generation']=4;assert not preview.valid_presented();view.paintGL();assert center()!=[0,0,255,255];checks.append('Retained CPU/GPU presentation validity checks live seek generation before deferred redraw')
 workspace.transport['generation']=5;result,binding=demand(current,'current',3);original=surface.render
 def fail(*args):raise MemoryError('Controlled GPU resource refusal')
 surface.render=fail;view.paintGL();assert preview.media.leased is None and preview.presented is None and 'Controlled GPU resource refusal' in preview.status.text();surface.render=original;workspace.transport['generation']=6;result,binding=demand(current,'current',3);view.paintGL();assert center()==[0,0,255,255] and preview.valid_presented();checks.append('Actual consumption exception releases reader and reports original failure; deliberate newer seek recovers same media/compositor')
 # Same-generation playback may hold the preceding frame while a latest demand
 # prepares; this is bounded lag, not an obsolete seek. Preserve that display.
 workspace.transport=dict(frame=5,generation=6,playing=True);preview.version=('current',3);preview.evaluator=Evaluator(current,'current',3);held=preview.presented;preview.poll();assert preview.presented==held and preview.valid_presented() and preview.serial is not None
 end=time.monotonic()+10
 while view.pending is None:assert time.monotonic()<end;preview.poll();time.sleep(.002)
 view.paintGL();assert preview.presented[-1]==5 and preview.valid_presented();checks.append('Bounded same-generation playback retains valid preceding presentation while latest frame5 prepares; seek-generation invalidation remains separate')
 # Cleanup while pending returns that last reader once and retires resources.
 workspace.transport['generation']=7;result,binding=demand(current,'current',3);calls=len(releases);host_dimensions=dict(glfw_framebuffer=list(glfw.get_framebuffer_size(window)),qt_widget=[view.width(),view.height()],detected_target=list(surface.host.target_for(view.defaultFramebufferObject(),(view.width(),view.height())).size),native_project=[64,64]);view.release();assert view.pending is None and view.pending_binding is None and preview.media.leased is None and len(releases)==calls+1;preview.media.close();preview.media.thread.join(5);assert preview.media.exited() and preview.media.metrics['rgba_bytes']==0;assert surface.stats['closed'] and view.surface is None;checks.append('Actual media worker and renderer/compositor cleanup complete; no readers/native RGBA/textures retained')
 assert all(hashlib.sha256((root/r).read_bytes()).hexdigest()==h for r,h in source_binding.items())
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,rows=rows,gpu=ctx.info['GL_RENDERER'],classification=__doc__,host_dimensions=host_dimensions,release_serials=releases),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if preview:
  if preview.media.leased:preview.media.release(preview.media.leased['serial'])
  preview.media.close();preview.media.thread.join(5)
 if surface:surface.close();view.surface=None
 if ctx:ctx.release()
 if window:glfw.destroy_window(window)
 glfw.terminate()
