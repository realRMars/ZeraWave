"""Latest-demand preparation on one codec owner, with explicit snapshot leases.

Pixels are native-resolution premultiplied RGBA, bottom up as in MediaFrames.
One consumer releases a taken snapshot before submitting its replacement.
No GL, document edits, clocks or device output run on this worker.
"""
from pathlib import Path
from collections import OrderedDict
from copy import deepcopy
from fractions import Fraction
from concurrent.futures import ThreadPoolExecutor
import threading,time,hashlib
from media_frames import DecoderWindow,MAX_CACHE_BYTES,MAX_FRAME_PIXELS,PlaneBudget
from media_registry import decode_image
from video_project import rational

RGBA_BUDGET=128*1024*1024
# Matched four-owner native-frame comparisons favour four codec threads on the
# supported device; legacy MediaFrames retains its two-thread default.
PROJECT_CODEC_THREADS=4
def source_metadata(path,cancel):
 from media_frames import backend
 av=backend()
 with av.open(str(path),mode='r',timeout=(2.,2.)) as container:
  stream=container.streams.video[0];start=Fraction(stream.start_time or 0)*stream.time_base
  length=Fraction(stream.duration)*stream.time_base if stream.duration is not None else Fraction(container.duration or 0,av.time_base)-start
  if cancel.is_set():raise InterruptedError('Source inspection cancelled')
  if length<=0:raise ValueError('No finite video duration after its start timestamp.')
  fps=stream.average_rate
  return dict(has_audio=bool(container.streams.audio),audio_channels=(container.streams.audio[0].codec_context.channels if container.streams.audio else 0),duration=float(length),duration_time=[length.numerator,length.denominator],container_frames=stream.frames or None,source_start=[start.numerator,start.denominator],time_base=[stream.time_base.numerator,stream.time_base.denominator],rational_fps=[fps.numerator,fps.denominator] if fps else None)
class DecodeLane:
 """One persistent worker owns one codec at a time; never concurrent access."""
 def __init__(self,index):self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Project video codec '+str(index));self.window=None
 def prepare(self,item,share,planes,cancel,cost):
  if cancel.is_set():raise InterruptedError('Obsolete project seek')
  if self.window is None:self.window=DecoderWindow(item['asset']['location']['path'],share,source_timestamps=True,codec_threads=PROJECT_CODEC_THREADS);self.window.demand_resync=True;self.window.pool=planes
  window=self.window;window.budget=share;window._evict(0.,1);start=Fraction(window.stream.start_time or 0)*window.stream.time_base;target=rational(item['source_time'])+start;result=window.get(float(target),cancel)
  if result is None:raise InterruptedError('Obsolete project seek')
  pts,(width,height,pixels)=result
  if width*height*4!=cost:raise ValueError('Video dimensions changed; prior document retained, relink required.')
  sar=float(window.stream.sample_aspect_ratio or 1)
  if item['asset']['metadata'].get('rotation',0) in (90,270):sar=1/sar
  return dict(width=width,height=height,data=pixels,pts=pts,source_start=[start.numerator,start.denominator],pixel_aspect=sar)
 def reset(self):
  if self.window is None:return
  # Run only after every previous task finished; disposal stays on its owner.
  def retire():
   if self.window:self.window.close();self.window=None
  self.pool.submit(retire).result()
 def close(self):
  try:self.reset()
  finally:self.pool.shutdown(wait=True)

class DecodeCancel:
 def __init__(self,request,failure):self.request=request;self.failure=failure
 def is_set(self):return self.request.is_set() or self.failure.is_set()

class Media:
 def __init__(self):
  self.condition=threading.Condition();self.pending=None;self.active=None;self.result=None;self.leased=None;self.stopping=False;self.serial=0;self.windows={};self.decode_lanes=[DecodeLane(i) for i in range(4)];self.images={};self.verified=OrderedDict();self.metrics={};self.planes=PlaneBudget();self.thread=threading.Thread(target=self.run,name='Project media preparation',daemon=True);self.thread.start()
 def submit(self,plan):
  with self.condition:
   if self.stopping:raise RuntimeError('Project media service is closing.')
   if self.leased is not None:raise RuntimeError('Release the prior prepared snapshot before replacing it.')
   self.serial+=1
   if self.active:self.active['cancel'].set()
   if self.pending:self.pending['cancel'].set()
   self.pending=dict(serial=self.serial,plan=deepcopy(plan),cancel=threading.Event(),requested=time.perf_counter());self.result=None;self.metrics=dict(self.metrics,ready_serial=None,pending=True);self.condition.notify_all();return self.serial
 def ready(self):
  # Readiness is metadata only. Pixels are available through the explicit
  # single-reader take/release contract, never an unaccounted borrowed mailbox.
  with self.condition:return dict(serial=self.result['serial']) if self.result else None
 def take(self):
  with self.condition:
   if self.leased is not None:raise RuntimeError('A prepared snapshot still has a reader.')
   self.leased,self.result=self.result,None;self.metrics=dict(self.metrics,ready_serial=None,reader_serial=self.leased['serial'] if self.leased else None);return self.leased
 def release(self,serial):
  with self.condition:
   if self.leased and self.leased['serial']!=serial:raise RuntimeError('Snapshot release identity mismatch.')
   self.leased=None;self.metrics=dict(self.metrics,reader_serial=None)
 def verify(self,asset,cancel):
  path=Path(asset['location']['path']);stat=path.stat();stamp=(stat.st_size,stat.st_mtime_ns);key=(str(path),asset['sha256'])
  if self.verified.get(key)==stamp:self.verified.move_to_end(key);return
  h=hashlib.sha256()
  with path.open('rb') as f:
   while True:
    if cancel.is_set():raise InterruptedError('Obsolete source verification')
    block=f.read(1024*1024)
    if not block:break
    h.update(block)
  if h.hexdigest()!=asset['sha256']:raise ValueError('Project source changed; relink deliberately: '+asset['name'])
  after=path.stat()
  if (after.st_size,after.st_mtime_ns)!=stamp:raise ValueError('Source changed during validation; accepted document retained.')
  self.verified[key]=stamp
  while len(self.verified)>64:self.verified.popitem(last=False)
 def key(self,item,plan):
  a=item['asset'];c=item['clip'];rate=rational(c['rate']);intercept=rational(c['source_in'])-Fraction(c['start'])/rational(plan['settings']['fps'])*rate
  return a['id'],a['sha256'],a['location']['path'],rate,intercept
 def accounting(self):
  values=[r['data'] for r in self.images.values()]+[lane.window.converted[1][2] for lane in self.windows.values() if lane.window and lane.window.converted]
  for result in (self.result,self.leased):
   if result:values.extend(r['data'] for r in result['images'].values())
  unique={id(b):len(b) for b in values}
  return dict(decoders=sum(lane.window is not None for lane in self.windows.values()),decoder_slots=len(self.windows),plane_bytes=self.planes.used,peak_plane_bytes=self.planes.peak,rgba_bytes=sum(unique.values()),rgba_limit=RGBA_BUDGET,conversion_temporaries=sum(lane.window.conversion_bytes for lane in self.windows.values() if lane.window),decode_temporary_planes=sum(lane.window.temporary_planes for lane in self.windows.values() if lane.window),codec_workers=sum(t.is_alive() for lane in self.decode_lanes for t in lane.pool._threads),codec_worker_limit=4,codec_threads_per_decoder=[lane.window.codec_threads for lane in self.windows.values() if lane.window],codec_thread_limit=4*PROJECT_CODEC_THREADS,verified_sources=len(self.verified),ready_serial=(self.result or {}).get('serial'),reader_serial=(self.leased or {}).get('serial'),pending=bool(self.pending))
 def prepare(self,job):
  plan=job['plan'];cancel=job['cancel'];items=plan['visual'];needed={};static=set();output={};costs={}
  for item in items:
   a=item['asset'];self.verify(a,cancel);meta=a['metadata'];w=meta.get('width',0);h=meta.get('height',0)
   if type(w) is not int or type(h) is not int or not 0<w*h<=MAX_FRAME_PIXELS:raise ValueError('Source has no supported native dimensions; relink it deliberately.')
   key=self.key(item,plan) if a['kind']=='Video' else (a['sha256'],a['location']['path']);costs[key]=w*h*4
   if a['kind']=='Video':needed[key]=item
   else:static.add(key)
  # Output plus the largest conservative RGBA conversion scratch is admitted
  # before allocation. Prior consumer was released; only active caches remain.
  if sum(costs.values())+3*max(costs.values(),default=0)>RGBA_BUDGET:raise MemoryError('Native project snapshots/conversion exceed 128 MiB; no resolution or samples reduced. Reduce simultaneous sources.')
  if len(needed)>4:raise ValueError('Four simultaneous project decoder clocks are supported; no samples dropped.')
  for key in list(self.windows):
   if key not in needed:self.windows.pop(key).reset()
  self.images={k:v for k,v in self.images.items() if k in static}
  share=MAX_CACHE_BYTES//max(1,len(needed))
  # The shared plane budget remains96MiB. Reserve worst-case concurrent RGBA
  # conversion before scheduling; supported combinations that do not fit that
  # reservation use the original serial route instead of a new lower limit.
  video_cost=sum(costs[key] for key in needed);parallel=sum(costs.values())+3*video_cost<=RGBA_BUDGET
  self.metrics=dict(self.metrics,decode_route='bounded parallel codec owners' if parallel else 'serial within original RGBA reservation',conversion_scratch_reservation=3*video_cost if parallel else 3*max(costs.values(),default=0))
  futures={};failure=threading.Event();combined=DecodeCancel(cancel,failure);primary=None
  for key,item in needed.items():
   lane=self.windows.get(key)
   if lane is None:lane=next(lane for lane in self.decode_lanes if lane not in self.windows.values());self.windows[key]=lane
   future=lane.pool.submit(lane.prepare,item,share,self.planes,combined,costs[key]);futures[key]=future
   if not parallel:
    try:needed[key]=future.result()
    except BaseException as exc:primary=exc;failure.set();break
  # Drain every submitted native task, including failures/cancellation, before
  # replacing resources or publishing one immutable reader snapshot. Secondary
  # resource errors cannot replace the first actual failure.
  for key,future in futures.items():
   try:needed[key]=future.result()
   except BaseException as exc:
    if primary is None:primary=exc;failure.set()
    elif exc is not primary:primary.add_note('Parallel codec retirement: '+type(exc).__name__+': '+str(exc))
  if primary is not None:raise primary
  for item in items:
   if cancel.is_set():raise InterruptedError('Obsolete project seek')
   a=item['asset'];clip=item['clip']
   if a['kind']=='Video':output[clip['id']]=needed[self.key(item,plan)]
   else:
    key=(a['sha256'],a['location']['path']);cached=self.images.get(key)
    if cached is None:
     meta,data=decode_image(a['location']['path'],cancel)
     if len(data)!=costs[key]:raise ValueError('Image dimensions changed; relink required.')
     cached=dict(width=meta['width'],height=meta['height'],data=data,pixel_aspect=1.);self.images[key]=cached
    output[clip['id']]=cached
  return dict(serial=job['serial'],plan=plan,images=output,requested=job['requested'],ready=time.perf_counter(),error='')
 def run(self):
  try:
   while True:
    with self.condition:
     self.condition.wait_for(lambda:self.pending or self.stopping)
     if self.stopping:break
     job=self.pending;self.pending=None;self.active=job
    try:result=self.prepare(job)
    except Exception as exc:result=dict(serial=job['serial'],plan=job['plan'],images={},error=type(exc).__name__+': '+str(exc),requested=job['requested'],ready=time.perf_counter())
    with self.condition:
     if not job['cancel'].is_set() and job['serial']==self.serial:self.result=result
     self.active=None;self.metrics=dict(self.metrics,**self.accounting());self.condition.notify_all()
    result=None;job=None
  finally:
   failures=[]
   for lane in self.decode_lanes:
    try:lane.close()
    except BaseException as exc:failures.append(str(exc))
   self.windows.clear();self.images.clear();self.verified.clear()
   if failures:self.metrics=dict(self.metrics,cleanup_errors=failures)
   with self.condition:self.metrics=dict(self.metrics,**self.accounting())
 def close(self):
  with self.condition:
   if self.leased:raise RuntimeError('A renderer/reader still owns the snapshot; release before closing.')
   self.stopping=True
   if self.active:self.active['cancel'].set()
   if self.pending:self.pending['cancel'].set()
   self.pending=None;self.result=None;self.condition.notify_all()
 def exited(self):return not self.thread.is_alive() and not self.planes.used and not self.metrics.get('cleanup_errors') and all(not t.is_alive() for lane in self.decode_lanes for t in lane.pool._threads)
