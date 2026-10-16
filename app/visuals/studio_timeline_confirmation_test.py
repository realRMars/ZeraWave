"""Real Qt nested confirmation loops and ProjectService; no native pointer claim."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import sys,os,time,json,uuid,traceback
root=Path(__file__).resolve().parents[2] if Path(__file__).parent.name=='visuals' else Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QLabel,QMessageBox
from PySide6.QtCore import Qt,QTimer
from PySide6.QtTest import QTest
from project_service import ProjectService
from studio_timeline import TimelinePanel
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);s=ProjectService();requests=[];checks=[];errors=[];p=None;uid=lambda:uuid.uuid4().hex
def binding(state=None):
 state=state or s.state();return dict(expected_project=state['project_id'],expected_epoch=state['epoch'],expected_revision=state['revision'],expected_command=state['command_revision'])
def request(op,**args):
 r=dict(op=op,operation_id=uid(),**binding(),**args);response=s.request(r);assert response['ok'],response
 while s.jobs:s.poll();app.processEvents();time.sleep(.002)
 return response
def batch(label,changes,captured):
 r=dict(op='batch',label=label,changes=changes,operation_id=uid(),**captured);result=s.request(r);requests.append(dict(request=r,result=result));return r['operation_id']
def settle():p.refresh();app.processEvents();p.refresh()
def answer_after(fn):
 def answer():
  try:
   if fn:fn()
   settle();modal=app.activeModalWidget();assert isinstance(modal,QMessageBox);QTest.mouseClick(modal.button(QMessageBox.Yes),Qt.LeftButton)
  except BaseException:
   errors.append(traceback.format_exc())
   if app.activeModalWidget():app.activeModalWidget().reject()
 QTimer.singleShot(30,answer)
try:
 request('new',name='Confirmation guards');asset,video,text,clip,caption=[uid() for _ in range(5)];request('batch',changes=[dict(op='media.add',id=asset,name='Missing fixture image',kind='Image',sha256='a'*64,metadata={},location=dict(kind='external',path=str(out/'absent.png')),placeholder=True),dict(op='track.add',id=video,kind='video'),dict(op='track.add',id=text,kind='graphics'),dict(op='clip.add',id=clip,asset=asset,track=video,start=20,duration=10),dict(op='caption.add',id=caption,track=text,start=100,duration=20,text='Later caption')])
 w=SimpleNamespace(shell=SimpleNamespace(safe=lambda fn:fn(),statusBar=lambda:SimpleNamespace(showMessage=lambda text:None)),notice=QLabel(),pending=None,trees={},state=s.state,binding=binding,document=lambda:s.document,transport=lambda *a,**k:None,transport_state=lambda:dict(frame=0,end=120),add_track=lambda:None,batch=batch)
 p=TimelinePanel(w);w.timeline=p;p.closed=True;p.resize(1500,700);p.show();settle();c=p.canvas;c.selection={clip};c.selected=('clips',clip);old=binding();after={}
 def move_during_modal():
  request('batch',changes=[dict(op='items.move',ids=[clip],delta=70)]);after['document']=deepcopy(s.document)
 answer_after(move_during_modal);c.delete_selection(True);assert not errors,errors;assert requests[-1]['request']['expected_revision']==old['expected_revision'] and not requests[-1]['result']['ok'];assert requests[-1]['result']['error']['code']=='stale_revision' and s.document==after['document'];checks.append('Actual nested ripple confirmation retains its original revision/selection when an intervening accepted move changes the confirmed interval; new interval is not deleted')
 settle();old=binding();extra=uid()
 def add_during_modal():
  request('batch',changes=[dict(op='clip.add',id=extra,asset=asset,track=video,start=200,duration=10)]);after['document']=deepcopy(s.document)
 answer_after(add_during_modal);p.headers.remove(video);assert not errors,errors;assert requests[-1]['request']['expected_revision']==old['expected_revision'] and requests[-1]['result']['error']['code']=='stale_revision' and s.document==after['document'];checks.append('Nonempty track confirmation keeps the pre-dialog binding/count; an API-added clip survives stale rejection intact')
 settle();before=deepcopy(s.document);answer_after(None);p.headers.remove(video);assert not errors,errors;assert requests[-1]['result']['ok'] and not s.document['clips'];request('undo');assert s.document==before;checks.append('Explicit renewed confirmation sees current contents, removes them in one owner operation and Undo restores exact IDs/source recipes')
 settle();c.selection={clip};c.selected=('clips',clip);before=deepcopy(s.document);answer_after(None);c.delete_selection(True);assert requests[-1]['result']['ok'] and next(r for r in s.document['clips'] if r['id']==extra)['start']==190;request('undo');assert s.document==before;checks.append('Explicit renewed ripple confirms the new interval and shifts synchronized downstream items once; exact Undo restores it')
 settle();before=deepcopy(s.document);request('batch',changes=[dict(op='project.rename',name='Owner newer than displayed')]);expected=deepcopy(s.document);count=len(requests);c.perform('Stale UI action',[dict(op='items.delete',ids=[clip])]);assert len(requests)==count and s.document==expected;checks.append('Action with stale displayed geometry refreshes/refuses submission instead of capturing a newer authoritative revision')
 p.close_resources();p.close();s.can_shutdown(True);s.shutdown();assert p.exited() and not any(t.is_alive() for t in s.pool._threads);(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,requests=requests,errors=errors),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if p:p.close_resources();p.close()
 if not s.closed:
  for job in s.jobs.values():job['cancel'].set()
  while s.jobs:s.poll();time.sleep(.002)
  s.shutdown()
