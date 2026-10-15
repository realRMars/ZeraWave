"""Actual owner/API export, protected files and process retirement; no device output."""
from pathlib import Path
import sys,os,json,time,uuid,threading,hashlib,traceback,wave
from copy import deepcopy
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
import numpy as np,av
from studio_control_client import ControlClient
from project_api import call
from project_cli import request
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);client=None;checks=[]
barrier=out/'export-barrier.flag';failure=out/'export-failure.flag';os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_TEST_EXPORT_BARRIER=str(barrier),ZERAWAVE_PROJECT_TEST_EXPORT_FAILURE=str(failure))
source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app/audio','app/visuals') for p in (ROOT/folder).glob('*.py')};(out/'SOURCE.json').write_text(json.dumps(source,indent=2),'utf8')
def state():return call(endpoint,dict(op='state'))['state']
def make(op,**args):
 s=state();return dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args)
def run(op,wait=True,**args):
 data=make(op,**args);r=request(endpoint,data,wait,120);assert r['ok'],r;return data,r
def terminal(key,seconds=120):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:
  r=call(endpoint,dict(op='operation_status',operation_id=key));o=r['outcome']
  if o['status'] not in ('saving','preparing','exporting'):return o
  time.sleep(.02)
 raise AssertionError('Pinned export did not drain')
try:
 w,h=384,216;x,y=np.meshgrid(np.arange(w),np.arange(h));rgba=np.stack([x%256,y%256,(x+y)%256,np.full_like(x,255)],2).astype(np.uint8);image=out/'pattern.png';assert QImage(rgba.tobytes(),w,h,QImage.Format_RGBA8888).save(str(image))
 audio=out/'stereo.wav';n=np.arange(48000*3);pcm=np.stack([.20*np.sin(2*np.pi*440*n/48000),.12*np.cos(2*np.pi*660*n/48000)],1)
 with wave.open(str(audio),'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(np.rint(pcm*32767).astype('<i2').tobytes())
 client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);run('new',name='Frozen export fixture',settings=dict(width=w,height=h));image_id,audio_id,vt,at,gt,ic,ac,caption=[uuid.uuid4().hex for _ in range(8)]
 edits=[dict(op='media.add',id=image_id,name='Native pattern',kind='Image',location=dict(kind='external',path=str(image))),dict(op='media.add',id=audio_id,name='Stereo channels',kind='Audio',location=dict(kind='external',path=str(audio))),dict(op='track.add',id=vt,kind='video',order=0),dict(op='track.add',id=at,kind='audio',order=1),dict(op='track.add',id=gt,kind='graphics',order=2),dict(op='clip.add',id=ic,asset=image_id,track=vt,start=0,duration=60),dict(op='clip.add',id=ac,asset=audio_id,track=at,start=0,duration=60,audio={'gain':.8}),dict(op='caption.add',id=caption,track=gt,start=5,duration=50,text='Editable café\nsecond line',style={'size':18,'bounds':[.03,.60,.94,.38],'padding':3,'line_spacing':24})]
 run('batch',label='Export fixture assembly',changes=edits);original=state()['document'];revision=state()['revision'];run('save',path=str(out/'before.zwv'));barrier.write_text('hold')
 export,r=run('export',wait=False,path=str(out/'frozen.mp4'));assert r['outcome']['status']=='exporting';frozen_revision=revision
 repeat=request(endpoint,export,False);assert repeat['outcome']['id']==export['operation_id'] and state()['revision']==revision
 denied=call(endpoint,make('export',path=str(out/'overflow.mp4')));assert not denied['ok'] and denied['error']['code']=='busy'
 closed=call(endpoint,make('close'));assert not closed['ok'] and closed['error']['code']=='busy'
 run('batch',label='Manual change during frozen export',changes=[dict(op='clip.audio',id=ac,values=dict(gain=.4)),dict(op='caption.edit',id=caption,values=dict(text='Changed café\nnew second line'))]);newer=state()['document'];newer_revision=state()['revision'];run('undo');assert state()['document']==original;run('redo');assert state()['document']==newer
 run('save',path=str(out/'newer.zwv'));saved_revision=state()['saved_revision'];barrier.unlink();result=terminal(export['operation_id']);assert result['status']=='exported',result;assert result['revision']==frozen_revision and state()['saved_revision']==saved_revision and state()['document']==newer
 assert result['result']['owned_resources_retired'];first_hash=hashlib.sha256((out/'frozen.mp4').read_bytes()).hexdigest();call(endpoint,dict(op='cancel',operation_id=export['operation_id']));assert terminal(export['operation_id'])['status']=='exported'
 checks.append('Real owner frozen export remains revision1 while caption/audio edits and exact Undo/Redo/Save progress; one-job pressure/duplicate/close protection and late-cancel durable wins')
 # Independent canonical mix and lossy channel/gain checks on the frozen revision.
 from project_evaluator import Evaluator
 from project_mixer import Mixer
 from video_project import sample_at
 mixer=Mixer();e=Evaluator(original,'reference',frozen_revision);parts=[];hasher=hashlib.sha256()
 for i in range(60):
  block=mixer.render(e.audio_span(i*1600,1600));hasher.update(block);parts.append(block)
 mixer.close();assert hasher.hexdigest()==result['result']['canonical_pcm_sha256'];expected=np.concatenate(parts)
 with av.open(str(out/'frozen.mp4')) as c:
  decoded=np.concatenate([f.to_ndarray().T for f in c.decode(audio=0)])[:len(expected)]
 middle=slice(2400,-2400);error=float(np.sqrt(np.mean((decoded[middle]-expected[middle])**2)));corr=[float(np.corrcoef(decoded[middle,j],expected[middle,j])[0,1]) for j in range(2)];assert error<.003 and min(corr)>.999,(error,corr)
 checks.append('Actual H264/AAC drain/full decode exact60frames/48k stereo samples with<1024AAC tail; canonical mix hash matches independent evaluator; lossy RMS/channel correlations bounded')
 # Failure and cancellation must preserve the previous good output and accepted work.
 failure.write_text('fail');bad=request(endpoint,make('export',path=str(out/'frozen.mp4')),True,120);assert not bad['ok'] and bad['outcome']['status']=='failed';assert hashlib.sha256((out/'frozen.mp4').read_bytes()).hexdigest()==first_hash and state()['document']==newer;failure.unlink()
 blocker=out/'not-a-directory';blocker.write_text('prior');bad=request(endpoint,make('export',path=str(blocker/'output.mp4')),True,120);assert not bad['ok'] and blocker.read_text()=='prior' and state()['document']==newer
 barrier.write_text('hold');cancelled,r=run('export',wait=False,path=str(out/'cancel.mp4'));call(endpoint,dict(op='cancel',operation_id=cancelled['operation_id']));o=terminal(cancelled['operation_id']);barrier.unlink();assert o['status']=='failed' and o['error']['code']=='cancelled' and not (out/'cancel.mp4').exists()
 run('export',path=str(out/'recovered.mp4'));assert state()['document']==newer
 checks.append('Controlled atomic-write fault plus actual invalid-directory write failure and held-worker cancellation preserve prior good hash/accepted edits; SAME owner subsequent export recovers')
 alias=out/'protected.mp4';os.link(image,alias);bad=request(endpoint,make('export',path=str(alias)),True);assert not bad['ok'] and bad['outcome']['error']['code']=='protected_source';assert hashlib.sha256(alias.read_bytes()).hexdigest()==hashlib.sha256(image.read_bytes()).hexdigest()
 run('close');run('open',path=str(out/'newer.zwv'));reopened=state()['document'];assert reopened['clips']==newer['clips'] and reopened['captions']==newer['captions'];run('export',path=str(out/'reopened.mp4'));checks.append('Source hardlink alias rejected; managed Save/close/Open reconstructs editable caption/gain and exports requested reopened revision')
 run('close');client.close();assert client.process.returncode==0 and client.protocol_error_count==0;client=None
 assert all(hashlib.sha256((ROOT/r).read_bytes()).hexdigest()==v for r,v in source.items());(out/'RESULT.json').write_text(json.dumps(dict(result='PASS',checks=checks,frozen=result,canonical_pcm_error_rms=error,channel_correlations=corr,source_unchanged=True),indent=2),'utf8');print(json.dumps(dict(result='PASS',groups=len(checks),folder=str(out)),indent=2))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if client is not None:
  for o in state().get('operations',[]):
   if o['status'] in ('saving','preparing','exporting'):call(endpoint,dict(op='cancel',operation_id=o['id']))
  if barrier.exists():barrier.unlink()
  end=time.perf_counter()+20
  while time.perf_counter()<end and any(o['status'] in ('saving','preparing','exporting') for o in state().get('operations',[])):time.sleep(.02)
  client.close(mode='discard',project_mode='discard')
