"""Standalone CPU metadata/selection/view/owner checks; no native UI/device."""
import argparse
import ast
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import time
from types import ModuleType,SimpleNamespace
import numpy as np

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work/planet-star-spectrum-tuning-01'
sys.path.insert(0,str(ROOT/'app/audio'))
from band_attack_tuning import (BASELINE,WINDOW_BASELINE,WINDOW_BOUNDS,BandAttackTuning,
    validate,weighted,curve_weights,window_settings)
from low_band_attack import LowBandAttack
from spectrum_widget import SpectrumFeed,frequencies,valid_packet
from starfield_tuning import StarfieldTuningWindow,decode,MAX_PACKET
from star_tuning_profiles import SHIPPED
from planet_canvas_dsp_test import audio_env,audio_state,tree
from starfield_tuning_test import controls_checks,exact_baseline_checks,fixture_checks,protocol_checks,live_owner_checks
from planet_star_attack_test import fixtures,simulate

def fft_frame(n=2048):
    t=np.arange(n);f=np.fft.rfftfreq(n,1/48000.)
    pcm=.25+.5*np.cos(2*np.pi*min(200,n//2-1)*t/n)+.125*np.cos(np.pi*t)
    m=np.abs(np.fft.rfft(pcm))
    return SimpleNamespace(spectrum_frequencies=f,spectrum_magnitudes=m),pcm

def spectrum_checks():
    f,pcm=fft_frame();before=f.spectrum_magnitudes.copy();clock=[1.]
    feed=SpectrumFeed(clock=lambda:clock[0]);feed.observe(f,2048);assert feed.raw is None
    feed.enable(True);feed.observe(f,2048);s=feed.snapshot()
    assert valid_packet(s) and len(s['db'])==1024 and s['nyquist_hz']==24000.
    assert s['bin_spacing_hz']==23.4375 and s['window_ms']==2048/48.
    assert [hz for hz in frequencies(s) if 60<=hz<100]==[70.3125,93.75]
    assert s['db'][199]==-6. and s['db'][-1]==-18.1 # Nyquist normalization1/N.
    assert np.array_equal(before,f.spectrum_magnitudes)
    copy=s['db'];copy[0]=0.;assert feed.snapshot()['db'][0]!=0.
    f.spectrum_magnitudes[200]=0.;assert feed.snapshot()['db'][199]==-6. # Own bounded copy.
    odd,_=fft_frame(2047);feed.observe(odd,2047);assert valid_packet(feed.snapshot())
    assert feed.snapshot()['max_frequency_hz']<feed.snapshot()['nyquist_hz']
    feed.observe(SimpleNamespace(spectrum_frequencies=None,spectrum_magnitudes=None),2048)
    assert feed.snapshot() is None and feed.error
    feed.enable(False);feed.observe(odd,2047);assert feed.raw is None
    frame,_=fft_frame();feed.enable(True);feed.observe(frame,2048);s=feed.snapshot()
    p=dict(version=1,pilot_active=True,revision=1,settings=WINDOW_BASELINE,spectrum=s)
    text=json.dumps(p,separators=(',',':'));assert decode(text) and len(text.encode())<MAX_PACKET
    for bad in [dict(s,sample_count=4096),dict(s,db=[float('nan')]*1024),dict(s,nyquist_hz=20000),dict(s,db=[])]:
        assert decode(json.dumps(dict(p,spectrum=bad))) is None
    return dict(positive_bins=1024,bin_spacing_hz=23.4375,nyquist_hz=24000.,DC_excluded=True,
        odd_packet_metadata=True,nyquist_normalization=True,copy_bounded=True,display_packet_bytes=len(text.encode()))

def window_checks():
    f,_=fft_frame();f.spectrum_magnitudes[:]=20.;baseline=20.
    tune=BandAttackTuning();detector=LowBandAttack()
    level,sens,summary=tune.apply(f,baseline,detector,'A');payload=detector.process(level,2048,'A');tune.completed(payload,summary)
    c=dict(WINDOW_BASELINE,start_hz=60.,end_hz=100.,weight=2.,sensitivity=1.25)
    assert tune.submit(1,c);level,sens,summary=tune.apply(f,baseline,detector,'A')
    assert type(level) is float and level==8. and sens==1.25 and detector.previous==8.
    payload=detector.process(level,2048,'A',sens);assert payload['bass_attack']==0. and payload['low_band_level']==8.;tune.completed(payload,summary)
    one=weighted(summary,dict(c,weight=1.));assert level==2.*one
    assert not tune.submit(2,dict(c,start_hz=141.,end_hz=142.))
    assert tune.rejected_revision==2 and tune.settings==c
    ack=tune.status(0,10.);assert ack['rejected_revision']==2 and ack['revision']==1 and ack['error']
    tune.submit(3,dict(WINDOW_BASELINE));level,sens,summary=tune.apply(f,baseline,detector,'A')
    assert level==baseline and sens==1. and detector.previous==baseline
    tune.submit(4,dict(c,enabled=False));assert tune.apply(f,baseline,detector,'A')[:2]==(baseline,1.)
    short=SimpleNamespace(spectrum_frequencies=np.array([0.,24000.]),spectrum_magnitudes=np.zeros(2))
    tune.submit(5,WINDOW_BASELINE);assert tune.apply(short,0.,detector,'A')[:2]==(0.,1.) and tune.revision==5
    for key,(lo,hi) in WINDOW_BOUNDS.items():
        for value in [lo-.01,hi+.01,float('nan'),True,'1']:
            try:validate(dict(WINDOW_BASELINE,**{key:value}))
            except ValueError:pass
            else:raise AssertionError((key,value))
    for c2 in [dict(WINDOW_BASELINE,start_hz=250,end_hz=20),dict(WINDOW_BASELINE,start_hz=100,end_hz=100)]:
        try:validate(c2)
        except ValueError:pass
        else:raise AssertionError('Unordered selection')
    assert window_settings(BASELINE)==WINDOW_BASELINE
    legacy=dict(BASELINE,low_weight=2.,body_weight=.5,upper_weight=1.5,extension=.4)
    assert window_settings(legacy) is None
    curve=curve_weights(f.spectrum_frequencies,legacy)
    assert curve[1]==2. and curve[2]==.5 and curve[7]==1.5 and curve[11]==legacy['upper_weight']*legacy['extension'] and not curve[14:].any()
    env={};exec(compile((OUT/'baseline/band_attack_tuning.py').read_text(encoding='utf8'),'prior-band-tuning','exec'),env)
    rng=np.random.default_rng(315);exact=0
    for _ in range(100):
        old=env['BandAttackTuning']();new=BandAttackTuning();f.spectrum_magnitudes[:]=rng.uniform(0,30,len(curve))
        baseline=float(f.spectrum_magnitudes[(f.spectrum_frequencies>=20)&(f.spectrum_frequencies<250)].mean())
        a=old.measure(f,baseline);b=new.measure(f,baseline)
        assert env['weighted'](a,legacy)==weighted(b,legacy);exact+=1
    return dict(ordered_and_nonempty=True,empty_selection_rejected=True,weight_not_normalized_away=True,
        exact_reset=True,bypass_exact=True,legacy_packets_exact=exact,unrepresentable_legacy_preserved=True,no_high_routing=True)

def observation_checks():
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');a=audio_state();b=audio_state()
    b[0]._planet_star_tuning=BandAttackTuning();b[0]._planet_star_tuning.submit(1,WINDOW_BASELINE)
    feed=SpectrumFeed();feed.enable(True);rng=np.random.default_rng(20261003)
    def equal(x,y):
        if isinstance(x,np.ndarray):return np.array_equal(x,y)
        if isinstance(x,dict):return x.keys()==y.keys() and all(equal(x[k],y[k]) for k in x)
        return x==y
    for _ in range(120):
        pcm=rng.normal(0,.06,(2048,2)).astype(np.float32)
        f=analyze(pcm,*a,descriptors=True,star_attack=True,source_id='same')
        g=analyze(pcm,*b,descriptors=True,star_attack=True,source_id='same')
        feed.observe(g,len(pcm));assert valid_packet(feed.snapshot()) and equal(f.__dict__,g.__dict__)
    return dict(entire_audio_frames_exact=120,spectrum_observation_changes_no_analysis=True,window_baseline_exact=True)

def rapid_window_checks():
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py')
    c=dict(WINDOW_BASELINE,start_hz=60.,end_hz=100.,weight=2.,sensitivity=1.25)
    def tuned(pcm,*state,**kw):
        if not hasattr(state[0],'_planet_star_tuning'):
            state[0]._planet_star_tuning=BandAttackTuning();state[0]._planet_star_tuning.submit(1,c)
        return analyze(pcm,*state,**kw)
    _,rows,events=simulate(fixtures()[0]['consecutive125ms'],tuned)
    assert events and all(b-a>=.08 for a,b in zip(events,events[1:]))
    assert all(1.<=r['rate']<=1.75 for r in rows) and all(b['phase']>=a['phase'] for a,b in zip(rows,rows[1:]))
    return dict(settings=c,accepted_proxy_events=len(events),source_events=23,guard_80ms=True,positive_phase=True,
        interpretation='Synthetic65Hz attack fixture; not instrument classification or a recommended current-song profile')

class Var:
    def __init__(self,value=None,**kw):self.value=value
    def get(self):return self.value
    def set(self,value):self.value=value

class Widget:
    all=[];focused=None
    def __init__(self,*args,**kw):
        self.kw=kw;self.parent=args[0] if args else None;self.grid_info={};self.hidden=False;self.bindings={};self.timers={};self.sequence=0;self.items={};self.exists=True;self.all.append(self)
    def pack(self,*a,**kw):pass
    def pack_forget(self):pass
    def grid(self,*a,**kw):
        if kw:self.grid_info=kw
        self.hidden=False
    def grid_remove(self):self.hidden=True
    def grid_slaves(self,row):return [w for w in self.all if w.parent is self and w.grid_info.get('row')==row]
    def columnconfigure(self,*a,**kw):pass
    def bind(self,event,fn,**kw):self.bindings[event]=fn
    def instate(self,states):return ('disabled' in states)==(self.kw.get('state')=='disabled')
    def focus_set(self):
        old=Widget.focused
        if old is self:return
        if old and '<FocusOut>' in old.bindings:old.bindings['<FocusOut>'](None)
        Widget.focused=self
        if '<FocusIn>' in self.bindings:self.bindings['<FocusIn>'](None)
    def focus_get(self):return Widget.focused
    def title(self,*a):pass
    def geometry(self,*a):pass
    def protocol(self,*a):pass
    def configure(self,**kw):self.kw.update(kw)
    def create_window(self,*a,**kw):return 1
    def yview(self,*a):pass
    def set(self,*a):pass
    def bbox(self,*a):return (0,0,840,1200)
    def itemconfigure(self,*a,**kw):pass
    def winfo_width(self):return 840
    def cget(self,key):return self.kw.get(key)
    def winfo_exists(self):return self.exists
    def destroy(self):self.exists=False
    def after(self,delay,fn):self.sequence+=1;self.timers[self.sequence]=(delay,fn);return self.sequence
    def after_cancel(self,identifier):self.timers.pop(identifier,None)
    def create_line(self,*args,**kw):self.sequence+=1;self.items[self.sequence]=(args,kw);return self.sequence
    create_text=create_line;create_rectangle=create_line;create_oval=create_line
    def delete(self,tag):self.items={k:v for k,v in self.items.items() if v[1].get('tags')!=tag}
    def coords(self,*a):pass
    def tag_raise(self,*a):pass

def view_checks():
    # Execute actual constructors and callbacks against inert widgets. Never Tk.
    tk=ModuleType('tkinter');ttk=ModuleType('tkinter.ttk');tk.ttk=ttk
    for name in ('Toplevel','Canvas'):setattr(tk,name,Widget)
    for name in ('StringVar','DoubleVar','BooleanVar'):setattr(tk,name,Var)
    for name in ('Frame','LabelFrame','Scrollbar','Label','Checkbutton','Scale','Button','Combobox','Entry'):setattr(ttk,name,Widget)
    saved={key:sys.modules.get(key) for key in ('tkinter','tkinter.ttk')}
    sys.modules['tkinter']=tk;sys.modules['tkinter.ttk']=ttk
    try:
        submitted=[];v=StarfieldTuningWindow(Widget(),lambda c:submitted.append(c) or len(submitted),lambda on:None)
        assert all(w.kw.get('state')=='disabled' for w in v.unsupported)
        frame,_=fft_frame();feed=SpectrumFeed();feed.enable(True);feed.observe(frame,2048)
        spectrum=feed.snapshot()
        p=dict(version=1,pilot_active=True,revision=0,settings=dict(BASELINE),state='reviewed baseline',analysis_age_seconds=0.,spectrum=spectrum)
        v.refresh((p,time.perf_counter()),True)
        assert v.settings()==BASELINE and len(v.spectrum.packet['db'])==1024
        v.vars['start_hz'].set(60.);v.vars['end_hz'].set(100.);v.vars['weight'].set(2.)
        for _ in range(1000):v.changed('weight')
        assert len(v.window.timers)==1
        # Requested position is not substituted into the applied curve.
        oldcurve=list(v.spectrum.weights);v.refresh((p,time.perf_counter()),True);assert list(v.spectrum.weights)==oldcurve
        _,callback=v.window.timers.pop(v.pending);callback()
        assert submitted[-1]==dict(dict(SHIPPED,**WINDOW_BASELINE),start_hz=60.,end_hz=100.,weight=2.)
        p.update(revision=1,settings=submitted[-1]);v.refresh((p,time.perf_counter()),True)
        assert '70.3125' in v.selection.get() and '93.7500' in v.selection.get()
        assert sum(v.spectrum.weights)==4. and 'applied revision 1' in v.applied.get()
        v.vars['start_hz'].set(141.);v.vars['end_hz'].set(142.);v.changed('start_hz')
        _,callback=v.window.timers.pop(v.pending);callback();assert len(submitted)==1 and 'rejected' in v.status.get()
        v.refresh((p,time.perf_counter()),True);assert 'rejected' in v.status.get() and sum(v.spectrum.weights)==4.
        legacy=dict(BASELINE,body_weight=.5,extension=.4)
        p.update(revision=3,settings=legacy);v.refresh((p,time.perf_counter()),True)
        assert v.settings()==legacy and 'cannot be represented' in v.compat.get()
        assert all(w.kw.get('state')=='disabled' for w in v.frequency_sliders)
        assert all(w.kw.get('state')=='disabled' for w in v.sliders[4:])
        v.vars['sensitivity'].set(1.4);v.changed('sensitivity');_,callback=v.window.timers.pop(v.pending);callback()
        assert submitted[-1]==dict(legacy,sensitivity=1.4)
        v.reset();_,callback=v.window.timers.pop(v.pending);callback();assert submitted[-1]==dict(SHIPPED,enabled=False)
        p.update(revision=len(submitted),settings=dict(SHIPPED,enabled=False),effective=SHIPPED,authored=SHIPPED);v.refresh((p,time.perf_counter()),True)
        p.update(revision=4,settings=dict(SHIPPED,enabled=False));v.revision=None;v.refresh((p,time.perf_counter()),True)
        assert 'AUTHORED baseline' in v.status.get() and v.spectrum.packet is not None and sum(v.spectrum.weights)==3.
        p.update(pilot_active=False);v.refresh((p,time.perf_counter()),True)
        assert 'full spectrum only' in v.status.get() and v.spectrum.packet is not None and sum(v.spectrum.weights)==0.
        assert all(w.kw.get('state')=='disabled' for w in v.unsupported+v.sliders)
        p.update(pilot_active=True);times=[]
        for i in range(200):
            p['spectrum']['sequence']=i+10;began=time.perf_counter();v.refresh((p,began),True);times.append((time.perf_counter()-began)*1000.)
            assert len(v.spectrum.canvas.items)<150
        v.preview_started();assert v.settings()==dict(SHIPPED,enabled=False) and v.spectrum.packet is None
        # This rollout deliberately extends Main command/ownership wiring.
        # Preserve the accepted pre-rollout storage functions against this task's
        # own dirty baseline, rather than an earlier historical assignment.
        baseline=tree(ROOT/'work/studio-audio-rollout-01/baseline/app/visuals/studio.py');current=tree(ROOT/'app/visuals/studio.py')
        def function(t,name):return next(n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name==name)
        for name in ('values','validate_session','save','load','new'):
            assert ast.dump(function(baseline,name),include_attributes=False)==ast.dump(function(current,name),include_attributes=False)
        import starfield_tuning
        original=starfield_tuning.StarfieldTuningWindow
        try:
            starfield_tuning.StarfieldTuningWindow=lambda *args,**kw:SimpleNamespace(alive=lambda:True,window=SimpleNamespace(lift=lambda:None))
            calls=[];root=SimpleNamespace(after_cancel=lambda timer:calls.append(('cancel',timer)))
            owner=SimpleNamespace(root=root,star_tuning_window=None,star_tuning_poll_after='old',
                submit_star_tuning=lambda c:None,show_star_tuning=lambda on:None,poll_star_tuning=lambda:calls.append(('poll',None)))
            env={};node=ast.Module(body=[deepcopy(function(current,'open_star_tuning'))],type_ignores=[])
            exec(compile(ast.fix_missing_locations(node),'actual-Studio-open','exec'),env)
            env['open_star_tuning'](owner);env['open_star_tuning'](owner);assert calls==[('cancel','old'),('poll',None)]
        finally:starfield_tuning.StarfieldTuningWindow=original
        return dict(actual_constructor_callbacks=True,unsupported_controls_disabled=True,ACK_curve_not_requested=True,
            real_bin_labels=True,coalesced_changes=1000,pending_slots=1,legacy_preserved=True,authored_reset=True,
            spectrum_visible_under_bypass_and_pilot_OFF=True,bounded_canvas_items=True,reopen_single_poll=True,Main_session_functions_unchanged=True,
            inert_repaint=dict(samples=len(times),p50_ms=float(np.median(times)),p95_ms=float(np.percentile(times,95)),
                limits='Actual callback/coordinates with inert widgets, no native Tk repaint measurement'))
    finally:
        for key,value in saved.items():
            if value is None:sys.modules.pop(key,None)
            else:sys.modules[key]=value
        Widget.all.clear();Widget.focused=None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    c=dict(WINDOW_BASELINE,start_hz=60.,end_hz=100.,weight=2.,sensitivity=1.25)
    result=dict(classification='CPU synthetic / inert UI constructors / exact real owner with mocked capture+graphics; no native UI/device/GPU/call audio',
        spectrum=spectrum_checks(),window=window_checks(),observation=observation_checks(),view=view_checks(),rapid_window=rapid_window_checks(),
        legacy_controls=controls_checks(),legacy_baseline=exact_baseline_checks(),fixtures=fixture_checks(),protocol=protocol_checks(),
        window_live_owner=live_owner_checks([c,dict(c,enabled=False),dict(WINDOW_BASELINE)]),
        pilot_OFF_live_owner=live_owner_checks(star_enabled=False))
    assert not any(n in sys.modules for n in ('glfw','moderngl','soundcard','tkinter','capture'))
    if args.output:args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));print('Spectrum tuning CPU checks PASS')

if __name__=='__main__':main()
