"""Actual export/evaluator parity and native codec faults; hiddenGL, no scanout."""
from pathlib import Path
import sys,os,json,time,uuid,threading,hashlib,subprocess,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')];os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
import numpy as np,av,glfw,moderngl
from video_project import create,apply,sample_at
from project_service import prepare_changes
from project_evaluator import Evaluator
from project_media import Media
from project_surface import ProjectSurface
from project_export import export_project
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);checks=[];cancel=threading.Event();m=None;surface=None;ctx=None;window=None
source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('app/audio','app/visuals') for p in (ROOT/folder).glob('*.py')};(out/'SOURCE.json').write_text(json.dumps(source,indent=2),'utf8')
try:
 source_video=out/'moving.mp4';c=av.open(str(source_video),'w');stream=c.add_stream('libx264',rate=30);stream.width=320;stream.height=180;stream.pix_fmt='yuv420p';stream.options={'crf':'12','bf':'0'}
 for frame in range(90):
  pixels=np.full((180,320,3),(frame*2%256,48,128),np.uint8);pixels[30:150,frame%180:frame%180+100]=[230,175,32];v=av.VideoFrame.from_ndarray(pixels,format='rgb24');v.pts=frame
  for packet in stream.encode(v):c.mux(packet)
 for packet in stream.encode(None):c.mux(packet)
 c.close();a,t,g,clip,caption=[uuid.uuid4().hex for _ in range(5)];changes=prepare_changes([dict(op='media.add',id=a,name='Moving source',kind='Video',location=dict(kind='external',path=str(source_video))),dict(op='track.add',id=t,kind='video'),dict(op='track.add',id=g,kind='graphics',order=1),dict(op='clip.add',id=clip,asset=a,track=t,start=0,duration=90,layout=dict(opacity=.9,brightness=.8)),dict(op='caption.add',id=caption,track=g,start=15,duration=60,text='Exact café\nshared evaluator',style=dict(bounds=[.027,.80,.946,.16],size=27))],None,cancel);d=apply(create('Native export parity'),changes,uuid.uuid4().hex)[0];e=Evaluator(d,'parity',7)
 assert glfw.init();glfw.window_hint(glfw.VISIBLE,False);glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3);glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3);glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE);window=glfw.create_window(1280,720,'ZeraWave export parity',None,None);glfw.make_context_current(window);ctx=moderngl.create_context(require=330);surface=ProjectSurface(ctx);m=Media();reference={};rgb_hash=hashlib.sha256()
 for frame in range(90):
  m.submit(e.at(frame));deadline=time.perf_counter()+15
  while not m.ready() and time.perf_counter()<deadline:time.sleep(.001)
  r=m.take();assert r and not r['error'],r
  try:
   surface.render(r,None);rgb=np.ascontiguousarray(np.frombuffer(surface.read(),np.uint8).reshape(720,1280,4)[::-1,:,:3]);rgb_hash.update(rgb)
   if frame in (0,14,15,44,74,75,89):reference[frame]=rgb.copy();QImage(rgb.tobytes(),1280,720,QImage.Format_RGB888).save(str(out/f'preencode-{frame}.png'))
  finally:m.release(r['serial'])
 surface.close();surface=None;m.close();m.thread.join();m=None;ctx.release();ctx=None;glfw.destroy_window(window);window=None;glfw.terminate()
 result=export_project(d,'parity',7,str(out/'native.mp4'),18,out/'job',cancel);assert result['preencode_rgb_sha256']==rgb_hash.hexdigest(),(rgb_hash.hexdigest(),result['preencode_rgb_sha256']);errors=[]
 with av.open(str(out/'native.mp4')) as container:
  for i,frame in enumerate(container.decode(video=0)):
   if i in reference:
    decoded=frame.to_ndarray(format='rgb24');delta=abs(decoded.astype(np.int16)-reference[i].astype(np.int16));row=dict(frame=i,mean=float(delta.mean()),p99=float(np.percentile(delta,99)),maximum=int(delta.max()));errors.append(row);assert row['mean']<2.5 and row['p99']<20,row;QImage(decoded.tobytes(),1280,720,QImage.Format_RGB888).save(str(out/f'encoded-{i}.png'))
 checks.append('90 native1280x720 H264/AAC frames use byte-exact independent preview evaluator/GL RGB hash; first/last/caption boundaries and lossy pixel distributions retained')
 # Rational 30000/1001 audio endpoint, explicit no downsample/odd-size rejection.
 ntsc=apply(d,[dict(op='clip.trim',id=clip,end=89),dict(op='project.settings',values=dict(fps=[30000,1001],width=384,height=216)),dict(op='caption.remove',id=caption)],uuid.uuid4().hex)[0];r=export_project(ntsc,'ntsc',8,str(out/'ntsc.mp4'),20,out/'ntsc-job',cancel);assert r['samples']==sample_at(ntsc,89) and r['fps']==[30000,1001];checks.append('Actual NTSC30000/1001 encode timestamps and48k endpoints retain exact absolute frame/sample mapping')
 prior=hashlib.sha256((out/'native.mp4').read_bytes()).hexdigest();os.environ['ZERAWAVE_PROJECT_TEST_EXPORT_ENCODER']='definitely_missing_h264_encoder'
 try:export_project(d,'parity',7,str(out/'native.mp4'),18,out/'failed-encoder',cancel)
 except ValueError:pass
 else:raise AssertionError('Unavailable codec accepted')
 os.environ.pop('ZERAWAVE_PROJECT_TEST_EXPORT_ENCODER');assert hashlib.sha256((out/'native.mp4').read_bytes()).hexdigest()==prior
 odd=apply(d,[dict(op='project.settings',values=dict(width=1279))],uuid.uuid4().hex)[0]
 try:export_project(odd,'odd',9,str(out/'odd.mp4'),18,out/'odd-job',cancel)
 except ValueError as exc:assert exc.code=='export_dimensions'
 else:raise AssertionError('Odd width silently resized')
 assert not (out/'odd.mp4').exists();checks.append('Actual missing codec configuration fails/retains good movie; odd native dimensions reject explicitly without silent resizing')
 assert all(hashlib.sha256((ROOT/r).read_bytes()).hexdigest()==v for r,v in source.items());(out/'RESULT.json').write_text(json.dumps(dict(result='PASS',checks=checks,export=result,lossy=errors,ntsc=r,source_unchanged=True),indent=2),'utf8');print(json.dumps(dict(result='PASS',checks=len(checks),folder=str(out))))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if surface:surface.close()
 if m:m.close();m.thread.join()
 if ctx:ctx.release()
 if window:glfw.destroy_window(window);glfw.terminate()
