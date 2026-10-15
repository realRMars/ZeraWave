"""Reviewer R1/R2 exact interleavings: real owner/API and offscreen Qt close.

Fixture-only delayed submission/faults; no physical desktop or device claim.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,time,json,uuid,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_api import call
from project_cli import request
from project_service import ProjectService
app=QApplication([]);shell=None;checks=[];evidence={}
def pump():app.processEvents();time.sleep(.003)
def wait(fn,timeout=30):
 end=time.perf_counter()+timeout
 while time.perf_counter()<end:
  pump()
  if fn():return
 raise AssertionError('Fixture did not settle')
def data(op,**args):
 s=call(endpoint,dict(op='state'))['state'];return dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args)
def run(op,**args):
 r=request(endpoint,data(op,**args));assert r.get('ok'),r;return r
def ready():wait(lambda:w.pending is None and shell.client.edit_count==0)
def binding(s):return dict(expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'])
try:
 shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;w.show_workspace();endpoint=w.state()['endpoint'];wait(lambda:not shell.client.snapshot['media_library']['loading']);run('new',name='Saved before close');run('save',path=str(out/'before-close.zwv'));wait(lambda:w.state().get('path')==str(out/'before-close.zwv'))
 before=call(endpoint,dict(op='state'))['state'];malformed=[]
 for changes in (None,{},'invalid',[],[None],['invalid'],[42],[{}],[dict(op='project.settings',values=None)],[dict(op='clip.audio',id=uuid.uuid4().hex,values=42)]):
  d=data('batch',changes=changes,label='Invalid input');r=call(endpoint,d);assert not r['ok'] and r['outcome']['status']=='rejected',r;replay=call(endpoint,d);assert replay['outcome']==r['outcome'];status=call(endpoint,dict(op='operation_status',operation_id=d['operation_id']));assert status['outcome']['status']=='rejected';malformed.append(dict(input=changes,outcome=r['outcome']))
 state=call(endpoint,dict(op='state'))['state'];assert state['document']==before['document'] and state['revision']==before['revision'] and state['history_bytes']==before['history_bytes'];assert not any(o['status']=='preparing' for o in state['operations']);wait(lambda:not w.pending and not any(o['status']=='preparing' for o in w.state()['operations']));w.refresh();assert w.controls[2].isEnabled();evidence['malformed']=malformed
 run('batch',label='Valid API after malformed input',changes=[dict(op='project.rename',name='After malformed API')]);wait(lambda:w.state()['document']['name']=='After malformed API');w.refresh();assert w.undo.isEnabled();QTest.mouseClick(w.undo,Qt.LeftButton);ready();assert w.state()['document']['name']=='Saved before close'
 checks.append('Ten malformed container/member/nested shapes terminalize through actual API; exact same-ID replay/status, no document/history loss, valid API edit and Qt Undo work afterwards')
 # Supplemental unexpected failure must be visible and terminal, not hidden or
 # called rejection of an already installed edit.
 service=ProjectService();s=service.state();service.request(dict(op='new',operation_id=uuid.uuid4().hex,**binding(s)));s=service.state();original=service._apply
 def unexpected(req,prepared=None):raise RuntimeError('Controlled unexpected handler fault')
 service._apply=unexpected;fault=service.request(dict(op='batch',operation_id=uuid.uuid4().hex,changes=[dict(op='project.rename',name='No install')],**binding(s)));assert fault['outcome']['status']=='failed' and not service.jobs
 def after_install(req,prepared=None):
  original(req,prepared);raise RuntimeError('Controlled fault after installation')
 service._apply=after_install;s=service.state();installed=service.request(dict(op='batch',operation_id=uuid.uuid4().hex,changes=[dict(op='project.rename',name='Accepted before fault')],**binding(s)));assert installed['outcome']['status']=='accepted' and installed['error']['code']=='outcome_unknown' and service.document['name']=='Accepted before fault';service._apply=original;service.can_shutdown(True);service.shutdown();evidence['unexpected_faults']=[fault,installed]
 checks.append('Supplementary unexpected handler faults are logged/terminalized; an installed edit remains accepted/unknown, never falsely rejected')
 run('save',path=str(out/'before-close.zwv'));wait(lambda:not w.state()['dirty']);shell.saved_art='fixture-artwork-only-dirty';original_submit=shell.client.submit;injected=False;close_data=[]
 def interleave(action,**args):
  global injected
  if action=='close' and not injected:
   injected=True;close_data.append(deepcopy(args));evidence['late_edit']=run('batch',label='API edit after GUI close decision',changes=[dict(op='project.rename',name='NEW ACCEPTED UNSAVED EDIT')])
  return original_submit(action,**args)
 shell.client.submit=interleave
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing or shell.close_request is None,40)
 assert injected and not shell.closing and shell.client.process.poll() is None and shell.isVisible();state=call(endpoint,dict(op='state'))['state'];assert state['dirty'] and state['document']['name']=='NEW ACCEPTED UNSAVED EDIT';assert json.loads((out/'before-close.zwv').read_text())['document']['name']=='Saved before close';assert close_data[0]['mode']=='discard' and close_data[0]['project_mode']=='clean' and close_data[0]['project_binding']['expected_revision']<state['revision'];evidence['close_interleaving']=dict(payload=close_data[0],status=shell.statusBar().currentMessage(),retained=state)
 checks.append('Exact R1 artwork-only discard / delayed close interleaving rejects at authoritative owner, retains newer accepted unsaved edit, prior file and same live instance')
 shell.client.submit=original_submit;run('batch',label='Continued editing after deferred close',changes=[dict(op='project.rename',name='Recovered same owner')]);run('undo');assert call(endpoint,dict(op='state'))['state']['document']['name']=='NEW ACCEPTED UNSAVED EDIT';run('redo');run('save',path=str(out/'recovered.zwv'));wait(lambda:not w.state()['dirty'])
 # Artistic discard alone must not implicitly discard a CURRENT dirty project.
 run('batch',label='Current dirty project',changes=[dict(op='project.rename',name='Needs own discard decision')]);wait(lambda:w.state()['dirty']);s=call(endpoint,dict(op='state'))['state'];f=original_submit('close',mode='discard',project_mode='clean',project_binding=binding(s));wait(f.done)
 try:f.result()
 except ValueError:pass
 else:raise AssertionError('Artwork discard leaked into video domain')
 assert shell.client.process.poll() is None and call(endpoint,dict(op='state'))['state']['document']['name']=='Needs own discard decision'
 checks.append('Artistic discard with a current dirty project is refused without its separate project discard permission')
 # Deliberate video discard can coexist with clean artwork; observe payload.
 shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True);payloads=[]
 def record(action,**args):
  if action=='close':payloads.append(deepcopy(args))
  return original_submit(action,**args)
 shell.client.submit=record
 with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,40)
 assert payloads[-1]['mode']=='clean' and payloads[-1]['project_mode']=='discard' and shell.client.process.returncode==0 and shell.client.closed;evidence['explicit_project_discard']=payloads[-1]
 checks.append('Explicit video discard with clean artistic domain closes normally, preserving separate decisions and actual owned reader/worker exit')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,evidence=evidence,classification=__doc__),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,evidence=evidence),indent=2),'utf8');raise
finally:
 if shell and not shell.closing:
  shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
