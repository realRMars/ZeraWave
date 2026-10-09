"""Source-bound B1 CPU / B2 fixed-region projection exact-pixel comparison."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_SCALE_FACTOR','1.5')
import importlib.util,sys,json,uuid
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
from PySide6.QtWidgets import QApplication,QComboBox,QLabel
from PySide6.QtGui import QImage,QColor
from PySide6.QtCore import QPointF
from composition import defaults,new_layer,transform,lookup
from native_raster import backend
from studio_composition import Canvas

def run(out,before):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);spec=importlib.util.spec_from_file_location('b1_cpu_reference',Path(before)/'app/visuals/studio_composition.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    app=QApplication([]);rng=np.random.default_rng(19);data=rng.integers(0,256,(391,523,4),dtype=np.uint8);data[:,:,:3]=np.minimum(data[:,:,:3],data[:,:,3,None]);image=QImage(data.tobytes(),523,391,QImage.Format_ARGB32_Premultiplied).copy();native=backend().storage().from_image(image)
    scene=defaults();scene['canvas']=[937,601];scene['presentation']='Layers only';refs=[dict(id=uuid.uuid4().hex,kind='Images',name='fixture',path='C:/ZeraWave/images n vids/Xeraphina.jpg') for _ in range(3)];scene['assets']=refs
    for i,ref in enumerate(refs):
        row=new_layer('Image',ref['id']);row.update(order=i,transform=transform(.05*i,-.06*i,.9-.2*i,.83-.1*i,17*i),crop=[.02,.07,.98,.91],flip_x=i==1,opacity=.57 if i else 1.);scene['layers'].append(row)
    scene['layers'][1]['masks']=[dict(enabled=True,mode='Keep',shape='Ellipse',points=[[.12,.09],[.87,.91]],handles=[])]
    def editor(native_route):
        e=SimpleNamespace(config=deepcopy(scene),canvas_size=(937,601),selected=None,images={ref['id']:native if native_route else image for ref in refs},editor_tools=QComboBox(),status=QLabel())
        e.editor_tools.addItems(['Select']);e.metadata=lambda row:dict(width=523,height=391);e.selected_row=lambda:None;e.sync_tool_ui=lambda:None;e.sync_controls=lambda:None;e.cancel_preview=lambda:None
        c=(Canvas if native_route else old.Canvas)(e);e.canvas=c;c.resize(809,463);c.zoom=.63;c.pan=QPointF(13,-9);c.show();return e,c
    left,b1=editor(False);right,b2=editor(True);checks=[]
    def check(name):
        b1.update();b2.update();app.processEvents();assert hasattr(b2,'composite_image'),right.status.text();a=np.frombuffer(b1.composite_image.constBits(),np.uint8);b=np.frombuffer(b2.composite_image.constBits(),np.uint8)
        if not np.array_equal(a,b):
            b1.composite_image.save(str(out/(name+'-b1.png')));b2.composite_image.save(str(out/(name+'-b2.png')));raise AssertionError((name,np.count_nonzero(a!=b),np.max(np.abs(a.astype(int)-b.astype(int)))))
        checks.append(name)
    try:
        for blend in ('Normal','Multiply','Screen','Add','Difference'):
            for strength in (0.,.37,1.):
                for e in (left,right):e.config['layers'][1].update(blend=blend,blend_strength=strength)
                check(blend+str(strength))
        group=new_layer('Group');group['order']=3;group['opacity']=.64;group['masks']=[dict(enabled=True,mode='Cut',shape='Rectangle',points=[[.2,.22],[.4,.8]],handles=[])];group['transform']=transform(.1,.03,.9,.9,-11)
        for e in (left,right):e.config['layers'].append(deepcopy(group));e.config['layers'][1]['parent']=group['id'];e.config['layers'][2]['parent']=e.config['layers'][1]['id']
        check('nested-own-group-isolation')
        previous=dict(b2.projection_cache.stats);part=image.copy(128,261,5,8);part.fill(QColor('#fe3280'));edited=native.patch((128,261,5,8),part);expected=image.copy()
        from PySide6.QtGui import QPainter
        p=QPainter(expected);p.setCompositionMode(QPainter.CompositionMode_Source);p.drawImage(128,261,part);p.end()
        left.images[refs[1]['id']]=expected;right.images[refs[1]['id']]=edited;check('small-source-edit-nested-masks')
        # Transformed filtered source edits deliberately invalidate broadly.
        assert b2.projection_cache.stats['region_policy']=='broad-preserve-Qt-filter-phase'
        for e in (left,right):e.config['layers'][1]['transform']=transform(-.18,.21,.71,.54,63);e.config['layers'][0]['source_visible']=False
        check('old-new-footprint-broad-invalidation')
        for c in (b1,b2):c.resize(653,387);c.pan=QPointF(-17,31);c.zoom=.41
        check('resize-view-broad-invalidation')
        for e in (left,right):
            e.config['layers']=e.config['layers'][:1];e.config['layers'][0].update(transform=transform(),crop=[0.,0.,1.,1.],flip_x=False,opacity=1.,fit='Stretch');e.canvas_size=(523,391);e.config['canvas']=[523,391];e.images[refs[0]['id']]=native if e is right else image
        for c in (b1,b2):c.resize(809,463);c.zoom=1/c.devicePixelRatioF();c.pan=QPointF(.5,1/6)
        check('physical-native-1to1')
        assert b2.projection_cache.stats['region_policy']=='integer-1:1',b2.projection_cache.stats
        previous=dict(b2.projection_cache.stats);left.images[refs[0]['id']]=expected;right.images[refs[0]['id']]=edited;check('native-small-edit')
        assert b2.projection_cache.stats['reused_regions']>previous['reused_regions']
        # Compare the B1 live partial route to the same B2 live damage route,
        # independently of the full filtered-view committed cache.
        from PySide6.QtCore import QRect
        b1.stroke=dict(row=left.config['layers'][0]['id'],preview=expected);b2.stroke=dict(row=right.config['layers'][0]['id'],preview=edited)
        rect=QRect(220,160,171,115);b1.repaint(rect);b2.repaint(rect);app.processEvents()
        assert bytes(b1.composite_image.constBits())==bytes(b2.composite_image.constBits());checks.append('live-partial-damage-route-exact-against-B1')
        b1.stroke=b2.stroke=None
        report=dict(checks=checks,cache=b2.projection_cache.stats,dpr=b2.devicePixelRatioF(),reference=str(before));(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    finally:b1.close();b2.close();app.processEvents()
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
