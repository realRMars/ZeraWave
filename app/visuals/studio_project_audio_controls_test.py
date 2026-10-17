"""Synthetic Qt typing/wheel through actual isolated owner; no device or physical UI claim."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,uuid,traceback,threading,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);source=Path(sys.argv[3]);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QPoint,QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_service import prepare_changes,read_project
from project_audio_timing import natural_frames
app=QApplication([]);shell=None;checks=[];steps=[];ns=uuid.uuid5(uuid.NAMESPACE_URL,'zerawave-human-agent-workflow-proof-v1');key=lambda cat,name:uuid.uuid5(ns,cat+':'+name).hex

def pump():app.processEvents();time.sleep(.002)
def wait(fn,seconds=35):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if fn():return
 raise AssertionError('Timeout '+w.notice.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and c.version==(w.state().get('epoch'),w.state().get('revision')))
def clip():return next(r for r in w.document()['clips'] if r['id']==cid)
def type_value(field,value):
 box=ins.fields[field];box.setFocus();box.lineEdit().selectAll();QTest.keyClicks(box.lineEdit(),value);QTest.keyClick(box.lineEdit(),Qt.Key_Return);idle();actual=deepcopy(clip()['audio']);steps.append(dict(field=field,input=value,actual=actual,revision=w.state()['revision'],notice=w.notice.text()));(out/'UI_STEPS.json').write_text(json.dumps(steps,indent=2),encoding='utf8');return actual

try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;c=w.timeline.canvas;ins=shell.video_panels.inspector;wait(lambda:w.state().get('endpoint'));w.submit('new',name='Human and agent workflow proof',settings=dict(width=1920,height=1080,fps=[30,1]));idle()
 a=prepare_changes([dict(op='media.add',id=key('media','narration'),name='Original narration tail',kind='Audio',location=dict(kind='external',path=str(source.resolve())),provenance={})],None,threading.Event())[0];cid=key('clips','narration');changes=[a,dict(op='track.add',id=key('tracks','narration'),kind='audio',name='Narration'),dict(op='track.add',id=key('tracks','captions'),kind='graphics',name='Captions'),dict(op='clip.add',id=cid,asset=a['id'],track=key('tracks','narration'),start=0,duration=natural_frames(a['metadata'],[30,1]),pad_end='silence'),dict(op='caption.add',id=key('captions','proof'),track=key('tracks','captions'),start=0,duration=360,text='Editable workflow proof')];w.batch('Proof: original narration and caption',changes);idle();c.select('clips',cid);ins.version=None;ins.refresh();before=deepcopy(w.document());revision=w.state()['revision']
 assert type_value('fade_in','3')['fade_in']==3 and type(clip()['audio']['fade_in']) is int;after=deepcopy(w.document());assert w.state()['revision']==revision+1;w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==after
 assert type_value('fade_out','4')['fade_out']==4 and type(clip()['audio']['fade_out']) is int
 box=ins.fields['fade_in'];w.notice.setFocus();pump();event=QWheelEvent(QPointF(10,10),box.mapToGlobal(QPoint(10,10)),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False);QApplication.sendEvent(box,event);until=time.monotonic()+.4
 while time.monotonic()<until:pump()
 idle();assert clip()['audio']['fade_in']==4 and type(clip()['audio']['fade_in']) is int;checks.append('Fade typing and unfocused wheel accepted as integers; exact Undo/Redo')
 assert type_value('gain','0.734')['gain']==.734;assert abs(type_value('pan','-12.3')['pan']+.123)<1e-12;checks.append('Fractional gain/pan retained within binary floating-point representation')
 # Pin the first edit, then advance owner revision before completing it.
 box=ins.fields['fade_in'];box.setFocus();box.lineEdit().selectAll();QTest.keyClicks(box.lineEdit(),'8');w.batch('Intervening accepted work',[dict(op='project.rename',name='Human and agent workflow proof')]);idle();pinned=deepcopy(w.document());rev=w.state()['revision'];QTest.keyClick(box.lineEdit(),Qt.Key_Return);until=time.monotonic()+.35
 while time.monotonic()<until:pump()
 idle();assert w.document()==pinned and w.state()['revision']==rev;checks.append('Intervening owner revision rejects stale fade draft without changing accepted work')
 accepted=deepcopy(w.document());w.submit('source_open',asset={k:a[k] for k in ('id','name','kind','location','sha256','metadata')});idle();source_doc=w.state()['source']['document'];assert source_doc['clips'][0]['duration']==31;w.transport('play',target='source');idle();wait(lambda:not w.source_transport_state().get('playing') and w.source_transport_state().get('frame')==31,10);w.transport('release',target='source');idle();assert w.document()==accepted;checks.append('Real owner Source audition uses complete31-frame natural interval, discard-test output, no artwork history change')
 w.save(path=str(proof.resolve()));idle();saved=deepcopy(w.document());opened,rev,states,_=read_project(proof,threading.Event());normalized=deepcopy(opened)
 for a,b in zip(normalized['media'],saved['media']):
  assert hashlib.sha256(Path(a['location']['path']).read_bytes()).hexdigest()==b['sha256'];a['location']=deepcopy(b['location'])
 assert normalized==saved and all(r['status']=='Ready' for r in states.values());w.open(str(proof.resolve()));idle();assert w.document()==opened and w.state()['revision']==rev;assert opened['clips'][0]['audio']['fade_in']==4 and opened['clips'][0]['audio']['fade_out']==4;checks.append('One12s editable proof saved portably; copied media hashes/all other fields match, then exact actual-owner reopen with integer fades/fractions')
 shell.close();wait(lambda:shell.closing);assert w.exited() and shell.client.process.returncode==0;(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,proof=str(proof),revision=rev,owner_exit=0,workers_exited=True,namespace=ns.hex,limits='Offscreen synthetic Qt and actual owner/discard lane. No physical desktop, audio-device or listening claim.'),indent=2),encoding='utf8');print('PASS',len(checks),'Qt/owner groups',out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if shell and not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();end=time.monotonic()+40
   while not shell.closing and time.monotonic()<end:pump()
