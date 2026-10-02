"""Standalone focused source, additive-analysis, modal and lifecycle fixtures."""
from pathlib import Path
import sys,math,ast,time,json,tempfile,wave
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1] if HERE.name=='visuals' else Path(r'C:\ZeraWave')
for p in (ROOT/'app/visuals',ROOT/'app/audio'):sys.path.insert(0,str(p))
from oscillator import Oscillator,Monitor,config
from frequency_bands import FrequencyBands,DEFAULT_EDGES
from cymatics import Basin
from cymatics_session import defaults,validate
import live_visual_test as live
from studio_color_link import ColorInbox
def generated(osc,total,chunk):return np.concatenate([osc.read(min(chunk,total-i)) for i in range(0,total,chunk)])
def fixtures():
    for shape in ('sine','triangle','square','saw'):
        data=dict(frequency=1125.,sweep_end=1125.,waveform=shape,amplitude=.4)
        a=generated(Oscillator(data),12000,137);b=generated(Oscillator(data),12000,2048)
        assert np.array_equal(a,b),shape
        assert np.isfinite(a).all() and np.max(abs(a))<=.5
    for logarithmic in (False,True):
        osc=Oscillator(dict(frequency=20.,sweep_end=2000.,sweep_seconds=2.,sweep_log=logarithmic))
        i=np.arange(1,60000,600);derivative=(osc.phase_at(i+1)-osc.phase_at(i-1))*48000/(2*math.tau)
        assert np.allclose(derivative,osc.frequency_at(i),rtol=1e-5)
    osc=Oscillator();osc.read(1024);phase=osc.phase_at(osc.index);cfg=dict(osc.settings.__dict__,frequency=4.)
    osc.apply(cfg);assert osc.phase_at(osc.index)==phase
    before=osc.index;osc.paused=True;assert len(osc.read(512))==0 and osc.index==before
    osc.paused=False;osc.read(512);osc.reset();assert osc.index==0
    analyser=live.AudioAnalyzer();tones=[]
    for i,(a,b) in enumerate(zip(DEFAULT_EDGES,DEFAULT_EDGES[1:])):
        f=(a*b)**.5;pcm=np.sin(np.arange(2048)*math.tau*f/48000.)*.5
        frequencies,mags=analyser.spectrum(pcm);summary=FrequencyBands().summarize(frequencies,mags,len(pcm))
        # Narrow low bands have unresolved/leaky bins; do not manufacture precision.
        if not summary['unresolved'][i]:assert np.argmax(summary['raw'])==i,(i,f,summary['raw'])
        tones.append(summary)
    empty=FrequencyBands(dict(edges=list(np.linspace(0,12,13)))).summarize(*analyser.spectrum(np.zeros(2048)),2048)
    assert all(v==0 for v in empty['raw']) and any(n==0 for n in empty['bins'])
    bands=FrequencyBands();f,m=analyser.spectrum(np.sin(np.arange(2048)*math.tau*1000/48000))
    peak=bands.summarize(f,m,2048)['levels']
    for i in range(100):quiet=bands.summarize(f,np.zeros_like(m),2048)['levels']
    assert max(quiet)<max(peak)*1e-5
    # Fixed pre-change legacy outputs keep this check portable beyond work/ captures.
    golden=json.loads((HERE/'cymatics_legacy_fixture.json').read_text())
    new=(live.AudioAnalyzer(),live.SignalProcessor(smoothing=.5),live.VisualSignalConditioner(quiet_threshold=.06),{k:live.OnsetDetector() for k in ('bass','mids','highs')})
    rng=np.random.default_rng(7301)
    for i,row in enumerate(golden['rows']):
        pcm=np.zeros(2048) if i>48 else rng.normal(size=2048)*(.001 if i%3==0 else .12)
        frame=live.analyze_samples(pcm,*new)
        for key,value in zip(golden['keys'],row):assert getattr(frame,key)==value,(i,key)
    # Identical audio samples partitioned as30/60/144Hz render intervals.
    pcm=np.sin(np.arange(48000)*math.tau*2.4/48000)*.35;states=[]
    for cadence in (30,60,144):
        basin=Basin();boundaries=np.linspace(0,48000,cadence+1).astype(int)
        for a,b in zip(boundaries,boundaries[1:]):basin.advance(pcm[a:b])
        states.append(basin.z.copy())
    assert np.allclose(states[0],states[1],atol=1e-14) and np.allclose(states[0],states[2],atol=1e-14)
    b=Basin(dict(modes=1));w=b.omega[0];gamma=b.gamma[0];freq=w/math.tau
    count=48000*12;coupling=b.coupling[0]*b.settings.excitation
    for start in range(0,count,2048):
        indices=np.arange(start,min(start+2048,count));b.advance(.2*np.sin(indices*w/48000))
    amplitude=.2*abs(coupling)/(2*gamma*w)
    assert abs(abs(b.z[0])/amplitude-1.)<.04,(abs(b.z[0]),amplitude)
    start=abs(b.z[0]);b.advance(np.zeros(2048));assert np.isclose(abs(b.z[0]),start*np.exp(-gamma*2048/48000),rtol=1e-10)
    large=Basin(dict(width=.2));assert large.omega[0]<Basin().omega[0]
    deeper=Basin(dict(depth=.01));assert deeper.omega[0]>Basin().omega[0]
    b=Basin();a=Basin();c=Basin();x=np.sin(np.arange(2048)*.0005);y=np.cos(np.arange(2048)*.0005)
    b.advance(x+y);a.advance(x);c.advance(y);assert np.allclose(b.z,a.z+c.z,atol=1e-15)
    zero=Basin();zero.advance(x-x);assert np.max(abs(zero.z))==0
    trial,reset=b.update(dict(b.settings.__dict__,damping=.8));assert not reset
    assert np.allclose(-trial.wd*trial.z.imag-trial.gamma*trial.z.real,-b.wd*b.z.imag-b.gamma*b.z.real)
    _,reset=b.update(dict(b.settings.__dict__,width=.12));assert reset
    assert b.weights.nbytes<=36*2048*16
    assert validate(dict(defaults(),monitor=True),stored=True)['monitor'] is False
    class Null:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def play(self,data):assert np.max(abs(data))<=.05
    monitor=Monitor(lambda:Null());assert not monitor.enabled;monitor.enable(.02);monitor.submit(np.ones(2048));time.sleep(.08);monitor.stop();assert not monitor.enabled and not monitor.error
    def broken():raise RuntimeError('mock device unavailable')
    monitor=Monitor(broken);monitor.enable();time.sleep(.03);assert not monitor.enabled and 'unavailable' in monitor.error;monitor.stop()
    print('PASS: oscillator determinism/phase/sweep/bounds;12band tone/empty/silence;64 exact legacy-analysis blocks;30/60/144 cadence;resonance/decay/coherent interference/edit/reset/bounds;muted/mock output lifecycle.',flush=True)
def extra_fixtures():
    osc=Oscillator(dict(frequency=2.,sweep_end=8.,sweep_seconds=3.));osc.read(2048)
    before=osc.phase_at(osc.index);hz=osc.frequency_at(osc.index)
    osc.apply(dict(osc.settings.__dict__,amplitude=.2));assert osc.phase_at(osc.index)==before and osc.frequency_at(osc.index)==hz
    # FFT chord: separated tones must coexist, not collapse to a pitch estimate.
    analyzer=live.AudioAnalyzer();t=np.arange(2048)/48000
    f,m=analyzer.spectrum(sum(.15*np.sin(math.tau*hz*t) for hz in (375.,1875.,7500.)))
    summary=FrequencyBands().summarize(f,m,2048)
    json.dumps(summary)
    assert all(summary['raw'][i] >= .7*.15*2048/(2*summary['bins'][i]) for i in (4,6,9))
    for hz in (375.,1875.,7500.):
        osc=Oscillator(dict(frequency=hz,sweep_end=hz));pcm=generated(osc,24000,2048)[-2048:]
        f,m=analyzer.spectrum(pcm);assert abs(f[np.argmax(m)]-hz)<=48000/2048
    # Impulse evolves at modeled damped frequency and gamma without forcing.
    basin=Basin(dict(modes=1));basin.advance(np.array([1.]))
    initial=basin.z.copy();n=2048;basin.advance(np.zeros(n))
    assert np.allclose(basin.z,initial*np.exp(basin.lam*n/48000),atol=1e-16)
    # Half-sample ZOH convergence against closed-form harmonic transfer.
    b=Basin(dict(modes=1));lam=b.lam[0];wd=b.wd[0];drive=b.omega[0]*.83;duration=.4
    def integration(rate):
        n=int(duration*rate);dt=1/rate
        u=np.sin(drive*np.arange(n)*dt)
        return (-1j/wd*np.expm1(lam*dt)/lam)*np.dot(np.exp(lam*dt*np.arange(n)),u[::-1])
    exact=(-1j/wd)*((np.exp(1j*drive*duration)-np.exp(lam*duration))/(1j*drive-lam)-(np.exp(-1j*drive*duration)-np.exp(lam*duration))/(-1j*drive-lam))/(2j)
    coarse=abs(integration(24000)-exact);fine=abs(integration(48000)-exact)
    assert fine<coarse*.51 and fine/abs(exact)<5e-5
    # Actual clock accumulator: no per-render truncation drift at144Hz.
    from cymatics_preview import Experiment
    class Params:pass
    class FakeRenderer:
        parameters=Params()
    e=Experiment(FakeRenderer());
    for i in range(144):e.advance(1/144)
    assert abs(e.index-48000)<=1 and e.oscillator.index==e.renderer.cymatics.sample_index==e.index
    e.close()
    # A decoded PCM fixture uses exactly the same model input as its source samples.
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'known.wav';osc=Oscillator(dict(frequency=3.7,sweep_end=5.7,sweep_seconds=1.))
        samples=(generated(osc,48000,2048)*32767).astype(np.int16)
        with wave.open(str(path),'wb') as audio:
            audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(48000);audio.writeframes(samples.tobytes())
        c=defaults();c['source']='track';e=Experiment(FakeRenderer(),c,path);reference=Basin()
        for start in range(0,len(samples),2048):reference.advance(samples[start:start+2048].astype(float)/32768)
        for i in range(10):e.advance(.1)
        assert e.index==48000 and np.allclose(e.renderer.cymatics.z,reference.z,atol=1e-14)
        e.advance(.1);assert e.eof;e.close()
    print('PASS chord assignment, exact-frequency tones, impulse phase/ringdown, half-sample convergence and actual144Hz clock ownership.')
def presentation_fixture():
    # Regression for the user-visible hang that offscreen shader tests missed.
    import cymatics_preview as preview
    from unittest.mock import patch
    from contextlib import redirect_stdout
    from types import SimpleNamespace
    import io
    instances=[]
    class Screen:
        def __init__(self,**kwargs):self.parameters=SimpleNamespace();self.color_inbox=None;self.frames=0;self.events=0;self.presented=0;instances.append(self)
        def set_colors(self,colors):pass
        def create(self):pass
        def should_close(self):return self.frames>=3
        def poll_events(self):self.events+=1
        def render(self,seconds):assert self.events==self.frames+1;self.frames+=1
        def swap_buffers(self):self.presented+=1
        def close(self):assert self.frames==self.presented==self.events==3
    with patch.object(preview,'Renderer',Screen),redirect_stdout(io.StringIO()):preview.run()
    assert len(instances)==1
    print('PASS controller pumps events and presents every frame; actual visible-window verification remains separate.')
def interactive_fixtures():
    from cymatics_view import BasinView,validate_pose
    from cymatics_preview import Experiment
    from types import SimpleNamespace
    import copy
    view=BasinView();view.sample(12.,True);view.button(0,True,100,100);view.move(150,125,800,600);view.button(0,False,150,125)
    yaw=view.yaw;view.sample(13.,True);assert view.yaw==yaw and view.manual
    view.sample(13.,False);before=view.yaw;pose,pan=view.sample(13.,True);assert abs(pose[0]-before)<1e-12 and not view.manual
    view.button(1,True,0,0);view.move(5000,-5000,800,600);view.button(1,False,5000,-5000);view.scroll(1000);assert view.distance==1.7 and all(abs(x)<=2 for x in view.pan)
    view.scroll(-1000);assert view.distance==10.;view.reset();assert view.config()==validate_pose()
    old=defaults();[old.pop(k) for k in ('camera','view_reset','finish','light_angle','dye_swirl')];assert validate(old,stored=True)['finish']=='obsidian'
    for data in ({'monitor':True,'source':'loopback'},{'camera':{'pitch':0.}},{'finish':'bad'}):
        try:validate(dict(defaults(),**data));raise AssertionError('Invalid accepted')
        except ValueError:pass
    class Player:
        def __init__(self):self.frames=[];self.closed=False
        def __enter__(self):return self
        def __exit__(self,*args):self.closed=True
        def play(self,pcm):self.frames.append(pcm.copy())
    with tempfile.TemporaryDirectory() as temporary:
        path=Path(temporary)/'monitor.wav';samples=np.round(np.sin(np.arange(12000)*math.tau*220/48000)*20000).astype(np.int16)
        with wave.open(str(path),'wb') as wav:wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(48000);wav.writeframes(samples.tobytes())
        c=defaults();c['source']='track';player=Player();monitor=Monitor(lambda:player)
        e=Experiment(SimpleNamespace(parameters=SimpleNamespace()),c,path,monitor);reference=Experiment(SimpleNamespace(parameters=SimpleNamespace()),c,path)
        c=copy.deepcopy(e.settings);c['monitor']=True;e.apply(c)
        for i in range(5):e.advance(.05);reference.advance(.05)
        assert e.index==reference.index and np.array_equal(e.renderer.cymatics.z,reference.renderer.cymatics.z)
        e.advance(.05);assert e.eof;monitor.drain();e.close();reference.close();assert player.closed and player.frames and not monitor.enabled
        assert max(float(np.max(np.abs(f))) for f in player.frames)<=.050001
    calls=[]
    def failed():calls.append(1);raise RuntimeError('controlled output failure')
    e=Experiment(SimpleNamespace(parameters=SimpleNamespace()),monitor=Monitor(failed));c=copy.deepcopy(e.settings);c['monitor']=True;e.apply(c);e.monitor.thread.join(.5);assert e.monitor.error and not e.monitor.enabled
    c['light_angle']=.4;e.apply(c);assert len(calls)==1 # unrelated edits never restart failed output
    c['monitor']=False;e.apply(c);c['monitor']=True;e.apply(c);e.monitor.thread.join(.5);assert len(calls)==2;e.close()
    print('PASS mouse view bounds/auto continuity/reset, old sessions, track monitor canonical PCM equivalence/headroom/EOF, failure latch and explicit retry; no hardware output.')

if __name__=='__main__':fixtures();extra_fixtures();presentation_fixture();interactive_fixtures()
