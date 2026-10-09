"""Snapshot-bound paint bucket. Transient regions never use saved-mask encoding.

Similarity is inclusive maximum straight-sRGB RGBA channel difference, 0..255.
Transparent pixels compare as transparent black. Traversal is four-connected by
default and constrained by nonzero crop/mask/selection coverage before flooding.
Writes replace own premultiplied RGBA, interpolated by exact boundary coverage.
Layer master opacity/blending remains presentation state, not baked into pixels.
"""
import math,time,threading
from copy import deepcopy
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage,QColor,QPainter,QTransform
from raster_edit import coverage
from pixel_selection import MAX_PIXELS

_worker=threading.local()

class Progress:
    def __init__(self):self.lock=threading.Lock();self.name='Starting';self.began=time.perf_counter();self.times={}
    def phase(self,name):
        with self.lock:
            now=time.perf_counter();self.times[self.name]=self.times.get(self.name,0)+(now-self.began)*1000;self.name=name;self.began=now
    def snapshot(self):
        with self.lock:return self.name,dict(self.times)

def bucket(image,row,selection,seed,color,tolerance=32,contiguous=True,cancel=None,groups=()):
    began=time.perf_counter();w,h=image.width(),image.height();progress=getattr(_worker,'progress',None)
    def phase(name):
        if progress:progress.phase(name)
    phase('Reading native pixels')
    if not 1<=w<=8192 or not 1<=h<=8192 or w*h>MAX_PIXELS:raise ValueError('Fill exceeds supported native dimensions (8192 / 8 MP).')
    def checkpoint():
        if cancel is not None and cancel.is_set():raise ValueError('Obsolete Fill cancelled; artwork unchanged.')
        if time.perf_counter()-began>30:raise ValueError('Fill exceeded its 30 s computation budget; artwork unchanged.')
    checkpoint();x,y=seed
    if not 0<=x<w or not 0<=y<h:return None
    # Native readers are immutable; QImage copies detach only on worker writes.
    base=image.copy()
    phase('Calculating boundaries')
    mask=coverage((0,0,w,h),(w,h),row,selection)
    # Group coverage is a subtree boundary. Ordinary parents' own masks do not
    # constrain children. Each projected group mask is released before the next.
    for group,mapping in groups:
        checkpoint();local=coverage((0,0,w,h),(w,h),group);projected=QImage(w,h,QImage.Format_ARGB32_Premultiplied);projected.fill(0)
        p=QPainter(projected);p.setRenderHint(QPainter.SmoothPixmapTransform);p.setTransform(QTransform(mapping[0,0],mapping[1,0],mapping[0,1],mapping[1,1],mapping[0,2],mapping[1,2]));p.drawImage(0,0,local);p.end()
        p=QPainter(mask);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,projected);p.end();del local,projected
    ca=np.frombuffer(mask.constBits(),np.uint8).reshape(h,mask.bytesPerLine())[:,3:w*4:4]
    if ca[y,x]==0:return None
    phase('Converting source format')
    rgba=base.convertToFormat(QImage.Format_RGBA8888)
    a=np.frombuffer(rgba.constBits(),np.uint8).reshape(h,rgba.bytesPerLine())[:,:w*4].reshape(h,w,4)
    seed_color=a[y,x].astype(np.int16)
    if seed_color[3]==0:seed_color[:3]=0
    matches=np.empty((h,w),bool)
    phase('Comparing colors')
    for start in range(0,h,64):
        checkpoint();strip=a[start:start+64];target=matches[start:start+64];target[:]=ca[start:start+64]>0
        # Inclusive max-channel distance without a four-channel int16 copy,
        # absolute-distance array and strided reduction at every pixel.
        transparent=strip[:,:,3]==0
        for channel in range(4):
            values=np.where(transparent,0,strip[:,:,channel]) if channel<3 else strip[:,:,3]
            low=int(seed_color[channel])-tolerance;high=int(seed_color[channel])+tolerance
            if low>0:target&=values>=low
            if high<255:target&=values<=high
    del a,rgba,strip
    phase('Tracing connected region')
    if contiguous and not matches.all():
        from native_raster import connected_region
        connected=connected_region(matches,(x,y),cancel,30-(time.perf_counter()-began))
        if connected is not None:matches=connected
        else:
            # Fixed capacity typed stack + scheduled bitmap prevent an unbounded
            # Python tuple queue or repeated enqueues in fragmented large regions.
            output=np.zeros((h,w),bool);queued=np.zeros((h,w),bool);todo=np.empty(w*h,np.int32);count=1;todo[0]=y*w+x;queued[y,x]=True;steps=0
            while count:
                count-=1;py,px=divmod(int(todo[count]),w)
                if output[py,px] or not matches[py,px]:continue
                left=px;right=px+1
                # Vectorized nearest barriers avoid Python per-pixel loops.
                barriers=np.flatnonzero(~matches[py,:px] | output[py,:px])
                left=int(barriers[-1])+1 if len(barriers) else 0
                barriers=np.flatnonzero(~matches[py,px+1:] | output[py,px+1:])
                right=px+1+int(barriers[0]) if len(barriers) else w
                output[py,left:right]=True;steps+=1
                if steps%64==0:checkpoint()
                for ny in (py-1,py+1):
                    if 0<=ny<h:
                        runs=matches[ny,left:right]&~output[ny,left:right]
                        starts=np.flatnonzero(runs&~np.r_[False,runs[:-1]])+left
                        starts=starts[~queued[ny,starts]];queued[ny,starts]=True
                        todo[count:count+len(starts)]=ny*w+starts;count+=len(starts)
            matches=output;del queued,todo,output
    checkpoint()
    if not matches.any():return None
    phase('Constructing changed tiles')
    # Write only changed tile regions; unchanged native tiles remain shared.
    paint=QImage(1,1,QImage.Format_ARGB32_Premultiplied);paint.fill(QColor(color));pixel=np.frombuffer(paint.constBits(),np.uint8).copy()
    from native_raster import NativeImage,backend,native_constrained
    fast=backend().status()['constraint_kernel'];paint_tiles={}
    native=isinstance(image,NativeImage);patches=[];result=None if native else base.copy();changed=False
    for top in range(0,h,128):
        checkpoint()
        for left in range(0,w,128):
            rh,rw=min(128,h-top),min(128,w-left);region=matches[top:top+rh,left:left+rw]
            if not region.any():continue
            bounds=(left,top,rw,rh);part=base.copy(*bounds);before=np.frombuffer(part.constBits(),np.uint8).reshape(rh,part.bytesPerLine())[:,:rw*4].reshape(rh,rw,4).copy()
            alpha=ca[top:top+rh,left:left+rw]*region
            if fast:
                # Reuse the established exact ABI-1 constraint kernel on bounded
                # tiles; never allocate another whole-source paint/coverage image.
                key=(rw,rh)
                if key not in paint_tiles:
                    solid=QImage(rw,rh,QImage.Format_ARGB32_Premultiplied);solid.fill(QColor(color));paint_tiles[key]=solid
                tile_mask=QImage(rw,rh,QImage.Format_ARGB32_Premultiplied);tile_mask.fill(0)
                np.frombuffer(tile_mask.bits(),np.uint8).reshape(rh,rw,4)[:,:,3]=alpha
                after_image=native_constrained(part,paint_tiles[key],tile_mask,1.)
                after=np.frombuffer(after_image.constBits(),np.uint8).reshape(rh,rw,4)
            else:
                alpha=alpha.astype(np.uint16)[:,:,None]
                # Exhaustive byte/coverage parity: denominator255 has no half
                # tie; integer weights match reference float32 nearest-even rint.
                after=((before.astype(np.uint16)*(255-alpha)+pixel.astype(np.uint16)*alpha+127)//255).astype(np.uint8)
            if np.array_equal(before,after):continue
            changed=True
            target=np.frombuffer(part.bits(),np.uint8).reshape(rh,part.bytesPerLine())[:,:rw*4].reshape(rh,rw,4);target[:]=after
            if native:patches.append((bounds,part))
            else:
                dst=np.frombuffer(result.bits(),np.uint8).reshape(h,result.bytesPerLine())[:,:w*4].reshape(h,w,4);dst[top:top+rh,left:left+rw]=after
    checkpoint()
    phase('Installing immutable tiles')
    if native:return image.patch_many(patches) if patches else None
    return result if changed else None

class PreparedFill:
    def __init__(self,image):self.image=image;self.source=None;self.transfer=None
    def take_source(self):value,self.source=self.source,None;return value
    def take_image(self):value,self.transfer=self.transfer,None;return value
    def discard(self):
        from raster_resources import release
        for pair in (self.source,self.transfer):
            if pair:release(pair[1])
        self.source=None;self.transfer=None

def prepare(args,retain_source,progress=None):
    _worker.progress=progress
    try:result=bucket(*args)
    finally:_worker.progress=None
    if result is None:return None
    if progress:progress.phase('Preparing immutable snapshots')
    prepared=PreparedFill(result)
    from raster_resources import snapshot
    from native_raster import NativeImage
    try:
        if args[7].is_set():raise ValueError('Obsolete Fill cancelled before snapshot preparation.')
        if retain_source:
            prepared.source=snapshot(args[0])
            if isinstance(result,NativeImage):result.names.update(args[0].names)
        prepared.transfer=snapshot(result)
        if args[7].is_set():raise ValueError('Obsolete Fill cancelled during snapshot preparation.')
        if progress:progress.phase('Awaiting GUI delivery')
        return prepared
    except BaseException:prepared.discard();raise

class FillController:
    def __init__(self,e):
        self.e=e;self.job=None;self.cancel_event=None;self.ticket=None;self.generation=0;self.metrics=[]
        self.timer=QTimer(e);self.timer.setInterval(16);self.timer.timeout.connect(self.poll);self.timer.start()
    def cancel(self):
        self.generation+=1
        if self.cancel_event:self.cancel_event.set()
    def close(self):
        self.cancel();self.timer.stop()
        if self.job is not None:
            def retire(job):
                try:
                    prepared=job.result()
                    if prepared is not None:prepared.discard()
                except Exception:pass
            self.job.add_done_callback(retire)
    def click(self,pos):
        e=self.e;c=e.canvas;row=e.selected_row()
        if self.job is not None:e.status.setText('Fill calculation pending; wait or change target/tool to cancel.');return
        if not row or row['type'] not in ('Image','Artwork','Paint'):e.status.setText('Fill requires the selected editable raster layer.');return
        if not e.editable_target(row) or not row['source_visible']:
            if not row['source_visible']:e.status.setText('Show selected own content before Fill.')
            return
        if e.edit_jobs or e.art_jobs:e.status.setText('Wait for preceding edit acceptance before Fill.');return
        image=c.source_image(row)
        if image is None:e.status.setText('Wait for native source pixels before Fill.');return
        if c.points and getattr(c,'pixel_selection_ready',False) and not e.pixel_editor.readable(False):return
        uv=c.mask_point(row,pos,clamp=False);seed=(math.floor(uv[0]*image.width()),math.floor(uv[1]*image.height()))
        if not 0<=seed[0]<image.width() or not 0<=seed[1]<image.height():e.status.setText('Click inside selected artwork.');return
        from native_raster import FillCancel
        self.cancel_event=FillCancel();selection=deepcopy(c.operation()) if c.points else None;target=deepcopy(row);binding=e.binding;scene=deepcopy(e.config)
        q=e.quick_colors;color=QColor(e.brush_color);args=(image if hasattr(image,'tiles') else image.copy(),target,selection,seed,color,q.tolerance.value(),q.contiguous.isChecked(),self.cancel_event)
        from composition import ancestors,world_matrix
        from editor_colors import pixel_frame
        groups=[];inverse=None
        for group in ancestors(e.config,row['id']):
            if group['type']!='Group' or not group['masks'] and group['crop']==[0.,0.,1.,1.]:continue
            if inverse is None:inverse=np.linalg.inv(pixel_frame(c,row,image))
            uv=np.array([[1/image.width(),0.,-.5],[0.,1/image.height(),-.5],[0.,0.,1.]])
            groups.append((deepcopy(group),inverse@world_matrix(e.config,group['id'])@uv))
        args=(*args,groups)
        original=next((a for a in e.media_assets() if a['id']==row['asset']),None);retain_source=bool(original and 'runtime' not in original)
        cost=image.sizeInBytes()*(2 if retain_source else 1)
        if sum(p.size for p in e.runtime_producers.values())+cost>128*1024*1024:e.status.setText('Fill snapshot reservation exceeds 128 MiB; prior artwork retained.');return
        self.ticket=(self.generation,binding,target,image,scene,selection,time.perf_counter());self.progress=Progress();self.last_phase=None;self.job=e.pool.submit(prepare,args,retain_source,self.progress);e.status.setText('Calculating Fill on selected own pixels… artwork unchanged; target/tool change cancels.')
    def poll(self):
        if self.job is None:return
        if not self.job.done():
            phase,_=self.progress.snapshot()
            if phase!=self.last_phase:
                self.last_phase=phase;self.e.status.setText('Fill: '+phase+'… artwork unchanged; target/tool change cancels.')
            return
        job,self.job=self.job,None;e=self.e;c=e.canvas;generation,binding,row,image,scene,selection,began=self.ticket;self.ticket=None
        valid=generation==self.generation and e.binding==binding and e.selected==row['id'] and e.config==scene and c.tool=='Fill' and c.source_image(row) is image and (deepcopy(c.operation()) if c.points else None)==selection and e.valid_target(*binding,row)
        prepared=None
        try:
            prepared=job.result()
            if not valid:e.status.setText('Obsolete Fill ignored; artwork unchanged.');return
            if prepared is None:e.status.setText('Fill unchanged or outside permitted coverage; no history added.');return
            stroke=dict(row=row['id'],asset=row['asset'],target=row,session=binding[0],revision=binding[1],tool='Fill',base=image)
            if not e.save_paint(stroke,prepared.image,prepared=prepared):return
            self.metrics.append(dict(dimensions=[image.width(),image.height()],compute_to_submit_ms=(time.perf_counter()-began)*1000,phases_ms=self.progress.snapshot()[1]));self.metrics=self.metrics[-32:]
        except Exception as exc:e.status.setText('Fill retained previous artwork: '+str(exc)[:180])
        finally:
            if prepared is not None:prepared.discard()
