"""Plain-text SRT on the existing project worker; style remains in .zwv."""
from pathlib import Path
from fractions import Fraction
import hashlib,os,re,uuid
from video_project import validate,fail
from project_export import protect

def encode_srt(document):
 document=validate(document,allow_missing_routes=True);fps=Fraction(*document['settings']['fps']);parts=[]
 def stamp(frame):
  # Import uses ceil(ms * fps): floor(frame/fps * 1000) roundtrips exactly
  # for supported <=120fps, including 30000/1001 and 24000/1001.
  value=int(Fraction(frame*1000,1)/fps)
  if -(-value*fps.numerator//(1000*fps.denominator))!=frame:fail('caption_roundtrip','Frame cannot be represented in SRT milliseconds.')
  hours,value=divmod(value,3600000);minutes,value=divmod(value,60000);seconds,ms=divmod(value,1000);return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'
 for row in sorted(document['captions'],key=lambda c:(c['start'],c['order'],c['id'])):
  text=row['text']
  if row.get('dynamic') is not None or not text or text!=text.strip() or '\r' in text or re.search(r'\n\s*\n',text):fail('caption_roundtrip','SRT export requires static, nonempty text without outer whitespace or blank paragraphs. Keep the exact rich caption in .zwv or edit it explicitly.')
  parts.append(f"{len(parts)+1}\n{stamp(row['start'])} --> {stamp(row['start']+row['duration'])}\n{text}\n\n")
 if not parts:fail('empty_captions','Add dedicated captions before exporting SRT; titles remain separate.')
 raw=''.join(parts).encode('utf8')
 if len(raw)>2*1024*1024:fail('caption_capacity','SRT output exceeds the existing2MiB import bound.')
 return raw

def write_srt(document,revision,path,cancel,extra=()):
 target=protect(document,path,extra,suffix='.srt')
 if target.exists():fail('destination_exists','SRT export requires a new destination; existing subtitles were preserved.')
 raw=encode_srt(document);target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_name('.'+target.name+'.'+uuid.uuid4().hex+'.tmp')
 try:
  with temporary.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
  if cancel.is_set():fail('cancelled','SRT export cancelled before publication; accepted project retained.')
  failure=os.environ.get('ZERAWAVE_PROJECT_TEST_WRITE_FAILURE')
  if failure=='1' or failure and Path(failure).exists():raise OSError('Controlled SRT write failure before publication')
  protect(document,target,extra,suffix='.srt')
  try:os.link(temporary,target)
  except FileExistsError:fail('destination_exists','SRT destination appeared while exporting; existing file preserved.')
  return dict(path=str(target),revision=revision,format='plain-text SRT',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),captions=len(document['captions']),limits='Text/timing only; no style, fonts, title graphics, rich metadata or original cue-number roundtrip. Exact styles remain in .zwv.')
 finally:
  try:temporary.unlink(missing_ok=True)
  except OSError:pass # Do not obscure the primary write failure; source/destination stay intact.
