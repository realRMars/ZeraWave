"""Bounded Qt text materialization for the existing project compositor.

Authoring remains saved text/style recipes. Context/CPU owner makes premultiplied
native-size pixels; there is no text clock, document edit, codec or second renderer.
"""
from collections import OrderedDict
from copy import deepcopy
from fractions import Fraction
import hashlib,json,math,threading,re
from pathlib import Path
from PySide6.QtCore import Qt,QPointF,QRectF
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QFontInfo,QTextLayout,QTextOption,QTextCharFormat,QPen,QFontDatabase,QFontMetricsF,QGuiApplication
from video_project import layout_defaults,MAX_DOCUMENT_BYTES,fail

TEXT_BYTES=64*1024*1024

class TextFitError(ValueError):
 def __init__(self,code,message,details=None):
  super().__init__(message);self.code=code;self.details=dict(details or {})

_font_registry=None
_registered_font_files={}
def existing_font(family):
 """Read/register existing Windows fonts when an offscreen DB lacks them."""
 global _font_registry
 available={name.casefold() for name in QFontDatabase.families()}
 if family.casefold() in available:return
 import sys,os
 app=QGuiApplication.instance()
 if not app:raise RuntimeError('Text needs its Qt GUI/context owner and font database.')
 if app.platformName()=='offscreen' and sys.platform=='win32':
  if _font_registry is None:
   import winreg
   _font_registry=[]
   for hive in (winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER):
    try:
     with winreg.OpenKey(hive,r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
      for i in range(min(2048,winreg.QueryInfoKey(key)[1])):
       label,value,kind=winreg.EnumValue(key,i)
       if isinstance(value,str):_font_registry.append((label,value))
    except FileNotFoundError:pass
  directory=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts'
  for label,value in _font_registry:
   stem=label.split(' (')[0].casefold()
   if not (stem==family.casefold() or stem.startswith(family.casefold()+' ')):continue
   path=Path(value) if Path(value).is_absolute() else directory/value
   if str(path) in _registered_font_files:continue
   if len(_registered_font_files)>=64:raise MemoryError('Offscreen application-font registration exceeds64 files; requested text retained.')
   if path.is_file():
    identity=QFontDatabase.addApplicationFont(str(path))
    if identity>=0:_registered_font_files[str(path)]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),families=QFontDatabase.applicationFontFamilies(identity))
 available={name.casefold() for name in QFontDatabase.families()}
 if family.casefold() not in available:raise TextFitError('font_unavailable','Requested font family is unavailable: '+family+'. Choose an installed family; no missing-glyph success is reported.',dict(font_requested=family))
def checked_font(font,text):
 import unicodedata
 chars={ord(c) for c in text if not c.isspace() and unicodedata.category(c) not in ('Cf','Cc')}
 def missing():
  metrics=QFontMetricsF(font);return sorted(code for code in chars if not metrics.inFontUcs4(code))
 absent=missing()
 if absent and QGuiApplication.instance().platformName()=='offscreen':
  for family in ('Yu Gothic','Segoe UI Emoji','Segoe UI Symbol'):
   try:existing_font(family)
   except ValueError:pass
  absent=missing()
 if absent:raise TextFitError('glyph_unavailable','Glyphs unavailable in installed Qt fonts: '+', '.join(f'U+{code:04X}' for code in absent[:8])+'. Accepted text retained; choose a covering font.',dict(font_requested=font.family(),missing_codepoints=absent[:128],missing_count=len(absent)))

def clock_text(value):
 seconds=max(0,int(value));return f'{seconds//60}:{seconds%60:02}'
def evaluated(row,plan):
 begin=row.get('range_start',row['start']);end=row.get('range_end',row['start']+row['duration']);elapsed=Fraction(max(0,plan['frame']-begin))/Fraction(*plan['settings']['fps']);length=Fraction(end-begin)/Fraction(*plan['settings']['fps']);progress=max(Fraction(0),min(Fraction(1),Fraction(plan['frame']-begin,end-begin)))
 if row['dynamic']=='progress':return '',float(progress)
 text=row['text']
 if row['dynamic']=='counter':
  for name,value in [('elapsed',clock_text(elapsed)),('duration',clock_text(math.ceil(length))),('frame',str(plan['frame']-begin))]:text=text.replace('{'+name+'}',value)
  if re.search(r'\{[^{}]+\}',text):raise ValueError('Counter supports {elapsed}, {duration} and {frame} only.')
 return text,None

class TextSurface:
 def __init__(self,limit=TEXT_BYTES):self.owner=threading.get_ident();self.limit=limit;self.cache=OrderedDict();self.bytes=0;self.peak=0;self.stats={};self.closed=False
 def check(self):
  if self.closed or threading.get_ident()!=self.owner:raise RuntimeError('Text pixels require their live composition owner.')
 def descriptors(self,plan):
  values=[];w,h=plan['settings']['width'],plan['settings']['height']
  for item in plan['text']:
   row=item['recipe'];text,progress=evaluated(row,plan);style=row['style'];width=max(1,round(style['bounds'][2]*w));height=max(1,round(style['bounds'][3]*h))
   if max(width,height)>8192 or width*height>8388608:raise MemoryError('Text bounds exceed native 8192-axis/8-megapixel materialization; accepted recipe retained.')
   # Placement, rotation and opacity are evaluated by the compositor. Their
   # animation cannot change this native glyph/background plane. Width/height
   # still key reflow, and every actual raster style input remains in the key.
   raster_style={key:value for key,value in style.items() if key not in ('bounds','rotation','opacity','keys')}
   key=hashlib.sha256(json.dumps([text,progress,raster_style,width,height],sort_keys=True,ensure_ascii=False).encode()).hexdigest();values.append(dict(item=item,text=text,progress=progress,style=style,size=(width,height),key=key,bytes=width*height*4))
  return values
 def pixels(self,descriptor,*,measure_only=False):
  self.check()
  d=descriptor;w,h=d['size'];style=d['style'];padding=style['padding'];px=style.get('padding_x',padding);py=style.get('padding_y',padding);radius=style.get('radius',9);image=QImage(w,h,QImage.Format_RGBA8888_Premultiplied);image.fill(Qt.transparent);p=QPainter(image);details={}
  try:
   p.setRenderHints(QPainter.Antialiasing|QPainter.TextAntialiasing);p.setPen(Qt.NoPen);p.setBrush(QColor(style['background']));p.drawRoundedRect(QRectF(0,0,w,h),radius,radius)
   if d['progress'] is not None:
    p.setBrush(QColor(style['color']));p.drawRect(QRectF(0,0,w*d['progress'],h));details=dict(dynamic='progress',font_used=False)
   elif d['text']:
    existing_font(style['font']);render_text=d['text'].replace('\r\n','\n').replace('\r','\n').replace('\n','\u2028').replace('\u2029','\u2028');font=QFont(style['font']);font.setPointSizeF(style['size']*72/image.logicalDpiY());font.setBold(style['bold']);checked_font(font,render_text);layout=QTextLayout(render_text,font);option=QTextOption();option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere);option.setTextDirection(Qt.LayoutDirectionAuto);layout.setTextOption(option)
    fmt=QTextCharFormat();fmt.setForeground(QColor(style['color']));stroke=style.get('stroke_width',0)
    if stroke:fmt.setTextOutline(QPen(QColor(style.get('stroke_color','#30221b')),stroke*2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
    formats=QTextLayout.FormatRange();formats.start=0;formats.length=len(render_text.encode('utf-16-le'))//2;formats.format=fmt;layout.setFormats([formats]);lines=[];height=0.;layout.beginLayout()
    try:
     while True:
      line=layout.createLine()
      if not line.isValid():break
      line.setLineWidth(max(1,w-2*px));lines.append(line);height=max(height,(len(lines)-1)*style['line_spacing']+line.height()) if style.get('line_spacing') else height+line.height()
    finally:layout.endLayout()
    maximum=style.get('max_lines',0);widths=[line.naturalTextWidth() for line in lines];resolved=QFontInfo(font).family()
    details=dict(lines=len(lines),font_requested=style['font'],font_resolved=resolved,font_fallback=resolved.casefold()!=style['font'].casefold(),font_used=True,font_pixels=style['size'],native_size=[w,h],padding=[px,py],available_width=w-2*px,available_height=h-2*py,text_height=height,max_natural_width=max(widths,default=0.),max_lines=maximum,line_heights=[line.height() for line in lines[:128]],line_widths=widths[:128],line_metrics_omitted=max(0,len(lines)-128),font_resolution_note='Installed primary family and codepoint coverage verified; per-glyph fallback names not enumerated.')
    if (maximum and len(lines)>maximum) or height+2*py>h+1 or max(widths,default=0.)>w-2*px+1:
     raise TextFitError('text_overflow','Text does not fit its saved native bounds/padding/line limit. Make explicit parameter changes; no characters were dropped.',details)
    valign=style.get('valign','center');y=py if valign=='top' else h-py-height if valign=='bottom' else (h-height)/2
    for line in lines:
     line_width=line.naturalTextWidth();x=px if style['align']=='left' else w-px-line_width if style['align']=='right' else (w-line_width)/2;line.setPosition(QPointF(x,y));y+=style.get('line_spacing') or line.height()
    layout.draw(p,QPointF(0,0))
  finally:p.end()
  if measure_only:return dict(width=w,height=h,pts=d['key'],text_details=details)
  import numpy as np
  data=np.frombuffer(image.constBits(),np.uint8).reshape(h,image.bytesPerLine())[:,:w*4].reshape(h,w,4)[::-1].tobytes();return dict(width=w,height=h,pixel_aspect=1.,data=data,pts=d['key'],text_details=details)
 def augment(self,result):
  self.check();plan=result['plan'];descriptors=self.descriptors(plan);costs={d['key']:d['bytes'] for d in descriptors};scratch=max(costs.values(),default=0)
  if sum(costs.values())+scratch>self.limit:raise MemoryError('Active text/cache/scratch exceeds64MiB; no font pixels or accepted recipes reduced.')
  needed=set(costs);new=sum(n for k,n in costs.items() if k not in self.cache)
  for key in list(self.cache):
   if self.bytes+new+scratch<=self.limit and len(self.cache)+len(needed-self.cache.keys())<=128:break
   if key not in needed:self.bytes-=len(self.cache[key]['data']);del self.cache[key];self.stats.update(text_cache_bytes=self.bytes,text_cached_items=len(self.cache))
  images=dict(result['images']);visual=list(plan['visual']);details=[]
  for d in descriptors:
   key=d['key'];frame=self.cache.get(key)
   if frame is None:
    self.peak=max(self.peak,self.bytes+d['bytes']*2);frame=self.pixels(d);self.cache[key]=frame;self.bytes+=len(frame['data'])
   else:self.cache.move_to_end(key)
   row=d['item']['recipe'];style=row['style'];clip=dict(id=row['id'],name=(d['text'] or 'Timed progress')[:128],start=row['start'],duration=row['duration'],layout=dict(layout_defaults(),bounds=deepcopy(style['bounds']),opacity=style.get('opacity',1.),rotation=style.get('rotation',0.)));asset=dict(kind='Image',id=row['id'],sha256=key,location=dict(path=str(Path(__file__).resolve().parent/'__runtime_text__'/row['id'])),metadata={});item=dict(clip=clip,asset=asset,track=d['item']['track'],source_time=[0,1],draw_order=row['order']+1);visual.append(item);images[row['id']]=frame;details.append(dict(id=row['id'],**frame['text_details']))
  visual.sort(key=lambda r:(r['track']['order'],r.get('draw_order',0),r['clip']['start'],r['clip']['id']));updated=dict(plan,visual=visual);self.stats=dict(text_cache_bytes=self.bytes,text_active_bytes=sum(costs.values()),text_prepare_scratch_upper_bound=scratch,text_peak_owned_bytes=self.peak,text_cache_limit=self.limit,text_cached_items=len(self.cache),text_details=details,application_font_sources=dict(_registered_font_files));return dict(result,plan=updated,images=images)
 def close(self):self.cache.clear();self.bytes=0;self.closed=True;self.stats=dict(self.stats,text_cache_bytes=0,text_active_bytes=0,text_prepare_scratch_upper_bound=0,text_cached_items=0,closed=True)

def parse_srt(path,track,fps,operation_id,cancel):
 path=Path(path).resolve()
 if path.stat().st_size>2*1024*1024:fail('caption_capacity','SRT input exceeds2MiB; previous document retained.')
 with path.open('rb') as reader:raw=reader.read(2*1024*1024+1)
 if len(raw)>2*1024*1024:fail('caption_capacity','SRT grew beyond2MiB; previous document retained.')
 content=raw.decode('utf-8-sig');digest=hashlib.sha256(raw).hexdigest();changes=[];total=0;rate=Fraction(*fps)
 def stamp(value):
  match=re.fullmatch(r'(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})',value)
  if not match or int(match[2])>=60 or int(match[3])>=60:fail('invalid_caption','SRT timestamps must be HH:MM:SS,mmm.')
  return Fraction(int(match[1])*3600000+int(match[2])*60000+int(match[3])*1000+int(match[4]),1000)
 import uuid
 blocks=re.split(r'\r?\n\s*\r?\n',content.strip())
 for index,block in enumerate(blocks):
  if cancel.is_set():fail('cancelled','Caption preparation cancelled; accepted document retained.')
  lines=block.splitlines()
  if len(lines)<3 or not re.fullmatch(r'\d+',lines[0].strip()):fail('invalid_caption','Each SRT cue needs its source index, time range and text.')
  match=re.fullmatch(r'\s*(\S+)\s+-->\s+(\S+)\s*',lines[1])
  if not match:fail('invalid_caption','Unsupported SRT timing line; no fields were silently ignored.')
  begin,end=stamp(match[1]),stamp(match[2]);start=math.ceil(begin*rate);stop=math.ceil(end*rate);text='\n'.join(lines[2:]);total+=len(text.encode('utf8'))
  if stop<=start:fail('subframe_caption','Cue has no output frame at project FPS; retime it explicitly.')
  if total>MAX_DOCUMENT_BYTES or index>=4096:fail('caption_capacity','SRT caption metadata exceeds the project bound.')
  changes.append(dict(op='caption.add',id=uuid.uuid5(uuid.UUID(operation_id),'srt-'+str(index)).hex,track=track,start=start,duration=stop-start,text=text,provenance=dict(source_file=str(path),source_sha256=digest,source_cue=lines[0],source_start=[begin.numerator,begin.denominator],source_end=[end.numerator,end.denominator],alignment='Imported cue timing, not verified word alignment')))
 with path.open('rb') as reader:after=reader.read(2*1024*1024+1)
 if after!=raw:fail('changed_media','SRT changed during preparation; original project retained.')
 return [dict(op='project.protect',paths=[str(path)])]+changes
