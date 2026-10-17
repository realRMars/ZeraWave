"""Bounded thumbnails and complete incremental raw waveforms.

One worker,32pending,128entries/8MiB cache and32MiB Mixer budget.
No device output,artwork edit or preview/export quality change.
"""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from copy import deepcopy
import threading,time
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QImage,QColor,QPen
from timeline_waveform import OVERVIEW_BINS,DETAIL_BINS,covered
class Cancellation:
 def __init__(self,global_cancel,local):self.global_cancel=global_cancel;self.local=local
 def is_set(self):return self.global_cancel.is_set() or self.local.is_set()
 def wait(self,seconds):return self.local.wait(seconds) or self.global_cancel.is_set()
class Decorations:
 def __init__(self,canvas):
  self.canvas=canvas;self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Timeline decorations');self.future=None;self.active=None;self.active_job=None;self.pending=OrderedDict();self.cache=OrderedDict();self.bytes=0;self.closed=False;self.cancel=threading.Event();self.state={};self.cleanup=None;self.domains={};self.wanted={};self.metrics=dict(requested=0,completed=0,waveforms_completed=0,scanned_samples=0,superseded=0,cancelled=0,stale_results=0,cache_bytes=0,cache_peak=0,pending_peak=0,cache_limit=8*1024*1024,pending_limit=32,cache_entries_limit=128,worker_count=1,quantum_max_ms=0.,reader_budget_peak=0)
 @staticmethod
 def domain(row,asset,document,kind):
  metadata=asset.get('metadata',{});return (asset['id'],asset['sha256'],asset['location']['path'],metadata.get('bytes'),metadata.get('mtime_ns'),kind,str(Fraction(*row['source_in'])),str(Fraction(*row['rate'])),row['duration'],str(Fraction(*document['settings']['fps'])))
 def valid(self,key):return self.domains.get(key[0])==key[1]
 def set_document(self,document):
  assets={a['id']:a for a in document['media']};tracks={t['id']:t for t in document['tracks']};domains={row['id']:self.domain(row,assets[row['asset']],document,'wave' if tracks[row['track']]['kind']=='audio' else 'thumb') for row in document['clips']}
  if domains==self.domains:return
  self.domains=domains
  for key in list(self.pending):
   if not self.valid(key):self.pending.pop(key);self.metrics['superseded']+=1
  for key in list(self.cache):
   if not self.valid(key):self.bytes-=self.cache.pop(key)[1]
  for key in list(self.wanted):
   if key not in domains:self.wanted.pop(key)
  if self.active is not None and not self.valid(self.active):self.active_job['cancel'].set()
 def want(self,clip,keys):
  self.wanted[clip]=set(keys)
  for key in list(self.pending):
   if key[0]==clip and key not in keys:self.pending.pop(key);self.metrics['superseded']+=1
  if self.active is not None and self.active[0]==clip and self.active not in keys:self.active_job['cancel'].set()
 def enqueue(self,key,job):
  if key==self.active or key in self.pending:return
  self.pending[key]=job
  while len(self.pending)>32:self.pending.popitem(last=False);self.metrics['superseded']+=1
  self.metrics['pending_peak']=max(self.metrics['pending_peak'],len(self.pending))
 def request(self,key,job):
  if self.closed:return
  result=self.cache.get(key,(None,0))[0]
  if result is not None:
   self.cache.move_to_end(key)
   if result.get('complete',True) or result.get('error'):return result
   job=dict(job,progress=result)
  self.enqueue(key,job);return result
 def draw(self,p,rect,row,document):
  asset=next(a for a in document['media'] if a['id']==row['asset']);track=next(t for t in document['tracks'] if t['id']==row['track']);fps=Fraction(*document['settings']['fps']);rate=Fraction(*row['rate']);source=Fraction(*row['source_in']);kind='wave' if track['kind']=='audio' else 'thumb';domain=self.domain(row,asset,document,kind);self.domains[row['id']]=domain;base=dict(asset=deepcopy(asset),source=source,rate=rate,fps=fps,kind=kind)
  if kind=='thumb':
   key=(row['id'],domain,'thumb');self.want(row['id'],[key]);result=self.request(key,base)
   if result and result.get('image'):
    image=result['image'];w=min(96,rect.width()-18);p.drawImage(QRectF(rect.left()+9,rect.top()+21,w,max(1,rect.height()-23)),image)
   elif result and result.get('error'):p.drawText(rect.adjusted(9,22,-9,-1),'Thumbnail unavailable')
   return
  seconds=Fraction(row['duration'])/fps;visible=self.canvas.visibleRegion().boundingRect();left=max(rect.left()+9,visible.left());right=min(rect.right()-9,visible.right())
  if left>=right:return
  jobs=[];pixels_per_second=self.canvas.scale*float(fps)
  if pixels_per_second<64:
   key=(row['id'],domain,'overview');jobs.append((key,dict(base,span=seconds,bins=OVERVIEW_BINS),rect.left()+9,max(1,rect.width()-18)))
  else:
   first=max(0,int((left-rect.left())/(pixels_per_second*2)));last=min(int((seconds+1)//2)+1,int((right-rect.left())/(pixels_per_second*2))+1)
   for chunk in range(first,min(last,first+32)):
    length=min(Fraction(2),seconds-chunk*2)
    if length<=0:continue
    key=(row['id'],domain,'detail',chunk);jobs.append((key,dict(base,source=source+chunk*2*rate,span=length,bins=DETAIL_BINS),rect.left()+chunk*2*pixels_per_second,float(length)*pixels_per_second))
  self.want(row['id'],[j[0] for j in jobs]);center=rect.top()+rect.height()*.68;height=rect.height()*.26
  for key,job,x,width in jobs:
   result=self.request(key,job);error=result and result.get('error');bins=job['bins'];p.setPen(QPen(QColor('#e6a89b' if error else '#748d99'),1,Qt.DashLine));p.drawLine(round(max(left,x)),round(center),round(min(right,x+width)),round(center))
   if result and 'peaks' in result:
    p.setPen(QPen(QColor('#bddfd0'),1))
    for i,value in enumerate(result['peaks']):
     px=x+width*(i+.5)/bins
     if left<=px<=right and covered(result,i):
      amplitude=max(.5,height*min(1,float(value)));p.drawLine(round(px),round(center-amplitude),round(px),round(center+amplitude))
   if error:p.drawText(QRectF(max(left,x)+3,rect.top()+21,min(250,right-left),18),'Waveform unavailable')
   elif not result or not result['complete']:
    percent=round(100*result['done']/result['total']) if result else 0;p.drawText(QRectF(max(left,x)+3,rect.top()+21,min(230,right-left),18),'Waveform preparing '+str(percent)+'%')
 def build(self,job):
  cancel=Cancellation(self.cancel,job['cancel'])
  if cancel.is_set():raise InterruptedError()
  if job['kind']=='wave':
   from timeline_waveform import prepare
   return prepare(self.state,job,cancel)
  from project_media import Media
  media=self.state.get('media')
  if media is None:media=Media();self.state['media']=media
  plan=dict(settings=dict(fps=[job['fps'].numerator,job['fps'].denominator]),visual=[dict(clip=dict(id='timeline-thumbnail',rate=[1,1],source_in=[0,1],start=0),asset=job['asset'],source_time=[job['source'].numerator,job['source'].denominator])]);serial=media.submit(plan);end=time.monotonic()+8
  while not media.ready():
   if cancel.wait(.005) or time.monotonic()>end:media.submit(dict(visual=[]));raise InterruptedError('Thumbnail superseded or preparation deadline')
  result=media.take()
  try:
   if result['error']:raise ValueError(result['error'])
   frame=result['images']['timeline-thumbnail'];image=QImage(frame['data'],frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).scaled(96,54,Qt.KeepAspectRatio,Qt.SmoothTransformation);return dict(image=image)
  finally:media.release(serial)
 def store(self,key,result):
  cost=result['image'].sizeInBytes() if result.get('image') else result['peaks'].nbytes+1024 if 'peaks' in result else len(result.get('error',''))+1024
  if key in self.cache:self.bytes-=self.cache.pop(key)[1]
  self.cache[key]=(result,cost);self.bytes+=cost
  while self.bytes>8*1024*1024 or len(self.cache)>128:
   _,(_,old)=self.cache.popitem(last=False);self.bytes-=old
  self.metrics['cache_peak']=max(self.metrics['cache_peak'],self.bytes)
 def poll(self):
  if self.future and self.future.done():
   key=self.active;job=self.active_job
   try:result=self.future.result()
   except InterruptedError:self.metrics['cancelled']+=1;result=None
   except Exception as exc:result=dict(error=str(exc)[:1024])
   self.future=None;self.active=None;self.active_job=None;wanted=key in self.wanted.get(key[0],set())
   if result and not self.closed and self.valid(key) and wanted and not job['cancel'].is_set():
    self.store(key,result);self.metrics['completed']+=1;self.metrics['scanned_samples']+=result.get('scanned',0);self.metrics['quantum_max_ms']=max(self.metrics['quantum_max_ms'],result.get('work_ms',0));self.metrics['reader_budget_peak']=max(self.metrics['reader_budget_peak'],result.get('reader_budget_peak',0))
    if result.get('complete'):self.metrics['waveforms_completed']+=1
    elif 'peaks' in result:self.enqueue(key,dict(job,progress=result))
    self.canvas.update()
   elif result:self.metrics['stale_results']+=1
  if not self.closed and self.future is None and self.pending:
   key,job=self.pending.popitem(last=False)
   if self.valid(key) and key in self.wanted.get(key[0],set()):
    self.active=key;self.active_job=dict(job,cancel=threading.Event());self.metrics['requested']+=1;self.future=self.pool.submit(self.build,self.active_job)
  if self.closed and self.future is None and self.cleanup is None:self.cleanup=self.pool.submit(self.release)
  if self.cleanup and self.cleanup.done():self.cleanup.result();self.pool.shutdown(wait=False,cancel_futures=True)
  self.metrics.update(cache_bytes=self.bytes,pending=len(self.pending),in_flight=int(self.future is not None))
 def release(self):
  media=self.state.pop('media',None)
  if media:
   media.close()
   while not media.exited():time.sleep(.005)
  mixer=self.state.pop('mixer',None)
  if mixer:mixer.close();self.metrics['retired_reader_budget']=mixer.budget.used
 def close(self):self.closed=True;self.cancel.set();self.pending.clear();self.cache.clear();self.bytes=0;self.poll()
 def exited(self):self.poll();return self.closed and self.cleanup is not None and self.cleanup.done() and all(not t.is_alive() for t in self.pool._threads)
