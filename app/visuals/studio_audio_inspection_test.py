"""Actual offscreen Qt/isolated owner/API/portable-save audio inspection.

Generated <=12s proof; CPU preview, discard-test sink, no hardware/foreground.
Delayed completion and availability-only changes are labelled controlled cases.
"""
from pathlib import Path
from copy import deepcopy
from concurrent.futures import Future
from unittest.mock import patch
import os, sys, json, time, traceback, hashlib, subprocess
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);inputs=Path(sys.argv[2]);proof=Path(sys.argv[3]);assert not proof.exists()
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QPushButton,QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from studio_qt import Shell
from video_project import new_id,sample_at
from project_api import call
from project_audio_inspection import describe,availability_key
from project_evaluator import Evaluator
from project_mixer import Mixer
import numpy as np
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;checks=[];observations=[]
def wait(fn,seconds=40):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        app.processEvents();time.sleep(.004)
        if fn():return
    raise AssertionError('Timeout '+w.notice.text())
def idle():wait(lambda:not w.pending and shell.client.edit_count==0 and not w.transport_future and not w.transport_desired)
def owner():return call(endpoint,dict(op='state'))['state']
def signature(s):return {k:deepcopy(s[k]) for k in ['document','epoch','revision','command_revision','saved_revision','dirty','undo_label','redo_label','history_bytes']}
def request(**kw):return dict(op='audio_inspect',**w.binding(),**kw)
def click(widget,title):
    button=next(b for b in widget.findChildren(QPushButton) if b.text()==title)
    assert button.isEnabled(),title
    QTest.mouseClick(button,Qt.LeftButton)
def inspected(widget,title):
    previous=widget.serial;click(widget,title);assert widget.serial==previous+1
    wait(lambda:widget.future is None and widget.desired is None)
    assert 'Ready' in widget.status.text(),(widget.status.text(),widget.intent,widget.context(widget.intent[1][4]))
    return deepcopy(widget.report)
def pcm(d,at):
    m=Mixer()
    try:return m.render(Evaluator(d,'comparison',1).audio_span(at,1024))
    finally:m.close();assert not m.budget.used
try:
    shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));endpoint=Path(w.state()['endpoint'])
    w.submit('new',name='Retrospective shared 12-second proof',settings=dict(width=1920,height=1080,fps=[30,1]));idle();w.show_workspace()
    voice,music,dialogue,bed,bus,titles,vc,mc1,mc2=[new_id() for _ in range(9)]
    changes=[]
    for key,name,path in [(voice,'Unity narration',inputs/'unity-voice.wav'),(music,'Music bed',inputs/'music-bed.wav')]:
        changes.append(dict(op='media.add',id=key,name=name,kind='Audio',location=dict(kind='external',path=str(path)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    changes.extend([dict(op='bus.add',id=bus,name='Dialogue'),dict(op='track.add',id=dialogue,kind='audio',name='Narration'),dict(op='track.output',id=dialogue,output=bus),dict(op='track.add',id=bed,kind='audio',name='Music'),dict(op='track.add',id=titles,kind='graphics',name='Proof labels'),dict(op='graphic.add',track=titles,start=0,duration=360,text='Review boundary / outro proof'),dict(op='clip.add',id=vc,asset=voice,track=dialogue,start=0,duration=233,pad_end='silence',audio=dict(gain=.04)),dict(op='track.audio',id=dialogue,values=dict(gain=10**(12/20))),dict(op='clip.add',id=mc1,asset=music,track=bed,start=60,duration=60,source_in=[2,1],audio=dict(gain=.05)),dict(op='clip.add',id=mc2,asset=music,track=bed,start=240,duration=120,source_in=[8,1],audio=dict(gain=.05,fade_out=9))])
    w.batch('Retrospective: authored audio proof',changes);idle();assert len(w.document()['clips'])==3
    c=w.timeline.canvas;c.selection={vc};c.selected=('clips',vc);w.video_panels.inspector.refresh();w.transport('seek_paused',30);idle()
    inspector=w.video_panels.inspector.audio_inspection;mixer=w.video_panels.mixer.audio_inspection
    before=signature(owner());report=inspected(inspector,'At playhead');after=signature(owner());assert before==after
    script=call(endpoint,request(frame=30,clips=[vc],tracks=[dialogue]));assert script['ok'] and report==script['report']
    assert inspector.details.toPlainText()==describe(report) and 'Narration' in inspector.details.toPlainText() and '1.000s' in inspector.details.toPlainText()
    expected=.04*10**(12/20);assert abs(report['contributions'][0]['observations'][0]['channel_multiplier'][0]['linear']-expected)<2e-8
    control=shell.client.submit('project',request=request(frame=30,clips=[vc],tracks=[dialogue]));wait(control.done);assert control.result()==script
    checks.append('Actual Qt press/release in existing Inspector -> existing Shell pool/API -> real owner; identical ordered-control/API/JSON/human values, no command/revision/history/save change')
    # Existing standalone CLI uses the same local authenticated endpoint.
    q=out/'CLI-REQUEST.json';q.write_text(json.dumps(request(frame=30,clips=[vc],tracks=[dialogue])),encoding='utf8')
    cli=subprocess.run([sys.executable,'-B','-X','utf8',str(root/'app/visuals/project_cli.py'),'--endpoint',str(endpoint),'--request',str(q)],capture_output=True,text=True,timeout=20)
    (out/'CLI-STDOUT.json').write_text(cli.stdout,encoding='utf8');(out/'CLI-STDERR.txt').write_text(cli.stderr,encoding='utf8');assert cli.returncode==0 and json.loads(cli.stdout)['report']==report
    c.selection.clear();c.selected=None;w.transport('range',[0,360]);idle();w.video_panels.mixer.refresh()
    # The Mixer can inspect all audio even without a clip selection.
    range_report=inspected(mixer,'Marked range');coverage=next(r for r in range_report['coverage'] if r['track_id']==bed)
    assert coverage['source_available']==[[96000,192000],[384000,576000]] and coverage['source_uncovered']==[[0,96000],[192000,384000]],coverage
    assert '4.000s (frame 120) to 8.000s (frame 240)' in mixer.details.toPlainText()
    checks.append('Actual Mixer Marked-range button with no selection explains exact intentional music gaps in readable seconds/frames; actual standalone CLI matches Inspector JSON')
    # Read-only stale owner requests never get journalled as artwork operations.
    bound=request(frame=30);state=signature(owner())
    for k,v in [('expected_epoch',new_id()),('expected_project',new_id()),('expected_revision',w.state()['revision']+1)]:
        bad=dict(bound,**{k:v});r=call(endpoint,bad);assert not r['ok'] and r['error']['code']=='stale_revision' and signature(owner())==state
    # Delay delivery of a real owner response at the GUI adapter, not the owner.
    retained=deepcopy(mixer.report);held=Future();sent=[]
    def delayed(query):sent.append(deepcopy(query));return held
    with patch.object(mixer,'submit_query',side_effect=delayed):click(mixer,'Marked range')
    assert len(sent)==1;reply=call(endpoint,sent[0]);assert reply['ok']
    w.batch('Explicit contribution change',[dict(op='track.audio',id=bed,values=dict(gain=.5))]);idle();held.set_result(reply);mixer.poll()
    assert mixer.report==retained and 'Outdated' in mixer.status.text() and mixer.future is None and mixer.desired is None
    checks.append('Stale epoch/project/revision rejected unchanged; controlled late real-owner reply after gain edit is visibly Outdated, retained as original evidence, no automatic retarget/retry')
    fresh=inspected(mixer,'Marked range');epoch=w.state()['epoch'];revision=w.state()['revision']
    # Controlled availability-only projection exercises no-revision invalidation.
    accepted_state=w.state;projection=deepcopy(accepted_state());projection['media'][music]['status']='Missing'
    with patch.object(w,'state',return_value=projection):
        mixer.poll();assert 'Outdated' in mixer.status.text() and mixer.report==fresh
        assert w.state()['epoch']==epoch and w.state()['revision']==revision
        assert availability_key(projection['document'],projection['media'])!=fresh['availability_sha256']
    checks.append('Controlled owner-projection availability change without document revision invalidates Ready display; report explicitly labels last verification, no fresh file-scan claim')
    # Latest explicit click waits for the prior read-only result, then uses its own intent.
    f1=Future();f2=Future();sent=[]
    def two(query):sent.append(deepcopy(query));return f1 if len(sent)==1 else f2
    with patch.object(mixer,'submit_query',side_effect=two):
        click(mixer,'At playhead');click(mixer,'Marked range');assert len(sent)==1
        f1.set_result(call(endpoint,sent[0]));mixer.poll();assert len(sent)==2 and 'range' in sent[1]
        f2.set_result(call(endpoint,sent[1]));mixer.poll();assert mixer.report['request']['range']==[0,360]
    checks.append('Controlled delayed read-only completions preserve latest deliberate frame/range intent; no parallel query fan-out or obsolete publication')
    c.selection={vc};c.selected=('clips',vc);w.video_panels.inspector.refresh()
    final=deepcopy(w.document());original_pcm=pcm(final,48000);w.save(True,str(proof));idle();wait(lambda:w.state()['saved_revision']==w.state()['revision'])
    w.submit('close');idle();w.submit('open',path=str(proof));idle();reopened=deepcopy(w.document());assert reopened['clips']==final['clips'] and reopened['tracks']==final['tracks'] and reopened['master']==final['master'] and reopened['buses']==final['buses'];assert np.array_equal(original_pcm,pcm(reopened,48000))
    c.selection={vc};c.selected=('clips',vc);w.transport('seek_paused',30);idle();w.video_panels.inspector.refresh();saved_report=inspected(inspector,'At playhead');assert abs(saved_report['contributions'][0]['observations'][0]['channel_multiplier'][0]['linear']-expected)<2e-8
    checks.append('Actual portable Save As/new path, owner Close/Open and editable authored clip/track/bus/Master values survive; canonical PCM exact, fresh report bound to new epoch')
    w.batch('Narration envelope proof',[dict(op='clip.audio',id=vc,values=dict(envelope=[[0,.5],[233,.5]]))]);idle();assert w.state()['undo_label']=='Narration envelope proof';w.submit('undo');idle();assert w.document()==reopened;w.submit('redo');idle();assert w.document()['clips'][0]['audio']['envelope']==[[0,.5],[233,.5]];w.submit('undo');idle();assert w.document()==reopened
    w.save(path=str(proof));idle();wait(lambda:w.state()['saved_revision']==w.state()['revision'])
    checks.append('Ordinary named gain/envelope edit and exact Undo/Redo restore content; final proof saved with intended original audio, no inspection history entry')
    # Detached publications share unchanged document/media values; idle pulses
    # must not repeatedly traverse/hash them even with a retained report.
    from project_audio_inspection import availability_key as native_key
    inspector.context('frame');mixer.context('range');pulse_ms=[]
    with patch('project_audio_inspection.availability_key',wraps=native_key) as hashing:
        for _ in range(200):
            started=time.perf_counter_ns();inspector.poll();mixer.poll();pulse_ms.append((time.perf_counter_ns()-started)/1e6)
        assert hashing.call_count==0,hashing.call_count
    checks.append('200 paired idle pulses reuse detached document/media/selection context with zero validation hashes; clock changes remain cheap and state/selection/validation changes invalidate')
    empty=dict(w.state(),document=None,media={})
    with patch.object(w,'state',return_value=empty):
        inspector.context('frame');mixer.context('range')
        with patch('project_audio_inspection.availability_key',wraps=native_key) as hashing:
            for _ in range(200):inspector.poll();mixer.poll()
            assert hashing.call_count==0
    checks.append('Controlled no-document projection retains visibly outdated reports with zero repeated empty-context hashing; actual owner/project untouched')
    inspected(inspector,'At playhead');w.video_panels.editing();app.processEvents();inspector.grab().save(str(out/'Inspector.png'))
    w.video_panels.audio_mixing();app.processEvents();inspected(mixer,'Marked range');mixer.grab().save(str(out/'Mixer.png'))
    (out/'FRAME-REPORT.json').write_text(json.dumps(saved_report,indent=2),encoding='utf8');(out/'RANGE-REPORT.json').write_text(json.dumps(range_report,indent=2),encoding='utf8')
    (out/'PROOF-IDS.json').write_text(json.dumps(dict(project=reopened['id'],voice=voice,music=music,dialogue=dialogue,bed=bed,bus=bus,titles=titles,voice_clip=vc,music_clips=[mc1,mc2]),indent=2),encoding='utf8')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,60)
    code=shell.client.process.returncode;assert code==0 and w.exited();shell=None
    errors=out/'qt-errors.log';text=errors.read_text(encoding='utf8') if errors.exists() else '';assert not text,text[-1500:]
    checks.append('Normal actual Qt Close retires disposable owner/project workers/readers, owner exit0 and empty Qt errors; no foreground or audible output')
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,poll_pair_ms=pulse_ms,poll_pair_summary_ms=dict(count=len(pulse_ms),median=float(np.median(pulse_ms)),p95=float(np.percentile(pulse_ms,95)),maximum=max(pulse_ms)),proof=str(proof),proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),owner_exit=code,classification=__doc__,physical_native_input_GPU_audio='UNVERIFIED'),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
    if shell and not shell.closing:
        w.close_resources();shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
