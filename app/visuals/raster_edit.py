"""Bounded segment preparation using the existing Qt dab and constraint policy."""
import math
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage,QPainter,QColor
from artwork import brush_stroke,smudge,selection_path,constrained_edit

def coverage(bounds,size,row,selection=None):
    x,y,w,h=bounds;sw,sh=size
    image=QImage(w,h,QImage.Format_ARGB32_Premultiplied);image.fill(0)
    p=QPainter(image);p.translate(-x,-y);c=row['crop'];p.fillRect(QRectF(c[0]*sw,c[1]*sh,(c[2]-c[0])*sw,(c[3]-c[1])*sh),QColor('white'));p.end()
    for operation in row['masks']+([dict(selection,mode='Keep')] if selection else []):
        if not operation['enabled']:continue
        from pixel_selection import operation_image
        shape=operation_image(operation,size,bounds)
        p=QPainter(image);p.setCompositionMode(QPainter.CompositionMode_DestinationIn if operation['mode']=='Keep' else QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,shape);p.end()
    return image

def segment(stroke,now):
    image=stroke['image'];brush=stroke['brush'];last=stroke['last'];row=stroke['target'];r=math.ceil(brush['size']/2)+4
    x,y=max(0,math.floor(min(last[0],now[0])-r)),max(0,math.floor(min(last[1],now[1])-r))
    right,bottom=min(image.width(),math.ceil(max(last[0],now[0])+r)),min(image.height(),math.ceil(max(last[1],now[1])+r))
    if right<=x or bottom<=y:return x,y,right,bottom
    bounds=x,y,right-x,bottom-y;working=image.region(bounds)
    if stroke['tool']=='Smudge':
        from editor_colors import pickup_tile
        smudge(working,last,now,brush['size'],brush['strength'],1.,brush['shape'],row,stroke['selection'],origin=(x,y),global_size=(image.width(),image.height()),pickup=pickup_tile(stroke,last,max(1,round(brush['size']/2))))
    else:brush_stroke(working,last,now,brush,stroke['color'],stroke['tool'],origin=(x,y))
    base=stroke['base'].region(bounds);mask=coverage(bounds,(image.width(),image.height()),row,stroke['selection'])
    from native_raster import native_constrained
    preview=native_constrained(base,working,mask,brush['opacity'])
    if preview is None:preview=constrained_edit(base,working,row,stroke['selection'],brush['opacity'],coverage=mask)
    # Both immutable allocations must succeed before installing either private state.
    next_work=image.patch(bounds,working);next_preview=stroke['preview'].patch(bounds,preview)
    stroke.update(image=next_work,preview=next_preview)
    return x,y,right,bottom


def masked_projection(canvas,image,row):
    if not row['masks']:return image.materialize()
    import json
    key=(image.family,json.dumps(row['masks'],sort_keys=True));old=canvas.mask_cache.get(row['id']);ids=tuple(t.id for t in image.tiles())
    if old and old[0]==key:
        result=old[1];previous=old[2]
    else:
        result=QImage(image.size(),QImage.Format_ARGB32_Premultiplied);result.fill(0);previous=()
        if sum(v[1].sizeInBytes() for v in canvas.mask_cache.values())+result.sizeInBytes()>128*1024*1024:canvas.mask_cache.clear()
    for i,t in enumerate(image.tiles()):
        if i<len(previous) and previous[i]==t.id:continue
        x,y=t.x,image.height()-t.y-t.height;bounds=x,y,t.width,t.height;part=image.region(bounds)
        for operation in row['masks']:
            if not operation['enabled']:continue
            from pixel_selection import operation_image
            shape=operation_image(operation,(image.width(),image.height()),bounds)
            p=QPainter(part);p.setCompositionMode(QPainter.CompositionMode_DestinationIn if operation['mode']=='Keep' else QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,shape);p.end()
        p=QPainter(result);p.setCompositionMode(QPainter.CompositionMode_Source);p.drawImage(x,y,part);p.end()
    canvas.mask_cache[row['id']]=(key,result,ids);return result
