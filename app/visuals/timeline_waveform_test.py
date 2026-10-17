"""Generated240s complete waveform,Qt paint,canonical rate coverage and bounded lifetime."""
from pathlib import Path
from fractions import Fraction
from copy import deepcopy
import sys,os,json,time,threading,uuid,traceback,wave,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);source=Path(sys.argv[2]);os.environ['QT_QPA_PLATFORM']='offscreen'
import numpy as np
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtGui import QPainter,QColor,QImage,QFont
from PySide6.QtCore import QRectF
from timeline_decorations import Decorations
from timeline_waveform import prepare,span,covered
from project_service import prepare_changes
from video_project import create,apply,new_id
app=QApplication([])
from project_text import existing_font
existing_font('Segoe UI');app.setFont(QFont('Segoe UI',9))
checks=[];decorations=[];raw=[];paint=[];worker=[]
def asset(path,name='Known waveform'):
 r=prepare_changes([dict(op='media.add',id=new_id(),name=name,kind='Audio',location=dict(kind='external',path=str(path)))],None,threading.Event())[0];r.pop('op');return r
def document(a,frames=7200,rate=[1,1],source_in=[0,1]):
 d=create('Waveform test',dict(width=1920,height=1080));track=new_id();return apply(d,[dict(op='media.add',**a),dict(op='track.add',id=track,kind='audio'),dict(op='clip.add',asset=a['id'],track=track,start=0,duration=frames,rate=rate,source_in=source_in)],new_id())[0]
class Canvas(QWidget):
 def __init__(self,d):
  super().__init__();self.d=d;self.scale=1300/7200;self.clip_rect=QRectF(0,0,1300,90);self.deco=None;self.resize(1400,100);self.show()
 def paintEvent(self,event):
  began=time.perf_counter();p=QPainter(self);p.fillRect(self.rect(),QColor('#101920'))
  if self.deco:self.deco.draw(p,self.clip_rect,self.d['clips'][0],self.d)
  p.end();paint.append((time.perf_counter()-began)*1000)
def wait(fn,seconds=40,deco=None):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  began=time.perf_counter();app.processEvents()
  if deco:deco.poll()
  raw.append((time.perf_counter()-began)*1000)
  if fn():return
  time.sleep(.001)
 raise AssertionError('Waveform timeout')
def close(deco):
 began=time.perf_counter();deco.close();wait(lambda:deco.exited(),20,deco);assert not deco.state and deco.metrics.get('retired_reader_budget',0)==0;return time.perf_counter()-began
def run_job(a,source_in,rate,seconds,fallback=False):
 class Quiet:
  def update(self):pass
 deco=Decorations(Quiet());decorations.append(deco);job=dict(asset=a,source=source_in,rate=rate,span=seconds,bins=128,kind='wave',cancel=threading.Event(),force_fallback=fallback)
 def work():
  result=None
  while not result or not result['complete']:
   result=deco.build(dict(job,progress=result))
  return result
 try:return deco.pool.submit(work).result(timeout=20)
 finally:close(deco)
try:
 a=asset(source);d=document(a);canvas=Canvas(d);deco=Decorations(canvas);decorations.append(deco);canvas.deco=deco;deco.set_document(d);app.processEvents();canvas.grab().save(str(out/'PENDING-OFFSCREEN.png'));began=time.perf_counter();first_feedback=None;intermediate=None
 while not any(r.get('complete') for r,_ in deco.cache.values()):
  before=time.perf_counter();app.processEvents();deco.poll();raw.append((time.perf_counter()-before)*1000)
  for result,_ in deco.cache.values():
   if 'peaks' in result:
    worker.append(dict(done=result['done'],total=result['total'],work_ms=result['work_ms']))
    if first_feedback is None:first_feedback=time.perf_counter()-began
    if not result['complete'] and intermediate is None:intermediate=dict(done=result['done'],total=result['total'],unprocessed_bins=sum(not covered(result,i) for i in range(result['bins'])));canvas.grab().save(str(out/'PARTIAL-OFFSCREEN.png'))
  assert time.perf_counter()-began<50;time.sleep(.001)
 elapsed=time.perf_counter()-began;result=next(r for r,_ in deco.cache.values() if 'peaks' in r);assert result['total']==result['done']==11520000 and result['complete'] and all(covered(result,i) for i in range(1024));assert deco.metrics['scanned_samples']==11520000
 for seconds in (.5,120.,239.):assert result['peaks'][int(seconds/240*1024)]>.1
 assert result['peaks'][400]==0 and intermediate['unprocessed_bins']>0;capture=canvas.grab().toImage().convertToFormat(QImage.Format_RGBA8888);capture.save(str(out/'COMPLETE-OFFSCREEN.png'));pixels=np.frombuffer(capture.constBits(),np.uint8).reshape(capture.height(),capture.bytesPerLine())[:,:capture.width()*4].reshape(capture.height(),capture.width(),4)
 for low,high in [(9,20),(630,670),(1270,1292)]:assert np.count_nonzero(np.all(pixels[40:58,low:high,:3]==[189,223,208],axis=2))>0
 overview=dict(seconds=elapsed,first_feedback_seconds=first_feedback,metrics=deepcopy(deco.metrics),result={k:v for k,v in result.items() if k!='peaks'},peaks=result['peaks'].tolist(),intermediate=intermediate,process_events_ms=list(raw),paint_ms=list(paint));checks.append('Actual offscreen Qt paints one full240s overview,all11520000canonical samples scanned; beginning/middle/near-end signals have visible pixels,processed silence zero,partial bins stay pending and progress visible')
 canvas.scale=4;canvas.clip_rect=QRectF(-238*120,0,7200*4,90);canvas.update();wait(lambda:any(k[2]=='detail' and k[3]==119 and r.get('complete') for k,(r,_) in deco.cache.items()),20,deco);detail=next(r for k,(r,_) in deco.cache.items() if k[2]=='detail' and k[3]==119);assert detail['first_source_sample']==238*48000 and detail['total']==96000 and detail['peaks'].max()>.1;checks.append('Near-end zoom lazily refines actual238–240source seconds with128bins; no first64second substitution')
 # A mute/gain-only edit cannot invalidate a raw-source display.
 changed=deepcopy(d);changed['clips'][0]['audio'].update(gain=0.,mute=True);domains=deepcopy(deco.domains);deco.set_document(changed);assert deco.domains==domains;checks.append('Raw pre-gain/mute/fade/envelope semantics are explicit; authoring gain/mute does not alter or invalidate source peaks')
 close(deco);canvas.close()
 pulses=out/'odd-pulses.wav';samples=np.zeros(96000,'<i2');samples[[1,101,90001]]=24576
 with wave.open(str(pulses),'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
 pulse_asset=asset(pulses);native=run_job(pulse_asset,Fraction(0),Fraction(2),Fraction(1));fallback=run_job(pulse_asset,Fraction(0),Fraction(2),Fraction(1),True);trim=run_job(pulse_asset,Fraction(1,48000),Fraction(1,2),Fraction(2));assert native['done']==96000 and native['peaks'].max()==fallback['peaks'].max()==.75 and np.array_equal(native['peaks'],fallback['peaks']);assert trim['first_source_sample']==1 and trim['total']==48000 and trim['peaks'].max()==.75;assert span(Fraction(1,96000),Fraction(1),Fraction(3,2))==(0,72001);checks.append('Native and supported fallback at2x capture all three odd-sample pulses that old display missed; half-rate/nonzero In and fractional covering interval map correctly')
 # Hold a REAL computed result only after preparation,then replace source identity.
 silence=out/'silence.wav'
 with wave.open(str(silence),'wb') as f:f.setparams((1,2,48000,0,'NONE','not compressed'));f.writeframes(np.zeros(96000,'<i2').tobytes())
 d1=document(pulse_asset,60);a2=asset(silence);a2['id']=pulse_asset['id'];d2=deepcopy(d1);d2['media']=[a2];canvas=Canvas(d1);canvas.scale=10;canvas.clip_rect=QRectF(0,0,600,90);deco=Decorations(canvas);decorations.append(deco);canvas.deco=deco;deco.set_document(d1);entered=threading.Event();release=threading.Event();original=deco.build
 def held(job):
  value=original(job);entered.set();assert release.wait(10);return value
 deco.build=held;app.processEvents();deco.poll();wait(entered.is_set,10);deco.set_document(d2);canvas.d=d2;release.set();wait(lambda:deco.future is None,10,deco);assert deco.metrics['stale_results']==1 and not deco.cache;deco.build=original;canvas.update();wait(lambda:any(r.get('complete') for r,_ in deco.cache.values()),15,deco);assert all(not r.get('error') and not np.any(r['peaks']) for r,_ in deco.cache.values());checks.append('Controlled delayed real result with changed hash/path is discarded after generation change; new source shows genuine completed silence,no stale pixels')
 close(deco);canvas.close()
 # Actual failure is labeled unavailable,not a silent zero waveform.
 bad=deepcopy(a2);bad['sha256']='0'*64;bad_doc=document(bad,60);canvas=Canvas(bad_doc);canvas.scale=10;canvas.clip_rect=QRectF(0,0,600,90);deco=Decorations(canvas);decorations.append(deco);canvas.deco=deco;deco.set_document(bad_doc);canvas.update();wait(lambda:any(r.get('error') for r,_ in deco.cache.values()),15,deco);error=next(r for r,_ in deco.cache.values());assert 'peaks' not in error and 'changed' in error['error'];canvas.grab().save(str(out/'ERROR-OFFSCREEN.png'));close(deco);canvas.close();checks.append('Actual source-hash failure caches an explicit unavailable state,not zero samples or an endless automatic retry')
 # Close during real incremental work; readers drain on their owning worker.
 canvas=Canvas(d);deco=Decorations(canvas);decorations.append(deco);canvas.deco=deco;deco.set_document(d);canvas.update();app.processEvents();deco.poll();wait(lambda:any(r.get('done',0)>0 and not r.get('complete') for r,_ in deco.cache.values()) and deco.future is not None and deco.future.running(),15,deco);prepared_before_cancel=max(r.get('done',0) for r,_ in deco.cache.values());cancel_seconds=close(deco);canvas.close();assert cancel_seconds<3 and prepared_before_cancel>0;checks.append('Real running generation after published partial progress cancels,drains on same worker and retires readers/budget/thread; latency recorded,not a universal deadline')
 class Quiet:
  def update(self):pass
 deco=Decorations(Quiet());decorations.append(deco)
 for i in range(200):
  key=(str(i),('domain',),'overview');deco.domains[str(i)]=('domain',);deco.want(str(i),[key]);deco.request(key,dict(kind='wave'));deco.store(key,dict(peaks=np.zeros(1024,np.float32),done=48000,total=48000,bins=1024,complete=True))
 assert len(deco.pending)==32 and len(deco.cache)==128
 for i in range(3):deco.store(('image'+str(i),(),''),dict(image=QImage(1024,1024,QImage.Format_RGBA8888)))
 assert deco.bytes<=8*1024*1024;bounds=dict(deepcopy(deco.metrics),cache_bytes=deco.bytes,cache_entries=len(deco.cache),pending=len(deco.pending));close(deco);checks.append('Disclosed synthetic queue/entry/byte pressure respects existing32pending,128entries/8MiB cache without raising limits')
 assert all(d.exited() for d in decorations)
 (out/'RAW_QT_PROCESS_EVENTS_MS.json').write_text(json.dumps(raw),encoding='utf8');(out/'RAW_PAINT_MS.json').write_text(json.dumps(paint),encoding='utf8');(out/'RAW_PROGRESS.json').write_text(json.dumps(worker),encoding='utf8');(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,fixture=str(source),fixture_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),overview=overview,zoom=dict(first=detail['first_source_sample'],total=detail['total']),cancel_seconds=cancel_seconds,prepared_before_cancel=prepared_before_cancel,synthetic_pressure=bounds,all_workers_exited=True,unverified='Offscreen Qt and generated sources,not physical/display/playback/listening/resource-plateau qualification. Codec working memory is outside explicit PCM counters.'),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 for deco in decorations:
  if not deco.exited() if deco.closed else True:close(deco)
