"""Direct transform gesture over the existing Program compositor/model."""
from copy import deepcopy
import math
from PySide6.QtCore import Qt,QPointF,QRectF,QEvent
from PySide6.QtGui import QPainter,QPen,QColor,QPolygonF
from PySide6.QtWidgets import QWidget,QApplication
from project_visual import evaluated_layout,text_layout

class TransformHandles(QWidget):
 def __init__(self,preview):
  super().__init__(preview);self.preview=preview;self.w=preview.workspace;self.gesture=None;self.draft=None;self.setAttribute(Qt.WA_TranslucentBackground);self.setAttribute(Qt.WA_NoSystemBackground);self.setMouseTracking(True);self.setAccessibleName('Selected clip transform handles; drag move/corners/rotation; Escape cancels');QApplication.instance().installEventFilter(self)
 def current(self):
  c=self.w.timeline.canvas
  if len(c.selection)!=1 or c.selected is None or c.selected[0] not in ('clips','captions','graphics') or self.w.pending or self.w.transport_state().get('playing'):return None
  row=next((r for r in (self.w.state().get('document') or {}).get(c.selected[0],[]) if r['id'] in c.selection),None)
  if row is None:return None
  track=next(t for t in self.w.document()['tracks'] if t['id']==row['track']);frame=self.w.transport_state().get('frame',0)
  if track['kind']=='audio' or track.get('locked') or not row['start']<=frame<row['start']+row['duration'] or not self.preview.valid_presented() or self.preview.presented[-1]!=frame:return None
  return row if c.selected[0]=='clips' else dict(row,layout=text_layout(row))
 def canvas_rect(self):
  settings=self.w.document()['settings'];ratio=min(self.width()/settings['width'],self.height()/settings['height']);width=settings['width']*ratio;height=settings['height']*ratio;return QRectF((self.width()-width)/2,(self.height()-height)/2,width,height)
 def geometry_for(self,layout):
  canvas=self.canvas_rect();x,y,width,height=layout['bounds'];center=QPointF(canvas.x()+(x+width/2)*canvas.width(),canvas.y()+(y+height/2)*canvas.height());angle=math.radians(layout['rotation']);u=QPointF(math.cos(angle)*width*canvas.width()/2,math.sin(angle)*width*canvas.width()/2);v=QPointF(-math.sin(angle)*height*canvas.height()/2,math.cos(angle)*height*canvas.height()/2);corners=[center-u-v,center+u-v,center+u+v,center-u+v];direction=QPointF(-math.sin(angle)*23,math.cos(angle)*23);knob=center-v-direction
  # A full-frame picture reaches the viewport edge. Keep rotation reachable
  # inside that edge rather than clipping the only rotation affordance away.
  visible=QRectF(self.rect()).adjusted(8,8,-8,-8)
  if not visible.contains(knob):
   below=center+v+direction;knob=below if visible.contains(below) else center-v+direction
  knob=QPointF(max(8,min(self.width()-8,knob.x())),max(8,min(self.height()-8,knob.y())));return center,corners,knob
 def refresh(self):
  self.setGeometry(self.preview.view.geometry())
  if self.gesture is not None and not self.valid_gesture():self.cancel('Transform draft cancelled after context, selection or frame changed.')
  # A transparent full-monitor child still makes Qt compose and repaint it.
  # No handles apply during playback or without a valid selected paused item.
  if self.current() is None:
   if not self.isHidden():self.hide()
   return
  if self.isHidden():self.show();self.raise_()
  stamp=(self.w.state().get('epoch'),self.w.state().get('revision'),self.w.transport_state().get('frame'),tuple(sorted(self.w.timeline.canvas.selection)),self.width(),self.height(),repr(self.draft))
  if stamp!=getattr(self,'paint_stamp',None):self.paint_stamp=stamp;self.update()
 def valid_gesture(self):
  g=self.gesture
  if g is None:return False
  current=self.w.binding();return not self.w.pending and not self.w.transport_state().get('playing') and self.w.transport_state().get('frame',0)==g['frame'] and tuple(sorted(self.w.timeline.canvas.selection))==g['ids'] and [self.width(),self.height()]==g['size'] and all(current.get(k)==g['binding'].get(k) for k in ('expected_epoch','expected_revision','expected_project'))
 def hit(self,point,layout):
  center,corners,knob=self.geometry_for(layout)
  if (point-knob).manhattanLength()<13:return ('rotation',None)
  for index,corner in enumerate(corners):
   if (point-corner).manhattanLength()<14:return ('corner',index)
  if QPolygonF(corners).containsPoint(point,Qt.OddEvenFill):return ('move',None)
  return None
 def paintEvent(self,event):
  row=self.current() if self.gesture is None else self.gesture['row']
  if row is None:return
  layout=self.draft or evaluated_layout(row,self.w.transport_state().get('frame',0));center,corners,knob=self.geometry_for(layout);p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(QColor('#f5bc73' if self.gesture else '#9bdae0'),1.4,Qt.DashLine if self.gesture else Qt.SolidLine));p.setBrush(Qt.NoBrush);p.drawPolygon(QPolygonF(corners));edges=[(corners[0]+corners[1])/2,(corners[2]+corners[3])/2];p.drawLine(min(edges,key=lambda point:(point-knob).manhattanLength()),knob);p.setBrush(QColor('#15242c'))
  for point in corners:p.drawRect(QRectF(point.x()-4,point.y()-4,8,8))
  p.drawEllipse(knob,5,5)
  if self.gesture:p.fillRect(QRectF(8,8,270,25),QColor('#e019242d'));p.drawText(QRectF(14,8,260,25),Qt.AlignVCenter,'Transform preview • not accepted')
  p.end()
 def mousePressEvent(self,event):
  self.preview.view.setFocus(Qt.MouseFocusReason);row=self.current()
  if event.button()!=Qt.LeftButton or row is None:event.ignore();return
  layout=evaluated_layout(row,self.w.transport_state().get('frame',0));hit=self.hit(event.position(),layout)
  if hit is None:event.ignore();return
  center,corners,knob=self.geometry_for(layout);self.gesture=dict(row=deepcopy(row),category=self.w.timeline.canvas.selected[0],binding=self.w.binding(),ids=tuple(sorted(self.w.timeline.canvas.selection)),frame=self.w.transport_state().get('frame',0),size=[self.width(),self.height()],layout=layout,press=event.position(),kind=hit[0],corner=hit[1],center=center,corners=corners,knob=knob);self.draft=deepcopy(layout);self.grabMouse();event.accept();self.update()
 def mouseMoveEvent(self,event):
  if self.gesture is None:
   row=self.current();hit=self.hit(event.position(),evaluated_layout(row,self.w.transport_state().get('frame',0))) if row else None;self.setCursor(Qt.SizeAllCursor if hit and hit[0]=='move' else Qt.CrossCursor if hit else Qt.ArrowCursor);event.ignore();return
  if not self.valid_gesture():self.cancel('Transform draft cancelled after target changed.');return
  g=self.gesture;layout=deepcopy(g['layout']);canvas=self.canvas_rect();delta=event.position()-g['press']
  if self.draft==g['layout'] and delta.manhattanLength()<3:event.accept();return
  if g['kind']=='move':layout['bounds'][0]+=delta.x()/canvas.width();layout['bounds'][1]+=delta.y()/canvas.height()
  elif g['kind']=='rotation':
   before=g['press']-g['center'];after=event.position()-g['center'];angle=math.degrees(math.atan2(after.y(),after.x())-math.atan2(before.y(),before.x()));layout['rotation']+=((angle+180)%360)-180
  else:
   index=g['corner'];anchor=g['corners'][(index+2)%4];relative=event.position()-anchor;angle=math.radians(g['layout']['rotation']);local_x=math.cos(angle)*relative.x()+math.sin(angle)*relative.y();local_y=-math.sin(angle)*relative.x()+math.cos(angle)*relative.y();sx=-1 if index in (0,3) else 1;sy=-1 if index in (0,1) else 1;width=max(.001,sx*local_x/canvas.width());height=max(.001,sy*local_y/canvas.height());cx=sx*width*canvas.width()/2;cy=sy*height*canvas.height()/2;center=anchor+QPointF(math.cos(angle)*cx-math.sin(angle)*cy,math.sin(angle)*cx+math.cos(angle)*cy);layout['bounds']=[(center.x()-canvas.x())/canvas.width()-width/2,(center.y()-canvas.y())/canvas.height()-height/2,width,height]
  self.draft=layout;self.preview.transform_preview=(g['row']['id'],deepcopy(layout));self.preview.draw_transform_preview();self.update();event.accept()
 def mouseReleaseEvent(self,event):
  if self.gesture is None:event.ignore();return
  valid=self.valid_gesture();g=self.gesture;draft=self.draft;self.gesture=None;self.draft=None;self.releaseMouse();self.preview.transform_preview=None;self.preview.draw_transform_preview();self.update()
  if not valid:self.w.notice.setText('Transform cancelled after context changed; nothing submitted.');event.accept();return
  if draft==g['layout']:event.accept();return
  row=g['row'];changes=[];base={};animated={k['parameter']:k for k in row['layout'].get('keys',[])};local=g['frame']-row['start']+row.get('visual_window',dict(offset=0))['offset']
  for name,value in [('bounds.'+str(i),v) for i,v in enumerate(draft['bounds'])]+[('rotation',draft['rotation'])]:
   old=g['layout']['bounds'][int(name[-1])] if name.startswith('bounds.') else g['layout']['rotation']
   if abs(value-old)<1e-10:continue
   if name in animated:changes.append(dict(op='keyframe.set',id=row['id'],parameter=name,frame=local,value=value,interpolation=next((p[2] for p in animated[name]['points'] if p[0]==local),'Linear')))
   elif name.startswith('bounds.'):base.setdefault('bounds',list(row['layout']['bounds']))[int(name[-1])]=value
   else:base[name]=value
  if base:changes.insert(0,dict(op='clip.layout' if g['category']=='clips' else 'caption.edit' if g['category']=='captions' else 'graphic.edit',id=row['id'],values=base if g['category']=='clips' else dict(style=base)))
  if not changes:event.accept();return
  binding=dict(g['binding']);binding['expected_command']=self.w.binding().get('expected_command');self.w.shell.safe(lambda:self.w.batch('Transform clip',changes,binding));event.accept()
 def cancel(self,message='Transform preview cancelled; nothing accepted.'):
  if self.gesture is None:return
  self.gesture=None;self.draft=None;self.releaseMouse();self.preview.transform_preview=None
  if not self.preview.closed:self.preview.draw_transform_preview()
  self.w.notice.setText(message);self.update()
 def eventFilter(self,obj,event):
  if self.gesture is not None:
   if event.type()==QEvent.KeyPress and event.key()==Qt.Key_Escape:self.cancel();return True
   if event.type()==QEvent.WindowDeactivate or obj is self.preview.view and event.type() in (QEvent.Hide,QEvent.FocusOut):self.cancel('Transform cancelled after focus/visibility changed.')
  return False
 def close_resources(self):self.cancel();QApplication.instance().removeEventFilter(self)
