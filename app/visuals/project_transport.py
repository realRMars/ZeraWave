"""Owner-only rational project clock; no history or legacy clock edits."""
from fractions import Fraction
import time
from video_project import duration,rational,integer,fail

class Transport:
 def __init__(self,clock=time.monotonic_ns):
  self.clock=clock;self.binding=None;self.frame=0;self.anchor_frame=0;self.anchor_ns=clock();self.playing=False;self.active=False;self.generation=0;self.end=0;self.fps=Fraction(30);self.discontinuity=0;self.audio_clock=None;self.audio_seed=0
 def sync(self,document,epoch,revision):
  binding=(epoch,revision,document['id'] if document else None)
  if binding==self.binding:return
  self.position();audio_sample=self.current_sample();prior=self.binding;old_fps=self.fps;self.binding=binding;self.end=duration(document) if document else 0;self.fps=rational(document['settings']['fps']) if document else Fraction(30)
  replacing=not document or prior is None or prior[0]!=epoch or prior[2]!=document['id']
  if replacing:self.active=False;self.playing=False;self.frame=0;self.audio_clock=None;self.audio_seed=0;self.discontinuity+=1;self.anchor()
  elif old_fps!=self.fps or self.frame>self.end:self.frame=min(self.frame,self.end);self.audio_clock=None;self.audio_seed=self.frame_sample();self.discontinuity+=1;self.anchor()
  # Ordinary edits retain the exact nanosecond anchor/subframe phase. Repeated
  # volume/text edits must not quantize or repeatedly pause the playback clock.
  self.generation+=1
  if not replacing and self.audio_clock is not None:self.audio_seed=audio_sample;self.audio_clock=dict(sample=audio_sample,status='Buffering',binding=(epoch,revision,self.generation))
 def anchor(self):self.anchor_frame=self.frame;self.anchor_ns=self.clock()
 def frame_sample(self,frame=None):
  value=Fraction(self.frame if frame is None else frame)*48000/self.fps;return (value.numerator*2+value.denominator)//(value.denominator*2)
 def current_sample(self):return self.audio_clock['sample'] if self.audio_clock else self.frame_sample()
 def audio_position(self,state=None):
  if state is None:self.audio_clock=dict(sample=self.audio_seed,status='Buffering',binding=(self.binding[0],self.binding[1],self.generation));return
  self.audio_clock=dict(sample=state['sample_estimate'],status=state['status'],binding=(self.binding[0],self.binding[1],self.generation))
  if state['status'] in ('Ended','Unavailable','Release unconfirmed'):self.playing=False
 def position(self):
  if self.audio_clock:
   sample=max(0,self.audio_clock['sample']);self.frame=min(self.end,(sample*self.fps.numerator)//(48000*self.fps.denominator))
   if self.frame<self.end and sample>=self.frame_sample(self.frame+1):self.frame+=1
   if self.frame>=self.end:self.playing=False
  elif self.playing:
   elapsed=max(0,self.clock()-self.anchor_ns);step=(elapsed*self.fps.numerator)//(1000000000*self.fps.denominator);self.frame=min(self.end,self.anchor_frame+step)
   if self.frame>=self.end:self.playing=False;self.anchor()
  return self.frame
 def command(self,op,frame=None):
  if not self.binding or self.binding[2] is None:fail('no_project','Open a video project before timeline transport.')
  self.position();sample=self.current_sample()
  if op=='seek':integer(frame,0,self.end);self.frame=frame;self.active=True;sample=self.frame_sample();self.discontinuity+=1
  elif op=='play':
   if not self.end:fail('empty_timeline','Place a clip or overlay before playing.')
   if self.frame>=self.end:self.frame=0;sample=0;self.discontinuity+=1
   self.playing=True;self.active=True
  elif op=='pause':self.playing=False;self.active=True
  elif op=='stop':self.playing=False;self.active=False;self.frame=0;sample=0;self.discontinuity+=1
  else:fail('unsupported_transport','Use seek, play, pause or stop.')
  self.anchor();self.generation+=1;self.audio_clock=None;self.audio_seed=sample;return self.state()
 def state(self):
  return dict(project=self.binding[2] if self.binding else None,epoch=self.binding[0] if self.binding else None,revision=self.binding[1] if self.binding else None,frame=self.position(),end=self.end,playing=self.playing,active=self.active,generation=self.generation,sample=self.current_sample(),discontinuity=self.discontinuity,audio_status=(self.audio_clock or {}).get('status'),clock='project submitted-minus-padding estimate; audible position unavailable' if self.audio_clock else 'monotonic rational frame clock; not audible device position')
