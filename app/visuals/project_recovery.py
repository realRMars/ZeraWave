"""Bounded accepted-metadata autosaves on the existing project worker pool.

This is recovery metadata, not a project Save or a secured copy of source media.
Only this owner may rotate its four slots; other sessions are never pruned.
"""
from pathlib import Path
from contextlib import contextmanager
from copy import deepcopy
import hashlib,json,os,time,uuid
from video_project import validate,fail,fields,MAX_DOCUMENT_BYTES

MAX_FILES=32
MAX_BYTES=MAX_FILES*(MAX_DOCUMENT_BYTES+8192)
INTERVAL=30.
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

@contextmanager
def capacity_lock(root,cancel=None):
 root.mkdir(parents=True,exist_ok=True);stream=(root/'capacity.lock').open('a+b');stream.seek(0,2)
 if stream.tell()==0:stream.write(b'\0');stream.flush()
 stream.seek(0);locked=False
 try:
  if os.name=='nt':
   import msvcrt
   for attempt in range(50):
    try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1);locked=True;break
    except OSError:
     if cancel and cancel.is_set():fail('cancelled','Recovery metadata write cancelled.')
     time.sleep(.01)
   if not locked:fail('recovery_busy','Another recovery writer owns the bounded store; accepted work remains in memory.')
  else:
   import fcntl
   fcntl.flock(stream,fcntl.LOCK_EX);locked=True
  yield
 finally:
  if locked:
   stream.seek(0)
   if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
   else:fcntl.flock(stream,fcntl.LOCK_UN)
  stream.close()

def read_snapshot(root,path,expected=None):
 root=Path(root).resolve();path=Path(path).resolve()
 if path.parent!=root or path.suffix!='.zwvr':fail('invalid_recovery','Choose a recovery entry from this bounded store.')
 if path.stat().st_size>MAX_DOCUMENT_BYTES+8192:fail('invalid_recovery','Recovery metadata exceeds its bounded file size.')
 with path.open('rb') as stream:raw=stream.read(MAX_DOCUMENT_BYTES+8193)
 if len(raw)>MAX_DOCUMENT_BYTES+8192:fail('invalid_recovery','Recovery file grew beyond its bound; existing files retained.')
 actual=hashlib.sha256(raw).hexdigest()
 if expected is not None and actual!=expected:fail('recovery_changed','Recovery entry changed after selection; inspect it again. Nothing replaced.')
 row=json.loads(raw.decode('utf8'))
 if not isinstance(row,dict) or row.get('format')!='zerawave-video-recovery' or row.get('version')!=1:fail('invalid_recovery','Unsupported recovery entry retained.')
 fields(row,('format','version','owner','epoch','at','saved_revision','original_path','source_policy','payload_sha256','project'));payload=row['project'];fields(payload,('format','version','revision','document'));validate(payload['document'],allow_missing_routes=True)
 if payload.get('format')!='zerawave-video-project-file' or payload.get('version')!=1 or type(payload.get('revision')) is not int or payload['revision']<0:fail('invalid_recovery','Recovery project metadata is invalid.')
 if hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8')).hexdigest()!=row.get('payload_sha256'):fail('invalid_recovery','Recovery payload identity differs; existing files preserved.')
 return row,actual

def catalogue(root):
 root=Path(root);entries=[];errors=[]
 if not root.exists():return dict(entries=[],errors=[])
 for path in sorted(root.glob('*.zwvr'),key=lambda p:p.stat().st_mtime,reverse=True)[:MAX_FILES]:
  try:
   row,digest=read_snapshot(root,path);project=row['project'];entries.append(dict(path=str(path.resolve()),sha256=digest,project_id=project['document']['id'],name=project['document']['name'],revision=project['revision'],saved_revision=row.get('saved_revision'),at=row['at'],original_path=row.get('original_path'),owner=row['owner']))
  except (OSError,ValueError,KeyError,TypeError) as exc:errors.append(dict(path=str(path),error=str(exc)))
 return dict(entries=entries,errors=errors)

def publish(root,owner,slot,expected,document,epoch,revision,saved_revision,path):
 root=Path(root);document=validate(document,allow_missing_routes=True);payload=dict(format='zerawave-video-project-file',version=1,revision=revision,document=document);raw_payload=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf8');row=dict(format='zerawave-video-recovery',version=1,owner=owner,epoch=epoch,at=time.time(),saved_revision=saved_revision,original_path=path,source_policy='External references only; media availability/hash rechecked when the recovery copy is opened. This is not project Save.',payload_sha256=hashlib.sha256(raw_payload).hexdigest(),project=payload);raw=json.dumps(row,ensure_ascii=False,separators=(',',':')).encode('utf8')
 if len(raw)>MAX_DOCUMENT_BYTES+8192:fail('recovery_capacity','Recovery metadata exceeds its bound; accepted project retained in memory.')
 target=root/(owner+'-'+str(slot)+'.zwvr');temporary=root/('.'+target.name+'.'+uuid.uuid4().hex+'.tmp')
 with capacity_lock(root):
  exists=target.exists()
  if exists!=(expected is not None) or exists and sha(target)!=expected:fail('recovery_changed','Owned recovery slot changed externally; preserved. Choose Save As for current work.')
  files=list(root.glob('*.zwvr'));total=sum(p.stat().st_size for p in files)-(target.stat().st_size if exists else 0)
  if len(files)+(not exists)>MAX_FILES or total+len(raw)>MAX_BYTES:fail('recovery_capacity','Recovery store is full. Existing snapshots retained; use Save As for current work. No other session was removed.')
  try:
   with temporary.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
   failure=os.environ.get('ZERAWAVE_PROJECT_TEST_RECOVERY_FAILURE')
   if failure=='1' or failure and Path(failure).exists():raise OSError('Controlled recovery write failure before atomic publication')
   if target.exists()!=exists or exists and sha(target)!=expected:fail('recovery_changed','Recovery slot changed before replacement; external changes preserved.')
   os.replace(temporary,target)
  finally:
   try:temporary.unlink(missing_ok=True)
   except OSError:pass
 return dict(path=str(target),sha256=hashlib.sha256(raw).hexdigest(),epoch=epoch,revision=revision,bytes=len(raw),catalogue=catalogue(root),slot=slot)

def recover_copy(root,source,expected,destination,cancel):
 row,_=read_snapshot(root,source,expected);payload=deepcopy(row['project']);target=Path(destination).resolve()
 from project_export import protect
 protect(payload['document'],target,[row.get('original_path'),source],suffix='.zwv')
 if target.exists():fail('destination_exists','Recovery requires a new .zwv destination; existing projects were preserved.')
 raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf8');target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_name('.'+target.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  with temporary.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
  if cancel.is_set():fail('cancelled','Recovery copy cancelled before publication.')
  try:os.link(temporary,target)
  except FileExistsError:fail('destination_exists','Recovery destination appeared; its existing content was preserved.')
  return dict(path=str(target),revision=payload['revision'],sha256=hashlib.sha256(raw).hexdigest(),warnings=['Recovery metadata is durable; source media remains referenced externally. Reopen verifies sources and preserves missing references.'],snapshot=str(source))
 finally:
  try:temporary.unlink(missing_ok=True)
  except OSError:pass

class Recovery:
 def __init__(self,pool,root=None,clock=time.monotonic):
  self.pool=pool;self.root=Path(root or os.environ.get('ZERAWAVE_PROJECT_RECOVERY',str(Path(os.environ.get('ZERAWAVE_ARTWORK_STORE',str(Path(__file__).resolve().parents[2]/'work/artwork'))).parent/'video-recovery')));self.clock=clock;self.owner=uuid.uuid4().hex;self.future=pool.submit(catalogue,self.root);self.kind='catalogue';self.error='';self.entries=[];self.catalogue_errors=[];self.slots={};self.next_slot=0;self.last=None;self.latest=None;self.due=clock()+INTERVAL;self.changed=clock();self.current_identity=None;self.closing=False;self.close_offered=None;self.closed=False;self.version=0
 def observe(self,document,epoch,revision,saved_revision,path):
  identity=(epoch,revision)
  if identity!=self.current_identity:self.current_identity=identity;self.changed=self.clock()
  self.latest=(document,epoch,revision,saved_revision,path) if document is not None and revision!=saved_revision else None
 def poll(self):
  if self.future and self.future.done():
   try:
    result=self.future.result();self.error=''
    if self.kind=='write':self.last=result;self.slots[result['slot']]=result['sha256'];result=result['catalogue']
    self.entries=result['entries'];self.catalogue_errors=result['errors']
   except Exception as exc:self.error=str(exc)
   self.future=None;self.version+=1
  if not self.closed and not self.closing and self.latest and self.future is None and self.clock()>=self.due and (self.clock()-self.changed>=2 or self.clock()>=self.due+5):self.offer()
 def offer(self):
  if self.future or self.latest is None:return
  document,epoch,revision,saved_revision,path=self.latest
  if self.last and (self.last['epoch'],self.last['revision'])==(epoch,revision):self.due=self.clock()+INTERVAL;return
  slot=self.next_slot;self.next_slot=(slot+1)%4;self.kind='write';self.future=self.pool.submit(publish,self.root,self.owner,slot,self.slots.get(slot),deepcopy(document),epoch,revision,saved_revision,path);self.due=self.clock()+INTERVAL;self.version+=1
 def finish(self):
  self.poll();self.closing=True
  if self.future:return False
  identity=self.latest[1:3] if self.latest else None
  if identity is not None and identity!=self.close_offered:self.close_offered=identity;self.offer()
  return self.future is None
 def resume(self):self.closing=False;self.close_offered=None
 def refresh(self):
  if self.future is None:self.kind='catalogue';self.future=self.pool.submit(catalogue,self.root);self.version+=1
 def state(self):
  return dict(root=str(self.root),busy=self.future is not None,entries=deepcopy(self.entries),invalid_entries=deepcopy(self.catalogue_errors),last=deepcopy({k:v for k,v in self.last.items() if k!='catalogue'}) if self.last else None,error=self.error,latest_revision=self.current_identity[1] if self.current_identity else None,interval_seconds=INTERVAL,slots_per_owner=4,max_files=MAX_FILES,max_bytes=MAX_BYTES,meaning='Accepted metadata snapshots; external media is not copied. Project Save remains separate.')
