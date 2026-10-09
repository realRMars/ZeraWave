"""Owned Qt controls/lifecycle smoke. Synthetic images; no capture or audio output."""
from pathlib import Path
from copy import deepcopy
import json,os,sys,time,shutil,traceback,faulthandler,hashlib
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog,QMenu
from PySide6.QtCore import Qt,QTimer
import PySide6QtAds as ads

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]

def composition_run():
    """Current dynamic workflow, including migrated Increment 1 safety checks."""
    from studio_qt import Shell
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPoint,QPointF,Qt
    from composition import lookup
    fixtures=ROOT/'work/media-composition-20261007';task=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(fixtures)));task.mkdir(parents=True,exist_ok=True);out=task/('qt-'+str(time.time_ns()));out.mkdir()
    import hashlib
    source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app/visuals','app/audio') for p in (ROOT/folder).glob('*.py')}
    (out/'source-identity.json').write_text(json.dumps(source,indent=2))
    os.environ['ZERAWAVE_MEDIA_LIBRARY']=str(out/'library.json');app=QApplication([]);shell=Shell(out/'layout.json',out/'control.log');shell.show();checks=[]
    def pump(seconds=.1):
        end=time.perf_counter()+seconds
        while time.perf_counter()<end:app.processEvents();time.sleep(.005)
    def wait(fn,timeout=12):
        deadline=time.perf_counter()+timeout
        while time.perf_counter()<deadline:
            pump(.03)
            if fn():return
        raise AssertionError(str(shell.client.snapshot if shell.client else 'No owner'))
    try:
        wait(lambda:shell.client is not None and hasattr(shell,'image_editor'));pump(.35);wait(lambda:not shell.client.snapshot['media_library']['loading'])
        assert shell.image_editor.config['layers']==[];assert shell.panels['image_layers'].windowTitle()=='Layers';areas={key:id(d.dockAreaWidget()) for key,d in shell.panels.items()}
        shell.client.request('media_import',paths=[str(ROOT/'images n vids/Xeraphina.jpg'),str(ROOT/'images n vids/Xeraphina_video.mp4'),str(fixtures/'timing-fixture.gif'),str(ROOT/'test_audio/Balloon.mp3')])
        wait(lambda:len(shell.client.snapshot['media_library']['assets'])==4 and not shell.client.snapshot['media_library']['pending']);shell.media_library.refresh()
        asset=next(a for a in shell.media_library.assets.values() if a['kind']=='Images');library=shell.media_library;library.selected=asset['id'];library.populate();shell.panels['media'].toggleView(True);shell.panels['media'].setAsCurrentTab();pump()
        shell.image_editor.working_options=lambda asset:(None,False)
        item=library.tree.currentItem();QTest.mouseClick(library.tree.viewport(),Qt.LeftButton,pos=library.tree.visualItemRect(item).center());QTest.mouseDClick(library.tree.viewport(),Qt.LeftButton,pos=library.tree.visualItemRect(item).center());QTest.mouseRelease(library.tree.viewport(),Qt.LeftButton,pos=library.tree.visualItemRect(item).center());pump();shell.image_editor.refresh(True)
        editor=shell.image_editor;assert len(editor.config['layers'])==1;identity=editor.selected;library.activate(library.tree.currentItem());assert len(editor.config['layers'])==1
        assert not shell.client.snapshot['running'];assert not shell.client.snapshot['audio_hub']['playing'];checks.append('Double-click and repeated activation: one stable image layer, no visual/audio autoplay')
        shell.panels['composition'].toggleView(True);shell.panels['composition'].setAsCurrentTab();wait(lambda:asset['id'] in editor.images);pump()
        canvas=editor.canvas;pos=canvas.view().map(QPointF(editor.canvas_size[0]*.5,editor.canvas_size[1]*.5)).toPoint();before=editor.config['layers'][0]['transform'].copy();undo_before=len(shell.client.snapshot['media_control'].get('history',{}))
        QTest.mousePress(canvas,Qt.LeftButton,pos=pos);QTest.mouseMove(canvas,pos+QPoint(36,18),delay=30);pump(.06);QTest.mouseRelease(canvas,Qt.LeftButton,pos=pos+QPoint(36,18));pump();assert editor.selected==identity and editor.selected_row()['transform']!=before,dict(selected=editor.selected,identity=identity,visible=canvas.isVisible(),size=[canvas.width(),canvas.height()],pos=[pos.x(),pos.y()],status=editor.status.text(),history=shell.client.snapshot['media_control'])
        assert shell.client.snapshot['media_control']['history']['undo']=='Canvas move';editor.history(False);assert editor.selected_row()['transform']==before;editor.history(True)
        checks.append('Qt mouse drag changes output transform; one named Undo/Redo command and stable selection')
        committed=deepcopy(editor.config);QTest.mousePress(canvas,Qt.LeftButton,pos=pos);QTest.mouseMove(canvas,pos+QPoint(20,10),delay=15);canvas.hide();QTest.mouseRelease(canvas,Qt.LeftButton,pos=pos+QPoint(20,10));assert canvas.drag is None and editor.config==committed;canvas.show()
        checks.append('Interrupted canvas drag restores committed state on hide; no unfinished gesture survives tab switch')
        editor.canvas.set_tool('Mask');editor.canvas.points=[[.1,.1],[.9,.1],[.9,.9],[.1,.9]];prior=len(editor.selected_row()['masks']);editor.canvas.discard();assert len(editor.selected_row()['masks'])==prior
        editor.canvas.points=[[.1,.1],[.9,.1],[.9,.9],[.1,.9]];editor.canvas.apply();assert len(editor.selected_row()['masks'])==prior+1;editor.history(False);assert len(editor.selected_row()['masks'])==prior
        editor.history(True);editor.edit_mask();assert editor.canvas.tool=='Mask' and editor.canvas.points;editor.canvas.discard();editor.history(False)
        editor.canvas.set_tool('Select');editor.duplicate();assert len(editor.config['layers'])==2 and editor.selected!=identity;editor.group();assert editor.selected_row()['type']=='Group';editor.ungroup();assert len(editor.config['layers'])==2
        checks.append('Mask cancel/apply and bounded history; independent duplicate; group/ungroup')
        collection=shell.client.request('media_action',op='collection',command='create',name='Live set')['media_library']['collections'];cid=next(iter(collection));shell.client.request('media_action',op='collection',command='add',collection=cid,asset=asset['id']);assert shell.client.snapshot['media_library']['collections'][cid]['assets']==[asset['id']]
        audio=next(a for a in shell.media_library.assets.values() if a['kind']=='Audio');shell.client.request('media_action',op='audio',asset=audio['id']);wait(lambda:shell.client.snapshot['audio_hub']['path']==audio['path']);assert not shell.client.snapshot['audio_hub']['playing'];shell.client.request('media_action',op='audio',asset=audio['id']);assert not shell.client.snapshot['audio_hub']['playing']
        video=next(a for a in shell.media_library.assets.values() if a['kind']=='Video');editor.add_asset(video);assert not shell.client.snapshot['media_frames'][editor.selected]['playing'];video_id=editor.selected;editor.transport('play');wait(lambda:shell.client.snapshot['media_frames'][video_id]['playing']);pump(.35);editor.transport('pause');assert not shell.client.snapshot['media_frames'][video_id]['playing']
        checks.append('Collections; existing AudioOwner selection stays stopped; real video layer transport independent of visuals')
        frozen=deepcopy(shell.client.snapshot['values']['media']);frames=deepcopy(shell.client.snapshot['media_frames'])
        for wrong in ({'media_session':'obsolete'},{'media_revision':99999},{'preview_run':'obsolete'},{'destination_revision':99999}):
            args=editor.binding_args();args.update(wrong)
            try:shell.client.request('composition',version=2,presentation=frozen['presentation'],layers=frozen['layers'],label='Stale edit',**args)
            except ValueError:pass
            else:raise AssertionError('Stale edit accepted: '+str(wrong))
            assert shell.client.snapshot['values']['media']==frozen and shell.client.snapshot['media_frames']==frames
        try:shell.client.request('start',scope='experimental',path=['cymatics','water'])
        except ValueError as exc:assert 'unsupported' in str(exc),str(exc)
        else:raise AssertionError('Legacy composition route started')
        assert not shell.client.snapshot['running']
        # Real pipe round-trip beyond the former 64 KiB reader boundary.
        shell.client.request('diagnostics',value=False,padding='x'*70000)
        assert not shell.client.disconnected and shell.client.snapshot['values']['media']==frozen
        before_audio=shell.client.snapshot['audio_hub']['path'];shell.client.request('media_action',op='remove',asset=audio['id']);assert shell.client.snapshot['audio_hub']['path']==before_audio
        editor.history(False);assert any(a['id']==audio['id'] for a in shell.client.snapshot['media_library']['assets'])
        saved_layers=deepcopy(editor.config['layers']);shell.client.request('media_action',op='remove',asset=asset['id']);editor.refresh(True)
        assert editor.config['layers']==saved_layers and Path(asset['path']).is_file()
        editor.history(False);assert asset['id'] in shell.client.snapshot['media_library']['collections'][cid]['assets']
        assert editor.config['layers']==saved_layers
        checks.append('Session/revision/run/destination stale edits rejected without changing frames; legacy route rejected; reference Remove/Undo preserves masks/transforms/membership, originals and independently active audio')

        assert all(id(shell.panels[k].dockAreaWidget())==v for k,v in areas.items())
        session=out/'session.json';shell.client.request('save',path=str(session),save_id='media-save');wait(lambda:any(s['id']=='media-save' and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves']));saved=json.loads(session.read_text());assert saved['version']==5
        shell.client.request('load',path=str(session));editor.refresh(True);assert editor.config['layers'] and not any(s['playing'] for s in shell.client.snapshot['media_frames'].values());checks.append('Artistic v5 round trip; layout areas unchanged; reopening animations stopped')
        shell.panels['composition'].toggleView(True);shell.panels['composition'].setAsCurrentTab();pump();shell.grab().save(str(out/'composition.png'))
        (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,evidence='Real Qt widgets and QTest mouse events; real decoded video without audio output; not hardware mouse/listening/scanout'),indent=2));(task/'qt-latest.txt').write_text(str(out));print('PASS',out,json.dumps(checks),flush=True)
        if '--renderer' in sys.argv:
            shell.client.request('select',scope='main',path=['organic','roots']);shell.browsed=('main',['organic','roots'])
            shell.client.request('resolution',policy=dict(mode='fixed',size=[1280,720],choice='1280×720'),preview_run=None);shell.start()
            wait(lambda:shell.client.snapshot.get('preview',{}).get('ready'),180);pump(1.)
            assert shell.client.snapshot['preview']['dimensions']['internal']==[1280,720]
            shell.image_editor.refresh(True);shell.panels['preview'].setAsCurrentTab();pump();shell.grab().save(str(out/'normal-main-composition.png'))
            (out/'normal-main-state.json').write_text(json.dumps(shell.client.snapshot,indent=2));print('RENDERER READY',out,flush=True)
        if '--interactive' in sys.argv:
            timer=QTimer(shell)
            def checkpoint():
                (out/'live-state.json').write_text(json.dumps(shell.client.snapshot,indent=2))
                if (out/'close-request').exists():shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True);shell.close()
            timer.timeout.connect(checkpoint);timer.start(500);print('INTERACTIVE',out,flush=True);app.exec()
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());
        if shell.client:(out/'failure-state.json').write_text(json.dumps(shell.client.snapshot,indent=2))
        raise
    finally:
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
        app.processEvents()

if __name__=='__main__':composition_run()
