"""Studio's scoped video document controls, all submitted to its existing owner.

No editable mirror or transport waits live in Qt. A dialog captures a revision;
intervening API/manual edits reject it explicitly rather than overwriting them.
"""
from pathlib import Path
import time,uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
 QTreeWidget,QTreeWidgetItem,QTabWidget,QFileDialog,QDialog,QFormLayout,
 QDialogButtonBox,QLineEdit,QPlainTextEdit,QComboBox,QSpinBox,QDoubleSpinBox,
 QCheckBox,QMessageBox,QApplication,QTableWidget,QTableWidgetItem)
from video_project import duration

TERMINAL=('accepted','durable','exported','rejected','failed')
class ProjectWorkspace(QWidget):
 def __init__(self,shell):
  super().__init__();self.shell=shell;self.client=shell.client;self.pending=None;self.version=None;self.last_save=None;self.callback_samples=[];self.export_id=None
  layout=QVBoxLayout(self);layout.setContentsMargins(8,8,8,8)
  row=QHBoxLayout();layout.addLayout(row);self.controls=[]
  for title,fn in [('New video',self.new),('Open video…',self.open),('Save project',self.save),('Save As…',lambda:self.save(True)),('Close project',self.close_project)]:self.button(row,title,fn)
  self.button(row,'Export Video…',self.export_video)
  self.button(row,'Project settings…',self.project_settings)
  self.export_notice=QLabel();layout.addWidget(self.export_notice);self.export_cancel=QPushButton('Cancel video export');layout.addWidget(self.export_cancel);self.export_cancel.clicked.connect(lambda:self.shell.safe(self.cancel_export))
  self.heading=QLabel();self.heading.setWordWrap(True);layout.addWidget(self.heading)
  from studio_timeline import TimelinePanel
  from studio_project_preview import ProjectPreview
  from PySide6.QtWidgets import QSplitter
  self.timeline=TimelinePanel(self);self.preview=ProjectPreview(self);splitter=QSplitter(Qt.Vertical);splitter.addWidget(self.preview);splitter.addWidget(self.timeline);layout.addWidget(splitter,2)
  self.transport_future=None;self.transport_desired=None
  self.tabs=QTabWidget();layout.addWidget(self.tabs,1);self.trees={};self.pages={}
  for key,title,columns in [('media','Project bin',['Source','Type','Availability','Location']),('tracks','Tracks',['Track','Type','Order','Gain','Mute']),('clips','Clips',['Clip','Track','Start frame','Frames','Source seconds','Gain']),('captions','Captions',['Text','Start frame','Frames']),('graphics','Titles / graphics',['Text / kind','Start frame','Frames'])]:
   page=QWidget();body=QVBoxLayout(page);tree=QTreeWidget();tree.setHeaderLabels(columns);tree.setSelectionMode(QTreeWidget.SingleSelection);body.addWidget(tree,1);buttons=QHBoxLayout();body.addLayout(buttons);self.trees[key]=tree;self.pages[key]=(page,buttons);self.tabs.addTab(page,title)
  for title,fn in [('Import…',self.import_media),('Relink selected…',self.relink),('Place selected…',self.place)]:self.button(self.pages['media'][1],title,fn)
  for title,fn in [('Add track…',self.add_track),('Volume…',lambda:self.audio_edit('tracks'))]:self.button(self.pages['tracks'][1],title,fn)
  for title,fn in [('Move…',self.move),('Trim…',self.trim),('Split…',self.split),('Layout…',self.spatial_edit),('Volume…',lambda:self.audio_edit('clips')),('Unlink',self.unlink),('Remove',self.remove)]:self.button(self.pages['clips'][1],title,fn)
  for title,fn in [('Add caption…',lambda:self.caption(False)),('Edit caption…',lambda:self.caption(True)),('Remove',self.remove_caption)]:self.button(self.pages['captions'][1],title,fn)
  self.button(self.pages['captions'][1],'Import SRT…',self.import_captions)
  self.button(self.pages['captions'][1],'Style / placement…',lambda:self.text_style('captions'))
  for title,fn in [('Add title / graphic…',lambda:self.caption(False,'graphics')),('Edit…',lambda:self.caption(True,'graphics')),('Style / placement…',lambda:self.text_style('graphics')),('Remove',lambda:self.remove_text('graphics'))]:self.button(self.pages['graphics'][1],title,fn)
  self.trees['graphics'].itemDoubleClicked.connect(lambda *_:self.caption(True,'graphics'))
  self.trees['captions'].itemDoubleClicked.connect(lambda *_:self.caption(True));self.trees['clips'].itemDoubleClicked.connect(lambda *_:self.trim())
  row=QHBoxLayout();layout.addLayout(row);self.undo=self.button(row,'Undo',lambda:self.submit('undo'));self.redo=self.button(row,'Redo',lambda:self.submit('redo'))
  self.cancel_button=QPushButton('Cancel pending preparation');row.addWidget(self.cancel_button);self.cancel_button.clicked.connect(lambda:self.shell.safe(self.cancel))
  endpoint=QPushButton('Copy agent endpoint');row.addWidget(endpoint);endpoint.clicked.connect(lambda:QApplication.clipboard().setText(self.state().get('endpoint','')))
  self.notice=QLabel('Create or open a video project. Layer sessions remain in Composition.');self.notice.setWordWrap(True);layout.addWidget(self.notice);self.refresh()
 def button(self,row,title,fn):
  b=QPushButton(title);b.setAccessibleName(title);b.clicked.connect(lambda checked=False:self.shell.safe(fn));row.addWidget(b);self.controls.append(b);return b
 def state(self):return self.client.snapshot.get('project',{})
 def transport_state(self):
  s=self.state();clock=getattr(self.client,'project_clock',None)
  return clock if clock and (clock.get('epoch'),clock.get('revision'))==(s.get('epoch'),s.get('revision')) else s.get('transport',{})
 def transport(self,action,frame=None):
  self.transport_desired=dict(action=action,**({'frame':frame} if frame is not None else {}));self.poll_transport()
 def poll_transport(self):
  if self.transport_future:
   if not self.transport_future.done():return
   try:
    result=self.transport_future.result()
    if not result.get('ok'):raise ValueError(result.get('error',{}).get('message','Timeline transport failed.'))
   except Exception as exc:self.transport_desired=None;self.notice.setText(str(exc)+' Reconcile this operation; do not duplicate an uncertain command.')
   self.transport_future=None
  if self.transport_desired and not self.pending:
   values=self.transport_desired;self.transport_desired=None
   self.transport_future=self.client.submit('project',request=dict(op='transport',operation_id=uuid.uuid4().hex,**self.binding(),**values))
 def close_resources(self):self.timeline.canvas.cancel_gesture();self.preview.close_resources()
 def exited(self):return self.preview.exited()
 def binding(self,state=None):
  s=self.state() if state is None else state;return dict(expected_epoch=s.get('epoch'),expected_revision=s.get('revision'),expected_project=s.get('project_id'),expected_command=s.get('command_revision'))
 def document(self):
  d=self.state().get('document')
  if d is None:raise ValueError('Create or open a video project first.')
  return d
 def selected(self,key):
  item=self.trees[key].currentItem()
  if item is None:raise ValueError('Select a '+key.rstrip('s')+' first.')
  identity=item.data(0,Qt.UserRole);return next(r for r in self.document()[key] if r['id']==identity)
 def submit(self,op,binding=None,**args):
  if self.pending:raise ValueError('This project operation is still reconciling. Wait for its outcome before another edit.')
  began=time.perf_counter();key=uuid.uuid4().hex;request=dict(op=op,operation_id=key,**(binding or self.binding()),**args)
  future=self.client.submit('project',request=request);self.pending=dict(id=key,request=request,future=future,started=began,uncertain=False)
  self.callback_samples.append(dict(op=op,ms=(time.perf_counter()-began)*1000));self.callback_samples=self.callback_samples[-256:]
  self.notice.setText('Submitted '+op+'. Acceptance and saving are reported separately.');self.refresh();return key
 def batch(self,label,changes,binding=None):return self.submit('batch',binding=binding,label=label,changes=changes)
 def cancel(self):
  if self.pending:self.client.submit('project',request=dict(op='cancel',operation_id=self.pending['id']))
 def poll_pending(self):
  p=self.pending
  if not p:return
  outcome=p.get('resolved') or next((o for o in self.state().get('operations',[]) if o['id']==p['id']),None)
  if outcome and outcome['op']=='export' and outcome['status']=='exporting':
   self.export_id=p['id'];self.pending=None;self.notice.setText('Exporting frozen revision '+str(outcome['requested_revision'])+'. Later edits remain separate.');return
  if outcome and outcome['status'] in TERMINAL:
   self.pending=None;self.last_outcome=outcome
   if outcome['status'] in ('failed','rejected'):self.unapplied_request=p['request']
   if outcome['status'] in ('failed','rejected'):self.notice.setText(outcome.get('error',{}).get('message','Operation failed')+' Existing accepted work retained.')
   elif outcome['status']=='exported':self.notice.setText('Video revision '+str(outcome['revision'])+' exported durably. '+str(outcome['result']['path']))
   elif outcome['status']=='durable':self.notice.setText('Project revision '+str(outcome['revision'])+' saved durably. '+str(outcome['result']['path']))
   else:self.notice.setText('Accepted project revision '+str(outcome['revision'])+'. Save project to preserve it.')
   self.shell.statusBar().showMessage(self.notice.text());return
  if p['future'].done() and not p.get('ack_checked'):
   p['ack_checked']=True
   try:
    result=p['future'].result()
    if result.get('outcome') and result['outcome']['status'] in TERMINAL:p['resolved']=result['outcome'];self.poll_pending();return
   except Exception as exc:
    p['uncertain']=True;self.notice.setText(str(exc)+' Operation outcome is uncertain; retained ID '+p['id']+'. Reconcile that ID; never repeat with a new ID.');self.shell.statusBar().showMessage(self.notice.text())
  if not outcome and p.get('ack_checked') and not self.client.disconnected:
   status=p.get('status_future')
   if status and status.done():
    try:
     result=status.result()
     if result.get('outcome') and result['outcome']['status'] in TERMINAL:p['resolved']=result['outcome'];self.poll_pending();return
    except Exception:p['uncertain']=True
    p['status_future']=None;p['status_at']=time.perf_counter()
   elif not status and time.perf_counter()-p.get('status_at',0)>.5:
    try:p['status_future']=self.client.submit('project',request=dict(op='operation_status',operation_id=p['id']))
    except ValueError:p['status_at']=time.perf_counter()
  if time.perf_counter()-p['started']>15 and not outcome:self.notice.setText('Still reconciling '+p['id']+'. Keep Studio open; accepted work has not been discarded.')
 def refresh(self):
  self.poll_pending();self.poll_transport();self.timeline.refresh();s=self.state();d=s.get('document');busy=bool(self.pending or any(o['status']=='preparing' for o in s.get('operations',[])))
  exporting=next((o for o in s.get('operations',[]) if o['id']==self.export_id),None)
  active_export=any(o['status']=='exporting' for o in s.get('operations',[]))
  if exporting:
   progress=exporting.get('progress',{});detail=str(progress.get('frame',0))+'/'+str(progress.get('frames','?'))+' frames'
   self.export_notice.setText(('Exporting revision '+str(exporting['requested_revision'])+': '+progress.get('phase','starting')+'; '+detail) if exporting['status']=='exporting' else ('Video revision '+str(exporting.get('revision',exporting['requested_revision']))+' exported: '+exporting['result']['path']) if exporting['status']=='exported' else exporting.get('error',{}).get('message','Export ended')+(' Accepted project retained; inspect destination before repeating.' if exporting.get('error',{}).get('code')=='export_outcome_unknown' else ' Accepted work and prior good output retained.'))
  self.export_cancel.setEnabled(active_export and bool(self.export_id))
  saving=any(o['status'] in ('saving','exporting') for o in s.get('operations',[]))
  for i,b in enumerate(self.controls):b.setEnabled(not busy and not self.client.disconnected and (d is not None or i<2) and not (saving and i in (0,1,4)))
  self.undo.setEnabled(not busy and bool(s.get('undo_label')));self.undo.setText('Undo '+s.get('undo_label',''))
  self.redo.setEnabled(not busy and bool(s.get('redo_label')));self.redo.setText('Redo '+s.get('redo_label',''))
  self.cancel_button.setEnabled(bool(self.pending));self.heading.setText((d['name']+' • revision '+str(s['revision'])+' • '+str(duration(d))+' frames • '+('unsaved' if s['dirty'] else 'saved')) if d else 'No video project open')
  rows_version=(s.get('epoch'),s.get('revision'),tuple((k,v.get('status')) for k,v in s.get('media',{}).items()))
  if self.version==rows_version:return
  self.version=rows_version;tracks={r['id']:r for r in d['tracks']} if d else {}
  for key,tree in self.trees.items():
   current=tree.currentItem();selection=current.data(0,Qt.UserRole) if current else None;tree.clear()
   for r in d[key] if d else []:
    if key=='media':fields=[r['name'],r['kind'],s.get('media',{}).get(r['id'],{}).get('status','Not checked'),r['location']['path']]
    elif key=='tracks':fields=[r['name'],r['kind'],str(r['order']),str(r['audio']['gain']),str(r['audio']['mute'])]
    elif key=='clips':fields=[r['name'],tracks[r['track']]['name'],str(r['start']),str(r['duration']),str(r['source_in']),str(r['audio']['gain'])]
    else:fields=[r['text'],str(r['start']),str(r['duration'])]
    item=QTreeWidgetItem(tree,fields);item.setData(0,Qt.UserRole,r['id']);item.setToolTip(0,r['id'])
    if r['id']==selection:tree.setCurrentItem(item)
   if tree.topLevelItemCount() and not tree.currentItem():tree.setCurrentItem(tree.topLevelItem(0))
 def dialog(self,title,fields):
  prior=getattr(self,'dialog_owner',None)
  if prior:prior.deleteLater()
  dialog=QDialog(self);dialog.setWindowTitle(title);layout=QFormLayout(dialog)
  # Keep the dialog (and its fields) alive until the caller reads accepted
  # values. Retire that hidden widget at the next dialog or workspace close.
  self.dialog_owner=dialog
  for name,widget in fields:widget.setAccessibleName(name);layout.addRow(name,widget)
  buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addRow(buttons)
  return dialog.exec()==QDialog.Accepted
 def spin(self,value,minimum=0):s=QSpinBox();s.setRange(minimum,120*24*3600);s.setValue(value);return s
 def choose_tracks(self,kind=None):
  box=QComboBox()
  for r in sorted(self.document()['tracks'],key=lambda r:r['order']):
   if kind is None or r['kind']==kind:box.addItem(r['name'],r['id'])
  if not box.count():raise ValueError('Add a compatible '+(kind or '')+' track first.')
  return box
 def replace_allowed(self):
  if not self.state().get('dirty'):return True,False
  answer=QMessageBox.question(self,'Unsaved video project','Accepted project changes are unsaved. Save project before replacing it, or explicitly discard this project?',QMessageBox.Discard|QMessageBox.Cancel)
  return answer==QMessageBox.Discard,answer==QMessageBox.Discard
 def new(self):
  ok,discard=self.replace_allowed()
  if not ok:return
  binding=self.binding();name=QLineEdit('Untitled video')
  if self.dialog('New video project',[('Name',name)]):self.submit('new',binding=binding,name=name.text(),discard=discard);self.show_workspace()
 def open(self,path=None):
  ok,discard=self.replace_allowed()
  if not ok:return
  binding=self.binding()
  if not path:path,_=QFileDialog.getOpenFileName(self,'Open video project',str(Path.home()),'ZeraWave video project (*.zwv)')
  if path:self.submit('open',binding=binding,path=path,discard=discard);self.show_workspace()
 def show_workspace(self):self.shell.panels['project'].toggleView(True);self.shell.panels['project'].setAsCurrentTab()
 def save(self,save_as=False,path=None):
  self.document();binding=self.binding();s=self.state()
  missing=any(r['status']=='Missing' for r in s.get('media',{}).values());allow_missing=False
  if missing:
   allow_missing=QMessageBox.question(self,'Missing project media','Save editable reference metadata while these sources are missing? Their content remains unresolved. Relink before playback/export can use it.',QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes
   if not allow_missing:return
  if not path:path=s.get('path') if not save_as else None
  if not path:path,_=QFileDialog.getSaveFileName(self,'Save video project with managed media',str(Path.home()/'video.zwv'),'ZeraWave video project (*.zwv)')
  if path:self.last_save=self.submit('save',binding=binding,path=path,portable=True,allow_missing=allow_missing);return self.last_save
 def project_settings(self):
  d=self.document();binding=self.binding();values=d['settings'];width=QSpinBox();width.setRange(16,8192);width.setValue(values['width']);height=QSpinBox();height.setRange(16,8192);height.setValue(values['height']);numerator=QSpinBox();numerator.setRange(1,1000000);numerator.setValue(values['fps'][0]);denominator=QSpinBox();denominator.setRange(1,1000000);denominator.setValue(values['fps'][1])
  note=QLabel('Native output pixels. Frame counts stay fixed; changing FPS changes timeline duration and source sampling. Invalid source ranges reject the entire change.')
  if self.dialog('Video project settings',[('Width',width),('Height',height),('FPS numerator',numerator),('FPS denominator',denominator),('Timing',note)]):
   changes=dict(width=width.value(),height=height.value(),fps=[numerator.value(),denominator.value()])
   self.batch('Video project settings',[dict(op='project.settings',values=changes)],binding)
 def cancel_export(self):
  if self.export_id:self.client.submit('project',request=dict(op='cancel',operation_id=self.export_id))
 def export_video(self,path=None,crf=None):
  d=self.document();binding=self.binding();settings=d['settings'];quality=QSpinBox();quality.setRange(0,51);quality.setValue(d['export']['crf'])
  if crf is None:
   details=QLabel(str(settings['width'])+'×'+str(settings['height'])+' at '+str(settings['fps'][0])+'/'+str(settings['fps'][1])+' FPS;48kHz stereo. Native project settings; lower CRF gives higher quality.')
   if not self.dialog('Export Video — frozen project revision',[('Output',details),('H264 CRF',quality)]):return
   crf=quality.value()
  if not path:path,_=QFileDialog.getSaveFileName(self,'Export Video MP4',str(Path.home()/'video.mp4'),'MP4 H264/AAC (*.mp4)')
  if path:return self.submit('export',binding=binding,path=path,crf=crf)
 def close_project(self):
  ok,discard=self.replace_allowed()
  if ok:self.submit('close',discard=discard)
 def import_media(self):
  self.document();binding=self.binding();kind=QComboBox();kind.addItems(['Video','Audio','Image'])
  if not self.dialog('Import source type',[('Type',kind)]):return
  path,_=QFileDialog.getOpenFileName(self,'Import '+kind.currentText(),str(Path.home()),'Media files (*.*)')
  if path:self.batch('Import '+Path(path).name,[dict(op='media.add',name=Path(path).name,kind=kind.currentText(),location=dict(kind='external',path=str(Path(path).resolve())))],binding)
 def relink(self):
  r=self.selected('media');binding=self.binding();path,_=QFileDialog.getOpenFileName(self,'Relink '+r['name'],str(Path(r['location']['path']).parent),'Media files (*.*)')
  if not path:return
  changed=QMessageBox.question(self,'Replacement identity','Accept a different source identity if its content changed? Choose No to require the exact recorded file.',QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes
  self.batch('Relink '+r['name'],[dict(op='media.relink',id=r['id'],kind=r['kind'],location=dict(kind='external',path=str(Path(path).resolve())),sha256=r['sha256'],accept_changed=changed)],binding)
 def add_track(self):
  self.document();binding=self.binding();name=QLineEdit('Track');kind=QComboBox();kind.addItems(['video','audio','graphics'])
  if self.dialog('Add track',[('Name',name),('Kind',kind)]):self.batch('Add '+name.text(),[dict(op='track.add',name=name.text(),kind=kind.currentText())],binding)
 def place(self):
  r=self.selected('media');binding=self.binding();track=self.choose_tracks();start=self.spin(0);length=self.spin(30,1)
  if self.dialog('Place '+r['name'],[('Track',track),('Start frame',start),('Duration frames',length)]):self.batch('Place '+r['name'],[dict(op='clip.add',name=r['name'],asset=r['id'],track=track.currentData(),start=start.value(),duration=length.value())],binding)
 def move(self):
  r=self.selected('clips');binding=self.binding();start=self.spin(r['start'])
  if self.dialog('Move linked clip',[('New start frame',start)]):self.batch('Move '+r['name'],[dict(op='clip.move',id=r['id'],start=start.value())],binding)
 def trim(self):
  r=self.selected('clips');binding=self.binding();start=self.spin(r['start']);end=self.spin(r['start']+r['duration'],1)
  if self.dialog('Trim linked clip',[('Start frame',start),('End frame (exclusive)',end)]):self.batch('Trim '+r['name'],[dict(op='clip.trim',id=r['id'],start=start.value(),end=end.value())],binding)
 def split(self):
  r=self.selected('clips');binding=self.binding();at=self.spin(r['start']+r['duration']//2)
  if self.dialog('Split linked clip',[('Split frame',at)]):self.batch('Split '+r['name'],[dict(op='clip.split',id=r['id'],at=at.value())],binding)
 def remove(self):
  r=self.selected('clips');self.batch('Remove '+r['name'],[dict(op='clip.remove',id=r['id'])])
 def unlink(self):
  r=self.selected('clips');self.batch('Unlink '+r['name'],[dict(op='clip.unlink',id=r['id'])])
 def spatial_edit(self):
  r=self.selected('clips');binding=self.binding();layout=r['layout'];fields=[];boxes={}
  for i,label in enumerate(('Left fraction','Top fraction','Width fraction','Height fraction')):
   box=QDoubleSpinBox();box.setRange(-4 if i<2 else .00001,4 if i<2 else 8);box.setDecimals(5);box.setValue(layout['bounds'][i]);boxes[label]=box;fields.append((label,box))
  fit=QComboBox();fit.addItems(['Stretch','Fit','Fill']);fit.setCurrentText(layout['fit']);fields.append(('Fit',fit))
  for name,low,high in [('opacity',0,1),('brightness',0,4),('rotation',-36000,36000)]:
   box=QDoubleSpinBox();box.setRange(low,high);box.setDecimals(4);box.setValue(layout[name]);boxes[name]=box;fields.append((name.title(),box))
  blend=QComboBox();blend.addItems(['Normal','Multiply','Screen','Add','Difference']);blend.setCurrentText(layout['blend']);fields.append(('Blend',blend))
  if self.dialog('Spatial layout '+r['name'],fields):self.batch('Layout '+r['name'],[dict(op='clip.layout',id=r['id'],values=dict(bounds=[boxes[label].value() for label in ('Left fraction','Top fraction','Width fraction','Height fraction')],fit=fit.currentText(),blend=blend.currentText(),**{name:boxes[name].value() for name in ('opacity','brightness','rotation')}))],binding)
 def audio_edit(self,key):
  r=self.selected(key);binding=self.binding();gain=QDoubleSpinBox();gain.setRange(0,4);gain.setDecimals(4);gain.setValue(r['audio']['gain']);initial_gain=gain.value();mute=QCheckBox();mute.setChecked(r['audio']['mute']);fade_in=self.spin(r['audio']['fade_in']);fade_out=self.spin(r['audio']['fade_out'])
  panel=QWidget();layout=QVBoxLayout(panel);table=QTableWidget(len(r['audio']['envelope']),2);table.setHorizontalHeaderLabels(['Project frame' if key=='tracks' else 'Local frame','Linear gain']);table.setAccessibleName('Volume envelope');table.setMinimumSize(390,150);layout.addWidget(table);buttons=QHBoxLayout();layout.addLayout(buttons)
  for i,point in enumerate(r['audio']['envelope']):
   for j,value in enumerate(point):table.setItem(i,j,QTableWidgetItem(str(value)))
  def add():
   row=table.rowCount()
   if row>=2048:raise ValueError('At most2048 envelope points are supported.')
   frame=int(table.item(row-1,0).text())+1 if row else 0;table.insertRow(row);table.setItem(row,0,QTableWidgetItem(str(frame)));table.setItem(row,1,QTableWidgetItem('1'));table.setCurrentCell(row,1)
  plus=QPushButton('Add point');plus.clicked.connect(lambda:self.shell.safe(add));buttons.addWidget(plus);remove=QPushButton('Remove point');remove.clicked.connect(lambda:table.removeRow(table.currentRow()) if table.currentRow()>=0 else None);buttons.addWidget(remove)
  fields=[('Linear gain (1 = unity)',gain),('Mute',mute),('Fade in frames',fade_in),('Fade out frames',fade_out),('Envelope (project frames)' if key=='tracks' else 'Envelope (local frames)',panel)]
  if self.dialog('Volume '+r['name'],fields):
   values={}
   if gain.value()!=initial_gain:values['gain']=gain.value()
   if mute.isChecked()!=r['audio']['mute']:values['mute']=mute.isChecked()
   for name,widget in [('fade_in',fade_in),('fade_out',fade_out)]:
    if widget.value()!=r['audio'][name]:values[name]=widget.value()
   try:points=[[int(table.item(i,0).text()),float(table.item(i,1).text())] for i in range(table.rowCount())]
   except (ValueError,AttributeError):raise ValueError('Envelope points need integer local frames and numeric linear gains.')
   if points!=r['audio']['envelope']:values['envelope']=points
   if values:self.batch('Volume '+r['name'],[dict(op='track.audio' if key=='tracks' else 'clip.audio',id=r['id'],values=values)],binding)
 def caption(self,editing,category='captions'):
  binding=self.binding();r=self.selected(category) if editing else dict(text='',start=0,duration=60,style={},dynamic=None,order=0);track=None if editing else self.choose_tracks('graphics');content=QPlainTextEdit(r['text']);content.setMinimumSize(420,130);start=self.spin(r['start']);length=self.spin(r['duration'],1);fields=[('Text' if category=='captions' else 'Text / counter template',content),('Start frame',start),('Duration frames',length)]
  if track:fields.insert(0,('Graphics track',track))
  mode=QComboBox();mode.addItems(['Static text','counter','progress']);mode.setCurrentIndex(0 if not r.get('dynamic') else 1 if r['dynamic']=='counter' else 2);order=self.spin(r.get('order',0));begin=self.spin(r.get('range_start',r['start']));end=self.spin(r.get('range_end',r['start']+r['duration']),1)
  if category=='graphics':fields.extend([('Kind',mode),('Within-track stacking order',order),('Counter/progress range start',begin),('Range end (exclusive)',end)])
  if not self.dialog(('Edit ' if editing else 'Add ')+('caption' if category=='captions' else 'title / timed graphic'),fields):return
  values=dict(text=content.toPlainText(),start=start.value(),duration=length.value())
  if category=='graphics':
   values.update(dynamic=[None,'counter','progress'][mode.currentIndex()],order=order.value())
   if values['dynamic']:values.update(range_start=begin.value(),range_end=end.value())
  change=dict(op='caption.edit' if category=='captions' else 'graphic.edit',id=r['id'],values=values) if editing else dict(op='caption.add' if category=='captions' else 'graphic.add',track=track.currentData(),**values)
  self.batch(('Correct caption' if editing else 'Add caption') if category=='captions' else ('Correct title / graphic' if editing else 'Add title / graphic'),[change],binding)
 def text_style(self,category):
  r=self.selected(category);binding=self.binding();style=r['style'];font=QLineEdit(style['font']);color=QLineEdit(style['color']);background=QLineEdit(style['background']);bold=QCheckBox();bold.setChecked(style['bold']);align=QComboBox();align.addItems(['left','center','right']);align.setCurrentText(style['align']);valign=QComboBox();valign.addItems(['top','center','bottom']);valign.setCurrentText(style.get('valign','center'));fields=[('Font family',font),('Text RGB / ARGB',color),('Background RGB / ARGB',background),('Bold',bold),('Alignment',align),('Vertical alignment',valign)];boxes={};initial={}
  for name,low,high,default in [('size',6,256,27),('padding',0,256,10),('radius',0,256,9),('opacity',0,1,1),('stroke_width',0,16,0),('padding_x',0,256,style['padding']),('padding_y',0,256,style['padding']),('line_spacing',0,512,0)]:
   box=QDoubleSpinBox();box.setRange(low,high);box.setDecimals(3);box.setValue(style.get(name,default));boxes[name]=box;initial[name]=box.value();fields.append((name.replace('_',' ').title(),box))
  for index,label in enumerate(('Left fraction','Top fraction','Width fraction','Height fraction')):
   box=QDoubleSpinBox();box.setRange(-4 if index<2 else .00001,4 if index<2 else 8);box.setDecimals(5);box.setValue(style['bounds'][index]);boxes[label]=box;initial[label]=box.value();fields.append((label,box))
  stroke_color=QLineEdit(style.get('stroke_color','#30221b'));lines=self.spin(style.get('max_lines',0));fields.extend([('Stroke RGB / ARGB',stroke_color),('Maximum lines (0 = bounds only)',lines)])
  if not self.dialog('Readable text style / placement',fields):return
  values={}
  for name,widget in [('font',font),('color',color),('background',background),('stroke_color',stroke_color)]:
   if widget.text()!=style.get(name,'#30221b' if name=='stroke_color' else ''):values[name]=widget.text()
  for name,value,default in [('bold',bold.isChecked(),True),('align',align.currentText(),'center'),('valign',valign.currentText(),'center'),('max_lines',lines.value(),0)]:
   if value!=style.get(name,default):values[name]=value
  for name in ('size','padding','radius','opacity','stroke_width','padding_x','padding_y','line_spacing'):
   if boxes[name].value()!=initial[name]:values[name]=boxes[name].value()
  names=('Left fraction','Top fraction','Width fraction','Height fraction');bounds=[boxes[name].value() if boxes[name].value()!=initial[name] else style['bounds'][i] for i,name in enumerate(names)]
  if bounds!=style['bounds']:values['bounds']=bounds
  if values:self.batch('Style '+category,[dict(op='caption.edit' if category=='captions' else 'graphic.edit',id=r['id'],values={'style':values})],binding)
 def import_captions(self):
  self.document();binding=self.binding();track=self.choose_tracks('graphics')
  if not self.dialog('Import SRT captions',[('Graphics track',track)]):return
  path,_=QFileDialog.getOpenFileName(self,'Import editable SRT captions',str(Path.home()),'UTF-8 SubRip captions (*.srt)')
  if path:self.submit('import_captions',binding=binding,path=path,track=track.currentData(),label='Import SRT '+Path(path).name)
 def remove_text(self,category):
  r=self.selected(category);self.batch('Remove '+category,[dict(op='caption.remove' if category=='captions' else 'graphic.remove',id=r['id'])])
 def remove_caption(self):self.remove_text('captions')
