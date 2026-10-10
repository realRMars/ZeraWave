"""Incremental CPU projection: fixed physical regions and dependency-complete LRU.

Structural/view changes deliberately invalidate all regions. Raster changes use
inverse transformed source tile dependencies with a four-source-pixel halo.
Qt projects from the complete presentation image to retain its filtering phase.
The image is updated by changed tiles, not rematerialized per paint.
"""
from collections import OrderedDict
import json,math
import numpy as np
from PySide6.QtCore import QRectF,Qt
from PySide6.QtGui import QImage,QPainter,QColor
from composition import ordered_children,effective,is_branch,world_matrix,partition_aligned
from native_raster import NativeImage,native_add

class Projection:
    def __init__(self,limit=128*1024*1024):
        self.cache=OrderedDict();self.bytes=0;self.limit=limit;self.signature=None;self.scratch={};self.scratch_bytes=0
        self.stats=dict(recomposited_pixels=0,reused_regions=0,produced_regions=0,cache_bytes=0,broad_invalidations=0)
    def scratch_image(self,key,width,height):
        if key not in self.scratch:
            size=width*height*4
            if self.scratch_bytes+size>128*1024*1024:raise MemoryError('Global-phase projection scratch exceeds 128 MiB; previous content retained')
            image=QImage(width,height,QImage.Format_ARGB32_Premultiplied)
            if image.isNull():raise MemoryError('Projection scratch allocation failed')
            self.scratch[key]=image;self.scratch_bytes+=size;self.stats['scratch_bytes']=self.scratch_bytes
        return self.scratch[key]
    def get(self,key,produce):
        if key in self.cache:
            value=self.cache.pop(key);self.cache[key]=value;self.stats['reused_regions']+=1;return value
        value=produce();size=value.sizeInBytes()
        if size>self.limit:raise MemoryError('Projection region exceeds 128 MiB cache limit')
        while self.cache and self.bytes+size>self.limit:self.bytes-=self.cache.popitem(last=False)[1].sizeInBytes()
        self.cache[key]=value;self.bytes+=size;self.stats['produced_regions']+=1;self.stats['recomposited_pixels']+=value.width()*value.height();self.stats['cache_bytes']=self.bytes;return value
    def render(self,canvas,width,height,full_projection,damage=None):
        from studio_composition import qtransform,masked_image
        config=canvas.editor.config
        smooth=not getattr(canvas,'pixel_inspection',lambda:False)()
        def source(row):
            image=canvas.editor.images.get(row['id']) or canvas.editor.images.get(row['asset'])
            if canvas.stroke and row['id']==canvas.stroke['row']:image=canvas.stroke['preview']
            elif getattr(canvas.editor,'pending_paint',None) and row['id']==canvas.editor.pending_paint['row']:image=canvas.editor.pending_paint['image']
            return image
        matrices={row['id']:canvas.source_matrix(row) for row in config['layers']}
        grain=128
        structure=[]
        for row in config['layers']:
            image=source(row);r=dict(row);r['asset']=image.family if isinstance(image,NativeImage) else row['asset'];structure.append((r,tuple(matrices[row['id']].flat)))
        signature=json.dumps([structure,grain,config.get('canvas'),width,height,list(full_projection.flat),smooth],sort_keys=True)
        reset=signature!=self.signature
        if reset:
            self.cache.clear();self.scratch.clear();self.scratch_bytes=0;self.bytes=0;self.signature=signature;self.stats['broad_invalidations']+=1
        if reset or not hasattr(self,'output'):
            self.output=QImage(width,height,QImage.Format_ARGB32_Premultiplied);self.output.fill(0)
        result=self.output;p=QPainter(result);p.setCompositionMode(QPainter.CompositionMode_Source)
        # Qt's transformed smooth rasterizer depends on clip start. Exact
        # direct phase is proven for whole-pixel 1:1 source projection only.
        # Other views use one broad region; no changed-pixel tolerance is hidden.
        incremental=True
        for row in config['layers']:
            if row['type']=='Group':
                if row['masks'] or row['crop']!=[0.,0.,1.,1.]:incremental=False
                continue
            image=source(row)
            if image is None:continue
            c=row['crop'];matrix=full_projection@matrices[row['id']]@np.diag([-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1,1.])
            step=matrix[:2,:2]@np.diag([1/(image.width()*(c[2]-c[0])),1/(image.height()*(c[3]-c[1]))])
            origin=matrix@np.array([-c[0]/(c[2]-c[0])-.5,-c[1]/(c[3]-c[1])-.5,1.])
            if not np.allclose(abs(step),np.eye(2),atol=1e-9) or not np.allclose(origin[:2],np.rint(origin[:2]),atol=1e-9):incremental=False
        self.stats['region_policy']='integer-1:1' if incremental else 'broad-preserve-Qt-filter-phase'
        step_x,step_y=(grain,grain) if incremental else (width,height)
        self.stats['region_side']=grain if incremental else None
        start_x,start_y,end_x,end_y=0,0,width,height
        if incremental and not reset and damage is not None:
            start_x=max(0,math.floor(damage.left()/grain)*grain);start_y=max(0,math.floor(damage.top()/grain)*grain);end_x=min(width,math.ceil(damage.right()/grain)*grain);end_y=min(height,math.ceil(damage.bottom()/grain)*grain)
        for y in range(start_y,end_y,step_y):
            for x in range(start_x,end_x,step_x):
                iw,ih=min(step_x,width-x),min(step_y,height-y)
                if incremental and not reset and damage is not None and not damage.intersects(QRectF(x,y,iw,ih)):continue
                projection=full_projection.copy();projection[:2,2]-=(x,y)
                dependencies={}
                for row in config['layers']:
                    image=source(row)
                    if image is None:dependencies[row['id']]=None;continue
                    if not isinstance(image,NativeImage):dependencies[row['id']]=image.cacheKey();continue
                    inverse=np.linalg.inv(full_projection@matrices[row['id']]);corners=[inverse@np.array([px,py,1.]) for px in (x-2,x+iw+2) for py in (y-2,y+ih+2)]
                    c=row['crop'];coords=[((1-(pt[0]+.5) if row['flip_x'] else pt[0]+.5)*(c[2]-c[0])+c[0],(1-(pt[1]+.5) if row['flip_y'] else pt[1]+.5)*(c[3]-c[1])+c[1]) for pt in corners]
                    x0=max(0,math.floor(min(v[0] for v in coords)*image.width())-4);y0=max(0,math.floor(min(v[1] for v in coords)*image.height())-4)
                    x1=min(image.width(),math.ceil(max(v[0] for v in coords)*image.width())+4);y1=min(image.height(),math.ceil(max(v[1] for v in coords)*image.height())+4)
                    dependencies[row['id']]=(image.family,image.stamp((x0,y0,max(0,x1-x0),max(0,y1-y0))))
                def ids(parent):
                    found=[]
                    for row in ordered_children(config,parent):
                        if is_branch(config,row):found.extend(ids(row['id']))
                        else:found.append(row['id'])
                    return found
                modes={'Normal':QPainter.CompositionMode_SourceOver,'Multiply':QPainter.CompositionMode_Multiply,'Screen':QPainter.CompositionMode_Screen,'Add':QPainter.CompositionMode_Plus,'Difference':QPainter.CompositionMode_Difference}
                w,h=canvas.canvas_size
                def children(parent):return self.get((parent,x,y,tuple((i,dependencies.get(i)) for i in ids(parent))),lambda:produce(parent))
                def produce(parent):
                    # Qt blends directly into the global target. Separately
                    # projecting a translucent Normal leaf rounds its opacity
                    # twice; translated small targets change filtering phase.
                    target=self.scratch_image((parent,'target'),width,height)
                    def painter_for(image):
                        q=QPainter(image);q.setClipRect(x,y,iw,ih);q.setRenderHint(QPainter.SmoothPixmapTransform,smooth);return q
                    q=painter_for(target);q.setCompositionMode(QPainter.CompositionMode_Source);q.fillRect(x,y,iw,ih,QColor(0,0,0,0));q.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    rows=ordered_children(config,parent)
                    def prefix_key(stop):
                        relevant=[]
                        for r in rows[:stop]:
                            relevant.extend(ids(r['id']) if is_branch(config,r) else [r['id']])
                        return ('prefix',parent,x,y,stop,tuple((i,dependencies.get(i)) for i in relevant))
                    # An unchanged completed backdrop is exactly the pixels Qt
                    # would draw again, at the same global sampling phase. Keep
                    # these images in the existing bounded dependency-complete
                    # LRU, never a second unbounded composition cache.
                    first=0
                    for stop in range(len(rows)-1,1,-1):
                        key=prefix_key(stop)
                        if key in self.cache:
                            q.setCompositionMode(QPainter.CompositionMode_Source);q.drawImage(x,y,self.get(key,lambda:None));q.setCompositionMode(QPainter.CompositionMode_SourceOver);first=stop;break
                    for index,row in enumerate(rows[first:],first):
                        if not effective(config,row,'enabled') or not is_branch(config,row) and not row['source_visible']:continue
                        group=is_branch(config,row);image=children(row['id']) if group else source(row)
                        if image is None:continue
                        if row['type']=='Group' and (row['masks'] or row['crop']!=[0.,0.,1.,1.]):
                            white=QImage(w,h,QImage.Format_ARGB32_Premultiplied);white.fill(0xffffffff);local=masked_image(white,row)
                            mask=self.scratch_image((parent,'mask'),width,height);mp=painter_for(mask);mp.setRenderHint(QPainter.SmoothPixmapTransform,False);mp.setCompositionMode(QPainter.CompositionMode_Source);mp.fillRect(x,y,iw,ih,QColor(0,0,0,0));mp.setCompositionMode(QPainter.CompositionMode_SourceOver);mp.setTransform(qtransform(full_projection@world_matrix(config,row['id'])));c=row['crop'];mp.setClipRect(QRectF(c[0]-.5,c[1]-.5,c[2]-c[0],c[3]-c[1]),Qt.IntersectClip);mp.drawImage(QRectF(-.5,-.5,1.,1.),local);mp.end()
                            image=image.copy();mp=QPainter(image);mp.setCompositionMode(QPainter.CompositionMode_DestinationIn);mp.drawImage(0,0,mask.copy(x,y,iw,ih));mp.end()
                        elif not group:image=canvas.mask_image(image,row)
                        partition=not row.get('_own') and partition_aligned(config,row);strength=row.get('blend_strength',1.);blend='Normal' if strength==0 else row['blend'];add=blend=='Add' or blend!='Normal' and strength<1.
                        if add:
                            q.end();foreground=self.scratch_image((parent,'source'),width,height);q=painter_for(foreground);q.setCompositionMode(QPainter.CompositionMode_Source);q.fillRect(x,y,iw,ih,QColor(0,0,0,0));q.setCompositionMode(QPainter.CompositionMode_SourceOver)
                        q.save();q.setOpacity(row['opacity']);q.setCompositionMode(QPainter.CompositionMode_SourceOver if add else QPainter.CompositionMode_Plus if partition else modes[blend])
                        if group:q.drawImage(x,y,image)
                        else:
                            q.setTransform(qtransform(full_projection@matrices[row['id']]));q.scale(-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1);c=row['crop'];q.drawImage(QRectF(-.5,-.5,1.,1.),image,QRectF(c[0]*image.width(),c[1]*image.height(),(c[2]-c[0])*image.width(),(c[3]-c[1])*image.height()))
                        q.restore()
                        if add:
                            q.end();original=target.copy(x,y,iw,ih);foreground=foreground.copy(x,y,iw,ih)
                            if blend=='Add':
                                mixed=native_add(original,foreground)
                                if mixed is None:
                                    from studio_composition import add_image
                                    mixed=add_image(original,foreground)
                            else:mixed=original.copy();bp=QPainter(mixed);bp.setCompositionMode(modes[blend]);bp.drawImage(0,0,foreground);bp.end()
                            if strength<1.:
                                normal=original.copy();bp=QPainter(normal);bp.drawImage(0,0,foreground);bp.end();a=np.frombuffer(normal.constBits(),np.uint8).astype(np.uint16);b=np.frombuffer(mixed.constBits(),np.uint8).astype(np.uint16);factor=round(strength*255);data=((a*(255-factor)+b*factor+127)//255).astype(np.uint8).tobytes();mixed=QImage(data,iw,ih,QImage.Format_ARGB32_Premultiplied).copy()
                            q=painter_for(target);q.setCompositionMode(QPainter.CompositionMode_Source);q.drawImage(x,y,mixed);q.setCompositionMode(QPainter.CompositionMode_SourceOver)
                        if 1<=index<len(rows)-1:
                            self.get(prefix_key(index+1),lambda:target.copy(x,y,iw,ih))
                    q.end();return target.copy(x,y,iw,ih)
                p.drawImage(x,y,children(None))
        p.end();return result




def artwork_sampling_plan(scene):
    """Compile immutable stroke order/visibility/partition policy once, not per dab."""
    def children(parent):
        result=[]
        for row in ordered_children(scene,parent):
            group=is_branch(scene,row)
            if not effective(scene,row,'enabled') or not group and not row['source_visible']:continue
            result.append((row,children(row['id']) if group else None,partition_aligned(scene,row)))
        return result
    return children(None)


def render_artwork_region(scene,images,frames,projection,width,height,target=None,preview=None,plan=None):
    """Bounded native-space artwork sampling for Smudge, using Qt blend semantics.

    No canvas/checker/world readback. Images/frames are immutable stroke pins;
    only the target preview is refreshed between dabs. Regional allocations have
    aggregate 16 MiB and single source 4 MiB admission budgets.
    """
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QImage,QPainter,QColor
    from studio_composition import qtransform,add_image
    from raster_edit import coverage
    total=0
    def allocate(w,h):
        nonlocal total
        total+=w*h*4
        if w*h*4>4*1024*1024 or total>16*1024*1024:raise ValueError('Smudge regional sampling capacity exceeded; reduce size or transform magnification.')
        result=QImage(w,h,QImage.Format_ARGB32_Premultiplied)
        if result.isNull():raise MemoryError('Cannot allocate Smudge regional composite.')
        result.fill(0);return result
    modes={'Normal':QPainter.CompositionMode_SourceOver,'Multiply':QPainter.CompositionMode_Multiply,'Screen':QPainter.CompositionMode_Screen,'Add':QPainter.CompositionMode_Plus,'Difference':QPainter.CompositionMode_Difference}
    def projected(row,image,frame,mask_only=False):
        m=projection@frame;inv=np.linalg.inv(m);corners=inv@np.array([[0,width,width,0],[0,0,height,height],[1,1,1,1]])
        x,y=max(0,math.floor(corners[0].min())-2),max(0,math.floor(corners[1].min())-2)
        right,bottom=min(image.width(),math.ceil(corners[0].max())+2),min(image.height(),math.ceil(corners[1].max())+2)
        out=allocate(width,height)
        if right<=x or bottom<=y:return out
        bounds=(x,y,right-x,bottom-y)
        nonlocal total
        total+=bounds[2]*bounds[3]*8
        if bounds[2]*bounds[3]*4>4*1024*1024 or total>16*1024*1024:raise ValueError('Smudge source footprint exceeds the regional budget; gesture cancelled.')
        masked=mask_only or row['crop']!=[0.,0.,1.,1.] or any(o['enabled'] for o in row['masks'])
        mask=coverage(bounds,(image.width(),image.height()),row) if masked else None
        if mask_only:part=mask
        else:
            part=image.region(bounds) if hasattr(image,'region') else image.copy(*bounds)
            if mask is not None:
                p=QPainter(part);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,mask);p.end()
        p=QPainter(out);p.setRenderHint(QPainter.SmoothPixmapTransform);p.setTransform(qtransform(m@np.array([[1,0,x],[0,1,y],[0,0,1.]])));p.drawImage(0,0,part);p.end();return out
    def children(nodes):
        result=allocate(width,height)
        for row,descendants,partition in nodes:
            if descendants is not None:
                source=children(descendants)
                if row['type']=='Group' and (row['masks'] or row['crop']!=[0.,0.,1.,1.]):
                    # Synthetic dimensions only; coverage reads its bounded region.
                    class Dimensions:
                        def width(self):return (scene.get('canvas') or (1280,720))[0]
                        def height(self):return (scene.get('canvas') or (1280,720))[1]
                    im=Dimensions();frame=world_matrix(scene,row['id'])@np.array([[1/im.width(),0,-.5],[0,1/im.height(),-.5],[0,0,1.]])
                    mask=projected(row,im,frame,True);p=QPainter(source);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,mask);p.end()
            else:
                image=preview if row['id']==target and preview is not None else images.get(row['id'])
                if image is None:raise ValueError('Visible '+row['name']+' has no readable frame; Smudge cancelled.')
                source=projected(row,image,frames[row['id']])
            # Opacity is applied once, including ordinary parent isolation.
            if row['opacity']!=1:
                opacity=allocate(width,height);p=QPainter(opacity);p.setOpacity(row['opacity']);p.drawImage(0,0,source);p.end();source=opacity
            strength=row.get('blend_strength',1.);blend='Normal' if strength==0 else row['blend']
            original=result
            if blend=='Add':mixed=add_image(result,source)
            else:
                # Retain a separate backdrop only when partial blend interpolation needs it.
                mixed=result.copy() if blend!='Normal' and strength<1 else result
                p=QPainter(mixed);p.setCompositionMode(QPainter.CompositionMode_Plus if partition else modes[blend]);p.drawImage(0,0,source);p.end()
            if blend!='Normal' and strength<1:
                normal=original.copy();p=QPainter(normal);p.drawImage(0,0,source);p.end();a=np.frombuffer(normal.constBits(),np.uint8).astype(np.uint16);b=np.frombuffer(mixed.constBits(),np.uint8).astype(np.uint16);factor=round(strength*255);data=((a*(255-factor)+b*factor+127)//255).astype(np.uint8).tobytes();mixed=QImage(data,width,height,QImage.Format_ARGB32_Premultiplied).copy()
            result=mixed
        return result
    return children(artwork_sampling_plan(scene) if plan is None else plan)
