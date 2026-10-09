"""Immutable tile transport, consumer leases and unique-allocation accounting."""
from multiprocessing.shared_memory import SharedMemory
from copy import deepcopy
import ctypes as C,mmap,uuid
from native_raster import NativeImage,backend

def tiled(desc):return isinstance(desc,dict) and desc.get('layout')=='tiles128-v1'
def validate(desc):
    from raster_resources import validate as common
    flat=dict(desc);flat.pop('layout',None);common(flat)
    if not tiled(desc) or desc.get('abi')!=1 or not isinstance(desc.get('family'),str) or len(desc['family'])!=32:raise ValueError('Incompatible tiled descriptor')
    tiles=desc.get('tiles');w,h=desc['width'],desc['height']
    if not isinstance(tiles,list) or len(tiles)!=((w+127)//128)*((h+127)//128):raise ValueError('Incomplete tile descriptor')
    names=set();i=0
    for y in range(0,h,128):
        for x in range(0,w,128):
            t=tiles[i];i+=1;tw,th=min(128,w-x),min(128,h-y)
            if any(type(t.get(k)) is not int for k in ('x','y','width','height','stride','bytes')) or (t['x'],t['y'],t['width'],t['height'],t['stride'],t['bytes'])!=(x,y,tw,th,tw*4,tw*th*4):raise ValueError('Invalid tile geometry/stride/length')
            name=t.get('name')
            if not isinstance(name,str) or not name.startswith('zw_raster_') or len(name)>64 or name in names:raise ValueError('Invalid/duplicate tile mapping identity')
            names.add(name)
    return desc

def allocations(desc):return {t['name']:t['bytes'] for t in validate(desc)['tiles']} if tiled(desc) else {desc['name']:desc['bytes']}
def unique_bytes(descriptors):
    sizes={}
    for d in descriptors:
        for name,size in allocations(d).items():
            if name in sizes and sizes[name]!=size:raise ValueError('Immutable mapping size changed')
            sizes[name]=size
    return sum(sizes.values())

def mapping_bytes(descriptors):
    sizes={}
    for desc in descriptors:
        for name,size in allocations(desc).items():sizes[name]=((size+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE
    return sum(sizes.values())

class TileLease:
    def __init__(self,desc,leases=None,native=True):
        self.desc=deepcopy(validate(desc));self.leases=[];self.native=None
        try:
            if leases is None:
                for tile in desc['tiles']:
                    lease=SharedMemory(name=tile['name']);self.leases.append(lease)
                    if not tile['bytes']<=lease.size<=((tile['bytes']+mmap.PAGESIZE-1)//mmap.PAGESIZE)*mmap.PAGESIZE:raise ValueError('Tile mapping allocation length changed')
            else:self.leases=leases
            if native and backend().available:self.native=backend().storage().import_tiles(desc,self.leases)
        except BaseException:self.close();raise
    @property
    def size(self):return unique_bytes([self.desc])
    def close(self):
        self.native=None
        for lease in self.leases:lease.close()
        self.leases=[]
    def unlink(self):pass # Windows readers own their handles; closure retires maps.

def export(image):
    """One native tile-table query; only newly changed mappings are copied."""
    if len(image.names)>65536:
        active={t.id for t in image.tiles()};image.names={k:v for k,v in image.names.items() if k in active}
    leases=[];tiles=[];copied=0
    try:
        for t in image.tiles():
            name=image.names.get(t.id);lease=None
            if name:
                try:lease=SharedMemory(name=name)
                except FileNotFoundError:pass
            if lease is None:
                name='zw_raster_'+uuid.uuid4().hex;lease=SharedMemory(name=name,create=True,size=t.length)
                try:
                    pointer=C.c_uint8.from_buffer(lease.buf);C.memmove(C.addressof(pointer),t.data,t.length);del pointer;copied+=t.length
                except BaseException:lease.close();raise
                image.names[t.id]=name
            leases.append(lease);tiles.append(dict(name=name,x=t.x,y=t.y,width=t.width,height=t.height,stride=t.width*4,bytes=t.length))
        desc=dict(name='zw_raster_tiles_'+uuid.uuid4().hex,width=image.w,height=image.h,stride=image.w*4,bytes=image.w*image.h*4,format='RGBA8',orientation='bottom-up',alpha='premultiplied',color='sRGB',layout='tiles128-v1',abi=1,family=image.family,tiles=tiles,transfer_copied_bytes=copied)
        return desc,TileLease(desc,leases,native=False)
    except BaseException:
        for lease in leases:lease.close()
        raise

def read(desc):
    lease=TileLease(desc,native=False)
    try:
        w,h=desc['width'],desc['height'];data=bytearray(w*h*4)
        for t,mapping in zip(desc['tiles'],lease.leases):
            for y in range(t['height']):
                at=((t['y']+y)*w+t['x'])*4;data[at:at+t['stride']]=mapping.buf[y*t['stride']:(y+1)*t['stride']]
        return dict(width=w,height=h),bytes(data)
    finally:lease.close()

def image(desc):
    lease=TileLease(desc)
    try:
        if lease.native is not None:return lease.native
        from PySide6.QtGui import QImage
        meta,data=read(desc);return QImage(data,meta['width'],meta['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).convertToFormat(QImage.Format_ARGB32_Premultiplied)
    finally:lease.close()

class Upload:
    """Renderer-owned bounded tile upload staging, no full CPU materialization."""
    def __init__(self,desc):self.desc=deepcopy(validate(desc));self.size=(desc['width'],desc['height'])
    def __len__(self):return self.desc['bytes'] # conservative GPU admission estimate
    def apply(self,ctx,texture,base=None,base_desc=None):
        copied=0
        if base is not None:
            old=ctx.framebuffer(color_attachments=[base]);new=ctx.framebuffer(color_attachments=[texture])
            try:ctx.copy_framebuffer(new,old)
            finally:new.release();old.release()
        old_names={t['name'] for t in (base_desc or {}).get('tiles',[])}
        lease=TileLease(self.desc,native=False)
        try:
            for tile,mapping in zip(self.desc['tiles'],lease.leases):
                if base is not None and tile['name'] in old_names:continue
                texture.write(mapping.buf[:tile['bytes']],viewport=(tile['x'],tile['y'],tile['width'],tile['height']),alignment=1);copied+=tile['bytes']
        finally:lease.close()
        return dict(upload_bytes=copied,reused_tiles=sum(t['name'] in old_names for t in self.desc['tiles']) if base is not None else 0,changed_tiles=sum(t['name'] not in old_names for t in self.desc['tiles']) if base is not None else len(self.desc['tiles']),gpu_copy_bytes=self.desc['bytes'] if base is not None else 0)
