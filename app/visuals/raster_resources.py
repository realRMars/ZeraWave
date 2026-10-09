"""B1 immutable pixel leases, bounded persistence and revision-pinned saves.

ControlOwner is the document authority. These are resources, not another model.
Windows mappings survive while any owner/reader handle is open. Writers never
modify a submitted mapping; readers copy under an open lease before closing it.
"""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
import hashlib,json,os,time,uuid,mmap

MAX_BYTES=384*1024*1024
MAX_MAPPING_BYTES=512*1024*1024
MAX_RESOURCES=256
MAX_JOBS=16
MAX_JOB_BYTES=256*1024*1024

def validate(desc):
    if isinstance(desc,dict) and desc.get('layout')=='tiles128-v1':
        from raster_tiles import validate as tiles_validate
        return tiles_validate(desc)
    if not isinstance(desc,dict):raise ValueError('Missing raster descriptor.')
    w,h=desc.get('width'),desc.get('height')
    if type(w) is not int or type(h) is not int or min(w,h)<1 or max(w,h)>8192 or w*h>8388608:raise ValueError('Raster exceeds native pixel limits.')
    if desc.get('stride')!=w*4 or desc.get('bytes')!=w*h*4:raise ValueError('Invalid raster stride/length.')
    if (desc.get('format'),desc.get('orientation'),desc.get('alpha'),desc.get('color'))!=('RGBA8','bottom-up','premultiplied','sRGB'):raise ValueError('Unsupported raster interpretation.')
    name=desc.get('name')
    if not isinstance(name,str) or not name.startswith('zw_raster_') or len(name)>64:raise ValueError('Invalid raster mapping identity.')
    return desc

def snapshot(image):
    """Producer lease; allocation/copy failure occurs before owner admission."""
    from native_raster import NativeImage
    if isinstance(image,NativeImage):
        from raster_tiles import export
        return export(image)
    from PySide6.QtGui import QImage
    if image.isNull():raise ValueError('Cannot snapshot empty pixels.')
    desc=dict(width=image.width(),height=image.height(),stride=image.width()*4,bytes=image.width()*image.height()*4,
              format='RGBA8',orientation='bottom-up',alpha='premultiplied',color='sRGB',name='zw_raster_'+uuid.uuid4().hex)
    validate(desc)
    native=image.convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True)
    if native.isNull():raise MemoryError('Cannot allocate immutable raster snapshot.')
    lease=SharedMemory(name=desc['name'],create=True,size=desc['bytes'])
    try:lease.buf[:desc['bytes']]=native.constBits()
    except BaseException:release(lease);raise
    return desc,lease

def release(lease):
    lease.close()
    try:lease.unlink()
    except FileNotFoundError:pass

def read(desc):
    if desc.get('layout')=='tiles128-v1':
        from raster_tiles import read as tiles_read
        return tiles_read(desc)
    validate(desc);lease=SharedMemory(name=desc['name'])
    try:
        if not desc['bytes']<=lease.size<=((desc['bytes']+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE:raise ValueError('Raster mapping length changed.')
        return dict(width=desc['width'],height=desc['height']),bytes(lease.buf[:desc['bytes']])
    finally:lease.close()

def image(desc):
    if desc.get('layout')=='tiles128-v1':
        from raster_tiles import image as tiles_image
        return tiles_image(desc)
    from PySide6.QtGui import QImage
    meta,data=read(desc)
    return QImage(data,meta['width'],meta['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied)

class Resources:
    def __init__(self,folder=None):
        self.folder=Path(folder or os.environ.get('ZERAWAVE_ARTWORK_STORE') or Path(__file__).resolve().parents[2]/'work/studio/artwork')
        self.rows={};self.leases={};self.jobs={};self.failures={};self.saves={};self.save_jobs={};self.save_pins={}
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Owner PNG persistence')
        self.save_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Revision-pinned session save')
        self.barrier=None # controlled fixture hook; never set by production
    def admit(self,assets):
        """All-or-nothing admission. No registry disk inspection or PNG decode."""
        assets=deepcopy(assets);new={};leases={}
        if len(assets)>MAX_JOBS:raise ValueError('Too many raster resources in one operation.')
        if len(self.rows)+len(assets)>MAX_RESOURCES:raise ValueError('256 raster resources retained; secure/release recovery checkpoints before another edit')
        from raster_tiles import unique_bytes,mapping_bytes,TileLease,tiled
        retained=[row['runtime'] for row in self.rows.values()]
        queued=[self.rows[k]['runtime'] for k,j in self.jobs.items() if not j.done()]
        if len([j for j in self.jobs.values() if not j.done()])+len(assets)>MAX_JOBS:raise ValueError('Raster persistence queue full; edit not accepted. Retry or Save As.')
        try:
            for asset in assets:
                from media_registry import reference
                ref=reference(asset);identity=ref['id'];desc=validate(asset.get('runtime'))
                if identity in self.rows:raise ValueError('Raster resource ID already exists.')
                source=asset.get('source_snapshot') is True
                if ref['kind']!='Images' or not ref.get('managed') and not source:raise ValueError('Runtime resources must be managed rasters or validated source leases.')
                # The producer cannot nominate a filesystem write destination.
                if not source:ref['path']=str((self.folder/(identity+'.png')).resolve())
                retained.append(desc)
                if not source:queued.append(desc)
                if unique_bytes(retained)>MAX_BYTES or mapping_bytes(retained)>MAX_MAPPING_BYTES or unique_bytes(queued)>MAX_JOB_BYTES:raise ValueError('Raster resource/queue byte limit; edit not accepted. Save/retry after pending work.')
                lease=TileLease(desc) if tiled(desc) else SharedMemory(name=desc['name']);leases[identity]=lease
                if not tiled(desc) and not desc['bytes']<=lease.size<=((desc['bytes']+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE:raise ValueError('Invalid raster mapping allocation.')
                metadata=deepcopy(asset['metadata']) if source else dict(width=desc['width'],height=desc['height'],bytes=desc['bytes'],mtime_ns=0,pixel_aspect=1,alpha=True,color='sRGB')
                new[identity]=dict(ref,runtime=desc,status='Ready',error='',durability='durable' if source else 'pending',source_snapshot=source,metadata=metadata)
        except BaseException:
            for lease in leases.values():lease.close()
            raise
        self.rows.update(new);self.leases.update(leases);return new
    def reject(self,ids):
        for key in ids:
            self.rows.pop(key,None)
            if key in self.leases:release(self.leases.pop(key))
    def retire(self):
        """Move old-context lease handles out of current asset-ID resolution.

        Stored asset IDs remain stable. Private retention keys distinguish old
        write/save readers from a newly loaded reference with that same ID.
        """
        mapping={k:uuid.uuid4().hex for k,r in self.rows.items() if not r.get('retired')}
        for old,key in mapping.items():
            row=self.rows.pop(old);row['retired']=True;self.rows[key]=row
            self.leases[key]=self.leases.pop(old)
            if old in self.jobs:self.jobs[key]=self.jobs.pop(old)
            if old in self.failures:self.failures[key]=self.failures.pop(old)
        for key,pins in self.save_pins.items():self.save_pins[key]={mapping.get(k,k) for k in pins}
        for out in self.saves.values():out['resource_keys']={k:mapping.get(v,v) for k,v in out.get('resource_keys',{}).items()}
        return mapping
    def persist(self,identity):
        row=deepcopy(self.rows[identity])
        def write():
            if self.barrier is not None:self.barrier.wait()
            barrier=os.environ.get('ZERAWAVE_RASTER_TEST_BARRIER')
            while barrier and Path(barrier).exists():time.sleep(.01)
            failure=os.environ.get('ZERAWAVE_RASTER_TEST_FAIL_WRITE')
            if failure and Path(failure).exists():raise OSError('Injected isolated PNG write failure')
            from artwork import MAX_STORE
            from PySide6.QtCore import QBuffer,QIODevice
            pixels=image(row['runtime']);buffer=QBuffer();buffer.open(QIODevice.WriteOnly)
            if not pixels.save(buffer,'PNG'):raise ValueError('PNG encoding failed; accepted pixels retained.')
            data=bytes(buffer.data());folder=Path(row['path']).parent;folder.mkdir(parents=True,exist_ok=True)
            target=Path(row['path'])
            if sum(p.stat().st_size for p in folder.glob('*.png'))+len(data)>MAX_STORE:raise ValueError('Artwork store reached 512 MiB; use Save As/recovery export.')
            temporary=target.with_suffix('.'+uuid.uuid4().hex+'.tmp')
            try:temporary.write_bytes(data);os.replace(temporary,target)
            finally:
                if temporary.exists():temporary.unlink()
            return dict(path=str(target),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),finished=time.perf_counter())
        self.jobs[identity]=self.pool.submit(write)
    def poll(self):
        for key,job in list(self.jobs.items()):
            if not job.done() or getattr(job,'reported',False):continue
            job.reported=True
            try:
                info=job.result();self.rows[key]['durability']='durable';self.rows[key]['persisted']=info;self.rows[key]['error']='';self.failures.pop(key,None)
            except Exception as exc:self.rows[key]['durability']='failed';self.rows[key]['error']=str(exc)[:240];self.failures[key]=str(exc)[:240]
        for key,job in list(self.save_jobs.items()):
            if not job.done() or getattr(job,'reported',False):continue
            job.reported=True;out=self.saves[key]
            try:out.update(status='durable',**job.result())
            except Exception as exc:out.update(status='failed',error=str(exc)[:240])
            # Failed recovery snapshots remain pinned and can be retried/exported.
            if out['status']=='durable':
                self.save_pins.pop(key,None)
                out.pop('values',None)
                for identity,path in out.get('recovered',{}).items():
                    resource=out['resource_keys'].get(identity,identity)
                    if resource in self.rows:
                        self.rows[resource].update(durability='secured',error='',recovery_path=path)
                        self.failures.pop(resource,None)
    def save(self,key,values,drafts,path,session,revision,resource_keys=None):
        if key in self.saves:return self.saves[key]
        if sum(not j.done() for j in self.save_jobs.values())>=4 or len(self.save_pins)>=4:raise ValueError('Four save/recovery checkpoints retained; retry/export failed checkpoints first.')
        values=deepcopy(values);drafts=deepcopy(drafts);destination=Path(path)
        refs={a['id'] for a in values['media']['assets']};keys=resource_keys if resource_keys is not None else {k:k for k in refs if k in self.rows}
        rows={k:deepcopy(self.rows[v]) for k,v in keys.items() if v in self.rows and not self.rows[v].get('source_snapshot')};waits={k:self.jobs.get(keys[k]) for k in rows}
        outcome=dict(id=key,session=session,revision=revision,path=str(destination),status='pending',error='',requested=time.perf_counter(),values_sha256=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest(),values=deepcopy(values),drafts=deepcopy(drafts),resource_keys=dict(keys))
        self.saves[key]=outcome;self.save_pins[key]=set(keys.values())
        def secure():
            from artwork import portable_scene,store_image
            # A Save As can recover a failed working-store write directly to its
            # own dependency folder. The working revision/resource never changes.
            recovered={}
            for k,row in rows.items():
                job=waits[k]
                try:
                    if job is not None:job.result()
                    if not Path(row['path']).is_file():raise OSError('Dependency not persisted.')
                except Exception:
                    record=store_image(image(row['runtime']),row['provenance'],destination.with_suffix('.assets'))
                    recovered[k]=record['path']
                    for ref in values['media']['assets']:
                        if ref['id']==k:ref['path']=record['path']
            values['media']=portable_scene(values['media'],destination)
            if values['media'].get('canvas') is None:values['media']['canvas']=[1280,720]
            saved=dict(version=5,**values,qt_tuning_drafts=drafts,b1_saved_revision=dict(session=session,revision=revision))
            destination.parent.mkdir(parents=True,exist_ok=True);temporary=destination.with_suffix('.'+uuid.uuid4().hex+'.tmp')
            try:temporary.write_text(json.dumps(saved,indent=2),encoding='utf8');os.replace(temporary,destination)
            finally:
                if temporary.exists():temporary.unlink()
            return dict(finished=time.perf_counter(),recovered=recovered)
        try:self.save_jobs[key]=self.save_pool.submit(secure)
        except Exception as exc:outcome.update(status='failed',error='Save worker unavailable: '+str(exc)[:200])
        # Only four full value snapshots are retained; terminal outcome metadata
        # is bounded independently from failed-checkpoint resource pins.
        for old in list(self.saves)[:-16]:
            if old not in self.save_pins:self.saves.pop(old,None);self.save_jobs.pop(old,None)
        return outcome
    def retry_save(self,key,path=None):
        prior=self.saves.get(key)
        if not prior or prior['status']!='failed':raise ValueError('No failed checkpoint to retry.')
        # Transfer its existing resource pin into the new retry reservation.
        pins=self.save_pins.pop(key,None)
        try:
            outcome=self.save(uuid.uuid4().hex,prior['values'],prior['drafts'],path or prior['path'],prior['session'],prior['revision'],prior['resource_keys'])
            prior.update(status='retried',retry_id=outcome['id']);prior.pop('values',None);prior.pop('drafts',None)
            return outcome
        except BaseException:
            if pins is not None:self.save_pins[key]=pins
            raise
    def retain(self,ids):
        pinned=set(ids)|set(self.failures)|set().union(*self.save_pins.values()) if self.save_pins else set(ids)|set(self.failures)
        pinned.update(k for k,j in self.jobs.items() if not j.done())
        for key in set(self.rows)-pinned:
            self.rows.pop(key);release(self.leases.pop(key));self.jobs.pop(key,None)
    def history_bytes(self,ids,sizes):
        from raster_tiles import unique_bytes
        return unique_bytes(self.rows[k]['runtime'] for k in ids if k in self.rows)+sum(sizes.get(k,0) for k in ids if k not in self.rows)
    def state(self):
        from native_raster import backend
        from raster_tiles import unique_bytes,mapping_bytes
        selection=backend();native=selection.core.stats() if selection.core else {}
        return dict(mapping_bytes=mapping_bytes(r['runtime'] for r in self.rows.values()),mapping_limit=MAX_MAPPING_BYTES,resource_count=len(self.rows),resource_limit=MAX_RESOURCES,backend=selection.status(),native=native,logical_bytes=sum(r['runtime']['bytes'] for r in self.rows.values()),bytes=unique_bytes(r['runtime'] for r in self.rows.values()),limit=MAX_BYTES,pending=sum(not j.done() for j in self.jobs.values()),retained_checkpoints=len(self.save_pins),failures=deepcopy(self.failures),resources={k:r['durability'] for k,r in self.rows.items()},saves=[{k:v for k,v in out.items() if k not in ('values','saved_values','drafts')} for out in self.saves.values()])
    def close(self):
        self.pool.shutdown(wait=True);self.save_pool.shutdown(wait=True)
        for lease in self.leases.values():release(lease)
        self.leases.clear()

class Outcomes:
    """Bounded duplicate ledger; evicted sequence IDs cannot be re-applied."""
    def __init__(self):self.rows=OrderedDict();self.sequence=0;self.stream=None
    def begin(self,name,data):
        op=data.get('operation_id');stream=data.get('operation_stream');seq=data.get('operation_sequence')
        if not isinstance(op,str) or len(op)!=32 or type(seq) is not int or not isinstance(stream,str) or len(stream)!=32:raise ValueError('Invalid ordered operation identity.')
        fingerprint=hashlib.sha256(json.dumps([name,data],sort_keys=True).encode()).hexdigest()
        if op in self.rows:
            row=self.rows[op]
            if row['fingerprint']!=fingerprint:raise ValueError('Operation ID reused with different content.')
            if row['status']=='rejected':raise ValueError(row['error'])
            return False
        if self.stream is not None and stream!=self.stream:raise ValueError('Operation stream changed.')
        if seq!=self.sequence+1:raise ValueError('Out-of-order or expired operation; reconcile before resubmission.')
        self.stream=stream;self.sequence=seq
        self.rows[op]=dict(id=op,fingerprint=fingerprint,status='submitted',resources=[],submitted=time.perf_counter())
        while len(self.rows)>256:self.rows.popitem(last=False)
        return True
    def finish(self,data,**fields):self.rows[data['operation_id']].update(fields)
    def state(self):return [{k:v for k,v in row.items() if k!='fingerprint'} for row in self.rows.values()]
