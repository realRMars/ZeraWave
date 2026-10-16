"""Exact ephemeral range, owner idempotency and real bounded audio preparation.

Synthetic/offscreen: this does not establish audible or visible timing.
"""
from pathlib import Path
import sys,os,time,json,uuid,traceback
from copy import deepcopy
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[]
from video_project import create,apply,sample_at,ProjectError
from project_transport import Transport
from project_evaluator import Evaluator
from project_service import ProjectService
from project_audio_lane import AudioLane
def doc(fps):return apply(create(settings=dict(fps=fps)),[dict(op='track.add',id='1'*32,kind='graphics'),dict(op='caption.add',track='1'*32,start=0,duration=120,text='Clock')],uuid.uuid4().hex)[0]
def wait(fn):
 end=time.monotonic()+5
 while time.monotonic()<end:
  value=fn()
  if value:return value
  time.sleep(.002)
 raise AssertionError('Bounded preparation timeout')
try:
 rows=[]
 for fps in ([30,1],[30000,1001]):
  d=doc(fps);original=deepcopy(d);tick=[0];t=Transport(lambda:tick[0]);t.sync(d,'epoch',0);t.command('range_in',7);t.command('range_out',31);t.command('loop',1);t.command('play');assert t.frame==7
  for action,value in [('range_in',31),('range_out',7),('loop',True),('loop',2)]:
   prior=(t.range_in,t.range_out,t.loop)
   try:t.command(action,value);raise AssertionError('Invalid range accepted')
   except ProjectError:pass
   assert prior==(t.range_in,t.range_out,t.loop)
  gen=t.generation;t.audio_position(dict(sample_estimate=sample_at(d,31),status='Ended'));assert t.frame==7 and t.playing and t.generation==gen+1 and t.audio_seed==sample_at(d,7)
  t.audio_position(dict(sample_estimate=sample_at(d,10)+1,status='Playing'));t.command('pause');assert t.audio_seed==sample_at(d,10)+1 and not t.playing
  t.command('stop');assert t.frame==0 and not t.active and t.range_in==7 and t.range_out==31
  # Monotonic fallback also wraps without rounded FPS.
  t.command('play');tick[0]=2_000_000_000;assert 7<=t.state()['frame']<31
  t.sync(d,'replacement',0);assert t.range_in==0 and t.range_out==120 and not t.loop and t.frame==0 and d==original
  lane=AudioLane();e=Evaluator(d,'test',0);serial=lane.offer(e,('test',0,1,1,d['id']),sample_at(d,7),True,end=sample_at(d,31));packets=[]
  try:
   while True:
    packet=wait(lambda:lane.take(serial));assert not packet['error']
    if packet['end']:assert packet['start']==sample_at(d,31);break
    packets.append(packet);assert packet['start']+len(packet['pcm'])<=sample_at(d,31)
   assert sum(len(p['pcm']) for p in packets)==sample_at(d,31)-sample_at(d,7);assert lane.snapshot()['prepared_blocks']<=4
  finally:lane.close();wait(lane.exited)
  rows.append(dict(fps=fps,range=[7,31],samples=sum(len(p['pcm']) for p in packets),blocks=len(packets),worker_exited=lane.exited()))
 checks.append('Exact 30 and 30000/1001 In/Out, invalid atomic rejection, frame/sample loop restart, pause/Stop/replacement and bounded real PCM preparation at exclusive Out')
 service=ProjectService()
 try:
  def send(op,**values):
   state=service.state(False);return service.request(dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['project_id'],expected_command=state['command_revision'],**values))
  assert send('new')['ok'];assert send('batch',changes=[dict(op='track.add',id='1'*32,kind='graphics'),dict(op='caption.add',track='1'*32,start=0,duration=120,text='Owner')])['ok'];before=deepcopy(service.document);revision=service.revision;history=len(service.undo)
  assert send('transport',action='range_in',frame=7)['ok'];assert send('transport',action='range_out',frame=31)['ok'];assert send('transport',action='loop',frame=1)['ok'];assert not send('transport',action='range_out',frame=7)['ok'];assert service.document==before and service.revision==revision and len(service.undo)==history
  state=service.state(False);request=dict(op='transport',operation_id=uuid.uuid4().hex,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['project_id'],expected_command=state['command_revision'],action='seek',frame=12);assert service.request(request)['ok'];generation=service.transport.generation;assert service.request(request)['ok'] and service.transport.generation==generation
 finally:service.shutdown()
 checks.append('Real shared owner commands, revision guards/idempotent retry and range validation do not alter artwork/history or repeat transport')
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,rows=rows),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
