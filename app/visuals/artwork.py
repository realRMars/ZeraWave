"""Native artwork dependencies and shared selection geometry; no pixel JSON.

Generated PNGs are immutable and content addressed. Disk admission uses physical
free space, explicit reservations and checkpoint headroom. Save/Save As copies only referenced dependencies beside a session.
Original inputs are never overwritten. Undo retains immutable previous versions.
"""
from pathlib import Path
import hashlib, os, uuid
import numpy as np
from PySide6.QtCore import Qt,QPointF,QRectF,QBuffer,QIODevice
from PySide6.QtGui import QImage,QPainterPath,QPainter,QColor

from artwork_store import get_store, check_cancel

def selection_path(operation,size,closed=True):
    w,h=size;pts=operation['points'];path=QPainterPath()
    shape=operation.get('shape','Path')
    if shape in ('Rectangle','Ellipse'):
        xs=[p[0]*w for p in pts];ys=[p[1]*h for p in pts];rect=QRectF(min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys))
        (path.addRect if shape=='Rectangle' else path.addEllipse)(rect);return path
    path.moveTo(pts[0][0]*w,pts[0][1]*h);handles=operation.get('handles')
    for i in range(1,len(pts)+(1 if closed else 0)):
        j=i%len(pts)
        if handles:path.cubicTo(QPointF(handles[i-1][1][0]*w,handles[i-1][1][1]*h),QPointF(handles[j][0][0]*w,handles[j][0][1]*h),QPointF(pts[j][0]*w,pts[j][1]*h))
        else:path.lineTo(pts[j][0]*w,pts[j][1]*h)
    if closed:path.closeSubpath()
    return path

def masked(image,operations):
    result=image.copy()
    for operation in operations:
        if not operation['enabled']:continue
        from pixel_selection import operation_image
        shape=operation_image(operation,(image.width(),image.height()))
        p=QPainter(result);p.setCompositionMode(QPainter.CompositionMode_DestinationIn if operation['mode']=='Keep' else QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,shape);p.end()
    return result

def encode_image(image):
    """Lossless RGBA PNG for immutable working pixels, using standard zlib.

    Qt's adaptive PNG filters dominated short-stroke persistence. The PNG Sub filter
    and zlib level 1 trade file size for throughput without changing a pixel.
    Qt still owns premultiplied -> straight-alpha conversion and PNG decoding.
    """
    import struct,zlib
    rgba=image.convertToFormat(QImage.Format_RGBA8888)
    if rgba.isNull():raise ValueError('Cannot encode empty artwork; accepted pixels retained.')
    w,h=rgba.width(),rgba.height();stride=w*4
    if max(w,h)>8192 or w*h>8388608:raise ValueError('Artwork exceeds the native 8 megapixel limit.')
    pixels=rgba.constBits();source=None
    try:
        source=np.frombuffer(pixels,dtype=np.uint8).reshape(h,rgba.bytesPerLine())[:,:stride]
        raw=np.empty((h,stride+1),dtype=np.uint8);raw[:,0]=1
        raw[:,1:5]=source[:,:4];raw[:,5:]=source[:,4:]-source[:,:-4]
    finally:source=None;pixels.release()
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    metadata=b''
    dx,dy=rgba.dotsPerMeterX(),rgba.dotsPerMeterY()
    if dx>0 and dy>0:metadata+=chunk(b'pHYs',struct.pack('>IIB',dx,dy,1))
    space=rgba.colorSpace()
    if space.isValid():
        profile=bytes(space.iccProfile())
        if profile:metadata+=chunk(b'iCCP',b'Profile\0\0'+zlib.compress(profile,1))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+metadata+chunk(b'IDAT',zlib.compress(raw,1))+chunk(b'IEND',b'')

def store_image(image,provenance,folder=None,cancel=None):
    if image.isNull() or max(image.width(),image.height())>8192 or image.width()*image.height()>8388608:raise ValueError('Artwork exceeds the native 8 megapixel limit.')
    folder=Path(folder or os.environ.get('ZERAWAVE_ARTWORK_STORE') or Path(__file__).resolve().parents[2]/'work/studio/artwork');folder.mkdir(parents=True,exist_ok=True)
    data=encode_image(image);digest=hashlib.sha256(data).hexdigest();path=folder/(digest+'.png')
    get_store(folder).write(path,data,cancel=cancel)
    from media_registry import inspect
    import threading
    record=inspect(str(path),threading.Event());record.update(id=uuid.uuid4().hex,managed=True,provenance=str(provenance)[:512]);return record

def portable_scene(scene,destination,cancel=None):
    """Prepare every copy before writing session state; original paths untouched."""
    from copy import deepcopy
    result=deepcopy(scene);folder=Path(destination).with_suffix('.assets')
    # Copy one dependency at a time; duplicate paths/content are charged once.
    copied=set()
    for asset in result['assets']:
        check_cancel(cancel)
        if not asset.get('managed'):continue
        source=Path(asset['path']);data=source.read_bytes();digest=hashlib.sha256(data).hexdigest();target=folder/(digest+'.png')
        if digest not in copied:get_store(folder).write(target,data,cancel=cancel);copied.add(digest)
        asset['path']=str(target.resolve())
    return result

def magnetic_point(image,uv,radius=12):
    """Local native-pixel gradient attraction, bounded 25×25, manual nodes remain.

    No segmentation or automatic background removal. Flat regions keep the
    pointer location; nearby strong edges attract the interactive tracing node.
    """
    if image is None:return list(uv)
    w,h=image.width(),image.height();x,y=round(uv[0]*(w-1)),round(uv[1]*(h-1))
    x0,x1=max(1,x-radius),min(w-1,x+radius+1);y0,y1=max(1,y-radius),min(h-1,y+radius+1)
    if x1<=x0 or y1<=y0:return list(uv)
    gray=image.copy(x0-1,y0-1,x1-x0+2,y1-y0+2).convertToFormat(QImage.Format_Grayscale8)
    a=np.frombuffer(gray.constBits(),np.uint8).reshape(gray.height(),gray.bytesPerLine())[:,:gray.width()].astype(np.int16)
    gx=a[1:-1,2:]-a[1:-1,:-2];gy=a[2:,1:-1]-a[:-2,1:-1]
    yy,xx=np.mgrid[y0:y1,x0:x1];score=np.hypot(gx,gy)/(1+np.hypot(xx-x,yy-y)/3)
    if score.max()<12:return list(uv)
    iy,ix=np.unravel_index(np.argmax(score),score.shape);return [float((x0+ix)/w),float((y0+iy)/h)]

def smudge(image,start,end,size,strength,opacity,shape='Round',row=None,selection=None,origin=(0,0),global_size=None,pickup=None):
    """Blend a bounded brush tile dragged from prior to current native position."""
    r=max(1,round(size/2));w,h=global_size or (image.width(),image.height());sx,sy=start;ex,ey=end
    tile=image.copy(QRectF(sx-r-origin[0],sy-r-origin[1],2*r,2*r).toRect())
    if pickup is not None:
        tile=pickup.copy()  # Already includes the evolving target once in scene order.
    mask=QImage(tile.size(),QImage.Format_ARGB32_Premultiplied);mask.fill(0)
    if row:
        coverage=QImage(tile.size(),QImage.Format_ARGB32_Premultiplied);coverage.fill(0);p=QPainter(coverage);p.translate(-(sx-r),-(sy-r));c=row['crop'];p.fillRect(QRectF(c[0]*w,c[1]*h,(c[2]-c[0])*w,(c[3]-c[1])*h),QColor('white'));p.end()
        for operation in row['masks']+([dict(selection,mode='Keep')] if selection else []):
            if not operation['enabled']:continue
            from pixel_selection import operation_image
            local=operation_image(operation,(w,h),(round(sx-r),round(sy-r),tile.width(),tile.height()));p=QPainter(coverage);p.setCompositionMode(QPainter.CompositionMode_DestinationIn if operation['mode']=='Keep' else QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,local);p.end()
        p=QPainter(tile);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,coverage);p.end()
    p=QPainter(mask);p.setBrush(QColor(255,255,255));p.setPen(Qt.NoPen)
    (p.drawRect if shape=='Square' else p.drawEllipse)(mask.rect());p.end();p=QPainter(tile);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,mask);p.end()
    p=QPainter(image);p.translate(-origin[0],-origin[1]);p.setOpacity(strength*opacity);p.drawImage(QPointF(ex-r,ey-r),tile);p.end()


def brush_stroke(image,start,end,brush,color,tool='Brush',origin=(0,0)):
    """Native-pixel spaced dabs; flow per dab, stroke opacity applied by caller."""
    from PySide6.QtGui import QRadialGradient
    from PySide6.QtCore import QRectF
    radius=max(.5,brush['size']/2);distance=float(np.hypot(end[0]-start[0],end[1]-start[1]))
    count=max(1,int(np.ceil(distance/max(1.,radius*.2))))
    p=QPainter(image);p.translate(-origin[0],-origin[1]);p.setRenderHint(QPainter.Antialiasing,tool!='Pencil')
    if tool=='Eraser':p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
    c=QColor(color);c.setAlphaF(c.alphaF()*brush.get('flow',1.))
    for i in range(1,count+1):
        x=start[0]+(end[0]-start[0])*i/count;y=start[1]+(end[1]-start[1])*i/count
        if tool=='Pencil' and max(1,round(radius*2))==1:
            # Qt's non-antialiased 1x1 ellipse is empty. Both one-pixel tips
            # occupy the same source cell; retain per-dab flow and stroke opacity.
            p.fillRect(QRectF(round(x-radius),round(y-radius),1,1),c)
        elif tool=='Pencil' and brush['shape']=='Round':
            p.setPen(Qt.NoPen);p.setBrush(c);p.drawEllipse(QRectF(round(x-radius),round(y-radius),max(1,round(radius*2)),max(1,round(radius*2))))
        elif tool=='Pencil':p.fillRect(QRectF(round(x-radius),round(y-radius),max(1,round(radius*2)),max(1,round(radius*2))),c)
        elif brush['shape']=='Square':p.fillRect(QRectF(x-radius,y-radius,radius*2,radius*2),c)
        else:
            hard=brush.get('hardness',1.)
            gradient=QRadialGradient(QPointF(x,y),radius);gradient.setColorAt(0,c)
            gradient.setColorAt(min(.999,hard),c);transparent=QColor(c);transparent.setAlpha(0);gradient.setColorAt(1,transparent)
            p.setPen(Qt.NoPen);p.setBrush(gradient);p.drawEllipse(QPointF(x,y),radius,radius)
    p.end()

def edit_coverage(size,row,selection=None):
    w,h=size;coverage=QImage(w,h,QImage.Format_ARGB32_Premultiplied);coverage.fill(0)
    p=QPainter(coverage);c=row['crop'];p.fillRect(QRectF(c[0]*w,c[1]*h,(c[2]-c[0])*w,(c[3]-c[1])*h),QColor('white'));p.end()
    return masked(coverage,row['masks']+([dict(selection,mode='Keep')] if selection else []))

def constrained_edit(before,after,row,selection=None,opacity=1.,bounds=None,coverage=None,result=None):
    """Write only the editable own-content footprint, without baking masks twice."""
    w,h=before.width(),before.height()
    if coverage is None:coverage=edit_coverage((w,h),row,selection)
    # Bounded 64-row strips avoid four full floating-point image temporaries.
    if result is None:result=before.copy()
    a=np.frombuffer(before.constBits(),np.uint8).reshape(h,before.bytesPerLine())[:,:w*4].reshape(h,w,4)
    b=np.frombuffer(after.constBits(),np.uint8).reshape(h,after.bytesPerLine())[:,:w*4].reshape(h,w,4)
    mask=np.frombuffer(coverage.constBits(),np.uint8).reshape(h,coverage.bytesPerLine())[:,3:w*4:4]
    dst=np.frombuffer(result.bits(),np.uint8).reshape(h,result.bytesPerLine())[:,:w*4].reshape(h,w,4)
    x0,y0,x1,y1=bounds or (0,0,w,h);x0,y0=max(0,x0),max(0,y0);x1,y1=min(w,x1),min(h,y1)
    for y in range(y0,y1,64):
        stop=min(y+64,y1);factor=mask[y:stop,x0:x1,None].astype(np.float32)*(opacity/255.)
        dst[y:stop,x0:x1]=np.rint(a[y:stop,x0:x1]*(1-factor)+b[y:stop,x0:x1]*factor).astype(np.uint8)
    return result
