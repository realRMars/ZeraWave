"""Version1 editable manifest planner on the existing authenticated owner API.

No server, editable mirror, renderer, pool or file authoring behind a live owner.
Planning simulates existing validated commands; only the owner accepts them.
"""
from pathlib import Path
from copy import deepcopy
from contextlib import contextmanager
import hashlib,json,os,re,threading,time,uuid
from video_project import apply,fields,identity,text,LIMITS,MAX_DOCUMENT_BYTES
from project_api import call,MAX_BYTES

FORMAT='zerawave-edit-manifest'
PLAN='zerawave-manifest-plan'
JOURNAL='zerawave-manifest-journal'
JOURNAL_BYTES=8*1024*1024
CATEGORIES={'tracks':'track','buses':'bus','clips':'clip','captions':'caption','graphics':'graphic'}
SETTERS={'clip.audio':'clips','clip.layout':'clips','clip.move':'clips','caption.edit':'captions','graphic.edit':'graphics','track.audio':'tracks','track.edit':'tracks','track.move':'tracks','track.output':'tracks','bus.edit':'buses'}
TERMINAL={'accepted','durable','exported','failed','rejected'}

class Conflict(ValueError):pass
class Uncertain(Conflict):pass
def encoded(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf8')
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def file_hash(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def logical(value):
 if not isinstance(value,str) or not re.fullmatch('[A-Za-z0-9_.-]{1,128}',value):raise ValueError('Logical keys use1–128 ASCII letters,digits,period,underscore or hyphen.')
 return value
def stable(namespace,category,key):return uuid.uuid5(uuid.UUID(identity(namespace)),category+':'+logical(key)).hex
def binding(state):return dict(expected_epoch=state['epoch'],expected_project=state['project_id'],expected_revision=state['revision'],expected_command=state['command_revision'])
def stamp(state):return dict(binding= binding(state),document_sha256=digest(state['document']))
def endpoint_identity(endpoint):
 row=json.loads(Path(endpoint).read_text(encoding='utf8'))
 if row.get('protocol')!=1 or row.get('host')!='127.0.0.1' or not isinstance(row.get('token'),str):raise ValueError('Choose one explicit existing authenticated local endpoint.')
 return {k:row[k] for k in ('protocol','host','port','owner_pid')}
def wire_bytes(endpoint,request):
 # Exactly project_api.call's envelope, UTF8 serialization and server newline.
 row=json.loads(Path(endpoint).read_text(encoding='utf8'));return len(json.dumps(dict(token=row['token'],request=request),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf8'))+1
def read_state(endpoint):
 result=call(endpoint,dict(op='state'))
 if not result.get('ok'):raise Conflict(str(result.get('error','Owner state unavailable.')))
 return result['state']
def source_stamp(path):
 s=Path(path).stat();return [s.st_size,s.st_mtime_ns]
def verify_sources(sources):
 # Planning already hashes every source. Recheck identity signals before each
 # deliberate send; a changed signal requires a fresh full hash, not silent
 # acceptance of a new file. Owner media preparation and Save hash independently.
 for row in sources:
  before=source_stamp(row['path'])
  if before!=row['stat']:
   if file_hash(row['path'])!=row['sha256'] or source_stamp(row['path'])!=before:raise Conflict('Source changed after planning: '+row['key']+'. Prior accepted work retained.')
def resolve(value,ids):
 if isinstance(value,dict):
  if set(value)=={'ref'}:
   if value['ref'] not in ids:raise ValueError('Unknown logical reference '+str(value['ref']))
   return ids[value['ref']]
  return {k:resolve(v,ids) for k,v in value.items()}
 if isinstance(value,list):return [resolve(v,ids) for v in value]
 return deepcopy(value)
def check_manifest(value,*,allow_recipes=False):
 if len(encoded(value))>MAX_DOCUMENT_BYTES:raise ValueError('Manifest exceeds the existing512KiB metadata bound.')
 fields(value,('format','version','id','project_id','media','sections','save'),('settings',))
 if value['format']!=FORMAT or type(value['version']) is not int or value['version']!=1:raise ValueError('Unsupported manifest format/version.')
 identity(value['id']);identity(value['project_id'])
 if not isinstance(value['media'],list) or not isinstance(value['sections'],list):raise ValueError('Media and sections must be lists.')
 seen=set()
 for a in value['media']:
  fields(a,('key','name','kind','path','sha256'),('provenance',));logical(a['key']);text(a['name'],256)
  if a['key'] in seen:raise ValueError('Duplicate logical media key.')
  seen.add(a['key']);text(a['path'],1024)
  if not Path(a['path']).is_absolute() or a['kind'] not in ('Video','Audio','Image') or not re.fullmatch('[0-9a-f]{64}',a['sha256']):raise ValueError('Media requires absolute path, supported kind and expected SHA256.')
  if not isinstance(a.get('provenance',{}),dict):raise ValueError('Provenance must be an object.')
 seen=set();items=set()
 for section in value['sections']:
  fields(section,('key','label','items'),('edits','recipes'));logical(section['key']);text(section['label'],220)
  if not section['label'] or section['key'] in seen:raise ValueError('Sections need unique keys and nonempty labels.')
  seen.add(section['key'])
  if not isinstance(section['items'],list) or not isinstance(section.get('edits',[]),list):raise ValueError('Section items/edits must be lists.')
  if not isinstance(section.get('recipes',[]),list):raise ValueError('Recipes must be a list of explicit versioned instances.')
  if section.get('recipes') and not allow_recipes:raise ValueError('Recipes must be expanded before ordinary command validation.')
  for item in section['items']:
   fields(item,('category','key','values'));category=item['category'];logical(item['key'])
   if category not in CATEGORIES or not isinstance(item['values'],dict) or 'id' in item['values']:raise ValueError('Items require supported category and ordinary add values; stable ID comes from key.')
   token=category+':'+item['key']
   if token in items:raise ValueError('Repeated logical entity '+token)
   items.add(token)
 fields(value['save'],('path',),('portable',));text(value['save']['path'],1024)
 if not Path(value['save']['path']).is_absolute() or Path(value['save']['path']).suffix.lower()!='.zwv' or type(value['save'].get('portable',True)) is not bool:raise ValueError('Save needs an absolute .zwv path and boolean portable option.')
 return deepcopy(value)

def compile_plan(endpoint,manifest,*,state=None):
 """Read-only source validation and local command simulation; never accepts edits."""
 from project_service import prepare_changes
 from project_import import normalized
 from project_recipes import expand
 original=check_manifest(manifest,allow_recipes=True);manifest,recipes=expand(original);manifest=check_manifest(manifest);owner=endpoint_identity(endpoint);state=read_state(endpoint) if state is None else deepcopy(state);doc=deepcopy(state['document'])
 if doc is None or state['project_id']!=manifest['project_id']:raise Conflict('Open/create the intended project first; manifest does not select another instance.')
 if 'settings' in manifest and manifest['settings']!=doc['settings']:raise Conflict('Project settings differ from the explicit manifest; inspect and plan a deliberate change separately.')
 ids={};sources=[];groups=[];summary=[];operation=uuid.uuid4().hex;media_by_id={a['id']:a for a in doc['media']};path_seen={}
 for section in manifest['sections']:
  for item in section['items']:ids[item['category']+':'+item['key']]=stable(manifest['id'],item['category'],item['key'])
 for a in manifest['media']:
  path=str(Path(a['path']).resolve());normal=normalized(path);candidate=prepare_changes([dict(op='media.add',id=stable(manifest['id'],'media',a['key']),name=a['name'],kind=a['kind'],location=dict(kind='external',path=path),sha256=a['sha256'],provenance=deepcopy(a.get('provenance',{})))],None,threading.Event())[0]
  existing=media_by_id.get(candidate['id']) or next((old for old in doc['media'] if normal in {normalized(p) for p in (old['location']['path'],old['provenance'].get('import_path'),old['provenance'].get('original_path')) if p}),None)
  if existing:
   if existing['sha256']!=a['sha256'] or existing['kind']!=a['kind'] or state['media'].get(existing['id'],{}).get('status')!='Ready':raise Conflict('Recorded media identity is changed/unavailable: '+a['key'])
   if any(existing['provenance'].get(k)!=v for k,v in a.get('provenance',{}).items()):raise Conflict('Recorded provenance differs: '+a['key'])
   key=existing['id'];action='reuse'
  elif normal in path_seen:
   prior=path_seen[normal]
   if prior['sha256']!=a['sha256'] or prior['kind']!=a['kind'] or prior['provenance']!=candidate['provenance']:raise Conflict('Conflicting logical aliases for one source.')
   key=prior['id'];action='reuse logical alias'
  else:
   doc=apply(doc,[candidate],operation)[0];key=candidate['id'];groups.append(dict(section='@media',label='Manifest: media references',changes=[candidate]));action='create'
  stat=source_stamp(path)
  if stat!=[candidate['metadata'].get('bytes'),candidate['metadata'].get('mtime_ns')]:raise Conflict('Source changed during planning inspection: '+a['key'])
  ids['media:'+a['key']]=key;path_seen[normal]=dict(candidate,id=key);sources.append(dict(key=a['key'],id=key,path=path,sha256=a['sha256'],kind=a['kind'],stat=stat,action=action,provenance=deepcopy(existing['provenance'] if existing else candidate['provenance'])))
 for section in manifest['sections']:
  for item in section['items']:
   category=item['category'];key=ids[category+':'+item['key']];values=resolve(item['values'],ids);extra=[]
   if category=='tracks':
    if 'order' not in values:raise ValueError('Manifest tracks require explicit stable order.')
    if 'output' in values:extra=[dict(op='track.output',id=key,output=values.pop('output'))]
   if category=='clips':
    if values.get('duration')=='natural':
     from project_audio_timing import natural_frames
     asset=next(a for a in doc['media'] if a['id']==values['asset'])
     if asset['kind']!='Audio':raise ValueError('Natural sample coverage is audio-only; give explicit video/still frames.')
     values['duration']=natural_frames(asset['metadata'],doc['settings']['fps'],start=values['start'],source_in=values.get('source_in',[0,1]),rate=values.get('rate',[1,1]));values.setdefault('pad_end','silence')
   if category in ('captions','graphics'):values.setdefault('order',0)
   if category in ('captions','graphics'):
    # Text add uses the existing model; animation keys are ordinary subsequent
    # keyframe.set commands in the SAME atomic entity unit. Do not invent a
    # private text origin or silently discard a trimmed/shifted one.
    from video_project import style,style_defaults
    style(dict(style_defaults(),**values.get('style',{})),extended=True)
    channels=values.get('style',{}).pop('keys',[]);window=values.pop('visual_window',None)
    if window is not None and (not channels or window!=dict(offset=0,duration=values['duration'])):raise Conflict('Text recipe has a modified visual origin; preserve it and plan deliberate ordinary edits.')
    for channel in channels:
     fields(channel,('parameter','points'))
     for point in channel['points']:
      if not isinstance(point,list) or len(point)!=3:raise ValueError('Text keys are [integer local frame,value,Linear/Hold].')
      extra.append(dict(op='keyframe.set',id=key,parameter=channel['parameter'],frame=point[0],value=point[1],interpolation=point[2]))
   change=dict(op=CATEGORIES[category]+'.add',id=key,**values);changes=[change]+extra;existing=next((r for r in doc[category] if r['id']==key),None)
   scratch=deepcopy(doc)
   if existing:scratch[category]=[r for r in scratch[category] if r['id']!=key]
   desired=apply(scratch,changes,operation)[0];row=next(r for r in desired[category] if r['id']==key)
   if existing:
    if existing!=row:raise Conflict('Manual/manifest content conflict at '+category+':'+item['key']+'; accepted object retained. Use an explicit guarded setter/new plan.')
    action='already applied'
   else:doc=desired;groups.append(dict(section=section['key'],label=section['label'],changes=changes));action='create'
   summary.append(dict(section=section['key'],category=category,key=item['key'],id=key,action=action,content_sha256=digest(row)))
  for edit in section.get('edits',[]):
   fields(edit,('change','expect'));change=resolve(edit['change'],ids);category=SETTERS.get(change.get('op'))
   if category is None:raise ValueError('Manifest edits are explicit idempotent entity setters; unsupported command '+str(change.get('op')))
   if change['op']=='clip.move' and change.get('linked',True):raise ValueError('Manifest move setters require linked=false; guard each intended companion explicitly.')
   row=next((r for r in doc[category] if r['id']==change.get('id')),None)
   if row is None:raise Conflict('Guarded edit target is missing.')
   new=apply(doc,[change],operation)[0]
   if new==doc:action='already applied setter'
   else:
    if edit['expect']!=digest(row):raise Conflict('Guarded edit precondition differs; manual values retained.')
    doc=new;groups.append(dict(section=section['key'],label=section['label'],changes=[change]));action='edit'
   summary.append(dict(section=section['key'],category=category,id=row['id'],action=action))
 # Chunk only at complete entity/setter boundaries. Every intermediate candidate
 # is validated by the same model. No cross-batch atomicity is promised.
 predicted=deepcopy(state);batches=[];index=0
 while index<len(groups):
  first=groups[index];changes=[];section=first['section'];label=first['label'];key=uuid.uuid4().hex
  while index<len(groups) and groups[index]['section']==section:
   candidate=changes+groups[index]['changes'];request=dict(op='batch',operation_id=key,**binding(predicted),label=label+' [part9999/9999]',changes=candidate)
   if len(candidate)>LIMITS['batch'] or wire_bytes(endpoint,request)>MAX_BYTES:
    if not changes:raise ValueError('One safe manifest unit exceeds existing request/change limits.')
    break
   changes=candidate;index+=1
  new=apply(predicted['document'],changes,key)[0];request=dict(op='batch',operation_id=key,**binding(predicted),label=label,changes=changes);before=stamp(predicted);predicted['revision']+=new!=predicted['document'];predicted['command_revision']+=1;predicted['document']=new;batches.append(dict(section=section,label=label,request=request,before=before,after=stamp(predicted)))
 totals={s:sum(b['section']==s for b in batches) for s in {b['section'] for b in batches}};parts={}
 for batch in batches:
  s=batch['section'];parts[s]=parts.get(s,0)+1
  if totals[s]>1:batch['request']['label']=batch['label']+' [part'+str(parts[s])+'/'+str(totals[s])+']'
  batch['wire_bytes']=wire_bytes(endpoint,batch['request']);batch['change_count']=len(batch['request']['changes']);assert batch['wire_bytes']<=MAX_BYTES
 request=dict(op='save',operation_id=uuid.uuid4().hex,**binding(predicted),path=str(Path(manifest['save']['path']).resolve()),portable=manifest['save'].get('portable',True));before=stamp(predicted);predicted['command_revision']+=1;batches.append(dict(section='@save',label='Pinned portable checkpoint',request=request,before=before,after=stamp(predicted),wire_bytes=wire_bytes(endpoint,request),change_count=0))
 # Protect the journal/input/endpoint separately at CLI admission; normal owner
 # Save additionally guards every actual media/protected/output alias.
 plan=dict(format=PLAN,version=1,id=uuid.uuid4().hex,manifest_id=manifest['id'],manifest_sha256=digest(original),expanded_sha256=digest(manifest),recipes=recipes,endpoint=str(Path(endpoint).resolve()),owner=owner,initial=stamp(state),sources=sources,entities=summary,ids=ids,steps=batches,limits=dict(changes=128,wire_bytes=MAX_BYTES,clients=4,ordered_clients_used=1,journal_bytes=JOURNAL_BYTES),atomicity='Each bounded section part is one owner Undo/atomic batch; no cross-part atomicity.',prepared_not_accepted=True)
 if len(encoded(plan))>JOURNAL_BYTES//2:raise ValueError('Plan/journal accounting exceeds8MiB helper budget; no command submitted.')
 return plan

@contextmanager
def journal_lock(folder):
 """OS lease releases on process death; no stale lock takeover heuristic."""
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);stream=(folder/'workflow.lock').open('a+b');stream.seek(0,2)
 if not stream.tell():stream.write(b'0');stream.flush()
 stream.seek(0);locked=False
 try:
  if os.name=='nt':
   import msvcrt
   try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
   except OSError:raise Conflict('Another helper owns this journal; no request submitted.')
  else:
   import fcntl
   try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except OSError:raise Conflict('Another helper owns this journal; no request submitted.')
  locked=True;yield
 finally:
  if locked:
   stream.seek(0)
   if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
   else:fcntl.flock(stream,fcntl.LOCK_UN)
  stream.close()

class Journal:
 def __init__(self,folder,plan=None):
  self.path=Path(folder)/'journal.json';self.expected=file_hash(self.path) if self.path.exists() else None
  if self.expected:
   if self.path.stat().st_size>JOURNAL_BYTES:raise Conflict('Journal is oversized; preserved.')
   self.value=json.loads(self.path.read_text(encoding='utf8'))
   if self.value.get('format')!=JOURNAL or self.value.get('version')!=1:raise Conflict('Unrecognized existing journal; preserved.')
   if self.value.get('plan_sha256')!=digest(self.value['plan']):raise Conflict('Saved exact plan changed; preserve it and make a deliberate new plan.')
   if plan is not None and self.value['plan']!=plan:raise Conflict('Existing journal belongs to a different exact plan; choose a new task destination.')
  elif plan is None:raise Conflict('Resume journal does not exist.')
  else:self.value=dict(format=JOURNAL,version=1,plan=deepcopy(plan),plan_sha256=digest(plan),records=[]);self.save()
 def save(self):
  if self.path.exists()!=(self.expected is not None) or self.expected is not None and file_hash(self.path)!=self.expected:raise Conflict('Journal changed after capture; later edits preserved.')
  raw=encoded(self.value)
  if len(raw)>JOURNAL_BYTES:raise Conflict('Journal budget reached; accepted work retained; no new submission.')
  temporary=self.path.with_name('journal-'+uuid.uuid4().hex+'.tmp')
  with temporary.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  if self.path.exists()!=(self.expected is not None) or self.expected is not None and file_hash(self.path)!=self.expected:raise Conflict('Journal changed while writing; both retained.')
  os.replace(temporary,self.path);self.expected=hashlib.sha256(raw).hexdigest()

def same_state(actual,expected):return stamp(actual)==expected
def apply_plan(endpoint,journal,*,timeout=120.,send=call,stop_after=None):
 """One ordered client. Resume reconciles SAME exact IDs; never silently rebases."""
 plan=journal.value['plan']
 if plan.get('format')!=PLAN or endpoint_identity(endpoint)!=plan['owner'] or str(Path(endpoint).resolve())!=plan['endpoint']:raise Conflict('Owner endpoint changed; explicit new plan/reconciliation required.')
 current=read_state(endpoint)
 if binding(current)['expected_epoch']!=plan['initial']['binding']['expected_epoch'] or current['project_id']!=plan['initial']['binding']['expected_project']:raise Conflict('Owner/project epoch changed; no automatic resume/rebase.')
 records=journal.value['records'];completed=0
 for index,step in enumerate(plan['steps']):
  request=step['request'];key=request['operation_id']
  if index<len(records):
   record=records[index]
   if record['request']!=request or record['request_sha256']!=digest(request):raise Conflict('Journal request differs from its exact plan; preserved.')
   if record.get('verified') and record.get('receipt',{}).get('status') in ('accepted','durable'):
    completed+=1;continue
   result=send(endpoint,dict(op='operation_status',operation_id=key));outcome=result.get('outcome')
  else:
   current=read_state(endpoint)
   if not same_state(current,step['before']):raise Conflict('Intervening manual/owner command changed the planned boundary; no new command submitted.')
   if wire_bytes(endpoint,request)>MAX_BYTES:raise Conflict('Actual authenticated UTF8/newline request exceeds512KiB; no submission.')
   record=dict(request=deepcopy(request),request_sha256=digest(request),binding=deepcopy(step['before']),wire_bytes=wire_bytes(endpoint,request),phase='prepared-before-send');records.append(record);journal.save();outcome=None
  if outcome is None:
   current=read_state(endpoint)
   if not same_state(current,step['before']):raise Uncertain('Detailed outcome is unknown/retired and boundary advanced. Keep accepted work; explicitly reconcile/new-plan. No replacement ID.')
   verify_sources(plan['sources'])
   # Same pre-command clock+document proves this deliberate command has not
   # advanced owner acceptance. Exact replay also protects a racing admission.
   record['phase']='send-started';journal.save()
   try:result=send(endpoint,deepcopy(request));outcome=result.get('outcome')
   except (OSError,RuntimeError,TimeoutError) as exc:
    record['transport_error']=str(exc)[:512];journal.save();raise Uncertain('Reply uncertain; resume queries the recorded SAME operation ID.') from exc
   if outcome is None:
    record['transport_error']=str(result.get('error','No detailed reply'))[:512];journal.save();raise Uncertain('Submission outcome unknown; reconcile SAME ID, no automatic replacement.')
  end=time.monotonic()+timeout
  while outcome.get('status') not in TERMINAL:
   if time.monotonic()>=end:raise Uncertain('Preparation remains owned; journal retained. Resume queries SAME ID.')
   time.sleep(.03);result=send(endpoint,dict(op='operation_status',operation_id=key));outcome=result.get('outcome')
   if outcome is None:raise Uncertain('Detailed outcome retired/unknown; no automatic replacement ID.')
  # Save a compact actual receipt (no full state/token) before inspecting any
  # later document. Accepted work must never become a false rejection.
  record['receipt']=deepcopy(outcome);record['phase']='terminal';journal.save()
  if outcome['status'] not in ('accepted','durable'):raise Conflict('Owner '+outcome['status']+': '+str(outcome.get('error',{}))+'. Accepted prior sections retained; use a deliberate new plan.')
  if outcome.get('revision')!=step['after']['binding']['expected_revision']:raise Uncertain('Receipt revision differs from planned revision; preserve/reconcile accepted work.')
  current=read_state(endpoint);record['observed_after']=stamp(current);journal.save()
  if not same_state(current,step['after']):raise Conflict('Command accepted, then owner/manual work diverged. Receipt retained; no dependent submission.')
  if request['op']=='save':
   result=outcome.get('result',{})
   if result.get('revision')!=request['expected_revision'] or result.get('path')!=request['path'] or not Path(request['path']).is_file() or file_hash(request['path'])!=result.get('sha256'):raise Uncertain('Pinned durable receipt/output differs; retain accepted project and reconcile destination.')
  record['verified']=True;journal.save()
  completed+=1
  if stop_after is not None and completed>=stop_after:return dict(status='partial',completed=completed,total=len(plan['steps']),accepted_not_necessarily_durable=True)
 current=read_state(endpoint);last=records[-1]['receipt']['result'];path=Path(last['path'])
 if not path.is_file() or file_hash(path)!=last['sha256']:raise Uncertain('Prior durable output changed after its receipt; accepted work and journal retained. Choose a deliberate checkpoint/new plan.')
 return dict(status='complete',completed=completed,total=len(plan['steps']),durable_revision=plan['steps'][-1]['request']['expected_revision'],current_matches=stamp(current)==plan['steps'][-1]['after'],journal=str(journal.path))
