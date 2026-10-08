"""Standalone scoped-history, ROI pixel, and isolated Qt workflow checks."""
from pathlib import Path
from copy import deepcopy
import sys,os,time,json,traceback
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from composition import History,new_layer,defaults,lookup,effective
from PySide6.QtGui import QImage,QColor
from PySide6.QtCore import Qt,QRect,QTimer,QPointF
from PySide6.QtWidgets import QApplication,QMessageBox,QLineEdit,QLabel
from PySide6.QtTest import QTest
from artwork import brush_stroke,constrained_edit,edit_coverage

def contracts():
    h=History();scene=defaults();a=new_layer();b=new_layer();scene['layers']=[a,b]
    def edit(identity,key,value,scope='layers'):
        before=deepcopy(scene);lookup(scene)[identity][key]=value;h.record(before,scene,key,identity,identity,scope,identity if scope=='drawing' else None)
    edit(a['id'],'asset','a1','drawing');edit(b['id'],'asset','b1','drawing');edit(a['id'],'name','Renamed')
    scene=h.step(False,scene,'drawing',a['id']);assert lookup(scene)[a['id']]['asset'] is None and lookup(scene)[b['id']]['asset']=='b1' and lookup(scene)[a['id']]['name']=='Renamed'
    assert h.step(False,scene,'drawing',a['id']) is None
    scene=h.step(True,scene,'drawing',a['id']);assert lookup(scene)[a['id']]['asset']=='a1'
    before=deepcopy(scene);scene['layers']=[lookup(scene)[b['id']]];h.record(before,scene,'Delete',a['id'],b['id'])
    scene=h.step(False,scene);assert lookup(scene)[a['id']]['asset']=='a1'
    scene=h.step(False,scene,'drawing',a['id']);assert lookup(scene)[a['id']]['asset'] is None
    scene=h.step(True,scene);assert a['id'] not in lookup(scene)
    scene=h.step(False,scene);assert lookup(scene)[a['id']]['asset'] is None
    edit(b['id'],'name','B2');edit(b['id'],'name','B3');scene=h.step(False,scene);scene=h.step(False,scene);assert lookup(scene)[b['id']]['name'] not in ('B2','B3')
    scene=h.step(True,scene);assert lookup(scene)[b['id']]['name']=='B2';scene=h.step(True,scene);assert lookup(scene)[b['id']]['name']=='B3'
    for i in range(100):edit(b['id'],'name',str(i))
    assert len(h.undo)+len(h.redo)<=64 and h.snapshot()['bytes']<=8*1024*1024
    parent=new_layer();child=new_layer();child['parent']=parent['id'];parent['locked']=True;scene=dict(defaults(),layers=[parent,child]);assert not effective(scene,child,'locked');parent['type']='Group';assert effective(scene,child,'locked');parent['locked']=False;assert not effective(scene,child,'locked')
    # The incremental update must exactly equal the complete native calculation,
    # including crop, shaped mask, partial opacity and disjoint later segments.
    before=QImage(384,216,QImage.Format_ARGB32_Premultiplied);before.fill(QColor(20,90,160,140));after=before.copy();row=new_layer();row['crop']=[.05,.1,.95,.9];row['masks']=[dict(mode='Keep',shape='Ellipse',points=[[.1,.1],[.9,.1],[.9,.9],[.1,.9]],enabled=True)]
    coverage=edit_coverage((384,216),row);preview=before.copy();brush=dict(size=18,opacity=.37,hardness=.4,flow=.55,shape='Round')
    for a,b in (((40,70),(200,140)),((200,140),(270,90)),((30,180),(60,195))):
        brush_stroke(after,a,b,brush,QColor('#f9c372'),'Brush');bounds=(int(min(a[0],b[0])-14),int(min(a[1],b[1])-14),int(max(a[0],b[0])+14),int(max(a[1],b[1])+14));constrained_edit(before,after,row,opacity=.37,bounds=bounds,coverage=coverage,result=preview)
    whole=constrained_edit(before,after,row,opacity=.37);assert bytes(preview.constBits())==bytes(whole.constBits())
    from studio_resources import simple_resources
    snap=dict(running=True,resources=dict(wall=100,processes={'a':dict(roles=['gui'],process_cpu_percent=63),'b':dict(roles=['owner'],process_cpu_percent=60)},system_cpu_percent=4))
    assert simple_resources(snap,100)['CPU']=='123.0 %';snap['resources']['processes']['b']['process_cpu_percent']=None;assert 'partial' in simple_resources(snap,100)['CPU'];assert 'stale' in simple_resources(snap,110)['CPU']
    return ['Scoped own Undo retains other layer pixels and management fields; exhaustion no-op; deletion restores drawing stack; independent Redo order; aggregate 64 / 8 MiB', 'Ordinary versus Group inherited locks', 'Incremental/native full constraint exact pixel equality with mask/crop/opacity', '123% one-core aggregate, partial and stale CPU presentation']

def preview_regions(app):
    from types import SimpleNamespace
    from composition import transform,BLENDS
    from studio_composition import Canvas
    base=QImage(320,180,QImage.Format_ARGB32_Premultiplied);base.fill(QColor(30,80,170,180))
    back=QImage(320,180,QImage.Format_ARGB32_Premultiplied);back.fill(QColor(55,35,20))
    scene=defaults();scene['canvas']=[320,180]
    a=new_layer(asset='a');b=new_layer(asset='b');b['order']=1;b['opacity']=.57;b['blend_strength']=.43;b['crop']=[.1,.1,.9,.9];b['transform']=transform(.02,-.03,.9,.8,17)
    group=new_layer('Group');group['opacity']=.62;group['crop']=[.04,.03,.97,.95];b['parent']=group['id'];group['order']=1
    scene['layers']=[a,group,b];images={'a':back,'b':base}
    editor=SimpleNamespace(config=scene,canvas_size=(320,180),images=images,selected_row=lambda:None,metadata=lambda r:dict(width=320,height=180),pending_paint=None,sync_tool_ui=lambda:None,status=QLabel(),cancel_preview=lambda:None)
    c=Canvas(editor);c.resize(480,270);c.show();app.processEvents();results=[]
    try:
        for blend in BLENDS:
            b['blend']=blend;changed=base.copy();brush=dict(size=18,shape='Round',hardness=.4,flow=.6)
            c.stroke=None;c.repaint();app.processEvents()
            brush_stroke(changed,(130,72),(173,98),brush,QColor('#efd37b'),'Brush')
            c.stroke=dict(row=b['id'],preview=changed)
            corners=[c.screen_point(b,(x/320,y/180)) for x in (115,190) for y in (56,116)]
            from PySide6.QtGui import QPolygonF
            rect=QPolygonF(corners).boundingRect().adjusted(-4,-4,4,4).toAlignedRect()
            c.repaint(rect);app.processEvents();partial=c.composite_image.copy()
            c.repaint();app.processEvents();full=c.composite_image.copy()
            delta=np.abs(np.frombuffer(partial.constBits(),np.uint8).astype(int)-np.frombuffer(full.constBits(),np.uint8).astype(int))
            assert delta.max()<=3 and delta.mean()<.02,(blend,int(delta.max()),float(delta.mean()))
            results.append(dict(blend=blend,max=int(delta.max()),mean=float(delta.mean()),dpr=c.devicePixelRatioF()))
        # A source can extend beyond the logical canvas; the sampler must honor
        # the displayed canvas clip rather than its off-canvas cached pixels.
        c.zoom=.5;c.composite_image.fill(QColor('red'));assert c.sample_composite(QPointF(1,1)) is None
        uv=(.46,.52);radius=9;centre=c.screen_point(b,uv);dx=c.screen_point(b,(uv[0]+radius/320,uv[1]))-centre;dy=c.screen_point(b,(uv[0],uv[1]+radius/180))-centre
        for i in range(48):
            x,y=np.cos(i*np.pi/24),np.sin(i*np.pi/24);fast=centre+dx*x+dy*y;direct=c.screen_point(b,(uv[0]+x*radius/320,uv[1]+y*radius/180));assert abs(fast.x()-direct.x())+abs(fast.y()-direct.y())<1e-8
        from studio_composition import LayerTree
        from PySide6.QtWidgets import QTreeWidgetItem
        from PySide6.QtCore import QMimeData,QPoint
        from PySide6.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent
        accepted=[];host=SimpleNamespace(config=scene,library_drop=lambda payload,identity:accepted.append((payload,identity)),status=QLabel())
        tree=LayerTree(host);node=QTreeWidgetItem(['Raster destination']);node.setData(0,Qt.UserRole,b['id']);tree.addTopLevelItem(node);tree.resize(360,220);tree.show();app.processEvents();pos=tree.visualItemRect(node).center();mime=QMimeData();mime.setData('application/x-zerawave-assets',b'["existing-id"]')
        for event in (QDragEnterEvent(pos,Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier),QDragMoveEvent(pos,Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier),QDropEvent(QPointF(pos),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)):
            app.sendEvent(tree.viewport(),event);assert event.isAccepted(),event.type()
        app.processEvents();assert accepted==[(b'["existing-id"]',b['id'])];tree.close()
        return results
    finally:c.close()

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ['ZERAWAVE_MEDIA_LIBRARY']=str(out/'library.json');os.environ['ZERAWAVE_ARTWORK_STORE']=str(out/'artwork');checks=contracts()
    from studio_qt import Shell
    app=QApplication([]);checks.append('Partial canvas preview within Qt raster rounding tolerance of full repaint for nested cropped Group, transformed own raster, master/effect contributions, every blend: '+json.dumps(preview_regions(app)));shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=None
    def pump(duration=.04):
        end=time.monotonic()+duration
        while time.monotonic()<end:app.processEvents();time.sleep(.001)
    def wait(test):
        end=time.monotonic()+30
        while time.monotonic()<end:
            pump()
            if test():return
        raise AssertionError('Timeout: '+(e.status.text() if e else 'startup'))
    def done():wait(lambda:not e.art_jobs and e.selected_row() and e.canvas.source_image(e.selected_row()) is not None)
    def stroke(tool):
        c=e.canvas;e.choose_tool(tool);row=e.selected_row();a=c.screen_point(row,(.4,.45)).toPoint();b=c.screen_point(row,(.6,.55)).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=a);assert c.stroke,e.status.text();QTest.mouseMove(c,b,delay=0);QTest.mouseRelease(c,Qt.LeftButton,pos=b);done()
    try:
        wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;c=e.canvas;e.reveal();pump()
        e.blank_layer();done();parent=e.selected;first=e.selected_row()['asset'];stroke('Pencil');drawn=e.selected_row()['asset'];assert drawn!=first
        e.blank_layer(True);done();child=e.selected;e.row_flag(parent,'locked');assert not effective(e.config,e.selected_row(),'locked');stroke('Brush');e.row_edit(child,'name','Unlocked child','Rename');assert e.selected_row()['name']=='Unlocked child'
        e.history(False,'drawing');child_first=e.selected_row()['asset'];e.history(False,'drawing');assert e.selected_row()['asset']==child_first and len(e.config['layers'])==2
        e.history(True,'drawing');child_drawn=e.selected_row()['asset'];e.row_flag(parent,'locked')
        e.expand_row(parent);e.expand_row(child);assert set(e.expanded)=={parent,child} and all(any(w.text()==lookup(e.config)[i]['name'] for w in e.row_widgets[i].findChildren(QLineEdit)) for i in (parent,child))
        e.row_widgets[parent].opacity.setValue(45);pump();assert lookup(e.config)[parent]['opacity']==.45 and lookup(e.config)[child]['opacity']==1
        e.row_edit(parent,'blend','Multiply','Blend');assert lookup(e.config)[parent]['opacity']==.45
        e.group();group=e.selected;e.row_flag(group,'locked');assert effective(e.config,lookup(e.config)[child],'locked');e.row_flag(group,'locked');assert not effective(e.config,lookup(e.config)[child],'locked');e.ungroup();pump()
        e.select(child);e.tree.blockSignals(True)
        for i in (parent,child):e.row_items[i].setSelected(True)
        e.tree.blockSignals(False);count=shell.client.snapshot['media_control']['history']['undo_count'];e.delete();assert not e.config['layers'] and shell.client.snapshot['media_control']['history']['undo_count']==count+1
        e.history(False);assert {r['id'] for r in e.config['layers']}=={parent,child} and lookup(e.config)[child]['asset']==child_drawn;e.select(child);e.history(False,'drawing');assert lookup(e.config)[child]['asset']==child_first
        checks.append('Isolated real owner: ordinary locked parent child draw/rename; current-layer drawing exhaustion; inline expansion; row opacity; Group protection; deduplicated batch deletion / content / drawing recovery')
        for tool in ('Brush','Pencil','Sampler','Eraser','Smudge','Select','Crop','Cut','Hand','Zoom'):
            button=e.direct_buttons[tool];QTest.mouseClick(button,Qt.LeftButton);pump();assert c.tool==tool
            QTest.mouseDClick(button,Qt.LeftButton);pump();palette=next(p for p in e.palettes if p.title==tool+' settings');assert palette.isVisible()
            QTest.mouseDClick(button,Qt.LeftButton);pump();assert not palette.isVisible() and len([p for p in e.palettes if p.title==tool+' settings'])==1
        e.choose_tool('Brush');e.brush['size']=31;e.brush_color=QColor('#12bc56');e.choose_tool('Pencil');e.brush['size']=7;e.brush_color=QColor('#db3251');e.choose_tool('Brush');assert e.brush['size']==31 and e.brush_color.name()=='#12bc56';e.choose_tool('Sampler');e.receive_sample(QColor('#abcdef'));assert e.tool_states['Brush']['color'].name()=='#abcdef' and e.tool_states['Pencil']['color'].name()=='#db3251' and e.tool_states['Brush']['brush']['size']==31
        checks.append('Direct click / double-click singleton settings per tool; independent Brush/Pencil size/color; Sampler receiving tool preserves other settings')

        e.tool_settings('Brush');e.apply_brush_preset('Brush',48,.2);assert e.settings_widgets['Brush']['size'].value()==48 and e.settings_widgets['Brush']['hardness'].value()==20
        e.tool_settings('Brush');e.choose_tool('Select');e.select(child);e.expand_row(child) if child not in e.expanded else None
        shell.activateWindow();pump();field=e.tree.findChild(QLineEdit,'layer_'+child+'_name');field.setFocus();pump();QTest.keyClick(field,Qt.Key_End);QTest.keyClicks(field,'XYZ');QTest.keyClick(field,Qt.Key_Z,Qt.ControlModifier);assert field.text()==lookup(e.config)[child]['name']
        field.selectAll();QTest.keyClicks(field,'Keyboard name');QTest.keyClick(field,Qt.Key_Return);pump();newfield=e.tree.findChild(QLineEdit,'layer_'+child+'_name');assert app.focusWidget() is newfield and newfield.text()=='Keyboard name',(app.focusWidget(),newfield.text(),e.selected_row()['name'])
        from unittest.mock import patch
        before_asset=e.selected_row()['asset'];QTimer.singleShot(0,lambda:app.activeModalWidget().button(QMessageBox.No).click())
        e.select(None);e.drawing_onboarding();assert len(e.config['layers'])==2
        e.select(child)
        with patch('studio_composition.QColorDialog.getColor',return_value=QColor(70,160,220,128)):
            e.solid_fill()
        done();filled=e.selected_row()['asset'];assert filled!=before_asset;e.history(False,'drawing');assert e.selected_row()['asset']==before_asset
        # A protected member blocks the whole selected batch, including unlocked rows.
        e.row_flag(parent,'locked');e.tree.blockSignals(True)
        for identity in (parent,child):e.row_items[identity].setSelected(True)
        e.tree.blockSignals(False);before=deepcopy(e.config);e.delete();assert e.config==before;e.row_flag(parent,'locked')
        checks.append('Preset exact fields stay synchronized; scripted Qt text Undo and focus survive rename; No onboarding preserves layers; solid fill one drawing Undo; protected batch deletion is atomic')
        # Explicit native placement and resized asynchronous placement share one add transaction.
        asset=next(a for a in e.media_assets() if a['id']==lookup(e.config)[parent]['asset'])
        prior=len(e.config['layers']);assert e.add_asset(asset,another=True,placement=dict(parent=parent,above=None));assert len(e.config['layers'])==prior+1 and e.selected_row()['parent']==parent
        e.history(False);assert len(e.config['layers'])==prior
        checks.append('Library asset placement commits native parent and asset identity in one management command')
        e.select(child);e.choose_tool('Mask');e.choose_shape('Curve');c.discard();c.closed_path=False;row=deepcopy(e.selected_row());initial=deepcopy(e.config)
        for uv in ((.23,.25),(.78,.25),(.52,.78)):
            QTest.mouseClick(c,Qt.LeftButton,pos=c.screen_point(row,uv).toPoint());pump()
        assert len(c.points)==3 and len(c.handles)==3 and e.config==initial
        original_handle=deepcopy(c.handles[1][1]);point=c.screen_point(row,original_handle).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=point);QTest.mouseMove(c,point+__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(8,6));QTest.mouseRelease(c,Qt.LeftButton,pos=point);assert c.handles[1][1]!=original_handle
        c.toggle_closed();assert c.closed_path and e.config==initial;c.preview_history(False);assert not c.closed_path;c.toggle_closed();c.apply();assert not c.points and len(e.selected_row()['masks'])==len(row['masks'])+1
        e.history(False);assert e.selected_row()['masks']==row['masks'];e.history(True);mask=deepcopy(e.selected_row()['masks']);e.mask_list.setCurrentIndex(len(mask)-1);e.edit_mask();assert c.points and c.handles;c.points[0][0]+=.02;c.discard();assert e.selected_row()['masks']==mask
        e.history(False);e.choose_tool('Crop');c.discard();row=deepcopy(e.selected_row());a=c.screen_point(row,(.2,.2)).toPoint();b=c.screen_point(row,(.8,.8)).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=a);QTest.mouseMove(c,b);QTest.mouseRelease(c,Qt.LeftButton,pos=b);assert len(c.points)==4
        side=c.screen_point(row,((c.points[0][0]+c.points[1][0])/2,c.points[0][1])).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=side);assert c.point_drag==('side',0);QTest.mouseMove(c,side+__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(0,7));QTest.mouseRelease(c,Qt.LeftButton,pos=side);assert c.points[0][1]>.2;c.discard();assert e.selected_row()['crop']==row['crop']
        checks.append('Curve provisional anchors/handles, closure and preview Undo, Apply/management Undo/Redo, saved edit Discard; Crop side adjustment with Discard')
        c.grab().save(str(out/'canvas.png'));shell.grab().save(str(out/'studio.png'));assert not shell.errors,list(shell.errors)
        (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,history=shell.client.snapshot['media_control']['history'],limits='Scripted Qt input, not physical/native acceptance'),indent=2));print('\n'.join(checks))
    finally:
        shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True);shell.close();pump(.1)
if __name__=='__main__':run()
