"""Audio-only natural-end coverage on the existing absolute canonical clock.

Does not edit media or define video/VFR duration. Explicit user Out ranges keep
their existing frame policy. Old metadata remains readable without exact counts.
"""
from fractions import Fraction
from video_project import rational,integer,fail

RATE=48000

def ceiling(value):
 value=Fraction(value);return -(-value.numerator//value.denominator)

def natural_duration(metadata):
 if 'sample_count' in metadata:
  count=integer(metadata['sample_count'],1);rate=integer(metadata.get('samplerate'),8000,192000)
  return Fraction(count,rate)
 return rational(metadata['duration_time']) if 'duration_time' in metadata else Fraction(str(metadata['duration']))

def natural_frames(metadata,fps,*,start=0,source_in=None,rate=None):
 """Smallest positive frame interval covering the remaining canonical samples.

Canonical resampling uses the existing finite, flushed output interval. Its
sample-count ceiling and absolute nearest frame-to-sample rounding are distinct:
the latter must cover the former, including at nonzero fractional-frame starts.
"""
 integer(start,0);fps=rational(fps);speed=rational([1,1] if rate is None else rate);source=rational([0,1] if source_in is None else source_in)
 if fps<=0 or not Fraction(1,16)<=speed<=16 or source<0:fail('invalid_time','Invalid audio-only natural range.')
 duration=natural_duration(metadata)
 if source>=duration:fail('source_range','Audio In is outside the natural source interval.')
 stop=Fraction(start)+(duration-source)*fps/speed
 out=max(start+1,ceiling(stop))
 source_samples=ceiling(duration*RATE)
 canonical_stop=ceiling(Fraction(start)*RATE/fps+(Fraction(source_samples)-source*RATE)/speed)
 def sample_at(frame):
  v=Fraction(frame)*RATE/fps;return (v.numerator*2+v.denominator)//(v.denominator*2)
 while sample_at(out)<canonical_stop:out+=1
 while out>start+1 and sample_at(out-1)>=canonical_stop:out-=1
 return out-start
