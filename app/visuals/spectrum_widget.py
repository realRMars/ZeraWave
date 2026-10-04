"""Reusable bounded display of measured FFT bins, separate from target routing."""
from dataclasses import dataclass
import math
import time

MAX_SAMPLES=2048
MAX_BINS=MAX_SAMPLES//2+1
MAX_RANGES=8

@dataclass(frozen=True)
class SpectrumRange:
    """Named display-only window; consumes existing spectrum/ACK metadata."""
    id:str
    label:str
    start_hz:float
    end_hz:float
    color:str
    dash:tuple=()
    enabled:bool=True
    ready:bool=True
    status:str=''

@dataclass(frozen=True)
class SpectrumTarget:
    label:str
    allowed_ranges:tuple
    feature:str
    target_id:str=''

def frequencies(packet):
    return [i*packet['sample_rate']/packet['sample_count']
            for i in range(packet['first_bin'],packet['first_bin']+len(packet['db']))]

def valid_packet(p):
    if not isinstance(p,dict):return False
    n=p.get('sample_count');rate=p.get('sample_rate');db=p.get('db')
    if type(n) is not int or not 2<=n<=MAX_SAMPLES:return False
    if type(rate) not in (int,float) or not math.isfinite(rate) or not 8000<=rate<=96000:return False
    if p.get('first_bin')!=1 or not isinstance(db,list) or len(db)!=n//2:return False
    if not all(type(v) in (int,float) and math.isfinite(v) and -120.<=v<=400. for v in db):return False
    for key in ('bin_spacing_hz','nyquist_hz','max_frequency_hz','window_ms','age_seconds','sample_seconds','observed_wall'):
        if type(p.get(key)) not in (int,float) or not math.isfinite(p[key]):return False
    return (p['bin_spacing_hz']==rate/n and p['nyquist_hz']==rate/2 and
            math.isclose(p['max_frequency_hz'],(n//2)*rate/n,rel_tol=1e-12) and
            p['window_ms']==n/rate*1000. and p['age_seconds']>=0. and p['sample_seconds']>=0. and
            type(p.get('sequence')) is int and isinstance(p.get('window'),str) and isinstance(p.get('sample_clock'),str))

class SpectrumFeed:
    """One copied FFT magnitude array, only while visible; no PCM or FFT."""
    def __init__(self,clock=time.perf_counter):
        self.clock=clock;self.enabled=False;self.sequence=0;self.samples=0
        self.raw=None;self.meta=None;self.grid=None;self.error=None

    def enable(self,enabled):
        self.enabled=bool(enabled);self.raw=None;self.meta=None;self.error=None

    def observe(self,frame,count,stamp=None,samplerate=48000):
        if type(count) is not int or count<0:raise ValueError('Invalid delivered sample count')
        self.sequence+=1;self.samples+=count
        if not self.enabled:return
        import numpy as np
        f=getattr(frame,'spectrum_frequencies',None);m=getattr(frame,'spectrum_magnitudes',None)
        if (not 2<=count<=MAX_SAMPLES or f is None or m is None or
                len(f)!=count//2+1 or len(m)!=len(f) or not np.isfinite(m).all() or np.any(m<0.)):
            self.raw=self.meta=None;self.error='No valid bounded FFT snapshot';return
        grid=(count,samplerate)
        if grid!=self.grid:
            if not np.allclose(f,np.arange(len(f))*samplerate/count,rtol=0.,atol=1e-8):
                self.raw=self.meta=None;self.error='FFT metadata does not match measured frequencies';return
            self.grid=grid
        p=getattr(frame,'planet_star_audio',None) or getattr(frame,'descriptors',None) or {}
        sample=p.get('sample_seconds',p.get('analyzed_seconds'))
        measured=type(sample) in (int,float) and math.isfinite(sample)
        self.meta=dict(sequence=self.sequence,sample_count=count,sample_rate=samplerate,first_bin=1,
            bin_spacing_hz=samplerate/count,nyquist_hz=samplerate/2,max_frequency_hz=float(f[-1]),
            window_ms=count/samplerate*1000.,window='rectangular / no overlap',
            sample_seconds=sample if measured else self.samples/samplerate,
            sample_clock='analyzed PCM' if measured else 'delivered PCM (queue drops excluded)',
            observed_wall=stamp if stamp is not None else self.clock())
        self.raw=np.array(m,dtype=float,copy=True);self.error=None

    def snapshot(self):
        if self.meta is None:return None
        import numpy as np
        n=self.meta['sample_count'];scale=np.full(len(self.raw),2./n);scale[0]=1./n
        if n%2==0:scale[-1]=1./n
        # Quantization is display/transport only. Detector keeps original bins.
        db=np.round(20.*np.log10(np.maximum(self.raw*scale,1e-6)),1)
        p=dict(self.meta,db=db[1:].tolist(),age_seconds=max(0.,self.clock()-self.meta['observed_wall']),
               units='FFT-bin peak amplitude dB relative to full scale; not RMS/power')
        return p

class SpectrumWidget:
    def __init__(self,parent,target):
        import tkinter as tk
        from tkinter import ttk
        self.target=target;self.packet=None;self.weights=None;self.identity=None;self.axis_key=None
        self.ranges=();self.focused_range=None;self.range_items=[]
        self.show_weight=True
        self.frame=ttk.Frame(parent)
        self.heading=tk.StringVar(value='Full measured spectrum · '+target.label)
        ttk.Label(self.frame,textvariable=self.heading).pack(anchor='w')
        self.metadata=tk.StringVar(value='Waiting for measured FFT bins; DC excluded.')
        ttk.Label(self.frame,textvariable=self.metadata,wraplength=740).pack(anchor='w',pady=3)
        self.canvas=tk.Canvas(self.frame,height=250,background='#111827',highlightthickness=0)
        self.canvas.pack(fill='x');self.canvas.bind('<Configure>',lambda event:self.draw(force=True))
        self.default_legend=('Cyan: measured FFT bins (dB peak). Amber: ACK-applied detector weight (×). '
            'Lines join real bins; they add no frequency resolution. Full spectrum remains visible under bypass.')
        self.legend=tk.StringVar(value=self.default_legend)
        self.legend_label=ttk.Label(self.frame,textvariable=self.legend,wraplength=740)
        self.legend_label.pack(anchor='w',pady=3)
        self.canvas.create_line(0,0,0,0,fill='#60d5ee',width=1.5,tags='spectrum')
        self.canvas.create_line(0,0,0,0,fill='#f9bf62',width=2,tags='weight')
        # Reuse one bounded pool through target switches and long sessions.
        for i in range(MAX_RANGES):
            tag='range-'+str(i)
            lines=tuple(self.canvas.create_line(0,0,0,0,state='hidden',tags=(tag,'ranges')) for _ in range(3))
            label=self.canvas.create_text(0,0,anchor='w',state='hidden',font=('Segoe UI',8),tags=(tag,'ranges'))
            self.range_items.append((*lines,label))

    def set_target(self,target):
        self.target=target;self.axis_key=None;self.identity=None
        self.ranges=();self.focused_range=None;self.legend.set(self.default_legend)
        self.hide_ranges()
        self.heading.set('Full measured spectrum · '+target.label)

    def hide_ranges(self):
        for items in self.range_items:
            for item in items:self.canvas.itemconfigure(item,state='hidden')

    def range_legend(self):
        if not self.ranges:self.legend.set(self.default_legend);return
        rows=[]
        for i,r in enumerate(self.ranges):
            style='dotted pending' if r.enabled and not r.ready else 'dashed' if r.dash else 'solid'
            state=r.status or ('OFF - original feature' if not r.enabled else 'applied' if r.ready else 'waiting for matching analysis')
            rows.append(f'{r.label}: {r.start_hz:g}-{r.end_hz:g} Hz; {style} lane {i+1}; {state}'+
                (' [editing]' if r.id==self.focused_range else ''))
        rows.append('Cyan = measured bins. Overlap stays in separate lanes. Windows show ACK values; no added FFT resolution.')
        if self.packet is None:rows.append('No current FFT snapshot; window overlays hidden.')
        self.legend.set('\n'.join(rows))

    def focus_range(self,range_id):
        if self.focused_range==range_id:return
        self.focused_range=range_id;self.range_legend();self.draw()

    def update(self,packet,weights,identity=None,ranges=(),show_weight=None):
        ranges=tuple(ranges)
        if len(ranges)>MAX_RANGES or not all(isinstance(r,SpectrumRange) for r in ranges):raise ValueError('Invalid spectrum ranges')
        if len({r.id for r in ranges})!=len(ranges):raise ValueError('Duplicate spectrum range IDs')
        for r in ranges:
            if (not r.id or not r.label or not math.isfinite(r.start_hz) or not math.isfinite(r.end_hz) or
                    not 0<=r.start_hz<r.end_hz):raise ValueError('Invalid spectrum range')
        self.ranges=ranges
        self.show_weight=not ranges if show_weight is None else bool(show_weight)
        self.packet=packet;self.weights=weights
        self.range_legend()
        if packet is None:
            self.identity=None
            self.metadata.set('No current FFT snapshot; DC excluded.')
            self.canvas.itemconfigure('spectrum',state='hidden');self.canvas.itemconfigure('weight',state='hidden');self.hide_ranges();return
        self.metadata.set(f"N={packet['sample_count']} · {packet['bin_spacing_hz']:.4f} Hz/bin · "
            f"Nyquist {packet['nyquist_hz']:g} Hz · packet {packet['window_ms']:.3f} ms · "
            f"age {packet['age_seconds']*1000.:.0f} ms · {packet['window']} · DC excluded")
        key=(packet['sequence'],identity,ranges,self.focused_range,self.show_weight)
        if key!=self.identity:self.identity=key;self.draw()

    def draw(self,force=False):
        p=self.packet
        if p is None:return
        width=max(340,self.canvas.winfo_width());left,right=54,width-48;top=24
        height=int(self.canvas.cget('height'));bottom=max(80,height-35)
        maximum=p['nyquist_hz'];minimum=min(20.,p['bin_spacing_hz'])
        def x(hz):return left+(right-left)*math.log(max(minimum,hz)/minimum)/math.log(maximum/minimum)
        def y(db):return bottom-(bottom-top)*(max(-120.,min(6.1,db))+120.)/126.1
        axis_key=(width,height,p['sample_count'],p['sample_rate'],bool(self.ranges),self.show_weight)
        if axis_key!=self.axis_key:
            self.axis_key=axis_key;self.canvas.delete('axis')
            self.plot_frequencies=frequencies(p);self.plot_x=[x(hz) for hz in self.plot_frequencies]
            for low,high in self.target.allowed_ranges:
                self.canvas.create_rectangle(x(low),top,x(min(high,maximum)),bottom,fill='#1d2a39',outline='',tags='axis')
            for hz in (20,40,80,160,315,1000,4000,10000,maximum):
                if minimum<=hz<=maximum:
                    xx=x(hz);self.canvas.create_line(xx,top,xx,bottom,fill='#283448',tags='axis')
                    self.canvas.create_text(xx,bottom+13,text=f'{hz:g}',fill='#b7c4d7',font=('Segoe UI',8),tags='axis')
            for db in (0,-30,-60,-90,-120):
                yy=y(db);self.canvas.create_line(left,yy,right,yy,fill='#283448',tags='axis')
                self.canvas.create_text(left-6,yy,text=str(db),anchor='e',fill='#b7c4d7',tags='axis')
            for gain in ((0,1,2) if self.show_weight else ()):
                self.canvas.create_text(right+6,bottom-(bottom-top)*gain/2,text=f'{gain}×',anchor='w',fill='#f9bf62',tags='axis')
            self.canvas.create_text(left,10,text='dB peak',anchor='w',fill='#60d5ee',tags='axis')
            self.canvas.create_text(right,10,text='Listening ranges' if self.ranges else 'Weight',anchor='e',
                fill='#b7c4d7' if self.ranges else '#f9bf62',tags='axis')
        self.canvas.delete('bins');points=[];curve=[]
        for hz,xx,db,gain in zip(self.plot_frequencies,self.plot_x,p['db'],self.weights):
            yy=y(db);points.extend((xx,yy));curve.extend((xx,bottom-(bottom-top)*gain/2))
            if hz<=315:self.canvas.create_oval(xx-2,yy-2,xx+2,yy+2,fill='#60d5ee',outline='',tags='bins')
        for tag,coords in (('spectrum',points),('weight',curve)):
            if len(coords)>=4 and (tag!='weight' or self.show_weight):self.canvas.coords(tag,*coords);self.canvas.itemconfigure(tag,state='normal');self.canvas.tag_raise(tag)
            else:self.canvas.itemconfigure(tag,state='hidden')
        self.hide_ranges()
        spacing=min(16.,(bottom-top-8)/max(1,len(self.ranges)))
        for i,r in enumerate(self.ranges):
            if not r.enabled or r.start_hz>=maximum:continue
            lo=x(r.start_hz);hi=x(min(r.end_hz,maximum));lane=top+8+i*spacing
            span,a,b,label=self.range_items[i];dash=r.dash if r.ready else (2,3)
            for item in (span,a,b):self.canvas.itemconfigure(item,state='normal',fill=r.color,dash=dash,width=3 if r.id==self.focused_range else 1.5)
            self.canvas.coords(span,lo,lane+4,lo,lane,hi,lane,hi,lane+4)
            self.canvas.coords(a,lo,lane+4,lo,bottom);self.canvas.coords(b,hi,lane+4,hi,bottom)
            self.canvas.coords(label,left+4,lane-4)
            self.canvas.itemconfigure(label,state='normal',text=r.label+(' [editing]' if r.id==self.focused_range else ''),fill=r.color)
            for item in self.range_items[i]:self.canvas.tag_raise(item)
        self.canvas.tag_raise('spectrum');self.canvas.tag_raise('bins')
