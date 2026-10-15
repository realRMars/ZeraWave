"""Frozen project export on one bounded, context-owning disposable process.

The Studio owner pins recipes, reconciles this process's real exit, and permits
later edits. No device output or alternative compositor is involved.
"""
from pathlib import Path
from fractions import Fraction
from copy import deepcopy
import os,sys,json,time,uuid,threading,subprocess,traceback,hashlib
from video_project import validate,duration,sample_at,integer,fail

def atomic_json(path,value,optional=False):
 path=Path(path);temporary=path.with_name('.'+path.name+'.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),'utf8')
 for attempt in range(4):
  try:os.replace(temporary,path);return
  except PermissionError:
   if attempt<3:time.sleep(.005)
   elif not optional:raise
 # Windows readers can temporarily disallow replacement. Progress is a
 # bounded advisory snapshot; keep the previous snapshot instead of failing
 # accepted export work over telemetry. Final result/completion stays strict.

def protect(document,destination,extra=()):
 destination=Path(destination).resolve();sources=[Path(a['location']['path']).resolve() for a in document['media']]
 sources.extend(Path(p).resolve() for p in document['protected_paths']);sources.extend(Path(p).resolve() for a in document['media'] for p in (a.get('provenance',{}).get('import_path'),a.get('provenance',{}).get('original_path')) if p);sources.extend(Path(p).resolve() for p in extra if p)
 for source in sources:
  if os.path.normcase(str(source))==os.path.normcase(str(destination)) or source.exists() and destination.exists() and os.path.samefile(source,destination):fail('protected_source','Export destination is or aliases a source, project or protected output.')
 if destination.suffix.lower()!='.mp4':fail('invalid_destination','Export Video requires an .mp4 destination; Save project uses .zwv.')
 return destination

def export_project(document,epoch,revision,path,crf,folder,cancel,extra=()):
 document=validate(document);integer(crf,0,51);destination=protect(document,path,extra)
 if duration(document)<=0:fail('empty_project','Place timed content before exporting.')
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
 config=dict(document=document,epoch=epoch,revision=revision,path=str(destination),crf=crf,protected_extra=list(extra));(folder/'request.json').write_text(json.dumps(config,ensure_ascii=False),'utf8')
 env=dict(os.environ,QT_QPA_PLATFORM='offscreen');command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',str(folder)]
 with (folder/'worker.stdout').open('wb') as stdout,(folder/'worker.stderr').open('wb') as stderr:
  process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  while process.poll() is None:
   if cancel.wait(.05):(folder/'cancel.flag').touch(exist_ok=True)
 result_path=folder/'RESULT.json'
 if not result_path.exists():fail('export_outcome_unknown','Export worker exited '+str(process.returncode)+' without a receipt. Inspect destination and diagnostics before repeating. Accepted project retained: '+str(folder))
 result=json.loads(result_path.read_text('utf8'))
 if not result.get('ok'):
  error=result['error'];exc=ValueError(error['message']+' Diagnostics: '+str(folder));exc.code=error['code']
  for note in error.get('notes',[]):exc.add_note(note)
  raise exc
 if process.returncode!=0:fail('export_outcome_unknown','Export completion was reported but worker exit was uncertain; inspect destination before repeating: '+str(folder))
 return result['result']

class Cancel:
 def __init__(self,folder):self.path=Path(folder)/'cancel.flag'
 def is_set(self):return self.path.exists()

def check(cancel):
 if cancel.is_set():fail('cancelled','Export cancelled before durable completion. Accepted project and prior good output retained.')

def validate_movie(path,width,height,fps,frames,samples,cancel):
 import av
 counts=dict(video=0,audio=0);first={};last={};streams={}
 for kind in ('video','audio'):
  with av.open(str(path),'r',timeout=(2.,2.)) as container:
   selected=getattr(container.streams,kind)
   if len(selected)!=1:fail('export_validation','Expected one '+kind+' stream.')
   stream=selected[0];streams[kind]=dict(codec=stream.codec_context.name,time_base=str(stream.time_base),duration=stream.duration)
   if kind=='video':
    if stream.codec_context.name!='h264' or (stream.width,stream.height)!=(width,height) or stream.average_rate!=fps:fail('export_validation','Encoded picture settings differ from requested native output.')
   elif stream.codec_context.name!='aac' or stream.codec_context.sample_rate!=48000 or len(stream.codec_context.layout.channels)!=2:fail('export_validation','Encoded audio is not requested48kHz stereo AAC.')
   for frame in container.decode(stream):
    check(cancel)
    if frame.pts is None:fail('export_validation','Encoded media lacks timestamps.')
    stamp=Fraction(frame.pts)*frame.time_base;first.setdefault(kind,stamp)
    if kind=='video':
     if stamp!=Fraction(counts[kind],1)/fps:fail('export_validation','Encoded frame order/timestamps differ from evaluator.')
     counts[kind]+=1
    else:
     if stamp!=Fraction(counts[kind],48000):fail('export_validation','Encoded audio sample order is discontinuous.')
     counts[kind]+=frame.samples
    last[kind]=stamp
 if counts['video']!=frames or not samples<=counts['audio']<samples+1024 or first.get('audio')!=0:fail('export_validation','Encoded duration/counts disagree with frozen project; AAC final padding limited to one frame.')
 return dict(counts=counts,first={k:str(v) for k,v in first.items()},last={k:str(v) for k,v in last.items()},aac_padding_samples=counts['audio']-samples,streams=streams,full_decode=True)

def worker(folder):
 folder=Path(folder);config=json.loads((folder/'request.json').read_text('utf8'));d=validate(config['document']);destination=protect(d,config['path'],config['protected_extra']);cancel=Cancel(folder);staging=None;media=surface=context=window=mixer=container=None;committed=False;primary=None;cleanup=[];result=None;log=None
 try:
  import faulthandler
  faulthandler.enable()
  if os.environ.get('ZERAWAVE_PROJECT_TEST_TRACE')=='1':faulthandler.dump_traceback_later(20,repeat=True)
  atomic_json(folder/'PROGRESS.json',dict(phase='initializing libraries',revision=config['revision']),True)
  import numpy as np,av,glfw,moderngl
  from PySide6.QtWidgets import QApplication
  from project_evaluator import Evaluator
  from project_media import Media
  from project_surface import ProjectSurface
  from project_mixer import Mixer
  atomic_json(folder/'PROGRESS.json',dict(phase='initializing Qt',revision=config['revision']),True)
  app=QApplication.instance() or QApplication([]);check(cancel);e=Evaluator(d,config['epoch'],config['revision']);width,height=d['settings']['width'],d['settings']['height'];fps=Fraction(*d['settings']['fps']);frames=e.end;samples=sample_at(d,frames)
  if width%2 or height%2:fail('export_dimensions','H264 yuv420p requires even output dimensions. Set deliberate project settings before export; no automatic resizing.')
  if width*height>8_000_000:fail('export_capacity','Export readback/encoder staging supports at most8million native pixels; no resolution reduced.')
  atomic_json(folder/'PROGRESS.json',dict(phase='initializing GL',revision=config['revision']),True)
  if not glfw.init():fail('export_context','Existing GLFW context initialization failed.')
  glfw.window_hint(glfw.VISIBLE,False);glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3);glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,3);glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE);window=glfw.create_window(width,height,'ZeraWave project export context',None,None)
  if not window:fail('export_context','Existing hidden native GL context unavailable; prior output retained.')
  glfw.make_context_current(window);context=moderngl.create_context(require=330);atomic_json(folder/'PROGRESS.json',dict(phase='initializing compositor',revision=config['revision']),True);surface=ProjectSurface(context);media=Media();mixer=Mixer();destination.parent.mkdir(parents=True,exist_ok=True);staging=destination.parent/('.'+destination.name+'.export-'+uuid.uuid4().hex+'.mp4')
  container=av.open(str(staging),'w',format='mp4',options={'movflags':'+faststart'});video=container.add_stream(os.environ.get('ZERAWAVE_PROJECT_TEST_EXPORT_ENCODER','libx264'),rate=fps);video.width=width;video.height=height;video.pix_fmt='yuv420p';video.time_base=1/fps;video.codec_context.thread_count=2;video.options={'crf':str(config['crf']),'preset':'veryfast','tune':'zerolatency','bf':'0'}
  audio=container.add_stream('aac',rate=48000);audio.layout='stereo';audio.bit_rate=192000;audio.time_base=Fraction(1,48000);audio.codec_context.thread_count=1
  log=(folder/'frames.jsonl').open('w',encoding='utf8');sample=0;last_report=0.;began=time.perf_counter();peak_pcm=0.;owned_peak=0;preencode_hash=hashlib.sha256();pcm_hash=hashlib.sha256()
  def report(phase,frame):atomic_json(folder/'PROGRESS.json',dict(phase=phase,frame=frame,frames=frames,sample=sample,samples=samples,revision=config['revision'],epoch=config['epoch'],elapsed_seconds=time.perf_counter()-began),True)
  report('rendering',0)
  for frame_number in range(frames):
   check(cancel);barrier=os.environ.get('ZERAWAVE_PROJECT_TEST_EXPORT_BARRIER')
   while barrier and Path(barrier).exists():check(cancel);time.sleep(.02)
   started=time.perf_counter();media.submit(e.at(frame_number))
   while not media.ready():check(cancel);time.sleep(.001)
   prepared=media.take()
   try:
    if prepared.get('error'):fail('export_media',prepared['error'])
    prepared_ms=(time.perf_counter()-started)*1000;render_start=time.perf_counter();surface.render(prepared,None);draw_ms=(time.perf_counter()-render_start)*1000;read_start=time.perf_counter();raw=surface.read();rgb=np.ascontiguousarray(np.frombuffer(raw,np.uint8).reshape(height,width,4)[::-1,:,:3]);preencode_hash.update(rgb);read_ms=(time.perf_counter()-read_start)*1000
    picture=av.VideoFrame.from_ndarray(rgb,format='rgb24');picture.pts=frame_number;picture.time_base=1/fps;encode_start=time.perf_counter()
    for packet in video.encode(picture):container.mux(packet)
    encode_ms=(time.perf_counter()-encode_start)*1000;picture=rgb=raw=None
   finally:media.release(prepared['serial']);prepared=None
   target=sample_at(d,frame_number+1);mix_ms=0.;audio_encode_ms=0.
   while sample<target:
    check(cancel);count=min(2048,target-sample);mix_start=time.perf_counter();pcm=mixer.render(e.audio_span(sample,count),cancel);mix_ms+=(time.perf_counter()-mix_start)*1000;peak_pcm=max(peak_pcm,float(np.max(np.abs(pcm))));pcm_hash.update(pcm)
    if peak_pcm>1.000001:fail('export_clipping','Authored mix exceeds full scale. Adjust track/clip gains before export; accepted work retained, no hidden master change.')
    af=av.AudioFrame.from_ndarray(np.ascontiguousarray(pcm.T),format='fltp',layout='stereo');af.sample_rate=48000;af.pts=sample;af.time_base=Fraction(1,48000);encode_start=time.perf_counter()
    for packet in audio.encode(af):container.mux(packet)
    audio_encode_ms+=(time.perf_counter()-encode_start)*1000;sample+=count;af=pcm=None
   owned_peak=max(owned_peak,mixer.metrics.get('peak_owned_bytes',0));log.write(json.dumps(dict(frame=frame_number,media_ms=prepared_ms,draw_ms=draw_ms,readback_ms=read_ms,video_encode_ms=encode_ms,mix_ms=mix_ms,audio_encode_ms=audio_encode_ms,total_ms=(time.perf_counter()-started)*1000,media=media.metrics,text_cache_bytes=surface.stats.get('text_cache_bytes'),texture_bytes=surface.stats.get('texture_bytes'),pcm_owned=mixer.metrics.get('owned_after_prepare_bytes',0)))+'\n')
   if time.perf_counter()-last_report>.25:report('rendering',frame_number+1);last_report=time.perf_counter()
  check(cancel);report('draining',frames)
  for stream in (video,audio):
   for packet in stream.encode(None):container.mux(packet)
  container.close();container=None;log.flush();log.close();log=None
  with staging.open('r+b') as handle:handle.flush();os.fsync(handle.fileno())
  report('validating',frames);validation=validate_movie(staging,width,height,fps,frames,samples,cancel)
  # Verify all sources again before completion; immutable recipes cannot excuse
  # in-place changed source bytes or aliases created during the job.
  from project_service import digest
  for asset in d['media']:
   if digest(asset['location']['path'],cancel)!=asset['sha256']:fail('changed_media','Source changed during export; previous output retained.')
  check(cancel);protect(d,destination,config['protected_extra']);failure=os.environ.get('ZERAWAVE_PROJECT_TEST_EXPORT_FAILURE')
  if failure=='1' or failure and Path(failure).exists():raise OSError('Controlled export write failure before atomic replacement')
  with staging.open('rb') as handle:encoded_hash=hashlib.file_digest(handle,'sha256').hexdigest()
  result=dict(path=str(destination),revision=config['revision'],epoch=config['epoch'],project=d['id'],sha256=encoded_hash,frames=frames,samples=samples,dimensions=[width,height],fps=[fps.numerator,fps.denominator],crf=config['crf'],preencode_rgb_sha256=preencode_hash.hexdigest(),canonical_pcm_sha256=pcm_hash.hexdigest(),peak_pcm=peak_pcm,validation=validation,seconds=time.perf_counter()-began,pcm_peak_owned_bytes=owned_peak,compositor=surface.stats,graphics_backend=context.info['GL_RENDERER'],codec_versions=av.library_versions,diagnostics=str(folder),frame_timing_log=str(folder/'frames.jsonl'))
  # Retire context/readers before publication; a cleanup failure must leave the
  # prior good output. A cancel after os.replace may not change durable outcome.
 except BaseException as exc:primary=exc;traceback.print_exc()
 finally:
  for name,action in [('encoder',lambda:container.close() if container else None),('timing log',lambda:log.close() if log else None),('mixer',lambda:mixer.close() if mixer else None),('media',lambda:media.close() if media else None),('media join',lambda:media.thread.join() if media else None),('surface',lambda:surface.close() if surface else None),('GL context',lambda:context.release() if context else None),('window',lambda:glfw.destroy_window(window) if window else None),('GLFW',lambda:glfw.terminate() if window else None)]:
   try:action()
   except BaseException as exc:cleanup.append(name+': '+str(exc))
 if primary is None and cleanup:primary=RuntimeError('Export resource retirement failed; prior output retained.');primary.add_note('; '.join(cleanup))
 elif primary is not None:
  for note in cleanup:primary.add_note(note)
 if primary is None:
  try:
   result['retirement']=dict(media=media.metrics,mixer=mixer.metrics,compositor=surface.stats,media_thread_exited=media.exited())
   if not media.exited() or mixer.budget.used or media.planes.used:raise RuntimeError('Export reader resources remain owned after retirement.')
   check(cancel);protect(d,destination,config['protected_extra']);os.replace(staging,destination);committed=True;result['owned_resources_retired']=True;atomic_json(folder/'PROGRESS.json',dict(phase='complete',frame=result['frames'],frames=result['frames'],revision=config['revision']),True);atomic_json(folder/'RESULT.json',dict(ok=True,result=result));return 0
  except BaseException as exc:primary=exc;traceback.print_exc()
 # Retain unpublished partial file/diagnostics, never overwrite or delete a
 # prior good result. Its unique path is returned as recovery evidence.
 if committed:
  # Output already passed decode/fsync and all resources retired. A receipt
  # error cannot become a false export rejection. Keep this durable outcome.
  result['receipt_warning']=str(primary)
  try:atomic_json(folder/'RESULT.json',dict(ok=True,result=result));return 0
  except BaseException:traceback.print_exc();return 3
 error=dict(code=getattr(primary,'code','export_failed'),message=str(primary),notes=getattr(primary,'__notes__',[]),partial=str(staging) if staging else None,committed=committed);atomic_json(folder/'RESULT.json',dict(ok=False,error=error));return 2

if __name__=='__main__':
 sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'audio'))
 if len(sys.argv)==3 and sys.argv[1]=='--worker':sys.exit(worker(sys.argv[2]))
 raise SystemExit('This module is invoked by the authoritative Studio project service.')
