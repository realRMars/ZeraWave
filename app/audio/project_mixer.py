"""Bounded canonical stereo preparation; no device, GUI or document mutations.

Inputs are immutable sample-span plans from the shared visual project evaluator.
PyAV supplies native codec/resampling work; mono is duplicated after resampling,
so it is never attenuated by an implicit stereo downmix. SoundFile remains the
supported audio-file fallback. Each owning mixer thread alone calls its readers.
"""
from pathlib import Path
from fractions import Fraction
from collections import OrderedDict,deque
import hashlib,threading,time,math,os
import numpy as np

RATE=48000
BLOCK=2048
PCM_LIMIT=32*1024*1024
class Cancelled(InterruptedError):pass
class Budget:
 def __init__(self,limit=PCM_LIMIT):self.limit=limit;self.used=0;self.peak=0
 def take(self,n):
  if self.used+n>self.limit:raise MemoryError('Shared project audio cache is full; requested mix not prepared.')
  self.used+=n;self.peak=max(self.peak,self.used)
 def release(self,n):self.used-=n;assert self.used>=0
def clock_key(item,plan):
 clip=item['clip'];asset=item['asset'];rate=Fraction(*clip['rate']);intercept=Fraction(*clip['source_in'])-Fraction(clip['start'])/Fraction(*plan['fps'])*rate
 return os.path.normcase(str(Path(asset['location']['path']))),asset['sha256'],rate,intercept,asset['kind']
def check(cancel):
 if cancel.is_set():raise Cancelled('Obsolete project audio preparation')
def nearest(value):value=Fraction(value);return (value.numerator*2+value.denominator)//(value.denominator*2)

class SoundSource:
 """Existing SoundFile/PCM Decoder fallback, bounded arbitrary indexed slabs."""
 def __init__(self,asset):
  from studio_transport import Decoder
  self.decoder=Decoder(asset['location']['path']);self.bytes=0;self.eof=False;self.backend='SoundFile/PCM linear fallback';self.closed=False
 def read(self,start,step,count,cancel):
  check(cancel);d=self.decoder;positions=(float(start)+np.arange(count)*float(step)/RATE)*d.rate;lo=max(0,int(math.floor(positions.min())));hi=min(d.frames,int(math.ceil(positions.max()))+2);pcm=np.zeros((count,2),np.float32)
  if hi<=lo:return pcm
  d.position(lo);raw=d.raw(hi-lo);check(cancel)
  if d.channels==1:raw=np.repeat(raw,2,axis=1)
  if not np.isfinite(raw).all():raise ValueError('Nonfinite source audio')
  grid=lo+np.arange(len(raw));valid=(positions>=0)&(positions<d.frames)
  for channel in range(2):pcm[valid,channel]=np.interp(positions[valid],grid,raw[:,channel])
  self.bytes=d.buffer.nbytes;return pcm
 def close(self):self.decoder.close();self.bytes=0;self.closed=True

class NativeSource:
 def __init__(self,asset,budget):
  import av
  self.budget=budget;self.av=av;self.path=asset['location']['path'];self.asset=asset;self.container=av.open(self.path,mode='r',timeout=(2.,2.));self.chunks=deque();self.bytes=0;self.iterator=None;self.resampler=None;self.eof=False;self.flushed=False;self.last=None;self.closed=False;self.backend='PyAV native canonical resampling';self.seeks=0;self.decoded=0;self.temporary_bytes=0
  try:self.configure()
  except BaseException:self.container.close();raise
 def configure(self):
  if not self.container.streams.audio:raise ValueError('Source has no audio stream; mute/remove its audio clip or choose an audio source.')
  self.stream=self.container.streams.audio[0];codec=self.stream.codec_context;codec.thread_count=2;self.channels=len(codec.layout.channels)
  if self.channels not in (1,2) or not 8000<=codec.sample_rate<=192000:raise ValueError('Project audio supports actual mono/stereo streams at 8–192 kHz; no implicit multichannel downmix.')
  self.stream_start=Fraction(self.stream.start_time or 0)*self.stream.time_base
  self.origin=Fraction(*self.asset['metadata'].get('source_start',[0,1])) if self.asset['kind']=='Video' else self.stream_start
 def reset(self,target):
  # Audio seeks use stream timestamps. Signed demuxers may not support indexes;
  # that case decodes from the beginning within the same bounded work limit.
  if self.stream_start<0:
   if self.iterator is not None:self.container.close();self.container=self.av.open(self.path,mode='r',timeout=(2.,2.));self.configure()
  else:
   seek=max(self.stream_start,target-Fraction(1,5));self.container.seek(int(seek/self.stream.time_base),stream=self.stream,backward=True,any_frame=False)
  self.iterator=iter(self.container.decode(self.stream));self.resampler=self.av.AudioResampler(format='fltp',layout='mono' if self.channels==1 else 'stereo',rate=RATE);self.eof=False;self.flushed=False;self.last=None;self.budget.release(self.bytes);self.chunks.clear();self.bytes=0;self.seeks+=1
 def append(self,frame):
  if frame.pts is None:raise ValueError('Decoded audio has no sample timestamp; deterministic source alignment is unavailable.')
  if frame.samples>RATE*2:raise ValueError('Decoded audio frame exceeds bounded2second sample size; no samples dropped.')
  start=nearest(Fraction(frame.pts)*frame.time_base*RATE)
  # Containers such as Matroska quantize packet PTS to milliseconds. Continue
  # exact decoded sample counts within one declared timestamp tick, avoiding
  # invented holes/overlaps. Larger genuine timestamp gaps remain explicit.
  resolution=max(1,math.ceil(self.stream.time_base*RATE))
  if self.last is not None and abs(start-self.last)<=resolution:start=self.last
  required=frame.samples*2*4;self.budget.take(required);committed=False
  try:
   data=frame.to_ndarray().T
   if data.shape!=(frame.samples,self.channels):raise ValueError('Native audio layout changed; relink source.')
   if self.channels==1:data=np.repeat(data,2,axis=1)
   data=np.ascontiguousarray(data,np.float32);self.temporary_bytes=data.nbytes
   if not np.isfinite(data).all():raise ValueError('Decoded audio contains nonfinite samples.')
   self.chunks.append((start,data));self.bytes+=data.nbytes;self.last=start+len(data);self.decoded+=len(data);committed=True
  finally:
   self.temporary_bytes=0
   if not committed:self.budget.release(required)
 def read(self,start,step,count,cancel):
  check(cancel);first=(Fraction(start)+self.origin)*RATE;positions=float(first)+np.arange(count)*float(step);lo=math.floor(float(first));hi=math.ceil(float(first)+(count-1)*float(step))+2
  # Need one canonical neighbour beyond the highest fractional source position.
  if hi-lo>BLOCK*16+4:raise ValueError('Audio source slab exceeds bounded rate/count admission.')
  covered=self.chunks and self.chunks[0][0]<=lo and self.last>=hi
  forward=self.iterator is not None and self.chunks and self.chunks[0][0]<=lo and (self.last is None or self.last<=hi and lo-self.last<=RATE*2)
  if not covered and not forward:self.reset(Fraction(lo,RATE))
  began=time.perf_counter();frames=0
  while not self.eof and (self.last is None or self.last<hi):
   check(cancel);frame=next(self.iterator,None);frames+=1
   if frames>512 or time.perf_counter()-began>2.:raise ValueError('Audio decode exceeded512frames/2seconds; choose a more seekable source.')
   if frame is None:
    if not self.flushed:
     self.flushed=True
     for value in self.resampler.resample(None):self.append(value)
    self.eof=True;break
   for value in self.resampler.resample(frame):self.append(value)
   while self.chunks and self.chunks[0][0]+len(self.chunks[0][1])<lo-1:
    _,old=self.chunks.popleft();self.bytes-=old.nbytes;self.budget.release(old.nbytes)
  check(cancel);slab=np.zeros((hi-lo,2),np.float32)
  for at,data in self.chunks:
   left=max(lo,at);right=min(hi,at+len(data))
   if right>left:slab[left-lo:right-lo]=data[left-at:right-at]
  pcm=np.empty((count,2),np.float32);grid=np.arange(len(slab))
  for channel in range(2):pcm[:,channel]=np.interp(positions-lo,grid,slab[:,channel],left=0,right=0)
  while self.chunks and self.chunks[0][0]+len(self.chunks[0][1])<lo-1:
   _,old=self.chunks.popleft();self.bytes-=old.nbytes;self.budget.release(old.nbytes)
  return pcm
 def close(self):
  if self.closed:return
  self.container.close();self.closed=True;self.budget.release(self.bytes);self.chunks.clear();self.bytes=0;self.iterator=self.resampler=None

def curve(recipe,frames,length):
 if recipe['mute']:return np.zeros(len(frames),np.float32)
 gain=np.full(len(frames),recipe['gain'],np.float64)
 if recipe['fade_in']:gain*=np.clip(frames/recipe['fade_in'],0,1)
 if recipe['fade_out']:gain*=np.clip((length-frames)/recipe['fade_out'],0,1)
 if recipe['envelope']:
  points=np.asarray(recipe['envelope'],float);gain*=np.interp(frames,points[:,0],points[:,1])
 return gain.astype(np.float32)

class Mixer:
 """One preparation owner,16 active source readers/32MiB caches and scratch."""
 def __init__(self,force_fallback=False,pcm_limit=PCM_LIMIT):self.budget=Budget(pcm_limit);self.owner=threading.get_ident();self.readers={};self.verified=OrderedDict();self.closed=False;self.force_fallback=force_fallback;self.metrics={};self.peak=0
 def verify(self,asset,cancel):
  p=Path(asset['location']['path']);stat=p.stat();key=(str(p),asset['sha256']);stamp=(stat.st_size,stat.st_mtime_ns)
  if self.verified.get(key)==stamp:self.verified.move_to_end(key);return key
  h=hashlib.sha256()
  with p.open('rb') as handle:
   while True:
    check(cancel);block=handle.read(1024*1024)
    if not block:break
    h.update(block)
  if h.hexdigest()!=asset['sha256']:raise ValueError('Project audio source changed; relink deliberately: '+asset['name'])
  after=p.stat()
  if (after.st_size,after.st_mtime_ns)!=stamp:raise ValueError('Audio source changed during validation')
  self.verified[key]=stamp
  while len(self.verified)>64:self.verified.popitem(last=False)
  return key
 def render(self,plan,cancel=None):
  if self.closed or threading.get_ident()!=self.owner:raise RuntimeError('Mixer preparation requires its live owner thread.')
  # Conservative4MiB scratch reservation derives from16x2048 maximum source
  # step,192kHz fallback slabs, stereo conversion/grid/gain temporaries. Ready
  # PCM packets and opaque codec working buffers remain separate counters.
  reserve=4*1024*1024;self.budget.take(reserve);self.peak=max(self.peak,self.budget.peak)
  try:return self._render(plan,cancel)
  finally:
   self.budget.release(reserve);self.peak=max(self.peak,self.budget.peak);self.metrics.update(scratch_reserved_upper_bound_bytes=reserve,scratch_reservation_live_bytes=0,peak_owned_bytes=self.peak,owned_after_prepare_bytes=self.budget.used)
 def _render(self,plan,cancel=None):
  if self.closed or threading.get_ident()!=self.owner:raise RuntimeError('Mixer reader calls require its live owning preparation thread.')
  cancel=cancel or threading.Event();check(cancel);count=plan['count']
  if type(count) is not int or not 1<=count<=BLOCK:raise ValueError('Mix blocks contain1–2048 canonical samples.')
  items=plan['audio'];active=[r for r in items if not r['clip']['audio']['mute'] and not r['track']['audio']['mute']];needed=set()
  for item in active:self.verify(item['asset'],cancel);needed.add(clock_key(item,plan))
  if len(needed)>16:raise ValueError('Sixteen active project audio readers are supported; requested mix rejected.')
  for key in list(self.readers):
   if key not in needed:self.readers.pop(key).close()
  output=np.zeros((count,2),np.float32);began=time.perf_counter();decode_ms=0.;gain_ms=0.;scratch=output.nbytes
  for item in active:
   check(cancel);asset=item['asset'];clip=item['clip'];key=clock_key(item,plan);reader=self.readers.get(key)
   if reader is None:
    if self.force_fallback:
     if asset['kind']!='Audio':raise ValueError('Video audio requires PyAV; audio-file fallback remains available.')
     reader=SoundSource(asset)
    else:
     try:reader=NativeSource(asset,self.budget)
     except ImportError:
      if asset['kind']!='Audio':raise ValueError('Video audio requires installed PyAV.')
      reader=SoundSource(asset)
    self.readers[key]=reader
   before=time.perf_counter();pcm=reader.read(Fraction(*item['source_time']),Fraction(*clip['rate']),item['count'],cancel);decode_ms+=(time.perf_counter()-before)*1000
   cache=sum(r.bytes for r in self.readers.values());scratch=4*1024*1024
   if cache+scratch>self.budget.limit:raise MemoryError('Project canonical audio/cache/scratch exceeds32MiB; no mix samples dropped.')
   self.peak=max(self.peak,self.budget.peak);before=time.perf_counter();offset=item['offset'];global_samples=plan['start']+offset+np.arange(item['count']);fps=Fraction(*plan['fps']);local=(global_samples/RATE-float(Fraction(clip['start'])/fps))*float(fps)+clip['audio_window']['offset'];track_frames=global_samples/RATE*float(fps)
   gains=curve(clip['audio'],local,clip['audio_window']['duration'])*curve(item['track']['audio'],track_frames,plan['end_frame']);output[offset:offset+len(pcm)]+=pcm*gains[:,None];gain_ms+=(time.perf_counter()-before)*1000
  if not np.isfinite(output).all():raise ValueError('Nonfinite prepared project mix')
  self.metrics=dict(readers=len(self.readers),cache_bytes=sum(r.bytes for r in self.readers.values()),scratch_reserved_upper_bound_bytes=scratch,peak_owned_bytes=self.peak,limit=self.budget.limit,verified_sources=len(self.verified),decode_ms=decode_ms,gain_mix_ms=gain_ms,total_ms=(time.perf_counter()-began)*1000,frames=count,source_clipped=int(np.count_nonzero(abs(output)>1)),backends=sorted({r.backend for r in self.readers.values()}));return output
 def close(self):
  if self.closed:return
  if threading.get_ident()!=self.owner:raise RuntimeError('Mixer closes on its reader owner thread.')
  for reader in self.readers.values():reader.close()
  self.readers.clear();self.verified.clear();self.closed=True;self.metrics=dict(self.metrics,readers=0,cache_bytes=0,scratch_reservation_live_bytes=0,owned_after_prepare_bytes=0,closed=True)
