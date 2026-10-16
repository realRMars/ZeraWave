"""Control-owned silent media service; bounded independent codec lanes.

Four visible sources, four persistent lanes (two FFmpeg threads per decoder),
one active and one replaceable pending request per lane. No audio output. Cache
planes share 96 MiB; transfer slots share 128 MiB. Every completion carries its
source, generation, transport epoch, clock turn, direction and requested PTS.
"""
from copy import deepcopy
from collections import OrderedDict
from multiprocessing.shared_memory import SharedMemory
from pathlib import Path
import math,struct,threading,time,uuid
import numpy as np

MAX_ANIMATIONS=4
MAX_FRAME_PIXELS=8*1024*1024
MAX_CACHE_BYTES=96*1024*1024
MAX_STAGING_BYTES=128*1024*1024
HEADER=64

def backend():
    try:import av;return av
    except ImportError:raise ValueError('Video requires PyAV 19.0.1; the decoder is unavailable in this environment. Still images remain available.')

def inspect_animation(path,cancel):
    av=backend()
    with av.open(str(path),mode='r',timeout=(2.,2.)) as container:
        if not container.streams.video:raise ValueError('No decodable video stream.')
        stream=container.streams.video[0];codec=stream.codec_context
        if codec.width<1 or codec.height<1 or codec.width*codec.height>MAX_FRAME_PIXELS:raise ValueError('Animated sources exceed 8,388,608 decoded pixels; no automatic reduction.')
        frame=next(container.decode(stream),None)
        if cancel.is_set():raise InterruptedError('Media operation cancelled.')
        if frame is None:raise ValueError('Decoder returned no video frames.')
        if int(frame.color_trc or 0) in (16,18) or int(frame.colorspace or 0)==9:raise ValueError('HDR video is not supported by this SDR composition path.')
        duration=float(stream.duration*stream.time_base) if stream.duration is not None else float(container.duration/av.time_base) if container.duration else 0.
        if duration<=0 or duration>86400:raise ValueError('A finite video duration up to 24 h is required.')
        sar=float(stream.sample_aspect_ratio or 1);rotation=int(getattr(frame,'rotation',0) or stream.metadata.get('rotate',0))%360
        if rotation not in (0,90,180,270):raise ValueError('Only right-angle source orientation is supported.')
        return dict(width=codec.width,height=codec.height,duration=duration,codec=codec.name,
            pixel_aspect=sar,rotation=rotation,fps=float(stream.average_rate or 0),decoded_plane_bytes=sum(p.buffer_size for p in frame.planes),pixel_format=frame.format.name,alpha='Decoded RGBA; codec-dependent',
            color='FFmpeg SDR conversion to display-encoded RGB; no HDR',backend='PyAV '+av.__version__,validation='Stream header and first decoded frame; later failures retain valid-source previous pixels with an error')

def timeline(elapsed,start,end,rate,loop,direction=1):
    span=end-start
    if span<=0:return start,False
    t=max(0.,elapsed)*rate
    if loop=='Loop':return (start+t%span if direction>0 else end-t%span),False
    if loop=='Ping-pong':
        phase=t%(2*span);offset=phase if phase<=span else 2*span-phase
        return (start+offset if direction>0 else end-offset),False
    return (min(end,start+t) if direction>0 else max(start,end-t)),t>=span

def elapsed_at(settings,position,end=None):
    end=settings['end'] if end is None else end
    return max(0.,position-settings['start'] if settings.get('direction',1)>0 else end-position)/settings['rate']

def token():return uuid.uuid4().int&((1<<64)-1)

class CachePressure(InterruptedError):
    """Temporary shared cache pressure; not a failed or accepted frame."""

class PlaneBudget:
    def __init__(self):self.lock=threading.Lock();self.used=0;self.peak=0
    def take(self,n):
        with self.lock:
            if self.used+n>MAX_CACHE_BYTES:return False
            self.used+=n;self.peak=max(self.peak,self.used);return True
    def release(self,n):
        with self.lock:self.used-=n;assert self.used>=0

class DecoderWindow:
    """One lane owns all codec calls. PTS lookup and a byte-bounded plane cache.

    Demand seeks keep other cached timestamps. Reverse misses refill from a
    timestamp lead-in below the demand; forward prefetch continues the iterator.
    Prefetch never converts every plane or preloads the clip.
    """
    def __init__(self,path,budget,*,source_timestamps=False,codec_threads=2):
        if type(codec_threads) is not int or not 1<=codec_threads<=4:raise ValueError('Codec thread count must be an integer from1 through4.')
        self.codec_threads=codec_threads
        av=backend();self.container=av.open(str(path),mode='r',timeout=(2.,2.))
        try:self.stream=self.container.streams.video[0]
        except Exception:self.container.close();raise ValueError('No video stream remains available.')
        self.stream.codec_context.thread_count=self.codec_threads
        self.stream.codec_context.thread_type='AUTO'
        self.cache=OrderedDict();self.bytes=0;self.budget=budget;self.pool=None
        # Legacy clocks retain their nonnegative seek policy. The project
        # evaluator requests actual signed source PTS, including preroll.
        self.seek_floor=min(0.,float((self.stream.start_time or 0)*self.stream.time_base)) if source_timestamps else 0.
        self.empty_pts=float('-inf') if source_timestamps else -1.
        self.iterator=None;self.last=self.empty_pts;self.decode_ms=0.;self.seek_count=0;self.ends={}
        self.convert_ms=0.;self.decoded_ready=0.;self.converted_ready=0.;self.temporary_planes=0;self.conversion_bytes=0
        self.converted=None;self.converted_bytes=0;self.frame_step=None;self.last_plane_bytes=0;self.eof=False;self.metrics={};self.refill_frames=0;self.refill_seconds=0.;self.refill_goal=None;self.obsolete_refills=0
        self._metrics()
    def _metrics(self):
        self.metrics=dict(codec_threads_configured=self.codec_threads,decoded_planes=self.bytes,converted_rgba=self.converted_bytes,
            decode_temporary_planes=self.temporary_planes,conversion_temporaries=self.conversion_bytes,
            cache_frames=len(self.cache),seeks=self.seek_count,decode_ms=self.decode_ms,convert_ms=self.convert_ms,refill_frames=self.refill_frames,refill_decode_ms=self.refill_seconds*1000,obsolete_refills=self.obsolete_refills)
    def _evict(self,target,direction,needed=0):
        while self.cache and self.bytes+needed>self.budget:
            # Retain frames towards the requested direction; drop farthest
            # behind first. Distances are timestamps, not guessed frame indices.
            candidates=list(self.cache)
            key=max(candidates,key=lambda p:(p>target if direction<0 else p<target,abs(p-target)))
            old=self.cache.pop(key);self.ends.pop(key,None);n=sum(p.buffer_size for p in old.planes);self.bytes-=n
            if self.pool:self.pool.release(n)
        self._metrics()
    def _store(self,pts,frame,target,direction):
        if pts in self.cache:return
        n=sum(p.buffer_size for p in frame.planes);self.last_plane_bytes=n
        if n>self.budget:raise ValueError('Frame exceeds the active reverse cache budget.')
        self._evict(target,direction,n)
        if self.pool:
            while not self.pool.take(n):
                if not self.cache:raise CachePressure('Waiting for decoded-plane budget retirement.')
                key=max(self.cache,key=lambda p:abs(p-target));old=self.cache.pop(key);self.ends.pop(key,None);size=sum(p.buffer_size for p in old.planes);self.bytes-=size;self.pool.release(size)
        self.cache[pts]=frame;self.bytes+=n;self._metrics()
    def rgba(self,frame):
        if frame.width*frame.height>MAX_FRAME_PIXELS:raise ValueError('Decoded frame exceeds 8,388,608 pixels.')
        if int(frame.color_trc or 0) in (16,18) or int(frame.colorspace or 0)==9:raise ValueError('HDR frame conversion is unsupported; valid previous SDR pixels retained.')
        started=time.perf_counter();self.conversion_bytes=frame.width*frame.height*8;self._metrics()
        try:
            data=frame.to_ndarray(format='rgba');rotation=int(getattr(frame,'rotation',0) or self.stream.metadata.get('rotate',0))%360
            # FFmpeg gives these explicitly alpha-free formats opaque RGBA.
            # Avoid scanning every full-size alpha plane on ordinary H264.
            # Palette, RGBA, YUVA and other formats keep the exact alpha path.
            opaque=frame.format.name in ('yuv420p','yuvj420p','yuv422p','yuvj422p','yuv444p','yuvj444p','nv12','nv21','rgb24','bgr24','gray')
            from media_transfer import backend as transfer_backend
            # Matched 720p opaque/zero-rotation publication is faster in NumPy.
            # Use the coarse native loop where alpha or rotation amortizes it.
            native=None if opaque and rotation==0 else transfer_backend().publication(data,rotation,opaque)
            if native is not None:
                self.convert_ms=(time.perf_counter()-started)*1000;self.converted_ready=time.perf_counter();return native
            if rotation:data=np.rot90(data,-rotation//90)
            if not opaque and np.min(data[:,:,3])<255:
                # RGBA ndarray can borrow a cached codec plane. Never mutate
                # that immutable source when premultiplying a publication.
                self.conversion_bytes=data.nbytes*3;self._metrics();data=data.copy()
                # Bound the uint16 alpha conversion to rows rather than several
                # additional full native images.
                for y in range(data.shape[0]):data[y,:,:3]=((data[y,:,:3].astype(np.uint16)*data[y,:,3:4].astype(np.uint16)+127)//255).astype(np.uint8)
            value=(data.shape[1],data.shape[0],data[::-1].tobytes())
            self.convert_ms=(time.perf_counter()-started)*1000;self.converted_ready=time.perf_counter();return value
        finally:self.conversion_bytes=0;self._metrics()
    def ready(self,target,nearest=False):
        keys=sorted(self.cache)
        if not keys:return None
        floor=max((p for p in keys if p<=target),default=None)
        if floor is None:return keys[0] if target==keys[0] else None
        end=self.ends.get(floor)
        if target!=floor and (end is None or target>=end) and not (self.eof and floor==keys[-1] and target>=floor):return None
        if nearest and end is not None and target-floor>end-target:
            return end if end in self.cache else None
        return floor
    def _refill(self,target,cancel,direction=1,lead=0.,deadline=None,interest=None,work_budget=None):
        if cancel.is_set():return False
        began=time.perf_counter();completed=False;progressed=False
        # A demand slice starts at actual codec service, after caller/queue
        # delay. A slow seek may consume the allowance; still permit one native
        # decode call so repeated slices make progress. Cancellation always wins.
        if work_budget is not None:deadline=began+work_budget
        # A sliced prefetch may still be inside GOP lead-in, well below its
        # target. Continue that iterator instead of restarting the same keyframe
        # every 40 ms. The existing 512-frame/two-second work bounds still apply.
        forward=self.iterator is not None and not self.eof and self.last<=target
        goal=self.refill_goal if self.refill_goal is not None else self.last
        if forward and interest and target-goal>2.:
            # Only a newer display demand can retire an obsolete forward goal.
            # Continuing its lead-in forever falsely exhausts the GOP bound as
            # a fast clock runs away. Resynchronize to the current keyframe;
            # cached planes and copied/published readers retain their ownership.
            # Fixed timestamp seeks and prefetch without live interest keep the
            # original cumulative 512-frame/two-second protection.
            forward=False;self.obsolete_refills+=1
        if self.refill_goal is None:self.refill_goal=target
        if not forward:
            seek=max(self.seek_floor,target-lead)
            if self.seek_floor<0.:
                # Some demuxers refuse negative seek offsets. Decode signed
                # preroll from the beginning instead, within the same bounded
                # GOP work/cache protection. Reopen only for a backwards miss.
                if self.iterator is not None:
                    path=self.container.name;self.container.close()
                    self.container=backend().open(path,mode='r',timeout=(2.,2.))
                    self.stream=self.container.streams.video[0]
                    self.stream.codec_context.thread_count=self.codec_threads;self.stream.codec_context.thread_type='AUTO'
            else:
                self.container.seek(max(int(self.seek_floor/float(self.stream.time_base)),int(seek/float(self.stream.time_base))),stream=self.stream,backward=True,any_frame=False)
            self.iterator=iter(self.container.decode(self.stream));self.seek_count+=1;self.eof=False;self.last=self.empty_pts;self.refill_frames=0;self.refill_seconds=0.;self.refill_goal=target
        previous=self.last if forward else None
        try:
            while True:
                # Test a prefetch deadline before entering the native call.
                # A returned plane must not be dropped just because that call
                # crossed the deadline: doing so creates a hole in PTS coverage.
                if cancel.is_set() or deadline is not None and time.perf_counter()>=deadline and (work_budget is None or progressed):return False
                frame=next(self.iterator,None)
                progressed=True
                if frame is None:break
                if cancel.is_set():return False
                self.refill_frames+=1
                if self.refill_frames>512 or self.refill_seconds+time.perf_counter()-began>2.:raise ValueError('Video GOP decode exceeds the bounded window; choose a more seekable clip.')
                if frame.pts is None:continue
                pts=float(frame.pts*self.stream.time_base)
                if previous is not None and pts>previous:
                    self.frame_step=pts-previous
                    if previous in self.cache:self.ends[previous]=pts
                previous=pts;self.last=pts;self.temporary_planes=sum(p.buffer_size for p in frame.planes);self._metrics()
                # Compressed lead-in remains native; keep only useful planes.
                span=(self.budget/max(1,self.temporary_planes)-2)*(self.frame_step or .04)
                if pts>=target-max(lead,span):
                    focus,active_direction=interest() if interest else (target,direction)
                    self._store(pts,frame,focus,active_direction)
                if pts>target:completed=True;return True
            self.eof=True;completed=True;return bool(self.cache)
        finally:
            elapsed=time.perf_counter()-began;self.refill_seconds=0. if completed else self.refill_seconds+elapsed
            if completed:self.refill_frames=0
            if completed:self.refill_goal=None
            self.decode_ms=elapsed*1000;self.decoded_ready=time.perf_counter();self.temporary_planes=0;self._metrics()
    def get(self,target,cancel,last_pts=None,nearest=False):
        if cancel.is_set():return None
        key=self.ready(target,nearest)
        if key is None:
            # Project display/export requests are distinct demands. A distant
            # forward miss must seek to its keyframe instead of walking hundreds
            # of obsolete planes from the previous demand. Legacy policy and
            # existing cumulative512-frame/two-second work limits stay intact.
            if getattr(self,'demand_resync',False):
                completed=self._refill(target,cancel,interest=lambda:(target,1))
            else:completed=self._refill(target,cancel)
            if not completed:return None
            key=self.ready(target,nearest)
        if cancel.is_set():return None
        if key is None:
            keys=sorted(self.cache)
            if not keys:raise ValueError('No frame at this video position.')
            key=min(keys,key=lambda p:abs(p-target))
        if key==last_pts:return key,None
        if self.converted and self.converted[0]==key:return self.converted
        # Retire the old converted snapshot before allocating its replacement.
        self.converted=None;self.converted_bytes=0;self._metrics()
        data=self.rgba(self.cache[key]);self.converted=(key,data);self.converted_bytes=len(data[2]);self._metrics();return self.converted
    def endpoint_pts(self,target,cancel):
        # Ping-pong phase needs a timestamp, not a converted 14 MB image.
        if self.ready(target) is None and not self._refill(target,cancel):return None
        if cancel.is_set():return None
        key=self.ready(target)
        return key if key is not None else max(self.cache,default=None)
    def adjacent(self,anchor,direction,start,end,cancel):
        """Actual adjacent PTS, with a bounded codec-owned refill; no FPS index."""
        anchor=max(start,min(anchor,end-1e-7))
        key=self.ready(anchor)
        if key is None:
            if not self._refill(anchor,cancel):return None
            key=self.ready(anchor)
        if key is None:raise ValueError('Frame navigation has no timestamp at this position.')
        if direction>0:
            following=self.ends.get(key)
            if following is None or following not in self.cache:
                if not self._refill(key,cancel):return None
                following=self.ends.get(key)
            return min(end-1e-7,following) if following is not None and following<end else key
        previous=max((p for p in self.cache if p<key and self.ends.get(p)==key),default=None)
        if previous is None and key>start:
            # Seeking before the anchor keyframe includes the preceding GOP.
            # Iterator/cache retain only the same bounded useful planes.
            self.iterator=None
            if not self._refill(key,cancel,-1,lead=2.):return None
            previous=max((p for p in self.cache if p<key and self.ends.get(p)==key),default=None)
        if previous is None:return key
        return max(start,previous)
    def prefetch(self,target,direction,rate,start,end,cancel,interest=None):
        if cancel.is_set() or not self.cache:return
        # Actual PTS spacings bound the lead; rate supplies intent, bytes capacity.
        step=self.frame_step or .04;frames=max(1,self.budget//max(1,self.last_plane_bytes)-3)
        lead=min(.35*rate,max(step,frames*step*.65),2.)
        ahead=max(start,min(end-1e-7,target+direction*lead))
        if self.ready(ahead) is not None:return
        self._refill(target if direction<0 else ahead,cancel,direction,lead if direction<0 else 0.,time.perf_counter()+.04,interest)
    def close(self):
        try:self.container.close()
        finally:
            if self.pool:self.pool.release(self.bytes)
            self.cache.clear();self.ends.clear();self.bytes=0;self.converted=None;self.converted_bytes=0;self._metrics()

class FrameReader:
    """A client mapping owns its Windows handle; returned bytes own their pixels.

    No exported memoryview escapes. The writer retires its handle only on its
    lane after work exits; a reader retains its own mapping until retain/close.
    Sequence validation rejects writes, retired generations and overwritten slots.
    """
    def __init__(self):self.maps={};self.last={};self.copies=0;self.skipped=0;self.read_ms=0.;self.copy_bytes=0;self.peak_copy_bytes=0;self.waiting_reads=0;self.racing_reads=0;self.held_reads=0
    def read(self,descriptor,copy=None):
        started=time.perf_counter();name=descriptor['name'];shm=self.maps.get(name)
        if shm is None:shm=self.maps[name]=SharedMemory(name=name,create=False)
        sequence,generation,width,height,pts=struct.unpack_from('<QQIId',shm.buf,0)
        if not sequence or sequence%2 or generation!=descriptor['generation']:self.waiting_reads+=1;return None
        length=width*height*4
        if width<1 or height<1 or length>descriptor['capacity'] or HEADER+2*descriptor['capacity']>shm.size:raise ValueError('Invalid shared media frame bounds.')
        if self.last.get(name)==sequence:self.held_reads+=1;return None
        slot=(sequence//2)%2;view=shm.buf[HEADER+slot*descriptor['capacity']:HEADER+slot*descriptor['capacity']+length]
        self.copy_bytes=length;self.peak_copy_bytes=max(self.peak_copy_bytes,length)
        try:data=bytes(view) if copy is None else copy(view,width,height)
        finally:view.release();self.copy_bytes=0
        if struct.unpack_from('<Q',shm.buf,0)[0]!=sequence:self.racing_reads+=1;return None
        if name in self.last:self.skipped+=max(0,(sequence-self.last[name])//2-1)
        self.last[name]=sequence;self.copies+=1;self.read_ms=(time.perf_counter()-started)*1000
        return dict(width=width,height=height,**({'data':data} if copy is None else {'image':data}),pts=pts,sequence=sequence,generation=generation,read_ms=self.read_ms)
    def retain(self,names):
        for name in list(self.maps):
            if name not in names:self.maps.pop(name).close();self.last.pop(name,None)
    def snapshot(self):
        return dict(mapped_handles=len(self.maps),mapped_address_bytes=sum(s.size for s in self.maps.values()),
            owned_copy_bytes=self.copy_bytes,peak_single_copy_bytes=self.peak_copy_bytes,copies=self.copies,coalesced_publications=self.skipped,read_ms=self.read_ms,waiting_reads=self.waiting_reads,racing_reads=self.racing_reads,held_reads=self.held_reads,
            accounting='Mapping address sizes reference owner allocations; do not add them again to shared physical allocation.')
    def close(self):self.retain(set())

class SourceLane:
    """Fixed lane; codec, sprite image, shared writer and cleanup have one owner."""
    def __init__(self,owner,index):
        self.owner=owner;self.index=index;self.identity=None;self.key=None;self.pending=None;self.active=None;self.retiring=False
        self.decoder=None;self.decoder_needs_close=False;self.image=None;self.shm=None;self.mapping_closed=False;self.capacity=0;self.sequence=0;self.last=None;self.last_completed=None;self.metrics={};self.endpoint=None
        self.thread=threading.Thread(target=self.run,name='Studio media lane '+str(index),daemon=True);self.thread.start()
    def metrics_update(self,**values):
        self.metrics=dict(self.metrics,**values)
    def submit(self,job):
        if self.active and self.active['stamp']!=job['stamp']:
            self.active['prefetch_cancel'].set()
            # A clock turn can still yield reusable immutable planes. Do not
            # restart every GOP lead-in at 12x and starve the source forever.
            # Its old-direction success/error is nevertheless never published.
            if self.active['stamp'][:3]!=job['stamp'][:3]:self.active['cancel'].set()
        if self.pending:self.pending['cancel'].set();self.owner.coalesced+=1
        self.pending=job;self.owner.condition.notify_all()
    def retire(self):
        self.retiring=True
        if self.active:self.active['cancel'].set()
        if self.pending:self.pending['cancel'].set();self.pending=None
        self.owner.condition.notify_all()
    def valid(self,job):
        with self.owner.condition:
            state=self.owner.layers.get(self.identity)
            if state:self.owner.advance(state,time.perf_counter())
            return bool(not self.owner.closed and not self.retiring and state and state['visible'] and not state.get('release') and self.owner.stamp(state)==job['stamp'] and not job['cancel'].is_set())
    def source_valid(self,job):
        with self.owner.condition:
            state=self.owner.layers.get(self.identity)
            return bool(not self.owner.closed and not self.retiring and state and state['visible'] and not state.get('release') and self.owner.stamp(state)[:3]==job['stamp'][:3] and not job['cancel'].is_set())
    def open(self,job):
        s=job['state']
        if s['key'][2] is not None and Path(s['path']).stat().st_mtime_ns!=s['key'][2]:raise ValueError('Animated source changed; Refresh it before use.')
        if s['type']=='Sprite':
            from media_registry import decode_image
            meta,data=decode_image(s['path'],job['cancel']);self.image=(meta['width'],meta['height'],data);capacity=len(data)
        else:
            self.decoder=DecoderWindow(s['path'],job['budget']);self.decoder.pool=self.owner.plane_budget
            c=self.decoder.stream.codec_context;capacity=c.width*c.height*4
        if not self.source_valid(job):return
        if capacity<4 or capacity>MAX_FRAME_PIXELS*4:raise ValueError('Invalid animated native frame capacity.')
        with self.owner.condition:
            if self.owner.staging_bytes+capacity*2>MAX_STAGING_BYTES:raise CachePressure('Waiting for shared staging retirement.')
            self.owner.staging_bytes+=capacity*2;self.capacity=capacity
        try:self.shm=SharedMemory(create=True,size=HEADER+capacity*2);self.shm.buf[:HEADER]=bytes(HEADER)
        except BaseException:
            with self.owner.condition:self.owner.staging_bytes-=capacity*2;self.capacity=0
            raise
        self.metrics_update(shared_slots=capacity*2,shared_header=HEADER,sprite_sheet=len(self.image[2]) if self.image else 0)
    def dispose(self):
        errors=[]
        if self.decoder:
            try:self.decoder.close()
            except Exception as exc:errors.append(str(exc))
            else:self.decoder=None;self.decoder_needs_close=False
        self.image=None
        if self.shm:
            try:
                # Existing reader handles remain valid; invalidate the epoch.
                if not self.mapping_closed:
                    # SharedMemory.close may release its own view before mmap
                    # reports another export. Retry mmap.close after that export
                    # ends; do not try to write through an already released view.
                    if self.shm.buf is not None:
                        struct.pack_into('<Q',self.shm.buf,0,self.sequence+1);struct.pack_into('<Q',self.shm.buf,8,0);struct.pack_into('<Q',self.shm.buf,0,self.sequence+2)
                    self.shm.close();self.mapping_closed=True
                try:self.shm.unlink()
                except FileNotFoundError:pass
            except Exception as exc:errors.append(str(exc))
            else:self.shm=None;self.mapping_closed=False
        with self.owner.condition:
            if self.shm is None:self.owner.staging_bytes-=self.capacity*2;self.capacity=0
            if errors:self.owner.cleanup_errors=list(dict.fromkeys(self.owner.cleanup_errors+errors))[-8:]
        if self.shm is not None or self.decoder is not None:return False
        self.sequence=0;self.last=None;self.last_completed=None;self.endpoint=None;self.metrics={}
        return True
    def process(self,job):
        o=self.owner;s=job['state'];cancel=job['cancel'];began=time.perf_counter();timing=dict(requested_at=job['at'],service_at=began,queue_ms=(began-job['at'])*1000,requested_pts=job['target'],direction=job['direction'],request=job['serial'],generation=s['generation'],epoch=s['epoch'],turn=s['turn'])
        self.metrics_update(timing=timing,in_flight=True)
        def interest():
            # Native lead-in may take several slices. Retain planes near the
            # live clock, not a queued goal that has become obsolete meanwhile.
            with o.condition:
                latest=o.layers.get(self.identity)
                if latest and o.stamp(latest)[:3]==job['stamp'][:3]:
                    o.advance(latest,time.perf_counter());return latest['position'],latest['direction']
                return job['target'],job['direction']
        if self.decoder_needs_close and self.decoder:
            try:self.decoder.close()
            except Exception as exc:
                with o.condition:o.cleanup_errors=list(dict.fromkeys(o.cleanup_errors+[str(exc)]))[-8:]
                raise CachePressure('Waiting for failed decoder cleanup; original failure remains recorded.')
            self.decoder=None;self.decoder_needs_close=False
        if self.shm is None:
            # A cancelled open still has an owned codec; retire it on this lane.
            if (self.decoder or self.image) and not self.dispose():raise CachePressure('Waiting for previous native decoder cleanup.')
            self.open(job)
        if not self.source_valid(job) or self.shm is None:return
        if self.decoder is None and s['type']!='Sprite':self.decoder=DecoderWindow(s['path'],job['budget']);self.decoder.pool=o.plane_budget
        if self.decoder:
            self.decoder.budget=job['budget'];self.decoder._evict(job['target'],job['direction'])
        setting=s['settings'];ping=setting['loop']=='Ping-pong';endpoint_key=(setting['start'],setting['end']);selection_ready=True
        if ping and (not self.endpoint or self.endpoint[0]!=endpoint_key):
            endpoint=(setting['last']-setting['first'])/setting['fps'] if s['type']=='Sprite' else self.decoder.endpoint_pts(setting['end']-1e-7,cancel)
            if endpoint is None:return
            self.endpoint=(endpoint_key,max(setting['start'],endpoint))
            with o.condition:
                latest=o.layers.get(self.identity)
                if latest and latest['key']==s['key'] and latest['settings']==setting:latest['ping_end']=self.endpoint[1];o.advance(latest,time.perf_counter())
            if not self.source_valid(job):return
        if s.get('step_request'):
            step=s['step_request'];position=step['anchor']
            for _ in range(abs(step['count'])):
                if cancel.is_set():return
                if self.decoder is None:raise ValueError('Exact source-frame stepping requires video/GIF timestamps.')
                value=self.decoder.adjacent(position,1 if step['count']>0 else -1,setting['start'],setting['end'],cancel)
                if value is None:return
                if value==position:break
                position=value
            with o.condition:
                if not self.source_valid(job):return
                latest=o.layers[self.identity];latest['position']=position;latest['elapsed']=elapsed_at(setting,position,latest.get('ping_end'));latest['at']=time.perf_counter();latest.pop('step_request',None)
        # Use the clock at actual service, not a queued clock or decode duration.
        with o.condition:
            latest=o.layers[self.identity];o.advance(latest,time.perf_counter());target=latest['position'];direction=latest['direction']
            job['stamp']=o.stamp(latest)
        timing['service_requested_pts']=target
        if s['type']=='Sprite':
            index_offset=math.floor(target*setting['fps']+(.5 if ping else 0));pts=index_offset/setting['fps'];w,h,data=self.image;array=np.frombuffer(data,np.uint8).reshape(h,w,4)[::-1]
            index=setting['first']+min(setting['last']-setting['first'],max(0,index_offset));cw,ch=w//setting['columns'],h//setting['rows'];x=index%setting['columns'];y=index//setting['columns'];frame=(cw,ch,array[y*ch:(y+1)*ch,x*cw:(x+1)*cw][::-1].tobytes());decoded=time.perf_counter();converted=decoded
            self.metrics_update(sprite_frame_temporary=len(frame[2]),sprite_frame_peak=max(self.metrics.get('sprite_frame_peak',0),len(frame[2])))
        else:
            if self.decoder is None:self.decoder=DecoderWindow(s['path'],job['budget']);self.decoder.pool=o.plane_budget
            if self.decoder.ready(target,ping) is None:
                step=self.decoder.frame_step or .04;frames=max(1,self.decoder.budget//max(1,self.decoder.last_plane_bytes)-3)
                lead=min(.35*setting['rate'],max(step,frames*step*.65),2.) if direction<0 else 0.
                # Demand service includes a bounded forward lead so conversion
                # can select the live clock after decode, rather than always
                # discovering that a slow refill ended just behind that clock.
                forward_lead=min(.2*setting['rate'],max(step,frames*step*.65),.6) if direction>0 and s['playing'] else 0.
                fill_target=min(setting['end']-1e-7,target+forward_lead)
                # Active clocks can outrun a full GOP refill. Service a bounded
                # slice, then select the latest ready/explicitly held plane and
                # continue the iterator on the next demand. Paused and final
                # scrub demands still decode their exact timestamp before ACK.
                self.decoder._refill(fill_target,cancel,direction,lead,interest=interest,work_budget=.04 if s['playing'] else None)
            if not self.source_valid(job):return
            # Decode completion is availability, not presentation. Issue a new
            # selection of the latest requested time from ready native planes.
            # Immutable planes may survive a clock turn; an obsolete selected
            # frame/error cannot. If that time is not ready, keep valid last-good
            # pixels and service the coalesced newest demand next.
            with o.condition:
                latest=o.layers[self.identity];o.advance(latest,time.perf_counter());current_target=latest['position']
                selection_ready=self.decoder.ready(current_target,ping) is not None
                selected_target=current_target
                if not selection_ready:
                    # The live requested time may outrun this bounded decoded
                    # window. Select the best available valid-source plane as
                    # explicitly HELD, never as a ready requested-time result.
                    # Keep a closer last-good image rather than moving backwards
                    # to a worse cached fallback. Paused/seek demands stay exact.
                    if not latest['playing'] or not self.decoder.cache:return
                    available=list(self.decoder.cache) if ping else [p for p in self.decoder.cache if p<=current_target]
                    if not available:return
                    selected_target=min(available,key=lambda p:abs(p-current_target)) if ping else max(available)
                    if self.last and self.last[1]==latest['generation'] and abs(self.last[0]-current_target)<=abs(selected_target-current_target):return
                job['stamp']=o.stamp(latest);o.serial+=1;timing['presentation_request']=dict(serial=o.serial,at=time.perf_counter(),pts=current_target,direction=latest['direction'],turn=latest['turn'],generation=latest['generation'],epoch=latest['epoch'])
                target=current_target;direction=latest['direction']
            timing.update(selection_ready=selection_ready,selected_target=selected_target)
            value=self.decoder.get(selected_target,cancel,last_pts=self.last[0] if self.last and self.last[1]==s['generation'] else None,nearest=ping)
            if value is None:return
            pts,frame=value;decoded=self.decoder.decoded_ready;converted=self.decoder.converted_ready
        timing.update(decoded_ready=decoded,converted_ready=converted,decode_ms=self.decoder.decode_ms if self.decoder else 0.,convert_ms=self.decoder.convert_ms if self.decoder else 0.)
        if not self.valid(job):return
        if frame is not None and self.last!=(pts,s['generation']):
            w,h,data=frame
            if len(data)!=w*h*4 or len(data)>self.capacity:raise ValueError('Invalid animated converted frame bounds.')
            sequence=self.sequence+2;slot=(sequence//2)%2
            # Copy only the inactive slot, outside the control lock. Commit a
            # short seqlock header only after all identity guards pass again.
            copy_started=time.perf_counter();self.shm.buf[HEADER+slot*self.capacity:HEADER+slot*self.capacity+len(data)]=data
            timing['shared_copy_ms']=(time.perf_counter()-copy_started)*1000
            with o.condition:
                if not self.valid(job):return
                latest=o.layers[self.identity];struct.pack_into('<Q',self.shm.buf,0,sequence-1);struct.pack_into('<QIId',self.shm.buf,8,s['generation'],w,h,pts);struct.pack_into('<Q',self.shm.buf,0,sequence)
                self.sequence=sequence;self.last=(pts,s['generation']);timing['published_at']=time.perf_counter();timing['publish_requested_pts']=latest['position']
                o.results[self.identity]=dict(name=self.shm.name,generation=s['generation'],capacity=self.capacity,width=w,height=h,pixel_aspect=s['pixel_aspect'],pts=pts,sequence=sequence,
                    ready_at_request=selection_ready,selection_requested_pts=target,decode_ms=timing['decode_ms'],convert_ms=timing['convert_ms'],cache_bytes=self.decoder.bytes if self.decoder else len(self.image[2]),seeks=self.decoder.seek_count if self.decoder else 0,timing=timing)
                latest['error']='';latest['waiting']='';o.published+=1
                if latest.get('seek_pending') and selection_ready and not latest.get('step_request'):
                    latest['seek_pending']=False
                    if latest.pop('seek_resume',False):latest['playing']=True;latest['mode']='playing';latest['at']=time.perf_counter()
        with o.condition:
            self.last_completed=(job['stamp'],job['target'])
            if self.valid(job) and self.identity in o.results:
                o.results[self.identity]['ready_at_request']=selection_ready
                o.results[self.identity]['selection_requested_pts']=target
        if s.get('release_decoder') and self.decoder:
            self.decoder.close();self.decoder=None
            with o.condition:
                if self.identity in o.results:o.results[self.identity]['cache_bytes']=0
        elif self.decoder and s['playing'] and not o.frozen and self.valid(job):
            # Prefetch is low priority: a newer demand cancels it cooperatively.
            self.metrics_update(prefetch=True)
            self.decoder.prefetch(target,direction,setting['rate'],setting['start'],self.endpoint[1] if ping and self.endpoint else setting['end'],job['prefetch_cancel'],interest)
            self.metrics_update(prefetch=False)
        self.metrics_update(timing=timing)
    def run(self):
        o=self.owner
        try:
            while True:
                with o.condition:
                    o.condition.wait_for(lambda:o.closed or self.retiring or self.pending is not None)
                    if self.retiring or o.closed:job=None
                    else:job=self.pending;self.pending=None;self.active=job
                if job is None:
                    if not self.dispose():
                        with o.condition:o.condition.wait(timeout=.05)
                        continue
                    with o.condition:
                        if self.identity is not None and o.sources.get(self.identity) is self:o.sources.pop(self.identity,None)
                        self.identity=self.key=None;self.retiring=False;o.condition.notify_all()
                        if o.closed:return
                    continue
                try:self.process(job)
                except InterruptedError as exc:
                    with o.condition:
                        if self.valid(job):o.layers[self.identity]['waiting']=str(exc)
                except Exception as exc:
                    # Preserve the primary failure; cleanup diagnostics are a
                    # separate bounded ledger. Never fail a new transport epoch.
                    with o.condition:
                        if self.valid(job):
                            s=o.layers[self.identity];s['error']=str(exc)[:240];s['error_stamp']=job['stamp'];s['playing']=False;s['mode']='failed';o.failed+=1
                        else:o.stale+=1
                    if self.decoder:
                        self.decoder_needs_close=True
                        try:self.decoder.close()
                        except Exception as cleanup:
                            with o.condition:o.cleanup_errors=(o.cleanup_errors+[str(cleanup)])[-8:]
                        else:self.decoder=None;self.decoder_needs_close=False
                finally:
                    with o.condition:
                        self.metrics_update(in_flight=False,sprite_frame_temporary=0);self.active=None;o.condition.notify_all()
        finally:self.dispose()

class MediaFrames:
    def __init__(self):
        self.condition=threading.Condition();self.closed=False;self.layers={};self.sources={};self.results={};self.frozen=False
        self.plane_budget=PlaneBudget();self.staging_bytes=0;self.cleanup_errors=[];self.coalesced=0;self.stale=0;self.failed=0;self.published=0;self.serial=0
        self.lanes=[SourceLane(self,i) for i in range(MAX_ANIMATIONS)]
        self.thread=threading.Thread(target=self.run,name='Studio media scheduler',daemon=True);self.thread.start()
    def advance(self,state,now):
        if state['playing'] and state['visible'] and not self.frozen and not state.get('release'):state['elapsed']+=max(0.,now-state['at'])
        state['at']=now;setting=state['settings'];end=state.get('ping_end',setting['end']) if setting['loop']=='Ping-pong' else setting['end']
        base_direction=setting.get('direction',1)
        state['position'],done=timeline(state['elapsed'],setting['start'],end,setting['rate'],setting['loop'],base_direction)
        if state.get('step_request'):state['position']=state['step_request']['anchor']
        span=max(1e-9,end-setting['start']);phase=max(0.,state['elapsed'])*setting['rate'];turn=int(phase/span) if setting['loop'] in ('Ping-pong','Loop') else 0
        state['direction']=base_direction*(-1 if setting['loop']=='Ping-pong' and turn%2 else 1);state['turn']=turn
        if done and state['playing']:state['playing']=False;state['mode']='ended'
    def stamp(self,s):return (s['key'],s['generation'],s['epoch'],s['direction'],s['turn'])
    def sync(self,scene,assets,apply=True):
        from composition import effective
        proposals=[];clock=time.perf_counter()
        for row in scene['layers']:
            if row['type'] not in ('Video','GIF','Sprite'):continue
            asset=assets.get(row['asset'])
            if not asset or asset.get('status')!='Ready':continue
            meta=asset.get('metadata',{});key=(asset['id'],asset['path'],meta.get('mtime_ns'),row['type'])
            duration=meta.get('duration',1.) if row['type']!='Sprite' else (row['media']['last']-row['media']['first']+1)/row['media']['fps']
            settings=deepcopy(row['media']);settings['end']=min(settings['end'] or duration,duration)
            if settings['start']>=settings['end']:raise ValueError('Video in point must precede its available out point.')
            visible=effective(scene,row,'enabled') and scene['presentation']!='World only'
            if row['type']=='Sprite' and (meta.get('width',0)<settings['columns'] or meta.get('height',0)<settings['rows']):raise ValueError('Sprite grid cells must contain pixels.')
            proposals.append((row,asset,key,settings,visible,meta))
        visible=[p for p in proposals if p[4]]
        if len(visible)>MAX_ANIMATIONS:raise ValueError('At most 4 visible animated layers; hide one before adding another.')
        if sum(p[5].get('width',0)*p[5].get('height',0)*8 for p in visible)>MAX_STAGING_BYTES:raise ValueError('Animated shared staging exceeds 128 MiB; hide a source before adding another.')
        if not apply:return
        with self.condition:
            if self.closed:return
            candidates={}
            for row,asset,key,settings,visible,meta in proposals:
                old=self.layers.get(row['id'])
                if old:self.advance(old,clock)
                changed=old is None or old['key']!=key or old['settings']!=settings or old['visible']!=visible
                state=old if not changed else deepcopy(old) if old and old['key']==key else dict(key=key,path=asset['path'],type=row['type'],playing=False,elapsed=0.,at=clock,error='',waiting='',position=settings['start'],mode='paused',direction=1,turn=0)
                if changed:
                    rate_only=bool(old and old['key']==key and old['visible']==visible and all(old['settings'][k]==settings[k] for k in settings if k!='rate'))
                    if old and old['key']==key and old['settings']!=settings:
                        same_range=all(old['settings'].get(k,1)==settings.get(k,1) for k in ('start','end','loop','direction'))
                        position=max(settings['start'],min(state['position'],settings['end']))
                        state['elapsed']=old['elapsed']*old['settings']['rate']/settings['rate'] if same_range else elapsed_at(settings,position)
                        if not same_range:state.pop('ping_end',None)
                    state['at']=clock;state['epoch']=token();state.pop('error_stamp',None);state['error']='';state['waiting']='';state.pop('step_request',None);state.pop('seek_resume',None);state['seek_pending']=False
                    if not rate_only:state['generation']=token();self.results.pop(row['id'],None)
                state['settings']=settings;state['visible']=visible;state['sprite']=deepcopy(row['media']);sar=meta.get('pixel_aspect',1.)
                state['cache_weight']=max(1,meta.get('decoded_plane_bytes') or meta.get('width',1)*meta.get('height',1))
                state['pixel_aspect']=1/sar if meta.get('rotation',0) in (90,270) else sar;candidates[row['id']]=state
            for identity in set(self.layers)-set(candidates):self.results.pop(identity,None)
            self.layers=candidates;self.condition.notify_all()
    def reset(self):
        with self.condition:self.layers={};self.results={};self.condition.notify_all()
    def command(self,identity,op,value=None,source=None):
        with self.condition:
            if self.closed:raise ValueError('Media service is closing.')
            if identity not in self.layers:raise ValueError('Animation source is unavailable.')
            s=self.layers[identity]
            if source is not None and list(s['key'])!=source:raise ValueError('Animation command belongs to an obsolete source.')
            if op=='cancel_resume':s.pop('seek_resume',None);return
            if op not in ('play','pause','stop','seek','scrub','step'):raise ValueError('Unsupported animation transport.')
            if op=='step':
                value=value.get('count') if isinstance(value,dict) else value
                if type(value) is not int or not -64<=value<=64 or value==0:raise ValueError('Frame step count must be a nonzero integer within 64.')
                prior=s.get('step_request')
                if abs((prior['count'] if prior else 0)+value)>64:raise ValueError('Frame navigation is busy; wait for the pending frame.')
            if op in ('seek','scrub'):
                target=float(value['position'] if isinstance(value,dict) else value)
                if not math.isfinite(target):raise ValueError('Seek position must be finite.')
            now=time.perf_counter();self.advance(s,now);s['epoch']=token();s.pop('error_stamp',None);s['error']='';s['waiting']='';s.pop('seek_resume',None)
            if op=='play':
                if s['mode']=='ended' or s['settings'].get('direction',1)<0 and s['position']<=s['settings']['start']:s['elapsed']=0.
                s['playing']=True;s['mode']='playing';s['at']=now;s.pop('release',None);s.pop('release_decoder',None);s.pop('step_request',None);s['seek_pending']=False
            elif op=='pause':s['playing']=False;s['mode']='paused'
            elif op=='stop':s['playing']=False;s['mode']='stopped';s['elapsed']=elapsed_at(s['settings'],s['settings']['start'],s.get('ping_end'));s['position']=s['settings']['start'];s['generation']=token();s['release_decoder']=True;s.pop('step_request',None);s['seek_pending']=False;self.results.pop(identity,None)
            elif op in ('seek','scrub'):
                target=max(s['settings']['start'],min(target,s['settings']['end']));s['elapsed']=elapsed_at(s['settings'],target,s.get('ping_end'));s['position']=target;s['at']=now;s['generation']=token();self.results.pop(identity,None);s.pop('release_decoder',None);s.pop('step_request',None);s['seek_pending']=True
                if op=='scrub':s['playing']=False;s['seek_resume']=bool(isinstance(value,dict) and value.get('final') and value.get('resume'))
                if not s['playing']:s['mode']='paused'
            elif op=='step':
                prior=s.get('step_request');anchor=prior['anchor'] if prior else (self.results.get(identity) or {}).get('pts',s['position']);count=(prior['count'] if prior else 0)+value
                s.update(playing=False,mode='paused',seek_pending=True,step_request=dict(anchor=anchor,count=count),generation=token());self.results.pop(identity,None);s.pop('release_decoder',None)
            lane=self.sources.get(identity)
            if lane:
                if lane.active:lane.active['cancel'].set();lane.active['prefetch_cancel'].set()
                if lane.pending:lane.pending['cancel'].set();lane.pending=None
            self.condition.notify_all()
    def freeze(self,active):
        with self.condition:
            if self.frozen==bool(active):return
            for s in self.layers.values():self.advance(s,time.perf_counter());s['epoch']=token()
            self.frozen=bool(active);self.condition.notify_all()
    def stop(self):
        with self.condition:
            for s in self.layers.values():self.advance(s,time.perf_counter());s['playing']=False;s['release']=True;s['mode']='cancelled';s['epoch']=token()
            self.results={};self.condition.notify_all()
    def snapshot(self):
        with self.condition:
            now=time.perf_counter();result={}
            for identity,s in self.layers.items():
                self.advance(s,now);frame=self.results.get(identity);lag=abs(s['position']-frame['pts']) if frame else None;held=bool(frame and (s['error'] or not frame.get('ready_at_request',True) or lag>.1))
                status='cancelled' if self.closed or s.get('release') or not s['visible'] else 'failed' if s['error'] else 'waiting' if frame is None or s['playing'] and not self.frozen and held else 'paused' if self.frozen else s['mode']
                result[identity]=dict(playing=s['playing'],position=s['position'],duration=s['settings']['end'],source=list(s['key']),seek_pending=s.get('seek_pending',False),step_pending=deepcopy(s.get('step_request')),error=s['error'],waiting=s['waiting'],state=status,transport=s['mode'],direction=s['direction'],generation=s['generation'],epoch=s['epoch'],turn=s['turn'],frame=deepcopy(frame),silent=True,
                    held=held,lag_seconds=lag,last_good_policy='Only this visible source and generation; when decoding lags, best cached floor (nearest for ping-pong) may replace a farther last-good image, explicitly held, not ready at requested time. Paused/seek demands stay exact.')
            return result
    def resources(self):
        with self.condition:
            rows=[]
            for lane in self.lanes:
                decoder=dict(lane.decoder.metrics) if lane.decoder else {}
                rows.append(dict(lane.metrics,lane=lane.index,identity=lane.identity,retiring=lane.retiring,in_flight=lane.active is not None,pending=lane.pending is not None,worker_alive=lane.thread.is_alive(),decoder=decoder))
            return dict(route='PyAV/FFmpeg native software codecs; bounded Python scheduling',lanes=rows,
                decoded_planes_bytes=self.plane_budget.used,peak_decoded_planes_bytes=self.plane_budget.peak,cache_budget=MAX_CACHE_BYTES,
                converted_rgba_bytes=sum(r['decoder'].get('converted_rgba',0) for r in rows),decode_temporary_planes_bytes=sum(r['decoder'].get('decode_temporary_planes',0) for r in rows),conversion_temporary_bytes=sum(r['decoder'].get('conversion_temporaries',0) for r in rows),
                shared_slots_bytes=self.staging_bytes,shared_header_bytes=sum(HEADER for lane in self.lanes if lane.shm),sprite_sheet_bytes=sum(r.get('sprite_sheet',0) for r in rows),sprite_conversion_temporary_bytes=sum(r.get('sprite_frame_temporary',0) for r in rows),peak_sprite_frame_bytes=sum(r.get('sprite_frame_peak',0) for r in rows),staging_budget=MAX_STAGING_BYTES,
                jobs=sum(r['in_flight'] for r in rows),pending=sum(r['pending'] for r in rows),retiring=sum(r['retiring'] and r['worker_alive'] and r['identity'] is not None for r in rows),published=self.published,coalesced=self.coalesced,stale=self.stale,failed=self.failed,cleanup_errors=list(self.cleanup_errors),
                temporary_bound='At most one incoming native plane and two full RGBA buffers per lane for native publication, three for owned transparent/rotated Qt publication, plus row-sized alpha scratch; codec-internal references/FFmpeg queues and process RSS are separate.',client_accounting='Qt/GL report owned copies/textures and reader handles separately; mappings reference these same shared allocations.')
    def request(self,identity,s,lane,now):
        self.serial+=1
        return dict(identity=identity,state=deepcopy(s),stamp=self.stamp(s),target=s['position'],direction=s['direction'],at=now,serial=self.serial,cancel=threading.Event(),prefetch_cancel=threading.Event(),budget=self.cache_share(s))
    def cache_share(self,state):
        rows=[s for s in self.layers.values() if s['visible'] and not s.get('release')]
        # Equal timestamp capacity per source, weighted by observed native-plane
        # bytes. Equal byte slices made a small clip retain seconds while the
        # large clip retained only a few frames. The aggregate cap is unchanged.
        total=sum(s['cache_weight'] for s in rows)
        return max(1,int(MAX_CACHE_BYTES*state['cache_weight']/max(1,total)))
    def run(self):
        next_tick=time.perf_counter();signature=None
        try:
            while True:
                with self.condition:
                    self.condition.wait(timeout=max(0.,next_tick-time.perf_counter()))
                    if self.closed:break
                    now=time.perf_counter()
                    controls=tuple((i,s['key'],s['generation'],s['epoch'],s['visible'],s.get('release')) for i,s in self.layers.items())
                    if controls==signature and now<next_tick:continue
                    signature=controls;next_tick=now+1/120
                    for s in self.layers.values():self.advance(s,now)
                    current={i:s for i,s in self.layers.items() if s['visible'] and not s.get('release')}
                    for identity,lane in list(self.sources.items()):
                        if identity not in current or lane.key!=current[identity]['key']:
                            self.results.pop(identity,None);lane.retire()
                    for identity,s in current.items():
                        lane=self.sources.get(identity)
                        if lane is None:
                            lane=next((l for l in self.lanes if l.identity is None),None)
                            if lane is None:s['waiting']='Waiting for old decoder work to retire.';continue
                            lane.identity=identity;lane.key=s['key'];self.sources[identity]=lane
                        if lane.retiring:continue
                        stamp=self.stamp(s)
                        if s.get('error_stamp')==stamp:continue
                        trim=bool(lane.decoder and lane.decoder.budget>self.cache_share(s))
                        if (not s['playing'] or self.frozen) and not trim:
                            if lane.last_completed==(stamp,s['position']):continue
                            if lane.active and lane.active['stamp']==stamp and lane.active['target']==s['position']:continue
                            if lane.pending and lane.pending['stamp']==stamp and lane.pending['target']==s['position']:continue
                        lane.submit(self.request(identity,s,lane,now))
        finally:
            with self.condition:
                for lane in self.lanes:lane.retire()
                self.condition.notify_all()
    def begin_close(self):
        with self.condition:
            self.closed=True;self.results={}
            for lane in self.lanes:lane.retire()
            self.condition.notify_all()
    def is_closed(self):return not self.thread.is_alive() and all(not lane.thread.is_alive() for lane in self.lanes)
    def close(self):
        self.begin_close();until=time.perf_counter()+3.
        for t in [self.thread]+[lane.thread for lane in self.lanes]:t.join(timeout=max(0.,until-time.perf_counter()))
        return self.is_closed()
