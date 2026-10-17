"""Incremental raw canonical source peaks using the existing Mixer/readers.

Every sample in the covering source interval is inspected at unity rate, even
at faster clip rates. Authored gain/mute/fades,routing,playback/export stay put.
"""
from fractions import Fraction
from copy import deepcopy
import math,time
import numpy as np
from video_project import audio_defaults
RATE=48000
OVERVIEW_BINS=1024
DETAIL_BINS=128
QUANTUM_SAMPLES=RATE*5
AGGREGATE_SCRATCH=64*1024
def span(source,seconds,rate):
 first=math.floor(source*RATE);last=math.ceil((source+seconds*rate)*RATE)
 return first,max(1,last-first)
def prepare(state,job,cancel):
 from project_mixer import Mixer
 mixer=state.get('mixer')
 if mixer is None:mixer=Mixer(force_fallback=job.get('force_fallback',False));state['mixer']=mixer
 prior=job.get('progress');bins=job['bins'];first,total=span(job['source'],job['span'],job['rate']);done=prior['done'] if prior else 0;peaks=prior['peaks'].copy() if prior else np.zeros(bins,np.float32);began=time.perf_counter();start_done=done
 # Decoration-only unity span. Mixer owns verification,resampling and leases;
 # sample step1 inspects intervals that output-rate thinning could miss.
 track=dict(id='timeline-wave-track',order=0,kind='audio',audio=audio_defaults());clip=dict(id='timeline-wave-source',start=0,duration=1,source_in=[0,1],rate=[1,1],audio=audio_defaults(),audio_window=dict(offset=0,duration=1));item=dict(asset=job['asset'],track=track,clip=clip,offset=0)
 while done<total and done-start_done<QUANTUM_SAMPLES:
  if cancel.is_set():raise InterruptedError('Obsolete waveform generation')
  count=min(2048,total-done,QUANTUM_SAMPLES-(done-start_done));at=first+done;item.update(count=count,source_time=[at,RATE]);pcm=mixer.render(dict(start=at,count=count,fps=[30,1],end_frame=1,audio=[item]),cancel);mixer.budget.take(AGGREGATE_SCRATCH)
  try:
   indices=np.minimum(bins-1,(np.arange(count,dtype=np.int64)+done)*bins//total);np.maximum.at(peaks,indices,np.abs(pcm).max(axis=1));done+=count
  finally:mixer.budget.release(AGGREGATE_SCRATCH)
  if time.perf_counter()-began>=.05:break
 if cancel.is_set():raise InterruptedError('Obsolete waveform result')
 return dict(peaks=peaks,done=done,total=total,complete=done==total,bins=bins,first_source_sample=first,scanned=done-start_done,work_ms=(time.perf_counter()-began)*1000,reader_metrics=deepcopy(mixer.metrics),reader_budget_peak=mixer.budget.peak,aggregate_scratch_upper_bound=AGGREGATE_SCRATCH,basis='Raw canonical source max(abs L,R),before authored gain/fades/envelope/mute; covering floor-In/ceil-Out source samples,not output-rate thinning.')
def covered(result,index):
 """A partially scanned bin stays pending,even when its partial peak is nonzero."""
 return result['done']*result['bins']>=(index+1)*result['total']
