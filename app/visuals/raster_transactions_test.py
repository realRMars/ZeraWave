"""B1 owner/Qt/GPU acceptance with delayed persistence, no native-input claim."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,os,sys,time,threading,uuid,traceback
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtGui import QImage,QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from composition import defaults,new_layer,lookup
from raster_resources import Resources,Outcomes,snapshot,read,release

def contracts(out):
    # The existing pipe preserves completed images beside replaceable previews,
    # color updates and backpressure; no renderer or audio replacement is used.
    from studio_color_link import ColorInbox,ColorLink
    from color_controls import TARGETS,validate_colors
    from unittest.mock import patch
    with patch.dict(os.environ,{'ZERAWAVE_PREVIEW_RUN':'b1-pipe'}):
        fd,writer=os.pipe();inbox=ColorInbox(fd)
    try:
        def packet(serial,ordered=True):return dict(kind='preview-control',run='b1-pipe',op='images',serial=serial,revision=serial,ordered=ordered)
        target=TARGETS[0];colors={target.id:{target.slots[0].id:{'color':'#1268ab'}}}
        for serial in range(1,4):inbox.accept(json.dumps(packet(serial)).encode())
        for serial in range(4,7):inbox.accept(json.dumps(packet(serial,False)).encode())
        inbox.accept(json.dumps(dict(kind='colors',revision=1,targets=colors)).encode())
        assert [p['serial'] for p in inbox.take_controls()]==[1,2,3,6]
        assert inbox.pending==(1,validate_colors(colors))
        link=ColorLink.__new__(ColorLink);link.condition=threading.Condition();link.closed=False;link.preview_run='b1-pipe';link.preview_serial=0;link.pending_controls={}
        for revision in range(64):assert link.submit_control('images',revision=revision,ordered=True)
        try:link.submit_control('images',revision=64,ordered=True);raise AssertionError('Publication overflow accepted')
        except ValueError:pass
        assert len(link.pending_controls)==64
    finally:
        inbox.closed=True;os.close(writer);inbox.thread.join(2);os.close(fd)
    image=QImage(64,48,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(90,160,210,170))
    desc,producer=snapshot(image);identity=uuid.uuid4().hex
    asset=dict(id=identity,path=str(out/'nomination.png'),kind='Images',name='Immutable fixture',managed=True,internal=True,provenance='Editable drawing stroke',runtime=desc)
    resources=Resources(out/'unit-artwork');barrier=threading.Event();resources.barrier=barrier
    try:
        resources.admit([asset]);resources.persist(identity);before=read(desc)[1];image.fill(QColor('red'));assert read(desc)[1]==before
        release(producer);producer=None;assert read(desc)[1]==before # authority lease owns it now
        row=new_layer(asset=identity);scene=dict(defaults(),assets=[{k:v for k,v in resources.rows[identity].items() if k in ('id','path','name','kind','managed','internal','provenance')}],layers=[row])
        values=dict(media=scene);resources.save('save-1',values,[{'qt':'pinned'}],out/'unit-save.json','unit-session',3)
        row['name']='later mutation';assert resources.saves['save-1']['values']['media']['layers'][0]['name']!='later mutation'
        assert not (out/'unit-save.json').exists() and resources.state()['pending']==1
        barrier.set()
        end=time.monotonic()+10
        while resources.saves['save-1']['status']=='pending' and time.monotonic()<end:resources.poll();time.sleep(.01)
        assert resources.saves['save-1']['status']=='durable',resources.state()
        saved=json.loads((out/'unit-save.json').read_text());assert saved['qt_tuning_drafts']==[{'qt':'pinned'}] and saved['b1_saved_revision']['revision']==3
        assert Path(saved['media']['assets'][0]['path']).is_file()
        from unittest.mock import patch
        prior=(out/'unit-save.json').read_bytes()
        with patch('artwork.portable_scene',side_effect=OSError('Injected dependency copy failure')):
            resources.save('failed-copy',values,[],out/'unit-save.json','unit-session',4)
            end=time.monotonic()+5
            while resources.saves['failed-copy']['status']=='pending' and time.monotonic()<end:resources.poll();time.sleep(.01)
            assert resources.saves['failed-copy']['status']=='failed' and (out/'unit-save.json').read_bytes()==prior
        retry=resources.retry_save('failed-copy',out/'retry-save.json')
        end=time.monotonic()+5
        while retry['status']=='pending' and time.monotonic()<end:resources.poll();time.sleep(.01)
        assert retry['status']=='durable' and Path(retry['path']).is_file()
        with patch.object(resources.save_pool,'submit',side_effect=MemoryError('Injected save executor allocation failure')):
            failed=resources.save('failed-allocation',values,[],out/'allocation-save.json','unit-session',5)
        assert failed['status']=='failed' and 'failed-allocation' in resources.save_pins
        retry=resources.retry_save('failed-allocation')
        end=time.monotonic()+5
        while retry['status']=='pending' and time.monotonic()<end:resources.poll();time.sleep(.01)
        assert retry['status']=='durable' and resources.saves['failed-allocation']['status']=='retried'
        resources.retain([]);assert not resources.rows
        ledger=Outcomes();data=dict(operation_id=uuid.uuid4().hex,operation_stream=uuid.uuid4().hex,operation_sequence=1)
        assert ledger.begin('composition',data);ledger.finish(data,status='applied');assert not ledger.begin('composition',data)
        try:ledger.begin('composition',dict(data,operation_sequence=2));raise AssertionError('changed duplicate accepted')
        except ValueError:pass
        try:ledger.begin('composition',dict(data,operation_id=uuid.uuid4().hex,operation_sequence=3));raise AssertionError('out of order accepted')
        except ValueError:pass
        from unittest.mock import patch
        desc,p=snapshot(image);asset.update(id=uuid.uuid4().hex,runtime=desc)
        try:
            with patch('raster_resources.MAX_BYTES',1):
                try:resources.admit([asset]);raise AssertionError('Exhaustion accepted')
                except ValueError:pass
            assert not resources.rows
            with patch('raster_resources.SharedMemory',side_effect=MemoryError('Injected allocation failure')):
                try:resources.admit([asset]);raise AssertionError('Allocation failure accepted')
                except MemoryError:pass
            assert not resources.rows and not resources.leases
            with patch('raster_resources.MAX_JOBS',0):
                try:resources.admit([asset]);raise AssertionError('Queue exhaustion accepted')
                except ValueError:pass
            assert not resources.rows and not resources.leases
        finally:release(p)
    finally:
        barrier.set();resources.close()
        if producer:release(producer)
    return ['Immutable producer detachment and owner/reader leases; pinned Save with Qt metadata; failed dependency copy retains previous session and retry succeeds; duplicate/change/out-of-order rejection; byte/allocation/queue pressure atomic admission']

def run():
    # Qt must own application/plugin initialization before the contracts start
    # background QImage encoders. A late QApplication faults on native Windows.
    app=QApplication([])
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=contracts(out)
    hold=out/'persistence.hold';hold.touch();fail=out/'fail-write';drop=out/'drop-ack'
    os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_RASTER_TEST_BARRIER=str(hold),ZERAWAVE_RASTER_TEST_FAIL_WRITE=str(fail),ZERAWAVE_RASTER_TEST_DROP_ACK=str(drop))
    source=ROOT/'images n vids/Xeraphina.jpg';assert hashlib.sha256(source.read_bytes()).hexdigest()=='256e6ced41f77999576cf42dc574d262c45791e875484f736607cd5ecfe57c1f'
    from studio_qt import Shell
    shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=None;timings=[];gpu=None;ctx=None
    def pump(duration=.02):
        end=time.monotonic()+duration
        while time.monotonic()<end:app.processEvents();time.sleep(.001)
    def wait(fn,timeout=25):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            pump()
            if fn():return
        raise AssertionError('Timeout: '+(e.status.text() if e else 'owner startup'))
    def idle():wait(lambda:not e.edit_jobs and not e.art_jobs)
    def stroke(tool,offset=0,settle=True):
        e.choose_tool(tool);c=e.canvas;row=e.selected_row();a=c.screen_point(row,(.35+offset,.43)).toPoint();b=c.screen_point(row,(.65+offset,.57)).toPoint()
        start=time.perf_counter();QTest.mousePress(c,Qt.LeftButton,pos=a);assert c.stroke,e.status.text();QTest.mouseMove(c,b,delay=0);QTest.mouseRelease(c,Qt.LeftButton,pos=b)
        submitted=time.perf_counter();op=e.edit_jobs[-1][0].operation_id
        if settle:idle()
        timings.append(dict(tool=tool,input_and_snapshot_ms=(submitted-start)*1000,return_to_observed_acceptance_ms=(time.perf_counter()-submitted)*1000,operation_id=op))
        return op
    def gpu_pixels():
        nonlocal gpu,ctx
        from image_layers import ImageLayers
        import moderngl
        if gpu is None:
            ctx=moderngl.create_standalone_context(require=330);target=ctx.simple_framebuffer((1792,1008),components=4)
            class Proxy:
                screen=target
                def __getattr__(self,k):return getattr(ctx,k)
            vertices=ctx.buffer(np.asarray([[-1,-1],[1,-1],[-1,1],[1,1]],'f4').tobytes());gpu=ImageLayers(Proxy(),vertices)
        records={a['id']:a for a in e.media_assets()};scene=deepcopy(shell.client.snapshot['values']['media']);scene['assets']=[records[a['id']] for a in scene['assets']];scene['presentation']='Layers only'
        # Qt's GPU canvas changes the current context while pump() processes
        # paint events. Bind this independent test context around each GL use.
        begun=time.perf_counter()
        with ctx:gpu.request(scene,shell.client.snapshot['media_control']['revision'],shell.client.snapshot['media_control']['session'])
        def published():
            with ctx:gpu.poll()
            return not gpu.pending
        wait(published);assert not gpu.error,gpu.snapshot()
        with ctx:
            target=gpu.ctx.screen;target.use();target.clear(0,0,0,0);ctx.viewport=(0,0,1792,1008);gpu.draw((1792,1008));data=target.read(components=4,alignment=1)
        timings.append(dict(gpu_publication_readback_ms=(time.perf_counter()-begun)*1000))
        return hashlib.sha256(data).hexdigest()
    try:
        wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;c=e.canvas
        from unittest.mock import patch
        sequence=shell.client.edit_sequence
        with patch.object(shell.client.edits,'submit',side_effect=MemoryError('Injected executor allocation failure')):
            try:shell.client.submit('composition');raise AssertionError('Allocation failure ignored')
            except MemoryError:pass
        assert shell.client.edit_sequence==sequence and shell.client.edit_count==0
        with patch.object(shell.client,'edit_count',16):
            try:shell.client.submit('composition');raise AssertionError('Full client queue accepted')
            except ValueError:pass
        assert shell.client.edit_sequence==sequence
        shell.panels['composition'].toggleView(True);shell.panels['image_layers'].toggleView(True);pump()
        shell.client.request('media_import',paths=[str(source)]);wait(lambda:not shell.client.snapshot['media_library']['pending'] and shell.client.snapshot['media_library']['assets'])
        asset=shell.client.snapshot['media_library']['assets'][0];assert e.add_asset(asset);e.resize_canvas((1792,1008),False);wait(lambda:asset['id'] in e.images);parent=e.selected;initial=e.selected_row()['asset']
        from raster_resources import snapshot as allocate
        before_allocation=deepcopy(shell.client.snapshot['media_control']['history'])
        calls=[]
        def fail_second(image):
            calls.append(1)
            if len(calls)==2:raise MemoryError('Injected edited snapshot allocation failure')
            return allocate(image)
        with patch('raster_resources.snapshot',side_effect=fail_second):
            c.paint_press(e.selected_row(),c.screen_point(e.selected_row(),(.4,.4)));assert c.stroke;c.paint_finish()
        assert e.selected_row()['asset']==initial and not e.edit_jobs and not e.runtime_producers and not e.unsubmitted_sources
        assert shell.client.snapshot['media_control']['history']==before_allocation
        first=stroke('Pencil');accepted=e.selected_row()['asset'];state=shell.client.snapshot['media_control'];assert state['history']['drawing'][parent]['undo_count']==1 and state['raster']['pending']==1
        runtime=next(a for a in e.media_assets() if a['id']==accepted);assert not Path(runtime['path']).exists();paint_gpu=gpu_pixels();assert gpu.applied==state['revision']
        assert c.source_image(e.selected_row()) is not None
        # A busy decoder/preparation pool cannot gate recovery-source loading.
        decoder_release=threading.Event();decoder_busy=e.pool.submit(decoder_release.wait)
        e.images.pop(initial,None)
        try:
            e.history(False,'drawing');idle();assert e.selected_row()['asset']==initial and c.source_image(e.selected_row()) is not None
            wait(lambda:'source pixels unavailable' not in getattr(e,'target_diagnostic',''))
        finally:decoder_release.set();decoder_busy.result(5)
        undo_gpu=gpu_pixels();assert undo_gpu!=paint_gpu
        e.history(True,'drawing');idle();assert e.selected_row()['asset']==accepted and gpu_pixels()==paint_gpu
        newer=stroke('Brush',.05);new_asset=e.selected_row()['asset'];new_gpu=gpu_pixels();assert new_gpu!=paint_gpu
        save_revision=shell.client.snapshot['media_control']['revision'];shell.client.request('save',path=str(out/'pending-save.json'),save_id='pending-save')
        stroke('Eraser',-.05);erased=e.selected_row()['asset'];assert erased!=new_asset
        stroke('Smudge',.02);assert e.selected_row()['asset']!=erased
        count=shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count']
        for offset in (0,.015,.03):stroke('Pencil',offset,False)
        idle();assert shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count']==count+3
        final=e.selected_row()['asset'];final_gpu=gpu_pixels();hold.unlink();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0)
        wait(lambda:any(s['id']=='pending-save' and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves']))
        assert e.selected_row()['asset']==final and gpu_pixels()==final_gpu
        saved=json.loads((out/'pending-save.json').read_text());assert saved['b1_saved_revision']['revision']==save_revision and lookup(saved['media'])[parent]['asset']==new_asset and 'qt_tuning_drafts' in saved
        assert all(Path(a['path']).is_file() for a in saved['media']['assets'] if a.get('managed'))
        checks.append('Native-size scripted Pencil/Brush/Eraser/Smudge; owner history and existing GPU stage before held PNG; immediate Undo/Redo; three rapid ordered strokes; late writes cannot reinstall pixels; pinned pending Save retains older revision and Qt metadata')
        drop.touch();before_count=shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count'];op=stroke('Pencil',.01)
        assert shell.client.snapshot['media_control']['history']['drawing'][parent]['undo_count']==before_count+1
        assert sum(t['id']==op for t in shell.client.snapshot['media_control']['transactions'])==1
        # Capture immutable command metadata at the actual client request boundary.
        request=shell.client.request;sent=[]
        def capture(name,**data):
            if data.get('operation_id'):sent.append((name,deepcopy(data)))
            return request(name,**data)
        shell.client.request=capture
        stroke('Pencil',.005);name,data=sent[-1];history=deepcopy(shell.client.snapshot['media_control']['history']);revision=shell.client.snapshot['media_control']['revision']
        request(name,**data);assert shell.client.snapshot['media_control']['history']==history and shell.client.snapshot['media_control']['revision']==revision
        try:request(name,**dict(data,operation_id=uuid.uuid4().hex,operation_sequence=data['operation_sequence']+2));raise AssertionError('Out-of-order owner delivery accepted')
        except ValueError as exc:assert 'Out-of-order' in str(exc)
        assert shell.client.snapshot['media_control']['history']==history
        shell.client.request=request
        checks.append('One ACK dropped after owner applies; snapshot reconciliation, actual duplicate and out-of-order owner delivery yield exactly one history entry')
        wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0)
        fail.touch();stroke('Brush',.025);wait(lambda:bool(shell.client.snapshot['media_control']['raster']['failures']))
        failed_asset=e.selected_row()['asset'];before_failed=gpu_pixels();shell.client.request('save',path=str(out/'recovered.json'),save_id='recover-save')
        wait(lambda:any(s['id']=='recover-save' and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves']))
        recovered=json.loads((out/'recovered.json').read_text());assert lookup(recovered['media'])[parent]['asset']==failed_asset and e.selected_row()['asset']==failed_asset and gpu_pixels()==before_failed
        assert not shell.client.snapshot['media_control']['raster']['failures'];fail.unlink()
        checks.append('Injected PNG failure preserves accepted pixels/history and GPU result; Save As secures compatible portable revision without installing old pixels')
        row=deepcopy(e.selected_row());e.edit('locked',True,'Lock',allow_locked=True);before_count=shell.client.snapshot['media_control']['history']['commands'];c.paint_press(e.selected_row(),c.screen_point(e.selected_row(),(.5,.5)));assert c.stroke is None and shell.client.snapshot['media_control']['history']['commands']==before_count
        e.edit('locked',False,'Unlock',allow_locked=True)
        # Admission rejects wrong/deleted/obsolete/locked targets before history.
        from raster_resources import snapshot,release
        desc,producer=snapshot(c.source_image(e.selected_row()));record=dict(runtime,id=uuid.uuid4().hex,runtime=desc)
        protected=deepcopy(shell.client.snapshot['media_control']['history'])
        def rejected(**changes):
            state=shell.client.snapshot['media_control'];data=dict(value=deepcopy(e.config),label='Rejected fixture',media_session=state['session'],media_revision=state['revision'],history_scope='drawing',history_target=parent,raster_target=deepcopy(e.selected_row()),raster_assets=[dict(record,id=uuid.uuid4().hex)])
            data.update(changes);job=shell.client.submit('composition',**data)
            try:job.result(5);raise AssertionError('Invalid operation accepted')
            except ValueError:pass
            assert shell.client.snapshot['media_control']['history']==protected and e.selected_row()['asset']==failed_asset
        try:
            wrong=dict(e.selected_row(),name='Wrong target version');rejected(raster_target=wrong)
            deleted=dict(e.selected_row(),id=uuid.uuid4().hex);rejected(raster_target=deleted)
            rejected(media_session='obsolete-session');rejected(media_revision=-1)
        finally:release(producer)
        # Held accepted work survives replacement, close refusal and session load.
        hold.touch();stroke('Pencil',.01);retained=e.selected_row()['asset'];old_session=shell.client.snapshot['media_control']['session']
        assert shell.client.snapshot['media_control']['raster']['pending']
        try:shell.client.request('close');raise AssertionError('Pending accepted work released on close')
        except ValueError as exc:assert 'not secured' in str(exc)
        replacement=out/'replacement.png';pixels=QImage(1792,1008,QImage.Format_ARGB32_Premultiplied);pixels.fill(QColor('#1569ab'));assert pixels.save(str(replacement))
        e.drop_files([str(replacement)],parent,'replace');wait(lambda:not e.drops and not e.edit_jobs);replacement_id=e.selected_row()['asset'];assert replacement_id!=retained
        e.history(False,'layers');idle();assert e.selected_row()['asset']==retained and c.source_image(e.selected_row()) is not None
        e.history(True,'layers');idle();assert e.selected_row()['asset']==replacement_id
        from PySide6.QtWidgets import QMessageBox
        from unittest.mock import patch
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes):e.delete()
        idle();assert parent not in lookup(e.config)
        e.history(False,'layers');idle();assert lookup(e.config)[parent]['asset']==replacement_id
        shell.client.request('load',path=str(out/'pending-save.json'));e.refresh(True);e.select(parent);wait(lambda:c.source_image(e.selected_row()) is not None if e.selected_row() else False)
        assert shell.client.snapshot['media_control']['session']!=old_session
        assert shell.client.snapshot['media_control']['raster']['resources']
        hold.unlink();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0 and not any(s['status']=='pending' for s in shell.client.snapshot['media_control']['raster']['saves']))
        assert lookup(e.config)[parent]['asset']==new_asset
        assert next(a['path'] for a in e.config['assets'] if a['id']==new_asset)==next(a['path'] for a in saved['media']['assets'] if a['id']==new_asset)
        wait(lambda:not shell.client.snapshot['media_control']['raster']['resources'])
        # Reopening a recovery export must use its durable portable dependency,
        # including when a prior working PNG failed under this same asset ID.
        shell.client.request('load',path=str(out/'recovered.json'));e.refresh(True);e.select(parent);wait(lambda:c.source_image(e.selected_row()) is not None)
        assert e.selected_row()['asset']==failed_asset
        assert next(a['path'] for a in e.config['assets'] if a['id']==failed_asset)==next(a['path'] for a in recovered['media']['assets'] if a['id']==failed_asset)
        assert any(s['session']==old_session and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves'])
        c.paint_press(e.selected_row(),c.screen_point(e.selected_row(),(.4,.4)));assert c.stroke
        before_switch=deepcopy(shell.client.snapshot['media_control']['history']);e.select(None);assert not c.stroke
        c.paint_finish();assert shell.client.snapshot['media_control']['history']==before_switch;e.select(parent)
        checks.append('Wrong/deleted/obsolete target rejection leaves history; ordinary lock; pending source replacement management recovery; close refusal; session switch pins recovery checkpoint and late callbacks cannot cross context')
        c.grab().save(str(out/'canvas.png'))
        expected=('Out-of-order or expired operation','Raster target changed; edit rejected.','Obsolete raster session/revision','Accepted raster work is not secured')
        assert all(any(message in error for message in expected) for error in shell.errors),list(shell.errors)
        result=dict(checks=checks,expected_rejection_diagnostics=list(shell.errors),timing=timings,gpu=ctx.info.get('GL_RENDERER'),canvas=[1792,1008],viewport=[c.width(),c.height()],dpr=c.devicePixelRatioF(),zoom=c.zoom,limits='Qt-scripted gestures and standalone existing GPU ImageLayers; no native pointer or live visualizer acceptance')
        (out/'RESULT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    except BaseException:
        (out/'FAILURE.txt').write_text(traceback.format_exc());raise
    finally:
        if hold.exists():hold.unlink()
        if gpu:
            with ctx:gpu.close()
            ctx.release()
        if shell.client:shell.client.close(force=True)
        shell.closing=True
        if e:e.close_resources()
        shell.close();pump(.03)
if __name__=='__main__':run()
