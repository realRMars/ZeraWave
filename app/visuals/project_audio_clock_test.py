"""Shared rational sample span/transport mapping; deterministic no-device checks."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import sys,json,uuid,time,traceback
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals')]
from video_project import create,apply,sample_at
from project_evaluator import Evaluator
from project_transport import Transport
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];rows=[]
try:
 for fps,end in (([30,1],11781),([30000,1001],2),([30000,1001],11781),([24,1],11781)):
  d=apply(create(settings=dict(fps=fps)),[dict(op='track.add',id='1'*32,kind='graphics'),dict(op='caption.add',track='1'*32,start=0,duration=end,text='Clock only')],uuid.uuid4().hex)[0];e=Evaluator(d,'clock',1);total=sample_at(d,end);cursor=0;count=0
  while cursor<total:
   p=e.audio_span(cursor,2048);assert p['start']==cursor and 1<=p['count']<=2048 and not p['audio'];cursor+=p['count'];count+=1
  assert cursor==total and e.audio_span(total,2048)['count']==0
  clock=Transport();clock.sync(d,'clock',1);clock.command('play');clock.audio_position()
  for frame in (0,1,end//2,end):
   sample=sample_at(d,frame);clock.audio_position(dict(sample_estimate=sample,status='Playing' if frame<end else 'Ended'));s=clock.state();assert s['frame']==frame and s['sample']==sample,(fps,frame,s)
  rows.append(dict(fps=fps,frames=end,total_samples=total,blocks=count,exact_end_frame=clock.state()['frame']))
 checks.append('Full392.7second frame/sample count and NTSC24/30 clocks cover all bounded audio spans; nearest sample inverse including rounded-down exclusive end is exact')
 d=apply(create(),[dict(op='track.add',id='1'*32,kind='graphics'),dict(op='caption.add',track='1'*32,start=0,duration=100,text='Clock')],uuid.uuid4().hex)[0];clock=Transport();clock.sync(d,'same',1);clock.command('play');clock.audio_position(dict(sample_estimate=5001,status='Playing'));assert clock.state()['sample']==5001;doc=deepcopy(d);doc['name']='Gain edit';discontinuity=clock.discontinuity;clock.sync(doc,'same',2);assert clock.state()['sample']==5001 and clock.audio_seed==5001 and clock.discontinuity==discontinuity and clock.state()['audio_status']=='Buffering';checks.append('Ordinary authoring revision retains exact subframe sample seed and explicit buffering until new audio binding applies')
 clock.command('seek',13);clock.audio_position();assert clock.state()['sample']==20800 and clock.state()['frame']==13 and clock.discontinuity==discontinuity+1;clock.audio_position(dict(sample_estimate=21417,status='Playing'));clock.command('pause');assert clock.audio_seed==21417;clock.audio_position();assert clock.state()['sample']==21417 and not clock.state()['playing'];clock.command('play');clock.audio_position();assert clock.state()['sample']==21417 and clock.state()['playing'];checks.append('Explicit seek resets exact canonical sample; pause/resume preserve subframe seed without artificial float-clock advancement')
 clock.command('stop');assert not clock.state()['active'] and clock.state()['frame']==0;clock.sync(doc,'replacement',3);assert clock.state()['sample']==0 and clock.state()['audio_status'] is None;checks.append('Stop/replacement releases project output-clock mode and restores independent rational clock state')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,rows=rows,classification=__doc__,limits='Numeric sample count/mapping; not whole-episode output, audible-clock or listening evidence'),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
