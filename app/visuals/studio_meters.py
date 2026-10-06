"""Bounded Studio displays of actual decoded PCM and existing twelve FFT bands."""
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from pathlib import Path
import threading
import time
import wave
import tkinter as tk
from tkinter import ttk


def envelope(path, cancelled, buckets=2048):
    import numpy as np
    with wave.open(str(path), 'rb') as audio:
        if audio.getsampwidth()!=2: raise ValueError('Waveform needs decoded 16-bit PCM.')
        count = audio.getnframes(); channels=audio.getnchannels(); rate=audio.getframerate()
        if not count or not rate or channels>8: raise ValueError('Unavailable PCM metadata.')
        result=[]
        for i in range(min(buckets,count)):
            if cancelled.is_set(): return None
            start=i*count//min(buckets,count); end=(i+1)*count//min(buckets,count)
            remaining=end-start; low=high=0.
            while remaining:
                block=min(remaining,65536)
                samples=np.frombuffer(audio.readframes(block),dtype='<i2')
                if not len(samples):raise ValueError('Decoded track ended before its declared length.')
                low=min(low,float(samples.min())/32768.); high=max(high,float(samples.max())/32768.)
                remaining-=block
            result.append((low,high))
        return dict(path=str(path), duration=count/rate, peaks=result,
                    evidence='Stereo/channel PCM min/max envelope; actual decoded file, no resynthesis')


class Waveform:
    def __init__(self, parent):
        self.label=tk.StringVar(value='Session waveform · choose a decoded test track')
        ttk.Label(parent,textvariable=self.label).pack(anchor='w',pady=(4,1))
        self.canvas=tk.Canvas(parent,height=68,background='#0c1319',highlightthickness=0)
        self.canvas.pack(fill='x',expand=True)
        self.canvas.bind('<Configure>',lambda e:self.draw())
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Studio waveform')
        self.cancelled=threading.Event();self.future=None;self.pending=None;self.key=None;self.data=None
        self.lines=[self.canvas.create_line(0,0,0,0,fill='#329bb8',state='hidden') for _ in range(2048)]
        self.cursor=self.canvas.create_line(0,0,0,0,fill='#e2a777',width=2,state='hidden')
        self.live=deque(maxlen=192);self.live_sequence=None;self.seconds=None;self.source=None

    def request(self, source, path):
        previous_source=self.source
        self.source=source
        if source!='Test track':
            self.pending=None;self.key=None;self.data=None;self.seconds=None
            if previous_source!=source:self.live.clear();self.live_sequence=None
            self.label.set('Live PCM snapshots · current input' if source=='Live system audio' else 'Waveform unavailable · synthetic source')
            self.draw();return
        try:
            p=Path(path);stat=p.stat();key=(str(p.resolve()),stat.st_size,stat.st_mtime_ns)
        except OSError:
            self.pending=None;self.key=None;self.data=None;self.seconds=None
            self.label.set('Waveform unavailable · choose an existing decoded track');self.draw();return
        if key==self.key:return
        self.key=key;self.pending=p;self.data=None;self.live.clear();self.label.set('Reading '+p.name+' waveform…');self.draw()
        self.poll()

    def poll(self):
        if self.future is not None and self.future.done():
            try:
                data=self.future.result()
                if data and self.key and data['path']==self.key[0] and self.source=='Test track':
                    self.data=data;self.draw()
            except (OSError,ValueError,wave.Error) as exc:self.label.set('Waveform unavailable: '+str(exc))
            self.future=None
        if self.future is None and self.pending is not None:
            path=self.pending;self.pending=None;self.future=self.pool.submit(envelope,path.resolve(),self.cancelled)

    def update(self, latest):
        self.poll()
        current=bool(latest and time.perf_counter()-latest[1]<1.5 and (latest[0].get('audio_age_seconds') or 0)<1.5)
        packet=latest[0] if current else {}
        spectrum=packet.get('spectrum') or {}
        self.seconds=spectrum.get('sample_seconds') if spectrum.get('sample_clock')=='analyzed PCM' else None
        # File playback cursor comes from the shared analyzer's PCM position,
        # never shell wall time or the renderer's Hold/route clock.
        if self.source=='Test track' and self.data:
            self.label.set(Path(self.data['path']).name+' · '+
                (f'{self.seconds:.1f} / {self.data["duration"]:.1f}s' if self.seconds is not None else f'{self.data["duration"]:.1f}s · playback position unavailable'))
        elif self.source=='Live system audio':
            audio=packet.get('audio') or {}; peaks=audio.get('waveform')
            if current and audio.get('frame')!=self.live_sequence and isinstance(peaks,list):
                self.live.extend(peaks);self.live_sequence=audio.get('frame')
            self.label.set('Live PCM snapshots · '+('current' if current and peaks else 'no current PCM'))
        self.draw()

    def draw(self):
        if not self.canvas.winfo_exists():return
        width=max(1,self.canvas.winfo_width());height=max(1,self.canvas.winfo_height())
        peaks=self.data['peaks'] if self.source=='Test track' and self.data else list(self.live) if self.source=='Live system audio' else []
        # One envelope segment per effective display column at most; retained
        # item pool is bounded and reused across tracks/layouts.
        stride=max(1,(len(peaks)+min(2048,width)-1)//min(2048,width))
        key=(id(self.data),self.live_sequence if self.source=='Live system audio' else None,self.source,width,height)
        displayed=[(min(p[0] for p in peaks[i:i+stride]),max(p[1] for p in peaks[i:i+stride])) for i in range(0,len(peaks),stride)] if key!=getattr(self,'drawn',None) else None
        self.drawn=key
        for i,item in enumerate(self.lines):
            if displayed is None:break
            if i<len(displayed):
                low,high=displayed[i];x=i*width/max(1,len(displayed)-1)
                self.canvas.coords(item,x,height/2-high*(height/2-3),x,height/2-low*(height/2-3))
                self.canvas.itemconfigure(item,state='normal')
            else:self.canvas.itemconfigure(item,state='hidden')
        if self.seconds is not None and self.data and self.source=='Test track':
            x=width*max(0,min(1,self.seconds/self.data['duration']));self.canvas.coords(self.cursor,x,0,x,height)
            self.canvas.itemconfigure(self.cursor,state='normal');self.canvas.tag_raise(self.cursor)
        else:self.canvas.itemconfigure(self.cursor,state='hidden')

    def close(self):
        self.cancelled.set();self.pending=None;self.pool.shutdown(wait=True,cancel_futures=True)


class Analyzer:
    def __init__(self,parent):
        self.status=tk.StringVar(value='12-band analyzer · no current input')
        ttk.Label(parent,textvariable=self.status).pack(anchor='w')
        self.canvas=tk.Canvas(parent,height=140,background='#0c141a',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        self.items=[(self.canvas.create_rectangle(0,0,0,0,fill='#32b6d2',outline=''),
                     self.canvas.create_rectangle(0,0,0,0,fill='#d39769',outline=''),
                     self.canvas.create_text(0,0,fill='#b9c9d0',font=('Segoe UI',8))) for _ in range(12)]
        self.packet=None;self.stamp=None;self.drawn=None
        self.canvas.bind('<Configure>',lambda e:self.draw(force=True))

    def update(self,latest):
        self.packet=latest[0] if latest else None;self.stamp=latest[1] if latest else None;self.draw()

    def draw(self,force=False):
        p=self.packet or {};a=p.get('audio') or {};bands=a.get('band12') or {}
        valid=(self.stamp is not None and time.perf_counter()-self.stamp<1.5 and p.get('audio_age_seconds') is not None
               and p['audio_age_seconds']<1.5 and len(bands.get('edges',()))==13 and len(bands.get('levels',()))==12)
        key=(a.get('frame'),valid,self.canvas.winfo_width(),self.canvas.winfo_height())
        if key==self.drawn and not force:return
        self.drawn=key
        self.status.set('12-band analyzer · actual FFT ranges (* under-resolved)' if valid else '12-band analyzer · no current measured FFT bands')
        width=max(1,self.canvas.winfo_width());height=max(60,self.canvas.winfo_height());step=width/12
        for i,(bar,cap,label) in enumerate(self.items):
            value=max(0,min(1,float(bands['levels'][i]))) if valid else 0
            left=i*step+step*.15;right=(i+1)*step-step*.15;bottom=height-28;top=bottom-value*(height-38)
            self.canvas.coords(bar,left,top,right,bottom);self.canvas.coords(cap,left,top,right,top+min(3,bottom-top))
            edges=bands.get('edges')
            text=f'{edges[i]:g}–{edges[i+1]:g}' if valid else 'N/A'
            if valid and bands.get('unresolved',[True]*12)[i]:text+='*'
            self.canvas.coords(label,(i+.5)*step,height-15);self.canvas.itemconfigure(label,text=text,width=max(1,step-4))
