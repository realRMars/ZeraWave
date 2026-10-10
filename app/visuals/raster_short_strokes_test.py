"""Natural short-stroke regression through scripted Qt and a real owner.

Usage: project python -B raster_short_strokes_test.py NEW_OUTPUT SIZE COUNT TOOL [rapid]
No injected write fault or worker barrier. Each stroke presses, moves briefly,
releases and clicks again; rapid does not wait for owner/PNG acknowledgement.
Optional test environment: ZERAWAVE_NATURAL_GAP (seconds), STORE_COPY (prefix
ZERAWAVE_NATURAL_), SAVE_RECOVERY=1, UNDO=1, RESUMED_COUNT. Use only disposable
copies/new destinations. Output binds actual source/native/harness identities,
raw events, accepted state, rejection disposition, PNG/recovery and exact reopen.
Passing recovery allows explicit bounded rejection; report its count and reason.
This is scripted native-pixel evidence, not physical pointer/user acceptance.
"""
from pathlib import Path
from copy import deepcopy
import sys,os,time,json,hashlib,traceback
ROOT=Path(os.environ.get('ZERAWAVE_PROBE_ROOT',str(Path(__file__).resolve().parents[2])));sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);size=int(sys.argv[2]);count=int(sys.argv[3]);tool=sys.argv[4];rapid=len(sys.argv)>5 and sys.argv[5]=='rapid'
import faulthandler
stacks=(out/'stacks.log').open('w');faulthandler.dump_traceback_later(20,repeat=True,file=stacks)
if os.environ.get('ZERAWAVE_NATURAL_STORE_COPY'):
 import shutil
 shutil.copytree(os.environ['ZERAWAVE_NATURAL_STORE_COPY'],out/'artwork')
os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'))
for name in ('ZERAWAVE_RASTER_TEST_BARRIER','ZERAWAVE_RASTER_TEST_FAIL_WRITE','ZERAWAVE_CONTROL_TEST_DROP_ACK'):os.environ.pop(name,None)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import studio_qt
from unittest.mock import patch
error=studio_qt.Shell.error
def isolated_error(self,*args,**kwargs):
 with patch.object(studio_qt,'ROOT',out):return error(self,*args,**kwargs)
studio_qt.Shell.error=isolated_error
from native_raster import backend
(out/'harness-used.py').write_bytes(Path(__file__).read_bytes())
app=QApplication([]);shell=studio_qt.Shell(out/'layout.json',out/'owner.log');shell.resize(1440,900);shell.show();e=None;samples=[];states=[];result={};started=time.perf_counter()
(out/'source-binding.json').write_text(json.dumps(dict(root=str(ROOT),dimensions=[size,size],tool=tool,rapid=rapid,gap_seconds=float(os.environ.get('ZERAWAVE_NATURAL_GAP','.005')),harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),native=backend().status(),native_sha256=hashlib.sha256(Path(backend().path).read_bytes()).hexdigest() if backend().available else None,files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app/visuals').glob('*.py')},store_copy=os.environ.get('ZERAWAVE_NATURAL_STORE_COPY')),indent=2),'utf8')
def pump(t=.001):
 end=time.perf_counter()+t
 while time.perf_counter()<end:app.processEvents();time.sleep(.0005)
def wait(fn,t=40):
 end=time.perf_counter()+t
 while time.perf_counter()<end:
  pump()
  if fn():return
 raise RuntimeError('Timeout '+(e.status.text() if e else 'startup'))
def idle():wait(lambda:not e.edit_jobs and not e.art_jobs)
def pixels():return e.canvas.source_image(e.selected_row())
def digest(im):
 converted=im.convertToFormat(QImage.Format_RGBA8888_Premultiplied)
 return hashlib.sha256(bytes(converted.constBits())).hexdigest()
def state(label):
 s=dict(label=label,elapsed=time.perf_counter()-started,status=e.status.text(),binding=e.binding,owner=deepcopy(shell.client.snapshot['media_control']),snapshot_bytes=len(json.dumps(shell.client.snapshot,separators=(',',':')).encode()),native=backend().core.stats() if backend().core else {},conditions=dict(scene=deepcopy(e.config),canvas_viewport=[e.canvas.width(),e.canvas.height()],zoom=e.canvas.zoom,dpr=e.canvas.devicePixelRatioF(),screen=[app.primaryScreen().size().width(),app.primaryScreen().size().height()],refresh_hz=app.primaryScreen().refreshRate(),output=shell.client.snapshot.get('preview',{})))
 states.append(s);(out/'states.json').write_text(json.dumps(states,indent=2),'utf8');return s
def stroke(tool,i):
 if e.canvas.tool!=tool:e.choose_tool(tool)
 c=e.canvas;r=e.selected_row();a=c.screen_point(r,(.1+(i%20)*.037,.25+(i//20%8)*.06));b=c.screen_point(r,(.12+(i%20)*.037,.27+(i//20%8)*.06));before=e.binding[1];asset=r['asset'];began=time.perf_counter()
 if tool=='Brush':e.brush_color=QColor.fromHsv((i*37)%360,180,210)
 QTest.mousePress(c,Qt.LeftButton,pos=a.toPoint());pressed=time.perf_counter();prepared=bool(c.stroke);press_status=e.status.text()
 QTest.mouseMove(c,b.toPoint(),delay=0);moved=time.perf_counter();QTest.mouseRelease(c,Qt.LeftButton,pos=b.toPoint());released=time.perf_counter()
 if rapid:pump(float(os.environ.get('ZERAWAVE_NATURAL_GAP','.005')))
 else:idle()
 done=time.perf_counter()
 s=dict(index=i,tool=tool,prepared=prepared,press_status=press_status,press_ms=(pressed-began)*1000,move_ms=(moved-pressed)*1000,release_ms=(released-moved)*1000,ack_ms=(done-released)*1000,total_ms=(done-began)*1000,revision_before=before,revision_after=e.binding[1],asset_changed=asset!=e.selected_row()['asset'],status=e.status.text(),pending=shell.client.snapshot['media_control']['raster']['pending'])
 samples.append(s)
 if i%10==0:print(json.dumps(s),flush=True);(out/'samples.json').write_text(json.dumps(samples,indent=2),'utf8')
 return s
try:
 wait(lambda:hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor
 shell.panels['composition'].toggleView(True);shell.panels['image_layers'].toggleView(True)
 e.resize_canvas((size,size),False);e.blank_layer();idle();wait(lambda:pixels() is not None);e.editor_view.fit();pump(.1)
 seed=QImage(size,size,QImage.Format_ARGB32_Premultiplied);seed.fill(QColor('#345be2'))
 from PySide6.QtGui import QPainter
 p=QPainter(seed)
 for x in range(0,size,32):p.fillRect(x,0,16,size,QColor('#fbd035'))
 p.end();e.save_paint(dict(row=e.selected,asset=e.selected_row()['asset'],target=deepcopy(e.selected_row()),session=e.binding[0],revision=e.binding[1],tool='Brush',base=pixels()),seed);idle();target=e.selected;state('start')
 for i in range(count):
  s=stroke(tool,i)
  if i%10==0:state('stroke-'+str(i))
  if 'rejected' in s['status'].lower() or 'Stroke not started:' in s['status'] or shell.errors:result['first_failure']=s;print('Failure '+json.dumps(s),flush=True);break
 idle();state('stroke_end');result['accepted_hash_before_pause']=digest(pixels());result['strokes_attempted']=len(samples)
 if os.environ.get('ZERAWAVE_NATURAL_UNDO'):
  accepted=digest(pixels());e.history(False,'drawing');idle();undo=digest(pixels());e.history(True,'drawing');idle();assert digest(pixels())==accepted and undo!=accepted;result['undo_redo_exact']=True;state('natural_pending_undo_redo')
 pause_start=time.perf_counter();pump(30);result['pause_seconds']=time.perf_counter()-pause_start;state('after_30_seconds')
 e.retry_saving();pump(2);idle();state('retry');result['accepted_hash_after_retry']=digest(pixels())
 if os.environ.get('ZERAWAVE_NATURAL_AFTER_DRAIN'):
  for i in range(count,count+int(os.environ['ZERAWAVE_NATURAL_AFTER_DRAIN'])):
   s=stroke(tool,i)
   if 'rejected' in s['status'].lower():result['post_drain_failure']=s;print('Post-drain failure '+json.dumps(s),flush=True);break
  state('more_short_strokes_after_drain')
 if os.environ.get('ZERAWAVE_NATURAL_SAVE_RECOVERY'):
  accepted_hash=digest(pixels());requested=e.binding[1];save=out/'recovery-save-as.json';shell.client.request('save',path=str(save));wait(lambda:any(s['status']=='durable' and s['revision']==requested for s in shell.client.snapshot['media_control']['raster']['saves']));state('recovery_save_durable');assert digest(pixels())==accepted_hash
  wait(lambda:not shell.client.snapshot['media_control']['raster']['failures'] and not shell.client.snapshot['media_control']['raster']['pending']);result['recovery_exact']=True
 if os.environ.get('ZERAWAVE_NATURAL_RESUMED_COUNT'):
  rejected_before={r['id'] for r in shell.client.snapshot['media_control']['transactions'] if r['status']=='rejected'};resumed_rejected=set();resumed_blocked=0
  for i in range(int(os.environ['ZERAWAVE_NATURAL_RESUMED_COUNT'])):
   item=stroke('Brush',count+i+1);resumed_blocked+=not item['prepared']
   resumed_rejected.update(r['id'] for r in shell.client.snapshot['media_control']['transactions'] if r['status']=='rejected' and r['id'] not in rejected_before)
  idle();resumed_rejected.update(r['id'] for r in shell.client.snapshot['media_control']['transactions'] if r['status']=='rejected' and r['id'] not in rejected_before)
  result['resumed_rejections']=len(resumed_rejected);result['resumed_blocked_presses']=resumed_blocked;state('resumed_short_brushes')
 result['after_retry_stroke']=stroke('Brush',count+1);state('subsequent_drawing')
 idle();state('before_layer_creation_drain');wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0);state('layer_creation_quiescent')
 original_count=len(e.config['layers']);e.blank_layer();idle();result['blank_created']=len(e.config['layers'])==original_count+1
 e.select(target);e.blank_child();idle();result['child_created']=len(e.config['layers'])==original_count+2;state('blank_child')
 e.select(target);wait(lambda:pixels() is not None);saved_hash=digest(pixels());requested=e.binding[1];save=out/'save-as.json';shell.client.request('save',path=str(save));wait(lambda:any(s['status']=='durable' and s['revision']==requested for s in shell.client.snapshot['media_control']['raster']['saves']));state('save_durable')
 shell.client.request('load',path=str(save));e.refresh(True);e.select(target);wait(lambda:pixels() is not None);result['reopen_exact']=digest(pixels())==saved_hash;state('reopened')
 result['saved_hash']=saved_hash;result['errors']=list(shell.errors)
except BaseException:result['exception']=traceback.format_exc();print(result['exception'],flush=True)
finally:
 if (out/'last-owner-snapshot.json').exists():
  try:
   observed=json.loads((out/'last-owner-snapshot.json').read_text('utf8'))['snapshot'];values=deepcopy(observed['values']);records={r['id']:r for r in observed['media_library']['resources']}
   from raster_resources import image as observer_image
   for ref in values['media']['assets']:
    row=records.get(ref['id'])
    if row and row.get('runtime'):
     target=out/'preserved-owner-accepted'/('asset-'+ref['id']+'.png');target.parent.mkdir(exist_ok=True);assert observer_image(row['runtime'],native=False).save(str(target));ref['path']=str(target.resolve())
   (out/'preserved-owner-accepted.json').write_text(json.dumps(dict(version=5,**values),indent=2),'utf8')
  except Exception:(out/'owner-preservation-error.txt').write_text(traceback.format_exc(),'utf8')
 (out/'samples.json').write_text(json.dumps(samples,indent=2),'utf8');(out/'result.json').write_text(json.dumps(result,indent=2),'utf8')
 if e:
  # Preserve GUI-known accepted pixels independently if protocol publication fails.
  try:
   from raster_resources import image,snapshot,release
   desc,lease=snapshot(pixels())
   try:assert image(desc,native=False).save(str(out/'last-gui-accepted.png'))
   finally:release(lease)
   (out/'last-gui-scene.json').write_text(json.dumps(e.config,indent=2),'utf8')
  except Exception:(out/'preservation-error.txt').write_text(traceback.format_exc(),'utf8')
 shell.client.close(force=True);shell.closing=True
 if e:e.close_resources()
 shell.media_library.close_resources();shell.waveform.close_pool();shell.operations.shutdown(wait=False,cancel_futures=True)
 shell.close();app.processEvents();faulthandler.cancel_dump_traceback_later();stacks.close();print(json.dumps(dict(out=str(out),result=result)),flush=True)

if result.get('exception') or not all(result.get(k) for k in ('blank_created','child_created','reopen_exact')):
 raise SystemExit(1)
