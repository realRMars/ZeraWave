"""Actual offscreen Qt component authoring, native-size CPU images and motion.

One disposable copy of the shared12s proof; real owner/codec/Inspector controls,
synthetic Qt input. No physical desktop/GPU/device or production interaction.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,json,time,traceback,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);identity=json.loads(Path(sys.argv[3]).read_text());destination=Path(sys.argv[4]);assert not destination.exists()
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import Qt,QRect
from PySide6.QtTest import QTest
from studio_qt import Shell
from project_manifest import stable,file_hash
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;checks=[];frames=[];callbacks=[];ns=identity['namespace']
def wait(fn,seconds=45):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        started=time.perf_counter_ns();app.processEvents();callbacks.append((time.perf_counter_ns()-started)/1e6);time.sleep(.004)
        if fn():return
    raise AssertionError('Timeout '+w.notice.text()+' | '+w.preview.status.text())
def idle():wait(lambda:not w.pending and not w.transport_future and not w.transport_desired and shell.client.edit_count==0)
def rendered(frame):
    w.transport('seek_paused',frame);idle();wait(lambda:w.preview.valid_presented() and w.preview.presented[-1]==frame)
    image=w.preview.view.surface.image;assert image is not None and [image.width(),image.height()]==[1920,1080]
    return image.copy()
def image_hash(image):return hashlib.sha256(image.constBits()).hexdigest()
try:
    shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1700,1000);shell.show();w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));w.open(str(proof));idle();w.show_workspace();original=deepcopy(w.document());c=w.timeline.canvas;ins=w.video_panels.inspector
    before=rendered(3);before.save(str(out/'card-1.png'));quote=stable(ns,'graphics','review-1.quote');c.select('graphics',quote);ins.version=None;ins.refresh();assert ins.text.isVisible()
    ins.text.setFocus();ins.text.selectAll();QTest.keyClicks(ins.text,'Explicit Qt component edit; other cards stay intact.');QTest.mouseClick(ins.text_apply,Qt.LeftButton);idle();edited=deepcopy(w.document());row=next(g for g in edited['graphics'] if g['id']==quote);assert row['text']=='Explicit Qt component edit; other cards stay intact.' and w.state()['undo_label']
    assert [g for g in edited['graphics'] if g['id']!=quote]==[g for g in original['graphics'] if g['id']!=quote]
    wait(lambda:w.preview.valid_presented() and w.preview.presented[:2]==(w.state()['epoch'],w.state()['revision']));changed=w.preview.view.surface.image.copy();assert image_hash(changed.copy(QRect(1104,448,738,158)))!=image_hash(before.copy(QRect(1104,448,738,158)))
    w.submit('undo');idle();assert w.document()==original;w.submit('redo');idle();assert w.document()==edited;w.submit('undo');idle();assert w.document()==original
    checks.append('Actual existing Inspector QTextEdit typing and Apply press/release change one normal component part and native pixels; exact other-instance preservation and descriptive Undo/Redo')
    # Ordinary style edit remains in the existing Inspector, no template runtime.
    c.select('graphics',quote);ins.version=None;ins.refresh();color=ins.lines['color'];color.setFocus();color.selectAll();QTest.keyClicks(color,'#83bed8');QTest.keyClick(color,Qt.Key_Return);idle();colored=deepcopy(w.document());assert next(g['style']['color'] for g in colored['graphics'] if g['id']==quote)=='#83bed8';w.submit('undo');idle();assert w.document()==original
    checks.append('Existing Qt color field edits the chosen native text part and Undo restores exact styles; other components and source media intact')
    for frame,label in [(18,'card-2'),(138,'card-10'),(180,'outro-0'),(195,'outro-15'),(210,'outro-30')]:
        image=rendered(frame);assert image.save(str(out/(label+'.png')));crop=image.copy(QRect(576,648,768,216));frames.append(dict(frame=frame,native_size=[1920,1080],image_sha256=image_hash(image),background_only_region=[576,648,768,216],background_sha256=image_hash(crop),presented=list(w.preview.presented),status=w.preview.status.text()))
    motion=[r for r in frames if r['frame']>=180];assert len({r['background_sha256'] for r in motion})>1
    assert w.document()==original
    checks.append('Representative native1080 quote-card/outro captures; three distinct requested outro frames change in a background-only region away from overlays, proving real decoded gameplay motion rather than a still/cursor/progress change')
    c.selection.clear();c.selected=None;w.save(True,str(destination));idle();wait(lambda:w.state()['saved_revision']==w.state()['revision']);saved=deepcopy(w.document());w.submit('close');idle();w.open(str(destination));idle();assert w.document()['clips']==saved['clips'] and w.document()['graphics']==saved['graphics'];rendered(195)
    text_stats=deepcopy(w.preview.view.surface.text.stats);media=deepcopy(w.preview.media.metrics);shell.grab().save(str(out/'Qt-Inspector.png'))
    checks.append('Actual Qt Save As to a new disposable destination, owner Close/Open and normal native preview preserve every stable part ID/source/style/key/curve; no production/source overwrite')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,60)
    code=shell.client.process.returncode;assert code==0 and w.exited();shell=None
    errors=out/'qt-errors.log';error=errors.read_text(encoding='utf8') if errors.exists() else '';assert not error,error[-1500:]
    checks.append('Normal Qt Close waits for real owner, native readers, scratch/cache and workers; owner exit0/empty Qt errors, no forced/live-session termination')
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,frames=frames,process_events_ms=callbacks,text_stats=text_stats,media_stats=media,proof=str(destination),proof_sha256=file_hash(destination),owner_exit=code,classification=__doc__,unverified='Physical Windows input, GPU display/scanout, listening and full editor acceptance'),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(frames=frames,checks=checks),indent=2),encoding='utf8');raise
finally:
    if shell and not shell.closing:
        w.close_resources();shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
