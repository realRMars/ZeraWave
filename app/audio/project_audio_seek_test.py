"""Actual long compressed-audio demand/canonical-byte parity; no device or GUI."""
from pathlib import Path
from fractions import Fraction
import json,sys,time,threading,hashlib,importlib.util,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/audio')];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);plan=json.loads(Path(sys.argv[2]).read_text());asset=next(a for a in plan['assets'].values() if a['name']=='Haunted Level 1');old_path=Path(sys.argv[3]);spec=importlib.util.spec_from_file_location('old_audio_seek_reference',old_path);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);from project_mixer import NativeSource,Budget
import numpy as np
cancel=threading.Event();legacy=candidate=None;identity=hashlib.sha256((ROOT/'app/audio/project_mixer.py').read_bytes()).hexdigest();rows=[]
try:
 legacy=old.NativeSource(asset,old.Budget());error=None
 try:legacy.read(Fraction(1),Fraction(1),2048,cancel);legacy.read(Fraction(75),Fraction(1),2048,cancel)
 except ValueError as exc:error=str(exc)
 assert error and 'Audio decode exceeded' in error,error;legacy.close();legacy=None;budget=Budget();candidate=NativeSource(asset,budget)
 for position in (Fraction(1),Fraction(75),Fraction(3),Fraction(100),Fraction(30),Fraction(75)):
  began=time.perf_counter();pcm=candidate.read(position,Fraction(1),2048,cancel);ms=(time.perf_counter()-began)*1000;ref=NativeSource(asset,Budget())
  try:expected=ref.read(position,Fraction(1),2048,cancel)
  finally:ref.close()
  assert np.array_equal(pcm,expected),float(np.max(abs(pcm-expected)));assert budget.used<=budget.limit;rows.append(dict(source_time=str(position),samples=len(pcm),ms=ms,seeks=candidate.seeks,cache_bytes=candidate.bytes,sha256=hashlib.sha256(pcm).hexdigest()))
 cancel.set();before=candidate.seeks
 try:candidate.read(Fraction(20),Fraction(1),2048,cancel)
 except InterruptedError:pass
 else:raise AssertionError('Cancelled demand read')
 assert candidate.seeks==before;candidate.close();candidate=None;assert budget.used==0;assert hashlib.sha256((ROOT/'app/audio/project_mixer.py').read_bytes()).hexdigest()==identity;(out/'RESULT.json').write_text(json.dumps(dict(result='PASS',original_failure=error,records=rows,source_sha256=identity,old_source_sha256=hashlib.sha256(old_path.read_bytes()).hexdigest(),checks=['Actual old compressed-audio forward demand reproduces512-frame/2-second rejection','Bounded distant seek matches fresh native canonical stereo bytes at six forward/back/repeat targets','Cancellation adds no source seek; actual reader/cache budget releases to0'],classification=__doc__),indent=2),'utf8');print('PASS audio seek',len(rows))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if legacy:legacy.close()
 if candidate:candidate.close()
