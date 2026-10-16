"""Actual owner/preparation, controlled padding and signals; no hardware clock."""
from pathlib import Path
from contextlib import contextmanager
import sys,time,json,threading,uuid,hashlib,traceback
import numpy as np,soundfile as sf
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/audio'),str(root/'app/visuals')]
from studio_transport import AudioOwner
from project_evaluator import Evaluator
from video_project import create,apply
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);owner=None;checks=[];rows=[]
class Enumeration:
 def request(self):pass
 def snapshot(self):return dict(sources=[],error=None)
 def close(self):pass
class Sink:
 paces_audio=False
 padding=1024
 def __init__(self):self.active=0;self.maximum=0;self.blocks=0
 @contextmanager
 def context(self):
  self.active+=1;self.maximum=max(self.active,self.maximum)
  try:yield self
  finally:self.active-=1
 def play(self,pcm):self.blocks+=1
 def drain(self):pass
 def snapshot(self):return dict(backend='Controlled1024-frame padding; NO device',device_position=None)
def wait(fn):
 end=time.monotonic()+10
 while time.monotonic()<end:
  if fn():return
  time.sleep(.002)
 raise AssertionError('Did not settle: '+str(owner.project_snapshot()))
try:
 path=out/'stereo.wav';sf.write(path,np.tile(np.array([.25,.125],np.float32),(48000*3,1)),48000,subtype='FLOAT');a,t,b=[uuid.uuid4().hex for _ in range(3)];d=apply(create('Meter graph'),[dict(op='media.add',id=a,name='Constant stereo',kind='Audio',location=dict(kind='external',path=str(path)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=dict(duration=3)),dict(op='track.add',id=t,kind='audio'),dict(op='clip.add',asset=a,track=t,start=0,duration=90),dict(op='bus.add',id=b,name='Dialogue',gain=2.),dict(op='track.output',id=t,output=b),dict(op='master.audio',values=dict(gain=.5))],uuid.uuid4().hex)[0];e=Evaluator(d,'meters',1);sink=Sink();owner=AudioOwner(output_factory=sink.context,enumerator=Enumeration())
 def clock(generation,playing=True,active=True):return dict(project=d['id'],epoch='meters',revision=1,generation=generation,discontinuity=generation,frame=0,sample=0,playing=playing,active=active)
 owner.offer_project(e,clock(1));wait(lambda:owner.project_snapshot().get('meter_timing_available'));s=owner.project_snapshot();rows.append(s)
 for key,expected in [(t,[.25,.125]),(b,[.5,.25]),('master',[.25,.125])]:assert np.max(abs(np.array(s['levels'][key]['peak'])-expected))<1e-6 and np.max(abs(np.array(s['levels'][key]['rms'])-expected))<1e-6
 assert s['meter_span'][0]<=s['meter_sample_estimate']<s['meter_span'][1] and s['padding_frames']==1024 and s['meter_blocks']<=32 and s['device_position'] is None;checks.append('Post-track/bus/Master stereo peak/RMS match independent constants and submitted block containing padding estimate; bounded32-block metadata, no heard clock assertion')
 owner.submit('volume',value=.1);owner.submit('mute',value=True);wait(lambda:owner.snapshot()['mute']);time.sleep(.1);s=owner.project_snapshot();assert np.max(abs(np.array(s['levels']['master']['peak'])-[.25,.125]))<1e-6;checks.append('Hardware/playback volume and mute do not falsify authored Master meters')
 owner.offer_project(e,clock(2,False));wait(lambda:owner.project_snapshot().get('applied_binding',[None]*3)[2]==2);s=owner.project_snapshot();assert not s['meter_timing_available'] and s['levels'] is None and s['meter_blocks']==0;rows.append(s);checks.append('Pause clears old-generation meter blocks; unavailable timing is explicit')
 sink.padding=0;owner.offer_project(e,clock(3));wait(lambda:owner.project_snapshot().get('status')=='Playing');s=owner.project_snapshot();assert not s['meter_timing_available'] and s['levels'] is None;checks.append('Zero-padding estimate at exclusive submitted end has no invented current block')
 owner.offer_project(e,clock(4,False,False));wait(lambda:not owner.project_snapshot()['active']);owner.close();assert not owner.worker.is_alive() and not owner.server.is_alive() and owner.project_lane.exited() and sink.active==0 and sink.maximum==1;owner=None;checks.append('One output owner and actual worker/reader/context retirement')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,rows=rows,classification=__doc__),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if owner:owner.close()
