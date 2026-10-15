"""Actual GL renderer adapter fidelity/cost; hidden window, no scanout/audio claim."""
from pathlib import Path
from copy import deepcopy
import sys,os,uuid,time,json,hashlib,threading,traceback,importlib.util
from fractions import Fraction
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
from video_project import create,apply,layout_defaults
from project_evaluator import Evaluator
from project_media import Media
from project_surface import ProjectSurface,ReferenceSurface,TargetContext,scene_for
from media_registry import inspect
import numpy as np,glfw,moderngl
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);window=None;ctx=None;surface=None;baseline=None;m=None;checks=[];samples=[];differences=[]
def stats(a):
 a=np.asarray(a,float);return dict(n=len(a),median=float(np.median(a)),p95=float(np.percentile(a,95)),p99=float(np.percentile(a,99)),maximum=float(a.max()),over_50ms=int(sum(a>50)))
try:
 w,h=96,64;x,y=np.meshgrid(np.arange(w),np.arange(h));rgba=np.stack([(x*2)%256,(y*3)%256,(x+y)%256,np.full_like(x,255)],axis=2).astype(np.uint8);file=out/'native-pattern.png';assert QImage(rgba.tobytes(),w,h,QImage.Format_RGBA8888).save(str(file));meta=inspect(str(file),threading.Event())['metadata'];a,t,c=[uuid.uuid4().hex for _ in range(3)];d=create('GPU fixture',dict(width=1280,height=720));d=apply(d,[dict(op='media.add',id=a,name='Pattern',kind='Image',location=dict(kind='external',path=str(file)),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),metadata=meta),dict(op='track.add',id=t,kind='video'),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=60,layout=dict(layout_defaults(),bounds=[.1,.12,.65,.63],fit='Fit',opacity=.73,rotation=8))],uuid.uuid4().hex)[0]
 assert glfw.init();glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3);glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3);glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE);glfw.window_hint(glfw.VISIBLE,False);window=glfw.create_window(1280,720,'ZeraWave bounded project GPU fixture',None,None);assert window;glfw.make_context_current(window);ctx=moderngl.create_context(require=330);surface=ProjectSurface(ctx);m=Media();e=Evaluator(d,'gpu',1);m.submit(e.at(15));end=time.perf_counter()+10
 while m.ready() is None and time.perf_counter()<end:time.sleep(.002)
 r=m.take();assert not r['error'];surface.render(r,None);candidate=np.frombuffer(surface.read(),np.uint8).reshape(720,1280,4)[::-1].copy()
 # Load the captured A compositor source, sharing its unchanged composition,
 # decoder/native helpers. Exact source copy defines the comparison baseline.
 baseline_path=Path(sys.argv[2]);spec=importlib.util.spec_from_file_location('editor_previous_image_layers',baseline_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);adapter=TargetContext(ctx);bt=ctx.texture((1280,720),4);bf=ctx.framebuffer(color_attachments=(bt,));adapter.screen=bf;baseline=module.ImageLayers(adapter,surface.host.vertices);scene,_=scene_for(r);refs=[]
 for asset in scene['assets']:
  row=dict(asset,status='Ready',metadata=meta);refs.append(row)
 baseline.request(dict(scene,assets=refs),1,'matched-project');end=time.perf_counter()+10
 while baseline.pending and time.perf_counter()<end:baseline.poll();time.sleep(.002)
 assert not baseline.error,baseline.error;bf.clear(0,0,0,1);baseline.draw((1280,720));before=np.frombuffer(bf.read(components=4,alignment=1),np.uint8).reshape(720,1280,4)[::-1].copy();assert np.array_equal(before,candidate),int(np.abs(before.astype(int)-candidate).max());checks.append('Exact native-byte parity with captured pre-B ImageLayers shader/compositor at 1280x720, rotation8/Fit/opacity0.73; authored pixels preserved')
 for mode in ('Normal','Multiply','Screen','Add','Difference'):
  for stage in (baseline,surface.layers):stage.config['layers'][0]['blend']=mode
  baseline.geometry_key=None;surface.layers.geometry_key=None;bf.clear(0,0,0,1);baseline.draw((1280,720));surface.render(r,None);before=bf.read(components=4,alignment=1);after=surface.read();assert before==after,mode
 checks.append('All existing blend modes preserve exact captured-compositor native output at brightness1')
 # Restore the document's Normal recipe, then compare a colour operation to
 # the supported CPU reference. The two resamplers have separate known phases;
 # report full raw errors rather than inventing bit equality for scaled pixels.
 r['plan']['revision']=2;r['plan']['visual'][0]['clip']['layout']['brightness']=.24;surface.render(r,None);gpu=np.frombuffer(surface.read(),np.uint8).reshape(720,1280,4)[::-1].copy();reference=ReferenceSurface();image=reference.render(r).convertToFormat(QImage.Format_RGBA8888_Premultiplied);cpu=np.frombuffer(image.constBits(),np.uint8).reshape(720,image.bytesPerLine())[:,:1280*4].reshape(720,1280,4).copy();delta=np.abs(gpu.astype(np.int16)-cpu.astype(np.int16));differences.append(dict(case='rotation8/Fit/opacity0.73/brightness0.24',mean=float(delta.mean()),p99=float(np.percentile(delta,99)),maximum=int(delta.max()),different_pixels=int(np.count_nonzero(np.any(delta,axis=2)))));assert delta[:,:,3].max()==0 and float(delta.mean())<1.5,differences
 QImage(gpu.tobytes(),1280,720,QImage.Format_RGBA8888_Premultiplied).save(str(out/'gpu-brightness.png'));image.save(str(out/'cpu-brightness.png'));reference.close();checks.append('Native-resolution brightness modifies RGB only; opaque output alpha matches CPU reference; scaled/filter error distribution and images retained')
 # Matched warmed CPU submission and isolated GPU queries, no swap/readback in
 # measured calls. Decode/import/startup happened outside these distributions.
 r['plan']['revision']=3;r['plan']['visual'][0]['clip']['layout']['brightness']=1.;surface.render(r,None);baseline.config['layers'][0]['blend']='Normal';surface.layers.config['layers'][0]['blend']='Normal'
 for i in range(80):
  for arm in ('captured-compositor','project-adapter'):
   began=time.perf_counter()
   with ctx.query(time=True) as query:
    if arm=='captured-compositor':bf.clear(0,0,0,1);baseline.draw((1280,720))
    else:surface.render(r,None)
   cpu_ms=(time.perf_counter()-began)*1000;gpu_ms=query.elapsed/1000000
   if i>=20:samples.append(dict(arm=arm,cpu_call_ms=cpu_ms,gpu_query_ms=gpu_ms))
 report=dict(result='PASS',checks=checks,differences=differences,samples=samples,summaries={arm:{key:stats([s[key] for s in samples if s['arm']==arm]) for key in ('cpu_call_ms','gpu_query_ms')} for arm in ('captured-compositor','project-adapter')},conditions=dict(gpu=ctx.info['GL_RENDERER'],framebuffer=[1280,720],native_source=[96,64],output=[1280,720],hidden_glfw=True,swaps=0,readback='fidelity only, outside timing',clock='fixed project frame15',baseline_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),classification=__doc__),resources=surface.stats)
 m.release(r['serial']);m.close();m.thread.join(5);assert m.exited();m=None;baseline.close();baseline=None;bf.release();bt.release();surface.close();surface=None;(out/'RESULT.json').write_text(json.dumps(report,indent=2));print('PASS',len(checks),report['conditions']['gpu'])
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc());raise
finally:
 if m:
  if m.leased:m.release(m.leased['serial'])
  m.close();m.thread.join(5)
 if baseline:baseline.close()
 if surface:surface.close()
 if ctx:ctx.release()
 if window:glfw.destroy_window(window)
 glfw.terminate()
