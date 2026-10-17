"""Same12-second proof extended by real recipe helper; synthetic editable Qt paths."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,threading,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);input_manifest=Path(sys.argv[3]);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox,QPushButton
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_manifest import *
from project_service import read_project
app=QApplication([]);shell=None;checks=[];raw=[];ns='e360d7247a3c5f3fb9528f39f1efbbb9';ref=lambda s:dict(ref=s)
def pump():
 began=time.perf_counter();app.processEvents();raw.append((time.perf_counter()-began)*1000);time.sleep(.002)
def wait(fn,seconds=50):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if fn():return
 raise AssertionError('Timeout '+w.notice.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and w.timeline.canvas.version==(w.state().get('epoch'),w.state().get('revision')))
def threaded(fn):
 answer={}
 def run():
  try:answer['value']=fn()
  except BaseException:answer['error']=traceback.format_exc()
 thread=threading.Thread(target=run);thread.start();wait(lambda:not thread.is_alive());thread.join();assert not answer.get('error'),answer;return answer.get('value')
def apply_manifest(manifest):
 plan=compile_plan(endpoint,manifest);(out/'PLAN.json').write_text(json.dumps(plan,indent=2),encoding='utf8')
 with journal_lock(out/'journal'):return apply_plan(endpoint,Journal(out/'journal',plan))
try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1800,1080);shell.show();w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));shell.video_panels.activate(False);w.open(str(proof));idle();endpoint=Path(w.state()['endpoint']);before=deepcopy(w.document());manifest=json.loads(input_manifest.read_text(encoding='utf8'));recipes=[]
 for section in manifest['sections']:
  kept=[]
  for entity in section['items']:
   if entity['category']=='clips' and entity['key'] in ('music','still'):
    values=deepcopy(entity['values']);values.pop('link_id',None);values.pop('audio_window',None)
    if entity['key']=='music':
     values.pop('layout',None);kind='music'
    else:
     values.pop('audio',None);values.pop('rate',None);values.pop('pad_end',None);kind='still'
    recipes.append(dict(key=entity['key'],kind=kind,version=1,params=values))
   else:kept.append(entity)
  section['items']=kept
 # Explicit empty provenance adopts compatible pre-existing Stage3 media clips;
 # the planner still compares their complete ordinary content before reuse.
 def add(kind,key,**params):recipes.append(dict(key=key,kind=kind,version=1,params=params))
 for key,start,brand,game in [('intro-a',0,'ZeraWave','Editable workflow'),('intro-b',180,'Independent variant','Ordinary timeline items')]:add('entrance',key,track=ref('tracks:titles'),start=start,duration=90,brand=brand,game=game,enter_frames=12,exit_frames=8)
 add('review_card','review',track=ref('tracks:titles'),start=270,duration=90,heading='Recipe expansion',body='Text, layout, timing and audio stay editable.',parts=dict(body=dict(size=32,max_lines=3)))
 add('chapter','chapter',track=ref('tracks:titles'),start=0,duration=360,text='{elapsed} / {duration}',range_start=0,range_end=360)
 add('caption','recipe-caption',track=ref('tracks:captions'),start=90,duration=90,text='A separate editable recipe caption',style=dict(bounds=[.06,.65,.60,.10],size=26))
 manifest['sections'].append(dict(key='editable-recipes',label='Proof: editable recipe variants',items=[],recipes=recipes));manifest['save']['path']=str(proof.resolve());(out/'MANIFEST_INPUT.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8');result=threaded(lambda:apply_manifest(manifest));wait(lambda:len(w.document()['graphics'])==8);idle();assembled=deepcopy(w.document());assert assembled['clips']==before['clips'] and assembled['captions'][:1]==before['captions'] and assembled['media']==before['media'];assert len(assembled['captions'])==2 and len(w.timeline.canvas.rows())==15;checks.append('Same proof gains8ordinary graphics/timer/progress and1caption,with2independent entrance variants; existing5clips/5media/original caption exact,all15timeline rows exposed')
 w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==assembled;checks.append('Qt named recipe-section Undo/Redo restores exact original/expanded proof')
 c=w.timeline.canvas;ins=shell.video_panels.inspector;c.select('graphics',stable(ns,'graphics','intro-a.brand'));ins.version=None;ins.refresh();assert ins.text.isVisible();ins.text.setFocus();ins.text.selectAll();QTest.keyClicks(ins.text,'Human recipe override');QTest.mouseClick(ins.text_apply,Qt.LeftButton);idle();manual=deepcopy(w.document());second=stable(ns,'graphics','intro-b.brand');assert next(g for g in manual['graphics'] if g['id']==second)==next(g for g in assembled['graphics'] if g['id']==second)
 def conflict():
  try:compile_plan(endpoint,manifest);raise AssertionError('Manual override overwritten')
  except Conflict:return True
 assert threaded(conflict);assert w.document()==manual;w.submit('undo');idle();assert w.document()==assembled;checks.append('Existing inline title text remains editable; variantB unchanged,helper refuses manual override,normal Undo exact')
 c.select('clips',stable(ns,'clips','music'));ins.version=None;ins.refresh();editor=ins.envelope;assert editor.table.rowCount()==6;editor.table.item(2,1).setText('0.35');button=next(b for b in editor.findChildren(QPushButton) if b.text()=='Apply envelope');QTest.mouseClick(button,Qt.LeftButton);idle();edited=deepcopy(w.document());audio=next(r['audio'] for r in edited['clips'] if r['id']==stable(ns,'clips','music'));assert len(audio['envelope'])==6 and audio['envelope'][2]==[120,.35];assert edited['clips'][0]==assembled['clips'][0];w.submit('undo');idle();assert w.document()==assembled;w.submit('redo');idle();assert w.document()==edited;w.submit('undo');idle();assert w.document()==assembled;checks.append('Existing Qt envelope table applies complete6-point array to music only; narrator/other items exact and exact UndoRedo')
 w.save(path=str(proof));idle();w.open(str(proof));idle();opened,revision,states,_=read_project(proof,threading.Event());assert w.document()==opened and all(r['status']=='Ready' for r in states.values());assert all(opened[k]==assembled[k] for k in ('clips','captions','graphics','tracks','buses'));assert all(a['sha256']==b['sha256'] for a,b in zip(opened['media'],before['media']));checks.append('Normal portable save/actual owner reopen preserves recipe provenance,stable IDs,full styles/keys/ranges/envelopes/source hashes and original narration tail')
 c.select('graphics',stable(ns,'graphics','intro-a.brand'));ins.version=None;ins.refresh();wait(lambda:w.preview.presented and w.preview.presented[:2]==(w.state()['epoch'],w.state()['revision']));shell.grab().save(str(out/'OFFSCREEN-SYNTHETIC.png'));(out/'FINAL_DOCUMENT.json').write_text(json.dumps(opened,indent=2),encoding='utf8');(proof.parent/'manifest-stage4-v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8');shell.close();wait(lambda:shell.closing);assert w.exited() and shell.client.process.returncode==0;(out/'RAW_QT_PROCESS_EVENTS_MS.json').write_text(json.dumps(raw),encoding='utf8');(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,helper=result,proof=str(proof),revision=revision,proof_sha256=file_hash(proof),owner_exit=0,workers_exited=True,unverified='Synthetic Qt/CPU preview; no natural typing,pointer/GPU/device/listening/scanout qualification.'),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if shell and not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
   shell.close();end=time.monotonic()+40
   while not shell.closing and time.monotonic()<end:pump()
