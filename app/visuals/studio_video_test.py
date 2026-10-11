"""Real isolated Studio/owner; continuous gesture observations, exact publication waits, Qt pointer/button/key/wheel input and accepted raster/save flow."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,time,json,uuid,traceback,hashlib
ROOT=Path(r'C:\ZeraWave');out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'))
(out/'artwork').mkdir()
from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog
from PySide6.QtCore import Qt,QEvent,QPoint,QPointF
from PySide6.QtGui import QImage,QMouseEvent,QWheelEvent,QColor
from PySide6.QtTest import QTest
import studio_qt
original=studio_qt.Shell.error
def error(self,*a,**k):
    with patch.object(studio_qt,'ROOT',out):return original(self,*a,**k)
studio_qt.Shell.error=error;app=QApplication([]);shell=studio_qt.Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=shell.image_editor;checks=[];report=dict(evidence=__doc__,checks=checks)
def pump(t=.015):
    end=time.perf_counter()+t
    while time.perf_counter()<end:app.processEvents();time.sleep(.001)
def wait(fn,timeout=20):
    end=time.perf_counter()+timeout
    while time.perf_counter()<end:
        pump()
        if fn():return
    raise AssertionError('Timeout: '+e.status.text())
def idle():wait(lambda:not e.art_jobs and not e.edit_jobs and not e.await_recovery and e.binding==(shell.client.snapshot['media_control']['session'],shell.client.snapshot['media_control']['revision']))
def pixels(im):
    owned=im.convertToFormat(QImage.Format_RGBA8888)
    return bytes(owned.constBits())
def transport(identity,op,value=None):shell.client.request('media_transport',media_session=e.binding[0],layer=identity,op=op,value=value)
def saved(path):
    sid=uuid.uuid4().hex;shell.client.request('save',save_id=sid,path=str(path));wait(lambda:any(s['id']==sid and s['status']=='durable' for s in shell.client.snapshot['media_control']['raster']['saves']))

def settled():
    wait(lambda:not e.video.pending and (e.video.future is None or e.video.future.done()))
    idle()
def displayed(identity):
    state=shell.client.snapshot['media_frames'].get(identity,{})
    shown=getattr(e,'media_presented',{}).get(identity,{})
    return shown if shown.get('generation')==state.get('generation') and not state.get('seek_pending') else None
def wheel(widget,count,control=False):
    p=QPointF(widget.rect().center());event=QWheelEvent(p,widget.mapToGlobal(p.toPoint()),QPoint(),QPoint(0,120*count),Qt.NoButton,Qt.ControlModifier if control else Qt.NoModifier,Qt.NoScrollPhase,False);app.sendEvent(widget,event)

def click(button):
    assert button.isVisible(),button.text()
    QTest.mouseClick(button,Qt.LeftButton);pump(.03)
def key_value(widget,value):
    widget.setFocus();QTest.keyClick(widget,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(widget,str(value));QTest.keyClick(widget,Qt.Key_Return);pump(.03)
def seek_point(fraction):
    return QPoint(round(8+fraction*(v.seek.width()-16)),v.seek.height()//2)
def drag_seek(fractions):
    QTest.mousePress(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(fractions[0]));pump(.12);observed=[];endpoints=[]
    for fraction in fractions[1:]:
        QTest.mouseMove(v.seek,seek_point(fraction));until=time.perf_counter()+.16
        while time.perf_counter()<until:
            pump(.012);shown=displayed(video)
            if shown:
                point=dict(pts=shown['pts'],pixels=hashlib.sha256(pixels(e.images[video])).hexdigest(),wall=time.perf_counter(),move_fraction=fraction)
                if not observed or (point['pts'],point['pixels'])!=(observed[-1]['pts'],observed[-1]['pixels']):observed.append(point)
        shown=displayed(video)
        if shown:endpoints.append(dict(pts=shown['pts'],pixels=hashlib.sha256(pixels(e.images[video])).hexdigest()))
    report.setdefault('drag_sampling',[]).append(dict(pattern=fractions,move_seconds=.16,continuous=observed,endpoints=endpoints))
    target=v.seek.value()/10000*v.source_duration();QTest.mouseRelease(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(fractions[-1]));settled();wait(lambda:displayed(video));return target,observed

try:
    wait(lambda:shell.client and not shell.client.snapshot['media_library']['loading']);shell.panels['composition'].toggleView(True);shell.panels['composition'].setAsCurrentTab();shell.panels['image_layers'].toggleView(True);shell.panels['image_layers'].setAsCurrentTab();e.resize_canvas((320,180),False);idle()
    from media_foundation_test import fixture
    source=fixture(out);shell.client.request('media_import',paths=[str(source)]);wait(lambda:len(shell.client.snapshot['media_library']['assets'])==1 and not shell.client.snapshot['media_library']['pending']);asset=shell.client.snapshot['media_library']['assets'][0];e.add_asset(asset,kind='Video');idle();video=e.selected;wait(lambda:displayed(video));v=e.video
    assert v.bar.isVisible() and e.editor_view.toolBarArea(v.bar)==Qt.BottomToolBarArea
    report['initial_toolbar']=dict(size=[v.width(),v.height()],source_duration=v.source_duration(),label=v.info.text());assert 'source 8.000 s' in v.info.text() and 'source fps' in v.info.text()
    e.brush_color=QColor('#ca231f');e.secondary_color=QColor('#2a69bd');colors=(e.brush_color.name(),e.secondary_color.name());brush=deepcopy(e.brush)
    v.show_settings('Range');assert v.stack.currentWidget()==v.panel and v.groups['Range'].isVisible();e.choose_tool(e.canvas.tool);assert v.stack.currentWidget()==v.colors and not v.settings;assert colors==(e.brush_color.name(),e.secondary_color.name()) and e.brush==brush
    checks.append('Selected bottom toolbar and shared resizable/scroll sidebar; same-tool click restores drawing panel without changing colors/preferences')
    # Dispatch actual Qt pointer events at observed widget geometry.
    target,observed=drag_seek((.2,.7,.35,.6,.25));assert len({r['pts'] for r in observed})>=3 and len({r['pixels'] for r in observed})>=3,observed
    assert displayed(video)['pts']<=target+1e-6 and target-displayed(video)['pts']<1/24+1e-6
    assert not shell.client.snapshot['media_frames'][video]['playing'];report['pointer_scrub']=dict(target=target,observed=observed,final=displayed(video))
    checks.append('Qt press/move/release in both directions changes actual displayed pixels during drag; latest final floor frame wins while paused')
    click(v.buttons['play']);settled();wait(lambda:shell.client.snapshot['media_frames'][video]['playing']);target,playing_observed=drag_seek((.3,.8,.4,.7));wait(lambda:shell.client.snapshot['media_frames'][video]['playing'] and displayed(video));report['playing_pointer_scrub']=playing_observed
    assert len({r['pts'] for r in playing_observed})>=2;click(v.buttons['pause']);settled();wait(lambda:not shell.client.snapshot['media_frames'][video]['playing'])
    QTest.mousePress(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.45));QTest.mouseMove(v.seek,seek_point(.32));click(v.buttons['pause']);QTest.mouseRelease(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.32));settled();wait(lambda:displayed(video));assert not shell.client.snapshot['media_frames'][video]['playing']
    QTest.mousePress(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.6));click(v.buttons['stop']);QTest.mouseRelease(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.6));settled();wait(lambda:displayed(video));assert displayed(video)['pts']==0 and shell.client.snapshot['media_frames'][video]['state']=='stopped'
    v.queue('scrub',dict(position=2.5,final=True,resume=False));settled();wait(lambda:displayed(video) and displayed(video)['pts']==2.5)
    wheel(v.seek,1,True);settled();wait(lambda:displayed(video) and abs(displayed(video)['pts']-(2.5+1/24))<1e-6);wheel(v.seek,-1,True);settled();wait(lambda:displayed(video) and displayed(video)['pts']==2.5)
    wheel(v.seek,1);settled();wait(lambda:displayed(video) and displayed(video)['pts']==3.5);click(v.buttons['previous']);settled();wait(lambda:displayed(video) and abs(displayed(video)['pts']-(3.5-1/24))<1e-6);click(v.buttons['next']);settled();wait(lambda:displayed(video) and displayed(video)['pts']==3.5)
    checks.append('Final-publication resume, explicit Pause override, wheel +1 second, Ctrl wheel exact source frames, frame arrows pause')
    cycle=[]
    for direction in (-1,-1,-1,-1,-1,-1,1,1):
        click(v.buttons['reverse' if direction<0 else 'forward']);settled();cycle.append((e.selected_row()['media']['direction'],e.selected_row()['media']['rate']))
    assert cycle==[(-1,1.),(-1,2.),(-1,4.),(-1,6.),(-1,8.),(-1,1.),(1,1.),(1,2.)],cycle
    forward_clicks=[]
    for expected in (4.,6.,8.,1.):
        click(v.buttons['forward']);settled();forward_clicks.append(e.selected_row()['media']['rate']);assert e.selected_row()['media']['rate']==expected
    report['complete_forward_clicks']=forward_clicks
    click(v.buttons['rate']);key_value(v.rate,12.);settled();assert e.selected_row()['media']['rate']==12.
    click(v.buttons['range']);key_value(v.in_point,1.125);settled();key_value(v.out_point,4.875);settled();valid=deepcopy(e.selected_row()['media']);key_value(v.in_point,5.);assert e.selected_row()['media']==valid;v.show_settings('Range');v.in_point.clearFocus();v.out_point.clearFocus();v.sync();wheel(v.in_point,1,True);pump(.3);settled();assert abs(e.selected_row()['media']['start']-1.126)<1e-7
    fine=deepcopy(e.selected_row()['media']);click(e.undo);idle();wait(lambda:e.selected_row()['media']==valid);click(e.redo);idle();wait(lambda:e.selected_row()['media']==fine)
    auto_button=next(b for b in v.panel.findChildren(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton) if b.text()=='Out: automatic source end');click(auto_button);settled();v.sync();assert 'Automatic source end: 8.000 s'==v.auto.text() and v.out_point.value()==8.
    checks.append('Separate direction cycles/reset, exact 12x, fine Ctrl range wheel, invalid In retains valid range, automatic source Out')
    # Selection override also cancels remembered resume on the old source.
    v.queue('scrub',dict(position=2.,final=True,resume=True));e.blank_layer();idle();paint=e.selected;settled();assert not v.bar.isVisible();wait(lambda:not shell.client.snapshot['media_frames'][video]['playing'])
    e.select(video);idle();wait(lambda:displayed(video));assert v.bar.isVisible();
    with patch.object(QMessageBox,'information',return_value=QMessageBox.Ok),patch('artwork_save_ui.SaveOptions',side_effect=AssertionError('Video Save entered still-image dialog')):
        e.artwork_save.save(True,ids=[video]);assert 'OPEN' in e.status.text()
    checks.append('Selection cancels remembered resume; video Save explicitly OPEN and cannot enter image formats')
    e.select(paint);e.blank_child();idle();child=e.selected;e.blank_child();idle();grand=e.selected
    before=deepcopy(e.config);e.select(child);click(e.order_up);idle();wait(lambda:e.config==before) # only child: boundary
    e.select(paint);e.blank_child();idle();second=e.selected;before=deepcopy(e.config);e.select(child);click(e.order_up);idle();assert e.selected_row()['parent']==paint and next(r for r in e.config['layers'] if r['id']==grand)['parent']==child
    after=deepcopy(e.config);assert before!=after;click(e.undo);idle();wait(lambda:e.config==before);click(e.redo);idle();wait(lambda:e.config==after)
    click(e.order_down);idle();wait(lambda:e.config==before);click(e.undo);idle();wait(lambda:e.config==after);click(e.redo);idle();wait(lambda:e.config==before)
    checks.append('Complete forward Qt button cycle and actual sibling Down/Undo/Redo preserve subtree and branch')
    e.select(video);v.edit({'direction':-1,'rate':6.,'start':1.25,'end':4.75,'loop':'Ping-pong'},'Video reopen fixture');settled();config=deepcopy(e.config);saved(out/'finishing-session.json');old_session=e.binding[0];shell.client.request('load',path=str(out/'finishing-session.json'));e.refresh(True);idle();wait(lambda:not shell.client.snapshot['media_library']['pending']);assert e.config['layers']==config['layers'] and e.config['canvas']==config['canvas'] and e.config['editor']==config['editor'];assert not shell.client.snapshot['media_frames'][video]['playing'];e.select(video);wait(lambda:displayed(video));settled();pump(.1)
    try:shell.client.request('media_transport',media_session=old_session,layer=video,op='play');raise AssertionError('Obsolete command accepted')
    except ValueError as exc:assert 'obsolete' in str(exc)
    pump(.1);assert not shell.errors,shell.errors;shell.panels['composition'].setAsCurrentTab();pump(.1);shell.composition_editor.grab().save(str(out/'studio-bottom-toolbar.png'))
    checks.append('Selected accessible sibling ordering carries grandchildren; boundaries add no operation; owner Undo/Redo and video direction/range/order durable session reopen without autoplay')
    # A second selected video cannot receive queued work from the first.
    import shutil
    second_path=out/'second-source.mp4';shutil.copy2(source,second_path);shell.client.request('media_import',paths=[str(second_path)]);wait(lambda:len(shell.client.snapshot['media_library']['assets'])>=2 and not shell.client.snapshot['media_library']['pending']);asset2=next(a for a in shell.client.snapshot['media_library']['assets'] if a['path']==str(second_path));e.add_asset(asset2,kind='Video');idle();video2=e.selected;wait(lambda:displayed(video2));QTest.mousePress(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.5));e.select(video);QTest.mouseRelease(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.5));settled();wait(lambda:not shell.client.snapshot['media_frames'][video2]['playing']);assert v.binding[1]==video;v.queue('scrub',dict(position=2.,final=True,resume=False));settled();wait(lambda:displayed(video) and displayed(video)['pts']==2.)
    checks.append('Two imported sources: selection changes supersede live intent, preserve old paused source and bind final displayed frame to selected video')
    # A Video source with actual irregular PTS exercises the same input widgets.
    from fractions import Fraction
    import av,numpy as np
    vfr_path=out/'irregular-source.mkv';native_pts=[0.,.08,.21,.43,.69,1.07,1.5]
    with av.open(str(vfr_path),'w') as container:
        stream=container.add_stream('ffv1',rate=24);stream.width=160;stream.height=90;stream.pix_fmt='bgra';stream.time_base=Fraction(1,1000);stream.codec_context.time_base=Fraction(1,1000)
        for i,pts in enumerate(native_pts):
            data=np.zeros((90,160,4),np.uint8);data[:]=[i*31,i*19,255-i*29,255];frame=av.VideoFrame.from_ndarray(data,format='rgba');frame.pts=round(pts*1000);frame.time_base=Fraction(1,1000)
            for packet in stream.encode(frame):container.mux(packet)
        for packet in stream.encode():container.mux(packet)
    with av.open(str(vfr_path)) as container:actual_pts=[float(frame.pts*frame.time_base) for frame in container.decode(video=0)]
    assert actual_pts==native_pts,actual_pts
    shell.client.request('media_import',paths=[str(vfr_path)]);wait(lambda:any(a['path']==str(vfr_path) and a['status']=='Ready' for a in shell.client.snapshot['media_library']['assets']))
    vfr_asset=next(a for a in shell.client.snapshot['media_library']['assets'] if a['path']==str(vfr_path));e.add_asset(vfr_asset,kind='Video');idle();vfr_video=e.selected;wait(lambda:displayed(vfr_video));observed=[displayed(vfr_video)['pts']]
    for expected in actual_pts[1:4]:
        click(v.buttons['next']);settled();wait(lambda:displayed(vfr_video) and displayed(vfr_video)['pts']==expected);observed.append(displayed(vfr_video)['pts'])
    wheel(v.seek,-1,True);settled();wait(lambda:displayed(vfr_video) and displayed(vfr_video)['pts']==.21);click(v.buttons['previous']);settled();wait(lambda:displayed(vfr_video) and displayed(vfr_video)['pts']==.08)
    report['vfr_input']=dict(path=str(vfr_path),sha256=hashlib.sha256(vfr_path.read_bytes()).hexdigest(),actual_pts=actual_pts,button_pts=observed)
    checks.append('Actual Qt previous/next clicks and Ctrl wheel select adjacent irregular source PTS, independent of source nominal FPS')
    click(v.buttons['play']);settled();QTest.mousePress(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.6));QTest.mouseMove(v.seek,seek_point(.2));pump(.08)
    replacement=out/'replacement-source.mp4';shutil.copy2(source,replacement);old_source=v.binding[2]
    shell.client.request('media_action',op='relink',asset=vfr_asset['id'],path=str(replacement));wait(lambda:v.binding and v.binding[2]!=old_source and not shell.client.snapshot['media_library']['pending']);QTest.mouseRelease(v.seek,Qt.LeftButton,Qt.NoModifier,seek_point(.2));settled();wait(lambda:displayed(vfr_video));assert not shell.client.snapshot['media_frames'][vfr_video]['playing']
    assert not v.pending and not v.scrub;click(v.buttons['stop']);settled();wait(lambda:displayed(vfr_video) and displayed(vfr_video)['pts']==0.)
    checks.append('Source replacement during a dispatched drag cancels obsolete final seek/resume; Stop publishes the replacement In frame')
    saved(out/'close-secured.json');report['result']='PASS'
except Exception:
    report['result']='FAIL';report['failure']=traceback.format_exc();report['failure_state']=dict(status=e.status.text(),selected=e.selected,config=e.config,snapshot=shell.client.snapshot);print(report['failure'],flush=True)
finally:
    (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Save),patch.object(QFileDialog,'getSaveFileName',return_value=(str(out/'normal-close-session.json'),'Session (*.json)')):
        shell.close();wait(lambda:getattr(shell,'closing',False))
    report['owner_exit']=shell.client.process.poll();report['errors']=list(shell.errors);(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert report['result']=='PASS',report.get('failure');assert report['owner_exit']==0 and not report['errors'],report;print('PASS',out,checks,flush=True)
