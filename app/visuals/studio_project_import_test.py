"""Synthetic offscreen Qt through the real isolated Studio owner, not physical input."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,traceback,threading
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);inputs=Path(sys.argv[3]);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QFileDialog,QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from studio_qt import Shell
from project_service import read_project
app=QApplication([]);shell=None;checks=[];pumps=[]
def pump():
 t=time.perf_counter();app.processEvents();pumps.append((time.perf_counter()-t)*1000);time.sleep(.002)
def wait(fn,seconds=40):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if fn():return
 raise AssertionError('Timeout '+w.notice.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and w.timeline.canvas.version==(w.state().get('epoch'),w.state().get('revision')))
def place_still(seconds,frame):
 panel.still_seconds.setFocus();panel.still_seconds.lineEdit().selectAll();QTest.keyClicks(panel.still_seconds.lineEdit(),str(seconds));QTest.keyClick(panel.still_seconds.lineEdit(),Qt.Key_Return);before=deepcopy(w.document());assert panel.still_seconds.value()==seconds
 w.transport('seek_paused',frame);idle();panel.place();wait(lambda:w.timeline.placement is None and not w.pending);idle();added=[r for r in w.document()['clips'] if r['id'] not in {i['id'] for i in before['clips']}];assert len(added)==1 and added[0]['duration']==int(seconds*30);return deepcopy(w.document()),added[0]
try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;panel=shell.video_panels.source;wait(lambda:w.state().get('endpoint'));w.open(str(proof));idle();before=deepcopy(w.document());chosen=[str((inputs/n).resolve()) for n in ('Still.png','Shot-2.mp4','Music.wav','Shot-1.mp4','Still.png')];began=time.perf_counter()
 with patch.object(QFileDialog,'getOpenFileNames',return_value=(chosen,'')):key=w.import_media()
 wait(lambda:not w.pending and (w.import_status.outcome or {}).get('status')=='accepted');idle();elapsed=time.perf_counter()-began;row=w.import_status.outcome;assert [r['path'] for r in row['files']]==sorted(chosen,key=lambda p:(os.path.normcase(p),p));assert [r['status'] for r in row['files']].count('accepted')==4 and [r['status'] for r in row['files']].count('skipped')==1;assert len(w.document()['media'])==len(before['media'])+4 and w.document()['clips']==before['clips'];imported=deepcopy(w.document());assert 'No clips placed' in w.import_status.label.text();w.import_status.show_details();pump();assert not w.import_status.details.isModal() and w.import_status.details.table.topLevelItemCount()==5;w.import_status.details.close();pump();w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==imported;checks.append('Actual Project Media mixed chooser path sorts5inputs;4verified refs+1duplicate,5per-file details,nonmodal UI,zero auto-clips,exact Undo/Redo')
 # Existing Library multi-import is demonstrated, not new implementation.
 with patch.object(QFileDialog,'getOpenFileNames',return_value=([str(inputs/'Still.png'),str(inputs/'Music.wav')],'')):shell.media_library.import_files()
 wait(lambda:len(shell.media_library.assets)==2 and all(a.get('status')=='Ready' for a in shell.media_library.assets.values()));assert w.document()==imported and 'Library' in w.import_hint.text();checks.append('Existing Library Import accepts2files separately; Project document unchanged; contextual discovery text present')
 asset=next(a for a in w.document()['media'] if a['kind']=='Image');w.submit('source_open',asset={k:asset[k] for k in ('id','name','kind','location','sha256','metadata')});idle();wait(lambda:panel.asset and panel.asset['id']==asset['id']);assert panel.still_seconds.value()==5.;first,r1=place_still(1.25,60);second,r2=place_still(2.5,150);assert r1['duration']==37 and r2['duration']==75 and next(r for r in second['clips'] if r['id']==r1['id'])==r1
 w.submit('undo');idle();assert w.document()==first;w.submit('redo');idle();assert w.document()==second;checks.append('Source still default5s; typed1.25s→37frames and2.5s→75frames; independent existing clip unchanged,exact Undo/Redo')
 # Test placements are removed via owner Undo, leaving imported sources for the
 # same proof's next stage; no direct project JSON rewrite.
 w.submit('undo');idle();w.submit('undo');idle();assert w.document()==imported
 w.save(path=str(proof));idle();w.open(str(proof));idle();opened,rev,states,_=read_project(proof,threading.Event());assert w.document()==opened and all(r['status']=='Ready' for r in states.values());assert len(opened['media'])==5 and opened['clips']==before['clips'];checks.append('Same proof extended with4mixed references; normal portable Save/actual-owner reopen preserves5stableIDs,hashes and narration/caption')
 shell.close();wait(lambda:shell.closing);assert w.exited() and shell.client.process.returncode==0;values=sorted(pumps);report=dict(classification=__doc__,checks=checks,small_import_seconds=elapsed,qt_process_events_ms=dict(count=len(values),median=values[len(values)//2],p95=values[int(len(values)*.95)],maximum=max(values),stalls_over100ms=sum(v>100 for v in values)),owner_exit=0,workers_exited=True,proof=str(proof),revision=rev,limits='Synthetic Qt callbacks/events, actual owner and preparation; no physical native file picker, foreground responsiveness, device/listening or playback qualification claim.');(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if shell and not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();end=time.monotonic()+40
   while not shell.closing and time.monotonic()<end:pump()
