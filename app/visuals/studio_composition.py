"""Layers and direct composition canvas; edits commit to the existing owner.

The editor draws only layers. It never renders a world or starts visual/audio
transport. Canvas transforms share the renderer's composition contract.
"""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json,math,threading,time
import numpy as np
from PySide6.QtCore import Qt,QTimer,QPointF,QRectF,QSize,Signal,QEvent,QMimeData
from PySide6.QtGui import QImage,QPainter,QPainterPath,QPolygonF,QColor,QPen,QTransform,QIcon,QPixmap,QCursor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QPushButton,QComboBox,QTreeWidget,QTreeWidgetItem,QTreeWidgetItemIterator,QLineEdit,QDoubleSpinBox,QSlider,QCheckBox,QGroupBox,QMenu,QMessageBox,QInputDialog,QSpinBox,QScrollArea,QTabWidget,QApplication,QToolButton,QGridLayout,QFileDialog,QDialog,QDialogButtonBox,QColorDialog,QToolTip,QHeaderView,QSizeGrip,QMainWindow,QToolBar
from composition import defaults,validate_scene,new_layer,lookup,ancestors,effective,asset_matrix,world_matrix,coefficients,transform,properties,reparent,renumber,PRESENTATIONS,BLENDS,MAX_LAYERS,is_branch,ordered_children,partition_aligned,piece_geometry,IDENTITY
from media_frames import FrameReader
from media_registry import decode_image
from artwork import masked,selection_path,store_image,magnetic_point,smudge,brush_stroke,constrained_edit,edit_coverage

def qtransform(m):return QTransform(m[0,0],m[1,0],m[0,1],m[1,1],m[0,2],m[1,2])
def point(m,p):
    v=m@np.array([p[0],p[1],1.]);return v[0],v[1]
def masked_image(image,row):
    if not row['masks']:return image
    return masked(image,row['masks'])

def group_mask(image,row,scene):
    if not row['masks'] and row['crop']==[0.,0.,1.,1.]:return image
    w,h=image.width(),image.height();white=QImage(w,h,QImage.Format_ARGB32_Premultiplied);white.fill(0xffffffff);local=masked_image(white,row)
    mask=QImage(w,h,QImage.Format_ARGB32_Premultiplied);mask.fill(0);p=QPainter(mask);p.setRenderHint(QPainter.SmoothPixmapTransform)
    pixel=np.array([[w,0.,w*.5],[0.,h,h*.5],[0.,0.,1.]])@world_matrix(scene,row['id']);p.setTransform(qtransform(pixel));c=row['crop'];p.setClipRect(QRectF(c[0]-.5,c[1]-.5,c[2]-c[0],c[3]-c[1]));p.drawImage(QRectF(-.5,-.5,1.,1.),local);p.end()
    result=image.copy();p=QPainter(result);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,mask);p.end();return result

def add_image(back,source):
    # W3C Add blend uses source-over alpha; QPainter Plus instead adds alpha.
    result=back.copy();b=np.frombuffer(back.constBits(),np.uint8).reshape(back.height(),back.width(),4)
    s=np.frombuffer(source.constBits(),np.uint8).reshape(source.height(),source.width(),4)
    output=np.frombuffer(result.bits(),np.uint8).reshape(back.height(),back.width(),4)
    # Small planar strips keep arithmetic contiguous and cache resident. The
    # equivalent numerator is 255*(b+s)-max(0,a*b+ab*s-a*ab).
    for y in range(0,back.height(),64):
        bp=b[y:y+64].transpose(2,0,1).astype(np.uint16,order='C');sp=s[y:y+64].transpose(2,0,1).astype(np.uint16,order='C')
        ab,a=bp[3],sp[3]
        for channel in range(3):
            first=a*bp[channel];second=ab*(a-sp[channel]);excess=np.maximum(first,second)-second+127
            # Exact floor(v/255) for this bounded 0..65152 numerator. Avoid
            # slow integer division and wider intermediates without rounding loss.
            output[y:y+64,:,channel]=bp[channel]+sp[channel]-((excess+1+(excess>>8))>>8)
        alpha=ab*(255-a)+127;output[y:y+64,:,3]=a+((alpha+1+(alpha>>8))>>8)
    return result

class GestureSpin(QDoubleSpinBox):
    """Explicit Qt buttons avoid platform style subcontrol hit-test ambiguity."""
    finished=Signal()
    def __init__(self):
        super().__init__();self.setButtonSymbols(QDoubleSpinBox.NoButtons);self.setKeyboardTracking(True)
        self.up=QToolButton(self);self.down=QToolButton(self)
        for button,text,step in ((self.up,'▴',1),(self.down,'▾',-1)):
            button.setText(text);button.setAccessibleName('Increase' if step>0 else 'Decrease');button.setFocusPolicy(Qt.NoFocus);button.setAutoRepeat(True);button.clicked.connect(lambda checked=False,s=step:self.stepBy(s));button.released.connect(lambda:self.finished.emit())
        self.setStyleSheet('GestureSpin { padding-right:48px; }')
    def resizeEvent(self,event):
        super().resizeEvent(event);h=self.height();self.up.setGeometry(self.width()-46,2,22,h-4);self.down.setGeometry(self.width()-24,2,22,h-4)

class EditorStatus(QLabel):
    """Leave concise action/errors readable across periodic telemetry refresh."""
    def setText(self,text):self.until=time.monotonic()+8.;super().setText(text)
    def routine(self,text):
        if time.monotonic()>=getattr(self,'until',0.):super().setText(text)

class QuickToolButton(QToolButton):
    def __init__(self,parent=None):
        super().__init__(parent);self.tip_timer=QTimer(self);self.tip_timer.setSingleShot(True);self.tip_timer.setInterval(250);self.tip_timer.timeout.connect(lambda:QToolTip.showText(QCursor.pos(),self.toolTip(),self) if self.underMouse() else None)
    def enterEvent(self,event):self.tip_timer.start();super().enterEvent(event)
    def leaveEvent(self,event):self.tip_timer.stop();QToolTip.hideText();super().leaveEvent(event)

def icon_button(text,help,callback,parent=None):
    button=QuickToolButton(parent);button.setText(text);button.setToolTip(help);button.setAccessibleName(help);button.setMinimumSize(30,30);button.setStyleSheet('QToolButton {padding:4px;} QToolButton:checked {background:#285463;border:1px solid #68d6df;} QToolButton:pressed {background:#855834;}');button.clicked.connect(callback);return button

def matrix_rotation(degrees,aspect):
    r=math.radians(degrees);c=math.cos(r);s=math.sin(r);return np.array([[c,-s/aspect,0],[s*aspect,c,0],[0,0,1.]])

def tool_icon(name,size,dpr=1.):
    """Aspect-correct vector silhouettes rasterized at the window's actual DPR."""
    pix=QPixmap(max(1,round(size*dpr)),max(1,round(size*dpr)));pix.setDevicePixelRatio(dpr);pix.fill(Qt.transparent)
    p=QPainter(pix);p.setRenderHint(QPainter.Antialiasing);p.scale(size/32,size/32);p.setPen(QPen(QColor('#bfe8ed'),2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin));p.setBrush(Qt.NoBrush)
    if name in ('OwnEye','BranchEye'):
        path=QPainterPath();path.moveTo(2,15);path.quadTo(16,1,30,15);path.quadTo(16,29,2,15);p.drawPath(path);p.drawEllipse(11,10,10,10)
        if name=='BranchEye':p.drawLine(8,27,24,27);p.drawLine(16,24,16,30)
    elif name in ('Brush','Pencil','Sampler'):
        path=QPainterPath();path.moveTo(6,26);path.lineTo(10,17);path.lineTo(23,4);path.lineTo(28,9);path.lineTo(15,22);path.closeSubpath();p.drawPath(path);p.drawLine(10,17,15,22)
        if name=='Brush':p.drawEllipse(QRectF(3,23,8,5))
        if name=='Sampler':p.drawLine(18,5,27,14)
    elif name=='Eraser':p.drawPolygon(QPolygonF([QPointF(4,21),QPointF(18,5),QPointF(28,14),QPointF(16,27),QPointF(10,27)]));p.drawLine(12,12,23,21);p.drawLine(5,28,28,28)
    elif name in ('Cut','Remove'):
        p.drawEllipse(3,20,8,8);p.drawEllipse(20,20,8,8);p.drawLine(8,21,24,4);p.drawLine(23,21,8,4)
    elif name in ('Rectangle','Square','Selection','Mask','Extract'):
        p.setPen(QPen(QColor('#bfe8ed'),2,Qt.DashLine if name in ('Selection','Mask') else Qt.SolidLine));p.drawRect(4,6,24,20)
        if name=='Extract':p.drawLine(10,16,24,16);p.drawLine(19,11,24,16);p.drawLine(19,21,24,16)
    elif name in ('Ellipse','Circle'):p.drawEllipse(3,6,26,20)
    elif name=='Crop':p.drawLine(9,3,9,23);p.drawLine(9,23,29,23);p.drawLine(3,9,23,9);p.drawLine(23,9,23,29)
    elif name=='Select':
        p.drawLine(3,16,29,16);p.drawLine(16,3,16,29)
        for x,y,dx,dy in ((3,16,5,5),(29,16,-5,5),(16,3,5,5),(16,29,5,-5)):p.drawLine(x,y,x+dx,y+dy);p.drawLine(x,y,x+(dx if x==16 else dx),y+(-dy if x!=16 else dy))
    elif name=='Zoom':p.drawEllipse(3,3,19,19);p.drawLine(20,20,29,29);p.drawLine(8,12,17,12);p.drawLine(12,8,12,17)
    elif name in ('Hand','Smudge'):
        path=QPainterPath();path.moveTo(6,22);path.lineTo(4,15);path.quadTo(5,11,9,17);path.lineTo(9,5);path.quadTo(12,1,13,5);path.lineTo(13,14);path.lineTo(14,4);path.quadTo(17,1,18,5);path.lineTo(18,14);path.lineTo(20,6);path.quadTo(23,3,24,8);path.lineTo(24,15);path.quadTo(29,12,28,19);path.lineTo(24,27);path.lineTo(12,29);path.closeSubpath();p.drawPath(path)
        if name=='Smudge':p.drawLine(4,29,22,29)
    else:
        path=QPainterPath();path.moveTo(3,23);path.cubicTo(8,2,18,30,29,7);p.drawPath(path)
        for x,y in ((3,23),(16,15),(29,7)):p.drawEllipse(x-2,y-2,4,4)
    p.end();return QIcon(pix)

class Palette(QWidget):
    """One reusable tool window; geometry is part of existing Studio preferences."""
    def __init__(self,editor,title):
        super().__init__(editor,Qt.Tool);self.editor=editor;self.title=title;self.setWindowTitle(title);self.setMinimumSize(180,120);self.body=QWidget();outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(self.body);outer.addWidget(scroll);grip=QSizeGrip(self);grip.setToolTip('Drag to resize this palette; tool tiles scale with width and height.');grip.setAccessibleName('Resize '+title+' palette');outer.addWidget(grip,0,Qt.AlignRight)
        self.setStyleSheet('QToolTip {opacity:245;} QWidget {widget-animation-duration:0;}')
    def remember(self):
        if self.isVisible():
            p=self.geometry();self.editor.shell.preferences.setdefault('media_palettes',{})[self.title]=[p.x(),p.y(),p.width(),p.height()]
    def closeEvent(self,event):self.remember();super().closeEvent(event)
    def hideEvent(self,event):self.remember();super().hideEvent(event)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        for grid,buttons in getattr(self,'grids',[]):
            count=sum(len(b) for g,b in self.grids);area=max(32,self.width()-32)*max(32,self.height()-80)
            size=max(32,min(88,round(math.sqrt(area/max(1,count))* .72)));columns=max(1,(self.width()-32)//(size+6))
            for i,button in enumerate(buttons):
                grid.addWidget(button,i//columns,i%columns);button.setFixedSize(size,size);button.setIconSize(QSize(round(size*.55),round(size*.55)));button.setIcon(tool_icon(button.property('toolName'),round(size*.55),self.devicePixelRatioF()));button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if size>=68 else Qt.ToolButtonIconOnly)
                font=button.font();font.setPointSizeF(max(8,min(12,size/7)));button.setFont(font)
        for widget in self.body.findChildren(QDoubleSpinBox)+self.body.findChildren(QSpinBox)+self.body.findChildren(QPushButton):
            widget.setMinimumHeight(max(24,min(44,round(self.height()/14))))
        self.remember()
    def moveEvent(self,event):super().moveEvent(event);self.remember()

class Canvas(QWidget):
    def __init__(self,editor):
        super().__init__();self.editor=editor;self.setFocusPolicy(Qt.StrongFocus);self.setMouseTracking(True);self.setMinimumSize(260,180)
        self.zoom=None;self.pan=QPointF();self.drag=None;self.tool='Select';self.points=[];self.point_drag=None;self.mask_mode='Keep';self.shape='Rectangle';self.handles=[];self.closed_path=True;self.preview_undo=[];self.preview_redo=[];self.selection_drag=None;self.stroke=None;self.space_pan=False;self.interactive=None;self.mask_cache={};self.setAcceptDrops(True)
        self.bubble=QWidget(self);bubble=QHBoxLayout(self.bubble);bubble.setContentsMargins(3,3,3,3)
        for text,help,cb,color in (('✓','Apply preview',self.apply,'#77dc99'),('×','Discard preview',self.discard,'#fc7878'),('⧉','Extract this region to an aligned child',self.extract_preview,'#63d6e1'),('↶','Undo preview adjustment',lambda:self.preview_history(False),'#ffcd78'),('↷','Redo preview adjustment',lambda:self.preview_history(True),'#ffcd78')):
            b=icon_button(text,help,cb);b.setStyleSheet('color:'+color);bubble.addWidget(b)
        cut=QPushButton('Cut to Child');cut.clicked.connect(lambda:self.editor.cut_child(self.operation(),True));bubble.addWidget(cut)
        copy=QPushButton('Copy to Child');copy.clicked.connect(lambda:self.editor.cut_child(self.operation(),False));bubble.addWidget(copy)
        self.bubble.hide()
        self.setToolTip('Click to select; drag to move. Corner handles resize; the upper circle rotates. Wheel zooms; middle-drag pans. Shift+D duplicates; Ctrl+D deselects; Delete removes; arrows nudge; Ctrl+Z / Ctrl+Y undo/redo.')
    @property
    def canvas_size(self):return self.editor.canvas_size
    def set_tool(self,name):
        self.tool=name
        if name in ('Brush','Pencil') and hasattr(self.editor,'color_target'):self.editor.color_target=name
        combo=getattr(self.editor,'editor_tools',None)
        if combo:combo.blockSignals(True);combo.setCurrentText(name);combo.blockSignals(False)
        if name in ('Brush','Pencil','Eraser','Sampler','Smudge'):
            pix=QPixmap(28,28);pix.fill(Qt.transparent);p=QPainter(pix);p.setPen(QPen(QColor('black'),3));p.drawLine(0,4,8,4);p.drawLine(4,0,4,8);p.setPen(QColor('white'));p.drawLine(0,4,8,4);p.drawLine(4,0,4,8);p.drawText(9,23,{'Brush':'✎','Pencil':'✎','Eraser':'▱','Sampler':'⌾','Smudge':'≈'}[name]);p.end();self.setCursor(QCursor(pix,4,4))
        else:self.setCursor(Qt.ArrowCursor)
        self.editor.sync_tool_ui()
        self.update()
    def source_image(self,row):return self.editor.images.get(row['asset']) or self.editor.images.get(row['id'])
    def magnetic(self,row,uv):
        image=self.source_image(row);snapped=magnetic_point(image,uv)
        distance=math.hypot((snapped[0]-uv[0])*image.width(),(snapped[1]-uv[1])*image.height()) if image else 0
        self.editor.status.setText(('Magnetic: attracted %.1f source px; '%distance if distance>.1 else 'Magnetic: no strong nearby edge; ')+str(len(self.points))+'/128 points • 12 px search radius • manual correction available.')
        return snapped
    def mask_image(self,image,row):
        key=(image.cacheKey(),json.dumps(row['masks'],sort_keys=True));old=self.mask_cache.get(row['id'])
        if old and old[0]==key:return old[1]
        result=masked_image(image,row);self.mask_cache[row['id']]=(key,result)
        if sum(v[1].sizeInBytes() for v in self.mask_cache.values())>128*1024*1024:self.mask_cache={row['id']:(key,result)}
        return result
    def view(self):
        w,h=self.canvas_size;scale=self.zoom if self.zoom is not None else min(max(1,self.width()-48)/w,max(1,self.height()-48)/h)
        return QTransform(scale,0.,0.,scale,(self.width()-w*scale)/2+self.pan.x(),(self.height()-h*scale)/2+self.pan.y())
    def canvas_point(self,p):
        v=self.view().inverted()[0].map(p);w,h=self.canvas_size;return v.x()/w-.5,v.y()/h-.5
    def source_matrix(self,row):
        meta=self.editor.metadata(row);return asset_matrix(self.editor.config,row,self.canvas_size,(meta.get('width',1)*meta.get('pixel_aspect',1),meta.get('height',1)))
    def mask_point(self,row,pos):
        local=point(np.linalg.inv(self.source_matrix(row)),self.canvas_point(pos));uv=[local[0]+.5,local[1]+.5]
        c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop']
        if row['type']!='Group':uv=[1-uv[0] if row['flip_x'] else uv[0],1-uv[1] if row['flip_y'] else uv[1]]
        return [float(max(0.,min(1.,c[i]+uv[i]*(c[i+2]-c[i])))) for i in (0,1)]
    def screen_point(self,row,uv):
        c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop'];u=(uv[0]-c[0])/(c[2]-c[0])-.5;v=(uv[1]-c[1])/(c[3]-c[1])-.5
        if row['type']!='Group':u=-u if row['flip_x'] else u;v=-v if row['flip_y'] else v
        x,y=point(self.source_matrix(row),(u,v));w,h=self.canvas_size;return self.view().map(QPointF((x+.5)*w,(y+.5)*h))
    def preview_state(self):return deepcopy((self.points,self.handles,self.closed_path))
    def preview_begin(self):
        self.preview_undo.append(self.preview_state());self.preview_undo=self.preview_undo[-32:];self.preview_redo=[]
    def preview_history(self,redo):
        source,target=(self.preview_redo,self.preview_undo) if redo else (self.preview_undo,self.preview_redo)
        if source:target.append(self.preview_state());self.points,self.handles,self.closed_path=source.pop();self.update()
    def operation(self):
        shape='Rectangle' if self.shape in ('Rectangle','Square') or self.tool=='Crop' else 'Ellipse' if self.shape in ('Ellipse','Circle') else 'Curve' if self.shape=='Curve' else 'Path'
        return dict(mode='Cut' if self.tool in ('Cut','Remove') else 'Keep',enabled=True,points=deepcopy(self.points),shape=shape,handles=deepcopy(self.handles) if shape=='Curve' else [])
    def auto_handles(self):
        self.handles=[]
        for i,p in enumerate(self.points):
            a=self.points[i-1];b=self.points[(i+1)%len(self.points)];d=[(b[j]-a[j])/6 for j in (0,1)];self.handles.append([[max(0.,min(1.,p[j]-d[j])) for j in (0,1)],[max(0.,min(1.,p[j]+d[j])) for j in (0,1)]])
    def polygon(self,row):
        m=self.source_matrix(row);w,h=self.canvas_size
        return QPolygonF([self.view().map(QPointF((x+.5)*w,(y+.5)*h)) for x,y in (point(m,p) for p in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)))])
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing);painter.fillRect(self.rect(),QColor('#080e12'))
        w,h=self.canvas_size;view=self.view();canvas=view.mapRect(QRectF(0,0,w,h));painter.save();painter.setClipRect(canvas)
        visible=canvas.intersected(QRectF(self.rect()));left,top=int(canvas.left()),int(canvas.top())
        if not hasattr(self,'checker_tile'):
            self.checker_tile=QPixmap(32,32);self.checker_tile.fill(QColor('#1b242b'));tile=QPainter(self.checker_tile);tile.fillRect(0,0,16,16,QColor('#263038'));tile.fillRect(16,16,16,16,QColor('#263038'));tile.end()
        painter.drawTiledPixmap(visible.toRect(),self.checker_tile,QPointF(visible.left()-left,visible.top()-top).toPoint())
        painter.restore()
        # Paint the visible physical viewport, preserving native detail at 100%.
        # Zoom never allocates a zoomed whole canvas or alters source pixels.
        dpr=self.devicePixelRatioF();region=event.rect() if self.stroke and hasattr(self,'composite_image') else self.rect()
        iw,ih=max(1,round(region.width()*dpr)),max(1,round(region.height()*dpr))
        if iw*ih>8388608:painter.end();return
        projection=np.array([[dpr,0.,0.],[0.,dpr,0.],[0.,0.,1.]])@np.array([[view.m11(),0.,view.dx()],[0.,view.m22(),view.dy()],[0.,0.,1.]])@np.array([[w,0.,w*.5],[0.,h,h*.5],[0.,0.,1.]])
        full_projection=projection.copy();projection[:2,2]-=np.array([region.left(),region.top()])*dpr
        modes={'Normal':QPainter.CompositionMode_SourceOver,'Multiply':QPainter.CompositionMode_Multiply,'Screen':QPainter.CompositionMode_Screen,'Add':QPainter.CompositionMode_Plus,'Difference':QPainter.CompositionMode_Difference}
        def children(parent):
            target=QImage(iw,ih,QImage.Format_ARGB32_Premultiplied);target.fill(0);p=QPainter(target);p.setRenderHint(QPainter.SmoothPixmapTransform)
            rows=ordered_children(self.editor.config,parent)
            for row in rows:
                if not effective(self.editor.config,row,'enabled') or not is_branch(self.editor.config,row) and not row['source_visible']:continue
                group=is_branch(self.editor.config,row);image=children(row['id']) if group else self.editor.images.get(row['id']) or self.editor.images.get(row['asset'])
                if self.stroke and row['id']==self.stroke['row'] and not group:image=self.stroke['preview']
                elif getattr(self.editor,'pending_paint',None) and row['id']==self.editor.pending_paint['row'] and not group:image=self.editor.pending_paint['image']
                if image is None:continue
                if row['type']=='Group' and (row['masks'] or row['crop']!=[0.,0.,1.,1.]):
                    white=QImage(w,h,QImage.Format_ARGB32_Premultiplied);white.fill(0xffffffff);local=masked_image(white,row);mask=QImage(iw,ih,QImage.Format_ARGB32_Premultiplied);mask.fill(0);mp=QPainter(mask);mp.setTransform(qtransform(projection@world_matrix(self.editor.config,row['id'])));c=row['crop'];mp.setClipRect(QRectF(c[0]-.5,c[1]-.5,c[2]-c[0],c[3]-c[1]));mp.drawImage(QRectF(-.5,-.5,1.,1.),local);mp.end();image=image.copy();mp=QPainter(image);mp.setCompositionMode(QPainter.CompositionMode_DestinationIn);mp.drawImage(0,0,mask);mp.end()
                elif not group:image=self.mask_image(image,row)
                partition=not row.get('_own') and partition_aligned(self.editor.config,row)
                strength=row.get('blend_strength',1.);blend='Normal' if strength==0 else row['blend'];add=blend=='Add' or (blend!='Normal' and strength<1.)
                if add:
                    p.end();source=QImage(iw,ih,QImage.Format_ARGB32_Premultiplied);source.fill(0);p=QPainter(source);p.setRenderHint(QPainter.SmoothPixmapTransform)
                p.save();p.setOpacity(row['opacity']);p.setCompositionMode(QPainter.CompositionMode_SourceOver if add else QPainter.CompositionMode_Plus if partition else modes[blend])
                if group:p.drawImage(QRectF(0,0,iw,ih),image)
                else:
                    m=self.source_matrix(row);pixel=projection@m
                    p.setTransform(qtransform(pixel));p.scale(-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1)
                    c=row['crop'];p.drawImage(QRectF(-.5,-.5,1.,1.),image,QRectF(c[0]*image.width(),c[1]*image.height(),(c[2]-c[0])*image.width(),(c[3]-c[1])*image.height()))
                p.restore()
                if add:
                    p.end();original=target
                    if blend=='Add':target=add_image(target,source)
                    else:
                        target=target.copy();bp=QPainter(target);bp.setCompositionMode(modes[blend]);bp.drawImage(0,0,source);bp.end()
                    if strength<1.:
                        normal=original.copy();bp=QPainter(normal);bp.drawImage(0,0,source);bp.end();a=np.frombuffer(normal.constBits(),np.uint8).astype(np.uint16);b=np.frombuffer(target.constBits(),np.uint8).astype(np.uint16);factor=round(strength*255);data=((a*(255-factor)+b*factor+127)//255).astype(np.uint8).tobytes();target=QImage(data,iw,ih,QImage.Format_ARGB32_Premultiplied).copy()
                    p=QPainter(target);p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.end();return target
        image=children(None)
        if region==self.rect():self.composite_image=image
        else:
            cp=QPainter(self.composite_image);cp.setCompositionMode(QPainter.CompositionMode_Source);cp.drawImage(round(region.left()*dpr),round(region.top()*dpr),image);cp.end()
        painter.save();painter.setClipRect(canvas);painter.drawImage(QRectF(region),image);painter.restore();painter.setPen(QPen(QColor('#607078'),1));painter.drawRect(canvas)
        row=self.editor.selected_row()
        if row is not None:
            polygon=self.polygon(row);painter.setPen(QPen(QColor('#f0ae78' if effective(self.editor.config,row,'locked') else '#63d6e1'),1.5));painter.setBrush(Qt.NoBrush);painter.drawPolygon(polygon)
            if not effective(self.editor.config,row,'locked'):
                painter.setBrush(QColor('#10171c'))
                self.resize_handles=list(polygon)+[(polygon[i]+polygon[(i+1)%4])/2 for i in range(4)]
                for p in self.resize_handles:painter.drawRect(QRectF(p.x()-4,p.y()-4,8,8))
                top=(polygon[0]+polygon[1])/2;centre=sum((p for p in polygon),QPointF())/4;direction=top-centre;length=math.hypot(direction.x(),direction.y()) or 1.;handle=top+direction*(22/length)
                painter.drawLine(top,handle);painter.drawEllipse(handle,4,4);self.rotation_handle=handle
            if self.points:
                m=self.source_matrix(row);c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop'];poly=[]
                for x,y in self.points:
                    u=(x-c[0])/(c[2]-c[0])-.5;v=(y-c[1])/(c[3]-c[1])-.5
                    if row['type']!='Group':u=-u if row['flip_x'] else u;v=-v if row['flip_y'] else v
                    x1,y1=point(m,(u,v));poly.append(self.view().map(QPointF((x1+.5)*w,(y1+.5)*h)))
                painter.setPen(QPen(QColor('#ffcd78'),2));painter.drawPolyline(QPolygonF(poly))
                for p in poly:painter.drawEllipse(p,4,4)
                if len(self.points)>=3:
                    op=self.operation();path=selection_path(op,(1.,1.),self.closed_path);c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop'];uv=np.array([[1/(c[2]-c[0]),0.,-c[0]/(c[2]-c[0])-.5],[0.,1/(c[3]-c[1]),-c[1]/(c[3]-c[1])-.5],[0.,0.,1.]])
                    flip=np.diag([-1. if row['flip_x'] else 1.,-1. if row['flip_y'] else 1.,1.]) if row['type']!='Group' else np.eye(3)
                    pp=full_projection/dpr@self.source_matrix(row)@flip@uv;painter.save();painter.setTransform(qtransform(pp));painter.setPen(QPen(QColor('#ffcd78'),0));painter.setBrush(QColor(255,205,120,35) if self.closed_path else Qt.NoBrush);painter.drawPath(path);painter.restore()
                for i,pair in enumerate(self.handles):
                    for v in pair:
                        a=self.screen_point(row,self.points[i]);b=self.screen_point(row,v);painter.setPen(QPen(QColor('#bd9ddc'),1));painter.drawLine(a,b);painter.drawEllipse(b,3,3)
                self.bubble.adjustSize();self.bubble.move(max(0,min(self.width()-self.bubble.width(),round(poly[-1].x()+12))),max(0,min(self.height()-self.bubble.height(),round(poly[-1].y()+12))));self.bubble.show()
            else:self.bubble.hide()
        # A private first-stroke buffer is displayed before its atomic child commit.
        if self.stroke and self.stroke.get('new_child'):
            row=self.stroke['target'];painter.save();painter.setTransform(qtransform(projection/dpr@self.source_matrix(row)));painter.scale(-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1);c=row['crop'];im=self.stroke['image'];painter.drawImage(QRectF(-.5,-.5,1.,1.),im,QRectF(c[0]*im.width(),c[1]*im.height(),(c[2]-c[0])*im.width(),(c[3]-c[1])*im.height()));painter.restore()
        if row and self.points and len(self.points)==4 and (self.tool=='Crop' or self.shape in ('Rectangle','Square','Ellipse','Circle')):
            painter.setPen(QPen(QColor('#ffcd78'),2));painter.setBrush(QColor('#10171c'))
            for i in range(4):
                uv=[(self.points[i][j]+self.points[(i+1)%4][j])/2 for j in (0,1)];p=self.screen_point(row,uv);painter.drawRect(QRectF(p.x()-4,p.y()-4,8,8))
        if row and self.points and not self.closed_path and len(self.points)>2:
            painter.setPen(QPen(QColor('#ffcd78'),1,Qt.DashLine));painter.drawLine(self.screen_point(row,self.points[-1]),self.screen_point(row,self.points[0]))
        if row and self.tool in ('Brush','Pencil','Eraser','Smudge') and getattr(self,'hover',None) is not None:
            im=self.source_image(row)
            if im is not None:
                uv=self.mask_point(row,self.hover);r=self.editor.brush['size']/2
                ring=[(-1,-1),(1,-1),(1,1),(-1,1)] if self.editor.brush['shape']=='Square' else [(math.cos(i*math.tau/48),math.sin(i*math.tau/48)) for i in range(48)]
                centre=self.screen_point(row,uv);dx=self.screen_point(row,(uv[0]+r/im.width(),uv[1]))-centre;dy=self.screen_point(row,(uv[0],uv[1]+r/im.height()))-centre
                # An affine basis preserves the cursor outline while avoiding
                # repeated matrix/metadata work for all 48 round vertices.
                outline=QPolygonF([centre+dx*x+dy*y for x,y in ring]);painter.setBrush(Qt.NoBrush)
                for color,width in (('#000000',3),('#ffffff',1)):
                    painter.setPen(QPen(QColor(color),width));painter.drawPolygon(outline)
        painter.end()
    def mousePressEvent(self,event):
        self.setFocus();pos=event.position()
        self.tracing=False
        if self.interactive:
            if event.button()==Qt.LeftButton:self.finish_interactive(True)
            elif event.button()==Qt.RightButton:self.finish_interactive(False)
            return
        if event.button()==Qt.MiddleButton or self.space_pan or self.tool=='Hand':self.drag=('pan',pos,QPointF(self.pan));return
        if self.tool=='Zoom':
            self.zoom=max(.02,min(16.,self.view().m11()*(1/1.25 if event.modifiers()&Qt.AltModifier else 1.25)));self.update();return
        erase=event.button()==Qt.RightButton and self.tool in ('Brush','Pencil','Eraser','Smudge') and not event.modifiers()&Qt.ShiftModifier
        if event.button()!=Qt.LeftButton and not erase:return
        row=self.editor.selected_row()
        if self.tool in ('Brush','Pencil','Eraser','Smudge') and row is None:self.editor.drawing_onboarding();return
        if self.tool=='Sampler' and self.editor.sample_scope=='Visible Composite':
            self.editor.receive_sample(self.sample_composite(pos));return
        if self.tool=='Sampler' and row and not self.polygon(row).containsPoint(pos,Qt.OddEvenFill):
            self.editor.receive_sample(None);return
        if self.tool in ('Brush','Pencil','Eraser','Smudge','Sampler') and row:
            self.paint_press(row,pos,erase);return
        if self.tool in ('Selection','Mask','Remove','Cut','Crop','Extract') and row:
            if not self.editor.editable_target(row):return
            p=self.mask_point(row,pos)
            self.preview_begin()
            if self.shape=='Magnetic':p=self.magnetic(row,p)
            for i,pair in enumerate(self.handles):
                for j,v in enumerate(pair):
                    q=self.screen_point(row,v)
                    if math.hypot(q.x()-pos.x(),q.y()-pos.y())<8:self.point_drag=('handle',i,j);return
            # Adjust an existing preview point, or append one. No owner/history edit.
            nearest=min(range(len(self.points)),key=lambda i:math.dist(self.points[i],p),default=None)
            if nearest==0 and math.dist(self.points[nearest],p)<.015 and len(self.points)>=3 and self.shape in ('Polygon','Curve','Magnetic'):
                self.closed_path=True;self.apply();return
            if nearest is not None and math.dist(self.points[nearest],p)<.015:self.point_drag=nearest;self.selected_point=nearest
            elif self.tool=='Crop' or self.shape in ('Rectangle','Square','Ellipse','Circle'):
                if len(self.points)==4:
                    mids=[[(self.points[i][j]+self.points[(i+1)%4][j])/2 for j in (0,1)] for i in range(4)];i=min(range(4),key=lambda i:math.dist(mids[i],p))
                    if math.dist(mids[i],p)<.02:self.point_drag=('side',i);return
                self.selection_drag=p;self.points=[p.copy() for _ in range(4)];self.handles=[]
            elif len(self.points)<128:self.points.append(p);self.selected_point=len(self.points)-1;self.point_drag=len(self.points)-1;self.tracing=True
            else:self.editor.status.setText('128-point limit reached. Apply or edit/delete existing points; preview retained.')
            self.update();return
        handle=None
        if row and not effective(self.editor.config,row,'locked'):
            if hasattr(self,'rotation_handle') and math.hypot(pos.x()-self.rotation_handle.x(),pos.y()-self.rotation_handle.y())<10:handle='rotate'
            else:
                polygon=self.polygon(row);handles=list(polygon)+[(polygon[i]+polygon[(i+1)%4])/2 for i in range(4)]
                for i,p in enumerate(handles):
                    if math.hypot(pos.x()-p.x(),pos.y()-p.y())<9:handle='scale';self.scale_handle=i;break
        if handle is None:
            hit=None
            # Children and groups obey stored front-to-back order.
            def ordered(parent):
                result=[]
                for r in sorted((r for r in self.editor.config['layers'] if r['parent']==parent),key=lambda r:r['order'],reverse=True):
                    if is_branch(self.editor.config,r):result+=ordered(r['id']);result.append(r)
                    else:result.append(r)
                return result
            for r in ordered(None):
                if effective(self.editor.config,r,'enabled') and self.polygon(r).containsPoint(pos,Qt.OddEvenFill):hit=r;break
            self.editor.select(hit['id'] if hit else None);row=hit
        if row and not effective(self.editor.config,row,'locked'):
            self.drag=(handle or 'move',self.canvas_point(pos),deepcopy(row),deepcopy(self.editor.config));self.setCursor(Qt.SizeAllCursor)
    def mouseMoveEvent(self,event):
        if self.interactive:self.interactive_move(event.position(),event.modifiers());return
        if self.tool in ('Brush','Pencil','Eraser','Smudge'):
            self.hover=event.position()
            if not self.stroke:self.update()
        if self.stroke:self.paint_move(event.position());return
        if self.selection_drag is not None:
            row=self.editor.selected_row();a=self.selection_drag;b=self.mask_point(row,event.position())
            if self.shape in ('Square','Circle'):
                image=self.source_image(row);iw,ih=(image.width(),image.height()) if image else (1,1);length=min(abs(b[0]-a[0])*iw,abs(b[1]-a[1])*ih);b=[max(0.,min(1.,a[0]+math.copysign(length/iw,b[0]-a[0]))),max(0.,min(1.,a[1]+math.copysign(length/ih,b[1]-a[1])))]
            self.points=[[min(a[0],b[0]),min(a[1],b[1])],[max(a[0],b[0]),min(a[1],b[1])],[max(a[0],b[0]),max(a[1],b[1])],[min(a[0],b[0]),max(a[1],b[1])]];self.update();return
        if self.point_drag is not None:
            row=self.editor.selected_row();p=self.mask_point(row,event.position())
            if isinstance(self.point_drag,tuple):
                if self.point_drag[0]=='handle':self.handles[self.point_drag[1]][self.point_drag[2]]=p
                else:
                    i=self.point_drag[1];axis=1 if i%2==0 else 0
                    for j in (i,(i+1)%4):self.points[j][axis]=p[axis]
                    if self.shape in ('Square','Circle'):
                        image=self.source_image(row);dims=(image.width(),image.height()) if image else (1,1);other=1-axis;centre=(self.points[0][other]+self.points[2][other])/2;length=min(abs(self.points[2][axis]-self.points[0][axis])*dims[axis],2*min(centre,1-centre)*dims[other]);half=length/dims[other]/2
                        for j in (0,1,2,3):self.points[j][other]=centre+(-half if j in ((0,3) if other==0 else (0,1)) else half)
            elif getattr(self,'tracing',False) and self.shape in ('Freehand','Magnetic') and event.buttons()&Qt.LeftButton and math.dist(self.points[-1],p)>.003:
                if len(self.points)>=128:self.editor.status.setText('128-point limit reached; preview retained. Edit/delete points or finish this region.');return
                if self.shape=='Magnetic':p=self.magnetic(row,p)
                self.points.append(p);self.point_drag=len(self.points)-1
            else:
                i=self.point_drag;delta=[p[j]-self.points[i][j] for j in (0,1)]
                if len(self.points)==4 and (self.tool=='Crop' or self.shape in ('Rectangle','Square','Ellipse','Circle')):
                    opposite=self.points[(i+2)%4]
                    if self.shape in ('Square','Circle'):
                        image=self.source_image(row);iw,ih=(image.width(),image.height()) if image else (1,1);length=min(abs(p[0]-opposite[0])*iw,abs(p[1]-opposite[1])*ih);p=[opposite[0]+math.copysign(length/iw,p[0]-opposite[0]),opposite[1]+math.copysign(length/ih,p[1]-opposite[1])]
                    self.points[i]=p;self.points[(i+1)%4][1 if i%2==0 else 0]=p[1 if i%2==0 else 0];self.points[(i-1)%4][0 if i%2==0 else 1]=p[0 if i%2==0 else 1]
                else:self.points[i]=p
                if len(self.handles)==len(self.points):self.handles[i]=[[max(0.,min(1.,v[j]+delta[j])) for j in (0,1)] for v in self.handles[i]]
            self.update();return
        if not self.drag:return
        kind,begin,old,*before=self.drag
        if kind=='pan':self.pan=old+event.position()-begin;self.update();return
        row=self.editor.selected_row()
        if row is None:return
        now=self.canvas_point(event.position());parent=world_matrix(before[0],old['parent']) if old['parent'] else np.eye(3)
        local_begin=point(np.linalg.inv(parent),begin);local_now=point(np.linalg.inv(parent),now);values=old['transform'].copy();x,y,s,sy,r=properties(values,self.canvas_size[0]/self.canvas_size[1])
        if kind=='move':values[4]+=local_now[0]-local_begin[0];values[5]+=local_now[1]-local_begin[1]
        elif kind=='scale':
            inv=np.linalg.inv(self.source_matrix(old));a=point(inv,begin);b=point(inv,now);index=getattr(self,'scale_handle',0)
            sx=max(.01,min(100.,abs(b[0]/a[0]))) if abs(a[0])>1e-6 and index not in (4,6) else 1.;sy1=max(.01,min(100.,abs(b[1]/a[1]))) if abs(a[1])>1e-6 and index not in (5,7) else 1.
            if row['aspect_lock']:sx=sy1=max(sx,sy1) if index<4 else sy1 if index in (4,6) else sx
            values[0]*=sx;values[1]*=sx;values[2]*=sy1;values[3]*=sy1
        elif kind=='rotate':
            aspect=self.canvas_size[0]/self.canvas_size[1];a=math.atan2((local_begin[1]-y)/aspect,local_begin[0]-x);b=math.atan2((local_now[1]-y)/aspect,local_now[0]-x);values=transform(x,y,s,sy,r+math.degrees(b-a),aspect)
        row['transform']=[float(v) for v in values];self.editor.sync_controls();self.editor.schedule_preview();self.update()
    def mouseReleaseEvent(self,event):
        if self.stroke:self.paint_finish();return
        if self.shape=='Curve' and self.points and len(self.handles)!=len(self.points):self.auto_handles()
        complete=self.selection_drag is not None or self.tracing and self.shape=='Freehand'
        self.selection_drag=None
        self.point_drag=None;self.tracing=False
        if complete:
            self.closed_path=True;row=self.editor.selected_row();self.selection_target=row['id'] if row else None
            if self.tool=='Cut':self.apply()
        if self.drag and self.drag[0]!='pan':self.editor.commit('Canvas '+self.drag[0],before=self.drag[3])
        self.drag=None;self.unsetCursor()
    def cancel_drag(self):
        if self.interactive:self.finish_interactive(False)
        if self.drag and self.drag[0]!='pan':self.editor.config=deepcopy(self.drag[3]);self.editor.sync_controls()
        if self.stroke:self.stroke=None;self.editor.status.setText('Uncommitted stroke cancelled; previous artwork retained.')
        self.drag=None;self.point_drag=None;self.selection_drag=None;self.space_pan=False;self.unsetCursor();self.editor.cancel_preview();self.update()
    def hideEvent(self,event):self.cancel_drag();super().hideEvent(event)
    def focusOutEvent(self,event):self.cancel_drag();super().focusOutEvent(event)
    def focusInEvent(self,event):self.set_tool(self.tool);super().focusInEvent(event)
    def leaveEvent(self,event):self.hover=None;self.update();super().leaveEvent(event)
    def wheelEvent(self,event):
        old=self.view();self.zoom=max(.02,min(8.,old.m11()*math.pow(1.15,event.angleDelta().y()/120)));self.update();event.accept()
    def keyPressEvent(self,event):
        if self.editor.editor_key(event):event.accept();return
        super().keyPressEvent(event)
    def keyReleaseEvent(self,event):
        if event.key()==Qt.Key_Space:self.space_pan=False;event.accept();return
        super().keyReleaseEvent(event)
    def mouseDoubleClickEvent(self,event):
        if self.points and self.shape in ('Polygon','Curve','Magnetic'):
            self.closed_path=True;self.apply();event.accept();return
        super().mouseDoubleClickEvent(event)
    def begin_interactive(self,kind):
        row=self.editor.selected_row()
        if not row or not self.editor.editable_target(row):return
        if self.points and self.tool!='Selection' and not self.editor.resolve_pending():return
        self.editor.numeric_finish();self.setFocus();self.drag=None
        self.interactive=dict(kind=kind,before=deepcopy(self.editor.config),target=deepcopy(row),start=self.canvas_point(self.mapFromGlobal(QCursor.pos())),number='',axis=None)
        self.editor.status.setText(kind.title()+' preview • type px / degrees / % • X/Y axis • Enter/click accept • Esc/right-click cancel');self.update()
    def interactive_move(self,pos,mods=Qt.NoModifier):
        op=self.interactive;row=self.editor.selected_row();base=op['target'];dx,dy=np.subtract(self.canvas_point(pos),op['start']);kind=op['kind'];numeric=op['number']
        try:value=float(numeric) if numeric not in ('','-','.','-.') else None
        except ValueError:return
        aspect=self.canvas_size[0]/self.canvas_size[1];x,y,s,sy,angle=properties(base['transform'],aspect);axis=op['axis']
        if kind=='move':
            if value is not None:dx,dy=(value/self.canvas_size[0],0.) if axis!='Y' else (0.,value/self.canvas_size[1])
            if axis=='X':dy=0
            if axis=='Y':dx=0
            # Mouse displacement is canvas-space, so compensate the inherited affine.
            parent=base['parent'];pm=world_matrix(self.editor.config,parent) if parent else np.eye(3);local=np.linalg.inv(pm[:2,:2])@np.array([dx,dy]);row['transform']=base['transform'].copy();row['transform'][4]+=local[0];row['transform'][5]+=local[1]
            label=f'{dx*self.canvas_size[0]:.2f}, {dy*self.canvas_size[1]:.2f} px'
        elif kind=='rotate':
            amount=value if value is not None else dx*360
            if mods&Qt.ShiftModifier:amount=round(amount/15)*15
            row['transform']=coefficients(matrix_rotation(amount,aspect)@np.array([[base['transform'][0],base['transform'][2],0],[base['transform'][1],base['transform'][3],0],[0,0,1.]]));row['transform'][4:]=base['transform'][4:];label=f'{amount:.2f}° around centre pivot'
        else:
            factor=max(.01,value/100 if value is not None else 1+dx*2);fx=factor if axis!='Y' else 1;fy=factor if axis!='X' else 1
            if axis is None and mods&Qt.AltModifier:fy=max(.01,1+dy*2)
            m=np.array([[base['transform'][0],base['transform'][2],base['transform'][4]],[base['transform'][1],base['transform'][3],base['transform'][5]],[0,0,1.]])@np.diag([fx,fy,1.]);row['transform']=coefficients(m);label=f'{fx*100:.2f} × {fy*100:.2f}% • Alt unconstrained'
        row['transform']=[float(v) for v in row['transform']]
        self.editor.status.setText(kind.title()+' '+label+' • '+(axis or 'XY')+' • Enter accept / Esc cancel');self.editor.sync_controls();self.editor.schedule_preview();self.update()
    def finish_interactive(self,accept):
        op,self.interactive=self.interactive,None
        if not op:return
        if accept:self.editor.commit('Interactive '+op['kind'],op['before'])
        else:self.editor.config=op['before'];self.editor.cancel_preview();self.editor.sync_controls();self.update()
    def discard(self):self.points=[];self.handles=[];self.closed_path=True;self.preview_undo=[];self.preview_redo=[];self.point_drag=None;self.editing_mask=None;self.selection_drag=None;self.bubble.hide();self.editor.sync_tool_ui();self.update()
    def extract_preview(self):
        if len(self.points)<3 or not self.closed_path:self.editor.status.setText('Finish and close the boundary before extraction; preview retained.');return
        self.editor.extract_child(self.operation())
    def apply(self):
        row=self.editor.selected_row()
        if not row or not self.points:return
        if not self.editor.editable_target(row):return
        before=deepcopy(self.editor.config)
        if self.tool=='Selection':self.selection_target=row['id'];self.editor.status.setText('Selected pixels of '+row['name']+' • Ctrl+C/X or Copy/Cut to Child');return
        if self.tool=='Cut':
            if not self.closed_path:self.editor.status.setText('Complete this boundary with Enter, double-click or closure.');return
            self.editor.cut_child(self.operation());return
        if self.tool=='Extract':
            if not self.closed_path:self.editor.status.setText('Close this path before extraction.');return
            self.editor.extract_child(self.operation());return
        if self.tool=='Crop':
            if len(self.points)<2:self.editor.status.setText('Crop needs two opposite corners.');return
            row['crop']=[min(p[0] for p in self.points),min(p[1] for p in self.points),max(p[0] for p in self.points),max(p[1] for p in self.points)]
        else:
            if not self.closed_path:self.editor.status.setText('Close this path before applying.');return
            mask=self.operation();index=getattr(self,'editing_mask',None)
            if index is not None:row['masks'][index]=mask
            else:row['masks'].append(mask)
        try:validate_scene(self.editor.config)
        except ValueError as exc:self.editor.config=before;self.editor.status.setText(str(exc));return
        if self.editor.commit('Apply '+self.tool.lower(),before=before):self.discard()
    def paint_press(self,row,pos,erase=False):
        if self.editor.art_jobs and not self.editor.pending_paint:self.editor.status.setText('Finish the pending non-stroke edit first.');return
        if getattr(self.editor,'queued_paint',None):self.editor.status.setText('Two stroke buffers are pending; finish saving before another gesture.');return
        if not self.editor.editable_target(row):return
        if row['type'] not in ('Image','Artwork','Paint'):
            if row['type']=='Group':self.editor.status.setText('Group is an organizational container, not a drawable surface. Select an editable layer.');return
            self.editor.status.setText('Moving media needs an explicit editable frame snapshot. Use Layers → Snapshot current frame.');return
        pending=getattr(self.editor,'pending_paint',None)
        image=pending['image'] if pending and pending['row']==row['id'] else self.source_image(row)
        if image is None:self.editor.status.setText('Target pixels unavailable; wait for decoding or relink.');return
        uv=self.mask_point(row,pos);x,y=uv[0]*image.width(),uv[1]*image.height()
        if self.tool=='Sampler':
            if self.editor.sample_scope=='Visible Composite':sampled=self.sample_composite(pos)
            else:sampled=self.mask_image(image,row).pixelColor(max(0,min(image.width()-1,int(x))),max(0,min(image.height()-1,int(y))))
            self.editor.receive_sample(sampled);return
        if not row['source_visible']:self.editor.status.setText('Own content is hidden. Show it before pixel editing.');return
        buffer=image.convertToFormat(QImage.Format_ARGB32_Premultiplied).copy()
        if buffer.isNull():self.editor.status.setText('Cannot allocate stroke; previous content retained.');return
        selection=self.operation() if self.points and getattr(self,'selection_target',row['id'])==row['id'] else None
        self.stroke=dict(asset=row['asset'],image=buffer,base=image.copy(),scene=deepcopy(self.editor.config),target=deepcopy(row),row=row['id'],session=self.editor.binding[0],revision=self.editor.binding[1],new_child=False,tool='Eraser' if erase else self.tool,brush=deepcopy(self.editor.brush),color=QColor(self.editor.brush_color),last=(x,y),selection=selection)
        self.stroke['coverage']=edit_coverage((image.width(),image.height()),row,selection);self.stroke['preview']=image.copy();self.paint_move(pos)
    def sample_composite(self,pos):
        w,h=self.canvas_size
        if not self.view().mapRect(QRectF(0,0,w,h)).contains(pos):return None
        image=getattr(self,'composite_image',None)
        if image is None:self.editor.status.setText('Visible composite is not ready.');return None
        dpr=self.devicePixelRatioF();x,y=round(pos.x()*dpr),round(pos.y()*dpr)
        return image.pixelColor(x,y) if 0<=x<image.width() and 0<=y<image.height() else None
    def paint_move(self,pos):
        if not self.stroke:return
        stroke=self.stroke
        if not self.editor.valid_target(stroke['session'],stroke['revision'],stroke['target']):self.cancel_drag();return
        row=stroke['target'];uv=self.mask_point(row,pos);image=stroke['image'];now=(uv[0]*image.width(),uv[1]*image.height());last=stroke['last'];brush=stroke['brush']
        if stroke['tool']=='Smudge':
            smudge(image,last,now,brush['size'],brush['strength'],1.,brush['shape'],row,stroke['selection'])
        else:brush_stroke(image,last,now,brush,stroke['color'],stroke['tool'])
        radius=math.ceil(brush['size']/2)+4
        bounds=(math.floor(min(last[0],now[0])-radius),math.floor(min(last[1],now[1])-radius),math.ceil(max(last[0],now[0])+radius),math.ceil(max(last[1],now[1])+radius))
        constrained_edit(stroke['base'],image,row,stroke['selection'],brush['opacity'],bounds=bounds,coverage=stroke['coverage'],result=stroke['preview'])
        stroke['last']=now
        corners=[self.screen_point(row,(x/image.width(),y/image.height())) for x in (bounds[0],bounds[2]) for y in (bounds[1],bounds[3])]
        self.update(QPolygonF(corners).boundingRect().adjusted(-3,-3,3,3).toAlignedRect())

    def paint_finish(self):
        stroke,self.stroke=self.stroke,None
        if stroke and self.editor.valid_target(stroke['session'],stroke['revision'],stroke['target']):self.editor.save_paint(stroke,stroke['preview'])
        self.update()
    def contextMenuEvent(self,event):
        if self.tool in ('Brush','Pencil','Eraser','Smudge') and not QApplication.keyboardModifiers()&Qt.ShiftModifier:event.accept();return
        menu=QMenu(self);view=menu.addMenu('View');view.addAction('Fit canvas',lambda:self.editor.editor_view.fit());view.addAction('100% native detail',lambda:self.editor.editor_view.actual());view.addAction('Canvas Size…',self.editor.canvas_dialog)
        menu.addAction(self.tool+' settings…',lambda:self.editor.tool_settings(self.tool))
        if self.points:
            menu.addAction('Apply preview',self.apply);menu.addAction('Discard preview',self.discard);menu.addAction('Undo preview adjustment',lambda:self.preview_history(False));menu.addAction('Redo preview adjustment',lambda:self.preview_history(True));menu.addAction('Reopen path' if self.closed_path else 'Close path',self.toggle_closed)
        else:
            for name,callback in (('Copy layer',self.editor.copy_layer),('Paste layer',self.editor.paste_layer),('Fit selected artwork',self.editor.fit_action)) :menu.addAction(name,callback)
        menu.exec(event.globalPos())
    def toggle_closed(self):self.preview_begin();self.closed_path=not self.closed_path;self.update()
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dragMoveEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dropEvent(self,event):
        if not self.editor.resolve_pending():return
        paths=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        def ordered(parent):
            for r in sorted((r for r in self.editor.config['layers'] if r['parent']==parent),key=lambda r:r['order'],reverse=True):
                if effective(self.editor.config,r,'enabled'):
                    yield from ordered(r['id']);yield r
        target=next((r for r in ordered(None) if r['type'] in ('Image','Artwork','Paint') and self.polygon(r).containsPoint(event.position(),Qt.OddEvenFill)),None)
        policy='layer'
        if target:
            box=QMessageBox(self);box.setWindowTitle('Drop media');box.setText('Add content without changing originals, or explicitly replace the selected source.');child=box.addButton('Add child',QMessageBox.ActionRole);layer=box.addButton('Add layer',QMessageBox.ActionRole);replace=box.addButton('Replace source',QMessageBox.ActionRole);box.addButton(QMessageBox.Cancel);box.exec();button=box.clickedButton()
            if button not in (child,layer,replace):return
            policy='child' if button is child else 'replace' if button is replace else 'layer'
        self.editor.drop_files(paths,target['id'] if target else None,policy);event.acceptProposedAction()

class DirectToolButton(QuickToolButton):
    def __init__(self,editor,tool,description):
        super().__init__();self.editor=editor;self.tool=tool;self.setText(tool);self.setAccessibleName(tool);self.setToolTip(description+' • Double-click for '+tool+' settings');self.setCheckable(True);self.setIcon(tool_icon(tool,26));self.setIconSize(QSize(26,26));self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);self.setMinimumSize(54,54)
        self.clicked.connect(lambda:editor.choose_tool(tool));self.setStyleSheet('QToolButton:checked {background:#285463;border:2px solid #68d6df;}')
    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.setDown(False);self.editor.tool_settings(self.tool);event.accept();return
        super().mouseDoubleClickEvent(event)

class InlineControls(QWidget):
    """Real row body; not an extra tree item, identity bound across selection."""
    def __init__(self,editor,row):
        super().__init__();self.editor=editor;self.identity=row['id'];self.initial=deepcopy(row);self.fields={};form=QFormLayout(self);form.setContentsMargins(22,4,8,12);form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        protected=effective(editor.config,row,'locked')
        name=QLineEdit(row['name']);name.setObjectName('layer_'+self.identity+'_name');name.setMaxLength(128);name.setEnabled(not protected);name.setAccessibleName('Name '+row['name']);form.addRow('Name',name)
        def rename():
            if getattr(editor,'rebuilding',False):return
            value=name.text();identity=self.identity;QTimer.singleShot(0,lambda:editor.row_edit(identity,'name',value,'Rename layer'))
        name.editingFinished.connect(rename)
        w,h=editor.base_dimensions(row);x,y,s,sy,r=properties(row['transform'],editor.canvas_size[0]/editor.canvas_size[1])
        meta=editor.metadata(row);dims=QLabel(f"Working {meta.get('width','—')} × {meta.get('height','—')} px");form.addRow(dims)
        values=dict(x=x*100,y=y*100,scale=s*100,scale_y=sy*100,width=w*s,height=h*sy,rotation=r,blend_strength=row['blend_strength']*100)
        for key,label,low,high in (('x','Position X %',-10000,10000),('y','Position Y %',-10000,10000),('scale','Scale X %',1,10000),('scale_y','Scale Y %',1,10000),('width','Local width px',.1,100000),('height','Local height px',.1,100000),('rotation','Rotation °',-36000,36000),('blend_strength','Effect contribution %',0,100)):
            box=GestureSpin();box.setObjectName('layer_'+self.identity+'_'+key);box.setRange(low,high);box.setDecimals(1);box.setSingleStep(.1);box.setValue(values[key]);box.setEnabled(not protected);box.setAccessibleName(label+' '+row['name']);form.addRow(label,box);self.fields[key]=box
            box.valueChanged.connect(lambda v,k=key:self.preview(k,v));box.editingFinished.connect(self.finish);box.finished.connect(self.finish)
            if key=='blend_strength':box.setToolTip('0% Normal appearance; 100% selected blend effect. Row master opacity and stroke opacity remain independent.')
        fit=QComboBox();fit.addItems(['Fit','Fill','Stretch']);fit.setCurrentText(row['fit']);fit.setEnabled(not protected and row['type']!='Group');form.addRow('Fit / Fill / Stretch',fit)
        fit.currentTextChanged.connect(lambda v:editor.bound_action(self.identity,lambda:editor.fit_action(v)))
        aspect=QCheckBox('Keep aspect');aspect.setChecked(row['aspect_lock']);aspect.setEnabled(not protected);aspect.toggled.connect(lambda v:editor.row_edit(self.identity,'aspect_lock',v,'Aspect lock'));form.addRow(aspect)
        blend=QComboBox();blend.addItems(BLENDS);blend.setCurrentText(row['blend']);blend.setEnabled(not protected);form.addRow('Blend effect',blend);blend.currentTextChanged.connect(lambda v:editor.row_edit(self.identity,'blend',v,'Layer blend'))
        buttons=QHBoxLayout();form.addRow(buttons)
        for label,cb in (('Flip X',lambda:editor.flip('flip_x')),('Flip Y',lambda:editor.flip('flip_y')),('−90°',lambda:editor.rotate(-90)),('+90°',lambda:editor.rotate(90)),('Align',editor.align_menu)):
            b=QPushButton(label);b.setEnabled(not protected);b.clicked.connect(lambda checked=False,c=cb:editor.bound_action(self.identity,c));buttons.addWidget(b)
        organization=QHBoxLayout();form.addRow(organization)
        for label,cb in (('↑',lambda:editor.step_order(1)),('↓',lambda:editor.step_order(-1)),('Reparent…',editor.move_menu),('Ungroup',editor.ungroup)):
            if label=='Ungroup' and row['type']!='Group':continue
            b=QPushButton(label);b.setEnabled(not protected);b.clicked.connect(lambda checked=False,c=cb:editor.bound_action(self.identity,c));organization.addWidget(b)
        if row['type'] in ('Video','GIF','Sprite'):
            playback=QHBoxLayout();form.addRow('Playback (silent)',playback)
            for label,op in (('▶','play'),('Ⅱ','pause'),('■','stop')):
                button=QPushButton(label);button.clicked.connect(lambda checked=False,o=op:editor.bound_action(self.identity,lambda:editor.transport(o)));playback.addWidget(button)
            for key,label,low,high in (('rate','Rate',.1,8),('start','In s',0,86400),('end','Out s',0,86400)):
                box=QDoubleSpinBox();box.setRange(low,high);box.setDecimals(2);box.setKeyboardTracking(False);box.setValue(row['media'][key] or 0);box.setEnabled(not protected);box.editingFinished.connect(lambda k=key,w=box:editor.bound_action(self.identity,lambda:editor.media_edit(k,w.value())));form.addRow(label,box)
            loop=QComboBox();loop.addItems(['None','Loop','Ping-pong']);loop.setCurrentText(row['media']['loop']);loop.setEnabled(not protected);loop.currentTextChanged.connect(lambda v:editor.bound_action(self.identity,lambda:editor.media_edit('loop',v)));form.addRow('Loop',loop)
            seek=QSlider(Qt.Horizontal);seek.setRange(0,10000);seek.sliderReleased.connect(lambda:editor.bound_action(self.identity,lambda:editor.transport('seek',seek.value()/10000*editor.duration())));form.addRow('Seek',seek)
        if row['type']=='Model':
            for key in ('yaw','pitch','roll'):
                box=QDoubleSpinBox();box.setRange(-36000,36000);box.setValue(row['model'][key]);box.setKeyboardTracking(False);box.setEnabled(not protected);box.editingFinished.connect(lambda k=key,w=box:editor.bound_action(self.identity,lambda:editor.model_edit(k,w.value())));form.addRow(key.title()+' °',box)
        if row['type']=='Web':
            url=QLineEdit(row['web']['url']);url.setEnabled(not protected);url.editingFinished.connect(lambda:editor.bound_action(self.identity,lambda:editor.web_edit('url',url.text())));form.addRow('HTTPS URL',url)
            for label,callback in (('Load / Reload',editor.web_start),('Stop browser',editor.web_sources.stop)):
                b=QPushButton(label);b.clicked.connect(lambda checked=False,c=callback:editor.bound_action(self.identity,c));form.addRow(b)
    def preview(self,key,value):
        e=self.editor;row=lookup(e.config).get(self.identity)
        if not row or effective(e.config,row,'locked'):return
        if e.numeric_before is None:e.numeric_before=deepcopy(e.config)
        e.numeric_key=key
        if key=='blend_strength':row[key]=value/100
        else:
            x,y,s,sy,r=properties(row['transform'],e.canvas_size[0]/e.canvas_size[1]);values=dict(x=x,y=y,scale=s,scale_y=sy,rotation=r)
            if key in ('width','height'):
                w,h=e.base_dimensions(row);mapped='scale' if key=='width' else 'scale_y';values[mapped]=value/(w if key=='width' else h)
                if row['aspect_lock']:values['scale']=values['scale_y']=values[mapped]
            else:
                values[key]=value/(1 if key=='rotation' else 100)
                if row['aspect_lock'] and key in ('scale','scale_y'):values['scale']=values['scale_y']=values[key]
            row['transform']=transform(**values,aspect=e.canvas_size[0]/e.canvas_size[1])
        e.schedule_preview();e.numeric_timer.start();e.canvas.update()
    def finish(self):
        if not getattr(self.editor,'rebuilding',False):QTimer.singleShot(0,self.editor.numeric_finish)

class LayerRow(QWidget):
    def __init__(self,editor,row):
        super().__init__();self.editor=editor;self.identity=row['id'];outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0);line=QHBoxLayout();line.setContentsMargins(2,2,2,2);line.setSpacing(3);outer.addLayout(line)
        inherited=not row['locked'] and effective(editor.config,row,'locked');protected=effective(editor.config,row,'locked')
        edit=icon_button('✎','Edit '+row['name']+' — expand layer controls',lambda:QTimer.singleShot(0,lambda:editor.expand_row(self.identity)));edit.setCheckable(True);edit.setChecked(self.identity in editor.expanded);edit.setStyleSheet('QToolButton:checked {background:#684c28;border:1px solid #f1c178;}');line.addWidget(edit)
        image=editor.images.get(row['id']) or editor.images.get(row['asset'])
        name=QLabel(row['name']);name.setToolTip(row['name']+' • '+row['type']+' • '+row['id']);name.setMinimumWidth(35);name.setWordWrap(True);line.addWidget(name,1)
        self.thumb=QLabel();self.thumb.setFixedSize(28,24);line.insertWidget(1,self.thumb)
        if image is not None:self.update_thumbnail(image)
        if row['type']!='Group':
            own=icon_button('','Own content eye: this layer pixels only; child eyes stay independent',lambda:QTimer.singleShot(0,lambda:editor.row_flag(self.identity,'source_visible')));own.setIcon(tool_icon('OwnEye',24));own.setCheckable(True);own.setChecked(row['source_visible']);line.addWidget(own)
        branch=icon_button('','Subtree eye: layer and descendants; retains individual eye states',lambda:QTimer.singleShot(0,lambda:editor.row_flag(self.identity,'enabled')));branch.setIcon(tool_icon('BranchEye',24));branch.setCheckable(True);branch.setChecked(row['enabled']);line.addWidget(branch)
        master=QHBoxLayout();master.setContentsMargins(35,0,4,3);master.addWidget(QLabel('Opacity'));outer.addLayout(master)
        self.opacity=QSlider(Qt.Horizontal);self.opacity.setRange(0,100);self.opacity.setValue(round(row['opacity']*100));self.opacity.setMinimumWidth(48);self.opacity.setMaximumWidth(100);self.opacity.setEnabled(not protected);self.opacity.setAccessibleName('Master opacity '+row['name']);self.opacity.setToolTip('Finished layer/subtree master opacity; applied once after its effects');master.addWidget(self.opacity,1)
        self.percent=QLabel(f"{row['opacity']*100:.0f}%");self.percent.setMinimumWidth(31);master.addWidget(self.percent);master.addStretch();self.opacity.sliderPressed.connect(editor.slider_begin);self.opacity.valueChanged.connect(self.opacity_preview);self.opacity.sliderReleased.connect(lambda:QTimer.singleShot(0,lambda:editor.slider_commit('opacity')))
        if row['type'] in ('Image','Artwork','Paint'):
            add=icon_button('+','Add inside '+row['name'],lambda:editor.row_add_menu(self.identity));add.setEnabled(not inherited);line.addWidget(add)
        lock=icon_button('⛓' if inherited else '🔒' if row['locked'] else '🔓','Protected by ancestor Group' if inherited else 'Group lock protects subtree' if row['type']=='Group' else 'Lock own content and transforms only',lambda:QTimer.singleShot(0,lambda:editor.row_flag(self.identity,'locked')));lock.setEnabled(not inherited);line.addWidget(lock)
        if self.identity in editor.expanded:outer.addWidget(InlineControls(editor,row))
        self.setStyleSheet('LayerRow {border-bottom:1px solid #344049;}')
    def update_thumbnail(self,image):
        self.thumb.setPixmap(QPixmap.fromImage(image.scaled(28,24,Qt.KeepAspectRatio,Qt.SmoothTransformation)))
    def opacity_preview(self,value):
        e=self.editor;row=lookup(e.config).get(self.identity)
        if not row or effective(e.config,row,'locked'):return
        if e.slider_before is None:e.slider_begin()
        row['opacity']=value/100;self.percent.setText(str(value)+'%');e.schedule_preview();e.canvas.update()
        if not self.opacity.isSliderDown():QTimer.singleShot(0,lambda:e.slider_commit('opacity'))


class LayerTree(QTreeWidget):
    def __init__(self,editor):
        super().__init__();self.editor=editor;self.setHeaderLabels(['Layers • front at top']);self.setDragDropMode(QTreeWidget.DragDrop);self.setDefaultDropAction(Qt.MoveAction);self.setSelectionMode(QTreeWidget.ExtendedSelection);self.setDropIndicatorShown(True);self.itemClicked.connect(lambda item,column:None)
        self.header().setStretchLastSection(False);self.header().setSectionResizeMode(0,QHeaderView.Stretch);self.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)
    def toggle_flag(self,item,column):
        if column not in (1,2,3):return
        identity=item.data(0,Qt.UserRole)
        # An ACK rebuilds the tree; never destroy a clicked item inside Qt's
        # itemClicked emission or retain that C++ item across the event boundary.
        QTimer.singleShot(0,lambda:self.apply_flag(identity,column))
    def apply_flag(self,identity,column):
        if not self.editor.resolve_pending():return
        row=lookup(self.editor.config).get(identity)
        if row:
            before=deepcopy(self.editor.config);key='enabled' if column==1 else 'locked' if column==2 else 'source_visible';row[key]=not row[key];self.editor.commit('Layer '+key,before)
    def dropEvent(self,event):
        if event.mimeData().hasFormat('application/x-zerawave-assets'):
            node=self.itemAt(event.position().toPoint());identity=node.data(0,Qt.UserRole) if node else None
            payload=bytes(event.mimeData().data('application/x-zerawave-assets'));event.acceptProposedAction()
            QTimer.singleShot(0,lambda:self.editor.library_drop(payload,identity));return
        if any(effective(self.editor.config,lookup(self.editor.config)[item.data(0,Qt.UserRole)],'locked') for item in self.selectedItems()):event.ignore();return
        before=deepcopy(self.editor.config);super().dropEvent(event)
        def scan(parent_item,parent):
            items=[parent_item.child(i) for i in range(parent_item.childCount())] if parent_item else [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
            for order,item in enumerate(reversed(items)):
                identity=item.data(0,Qt.UserRole);row=lookup(self.editor.config)[identity]
                if parent is not None and any(a['type']=='Group' and a['locked'] for a in [lookup(self.editor.config)[parent]]+ancestors(self.editor.config,parent)) and row['parent']!=parent:raise ValueError('Unlock the protecting Group before reparenting.')
                changed=row['parent']!=parent or row['order']!=order
                if row['parent']!=parent:reparent(self.editor.config,identity,parent)
                row['order']=order
                if changed:row['cut_alignment']=None
                scan(item,identity)
        try:scan(None,None);validate_scene(self.editor.config);self.editor.commit('Reorder / reparent layers',before=before)
        except ValueError as exc:self.editor.config=before;self.editor.status.setText(str(exc));self.editor.populate()
    def dragEnterEvent(self,event):
        if event.mimeData().hasFormat('application/x-zerawave-assets'):event.acceptProposedAction();return
        super().dragEnterEvent(event)
    def dragMoveEvent(self,event):
        if event.mimeData().hasFormat('application/x-zerawave-assets'):
            node=self.itemAt(event.position().toPoint());row=lookup(self.editor.config).get(node.data(0,Qt.UserRole)) if node else None
            self.editor.status.setText('Drop '+('onto '+row['name']+' to choose child / sibling placement' if row else 'into Layers to add at top level')+'; native options can be cancelled.');event.acceptProposedAction();return
        super().dragMoveEvent(event)
    def keyPressEvent(self,event):
        if self.editor.editor_key(event):event.accept();return
        super().keyPressEvent(event)

class CompositionEditor(QMainWindow):
    def __init__(self,layers):
        super().__init__();self.layers=layers;layers.editor_view=self;central=QWidget();self.setCentralWidget(central);layout=QVBoxLayout(central);layout.setContentsMargins(0,0,0,0)
        self.canvas=Canvas(layers);layers.canvas=self.canvas;layout.addWidget(self.canvas,1)
        bar=QToolBar('Composition tools',self);bar.setObjectName('composition_tools');bar.setMovable(True);bar.setFloatable(True);bar.setAllowedAreas(Qt.AllToolBarAreas);bar.setToolTip('Drag the dotted grip to float or redock this toolbar');self.addToolBar(Qt.TopToolBarArea,bar);self.toolbar=bar
        layers.direct_buttons={}
        for tool,key in (('Brush','B'),('Pencil','P'),('Sampler','I'),('Eraser','E'),('Smudge','U'),('Select','V'),('Crop','C'),('Cut','K')):
            button=DirectToolButton(layers,tool,tool+' ('+key+')');layers.direct_buttons[tool]=button;bar.addWidget(button)
        bar.addSeparator()
        for tool in ('Hand','Zoom'):
            button=DirectToolButton(layers,tool,tool+' view tool');layers.direct_buttons[tool]=button;bar.addWidget(button)
        bar.addWidget(icon_button('▨','Fill selected own editable pixels',layers.solid_fill));bar.addWidget(icon_button('?','Shortcut reference',layers.shortcut_reference))
        self.info=QLabel('Canvas Undo: selected layer drawing. Layers Undo: management, transforms, crop and masks.');self.info.setWordWrap(True);layout.addWidget(self.info)
        layers.target_status=QLabel();layers.target_status.setWordWrap(True);layout.addWidget(layers.target_status)
        saved=layers.shell.preferences.get('composition_toolbar')
        if saved:
            from PySide6.QtCore import QByteArray
            self.restoreState(QByteArray.fromHex(saved.encode()))
        bar.topLevelChanged.connect(lambda floating:layers.shell.preferences.update(composition_toolbar=bytes(self.saveState().toHex()).decode()))
        bar.orientationChanged.connect(lambda orientation:layers.shell.preferences.update(composition_toolbar=bytes(self.saveState().toHex()).decode()))
        layers.sync_tool_ui()
    def tool(self,name):
        if not self.layers.resolve_pending():return
        self.canvas.set_tool(name)
    def fit(self):self.canvas.zoom=None;self.canvas.pan=QPointF();self.canvas.update()
    def actual(self):
        canvas=self.canvas;row=canvas.editor.selected_row();canvas.zoom=1./canvas.devicePixelRatioF();canvas.pan=QPointF()
        if row and row['type']!='Group':
            meta=canvas.editor.metadata(row);width,height=meta.get('width'),meta.get('height')
            if width and height:
                w,h=canvas.canvas_size;c=row['crop'];m=canvas.source_matrix(row)
                pixels=np.diag([w,h])@m[:2,:2]@np.diag([1/(width*(c[2]-c[0])),1/(height*(c[3]-c[1]))])
                # Preserve authored deformation; the least magnified direction
                # reaches native detail, rather than merely 100% canvas zoom.
                canvas.zoom/=max(1e-9,float(np.linalg.svd(pixels,compute_uv=False)[-1]))
                canvas.pan=QPointF(-w*m[0,2]*canvas.zoom,-h*m[1,2]*canvas.zoom)
        canvas.update()

class Layers(QWidget):
    def __init__(self,shell):
        super().__init__();self.shell=shell;self.config=defaults();self.binding=None;self.selected=None;self.syncing=False;self.canvas=None;self.images={};self.models={};self.model_keys={};self.image_jobs={};self.image_errors={};self.reader=FrameReader();self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Editor native artwork');self.canvas_size=(1280,720);self.before=None;self.asset_key=None;self.collapsed=set();self.numeric_before=None;self.preview_active=False;self.art_jobs=[];self.drops=[];self.color_target='Brush';self.tool_states={t:dict(brush=dict(size=12.,opacity=1.,strength=.5,shape='Round',hardness=.8,flow=.5),color=QColor('#f6c490')) for t in ('Brush','Pencil','Eraser','Smudge')};self.tool_states['Pencil']['brush']['shape']='Square';self.sample_scope='Active Layer';self.pending_paint=None;self.queued_paint=None;self.palettes=[];self.onboarding_pending=False
        for t,values in shell.preferences.get('media_tool_settings',{}).items():
            if t in self.tool_states:self.tool_states[t]['brush'].update(values.get('brush',{}));self.tool_states[t]['color']=QColor(values.get('color','#f6c490'))
        self.preview_timer=QTimer(self);self.preview_timer.setSingleShot(True);self.preview_timer.setInterval(50);self.preview_timer.timeout.connect(self.send_preview)
        self.numeric_timer=QTimer(self);self.numeric_timer.setSingleShot(True);self.numeric_timer.setInterval(350);self.numeric_timer.timeout.connect(self.numeric_finish)
        outer=QVBoxLayout(self);outer.setContentsMargins(8,8,8,8);self.presentation=QComboBox();self.presentation.addItems(PRESENTATIONS);self.presentation.currentTextChanged.connect(lambda value:self.change_presentation(value));outer.addWidget(self.presentation)
        row=QHBoxLayout();outer.addLayout(row)
        for label,callback in (('+',self.add_menu),('Duplicate',self.duplicate),('Delete',self.delete)):
            b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
        self.child_button=QPushButton('+ Add layer ▾');self.child_button.setToolTip('New blank raster above / inside the selection, import media, or cut selected own pixels • 32 layers / six levels.');self.child_button.clicked.connect(self.child_menu);self.child_button.hide()
        self.expanded=set();self.tree=LayerTree(self);outer.addWidget(self.tree,1);self.tree.itemSelectionChanged.connect(self.tree_select);self.tree.setContextMenuPolicy(Qt.CustomContextMenu);self.tree.customContextMenuRequested.connect(self.context);self.tree.itemCollapsed.connect(lambda item:self.collapsed.add(item.data(0,Qt.UserRole)));self.tree.itemExpanded.connect(lambda item:self.collapsed.discard(item.data(0,Qt.UserRole)));self.tree.setAutoScroll(True);self.tree.setAutoExpandDelay(550)
        details=QWidget(self);details.hide();detail_layout=QVBoxLayout(details);self.legacy_details=details
        self.controls=QGroupBox('Selected layer');self.controls.setCheckable(True);self.controls.setChecked(True);body=QWidget();form=QFormLayout(body);layout=QVBoxLayout(self.controls);layout.addWidget(body);self.controls.toggled.connect(body.setVisible);detail_layout.addWidget(self.controls)
        self.name=QLineEdit();self.name.setMaxLength(128);self.name.editingFinished.connect(lambda:self.edit('name',self.name.text(),'Rename layer'));form.addRow('Name',self.name)
        self.visible=QCheckBox('Entire branch visible');self.locked=QCheckBox('Locked');self.visible.toggled.connect(lambda v:self.edit('enabled',v,'Layer visibility',allow_locked=True));self.locked.toggled.connect(lambda v:self.edit('locked',v,'Layer lock',allow_locked=True));flags=QHBoxLayout();flags.addWidget(self.visible);flags.addWidget(self.locked);form.addRow(flags)
        self.original=QCheckBox('Own content visible');self.original.toggled.connect(lambda v:self.edit('source_visible',v,'Original image visibility'));form.addRow(self.original)
        self.dimensions=QLabel();self.dimensions.setWordWrap(True);form.addRow(self.dimensions)
        sections=QGridLayout();form.addRow(sections);self.sections={};self.section_buttons={};self.section_forms={}
        for i,(name,glyph) in enumerate((('Position','✥'),('Scale','⤢'),('Flip & Rotate','⟳'),('Align','⊞'),('Blend','◐'),('Selection','✂'))):
            content=QWidget();sf=QFormLayout(content);sf.setContentsMargins(0,4,0,4);sf.setRowWrapPolicy(QFormLayout.WrapLongRows);content.hide();self.sections[name]=content;self.section_forms[name]=sf
            button=icon_button(glyph,name+' controls',lambda checked=False,n=name:self.toggle_section(n));button.setCheckable(True);sections.addWidget(button,i//6,i%6);self.section_buttons[name]=button
            button.setStyleSheet('QToolButton:checked {border-bottom:2px solid #e0aa78;background:#302b25;}');button.setToolTip(name+' section (expanded highlight is not an active tool)')
        for content in self.sections.values():form.addRow(content)
        tools=QHBoxLayout();form.addRow(tools);tools.addStretch()
        form=self.section_forms['Blend'];self.blend=QComboBox();self.blend.addItems(BLENDS);self.blend.currentTextChanged.connect(lambda v:self.edit('blend',v,'Layer blend'));form.addRow('Mode',self.blend)
        self.strength=GestureSpin();self.strength.setRange(0,100);self.strength.setDecimals(1);self.strength.setSuffix(' %');self.strength.setToolTip('0% uses Normal source-over; 100% uses the saved blend. Opacity is separate.');self.strength.valueChanged.connect(lambda v:self.numeric('blend_strength'));self.strength.finished.connect(self.numeric_finish);form.addRow('Strength',self.strength)
        form=self.section_forms['Scale'];self.fit=QComboBox();self.fit.addItems(['Fit','Fill','Stretch']);self.fit.currentTextChanged.connect(lambda v:self.fit_action(v));form.addRow('Fit / Cover / Stretch',self.fit)
        fitbutton=QPushButton('Fit artwork to canvas');fitbutton.setToolTip('Centres artwork, removes its rotation/scale, compensates inherited transforms; retains crop/masks/source.');fitbutton.clicked.connect(lambda:self.fit_action('Fit'));form.addRow(fitbutton)
        self.aspect=QCheckBox('Keep aspect');self.aspect.toggled.connect(lambda v:self.edit('aspect_lock',v,'Aspect lock'));form.addRow(self.aspect)
        self.fields={}
        for key,label,low,high in (('x','X %',-10000,10000),('y','Y %',-10000,10000),('scale','Scale X %',1,10000),('scale_y','Scale Y %',1,10000),('width','Local width px',.1,100000),('height','Local height px',.1,100000),('rotation','Rotation °',-36000,36000),('opacity','Opacity %',0,100)):
            form=self.section_forms['Position' if key in ('x','y') else 'Scale' if key in ('scale','scale_y','width','height') else 'Flip & Rotate' if key=='rotation' else 'Blend']
            spin=GestureSpin();spin.setDecimals(1);spin.setSingleStep(.1);spin.setRange(low,high);spin.valueChanged.connect(lambda value,k=key:self.numeric(k));spin.editingFinished.connect(self.numeric_finish);spin.finished.connect(self.numeric_finish);form.addRow(label,spin);self.fields[key]=spin
        self.sliders={};self.slider_before=None
        for key,label,low,high in (('scale','Scale %',10,10000),('opacity','Opacity %',0,1000)):
            form=self.section_forms['Scale' if key=='scale' else 'Blend']
            slider=QSlider(Qt.Horizontal);slider.setRange(low,high);slider.setToolTip('Drag previews locally; release commits one Undo command. Numeric fields retain the full range and precision.');slider.sliderPressed.connect(lambda:self.slider_begin());slider.valueChanged.connect(lambda v,k=key:self.slider_preview(k,v));slider.sliderReleased.connect(lambda k=key:self.slider_commit(k));form.addRow(label,slider);self.sliders[key]=slider
        form=self.section_forms['Flip & Rotate'];row=QHBoxLayout();form.addRow(row)
        for label,callback in (('↔',lambda:self.flip('flip_x')),('↕',lambda:self.flip('flip_y')),('−90°',lambda:self.rotate(-90)),('+90°',lambda:self.rotate(90)),('Reset',self.reset)):
            b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
        form=self.section_forms['Align'];row=QHBoxLayout();form.addRow(row)
        for label,callback in (('Front',lambda:self.reorder(True)),('Back',lambda:self.reorder(False)),('Align…',self.align_menu)):
            b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
            if label=='Align…':self.align_button=b
        form=self.section_forms['Selection'];self.mask_list=QComboBox();form.addRow('Masks / cuts',self.mask_list);row=QHBoxLayout();form.addRow(row)
        for label,callback in (('Edit points',self.edit_mask),('Enable / disable',self.toggle_mask),('Remove mask',self.remove_mask)):
            b=QPushButton(label);b.clicked.connect(callback);row.addWidget(b)
        self.animation=QGroupBox('Playback');af=QFormLayout(self.animation);detail_layout.addWidget(self.animation);row=QHBoxLayout();af.addRow(row)
        for label,op in (('▶','play'),('Ⅱ','pause'),('■','stop')):
            b=QPushButton(label);b.setToolTip(op.title());b.clicked.connect(lambda checked=False,o=op:self.transport(o));row.addWidget(b)
        self.time=QLabel();af.addRow(self.time);self.seek=QSlider(Qt.Horizontal);self.seek.setRange(0,10000);self.seek.sliderReleased.connect(lambda:self.transport('seek',self.seek.value()/10000*self.duration()));af.addRow('Position',self.seek)
        self.rate=GestureSpin();self.rate.setRange(.1,12.);self.rate.setSingleStep(.1);self.rate.valueChanged.connect(lambda v:self.numeric('rate'));self.rate.editingFinished.connect(self.numeric_finish);self.rate.finished.connect(self.numeric_finish);af.addRow('Rate',self.rate)
        self.loop=QComboBox();self.loop.addItems(['None','Loop','Ping-pong']);self.loop.currentTextChanged.connect(lambda v:self.media_edit('loop',v));af.addRow('Loop',self.loop)
        self.in_point=QDoubleSpinBox();self.out_point=QDoubleSpinBox()
        for label,widget,key in (('In s',self.in_point,'start'),('Out s',self.out_point,'end')):
            widget.setDecimals(3);widget.setRange(0,86400);widget.setKeyboardTracking(False);widget.editingFinished.connect(lambda w=widget,k=key:self.media_edit(k,w.value()));af.addRow(label,widget)
        self.sprite=QGroupBox('Sprite sheet');sf=QFormLayout(self.sprite);detail_layout.addWidget(self.sprite);self.sprite_fields={}
        hint=QLabel('Advanced: an evenly spaced frame grid. Example: 4 columns × 2 rows, First 0, Last 7, 12 fps; frames read left to right, then downward. A normal portrait needs an Image layer, not a sheet.');hint.setWordWrap(True);sf.addRow(hint)
        for key,high in (('columns',64),('rows',64),('first',4095),('last',4095),('fps',120)):
            spin=QDoubleSpinBox() if key=='fps' else QSpinBox();spin.setRange(.1 if key=='fps' else 0 if key in ('first','last') else 1,high);spin.setKeyboardTracking(False);spin.editingFinished.connect(lambda w=spin,k=key:self.media_edit(k,w.value()));sf.addRow(key.title(),spin);self.sprite_fields[key]=spin
        self.model_box=QGroupBox('Static 3D orientation');mf=QFormLayout(self.model_box);detail_layout.addWidget(self.model_box);self.model_fields={}
        for key in ('yaw','pitch','roll'):
            spin=QDoubleSpinBox();spin.setRange(-36000,36000);spin.setDecimals(1);spin.setSingleStep(.1);spin.setKeyboardTracking(False);spin.editingFinished.connect(lambda k=key,w=spin:self.model_edit(k,w.value()));mf.addRow(key.title()+' °',spin);self.model_fields[key]=spin
        hint=QLabel('Editor shows a bounded geometry guide (up to 4,000 triangles); Visualizer renders the complete supported mesh/materials. Static glTF/GLB only.');hint.setWordWrap(True);mf.addRow(hint)
        from studio_web_layer import WebSources
        self.web_sources=WebSources(self);self.web_box=QGroupBox('Read-only web source');wf=QFormLayout(self.web_box);detail_layout.addWidget(self.web_box)
        self.web_url=QLineEdit();self.web_url.setMaxLength(2048);self.web_url.editingFinished.connect(lambda:self.web_edit('url',self.web_url.text()));wf.addRow('HTTPS URL',self.web_url);self.web_fields={}
        for key,low,high in (('width',64,2048),('height',64,2048),('cadence',5,3600)):
            spin=QSpinBox();spin.setRange(low,high);spin.setKeyboardTracking(False);spin.editingFinished.connect(lambda w=spin,k=key:self.web_edit(k,w.value()));wf.addRow(key.title()+(' s' if key=='cadence' else ' px'),spin);self.web_fields[key]=spin
        self.web_offline=QComboBox();self.web_offline.addItems(['Retain last','Hide']);self.web_offline.currentTextChanged.connect(lambda v:self.web_edit('offline',v));wf.addRow('Offline',self.web_offline);self.web_transparent=QCheckBox('Transparent where the page supports it');self.web_transparent.toggled.connect(lambda v:self.web_edit('transparent',v));wf.addRow(self.web_transparent)
        buttons=QHBoxLayout();wf.addRow(buttons)
        for label,callback in (('Load / Reload',self.web_start),('Stop browser',self.web_sources.stop)):
            b=QPushButton(label);b.clicked.connect(callback);buttons.addWidget(b)
        self.status=EditorStatus('32 layers • 6 group levels • 4 active animated layers');self.status.setWordWrap(True);outer.addWidget(self.status)
        row=QHBoxLayout();outer.addLayout(row);self.undo=QPushButton('Undo');self.redo=QPushButton('Redo');self.undo.clicked.connect(lambda:self.history(False));self.redo.clicked.connect(lambda:self.history(True));row.addWidget(self.undo);row.addWidget(self.redo)
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.frames);self.timer.start()
    def resolve_pending(self):
        self.numeric_finish()
        if self.art_jobs:
            self.status.setText('Wait for the pending artwork write before switching, saving or closing.');return False
        if self.canvas and self.canvas.stroke:self.canvas.cancel_drag()
        if not self.canvas or not self.canvas.points or self.canvas.tool=='Selection':return True
        answer=QMessageBox.question(self,'Unfinished '+self.canvas.tool.lower(),'Apply this preview, discard it, or keep editing?',QMessageBox.Apply|QMessageBox.Discard|QMessageBox.Cancel)
        if answer==QMessageBox.Cancel:return False
        if answer==QMessageBox.Apply:self.canvas.apply();return not self.canvas.points
        self.canvas.discard();return True
    def selected_row(self):return lookup(self.config).get(self.selected)
    def focus_pane(self,widget):
        layers=widget is self or widget is not None and self.isAncestorOf(widget)
        canvas=widget is not None and (self.editor_view.isAncestorOf(widget) or any(p is widget.window() for p in self.palettes))
        state=(bool(layers),bool(canvas))
        if state==getattr(self,'focus_state',None):return
        self.focus_state=state
        self.setAttribute(Qt.WA_StyledBackground,True);self.setObjectName('layers_focus')
        self.setProperty('keyboardActive',bool(layers));self.editor_view.setProperty('keyboardActive',bool(canvas))
        self.setStyleSheet('#layers_focus[keyboardActive="true"] {border:2px solid #b79ee8;} #layers_focus[keyboardActive="false"] {border:2px solid transparent;}')
        central=self.editor_view.centralWidget();central.setAttribute(Qt.WA_StyledBackground,True);central.setObjectName('composition_focus');central.setProperty('keyboardActive',bool(canvas))
        central.setStyleSheet('#composition_focus[keyboardActive="true"] {border:2px solid #b79ee8;} #composition_focus[keyboardActive="false"] {border:2px solid transparent;}')
    def editable_target(self,row):
        reason='hidden artwork/subtree' if not effective(self.config,row,'enabled') else 'locked artwork/subtree' if effective(self.config,row,'locked') else None
        if reason is None and any(r['opacity']==0 for r in [row]+ancestors(self.config,row['id'])):reason='zero-opacity artwork/subtree'
        if reason:self.status.setText(row['name']+': '+reason+'. Show/unlock it before editing.');return False
        return True
    def valid_target(self,session,revision,target):
        media=self.shell.client.snapshot.get('media_control',{});current=lookup(self.shell.client.snapshot.get('values',{}).get('media',self.config)).get(target['id'])
        return media.get('session')==session and media.get('revision')==revision and current==target
    def sync_tool_ui(self):
        if not self.canvas:return
        shown='Select' if self.canvas.tool=='Selection' else 'Cut' if self.canvas.tool in ('Mask','Remove','Extract') else self.canvas.tool
        for tool,button in getattr(self,'direct_buttons',{}).items():button.setChecked(tool==shown)
        self.sync_saved_masks();self.sync_settings_values()
        for button,tool,shape in getattr(self,'tool_buttons',[]):button.setChecked(self.canvas.tool==tool if shape is None else self.canvas.shape==shape and self.canvas.tool in ('Selection','Mask','Remove','Cut','Extract'))
        if hasattr(self,'color_swatch'):self.color_swatch.setStyleSheet('background:'+self.brush_color.name()+'; color:'+('#10171c' if self.brush_color.lightness()>128 else '#ffffff'));self.color_swatch.setText(self.brush_color.name())
        for key,box in getattr(self,'brush_boxes',{}).items():box.setVisible(self.canvas.tool in ('Brush','Pencil','Eraser','Smudge') and (key!='strength' or self.canvas.tool=='Smudge') and (key not in ('hardness','flow') or self.canvas.tool in ('Brush','Eraser')))
        for button,key,value in getattr(self,'preset_buttons',[]):button.setChecked(self.brush[key]==value)
        row=self.selected_row()
        if hasattr(self,'target_status'):
            state='No editing target' if row is None else row['name']+' • '+('hidden subtree' if not effective(self.config,row,'enabled') else 'locked' if effective(self.config,row,'locked') else row['type'])
            if row and not row['source_visible']:state+=' • own content hidden; children remain independent'
            if row:state+=' • own raster pixels' if row['type'] in ('Image','Artwork','Paint') else ' • layer branch'
            if self.canvas.points:state+=' • clipboard targets selected own pixels'
            if row and self.canvas.tool in ('Brush','Pencil','Eraser','Smudge') and row['type'] not in ('Image','Artwork','Paint'):state+=' • drawing requires still artwork'
            if row and row['type'] in ('Image','Artwork','Paint') and self.canvas.source_image(row) is None:state+=' • source pixels unavailable'
            self.target_status.setText(self.canvas.tool+(' / '+self.canvas.shape if self.canvas.tool in ('Selection','Mask','Remove','Cut','Extract') else '')+' → '+state)
    def media_assets(self):
        data=self.shell.client.snapshot.get('media_library',{});return data.get('assets',[])+data.get('resources',[])
    def metadata(self,row):
        asset=next((a for a in self.media_assets() if a['id']==row['asset']),{})
        frame=self.shell.client.snapshot.get('media_frames',{}).get(row['id'],{}).get('frame') or {}
        result=dict(asset.get('metadata',{}),**frame);image=self.images.get(row['asset']) or self.images.get(row['id'])
        if image is not None:result.setdefault('width',image.width());result.setdefault('height',image.height())
        return result
    def refresh(self,force=False):
        snap=self.shell.client.snapshot;media=snap.get('media_control',{});binding=(media.get('session'),media.get('revision'))
        size=snap.get('preview',{}).get('dimensions',{}).get('internal')
        policy=snap.get('resolution',{}).get('policy')
        if size is None and policy and policy.get('mode')=='fixed':size=policy.get('size')
        prior_size=self.canvas_size;self.canvas_size=tuple(self.config.get('canvas') or size or (1280,720))
        if self.canvas and self.canvas_size!=prior_size:self.canvas.update()
        if force or binding!=self.binding:
            if self.canvas and (self.canvas.drag or self.canvas.stroke or self.canvas.interactive) or self.slider_before is not None or self.numeric_before is not None:return
            session_changed=self.binding and binding[0]!=self.binding[0]
            if session_changed and self.canvas:self.canvas.discard()
            self.binding=binding;self.config=deepcopy(snap['values'].get('media',defaults()))
            self.config=validate_scene(self.config);selection=media.get('history',{}).get('selection')
            self.canvas_size=tuple(self.config.get('canvas') or size or (1280,720))
            if selection!=getattr(self,'history_selection',None) or session_changed:
                if selection in lookup(self.config) or selection is None:
                    self.selected=selection;self.tree.blockSignals(True);self.tree.clearSelection();self.tree.blockSignals(False)
            self.history_selection=selection
            if self.selected not in lookup(self.config):self.selected=None
            self.populate();self.sync_controls()
            if self.canvas:self.canvas.update()
        history=media.get('history',{})
        for button,key in ((self.undo,'undo'),(self.redo,'redo')):button.setEnabled(bool(history.get(key)));button.setText(key.title()+(' '+history[key] if history.get(key) else ''))
        row=self.selected_row();state=snap.get('media_frames',{}).get(self.selected,{})
        decode=(state.get('frame') or {}).get('decode_ms',0.)
        self.time.setText(f"{state.get('position',0):.2f} / {self.duration():.2f} s • {'Playing' if state.get('playing') else 'Paused'} • muted"+(f'\nDecode/refill {decode:.0f} ms • '+('slow source: frames skipped; reverse may stall' if decode>100 else 'high rates skip source frames') if row and row['type']=='Video' else ''))
        if not self.seek.isSliderDown():self.seek.setValue(round(state.get('position',0)/max(.001,self.duration())*10000))
        asset=next((a for a in self.media_assets() if row and a['id']==row['asset']),None)
        source_error=(asset.get('error') if asset else 'Reference removed; cached pixels may remain. Undo or Relink to recover.' if row and row['asset'] else '')
        error=state.get('error') or snap.get('preview',{}).get('image_layers',{}).get('error') or self.image_errors.get(row['asset'] if row else None,'') or source_error
        self.status.routine(error or 'Layers Undo: management / transforms / crop / masks • Drawing Undo: canvas, current layer only')
        self.load_images()
    def populate(self):
        focus=QApplication.focusWidget();focus_name=focus.objectName() if focus else '';cursor=focus.cursorPosition() if isinstance(focus,QLineEdit) else None
        if not focus_name and isinstance(focus,QLineEdit) and focus.parentWidget():focus_name=focus.parentWidget().objectName()
        selected_ids={item.data(0,Qt.UserRole) for item in self.tree.selectedItems()};scroll=self.tree.verticalScrollBar().value();self.rebuilding=True;self.tree.blockSignals(True);self.tree.clear()
        self.row_widgets={};self.row_items={}
        def children(parent,item=None):
            for row in sorted((r for r in self.config['layers'] if r['parent']==parent),key=lambda r:r['order'],reverse=True):
                node=QTreeWidgetItem();node.setData(0,Qt.UserRole,row['id']);node.setToolTip(0,row['name']+' • '+row['type']+' • '+row['id'])
                if row['type'] not in ('Group','Image','Artwork','Paint'):node.setFlags(node.flags() & ~Qt.ItemIsDropEnabled)
                if effective(self.config,row,'locked'):node.setFlags(node.flags() & ~Qt.ItemIsDragEnabled)
                # Ordinary locked parents still accept editable descendants.
                if any(a['type']=='Group' and a['locked'] for a in [row]+ancestors(self.config,row['id'])):node.setFlags(node.flags() & ~Qt.ItemIsDropEnabled)
                (item.addChild if item else self.tree.addTopLevelItem)(node);widget=LayerRow(self,row);self.tree.setItemWidget(node,0,widget);node.setSizeHint(0,widget.sizeHint());self.row_widgets[row['id']]=widget;self.row_items[row['id']]=node
                children(row['id'],node);node.setExpanded(row['id'] not in self.collapsed)
                node.setSelected(row['id'] in selected_ids)
                if row['id']==self.selected:self.tree.setCurrentItem(node,0, __import__('PySide6.QtCore',fromlist=['QItemSelectionModel']).QItemSelectionModel.NoUpdate)
        children(None)
        if self.selected in self.row_items and not selected_ids:self.row_items[self.selected].setSelected(True)
        self.tree.blockSignals(False);self.tree.verticalScrollBar().setValue(scroll);self.rebuilding=False
        if focus_name.startswith('layer_'):
            replacement=self.tree.findChild(QWidget,focus_name)
            if replacement is not None and replacement.isEnabled():
                replacement.setFocus(Qt.OtherFocusReason)
                if isinstance(replacement,QLineEdit) and cursor is not None:replacement.setCursorPosition(min(cursor,len(replacement.text())))
    def expand_row(self,identity):
        if not self.resolve_pending():return
        if identity in self.expanded:self.expanded.remove(identity)
        else:self.expanded.add(identity)
        self.populate()
    def bound_action(self,identity,callback):
        def run():
            self.select(identity)
            if self.selected==identity:callback()
        QTimer.singleShot(0,run)
    def row_edit(self,identity,key,value,label):
        if self.syncing or not self.resolve_pending():return
        row=lookup(self.config).get(identity)
        if not row or effective(self.config,row,'locked'):self.status.setText('Unlock this layer or its protecting Group first.');return
        if row[key]==value:return
        before=deepcopy(self.config);row[key]=value;self.commit(label,before)
    def row_flag(self,identity,key):
        if not self.resolve_pending():return
        row=lookup(self.config).get(identity)
        if not row:return
        if key=='locked' and any(a['type']=='Group' and a['locked'] for a in ancestors(self.config,identity)):self.status.setText('Unlock the protecting Group first; individual lock choices are preserved.');return
        before=deepcopy(self.config);row[key]=not row[key];self.commit('Layer '+key,before)
    def row_add_menu(self,identity):
        menu=QMenu(self);menu.addAction('Media Library',lambda:self.library_inside(identity));menu.addAction('New Layer',lambda:self.bound_action(identity,lambda:self.blank_layer(True)));menu.addAction('Web Source',lambda:self.bound_action(identity,lambda:self.web(True)));menu.exec(QCursor.pos())
    def library_inside(self,identity):
        self.library_target=identity;self.shell.panels['media'].toggleView(True);self.shell.panels['media'].setAsCurrentTab();self.status.setText('Drag a Library asset onto '+lookup(self.config)[identity]['name']+' to add inside it.')
    def library_drop(self,payload,identity):
        if not self.resolve_pending():return
        try:ids=json.loads(payload)
        except (ValueError,TypeError):self.status.setText('Invalid Library drag payload; unchanged.');return
        row=lookup(self.config).get(identity);parent=None
        if row:
            labels=['Inside '+row['name'],'Above '+row['name'],'Top level'] if row['type'] in ('Group','Image','Artwork','Paint') else ['Above '+row['name'],'Top level']
            choice,ok=QInputDialog.getItem(self,'Place Library asset','Drop destination (Cancel keeps composition unchanged)',labels,0,False)
            if not ok:return
            parent=row['id'] if choice.startswith('Inside') else row['parent'] if choice.startswith('Above') else None
            if parent and any(a['type']=='Group' and a['locked'] for a in [lookup(self.config)[parent]]+ancestors(self.config,parent)):self.status.setText('Unlock the protecting Group before inserting.');return
        assets={a['id']:a for a in self.media_assets()};records=[assets[i] for i in dict.fromkeys(ids) if i in assets]
        if len(records)!=len(set(ids)):self.status.setText('A dragged asset is unavailable; unchanged.');return
        if len(records)+len(self.config['layers'])>MAX_LAYERS:self.status.setText('Drop exceeds 32 layers; unchanged.');return
        # Native workflow is reused per reference. Cancellation affects only the
        # unplaced reference; completed earlier placements remain recoverable.
        for asset in records:
            placement=dict(parent=parent,above=row['id'] if row and choice.startswith('Above') else None)
            self.add_asset(asset,another=True,offer=True,placement=placement)
    def select(self,identity):
        if identity!=self.selected and self.canvas and self.canvas.tool=='Selection':self.canvas.discard()
        if identity!=self.selected and not self.resolve_pending():self.populate();return
        if identity not in {i.data(0,Qt.UserRole) for i in self.tree.selectedItems()}:
            self.tree.blockSignals(True);self.tree.clearSelection();self.tree.blockSignals(False)
        self.selected=identity;self.last_selection=identity;self.populate();self.sync_controls()
        if self.canvas:self.canvas.update()
    def tree_select(self):
        item=self.tree.currentItem();identity=item.data(0,Qt.UserRole) if item else None
        pending=self.art_jobs or self.numeric_before is not None or self.canvas and (self.canvas.points or self.canvas.stroke)
        if identity!=self.selected and self.canvas and self.canvas.tool=='Selection':self.canvas.discard();pending=False
        if identity!=self.selected and pending:QTimer.singleShot(0,lambda:self.select(identity));return
        if identity!=self.selected and self.canvas and self.canvas.tool=='Selection':self.canvas.discard()
        if identity!=self.selected and not self.resolve_pending():self.populate();return
        self.selected=identity;self.last_selection=identity;self.sync_controls()
        if self.canvas:self.canvas.update()
    def sync_controls(self):
        self.syncing=True;row=self.selected_row();self.controls.setEnabled(row is not None);self.animation.setVisible(bool(row and row['type'] in ('Video','GIF','Sprite')));self.sprite.setVisible(bool(row and row['type']=='Sprite'));self.model_box.setVisible(bool(row and row['type']=='Model'));self.web_box.setVisible(bool(row and row['type']=='Web'))
        self.child_button.setEnabled(True)
        try:
            self.presentation.setCurrentText(self.config['presentation'])
            if row:
                self.original.setVisible(row['type']!='Group');self.original.setChecked(row['source_visible']);self.strength.setValue(row['blend_strength']*100)
                self.name.setText(row['name']);self.visible.setChecked(row['enabled']);self.locked.setChecked(row['locked']);self.blend.setCurrentText(row['blend']);self.fit.setCurrentText(row['fit']);self.aspect.setChecked(row['aspect_lock'])
                x,y,s,sy,r=properties(row['transform'],self.canvas_size[0]/self.canvas_size[1]);values=dict(x=x*100,y=y*100,scale=s*100,scale_y=sy*100,rotation=r,opacity=row['opacity']*100)
                bw,bh=self.base_dimensions(row);values.update(width=bw*s,height=bh*sy)
                meta=self.metadata(row);output=self.shell.client.snapshot.get('preview',{}).get('dimensions',{}).get('internal');self.dimensions.setText(f"Working {meta.get('width','?')} × {meta.get('height','?')} px\nCanvas {self.canvas_size[0]} × {self.canvas_size[1]} • Output {output or 'not running'}")
                for k,w in self.fields.items():w.setValue(values[k]);w.setEnabled(not effective(self.config,row,'locked'))
                for k,w in self.sliders.items():
                    w.blockSignals(True);w.setValue(round(values[k]*10));w.setEnabled(not effective(self.config,row,'locked'));w.blockSignals(False)
                self.fit.setEnabled(row['type']!='Group')
                self.mask_list.clear()
                for i,m in enumerate(row['masks']):self.mask_list.addItem(f"{i+1}: {m['mode']} • {'on' if m['enabled'] else 'off'}")
                self.rate.setValue(row['media']['rate']);self.loop.setCurrentText(row['media']['loop']);self.in_point.setValue(row['media']['start']);self.out_point.setValue(row['media']['end'] or self.duration())
                for k,w in self.sprite_fields.items():w.setValue(row['media'][k])
                for k,w in self.model_fields.items():w.setValue(row['model'][k])
                self.web_url.setText(row['web']['url']);self.web_offline.setCurrentText(row['web']['offline']);self.web_transparent.setChecked(row['web']['transparent'])
                for k,w in self.web_fields.items():w.setValue(row['web'][k])
        finally:self.syncing=False;self.sync_tool_ui()
    def binding_args(self):
        snap=self.shell.client.snapshot
        return dict(media_session=self.binding[0],media_revision=self.binding[1],preview_run=snap.get('preview_run'),destination_revision=snap.get('destination_revision',0))
    def commit(self,label,before=None,scope="layers",target=None):
        if self.syncing or self.binding is None:return False
        prior=before or deepcopy(self.config)
        self.preview_timer.stop()
        try:
            self.config=validate_scene(self.config)
            selection=self.selected if self.selected in lookup(prior) else getattr(self,'last_selection',None)
            self.shell.client.request('composition',version=4,canvas=self.config.get('canvas'),presentation=self.config['presentation'],layers=deepcopy(self.config['layers']),label=label,selection=self.selected,before_selection=selection,history_scope=scope,history_target=target,**self.binding_args());self.preview_active=False
            media=self.shell.client.snapshot['media_control'];self.binding=(media['session'],media['revision'])
        except Exception as exc:self.cancel_preview();self.config=prior;self.status.setText(str(exc));self.populate();self.sync_controls();return False
        self.refresh(True)
        if self.canvas:self.canvas.update()
        return True
    def edit(self,key,value,label,allow_locked=False):
        if self.syncing:return
        row=self.selected_row()
        if not row or effective(self.config,row,'locked') and not allow_locked:return
        before=deepcopy(self.config);row[key]=value;self.commit(label,before)
    def numeric(self,key):
        if self.syncing:return
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        if self.numeric_before is None:self.numeric_before=deepcopy(self.config)
        self.numeric_key=key
        if key=='rate':row['media']['rate']=self.rate.value()
        elif key=='blend_strength':row[key]=self.strength.value()/100
        elif key=='opacity':row['opacity']=self.fields[key].value()/100
        else:
            x,y,s,sy,r=properties(row['transform'],self.canvas_size[0]/self.canvas_size[1]);values=dict(x=x,y=y,scale=s,scale_y=sy,rotation=r)
            if key in ('width','height'):
                bw,bh=self.base_dimensions(row);mapped='scale' if key=='width' else 'scale_y';values[mapped]=self.fields[key].value()/(bw if key=='width' else bh)
                if row['aspect_lock']:values['scale']=values['scale_y']=values[mapped]
            else:values[key]=self.fields[key].value()/(1 if key=='rotation' else 100)
            if row['aspect_lock'] and key in ('scale','scale_y'):values['scale']=values['scale_y']=values[key]
            row['transform']=transform(**values,aspect=self.canvas_size[0]/self.canvas_size[1])
        self.schedule_preview();self.numeric_timer.start()
        if self.canvas:self.canvas.update()
    def numeric_finish(self):
        if self.syncing:return
        self.numeric_timer.stop();before,self.numeric_before=self.numeric_before,None
        if before is not None:self.commit('Layer '+getattr(self,'numeric_key','value'),before)
    def schedule_preview(self):
        if not self.syncing and not self.preview_timer.isActive():self.preview_timer.start()
    def send_preview(self):
        if self.binding is None:return
        try:
            self.shell.client.request('composition_preview',version=4,canvas=self.config.get('canvas'),presentation=self.config['presentation'],layers=deepcopy(self.config['layers']),selection=self.selected,**self.binding_args());self.preview_active=True
            media=self.shell.client.snapshot['media_control'];self.binding=(media['session'],media['revision'])
        except Exception as exc:self.status.setText(str(exc));self.cancel_preview()
    def cancel_preview(self):
        self.preview_timer.stop()
        if self.preview_active and self.binding:
            self.shell.safe(lambda:self.shell.client.request('composition_cancel',media_session=self.binding[0]));self.preview_active=False
            media=self.shell.client.snapshot['media_control'];self.binding=(media['session'],media['revision'])
    def base_dimensions(self,row):
        from composition import fit_size
        meta=self.metadata(row);fw,fh=(1.,1.) if row['type']=='Group' else fit_size(self.canvas_size,(meta.get('width',1)*meta.get('pixel_aspect',1),meta.get('height',1)),row)
        return fw*self.canvas_size[0],fh*self.canvas_size[1]
    def slider_begin(self):self.slider_before=deepcopy(self.config)
    def slider_preview(self,key,value):
        if self.syncing:return
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        if self.slider_before is None:self.slider_begin()
        self.fields[key].blockSignals(True);self.fields[key].setValue(value/10);self.fields[key].blockSignals(False)
        if key=='opacity':row['opacity']=value/1000
        else:
            x,y,s,sy,r=properties(row['transform'],self.canvas_size[0]/self.canvas_size[1]);s=value/1000
            if row['aspect_lock']:sy=s
            row['transform']=transform(x,y,s,sy,r,self.canvas_size[0]/self.canvas_size[1])
        if self.canvas:self.canvas.update()
        self.schedule_preview()
        if not self.sliders[key].isSliderDown():self.slider_commit(key)
    def slider_commit(self,key):
        before,self.slider_before=self.slider_before,None
        if before is not None:self.commit('Layer '+key+' slider',before)
    def change_presentation(self,value):
        if self.syncing:return
        before=deepcopy(self.config);self.config['presentation']=value;self.commit('Composition presentation',before)
    def add_asset(self,asset,another=False,kind=None,offer=False,placement=None):
        if not self.resolve_pending():return False
        self.refresh()
        existing=next((r for r in self.config['layers'] if r['asset']==asset['id'] and (kind is None or r['type']==kind)),None)
        if existing and not another:self.select(existing['id']);self.reveal();return True
        if offer and asset['kind']=='Images' and not asset.get('managed'):
            choice=self.working_options(asset)
            if choice is None:return
            if choice[0] is not None:
                size,canvas=choice;meta=asset['metadata']
                def derivative():
                    from pathlib import Path
                    if Path(asset['path']).stat().st_mtime_ns!=meta['mtime_ns']:raise ValueError('Source changed; refresh it before creating a derivative.')
                    decoded,data=decode_image(asset['path']);return QImage(data,decoded['width'],decoded['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).scaled(*size,Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
                def finish(record):
                    if canvas:self.resize_canvas((meta['width'],meta['height']),False)
                    self.add_asset(record,True,kind,placement=placement)
                self.generated_work(derivative,'Resized derivative '+str(size)+' of '+asset['path'],finish);return
            if choice[1]:self.resize_canvas((asset['metadata']['width'],asset['metadata']['height']),False)
        if len(self.config['layers'])>=MAX_LAYERS:self.status.setText('32-layer limit. Remove an unused layer first.');return
        if asset.get('status')!='Ready':self.status.setText(asset.get('error') or 'Refresh/Relink this unavailable source before use.');return
        if placement:
            parent=placement['parent'];above=placement['above'];rows=lookup(self.config)
            if parent and parent not in rows or above and above not in rows:self.status.setText('Drop destination changed; no layer added.');return False
            if parent and any(a['type']=='Group' and a['locked'] for a in [rows[parent]]+ancestors(self.config,parent)):self.status.setText('Unlock the protecting Group before inserting.');return False
        before=deepcopy(self.config);typ=kind or {'Images':'Image','Video':'Video','Animated':'GIF','Models':'Model'}.get(asset['kind'])
        if typ is None:self.status.setText('Use audio through Session Waveform.');return
        row=new_layer(typ,asset['id'],asset['name']);row['order']=max((r['order'] for r in self.config['layers'] if r['parent'] is None),default=-1)+1;self.config['layers'].append(row)
        if placement:
            if placement['parent']:reparent(self.config,row['id'],placement['parent'])
            if placement['above']:
                siblings=sorted((r for r in self.config['layers'] if r['parent']==placement['parent'] and r['id']!=row['id']),key=lambda r:r['order']);siblings.insert(siblings.index(lookup(self.config)[placement['above']])+1,row)
                for i,r in enumerate(siblings):r['order']=i
        if not any(a['id']==asset['id'] for a in self.config['assets']):self.config['assets'].append({k:asset[k] for k in ('id','kind','name','path')})
        self.selected=row['id'];applied=self.commit('Add '+typ.lower(),before);self.reveal();return applied
    def assign(self,index,asset):
        # Compatibility entry point; dynamic activation is never row-index owned.
        record=next((a for a in self.shell.client.snapshot['media_library']['assets'] if a['id']==asset),None)
        if record:self.add_asset(record)
    def reveal(self):
        for key in ('image_layers','composition'):
            dock=self.shell.panels.get(key)
            if dock:dock.toggleView(True);dock.setAsCurrentTab()
    def add_menu(self):
        menu=QMenu(self);menu.addAction('Media Library',lambda:self.shell.panels['media'].toggleView(True));menu.addAction('New Layer',lambda:self.blank_layer(False));menu.addAction('New Group',self.group);menu.addAction('Web Source',self.web);menu.exec(QCursor.pos())
    def duplicate(self):
        row=self.selected_row()
        if not row or not self.resolve_pending() or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);desc=[row]+[r for r in self.config['layers'] if any(a['id']==row['id'] for a in ancestors(self.config,r['id']))]
        if len(self.config['layers'])+len(desc)>MAX_LAYERS:self.status.setText('Duplication would exceed 32 layers.');return
        import uuid
        mapping={r['id']:uuid.uuid4().hex for r in desc}
        for old in desc:
            r=deepcopy(old);r['id']=mapping[old['id']];r['parent']=mapping.get(old['parent'],old['parent']);r['cut_alignment']=dict(r['cut_alignment'],parent=mapping.get(r['cut_alignment']['parent'],r['cut_alignment']['parent'])) if r.get('cut_alignment') else None;r['name']=r['name'][:123]+' copy'
            if old is row:r['order']=max((a['order'] for a in self.config['layers'] if a['parent']==row['parent']),default=-1)+1
            self.config['layers'].append(r)
        self.selected=mapping[row['id']];self.commit('Duplicate layer/group',before)
    def delete(self):
        if not self.resolve_pending():return
        chosen={item.data(0,Qt.UserRole) for item in self.tree.selectedItems()} or ({self.selected} if self.selected else set())
        ids={r['id'] for r in self.config['layers'] if r['id'] in chosen or any(a['id'] in chosen for a in ancestors(self.config,r['id']))}
        if not ids:return
        if any(effective(self.config,r,'locked') for r in self.config['layers'] if r['id'] in ids):self.status.setText('Nothing deleted: the selected batch contains a protected layer. Unlock it or deselect that subtree.');return
        before=deepcopy(self.config);self.last_selection=self.selected or next(iter(chosen));self.config['layers']=[r for r in self.config['layers'] if r['id'] not in ids];renumber(self.config);self.selected=None;self.commit('Delete '+str(len(ids))+' layers (one batch)',before)
    def reset(self):
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);row.update(transform=transform(),opacity=1.,fit='Fit',flip_x=False,flip_y=False);self.commit('Reset transform / opacity (retain source, crop, masks)',before)
    def flip(self,key):
        row=self.selected_row()
        if row:self.edit(key,not row[key],'Flip layer')
    def reorder(self,front):
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);siblings=sorted((r for r in self.config['layers'] if r['parent']==row['parent'] and r['id']!=row['id']),key=lambda r:r['order']);siblings=siblings+[row] if front else [row]+siblings
        for i,r in enumerate(siblings):r['order']=i;r['cut_alignment']=None
        self.commit('Bring to front' if front else 'Send to back',before)
    def group(self):
        if not self.resolve_pending():return
        before=deepcopy(self.config);selected=[lookup(self.config)[i.data(0,Qt.UserRole)] for i in self.tree.selectedItems()]
        if any(effective(self.config,r,'locked') for r in selected):self.status.setText('Unlock selected layers before grouping.');return
        parents={r['parent'] for r in selected}
        if len(parents)>1:self.status.setText('Group sibling layers; reparent first.');return
        selected.sort(key=lambda r:r['order'])
        if selected and max(r['order'] for r in selected)-min(r['order'] for r in selected)+1!=len(selected):self.status.setText('Select adjacent siblings to preserve the composition order when grouping.');return
        row=new_layer('Group',name='Group');row['parent']=next(iter(parents),None);row['order']=selected[0]['order'] if selected else max((r['order'] for r in self.config['layers'] if r['parent'] is None),default=-1)+1;self.config['layers'].append(row)
        for old in selected:reparent(self.config,old['id'],row['id'])
        renumber(self.config);self.selected=row['id'];self.commit('Group layers',before)
    def ungroup(self):
        row=self.selected_row()
        if not row or row['type']!='Group' or effective(self.config,row,'locked'):return
        if row['opacity']!=1 or row['blend']!='Normal' or row['masks'] or row['crop']!=[0.,0.,1.,1.]:self.status.setText('Ungroup would change isolation. Reset group opacity/blend/masks/crop first.');return
        before=deepcopy(self.config)
        children=sorted((r for r in self.config['layers'] if r['parent']==row['id']),key=lambda r:r['order']);siblings=sorted((r for r in self.config['layers'] if r['parent']==row['parent']),key=lambda r:r['order']);replacement=[]
        for sibling in siblings:replacement.extend(children if sibling is row else [sibling])
        for r in children:reparent(self.config,r['id'],row['parent']);r['enabled']=r['enabled'] and row['enabled']
        for order,r in enumerate(replacement):r['order']=order
        self.config['layers'].remove(row);renumber(self.config);self.selected=None;self.commit('Ungroup (preserve canvas transforms)',before)
    def align_menu(self):
        menu=QMenu(self)
        menu.addSection('Canvas')
        for label,key in (('↤ Left edge','left'),('↔ Horizontal centre','cx'),('↦ Right edge','right'),('↥ Top edge','top'),('↕ Vertical centre','cy'),('↧ Bottom edge','bottom')):menu.addAction(label,lambda checked=False,k=key:self.align(k))
        menu.addSection('Selected layers')
        for label,key in (('↔ Align horizontal centres','sx'),('↕ Align vertical centres','sy')):menu.addAction(label,lambda checked=False,k=key:self.align(k))
        menu.ensurePolished();size=menu.sizeHint();position=QCursor.pos();area=self.screen().availableGeometry();position.setX(max(area.left(),min(position.x(),area.right()-size.width())));position.setY(max(area.top(),min(position.y(),area.bottom()-size.height())));menu.exec(position)
    def align(self,key):
        selected=[lookup(self.config)[i.data(0,Qt.UserRole)] for i in self.tree.selectedItems()];selected=selected or ([self.selected_row()] if self.selected_row() else []);before=deepcopy(self.config)
        centres=[world_matrix(self.config,r['id'])[:2,2] for r in selected];average=np.mean(centres,axis=0) if centres else (0.,0.)
        for row in selected:
            if effective(self.config,row,'locked'):continue
            m=world_matrix(self.config,row['id']);box=[point(asset_matrix(self.config,row,self.canvas_size,(self.metadata(row).get('width',1),self.metadata(row).get('height',1))),p) for p in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5))];delta=np.zeros(2)
            if key in ('cx','sx'):delta[0]=(average[0] if key=='sx' else 0)-m[0,2]
            if key in ('cy','sy'):delta[1]=(average[1] if key=='sy' else 0)-m[1,2]
            if key in ('left','right'):delta[0]=(-.5-min(p[0] for p in box)) if key=='left' else .5-max(p[0] for p in box)
            if key in ('top','bottom'):delta[1]=(-.5-min(p[1] for p in box)) if key=='top' else .5-max(p[1] for p in box)
            m[:2,2]+=delta;parent=world_matrix(self.config,row['parent']) if row['parent'] else np.eye(3);row['transform']=coefficients(np.linalg.inv(parent)@m)
        self.commit('Align layers',before)
    def history(self,redo,scope='layers'):
        if not self.resolve_pending():return
        target=self.selected if scope=='drawing' else None;key='redo' if redo else 'undo';history=self.shell.client.snapshot.get('media_control',{}).get('history',{})
        state=history.get('drawing',{}).get(target,{}) if scope=='drawing' else history
        if not state.get(key):self.status.setText('Nothing to '+key+' in '+('this layer drawing history.' if scope=='drawing' else 'Layers management history.'));return
        self.shell.safe(lambda:self.shell.client.request('composition_history',redo=redo,scope=scope,target=target,media_session=self.binding[0]));self.refresh(True)
        if self.canvas:self.canvas.update()
        if hasattr(self.shell,'media_library'):self.shell.media_library.refresh()
    def duration(self):
        row=self.selected_row();return float(self.metadata(row).get('duration',1.)) if row else 1.
    def transport(self,op,value=None):
        if not self.selected:return
        self.shell.safe(lambda:self.shell.client.request('media_transport',layer=self.selected,op=op,value=value,media_session=self.binding[0]))
    def media_edit(self,key,value):
        if self.syncing:return
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);row['media'][key]=value;self.commit('Layer '+key,before)
    def model_edit(self,key,value):
        if self.syncing:return
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);row['model'][key]=value;self.commit('3D '+key,before)
    def edit_mask(self):
        row=self.selected_row();i=self.mask_list.currentIndex()
        if not row or i<0 or effective(self.config,row,'locked') or not self.resolve_pending():return
        mask=row['masks'][i];self.canvas.points=deepcopy(mask['points']);self.canvas.handles=deepcopy(mask.get('handles',[]));self.canvas.shape=mask.get('shape','Path');self.canvas.set_tool('Remove' if mask['mode']=='Cut' else 'Mask');self.canvas.editing_mask=i;self.reveal();self.canvas.update()
    def toggle_mask(self):
        row=self.selected_row();i=self.mask_list.currentIndex()
        if row and i>=0 and not effective(self.config,row,'locked'):
            before=deepcopy(self.config);row['masks'][i]['enabled']=not row['masks'][i]['enabled'];self.commit('Mask enable / disable',before)
    def remove_mask(self):
        row=self.selected_row();i=self.mask_list.currentIndex()
        if row and i>=0 and not effective(self.config,row,'locked'):
            before=deepcopy(self.config);row['masks'].pop(i);self.commit('Remove mask',before)
    def web(self,inside=False):
        if not self.resolve_pending():return
        parent=self.selected_row() if inside else None
        if parent and any(a['type']=='Group' and a['locked'] for a in [parent]+ancestors(self.config,parent['id'])):self.status.setText('Unlock the protecting Group before adding inside.');return
        from studio_web_layer import LOUDMAN
        before=deepcopy(self.config);row=new_layer('Web',name='Loudman now playing');row['web'].update(url=LOUDMAN,width=720,height=1280);row['parent']=parent['id'] if parent else None;row['order']=max((r['order'] for r in self.config['layers'] if r['parent']==row['parent']),default=-1)+1;self.config['layers'].append(row);self.selected=row['id'];self.commit('Add web source (stopped)',before);self.reveal()
    def web_edit(self,key,value):
        if self.syncing:return
        row=self.selected_row()
        if not row or row['type']!='Web' or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);row['web'][key]=value;self.commit('Web '+key,before)
    def web_start(self):
        row=self.selected_row()
        if row and row['type']=='Web':self.web_sources.start(row)
    def context(self,pos):
        item=self.tree.itemAt(pos)
        if item and not item.isSelected():self.tree.setCurrentItem(item)
        row=lookup(self.config).get(item.data(0,Qt.UserRole)) if item else None;menu=QMenu(self)
        for label,callback in (('Copy',self.copy_layer),('Paste',self.paste_layer),('Duplicate',self.duplicate),('Delete',self.delete)):menu.addAction(label,callback)
        if row and row['type'] in ('Image','Artwork','Paint'):menu.addAction('Add inside…',lambda:self.row_add_menu(row['id']))
        if row and row['type'] in ('Video','GIF','Sprite'):menu.addAction('Snapshot current frame',self.snapshot_frame)
        if row:menu.addAction('Relink source…',self.relink_source)
        menu.exec(self.tree.viewport().mapToGlobal(pos))
    def toggle_section(self,name):
        visible=not self.sections[name].isVisible();self.sections[name].setVisible(visible);self.section_buttons[name].setChecked(visible)
    def tree_eye(self,item,column):
        identity=item.data(0,Qt.UserRole);row=lookup(self.config).get(identity)
        if not row or column!=0 or row['enabled']==(item.checkState(0)==Qt.Checked):return
        before=deepcopy(self.config);row['enabled']=item.checkState(0)==Qt.Checked;self.commit('Layer eye visibility',before)
    def fit_action(self,mode='Fit'):
        if self.syncing:return
        if type(mode) is not str:mode='Fit'
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);parent=world_matrix(self.config,row['parent']) if row['parent'] else np.eye(3);row['transform']=coefficients(np.linalg.inv(parent));row['fit']=mode;self.commit('Fit artwork to canvas ('+mode+')',before)
    def rotate(self,degrees):
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        before=deepcopy(self.config);x,y,s,sy,r=properties(row['transform'],self.canvas_size[0]/self.canvas_size[1]);row['transform']=transform(x,y,s,sy,r+degrees,self.canvas_size[0]/self.canvas_size[1]);self.commit('Rotate '+str(degrees)+' degrees',before)
    def copy_layer(self):
        if self.canvas and self.canvas.points:return self.copy_pixels(False)
        row=self.selected_row()
        if not row:return
        rows=[row]+[r for r in self.config['layers'] if any(a['id']==row['id'] for a in ancestors(self.config,r['id']))];ids={r['asset'] for r in rows};mime=QMimeData();payload=json.dumps(dict(version=1,layers=rows,assets=[a for a in self.config['assets'] if a['id'] in ids])).encode()
        self.layer_clipboard=payload;mime.setData('application/x-zerawave-layers',payload);QApplication.clipboard().setMimeData(mime);self.status.setText('Copied layer artwork and source references; new IDs on Paste.')
    def paste_layer(self):
        mime=QApplication.clipboard().mimeData()
        if mime.hasImage():return self.paste_pixels()
        if not self.resolve_pending():return
        available=mime.hasFormat('application/x-zerawave-layers')
        local=getattr(self,'layer_clipboard',None) if not mime.formats() else None
        if not available and not local:self.status.setText('Clipboard contains no ZeraWave layers. Text fields retain ordinary paste.');return
        if not self.resolve_pending():return
        import uuid
        try:
            data=bytes(mime.data('application/x-zerawave-layers')) if available else local
            if len(data)>262144:raise ValueError('Layer clipboard is too large.')
            copied=json.loads(data);rows=copied['layers']
            if not rows or len(self.config['layers'])+len(rows)>MAX_LAYERS:raise ValueError('Paste exceeds the layer limit.')
            before=deepcopy(self.config);mapping={r['id']:uuid.uuid4().hex for r in rows};root=rows[0];parent=self.selected_row();parent_id=parent['id'] if parent and parent['type'] in ('Group','Image','Artwork','Paint') else None
            if parent_id and any(a['type']=='Group' and a['locked'] for a in [parent]+ancestors(self.config,parent_id)):self.status.setText('Unlock the protecting Group before pasting inside.');return
            for source in rows:
                r=deepcopy(source);r['id']=mapping[source['id']];r['parent']=mapping.get(source['parent'],parent_id);r['cut_alignment']=dict(r['cut_alignment'],parent=mapping.get(r['cut_alignment']['parent'],r['cut_alignment']['parent'])) if r.get('cut_alignment') else None;r['name']=(r['name'][:122]+' copy');self.config['layers'].append(r)
                if source is root:r['order']=max((s['order'] for s in self.config['layers'] if s['parent']==parent_id and s is not r),default=-1)+1
            known={a['id'] for a in self.config['assets']}
            self.config['assets'] += [a for a in copied['assets'] if a['id'] not in known];self.selected=mapping[root['id']];validate_scene(self.config);self.commit('Paste layers (new identities)',before)
        except Exception as exc:
            if 'before' in locals():self.config=before
            self.status.setText(str(exc))
    def editor_key(self,event):
        if not self.canvas:return False
        key=event.key();mods=event.modifiers();canvas=self.canvas;row=self.selected_row();ctrl=bool(mods&Qt.ControlModifier);shift=bool(mods&Qt.ShiftModifier)
        if canvas.interactive:
            op=canvas.interactive
            if key in (Qt.Key_Return,Qt.Key_Enter):canvas.finish_interactive(True)
            elif key==Qt.Key_Escape:canvas.finish_interactive(False)
            elif key in (Qt.Key_X,Qt.Key_Y) and op['kind']!='rotate':op['axis']='X' if key==Qt.Key_X else 'Y'
            elif key==Qt.Key_Backspace:op['number']=op['number'][:-1]
            elif event.text() and all(c in '0123456789.-' for c in event.text()):op['number']+=event.text()
            else:return True
            if canvas.interactive:canvas.interactive_move(canvas.mapFromGlobal(QCursor.pos()),mods)
            return True
        if key==Qt.Key_Escape:canvas.cancel_drag();canvas.discard();return True
        if key in (Qt.Key_Return,Qt.Key_Enter) and canvas.points:canvas.closed_path=True;canvas.apply();return True
        if ctrl:
            if key==Qt.Key_D:canvas.discard();return True
            if key==Qt.Key_C:self.copy_layer();return True
            if key==Qt.Key_X:self.cut_clipboard();return True
            if key==Qt.Key_V:self.paste_layer();return True
            if key==Qt.Key_J:
                if canvas.points:self.cut_child(canvas.operation(),shift)
                else:self.duplicate()
                return True
            if key in (Qt.Key_Z,Qt.Key_Y):
                redo=key==Qt.Key_Y or shift
                if canvas.points and canvas.tool not in ('Selection','Brush','Pencil','Eraser','Smudge'):canvas.preview_history(redo)
                else:self.history(redo,'drawing' if QApplication.focusWidget() is canvas else 'layers')
                return True
            return False
        if mods&Qt.AltModifier:return False
        if shift and key==Qt.Key_D:self.duplicate();return True
        if key in (Qt.Key_G,Qt.Key_R,Qt.Key_S):canvas.begin_interactive({Qt.Key_G:'move',Qt.Key_R:'rotate',Qt.Key_S:'scale'}[key]);return True
        if key==Qt.Key_Space:canvas.space_pan=True;return True
        if key in (Qt.Key_BracketLeft,Qt.Key_BracketRight):self.brush['size']=max(1,min(512,self.brush['size']*(1/1.2 if key==Qt.Key_BracketLeft else 1.2)));self.sync_tool_ui();canvas.update();return True
        tools={Qt.Key_V:'Select',Qt.Key_B:'Brush',Qt.Key_P:'Pencil',Qt.Key_E:'Eraser',Qt.Key_I:'Sampler',Qt.Key_U:'Smudge',Qt.Key_C:'Crop',Qt.Key_K:'Cut',Qt.Key_H:'Hand',Qt.Key_Z:'Zoom'}
        if key in (Qt.Key_M,Qt.Key_L):
            if not self.resolve_pending():return True
            canvas.discard();canvas.shape='Rectangle' if key==Qt.Key_M else 'Freehand';canvas.set_tool('Selection');return True
        if key in tools:self.choose_tool(tools[key]);return True
        if key in (Qt.Key_Delete,Qt.Key_Backspace):
            if canvas.points:
                canvas.preview_begin();index=min(getattr(canvas,'selected_point',len(canvas.points)-1),len(canvas.points)-1);canvas.points.pop(index);canvas.handles=[];canvas.update()
            else:self.delete()
            return True
        if key in (Qt.Key_Left,Qt.Key_Right,Qt.Key_Up,Qt.Key_Down) and row and self.editable_target(row):
            before=deepcopy(self.config);step=10 if shift else 1;w,h=self.canvas_size;row['transform'][4]+=(-step if key==Qt.Key_Left else step if key==Qt.Key_Right else 0)/w;row['transform'][5]+=(-step if key==Qt.Key_Up else step if key==Qt.Key_Down else 0)/h;self.commit('Nudge layer',before);return True
        return key==Qt.Key_Shift
    def shortcut_reference(self):
        QMessageBox.information(self,'Editor shortcuts','V Move/select • G/R/S interactive move px / rotate ° / scale %\nB Brush • P Pencil • E Eraser • I Eyedropper • U Smudge\nM Marquee • L Lasso • C Crop own content • K Automatic Cut to Child\nH Hand • Z Zoom • Space held temporary pan • [ / ] brush size\nCtrl+D Deselect • Shift+D Duplicate branch\nCtrl+J Copy pixels to Child (duplicate without selection)\nCtrl+Shift+J Cut pixels to Child\nCtrl+C/X/V Selected pixels when a selection exists, otherwise layer branch\nCanvas Ctrl+Z: current layer drawing only; exhausted stops. Layers Ctrl+Z: management, transforms, crop/masks. Ctrl+Shift+Z / Ctrl+Y Redo. Unfinished paths: preview-local recovery\nTransform: type value, X/Y axis; Shift rotation snaps 15°, Alt scaling unconstrained; Enter/click accept, Esc/right-click cancel. Pivot is centre.\nText, numeric inputs, searches and dialogs retain ordinary typing.')
    def step_order(self,direction):
        row=self.selected_row()
        if not row or not self.editable_target(row):return
        before=deepcopy(self.config);siblings=sorted((r for r in self.config['layers'] if r['parent']==row['parent']),key=lambda r:r['order']);i=siblings.index(row);j=max(0,min(len(siblings)-1,i+direction));siblings[i],siblings[j]=siblings[j],siblings[i]
        for order,r in enumerate(siblings):r['order']=order;r['cut_alignment']=None
        self.commit('Raise within siblings' if direction>0 else 'Lower within siblings',before)
    def move_to_parent(self):
        row=self.selected_row();parent=lookup(self.config).get(row['parent']) if row else None
        if parent:self.move_branch(parent['parent'])
    def move_menu(self):
        row=self.selected_row()
        if not row:return
        candidates=[r for r in self.config['layers'] if r['id']!=row['id'] and r['type'] in ('Group','Image','Artwork','Paint') and not any(a['id']==row['id'] for a in ancestors(self.config,r['id']))]
        labels=[r['name']+' • '+r['id'][:8] for r in candidates];choice,ok=QInputDialog.getItem(self,'Move inside layer','Destination parent (placement preserved)',labels,0,False) if labels else ('',False)
        if ok:self.move_branch(candidates[labels.index(choice)]['id'])
    def move_branch(self,parent):
        row=self.selected_row()
        if not row or not self.resolve_pending() or not self.editable_target(row):return
        if parent and any(a['type']=='Group' and a['locked'] for a in [lookup(self.config)[parent]]+ancestors(self.config,parent)):self.status.setText('Unlock the destination Group.');return
        before=deepcopy(self.config)
        try:reparent(self.config,row['id'],parent);renumber(self.config);validate_scene(self.config);self.commit('Move branch (preserve canvas placement)',before)
        except Exception as exc:self.config=before;self.status.setText(str(exc))
    def copy_pixels(self,cut=False):
        row=self.selected_row()
        if not row or row['type'] not in ('Image','Artwork','Paint'):self.status.setText('Pixel clipboard targets still own content.');return False
        image=self.canvas.source_image(row)
        if image is None:self.status.setText('Source pixels unavailable.');return False
        op=dict(self.canvas.operation(),mode='Keep');image=masked(masked(image,row['masks']),[op]);QApplication.clipboard().setImage(image);self.pixel_clipboard=image.copy();self.status.setText('Copied selected own pixels • Paste creates a new editable raster layer.')
        if cut:
            if not self.editable_target(row):return False
            before=deepcopy(self.config);row['masks'].append(dict(op,mode='Cut'));self.commit('Cut selected own pixels to clipboard',before);self.canvas.discard()
        return True
    def cut_clipboard(self):
        if self.canvas.points:self.copy_pixels(True)
        else:
            row=self.selected_row()
            if row and self.editable_target(row):self.copy_layer();self.delete()
    def paste_pixels(self):
        image=QApplication.clipboard().image().convertToFormat(QImage.Format_ARGB32_Premultiplied)
        if image.isNull():return
        target=self.selected_row();template=deepcopy(target) if target else None
        if target and any(a['type']=='Group' and a['locked'] for a in ancestors(self.config,target['id'])):self.status.setText('Unlock the protecting Group before pasting a sibling.');return
        def finish(asset):
            before=deepcopy(self.config);row=new_layer('Image',asset['id'],'Pasted pixels')
            if template:
                row.update(piece_geometry(template));row['parent']=template['parent'];row['transform']=template['transform'].copy()
            row['order']=max((r['order'] for r in self.config['layers'] if r['parent']==row['parent']),default=-1)+1;self.config['layers'].append(row)
            from media_registry import reference
            if asset['id'] not in {a['id'] for a in self.config['assets']}:self.config['assets'].append(reference(asset))
            self.images[asset['id']]=image;self.selected=row['id'];self.canvas.discard();self.commit('Paste editable pixels',before)
        self.generated(image,'Editable pixel clipboard',finish,target)
    def artwork_parent(self,identity):
        row=lookup(self.config).get(identity)
        if not row or row['type'] not in ('Group','Image','Artwork','Paint') or any(a['type']=='Group' and a['locked'] for a in [row]+ancestors(self.config,row['id'])):raise ValueError('Choose a parent outside a locked Group.')
        return row
    def create_child(self,asset,parent_id,kind='Image',template=None,label='Create artwork child',prepared=False):
        if not prepared and not self.resolve_pending():return
        self.refresh()
        before=deepcopy(self.config)
        try:
            parent=self.artwork_parent(parent_id);row=new_layer(kind,asset['id'],asset['name']);row['parent']=parent['id'];row['order']=max((r['order'] for r in self.config['layers'] if r['parent']==parent_id),default=-1)+1
            if template:
                for key in ('crop','flip_x','flip_y','fit'):row[key]=deepcopy(template[key])
            self.config['layers'].append(row)
            if asset['id'] not in {a['id'] for a in self.config['assets']}:
                from media_registry import reference
                self.config['assets'].append(reference(asset))
            self.selected=row['id']
            for ancestor in ancestors(self.config,row['id']):self.collapsed.discard(ancestor['id'])
            applied=self.commit(label,before);self.reveal();return applied
        except Exception as exc:self.config=before;self.status.setText(str(exc))
    def generated(self,image,provenance,callback,target=None):
        copied=image.copy();self.generated_work(lambda:copied,provenance,callback,target)
    def generated_work(self,prepare,provenance,callback,target=None):
        if self.art_jobs:self.status.setText('Artwork write pending; wait before another stroke/import.');return
        import os
        from pathlib import Path
        session=self.shell.client.snapshot.get('session_path');folder=Path(session).with_suffix('.assets') if session and not os.environ.get('ZERAWAVE_ARTWORK_STORE') else None
        binding=self.binding[0] if self.binding else None;token=(binding,self.binding[1],deepcopy(target)) if target else None;self.art_jobs.append((binding,self.pool.submit(lambda:dict(store_image(prepare(),provenance,folder),internal=not provenance.startswith('Resized derivative '))),callback,token));self.status.setText('Saving native artwork dependency…')
    def blank_child(self):
        parent=self.selected_row()
        if parent is None or parent['type']=='Group':
            return self.blank_layer(True)
        meta=self.metadata(parent);w,h=meta.get('width'),meta.get('height')
        if not w or not h:self.status.setText('Wait for native source pixels.');return
        image=QImage(w,h,QImage.Format_ARGB32_Premultiplied);image.fill(0);identity=parent['id'];template=deepcopy(parent)
        if not self.editable_target(parent):return
        self.generated(image,'Transparent drawing child of '+parent['name'],lambda asset:self.create_child(dict(asset,name='Drawing'),identity,'Paint',template,prepared=True),parent)
    def extract_child(self,operation):return self.cut_child(operation,False)

    def save_paint(self,stroke,image):
        identity=stroke['row']
        if self.art_jobs:
            self.queued_paint=(stroke,image);self.status.setText('Stroke queued behind the active write; own content remains previewed.');return
        self.pending_paint=dict(row=identity,image=image)
        def finish(asset):
            row=lookup(self.config).get(identity)
            if not row or row['asset']!=stroke['asset']:self.status.setText('Drawing target changed; obsolete stroke not applied.');self.pending_paint=None;return
            before=deepcopy(self.config);row['asset']=asset['id'];row['cut_alignment']=None
            from media_registry import reference
            if asset['id'] not in {a['id'] for a in self.config['assets']}:self.config['assets'].append(reference(asset))
            used={r['asset'] for r in self.config['layers']};self.config['assets']=[a for a in self.config['assets'] if a['id'] in used];self.images[asset['id']]=image
            active=self.canvas.stroke;self.canvas.stroke=None
            applied=self.commit(stroke['tool']+' own-content stroke',before,scope='drawing',target=identity)
            if applied:
                current=deepcopy(lookup(self.config)[identity])
                for pending in ([active] if active and active['row']==identity else [])+([self.queued_paint[0]] if self.queued_paint else []):
                    pending.update(asset=current['asset'],target=current,revision=self.binding[1],session=self.binding[0])
            self.canvas.stroke=active;self.pending_paint=None
            if self.queued_paint:
                queued,self.queued_paint=self.queued_paint,None
                if applied:self.save_paint(*queued)
        self.generated(image,'Editable drawing stroke',finish,stroke['target'])
    def cut_child(self,operation,remove=True):
        parent=self.selected_row()
        if not parent or parent['type'] not in ('Image','Artwork','Paint'):self.status.setText('Cut targets own raster content; moving media needs a frame snapshot.');return False
        if not self.editable_target(parent) or self.art_jobs:return False
        image=self.canvas.source_image(parent)
        if image is None:self.status.setText('Wait for native source pixels.');return False
        before=deepcopy(self.config);operation=deepcopy(operation);operation.update(mode='Keep',enabled=True)
        try:
            if len(self.config['layers'])>=MAX_LAYERS:raise ValueError('32-layer limit; cut preview retained.')
            own=masked(image,parent['masks']);piece=masked(own,[operation])
            alpha=np.frombuffer(piece.constBits(),np.uint8).reshape(piece.height(),piece.bytesPerLine())[:,3:piece.width()*4:4]
            if not alpha.any():raise ValueError('Boundary contains no visible own pixels; adjust it. Preview retained.')
            if remove and len(parent['masks'])>=8:raise ValueError('Eight own masks reached; edit/remove a mask before cutting again.')
            row=new_layer('Image',name=parent['name'][:110]+(' cut' if remove else ' copy'));row.update(parent=parent['id'],order=max((r['order'] for r in self.config['layers'] if r['parent']==parent['id']),default=-1)+1)
            row.update(piece_geometry(parent));candidate=deepcopy(self.config);candidate['layers'].append(dict(row,asset=parent['asset']))
            if remove:lookup(candidate)[parent['id']]['masks'].append(dict(operation,mode='Cut'))
            else:lookup(candidate)[row['id']]['masks'].append(operation)
            validate_scene(candidate)
        except Exception as exc:self.status.setText(str(exc));return False
        identity=parent['id'];target=deepcopy(parent)
        def finish(asset):
            prior=deepcopy(self.config);current=lookup(self.config)[identity];child=deepcopy(row);child['asset']=asset['id']
            if remove:
                current['masks'].append(dict(operation,mode='Cut'));child['cut_alignment']=dict(parent=identity,geometry=piece_geometry(current),asset=asset['id'])
            self.config['layers'].append(child)
            from media_registry import reference
            if asset['id'] not in {a['id'] for a in self.config['assets']}:self.config['assets'].append(reference(asset))
            self.selected=child['id'];self.last_selection=identity
            for a in ancestors(self.config,child['id']):self.collapsed.discard(a['id'])
            self.images[asset['id']]=piece
            if self.commit('Cut own pixels to child' if remove else 'Copy own pixels to child',prior):self.canvas.discard();self.reveal();self.canvas.setFocus(Qt.OtherFocusReason)
        self.generated(piece,'Native extraction from '+parent['name'],finish,target);return True
    def blank_layer(self,inside=False):
        parent=self.selected_row();parent_id=parent['id'] if inside and parent else None
        if parent and any(a['type']=='Group' and a['locked'] for a in ([parent] if inside else [])+ancestors(self.config,parent['id'])):self.status.setText('Unlock the protecting Group before adding inside.');return
        if inside and parent and parent['type'] not in ('Group','Image','Artwork','Paint'):self.status.setText('Choose a raster or mixed-media group parent.');return
        size=self.canvas_size;image=QImage(*size,QImage.Format_ARGB32_Premultiplied);image.fill(0)
        before_selection=self.selected
        def finish(asset):
            prior=deepcopy(self.config);row=new_layer('Image',asset['id'],'Blank raster');row['parent']=parent_id;row['fit']='Stretch'
            if parent and not inside:
                row['parent']=parent['parent'];siblings=sorted((r for r in self.config['layers'] if r['parent']==row['parent']),key=lambda r:r['order']);siblings.insert(siblings.index(lookup(self.config)[parent['id']])+1,row)
                for i,r in enumerate(siblings):r['order']=i
            else:row['order']=max((r['order'] for r in self.config['layers'] if r['parent']==parent_id),default=-1)+1
            self.config['layers'].append(row)
            from media_registry import reference
            if asset['id'] not in {a['id'] for a in self.config['assets']}:self.config['assets'].append(reference(asset))
            self.selected=row['id'];self.last_selection=before_selection;self.images[asset['id']]=image
            if parent_id:self.collapsed.discard(parent_id)
            self.commit('New Layer '+('inside row' if inside else 'above selection'),prior)
        if len(self.config['layers'])>=MAX_LAYERS:self.status.setText('32-layer limit.');return
        self.generated(image,'Transparent new layer',finish,parent if inside else None)
    def snapshot_frame(self):
        parent=self.selected_row()
        if not parent or parent['type'] not in ('Video','GIF','Sprite'):self.status.setText('Select a moving-media frame.');return
        image=self.images.get(parent['id'])
        if image is None:self.status.setText('No decoded frame available; explicitly play/seek first.');return
        template=deepcopy(parent);image=image.copy()
        def finish(asset):
            before=deepcopy(self.config);row=new_layer('Image',asset['id'],parent['name'][:105]+' frame snapshot');row.update({k:deepcopy(template[k]) for k in ('transform','crop','masks','flip_x','flip_y','fit','parent')});row['order']=max((r['order'] for r in self.config['layers'] if r['parent']==row['parent']),default=-1)+1;self.config['layers'].append(row)
            from media_registry import reference
            if asset['id'] not in {a['id'] for a in self.config['assets']}:self.config['assets'].append(reference(asset))
            self.selected=row['id'];self.images[asset['id']]=image;self.commit('Editable frame snapshot (one frame)',before)
        self.generated(image,'Editable frame snapshot',finish,parent)

    def import_child(self):
        row=self.selected_row()
        if not row:return
        paths,_=QFileDialog.getOpenFileNames(self,'Import child artwork','','Images (*.png *.jpg *.jpeg)')
        if paths:self.drop_files(paths,row['id'],'child')
    def child_menu(self):
        menu=QMenu(self);menu.addAction('Blank drawing child',self.blank_child);menu.addAction('Imported image child…',self.import_child);menu.addAction('Extract selected region → draw a boundary, then Apply',lambda:self.choose_tool('Extract'));menu.exec(self.child_button.mapToGlobal(self.child_button.rect().bottomLeft()))
    def import_layer(self):
        from studio_media import FILTER
        paths,_=QFileDialog.getOpenFileNames(self,'Add media layers','',FILTER)
        if paths:self.drop_files(paths,None,'layer')
    def relink_source(self):
        row=self.selected_row()
        if not row or not row['asset']:return
        from studio_media import FILTER
        path,_=QFileDialog.getOpenFileName(self,'Relink artwork source','',FILTER)
        if not path:return
        known={a['id'] for a in self.media_assets()}
        if row['asset'] in known:self.shell.safe(lambda:self.shell.client.request('media_action',op='relink',asset=row['asset'],path=path))
        else:self.shell.safe(lambda:self.shell.client.request('media_recover',asset=row['asset'],path=path))
    def as_sprite(self):
        row=self.selected_row()
        if not row or row['type']!='Image':self.status.setText('Sprite sheets use a still image; static images are already sprites/elements.');return
        self.edit('type','Sprite','Use image as sprite sheet')
    def drop_files(self,paths,target,policy):
        from media_registry import normalized
        if not 1<=len(paths)<=16:self.status.setText('Drop one to sixteen local files.');return
        if policy=='replace' and len(paths)!=1:self.status.setText('Replace accepts one source; use Add for mixed files.');return
        self.shell.safe(lambda:self.shell.client.request('media_import',paths=paths));self.drops.append(dict(paths=list(dict.fromkeys(normalized(p) for p in paths)),target=target,policy=policy,session=self.binding[0],results=[]))
    def working_options(self,asset):
        dialog=QDialog(self);dialog.setWindowTitle('Artwork working pixels');form=QFormLayout(dialog);meta=asset['metadata'];form.addRow(QLabel(f"Native source: {meta['width']} × {meta['height']} px\nOriginal remains unchanged. Canvas/output are separate."));mode=QComboBox();mode.addItems(['Native (default)','Separate resized derivative']);form.addRow('Working pixels',mode);width=QSpinBox();height=QSpinBox()
        for name,widget,value in (('Width',width,meta['width']),('Height',height,meta['height'])):widget.setRange(1,8192);widget.setValue(value);widget.setEnabled(False);form.addRow(name,widget)
        mode.currentIndexChanged.connect(lambda i:(width.setEnabled(bool(i)),height.setEnabled(bool(i))));canvas=QCheckBox('Use source dimensions for canvas (explicit)');form.addRow(canvas);buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
        if dialog.exec()!=QDialog.Accepted:return None
        if width.value()*height.value()>8388608:self.status.setText('Working dimensions exceed 8 megapixels.');return None
        return ((width.value(),height.value()) if mode.currentIndex() else None,canvas.isChecked())
    def canvas_dialog(self):
        dialog=QDialog(self);dialog.setWindowTitle('Canvas Size');form=QFormLayout(dialog);mode=QComboBox();mode.addItems(['Landscape 16:9','Portrait 9:16','Square','Custom']);form.addRow('Shape',mode);width=QSpinBox();height=QSpinBox()
        for label,widget,value in (('Width px',width,self.canvas_size[0]),('Height px',height,self.canvas_size[1])):widget.setRange(1,8192);widget.setValue(value);form.addRow(label,widget)
        def preset(i):
            if i<3:
                w,h=((1920,1080),(1080,1920),(1080,1080))[i];width.setValue(w);height.setValue(h)
        mode.setCurrentIndex(3);mode.currentIndexChanged.connect(preset);placement=QComboBox();placement.addItems(['Preserve proportional placement','Preserve pixel size / centre offset']);form.addRow('Artwork',placement);form.addRow(QLabel('Canvas defines composition geometry. Visualizer Resolution defines output pixels. Canvas fits proportionally into output; zoom changes neither.'));buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);form.addRow(buttons)
        if dialog.exec()==QDialog.Accepted:self.resize_canvas((width.value(),height.value()),placement.currentIndex()==1)
    def resize_canvas(self,size,pixels):
        if not self.resolve_pending():return
        from composition import fit_size
        before=deepcopy(self.config);old_size=self.canvas_size;old_world={r['id']:world_matrix(self.config,r['id']) for r in self.config['layers']};target={}
        try:
            for row in self.config['layers']:
                wm=old_world[row['id']]
                if pixels:
                    meta=self.metadata(row);source=(meta.get('width',1),meta.get('height',1));old_fit=(1,1) if row['type']=='Group' else fit_size(old_size,source,row);new_fit=(1,1) if row['type']=='Group' else fit_size(size,source,row)
                    wm=np.diag([old_size[0]/size[0],old_size[1]/size[1],1.])@wm@np.diag([old_fit[0]/new_fit[0],old_fit[1]/new_fit[1],1.])
                target[row['id']]=wm
            for row in self.config['layers']:
                parent=target[row['parent']] if row['parent'] else np.eye(3);flip=np.diag([-1. if row['flip_x'] else 1.,-1. if row['flip_y'] else 1.,1.]) if row['type']=='Group' else np.eye(3);row['transform']=coefficients(np.linalg.inv(parent)@target[row['id']]@flip)
            self.config['canvas']=list(size);validate_scene(self.config);self.canvas_size=tuple(size);self.commit('Canvas Size ('+('pixel' if pixels else 'proportional')+' placement)',before)
        except Exception as exc:self.config=before;self.canvas_size=old_size;self.status.setText(str(exc))
    def palette(self,title):
        existing=next((p for p in self.palettes if p.title==title),None)
        if existing:
            if existing.isVisible():existing.remember();existing.hide()
            else:self.show_palette(existing)
            return None
        widget=Palette(self,title);self.palettes.append(widget);return widget
    def show_palette(self,widget):
        widget.adjustSize();area=self.screen().availableGeometry();saved=self.shell.preferences.get('media_palettes',{}).get(widget.title)
        if saved and len(saved)==4:widget.resize(max(210,min(area.width(),saved[2])),max(100,min(area.height(),saved[3])));x,y=saved[:2]
        else:
            pos=self.mapToGlobal(self.rect().topLeft());x,y=pos.x()-widget.width(),pos.y()
        widget.move(max(area.left(),min(area.right()-widget.width(),x)),max(area.top(),min(area.bottom()-widget.height(),y)));widget.show();self.sync_tool_ui()
    def tool_grid(self,palette,layout,entries,shapes=False):
        grid=QGridLayout();layout.addLayout(grid);buttons=[]
        if not hasattr(self,'tool_buttons'):self.tool_buttons=[]
        for i,(glyph,label,tool) in enumerate(entries):
            callback=(lambda checked=False,t=tool:self.choose_shape(t)) if shapes else (lambda checked=False,t=tool:self.choose_tool(t))
            button=icon_button('',label,callback);button.setProperty('toolName',tool);button.setText(tool);button.setIcon(tool_icon(tool,26,self.devicePixelRatioF()));button.setIconSize(QSize(26,26));button.setFixedSize(44,44);button.setToolButtonStyle(Qt.ToolButtonIconOnly);button.setCheckable(True);grid.addWidget(button,i//4,i%4);buttons.append(button);self.tool_buttons.append((button,None,tool) if shapes else (button,tool,None))
        if not hasattr(palette,'grids'):palette.grids=[]
        palette.grids.append((grid,buttons))
    def choose_tool(self,tool):
        if self.canvas.tool==tool:self.canvas.setFocus();self.sync_tool_ui();return
        if self.resolve_pending():
            if tool=='Select' and self.canvas.tool=='Selection':self.canvas.discard()
            self.canvas.set_tool(tool);self.reveal();self.canvas.setFocus()
    def choose_shape(self,shape):
        if self.resolve_pending():
            self.canvas.shape=shape;self.canvas.closed_path=shape not in ('Polygon','Curve','Magnetic');self.canvas.set_tool(self.canvas.tool if self.canvas.tool in ('Selection','Mask','Remove','Cut','Extract') else 'Selection');self.canvas.setFocus()
    def brush_tool(self):
        tool=self.canvas.tool if self.canvas else 'Brush'
        return tool if tool in ('Brush','Pencil','Eraser','Smudge') else self.color_target
    @property
    def brush(self):return self.tool_states[self.brush_tool()]['brush']
    @property
    def brush_color(self):return self.tool_states[self.color_target]['color']
    @brush_color.setter
    def brush_color(self,color):self.tool_states[self.color_target]['color']=QColor(color)
    def receive_sample(self,color):
        if color is None or color.alpha()==0:self.status.setText('No visible pixel sampled; drawing colors unchanged.');return
        self.brush_color=color;self.remember_tools();self.sync_tool_ui();self.status.setText('Sampled '+color.name(QColor.HexArgb)+' → '+self.color_target+' color; other settings preserved.')
    def remember_tools(self):
        self.shell.preferences['media_tool_settings']={t:dict(brush=dict(v['brush']),color=v['color'].name(QColor.HexArgb)) for t,v in self.tool_states.items()}
    def restore_tool_preferences(self):
        for tool,values in self.shell.preferences.get('media_tool_settings',{}).items():
            if tool not in self.tool_states or not isinstance(values,dict):continue
            brush=values.get('brush',{});state=self.tool_states[tool]
            for key in state['brush']:
                value=brush.get(key)
                if key=='shape':
                    if value in ('Round','Square'):state['brush'][key]=value
                elif isinstance(value,(int,float)) and math.isfinite(value) and (1<=value<=512 if key=='size' else 0<=value<=1):state['brush'][key]=value
            color=QColor(values.get('color','#f6c490'))
            if color.isValid():state['color']=color
    def tool_settings(self,tool):
        if tool in ('Selection',):tool='Select'
        if tool in ('Mask','Remove','Extract'):tool='Cut'
        palette=self.palette(tool+' settings')
        if palette is None:return
        layout=QVBoxLayout(palette.body);hint=QLabel(tool+' settings • tools remain active with this window closed.');hint.setWordWrap(True);layout.addWidget(hint)
        if tool in self.tool_states:
            state=self.tool_states[tool];form=QFormLayout();layout.addLayout(form)
            if not hasattr(self,'settings_widgets'):self.settings_widgets={}
            widgets={};self.settings_widgets[tool]=widgets
            if tool in ('Brush','Pencil'):
                color=QPushButton(state['color'].name());widgets['color']=color;color.setStyleSheet('background:'+state['color'].name());form.addRow(tool+' color / alpha',color)
                def choose_color():
                    value=QColorDialog.getColor(state['color'],palette,tool+' color',QColorDialog.ShowAlphaChannel)
                    if value.isValid():state['color']=value;color.setText(value.name());color.setStyleSheet('background:'+value.name());self.remember_tools();self.sync_tool_ui()
                color.clicked.connect(choose_color)
            for key,label in (('size','Size native px'),('opacity','Stroke opacity %'),('hardness','Hardness %'),('flow','Flow per dab %'),('strength','Smudge strength %')):
                if key=='strength' and tool!='Smudge' or key=='hardness' and tool not in ('Brush','Eraser') or key=='flow' and tool not in ('Brush','Pencil','Eraser'):continue
                row=QHBoxLayout();box=GestureSpin();widgets[key]=box;box.setRange(1 if key=='size' else 0,512 if key=='size' else 100);box.setDecimals(1);box.setValue(state['brush'][key]*(1 if key=='size' else 100));row.addWidget(box)
                box.valueChanged.connect(lambda v,k=key,t=tool:self.tool_value(t,k,v/(1 if k=='size' else 100)))
                for value in ((4,12,48) if key=='size' else (25,50,100)):
                    b=QPushButton(str(value));b.setMaximumWidth(42);b.clicked.connect(lambda checked=False,v=value,w=box:w.setValue(v));row.addWidget(b)
                form.addRow(label,row)
            footprint=QComboBox();widgets['shape']=footprint;footprint.addItems(['Round','Square']);footprint.setCurrentText(state['brush']['shape']);footprint.currentTextChanged.connect(lambda v,t=tool:self.tool_value(t,'shape',v));form.addRow('Footprint',footprint)
            previews=QHBoxLayout();layout.addLayout(previews)
            for label,size,hardness in (('Fine',4,1.),('Soft',12,.2),('Broad',48,.8)):
                if tool=='Pencil' and label=='Soft':label='Medium'
                image=QImage(120,42,QImage.Format_ARGB32_Premultiplied);image.fill(QColor('#17212b'));brush=dict(state['brush'],size=min(size,24),hardness=hardness,opacity=1.,flow=1.);brush_stroke(image,(12,28),(108,14),brush,state['color'],tool if tool!='Smudge' else 'Brush')
                b=QPushButton(label);b.setIcon(QIcon(QPixmap.fromImage(image)));b.setIconSize(QSize(100,36));b.setToolTip('Stroke preview: '+label);b.clicked.connect(lambda checked=False,t=tool,z=size,h=hardness:self.apply_brush_preset(t,z,h));previews.addWidget(b)
        elif tool=='Sampler':
            scope=QComboBox();scope.addItems(['Active Layer','Visible Composite']);scope.setCurrentText(self.sample_scope);scope.currentTextChanged.connect(lambda v:setattr(self,'sample_scope',v));layout.addWidget(scope);layout.addWidget(QLabel('Samples pixels before checkerboard/handles. Receiving color: last Brush or Pencil.'))
        elif tool in ('Select','Cut'):
            if tool=='Select':
                mode=QComboBox();mode.addItems(['Whole layer handles','Shaped pixel selection']);mode.setCurrentIndex(1 if self.canvas.tool=='Selection' else 0);mode.currentIndexChanged.connect(lambda i:self.choose_tool('Selection' if i else 'Select'));layout.addWidget(mode)
            else:
                outcome=QComboBox();outcome.addItems(['Cut → child + remove own region','Keep → own mask','Remove → own mask','Mask → own keep mask','Extract → child copy']);mapping=['Cut','Mask','Remove','Mask','Extract'];outcome.setCurrentIndex({'Cut':0,'Mask':3,'Remove':2,'Extract':4}.get(self.canvas.tool,0));outcome.currentIndexChanged.connect(lambda i:self.choose_tool(mapping[i]));layout.addWidget(outcome)
            shapes=QComboBox();shapes.addItems(['Rectangle','Square','Circle','Ellipse','Freehand','Polygon','Curve','Magnetic']);shapes.setCurrentText(self.canvas.shape);shapes.currentTextChanged.connect(self.choose_shape);layout.addWidget(QLabel('Advanced boundary shape'));layout.addWidget(shapes)
            hint=QLabel('Provisional path: drag anchors/handles to adjust. Curve, Polygon and Magnetic: Enter or double-click completes; click first anchor closes. Open/Close changes preview only. Apply commits the labelled outcome; Discard cancels. Preview Ctrl+Z stays local.');hint.setWordWrap(True);layout.addWidget(hint)
            row=QHBoxLayout();layout.addLayout(row)
            for label,cb in (('Open / Close',self.canvas.toggle_closed),('Apply',self.canvas.apply),('Discard',self.canvas.discard)):
                b=QPushButton(label);b.clicked.connect(cb);row.addWidget(b)
            masks=QComboBox()
            if not hasattr(self,'settings_mask_widgets'):self.settings_mask_widgets={}
            self.settings_mask_widgets[tool]=masks;layout.addWidget(QLabel('Selected layer saved masks'));layout.addWidget(masks);self.sync_saved_masks()
            masks.currentIndexChanged.connect(lambda i:self.mask_list.setCurrentIndex(i))
            row=QHBoxLayout();layout.addLayout(row)
            for label,cb in (('Edit points',self.edit_mask),('Enable / disable',self.toggle_mask),('Remove mask',self.remove_mask)):
                b=QPushButton(label);b.clicked.connect(lambda checked=False,c=cb,w=masks:self.saved_mask_action(w.currentIndex(),c));row.addWidget(b)
        elif tool=='Crop':
            hint=QLabel('Drag a crop rectangle, then adjust corner/side handles. Apply commits to Layers history; Discard retains the saved crop.');hint.setWordWrap(True);layout.addWidget(hint)
            for label,cb in (('Apply crop',self.canvas.apply),('Discard preview',self.canvas.discard)):
                b=QPushButton(label);b.clicked.connect(cb);layout.addWidget(b)
        else:
            for label,cb in (('Fit canvas',self.editor_view.fit),('100% native detail',self.editor_view.actual),('Canvas Size…',self.canvas_dialog)):
                b=QPushButton(label);b.clicked.connect(cb);layout.addWidget(b)
        self.show_palette(palette)
    def sync_settings_values(self):
        for tool,widgets in getattr(self,'settings_widgets',{}).items():
            state=self.tool_states[tool]
            for key,widget in widgets.items():
                widget.blockSignals(True)
                if key=='color':widget.setText(state['color'].name(QColor.HexArgb));widget.setStyleSheet('background:'+state['color'].name())
                elif key=='shape':widget.setCurrentText(state['brush'][key])
                else:widget.setValue(state['brush'][key]*(1 if key=='size' else 100))
                widget.blockSignals(False)
    def tool_value(self,tool,key,value):
        self.tool_states[tool]['brush'][key]=value;self.remember_tools();self.sync_tool_ui();self.canvas.update()
    def apply_brush_preset(self,tool,size,hardness):
        self.tool_states[tool]['brush'].update(size=size,hardness=hardness);self.remember_tools();self.status.setText(tool+' preset applied; exact values retained.');self.sync_tool_ui()
    def sync_saved_masks(self):
        for masks in getattr(self,'settings_mask_widgets',{}).values():
            index=masks.currentIndex();masks.blockSignals(True);masks.clear();row=self.selected_row()
            for i,m in enumerate(row['masks'] if row else []):masks.addItem(f"{i+1}: {m['mode']} • {'on' if m['enabled'] else 'off'}")
            masks.setCurrentIndex(max(0,min(index,masks.count()-1)));masks.blockSignals(False)
    def saved_mask_action(self,index,callback):
        self.mask_list.setCurrentIndex(index);callback();self.sync_saved_masks()
    def solid_fill(self):
        row=self.selected_row()
        if not row or row['type'] not in ('Image','Artwork','Paint'):self.status.setText('Fill requires a selected editable raster layer.');return
        if not self.editable_target(row) or not self.resolve_pending():return
        image=self.canvas.source_image(row)
        if image is None:self.status.setText('Wait for native source pixels before Fill.');return
        color=QColorDialog.getColor(self.brush_color,self,'Solid fill — replaces selected own RGBA; stroke opacity separate',QColorDialog.ShowAlphaChannel)
        if not color.isValid():return
        filled=image.copy();filled.fill(color);selection=self.canvas.operation() if self.canvas.points else None;result=constrained_edit(image,filled,row,selection,1.)
        stroke=dict(row=row['id'],asset=row['asset'],target=deepcopy(row),session=self.binding[0],revision=self.binding[1],tool='Solid fill');self.save_paint(stroke,result)
    def drawing_onboarding(self):
        if self.onboarding_pending:return
        box=QMessageBox(self);box.setWindowTitle('Create a new layer?');box.setText('Create a new layer?');box.setStandardButtons(QMessageBox.Yes|QMessageBox.No);box.setDefaultButton(QMessageBox.Yes)
        if self.config['layers']:box.setInformativeText('Yes adds a transparent overlay to this composition. No keeps it unchanged.')
        else:box.setInformativeText('Yes creates a white editable surface. No keeps the empty canvas unchanged.')
        if box.exec()!=QMessageBox.Yes:return
        if len(self.config['layers'])>=MAX_LAYERS:self.status.setText('32-layer limit; canvas unchanged.');return
        self.onboarding_pending=True;white=not self.config['layers'];image=QImage(*self.canvas_size,QImage.Format_ARGB32_Premultiplied)
        if image.isNull():self.onboarding_pending=False;self.status.setText('Allocation failed; canvas unchanged.');return
        image.fill(QColor('white') if white else Qt.transparent);session=self.binding[0]
        def finish(asset):
            self.onboarding_pending=False
            if self.binding[0]!=session:return
            before=deepcopy(self.config);row=new_layer('Image',asset['id'],'Drawing surface' if white else 'Drawing overlay');row['fit']='Stretch';row['order']=max((r['order'] for r in self.config['layers'] if r['parent'] is None),default=-1)+1;self.config['layers'].append(row)
            from media_registry import reference
            self.config['assets'].append(reference(asset));self.images[asset['id']]=image;self.selected=row['id'];self.commit('Create drawing layer',before);self.canvas.setFocus();self.status.setText('Layer ready. Draw with the active tool; canvas Undo recovers its drawing only.')
        self.generated(image,'White empty-canvas onboarding' if white else 'Transparent drawing overlay',finish)

    def load_images(self):
        assets={a['id']:a for a in self.media_assets()};needed={r['asset'] for r in self.config['layers'] if r['type'] in ('Image','Artwork','Paint','Model')}
        layer_ids=set(lookup(self.config));cache_ids=needed|layer_ids
        for identity in set(self.images)-cache_ids:self.images.pop(identity,None)
        if self.canvas:self.canvas.mask_cache={k:v for k,v in self.canvas.mask_cache.items() if k in layer_ids}
        for identity in list(self.image_jobs):
            if identity not in needed:self.image_jobs.pop(identity)[1].cancel();self.images.pop(identity,None);self.models.pop(identity,None);self.image_errors.pop(identity,None)
        for identity in list(self.model_keys):
            if identity not in lookup(self.config):self.model_keys.pop(identity,None)
        for identity in list(self.images):
            if identity not in needed and identity not in lookup(self.config):self.images.pop(identity,None)
        for identity in needed:
            asset=assets.get(identity)
            if not asset or asset.get('status')!='Ready':continue
            key=(asset['path'],asset.get('metadata',{}).get('mtime_ns'),json.dumps(asset.get('metadata',{}).get('dependencies',{}),sort_keys=True))
            job=self.image_jobs.get(identity)
            if job and job[0]==key:
                if identity not in self.images and identity not in self.models and job[1].done() and identity not in self.image_errors:job[1].displayed=False
                continue
            if sum(1 for _,f in self.image_jobs.values() if not f.done())>=8:continue
            def decode(a=deepcopy(asset)):
                if a['kind']=='Models':
                    from model_layer import load_model
                    return load_model(a['path'])
                meta,data=decode_image(a['path']);return QImage(data,meta['width'],meta['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied)
            self.image_jobs[identity]=(key,self.pool.submit(decode))
    def frames(self):
        changed=False
        for session,job,callback,token in list(self.art_jobs):
            if not job.done():continue
            self.art_jobs.remove((session,job,callback,token))
            self.onboarding_pending=False
            try:
                if session!=self.shell.client.snapshot.get('media_control',{}).get('session'):
                    self.pending_paint=None;self.queued_paint=None;continue
                record=job.result()
                if token and not self.valid_target(*token):self.pending_paint=None;self.queued_paint=None;self.status.setText('Target/session changed; completed dependency retained, obsolete edit not applied.');continue
                existing=next((a for a in self.media_assets() if a['path']==record['path']),None)
                if existing:record=existing
                else:self.shell.client.request('media_artwork',asset=record)
                callback(record)
            except Exception as exc:
                self.pending_paint=None;self.queued_paint=None
                if self.canvas.stroke:self.canvas.cancel_drag()
                self.status.setText('Artwork not applied; previous content retained: '+str(exc)[:180])
        from media_registry import normalized
        library=self.shell.client.snapshot.get('media_library',{});assets=library.get('assets',[]);pending=library.get('pending',[])
        for drop in list(self.drops):
            if self.canvas and (self.canvas.drag or self.canvas.stroke or self.canvas.interactive) or self.numeric_before is not None:continue
            if drop['session']!=self.shell.client.snapshot.get('media_control',{}).get('session'):self.drops.remove(drop);continue
            for path in list(drop['paths']):
                asset=next((a for a in assets if normalized(a['path'])==path and a.get('status')=='Ready'),None)
                if asset:
                    if drop['policy']=='child':
                        kind={'Images':'Image','Video':'Video','Animated':'GIF'}.get(asset['kind'])
                        if kind is None:drop['results'].append('Unsupported child type: '+asset['name']);drop['paths'].remove(path);continue
                        applied=self.create_child(asset,drop['target'],kind)
                    elif drop['policy']=='replace':
                        target=lookup(self.config).get(drop['target'])
                        kind={'Images':'Image','Video':'Video','Animated':'GIF'}.get(asset['kind'])
                        if not target or not kind:drop['results'].append('Replacement source/type unavailable');drop['paths'].remove(path);continue
                        elif effective(self.config,target,'locked'):drop['results'].append('Unlock the replacement target first');drop['paths'].remove(path);continue
                        elif target['type']=='Artwork' and kind!='Image':drop['results'].append('Keep artwork children: replace with another still image');drop['paths'].remove(path);continue
                        else:
                            before=deepcopy(self.config);target['asset']=asset['id'];target['type']='Artwork' if target['type']=='Artwork' else kind
                            from media_registry import reference
                            if asset['id'] not in {a['id'] for a in self.config['assets']}:self.config['assets'].append(reference(asset))
                            applied=self.commit('Replace layer source',before)
                    else:applied=self.add_asset(asset,True)
                    drop['results'].append(('Applied '+asset['name']) if applied else ('Not applied: '+asset['name']+' • '+self.status.text()));drop['paths'].remove(path)
                elif not any(j.get('path') and normalized(j['path'])==path for j in pending):
                    result=next((r for r in reversed(library.get('import_results',[])) if normalized(r['path'])==path),{})
                    drop['results'].append('Not imported: '+path+' • '+result.get('error','validation failed/cancelled'));drop['paths'].remove(path)
            if not drop['paths']:self.status.setText('; '.join(drop['results'])[:800]);self.drops.remove(drop)
        for identity,(key,job) in list(self.image_jobs.items()):
            if job.done() and getattr(job,'displayed',False) is False:
                job.displayed=True
                try:
                    result=job.result()
                    if isinstance(result,dict):
                        cost=lambda d:sum(p['vertices'].nbytes+p['indices'].nbytes for p in d['primitives'])+sum(w*h*4 for w,h,b in d['images'])
                        if sum(cost(d) for d in self.models.values())+cost(result)>64*1024*1024:raise ValueError('Editor geometry-guide cache exceeds 64 MiB; inspect this model in Visualizer.')
                        self.models[identity]=result
                    else:
                        if sum(i.sizeInBytes() for k,i in self.images.items() if k!=identity)+result.sizeInBytes()>192*1024*1024:raise ValueError('Native editor cache exceeds 192 MiB; hide/remove an unused source.')
                        self.images[identity]=result
                    changed=True
                except Exception as exc:self.image_errors[identity]=str(exc)[:180]
        visible_canvas=bool(self.canvas and self.canvas.isVisible())
        if not visible_canvas and not self.tree.isVisible():self.reader.close();return
        import time
        now=time.monotonic()
        if now-getattr(self,'last_frame_read',0)<(.033 if visible_canvas else .25):return
        self.last_frame_read=now
        names=set()
        for identity,state in self.shell.client.snapshot.get('media_frames',{}).items():
            desc=state.get('frame')
            if not desc:continue
            names.add(desc['name'])
            try:
                frame=self.reader.read(desc)
                if frame:
                    if sum(i.sizeInBytes() for k,i in self.images.items() if k!=identity)+frame['width']*frame['height']*4>192*1024*1024:raise ValueError('Native editor cache exceeds 192 MiB; hide/remove an unused source.')
                    self.images[identity]=QImage(frame['data'],frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied);changed=True
            except Exception as exc:self.status.setText(str(exc)[:180])
        self.reader.retain(names)
        for row in self.config['layers']:
            if row['type']!='Model' or row['asset'] not in self.models:continue
            key=json.dumps(row['model'],sort_keys=True)
            if self.model_keys.get(row['id'])==key:continue
            data=self.models[row['asset']];m=np.eye(3)
            for axis,angle in zip((1,0,2),(row['model'][k] for k in ('yaw','pitch','roll'))):
                r=np.eye(3);a=math.radians(angle);i,j=((2,0) if axis==1 else (1,2) if axis==0 else (0,1));r[i,i]=r[j,j]=math.cos(a);r[i,j]=-math.sin(a);r[j,i]=math.sin(a);m=r@m
            image=QImage(512,512,QImage.Format_ARGB32_Premultiplied);image.fill(0);p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);triangles=[]
            count=sum(len(p['indices'])//3 for p in data['primitives']);stride=max(1,math.ceil(count/4000))
            for primitive in data['primitives']:
                positions=(primitive['vertices'][:,:3]-data['centre'])/data['radius'];positions=positions@m.T
                for triangle in primitive['indices'].reshape(-1,3)[::stride]:triangles.append((positions[triangle,2].mean(),positions[triangle],primitive['factor']))
            for z,points,color in sorted(triangles,key=lambda t:t[0],reverse=True):
                p.setPen(QPen(QColor('#71cdda'),.5));p.setBrush(QColor.fromRgbF(*[max(0,min(1,float(v))) for v in color]));p.drawPolygon(QPolygonF([QPointF(256+x/1.8*256,256-y/1.8*256) for x,y,z in points]))
            p.end();self.images[row['id']]=image;self.model_keys[row['id']]=key;changed=True
        if changed:
            # setIcon emits itemChanged too. Do not let a thumbnail refresh
            # become an eye command which clears this tree during iteration.
            blocked=self.tree.blockSignals(True)
            try:
                iterator=QTreeWidgetItemIterator(self.tree)
                while iterator.value():
                    node=iterator.value();row=lookup(self.config).get(node.data(0,Qt.UserRole));image=(self.images.get(row['id']) or self.images.get(row['asset'])) if row else None
                    if image is not None and row['id'] in self.row_widgets:self.row_widgets[row['id']].update_thumbnail(image)
                    iterator+=1
            finally:self.tree.blockSignals(blocked)
            if visible_canvas:self.canvas.update()
    def close_resources(self):
        self.cancel_preview();self.timer.stop();self.preview_timer.stop();self.numeric_timer.stop();self.web_sources.close();self.reader.close();self.pool.shutdown(wait=False,cancel_futures=True)
        for palette in self.palettes:palette.close()
