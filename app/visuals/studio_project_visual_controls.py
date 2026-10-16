"""Inline bounded effects, visual keys, transitions and clip envelopes."""
from copy import deepcopy
from PySide6.QtCore import Qt,QTimer,QRectF,QObject,QEvent
from PySide6.QtGui import QPainter,QColor
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,
 QListWidget,QListWidgetItem,QDoubleSpinBox,QSpinBox,QCheckBox,QTableWidget,QTableWidgetItem,QAbstractItemView,QHeaderView)
from project_visual import EFFECTS,parameter,read_parameter,evaluated_layout,text_layout

def layout_for(row):return row['layout'] if 'layout' in row else text_layout(row)
def evaluated_for(row,frame):return evaluated_layout(dict(row,layout=layout_for(row)),frame)

class IntentFilter(QObject):
 def __init__(self,parent,callback,widgets):
  super().__init__(parent);self.callback=callback
  for widget in widgets:
   widget.installEventFilter(self)
   if hasattr(widget,'lineEdit') and widget.lineEdit():widget.lineEdit().installEventFilter(self)
 def eventFilter(self,obj,event):
  if event.type() in (QEvent.MouseButtonPress,QEvent.Wheel,QEvent.KeyPress):self.callback()
  return False

def compact_table(table):
 table.setMinimumWidth(120);table.horizontalHeader().setMinimumSectionSize(24);table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

class KeyRuler(QWidget):
 def __init__(self,controls):super().__init__();self.controls=controls;self.setMinimumHeight(40);self.setAccessibleName('Visual keyframe ruler; click selects exact local frame')
 def paintEvent(self,event):
  c=self.controls;p=QPainter(self);p.fillRect(self.rect(),QColor('#101b22'));p.setPen(QColor('#607d88'));p.drawLine(8,25,self.width()-8,25);end=max(1,c.key_end)
  for point in c.points():p.setBrush(QColor('#e9b670'));p.drawEllipse(QRectF(5+point[0]/end*(self.width()-16),21,7,7))
  x=8+c.frame.value()/end*(self.width()-16);p.setPen(QColor('#99dbe1'));p.drawLine(round(x),4,round(x),35);p.drawText(8,16,'Local frames0–'+str(end));p.end()
 def mousePressEvent(self,event):self.controls.frame.setValue(max(0,min(self.controls.key_end,round((event.position().x()-8)/max(1,self.width()-16)*self.controls.key_end))));event.accept()

class VisualControls:
 def __init__(self,inspector):
  self.ins=inspector;self.w=inspector.w;self.clip=None;self.version=None;self.updating=False;self.amount_draft=None;self.amount_effect=None;self.key_intent=None;self.transition_intent=None;self.key_end=1;self.timer=QTimer(inspector);self.timer.setSingleShot(True);self.timer.setInterval(180);self.timer.timeout.connect(self.flush)
  self.effects_panel=QWidget();layout=QVBoxLayout(self.effects_panel);layout.setContentsMargins(0,0,0,0);self.effect_note=QLabel('Select one picture clip for its effect stack.');self.effect_note.setWordWrap(True);layout.addWidget(self.effect_note);self.stack=QListWidget();self.stack.setMaximumHeight(125);self.stack.currentItemChanged.connect(lambda *_:self.select_effect());layout.addWidget(self.stack);line=QHBoxLayout();layout.addLayout(line);self.search=QComboBox();self.search.setEditable(True);self.search.addItems(EFFECTS);self.search.setAccessibleName('Search supported effects');line.addWidget(self.search,1);add=QPushButton('Add');add.clicked.connect(self.add_effect);line.addWidget(add)
  self.bypass=QCheckBox('Enabled');self.bypass.clicked.connect(lambda checked:self.effect_change(dict(enabled=checked)));layout.addWidget(self.bypass);line=QHBoxLayout();layout.addLayout(line)
  for title,fn in [('↑',lambda:self.move_effect(-1)),('↓',lambda:self.move_effect(1)),('Remove',self.remove_effect)]:b=QPushButton(title);b.clicked.connect(fn);line.addWidget(b)
  from studio_project_inspector import BoundSpin
  self.amount=BoundSpin(inspector);self.amount.setRange(0,4);self.amount.setDecimals(3);self.amount.setKeyboardTracking(False);self.amount.setAccessibleName('Selected effect amount');self.amount.lineEdit().textEdited.connect(lambda:self.pin_amount());self.amount.valueChanged.connect(self.amount_changed);self.amount.editingFinished.connect(self.flush);layout.addWidget(self.amount)
  self.keys_panel=QWidget();layout=QVBoxLayout(self.keys_panel);layout.setContentsMargins(0,0,0,0);self.key_note=QLabel('Keys use the preserved local clip origin. Linear/Hold applies after each key.');self.key_note.setWordWrap(True);layout.addWidget(self.key_note);self.parameters=QComboBox();self.parameters.setAccessibleName('Animated visual parameter');self.parameters.currentIndexChanged.connect(self.select_parameter);layout.addWidget(self.parameters);self.ruler=KeyRuler(self);layout.addWidget(self.ruler);self.keys=QTableWidget(0,3);self.keys.setHorizontalHeaderLabels(['Frame','Value','Mode']);self.keys.setMaximumHeight(130);self.keys.setEditTriggers(QAbstractItemView.NoEditTriggers);self.keys.setSelectionBehavior(QAbstractItemView.SelectRows);self.keys.cellClicked.connect(self.select_key);layout.addWidget(self.keys)
  self.frame=QSpinBox();self.frame.setRange(0,10368000);self.frame.setKeyboardTracking(False);self.frame.setAccessibleName('Key local frame');self.frame.valueChanged.connect(lambda _:self.ruler.update());self.value=QDoubleSpinBox();self.value.setDecimals(4);self.value.setKeyboardTracking(False);self.value.setAccessibleName('Key value');self.interpolation=QComboBox();self.interpolation.addItems(['Linear','Hold']);self.interpolation.setAccessibleName('Key outgoing interpolation')
  for label,box in [('Local frame',self.frame),('Value',self.value),('Interpolation',self.interpolation)]:line=QHBoxLayout();layout.addLayout(line);line.addWidget(QLabel(label));line.addWidget(box,1)
  for box in (self.frame,self.value):box.lineEdit().textEdited.connect(lambda:self.pin_key())
  line=QHBoxLayout();layout.addLayout(line)
  for title,fn in [('Set key',self.set_key),('Delete key',self.delete_key)]:b=QPushButton(title);b.clicked.connect(fn);line.addWidget(b)
  self.transition_panel=QWidget();layout=QVBoxLayout(self.transition_panel);layout.setContentsMargins(0,0,0,0);self.transition_note=QLabel('Dissolve uses adjacent Normal-blend picture clips and valid source handles. Linked audio receives matching linear fades.');self.transition_note.setWordWrap(True);layout.addWidget(self.transition_note);self.next_clip=QComboBox();self.next_clip.setAccessibleName('Dissolve incoming clip');layout.addWidget(self.next_clip);self.duration=QSpinBox();self.duration.setRange(2,10368000);self.duration.setValue(30);self.duration.setKeyboardTracking(False);self.duration.setAccessibleName('Dissolve duration frames');self.duration.lineEdit().textEdited.connect(lambda:self.pin_transition());layout.addWidget(self.duration);line=QHBoxLayout();layout.addLayout(line);self.transition_apply=QPushButton('Add dissolve');self.transition_apply.clicked.connect(self.apply_transition);line.addWidget(self.transition_apply);self.transition_remove=QPushButton('Remove');self.transition_remove.clicked.connect(self.remove_transition);line.addWidget(self.transition_remove)
  compact_table(self.keys);self.search.setMinimumWidth(70);self.search.setMinimumContentsLength(5);add.setFixedWidth(45)
  buttons=self.effects_panel.findChildren(QPushButton)
  for button in buttons:
   if button.text() in ('↑','↓'):button.setFixedWidth(28)
   elif button.text()=='Remove':button.setFixedWidth(68)
  line.removeWidget(self.transition_remove);layout.addWidget(self.transition_remove)
  self.key_filter=IntentFilter(inspector,self.pin_key,[self.frame,self.value,self.interpolation]);self.transition_filter=IntentFilter(inspector,self.pin_transition,[self.duration,self.next_clip]);self.next_clip.activated.connect(self.transition_destination)
 def selected_effect(self):
  item=self.stack.currentItem();return item.data(Qt.UserRole) if item else None
 def submit(self,label,changes,intent=None):return self.w.shell.safe(lambda:self.ins.submit_bound(label,changes,intent or self.ins.capture()))
 def add_effect(self):
  if not self.clip:return
  kind=next((k for k in EFFECTS if k.casefold()==self.search.currentText().strip().casefold()),None)
  if not kind:self.effect_note.setText('Supported effects: Brightness and Contrast.');return
  self.submit('Add '+kind,[dict(op='effect.add',id=self.clip['id'],kind=kind)])
 def effect_change(self,values):
  key=self.selected_effect()
  if self.clip and key:self.submit('Edit effect',[dict(op='effect.edit',id=self.clip['id'],effect=key,values=values)])
 def move_effect(self,delta):
  key=self.selected_effect();index=self.stack.currentRow()+delta
  if self.clip and key and 0<=index<self.stack.count():self.submit('Reorder effect',[dict(op='effect.move',id=self.clip['id'],effect=key,index=index)])
 def remove_effect(self):
  key=self.selected_effect()
  if self.clip and key:self.submit('Remove effect and its keys',[dict(op='effect.remove',id=self.clip['id'],effect=key)])
 def pin_amount(self):
  if not self.updating and self.amount_effect is None:self.amount_effect=self.selected_effect()
 def amount_changed(self,value):
  if self.updating or not self.clip:return
  self.pin_amount();self.amount_draft=dict(intent=self.amount.intent or self.ins.capture(),effect=self.amount_effect,value=value);self.timer.start()
 def flush(self):
  self.ins.flush()
 def take_draft(self):
  if self.amount_draft is None:return None
  self.timer.stop();draft=self.amount_draft;self.amount_draft=None;self.amount.intent=None;self.amount_effect=None
  if not self.clip or draft['effect']!=self.selected_effect() or not self.ins.matches(draft['intent']):self.effect_note.setText('Unsubmitted amount cancelled after effect/target changed.');self.ins.retained_property=dict(value=draft['value'],target=draft['intent']['ids']);self.version=None;return None
  row=draft['intent']['rows'][0];name='effect.'+draft['effect']+'.amount';channel=next((k for k in row['layout'].get('keys',[]) if k['parameter']==name),None)
  if channel:
   if not row['start']<=draft['intent']['frame']<row['start']+row['duration']:self.effect_note.setText('Seek inside the animated clip before changing an evaluated amount; nothing accepted.');return None
   frame=draft['intent']['frame']-row['start']+row['visual_window']['offset'];mode=next((p[2] for p in channel['points'] if p[0]==frame),'Linear');change=dict(op='keyframe.set',id=row['id'],parameter=name,frame=frame,value=draft['value'],interpolation=mode)
  else:change=dict(op='effect.edit',id=row['id'],effect=draft['effect'],values=dict(amount=draft['value']))
  return [change],draft['intent']
 def select_effect(self,preserve_input=False):
  if self.updating:return
  if preserve_input and self.amount.intent is not None:
   if self.ins.matches(self.amount.intent) and self.amount.hasFocus():return
   self.ins.retained_property=dict(value=self.amount.text(),target=self.amount.intent['ids']);self.effect_note.setText('Unsubmitted amount cancelled after target/revision changed; last input retained.')
  if self.amount_draft is not None:self.timer.stop();self.amount_draft=None;self.amount.intent=None;self.amount_effect=None;self.effect_note.setText('Unsubmitted amount cancelled after effect selection changed.')
  self.amount.intent=None;self.amount_effect=None
  effect=next((e for e in (self.clip or {}).get('layout',{}).get('effects',[]) if e['id']==self.selected_effect()),None);self.updating=True
  try:
   self.amount.setEnabled(effect is not None);self.bypass.setEnabled(effect is not None)
   if effect:
    layout=evaluated_layout(self.clip,self.w.transport_state().get('frame',0));self.amount.setValue(read_parameter(layout,'effect.'+effect['id']+'.amount'));self.bypass.setChecked(effect['enabled'])
  finally:self.updating=False
 def parameter_name(self):return self.parameters.currentData()
 def points(self):return next((k['points'] for k in (layout_for(self.clip) if self.clip else {}).get('keys',[]) if k['parameter']==self.parameter_name()),[])
 def select_parameter(self):
  if self.updating:return
  if self.key_intent is not None:self.key_note.setText('Unsubmitted key edit cancelled after parameter change.');self.key_intent=None
  self.update_keys()
 def update_keys(self):
  if not self.clip or not self.parameter_name():return
  self.updating=True
  try:
   points=self.points();self.keys.setRowCount(len(points))
   for row,point in enumerate(points):
    for column,value in enumerate(point):self.keys.setItem(row,column,QTableWidgetItem(str(value)))
   lo,hi=parameter(layout_for(self.clip),self.parameter_name());self.value.setRange(lo,hi);self.value.setValue(read_parameter(evaluated_for(self.clip,self.w.transport_state().get('frame',0)),self.parameter_name()));self.ruler.update()
  finally:self.updating=False
 def select_key(self,row,column):
  points=self.points()
  if row<len(points):self.frame.setValue(points[row][0]);self.value.setValue(points[row][1]);self.interpolation.setCurrentText(points[row][2]);self.key_intent=None
 def pin_key(self):
  if not self.updating and self.key_intent is None:self.key_intent=(self.ins.capture(),self.parameter_name())
 def set_key(self):
  if not self.clip:return
  intent,name=self.key_intent or (self.ins.capture(),self.parameter_name());self.key_intent=None
  self.submit('Set visual key',[dict(op='keyframe.set',id=intent['rows'][0]['id'],parameter=name,frame=self.frame.value(),value=self.value.value(),interpolation=self.interpolation.currentText())],intent)
 def delete_key(self):
  if not self.clip:return
  intent,name=self.key_intent or (self.ins.capture(),self.parameter_name());self.key_intent=None
  self.submit('Delete visual key',[dict(op='keyframe.remove',id=intent['rows'][0]['id'],parameter=name,frame=self.frame.value())],intent)
 def current_transition(self):return next((t for t in self.w.document().get('transitions',[]) if self.clip and self.clip['id'] in (t['left'],t['right'])),None)
 def pin_transition(self):
  if not self.updating and self.transition_intent is None:self.transition_intent=(self.ins.capture(),deepcopy(self.current_transition()),self.next_clip.currentData())
 def transition_destination(self,index):
  if self.transition_intent:self.transition_intent=(*self.transition_intent[:2],self.next_clip.itemData(index))
 def apply_transition(self):
  if not self.clip:return
  intent,current,right=self.transition_intent or (self.ins.capture(),self.current_transition(),self.next_clip.currentData());self.transition_intent=None
  if current:change=dict(op='transition.edit',id=current['id'],duration=self.duration.value())
  elif right:change=dict(op='transition.add',left=intent['rows'][0]['id'],right=right,duration=self.duration.value())
  else:self.transition_note.setText('Select an outgoing clip adjacent to another Normal-blend picture clip.');return
  self.submit('Dissolve',[change],intent)
 def remove_transition(self):
  current=self.current_transition()
  if current:self.submit('Remove dissolve',[dict(op='transition.remove',id=current['id'])])
 def refresh(self):
  rows=self.ins.rows;state=self.w.state();frame=self.w.transport_state().get('frame',0);doc=state.get('document') or {};tracks={t['id']:t for t in doc.get('tracks',[])};clip=rows[0] if self.ins.category in ('clips','captions','graphics') and len(rows)==1 and tracks[rows[0]['track']]['kind']!='audio' else None;version=(state.get('epoch'),state.get('revision'),clip['id'] if clip else None,frame,bool(self.w.pending))
  if self.version==version:return
  if self.amount_draft is not None and not self.ins.matches(self.amount_draft['intent']):self.timer.stop();self.amount_draft=None;self.amount.intent=None;self.amount_effect=None;self.effect_note.setText('Unsubmitted amount cancelled after target/revision change.')
  self.version=version;self.clip=clip;self.updating=True
  try:
   selected=self.selected_effect();name=self.parameter_name();self.stack.clear();self.parameters.clear();self.next_clip.clear();self.effect_note.setText('Ordered source-color effects; bypass preserves recipe.' if clip else 'Select one picture clip for effects/keys/transitions.')
   for box in (self.effects_panel,self.keys_panel,self.transition_panel):box.setEnabled(clip is not None and not self.w.pending and not tracks[clip['track']].get('locked',False) if clip else False)
   if not clip:return
   for effect in layout_for(clip).get('effects',[]):
    item=QListWidgetItem(effect['kind']+(' • bypassed' if not effect['enabled'] else ''));item.setData(Qt.UserRole,effect['id']);self.stack.addItem(item)
    if effect['id']==selected:self.stack.setCurrentItem(item)
   if self.stack.currentRow()<0 and self.stack.count():self.stack.setCurrentRow(0)
   params=[('Position X','bounds.0'),('Position Y','bounds.1'),('Width','bounds.2'),('Height','bounds.3'),('Rotation','rotation'),('Opacity','opacity')]
   if 'layout' in clip:params+=[('Brightness','brightness')]+[(e['kind']+' '+str(i+1)+' amount','effect.'+e['id']+'.amount') for i,e in enumerate(clip['layout'].get('effects',[]))]
   for label,key in params:self.parameters.addItem(label,key)
   index=self.parameters.findData(name);self.parameters.setCurrentIndex(max(0,index));self.key_end=max(1,clip.get('visual_window',dict(duration=clip['duration']))['duration']-1,max((p[0] for k in layout_for(clip).get('keys',[]) for p in k['points']),default=0));self.frame.setRange(0,self.key_end)
   if self.key_intent is None:self.frame.setValue(max(0,min(self.key_end,frame-clip['start']+clip.get('visual_window',dict(offset=0))['offset'])))
   for row in doc.get('clips',[]):
    if row['track']==clip['track'] and row['start']==clip['start']+clip['duration']:self.next_clip.addItem(row['name'],row['id'])
   current=self.current_transition();self.transition_apply.setText('Change dissolve' if current else 'Add dissolve');self.transition_remove.setEnabled(current is not None)
   if current and self.transition_intent is None:self.duration.setValue(current['duration'])
  finally:self.updating=False
  if self.amount_draft is None:self.select_effect(True)
  if self.key_intent is None:self.update_keys()

class EnvelopeEditor(QWidget):
 def __init__(self,inspector):
  super().__init__();self.ins=inspector;self.version=None;self.intent=None;self.updating=False;layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);self.note=QLabel('Clip envelope: preserved local frame / linear gain');self.note.setWordWrap(True);layout.addWidget(self.note);self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(['Frame','Gain']);self.table.setMaximumHeight(135);self.table.itemChanged.connect(lambda _:self.pin());layout.addWidget(self.table);line=QHBoxLayout();layout.addLayout(line)
  for title,fn in [('+ Point',self.add),('Remove point',self.remove)]:b=QPushButton(title);b.setFixedWidth(68 if title=='+ Point' else 88);b.clicked.connect(lambda checked=False,f=fn:self.ins.w.shell.safe(f));line.addWidget(b)
  apply=QPushButton('Apply envelope');apply.clicked.connect(self.apply);layout.addWidget(apply)
  reload=QPushButton('Reload selected envelope');reload.clicked.connect(self.reload);layout.addWidget(reload)
  compact_table(self.table)
 def pin(self):
  if not self.updating and self.intent is None:self.intent=self.ins.capture()
 def reload(self):
  self.intent=None;self.version=None;self.refresh();self.note.setText('Reloaded selected envelope; unaccepted table draft discarded.')
 def add(self):
  if self.table.rowCount()>=2048:self.note.setText('Existing2048-point envelope limit reached.');return
  self.pin();row=self.table.rowCount();frame=int(self.table.item(row-1,0).text())+1 if row else 0;self.table.insertRow(row);self.table.setItem(row,0,QTableWidgetItem(str(frame)));self.table.setItem(row,1,QTableWidgetItem('1.0'))
 def remove(self):
  if self.table.currentRow()>=0:self.pin();self.table.removeRow(self.table.currentRow())
 def apply(self):
  intent=self.intent or self.ins.capture()
  def submit():
   points=[[int(self.table.item(r,0).text()),float(self.table.item(r,1).text())] for r in range(self.table.rowCount())];key=self.ins.submit_bound('Clip envelope',[dict(op='clip.audio',id=r['id'],values=dict(envelope=points)) for r in intent['rows']],intent)
   if key:self.intent=None
  self.ins.w.shell.safe(submit)
 def refresh(self):
  rows=self.ins.rows;version=(self.ins.version,tuple(r['id'] for r in rows))
  if self.version==version or self.ins.category!='clips' or not rows:return
  self.version=version
  if self.intent is not None:return # retain edited table until explicit Apply/re-entry
  values=[r['audio']['envelope'] for r in rows];points=values[0] if all(v==values[0] for v in values) else [];self.note.setText('Mixed envelopes — Apply explicitly replaces selected curves.' if any(v!=values[0] for v in values) else 'Clip envelope: preserved local frame / linear gain');self.updating=True
  try:
   self.table.setRowCount(len(points))
   for row,point in enumerate(points):
    for column,value in enumerate(point):self.table.setItem(row,column,QTableWidgetItem(str(value)))
  finally:self.updating=False
