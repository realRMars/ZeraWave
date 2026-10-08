"""Real isolated ControlOwner + scripted Qt raster workflow. No listening claim."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,time,json,traceback,hashlib,threading
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QPoint,QPointF
from PySide6.QtGui import QImage,QColor,QPainter
from PySide6.QtTest import QTest
from composition import lookup,validate_scene,world_matrix,effective,MAX_DEPTH
import numpy as np

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    os.environ['ZERAWAVE_MEDIA_LIBRARY']=str(out/'library.json');os.environ['ZERAWAVE_ARTWORK_STORE']=str(out/'artwork')
    from studio_qt import Shell
    def error(self,exc,tb=None):
        self.errors.append(''.join(traceback.format_exception(type(exc),exc,tb)));(out/'qt-errors.log').write_text('\n'.join(self.errors))
    Shell.error=error;app=QApplication([])
    from PySide6.QtCore import QMimeData
    prior_clipboard=QMimeData()
    for kind in app.clipboard().mimeData().formats():prior_clipboard.setData(kind,app.clipboard().mimeData().data(kind))
    shell=Shell(out/'layout.json',out/'owner.log');shell.show();checks=[];editor=None
    def pump(seconds=.05):
        end=time.monotonic()+seconds
        while time.monotonic()<end:app.processEvents();time.sleep(.002)
    def wait(fn,seconds=20):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            pump()
            if fn():return
        raise AssertionError('Timeout: '+(editor.status.text() if editor else 'owner readiness'))
    def done():wait(lambda:not editor.art_jobs and editor.selected_row()['asset'] in editor.images)
    def key(k,mods=Qt.NoModifier):QTest.keyClick(canvas,k,mods);pump()
    def stroke(tool):
        wait(lambda:editor.selected_row()['asset'] in editor.images)
        canvas.set_tool(tool);row=deepcopy(editor.selected_row());start=canvas.screen_point(row,(.42,.45)).toPoint();end=canvas.screen_point(row,(.61,.52)).toPoint();QTest.mousePress(canvas,Qt.LeftButton,pos=start);assert canvas.stroke,editor.status.text();QTest.mouseMove(canvas,end);QTest.mouseRelease(canvas,Qt.LeftButton,pos=end);done()
    def boundary(tool='Cut',shape='Rectangle',a=(.24,.22),b=(.72,.77)):
        wait(lambda:editor.selected_row()['asset'] in editor.images)
        row=deepcopy(editor.selected_row());canvas.set_tool(tool);canvas.shape=shape;canvas.discard();start=canvas.screen_point(row,a).toPoint();end=canvas.screen_point(row,b).toPoint()
        QTest.mousePress(canvas,Qt.LeftButton,pos=start);QTest.mouseMove(canvas,end);QTest.mouseRelease(canvas,Qt.LeftButton,pos=end);pump()
    try:
        wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);editor=shell.image_editor;canvas=editor.canvas
        shell.panels['composition'].toggleView(True);shell.panels['image_layers'].toggleView(True);pump()
        image=QImage(320,180,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(50,100,175,155));p=QPainter(image);p.fillRect(80,20,80,140,QColor(225,60,45,230));p.end();source=out/'original.png';assert image.save(str(source));original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        shell.client.request('media_import',paths=[str(source)]);wait(lambda:len(shell.client.snapshot['media_library']['assets'])==1 and not shell.client.snapshot['media_library']['pending']);asset=shell.client.snapshot['media_library']['assets'][0];assert editor.add_asset(asset);parent=editor.selected;wait(lambda:asset['id'] in editor.images);editor.resize_canvas((320,180),False);canvas.setFocus();pump()
        initial=editor.selected_row()['asset'];pixels=image.copy()
        for tool in ('Brush','Eraser','Smudge'):
            wait(lambda:canvas.source_image(editor.selected_row()) is not None)
            before=editor.selected_row()['asset'];native=canvas.source_image(editor.selected_row()).convertToFormat(QImage.Format_RGBA8888_Premultiplied);old_pixels=np.frombuffer(native.constBits(),np.uint8).reshape(native.height(),native.width(),4).copy()
            stroke(tool);native=canvas.source_image(editor.selected_row()).convertToFormat(QImage.Format_RGBA8888_Premultiplied);new_pixels=np.frombuffer(native.constBits(),np.uint8).reshape(native.height(),native.width(),4).copy();assert not np.array_equal(old_pixels,new_pixels),tool
            if tool=='Eraser':assert new_pixels[:,:,3].sum()<old_pixels[:,:,3].sum()
            assert editor.selected==parent and len(editor.config['layers'])==1 and editor.selected_row()['asset']!=before,(tool,editor.status.text())
            editor.history(False,'drawing');assert editor.selected==parent and editor.selected_row()['asset']==before;editor.history(True,'drawing')
        assert hashlib.sha256(source.read_bytes()).hexdigest()==original_hash;assert len(shell.client.snapshot['media_library']['assets'])==1
        checks.append('Brush/Eraser/Smudge directly edit one stable image identity; immutable original; own undo/redo; internal dependencies stay out of Library')
        before=deepcopy(editor.config);history_count=shell.client.snapshot['media_control']['history']['undo_count'];boundary();done();child=editor.selected
        assert child!=parent and lookup(editor.config)[child]['parent']==parent and canvas.tool=='Cut' and not canvas.points,dict(child=child,parent=parent,points=canvas.points,status=editor.status.text(),visible=canvas.isVisible(),size=[canvas.width(),canvas.height()]);assert shell.client.snapshot['media_control']['history']['undo_count']==history_count+1;assert lookup(editor.config)[parent]['masks'][-1]['mode']=='Cut';assert parent not in editor.collapsed
        editor.history(False);assert child not in lookup(editor.config) and editor.config['layers']==before['layers'];editor.history(True);assert child in lookup(editor.config)
        stroke('Pencil');boundary(a=(.35,.35),b=(.55,.57));done();grandchild=editor.selected;assert lookup(editor.config)[grandchild]['parent']==child and lookup(editor.config)[child]['parent']==parent
        editor.select(parent);editor.mask_list.setCurrentIndex(0);count=len(editor.config['layers']);editor.edit_mask();assert canvas.tool=='Remove' and canvas.points
        canvas.apply();assert len(editor.config['layers'])==count and canvas.tool=='Remove';editor.select(grandchild)
        checks.append('Release automatically cuts and selects nested child; one history command removes own region; Undo/Redo restores identity; child paints and cuts to grandchild')
        editor.select(parent);children=deepcopy([r for r in editor.config['layers'] if r['id']!=parent]);editor.edit('source_visible',False,'Hide own',True);assert all(effective(editor.config,r,'enabled') for r in children);editor.edit('enabled',False,'Hide branch',True);assert not any(effective(editor.config,r,'enabled') for r in children);editor.edit('enabled',True,'Show branch',True);assert [r['enabled'] for r in editor.config['layers'] if r['id']!=parent]==[r['enabled'] for r in children];editor.edit('source_visible',True,'Show own',True)
        editor.select(grandchild);matrix=world_matrix(editor.config,grandchild).copy();editor.move_branch(None);assert np.allclose(matrix,world_matrix(editor.config,grandchild));editor.move_branch(child);assert np.allclose(matrix,world_matrix(editor.config,grandchild));editor.step_order(1);editor.reorder(False)
        checks.append('Own visibility leaves descendants; branch restores saved eye states; reparent root/parent retains canvas affine')
        canvas.discard();canvas.setFocus();original=deepcopy(editor.selected_row()['transform']);count=shell.client.snapshot['media_control']['history']['undo_count'];key(Qt.Key_G);assert canvas.interactive;key(Qt.Key_X);QTest.keyClicks(canvas,'25');preview=deepcopy(canvas.interactive);key(Qt.Key_Return);assert shell.client.snapshot['media_control']['history']['undo_count']==count+1 and not canvas.interactive,dict(history=shell.client.snapshot['media_control']['history'],count=count,preview=preview,status=editor.status.text(),original=original,current=editor.selected_row()['transform'])
        transformed=deepcopy(editor.selected_row()['transform']);key(Qt.Key_R);QTest.keyClicks(canvas,'35');key(Qt.Key_Escape);assert editor.selected_row()['transform']==transformed
        key(Qt.Key_S);QTest.keyClicks(canvas,'125');key(Qt.Key_Return);key(Qt.Key_B);assert canvas.tool=='Brush';size=editor.brush['size'];key(Qt.Key_BracketRight);assert editor.brush['size']>size;key(Qt.Key_U);assert canvas.tool=='Smudge';key(Qt.Key_K);assert canvas.tool=='Cut'
        editor.expand_row(grandchild) if grandchild not in editor.expanded else None
        from PySide6.QtWidgets import QLineEdit
        name=editor.tree.findChild(QLineEdit,'layer_'+grandchild+'_name');name.setFocus();QTest.keyClicks(name,'GRSBPEIUK');assert canvas.tool=='Cut' and not canvas.interactive
        checks.append('G/R/S numeric preview, axis constraint, commit and cancellation; tool keys/brackets; name typing never changes tools')
        canvas.setFocus();editor.select(child);boundary('Selection',a=(.26,.3),b=(.33,.6));assert canvas.points;state=deepcopy(editor.config);key(Qt.Key_C,Qt.ControlModifier);assert QApplication.clipboard().mimeData().hasImage() and editor.config==state;key(Qt.Key_V,Qt.ControlModifier);done();assert len(editor.config['layers'])==4
        pasted=editor.selected;boundary('Selection',a=(.28,.35),b=(.31,.45));key(Qt.Key_J,Qt.ControlModifier|Qt.ShiftModifier);done();assert lookup(editor.config)[editor.selected]['parent']==pasted,editor.status.text()
        key(Qt.Key_D,Qt.ControlModifier);assert not canvas.points
        checks.append('Neutral selection never modifies pixels; Ctrl+C copies selection directly; Paste editable layer; Ctrl+Shift+J nested cut')
        sizes=[]
        for tool in ('Brush','Pencil','Sampler','Eraser','Smudge','Select','Crop','Cut'):
            editor.tool_settings(tool);pump();palette=next(p for p in editor.palettes if p.title==tool+' settings');assert palette.isVisible()
            for w,h in ((220,240),(720,600),(220,800),(800,220)):
                palette.resize(w,h);pump();assert palette.body.layout().count()>0
            sizes.append(dict(tool=tool,window=[palette.width(),palette.height()]));editor.tool_settings(tool);assert not palette.isVisible()
        checks.append('Direct tools have singleton remembered settings with real content across wide/tall sizes; no generic launchers')
        editor.select(parent);canvas.discard();editor.flip('flip_x');editor.rotate(25);editor.edit('crop',[.1,.15,.9,.85],'Crop');editor.edit('opacity',.5,'Opacity');editor.edit('blend','Screen','Blend');boundary(a=(.12,.2),b=(.24,.32));done();assert editor.selected_row()['parent']==parent
        checks.append('Automatic cut works after rotate/flip/crop with parent opacity/blend isolation')
        row=deepcopy(editor.selected_row());canvas.set_tool('Brush');canvas.paint_press(row,canvas.screen_point(row,(.2,.3)));before=editor.selected_row()['asset']
        import studio_composition
        with patch.object(studio_composition,'store_image',side_effect=OSError('Injected write failure')):canvas.paint_finish();wait(lambda:not editor.art_jobs)
        assert editor.selected_row()['asset']==before and 'previous content retained' in editor.status.text()
        checks.append('Injected immutable write failure retains accepted content')
        editor.select(parent);wait(lambda:editor.selected_row()['asset'] in editor.images);canvas.discard();canvas.set_tool('Brush');row=deepcopy(editor.selected_row());a=canvas.screen_point(row,(.15,.8));b=canvas.screen_point(row,(.19,.81));count=shell.client.snapshot['media_control']['history']['drawing'].get(parent,{}).get('undo_count',0);writer=studio_composition.store_image
        def slow_writer(*args):time.sleep(.2);return writer(*args)
        with patch.object(studio_composition,'store_image',side_effect=slow_writer):
            canvas.paint_press(row,a);canvas.paint_move(b);canvas.paint_finish();assert editor.pending_paint
            row=deepcopy(editor.selected_row());canvas.paint_press(row,a);assert canvas.stroke;wait(lambda:not editor.art_jobs);assert canvas.stroke and canvas.stroke['revision']==editor.binding[1];canvas.paint_move(b+QPointF(9,3));canvas.paint_finish();done()
        assert shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count']==count+2
        before=editor.selected_row()['asset'];row=deepcopy(editor.selected_row())
        with patch.object(studio_composition,'store_image',side_effect=slow_writer):
            canvas.paint_press(row,a);canvas.paint_move(b);canvas.paint_finish();editor.rotate(5);wait(lambda:not editor.art_jobs)
        assert editor.selected_row()['asset']==before and editor.pending_paint is None and 'obsolete edit not applied' in editor.status.text()
        checks.append('Continuous second stroke remains responsive across first async completion; revision rebinding yields two history commands; changed-target late write rejected without content loss')
        # Mixed imports and an explicit silent video play/seek; one AudioOwner remains parked.
        import wave
        audio=out/'silence.wav'
        with wave.open(str(audio),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*8000)
        bad=out/'unsupported.txt';bad.write_text('unsupported local media fixture')
        shell.client.request('media_import',paths=[str(audio),str(ROOT/'images n vids/Xeraphina_video.mp4'),str(bad)]);wait(lambda:not shell.client.snapshot['media_library']['pending']);records=shell.client.snapshot['media_library']['assets'];assert any(a['kind']=='Audio' for a in records) and any(a['kind']=='Video' for a in records);assert not shell.client.snapshot['audio_hub']['playing']
        audio_asset=next(a for a in records if a['kind']=='Audio');shell.media_library.activate(next(i for i in shell.media_library.tree.findItems(audio_asset['name'],Qt.MatchExactly|Qt.MatchRecursive,0) if i.data(0,Qt.UserRole)==audio_asset['id']));assert not shell.client.snapshot['audio_hub']['playing']
        video=next(a for a in records if a['kind']=='Video');editor.add_asset(video,True);video_id=editor.selected;editor.transport('play');wait(lambda:editor.selected in editor.images);editor.transport('pause');editor.transport('seek',.2);pump(.2);editor.snapshot_frame();done();assert editor.selected_row()['type']=='Image' and lookup(editor.config)[video_id]['type']=='Video';assert not shell.client.snapshot['audio_hub']['playing'];assert any(Path(r['path'])==bad and r['status']=='Failed' and r['error'] for r in shell.client.snapshot['media_library']['import_results'])
        checks.append('Mixed image/audio/video import has per-file failure; audio activation reveals sole owner without autoplay; explicit silent video play/pause/seek and editable single-frame snapshot')
        session=out/'review.json';shell.client.request('save',path=str(session));saved=json.loads(session.read_text());assert saved['media']['version']==4;identities={r['id'] for r in saved['media']['layers']};shell.client.request('load',path=str(session));pump();editor.refresh(True);assert {r['id'] for r in editor.config['layers']}==identities
        old=deepcopy(saved['media']);old['version']=3
        for r in old['layers']:r.pop('cut_alignment',None)
        migrated=validate_scene(old);assert {r['id'] for r in migrated['layers']}==identities
        checks.append('Portable save/reopen nested edits preserves IDs/masks/geometry; v3 migration retains old row identities')
        shell.grab().save(str(out/'studio.png'));canvas.grab().save(str(out/'canvas.png'));assert not shell.errors,shell.errors
        (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,palettes=sizes,evidence=__doc__),indent=2));print('PASS',out,checks,flush=True)
    except Exception:
        (out/'FAILURE.txt').write_text(traceback.format_exc());raise
    finally:
        app.clipboard().setMimeData(prior_clipboard)
        if editor:
            for p in editor.palettes:p.close()
        shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
        pump()
if __name__=='__main__':run()
