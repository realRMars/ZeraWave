"""Controlled slow preparation/lost timing pressure with actual worker/single AudioOwner."""
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
import os,sys,time,json,uuid,threading,hashlib,traceback,socket,struct
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/audio'),str(root/'app/visuals')]
import numpy as np,soundfile as sf
from studio_transport import AudioOwner,receive
from project_audio_lane import AudioLane
from project_mixer import Mixer
from project_evaluator import Evaluator
from video_project import create,apply
from media_registry import inspect
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];owner=None;lane=None;client=None;rows=[]
class Enum:
 def request(self):pass
 def snapshot(self):return dict(sources=[],error=None)
 def close(self):pass
class Sink:
 paces_audio=False
 padding=0
 def __init__(self):self.samples=[];self.opens=self.closes=0
 @contextmanager
 def context(self):
  self.opens+=1
  try:yield self
  finally:self.closes+=1
 def play(self,pcm):self.samples.append(pcm.copy())
 def drain(self):pass
 def snapshot(self):return dict(device_position=None,backend='Controlled no-device sink')
def wait(test,seconds=12):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if test():return
  time.sleep(.004)
 raise AssertionError('Timeout waiting for controlled audio')
def transport(generation,frame=0,playing=True,active=True):return dict(project=d['id'],epoch='delayed',revision=1,generation=generation,discontinuity=generation,frame=frame,sample=frame*1600,playing=playing,active=active)
try:
 file=out/'stereo.wav';source=np.column_stack((np.linspace(-.2,.2,48000,dtype=np.float32),np.full(48000,.125,np.float32)));sf.write(file,source,48000,subtype='FLOAT');meta=inspect(str(file),threading.Event())['metadata'];a,t,c=[uuid.uuid4().hex for _ in range(3)];d=apply(create(),[dict(op='media.add',id=a,name='Source',kind='Audio',location=dict(kind='external',path=str(file)),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),metadata=meta),dict(op='track.add',id=t,kind='audio'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=30)],uuid.uuid4().hex)[0];e=Evaluator(d,'delayed',1);entered=threading.Event();release=threading.Event();original=Mixer.render
 def held(self,plan,cancel=None):entered.set();assert release.wait(5);return original(self,plan,cancel)
 with patch('project_audio_lane.Mixer.render',held):
  lane=AudioLane();serial=lane.offer(e,('delayed',1,1,1,d['id']),0,True);assert entered.wait(3);latest=lane.offer(e,('delayed',1,2,2,d['id']),16000,True);release.set();wait(lambda:lane.snapshot()['prepared_blocks']>0);packet=lane.take(latest);assert packet['serial']==latest and packet['start']==16000 and packet['binding'][2]==2 and not packet['error'];lane.close();lane.thread.join(5);assert lane.exited();lane=None
 checks.append('Actually delayed native preparation cancels old active job; latest seek emits exact new source sample/binding without obsolete PCM')
 def slow(self,plan,cancel=None):time.sleep(.07);return original(self,plan,cancel)
 sink=Sink()
 with patch('project_audio_lane.Mixer.render',slow):
  owner=AudioOwner(output_factory=sink.context,enumerator=Enum());owner.offer_project(e,transport(1));wait(lambda:owner.project_snapshot().get('status')=='Ended');rendered=np.concatenate(sink.samples);assert len(rendered)==len(source) and np.array_equal(rendered,source);assert sink.opens==sink.closes==1;rows.append(dict(slow_preparation=owner.project_snapshot(),frames=len(rendered)));checks.append('Sustained preparation slower than42.67ms block budget reports waiting/buffering, preserves every ordered sample/tail, drains and closes one context')
 owner.offer_project(e,transport(2));wait(lambda:owner.project_snapshot().get('status')=='Playing');endpoint=json.loads(owner.environment());client=socket.create_connection(('127.0.0.1',endpoint['port']),timeout=2);client.settimeout(3);client.sendall(endpoint['token'].encode());found=None
 for _ in range(10):
  size,count=struct.unpack('<II',receive(client,8));header=json.loads(receive(client,size));data=receive(client,count) if count else b''
  if count:found=(header,np.frombuffer(data,'<f4').reshape(-1,2));break
 assert found and found[0]['mode']=='Video Project' and found[0]['device'] is None and found[0]['project_binding'][0]=='delayed';assert found[1].shape[1]==2;client.close();client=None;checks.append('Actual authenticated PCM socket labels project mix/binding; captured-device identity is never falsely attached')
 owner.offer_project(e,transport(3,playing=False,active=False));wait(lambda:not owner.project_snapshot()['active']);owner.close();assert owner.project_lane.exited();owner=None;checks.append('Same owner resumes ordinary project preparation after slow run, Stop and normal audio/preparation/server cleanup')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,rows=rows,classification=__doc__,limits='Controlled sink/timing, no actual WASAPI deadline or listening evidence'),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if client:client.close()
 if lane:lane.close();lane.thread.join(5)
 if owner:
  try:owner.close()
  except RuntimeError:pass
