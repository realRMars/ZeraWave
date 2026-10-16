"""Independent Video Editing panels over Studio's existing project authority."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import json,hashlib,threading,time,uuid,base64
from PySide6.QtCore import Qt,QObject,QEvent,QTimer,QByteArray
from PySide6.QtGui import QAction,QKeySequence
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,
 QPushButton,QComboBox,QStackedWidget,QSplitter,QLineEdit,QPlainTextEdit,QTextEdit,
 QAbstractSpinBox,QSlider,QSpinBox,QFormLayout,QScrollArea,QDoubleSpinBox,QCheckBox,QToolBar,QMenu,QHeaderView)
import PySide6QtAds as ads
from video_project import create,apply,rational,duration

def clock_text(frame,fps):
 value=Fraction(frame)/rational(fps);milliseconds=value.numerator*1000//value.denominator;seconds,ms=divmod(milliseconds,1000);minutes,sec=divmod(seconds,60);hours,minute=divmod(minutes,60)
 return f'{hours:02}:{minute:02}:{sec:02}.{ms:03}'

from studio_project_controls import MonitorTransport as ProgramTransport


def inspect_source(asset,cancel):
 """Read-only derived preview input. Never imports/edits the project or Library."""
 from media_registry import inspect
 from project_media import source_metadata
 path=Path(asset.get('path') or asset['location']['path']);h=hashlib.sha256()
 with path.open('rb') as f:
  while block:=f.read(1024*1024):
   if cancel.is_set():raise InterruptedError('Source view superseded')
   h.update(block)
 record=inspect(str(path),cancel);kind={'Images':'Image','Video':'Video','Audio':'Audio'}.get(record['kind'])
 if kind is None:raise ValueError('This source type has no video-editor source view.')
 if asset.get('sha256') and asset['sha256']!=h.hexdigest():raise ValueError('Source changed; relink deliberately before viewing it.')
 meta=record['metadata']
 if kind=='Video':meta=dict(meta,**source_metadata(path,cancel))
 return dict(id=asset['id'],name=asset['name'],kind=kind,metadata=meta,sha256=h.hexdigest(),location=dict(kind='external',path=str(path.resolve())))

from studio_project_source import SourcePanel


from studio_project_mixer import TrackMixer


def write_layout(path,data):
 """One immutable settings snapshot; preserve the last file on failed replacement."""
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  temp.write_text(json.dumps(data),'utf8')
  for attempt in range(4):
   try:temp.replace(path);return
   except PermissionError:
    if attempt==3:raise
    time.sleep((.02,.08,.2)[attempt])
 finally:
  try:temp.unlink(missing_ok=True)
  except OSError:pass

class LayoutWriter:
 """One worker plus one latest settings snapshot, independent of artwork saves."""
 def __init__(self):self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Video layout');self.future=None;self.next=None;self.error='';self.stopped=False
 def offer(self,path,data):
  if self.stopped:return
  self.next=(path,data);self.poll()
 def poll(self):
  if self.future and self.future.done():
   try:self.future.result();self.error=''
   except Exception as exc:self.error=str(exc)
   self.future=None
  if self.future is None and self.next is not None:
   path,data=self.next;self.next=None;self.future=self.pool.submit(write_layout,path,data)
 def close(self):self.poll();self.stopped=True
 def exited(self):
  self.poll()
  if self.future is not None or self.next is not None:return False
  if self.stopped:self.pool.shutdown(wait=False)
  return not self.stopped or all(not t.is_alive() for t in self.pool._threads)


class PreviewWindow(QMainWindow):
 """Temporary desktop host for the existing view, never another document/player."""
 def __init__(self,panels):
  super().__init__();self.panels=panels;self.returning=False;self.setObjectName('project-fullscreen-window');self.setWindowTitle('ZeraWave — Project Preview');self.setStyleSheet(panels.shell.styleSheet())
 def keep_composited(self):
  # Qt documents WS_BORDER for fullscreen OpenGL top levels on Windows:
  # retain DWM composition and usable sibling windows/dialogs. No mode switch.
  if QApplication.platformName()!='windows' or not self.effectiveWinId():return
  from window_host import windows
  user=windows();handle=int(self.effectiveWinId());style=user.GetWindowLongPtrW(handle,-16)
  if not style&0x00800000:user.SetWindowLongPtrW(handle,-16,style|0x00800000)
 def event(self,event):
  result=super().event(event)
  if event.type()==QEvent.WinIdChange:self.keep_composited()
  return result
 def closeEvent(self,event):
  if self.returning:event.accept();return
  event.ignore();self.panels.fullscreen()


class VideoPanels(QObject):
 """Moves existing views between ADS areas; one document, selection and audio owner."""
 def __init__(self,w):
  super().__init__(w);self.w=w;self.shell=w.shell;self.active=False;self.fullscreen_state=None;self.fullscreen_window=None;self.video_path=self.shell.layout_path.with_name(self.shell.layout_path.stem+'-video.json');self.studio_state=None;self.mode='Project Media';self.source=SourcePanel(w);self.mixer=TrackMixer(w);self.property_version=None;self.layout_writer=LayoutWriter();self.saved_layout=None;self.preset='editing'
  # The old data views remain optional. Remove only the embedded preview/timeline.
  w.layout().removeWidget(w.tabs);self.data=w.tabs;self.data.setParent(None)
  splitter=w.preview.parentWidget();splitter.hide();w.preview.setParent(None);w.timeline.setParent(None);w.layout().removeWidget(splitter);splitter.deleteLater()
  media_page=w.pages['media'][0];self.data.removeTab(self.data.indexOf(media_page));self.shell.panels['media'].takeWidget();library=QWidget();body=QVBoxLayout(library);body.setContentsMargins(4,4,4,4);self.scope=QComboBox();self.scope.addItems(['Project Media','Library']);self.scope.setAccessibleName('Media scope');body.addWidget(self.scope);self.stack=QStackedWidget();self.stack.addWidget(media_page);self.stack.addWidget(self.shell.media_library);body.addWidget(self.stack,1);self.scope.currentIndexChanged.connect(self.stack.setCurrentIndex);self.shell.panels['media'].setWidget(library)
  for button in media_page.findChildren(QPushButton):button.hide()
  tools=QHBoxLayout();media_page.layout().insertLayout(0,tools);button=QPushButton('Import…');button.clicked.connect(lambda:self.shell.safe(w.import_media));tools.addWidget(button);w.media_type=QComboBox();w.media_type.addItems(['All types','Video','Audio','Image']);w.media_type.currentTextChanged.connect(w.filter_media);tools.addWidget(w.media_type,1);tree=w.trees['media'];tree.setColumnHidden(3,True);tree.setColumnHidden(2,True);tree.setContextMenuPolicy(Qt.CustomContextMenu)
  def media_menu(pos):
   menu=QMenu(tree)
   for label,fn in [('Open in Source',self.show_source),('Place source range',w.place),('Relink…',w.relink),('Remove reference',w.remove_media)]:menu.addAction(label,lambda checked=False,fn=fn:self.shell.safe(fn))
   menu.exec(tree.viewport().mapToGlobal(pos))
  tree.customContextMenuRequested.connect(media_menu);tree.header().setStretchLastSection(False);tree.header().setSectionResizeMode(0,QHeaderView.Stretch);tree.header().setSectionResizeMode(1,QHeaderView.ResizeToContents)
  from studio_project_inspector import Inspector
  inspector=Inspector(w);self.inspector=inspector;self.selection=inspector.heading;self.inspector_actions=[]
  center=self.shell.panels['project'].dockAreaWidget();self.shell.dock('project_preview','Program',w.preview,ads.CenterDockWidgetArea,center);self.shell.dock('timeline','Timeline',w.timeline,ads.BottomDockWidgetArea,self.shell.panels['project_preview'].dockAreaWidget());self.shell.dock('project_properties','Inspector',inspector,ads.RightDockWidgetArea,self.shell.panels['project_preview'].dockAreaWidget());self.shell.dock('project_mixer','Audio Mixer',self.mixer,ads.CenterDockWidgetArea,self.shell.panels['project_properties'].dockAreaWidget());self.shell.dock('source_preview','Source',self.source,ads.CenterDockWidgetArea,self.shell.panels['media'].dockAreaWidget());self.shell.dock('project_data','Project data / captions',self.data,ads.CenterDockWidgetArea,self.shell.panels['project'].dockAreaWidget())
  # GL views and Timeline manage their own native viewport/scrolling. Avoid
  # ADS's automatic scroll viewport between the GL host and its dock window.
  for key in ('project_preview','source_preview','timeline','project_properties','media','project_mixer'):
   dock=self.shell.panels[key];body=dock.takeWidget();dock.setWidget(body,ads.CDockWidget.ForceNoScrollArea)
  for key in self.keys:self.shell.panels[key].toggleView(False)
  for key,tree in w.trees.items():tree.itemSelectionChanged.connect(self.refresh)
  w.preview.status.hide();self.preview_transport=ProgramTransport(w);w.preview.layout_.addWidget(self.preview_transport);w.preview.setFocusPolicy(Qt.StrongFocus);self.source.timer.timeout.connect(self.refresh);QApplication.instance().installEventFilter(self)
  self.shell.panels['project_preview'].topLevelChanged.connect(lambda floating:QTimer.singleShot(0,self.show_floating_preview) if floating else None)
  app=QApplication.instance();app.screenRemoved.connect(lambda *_:QTimer.singleShot(0,self.shell.recover));self.refresh()
 keys=('project_preview','timeline','project_properties','project_mixer','source_preview','project_data')
 def show_floating_preview(self):
  dock=self.shell.panels['project_preview']
  if dock.isFloating() and not dock.isClosed():dock.setAsCurrentTab();self.w.preview.show();self.w.preview.rehost();self.w.preview.view.update()
 def show_source(self):
  if self.scope.currentIndex()==0:asset=self.w.selected('media')
  else:
   asset=self.shell.media_library.assets.get(self.shell.media_library.selected)
   if not asset:raise ValueError('Select a source in Library first.')
  self.open_source(asset)
 def open_source(self,asset):
  dock=self.shell.panels['source_preview'];dock.toggleView(True);dock.setAsCurrentTab();self.preview_transport.set_target('source');self.source.load(asset)
 def refresh(self):
  self.layout_writer.poll()
  if self.active:
   pending=bool(self.shell.client.snapshot.get('media_library',{}).get('pending'))
   for button in self.shell.media_library.findChildren(QPushButton):
    if button.text()=='Cancel pending imports':button.setVisible(pending)
  if self.layout_writer.error:self.w.notice.setText("Video layout could not be saved; previous layout retained. "+self.layout_writer.error)
  if self.w.preview.closed:return
  self.preview_transport.refresh();self.mixer.refresh();self.inspector.refresh();self.w.preview.setToolTip(self.w.preview.status.text()+'\n'+self.w.preview.status.toolTip())

  for splitter in self.shell.manager.findChildren(QSplitter):splitter.setHandleWidth(8)
 def activate(self,restore=True):
  if self.active:
   if self.fullscreen_state is not None:self.fullscreen()
   self.shell.panels['project_preview'].toggleView(True);self.shell.panels['timeline'].toggleView(True);return
  self.studio_state=QByteArray(self.shell.manager.saveState());self.active=True;self.shell.preferences['workspace_mode']='video'
  if restore and (self.saved_layout is not None or self.video_path.exists()):
   try:
    data=self.saved_layout or json.loads(self.video_path.read_text());assert data['version']==1
    scope=data.get('media_scope',0)
    if type(scope) is not int or scope not in (0,1):raise ValueError('Unknown media scope in saved layout')
    if not self.shell.manager.restoreState(QByteArray(base64.b64decode(data['docks'],validate=True))):raise ValueError('ADS rejected the saved layout')
    self.preset=data.get('preset','editing');self.preview_transport.set_target(data.get('monitor','program'));self.compact_library(True);self.scope.setCurrentIndex(scope);self.w.timeline.restore_view(data.get('timeline',{}));self.w.timeline.set_compact(self.shell.width()<1500);self.shell.recover();return
   except Exception as exc:self.w.notice.setText('Saved Video Editing layout unavailable; using default. '+str(exc))
  self.default_layout()
 def default_layout(self,preset=None):
  if preset is not None:self.preset=preset
  if self.fullscreen_state is not None:self.fullscreen()
  manager=self.shell.manager
  for dock in self.shell.panels.values():dock.toggleView(False)
  preview=self.shell.panels['project_preview'];upper=manager.addDockWidget(ads.CenterDockWidgetArea,preview)
  left=manager.addDockWidget(ads.LeftDockWidgetArea,self.shell.panels['media'],upper);manager.addDockWidget(ads.CenterDockWidgetArea,self.shell.panels['source_preview'],left)
  right=manager.addDockWidget(ads.RightDockWidgetArea,self.shell.panels['project_properties'],preview.dockAreaWidget());manager.addDockWidget(ads.CenterDockWidgetArea,self.shell.panels['project_mixer'],right)
  # No relative area: the Timeline spans the entire root below ALL upper docks.
  manager.addDockWidget(ads.BottomDockWidgetArea,self.shell.panels['timeline'])
  for key in ('media','project_preview','timeline','project_properties'):self.shell.panels[key].toggleView(True)
  self.shell.panels['source_preview'].toggleView(False);self.shell.panels['project_mixer'].toggleView(False)
  if self.preset=='audio':
   self.shell.panels['media'].toggleView(False);self.shell.panels['project_properties'].toggleView(False);self.shell.panels['project_mixer'].toggleView(True);self.shell.panels['project_mixer'].setAsCurrentTab()
  else:self.shell.panels['media'].setAsCurrentTab();self.shell.panels['project_properties'].setAsCurrentTab()
  for key in ('media','project_preview','timeline','project_properties','project_mixer','source_preview'):
   if not self.shell.panels[key].isClosed():self.shell.panels[key].tabWidget().show()
  for key,size in {'media':(180,150),'project_preview':(320,240),'timeline':(400,220),'source_preview':(180,220),'project_properties':(180,170),'project_mixer':(220,170)}.items():self.shell.panels[key].setMinimumSize(*size)
  preview.setAsCurrentTab();self.preview_transport.set_target('program');self.scope.setCurrentIndex(0);self.compact_library(True);QTimer.singleShot(0,self.balance);QTimer.singleShot(50,self.balance)
 def editing(self):
  if not self.active:self.activate(False)
  self.default_layout('editing')
 def audio_mixing(self):
  if not self.active:self.activate(False)
  self.default_layout('audio')
 def compact_library(self,enabled):
  library=self.shell.media_library
  for widget in [library.name,library.detail,library.audio,*library.assign,library.relink,library.refresh_button,library.remove,library.collection_button]:widget.setVisible(not enabled)
  library.detail.setToolTip(library.detail.text())
  for button in library.findChildren(QPushButton):
   if button.text()=='Cancel pending imports':button.setVisible(not enabled or bool(self.shell.client.snapshot.get('media_library',{}).get('pending')))
 def balance(self):
  small=self.shell.width()<1500;side=220 if small else 300;self.w.timeline.set_compact(small)
  for splitter in self.shell.manager.findChildren(QSplitter):
   splitter.setHandleWidth(6);names=[{d.objectName() for d in splitter.widget(i).findChildren(ads.CDockWidget) if not d.isClosed()} for i in range(splitter.count())]
   if sum(bool(n) for n in names)<2:continue
   total=splitter.width() if splitter.orientation()==Qt.Horizontal else splitter.height()
   if splitter.orientation()==Qt.Vertical:
    timeline=290 if small else 440;sizes=[timeline if n=={'timeline'} else max(240,total-timeline-6) if n else 0 for n in names]
   else:
    sizes=[0 if not n else max(280,total*.6) if self.preset=='audio' and n<={'project_mixer','project_properties'} else max(320,total*.4) if self.preset=='audio' and 'project_preview' in n else side if n<={'media','source_preview'} or n<={'project_properties','project_mixer'} else max(320,total-side*2) for n in names]
   splitter.setSizes([round(n) for n in sizes])
 def save(self):
  if not self.active:return
  state=self.fullscreen_state or QByteArray(self.shell.manager.saveState());self.saved_layout=dict(version=1,media_scope=self.scope.currentIndex(),timeline=self.w.timeline.view_settings(),preset=self.preset,monitor=self.preview_transport.target,docks=base64.b64encode(bytes(state)).decode());self.layout_writer.offer(self.video_path,self.saved_layout)
 def studio(self):
  self.save()
  if self.fullscreen_state:self.fullscreen()
  if self.studio_state:self.shell.manager.restoreState(self.studio_state)
  self.active=False;self.compact_library(False);self.scope.setCurrentIndex(1);self.shell.preferences['workspace_mode']='studio';self.shell.recover()
 def fullscreen(self):
  dock=self.shell.panels['project_preview']
  if self.fullscreen_state is not None:
   state=self.fullscreen_state;window=self.fullscreen_window;self.fullscreen_state=None;self.fullscreen_window=None
   view=window.takeCentralWidget();dock.setWidget(view,ads.CDockWidget.ForceNoScrollArea);window.returning=True;window.hide();window.close();window.deleteLater();self.shell.manager.restoreState(state);self.shell.recover();return
  if not self.active:self.activate()
  self.preview_transport.set_target('program')
  self.fullscreen_state=QByteArray(self.shell.manager.saveState());window=PreviewWindow(self);self.fullscreen_window=window;view=dock.takeWidget();dock.toggleView(False);window.setCentralWidget(view);window.resize(max(900,self.shell.width()),max(600,self.shell.height()));window.showFullScreen();window.keep_composited();view.show();view.setFocus()
 def eventFilter(self,obj,event):
  if event.type()==QEvent.Resize and obj is self.shell and self.active:
   self.w.timeline.set_compact(self.shell.width()<1500)
  if event.type() in (QEvent.MouseButtonPress,QEvent.FocusIn) and self.active and isinstance(obj,QWidget):
   if obj is self.source or self.source.isAncestorOf(obj):self.preview_transport.set_target('source')
   elif obj is self.w.preview.view or obj is getattr(self.w.preview,'handles',None) or obj is self.w.timeline.canvas:self.preview_transport.set_target('program')
  if event.type()==QEvent.KeyPress and self.active and QApplication.activeModalWidget() is None and QApplication.activePopupWidget() is None:
   if event.key()==Qt.Key_F11:self.fullscreen();return True
   if event.key()==Qt.Key_Escape and self.fullscreen_state is not None:self.w.timeline.canvas.cancel_gesture();self.fullscreen();return True
   focus=QApplication.focusWidget()
   editor=focus and any(body is focus or body.isAncestorOf(focus) for body in (self.w.preview,self.w.timeline,self.source))
   if editor and not isinstance(focus,(QLineEdit,QPlainTextEdit,QTextEdit,QAbstractSpinBox)):
    if event.key()==Qt.Key_Space and not event.isAutoRepeat():self.shell.safe(lambda:self.preview_transport.command('toggle'));return True
    if event.key() in (Qt.Key_BracketLeft,Qt.Key_BracketRight):self.shell.safe(lambda:self.preview_transport.command('range_in' if event.key()==Qt.Key_BracketLeft else 'range_out'));return True
  return False
 def close_resources(self):
  try:
   self.save()
   if self.fullscreen_state is not None:self.fullscreen()
  finally:self.layout_writer.close();self.source.close_resources();self.mixer.close_resources()
 def exited(self):return self.layout_writer.exited() and self.source.exited()
