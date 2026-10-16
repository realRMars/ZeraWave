"""Owner-only rational project clock and ephemeral In/Out; no history edits."""
from fractions import Fraction
import time
from video_project import duration,rational,integer,fail

class Transport:
 def __init__(self,clock=time.monotonic_ns):
  self.clock=clock;self.binding=None;self.frame=0;self.anchor_frame=0;self.anchor_ns=clock();self.playing=False;self.active=False;self.generation=0;self.end=0;self.fps=Fraction(30);self.discontinuity=0;self.audio_clock=None;self.audio_seed=0;self.range_in=0;self.range_out=0;self.loop=False
 def sync(self,document,epoch,revision):
  binding=(epoch,revision,document['id'] if document else None)
  if binding==self.binding:return
  self.position();audio_sample=self.current_sample();prior=self.binding;old_fps=self.fps;old_end=self.end;self.binding=binding;self.end=duration(document) if document else 0;self.fps=rational(document['settings']['fps']) if document else Fraction(30)
  replacing=not document or prior is None or prior[0]!=epoch or prior[2]!=document['id']
  if replacing:self.active=False;self.playing=False;self.frame=0;self.audio_clock=None;self.audio_seed=0;self.range_in=0;self.range_out=self.end;self.loop=False;self.discontinuity+=1;self.anchor()
  else:
   self.range_out=self.end if self.range_out==old_end else min(self.range_out,self.end);self.range_in=min(self.range_in,max(0,self.range_out-1))
   if not self.end:self.loop=False
   if old_fps!=self.fps or self.frame>self.end:self.frame=min(self.frame,self.end);self.audio_clock=None;self.audio_seed=self.frame_sample();self.discontinuity+=1;self.anchor()
  # Ordinary edits preserve the exact subframe sample and nanosecond anchor.
  self.generation+=1
  if not replacing and self.audio_clock is not None:self.audio_seed=audio_sample;self.audio_clock=dict(sample=audio_sample,status='Buffering',binding=(epoch,revision,self.generation))
 def anchor(self):self.anchor_frame=self.frame;self.anchor_ns=self.clock()
 def frame_sample(self,frame=None):
  value=Fraction(self.frame if frame is None else frame)*48000/self.fps;return (value.numerator*2+value.denominator)//(value.denominator*2)
 def current_sample(self):
  if not self.audio_clock:return self.frame_sample()
  value=self.audio_clock['sample'];stamp=self.audio_clock.get('measured_ns');ceiling=self.audio_clock.get('submitted_sample')
  # Padding is sampled at audio-block boundaries. Hold on starvation/pause, but
  # interpolate a playing estimate between reports without inventing queued or
  # heard samples. The actual submitted-sample ceiling is a strict bound.
  if self.playing and self.audio_clock['status']=='Playing' and type(stamp) is int and type(ceiling) is int:
   elapsed=max(0,self.clock()-stamp);value=min(max(value,ceiling),value+elapsed*48000//1000000000)
  return value
 def restart_loop(self):
  self.frame=self.range_in;self.audio_seed=self.frame_sample();self.audio_clock=None;self.playing=True;self.generation+=1;self.discontinuity+=1;self.anchor()
 def audio_position(self,state=None):
  if state is None:self.audio_clock=dict(sample=self.audio_seed,status='Buffering',binding=(self.binding[0],self.binding[1],self.generation));return
  if state['status']=='Ended' and self.loop and self.playing and self.range_out>self.range_in:self.restart_loop();return
  self.audio_clock=dict(sample=state['sample_estimate'],status=state['status'],binding=(self.binding[0],self.binding[1],self.generation),measured_ns=state.get('sample_estimate_ns'),submitted_sample=state.get('submitted_sample'))
  if state['status'] in ('Ended','Unavailable','Release unconfirmed'):self.playing=False
 def position(self):
  if self.audio_clock:
   sample=max(0,self.current_sample());self.frame=min(self.end,(sample*self.fps.numerator)//(48000*self.fps.denominator))
   if self.frame<self.end and sample>=self.frame_sample(self.frame+1):self.frame+=1
   # Loop waits for the real output lane to drain its exact exclusive Out.
   if self.frame>=self.end and not self.loop:self.playing=False
  elif self.playing:
   elapsed=max(0,self.clock()-self.anchor_ns);step=(elapsed*self.fps.numerator)//(1000000000*self.fps.denominator);frame=self.anchor_frame+step
   if self.loop and self.range_out>self.range_in and frame>=self.range_out:
    self.frame=self.range_in+(frame-self.range_in)%(self.range_out-self.range_in);self.audio_seed=self.frame_sample();self.generation+=1;self.discontinuity+=1;self.anchor()
   else:
    self.frame=min(self.end,frame)
    if self.frame>=self.end:self.playing=False;self.anchor()
  return self.frame
 def command(self,op,frame=None):
  if not self.binding or self.binding[2] is None:fail('no_project','Open a video project before timeline transport.')
  self.position();sample=self.current_sample()
  if op in ('range_in','range_out'):
   integer(frame,0,self.end)
   if op=='range_in' and frame>=self.range_out or op=='range_out' and frame<=self.range_in:fail('invalid_range','In must precede exclusive Out; previous range retained.')
   if op=='range_in':self.range_in=frame
   else:self.range_out=frame
  elif op=='loop':
   integer(frame,0,1)
   if frame and self.range_out<=self.range_in:fail('invalid_range','Place material and set a nonempty In/Out range before looping.')
   self.loop=bool(frame)
  elif op=='range_clear':self.range_in=0;self.range_out=self.end;self.loop=False
  elif op=='range':
   if not isinstance(frame,list) or len(frame)!=2:fail('invalid_range','Source range needs [In, exclusive Out].')
   integer(frame[0],0,self.end);integer(frame[1],1,self.end)
   if frame[0]>=frame[1]:fail('invalid_range','In must precede exclusive Out.')
   self.range_in,self.range_out=frame
  elif op=='seek_paused':
   integer(frame,0,max(0,self.end-1));self.playing=False;self.active=True;self.frame=frame;sample=self.frame_sample();self.discontinuity+=1
  elif op in ('beginning','last','step'):
   if op=='step':integer(frame,-1,1)
   self.playing=False;self.active=True
   self.frame=0 if op=='beginning' else max(0,self.end-1) if op=='last' else max(0,min(max(0,self.end-1),self.frame+frame))
   sample=self.frame_sample();self.discontinuity+=1
  elif op=='release':
   # Retire output ownership while keeping an inspection position. Stop remains
   # the distinct reset-to-zero release used for document/legacy handover.
   self.playing=False;self.active=False;self.discontinuity+=1
  elif op=='seek':integer(frame,0,self.end);self.frame=frame;self.active=True;sample=self.frame_sample();self.discontinuity+=1
  elif op=='play':
   if not self.end:fail('empty_timeline','Place a clip or overlay before playing.')
   if self.loop and not self.range_in<=self.frame<self.range_out:self.frame=self.range_in;sample=self.frame_sample();self.discontinuity+=1
   elif self.frame>=self.end:self.frame=0;sample=0;self.discontinuity+=1
   self.playing=True;self.active=True
  elif op=='pause':self.playing=False;self.active=True
  elif op=='stop':self.playing=False;self.active=False;self.frame=0;sample=0;self.discontinuity+=1
  else:fail('unsupported_transport','Use seek, play, pause, stop, beginning, last, step, release, range_in, range_out or loop (0/1).')
  if self.playing and self.loop and not self.range_in<=self.frame<self.range_out:self.frame=self.range_in;sample=self.frame_sample();self.discontinuity+=1
  self.anchor();self.generation+=1;self.audio_clock=None;self.audio_seed=sample;return self.state()
 def state(self):
  return dict(project=self.binding[2] if self.binding else None,epoch=self.binding[0] if self.binding else None,revision=self.binding[1] if self.binding else None,frame=self.position(),end=self.end,playing=self.playing,active=self.active,generation=self.generation,sample=self.current_sample(),discontinuity=self.discontinuity,range_in=self.range_in,range_out=self.range_out,loop=self.loop,audio_end=self.frame_sample(self.range_out if self.loop else self.end),audio_status=(self.audio_clock or {}).get('status'),clock='project bounded interpolation of submitted-minus-padding estimate; audible position unavailable' if self.audio_clock else 'monotonic rational frame clock; not audible device position')
