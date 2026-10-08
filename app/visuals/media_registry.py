"""Studio-owned local references and bounded, cancellable media validation.

No capture/output or graphics resources. Original files are never modified.
Worker results are committed only on the control-owner thread.
"""
from copy import deepcopy
from pathlib import Path
import json,os,queue,threading,uuid,time,math

KINDS={'Images':('.png','.jpg','.jpeg'),'Audio':('.wav','.mp3'),'Video':('.mp4','.mov','.mkv','.webm','.avi','.m4v'),'Animated':('.gif',),'Models':('.gltf','.glb')}
MAX_ASSETS=128
MAX_INTERNAL=4096 # Metadata only; pixels stay in bounded managed stores.
MAX_FILE_BYTES=128*1024*1024 # Image file limit; audio/video are streamed/referenced.
MAX_PIXELS=8*1024*1024
MAX_DIMENSION=8192
MAX_JOBS=16
MAX_RELINK_PATHS=8
MAX_REGISTRY_BYTES=8*1024*1024
from composition import PRESENTATIONS
LEGACY_PRESENTATIONS=('World + images','Image only')
LAYER_IDS=('image.layer1','image.layer2')

def normalized(path):return os.path.normcase(os.path.abspath(os.path.normpath(path)))
def text(value,label,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or '\0' in value:raise ValueError('Invalid '+label+'.')
    return value.strip()
def reference(data):
    if not isinstance(data,dict):raise ValueError('Invalid media reference.')
    identity=text(data.get('id'),'asset ID',32)
    if len(identity)!=32 or any(c not in '0123456789abcdef' for c in identity):raise ValueError('Invalid asset ID.')
    kind=data.get('kind');path=text(data.get('path'),'media path',1024)
    if kind not in KINDS or not Path(path).is_absolute():raise ValueError('Invalid media kind/path.')
    result=dict(id=identity,kind=kind,path=path,name=text(data.get('name'),'media name',128))
    if data.get('managed') is True:
        result.update(managed=True,provenance=text(data.get('provenance','Generated artwork'),'artwork provenance',512))
        # Migrate only known writer provenance, never infer ownership from names.
        if data.get('internal') is True or result['provenance'].startswith(('Editable drawing stroke','Transparent drawing child of ','Native extraction from ','Editable pixel clipboard','Editable frame snapshot')):result['internal']=True
    return result

def library_record(data):
    record=reference(data);previous=data.get('relinked_from',[])
    if not isinstance(previous,list) or len(previous)>MAX_RELINK_PATHS:raise ValueError('Invalid relink history.')
    for path in previous:
        text(path,'previous media path',1024)
        if not Path(path).is_absolute():raise ValueError('Invalid previous media path.')
    record['relinked_from']=list(dict.fromkeys(normalized(path) for path in previous))
    return record
def signature(path):
    stat=Path(path).stat()
    if not Path(path).is_file():raise ValueError('Media source is not a file.')
    return dict(bytes=stat.st_size,mtime_ns=stat.st_mtime_ns)
def check_cancel(cancel):
    if cancel.is_set():raise InterruptedError('Media operation cancelled.')

def decode_image(path,cancel=None,pixels=True,expected=None):
    """Qt PNG/JPEG decoding, EXIF orientation and tagged-color conversion.

    Returns vertically flipped premultiplied sRGB bytes for GL. Images beyond
    the bounds are rejected; no silent downscale. No persistent CPU image cache.
    """
    from PySide6.QtGui import QImageReader,QImage,QColorSpace
    cancel=cancel or threading.Event();check_cancel(cancel);before=signature(path)
    if expected is not None and before!=expected:raise ValueError('Image changed since validation; Refresh it in Media Library.')
    if before['bytes']>MAX_FILE_BYTES:raise ValueError('Image file exceeds 128 MiB; resize it externally.')
    QImageReader.setAllocationLimit(64)
    reader=QImageReader(str(path));reader.setAutoTransform(True)
    if bytes(reader.format()).lower() not in (b'png',b'jpeg',b'jpg'):raise ValueError('Only decoded PNG/JPEG images are supported.')
    size=reader.size();width,height=size.width(),size.height()
    if width<1 or height<1 or width>MAX_DIMENSION or height>MAX_DIMENSION or width*height>MAX_PIXELS:
        raise ValueError('Image exceeds 8192 pixels per side or 8,388,608 decoded pixels; resize it externally.')
    check_cancel(cancel);image=reader.read()
    if image.isNull():raise ValueError('Image decode failed: '+reader.errorString())
    if image.width()*image.height()>MAX_PIXELS:raise ValueError('Decoded image exceeds the pixel limit.')
    check_cancel(cancel)
    info=dict(width=image.width(),height=image.height(),alpha=image.hasAlphaChannel(),orientation='EXIF applied',color='sRGB; untagged sources assumed sRGB',**before)
    if pixels:
        color=image.colorSpace()
        if color.isValid():image=image.convertedToColorSpace(QColorSpace(QColorSpace.SRgb))
        image=image.convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True)
        check_cancel(cancel);data=bytes(image.constBits())
        if len(data)!=image.width()*image.height()*4:raise ValueError('Unexpected image row stride.')
    else:data=None
    check_cancel(cancel)
    if signature(path)!=before:raise ValueError('Image changed during decoding; retry after the file settles.')
    return info,data

def inspect(path,cancel):
    check_cancel(cancel);path=str(Path(text(path,'media path',1024)).resolve());suffix=Path(path).suffix.lower()
    kind=next((k for k,v in KINDS.items() if suffix in v),None)
    if kind is None:raise ValueError('Choose PNG/JPEG, WAV/MP3 or a supported video file reference.')
    meta=signature(path);check_cancel(cancel)
    if kind=='Images':meta,_=decode_image(path,cancel,pixels=False)
    elif kind=='Audio':
        from studio_transport import Decoder
        decoder=Decoder(path)
        try:
            check_cancel(cancel);block=decoder.read();check_cancel(cancel)
            if not len(block):raise ValueError('Audio decoder produced no samples.')
            meta.update(duration=decoder.duration,samplerate=decoder.rate,channels=decoder.channels,validation='Header and first decoded PCM block; later decode errors reported by Audio Hub')
        finally:decoder.close()
    elif kind in ('Video','Animated'):
        from media_frames import inspect_animation
        meta.update(inspect_animation(path,cancel))
    else:
        from model_layer import load_model
        meta.update(load_model(path,cancel)['metadata'])
    check_cancel(cancel)
    if {k:meta[k] for k in ('bytes','mtime_ns')}!=signature(path):raise ValueError('Media changed during validation; retry.')
    return dict(kind=kind,path=path,name=Path(path).stem[:128],metadata=meta,status='Ready',error='')

def legacy_defaults():
    return dict(version=1,presentation=LEGACY_PRESENTATIONS[0],assets=[],layers=[dict(id=identity,asset=None,enabled=False,order=i,opacity=1.,fit='Fit',x=0.,y=0.,scale=1.) for i,identity in enumerate(LAYER_IDS)])
def legacy_validate_scene(data):
    if data is None:return legacy_defaults()
    if not isinstance(data,dict) or data.get('version')!=1 or data.get('presentation') not in LEGACY_PRESENTATIONS:raise ValueError('Invalid image-layer scene.')
    assets=data.get('assets');layers=data.get('layers')
    if not isinstance(assets,list) or len(assets)>2 or not isinstance(layers,list) or len(layers)!=2:raise ValueError('Invalid media scene bounds.')
    assets=[reference(row) for row in assets];ids={row['id'] for row in assets}
    if len(ids)!=len(assets):raise ValueError('Duplicate session asset IDs.')
    if len({normalized(row['path']) for row in assets})!=len(assets):raise ValueError('Duplicate session media paths.')
    clean=[]
    for row in layers:
        if not isinstance(row,dict) or row.get('id') not in LAYER_IDS or type(row.get('enabled')) is not bool or type(row.get('order')) is not int or row['order'] not in (0,1) or row.get('fit') not in ('Fit','Fill'):raise ValueError('Invalid image layer.')
        asset=row.get('asset')
        if asset is not None and (asset not in ids or next(a for a in assets if a['id']==asset)['kind']!='Images'):raise ValueError('Image layer needs its own saved image reference.')
        out=dict(id=row['id'],asset=asset,enabled=row['enabled'],order=row['order'],fit=row['fit'])
        for key,lo,hi in (('opacity',0.,1.),('scale',.1,4.),('x',-1.,1.),('y',-1.,1.)):
            value=row.get(key)
            if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:raise ValueError('Invalid image '+key+'.')
            out[key]=float(value)
        clean.append(out)
    if {row['id'] for row in clean}!=set(LAYER_IDS) or len({row['order'] for row in clean})!=2:raise ValueError('Image layer IDs/order must be unique.')
    clean.sort(key=lambda row:LAYER_IDS.index(row['id']))
    return dict(version=1,presentation=data['presentation'],assets=assets,layers=clean)

class MediaRegistry:
    def __init__(self,path):
        self.path=Path(path);self.assets={};self.collections={};self.pending={};self.jobs=queue.Queue(MAX_JOBS);self.results=queue.Queue(MAX_JOBS+1)
        self.required_internal=set()
        self.lock=threading.Lock();self.save_pending=None;self.closed=threading.Event();self.epoch=0;self.revision=0;self.error='';self.loading=True;self.import_results=[]
        self.submit('read');self.worker=threading.Thread(target=self.run,name='Studio media validation',daemon=True);self.worker.start()
    def submit(self,op,path=None,asset=None):
        if self.closed.is_set():raise ValueError('Media Library is closed.')
        if len(self.pending)>=MAX_JOBS:raise ValueError('Media Library is busy; wait or cancel pending imports.')
        token=uuid.uuid4().hex;cancel=threading.Event();job=dict(token=token,epoch=self.epoch,op=op,path=path,asset=asset,cancel=cancel)
        if asset is not None and asset not in self.assets:raise ValueError('Media asset no longer exists.')
        if asset is not None:job['original']=deepcopy(self.assets[asset])
        try:self.jobs.put_nowait(job)
        except queue.Full:raise ValueError('Media validation queue is draining cancelled work; retry shortly.')
        self.pending[token]=job
        if op=='import':self.import_results=[r for r in self.import_results if normalized(r['path'])!=normalized(path)]
        return token
    def imported(self,job,status,error='',asset=None):
        if job['op']=='import':
            collection=job.get('collection')
            if status in ('Ready','Duplicate') and collection in self.collections and asset in self.assets:self.collection('add',collection,asset=asset)
            self.import_results.append(dict(token=job['token'],path=job['path'],status=status,error=error,asset=asset));self.import_results=self.import_results[-64:]
    def cancel(self,token=None):
        for key,job in list(self.pending.items()):
            if (token is None or key==token) and (job['op']!='read' or self.closed.is_set()):job['cancel'].set();self.pending.pop(key,None);self.imported(job,'Cancelled','Import cancelled.')
    def schedule_save(self):
        with self.lock:self.save_pending=dict(version=2,assets=[library_record(a) for a in self.assets.values()],collections=deepcopy(self.collections))
    def deliver(self,result):
        while not self.closed.is_set():
            try:self.results.put(result,timeout=.05);return
            except queue.Full:pass
    def run(self):
        while not self.closed.is_set():
            try:job=self.jobs.get(timeout=.05)
            except queue.Empty:job=None
            if job is not None:
                try:
                    check_cancel(job['cancel'])
                    if job['op']=='read':
                        if self.path.exists():
                            if self.path.stat().st_size>MAX_REGISTRY_BYTES:raise ValueError('Media registry exceeds 8 MiB.')
                            saved=json.loads(self.path.read_text(encoding='utf-8'))
                            if saved.get('version') not in (1,2) or not isinstance(saved.get('assets'),list) or len(saved['assets'])>MAX_ASSETS+MAX_INTERNAL:raise ValueError('Unsupported or oversized Media Library.')
                            rows=[library_record(a) for a in saved['assets']]
                            if sum(not a.get('internal') for a in rows)>MAX_ASSETS or sum(bool(a.get('internal')) for a in rows)>MAX_INTERNAL:raise ValueError('Library resource bounds exceeded.')
                            public=[a for a in rows if not a.get('internal')]
                            if len({a['id'] for a in rows})!=len(rows) or len({normalized(a['path']) for a in public})!=len(public):raise ValueError('Duplicate library identity/path.')
                            collections=validate_collections(saved.get('collections',{}),{a['id'] for a in rows})
                        else:rows=[];collections={}
                        value=(rows,collections)
                    else:value=inspect(job['path'],job['cancel'])
                    result=dict(job=job,value=value)
                except Exception as exc:result=dict(job=job,error=str(exc)[:240],missing=isinstance(exc,FileNotFoundError))
                self.deliver(result)
            with self.lock:save,self.save_pending=self.save_pending,None
            if save is not None:
                try:
                    self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.media-tmp')
                    tmp.write_text(json.dumps(save,indent=2),encoding='utf-8');os.replace(tmp,self.path)
                except OSError as exc:
                    self.deliver(dict(save_error='Library save failed: '+str(exc)[:180]))
        # Flush the last explicit library edit on orderly shutdown.
        with self.lock:save=self.save_pending;self.save_pending=None
        if save is not None:
            try:
                self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.media-tmp');tmp.write_text(json.dumps(save,indent=2),encoding='utf-8');os.replace(tmp,self.path)
            except OSError as exc:self.error='Library save failed: '+str(exc)[:180]
    def poll(self):
        changed=False
        for _ in range(MAX_JOBS+1):
            try:result=self.results.get_nowait()
            except queue.Empty:break
            if 'save_error' in result:self.error=result['save_error'];continue
            job=result['job'];token=job['token']
            if token not in self.pending or job['epoch']!=self.epoch or job['cancel'].is_set():continue
            self.pending.pop(token,None);asset=job.get('asset');error=result.get('error')
            if asset is not None and self.assets.get(asset)!=job['original']:continue
            if job['op']=='read':
                self.loading=False
                if error:self.error='Library unavailable: '+error
                else:
                    rows,self.collections=result['value'];self.assets={row['id']:dict(row,status='Unchecked',metadata={},error='') for row in rows};changed=True
                continue
            if error:
                self.error=error
                self.imported(job,'Failed',error)
                if job['op']=='validate' and asset in self.assets:self.assets[asset].update(status='Missing' if result.get('missing') else 'Invalid',error=error);changed=True
                continue
            value=result['value'];duplicate=next((a for a in self.assets.values() if not a.get('internal') and normalized(a['path'])==normalized(value['path']) and a['id']!=asset),None)
            if asset is not None and self.assets[asset].get('internal'):duplicate=None
            if duplicate is not None:self.error='Already in Media Library: '+duplicate['name'];self.imported(job,'Duplicate',self.error,duplicate['id']);continue
            if asset is not None:
                if value['kind']!=self.assets[asset]['kind']:self.error='Relink must retain the asset kind.';continue
                previous=self.assets[asset].get('relinked_from',[])
                if job['op']=='relink' and normalized(value['path'])!=normalized(self.assets[asset]['path']):previous=(previous+[normalized(self.assets[asset]['path'])])[-MAX_RELINK_PATHS:]
                value['relinked_from']=previous
                if self.assets[asset].get('managed'):
                    value.update(reference(self.assets[asset]),path=value['path'])
                value.update(id=asset,name=self.assets[asset]['name']);self.assets[asset]=value
            else:
                if sum(not a.get('internal') for a in self.assets.values())>=MAX_ASSETS:self.error='Media Library is limited to 128 references.';self.imported(job,'Failed',self.error);continue
                value['id']=uuid.uuid4().hex;self.assets[value['id']]=value
            self.imported(job,'Ready',asset=value['id'])
            self.error='';changed=True;self.schedule_save()
        busy={j.get('asset') for j in self.pending.values()}
        for row in self.assets.values():
            if row.get('internal') and row['id'] not in self.required_internal:continue
            if row['status']=='Unchecked' and row['id'] not in busy and len(self.pending)<MAX_JOBS:
                try:self.submit('validate',row['path'],row['id'])
                except ValueError:break # cancelled jobs may still occupy the bounded queue
        if changed:self.revision+=1
        return changed
    def rename(self,asset,name):
        self.assets[asset]['name']=text(name,'display name',128);self.revision+=1;self.schedule_save()
    def remove(self,asset,*,cancel_pending=True):
        if asset not in self.assets:raise ValueError('Media asset no longer exists.')
        for token,job in list(self.pending.items()):
            if cancel_pending and job.get('asset')==asset:self.cancel(token)
        self.assets.pop(asset)
        for collection in self.collections.values():collection['assets']=[a for a in collection['assets'] if a!=asset]
        self.revision+=1;self.schedule_save()
    def restore_refs(self,refs,*,apply=True,cancel_pending=True):
        refs=[reference(a) for a in refs]
        if self.loading:raise ValueError('Wait for Media Library loading before reopening a media session.')
        additions=[];relocations=[]
        for row in refs:
            current=self.assets.get(row['id']);duplicate=next((a for a in self.assets.values() if not a.get('internal') and normalized(a['path'])==normalized(row['path']) and a['id']!=row['id']),None)
            explicitly_relinked=current is not None and normalized(row['path']) in current.get('relinked_from',[])
            if current and row.get('managed') and current.get('managed') and normalized(row['path'])!=normalized(current['path']):
                import hashlib
                old=Path(current['path']);new=Path(row['path'])
                if old.is_file() and new.is_file() and hashlib.sha256(old.read_bytes()).digest()==hashlib.sha256(new.read_bytes()).digest():explicitly_relinked=True;relocations.append((current,row))
            if current and (current['kind']!=row['kind'] or normalized(current['path'])!=normalized(row['path']) and not explicitly_relinked):raise ValueError('Session asset identity conflicts with the library; resolve the reference explicitly.')
            if duplicate and not explicitly_relinked and not row.get('internal'):raise ValueError('Session path belongs to a different asset ID; resolve the reference explicitly.')
            if current is None:additions.append(dict(row,status='Unchecked',metadata={},error=''))
        combined=list(self.assets.values())+additions
        if sum(not a.get('internal') for a in combined)>MAX_ASSETS or sum(bool(a.get('internal')) for a in combined)>MAX_INTERNAL:raise ValueError('Session would exceed library/internal resource bounds.')
        if not apply:return
        self.required_internal.update(row['id'] for row in refs if row.get('internal'))
        if not additions and not relocations:return
        if cancel_pending:self.cancel();self.epoch+=1
        for current,row in relocations:
            current['relinked_from']=(current.get('relinked_from',[])+[normalized(current['path'])])[-MAX_RELINK_PATHS:];current['path']=row['path'];current.update(status='Unchecked',metadata={},error='')
        for row in additions:self.assets[row['id']]=row
        if additions or relocations:self.revision+=1;self.schedule_save()
    def snapshot(self,internal_ids=()):
        # Relink provenance is registry-local, not repeated in GUI snapshots.
        self.required_internal=set(internal_ids)
        rows=[{key:value for key,value in row.items() if key!='relinked_from'} for row in self.assets.values()]
        assets=[a for a in rows if not a.get('internal')];resources=[a for a in rows if a.get('internal') and a['id'] in internal_ids]
        return dict(version=2,revision=self.revision,assets=assets,resources=resources,collections=deepcopy(self.collections),loading=self.loading,error=self.error,
            import_results=deepcopy(self.import_results),pending=[dict(token=t,op=j['op'],path=j.get('path'),asset=j.get('asset')) for t,j in self.pending.items()])
    def close(self):
        self.closed.set();self.cancel();self.worker.join(timeout=2.)
        return not self.worker.is_alive()

    def collection(self,op,identity=None,name=None,asset=None):
        if op=='create':
            if len(self.collections)>=32:raise ValueError('At most 32 collections.')
            identity=uuid.uuid4().hex;self.collections[identity]=dict(name=text(name,'collection name',128),assets=[])
        elif identity not in self.collections:raise ValueError('Collection no longer exists.')
        elif op=='rename':self.collections[identity]['name']=text(name,'collection name',128)
        elif op=='delete':self.collections.pop(identity)
        elif op in ('add','remove'):
            if asset not in self.assets:raise ValueError('Asset no longer exists.')
            members=self.collections[identity]['assets']
            if op=='add' and asset not in members:members.append(asset)
            if op=='remove' and asset in members:members.remove(asset)
        else:raise ValueError('Unsupported collection action.')
        self.revision+=1;self.schedule_save();return identity

def validate_collections(data,assets):
    if not isinstance(data,dict) or len(data)>32:raise ValueError('Invalid collection bounds.')
    clean={}
    for identity,row in data.items():
        text(identity,'collection ID',32)
        if not isinstance(row,dict) or not isinstance(row.get('assets'),list) or len(row['assets'])>MAX_ASSETS or any(a not in assets for a in row['assets']):raise ValueError('Invalid collection membership.')
        clean[identity]=dict(name=text(row.get('name'),'collection name',128),assets=list(dict.fromkeys(row['assets'])))
    return clean

from composition import defaults,validate_scene
