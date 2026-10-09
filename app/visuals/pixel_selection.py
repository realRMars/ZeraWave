"""Full-resolution color coverage, bounded compressed storage and regional reads.

Coverage uses exact 8-bit samples. No contour/rectangle substitutes enter edits.
The existing 256 KiB scene budget remains authoritative; overly complex coverage
is rejected before changing artwork, with the local preview retained.
"""
import base64,zlib,time
from functools import lru_cache
from collections import deque
import numpy as np
from PySide6.QtGui import QImage,QPainter,QColor
from PySide6.QtCore import Qt,QRectF
MAX_PIXELS=8388608
MAX_ENCODED=120*1024

def encode(a):
    h,w=a.shape
    if w*h>MAX_PIXELS:raise ValueError('Selection exceeds 8 megapixels.')
    data=base64.b64encode(zlib.compress(a.astype(np.uint8).tobytes(),6)).decode('ascii')
    if len(data)>MAX_ENCODED:raise ValueError('Detailed selection exceeds the 120 KiB coverage budget; preview retained. Use a smaller region or simpler refinement.')
    return dict(shape='Pixels',mode='Keep',enabled=True,size=[w,h],coverage=data,points=bounds_points(a),handles=[])

def bounds_points(a):
    ys=np.flatnonzero(np.any(a,axis=1));xs=np.flatnonzero(np.any(a,axis=0));h,w=a.shape
    if not len(xs):return [[0.,0.],[1.,0.],[1.,1.],[0.,1.]]
    x0,x1=xs[0]/w,(xs[-1]+1)/w;y0,y1=ys[0]/h,(ys[-1]+1)/h
    return [[float(x0),float(y0)],[float(x1),float(y0)],[float(x1),float(y1)],[float(x0),float(y1)]]

@lru_cache(maxsize=8)
def decode(size,data):
    w,h=size
    if type(w) is not int or type(h) is not int or not 1<=w<=8192 or not 1<=h<=8192 or w*h>MAX_PIXELS or len(data)>MAX_ENCODED:raise ValueError('Invalid pixel selection budget.')
    compressed=base64.b64decode(data,validate=True);reader=zlib.decompressobj();raw=reader.decompress(compressed,w*h+1)
    if len(raw)!=w*h or not reader.eof or reader.unused_data or reader.unconsumed_tail:raise ValueError('Invalid pixel selection coverage.')
    return np.frombuffer(raw,np.uint8).reshape(h,w)

def coverage_image(op,size,bounds=None):
    w,h=size;x,y,rw,rh=bounds or (0,0,w,h)
    a=decode(tuple(op['size']),op['coverage']);sw,sh=op['size']
    # Exact native coverage; nearest mapping only for differing render-mask grids.
    xx=np.clip(np.floor((np.arange(x,x+rw)+.5)*sw/w).astype(int),0,sw-1)
    yy=np.clip(np.floor((np.arange(y,y+rh)+.5)*sh/h).astype(int),0,sh-1)
    v=a[np.ix_(yy,xx)];rgba=np.repeat(v[:,:,None],4,axis=2)
    return QImage(rgba.data,rw,rh,rw*4,QImage.Format_RGBA8888_Premultiplied).copy()

def operation_image(op,size,bounds=None):
    if op.get('shape')=='Pixels':return coverage_image(op,size,bounds)
    from artwork import selection_path
    w,h=size;x,y,rw,rh=bounds or (0,0,w,h)
    im=QImage(rw,rh,QImage.Format_ARGB32_Premultiplied);im.fill(0);p=QPainter(im);p.setRenderHint(QPainter.Antialiasing);p.translate(-x,-y);p.fillPath(selection_path(op,size),QColor('white'));p.end();return im

def select(image,row,seed,tolerance,contiguous,previous=None,mode='New',expand=0,feather=0):
    from artwork import edit_coverage
    w,h=image.width(),image.height()
    if w*h>MAX_PIXELS:raise ValueError('Selection exceeds 8 megapixels.')
    im=image.convertToFormat(QImage.Format_RGBA8888);a=np.frombuffer(im.constBits(),np.uint8).reshape(h,im.bytesPerLine())[:,:w*4].reshape(h,w,4)
    x,y=seed
    if not 0<=x<w or not 0<=y<h or a[y,x,3]==0:raise ValueError('Choose a visible selected-layer pixel.')
    allowed=edit_coverage((w,h),row).convertToFormat(QImage.Format_RGBA8888)
    ca=np.frombuffer(allowed.constBits(),np.uint8).reshape(h,allowed.bytesPerLine())[:,3:w*4:4]
    matches=np.empty((h,w),bool);seed_color=a[y,x].astype(np.int16)
    for start in range(0,h,64):
        strip=a[start:start+64];matches[start:start+64]=(np.max(abs(strip.astype(np.int16)-seed_color),axis=2)<=tolerance)&(strip[:,:,3]>0)&(ca[start:start+64]>0)
    if contiguous:
        output=np.zeros((h,w),bool);todo=deque([(x,y)]);began=time.monotonic();steps=0
        while todo:
            px,py=todo.pop()
            if output[py,px] or not matches[py,px]:continue
            left=px;right=px+1
            while left>0 and matches[py,left-1] and not output[py,left-1]:left-=1
            while right<w and matches[py,right] and not output[py,right]:right+=1
            output[py,left:right]=True;steps+=1
            if steps%256==0 and (steps>MAX_PIXELS or time.monotonic()-began>8):raise ValueError('Contiguous selection exceeded its 8 s work budget; artwork unchanged.')
            for ny in (py-1,py+1):
                if 0<=ny<h:
                    runs=matches[ny,left:right]&~output[ny,left:right];starts=np.flatnonzero(runs&~np.r_[False,runs[:-1]])
                    todo.extend((left+int(v),ny) for v in starts)
        matches=output
    result=matches.astype(np.uint8)*255
    if previous is not None:
        if mode=='Add':result=np.maximum(previous,result)
        elif mode=='Subtract':result=np.minimum(previous,255-result)
    for _ in range(abs(expand)):
        padded=np.pad(result,1,mode='constant',constant_values=0)
        items=[padded[dy:dy+h,dx:dx+w] for dy in range(3) for dx in range(3)]
        result=(np.maximum.reduce if expand>0 else np.minimum.reduce)(items)
    if feather:
        r=feather
        for axis in (0,1):
            pad=[(0,0),(0,0)];pad[axis]=(r,r);v=np.pad(result.astype(np.uint32),pad);v=np.concatenate([np.zeros_like(np.take(v,[0],axis=axis)),v.cumsum(axis=axis,dtype=np.uint32)],axis=axis)
            result=np.rint((np.take(v,range(2*r+1,v.shape[axis]),axis=axis)-np.take(v,range(v.shape[axis]-2*r-1),axis=axis))/(2*r+1)).astype(np.uint8)
    return np.minimum(result,ca)
