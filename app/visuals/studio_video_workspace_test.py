"""Synthetic Qt/actual-owner panel lifecycles; not physical docking evidence."""
from pathlib import Path
from copy import deepcopy
import sys,os,time,json,traceback
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import Qt
from studio_qt import Shell
app=QApplication([]);shell=None;checks=[]
def pump():app.processEvents();time.sleep(.002)
def wait(fn,seconds=25):
 deadline=time.perf_counter()+seconds
 while time.perf_counter()<deadline:
  pump()
  if fn():return
 raise AssertionError('Timed out '+(w.notice.text() if shell else 'starting'))
try:
 shell=Shell(layout_path=out/'layout.json',control_log_path=out/'owner.log');shell.resize(1800,1000);shell.show();legacy=deepcopy(shell.owner.values());w=shell.project_workspace;v=shell.video_panels;w.open(str(Path(sys.argv[2]).resolve()));wait(lambda:not w.pending and w.state().get('document') is not None);wait(lambda:w.preview.presented is not None);before=deepcopy(w.document());transport=deepcopy(w.transport_state());assert v.active
 assert v.stack.count()==2 and v.stack.indexOf(shell.media_library)==1
 v.scope.setCurrentIndex(1);pump();assert v.stack.currentWidget() is shell.media_library and shell.media_library.isVisible();v.scope.setCurrentIndex(0);pump();assert v.stack.currentWidget() is w.pages['media'][0]
 checks.append('Real Library widget ownership survives ADS transfer; both visible scope choices select the intended existing surface')
 assert all(k in shell.panels for k in v.keys);assert w.preview.parentWidget() is not w.timeline.parentWidget();checks.append('Separate ADS panel identities and shared existing preview/controller; real owner open and CPU preview')
 for key in ('timeline','project_properties','project_mixer','project_preview'):
  shell.panels[key].toggleView(False);pump();assert w.document()==before;shell.panels[key].toggleView(True);pump()
 checks.append('Closing/hiding independent panels preserves exact accepted document')
 shell.reset_layout();pump();assert w.document()==before and w.transport_state()['frame']==transport['frame'];v.save();wait(lambda:v.video_path.exists() and v.layout_writer.future is None);v.studio();assert not v.active;v.activate();assert v.active;checks.append('Video reset/save/Studio/restore leaves document and playhead intact')
 shell.resize(1280,720);pump();v.save();wait(lambda:v.layout_writer.future is None);v.studio();w.timeline.compact=None;w.timeline.header_width=180;w.timeline.header_column.setFixedWidth(180);w.timeline.header_scroll.setFixedWidth(180);v.activate();assert w.timeline.header_width==140 and w.timeline.canvas.row_height==48;checks.append('Compact saved-layout restore applies140px track headers immediately without an extra resize; retained custom non-default lane heights remain supported')
 v.scope.setCurrentIndex(0);v.show_source();wait(lambda:v.source.asset is not None and v.source.preview is not None);wait(lambda:v.source.preview.presented is not None);assert shell.panels['source_preview'].height()>=250;v.source.seek.setValue(5);wait(lambda:v.source.preview.presented is not None and v.source.preview.presented[-1]==5);v.source.in_box.setValue(2);v.source.out_box.setValue(20);v.source.mark_range();wait(lambda:v.source.range==[2,20]);assert w.document()==before and w.transport_state()['frame']==transport['frame'];shell.panels['source_preview'].toggleView(False);wait(lambda:not v.source.retiring);v.show_source();wait(lambda:v.source.preview is not None and v.source.preview.presented is not None);assert v.source.range==[2,20] and v.source.frame==5;v.fullscreen();pump();assert w.preview.isVisible() and not w.preview.isHidden();v.fullscreen();pump();assert w.document()==before and w.transport_state()['frame']==transport['frame'];shell.panels['source_preview'].toggleView(False);wait(lambda:not v.source.retiring);checks.append('Substantial Source Preview/frame seek/In-Out survive hide/return for same source, retire workers and do not edit project/program transport')
 from PySide6.QtTest import QTest
 from PySide6.QtWidgets import QLineEdit
 actions=[];bonks=[];holds=[];transport_fn=w.transport;bonk_fn=shell.owner.bonk_preview;hold_fn=shell.owner.hold_preview
 w.transport=lambda action,frame=None,target='program',**kw:actions.append((action,frame,target));shell.owner.bonk_preview=lambda:bonks.append(True);shell.owner.hold_preview=lambda *args:holds.append(args)
 try:
  shell.panels['project_preview'].toggleView(True);shell.panels['project_preview'].setAsCurrentTab();w.preview.setFocus();pump();QTest.keyClick(w.preview,Qt.Key_Space);assert actions==[('play',None,'program')] and not bonks
  actions.clear();shell.panels['timeline'].toggleView(True);w.timeline.canvas.setFocus();pump();QTest.keyClick(w.timeline.canvas,Qt.Key_Space);assert actions==[('play',None,'program')] and not bonks
  actions.clear();v.source.setFocusPolicy(Qt.StrongFocus);shell.panels['source_preview'].toggleView(True);shell.panels['source_preview'].setAsCurrentTab();v.source.setFocus();pump();QTest.keyClick(v.source,Qt.Key_Space);QTest.keyClick(v.source,Qt.Key_Shift);assert actions==[('play',None,'source')] and not bonks and not holds;actions.clear()
  field=QLineEdit();w.preview.layout_.addWidget(field);shell.panels['project_preview'].setAsCurrentTab();field.setFocus();pump();QTest.keyClicks(field,'normal typing ');assert field.text()=='normal typing ' and not actions and not bonks;w.preview.layout_.removeWidget(field);field.deleteLater()
 finally:w.transport=transport_fn;shell.owner.bonk_preview=bonk_fn;shell.owner.hold_preview=hold_fn
 checks.append('Independent preview/timeline Space routes once to shared transport; Source keys and normal text cannot trigger legacy BONK/Hold or project edits')
 from types import SimpleNamespace
 from studio_video_workspace import TrackMixer
 from PySide6.QtWidgets import QDoubleSpinBox
 submitted=[]
 for value in (1.,.1234567,.0004):
  doc={'tracks':[dict(id='1'*32,kind='audio',name='Precision',order=0,audio=dict(gain=value,mute=False))]}
  fake=SimpleNamespace(state=lambda:dict(document=doc,epoch='precision',revision=0),binding=lambda:{},pending=None,transport_state=lambda:dict(generation=0,active=False,playing=False),client=SimpleNamespace(snapshot={}),shell=SimpleNamespace(safe=lambda fn:fn()),batch=lambda *args:submitted.append(args),timeline=SimpleNamespace(quick_track=lambda kind:None))
  mixer=TrackMixer(fake);mixer.refresh();box=mixer.strips['1'*32].db;box.editingFinished.emit();assert not submitted
  box.setValue(-6.);box.editingFinished.emit();assert len(submitted)==1 and abs(submitted[-1][1][0]['values']['gain']-10**(-6/20))<1e-8;submitted.clear();mixer.close_resources();mixer.close();mixer.deleteLater();pump()
 checks.append('Untouched mixer values retain full authoritative precision, including sub-display nonzero gain; a deliberate dB change submits the expected linear gain')
 from studio_video_workspace import LayoutWriter
 import stat
 protected=out/'protected-layout.json';protected.write_text('prior good layout','utf8');writer=LayoutWriter()
 try:
  os.chmod(protected,stat.S_IREAD);writer.offer(protected,dict(replacement='must fail'));wait(lambda:(writer.poll(),writer.future is None)[1]);assert writer.error and protected.read_text()=='prior good layout'
  os.chmod(protected,stat.S_IWRITE);writer.offer(protected,dict(recovered=True));wait(lambda:(writer.poll(),writer.future is None)[1]);assert not writer.error and json.loads(protected.read_text())==dict(recovered=True)
 finally:
  os.chmod(protected,stat.S_IWRITE);writer.close();wait(writer.exited)
 checks.append('Actual readonly-target layout write failure retains prior good bytes, reports failure, then recovers on same bounded worker and exits')
 assert shell.owner.values()==legacy;checks.append('Exact preexisting Studio/world/artistic values survive video/source/layout operations')
 shell.close();wait(lambda:shell.closing,40);assert w.exited() and shell.client.process.returncode==0 and shell.client.protocol_error_count==0;checks.append('Normal owned close waits for actual source/media/owner retirement without output duplication')
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,protocol_errors=0),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if shell and not shell.closing:
  w.close_resources();wait(lambda:w.exited(),10);shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
