"""Studio audio transport presentation; state and PCM remain in AudioOwner."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading,time,uuid,sys
from PySide6.QtCore import Qt,Signal,QRectF,QPointF,QTimer,QEvent
from PySide6.QtGui import QColor,QPainter,QPen,QPixmap,QIcon,QPolygonF
from PySide6.QtWidgets import QWidget,QLabel,QHBoxLayout,QVBoxLayout,QToolButton,QButtonGroup,QSizePolicy


def load_waveform(path,cancelled):
    # Keep decoder/numpy cold imports and all file reading off the Qt thread.
    audio_path=str(Path(__file__).resolve().parents[1]/'audio')
    if audio_path not in sys.path:sys.path.append(audio_path)
    from file_waveform import envelope
    return envelope(path,cancelled)


def clock_text(seconds):
    seconds=max(0,int(seconds or 0));hours,remaining=divmod(seconds,3600);minutes,seconds=divmod(remaining,60)
    return f'{hours}:{minutes:02}:{seconds:02}' if hours else f'{minutes:02}:{seconds:02}'


def transport_icon(kind):
    image=QPixmap(28,28);image.fill(Qt.transparent);p=QPainter(image);p.setRenderHint(QPainter.Antialiasing)
    color=QColor('#b9e9ee');p.setPen(QPen(color,1.8));p.setBrush(color)
    triangle=lambda points:p.drawPolygon(QPolygonF([QPointF(x,y) for x,y in points]))
    if kind=='play':triangle([(10,6),(23,14),(10,22)])
    elif kind=='pause':p.drawRoundedRect(QRectF(8,7,4,14),1,1);p.drawRoundedRect(QRectF(17,7,4,14),1,1)
    elif kind=='stop':p.drawRoundedRect(QRectF(8,8,13,13),2,2)
    elif kind in ('forward','reverse'):
        for x in (4,14):
            triangle([(x,7),(x+10,14),(x,21)] if kind=='forward' else [(28-x,7),(18-x,14),(28-x,21)])
    elif kind=='refresh':
        p.setBrush(Qt.NoBrush);p.drawArc(QRectF(6,6,16,16),35*16,290*16)
        p.setBrush(color);triangle([(22,5),(24,13),(17,11)])
    elif kind=='open':
        p.setBrush(Qt.NoBrush);p.drawRoundedRect(QRectF(4,10,20,13),2,2);p.drawLine(5,10,5,6);p.drawLine(5,6,12,6);p.drawLine(12,6,16,10)
    p.end();return QIcon(image)


def icon_button(kind,description,callback):
    button=QToolButton();button.setIcon(transport_icon(kind));button.setIconSize(image_size())
    button.setAccessibleName(description);button.setToolTip(description);button.clicked.connect(callback)
    button.setFixedSize(40,36);button.setStyleSheet('QToolButton{background:#14242c;border:1px solid #304a55;border-radius:8px;} QToolButton:hover{background:#21424b;border-color:#4ac5cf;} QToolButton:pressed,QToolButton[active="true"]{background:#514033;border-color:#c78c62;} QToolButton:disabled{background:#101b23;border-color:#26333c;}')
    return button


def image_size():
    from PySide6.QtCore import QSize
    return QSize(26,26)


class TwoWaySwitch(QWidget):
    """Two exclusive positions, with the function named outside the switch."""
    currentTextChanged=Signal(str)
    toggled=Signal(bool)
    def __init__(self,label,choices,callback=None):
        super().__init__();self.choices=tuple(choices);self.value=False
        layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(8)
        self.description=QLabel(label);self.description.setWordWrap(True);layout.addWidget(self.description,1)
        group_widget=QWidget();group=QHBoxLayout(group_widget);group.setContentsMargins(0,0,0,0);group.setSpacing(0)
        self.group=QButtonGroup(self);self.group.setExclusive(True);self.buttons=[]
        for i,name in enumerate(self.choices):
            button=QToolButton();button.setText(name);button.setCheckable(True);button.setMinimumHeight(30)
            button.setAccessibleName(label+': '+name);button.setToolTip(label+': '+name)
            side='top-left' if i==0 else 'top-right';bottom='bottom-left' if i==0 else 'bottom-right'
            button.setStyleSheet(f'QToolButton{{background:#14212a;border:1px solid #344a54;border-{side}-radius:6px;border-{bottom}-radius:6px;padding:4px 9px;}} QToolButton:checked{{background:#31515a;color:#d2f5f7;border-color:#4ac5cf;}} QToolButton:hover{{border-color:#87d5df;}} QToolButton:disabled{{color:#687c85;background:#14212a;border-color:#26333c;}}')
            self.group.addButton(button,i);group.addWidget(button);self.buttons.append(button)
        layout.addWidget(group_widget);self.group.idClicked.connect(self.choose)
        if callback:self.toggled.connect(callback)
        self.sync(False);self.setAccessibleName(label)
    def setToolTip(self,text):
        super().setToolTip(text)
        for button in self.buttons:button.setToolTip(text+"\n"+button.text())
    def choose(self,index):
        if bool(index)==self.value:return
        self.value=bool(index);self.currentTextChanged.emit(self.currentText());self.toggled.emit(self.value)
    def currentText(self):return self.choices[int(self.value)]
    def setCurrentText(self,text):
        if text in self.choices:self.sync(text==self.choices[1])
    def sync(self,value):self.value=bool(value);self.buttons[int(self.value)].setChecked(True)
    def isChecked(self):return self.value
    def click(self):self.buttons[int(not self.value)].click()


class Waveform(QWidget):
    seekRequested=Signal(float,int,str)
    def __init__(self):
        super().__init__();self.setMinimumSize(200,125);self.setMouseTracking(True)
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Song waveform');self.cancel=threading.Event()
        self.future=None;self.future_key=None;self.pending=None;self.key=None;self.peaks=[]
        self.duration=0.;self.position=0.;self.file=False;self.dragging=False;self.expected=None;self.revision=0
        self.caption='No current PCM waveform';self.error=None;self.last_sent=None
        layout=QVBoxLayout(self);layout.setContentsMargins(8,4,8,4);layout.setSpacing(0)
        row=QHBoxLayout();self.current=QLabel('00:00');self.total=QLabel('—');self.name=QLabel()
        self.name.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);self.name.setAlignment(Qt.AlignCenter)
        self.setAccessibleName('Session audio waveform and playhead')
        self.current.setAccessibleName('Current audio time');self.total.setAccessibleName('Total audio duration')
        self.current.setStyleSheet('color:#e9bc93;');row.addWidget(self.current);row.addWidget(self.name,1);row.addWidget(self.total)
        layout.addStretch(1);layout.addLayout(row)
        self.seek_timer=QTimer(self);self.seek_timer.setSingleShot(True);self.seek_timer.setInterval(150);self.seek_timer.timeout.connect(self.send_seek)
        self.setToolTip('Click or drag the full-song waveform to seek. File time follows the audio owner; it is not measured speaker latency. Current time is at left, total duration at right. Live capture has no seeking.')
    def refresh(self,hub):
        self.file=hub.get('mode')=='Audio File' and bool(hub.get('path')) and hub.get('duration') is not None
        key=(hub.get('file_revision',0),hub.get('path')) if self.file else None
        if key!=self.key:
            self.cancel.set();self.cancel=threading.Event();self.key=key;self.peaks=[];self.error=None
            self.dragging=False;self.expected=None;self.last_sent=None;self.seek_timer.stop();self.pending=(key,self.cancel) if key else None
        if self.future and self.future.done():
            try:
                result=self.future.result()
                if result and self.future_key==self.key:self.peaks=result['peaks']
            except Exception as exc:
                if self.future_key==self.key:self.error=str(exc)[:160]
            self.future=None
        if self.future is None and self.pending:
            key,cancel=self.pending;self.pending=None
            self.future_key=key;self.future=self.pool.submit(load_waveform,Path(key[1]),cancel)
        self.duration=hub.get('duration',0.) or 0. if self.file else 0.;self.revision=hub.get('file_revision',0)
        if self.expected and (hub.get('last_seek_id')==self.expected[0] or time.perf_counter()>self.expected[1]):self.expected=None
        if not self.dragging and self.expected is None:self.position=hub.get('playhead',0.)
        if self.file:
            self.caption='Waveform unavailable: '+self.error if self.error else 'Whole-song waveform' if self.peaks else 'Reading song waveform…'
            self.name.setText(Path(hub['path']).name);self.name.setToolTip(hub['path']);self.total.setText(clock_text(self.duration))
        else:
            self.peaks=hub.get('waveform',[]) if not hub.get('stale',True) else []
            self.caption='Captured PCM • recent snapshots' if self.peaks else 'No fresh captured PCM'
            self.name.setText('Live input');self.total.setText('—')
        self.current.setText(clock_text(self.position));self.setCursor(Qt.PointingHandCursor if self.file else Qt.ArrowCursor);self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#0b141a'));p.setPen(QColor('#8ea8b6'))
        p.drawText(8,18,self.caption);bottom=self.height()-30;center=(26+bottom)/2;amplitude=max(1,(bottom-26)/2)
        if self.file and self.duration:
            x=8+(self.width()-16)*max(0.,min(1.,self.position/self.duration))
            p.fillRect(QRectF(8,24,max(0,x-8),max(1,bottom-24)),QColor(43,126,142,35))
        p.setPen(QColor('#2a424b'));p.drawLine(8,int(center),self.width()-8,int(center))
        p.setPen(QColor('#4cbad0'))
        for i,(low,high) in enumerate(self.peaks):
            x=8+i*(self.width()-16)/max(1,len(self.peaks)-1)
            p.drawLine(QPointF(x,center-min(1.,high)*amplitude),QPointF(x,center-max(-1.,low)*amplitude))
        if self.file and self.duration:
            p.setPen(QPen(QColor('#f0b783'),2));p.drawLine(QPointF(x:=8+(self.width()-16)*max(0.,min(1.,self.position/self.duration)),24),QPointF(x,bottom))
            p.setBrush(QColor('#f0b783'));p.drawEllipse(QPointF(x,25),3,3)
    def pick(self,event):
        self.position=max(0.,min(1.,(event.position().x()-8)/max(1,self.width()-16)))*self.duration
        self.current.setText(clock_text(self.position));self.update()
    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton and self.file and self.duration and event.position().y()<self.height()-28:
            self.last_sent=None;self.dragging=True;self.pick(event);self.send_seek();event.accept()
        else:super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self.dragging:
            self.pick(event)
            if not self.seek_timer.isActive():self.seek_timer.start()
            event.accept()
        else:super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self.dragging and event.button()==Qt.LeftButton:
            self.pick(event);self.seek_timer.stop();self.send_seek();self.dragging=False;event.accept()
        else:super().mouseReleaseEvent(event)
    def send_seek(self):
        if not self.file or not self.key:return
        if self.last_sent and self.last_sent[0]==self.key and abs(self.last_sent[1]-self.position)<1e-6:return
        self.last_sent=(self.key,self.position)
        identity=uuid.uuid4().hex;self.expected=(identity,time.perf_counter()+2.,self.position)
        self.seekRequested.emit(self.position,self.revision,identity)
    def event(self,event):
        if event.type() in (QEvent.Hide,QEvent.WindowDeactivate) and hasattr(self,'seek_timer'):
            self.dragging=False;self.seek_timer.stop()
        return super().event(event)
    def close_pool(self):self.seek_timer.stop();self.cancel.set();self.pool.shutdown(wait=False,cancel_futures=True)
