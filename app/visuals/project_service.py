"""Authoritative video-project service, owned by Studio's existing control thread.

Workers prepare immutable input/save snapshots. Only poll/request on the owning
thread installs document/history state. UI and local API call this same service.
"""
from pathlib import Path
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor,Future
from copy import deepcopy
import hashlib,json,os,threading,time,uuid,traceback
from video_project import create,validate,apply,ProjectError,fail,identity,MAX_DOCUMENT_BYTES,LIMITS,duration,text,fields,integer,VERSION

def summary(row):
 result=deepcopy({k:v for k,v in row.items() if k not in ('result','files')})
 if 'files' in row:
  from project_import import counts
  files=row['files'];result.update(file_count=len(files),file_counts=counts(files),files=deepcopy(files[:4]),files_truncated=max(0,len(files)-4))
 if 'result' in row:
  r=row['result'];result['result']=deepcopy({k:v for k,v in r.items() if k not in ('dependencies','warnings')});result['result']['dependency_count']=len(r.get('dependencies',{}));result['result']['warnings']=deepcopy(r.get('warnings',[])[:8])
 return result

def digest(path,cancel=None):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while True:
   if cancel and cancel.is_set():fail('cancelled','Preparation cancelled; accepted project retained.')
   data=f.read(1024*1024)
   if not data:break
   h.update(data)
 return h.hexdigest()
def resolve(asset,base):
 loc=asset['location'];p=Path(loc['path'])
 if loc['kind']=='relative':
  if base is None:fail('missing_project_base','Relative media needs an opened project directory.')
  p=(Path(base)/p).resolve()
  if not p.is_relative_to(Path(base).resolve()):fail('invalid_path','Relative media escapes the project directory.')
 return p.resolve()
def availability(document,base,cancel=None):
 result={}
 for a in document['media']:
  p=resolve(a,base)
  try:actual=digest(p,cancel);status='Ready' if actual==a['sha256'] else 'Changed'
  except FileNotFoundError:status='Missing'
  except OSError as exc:status='Unavailable';result[a['id']]=dict(status=status,error=str(exc),path=str(p));continue
  result[a['id']]=dict(status=status,path=str(p),expected=a['sha256'])
 return result
def read_project(path,cancel):
 path=Path(path).resolve()
 if path.stat().st_size>MAX_DOCUMENT_BYTES:fail('capacity','Video project exceeds 512 KiB.')
 data=json.loads(path.read_text('utf-8-sig'))
 if not isinstance(data,dict) or data.get('format')!='zerawave-video-project-file' or data.get('version')!=1:fail('unsupported_project','Unsupported video-project file; previous project retained. Layer sessions use Open session.')
 fields(data,('format','version','revision','document'))
 doc=validate(data['document'],allow_missing_routes=True)
 revision=data['revision']
 if type(revision) is not int or revision<0:fail('invalid_revision','Invalid saved revision.')
 states=availability(doc,path.parent,cancel)
 # In-memory references are always explicit absolute identities. Disk uses
 # relative managed paths; history therefore survives Save As rebinding.
 for a in doc['media']:a['location']=dict(kind='external',path=states[a['id']]['path'])
 return doc,revision,states,str(path)
def prepare_changes(changes,base,cancel):
 changes=deepcopy(changes)
 for c in changes:
  if c['op'] not in ('media.add','media.relink'):continue
  for flag in ('placeholder','accept_changed'):
   if flag in c and type(c[flag]) is not bool:fail('invalid_value',flag+' must be true or false.')
  a=dict(location=c['location']);path=resolve(a,base)
  if c.get('placeholder') and not path.exists():c['location']=dict(kind='external',path=str(path));continue
  actual=digest(path,cancel)
  if c.get('sha256') and c['sha256']!=actual and not c.get('accept_changed'):fail('changed_media','Imported file differs from the recorded identity.')
  from media_registry import inspect
  inspected=inspect(str(path),cancel);kind={'Images':'Image','Video':'Video','Audio':'Audio'}.get(inspected['kind'])
  if kind is None or kind!=c.get('kind'):fail('unsupported_media','Source format does not match the requested video/audio/image type.')
  if kind=='Video':
   from project_media import source_metadata
   inspected['metadata'].update(source_metadata(path,cancel))
  c.setdefault('provenance',{}).setdefault('import_path',str(path))
  c.update(sha256=actual,metadata=inspected['metadata'],location=dict(kind='external',path=str(path)))
 return changes
def schema_backup(destination,expected,cancel,target_version=VERSION):
 # Save never upgrades an old file without a source-bound, independently durable
 # copy in the SAME directory, so its relative media paths remain usable.
 exists=destination.exists()
 if exists!=(expected is not None) or exists and digest(destination,cancel)!=expected:fail('destination_changed','Save destination changed during preparation. Existing file retained; inspect it or choose Save As.')
 if not exists:return None
 raw=destination.read_bytes()
 if len(raw)>MAX_DOCUMENT_BYTES:fail('unsupported_project','Existing destination is not a supported bounded project; choose a new destination.')
 try:prior=json.loads(raw.decode('utf-8-sig'))
 except (ValueError,UnicodeError):fail('unsupported_project','Existing destination is not a readable project. It was preserved; choose Save As.')
 if not isinstance(prior,dict) or prior.get('format')!='zerawave-video-project-file' or type(prior.get('version')) is not int or prior.get('version')!=1 or not isinstance(prior.get('document'),dict):fail('unsupported_project','Existing destination has an unsupported format; choose Save As.')
 if hashlib.sha256(raw).hexdigest()!=expected:fail('destination_changed','Destination changed while reading its backup. It was retained.')
 fields(prior,('format','version','revision','document'));integer(prior['revision'],0);version=prior['document'].get('version')
 if type(version) is not int or version not in (1,2,VERSION):fail('unsupported_project','Existing destination uses an unsupported schema; choose Save As.')
 validate(prior['document'],allow_missing_routes=True)
 if version==target_version:return None
 target=destination.with_name(destination.stem+'.before-v'+str(target_version)+'-'+expected[:16]+'.zwv')
 if target.exists():
  if digest(target,cancel)!=expected:fail('backup_conflict','Legacy-schema backup has changed. Both files were retained; choose Save As.')
  return str(target)
 if sum(p.name.startswith(destination.stem+'.before-v') and p.suffix=='.zwv' for p in destination.parent.iterdir())>=8:fail('backup_capacity','Eight legacy-schema backups are retained. Choose a new Save As destination; no backups were removed.')
 temporary=target.with_name('.'+target.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  with temporary.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  if cancel.is_set():fail('cancelled','Save cancelled before schema upgrade; old project retained.')
  try:os.link(temporary,target)
  except FileExistsError:
   if digest(target,cancel)!=expected:fail('backup_conflict','A different schema backup appeared; choose Save As.')
 finally:
  try:temporary.unlink(missing_ok=True)
  except OSError:pass
 return str(target)

def write_project(document,revision,base,path,portable,cancel,allow_missing=False):
 barrier=os.environ.get('ZERAWAVE_PROJECT_TEST_SAVE_BARRIER')
 while barrier and Path(barrier).exists():
  if cancel.wait(.02):fail('cancelled','Pinned project save cancelled before durable completion; accepted work retained.')
 if cancel.is_set():fail('cancelled','Pinned project save cancelled before preparation.')
 destination=Path(path).resolve();sources={a['id']:resolve(a,base) for a in document['media']}
 protected={os.path.normcase(str(p)) for p in sources.values()}|{os.path.normcase(str(Path(p).resolve())) for p in document['protected_paths']}
 protected.update(os.path.normcase(str(Path(p).resolve())) for a in document['media'] for p in [a.get('provenance',{}).get('import_path'),a.get('provenance',{}).get('original_path')] if p)
 if os.path.normcase(str(destination)) in protected:fail('protected_source','Save destination is a source or protected output.')
 if destination.exists():
  aliases=list(sources.values())+[Path(p) for p in document['protected_paths']]+[Path(p) for a in document['media'] for p in (a.get('provenance',{}).get('import_path'),a.get('provenance',{}).get('original_path')) if p]
  for source in aliases:
   if source.exists() and os.path.samefile(source,destination):fail('protected_source','Save destination aliases a protected source/output.')
 if destination.suffix.lower()!='.zwv':fail('invalid_destination','Video-project Save requires a .zwv destination. Still images and Export Video are separate actions.')
 prior_destination=digest(destination,cancel) if destination.exists() else None
 destination.parent.mkdir(parents=True,exist_ok=True);saved=deepcopy(document);staging=destination.parent/('.'+destination.name+'.work-'+uuid.uuid4().hex);warnings=[];dependencies={};committed=False
 try:
  for a in saved['media']:
   src=sources[a['id']]
   try:actual=digest(src,cancel)
   except FileNotFoundError:
    if not allow_missing:fail('missing_media','Save needs missing source '+a['name']+'. Relink, or explicitly save reference-only placeholders.')
    warnings.append('Missing source retained as a placeholder: '+a['name']);a['location']=dict(kind='external',path=str(src));dependencies[a['id']]='missing';continue
   if actual!=a['sha256']:fail('changed_media','Source changed before saving: '+a['name'])
   if portable:
    folder=destination.parent/(destination.stem+'.media');folder.mkdir(exist_ok=True);target=folder/(a['sha256']+src.suffix.lower())
    if target.exists():
     if digest(target,cancel)!=a['sha256']:fail('changed_media','Managed dependency collision; existing file retained.')
    else:
     temporary=folder/('.'+target.name+'.work-'+uuid.uuid4().hex)
     with src.open('rb') as reader,temporary.open('xb') as writer:
      while True:
       if cancel.is_set():fail('cancelled','Save cancelled; previous project retained.')
       block=reader.read(1024*1024)
       if not block:break
       writer.write(block)
      writer.flush();os.fsync(writer.fileno())
     if digest(temporary,cancel)!=a['sha256']:fail('changed_media','Source changed during copy; previous project retained.')
     os.replace(temporary,target)
    a['location']=dict(kind='relative',path=target.relative_to(destination.parent).as_posix())
   else:a['location']=dict(kind='external',path=str(src))
   dependencies[a['id']]='secured' if portable else 'verified_external_reference'
  from project_audio_graph import missing_routes
  warnings.extend('Unresolved audio route retained for '+row['name']+'; playback/export requires deliberate repair.' for row in missing_routes(saved))
  payload=dict(format='zerawave-video-project-file',version=1,revision=revision,document=validate(saved,allow_missing_routes=True));raw=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf8')
  # Model and file size limits are measured in their exact serialized forms.
  if len(raw)>MAX_DOCUMENT_BYTES:fail('capacity','Saved project exceeds 512 KiB; previous file retained.')
  with staging.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  if cancel.is_set():fail('cancelled','Save cancelled; previous project retained.')
  failure=os.environ.get('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE')
  if failure=='1' or failure and Path(failure).exists():raise OSError('Controlled project write failure before atomic replacement')
  backup=schema_backup(destination,prior_destination,cancel,saved['version'])
  if document['version']>=2 and (destination.exists()!=(prior_destination is not None) or prior_destination is not None and digest(destination,cancel)!=prior_destination):fail('destination_changed','Destination changed before replacement. Existing file and accepted project retained.')
  os.replace(staging,destination)
  committed=True
  # No late cancellation check after commit: the durable result wins that race.
  return dict(path=str(destination),revision=revision,sha256=hashlib.sha256(raw).hexdigest(),dependencies=dependencies,warnings=warnings,schema_backup=backup)
 finally:
  # Partial dependency copies are retained for diagnosis; only our unpublished
  # metadata temp is removed, and never a source or prior good destination.
  try:
   if not committed and staging.exists():staging.unlink()
  except OSError as cleanup:
   if cleanup.__context__ is not None:cleanup.__context__.add_note('Unpublished project temp retained after cleanup failed: '+str(cleanup))
   else:raise

class ProjectService:
 def __init__(self):
  self.thread=threading.get_ident();self.document=None;self.revision=0;self.epoch=uuid.uuid4().hex;self.path=None;self.saved_revision=None;self.undo=[];self.redo=[];self.history_bytes=0;self.history_limit=64*1024*1024;self.outcomes=OrderedDict();self.jobs={};self.inspections={};self.pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='Video project preparation');self.version=0;self.closed=False;self.media_state={};self.admit=lambda doc:None;self.save_serial=0;self.path_serial=0;self.source_base=None;self.command_revision=0
  from project_transport import Transport
  self.transport=Transport();self.transport_admit=lambda request:None
  from project_source import SourceContext
  self.source=SourceContext();self.audio_target='program'
  from project_recovery import Recovery
  self.recovery=Recovery(self.pool)
 def _submit_preparation(self,function,*args,**kwargs):
  self.check_thread()
  if len(self.jobs)+len(self.inspections)>=16:fail('busy','Sixteen combined project preparations/inspections are pending; this request was not admitted. Accepted work remains intact.')
  return self.pool.submit(function,*args,**kwargs)
 def check_thread(self):
  if threading.get_ident()!=self.thread:raise RuntimeError('Video document may only be mutated by its Studio owner thread.')
 def transport_state(self):
  self.check_thread();self.transport.sync(self.document,self.epoch,self.revision);return dict(self.transport.state(),source=self.source.state(False)['transport'],audio_target=self.audio_target)
 def state(self,full=True,*,_omit_document=False,_owner_projection=False):
  self.check_thread();self.transport.sync(self.document,self.epoch,self.revision);self.recovery.observe(self.document,self.epoch,self.revision,self.saved_revision,self.path);value=dict(project_id=self.document['id'] if self.document else None,command_revision=self.command_revision,document=self.document if full and not _omit_document else None,revision=self.revision,epoch=self.epoch,path=self.path,saved_revision=self.saved_revision,dirty=self.document is not None and self.revision!=self.saved_revision,undo_label=self.undo[-1]['label'] if self.undo else '',redo_label=self.redo[-1]['label'] if self.redo else '',history_bytes=self.history_bytes,history_limit=self.history_limit,media=self.media_state,operations=[summary(r) for r in list(self.outcomes.values())[-64:]],limits=LIMITS,version=self.version,closed=self.closed,recovery=self.recovery.state(),transport=self.transport.state(),source=self.source.state(full),audio_target=self.audio_target)
  # Only the same-thread section publisher may read owner references here; it
  # copies before retaining/publication. Public/API callers always detach.
  return value if _owner_projection else deepcopy(value)
 def release_for_layers(self,binding,validate_only=False):
  """Explicit valid Layer Play hands off runtime only, preserving both positions.

  The outer ordered media operation supplies replay/receipt ownership. Its
  captured project clocks must still match before any layer/project change.
  Inspection, selection and Layer pause/seek do not acquire this handoff.
  """
  self.check_thread();self.transport_state();self.source.state(False)
  clocks=[clock for clock in (self.transport,self.source.transport) if clock.active]
  if not clocks:return False
  if not isinstance(binding,dict):fail('unbound_handoff','Video Editor/Source still owns transport. Refresh and press Layer Play again with its current project binding; no playback was changed.')
  self._guard(binding)
  if validate_only:return True
  for clock in clocks:clock.command('release')
  self.command_revision+=1;self.version+=1
  return True
 def _guard(self,data,command=True):
  if self.closed:fail('closed','Project service is closed.')
  if type(data.get('expected_revision')) is not int:fail('invalid_revision','Expected revision must be an integer.')
  if data.get('expected_epoch')!=self.epoch or data.get('expected_revision')!=self.revision or data.get('expected_project')!=(self.document['id'] if self.document else None):fail('stale_revision','Project changed; inspect current state and explicitly rebase the operation. Nothing was applied.')
  if command and (type(data.get('expected_command')) is not int or data['expected_command']!=self.command_revision):fail('stale_command','Another command arrived or this operation result retired. This submission applied nothing. Inspect project/output state; do not automatically rebase an uncertain operation.')
 def _record(self,key,request):
  request_hash=hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();previous=self.outcomes.get(key)
  if previous:
   if previous['request_hash']!=request_hash:fail('operation_conflict','Operation ID was reused with different contents.')
   return previous,True
  while len(self.outcomes)>=1024:
   first=next(iter(self.outcomes))
   if self.outcomes[first]['status'] in ('preparing','saving','exporting'):fail('busy','Operation retention is busy; wait for the pinned work.')
   self.outcomes.pop(first)
  row=dict(id=key,request_hash=request_hash,status='preparing',op=request['op'],requested_revision=self.revision,at=time.time());self.outcomes[key]=row;self.version+=1;return row,False
 def _reserved(self,document):
  from project_export import protect
  for job in self.jobs.values():
   if job['kind'] in ('export','caption_export','recovery_copy'):
    try:protect(document,job['path'],suffix='.srt' if job['kind']=='caption_export' else '.zwv' if job['kind']=='recovery_copy' else '.mp4')
    except ProjectError as exc:
     if exc.code=='protected_source':fail('reserved_destination','This source/protected path aliases a pending export destination. Wait for its real outcome, then import/protect deliberately; existing document retained.')
     raise
 def _preflight_reserved(self,changes):
  if not any(j['kind'] in ('export','caption_export','recovery_copy') for j in self.jobs.values()):return
  # Reject reference conflicts before asynchronous preparation starts; repeat
  # the same guard at the owning commit boundary for aliases/races.
  references={'media':[],'protected_paths':[]}
  for change in changes:
   if change['op'] in ('media.add','media.relink'):
    location=dict(kind='external',path=str(resolve({'location':change['location']},self.source_base)))
    references['media'].append(dict(location=location,provenance=change.get('provenance',{})))
   elif change['op']=='project.protect':references['protected_paths'].extend(change.get('paths',[]))
  self._reserved(references)
 def _commit(self,new,label,created,media_state=None):
  self._reserved(new);self.admit(new)
  states=deepcopy(self.media_state if media_state is None else media_state)
  states={k:v for k,v in states.items() if k in {a['id'] for a in new['media']}}
  if new==self.document:
   if states!=self.media_state:self.media_state=states;self.version+=1
   return created
  cost=len(json.dumps([self.document,new,self.media_state,states],ensure_ascii=False).encode())
  retained=self.history_bytes-sum(r['bytes'] for r in self.redo)
  if retained+cost>self.history_limit:fail('history_capacity','Project history is full; operation rejected before acceptance. Existing edits/history remain.')
  # Retain exact existing histories rather than discarding them for a zero count.
  # Accepted documents are owner-private immutable values: apply always copies,
  # public snapshots detach, and save/export workers receive private snapshots.
  # Adjacent history entries can retain the same exact document. No operation
  # is coalesced or removed, and the conservative history charge stays.
  self.undo.append(dict(before=self.document,after=new,before_media=deepcopy(self.media_state),after_media=states,label=label,bytes=cost));self.redo=[];self.history_bytes=retained+cost;self.document=new;self.media_state=deepcopy(states);self.revision+=1;self.version+=1;return created
 def _apply(self,request,prepared=None):
  op=request['op']
  if op=='transport':
   target=request.get('target','program')
   if target not in ('program','source'):fail('invalid_target','Transport target is Program or Source.')
   if target=='program' and request.get('action')=='play' and self.document is not None:
    from project_audio_graph import validate as validate_audio_graph
    validate_audio_graph(self.document)
   if target=='source' and request.get('source_epoch') is not None and request['source_epoch']!=self.source.epoch:fail('stale_source','Source changed; the previous Source gesture was not applied.')
   self.transport_admit(request);self.transport.sync(self.document,self.epoch,self.revision)
   clock=self.source.transport if target=='source' else self.transport
   if target=='source' and self.source.document is None:fail('no_source','Open a source before Source transport.')
   # Validate without switching the audible context on an invalid command.
   clock.command(request['action'],request.get('frame'))
   if request['action']=='play' or target=='program' and self.audio_target=='source' and request['action'] in ('seek','seek_paused','beginning','last','step'):
    other=self.transport if target=='source' else self.source.transport
    if other.binding and other.binding[2]:other.command('release')
    self.audio_target=target
   return []
  if op=='source_open':self._reserved(prepared);self.source.install(prepared);return []
  if op=='source_release':self.source.release();return []
  if op=='new':
   if self.document is not None and self.revision!=self.saved_revision and not request.get('discard'):fail('unsaved_project','Save or explicitly discard the current project before creating another.')
   base=request.get('base_directory')
   if base is not None and not Path(base).is_dir():fail('invalid_path','Explicit media base must be an existing directory.')
   doc=create(request.get('name','Untitled video'),request.get('settings'),request.get('project_id'));self.admit(doc);self.source.clear();self.audio_target='program';self.document=doc;self.revision=0;self.saved_revision=None;self.path=None;self.epoch=uuid.uuid4().hex;self.undo=[];self.redo=[];self.history_bytes=0;self.media_state={};self.source_base=str(Path(base).resolve()) if base else None;self.version+=1;return [doc['id']]
  if self.document is None:fail('no_project','Create or open a video project first.')
  if op=='import_captions':
   doc=self.document;created=[]
   for begin in range(0,len(prepared),LIMITS['batch']):
    doc,part=apply(doc,prepared[begin:begin+LIMITS['batch']],request['operation_id']);created.extend(part)
   return self._commit(doc,request.get('label','Import SRT captions'),created)
  if op=='import_media':
   changes=prepared['changes']
   if not changes:return []
   doc,created=apply(self.document,changes,request['operation_id']);states=deepcopy(self.media_state)
   for c in changes:states[c['id']]=dict(status='Ready',path=c['location']['path'],expected=c['sha256'])
   return self._commit(doc,request.get('label','Import Project Media'),created,states)
  if op=='batch':
   changes=prepared if prepared is not None else request['changes'];doc,created=apply(self.document,changes,request['operation_id']);states=deepcopy(self.media_state)
   if prepared is not None:
    for index,c in enumerate(changes):
     if c['op'] in ('media.add','media.relink'):
      asset_id=c.get('id') or uuid.uuid5(uuid.UUID(request['operation_id']),str(index)).hex;asset=next(a for a in doc['media'] if a['id']==asset_id);states[asset_id]=dict(status='Missing' if c.get('placeholder') and not Path(c['location']['path']).exists() else 'Ready',path=c['location']['path'],expected=asset['sha256'])
   return self._commit(doc,request.get('label','Edit video project'),created,states)
  if op in ('undo','redo'):
   source=self.undo if op=='undo' else self.redo;target=self.redo if op=='undo' else self.undo
   if not source:return []
   row=source[-1];doc=deepcopy(row['before' if op=='undo' else 'after']);self._reserved(doc);self.admit(doc);source.pop();target.append(row);self.document=doc;self.media_state=deepcopy(row['before_media' if op=='undo' else 'after_media']);self.revision+=1;self.version+=1;return []
  if op=='close':
   if self.revision!=self.saved_revision and not request.get('discard'):fail('unsaved_project','Save accepted project work or explicitly discard before closing it.')
   self.source.clear();self.audio_target='program';self.document=None;self.epoch=uuid.uuid4().hex;self.revision=0;self.path=None;self.saved_revision=None;self.media_state={};self.undo=[];self.redo=[];self.history_bytes=0;self.version+=1;return []
  fail('unsupported_command','Unsupported project command: '+str(op))
 def request(self,data):
  self.check_thread()
  if not isinstance(data,dict):return dict(ok=False,error=dict(code='invalid_request',message='Project request must be a structured object.'),outcome=None)
  op=data.get('op')
  if op=='state':return dict(ok=True,state=self.state())
  if op=='audio_inspect':
   try:
    self._guard(data,command=False)
    if len(self.inspections)>=4:fail('busy','Audio inspections share the bounded preparation pool; wait for the pending queries. No edit was made.')
    from project_audio_inspection import inspect_audio
    document=deepcopy(self.document);media=deepcopy(self.media_state);query=deepcopy(data);cancel=threading.Event();reply=Future()
    worker=self._submit_preparation(inspect_audio,document,self.epoch,self.revision,query,media,cancel)
    self.inspections[reply]=dict(future=worker,cancel=cancel,query=query,media=media)
    return reply
   except (ProjectError,ValueError,TypeError,KeyError) as exc:
    return dict(ok=False,error=dict(code=getattr(exc,'code','invalid_request'),message=str(exc)))
  if op=='review_cancel':
   try:
    key=identity(data['query_id']);found=False
    for job in self.inspections.values():
     if job.get('kind')=='review' and job['query'].get('query_id')==key:job['cancel'].set();found=True
    return dict(ok=True,cancel_requested=found,query_id=key)
   except (ProjectError,KeyError,TypeError) as exc:return dict(ok=False,error=dict(code=getattr(exc,'code','invalid_request'),message=str(exc)))
  if op=='review_inspect':
   try:
    self._guard(data,command=False)
    if len(self.inspections)>=4:fail('busy','Four shared audio/source inspections are pending; this review was not admitted. No edit was made.')
    from project_review import inspect_review
    document=deepcopy(self.document);media=deepcopy(self.media_state);source=self.source.state();query=deepcopy(data);query.setdefault('query_id',uuid.uuid4().hex);identity(query['query_id'])
    if any(job.get('kind')=='review' and job['query'].get('query_id')==query['query_id'] for job in self.inspections.values()):fail('busy','This read-only review query is already pending; no duplicate inspection admitted.')
    cancel=threading.Event();reply=Future();worker=self._submit_preparation(inspect_review,document,self.epoch,self.revision,query,media,source,cancel)
    self.inspections[reply]=dict(kind='review',future=worker,cancel=cancel,query=query,media=media,source=source)
    return reply
   except (ProjectError,ValueError,TypeError,KeyError) as exc:return dict(ok=False,error=dict(code=getattr(exc,'code','invalid_request'),message=str(exc)))
  if op=='recovery_refresh':self.recovery.refresh();return dict(ok=True,state=self.state(False))
  if op=='operation_status':
   outcome=deepcopy(self.outcomes.get(data['operation_id']))
   return dict(ok=outcome is not None,outcome=outcome,state=self.state(False),**({} if outcome is not None else dict(error=dict(code='outcome_unknown',message='Operation is unknown or its detailed result retired. This query applied nothing; inspect current project/output state. Do not automatically rebase or submit a new operation ID.'))))
  if op=='cancel':
   job=self.jobs.get(data['operation_id'])
   if job:job['cancel'].set()
   return dict(ok=True,outcome=deepcopy(self.outcomes.get(data['operation_id'])))
  try:
   key=identity(data['operation_id']);row,replay=self._record(key,data)
   if replay:return dict(ok=row['status'] not in ('rejected','failed'),outcome=deepcopy(row),state=self.state(False))
   self._guard(data);self.recovery.resume()
   prior_identity=(self.epoch,self.revision)
   text(data.get('label','Edit video project'),256)
   if op=='batch':
    changes=data.get('changes')
    if not isinstance(changes,list) or not 1<=len(changes)<=LIMITS['batch']:fail('invalid_batch','Batch requires 1–128 structured edits.')
    for change in changes:
     if not isinstance(change,dict) or not isinstance(change.get('op'),str):fail('invalid_batch','Every batch member must be an edit object with an operation name.')
     for field in ('values','metadata','provenance','audio','layout','location'):
      if field in change and not isinstance(change[field],dict):fail('invalid_request',field+' must be a structured object.')
   for flag in ('discard','portable','allow_missing'):
    if flag in data and type(data[flag]) is not bool:fail('invalid_value',flag+' must be true or false.')
   if op=='import_media':
    paths=data.get('paths')
    if self.document is None:fail('no_project','Create/open a project before importing references.')
    if not isinstance(paths,list) or not 1<=len(paths)<=LIMITS['batch']:fail('invalid_batch','One import group requires1–128 paths.')
    for path in paths:
     text(path,1024)
     if not Path(path).is_absolute():fail('invalid_path','Import paths must be explicit absolute files.')
   if op in ('new','open','close','undo','redo','batch','import_captions','import_media') and any(j['kind'] not in ('save','export','caption_export','recovery_copy','source') for j in self.jobs.values()):fail('busy','Source/open preparation is pending; completed edit was not accepted. Wait and repeat it.')
   if op in ('new','open','close') and self.jobs:fail('busy','Pinned save/export work is pending; wait for its real outcome before replacement/close.')
   cancel=threading.Event();job=None
   if op=='batch':self._preflight_reserved(data['changes'])
   if op=='import_media':
    from project_import import prepare,Progress
    self._preflight_reserved([dict(op='media.add',location=dict(kind='external',path=p)) for p in paths]);progress=Progress();row['files']=[dict(index=i,path=p,name=Path(p).name[:256],status='queued') for i,p in enumerate(paths)];job=dict(kind='import_media',progress=progress,future=self._submit_preparation(prepare,list(paths),deepcopy(self.document),deepcopy(self.media_state),self.source_base,key,cancel,progress))
   elif op=='source_open':
    if any(j['kind']=='source' for j in self.jobs.values()):fail('busy','Source inspection is pending; wait or cancel its exact operation.')
    from project_source import prepare_source
    job=dict(kind='source',future=self._submit_preparation(prepare_source,data.get('asset'),key,cancel))
   elif op=='open':
    if self.document is not None and self.revision!=self.saved_revision and not data.get('discard'):fail('unsaved_project','Save or explicitly discard before opening another project.')
    job=dict(kind='open',future=self._submit_preparation(read_project,data['path'],cancel))
   elif op=='batch' and any(c.get('op') in ('media.add','media.relink') for c in data['changes']):job=dict(kind='batch',future=self._submit_preparation(prepare_changes,data['changes'],self.source_base,cancel))
   elif op=='import_captions':
    if self.document is None:fail('no_project','Create/open a project before importing captions.')
    track=next((t for t in self.document['tracks'] if t['id']==data.get('track')),None)
    if not track or track['kind']!='graphics':fail('invalid_track','Caption import needs a selected graphics track.')
    from project_text import parse_srt
    job=dict(kind='caption_import',future=self._submit_preparation(parse_srt,data['path'],track['id'],deepcopy(self.document['settings']['fps']),key,cancel))
   elif op=='recover_copy':
    from project_recovery import recover_copy
    from project_export import protect
    target=protect(self.document or {'media':[],'protected_paths':[]},data['path'],[self.path],suffix='.zwv')
    if any(os.path.normcase(j.get('path',''))==os.path.normcase(str(target)) for j in self.jobs.values()):fail('busy','This destination is already pinned by another job.')
    row['status']='saving';job=dict(kind='recovery_copy',path=str(target),future=self._submit_preparation(recover_copy,self.recovery.root,data['snapshot'],data['snapshot_sha256'],str(target),cancel))
   elif op=='export_captions':
    if self.document is None:fail('no_project','Create/open a project before exporting captions.')
    from project_caption_export import write_srt
    from project_export import protect
    target=protect(self.document,data['path'],[self.path],suffix='.srt')
    history_paths=set()
    for history in self.undo+self.redo:
     for retained in (history['before'],history['after']):
      if retained:
       history_paths.update(retained['protected_paths'])
       for asset in retained['media']:
        history_paths.add(asset['location']['path']);history_paths.update(p for p in (asset.get('provenance',{}).get('import_path'),asset.get('provenance',{}).get('original_path')) if p)
    protect({'media':[],'protected_paths':list(history_paths)},target,[self.path],suffix='.srt')
    if any(os.path.normcase(j.get('path',''))==os.path.normcase(str(target)) for j in self.jobs.values()):fail('busy','This destination is already pinned by another job.')
    row['status']='exporting';job=dict(kind='caption_export',path=str(target),future=self._submit_preparation(write_srt,deepcopy(self.document),self.revision,str(target),cancel,[self.path]))
   elif op=='export':
    if self.document is not None:
     from project_audio_graph import validate as validate_audio_graph
     validate_audio_graph(self.document)
    if self.document is None:fail('no_project','Create/open a project before Export Video.')
    if any(j['kind'] in ('export','caption_export','recovery_copy') for j in self.jobs.values()):fail('busy','One export context/job is already owned; wait or cancel that exact operation.')
    if any(r.get('status')!='Ready' for r in self.media_state.values()):fail('missing_media','Relink unavailable project sources before export.')
    from project_export import export_project,protect,export_range
    if any(j['kind'] not in ('save','export','caption_export','recovery_copy') for j in self.jobs.values()):fail('busy','An unaccepted source/open edit is preparing; reconcile it before pinning export.')
    from video_project import integer
    frame_range=export_range(self.document,data.get('range'));crf=integer(data.get('crf',self.document['export']['crf']),0,51);target=protect(self.document,data['path'],[self.path])
    history_paths=set()
    for history in self.undo+self.redo:
     for retained in (history['before'],history['after']):
      if retained is not None:
       history_paths.update(retained['protected_paths'])
       for asset in retained['media']:
        history_paths.add(asset['location']['path']);history_paths.update(p for p in (asset.get('provenance',{}).get('import_path'),asset.get('provenance',{}).get('original_path')) if p)
    protect({'media':[],'protected_paths':list(history_paths)},target,[self.path])
    if any(os.path.normcase(j.get('path',''))==os.path.normcase(str(target)) for j in self.jobs.values()):fail('busy','This destination is already pinned by another job.')
    folder=Path(os.environ.get('ZERAWAVE_ARTWORK_STORE',str(Path(__file__).resolve().parents[2]/'work/project-exports'))).parent/('project-export-'+key)
    export_function=export_project;export_args=[deepcopy(self.document),self.epoch,self.revision,str(target),crf,str(folder),cancel,[self.path] if self.path else [],frame_range]
    if 'review_sample' in data:
     from project_review import export_review_project,certificate_ok
     certificate_ok(data['review_sample']);export_function=export_review_project;export_args.extend([deepcopy(self.media_state),self.source.state(),deepcopy(data['review_sample'])])
    row['status']='exporting';row['diagnostics']=str(folder);job=dict(kind='export',path=str(target),folder=str(folder),future=self._submit_preparation(export_function,*export_args))
   elif op=='save':
    if self.document is None:fail('no_project','Create/open a project before saving.')
    target=str(Path(data.get('path') or self.path or '').resolve())
    if not data.get('path') and self.path is None:fail('missing_destination','Choose a project Save destination.')
    if any(os.path.normcase(j.get('path',''))==os.path.normcase(target) for j in self.jobs.values()):fail('busy','This destination already has a pinned save; previous/newer work retained.')
    self.save_serial+=1;row['status']='saving';job=dict(kind='save',serial=self.save_serial,path=target,future=self._submit_preparation(write_project,deepcopy(self.document),self.revision,None,target,data.get('portable',True),cancel,data.get('allow_missing',False)))
   if job:
    job.update(cancel=cancel,request=deepcopy(data),epoch=self.epoch,revision=self.revision);self.jobs[key]=job
   else:row.update(status='accepted',created=self._apply(data),revision=self.revision)
   self.command_revision+=1;self.version+=1;return dict(ok=True,outcome=deepcopy(row),state=self.state(False))
  except Exception as exc:
   known=isinstance(exc,(ProjectError,ValueError,KeyError,TypeError,OSError));error=dict(code=getattr(exc,'code','invalid_request' if known else 'internal_error'),message=str(exc))
   if not known:traceback.print_exception(type(exc),exc,exc.__traceback__)
   if 'row' in locals() and not locals().get('replay'):
    owned=locals().get('key') in self.jobs;installed=locals().get('prior_identity',(self.epoch,self.revision))!=(self.epoch,self.revision)
    if owned or installed or row['status']=='accepted':
     # Never turn an installed edit or a real pinned job into a false rejection.
     if installed:row.update(status='accepted',revision=self.revision)
     error['code']='outcome_unknown';row['warning']=str(exc)
    else:row.update(status='rejected' if known else 'failed',error=error)
    self.version+=1
   return dict(ok=False,error=error,outcome=deepcopy(locals().get('row')),state=self.state(False))
 def poll_inspections(self):
  self.check_thread()
  for reply,job in list(self.inspections.items()):
   if not job['future'].done():continue
   try:
    if job.get('kind')=='review' and job['cancel'].is_set():fail('cancelled','Source review cancelled, including late completion; no report published.')
    report=job['future'].result();self._guard(job['query'],command=False)
    if job.get('kind')=='review' and job['query'].get('source_epoch') is not None:
     current=self.source.state()
     if (current['epoch'],current['revision'],current['document'])!=(job['source']['epoch'],job['source']['revision'],job['source']['document']):fail('stale_source','Source changed while inspecting; old result was not published.')
    if self.media_state!=job['media']:fail('stale_source_verification','Source verification changed while inspecting; retained report is outdated. Inspect again.')
    value=dict(ok=True,report=report)
   except BaseException as exc:
    value=dict(ok=False,error=dict(code=getattr(exc,'code','inspection_failed'),message=str(exc)))
   del self.inspections[reply]
   if not reply.done():reply.set_result(value)
 def poll(self):
  self.check_thread();self.poll_inspections();self.recovery.observe(self.document,self.epoch,self.revision,self.saved_revision,self.path);self.recovery.poll()
  if self.recovery.version!=getattr(self,'recovery_version',-1):self.recovery_version=self.recovery.version;self.version+=1
  for key,job in list(self.jobs.items()):
   if job['kind']=='import_media':
    progress=job['progress'].take()
    if progress is not None:self.outcomes[key]['files']=progress;self.version+=1
   if not job['future'].done():
    if job['kind']=='export':
     try:
      progress=json.loads((Path(job['folder'])/'PROGRESS.json').read_text('utf8'))
      if self.outcomes[key].get('progress')!=progress:self.outcomes[key]['progress']=progress;self.version+=1
     except (OSError,ValueError):pass
    continue
   row=self.outcomes[key]
   try:
    prepared=job['future'].result()
    if job['kind']=='import_media':row['files']=deepcopy(prepared['files'])
    if job['kind'] in ('export','caption_export'):row.update(status='exported',result=prepared,revision=job['revision'])
    elif job['kind']=='recovery_copy':row.update(status='durable',result=prepared,revision=prepared['revision'])
    elif job['kind']=='save':
     row.update(status='durable',result=prepared,revision=job['revision'])
     if job['epoch']==self.epoch and job['serial']>=self.path_serial:self.path=prepared['path'];self.saved_revision=job['revision'];self.path_serial=job['serial'];self.source_base=str(Path(prepared['path']).parent)
    else:
     self._guard(job['request'],command=False)
     if job['cancel'].is_set():fail('cancelled','Preparation cancelled before acceptance.')
     if job['kind']=='open':
      self.source.clear();self.audio_target='program'
      doc,revision,states,path=prepared;self.admit(doc);self.document=doc;self.revision=revision;self.saved_revision=revision;self.media_state=states;self.path=path;self.source_base=str(Path(path).parent);self.epoch=uuid.uuid4().hex;self.undo=[];self.redo=[];self.history_bytes=0;created=[doc['id']]
     elif job['kind']=='source':
      created=self._apply(job['request'],prepared)
     else:
      created=self._apply(job['request'],prepared)
     row.update(status='accepted',created=created,revision=self.revision)
     if job['kind']=='import_media':
      from project_import import finish
      row['files']=finish(row['files'],True)
   except BaseException as exc:
    row.update(status='failed',error=dict(code=getattr(exc,'code','preparation_failed'),message=str(exc),notes=getattr(exc,'__notes__',[])))
    if job['kind']=='import_media':
     from project_import import finish
     row['files']=finish(getattr(exc,'files',row.get('files',[])),False,row['error']['code']=='cancelled')
   del self.jobs[key];self.version+=1
 def can_shutdown(self,discard=False,binding=None):
  self.poll()
  # Prepared work can install a new revision. Validate the ORIGINAL close
  # decision after that reconciliation; no later poll may escape this guard.
  if binding is not None:self._guard(binding)
  if discard:
   for job in self.jobs.values():job['cancel'].set()
  for job in self.inspections.values():job['cancel'].set()
  if self.jobs or self.inspections:return False
  if self.document is not None and self.revision!=self.saved_revision and not discard:fail('unsaved_project','Video project remains unsaved; Save it or explicitly Discard.')
  self.recovery.observe(self.document,self.epoch,self.revision,self.saved_revision,self.path)
  return self.recovery.finish()
 def shutdown(self):
  self.check_thread()
  if self.jobs or self.inspections:fail('busy','Project jobs still own immutable work; cannot release them yet.')
  self.source.clear();self.recovery.closed=True;self.pool.shutdown(wait=True);self.recovery.poll();self.closed=True
