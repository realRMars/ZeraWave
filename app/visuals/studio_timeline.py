"""Frame-precise Qt timeline. Gestures submit one owner transaction on release."""
from copy import deepcopy
from fractions import Fraction
import math
from PySide6.QtCore import Qt,QRectF,QPoint,QSize,QEvent
from PySide6.QtGui import QPainter,QColor,QPen
from PySide6.QtWidgets import QWidget,QScrollArea,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QSpinBox,QCheckBox
from video_project import duration,rational

class Timeline(QWidget):
 label_width=135;row_height=46;ruler_height=30
 def __init__(self,workspace):
  super().__init__();self.workspace=workspace;self.scale=3.;self.document=None;self.version=None;self.selected=None;self.gesture=None;self.frame=0;self.snap=True;self.rects={};self.setFocusPolicy(Qt.StrongFocus);self.setMouseTracking(True);self.setAccessibleName('Video timeline')
 def cancel_gesture(self,message=''):
  had=self.gesture is not None;self.gesture=None
  if QWidget.mouseGrabber() is self:self.releaseMouse()
  if had and message:self.workspace.notice.setText(message)
  self.update()
 def event(self,event):
  if hasattr(self,'gesture') and event.type() in (QEvent.Hide,QEvent.WindowDeactivate,QEvent.UngrabMouse,QEvent.Close,QEvent.DeferredDelete,QEvent.ParentChange,QEvent.FocusOut):self.cancel_gesture()
  return super().event(event)
 def set_document(self,document,version):
  if version==self.version:return
  self.version=version;self.document=deepcopy(document);self.tracks=sorted(document['tracks'],key=lambda r:r['order']) if document else [];self.end=duration(document) if document else 0
  if self.gesture and self.gesture['binding']!=self.workspace.binding():self.cancel_gesture('Timeline changed during gesture; no gesture edit submitted. Select and drag again.')
  self.resize_canvas()
 def resize_canvas(self):
  if self.end*self.scale>2000000:self.scale=2000000/max(1,self.end)
  self.resize(max(800,math.ceil(self.end*self.scale)+self.label_width+120),self.ruler_height+max(1,len(getattr(self,'tracks',[])))*self.row_height+20);self.update()
 def x(self,frame):return self.label_width+frame*self.scale
 def at(self,x):return max(0,int(math.floor((x-self.label_width)/self.scale+.5)))
 def hit(self,pos):
  for (category,key),rect in reversed(list(self.rects.items())):
   if rect.contains(pos):return category,key,rect
  return None
 def rows(self):
  if not self.document:return []
  return [(category,r) for category in ('clips','captions','graphics') for r in self.document[category]]
 def select(self,category,key):
  self.selected=(category,key)
  tree=self.workspace.trees.get(category)
  if tree:
   for i in range(tree.topLevelItemCount()):
    if tree.topLevelItem(i).data(0,Qt.UserRole)==key:tree.setCurrentItem(tree.topLevelItem(i));break
  self.update()
 def paintEvent(self,event):
  p=QPainter(self);p.fillRect(event.rect(),QColor('#101920'));self.rects={};left=max(0,self.at(event.rect().left()));right=self.at(event.rect().right())
  fps=rational(self.document['settings']['fps']) if self.document else Fraction(30);step=1
  while step*self.scale<65:step*=2
  p.setPen(QColor('#8196a2'))
  for f in range(left//step*step,right+step,step):
   x=self.x(f);p.drawLine(QPoint(round(x),0),QPoint(round(x),self.height()));p.drawText(QRectF(x+3,1,110,24),str(f)+'f')
  tracks={r['id']:i for i,r in enumerate(getattr(self,'tracks',[]))}
  for i,t in enumerate(getattr(self,'tracks',[])):
   y=self.ruler_height+i*self.row_height;p.fillRect(QRectF(0,y,self.label_width,self.row_height),QColor('#1d2a32'));p.setPen(QColor('#d6e2e8'));p.drawText(QRectF(6,y+3,self.label_width-12,self.row_height-6),Qt.AlignVCenter|Qt.TextWordWrap,t['name']+' • '+t['kind']);p.setPen(QColor('#293943'));p.drawLine(0,y+self.row_height,self.width(),y+self.row_height)
  for category,row in self.rows():
   display=row
   if self.gesture and self.gesture['key']==row['id']:display=self.gesture['preview']
   y=self.ruler_height+tracks[display['track']]*self.row_height+5;rect=QRectF(self.x(display['start']),y,max(2,display['duration']*self.scale),self.row_height-10);self.rects[(category,row['id'])]=rect
   if not rect.intersects(QRectF(event.rect())):continue
   color='#315577' if category=='clips' else '#725333'
   if category=='clips' and next(t for t in self.tracks if t['id']==row['track'])['kind']=='audio':color='#30634f'
   p.fillRect(rect,QColor(color));p.setPen(QPen(QColor('#a4d7e8' if self.selected==(category,row['id']) else '#658390'),2));p.drawRect(rect);p.fillRect(QRectF(rect.left(),rect.top(),min(6,rect.width()/3),rect.height()),QColor('#8db2bc'));p.fillRect(QRectF(rect.right()-min(6,rect.width()/3),rect.top(),min(6,rect.width()/3),rect.height()),QColor('#8db2bc'));p.setClipRect(rect.adjusted(7,0,-7,0));p.setPen(QColor('#ffffff'));p.drawText(rect.adjusted(9,2,-9,-2),Qt.AlignVCenter,row.get('name',row.get('text','')));p.setClipping(False)
  p.setPen(QPen(QColor('#ffc35a'),2));p.drawLine(round(self.x(self.frame)),0,round(self.x(self.frame)),self.height());p.end()
 def mousePressEvent(self,e):
  if e.button()!=Qt.LeftButton:return
  self.setFocus();pos=e.position();hit=self.hit(pos)
  if pos.y()<self.ruler_height or not hit:
   self.workspace.transport('seek',min(self.end,self.at(pos.x())));return
  category,key,rect=hit;self.select(category,key)
  if self.workspace.pending:return
  row=next(r for c,r in self.rows() if c==category and r['id']==key);edge=min(8,rect.width()/3);mode='left' if pos.x()-rect.left()<edge else 'right' if rect.right()-pos.x()<edge else 'move'
  self.gesture=dict(category=category,key=key,original=deepcopy(row),preview=deepcopy(row),binding=self.workspace.binding(),mode=mode,origin=self.at(pos.x()));self.grabMouse()
 def snapped(self,frame,row,e):
  if not self.snap or e.modifiers()&Qt.AltModifier:return frame
  edges={0}
  for category,r in self.rows():
   if r['id']!=row['id']:edges.update((r['start'],r['start']+r['duration']))
  closest=min(edges,key=lambda f:abs(f-frame));return closest if abs(closest-frame)*self.scale<=8 else frame
 def mouseMoveEvent(self,e):
  g=self.gesture
  if not g:return
  row=g['original'];delta=self.at(e.position().x())-g['origin'];preview=deepcopy(row)
  if g['mode']=='move':
   preview['start']=self.snapped(max(0,row['start']+delta),row,e);index=int((e.position().y()-self.ruler_height)//self.row_height)
   if g['category']=='clips' and 0<=index<len(self.tracks):
    source=next(t for t in self.tracks if t['id']==row['track']);target=self.tracks[index]
    if target['kind']==source['kind']:preview['track']=target['id']
  elif g['mode']=='left':
   start=self.snapped(max(0,min(row['start']+row['duration']-1,row['start']+delta)),row,e);preview.update(start=start,duration=row['start']+row['duration']-start)
  else:preview['duration']=max(1,self.snapped(row['start']+row['duration']+delta,row,e)-row['start'])
  g['preview']=preview;self.update()
 def mouseReleaseEvent(self,e):
  if e.button()!=Qt.LeftButton:return
  if not self.gesture:
   if QWidget.mouseGrabber() is self:self.releaseMouse()
   return
  g=self.gesture;self.gesture=None;self.releaseMouse();self.update();row=g['original'];preview=g['preview']
  if preview==row:return
  if g['category']=='clips':
   change=dict(op='clip.move',id=row['id'],start=preview['start'],track=preview['track']) if g['mode']=='move' else dict(op='clip.trim',id=row['id'],start=preview['start'],end=preview['start']+preview['duration'])
  else:change=dict(op='caption.edit' if g['category']=='captions' else 'graphic.edit',id=row['id'],values=dict(start=preview['start'],duration=preview['duration']))
  self.workspace.shell.safe(lambda:self.workspace.batch(('Move ' if g['mode']=='move' else 'Trim ')+row.get('name','text'),[change],g['binding']))
 def keyPressEvent(self,e):
  if e.key()==Qt.Key_Escape and self.gesture:self.cancel_gesture();return
  if e.key()==Qt.Key_Space:self.workspace.transport('pause' if self.workspace.transport_state().get('playing') else 'play');return
  if e.key() in (Qt.Key_Left,Qt.Key_Right):self.workspace.transport('seek',max(0,min(self.end,self.frame+(-1 if e.key()==Qt.Key_Left else 1))));return
  if e.key() in (Qt.Key_Delete,Qt.Key_S) and self.selected and not self.workspace.pending:
   category,key=self.selected
   if e.key()==Qt.Key_Delete:change=dict(op={'clips':'clip.remove','captions':'caption.remove','graphics':'graphic.remove'}[category],id=key)
   elif category=='clips':change=dict(op='clip.split',id=key,at=self.frame)
   else:return
   self.workspace.shell.safe(lambda:self.workspace.batch('Remove timeline item' if e.key()==Qt.Key_Delete else 'Split at playhead',[change]));return
  super().keyPressEvent(e)
 def wheelEvent(self,e):
  if e.modifiers()&Qt.ControlModifier:
   self.scale=max(.002,min(24.,self.scale*(1.25 if e.angleDelta().y()>0 else .8)));self.resize_canvas();e.accept()
  else:e.ignore()

class TimelinePanel(QWidget):
 def __init__(self,workspace):
  super().__init__();self.workspace=workspace;self.setMinimumHeight(220);layout=QVBoxLayout(self);row=QHBoxLayout();layout.addLayout(row)
  for label,fn in [('Play',lambda:workspace.transport('play')),('Pause',lambda:workspace.transport('pause')),('Stop / legacy clocks',lambda:workspace.transport('stop'))]:
   b=QPushButton(label);b.setAccessibleName(label);b.clicked.connect(lambda checked=False,fn=fn:workspace.shell.safe(fn));row.addWidget(b)
  self.position=QSpinBox();self.position.setAccessibleName('Timeline frame');self.position.setRange(0,0);self.position.editingFinished.connect(lambda:workspace.transport('seek',self.position.value()));row.addWidget(self.position);self.time=QLabel('0f');row.addWidget(self.time)
  self.canvas=Timeline(workspace);snap=QCheckBox('Snap edges');self.snap_control=snap;snap.setChecked(True);snap.toggled.connect(lambda v:setattr(self.canvas,'snap',v));row.addWidget(snap)
  for label,factor in [('Zoom +',1.25),('Zoom −',.8)]:
   b=QPushButton(label);b.clicked.connect(lambda checked=False,factor=factor:self.zoom(factor));row.addWidget(b)
  self.scroll=QScrollArea();self.scroll.setMinimumHeight(155);self.scroll.setWidget(self.canvas);layout.addWidget(self.scroll,1)
 def zoom(self,factor):self.canvas.scale=max(.002,min(24.,self.canvas.scale*factor));self.canvas.resize_canvas()
 def refresh(self):
  s=self.workspace.state();d=s.get('document');t=self.workspace.transport_state();self.canvas.set_document(d,(s.get('epoch'),s.get('revision')));self.canvas.frame=t.get('frame',0);self.canvas.update();self.position.setRange(0,t.get('end',0))
  if not self.position.hasFocus():self.position.setValue(t.get('frame',0))
  fps=rational(d['settings']['fps']) if d else Fraction(30);seconds=Fraction(t.get('frame',0))/fps;self.time.setText(str(t.get('frame',0))+'f • '+f'{float(seconds):.3f}s'+(' • Playing' if t.get('playing') else ''))
  audio=self.workspace.client.snapshot.get('audio_hub',{}).get('project_audio',{});pending=audio.get('transition_pending');status='Applying audio transition' if pending else audio.get('status','');self.time.setToolTip(t.get('clock','')+'; '+status+'; audible device position unavailable')
