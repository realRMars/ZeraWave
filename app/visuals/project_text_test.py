"""Text/native GPU+CPU composition, immutable recipes, import and recovery checks."""
from pathlib import Path
import sys,os,json,time,uuid,threading,hashlib,traceback
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage
import numpy as np,glfw,moderngl
from video_project import create,apply,style_defaults,ProjectError
from project_evaluator import Evaluator
from project_text import TextSurface,parse_srt
from project_surface import ProjectSurface,ReferenceSurface
from project_service import ProjectService,read_project
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);checks=[];window=None;context=None;surface=None;reference=None;service=None
def frame(e,f):return dict(plan=e.at(f),images={},error=None)
def req(op,**values):
 s=service.state();r=service.request(dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**values));key=r.get('outcome',{}).get('id');end=time.monotonic()+10
 while key and service.outcomes[key]['status'] in ('preparing','saving') and time.monotonic()<end:service.poll();time.sleep(.002)
 return service.outcomes[key] if key else r
try:
 t,c,title,progress=[uuid.uuid4().hex for _ in range(4)];d=create('Editable text fixture',dict(width=320,height=180));style=dict(style_defaults(),size=20,padding=4,bounds=[.05,.15,.9,.7],background='#cc17120e',stroke_width=1,stroke_color='#30221b',max_lines=4)
 d=apply(d,[dict(op='track.add',id=t,kind='graphics'),dict(op='caption.add',id=c,track=t,start=1,duration=59,text='Café — 日本語\nالعربية 🎮 editable',style=style),dict(op='graphic.add',id=title,track=t,start=0,duration=60,text='{elapsed} / {duration}',dynamic='counter',range_start=0,range_end=60,style=dict(style_defaults(),size=14,padding=2,bounds=[.05,.01,.9,.14],background='#00000000')),dict(op='graphic.add',id=progress,track=t,start=0,duration=60,text='',dynamic='progress',style=dict(style_defaults(),bounds=[0,.94,1,.04],padding=0,background='#ff211d18',color='#ff40c8b0'))],uuid.uuid4().hex)[0];e=Evaluator(d,'text',1);r=frame(e,30);before=json.dumps(r,sort_keys=True);text=TextSurface();augmented=text.augment(r);assert json.dumps(r,sort_keys=True)==before and len(augmented['plan']['visual'])==3;assert all(np.frombuffer(i['data'],np.uint8).reshape(-1,4)[:,:3].max(axis=1).max()<=255 for i in augmented['images'].values());text.close();checks.append('Immutable timed recipes materialize native Unicode/wrapped text, counter and progress without document/history mutation')
 assert c not in {v['clip']['id'] for v in TextSurface().augment(frame(e,0))['plan']['visual']};assert not TextSurface().augment(frame(e,60))['plan']['visual'];checks.append('Caption start and exclusive end follow the shared evaluator; counter/progress use exact frame ranges')
 reference=ReferenceSurface();image=reference.render(r).convertToFormat(QImage.Format_RGBA8888_Premultiplied);cpu=np.frombuffer(image.constBits(),np.uint8).reshape(180,image.bytesPerLine())[:,:1280].reshape(180,320,4).copy();assert image.save(str(out/'cpu-text.png'))
 assert glfw.init();glfw.window_hint(glfw.VISIBLE,False);glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3);glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3);glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE);window=glfw.create_window(320,180,'ZeraWave text fixture',None,None);assert window;glfw.make_context_current(window);context=moderngl.create_context(require=330);surface=ProjectSurface(context);surface.render(r,None);gpu=np.frombuffer(surface.read(),np.uint8).reshape(180,320,4)[::-1].copy();delta=np.abs(cpu.astype(int)-gpu.astype(int));assert delta.mean()<2 and np.percentile(delta,99)<8 and np.max(delta[:,:,3])==0,(delta.mean(),np.percentile(delta,99),delta.max());QImage(gpu.tobytes(),320,180,QImage.Format_RGBA8888_Premultiplied).save(str(out/'gpu-text.png'));comparison=dict(mean=float(delta.mean()),p99=float(np.percentile(delta,99)),maximum=int(delta.max()),gpu=context.info['GL_RENDERER'],size=[320,180]);checks.append('Existing GPU compositor and Qt reference render identical text recipes with declared filtering distribution and exact opaque alpha')
 again=surface.text.bytes;surface.render(r,None);assert surface.text.bytes==again;changed=apply(d,[dict(op='caption.edit',id=c,values={'text':'Corrected caption with preserved ID','style':{'color':'#ffd6f8'}})],uuid.uuid4().hex)[0];surface.render(frame(Evaluator(changed,'text',2),30),None);assert surface.read()!=gpu[::-1].tobytes();checks.append('Revision/style correction changes visible pixels; repeated text preparation reuses bounded cache')
 surface.text.limit=8
 try:surface.render(frame(e,15),None);raise AssertionError('Text pressure accepted')
 except MemoryError:pass
 surface.text.limit=64*1024*1024;surface.render(r,None);assert surface.read()==gpu[::-1].tobytes();checks.append('Controlled text byte pressure reports rejection; same context recovers exact pixels without changing accepted recipes/history')
 file=out/'input.srt';file.write_text('1\n00:00:00,001 --> 00:00:00,100\nFirst café\n\n2\n00:00:01,000 --> 00:00:02,000\nSecond line\n日本語\n','utf8');parsed=parse_srt(file,t,[30,1],uuid.uuid4().hex,threading.Event());assert parsed[1]['start']==1 and parsed[1]['duration']==2 and parsed[2]['text']=='Second line\n日本語';checks.append('Actual UTF-8 SRT import retains cue text/provenance and ceil/ceil output-frame boundary mapping')
 service=ProjectService();assert req('new')['status']=='accepted';assert req('batch',changes=[dict(op='track.add',id=t,kind='graphics')])['status']=='accepted';old=service.document;result=req('import_captions',path=str(file),track=t);assert result['status']=='accepted',result;imported=json.loads(json.dumps(service.document));assert len(imported['captions'])==2 and str(file) in imported['protected_paths'];assert req('undo')['status']=='accepted' and service.document==old;assert req('redo')['status']=='accepted' and service.document==imported;assert req('save',path=str(out/'captions.zwv'))['status']=='durable';opened,revision,media,path=read_project(out/'captions.zwv',threading.Event());assert opened==imported;checks.append('Owner-backed SRT import is one named atomic history operation; exact Undo/Redo and protected Save/reopen retain editable text/styles/IDs')
 file.write_text('bad cue','utf8');saved=service.document;failed=req('import_captions',path=str(file),track=t);assert failed['status']=='failed' and service.document==saved;checks.append('Malformed import fails before acceptance, retaining current document, history and prior good project')
 bad=frame(e,30);next(v for v in bad['plan']['text'] if v['recipe']['id']==c)['recipe']['style']['max_lines']=1
 try:TextSurface().augment(bad);raise AssertionError('Text silently truncated')
 except ValueError:pass
 checks.append('Text overflow is explicit rather than dropping authored characters')
 samples=[]
 for i in range(80):
  a=time.perf_counter();surface.render(r,None);ms=(time.perf_counter()-a)*1000
  if i>=20:samples.append(ms)
 resources=dict(surface.stats);surface.close();surface=None;reference.close();reference=None;service.shutdown();service=None
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,comparison=comparison,resources=resources,samples=samples,median=float(np.median(samples)),p95=float(np.percentile(samples,95)),maximum=max(samples),classification=__doc__),indent=2),'utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if surface:surface.close()
 if reference:reference.close()
 if service:
  while service.jobs:service.poll();time.sleep(.002)
  service.shutdown()
 if context:context.release()
 if window:glfw.destroy_window(window)
 glfw.terminate()
