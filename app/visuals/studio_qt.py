"""Bounded Qt ADS presentation proof over one retained Studio state owner.

The withdrawn Tk owner is a compatibility bridge, not a second editable UI.
Renderer resources remain exclusively in the existing preview child process.
"""
import base64
from collections import deque
import json
import os
from pathlib import Path
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
import threading

from PySide6.QtCore import Qt, QTimer, QByteArray, QEvent
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QAction, QActionGroup, QIcon, QWindow
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QComboBox, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QDoubleSpinBox, QDial, QSlider, QMenu, QFileDialog, QColorDialog,
    QPlainTextEdit, QGroupBox, QMessageBox, QSplitter, QGridLayout, QLineEdit, QMenuBar,QProgressBar,
    QDialog,QDialogButtonBox,QSpinBox,QFormLayout,QSizePolicy,QToolButton)
import PySide6QtAds as ads
from studio_control_client import ControlClient,OwnerView
ROOT=Path(__file__).resolve().parents[2]
STUDIO_TREES={}
SOURCES=()
from color_controls import targets_for, resolved_slots, rgb_hex
from window_host import NativeSurface, owned_process, dpi_awareness

STYLE = '''
QWidget { background:#10171c; color:#dce4e8; font:10pt "Segoe UI"; }
QMainWindow, ads--CDockManager { background:#080e12; }
QMenuBar { background:#0c1319; padding:5px; } QMenuBar::item { padding:6px 12px; }
QMenu::item:selected { background:#684932; }
QPushButton { background:#192329; border:1px solid #37444b; border-radius:5px; padding:6px 7px; }
QPushButton:hover { border-color:#ce966b; } QPushButton:focus { border:2px solid #52d3df; }
QPushButton:checked { background:#66452f; border-color:#d6a177; color:#ffe1bf; }
QPushButton:disabled { color:#69767c; border-color:#273238; }
QComboBox,QDoubleSpinBox { background:#0c141a; border:1px solid #39464e; border-radius:4px; padding:5px; }
QTreeWidget { background:#10171c; border:0; outline:0; }
QTreeWidget::item { padding:9px 3px; } QTreeWidget::item:selected { background:#513b2c; color:#efc29c; }
QLabel#brand { color:#e8b98f; font:bold 21pt "Segoe UI"; }
QLabel#muted { color:#8fa7b2; } QLabel#sceneTitle { color:#edc49f; font:600 12pt "Segoe UI"; }
QPushButton#accent { background:#362a22; border-color:#b78660; color:#f0c6a4; }
QPushButton#signal { background:#15343c; border-color:#51b8c8; color:#a1e3ec; } QGroupBox { border:1px solid #303d44; border-radius:5px; margin-top:15px; padding-top:12px; }
QGroupBox::title { color:#d9ab83; subcontrol-origin:margin; left:8px; }
QScrollArea { border:0; } QPlainTextEdit { background:#0b1218; border:0; font:9pt Consolas; }
QSlider::groove:horizontal { height:4px; background:#34454f; } QSlider::handle:horizontal { background:#8ecdd9; width:12px; margin:-5px 0; border-radius:6px; }
ads--CDockAreaWidget { background:#10171c; border:1px solid #2b383f; }
ads--CDockAreaTitleBar { background:#121b22; border-bottom:1px solid #2b383f; }
ads--CDockWidgetTab { background:#121b22; padding:6px; color:#a8bbc5; font:600 10pt "Segoe UI"; }
ads--CDockWidgetTab[activeTab="true"] { background:#2d2924; color:#edbd94; border-bottom:2px solid #c68c5d; }
ads--CDockSplitter::handle { background:#080e12; }
'''


from studio_audio_widgets import TwoWaySwitch,Waveform,icon_button
from studio_band_analyzer import BandAnalyzer

class Switch(TwoWaySwitch):
    def __init__(self,label,callback):super().__init__(label,('Off','On'),callback)


class Numeric(QWidget):
    """One destination-bound value; knob/slider preference is layout data only."""
    def __init__(self, shell, view, key, index):
        super().__init__();self.shell=shell;self.view=view;self.key=key
        self.binding=(view.owner_key(),view.target.target_id)
        self.destination=(shell.client.snapshot.get('preview_run'),shell.client.snapshot.get('destination_revision',0))
        low,high=view.bounds[key];self.low,self.high=low,high
        self.step=1. if key.endswith('_hz') else .01
        layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        title=view.focus_labels[index][0].get().lstrip('> ')
        label=QLabel(title);label.setWordWrap(True);label.setMinimumWidth(70);layout.addWidget(label,2)
        self.dial=QDial();self.dial.setRange(0,round((high-low)/self.step));self.dial.setNotchesVisible(True)
        self.dial.setFixedSize(34,34);self.slider=QSlider(Qt.Horizontal);self.slider.setRange(0,self.dial.maximum())
        self.spin=QDoubleSpinBox();self.spin.setRange(low,high);self.spin.setDecimals(1 if key.endswith('_hz') else 2)
        self.spin.setSingleStep(self.step);self.spin.setSuffix(' Hz' if key.endswith('_hz') else ' ×')
        self.spin.setKeyboardTracking(False);self.spin.setAccessibleName(title)
        self.spin.setFixedWidth(94);layout.setSpacing(6)
        layout.addWidget(self.dial);layout.addWidget(self.slider,2);layout.addWidget(self.spin)
        self.dial.valueChanged.connect(lambda v:self.set_value(low+v*self.step))
        self.slider.valueChanged.connect(lambda v:self.set_value(low+v*self.step))
        self.spin.valueChanged.connect(self.edit)
        self.sync();self.preference(shell.preferences.get(self.prefkey(),'knob'))
        self.setContextMenuPolicy(Qt.CustomContextMenu);self.customContextMenuRequested.connect(self.menu)
    def prefkey(self):return self.view.target.target_id+':'+self.key
    def preference(self,mode):
        self.dial.setVisible(mode=='knob');self.slider.setVisible(mode=='slider')
        self.shell.preferences[self.prefkey()]=mode
    def menu(self,pos):
        menu=QMenu(self);menu.addAction('Switch to knob',lambda:self.preference('knob'))
        menu.addAction('Switch to slider',lambda:self.preference('slider'))
        menu.addSeparator();menu.addAction('Reset to authored parameter',self.reset)
        menu.exec(self.mapToGlobal(pos))
    def reset(self):
        if self.key in self.view.authored:self.set_value(self.view.authored[self.key])
    def valid(self):return self.binding==(self.view.owner_key(),self.view.target.target_id) and self.destination==(self.shell.client.snapshot.get('preview_run'),self.shell.client.snapshot.get('destination_revision',0))
    def set_value(self,value):
        if self.valid():self.spin.setValue(value)
    def edit(self,value):
        if not self.valid():return
        self.shell.safe(lambda:self.shell.client.request('tune',key=self.key,value=value,binding=[list(self.binding[0]),self.binding[1]],preview_run=self.destination[0],destination_revision=self.destination[1]));self.sync()
    def sync(self):
        value=self.view.vars[self.key].get()
        for widget in (self.spin,self.dial,self.slider):widget.blockSignals(True)
        self.spin.setValue(value);tick=round((value-self.low)/self.step)
        self.dial.setValue(tick);self.slider.setValue(tick)
        for widget in (self.spin,self.dial,self.slider):widget.blockSignals(False)


class MappingMeters(QWidget):
    """Real CPU submission fields; gain is not inferred GPU output."""
    def __init__(self):
        super().__init__();self.setMinimumSize(300,190);self.packet={};self.scope='';self.current=False
    def set_packet(self,packet,scope,current):
        self.packet=packet;self.scope=scope;self.current=current;self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#0b1218'));p.setPen(QColor('#9bb2bc'))
        p.drawText(8,18,self.scope);p.drawText(8,36,'Raw RMS/peak | Gain ×1 (bypassed)' if self.packet.get('audio_bypassed') else 'Analyzed 0–1 | Applied CPU gain ×')
        if not self.current:p.drawText(8,59,'Unavailable / stale');return
        rows=list((self.packet.get('submissions') or {}).items())[:6]
        if not rows:p.drawText(8,59,self.packet.get('availability_note') or 'No submission for this target');return
        for i,(key,row) in enumerate(rows):
            y=54+i*25;source=row.get('source',key);value=row.get('input');gain=row.get('slot')
            p.setPen(QColor('#dce4e8'));p.drawText(8,y,str(source).title()[:16])
            if isinstance(value,(int,float)):
                x=92;w=max(25,self.width()-190);p.fillRect(x,y-10,w,8,QColor('#24323b'))
                p.fillRect(x,y-10,int(w*max(0,min(1,value))),8,QColor('#4dbbce'))
                p.drawText(x+w+5,y,f'{value:.2f}')
            p.setPen(QColor('#edbd94'));p.drawText(max(165,self.width()-55),y,f'{gain:.2f} ×' if isinstance(gain,(int,float)) else '—')


class Shell(QMainWindow):
    def __init__(self,layout_path=None,control_log_path=None,async_bootstrap=False):
        super().__init__();self.setWindowTitle('ZeraphinaX • ZeraWave Studio — Qt proof')
        self.setWindowFlags(self.windowFlags()|Qt.FramelessWindowHint|Qt.WindowSystemMenuHint|Qt.WindowMinMaxButtonsHint)
        self.resize(1600,980);self.setMinimumSize(900,600);self.setStyleSheet(STYLE)
        self.setMouseTracking(True)
        self.layout_path=Path(layout_path or ROOT/'work/studio/qt-layout.json')
        self.preferences={};self.panels={};self.surface=QWidget();self.surface.setAttribute(Qt.WA_NativeWindow)
        self.surface.setMinimumSize(360,230);self.surface.setStyleSheet('background:#080e12;')
        self.foreign=None;self.container=None;self.surface_layout=QVBoxLayout(self.surface);self.surface_layout.setContentsMargins(0,0,0,0)
        self.errors=deque(maxlen=30);self.samples=deque(maxlen=1200);self.closing=False;self.native=None
        self.operations=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Studio lifecycle')
        self.operation=None;self.pending_operation=None;self.cancel_attach=False;self.load_revision=0
        self.browsed=None;self.active_run=None;self.starting=False;self.resource_stamp=0.
        self.client=None;self.control_cancel=threading.Event()
        QApplication.instance().installEventFilter(self)
        self.async_bootstrap=async_bootstrap
        self.control_host={'ZERAWAVE_WORKSPACE_HOST':str(int(self.surface.winId())),
            'ZERAWAVE_WORKSPACE_PID':str(os.getpid()),'ZERAWAVE_WORKSPACE_QT_FOREIGN':'1','ZERAWAVE_OWNER_TELEMETRY':'1'}
        self.control_log_path=control_log_path
        if async_bootstrap:
            body,layout=self.body();self.boot_title=QLabel('Connecting to Studio control owner…');self.boot_title.setAlignment(Qt.AlignCenter);layout.addStretch();layout.addWidget(self.boot_title)
            busy=QProgressBar();busy.setRange(0,0);layout.addWidget(busy);layout.addStretch()
            self.boot_retry=self.button(layout,'Retry connection',self.connect_owner);self.boot_retry.hide()
            self.button(layout,'Cancel / Close Studio',self.close);self.setCentralWidget(body);self.menus();self.menu_bar.setEnabled(False)
            self.boot_timer=QTimer(self);self.boot_timer.timeout.connect(self.poll_connection);self.boot_timer.start(100);self.connect_owner()
            return
        self.client=ControlClient(self.control_host,log_path=control_log_path)
        self.finish_owner()
    def connect_owner(self):
        self.control_cancel.clear();self.boot_title.setText('Connecting to Studio control owner…');self.boot_retry.hide()
        self.connection=self.operations.submit(ControlClient,self.control_host,self.control_log_path,self.control_cancel)
        def discard_late(future):
            if self.closing:
                try:future.result().close(force=True)
                except Exception:pass
        self.connection.add_done_callback(discard_late)
    def poll_connection(self):
        if self.closing or self.connection is None or not self.connection.done():return
        future=self.connection;self.connection=None
        try:self.client=future.result()
        except Exception as exc:
            self.boot_title.setText(str(exc)+'\nSee work/studio/qt-startup.log');self.boot_retry.show();traceback.print_exception(exc);return
        self.boot_timer.stop();self.finish_owner()
    def finish_owner(self):
        self.owner=OwnerView(self.client);self.disconnect_reported=False;self.owner_error_seen=None
        global STUDIO_TREES,SOURCES
        STUDIO_TREES=self.client.snapshot['catalog'];SOURCES=self.client.snapshot['sources']
        self.view=self.owner.star_tuning_window
        self.browsed=(self.client.snapshot['selection_scope'],list(self.client.snapshot['selection']))
        self.form_names={row['id']:row['name'] for row in __import__('world_catalog').main_entries(__import__('renderer').LIVE_FORMS)}
        from world_catalog import LIVE_STATES
        def names(nodes):
            for node in nodes.values():
                if node.get('children'):names(node['children'])
                elif node.get('state') in LIVE_STATES:self.form_names.setdefault(LIVE_STATES[node['state']],node['label'])
        for tree in STUDIO_TREES.values():names(tree)
        ads.CDockManager.setConfigFlag(ads.CDockManager.OpaqueSplitterResize,True)
        ads.CDockManager.setConfigFlag(ads.CDockManager.DragPreviewIsDynamic,True)
        ads.CDockManager.setConfigFlag(ads.CDockManager.DragPreviewShowsContentPixmap,True)
        ads.CDockManager.setConfigFlag(ads.CDockManager.ActiveTabHasCloseButton,False)
        self.manager=ads.CDockManager(self);self.manager.setStyleSheet(STYLE)
        for overlay in (self.manager.containerOverlay(),self.manager.dockAreaOverlay()):
            overlay.setStyleSheet('background-color:rgba(50,195,218,70); border:2px solid #49d9ed;')
        self.setCentralWidget(self.manager)
        self.build();self.menus();self.balance();self.default=QByteArray(self.manager.saveState())
        self.restore();QTimer.singleShot(200,self.settle_default)
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(200)
        self.analyzer_timer=QTimer(self);self.analyzer_timer.timeout.connect(self.poll_analyzer);self.analyzer_timer.start(33)
        self.saved_art=json.dumps(self.owner.values(),sort_keys=True)
        QApplication.instance().applicationStateChanged.connect(lambda state:self.owner.release_preview_holds() if state!=Qt.ApplicationActive else None)
        QApplication.instance().focusChanged.connect(lambda old,new:self.owner.release_preview_holds() if not self.closing else None)
        QApplication.instance().installEventFilter(self)
        for screen in QApplication.screens():screen.availableGeometryChanged.connect(lambda rect:self.recover())
        QApplication.instance().screenRemoved.connect(lambda screen:QTimer.singleShot(0,self.recover))
        QApplication.instance().screenAdded.connect(lambda screen:self.recover())
    def body(self):
        body=QWidget();layout=QVBoxLayout(body);layout.setContentsMargins(10,8,10,8);layout.setSpacing(7);return body,layout
    def button(self,layout,title,callback):
        button=QPushButton(title);button.setObjectName('signal' if 'Start' in title else 'accent' if 'BONK' in title or title=='Save Authored' else '');button.clicked.connect(lambda:self.safe(callback));layout.addWidget(button);return button
    def dock(self,key,title,body,area,relative=None):
        dock=ads.CDockWidget(title);dock.setObjectName(key);dock.setWidget(body)
        help_action=QAction('?',dock);help_action.setToolTip(title+' help (F1)')
        help_action.triggered.connect(self.help);dock.setTitleBarActions([help_action])
        dock.setMinimumSize(240 if key!='preview' else 400,100)
        self.panels[key]=dock;result=self.manager.addDockWidget(area,dock,relative)
        return result
    def build(self):
        preview,layout=self.body();heading=QHBoxLayout();self.title=QLabel('Main • Ready');self.title.setObjectName('sceneTitle');heading.addWidget(self.title,1)
        self.quality=QLabel('Full quality');self.quality.setObjectName('muted');heading.addWidget(self.quality,0,Qt.AlignRight);layout.addLayout(heading)
        self.quality.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);self.quality.setMinimumWidth(160);self.quality.setMaximumWidth(250)
        self.title.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
        self.title.setMaximumHeight(24);self.quality.setMaximumHeight(24);layout.setAlignment(Qt.AlignTop)
        layout.addWidget(self.surface,1);self.placeholder=QWidget(self.surface);progress=QVBoxLayout(self.placeholder)
        progress.addStretch();self.progress_title=QLabel('Select a world and Start');self.progress_title.setAlignment(Qt.AlignCenter);progress.addWidget(self.progress_title)
        self.progress_bar=QProgressBar();self.progress_bar.setRange(0,0);self.progress_bar.hide();progress.addWidget(self.progress_bar)
        actions=QHBoxLayout();progress.addLayout(actions);actions.addStretch()
        self.cancel_button=self.button(actions,'Cancel',self.cancel_preview);self.cancel_button.hide()
        self.retry_button=self.button(actions,'Retry',self.start);self.retry_button.hide();actions.addStretch();progress.addStretch()
        self.surface_layout.addWidget(self.placeholder)
        center=self.dock('preview','Visualizer',preview,ads.CenterDockWidgetArea)
        tab=self.panels['preview'].tabWidget();tab.setContextMenuPolicy(Qt.CustomContextMenu)
        tab.customContextMenuRequested.connect(self.visualizer_menu)
        body,left=self.body()
        self.session=QLabel('Unsaved session');left.addWidget(self.session)
        self.tree=QTreeWidget();self.tree.setHeaderHidden(True);left.addWidget(self.tree,1)
        for scope,tree in STUDIO_TREES.items():
            parent=QTreeWidgetItem(self.tree,[scope.title()]);parent.setData(0,Qt.UserRole,(scope,[]));parent.setExpanded(True)
            def add(nodes,parent,path):
                for key,node in nodes.items():
                    item=QTreeWidgetItem(parent,[node['label']]);item.setData(0,Qt.UserRole,(scope,path+[key]));item.setToolTip(0,node['label']);item.setExpanded(len(path)<1)
                    add(node.get('children',{}),item,path+[key])
            add(tree,parent,[])
        self.tree.currentItemChanged.connect(self.world)
        self.tree.itemDoubleClicked.connect(self.double_load)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu);self.tree.customContextMenuRequested.connect(self.library_menu)
        self.scope_label=QLabel('Playback scope: stopped');self.scope_label.setWordWrap(True);left.addWidget(self.scope_label)
        leftarea=self.dock('session','World Library',body,ads.LeftDockWidgetArea,center)
        saved,sl=self.body();sl.addWidget(QLabel('Existing artistic sessions'))
        sessions=QTreeWidget();sessions.setHeaderHidden(True);sl.addWidget(sessions)
        for path in sorted((ROOT/'work/studio').glob('*.json')):
            if 'layout' not in path.name and path.name!='media-library.json':QTreeWidgetItem(sessions,[path.name])
        self.button(sl,'Open session…',self.open_session)
        self.dock('sessions','Saved sessions',saved,ads.CenterDockWidgetArea,leftarea);self.panels['sessions'].toggleView(False)
        presets,pl=self.body();pl.addWidget(QLabel('Existing color preset files'))
        listing=QTreeWidget();listing.setHeaderHidden(True);pl.addWidget(listing)
        for path in sorted(self.owner.color_preset_folder().glob('*.json')):QTreeWidgetItem(listing,[path.name])
        self.dock('presets','Color preset library',presets,ads.CenterDockWidgetArea,leftarea);self.panels['presets'].toggleView(False)
        setup,lay=self.body();self.source=QComboBox();self.source.addItems(['Device Listening','Audio File'])
        self.source.currentTextChanged.connect(lambda v:self.audio_action('source',value=v));lay.addWidget(self.source)
        self.track=QLabel('No decoded track selected');self.track.setWordWrap(True);lay.addWidget(self.track)
        self.button(lay,'Import audio…',self.import_audio);lay.addStretch()
        self.dock('setup','Preview setup',setup,ads.CenterDockWidgetArea,center);self.panels['setup'].toggleView(False)
        colors,cl=self.body();self.color_target=QComboBox();self.color_target.setMinimumContentsLength(12);self.color_target.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);cl.addWidget(self.color_target)
        self.color_fields=QWidget();self.color_layout=QGridLayout(self.color_fields);self.color_layout.setContentsMargins(0,0,0,0);cl.addWidget(self.color_fields)
        self.button(cl,'Reset target',self.reset_color_target);self.color_status=QLabel();self.color_status.setWordWrap(True);cl.addWidget(self.color_status);cl.addStretch()
        self.color_target.currentTextChanged.connect(lambda label:self.safe(lambda:self.choose_color_target(label)))
        right=self.dock('colors','Color Inspector',colors,ads.RightDockWidgetArea,center)
        tuning,tl=self.body();switches=QHBoxLayout();tl.addLayout(switches)
        self.pin=Switch('Pin target',self.pin_changed);self.pin.setToolTip('ON pins the editing destination; OFF follows the active form.');switches.addWidget(self.pin)
        self.override=Switch('Live override',self.override_changed);switches.addWidget(self.override)
        destinations=QHBoxLayout();tl.addLayout(destinations)
        self.forms=QComboBox();self.forms.addItems(list(self.client.snapshot['edit_forms'].values()));self.forms.currentTextChanged.connect(lambda label:self.safe(lambda:self.choose_form(label)));destinations.addWidget(self.forms)
        self.target=QComboBox();self.target.currentTextChanged.connect(lambda label:self.safe(lambda:self.choose_target(label)));destinations.addWidget(self.target)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);self.numeric_body=QWidget();self.numeric_layout=QVBoxLayout(self.numeric_body);self.numeric_layout.setContentsMargins(0,0,0,0);self.numeric_layout.setSpacing(3);scroll.setWidget(self.numeric_body);tl.addWidget(scroll,1)
        self.audio_status=QLabel();self.audio_status.setWordWrap(True);tl.addWidget(self.audio_status)
        self.save_authored=self.button(tl,'Save Authored',self.view.save_authored)
        self.save_destination=QLabel();self.save_destination.setWordWrap(True);self.save_destination.setObjectName('muted');tl.addWidget(self.save_destination)
        reset=self.button(tl,'Back to authored',self.view.reset)
        tl.removeWidget(self.save_authored);tl.removeWidget(reset);actions=QHBoxLayout();actions.addWidget(self.save_authored);actions.addWidget(reset);tl.insertLayout(tl.count()-1,actions)
        for combo in (self.forms,self.target):
            combo.setMinimumContentsLength(8);combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.dock('tuning','Audio Tuning',tuning,ads.BottomDockWidgetArea,right)
        monitor,ml=self.body();ml.addWidget(QLabel('Read only • CPU submitted mapping'))
        self.monitor=MappingMeters();ml.addWidget(self.monitor,1)
        self.dock('monitor','Mapping Monitor',monitor,ads.BottomDockWidgetArea,self.panels['tuning'].dockAreaWidget())
        resources,rl=self.body();self.resource_mode=QComboBox();self.resource_mode.addItems(['Detailed','Simple'])
        self.resource_mode.setAccessibleName('Resource Monitor mode');rl.addWidget(self.resource_mode)
        resource_body,resource_layout=self.body()
        self.resource_text=QLabel('Resources warming up');self.resource_text.setWordWrap(True);self.resource_text.setTextInteractionFlags(Qt.TextSelectableByMouse);resource_layout.addWidget(self.resource_text)
        self.resource_simple=QWidget();simple_layout=QVBoxLayout(self.resource_simple);self.resource_fields={}
        from studio_resources import SIMPLE_TOOLTIPS
        for name,tooltip in SIMPLE_TOOLTIPS.items():
            label=QLabel(name+': unavailable');label.setToolTip(tooltip);label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse);simple_layout.addWidget(label);self.resource_fields[name]=label
        resource_layout.addWidget(self.resource_simple);resource_layout.addStretch();self.resource_simple.hide()
        self.resource_mode.currentTextChanged.connect(self.resource_mode_changed)
        resource_scroll=QScrollArea();resource_scroll.setWidgetResizable(True);resource_scroll.setWidget(resource_body);rl.addWidget(resource_scroll)
        self.dock('resources','Resources',resources,ads.CenterDockWidgetArea,self.panels['monitor'].dockAreaWidget());self.panels['resources'].toggleView(False)
        transport,tr=self.body();row=QHBoxLayout();tr.addLayout(row)
        self.start_button=self.button(row,'▶ Start',self.start);self.button(row,'Ⅱ Pause / Resume',self.owner.pause_preview)
        self.button(row,'■ Stop',self.cancel_preview);hold=QPushButton('Hold');row.addWidget(hold)
        hold.pressed.connect(lambda:self.owner.hold_preview('qt.mouse',True));hold.released.connect(lambda:self.owner.hold_preview('qt.mouse',False))
        extras=QHBoxLayout();tr.addLayout(extras);self.bonk_button=self.button(extras,'◆ BONK',self.owner.bonk_preview)
        mode=QComboBox();mode.addItems(['Normal','Instant']);mode.currentTextChanged.connect(lambda v:self.owner.bonk_mode.set(v));extras.addWidget(mode)
        self.transport_status=QLabel();self.transport_status.setWordWrap(True);tr.addWidget(self.transport_status)
        bottom=self.dock('transport','Transport',transport,ads.BottomDockWidgetArea,center)
        analyzer,al=self.body();self.analyzer=BandAnalyzer();al.addWidget(self.analyzer,1);self.analyzer_requested=None
        self.dock('analyzer','Band Analyzer',analyzer,ads.RightDockWidgetArea,bottom)
        waveform,wl=self.body();self.create_audio_hub(wl);self.waveform=Waveform();self.waveform.seekRequested.connect(lambda seconds,revision,identity:self.audio_action('seek',seconds=seconds,file_revision=revision,seek_id=identity));wl.addWidget(self.waveform)
        self.dock('waveform','Session waveform',waveform,ads.CenterDockWidgetArea,bottom)
        self.panels['transport'].setAsCurrentTab()
        diagnostics,dl=self.body();self.logs=QPlainTextEdit();self.logs.setReadOnly(True);dl.addWidget(self.logs)
        self.button(dl,'Open diagnostics folder',lambda:os.startfile(str(ROOT/'work/studio')))
        self.dock('diagnostics','Diagnostics',diagnostics,ads.CenterDockWidgetArea,center);self.panels['diagnostics'].toggleView(False)
        from studio_media import MediaLibrary
        from studio_composition import Layers,CompositionEditor
        self.media_library=MediaLibrary(self);self.image_editor=Layers(self)
        self.dock('media','Media Library',self.media_library,ads.CenterDockWidgetArea,leftarea);self.panels['media'].toggleView(False)
        self.dock('image_layers','Layers',self.image_editor,ads.CenterDockWidgetArea,right);self.panels['image_layers'].toggleView(False)
        self.composition_editor=CompositionEditor(self.image_editor)
        self.dock('composition','Composition Editor',self.composition_editor,ads.CenterDockWidgetArea,center);self.panels['composition'].toggleView(False)
        self.media_library.refresh();self.image_editor.refresh()
        self.statusBar().showMessage('Qt proof • F1 help')
        self.refresh_colors();self.tuning_identity=None;self.refresh_tuning()
    def create_header(self):
        brand=QWidget();row=QHBoxLayout(brand);row.setContentsMargins(12,0,20,0)
        title=QLabel('ZeraphinaX');title.setObjectName('brand');row.addWidget(title)
        subtitle=QLabel('ZeraWave Studio');subtitle.setObjectName('muted');row.addWidget(subtitle)
        self.brand=brand;brand.setFixedSize(330,42);bar=QMenuBar();bar.setNativeMenuBar(False)
        self.menu_bar=bar
        header=QWidget();header_row=QHBoxLayout(header);header_row.setContentsMargins(0,0,0,0);header_row.setSpacing(0)
        header_row.addWidget(brand);header_row.addWidget(bar);header_row.addStretch();header.setMinimumHeight(44);self.header=header;self.setMenuWidget(header)
        buttons=[]
        for text,name,callback in (('—','Minimize window',self.showMinimized),('□','Maximize window',lambda:self.chrome.toggle_maximize()),('×','Close Studio',self.close)):
            button=QPushButton(text);button.setAccessibleName(name);button.setToolTip(name);button.setFixedSize(42,36);button.clicked.connect(callback);header_row.addWidget(button);buttons.append(button)
        from studio_chrome import WindowChrome
        self.chrome=WindowChrome(self,header,*buttons);self.chrome.install();self.chrome.sync()
    def menus(self):
        # Connection readiness changes menu contents, never native chrome.
        # Reapplying FRAMECHANGED while maximized loses Windows' restore rect.
        if not hasattr(self,'menu_bar'):self.create_header()
        else:self.menu_bar.clear()
        bar=self.menu_bar;bar.setEnabled(self.client is not None)
        file=bar.addMenu('&File');file.addAction('Open session…',lambda:self.safe(self.open_session))
        file.addAction('Save session…',lambda:self.safe(self.save_session));file.addAction('Import media…',self.import_media);file.addSeparator();file.addAction('Exit',self.close)
        edit=bar.addMenu('&Edit');edit.addAction('Reset selected color target',lambda:self.safe(self.owner.color_editor.reset_target))
        edit.addAction('Restore saved tuning draft at selected destination',lambda:self.safe(lambda:self.client.request('restore_draft',binding=self.view.binding())))
        view=bar.addMenu('&View')
        for dock in self.panels.values():view.addAction(dock.toggleViewAction())
        view.addSeparator();view.addAction('Reset Layout',self.reset_layout);view.addAction('Recover floating panels',self.recover)
        view.addAction('Demonstrate nine adjacent panels',self.nine_panels)
        self.settings_menu=QMenu('&Settings',bar);bar.addMenu(self.settings_menu)
        if not hasattr(self,'resolution_menu'):self.create_resolution_menu()
        self.settings_menu.addMenu(self.resolution_menu)
        if not hasattr(self,'audio_menu'):self.create_audio_menu()
        self.settings_menu.addMenu(self.audio_menu)
        help=bar.addMenu('&Help');help.addAction('Proof controls and limitations',self.help)
        help.addAction('Diagnostics',lambda:self.panels['diagnostics'].toggleView(True))
    def create_resolution_menu(self):
        from visualizer_resolution import PRESETS
        self.resolution_menu=QMenu('Visualizer Resolution',self)
        self.resolution_group=QActionGroup(self);self.resolution_group.setExclusive(True);self.resolution_actions={}
        for width,height in PRESETS:
            label=f'{width}×{height}'
            action=QAction(label,self);self.resolution_menu.addAction(action);action.setCheckable(True);self.resolution_group.addAction(action)
            action.triggered.connect(lambda checked=False,w=width,h=height:self.choose_resolution({'mode':'fixed','size':[w,h],'choice':f'{w}×{h}'}))
            self.resolution_actions[label]=action
        for label,callback in (('Native',lambda:self.choose_resolution({'mode':'native'})),('Custom…',self.custom_resolution)):
            action=QAction(label,self);self.resolution_menu.addAction(action);action.setCheckable(True);self.resolution_group.addAction(action)
            action.triggered.connect(callback);self.resolution_actions[label]=action
        self.resolution_menu.aboutToShow.connect(self.sync_resolution)
        self.resolution_info=QAction('',self);self.resolution_menu.addAction(self.resolution_info);self.resolution_info.setEnabled(False)
        self.sync_resolution()
    def sync_resolution(self):
        resolution=self.client.snapshot.get('resolution',{}) if self.client else {};policy=resolution.get('policy')
        selected=('Native' if policy['mode']=='native' else ('Custom…' if policy['choice']=='Custom' else policy['choice'])) if policy else None
        for label,action in self.resolution_actions.items():action.setChecked(label==selected)
        preview=self.client.snapshot.get('preview',{}) if self.client else {};dimensions=preview.get('dimensions',{})
        pixels=dimensions.get('internal');actual='×'.join(map(str,pixels)) if pixels else 'unavailable (preview stopped)'
        legacy=(self.owner.vars['render_scale'].get() if self.client else 'existing Quality setting')
        description=('Native physical pixels' if policy and policy['mode']=='native' else 'Fixed pixels • aspect fit') if policy else 'Existing Quality: '+legacy+' • choose a resolution to replace scale'
        self.resolution_info.setText('Internal '+actual+(' • applying…' if resolution.get('pending') else '')+' • '+description)
        if hasattr(self,'quality'):
            self.quality.setText((actual if pixels else 'Internal — stopped')+' • '+('Native' if policy and policy['mode']=='native' else 'Fixed' if policy else 'Quality '+str(round(dimensions.get('scale',__import__('studio').RENDER_SCALES.get(legacy,1.))*100))+'%'));self.quality.setToolTip('Actual internal render pixels. '+description+'; explicit resolutions use no additional Quality reduction.')
        error=resolution.get('error')
        if error and error!=getattr(self,'resolution_error_seen',None):self.statusBar().showMessage(error)
        self.resolution_error_seen=error
    def choose_resolution(self,policy):
        self.queue_operation('resolution',policy=policy,preview_run=self.client.snapshot.get('preview_run'))
        self.sync_resolution()
    def custom_resolution(self):
        resolution=self.client.snapshot.get('resolution',{});policy=resolution.get('policy') or {}
        size=policy.get('size') or (self.owner.preview_state.get('dimensions') or {}).get('internal') or [1280,720]
        limit=resolution.get('limit',16384)
        dialog=QDialog(self);dialog.setWindowTitle('Custom Visualizer Resolution');layout=QFormLayout(dialog);fields=[]
        for label,value in zip(('Width','Height'),size):
            spin=QSpinBox();spin.setRange(1,limit);spin.setValue(value);spin.setSuffix(' px');spin.setAccessibleName(label)
            spin.setToolTip(f'Actual internal render pixels; device limit {limit}');layout.addRow(label,spin);fields.append(spin)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addRow(buttons)
        if dialog.exec()==QDialog.Accepted:self.choose_resolution({'mode':'fixed','size':[spin.value() for spin in fields],'choice':'Custom'})
        else:self.sync_resolution()
        dialog.deleteLater()
    def visualizer_menu(self,pos):
        tab=self.panels['preview'].tabWidget()
        menu=tab.buildContextMenu(None)  # retain ADS's own docking actions
        self.extend_visualizer_menu(menu)
        menu.exec(tab.mapToGlobal(pos));menu.deleteLater()
    def extend_visualizer_menu(self,menu):
        menu.addSeparator();resolution=QMenu('Visualizer Resolution',menu);menu.addMenu(resolution)
        for action in self.resolution_actions.values():resolution.addAction(action)
        resolution.addAction(self.resolution_info);self.sync_resolution()
        return resolution
    def resource_mode_changed(self,mode):
        self.resource_text.setVisible(mode=='Detailed');self.resource_simple.setVisible(mode=='Simple');self.resource_stamp=0.
    def help(self):
        self.panels['diagnostics'].toggleView(True)
        self.logs.setPlainText('Drag tabs or floating title bars into highlighted targets. View recovers hidden panels.\n'
            'Right-click numeric tuning controls to switch knob/slider or reset that parameter to its authored value.\n'
            'Pin retains the editing destination; Follow is Pin OFF. Disabled controls need a current compatible ACK.\n'
            'Layout reset changes presentation only. A separate control process owns artistic state.\n'
            'Full legacy controls, profile dialogs, palette cycle tools and audition UI remain pending migration.\n'
            'Use run_unified_studio.vbs for the previous presentation. F1 opens this help.\n'
            'Current transport: '+self.owner.active_preview.get()+'\nCurrent colors: '+self.owner.color_status.get()+'\n'+str(self.layout_path))
    def safe(self,callback):
        try:return callback()
        except Exception as exc:self.error(exc,exc.__traceback__)
    def error(self,exc,tb=None):
        text=''.join(traceback.format_exception(type(exc),exc,tb));self.errors.append(text)
        path=ROOT/'work/studio/qt-errors.log'
        try:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(self.errors),encoding='utf8')
        except OSError:text+='\nDiagnostics file unavailable; details retained in this panel.'
        self.statusBar().showMessage(f'{type(exc).__name__}: {exc or "Operation failed"} — View > Diagnostics')
        self.logs.setPlainText(str(path)+'\n\n'+text);self.panels['diagnostics'].toggleView(True)
    def world(self,item,previous):
        if item is None:return
        scope,path=item.data(0,Qt.UserRole)
        self.browsed=(scope,list(path))
    def double_load(self,item,column=0):
        if item.childCount():return  # QTreeWidget retains its native expansion.
        self.load_leaf(item)
    def library_menu(self,pos):
        item=self.tree.itemAt(pos)
        if item is None or item.childCount():return
        menu=QMenu(self);menu.addAction('Load',lambda:self.load_leaf(item));menu.exec(self.tree.viewport().mapToGlobal(pos))
    def load_leaf(self,item):
        scope,path=item.data(0,Qt.UserRole)
        from studio_scope import leaf_destination
        from renderer import LIVE_FORMS
        leaf_destination(scope,path,self.client.snapshot.get('committed_scope'),LIVE_FORMS)
        self.load_revision=max(self.load_revision,self.client.snapshot.get('destination_revision',0))+1
        self.cancel_attach=False
        self.queue_operation('load_leaf',scope=scope,path=list(path),revision=self.load_revision)
    def queue_operation(self,action,**data):
        if self.operation and not self.operation.done():
            self.pending_operation=(action,data)
            return
        if action=='load_leaf':data['preview_run']=self.client.snapshot.get('preview_run')
        self.operation=self.operations.submit(self.client.request,action,**data)
        if action in ('start','load_leaf') and not self.client.snapshot.get('running'):
            self.starting=True;self.progress_title.setText('Connecting to preview owner…');self.progress_bar.show();self.cancel_button.show();self.retry_button.hide()
    def cancel_preview(self):
        self.cancel_attach=True;self.pending_operation=None
        self.progress_title.setText('Cancellation pending — waiting for the owned renderer to stop')
        self.queue_operation('stop')
    def choose_track(self):self.import_audio()
    def audio_action(self,op,**values):
        if not self.client:return
        self.safe(lambda:self.client.request('audio_transport',op=op,values=values))
        if op in ('source','device','open') and 'waveform' in self.panels:
            self.panels['waveform'].toggleView(True);self.panels['waveform'].setAsCurrentTab()
    def import_audio(self):
        path,_=QFileDialog.getOpenFileName(self,'Import audio',str(ROOT),'Audio files (*.wav *.mp3)')
        if path:self.audio_action('open',path=path)
    def create_audio_hub(self,layout):
        self.hub_source=TwoWaySwitch('Audio source',('Device Listening','Audio File'));layout.addWidget(self.hub_source)
        self.hub_source.currentTextChanged.connect(lambda v:self.audio_action('source',value=v))
        self.hub_device=QComboBox();self.hub_device.setMinimumContentsLength(12)
        self.hub_device.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);layout.addWidget(self.hub_device)
        self.hub_device.setToolTip('Exact output-device loopback or explicit microphone. Analysis only; captured input is never replayed.')
        self.hub_device.activated.connect(lambda i:self.audio_action('device',value=self.hub_device.itemData(i)) if self.hub_device.itemData(i) else None)
        self.hub_refresh=icon_button('refresh','Refresh listening devices',lambda:self.audio_action('refresh'));layout.addWidget(self.hub_refresh)
        self.file_controls=QWidget();controls=QVBoxLayout(self.file_controls);controls.setContentsMargins(0,0,0,0);controls.setSpacing(5);layout.addWidget(self.file_controls)
        transport=QHBoxLayout();transport.setSpacing(5);controls.addLayout(transport)
        self.audio_buttons={}
        for kind,description in (('open','Open audio file'),('reverse','Rewind at selected scan rate (audible)'),('play','Play at normal speed'),('pause','Pause audio'),('stop','Stop and return to start'),('forward','Fast forward at selected scan rate (audible)')):
            button=icon_button(kind,description,lambda checked=False,o=kind:self.import_audio() if o=='open' else self.scan_audio(-1 if o=='reverse' else 1) if o in ('reverse','forward') else self.audio_action(o))
            transport.addWidget(button);self.audio_buttons[kind]=button
        transport.addStretch(1);transport.addWidget(QLabel('Scan'))
        self.hub_rate=QComboBox();self.hub_rate.addItems(['2×','4×','6×','12×']);self.hub_rate.setFixedWidth(68)
        self.hub_rate.setAccessibleName('Forward / rewind scan rate');self.hub_rate.setToolTip('Audible forward/reverse speed. Pitch changes with rate; Play returns to normal 1×.')
        self.hub_rate.currentIndexChanged.connect(self.scan_rate_changed);transport.addWidget(self.hub_rate)
        modes=QHBoxLayout();controls.addLayout(modes)
        self.hub_repeat=TwoWaySwitch('Repeat',('Once','Loop'),lambda v:self.audio_action('repeat',value=v));modes.addWidget(self.hub_repeat)
        self.hub_mute=TwoWaySwitch('Output',('Sound','Muted'),lambda v:self.audio_action('mute',value=v));modes.addWidget(self.hub_mute)
        self.hub_mute.setToolTip('Mute file output only. Analysis and visual input continue.')
        volume_row=QHBoxLayout();volume_row.addWidget(QLabel('Output volume'));controls.addLayout(volume_row)
        self.hub_volume=QSlider(Qt.Horizontal);self.hub_volume.setRange(0,100);self.hub_volume.setValue(100)
        self.hub_volume.setAccessibleName('File output volume');self.hub_volume.setToolTip('0–100% file output only. 100% is unity gain. Analysis and visual input are unaffected.')
        self.hub_volume_label=QLabel('100%');volume_row.addWidget(self.hub_volume,1);volume_row.addWidget(self.hub_volume_label)
        self.volume_timer=QTimer(self);self.volume_timer.setSingleShot(True);self.volume_timer.setInterval(100)
        self.volume_expected=None;self.volume_timer.timeout.connect(self.send_volume)
        self.hub_volume.valueChanged.connect(lambda v:(self.hub_volume_label.setText(f'{v}%'),self.volume_timer.start()))
        self.hub_raw=TwoWaySwitch('Visual drive',('Analyzed','Raw waveform'),lambda v:self.audio_action('raw_waveform',value=v));layout.addWidget(self.hub_raw)
        self.hub_raw.setToolTip('Analyzed: musical levels with saved tuning. Raw waveform: PCM RMS/peak before output gain; bypasses normalization and visual audio tuning. Shared audio previews only.')
        self.hub_status=QLabel('Audio owner warming up');self.hub_status.setWordWrap(True);layout.addWidget(self.hub_status)
        self.audio_device_identity=None
    def scan_audio(self,direction):
        hub=self.client.snapshot.get('audio_hub',{})
        self.audio_action('speed',value=direction*(2,4,6,12)[self.hub_rate.currentIndex()],play=True,file_revision=hub.get('file_revision',0))
    def scan_rate_changed(self,index):
        hub=self.client.snapshot.get('audio_hub',{});speed=hub.get('speed',1.)
        if abs(speed)!=1. and hub.get('mode')=='Audio File':
            self.audio_action('speed',value=(-1 if speed<0 else 1)*(2,4,6,12)[index],file_revision=hub.get('file_revision',0))
    def create_audio_menu(self):
        self.audio_menu=QMenu('Audio',self);self.audio_source_group=QActionGroup(self);self.audio_source_group.setExclusive(True)
        self.audio_source_actions={}
        for mode in ('Device Listening','Audio File'):
            action=QAction(mode,self);action.setCheckable(True);self.audio_source_group.addAction(action);self.audio_menu.addAction(action)
            action.triggered.connect(lambda checked=False,v=mode:self.audio_action('source',value=v));self.audio_source_actions[mode]=action
        self.audio_devices_menu=self.audio_menu.addMenu('Listening device')
        self.audio_device_group=QActionGroup(self.audio_devices_menu);self.audio_device_group.setExclusive(True)
        self.audio_menu.addAction('Refresh listening devices',lambda:self.audio_action('refresh'))
        self.audio_menu.addSeparator();self.audio_menu.addAction('Import audio…',self.import_audio)
        self.audio_raw_action=QAction('Raw waveform drives visuals',self);self.audio_raw_action.setCheckable(True);self.audio_raw_action.triggered.connect(lambda v:self.audio_action('raw_waveform',value=v));self.audio_menu.addAction(self.audio_raw_action)
        self.audio_menu.aboutToShow.connect(self.sync_audio_hub)
    def send_volume(self):
        value=self.hub_volume.value()/100.
        self.volume_expected=(value,time.perf_counter()+2.)
        self.audio_action('volume',value=value)
    def sync_audio_hub(self):
        hub=self.client.snapshot.get('audio_hub',{})
        if not hub:return
        mode=hub['mode'];file=mode=='Audio File'
        for combo in (self.hub_source,self.source):
            combo.blockSignals(True);combo.setCurrentText(mode);combo.blockSignals(False)
        self.file_controls.setVisible(file);self.hub_device.setVisible(not file);self.hub_refresh.setVisible(not file)
        for op in ('mute','repeat'):
            getattr(self,'hub_'+op).sync(hub[op])
        speed=hub.get('speed',1.)
        if abs(speed) in (2,4,6,12):
            self.hub_rate.blockSignals(True);self.hub_rate.setCurrentIndex((2,4,6,12).index(abs(speed)));self.hub_rate.blockSignals(False)
        for kind,button in self.audio_buttons.items():
            if kind!='open':button.setEnabled(file and bool(hub.get('path')) and hub.get('status')!='Release unconfirmed')
            active=file and ((kind=='play' and hub['playing'] and speed==1.) or (kind=='forward' and hub['playing'] and speed>1.) or (kind=='reverse' and hub['playing'] and speed<0.) or (kind=='pause' and hub['status']=='Paused') or (kind=='stop' and hub['status']=='Stopped'))
            if button.property('active')!=active:
                button.setProperty('active',active);button.style().unpolish(button);button.style().polish(button)
        self.hub_raw.sync(hub.get('raw_waveform',False));self.audio_raw_action.setChecked(hub.get('raw_waveform',False))
        if self.volume_expected and (hub.get('volume',1.)==self.volume_expected[0] or time.perf_counter()>self.volume_expected[1]):self.volume_expected=None
        if not self.hub_volume.isSliderDown() and not self.volume_timer.isActive() and self.volume_expected is None:
            self.hub_volume.blockSignals(True);self.hub_volume.setValue(round(hub.get('volume',1.)*100));self.hub_volume.blockSignals(False);self.hub_volume_label.setText(f"{round(hub.get('volume',1.)*100)}%")
        devices=hub['devices'];identity=json.dumps([devices,hub['device']],sort_keys=True)
        if identity!=self.audio_device_identity:
            self.audio_device_identity=identity;self.hub_device.blockSignals(True);self.hub_device.clear()
            self.hub_device.addItem('Select listening device…',None);self.audio_devices_menu.clear()
            for device in devices:
                label=('Output loopback: ' if device['kind']=='loopback' else 'Microphone: ')+device['name']
                self.hub_device.addItem(label,device)
                action=QAction(label,self.audio_devices_menu);action.setCheckable(True);self.audio_device_group.addAction(action);self.audio_devices_menu.addAction(action)
                action.setChecked(device==hub['device']);action.triggered.connect(lambda checked=False,d=device:self.audio_action('device',value=d))
                if device==hub['device']:self.hub_device.setCurrentIndex(self.hub_device.count()-1)
            self.hub_device.blockSignals(False)
        for value,action in self.audio_source_actions.items():action.setChecked(value==mode)
        self.audio_devices_menu.setEnabled(not file)
        status=hub['status']
        if file:status+=' • '+('Reverse ' if speed<0 else '')+f'{abs(speed):g}×'
        if hub.get('pending'):status+=' • applying'
        if hub.get('error'):status+=' • '+hub['error']
        if hub.get('device_error') and not file:status+=' • devices: '+hub['device_error']
        status+=' • '+('Raw waveform' if hub.get('raw_waveform') else 'Analyzed')+' drives visuals'
        if not hub['stale'] and hub.get('rms') is not None:
            import math
            status+=f"\nPCM RMS {20*math.log10(max(hub['rms'],1e-12)):.1f} dBFS • Peak {20*math.log10(max(hub.get('peak') or 0.,1e-12)):.1f} dBFS"
            if file and hub.get('output_rms') is not None:status+=f" • Output {20*math.log10(max(hub['output_rms'],1e-12)):.1f} dBFS"
            if hub.get('output_clipped'):status+=' • output clipping'
            if hub.get('source_clipped'):status+=' • source over full scale'
        self.hub_status.setText(status);self.track.setText(hub['path'] or 'No audio file selected')
        self.hub_status.setToolTip('Audio playhead counts submitted decoded/captured PCM, not measured speaker latency. Output volume/mute affect playback only; PCM/analyzer levels are pre-output digital RMS/peak. dBFS0 is full scale; silence reads -240dBFS. Raw mode bypasses visual audio tuning without changing saved values. Seek resets queued PCM events; visual clocks stay independent. Audible scan changes pitch.')
        self.waveform.refresh(hub)
    def open_session(self):
        if not self.image_editor.resolve_pending():return
        path,_=QFileDialog.getOpenFileName(self,'Open artistic session',str(ROOT/'work/studio'),'Session (*.json)')
        if path:
            self.client.request('load',path=path)
            self.refresh_colors()
    def import_media(self):
        self.panels['media'].toggleView(True);self.panels['media'].setAsCurrentTab();self.media_library.import_files()
    def save_session(self):
        if not self.image_editor.resolve_pending():return
        path,_=QFileDialog.getSaveFileName(self,'Save artistic session',str(ROOT/'work/studio/session.json'),'Session (*.json)')
        if path:
            if self.client.disconnected:raise ValueError('Owner disconnected; the operation outcome is unknown and this instance cannot save an authoritative revision. Keep it open; memory-only pixels are not a durable session.')
            import uuid
            key=uuid.uuid4().hex
            requested=json.dumps(self.owner.values(),sort_keys=True)
            self.client.request('save',path=path,save_id=key)
            self.requested_save=(key,requested)
            self.statusBar().showMessage('Saving pinned document revision; newer edits remain separate.')
    def start(self):
        if self.owner.process is None and not self.operation:
            self.panels['preview'].toggleView(True);self.panels['preview'].setAsCurrentTab()
            self.progress_title.setText('Starting requested preview • first load may take longer; waiting for renderer telemetry')
            self.progress_bar.setRange(0,0)
            self.native=None;self.cancel_attach=False
            scope,path=self.browsed
            self.queue_operation('start',scope=scope,path=path)
    def clear(self,layout):
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
    def refresh_colors(self):
        editor=self.owner.color_editor;editor.targets=targets_for(self.owner.color_scene())
        if not editor.targets:return
        if editor.target_choice.get() not in [t.label for t in editor.targets] or not editor.target().slots:
            preferred=next((t for t in editor.targets if t.scene==self.owner.color_scene() and t.slots),next((t for t in editor.targets if t.slots),editor.targets[0]))
            editor.target_choice.set(preferred.label)
        editor.scene=self.owner.color_scene();editor.refresh();self.color_target.blockSignals(True);self.color_target.clear();self.color_target.addItems([t.label for t in editor.targets]);self.color_target.setCurrentText(editor.target_choice.get());self.color_target.blockSignals(False)
        self.color_identity=(self.client.snapshot['color_scene'],self.client.snapshot['color_target'])
        self.clear(self.color_layout);target=editor.target();values=resolved_slots(target,self.owner.color_overrides)
        for i,(slot,value) in enumerate(zip(target.slots,values)):
            button=QPushButton(slot.label+'\n'+rgb_hex(value[0]));button.setMinimumHeight(70);button.setStyleSheet('background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 '+rgb_hex(value[0])+',stop:0.35 '+rgb_hex(value[0])+',stop:0.36 #192329,stop:1 #192329); border:1px solid #46555d; padding-top:25px; padding-bottom:4px; text-align:left; font-size:9pt;')
            button.clicked.connect(lambda checked=False,t=target.id,r=slot.id:self.color_edit(t,r));self.color_layout.addWidget(button,i//2,i%2)
    def choose_color_target(self,label):
        if not label:return
        self.owner.color_editor.target_choice.set(label);self.refresh_colors()
    def color_edit(self,target,role):
        editor=self.owner.color_editor
        destination=(self.client.snapshot.get('preview_run'),self.client.snapshot.get('destination_revision',0))
        if editor.target().id!=target:return
        declaration=editor.target();index=next(i for i,s in enumerate(declaration.slots) if s.id==role)
        initial=QColor(rgb_hex(resolved_slots(declaration,self.owner.color_overrides)[index][0]))
        value=QColorDialog.getColor(initial,self,editor.target().label+' / '+role)
        if value.isValid() and editor.target().id==target and destination==(self.client.snapshot.get('preview_run'),self.client.snapshot.get('destination_revision',0)):
            editor.commit(role,{'color':value.name().upper()});self.refresh_colors()
    def reset_color_target(self):self.owner.color_editor.reset_target();self.refresh_colors()
    def pin_changed(self):self.safe(lambda:self.view.pin.set(self.pin.isChecked()))
    def override_changed(self):self.safe(lambda:self.view.enabled.set(self.override.isChecked()))
    def choose_form(self,label):
        if label and label!=self.view.form_var.get():
            self.view.select_form(form=int(next(k for k,v in self.client.snapshot['edit_forms'].items() if v==label)));self.refresh_tuning(force=True)
    def choose_target(self,label):
        if label and label!=self.view.target_var.get():self.view.target_var.set(label);self.view.select_target();self.refresh_tuning(force=True)
    def refresh_tuning(self,force=False):
        identity=(self.view.owner_key(),tuple(self.view.bounds),self.client.snapshot.get('destination_revision',0))
        self.pin.sync(self.view.pin.get());self.override.sync(self.view.enabled.get())
        if identity!=self.tuning_identity or force:
            self.tuning_identity=identity
            self.forms.blockSignals(True);self.forms.setCurrentText(self.view.form_var.get());self.forms.blockSignals(False)
            self.target.blockSignals(True);self.target.clear();self.target.addItems([t[1] for t in self.view.data['choices']]);self.target.setCurrentText(self.view.target.label);self.target.blockSignals(False)
            self.clear(self.numeric_layout);self.numerics=[]
            advanced=QGroupBox('Advanced • listening windows');advanced.setCheckable(True);advanced.setChecked(False)
            advanced_body=QWidget();advanced_layout=QVBoxLayout(advanced_body);outer=QVBoxLayout(advanced);outer.addWidget(advanced_body)
            advanced_body.hide();advanced.toggled.connect(advanced_body.setVisible)
            for index,key in enumerate(self.view.bounds):
                widget=Numeric(self,self.view,key,index);self.numerics.append(widget)
                (advanced_layout if key.endswith("_hz") or key=="impact_sensitivity" else self.numeric_layout).addWidget(widget)
            for name,var in self.view.range_vars.items():
                check=self.view.range_checks[name]
                if name in self.view.data['ranges']:
                    switch=Switch(name.title()+' range',lambda checked,n=name:self.range_edit(n,checked));switch.sync(var.get());switch.setEnabled(str(check.cget('state'))!='disabled');advanced_layout.addWidget(switch)
            self.numeric_layout.addWidget(advanced)
            self.numeric_layout.addStretch()
        for i,widget in enumerate(self.numerics):
            widget.setEnabled(str(self.view.sliders[i].cget('state'))!='disabled')
            if not widget.spin.hasFocus() and not widget.dial.isSliderDown() and not widget.slider.isSliderDown():widget.sync()
        self.save_authored.setText('Save Authored');self.save_authored.setToolTip(self.view.author_button.cget('text'));self.save_authored.setEnabled(str(self.view.author_button.cget('state'))!='disabled')
        path=Path(self.view.data['authored_path']);self.save_destination.setText('Authored file destination \u2022 hover for full path');self.save_destination.setToolTip(str(path));self.save_destination.setAccessibleName(str(path))
        self.audio_status.setText(self.view.status.get()+(' • Raw waveform: tuning parked' if self.client.snapshot.get('audio_hub',{}).get('raw_waveform') else ''));self.audio_status.setToolTip(self.view.target_info.get())
    def range_edit(self,name,value):self.safe(lambda:self.view.range_vars[name].set(value))
    def poll(self):
        if self.closing:return
        if self.operation and self.operation.done():
            future=self.operation;self.operation=None
            try:future.result();self.refresh_colors()
            except Exception as exc:self.error(exc);self.progress_title.setText(str(exc));self.retry_button.show();self.progress_bar.hide()
            if self.pending_operation:
                action,data=self.pending_operation;self.pending_operation=None;self.queue_operation(action,**data)
        attach_future=getattr(self,'attach_future',None)
        if attach_future and attach_future.done():
            self.attach_future=None
            try:attach_future.result()
            except Exception as exc:self.error(exc);self.cancel_preview()
        if self.client.disconnected:
            if not self.disconnect_reported:
                self.disconnect_reported=True;self.client.job.close();self.error(RuntimeError('Control owner disconnected. Last received settings remain available through File > Save session. Reopen Studio to recover the connection.'))
                self.save_authored.setEnabled(False)
                for widget in self.numerics:widget.setEnabled(False)
            return
        began=time.perf_counter()
        owner_errors=self.client.snapshot.get('errors',[])
        if owner_errors and owner_errors[-1]!=self.owner_error_seen:
            self.owner_error_seen=owner_errors[-1]
            self.error(RuntimeError(owner_errors[-1].strip().splitlines()[-1]+'; owner diagnostics: '+str(self.client.log_path)))
        def update():
            self.media_library.refresh();self.image_editor.refresh()
            running=self.owner.process is not None and self.owner.process.poll() is None
            link=self.owner.color_link;latest=link.get_audio() if link and link.audio_run else None
            self.view.refresh(latest,running);self.refresh_tuning()
            if getattr(self,'color_identity',None)!=(self.client.snapshot['color_scene'],self.client.snapshot['color_target']):self.refresh_colors()
            run=self.client.snapshot.get('preview_run')
            if self.native and (not running or self.native.get('run')!=run):
                self.native=None
                if self.container:self.container.deleteLater();self.container=None;self.foreign=None
            if running and self.native is None and not self.cancel_attach:
                packet=link.get_window() if link else None
                if packet and packet.get('run')==run and owned_process(packet['pid'],self.owner.process.pid):
                    self.native=packet;self.foreign=QWindow.fromWinId(packet['hwnd'])
                    if self.foreign is None:raise RuntimeError('The owned renderer window could not be adopted.')
                    self.container=QWidget.createWindowContainer(self.foreign,self.surface);self.container.hide();self.surface_layout.addWidget(self.container)
                    self.container.winId()  # Materialize Qt's native parent while still hidden.
            if running and self.native and not self.cancel_attach and getattr(self,'attach_requested_run',None)!=run:
                if self.align_native():
                    self.attach_requested_run=run;self.attach_future=self.operations.submit(self.client.request,'attach',preview_run=run)
            if running and self.native and self.owner.preview_state.get('ready') and not self.cancel_attach:
                self.placeholder.hide()
                self.container.show();self.starting=False;self.active_run=run
                self.align_native()
            elif not running:
                self.native=None;self.placeholder.show()
                if self.container:self.container.deleteLater();self.container=None;self.foreign=None
                if self.starting and self.operation is None:
                    self.progress_title.setText('Preview cancelled' if self.cancel_attach else 'Preview stopped before readiness — '+self.client.snapshot.get('status','See Diagnostics'))
                    self.starting=False;self.progress_bar.hide();self.cancel_button.hide();self.retry_button.show()
                elif not self.starting:self.progress_bar.hide();self.cancel_button.hide();self.retry_button.show()
            elif not self.owner.preview_state.get('ready'):
                self.starting=True;self.placeholder.show();self.progress_bar.show();self.cancel_button.show()
                phase=self.client.snapshot.get('startup') or {}
                if phase.get('run')==run and not self.cancel_attach:
                    labels={'context':'Creating graphics context','compiling':'Compiling shaders','resources':'Preparing graphics resources','attaching':'Attaching preview','ready':'Preparing first presentation'}
                    self.progress_title.setText(labels.get(phase.get('phase'),'Starting preview')+f" • {phase.get('seconds',0.):.1f} s reported"+(' • first load may take longer' if phase.get('phase') in ('context','compiling','resources') else ''))
            values=self.owner.running_values if running else self.owner.values()
            shown=self.form_names.get(self.owner.preview_state.get('current_form'),self.client.snapshot['active_title'])
            self.title.setText(shown+' • '+self.client.snapshot.get('audio_hub',{}).get('mode',values['source']))
            self.sync_audio_hub()
            packet,stamp=latest if latest else ({},0)
            current=time.perf_counter()-stamp<1.5
            submitted=packet.get('audio_targets',{}).get(self.view.target.target_id,{})
            if self.monitor.isVisible():self.monitor.set_packet(submitted,self.view.target.label,current)
            transport=self.owner.active_preview.get();color=self.owner.color_status.get()
            self.transport_status.setToolTip(transport);self.color_status.setToolTip(color)
            state=self.owner.preview_state
            self.start_button.setEnabled(not running and self.operation is None)
            self.bonk_button.setEnabled(bool(state.get('can_bonk')))
            self.bonk_button.setToolTip(state.get('bonk_unavailable_reason') or 'Select an eligible alternative in the committed playback scope')
            scope=state.get('committed_scope') or self.client.snapshot.get('committed_scope')
            form=state.get('current_form')
            names=self.form_names
            self.scope_label.setText(('Playback scope: '+scope['namespace'].title()+' / '+scope['label'] if running and scope else 'Playback scope: stopped')+'\nRendered: '+names.get(form,str(form) if form is not None else 'unavailable')+('\n'+state['bonk_unavailable_reason'] if state.get('bonk_unavailable_reason') else ''))
            if running and self.client.snapshot.get('scope_note'):self.scope_label.setText(self.scope_label.text()+'\n'+self.client.snapshot['scope_note'])
            self.sync_resolution()
            if (self.resource_text.isVisible() or self.resource_simple.isVisible()) and time.perf_counter()-self.resource_stamp>=1.:
                from studio_resources import resource_text,simple_resources
                if self.resource_mode.currentText()=='Detailed':self.resource_text.setText(resource_text(self.client.snapshot))
                else:
                    for key,value in simple_resources(self.client.snapshot).items():self.resource_fields[key].setText(key+': '+value)
                self.resource_stamp=time.perf_counter()
            if transport.startswith('Active color preview'):
                transport=('Paused' if state.get('paused') else 'Held' if state.get('held') else 'Running' if state.get('ready') else 'Starting')+' • '+values['source']
            if color.startswith('Applied live to the running preview.'):
                color='Live pigments applied • other edits next preview'
            self.transport_status.setText(transport);self.color_status.setText(color);self.session.setText(self.owner.session_path.name if self.owner.session_path else 'Unsaved session')
        self.safe(update);self.samples.append((time.perf_counter()-began)*1000)
    def align_native(self):
        # Qt retains foreign-window parenting. Some Windows container moves
        # leave the adopted HWND at a parent-relative global offset. Correct
        # only mismatched geometry within that existing owned native parent.
        import ctypes as c
        from ctypes import wintypes as w
        native=NativeSurface(self.native['hwnd'],self.native['pid']);u=native.u
        parent=int(u.GetParent(native.hwnd) or 0)
        if not parent:return False
        from window_host import owner
        if owner(u,parent)!=os.getpid():raise RuntimeError('Renderer attachment parent is not owned by this Studio.')
        u.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)];u.GetClientRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
        u.ClientToScreen.argtypes=[w.HWND,c.POINTER(w.POINT)]
        rect=w.RECT();client=w.RECT();origin=w.POINT()
        if not (u.GetWindowRect(native.hwnd,c.byref(rect)) and u.GetClientRect(parent,c.byref(client)) and u.ClientToScreen(parent,c.byref(origin))):return False
        size=(client.right-client.left,client.bottom-client.top)
        if (rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top)!=(origin.x,origin.y,*size):
            native.attach(parent,*size,os.getpid())
        return True
    def restore(self):
        if not self.layout_path.exists():return
        try:
            data=json.loads(self.layout_path.read_text(encoding='utf8'));self.preferences=data.get('controls',{})
            self.image_editor.restore_tool_preferences()
            state=self.preferences.get('composition_toolbar')
            if state:self.composition_editor.restoreState(QByteArray.fromHex(state.encode()))
            self.analyzer.restore_configuration(self.preferences.get('band_analyzer'))
            self.manager.restoreState(QByteArray(base64.b64decode(data['docks'])))
            self.restoreGeometry(QByteArray(base64.b64decode(data['geometry'])));self.recover()
        except Exception as exc:self.error(exc)
    def poll_analyzer(self):
        if self.closing or not self.client:return
        visible=self.analyzer.isVisible()
        if visible!=self.analyzer_requested:
            self.audio_action('analyzer',value=visible);self.analyzer_requested=visible
        if visible:self.analyzer.refresh(self.client.latest_analyzer())
    def save_layout(self):
        self.layout_path.parent.mkdir(parents=True,exist_ok=True)
        self.image_editor.remember_tools();self.preferences['composition_toolbar']=bytes(self.composition_editor.saveState().toHex()).decode()
        for palette in self.image_editor.palettes:palette.remember()
        data={'version':1,'docks':bytes(self.manager.saveState()).hex(),'geometry':bytes(self.saveGeometry()).hex(),'controls':dict(self.preferences,band_analyzer=self.analyzer.configuration())}
        # Base64 is used so QByteArray round trips without text encoding changes.
        data['docks']=base64.b64encode(bytes(self.manager.saveState())).decode();data['geometry']=base64.b64encode(bytes(self.saveGeometry())).decode()
        self.layout_path.write_text(json.dumps(data,indent=2),encoding='utf8')
    def settle_default(self):
        if not self.layout_path.exists():self.balance()
    def balance(self):
        if self.width()<1450 and self.panels['colors'].dockAreaWidget()!=self.panels['tuning'].dockAreaWidget():
            self.manager.addDockWidget(ads.CenterDockWidgetArea,self.panels['colors'],self.panels['tuning'].dockAreaWidget())
            self.panels['tuning'].setAsCurrentTab()
        for splitter in self.manager.findChildren(QSplitter):
            names=[{w.objectName() for w in splitter.widget(i).findChildren(ads.CDockWidget)} for i in range(splitter.count())]
            if splitter.orientation()==Qt.Horizontal and len(names)==3 and 'session' in names[0]:
                width=max(1100,self.width());right=400;left=235 if width>=1450 else 205;splitter.setSizes([left,width-left-right,right])
            elif splitter.orientation()==Qt.Vertical and len(names)==2 and 'preview' in names[0]:splitter.setSizes([max(350,self.height()-290),235])
            elif splitter.orientation()==Qt.Vertical and len(names)==3 and 'colors' in names[0]:splitter.setSizes([235,max(340,self.height()-535),230])
            elif splitter.orientation()==Qt.Vertical and len(names)==2 and 'tuning' in names[0] and 'monitor' in names[1]:splitter.setSizes([max(420,self.height()-300),230])
    def reset_layout(self):
        self.owner.release_preview_holds();self.manager.restoreState(self.default);self.balance();self.recover()
    def nine_panels(self):
        self.reset_layout()
        for keys,area in ((('session','sessions','presets'),ads.LeftDockWidgetArea),(('colors','tuning','monitor'),ads.RightDockWidgetArea),(('transport','analyzer','waveform'),ads.BottomDockWidgetArea)):
            anchor=None
            for key in keys:
                dock=self.panels[key];self.manager.removeDockWidget(dock)
                anchor=self.manager.addDockWidget(area if anchor is None else (ads.RightDockWidgetArea if area==ads.BottomDockWidgetArea else ads.BottomDockWidgetArea),dock,anchor)
                dock.toggleView(True)
    def recover(self):
        screens=[s.availableGeometry() for s in QApplication.screens()]
        if not screens or self.closing:return
        for window in [self,*self.manager.floatingWidgets()]:
            frame=window.frameGeometry()
            screen=max(screens,key=lambda rect:rect.intersected(frame).width()*rect.intersected(frame).height())
            width=min(window.width(),screen.width());height=min(window.height(),screen.height())
            window.resize(width,height)
            window.move(max(screen.left(),min(frame.left(),screen.right()-width+1)),max(screen.top(),min(frame.top(),screen.bottom()-height+1)))
    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Space and event.modifiers() & Qt.AltModifier:
            self.system_menu();event.accept();return
        if event.key()==Qt.Key_F1:self.help();event.accept();return
        super().keyPressEvent(event)
    def system_menu(self):
        if os.name!='nt':return
        import ctypes as c
        from ctypes import wintypes as w
        u=NativeSurface(int(self.winId()),os.getpid()).u
        u.GetSystemMenu.argtypes=[w.HWND,w.BOOL];u.GetSystemMenu.restype=w.HMENU
        u.TrackPopupMenu.argtypes=[w.HMENU,w.UINT,c.c_int,c.c_int,c.c_int,w.HWND,c.c_void_p];u.TrackPopupMenu.restype=w.UINT
        u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
        point=self.mapToGlobal(self.header.rect().bottomLeft());scale=self.devicePixelRatioF()
        command=u.TrackPopupMenu(u.GetSystemMenu(int(self.winId()),False),0x100,round(point.x()*scale),round(point.y()*scale),0,int(self.winId()),None)
        if command:u.PostMessageW(int(self.winId()),0x112,command,0)
    def nativeEvent(self,event_type,message):
        if hasattr(self,'chrome'):
            handled,result=self.chrome.native(event_type,message)
            if handled:return handled,result
        return super().nativeEvent(event_type,message)
    def changeEvent(self,event):
        super().changeEvent(event)
        if hasattr(self,'chrome') and event.type()==QEvent.WindowStateChange:self.chrome.state_changed(event)
    def moveEvent(self,event):
        super().moveEvent(event)
        if hasattr(self,'chrome'):QTimer.singleShot(0,self.chrome.remember_normal)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'chrome'):QTimer.singleShot(0,self.chrome.remember_normal)
    def eventFilter(self,watched,event):
        if self.closing:return False
        kind=event.type()
        # Global Qt layout/style events do not participate in input handling.
        # Expanded layer construction produces thousands of these; avoid window
        # ancestry and chrome/client lookups unless this filter handles the type.
        if kind not in (QEvent.ChildPolished,QEvent.MouseMove,QEvent.MouseButtonPress,QEvent.MouseButtonDblClick,QEvent.FocusIn,QEvent.WindowDeactivate,QEvent.KeyPress,QEvent.KeyRelease):return False
        if kind==QEvent.ChildPolished and isinstance(event.child(),QWidget) and event.child().window()==self:
            event.child().setMouseTracking(True)
        if hasattr(self,'chrome') and isinstance(watched,QWidget) and watched.window()==self:
            if kind==QEvent.MouseMove:self.chrome.client_hover(event)
            if kind in (QEvent.MouseButtonPress,QEvent.MouseButtonDblClick):
                if self.chrome.client_press(event,kind==QEvent.MouseButtonDblClick):return True
        if self.client is None or self.client.disconnected:return False
        if kind==QEvent.FocusIn and hasattr(self,'image_editor') and hasattr(self.image_editor,'editor_view') and hasattr(self.image_editor,'focus_pane'):
            self.image_editor.focus_pane(QApplication.focusWidget())
        if kind in (QEvent.FocusIn,QEvent.WindowDeactivate,QEvent.MouseButtonPress):
            self.safe(self.owner.release_preview_holds);return False
        if kind not in (QEvent.KeyPress,QEvent.KeyRelease):return False
        if kind==QEvent.KeyRelease and event.key()==Qt.Key_Shift:
            self.safe(self.owner.release_preview_holds);return False
        focus=QApplication.focusWidget()
        library_focus=focus is not None and self.media_library.isAncestorOf(focus)
        if library_focus and kind==QEvent.KeyPress and event.modifiers()&Qt.ControlModifier and event.key() in (Qt.Key_Z,Qt.Key_Y) and not isinstance(focus,(QLineEdit,QDoubleSpinBox,QSpinBox,QPlainTextEdit)):
            self.image_editor.history(event.key()==Qt.Key_Y or bool(event.modifiers()&Qt.ShiftModifier));self.media_library.refresh();return True
        media_focus=focus is not None and (self.composition_editor.isAncestorOf(focus) or self.image_editor.isAncestorOf(focus))
        palette_focus=focus is not None and any(p is focus.window() for p in self.image_editor.palettes)
        if (media_focus or palette_focus) and not isinstance(focus,(QLineEdit,QDoubleSpinBox,QSpinBox,QPlainTextEdit)) and QApplication.activeModalWidget() is None:
            if kind==QEvent.KeyRelease and event.key()==Qt.Key_Space:self.image_editor.canvas.space_pan=False;return True
            if kind==QEvent.KeyPress and self.image_editor.editor_key(event):return True
        if focus is not None and (self.composition_editor.isAncestorOf(focus) or self.image_editor.isAncestorOf(focus) or self.media_library.isAncestorOf(focus)):return False
        if isinstance(focus,(QLineEdit,QDoubleSpinBox,QSpinBox,QPlainTextEdit)):
            self.safe(self.owner.release_preview_holds);return False
        if isinstance(focus,QToolButton) and event.key() in (Qt.Key_Space,Qt.Key_Return,Qt.Key_Enter) and not event.modifiers() & (Qt.ControlModifier|Qt.AltModifier|Qt.ShiftModifier):return False
        audio_focus=(hasattr(self,'file_controls') and self.file_controls.isAncestorOf(focus)) if focus is not None else False
        audio_focus=audio_focus or focus in (getattr(self,'hub_source',None),getattr(self,'hub_device',None),getattr(self,'source',None),getattr(self,'hub_refresh',None))
        if audio_focus and event.key() in (Qt.Key_Space,Qt.Key_Return,Qt.Key_Enter) and not event.modifiers() & (Qt.ControlModifier|Qt.AltModifier|Qt.ShiftModifier):return False
        if event.isAutoRepeat():return False
        pressed=kind==QEvent.KeyPress;key=event.key();mods=event.modifiers()
        if focus in self.chrome.buttons and key in (Qt.Key_Space,Qt.Key_Return,Qt.Key_Enter):return False
        if isinstance(focus,(QMenu,QMenuBar)):return False
        if pressed and key==Qt.Key_Space and mods & Qt.AltModifier:self.system_menu();return True
        if key==Qt.Key_Shift:
            if mods & (Qt.ControlModifier|Qt.AltModifier):return False
            self.safe(lambda:self.owner.hold_preview('qt.keyboard',pressed));return True
        if not pressed:return False
        if key==Qt.Key_Space:self.safe(self.owner.bonk_preview);return True
        if mods & Qt.ControlModifier:
            if key in (Qt.Key_Return,Qt.Key_Enter):self.safe(self.start);return True
            if key==Qt.Key_P:self.safe(self.owner.pause_preview);return True
            if key==Qt.Key_S and mods & Qt.ShiftModifier:self.safe(self.cancel_preview);return True
        return False
    def closeEvent(self,event):
        if self.closing:event.accept();return
        if self.client is None:
            self.closing=True;self.control_cancel.set()
            if hasattr(self,'boot_timer'):self.boot_timer.stop()
            self.operations.shutdown(wait=False,cancel_futures=True);event.accept();return
        if not self.image_editor.resolve_pending():event.ignore();return
        if json.dumps(self.owner.values(),sort_keys=True)!=self.saved_art or self.client.snapshot.get('tuning_dirty'):
            answer=QMessageBox.question(self,'Unsaved artistic settings','Save the session and destination-bound tuning drafts before closing? Save keeps drafts in the session; Save Authored remains a separate explicit action.',QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel)
            if answer==QMessageBox.Cancel:event.ignore();return
            if answer==QMessageBox.Save:
                self.safe(self.save_session)
                if json.dumps(self.owner.values(),sort_keys=True)!=self.saved_art or self.client.snapshot.get('tuning_dirty'):event.ignore();return
        raster=self.client.snapshot.get('media_control',{}).get('raster',{})
        if raster.get('pending') or raster.get('failures') or raster.get('retained_checkpoints'):
            self.statusBar().showMessage('Accepted work not secured. Wait, retry persistence, or Save As/recovery export before closing.');event.ignore();return
        self.closing=True;self.timer.stop();self.analyzer_timer.stop()
        try:
            try:self.save_layout()
            except OSError as exc:print('Layout was not saved:',exc,file=sys.stderr)
            self.cancel_attach=True;self.pending_operation=None
            self.owner.release_preview_holds();self.waveform.close_pool();self.image_editor.close_resources();self.media_library.close_resources()
            def cleanup():
                try:self.client.close(force=self.client.disconnected or self.starting)
                except Exception as exc:self.client.close(force=True);print('Close cleanup:',exc,file=sys.stderr)
            if self.async_bootstrap:self.shutdown_future=self.operations.submit(cleanup)
            else:cleanup()
            self.operations.shutdown(wait=False,cancel_futures=not self.async_bootstrap)
        except Exception as exc:
            self.client.close(force=True);print('Close cleanup:',exc,file=sys.stderr)
        event.accept()


def main():
    dpi_awareness();app=QApplication(sys.argv);app.setApplicationName('ZeraWave Qt Studio proof')
    shell=Shell(async_bootstrap=True);shell.show();sys.exit(app.exec())

if __name__=='__main__':main()
