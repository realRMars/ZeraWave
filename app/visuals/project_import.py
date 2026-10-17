"""Mixed Project Media preparation on the existing owner's bounded pool.

Worker owns only verified temporary recipes/progress; owner alone commits/history.
No registry, output device, graphics context or additional worker pool.
"""
from pathlib import Path
from copy import deepcopy
from collections import Counter
import os,threading,uuid

class Progress:
 def __init__(self):self.lock=threading.Lock();self.latest=None
 def publish(self,rows):
  with self.lock:self.latest=deepcopy(rows) # one bounded latest snapshot, no queue
 def take(self):
  with self.lock:value=self.latest;self.latest=None;return value

class ImportFailure(ValueError):
 def __init__(self,message,files,code='import_failed'):super().__init__(message);self.files=deepcopy(files);self.code=code

def normalized(path):return os.path.normcase(str(Path(path).resolve()))

def finish(rows,accepted,cancelled=False):
 result=deepcopy(rows)
 for row in result:
  status=row['status']
  if accepted:row['status']={'verified':'accepted','reuse_planned':'reused','duplicate_planned':'skipped'}.get(status,status)
  elif status not in ('failed','cancelled'):row['status']='retained' if status=='reuse_planned' else 'cancelled' if cancelled else 'not_accepted'
 return result

def counts(rows):return dict(Counter(r['status'] for r in rows))

def prepare(paths,document,states,base,operation,cancel,progress):
 from project_service import prepare_changes
 from media_registry import KINDS
 rows=[dict(index=i,path=p,name=Path(p).name[:256],status='queued') for i,p in enumerate(paths)];changes=[];seen={};progress.publish(rows)
 for i,path in enumerate(paths):
  try:
   if cancel.is_set():raise InterruptedError('Project import cancelled before acceptance.')
   rows[i]['status']='preparing';progress.publish(rows);normal=normalized(path);suffix=Path(path).suffix.lower();kind=next(({'Images':'Image','Video':'Video','Audio':'Audio'}.get(k) for k,values in KINDS.items() if suffix in values),None)
   if kind is None:raise ImportFailure('Unsupported Project Media type: '+Path(path).name,rows,'unsupported_media')
   existing=next((a for a in document['media'] if normal in {normalized(p) for p in (a['location']['path'],a.get('provenance',{}).get('import_path'),a.get('provenance',{}).get('original_path')) if p}),None)
   if existing and states.get(existing['id'],{}).get('status')!='Ready':raise ImportFailure('Recorded source is unavailable; Relink it deliberately: '+existing['name'],rows,'missing_media')
   change=dict(op='media.add',id=uuid.uuid5(uuid.UUID(operation),str(i)).hex,name=Path(path).stem[:256],kind=kind,location=dict(kind='external',path=path),provenance={})
   if existing:change['sha256']=existing['sha256']
   prepared=prepare_changes([change],base,cancel)[0]
   if cancel.is_set():raise InterruptedError('Project import cancelled before acceptance.')
   if normal in seen:
    prior=seen[normal]
    if prior['sha256']!=prepared['sha256']:raise ImportFailure('Source changed within this import group.',rows,'changed_media')
    asset_id=prior['id'];status='duplicate_planned'
   elif existing:
    if existing['kind']!=prepared['kind']:raise ImportFailure('Recorded type changed; Relink deliberately.',rows,'changed_media')
    asset_id=existing['id'];status='reuse_planned'
   else:changes.append(prepared);asset_id=prepared['id'];status='verified'
   seen[normal]=dict(id=asset_id,sha256=prepared['sha256']);rows[i].update(status=status,asset_id=asset_id,sha256=prepared['sha256'],kind=prepared['kind']);progress.publish(rows)
  except BaseException as exc:
   cancelled=isinstance(exc,InterruptedError);rows[i].update(status='cancelled' if cancelled else 'failed',error=str(exc)[:512]);rows=finish(rows,False,cancelled);progress.publish(rows);raise ImportFailure(str(exc),rows,'cancelled' if cancelled else getattr(exc,'code','import_failed')) from exc
 return dict(changes=changes,files=rows)
