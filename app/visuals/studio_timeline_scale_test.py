"""500-item Qt widget navigation, not physical/display or owner latency proof."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import sys,os,time,json,traceback,statistics
root=Path(__file__).resolve().parents[2] if Path(__file__).parent.name=='visuals' else Path(r'C:\ZeraWave');sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication,QLabel
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from studio_timeline import TimelinePanel
from video_project import validate
from studio_video_workspace import clock_text
app=QApplication([]);out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);d=validate(json.loads(Path(sys.argv[2]).read_text('utf8'))['document']);assert len(d['clips'])==500 and len(d['tracks'])==12;samples=[];checks=[];notice=QLabel();shell=SimpleNamespace(safe=lambda f:f(),statusBar=lambda:SimpleNamespace(showMessage=lambda s:None));w=SimpleNamespace(shell=shell,notice=notice,pending=None,trees={},binding=lambda:dict(expected_epoch='widget-only',expected_revision=0),state=lambda:dict(document=d,epoch='widget-only',revision=0,media={}),transport_state=lambda:dict(frame=0,end=15000),transport=lambda *a,**k:None,add_track=lambda:None,document=lambda:d)
try:
 p=TimelinePanel(w);w.timeline=p;p.closed=True # This widget-only check does not own decoder preparation.
 p.resize(1500,850);p.show();c=p.canvas;p.refresh();app.processEvents();p.refresh();app.processEvents();geometry=id(c.rects);document=id(c.document);before=deepcopy(c.document)
 for index in range(100):
  row=d['clips'][index%len(d['clips'])];point=c.rects[('clips',row['id'])].center().toPoint();began=time.perf_counter();QTest.mouseClick(c,Qt.LeftButton,Qt.ControlModifier,point);app.processEvents();samples.append(dict(kind='ctrl-selection',ms=(time.perf_counter()-began)*1000));assert id(c.rects)==geometry and id(c.document)==document
 assert c.document==before and len(c.selection)==100;checks.append('100 Qt individual selections in500 clips preserve geometry/document object identity and exact recipes; no per-pointer deep copy/reindex')
 for index in range(60):
  began=time.perf_counter();p.zoom(1.02 if index%2==0 else 1/1.02);p.scroll.horizontalScrollBar().setValue(index*45);p.scroll.verticalScrollBar().setValue(index*3);app.processEvents();p.refresh();app.processEvents();samples.append(dict(kind='zoom-scroll',ms=(time.perf_counter()-began)*1000));assert p.header_scroll.verticalScrollBar().value()==p.scroll.verticalScrollBar().value()
 p.fit(False);p.fit(True);p.height_control.setValue(92);assert c.row_height==92 and all(q.height()==92 for q in p.headers.widgets.values());settings=p.view_settings();p.height_control.setValue(64);p.restore_view(settings);assert p.view_settings()==settings and c.document==before;checks.append('60 offscreen zoom/scroll paints, Fit Project/Selection, fixed synchronized headers, track heights and valid view preference restore leave content intact')
 p.restore_view(dict(version=1,scale=float('nan'),height=92));assert p.view_settings()==settings
 fps=[30000,1001]
 for frame in (0,1,29,30,299,899,30000,107892):
  from fractions import Fraction
  ms=int(Fraction(frame*1000*fps[1],fps[0]));assert clock_text(frame,fps).endswith(f'{ms%1000:03}')
 checks.append('Malformed view settings reject intact; fractional-rate clock formatting remains rational at near-second/hour boundaries')
 p.close_resources();p.close();end=time.monotonic()+20
 while not p.exited():app.processEvents();assert time.monotonic()<end;time.sleep(.002)
 stats={}
 for kind in {r['kind'] for r in samples}:
  values=sorted(r['ms'] for r in samples if r['kind']==kind);stats[kind]=dict(count=len(values),median=statistics.median(values),p95=values[int(.95*(len(values)-1))],p99=values[int(.99*(len(values)-1))],maximum=max(values),stalls_over_250=sum(x>250 for x in values))
 (out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,samples=samples,statistics=stats,counts=dict(clips=len(c.rects),tracks=len(p.headers.widgets))),indent=2),'utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
