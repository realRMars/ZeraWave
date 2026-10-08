"""One control-owned, silent animation decoder, shared frames for GL/Qt clients.

Never opens audio streams/output. Four active animated layers, 96 MiB aggregate
reverse windows, 128 MiB shared staging; two buffers per source, latest request
only, generation guards on seek/replace. Reverse decodes bounded GOP windows,
not a clip preload. A pathological GOP is rejected after 512 frames / 2 s work.
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
        if cancel.is_set():raise ValueError('Media operation cancelled.')
        if frame is None:raise ValueError('Decoder returned no video frames.')
        # BT.2020/PQ/HLG need an agreed HDR conversion, not an accidental SDR cast.
        if int(frame.color_trc or 0) in (16,18) or int(frame.colorspace or 0)==9:raise ValueError('HDR video is not supported by this SDR composition path.')
        duration=float(stream.duration*stream.time_base) if stream.duration is not None else float(container.duration/av.time_base) if container.duration else 0.
        if duration<=0 or duration>86400:raise ValueError('A finite video duration up to 24 h is required.')
        sar=float(stream.sample_aspect_ratio or 1);rotation=int(getattr(frame,'rotation',0) or stream.metadata.get('rotate',0))%360
        if rotation not in (0,90,180,270):raise ValueError('Only right-angle source orientation is supported.')
        return dict(width=codec.width,height=codec.height,duration=duration,codec=codec.name,
            pixel_aspect=sar,rotation=rotation,fps=float(stream.average_rate or 0),alpha='Decoded RGBA; codec-dependent',
            color='FFmpeg SDR conversion to display-encoded RGB; no HDR',backend='PyAV '+av.__version__,validation='Stream header and first decoded frame; later failures retain the previous frame')

def timeline(elapsed,start,end,rate,loop):
    span=end-start
    if span<=0:return start,False
    t=max(0.,elapsed)*rate
    if loop=='Loop':return start+t%span,False
    if loop=='Ping-pong':
        phase=t%(2*span);return start+(phase if phase<=span else 2*span-phase),False
    return min(end,start+t),t>=span

class DecoderWindow:
    def __init__(self,path,budget):
        av=backend();self.container=av.open(str(path),mode='r',timeout=(2.,2.))
        try:self.stream=self.container.streams.video[0]
        except Exception:self.container.close();raise ValueError('No video stream remains available.')
        self.stream.codec_context.thread_count=2
        self.cache=OrderedDict();self.bytes=0;self.budget=budget;self.iterator=None;self.last=-1.;self.decode_ms=0.;self.seek_count=0
    def rgba(self,frame):
        if frame.width*frame.height>MAX_FRAME_PIXELS:raise ValueError('Decoded frame exceeds 8,388,608 pixels.')
        if int(frame.color_trc or 0) in (16,18) or int(frame.colorspace or 0)==9:raise ValueError('HDR frame conversion is unsupported; previous SDR pixels retained.')
        data=frame.to_ndarray(format='rgba');rotation=int(getattr(frame,'rotation',0) or self.stream.metadata.get('rotate',0))%360
        if rotation:data=np.rot90(data,-rotation//90)
        if np.min(data[:,:,3])<255:
            data=data.copy();data[:,:,:3]=((data[:,:,:3].astype(np.uint16)*data[:,:,3:4].astype(np.uint16)+127)//255).astype(np.uint8)
        return data.shape[1],data.shape[0],data[::-1].tobytes()
    def get(self,target,cancel,last_pts=None,nearest=False):
        total_started=time.perf_counter()
        def converted(key,frame):
            result=(key,None if key==last_pts else self.rgba(frame))
            self.decode_ms=(time.perf_counter()-total_started)*1000
            return result
        keys=list(self.cache)
        # Cache timestamp floor, never estimate frame index from average FPS.
        if keys and keys[0]<=target<=keys[-1]:
            key=min(keys,key=lambda p:abs(p-target)) if nearest else max((p for p in keys if p<=target),default=keys[0]);return converted(key,self.cache[key])
        started=time.perf_counter();forward=self.iterator is not None and self.last<=target<=self.last+.5
        if not forward:
            self.container.seek(max(0,int(target/float(self.stream.time_base))),stream=self.stream,backward=True,any_frame=False)
            self.iterator=iter(self.container.decode(self.stream));self.seek_count+=1;self.cache.clear();self.bytes=0
        floor=max((p for p in self.cache if p<=target),default=None);best=(floor,self.cache[floor]) if floor is not None else None;count=0
        for frame in self.iterator:
            if cancel.is_set():return None
            count+=1
            if count>512 or time.perf_counter()-started>2.:raise ValueError('Video GOP decode exceeds the bounded window; choose a more seekable clip.')
            if frame.pts is None:continue
            pts=float(frame.pts*self.stream.time_base);self.last=pts
            # Decode compressed lead-in without converting/storing discarded
            # frames. Cache span follows bytes and source rate, not clip length.
            pixels=sum(p.buffer_size for p in frame.planes)
            span=max(1/float(self.stream.average_rate or 30),max(1,self.budget//pixels-2)/float(self.stream.average_rate or 30))
            if pts<target-span:continue
            value=frame;size=sum(p.buffer_size for p in frame.planes)
            if size>self.budget:raise ValueError('Frame exceeds the active reverse cache budget.')
            while self.cache and self.bytes+size>self.budget:
                _,old=self.cache.popitem(last=False);self.bytes-=sum(p.buffer_size for p in old.planes)
            self.cache[pts]=value;self.bytes+=size
            if pts<=target:best=(pts,value)
            if pts>target:
                if nearest and (best is None or pts-target<target-best[0]):best=(pts,value)
                else:best=best or (pts,value)
                break
        self.decode_ms=(time.perf_counter()-started)*1000
        if best:return converted(*best)
        if self.cache:
            key=next(reversed(self.cache));return converted(key,self.cache[key])
        raise ValueError('No frame at this video position.')
    def close(self):self.container.close();self.cache.clear();self.bytes=0

class FrameReader:
    """Read-only clients. Header seqlock rejects a concurrent write/old epoch."""
    def __init__(self):self.maps={};self.last={}
    def read(self,descriptor):
        name=descriptor['name'];shm=self.maps.get(name)
        if shm is None:shm=self.maps[name]=SharedMemory(name=name,create=False)
        before=struct.unpack_from('<QQIId',shm.buf,0);sequence,generation,width,height,pts=before
        if not sequence or sequence%2 or generation!=descriptor['generation']:return None
        length=width*height*4
        if width<1 or height<1 or length>descriptor['capacity'] or HEADER+2*descriptor['capacity']>shm.size:raise ValueError('Invalid shared media frame bounds.')
        if self.last.get(name)==sequence:return None
        slot=(sequence//2)%2;data=bytes(shm.buf[HEADER+slot*descriptor['capacity']:HEADER+slot*descriptor['capacity']+length])
        if struct.unpack_from('<Q',shm.buf,0)[0]!=sequence:return None
        self.last[name]=sequence;return dict(width=width,height=height,data=data,pts=pts,sequence=sequence)
    def retain(self,names):
        for name in list(self.maps):
            if name not in names:self.maps.pop(name).close();self.last.pop(name,None)
    def close(self):self.retain(set())

class MediaFrames:
    def __init__(self):
        self.condition=threading.Condition();self.closed=False;self.layers={};self.sources={};self.results={};self.frozen=False
        self.thread=threading.Thread(target=self.run,name='Studio silent animated layers',daemon=True);self.thread.start()
    def sync(self,scene,assets,apply=True):
        from composition import effective
        # Preflight the whole proposal before changing clocks or published frames.
        proposals=[];clock=time.perf_counter()
        for row in scene['layers']:
            if row['type'] not in ('Video','GIF','Sprite'):continue
            asset=assets.get(row['asset'])
            if not asset or asset.get('status')!='Ready':continue
            meta=asset.get('metadata',{});key=(asset['id'],asset['path'],meta.get('mtime_ns'),row['type'])
            duration=asset.get('metadata',{}).get('duration',1.) if row['type']!='Sprite' else (row['media']['last']-row['media']['first']+1)/row['media']['fps']
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
            candidates={}
            for row,asset,key,settings,visible,meta in proposals:
                old=self.layers.get(row['id'])
                changed=old is None or old['key']!=key or old['settings']!=settings or old['visible']!=visible
                state=old if not changed else deepcopy(old) if old and old['key']==key else dict(key=key,path=asset['path'],type=row['type'],playing=False,elapsed=0.,at=clock,error='',position=settings['start'])
                if changed:
                    rate_only=bool(old and old['key']==key and old['visible']==visible and all(old['settings'][k]==settings[k] for k in settings if k!='rate'))
                    if old and old['key']==key and old['settings']!=settings:
                        same_range=all(old['settings'][k]==settings[k] for k in ('start','end','loop'))
                        state['elapsed']=old['elapsed']*old['settings']['rate']/settings['rate'] if same_range else max(0.,state['position']-settings['start'])/settings['rate']
                    state['at']=clock
                    if not rate_only:state['generation']=uuid.uuid4().int&((1<<64)-1);self.results.pop(row['id'],None)
                state['settings']=settings;state['visible']=visible;state['sprite']=deepcopy(row['media']);sar=meta.get('pixel_aspect',1.)
                state['pixel_aspect']=1/sar if meta.get('rotation',0) in (90,270) else sar;candidates[row['id']]=state
            for identity in set(self.layers)-set(candidates):self.results.pop(identity,None)
            self.layers=candidates;self.condition.notify()
    def reset(self):
        with self.condition:self.layers={};self.results={};self.condition.notify()
    def command(self,identity,op,value=None):
        with self.condition:
            if identity not in self.layers:raise ValueError('Animation source is unavailable.')
            s=self.layers[identity];now=time.perf_counter()
            if op=='play':s['playing']=True;s['at']=now;s.pop('release',None);s.pop('release_decoder',None);s.pop('error_generation',None);s['error']=''
            elif op=='pause':s['playing']=False
            elif op=='stop':s['playing']=False;s['elapsed']=0.;s['position']=s['settings']['start'];s['generation']=uuid.uuid4().int&((1<<64)-1);s['release_decoder']=True;self.results.pop(identity,None)
            elif op=='seek':
                target=max(s['settings']['start'],min(float(value),s['settings']['end']));s['elapsed']=(target-s['settings']['start'])/s['settings']['rate'];s['position']=target;s['at']=now;s['generation']=uuid.uuid4().int&((1<<64)-1)
                self.results.pop(identity,None)
            else:raise ValueError('Unsupported animation transport.')
            self.condition.notify()
    def freeze(self,active):
        with self.condition:self.frozen=bool(active);self.condition.notify()
    def stop(self):
        with self.condition:
            for s in self.layers.values():s['playing']=False;s['release']=True
            self.condition.notify()
    def snapshot(self):
        with self.condition:
            return {identity:dict(playing=s['playing'],position=s['position'],duration=s['settings']['end'],error=s['error'],frame=deepcopy(self.results.get(identity)),silent=True) for identity,s in self.layers.items()}
    def release(self,identity):
        source=self.sources.pop(identity,None)
        with self.condition:self.results.pop(identity,None)
        if source:
            if source.get('decoder'):source['decoder'].close()
            source['shm'].close();source['shm'].unlink()
    def run(self):
        cancel=threading.Event()
        try:
            while True:
                with self.condition:
                    self.condition.wait(timeout=1/60)
                    if self.closed:break
                    rows=list(self.layers.items());frozen=self.frozen
                current={i for i,s in rows if s['visible'] and not s.get('release')}
                for i in list(self.sources):
                    if i not in current:self.release(i)
                for identity,state in rows:
                    if identity not in current:state['at']=time.perf_counter();continue
                    now=time.perf_counter()
                    with self.condition:
                        if self.layers.get(identity) is not state:continue
                        if state['playing'] and not frozen:state['elapsed']+=max(0.,now-state['at'])
                        state['at']=now;setting=state['settings'];target,done=timeline(state['elapsed'],setting['start'],setting['end'],setting['rate'],setting['loop']);state['position']=target
                        if done:state['playing']=False
                        generation=state['generation']
                        if state.get('error_generation')==generation:continue
                    source=self.sources.get(identity)
                    try:
                        if source and source['key']!=state['key']:self.release(identity);source=None
                        if source is None:
                            if state['key'][2] is not None and Path(state['path']).stat().st_mtime_ns!=state['key'][2]:raise ValueError('Animated source changed; Refresh it before use.')
                            if state['type']=='Sprite':
                                from media_registry import decode_image
                                meta,data=decode_image(state['path']);image=(meta['width'],meta['height'],data);decoder=None
                                capacity=meta['width']*meta['height']*4
                            else:
                                decoder=DecoderWindow(state['path'],MAX_CACHE_BYTES//max(1,len(current)));image=None
                                c=decoder.stream.codec_context;capacity=c.width*c.height*4
                            if sum(v['capacity']*2 for v in self.sources.values())+capacity*2>MAX_STAGING_BYTES:
                                if decoder:decoder.close()
                                raise ValueError('Animated shared staging exceeds 128 MiB.')
                            shm=SharedMemory(create=True,size=HEADER+capacity*2);shm.buf[:HEADER]=bytes(HEADER)
                            source=self.sources[identity]=dict(key=state['key'],decoder=decoder,image=image,shm=shm,capacity=capacity,sequence=0,last=None)
                        if source['decoder']:
                            budget=MAX_CACHE_BYTES//max(1,len(current));source['decoder'].budget=budget
                            while source['decoder'].cache and source['decoder'].bytes>budget:
                                _,old=source['decoder'].cache.popitem(last=False);source['decoder'].bytes-=sum(p.buffer_size for p in old.planes)
                        elif state['type']!='Sprite':
                            if source.get('still_generation')==generation and not state['playing']:continue
                            source['decoder']=DecoderWindow(state['path'],MAX_CACHE_BYTES//max(1,len(current)))
                        ping=setting['loop']=='Ping-pong'
                        if ping:
                            endpoint_key=(setting['start'],setting['end'])
                            if source.get('endpoint_key')!=endpoint_key:
                                source['ping_end']=(setting['last']-setting['first'])/setting['fps'] if state['type']=='Sprite' else source['decoder'].get(setting['end']-1e-7,cancel)[0];source['endpoint_key']=endpoint_key
                            target,done=timeline(state['elapsed'],setting['start'],max(setting['start'],source['ping_end']),setting['rate'],'Ping-pong')
                            with self.condition:
                                if self.layers.get(identity) is state:state['position']=target
                        if state['type']=='Sprite':
                            index_offset=math.floor(target*setting['fps']+(.5 if ping else 0));pts=index_offset/setting['fps'];w,h,data=source['image'];array=np.frombuffer(data,np.uint8).reshape(h,w,4)[::-1]
                            index=setting['first']+min(setting['last']-setting['first'],index_offset);cw,ch=w//setting['columns'],h//setting['rows'];x=index%setting['columns'];y=index//setting['columns'];rgba=array[y*ch:(y+1)*ch,x*cw:(x+1)*cw][::-1].tobytes();frame=(cw,ch,rgba)
                        else:
                            last_pts=source['last'][0] if source['last'] and source['last'][1]==generation else None
                            value=source['decoder'].get(target,cancel,last_pts=last_pts,nearest=ping)
                            if value is None:continue
                            pts,frame=value
                            if frame is None:continue
                        if source['last']==(pts,generation):continue
                        with self.condition:
                            latest=self.layers.get(identity)
                            if latest is None or latest['key']!=state['key'] or latest['generation']!=generation:continue
                            state=latest # A rate-only edit retains this epoch and valid pixels.
                            w,h,data=frame;capacity=source['capacity'];sequence=source['sequence']+2;slot=(sequence//2)%2
                            struct.pack_into('<Q',source['shm'].buf,0,sequence-1)
                            source['shm'].buf[HEADER+slot*capacity:HEADER+slot*capacity+len(data)]=data
                            struct.pack_into('<QIId',source['shm'].buf,8,generation,w,h,pts)
                            struct.pack_into('<Q',source['shm'].buf,0,sequence)
                            source['sequence']=sequence;source['last']=(pts,generation)
                            self.results[identity]=dict(name=source['shm'].name,generation=generation,capacity=capacity,width=w,height=h,pixel_aspect=state['pixel_aspect'],pts=pts,decode_ms=source['decoder'].decode_ms if source['decoder'] else 0.,cache_bytes=source['decoder'].bytes if source['decoder'] else len(source['image'][2]),seeks=source['decoder'].seek_count if source['decoder'] else 0)
                            state['error']=''
                            if state.get('release_decoder') and source['decoder']:
                                source['decoder'].close();source['decoder']=None;source['still_generation']=generation;self.results[identity]['cache_bytes']=0
                    except Exception as exc:
                        if source and source.get('decoder'):
                            source['decoder'].close();source['decoder']=None
                        with self.condition:
                            state['error']=str(exc)[:240];state['playing']=False;state['error_generation']=generation
        finally:
            for i in list(self.sources):self.release(i)
    def close(self):
        with self.condition:self.closed=True;self.condition.notify()
        self.thread.join(timeout=3.);return not self.thread.is_alive()
