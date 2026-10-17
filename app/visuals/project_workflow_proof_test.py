"""Same editable12s proof: portable checkpoint,ONE native export,separate numerical checks.

Modes preserve completed export: prepare once,export once,verify can rerun on the
same movie/receipt without rendering again. No playback/audio device/production.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import argparse,sys,os,json,time,uuid,threading,hashlib,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test')
from project_manifest import read_state,binding,compile_plan,Journal,journal_lock,apply_plan,file_hash,stable
from project_service import read_project
from project_api import call
from project_cli import request
from studio_control_client import ControlClient
p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','export','verify']);p.add_argument('out',type=Path);p.add_argument('--proof',type=Path);p.add_argument('--manifest',type=Path);a=p.parse_args();out=a.out.resolve();ns='e360d7247a3c5f3fb9528f39f1efbbb9';client=None;endpoint=None
def write(name,value):(out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf8')
def state():return read_state(endpoint)
def op(action,wait=True,**kw):
 data=dict(op=action,operation_id=uuid.uuid4().hex,**binding(state()),**kw);r=request(endpoint,data,wait,180);assert r['ok'],r;return data,r
def owner():
 global client,endpoint
 os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/(a.mode+'-artwork')),ZERAWAVE_MEDIA_LIBRARY=str(out/(a.mode+'-library.json')));client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/(a.mode+'-owner.log'));endpoint=Path(client.snapshot['project']['endpoint'])
def mix(document,force_fallback=False):
 import numpy as np
 from project_evaluator import Evaluator
 from project_mixer import Mixer
 from video_project import duration,sample_at
 evaluator=Evaluator(document,'reference',0);mixer=Mixer(force_fallback=force_fallback);parts=[]
 try:
  total=sample_at(document,duration(document))
  for start in range(0,total,2048):parts.append(mixer.render(evaluator.audio_span(start,min(2048,total-start))))
  metrics=deepcopy(mixer.metrics);pcm=np.concatenate(parts)
 finally:mixer.close();assert mixer.budget.used==0
 return pcm,metrics
try:
 if a.mode=='prepare':
  out.mkdir(parents=True,exist_ok=False);assert a.proof and a.manifest;original=file_hash(a.proof);owner();op('open',path=str(a.proof.resolve()));before=deepcopy(state()['document']);manifest=json.loads(a.manifest.read_text(encoding='utf8'));manifest['save']['path']=str(out/'Workflow-proof-portable.zwv');plan=compile_plan(endpoint,manifest);assert len(plan['steps'])==1 and all(e['action']=='already applied' for e in plan['entities']);write('MANIFEST_INPUT.json',manifest);write('PLAN.json',plan)
  with journal_lock(out/'checkpoint-journal'):result=apply_plan(endpoint,Journal(out/'checkpoint-journal',plan))
  accepted=deepcopy(state()['document']);op('close');op('open',path=str(out/'Workflow-proof-portable.zwv'));opened=state()['document'];assert all(opened[k]==accepted[k]==before[k] for k in ('id','settings','tracks','clips','captions','graphics','buses','master'));assert [r['sha256'] for r in opened['media']]==[r['sha256'] for r in before['media']];assert len(opened['media'])==5 and len(opened['clips'])==5 and len(opened['captions'])==2 and len(opened['graphics'])==8 and opened['settings']==dict(width=1920,height=1080,fps=[30,1],sample_rate=48000,background='#000000');assert original==file_hash(a.proof);revision=state()['revision'];op('close');client.close();assert client.process.returncode==0;write('PREPARE_RESULT.json',dict(classification='Normal existing helper pinned portable Save As/actual owner reopen of SAME proof',revision=revision,helper=result,original_proof=str(a.proof),original_sha256=original,portable=str(out/'Workflow-proof-portable.zwv'),portable_sha256=file_hash(out/'Workflow-proof-portable.zwv'),all_entities_exact=True,original_unchanged=True,owner_exit=0))
 elif a.mode=='export':
  assert (out/'PREPARE_RESULT.json').is_file() and not (out/'Workflow-proof.mp4').exists() and not (out/'EXPORT_RECEIPT.json').exists(),'Completed movie/receipt already exists; use verify,never re-export.';owner();op('open',path=str(out/'Workflow-proof-portable.zwv'));frozen=deepcopy(state());write('FROZEN_DOCUMENT.json',frozen['document']);request_data,response=op('export',wait=False,path=str(out/'Workflow-proof.mp4'));write('EXPORT_REQUEST.json',request_data);began=time.perf_counter();samples=[];outcome=response['outcome']
  while outcome['status']=='exporting':
   assert time.perf_counter()-began<240,'Export still owned; inspect recorded SAME ID before any retry.';time.sleep(.1);result=call(endpoint,dict(op='operation_status',operation_id=request_data['operation_id']));outcome=result['outcome'];assert outcome is not None,'Uncertain retained outcome; no replacement ID.';samples.append(dict(seconds=time.perf_counter()-began,status=outcome['status'],progress=outcome.get('result',{})))
  write('EXPORT_RECEIPT.json',outcome);write('RAW_EXPORT_POLL.json',samples);assert outcome['status']=='exported',outcome;assert outcome['revision']==frozen['revision'] and state()['document']==frozen['document'] and outcome['result']['owned_resources_retired'];assert file_hash(out/'Workflow-proof.mp4')==outcome['result']['sha256'];op('close');client.close();assert client.process.returncode==0;write('EXPORT_RESULT.json',dict(classification='ONE completed native GL compositor/H264/AAC export through real owner; no playback/device',seconds=time.perf_counter()-began,revision=frozen['revision'],movie=str(out/'Workflow-proof.mp4'),sha256=file_hash(out/'Workflow-proof.mp4'),owner_exit=0,owned_resources_retired=True))
 else:
  assert (out/'EXPORT_RECEIPT.json').is_file();import numpy as np,av,soundfile as sf
  from PySide6.QtWidgets import QApplication
  from PySide6.QtGui import QImage
  from project_evaluator import Evaluator
  from project_media import Media
  from project_surface import ReferenceSurface
  from video_project import audio_defaults,duration,sample_at
  app=QApplication([]);d=json.loads((out/'FROZEN_DOCUMENT.json').read_text(encoding='utf8'));receipt=json.loads((out/'EXPORT_RECEIPT.json').read_text());movie=out/'Workflow-proof.mp4';assert file_hash(movie)==receipt['result']['sha256'];assert duration(d)==360 and sample_at(d,360)==576000;checks=[]
  narration=next(c for c in d['clips'] if c['id']==stable(ns,'clips','narration'));asset=next(r for r in d['media'] if r['id']==narration['asset']);source,rate=sf.read(asset['location']['path'],dtype='float32',always_2d=True);assert rate==48000 and len(source)==48017 and narration['duration']==31 and narration['pad_end']=='silence';assert file_hash(asset['location']['path'])==asset['sha256'];raw_doc=deepcopy(d);raw=deepcopy(narration);raw['audio']=dict(audio_defaults(),pan=0.);raw_doc.update(clips=[raw],captions=[],graphics=[]);pcm,raw_metrics=mix(raw_doc);fallback,fallback_metrics=mix(raw_doc,True);expected=np.repeat(source,2,axis=1);assert np.array_equal(pcm[:48017],expected) and np.array_equal(fallback,pcm);assert np.all(pcm[48017:]==0) and len(pcm)==49600 and np.all(pcm[48000:48017]!=0);checks.append('Exact native/fallback same-rate original48017samples include identifiable17sample tail; only remaining1583samples of final partial frame are silence before authored gains/fades')
  canonical,mix_metrics=mix(d);canonical_hash=hashlib.sha256(canonical.tobytes()).hexdigest();assert canonical_hash==receipt['result']['canonical_pcm_sha256'];(out/'reference-canonical-stereo.f32').write_bytes(canonical.tobytes());checks.append('Independent shared evaluator/Mixer full12s canonical PCM matches native-export receipt SHA exactly,with original fractions/integer fades/full music envelope/routing')
  frames=[];audio=[];first_packet=None;first_audio_pts=None;audio_samples=0
  with av.open(str(movie)) as container:
   stream=container.streams.audio[0]
   for packet in container.demux(stream):
    if packet.pts is not None:first_packet=dict(pts=packet.pts,dts=packet.dts,duration=packet.duration,time_base=str(packet.time_base));break
  with av.open(str(movie)) as container:
   for f in container.decode(audio=0):
    assert f.pts is not None
    if first_audio_pts is None:first_audio_pts=str(f.pts*f.time_base)
    assert f.pts*f.time_base==Fraction(audio_samples,48000);audio_samples+=f.samples;audio.append(f.to_ndarray().T.copy())
  decoded=np.concatenate(audio);assert len(canonical)<=len(decoded)<len(canonical)+1024 and first_audio_pts=='0';aligned=decoded[:len(canonical)];rms=float(np.sqrt(np.mean((aligned-canonical)**2)));corr=[float(np.corrcoef(aligned[:,i],canonical[:,i])[0,1]) for i in range(2)];assert rms<.006 and min(corr)>.99,(rms,corr);checks.append('Full AAC decode begins at0 with continuous sample timestamps; priming packet recorded,canonical alignment and <1024final padding accounted separately; lossy RMS/correlation pass declared tolerances')
  checkpoints=(0,45,179,180,210,299,300,359);decoded_frames={};count=0
  with av.open(str(movie)) as container:
   stream=container.streams.video[0];assert (stream.width,stream.height)==(1920,1080) and stream.average_rate==30
   for frame in container.decode(stream):
    assert frame.pts*frame.time_base==Fraction(count,30)
    if count in checkpoints:decoded_frames[count]=frame.to_ndarray(format='rgb24')
    count+=1
  assert count==360;media=Media();surface=ReferenceSurface();e=Evaluator(d,'cpu-reference',receipt['revision']);comparisons=[]
  try:
   for number in checkpoints:
    serial=media.submit(e.at(number));end=time.monotonic()+25
    while not media.ready():assert time.monotonic()<end;time.sleep(.002)
    prepared=media.take()
    try:
     assert not prepared['error'];image=surface.render(prepared).convertToFormat(QImage.Format_RGBA8888);reference=np.frombuffer(image.constBits(),np.uint8).reshape(1080,image.bytesPerLine())[:,:1920*4].reshape(1080,1920,4)[:,:,:3].copy();delta=np.abs(reference.astype(np.int16)-decoded_frames[number].astype(np.int16));row=dict(frame=number,mae=float(delta.mean()),p99=float(np.percentile(delta,99)),maximum=int(delta.max()),reference_sha256=hashlib.sha256(reference.tobytes()).hexdigest());comparisons.append(row);assert row['mae']<5 and row['p99']<35,row
     if number in (45,210,300):image.save(str(out/('REFERENCE-'+str(number)+'.png')));QImage(decoded_frames[number].tobytes(),1920,1080,QImage.Format_RGB888).save(str(out/('DECODED-'+str(number)+'.png')))
    finally:media.release(serial)
  finally:surface.close();media.close();media.thread.join(25);assert media.exited()
  checks.append('Exactly360native1920x1080/30frames with exact timestamps;8decoded checkpoints across shots/entrances/card/timer/still match CPU reference within declared lossy/compositor tolerances')
  assert file_hash(movie)==receipt['result']['sha256'];write('VERIFY_RESULT.json',dict(classification='Numerical exact PCM,separate AAC lossy and decoded video/CPU references; no device/listening/scanout certificate',checks=checks,movie_sha256=file_hash(movie),frames=count,canonical_samples=len(canonical),canonical_pcm_sha256=canonical_hash,raw_original_samples=len(source),raw_tail_samples=17,raw_padding_samples=len(pcm)-len(source),aac=dict(first_packet=first_packet,first_decoded_pts=first_audio_pts,decoded_samples=len(decoded),padding_samples=len(decoded)-len(canonical),rms=rms,channel_correlations=corr,tolerances=dict(rms_lt=.006,correlation_gt=.99)),video=dict(checkpoints=comparisons,tolerances=dict(mae_lt=5,p99_lt=35)),resources=dict(raw=raw_metrics,fallback=fallback_metrics,mix=mix_metrics,reference_media_exited=True),reused='Stage1 separate44.1kHz resampler references/human Source agreement remain source-bound unchanged; no audio-engine change in Stage5.',unverified='Physical display/audio correlation,listening,continuous real-time preview and historical whole-editor HOLD remain open.'))
 print('PASS',a.mode,out)
except BaseException:
 if out.is_dir():(out/('FAILURE-'+a.mode+'-'+str(time.time_ns())+'.txt')).write_text(traceback.format_exc(),encoding='utf8')
 raise
finally:
 if client and not client.closed:
  for outcome in state().get('operations',[]):
   if outcome['status'] in ('preparing','saving','exporting'):call(endpoint,dict(op='cancel',operation_id=outcome['id']))
  end=time.monotonic()+30
  while any(o['status'] in ('preparing','saving','exporting') for o in state().get('operations',[])) and time.monotonic()<end:time.sleep(.03)
  client.close(mode='discard',project_mode='discard')
