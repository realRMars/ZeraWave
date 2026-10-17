"""Derived owner-report/real PCM comparisons; generated sources, no output device."""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import sys, json, threading, uuid, hashlib, time, traceback, importlib.util
root=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
import numpy as np
from video_project import create, apply, sample_at, new_id, ProjectError
from media_registry import inspect
from project_audio_inspection import inspect_audio, describe
from project_evaluator import Evaluator
from project_mixer import Mixer
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
inputs=Path(sys.argv[2]);baseline=Path(sys.argv[3]);checks=[];timings=[];comparisons=[]
spec=importlib.util.spec_from_file_location('before_inspection_mixer',baseline);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
epoch=new_id();revision=11
def edit(d,*changes):return apply(d,list(changes),new_id())[0]
def query(d,**kw):return inspect_audio(d,epoch,revision,dict(op='audio_inspect',expected_epoch=epoch,expected_revision=revision,expected_project=d['id'],**kw),{a['id']:dict(status='Ready') for a in d['media']})
def pcm(d,sample,count=1,fallback=False,legacy=False):
    m=(old.Mixer if legacy else Mixer)(force_fallback=fallback)
    try:r=m.render(Evaluator(d,epoch,revision).audio_span(sample,count));return r,deepcopy(m.metrics)
    finally:m.close();assert m.budget.used==0 and not m.readers
def match(d,frame,label,fallback=False):
    at=sample_at(d,frame);r=query(d,sample=at,clips=[clip],tracks=[track]);point=r['contributions'][0]['observations'][0]
    actual,metrics=pcm(d,at,17,fallback);before,_=pcm(d,at,17,fallback,True)
    assert np.array_equal(actual,before),(label,np.max(abs(actual-before)))
    factors=np.array([v['linear'] for v in point['routed_channel_multiplier']],np.float32)
    assert np.array_equal(actual[0],factors),(label,actual[0],factors,point['gates'])
    comparisons.append(dict(case=label,frame=frame,sample=at,channels=actual[0].tolist(),gates=point['gates'],backend=metrics['backends'],legacy_max_error=float(np.max(abs(actual-before)))))
    return r,point
try:
    asset,track,clip,bus,marker=[new_id() for _ in range(5)]
    path=inputs/'unity-voice.wav';meta=inspect(str(path),threading.Event())['metadata']
    d=edit(create('Audio inspection proof',dict(width=1920,height=1080,fps=[30,1])),
        dict(op='media.add',id=asset,name='Unity voice',kind='Audio',location=dict(kind='external',path=str(path)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=meta),
        dict(op='track.add',id=track,kind='audio',name='Dialogue'),dict(op='bus.add',id=bus,name='Dialogue bus'),dict(op='track.output',id=track,output=bus),
        dict(op='track.add',id=marker,kind='graphics'),dict(op='graphic.add',track=marker,start=0,duration=360,text='12-second shared proof'),
        dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=233,pad_end='silence',audio=dict(gain=.04)),
        dict(op='track.audio',id=track,values=dict(gain=10**(12/20))))
    snapshot=deepcopy(d);r,p=match(d,30,'Exact +12 dB');expected=.04*10**(12/20)
    assert abs(p['channel_multiplier'][0]['linear']-expected)<2e-8 and abs(p['track']['gain']['db']-12)<1e-12
    half=edit(d,dict(op='clip.audio',id=clip,values=dict(envelope=[[0,.5],[233,.5]])))
    _,p=match(half,30,'Half envelope');assert abs(p['channel_multiplier'][0]['linear']-expected*.5)<1e-8 and abs(p['clip']['envelope']['db']+6.020599913279624)<1e-10
    four=edit(d,dict(op='track.audio',id=track,values=dict(gain=4.)))
    _,p=match(four,30,'Control ceiling 4 is not +12 dB');assert abs(p['track']['gain']['db']-12.041199826559248)<1e-10
    checks.append('Unity PCM/report exact +12dB versus gain4, half-envelope -6.020599913dB; before-migration mixer bit identity')
    shaped=edit(d,dict(op='clip.audio',id=clip,values=dict(gain=.4,pan=.25,fade_in=30,fade_out=60,envelope=[[0,.1],[45,.7],[200,.3],[233,0]])),dict(op='track.audio',id=track,values=dict(gain=.8,pan=-.3,fade_in=15,fade_out=60,envelope=[[0,.7],[120,.3],[360,1]])),dict(op='bus.edit',id=bus,values=dict(gain=.7,balance=.2)),dict(op='master.audio',values=dict(gain=.6)))
    for f in [0,1,20,45,119,210,232]:match(shaped,f,'Fades/envelopes/pan/bus/Master '+str(f))
    match(shaped,45,'Supported SoundFile fallback',True)
    trimmed=edit(shaped,dict(op='clip.trim',id=clip,start=10,end=230,linked=False))
    _,p=match(trimmed,20,'Trim retains original local window');assert p['clip_local_frame']==[20,1]
    split=edit(trimmed,dict(op='clip.split',id=clip,at=110,linked=False))
    for f in [20,109,110,150,229]:
        before,_=pcm(trimmed,sample_at(trimmed,f),17);after,_=pcm(split,sample_at(split,f),17);assert np.array_equal(before,after)
        report=query(split,frame=f,tracks=[track]);point=report['contributions'][0]['observations'][0];assert np.array_equal(after[0],np.array([x['linear'] for x in point['routed_channel_multiplier']],np.float32))
    checks.append('Clip/sequence envelopes, retained trims/splits, fades, per-channel balances, nonunity bus/Master and fallback match canonical PCM; no authored recipe mutation')
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise

try:
    for label,changes in [
        ('clip mute',[dict(op='clip.audio',id=clip,values=dict(mute=True))]),
        ('track mute',[dict(op='track.audio',id=track,values=dict(mute=True))]),
        ('bus mute',[dict(op='bus.edit',id=bus,values=dict(mute=True))]),
        ('Master mute',[dict(op='master.audio',values=dict(mute=True))]),
        ('None track route',[dict(op='track.output',id=track,output=None)]),
        ('None bus output',[dict(op='bus.edit',id=bus,values=dict(output=None))]),
        ('zero envelope',[dict(op='clip.audio',id=clip,values=dict(envelope=[[0,0],[233,0]]))])]:
        test=edit(d,*changes);r,p=match(test,30,label);assert not any(v['linear'] for v in p['routed_channel_multiplier']) and p['gates'];assert not query(test,range=[0,360],tracks=[track])['coverage'][0]['routed_nonzero_multiplier']
    another=new_id();solo=edit(d,dict(op='track.add',id=another,kind='audio'),dict(op='track.edit',id=another,values=dict(solo=True)))
    _,p=match(solo,30,'Solo exclusion');assert 'solo_exclusion' in p['gates']
    missing=deepcopy(d);missing['buses']=[];r=query(missing,frame=30);assert r['mix_state']=='blocked_missing_route' and 'missing_route' in r['contributions'][0]['observations'][0]['gates']
    try:pcm(missing,48000);raise AssertionError('Missing route rendered')
    except ValueError as exc:assert 'Missing audio destination' in str(exc)
    checks.append('Explicit mute/solo/None/missing route and zero envelope retain authored factors but explain excluded PCM; missing route blocks whole canonical mix')
    coverage=query(d,range=[0,360],tracks=[track])['coverage'][0]
    assert coverage['source_available']==[[0,372000]] and coverage['source_uncovered']==[[372000,576000]],coverage
    r=query(d,sample=372100);assert 'intentional_end_padding' in r['contributions'][0]['observations'][0]['gates']
    r=query(d,frame=300);assert not r['contributions'] and r['coverage'][0]['gates']==['absent_clip'] and 'higher fader cannot fill' in describe(r)
    unknown=inspect_audio(d,epoch,revision,dict(op='audio_inspect',expected_epoch=epoch,expected_revision=revision,expected_project=d['id'],range=[0,360]),{})
    assert unknown['coverage'][0]['availability_unverified']==[[0,372000]] and not unknown['coverage'][0]['source_available']
    gates=deepcopy(d);gates['clips'][0]['audio']['envelope']=[[0,0],[30,0],[60,1],[90,0],[120,0],[150,1]]
    r=query(gates,range=[0,233],tracks=[track]);intervals=r['coverage'][0]['routed_nonzero_multiplier'];assert intervals==[[48001,144000],[192001,372000]],intervals
    # Compare every integer sample's reported support with real PCM, bounded 7.75s.
    actual=[];e=Evaluator(gates,epoch,revision);m=Mixer()
    try:
        for start in range(0,372800,2048):actual.extend(np.any(m.render(e.audio_span(start,min(2048,372800-start)))>0,axis=1))
    finally:m.close();assert m.budget.used==0
    mask=np.zeros(372800,bool)
    for a,b in intervals:mask[a:b]=True
    # Last17 real source samples are a signal tail, not a gain gate.
    assert np.array_equal(mask[:-17-800],np.asarray(actual)[:-17-800])
    checks.append('Exact source sample extent/end padding, absent clip and unknown validation separated; zero-envelope support checked against every canonical sample without claiming actual decoded silence')
    # A real native dissolve plan supplies retained clip-local transition fades.
    from PySide6.QtGui import QImage
    picture=out/'transition-picture.png';image=QImage(64,64,QImage.Format_RGBA8888);image.fill(0xff123456);assert image.save(str(picture));del image
    ia,vt,vl,vr,ar,ll,lr=[new_id() for _ in range(7)]
    trans=edit(d,dict(op='clip.remove',id=clip,linked=False),dict(op='media.add',id=ia,name='Transition picture',kind='Image',location=dict(kind='external',path=str(picture)),sha256=hashlib.sha256(picture.read_bytes()).hexdigest(),metadata=dict(width=64,height=64)),dict(op='track.add',id=vt,kind='video'),dict(op='clip.add',id=vl,asset=ia,track=vt,start=0,duration=60,link_id=ll),dict(op='clip.add',id=vr,asset=ia,track=vt,start=60,duration=60,source_in=[2,1],link_id=lr),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=60,link_id=ll,audio=dict(gain=.04)),dict(op='clip.add',id=ar,asset=asset,track=track,start=60,duration=60,source_in=[2,1],link_id=lr,audio=dict(gain=.02)),dict(op='transition.add',left=vl,right=vr,duration=30))
    for frame in [44,45,59,60,74,75]:
        at=sample_at(trans,frame);actual,_=pcm(trans,at,17);before,_=pcm(trans,at,17,legacy=True);r=query(trans,frame=frame,tracks=[track]);factors=np.sum([[x['linear'] for x in row['observations'][0]['routed_channel_multiplier']] for row in r['contributions']],axis=0)
        assert np.array_equal(actual,before) and np.max(abs(actual[0]-factors))<3e-8
        comparisons.append(dict(case='Linked dissolve '+str(frame),sample=at,channels=actual[0].tolist(),summed_report=factors.tolist(),legacy_max_error=0.))
    rational_doc=deepcopy(d);rational_doc['settings']['fps']=[30000,1001];match(rational_doc,90,'Fractional frame/sample mapping')
    fast=edit(d,dict(op='clip.remove',id=clip,linked=False),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=233,pad_end='silence',rate=[3,2],audio=dict(gain=.04)))
    match(fast,45,'Rational source playback rate')
    import soundfile as sf
    silence=out/'actual-silence.wav';sf.write(silence,np.zeros((48000,2),np.float32),48000,subtype='FLOAT')
    silent=edit(d,dict(op='clip.remove',id=clip,linked=False),dict(op='media.relink',id=asset,kind='Audio',location=dict(kind='external',path=str(silence)),sha256=hashlib.sha256(silence.read_bytes()).hexdigest(),metadata=inspect(str(silence),threading.Event())['metadata'],accept_changed=True),dict(op='clip.add',id=clip,asset=asset,track=track,start=0,duration=30,audio=dict(gain=.04)))
    signal,_=pcm(silent,1600);r=query(silent,frame=1);p=r['contributions'][0]['observations'][0];assert not signal.any() and p['routed_channel_multiplier'][0]['linear']>0 and p['pcm_measurement']['decoded_silence']=='unverified'
    checks.append('Real linked-dissolve plan and fractional frame/source rates preserve canonical PCM; actual silent file is distinguished from derived nonzero gain and never reported as measured audibility')
    tiny=edit(d,dict(op='clip.audio',id=clip,values=dict(gain=1e-36,fade_in=233)),dict(op='track.audio',id=track,values=dict(gain=1e-6)))
    r=query(tiny,range=[0,1],tracks=[track]);intervals=r['coverage'][0]['routed_nonzero_multiplier'];mask=np.zeros(1600,bool)
    for a,b in intervals:mask[a:b]=True
    actual,_=pcm(tiny,0,1600);assert np.array_equal(mask,np.any(actual>0,axis=1))
    try:query(tiny,range=[0,360],tracks=[track]);raise AssertionError('Unbounded subnormal coverage')
    except ProjectError as exc:assert exc.code=='inspection_capacity'
    checks.append('Rare float32 underflow/zero support uses exact bounded samples; oversized exact work rejects the report with narrow-range guidance, accepted document/mix unchanged')
    original=deepcopy(d)
    for _ in range(20):
        began=time.perf_counter_ns();r=query(d,range=[0,360]);timings.append((time.perf_counter_ns()-began)/1e6)
    assert d==original==snapshot
    for bad in [dict(frame=1,sample=1),dict(range=[10,10]),dict(frame=360),dict(frame=1,tracks=[new_id()]),dict(frame=1,limit=129),dict(frame=1,tracks=[track,track])]:
        try:query(d,**bad);raise AssertionError('Invalid query accepted '+str(bad))
        except ProjectError:pass
    checks.append('Read-only repeated bound report, malformed ranges/selectors/capacity rejected; raw20 latency samples retained')
    (out/'MODEL-PROOF.json').write_text(json.dumps(d,indent=2),encoding='utf8')
    (out/'REPORT.json').write_text(json.dumps(query(d,range=[0,360]),indent=2),encoding='utf8')
    (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,comparisons=comparisons,query_ms=timings,summary_ms=dict(count=len(timings),median=float(np.median(timings)),p95=float(np.percentile(timings,95)),maximum=max(timings)),classification=__doc__,baseline_mixer=str(baseline),baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest()),indent=2),encoding='utf8');print('PASS',len(checks),len(comparisons))
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
