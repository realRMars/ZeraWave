"""B1 immutable pixel leases, bounded persistence and revision-pinned saves.

ControlOwner is the document authority. These are resources, not another model.
Windows mappings survive while any owner/reader handle is open. Writers never
modify a submitted mapping; readers copy under an open lease before closing it.
"""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, CancelledError
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

def read(desc,lease=None):
    if desc.get('layout')=='tiles128-v1':
        from raster_tiles import read as tiles_read
        return tiles_read(desc,lease=lease)
    validate(desc);owned=lease is None;lease=SharedMemory(name=desc['name']) if owned else lease
    try:
        if not desc['bytes']<=lease.size<=((desc['bytes']+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE:raise ValueError('Raster mapping length changed.')
        return dict(width=desc['width'],height=desc['height']),bytes(lease.buf[:desc['bytes']])
    finally:
        if owned:lease.close()

def image(desc,native=True,lease=None):
    if desc.get('layout')=='tiles128-v1':
        from raster_tiles import image as tiles_image
        return tiles_image(desc,native=native,lease=lease)
    from PySide6.QtGui import QImage
    meta,data=read(desc,lease=lease)
    return QImage(data,meta['width'],meta['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied)

def forget_traceback(exc):
    # Futures must keep the failure outcome for Save/Retry, not the worker's
    # pixel/mapping locals. Preserve the exception type and message.
    seen=set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc));exc.__traceback__=None
        next_exc=exc.__cause__ or exc.__context__;exc.__cause__=None;exc.__context__=None;exc=next_exc

class _MappingReader:
    """One resource's reference to an immutable owner mapping."""
    def __init__(self,pool,name):self.pool=pool;self.name=name;self.closed=False
    @property
    def buf(self):return self.pool.rows[self.name][0].buf
    @property
    def size(self):return self.pool.rows[self.name][0].size
    def close(self):
        if not self.closed:self.pool.release(self.name);self.closed=True

class _MappingPool:
    """Owner-only shared handles; jobs/saves pin the resource that borrows them."""
    def __init__(self):self.rows={}
    def acquire(self,tile):
        name=tile['name'];row=self.rows.get(name)
        if row is None:
            handle=SharedMemory(name=name)
            if not tile['bytes']<=handle.size<=((tile['bytes']+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE:
                handle.close();raise ValueError('Tile mapping allocation length changed')
            row=[handle,0];self.rows[name]=row
        row[1]+=1;return _MappingReader(self,name)
    def release(self,name):
        row=self.rows[name]
        if row[1]==1:
            # If a foreign exported buffer blocks closure, preserve ownership
            # and the original handle so a later safe close can be retried.
            row[0].close();self.rows.pop(name)
        else:row[1]-=1

class Resources:
    def __init__(self,folder=None):
        self.folder=Path(folder or os.environ.get('ZERAWAVE_ARTWORK_STORE') or Path(__file__).resolve().parents[2]/'work/studio/artwork')
        self.rows={};self.leases={};self.jobs={};self.failures={};self.saves={};self.save_jobs={};self.save_pins={}
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Owner PNG persistence')
        self.save_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Revision-pinned session save')
        self.barrier=None # controlled fixture hook; never set by production
        self.write_cancels={};self.save_cancels={};self.stores={};self.store_errors={};self.closing=False
        if self.folder.is_dir():
            from artwork_store import get_store
            try:store=get_store(self.folder);self.stores[str(store.folder)]=store
            except Exception as exc:self.store_errors[str(self.folder)]=str(exc)[:240]
        self.retry_queue=set();self.allocations={};self.owned_paths={};self.cleanup_failures={};self.cleanup_after=0;self.lease_cleanup_failures={};self.mapping_pool=_MappingPool()
    def usage(self,keys=None):
        # Rows own immutable, admission-validated tile tables. Revalidating every
        # history tile on each tick starves the PNG worker under the same GIL.
        sizes={}
        for key in self.rows if keys is None else keys:sizes.update(self.allocations.get(key,{}))
        return sizes
    def admit(self,assets):
        """All-or-nothing admission. No registry disk inspection or PNG decode."""
        if len(self.cleanup_failures)>=MAX_RESOURCES:raise ValueError('Retired PNG cleanup is blocked; completed edit rejected, not saved. Correct the destination or Save As.')
        assets=deepcopy(assets);new={};leases={};allocations={}
        if len(assets)>MAX_JOBS:raise ValueError('Too many raster resources in one operation.')
        if len(self.rows)+len(assets)>MAX_RESOURCES:raise ValueError('256 raster resources retained; secure/release recovery checkpoints before another edit')
        from raster_tiles import unique_bytes,mapping_bytes,TileLease,tiled
        retained=self.usage();queued=self.usage(k for k,j in self.jobs.items() if not j.done())
        if sum(not j.done() for j in self.jobs.values())+sum(a.get('source_snapshot') is not True for a in assets)>MAX_JOBS:raise ValueError('Raster persistence queue full; completed stroke rejected, not saved. Redraw after work drains or Retry succeeds.')
        try:
            for asset in assets:
                from media_registry import reference
                ref=reference(asset);identity=ref['id'];desc=validate(asset.get('runtime'))
                if identity in self.rows or identity in new:raise ValueError('Raster resource ID already exists.')
                source=asset.get('source_snapshot') is True
                if ref['kind']!='Images' or not ref.get('managed') and not source:raise ValueError('Runtime resources must be managed rasters or validated source leases.')
                # The producer cannot nominate a filesystem write destination.
                if not source:ref['path']=str((self.folder/(identity+'.png')).resolve())
                from raster_tiles import allocations as allocation_sizes
                allocated=allocation_sizes(desc)
                if any(name in retained and retained[name]!=size for name,size in allocated.items()):raise ValueError('Immutable mapping size changed')
                allocations[identity]=allocated;retained.update(allocated)
                if not source:queued.update(allocated)
                if sum(retained.values())>MAX_BYTES or sum(((size+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE for size in retained.values())>MAX_MAPPING_BYTES or sum(queued.values())>MAX_JOB_BYTES:raise ValueError('Raster resource/queue byte limit; edit not accepted. Save/retry after pending work.')
                if tiled(desc):
                    readers=[]
                    try:
                        for tile in desc['tiles']:readers.append(self.mapping_pool.acquire(tile))
                        lease=TileLease(desc,leases=readers,native=False)
                    except BaseException as original:
                        for reader in readers:
                            try:reader.close()
                            except Exception as cleanup:original.add_note('Pooled tile admission cleanup: '+str(cleanup))
                        raise
                else:lease=SharedMemory(name=desc['name'])
                leases[identity]=lease
                if not tiled(desc) and not desc['bytes']<=lease.size<=((desc['bytes']+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE:raise ValueError('Invalid raster mapping allocation.')
                metadata=deepcopy(asset['metadata']) if source else dict(width=desc['width'],height=desc['height'],bytes=desc['bytes'],mtime_ns=0,pixel_aspect=1,alpha=True,color='sRGB')
                new[identity]=dict(ref,runtime=desc,status='Ready',error='',durability='durable' if source else 'pending',source_snapshot=source,metadata=metadata)
        except BaseException as original:
            for lease in leases.values():
                try:lease.close()
                except Exception as cleanup:original.add_note('Raster admission cleanup: '+str(cleanup))
            raise
        self.rows.update(new);self.leases.update(leases);self.allocations.update(allocations);return new
    def reject(self,ids):
        for key in ids:
            self.write_cancels.pop(key,None)
            self.rows.pop(key,None);self.allocations.pop(key,None)
            if key in self.leases:release(self.leases.pop(key))
    def retire(self):
        """Move old-context lease handles out of current asset-ID resolution.

        Stored asset IDs remain stable. Private retention keys distinguish old
        write/save readers from a newly loaded reference with that same ID.
        """
        mapping={k:uuid.uuid4().hex for k,r in self.rows.items() if not r.get('retired')}
        for old,key in mapping.items():
            row=self.rows.pop(old);row['retired']=True;self.rows[key]=row
            self.leases[key]=self.leases.pop(old);self.allocations[key]=self.allocations.pop(old)
            if old in self.owned_paths:self.owned_paths[key]=self.owned_paths.pop(old)
            if old in self.jobs:self.jobs[key]=self.jobs.pop(old)
            if old in self.write_cancels:self.write_cancels[key]=self.write_cancels.pop(old)
            if old in self.failures:self.failures[key]=self.failures.pop(old)
            if old in self.retry_queue:self.retry_queue.discard(old);self.retry_queue.add(key)
        for key,pins in self.save_pins.items():self.save_pins[key]={mapping.get(k,k) for k in pins}
        for out in self.saves.values():out['resource_keys']={k:mapping.get(v,v) for k,v in out.get('resource_keys',{}).items()}
        return mapping
    def persist(self,identity):
        prior=self.jobs.get(identity)
        if prior is not None and not prior.done():return False
        from raster_tiles import unique_bytes
        active=[k for k,j in self.jobs.items() if not j.done()];queued=self.usage(active);queued.update(self.allocations[identity])
        if len(active)>=MAX_JOBS or sum(queued.values())>MAX_JOB_BYTES:return False
        row=deepcopy(self.rows[identity]);reader=self.leases[identity]
        # Pending job ownership pins this admission-validated immutable lease.
        # Reopening hundreds of the same mappings per PNG dominated materialize.
        import threading
        from artwork_store import get_store,check_cancel
        cancel=threading.Event();self.write_cancels[identity]=cancel
        store_ref=[]
        def write():
            started=time.perf_counter()
            while self.barrier is not None and not self.barrier.wait(.02):check_cancel(cancel)
            barrier=os.environ.get('ZERAWAVE_RASTER_TEST_BARRIER')
            while barrier and Path(barrier).exists():
                check_cancel(cancel);time.sleep(.01)
            check_cancel(cancel)
            failure=os.environ.get('ZERAWAVE_RASTER_TEST_FAIL_WRITE')
            if failure and Path(failure).exists():raise OSError('Injected isolated PNG write failure')
            from artwork import encode_image
            store=get_store(Path(row['path']).parent);store_ref.append(store)
            materialized=time.perf_counter();pixels=image(row['runtime'],native=False,lease=reader);data=encode_image(pixels)
            encoded=time.perf_counter();check_cancel(cancel)
            created=store.write(row['path'],data,kind='working',cancel=cancel)
            return dict(path=row['path'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),finished=time.perf_counter(),created=created,queue_ms=(materialized-started)*1000,encode_ms=(encoded-materialized)*1000,write_ms=(time.perf_counter()-encoded)*1000)
        self.jobs[identity]=self.pool.submit(write);self.jobs[identity].store_ref=store_ref
        self.rows[identity].update(durability='pending',error='')
        return True
    def retry(self):
        # A bounded set coalesces repeated user Retry requests. Every failed
        # accepted resource stays leased until success or a secured Save As.
        self.retry_queue.update(self.failures)
        self._retry_pending()
        return dict(scheduled=sum(not j.done() for j in self.jobs.values()),waiting=len(self.retry_queue))
    def _retry_pending(self):
        for key in list(self.retry_queue):
            if key not in self.rows or key not in self.failures:self.retry_queue.discard(key);continue
            try:
                if self.persist(key):self.retry_queue.discard(key)
            except Exception as exc:
                self.rows[key].update(durability='failed',error=str(exc)[:240]);self.failures[key]=str(exc)[:240]
                self.retry_queue.discard(key)
                forget_traceback(exc)
    def poll(self):
        for key,job in list(self.jobs.items()):
            for store in getattr(job,'store_ref',()):self.stores[str(store.folder)]=store
            if not job.done() or getattr(job,'reported',False):continue
            job.reported=True
            try:
                info=job.result();
                if info.get('created'):self.owned_paths[key]=info['path']
                self.rows[key]['durability']='durable';self.rows[key]['persisted']=info;self.rows[key]['error']='';self.failures.pop(key,None)
            except Exception as exc:
                self.rows[key]['durability']='failed';self.rows[key]['error']=str(exc)[:240];self.failures[key]=str(exc)[:240]
                forget_traceback(exc)
        self._retry_pending()
        for key,job in list(self.save_jobs.items()):
            if not job.done() or getattr(job,'reported',False):continue
            job.reported=True;out=self.saves[key]
            try:out.update(status='durable',**job.result())
            except CancelledError as exc:out.update(status='cancelled',error=str(exc)[:240])
            except Exception as exc:
                out.update(status='failed',error=str(exc)[:240]);forget_traceback(exc)
            # Failed recovery snapshots remain pinned and can be retried/exported.
            if out['status']=='cancelled':
                self.save_pins.pop(key,None);out.pop('values',None);out.pop('drafts',None)
            if out['status']=='durable':
                self.save_pins.pop(key,None)
                out.pop('values',None)
                for identity,path in out.get('recovered',{}).items():
                    resource=out['resource_keys'].get(identity,identity)
                    if resource in self.rows:
                        self.rows[resource].update(durability='secured',error='',recovery_path=path)
                        self.failures.pop(resource,None)
    def save(self,key,values,drafts,path,session,revision,resource_keys=None,recover_all=False):
        if key in self.saves:return self.saves[key]
        if sum(not j.done() for j in self.save_jobs.values())>=4 or len(self.save_pins)>=4:raise ValueError('Four save/recovery checkpoints retained; retry/export failed checkpoints first.')
        values=deepcopy(values);drafts=deepcopy(drafts);destination=Path(path)
        refs={a['id'] for a in values['media']['assets']};keys=dict(resource_keys) if resource_keys is not None else {k:k for k in refs if k in self.rows}
        if recover_all:
            # Explicit Save As secures accepted unsaved versions as well as its
            # requested scene. Old-context and failed history snapshots are not
            # discarded to make room, and repeated Retry never replays strokes.
            included=set(keys.values())
            keys.update({'retained-'+k:k for k,r in self.rows.items() if k not in included and not r.get('source_snapshot') and r['durability'] not in ('durable','secured')})
        rows={k:deepcopy(self.rows[v]) for k,v in keys.items() if v in self.rows};readers={k:self.leases[v] for k,v in keys.items() if v in self.rows};waits={k:self.jobs.get(keys[k]) for k in rows}
        outcome=dict(id=key,session=session,revision=revision,path=str(destination),status='pending',error='',requested=time.perf_counter(),values_sha256=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest(),values=deepcopy(values),drafts=deepcopy(drafts),resource_keys=dict(keys))
        outcome['recover_all']=recover_all
        if recover_all:outcome['resume_folder']=str(destination.with_suffix('.rasters')/session)
        self.saves[key]=outcome;self.save_pins[key]=set(keys.values())
        import threading
        from artwork_store import check_cancel, get_store, write_json
        cancel=threading.Event();self.save_cancels[key]=cancel
        def secure():
            from artwork import portable_scene,store_image
            check_cancel(cancel)
            # A Save As can recover a failed working-store write directly to its
            # own dependency folder. The working revision/resource never changes.
            recovered={};recovery_rows=[]
            for k,row in rows.items():
                check_cancel(cancel)
                if row.get('source_snapshot'):
                    # Undo can restore frozen source pixels after the external
                    # file changes. Export only this requested save's immutable
                    # snapshot, never change/relink the library original.
                    record=store_image(image(row['runtime'],native=False,lease=readers[k]),'Revision-pinned source snapshot',destination.with_suffix('.assets'),cancel=cancel)
                    source_id=uuid.uuid5(uuid.NAMESPACE_URL,'zerawave-source:'+k+':'+Path(record['path']).stem).hex
                    for ref in values['media']['assets']:
                        if ref['id']==k:ref.update(id=source_id,path=record['path'],managed=True,internal=True)
                    for layer in values['media']['layers']:
                        if layer.get('asset')==k:layer['asset']=source_id
                    recovered[k]=record['path']
                    continue
                job=waits[k]
                secured=row.get('recovery_path')
                if secured and Path(secured).is_file():
                    recovered[k]=secured
                    for ref in values['media']['assets']:
                        if ref['id']==k:ref['path']=secured
                    continue
                try:
                    while job is not None and not job.done():check_cancel(cancel);time.sleep(.01)
                    check_cancel(cancel)
                    if job is not None:job.result()
                    if not Path(row['path']).is_file():raise OSError('Dependency not persisted.')
                except CancelledError:raise
                except Exception:
                    record=store_image(image(row['runtime'],native=False,lease=readers[k]),row['provenance'],destination.with_suffix('.assets'),cancel=cancel)
                    recovered[k]=record['path']
                    for ref in values['media']['assets']:
                        if ref['id']==k:ref['path']=record['path']
                if k not in refs:
                    dependency=Path(recovered.get(k,row['path']));data=dependency.read_bytes();digest=hashlib.sha256(data).hexdigest()
                    folder=destination.with_suffix('.assets');folder.mkdir(parents=True,exist_ok=True);portable=folder/(digest+'.png')
                    get_store(folder).write(portable,data,cancel=cancel)
                    recovered[k]=str(portable.resolve())
                    # Non-scene accepted work is independently portable and
                    # indexed before declaring this recovery checkpoint durable.
                    recovery_rows.append(dict(resource_key=keys[k],asset_id=row['id'],original_path=row['path'],path=str(portable.resolve()),sha256=digest))
            recovery_index=None
            if recovery_rows:
                recovery_index=destination.with_suffix('.assets')/('accepted-'+key+'.json')
                write_json(recovery_index,json.dumps(dict(session=session,revision=revision,resources=recovery_rows),indent=2).encode('utf8'),cancel)
            values['media']=portable_scene(values['media'],destination,cancel=cancel)
            if values['media'].get('canvas') is None:values['media']['canvas']=[1280,720]
            saved=dict(version=5,**values,qt_tuning_drafts=drafts,b1_saved_revision=dict(session=session,revision=revision))
            write_json(destination,json.dumps(saved,indent=2).encode('utf8'),cancel)
            return dict(finished=time.perf_counter(),recovered=recovered,recovery_index=str(recovery_index) if recovery_index else None)
        try:self.save_jobs[key]=self.save_pool.submit(secure)
        except Exception as exc:outcome.update(status='failed',error='Save worker unavailable: '+str(exc)[:200])
        # Only four full value snapshots are retained; terminal outcome metadata
        # is bounded independently from failed-checkpoint resource pins.
        for old in list(self.saves)[:-16]:
            if old not in self.save_pins:self.saves.pop(old,None);self.save_jobs.pop(old,None);self.save_cancels.pop(old,None)
        return outcome
    def retry_save(self,key,path=None):
        prior=self.saves.get(key)
        if not prior or prior['status']!='failed':raise ValueError('No failed checkpoint to retry.')
        # Transfer its existing resource pin into the new retry reservation.
        pins=self.save_pins.pop(key,None)
        try:
            outcome=self.save(uuid.uuid4().hex,prior['values'],prior['drafts'],path or prior['path'],prior['session'],prior['revision'],prior['resource_keys'],prior.get('recover_all',False))
            prior.update(status='retried',retry_id=outcome['id']);prior.pop('values',None);prior.pop('drafts',None)
            return outcome
        except BaseException:
            if pins is not None:self.save_pins[key]=pins
            raise
    def resume_store(self,key):
        out=self.saves[key]
        if out['status']=='durable' and out.get('resume_folder'):self.folder=Path(out['resume_folder'])
    def retain(self,ids,protected_paths=()):
        pinned=set(ids)
        for pins in self.save_pins.values():pinned.update(pins)
        pinned.update(k for k,j in self.jobs.items() if not j.done())
        for key in set(self.rows)-pinned:
            try:release(self.leases[key])
            except Exception as exc:
                # A borrowed foreign buffer can temporarily prevent closure.
                # Keep the complete resource/accounting so the next tick can
                # retry after that reader releases; never lose its last lease.
                self.lease_cleanup_failures[key]=str(exc)[:160]
                continue
            self.lease_cleanup_failures.pop(key,None)
            self.leases.pop(key);self.rows.pop(key);self.allocations.pop(key,None);self.jobs.pop(key,None)
            self.failures.pop(key,None);self.retry_queue.discard(key);self.write_cancels.pop(key,None)
            path=self.owned_paths.pop(key,None)
            if path:self.cleanup_failures.setdefault(path,'')
        if time.perf_counter()>=self.cleanup_after:
            self.cleanup_after=time.perf_counter()+.25
            from artwork_store import get_store
            protected={str(Path(p).resolve()).casefold() for p in protected_paths}
            for path in list(self.cleanup_failures):
                if str(Path(path).resolve()).casefold() in protected:continue
                store=get_store(Path(path).parent);self.stores[str(store.folder)]=store;store.retire(path)
            errors={}
            for store in self.stores.values():
                try:store.reconcile();errors.update(store.reclaim(protected_paths));self.store_errors.pop(str(store.folder),None)
                except Exception as exc:errors[str(store.folder)]=str(exc)[:160];self.store_errors[str(store.folder)]=str(exc)[:240]
            self.cleanup_failures=errors
    def cancel_save(self,key):
        if key not in self.save_jobs:raise ValueError('No requested save to cancel.')
        self.save_cancels[key].set();self.save_jobs[key].cancel()
    def prepare_close(self,discard=False):
        if discard:
            self.retry_queue.clear()
            for event in self.write_cancels.values():event.set()
            for key in self.save_jobs:self.cancel_save(key)
            for job in self.jobs.values():job.cancel()
        return all(j.done() for j in list(self.jobs.values())+list(self.save_jobs.values()))
    def history_bytes(self,ids,sizes):
        from raster_tiles import unique_bytes
        return sum(self.usage(ids).values())+sum(sizes.get(k,0) for k in ids if k not in self.rows)
    def state(self):
        from native_raster import backend
        from raster_tiles import unique_bytes,mapping_bytes
        selection=backend();native=selection.core.stats() if selection.core else {}
        return dict(mapping_bytes=sum(((size+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE for size in self.usage().values()),mapping_limit=MAX_MAPPING_BYTES,resource_count=len(self.rows),resource_limit=MAX_RESOURCES,backend=selection.status(),native=native,logical_bytes=sum(r['runtime']['bytes'] for r in self.rows.values()),bytes=sum(self.usage().values()),limit=MAX_BYTES,job_limit=MAX_JOBS,queued_bytes=sum(self.usage(k for k,j in self.jobs.items() if not j.done()).values()),queue_byte_limit=MAX_JOB_BYTES,pending=sum(not j.done() for j in self.jobs.values()),retry_waiting=len(self.retry_queue),retained_checkpoints=len(self.save_pins),failures=deepcopy(self.failures),owner_mapping_handles=len(self.mapping_pool.rows),working_store=str(self.folder),stores={path:store.state() for path,store in self.stores.items()},store_errors=dict(self.store_errors),lease_cleanup_failures=dict(self.lease_cleanup_failures),cleanup_failure_count=len(self.cleanup_failures),cleanup_failures=dict(list(self.cleanup_failures.items())[-16:]),resources={k:r['durability'] for k,r in self.rows.items()},saves=[{k:v for k,v in out.items() if k not in ('values','saved_values','drafts')} for out in self.saves.values()])
    def close(self,discard=False,protected_paths=()):
        deadline=time.perf_counter()+5
        while not self.prepare_close(discard):
            if time.perf_counter()>=deadline:raise TimeoutError('Raster close incomplete: a worker is still using its snapshot.')
            time.sleep(.01)
        self.poll()
        # Future completion precedes resource release; executor shutdown is then
        # finite and observes its actual thread exit, never a wait=False fiction.
        self.pool.shutdown(wait=True,cancel_futures=True);self.save_pool.shutdown(wait=True,cancel_futures=True)
        for key,lease in list(self.leases.items()):release(lease);self.leases.pop(key)
        for path in self.owned_paths.values():
            from artwork_store import get_store
            get_store(Path(path).parent).retire(path)
        for store in self.stores.values():store.reclaim(protected_paths,limit=MAX_RESOURCES)
        self.rows.clear();self.allocations.clear();return True

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
