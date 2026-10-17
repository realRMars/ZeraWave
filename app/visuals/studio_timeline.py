"""Qt authoring surfaces; each completed edit submits one shared owner command."""
from copy import deepcopy
from fractions import Fraction
import math,json,time,uuid
from PySide6.QtCore import Qt,QRectF,QPoint,QEvent,QMimeData,QSize
from PySide6.QtGui import QPainter,QColor,QPen,QDrag,QActionGroup,QAction
from PySide6.QtWidgets import (QWidget,QScrollArea,QVBoxLayout,QHBoxLayout,QLabel,QSpinBox,
 QCheckBox,QToolBar,QComboBox,QApplication,QMenu,QLineEdit,QToolButton,QMessageBox,QSlider,QSizePolicy)
from video_project import duration,rational
from project_edits import entries,selected as expanded_selection

CLIPBOARD='application/x-zerawave-timeline'
TRACK_MIME='application/x-zerawave-project-track'

class Timeline(QWidget):
    label_width=0;row_height=64;ruler_height=28
    def __init__(self,workspace):
        super().__init__();self.workspace=workspace;self.document=None;self.version=None;self.tracks=[];self.end=0;self.scale=3.;self.selected=None;self.selection=set();self.anchor=None;self.current_track=None;self.gesture=None;self.pending_preview=None;self.selection_request=None;self.frame=0;self.snap=True;self.linked=True;self.tool='Select';self.mode='Normal';self.rects={};self.rows_by_id={};self.track_rows={};self.drop_preview=None;self.feedback_samples=[]
        self.setFocusPolicy(Qt.StrongFocus);self.setMouseTracking(True);self.setAcceptDrops(True);self.setAccessibleName('Video timeline')
    def notify(self,text):self.workspace.notice.setText(text);self.workspace.shell.statusBar().showMessage(text)
    def perform(self,label,changes,binding=None,preview=None):
        try:
            if binding is None:
                state=self.workspace.state()
                if self.version!=(state.get('epoch'),state.get('revision')):
                    self.workspace.timeline.refresh();self.notify('Timeline changed before this action. Review the refreshed selection and repeat explicitly; no edit submitted.');return
                binding=self.workspace.binding(state)
            key=self.workspace.batch(label,changes,binding);self.pending_preview=preview
            if any(change['op'] in ('items.paste','items.place','items.split') for change in changes):self.selection_request=(key,any(change['op']=='items.split' for change in changes),set(self.selection))
            self.update();return key
        except Exception as exc:self.pending_preview=None;self.notify(str(exc));self.update()
    def cancel_gesture(self,message=''):
        if self.gesture and self.gesture.get('kind')=='seek' and self.gesture.get('token'):
            cancel=getattr(self.workspace,'cancel_transport_intent',None)
            if cancel:cancel(self.gesture['token'])
        had=self.gesture is not None or self.drop_preview is not None;self.gesture=None;self.drop_preview=None
        if QWidget.mouseGrabber() is self:self.releaseMouse()
        if had and message:self.notify(message)
        self.update()
    def event(self,event):
        if hasattr(self,'gesture') and event.type() in (QEvent.Hide,QEvent.WindowDeactivate,QEvent.UngrabMouse,QEvent.Close,QEvent.DeferredDelete,QEvent.ParentChange,QEvent.FocusOut):self.cancel_gesture()
        return super().event(event)
    def set_document(self,document,version):
        if version==self.version:return
        if self.gesture and self.gesture.get('binding')!=self.workspace.binding():self.cancel_gesture('Project changed during gesture. No gesture edit was submitted.')
        self.version=version;self.document=deepcopy(document);self.tracks=sorted(document['tracks'],key=lambda t:t['order']) if document else [];self.end=duration(document) if document else 0;self.rows_by_id={r['id']:(c,r) for c,r in entries(self.document)} if document else {};self.selection.intersection_update(self.rows_by_id)
        if self.selected and self.selected[1] not in self.rows_by_id:self.selected=None
        if self.selected:self.current_track=self.rows_by_id[self.selected[1]][1]['track']
        elif self.current_track not in {t['id'] for t in self.tracks}:self.current_track=self.tracks[0]['id'] if self.tracks else None
        self.pending_preview=None;self.resize_canvas()
    def rows(self):return list(self.rows_by_id.values())
    def resize_canvas(self):
        self.scale=min(self.scale,2000000/max(1,self.end));self.resize(max(800,math.ceil(self.end*self.scale)+120),self.ruler_height+max(1,len(self.tracks))*self.row_height+20);self.geometry_index();self.update()
    def geometry_index(self):
        tracks={t['id']:i for i,t in enumerate(self.tracks)};self.rects={};self.track_rows={t['id']:[] for t in self.tracks}
        for category,row in self.rows():
            self.rects[(category,row['id'])]=QRectF(self.x(row['start']),self.ruler_height+tracks[row['track']]*self.row_height+5,max(2,row['duration']*self.scale),self.row_height-10);self.track_rows[row['track']].append((category,row))
        for rows in self.track_rows.values():rows.sort(key=lambda entry:(entry[1]['start'],entry[1]['id']))
    def x(self,frame):return self.label_width+frame*self.scale
    def at(self,x):return max(0,int(math.floor((x-self.label_width)/self.scale+.5)))
    def hit(self,pos):
        index=int((pos.y()-self.ruler_height)//self.row_height)
        if not 0<=index<len(self.tracks):return None
        for category,row in reversed(self.track_rows.get(self.tracks[index]['id'],[])):
            rect=self.rects[(category,row['id'])]
            if rect.contains(pos):return category,row['id'],rect
        return None
    def select(self,category,key,modifiers=Qt.NoModifier):
        if key not in self.rows_by_id:return
        if modifiers&Qt.ControlModifier:
            if key in self.selection:self.selection.remove(key)
            else:self.selection.add(key)
        elif modifiers&Qt.ShiftModifier and self.anchor in self.rows_by_id:
            anchor=self.rows_by_id[self.anchor][1];target=self.rows_by_id[key][1]
            if anchor['track']==target['track']:
                rows=[r['id'] for _,r in self.track_rows[target['track']]];a,b=rows.index(self.anchor),rows.index(key);self.selection.update(rows[min(a,b):max(a,b)+1])
            else:self.selection.add(key)
        else:
            if key not in self.selection:self.selection={key}
            self.anchor=key
        self.selected=(category,key) if key in self.selection else next((self.rows_by_id[i][0],i) for i in self.rows_by_id if i in self.selection) if self.selection else None;self.current_track=self.rows_by_id[key][1]['track']
        tree=self.workspace.trees.get(category)
        if tree:
            for i in range(tree.topLevelItemCount()):
                item=tree.topLevelItem(i)
                if item.data(0,Qt.UserRole)==key:tree.setCurrentItem(item);break
        self.update()
        if hasattr(self.workspace,'video_panels'):self.workspace.video_panels.refresh()
    def ids(self):return [i for i in self.rows_by_id if i in self.selection]
    def members(self,ids=None,groups=True):return expanded_selection(self.document,ids or self.ids(),self.linked,groups) if self.document and (ids or self.selection) else []
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(event.rect(),QColor('#101920'));left=self.at(event.rect().left());right=self.at(event.rect().right());fps=rational(self.document['settings']['fps']) if self.document else Fraction(30)
        from studio_video_workspace import clock_text
        tick=Fraction(1,10)
        for candidate in [Fraction(1,10),Fraction(1,4),Fraction(1,2),1,2,5,10,15,30,60,120,300,600,1800,3600]:
            tick=Fraction(candidate)
            if tick*fps*self.scale>=90:break
        p.setPen(QColor('#8196a2'))
        for i in range(int((Fraction(left)/fps)//tick),int((Fraction(right)/fps)//tick)+2):
            value=i*tick*fps;f=(value.numerator*2+value.denominator)//(value.denominator*2);x=self.x(f);p.drawLine(round(x),0,round(x),self.height());p.drawText(QRectF(x+3,1,130,24),clock_text(f,[fps.numerator,fps.denominator])[3:]+(' • '+str(f)+'f' if self.scale>=10 else ''))
        indices={t['id']:i for i,t in enumerate(self.tracks)};preview=(self.gesture or {}).get('preview') or self.pending_preview or {}
        for t in self.tracks:
            y=self.ruler_height+indices[t['id']]*self.row_height
            if y+self.row_height<event.rect().top() or y>event.rect().bottom():continue
            p.setPen(QColor('#293943'));p.drawLine(0,y+self.row_height,self.width(),y+self.row_height)
            for category,row in self.track_rows.get(t['id'],[]):
                rect=self.rects[(category,row['id'])]
                if not rect.intersects(QRectF(event.rect())):continue
                color='#30634f' if t['kind']=='audio' else '#315577' if category=='clips' else '#725333';p.fillRect(rect,QColor(color));p.setPen(QPen(QColor('#ffc35a' if row['id'] in self.selection else '#658390'),2));p.drawRect(rect)
                p.fillRect(QRectF(rect.left(),rect.top(),min(7,rect.width()/3),rect.height()),QColor('#8db2bc'));p.fillRect(QRectF(rect.right()-min(7,rect.width()/3),rect.top(),min(7,rect.width()/3),rect.height()),QColor('#8db2bc'))
                p.save();p.setClipRect(rect.adjusted(8,1,-8,-1));p.setPen(QColor('#ffffff'));p.drawText(rect.adjusted(9,2,-9,-2),Qt.AlignTop,row.get('name',row.get('text',''))+('  🔗' if row.get('link_id') else '')+('  Group' if row.get('group_id') else ''))
                cache=getattr(self.workspace.timeline,'decorations',None)
                if cache and rect.width()>48 and category=='clips':cache.draw(p,rect,row,self.document)
                p.restore()
        for key,row in preview.items():
            if row['track'] not in indices:continue
            rect=QRectF(self.x(row['start']),self.ruler_height+indices[row['track']]*self.row_height+5,max(2,row['duration']*self.scale),self.row_height-10);p.fillRect(rect,QColor(245,184,78,65));p.setPen(QPen(QColor('#ff665b' if (self.gesture or {}).get('error') else '#ffd186'),2,Qt.DashLine));p.drawRect(rect)
        if self.gesture and self.gesture.get('kind')=='marquee' and self.gesture.get('active'):
            p.setPen(QPen(QColor('#a4d7e8'),1,Qt.DashLine));p.drawRect(QRectF(self.gesture['press'],self.gesture['last']).normalized())
        if self.drop_preview:
            g=self.drop_preview;y=self.ruler_height+indices.get(g.get('track'),0)*self.row_height;p.setPen(QPen(QColor('#ffc35a'),2,Qt.DashLine));p.drawRect(QRectF(self.x(g['frame']),y,max(20,g.get('duration',30)*self.scale),self.row_height));p.drawText(QRectF(self.x(g['frame'])+4,y+18,360,30),g.get('label','Media placement'))
        p.setPen(QPen(QColor('#ffc35a'),2));p.drawLine(round(self.x(self.frame)),0,round(self.x(self.frame)),self.height());p.end()
    def mousePressEvent(self,e):
        if not self.document:return
        if e.button()==Qt.RightButton:self.context(e.position().toPoint());return
        if e.button() not in (Qt.LeftButton,Qt.MiddleButton):return
        if self.version!=(self.workspace.state().get('epoch'),self.workspace.state().get('revision')):
            self.workspace.timeline.refresh();self.notify('Timeline updated from the owner. Click again on the refreshed item; no edit started.');return
        self.setFocus();pos=e.position();binding=self.workspace.binding();hit=self.hit(pos)
        if e.button()==Qt.MiddleButton:self.gesture=dict(kind='pan',press=pos,binding=binding,scroll=self.workspace.timeline.scroll.horizontalScrollBar().value());self.grabMouse();return
        if pos.y()<self.ruler_height:
            frame=min(self.end,self.at(pos.x()));self.gesture=dict(kind='seek',binding=binding,token=uuid.uuid4().hex,last_frame=frame);self.workspace.transport('seek',frame,binding=binding,gesture_token=self.gesture['token']);self.grabMouse();return
        if not hit:
            index=int((pos.y()-self.ruler_height)//self.row_height)
            if 0<=index<len(self.tracks):self.current_track=self.tracks[index]['id']
            if not e.modifiers()&Qt.ControlModifier:self.selection.clear();self.selected=None
            self.workspace.transport('seek',min(self.end,self.at(pos.x())));self.gesture=dict(kind='marquee',press=pos,last=pos,active=False,initial=set(self.selection),binding=binding);self.grabMouse();self.update();return
        category,key,rect=hit;self.select(category,key,e.modifiers())
        if self.tool=='Razor':self.split(self.at(pos.x()),[key]);return
        if self.workspace.pending or getattr(self.workspace.timeline,'placement',None):self.notify('Waiting for the preceding operation. Selection changed; no edit gesture started.');return
        if e.modifiers()&(Qt.ControlModifier|Qt.ShiftModifier):return
        row=self.rows_by_id[key][1];edge=min(8,rect.width()/3);mode='left' if pos.x()-rect.left()<edge else 'right' if rect.right()-pos.x()<edge else 'move';rows=self.members([key],False) if mode!='move' else self.members();selected_ids={r['id'] for _,r in rows};edges={0,self.frame}
        for _,r in self.rows():
            if r['id'] not in selected_ids:edges.update((r['start'],r['start']+r['duration']))
        collision={t['id']:[] for t in self.tracks}
        for category,other in self.rows():
            if category=='clips' and other['id'] not in selected_ids:collision[other['track']].append(other)
        self.gesture=dict(kind='edit',mode=mode,key=key,rows=rows,original=row,press=pos,origin=self.at(pos.x()),active=False,binding=binding,edges=edges,collision=collision,preview={},error='',started=time.perf_counter());self.grabMouse()
    def snapped(self,frame,g,e):
        if not self.snap or e.modifiers()&Qt.AltModifier:return frame
        closest=min(g['edges'],key=lambda f:abs(f-frame));return closest if abs(closest-frame)*self.scale<=8 else frame
    def mouseMoveEvent(self,e):
        began=time.perf_counter();g=self.gesture;pos=e.position()
        if not g:
            hit=self.hit(pos);edge=False
            if hit:edge=min(pos.x()-hit[2].left(),hit[2].right()-pos.x())<min(8,hit[2].width()/3)
            self.setCursor(Qt.CrossCursor if self.tool=='Razor' else Qt.SizeHorCursor if edge else Qt.OpenHandCursor if hit else Qt.ArrowCursor);return
        if g['kind']=='seek':
            frame=min(self.end,self.at(pos.x()))
            if frame!=g['last_frame']:g['last_frame']=frame;self.workspace.transport('seek',frame,binding=g['binding'],gesture_token=g['token'])
            return
        if g['kind']=='pan':self.workspace.timeline.scroll.horizontalScrollBar().setValue(g['scroll']+round(g['press'].x()-pos.x()));return
        if not g.get('active') and (pos-g['press']).manhattanLength()<QApplication.startDragDistance():return
        g['active']=True
        if g['kind']=='marquee':
            g['last']=pos;rect=QRectF(g['press'],pos).normalized();self.selection=g['initial']|{key for (cat,key),r in self.rects.items() if rect.intersects(r)};self.selected=next(((self.rows_by_id[i][0],i) for i in self.rows_by_id if i in self.selection),None);self.update();return
        primary=g['original'];delta=self.at(pos.x())-g['origin'];g['error']='';mapping={};previews={};tracks={t['id']:t for t in self.tracks}
        if g['mode']=='move':
            delta=self.snapped(max(0,primary['start']+delta),g,e)-primary['start'];index=int((pos.y()-self.ruler_height)//self.row_height);source=tracks[primary['track']]
            if not 0<=index<len(self.tracks) or self.tracks[index]['kind']!=source['kind']:g['error']='Choose a destination track of the same type.'
            else:
                kinds={kind:[t['id'] for t in self.tracks if t['kind']==kind] for kind in ('video','audio','graphics')};vertical=kinds[source['kind']].index(self.tracks[index]['id'])-kinds[source['kind']].index(source['id'])
                for _,row in g['rows']:
                    choices=kinds[tracks[row['track']]['kind']];target=choices.index(row['track'])+vertical
                    if not 0<=target<len(choices):g['error']='A selected/linked companion has no compatible destination track.';continue
                    mapping[row['id']]=choices[target]
            for _,row in g['rows']:previews[row['id']]=dict(row,start=row['start']+delta,track=mapping.get(row['id'],row['track']))
            change=dict(op='items.move',ids=self.ids(),delta=delta,track_map=mapping,linked=self.linked,groups=True,mode=self.mode)
        else:
            start=primary['start'];end=start+primary['duration']
            if g['mode']=='left':start=self.snapped(max(0,min(end-1,start+delta)),g,e)
            else:end=max(start+1,self.snapped(end+delta,g,e))
            left=start-primary['start'];right=end-(primary['start']+primary['duration'])
            for _,row in g['rows']:previews[row['id']]=dict(row,start=row['start']+left,duration=row['duration']+right-left)
            change=dict(op='items.trim',id=g['key'],start=start,end=end,linked=self.linked)
        if any(r['start']<0 or r['duration']<1 for r in previews.values()):g['error']='Every item must stay at or after zero and contain at least one frame.'
        if any(tracks[r['track']].get('locked',False) for _,r in g['rows']) or any(tracks[r['track']].get('locked',False) for r in previews.values()):g['error']='A selected/linked source or target track is locked.'
        fps=rational(self.document['settings']['fps']);assets={a['id']:a for a in self.document['media']}
        if g['mode']!='move':
            for category,original in g['rows']:
                if category!='clips':continue
                proposed=previews[original['id']];source=rational(original['source_in'])+Fraction(proposed['start']-original['start'])/fps*rational(original['rate']);end=source+Fraction(proposed['duration'])/fps*rational(original['rate']);available=assets[original['asset']]['metadata'].get('duration')
                if source<0 or available is not None and assets[original['asset']]['kind']!='Image' and original['pad_end']=='none' and end>Fraction(str(available))+Fraction(1,48000):g['error']='Source handles exhausted; no padding or destructive trim.'
        if self.mode=='Normal' or g['mode']!='move':
            for category,original in g['rows']:
                if category!='clips':continue
                proposed=previews[original['id']]
                for other in g['collision'].get(proposed['track'],[]):
                    overlap=max(0,min(proposed['start']+proposed['duration'],other['start']+other['duration'])-max(proposed['start'],other['start']));prior=max(0,min(original['start']+original['duration'],other['start']+other['duration'])-max(original['start'],other['start'])) if original['track']==other['track'] else 0
                    if overlap>prior:g['error']='Normal edit collides with material. Choose Insert, Overwrite or an explicit transition.';break
        elif self.mode=='Insert':
            left=min(r['start'] for r in previews.values());moving=set(previews)
            if any(tracks[r['track']].get('locked',False) for _,r in self.rows() if r['id'] not in moving and r['start']+r['duration']>left):g['error']='Insert would shift/cut a locked synchronized track. Entire gesture rejected.'
        g.update(preview=previews,change=change);self.notify(g['error'] or f"{g['mode'].title()} preview • Δ {delta:+} frames • {len(previews)} item(s) • {self.mode} • not accepted until release");self.feedback_samples.append(dict(kind=g['mode'],event_work_ms=(time.perf_counter()-began)*1000,classification='handler work, not visible latency'));self.feedback_samples=self.feedback_samples[-256:];self.update()
    def mouseReleaseEvent(self,e):
        if e.button() not in (Qt.LeftButton,Qt.MiddleButton):return
        g=self.gesture;self.gesture=None
        if QWidget.mouseGrabber() is self:self.releaseMouse()
        self.update()
        if g and g['kind']=='seek':
            frame=min(self.end,self.at(e.position().x()))
            if frame!=g['last_frame']:self.workspace.transport('seek',frame,binding=g['binding'],gesture_token=g['token'])
            return
        if not g or g['kind']!='edit' or not g.get('active') or not g.get('change'):return
        if g['error']:self.notify(g['error']+' Gesture rejected; accepted document retained.');return
        self.perform(('Move selection' if g['mode']=='move' else 'Trim linked clip'),[g['change']],g['binding'],g['preview'])
    def split(self,at=None,ids=None):
        ids=ids or self.ids();at=self.workspace.transport_state().get('frame',self.frame) if at is None else at
        if not ids:self.notify('Select an item to split.');return
        if not any(r['start']<at<r['start']+r['duration'] for _,r in self.members(ids)):self.notify('Split at an endpoint: no edit needed.');return
        self.perform('Split at frame '+str(at),[dict(op='items.split',ids=ids,at=at,linked=self.linked,groups=True)])
    def copy(self,cut=False):
        rows=self.members()
        if not rows:self.notify('Select timeline items first.');return
        used={r['track'] for _,r in rows};packet=dict(version=1,project=self.document['id'],rows=[dict(category=c,row=deepcopy(r)) for c,r in rows],tracks=[deepcopy(t) for t in self.tracks if t['id'] in used]);mime=QMimeData();mime.setData(CLIPBOARD,json.dumps(packet,separators=(',',':')).encode());QApplication.clipboard().setMimeData(mime)
        if cut:self.perform('Cut selection',[dict(op='items.delete',ids=self.ids(),linked=self.linked,groups=True)])
        else:self.notify('Copied '+str(len(rows))+' timeline items; project unchanged.')
    def paste(self,duplicate=False):
        try:
            if duplicate:
                rows=self.members();packet=dict(project=self.document['id'],rows=[dict(category=c,row=deepcopy(r)) for c,r in rows],tracks=self.tracks);at=max((r['start']+r['duration'] for _,r in rows),default=self.frame)
            else:
                mime=QApplication.clipboard().mimeData()
                if not mime.hasFormat(CLIPBOARD):raise ValueError('Clipboard has no ZeraWave timeline items.')
                raw=bytes(mime.data(CLIPBOARD))
                if len(raw)>524288:raise ValueError('Timeline clipboard exceeds the existing512KiB request limit.')
                packet=json.loads(raw);at=self.workspace.transport_state().get('frame',self.frame)
            if packet['project']!=self.document['id']:raise ValueError('This clipboard belongs to another project. Add its sources through Library before pasting across projects.')
            mapping={};source_tracks={t['id']:t for t in packet['tracks']};primary=next((source_tracks[e['row']['track']] for e in packet['rows']),None);target=next((t for t in self.tracks if t['id']==self.current_track),None)
            for old,track in source_tracks.items():
                if old in {t['id'] for t in self.tracks}:mapping[old]=old
                else:
                    candidates=[t for t in self.tracks if t['kind']==track['kind']]
                    if not candidates:raise ValueError('Add a '+track['kind']+' track before pasting.')
                    mapping[old]=candidates[0]['id']
            if not duplicate and target and primary and target['kind']==primary['kind']:
                kinds={kind:[t['id'] for t in self.tracks if t['kind']==kind] for kind in ('video','audio','graphics')};origin=kinds[primary['kind']].index(primary['id']) if primary['id'] in kinds[primary['kind']] else 0;offset=kinds[target['kind']].index(target['id'])-origin
                for old,track in source_tracks.items():
                    choices=kinds[track['kind']];index=(choices.index(old) if old in choices else 0)+offset
                    if not 0<=index<len(choices):raise ValueError('A copied companion has no compatible destination track. Add it or choose another target; nothing changed.')
                    mapping[old]=choices[index]
            self.perform('Duplicate selection' if duplicate else 'Paste selection',[dict(op='items.paste',rows=packet['rows'],at=at,track_map=mapping,mode=self.mode)])
        except Exception as exc:self.notify(str(exc))
    def delete_selection(self,ripple=None):
        if ripple is None:ripple=self.workspace.timeline.ripple_control.isChecked()
        rows=self.members();ids=self.ids();linked=self.linked;binding=self.workspace.binding()
        if self.version!=(binding.get('expected_epoch'),binding.get('expected_revision')):self.workspace.timeline.refresh();self.notify('Timeline changed. Review the refreshed selection before confirming deletion.');return
        if not rows:self.notify('Select timeline items first.');return
        if ripple:
            left=min(r['start'] for _,r in rows);right=max(r['start']+r['duration'] for _,r in rows);affected=sum(r['start']+r['duration']>left for _,r in self.rows())
            answer=QMessageBox.question(self,'Ripple delete synchronized range',f'Remove [{left}, {right}) across ALL project tracks, including captions and graphics?\n{affected} items may be cut or shifted. Locked or external linked conflicts reject the entire operation.',QMessageBox.Yes|QMessageBox.No)
            if answer!=QMessageBox.Yes:return
        self.perform('Ripple delete synchronized range' if ripple else 'Delete selection',[dict(op='items.delete',ids=ids,ripple=ripple,linked=linked,groups=True)],binding)
    def action(self,op):
        if self.selection:self.perform(op.removeprefix('items.').title()+' selection',[dict(op=op,ids=self.ids())])
        else:self.notify('Select matching timeline items first.')
    def context(self,pos):
        hit=self.hit(pos)
        if hit and hit[1] not in self.selection:self.select(hit[0],hit[1])
        menu=QMenu(self)
        for label,fn in [('Cut',lambda:self.copy(True)),('Copy',self.copy),('Paste',self.paste),('Duplicate',lambda:self.paste(True)),('Split at playhead',self.split),('Delete',self.delete_selection),('Ripple delete…',lambda:self.delete_selection(True)),('Group',lambda:self.action('items.group')),('Ungroup',lambda:self.action('items.ungroup')),('Link A/V',lambda:self.action('items.link')),('Unlink',lambda:self.action('items.unlink'))]:menu.addAction(label,lambda checked=False,fn=fn:fn())
        menu.exec(self.mapToGlobal(pos))
    def keyPressEvent(self,e):
        mods=e.modifiers();key=e.key()
        if key==Qt.Key_Escape:
            self.cancel_gesture('Unfinished gesture cancelled; no document edit.');self.workspace.timeline.cancel_placement();return
        if mods&Qt.ControlModifier:
            if key==Qt.Key_A:self.selection=set(self.rows_by_id);self.update();return
            if key==Qt.Key_C:self.copy();return
            if key==Qt.Key_X:self.copy(True);return
            if key==Qt.Key_V:self.paste();return
            if key==Qt.Key_D:self.paste(True);return
        if key==Qt.Key_V:self.workspace.timeline.set_tool('Select');return
        if key==Qt.Key_C:self.workspace.timeline.set_tool('Razor');return
        if key==Qt.Key_N:self.workspace.timeline.snap_control.toggle();return
        if key==Qt.Key_F2 and self.current_track in self.workspace.timeline.headers.widgets:
            field=self.workspace.timeline.headers.widgets[self.current_track].findChild(QLineEdit);field.setFocus();field.selectAll();return
        if key==Qt.Key_S:self.split();return
        if key==Qt.Key_Delete:self.delete_selection(True if mods&Qt.ShiftModifier else None);return
        if key in (Qt.Key_I,Qt.Key_O):self.workspace.transport('range_in' if key==Qt.Key_I else 'range_out',self.frame);return
        if key in (Qt.Key_Home,Qt.Key_End):self.workspace.transport('beginning' if key==Qt.Key_Home else 'last');return
        if key in (Qt.Key_Left,Qt.Key_Right):self.workspace.transport('step',-1 if key==Qt.Key_Left else 1);return
        if key==Qt.Key_Space:self.workspace.transport('pause' if self.workspace.transport_state().get('playing') else 'play');return
        super().keyPressEvent(e)
    def wheelEvent(self,e):
        panel=self.workspace.timeline
        if e.modifiers()&Qt.ControlModifier:panel.zoom(1.25 if e.angleDelta().y()>0 else .8,e.position().x());e.accept();return
        bar=panel.scroll.verticalScrollBar() if e.modifiers()&Qt.ShiftModifier else panel.scroll.horizontalScrollBar();delta=e.pixelDelta().y() or e.angleDelta().y();bar.setValue(bar.value()-delta);e.accept()
    def dragEnterEvent(self,event):
        if event.mimeData().hasFormat('application/x-zerawave-assets') or event.mimeData().hasFormat('application/x-zerawave-project-media'):event.setDropAction(Qt.CopyAction);event.accept()
    def dragMoveEvent(self,event):
        try:
            frame=self.at(event.position().x());index=int((event.position().y()-self.ruler_height)//self.row_height);track=self.tracks[index]['id'] if 0<=index<len(self.tracks) else None
            from studio_timeline_media import placement_channels
            channels=placement_channels(self.workspace.document(),track);self.drop_preview=dict(frame=frame,track=track,label=channels+' • '+self.mode+' placement • release to prepare',duration=30);event.setDropAction(Qt.CopyAction);event.accept();self.update()
        except Exception:event.ignore()
    def dragLeaveEvent(self,event):self.drop_preview=None;self.update();event.accept()
    def dropEvent(self,event):
        preview=self.drop_preview;self.drop_preview=None;self.update()
        if preview:
            self.workspace.timeline.place_mime(event.mimeData(),preview['track'],preview['frame']);event.setDropAction(Qt.CopyAction);event.accept()
        else:event.ignore()

class TrackGrip(QToolButton):
    def __init__(self,key,parent):super().__init__(parent);self.key=key;self.press=None;self.setText('⋮⋮');self.setToolTip('Drag to reorder this track')
    def mousePressEvent(self,event):self.press=event.position();super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self.press is not None and event.buttons()&Qt.LeftButton and (event.position()-self.press).manhattanLength()>=QApplication.startDragDistance():
            self.press=None;mime=QMimeData();mime.setData(TRACK_MIME,self.key.encode());drag=QDrag(self);drag.setMimeData(mime);drag.exec(Qt.MoveAction)
        else:super().mouseMoveEvent(event)

class TrackHeaders(QWidget):
    def __init__(self,panel):super().__init__();self.panel=panel;self.version=None;self.setAcceptDrops(True);self.layout_=QVBoxLayout(self);self.layout_.setContentsMargins(0,0,0,0);self.layout_.setSpacing(0);self.spacer=QWidget();self.spacer.setFixedHeight(panel.canvas.ruler_height);self.layout_.addWidget(self.spacer);self.widgets={}
    def refresh(self):
        c=self.panel.canvas
        version=(c.version,bool(c.workspace.pending))
        if self.version==version:return
        self.version=version;remaining=dict(self.widgets);self.widgets={}
        for widget in remaining.values():self.layout_.removeWidget(widget)
        for track in c.tracks:
            key=track['id'];widget=remaining.pop(key,None)
            if widget is None:
                widget=QWidget();layout=QVBoxLayout(widget);layout.setContentsMargins(3,2,3,2);layout.setSpacing(1);top=QHBoxLayout();layout.addLayout(top);top.addWidget(TrackGrip(key,widget));name=QLineEdit();name.setMaxLength(256);name.edit_binding=None;name.authoritative='';name.submitted=None;widget.name_field=name;top.addWidget(name,1)
                name.textEdited.connect(lambda text,key=key,box=name:self.name_started(key,box));name.returnPressed.connect(lambda key=key,box=name:self.rename(key,box,True));name.editingFinished.connect(lambda key=key,box=name:self.rename(key,box));controls=QHBoxLayout();layout.addLayout(controls);widget.controls={}
                for label,field in [('Lock','locked')]+([('Mute','mute'),('Solo','solo')] if track['kind']=='audio' else [('Visible','visible')]):
                    b=QToolButton();b.setText('M' if label=='Mute' else 'S' if label=='Solo' else '');b.setFixedSize(24,24);b.setAccessibleName(label);b.setToolTip(label);
                    if field in ('locked','visible'):
                        from studio_project_controls import editor_icon
                        b.setIcon(editor_icon('lock' if field=='locked' else 'visible'));b.setIconSize(QSize(20,20))
                    b.setCheckable(True);controls.addWidget(b);widget.controls[field]=b;b.clicked.connect(lambda checked,key=key,field=field:c.perform('Track '+field,[dict(op='track.audio' if field=='mute' else 'track.edit',id=key,values={field:checked})]))
                more=QToolButton();more.setText('⋯');more.setToolTip('Track rename, reorder and remove');more.clicked.connect(lambda checked=False,key=key,widget=widget:self.menu(key,widget));controls.addWidget(more)
            widget.setFixedHeight(c.row_height);name=widget.name_field
            # Preserve a focused/modified edit through unrelated revision updates.
            # A stale submission rejects against its captured binding; its text
            # remains available for an explicit retry rather than automatic rebase.
            if not name.isModified() or name.text()==track['name']:
                name.blockSignals(True);name.setText(track['name']);name.setModified(False);name.blockSignals(False);name.authoritative=track['name'];name.edit_binding=None;name.submitted=None
            name.setAccessibleName('Rename track '+track['name']);name.setToolTip('Track name • F2 or edit inline. Unsaved typed text is retained across other edits.')
            for field,b in widget.controls.items():
                b.blockSignals(True);b.setChecked(track['audio']['mute'] if field=='mute' else track.get(field,field=='visible'));b.blockSignals(False);b.setAccessibleName(track['name']+' '+field);b.setToolTip(field.title()+' '+track['name']);b.setEnabled(not c.workspace.pending)
            self.layout_.addWidget(widget);self.widgets[key]=widget
        for key,widget in remaining.items():
            if widget.name_field.isModified():c.notify('Track removed while a name was being edited. Unaccepted name: '+widget.name_field.text())
            widget.deleteLater()
        self.setFixedSize(self.panel.header_width,c.height())
    def name_started(self,key,box):
        self.panel.canvas.current_track=key
        if box.edit_binding is None:box.edit_binding=self.panel.workspace.binding()
    def rename(self,key,box,explicit=False):
        c=self.panel.canvas;w=self.panel.workspace
        if not box.isModified() or box.text()==box.authoritative:return
        if w.pending:c.notify('Track name is still typed, not accepted. Wait for the current operation, then press Enter.');return
        if box.submitted:
            outcome=getattr(w,'last_outcome',{})
            if outcome.get('id')==box.submitted and outcome.get('status') in ('failed','rejected'):

                if not explicit:c.notify('Rejected track name retained. Press Enter to retry against the current project.');return
                box.edit_binding=w.binding();box.submitted=None
        box.submitted=c.perform('Rename track',[dict(op='track.edit',id=key,values=dict(name=box.text()))],box.edit_binding or w.binding())
    def menu(self,key,widget):
        menu=QMenu(self);c=self.panel.canvas;order=next(i for i,t in enumerate(c.tracks) if t['id']==key)
        menu.addAction('Rename (F2)',lambda:widget.findChild(QLineEdit).setFocus());up=menu.addAction('Move track up',lambda:c.perform('Move track up',[dict(op='track.move',id=key,order=order-1)]));up.setEnabled(order>0);down=menu.addAction('Move track down',lambda:c.perform('Move track down',[dict(op='track.move',id=key,order=order+1)]));down.setEnabled(order<len(c.tracks)-1);menu.addAction('Remove track…',lambda:self.remove(key));menu.exec(widget.mapToGlobal(widget.rect().bottomLeft()))
    def remove(self,key):
        c=self.panel.canvas;binding=c.workspace.binding()
        if c.version!=(binding.get('expected_epoch'),binding.get('expected_revision')):self.panel.refresh();c.notify('Timeline changed. Review track contents before confirming removal.');return
        own=[r['id'] for _,r in c.rows() if r['track']==key];all_rows=expanded_selection(c.document,own,True,False) if own else [];external=sum(r['track']!=key for _,r in all_rows)
        if own and QMessageBox.question(self,'Remove track',f'Remove this track and {len(own)} items, plus {external} linked partners on other tracks? Original source files stay intact. Locked partners reject the whole operation.',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        c.perform('Remove track and linked contents',[dict(op='track.remove',id=key,confirmed=True,linked=True)],binding)
    def dragEnterEvent(self,event):
        if event.mimeData().hasFormat(TRACK_MIME):event.acceptProposedAction()
    def dragMoveEvent(self,event):self.dragEnterEvent(event)
    def dropEvent(self,event):
        c=self.panel.canvas;key=bytes(event.mimeData().data(TRACK_MIME)).decode();ids=[t['id'] for t in c.tracks]
        if key not in ids:event.ignore();return
        target=max(0,min(len(ids),round((event.position().y()-c.ruler_height)/c.row_height)));old=ids.index(key);target=max(0,min(len(ids)-1,target-(old<target)));c.perform('Reorder track',[dict(op='track.move',id=key,order=target)]);event.setDropAction(Qt.MoveAction);event.accept()

class TimelinePanel(QWidget):
    def __init__(self,workspace):
        super().__init__();self.workspace=workspace;self.setMinimumHeight(220);self.placement=None;self.decorations=None;self.retiring_decorations=[];self.decoration_epoch=None;self.closed=False;self.header_width=180;self.compact=None;layout=QVBoxLayout(self);layout.setContentsMargins(3,2,3,2);layout.setSpacing(2);self.canvas=Timeline(workspace);self.tools={};group=QActionGroup(self);group.setExclusive(True)
        from studio_project_controls import editor_icon,tool_button
        self.toolbar=QToolBar('Timeline editing');self.toolbar.setMovable(False);self.toolbar.setFixedHeight(32);self.toolbar.setIconSize(QSize(22,22));self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly);layout.addWidget(self.toolbar)
        for name,key in [('Select','V'),('Razor','C')]:
            action=self.toolbar.addAction(editor_icon(name.lower()),name,lambda checked=False,name=name:self.set_tool(name));action.setCheckable(True);action.setToolTip(name+' • '+key);group.addAction(action);self.tools[name]=action
        self.tools['Select'].setChecked(True);self.mode=QComboBox();self.mode.addItems(['Normal','Insert','Overwrite']);self.mode.setMaximumWidth(110);self.mode.setAccessibleName('Timeline placement mode');self.mode.setToolTip('Normal rejects new collisions; Insert shifts synchronized tracks; Overwrite replaces the targeted interval.');self.mode.currentTextChanged.connect(lambda value:setattr(self.canvas,'mode',value));self.toolbar.addWidget(self.mode)
        self.snap_control=tool_button('snap','Snapping (N)',None,self,True);self.snap_control.setChecked(True);self.snap_control.toggled.connect(lambda value:setattr(self.canvas,'snap',value));self.toolbar.addWidget(self.snap_control)
        self.links_control=tool_button('linked','Linked A/V selection',None,self,True);self.links_control.setChecked(True);self.links_control.toggled.connect(lambda value:setattr(self.canvas,'linked',value));self.toolbar.addWidget(self.links_control)
        add=tool_button('add','Add track',None,self);menu=QMenu(add)
        for kind,label in [('video','Video'),('audio','Audio'),('graphics','Titles / captions')]:menu.addAction(label,lambda checked=False,kind=kind:self.quick_track(kind))
        add.setMenu(menu);add.setPopupMode(QToolButton.InstantPopup);self.toolbar.addWidget(add);self.add=add;self.add_track_binding=None;menu.aboutToShow.connect(lambda:setattr(self,'add_track_binding',self.workspace.binding()))
        self.ripple_control=tool_button('ripple','Ripple Delete mode — closes selected range across synchronized tracks',None,self,True);self.toolbar.addWidget(self.ripple_control)
        spacer=QWidget();spacer.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Preferred);self.toolbar.addWidget(spacer)
        for icon,label,fn in [('fit','Fit Sequence',lambda:self.fit(False)),('minus','Timeline zoom out',lambda:self.zoom(.8))]:self.toolbar.addWidget(tool_button(icon,label,lambda checked=False,fn=fn:fn(),self))
        self.zoom_control=QSlider(Qt.Horizontal);self.zoom_control.setRange(0,100);self.zoom_control.setValue(63);self.zoom_control.setMaximumWidth(120);self.zoom_control.setMinimumWidth(45);self.zoom_control.setAccessibleName('Timeline zoom');self.zoom_control.valueChanged.connect(lambda value:self.set_zoom(value));self.toolbar.addWidget(self.zoom_control)
        self.toolbar.addWidget(tool_button('plus','Timeline zoom in',lambda:self.zoom(1.25),self));self.toolbar.addWidget(tool_button('mixer','Show/hide Audio Mixer',lambda:self.toggle_mixer(),self))
        self.undo=QAction('Undo',self);self.undo.triggered.connect(lambda:self.canvas.workspace.shell.safe(lambda:workspace.submit('undo')));self.redo=QAction('Redo',self);self.redo.triggered.connect(lambda:self.canvas.workspace.shell.safe(lambda:workspace.submit('redo')))
        self.source_mode=QComboBox();self.source_mode.addItems(['A/V linked','Video only','Audio only']);self.source_mode.setAccessibleName('Source placement channels');self.source_mode.hide()
        self.position=QSpinBox(self);self.position.setAccessibleName('Timeline frame');self.position.setRange(0,0);self.position.editingFinished.connect(lambda:workspace.transport('seek_paused',self.position.value()));self.position.hide();self.time=QLabel(self);self.time.hide();self.height_control=QSpinBox(self);self.height_control.setRange(46,160);self.height_control.setValue(64);self.height_control.setAccessibleName('Track height');self.height_control.valueChanged.connect(self.track_height);self.height_control.hide()
        body=QHBoxLayout();body.setSpacing(0);layout.addLayout(body,1);self.headers=TrackHeaders(self);column=QWidget();self.header_column=column;column.setFixedWidth(self.header_width);column_layout=QVBoxLayout(column);column_layout.setContentsMargins(0,0,0,0);column_layout.setSpacing(0);self.header_scroll=QScrollArea();self.header_scroll.setFixedWidth(self.header_width);self.header_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.header_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.header_scroll.setWidget(self.headers);column_layout.addWidget(self.header_scroll,1);self.header_footer=QWidget();self.header_footer.setFixedHeight(0);column_layout.addWidget(self.header_footer);body.addWidget(column);self.scroll=QScrollArea();self.scroll.setMinimumHeight(120);self.scroll.setWidget(self.canvas);body.addWidget(self.scroll,1);self.scroll.verticalScrollBar().valueChanged.connect(self.header_scroll.verticalScrollBar().setValue);self.header_scroll.verticalScrollBar().valueChanged.connect(self.scroll.verticalScrollBar().setValue);self.notice=QLabel();self.notice.setFixedHeight(18);self.notice.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);self.notice.hide()
    def set_compact(self,small):
        if self.compact==small:return
        self.compact=small;self.header_width=140 if small else 180;self.header_column.setFixedWidth(self.header_width);self.header_scroll.setFixedWidth(self.header_width)
        if self.canvas.row_height in (48,64):self.height_control.setValue(48 if small else 64)
        self.headers.version=None;self.headers.refresh()
    def quick_track(self,kind):
        def submit():
            d=self.workspace.document();prefix={'video':'V','audio':'A','graphics':'Titles '}[kind];name=prefix+str(sum(t['kind']==kind for t in d['tracks'])+1);self.workspace.batch('Add '+name,[dict(op='track.add',kind=kind,name=name)],self.add_track_binding or self.workspace.binding());self.add_track_binding=None
        self.workspace.shell.safe(submit)
    def set_zoom(self,value):
        target=.002*(240/.002)**(value/100);self.zoom(target/self.canvas.scale)
    def toggle_mixer(self):
        dock=self.workspace.video_panels.shell.panels['project_mixer'];dock.toggleView(dock.isClosed())
        if not dock.isClosed():dock.setAsCurrentTab()
    def view_settings(self):return dict(version=1,scale=self.canvas.scale,height=self.canvas.row_height,snap=self.canvas.snap,linked=self.canvas.linked,channels=self.source_mode.currentIndex())
    def restore_view(self,data):
        if not isinstance(data,dict) or data.get('version')!=1:return
        scale=data.get('scale',3.);height=data.get('height',64);channels=data.get('channels',0)
        if type(scale) not in (int,float) or not math.isfinite(scale) or not .002<=scale<=240 or type(height) is not int or not 46<=height<=160 or type(channels) is not int or not 0<=channels<=2 or any(type(data.get(k,True)) is not bool for k in ('snap','linked')):return
        self.canvas.scale=scale;self.height_control.setValue(height);self.snap_control.setChecked(data.get('snap',True));self.links_control.setChecked(data.get('linked',True));self.source_mode.setCurrentIndex(channels);self.canvas.resize_canvas()
    def set_tool(self,name):self.canvas.cancel_gesture();self.canvas.tool=name;self.tools[name].setChecked(True);self.canvas.setCursor(Qt.CrossCursor if name=='Razor' else Qt.ArrowCursor)
    def track_height(self,value):self.canvas.row_height=value;self.canvas.resize_canvas();self.headers.version=None;self.headers.refresh()
    def zoom(self,factor,anchor=None):
        bar=self.scroll.horizontalScrollBar();anchor=self.canvas.at(bar.value()+self.scroll.viewport().width()/2) if anchor is None else self.canvas.at(anchor);pixel=self.canvas.x(anchor)-bar.value();self.canvas.scale=max(.002,min(240.,self.canvas.scale*factor));self.canvas.resize_canvas();bar.setValue(round(self.canvas.x(anchor)-pixel))
    def fit(self,selection=False):
        rows=self.canvas.members() if selection else [];left=min((r['start'] for _,r in rows),default=0);right=max((r['start']+r['duration'] for _,r in rows),default=self.canvas.end)
        if selection and not rows:self.canvas.notify('Select timeline items before Fit Selection.');return
        self.canvas.scale=max(.002,min(240.,max(1,self.scroll.viewport().width()-30)/max(1,right-left)));self.canvas.resize_canvas();self.scroll.horizontalScrollBar().setValue(round(self.canvas.x(left)))
    def place_mime(self,mime,track,frame,channels=None):
        from studio_timeline_media import Placement
        if self.placement or self.workspace.pending:self.canvas.notify('A placement/edit is still pending. This drop was not admitted; try again after its outcome.');return
        try:self.placement=Placement(self,mime,track,frame,channels=channels)
        except Exception as exc:self.canvas.notify(str(exc))
    def cancel_placement(self):
        if self.placement:self.placement.cancel.set();self.canvas.notify('Placement preparation cancelled; no automatic resubmission. Accepted work retained.')
    def close_resources(self):
        self.closed=True;self.cancel_placement()
        self.retire_decorations()
    def retire_decorations(self):
        if self.decorations:self.decorations.close();self.retiring_decorations.append(self.decorations);self.decorations=None
    def hideEvent(self,event):
        if hasattr(self,'decorations'):self.retire_decorations()
        super().hideEvent(event)
    def exited(self):
        if self.placement:self.placement.poll()
        return (self.placement is None or self.placement.exited()) and self.decorations is None and all(d.exited() for d in self.retiring_decorations)
    def refresh(self):
        s=self.workspace.state();d=s.get('document');t=self.workspace.transport_state();self.canvas.set_document(d,(s.get('epoch'),s.get('revision')));self.canvas.frame=t.get('frame',0);self.canvas.update();self.headers.refresh();self.position.setRange(0,t.get('end',0))
        if s.get('epoch')!=self.decoration_epoch or not d or not d['clips']:self.retire_decorations();self.decoration_epoch=s.get('epoch')
        self.retiring_decorations=[old for old in self.retiring_decorations if not old.exited()]
        if d and d['clips'] and self.isVisible() and not self.closed and self.decorations is None and not self.retiring_decorations:
            from timeline_decorations import Decorations
            self.decorations=Decorations(self.canvas)
        if self.canvas.pending_preview is not None and not self.workspace.pending:self.canvas.pending_preview=None
        if self.canvas.selection_request and not self.workspace.pending:
            key,keep,previous=self.canvas.selection_request;outcome=getattr(self.workspace,'last_outcome',{})
            if outcome.get('id')==key:
                if outcome.get('status')=='accepted':
                    created=outcome.get('created',[]);self.canvas.selection=({i for i in previous if i in self.canvas.rows_by_id} if keep else set())|{i for i in created if i in self.canvas.rows_by_id};self.canvas.selected=next(((self.canvas.rows_by_id[i][0],i) for i in self.canvas.rows_by_id if i in self.canvas.selection),None)
                self.canvas.selection_request=None
        if not self.position.hasFocus():self.position.setValue(t.get('frame',0))
        from studio_video_workspace import clock_text
        fps=d['settings']['fps'] if d else [30,1];self.time.setText(clock_text(t.get('frame',0),fps)+' / '+clock_text(t.get('end',0),fps)+' • '+str(t.get('frame',0))+'f'+(' • Playing' if t.get('playing') else ''));self.time.setToolTip(t.get('clock','')+'; transport position is separate from audible-device/display verification')
        self.undo.setText(self.workspace.undo.text() if hasattr(self.workspace,'undo') else 'Undo');self.redo.setText(self.workspace.redo.text() if hasattr(self.workspace,'redo') else 'Redo');self.undo.setText('Undo '+s.get('undo_label',''));self.redo.setText('Redo '+s.get('redo_label',''));self.undo.setEnabled(bool(d and s.get('undo_label') and not self.workspace.pending));self.redo.setEnabled(bool(d and s.get('redo_label') and not self.workspace.pending));self.notice.setText(self.workspace.notice.text() if hasattr(self.workspace,'notice') else '')
        if self.placement:
            self.placement.poll()
            if self.placement.exited():self.placement=None
        if self.decorations:
            self.decorations.set_document(d);self.decorations.poll()
        self.header_footer.setFixedHeight(self.scroll.horizontalScrollBar().height() if self.scroll.horizontalScrollBar().isVisible() else 0)
