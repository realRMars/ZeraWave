"""Composition Editor quick colors/sizes and bounded own-content sampling."""
import math,time
from copy import deepcopy
import numpy as np
from PySide6.QtCore import Qt,QTimer,QRectF,QPointF,QSize,QEvent
from PySide6.QtGui import QColor,QImage,QPainter,QTransform
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QToolBar,QComboBox,QDoubleSpinBox,QColorDialog,QMenu,QScrollArea,QFormLayout,QCheckBox,QSpinBox,QSizePolicy
BASES=['#000000','#ffffff','#555555','#aaaaaa','#800000','#ff0000','#ff8080','#ff8000','#ffc040','#ffff00','#808000','#80ff00','#008000','#00c060','#00ffff','#008080','#0080ff','#0000ff','#000080','#8000ff','#ff00ff','#800080','#ff80c0','#804020']

class CompactSpin(QDoubleSpinBox):
    def textFromValue(self,value):return format(value,'.10f').rstrip('0').rstrip('.')

class QuickColors(QWidget):
    def __init__(self,e):
        super().__init__();self.e=e;self.assignment='main';self.hover_color=None;self.setMinimumWidth(216);self.active_tool=None
        outer=QVBoxLayout(self);outer.setContentsMargins(4,4,4,4);self.title=QLabel();outer.addWidget(self.title);self.color_block=QWidget();outer.addWidget(self.color_block)
        body=QVBoxLayout(self.color_block);body.setContentsMargins(4,4,4,4);body.setSpacing(3)
        self.receiver=QLabel();body.addWidget(self.receiver)
        self.chips={}
        for key,label in (('main','Main / Left button'),('secondary','Secondary / Right button')):
            b=QPushButton(label);b.setCheckable(True);b.clicked.connect(lambda checked=False,k=key:self.assign(k));body.addWidget(b);self.chips[key]=b
        self.swatches=QWidget();palette=QVBoxLayout(self.swatches);palette.setContentsMargins(0,0,0,0);palette.setSpacing(3)
        self.base_grid=QGridLayout();self.base_grid.setSpacing(2);palette.addLayout(self.base_grid);self.base_buttons=[self.swatch(value) for value in BASES]
        for i,button in enumerate(self.base_buttons):self.base_grid.addWidget(button,i//6,i%6)
        self.custom_grid=QGridLayout();self.custom_grid.setSpacing(2);palette.addLayout(self.custom_grid)
        self.custom_buttons=[]
        for i in range(16):
            b=QPushButton();b.setFixedSize(24,24);b.setContextMenuPolicy(Qt.CustomContextMenu);b.clicked.connect(lambda checked=False,n=i:self.custom(n));b.customContextMenuRequested.connect(lambda pos,n=i:self.custom_menu(n));self.custom_grid.addWidget(b,i//6,i%6);self.custom_buttons.append(b)
        row=QHBoxLayout();palette.addLayout(row)
        picker=QPushButton('+');picker.setFixedWidth(28);picker.setToolTip('Full RGBA picker. Custom colors below are saved by Studio.');picker.clicked.connect(self.pick);row.addWidget(picker)
        save=QPushButton('Add custom');save.clicked.connect(self.add_custom);row.addWidget(save)
        self.preview=QLabel('Hover sample: —');self.preview.setWordWrap(True);body.addWidget(self.preview)
        self.scope=QComboBox();self.scope.addItems(['Selected layer','Visible Composite']);self.scope.currentIndexChanged.connect(lambda i:setattr(e,'sample_scope','Visible Composite' if i else 'Active Layer'));body.addWidget(self.scope)
        body=outer
        self.size_row=QWidget();sizes=QHBoxLayout(self.size_row);sizes.setContentsMargins(0,0,0,0);body.addWidget(self.size_row)
        self.size=CompactSpin();self.size.setRange(1,512);self.size.setDecimals(10);self.size.setSuffix(' px');self.size.valueChanged.connect(lambda v:e.tool_value(e.brush_tool(),'size',v));sizes.addWidget(self.size)
        add=QPushButton('+');add.setMaximumWidth(25);add.setToolTip('Save current size; three shared session presets');add.clicked.connect(self.add_size);sizes.addWidget(add)
        self.presets=QWidget();self.presets_layout=QGridLayout(self.presets);self.presets_layout.setContentsMargins(0,0,0,0);body.addWidget(self.presets)
        self.builtin_widget=QWidget();builtin=QGridLayout(self.builtin_widget);self.builtin_buttons=[];builtin.setContentsMargins(0,0,0,0);body.addWidget(self.builtin_widget)
        for i,(label,z,h) in enumerate((('Fine',4,1.),('Soft',12,.2),('Broad',48,.8))):
            b=QPushButton(label);b.clicked.connect(lambda checked=False,s=z,v=h:e.apply_brush_preset(e.brush_tool(),s,v));builtin.addWidget(b,i//3,i%3);self.builtin_buttons.append(b)
        self.opacity_widget=QWidget();row=QHBoxLayout(self.opacity_widget);row.setContentsMargins(0,0,0,0);row.addWidget(QLabel('Opacity'));self.opacity=CompactSpin();self.opacity.setRange(0,100);self.opacity.setDecimals(10);self.opacity.setSuffix(' %');self.opacity.valueChanged.connect(lambda v:e.tool_value(e.brush_tool(),'opacity',v/100));row.addWidget(self.opacity);body.addWidget(self.opacity_widget)
        self.opacity_row=row
        self.fields={'size':self.size,'opacity':self.opacity};self.field_rows={}
        for key,label in (('hardness','Hardness'),('flow','Flow'),('strength','Strength')):
            widget=QWidget();row=QHBoxLayout(widget);row.setContentsMargins(0,0,0,0);row.addWidget(QLabel(label));box=CompactSpin();box.setRange(0,100);box.setDecimals(10);box.setSuffix(' %');row.addWidget(box);body.addWidget(widget)
            box.valueChanged.connect(lambda v,k=key:e.tool_value(e.brush_tool(),k,v/100));self.fields[key]=box;self.field_rows[key]=widget
        self.footprint=QComboBox();self.footprint.addItems(['Round','Square']);self.footprint.currentTextChanged.connect(lambda v:e.tool_value(e.brush_tool(),'shape',v));self.shape_widget=QWidget();row=QHBoxLayout(self.shape_widget);row.setContentsMargins(0,0,0,0);row.addWidget(QLabel('Footprint'));row.addWidget(self.footprint);body.addWidget(self.shape_widget)
        for box in self.fields.values():box.setMaximumWidth(132);box.setMinimumWidth(80)
        self.pickup_hint=QLabel('Smudge samples visible artwork automatically; only the selected raster changes.');self.pickup_hint.setWordWrap(True);body.addWidget(self.pickup_hint)
        self.fill_options=QWidget();form=QFormLayout(self.fill_options);self.tolerance=QSpinBox();self.tolerance.setRange(0,255);self.tolerance.setValue(32);form.addRow('Tolerance',self.tolerance)
        self.contiguous=QCheckBox('Contiguous (4 neighbors)');self.contiguous.setChecked(True);form.addRow(self.contiguous);hint=QLabel('Off: all matching colors. Fill uses Main with left click and Secondary with right click.');hint.setWordWrap(True);form.addRow(hint);body.addWidget(self.fill_options)
        body.addWidget(self.swatches)
        self.selection_host=QWidget();self.selection_layout=QVBoxLayout(self.selection_host);self.selection_layout.setContentsMargins(0,0,0,0);body.addWidget(self.selection_host)
        self.boundary_actions=QWidget();self.boundary_actions.hide();e.settings_mask_widgets={}
        body.addStretch(1);self.resize_grip=SidebarResizeGrip(self);body.addWidget(self.resize_grip,0,Qt.AlignRight);e.quick_colors=self;self.sync()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        columns=max(4,min(12,(self.width()-24)//28))
        if columns!=getattr(self,'swatch_columns',None):
            self.swatch_columns=columns
            for grid,buttons in ((self.base_grid,self.base_buttons),(self.custom_grid,self.custom_buttons)):
                for button in buttons:grid.removeWidget(button)
                for i,button in enumerate(buttons):grid.addWidget(button,i//columns,i%columns)

        columns=max(1,min(3,(self.width()-12)//100))
        for grid,buttons in ((self.builtin_widget.layout(),self.builtin_buttons),(self.presets_layout,[self.presets_layout.itemAt(i).widget() for i in range(self.presets_layout.count())])):
            signature=(columns,tuple(id(button) for button in buttons))
            if getattr(grid,'reflow_signature',None)==signature:continue
            grid.reflow_signature=signature
            for button in buttons:grid.removeWidget(button)
            for i,button in enumerate(buttons):grid.addWidget(button,i//columns,i%columns)
    def assign(self,key):self.assignment=key;self.sync()
    def current(self):return self.e.secondary_color if self.assignment=='secondary' else self.e.brush_color
    def set_color(self,color):
        if not color.isValid():return
        began=time.perf_counter()
        if self.assignment=='secondary':self.e.secondary_color=QColor(color)
        else:self.e.brush_color=color
        self.e.remember_tools();self.e.sync_tool_ui();self.e.status.setText(self.e.color_target+' '+self.assignment+' '+color.name(QColor.HexArgb))
        self.e.ui_timings.append(dict(event='color_assignment',tool=self.e.color_target,ms=(time.perf_counter()-began)*1000));self.e.ui_timings=self.e.ui_timings[-256:]
    def swatch(self,value):
        b=QPushButton();b.setFixedSize(24,24);b.setStyleSheet('background:'+value);b.setToolTip(value);b.clicked.connect(lambda checked=False:self.set_color(QColor(value)));return b
    def pick(self):
        began=time.perf_counter()
        d=QColorDialog(self.current(),self);d.setWindowTitle('RGBA picker • Studio custom swatches use Add custom');d.setOption(QColorDialog.ShowAlphaChannel);d.setOption(QColorDialog.DontUseNativeDialog)
        help=QLabel('Qt custom slots begin white: select a slot, choose a color, then Add to Custom Colors.\nFor persistent RGBA swatches, accept this picker and use Studio Add custom.',d);help.setWordWrap(True);d.layout().addWidget(help)
        self.e.ui_timings.append(dict(event='picker_construct',tool=self.e.color_target,ms=(time.perf_counter()-began)*1000));self.e.ui_timings=self.e.ui_timings[-256:]
        if d.exec():self.set_color(d.selectedColor())
    def custom(self,n):
        values=self.e.shell.preferences.get('media_custom_colors',[])
        if n<len(values):self.set_color(QColor(values[n]))
        else:self.e.status.setText('Empty custom slot '+str(n+1)+': choose a color, then Add custom. Empty slots do not assign white.')
    def add_custom(self):
        values=list(self.e.shell.preferences.get('media_custom_colors',[]));color=self.current().name(QColor.HexArgb)
        if color in values:self.e.status.setText('This RGBA color is already a custom swatch.');return
        if len(values)>=16:self.e.status.setText('16 custom colors full. Right-click a saved swatch to replace or remove.');return
        values.append(color);self.e.shell.preferences['media_custom_colors']=values;self.sync()
    def custom_menu(self,n):
        values=list(self.e.shell.preferences.get('media_custom_colors',[]))
        if n>=len(values):self.custom(n);return
        menu=QMenu(self);menu.addAction('Replace with active '+self.assignment,lambda:self.change_custom(n,False));menu.addAction('Remove custom swatch',lambda:self.change_custom(n,True));menu.exec(self.custom_buttons[n].mapToGlobal(self.custom_buttons[n].rect().center()))
    def change_custom(self,n,remove):
        values=list(self.e.shell.preferences.get('media_custom_colors',[]))
        if remove:values.pop(n)
        else:values[n]=self.current().name(QColor.HexArgb)
        self.e.shell.preferences['media_custom_colors']=values;self.sync()
    def add_size(self):
        sizes=list(self.e.config.get('editor',{}).get('custom_sizes',[]));v=self.e.brush['size']
        if v in sizes:self.e.status.setText('Size already saved in this session.');return
        if len(sizes)==3:self.e.status.setText('Three sizes full. Right-click a preset to remove or replace.');return
        self.change_sizes(sizes+[v])
    def change_sizes(self,sizes):
        if not self.e.resolve_pending():return
        before=deepcopy(self.e.config);self.e.config['editor']=dict(custom_sizes=sizes);self.e.commit('Session custom sizes',before);self.sync()
    def size_menu(self,n):
        sizes=list(self.e.config['editor']['custom_sizes']);menu=QMenu(self)
        def remove():self.change_sizes(sizes[:n]+sizes[n+1:])
        def replace():
            if self.e.brush['size'] in sizes and self.e.brush['size']!=sizes[n]:self.e.status.setText('Size already saved; duplicate not added.');return
            sizes[n]=self.e.brush['size'];self.change_sizes(sizes)
        menu.addAction('Replace with current size',replace);menu.addAction('Remove preset',remove);menu.exec(self.mapToGlobal(self.rect().center()))
    def preview_sample(self,color,message=''):
        self.hover_color=color;self.preview.setText('Hover sample: '+(color.name(QColor.HexArgb) if color is not None and color.alpha() else message or 'transparent / unavailable')+'\nLeft → shared Main • Right → shared Secondary')
    def sync(self):
        e=self.e;state=e.tool_states[e.color_target];fill=bool(e.canvas and e.canvas.tool=='Fill');self.receiver.setText('Shared Main / Secondary RGBA • Brush / Pencil / Fill'+(' • Sampler receiver' if e.canvas and e.canvas.tool=='Sampler' else ''))
        for key,b in self.chips.items():
            color=e.brush_color if key=='main' else e.secondary_color;b.setChecked(key==self.assignment);b.setText((('Main' if key=='main' else 'Secondary') if fill else ('Main / Left' if key=='main' else 'Secondary / Right'))+' '+color.name(QColor.HexArgb));b.setStyleSheet('background:'+color.name()+';color:'+('#000000' if color.lightness()>127 else '#ffffff'))
        values=e.shell.preferences.get('media_custom_colors',[])
        for i,b in enumerate(self.custom_buttons):b.setText('' if i<len(values) else '·');b.setStyleSheet('background:'+QColor(values[i]).name() if i<len(values) else '');b.setToolTip('Custom '+str(i+1)+': '+(values[i] if i<len(values) else 'empty; Add custom'))
        tool=e.canvas.tool if e.canvas else 'Select';changed=tool!=self.active_tool;self.active_tool=tool;painting=tool in ('Brush','Pencil','Eraser','Smudge');self.title.setText(('Select' if tool in ('Selection','Wand') else tool)+' settings')
        self.color_block.setVisible(tool in ('Brush','Pencil','Sampler','Fill'));self.swatches.setVisible(tool in ('Brush','Pencil','Sampler','Fill'));self.size_row.setVisible(painting);self.presets.setVisible(painting);self.builtin_widget.setVisible(tool in ('Brush','Pencil','Eraser'));self.opacity_widget.setVisible(painting);self.shape_widget.setVisible(painting)
        state=e.tool_states[e.brush_tool()];e.settings_widgets={e.brush_tool():dict(self.fields,shape=self.footprint)} if painting else {}
        for key,box in self.fields.items():
            value=state['brush'][key]*(1 if key=='size' else 100)
            if changed or not box.hasFocus() and not box.lineEdit().hasFocus():
                if box.value()!=value:box.blockSignals(True);box.setValue(value);box.blockSignals(False)
        if self.footprint.currentText()!=state['brush']['shape']:self.footprint.blockSignals(True);self.footprint.setCurrentText(state['brush']['shape']);self.footprint.blockSignals(False)
        for key,widget in self.field_rows.items():widget.setVisible(tool=='Smudge' if key=='strength' else tool in ('Brush','Eraser') if key=='hardness' else tool in ('Brush','Pencil','Eraser'))
        self.pickup_hint.setVisible(tool=='Smudge')
        self.fill_options.setVisible(tool=='Fill');self.selection_host.setVisible(tool in ('Select','Selection','Wand','Crop'));self.boundary_actions.hide()
        sizes=tuple(e.config.get('editor',{}).get('custom_sizes',[]))
        if sizes!=getattr(self,'size_key',None):
            self.size_key=sizes
            while self.presets_layout.count():
                retired=self.presets_layout.takeAt(0).widget();retired.hide();retired.deleteLater()
            for i,v in enumerate(sizes):
                b=QPushButton(format(v,'.10g')+' px');b.setToolTip(repr(v)+' native pixels');b.clicked.connect(lambda checked=False,z=v:e.tool_value(e.brush_tool(),'size',z));b.setContextMenuPolicy(Qt.CustomContextMenu);b.customContextMenuRequested.connect(lambda pos,n=i:self.size_menu(n));self.presets_layout.addWidget(b,i//3,i%3)
        self.scope.setVisible(bool(e.canvas and e.canvas.tool=='Sampler'));self.preview.setVisible(bool(e.canvas and e.canvas.tool=='Sampler'))

class SidebarResizeGrip(QLabel):
    def __init__(self,panel):
        super().__init__('◢',panel);self.panel=panel;self.setCursor(Qt.SizeFDiagCursor);self.setToolTip('Drag to resize the tool sidebar width; floating sidebar height also resizes.');self.setAccessibleName('Resize tool sidebar');self.setFixedSize(24,20);self.start=None
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:self.start=(event.globalPosition(),self.panel.e.tool_scroll.size())
    def mouseMoveEvent(self,event):
        if not self.start:return
        pos,size=self.start;delta=event.globalPosition()-pos;e=self.panel.e;scroll=e.tool_scroll
        scroll.setFixedWidth(max(224,min(760,round(size.width()+delta.x()))))
        if e.color_toolbar.isWindow():scroll.setFixedHeight(max(120,min(1200,round(size.height()+delta.y()))));e.color_toolbar.adjustSize()
    def mouseReleaseEvent(self,event):
        self.start=None;e=self.panel.e;e.shell.preferences['media_tool_sidebar_width']=e.tool_scroll.width()
        if e.color_toolbar.isWindow():e.shell.preferences['media_tool_sidebar_float_height']=e.tool_scroll.height()

class ToolScroll(QScrollArea):
    def __init__(self,editor,bar):
        super().__init__();self.host=editor;self.bar=bar;self.setMinimumHeight(80)
    def sizeHint(self):
        hint=super().sizeHint()
        if self.bar.orientation()==Qt.Vertical and not self.bar.isWindow():hint.setHeight(max(160,self.host.height()-self.host.toolbar.height()-12))
        return hint

def attach(editor,e):
    bar=QToolBar('Tool settings and colors',editor);bar.setObjectName('composition_colors');bar.setMovable(True);bar.setFloatable(True);bar.setAllowedAreas(Qt.AllToolBarAreas);bar.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
    panel=QuickColors(e);scroll=ToolScroll(editor,bar);scroll.setWidgetResizable(True);scroll.setWidget(panel);scroll.setMinimumWidth(224);scroll.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding);bar.addWidget(scroll);e.tool_scroll=scroll;editor.addToolBar(Qt.LeftToolBarArea,bar);e.color_toolbar=bar
    width=e.shell.preferences.get('media_tool_sidebar_width')
    if isinstance(width,int) and 224<=width<=760:scroll.setFixedWidth(width)
    def floating(value):
        if not value:scroll.setMinimumHeight(80);scroll.setMaximumHeight(16777215)
        else:
            height=e.shell.preferences.get('media_tool_sidebar_float_height',420)
            if isinstance(height,int) and 120<=height<=1200:scroll.setFixedHeight(height)
    bar.topLevelChanged.connect(floating);bar.hide()

def sample(canvas,pos,commit=False,secondary=False):
    e=canvas.editor;row=e.selected_row()
    if e.sample_scope=='Visible Composite':color=canvas.sample_composite(pos)
    elif row and row['type'] in ('Image','Artwork','Paint') and row['source_visible']:
        image=canvas.source_image(row);color=None
        if image is not None:
            uv=canvas.mask_point(row,pos,clamp=False);x,y=math.floor(uv[0]*image.width()),math.floor(uv[1]*image.height())
            if 0<=x<image.width() and 0<=y<image.height():
                from raster_edit import coverage
                color=image.pixelColor(x,y);alpha=coverage((x,y,1,1),(image.width(),image.height()),row).pixelColor(0,0).alpha()
                color.setAlpha(round(color.alpha()*alpha/255*row['opacity']))
    else:color=None
    if hasattr(e,'quick_colors'):e.quick_colors.preview_sample(color,'outside / no readable selected pixel')
    if commit:e.receive_sample(color,secondary=secondary)
    return color

def pixel_frame(canvas,row,image):
    c=row['crop'];flip=np.diag([-1. if row['flip_x'] else 1.,-1. if row['flip_y'] else 1.,1.])
    uv=np.array([[1/(c[2]-c[0]),0.,-c[0]/(c[2]-c[0])-.5],[0.,1/(c[3]-c[1]),-c[1]/(c[3]-c[1])-.5],[0.,0.,1.]])
    return canvas.source_matrix(row)@flip@uv@np.diag([1/image.width(),1/image.height(),1.])

def pin_pickup(canvas,stroke):
    from composition import effective,is_branch
    e=canvas.editor;images={};frames={};scene=deepcopy(e.config)
    for row in scene['layers']:
        if row['type']=='Group' or not effective(scene,row,'enabled') or not row['source_visible']:continue
        image=canvas.source_image(row)
        if image is None:raise ValueError('Visible '+row['name']+' has no readable frame. Snapshot unsupported sources or hide them before Smudge.')
        # Native views share immutable tiles; QImage implicit sharing pins decoded
        # GIF/Video/Sprite frames without a whole-frame pixel copy.
        images[row['id']]=image.private_view() if hasattr(image,'private_view') else QImage(image)
        frames[row['id']]=pixel_frame(canvas,row,image)
    from cpu_projection import artwork_sampling_plan
    stroke['pickup']=dict(scene=scene,images=images,frames=frames,plan=artwork_sampling_plan(scene),target_frame=pixel_frame(canvas,stroke['target'],stroke['image']),session=stroke['session'],revision=stroke['revision'])

def pickup_tile(stroke,start,r):
    pickup=stroke.get('pickup')
    if not pickup:return None
    from cpu_projection import render_artwork_region
    sx,sy=start;origin=np.array([[1.,0.,sx-r],[0.,1.,sy-r],[0.,0.,1.]])
    projection=np.linalg.inv(pickup['target_frame']@origin)
    return render_artwork_region(pickup['scene'],pickup['images'],pickup['frames'],projection,2*r,2*r,stroke['row'],stroke['preview'],plan=pickup['plan'])
