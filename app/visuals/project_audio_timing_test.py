"""Focused generated PCM/source/placement preservation; no device or production media."""
from pathlib import Path
from fractions import Fraction
from copy import deepcopy
from types import SimpleNamespace
import sys,json,wave,uuid,threading,math,hashlib,traceback
import numpy as np
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
from video_project import create,apply,pair,sample_at,ProjectError
from project_service import prepare_changes,write_project,read_project
from project_source import prepare_source
from project_audio_timing import natural_frames,ceiling
from project_evaluator import Evaluator
from project_mixer import Mixer
from studio_timeline_media import Placement
checks=[];details=[];cancel=threading.Event();uid=lambda:uuid.uuid4().hex

def fixture(n,rate):
 raw=(np.sin(np.arange(n)*2*np.pi*277/rate)*8192).astype(np.int16);raw[-min(17,n):]=24576;p=out/(str(rate)+'-'+str(n)+'.wav')
 with wave.open(str(p),'wb') as f:f.setparams((1,2,rate,0,'NONE','PCM'));f.writeframes(raw.tobytes())
 a=prepare_changes([dict(op='media.add',id=uid(),name=p.stem,kind='Audio',location=dict(kind='external',path=str(p)),provenance={})],None,cancel)[0]
 return a,raw.astype(np.float32)/32768

def document(a,fps,start=0,source=(0,1),rate=(1,1)):
 t=uid();c=uid();length=natural_frames(a['metadata'],fps,start=start,source_in=list(source),rate=list(rate));d=create('Audio sample proof',dict(fps=fps));d=apply(d,[a,dict(op='track.add',id=t,kind='audio'),dict(op='clip.add',id=c,asset=a['id'],track=t,start=start,duration=length,source_in=list(source),rate=list(rate),pad_end='silence')],uid())[0];return d,c

def render(d,fallback=False):
 e=Evaluator(d,'test',0);m=Mixer(force_fallback=fallback);blocks=[]
 try:
  for start in range(0,sample_at(d,e.end),2048):blocks.append(m.render(e.audio_span(start,min(2048,sample_at(d,e.end)-start))))
  peak=m.peak
 finally:m.close()
 assert m.budget.used==0
 return np.concatenate(blocks),peak

def native_reference(a):
 import av
 chunks=[]
 with av.open(a['location']['path']) as f:
  r=av.AudioResampler(format='fltp',layout='mono',rate=48000)
  for frame in f.decode(audio=0):chunks.extend(x.to_ndarray().reshape(-1) for x in r.resample(frame))
  chunks.extend(x.to_ndarray().reshape(-1) for x in r.resample(None))
 return np.concatenate(chunks)

try:
 for n,sr in [(47999,48000),(48000,48000),(48001,48000),(48017,48000),(44117,44100)]:
  a,raw=fixture(n,sr);assert a['metadata']['sample_count']==n and a['metadata']['duration_time']==[n,sr]
  reference=native_reference(a);assert len(reference)==ceiling(Fraction(n*48000,sr))
  for fps in ([30,1],[30000,1001],[24000,1001]):
   d,c=document(a,fps);left=sample_at(d,0);total=sample_at(d,d['clips'][0]['duration']);assert total>=len(reference)
   if d['clips'][0]['duration']>1:assert sample_at(d,d['clips'][0]['duration']-1)<len(reference)
   for fallback in (False,True):
    actual,peak=render(d,fallback);expected=raw if sr==48000 else np.interp(np.arange(len(reference))*sr/48000,np.arange(n),raw).astype(np.float32) if fallback else reference
    error=float(np.max(np.abs(actual[:len(expected),0]-expected)));assert error<1e-6,(n,sr,fps,fallback,error);assert np.array_equal(actual[:,0],actual[:,1]);assert np.count_nonzero(actual[len(expected):])==0
    if sr==48000:assert np.array_equal(actual[:n,0],raw) and np.all(actual[n-17:n,0]==.75)
    details.append(dict(n=n,sr=sr,fps=fps,fallback=fallback,out=d['clips'][0]['duration'],canonical=len(expected),padding=total-len(expected),max_error=error,peak=peak))
  s=prepare_source({k:a[k] for k in ('id','name','kind','location','sha256','metadata')},uid(),cancel);assert s['clips'][0]['duration']==natural_frames(a['metadata'],[30,1]) and s['clips'][0]['pad_end']=='silence'
  base=create('Placement',dict(fps=[30,1]));base=apply(base,[a,dict(op='track.add',id='a'*32,kind='audio')],uid())[0]
  p=object.__new__(Placement);p.document=base;p.frame=0;p.target='a'*32;p.range=None;p.channels='Both';p.library=False;p.mode='Normal';p.panel=SimpleNamespace(workspace=SimpleNamespace(state=lambda:dict(media={a['id']:dict(status='Ready')})))
  _,rows=p.plan([a]);assert rows[0]['row']['duration']==s['clips'][0]['duration'] and rows[0]['row']['pad_end']=='silence'
  p.range=dict(fps=[30,1],interval=[0,s['clips'][0]['duration']],natural_end=True);_,rows=p.plan([a]);assert rows[0]['row']['duration']==s['clips'][0]['duration']
  p.document['settings']['fps']=[60,1];_,rows=p.plan([a]);assert rows[0]['row']['duration']==natural_frames(a['metadata'],[60,1]);p.document['settings']['fps']=[30,1]
  if s['clips'][0]['duration']>2:
   p.range=dict(fps=[30,1],interval=[1,2],natural_end=False);_,rows=p.plan([a]);assert rows[0]['row']['duration']==1 and rows[0]['row']['source_in']==[1,30] and rows[0]['row']['pad_end']=='none'
 checks.append('30 native/fallback PCM cases across boundary tails,44100 resampling and three rational FPS; full Source/placement agreement and intentional trim')
 a,raw=fixture(48017,48000)
 for fps in ([30,1],[30000,1001],[24000,1001]):
  for start in (0,1,7,37):
   for speed in ([1,2],[1,1],[2,1]):
    d,c=document(a,fps,start,[17,48000],speed);clip=d['clips'][0];end=start+clip['duration'];threshold=ceiling(Fraction(start)*48000/Fraction(*fps)+Fraction(48000,1)/Fraction(*speed));assert sample_at(d,end)>=threshold
    if end>start+1:assert sample_at(d,end-1)<threshold
 checks.append('Minimal absolute rounded Out with nonzero source In/start and half/double rates')
 for speed in ([1,2],[2,1]):
  d,c=document(a,[30000,1001],7,[17,48000],speed);left=sample_at(d,7);end=sample_at(d,7+d['clips'][0]['duration']);positions=17+(np.arange(left,end)-float(Fraction(7)*48000/Fraction(30000,1001)))*float(Fraction(*speed))
  for fallback in (False,True):
   actual,_=render(d,fallback);grid=np.arange(len(raw)+(0 if fallback else 1));values=raw if fallback else np.append(raw,0);expected=np.interp(positions,grid,values).astype(np.float32);expected[(positions<0)|(positions>=len(raw))]=0;error=float(np.max(np.abs(actual[left:end,0]-expected)));assert error<1e-6,(speed,fallback,error)
   details.append(dict(case='fractional absolute start/source In/rate',fps=[30000,1001],start=7,source_in=[17,48000],rate=speed,fallback=fallback,max_error=error))
 checks.append('Nonzero fractional-frame start, source In and half/double-speed PCM versus declared native zero-neighbour/fallback held-neighbour interpolation')
 import av
 video=out/'five-frame-fractional.mp4'
 with av.open(str(video),'w') as container:
  stream=container.add_stream('libx264',rate=Fraction(24000,1001));stream.width=96;stream.height=64;stream.pix_fmt='yuv420p'
  for i in range(5):
   frame=av.VideoFrame.from_ndarray(np.full((64,96,3),i*40,np.uint8),format='rgb24');frame.pts=i;frame.time_base=Fraction(1001,24000)
   for packet in stream.encode(frame):container.mux(packet)
  for packet in stream.encode():container.mux(packet)
 va=prepare_changes([dict(op='media.add',id=uid(),name='Five fractional CFR frames',kind='Video',location=dict(kind='external',path=str(video)),provenance={})],None,cancel)[0];vs=prepare_source({k:va[k] for k in ('id','name','kind','location','sha256','metadata')},uid(),cancel);assert vs['clips'][0]['duration']==5 and vs['clips'][0]['pad_end']=='none';checks.append('Five-frame24000/1001 CFR video retains exactly5frames/no audio padding or picture extension')
 d,c=document(a,[30,1]);d=apply(d,[dict(op='clip.audio',id=c,values=dict(fade_in=2,fade_out=3,envelope=[[0,.5],[15,1.],[31,.2]]))],uid())[0];before=render(d)[0];split=apply(d,[dict(op='clip.split',id=c,at=15)],uid())[0];assert np.array_equal(before,render(split)[0]);assert split['clips'][1]['audio_window']['offset']==15
 path=out/'portable.zwv';saved=write_project(split,7,None,str(path),True,cancel);opened,revision,states,_=read_project(path,cancel);assert revision==7 and np.array_equal(before,render(opened)[0]);assert all(r['status']=='Ready' for r in states.values())
 for value in (3.0,3.5,True):
  try:apply(d,[dict(op='clip.audio',id=c,values=dict(fade_in=value))],uid());raise AssertionError('Strict model accepted noninteger fade')
  except ProjectError:pass
 changed=apply(d,[dict(op='clip.audio',id=c,values=dict(gain=.734,pan=-.123))],uid())[0];assert changed['clips'][0]['audio']['gain']==.734 and changed['clips'][0]['audio']['pan']==-.123
 checks.append('Native sample-identical split with retained fade/envelope origins; portable save/reopen; strict noninteger rejection and fractional controls preserved')
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,pcm_cases=details,portable=saved,limits='Generated bounded PCM; native resampler reference and fallback linear reference are separate. No encoded-output/listening/physical UI claim.'),indent=2),encoding='utf8');print('PASS',len(details),'PCM cases and',len(checks),'contract groups',out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
