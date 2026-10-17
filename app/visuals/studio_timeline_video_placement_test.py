"""Actual offscreen Qt drag dispatch and Source load/Place with isolated owner.

No foreground, physical/OLE input, GPU, audio output or production session use.
--expect-bug preserves a natural pre-fix reproduction of both reported paths.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from unittest.mock import patch
import os,sys,json,time,uuid,threading,hashlib,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);expect_bug='--expect-bug' in sys.argv
os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_EDITOR_GPU='cpu',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
import av,numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPoint,QPointF,QMimeData
from PySide6.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent
from studio_qt import Shell
from studio_video_workspace import inspect_source
from project_evaluator import Evaluator
from video_project import new_id
app=QApplication([]);app.setQuitOnLastWindowClosed(False);shell=None;checks=[];cases=[];events=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def wait(fn,seconds=40):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        app.processEvents();time.sleep(.002)
        if fn():return
    raise AssertionError('Timed out: '+w.notice.text())
def idle():
    wait(lambda:not w.pending and w.timeline.placement is None and shell.client.edit_count==0 and not w.transport_future and not w.transport_desired)
    w.refresh()
def make_source(path,with_audio=True):
    with av.open(str(path),'w') as container:
        video=container.add_stream('mpeg4',rate=30);video.width=64;video.height=48;video.pix_fmt='yuv420p'
        audio=container.add_stream('aac',rate=48000) if with_audio else None
        if audio:audio.layout='stereo'
        for i in range(18):
            data=np.zeros((48,64,3),np.uint8);data[:,:,i%3]=70+i*8;data[:,i*3%50:i*3%50+12]=240
            frame=av.VideoFrame.from_ndarray(data,format='rgb24');frame.pts=i;frame.time_base=Fraction(1,30)
            for packet in video.encode(frame):container.mux(packet)
            if audio:
                samples=np.full((2,1600),.08,np.float32);f=av.AudioFrame.from_ndarray(samples,format='fltp',layout='stereo');f.sample_rate=48000;f.pts=i*1600;f.time_base=Fraction(1,48000)
                for packet in audio.encode(f):container.mux(packet)
        for packet in video.encode():container.mux(packet)
        if audio:
            for packet in audio.encode():container.mux(packet)
def setup(mode):
    # Clear the preceding fixture's selected Inspector row before replacing its
    # document. Otherwise the rapid synthetic loop exposes an unrelated baseline
    # Inspector refresh ordering error; it is retained in correction-check-01.
    w.timeline.canvas.selection.clear();w.timeline.canvas.selected=None;w.video_panels.inspector.version=None;w.video_panels.inspector.refresh()
    w.submit('new',discard=True,name='Disposable placement',settings=dict(width=64,height=48,fps=[30,1]));idle()
    v,a=[new_id() for _ in range(2)]
    w.batch('Fixture tracks',[dict(op='track.add',id=v,kind='video',name='Video target'),dict(op='track.add',id=a,kind='audio',name='Audio target')]);idle()
    w.timeline.source_mode.setCurrentIndex(mode);saved=w.timeline.view_settings();path=out/('view-mode-'+str(mode)+'.json');path.write_text(json.dumps(saved),encoding='utf8');w.timeline.source_mode.setCurrentIndex(0);w.timeline.restore_view(json.loads(path.read_text()));w.timeline.canvas.resize(600,220);w.timeline.refresh()
    assert w.timeline.source_mode.currentIndex()==mode
    return v,a
def counts():
    d=w.document();tracks={t['id']:t for t in d['tracks']};e=Evaluator(d,w.state()['epoch'],w.state()['revision']);p=e.at(0)
    return dict(video=sum(tracks[c['track']]['kind']!='audio' for c in d['clips']),audio=sum(tracks[c['track']]['kind']=='audio' for c in d['clips']),visual_plan=len(p['visual']),audio_plan=len(p['audio']))
def drop(asset,track,frame=0,project=False,settle=True):
    c=w.timeline.canvas;mime=QMimeData();mime.setData('application/x-zerawave-project-media' if project else 'application/x-zerawave-assets',json.dumps([asset['id']]).encode())
    index=next((i for i,t in enumerate(c.tracks) if t['id']==track),len(c.tracks));point=QPoint(round(c.x(frame)+1),c.ruler_height+index*c.row_height+15)
    for event in [QDragEnterEvent(point,Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier),QDragMoveEvent(point,Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier),QDropEvent(QPointF(point),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)]:
        app.sendEvent(c,event);events.append(dict(type=int(event.type()),accepted=event.isAccepted(),target=track,frame=frame));assert event.isAccepted(),events[-1]
    if settle:idle()
def load_source(asset):
    source=w.video_panels.source;before=deepcopy(w.document());program=w.transport_state().get('frame',0);source.load(asset)
    wait(lambda:source.asset is not None and source.asset['sha256']==asset['sha256'] and source.request_id is None and not w.pending and source.future is None and source.next_source is None and source.prepared_asset is None and w.state().get('source',{}).get('document') is not None);idle()
    assert w.document()==before and w.transport_state().get('frame',0)==program
    assert source.asset['kind']=='Video' and source.asset['metadata']['has_audio']
    return source

try:
    video=out/'moving-av.mp4';make_source(video);source=inspect_source(dict(id=new_id(),name='Moving video with audio',path=str(video)),threading.Event())
    assert source['kind']=='Video' and source['metadata']['has_audio'];original_hash=sha(video)
    with av.open(str(video)) as decoder:frames=[f.to_ndarray(format='rgb24') for f in decoder.decode(video=0)]
    assert len(frames)==18 and not np.array_equal(frames[0],frames[-1]);checks.append('Actual encoded video has 18 distinct moving frames and embedded audio; classifier and video decoder succeed')
    shell=Shell(out/'layout.json',out/'owner.log');w=shell.project_workspace;wait(lambda:w.state().get('endpoint'));shell.media_library.assets[source['id']]=dict(id=source['id'],name=source['name'],kind='Video',path=str(video),sha256=source['sha256'],metadata=source['metadata'],status='Ready')
    if expect_bug:
        v,a=setup(2);drop(source,v);result=counts();assert result==dict(video=0,audio=1,visual_plan=0,audio_plan=1),result;cases.append(dict(path='Global Library actual Qt drag/drop',restored_mode='Audio only',target='video',result=result))
        v,a=setup(2);panel=load_source(source);w.timeline.canvas.current_track=v;panel.place();idle();result=counts();assert result==dict(video=0,audio=1,visual_plan=0,audio_plan=1),result;cases.append(dict(path='Source actual load/place',restored_mode='Audio only',target='video',result=result))
        checks.append('BOTH user entry paths naturally reproduce audio-only accepted placement on a VIDEO target with persisted Source mode; source data is not missing')
    else:
        modes=['A/V linked','Video only','Audio only']
        for mode in range(3):
            for target_kind in ('video','audio',None):
                v,a=setup(mode);target={'video':v,'audio':a}.get(target_kind);drop(source,target);result=counts();expected=dict(video=0,audio=1,visual_plan=0,audio_plan=1) if target_kind=='audio' else dict(video=1,audio=1,visual_plan=1,audio_plan=1);assert result==expected,(mode,target_kind,result)
                cases.append(dict(path='Global Library Qt enter/move/drop',restored_source_mode=modes[mode],target=target_kind,result=result))
        checks.append('Nine real Qt Library-drop cases: video/empty targets receive linked A/V independently of restored Source mode; audio targets deliberately extract audio')
        for mode in range(3):
            for target_kind in ('video','audio',None):
                v,a=setup(mode);panel=load_source(source);target={'video':v,'audio':a}.get(target_kind);w.timeline.canvas.current_track=target;before=deepcopy(w.document());bad=(mode==2 and target_kind=='video') or (mode==1 and target_kind=='audio')
                if bad:
                    try:panel.place();raise AssertionError('Contradictory target accepted')
                    except ValueError as exc:assert 'track' in str(exc).lower()
                    idle();assert w.document()==before;result=dict(rejected=True,document_intact=True)
                else:
                    assert modes[mode] in panel.place_button.text();panel.place();idle();result=counts();assert result['video']==(mode!=2) and result['audio']==(mode!=1),(mode,target_kind,result)
                cases.append(dict(path='Source actual load/place',restored_source_mode=modes[mode],target=target_kind,result=result))
        checks.append('Nine Source load/place cases: visible chosen channel intent retained; contradictory single-channel targets reject intact; explicit audio extraction remains available')
        v,a=setup(2);drop(source,v);before=deepcopy(w.document());ids={c['id'] for c in before['clips']};assert len(ids)==2 and len({c['link_id'] for c in before['clips']})==1
        w.submit('undo');idle();assert not w.document()['clips'];w.submit('redo');idle();assert w.document()==before;checks.append('One named atomic linked placement, exact Undo/Redo and stable video/audio IDs')
        saved=out/'portable'/'placed.zwv';w.save(save_as=True,path=str(saved));idle();assert w.last_outcome['status']=='durable';w.open(path=str(saved));idle();d=w.document();assert {c['id'] for c in d['clips']}==ids and counts()['visual_plan']==1 and counts()['audio_plan']==1;assert d['media'][0]['sha256']==original_hash and sha(d['media'][0]['location']['path'])==original_hash;checks.append('Portable Save As/reopen preserves linked IDs, exact counts, visual evaluation and original/managed source identity')
        # Project Media uses the same actual Qt boundary; video-only source stays visual.
        known=deepcopy(d['media'][0]);drop(known,v,30,project=True);assert counts()['video']==2 and counts()['audio']==2;checks.append('Project Media actual Qt drop retains video despite restored Source Audio only')
        noaudio=out/'moving-silent.mp4';make_source(noaudio,False);asset=inspect_source(dict(id=new_id(),name='Video without audio',path=str(noaudio)),threading.Event());shell.media_library.assets[asset['id']]=dict(asset,path=str(noaudio),status='Ready');v,a=setup(2);drop(asset,v);assert counts()==dict(video=1,audio=0,visual_plan=1,audio_plan=0);checks.append('Video without an audio stream remains visible and does not invent an audio clip')
        v,a=setup(1);drop(source,v,settle=False);w.timeline.source_mode.setCurrentIndex(2);w.timeline.canvas.current_track=a;idle();assert counts()['video']==1 and counts()['audio']==1
        v,a=setup(2);panel=load_source(source);w.timeline.canvas.current_track=a;panel.place();panel.channels.setCurrentIndex(0);idle();assert counts()['video']==0 and counts()['audio']==1;checks.append('Pending Library drop and explicit Source extraction pin their original channels/target despite later channel/selection changes')
        v,a=setup(0);w.batch('Lock target',[dict(op='track.edit',id=v,values=dict(locked=True))]);idle();before=deepcopy(w.document());revision=w.state()['revision'];drop(source,v);assert w.document()==before and w.state()['revision']==revision and 'locked' in w.notice.text().lower();checks.append('Locked visual target rejects intact instead of silently falling back to an audio track')
        v,a=setup(2);before=deepcopy(w.document());revision=w.state()['revision'];allow=threading.Event()
        from studio_timeline_media import inspect_all
        def delayed(sources,cancel):
            while not allow.wait(.005):
                if cancel.is_set():raise InterruptedError('Controlled cancelled placement')
            return inspect_all(sources,cancel)
        with patch('studio_timeline_media.inspect_all',side_effect=delayed):
            drop(source,v,settle=False);w.timeline.cancel_placement();allow.set();idle()
        assert w.document()==before and w.state()['revision']==revision;checks.append('Cancelled actual Qt drop retires its preparation worker and accepts no source/clip/history edit')
        w.submit('close',discard=True);idle()
    if expect_bug:w.submit('close',discard=True);idle()
    shell.close();wait(lambda:shell.closing);exit_code=shell.client.process.returncode;assert exit_code==0 and w.exited();shell=None
    errors=out/'qt-errors.log';error_text=errors.read_text(encoding='utf8') if errors.exists() else '';assert not error_text,error_text[-1500:]
    result=dict(status='EXPECTED_BUG_REPRODUCED' if expect_bug else 'PASS',checks=checks,cases=cases,qt_drag_events=events,owner_exit=exit_code,qt_errors=error_text,source_sha256=original_hash,source_unchanged=sha(video)==original_hash,classification=__doc__,native_windows_or_OLE='UNVERIFIED',GPU_or_audio_output=False)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(result['status'],len(checks),'groups',len(cases),'cases')
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
    if shell and not shell.closing:
        shell.client.gui_thread=None;shell.client.close(mode='discard',project_mode='discard');shell.closing=True;shell.close();shell.waveform.close_pool();shell.image_editor.close_resources();shell.media_library.close_resources();shell.operations.shutdown(wait=True)
