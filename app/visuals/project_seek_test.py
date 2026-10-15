"""Real60FPS production-copy demand seeks/native pixel reference; no GL/device."""
from pathlib import Path
import sys,json,threading,time,hashlib,traceback
from fractions import Fraction
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals')]
from media_frames import DecoderWindow,MAX_CACHE_BYTES
import av
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);receipt=Path(sys.argv[2]);r=json.loads(receipt.read_text());source=next(v['copy'] for k,v in r['remapping'].items() if '1170570-' in k);cancel=threading.Event();records=[];legacy=None;candidate=None;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();identity={name:sha(ROOT/'app/visuals'/name) for name in ('media_frames.py','project_media.py')};(out/'SOURCE.json').write_text(json.dumps(identity,indent=2),'utf8')
try:
 legacy=DecoderWindow(source,MAX_CACHE_BYTES,source_timestamps=True);origin=Fraction(legacy.stream.start_time or 0)*legacy.stream.time_base
 legacy_error=None
 try:
  legacy.get(float(Fraction(62)+origin),cancel);legacy.get(float(Fraction(65)+origin),cancel);legacy.get(float(Fraction(2293,30)+origin),cancel)
 except ValueError as exc:legacy_error=str(exc)
 assert legacy_error and 'GOP decode' in legacy_error,legacy_error;legacy.close();legacy=None
 candidate=DecoderWindow(source,MAX_CACHE_BYTES,source_timestamps=True);candidate.demand_resync=True
 for target in (Fraction(62),Fraction(65),Fraction(2293,30),Fraction(1),Fraction(100),Fraction(2293,30)):
  stamp=target+origin;began=time.perf_counter();pts,(w,h,pixels)=candidate.get(float(stamp),cancel);elapsed=(time.perf_counter()-began)*1000
  # Independent direct native timestamp lookup from a newly opened decoder.
  with av.open(source) as container:
   stream=container.streams.video[0];container.seek(int(stamp/stream.time_base),stream=stream,backward=True,any_frame=False);chosen=None
   for frame in container.decode(stream):
    at=Fraction(frame.pts)*frame.time_base
    if at>stamp:break
    chosen=frame
   assert chosen is not None;expected_pts=float(Fraction(chosen.pts)*chosen.time_base);expected=chosen.to_ndarray(format='rgba')[::-1].tobytes();assert pts==expected_pts and pixels==expected,(target,pts,expected_pts)
  assert candidate.bytes<=MAX_CACHE_BYTES;records.append(dict(target=str(target),pts=pts,ms=elapsed,metrics=candidate.metrics,pixels_sha256=hashlib.sha256(pixels).hexdigest()))
 cancel.set();before=candidate.seek_count;assert candidate.get(float(Fraction(70)+origin),cancel) is None and candidate.seek_count==before;cancel.clear();candidate.close();candidate=None
 assert {name:sha(ROOT/'app/visuals'/name) for name in identity}==identity;(out/'RESULT.json').write_text(json.dumps(dict(result='PASS',legacy_failure=legacy_error,records=records,checks=['Natural old-policy large forward walk reproduces512frame/2s rejection on preserved60FPS source','Project-only distant demand resync retains existing bounds, exact independent native PTS/RGBA at forward/back/repeat targets','Cancellation does no additional seek; actual decoded cache bytes remain bounded and reader closes'],classification=__doc__),indent=2),'utf8');print('PASS seek',len(records),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if legacy:legacy.close()
 if candidate:candidate.close()
