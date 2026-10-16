"""Bounded visual authoring/evaluation policy; renderer and media owners stay put."""
from copy import deepcopy
from fractions import Fraction
import uuid

EFFECTS={'Brightness':(0.,4.,1.),'Contrast':(0.,4.,1.)}
OP_FIELDS={
 'effect.add':(('id','kind'),('effect_id','amount')),
 'effect.edit':(('id','effect','values'),()),
 'effect.move':(('id','effect','index'),()),'effect.remove':(('id','effect'),()),
 'keyframe.set':(('id','parameter','frame','value'),('interpolation',)),
 'keyframe.remove':(('id','parameter','frame'),()),'keyframe.clear':(('id','parameter'),()),
 'transition.add':(('left','right','duration'),('id',)),
 'transition.edit':(('id','duration'),()),'transition.remove':(('id',),())}
def model():import video_project;return video_project
def parameter(layout,name):
 v=model()
 if name in ('bounds.0','bounds.1'):return (-4.,4.)
 if name in ('bounds.2','bounds.3'):return (.001,8.)
 if name=='rotation':return (-36000.,36000.)
 if name=='opacity':return (0.,1.)
 if name=='brightness':return (0.,4.)
 if isinstance(name,str) and name.startswith('effect.') and name.endswith('.amount'):
  key=name[7:-7];effect=next((e for e in layout.get('effects',[]) if e['id']==key),None)
  if effect:return EFFECTS[effect['kind']][:2]
 v.fail('invalid_visual_parameter','Choose transform, opacity, brightness or an existing supported effect amount.')
def read_parameter(layout,name):
 parameter(layout,name)
 if name.startswith('bounds.'):return layout['bounds'][int(name[-1])]
 if name.startswith('effect.'):return next(e['amount'] for e in layout['effects'] if e['id']==name[7:-7])
 return layout.get(name,{'opacity':1.,'rotation':0.,'brightness':1.}.get(name))
def write_parameter(layout,name,value):
 if name.startswith('bounds.'):layout['bounds'][int(name[-1])]=value
 elif name.startswith('effect.'):next(e for e in layout['effects'] if e['id']==name[7:-7])['amount']=value
 else:layout[name]=value
def validate_layout(layout):
 v=model();effects=layout.get('effects',[]);keys=layout.get('keys',[])
 if not isinstance(effects,list) or len(effects)>8:v.fail('effect_capacity','At most8 ordered Brightness/Contrast effects per picture clip.')
 seen=set()
 for effect in effects:
  v.fields(effect,('id','kind','enabled','amount'));v.identity(effect['id'])
  if effect['id'] in seen:v.fail('duplicate_id','Effect IDs must be unique within their clip.')
  seen.add(effect['id'])
  if effect['kind'] not in EFFECTS or type(effect['enabled']) is not bool:v.fail('invalid_effect','Supported effects: Brightness and Contrast, with boolean bypass.')
  v.number(effect['amount'],*EFFECTS[effect['kind']][:2])
 if not isinstance(keys,list) or len(keys)>16:v.fail('keyframe_capacity','At most16 visual parameter tracks per clip.')
 seen=set();total=0
 for channel in keys:
  v.fields(channel,('parameter','points'));name=channel['parameter'];low,high=parameter(layout,name)
  if name in seen:v.fail('duplicate_keyframe','One keyframe track per parameter.')
  seen.add(name);points=channel['points']
  if not isinstance(points,list) or not 1<=len(points)<=256:v.fail('keyframe_capacity','Each visual parameter uses1–256 explicit keys.')
  previous=-1;total+=len(points)
  for point in points:
   if not isinstance(point,list) or len(point)!=3:v.fail('invalid_keyframe','Keys are [integer local frame, value, Linear/Hold].')
   v.integer(point[0],0,120*24*3600);v.number(point[1],low,high)
   if point[0]<=previous or point[2] not in ('Linear','Hold'):v.fail('invalid_keyframe','Keys increase strictly; outgoing interpolation is Linear or Hold.')
   previous=point[0]
 if total>2048:v.fail('keyframe_capacity','At most2048 visual keys per clip, within document metadata capacity.')
 if 'crop' in layout:
  crop=layout['crop']
  if not isinstance(crop,list) or len(crop)!=4:v.fail('invalid_crop','Crop is normalized left/top/right/bottom.')
  for x in crop:v.number(x,0,1)
  if crop[2]-crop[0]<.001 or crop[3]-crop[1]<.001:v.fail('invalid_crop','Crop must retain a nonempty source rectangle.')
def evaluated_layout(clip,frame):
 layout=deepcopy(clip['layout']);local=frame-clip['start']+clip.get('visual_window',dict(offset=0))['offset']
 for channel in layout.pop('keys',[]):
  points=channel['points'];value=points[0][1]
  for i,point in enumerate(points):
   if local<point[0]:break
   value=point[1]
   if i+1<len(points) and local<points[i+1][0]:
    if point[2]=='Linear':value+=(points[i+1][1]-value)*float(Fraction(local-point[0],points[i+1][0]-point[0]))
    break
  write_parameter(layout,channel['parameter'],value)
 return layout

def text_layout(row):
 v=model();style=row['style'];return dict(v.layout_defaults(),bounds=deepcopy(style['bounds']),rotation=style.get('rotation',0.),opacity=style.get('opacity',1.),keys=deepcopy(style.get('keys',[])))

def validate_style(style):
 validate_layout(text_layout(dict(style=style)))
 for channel in style.get('keys',[]):
  if not isinstance(channel,dict) or channel.get('parameter') not in ('bounds.0','bounds.1','bounds.2','bounds.3','rotation','opacity'):model().fail('invalid_visual_parameter','Text supports transform and opacity keys; color effects apply to picture clips.')

def evaluated_text(row,frame):
 result=deepcopy(row);layout=evaluated_layout(dict(row,layout=text_layout(row)),frame);result['style'].pop('keys',None)
 # Leave unchanged legacy styles byte-for-byte compatible; optional evaluated
 # defaults become explicit only on an animated/new transform recipe.
 if row['style'].get('keys'):
  for field in ('bounds','rotation','opacity'):result['style'][field]=layout[field]
 return result
def transitions(document,frame):return [deepcopy(t) for t in document.get('transitions',[]) if t['start']<=frame<t['start']+t['duration']]
def validate_document(d):
 v=model();clips={c['id']:c for c in d['clips']};tracks={t['id']:t for t in d['tracks']};rows=d.get('transitions',[]);seen=set();participants=set();events=[]
 for c in d['clips']+d['captions']+d['graphics']:
  window=c.get('visual_window')
  if window is not None:v.fields(window,('offset','duration'));v.integer(window['offset'],-120*24*3600,120*24*3600);v.integer(window['duration'],1,120*24*3600)
  layout=c.get('layout',c.get('style',{}))
  if layout.get('keys') and window is None:v.fail('invalid_keyframe','Visual keys require an explicit preserved local origin.')
  if tracks[c['track']]['kind']=='audio' and any(layout.get(k) for k in ('keys','effects')):v.fail('invalid_effect','Visual effects/keys apply to picture clips, not audio-only clips.')
 if not isinstance(rows,list) or len(rows)>64:v.fail('transition_capacity','At most64 bounded two-source dissolves.')
 for t in rows:
  v.fields(t,('id','kind','track','left','right','start','duration','cut','audio'));v.identity(t['id'])
  if t['id'] in seen or t['id']==d['id'] or any(t['id']==r['id'] for category in ('media','tracks','clips','captions','graphics','buses') for r in d.get(category,[])):v.fail('duplicate_id','Transition IDs are unique.')
  seen.add(t['id']);v.integer(t['start']);v.integer(t['duration'],2,120*24*3600);v.integer(t['cut']);v.identity(t['track'])
  v.identity(t['left']);v.identity(t['right'])
  if t['kind']!='Dissolve' or t['left']==t['right'] or any(k not in clips for k in (t['left'],t['right'])):v.fail('invalid_transition','Dissolve needs two distinct existing picture clips.')
  left,right=clips[t['left']],clips[t['right']];start=t['start'];end=start+t['duration']
  if left['track']!=right['track'] or left['track']!=t['track'] or tracks[left['track']]['kind']!='video' or left['layout']['blend']!='Normal' or right['layout']['blend']!='Normal':v.fail('invalid_transition','Initial dissolve requires adjacent Normal-blend clips on one video track.')
  if not left['start']<=start<t['cut']<end<=right['start']+right['duration'] or left['start']+left['duration']!=end or right['start']!=start:v.fail('transition_handles','Dissolve handles changed. Remove the transition before trimming or replacing a participant.')
  if not isinstance(t['audio'],list) or len(t['audio']) not in (0,2):v.fail('invalid_transition','Dissolve audio companions are an explicit optional left/right pair.')
  for key in t['audio']:
   if key is not None:v.identity(key)
  pair=[t['left'],t['right']]+[k for k in t['audio'] if k is not None]
  if len(set(pair))!=len(pair):v.fail('invalid_transition','Dissolve participants must be distinct.')
  if any(k in participants for k in pair):v.fail('transition_overlap','A clip participates in at most one initial dissolve; split a longer clip deliberately.')
  participants.update(pair)
  for side,key in enumerate(t['audio']):
   if key is None:continue
   if key not in clips or tracks[clips[key]['track']]['kind']!='audio':v.fail('invalid_transition','A dissolve audio companion is unavailable.')
   row=clips[key]
   if side==0 and row['start']+row['duration']!=end or side==1 and row['start']!=start:v.fail('transition_handles','Audio companion handles changed; remove transition first.')
  events.extend([(start,1),(end,-1)])
 # Each dissolve introduces one isolated group in the existing32-layer adapter.
 visual=[r for r in d['clips'] if tracks[r['track']]['kind']!='audio']+d['captions']+d['graphics'];events.extend((at,delta) for row in visual for at,delta in [(row['start'],1),(row['start']+row['duration'],-1)])
 active=0
 for _,delta in sorted(events):
  active+=delta
  if active>v.LIMITS['active_visual']:v.fail('transition_capacity','Pictures, text and isolated dissolve groups exceed the existing32-layer compositor capacity.')
def clip_for(d,key):
 v=model();row=v._find(d,'clips',key)
 from project_edits import unlocked
 unlocked(d,[('clips',row)])
 if next(t['kind'] for t in d['tracks'] if t['id']==row['track'])=='audio':v.fail('invalid_effect','Choose a picture clip.')
 return row
def effect_for(clip,key):
 row=next((e for e in clip['layout'].get('effects',[]) if e['id']==key),None)
 if row is None:model().fail('missing_effect','Effect is no longer on the selected clip.')
 return row
def remove_transition(d,t):
 v=model();clips={c['id']:c for c in d['clips']}
 from project_edits import unlocked,piece
 ids=[t['left'],t['right']]+[k for k in t['audio'] if k is not None];unlocked(d,[('clips',clips[k]) for k in ids]);cut=t['cut']
 for i,key in enumerate([t['left'],t['right']]):
  row=clips[key];replacement=piece(d,row,row['start'] if i==0 else cut,cut if i==0 else row['start']+row['duration']);row.clear();row.update(replacement)
 for i,key in enumerate(t['audio']):
  if key is None:continue
  row=clips[key];replacement=piece(d,row,row['start'] if i==0 else cut,cut if i==0 else row['start']+row['duration']);row.clear();row.update(replacement)
 d['transitions'].remove(t)
def add_transition(d,left_id,right_id,duration,key):
 v=model();v.integer(duration,2,120*24*3600);left=clip_for(d,left_id);right=clip_for(d,right_id);cut=right['start']
 if left['start']+left['duration']!=cut or left['track']!=right['track']:v.fail('transition_handles','Choose adjacent outgoing/incoming clips on one video track.')
 before=duration//2;after=duration-before;start=cut-before
 if start<=left['start'] or cut+after>=right['start']+right['duration']:v.fail('transition_handles','Dissolve must fit inside both participant timeline ranges.')
 tracks={t['id']:t for t in d['tracks']};audio=[]
 for row in (left,right):
  matches=[c for c in d['clips'] if row.get('link_id') and c['id']!=row['id'] and c.get('link_id')==row['link_id'] and tracks[c['track']]['kind']=='audio']
  if len(matches)>1 or matches and (matches[0]['start'],matches[0]['duration'])!=(row['start'],row['duration']):v.fail('transition_handles','Linked audio requires one aligned companion per side.')
  audio.append(matches[0]['id'] if matches else None)
 from project_edits import unlocked
 companions=[v._find(d,'clips',k) for k in audio if k is not None];unlocked(d,[('clips',r) for r in companions])
 for i,row in enumerate((left,right)):
  rows=[row]+([v._find(d,'clips',audio[i])] if audio[i] else [])
  for member in rows:
   if i==0:member['duration']+=after
   else:
    member['start']-=before;member['duration']+=before;member['source_in']=v.pair(v.rational(member['source_in'])-v.frame_time(d,before)*v.rational(member['rate']));member['audio_window']['offset']-=before
    if 'visual_window' in member:member['visual_window']['offset']-=before
 t=dict(id=key,kind='Dissolve',track=left['track'],left=left_id,right=right_id,start=start,duration=duration,cut=cut,audio=audio if any(audio) else []);d.setdefault('transitions',[]).append(t)
 # Full document validation checks actual source handles, locks and native caps.
 return t
def apply_edit(d,change,operation,index):
 v=model();op=change['op'];created=[]
 if op=='transition.add':
  key=change.get('id') or uuid.uuid5(uuid.UUID(operation),'transition-'+str(index)).hex;add_transition(d,change['left'],change['right'],change['duration'],key);created.append(key);return created
 if op.startswith('transition.'):
  row=next((t for t in d.get('transitions',[]) if t['id']==change['id']),None)
  if row is None:v.fail('missing_transition','Transition is no longer present.')
  prior=deepcopy(row);remove_transition(d,row)
  if op=='transition.edit':add_transition(d,prior['left'],prior['right'],change['duration'],prior['id'])
  return created
 if op.startswith('keyframe.'):
  category,clip=next(((category,row) for category in ('clips','captions','graphics') for row in d[category] if row['id']==change['id']),(None,None))
  if clip is None:v.fail('missing_object','Animated item no longer exists.')
  from project_edits import unlocked
  unlocked(d,[(category,clip)])
  if category=='clips':clip=clip_for(d,change['id'])
  elif change['parameter'] not in ('bounds.0','bounds.1','bounds.2','bounds.3','rotation','opacity'):v.fail('invalid_visual_parameter','Text supports transform and opacity keys.')
  layout=clip['layout'] if category=='clips' else clip['style']
 else:clip=clip_for(d,change['id']);layout=clip['layout']
 if op=='effect.add':
  if change['kind'] not in EFFECTS:v.fail('invalid_effect','Choose supported Brightness or Contrast.')
  key=change.get('effect_id') or uuid.uuid5(uuid.UUID(operation),'effect-'+str(index)).hex;layout.setdefault('effects',[]).append(dict(id=key,kind=change['kind'],enabled=True,amount=change.get('amount',1.)));created.append(key)
 elif op.startswith('effect.'):
  effect=effect_for(clip,change['effect'])
  if op=='effect.edit':
   if not isinstance(change['values'],dict) or set(change['values'])-{'enabled','amount'}:v.fail('invalid_effect','Edit effect amount or boolean enabled state.')
   effect.update(deepcopy(change['values']))
  elif op=='effect.move':v.integer(change['index'],0,len(layout['effects'])-1);layout['effects'].remove(effect);layout['effects'].insert(change['index'],effect)
  else:
   layout['effects'].remove(effect);layout['keys']=[k for k in layout.get('keys',[]) if k['parameter']!='effect.'+effect['id']+'.amount']
 else:
  name=change['parameter'];low,high=parameter(layout,name);keys=layout.setdefault('keys',[]);channel=next((k for k in keys if k['parameter']==name),None)
  if op=='keyframe.remove':v.integer(change['frame'],0,120*24*3600)
  if op=='keyframe.set':
   frame=v.integer(change['frame'],0,120*24*3600);v.number(change['value'],low,high);interpolation=change.get('interpolation','Linear')
   if channel is None:channel=dict(parameter=name,points=[]);keys.append(channel)
   channel['points']=[p for p in channel['points'] if p[0]!=frame]+[[frame,change['value'],interpolation]];channel['points'].sort(key=lambda p:p[0]);clip.setdefault('visual_window',dict(offset=0,duration=clip['duration']))
  elif channel is not None:
   if op=='keyframe.clear':keys.remove(channel)
   else:
    v.integer(change['frame'],0,120*24*3600);channel['points']=[p for p in channel['points'] if p[0]!=change['frame']]
    if not channel['points']:keys.remove(channel)
 return created
def reconcile(before,after):
 """Moving both complete participants preserves an absolute transition recipe."""
 prior={c['id']:c for c in before['clips']};current={c['id']:c for c in after['clips']}
 for t in after.get('transitions',[]):
  ids=[t['left'],t['right']]+[i for i in t['audio'] if i is not None]
  if not all(i in prior and i in current for i in ids):continue
  deltas={current[i]['start']-prior[i]['start'] for i in ids}
  if len(deltas)==1 and all(current[i]['duration']==prior[i]['duration'] for i in ids):
   delta=deltas.pop();t['start']+=delta;t['cut']+=delta
