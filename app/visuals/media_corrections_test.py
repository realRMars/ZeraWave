"""Correction workflow checks with real Qt/ControlOwner on isolated storage.

QTest interactions are synthetic events, not physical mouse acceptance. No audio
capture/output and no world renderer. Failures and snapshots are retained.
"""
from pathlib import Path
from copy import deepcopy
import json,os,sys,time,traceback,hashlib,faulthandler
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtGui import QImage,QDragEnterEvent,QDropEvent
from PySide6.QtCore import Qt,QPoint,QPointF,QMimeData,QUrl
from PySide6.QtTest import QTest
from composition import lookup,world_matrix,asset_matrix,validate_scene
import numpy as np

def run():
    from studio_qt import Shell
    out=ROOT/'work/media-corrections-20261007'/('qt-'+str(time.time_ns()));out.mkdir();os.environ['ZERAWAVE_MEDIA_LIBRARY']=str(out/'library.json');os.environ['ZERAWAVE_ARTWORK_STORE']=str(out/'artwork')
    fault_log=(out/'native-faults.txt').open('w');faulthandler.enable(file=fault_log)
    app=QApplication([]);shell=Shell(out/'layout.json',out/'owner.log');shell.show();checks=[]
    def pump(seconds=.08):
        end=time.monotonic()+seconds
        while time.monotonic()<end:app.processEvents();time.sleep(.004)
    def wait(fn,timeout=15):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            pump(.02)
            if fn():return
        raise AssertionError('Timeout; '+editor.status.text() if 'editor' in locals() else 'Timeout')
    def pixels(image):return np.frombuffer(image.constBits(),np.uint8).copy()
    try:
        wait(lambda:shell.client is not None and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);editor=shell.image_editor;canvas=editor.canvas;areas={k:id(d.dockAreaWidget()) for k,d in shell.panels.items()}
        shell.client.request('media_import',paths=[str(ROOT/'images n vids/Xeraphina.jpg'),str(ROOT/'images n vids/Bobs Mock up.jpg'),str(ROOT/'images n vids/Xeraphina_video.mp4')]);wait(lambda:len(shell.client.snapshot['media_library']['assets'])==3 and not shell.client.snapshot['media_library']['pending']);assets=shell.client.snapshot['media_library']['assets'];image=next(a for a in assets if a['name']=='Xeraphina');other=next(a for a in assets if a['name']=='Bobs Mock up');video=next(a for a in assets if a['kind']=='Video')
        editor.add_asset(image);parent=editor.selected;wait(lambda:image['id'] in editor.images);assert editor.images[image['id']].size().width()==1792;assert editor.images[image['id']].size().height()==1008
        shell.panels['image_layers'].toggleView(True);shell.panels['image_layers'].setAsCurrentTab();editor.tabs.setCurrentIndex(1);editor.section_buttons['Position'].click();shell.panels['composition'].toggleView(True);shell.panels['composition'].setAsCurrentTab();pump()
        original=deepcopy(editor.selected_row()['transform']);spin=editor.fields['x'];QTest.mouseClick(spin.up,Qt.LeftButton);pump(.4);assert abs(editor.selected_row()['transform'][4]-.001)<1e-6
        QTest.mouseClick(spin.down,Qt.LeftButton);pump(.4);assert abs(editor.selected_row()['transform'][4])<1e-6
        spin.setFocus();QTest.keyClick(spin,Qt.Key_Up);pump(.4);assert abs(editor.selected_row()['transform'][4]-.001)<1e-6
        spin.lineEdit().selectAll();QTest.keyClicks(spin,'12.3');QTest.keyClick(spin,Qt.Key_Return);pump();assert abs(editor.selected_row()['transform'][4]-.123)<1e-6
        checks.append('Native-size decoded still; explicit spin buttons, keyboard arrow and typed 0.1 precision propagated via real owner')
        editor.fit_action();assert np.allclose(world_matrix(editor.config,parent),np.eye(3));editor.fit_action('Stretch');assert editor.selected_row()['fit']=='Stretch';editor.fit_action('Fill');assert editor.selected_row()['fit']=='Fill';editor.fit_action('Fit')
        editor.edit('aspect_lock',False,'Unlock independent scales');editor.fields['scale'].setValue(70);editor.numeric_finish();editor.fields['scale_y'].setValue(40);editor.numeric_finish();assert not np.isclose(editor.selected_row()['transform'][0],editor.selected_row()['transform'][3]);editor.rotate(90);editor.rotate(-90);editor.fit_action()
        editor.copy_layer();editor.paste_layer();pasted=editor.selected;assert pasted!=parent and editor.selected_row()['asset']==image['id'],editor.status.text();editor.history(False);assert pasted not in lookup(editor.config);editor.history(True);assert pasted in lookup(editor.config);editor.select(pasted);editor.delete();editor.select(parent)
        editor.create_child(other,parent);child=editor.selected;assert editor.selected_row()['parent']==parent;editor.select(parent);assert editor.selected_row()['type']=='Artwork';editor.edit('source_visible',False,'Hide original');assert lookup(editor.config)[child]['enabled'];assert editor.selected_row()['enabled'];editor.edit('source_visible',True,'Show original');editor.select(child);editor.fields['x'].setValue(5);editor.numeric_finish();editor.select(parent);editor.fields['x'].setValue(10);editor.numeric_finish();assert not np.allclose(world_matrix(editor.config,child),np.eye(3));editor.fit_action()
        editor.collapsed.add(parent);editor.populate();editor.refresh(True);assert parent in editor.collapsed
        checks.append('Fit recovers placement; Fill/Stretch distinct; independent scaling and ±90; Copy/Paste new IDs; artwork child inheritance and original-only visibility; collapse retained')
        editor.select(parent);canvas.set_tool('Crop');canvas.shape='Rectangle';a=canvas.screen_point(editor.selected_row(),(.1,.1)).toPoint();b=canvas.screen_point(editor.selected_row(),(.9,.9)).toPoint();QTest.mousePress(canvas,Qt.LeftButton,pos=a);QTest.mouseMove(canvas,b,delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=b);assert len(canvas.points)==4;canvas.discard();assert editor.selected_row()['crop']==[0,0,1,1]
        QTest.mousePress(canvas,Qt.LeftButton,pos=a);QTest.mouseMove(canvas,b,delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=b);canvas.apply();assert np.allclose(editor.selected_row()['crop'],[.1,.1,.9,.9],atol=.003);editor.history(False)
        for shape in ('Rectangle','Ellipse','Curve','Freehand','Magnetic'):
            canvas.set_tool('Mask');canvas.shape=shape;canvas.points=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]
            if shape=='Curve':canvas.auto_handles();assert len(canvas.handles)==4
            canvas.apply();assert editor.selected_row()['masks'][-1]['shape']==('Path' if shape in ('Freehand','Magnetic') else shape);editor.history(False)
        canvas.set_tool('Extract');canvas.shape='Ellipse';canvas.points=[[.25,.2],[.75,.2],[.75,.8],[.25,.8]];canvas.apply();wait(lambda:not editor.art_jobs);extracted=editor.selected;assert extracted!=parent and editor.selected_row()['parent']==parent;assert editor.selected_row()['masks'][-1]['shape']=='Ellipse';assert editor.metadata(editor.selected_row())['width']==1792
        editor.select(parent);editor.blank_child();wait(lambda:not editor.art_jobs);paint=editor.selected;assert editor.selected_row()['type']=='Paint';wait(lambda:editor.selected_row()['asset'] in editor.images)
        editor.fit_action();canvas.set_tool('Pencil');row=editor.selected_row();a=canvas.screen_point(row,(.4,.4)).toPoint();b=canvas.screen_point(row,(.6,.6)).toPoint();QTest.mousePress(canvas,Qt.LeftButton,pos=a);QTest.mouseMove(canvas,b,delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=b);wait(lambda:not editor.art_jobs);paint_asset=editor.selected_row()['asset'];wait(lambda:paint_asset in editor.images);paint_pixels=pixels(editor.images[paint_asset]);assert np.any(paint_pixels[3::4])
        editor.history(False);wait(lambda:editor.selected_row()['asset'] in editor.images);assert not np.any(pixels(editor.images[editor.selected_row()['asset']])[3::4]);editor.history(True);wait(lambda:editor.selected_row()['asset'] in editor.images)
        canvas.set_tool('Sampler');canvas.paint_press(editor.selected_row(),canvas.screen_point(editor.selected_row(),(.5,.5)));assert editor.brush_color.alpha()>0
        for tool in ('Smudge','Eraser'):
            canvas.set_tool(tool);old=editor.selected_row()['asset'];a=canvas.screen_point(editor.selected_row(),(.5,.5));b=canvas.screen_point(editor.selected_row(),(.55,.5));canvas.paint_press(editor.selected_row(),a);canvas.paint_move(b);canvas.paint_finish();wait(lambda:not editor.art_jobs);assert editor.selected_row()['asset']!=old
        checks.append('QTest crop drag/cancel/commit/Undo; shape/curve storage; native extracted child; real pencil/sampler/smudge/eraser; one Undo per stroke')
        canvas.set_tool('Select');before=deepcopy(editor.config);editor.resize_canvas((1080,1920),False);assert editor.config['canvas']==[1080,1920];editor.history(False);assert editor.config==before;editor.resize_canvas((1000,1000),True);assert editor.config['canvas']==[1000,1000]
        session=out/'art.json';shell.client.request('save',path=str(session));saved=json.loads(session.read_text());assert saved['media']['canvas']==[1000,1000];assert all(Path(a['path']).is_file() for a in saved['media']['assets']);assert any(a.get('managed') and '.assets' in a['path'] for a in saved['media']['assets']);shell.client.request('load',path=str(session));editor.refresh(True);wait(lambda:not shell.client.snapshot['media_library']['pending']);assert paint in lookup(editor.config);assert not shell.client.snapshot['audio_hub']['playing'];assert all(id(shell.panels[k].dockAreaWidget())==v for k,v in areas.items())
        checks.append('Canvas dimension authority with proportional/pixel placement; portable Save/reopen dependencies; unchanged dock areas, no audio/visual autoplay')
        editor.refresh(True);before=deepcopy(editor.config)
        (out/'before-remove.json').write_text(json.dumps(before,indent=2));shell.client.request('media_action',op='remove',asset=image['id'],choice='recover',selection=parent);editor.refresh(True);(out/'after-remove.json').write_text(json.dumps(editor.config,indent=2));assert editor.config==before;editor.history(False);assert any(a['id']==image['id'] for a in shell.client.snapshot['media_library']['assets']);editor.refresh(True)
        (out/'pre-drop-editor.json').write_text(json.dumps(dict(binding=editor.binding,drag=repr(canvas.drag),numeric=repr(editor.numeric_before),slider=repr(editor.slider_before),config=editor.config,snapshot=shell.client.snapshot),indent=2))
        editor.drop_files([str(ROOT/'images n vids/Bobs Mock up.jpg'),str(ROOT/'images n vids/Xeraphina_video.mp4'),str(out/'missing.png')],None,'layer');wait(lambda:not editor.drops);assert any(r['type']=='Video' for r in editor.config['layers']);assert not any(s['playing'] for s in shell.client.snapshot['media_frames'].values())
        ledger=shell.client.snapshot['media_library']['import_results'];assert any(r['status']=='Failed' and r['path'].endswith('missing.png') and 'missing' in r['error'].lower() for r in ledger)
        editor.select(parent);editor.drop_files([video['path']],parent,'child');wait(lambda:not editor.drops);assert any(r['parent']==parent and r['type']=='Video' for r in editor.config['layers'])
        mime=QMimeData();mime.setUrls([QUrl.fromLocalFile(other['path']),QUrl.fromLocalFile(str(out/'another-missing.png'))]);viewport=shell.media_library.tree.viewport();enter=QDragEnterEvent(QPoint(10,10),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(viewport,enter);assert enter.isAccepted();drop=QDropEvent(QPointF(10,10),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier);QApplication.sendEvent(viewport,drop);assert drop.isAccepted();wait(lambda:not shell.client.snapshot['media_library']['pending']);assert any(r['path'].endswith('another-missing.png') and r['status']=='Failed' for r in shell.client.snapshot['media_library']['import_results'])
        checks.append('Recoverable in-use remove/Undo preserved artwork; per-file mixed/duplicate/invalid drop and video child remain stopped')
        with patch.object(editor,'working_options',return_value=((896,504),True)):editor.add_asset(image,True,offer=True)
        wait(lambda:not editor.art_jobs);derivative=editor.selected_row()['asset'];wait(lambda:derivative in editor.images);assert editor.images[derivative].size().width()==896 and editor.images[derivative].height()==504;assert editor.config['canvas']==[1792,1008];record=next(a for a in shell.client.snapshot['media_library']['assets'] if a['id']==derivative);assert record['managed'] and 'Resized derivative' in record['provenance'] and Path(image['path']).is_file()
        checks.append('Asynchronous explicit derivative preserves original, native source canvas option and provenance')
        shell.grab().save(str(out/'studio.png'));(out/'RESULT.json').write_text(json.dumps(dict(checks=checks,evidence='Real Qt and owner with QTest synthetic events, no physical mouse/audio/world acceptance'),indent=2));print('PASS',out,checks,flush=True)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc()+'\n'+(editor.status.text() if 'editor' in locals() else ''),encoding='utf8');(out/'failure-state.json').write_text(json.dumps(shell.client.snapshot if shell.client else {},indent=2));raise
    finally:
        shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True)
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
        pump(.2)

if __name__=='__main__':run()
