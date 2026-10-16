"""Standalone model/owner/SRT regression; no device or physical UI claim."""
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from fractions import Fraction
import os,uuid,time,json,threading
import video_project as v
from project_service import ProjectService,read_project,write_project
from project_text import parse_srt
from project_caption_export import encode_srt,write_srt
from project_visual import evaluated_layout

def run(folder):
 folder=Path(folder);checks=[];uid=lambda:uuid.uuid4().hex;s=ProjectService()
 def request(op,**args):
  b=dict(expected_project=s.document['id'] if s.document else None,expected_epoch=s.epoch,expected_revision=s.revision,expected_command=s.command_revision)
  result=s.request(dict(op=op,operation_id=uid(),**b,**args));assert result['ok'],result
  key=result['outcome']['id'];limit=time.monotonic()+15
  while key in s.jobs:
   s.poll();assert time.monotonic()<limit;time.sleep(.001)
  row=s.outcomes[key];assert row['status'] in ('accepted','durable','exported'),row;return row
 try:
  request('new');track,caption,title=uid(),uid(),uid();request('batch',changes=[dict(op='track.add',id=track,kind='graphics'),dict(op='caption.add',id=caption,track=track,start=7,duration=111,text='Dedicated caption\nSecond line'),dict(op='graphic.add',id=title,track=track,start=4,duration=40,text='Distinct title')]);original=deepcopy(s.document)
  for fps in ([30,1],[30000,1001],[24000,1001]):
   doc=deepcopy(original);doc['settings']['fps']=fps;raw=encode_srt(doc);path=folder/('roundtrip-'+str(fps[0])+'.srt');path.write_bytes(raw);changes=parse_srt(path,track,fps,uid(),threading.Event());cue=changes[1];assert (cue['start'],cue['duration'],cue['text'])==(7,111,'Dedicated caption\nSecond line');assert len(changes)==2
  checks.append('Dedicated captions export independently of titles; 30/30000-1001/24000-1001 SRT millisecond timing reimports to exact start/out frames and multiline text')
  dest=folder/'frozen.srt';revision=s.revision;before_history=len(s.undo);row=request('export_captions',path=str(dest));assert row['revision']==revision and len(s.undo)==before_history and s.document==original and s.saved_revision is None;raw=dest.read_bytes();assert row['result']['sha256']==__import__('hashlib').sha256(raw).hexdigest()
  for path in (dest,):
   try:write_srt(original,revision,path,threading.Event());raise AssertionError('Overwrite admitted')
   except v.ProjectError as e:assert e.code=='destination_exists'
   assert path.read_bytes()==raw
  protected=deepcopy(original);protected['protected_paths']=[str(folder/'source.srt')]
  try:write_srt(protected,0,folder/'source.srt',threading.Event());raise AssertionError('Source overwrite admitted')
  except v.ProjectError as e:assert e.code=='protected_source'
  cancel=threading.Event();cancel.set()
  try:write_srt(original,revision,folder/'cancelled.srt',cancel);raise AssertionError('Cancel ignored')
  except v.ProjectError as e:assert e.code=='cancelled'
  assert not (folder/'cancelled.srt').exists();checks.append('Owner export pins revision without artwork history/saved-state changes; original/existing paths and cancellation protected before atomic publication')
  os.environ['ZERAWAVE_PROJECT_TEST_WRITE_FAILURE']='1'
  try:
   try:write_srt(original,revision,folder/'failed.srt',threading.Event());raise AssertionError('Write failure ignored')
   except OSError:pass
  finally:os.environ.pop('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE',None)
  assert not (folder/'failed.srt').exists();request('export_captions',path=str(folder/'recovered.srt'));assert s.document==original
  invalid=deepcopy(original);invalid['captions'][0]['text']='blank\n\nparagraph'
  try:encode_srt(invalid);raise AssertionError('Lossy roundtrip silently accepted')
  except v.ProjectError as e:assert e.code=='caption_roundtrip'
  checks.append('Real worker resumes after write failure in same owner; unsupported blank-paragraph roundtrip rejects explicitly and exact rich captions stay accepted')
  # New visual commands use the same atomic model and owner receipts.
  asset,picture,left,right=uid(),uid(),uid(),uid();doc,_=v.apply(v.create('Visual contracts',dict(width=64,height=48)),[dict(op='media.add',id=asset,name='Placeholder',kind='Video',location=dict(kind='external',path=str(folder/'placeholder.mp4')),sha256='a'*64,metadata=dict(width=64,height=48,duration=12)),dict(op='track.add',id=picture,kind='video'),dict(op='clip.add',id=left,asset=asset,track=picture,start=0,duration=180),dict(op='clip.add',id=right,asset=asset,track=picture,start=180,duration=180,source_in=[6,1])],uid())
  base=deepcopy(doc)
  for change in [dict(op='keyframe.remove',id=left,parameter='opacity',frame=True),dict(op='keyframe.remove',id=left,parameter='opacity',frame=-1)]:
   try:v.apply(doc,[change],uid());raise AssertionError('Malformed absent key accepted')
   except v.ProjectError:pass
   assert doc==base
  doc,ids=v.apply(doc,[dict(op='effect.add',id=left,kind='Contrast',amount=1.5),dict(op='keyframe.set',id=left,parameter='opacity',frame=0,value=.3,interpolation='Hold'),dict(op='keyframe.set',id=left,parameter='opacity',frame=90,value=.9)],uid());assert evaluated_layout(doc['clips'][0],89)['opacity']==.3
  write_project(doc,8,None,folder/'visual.zwv',False,threading.Event(),True);loaded=read_project(folder/'visual.zwv',threading.Event())[0];assert loaded==doc
  checks.append('Malformed key deletion rejects even when parameter has no keys; effects and exact Hold keys survive real write/read unchanged')
  animated,_=v.apply(original,[dict(op='keyframe.set',id=title,parameter='opacity',frame=0,value=.2),dict(op='keyframe.set',id=title,parameter='opacity',frame=30,value=.8),dict(op='keyframe.set',id=title,parameter='bounds.0',frame=0,value=.1),dict(op='keyframe.set',id=title,parameter='bounds.0',frame=30,value=.3)],uid())
  from project_visual import evaluated_text
  from project_evaluator import Evaluator
  expected=evaluated_text(animated['graphics'][0],19);assert abs(expected['style']['opacity']-.5)<1e-10 and abs(expected['style']['bounds'][0]-.2)<1e-10
  plan=Evaluator(animated,'title',1).at(19);assert next(r for r in plan['text'] if r['recipe']['id']==title)['recipe']['style']==expected['style']
  split,ids=v.apply(animated,[dict(op='items.split',ids=[title],at=15)],uid());part=next(r for r in split['graphics'] if r['id'] in ids);assert evaluated_text(part,19)['style']==expected['style'] and part['visual_window']['offset']==11
  trimmed,_=v.apply(animated,[dict(op='items.trim',id=title,start=10,end=44)],uid());assert evaluated_text(trimmed['graphics'][0],19)['style']==expected['style']
  write_project(animated,9,None,folder/'animated-title.zwv',False,threading.Event());assert read_project(folder/'animated-title.zwv',threading.Event())[0]==animated
  checks.append('Title transform/opacity keys use identical exact evaluator policy; text trim/split preserve local origin and real save/reopen keeps every key/style')
  return dict(classification=__doc__,checks=checks)
 finally:
  for job in s.jobs.values():job['cancel'].set()
  while s.jobs:s.poll();time.sleep(.001)
  s.shutdown()

if __name__=='__main__':
 with TemporaryDirectory(prefix='zerawave-visual-authoring-') as folder:result=run(folder)
 print(json.dumps(result,indent=2))
