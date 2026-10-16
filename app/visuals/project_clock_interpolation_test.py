"""Deterministic block-report gaps: bounded frame estimates, starvation, pause and exact loop boundaries."""
from pathlib import Path
import sys,uuid,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project_transport import Transport
from video_project import create,apply
now=[0];clock=Transport(lambda:now[0]);track=uuid.uuid4().hex;document=apply(create(),[dict(op='track.add',id=track,kind='graphics'),dict(op='caption.add',track=track,start=0,duration=360,text='Clock')],uuid.uuid4().hex)[0];clock.sync(document,'bounded',0);clock.command('play');clock.audio_position(dict(status='Playing',sample_estimate=0,sample_estimate_ns=0,submitted_sample=4096))
frames=[]
for frame in range(3):
 now[0]=frame*1000000000//30+1;frames.append(clock.state()['frame'])
assert frames==[0,1,2],frames
now[0]=1000000000;assert clock.current_sample()==4096 and clock.position()==2
clock.audio_position(dict(status='Buffering',sample_estimate=4096,sample_estimate_ns=now[0],submitted_sample=8192));now[0]+=1000000000;assert clock.current_sample()==4096
clock.audio_position(dict(status='Playing',sample_estimate=4096,sample_estimate_ns=now[0],submitted_sample=8192));now[0]+=10000000;sample=clock.current_sample();position=clock.position();clock.command('pause');assert clock.audio_seed==sample and clock.position()==position;now[0]+=1000000000;assert clock.position()==position and clock.audio_seed==sample
clock.command('play');clock.audio_position(dict(status='Playing',sample_estimate=10000,submitted_sample=14000));now[0]+=1000000000;assert clock.current_sample()==10000
clock.command('range',[0,60]);clock.command('loop',1);clock.audio_position(dict(status='Playing',sample_estimate=95990,sample_estimate_ns=now[0],submitted_sample=96000));now[0]+=1000000000;assert clock.current_sample()==96000;generation=clock.generation;clock.audio_position(dict(status='Ended',sample_estimate=96000,submitted_sample=96000));assert clock.frame==0 and clock.playing and clock.generation==generation+1
print('PASS bounded audio-report interpolation: contiguous0/1/2, submitted ceiling, starvation hold, exact pause, legacy report hold, actual-ended loop boundary')
