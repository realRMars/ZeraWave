"""Local, target-pinned color selection in the existing authoring editor."""
from copy import deepcopy
import time,math
from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QSpinBox,QCheckBox,QToolBar
from PySide6.QtGui import QImage
from pixel_selection import encode,decode,select

class SelectionControls(QWidget):
    def __init__(self,e):
        super().__init__();self.e=e;self.job=None;self.ticket=None;self.seed=None;self.baseline=None;self.generation=0;self.request=None
        body=QVBoxLayout(self);body.setContentsMargins(4,4,4,4);self.setMinimumWidth(190)
        self.hint=QLabel();self.hint.setWordWrap(True);body.addWidget(self.hint)
        row=QHBoxLayout();body.addLayout(row);self.tolerance_label=QLabel('Tolerance 0–255');row.addWidget(self.tolerance_label);self.tolerance=QSpinBox();self.tolerance.setRange(0,255);self.tolerance.setValue(32);row.addWidget(self.tolerance)
        self.contiguous=QCheckBox('Contiguous: connected neighbors only');self.contiguous.setChecked(True);body.addWidget(self.contiguous)
        self.combine=QComboBox();self.combine.addItems(['New','Add','Subtract']);body.addWidget(self.combine)
        row=QHBoxLayout();body.addLayout(row)
        self.expand=QSpinBox();self.expand.setRange(-8,8);self.expand.setPrefix('Edge ');self.expand.setSuffix(' px');self.expand.setToolTip('Negative contracts; positive expands.');row.addWidget(self.expand)
        self.feather=QSpinBox();self.feather.setRange(0,8);self.feather.setPrefix('Feather ');self.feather.setSuffix(' px');row.addWidget(self.feather)
        for field in (self.tolerance,self.expand,self.feather):field.valueChanged.connect(self.adjust)
        self.contiguous.toggled.connect(self.adjust)
        self.feedback=QLabel('Full resolution • one pending calculation');self.feedback.setWordWrap(True);body.addWidget(self.feedback)
        self.actions=[]
        for label,cb in (('Copy pixels  Ctrl+C',e.copy_layer),('Cut pixels  Ctrl+X',e.cut_clipboard),('Paste pixels  Ctrl+V',e.paste_layer),('Delete pixels',lambda:e.pixel_editor.delete()),('Deselect  Ctrl+D',e.canvas.discard)):
            button=QPushButton(label);button.clicked.connect(cb);body.addWidget(button);self.actions.append(button)
        self.crop_apply=QPushButton('Apply crop');self.crop_apply.clicked.connect(e.canvas.apply);body.addWidget(self.crop_apply)
        self.crop_cancel=QPushButton('Cancel crop');self.crop_cancel.clicked.connect(e.canvas.discard);body.addWidget(self.crop_cancel)
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.poll);self.timer.start()
    def choose(self,value):
        self.e.choose_selection('Wand' if value=='Magic Wand' else 'Lasso' if value=='Lasso' else 'Select')
    def click(self,pos):
        e=self.e;c=e.canvas;row=e.selected_row();image=c.source_image(row) if row else None
        if image is None or row['type'] not in ('Image','Artwork','Paint'):e.status.setText('Magic Wand needs readable selected-layer pixels.');return
        uv=c.mask_point(row,pos,clamp=False);seed=(math.floor(uv[0]*image.width()),math.floor(uv[1]*image.height()))
        if not 0<=seed[0]<image.width() or not 0<=seed[1]<image.height():e.status.setText('Click inside selected artwork.');return
        c.preview_begin();self.seed=seed;self.baseline=decode(tuple(c.pixel_op['size']),c.pixel_op['coverage']).copy() if getattr(c,'pixel_op',None) and self.combine.currentText()!='New' else None
        self.request=(e.binding,deepcopy(row),image,self.seed,self.baseline,self.combine.currentText());self.adjust()
    def adjust(self,*args):
        if not self.request:return
        self.generation+=1
        if self.job is None:self.launch()
    def launch(self):
        binding,row,image,seed,previous,mode=self.request;generation=self.generation
        args=(image,row,seed,self.tolerance.value(),self.contiguous.isChecked(),previous,mode,self.expand.value(),self.feather.value())
        self.ticket=(generation,binding,row);self.job=self.e.pool.submit(lambda:select(*args));self.feedback.setText('Calculating selected-layer coverage… artwork unchanged')
    def poll(self):
        if self.job is None or not self.job.done():return
        job,self.job=self.job,None;generation,binding,row=self.ticket;e=self.e;c=e.canvas
        if generation!=self.generation:
            if self.request:self.launch()
            return
        if e.binding!=binding or e.selected!=row['id'] or e.selected_row()!=row or c.tool!='Wand':self.feedback.setText('Obsolete selection ignored.');return
        try:
            a=job.result();op=encode(a)
            if not a.any():raise ValueError('Selection is empty; previous preview retained.')
            c.pixel_op=op;c.points=deepcopy(op['points']);c.handles=[];c.closed_path=True;c.selection_target=row['id'];c.pixel_overlay=None;e.pixel_editor.ready();c.update()
            self.feedback.setText(f'{int((a>0).sum())} selected native pixels • tolerance {self.tolerance.value()} • '+('connected' if self.contiguous.isChecked() else 'all matching colors'))
        except Exception as exc:self.feedback.setText(str(exc));e.status.setText(str(exc))
    def confirm(self):
        if self.e.canvas.tool=='Crop':self.e.canvas.apply()
        elif self.e.canvas.points:self.e.pixel_editor.ready()
    def sync(self):
        c=self.e.canvas;crop=c.tool=='Crop';wand=c.tool=='Wand'
        for field in (self.tolerance_label,self.tolerance,self.contiguous,self.combine,self.expand,self.feather):field.setVisible(wand)
        self.hint.setText('Drag retained area; Apply crop accepts, Cancel crop restores.' if crop else 'Complete a selection, then copy, cut, delete or drag its pixels. No confirmation step. T transforms a whole layer.')
        for button in self.actions:button.setVisible(not crop)
        self.crop_apply.setVisible(crop);self.crop_cancel.setVisible(crop);self.feedback.setVisible(wand)

    def commit_mask(self,mode):
        e=self.e;c=e.canvas;row=e.selected_row()
        if not row or not c.points or not e.editable_target(row):return
        before=deepcopy(e.config);op=c.operation();op['mode']=mode;row['masks'].append(op)
        if e.commit('Keep selected area visible' if mode=='Keep' else 'Remove selected own pixels',before):c.discard()
    def cancel(self):self.generation+=1;self.request=None;self.seed=None;self.baseline=None

def attach(editor,e):
    # Reuse the selection/refinement panel inside the same dockable tool sidebar.
    panel=SelectionControls(e);e.selection_controls=panel;e.quick_colors.selection_layout.addWidget(panel)
