"""Project-owned exact-frame writes over the inspected SoundCard Windows ABI.

No installed package changes. Native buffer occupancy provides the pacing;
never release uninitialized or surplus frames beyond the supplied PCM.
"""
import hashlib
from pathlib import Path
import time
import numpy as np
from wasapi_cleanup import BACKEND_SHA256

class FrameOutput:
    paces_audio = True
    def __init__(self, player):
        import soundcard.mediafoundation as backend
        if type(player) is not backend._Player or hashlib.sha256(Path(backend.__file__).read_bytes()).hexdigest()!=BACKEND_SHA256:
            raise RuntimeError('Windows output ABI changed; exact-frame playback needs review.')
        self.player=player;self.ffi=backend._ffi
        self.submitted=0;self.released=0;self.maximum_padding=0;self.last_padding=0;self.waits=0;self.last_play_ms=0.;self.maximum_play_ms=0.;self.deadline_failures=0
    @property
    def padding(self):return int(self.player.currentpadding)
    def play(self, pcm):
        pcm=np.asarray(pcm,dtype=np.float32,order='C')
        if pcm.ndim!=2 or pcm.shape[1]!=2 or not np.isfinite(pcm).all():raise ValueError('Expected finite stereo float32 output PCM.')
        position=0;started=time.perf_counter()
        deadline=time.perf_counter()+max(.5,(len(pcm)+self.player.buffersize)/self.player.samplerate*3)
        while position<len(pcm):
            available=int(self.player._render_available_frames())
            if available<=0:
                if time.perf_counter()>=deadline:self.deadline_failures+=1;raise RuntimeError("Output stopped accepting PCM within its bounded deadline.")
                self.waits+=1;time.sleep(.001);continue
            count=min(available,len(pcm)-position)
            data=pcm[position:position+count].tobytes()
            buffer=self.player._render_buffer(count)
            self.ffi.memmove(buffer[0],data,len(data))
            self.player._render_release(count)
            self.released+=count;position+=count
            self.last_padding=self.padding;self.maximum_padding=max(self.maximum_padding,self.last_padding)
        self.submitted+=len(pcm);self.last_play_ms=(time.perf_counter()-started)*1000;self.maximum_play_ms=max(self.maximum_play_ms,self.last_play_ms)
    def snapshot(self):
        # Last owning-thread observations only; no GUI device/clock queries.
        return dict(submitted_frames=self.submitted,released_frames=self.released,last_padding_frames=self.last_padding,maximum_padding_frames=self.maximum_padding,
            waits=self.waits,last_play_ms=self.last_play_ms,maximum_play_ms=self.maximum_play_ms,deadline_failures=self.deadline_failures,
            device_position=None,position_note='Submitted/released/padding observations; correlated audible device position is unavailable, not decoded playhead.')
    def drain(self):
        deadline=time.perf_counter()+max(.5,self.player.buffersize/self.player.samplerate*3)
        while self.padding:
            if time.perf_counter()>=deadline:raise RuntimeError('Output tail did not drain within its bounded deadline.')
            time.sleep(.001)
