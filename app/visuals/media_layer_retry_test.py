"""Controlled native-worker failure and Qt Play callback over real owner components.

Real ProjectService, MediaFrames/native lanes, canonical dispatch and existing
Layers.transport callback; lightweight client/registry adapters, no IPC/full Studio
for injected cases. No device/GPU/foreground/production or automatic retry.
"""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace as NS
from unittest.mock import patch
import sys,os,time,json,threading,uuid,traceback,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);fixture=Path(sys.argv[2]);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from PySide6.QtWidgets import QApplication,QPushButton
from project_service import ProjectService
from studio_control_service import dispatch_media_transport
from studio_composition import Layers
from studio_video_workspace import inspect_source
from media_frames import MediaFrames,SourceLane,FrameReader,failure_kind,MediaSourceUnavailable,MediaSourceChanged,MediaSourceInvalid
from composition import defaults,new_layer,validate_scene
app=QApplication([]);app.setQuitOnLastWindowClosed(False);service=ProjectService();frames=None;checks=[];cases=[];reader=FrameReader();errors=[]
def wait(fn,seconds=12):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.processEvents();time.sleep(.004)
        value=fn()
        if value:return value
    raise AssertionError('Component worker did not settle')
def binding():
    s=service.state(False);return dict(expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'])
def request(op,**args):
    reply=service.request(dict(op=op,operation_id=uuid.uuid4().hex,**binding(),**args));assert reply['ok'],reply;return reply
def safe(fn):
    try:return fn()
    except ValueError as exc:errors.append(str(exc))
class Client:
    @property
    def snapshot(self):return dict(media_frames=frames.snapshot())
    def command(self,action,**data):assert action=='media_transport';return dispatch_media_transport(owner,data)
def click():
    before=len(errors);button.click();app.processEvents();return errors[before:]
def close_frames():
    global frames
    if frames is None:return
    reader.close();assert frames.close();r=frames.resources();assert not r['cleanup_errors'] and r['decoded_planes_bytes']==0 and r['shared_slots_bytes']==0 and all(not lane['worker_alive'] for lane in r['lanes']);frames=None
def activate():request('transport',action='seek_paused',frame=15);assert service.transport.active
def new_frames(record,transient=False):
    global frames,owner
    records[asset['id']]=deepcopy(record);frames=MediaFrames();frames.freeze(True);owner=NS(media_frames=frames,projects=service,media_registry=NS(assets=records),rasters=NS(rows={}),media_session='controlled-session');frames.sync(scene,records)
try:
    path=out/'valid-av.mp4';path.write_bytes(fixture.read_bytes());source_hash=hashlib.sha256(path.read_bytes()).hexdigest();asset=inspect_source(dict(id=uuid.uuid4().hex,name='Valid pinned fixture',path=str(path)),threading.Event());record=dict(id=asset['id'],kind='Video',name=asset['name'],path=str(path),metadata=asset['metadata'],sha256=asset['sha256'],status='Ready');records={asset['id']:record}
    scene=defaults();layer=new_layer('Video',asset['id'],'Retry fixture');layer['media']['loop']='Loop';scene['layers']=[layer];scene['assets']=[{k:record[k] for k in ('id','kind','name','path')}];key=layer['id']
    request('new',name='Retained project');track=uuid.uuid4().hex;request('batch',changes=[dict(op='track.add',id=track,kind='graphics'),dict(op='graphic.add',track=track,start=0,duration=60,text='Preserved')]);request('transport',action='range',frame=[5,45]);activate();document=deepcopy(service.document);revision=service.revision;history=len(service.undo)
    editor=NS(selected=key,binding=('controlled-session',0),shell=NS(client=Client(),project_workspace=NS(binding=binding),safe=safe));button=QPushButton('Play');button.clicked.connect(lambda:Layers.transport(editor,'play'))
    original=SourceLane.process;fault=dict(remaining=1,calls=0)
    def fail_once(lane,job):
        fault['calls']+=1
        if fault['remaining']:
            fault['remaining']-=1;raise MemoryError('Controlled transient native-plane admission failure')
        return original(lane,job)
    with patch.object(SourceLane,'process',new=fail_once):
        new_frames(record);wait(lambda:frames.snapshot().get(key,{}).get('error_kind')=='decode_retryable');failed=deepcopy(frames.snapshot()[key]);calls=fault['calls'];time.sleep(.08);assert fault['calls']==calls and service.transport.active
        command=service.command_revision;assert click()==[];assert frames.layers[key]['playing'] and frames.layers[key]['error']=='' and not service.transport.active and service.command_revision==command+1
        # Handoff cannot clear an independent/global MediaFrames freeze.
        assert frames.frozen;positions=[frames.snapshot()[key]['position'] for _ in range(3)];assert len(set(positions))==1
        frames.freeze(False);wait(lambda:key in frames.results and not frames.snapshot()[key].get('error_kind'));first=reader.read(frames.results[key]);assert first
        at=first['pts'];wait(lambda:frames.results.get(key,{}).get('pts')!=at);assert reader.read(frames.results[key]);assert service.document==document and service.revision==revision and len(service.undo)==history
        cases.append(dict(case='transient',error_kind=failed['error_kind'],Play_cleared_error=True,native_decode_resumed=True,same_source_sha256=source_hash,only_explicit_retry=True,independent_freeze_retained=True,project_frame=service.transport.frame,project_range=[service.transport.range_in,service.transport.range_out]));assert service.transport.frame==15 and service.transport.range_in==5 and service.transport.range_out==45
    checks.append('Real native lane MemoryError stops automatic scheduling; existing Qt Play callback clears transient error, hands off once, and decodes the same pinned source without hidden Release')
    checks.append('Handoff leaves independent MediaFrames freeze intact; explicit fixture release resumes native frames. This is component Hold evidence, not a running renderer/device test')
    close_frames()
    for name,target,kind in [('missing',out/'absent.mp4','source_unavailable'),('changed',out/'changed.mp4','source_changed'),('invalid',out/'invalid.mp4','source_invalid')]:
        if name=='changed':target.write_bytes(path.read_bytes())
        if name=='invalid':target.write_bytes(b'Controlled invalid local test copy')
        bad=dict(record,path=str(target),metadata=deepcopy(record['metadata']))
        if name=='invalid':bad['metadata']['mtime_ns']=target.stat().st_mtime_ns
        activate();new_frames(bad);wait(lambda:frames.snapshot().get(key,{}).get('error_kind')==kind);before=deepcopy(frames.layers[key]);command=service.command_revision;messages=click();assert messages and 'Refresh/Relink' in messages[-1];assert service.transport.active and service.transport.frame==15 and service.command_revision==command and frames.layers[key]['epoch']==before['epoch'] and frames.layers[key]['error']==before['error'];cases.append(dict(case=name,error_kind=kind,rejected=messages[-1],project_retained=True));close_frames()
    checks.append('Actual missing-file, changed-timestamp and PyAV invalid-format failures cannot take active project ownership; no source/edit/history mutation')
    activate();new_frames(record);wait(lambda:key in frames.results)
    for status in ('Missing','Changed','Unavailable','Loading'):
        records[asset['id']]['status']=status;command=service.command_revision;messages=click();assert messages and service.transport.active and service.command_revision==command;cases.append(dict(case='registry '+status,rejected=True,project_retained=True))
    records[asset['id']]['status']='Ready';assert click()==[];assert not service.transport.active;frames.freeze(False);wait(lambda:frames.snapshot()[key]['playing']);assert service.document==document and service.revision==revision and len(service.undo)==history;close_frames();checks.append('Unvalidated/changed registry references reject intact; explicit Ready recovery and Play work in the same owner components')
    # Existing editable-raster Image -> Sprite sheet path, not a new source type.
    from PySide6.QtGui import QImage,QColor,QPainter
    from media_registry import inspect
    sheet=out/'sprite-sheet.png';image=QImage(32,16,QImage.Format_RGBA8888);image.fill(QColor('red'));painter=QPainter(image);painter.fillRect(16,0,16,16,QColor('green'));painter.end();assert image.save(str(sheet),'PNG')
    raster=inspect(str(sheet),threading.Event());raster.update(id=uuid.uuid4().hex,managed=True,internal=True)
    sprite=new_layer('Sprite',raster['id'],'Raster-owned sheet');sprite['media'].update(columns=2,rows=1,first=0,last=1,fps=6,loop='Loop');sprite_scene=defaults();sprite_scene['layers']=[sprite];sprite_scene['assets']=[{k:raster[k] for k in ('id','kind','name','path')}];sprite_scene=validate_scene(sprite_scene);key=sprite['id'];editor.selected=key
    activate();frames=MediaFrames();frames.freeze(True);owner=NS(media_frames=frames,projects=service,media_registry=NS(assets={raster['id']:dict(raster,status='Missing')}),rasters=NS(rows={raster['id']:raster}),media_session='controlled-session');frames.sync(sprite_scene,{**owner.media_registry.assets,**owner.rasters.rows});wait(lambda:key in frames.results);assert reader.read(frames.results[key])
    assert click()==[] and not service.transport.active and frames.layers[key]['playing'];assert frames.frozen;frames.freeze(False);first=frames.results[key]['pts'];wait(lambda:frames.results.get(key,{}).get('pts')!=first);assert reader.read(frames.results[key]);assert service.document==document and service.revision==revision and len(service.undo)==history;cases.append(dict(case='raster-owned Sprite',ready_raster_overrides_missing_library=True,native_frames=True,Play_handoff=True,project_preserved=True))
    frames.command(key,'pause');activate();frames.freeze(True);owner.media_registry.assets[raster['id']]=dict(raster,status='Ready');owner.rasters.rows[raster['id']]=dict(raster,status='Missing');command=service.command_revision;messages=click();assert messages and service.transport.active and service.command_revision==command and not frames.layers[key]['playing'];cases.append(dict(case='unavailable raster overrides Ready library',rejected=True,project_preserved=True));close_frames()
    checks.append('Validated raster-owned Sprite decodes/plays/hands off without reimport; exact raster precedence permits Ready raster over Missing library and rejects Missing raster over Ready library')
    assert failure_kind(MediaSourceChanged())=='source_changed' and failure_kind(MediaSourceInvalid())=='source_invalid';assert failure_kind(FileNotFoundError())=='source_unavailable' and failure_kind(PermissionError())=='source_unavailable' and failure_kind(MediaSourceUnavailable())=='source_unavailable' and failure_kind(MemoryError())=='decode_retryable' and failure_kind(RuntimeError())=='decode_retryable';assert hashlib.sha256(path.read_bytes()).hexdigest()==source_hash
    service.shutdown();checks.append('Typed failure labels, unchanged source hash, all native lanes/maps/planes/shared slots retire without cleanup errors')
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,cases=cases,classification=__doc__,source_sha256=source_hash,project_and_history_preserved=True,component_freeze_preserved=True,actual_legacy_renderer_Hold='UNVERIFIED'),indent=2),encoding='utf8');print('PASS',len(checks),'groups',len(cases),'cases')
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8')
    (out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,cases=cases,current_case=locals().get('name'),runtime=frames.snapshot() if frames else None,resources=frames.resources() if frames else None),indent=2),encoding='utf8');raise
finally:
    close_frames()
    if not service.closed:service.shutdown()
