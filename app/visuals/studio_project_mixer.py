"""Real track/bus/Master strips over the canonical owner graph and sample meters."""

from copy import deepcopy

import math,time

from PySide6.QtCore import Qt,QTimer,QRectF,QEvent

from PySide6.QtGui import QPainter,QColor,QPen

from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QLabel,QToolButton,QSlider,

 QDoubleSpinBox,QComboBox,QScrollArea,QInputDialog,QMessageBox,QMenu,QPushButton)



def db(gain):return -100. if gain<=0 else 20*math.log10(gain)

def gain(value):return 0. if value<=-100 else min(4.,10**(value/20))



class ResetSlider(QSlider):

 def mouseDoubleClickEvent(self,event):self.setValue(self.unity);self.resetRequested();event.accept()



class MixerNumber(QDoubleSpinBox):
 def __init__(self,strip,field):
  super().__init__();self.strip=strip;self.field=field;self.intent=None;self.accepted_value=0.;self.lineEdit().textEdited.connect(lambda:self.pin());self.installEventFilter(self);self.lineEdit().installEventFilter(self)
 def pin(self):
  if not self.strip.updating and self.intent is None:self.intent=dict(self.strip.w.binding())
 def eventFilter(self,watched,event):
  if event.type() in (QEvent.MouseButtonPress,QEvent.Wheel):self.pin()
  return super().eventFilter(watched,event)
 def stepBy(self,steps):self.pin();super().stepBy(steps)
 def accepted(self,value):
  self.accepted_value=value
  if self.intent is None:self.setValue(value)

class ResetBalance(MixerNumber):
 def eventFilter(self,watched,event):
  if event.type()==QEvent.MouseButtonDblClick:self.pin();self.setValue(0.);self.editingFinished.emit();event.accept();return True
  return super().eventFilter(watched,event)

class Meter(QWidget):

 """Levels are measured submitted-block samples at estimated playback time."""

 def __init__(self):

  super().__init__();self.value=None;self.hold=[0.,0.];self.hold_until=[0.,0.];self.clipped=[False,False];self.setMinimumSize(26,70);self.setMaximumWidth(34);self.setToolTip('Post-fader/gate stereo samples at submitted-minus-padding estimate, not measured heard time. Peaks hold3seconds; clipping latches at0dBFS. Click to reset.');self.setAccessibleName('Stereo signal meter; click resets held peak and clipping')

 def set_levels(self,value):

  self.value=value;now=time.monotonic()

  if value:

   for i,p in enumerate(value['peak']):

    if p>=self.hold[i] or now>=self.hold_until[i]:self.hold[i]=p;self.hold_until[i]=now+3.

    self.clipped[i]|=value['clipped'][i]

  elif now>=max(self.hold_until):self.hold=[0.,0.]

  self.update()

 def mousePressEvent(self,event):self.hold=[0.,0.];self.hold_until=[0.,0.];self.clipped=[False,False];self.update();event.accept()

 def paintEvent(self,event):

  p=QPainter(self);p.fillRect(self.rect(),QColor('#0a1116'));width=max(4,(self.width()-8)//2);height=self.height()-12

  for i in range(2):

   x=3+i*(width+2);value=self.value['peak'][i] if self.value else 0.;level=max(0,min(1,(db(value)+60)/60));p.fillRect(x,6,width,height,QColor('#182932'));bar=round(height*level);p.fillRect(x,6+height-bar,width,bar,QColor('#e7ae65' if value>.89 else '#65bda9'));mark=max(0,min(1,(db(self.hold[i])+60)/60));y=6+height-round(height*mark);p.setPen(QColor('#dce8df'));p.drawLine(x,y,x+width,y);p.fillRect(x,0,width,4,QColor('#e57768' if self.clipped[i] else '#26343d'))

  if self.value is None:p.setPen(QColor('#87979f'));p.drawText(self.rect(),Qt.AlignCenter,'—')

  p.end()



class RouteBox(QComboBox):

 def showPopup(self):self.pinned_binding=self.strip.w.binding();self.pinned_id=self.strip.key;super().showPopup()



class Strip(QWidget):

 def __init__(self,mixer,kind,key):

  super().__init__();self.mixer=mixer;self.w=mixer.workspace;self.kind=kind;self.key=key;self.revision=None;self.values=None;self.updating=False;self.draft=None;self.gesture_binding=None;self.cancelled=False;self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(180);self.timer.timeout.connect(self.flush);self.setFixedWidth(130);self.setObjectName('mixer-'+kind+'-'+key);layout=QVBoxLayout(self);layout.setContentsMargins(6,5,6,5);layout.setSpacing(3)

  self.name=QToolButton();self.name.setFixedHeight(22);self.name.setToolButtonStyle(Qt.ToolButtonTextOnly);self.name.setSizePolicy(self.name.sizePolicy().horizontalPolicy(),self.name.sizePolicy().verticalPolicy());self.name.setToolTip('Bus options' if kind=='bus' else 'Track name follows Timeline' if kind=='track' else 'Final rendered stereo mix');layout.addWidget(self.name)

  if kind=='bus':self.name.clicked.connect(lambda:self.bus_menu())

  else:self.name.setFocusPolicy(Qt.NoFocus);self.name.setAutoRaise(True)

  self.output=RouteBox();self.output.setFixedHeight(26);self.output.strip=self;self.output.pinned_binding=None;self.output.pinned_id=key;self.output.setAccessibleName(kind+' output destination');self.output.activated.connect(self.route_changed);layout.addWidget(self.output)

  self.device=QPushButton('Audio Settings');self.device.setToolTip('Existing Audio Settings; rendered Master gain is separate from playback/hardware volume.');self.device.clicked.connect(lambda:self.w.shell.audio_menu.exec(self.device.mapToGlobal(self.device.rect().bottomLeft())));layout.addWidget(self.device);self.device.setVisible(kind=='master');self.output.setVisible(kind!='master')

  middle=QHBoxLayout();layout.addLayout(middle,1);self.fader=ResetSlider(Qt.Vertical);self.fader.setRange(0,1001);self.fader.unity=round((0.+80)/(20*math.log10(4)+80)*1000)+1;self.fader.setMinimumHeight(70);self.fader.setAccessibleName(kind+' gain fader');self.fader.setToolTip('Authored gain.0dB unity,−∞silence. Double-click resets0dB.');self.fader.valueChanged.connect(self.fader_changed);self.fader.sliderPressed.connect(self.pin);self.fader.sliderReleased.connect(self.flush);self.fader.resetRequested=self.reset_fader;middle.addWidget(self.fader);self.meter=Meter();middle.addWidget(self.meter)

  self.db=MixerNumber(self,'gain');self.db.setFixedHeight(26);self.db.setRange(-100,20*math.log10(4));self.db.setDecimals(2);self.db.setSuffix(' dB');self.db.setSpecialValueText('−∞');self.db.setKeyboardTracking(False);self.db.setAccessibleName(kind+' gain dB');self.db.valueChanged.connect(lambda value:self.numeric_changed(self.db,gain(value)));self.db.editingFinished.connect(lambda:self.finish_numeric(self.db));layout.addWidget(self.db)

  self.pan=ResetBalance(self,'balance' if kind=='bus' else 'pan');self.pan.setFixedHeight(26);self.pan.setRange(-100,100);self.pan.setDecimals(1);self.pan.setSuffix(' %');self.pan.setKeyboardTracking(False);self.pan.setAccessibleName('Bus balance' if kind=='bus' else 'Track pan/balance');self.pan.setToolTip('Linear channel balance; center0% unity; −100%left,+100%right. Mono keeps legacy duplication at center. Double-click/Reset centers.');self.pan.valueChanged.connect(lambda value:self.numeric_changed(self.pan,value/100));self.pan.editingFinished.connect(lambda:self.finish_numeric(self.pan));layout.addWidget(self.pan);self.pan.setVisible(kind!='master')

  row=QHBoxLayout();layout.addLayout(row);self.mute=QToolButton();self.mute.setText('M');self.mute.setCheckable(True);self.mute.setAccessibleName(kind+' mute');self.mute.clicked.connect(lambda checked:self.immediate('mute',checked));row.addWidget(self.mute);self.solo=QToolButton();self.solo.setText('S');self.solo.setCheckable(True);self.solo.setAccessibleName(kind+' solo');self.solo.clicked.connect(lambda checked:self.immediate('solo',checked));row.addWidget(self.solo);self.solo.setVisible(kind!='master')

  reset=QToolButton();reset.setText('↺');reset.setToolTip('Reset gain to0dB and pan/balance to center');reset.clicked.connect(self.reset);row.addWidget(reset);self.peak=QLabel('Peak —');self.peak.setToolTip(self.meter.toolTip());layout.addWidget(self.peak)

 def pin(self):

  if self.gesture_binding is None:self.gesture_binding=self.w.binding();self.cancelled=False

 def reject_numeric(self,box):
  self.mixer.retained_numeric=dict(kind=self.kind,id=self.key,field=box.field,text=box.text()[:512],binding=box.intent);self.timer.stop();self.draft=None;self.gesture_binding=None;box.intent=None;box.blockSignals(True);box.setValue(box.accepted_value);box.blockSignals(False);self.w.notice.setText('Mixer number changed context before completion. Nothing submitted; input retained in Mixer for explicit re-entry.');self.mixer.refresh()
 def numeric_changed(self,box,value):
  if self.updating:return
  intent=box.intent or self.w.binding()
  if intent!=self.w.binding() or self.w.pending:self.reject_numeric(box);return
  self.mixer.retained_numeric=None;self.gesture_binding=dict(intent);self.queue(box.field,value)
 def finish_numeric(self,box):
  if box.intent is not None and box.intent!=self.w.binding():self.reject_numeric(box);return
  self.flush();box.intent=None
 def reset_fader(self):

  self.queue('gain',1.);self.flush()

 def queue(self,field,value):

  if self.updating or self.cancelled:return

  if self.w.pending:self.mixer.cancel_drafts('Mixer change not accepted while an edit is pending; previous values restored.');return

  self.pin();self.draft=dict(self.draft or {},**{field:value});self.timer.start()

 def fader_changed(self,value):

  if self.updating:return

  self.queue('gain',0. if value==0 else 10**((-80+(value-1)/1000*(20*math.log10(4)+80))/20))

  if self.draft is not None:self.db.blockSignals(True);self.db.setValue(db(self.draft.get('gain',self.values.get('audio',self.values)['gain'])));self.db.blockSignals(False)

 def changes(self,values):

  if self.kind=='master':return [dict(op='master.audio',values=values)]

  if self.kind=='bus':return [dict(op='bus.edit',id=self.key,values=values)]

  audio={k:v for k,v in values.items() if k!='solo'};return ([dict(op='track.audio',id=self.key,values=audio)] if audio else [])+([dict(op='track.edit',id=self.key,values=dict(solo=values['solo']))] if 'solo' in values else [])

 def flush(self):

  if self.updating or self.draft is None or self.cancelled:return

  self.w.shell.safe(self.mixer.flush)

 def immediate(self,field,value):self.queue(field,value);self.flush()

 def reset(self):

  self.queue('gain',1.)

  if self.kind!='master':self.queue('balance' if self.kind=='bus' else 'pan',0.)

  self.flush()

 def route_changed(self,index):

  if self.updating:return

  binding=self.output.pinned_binding or self.w.binding();self.output.pinned_binding=None;destination=self.output.itemData(index)

  if isinstance(destination,str) and destination.startswith('missing:'):return

  change=dict(op='track.output',id=self.key,output=destination) if self.kind=='track' else dict(op='bus.edit',id=self.key,values=dict(output=destination));self.w.shell.safe(lambda:self.w.batch('Route '+self.name.text(),[change],binding))

 def bus_menu(self):

  binding=self.w.binding();name=self.name.text();affected=[t['name'] for t in self.w.document()['tracks'] if t.get('output')==self.key];menu=QMenu(self);rename=menu.addAction('Rename bus…');remove=menu.addAction('Delete bus…');choice=menu.exec(self.name.mapToGlobal(self.name.rect().bottomLeft()))

  if choice is rename:

   text,ok=QInputDialog.getText(self,'Rename bus','Name',text=name)

   if ok:self.w.shell.safe(lambda:self.w.batch('Rename bus',[dict(op='bus.edit',id=self.key,values=dict(name=text))],binding))

  elif choice is remove:

   message=QMessageBox(self);message.setWindowTitle('Delete bus');message.setText('Affected tracks: '+(', '.join(affected) if affected else 'none')+'\nChoose their destination. Original media and clips stay intact.');master=message.addButton('Reroute to Master',QMessageBox.AcceptRole);none=message.addButton('Disconnect to None',QMessageBox.DestructiveRole);message.addButton(QMessageBox.Cancel);message.exec();clicked=message.clickedButton()

   if clicked in (master,none):self.w.shell.safe(lambda:self.w.batch('Delete bus with explicit routing',[dict(op='bus.remove',id=self.key,reroute='master' if clicked is master else None)],binding))

 def refresh(self,row,buses,version,pending):

  if version!=self.revision and self.draft is not None:self.timer.stop();self.draft=None;self.gesture_binding=None;self.cancelled=self.fader.isSliderDown();self.mixer.message.setText('Mixer gesture cancelled after a revision change; nothing automatically resubmitted.')

  routes=tuple((bus['id'],bus['name']) for bus in buses)

  if self.values==row and getattr(self,'routes',None)==routes:

   self.revision=version

   for box in (self.db,self.fader,self.pan,self.mute,self.solo,self.output):

    if box.isEnabled()==pending:box.setEnabled(not pending)

   return

  self.revision=version;self.routes=routes;self.values=deepcopy(row);self.updating=True

  try:

   self.name.setText(row['name']);self.name.setToolTip(row['name']+(' • Bus options' if self.kind=='bus' else ''));audio=row['audio'] if self.kind=='track' else row;value=audio['gain'];self.db.accepted(db(value));self.fader.setValue(0 if value<=0 else max(1,min(1001,round((db(value)+80)/(20*math.log10(4)+80)*1000)+1)));self.pan.accepted(audio.get('pan' if self.kind=='track' else 'balance',0)*100);self.mute.setChecked(audio['mute']);self.solo.setChecked(row.get('solo',False));self.output.clear();self.output.addItem('Master','master')

   if self.kind=='track':

    for bus in buses:self.output.addItem(bus['name'],bus['id'])

   self.output.addItem('None',None);destination=row.get('output','master');index=next((i for i in range(self.output.count()) if self.output.itemData(i)==destination),-1)

   if index<0:self.output.addItem('Missing bus — choose output','missing:'+str(destination));index=self.output.count()-1

   self.output.setCurrentIndex(index)

   for box in (self.db,self.fader,self.pan,self.mute,self.solo,self.output):box.setEnabled(not pending)

  finally:self.updating=False

 def levels(self,value):

  self.meter.set_levels(value);peak=max(self.meter.hold);self.peak.setText('Peak '+('−∞' if peak<=0 else f'{db(peak):.1f}')+' dB')



class TrackMixer(QWidget):

 def __init__(self,workspace):

  super().__init__();self.workspace=workspace;self.strips={};self.version=None;self.closed=False;self.retained_numeric=None;layout=QVBoxLayout(self);layout.setContentsMargins(4,4,4,4);row=QHBoxLayout();layout.addLayout(row);add=QPushButton('+ Bus');add.clicked.connect(self.add_bus);row.addWidget(add);track=QPushButton('+ Audio Track');track.clicked.connect(lambda:workspace.timeline.quick_track('audio'));row.addWidget(track);row.addStretch();self.message=QLabel('');self.message.setWordWrap(True);self.message.setMinimumHeight(self.message.fontMetrics().lineSpacing()*2+4);layout.addWidget(self.message);body=QHBoxLayout();layout.addLayout(body,1);self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);body.addWidget(self.scroll,1);self.channels=QWidget();self.channel_layout=QHBoxLayout(self.channels);self.channel_layout.setContentsMargins(0,0,0,0);self.channel_layout.setSpacing(3);self.scroll.setWidget(self.channels);self.master=Strip(self,'master','master');body.addWidget(self.master);self.setMinimumSize(280,250)

 def add_bus(self):

  binding=self.workspace.binding();name,ok=QInputDialog.getText(self,'Add named bus','Bus name')

  if ok:self.workspace.shell.safe(lambda:self.workspace.batch('Add named bus',[dict(op='bus.add',name=name)],binding))

 def cancel_drafts(self,message):

  for box in [*self.strips.values(),self.master]:box.timer.stop();box.draft=None;box.gesture_binding=None;box.revision=None

  self.version=None;self.refresh();self.message.setText(message);self.message.show()

 def flush(self):

  boxes=[b for b in [*self.strips.values(),self.master] if b.draft is not None]

  if not boxes:return

  w=self.workspace;binding=boxes[0].gesture_binding

  if w.pending or binding!=w.binding() or any(b.gesture_binding!=binding for b in boxes):self.cancel_drafts('Mixer draft cancelled after pending work or target change; nothing submitted.');return

  changes=[change for b in boxes for change in b.changes(b.draft)]

  if len(changes)>128:self.cancel_drafts('Mixer draft exceeds128 changes; nothing submitted.');return

  for box in boxes:box.timer.stop();box.draft=None;box.gesture_binding=None;box.db.intent=None;box.pan.intent=None

  try:w.batch('Mixer properties',changes,binding)

  except Exception:self.cancel_drafts('Mixer change was not submitted; previous values restored.');raise

 def refresh(self):

  if self.closed:return

  w=self.workspace;s=w.state();document=s.get('document') or {};version=(s.get('epoch'),s.get('revision'),w.pending['id'] if w.pending else None);buses=document.get('buses',[]);rows=[('track',t) for t in sorted(document.get('tracks',[]),key=lambda t:t['order']) if t['kind']=='audio']+[('bus',b) for b in buses];needed={row['id'] for _,row in rows}

  requested={};p=w.pending

  if p:

   request=p['request'];binding=w.binding()

   if request.get('op')=='batch' and all(request.get(key)==binding.get(key) for key in ('expected_epoch','expected_revision','expected_project')):

    for change in request.get('changes',[]):

     kind={'track.audio':'track','track.edit':'track','track.output':'track','bus.edit':'bus','master.audio':'master'}.get(change['op'])

     if kind:

      key=change.get('id','master');values=dict(output=change['output']) if change['op']=='track.output' else change['values'];requested.setdefault((kind,key),{}).update({k:v for k,v in values.items() if k in ('gain','pan','balance','mute','solo','output')})

  def display(kind,row):

   values=requested.get((kind,row.get('id','master')))

   if not values:return row

   row=deepcopy(row)

   for key,value in values.items():

    if kind=='track' and key in ('gain','pan','mute'):row['audio'][key]=value

    else:row[key]=value

   return row

  if version!=self.version:

   self.version=version

   for key in list(self.strips):

    if key not in needed:box=self.strips.pop(key);self.channel_layout.removeWidget(box);box.timer.stop();box.deleteLater()

   for index,(kind,row) in enumerate(rows):

    box=self.strips.get(row['id'])

    if box is None:box=Strip(self,kind,row['id']);self.strips[row['id']]=box

    item=self.channel_layout.itemAt(index)

    if item is None or item.widget() is not box:self.channel_layout.insertWidget(index,box)

    box.refresh(display(kind,row),buses,version,bool(w.pending))

   self.master.refresh(display('master',dict(document.get('master',dict(gain=1.,mute=False)),name='MASTER')),buses,version,bool(w.pending))

   from project_audio_graph import missing_routes

   missing=missing_routes(document) if document else [];self.message.setText('Missing bus destinations: '+', '.join(r['name'] for r in missing) if missing else 'No audio tracks — add an Audio Track.' if not rows else '');self.message.show()

  clock=w.transport_state();fast=getattr(w.client,'project_clock',None);audio=(fast.get('audio_report') if fast and (fast.get('epoch'),fast.get('revision'))==(s.get('epoch'),s.get('revision')) else None) or w.client.snapshot.get('audio_hub',{}).get('project_audio',{});binding=audio.get('binding') or [];target=clock.get('audio_target',s.get('audio_target','program'));source_active=target=='source' and clock.get('source',{}).get('active',False);matches=target=='program' and len(binding)>=5 and binding[0]==s.get('epoch') and binding[1]==s.get('revision') and binding[2]==clock.get('generation') and binding[4]==document.get('id');idle=not source_active and (not clock.get('active') or not clock.get('playing'));levels=audio.get('levels') if matches and not idle else None;zero=dict(peak=[0.,0.],rms=[0.,0.],clipped=[False,False])

  for key,box in self.strips.items():box.levels((levels or {}).get(key) if levels is not None else zero if idle else None)

  self.master.levels((levels or {}).get('master') if levels is not None else zero if idle else None);device=w.client.snapshot.get('audio_hub',{}).get('output_device_name');self.master.device.setText(self.master.device.fontMetrics().elidedText(device or 'Audio Settings',Qt.ElideRight,108));self.master.device.setToolTip((('Last output: ' if idle else 'Output: ')+device+' • ' if device else '')+'Existing Audio Settings; Master is the rendered mix. Playback/hardware volume is separate.\n'+audio.get('meter_basis','Meters idle; submitted-minus-padding estimate is not a measured heard-device clock.'))

  if not idle and not matches:self.message.setText('Source audition owns output.' if w.state().get('audio_target')=='source' else 'Preparing current mix.');self.message.show()

  if self.retained_numeric:
   retained=self.retained_numeric;self.message.setText('Unapplied '+retained['kind']+' '+retained['field']+': '+retained['text']+'. Context changed; re-enter explicitly.');self.message.show()
  if requested:self.message.setText('Applying Mixer controls — displayed request is not yet accepted. Existing accepted mix continues.');self.message.show()



 def close_resources(self):

  self.closed=True

  for box in [*self.strips.values(),self.master]:box.timer.stop();box.draft=None;box.gesture_binding=None
