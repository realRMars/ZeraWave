"""Standalone document/owner history, portable identity and failure retention."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import sys,os,json,uuid,time,wave,threading,hashlib,shutil
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from video_project import create,validate,apply,frame_time,sample_at,ProjectError
from project_service import ProjectService
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];samples=[];service=ProjectService()
def req(op,wait=True,**args):
 state=service.state();data=dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['document']['id'] if state['document'] else None,expected_command=state['command_revision'],**args);start=time.perf_counter();result=service.request(data);samples.append(dict(op=op,callback_ms=(time.perf_counter()-start)*1000))
 if wait and result.get('outcome',{}).get('status') in ('preparing','saving'):
  end=time.perf_counter()+15
  while time.perf_counter()<end:
   service.poll();result=service.request(dict(op='operation_status',operation_id=data['operation_id']))
   if result['outcome']['status'] not in ('preparing','saving'):break
   time.sleep(.003)
  else:raise AssertionError('Preparation did not settle')
 return data,result
def accepted(result):assert result.get('outcome',{}).get('status') in ('accepted','durable'),result
try:
 req('new',name='Unicode episode — 测试 🎮')
 track,asset,clip,caption_track,caption=[uuid.uuid4().hex for _ in range(5)];path=out/'source.wav'
 with wave.open(str(path),'wb') as f:f.setparams((2,2,48000,0,'NONE','not compressed'));f.writeframes(b'\x01\0\x02\0'*48000*4)
 digest=hashlib.sha256(path.read_bytes()).hexdigest();changes=[dict(op='media.add',id=asset,name='Stereo source',kind='Audio',location=dict(kind='external',path=str(path)),sha256=digest),dict(op='track.add',id=track,name='Narration',kind='audio'),dict(op='track.add',id=caption_track,name='Captions',kind='graphics'),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=90,audio=dict(gain=.6,fade_in=6,fade_out=6,envelope=[[0,1.],[30,.4],[90,.8]])),dict(op='caption.add',id=caption,track=caption_track,start=0,duration=40,text='Exact editable text — 🎮')]
 data,result=req('batch',changes=changes,label='Assemble editable fixture');accepted(result);assert service.revision==1 and len(service.undo)==1;before=deepcopy(service.document)
 assert service.request(data)['outcome']==result['outcome'];assert service.revision==1 and len(service.undo)==1
 conflict=deepcopy(data);conflict['label']='Different content';assert service.request(conflict)['error']['code']=='operation_conflict';assert service.document==before
 stale=deepcopy(data);stale['operation_id']=uuid.uuid4().hex;assert service.request(stale)['error']['code']=='stale_revision';assert service.document==before
 checks.append('One named batch/one revision; same-ID replay no duplicate; ID conflict/stale revision preserve exact document')
 bad=[dict(op='project.rename',name='Must not leak'),dict(op='clip.trim',id=clip,start=90,end=40)];_,result=req('batch',changes=bad);assert result['outcome']['status']=='rejected' and service.document==before
 checks.append('Invalid final batch member does not partially accept earlier changes')
 _,result=req('batch',changes=[dict(op='clip.split',id=clip,at=35)],label='Split audio');accepted(result);left,right=service.document['clips'];assert left['duration']==35 and right['duration']==55 and right['source_in']==[7,6] and right['audio_window']==dict(offset=35,duration=90)
 split=deepcopy(service.document);req('undo');assert service.document==before;req('redo');assert service.document==split
 checks.append('Exact split source rational, preserved fade/envelope origin and full Undo/Redo')
 for fps in ([30,1],[30000,1001],[24000,1001]):
  d=create(settings=dict(fps=fps));assert frame_time(d,11781)==Fraction(11781)/Fraction(*fps)
  for frame in (0,1,2,11781,100000):assert abs(Fraction(sample_at(d,frame),48000)-frame_time(d,frame))<=Fraction(1,96000)
 checks.append('Absolute rational CFR/fractional FPS frame/sample boundaries never accumulate float drift')
 _,result=req('save',path=str(out/'first.zwv'),portable=True);accepted(result);assert not service.state()['dirty'];assert path.read_bytes()[:4]==b'RIFF'
 raw=json.loads((out/'first.zwv').read_text());assert raw['document']['media'][0]['location']['kind']=='relative';saved_revision=service.revision
 moved=out/'moved';moved.mkdir();shutil.copy2(out/'first.zwv',moved/'first.zwv');shutil.copytree(out/'first.media',moved/'first.media');_,result=req('open',path=str(moved/'first.zwv'));accepted(result);assert service.revision==saved_revision and service.document['clips']==split['clips'];assert service.media_state[asset]['status']=='Ready'
 checks.append('Portable saved revision retains all editable fields; moved folder resolves exact content identity')
 source_copy=Path(service.document['media'][0]['location']['path']);kept=source_copy.read_bytes();source_copy.write_bytes(b'changed same-name file');_,result=req('open',path=str(moved/'first.zwv'));accepted(result);assert service.media_state[asset]['status']=='Changed';source_copy.write_bytes(kept)
 checks.append('Same-named replacement is explicitly Changed, never silently selected as correct media')
 destination=out/'protected.zwv';_,result=req('save',path=str(destination));accepted(result);prior_good=destination.read_bytes();req('batch',label='Accepted before write failure',changes=[dict(op='project.rename',name='Unsaved failure fixture')]);accepted_before=deepcopy(service.document);os.environ['ZERAWAVE_PROJECT_TEST_WRITE_FAILURE']='1';_,result=req('save',path=str(destination));assert result['outcome']['status']=='failed' and result['outcome']['error']['code']=='preparation_failed' and 'Controlled project write failure before atomic replacement' in result['outcome']['error']['message'];assert destination.read_bytes()==prior_good and service.document==accepted_before and service.state()['dirty'];os.environ.pop('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE')
 checks.append('Real failed write before atomic replacement retains prior good output and accepted editable work')
 prior=deepcopy(service.document);service.history_limit=service.history_bytes;_,result=req('batch',changes=[dict(op='project.rename',name='No room')]);assert result['outcome']['status']=='rejected' and service.document==prior;service.history_limit=64*1024**2
 checks.append('History pressure rejects before acceptance without clearing retained Undo/Redo')
 _,result=req('save',path=str(path));assert result['outcome']['status']=='failed' and hashlib.sha256(path.read_bytes()).hexdigest()==digest
 checks.append('Save cannot overwrite referenced source; source bytes intact')
 # Complete real history remains owned at quiescence; do not require a zero.
 req('batch',changes=[dict(op='project.rename',name='Quiescent accepted edit')]);assert service.history_bytes>0 and not service.jobs;close_deadline=time.monotonic()+10
 while not service.can_shutdown(True):assert time.monotonic()<close_deadline;time.sleep(.003)
 assert service.recovery.future is None;service.shutdown()
 (out/'RESULT.json').write_text(json.dumps(dict(result='PASS',checks=checks,samples=samples,history_bytes=service.history_bytes,source={name:hashlib.sha256((ROOT/'app/visuals'/name).read_bytes()).hexdigest() for name in ['video_project.py','project_service.py']}),indent=2));print('PASS',len(checks),flush=True)
except BaseException:
 import traceback
 (out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 os.environ.pop('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE',None)
 if not service.closed:
  while not service.can_shutdown(True):time.sleep(.003)
  service.shutdown()
