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

def exact_output_and_conversion():
    from wasapi_output import FrameOutput
    class FFI:
        def memmove(self, destination, source, count):
            assert len(destination)==len(source)==count
            destination[:]=source
    class Native:
        buffersize=2238;samplerate=RATE;currentpadding=0
        def __init__(self):self.requests=[];self.blocks=[]
        def _render_available_frames(self):return self.buffersize
        def _render_buffer(self, count):
            self.requests.append(count);self.buffer=bytearray(count*8);return [self.buffer]
        def _render_release(self,count):
            assert count==self.requests[-1];self.blocks.append(bytes(self.buffer))
    native=Native();out=FrameOutput.__new__(FrameOutput)
    out.player=native;out.ffi=FFI();out.submitted=out.released=out.maximum_padding=0
    pcm=np.arange(4099*2,dtype=np.float32).reshape(-1,2)/10000
    out.play(pcm[:2048]);out.play(pcm[2048:4096]);out.play(pcm[4096:]);out.drain()
    assert native.requests==[2048,2048,3] and out.submitted==out.released==4099
    assert b''.join(native.blocks)==pcm.tobytes()
    native._render_available_frames=lambda:0
    with patch('wasapi_output.time.perf_counter',side_effect=[0.,1.]):
        try:out.play(pcm[:1])
        except RuntimeError:pass
        else:raise AssertionError('Stalled output accepted indefinitely')
    with tempfile.TemporaryDirectory() as folder:
        for rate,channels in ((48000,1),(48000,2),(44100,2),(32000,1),(96000,2)):
            count=rate//5;t=np.arange(count)/rate
            left=.2*np.sin(2*np.pi*1000*t)
            source=left[:,None] if channels==1 else np.column_stack((left,.1*np.sin(2*np.pi*3000*t)))
            path=Path(folder)/f'{rate}-{channels}.wav'
            encoded=(source*32767).astype('<i2')
            with wave.open(str(path),'wb') as f:
                f.setnchannels(channels);f.setsampwidth(2);f.setframerate(rate);f.writeframes(encoded.tobytes())
            with patch('studio_transport.importlib.util.find_spec',return_value=None):
                d=Decoder(path);blocks=[]
                while True:
                    block=d.read()
                    if not len(block):break
                    assert block.dtype==np.float32 and np.isfinite(block).all();blocks.append(block)
                d.close()
            actual=np.concatenate(blocks);assert len(actual)==9600
            raw=encoded.astype(np.float32)/32768
            if channels==1:raw=np.repeat(raw,2,axis=1)
            positions=np.arange(9600)*rate/RATE
            reference=np.column_stack([np.interp(positions,np.arange(count),raw[:,c]) for c in range(2)]).astype(np.float32)
            assert np.array_equal(actual,reference) # Includes every block boundary and tail.
            for c,hz in enumerate((1000,1000 if channels==1 else 3000)):
                assert abs(np.fft.rfftfreq(len(actual),1/RATE)[np.argmax(abs(np.fft.rfft(actual[:,c])))]-hz)<1
    output=Output();owner=AudioOwner(enumerator=Enumeration())
    try:
        with patch('soundcard.default_speaker',return_value=SimpleNamespace(player=lambda **kwargs:output.context())),patch('wasapi_output.FrameOutput',side_effect=RuntimeError('Injected ABI rejection')):
            try:owner.start_output()
            except RuntimeError:pass
            else:raise AssertionError('ABI rejection was ignored')
        assert output.opens==output.closes==1 and owner.output is None and owner.output_stack is None
    finally:owner.close()
    print('PASS: exact native frame writes including partial tail, bounded stalled output; mono/stereo 32/44.1/48/96 kHz conversion duration/frequency/continuity.')


def volume_and_drive():
    # One owner, real PCM bus, mocked output: no audible hardware testing.
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'levels.wav';write(path,RATE,RATE*2)
        output=Output();owner=AudioOwner(output_factory=output.context,enumerator=Enumeration())
        analyzed=lambda pcm:SimpleNamespace(bass=.9,mids=.8,highs=.7,flux=.4,impact=1.,bass_onset=1.,mids_onset=1.,highs_onset=1.,beat_tick=True)
        stream=HubStream(owner.environment(),analyzed)
        try:
            for value in (-.1,1.1,float('nan'),float('inf'),True,'1',None):
                try:owner.submit('volume',value=value)
                except ValueError:pass
                else:raise AssertionError('Invalid volume accepted')
            stream.start();owner.submit('open',path=str(path));wait(lambda:owner.snapshot()['status']=='Ready')
            assert owner.snapshot()['volume']==1. and not owner.snapshot()['raw_waveform']
            owner.submit('play');wait(lambda:len(output.blocks)>=2)
            assert np.allclose(output.blocks[-1],.125) # Unity, no hidden 0.2 attenuation.
            generation=owner.snapshot()['generation'];opens=output.opens
            owner.submit('volume',value=.5);wait(lambda:np.allclose(output.blocks[-1],.0625))
            assert owner.snapshot()['rms']==.125 and owner.snapshot()['output_rms']==.0625
            owner.submit('raw_waveform',value=True)
            wait(lambda:owner.snapshot()['raw_waveform'])
            wait(lambda:stream.latest.get('drive_revision')==1 and any(row[1][1].audio_source.get('drive_revision')==1 for row in stream.frames))
            frames=stream.drain();assert frames and all(row[1][1].audio_source['raw_waveform'] for row in frames)
            frame=frames[-1][1][1];assert frame.bass==frame.mids==frame.highs==.125 and frame.analyzed_levels['bass']==.9
            assert owner.snapshot()['generation']==generation and output.opens==opens
            before=owner.snapshot()['pcm_frames'];owner.submit('mute',value=True)
            wait(lambda:owner.snapshot()['mute'] and not np.any(output.blocks[-1]))
            wait(lambda:owner.snapshot()['pcm_frames']>before+2048)
            assert owner.snapshot()['rms']==.125 and owner.snapshot()['output_rms']==0.
            owner.submit('raw_waveform',value=False);wait(lambda:stream.latest.get('drive_revision')==2)
            wait(lambda:any(row[1][1].audio_source.get('drive_revision')==2 for row in stream.frames))
            frame=stream.drain()[-1][1][1];assert frame.bass==.9 and frame.visual_drive=='Analyzed'
            assert output.opens==opens and owner.snapshot()['generation']==generation
        finally:stream.stop();owner.close()
    print('PASS: unity/50%/mute output, unchanged PCM/analysis, validation, shared mode revision, stale-mode rejection, no stream reopen/source reset.')


def seek_and_speed():
    from file_waveform import envelope
    import threading
    with tempfile.TemporaryDirectory() as folder:
        # Ramp identifies exact sample order, seek offsets, signed speed and tails.
        for rate in (32000,48000,96000,192000):
            count=rate*2;source=(np.arange(count)%20001-10000).astype('<i2')
            path=Path(folder)/f'ramp-{rate}.wav'
            with wave.open(str(path),'wb') as out:
                out.setnchannels(1);out.setsampwidth(2);out.setframerate(rate);out.writeframes(source.tobytes())
            d=Decoder(path)
            try:
                for speed in (1.,2.,4.,6.,12.,-1.,-2.,-4.,-6.,-12.):
                    start=24000 if speed>0 else 72000;d.seek(start/RATE)
                    block=d.read(speed);canonical=start+np.arange(len(block))*speed if speed>0 else start+(np.arange(len(block))+1)*speed
                    reference=np.interp(canonical*rate/RATE,np.arange(count),source.astype(np.float32)/32768).astype(np.float32)
                    assert np.array_equal(block[:,0],reference),(rate,speed)
                    assert np.array_equal(block[:,0],block[:,1])
                    assert d.output_index==start+len(block)*speed
                    assert len(d.buffer)<2048*12*rate/RATE+4096
                for speed in (1.,4.,12.,-1.,-4.,-12.):
                    d.seek(0. if speed>0 else d.duration);frames=0
                    while True:
                        block=d.read(speed)
                        if not len(block):break
                        frames+=len(block)
                    assert frames==int(np.ceil(2*RATE/abs(speed)))
                    assert d.output_index==(2*RATE if speed>0 else 0)
                d.seek(1.234);assert d.output_index==round(1.234*RATE)
            finally:d.close()
            overview=envelope(path,threading.Event(),64)
            assert overview['duration']==2. and len(overview['peaks'])==64
            for i,(low,high) in enumerate(overview['peaks']):
                actual=source[i*count//64:(i+1)*count//64].astype(np.float32)/32768
                assert low==actual.min() and high==actual.max()
            cancel=threading.Event();cancel.set();assert envelope(path,cancel) is None
        path=Path(folder)/'owner.wav';write(path,RATE,RATE*2)
        output=Output();owner=AudioOwner(output_factory=output.context,enumerator=Enumeration())
        stream=HubStream(owner.environment(),lambda pcm:SimpleNamespace(impact=1.,bass_onset=1.,mids_onset=1.,highs_onset=1.,beat_tick=True))
        try:
            for value in (0.,3.,-3.,float('nan'),float('inf'),True,'2'):
                try:owner.submit('speed',value=value)
                except ValueError:pass
                else:raise AssertionError('Invalid speed accepted')
            stream.start();owner.submit('open',path=str(path));wait(lambda:owner.snapshot()['status']=='Ready')
            revision=owner.snapshot()['file_revision'];generation=owner.snapshot()['generation']
            with owner.lock:
                for i in range(10):owner.submit('seek',seconds=i/10,file_revision=revision,seek_id='drag-'+str(i))
            wait(lambda:owner.snapshot()['last_seek_id']=='drag-9')
            assert owner.snapshot()['playhead']==.9 and owner.snapshot()['generation']==generation+1
            generation=owner.snapshot()['generation']
            with owner.lock:
                for i in range(5):owner.submit('seek',seconds=i/10,file_revision=revision,seek_id='cancel-'+str(i))
                owner.submit('stop')
            wait(lambda:owner.snapshot()['status']=='Stopped')
            assert owner.snapshot()['playhead']==0. and owner.snapshot()['generation']==generation+1
            owner.submit('seek',seconds=1.,file_revision=revision,seek_id='paused-seek')
            wait(lambda:owner.snapshot()['last_seek_id']=='paused-seek')
            assert owner.snapshot()['playhead']==1. and not owner.snapshot()['playing'] and not owner.snapshot()['output']
            owner.submit('speed',value=-4.,play=True,file_revision=revision)
            wait(lambda:owner.snapshot()['speed']==-4. and owner.snapshot()['pcm_frames']>=2048)
            assert owner.snapshot()['playhead']<1. and output.opens==1 and np.allclose(output.blocks[-1],.125)
            opens=output.opens;generation=owner.snapshot()['generation']
            owner.submit('speed',value=-4.,play=True,file_revision=revision);wait(lambda:not owner.snapshot()['pending'])
            assert output.opens==opens and owner.snapshot()['generation']==generation
            wait(lambda:stream.latest.get('speed')==-4.)
            assert all(row[1][1].audio_source['speed']==-4. for row in stream.drain())
            owner.submit('pause');wait(lambda:owner.snapshot()['status']=='Paused')
            frames=owner.snapshot()['pcm_frames'];time.sleep(.09);assert owner.snapshot()['pcm_frames']==frames
            owner.submit('seek',seconds=1.5,file_revision=revision)
            wait(lambda:owner.snapshot()['playhead']==1.5)
            owner.submit('play');wait(lambda:owner.snapshot()['playing']);assert owner.snapshot()['speed']==1.
            owner.submit('seek',seconds=.75,file_revision=revision,seek_id='playing-seek')
            wait(lambda:owner.snapshot()['last_seek_id']=='playing-seek');assert owner.snapshot()['playing'] and owner.snapshot()['playhead']>=.75
            owner.submit('stop');wait(lambda:owner.snapshot()['status']=='Stopped')
            owner.submit('open',path=str(path));wait(lambda:owner.snapshot()['file_revision']>revision)
            before=owner.snapshot()['generation'];owner.submit('seek',seconds=1.,file_revision=revision)
            wait(lambda:'changed' in owner.snapshot()['error']);assert owner.snapshot()['generation']==before and owner.snapshot()['playhead']==0.
            owner.submit('repeat',value=True);owner.submit('seek',seconds=.05)
            wait(lambda:owner.snapshot()['playhead']==.05)
            owner.submit('speed',value=-12.,play=True);wait(lambda:owner.snapshot()['speed']==-12.)
            generation=owner.snapshot()['generation'];wait(lambda:owner.snapshot()['generation']>generation)
            assert owner.snapshot()['playing'] and owner.snapshot()['playhead']>0.
        finally:stream.stop();owner.close()
    print('PASS: bounded exact seek/rate/reverse sample order and endpoint duration at 32/48/96/192 kHz; file overview, cancellation, shared PCM bus, pause/resume/seek, reverse repeat, stale file rejection. Mock output; real decoder/socket.')


def run():
    exact_output_and_conversion()
    volume_and_drive()
    seek_and_speed()
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
