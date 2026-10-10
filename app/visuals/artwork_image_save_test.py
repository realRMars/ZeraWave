"""Focused artwork-image pixel/scope/writer safety; standalone, no pytest."""
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import sys,json,threading,time,hashlib,os
from unittest.mock import patch
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor,QPainter,QImageReader
from composition import defaults,new_layer,lookup,transform,validate_scene
from artwork_export import capture,compose,write_image,formats,ImageSaves,validate_outputs,output_key
from native_raster import backend
def pixels(im):
    im=im.convertToFormat(QImage.Format_RGBA8888);return bytes(im.constBits())
def run(out):
    out.mkdir(parents=True,exist_ok=False);app=QApplication([]);checks=[];caps=formats();(out/'formats.json').write_text(json.dumps(caps,indent=2),'utf8')
    scene=defaults();scene.update(canvas=[64,48],presentation='Layers only');images={}
    def row(name,color,parent=None):
        r=new_layer('Image',name=name);r['asset']=r['id'];r['fit']='Stretch';r['parent']=parent;r['order']=sum(v['parent']==parent for v in scene['layers']);scene['layers'].append(r)
        im=QImage(64,48,QImage.Format_ARGB32_Premultiplied);im.fill(QColor(color));images[r['asset']]=backend().storage().from_image(im) if backend().available else im
        scene['assets'].append(dict(id=r['asset'],name=name,kind='Images',path=str(out/(r['id']+'.png'))));return r
    back=row('back','#406080');parent=row('parent','#ff0000');parent['opacity']=.6;parent['transform']=transform(.2,0,.5);child=row('child','#00ff00',parent['id']);child['transform']=transform(.25,.1,.5);hidden=row('hidden','#0000ff');hidden['enabled']=False
    editor=SimpleNamespace(config=scene,images=images,canvas_size=(64,48),binding=('fixture',7),edit_jobs=[],art_jobs=[],await_recovery=False,pending_paint=None,canvas=SimpleNamespace(stroke=None),metadata=lambda r:dict(width=64,height=48))
    pin=capture(editor,'composition',[]);original=compose(pin);assert original.size()==images[back['asset']].size();assert original.pixelColor(0,0).blue()!=255;checks.append('composition dimensions/hidden content')
    own=compose(capture(editor,'own',[parent['id']]));branchpin=capture(editor,'branch',[parent['id']]);branch=compose(branchpin);combined=compose(capture(editor,'selection',[parent['id'],child['id']]));assert pixels(branch)==pixels(combined);assert pixels(own)!=pixels(branch);checks.append('own/branch/overlapping branches aligned once')
    # Off-canvas content expands selected bounds at the same pixel scale.
    parent['transform']=transform(1.2,.1,.5);off=capture(editor,'branch',[parent['id']]);assert off['bounds'][0]>=64;assert off['bounds'][2]==branchpin['bounds'][2];checks.append('off-canvas geometric bounds no clipping/recentering')
    parent['transform']=transform(.2,0,.5)
    frozen=capture(editor,'composition',[]);before=pixels(compose(frozen));old=images[parent['asset']];new=QImage(64,48,QImage.Format_ARGB32_Premultiplied);new.fill(QColor('#ffff00'));images[parent['asset']]=backend().storage().from_image(new) if backend().available else new;parent['opacity']=.2;assert pixels(compose(frozen))==before;images[parent['asset']]=old;parent['opacity']=.6;checks.append('immutable pixel/metadata capture after later edit')
    parent['masks']=[dict(shape='Rectangle',points=[[0,0],[.5,0],[.5,1],[0,1]],mode='Keep',enabled=True)];child['blend']='Add';child['blend_strength']=.4
    masked=capture(editor,'branch',[parent['id']]);rendered=compose(masked);assert rendered.width()>0;checks.append('transformed crop/mask/partial Add')
    opts=dict(background='#ffffff',quality=98);event=threading.Event();output=out/'transparent.png';result=write_image(masked,output,'png',opts,event,caps);decoded=QImage(str(output));assert decoded.size()==rendered.size();assert pixels(decoded)==pixels(rendered);assert decoded.hasAlphaChannel();checks.append('PNG exact decoded straight RGBA and transparency')
    jpeg=out/'flattened.jpg';write_image(masked,jpeg,'jpeg',opts,event,caps);im=QImage(str(jpeg));assert im.size()==rendered.size() and not im.hasAlphaChannel();checks.append('JPEG explicit white background and lossy decoded dimensions')
    bmp=out/'flattened.bmp';write_image(masked,bmp,'bmp',dict(background='#204060',quality=95),event,caps);assert QImage(str(bmp)).size()==rendered.size();checks.append('additional BMP installed opaque writer')
    good=output.read_bytes();event.set()
    try:write_image(masked,output,'png',opts,event,caps);raise AssertionError('cancel not honored')
    except InterruptedError:pass
    event.clear();assert output.read_bytes()==good
    with patch('artwork_export.os.replace',side_effect=PermissionError('controlled replacement denied')):
        try:write_image(masked,output,'png',opts,event,caps);raise AssertionError('replacement not failed')
        except PermissionError:pass
    assert output.read_bytes()==good and not list(out.glob('*.tmp'));checks.append('cancel/replacement failure protects good output and temp cleanup')
    for fmt,destination in [('nonsense',out/'bad.nonsense'),('png',out/'wrong.jpg')]:
        try:write_image(masked,destination,fmt,opts,event,caps);raise AssertionError('unsupported mismatch accepted')
        except ValueError:pass
    try:write_image(masked,out/'missing-folder/bad.png','png',opts,event,caps);raise AssertionError('bad write accepted')
    except FileNotFoundError:pass
    assert output.read_bytes()==good;checks.append('unsupported format/extension/write failure truthful')
    with patch('artwork_export.compose',return_value=QImage()):
        try:write_image(masked,output,'png',opts,event,caps);raise AssertionError('empty-image encoding succeeded')
        except OSError:pass
    assert output.read_bytes()==good and not list(out.glob('*.tmp'));checks.append('actual Qt encoder rejection of controlled empty image preserves good output')
    saves=ImageSaves();held=threading.Event();started=threading.Event();real=write_image
    def slow(*a,**k):started.set();held.wait(5);return real(*a,**k)
    with patch('artwork_export.write_image',side_effect=slow):
        saves.submit(frozen,out/'ordered.png','png',opts);assert started.wait(3);later=capture(editor,'composition',[]);saves.submit(later,out/'ordered.png','png',opts)
        try:saves.submit(later,out/'third.png','png',opts);raise AssertionError('unbounded jobs')
        except ValueError:pass
        held.set();deadline=time.monotonic()+10
        while saves.jobs and time.monotonic()<deadline:saves.poll();time.sleep(.005)
    assert not saves.jobs and len(saves.results)==2 and all(v['status']=='durable' for v in saves.results);assert pixels(QImage(str(out/'ordered.png')))==pixels(compose(later));saves.close();checks.append('two bounded immutable saves ordered at same destination')
    values=[dict(scope='own',targets=[parent['id']],path=str(output),format='png',background='#ffffff',quality=95,fingerprint='')];assert validate_outputs(values)==values;assert output_key('own',[child['id']])!=output_key('own',[parent['id']]);assert output_key('branch',[parent['id']])!=output_key('own',[parent['id']]);checks.append('separate stable destination scope validation')
    for flag in ('edit_jobs','art_jobs','pending_paint'):
        setattr(editor,flag,[True])
        try:capture(editor,'composition',[]);raise AssertionError('unaccepted capture')
        except ValueError:pass
        setattr(editor,flag,None if flag=='pending_paint' else [])
    checks.append('pending/unknown/previews refused')
    (out/'result.json').write_text(json.dumps(dict(checks=checks,native=backend().status(),format_results=result),indent=2),'utf8');print('passed',len(checks),checks,flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
