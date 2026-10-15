"""Standalone shared evaluator/audio recipe checks; decoded numeric, no device/listening."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import os,sys,time,json,hashlib,uuid,threading,traceback
root=Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/audio'),str(root/'app/visuals')];os.environ['QT_QPA_PLATFORM']='offscreen'
import numpy as np,soundfile as sf,av
from video_project import create,apply,audio_defaults,sample_at
from project_evaluator import Evaluator
from project_mixer import Mixer,RATE,BLOCK
from media_registry import inspect
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];samples=[];m=None
def make(path,data,rate):sf.write(path,data,rate,subtype='FLOAT');return inspect(str(path),threading.Event())['metadata']
def base(path,meta,seconds=1):
 a,t,c=[uuid.uuid4().hex for _ in range(3)];d=apply(create(),[dict(op='media.add',id=a,name=path.name,kind='Audio',location=dict(kind='external',path=str(path)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=meta),dict(op='track.add',id=t,name='Narration',kind='audio'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=round(seconds*30))],uuid.uuid4().hex)[0];return d,a,t,c
def render_all(d,fallback=False):
 global m
 e=Evaluator(d,'mix',3);m=Mixer(force_fallback=fallback);parts=[];cursor=0;total=sample_at(d,e.end)
 try:
  while cursor<total:
   began=time.perf_counter();pcm=m.render(e.audio_span(cursor,min(BLOCK,total-cursor)));samples.append(dict(ms=(time.perf_counter()-began)*1000,metrics=deepcopy(m.metrics)));parts.append(pcm);cursor+=len(pcm)
  return np.concatenate(parts),deepcopy(m.metrics)
 finally:m.close();assert m.metrics['readers']==0 and m.metrics['cache_bytes']==0 and m.budget.used==0;m=None
try:
 source=np.column_stack((np.linspace(-.4,.4,RATE,dtype=np.float32),np.full(RATE,.125,np.float32)));path=out/'stereo.wav';meta=make(path,source,RATE);d,a,t,c=base(path,meta);pcm,metrics=render_all(d);assert np.array_equal(source,pcm),(np.max(abs(source-pcm)),source.shape,pcm.shape);checks.append('Native48k stereo sample order/channel preservation and full tail are byte-exact through shared evaluator')
 changed=apply(d,[dict(op='clip.audio',id=c,values=dict(gain=.5,fade_in=3,fade_out=3,envelope=[[0,1],[15,.25],[30,1]])),dict(op='track.audio',id=t,values=dict(gain=.8))],uuid.uuid4().hex)[0];pcm,_=render_all(changed);frames=np.arange(RATE)/1600;gain=.4*np.minimum(frames/3,1)*np.minimum((30-frames)/3,1)*np.interp(frames,[0,15,30],[1,.25,1]);expected=source*gain[:,None];assert np.max(abs(expected-pcm))<2e-7;checks.append('Clip/track gain, fades and editable ducking envelope match sample reference, with no output-master gain baked in')
 split=apply(changed,[dict(op='clip.split',id=c,at=13)],uuid.uuid4().hex)[0];after,_=render_all(split);assert np.array_equal(after,pcm),np.max(abs(after-pcm));checks.append('Split retains exact source samples and original envelope/fade coordinate window')
 muted=apply(changed,[dict(op='track.audio',id=t,values=dict(mute=True))],uuid.uuid4().hex)[0];silent,stats=render_all(muted);assert not np.any(silent) and stats['readers']==0;checks.append('Track mute makes exact silence and retires inactive readers; authored sources/history remain')
 mono=np.full(RATE//2,.2,np.float32);path=out/'mono24.wav';meta=make(path,mono,24000);d,a,t,c=base(path,meta);native,_=render_all(d);fallback,_=render_all(d,True);print('MONO_DIAGNOSTIC',native.min(),native.max(),fallback.min(),fallback.max(),float(np.max(abs(native[100:-100]-.2))),np.flatnonzero(abs(native[:,0]-.2)>1e-6)[:30],flush=True);assert np.array_equal(native[:,0],native[:,1]) and np.max(abs(native[100:-100]-.2))<3e-6 and np.max(abs(fallback-.2))<1e-6;resampler=av.AudioResampler(format='fltp',layout='mono',rate=RATE);reference=[]
 with av.open(str(path)) as container:
  for f in container.decode(audio=0):reference.extend(r.to_ndarray().T for r in resampler.resample(f))
  reference.extend(r.to_ndarray().T for r in resampler.resample(None))
 reference=np.concatenate(reference);assert np.array_equal(native[:,0],reference[:,0]) and len(reference)==RATE
 checks.append('Actual24k mono is duplicated without3dB attenuation; native resampling and SoundFile fallback preserve intended constant level')
 source=np.column_stack((.2*np.sin(np.arange(RATE*2)*2*np.pi*400/RATE),.1*np.sin(np.arange(RATE*2)*2*np.pi*1000/RATE))).astype(np.float32);path=out/'rates.wav';meta=make(path,source,RATE);d,a,t,c=base(path,meta);d=apply(d,[dict(op='clip.add',asset=a,track=t,start=0,duration=30,source_in=[1,2],rate=[1,2],audio=dict(audio_defaults(),gain=.5))],uuid.uuid4().hex)[0];native,stats=render_all(d);positions=RATE*.5+np.arange(RATE)*.5;expected=source[:RATE]+.5*np.column_stack([np.interp(positions,np.arange(len(source)),source[:,i]) for i in range(2)]);assert np.max(abs(native-expected))<2e-7 and stats['readers']==2;checks.append('Simultaneous same-file different source clocks/rational rates use deliberate independent readers and match interpolation reference')
 e=Evaluator(d,'seek',4);m=Mixer();original=m.render(e.audio_span(12000,1024));m.render(e.audio_span(0,1024));again=m.render(e.audio_span(12000,1024));assert np.array_equal(original,again);m.close();assert m.budget.used==0;m=None;checks.append('Repeated forward/backwards seeks return exact requested PCM in one mixer and release cache ownership')
 # Actual video/audio offset fixture; compare timestamps without hidden channel assumptions.
 video=out/'offset.mkv'
 with av.open(str(video),'w') as container:
  v=container.add_stream('ffv1',rate=10);v.width=32;v.height=32;v.pix_fmt='yuv420p';v.time_base=Fraction(1,1000);audio=container.add_stream('pcm_f32le',rate=RATE);audio.layout='stereo'
  for i in range(20):
   f=av.VideoFrame.from_ndarray(np.zeros((32,32,3),np.uint8),format='rgb24');f.pts=5000+i*100;f.time_base=Fraction(1,1000)
   for packet in v.encode(f):container.mux(packet)
  for packet in v.encode():container.mux(packet)
  for at in range(0,RATE,1024):
   n=min(1024,RATE-at);data=np.full((2,n),.25,np.float32);f=av.AudioFrame.from_ndarray(data,format='fltp',layout='stereo');f.sample_rate=RATE;f.time_base=Fraction(1,RATE);f.pts=RATE*5+RATE//2+at
   for packet in audio.encode(f):container.mux(packet)
  for packet in audio.encode():container.mux(packet)
 meta=inspect(str(video),threading.Event())['metadata'];from project_media import source_metadata
 meta.update(source_metadata(video,threading.Event()));d,a,t,c=base(video,meta,2);d['media'][0]['kind']='Video';pcm,_=render_all(d);print('OFFSET_DIAGNOSTIC',np.flatnonzero(pcm[:,0])[:5],np.flatnonzero(pcm[:,0])[-5:],np.max(abs(pcm[RATE//2+100:RATE*3//2-100]-.25)),np.flatnonzero(pcm[RATE//2+100:RATE*3//2-100,0]!=.25)[:30],flush=True);assert not np.any(pcm[:RATE//2]) and np.max(abs(pcm[RATE//2+100:RATE*3//2-100]-.25))<1e-6 and not np.any(pcm[RATE*3//2+100:]);checks.append('Actual combined video source start5s/audio start5.5s yields exact0.5s leading gap and aligned native stereo game audio')
 # Controlled pressure leaves accepted document alone and can recover after drain.
 m=Mixer(pcm_limit=1024);e=Evaluator(d,'pressure',3)
 try:m.render(e.audio_span(RATE//2,1024));raise AssertionError('PCM pressure accepted')
 except MemoryError:pass
 m.budget.limit=32*1024*1024;recovered=m.render(e.audio_span(RATE//2,1024));assert np.max(abs(recovered-.25))<1e-6;m.close();assert m.budget.used==0;m=None;recovered,_=render_all(d);assert np.array_equal(recovered,pcm);checks.append('Shared PCM byte pressure rejects preparation explicitly; complete cache release and fresh bounded mixer recover identical accepted recipes')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,samples=samples,classification=__doc__,fixtures={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ('.wav','.mkv')}),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if m:m.close()
