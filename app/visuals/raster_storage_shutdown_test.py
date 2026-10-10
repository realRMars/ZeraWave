"""Pass 1 standalone storage and normal-exit cases; isolated new destinations only.

Usage: project python -B raster_storage_shutdown_test.py NEW_OUTPUT [case]
The parent observes child OS exit; no forced finalizer counts as success.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import os,sys,json,time,threading,hashlib,subprocess,traceback,shutil
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]

def unit(out):
 from artwork_store import Store,HEADROOM,write_json
 from concurrent.futures import CancelledError
 checks=[];folder=out/'unit-store';store=Store(folder);data=b'fixture PNG accounting'
 target=folder/'owned.png';assert store.write(target,data,'working');assert not store.write(target,data,'working')
 assert store.state()['files']==1 and store.state()['written_bytes']==len(data)
 legacy=folder/'original.png';legacy.write_bytes(b'library original');store.last_scan=0
 for _ in range(4):store.reconcile(1)
 assert store.state()['files']==2
 store.retire(target)
 with patch.object(Path,'unlink',side_effect=PermissionError('Controlled cleanup denial')):assert store.reclaim()
 assert target.exists() and store.state()['files']==2
 assert not store.reclaim([str(target)]);assert target.exists()
 assert not store.reclaim();assert not target.exists() and legacy.exists()
 check=store.state();assert check['files']==1 and check['reclaimed_bytes']==len(data)
 checks.append('Deduplicated counters, failed/held cleanup, retirement and conservative legacy preservation')
 with patch('artwork_store.shutil.disk_usage',return_value=shutil._ntuple_diskusage(HEADROOM+2,0,HEADROOM+2)):
  try:store.write(folder/'no-space.png',b'abcd');raise AssertionError('Space safeguard ignored')
  except OSError as exc:assert 'physical disk space' in str(exc)
 assert not (folder/'no-space.png').exists() and not store.state()['reserved_bytes']
 checks.append('Controlled real-disk-full response preserves originals and has no ghost reservation')
 # A failed replacement plus denied temporary cleanup preserves the primary
 # failure and journal reservation. Once deletion works, Retry in this Store
 # clears the obsolete token, without restarting or deleting accepted artwork.
 candidate=folder/'recoverable.png';original_unlink=Path.unlink
 def denied_temporary(path,*args,**kwargs):
  if path.suffix=='.tmp':raise PermissionError('Controlled temporary cleanup denial')
  return original_unlink(path,*args,**kwargs)
 with patch('artwork_store.os.replace',side_effect=OSError('Primary dependency replacement failure')),patch.object(Path,'unlink',denied_temporary):
  try:store.write(candidate,b'accepted immutable recovery pixels','working');raise AssertionError('Failed replace succeeded')
  except OSError as exc:assert str(exc)=='Primary dependency replacement failure' and 'cleanup denial' in str(exc.__notes__)
 assert store.state()['reserved_bytes'] and not candidate.exists()
 store.reconcile(1);assert not store.state()['reserved_bytes']
 assert store.write(candidate,b'accepted immutable recovery pixels','working')
 assert candidate.read_bytes()==b'accepted immutable recovery pixels' and legacy.exists()
 store.retire(candidate);store.reclaim()
 checks.append('Interrupted dependency replacement and denied temporary cleanup retain primary error; same-process reconciliation/Retry succeeds with no stranded reservation or original deletion')
 cancel=threading.Event();cancel.set()
 try:store.write(folder/'cancel.png',b'data',cancel=cancel);raise AssertionError('Cancelled write applied')
 except CancelledError:pass
 session=out/'last-good.json';session.write_bytes(b'old-good')
 with patch('artwork_store.os.replace',side_effect=OSError('Interrupted before JSON commit')):
  try:write_json(session,b'new-good');raise AssertionError('Interrupted save succeeded')
  except OSError:pass
 assert session.read_bytes()==b'old-good'
 replace=os.replace
 def after_replace(*args):replace(*args);cancel.set()
 cancel.clear()
 with patch('artwork_store.os.replace',side_effect=after_replace):write_json(session,b'new-good',cancel)
 assert session.read_bytes()==b'new-good'
 checks.append('Cancellation before commit keeps last good JSON; completed atomic commit remains truthful after late cancellation')
 # A child interrupts a working dependency immediately after replacement. Its
 # byte lock is released by OS exit; a new Store safely reconciles reservation.
 interrupted=out/'interrupted';helper=out/'interrupt-writer.py'
 helper.write_text("import sys,os\nfrom pathlib import Path\nsys.path.insert(0,"+repr(str(ROOT/'app/visuals'))+")\nfrom artwork_store import Store\ns=Store("+repr(str(interrupted))+")\nreplace=os.replace\ndef stop(*a):replace(*a);os._exit(7)\nos.replace=stop\ns.write(s.folder/'accepted.png',b'immutable accepted pixels','working')\n")
 child=subprocess.run([sys.executable,str(helper)]);assert child.returncode==7
 reopened=Store(interrupted);assert reopened.state()['reserved_bytes']==0 and reopened.state()['files']==1 and (interrupted/'accepted.png').exists()
 reopened.retire(interrupted/'accepted.png');reopened.reclaim();assert reopened.state()['files']==0
 checks.append('Interrupted dependency replace reconciles reservation; active accepted file stays protected until explicit retirement; restart completes retirement')
 # Expired failure entries follow actual History and save-reader ownership.
 from PySide6.QtWidgets import QApplication
 app=QApplication.instance() or QApplication([])
 from PySide6.QtGui import QImage,QColor
 from raster_resources import Resources,snapshot,release
 from composition import History,defaults,new_layer
 import uuid
 im=QImage(16,16,QImage.Format_ARGB32_Premultiplied);im.fill(QColor('#742cab'));desc,producer=snapshot(im)
 bad=out/'failed-turnover-store';bad.write_text('Actual invalid working destination')
 resources=Resources(bad);history=History();scene=defaults();layer=new_layer('Artwork');scene['layers']=[layer];held=None
 try:
  for i in range(350):
   key=uuid.uuid4().hex;a=dict(id=key,kind='Images',path=str(out/'placeholder.png'),name='Accepted version',managed=True,internal=True,provenance='drawing',runtime=desc)
   resources.admit([a]);resources.persist(key)
   while not resources.jobs[key].done():time.sleep(.001)
   resources.poll();assert key in resources.failures
   before=deepcopy(scene);ref={k:v for k,v in resources.rows[key].items() if k in ('id','kind','path','name','managed','internal','provenance')};scene['assets']=[ref];scene['layers'][0]['asset']=key
   history.record(before,scene,'Brush own-content stroke',scope='drawing',target=layer['id'])
   if i==0:held=key;resources.save_pins['requested-old-revision']={held}
   keep={a['id'] for item in history.undo+history.redo for candidate in (item['before'],item['after']) for a in candidate['assets']}|{key}
   resources.retain(keep);assert key in resources.rows and held in resources.rows
  assert len(history.undo)==64 and len(resources.rows)<=66 and len(resources.failures)==len(resources.rows)
  resources.save_pins.clear();resources.retain(keep);assert held not in resources.rows and len(resources.rows)==65
  checks.append('350 accepted failed-write versions through five Undo turnovers: only current/64-history plus a held save survive; releasing save retires obsolete failure without losing accepted current pixels')
 finally:resources.close(discard=True);release(producer)
 from media_registry import MediaRegistry
 registry=MediaRegistry(out/'metadata-library.json')
 try:
  while registry.loading:registry.poll();time.sleep(.001)
  public_id=uuid.uuid4().hex
  public=dict(id=public_id,kind='Images',path=str(legacy),name='Original',internal=False,status='Ready',metadata={},error='')
  registry.assets[public['id']]=public
  for i in range(4200):
   key=f'{i:032x}';registry.assets[key]=dict(public,id=key,internal=True);registry.prune_internal({public_id,key})
  assert len(registry.assets)==2 and registry.assets[f'{4199:032x}']['internal'] and legacy.exists()
  checks.append('4,200 generated metadata replacements prune obsolete internal rows while public Library original survives; no lifetime internal-reference accumulation')
 finally:assert registry.close()
 (out/'unit.json').write_text(json.dumps(dict(checks=checks,store=check),indent=2));return checks

def child(out,case):
 out.mkdir(parents=True,exist_ok=False)
 os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
 hold=out/'hold'
 if case in ('pending','cancel_save','held_save'):hold.touch();os.environ['ZERAWAVE_RASTER_TEST_BARRIER']=str(hold)
 if case in ('failure','recovery'):os.environ['ZERAWAVE_ARTWORK_STORE']=str(out/'blocked');(out/'blocked').write_text('Actual unavailable folder')
 from PySide6.QtWidgets import QApplication,QMessageBox,QFileDialog
 from PySide6.QtGui import QImage,QColor
 import studio_qt
 error=studio_qt.Shell.error
 def isolated(self,*args,**kwargs):
  with patch.object(studio_qt,'ROOT',out):return error(self,*args,**kwargs)
 app=QApplication([]);app.setQuitOnLastWindowClosed(False)
 with patch.object(studio_qt.Shell,'error',isolated):shell=studio_qt.Shell(out/'layout.json',out/'owner.log')
 shell.resize(1440,900);shell.show();samples=[];began=time.perf_counter();e=None
 def pump(t=.02):
  end=time.perf_counter()+t
  while time.perf_counter()<end:app.processEvents();time.sleep(.001)
 def wait(fn,t=25):
  end=time.perf_counter()+t
  while time.perf_counter()<end:
   a=time.perf_counter();pump();samples.append((time.perf_counter()-a)*1000)
   if fn():return
  raise AssertionError('Timeout '+shell.statusBar().currentMessage())
 def idle():wait(lambda:not e.edit_jobs and not e.art_jobs)
 def pixels():return e.canvas.source_image(e.selected_row())
 def digest():
  im=pixels().convertToFormat(QImage.Format_RGBA8888_Premultiplied);return hashlib.sha256(bytes(im.constBits())).hexdigest()
 from native_raster import backend
 result=dict(case=case,pid=os.getpid(),native=backend().status(),native_sha256=hashlib.sha256(Path(backend().path).read_bytes()).hexdigest() if backend().available else None)
 wait(lambda:hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;result['owner_pid']=shell.client.process.pid
 if case!='clean':
  shell.panels['composition'].toggleView(True);e.resize_canvas((128,96),False);e.blank_layer();idle();wait(lambda:pixels() is not None)
  c=e.canvas;r=e.selected_row();e.choose_tool('Brush');c.paint_press(r,c.screen_point(r,(.2,.3)));c.paint_move(c.screen_point(r,(.3,.35)));c.paint_finish();idle();result['accepted_hash']=digest()
 if case in ('failure','recovery'):wait(lambda:bool(shell.client.snapshot['media_control']['raster']['failures']))
 if case=='recovery':
  requested=e.binding[1];save=out/'recovered.json';shell.client.request('save',path=str(save));wait(lambda:any(s['status']=='durable' and s['revision']==requested for s in shell.client.snapshot['media_control']['raster']['saves']));assert digest()==result['accepted_hash']
  e.blank_layer();idle();e.blank_child();idle();assert len(e.config['layers'])==3;result['recovery_then_creation']=True
 if case=='save_failure':
  save=out/'save.json';save.write_text('{"last_good":true}');save.chmod(0o444)
 else:save=out/'save.json'
 choice=QMessageBox.Save if case in ('save','save_failure','cancel_save','held_save') else QMessageBox.Cancel if case=='cancel' else QMessageBox.Discard
 close_start=time.perf_counter()
 def choose_modal(*args,**kwargs):
  from PySide6.QtCore import QTimer
  original=question
  def click():
   box=app.activeModalWidget()
   if isinstance(box,QMessageBox):box.button(QMessageBox.Discard).click()
  QTimer.singleShot(100,click);return original(*args,**kwargs)
 question=QMessageBox.question
 dialog=patch.object(QMessageBox,'question',side_effect=choose_modal) if case=='modal_discard' else patch.object(QMessageBox,'question',return_value=choice)
 with dialog,patch.object(QFileDialog,'getSaveFileName',return_value=(str(save),'Session')):
  shell.close()
  if case in ('cancel','save_failure'):
   wait(lambda:getattr(shell,'close_request',None) is None);assert shell.isVisible() and shell.client.process.poll() is None
   if case=='save_failure':assert save.read_text()=='{"last_good":true}';save.chmod(0o666)
   assert digest()==result['accepted_hash'];result['remained_open']=True
  elif case=='cancel_save':
   wait(lambda:shell.close_request and shell.close_request['phase']=='save');shell.cancel_close();wait(lambda:getattr(shell,'close_request',None) is None);hold.unlink();wait(lambda:shell.client.snapshot['media_control']['raster']['pending']==0);assert digest()==result['accepted_hash'];result['cancelled_save_usable']=True
  else:
   if case=='held_save':wait(lambda:shell.close_request and shell.close_request['phase']=='save');pump(.5);assert shell.isVisible() and shell.client.process.poll() is None;hold.unlink()
   wait(lambda:shell.closing,t=35)
 if not shell.closing:
  with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close();wait(lambda:shell.closing,t=35)
 result.update(close_ms=(time.perf_counter()-close_start)*1000,owner_exit=shell.client.process.poll(),window_visible=shell.isVisible(),threads=[t.name for t in threading.enumerate() if not t.daemon and t is not threading.main_thread()],pump_ms=samples,errors=list(shell.errors))
 assert result['owner_exit']==0 and not result['window_visible'] and not result['threads'],result
 if case=='save':
  saved=json.loads(save.read_text());assert saved['b1_saved_revision']['revision']>=1;result['save_durable']=True
 (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='pump_ms'}),flush=True)
 # No force-close cleanup: interpreter return and parent-observed process exit.

def run(out):
 out.mkdir(parents=True,exist_ok=False);checks=unit(out);cases=[]
 binding=dict(root=str(ROOT),files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app/visuals').glob('*.py')})
 (out/'source-binding.json').write_text(json.dumps(binding,indent=2))
 for case in ('clean','discard','pending','failure','save','save_failure','cancel','cancel_save','held_save','recovery','modal_discard'):
  began=time.perf_counter()
  with (out/(case+'.console.log')).open('w') as log:
   p=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),str(out/case),case],stdout=log,stderr=subprocess.STDOUT)
   try:code=p.wait(timeout=65)
   except subprocess.TimeoutExpired:
    p.terminate();code=p.wait();cases.append(dict(case=case,exit=code,forced_cleanup=True));raise AssertionError('Child did not exit normally: '+case)
  cases.append(dict(case=case,exit=code,seconds=time.perf_counter()-began,forced_cleanup=False));(out/'exits.json').write_text(json.dumps(cases,indent=2));assert code==0,(case,code)
 print(json.dumps(dict(checks=checks,exits=cases),indent=2))
if __name__=='__main__':
 if len(sys.argv)>2:child(Path(sys.argv[1]).resolve(),sys.argv[2])
 else:run(Path(sys.argv[1]).resolve())
