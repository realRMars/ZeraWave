"""Compact native editor controls; commands stay with the existing owner."""
from fractions import Fraction
from functools import lru_cache
import math,re
from PySide6.QtCore import Qt,QSize,QPointF,QRectF
from PySide6.QtGui import QIcon,QPixmap,QPainter,QPen,QColor,QPolygonF
from PySide6.QtWidgets import QWidget,QHBoxLayout,QToolButton,QComboBox,QLineEdit,QLabel,QMenu,QSizePolicy,QApplication

def editor_icon(name):
 screen=QApplication.primaryScreen();dpr=screen.devicePixelRatio() if screen else 1.;return _editor_icon(name,dpr)

@lru_cache(maxsize=64)
def _editor_icon(name,dpr):
 image=QPixmap(round(24*dpr),round(24*dpr));image.setDevicePixelRatio(dpr);image.fill(Qt.transparent);p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(QColor('#b9e9ee'),1.6));p.setBrush(QColor('#b9e9ee'))
 def triangle(points):p.drawPolygon(QPolygonF([QPointF(*point) for point in points]))
 if name=='play':triangle([(8,5),(19,12),(8,19)])
 elif name=='pause':p.drawRect(7,5,3,14);p.drawRect(14,5,3,14)
 elif name in ('beginning','previous','next','last'):
  back=name in ('beginning','previous');triangle([(16,6),(7,12),(16,18)] if back else [(8,6),(17,12),(8,18)]);x=5 if name=='beginning' else 19 if name=='last' else 18 if back else 5;p.drawLine(x,5,x,19)
 elif name in ('in','out'):
  x=8 if name=='in' else 16;dx=7 if name=='in' else -7;p.drawLine(x,5,x,19);p.drawLine(x,5,x+dx,5);p.drawLine(x,19,x+dx,19)
 elif name=='select':triangle([(6,3),(18,14),(12,14),(10,21)])
 elif name=='razor':p.setBrush(Qt.NoBrush);p.drawPolygon(QPolygonF([QPointF(7,6),QPointF(14,3),QPointF(19,16),QPointF(12,20)]));p.drawLine(8,9,17,14)
 elif name=='snap':p.setBrush(Qt.NoBrush);p.drawArc(5,4,14,14,180*16,180*16);p.drawLine(5,10,5,16);p.drawLine(19,10,19,16)
 elif name=='linked':
  p.setBrush(Qt.NoBrush);p.drawRoundedRect(QRectF(3,8,12,7),3,3);p.drawRoundedRect(QRectF(9,8,12,7),3,3)
 elif name in ('add','plus','minus'):
  p.drawLine(5,12,19,12)
  if name!='minus':p.drawLine(12,5,12,19)
 elif name in ('fit','fullscreen'):
  for x,y,dx,dy in [(4,4,5,5),(20,4,-5,5),(4,20,5,-5),(20,20,-5,-5)]:p.drawLine(x,y,x+dx,y);p.drawLine(x,y,x,y+dy)
 elif name=='mixer':
  for x,y in [(6,8),(12,15),(18,10)]:p.drawLine(x,4,x,20);p.drawRect(x-2,y-2,4,4)
 elif name=='loop':p.setBrush(Qt.NoBrush);p.drawArc(QRectF(4,4,16,16),35*16,290*16);triangle([(20,3),(22,10),(15,8)])
 elif name=='ripple':p.drawLine(12,3,12,21);p.drawLine(3,12,9,12);p.drawLine(15,12,21,12);triangle([(6,9),(10,12),(6,15)]);triangle([(18,9),(14,12),(18,15)])
 elif name=='lock':p.setBrush(Qt.NoBrush);p.drawRoundedRect(QRectF(6,10,12,10),1,1);p.drawArc(QRectF(8,3,8,13),0,180*16)
 elif name=='visible':p.setBrush(Qt.NoBrush);p.drawEllipse(QRectF(3,7,18,10));p.drawEllipse(QRectF(10,10,4,4))
 else:
  for x in (5,12,19):p.drawEllipse(QPointF(x,12),1,1)
 p.end();return QIcon(image)

def tool_button(name,label,callback,parent=None,checkable=False):
 b=QToolButton(parent);b.setIcon(editor_icon(name));b.setIconSize(QSize(22,22));b.setFixedSize(28,28);b.setAccessibleName(label);b.setToolTip(label);b.setCheckable(checkable)
 if callback:b.clicked.connect(callback)
 return b

def timecode(frame,fps):
 nominal=math.ceil(Fraction(*fps));seconds,ff=divmod(max(0,int(frame)),nominal);minutes,ss=divmod(seconds,60);hh,mm=divmod(minutes,60);return f'{hh:02}:{mm:02}:{ss:02}:{ff:02}'
def timecode_frame(text,fps):
 if not re.fullmatch(r'\d{2,}:\d{2}:\d{2}:\d{2,3}',text):raise ValueError('Use HH:MM:SS:FF non-drop frame timecode.')
 hh,mm,ss,ff=map(int,text.split(':'));nominal=math.ceil(Fraction(*fps))
 if mm>=60 or ss>=60 or ff>=nominal:raise ValueError('Timecode field exceeds the nominal frame rate.')
 return ((hh*60+mm)*60+ss)*nominal+ff

class MonitorTransport(QWidget):
 """Exactly one row, an explicit context, and atomic owner navigation."""
 def __init__(self,w):
  super().__init__();self.w=w;self.target='program';self.setObjectName('project-preview-transport');self.setFixedHeight(38);line=QHBoxLayout(self);line.setContentsMargins(2,3,2,3);line.setSpacing(2)
  self.context=QComboBox();self.context.addItems(['Program','Source']);self.context.setAccessibleName('Active monitor');self.context.setToolTip('Explicit transport target; Source inspection never seeks the sequence');self.context.setMaximumWidth(90);self.context.currentIndexChanged.connect(lambda i:self.set_target('source' if i else 'program'));line.addWidget(self.context)
  self.buttons={};self.actions_=[]
  for name,label,action,value in [('in','Set In [ / I','range_in',None),('beginning','Go to beginning (Home) — pause at frame 0','beginning',None),('previous','Previous frame — pause','step',-1),('play','Play/Pause (Space)','toggle',None),('next','Next frame — pause','step',1),('last','Go to end (End) — pause at last valid frame','last',None),('out','Set exclusive Out ] / O','range_out',None)]:
   b=tool_button(name,label,lambda checked=False,op=action,val=value:self.w.shell.safe(lambda:self.command(op,val)),self);line.addWidget(b);self.buttons[name]=b;self.actions_.append(b)
  self.time=QLineEdit();self.time.edit_context=None;self.time.textEdited.connect(lambda:self.pin_timecode());self.time.setAccessibleName('Monitor current timecode non-drop');self.time.setMaximumWidth(123);self.time.editingFinished.connect(lambda:self.w.shell.safe(self.seek_timecode));line.addWidget(self.time)
  self.total=QLabel();self.total.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);self.total.setMinimumWidth(0);line.addWidget(self.total,1)
  self.loop_action=tool_button('loop','Loop [In, Out)',lambda checked:self.w.shell.safe(lambda:self.command('loop',int(checked))),self,True);line.addWidget(self.loop_action)
  self.fit=QLabel('Fit');self.fit.setToolTip('Aspect-fit monitor; authored source/output resolution is unchanged.');line.addWidget(self.fit)
  self.full=tool_button('fullscreen','Program full screen (F11); Escape returns',lambda:self.w.video_panels.fullscreen(),self);line.addWidget(self.full)
  self.more=tool_button('more','Monitor options',None,self);menu=QMenu(self.more);self.more.setMenu(menu);self.more.setPopupMode(QToolButton.InstantPopup)
  for label,op,which in [('Go to In','seek','in'),('Go to exclusive Out','seek','out'),('Clear In/Out','range_clear',None),('Release playback ownership','release',None)]:menu.addAction(label,lambda checked=False,op=op,which=which:self.w.shell.safe(lambda:self.command(op,self.clock().get('range_'+which,0) if which else None)))
  line.addWidget(self.more)
 def set_target(self,target):
  self.target=target;self.context.blockSignals(True);self.context.setCurrentIndex(int(target=='source'));self.context.blockSignals(False);self.refresh()
 def clock(self):return self.w.source_transport_state() if self.target=='source' else self.w.transport_state()
 def document(self):return self.w.state().get('source',{}).get('document') if self.target=='source' else self.w.state().get('document')
 def command(self,action,value=None):
  clock=self.clock()
  if action=='toggle':action='pause' if clock.get('playing') else 'play'
  if action in ('range_in','range_out'):value=clock.get('frame',0)
  self.w.transport(action,value,target=self.target)
 def step(self,delta):self.command('step',delta)
 def pin_timecode(self):
  if self.time.edit_context is None:
   from video_project import duration
   d=self.document();self.time.edit_context=dict(target=self.target,epoch=self.clock().get('epoch'),binding=self.w.binding(),fps=list(d['settings']['fps']) if d else None,end=duration(d) if d else 0)
 def seek_timecode(self):
  if not self.time.isModified():return
  self.pin_timecode();intent=self.time.edit_context;target=intent['target'];epoch=intent['epoch'];current=self.w.binding()
  if target!=self.target or any(intent['binding'].get(k)!=current.get(k) for k in ('expected_project','expected_epoch','expected_revision')) or target=='source' and epoch!=self.w.source_transport_state().get('epoch'):
   self.time.edit_context=None;raise ValueError('Monitor context changed; typed timecode retained, nothing submitted. Re-edit or press Enter deliberately to apply it to the current context.')
  if not intent['fps']:return
  value=timecode_frame(self.time.text(),intent['fps'])
  if value>max(0,intent['end']-1):raise ValueError('Timecode is beyond the final valid frame.')
  self.w.transport('seek_paused',value,target=target,source_epoch=epoch if target=='source' else None,binding=intent['binding']);self.time.setModified(False);self.time.edit_context=None
 def refresh(self):
  d=self.document();clock=self.clock();fps=d['settings']['fps'] if d else [30,1];playing=clock.get('playing',False);screen=QApplication.primaryScreen();icon_state=(playing,self.target,screen.devicePixelRatio() if screen else 1.)
  if icon_state!=getattr(self,'icon_state',None):self.icon_state=icon_state;self.buttons['play'].setIcon(editor_icon('pause' if playing else 'play'));self.buttons['play'].setAccessibleName(('Pause' if playing else 'Play')+' '+self.target.title())
  for b in self.buttons.values():b.setEnabled(bool(d))
  self.buttons['play'].setEnabled(bool(d and clock.get('end',0)));self.loop_action.setEnabled(bool(d and clock.get('end',0)));self.loop_action.blockSignals(True);self.loop_action.setChecked(clock.get('loop',False));self.loop_action.blockSignals(False);self.time.setEnabled(bool(d));self.more.setEnabled(bool(d))
  if not self.time.hasFocus() and not self.time.isModified():self.time.setText(timecode(clock.get('frame',0),fps))
  self.total.setText('/ '+timecode(clock.get('end',0),fps)+' NDF');self.total.setToolTip('Exclusive duration; exact '+str(fps[0])+'/'+str(fps[1])+' FPS; non-drop timecode')
  self.time.setToolTip(self.target.title()+' • frame '+str(clock.get('frame',0))+' • NDF '+str(fps[0])+'/'+str(fps[1])+' FPS; [In, Out) '+str(clock.get('range_in',0))+'–'+str(clock.get('range_out',0)))
