"""Short standalone PCM/transport checks. Mock devices/output, real local bus."""
from collections import deque
from contextlib import contextmanager
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch
import wave
import numpy as np
from studio_transport import AudioOwner, Decoder, HubStream, RATE


DEVICE = dict(kind='loopback', id='test-exact', name='Controlled output')

class Enumeration:
    def request(self):pass
    def snapshot(self):return dict(sources=[DEVICE], error=None)
    def close(self):pass

class Capture:
    def __init__(self):self.closed=False;self.reads=0
    def start(self):pass
    def read(self,numframes=2048):
        time.sleep(numframes/RATE);self.reads+=1
        return np.full((numframes,2),.125,dtype=np.float32)
    def stop(self):self.closed=True

class Output:
    def __init__(self):self.blocks=deque(maxlen=64);self.opens=self.closes=0;self.fail_close=False
    @contextmanager
    def context(self):
        self.opens+=1
        try:yield self
        finally:
            self.closes+=1
            if self.fail_close:raise RuntimeError('Injected output close failure')
    def play(self,pcm):self.blocks.append(pcm.copy())

def wait(predicate):
    deadline=time.perf_counter()+3.
    while time.perf_counter()<deadline:
        if predicate():return
        time.sleep(.01)
    raise AssertionError('Timed out waiting for audio state')

def write(path,rate,count):
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate)
        out.writeframes(np.full(count,4096,dtype='<i2').tobytes())

def run():
    with tempfile.TemporaryDirectory() as folder:
        track=Path(folder)/'short.wav';write(track,RATE,7200)
        # WAV-only fallback works independently of the optional MP3 dependency.
        with patch('studio_transport.importlib.util.find_spec',return_value=None):
            converted=Path(folder)/'44100.wav';write(converted,44100,4410)
            decoder=Decoder(converted);blocks=[]
            while True:
                pcm=decoder.read()
                if not len(pcm):break
                blocks.append(pcm)
            assert sum(map(len,blocks))==4800
            assert np.allclose(np.concatenate(blocks),.125)
            assert len(decoder.buffer)<4096;decoder.close()
        output=Output();captures=[]
        def create_capture(device):
            assert device==DEVICE
            cap=Capture();captures.append(cap);return cap
        owner=AudioOwner(create_capture,output.context,Enumeration())
        stream=HubStream(owner.environment(),lambda pcm:SimpleNamespace(impact=1.,bass_onset=1.,mids_onset=1.,highs_onset=1.,beat_tick=True))
        try:
            assert output.opens==0 and not captures
            stream.start();owner.submit('device',value=DEVICE)
            wait(lambda:owner.snapshot()['sequence']>=2)
            assert output.opens==0  # Captured PCM has no playback/monitor path.
            wait(lambda:len(stream.frames)>0)
            assert stream.drain()[-1][1][0].shape[1]==2
            owner.submit('open',path=str(track));wait(lambda:owner.snapshot()['status']=='Ready')
            assert captures[-1].closed and owner.capture is None
            owner.submit('repeat',value=True);owner.submit('play')
            wait(lambda:owner.snapshot()['output'] and len(output.blocks)>=2)
            owner.submit('mute',value=True);wait(lambda:owner.snapshot()['mute'])
            before=owner.snapshot()['pcm_frames'];wait(lambda:owner.snapshot()['pcm_frames']>before+2048)
            assert not np.any(output.blocks[-1]) and owner.snapshot()['rms']>.1
            generation=owner.snapshot()['generation'];wait(lambda:owner.snapshot()['generation']>generation)
            owner.submit('pause');wait(lambda:owner.snapshot()['status']=='Paused')
            frozen=owner.snapshot()['pcm_frames'];time.sleep(.09)
            assert owner.snapshot()['pcm_frames']==frozen and not owner.snapshot()['output']
            owner.submit('open',path=str(Path(folder)/'missing.mp3'));wait(lambda:bool(owner.snapshot()['error']))
            assert owner.decoder is not None and owner.snapshot()['path']==str(track.resolve())
            owner.submit('play');wait(lambda:owner.snapshot()['playing'])
            owner.submit('stop');wait(lambda:owner.snapshot()['status']=='Stopped')
            assert owner.snapshot()['playhead']==0. and not owner.snapshot()['output']
            assert owner.decoder.output_index==0
            owner.submit('play');wait(lambda:owner.snapshot()['output'])
            output.fail_close=True;owner.submit('pause');wait(lambda:owner.blocked)
            opens=output.opens;owner.submit('play');wait(lambda:'unconfirmed' in owner.snapshot()['error'])
            assert output.opens==opens
        finally:
            stream.stop()
            try:owner.close()
            except RuntimeError:assert owner.output_release_error is not None
        assert not owner.worker.is_alive() and not owner.server.is_alive() and not stream.worker.is_alive()
    print('PASS: bounded WAV conversion, exact capture with no output, file/shared bus, mute PCM, pause/stop/repeat, invalid import preservation, ambiguous close blocks reopen, cleanup. Mock hardware; real PCM/socket.')

if __name__=='__main__':run()
