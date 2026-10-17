"""Real offscreen Qt Source/review/API/CLI/marks and1280x720 layout.

Actual disposable owner and CPU previews; synthetic Qt input, controlled Future/
publication races explicitly labelled. No physical desktop/GPU/device/export.
"""
from pathlib import Path
from copy import deepcopy
from concurrent.futures import Future
from unittest.mock import patch
import os,sys,json,time,traceback,subprocess,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);destination=Path(sys.argv[3]);assert not destination.exists()
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox,QPushButton,QWidget
from PySide6.QtCore import Qt,QRect
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_api import call
from project_review import marks
from video_project import new_id
source_files=['studio_project_review_test.py','studio_project_review.py','studio_project_source.py','project_review.py','project_service.py','studio_control_service.py','video_project.py','studio_project.py']
source_hashes={name:hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest() for name in source_files};(out/'SOURCE.json').write_text(json.dumps(source_hashes,indent=2),encoding='utf8')
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;checks=[];events=[];layout_rows=[];idle_samples=[]
def wait(fn,seconds=60):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        start=time.perf_counter_ns();app.processEvents();events.append((time.perf_counter_ns()-start)/1e6);time.sleep(.004)
        if fn():return
    raise AssertionError('Qt review timeout: '+w.notice.text()+' | '+r.status.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and shell.client.edit_count==0)
def reveal(control):
    if source.controls_scroll.isAncestorOf(control):
        # Follow keyboard-focus intent first. Qt can otherwise restore the
        # previous focused child after a programmatic scroll on a tall panel.
        control.setFocus(Qt.TabFocusReason);app.processEvents();source.controls_scroll.ensureWidgetVisible(control,0,0);app.processEvents()

def spin(box,value):
    reveal(box)
    box.setFocus();box.lineEdit().selectAll();QTest.keyClicks(box.lineEdit(),str(value));QTest.keyClick(box.lineEdit(),Qt.Key_Return);app.processEvents()
def click(button):
    reveal(button)
    QTest.mouseClick(button,Qt.LeftButton);app.processEvents()
def inspect(mode='source'):
    click(r.buttons['Inspect Source' if mode=='source' else 'Inspect placement']);wait(lambda:r.future is None and r.desired is None and r.report_context==r.context());assert r.report['status']=='ready',r.status.text();return deepcopy(r.report)
def must_refuse(fn):
    try:fn();raise AssertionError('Stale/pending report action admitted')
    except ValueError:pass
def prepare_source(asset):
    w.video_panels.open_source(asset);wait(lambda:source.asset is not None and source.asset['sha256']==asset['sha256'] and source.future is None and source.next_source is None and source.prepared_asset is None and not w.pending);wait(lambda:source.version==(w.state()['source']['epoch'],w.state()['source']['revision']))
try:
    shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1280,720);shell.show();w=shell.project_workspace;source=w.video_panels.source;r=source.review;wait(lambda:w.state().get('endpoint'));endpoint=Path(w.state()['endpoint'])
    fixture=json.loads(proof.read_text(encoding='utf8'))['document'];asset=deepcopy(next(a for a in fixture['media'] if a['kind']=='Video'));asset['location']=dict(kind='external',path=str((proof.parent/asset['location']['path']).resolve()) if asset['location']['kind']=='relative' else asset['location']['path'])
    w.submit('new',name='Source review before placement',settings=dict(width=1920,height=1080,fps=[30,1]));idle();w.show_workspace();prepare_source(asset);click(r.toggle);assert r.scroll.isVisible();spin(source.in_box,4506);idle();spin(source.out_box,4536);idle();wait(lambda:source.range==[4506,4536]);spin(r.before,18);spin(r.after,30);r.purpose.setFocus();QTest.keyClicks(r.purpose,'Source-only purpose before placement');before=deepcopy(w.document());program=deepcopy(w.transport_state());report=inspect();assert report['sequence']['range'] is None and report['source']['effective_grid']==[4488,4566] and not w.document()['clips']
    click(r.buttons['Remember range']);idle();remembered=deepcopy(w.document());assert marks(remembered)['items'][0]['sequence_range'] is None and w.state()['undo_label']=='Remember source review purpose and range';w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==remembered
    click(r.buttons['Validate report']);wait(lambda:r.future is None and r.report_context==r.context());assert r.report['status']=='ready' and r.report['certificate']['origin']['binding']['revision']==report['binding']['revision'];click(r.buttons['Set Source handles']);idle();wait(lambda:source.range==[4488,4566]);assert w.transport_state()['frame']==program['frame'] and w.transport_state()['active']==program['active']
    source.seek_to(4490);idle();assert w.transport_state()['frame']==program['frame'];wait(lambda:source.clock()['frame']==4490)
    monitor=w.video_panels.preview_transport;monitor.set_target('source');click(monitor.loop_action);idle();wait(lambda:source.clock()['loop']);click(monitor.buttons['play']);idle();wait(lambda:source.clock()['playing']);QTest.qWait(120);assert 4488<=source.clock()['frame']<4566 and w.transport_state()['frame']==program['frame'];click(monitor.buttons['play']);idle();wait(lambda:not source.clock()['playing']);assert w.state()['audio_target']=='source' and w.document()==remembered
    w.save(True,str(out/'source-only.zwv'));idle();w.submit('close');idle();w.open(str(out/'source-only.zwv'));idle();assert not w.document()['clips'] and marks(w.document())['items'][0]['sequence_range'] is None
    checks.append('Actual empty-timeline Source In/Out/handles inspection, Qt Remember/named UndoRedo, explicit unchanged validation, Source range/seek independent Program and existing Source Loop/Play/Pause via shared discard-test sink (no device/heard timing), new SaveAs/reopen preserve source-only note without hidden placement/import')
    w.submit('close');idle();w.open(str(proof));idle();w.show_workspace();clip=next(c for c in w.document()['clips'] if c['provenance'].get('component',{}).get('instance_key')=='review-1' and c['provenance']['component']['part']=='background');asset=next(a for a in w.document()['media'] if a['id']==clip['asset']);w.timeline.canvas.select('clips',clip['id']);prepare_source(asset)
    if not r.toggle.isChecked():click(r.toggle)
    spin(source.in_box,4506);idle();spin(source.out_box,4536);idle();source.seek_to(4506);idle();wait(lambda:source.preview is not None and source.preview.valid_presented() and source.preview.presented[-1]==4506);native=source.preview.view.surface.image;assert [native.width(),native.height()]==[asset['metadata']['width'],asset['metadata']['height']];native.save(str(out/'source-audition-4506.png'));assert w.transport_state()['frame']==0
    spin(r.sequence_in,90);spin(r.sequence_out,210);spin(r.before,18);spin(r.after,30);r.purpose.setText('Review to highlight boundary');report=inspect('placement');assert report['duplicate_use']['total']>1 and report['source']['sha256'] not in r.details.toPlainText();assert 'Source frames at 60' in r.units.text() and 'project frames at 30' in r.units.text();assert 'Shared shot' in r.details.toPlainText()
    query=r.query('placement');query['query_id']=new_id();reply=call(endpoint,query);assert reply['ok'] and reply['report']==r.report
    query_file=out/'exact-query.json';query_file.write_text(json.dumps(query),encoding='utf8');p=subprocess.run([sys.executable,'-B','-X','utf8',str(root/'app/visuals/project_cli.py'),'--endpoint',str(endpoint),'--request',str(query_file)],capture_output=True,text=True,encoding='utf8',timeout=30);(out/'CLI.stdout.json').write_text(p.stdout,encoding='utf8');(out/'CLI.stderr.txt').write_text(p.stderr,encoding='utf8');assert p.returncode==0 and json.loads(p.stdout)['report']==reply['report']
    checks.append('Actual Qt selected placement and script API/CLI return the same exact report over ordinary editable proof; readable names/seconds/Source60 vs sequence30 units, exact JSON/full hashes retained')
    assert shell.width()==1280 and shell.height()==720
    (out/'LAYOUT-DIAGNOSTICS.json').write_text(json.dumps(dict(review=[r.width(),r.height()],body=[r.body.width(),r.body.height()],body_min=[r.body.minimumSizeHint().width(),r.body.minimumSize().width()],viewport=[r.scroll.viewport().width(),r.scroll.viewport().height()],rows=[dict(direction=int(row.direction().value),minimum_width=row.minimumSize().width()) for row in r.wrap_rows],children=[dict(type=c.metaObject().className(),name=c.accessibleName(),text=c.text()[:80] if hasattr(c,'text') else '',minimum=c.minimumSizeHint().width(),explicit=c.minimumWidth()) for c in r.body.findChildren(QWidget) if c.parent()==r.body]),indent=2),encoding='utf8')
    for name,button in r.buttons.items():
        reveal(button);rect=QRect(button.mapTo(r.scroll.viewport(),button.rect().topLeft()),button.size());visible=button.visibleRegion().boundingRect();assert rect.left()>=-1 and rect.right()<r.scroll.viewport().width()+1 and rect.top()>=0 and rect.bottom()<r.scroll.viewport().height(),(name,rect,r.scroll.viewport().size());assert visible==button.rect(),(name,visible,button.rect());layout_rows.append(dict(control=name,rect=[rect.x(),rect.y(),rect.width(),rect.height()],viewport=[r.scroll.viewport().width(),r.scroll.viewport().height()],visible=[visible.x(),visible.y(),visible.width(),visible.height()]))
    assert r.body.width()<=r.scroll.viewport().width() and not source.controls_scroll.isAncestorOf(source.preview);r.scroll.ensureWidgetVisible(r.units);app.processEvents();assert shell.grab().save(str(out/'expanded-review-1280x720.png'));r.scroll.ensureWidgetVisible(r.details);app.processEvents();assert shell.grab().save(str(out/'expanded-review-report-1280x720.png'))
    checks.append('Actual1280x720 expanded narrow Source review: every action fully visible vertically/horizontally through ONE controls-only scroll viewport, ancestor visibleRegion checked; native Source preview stays outside scroll hosting and retains actual native pixels, Program position unchanged; screenshots/geometry retained')
    with patch('project_review.digest',side_effect=AssertionError('Idle hashed document')) as hashes:
        for _ in range(200):start=time.perf_counter_ns();r.poll();idle_samples.append((time.perf_counter_ns()-start)/1e6)
        assert hashes.call_count==0
    # Controlled detached publication replacements, not an OS address-reuse claim.
    genuine=deepcopy(reply);state=w.state();projected=state;retained=r.report;retained_refs=r.report_refs;pending=Future();submitted=[]
    with patch.object(w,'state',side_effect=lambda:projected),patch.object(r,'submit_query',side_effect=lambda q:submitted.append(deepcopy(q)) or pending):
        projected=dict(state,media=deepcopy(state['media']));r.request('placement');first=projected['media'];assert r.intent[3][1] is first
        for i in range(16):
            next_media=deepcopy(state['media'])
            if i%2==0:next_media[asset['id']]['status']='Missing'
            projected=dict(state,media=next_media,source=dict(state['source'],document=deepcopy(state['source']['document'])));r.poll();assert r.report_refs is retained_refs and r.report_refs[1] is not projected['media'] and r.intent[3][1] is first
        pending.set_result(genuine);r.poll();assert r.report is retained and 'Outdated' in r.status.text();must_refuse(r.current_report)
    report=inspect('placement')
    checks.append('Controlled16 availability-only detached publications at same document revision retain original report/active intent objects; stale completion cannot match recycled IDs or publish;200idle polls perform0hashes (raw widget-only timings retained)')
    # Actual ordinary >64 same-source placements within the SAME12s timeline.
    before=deepcopy(w.document());changes=[dict(op='clip.add',id=new_id(),asset=asset['id'],track=clip['track'],name='Temporary duplicate '+str(i),start=i,duration=1,source_in=[10,1],layout=dict(opacity=0.)) for i in range(60)];w.batch('Temporary bounded duplicate-use pages',changes);idle();w.timeline.canvas.select('clips',clip['id']);report=inspect('placement');assert report['duplicate_use']['total']>64 and report['duplicate_use']['offset']==0;click(r.next_page);wait(lambda:r.future is None and r.report_context==r.context() and r.report['duplicate_use']['offset']==64);assert r.report['duplicate_use']['rows'] and 'later uses' in r.page_label.text();click(r.previous_page);wait(lambda:r.future is None and r.report['duplicate_use']['offset']==0);w.submit('undo');idle();assert w.document()==before;report=inspect('placement')
    checks.append('Actual >64-use fixture stays <=12s and within active-source caps; next/previous GUI pages reach later named uses/counts, no automatic editorial deletion; one exact Undo restores all original clips/pixels/audio recipes')
    # Actual accepted edit while a controlled GUI Future retains the old receipt.
    future=Future();old=deepcopy(report);voice=next(c for c in w.document()['clips'] if c['provenance'].get('component',{}).get('part')=='voice');before=deepcopy(w.document())
    with patch.object(r,'submit_query',return_value=future):
        r.request('placement');w.batch('Gain during retained GUI review', [dict(op='clip.audio',id=voice['id'],values=dict(gain=.31))]);idle();future.set_result(dict(ok=True,report=old));r.poll();assert 'Outdated' in r.status.text();must_refuse(r.current_report)
    w.submit('undo');idle();assert w.document()==before;click(r.buttons['Validate report']);wait(lambda:r.future is None and r.report_context==r.context());assert r.report['status']=='ready' and r.report['certificate']['origin']==old['certificate']['origin']
    checks.append('Actual accepted gain edit invalidates controlled pending GUI receipt; stale callback never publishes, exact Undo restores recipes and explicit validation preserves original provenance at a newer accepted revision')
    # Cancel-before-send and failed/unavailable projection states remain visible.
    for error,label in [('busy','Failed'),('missing_source','Unavailable')]:
        future=Future()
        with patch.object(r,'submit_query',return_value=future):r.request('placement');future.set_result(dict(ok=False,error=dict(code=error,message='Controlled '+error)));r.poll()
        for _ in range(5):r.poll()
        assert label in r.status.text();must_refuse(r.current_report)
    future=Future()
    with patch.object(r,'submit_query',return_value=future):r.request('placement');r.cancel();r.poll();assert 'Cancelled before' in r.status.text()
    report=inspect('placement');before=deepcopy(w.document());click(r.buttons['Remember range']);idle();remembered=deepcopy(w.document());assert marks(remembered)['items'];w.submit('undo');idle();assert w.document()==before;w.submit('redo');idle();assert w.document()==remembered;w.save(True,str(destination));idle();saved=deepcopy(w.document());w.submit('close');idle();w.open(str(destination));idle();assert all(w.document()[k]==saved[k] for k in ('provenance','clips','graphics','tracks','buses','master'))
    checks.append('Controlled GUI Busy/Unavailable/cancel-before-send states stay truthful without duplicate submission; ordinary remembered mixed range/named UndoRedo/portable new SaveAs/reopen preserve all original editable content')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,60)
    code=shell.client.process.returncode;assert code==0 and w.exited();shell=None;errors=out/'qt-errors.log';assert not errors.exists() or not errors.read_text(encoding='utf8')
    checks.append('Normal owned Qt Close drains real owner, Source/review/API/pixel readers and workers; owner exit0/empty Qt errors; no live session/window touched')
    assert all(hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest()==sha for name,sha in source_hashes.items());(out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,classification=__doc__,process_events_ms=events,widget_idle_ms=idle_samples,layout=layout_rows,proof=str(destination),proof_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),owner_exit=code,source_unchanged=True,unverified='Physical native input, actual device listening, GPU/scanout, correlated A/V and native sample exports are separate'),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,layout=layout_rows,process_events_ms=events,widget_idle_ms=idle_samples),indent=2),encoding='utf8')
    if shell:
        shell.grab().save(str(out/'failure-1280x720.png'))
        (out/'CONTEXT-DIAGNOSTICS.json').write_text(json.dumps(dict(status=r.status.text(),last_discard=r.last_discard,equal_publications=r.equal_publications,source_range=source.range,context=list(r.context()),controls_size=[source.controls_body.width(),source.controls_body.height()],controls_min=[source.controls_body.minimumWidth(),source.controls_body.minimumHeight()],scroll=[r.scroll.verticalScrollBar().value(),r.scroll.verticalScrollBar().maximum()],focus=app.focusWidget().accessibleName() if app.focusWidget() else None),indent=2),encoding='utf8')
    raise
finally:
    if shell and not shell.closing:
        w.close_resources();shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
        wait(lambda:w.exited(),60)
        (out/'CLEANUP.json').write_text(json.dumps(dict(owner_exit=shell.client.process.returncode,workspace_exited=w.exited(),source_exited=source.exited(),program_preview_exited=w.preview.exited(),classification='Failed-run finally cleanup only; exact parent failure retained separately. No process was terminated to obtain clearance.'),indent=2),encoding='utf8')
