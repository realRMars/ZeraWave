"""Still-image saves of immutable accepted Composition artwork.

Uses the existing Qt reference compositor at authored canvas pixel scale. This is
save-time CPU composition, not a new renderer or per-frame display readback.
"""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,math,os,threading,time,uuid
import numpy as np
from PySide6.QtCore import QBuffer,QByteArray,QIODevice
from PySide6.QtGui import QImage,QImageWriter,QImageReader,QColor,QPainter
from composition import lookup,ancestors,effective,asset_matrix,world_matrix,is_branch

SCOPES=('composition','own','branch','selection')
def output_key(scope,ids):return json.dumps([scope,sorted(set(ids)) if scope!='composition' else []],separators=(',',':'))
def validate_outputs(values):
    if not isinstance(values,list) or len(values)>128:raise ValueError('At most 128 artwork output associations.')
    clean=[];keys=set()
    for v in values:
        if not isinstance(v,dict) or v.get('scope') not in SCOPES:raise ValueError('Invalid artwork output scope.')
        ids=v.get('targets',[])
        if not isinstance(ids,list) or len(ids)>32 or any(not isinstance(i,str) or not 1<=len(i)<=64 for i in ids):raise ValueError('Invalid artwork output targets.')
        key=output_key(v['scope'],ids)
        if key in keys:raise ValueError('Duplicate artwork output scope.')
        keys.add(key);path=v.get('path');fmt=v.get('format');background=v.get('background','#ffffff');quality=v.get('quality',95)
        if not isinstance(path,str) or not Path(path).is_absolute() or len(path)>32760:raise ValueError('Artwork output needs an absolute path.')
        if not isinstance(fmt,str) or not 1<=len(fmt)<=16 or not fmt.isalnum():raise ValueError('Invalid artwork image format.')
        if not isinstance(background,str) or not QColor(background).isValid() or QColor(background).alpha()!=255:raise ValueError('Invalid flattening background.')
        if type(quality) is not int or not 0<=quality<=100:raise ValueError('Invalid image quality.')
        fingerprint=v.get('fingerprint','')
        if not isinstance(fingerprint,str) or len(fingerprint)>64:raise ValueError('Invalid saved artwork fingerprint.')
        clean.append(dict(scope=v['scope'],targets=sorted(set(ids)),path=path,format=fmt.lower(),background=background,quality=quality,fingerprint=fingerprint))
    return clean

def formats():
    """Only offer installed writers that encode and decode a real alpha fixture."""
    found={};image=QImage(7,5,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(40,110,180,130));image.setPixelColor(0,0,QColor(0,0,0,0))
    for raw in QImageWriter.supportedImageFormats():
        name=bytes(raw).decode().lower()
        if name in ('jpg','jpe','tif'):continue
        data=QByteArray();buffer=QBuffer(data);buffer.open(QIODevice.WriteOnly);writer=QImageWriter(buffer,raw)
        if not writer.write(image):continue
        decoded=QImage.fromData(data)
        if decoded.isNull() or decoded.size()!=image.size():continue
        found[name]=dict(alpha=decoded.pixelColor(0,0).alpha()==0 and abs(decoded.pixelColor(1,1).alpha()-130)<=1,quality=writer.supportsOption(QImageIOHandler.ImageOption.Quality),compression=writer.supportsOption(QImageIOHandler.ImageOption.CompressionRatio),lossy=name in ('jpeg','jfif','webp'))
    return found
from PySide6.QtGui import QImageIOHandler

class FrozenCanvas:
    stroke=None
    def __init__(self,scene,images,metadata,size):
        self.editor=SimpleNamespace(config=scene,images=images,pending_paint=None);self.canvas_size=size;self.metadata=metadata;self.mask_cache={}
    def source_matrix(self,row):
        m=self.metadata.get(row['id'],{});im=self.editor.images.get(row['id']) or self.editor.images.get(row['asset'])
        dims=(m.get('width',im.width() if im else 1)*m.get('pixel_aspect',1.),m.get('height',im.height() if im else 1))
        return asset_matrix(self.editor.config,row,self.canvas_size,dims)
    def mask_image(self,image,row):
        from studio_composition import masked_image
        from native_raster import NativeImage
        if isinstance(image,NativeImage):
            # Materialize under the native presentation lock into an independent
            # reader image. Another revision cannot swap these writer pixels.
            image=image.copy()
        return masked_image(image,row)

def capture(editor,scope,ids):
    """Freeze only accepted images. Holding NativeImages retains their versions."""
    if scope not in SCOPES:raise ValueError('Unknown artwork scope.')
    if editor.edit_jobs or editor.art_jobs or editor.canvas.stroke or editor.await_recovery or editor.pending_paint or getattr(editor,'before',None) or getattr(getattr(editor,'fill_controller',None),'job',None) or getattr(getattr(editor,'pixel_editor',None),'gesture',None):raise ValueError('Finish/reconcile the active edit before saving accepted artwork.')
    if hasattr(editor,'shell'):
        snapshot=editor.shell.client.snapshot
        media=snapshot.get('media_control',{})
        if editor.binding!=(media.get('session'),media.get('revision')) or editor.config!=snapshot.get('values',{}).get('media'):raise ValueError('Editor/owner revision is still reconciling; no preview was captured.')
    scene=deepcopy(editor.config);rows=lookup(scene);ids=sorted(set(ids))
    if scope!='composition' and (not ids or any(i not in rows for i in ids)):raise ValueError('Artwork targets changed; choose the scope again.')
    selected=set(ids);included=set(rows) if scope=='composition' else set(ids)
    if scope in ('branch','selection'):
        included.update(r['id'] for r in rows.values() if any(a['id'] in selected for a in ancestors(scene,r['id'])))
    needed=set(included)
    for i in included:needed.update(a['id'] for a in ancestors(scene,i))
    scene['layers']=[r for r in scene['layers'] if r['id'] in needed]
    for r in scene['layers']:
        if r['id'] not in included:r['source_visible']=False
        if scope=='own' and r['id'] in selected and r['type'] in ('Artwork',):r['type']='Image'
    images={};metadata={}
    from native_raster import NativeImage
    for r in scene['layers']:
        metadata[r['id']]=deepcopy(editor.metadata(r))
        if r['type']=='Group' or not r['source_visible'] or not effective(scene,r,'enabled'):continue
        image=editor.images.get(r['id']) or editor.images.get(r['asset'])
        if image is None:raise ValueError('No readable current artwork frame for '+r['name']+'. Play/seek/snapshot the source first; no placeholder is saved.')
        # Native handle retain is O(1), QImage implicit sharing is an immutable
        # read pin: editor gestures always use a separate writable buffer.
        images[r['id']]=image.private_view() if isinstance(image,NativeImage) else QImage(image)
    size=tuple(scene.get('canvas') or editor.canvas_size);adapter=FrozenCanvas(scene,images,metadata,size)
    bounds=(0,0,*size)
    if scope!='composition':
        corners=[]
        for r in scene['layers']:
            if r['id'] not in included or r['id'] not in images:continue
            m=np.array([[size[0],0,size[0]*.5],[0,size[1],size[1]*.5],[0,0,1.]])@adapter.source_matrix(r)
            corners.extend((m@np.array([x,y,1.]))[:2] for x in (-.5,.5) for y in (-.5,.5))
        if corners:
            x,y=map(math.floor,np.min(corners,axis=0));right,bottom=map(math.ceil,np.max(corners,axis=0));bounds=x,y,max(1,right-x),max(1,bottom-y)
    if bounds[2]>8192 or bounds[3]>8192 or bounds[2]*bounds[3]>8388608:raise ValueError('Artwork bounds exceed the existing 8192-side / 8 MP image capacity; no clipping or downsampling was applied.')
    # Fingerprint includes exact version identity plus structural state; it is
    # target-specific and never marks the editable session saved.
    identity={k:(v.family,v.cacheKey()) if isinstance(v,NativeImage) else v.cacheKey() for k,v in images.items()}
    fingerprint=hashlib.sha256(json.dumps([scene,identity,bounds],sort_keys=True).encode()).hexdigest()
    return dict(canvas=adapter,bounds=bounds,scope=scope,targets=ids,session=editor.binding[0],revision=editor.binding[1],fingerprint=fingerprint,frames=[r['name'] for r in scene['layers'] if r['id'] in images and r['type'] not in ('Image','Artwork','Paint')])

def compose(pin):
    from cpu_projection import Projection
    x,y,w,h=pin['bounds'];cw,ch=pin['canvas'].canvas_size
    projection=np.array([[cw,0,cw*.5-x],[0,ch,ch*.5-y],[0,0,1.]])
    return Projection().render(pin['canvas'],w,h,projection).copy()

def write_image(pin,path,fmt,options,cancel,capabilities):
    if fmt not in capabilities:raise ValueError('Unsupported installed image writer: '+fmt)
    if fmt in ('ico','cur') and max(pin['bounds'][2:])>256:raise ValueError('ICO/CUR writer supports up to 256 pixels per side; choose PNG without reducing artwork.')
    path=Path(path);expected='jpg' if fmt=='jpeg' else fmt
    if path.suffix.lower() not in ('.'+expected,'.jpeg' if fmt=='jpeg' else '.'+expected):raise ValueError('Filename extension does not match encoded '+fmt)
    if cancel.is_set():raise InterruptedError('Artwork save cancelled before composition.')
    start=time.perf_counter();image=compose(pin);composed=time.perf_counter()
    from PySide6.QtGui import QColorSpace
    image.setColorSpace(QColorSpace(QColorSpace.SRgb))
    if cancel.is_set():raise InterruptedError('Artwork save cancelled before encoding.')
    if not capabilities[fmt]['alpha']:
        color=QColor(options.get('background','#ffffff'));color.setAlpha(255)
        flat=QImage(image.size(),QImage.Format_RGB32);flat.fill(color);p=QPainter(flat);p.drawImage(0,0,image);p.end();image=flat
    import tempfile
    fd,temp=tempfile.mkstemp(prefix='.'+path.name+'.zw-',suffix='.tmp',dir=path.parent);os.close(fd)
    try:
        writer=QImageWriter(temp,fmt.encode());writer.setQuality(options.get('quality',95))
        if capabilities[fmt]['compression'] and fmt=='png':writer.setCompression(1)
        writer.setText('Software','ZeraWave artwork image save');
        success=writer.write(image);error=writer.errorString();writer.device().close();del writer
        if not success:raise OSError(error)
        encoded=time.perf_counter()
        if cancel.is_set():raise InterruptedError('Artwork save cancelled before replacement.')
        with open(temp,'rb+') as stream:stream.flush();os.fsync(stream.fileno())
        if cancel.is_set():raise InterruptedError('Artwork save cancelled before replacement.')
        os.replace(temp,path);finished=time.perf_counter()
        return dict(path=str(path),format=fmt,dimensions=[image.width(),image.height()],scope=pin['scope'],targets=pin['targets'],session=pin['session'],revision=pin['revision'],fingerprint=pin['fingerprint'],background=options.get('background','#ffffff'),quality=options.get('quality',95),compose_ms=(composed-start)*1000,encode_ms=(encoded-composed)*1000,write_ms=(finished-encoded)*1000,bytes=path.stat().st_size)
    except BaseException as original:
        try:Path(temp).unlink(missing_ok=True)
        except OSError as cleanup:original.add_note('Artwork temporary cleanup: '+str(cleanup))
        raise

class ImageSaves:
    """Two pinned jobs, one ordered encoder/writer; no stale destination writes."""
    def __init__(self):
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Artwork image save');self.jobs=[];self.results=[];self.capabilities=formats();self.closed=False
    def submit(self,pin,path,fmt,options):
        if self.closed or len(self.jobs)>=2:raise ValueError('Two image saves are pending. Wait before capturing another revision.')
        cancel=threading.Event();future=self.pool.submit(write_image,pin,str(Path(path).resolve()),fmt,deepcopy(options),cancel,self.capabilities)
        entry=dict(id=uuid.uuid4().hex,future=future,cancel=cancel,pin=pin);self.jobs.append(entry);return entry['id']
    def poll(self):
        completed=[]
        for entry in list(self.jobs):
            if not entry['future'].done():continue
            self.jobs.remove(entry)
            try:result=dict(status='durable',**entry['future'].result())
            except InterruptedError as exc:result=dict(status='cancelled',error=str(exc))
            except Exception as exc:result=dict(status='failed',error=str(exc),notes=getattr(exc,'__notes__',[]))
            result['id']=entry['id'];completed.append(result);self.results=(self.results+[result])[-32:]
            entry.pop('pin',None) # only after actual terminal Future
        return completed
    def cancel_all(self):
        for entry in self.jobs:entry['cancel'].set()
    def close(self):
        self.cancel_all();self.closed=True;self.pool.shutdown(wait=False,cancel_futures=False)
