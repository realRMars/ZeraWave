"""Project mix adapter inside the existing AudioOwner, not another device owner."""

from fractions import Fraction
from collections import deque

import threading,time

import numpy as np

from project_audio_lane import AudioLane

from project_mixer import RATE



class ProjectOutputMixin:

 def setup_project(self):

  self.project_lane=AudioLane();self.project_desired=None;self.project_offer_serial=0;self.project_applied=0;self.project_signature=None;self.project_saved=None;self.project_serial=None;self.project_binding=None;self.project_cursor=0;self.project_last_submitted=None;self.project_spec=None;self.next_project=0.

  self.state['project_audio']=dict(active=False,status='Stopped',device_position=None,clock_note='Submitted minus observed padding estimate; correlated audible position unavailable.')
  self.project_meter_blocks=deque(maxlen=32)

 def offer_project(self,evaluator,transport):

  binding=(transport.get('epoch'),transport.get('revision'),transport.get('generation'),transport.get('discontinuity',0),transport.get('project'));signature=(*binding,transport.get('playing'),transport.get('active'))

  with self.lock:

   if signature==self.project_signature:return

   self.project_signature=signature;self.project_offer_serial+=1;self.project_desired=dict(serial=self.project_offer_serial,evaluator=evaluator,binding=binding,transport=dict(transport));self.state['project_audio']=dict(self.state['project_audio'],requested_binding=list(binding),requested_serial=self.project_offer_serial,requested_outcome='pending',transition_pending=True);self.wake.notify_all()

 def project_snapshot(self):

  with self.lock:return dict(self.state['project_audio'])

 def project_estimate(self):

  try:padding=getattr(self.output,'padding',0) if self.output else 0

  except Exception:return self.state.get('project_audio',{}).get('sample_estimate',self.project_spec['start']),None

  return max(self.project_spec['start'],self.project_cursor-int(padding)),int(padding)

 def project_report(self,status,error='',**extra):

  current=self.project_spec or {};binding=current.get('binding',self.project_binding);estimate,padding=self.project_estimate() if self.project_spec else (0,0)

  value=dict(active=self.project_saved is not None,name=current.get('name','Video Project'),status=status,error=error,binding=list(binding) if binding else None,submitted_sample=self.project_cursor,sample_estimate=estimate,sample_estimate_ns=time.monotonic_ns() if padding is not None else None,padding_frames=padding,device_position=None,clock_note='Submitted minus observed padding estimate; not measured audible position',transition_pending=False,preparation=self.project_lane.snapshot(),**extra)
  meter=next((b for b in reversed(self.project_meter_blocks) if b['binding']==binding and b['start']<=estimate<b['end']),None) if status in ('Playing','Buffering') else None
  value.update(levels=meter['levels'] if meter else None,meter_span=[meter['start'],meter['end']] if meter else None,meter_sample_estimate=estimate,meter_basis='Submitted block containing submitted-minus-padding sample estimate; not measured heard-device position',meter_timing_available=meter is not None,meter_blocks=len(self.project_meter_blocks))

  if 'output' not in value:value['output']=self.output.snapshot() if hasattr(self.output,'snapshot') else None

  # Read latest intent and publish while holding the same lock as offer_project.
  # A previous block's native submission may finish after a newer seek/pause/Stop
  # arrives. Its applied/submitted observations cannot erase that newer intent.
  with self.lock:
   latest=self.project_desired;pending=bool(latest and latest['serial']!=self.project_applied)
   requested=latest['binding'] if latest else None
   value.update(requested_binding=list(requested) if requested else None,requested_serial=latest['serial'] if latest else None,requested_outcome='pending' if pending else 'failed' if error else 'applied',transition_pending=pending,applied_binding=list(binding) if binding else None,applied_serial=current.get('serial',self.project_applied),applied_status=status,applied_error=error,last_submitted_binding=list(self.project_last_submitted['binding']) if self.project_last_submitted else None,last_submitted_sample=self.project_last_submitted['sample'] if self.project_last_submitted else None,error_binding=list(binding) if binding else None)
   self.change(project_audio=value)

 def apply_project(self):

  with self.lock:desired=self.project_desired

  if not desired or desired['serial']==self.project_applied:return

  self.project_applied=desired['serial'];evaluator=desired['evaluator'];transport=desired['transport'];binding=desired['binding'];playing=transport.get('playing',False);active=transport.get('active',False)
  self.project_meter_blocks.clear()

  if evaluator is None or not active:

   self.project_lane.offer(None,binding,0,False)

   if self.project_saved is not None:

    self.release_output();saved=self.project_saved;self.project_saved=None;self.project_spec=None;self.boundary();self.change(**saved)

    if saved['playing']:

     if saved['mode']=='Device Listening':self.start_capture()

     elif self.decoder:self.start_output();self.next_file=time.perf_counter()

   self.project_spec=None;self.project_binding=binding;self.project_report('Stopped');return

  # A paused ruler seek before project playback does not steal a working legacy

  # source. Once playing owns output, Pause retains its explicit project lease.

  if self.project_saved is None and not playing:
   self.project_binding=binding;self.project_report('Paused',parked_legacy=True,requested_sample=transport.get('sample',evaluator.at(transport['frame'])['sample']));return

  if self.blocked:raise RuntimeError('Audio release is unconfirmed; no project replacement output can start.')

  old=self.project_spec;carry=None

  if old and old['binding'][0]==binding[0] and old['binding'][4]==binding[4] and old['binding'][3]==binding[3]:carry=self.project_estimate()[0]

  if self.project_saved is None:

   keys=('mode','device','path','duration','status','error','playing','speed','file_revision','last_seek_id','playhead','repeat');self.project_saved={k:self.state[k] for k in keys};self.release_output();self.stop_capture()

  else:self.release_output()

  self.boundary();start=carry if carry is not None else transport.get('sample',evaluator.at(transport['frame'])['sample']);end=min(evaluator.at(evaluator.end)['sample'],transport.get('audio_end',evaluator.at(evaluator.end)['sample']));start=max(0,min(end,start));self.project_spec=dict(serial=desired['serial'],binding=binding,start=start,end=end,playing=playing,name=evaluator.document['name']);self.project_binding=binding;self.project_cursor=start;self.project_serial=self.project_lane.offer(evaluator,binding,start,playing,end=end);self.next_project=time.perf_counter();self.change(playing=False,error='',status='Project buffering' if playing else 'Project paused',playhead=start/RATE,duration=end/RATE);self.project_report('Buffering' if playing else 'Paused')

 def service_project(self):

  spec=self.project_spec

  if spec is None or not spec['playing'] or self.blocked:return

  if time.perf_counter()<self.next_project:return

  packet=self.project_lane.take(self.project_serial)

  if packet is None:

   self.next_project=time.perf_counter()+.005

   if self.output is not None:

    estimate,padding=self.project_estimate();status='Buffering' if padding==0 else 'Playing'

    self.change(status='Project buffering' if padding==0 else 'Project playing');self.project_report(status,preparation_wait=True)

   return

  # The control owner can replace the mailbox while a native output call is in

  # progress. Its next boundary releases that queue before any new packet plays.

  with self.lock:latest=self.project_desired

  if latest and latest['serial']!=self.project_applied:return

  if tuple(packet['binding'])!=self.project_binding:return

  if packet['error']:

   self.release_output();spec['playing']=False;self.change(playing=False,status='Project unavailable',error=packet['error']);self.project_report('Unavailable',packet['error']);return

  if packet['end']:

   if hasattr(self.output,'drain'):self.output.drain()

   self.release_output();self.project_cursor=spec['end'];spec['playing']=False;self.change(playing=False,status='Project ended',playhead=spec['end']/RATE);self.project_report('Ended');return

  pcm=packet['pcm'];self.start_output();started=time.perf_counter();audible=pcm*self.state['volume'];clipped=0 if self.state['mute'] else int(np.count_nonzero(abs(audible)>1.));audible=np.zeros_like(pcm) if self.state['mute'] else np.clip(audible,-1,1);prepared_ms=(time.perf_counter()-started)*1000;started=time.perf_counter();self.output.play(audible);output_ms=(time.perf_counter()-started)*1000;self.project_cursor=packet['start']+len(pcm);self.project_last_submitted=dict(binding=tuple(packet['binding']),sample=self.project_cursor);self.change(playing=True,status='Project playing',playhead=self.project_cursor/RATE)

  self.project_meter_blocks.append(dict(binding=tuple(packet['binding']),start=packet['start'],end=self.project_cursor,levels=packet.get('levels')))
  metrics=dict(output_rms=float(np.sqrt(np.mean(audible*audible))),output_peak=float(abs(audible).max()),output_clipped=clipped);started=time.perf_counter();self.publish(pcm,metrics);self.project_report('Playing',prepare_ms=packet['prepare_ms'],output_prepare_ms=prepared_ms,output_ms=output_ms,publish_ms=(time.perf_counter()-started)*1000,block_frames=len(pcm),output=self.output.snapshot() if hasattr(self.output,'snapshot') else None)

  self.next_project=time.perf_counter() if getattr(self.output,'paces_audio',False) else max(self.next_project+len(pcm)/RATE,time.perf_counter())

 def project_failure(self,exc):

  if self.project_spec:self.project_spec['playing']=False

  error=str(exc)

  try:self.release_output()

  except Exception as release:self.blocked=True;error+='; output release unconfirmed: '+str(release)

  self.change(playing=False,status='Release unconfirmed' if self.blocked else 'Project unavailable',error=error);self.project_report('Release unconfirmed' if self.blocked else 'Unavailable',error)





class TestSink:

 """Explicit discard-test diagnostic. No device; caller uses sample pacing."""

 paces_audio=False

 padding=0

 def __init__(self):self.submitted=0;self.peak=0.;self.closed=False

 def __enter__(self):return self

 def __exit__(self,*args):self.closed=True

 def play(self,pcm):self.submitted+=len(pcm);self.peak=max(self.peak,float(np.max(abs(pcm))))

 def drain(self):pass

 def snapshot(self):return dict(backend='discard-test diagnostic; NO hardware/output/listening',submitted_frames=self.submitted,last_padding_frames=0,device_position=None)

