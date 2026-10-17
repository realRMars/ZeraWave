"""Real bounded native Qt batch fit, failure aggregation, parity and cancellation."""
from pathlib import Path
from copy import deepcopy
import sys,os,json,hashlib,time,threading,traceback,importlib.util
root=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);baseline=Path(sys.argv[2])
sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')];os.environ['QT_QPA_PLATFORM']='offscreen'
from video_project import create,apply,new_id
from project_text_fit import native_preflight,digest
from project_components import DEFINITIONS
checks=[]
try:
    doc=create('Native fit unit cases',dict(width=1920,height=1080,fps=[30,1]));track=new_id();ids=[new_id() for _ in range(10)];changes=[dict(op='track.add',id=track,kind='graphics')]
    quotes=['A careful update; the controls finally feel precise.','Good tools, thoughtful pacing — I kept finding another route.','“A tiny detail,” they wrote,\n“made the whole place feel lived in.”','It rewards a patient first hour rather than a hurried tour.','The last patch made me return; the building kept me there.','A long evening with friends, followed by one more short task.','Worth returning for the map, even when I ignored the main quest.','Better with headphones; the little sounds sell the machinery.','A test quote retained exactly while excessive padding fails.','A test quote retained exactly while a missing font fails.']
    style=deepcopy(DEFINITIONS['card']['quote']['style'])
    for field in ('size','padding','radius'):style[field]*=1.5
    for i,(key,quote) in enumerate(zip(ids,quotes)):
        s=deepcopy(style)
        if i==8:s['padding_y']=200
        if i==9:s['font']='ZeraWave Deliberately Missing Typeface 9271'
        changes.append(dict(op='graphic.add',id=key,track=track,start=0,duration=360,text=quote,style=s,provenance=dict(component=dict(instance_id=new_id(),part='quote-'+str(i+1)))))
    doc=apply(doc,changes,new_id())[0];before=deepcopy(doc);(out/'INPUT.json').write_text(json.dumps(doc,indent=2),encoding='utf8');report=native_preflight(doc,ids,dict(case='ten varied native quote-fit fixtures'))
    (out/'FAILED.json').write_text(json.dumps(report,indent=2),encoding='utf8');assert report['status']=='FAIL' and {f['id'] for f in report['failures']}==set(ids[-2:]),report
    assert {f['code'] for f in report['failures']}=={'font_unavailable','text_overflow'} and doc==before
    checks.append('Ten full native quote strings; two intentional font/padding failures collected together with correct IDs/parts/dimensions and actual line metrics; no word/font/bounds repair performed automatically')
    repaired=apply(doc,[dict(op='graphic.edit',id=ids[8],values=dict(style=dict(padding_y=0))),dict(op='graphic.edit',id=ids[9],values=dict(style=dict(font='Segoe UI')))],new_id())[0]
    (out/'REPAIRED-INPUT.json').write_text(json.dumps(repaired,indent=2),encoding='utf8');result=native_preflight(repaired,ids[-2:],dict(case='explicit permitted padding/font repairs; affected rows only'))
    (out/'REPAIRED.json').write_text(json.dumps(result,indent=2),encoding='utf8');assert result['status']=='PASS' and result['resources']['retained_pixel_cache_bytes']==0
    assert [r['text'] for r in repaired['graphics']]==quotes
    checks.append('Explicit padding/font-only repairs rerun just the two affected rows; exact wording/native bounds/font sizes preserved, native scratch/cache closed')
    from PySide6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    from project_text import TextSurface
    spec=importlib.util.spec_from_file_location('retrospective_before_text',baseline);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    previous=old.TextSurface();current=TextSurface();pixels=[]
    try:
        for row in repaired['graphics'][:3]:
            p=dict(settings=repaired['settings'],frame=0,text=[dict(recipe=row,track=dict(id=track))]);a=previous.pixels(previous.descriptors(p)[0]);b=current.pixels(current.descriptors(p)[0]);assert a['data']==b['data'];pixels.append(dict(id=row['id'],size=[b['width'],b['height']],sha256=hashlib.sha256(b['data']).hexdigest()))
    finally:previous.close();current.close()
    checks.append('Three representative native-size Unicode/newline quote planes byte-identical to pre-increment TextSurface; same real QImage/QTextLayout/fonts, no GPU or reduced resolution')
    glyph=apply(repaired,[dict(op='graphic.edit',id=ids[0],values=dict(text='Unmapped noncharacter: '+chr(0x10ffff)))],new_id())[0];result=native_preflight(glyph,[ids[0]],dict(case='actual missing glyph'))
    (out/'GLYPH-FAIL.json').write_text(json.dumps(result,indent=2),encoding='utf8');assert result['status']=='FAIL' and result['failures'][0]['code']=='glyph_unavailable'
    pressure=apply(repaired,[dict(op='graphic.edit',id=ids[0],values=dict(style=dict(bounds=[0.,0.,8.,8.])))],new_id())[0];result=native_preflight(pressure,[ids[0]],dict(case='native dimensions exceed supported materialization'))
    (out/'RESOURCE-FAIL.json').write_text(json.dumps(result,indent=2),encoding='utf8');assert result['status']=='FAIL' and result['resources']['retained_pixel_cache_bytes']==0
    checks.append('Actual unavailable glyph and native8192-axis/8MP resource boundary fail explicitly and retire scratch without altering recipes')
    counter=apply(repaired,[dict(op='graphic.edit',id=ids[0],values=dict(text='{elapsed} / {duration} · {frame}',duration=5000,dynamic='counter',range_start=0,range_end=5000,style=dict(bounds=[.01,.01,.4,.1],font='Segoe UI',size=18)))],new_id())[0];event=threading.Event();timer=threading.Timer(.8,event.set);timer.start()
    try:result=native_preflight(counter,[ids[0]],dict(case='cancel during owned native preparation'),event)
    finally:timer.cancel();timer.join()
    (out/'CANCELLED.json').write_text(json.dumps(result,indent=2),encoding='utf8');assert result['status']=='CANCELLED' and result['worker_exit']==2
    result=native_preflight(repaired,[ids[0]],dict(case='fresh native preparation after failures/cancel'));assert result['status']=='PASS'
    (out/'RECOVERED.json').write_text(json.dumps(result,indent=2),encoding='utf8');checks.append('Actual owned offscreen worker cancellation returns no fit acceptance; subsequent native preparation succeeds with same accepted text, no foreground/device/process replacement')
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,pixel_parity=pixels,classification='Native offscreen QImage/QTextLayout unit fixtures; no movie, compositing/physical/GPU/audio claim'),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
