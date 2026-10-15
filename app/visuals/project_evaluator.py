"""One immutable rational timeline evaluation shared by preview and export.

No clocks, decoders, authoring edits or graphics/audio device ownership here.
"""
from copy import deepcopy
from fractions import Fraction
from video_project import validate,integer,frame_time,sample_at,duration,rational,LIMITS,fail

class Evaluator:
 def __init__(self,document,epoch,revision):
  self.document=validate(document);self.epoch=epoch;self.revision=revision;self.end=duration(document)
  self.assets={a['id']:a for a in self.document['media']};self.tracks={t['id']:t for t in self.document['tracks']}
 def at(self,frame):
  integer(frame,0,max(0,self.end));d=self.document;visual=[];audio=[]
  for c in d['clips']:
   if not c['start']<=frame<c['start']+c['duration']:continue
   asset=self.assets[c['asset']];track=self.tracks[c['track']];source=rational(c['source_in'])+frame_time(d,frame-c['start'])*rational(c['rate'])
   item=dict(clip=deepcopy(c),asset=deepcopy(asset),track=deepcopy(track),source_time=[source.numerator,source.denominator])
   (audio if track['kind']=='audio' else visual).append(item)
  visual.sort(key=lambda r:(r['track']['order'],r['clip']['start'],r['clip']['id']))
  audio.sort(key=lambda r:(r['track']['order'],r['clip']['id']))
  text=[]
  for category in ('captions','graphics'):
   for row in d[category]:
    if row['start']<=frame<row['start']+row['duration']:text.append(dict(category=category,recipe=deepcopy(row),track=deepcopy(self.tracks[row['track']])))
  text.sort(key=lambda r:(r['track']['order'],r['recipe']['order'],r['recipe']['id']))
  time=frame_time(d,frame)
  return dict(project=d['id'],epoch=self.epoch,revision=self.revision,frame=frame,end=self.end,time=[time.numerator,time.denominator],sample=sample_at(d,frame),visual=visual,audio=audio,text=text,settings=deepcopy(d['settings']))

 def audio_span(self,start,count):
  integer(start,0,sample_at(self.document,self.end));integer(count,1,2048);d=self.document;total=sample_at(d,self.end);count=min(count,total-start)
  if count<=0:return dict(project=d['id'],epoch=self.epoch,revision=self.revision,start=start,count=0,audio=[],fps=deepcopy(d['settings']['fps']),end_frame=self.end)
  audio=[]
  for clip in d['clips']:
   track=self.tracks[clip['track']]
   if track['kind']!='audio':continue
   left=max(start,sample_at(d,clip['start']));right=min(start+count,sample_at(d,clip['start']+clip['duration']))
   if right<=left:continue
   source=rational(clip['source_in'])+(Fraction(left,d['settings']['sample_rate'])-frame_time(d,clip['start']))*rational(clip['rate'])
   audio.append(dict(clip=deepcopy(clip),track=deepcopy(track),asset=deepcopy(self.assets[clip['asset']]),offset=left-start,count=right-left,source_time=[source.numerator,source.denominator]))
  audio.sort(key=lambda r:(r['track']['order'],r['clip']['id']))
  return dict(project=d['id'],epoch=self.epoch,revision=self.revision,start=start,count=count,audio=audio,fps=deepcopy(d['settings']['fps']),end_frame=self.end)

def exact_clip_source(document,clip,frame):
 return rational(clip['source_in'])+frame_time(document,frame-clip['start'])*rational(clip['rate'])
