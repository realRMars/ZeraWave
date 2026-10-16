"""Four prepared PCM blocks on one codec/mix owner; no output device here."""
from collections import deque
import threading,time
from project_mixer import Mixer,BLOCK

class AudioLane:
 def __init__(self):
  self.condition=threading.Condition();self.desired=None;self.current=None;self.serial=0;self.packets=deque();self.stopping=False;self.error='';self.metrics={};self.active_cancel=None;self.thread=threading.Thread(target=self.run,name='Project audio preparation',daemon=True);self.thread.start()
 def offer(self,evaluator,binding,start,playing,end=None):
  with self.condition:
   if self.stopping:raise RuntimeError('Project audio preparation is closing.')
   self.serial+=1
   if self.active_cancel:self.active_cancel.set()
   self.desired=dict(serial=self.serial,evaluator=evaluator,binding=tuple(binding),cursor=start,playing=playing,end=end,cancel=threading.Event());self.packets.clear();self.error='';self.condition.notify_all();return self.serial
 def take(self,serial):
  with self.condition:
   if serial!=self.serial:return None
   value=self.packets.popleft() if self.packets else None;self.condition.notify_all();return value
 def snapshot(self):
  with self.condition:return dict(self.metrics,serial=self.serial,prepared_blocks=len(self.packets),prepared_bytes=sum(p['pcm'].nbytes for p in self.packets if p.get('pcm') is not None),error=self.error,worker_alive=self.thread.is_alive())
 def run(self):
  mixer=None;spec=None
  try:
   mixer=Mixer()
   while True:
    with self.condition:
     self.condition.wait_for(lambda:self.stopping or self.desired is not None or spec is not None and spec['playing'] and len(self.packets)<4)
     if self.stopping:break
     if self.desired is not None:
      spec=self.desired;self.desired=None;self.current=spec;self.active_cancel=spec['cancel']
     if spec['evaluator'] is None or not spec['playing']:
      # Retire runtime source caches, not accepted document/history state.
      mixer.close();mixer=Mixer();spec=None;self.current=None;self.metrics=dict(mixer.metrics,retired=True);continue
     cursor=spec['cursor'];serial=spec['serial'];evaluator=spec['evaluator'];cancel=spec['cancel']
    began=time.perf_counter()
    try:
     count=BLOCK if spec['end'] is None else max(1,min(BLOCK,spec['end']-cursor));plan=evaluator.audio_span(cursor,count)
     if spec['end'] is not None and cursor>=spec['end']:plan=dict(plan,count=0,audio=[])
     if not plan['count']:packet=dict(serial=serial,binding=spec['binding'],start=cursor,pcm=None,end=True,error='')
     else:
      pcm=mixer.render(plan,cancel);pcm.flags.writeable=False;packet=dict(serial=serial,binding=spec['binding'],start=cursor,pcm=pcm,end=False,error='',prepare_ms=(time.perf_counter()-began)*1000,levels=mixer.metrics.get('levels'),level_span=mixer.metrics.get('level_span'));spec['cursor']+=len(pcm)
    except Exception as exc:
     packet=dict(serial=serial,binding=spec['binding'],start=cursor,pcm=None,end=False,error=type(exc).__name__+': '+str(exc));spec['playing']=False
    with self.condition:
     if not cancel.is_set() and serial==self.serial:
      self.packets.append(packet);self.metrics=dict(mixer.metrics,requested_sample=cursor,prepared_cursor=spec['cursor'],prepare_ms=(time.perf_counter()-began)*1000,binding=list(spec['binding']))
      if packet['error']:self.error=packet['error']
      if packet['end']:spec['playing']=False
     self.condition.notify_all()
    packet=None
  finally:
   if mixer:mixer.close()
   with self.condition:self.current=self.desired=None;self.packets.clear();self.metrics=dict(self.metrics,readers=0,cache_bytes=0,prepared_bytes=0,worker_alive=False);self.active_cancel=None
 def close(self):
  with self.condition:
   self.stopping=True
   if self.active_cancel:self.active_cancel.set()
   if self.desired:self.desired['cancel'].set()
   self.desired=None;self.packets.clear();self.condition.notify_all()
 def exited(self):return not self.thread.is_alive()
