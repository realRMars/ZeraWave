"""ABI-1 ctypes adapter: immutable versions; batched region calls, no pixel policy.

Contexts/handles/pointers are process-local. Only raster_tiles' named immutable
Windows mappings cross processes. DLL choice is fixed for this process lifetime.
"""
from pathlib import Path
from collections import OrderedDict
import ctypes as C,hashlib,os,threading,weakref,uuid
from PySide6.QtCore import QRect,QSize,Qt
from PySide6.QtGui import QImage

class Error(C.Structure):_fields_=[('code',C.c_int32),('message',C.c_char*252)]
class Region(C.Structure):_fields_=[('x',C.c_uint32),('y',C.c_uint32),('width',C.c_uint32),('height',C.c_uint32),('stride',C.c_uint64),('length',C.c_uint64),('data',C.c_void_p)]
class Tile(C.Structure):_fields_=[('id',C.c_uint64),('x',C.c_uint32),('y',C.c_uint32),('width',C.c_uint32),('height',C.c_uint32),('length',C.c_uint64),('data',C.c_void_p)]
class Stats(C.Structure):_fields_=[(k,C.c_uint64) for k in ('bytes','peak_bytes','versions','tiles','copied_bytes','read_bytes')]

class Backend:
    def __init__(self):
        directory=Path(__file__).resolve().parents[2]/'work/native-raster/x64';candidate=directory/'abi1-fill-20261009-v2/zerawave_raster.dll'
        if not candidate.is_file():candidate=directory/'abi1-completion/zerawave_raster.dll'
        self.dll=None;self.reason='';self.core=None;self.lock=threading.RLock();self.path=Path(os.environ.get('ZERAWAVE_RASTER_DLL') or (candidate if candidate.is_file() else directory/'abi1/zerawave_raster.dll'))
        try:
            if os.environ.get('ZERAWAVE_RASTER_BACKEND','auto').lower()=='b1':raise OSError('B1 compatibility explicitly selected at project open')
            if C.sizeof(C.c_void_p)!=8:raise OSError('Native raster requires 64-bit Python')
            dll=C.CDLL(str(self.path));u=C.c_uint32;v=C.c_uint64;p=C.c_void_p;e=C.POINTER(Error)
            signatures={'zw_abi':[C.POINTER(u)]*3,'zw_open':[v,C.POINTER(p),e],'zw_close':[p,e],'zw_limit':[p,v,e],'zw_create':[p,u,u,p,v,v,C.POINTER(v),e],'zw_import':[p,u,u,C.POINTER(Tile),u,C.POINTER(v),e],'zw_patch':[p,v,C.POINTER(Region),u,C.POINTER(v),e],'zw_retain':[p,v,e],'zw_release':[p,v,e],'zw_read':[p,v,C.POINTER(Region),u,e],'zw_tiles':[p,v,C.POINTER(Tile),u,C.POINTER(u),e],'zw_stats':[p,C.POINTER(Stats),e],'zw_add':[p,p,p,v,e]}
            for name,args in signatures.items():f=getattr(dll,name);f.argtypes=args;f.restype=C.c_int32
            if hasattr(dll,'zw_constrain'):dll.zw_constrain.argtypes=[p,p,p,p,v,C.c_double,e];dll.zw_constrain.restype=C.c_int32
            if hasattr(dll,'zw_connected'):dll.zw_connected.argtypes=[p,v,u,u,u,u,p,v,C.POINTER(C.c_int32),C.c_double,e];dll.zw_connected.restype=C.c_int32
            if hasattr(dll,'zw_cancel'):dll.zw_cancel.argtypes=[C.POINTER(C.c_int32),C.c_int32,e];dll.zw_cancel.restype=C.c_int32
            abi=u();side=u();bits=u()
            if dll.zw_abi(C.byref(abi),C.byref(side),C.byref(bits)) or (abi.value,side.value,bits.value)!=(1,128,64):raise OSError('Incompatible raster ABI/tile/architecture')
            self.dll=dll;self.reason='Native tiles ABI 1 / 128 px / x64'
        except (OSError,AttributeError) as exc:self.reason='B1 fallback: '+str(exc)[:200]
    @property
    def available(self):return self.dll is not None
    def storage(self):
        with self.lock:
            if not self.available:raise ValueError(self.reason)
            if self.core is None:self.core=Core(self,384*1024*1024)
            return self.core
    def status(self):return dict(backend='native' if self.available else 'b1',message=self.reason,path=str(self.path),abi=1 if self.available else None,constraint_kernel=bool(self.dll and hasattr(self.dll,'zw_constrain')),fill_kernel=bool(self.dll and hasattr(self.dll,'zw_connected') and hasattr(self.dll,'zw_cancel')),presentation_bytes=_display_bytes,presentation_limit=512*1024*1024)

_backend=None
_backend_lock=threading.RLock()
def backend():
    global _backend
    with _backend_lock:
        if _backend is None:_backend=Backend()
        return _backend

class Core:
    def __init__(self,selection=None,limit=384*1024*1024):
        self.selection=selection or backend();self.dll=self.selection.dll;self.context=C.c_void_p();self.lock=threading.RLock();self.import_names={}
        self.call('zw_open',limit,C.byref(self.context))
    def call(self,name,*args):
        error=Error();code=getattr(self.dll,name)(*args,C.byref(error))
        if code:raise MemoryError(error.message.decode('utf8','replace')) if code==2 else ValueError(error.message.decode('utf8','replace'))
    def stats(self):
        result=Stats();self.call('zw_stats',self.context,C.byref(result));return {k:getattr(result,k) for k,_ in Stats._fields_}
    def close(self):self.call('zw_close',self.context);self.context=None
    def from_image(self,image):
        canonical=image.convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True)
        if canonical.isNull():raise MemoryError('Native source conversion failed')
        pointer=C.c_uint8.from_buffer(canonical.bits());out=C.c_uint64()
        self.call('zw_create',self.context,canonical.width(),canonical.height(),C.addressof(pointer),canonical.sizeInBytes(),canonical.bytesPerLine(),C.byref(out))
        try:
            display=Display(image.copy());display.spare=Display(image.copy())
            result=NativeImage(self,out.value,image.width(),image.height(),display=display,family=uuid.uuid4().hex);display.spare.stamps=display.stamps;return result
        except BaseException:
            self.call('zw_release',self.context,out.value);raise
    def import_tiles(self,desc,leases):
        table=(Tile*len(desc['tiles']))();pointers=[];pointer=None
        try:
            for i,(t,lease) in enumerate(zip(desc['tiles'],leases)):
                identity=int.from_bytes(hashlib.sha256(t['name'].encode()).digest()[:8],'little') or 1
                if identity in self.import_names and self.import_names[identity]!=t['name']:raise ValueError('Transfer tile identity collision')
                if identity not in self.import_names and len(self.import_names)>=262144:raise MemoryError('Transfer identity table reached its fixed bound')
                self.import_names[identity]=t['name'];pointer=C.c_uint8.from_buffer(lease.buf);pointers.append(pointer)
                table[i]=Tile(identity,t['x'],t['y'],t['width'],t['height'],t['bytes'],C.addressof(pointer))
            out=C.c_uint64();self.call('zw_import',self.context,desc['width'],desc['height'],table,len(table),C.byref(out))
            result=NativeImage(self,out.value,desc['width'],desc['height'],family=desc['family']);result.names={t.id:d['name'] for t,d in zip(result.tiles(),desc['tiles'])};return result
        finally:
            pointer=None;pointers.clear();table=None


_displays=weakref.WeakValueDictionary()
_display_bytes=0
_display_lock=threading.RLock()
class Display:
    def __init__(self,image=None):
        self.image=None;self.size=0;self.stamps=();self.lock=threading.RLock();self.copied=0;self.spare=None;self.refresh_regions=0
        if image is not None:self.install(image)
    def install(self,image):
        global _display_bytes
        size=image.sizeInBytes()
        with _display_lock:
            if image.isNull() or _display_bytes-self.size+size>512*1024*1024:raise MemoryError('Qt family presentation cache exceeds 512 MiB; accepted storage retained')
            _display_bytes+=size-self.size;self.size=size;self.image=image
    def __del__(self):
        global _display_bytes
        with _display_lock:_display_bytes-=getattr(self,'size',0)

class NativeImage:
    """Qt-compatible access for broad operations; region reads on interactive paths.

    The mutable display cache is presentation only, never a document snapshot.
    Each committed version owns immutable C++ tile references independently.
    """
    def __init__(self,core,handle,w,h,family=None,display=None,names=None):
        self.core,self.handle,self.w,self.h=core,handle,w,h;self.family=family or uuid.uuid4().hex;self.names=names if names is not None else {};self._table=None;self._pin=None
        self.display=display or _displays.get(self.family) or Display();_displays[self.family]=self.display
        self._refresh_base=None;self._dirty_rect=None
        if display and display.image is not None and not display.stamps:self.display.stamps=tuple(t.id for t in self.tiles())
    def __del__(self):
        if getattr(self,'handle',None):
            try:self.core.call('zw_release',self.core.context,self.handle)
            except Exception:pass
            self.handle=None
    def private_view(self):
        # Cold decode prepares a second full Qt presentation surface. Drawing
        # updates it by tiles while unchanged aliases keep their original view.
        # No full presentation copy is made at gesture start or per segment.
        display=self.display.spare or self.display
        self.core.call('zw_retain',self.core.context,self.handle)
        return NativeImage(self.core,self.handle,self.w,self.h,self.family,display,self.names)
    def width(self):return self.w
    def height(self):return self.h
    def size(self):return QSize(self.w,self.h)
    def isNull(self):return False
    def sizeInBytes(self):return self.w*self.h*4
    def cacheKey(self):return self.handle
    def bytesPerLine(self):return self.w*4
    def tiles(self):
        if self._table is None:
            count=(self.w+127)//128*((self.h+127)//128);self._table=(Tile*count)();n=C.c_uint32();self.core.call('zw_tiles',self.core.context,self.handle,self._table,count,C.byref(n))
        return self._table
    def stamp(self,bounds):
        x,y,w,h=bounds
        if w<=0 or h<=0:return ()
        x0,x1=max(0,int(x)//128),min((self.w-1)//128,int(x+w-1)//128);bottom=self.h-y-h
        y0,y1=max(0,int(bottom)//128),min((self.h-1)//128,int(bottom+h-1)//128);columns=(self.w+127)//128;table=self.tiles()
        return tuple(table[i*columns+j].id for i in range(y0,y1+1) for j in range(x0,x1+1))
    def region(self,bounds):
        x,y,w,h=map(int,bounds)
        if min(x,y)<0 or w<1 or h<1 or x+w>self.w or y+h>self.h:raise ValueError('Native region outside source')
        image=QImage(w,h,QImage.Format_RGBA8888_Premultiplied);pointer=C.c_uint8.from_buffer(image.bits());r=Region(x,self.h-y-h,w,h,image.bytesPerLine(),image.sizeInBytes(),C.addressof(pointer))
        self.core.call('zw_read',self.core.context,self.handle,C.byref(r),1)
        return image.mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied)
    def patch(self,bounds,image):return self.patch_many([(bounds,image)])
    def patch_many(self,regions):
        table=(Region*len(regions))();buffers=[];pointers=[]
        for i,(bounds,image) in enumerate(regions):
            x,y,w,h=map(int,bounds);canonical=image.convertToFormat(QImage.Format_RGBA8888_Premultiplied).mirrored(False,True);buffers.append(canonical);pointer=C.c_uint8.from_buffer(canonical.bits());pointers.append(pointer)
            if (canonical.width(),canonical.height())!=(w,h):raise ValueError('Patch dimensions changed')
            table[i]=Region(x,self.h-y-h,w,h,canonical.bytesPerLine(),canonical.sizeInBytes(),C.addressof(pointer))
        out=C.c_uint64();self.core.call('zw_patch',self.core.context,self.handle,table,len(table),C.byref(out))
        result=NativeImage(self.core,out.value,self.w,self.h,self.family,self.display,self.names)
        # A presentation delta is valid only against its exact predecessor.
        # Keep IDs/geometry, never a chain of retained native version handles.
        # Skipped paints accumulate one rectangle; unrelated/older readers use
        # the conservative tile path below instead of applying stale damage.
        base=self.display.stamps
        if self._refresh_base==base and self._dirty_rect is not None:
            bounds=[self._dirty_rect]+[r[0] for r in regions]
        elif self._table is not None and base==tuple(t.id for t in self._table):bounds=[r[0] for r in regions]
        else:bounds=[]
        if bounds:
            x=min(b[0] for b in bounds);y=min(b[1] for b in bounds);right=max(b[0]+b[2] for b in bounds);bottom=max(b[1]+b[3] for b in bounds)
            result._refresh_base=base;result._dirty_rect=(x,y,right-x,bottom-y)
        return result
    def materialize(self):
        with self.display.lock:
            ids=tuple(t.id for t in self.tiles());cache=self.display
            if cache.image is None:cache.install(self.region((0,0,self.w,self.h)));cache.copied+=self.w*self.h*4
            elif cache.stamps!=ids:
                from PySide6.QtGui import QPainter
                if self._refresh_base==cache.stamps and self._dirty_rect is not None:regions=[self._dirty_rect]
                else:
                    # Coalesce neighbouring changed tiles for readers which
                    # switched revisions, including pinned older PNG workers.
                    changed=sorted((t for i,t in enumerate(self.tiles()) if i>=len(cache.stamps) or cache.stamps[i]!=t.id),key=lambda t:(t.y,t.x));regions=[]
                    for t in changed:
                        y=self.h-t.y-t.height
                        if regions and regions[-1][1]==y and regions[-1][3]==t.height and regions[-1][0]+regions[-1][2]==t.x:
                            x0,y0,w,h=regions[-1];regions[-1]=(x0,y0,w+t.width,h)
                        else:regions.append((t.x,y,t.width,t.height))
                for bounds in regions:
                    x,y,w,h=bounds;part=self.region(bounds);p=QPainter(cache.image);p.setCompositionMode(QPainter.CompositionMode_Source);p.drawImage(x,y,part);p.end();cache.copied+=w*h*4;cache.refresh_regions+=1
            cache.stamps=ids;self._refresh_base=ids;self._dirty_rect=None;return cache.image
    def copy(self,*args):
        with self.display.lock:return self.materialize().copy(*args)
    def convertToFormat(self,*args):
        with self.display.lock:return self.materialize().convertToFormat(*args)
    def constBits(self):
        with self.display.lock:self._pin=self.materialize().copy();return self._pin.constBits()
    def bits(self):raise ValueError('Committed native pixels are immutable; derive a private version')
    def scaled(self,*args):return self.materialize().scaled(*args)
    def pixelColor(self,x,y):return self.region((x,y,1,1)).pixelColor(0,0)
    def save(self,*args):
        # Encode under the family presentation lock: concurrent older/newer
        # pinned saves must never swap the cache while Qt reads its pixels.
        with self.display.lock:return self.materialize().save(*args)

def native_add(back,source):
    selection=backend()
    if not selection.available:return None
    result=QImage(back.size(),QImage.Format_ARGB32_Premultiplied)
    # Inputs are region QImages, never cross-process pointers. One kernel call.
    a=C.c_uint8.from_buffer(back.bits());b=C.c_uint8.from_buffer(source.bits());d=C.c_uint8.from_buffer(result.bits());error=Error()
    code=selection.dll.zw_add(C.addressof(a),C.addressof(b),C.addressof(d),result.sizeInBytes(),C.byref(error))
    if code:raise ValueError(error.message.decode())
    return result

def native_constrained(before,after,coverage,opacity):
    selection=backend()
    if not selection.available or not hasattr(selection.dll,'zw_constrain'):return None
    if not before.size()==after.size()==coverage.size():raise ValueError('Constraint region sizes differ')
    if any(im.format()!=QImage.Format_ARGB32_Premultiplied or im.bytesPerLine()!=im.width()*4 for im in (before,after,coverage)):raise ValueError('Constraint regions require packed premultiplied pixels')
    result=QImage(before.size(),QImage.Format_ARGB32_Premultiplied);inputs=[C.c_uint8.from_buffer(im.bits()) for im in (before,after,coverage,result)];error=Error()
    code=selection.dll.zw_constrain(*(C.addressof(p) for p in inputs),result.sizeInBytes(),opacity,C.byref(error))
    if code:raise ValueError(error.message.decode())
    return result


class FillCancel(threading.Event):
    """Event plus aligned Windows interlocked flag; no Python per-pixel calls."""
    def __init__(self):
        super().__init__();self.flag=C.c_int32(0);self.exchange=getattr(backend().dll,'zw_cancel',None)
    def write(self,value):
        if self.exchange:
            error=Error();code=self.exchange(C.byref(self.flag),value,C.byref(error))
            if code:raise ValueError(error.message.decode('utf8','replace'))
        else:self.flag.value=value  # No native traversal on B1/older exports.
    def set(self):self.write(1);super().set()
    def clear(self):self.write(0);super().clear()

def connected_region(matches,seed,cancel,seconds):
    selection=backend()
    if not selection.dll or not hasattr(selection.dll,'zw_connected') or not hasattr(selection.dll,'zw_cancel'):return None
    import numpy as np
    matches=np.ascontiguousarray(matches,dtype=np.bool_);h,w=matches.shape;output=np.zeros((h,w),np.bool_);event=cancel if isinstance(cancel,FillCancel) else FillCancel();finished=threading.Event();watcher=None
    if event is not cancel and cancel is not None:
        if cancel.is_set():event.set()
        def watch():
            while not finished.wait(.005):
                if cancel.is_set():event.set();return
        watcher=threading.Thread(target=watch,daemon=True);watcher.start()
    error=Error()
    try:
        code=selection.dll.zw_connected(matches.ctypes.data,matches.nbytes,w,h,seed[0],seed[1],output.ctypes.data,output.nbytes,C.byref(event.flag),max(.000001,min(30.,seconds)),C.byref(error))
        if code:raise MemoryError(error.message.decode('utf8','replace')) if code==2 else ValueError(error.message.decode('utf8','replace'))
        if cancel is not None and cancel.is_set():raise ValueError('Obsolete Fill cancelled; artwork unchanged.')
        return output
    finally:
        finished.set()
        if watcher:watcher.join()
