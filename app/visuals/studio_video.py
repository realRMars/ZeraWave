"""Selected Video transport; bounded live intent and the existing shared sidebar."""
import time,math
from collections import deque
from copy import deepcopy
from PySide6.QtCore import Qt,QTimer,QPoint,QSignalBlocker
from PySide6.QtWidgets import QWidget,QToolBar,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QPushButton,QSlider,QDoubleSpinBox,QGroupBox,QStackedWidget,QSizePolicy,QStyle,QMessageBox
from composition import effective,validate_scene

CYCLE=(1.,2.,4.,6.,8.)
class SeekSlider(QSlider):
    def __init__(self,host):
        super().__init__(Qt.Horizontal);self.host=host;self.setRange(0,10000);self.setMinimumHeight(24);self.setMinimumWidth(90);self.setAccessibleName('Video seek: wheel one second; Ctrl wheel one source frame')
        self.setToolTip('Drag previews while paused; release resumes previous playback only after the final frame is published. Wheel: 1 s; Ctrl+wheel: one actual source frame per notch.')
        self.sliderPressed.connect(host.begin_scrub);self.valueChanged.connect(host.scrub_changed);self.sliderReleased.connect(host.end_scrub)
    def value_at(self,event):return round(max(0.,min(1.,(event.position().x()-8)/max(1,self.width()-16)))*10000)
    def mousePressEvent(self,event):
        if event.button()!=Qt.LeftButton:return super().mousePressEvent(event)
        self.setFocus();self.setSliderDown(True);self.setValue(self.value_at(event));event.accept()
    def mouseMoveEvent(self,event):
        if self.isSliderDown():self.setValue(self.value_at(event));event.accept()
        else:super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self.isSliderDown() and event.button()==Qt.LeftButton:self.setValue(self.value_at(event));self.setSliderDown(False);event.accept()
        else:super().mouseReleaseEvent(event)
    def wheelEvent(self,event):
        if not self.isEnabled():return super().wheelEvent(event)
        n=event.angleDelta().y()/120;self.host.wheel_remainder+=n;count=math.trunc(self.host.wheel_remainder);self.host.wheel_remainder-=count
        if event.modifiers()&Qt.ControlModifier:
            for _ in range(min(abs(count),64)):self.host.step(1 if count>0 else -1)
        elif count:self.host.coarse_seek(count)
        event.accept()

class VideoSpin(QDoubleSpinBox):
    def __init__(self,callback,step):
        super().__init__();self.commit=callback;self.setDecimals(3);self.setSingleStep(step);self.setKeyboardTracking(False);self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(250);self.timer.timeout.connect(callback);self.editingFinished.connect(self.finish)
    def finish(self):self.timer.stop();self.commit()
    def wheelEvent(self,event):
        amount=event.angleDelta().y()/120
        if amount:self.setValue(self.value()+amount*(.001 if event.modifiers()&Qt.ControlModifier else self.singleStep()));self.timer.start()
        event.accept()

class VideoControls(QWidget):
    def __init__(self,e):
        super().__init__();self.e=e;self.binding=None;self.pending=None;self.future=None;self.scrub=None;self.settings=False;self.syncing=False;self.wheel_remainder=0.;self.frames=deque(maxlen=60);self.output_frames=deque(maxlen=60);self.last_sample=None;self.last_output=None;self.last_display=None;self.coarse_intent=None
        box=QVBoxLayout(self);box.setContentsMargins(4,2,4,2);box.setSpacing(2)
        self.info=QLabel();self.info.setTextInteractionFlags(Qt.TextSelectableByMouse);self.info.setWordWrap(True);self.info.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);box.addWidget(self.info)
        row=QHBoxLayout();box.addLayout(row);self.buttons={}
        for key,text,tip,callback,icon in (
            ('play','', 'Play selected video',lambda:self.action('play'),QStyle.SP_MediaPlay),('pause','', 'Pause; cancel remembered scrub resume',lambda:self.action('pause'),QStyle.SP_MediaPause),('stop','', 'Stop at In; cancel seek resume',lambda:self.action('stop'),QStyle.SP_MediaStop),
            ('previous','', 'Previous actual source frame; pause until Play',lambda:self.step(-1),QStyle.SP_MediaSkipBackward),('next','', 'Next actual source frame; pause until Play',lambda:self.step(1),QStyle.SP_MediaSkipForward),
            ('reverse','◀◀ 1×','Reverse cycle 1→2→4→6→8→1; changing direction begins at 1× from current position',lambda:self.cycle(-1),None),('forward','▶▶ 1×','Forward cycle 1→2→4→6→8→1; changing direction begins at 1× from current position',lambda:self.cycle(1),None),
            ('range','In / Out','Edit In/Out in the shared sidebar',lambda:self.show_settings('Range'),None),('loop','Loop','Toggle Loop (restart at opposite endpoint)',lambda:self.toggle_loop('Loop'),None),('ping','↔ Ping-pong','Toggle Ping-pong (reflect at endpoints)',lambda:self.toggle_loop('Ping-pong'),None),('rate','Rate','Exact rate/presets and direction in the shared sidebar',lambda:self.show_settings('Rate'),None)):
            b=QPushButton(text);b.setToolTip(tip);b.setAccessibleName(tip);b.setCheckable(key in ('play','pause','reverse','forward','loop','ping'));b.clicked.connect(callback)
            if icon:b.setIcon(self.style().standardIcon(icon));b.setFixedWidth(30)
            else:b.setMaximumWidth(104)
            row.addWidget(b);self.buttons[key]=b
        self.seek=SeekSlider(self);row.addWidget(self.seek,1)
        self.panel=QWidget();self.panel.e=e;layout=QVBoxLayout(self.panel);layout.setContentsMargins(4,4,4,4);self.title=QLabel('Video settings');layout.addWidget(self.title);self.groups={}
        rate=QGroupBox('Rate and direction');form=QFormLayout(rate);layout.addWidget(rate);self.groups['Rate']=rate
        presets=QWidget();pl=QHBoxLayout(presets);pl.setContentsMargins(0,0,0,0)
        for n in (*CYCLE,12.):
            b=QPushButton(f'{n:g}×');b.setMaximumWidth(38);b.clicked.connect(lambda checked=False,v=n:self.edit({'rate':v},'Video rate'));pl.addWidget(b)
        form.addRow(presets);self.rate=VideoSpin(lambda:self.edit({'rate':self.rate.value()},'Video rate'),.1);self.rate.setRange(.1,12.);form.addRow('Exact magnitude ×',self.rate)
        dirs=QWidget();dl=QHBoxLayout(dirs);dl.setContentsMargins(0,0,0,0);self.directions={}
        for n,label in ((1,'▶ Forward'),(-1,'◀ Reverse')):
            b=QPushButton(label);b.setCheckable(True);b.clicked.connect(lambda checked=False,v=n:self.edit({'direction':v},'Video direction'));dl.addWidget(b);self.directions[n]=b
        form.addRow(dirs)
        ranges=QGroupBox('In / Out (source seconds)');form=QFormLayout(ranges);layout.addWidget(ranges);self.groups['Range']=ranges
        self.in_point=VideoSpin(lambda:self.edit({'start':self.in_point.value()},'Video In'),.01);self.out_point=VideoSpin(lambda:self.edit({'end':self.out_point.value()},'Video Out'),.01)
        for label,w in (('In s',self.in_point),('Out s',self.out_point)):w.setRange(0,86400);form.addRow(label,w)
        auto=QPushButton('Out: automatic source end');auto.clicked.connect(lambda:self.edit({'end':None},'Video automatic Out'));form.addRow(auto);self.auto=QLabel();form.addRow(self.auto)
        loops=QGroupBox('Boundary behavior');l=QHBoxLayout(loops);layout.addWidget(loops);self.groups['Loop']=loops;self.loop_presets={}
        for mode in ('None','Loop','Ping-pong'):
            b=QPushButton(mode);b.setCheckable(True);b.clicked.connect(lambda checked=False,v=mode:self.edit({'loop':v},'Video loop'));l.addWidget(b);self.loop_presets[mode]=b
        hint=QLabel('In < Out within the source. Range wheel: 0.01 s, Ctrl: 0.001 s. Rate remains a positive magnitude up to 12×. Video is silent; audio transport is independent.');hint.setWordWrap(True);layout.addWidget(hint)
        layout.addStretch();from editor_colors import SidebarResizeGrip
        layout.addWidget(SidebarResizeGrip(self.panel),0,Qt.AlignRight)
        scroll=e.tool_scroll;colors=scroll.takeWidget();stack=QStackedWidget();stack.addWidget(colors);stack.addWidget(self.panel);scroll.setWidget(stack);self.stack=stack;self.colors=colors
        self.timer=QTimer(self);self.timer.setInterval(40);self.timer.timeout.connect(self.flush);self.timer.start()
    def selected(self):
        row=self.e.selected_row();return row if row and row['type']=='Video' else None
    def state(self):return self.e.shell.client.snapshot.get('media_frames',{}).get(self.e.selected,{})
    def source_duration(self):return float(self.e.metadata(self.selected()).get('duration',0.)) if self.selected() else 0.
    def packet(self,op,value=None):
        if not self.selected():return None
        state=self.state();return dict(layer=self.e.selected,op=op,value=value,media_session=self.e.binding[0],source=state.get('source'))
    def queue(self,op,value=None):
        packet=self.packet(op,value)
        if packet is None:return
        if op=='step' and self.pending and self.pending['op']=='step' and self.pending['layer']==packet['layer']:
            self.pending['value']+=value
            if abs(self.pending['value'])>64:self.pending['value']-=value;self.e.status.setText('Frame navigation busy; wait for the pending frame.')
            return
        self.pending=packet
    def flush(self):
        if self.future:
            if not self.future.done():return
            future=self.future;self.future=None
            try:future.result()
            except Exception as exc:
                packet=self.submitted
                if self.binding==(packet['media_session'],packet['layer'],packet['source']) and self.pending is None:
                    self.e.status.setText('Video action failed: '+str(exc));self.scrub=None
        if self.pending:
            packet=self.pending;self.pending=None
            snapshot=self.e.shell.client.snapshot;state=snapshot.get('media_frames',{}).get(packet['layer'])
            if snapshot.get('media_control',{}).get('session')!=packet['media_session'] or state is None or packet['source'] is not None and state.get('source')!=packet['source']:return
            if packet['op']=='step' and packet['value']!=0:
                # Submit one batched bounded count, preserving each notch.
                count=packet['value'];packet['value']={'count':count}
            elif packet['op']=='step':return
            self.submitted=packet;self.future=self.e.shell.client.edits.submit(self.e.shell.client.request,'media_transport',**packet)
    def cancel_intent(self):
        self.scrub=None;self.coarse_intent=None;self.pending=None
        if self.binding:
            session,identity,source=self.binding
            self.pending=dict(layer=identity,media_session=session,source=source,op='cancel_resume',value=None)
    def action(self,op):
        self.scrub=None;self.coarse_intent=None;self.queue(op)
    def begin_scrub(self):
        if not self.selected():return
        self.scrub=dict(binding=self.binding,resume=bool(self.state().get('playing')))
        self.coarse_intent=None;self.queue('scrub',dict(position=self.seek.value()/10000*self.source_duration(),final=False,resume=False))
    def scrub_changed(self,value):
        if self.syncing or not self.scrub or self.scrub['binding']!=self.binding:return
        self.queue('scrub',dict(position=value/10000*self.source_duration(),final=False,resume=False))
    def end_scrub(self):
        if self.scrub and self.scrub['binding']==self.binding:
            self.queue('scrub',dict(position=self.seek.value()/10000*self.source_duration(),final=True,resume=self.scrub['resume']))
        self.scrub=None
    def coarse_seek(self,count):
        state=self.state();duration=self.source_duration();target=(self.coarse_intent if self.coarse_intent is not None else state.get('position',0.))+count
        self.coarse_intent=max(0.,min(duration,target));self.scrub=None
        self.queue('scrub',dict(position=self.coarse_intent,final=True,resume=bool(state.get('playing'))))
    def step(self,direction):
        self.scrub=None;self.coarse_intent=None;self.queue('step',direction)
    def edit(self,updates,label):
        if self.syncing:return
        row=self.selected()
        if not row or effective(self.e.config,row,'locked'):return
        self.action('cancel_resume')
        if not self.e.resolve_pending():return
        before=deepcopy(self.e.config);row=self.selected();settings=dict(row['media'],**updates);duration=self.source_duration();end=settings['end'] if settings['end'] is not None else duration
        if not 0<=settings['start']<end<=duration:
            self.e.status.setText('In must precede Out within source duration; last valid range retained.');self.sync(True);return
        row['media']=settings
        try:validate_scene(self.e.config)
        except ValueError as exc:self.e.config=before;self.e.status.setText(str(exc));self.sync();return
        if before!=self.e.config:self.e.commit(label,before)
        self.sync()
    def cycle(self,direction):
        row=self.selected()
        if not row:return
        current=row['media'];rate=current['rate'];value=CYCLE[(CYCLE.index(rate)+1)%len(CYCLE)] if current.get('direction',1)==direction and rate in CYCLE else 1.
        self.edit(dict(direction=direction,rate=value),'Video direction / rate');self.show_settings('Rate')
    def toggle_loop(self,mode):
        row=self.selected()
        if row:self.edit({'loop':'None' if row['media']['loop']==mode else mode},'Video loop');self.show_settings('Loop')
    def show_settings(self,section):
        if not self.selected():return
        self.settings=True;self.stack.setCurrentWidget(self.panel);self.title.setText(self.selected()['name']+' • '+section)
        for key,group in self.groups.items():group.setVisible(key==section)
        self.e.color_toolbar.show();self.e.tool_scroll.setFocus(Qt.OtherFocusReason);self.sync()
    def drawing_settings(self):self.settings=False;self.stack.setCurrentWidget(self.colors)
    @staticmethod
    def measured(samples):
        if len(samples)<2:return 'unavailable'
        elapsed=samples[-1][0]-samples[0][0]
        return f'{elapsed/(len(samples)-1)*1000:.0f} ms / {(len(samples)-1)/elapsed:.1f} updates/s' if elapsed>0 else 'unavailable'
    def sync(self,reset_values=False):
        row=self.selected();state=self.state();binding=(self.e.binding[0],row['id'],state.get('source')) if row and self.e.binding else None
        if binding!=self.binding:
            self.cancel_intent();self.binding=binding;self.drawing_settings();self.frames.clear();self.output_frames.clear();self.last_sample=self.last_output=None;self.last_display=None
            for box in (self.rate,self.in_point,self.out_point):box.timer.stop()
            reset_values=True
        self.setVisible(row is not None);self.bar.setVisible(row is not None)
        if not row:return
        if self.settings:self.e.color_toolbar.show()
        settings=row['media'];duration=self.source_duration();self.syncing=True
        try:
            displayed=self.e.media_stats.get('presented',{}).get(row['id']) if getattr(self.e,'media_stats',None) else None
            if displayed and displayed['generation']==state.get('generation'):
                key=(displayed['generation'],displayed['sequence'])
                if key!=self.last_sample:self.last_sample=key;self.frames.append((displayed['consumed_at'],displayed['pts']));self.last_display=displayed['pts']
            else:self.last_display=None
            output=self.e.shell.client.snapshot.get('preview',{}).get('image_layers',{}).get('animated_presented',{}).get(row['id'])
            if output and output['generation']==state.get('generation'):
                key=(output['generation'],output['sequence'])
                if key!=self.last_output:self.last_output=key;self.output_frames.append((output['uploaded_at'],output['pts']))
            position=self.last_display;requested=(self.pending or {}).get('value');requested=requested.get('position',state.get('position',0.)) if isinstance(requested,dict) else state.get('position',0.)
            pending=bool(self.scrub or self.pending or state.get('seek_pending') or state.get('held') or position is None or abs((position or 0)-float(requested or 0))>.1)
            meta=self.e.metadata(row);fps=meta.get('fps');source_fps=f'{fps:.2f} avg/nominal source fps' if fps else 'source fps unavailable'
            shown='unavailable' if position is None else f'{position:.3f} s';intent=f' • seeking/requested {float(requested or 0):.3f} s (pending)' if pending else ''
            now=time.perf_counter();editor_rate=self.measured(self.frames) if self.frames and now-self.frames[-1][0]<1 and state.get('playing') else 'unavailable';output_rate=self.measured(self.output_frames) if self.output_frames and now-self.output_frames[-1][0]<1 and state.get('playing') else 'unavailable'
            self.info.setText(f"{row['name']} • source {duration:.3f} s • shown {shown}{intent} • {state.get('state','waiting')} • {source_fps} • editor {editor_rate} • output {output_rate}")
            self.info.setToolTip('Measured distinct frame consumption/upload updates; Qt paint, swap and physical scanout are separate. Output is unavailable unless renderer telemetry is present. '+(state.get('error') or ''))
            if not self.seek.isSliderDown():self.seek.setValue(round((float(requested or 0) if pending else position or 0)/max(.001,duration)*10000))
            for key in ('play','pause'):self.buttons[key].setChecked(bool(state.get('playing'))==(key=='play'))
            for direction,key in ((1,'forward'),(-1,'reverse')):
                self.buttons[key].setChecked(settings.get('direction',1)==direction);self.buttons[key].setText(('▶▶' if direction>0 else '◀◀')+f" {settings['rate']:g}×");self.directions[direction].setChecked(settings.get('direction',1)==direction)
            for key,mode in (('loop','Loop'),('ping','Ping-pong')):self.buttons[key].setChecked(settings['loop']==mode)
            for mode,b in self.loop_presets.items():b.setChecked(settings['loop']==mode)
            for box,value in ((self.rate,settings['rate']),(self.in_point,settings['start']),(self.out_point,settings['end'] if settings['end'] is not None else duration)):
                if reset_values or not box.hasFocus() and not box.lineEdit().hasFocus() and not box.timer.isActive():box.setValue(value)
                box.setEnabled(not effective(self.e.config,row,'locked'))
            self.auto.setText(f"Automatic source end: {duration:.3f} s" if settings['end'] is None else f"Active range {settings['start']:.3f}–{settings['end']:.3f} s; total source {duration:.3f} s")
        finally:self.syncing=False
    def save_video(self):
        self.e.status.setText('Video Save is OPEN: no product video writer. Current-frame image and File session Save remain separate. See B3 finishing export proposal.')
        QMessageBox.information(self,'Video Save — pending scope approval','No product video writer exists in this candidate. Video Save is OPEN pending the scoped export proposal. Imported originals are protected. Use the explicitly labeled current-frame image action for a still, or File → Save session for editable settings.')
    def close(self):self.timer.stop();self.pending=None;self.scrub=None

def attach(editor,e):
    e.video=VideoControls(e);bar=QToolBar('Selected video',editor);bar.setObjectName('composition_video');bar.setMovable(False);bar.setAllowedAreas(Qt.BottomToolBarArea);bar.addWidget(e.video);editor.addToolBar(Qt.BottomToolBarArea,bar);e.video.bar=bar;bar.hide()
