"""Actual preparation/AudioOwner/PCM bus; controlled sinks/capture, no hardware listening."""
from pathlib import Path
from contextlib import contextmanager
from collections import deque
import sys,time,json,threading,uuid,hashlib,traceback
import numpy as np,soundfile as sf
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/audio'),str(root/'app/visuals')]
from studio_transport import AudioOwner
from project_audio_lane import AudioLane
from project_evaluator import Evaluator
from video_project import create,apply,audio_defaults
from media_registry import inspect
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);owner=None;lane=None;checks=[];rows=[]
DEVICE=dict(kind='loopback',id='controlled',name='Controlled analysis source')
class Enumeration:
 def request(self):pass
 def snapshot(self):return dict(sources=[DEVICE],error=None)
 def close(self):pass
class Capture:
 def __init__(self):self.closed=False
 def start(self):pass
 def read(self,numframes=2048):time.sleep(numframes/48000);return np.full((numframes,2),.1,np.float32)
 def stop(self):self.closed=True
class Sink:
 paces_audio=False
 padding=0
 def __init__(self):self.active=0;self.maximum=0;self.opens=0;self.closes=0;self.blocks=deque(maxlen=128);self.fail_close=False
 @contextmanager
 def context(self):
  self.opens+=1;self.active+=1;self.maximum=max(self.maximum,self.active)
  try:yield self
  finally:
   self.closes+=1;self.active-=1
   if self.fail_close:raise RuntimeError('Controlled unconfirmed device release')
 def play(self,pcm):self.blocks.append(pcm.copy())
 def drain(self):pass
 def snapshot(self):return dict(backend='Controlled sink, no hardware',blocks=len(self.blocks),device_position=None)
def wait(test,seconds=8):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if test():return
  time.sleep(.005)
 raise AssertionError('Did not settle: '+str(owner.snapshot()['project_audio'] if owner else lane.snapshot()))
def transport(generation,frame=0,playing=True,active=True,revision=1):return dict(project=doc['id'],epoch='project',revision=revision,generation=generation,discontinuity=generation,frame=frame,sample=frame*1600,playing=playing,active=active)
try:
 file=out/'source.wav';sf.write(file,np.full((48000*3,2),.25,np.float32),48000,subtype='FLOAT');meta=inspect(str(file),threading.Event())['metadata'];a,t,c=[uuid.uuid4().hex for _ in range(3)];doc=apply(create(),[dict(op='media.add',id=a,name='Source',kind='Audio',location=dict(kind='external',path=str(file)),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),metadata=meta),dict(op='track.add',id=t,kind='audio'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=60,audio=dict(audio_defaults(),gain=.5))],uuid.uuid4().hex)[0];e=Evaluator(doc,'project',1)
 lane=AudioLane();serial=lane.offer(e,('project',1,1,1,doc['id']),0,True);wait(lambda:lane.snapshot()['prepared_blocks']==4);time.sleep(.1);assert lane.snapshot()['prepared_blocks']==4 and lane.snapshot()['prepared_bytes']==4*2048*8;rows.append(dict(saturation=lane.snapshot()));serial=lane.offer(e,('project',1,2,2,doc['id']),16000,True);wait(lambda:lane.snapshot()['prepared_blocks']>0);packet=lane.take(serial);assert packet['start']==16000 and packet['binding'][2]==2 and packet['serial']==serial;lane.offer(None,('closed',0,3,3,None),0,False);wait(lambda:lane.snapshot().get('retired'));assert not lane.snapshot()['prepared_blocks'];lane.close();lane.thread.join(5);assert lane.exited();lane=None;checks.append('Natural four-block saturation stops preparation; latest seek flushes old blocks and starts exact sample; cancellation retires workers/readers')
 sink=Sink();captures=[]
 def capture(device):result=Capture();captures.append(result);return result
 owner=AudioOwner(output_factory=sink.context,capture_factory=capture,enumerator=Enumeration());owner.submit('device',value=DEVICE);wait(lambda:owner.snapshot()['playing']);assert not owner.snapshot()['output'] and sink.opens==0
 owner.offer_project(e,transport(1));wait(lambda:owner.snapshot()['project_audio']['status']=='Playing');assert captures[-1].closed and owner.capture is None and sink.maximum==1;assert np.max(abs(sink.blocks[-1]-.125))<1e-6;checks.append('Explicit timeline Play stops analysis-only capture and uses existing single output with authored mix, never replaying captured PCM')
 owner.submit('volume',value=.5);wait(lambda:owner.snapshot()['volume']==.5);wait(lambda:len(sink.blocks)>3 and np.max(abs(sink.blocks[-1]-.0625))<1e-6);assert abs(owner.snapshot()['rms']-.125)<1e-6;owner.submit('mute',value=True);wait(lambda:owner.snapshot()['mute']);wait(lambda:not np.any(sink.blocks[-1]));assert abs(owner.snapshot()['rms']-.125)<1e-6;checks.append('Master output gain/mute modify output only; raw authored mix and existing analysis retain level')
 owner.offer_project(e,transport(2,frame=10,playing=False));wait(lambda:owner.snapshot()['project_audio']['status']=='Paused');assert not owner.snapshot()['output'];frozen=owner.snapshot()['pcm_frames'];time.sleep(.1);assert owner.snapshot()['pcm_frames']==frozen;owner.submit('mute',value=False);owner.offer_project(e,transport(3,frame=20));wait(lambda:owner.snapshot()['project_audio']['status']=='Playing' and owner.snapshot()['project_audio']['binding'][2]==3);assert owner.snapshot()['project_audio']['submitted_sample']>=32000;rows.append(dict(seek=owner.snapshot()['project_audio']));checks.append('Pause releases native queue and freezes packets; explicit seek/play prepares exact new binding in the same owner')
 owner.submit('open',path=str(file));wait(lambda:'Timeline owns' in owner.snapshot()['error']);assert owner.snapshot()['project_audio']['active'] and sink.maximum==1;owner.offer_project(e,transport(4,playing=False,active=False));wait(lambda:not owner.snapshot()['project_audio']['active'] and owner.capture is not None);assert owner.snapshot()['mode']=='Device Listening' and owner.snapshot()['playing'] and not owner.snapshot()['output'];checks.append('Legacy actions reject while project owns output; Stop restores the retained Device Listening source without output replay')
 owner.submit('open',path=str(file));wait(lambda:owner.snapshot()['mode']=='Audio File');owner.submit('play');wait(lambda:owner.snapshot()['output']);saved=owner.decoder;owner.offer_project(e,transport(5));wait(lambda:owner.snapshot()['project_audio']['status']=='Playing' and owner.snapshot()['project_audio']['binding'][2]==5);assert owner.decoder is saved;owner.offer_project(e,transport(6,playing=False,active=False));wait(lambda:not owner.snapshot()['project_audio']['active'] and owner.snapshot()['status']=='Playing');assert owner.decoder is saved and sink.maximum==1;checks.append('Audio File decoder/settings remain parked during project output and resume from retained position on Stop; maximum one device context')
 owner.offer_project(e,transport(7));wait(lambda:owner.snapshot()['project_audio']['status']=='Playing');sink.fail_close=True;opens=sink.opens;owner.offer_project(e,transport(8,frame=5));wait(lambda:owner.blocked);assert 'unconfirmed' in owner.snapshot()['project_audio']['error'].lower();owner.offer_project(e,transport(9));time.sleep(.15);assert sink.opens==opens;checks.append('Actual controlled output-context close failure retains ownership/error and blocks replacement, including later Play')
 try:owner.close()
 except RuntimeError:assert owner.output_release_error is not None
 assert not owner.worker.is_alive() and not owner.server.is_alive() and owner.project_lane.exited();owner=None;checks.append('Owned preparation/audio/PCM-server threads exit; unconfirmed hardware release remains explicit')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,rows=rows,classification=__doc__,source_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),maximum_output_contexts=sink.maximum),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if lane:lane.close();lane.thread.join(5)
 if owner:
  try:owner.close()
  except RuntimeError:pass
