"""Source inspection UI over the existing owner's read-only Source context."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from types import SimpleNamespace
import threading
from PySide6.QtCore import Qt,QTimer,QEvent
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QSlider,QSpinBox,QComboBox,QPushButton,QDoubleSpinBox

class SourcePanel(QWidget):
 def __init__(self,workspace):
  super().__init__();self.workspace=workspace;self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Source inspection');self.future=None;self.cancel=threading.Event();self.next_source=None;self.prepared_asset=None;self.asset=None;self.preview=None;self.retiring=[];self.closed=False;self.serial=0;self.frame=0;self.range=[0,1];self.version=None;self.request_id=None;self.end=1;self.fps=[30,1]
  self.range_intent=None;self.retained_range=None;self.seek_intent=None
  layout=QVBoxLayout(self);layout.setContentsMargins(4,4,4,4);layout.setSpacing(3);self.heading=QLabel('Double-click media to preview.');self.heading.setWordWrap(True);layout.addWidget(self.heading);self.metadata=QLabel();layout.addWidget(self.metadata);self.host=QVBoxLayout();layout.addLayout(self.host,1)
  self.seek=QSlider(Qt.Horizontal);self.seek.setAccessibleName('Source frame');self.seek.setMinimumHeight(24);self.seek.valueChanged.connect(lambda frame:workspace.shell.safe(lambda:self.seek_to(frame)));layout.addWidget(self.seek);row=QHBoxLayout();layout.addLayout(row);self.in_box=QSpinBox();self.out_box=QSpinBox()
  self.seek.sliderPressed.connect(lambda:setattr(self,'seek_intent',(self.version,self.workspace.binding())));self.seek.sliderReleased.connect(lambda:setattr(self,'seek_intent',None))
  for text,box in [('In',self.in_box),('Out',self.out_box)]:
   box.setAccessibleName('Source '+text+(' exclusive' if text=='Out' else ''));box.setRange(0,1);box.setKeyboardTracking(False);row.addWidget(QLabel(text));row.addWidget(box,1);box.editingFinished.connect(lambda:workspace.shell.safe(self.mark_range));box.installEventFilter(self);box.valueChanged.connect(lambda _:self.range_edited());box.lineEdit().textEdited.connect(lambda _:self.range_edited())
  self.range_retry=QPushButton('Apply retained range to current Source');self.range_retry.clicked.connect(lambda:workspace.shell.safe(self.retry_range));self.range_retry.hide();layout.addWidget(self.range_retry)
  self.still_row=QWidget();line=QHBoxLayout(self.still_row);line.setContentsMargins(0,0,0,0);line.addWidget(QLabel('Still seconds'));self.still_seconds=QDoubleSpinBox();self.still_seconds.setRange(.001,86400);self.still_seconds.setDecimals(3);self.still_seconds.setValue(5.);self.still_seconds.setKeyboardTracking(False);self.still_seconds.setAccessibleName('Still placement duration seconds');self.still_seconds.setToolTip('New still placements only; maps down to whole sequence frames, minimum one. Existing clips stay unchanged.');line.addWidget(self.still_seconds);layout.addWidget(self.still_row);self.still_row.hide()
  row=QHBoxLayout();layout.addLayout(row);self.channels=workspace.timeline.source_mode;self.channels.setParent(self);row.addWidget(self.channels,1);self.channels.show();button=QPushButton('Place');button.setToolTip('Place the current Source In/Out using the Timeline mode');button.clicked.connect(lambda:workspace.shell.safe(self.place));row.addWidget(button)
  self.info=QLabel();self.info.setWordWrap(True);layout.addWidget(self.info);self.timer=QTimer(self);self.timer.setInterval(30);self.timer.timeout.connect(lambda:workspace.shell.safe(self.poll));self.timer.start();self.setMinimumSize(180,220);self.setFocusPolicy(Qt.StrongFocus)
  self.still_seconds.valueChanged.connect(lambda *_:self.still_note())
 def still_note(self):
  if self.asset and self.asset['kind']=='Image':
   from fractions import Fraction
   fps=Fraction(*(self.workspace.state().get('document') or {}).get('settings',{}).get('fps',[30,1]));frames=max(1,int(Fraction(str(self.still_seconds.value()))*fps));self.info.setText('New still placement: '+str(frames)+' sequence frames. Existing clips stay unchanged.')
 def load(self,asset):
  self.cancel.set();self.next_source=deepcopy(asset);self.prepared_asset=None;self.heading.setText('Preparing Source…');self.poll()
 def clock(self):return self.workspace.source_transport_state()
 def poll(self):
  self.retiring=[p for p in self.retiring if not self.retire_finished(p)]
  if self.closed:return
  if self.future and self.future.done():
   future=self.future;self.future=None
   try:
    asset=future.result()
    if not self.cancel.is_set():self.prepared_asset=asset
   except InterruptedError:pass
   except Exception as exc:self.info.setText('Source unavailable: '+str(exc))
  if self.next_source and self.future is None:
   from studio_video_workspace import inspect_source
   asset=self.next_source;self.next_source=None;self.cancel=threading.Event();self.future=self.pool.submit(inspect_source,asset,self.cancel)
  if self.prepared_asset and not self.workspace.pending:
   asset=self.prepared_asset;self.prepared_asset=None;self.request_id=self.workspace.submit('source_open',asset=asset)
  state=self.workspace.state().get('source',{});document=state.get('document');version=(state.get('epoch'),state.get('revision'))
  if not document and self.asset:
   self.retire_preview();self.asset=None;self.version=None;self.heading.setText('Double-click media to preview.');self.metadata.clear();self.info.clear();self.still_row.hide()
  if document and version!=self.version:
   self.version=version;self.install(state)
  if self.request_id and not self.workspace.pending:
   outcome=getattr(self.workspace,'last_outcome',{})
   if outcome.get('id')==self.request_id:
    self.request_id=None
    if outcome.get('status')!='accepted':self.info.setText('Source not opened: '+str(outcome.get('error',{}).get('message','Outcome unknown; inspect status before retry.')))
  if self.asset:
   clock=self.clock();self.frame=clock.get('frame',self.frame);self.range=[clock.get('range_in',0),clock.get('range_out',self.end)]
   for box,value in [(self.seek,min(self.frame,self.end-1)),(self.in_box,self.range[0]),(self.out_box,self.range[1])]:
    if not box.hasFocus():box.blockSignals(True);box.setValue(value);box.blockSignals(False)
 def retire_finished(self,p):
  if not p.exited():return False
  p.deleteLater();return True
 def retire_preview(self):
  if self.preview:
   p=self.preview;self.preview=None;p.close_resources();self.host.removeWidget(p);p.hide();self.retiring.append(p)
 def install(self,state):
  self.version=(state['epoch'],state['revision'])
  self.retire_preview();document=state['document'];self.asset=deepcopy(document['media'][0]);self.serial+=1;clock=self.clock();self.end=clock.get('end',1);self.fps=document['settings']['fps'];self.frame=clock.get('frame',0);self.range=[clock.get('range_in',0),clock.get('range_out',self.end)];self.heading.setText('SOURCE • '+self.asset['name']);self.metadata.setText(self.asset['kind']+' • '+str(self.end)+' frames');self.metadata.setToolTip(self.asset['location']['path'])
  self.still_row.setVisible(self.asset['kind']=='Image')
  for box,low,high in [(self.seek,0,max(0,self.end-1)),(self.in_box,0,max(0,self.end-1)),(self.out_box,1,self.end)]:box.blockSignals(True);box.setRange(low,high);box.blockSignals(False)
  self.derived_state=dict(document=document,revision=state['revision'],epoch=state['epoch'])
  if self.asset['kind']=='Audio':self.info.setText('Audio source ready. Choose Source in the shared monitor transport to audition.');return
  if not self.isVisible():return
  from studio_project_preview import ProjectPreview
  self.preview=ProjectPreview(SimpleNamespace(state=lambda:self.derived_state,transport_state=self.clock));self.preview.view.setMinimumHeight(80);self.preview.status.hide();self.host.addWidget(self.preview);self.preview.show();self.info.setText('Out is exclusive; sequence playhead is independent.')
  self.still_note()
 def seek_to(self,frame):
  if self.asset and not self.closed:
   version,binding=self.seek_intent or (self.version,self.workspace.binding());source=self.workspace.state().get('source',{});current=self.workspace.binding()
   if version!=(source.get('epoch'),source.get('revision')) or any(binding.get(k)!=current.get(k) for k in ('expected_project','expected_epoch','expected_revision')):self.info.setText('Source seek '+str(frame)+' not accepted after a context change. Release and seek again deliberately.');return
   self.workspace.transport('seek_paused',frame,target='source',source_epoch=version[0],binding=binding)
 def mark_range(self):
  if not self.asset or self.closed:return
  if self.retained_range is not None:self.info.setText('Range '+str(self.retained_range)+' remains rejected/retained. Edit a value or use explicit Apply to current Source.');return
  values=[self.in_box.value(),self.out_box.value()]
  if values==self.range:self.range_intent=None;return
  self.pin_range();intent=self.range_intent;current=self.workspace.state().get('source',{});binding=self.workspace.binding()
  if intent['version']!=(current.get('epoch'),current.get('revision')) or any(intent['binding'].get(k)!=binding.get(k) for k in ('expected_project','expected_epoch','expected_revision')):
   self.retained_range=values;self.range_intent=None;self.range_retry.show();self.info.setText('Source changed; range '+str(values)+' not accepted. Retained for deliberate Apply to current Source; no automatic submission.');return
  if values[0]>=values[1]:self.info.setText('In must precede exclusive Out. Previous range retained.');return
  self.workspace.transport('range',values,target='source',source_epoch=intent['version'][0],binding=intent['binding']);self.range_intent=None;self.retained_range=None;self.range_retry.hide()
 def pin_range(self):
  if self.range_intent is None and self.asset:self.range_intent=dict(version=self.version,binding=self.workspace.binding())
 def range_edited(self):
  # editingFinished can fire on both Enter and a later blur. Focus, panel
  # refresh and that second signal cannot rebind a rejected gesture.
  if self.retained_range is not None:self.retained_range=None;self.range_intent=None;self.range_retry.hide()
  self.pin_range()
 def eventFilter(self,obj,event):
  if obj in (self.in_box,self.out_box) and event.type() in (QEvent.FocusIn,QEvent.MouseButtonPress):self.pin_range()
  return super().eventFilter(obj,event)
 def retry_range(self):
  if not self.retained_range:return
  values=list(self.retained_range);state=self.workspace.state().get('source',{});clock=self.clock()
  if self.version!=(state.get('epoch'),state.get('revision')):self.info.setText('Current Source is still updating; retained range remains unapplied.');return
  if not 0<=values[0]<values[1]<=clock.get('end',0):self.info.setText('Retained range exceeds current Source. Re-enter a valid range; nothing accepted.');return
  self.workspace.transport('range',values,target='source',source_epoch=state['epoch'],binding=self.workspace.binding());self.retained_range=None;self.range_intent=None;self.range_retry.hide()
 def place(self):
  if not self.asset:raise ValueError('Load a Source first.')
  from PySide6.QtCore import QMimeData
  import json
  mime=QMimeData();d=self.workspace.document();known=next((a for a in d['media'] if a['id']==self.asset['id']),None)
  if known:mime.setData('application/x-zerawave-project-media',json.dumps([known['id']]).encode())
  else:mime.setData('application/x-zerawave-assets',json.dumps([self.asset['id']]).encode())
  self.workspace.timeline.place_mime(mime,self.workspace.timeline.canvas.current_track,self.workspace.transport_state().get('frame',0))
 def hideEvent(self,event):
  self.cancel.set();self.next_source=self.prepared_asset=None;self.retire_preview()
  if not self.closed:
   if self.request_id:self.workspace.shell.safe(lambda:self.workspace.client.submit('project',request=dict(op='cancel',operation_id=self.request_id)))
   if self.asset:self.workspace.shell.safe(lambda:self.workspace.transport('release',target='source'))
  super().hideEvent(event)
 def showEvent(self,event):
  super().showEvent(event)
  state=self.workspace.state().get('source',{})
  if state.get('document') and self.preview is None:self.install(state)
 def close_resources(self):
  self.closed=True;self.timer.stop();self.cancel.set();self.next_source=self.prepared_asset=None;self.retire_preview();self.pool.shutdown(wait=False,cancel_futures=True)
 def exited(self):return (self.future is None or self.future.done()) and all(p.exited() for p in self.retiring) and (not self.closed or all(not t.is_alive() for t in self.pool._threads))
