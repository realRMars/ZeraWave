"""Layers and direct composition canvas; edits commit to the existing owner.

The editor draws only layers. It never renders a world or starts visual/audio
transport. Canvas transforms share the renderer's composition contract.
"""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json,math,threading,time,os
import numpy as np
from PySide6.QtCore import Qt,QTimer,QPointF,QRectF,QSize,Signal,QEvent,QMimeData
from PySide6.QtGui import QImage,QPainter,QPainterPath,QPolygonF,QColor,QPen,QTransform,QIcon,QPixmap,QCursor
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QPushButton,QComboBox,QTreeWidget,QTreeWidgetItem,QTreeWidgetItemIterator,QLineEdit,QDoubleSpinBox,QSlider,QCheckBox,QGroupBox,QMenu,QMessageBox,QInputDialog,QSpinBox,QScrollArea,QTabWidget,QApplication,QToolButton,QGridLayout,QFileDialog,QDialog,QDialogButtonBox,QColorDialog,QToolTip,QHeaderView,QSizeGrip,QMainWindow,QToolBar,QStyle,QStyleOptionSlider
from composition import defaults,validate_scene,new_layer,lookup,ancestors,effective,asset_matrix,world_matrix,matrix,coefficients,transform,properties,reparent,renumber,PRESENTATIONS,BLENDS,MAX_LAYERS,is_branch,ordered_children,partition_aligned,piece_geometry,IDENTITY
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
    elif name in ('Select','Rectangle','Square','Selection','Mask','Extract'):
        p.setPen(QPen(QColor('#bfe8ed'),2,Qt.DashLine if name in ('Selection','Mask') else Qt.SolidLine));p.drawRect(4,6,24,20)
        if name=='Extract':p.drawLine(10,16,24,16);p.drawLine(19,11,24,16);p.drawLine(19,21,24,16)
    elif name=='Lasso':
        path=QPainterPath();path.moveTo(7,23);path.cubicTo(-2,12,10,1,23,6);path.cubicTo(35,13,24,25,12,25);path.cubicTo(5,25,5,20,11,19);path.cubicTo(19,19,15,30,25,29);p.drawPath(path)
    elif name=='Wand':
        p.drawLine(5,28,22,11);p.drawLine(4,25,8,29)
        for x,y in ((24,6),(10,7),(27,20)):
            p.drawLine(x-3,y,x+3,y);p.drawLine(x,y-3,x,y+3)
    elif name in ('Ellipse','Circle'):p.drawEllipse(3,6,26,20)
    elif name=='Crop':p.drawLine(9,3,9,23);p.drawLine(9,23,29,23);p.drawLine(3,9,23,9);p.drawLine(23,9,23,29)
    elif name=='Transform':
        p.drawLine(3,16,29,16);p.drawLine(16,3,16,29)
        for x,y,dx,dy in ((3,16,5,5),(29,16,-5,5),(16,3,5,5),(16,29,5,-5)):p.drawLine(x,y,x+dx,y+dy);p.drawLine(x,y,x+(dx if x==16 else dx),y+(-dy if x!=16 else dy))
    elif name in ('ZoomIn','ZoomOut'):
        p.drawEllipse(3,3,19,19);p.drawLine(20,20,29,29);p.drawLine(8,12,17,12)
        if name=='ZoomIn':p.drawLine(12,8,12,17)
    elif name=='Save':
        p.drawPolygon(QPolygonF([QPointF(5,4),QPointF(24,4),QPointF(28,8),QPointF(28,28),QPointF(5,28)]));p.drawRect(10,4,12,9);p.drawRect(10,19,13,9);p.drawLine(18,6,18,11)
    elif name=='Fill':
        p.drawPolygon(QPolygonF([QPointF(5,15),QPointF(16,4),QPointF(27,15),QPointF(16,26)]));p.drawLine(5,15,27,15)
        path=QPainterPath();path.moveTo(9,11);path.cubicTo(3,0,17,0,21,9);p.drawPath(path)
        path=QPainterPath();path.moveTo(28,19);path.quadTo(21,29,28,29);path.quadTo(34,29,28,19);p.drawPath(path)
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

MAX_CANVAS_ZOOM=256.
MIN_CANVAS_ZOOM=.02

class _CanvasMethods:
    def __init__(self,editor):
        super().__init__();self.editor=editor;self.setFocusPolicy(Qt.StrongFocus);self.setMouseTracking(True);self.setMinimumSize(260,180)
        self.zoom=None;self.pan=QPointF();self.drag=None;self.tool='Select';self.points=[];self.point_drag=None;self.mask_mode='Keep';self.shape='Rectangle';self.handles=[];self.closed_path=True;self.preview_undo=[];self.preview_redo=[];self.selection_drag=None;self.stroke=None;self.space_pan=False;self.interactive=None;self.mask_cache={};self.setAcceptDrops(True)
        self.bubble=QWidget(self);bubble=QHBoxLayout(self.bubble);bubble.setContentsMargins(3,3,3,3)
        for text,help,cb,color in (('✓','Apply crop',self.apply,'#77dc99'),('×','Cancel crop',self.discard,'#fc7878'),('↶','Undo preview adjustment',lambda:self.preview_history(False),'#ffcd78'),('↷','Redo preview adjustment',lambda:self.preview_history(True),'#ffcd78')):
            b=icon_button(text,help,cb);b.setStyleSheet('color:'+color);bubble.addWidget(b)
        self.bubble.hide();self.apply_tool_cursor()
        self.setToolTip('')
    @property
    def canvas_size(self):return self.editor.canvas_size
    def set_tool(self,name):
        import time
        began=time.perf_counter()
        if name=='Zoom':name='Transform'
        if name=='Cut':name='Select'
        if name!=self.tool and hasattr(self.editor,'pixel_editor'):self.editor.pixel_editor.cancel()
        if name!=self.tool and hasattr(self.editor,'fill_controller'):self.editor.fill_controller.cancel()
        self.tool=name
        if name in ('Brush','Pencil') and hasattr(self.editor,'color_target'):self.editor.color_target=name
        combo=getattr(self.editor,'editor_tools',None)
        if combo:combo.blockSignals(True);combo.setCurrentText(name);combo.blockSignals(False)
        self.apply_tool_cursor()
        self.editor.sync_tool_ui()
        if hasattr(self.editor,'ui_timings'):
            self.editor.ui_timings.append(dict(event='tool_activation_sidebar',tool=name,ms=(time.perf_counter()-began)*1000));self.editor.ui_timings=self.editor.ui_timings[-256:]
        self.update()
    def cursor_method(self):
        return 'Lasso' if self.tool in ('Select','Selection') and self.shape=='Freehand' else 'Select' if self.tool=='Selection' else self.tool
    def tool_cursor(self,dpr=None):
        dpr=self.devicePixelRatioF() if dpr is None else dpr;name=self.cursor_method();key=(name,round(dpr,4));cache=getattr(self,'cursor_cache',{})
        if key not in cache:
            pix=QPixmap(round(42*dpr),round(42*dpr));pix.setDevicePixelRatio(dpr);pix.fill(Qt.transparent);p=QPainter(pix);p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor('#10171c'),3));p.drawLine(0,4,8,4);p.drawLine(4,0,4,8);p.setPen(QPen(QColor('#ffffff'),1));p.drawLine(0,4,8,4);p.drawLine(4,0,4,8)
            p.drawPixmap(QPointF(10,10),tool_icon(name,28,dpr).pixmap(QSize(28,28),dpr));p.end();cache[key]=QCursor(pix,4,4);self.cursor_cache=cache
        return cache[key]
    def apply_tool_cursor(self):
        gesture=getattr(getattr(self.editor,'pixel_editor',None),'gesture',None)
        self.setCursor(Qt.ClosedHandCursor if self.drag and self.drag[0]=='pan' else Qt.SizeAllCursor if self.drag or gesture and gesture['kind']=='move' else self.tool_cursor())
    def event(self,event):
        if hasattr(self,'tool') and event.type()==getattr(QEvent,'DevicePixelRatioChange',None):self.apply_tool_cursor()
        return super().event(event)
    def enterEvent(self,event):self.apply_tool_cursor();super().enterEvent(event)
    def source_image(self,row):return self.editor.images.get(row['asset']) or self.editor.images.get(row['id'])
    def magnetic(self,row,uv):
        image=self.source_image(row);snapped=magnetic_point(image,uv)
        distance=math.hypot((snapped[0]-uv[0])*image.width(),(snapped[1]-uv[1])*image.height()) if image else 0
        self.editor.status.setText(('Magnetic: attracted %.1f source px; '%distance if distance>.1 else 'Magnetic: no strong nearby edge; ')+str(len(self.points))+'/128 points • 12 px search radius • manual correction available.')
        return snapped
    def mask_image(self,image,row):
        from native_raster import NativeImage
        if isinstance(image,NativeImage):
            from raster_edit import masked_projection
            return masked_projection(self,image,row)
        key=(image.cacheKey(),json.dumps(row['masks'],sort_keys=True));old=self.mask_cache.get(row['id'])
        if old and old[0]==key:return old[1]
        result=masked_image(image,row);self.mask_cache[row['id']]=(key,result)
        if sum(v[1].sizeInBytes() for v in self.mask_cache.values())>128*1024*1024:self.mask_cache={row['id']:(key,result)}
        return result
    def view(self):
        w,h=self.canvas_size;scale=self.zoom if self.zoom is not None else min(max(1,self.width()-48)/w,max(1,self.height()-48)/h)
        return QTransform(scale,0.,0.,scale,(self.width()-w*scale)/2+self.pan.x(),(self.height()-h*scale)/2+self.pan.y())
    def pixel_inspection(self):return self.zoom is not None and self.view().m11()*self.devicePixelRatioF()>=16.
    def canvas_point(self,p):
        v=self.view().inverted()[0].map(p);w,h=self.canvas_size;return v.x()/w-.5,v.y()/h-.5
    def source_matrix(self,row):
        meta=self.editor.metadata(row);return asset_matrix(self.editor.config,row,self.canvas_size,(meta.get('width',1)*meta.get('pixel_aspect',1),meta.get('height',1)))
    def mask_point(self,row,pos,clamp=True):
        local=point(np.linalg.inv(self.source_matrix(row)),self.canvas_point(pos));uv=[local[0]+.5,local[1]+.5]
        c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop']
        if row['type']!='Group':uv=[1-uv[0] if row['flip_x'] else uv[0],1-uv[1] if row['flip_y'] else uv[1]]
        values=[float(c[i]+uv[i]*(c[i+2]-c[i])) for i in (0,1)]
        return [max(0.,min(1.,v)) for v in values] if clamp else values
    def screen_point(self,row,uv):
        c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop'];u=(uv[0]-c[0])/(c[2]-c[0])-.5;v=(uv[1]-c[1])/(c[3]-c[1])-.5
        if row['type']!='Group':u=-u if row['flip_x'] else u;v=-v if row['flip_y'] else v
        x,y=point(self.source_matrix(row),(u,v));w,h=self.canvas_size;return self.view().map(QPointF((x+.5)*w,(y+.5)*h))
    def preview_state(self):return deepcopy((self.points,self.handles,self.closed_path,getattr(self,'pixel_op',None)))
    def preview_begin(self):
        self.preview_undo.append(self.preview_state());self.preview_undo=self.preview_undo[-32:];self.preview_redo=[]
    def preview_history(self,redo):
        source,target=(self.preview_redo,self.preview_undo) if redo else (self.preview_undo,self.preview_redo)
        if source:target.append(self.preview_state());self.points,self.handles,self.closed_path,self.pixel_op=source.pop();self.pixel_overlay=None;self.update()
    def operation(self):
        if getattr(self,'pixel_op',None):return deepcopy(self.pixel_op)
        shape='Rectangle' if self.shape in ('Rectangle','Square') or self.tool=='Crop' else 'Ellipse' if self.shape in ('Ellipse','Circle') else 'Curve' if self.shape=='Curve' else 'Path'
        return dict(mode='Cut' if self.tool in ('Cut','Remove') else 'Keep',enabled=True,points=deepcopy(self.points),shape=shape,handles=deepcopy(self.handles) if shape=='Curve' else [])
    def auto_handles(self):
        self.handles=[]
        for i,p in enumerate(self.points):
            a=self.points[i-1];b=self.points[(i+1)%len(self.points)];d=[(b[j]-a[j])/6 for j in (0,1)];self.handles.append([[max(0.,min(1.,p[j]-d[j])) for j in (0,1)],[max(0.,min(1.,p[j]+d[j])) for j in (0,1)]])
    def content_bounds(self,row):
        c=row['crop'];image=self.source_image(row)
        if row['type']=='Group' or image is None:return c
        key=(image.cacheKey(),json.dumps(row['masks'],sort_keys=True),tuple(c))
        cache=getattr(self,'bounds_cache',{});old=cache.get(row['id'])
        if old and old[0]==key:return old[1]
        # New immutable source/mask only; never repeated on pointer movement.
        im=self.mask_image(image,row);a=np.frombuffer(im.constBits(),np.uint8).reshape(im.height(),im.bytesPerLine())[:,3:im.width()*4:4]
        x0,y0=math.floor(c[0]*im.width()),math.floor(c[1]*im.height());x1,y1=math.ceil(c[2]*im.width()),math.ceil(c[3]*im.height());part=a[y0:y1,x0:x1]
        ys=np.flatnonzero(np.any(part,axis=1));xs=np.flatnonzero(np.any(part,axis=0))
        bounds=[max(c[0],(x0+xs[0])/im.width()),max(c[1],(y0+ys[0])/im.height()),min(c[2],(x0+xs[-1]+1)/im.width()),min(c[3],(y0+ys[-1]+1)/im.height())] if len(xs) else c
        cache[row['id']]=(key,bounds);self.bounds_cache={k:v for k,v in cache.items() if k in lookup(self.editor.config)};return bounds
    def polygon(self,row):
        if row['type']=='Group':
            m=self.source_matrix(row);w,h=self.canvas_size
            return QPolygonF([self.view().map(QPointF((x+.5)*w,(y+.5)*h)) for x,y in (point(m,p) for p in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)))])
        c=self.content_bounds(row);return QPolygonF([self.screen_point(row,uv) for uv in ((c[0],c[1]),(c[2],c[1]),(c[2],c[3]),(c[0],c[3]))])
    def paintEvent(self,event):
        smooth=not self.pixel_inspection()
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
            target=QImage(iw,ih,QImage.Format_ARGB32_Premultiplied);target.fill(0);p=QPainter(target);p.setRenderHint(QPainter.SmoothPixmapTransform,smooth)
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
                    p.end();source=QImage(iw,ih,QImage.Format_ARGB32_Premultiplied);source.fill(0);p=QPainter(source);p.setRenderHint(QPainter.SmoothPixmapTransform,smooth)
                p.save();p.setOpacity(row['opacity']);p.setCompositionMode(QPainter.CompositionMode_SourceOver if add else QPainter.CompositionMode_Plus if partition else modes[blend])
                if group:p.drawImage(QRectF(0,0,iw,ih),image)
                else:
                    m=self.source_matrix(row);pixel=projection@m
                    p.setTransform(qtransform(pixel));p.scale(-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1)
                    c=row['crop'];p.drawImage(QRectF(-.5,-.5,1.,1.),image,QRectF(c[0]*image.width(),c[1]*image.height(),(c[2]-c[0])*image.width(),(c[3]-c[1])*image.height()))
                p.restore()
                if add:
                    p.end();original=target
                    if blend=='Add':
                        from native_raster import backend,native_add
                        target=native_add(target,source) if backend().available else add_image(target,source)
                    else:
                        target=target.copy();bp=QPainter(target);bp.setCompositionMode(modes[blend]);bp.drawImage(0,0,source);bp.end()
                    if strength<1.:
                        normal=original.copy();bp=QPainter(normal);bp.drawImage(0,0,source);bp.end();a=np.frombuffer(normal.constBits(),np.uint8).astype(np.uint16);b=np.frombuffer(target.constBits(),np.uint8).astype(np.uint16);factor=round(strength*255);data=((a*(255-factor)+b*factor+127)//255).astype(np.uint8).tobytes();target=QImage(data,iw,ih,QImage.Format_ARGB32_Premultiplied).copy()
                    p=QPainter(target);p.setRenderHint(QPainter.SmoothPixmapTransform,smooth)
            p.end();return target
        from native_raster import backend
        surface=getattr(self,'gpu_surface',None)
        if surface is not None:
            painter.beginNativePainting()
            try:
                size=(max(1,round(self.width()*dpr)),max(1,round(self.height()*dpr)));target=surface.target_for(self.defaultFramebufferObject(),size)
                self.gpu_stats=surface.draw(self,size,full_projection,target)
                self.editor.projection_diagnostic=('GPU display / exact Qt filtered view' if smooth else 'GPU display / exact Qt pixel inspection') if self.gpu_stats.get('sampling_reference') else 'GPU native pixel projection'
                if self.gpu_stats.get('error'):self.editor.status.setText('Editor projection retained: '+self.gpu_stats['error'])
            finally:painter.endNativePainting()
            image=None
        elif backend().available and self.stroke and hasattr(self,'composite_image'):
            # Preserve the B1 live damage projection/rounding route. Native
            # presentation and masks update tiles; Add uses the native kernel.
            image=children(None)
            if hasattr(self,'projection_cache'):
                stats=self.projection_cache.stats;stats['active_damage_pixels']=stats.get('active_damage_pixels',0)+iw*ih;stats['active_damage_paints']=stats.get('active_damage_paints',0)+1
        elif backend().available:
            from cpu_projection import Projection
            if not hasattr(self,'projection_cache'):self.projection_cache=Projection()
            try:image=self.projection_cache.render(self,max(1,round(self.width()*dpr)),max(1,round(self.height()*dpr)),full_projection,QRectF(region.left()*dpr,region.top()*dpr,region.width()*dpr,region.height()*dpr) if self.stroke else None)
            except Exception as exc:
                painter.end();self.editor.status.setText('Projection failed; accepted content retained: '+str(exc)[:180]);return
            region=self.rect()
        else:image=children(None)
        if image is not None:
            if region==self.rect():self.composite_image=image
            else:
                cp=QPainter(self.composite_image);cp.setCompositionMode(QPainter.CompositionMode_Source);cp.drawImage(round(region.left()*dpr),round(region.top()*dpr),image);cp.end()
            painter.save();painter.setClipRect(canvas);painter.drawImage(QRectF(region),image);painter.restore()
        painter.setPen(QPen(QColor('#607078'),1));painter.drawRect(canvas)
        row=self.editor.selected_row()
        if row is not None:
            polygon=self.polygon(row);painter.setPen(QPen(QColor('#f0ae78' if effective(self.editor.config,row,'locked') else '#63d6e1'),1.5));painter.setBrush(Qt.NoBrush);painter.drawPolygon(polygon) if self.tool=='Transform' else None
            if self.tool=='Transform' and not effective(self.editor.config,row,'locked'):
                painter.setBrush(QColor('#10171c'))
                self.resize_handles=list(polygon)+[(polygon[i]+polygon[(i+1)%4])/2 for i in range(4)]
                for p in self.resize_handles:painter.drawRect(QRectF(p.x()-4,p.y()-4,8,8))
                top=(polygon[0]+polygon[1])/2;centre=sum((p for p in polygon),QPointF())/4;direction=top-centre;length=math.hypot(direction.x(),direction.y()) or 1.;handle=top+direction*(22/length)
                painter.drawLine(top,handle);painter.drawEllipse(handle,4,4);self.rotation_handle=handle
            if self.points and not getattr(self,'pixel_selection_ready',False):
                m=self.source_matrix(row);c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop'];poly=[]
                for x,y in self.points:
                    u=(x-c[0])/(c[2]-c[0])-.5;v=(y-c[1])/(c[3]-c[1])-.5
                    if row['type']!='Group':u=-u if row['flip_x'] else u;v=-v if row['flip_y'] else v
                    x1,y1=point(m,(u,v));poly.append(self.view().map(QPointF((x1+.5)*w,(y1+.5)*h)))
                painter.setPen(QPen(QColor('#ffcd78'),2));painter.drawPolyline(QPolygonF(poly))
                for p in poly:painter.drawEllipse(p,4,4)
                if getattr(self,'pixel_op',None):
                    from pixel_selection import operation_image
                    op=self.pixel_op;im=self.source_image(row)
                    if getattr(self,'pixel_overlay',None) is None:
                        overlay=operation_image(op,(im.width(),im.height()));a=np.frombuffer(overlay.bits(),np.uint8).reshape(overlay.height(),overlay.bytesPerLine())[:,:overlay.width()*4].reshape(overlay.height(),overlay.width(),4);alpha=(a[:,:,3].astype(np.uint16)*70//255).astype(np.uint8);a[:,:,0]=alpha.astype(np.uint16)*120//255;a[:,:,1]=alpha.astype(np.uint16)*205//255;a[:,:,2]=alpha;a[:,:,3]=alpha;self.pixel_overlay=overlay
                    c=row['crop'];uv=np.array([[1/(c[2]-c[0]),0.,-c[0]/(c[2]-c[0])-.5],[0.,1/(c[3]-c[1]),-c[1]/(c[3]-c[1])-.5],[0.,0.,1.]]);flip=np.diag([-1. if row['flip_x'] else 1.,-1. if row['flip_y'] else 1.,1.]);painter.save();painter.setTransform(qtransform(full_projection/dpr@self.source_matrix(row)@flip@uv));painter.drawImage(QRectF(0,0,1,1),self.pixel_overlay);painter.restore()
                if len(self.points)>=3 and not getattr(self,'pixel_op',None):
                    op=self.operation();path=selection_path(op,(1.,1.),self.closed_path);c=[0.,0.,1.,1.] if row['type']=='Group' else row['crop'];uv=np.array([[1/(c[2]-c[0]),0.,-c[0]/(c[2]-c[0])-.5],[0.,1/(c[3]-c[1]),-c[1]/(c[3]-c[1])-.5],[0.,0.,1.]])
                    flip=np.diag([-1. if row['flip_x'] else 1.,-1. if row['flip_y'] else 1.,1.]) if row['type']!='Group' else np.eye(3)
                    pp=full_projection/dpr@self.source_matrix(row)@flip@uv;painter.save();painter.setTransform(qtransform(pp));painter.setPen(QPen(QColor('#ffcd78'),0));painter.setBrush(QColor(255,205,120,35) if self.closed_path else Qt.NoBrush);painter.drawPath(path);painter.restore()
                for i,pair in enumerate(self.handles):
                    for v in pair:
                        a=self.screen_point(row,self.points[i]);b=self.screen_point(row,v);painter.setPen(QPen(QColor('#bd9ddc'),1));painter.drawLine(a,b);painter.drawEllipse(b,3,3)
                self.bubble.adjustSize();self.bubble.move(max(0,min(self.width()-self.bubble.width(),round(poly[-1].x()+12))),max(0,min(self.height()-self.bubble.height(),round(poly[-1].y()+12))));self.bubble.setVisible(self.tool=='Crop' or self.tool in ('Mask','Remove','Extract'))
            else:self.bubble.hide()
        if hasattr(self.editor,'pixel_editor'):self.editor.pixel_editor.draw(painter,full_projection/dpr)
        # A private first-stroke buffer is displayed before its atomic child commit.
        if self.stroke and self.stroke.get('new_child'):
            row=self.stroke['target'];painter.save();painter.setTransform(qtransform(projection/dpr@self.source_matrix(row)));painter.scale(-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1);c=row['crop'];im=self.stroke['image'];painter.drawImage(QRectF(-.5,-.5,1.,1.),im,QRectF(c[0]*im.width(),c[1]*im.height(),(c[2]-c[0])*im.width(),(c[3]-c[1])*im.height()));painter.restore()
        if row and self.points and not getattr(self,'pixel_selection_ready',False) and len(self.points)==4 and (self.tool=='Crop' or self.shape in ('Rectangle','Square','Ellipse','Circle')):
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
        if self.stroke:return # another button cannot replace an active private gesture
        self.tracing=False
        if self.interactive:
            if event.button()==Qt.LeftButton:self.finish_interactive(True)
            elif event.button()==Qt.RightButton:self.finish_interactive(False)
            return
        if event.button()==Qt.MiddleButton or self.space_pan or self.tool=='Hand':self.drag=('pan',pos,QPointF(self.pan));self.apply_tool_cursor();return
        secondary=event.button()==Qt.RightButton and self.tool in ('Brush','Pencil','Fill','Sampler') and not event.modifiers()&Qt.ShiftModifier
        erase=event.button()==Qt.RightButton and self.tool in ('Eraser','Smudge') and not event.modifiers()&Qt.ShiftModifier
        if event.button()!=Qt.LeftButton and not erase and not secondary:return
        row=self.editor.selected_row()
        if self.tool in ('Brush','Pencil','Eraser','Smudge') and row is None:self.editor.drawing_onboarding();return
        if self.tool=='Fill':self.editor.fill_controller.click(pos,secondary=secondary);return
        if self.tool=='Sampler':
            from editor_colors import sample
            sample(self,pos,True,secondary=secondary);return
        if self.tool=='Wand':
            if not self.editor.pixel_editor.press(event):self.editor.selection_controls.click(pos)
            return
        if self.editor.pixel_editor.press(event):return
        if self.tool=='Sampler':
            from editor_colors import sample
            sample(self,pos,True);return
        if self.tool=='Sampler' and self.editor.sample_scope=='Visible Composite':
            self.editor.receive_sample(self.sample_composite(pos));return
        if self.tool=='Sampler' and row and not self.polygon(row).containsPoint(pos,Qt.OddEvenFill):
            self.editor.receive_sample(None);return
        if self.tool in ('Brush','Pencil','Eraser','Smudge','Sampler') and row:
            self.paint_press(row,pos,erase,secondary)
            if self.stroke:
                from stroke_input import MouseHistory
                self.stroke['input']=MouseHistory(self,event);self.stroke['button']=event.button();self.stroke['input_stats']=dict(delivered=1,captured=1,history=0,processing_ms=[],history_gaps=0,sample_age_ms=[])
            return
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
            self.drag_frame=self.source_matrix(row).copy();self.drag_polygon=QPolygonF(self.polygon(row));self.drag=(handle or 'move',self.canvas_point(pos),deepcopy(row),deepcopy(self.editor.config));self.setCursor(Qt.SizeAllCursor)
    def mouseMoveEvent(self,event):
        if self.editor.pixel_editor.move(event):return
        if self.tool=='Sampler':
            self.sample_position=QPointF(event.position())
            if not hasattr(self,'sample_timer'):
                from editor_colors import sample
                self.sample_timer=QTimer(self);self.sample_timer.setSingleShot(True);self.sample_timer.setInterval(33);self.sample_timer.timeout.connect(lambda:sample(self,self.sample_position) if self.tool=='Sampler' else None)
            if not self.sample_timer.isActive():self.sample_timer.start()
        if self.interactive:self.interactive_move(event.position(),event.modifiers());return
        if self.tool in ('Brush','Pencil','Eraser','Smudge'):
            self.hover=event.position()
            if not self.stroke:self.update()
        if self.stroke:self.paint_event(event);return
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
            polygon=self.drag_polygon;centre=sum((p for p in polygon),QPointF())/4;centre_canvas=self.canvas_point(centre)
            inv=np.linalg.inv(self.drag_frame);pivot=point(inv,centre_canvas);a=np.subtract(point(inv,begin),pivot);b=np.subtract(point(inv,now),pivot);index=getattr(self,'scale_handle',0)
            sx=max(.01,min(100.,abs(b[0]/a[0]))) if abs(a[0])>1e-6 and index not in (4,6) else 1.;sy1=max(.01,min(100.,abs(b[1]/a[1]))) if abs(a[1])>1e-6 and index not in (5,7) else 1.
            if row['aspect_lock']:sx=sy1=max(sx,sy1) if index<4 else sy1 if index in (4,6) else sx
            pivot_local=np.array(point(np.linalg.inv(parent),centre_canvas));offset=np.linalg.inv(matrix(values)[:2,:2])@(pivot_local-np.array(values[4:]))
            values[0]*=sx;values[1]*=sx;values[2]*=sy1;values[3]*=sy1
            values[4:]=list(pivot_local-matrix(values)[:2,:2]@offset)
        elif kind=='rotate':
            polygon=self.drag_polygon;centre=sum((p for p in polygon),QPointF())/4;pivot=np.array(point(np.linalg.inv(parent),self.canvas_point(centre)));aspect=self.canvas_size[0]/self.canvas_size[1];a=math.atan2((local_begin[1]-pivot[1])/aspect,local_begin[0]-pivot[0]);b=math.atan2((local_now[1]-pivot[1])/aspect,local_now[0]-pivot[0]);rotation=matrix_rotation(math.degrees(b-a),aspect);m=matrix(values);m[:2,:2]=rotation[:2,:2]@m[:2,:2];m[:2,2]=pivot+rotation[:2,:2]@(m[:2,2]-pivot);values=coefficients(m)
        row['transform']=[float(v) for v in values];self.editor.sync_controls();self.editor.schedule_preview();self.update()
    def mouseReleaseEvent(self,event):
        if self.editor.pixel_editor.release(event):return
        if self.stroke:
            if event.button()!=self.stroke.get('button',event.button()):return
            self.paint_event(event);self.paint_finish();return
        if self.shape=='Curve' and self.points and len(self.handles)!=len(self.points):self.auto_handles()
        complete=self.selection_drag is not None or self.tracing and self.shape=='Freehand'
        self.selection_drag=None
        self.point_drag=None;self.tracing=False
        if complete:
            self.closed_path=True;row=self.editor.selected_row();self.selection_target=row['id'] if row else None
            self.editor.status.setText('Boundary preview ready. Confirm, keep/remove own pixels, or extract to child — keep source.')
        if self.drag and self.drag[0]!='pan':self.editor.commit('Canvas '+self.drag[0],before=self.drag[3])
        self.drag=None;self.apply_tool_cursor()
    def cancel_drag(self):
        if hasattr(self.editor,'pixel_editor'):self.editor.pixel_editor.cancel()
        if self.interactive:self.finish_interactive(False)
        if self.drag and self.drag[0]!='pan':self.editor.config=deepcopy(self.drag[3]);self.editor.sync_controls()
        if self.stroke:self.stroke=None;self.editor.status.setText('Uncommitted stroke cancelled; previous artwork retained.')
        self.drag=None;self.point_drag=None;self.selection_drag=None;self.space_pan=False;self.apply_tool_cursor();self.editor.cancel_preview();self.update()
    def hideEvent(self,event):self.cancel_drag();super().hideEvent(event)
    def focusOutEvent(self,event):self.cancel_drag();super().focusOutEvent(event)
    def focusInEvent(self,event):self.set_tool(self.tool);super().focusInEvent(event)
    def leaveEvent(self,event):self.hover=None;self.update();super().leaveEvent(event)
    def wheelEvent(self,event):
        if self.stroke:self.cancel_drag()
        old=self.view();delta=event.angleDelta().y()/120 if event.angleDelta().y() else event.pixelDelta().y()/120;step=1.02 if event.modifiers()&Qt.ControlModifier else 1.15;self.zoom=max(MIN_CANVAS_ZOOM,min(MAX_CANVAS_ZOOM,old.m11()*math.pow(step,delta)));anchor=old.inverted()[0].map(event.position());self.pan+=event.position()-self.view().map(anchor);self.update();event.accept()
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
        self.interactive=dict(kind=kind,pivot=self.canvas_point(sum((p for p in self.polygon(row)),QPointF())/4),before=deepcopy(self.editor.config),target=deepcopy(row),start=self.canvas_point(self.mapFromGlobal(QCursor.pos())),number='',axis=None)
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
        if kind in ('rotate','scale'):
            parent=world_matrix(self.editor.config,base['parent']) if base['parent'] else np.eye(3);pivot=np.array(point(np.linalg.inv(parent),op['pivot']));offset=np.linalg.inv(matrix(base['transform'])[:2,:2])@(pivot-np.array(base['transform'][4:]));row['transform'][4:]=list(pivot-matrix(row['transform'])[:2,:2]@offset)
        row['transform']=[float(v) for v in row['transform']]
        self.editor.status.setText(kind.title()+' '+label+' • '+(axis or 'XY')+' • Enter accept / Esc cancel');self.editor.sync_controls();self.editor.schedule_preview();self.update()
    def finish_interactive(self,accept):
        op,self.interactive=self.interactive,None
        if not op:return
        if accept:self.editor.commit('Interactive '+op['kind'],op['before'])
        else:self.editor.config=op['before'];self.editor.cancel_preview();self.editor.sync_controls();self.update()
    def discard(self):
        self.pixel_op=None;self.pixel_overlay=None;self.pixel_selection_ready=False
        if hasattr(self.editor,'pixel_editor'):self.editor.pixel_editor.reset()
        if hasattr(self.editor,'selection_controls'):self.editor.selection_controls.cancel()
        self.points=[];self.handles=[];self.closed_path=True;self.preview_undo=[];self.preview_redo=[];self.point_drag=None;self.editing_mask=None;self.selection_drag=None;self.bubble.hide();self.editor.sync_tool_ui();self.update()
    def extract_preview(self):
        if len(self.points)<3 or not self.closed_path:self.editor.status.setText('Finish and close the boundary before extraction; preview retained.');return
        self.editor.extract_child(self.operation())
    def apply(self):
        row=self.editor.selected_row()
        if not row or not self.points:return
        if not self.editor.editable_target(row):return
        before=deepcopy(self.editor.config)
        if self.tool in ('Selection','Wand'):self.selection_target=row['id'];self.editor.status.setText('Selected pixels of '+row['name']+' • Ctrl+C copies; Ctrl+X removes; Extract to child keeps source');return
        if self.tool=='Cut':
            if not self.closed_path:self.editor.status.setText('Complete this boundary with Enter, double-click or closure.');return
            self.editor.selection_controls.commit_mask('Keep');return
        if self.tool=='Extract':
            if not self.closed_path:self.editor.status.setText('Close this path before extraction.');return
            self.editor.extract_child(self.operation());return
        if self.tool=='Crop':
            if len(self.points)<2:self.editor.status.setText('Crop needs two opposite corners.');return
            from composition import crop_preserving
            meta=self.editor.metadata(row);crop=[min(p[0] for p in self.points),min(p[1] for p in self.points),max(p[0] for p in self.points),max(p[1] for p in self.points)]
            crop_preserving(self.editor.config,row,self.canvas_size,(meta.get('width',1)*meta.get('pixel_aspect',1),meta.get('height',1)),crop)
        else:
            if not self.closed_path:self.editor.status.setText('Close this path before applying.');return
            mask=self.operation();index=getattr(self,'editing_mask',None)
            if index is not None:row['masks'][index]=mask
            else:row['masks'].append(mask)
        try:validate_scene(self.editor.config)
        except ValueError as exc:self.editor.config=before;self.editor.status.setText(str(exc));return
        if self.editor.commit('Apply '+self.tool.lower(),before=before):self.discard()
    def paint_press(self,row,pos,erase=False,secondary=False):
        import time
        began=time.perf_counter()
        if self.editor.await_recovery:self.editor.status.setText('Drawing recovery is applying; start the next stroke when its accepted pixels arrive.');return
        if self.tool in ('Brush','Pencil','Eraser','Smudge'):
            capacity=self.editor.shell.client.snapshot.get('media_control',{}).get('raster',{})
            if capacity.get('pending',0)>=capacity.get('job_limit',16):
                self.editor.status.setText('Stroke not started: saving is at capacity. No edit accepted. Redraw after writes drain or recovery succeeds.');return
            if capacity.get('resource_count',0)>=capacity.get('resource_limit',256):
                self.editor.status.setText('Stroke not started: retained artwork is at capacity. No edit accepted. Save As to secure accepted work, then redraw.');return
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
            self.editor.receive_sample(sampled,secondary=secondary);return
        if not row['source_visible']:self.editor.status.setText('Own content is hidden. Show it before pixel editing.');return
        from native_raster import NativeImage
        buffer=image.private_view() if isinstance(image,NativeImage) else image.convertToFormat(QImage.Format_ARGB32_Premultiplied).copy()
        if buffer.isNull():self.editor.status.setText('Cannot allocate stroke; previous content retained.');return
        if self.points and getattr(self,'pixel_selection_ready',False) and not self.editor.pixel_editor.readable(False):return
        selection=self.operation() if self.points and getattr(self,'selection_target',row['id'])==row['id'] else None
        self.stroke=dict(asset=row['asset'],image=buffer,base=image if isinstance(image,NativeImage) else image.copy(),scene=deepcopy(self.editor.config),target=deepcopy(row),row=row['id'],session=self.editor.binding[0],revision=self.editor.binding[1],new_child=False,tool='Eraser' if erase else self.tool,brush=deepcopy(self.editor.brush),color=QColor(self.editor.secondary_color if secondary else self.editor.brush_color),last=(x,y),selection=selection)
        if self.tool=='Smudge':
            from editor_colors import pin_pickup
            try:pin_pickup(self,self.stroke)
            except Exception as exc:self.stroke=None;self.editor.status.setText('Smudge unavailable: '+str(exc)[:180]);return
        view=self.view();w,h=self.canvas_size;v=np.array([[1/(view.m11()*w),0.,-view.dx()/(view.m11()*w)-.5],[0.,1/(view.m22()*h),-view.dy()/(view.m22()*h)-.5],[0.,0.,1.]])
        c=row['crop'];flip=np.diag([-1 if row['flip_x'] else 1, -1 if row['flip_y'] else 1,1.]);uv=np.array([[(c[2]-c[0])*image.width(),0.,(c[0]+(c[2]-c[0])*.5)*image.width()],[0.,(c[3]-c[1])*image.height(),(c[1]+(c[3]-c[1])*.5)*image.height()],[0.,0.,1.]])
        self.stroke['input_matrix']=uv@flip@np.linalg.inv(self.source_matrix(row))@v
        self.stroke['view_signature']=(self.width(),self.height(),self.devicePixelRatioF(),view.m11(),view.m22(),view.dx(),view.dy())
        self.stroke['coverage']=None if isinstance(image,NativeImage) else edit_coverage((image.width(),image.height()),row,selection);self.stroke['preview']=buffer if isinstance(image,NativeImage) else image.copy();self.editor.ui_timings.append(dict(event='stroke_prepare',tool=self.tool,ms=(time.perf_counter()-began)*1000));self.editor.ui_timings=self.editor.ui_timings[-256:];self.paint_move(pos)
    def sample_composite(self,pos):
        w,h=self.canvas_size
        if not self.view().mapRect(QRectF(0,0,w,h)).contains(pos):return None
        surface=getattr(self,'gpu_surface',None)
        if surface is not None:
            self.makeCurrent()
            try:return surface.layers.read_pixel(round(pos.x()*self.devicePixelRatioF()),round(pos.y()*self.devicePixelRatioF()))
            finally:self.doneCurrent()
        image=getattr(self,'composite_image',None)
        if image is None:self.editor.status.setText('Visible composite is not ready.');return None
        dpr=self.devicePixelRatioF();x,y=round(pos.x()*dpr),round(pos.y()*dpr)
        return image.pixelColor(x,y) if 0<=x<image.width() and 0<=y<image.height() else None
    def paint_move(self,pos):
        if self.stroke and self.stroke.get('pickup') and (self.editor.binding!=(self.stroke['session'],self.stroke['revision']) or self.editor.config!=self.stroke['scene']):
            self.cancel_drag();self.editor.status.setText('Smudge scene changed; uncommitted gesture cancelled.');return
        if not self.stroke:return
        stroke=self.stroke
        if not self.editor.valid_target(stroke['session'],stroke['revision'],stroke['target']):self.cancel_drag();return
        row=stroke['target'];image=stroke['image'];v=stroke['input_matrix']@np.array([pos.x(),pos.y(),1.]);now=(max(0.,min(image.width(),v[0])),max(0.,min(image.height(),v[1])));last=stroke['last'];brush=stroke['brush']
        from native_raster import NativeImage
        if isinstance(image,NativeImage):
            from raster_edit import segment
            try:bounds=segment(stroke,now)
            except Exception as exc:
                self.stroke=None;self.editor.status.setText('Private stroke cancelled; accepted content retained: '+str(exc)[:180]);self.update();return
            stroke['last']=now
            corners=[self.screen_point(row,(x/image.width(),y/image.height())) for x in (bounds[0],bounds[2]) for y in (bounds[1],bounds[3])]
            self.update(QPolygonF(corners).boundingRect().adjusted(-3,-3,3,3).toAlignedRect());return
        if stroke['tool']=='Smudge':
            from editor_colors import pickup_tile
            try:smudge(image,last,now,brush['size'],brush['strength'],1.,brush['shape'],row,stroke['selection'],pickup=pickup_tile(stroke,last,max(1,round(brush['size']/2))))
            except Exception as exc:self.stroke=None;self.editor.status.setText('Private Smudge cancelled; accepted pixels retained: '+str(exc)[:180]);self.update();return
        else:brush_stroke(image,last,now,brush,stroke['color'],stroke['tool'])
        radius=math.ceil(brush['size']/2)+4
        bounds=(math.floor(min(last[0],now[0])-radius),math.floor(min(last[1],now[1])-radius),math.ceil(max(last[0],now[0])+radius),math.ceil(max(last[1],now[1])+radius))
        constrained_edit(stroke['base'],image,row,stroke['selection'],brush['opacity'],bounds=bounds,coverage=stroke['coverage'],result=stroke['preview'])
        stroke['last']=now
        corners=[self.screen_point(row,(x/image.width(),y/image.height())) for x in (bounds[0],bounds[2]) for y in (bounds[1],bounds[3])]
        self.update(QPolygonF(corners).boundingRect().adjusted(-3,-3,3,3).toAlignedRect())

    def paint_event(self,event):
        stroke=self.stroke
        if not stroke:return
        view=self.view()
        if stroke.get('view_signature')!=(self.width(),self.height(),self.devicePixelRatioF(),view.m11(),view.m22(),view.dx(),view.dy()):self.cancel_drag();self.editor.status.setText('View changed during gesture; uncommitted stroke cancelled, previous artwork retained.');return
        from stroke_input import MouseHistory
        history=stroke.get('input');samples,ages,gap=history.samples(event) if history else ([event.position()],[],False)
        stats=stroke.setdefault('input_stats',dict(delivered=0,captured=1,history=0,processing_ms=[],history_gaps=0,sample_age_ms=[]))
        stats['delivery_age_ms']=(stats.get('delivery_age_ms',[])+[getattr(history,'delivery_age_ms',None)])[-256:]
        stats['delivered']+=1;stats['captured']+=len(samples);stats['history']+=max(0,len(samples)-1);stats['history_gaps']+=int(gap);stats['sample_age_ms']=(stats['sample_age_ms']+ages)[-256:]
        started=time.perf_counter()
        from native_raster import NativeImage
        if len(samples)>1 and stroke['tool']!='Smudge' and isinstance(stroke['image'],NativeImage):
            if not self.editor.valid_target(stroke['session'],stroke['revision'],stroke['target']):self.cancel_drag();return
            image=stroke['image'];points=[]
            for pos in samples:
                v=stroke['input_matrix']@np.array([pos.x(),pos.y(),1.]);points.append((max(0.,min(image.width(),v[0])),max(0.,min(image.height(),v[1]))))
            try:
                from raster_edit import path
                bounds=path(stroke,points);stroke['last']=points[-1]
                corners=[self.screen_point(stroke['target'],(x/image.width(),y/image.height())) for x in (bounds[0],bounds[2]) for y in (bounds[1],bounds[3])]
                self.update(QPolygonF(corners).boundingRect().adjusted(-3,-3,3,3).toAlignedRect())
            except Exception as exc:self.stroke=None;self.editor.status.setText('Private stroke cancelled; accepted content retained: '+str(exc)[:180]);self.update()
        else:
            for pos in samples:
                if not self.stroke:break
                self.paint_move(pos)
        stats['last_history_count']=getattr(history,'last_count',None);stats['last_history_error']=getattr(history,'last_error',None)
        stats['processing_ms']=(stats['processing_ms']+[(time.perf_counter()-started)*1000])[-256:]
    def paint_finish(self):
        stroke,self.stroke=self.stroke,None
        if stroke:self.last_input_stats=stroke.get('input_stats',{});self.last_input_stats['final_source_position']=list(stroke['last'])
        if stroke and self.editor.valid_target(stroke['session'],stroke['revision'],stroke['target']):self.editor.save_paint(stroke,stroke['preview'])
        self.update()
    def contextMenuEvent(self,event):
        # Consume queued/modified events at the canvas boundary for every tool.
        event.accept()
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

class Canvas(_CanvasMethods,QWidget):
    pass

from PySide6.QtOpenGLWidgets import QOpenGLWidget

class GPUCanvas(_CanvasMethods,QOpenGLWidget):
    """The same authoring Canvas hosted by Qt's current GL surface."""
    def __init__(self,editor):
        super().__init__(editor)
        from PySide6.QtGui import QSurfaceFormat
        fmt=QSurfaceFormat();fmt.setVersion(3,3);fmt.setProfile(QSurfaceFormat.CoreProfile);fmt.setSamples(0);self.setFormat(fmt)
        self.gpu_surface=None;self.gpu_stats={};self._paint_event=None
    def initializeGL(self):
        try:
            import moderngl
            from renderer import EditorSurface
            self.gpu_surface=EditorSurface(moderngl.create_context(require=330))
            self.context().aboutToBeDestroyed.connect(self.close_gpu)
        except Exception as exc:
            self.editor.status.setText('GPU editor unavailable; retaining CPU reference: '+str(exc)[:140]);QTimer.singleShot(0,self.fallback_cpu)
    def paintEvent(self,event):
        self._paint_event=event;QOpenGLWidget.paintEvent(self,event)
    def paintGL(self):
        # QOpenGLWidget makes the context current before this callback.
        if self._paint_event is None:
            from PySide6.QtGui import QPaintEvent
            self._paint_event=QPaintEvent(self.rect())
        _CanvasMethods.paintEvent(self,self._paint_event)
    def close_gpu(self):
        surface=self.gpu_surface
        if surface is None:return
        self.gpu_surface=None;self.makeCurrent()
        try:surface.close()
        finally:self.doneCurrent()
    def fallback_cpu(self):
        if self.editor.canvas is not self:return
        replacement=Canvas(self.editor)
        for key,value in self.__dict__.items():
            if key not in ('editor','bubble','gpu_surface','gpu_stats','_paint_event','checker_tile') and not isinstance(value,QWidget):setattr(replacement,key,value)
        parent=self.parentWidget();parent.layout().replaceWidget(self,replacement);self.editor.canvas=replacement
        if getattr(self.editor,'editor_view',None):self.editor.editor_view.canvas=replacement
        self.editor.projection_diagnostic='CPU reference / GPU unavailable'
        self.close_gpu();self.hide();replacement.apply_tool_cursor();replacement.show();self.deleteLater();replacement.update()

def create_canvas(editor):
    from native_raster import backend
    return (GPUCanvas if os.name=='nt' and os.environ.get('QT_QPA_PLATFORM')!='offscreen' and os.environ.get('ZERAWAVE_EDITOR_GPU','auto')!='cpu' and backend().available else Canvas)(editor)

class DirectToolButton(QuickToolButton):
    def __init__(self,editor,tool,description):
        super().__init__();self.editor=editor;self.tool=tool;self.setText('Magic Wand' if tool=='Wand' else tool);self.setAccessibleName('Magic Wand' if tool=='Wand' else tool);self.setToolTip(('Magic Wand • '+description if tool=='Wand' else description)+('' if tool=='Hand' else ' • Double-click to focus tool sidebar'));self.setCheckable(True);self.setIcon(tool_icon(tool,26));self.setIconSize(QSize(26,26));self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon);self.setMinimumSize(54,54)
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

class OpacitySlider(QSlider):
    """The whole track is an immediate drag target, including the groove."""
    def __init__(self,*args):
        super().__init__(*args);self.setMinimumHeight(26);self.setFocusPolicy(Qt.StrongFocus)
    def point_value(self,pos):
        option=QStyleOptionSlider();self.initStyleOption(option)
        handle=self.style().subControlRect(QStyle.CC_Slider,option,QStyle.SC_SliderHandle,self)
        span=max(1,self.width()-handle.width());x=max(0,min(span,round(pos.x()-handle.width()/2)))
        return QStyle.sliderValueFromPosition(self.minimum(),self.maximum(),x,span,option.upsideDown)
    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return super().mousePressEvent(event)
        self.setFocus();self.setSliderDown(True);self.setValue(self.point_value(event.position()));event.accept()
    def mouseMoveEvent(self,event):
        if self.isSliderDown():self.setValue(self.point_value(event.position()));event.accept()
        else:super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton and self.isSliderDown():
            self.setValue(self.point_value(event.position()));self.setSliderDown(False);event.accept()
        else:super().mouseReleaseEvent(event)
    def wheelEvent(self,event):
        # Do not require hover activation/focus; the receiving track owns input.
        delta=event.angleDelta().y() or event.angleDelta().x()
        if delta:
            self.wheel_remainder=getattr(self,'wheel_remainder',0)+delta/120
            steps=int(self.wheel_remainder);self.wheel_remainder-=steps
            amount=self.pageStep() if event.modifiers()&(Qt.ControlModifier|Qt.ShiftModifier) else self.singleStep()
            self.setValue(self.value()+steps*amount);event.accept()
        else:super().wheelEvent(event)

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
        self.opacity=OpacitySlider(Qt.Horizontal);self.opacity.setRange(0,100);self.opacity.setValue(round(row['opacity']*100));self.opacity.setMinimumWidth(48);self.opacity.setMaximumWidth(100);self.opacity.setEnabled(not protected);self.opacity.setAccessibleName('Master opacity '+row['name']);self.opacity.setToolTip('Finished layer/subtree master opacity; applied once after its effects');master.addWidget(self.opacity,1)
        self.percent=QLabel(f"{row['opacity']*100:.0f}%");self.percent.setMinimumWidth(31);master.addWidget(self.percent);master.addStretch();self.opacity.sliderPressed.connect(lambda:editor.slider_begin('opacity'));self.opacity.valueChanged.connect(self.opacity_preview);self.opacity.sliderReleased.connect(lambda:QTimer.singleShot(0,lambda:editor.slider_commit('opacity')))
        if row['type'] in ('Image','Artwork','Paint'):
            add=icon_button('+','Create blank transparent child inside '+row['name'],lambda:editor.blank_child(self.identity));add.setEnabled(not inherited);line.addWidget(add)
        lock=icon_button('⛓' if inherited else '🔒' if row['locked'] else '🔓','Protected by ancestor Group' if inherited else 'Group lock protects subtree' if row['type']=='Group' else 'Lock own content and transforms only',lambda:QTimer.singleShot(0,lambda:editor.row_flag(self.identity,'locked')));lock.setEnabled(not inherited);line.addWidget(lock)
        if self.identity in editor.expanded:outer.addWidget(InlineControls(editor,row))
        self.setStyleSheet('LayerRow {border-bottom:1px solid #344049;}')
    def update_thumbnail(self,image):
        self.thumb.setPixmap(QPixmap.fromImage(image.scaled(28,24,Qt.KeepAspectRatio,Qt.SmoothTransformation)))
    def opacity_preview(self,value):
        e=self.editor;row=lookup(e.config).get(self.identity)
        if not row or effective(e.config,row,'locked'):return
        if e.slider_before is None:e.slider_begin('opacity')
        row['opacity']=value/100;self.percent.setText(str(value)+'%');e.schedule_preview();e.canvas.update()
        if not self.opacity.isSliderDown():e.opacity_timer.start(180)


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

class FocusHost(QWidget):
    def paintEvent(self,event):
        super().paintEvent(event)
        if self.property('keyboardActive'):
            p=QPainter(self);p.setPen(QPen(QColor('#b79ee8'),2));p.setBrush(Qt.NoBrush);p.drawRect(self.rect().adjusted(1,1,-1,-1));p.end()

class CompositionEditor(QMainWindow):
    def __init__(self,layers):
        super().__init__();self.layers=layers;layers.editor_view=self;central=FocusHost();self.setCentralWidget(central);layout=QVBoxLayout(central);layout.setContentsMargins(0,0,0,0)
        self.canvas=create_canvas(layers);layers.canvas=self.canvas;layout.addWidget(self.canvas,1)
        bar=QToolBar('Composition tools',self);bar.setObjectName('composition_tools');bar.setMovable(True);bar.setFloatable(True);bar.setAllowedAreas(Qt.AllToolBarAreas);bar.setToolTip('Drag the dotted grip to float or redock this toolbar');self.addToolBar(Qt.TopToolBarArea,bar);self.toolbar=bar
        layers.direct_buttons={}
        for tool,key in (('Brush','B'),('Pencil','P'),('Sampler','I'),('Eraser','E'),('Smudge','U'),('Select','V'),('Lasso','L'),('Wand','W'),('Transform','T'),('Crop','C')):
            if tool=='Select':
                self.cut_button=icon_button('', 'Cut selected pixels (Ctrl+X)',layers.cut_clipboard);self.cut_button.setIcon(tool_icon('Cut',26));self.cut_button.setIconSize(QSize(26,26));bar.addWidget(self.cut_button)
            button=DirectToolButton(layers,tool,tool+' ('+key+')');layers.direct_buttons[tool]=button;bar.addWidget(button)
            bar.addSeparator()
        for tool in ('Hand','Fill'):
            button=DirectToolButton(layers,tool,'Fill (F): click connected pixels with the chosen sidebar RGBA' if tool=='Fill' else 'Hand view tool');layers.direct_buttons[tool]=button;bar.addWidget(button)
        bar.addWidget(icon_button('?','Shortcut reference',layers.shortcut_reference))
        self.editor_undo=QPushButton('Undo');self.editor_redo=QPushButton('Redo');bar.addWidget(self.editor_undo);bar.addWidget(self.editor_redo);self.editor_undo.clicked.connect(lambda:layers.history(False,'editor'));self.editor_redo.clicked.connect(lambda:layers.history(True,'editor'))
        from native_raster import backend
        layers.backend_diagnostic=backend().status();layers.projection_diagnostic='GPU initializing' if isinstance(self.canvas,GPUCanvas) else 'CPU reference'
        from editor_pixels import PixelEditor
        layers.pixel_editor=PixelEditor(layers)
        from editor_colors import attach as attach_colors
        from editor_selection import attach as attach_selection
        attach_colors(self,layers);attach_selection(self,layers)
        from editor_fill import FillController
        layers.fill_controller=FillController(layers)
        from artwork_save_ui import ArtworkSaveController
        layers.artwork_save=ArtworkSaveController(layers)
        self.image_save=icon_button('','Save composition artwork image',lambda:layers.artwork_save.save());self.image_save.setIcon(tool_icon('Save',26,self.devicePixelRatioF()));self.image_save.setIconSize(QSize(26,26));bar.insertWidget(bar.actions()[0],self.image_save)
        self.image_save_as=icon_button('Save As…','Save composition artwork image As…',lambda:layers.artwork_save.save(True));self.image_save_as.setToolButtonStyle(Qt.ToolButtonTextOnly);self.image_save_as.setMinimumWidth(82);bar.insertWidget(bar.actions()[1],self.image_save_as)
        self.image_save_cancel=icon_button('Cancel save','Cancel pending artwork image saves',layers.artwork_save.cancel);self.image_save_cancel.setToolButtonStyle(Qt.ToolButtonTextOnly);self.image_save_cancel.setMinimumWidth(94);self.image_save_cancel_action=bar.insertWidget(bar.actions()[2],self.image_save_cancel);self.image_save_cancel_action.setVisible(False)
        self.zoom_buttons=[]
        for name,label,factor in (('ZoomIn','Zoom in',1.25),('ZoomOut','Zoom out',1/1.25)):
            button=icon_button('',label,lambda checked=False,f=factor:self.zoom_step(f));button.setIcon(tool_icon(name,26));button.setIconSize(QSize(26,26));bar.addWidget(button);self.zoom_buttons.append(button)
        saved=layers.shell.preferences.get('composition_toolbar')
        if saved:
            from PySide6.QtCore import QByteArray
            self.restoreState(QByteArray.fromHex(saved.encode()))
        for owned_bar in (bar,layers.color_toolbar):
            owned_bar.topLevelChanged.connect(lambda floating:layers.shell.preferences.update(composition_toolbar=bytes(self.saveState().toHex()).decode()))
            owned_bar.orientationChanged.connect(lambda orientation:layers.shell.preferences.update(composition_toolbar=bytes(self.saveState().toHex()).decode()))
        layers.sync_tool_ui()
    def tool(self,name):
        if not self.layers.resolve_pending():return
        self.canvas.set_tool(name)
    def zoom_step(self,factor):self.canvas.zoom=max(MIN_CANVAS_ZOOM,min(MAX_CANVAS_ZOOM,self.canvas.view().m11()*factor));self.canvas.update()
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
                canvas.zoom=max(MIN_CANVAS_ZOOM,min(MAX_CANVAS_ZOOM,canvas.zoom))
                canvas.pan=QPointF(-w*m[0,2]*canvas.zoom,-h*m[1,2]*canvas.zoom)
        canvas.update()

class Layers(QWidget):
    def __init__(self,shell):
        super().__init__();self.shell=shell;self.config=defaults();self.binding=None;self.selected=None;self.syncing=False;self.canvas=None;self.images={};self.models={};self.model_keys={};self.image_jobs={};self.image_errors={};self.reader=FrameReader();self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Editor native artwork');self.canvas_size=(1280,720);self.before=None;self.asset_key=None;self.collapsed=set();self.numeric_before=None;self.preview_active=False;self.art_jobs=[];self.edit_jobs=[];self.runtime_producers={};self.runtime_assets={};self.unsubmitted_assets={};self.await_recovery=False;self.retry_watch=None;self.drops=[];self.color_target='Brush';self.tool_states={t:dict(brush=dict(size=12.,opacity=1.,strength=.5,shape='Round',hardness=.8,flow=.5),color=QColor('#f6c490'),secondary=QColor('#ffffff')) for t in ('Brush','Pencil','Eraser','Smudge')};self.tool_states['Pencil']['brush']['shape']='Square';self.main_color=QColor('#f6c490');self._secondary_color=QColor('#ffffff');self.ui_timings=[];self.sample_scope='Active Layer';self.pending_paint=None;self.queued_paint=None;self.palettes=[];self.onboarding_pending=False
        self.restore_tool_preferences()
        self.preview_timer=QTimer(self);self.preview_timer.setSingleShot(True);self.preview_timer.setInterval(50);self.preview_timer.timeout.connect(self.send_preview)
        self.opacity_job=None;self.opacity_gesture=False;self.opacity_dirty=False
        self.opacity_timer=QTimer(self);self.opacity_timer.setSingleShot(True);self.opacity_timer.timeout.connect(lambda:self.slider_commit('opacity'))
        self.numeric_timer=QTimer(self);self.numeric_timer.setSingleShot(True);self.numeric_timer.setInterval(350);self.numeric_timer.timeout.connect(self.numeric_finish)
        outer=QVBoxLayout(self);outer.setContentsMargins(8,8,8,8);self.presentation=QComboBox();self.presentation.addItems(PRESENTATIONS);self.presentation.currentTextChanged.connect(lambda value:self.change_presentation(value));outer.addWidget(self.presentation)
        row=QHBoxLayout();outer.addLayout(row)
        for label,callback in (('+',self.add_menu),('Duplicate',self.duplicate),('Delete',lambda:self.delete())):
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
            slider=OpacitySlider(Qt.Horizontal) if key=='opacity' else QSlider(Qt.Horizontal);slider.setRange(low,high);slider.setToolTip('Drag previews locally; release commits one Undo command. Numeric fields retain the full range and precision.');slider.sliderPressed.connect(lambda k=key:self.slider_begin(k));slider.valueChanged.connect(lambda v,k=key:self.slider_preview(k,v));slider.sliderReleased.connect(lambda k=key:self.slider_commit(k));form.addRow(label,slider);self.sliders[key]=slider
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
        self.persistence_status=QLabel();self.persistence_status.setWordWrap(True);outer.addWidget(self.persistence_status)
        row=QHBoxLayout();outer.addLayout(row);self.undo=QPushButton('Undo');self.redo=QPushButton('Redo');self.undo.clicked.connect(lambda:self.history(False));self.redo.clicked.connect(lambda:self.history(True));row.addWidget(self.undo);row.addWidget(self.redo)
        retry=QPushButton('Retry saving');retry.setToolTip('Retry failed accepted PNGs and the latest failed revision-pinned checkpoint. Save As can secure a different destination.');retry.clicked.connect(self.retry_saving);row.addWidget(retry)
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.frames);self.timer.start()
    def resolve_pending(self):
        if self.slider_before is not None:
            self.slider_commit('opacity' if self.opacity_gesture else 'scale')
            if self.slider_before is not None:
                self.status.setText('Opacity gesture awaiting owner acknowledgement; retry this action after acceptance.');return False
        self.numeric_finish()
        if self.edit_jobs:
            self.status.setText('Completed edits awaiting owner outcome; retry this context/save action after acceptance. PNG saving does not block it.');return False
        if self.art_jobs:
            self.status.setText('Wait for the pending artwork write before switching, saving or closing.');return False
        if hasattr(self,'pixel_editor') and self.pixel_editor.gesture:self.pixel_editor.cancel()
        if self.canvas and self.canvas.stroke:self.canvas.cancel_drag()
        if not self.canvas or not self.canvas.points or self.canvas.tool in ('Select','Selection','Wand','Fill','Brush','Pencil','Eraser','Smudge'):return True
        answer=QMessageBox.question(self,'Unfinished '+self.canvas.tool.lower(),'Apply this preview, discard it, or keep editing?',QMessageBox.Apply|QMessageBox.Discard|QMessageBox.Cancel)
        if answer==QMessageBox.Cancel:return False
        if answer==QMessageBox.Apply:self.canvas.apply();return not self.canvas.points
        self.canvas.discard();return True
    def retry_saving(self):
        try:
            outcome=self.shell.client.request('raster_retry')['media_control']['raster']
            saves=self.shell.client.snapshot.get('media_control',{}).get('raster',{}).get('saves',[])
            failed=next((s for s in reversed(saves) if s['status']=='failed'),None)
            if failed:
                path,_=QFileDialog.getSaveFileName(self,'Recover retained revision '+str(failed['revision']),failed['path'],'Session (*.json)')
                if not path:self.status.setText('Retained checkpoint remains unsaved; choose Retry saving to export it.');return
                self.shell.client.request('save_retry',save_id=failed['id'],path=path)
            self.retry_watch=dict(session=self.binding[0],state=None)
            self.status.setText('Retry requested through owner: '+str(outcome['pending'])+' PNG jobs pending, '+str(outcome.get('retry_waiting',0))+' waiting; failures remain visible until secured. Pixels/history retained.')
        except Exception as exc:self.status.setText(str(exc))
    def selected_row(self):return lookup(self.config).get(self.selected)
    def focus_pane(self,widget):
        layers=widget is self or widget is not None and self.isAncestorOf(widget)
        canvas=widget is not None and (self.editor_view.isAncestorOf(widget) or any(p is widget.window() for p in self.palettes))
        state=(bool(layers),bool(canvas))
        if state==getattr(self,'focus_state',None):return
        self.focus_state=state;self.setProperty('keyboardActive',bool(layers));self.editor_view.setProperty('keyboardActive',bool(canvas));central=self.editor_view.centralWidget();central.setProperty('keyboardActive',bool(canvas));self.update();central.update()
    def paintEvent(self,event):
        super().paintEvent(event)
        if self.property('keyboardActive'):
            p=QPainter(self);p.setPen(QPen(QColor('#b79ee8'),2));p.setBrush(Qt.NoBrush);p.drawRect(self.rect().adjusted(1,1,-1,-1));p.end()
    def editable_target(self,row):
        reason='hidden artwork/subtree' if not effective(self.config,row,'enabled') else 'locked artwork/subtree' if effective(self.config,row,'locked') else None
        if reason is None and any(r['opacity']==0 for r in [row]+ancestors(self.config,row['id'])):reason='zero-opacity artwork/subtree'
        if reason:self.status.setText(row['name']+': '+reason+'. Show/unlock it before editing.');return False
        return True
    def valid_target(self,session,revision,target):
        media=self.shell.client.snapshot.get('media_control',{})
        # Queued completed edits have an explicit provisional revision chain.
        # Their owner validates the original target/revision on admission.
        if self.edit_jobs:
            return media.get('session')==session and self.binding==(session,revision) and lookup(self.config).get(target['id'])==target
        current=lookup(self.shell.client.snapshot.get('values',{}).get('media',self.config)).get(target['id'])
        return media.get('session')==session and media.get('revision')==revision and current==target
    def sync_tool_ui(self):
        if not self.canvas:return
        shown=self.canvas.cursor_method() if self.canvas.tool in ('Select','Selection','Wand') else self.canvas.tool
        for tool,button in getattr(self,'direct_buttons',{}).items():button.setChecked(tool==shown)
        self.sync_saved_masks()
        if hasattr(self,'quick_colors'):self.quick_colors.sync();self.color_toolbar.setVisible(self.canvas.tool in ('Brush','Pencil','Eraser','Smudge','Sampler','Fill','Select','Selection','Wand','Cut','Mask','Remove','Extract','Crop'))
        if hasattr(self,'selection_controls'):self.selection_controls.sync()
        for button,tool,shape in getattr(self,'tool_buttons',[]):button.setChecked(self.canvas.tool==tool if shape is None else self.canvas.shape==shape and self.canvas.tool in ('Selection','Mask','Remove','Cut','Extract'))
        if hasattr(self,'color_swatch'):self.color_swatch.setStyleSheet('background:'+self.brush_color.name()+'; color:'+('#10171c' if self.brush_color.lightness()>128 else '#ffffff'));self.color_swatch.setText(self.brush_color.name())
        for key,box in getattr(self,'brush_boxes',{}).items():box.setVisible(self.canvas.tool in ('Brush','Pencil','Eraser','Smudge') and (key!='strength' or self.canvas.tool=='Smudge') and (key not in ('hardness','flow') or self.canvas.tool in ('Brush','Eraser')))
        for button,key,value in getattr(self,'preset_buttons',[]):button.setChecked(self.brush[key]==value)
        row=self.selected_row()
        if self.canvas:
            state='No editing target' if row is None else row['name']+' • '+('hidden subtree' if not effective(self.config,row,'enabled') else 'locked' if effective(self.config,row,'locked') else row['type'])
            if row and not row['source_visible']:state+=' • own content hidden; children remain independent'
            if row:state+=' • own raster pixels' if row['type'] in ('Image','Artwork','Paint') else ' • layer branch'
            if self.canvas.points:state+=' • clipboard targets selected own pixels'
            if row and self.canvas.tool in ('Brush','Pencil','Eraser','Smudge') and row['type'] not in ('Image','Artwork','Paint'):state+=' • drawing requires still artwork'
            if row and row['type'] in ('Image','Artwork','Paint') and self.canvas.source_image(row) is None:state+=' • source pixels unavailable'
            self.target_diagnostic=self.canvas.tool+' → '+state
    def media_assets(self):
        data=self.shell.client.snapshot.get('media_library',{});return data.get('assets',[])+data.get('resources',[])+list(self.runtime_assets.values())
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
        if self.edit_jobs:return
        if force or binding!=self.binding:
            if self.canvas and (self.canvas.drag or self.canvas.stroke or self.canvas.interactive) or self.slider_before is not None or self.numeric_before is not None:return
            session_changed=self.binding and binding[0]!=self.binding[0]
            if session_changed:
                from pixel_selection import decode
                decode.cache_clear()
                if self.canvas:self.canvas.discard()
                for _,job in self.image_jobs.values():job.cancel()
                self.image_jobs.clear();self.images.clear();self.models.clear();self.image_errors.clear();self.model_keys.clear()
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
        for button,key in ((self.undo,'undo'),(self.redo,'redo'),(self.editor_view.editor_undo,'undo'),(self.editor_view.editor_redo,'redo')):
            recovery=history.get('editor',{});button.setEnabled(bool(recovery.get(key)));button.setText(key.title()+(' '+recovery[key] if recovery.get(key) else ''))
        row=self.selected_row();state=snap.get('media_frames',{}).get(self.selected,{})
        decode=(state.get('frame') or {}).get('decode_ms',0.)
        self.time.setText(f"{state.get('position',0):.2f} / {self.duration():.2f} s • {'Playing' if state.get('playing') else 'Paused'} • muted"+(f'\nDecode/refill {decode:.0f} ms • '+('slow source: frames skipped; reverse may stall' if decode>100 else 'high rates skip source frames') if row and row['type']=='Video' else ''))
        if not self.seek.isSliderDown():self.seek.setValue(round(state.get('position',0)/max(.001,self.duration())*10000))
        asset=next((a for a in self.media_assets() if row and a['id']==row['asset']),None)
        source_error=(asset.get('error') if asset else 'Reference removed; cached pixels may remain. Undo or Relink to recover.' if row and row['asset'] else '')
        error=state.get('error') or snap.get('preview',{}).get('image_layers',{}).get('error') or self.image_errors.get(row['asset'] if row else None,'') or source_error
        self.status.routine(error or 'Select artwork to edit • Undo/Redo recovers editor changes in order')
        self.load_images()
    def populate(self):
        # Preserve identity-bound rows and editors; selection/ACK refresh must
        # not recreate every widget and trigger whole-tree Qt polish/layout.
        from shiboken6 import isValid
        from PySide6.QtCore import QItemSelectionModel
        focus=QApplication.focusWidget();focus_name=focus.objectName() if focus else '';cursor=focus.cursorPosition() if isinstance(focus,QLineEdit) else None
        selected_ids={item.data(0,Qt.UserRole) for item in self.tree.selectedItems()};scroll=self.tree.verticalScrollBar().value();self.rebuilding=True;blocked=self.tree.blockSignals(True);self.tree.setUpdatesEnabled(False)
        self.row_widgets=getattr(self,'row_widgets',{});self.row_items=getattr(self,'row_items',{});self.row_signatures=getattr(self,'row_signatures',{});desired=lookup(self.config);removed=[]
        def children(parent,parent_node=None):
            siblings=sorted((r for r in self.config['layers'] if r['parent']==parent),key=lambda r:r['order'],reverse=True)
            for index,row in enumerate(siblings):
                identity=row['id'];node=self.row_items.get(identity);moved=False
                if node is None:node=QTreeWidgetItem();self.row_items[identity]=node;moved=True
                old_parent=node.parent();old_index=old_parent.indexOfChild(node) if old_parent else self.tree.indexOfTopLevelItem(node)
                if old_parent is not parent_node or old_index!=index:
                    if old_index>=0:(old_parent.takeChild if old_parent else self.tree.takeTopLevelItem)(old_index)
                    (parent_node.insertChild if parent_node else self.tree.insertTopLevelItem)(index,node);moved=True
                node.setData(0,Qt.UserRole,identity);node.setToolTip(0,row['name']+' • '+row['type']+' • '+identity)
                protected=effective(self.config,row,'locked');inherited=any(a['type']=='Group' and a['locked'] for a in [row]+ancestors(self.config,identity));flags=node.flags()|Qt.ItemIsDropEnabled|Qt.ItemIsDragEnabled
                if row['type'] not in ('Group','Image','Artwork','Paint') or inherited:flags&=~Qt.ItemIsDropEnabled
                if protected:flags&=~Qt.ItemIsDragEnabled
                node.setFlags(flags)
                # Frame/lease arrivals update thumbnails through frames(); a
                # new reader handle must not replace every row/control.
                # Stacking order is reconciled by node position, and is not a
                # displayed control value. Renumbering surviving siblings must
                # not rebuild their editors after one deletion/Undo.
                row_state=deepcopy(row);row_state.pop('order',None);row_state.pop('opacity',None)
                # Drawing changes immutable resource identity, not row controls.
                # Only reuse across the same native geometry/interpretation.
                if row['type'] in ('Image','Artwork','Paint'):
                    row_state.pop('asset',None);meta=self.metadata(row)
                    row_state['_working_geometry']=tuple(meta.get(k,1) for k in ('width','height','pixel_aspect'))
                signature=(row_state,identity in self.expanded,protected,inherited,self.canvas_size)
                widget=self.row_widgets.get(identity)
                if moved or widget is None or not isValid(widget) or self.row_signatures.get(identity)!=signature:
                    if widget is not None and isValid(widget):widget.hide();self.tree.removeItemWidget(node,0);widget.setParent(None);widget.deleteLater()
                    widget=LayerRow(self,row);self.tree.setItemWidget(node,0,widget);node.setSizeHint(0,widget.sizeHint());self.row_widgets[identity]=widget;self.row_signatures[identity]=signature
                if getattr(widget,'source_asset',None)!=row['asset']:
                    widget.source_asset=row['asset']
                    inline=widget.findChild(InlineControls)
                    if inline is not None:
                        w,h=self.base_dimensions(row);_,_,sx,sy,_=properties(row['transform'],self.canvas_size[0]/self.canvas_size[1])
                        for key,value in (('width',w*sx),('height',h*sy)):
                            box=inline.fields[key]
                            if not box.hasFocus():box.blockSignals(True);box.setValue(value);box.blockSignals(False)
                if not widget.opacity.isSliderDown():
                    widget.opacity.blockSignals(True);widget.opacity.setValue(round(row['opacity']*100));widget.opacity.blockSignals(False);widget.percent.setText(f"{row['opacity']*100:.0f}%")
                children(identity,node);node.setExpanded(identity not in self.collapsed);node.setSelected(identity in selected_ids or identity==self.selected and not selected_ids)
                if identity==self.selected and self.tree.currentItem() is not node:self.tree.setCurrentItem(node,0,QItemSelectionModel.NoUpdate)
        try:
            # Remove absent branch roots before comparing sibling positions;
            # deleting one row must not make every following row look moved.
            for identity in set(self.row_items)-set(desired):
                node=self.row_items[identity];parent=node.parent()
                if parent is None or parent.data(0,Qt.UserRole) in desired:
                    index=parent.indexOfChild(node) if parent else self.tree.indexOfTopLevelItem(node)
                    if index>=0:removed.append((parent.takeChild if parent else self.tree.takeTopLevelItem)(index))
                widget=self.row_widgets.pop(identity,None)
                if widget is not None and isValid(widget):widget.hide();widget.setParent(None);widget.deleteLater()
                self.row_signatures.pop(identity,None)
            children(None)
            self.row_items={k:v for k,v in self.row_items.items() if k in desired}
        finally:self.tree.blockSignals(blocked);self.tree.setUpdatesEnabled(True);self.tree.verticalScrollBar().setValue(scroll);self.rebuilding=False
        if focus_name.startswith('layer_'):
            # Removed editors may await deleteLater; search only retained rows.
            replacement=next((w.findChild(QWidget,focus_name) for w in self.row_widgets.values() if w.findChild(QWidget,focus_name) is not None),None)
            if replacement is not None and replacement.isEnabled() and replacement is not focus:
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
        if identity!=self.selected and hasattr(self,'fill_controller'):self.fill_controller.cancel()
        if identity!=self.selected and self.canvas and self.canvas.tool in ('Select','Selection','Wand','Fill','Brush','Pencil','Eraser','Smudge'):self.canvas.discard()
        if identity!=self.selected and not self.resolve_pending():self.populate();return
        if identity not in {i.data(0,Qt.UserRole) for i in self.tree.selectedItems()}:
            self.tree.blockSignals(True);self.tree.clearSelection();self.tree.blockSignals(False)
        self.selected=identity;self.last_selection=identity;self.populate();self.sync_controls()
        if self.canvas:self.canvas.update()
    def tree_select(self):
        item=self.tree.currentItem();identity=item.data(0,Qt.UserRole) if item else None
        if identity!=self.selected and hasattr(self,'fill_controller'):self.fill_controller.cancel()
        pending=self.art_jobs or self.numeric_before is not None or self.canvas and (self.canvas.points or self.canvas.stroke)
        if identity!=self.selected and self.canvas and self.canvas.tool in ('Select','Selection','Wand','Fill','Brush','Pencil','Eraser','Smudge'):self.canvas.discard();pending=False
        if identity!=self.selected and pending:QTimer.singleShot(0,lambda:self.select(identity));return
        if identity!=self.selected and self.canvas and self.canvas.tool in ('Select','Selection','Wand','Fill','Brush','Pencil','Eraser','Smudge'):self.canvas.discard()
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
        prior=before or deepcopy(self.config);self.preview_timer.stop()
        try:
            self.config=validate_scene(self.config)
            selection=self.selected if self.selected in lookup(prior) else getattr(self,'last_selection',None)
            data=dict(version=4,editor=deepcopy(self.config.get('editor',{})),canvas=self.config.get('canvas'),presentation=self.config['presentation'],layers=deepcopy(self.config['layers']),label=label,selection=self.selected,before_selection=selection,history_scope=scope,history_target=target,**self.binding_args())
            assets=list(self.unsubmitted_assets.values())
            if assets or self.edit_jobs or label=='Layer opacity slider':
                sources=getattr(self,'unsubmitted_sources',{})
                data.update(raster_assets=assets,raster_sources=list(sources.values()),raster_target=getattr(self,'raster_target',None))
                job=self.shell.client.submit('composition',**data)
                self.edit_jobs.append((job,[a['id'] for a in assets]+list(sources)))
                self.unsubmitted_sources={}
                self.unsubmitted_assets.clear();self.raster_target=None
                self.binding=(self.binding[0],self.binding[1]+1)
                self.populate();self.sync_controls();self.status.setText('Submitted '+label+' • awaiting owner acceptance; PNG saving is separate.')
            else:
                self.shell.client.request('composition',**data);self.preview_active=False
                media=self.shell.client.snapshot['media_control'];self.binding=(media['session'],media['revision']);self.refresh(True)
        except Exception as exc:
            from raster_resources import release
            for key in list(self.unsubmitted_assets)+list(getattr(self,'unsubmitted_sources',{})):
                self.unsubmitted_assets.pop(key,None);self.runtime_assets.pop(key,None)
                if key in self.runtime_producers:release(self.runtime_producers.pop(key))
            self.unsubmitted_sources={}
            self.raster_target=None;self.config=prior;self.status.setText(str(exc));self.populate();self.sync_controls();return False
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
        if self.opacity_gesture:self.opacity_dirty=True
        if not self.syncing and not self.preview_timer.isActive():self.preview_timer.start()
    def finish_opacity_preview(self):
        if self.opacity_job is None:return True
        if not self.opacity_job.done():return False
        job,self.opacity_job=self.opacity_job,None
        try:
            job.result();media=self.shell.client.snapshot['media_control'];self.binding=(media['session'],media['revision']);self.preview_active=True;return True
        except Exception as exc:
            self.opacity_dirty=False;self.opacity_gesture=False;self.slider_before=None
            self.cancel_preview();self.refresh(True);self.status.setText('Opacity preview failed; owner state restored: '+str(exc));return True
    def send_preview(self):
        if self.binding is None:return
        if self.opacity_gesture:
            if not self.finish_opacity_preview():self.preview_timer.start(16);return
            if not self.opacity_dirty:return
            self.opacity_dirty=False
            data=dict(version=4,canvas=self.config.get('canvas'),presentation=self.config['presentation'],layers=deepcopy(self.config['layers']),selection=self.selected,**self.binding_args())
            self.opacity_job=self.shell.client.edits.submit(self.shell.client.request,'composition_preview',**data)
            self.preview_timer.start(16);return
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
        if row['type']!='Group' and self.canvas:
            bounds=self.canvas.content_bounds(row);c=row['crop'];fw*=(bounds[2]-bounds[0])/(c[2]-c[0]);fh*=(bounds[3]-bounds[1])/(c[3]-c[1])
        return fw*self.canvas_size[0],fh*self.canvas_size[1]
    def slider_begin(self,key=None):
        self.opacity_timer.stop()
        if self.slider_before is None:self.slider_before=deepcopy(self.config)
        self.opacity_gesture=key=='opacity'
    def slider_preview(self,key,value):
        if self.syncing:return
        row=self.selected_row()
        if not row or effective(self.config,row,'locked'):return
        if self.slider_before is None:self.slider_begin(key)
        self.fields[key].blockSignals(True);self.fields[key].setValue(value/10);self.fields[key].blockSignals(False)
        if key=='opacity':row['opacity']=value/1000
        else:
            x,y,s,sy,r=properties(row['transform'],self.canvas_size[0]/self.canvas_size[1]);s=value/1000
            if row['aspect_lock']:sy=s
            row['transform']=transform(x,y,s,sy,r,self.canvas_size[0]/self.canvas_size[1])
        if self.canvas:self.canvas.update()
        self.schedule_preview()
        if not self.sliders[key].isSliderDown():
            if key=='opacity':self.opacity_timer.start(180)
            else:self.slider_commit(key)
    def slider_commit(self,key):
        self.opacity_timer.stop()
        if self.opacity_gesture:
            self.preview_timer.stop()
            if not self.finish_opacity_preview():self.opacity_timer.start(16);return
            self.opacity_dirty=False;self.opacity_gesture=False
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
    def delete(self,identity=None):
        chosen={identity} if identity is not None else {item.data(0,Qt.UserRole) for item in self.tree.selectedItems()} or ({self.selected} if self.selected else set())
        def closure():return {r['id'] for r in self.config['layers'] if r['id'] in chosen or any(a['id'] in chosen for a in ancestors(self.config,r['id']))}
        ids=closure()
        if not ids:return False
        if any(effective(self.config,r,'locked') for r in self.config['layers'] if r['id'] in ids):self.status.setText('Nothing deleted: the branch contains locked content or a protecting Group.');return False
        binding=self.binding;scene=deepcopy(self.config)
        answer=QMessageBox.question(self,'Delete layer branch','Everything within layer will be deleted',QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if answer!=QMessageBox.Yes:return False
        current=self.shell.client.snapshot.get('media_control',{})
        if self.binding!=binding or (current.get('session'),current.get('revision'))!=binding or self.config!=scene or closure()!=ids:
            self.status.setText('Layer branch changed while confirmation was open; nothing deleted. Review and retry.');return False
        if not self.resolve_pending():return False
        if self.binding!=binding or self.config!=scene:
            self.status.setText('Pending edit changed the branch; review and retry deletion.');return False
        before=deepcopy(self.config);self.last_selection=self.selected or next(iter(chosen));self.config['layers']=[r for r in self.config['layers'] if r['id'] not in ids];renumber(self.config);self.selected=None
        return self.commit('Delete '+str(len(ids))+' layers (one batch)',before)
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
    def history(self,redo,scope='editor'):
        if hasattr(self,'fill_controller'):self.fill_controller.cancel()
        if self.canvas and self.canvas.stroke:self.canvas.cancel_drag()
        if self.art_jobs:self.status.setText('Finish native preparation before recovery.');return
        target=self.selected if scope=='drawing' else None;key='redo' if redo else 'undo'
        history=self.shell.client.snapshot.get('media_control',{}).get('history',{})
        state=history.get('drawing',{}).get(target,{}) if scope=='drawing' else history.get('editor',{}) if scope=='editor' else history
        if not self.edit_jobs and not state.get(key):self.status.setText('Nothing to '+key+' in '+('this layer drawing history.' if scope=='drawing' else 'editor history.' if scope=='editor' else 'Layers management history.'));return
        if self.edit_jobs or self.runtime_assets:
            try:
                job=self.shell.client.submit('composition_history',redo=redo,scope=scope,target=target,media_session=self.binding[0])
                self.edit_jobs.append((job,[]));self.await_recovery=True;self.status.setText('Applying '+key+' • '+scope+' recovery; saving continues independently.')
            except Exception as exc:self.status.setText(str(exc))
        else:
            self.shell.safe(lambda:self.shell.client.request('composition_history',redo=redo,scope=scope,target=target,media_session=self.binding[0]));self.refresh(True)
        if self.canvas:self.canvas.update()
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
        for label,callback in (('Copy layer/subtree',self.copy_branch),('Paste layer/subtree',self.paste_branch),('Duplicate layer/subtree',self.duplicate),('Delete layer/subtree',lambda:self.delete(row['id']) if row else self.delete())):menu.addAction(label,callback)
        ids=[i.data(0,Qt.UserRole) for i in self.tree.selectedItems()]
        if row:
            if not ids:ids=[row['id']]
            menu.addAction('Save artwork image…',lambda:self.artwork_save.save(ids=ids));menu.addAction('Save artwork image As…',lambda:self.artwork_save.save(True,ids=ids))
        if row and row['type'] in ('Image','Artwork','Paint'):menu.addAction('Create blank drawing child',lambda:self.blank_child(row['id']))
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
    def copy_branch(self):
        row=self.selected_row()
        if not row:return
        rows=[row]+[r for r in self.config['layers'] if any(a['id']==row['id'] for a in ancestors(self.config,r['id']))];ids={r['asset'] for r in rows};mime=QMimeData();payload=json.dumps(dict(version=1,layers=rows,assets=[a for a in self.config['assets'] if a['id'] in ids])).encode()
        self.layer_clipboard=payload;mime.setData('application/x-zerawave-layers',payload);QApplication.clipboard().setMimeData(mime);self.status.setText('Copied layer artwork and source references; new IDs on Paste.')
    def paste_branch(self):
        mime=QApplication.clipboard().mimeData()
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
        if not canvas.interactive and QApplication.focusWidget() is self.canvas and self.canvas.tool in ('Brush','Pencil') and not mods and Qt.Key_0<=key<=Qt.Key_9:
            value=100 if key==Qt.Key_0 else (key-Qt.Key_0)*10;self.tool_value(self.canvas.tool,'opacity',value/100);self.status.setText('Stroke opacity '+str(value)+'% • active gesture retains its starting value');return True
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
        if key==Qt.Key_Escape:
            if hasattr(self,'fill_controller'):self.fill_controller.cancel()
            if self.pixel_editor.gesture:self.pixel_editor.cancel();return True
            canvas.cancel_drag();return True
        if key in (Qt.Key_Return,Qt.Key_Enter) and self.pixel_editor.gesture and self.pixel_editor.gesture['kind']=='move':self.pixel_editor.release(None);return True
        if key in (Qt.Key_Return,Qt.Key_Enter) and canvas.drag and canvas.drag[0]!='pan':
            drag,canvas.drag=canvas.drag,None;self.commit('Canvas '+drag[0],drag[3]);canvas.update();return True
        if key in (Qt.Key_Return,Qt.Key_Enter) and canvas.points and canvas.tool=='Crop':canvas.closed_path=True;canvas.apply();return True
        if ctrl:
            if key==Qt.Key_D:canvas.discard();return True
            if key==Qt.Key_C:self.copy_layer();return True
            if key==Qt.Key_X:self.cut_clipboard();return True
            if key==Qt.Key_V:self.paste_layer();return True
            if key in (Qt.Key_Z,Qt.Key_Y):
                self.history(key==Qt.Key_Y or shift,'editor');return True
            return False
        if mods&Qt.AltModifier:return False
        if shift and key==Qt.Key_D:self.duplicate();return True
        if key in (Qt.Key_G,Qt.Key_R,Qt.Key_S):canvas.begin_interactive({Qt.Key_G:'move',Qt.Key_R:'rotate',Qt.Key_S:'scale'}[key]);return True
        if key==Qt.Key_Space:canvas.space_pan=True;return True
        if key in (Qt.Key_BracketLeft,Qt.Key_BracketRight):self.brush['size']=max(1,min(512,self.brush['size']*(1/1.2 if key==Qt.Key_BracketLeft else 1.2)));self.sync_tool_ui();canvas.update();return True
        tools={Qt.Key_V:'Select',Qt.Key_W:'Wand',Qt.Key_B:'Brush',Qt.Key_P:'Pencil',Qt.Key_E:'Eraser',Qt.Key_I:'Sampler',Qt.Key_U:'Smudge',Qt.Key_C:'Crop',Qt.Key_T:'Transform',Qt.Key_H:'Hand',Qt.Key_F:'Fill'}
        if key in (Qt.Key_M,Qt.Key_L):
            if not self.resolve_pending():return True
            self.choose_selection('Select' if key==Qt.Key_M else 'Lasso');return True
        if key in tools:self.choose_tool(tools[key]);return True
        if key in (Qt.Key_Delete,Qt.Key_Backspace):self.pixel_editor.delete();return True
        if key in (Qt.Key_Left,Qt.Key_Right,Qt.Key_Up,Qt.Key_Down) and row and self.editable_target(row):
            before=deepcopy(self.config);step=10 if shift else 1;w,h=self.canvas_size;row['transform'][4]+=(-step if key==Qt.Key_Left else step if key==Qt.Key_Right else 0)/w;row['transform'][5]+=(-step if key==Qt.Key_Up else step if key==Qt.Key_Down else 0)/h;self.commit('Nudge layer',before);return True
        return key==Qt.Key_Shift
    def shortcut_reference(self):
        QMessageBox.information(self,'Editor shortcuts','V Select pixels • M Rectangle • L Lasso • W Magic Wand\nT Transform whole layer • G/R/S move/rotate/scale; Enter accepts, Esc cancels\nB Brush • P Pencil • E Eraser • I Sampler • U visible-artwork Smudge\nF Fill connected region: left Main / right Secondary • C Crop (Apply crop / Cancel crop)\nCtrl+C Copy pixels • Ctrl+X Cut pixels • Ctrl+V Paste new layer • Delete clears selected pixels\nCtrl+D Deselect • Ctrl+Z Undo editor • Ctrl+Shift+Z / Ctrl+Y Redo editor\nDrag inside pixel selection moves content on the same raster. Pasted layers use Transform handles.\nH Hand • wheel zoom 15% • Ctrl+wheel fine zoom 2% • magnifiers 25% • zoom 2%–25600% (wheel anchored at pointer) • Space held pan • [ / ] size • digits stroke opacity\nBrush/Pencil left Main, right Secondary; Fill/Sampler left Main, right Secondary. No canvas popup. Text fields retain ordinary typing/clipboard/Undo.\nLayers context menu provides explicit layer/subtree commands.')
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
    def copy_pixels(self,cut=False):return self.pixel_editor.copy(cut)
    def copy_layer(self):return self.pixel_editor.copy(False)
    def paste_layer(self):return self.pixel_editor.paste()
    def cut_clipboard(self):return self.pixel_editor.copy(True)
    def paste_pixels(self):return self.pixel_editor.paste()
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
        self.resource_generated(image,provenance,callback,target)
    def resource_generated(self,image,provenance,callback,target=None,prepared=None):
        from raster_resources import snapshot,release
        from native_raster import NativeImage,backend
        if backend().available and not isinstance(image,NativeImage):
            try:image=backend().storage().from_image(image)
            except Exception as exc:self.status.setText('Operation rejected, not saved. Accepted content retained; redraw stroke/repeat action after pressure is relieved: '+str(exc)[:180]);return False
        import os,uuid
        from pathlib import Path
        if len(self.edit_jobs)>=16:self.status.setText('Completed operation rejected, not saved: GUI command queue full. Redraw stroke/repeat action after commands drain.');return False
        identity=uuid.uuid4().hex;lease=None
        try:
            desc,lease=prepared.take_image() if prepared is not None else snapshot(image)
            from raster_tiles import unique_bytes
            retained=[p.desc for p in self.runtime_producers.values() if hasattr(p,'desc')]
            flat=sum(p.size for p in self.runtime_producers.values() if not hasattr(p,'desc'))
            if flat+unique_bytes(retained+[desc])>128*1024*1024:raise ValueError('GUI transfer reached 128 MiB; completed stroke rejected, not saved. Redraw after transfers drain.')
            from native_raster import NativeImage
            cached=image if isinstance(image,NativeImage) else image.copy()
            if cached.isNull():raise MemoryError('Cannot allocate the native editor snapshot cache.')
            folder=Path(os.environ.get('ZERAWAVE_ARTWORK_STORE') or Path(__file__).resolve().parents[2]/'work/studio/artwork')
            record=dict(id=identity,name='Editable artwork',kind='Images',path=str((folder/(identity+'.png')).resolve()),managed=True,internal=not provenance.startswith('Resized derivative '),provenance=provenance,status='Ready',runtime=desc,metadata=dict(width=image.width(),height=image.height(),bytes=desc['bytes'],mtime_ns=0))
            self.runtime_producers[identity]=lease;self.runtime_assets[identity]=record;self.unsubmitted_assets[identity]=record;self.images[identity]=cached;self.raster_target=deepcopy(target)
            callback(record);self.onboarding_pending=False
            if not any(identity in ids for _,ids in self.edit_jobs):raise ValueError(self.status.text() or 'Raster operation did not submit; previous content retained.')
            return True
        except Exception as exc:
            if identity in self.unsubmitted_assets:
                self.unsubmitted_assets.pop(identity,None);self.runtime_assets.pop(identity,None);self.images.pop(identity,None)
                self.runtime_producers.pop(identity,None)
            if lease and not any(identity in ids for _,ids in self.edit_jobs):release(lease)
            self.onboarding_pending=False;self.status.setText('Raster not submitted: '+str(exc)[:200]);return False
    def generated_work(self,prepare,provenance,callback,target=None):
        if self.art_jobs:self.status.setText('Native preparation pending; wait before another structural import.');return
        token=(self.binding[0],self.binding[1],deepcopy(target)) if target else None
        self.art_jobs.append((self.binding[0],self.pool.submit(prepare),(provenance,callback),token))
        self.status.setText('Preparing native source pixels…')
    def blank_child(self,identity=None):
        if not self.resolve_pending():return
        parent=lookup(self.config).get(identity or self.selected)
        if not parent:self.status.setText('Child not created: that parent is unavailable.');return
        try:self.artwork_parent(parent['id'])
        except ValueError as exc:self.status.setText(str(exc));return
        if len(self.config['layers'])>=MAX_LAYERS:self.status.setText('Child not created: 32-layer capacity.');return
        if parent['type']=='Group':
            self.selected=parent['id'];return self.blank_layer(True)
        meta=self.metadata(parent);w,h=meta.get('width'),meta.get('height')
        if not w or not h:self.status.setText('Child not created: wait for native source dimensions.');return
        image=QImage(w,h,QImage.Format_ARGB32_Premultiplied)
        if image.isNull():self.status.setText('Child not created: allocation failed.');return
        image.fill(0);identity=parent['id'];template=deepcopy(parent)
        self.generated(image,'Transparent drawing child of '+parent['name'],lambda asset:self.create_child(dict(asset,name='Drawing'),identity,'Paint',template,label='Create blank drawing child',prepared=True),parent)
    def extract_child(self,operation):return self.cut_child(operation,False)

    def save_paint(self,stroke,image,prepared=None):
        identity=stroke['row']
        # Retain immutable original pixels alongside the first accepted stroke.
        # Recovery must not wait behind an image/model decoder or reopen a file.
        records={a['id']:a for a in self.media_assets()};old=records.get(stroke['asset'])
        if old and 'runtime' not in old:
            from raster_resources import snapshot
            try:
                desc,lease=prepared.take_source() if prepared is not None else snapshot(self.canvas.source_image(stroke['target']))
                source=dict(old,runtime=desc,source_snapshot=True)
                self.runtime_producers[old['id']]=lease;self.runtime_assets[old['id']]=source
                self.unsubmitted_sources={old['id']:source}
                from native_raster import NativeImage
                if isinstance(image,NativeImage):image.names.update(stroke['base'].names)
            except Exception as exc:self.status.setText('Cannot retain recovery source; stroke not submitted: '+str(exc));return False
        def finish(asset):
            row=lookup(self.config).get(identity)
            if not row or row['asset']!=stroke['asset']:raise ValueError('Drawing target changed; stroke not submitted.')
            before=deepcopy(self.config);row['asset']=asset['id'];row['cut_alignment']=None
            from media_registry import reference
            self.config['assets'].append(reference(asset))
            used={r['asset'] for r in self.config['layers']};self.config['assets']=[a for a in self.config['assets'] if a['id'] in used]
            if self.commit(stroke['tool']+' own-content stroke',before,scope='drawing',target=identity):self.canvas.discard()
        applied=self.resource_generated(image,'Editable drawing stroke',finish,stroke['target'],prepared=prepared)
        if not applied:
            # A preflight allocation/queue failure must release an unsubmitted
            # recovery-source reservation as well as the edited snapshot.
            from raster_resources import release
            for key in list(self.unsubmitted_sources):
                self.unsubmitted_sources.pop(key,None);self.runtime_assets.pop(key,None)
                lease=self.runtime_producers.pop(key,None)
                if lease:release(lease)
        return applied
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
            self.images.setdefault(asset['id'],piece)
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
            self.selected=row['id'];self.last_selection=before_selection;self.images.setdefault(asset['id'],image)
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
            self.selected=row['id'];self.images.setdefault(asset['id'],image);self.commit('Editable frame snapshot (one frame)',before)
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
        if any(a['id']==row['asset'] and a.get('runtime') for a in self.media_assets()):
            # Accepted snapshots are immutable, including retained originals.
            # A replacement uses a new reference and the existing management
            # transaction; old drawing/history consumers retain their pixels.
            self.drop_files([path],row['id'],'replace')
        elif row['asset'] in known:self.shell.safe(lambda:self.shell.client.request('media_action',op='relink',asset=row['asset'],path=path))
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
    def choose_selection(self,method):
        target='Wand' if method=='Wand' else 'Select';shape='Freehand' if method=='Lasso' else 'Rectangle'
        if self.canvas.tool!=target or self.canvas.shape!=shape:
            if not self.resolve_pending():return
            self.canvas.discard();self.canvas.shape=shape;self.canvas.set_tool(target)
        self.reveal();self.canvas.setFocus();self.sync_tool_ui()
    def choose_tool(self,tool):
        if tool in ('Select','Lasso','Wand'):return self.choose_selection(tool)
        if self.canvas.tool==tool:self.canvas.setFocus();self.sync_tool_ui();return
        if self.resolve_pending():
            if tool=='Transform':self.canvas.discard()
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
    def brush_color(self):return self.main_color
    @brush_color.setter
    def brush_color(self,color):
        self.main_color=QColor(color)
        for state in self.tool_states.values():state['color']=QColor(color)
    @property
    def secondary_color(self):return self._secondary_color
    @secondary_color.setter
    def secondary_color(self,color):
        self._secondary_color=QColor(color)
        for state in self.tool_states.values():state['secondary']=QColor(color)
    def receive_sample(self,color,secondary=False):
        if color is None or color.alpha()==0:self.status.setText('No visible pixel sampled; drawing colors unchanged.');return
        if secondary:self.secondary_color=color
        else:self.brush_color=color
        channel='Secondary' if secondary else 'Main'
        if hasattr(self,'quick_colors'):self.quick_colors.assignment=channel.lower()
        self.remember_tools();self.sync_tool_ui();self.status.setText('Sampled '+color.name(QColor.HexArgb)+' → shared '+channel+'; artwork unchanged.')
    def remember_tools(self):
        self.shell.preferences['media_main_rgba']=self.main_color.name(QColor.HexArgb)
        self.shell.preferences['media_secondary_rgba']=self.secondary_color.name(QColor.HexArgb)
        self.shell.preferences['media_tool_settings']={t:dict(brush=dict(v['brush']),color=v['color'].name(QColor.HexArgb),secondary=v['secondary'].name(QColor.HexArgb)) for t,v in self.tool_states.items()}
    def restore_tool_preferences(self):
        for tool,values in self.shell.preferences.get('media_tool_settings',{}).items():
            if tool not in self.tool_states or not isinstance(values,dict):continue
            brush=values.get('brush',{});state=self.tool_states[tool]
            for key in state['brush']:
                value=brush.get(key)
                if key=='shape':
                    if value in ('Round','Square'):state['brush'][key]=value
                elif isinstance(value,(int,float)) and math.isfinite(value) and (1<=value<=512 if key=='size' else 0<=value<=1):state['brush'][key]=value
            secondary=QColor(values.get('secondary','#ffffffff'))
            if secondary.isValid():state['secondary']=secondary
        secondary=QColor(self.shell.preferences.get('media_secondary_rgba',self.tool_states['Brush']['secondary'].name(QColor.HexArgb)))
        if secondary.isValid():self.secondary_color=secondary
        # Deterministic one-time migration: saved shared Main, otherwise old Brush Main.
        legacy=self.shell.preferences.get('media_tool_settings',{}).get('Brush',{}).get('color','#fff6c490')
        color=QColor(self.shell.preferences.get('media_main_rgba',legacy))
        self.brush_color=color if color.isValid() else QColor('#f6c490')
        self.remember_tools()
    def tool_settings(self,tool):
        if tool=='Zoom':return
        if tool!=self.canvas.cursor_method():self.choose_tool(tool)
        if self.canvas.cursor_method()!=tool:return
        if tool=='Hand':return
        self.color_toolbar.show();self.quick_colors.sync();self.tool_scroll.setFocus(Qt.OtherFocusReason)
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
        # Compatibility entry point arms the paint bucket; only artwork clicks write.
        self.choose_tool('Fill')
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
            self.config['assets'].append(reference(asset));self.images.setdefault(asset['id'],image);self.selected=row['id'];self.commit('Create drawing layer',before);self.canvas.setFocus();self.status.setText('Layer ready. Editor Undo recovers drawing and layer edits in order.')
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
            if 'runtime' in asset:
                if identity not in self.images:
                    try:
                        from raster_resources import image as raster_image
                        if sum(i.sizeInBytes() for i in self.images.values())+asset['runtime']['bytes']>192*1024*1024:raise ValueError('Native editor cache exceeds 192 MiB; hide an unused source.')
                        self.images[identity]=raster_image(asset['runtime'])
                        if self.canvas:self.canvas.update()
                    except Exception as exc:self.image_errors[identity]=str(exc)[:180]
                continue
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
                if 'runtime' in a:
                    from raster_resources import image as raster_image
                    return raster_image(a['runtime'])
                meta,data=decode_image(a['path']);pixels=QImage(data,meta['width'],meta['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied)
                from native_raster import backend
                return backend().storage().from_image(pixels) if backend().available else pixels
            self.image_jobs[identity]=(key,self.pool.submit(decode))
    def frames(self):
        changed=False
        from raster_resources import release
        completed=False
        for job,ids in list(self.edit_jobs):
            if not job.done():continue
            try:
                job.result()
                for key in ids:
                    if key in self.runtime_producers:release(self.runtime_producers.pop(key))
                    self.runtime_assets.pop(key,None)
                self.status.setText('Owner accepted/applied edit • canvas/output publication ordered; PNG durability shown separately.')
            except ValueError as exc:
                for key in ids:
                    if key in self.runtime_producers:release(self.runtime_producers.pop(key))
                    self.runtime_assets.pop(key,None)
                self.status.setText('Completed operation rejected; not saved. Redraw stroke after work drains or Retry succeeds. Accepted content retained: '+str(exc)[:180])
            except Exception as exc:
                self.status.setText('Unknown owner outcome: '+str(exc)[:160]+' • retain this Studio instance for recovery.')
                continue
            self.edit_jobs.remove((job,ids));completed=True
        if completed and not self.edit_jobs:
            self.await_recovery=False
            active=self.canvas.stroke if self.canvas else None
            # The accepted predecessor must not invalidate a newer live gesture.
            if active:
                media=self.shell.client.snapshot['media_control'];current=lookup(self.shell.client.snapshot['values']['media']).get(active['row'])
                if current==active['target']:active.update(revision=media['revision']);self.binding=(media['session'],media['revision'])
                else:self.canvas.cancel_drag()
            self.refresh(True);changed=True
        for session,job,callback,token in list(self.art_jobs):
            if not job.done():continue
            self.art_jobs.remove((session,job,callback,token));self.onboarding_pending=False
            try:
                if session!=self.shell.client.snapshot.get('media_control',{}).get('session'):continue
                if token and not self.valid_target(*token):self.status.setText('Target/session changed; provisional preparation cancelled.');continue
                provenance,finish=callback;self.resource_generated(job.result(),provenance,finish,token[2] if token else None)
            except Exception as exc:self.status.setText('Operation rejected, not saved. Accepted content retained; redraw stroke/repeat action after pressure is relieved: '+str(exc)[:180])
        raster=self.shell.client.snapshot.get('media_control',{}).get('raster',{})
        failures=raster.get('failures',{});pending=raster.get('pending',0)
        if failures:
            message=next(iter(failures.values()))
            text=('Accepted artwork is not saved. Retry saving or Save As. '+message)
        elif pending:text=f'Accepted artwork is waiting to save: {pending} writes pending.'
        else:text='No artwork writes pending. Save session to preserve current edits.'
        self.persistence_status.setText(text)
        store=raster.get('stores',{}).get(raster.get('working_store'),{})
        free=store.get('physical_free_bytes');reserve=store.get('reserved_bytes',0);headroom=store.get('headroom_bytes',0)
        if free is not None and free-reserve<=headroom and not failures:
            self.persistence_status.setText('Destination space is below checkpoint headroom; new writes may fail. Accepted pixels remain in this editor.')
        detail=raster.get('working_store','')
        if store:detail+=f"\nPNG bytes: {store['bytes']:,}; reservations: {reserve:,}; free: {format(free,',') if free is not None else 'unavailable'}; headroom: {headroom:,}; optional budget: {store.get('optional_budget_bytes') or 'none'}; protected legacy: {store.get('protected_legacy_bytes',0):,}"
        self.persistence_status.setToolTip(detail)
        request=getattr(self.shell,'requested_save',None)
        if request:
            outcome=next((s for s in raster.get('saves',[]) if s['id']==request[0]),None)
            if outcome and outcome['status']=='durable':
                import hashlib
                same_session=outcome['session']==self.shell.client.snapshot['media_control']['session']
                verified=hashlib.sha256(request[1].encode()).hexdigest()==outcome['values_sha256']
                if same_session and verified:self.shell.saved_art=request[1]
                self.shell.requested_save=None
                newer=json.dumps(self.shell.owner.values(),sort_keys=True)!=request[1]
                self.shell.statusBar().showMessage('Saved revision '+str(outcome['revision'])+('; current work remains unsaved.' if newer or not same_session or not verified else '.'))
            elif outcome and outcome['status']=='cancelled':
                self.shell.requested_save=None;self.shell.statusBar().showMessage('Save cancelled; accepted content remains in this open editor.')
            elif outcome and outcome['status']=='failed':
                self.shell.requested_save=None;self.shell.statusBar().showMessage('Save failed; prior session and accepted content retained. Save As to recover: '+outcome['error'])
        if raster.get('failures'):self.status.routine('Accepted pixels retained, PNG not durable. Retry saving or Save As/recovery export. '+next(iter(raster['failures'].values())))
        if self.retry_watch:
            if self.retry_watch['session']!=self.binding[0]:self.retry_watch=None
            else:
                pending=raster.get('pending',0);waiting=raster.get('retry_waiting',0);saves=raster.get('saves',[])
                save_pending=sum(s['status']=='pending' for s in saves);failed=raster.get('failures',{});save_failed=next((s['error'] for s in reversed(saves) if s['status']=='failed'),'')
                state=(pending,waiting,save_pending,len(failed),save_failed)
                if state!=self.retry_watch['state']:
                    self.retry_watch['state']=state
                    if pending or waiting or save_pending:self.status.setText(f'Retry in progress: {pending} PNG jobs, {waiting} waiting, {save_pending} pinned saves. Accepted pixels retained; rejected strokes must be redrawn.')
                    elif failed or save_failed:
                        self.status.setText('Retry finished with failed writes; accepted pixels/history remain unsaved and retained. Correct the destination or use Save As, then Retry. Rejected strokes must be redrawn. '+(next(iter(failed.values())) if failed else save_failed));self.retry_watch=None
                    else:
                        self.status.setText('Retry finished: accepted raster dependencies secured; check the requested save revision separately. Rejected strokes remain unsaved and must be redrawn.');self.retry_watch=None

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
        row=self.selected_row()
        if row and self.canvas and 'source pixels unavailable' in getattr(self,'target_diagnostic','') and self.canvas.source_image(row) is not None:self.sync_tool_ui()
    def close_resources(self):
        if hasattr(self,'fill_controller'):self.fill_controller.close()
        from pixel_selection import decode
        decode.cache_clear()
        if self.canvas and hasattr(self.canvas,'close_gpu'):self.canvas.close_gpu()
        from raster_resources import release
        for lease in self.runtime_producers.values():release(lease)
        self.runtime_producers.clear()
        if hasattr(self,'artwork_save'):self.artwork_save.close()
        self.opacity_timer.stop();self.cancel_preview();self.timer.stop();self.preview_timer.stop();self.numeric_timer.stop();self.web_sources.close();self.reader.close();self.pool.shutdown(wait=False,cancel_futures=True)
        if hasattr(self,'selection_controls'):self.selection_controls.cancel();self.selection_controls.timer.stop()
        if self.canvas and hasattr(self.canvas,'sample_timer'):self.canvas.sample_timer.stop()
        for palette in self.palettes:palette.close()
