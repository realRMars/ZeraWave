"""Read-only Band Analyzer presentation over the shared audio owner's PCM FFT.

No audio stream, visual gain, FFT, or engine tuning lives in this widget.
"""
from collections import deque
from bisect import bisect_right
import math,time
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QColor,QPainter,QPen,QPainterPath,QLinearGradient,QImage,QBrush
from PySide6.QtWidgets import QWidget,QVBoxLayout,QGridLayout,QLabel,QComboBox,QSlider,QSpinBox,QPushButton,QMenu,QDialog,QDialogButtonBox,QLineEdit,QColorDialog,QHBoxLayout

LIMITS={31:992,63:945}
MODES=('Bars','Spectrum','Line','Spectrogram')
TICKS=(20,50,100,200,500,1000,2000,5000,10000,20000)
PALETTES={
    'Studio Cyan':('#084c6c','#50d4de','#edbb91'),
    'Galaxy Ember':('#0e4b7f','#c87f52','#ffe7c4'),
    'Aurora':('#18244b','#46d5ac','#c8f2a1'),
    'Violet Pulse':('#28134d','#ab71e6','#ffb2d2'),
}
DEFAULTS=dict(level=0,range=60,smooth=60,history=10)


def valid_colors(values):
    return isinstance(values,(list,tuple)) and len(values)==3 and all(isinstance(v,str) and len(v)==7 and v.startswith('#') and QColor(v).isValid() for v in values)


class GradientEditor(QDialog):
    """Local three-stop editor; Cancel never changes the view."""
    def __init__(self,colors,parent=None):
        super().__init__(parent);self.setWindowTitle('Band Analyzer gradient');self.edits=[];self.swatches=[]
        layout=QVBoxLayout(self);layout.addWidget(QLabel('Low → Mid → High • analyzer display only'))
        for role,color in zip(('Low','Mid','High'),colors):
            row=QHBoxLayout();row.addWidget(QLabel(role));button=QPushButton('Choose…');edit=QLineEdit(color);edit.setMaxLength(7)
            edit.setAccessibleName(role+' analyzer color hex');self.edits.append(edit);self.swatches.append(button)
            button.clicked.connect(lambda checked=False,e=edit:self.pick(e));edit.textChanged.connect(self.preview)
            row.addWidget(button);row.addWidget(edit);layout.addLayout(row)
        self.gradient=QLabel();self.gradient.setMinimumHeight(32);layout.addWidget(self.gradient)
        self.buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);self.buttons.accepted.connect(self.accept);self.buttons.rejected.connect(self.reject);layout.addWidget(self.buttons);self.preview()
    def colors(self):return tuple(edit.text().lower() for edit in self.edits)
    def pick(self,edit):
        color=QColorDialog.getColor(QColor(edit.text()),self,'Analyzer color',QColorDialog.DontUseNativeDialog)
        if color.isValid():edit.setText(color.name())
    def preview(self):
        if not hasattr(self,'buttons'):return
        colors=self.colors();self.buttons.button(QDialogButtonBox.Ok).setEnabled(valid_colors(colors))
        for edit,button in zip(self.edits,self.swatches):
            color=QColor(edit.text());button.setStyleSheet('background:'+color.name()+';color:'+('#10171c' if color.lightness()>140 else '#f0e5db')+';' if color.isValid() else '')
        if valid_colors(colors):self.gradient.setStyleSheet(f'background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {colors[0]},stop:0.65 {colors[1]},stop:1 {colors[2]});border-radius:5px;')


def db(power):return 10*math.log10(max(power,1e-24))
def hz(value):return f'{value/1000:g}k' if value>=1000 else f'{value:g}'


def display_values(group,columns):
    """Reduce power when combining groups; interpolate dB when adding columns.

    Finer columns are presentation only. Coarse boundaries assume uniform power
    per log interval within each measured group, without claiming a new FFT.
    """
    powers=group['power'];count=len(powers)
    if columns==count:return [db(p) for p in powers]
    if columns<count:
        edges=[math.log(f/20)/math.log(1000) for f in group['edges']];values=[]
        for i in range(columns):
            low,high=i/columns,(i+1)/columns
            values.append(db(sum(p*max(0,min(high,b)-max(low,a))/(b-a)
                for p,a,b in zip(powers,edges,edges[1:]))))
        return values
    centers=[math.log(f/20)/math.log(1000) for f in group['centers']];levels=[db(p) for p in powers];values=[]
    for i in range(columns):
        x=(i+.5)/columns;j=bisect_right(centers,x)
        if j==0:values.append(levels[0])
        elif j==count:values.append(levels[-1])
        else:
            fraction=(x-centers[j-1])/(centers[j]-centers[j-1])
            values.append(levels[j-1]+fraction*(levels[j]-levels[j-1]))
    return values


class AnalyzerPlot(QWidget):
    def __init__(self):
        super().__init__();self.setMinimumSize(280,145);self.setMouseTracking(True)
        self.mode='Bars';self.groups=31;self.columns=31;self.offset=0;self.range=60;self.smoothing=60;self.seconds=10;self.colors=PALETTES['Studio Cyan']
        self.packet=None;self.identity=None;self.generation=None;self.values=[];self.smoothed=[]
        self.history=deque(maxlen=1024);self.rows={};self.status='No current source PCM';self.last_stamp=None;self.current=False
        self.path_key=None;self.path=None;self.fill_path=None;self.bar_rects=[]
        self.history_key=None;self.history_image=None
        self.setAccessibleName('Band Analyzer frequency display')
    def clear(self):
        self.packet=None;self.identity=None;self.values=[];self.smoothed=[];self.history.clear();self.rows.clear();self.last_stamp=None;self.path_key=None;self.history_key=None
    def accept(self,hub):
        previous=(self.identity,self.status,self.current)
        packet=hub.get('band_analyzer');generation=hub.get('generation')
        if generation!=self.generation:
            if not (packet and packet.get('held') and hub.get('status')=='Paused'):self.clear()
            self.generation=generation
        error=hub.get('analyzer_error')
        if not packet:
            self.current=False
            if hub.get('status') not in ('Paused','Ended'):self.clear()
            self.status='Spectrum unavailable: '+error if error else hub.get('status','Stopped')+' • no current spectrum'
            if previous!=(self.identity,self.status,self.current):self.update()
            return
        try:
            for n in (31,63):
                group=packet['groups'][str(n)]
                if len(group['power'])!=n or len(group['edges'])!=n+1 or len(group['centers'])!=n:raise ValueError('Invalid band counts')
                if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in group['power']):raise ValueError('Invalid band power')
            if packet['generation']!=generation:raise ValueError('Stale source identity')
        except (KeyError,TypeError,ValueError):
            self.clear();self.current=False;self.status='Spectrum unavailable • invalid snapshot';self.update();return
        self.packet=packet;identity=(packet.get('origin_generation',generation),packet['sequence'])
        self.current=not packet.get('held',False) and time.perf_counter()-packet['stamp']<=1.5 and hub.get('playing',False)
        self.status='Live source PCM' if self.current else 'Paused • last spectrum' if hub.get('status')=='Paused' else 'Ended • last spectrum' if hub.get('status')=='Ended' else 'Stale spectrum'
        if identity!=self.identity:
            self.identity=identity
            self.history.append((packet['stamp'],{k:list(v['power']) for k,v in packet['groups'].items()}))
            self.recompute(True)
        if previous!=(self.identity,self.status,self.current):self.update()
    def recompute(self,new_sample=False):
        if not self.packet:return
        group=self.packet['groups'][str(self.groups)];self.values=display_values(group,self.columns)
        stamp=self.packet['stamp'];dt=max(0.,stamp-(self.last_stamp if self.last_stamp is not None else stamp))
        if not new_sample or len(self.smoothed)!=len(self.values) or not self.smoothing:self.smoothed=list(self.values)
        else:
            alpha=-math.expm1(-dt/(self.smoothing/1000.))
            self.smoothed=[a+(b-a)*alpha for a,b in zip(self.smoothed,self.values)]
        self.last_stamp=stamp
    def configure(self,**values):
        changed={key for key,value in values.items() if getattr(self,key)!=value}
        if not changed:return
        for key,value in values.items():setattr(self,key,value)
        if changed & {'groups','columns','offset','range','colors'}:self.rows.clear();self.history_key=None
        if changed & {'groups','columns','smoothing'}:self.recompute()
        self.path_key=None;self.update()
    def rect_plot(self):return QRectF(43,24,max(1,self.width()-55),max(1,self.height()-52))
    def normalized(self,value):return max(0.,min(1.,(value+self.offset+self.range)/self.range))
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#0b141a'));rect=self.rect_plot()
        p.setPen(QColor('#20333e'))
        for fraction in (0.,.25,.5,.75,1.):
            y=rect.bottom()-fraction*rect.height();p.drawLine(QPointF(rect.left(),y),QPointF(rect.right(),y))
            p.setPen(QColor('#829ba9'))
            value=-self.range*(1-fraction)-self.offset
            label=f'{value if value else 0:g}' if self.mode!='Spectrogram' else f'{self.seconds*fraction:g}s'
            p.drawText(QRectF(0,y-8,37,17),Qt.AlignRight|Qt.AlignVCenter,label);p.setPen(QColor('#20333e'))
        last=-100.
        for frequency in TICKS:
            x=rect.left()+math.log(frequency/20)/math.log(1000)*rect.width()
            if x-last<36 and frequency!=20000:continue
            p.setPen(QColor('#20333e'));p.drawLine(QPointF(x,rect.top()),QPointF(x,rect.bottom()))
            p.setPen(QColor('#91a8b4'));p.drawText(QRectF(x-21,rect.bottom()+3,42,18),Qt.AlignCenter,hz(frequency));last=x
        p.drawText(QRectF(self.width()-44,self.height()-16,40,15),Qt.AlignRight,'Hz')
        if self.mode=='Spectrogram':
            gradient=QLinearGradient(rect.left(),0,rect.left()+80,0)
            for stop,color in zip((0.,.65,1.),self.colors):gradient.setColorAt(stop,QColor(color))
            p.fillRect(QRectF(rect.left(),3,80,5),gradient)
            p.drawText(QRectF(rect.left()+84,0,rect.width()-84,18),Qt.AlignRight|Qt.AlignVCenter,f'{-self.range-self.offset:g} → {-self.offset if self.offset else 0:g} dBFS')
        else:p.drawText(QRectF(0,0,40,18),Qt.AlignRight|Qt.AlignVCenter,'dBFS')
        if not self.packet or not self.smoothed:
            p.drawText(rect,Qt.AlignCenter,self.status);return
        if self.mode=='Spectrogram':self.paint_history(p,rect)
        else:
            # Bound drawing to pixels, retaining peaks when many columns share
            # a pixel. Density never creates thousands of Qt child widgets.
            key=(self.identity,self.width(),self.height(),self.mode,self.columns,self.groups,self.offset,self.range,self.smoothing)
            if self.path_key!=key:
                count=min(len(self.smoothed),max(1,min(1200,int(rect.width()))));levels=[-240.]*count
                for i,value in enumerate(self.smoothed):
                    j=min(count-1,i*count//len(self.smoothed));levels[j]=max(levels[j],value)
                path=QPainterPath()
                self.bar_rects=[]
                for i,value in enumerate(levels):
                    x=rect.left()+(i+.5)*rect.width()/count;y=rect.bottom()-self.normalized(value)*rect.height()
                    if self.mode=='Bars':
                        width=rect.width()/count
                        self.bar_rects.append(QRectF(x-width*.43,y,width*.86,rect.bottom()-y))
                    else:
                        if i==0:path.moveTo(x,y)
                        else:path.lineTo(x,y)
                self.path=path;self.fill_path=QPainterPath(path)
                if self.mode=='Spectrum':self.fill_path.lineTo(rect.right(),rect.bottom());self.fill_path.lineTo(rect.left(),rect.bottom());self.fill_path.closeSubpath()
                self.path_key=key
            gradient=QLinearGradient(0,rect.bottom(),0,rect.top())
            for stop,color in zip((0.,.65,1.),self.colors):gradient.setColorAt(stop,QColor(color))
            if self.mode=='Bars':
                brush=QBrush(gradient)
                for bar in self.bar_rects:p.fillRect(bar,brush)
            if self.mode=='Spectrum':
                p.fillPath(self.fill_path,gradient)
            if self.mode!='Bars':p.setRenderHint(QPainter.Antialiasing);p.setPen(QPen(QColor(self.colors[1]),1.6));p.drawPath(self.path)
        if not self.current:
            p.fillRect(rect,QColor(11,20,26,115));p.setPen(QColor('#e5b789'));p.drawText(rect,Qt.AlignCenter,self.status)
    def paint_history(self,p,rect):
        # Batch recolor only missing rows, including a full-history slider edit.
        # PCM powers remain untouched; the output is a bounded raster cache.
        import numpy as np
        stamp=self.packet['stamp'];geometry=self.packet['groups'][str(self.groups)]
        visible=[(wall,powers) for wall,powers in self.history if stamp-wall<=self.seconds]
        if not visible:return
        # Project time onto physical screen rows before expanding frequency
        # columns. Retain the full bounded history for changing the time span.
        height=max(1,math.ceil(rect.height()*self.devicePixelRatioF()))
        period=min(.2,self.packet.get('frames',2048)/self.packet.get('samplerate',48000))
        walls=np.asarray([wall for wall,powers in visible]);times=stamp-self.seconds*(1-(np.arange(height)+.5)/height)
        index=np.searchsorted(walls,times,side='left');safe=np.minimum(index,len(walls)-1)
        # Hold a display snapshot between normal updates (including a skipped
        # telemetry packet), rather than inventing a time gap at every poll.
        # Longer interruptions remain transparent; this is a diagnostic history.
        intervals=np.r_[period,np.diff(walls)]
        spans=np.where(intervals<=.25,np.maximum(period,intervals),period)
        valid=(index<len(walls))&(walls[safe]-times<=spans[safe])
        selected=np.unique(safe[valid])
        missing=[visible[i] for i in selected if visible[i][0] not in self.rows]
        if missing:
            energy=np.asarray([powers[str(self.groups)] for wall,powers in missing])
            if self.columns<self.groups:
                edges=np.log(np.asarray(geometry['edges'])/20)/np.log(1000)
                low=np.arange(self.columns)[:,None]/self.columns;high=low+1/self.columns
                weights=np.maximum(0,np.minimum(high,edges[1:])-np.maximum(low,edges[:-1]))/np.diff(edges)
                energy=np.einsum('ij,kj->ik',energy,weights,optimize=False)
            levels=10*np.log10(np.maximum(energy,1e-24))
            if self.columns>self.groups:
                centers=np.log(np.asarray(geometry['centers'])/20)/np.log(1000);positions=(np.arange(self.columns)+.5)/self.columns
                right=np.clip(np.searchsorted(centers,positions),1,self.groups-1);left=right-1
                fraction=np.clip((positions-centers[left])/(centers[right]-centers[left]),0,1)
                levels=levels[:,left]*(1-fraction)+levels[:,right]*fraction
            v=np.arange(256)/255;stops=(0.,.65,1.)
            rgb=np.asarray([QColor(color).getRgb()[:3] for color in self.colors])
            palette=np.column_stack([np.interp(v,stops,rgb[:,index]) for index in (2,1,0)]+[np.full(256,255)]).astype(np.uint8)
            indices=np.clip((levels+self.offset+self.range)*255/self.range,0,255).astype(np.uint8);pixels=palette[indices]
            for i,(wall,powers) in enumerate(missing):self.rows[wall]=pixels[i]
        key=(stamp,height,self.seconds,self.columns,self.groups,self.offset,self.range,self.colors)
        if missing or key!=self.history_key:
            # One raster blit, with transparency for interrupted display updates.
            pixels=np.zeros((height,self.columns,4),dtype=np.uint8)
            if len(selected):
                colors=np.asarray([self.rows[walls[i]] for i in selected])
                pixels[valid]=colors[np.searchsorted(selected,safe[valid])]
            self.history_image=QImage(pixels.tobytes(),self.columns,height,self.columns*4,QImage.Format_ARGB32).copy();self.history_key=key
        p.drawImage(rect,self.history_image)
        active={wall for wall,powers in visible};self.rows={wall:image for wall,image in self.rows.items() if wall in active}
    def mouseMoveEvent(self,event):
        if not self.packet:return
        rect=self.rect_plot();fraction=max(0,min(.999999,(event.position().x()-rect.left())/rect.width()));group=self.packet['groups'][str(self.groups)]
        index=min(self.groups-1,bisect_right(group['edges'],20*1000**fraction)-1);index=max(0,index)
        note=' • under-resolved by FFT' if group['unresolved'][index] else ''
        resolution=(group.get('resolution_hz') or [self.packet['resolution_hz']]*self.groups)[index]
        self.setToolTip(f"Band estimate {hz(group['edges'][index])}–{hz(group['edges'][index+1])} Hz: {db(group['power'][index]):.1f} dBFS RMS{note}\nFFT spacing {resolution:.1f} Hz; longer window for bass/narrow groups. Source PCM before output volume/mute; display changes do not affect audio or visuals.")


class BandAnalyzer(QWidget):
    def __init__(self):
        super().__init__();layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(5);self.slider_rows={}
        grid=QGridLayout();grid.setHorizontalSpacing(6);grid.setVerticalSpacing(3);layout.addLayout(grid)
        self.mode=QComboBox();self.mode.addItems(MODES);self.mode.setAccessibleName('Band Analyzer display')
        self.groups=QComboBox();self.groups.addItems(['31 • third-octave style','63 • logarithmic']);self.groups.setAccessibleName('Measured frequency groups')
        grid.addWidget(QLabel('View'),0,0);grid.addWidget(self.mode,0,1,1,2);grid.addWidget(self.groups,0,3,1,3)
        self.detail=QSlider(Qt.Horizontal);self.detail.setRange(3,992);self.detail.setValue(31)
        self.count=QSpinBox();self.count.setRange(3,992);self.count.setValue(31);self.count.setKeyboardTracking(False)
        grid.addWidget(QLabel('Columns'),1,0);grid.addWidget(self.detail,1,1,1,4);grid.addWidget(self.count,1,5)
        self.detail.valueChanged.connect(self.count.setValue);self.count.valueChanged.connect(self.detail.setValue)
        self.level=self.slider(grid,2,0,'Level',-24,24,0,'dB')
        self.span=self.slider(grid,2,3,'Range',20,120,60,'dB')
        self.smooth=self.slider(grid,3,0,'Smooth',0,1500,DEFAULTS['smooth'],'ms')
        self.history=self.slider(grid,3,3,'History',2,30,10,'s')
        self.palette=QComboBox();self.palette.addItems(list(PALETTES)+['Custom']);self.palette.setAccessibleName('Analyzer color palette');self.custom_colors=PALETTES['Studio Cyan'];self.last_palette='Studio Cyan'
        self.edit_colors=QPushButton('Edit gradient…');self.edit_colors.clicked.connect(self.customize_colors)
        self.reset_button=QPushButton('Reset sliders');self.reset_button.clicked.connect(self.reset_sliders);self.reset_button.setToolTip('Reset Columns, Level, Range, Smooth and History. Keeps display mode, grouping, colors and audio source.')
        grid.addWidget(QLabel('Colors'),4,0);grid.addWidget(self.palette,4,1,1,2);grid.addWidget(self.edit_colors,4,3,1,2);grid.addWidget(self.reset_button,4,5)
        self.plot=AnalyzerPlot();layout.addWidget(self.plot,1);self.info=QLabel();self.info.setWordWrap(True);layout.addWidget(self.info)
        self.groups.setToolTip('31 third-octave-style or 63 log bands, 20–20,000 Hz. Fractional FFT-bin energy removes empty-bin gaps; narrow bands remain estimates, not certified acoustic/SPL measurements.')
        self.detail.setToolTip('3–992 columns with 31 groups, or 3–945 with 63. Extra columns interpolate measured groups; they add no frequency resolution.')
        self.count.setToolTip(self.detail.toolTip())
        self.level.setToolTip('Display offset only. Does not change PCM, playback volume, analyzer data, visual tuning or engine input.')
        self.span.setToolTip('Visible dBFS range below the display ceiling. Higher values reveal quieter detail.')
        self.smooth.setToolTip('Bars, Spectrum and Line display smoothing in milliseconds. Spectrogram shows the recorded unsmoothed snapshots.')
        self.history.setToolTip('Spectrogram history in seconds; bounded to 1024 snapshots. Normally about 23 snapshots/s, depending on PCM cadence. This is not an audio-rate spectrogram.')
        self.palette.setToolTip('Local analyzer pigments only. Presets or a custom Low/Mid/High gradient; does not change scene palettes.')
        for widget in (self.detail,self.count):self.install_reset(widget,'columns')
        self.mode.currentTextChanged.connect(self.settings);self.groups.currentIndexChanged.connect(self.group_changed)
        for slider in (self.detail,self.level,self.span,self.smooth,self.history):slider.valueChanged.connect(self.settings)
        self.palette.currentTextChanged.connect(self.palette_changed)
        self.settings()
    def slider(self,grid,row,column,label,low,high,value,suffix):
        slider=QSlider(Qt.Horizontal);slider.setRange(low,high);slider.setValue(value);slider.setAccessibleName('Band Analyzer '+label)
        text=QLabel(f'{value} {suffix}');text.setMinimumWidth(44);slider.valueChanged.connect(lambda v:text.setText(f'{v} {suffix}'))
        caption=QLabel(label);grid.addWidget(caption,row,column);grid.addWidget(slider,row,column+1);grid.addWidget(text,row,column+2)
        key={'Level':'level','Range':'range','Smooth':'smooth','History':'history'}[label]
        self.slider_rows[key]=(caption,slider,text);self.install_reset(slider,key);return slider
    def install_reset(self,widget,key):
        widget.setProperty('analyzer_setting',key);widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(lambda pos,w=widget:self.reset_menu(w).exec(w.mapToGlobal(pos)))
    def default_value(self,key):return (31 if self.groups.currentIndex()==0 else 63) if key=='columns' else DEFAULTS[key]
    def reset_menu(self,widget):
        key=widget.property('analyzer_setting');menu=QMenu(widget);value=self.default_value(key)
        menu.addAction(f'Reset to default ({value})',lambda:widget.setValue(value));return menu
    def reset_sliders(self):
        for key,widget in (('columns',self.count),('level',self.level),('range',self.span),('smooth',self.smooth),('history',self.history)):
            widget.blockSignals(True);widget.setValue(self.default_value(key));widget.blockSignals(False)
            if key in self.slider_rows:self.slider_rows[key][2].setText(f"{self.default_value(key)} "+{'level':'dB','range':'dB','smooth':'ms','history':'s'}[key])
        self.detail.blockSignals(True);self.detail.setValue(self.count.value());self.detail.blockSignals(False);self.settings()
    def palette_changed(self,name):
        if name=='Custom':
            if self.last_palette!='Custom':self.customize_colors()
        else:self.last_palette=name;self.settings()
    def customize_colors(self):
        colors=self.custom_colors if self.last_palette=='Custom' else PALETTES[self.last_palette]
        dialog=GradientEditor(colors,self)
        if dialog.exec()==QDialog.Accepted:
            self.custom_colors=dialog.colors();self.last_palette='Custom';self.palette.blockSignals(True);self.palette.setCurrentText('Custom');self.palette.blockSignals(False)
        else:
            self.palette.blockSignals(True);self.palette.setCurrentText(self.last_palette);self.palette.blockSignals(False)
        self.settings()
    def group_changed(self):
        old=31 if self.plot.groups==31 else 63;size=31 if self.groups.currentIndex()==0 else 63
        value=self.count.value();value=size if value==old else min(value,LIMITS[size])
        self.detail.blockSignals(True);self.count.blockSignals(True)
        self.detail.setMaximum(LIMITS[size]);self.count.setMaximum(LIMITS[size]);self.detail.setValue(value);self.count.setValue(value)
        self.detail.blockSignals(False);self.count.blockSignals(False);self.settings()
    def settings(self,*args):
        mode=self.mode.currentText();self.history.setEnabled(mode=='Spectrogram');self.smooth.setEnabled(mode!='Spectrogram')
        for key,applies in (('history',mode=='Spectrogram'),('smooth',mode!='Spectrogram')):
            for widget in self.slider_rows[key]:widget.setVisible(applies)
        colors=self.custom_colors if self.last_palette=='Custom' else PALETTES[self.last_palette]
        self.plot.configure(mode=mode,groups=31 if self.groups.currentIndex()==0 else 63,columns=self.count.value(),offset=self.level.value(),range=self.span.value(),smoothing=self.smooth.value(),seconds=self.history.value(),colors=colors)
        self.describe()
    def configuration(self):
        return dict(mode=self.mode.currentText(),groups=31 if self.groups.currentIndex()==0 else 63,columns=self.count.value(),
            level=self.level.value(),range=self.span.value(),smooth=self.smooth.value(),history=self.history.value(),palette=self.last_palette,custom_colors=list(self.custom_colors))
    def restore_configuration(self,values):
        if not isinstance(values,dict):return
        if values.get('mode') in MODES:self.mode.setCurrentText(values['mode'])
        if values.get('groups') in (31,63):self.groups.setCurrentIndex(int(values['groups']==63))
        if valid_colors(values.get('custom_colors')):self.custom_colors=tuple(v.lower() for v in values['custom_colors'])
        name=values.get('palette')
        if name in PALETTES or name=='Custom':
            self.last_palette=name;self.palette.blockSignals(True);self.palette.setCurrentText(name);self.palette.blockSignals(False)
        for key,widget in (('columns',self.count),('level',self.level),('range',self.span),('smooth',self.smooth),('history',self.history)):
            if type(values.get(key)) is int:widget.setValue(max(widget.minimum(),min(widget.maximum(),values[key])))
        self.settings()
    def refresh(self,hub):self.plot.accept(hub);self.describe()
    def describe(self):
        plot=self.plot;resolution=f" • FFT bass {plot.packet.get('low_resolution_hz',plot.packet['resolution_hz']):.1f} / upper {plot.packet['resolution_hz']:.1f} Hz" if plot.packet else ''
        density='interpolated' if plot.columns>plot.groups else 'combined' if plot.columns<plot.groups else 'measured groups'
        text=f'{plot.status} • 20 Hz–20,000 Hz • {plot.groups} groups / {plot.columns} columns ({density}){resolution}'
        if text!=self.info.text():self.info.setText(text)
        self.info.setToolTip('Source RMS dBFS before output volume/mute and visual gain. Bass/narrow groups use up to 171 ms of PCM; broad upper groups use 43 ms. Fractional-bin energy estimates avoid artificial empty groups; narrow bands are not independently resolved. Normal PCM cadence is about 23 snapshots/s, capped at 33; more columns add no FFT resolution. Colors and sliders affect only this display.')
