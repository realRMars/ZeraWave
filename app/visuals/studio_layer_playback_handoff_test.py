"""Isolated actual Qt/owner Layers-New-project and transport handoff checks.

Offscreen CPU, generated AV fixture and discard-test sink; no audible device,
foreground, GPU, physical/native input, production or live-session interaction.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,time,json,traceback,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);fixture=Path(sys.argv[2])
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QPushButton,QMessageBox
from studio_qt import Shell
from video_project import new_id
from studio_video_workspace import inspect_source
import threading
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;observations=[];checks=[];rejections=[]
def wait(fn,seconds=40):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.processEvents();time.sleep(.004)
        if fn():return
    raise AssertionError('Timeout: '+w.notice.text()+' | '+ed.status.text())
def idle():wait(lambda:not w.pending and not ed.edit_jobs and shell.client.edit_count==0 and not w.transport_future and not w.transport_desired)
def sample(label,seconds=.7):
    rows=[];deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.processEvents();time.sleep(.025);snap=deepcopy(shell.client.snapshot);r=snap.get('media_frames',{}).get(layer,{})
        image=ed.images.get(layer);pixels=hashlib.sha256(image.constBits()).hexdigest() if image is not None else None
        rows.append(dict(at=time.perf_counter(),position=r.get('position'),state=r.get('state'),playing=r.get('playing'),transport=r.get('transport'),error=r.get('error'),held=r.get('held'),frame=(r.get('frame') or {}).get('pts'),presented=deepcopy(getattr(ed,'media_presented',{}).get(layer)),pixels=pixels,project=snap.get('project_transport'),audio=deepcopy(snap.get('audio_hub',{}).get('project_audio',{}))))
    observations.append(dict(label=label,rows=rows));return rows
def moving(rows):return len({r['position'] for r in rows if r['position'] is not None})>1
def pixels_move(rows):return len({r['pixels'] for r in rows if r['pixels'] is not None})>1
def project_frame(frame=15):
    w.transport('seek_paused',frame);idle();wait(lambda:w.transport_state().get('active') and not w.transport_state().get('playing'))
    if shell.client.snapshot['media_frames'][layer]['playing']:
        wait(lambda:shell.client.snapshot['media_frames'][layer]['state']=='paused')
    return deepcopy(w.transport_state())
def layer_play():
    buttons=[b for b in ed.findChildren(QPushButton) if b.text()=='▶' and b.toolTip()=='Play']
    assert len(buttons)==1,len(buttons)
    buttons[0].click() # Actual existing Qt control/signal -> captured owner command.
def monitor_play(target):
    monitor=w.video_panels.preview_transport;monitor.context.setCurrentIndex(int(target=='source'));monitor.refresh();assert monitor.buttons['play'].isEnabled();monitor.buttons['play'].click()
def layer_pause():
    ed.transport('pause');idle();wait(lambda:not shell.client.snapshot['media_frames'][layer]['playing'])
def reject_play(label,**overrides):
    before=deepcopy(w.document());p=deepcopy(w.transport_state());world=deepcopy(ed.config);state=deepcopy(shell.client.snapshot['media_frames'][layer]);command=w.binding()['expected_command']
    data=dict(layer=layer,op='play',media_session=ed.binding[0],source=state['source'],project_binding=deepcopy(w.binding()));data.update(overrides)
    if data.get('project_binding','missing') is None:data.pop('project_binding')
    future=shell.client.submit('media_transport',**data);wait(future.done)
    try:future.result();raise AssertionError(label+' unexpectedly accepted')
    except ValueError as exc:rejections.append(dict(case=label,error=str(exc)))
    idle();assert w.document()==before and ed.config==world and w.binding()['expected_command']==command
    assert w.transport_state()['active']==p['active'] and w.transport_state()['frame']==p['frame']
    assert shell.client.snapshot['media_frames'][layer]['playing']==state['playing']
try:
    source=out/'moving-av.mp4';source.write_bytes(fixture.read_bytes());original=hashlib.sha256(source.read_bytes()).hexdigest()
    shell=Shell(out/'layout.json',out/'owner.log');shell.show();w=shell.project_workspace;ed=shell.image_editor;wait(lambda:w.state().get('endpoint'))
    future=shell.client.submit('media_import',paths=[str(source)]);wait(future.done);future.result();wait(lambda:len(shell.client.snapshot.get('media_library',{}).get('assets',[]))==1 and not shell.client.snapshot['media_library'].get('pending'))
    shell.media_library.refresh();asset=deepcopy(next(iter(shell.media_library.assets.values())));assert asset['kind']=='Video' and asset['status']=='Ready';assert ed.add_asset(asset);wait(lambda:not ed.edit_jobs and len(ed.config['layers'])==1);layer=ed.selected;wait(lambda:layer in shell.client.snapshot.get('media_frames',{}));ed.media_edit('loop','Loop');idle();assert ed.selected_row()['media']['loop']=='Loop';layer_play();idle();initial=sample('Initial Layer playback');assert moving(initial) and pixels_move(initial)
    checks.append('Real Layer decode, shared-frame reader and offscreen CPU canvas image change before project use')
    world=deepcopy(ed.config)
    with patch.object(w,'dialog',return_value=True):w.new()
    idle();assert w.video_panels.active;created=deepcopy(w.document());revision=w.state()['revision'];new_rows=sample('Actual Qt New video callback + workspace');assert moving(new_rows) and not w.transport_state()['active']
    w.video_panels.studio();ed.reveal();returned=sample('Return from New to Studio/Layers');assert moving(returned) and pixels_move(returned);assert ed.config==world and w.document()==created and w.state()['revision']==revision
    w.show_workspace();again=sample('Reactivate workspace');assert moving(again);w.video_panels.studio();ed.reveal();again=sample('Return again');assert moving(again) and pixels_move(again)
    checks.append('Exact actual New/workspace/return control and repeated both-direction switches preserve Layer timestamps/pixels/content; New alone does not activate Program')
    w.batch('Project range fixture',[dict(op='track.add',id=(track:=new_id()),kind='graphics'),dict(op='graphic.add',track=track,start=0,duration=60,text='Transport handoff')]);idle();w.transport('range',[5,45]);idle();project_frame();doc=deepcopy(w.document());revision=w.state()['revision'];world=deepcopy(ed.config);layer_revision=shell.client.snapshot['media_control']['revision'];clock=deepcopy(w.transport_state());command=w.binding()['expected_command'];before=sample('Paused active Program freezes still-requested Layer');assert not moving(before)
    layer_play();idle();wait(lambda:not w.transport_state()['active']);after=sample('Explicit Layer Play returns ownership');assert moving(after) and pixels_move(after);assert w.transport_state()['frame']==clock['frame'] and w.transport_state()['range_in']==5 and w.transport_state()['range_out']==45;assert w.binding()['expected_command']==command+1
    assert w.document()==doc and w.state()['revision']==revision and ed.config==world and shell.client.snapshot['media_control']['revision']==layer_revision
    checks.append('Valid Layer Play releases paused Program once, preserves exact position/ranges/documents/history and resumes pixels in same instance')
    layer_pause();project_frame()
    reject_play('unbound cross-domain intent',project_binding=None)
    reject_play('unbound layer source',source=None)
    for key,value in [('expected_project',new_id()),('expected_epoch',new_id()),('expected_revision',revision+1),('expected_command',w.binding()['expected_command']+1)]:
        binding=deepcopy(w.binding());binding[key]=value;reject_play('stale '+key,project_binding=binding)
    reject_play('obsolete layer session',media_session='obsolete');reject_play('obsolete source',source=['obsolete']);reject_play('nonexistent layer',layer=new_id());reject_play('unsupported command',op='unknown')
    checks.append('Ten stale/unbound/invalid layer/source/project/command rejections preserve both runtime contexts and accepted work')
    before=deepcopy(ed.config);ed.config['layers'][0]['enabled']=False;assert ed.commit('Hide fixture layer',before);idle();reject_play('hidden layer cannot take active project ownership');before=deepcopy(ed.config);ed.config['layers'][0]['enabled']=True;assert ed.commit('Show fixture layer',before);idle();layer_play();idle();wait(lambda:not w.transport_state()['active']);assert moving(sample('Visible layer recovery'))
    checks.append('Hidden Layer cannot take active project ownership; deliberate show then Play recovers without restart')
    source_asset=inspect_source(dict(id=asset['id'],name=asset['name'],path=str(source)),threading.Event());w.submit('source_open',asset=source_asset);idle();wait(lambda:w.state().get('source',{}).get('document') is not None);w.transport('range',[1,17],target='source');idle();w.transport('seek_paused',4,target='source');idle();source_clock=deepcopy(w.source_transport_state());assert source_clock['active'];command=w.binding()['expected_command'];layer_play();idle();wait(lambda:not w.source_transport_state()['active']);assert w.binding()['expected_command']==command+1;assert w.source_transport_state()['frame']==4 and w.source_transport_state()['range_in']==1 and w.source_transport_state()['range_out']==17
    checks.append('Source inspection lease also releases through explicit Layer Play while preserving Source frame and range')
    monitor_play('source');idle();wait(lambda:w.source_transport_state()['active']);sample('Source plays through existing discard-test single audio owner',.2);layer_play();idle();wait(lambda:not w.source_transport_state()['active'] and not shell.client.snapshot.get('audio_hub',{}).get('project_audio',{}).get('active'));assert moving(sample('Layers after Source output retirement'))
    checks.append('Actual Source playback yields to Layer Play; existing single audio owner drains normally using discard-test, no audible device')
    monitor_play('program');idle();wait(lambda:w.transport_state()['active']);sample('Program playback takes its normal gate',.2);layer_play();idle();wait(lambda:not w.transport_state()['active']);assert moving(sample('Layers return from Program playback'));assert w.document()==doc and w.state()['revision']==revision
    checks.append('Program playback and return-to-Layers work in both directions without resetting or editing document')
    # Save/reopen the ordinary project while the separate accepted Layer scene is retained.
    saved=out/'project'/'handoff.zwv';w.save(save_as=True,path=str(saved));idle();assert w.last_outcome['status']=='durable';saved_doc=deepcopy(w.document());layer_ids=[r['id'] for r in ed.config['layers']];w.open(path=str(saved));idle();assert w.document()==saved_doc and [r['id'] for r in ed.config['layers']]==layer_ids;layer_play();idle();w.video_panels.studio();ed.reveal();assert moving(sample('Layers after project Save As/open/return'))
    checks.append('Project Save As/reopen/workspace return keeps authored values and stable Layer IDs; subsequent Layer playback remains available')
    resources=deepcopy(shell.client.snapshot['media_resources']);assert resources['cache_budget']==96*1024*1024 and resources['staging_budget']==128*1024*1024 and not resources['cleanup_errors'];assert len(resources['lanes'])==4
    checks.append('Existing four lanes and96MiB cache/128MiB staging observed without cleanup errors; actual legacy-renderer Hold remains UNVERIFIED')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):
        shell.close();wait(lambda:shell.closing,60)
    exit_code=shell.client.process.returncode;assert exit_code==0 and w.exited();shell=None
    checks.append('Actual normal Qt Close waits for owner exit, all project/Source readers and worker retirement; only disposable unsaved-content prompts are stubbed')
    errors=out/'qt-errors.log';error_text=errors.read_text(encoding='utf8') if errors.exists() else '';assert not error_text,error_text[-1200:];assert hashlib.sha256(source.read_bytes()).hexdigest()==original
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,observations=observations,rejections=rejections,resources=resources,owner_exit=exit_code,qt_errors=error_text,source_sha256=original,classification=__doc__,physical_windows_GPU_audio_correlation='UNVERIFIED',legacy_renderer_Hold_runtime='UNVERIFIED; unchanged freeze-policy comparison only',owner_pre_restart_failure='Unavailable; exact empty New control did not reproduce it'),indent=2),encoding='utf8');print('PASS',len(checks),'groups',len(rejections),'rejections')
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL_OBSERVATIONS.json').write_text(json.dumps(observations,indent=2),encoding='utf8');raise
finally:
    if shell and not shell.closing:
        w.close_resources();shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
