"""Standalone rational/decoder/resource checks; no physical/audio acceptance."""
from pathlib import Path
from fractions import Fraction
from copy import deepcopy
import sys,os,time,uuid,json,hashlib,traceback,threading
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
app=QApplication([])
from video_project import create,apply,sample_at,ProjectError
from project_evaluator import Evaluator
from project_media import Media,source_metadata
from project_transport import Transport
from project_surface import ReferenceSurface
from media_registry import inspect
import av,numpy as np
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[];samples=[];m=None
def change(d,rows):return apply(d,rows,uuid.uuid4().hex)[0]
def demand(m,e,f):
 began=time.perf_counter();serial=m.submit(e.at(f));end=began+15
 while m.ready() is None and time.perf_counter()<end:time.sleep(.002)
 result=m.take();assert result and result['serial']==serial and not result['error'],result;samples.append(dict(frame=f,ms=(time.perf_counter()-began)*1000,metrics=deepcopy(m.metrics)));return result
def make_video(path,offset,vfr):
 with av.open(str(path),'w',options={'avoid_negative_ts':'disabled'}) as c:
  stream=c.add_stream('ffv1',rate=10);stream.width=96;stream.height=64;stream.pix_fmt='yuv420p';stream.time_base=Fraction(1,1000)
  for i in range(12):
   frame=av.VideoFrame.from_ndarray(np.full((64,96,3),(i*17)%255,np.uint8),format='rgb24');frame.time_base=Fraction(1,1000);frame.pts=offset+i*100+(i//3)*100 if vfr else offset+i*100
   for packet in stream.encode(frame):c.mux(packet)
  for packet in stream.encode():c.mux(packet)
def doc(path):
 meta=inspect(str(path),threading.Event())['metadata'];meta.update(source_metadata(path,threading.Event()));a,t,c=[uuid.uuid4().hex for _ in range(3)];d=create('Timestamp fixture');d=change(d,[dict(op='media.add',id=a,name=path.name,kind='Video',location=dict(kind='external',path=str(path.resolve())),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=meta),dict(op='track.add',id=t,kind='video'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=int(Fraction(str(meta['duration']))*30))]);return d,a,t,c
try:
 cfr=out/'cfr.mkv';vfr=out/'offset-vfr.mkv';make_video(cfr,0,False);make_video(vfr,5000,True);signed=out/'signed-vfr.mkv';make_video(signed,-500,True)
 for path in (cfr,vfr,signed):
  d,a,t,c=doc(path);e=Evaluator(d,'fixture',4);m=Media()
  with av.open(str(path)) as native:pts=[Fraction(f.pts)*f.time_base for f in native.decode(video=0)]
  start=Fraction(*d['media'][0]['metadata']['source_start']);assert start==pts[0],(start,pts)
  for f in (0,1,4,9,17,e.end-1):
   if f>=e.end:continue
   r=demand(m,e,f);image=r['images'][c];target=start+Fraction(f,30);expected=max((p for p in pts if p<=target),default=pts[0]);assert abs(image['pts']-float(expected))<1e-8,(path,f,image['pts'],expected,pts);assert (image['width'],image['height'])==(96,64);assert len(image['data'])==96*64*4
   m.release(r['serial']);r=None
  checks.append('Native CFR/offset-VFR preceding PTS, exact source start, native pixels, first/last project frames: '+path.name)
  r=demand(m,e,e.end);assert not r['images'] and m.metrics['decoders']==0 and m.metrics['plane_bytes']==0;m.release(r['serial']);m.close();m.thread.join(5);assert m.exited() and m.metrics['rgba_bytes']==0;m=None
 checks.append('End-exclusive gap retires all actual decoder planes/conversions; close waits for real worker exit')
 from media_frames import DecoderWindow
 legacy=DecoderWindow(signed,24576,source_timestamps=True);assert legacy.codec_threads==legacy.stream.codec_context.thread_count==2;legacy.close()
 for bad in (0,5,True,'4'):
  try:DecoderWindow(signed,24576,codec_threads=bad);raise AssertionError('Unbounded codec policy admitted')
  except ValueError:pass
 decoder=DecoderWindow(signed,24576,source_timestamps=True,codec_threads=4);cancel=threading.Event()
 try:
  decoder.get(.9,cancel);pts,_=decoder.get(-.4,cancel);assert pts==-.4 and decoder.seek_count==2 and decoder.stream.codec_context.thread_count==decoder.codec_threads==4
 finally:decoder.close()
 checks.append('Signed backwards PTS cache miss rewinds refused-negative-seek demuxer within existing GOP/cache bounds')
 # Actual encoded stream SAR and display matrix, not a metadata-only fixture.
 import subprocess
 ffmpeg=Path(r'C:\Program Files\Streamlabs OBS\resources\app.asar.unpacked\node_modules\obs-studio-node\ffmpeg.exe')
 base=out/'sar.mp4';rotated=out/'rotated.mp4'
 with av.open(str(base),'w') as container:
  stream=container.add_stream('libx264',rate=10);stream.width=96;stream.height=64;stream.pix_fmt='yuv420p';stream.sample_aspect_ratio=Fraction(2);stream.codec_context.sample_aspect_ratio=Fraction(2)
  for i in range(4):
   pixels=np.zeros((64,96,3),np.uint8);pixels[:32,:48,0]=255;pixels[32:,48:,1]=255
   frame=av.VideoFrame.from_ndarray(pixels,format='rgb24')
   for packet in stream.encode(frame):container.mux(packet)
  for packet in stream.encode():container.mux(packet)
 run=subprocess.run([str(ffmpeg),'-v','error','-display_rotation:v:0','90','-i',str(base),'-c','copy',str(rotated)],capture_output=True);assert run.returncode==0,run.stderr
 d,a,t,c=doc(rotated);assert d['media'][0]['metadata']['rotation'] in (90,270),d['media'][0]['metadata'];m=Media();r=demand(m,Evaluator(d,'orientation',1),0);image=r['images'][c];assert (image['width'],image['height'])==(64,96) and abs(image['pixel_aspect']-.5)<1e-8
 with av.open(str(rotated)) as container:
  native=next(container.decode(video=0));rotation=int(native.rotation)%360;expected=np.rot90(native.to_ndarray(format='rgba'),-rotation//90)[::-1].copy()
 assert image['data']==expected.tobytes();m.release(r['serial']);r=None;m.close();m.thread.join(5);assert m.exited();m=None
 checks.append('Actual MP4 display-matrix orientation and SAR invert after native rotation; published RGBA matches decoded source byte-exactly')

 d,a,t,c=doc(cfr);d=change(d,[dict(op='clip.add',asset=a,track=t,start=0,duration=15,name='Same source clock'),dict(op='clip.add',asset=a,track=t,start=0,duration=15,source_in=[1,10],name='Different source clock')]);m=Media();e=Evaluator(d,'overlap',1);r=demand(m,e,1);assert len(r['images'])==3 and m.metrics['decoders']==2
 try:m.submit(e.at(2));raise AssertionError('Reader was disposed')
 except RuntimeError:pass
 m.release(r['serial']);r=None
 for frame in range(40):m.submit(e.at(min(frame,e.end)))
 end=time.perf_counter()+10
 while m.ready() is None and time.perf_counter()<end:time.sleep(.002)
 r=m.take();assert r['serial']==m.serial and r['plan']['frame']==e.end and not r['images'];m.release(r['serial']);m.close();m.thread.join(5);assert m.exited();m=None
 checks.append('Overlapping equal source clocks share one decoder; independent offsets use distinct windows; latest of 40 seeks wins; live reader blocks replacement')
 d,a,t,c=doc(cfr);d['clips']=[];d=change(d,[dict(op='clip.add',asset=a,track=t,start=i*30,duration=30,name='Shot '+str(i)) for i in range(50)]);m=Media();e=Evaluator(d,'fifty',1)
 for f in (0,299,600,1201,1499):
  r=demand(m,e,f);assert len(r['images'])==1 and m.metrics['decoders']==1 and m.metrics['plane_bytes']<=96*1024*1024 and m.metrics['rgba_bytes']<=128*1024*1024;m.release(r['serial']);r=None
 m.close();m.thread.join(5);assert m.exited();m=None;checks.append('50 timeline shots retain only their active decoder and bounded planes/RGBA; separate bin/clip/active counts')
 d,a,t,c=doc(cfr);e=Evaluator(d,'reference',1);m=Media();r=demand(m,e,4);reference=ReferenceSurface();image=reference.render(r);assert (image.width(),image.height())==(1280,720) and image.pixelColor(640,360).alpha()==255;assert image.save(str(out/'reference.png'));m.release(r['serial']);reference.close();m.close();m.thread.join(5);m=None
 checks.append('Existing Qt CPU projection renders native authored dimensions from the identical evaluated spatial recipe')
 clock=[1000000000];transport=Transport(lambda:clock[0]);transport.sync(d,'clock',1);transport.command('play');clock[0]+=100000000;assert transport.position()==3;transport.command('seek',5);clock[0]+=33333334;assert transport.position()==6;transport.command('pause');clock[0]+=1000000000;assert transport.position()==6;transport.command('stop');assert not transport.active and transport.position()==0
 fractional=create(settings=dict(fps=[30000,1001]));assert sample_at(fractional,107892)==172799827 and sample_at(fractional,1078920)==1727998272
 checks.append('Absolute rational frame/sample mapping and injectable monotonic clock; seek anchors, pause holds, stop releases legacy clock ownership')
 clock=[0];transport=Transport(lambda:clock[0]);transport.sync(d,'clock-phase',1);transport.command('play');clock[0]+=29000000;transport.sync(d,'clock-phase',2);clock[0]+=29000000;assert transport.position()==1;transport.sync(d,'replacement-epoch',2);assert not transport.playing and not transport.active and transport.position()==0
 checks.append('Ordinary revisions preserve subframe clock phase; project replacement epoch resets ephemeral playback even when project ID matches')
 bad=deepcopy(d);bad['clips'][0]['layout']['masks']=[dict(mode='Keep',enabled=True,points=[[0,0],[1,1],[0,1],[1,0]])]
 try:Evaluator(bad,'bad',1);raise AssertionError('Invalid crossing mask admitted')
 except (ProjectError,ValueError):pass
 checks.append('Existing mask contract rejects crossing/degenerate recipes before acceptance')
 # Valid source identity with deliberately oversized simultaneous native work:
 # reject before codec allocation, then recover in the SAME running worker.
 d,a,t,c=doc(cfr);e=Evaluator(d,'pressure',1);m=Media();plan=e.at(0);plan['visual'][0]['asset']['metadata'].update(width=8192,height=1024);other=deepcopy(plan['visual'][0]);other['clip']['id']=uuid.uuid4().hex;other['clip']['source_in']=[1,10];other['source_time']=[1,10];plan['visual'].append(other);serial=m.submit(plan);end=time.perf_counter()+10
 while m.ready() is None and time.perf_counter()<end:time.sleep(.002)
 r=m.take();assert r and '128 MiB' in r['error'] and not r['images'];m.release(serial);r=demand(m,e,0);assert r['images'];m.release(r['serial']);m.close();m.thread.join(5);assert m.exited() and m.metrics['rgba_bytes']==0 and m.metrics['plane_bytes']==0;m=None
 checks.append('Controlled native-snapshot pressure rejects before allocation; same worker resumes valid native drawing demand and releases resources after quiescence')
 changed=out/'changed-copy.mkv';changed.write_bytes(cfr.read_bytes());d,a,t,c=doc(changed);e=Evaluator(d,'changed',1);m=Media();r=demand(m,e,0);m.release(r['serial']);r=None;changed.write_bytes(changed.read_bytes()+b'changed');serial=m.submit(e.at(1));end=time.perf_counter()+10
 while m.ready() is None and time.perf_counter()<end:time.sleep(.002)
 r=m.take();assert r and 'source changed' in r['error'].lower() and not r['images'];m.release(serial);m.close();m.thread.join(5);assert m.exited();m=None
 checks.append('Actual changed-source copy is refused by hash/stat validation; no stale prepared pixels returned, accepted recipe retained')
 # High source brightness is applied to unassociated colour and clamped before
 # repremultiplication, so alpha is not accidentally amplified.
 from PySide6.QtGui import QImage,QColor
 alpha=out/'alpha.png';image=QImage(16,16,QImage.Format_ARGB32_Premultiplied);image.fill(QColor(200,100,50,128));assert image.save(str(alpha));meta=inspect(str(alpha),threading.Event())['metadata'];a,t,c=[uuid.uuid4().hex for _ in range(3)];d=create();d=change(d,[dict(op='media.add',id=a,name='Alpha',kind='Image',location=dict(kind='external',path=str(alpha)),sha256=hashlib.sha256(alpha.read_bytes()).hexdigest(),metadata=meta),dict(op='track.add',id=t,kind='video'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=30)]);d=change(d,[dict(op='clip.layout',id=c,values=dict(brightness=4.))]);m=Media();r=demand(m,Evaluator(d,'alpha',1),0);reference=ReferenceSurface();pixel=reference.render(r).pixelColor(640,360);assert (pixel.red(),pixel.green(),pixel.blue(),pixel.alpha())==(128,128,100,255),(pixel.red(),pixel.green(),pixel.blue(),pixel.alpha());reference.close();assert reference.stats['cache_bytes']==0 and reference.stats['scratch_bytes']==0;m.release(r['serial']);r=None;m.close();m.thread.join(5);assert m.exited();m=None
 checks.append('Supported CPU native alpha/brightness4 reference preserves opacity and clamps unassociated source colour; projection caches release truthfully')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,samples=samples,classification=__doc__,fixtures={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (cfr,vfr,signed)}),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if m:
  if m.leased:m.release(m.leased['serial'])
  m.close();m.thread.join(5)
