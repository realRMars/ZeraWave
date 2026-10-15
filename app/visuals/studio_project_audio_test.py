"""Real Studio/API and synthetic Qt controls; explicit discard sink, no device/listening."""
from pathlib import Path
from copy import deepcopy
import sys,os,time,json,uuid,hashlib,traceback
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QDialog,QDoubleSpinBox,QTableWidget,QTableWidgetItem,QCheckBox
from PySide6.QtCore import Qt,QTimer
from studio_qt import Shell
from project_api import call
import numpy as np,soundfile as sf
app=QApplication([]);shell=None;checks=[];samples=[]
def pump():app.processEvents();time.sleep(.003)
def wait(test,seconds=15):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  pump()
  if test():return
 raise AssertionError('Did not settle: '+w.notice.text()+'; '+str(audio()))
def audio():return shell.client.snapshot.get('audio_hub',{}).get('project_audio',{})
def idle():wait(lambda:w.pending is None and shell.client.edit_count==0)
def api(op,**args):
 s=call(endpoint,dict(op='state'))['state'];r=call(endpoint,dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args));assert r['ok'],r
 while r['outcome']['status'] in ('preparing','saving'):pump();r=call(endpoint,dict(op='operation_status',operation_id=r['outcome']['id']))
 assert r['outcome']['status'] in ('accepted','durable'),r;wait(lambda:w.state()['revision']==r['state']['revision']);return r
def select():
 wait(lambda:w.trees['clips'].topLevelItemCount()==1);w.tabs.setCurrentWidget(w.pages['clips'][0]);w.trees['clips'].setCurrentItem(w.trees['clips'].topLevelItem(0))
try:
 file=out/'stereo.wav';sf.write(file,np.full((48000*3,2),.25,np.float32),48000,subtype='FLOAT');original=file.read_bytes();shell=Shell(layout_path=out/'layout.json',control_log_path=out/'owner.log');shell.resize(1800,1100);shell.show();wait(lambda:shell.client is not None);w=shell.project_workspace;endpoint=w.state()['endpoint'];art=deepcopy(shell.owner.values());shell.panels['project'].toggleView(True);shell.panels['project'].setAsCurrentTab();api('new',name='Qt project audio');a,t,c=[uuid.uuid4().hex for _ in range(3)];api('batch',label='Shared audio fixture',changes=[dict(op='media.add',id=a,name='Source',kind='Audio',location=dict(kind='external',path=str(file))),dict(op='track.add',id=t,name='Narration',kind='audio'),dict(op='clip.add',id=c,name='Voice',asset=a,track=t,start=0,duration=60,audio=dict(gain=0.6123456789,mute=False,fade_in=0,fade_out=0,envelope=[]))]);select();before=deepcopy(w.document());revision=w.state()['revision']
 def unchanged():assert isinstance(app.activeModalWidget(),QDialog);app.activeModalWidget().accept()
 QTimer.singleShot(30,unchanged);w.audio_edit('clips');idle();assert w.state()['revision']==revision and w.document()==before;checks.append('Real volume dialog untouched OK preserves precise authored gain and creates no document/history edit')
 def volume():
  dialog=app.activeModalWidget();assert isinstance(dialog,QDialog)
  for box in dialog.findChildren(QDoubleSpinBox):
   if box.accessibleName()=='Linear gain (1 = unity)':box.setValue(.5)
  table=dialog.findChild(QTableWidget);table.setRowCount(3)
  for i,point in enumerate([(0,1),(30,.25),(60,1)]):
   for j,value in enumerate(point):table.setItem(i,j,QTableWidgetItem(str(value)))
  dialog.accept()
 QTimer.singleShot(30,volume);w.audio_edit('clips');idle();after=deepcopy(w.document());assert after['clips'][0]['audio']['gain']==.5 and after['clips'][0]['audio']['envelope']==[[0,1.],[30,.25],[60,1.]];w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==after;checks.append('Actual Qt gain and editable envelope table submit same owner transaction; exact Undo/Redo restore recipe and stable IDs')
 w.transport('play');wait(lambda:audio().get('status')=='Playing');s=w.transport_state();assert 'submitted-minus-padding' in s['clock'] and audio()['device_position'] is None and audio()['output']['backend'].startswith('discard-test');assert shell.hub_volume.isEnabled() and shell.hub_mute.isEnabled() and not shell.hub_source.isEnabled();assert shell.waveform.name.text()=='Qt project audio';checks.append('Real owner audio preparation connects to timeline clock and Qt project PCM/master controls; explicit diagnostic sink and no audible-position claim')
 for frame in (4,22,8,31,12,40):w.transport('seek',frame)
 wait(lambda:w.transport_future is None and w.transport_desired is None);wait(lambda:tuple(audio().get('binding',[])[:3])==(w.state()['epoch'],w.state()['revision'],w.transport_state()['generation']) and not audio().get('transition_pending'));assert audio()['submitted_sample']>=64000;samples.append(deepcopy(audio()));w.transport('pause');wait(lambda:audio().get('status')=='Paused');assert not shell.client.snapshot['audio_hub']['output'];checks.append('Latest repeated owner seeks reconcile applied audio binding, flush old queue and pause releases output in same running owner')
 # Change the disposable source, then restore it; accepted project stays intact.
 file.write_bytes(original+b'actual changed source');w.transport('play');wait(lambda:audio().get('status')=='Unavailable');assert 'source changed' in audio()['error'].lower() and w.document()==after;file.write_bytes(original);w.transport('play');wait(lambda:audio().get('status')=='Playing');assert w.document()==after;checks.append('Actual copied-file mutation fails source verification truthfully; restoring original identity and deliberate Play recover same owner without dropping accepted recipes')
 w.transport('stop');wait(lambda:not audio().get('active'));wait(lambda:audio().get('status')=='Stopped');wait(lambda:shell.hub_source.isEnabled());(out/'ART_PRESERVATION.json').write_text(json.dumps(dict(before=art,after=shell.owner.values()),indent=2),'utf8');assert shell.owner.values()==art;api('save',path=str(out/'audio.zwv'));api('close');api('open',path=str(out/'audio.zwv'));assert w.document()['clips']==after['clips'];checks.append('Stop restores legacy controls/artistic settings; portable Save/Close/Open retains separate editable source gains/envelopes and IDs')
 shell.close();wait(lambda:shell.closing,30);assert w.exited() and shell.client.process.returncode==0 and not shell.client.reader.is_alive();assert shell.client.protocol_error_count==0;checks.append('Normal Qt close confirms owner/media/reader and project audio preparation cleanup')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,samples=samples,classification=__doc__,submission_callbacks=w.callback_samples,source_sha256=hashlib.sha256(original).hexdigest()),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if shell and not shell.closing:
  w.close_resources();w.preview.media.thread.join(5);shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
