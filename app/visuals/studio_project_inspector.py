"""One inline Inspector over revision/selection-bound owner commands."""
from copy import deepcopy
from PySide6.QtCore import Qt,QTimer,QEvent
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QFormLayout,QLabel,QScrollArea,
 QDoubleSpinBox,QComboBox,QPushButton,QPlainTextEdit,QLineEdit,QToolButton,QCheckBox)

class BoundCombo(QComboBox):
 def showPopup(self):self.popup_intent=self.inspector.capture();super().showPopup()

class BoundSpin(QDoubleSpinBox):
 def __init__(self,inspector):
  super().__init__();self.inspector=inspector;self.intent=None;self.lineEdit().textEdited.connect(lambda:self.pin());self.installEventFilter(self)
 def pin(self):
  if not self.inspector.updating and self.intent is None:self.intent=self.inspector.capture()
 def eventFilter(self,obj,event):
  if event.type() in (QEvent.MouseButtonPress,QEvent.Wheel):self.pin()
  return super().eventFilter(obj,event)

class Inspector(QWidget):
 def __init__(self,w):
  super().__init__();self.w=w;self.version=None;self.display_binding=None;self.rows=[];self.category=None;self.binding=None;self.draft=None;self.draft_intent=None;self.draft_spins={};self.retained_property=None;self.text_intent=None;self.text_rejected=False;self.updating=False;self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(180);self.timer.timeout.connect(self.flush)
  root=QVBoxLayout(self);root.setContentsMargins(5,5,5,5);self.heading=QLabel('Select a clip to edit its properties.');self.heading.setWordWrap(True);root.addWidget(self.heading);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);root.addWidget(scroll,1);self.body=QWidget();self.form=QVBoxLayout(self.body);self.form.setContentsMargins(2,2,2,2);scroll.setWidget(self.body);self.fields={};self.groups={};self.lines={}
  self.group('Transform')
  for key,label,lo,hi,index in [('x','Position X %',-400,400,0),('y','Position Y %',-400,400,1),('width','Width %',.001,800,2),('height','Height %',.001,800,3)]:self.spin('Transform',key,label,lo,hi,100,'layout','bounds',index)
  self.spin('Transform','rotation','Rotation °',-36000,36000,1,'layout','rotation');reset=QPushButton('Reset transform');reset.clicked.connect(self.reset_transform);self.groups['Transform'][1].addRow(reset)
  self.group('Compositing');self.spin('Compositing','opacity','Opacity %',0,100,100,'layout','opacity');self.spin('Compositing','brightness','Brightness ×',0,4,1,'layout','brightness')
  for i,label in enumerate(('Crop left %','Crop top %','Crop right %','Crop bottom %')):self.spin('Compositing','crop'+str(i),label,0,100,100,'layout','crop',i)
  for field,items in [('fit',['Stretch','Fit','Fill']),('blend',['Normal','Multiply','Screen','Add','Difference'])]:self.combo('Compositing',field,field.title(),items,'layout')
  self.group('Audio');self.spin('Audio','gain','Clip gain ×',0,4,1,'audio','gain');self.spin('Audio','pan','Clip pan/balance %',-100,100,100,'audio','pan');self.spin('Audio','fade_in','Fade in frames',0,10368000,1,'audio','fade_in',decimals=0);self.spin('Audio','fade_out','Fade out frames',0,10368000,1,'audio','fade_out',decimals=0)
  self.group('Timing');self.spin('Timing','start','Start frame',0,10368000,1,'timing','start',decimals=0);self.spin('Timing','end','Out frame (exclusive)',1,10368000,1,'timing','end',decimals=0)
  self.group('Text');self.text=QPlainTextEdit();self.text.setAccessibleName('Selected title or caption text');self.text.setMaximumHeight(110);self.text.textChanged.connect(self.pin_text);self.groups['Text'][1].addRow(self.text);self.text_apply=QPushButton('Apply text');self.text_apply.clicked.connect(self.apply_text);self.groups['Text'][1].addRow(self.text_apply)
  self.group('Text style')
  self.spin('Text style','style_rotation','Text rotation °',-36000,36000,1,'style','rotation')
  for key,label in [('font','Font family'),('color','Text #RGB/ARGB'),('background','Background #RGB/ARGB')]:
   line=QLineEdit();line.intent=None;line.setAccessibleName(label);line.textEdited.connect(lambda _,b=line:self.pin_line(b));line.editingFinished.connect(lambda b=line,f=key:self.finish_line(b,f));self.groups['Text style'][1].addRow(label,line);self.lines[key]=line
  for field,label,lo,hi,default in [('size','Font size px',6,256,27),('padding','Padding px',0,256,10),('radius','Corner radius px',0,256,0),('stroke_width','Stroke px',0,16,0),('opacity','Text opacity %',0,100,1)]:self.spin('Text style','style_'+field,label,lo,hi,100 if field=='opacity' else 1,'style',field,default=default)
  for i,label in enumerate(('Text X %','Text Y %','Text width %','Text height %')):self.spin('Text style','style_bounds'+str(i),label,-400 if i<2 else .001,400 if i<2 else 800,100,'style','bounds',i)
  self.combo('Text style','align','Alignment',['left','center','right'],'style');self.bold=QCheckBox('Bold');self.bold.clicked.connect(lambda value:self.queue('style','bold',value));self.groups['Text style'][1].addRow(self.bold)
  from studio_project_visual_controls import VisualControls,EnvelopeEditor
  self.group('Effects');self.group('Keyframes');self.group('Transition');self.visual=VisualControls(self);self.groups['Effects'][1].addRow(self.visual.effects_panel);self.groups['Keyframes'][1].addRow(self.visual.keys_panel);self.groups['Transition'][1].addRow(self.visual.transition_panel);self.envelope=EnvelopeEditor(self);self.groups['Audio'][1].addRow(self.envelope)
  self.form.addStretch();self.setMinimumWidth(180)
 def group(self,name):
  box=QWidget();layout=QVBoxLayout(box);layout.setContentsMargins(0,0,0,0);layout.setSpacing(3);header=QToolButton();header.setText(name);header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon);header.setCheckable(True);header.setChecked(True);header.setArrowType(Qt.DownArrow);layout.addWidget(header);body=QWidget();form=QFormLayout(body);form.setContentsMargins(5,2,5,5);form.setSpacing(3);form.setRowWrapPolicy(QFormLayout.WrapLongRows);layout.addWidget(body);header.toggled.connect(lambda checked:(body.setVisible(checked),header.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)));self.form.addWidget(box);self.groups[name]=(box,form)
 def resizeEvent(self,event):
  for box,form in self.groups.values():form.setRowWrapPolicy(QFormLayout.WrapAllRows if self.width()<260 else QFormLayout.WrapLongRows)
  super().resizeEvent(event)
 def spin(self,group,key,label,low,high,factor,section,field,index=None,decimals=3,default=0.):
  box=BoundSpin(self);box.setRange(low,high);box.setDecimals(decimals);box.setKeyboardTracking(False);box.setAccessibleName(label);box.factor=factor;box.section=section;box.field=field;box.index=index;box.default=default;box.valueChanged.connect(lambda value,b=box:self.queue(b.section,b.field,round(value/b.factor) if b.section=='audio' and b.field in ('fade_in','fade_out') else value/b.factor,b.index,b.intent,raw=b.accessibleName()+': '+b.text(),source=b));box.editingFinished.connect(lambda b=box:self.finish_spin(b));self.groups[group][1].addRow(label,box);self.fields[key]=box
 def combo(self,group,key,label,items,section):
  box=BoundCombo();box.inspector=self;box.popup_intent=None;box.addItems(items);box.setAccessibleName(label);box.activated.connect(lambda index,b=box,f=key,s=section:self.combo_changed(b,s,f));self.groups[group][1].addRow(label,box);self.fields[key]=box
 def capture(self):
  binding=dict(self.display_binding or self.w.binding());binding['expected_command']=self.w.binding().get('expected_command')
  return dict(binding=binding,rows=deepcopy(self.rows),category=self.category,ids=tuple(sorted(r['id'] for r in self.rows)),frame=self.w.transport_state().get('frame',0))
 def matches(self,intent):
  c=self.w.timeline.canvas;current=self.w.binding();return intent['ids']==tuple(sorted(c.selection)) and intent['category']==(c.selected[0] if c.selected else None) and all(intent['binding'].get(k)==current.get(k) for k in ('expected_epoch','expected_revision','expected_project'))
 def reject(self,intent,value,message):
  retained=str(intent.get('raw_input',value if isinstance(value,(str,int,float,bool)) else 'property change'))[:512]
  self.retained_property=dict(targets=intent['ids'],category=intent['category'],value=retained);self.w.notice.setText(message+' Nothing accepted. Unapplied '+retained[:180]+'. Review the current target and re-enter deliberately.');self.timer.stop();self.draft=None;self.draft_intent=None;self.draft_spins={}
  for box in self.fields.values():
   if isinstance(box,BoundSpin):box.intent=None
  self.version=None;self.refresh()
 def combo_changed(self,box,section,field):
  intent=box.popup_intent or self.capture();box.popup_intent=None;self.queue(section,field,box.currentText(),intent=intent)
 def finish_spin(self,box):
  if box.intent is not None and not self.matches(box.intent):self.reject(box.intent,box.text(),'Inspector target changed.');box.intent=None;return
  self.flush();box.intent=None
 def pin_line(self,box):
  if not self.updating and box.intent is None:box.intent=self.capture()
 def finish_line(self,box,field):
  if not box.isModified():return
  intent=box.intent or self.capture();self.queue('style',field,box.text(),intent=intent);box.intent=None;box.setModified(False);self.flush()
 def queue(self,section,field,value,index=None,intent=None,raw=None,source=None):
  if self.updating or not self.rows:return
  intent=intent or self.capture()
  if raw is not None:intent['raw_input']=str(raw)[:512]
  if not self.matches(intent) or self.w.pending:self.reject(intent,value,'Inspector input is stale or another edit is pending.');return
  if self.draft is None:self.draft={};self.draft_intent=intent;self.draft_spins={};self.binding=intent['binding']
  elif self.draft_intent['ids']!=intent['ids'] or self.draft_intent['binding']!=intent['binding']:self.reject(intent,value,'Inspector gesture context changed.');return
  if source is not None:self.draft_spins[source]=source.intent
  for row in self.draft_intent['rows']:
   category=self.draft_intent['category']
   if section in ('layout','style'):
    name=field+'.'+str(index) if index is not None else field;channel=next((k for k in row[section].get('keys',[]) if k['parameter']==name),None)
    if channel:
     frame=intent['frame']-row['start']+row.get('visual_window',dict(offset=0))['offset']
     if not row['start']<=intent['frame']<row['start']+row['duration'] or frame<0:self.reject(intent,value,'Seek inside the animated item before changing an evaluated value.');return
     mode=next((p[2] for p in channel['points'] if p[0]==frame),'Linear');self.draft[('key',row['id'],name)]=dict(op='keyframe.set',id=row['id'],parameter=name,frame=frame,value=value,interpolation=mode);continue
   if section=='timing':
    op='items.trim' if category=='clips' else 'caption.edit' if category=='captions' else 'graphic.edit';change=self.draft.setdefault((op,row['id']),dict(op=op,id=row['id'],**({} if op=='items.trim' else {'values':{}})))
    if op=='items.trim':change[field]=round(value)
    else:
     values=change['values'];start=round(value) if field=='start' else values.get('start',row['start']);end=round(value) if field=='end' else values.get('start',row['start'])+values.get('duration',row['duration']);values.update(start=start,duration=end-start)
   elif section=='style':
    op='caption.edit' if category=='captions' else 'graphic.edit';style=self.draft.setdefault((op,row['id']),dict(op=op,id=row['id'],values=dict(style={})))['values']['style']
    if index is not None:style.setdefault(field,list(row['style'][field]))[index]=value
    else:style[field]=value
   else:
    name=field+'.'+str(index) if index is not None else field;animated=section=='layout' and any(k['parameter']==name for k in row['layout'].get('keys',[]))
    if animated:
     frame=self.draft_intent['frame']-row['start']+row.get('visual_window',dict(offset=0))['offset']
     if not row['start']<=self.draft_intent['frame']<row['start']+row['duration'] or frame<0:self.reject(intent,value,'Seek inside the animated clip before changing an evaluated value.');return
     channel=next(k for k in row['layout']['keys'] if k['parameter']==name);mode=next((p[2] for p in channel['points'] if p[0]==frame),'Linear');self.draft[('key',row['id'],name)]=dict(op='keyframe.set',id=row['id'],parameter=name,frame=frame,value=value,interpolation=mode)
    else:
     op='clip.'+section;change=self.draft.setdefault((op,row['id']),dict(op=op,id=row['id'],values={}))
     if index is not None:change['values'].setdefault(field,list(row['layout'].get(field,[0.,0.,1.,1.])))[index]=value
     else:change['values'][field]=value
  self.w.notice.setText('Inspector draft — not accepted yet.');self.timer.start()
 def submit_bound(self,label,changes,intent):
  if not self.matches(intent) or self.w.pending:self.reject(intent,changes,'Inspector target changed or another edit is pending.');return
  if len(changes)>128:raise ValueError('Inspector operation exceeds128 changes; nothing submitted.')
  binding=dict(intent['binding']);binding['expected_command']=self.w.binding().get('expected_command');return self.w.batch(label,changes,binding)
 def flush(self):
  if self.updating:return
  visual=self.visual.take_draft() if hasattr(self,'visual') else None
  if self.draft is None:
   if visual:self.w.shell.safe(lambda:self.submit_bound('Effect amount',*visual))
   return
  self.timer.stop();changes=list(self.draft.values());intent=self.draft_intent;spins=self.draft_spins;self.draft=None;self.draft_intent=None;self.draft_spins={}
  if visual:changes.extend(visual[0])
  def submit():
   try:self.submit_bound('Inspector properties',changes,intent)
   finally:
    for box,pinned in spins.items():
     if box.intent is pinned:box.intent=None
    self.version=None;self.refresh()
  self.w.shell.safe(submit)
 def reset_transform(self):
  intent=self.capture();changes=[]
  if self.category!='clips':return
  for row in intent['rows']:
   changes.extend(dict(op='keyframe.clear',id=row['id'],parameter=k['parameter']) for k in row['layout'].get('keys',[]) if k['parameter'].startswith('bounds.') or k['parameter']=='rotation');changes.append(dict(op='clip.layout',id=row['id'],values=dict(bounds=[0.,0.,1.,1.],rotation=0.)))
  self.w.shell.safe(lambda:self.submit_bound('Reset transform and its keys',changes,intent))
 def pin_text(self):
  if not self.updating and (self.text_intent is None or self.text_rejected):self.text_intent=self.capture();self.text_rejected=False
 def apply_text(self):
  if self.category not in ('captions','graphics') or not self.rows:return
  intent=self.text_intent or self.capture();text=self.text.toPlainText()
  if not self.matches(intent):self.text_rejected=True;self.w.notice.setText('Text target changed; unaccepted text retained. Re-select its target or edit deliberately for the current selection.');return
  def submit():
   key=self.submit_bound('Edit caption' if intent['category']=='captions' else 'Edit title',[dict(op='caption.edit' if intent['category']=='captions' else 'graphic.edit',id=r['id'],values=dict(text=text)) for r in intent['rows']],intent)
   if key:self.text_intent=None;self.text_rejected=False
  self.w.shell.safe(submit)
 def refresh(self):
  if self.updating:return
  w=self.w;s=w.state();c=w.timeline.canvas;selected=set(c.selection);category=c.selected[0] if c.selected else None;rows=[r for r in (s.get('document') or {}).get(category,[]) if r['id'] in selected] if category else [];frame=w.transport_state().get('frame',0);version=(s.get('epoch'),s.get('revision'),tuple(sorted(selected)),category,bool(w.pending),frame if any(r.get('layout',r.get('style',{})).get('keys') for r in rows) else None)
  if version==self.version:
   self.visual.refresh();return
  if self.draft is not None and (self.draft_intent is None or not self.matches(self.draft_intent)):self.timer.stop();self.retained_property=dict(value=str(self.draft)[:512]);self.draft=None;self.draft_intent=None;self.draft_spins={};w.notice.setText('Inspector draft cancelled after selection/revision change; nothing resubmitted.')
  self.version=version;self.rows=rows;self.category=category;self.display_binding=dict(expected_epoch=s.get('epoch'),expected_revision=s.get('revision'),expected_project=(s.get('document') or {}).get('id'),expected_command=s.get('command_revision'));self.updating=True
  try:
   self.heading.setText(('CAPTION • ' if category=='captions' else 'TITLE • ' if category=='graphics' else 'CLIP • ')+(rows[0].get('name',rows[0].get('text','')) if len(rows)==1 else str(len(rows))+' items • mixed values where shown') if rows else 'Select a clip to edit its properties.');tracks={t['id']:t for t in (s.get('document') or {}).get('tracks',[])};visual=bool(rows and category=='clips' and all(tracks[r['track']]['kind']!='audio' for r in rows));audio=bool(rows and category=='clips' and all(tracks[r['track']]['kind']=='audio' for r in rows));text=category in ('captions','graphics') and bool(rows);locked=any(tracks[r['track']].get('locked',False) for r in rows)
   states=[('Transform',visual),('Compositing',visual),('Audio',audio),('Timing',bool(rows)),('Text',text),('Text style',text),('Effects',visual),('Keyframes',visual or text),('Transition',visual)]
   batch_visibility=any(self.groups[name][0].isHidden()==show for name,show in states)
   # ADS may suppress an ancestor temporarily. Preserve our own paint flag,
   # not inherited effective disablement, so ancestor resumption still works.
   if batch_visibility:batch_updates=not self.body.testAttribute(Qt.WA_ForceUpdatesDisabled);batch_layout=self.form.isEnabled();self.body.setUpdatesEnabled(False);self.form.setEnabled(False)
   try:
    for name,show in states:self.groups[name][0].setVisible(show);self.groups[name][0].setEnabled(not w.pending and not locked)
   finally:
    if batch_visibility:self.form.setEnabled(batch_layout);self.form.activate();self.body.setUpdatesEnabled(batch_updates)
   from project_visual import evaluated_layout,evaluated_text
   display=[dict(r,layout=evaluated_layout(r,frame)) if visual else evaluated_text(r,frame) if text else r for r in rows]
   for key,box in self.fields.items():
    if not rows:continue
    if isinstance(box,BoundCombo):
     section='style' if key=='align' else 'layout'
     if section=='layout' and not visual or section=='style' and not text:continue
     values=[r[section][key] for r in display];box.setCurrentText(values[0]);box.setToolTip('Mixed values' if len(set(values))>1 else key.title());continue
    if box.section=='layout' and not visual or box.section=='audio' and not audio or box.section=='style' and not text:continue
    if self.draft is not None or box.intent is not None and box.hasFocus():continue
    values=[r['start'] if key=='start' else r['start']+r['duration'] if key=='end' else r[box.section].get(box.field,[0.,0.,1.,1.])[box.index] if box.index is not None else r[box.section].get(box.field,box.default) for r in display];box.setValue(values[0]*box.factor)
    if len(set(values))>1:box.lineEdit().clear();box.lineEdit().setPlaceholderText('Mixed')
   if text:
    for field,box in self.lines.items():
     if box.intent is not None and box.hasFocus():continue
     values=[r['style'][field] for r in rows];box.setText(values[0] if len(set(values))==1 else '');box.setPlaceholderText('Mixed' if len(set(values))>1 else '')
    self.bold.setChecked(all(r['style']['bold'] for r in rows));values=[r['text'] for r in rows]
    if self.text_intent is None:self.text.setPlainText(values[0] if len(set(values))==1 else '')
    self.text.setPlaceholderText('Mixed text — Apply explicitly replaces selected text' if len(set(values))>1 else '')
  finally:self.updating=False
  self.visual.refresh();self.envelope.refresh()
