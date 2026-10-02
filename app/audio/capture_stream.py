"""Owned blocking capture/analysis worker with a bounded presentation mailbox.

All 2048-sample chunks are analyzed; presentation drains available frames without
waiting for the next device packet. No FFT/normalization/onset retuning.
"""
from collections import deque
import threading,time

class CaptureStream:
 def __init__(self,capture,analyze,capacity=64):
  self.capture=capture;self.analyze=analyze;self.capacity=capacity;self.frames=deque();self.lock=threading.Lock();self.stop_event=threading.Event();self.worker=None;self.error=None;self.analyzed=0;self.coalesced=0
 def start(self):
  if self.worker is not None:raise RuntimeError('Capture stream already started')
  self.worker=threading.Thread(target=self._run,name='ZeraWave capture analysis',daemon=True);self.worker.start()
 def _run(self):
  try:
   self.capture.start()
   while not self.stop_event.is_set():
    samples=self.capture.read(numframes=2048);frame=self.analyze(samples)
    with self.lock:
     if len(self.frames)>=self.capacity:self.frames.popleft();self.coalesced+=1
     self.frames.append((time.perf_counter(),frame));self.analyzed+=1
  except Exception as exc:self.error=exc
  finally:
   try:self.capture.stop()
   except Exception as exc:
    if self.error is None:self.error=exc
 def drain(self):
  if self.error is not None:raise RuntimeError('Audio capture stream failed') from self.error
  with self.lock:frames=list(self.frames);self.frames.clear();return frames
 def stop(self):
  self.stop_event.set()
  if self.worker is not None:
   self.worker.join(2.)
   if self.worker.is_alive():raise RuntimeError('Owned audio capture did not stop within two seconds')
   self.worker=None
