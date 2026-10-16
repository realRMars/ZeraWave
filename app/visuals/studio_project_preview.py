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
  super().__init__(parent);self.preview=parent;self.surface=None;self.pending=None;self.pending_binding=None;self.draft_painted=False;self.setMinimumHeight(220);fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile);fmt.setSamples(0);self.setFormat(fmt)
 def initializeGL(self):
  try:
   import moderngl
   self.surface=ProjectSurface(moderngl.create_context(require=330));self.context().aboutToBeDestroyed.connect(self.release)
  except Exception as exc:self.preview.status.setText('Project GPU unavailable; switching to Qt reference: '+str(exc));QTimer.singleShot(0,lambda:self.preview.fallback(self))
 def consume(self,result):self.pending=result;self.pending_binding=tuple(self.preview.requested);self.update()
 def paintGL(self):
  if not self.surface:return
  context=self.surface.context;target=self.surface.host.target_for(self.defaultFramebufferObject(),(round(self.width()*self.devicePixelRatioF()),round(self.height()*self.devicePixelRatioF())))
  if self.pending:
   result=self.pending;binding=self.pending_binding;self.pending=None;self.pending_binding=None
   if not self.preview.valid_result(result,binding):
    self.preview.discarded(result,binding);target.clear(.035,.05,.06,1.);return
   try:self.surface.render(result,target);self.draft_painted=False;self.preview.rendered(result,self.surface.stats)
   except Exception as exc:self.preview.failed(result,exc)
  elif self.preview.valid_presented() and self.surface.texture:
   if self.preview.transform_preview or self.draft_painted:
    try:self.surface.recompose(self.preview.transform_preview,target);self.draft_painted=bool(self.preview.transform_preview)
    except Exception as exc:self.preview.status.setText('Unaccepted transform preview unavailable: '+str(exc));self.surface.present(target)
   else:self.surface.host.draw(None,self.surface.size,None,target)
  else:target.clear(.035,.05,.06,1.)
 def release(self):
  if self.pending:self.preview.media.release(self.pending['serial']);self.pending=None;self.pending_binding=None
  if self.surface:
   self.makeCurrent()
   try:self.surface.close();self.surface=None
   finally:self.doneCurrent()
  # Reparenting/fullscreen can recreate this context. Old pixels cannot certify
  # a new empty framebuffer; demand the same authoritative frame again.
  if self.preview.view is self:self.preview.serial=None;self.preview.requested=None;self.preview.presented=None
 def clear_project(self):
  if self.pending:self.preview.media.release(self.pending['serial']);self.pending=None;self.pending_binding=None
  if self.surface:
   context=self.surface.context;self.makeCurrent()
   try:self.surface.close();self.surface=ProjectSurface(context)
   finally:self.doneCurrent()
  self.update()

class ProjectPreview(QWidget):
 def __init__(self,workspace):
  super().__init__();self.workspace=workspace;self.media=Media();self.evaluator=None;self.version=None;self.wanted=None;self.requested=None;self.serial=None;self.presented=None;self.render_samples=[];self.seek_samples=[];self.closed=False;self.transform_preview=None;self.handles=None
  layout=QVBoxLayout(self);self.layout_=layout;self.view=(CPUView if os.environ.get('QT_QPA_PLATFORM')=='offscreen' or os.environ.get('ZERAWAVE_EDITOR_GPU')=='cpu' else GPUView)(self);layout.addWidget(self.view,1);self.status=QLabel('Timeline preview • native source resolution');self.status.setWordWrap(True);layout.addWidget(self.status);self.overlay=QLabel(self);self.overlay.setAlignment(Qt.AlignCenter);self.overlay.setWordWrap(True);self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents);self.overlay.setStyleSheet('QLabel { color:#d7e1e7; background:transparent; padding:12px; }');self.timer=QTimer(self);self.timer.setInterval(16);self.timer.timeout.connect(self.poll_safe);self.timer.start();self.failed_binding=None;self.host_window=self.window()
  if hasattr(workspace,'timeline'):
   from studio_project_handles import TransformHandles
   self.handles=TransformHandles(self)
 def draw_transform_preview(self):
  if isinstance(self.view,CPUView) and self.valid_presented():
   try:self.view.surface.recompose(self.transform_preview)
   except Exception as exc:self.status.setText('Unaccepted transform preview unavailable: '+str(exc))
  self.view.update()
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
  # Legacy binding name: rendered content available to Qt, not scanout evidence.
  state=self.workspace.state();transport=self.workspace.transport_state();return self.presented is not None and self.wanted is not None and self.presented[:3]==self.wanted[:3] and self.presented[:3]==(state.get('epoch'),state.get('revision'),transport.get('generation',0))
 def poll_safe(self):
  try:self.poll()
  except Exception as exc:self.status.setText('Preview preparation failed: '+str(exc)+'. Accepted project retained.');self.failed_binding=self.wanted[:3] if self.wanted else None
  finally:self.refresh_notice()
 def refresh_notice(self):
  self.overlay.setGeometry(self.view.geometry());document=self.workspace.state().get('document')
  if not document or self.evaluator and self.evaluator.end==0:text='Add a clip to the timeline.'
  elif self.failed_binding:text='Preview unavailable — accepted project retained.\n'+self.status.text()[:180]
  elif not self.valid_presented():text='Preparing preview…'
  else:text=''
  self.overlay.setText(text);self.overlay.setVisible(bool(text));self.overlay.raise_();
  if self.handles:self.handles.refresh()
  self.setToolTip(self.status.text()+'\n'+self.status.toolTip())
 def fallback(self,origin=None):
  if origin is not None and origin is not self.view:return
  prior=self.view;prior.release();replacement=CPUView(self);self.layout_.replaceWidget(prior,replacement);self.view=replacement;prior.hide();prior.deleteLater();replacement.show();self.requested=None;self.serial=None
 def rendered(self,result,stats):
  self.media.release(result['serial']);self.presented=self.requested;self.serial=None;self.render_samples.append(dict(stats));self.render_samples=self.render_samples[-512:];self.seek_samples.append(dict(frame=result['plan']['frame'],decode_ms=(result['ready']-result['requested'])*1000,render_complete_ms=(time.perf_counter()-result['requested'])*1000,measurement='render callback completion; excludes Qt composition, capture and physical display'));self.seek_samples=self.seek_samples[-512:];self.status.setText(f"Frame {result['plan']['frame']} • revision {result['plan']['revision']} • "+('Qt CPU reference' if isinstance(self.view,CPUView) else 'existing GPU compositor'))
  fonts=[str(d.get('font_requested'))+' → '+d.get('font_resolved','') for d in stats.get('text_details',[]) if d.get('font_fallback')];self.status.setToolTip(('Primary font substitution: '+'; '.join(fonts)+'. ' if fonts else '')+'Qt per-glyph fallback is not enumerated; verify displayed glyphs on this system.')
  self.prepare_next_playing_frame()
 def prepare_next_playing_frame(self):
  # Once the renderer owns the uploaded pixels, its source lease is released.
  # Start the next latest-clock preparation now, overlapping Qt composition;
  # never allocate a second reader lease or queue obsolete playback samples.
  if self.closed or self.serial is not None or self.evaluator is None:return
  state=self.workspace.state();clock=self.workspace.transport_state();version=(state.get('epoch'),state.get('revision'))
  if not clock.get('playing') or version!=self.version:return
  wanted=(*version,clock.get('generation',0),min(self.evaluator.end,clock.get('frame',0)))
  if self.presented is None or wanted[:3]!=self.presented[:3] or wanted==self.requested:return
  self.wanted=wanted;self.requested=wanted;self.serial=self.media.submit(self.evaluator.at(wanted[-1]))
 def failed(self,result,exc):
  self.media.release(result['serial']);self.serial=None;self.presented=None;self.failed_binding=self.wanted[:3] if self.wanted else None;self.status.setText('Requested preview failed: '+str(exc)+'. Accepted project retained. Seek again after resolving the source/resource error.')
 def rehost(self):
  """Retire only the GL host resources when a native top level changes."""
  window=self.window()
  if window is self.host_window:return
  self.host_window=window;prior=self.view
  if not isinstance(prior,GPUView) or prior.surface is None:return
  prior.release();replacement=GPUView(self);self.layout_.replaceWidget(prior,replacement);self.view=replacement;prior.hide();prior.deleteLater();replacement.show();self.requested=self.serial=self.presented=None
 def poll(self):
  if self.closed:return
  self.rehost()
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
  self.closed=True;self.timer.stop()
  if self.handles:self.handles.close_resources()
  self.view.release();self.media.close()
 def exited(self):return self.media.exited()
