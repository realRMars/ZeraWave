"""Bounded decorative thumbnails/waveforms through existing media/mix readers.

No device output or artwork editing. Full-quality project preview/export are
unaffected. Coarse clips ask the user to zoom for waveform detail.
"""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from copy import deepcopy
import threading,time
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QImage,QColor,QPen

class Decorations:
    def __init__(self,canvas):
        self.canvas=canvas;self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Timeline decorations');self.future=None;self.active=None;self.pending=OrderedDict();self.cache=OrderedDict();self.bytes=0;self.closed=False;self.cancel=threading.Event();self.state={};self.cleanup=None;self.metrics=dict(requested=0,completed=0,superseded=0,cache_bytes=0,cache_limit=8*1024*1024,pending_limit=32)
    def request(self,key,job):
        if self.closed:return
        if key in self.cache:self.cache.move_to_end(key);return self.cache[key][0]
        if key!=self.active:
            self.pending[key]=job;self.pending.move_to_end(key)
            while len(self.pending)>32:self.pending.popitem(last=False);self.metrics['superseded']+=1
        return None
    def draw(self,p,rect,row,document):
        asset=next(a for a in document['media'] if a['id']==row['asset']);track=next(t for t in document['tracks'] if t['id']==row['track']);fps=Fraction(*document['settings']['fps']);rate=Fraction(*row['rate']);source=Fraction(*row['source_in']);identity=(asset['id'],asset['sha256'],asset['location']['path']);kind='wave' if track['kind']=='audio' else 'thumb';base=dict(asset=deepcopy(asset),source=source,rate=rate,fps=fps,kind=kind)
        if kind=='thumb':
            key=identity+(kind,str(source));result=self.request(key,base)
            if result and result.get('image'):
                image=result['image'];w=min(96,rect.width()-18);p.drawImage(QRectF(rect.left()+9,rect.top()+21,w,max(1,rect.height()-23)),image)
            elif result and result.get('error'):p.drawText(rect.adjusted(9,22,-9,-1),'Thumbnail unavailable')
            return
        # Detailed peaks cover exact short source spans. Avoid scheduling an
        # unbounded whole-file decode when hours collapse into a few pixels.
        seconds=Fraction(row['duration'])/fps
        if seconds>64 and rect.width()/float(seconds)<2:p.drawText(rect.adjusted(9,22,-9,-1),'Zoom for waveform detail');return
        visible=self.canvas.visibleRegion().boundingRect();left=max(rect.left()+9,visible.left());right=min(rect.right()-9,visible.right());first=max(0,int((left-rect.left())/(self.canvas.scale*float(fps)*2)));last=min(int((seconds+1)//2),int((right-rect.left())/(self.canvas.scale*float(fps)*2))+1)
        for chunk in range(first,min(last,first+32)):
            span=min(Fraction(2),seconds-chunk*2)
            if span<=0:continue
            at=source+chunk*2*rate;key=identity+(kind,str(at),str(span),str(rate),str(fps));result=self.request(key,dict(base,source=at,span=span));x=rect.left()+chunk*2*float(fps)*self.canvas.scale;width=float(span*fps)*self.canvas.scale
            if result and 'peaks' in result:
                peaks=result['peaks'];p.setPen(QPen(QColor('#bddfd0'),1));center=rect.top()+rect.height()*.68;height=rect.height()*.26
                for i,value in enumerate(peaks):
                    px=x+width*i/len(peaks)
                    if left<=px<=right:p.drawLine(round(px),round(center-height*min(1,value)),round(px),round(center+height*min(1,value)))
    def build(self,job):
        if self.cancel.is_set():raise InterruptedError()
        if job['kind']=='thumb':
            from project_media import Media
            media=self.state.get('media')
            if media is None:media=Media();self.state['media']=media
            plan=dict(settings=dict(fps=[job['fps'].numerator,job['fps'].denominator]),visual=[dict(clip=dict(id='timeline-thumbnail',rate=[1,1],source_in=[0,1],start=0),asset=job['asset'],source_time=[job['source'].numerator,job['source'].denominator])]);serial=media.submit(plan);end=time.monotonic()+8
            while not media.ready():
                if self.cancel.wait(.005) or time.monotonic()>end:media.submit(dict(visual=[]));raise InterruptedError('Thumbnail superseded or preparation deadline')
            result=media.take()
            try:
                if result['error']:raise ValueError(result['error'])
                frame=result['images']['timeline-thumbnail'];image=QImage(frame['data'],frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).scaled(96,54,Qt.KeepAspectRatio,Qt.SmoothTransformation);return dict(image=image)
            finally:media.release(serial)
        from project_mixer import Mixer
        from video_project import create,apply,new_id,pair
        from project_evaluator import Evaluator
        import numpy as np
        mixer=self.state.get('mixer')
        if mixer is None:mixer=Mixer();self.state['mixer']=mixer
        asset=job['asset'];track=new_id();clip=new_id();count=max(1,int(job['span']*job['fps']));d=create('Waveform detail',dict(width=16,height=16,fps=pair(job['fps'])));d,_=apply(d,[dict(op='media.add',**deepcopy(asset)),dict(op='track.add',id=track,kind='audio'),dict(op='clip.add',id=clip,asset=asset['id'],track=track,start=0,duration=count,source_in=pair(job['source']),rate=pair(job['rate']))],new_id());evaluator=Evaluator(d,'decoration',0);total=evaluator.audio_span(0,1)['end_frame'];samples=int(Fraction(count)/job['fps']*48000);peaks=np.zeros(128,np.float32)
        for begin in range(0,samples,2048):
            if self.cancel.is_set():raise InterruptedError()
            plan=evaluator.audio_span(begin,min(2048,samples-begin));pcm=mixer.render(plan,self.cancel);indices=np.minimum(127,(np.arange(len(pcm))+begin)*128//max(1,samples));np.maximum.at(peaks,indices,np.abs(pcm).max(axis=1))
        return dict(peaks=peaks)
    def poll(self):
        if self.future and self.future.done():
            key=self.active
            try:result=self.future.result()
            except InterruptedError:result=None
            except Exception as exc:result=dict(error=str(exc))
            self.future=None;self.active=None
            if result and not self.closed:
                cost=result['image'].sizeInBytes() if result.get('image') else result['peaks'].nbytes if 'peaks' in result else len(result.get('error',''));self.cache[key]=(result,cost);self.bytes+=cost;self.metrics['completed']+=1
                while self.bytes>8*1024*1024 or len(self.cache)>128:
                    _,(_,old)=self.cache.popitem(last=False);self.bytes-=old
                self.canvas.update()
        if not self.closed and self.future is None and self.pending:
            key,job=self.pending.popitem(last=False);self.active=key;self.metrics['requested']+=1;self.future=self.pool.submit(self.build,job)
        if self.closed and self.future is None and self.cleanup is None:self.cleanup=self.pool.submit(self.release)
        if self.cleanup and self.cleanup.done():self.cleanup.result();self.pool.shutdown(wait=False,cancel_futures=True)
        self.metrics.update(cache_bytes=self.bytes,pending=len(self.pending),in_flight=int(self.future is not None))
    def release(self):
        media=self.state.pop('media',None)
        if media:
            media.close()
            while not media.exited():time.sleep(.005)
        mixer=self.state.pop('mixer',None)
        if mixer:mixer.close()
    def close(self):self.closed=True;self.cancel.set();self.pending.clear();self.cache.clear();self.bytes=0;self.poll()
    def exited(self):self.poll();return self.closed and self.cleanup is not None and self.cleanup.done() and all(not t.is_alive() for t in self.pool._threads)
