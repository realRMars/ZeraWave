"""Standalone codec-owner, concurrency-pressure, cancellation and reader-lifetime checks."""
from pathlib import Path
import sys,time,json,threading,hashlib,traceback
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
import project_media as pm
from project_evaluator import Evaluator
from project_service import read_project
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);fixture=Path(sys.argv[2]);document=read_project(fixture,threading.Event())[0];e=Evaluator(document,'codec-owner-test',0);original=pm.DecoderWindow;mode=['normal'];gate=threading.Event();entered=threading.Event();owners=[];checks=[];m=None
class OwnedWindow(original):
 def __init__(self,*a,**kw):self.owner=threading.get_ident();super().__init__(*a,**kw);assert self.codec_threads==4 and self.stream.codec_context.thread_count==4;owners.append(dict(event='open',thread=self.owner,codec_threads=self.codec_threads))
 def get(self,target,cancel,*a,**kw):
  assert threading.get_ident()==self.owner
  if mode[0]=='gate':entered.set();assert gate.wait(10),'Test gate timeout'
  if mode[0]=='failure':mode[0]='normal';raise MemoryError('Controlled codec pressure: original failure')
  return super().get(target,cancel,*a,**kw)
 def close(self):assert threading.get_ident()==self.owner;owners.append(dict(event='close',thread=self.owner));return super().close()
def demand(frame):
 serial=m.submit(e.at(frame));end=time.monotonic()+12
 while not m.ready():assert time.monotonic()<end;time.sleep(.002)
 r=m.take();assert r['serial']==serial;return r
try:
 with patch.object(pm,'DecoderWindow',OwnedWindow):
  m=pm.Media();r=demand(31);assert not r['error'] and len(r['images'])>=2 and m.metrics['decode_route']=='bounded parallel codec owners';assert m.metrics['codec_workers']<=4;native={k:hashlib.sha256(v['data']).hexdigest() for k,v in r['images'].items()}
  try:m.close();raise AssertionError('Borrowed snapshot disposed')
  except RuntimeError as error:assert 'snapshot' in str(error)
  assert native=={k:hashlib.sha256(v['data']).hexdigest() for k,v in r['images'].items()};m.release(r['serial']);r=None;assert m.metrics['codec_threads_per_decoder'] and all(n==4 for n in m.metrics['codec_threads_per_decoder']) and m.metrics['codec_thread_limit']==16;checks.append('Independent existing native clocks run on <=4 fixed codec-owner workers; an outstanding reader prevents disposal and its native bytes remain intact')
  plan=e.at(31);costs={m.key(item,plan):item['asset']['metadata']['width']*item['asset']['metadata']['height']*4 for item in plan['visual']};serial_bound=sum(costs.values())+3*max(costs.values());parallel_bound=4*sum(costs.values());assert serial_bound<parallel_bound;pressure_budget=(serial_bound+parallel_bound)//2
  with patch.object(pm,'RGBA_BUDGET',pressure_budget):
   r=demand(31);assert not r['error'] and m.metrics['decode_route']=='serial within original RGBA reservation';assert native=={k:hashlib.sha256(v['data']).hexdigest() for k,v in r['images'].items()};m.release(r['serial']);r=None
  assert pm.RGBA_BUDGET==128*1024*1024;checks.append('Controlled concurrency reservation pressure selects the original serial route with identical native bytes; product plane/RGBA caps and supported combinations stay unchanged')
  mode[0]='failure';r=demand(32);assert 'MemoryError: Controlled codec pressure: original failure'==r['error'];m.release(r['serial']);r=None;r=demand(33);assert not r['error'];m.release(r['serial']);r=None;checks.append('A real codec-task MemoryError is published as the original error after every sibling future drains; deliberate subsequent demand recovers in the same Media instance')
  mode[0]='gate';old=m.submit(e.at(34));assert entered.wait(5);latest=m.submit(e.at(35));mode[0]='normal';gate.set();end=time.monotonic()+12
  while not m.ready():assert time.monotonic()<end;time.sleep(.002)
  r=m.take();assert r['serial']==latest and r['serial']!=old and not r['error'] and r['plan']['frame']==35;m.release(r['serial']);r=None;checks.append('Replacement while native tasks are held cancels the obsolete generation, drains all owners and publishes only the newest immutable result; no stale reader/duplicate outcome')
  m.close();m.thread.join(12);assert m.exited() and m.planes.used==m.metrics['rgba_bytes']==m.metrics['codec_workers']==0;assert len([x for x in owners if x['event']=='open'])==len([x for x in owners if x['event']=='close']);checks.append('Normal cleanup closes every codec on its owning thread and retires all codec workers, shared planes and RGBA snapshots')
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,owners=owners,metrics=m.metrics,fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'app/visuals/project_media.py').read_bytes()).hexdigest()),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 gate.set()
 if m:
  if m.leased:m.release(m.leased['serial'])
  m.close();m.thread.join(12)
