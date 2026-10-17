"""EXACTLY TWO short native1080p range exports via existing Qt/API exporter.

Requires a separately coordinated hidden-GPU window. Parent Qt is CPU/offscreen,
audio uses discard-test only, no foreground/device/production/full-proof render.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from unittest.mock import patch
import os,sys,json,time,hashlib,threading,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);barrier=out/'owned-export-hold.flag';barrier.write_text('Bounded first-export snapshot test',encoding='utf8')
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_TEST_EXPORT_BARRIER=str(barrier))
from PySide6.QtWidgets import QApplication,QFileDialog,QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
import numpy as np,av
from studio_qt import Shell
from project_api import call
from project_manifest import binding as api_binding
from project_review import export_request,source_interval,inspect_review
from project_evaluator import Evaluator
from project_mixer import Mixer
from video_project import sample_at,new_id,pair
source_files=['project_review_samples_test.py','project_review.py','project_service.py','project_export.py','project_evaluator.py','project_visual.py','project_text.py','project_media.py','project_source.py','studio_project_review.py','studio_project_source.py','studio_project.py','studio_control_service.py','video_project.py']
source={str(Path('app/visuals')/name):hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest() for name in source_files}
for name in ('project_mixer.py','project_mix_factors.py'):source['app/audio/'+name]=hashlib.sha256((root/'app/audio'/name).read_bytes()).hexdigest()
native_paths=['work/native-raster/x64/abi1-migration-20261013-b/zerawave_raster.dll','work/native-media/x64/abi1-migration-20261013-a/zerawave_media_transfer.dll','work/native-surfaces/x64/abi1-migration-20261013-a/zerawave_surfaces.dll'];native={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in native_paths}
(out/'SOURCE.json').write_text(json.dumps(dict(source=source,native=native,proof=str(proof),proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),ranges=[[90,210],[180,360]],conditions=__doc__),indent=2),encoding='utf8')
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;checks=[];exports=[];timings=[];requests=[];comparison_failures=[]
def wait(fn,seconds=120):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        t=time.perf_counter_ns();app.processEvents();timings.append((time.perf_counter_ns()-t)/1e6);time.sleep(.004)
        if fn():return
    raise AssertionError('Native sample timeout: '+w.notice.text()+' | '+r.status.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and shell.client.edit_count==0)
def click(button):
    if source_panel.controls_scroll.isAncestorOf(button):button.setFocus(Qt.TabFocusReason);app.processEvents();source_panel.controls_scroll.ensureWidgetVisible(button,0,0);app.processEvents()
    QTest.mouseClick(button,Qt.LeftButton);app.processEvents()
def select_clip(clip):
    c=w.timeline.canvas;wait(lambda:c.version==(w.state()['epoch'],w.state()['revision']));rect=c.rects[('clips',clip['id'])];w.timeline.scroll.ensureVisible(round(rect.center().x()),round(rect.center().y()));app.processEvents();QTest.mouseClick(c,Qt.LeftButton,pos=rect.center().toPoint());app.processEvents();assert clip['id'] in c.selection
def query_for(clip,frame_range,purpose):
    state=call(endpoint,dict(op='state'))['state'];asset=next(a for a in state['document']['media'] if a['id']==clip['asset']);span=source_interval(state['document'],clip,asset)
    return dict(op='review_inspect',**api_binding(state),query_id=new_id(),source=asset['id'],source_range=[pair(v) for v in span],handles=[12,18] if frame_range[0]==90 else [0,0],range=frame_range,purpose=purpose,clip=clip['id'])
def terminal(key):
    value=call(endpoint,dict(op='operation_status',operation_id=key));assert value['ok'],value;return value['outcome']
def complete(key):
    holder={}
    def done():
        holder['value']=terminal(key);return holder['value']['status'] in ('exported','failed','rejected')
    wait(done);value=holder['value'];assert value['status']=='exported',value;assert value['result']['owned_resources_retired'];return value
def canonical(document,frames):
    e=Evaluator(document,'independent-frozen-mix',0);m=Mixer();parts=[];h=hashlib.sha256();begin=sample_at(document,frames[0]);sample=begin
    try:
        for frame in range(*frames):
            target=sample_at(document,frame+1)
            while sample<target:
                count=min(2048,target-sample);pcm=m.render(e.audio_span(sample,count));h.update(pcm);parts.append(pcm.copy());sample+=count
        return np.concatenate(parts),h.hexdigest(),deepcopy(m.metrics)
    finally:m.close();assert m.budget.used==0
def compare_audio(path,expected,frames):
    chunks=[];first=None;count=0
    with av.open(str(path)) as container:
        stream=container.streams.audio[0]
        for frame in container.decode(stream):
            stamp=Fraction(frame.pts)*frame.time_base
            if first is None:first=stamp
            assert stamp==Fraction(count,48000);chunks.append(frame.to_ndarray().T);count+=frame.samples
    decoded=np.concatenate(chunks);assert first==0 and len(expected)<=len(decoded)<len(expected)+1024;decoded=decoded[:len(expected)]
    windows=[(0,min(4800,len(expected))),(len(expected)//2,min(len(expected),len(expected)//2+4800)),(max(0,len(expected)-4800),len(expected))]
    # The voice fixture is deliberately UNITY DC +17 distinct tail samples,
    # not speech. Preserve raw DC/AC metrics separately; never claim heard words.
    metrics=[]
    for left,right in windows:
        a=expected[left:right].astype(np.float64);b=decoded[left:right].astype(np.float64);delta=b-a;variances=np.var(a,axis=0);corr=[float(np.corrcoef(a[:,j],b[:,j])[0,1]) if variances[j]>1e-8 else None for j in range(2)]
        metrics.append(dict(relative_samples=[left,right],sequence_samples=[sample_at(frozen,frames[0])+left,sample_at(frozen,frames[0])+right],expected_mean=a.mean(0).tolist(),decoded_mean=b.mean(0).tolist(),rmse=float(np.sqrt(np.mean(delta**2))),centered_rmse=float(np.sqrt(np.mean(((b-b.mean(0))-(a-a.mean(0)))**2))),correlation=corr))
    overall=float(np.sqrt(np.mean((decoded.astype(np.float64)-expected)**2)));result=dict(samples=len(expected),aac_tail_samples=count-len(expected),overall_rmse=overall,maximum_absolute_error=float(np.max(np.abs(decoded-expected))),windows=metrics,tolerance=dict(overall_rmse=.006,window_rmse=.01),basis='AAC192kbps lossy comparison, unity DC voice fixture; no exact encoded17sample-tail or spoken-word/listening claim')
    result['status']='PASS' if overall<.006 and all(m['rmse']<.01 for m in metrics) else 'FAIL'
    (out/(Path(path).stem+'-audio.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
    if result['status']=='FAIL':comparison_failures.append(dict(path=str(path),check='lossy_audio',metrics=result))
    return result
def compare_pictures(path,frames):
    wanted=[0,59,60,90,119] if frames[0]==90 else [0,52,53,60,179];count=0;metrics=[]
    with av.open(str(path)) as container:
        for index,frame in enumerate(container.decode(video=0)):
            assert Fraction(frame.pts)*frame.time_base==Fraction(index,30);assert [frame.width,frame.height]==[1920,1080];count+=1
            if index in wanted:
                sequence=frames[0]+index;w.transport('seek_paused',sequence);idle();wait(lambda:w.preview.valid_presented() and w.preview.presented[-1]==sequence);image=w.preview.view.surface.image.convertToFormat(QImage.Format_RGBA8888);reference=np.frombuffer(image.constBits(),np.uint8).reshape(1080,1920,4)[:,:,:3].copy();decoded=frame.to_ndarray(format='rgb24');delta=np.abs(decoded.astype(np.int16)-reference.astype(np.int16));row=dict(local_frame=index,sequence_frame=sequence,mean=float(delta.mean()),p99=float(np.percentile(delta,99)),maximum=int(delta.max()),comparison='Existing CPU reference preview vs native GPU/H264 decode; includes compositor/codec differences, not byte identity');metrics.append(row)
                assert QImage(decoded.tobytes(),1920,1080,QImage.Format_RGB888).save(str(out/(Path(path).stem+'-decoded-'+str(index)+'.png')));assert image.save(str(out/(Path(path).stem+'-reference-'+str(sequence)+'.png')))
                row['status']='PASS' if row['mean']<5 and row['p99']<32 else 'FAIL'
                if row['status']=='FAIL':comparison_failures.append(dict(path=str(path),check='decoded_picture',metrics=row))
    assert count==frames[1]-frames[0];return dict(frame_count=count,checkpoints=metrics,tolerance=dict(mean=5,p99=32),native_dimensions=[1920,1080],fps=[30,1],first_pts=0)
try:
    shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1280,720);shell.show();w=shell.project_workspace;source_panel=w.video_panels.source;r=source_panel.review;wait(lambda:w.state().get('endpoint'));endpoint=Path(w.state()['endpoint']);w.open(str(proof));idle();w.show_workspace();frozen=deepcopy(w.document());assert frozen['settings']['width']==1920 and frozen['settings']['height']==1080 and frozen['settings']['fps']==[30,1]
    # Capture the real GUI's exact export request BEFORE its normal submit.
    original_submit=w.client.submit
    def journal_submit(action,**data):
        request=data.get('request',{})
        if action=='project' and request.get('op')=='export':
            target=out/('GUI-exact-request-'+request['operation_id']+'.json')
            with target.open('x',encoding='utf8') as f:json.dump(request,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
            requests.append(deepcopy(request))
        return original_submit(action,**data)
    clip=next(c for c in frozen['clips'] if c['provenance'].get('component',{}).get('instance_key')=='review-10' and c['provenance']['component']['part']=='background');select_clip(clip);w.shell.panels['source_preview'].toggleView(True);w.shell.panels['source_preview'].setAsCurrentTab()
    if not r.toggle.isChecked():click(r.toggle)
    r.sequence_in.setValue(90);r.sequence_out.setValue(210);r.before.setValue(12);r.after.setValue(18);r.purpose.setText('Exact review to highlight context');click(r.buttons['Inspect placement']);wait(lambda:r.future is None and r.report_context==r.context());assert r.report['status']=='ready';report=deepcopy(r.report);assert report['mapping']['handled_interval_sequence_frames']==[[129,1],[159,1]]
    audio_before=call(endpoint,dict(op='audio_inspect',**w.binding(),range=[90,210]));assert audio_before['ok'];(out/'boundary-audio-chain.json').write_text(json.dumps(audio_before,indent=2),encoding='utf8')
    with patch.object(w.client,'submit',side_effect=journal_submit),patch.object(QFileDialog,'getSaveFileName',return_value=(str(out/'boundary-90-210.mp4'),'MP4')):click(r.buttons['Export sample…'])
    key=r.export_record['id'];wait(lambda:w.pending is None);assert len(requests)==1 and requests[0]['operation_id']==key and requests[0]['range']==[90,210]
    voice=next(c for c in frozen['clips'] if c['provenance'].get('component',{}).get('part')=='voice');original_revision=report['binding']['revision'];w.batch('Explicit gain/envelope during frozen review sample',[dict(op='clip.audio',id=voice['id'],values=dict(gain=.02,envelope=[[0,1.],[232,.7]]))]);idle();newer=deepcopy(w.document());assert newer!=frozen;w.save(True,str(out/'newer-pending.zwv'));idle();saved_revision=w.state()['saved_revision'];assert saved_revision==w.state()['revision'];barrier.unlink();first=complete(key);assert first['revision']==original_revision and first['result']['review_sample']==report['certificate'] and w.document()==newer and w.state()['saved_revision']==saved_revision
    wait(lambda:r.export_record.get('outcome',{}).get('status')=='exported');assert 'Outdated' in r.export_status.text();movie_hash=hashlib.sha256((out/'boundary-90-210.mp4').read_bytes()).hexdigest();click(r.buttons['Check sample']);wait(lambda:r.sample_future is None);click(r.buttons['Cancel sample']);wait(lambda:r.sample_future is None);assert r.export_record['outcome']['status']=='exported' and hashlib.sha256((out/'boundary-90-210.mp4').read_bytes()).hexdigest()==movie_hash
    w.submit('undo');idle();assert w.document()==frozen;w.save(True,str(out/'restored-project.zwv'));idle();checks.append('Actual Qt export press with patched filename choice journals exact request before normal owner submission; old revision/range remains frozen through actual gain/envelope edit + durable Save, no saved-revision corruption; SAME-ID Check and late Cancel preserve durable output')
    pcm,pcm_sha,pcm_stats=canonical(frozen,[90,210]);assert pcm_sha==first['result']['canonical_pcm_sha256'];audio=compare_audio(out/'boundary-90-210.mp4',pcm,[90,210]);pictures=compare_pictures(out/'boundary-90-210.mp4',[90,210]);exports.append(dict(range=[90,210],outcome=first,canonical_pcm_sha256=pcm_sha,pcm_stats=pcm_stats,decoded_audio=audio,pictures=pictures))
    # Second and last native movie. Script request uses the SAME ordinary owner.
    outro=next(c for c in frozen['clips'] if c['provenance'].get('component',{}).get('kind')=='outro' and c['provenance']['component']['part']=='background');q=query_for(outro,[180,360],'Complete synthetic voice tail and four-second sendoff');rr=call(endpoint,q);assert rr['ok'] and rr['report']['status']=='ready';state=call(endpoint,dict(op='state'))['state'];second_request=export_request(rr['report'],api_binding(state),str(out/'outro-180-360.mp4'),new_id(),state['document']['export']['crf'])
    with (out/'API-exact-request-outro.json').open('x',encoding='utf8') as f:json.dump(second_request,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    requests.append(deepcopy(second_request));reply=call(endpoint,second_request);assert reply['ok'];same=call(endpoint,second_request);assert same['outcome']['id']==second_request['operation_id'];second=complete(second_request['operation_id']);pcm,pcm_sha,pcm_stats=canonical(frozen,[180,360]);assert pcm_sha==second['result']['canonical_pcm_sha256'];audio=compare_audio(out/'outro-180-360.mp4',pcm,[180,360]);pictures=compare_pictures(out/'outro-180-360.mp4',[180,360]);exports.append(dict(range=[180,360],outcome=second,canonical_pcm_sha256=pcm_sha,pcm_stats=pcm_stats,decoded_audio=audio,pictures=pictures))
    checks.append('Exactly2new native1920x1080/30FPS H264/AAC outputs,120/180frames, PTS0/exclusiveOut/exact canonical48k spans; independent PCM hashes exact, decoded lossy checkpoints and card/highlight/outro native image comparisons retain raw metrics; complete17sample tail proven pre-encode, no encoded bit-identity/listening claim')
    assert len(list(out.glob('*.mp4')))==2 and all(e['outcome']['result']['owned_resources_retired'] for e in exports);w.submit('close');idle();w.open(str(out/'restored-project.zwv'));idle();assert all(w.document()[cat]==frozen[cat] for cat in ('clips','graphics','captions','tracks','buses','master','provenance'));checks.append('Normal new SaveAs/reopen preserves ordinary accepted edits/IDs/styles/curves/routing; each native job reports real reader/Mixer/GL retirement before durable output, no fullproof/episode or production write')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,60)
    code=shell.client.process.returncode;assert code==0 and w.exited();shell=None;errors=out/'qt-errors.log';assert not errors.exists() or not errors.read_text(encoding='utf8')
    assert all(hashlib.sha256((root/path).read_bytes()).hexdigest()==sha for path,sha in {**source,**native}.items());(out/'RESULT.json').write_text(json.dumps(dict(status='FAIL' if comparison_failures else 'PASS',checks=checks,exports=exports,comparison_failures=comparison_failures,classification=__doc__,raw_parent_process_events_ms=timings,owner_exit=code,source_unchanged=True,native_movies=2,unverified='Physical input/display/scanout/heard speech/continuous listening/correlated physical A-V; unity-DC synthetic voice is not narration'),indent=2),encoding='utf8');assert not comparison_failures,comparison_failures;print('PASS',len(checks),'EXACT2MOVIES')
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,exports=exports,raw_parent_process_events_ms=timings),indent=2),encoding='utf8');raise
finally:
    if shell and not shell.closing:
        for request in requests:
            try:call(endpoint,dict(op='cancel',operation_id=request['operation_id']))
            except Exception:pass
        barrier.unlink(missing_ok=True);w.close_resources();shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
