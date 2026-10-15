"""Versioned video document and pure validated edits; one Studio owner mutates it.

Project frames are integers, source seconds/rates are rationals. Native media,
audio and GL resource ownership stays outside these authoring recipes.
"""
from copy import deepcopy
from fractions import Fraction
import json,math,re,uuid
from pathlib import PureWindowsPath

FORMAT='zerawave-video-project'
VERSION=1
MAX_DOCUMENT_BYTES=524288
LIMITS=dict(media=1024,tracks=64,clips=2048,captions=4096,graphics=512,batch=128,active_video=4,active_visual=32,active_audio=16)
OP_FIELDS={
 'project.rename':(('name',),()),'project.settings':(('values',),()),'project.provenance':(('values',),()),'project.protect':(('paths',),()),
 'media.add':(('name','kind','location','sha256'),('id','metadata','provenance','placeholder','accept_changed')),
 'media.relink':(('id','kind','location','sha256','metadata'),('provenance','accept_changed','placeholder')),
 'track.add':(('kind',),('id','name','order','audio')),'track.audio':(('id','values'),()),
 'clip.add':(('asset','track','start','duration'),('id','name','source_in','rate','audio','layout','link_id','pad_end','provenance')),
 'clip.move':(('id','start'),('track','linked')),'clip.trim':(('id',),('start','end','linked')),
 'clip.remove':(('id',),('linked',)),'clip.unlink':(('id',),('linked',)),'clip.split':(('id','at'),('linked',)),
 'clip.audio':(('id','values'),()),'clip.layout':(('id','values'),()),
 'caption.add':(('track','start','duration','text'),('id','style','order','dynamic','provenance','range_start','range_end')),
 'graphic.add':(('track','start','duration','text'),('id','style','order','dynamic','provenance','range_start','range_end')),
 'caption.edit':(('id','values'),()),'graphic.edit':(('id','values'),()),'caption.remove':(('id',),()),'graphic.remove':(('id',),()),'export.settings':(('values',),())}
class ProjectError(ValueError):
 def __init__(self,code,message):super().__init__(message);self.code=code
def fail(code,message):raise ProjectError(code,message)

def fields(value,required,optional=()):
 if not isinstance(value,dict) or set(value)-set(required)-set(optional) or set(required)-set(value):fail('unsupported_fields','Unknown or missing recipe fields; nothing was discarded.')
def identity(value):
 if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{32}',value):fail('invalid_id','A stable 32-character hexadecimal ID is required.')
 return value
def new_id():return uuid.uuid4().hex
def integer(v,low=0,high=2**53):
 if type(v) is not int or not low<=v<=high:fail('invalid_time','Expected an integer within the supported range.')
 return v
def number(v,low=0.,high=4.):
 if type(v) not in (int,float) or not low<=v<=high or not math.isfinite(v):fail('invalid_value','Expected a finite value within the supported range.')
 return v
def text(v,limit=4096):
 if not isinstance(v,str) or len(v)>limit or '\0' in v:fail('invalid_text','Text is missing, oversized or contains a null character.')
 return v
def rational(v):
 if not isinstance(v,list) or len(v)!=2:fail('invalid_time','Rational values require [numerator, denominator].')
 integer(v[0],-2**53,2**53);integer(v[1],1,10**9);return Fraction(*v)
def pair(v):v=Fraction(v);return [v.numerator,v.denominator]
def frame_time(document,frame):return Fraction(frame)/rational(document['settings']['fps'])
def sample_at(document,frame):
 # Nearest sample with halves upward, evaluated from absolute time each time.
 value=frame_time(document,frame)*document['settings']['sample_rate'];return (value.numerator*2+value.denominator)//(value.denominator*2)
def duration(document):return max([0]+[c['start']+c['duration'] for category in ('clips','captions','graphics') for c in document[category]])
def create(name='Untitled video',settings=None,project_id=None):
 d=dict(format=FORMAT,version=VERSION,id=project_id or new_id(),name=name,settings=dict(width=1280,height=720,fps=[30,1],sample_rate=48000,background='#000000'),media=[],tracks=[],clips=[],captions=[],graphics=[],provenance={},protected_paths=[],export=dict(container='mp4',video_codec='h264',audio_codec='aac',crf=18))
 d['settings'].update(settings or {});return validate(d)
def envelope(value):
 if not isinstance(value,list) or len(value)>2048:fail('invalid_envelope','At most 2048 envelope points are supported.')
 prior=-1
 for point in value:
  if not isinstance(point,list) or len(point)!=2:fail('invalid_envelope','Envelope points are [local frame, linear gain].')
  integer(point[0]);number(point[1],0,4)
  if point[0]<=prior:fail('invalid_envelope','Envelope frame positions must increase strictly.')
  prior=point[0]
def audio(value):
 fields(value,('gain','fade_in','fade_out','envelope','mute'))
 if not isinstance(value,dict):fail('invalid_audio','Missing audio controls.')
 number(value['gain']);integer(value['fade_in']);integer(value['fade_out']);envelope(value['envelope'])
 if type(value['mute']) is not bool:fail('invalid_audio','Mute must be true or false.')
def audio_defaults():return dict(gain=1.,mute=False,fade_in=0,fade_out=0,envelope=[])
def style_defaults():return dict(font='Segoe UI',size=27,color='#fff7e7',background='#e017120e',bold=True,align='center',bounds=[.027,.82,.946,.16],padding=10)
def layout_defaults():return dict(bounds=[0.,0.,1.,1.],opacity=1.,rotation=0.,brightness=1.,fit='Stretch',masks=[],blend='Normal')
def timed(row):integer(row['start'],0,120*24*3600);integer(row['duration'],1,120*24*3600)
def style(value):
 fields(value,('font','size','color','background','bold','align','bounds','padding'),('radius','stroke_width','stroke_color','opacity','max_lines','valign','padding_x','padding_y','line_spacing'))
 text(value['font'],128);number(value['size'],6,256);text(value['color'],32);text(value['background'],32)
 if not re.fullmatch('#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})',value['color']) or not re.fullmatch('#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})',value['background']):fail('invalid_style','Use Qt hexadecimal RGB (#RRGGBB) or ARGB (#AARRGGBB) colors.')
 if value['align'] not in ('left','center','right') or type(value['bold']) is not bool:fail('invalid_style','Unsupported text alignment/weight.')
 bounds(value['bounds']);number(value['padding'],0,256)
 for name,low,high in [('radius',0,256),('stroke_width',0,16),('opacity',0,1),('padding_x',0,256),('padding_y',0,256),('line_spacing',0,512)]:
  if name in value:number(value[name],low,high)
 if 'max_lines' in value:integer(value['max_lines'],0,128)
 if value.get('valign','center') not in ('top','center','bottom'):fail('invalid_style','Unsupported vertical text alignment.')
 if 'stroke_color' in value and not re.fullmatch('#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{8})',value['stroke_color']):fail('invalid_style','Stroke color requires Qt RGB or ARGB hexadecimal.')
def bounds(value):
 if not isinstance(value,list) or len(value)!=4:fail('invalid_layout','Bounds must contain x, y, width and height.')
 for v in value[:2]:number(v,-4,4)
 for v in value[2:]:number(v,.00001,8)
def layout(value):
 fields(value,('bounds','opacity','rotation','brightness','fit','masks','blend'))
 bounds(value['bounds']);number(value['opacity'],0,1);number(value['rotation'],-36000,36000);number(value['brightness'],0,4)
 if value['fit'] not in ('Stretch','Fit','Fill') or value['blend'] not in ('Normal','Multiply','Screen','Add','Difference'):fail('invalid_layout','Unsupported fit or blend mode.')
 if not isinstance(value['masks'],list) or len(value['masks'])>8:fail('invalid_layout','At most 8 masks are supported by the existing composition renderer.')
 for mask in value['masks']:
  fields(mask,('mode','enabled','points'))
  if mask.get('mode') not in ('Keep','Remove') or type(mask.get('enabled')) is not bool or not isinstance(mask.get('points'),list) or not 3<=len(mask['points'])<=128:fail('invalid_layout','Invalid mask.')
  for point in mask['points']:
   if not isinstance(point,list) or len(point)!=2:fail('invalid_layout','Invalid mask point.')
   for v in point:number(v,0,1)
 # Validate masks against the actual existing composition contract at admission.
 from composition import defaults,new_layer,validate_scene
 scene=defaults();row=new_layer('Group');row['masks']=[dict(m,mode='Cut' if m['mode']=='Remove' else 'Keep') for m in value['masks']];scene['layers']=[row]
 try:validate_scene(scene)
 except ValueError as exc:fail('invalid_layout',str(exc))
def _peak(rows):
 events=[]
 for row in rows:events.extend([(row['start'],1),(row['start']+row['duration'],-1)])
 active=peak=0
 for at,delta in sorted(events):active+=delta;peak=max(peak,active)
 return peak
def validate(value):
 d=deepcopy(value)
 if not isinstance(d,dict) or d.get('format')!=FORMAT or d.get('version')!=VERSION:fail('unsupported_project','Not a supported ZeraWave video project. Legacy layer sessions use Open session.')
 required={'format','version','id','name','settings','media','tracks','clips','captions','graphics','provenance','protected_paths','export'}
 if set(d)!=required:fail('unsupported_fields','Unknown or missing video-project fields; nothing was discarded.')
 identity(d['id']);text(d['name'],256);s=d['settings'];fields(s,('width','height','fps','sample_rate','background'));integer(s['width'],16,8192);integer(s['height'],16,8192)
 if s['width']*s['height']>8388608 or not Fraction(1)<=rational(s['fps'])<=120 or s['sample_rate']!=48000:fail('invalid_settings','Use up to 8 megapixels, 1–120 FPS and 48 kHz audio.')
 text(s['background'],32)
 if not re.fullmatch('#[0-9a-fA-F]{6}',s['background']):fail('invalid_settings','Background must be a hexadecimal RGB color.')
 seen={d['id']};assets={};tracks={}
 for category in ('media','tracks','clips','captions','graphics'):
  rows=d[category]
  if not isinstance(rows,list) or len(rows)>LIMITS[category]:fail('capacity','Video-project '+category+' metadata limit reached; existing work retained.')
  for row in rows:
   key=identity(row['id'])
   if key in seen:fail('duplicate_id','Project object IDs must be unique.')
   seen.add(key)
 for asset in d['media']:
  fields(asset,('id','name','kind','location','sha256','metadata','provenance'));fields(asset['location'],('kind','path'))
  if not isinstance(asset['provenance'],dict):fail('invalid_document','Media provenance must be structured metadata.')
  text(asset['name'],256)
  if asset['kind'] not in ('Video','Audio','Image'):fail('unsupported_media','Use existing video, audio or image sources.')
  loc=asset['location'];text(loc['path'],4096)
  if loc['kind'] not in ('relative','external'):fail('invalid_path','Source must be project-relative or explicitly external.')
  path=PureWindowsPath(loc['path'])
  if loc['kind']=='relative' and (path.is_absolute() or path.drive or '..' in path.parts) or loc['kind']=='external' and not path.is_absolute():fail('invalid_path','Relative paths must stay in the project; external paths must be explicit absolute paths.')
  if not re.fullmatch('[0-9a-f]{64}',asset['sha256']) or not isinstance(asset['metadata'],dict):fail('invalid_media','Source identity/metadata is missing.')
  assets[asset['id']]=asset
 for track in d['tracks']:
  fields(track,('id','name','kind','order','audio'))
  text(track['name'],256);audio(track['audio']);integer(track['order'],0,63)
  if track['kind'] not in ('video','audio','graphics'):fail('invalid_track','Unsupported track type.')
  tracks[track['id']]=track
 if len({r['order'] for r in d['tracks']})!=len(tracks):fail('invalid_track','Track order must be unique.')
 for row in d['clips']:
  fields(row,('id','name','asset','track','start','duration','source_in','rate','audio','layout','link_id','audio_window','pad_end','provenance'));fields(row['audio_window'],('offset','duration'))
  if not isinstance(row['provenance'],dict):fail('invalid_document','Clip provenance must be structured metadata.')
  timed(row);text(row['name'],256);audio(row['audio']);layout(row['layout']);source=rational(row['source_in']);rate=rational(row['rate'])
  if source<0 or not Fraction(1,16)<=rate<=16:fail('invalid_time','Nonnegative source time and rate 1/16–16 are required.')
  if row.get('link_id') is not None:identity(row['link_id'])
  if row['asset'] not in assets or row['track'] not in tracks:fail('missing_reference','Clip source or track does not exist.')
  kind=assets[row['asset']]['kind'];tk=tracks[row['track']]['kind']
  if tk=='graphics' and kind!='Image' or tk=='video' and kind=='Audio' or tk=='audio' and kind=='Image':fail('invalid_track','Source is incompatible with this track.')
  window=row['audio_window'];integer(window['offset'],-30*24*3600);integer(window['duration'],1)
  if row['pad_end'] not in ('none','silence') or row['pad_end']=='silence' and tk!='audio':fail('invalid_time','Only an audio clip may explicitly pad its natural end with silence.')
  available=assets[row['asset']]['metadata'].get('duration')
  if available is not None:
   number(available,.0000001,24*3600)
   if kind!='Image' and row['pad_end']=='none' and source+frame_time(d,row['duration'])*rate>Fraction(str(available))+Fraction(1,48000):fail('source_range','Clip extends beyond the recorded source duration; audio silence padding must be explicit.')
 for category in ('captions','graphics'):
  for row in d[category]:
   fields(row,('id','track','start','duration','text','style','order','dynamic','provenance'),('range_start','range_end'))
   if not isinstance(row['provenance'],dict):fail('invalid_document','Text provenance must be structured metadata.')
   timed(row);text(row['text']);style(row['style']);integer(row['order'],0,65535)
   if row['track'] not in tracks or tracks[row['track']]['kind']!='graphics':fail('invalid_track','Text requires a graphics track.')
   if row.get('dynamic') not in (None,'counter','progress'):fail('invalid_graphic','Unsupported timed graphic.')
   if row.get('dynamic')=='counter' and any(token not in ('elapsed','duration','frame') for token in re.findall(r'\{([^{}]+)\}',row['text'])):fail('invalid_graphic','Counter supports {elapsed}, {duration} and {frame} only.')
   if row.get('dynamic') in ('counter','progress'):
    begin=integer(row.get('range_start',row['start']));integer(row.get('range_end',row['start']+row['duration']),begin+1)
 if not isinstance(d['protected_paths'],list) or len(d['protected_paths'])>4096 or not isinstance(d['provenance'],dict):fail('invalid_document','Protected paths and provenance must be explicit structured data.')
 for row in d['protected_paths']:
  text(row,4096)
  if not PureWindowsPath(row).is_absolute():fail('invalid_path','Protected source/output paths must be explicit absolute paths.')
 fields(d['export'],('container','video_codec','audio_codec','crf'))
 if d['export'].get('container')!='mp4' or d['export'].get('video_codec')!='h264' or d['export'].get('audio_codec')!='aac':fail('unsupported_export','Initial project export is MP4/H.264/AAC.')
 integer(d['export']['crf'],0,51)
 if frame_time(d,duration(d))>24*3600:fail('capacity','Project duration exceeds the supported 24 hours.')
 visuals=[r for r in d['clips'] if tracks[r['track']]['kind']!='audio'];videos=[r for r in visuals if assets[r['asset']]['kind']=='Video']
 if _peak(videos)>LIMITS['active_video'] or _peak(visuals+d['captions']+d['graphics'])>LIMITS['active_visual']:fail('active_capacity','Timeline overlap exceeds 4 video instances or 32 active visual recipes; clip/bin counts are separate.')
 if _peak([r for r in d['clips'] if tracks[r['track']]['kind']=='audio'])>LIMITS['active_audio']:fail('active_capacity','Timeline overlap exceeds 16 active audio recipes.')
 try:size=len(json.dumps(d,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf8'))
 except (ValueError,TypeError):fail('invalid_document','Project contains unsupported or nonfinite metadata.')
 if size>MAX_DOCUMENT_BYTES:fail('capacity','Project metadata exceeds 512 KiB; existing document retained.')
 return d
def _find(d,category,key):
 row=next((r for r in d[category] if r['id']==key),None)
 if row is None:fail('missing_object','The requested '+category+' object is unavailable.')
 return row
def _linked(d,row,enabled):return [r for r in d['clips'] if enabled and row.get('link_id') and r.get('link_id')==row['link_id'] or r['id']==row['id']]
def apply(document,changes,operation_id):
 if not isinstance(changes,list) or not 1<=len(changes)<=LIMITS['batch']:fail('invalid_batch','A batch requires 1–128 explicit changes.')
 d=deepcopy(document);created=[]
 for i,change in enumerate(changes):
  if not isinstance(change,dict) or not isinstance(change.get('op'),str) or change['op'] not in OP_FIELDS:fail('unsupported_command','Unsupported project edit.')
  required,optional=OP_FIELDS[change['op']];fields(change,('op',)+required,optional)
  for flag in ('linked','accept_changed','placeholder'):
   if flag in change and type(change[flag]) is not bool:fail('invalid_value',flag+' must be true or false.')
  op=change['op'];args={k:v for k,v in change.items() if k!='op'};key=args.get('id') or uuid.uuid5(uuid.UUID(operation_id),str(i)).hex
  if op=='project.rename':d['name']=args['name']
  elif op=='project.provenance':
   if not isinstance(args['values'],dict):fail('invalid_document','Project provenance must be structured metadata.')
   d['provenance'].update(deepcopy(args['values']))
  elif op=='project.protect':
   if not isinstance(args['paths'],list):fail('invalid_path','Protected source/output paths require an explicit list.')
   for path in args['paths']:
    if path not in d['protected_paths']:d['protected_paths'].append(path)
  elif op=='project.settings':d['settings'].update(args['values'])
  elif op=='media.add':
   row=dict(id=key,name=args['name'],kind=args['kind'],location=deepcopy(args['location']),sha256=args['sha256'],metadata=deepcopy(args.get('metadata',{})),provenance=deepcopy(args.get('provenance',{})));d['media'].append(row);created.append(key)
  elif op=='media.relink':
   row=_find(d,'media',args['id'])
   if args['sha256']!=row['sha256'] and not args.get('accept_changed',False):fail('changed_media','Replacement differs from recorded source; explicitly accept the change.')
   prior=row['provenance'].get('import_path')
   if prior and prior not in d['protected_paths']:d['protected_paths'].append(prior)
   row.update(location=deepcopy(args['location']),sha256=args['sha256'],metadata=deepcopy(args['metadata']))
   row['provenance'].update(deepcopy(args.get('provenance',{})))
  elif op=='track.add':
   d['tracks'].append(dict(id=key,name=args.get('name','Track'),kind=args['kind'],order=args.get('order',len(d['tracks'])),audio=dict(audio_defaults(),**args.get('audio',{}))));created.append(key)
  elif op=='track.audio':_find(d,'tracks',args['id'])['audio'].update(args['values'])
  elif op=='clip.add':
   row=dict(id=key,name=args.get('name','Clip'),asset=args['asset'],track=args['track'],start=args['start'],duration=args['duration'],source_in=args.get('source_in',[0,1]),rate=args.get('rate',[1,1]),audio=dict(audio_defaults(),**args.get('audio',{})),layout=dict(layout_defaults(),**args.get('layout',{})),link_id=args.get('link_id'),audio_window=dict(offset=0,duration=args['duration']),pad_end=args.get('pad_end','none'),provenance=deepcopy(args.get('provenance',{})));d['clips'].append(row);created.append(key)
  elif op in ('clip.move','clip.trim','clip.remove','clip.unlink','clip.split'):
   row=_find(d,'clips',args['id']);members=_linked(d,row,args.get('linked',True))
   if op=='clip.move':
    delta=args['start']-row['start']
    for member in members:member['start']+=delta
    if 'track' in args:row['track']=args['track']
   elif op=='clip.trim':
    start=args.get('start',row['start']);end=args.get('end',row['start']+row['duration']);left=start-row['start'];right=end-(row['start']+row['duration'])
    for member in members:member.update(start=member['start']+left,duration=member['duration']+right-left,source_in=pair(rational(member['source_in'])+frame_time(d,left)*rational(member['rate'])));member['audio_window']['offset']+=left
   elif op=='clip.remove':d['clips']=[c for c in d['clips'] if c not in members]
   elif op=='clip.unlink':
    for member in members:member['link_id']=None
   else:
    at=integer(args['at']);group=uuid.uuid5(uuid.UUID(operation_id),'right-link-'+str(i)).hex if row.get('link_id') else None
    for member in members:
     offset=at-member['start']
     if not 0<offset<member['duration']:fail('invalid_split','Split must be inside every linked clip.')
     right=deepcopy(member);right.update(id=uuid.uuid5(uuid.UUID(operation_id),member['id']+'-right').hex,start=at,duration=member['duration']-offset,source_in=pair(rational(member['source_in'])+frame_time(d,offset)*rational(member['rate'])),link_id=group);right['audio_window']['offset']+=offset;member['duration']=offset;d['clips'].append(right);created.append(right['id'])
  elif op in ('clip.audio','clip.layout'):
   row=_find(d,'clips',args['id']);row['audio' if op.endswith('audio') else 'layout'].update(args['values'])
   if op=='clip.audio' and set(args['values'])&{'fade_in','fade_out','envelope'}:row['audio_window']=dict(offset=0,duration=row['duration'])
  elif op in ('caption.add','graphic.add'):
   category='captions' if op=='caption.add' else 'graphics';row=dict(id=key,track=args['track'],start=args['start'],duration=args['duration'],text=args['text'],style=dict(style_defaults(),**args.get('style',{})),order=args.get('order',len(d[category])),dynamic=args.get('dynamic'),provenance=deepcopy(args.get('provenance',{})))
   if row['dynamic']:row.update(range_start=args.get('range_start',row['start']),range_end=args.get('range_end',row['start']+row['duration']))
   d[category].append(row);created.append(key)
  elif op in ('caption.edit','graphic.edit'):
   if set(args['values'])-{'start','duration','text','style','order','dynamic','range_start','range_end'}:fail('immutable_id','Text edits cannot replace stable IDs, tracks or provenance.')
   row=_find(d,'captions' if op.startswith('caption') else 'graphics',args['id'])
   for k,v in args['values'].items():
    if k=='style':row['style'].update(deepcopy(v))
    else:row[k]=deepcopy(v)
  elif op in ('caption.remove','graphic.remove'):
   category='captions' if op.startswith('caption') else 'graphics';_find(d,category,args['id']);d[category]=[r for r in d[category] if r['id']!=args['id']]
  elif op=='export.settings':d['export'].update(args['values'])
  else:fail('unsupported_command','Unsupported project edit: '+str(op))
 return validate(d),created
