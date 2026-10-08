"""Isolated real-owner regression, synthetic Qt events; not native acceptance.

Requires an explicit new evidence directory. Never uses Robert's state/log paths.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,time,json,traceback,importlib.util
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QPointF,QMimeData
from PySide6.QtGui import QImage,QDragEnterEvent,QDropEvent
from PySide6.QtTest import QTest
from composition import History,defaults,new_layer,lookup

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    os.environ['ZERAWAVE_MEDIA_LIBRARY']=str(out/'library.json');os.environ['ZERAWAVE_ARTWORK_STORE']=str(out/'artwork')
    from studio_qt import Shell
    def error(self,exc,tb=None):
        text=''.join(traceback.format_exception(type(exc),exc,tb));self.errors.append(text);(out/'qt-errors.log').write_text('\n'.join(self.errors),encoding='utf8')
    Shell.error=error
    app=QApplication([]);shell=Shell(out/'layout.json',out/'owner.log');shell.show();checks=[]
    def pump(seconds=.06):
        end=time.monotonic()+seconds
        while time.monotonic()<end:app.processEvents();time.sleep(.005)
    def wait(fn,seconds=15):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            pump(.03)
            if fn():return
        raise AssertionError('Timed out: '+editor.status.text())
    try:
        wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading'])
        editor=shell.image_editor;canvas=editor.canvas;lib=shell.media_library
        shell.client.request('media_import',paths=[str(ROOT/'images n vids/Xeraphina.jpg'),str(ROOT/'images n vids/Bobs Mock up.jpg')]);wait(lambda:len(shell.client.snapshot['media_library']['assets'])==2 and not shell.client.snapshot['media_library']['pending'])
        image=next(a for a in shell.client.snapshot['media_library']['assets'] if a['name']=='Xeraphina');other=next(a for a in shell.client.snapshot['media_library']['assets'] if a['id']!=image['id'])
        editor.add_asset(image);parent=editor.selected;wait(lambda:image['id'] in editor.images);editor.resize_canvas((1792,1008),False);canvas.set_tool('Pencil');count=len(lib.assets)
        def stroke(tool='Pencil',evict=False):
            canvas.set_tool(tool);row=deepcopy(editor.selected_row());a=canvas.screen_point(row,(.35,.45));b=canvas.screen_point(row,(.55,.55));canvas.paint_press(row,a)
            assert canvas.stroke is not None,editor.status.text()
            if evict:editor.images.pop(row['asset'],None)
            canvas.paint_move(b);canvas.paint_finish();wait(lambda:not editor.art_jobs);wait(lambda:editor.selected_row()['asset'] in editor.images)
        stroke(evict=True);paint=editor.selected;assert paint!=parent and editor.selected_row()['parent']==parent and editor.selected_row()['type']=='Paint'
        assert lookup(editor.config)[parent]['type']=='Artwork';assert paint in lookup(editor.config);assert parent not in editor.collapsed
        editor.select(parent);stroke();assert editor.selected==paint and len(editor.config['layers'])==2
        first=editor.selected_row()['asset'];stroke();stroke('Eraser');editor.history(False);editor.history(True);lib.refresh();assert len(lib.assets)==count==2
        assert all(not a.get('internal') for a in lib.assets.values());assert shell.client.snapshot['media_library']['resources']
        checks.append('Auto first-stroke child, stable layer ID, private buffer survives cache eviction, brush/erase history, no Library entries')
        history_label=shell.client.snapshot['media_control']['history']['undo'];editor.tabs.setCurrentIndex(0);pump();node=editor.tree.currentItem()
        for column,key in ((1,'enabled'),(2,'locked')):
            prior=editor.selected_row()[key]
            for expected in (not prior,prior):
                node=editor.tree.currentItem();y=editor.tree.visualItemRect(node).center().y();x=editor.tree.header().sectionPosition(column)+editor.tree.columnWidth(column)//2
                QTest.mouseClick(editor.tree.viewport(),Qt.LeftButton,pos=QPointF(x,y).toPoint());pump();assert editor.selected_row()[key]==expected
        assert shell.client.snapshot['media_control']['history']['undo']==history_label
        import studio_composition
        original_asset=editor.selected_row()['asset'];wait(lambda:original_asset in editor.images);canvas.set_tool('Pencil');r=editor.selected_row();canvas.paint_press(r,canvas.screen_point(r,(.5,.5)))
        with patch.object(studio_composition,'store_image',side_effect=OSError('Injected immutable artwork write failure')):canvas.paint_finish();wait(lambda:not editor.art_jobs)
        assert editor.selected_row()['asset']==original_asset and 'previous content retained' in editor.status.text();assert shell.client.snapshot['media_control']['history']['undo']==history_label
        checks.append('QTest eye/lock signals commit safely without history; injected write failure retains source and undo state')
        # Excluded state survives full-scene Undo/Redo, including hidden original.
        editor.edit('enabled',False,'Visibility',True);editor.edit('locked',True,'Lock',True);label=shell.client.snapshot['media_control']['history']['undo'];assert 'stroke' in label.lower()
        editor.history(False);assert not editor.selected_row()['enabled'] and editor.selected_row()['locked'];editor.history(True);assert not editor.selected_row()['enabled'] and editor.selected_row()['locked']
        editor.edit('locked',False,'Unlock',True);editor.edit('enabled',True,'Show',True)
        wait(lambda:editor.selected_row()['asset'] in editor.images);canvas.set_tool('Pencil')
        # Completion generation cannot touch a scene replaced after gesture start.
        row=deepcopy(editor.selected_row());canvas.paint_press(row,canvas.screen_point(row,(.2,.2)));token=deepcopy({k:v for k,v in canvas.stroke.items() if k not in ('image','color')});canvas.cancel_drag();editor.rotate(90);assert not editor.valid_target(token['session'],token['revision'],token['target']);editor.rotate(-90)
        checks.append('Visibility/lock excluded, flags survive Undo/Redo; obsolete generation rejected; cancelled stroke retains committed image')
        canvas.set_tool('Pencil');editor.choose_shape('Circle');assert canvas.tool=='Mask' and canvas.shape=='Circle';editor.choose_tool('Cut');editor.choose_shape('Magnetic');assert canvas.tool=='Cut';editor.choose_tool('Crop');editor.choose_tool('Pencil');assert canvas.tool=='Pencil'
        editor.tools_palette();editor.tools_palette();editor.tools_palette();editor.brushes_palette();editor.brushes_palette();editor.brushes_palette();assert len(editor.palettes)==2
        for palette in editor.palettes:palette.resize(260,420);palette.move(120,100);pump();palette.remember();palette.close()
        editor.brushes_palette();assert len(editor.palettes)==2;assert editor.shell.preferences['media_palettes']['Brushes'][0]==120
        checks.append('One authoritative tool; shape leaves drawing; singleton palettes and geometry reopen')
        for palette in editor.palettes:palette.close()
        canvas.setFocus();row=editor.selected_row();a=canvas.screen_point(row,(.4,.5)).toPoint();b=canvas.screen_point(row,(.5,.5)).toPoint();canvas.set_tool('Pencil')
        QTest.mousePress(canvas,Qt.RightButton,pos=a);assert canvas.stroke and canvas.stroke['tool']=='Eraser';QTest.mouseMove(canvas,b);QTest.mouseRelease(canvas,Qt.RightButton,pos=b);wait(lambda:not editor.art_jobs);assert canvas.tool=='Pencil'
        wait(lambda:editor.selected_row()['asset'] in editor.images);QTest.mousePress(canvas,Qt.LeftButton,pos=a);assert canvas.stroke;canvas.cancel_drag();assert canvas.stroke is None and canvas.tool=='Pencil'
        canvas.set_tool('Crop');canvas.shape='Rectangle';row=editor.selected_row();a=canvas.screen_point(row,(.15,.15)).toPoint();b=canvas.screen_point(row,(.85,.85)).toPoint();QTest.mousePress(canvas,Qt.LeftButton,pos=a);QTest.mouseMove(canvas,b);QTest.mouseRelease(canvas,Qt.LeftButton,pos=b);assert len(canvas.points)==4
        side=canvas.screen_point(row,(.5,.15)).toPoint();end=canvas.screen_point(row,(.5,.25)).toPoint();QTest.mousePress(canvas,Qt.LeftButton,pos=side);assert canvas.point_drag==('side',0);QTest.mouseMove(canvas,end);QTest.mouseRelease(canvas,Qt.LeftButton,pos=end);assert abs(canvas.points[0][1]-.25)<.01;canvas.apply();assert abs(editor.selected_row()['crop'][1]-.25)<.01;editor.history(False)
        checks.append('QTest temporary right eraser retains Pencil, cancellation; crop corner and side-midpoint drag/apply/Undo')
        canvas.set_tool('Mask');canvas.shape='Rectangle';canvas.points=[[.2,.2],[.7,.2],[.7,.7],[.2,.7]];canvas.closed_path=True
        preview=deepcopy(canvas.points)
        with patch.object(editor,'commit',return_value=False):canvas.apply()
        assert canvas.points==preview;editor.refresh(True);canvas.discard()
        for shape in ('Rectangle','Square','Ellipse','Circle','Freehand','Curve','Magnetic'):
            canvas.set_tool('Cut');canvas.shape=shape;canvas.points=deepcopy(preview);canvas.closed_path=True
            if shape=='Curve':canvas.auto_handles()
            canvas.apply();assert not canvas.points and editor.selected_row()['masks'][-1]['mode']=='Cut';editor.history(False)
        canvas.set_tool('Mask');canvas.shape='Rectangle';canvas.points=deepcopy(preview);canvas.closed_path=True;mask=canvas.operation();before_masks=deepcopy(editor.config);editor.selected_row()['masks']=[deepcopy(mask) for _ in range(8)];editor.commit('Eight bounded masks',before_masks);canvas.points=deepcopy(preview);canvas.apply();assert canvas.points==preview and len(editor.selected_row()['masks'])==8;canvas.discard();editor.history(False)
        checks.append('All seven selection shapes commit one Cut/Undo; ninth mask rejected with editable preview retained')
        editor.copy_layer();before=deepcopy(editor.config);editor.paste_layer();copied=editor.selected;assert copied!=paint and len(editor.config['layers'])==len(before['layers'])+1;editor.history(False);assert copied not in lookup(editor.config);editor.history(True);assert copied in lookup(editor.config)
        checks.append('Failed selection commit retains preview; layer clipboard fresh IDs and one Undo')
        editor.select(parent);canvas.set_tool('Mask');canvas.shape='Ellipse';canvas.points=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]];canvas.closed_path=True;canvas.extract_preview();wait(lambda:not editor.art_jobs);extracted=editor.selected;assert extracted!=parent and editor.selected_row()['parent']==parent and not canvas.points
        editor.select(parent);editor.edit('source_visible',False,'Original visibility');assert lookup(editor.config)[extracted]['enabled'];editor.create_child(other,extracted);nested=editor.selected;assert editor.selected_row()['parent']==extracted
        checks.append('Extraction creates selected aligned child; original-only eye; nested imported child')
        # Actual async completion after a forced owner replacement must be ignored.
        import threading,studio_composition
        from artwork import store_image
        entered=threading.Event();release=threading.Event();before_async=deepcopy(editor.config)
        def delayed(*args,**kwargs):entered.set();assert release.wait(5);return store_image(*args,**kwargs)
        with patch.object(studio_composition,'store_image',side_effect=delayed):
            editor.blank_child();assert entered.wait(2)
            rows=[r for r in editor.config['layers'] if r['id']!=nested]
            shell.client.request('composition',version=3,canvas=editor.config['canvas'],presentation=editor.config['presentation'],layers=rows,label='Delete pending target',selection=parent);editor.refresh(True);release.set();wait(lambda:not editor.art_jobs)
        assert nested not in lookup(editor.config) and len(editor.config['layers'])==len(before_async['layers'])-1;assert 'obsolete edit not applied' in editor.status.text();editor.history(False);assert nested in lookup(editor.config)
        checks.append('Delayed writer completion after target deletion rejected without resurrecting target; Undo recovers prior committed content')
        shell.client.request('media_action',op='collection',command='create',name='Review');collection=next(iter(shell.client.snapshot['media_library']['collections']));lib.import_paths([image['path']],collection);wait(lambda:image['id'] in shell.client.snapshot['media_library']['collections'][collection]['assets'])
        lib.refresh();shell.panels['media'].toggleView(True);shell.panels['media'].setAsCurrentTab();pump();group=next(lib.tree.topLevelItem(i) for i in range(lib.tree.topLevelItemCount()) if lib.tree.topLevelItem(i).data(0,Qt.UserRole+1)==collection);location=lib.tree.visualItemRect(group).center();mime=QMimeData();mime.setData('application/x-zerawave-assets',json.dumps([other['id']]).encode());enter=QDragEnterEvent(location,Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(lib.tree.viewport(),enter);drop=QDropEvent(QPointF(location),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(lib.tree.viewport(),drop);assert drop.isAccepted();assert other['id'] in shell.client.snapshot['media_library']['collections'][collection]['assets']
        shell.client.request('media_action',op='collection',command='rename',collection=collection,name='Recovered sources');shell.client.request('media_action',op='collection',command='remove',collection=collection,assets=[other['id']]);assert other['id'] in {a['id'] for a in shell.client.snapshot['media_library']['assets']};shell.client.request('media_action',op='collection',command='add',collection=collection,assets=[other['id']])
        checks.append('Collection-targeted import, synthetic drag membership, rename, membership-only removal and re-add')
        before=deepcopy(editor.config);shell.client.request('media_action',op='remove',assets=[image['id'],other['id']],choice='layers',selection=nested);editor.refresh(True);assert not shell.client.snapshot['media_library']['assets'];editor.history(False);assert editor.config==before;assert set(shell.client.snapshot['media_library']['collections'][collection]['assets'])=={image['id'],other['id']}
        lib.refresh();lib.tree.setFocus();QTest.keyClick(lib.tree,Qt.Key_A,Qt.ControlModifier);assert set(lib.selected_ids())=={image['id'],other['id']};lib.type_filter.setCurrentText('Audio');assert lib.tree.topLevelItem(0).isHidden();lib.type_filter.setCurrentText('All types');assert not lib.tree.topLevelItem(0).isHidden()
        images=lib.tree.topLevelItem(0);QTest.mouseClick(lib.tree.viewport(),Qt.LeftButton,pos=lib.tree.visualItemRect(images.child(0)).center());QTest.mouseClick(lib.tree.viewport(),Qt.LeftButton,Qt.ControlModifier,pos=lib.tree.visualItemRect(images.child(1)).center());assert len(lib.selected_ids())==2
        QTest.mouseClick(lib.tree.viewport(),Qt.LeftButton,pos=lib.tree.visualItemRect(images.child(0)).center());QTest.mouseClick(lib.tree.viewport(),Qt.LeftButton,Qt.ShiftModifier,pos=lib.tree.visualItemRect(images.child(1)).center());assert len(lib.selected_ids())==2
        checks.append('Atomic batch removal/Undo restores references, memberships, layers; focused Ctrl-A deduplicates; filtered empty categories hidden')
        session=out/'review.json';shell.client.request('save',path=str(session));saved=json.loads(session.read_text(encoding='utf8'));assert all(Path(a['path']).exists() for a in saved['media']['assets'])
        shell.client.request('load',path=str(session));editor.refresh(True);wait(lambda:not shell.client.snapshot['media_library']['pending']);assert paint in lookup(editor.config);assert not shell.client.snapshot['media_control']['history']['undo']
        shell.client.request('composition_history',redo=False,media_session=editor.binding[0]);shell.client.request('composition_history',redo=True,media_session=editor.binding[0]);editor.history(False);editor.history(True);assert not shell.errors
        editor.select(paint);editor.rotate(90);editor.history(False);editor.rotate(-90);assert not shell.client.snapshot['media_control']['history']['redo'];editor.history(True);assert not shell.errors
        checks.append('Portable Save As/reopen retains drawings, history intentionally clears; exhausted owner/UI history no diagnostics; branch clears redo')
        assert not shell.client.snapshot['audio_hub']['playing'];assert shell.client.snapshot.get('preview_run') is None
        shell.grab().save(str(out/'studio.png'));(out/'RESULT.json').write_text(json.dumps(dict(checks=checks,evidence='Synthetic Qt + real isolated ControlOwner; no native mouse, audible audio or GPU claim'),indent=2));print('PASS',out,checks,flush=True)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc()+'\n'+(editor.status.text() if 'editor' in locals() else ''),encoding='utf8');(out/'failure-state.json').write_text(json.dumps(shell.client.snapshot if shell.client else {},indent=2),encoding='utf8');raise
    finally:
        if shell.client:
            shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True)
            with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
        pump(.15)

if __name__=='__main__':run()
