"""Focused full-resolution coverage, geometry and actual Qt/owner workflows."""
from pathlib import Path
import sys,os,time,json,traceback,hashlib
from copy import deepcopy
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtWidgets import QApplication,QLineEdit
from PySide6.QtGui import QImage,QColor,QPainter
from PySide6.QtCore import Qt,QPointF
from PySide6.QtTest import QTest
from composition import defaults,new_layer,transform,asset_matrix,matrix,world_matrix,crop_preserving,lookup,validate_scene
from pixel_selection import select,encode,decode,operation_image
from artwork import masked
def geometry():
    checks=[]
    for flip in ((False,False),(True,False),(False,True),(True,True)):
        for fit in ('Fit','Fill','Stretch'):
            scene=defaults();scene['canvas']=[640,360];parent=new_layer('Group');parent['transform']=transform(.11,-.07,.73,1.1,31);row=new_layer();row.update(parent=parent['id'],fit=fit,transform=transform(-.09,.16,.67,1.3,-24),flip_x=flip[0],flip_y=flip[1]);child=new_layer();child.update(parent=row['id'],transform=transform(.05,.03,.2,.3,14));scene['layers']=[parent,row,child]
            def frame():
                c=row['crop'];f=np.diag([-1 if row['flip_x'] else 1,-1 if row['flip_y'] else 1,1]);u=np.array([[1/(c[2]-c[0]),0,-c[0]/(c[2]-c[0])-.5],[0,1/(c[3]-c[1]),-c[1]/(c[3]-c[1])-.5],[0,0,1]])
                return asset_matrix(scene,row,(640,360),(1792,1008))@f@u
            before=frame();child_before=world_matrix(scene,child['id']);crop_preserving(scene,row,(640,360),(1792,1008),[.07,.13,.42,.69]);assert np.max(abs(frame()-before))<1e-12;assert np.max(abs(world_matrix(scene,child['id'])-child_before))<1e-12
            checks.append('crop '+fit+' '+str(flip))
    scene=defaults();group=new_layer('Group');group.update(transform=transform(.1,-.2,.8,1.3,19),flip_x=True);child=new_layer();child['parent']=group['id'];scene['layers']=[group,child];before=world_matrix(scene,child['id']);crop_preserving(scene,group,(640,360),(1,1),[.1,.2,.6,.8]);assert np.array_equal(world_matrix(scene,child['id']),before);checks.append('Group crop clips unchanged local branch frame')
    return checks
def pixels():
    image=QImage(320,180,QImage.Format_ARGB32_Premultiplied);image.fill(QColor('#c00000'));p=QPainter(image);p.fillRect(20,20,80,80,QColor('#00c000'));p.fillRect(190,20,80,80,QColor('#00c000'));p.fillRect(55,50,20,20,QColor('#00c020'));p.end();row=new_layer()
    a=select(image,row,(30,30),0,True);b=select(image,row,(30,30),0,False);c=select(image,row,(30,30),35,True);assert a.sum()<b.sum() and a.sum()<c.sum()
    add=select(image,row,(200,30),0,True,a,'Add');sub=select(image,row,(30,30),0,True,add,'Subtract');assert np.array_equal(sub,b-a)
    expanded=select(image,row,(30,30),35,True,expand=2);contracted=select(image,row,(30,30),35,True,expand=-2);soft=select(image,row,(30,30),35,True,feather=3);assert expanded.sum()>c.sum()>contracted.sum() and np.any((soft>0)&(soft<255))
    op=encode(soft);assert np.array_equal(decode(tuple(op['size']),op['coverage']),soft)
    full=operation_image(op,(320,180));region=operation_image(op,(320,180),(18,17,70,60));copied=full.copy(18,17,70,60);assert bytes(region.constBits())==bytes(copied.constBits());result=masked(image,[op]);alpha=np.frombuffer(result.constBits(),np.uint8).reshape(180,result.bytesPerLine())[:,3:1280:4];assert np.array_equal(alpha,soft)
    return image,['Color tolerance / connected versus disjoint / Add / Subtract / expand / contract / feather and exact coverage roundtrip/regional reads']
def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'))
    app=QApplication([]);checks=geometry();fixture,pixel_checks=pixels();checks+=pixel_checks
    from studio_qt import Shell
    shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=None
    def pump():app.processEvents();time.sleep(.002)
    def wait(fn):
        end=time.perf_counter()+40
        while time.perf_counter()<end:
            pump()
            if fn():return
        raise AssertionError('timeout: '+(e.status.text() if e else 'startup'))
    def done():wait(lambda:not e.art_jobs and not e.edit_jobs and e.selected_row() and e.canvas.source_image(e.selected_row()) is not None)
    def stroke(tool,button=Qt.LeftButton,uv=(.25,.45)):
        e.choose_tool(tool);c=e.canvas;row=deepcopy(e.selected_row());a=c.screen_point(row,uv).toPoint();b=c.screen_point(row,(uv[0]+.06,uv[1]+.03)).toPoint();QTest.mousePress(c,button,pos=a);assert c.stroke,e.status.text();QTest.mouseMove(c,b,delay=0);QTest.mouseRelease(c,button,pos=b);done()
    try:
        wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;c=e.canvas;e.reveal();e.resize_canvas((320,180),False);e.blank_layer();done();parent=e.selected
        target=deepcopy(e.selected_row());e.save_paint(dict(row=target['id'],asset=target['asset'],target=target,session=e.binding[0],revision=e.binding[1],tool='Fixture'),fixture);done();original_asset=e.selected_row()['asset']
        e.choose_tool('Brush');q=e.quick_colors;assert e.color_toolbar.isVisible();q.set_color(QColor(20,70,230,128));q.assign('secondary');q.set_color(QColor(250,210,10,200));q.assign('main')
        for i in range(4):q.set_color(QColor(30+i*40,80,170,100+i*35));q.add_custom()
        assert len(shell.preferences['media_custom_colors'])==4;q.custom(2);assert e.brush_color.alpha()==170
        q.assign('secondary');before=QColor(e.tool_states['Brush']['secondary']);e.choose_tool('Pencil');q.set_color(QColor('#0000ff'));e.choose_tool('Brush');assert e.tool_states['Brush']['secondary']==before
        q.assign('main');q.set_color(QColor('red'));stroke('Brush',Qt.LeftButton,(.12,.7));stroke('Brush',Qt.RightButton,(.65,.7));assert c.source_image(e.selected_row()).pixelColor(210,130).alpha()>0
        for z in (17.,29.,43.):e.tool_value('Brush','size',z);q.add_size();done()
        assert e.config['editor']['custom_sizes']==[17.,29.,43.];e.tool_value('Brush','size',31);q.add_size();assert len(e.config['editor']['custom_sizes'])==3
        c.setFocus();pump();QTest.keyClick(c,Qt.Key_3);assert e.brush['opacity']==.3;QTest.keyClick(c,Qt.Key_0);assert e.brush['opacity']==1.
        e.tool_settings('Brush');assert 'color' not in e.settings_widgets['Brush'];e.tool_settings('Brush');checks.append('Sidebar closed-settings main/secondary RGBA, independent tools, four custom swatches, capacity, sizes, opacity keys; duplicate settings picker absent')
        e.choose_tool('Brush');c.setFocus();a=c.screen_point(e.selected_row(),(.85,.85)).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=a);pinned=c.stroke['brush']['opacity'];QTest.keyClick(c,Qt.Key_3);assert e.brush['opacity']==.3 and c.stroke['brush']['opacity']==pinned;QTest.mouseRelease(c,Qt.LeftButton,pos=a);done()
        q.size.lineEdit().setFocus();q.size.lineEdit().selectAll();QTest.keyClicks(q.size.lineEdit(),'29');assert e.brush['opacity']==.3;QTest.keyClick(q.size.lineEdit(),Qt.Key_Return);e.tool_value('Brush','opacity',1.)
        saved_colors=list(shell.preferences['media_custom_colors'])
        for i in range(16):q.set_color(QColor(i*13,200-i*7,90+i*4,80+i*9));q.add_custom()
        assert len(shell.preferences['media_custom_colors'])==16;q.custom(15);q.change_custom(15,False);q.set_color(QColor('#fea520'));q.add_custom();assert len(shell.preferences['media_custom_colors'])==16 and 'full' in e.status.text();q.change_custom(15,True);assert len(shell.preferences['media_custom_colors'])==15
        shell.preferences['media_custom_colors']=saved_colors;q.sync();checks.append('16 saved custom slots, full feedback, replace/remove; numeric typing and mid-gesture opacity pinning')
        e.choose_tool('Sampler');q.assign('secondary');secondary=QColor(e.tool_states['Brush']['secondary']);main=QColor(e.brush_color)
        from editor_colors import sample
        pos=c.screen_point(e.selected_row(),(.1,.1));sample(c,pos);assert e.brush_color==main;sample(c,pos,True);assert e.brush_color.name()=='#c00000' and e.tool_states['Brush']['secondary']==secondary and q.assignment=='main';sample(c,QPointF(-10000,-10000),True);assert e.brush_color.name()=='#c00000'
        e.row_flag(parent,'locked');sample(c,pos,True);e.row_flag(parent,'locked');checks.append('Sampler hover separate, click Main, Secondary unchanged, outside unchanged, readable lock')
        e.choose_tool('Wand');panel=e.selection_controls;panel.click(c.screen_point(e.selected_row(),(.1,.2)));wait(lambda:panel.job is None and getattr(c,'pixel_op',None));assert c.operation()['shape']=='Pixels';scene_before=deepcopy(e.config);panel.feather.setValue(2);wait(lambda:panel.job is None);assert e.config==scene_before;panel.commit_mask('Keep');done();assert e.selected_row()['masks'][-1]['shape']=='Pixels';e.history(False);done();assert e.selected_row()['masks']==scene_before['layers'][0]['masks'];e.history(True);done();e.history(False);done()
        e.choose_tool('Crop');assert panel.crop_apply.text()=='Apply crop' and not panel.tolerance.isVisible();c.points=[[.05,.1],[.47,.1],[.47,.65],[.05,.65]];before=deepcopy(e.config);landmarks=[c.screen_point(e.selected_row(),uv) for uv in ((.1,.2),(.3,.4))];panel.confirm();done()
        for uv,pos in zip(((.1,.2),(.3,.4)),landmarks):assert abs(c.screen_point(e.selected_row(),uv).x()-pos.x())+abs(c.screen_point(e.selected_row(),uv).y()-pos.y())<1e-7
        e.history(False);done();assert e.selected_row()['crop']==lookup(before)[parent]['crop'];e.choose_tool('Selection');c.points=[[.06,.12],[.31,.12],[.31,.52],[.06,.52]];c.closed_path=True;source_before=deepcopy(e.selected_row());e.extract_child(c.operation());done();child=e.selected;assert child!=parent and lookup(e.config)[parent]==source_before
        childrow=e.selected_row();bounds=c.content_bounds(childrow);assert bounds[2]-bounds[0]<.3 and bounds[3]-bounds[1]<.45;checks.append('Wand preview/mask one operation and management recovery; crop landmark stability; aligned source-preserving content-sized extraction')
        e.select(parent);e.choose_tool('Wand');panel.click(c.screen_point(e.selected_row(),(.1,.2)));e.select(child);stale_scene=deepcopy(e.config);wait(lambda:panel.job is None);assert e.config==stale_scene and not getattr(c,'pixel_op',None);checks.append('Async Wand target replacement ignores obsolete result without artwork mutation')
        e.select(parent);before=deepcopy(e.config);source=e.selected_row();source.update(transform=transform(.04,-.02,.83,1.2,26),flip_x=True,flip_y=True,opacity=.4);crop_preserving(e.config,source,e.canvas_size,(320,180),[.05,.05,.8,.8]);coverage=np.full((180,320),128,np.uint8);source['masks'].append(encode(coverage));e.commit('Transformed readable source fixture',before);done();e.choose_tool('Sampler');color=sample(c,c.screen_point(e.selected_row(),(.1,.1)));assert color.name()=='#c00000' and color.alpha()==51
        color=sample(c,c.screen_point(e.selected_row(),(.95,.95)));assert color is None or color.alpha()==0;e.history(False);done();checks.append('Selected-layer Sampler respects rotated/flipped independent scale, crop, pixel mask and own opacity')
        e.select(parent);e.blank_layer(True);done();blank=e.selected;blank_asset=e.selected_row()['asset'];e.row_flag(parent,'locked');source_before=deepcopy(lookup(e.config)[parent]);source_pixels=hashlib.sha256(bytes(c.source_image(source_before).constBits())).hexdigest();e.brush['strength']=.8;stroke('Smudge');assert e.selected_row()['asset']!=blank_asset and bytes(c.source_image(e.selected_row()).constBits()).count(0)<320*180*4;assert lookup(e.config)[parent]==source_before and hashlib.sha256(bytes(c.source_image(source_before).constBits())).hexdigest()==source_pixels;e.row_flag(parent,'locked');checks.append('Automatic visible-artwork Smudge on transparent child, locked readable source unchanged, selected target only')
        before=deepcopy(e.config);coverage=np.zeros((180,320),np.uint8);coverage[15:165,18:290]=255;coverage[65:75,130:200]=90;lookup(e.config)[parent]['masks'].append(encode(coverage));e.commit('Persist coverage fixture',before);done()
        save=out/'review.json';shell.client.request('save',path=str(save),save_id='usability-save');wait(lambda:save.exists() and shell.client.snapshot['media_control']['raster']['pending']==0);stored=json.loads(save.read_text());assert stored['media']['editor']['custom_sizes']==[17.,29.,43.] and lookup(stored['media'])[parent]['masks'][-1]['shape']=='Pixels'
        save_as=out/'review-copy.json';shell.client.request('save',path=str(save_as),save_id='usability-save-as');wait(lambda:save_as.exists());assert json.loads(save_as.read_text())['media']['editor']==stored['media']['editor']
        shell.client.request('load',path=str(save_as));wait(lambda:e.binding[0]==shell.client.snapshot['media_control']['session']);e.refresh(True);assert e.config['editor']['custom_sizes']==[17.,29.,43.];checks.append('Revision-pinned Save/Save As/load restores three session sizes, exact coverage and raster artwork')
        shell.save_layout();saved_preferences=json.loads((out/'layout.json').read_text())['controls'];assert saved_preferences['media_custom_colors']==shell.preferences['media_custom_colors'] and saved_preferences['media_tool_settings']['Brush']['secondary']==e.tool_states['Brush']['secondary'].name(QColor.HexArgb)
        assert not shell.errors,list(shell.errors);(out/'RESULT.json').write_text(json.dumps(dict(checks=checks,ui_timings=e.ui_timings,history=shell.client.snapshot['media_control']['history'],native='Qt QTest native-window events; separate physical-pointer review required'),indent=2));print(json.dumps(checks))
    except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc());raise
    finally:
        if shell.client:shell.client.close(force=True)
        shell.closing=True
        if e:e.close_resources()
        shell.close();app.processEvents()
if __name__=='__main__':run()
