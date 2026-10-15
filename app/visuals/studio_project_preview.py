"""Qt project preview: immutable plans, latest seeks and explicit reader release."""
import os,time
from PySide6.QtCore import Qt,QTimer,QRectF
from PySide6.QtGui import QPainter,QColor,QSurfaceFormat
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from project_evaluator import Evaluator
from project_media import Media
from project_surface import ProjectSurface,ReferenceSurface

class CPUView(QWidget):
 def __init__(self,parent):super().__init__(parent);self.preview=parent;self.surface=ReferenceSurface();self.setMinimumHeight(200)
 def paintEvent(self,e):
  p=QPainter(self);p.fillRect(self.rect(),QColor('#101920'));image=self.surface.image
  if image and self.preview.valid_presented():
   scale=min(self.width()/image.width(),self.height()/image.height());w,h=image.width()*scale,image.height()*scale;p.drawImage(QRectF((self.width()-w)/2,(self.height()-h)/2,w,h),image)
  p.end()
 def consume(self,result):self.surface.render(result);self.update()
 def clear_project(self):self.surface.close();self.surface=ReferenceSurface();self.update()
 def release(self):self.surface.close()

class GPUView(QOpenGLWidget):
 def __init__(self,parent):
  super().__init__(parent);self.preview=parent;self.surface=None;self.pending=None;self.pending_binding=None;self.setMinimumHeight(220);fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile);fmt.setSamples(0);self.setFormat(fmt)
 def initializeGL(self):
  try:
   import moderngl
   self.surface=ProjectSurface(moderngl.create_context(require=330));self.context().aboutToBeDestroyed.connect(self.release)
  except Exception as exc:self.preview.status.setText('Project GPU unavailable; switching to Qt reference: '+str(exc));QTimer.singleShot(0,self.preview.fallback)
 def consume(self,result):self.pending=result;self.pending_binding=tuple(self.preview.requested);self.update()
 def paintGL(self):
  if not self.surface:return
  context=self.surface.context;target=self.surface.host.target_for(self.defaultFramebufferObject(),(round(self.width()*self.devicePixelRatioF()),round(self.height()*self.devicePixelRatioF())))
  if self.pending:
   result=self.pending;binding=self.pending_binding;self.pending=None;self.pending_binding=None
   if not self.preview.valid_result(result,binding):
    self.preview.discarded(result,binding);target.clear(.035,.05,.06,1.);return
   try:self.surface.render(result,target);self.preview.rendered(result,self.surface.stats)
   except Exception as exc:self.preview.failed(result,exc)
  elif self.preview.valid_presented() and self.surface.texture:self.surface.host.draw(None,self.surface.size,None,target)
  else:target.clear(.035,.05,.06,1.)
 def release(self):
  if self.pending:self.preview.media.release(self.pending['serial']);self.pending=None;self.pending_binding=None
  if self.surface:
   self.makeCurrent()
   try:self.surface.close();self.surface=None
   finally:self.doneCurrent()
 def clear_project(self):
  if self.pending:self.preview.media.release(self.pending['serial']);self.pending=None;self.pending_binding=None
  if self.surface:
   context=self.surface.context;self.makeCurrent()
   try:self.surface.close();self.surface=ProjectSurface(context)
   finally:self.doneCurrent()
  self.update()

class ProjectPreview(QWidget):
 def __init__(self,workspace):
  super().__init__();self.workspace=workspace;self.media=Media();self.evaluator=None;self.version=None;self.wanted=None;self.requested=None;self.serial=None;self.presented=None;self.render_samples=[];self.seek_samples=[];self.closed=False
  layout=QVBoxLayout(self);self.layout_=layout;self.view=(CPUView if os.environ.get('QT_QPA_PLATFORM')=='offscreen' or os.environ.get('ZERAWAVE_EDITOR_GPU')=='cpu' else GPUView)(self);layout.addWidget(self.view,1);self.status=QLabel('Timeline preview • native source resolution');self.status.setWordWrap(True);layout.addWidget(self.status);self.timer=QTimer(self);self.timer.setInterval(16);self.timer.timeout.connect(self.poll_safe);self.timer.start();self.failed_binding=None
 def valid_result(self,result,binding):
  state=self.workspace.state();transport=self.workspace.transport_state();plan=result['plan'];request=binding;document=state.get('document')
  return bool(document) and plan['project']==document['id'] and request is not None and request==self.requested and request[:3]==(state.get('epoch'),state.get('revision'),transport.get('generation',0)) and (plan['epoch'],plan['revision'],plan['frame'])==(request[0],request[1],request[3])
 def discarded(self,result,binding):
  self.media.release(result['serial'])
  if self.serial==result['serial']:self.serial=None
  if self.presented==binding:self.presented=None
  # A newer intent/status may already be installed although its preparation
  # has not started. Retirement cannot clear or falsely fail that request.
  if self.requested==binding:
   self.presented=None;self.requested=None
   self.status.setText('No video project open.' if not self.workspace.state().get('document') else 'Obsolete prepared frame retired; current request will prepare.')
 def valid_presented(self):
  state=self.workspace.state();transport=self.workspace.transport_state();return self.presented is not None and self.wanted is not None and self.presented[:3]==self.wanted[:3] and self.presented[:3]==(state.get('epoch'),state.get('revision'),transport.get('generation',0))
 def poll_safe(self):
  try:self.poll()
  except Exception as exc:self.status.setText('Preview preparation failed: '+str(exc)+'. Accepted project retained.');self.failed_binding=self.wanted[:3] if self.wanted else None
 def fallback(self):
  prior=self.view;prior.release();replacement=CPUView(self);self.layout_.replaceWidget(prior,replacement);self.view=replacement;prior.hide();prior.deleteLater();replacement.show();self.requested=None;self.serial=None
 def rendered(self,result,stats):
  self.media.release(result['serial']);self.presented=self.requested;self.serial=None;self.render_samples.append(dict(stats));self.render_samples=self.render_samples[-512:];self.seek_samples.append(dict(frame=result['plan']['frame'],decode_ms=(result['ready']-result['requested'])*1000,present_ms=(time.perf_counter()-result['requested'])*1000));self.seek_samples=self.seek_samples[-512:];self.status.setText(f"Frame {result['plan']['frame']} • revision {result['plan']['revision']} • "+('Qt CPU reference' if isinstance(self.view,CPUView) else 'existing GPU compositor'))
  fonts=[str(d.get('font_requested'))+' → '+d.get('font_resolved','') for d in stats.get('text_details',[]) if d.get('font_fallback')];self.status.setToolTip(('Primary font substitution: '+'; '.join(fonts)+'. ' if fonts else '')+'Qt per-glyph fallback is not enumerated; verify displayed glyphs on this system.')
 def failed(self,result,exc):
  self.media.release(result['serial']);self.serial=None;self.presented=None;self.failed_binding=self.wanted[:3] if self.wanted else None;self.status.setText('Requested preview failed: '+str(exc)+'. Accepted project retained. Seek again after resolving the source/resource error.')
 def poll(self):
  if self.closed:return
  state=self.workspace.state();document=state.get('document');transport=self.workspace.transport_state();version=(state.get('epoch'),state.get('revision'))
  if version!=self.version:
   previous=self.evaluator;self.version=version;self.evaluator=Evaluator(document,*version) if document else None;self.failed_binding=None
   if self.evaluator:self.requested=None
   elif previous:
    self.view.clear_project();self.media.submit(dict(visual=[]));self.requested=self.wanted=self.presented=None;self.serial=None;self.status.setText('No video project open.')
  if not self.evaluator:
   if self.requested is not None:
    if isinstance(self.view,GPUView) and self.view.pending:self.media.release(self.view.pending['serial']);self.view.pending=None;self.view.pending_binding=None
    self.media.submit(dict(visual=[]));self.requested=self.wanted=self.presented=None;self.serial=None;self.view.update();self.status.setText('No video project open.')
   return
  frame=min(self.evaluator.end,transport.get('frame',0));wanted=(*version,transport.get('generation',0),frame);self.wanted=wanted
  if self.failed_binding==wanted[:3]:return
  replace=self.requested is None or wanted[:3]!=self.requested[:3] or not transport.get('playing') and wanted!=self.requested or self.serial is None and not self.valid_presented()
  if replace:
   if isinstance(self.view,GPUView) and self.view.pending:self.media.release(self.view.pending['serial']);self.view.pending=None;self.view.pending_binding=None
   self.requested=wanted;self.presented=None;self.serial=self.media.submit(self.evaluator.at(frame));self.view.update();self.status.setText(f'Preparing requested frame {frame}…')
  result=self.media.ready()
  if result and result['serial']==self.serial:
   result=self.media.take()
   if result['error']:self.failed(result,result['error'])
   elif isinstance(self.view,CPUView):
    try:self.view.consume(result);self.rendered(result,self.view.surface.stats)
    except Exception as exc:self.failed(result,exc)
   else:self.view.consume(result)
   result=None # release unused CPU callback references before next preparation
  # During playback preserve one in-flight preparation, then request the latest
  # clock frame. Report observed lag; never accumulate an obsolete frame queue.
  if transport.get('playing') and self.serial is None and wanted!=self.requested:
   self.requested=wanted;self.serial=self.media.submit(self.evaluator.at(frame))
 def close_resources(self):
  if self.closed:return
  self.closed=True;self.timer.stop();self.view.release();self.media.close()
 def exited(self):return self.media.exited()
