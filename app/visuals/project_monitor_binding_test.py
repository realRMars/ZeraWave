"""Qt controls and real owner context guards; generated fractional native sources."""
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import Future
from fractions import Fraction
import os,sys,json,time,uuid,threading,hashlib,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];os.environ['QT_QPA_PLATFORM']='offscreen';out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
from PySide6.QtWidgets import QApplication,QLabel,QComboBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
from studio_project_controls import MonitorTransport,timecode_frame
from studio_project import ProjectWorkspace
from studio_project_source import SourcePanel
from project_source import prepare_source
from project_service import ProjectService
from project_transport import Transport
import video_project as v
import av,numpy as np
app=QApplication([]);s=ProjectService();uid=lambda:uuid.uuid4().hex;requests=[];checks=[];rows=[];panel=None;control=None
def document(name,fps=[30,1],kind='Image'):
 a,t=uid(),uid();return v.apply(v.create(name,dict(fps=fps)),[dict(op='media.add',id=a,name=name,kind=kind,sha256='a'*64,location=dict(kind='external',path=str(out/(name+'.wav' if kind=='Audio' else name+'.png'))),metadata=dict(duration=12)),dict(op='track.add',id=t,kind='audio' if kind=='Audio' else 'video'),dict(op='clip.add',asset=a,track=t,start=0,duration=300)],uid())[0]
def binding(state=None):
 x=state or s.state();return dict(expected_epoch=x['epoch'],expected_revision=x['revision'],expected_project=x['project_id'],expected_command=x['command_revision'])
def submit(channel,request):
 answer=s.request(request);requests.append(dict(request=request,response=answer));f=Future();f.set_result(answer);return f
try:
 s.document=document('Program A');w=SimpleNamespace(state=s.state,binding=binding,transport_state=s.transport_state,source_transport_state=lambda:s.source.state()['transport'],shell=SimpleNamespace(safe=lambda f:f()),notice=QLabel(),transport_desired=None,transport_future=None,pending=None,client=SimpleNamespace(submit=submit),timeline=SimpleNamespace(source_mode=QComboBox()));w.poll_transport=lambda:ProjectWorkspace.poll_transport(w);w.transport=lambda *a,**k:ProjectWorkspace.transport(w,*a,**k);control=MonitorTransport(w)
 for name,change in [('replacement',True),('same-project FPS/revision',False)]:
  control.refresh();control.show();control.time.setFocus();app.processEvents();QTest.keyClick(control.time,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(control.time,'00:00:03:00');assert control.time.edit_context is not None;count=len(requests)
  if change:s.document=document('Program B',[24,1]);s.epoch=uid();s.revision=0;s.command_revision=0
  else:s.document=v.apply(s.document,[dict(op='project.settings',values=dict(fps=[30000,1001]))],uid())[0];s.revision+=1
  before=deepcopy_clock=s.transport_state()
  try:control.seek_timecode();raise AssertionError('Stale field accepted')
  except ValueError as exc:assert 'context changed' in str(exc)
  assert len(requests)==count and s.transport_state()['frame']==before['frame'] and control.time.isModified() and control.time.text()=='00:00:03:00';control.refresh();assert control.time.text()=='00:00:03:00'
  expected=timecode_frame(control.time.text(),s.document['settings']['fps']);control.seek_timecode();w.poll_transport();assert requests[-1]['response']['ok'] and s.transport_state()['frame']==expected;rows.append(dict(case=name,outcome='rejected stale field, explicit Enter retry uses current nominal NDF',expected_frame=expected,actual_frame=s.transport_state()['frame']))
 checks.append('Program project/epoch/revision/FPS pinned at first text edit; replacement/revision changes reject without submission and retain text; deliberate second Enter uses current context')
 s.source.install(document('Source A',kind='Audio'));panel=SourcePanel(w);panel.install(s.source.state());panel.show();app.processEvents();panel.out_box.setValue(180);panel.in_box.setFocus();QTest.keyClick(panel.in_box,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(panel.in_box,'60');panel.seek_intent=(panel.version,binding());count=len(requests);s.source.install(document('Source B',kind='Audio'));before=s.source.state()['transport'];QTest.keyClick(panel.in_box,Qt.Key_Return);panel.seek_to(40);assert len(requests)==count and s.source.state()['transport']['range_in']==before['range_in'] and s.source.state()['transport']['frame']==before['frame'] and panel.retained_range==[60,180];panel.seek_intent=None
 panel.install(s.source.state());panel.out_box.setFocus();app.processEvents();assert len(requests)==count and panel.retained_range==[60,180] # Enter then blur is still rejected
 panel.mark_range();panel.poll();assert len(requests)==count and panel.retained_range==[60,180]
 panel.retry_range();w.poll_transport();clock=s.source.state()['transport'];assert requests[-1]['response']['ok'] and [clock['range_in'],clock['range_out']]==[60,180];checks.append('Displayed Source epoch/initiating Program binding pin range fields; stale Enter then replacement install/poll and blur submit nothing; only explicit retained-range Apply binds current Source')
 panel.poll();panel.in_box.setFocus();QTest.keyClick(panel.in_box,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(panel.in_box,'70');s.source.install(document('Source C',kind='Audio'));QTest.keyClick(panel.in_box,Qt.Key_Return);assert panel.retained_range is not None;panel.install(s.source.state());panel.poll();count=len(requests);QTest.keyClick(panel.in_box,Qt.Key_A,Qt.ControlModifier);QTest.keyClicks(panel.in_box,'80');assert panel.retained_range is None;QTest.keyClick(panel.in_box,Qt.Key_Return);w.poll_transport();assert len(requests)==count+1 and requests[-1]['response']['ok'] and s.source.state()['transport']['range_in']==80;checks.append('Fresh deliberate Qt text edit after a rejected range starts a new current-Source intent and accepts once; old draft is not automatically repeated')
 # A command legitimately queued behind another GUI operation keeps its old
 # document binding even if replacement happens before actual dispatch.
 w.pending=object();old=binding();count=len(requests);w.transport('seek_paused',2,binding=old);s.epoch=uid();w.pending=None;w.poll_transport();assert len(requests)==count and w.transport_desired is None and w.transport_future is None;w.poll_transport();assert len(requests)==count;checks.append('Unsubmitted delayed GUI transport cancels on known project replacement without dispatch, rebase or duplicate; dispatched stale rejection is covered by real-owner delayed-transport Qt integration')
 for fps in (Fraction(30),Fraction(30000,1001),Fraction(24000,1001)):
  path=out/f'five-{fps.numerator}-{fps.denominator}.mp4'
  with av.open(str(path),'w') as c:
   stream=c.add_stream('libx264',rate=fps);stream.width=16;stream.height=16;stream.pix_fmt='yuv420p';stream.options={'bf':'0','g':'30'}
   for n in range(5):
    f=av.VideoFrame.from_ndarray(np.full((16,16,3),n*40,np.uint8),format='rgb24');f.pts=n;f.time_base=1/fps
    for packet in stream.encode(f):c.mux(packet)
   for packet in stream.encode(None):c.mux(packet)
  with av.open(str(path)) as c:
   stream=c.streams.video[0];actual=list(c.decode(stream));length=Fraction(stream.duration)*stream.time_base;assert len(actual)==5
  asset=dict(id=uid(),name='Five exact frames',kind='Video',location=dict(kind='external',path=str(path)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata={});derived=prepare_source(asset,uid(),threading.Event());meta=derived['media'][0]['metadata'];assert Fraction(*meta['duration_time'])==length and v.duration(derived)==5;clock=Transport();clock.sync(derived,'five',0);clock.command('last');assert clock.frame==4;clock.command('beginning')
  for frame in range(1,5):clock.command('step',1);assert clock.frame==frame
  from project_media import Media
  from project_evaluator import Evaluator
  media=Media()
  try:
   serial=media.submit(Evaluator(derived,'five',0).at(4));deadline=time.monotonic()+10
   while not media.ready() and time.monotonic()<deadline:time.sleep(.002)
   result=media.take();assert result and not result['error'],result
   try:
    image=next(iter(result['images'].values()));level=float(np.frombuffer(image['data'],np.uint8).reshape(-1,4)[:,:3].mean());assert abs(level-160)<8,level
   finally:media.release(serial)
  finally:media.close();media.thread.join(5);assert not media.thread.is_alive()
  rows.append(dict(fps=[fps.numerator,fps.denominator],decoded_frames=5,end=v.duration(derived),last=4,last_frame_mean_rgb=level,exact_duration=meta['duration_time'],sha256=asset['sha256']))
 checks.append('Actual five-frame CFR video at30/1,30000/1001,24000/1001 retains exact container duration and exposes all five frames through last/step; no float-floor loss or blanket ceil policy')
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,rows=rows,requests=requests,limits='VFR remains complete nominal Source grid over exact container duration; no decoded-frame-index mapping or audible/display claim'),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,rows=rows,requests=requests,clock=s.transport_state()),indent=2),encoding='utf8');raise
finally:
 if panel:panel.close_resources();panel.close()
 if control:control.close()
 s.shutdown();app.processEvents()
