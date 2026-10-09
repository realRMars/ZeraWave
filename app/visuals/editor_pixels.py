"""Conventional transient pixel selection and immutable clipboard in the existing editor.

Only completed raster changes enter ControlOwner; gestures and clipboard metadata
are local. The OS payload carries its origin token, so replacing it retires origin.
"""
from copy import deepcopy
import hashlib,json,math,uuid
import numpy as np
from PySide6.QtCore import Qt,QPointF,QRectF,QMimeData
from PySide6.QtGui import QImage,QPainter,QColor,QPen
from PySide6.QtWidgets import QApplication
from composition import lookup,ancestors,effective,new_layer,world_matrix,coefficients,MAX_LAYERS
from editor_colors import pixel_frame
from pixel_selection import operation_image,encode
from raster_edit import coverage

MIME='application/x-zerawave-pixel-origin-v1'
RASTER=('Image','Artwork','Paint')
def materialize(image):return image.materialize().copy() if hasattr(image,'materialize') else image.copy()
def digest(image):
    im=image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
    return hashlib.sha256(bytes(im.constBits())).hexdigest()
def alpha(image):return np.frombuffer(image.constBits(),np.uint8).reshape(image.height(),image.bytesPerLine())[:,3:image.width()*4:4]
def constrained_copy(image,mask):
    result=materialize(image);p=QPainter(result);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,mask);p.end();return result
def clear(image,mask):
    if hasattr(image,'patch_many'):
        changes=[]
        for tile in image.tiles():
            bounds=(tile.x,image.height()-tile.y-tile.height,tile.width,tile.height)
            local_mask=mask.copy(*bounds)
            if not alpha(local_mask).any():continue
            part=image.region(bounds);before=bytes(part.constBits());p=QPainter(part);p.setCompositionMode(QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,local_mask);p.end()
            if bytes(part.constBits())!=before:changes.append((bounds,part))
        return image.patch_many(changes) if changes else image
    result=materialize(image);p=QPainter(result);p.setCompositionMode(QPainter.CompositionMode_DestinationOut);p.drawImage(0,0,mask);p.end();return result

def translated(image,mask,delta):
    result=clear(image,mask)
    if hasattr(image,'patch_many'):
        a=alpha(mask);ys=np.flatnonzero(a.any(axis=1));xs=np.flatnonzero(a.any(axis=0))
        if not len(xs):return image
        x,y=int(xs[0]),int(ys[0]);w,h=int(xs[-1]+1-x),int(ys[-1]+1-y)
        piece=image.region((x,y,w,h));p=QPainter(piece);p.setCompositionMode(QPainter.CompositionMode_DestinationIn);p.drawImage(0,0,mask.copy(x,y,w,h));p.end();changes=[]
        dx,dy=x+delta[0],y+delta[1]
        for tile in result.tiles():
            tx,ty=tile.x,result.height()-tile.y-tile.height
            if tx+tile.width<=dx or tx>=dx+w or ty+tile.height<=dy or ty>=dy+h:continue
            bounds=(tx,ty,tile.width,tile.height);part=result.region(bounds);before=bytes(part.constBits());p=QPainter(part);p.drawImage(dx-tx,dy-ty,piece);p.end()
            if bytes(part.constBits())!=before:changes.append((bounds,part))
        return result.patch_many(changes) if changes else result
    piece=constrained_copy(image,mask);p=QPainter(result);p.drawImage(delta[0],delta[1],piece);p.end();return result

class PixelEditor:
    def __init__(self,e):self.e=e;self.pin=None;self.gesture=None;self.clipboard=None;self.outline=None
    def error(self,message):self.e.status.setText(message);return False
    def readable(self,write=False,selection=True):
        e=self.e;c=e.canvas;row=e.selected_row()
        if not row or row['type'] not in RASTER:return self.error('Select a readable raster layer; moving media needs Snapshot current frame.')
        image=c.source_image(row)
        if image is None:return self.error('Selected source pixels are unavailable; wait for decoding or relink.')
        if image.width()*image.height()>8388608:return self.error('Pixel operation exceeds the 8 megapixel budget.')
        if write:
            if not e.editable_target(row):return False
            if not row['source_visible']:return self.error('Selected own content is hidden; show it before editing.')
            if e.edit_jobs or e.art_jobs or e.await_recovery:return self.error('Wait for the pending raster command before editing selected pixels.')
        if selection:
            if not c.points:return self.error('Select pixels first. Use Select Rectangle, Lasso or Magic Wand.')
            if self.pin and (self.pin[0]!=e.binding[0] or any(self.pin[1].get(k)!=row.get(k) for k in ('id','asset','parent','transform','fit','crop','flip_x','flip_y','masks'))):return self.error('Selection belongs to changed source geometry. Deselect and select again.')
            if self.pin and (self.pin[3]!=(image.width(),image.height()) or not np.allclose(self.pin[2],pixel_frame(c,row,image),atol=1e-12)):return self.error('Selection source or inherited placement changed. Deselect and select again.')
            if getattr(c,'selection_target',row['id'])!=row['id']:return self.error('Selection belongs to another layer. Select pixels on this layer.')
        return row,image
    def ready(self):
        c=self.e.canvas;row=self.e.selected_row()
        if not row:return
        image=c.source_image(row);self.pin=(self.e.binding[0],deepcopy(row),pixel_frame(c,row,image), (image.width(),image.height()));c.selection_target=row['id'];c.pixel_selection_ready=True;self.outline=None
        self.e.status.setText('Selected pixels ready • drag inside to move • Ctrl+C / X / V • Delete clears • Ctrl+D deselects');c.bubble.hide();c.update()
    def reset(self):
        self.pin=None;self.outline=None;self.gesture=None
        if self.e.canvas.stroke and self.e.canvas.stroke.get('tool')=='Move pixels':self.e.canvas.stroke=None
    def mask(self,row,image,visible=False):
        op=self.e.canvas.operation();size=(image.width(),image.height())
        return coverage((0,0,*size),size,row,op) if visible else operation_image(op,size)
    def save(self,row,image,label):
        e=self.e;base=e.canvas.source_image(row)
        stroke=dict(row=row['id'],asset=row['asset'],target=deepcopy(row),session=e.binding[0],revision=e.binding[1],tool=label,base=base)
        return e.save_paint(stroke,image)
    def copy(self,cut=False):
        if self.gesture:return self.error('Finish or cancel the current gesture before copying/cutting pixels.')
        found=self.readable(cut)
        if not found:return False
        row,image=found;e=self.e;previous=self.clipboard;export_attempted=False
        try:
            mask=self.mask(row,image,True)
            if not alpha(mask).any():return self.error('Selection has no available pixels in the crop/masks.')
            payload=constrained_copy(image,mask)
            if not alpha(payload).any():return self.error('Selection contains no visible raster pixels to copy.')
            # Complete allocation/admission preflight before replacing the clipboard.
            result=clear(image,mask) if cut else None
            if cut and (len(e.edit_jobs)>=16 or sum(p.size for p in e.runtime_producers.values())+image.sizeInBytes()*2>128*1024*1024):return self.error('Raster transfer capacity exhausted; Cut and clipboard unchanged.')
            token=uuid.uuid4().hex;identity=digest(payload)
            metadata=dict(token=token,sha256=identity,session=e.binding[0],frame=pixel_frame(e.canvas,row,image).tolist(),width=image.width(),height=image.height(),opacity=row['opacity'],blend=row['blend'],blend_strength=row['blend_strength'])
            mime=QMimeData();mime.setImageData(payload);mime.setData(MIME,json.dumps(metadata).encode('utf8'))
            clipboard=QApplication.clipboard();old=clipboard.mimeData();old_copy=QMimeData()
            for fmt in (old.formats() if old else []):old_copy.setData(fmt,old.data(fmt))
            if old and old.hasImage():old_copy.setImageData(clipboard.image())
            export_attempted=True
            clipboard.setMimeData(mime)
            check=clipboard.mimeData()
            if not check.hasImage() or bytes(check.data(MIME))!=json.dumps(metadata).encode('utf8') or digest(clipboard.image())!=identity:
                clipboard.setMimeData(old_copy);return self.error('Clipboard image export failed; source pixels unchanged.')
            self.clipboard=dict(metadata=metadata,image=payload.copy())
            if cut and not self.save(row,result,'Cut selected pixels'):
                clipboard.setMimeData(old_copy);self.clipboard=previous;return False
            if cut:e.canvas.discard()
            else:e.status.setText('Copied selected own pixels with alpha and original placement; source unchanged.')
            return True
        except Exception as exc:
            if export_attempted and 'old_copy' in locals() and 'clipboard' in locals():
                try:clipboard.setMimeData(old_copy)
                except Exception:pass
                self.clipboard=previous
            return self.error('Pixel copy/cut rejected; source unchanged: '+str(exc))
    def delete(self):
        if self.gesture:return self.error('Finish or cancel the current gesture before deleting pixels.')
        found=self.readable(True)
        if not found:return False
        row,image=found
        try:
            result=clear(image,self.mask(row,image,True))
            if digest(result)==digest(materialize(image)):return self.error('Selected pixels are already empty; no edit.')
            if self.save(row,result,'Delete selected pixels'):self.e.canvas.discard();return True
        except Exception as exc:return self.error('Delete rejected; artwork retained: '+str(exc))
        return False
    def paste(self):
        e=self.e;c=e.canvas;mime=QApplication.clipboard().mimeData()
        if mime is None or not mime.hasImage():return self.error('Clipboard contains no raster image. Layer/subtree Paste is an explicit Layers command.')
        if not e.resolve_pending():return False
        if len(e.config['layers'])>=MAX_LAYERS:return self.error('Paste exceeds the layer limit; clipboard and artwork unchanged.')
        active=e.selected_row();parent=active['parent'] if active else None
        if active and any(r['type']=='Group' and r['locked'] for r in ancestors(e.config,active['id'])):return self.error('Unlock the destination Group before pasting a sibling.')
        try:
            image=QApplication.clipboard().image()
            if image.isNull() or image.width()>8192 or image.height()>8192 or image.width()*image.height()>8388608:return self.error('Clipboard image unavailable or exceeds native raster capacity.')
            image=image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            meta=None
            if self.clipboard and mime.hasFormat(MIME):
                encoded=bytes(mime.data(MIME));offered=json.loads(encoded) if len(encoded)<=4096 else None
                if offered==self.clipboard['metadata'] and offered['sha256']==digest(image):meta=offered;image=self.clipboard['image'].copy()
            # Full-size payload has transparent selection margins. Its original
            # source-pixel affine remains independent of the current layer.
            from composition import asset_matrix
            template=new_layer('Image');template['fit']='Stretch';template['parent']=parent
            pm=world_matrix(e.config,parent) if parent else np.eye(3)
            if meta:
                desired=np.array(meta['frame'])@np.array([[image.width(),0,image.width()/2],[0,image.height(),image.height()/2],[0,0,1.]])
                template['transform']=coefficients(np.linalg.inv(pm)@desired);template['opacity']=meta['opacity'];template['blend']=meta['blend'];template['blend_strength']=meta['blend_strength']
            else:
                # External image: centered on canvas at one canvas pixel per
                # source pixel, independent of the active layer transform.
                cw,ch=e.canvas_size;desired=np.diag([image.width()/cw,image.height()/ch,1.]);template['transform']=coefficients(np.linalg.inv(pm)@desired)
            template['name']='Pasted pixels';anchor=deepcopy(active);binding=e.binding
            def finish(asset):
                if e.binding!=binding or (anchor and lookup(e.config).get(anchor['id'])!=anchor):raise ValueError('Paste destination changed; no layer inserted.')
                before=deepcopy(e.config);row=deepcopy(template);row['asset']=asset['id']
                siblings=sorted((r for r in e.config['layers'] if r['parent']==parent),key=lambda r:r['order'])
                index=next((i+1 for i,r in enumerate(siblings) if anchor and r['id']==anchor['id']),len(siblings));siblings.insert(index,row)
                for i,r in enumerate(siblings):r['order']=i
                e.config['layers'].append(row)
                from media_registry import reference
                e.config['assets'].append(reference(asset));e.selected=row['id'];c.discard();c.set_tool('Transform');e.commit('Paste editable pixels',before)
            return e.resource_generated(image,'Editable pixel clipboard',finish,active)
        except Exception as exc:return self.error('Paste rejected; artwork unchanged: '+str(exc))
    def press(self,event):
        c=self.e.canvas
        if c.tool not in ('Select','Selection','Wand') or event.button()!=Qt.LeftButton:return False
        if c.tool=='Wand' and not getattr(c,'pixel_selection_ready',False):return False
        found=self.readable(False,False)
        if not found:return True
        row,image=found;uv=c.mask_point(row,event.position(),False);pt=(uv[0]*image.width(),uv[1]*image.height())
        if not (0<=pt[0]<image.width() and 0<=pt[1]<image.height()):self.error('Start the selection inside the active raster.');return True
        prior=c.preview_state();bound=deepcopy(row)
        if c.points and getattr(c,'pixel_selection_ready',False):
            valid=self.readable(True)
            if valid:
                mask=self.mask(row,image,True)
                if mask.pixelColor(int(pt[0]),int(pt[1])).alpha()>0:
                    self.gesture=dict(kind='move',start=pt,row=bound,image=image,mask=mask,prior=prior,binding=self.e.binding,delta=(0,0));c.apply_tool_cursor();return True
        if c.tool=='Wand':return False
        self.gesture=dict(kind='select',start=pt,row=bound,image=image,prior=prior,binding=self.e.binding)
        c.pixel_op=None;c.pixel_overlay=None;c.pixel_selection_ready=False;c.points=[list(uv)];c.handles=[];c.closed_path=False;self.outline=None;c.update();return True
    def move(self,event):
        if not self.gesture:return False
        g=self.gesture;c=self.e.canvas;row=g['row'];image=g['image'];uv=c.mask_point(row,event.position(),False)
        if g['kind']=='move':
            delta=(round(uv[0]*image.width()-g['start'][0]),round(uv[1]*image.height()-g['start'][1]));g['delta']=delta
            try:
                preview=translated(image,g['mask'],delta)
                c.stroke=dict(row=row['id'],preview=preview,image=preview,tool='Move pixels',target=row,new_child=False)
                self.e.status.setText(f'Move selected pixels {delta[0]}, {delta[1]} px • release accepts • Esc cancels')
            except Exception as exc:self.cancel();self.error('Move preview rejected: '+str(exc))
        elif c.shape=='Freehand':
            p=[max(0.,min(1.,v)) for v in uv]
            if len(c.points)<4096 and math.dist(p,c.points[-1])>.0001:c.points.append(p)
        else:
            a=(g['start'][0]/image.width(),g['start'][1]/image.height());b=[max(0.,min(1.,v)) for v in uv]
            c.points=[[min(a[0],b[0]),min(a[1],b[1])],[max(a[0],b[0]),min(a[1],b[1])],[max(a[0],b[0]),max(a[1],b[1])],[min(a[0],b[0]),max(a[1],b[1])]]
        c.update();return True
    def release(self,event):
        if not self.gesture:return False
        g=self.gesture;self.gesture=None;c=self.e.canvas;c.apply_tool_cursor()
        if self.e.binding!=g['binding'] or self.e.selected_row()!=g['row']:c.stroke=None;self.restore(g);self.error('Obsolete gesture discarded; artwork unchanged.');return True
        if g['kind']=='move':
            preview=c.stroke['preview'] if c.stroke else None;c.stroke=None
            if g['delta']!=(0,0) and preview is not None and digest(preview)!=digest(materialize(g['image'])):
                if self.save(g['row'],preview,'Move selected pixels'):c.discard()
                else:self.restore(g)
            else:self.restore(g)
        elif len(c.points)>=3:
            c.closed_path=True;mask=self.mask(g['row'],g['image'])
            if alpha(mask).any():self.ready()
            else:self.restore(g)
        else:self.restore(g)
        c.update();return True
    def restore(self,g):
        c=self.e.canvas;c.points,c.handles,c.closed_path,c.pixel_op=deepcopy(g['prior']);c.pixel_selection_ready=bool(c.points);self.outline=None;c.update()
    def cancel(self):
        if not self.gesture:return False
        g=self.gesture;self.gesture=None;self.e.canvas.stroke=None;self.e.canvas.apply_tool_cursor();self.restore(g);self.e.status.setText('Gesture cancelled; prior artwork and selection restored.');return True
    def draw(self,painter,projection):
        c=self.e.canvas
        if not c.points or not getattr(c,'pixel_selection_ready',False):return
        found=self.readable(False)
        if not found:return
        row,image=found
        if self.outline is None:
            mask=self.mask(row,image);a=alpha(mask)>0
            edge=a&~(np.roll(a,1,0)&np.roll(a,-1,0)&np.roll(a,1,1)&np.roll(a,-1,1));edge[0]|=a[0];edge[-1]|=a[-1];edge[:,0]|=a[:,0];edge[:,-1]|=a[:,-1]
            out=QImage(image.width(),image.height(),QImage.Format_ARGB32_Premultiplied);out.fill(0)
            raw=np.frombuffer(out.bits(),np.uint8).reshape(out.height(),out.bytesPerLine())[:,:out.width()*4].reshape(out.height(),out.width(),4);raw[edge]=[255,255,255,255];self.outline=out
        from studio_composition import qtransform
        painter.save();painter.setTransform(qtransform(projection@pixel_frame(c,row,image)));painter.drawImage(0,0,self.outline);painter.restore()
