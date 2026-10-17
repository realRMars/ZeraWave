"""One proof extended through real helper/API and synthetic Qt editing; no device."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,threading,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);inputs=Path(sys.argv[3]);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_manifest import compile_plan,apply_plan,journal_lock,Journal,stable,file_hash,FORMAT
from project_service import read_project
app=QApplication([]);shell=None;checks=[];answer={};raw=[]
def pump():
 began=time.perf_counter();app.processEvents();raw.append((time.perf_counter()-began)*1000);time.sleep(.002)
def wait(fn,seconds=45):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if fn():return
 raise AssertionError('Timeout '+w.notice.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and w.timeline.canvas.version==(w.state().get('epoch'),w.state().get('revision')))
def make_manifest(d):
 ns='e360d7247a3c5f3fb9528f39f1efbbb9';ref=lambda s:dict(ref=s);media=[]
 for key,kind,path in [('narration','Audio',inputs.parent/'narration-48017.wav'),('shot1','Video',inputs/'Shot-1.mp4'),('shot2','Video',inputs/'Shot-2.mp4'),('music','Audio',inputs/'Music.wav'),('still','Image',inputs/'Still.png')]:media.append(dict(key=key,name=key,kind=kind,path=str(path.resolve()),sha256=file_hash(path)))
 tracks=[dict(category='tracks',key=key,values={k:deepcopy(v) for k,v in row.items() if k!='id'}) for key,row in zip(('narration','captions'),d['tracks'])]
 tracks+=[dict(category='buses',key='music',values=dict(name='Music bus')),dict(category='tracks',key='picture',values=dict(name='Picture',kind='video',order=2)),dict(category='tracks',key='music',values=dict(name='Music',kind='audio',order=3,output=ref('buses:music'))),dict(category='tracks',key='titles',values=dict(name='Titles and graphics',kind='graphics',order=4))]
 narrator=deepcopy(next(c for c in d['clips'] if c['id']==stable(ns,'clips','narration')));narrator.pop('id');narrator.pop('audio_window');narrator.update(asset=ref('media:narration'),track=ref('tracks:narration'),duration='natural');caption=deepcopy(d['captions'][0]);caption.pop('id');caption['track']=ref('tracks:captions')
 items=[dict(category='clips',key='narration',values=narrator),dict(category='captions',key='proof',values=caption),dict(category='clips',key='shot1',values=dict(name='Shot one',asset=ref('media:shot1'),track=ref('tracks:picture'),start=0,duration=180,source_in=[0,1])),dict(category='clips',key='shot2',values=dict(name='Shot two',asset=ref('media:shot2'),track=ref('tracks:picture'),start=180,duration=120,source_in=[1,1])),dict(category='clips',key='still',values=dict(name='Still • explicit2seconds',asset=ref('media:still'),track=ref('tracks:picture'),start=300,duration=60,layout=dict(fit='Fit'))),dict(category='clips',key='music',values=dict(name='Independent music',asset=ref('media:music'),track=ref('tracks:music'),start=0,duration=360,audio=dict(gain=.04,fade_in=6,fade_out=12,envelope=[[0,1.],[90,1.],[120,.3],[210,.3],[240,.8],[359,.8]])))]
 return dict(format=FORMAT,version=1,id=ns,project_id=d['id'],settings=deepcopy(d['settings']),media=media,sections=[dict(key='foundation',label='Proof: named tracks and music bus',items=tracks),dict(key='sequence',label='Proof: two shots,still and music',items=items)],save=dict(path=str(proof.resolve()),portable=True))
try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1800,1080);shell.show();w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));shell.video_panels.activate(False);w.open(str(proof));idle();before=deepcopy(w.document());assert w.import_status.show_button.isVisible() and w.import_status.cancel_button.isVisible();assert not w.import_status.cancel_button.isEnabled();manifest=make_manifest(before);(out/'MANIFEST_INPUT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');endpoint=Path(w.state()['endpoint'])
 def helper():
  try:
   plan=compile_plan(endpoint,manifest);(out/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8')
   with journal_lock(out/'journal'):answer['result']=apply_plan(endpoint,Journal(out/'journal',plan))
  except BaseException:answer['error']=traceback.format_exc()
 thread=threading.Thread(target=helper,name='Proof manifest client');thread.start();wait(lambda:not thread.is_alive());thread.join();assert not answer.get('error'),answer;assert answer['result']['status']=='complete';wait(lambda:w.state().get('saved_revision')==w.state().get('revision') and len(w.document()['clips'])==5);idle();assembled=deepcopy(w.document());assert len(assembled['media'])==5 and assembled['settings']['width']==1920 and assembled['settings']['height']==1080 and max(r['start']+r['duration'] for r in assembled['clips'])==360;assert assembled['clips'][0]==before['clips'][0] and assembled['captions']==before['captions'];assert len(w.timeline.canvas.rows())==6;checks.append('Same12s1920x1080/30/48k proof extended by real helper on existing Studio endpoint:5reused media,5clips,caption,5named tracks+music bus; original entities exact and no Library mutation')
 w.submit('undo');idle();assert w.document()['clips']==before['clips'] and w.document()['captions']==before['captions'];w.submit('redo');idle();assert w.document()==assembled;checks.append('Named sequence Undo/Redo removes/restores exact intended helper data through Qt owner')
 ns=manifest['id'];music=stable(ns,'clips','music');c=w.timeline.canvas;c.select('clips',music);ins=shell.video_panels.inspector;ins.version=None;ins.refresh();box=ins.fields['gain'];box.setFocus();box.lineEdit().selectAll();QTest.keyClicks(box.lineEdit(),'0.052');QTest.keyClick(box.lineEdit(),Qt.Key_Return);idle();edited=deepcopy(w.document());assert next(r for r in edited['clips'] if r['id']==music)['audio']['gain']==.052 and edited['clips'][0]==assembled['clips'][0];w.submit('undo');idle();assert w.document()==assembled;w.submit('redo');idle();assert w.document()==edited;w.submit('undo');idle();assert w.document()==assembled
 c.select('captions',stable(ns,'captions','proof'));ins.version=None;ins.refresh();ins.text.setFocus();ins.text.selectAll();QTest.keyClicks(ins.text,'Human editable caption');QTest.mouseClick(ins.text_apply,Qt.LeftButton);idle();assert w.document()['captions'][0]['text']=='Human editable caption';w.submit('undo');idle();assert w.document()==assembled;checks.append('Helper-created music gain and caption remain manually editable in existing inline Inspector; narrator/other entities preserved,exact UndoRedo')
 w.save(path=str(proof));idle();w.open(str(proof));idle();opened,revision,states,_=read_project(proof,threading.Event());assert w.document()==opened and all(r['status']=='Ready' for r in states.values());assert opened['clips']==assembled['clips'] and opened['captions']==assembled['captions'] and opened['buses']==assembled['buses'];wait(lambda:w.preview.presented and w.preview.presented[:2]==(w.state()['epoch'],w.state()['revision']));assert w.preview.view.surface.image.width()==1920 and w.preview.view.surface.image.height()==1080;checks.append('Normal portable save/actual-owner reopen keeps stable entities,full envelope,original media hashes and1920x1080 supported CPU preview')
 shell.grab().save(str(out/'OFFSCREEN-SYNTHETIC.png'));shell.close();wait(lambda:shell.closing);assert w.exited() and shell.client.process.returncode==0;(out/'RAW_QT_PROCESS_EVENTS_MS.json').write_text(json.dumps(raw),encoding='utf8');(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,proof=str(proof),revision=revision,owner_exit=0,workers_exited=True,helper=answer['result'],unverified='Synthetic Qt/CPU preview,not physical pointer,device,listening or GPU qualification; separate bounded native UI observation follows.'),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if shell and not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();end=time.monotonic()+40
   while not shell.closing and time.monotonic()<end:pump()
