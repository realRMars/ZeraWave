"""Explicit paragraphs, Unicode/UTF16 formatting and missing-font rejection."""
from pathlib import Path
import sys,os,json,uuid
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from video_project import create,apply,style_defaults
from project_evaluator import Evaluator
from project_text import TextSurface
app=QApplication([]);out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);rows=[]
for name,text,expected in [('single','First line Second line',1),('LF','First line\nSecond line',2),('CRLF','First line\r\nSecond line',2),('CR','First line\rSecond line',2),('blank','First line\n\nSecond line',3),('trailing','First line\n',2),('unicode','🎮 café\n日本語 العربية',2)]:
 t,c=uuid.uuid4().hex,uuid.uuid4().hex;d=apply(create(settings=dict(width=1280,height=720)),[dict(op='track.add',id=t,kind='graphics'),dict(op='caption.add',id=c,track=t,start=0,duration=60,text=text,style=dict(style_defaults(),bounds=[.05,.1,.9,.5],color='#b9e5ff',stroke_width=1,line_spacing=33))],uuid.uuid4().hex)[0];s=TextSurface();r=s.augment(dict(plan=Evaluator(d,'lines',1).at(0),images={},error=None));frame=r['images'][c];assert frame['text_details']['lines']==expected,(name,frame['text_details']);assert d['captions'][0]['text']==text and frame['text_details']['font_resolved'];rows.append(dict(case=name,saved_text=text,details=frame['text_details'],font_sources=s.stats.get('application_font_sources')))
 import numpy as np
 from PySide6.QtGui import QImage
 pixels=np.frombuffer(frame['data'],np.uint8).reshape(frame['height'],frame['width'],4)[::-1].tobytes();assert QImage(pixels,frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).save(str(out/(name+'.png')));s.close()
# Glyph/paragraph failure is explicit and cannot change the authoring recipe.
bad=dict(d);bad['captions']=[dict(d['captions'][0],style=dict(d['captions'][0]['style'],max_lines=1))];s=TextSurface()
try:s.augment(dict(plan=Evaluator(bad,'lines',2).at(0),images={},error=None));raise AssertionError('Paragraphs silently omitted')
except ValueError:pass
finally:s.close()
bad['captions'][0]['style']['font']='ZeraWave intentionally absent font';s=TextSurface()
try:s.augment(dict(plan=Evaluator(bad,'lines',3).at(0),images={},error=None));raise AssertionError('Unavailable font accepted as readable')
except ValueError as error:assert 'font family is unavailable' in str(error)
finally:s.close()
(out/'RESULT.json').write_text(json.dumps(dict(checks=9,rows=rows,classification=__doc__),ensure_ascii=False,indent=2),'utf8');print('PASS explicit paragraphs/font coverage 9')
