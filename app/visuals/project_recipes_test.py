"""Real existing-owner editable recipe variants, conflicts, history and persistence."""
from pathlib import Path
from copy import deepcopy
import sys,os,json,time,uuid,traceback,threading
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);inputs=Path(sys.argv[2]);os.environ.update(QT_QPA_PLATFORM='offscreen',ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test',ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
from studio_control_client import ControlClient
from project_cli import request
from project_manifest import *
from project_text import evaluated
from project_visual import evaluated_text
client=None;checks=[];ns=uuid.uuid4().hex;ref=lambda s:dict(ref=s)
def state():return read_state(endpoint)
def op(action,**kw):
 r=request(endpoint,dict(op=action,operation_id=uuid.uuid4().hex,**binding(state()),**kw));assert r['ok'],r;return r
def run(plan,name):
 with journal_lock(out/name):return apply_plan(endpoint,Journal(out/name,plan))
def reject(manifest):
 before=stamp(state())
 try:compile_plan(endpoint,manifest);raise AssertionError('Expected recipe/override rejection')
 except ValueError:pass
 assert stamp(state())==before
try:
 client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);op('new',name='Recipe unit fixture',settings=dict(width=1920,height=1080,fps=[30,1]));media=[dict(key=k,name=k,kind=kind,path=str((inputs/p).resolve()),sha256=file_hash(inputs/p)) for k,kind,p in [('music','Audio','Music.wav'),('still','Image','Still.png')]]
 foundation=[dict(category='tracks',key=kind,values=dict(name=kind,kind='graphics' if kind=='captions' else kind,order=i)) for i,kind in enumerate(('video','audio','graphics','captions'))];recipes=[]
 for i in range(2):
  suffix='a' if i==0 else 'b';start=i*120;common=dict(start=start,duration=90)
  def add(kind,key,params):recipes.append(dict(key=key,kind=kind,version=1,params=params))
  add('entrance','intro-'+suffix,dict(common,track=ref('tracks:graphics'),brand='Brand '+suffix,game='Game '+suffix,enter_frames=6+i*6,exit_frames=8,parts=dict(brand=dict(size=54+i*4,color='#efb778' if i==0 else '#9cdec7'))))
  add('review_card','card-'+suffix,dict(common,track=ref('tracks:graphics'),heading='Review '+suffix,body='Ordinary editable body '+suffix,parts=dict(body=dict(bounds=[.12,.34,.76,.22],size=24+i*2))))
  add('chapter','chapter-'+suffix,dict(common,track=ref('tracks:graphics'),range_start=start-10 if i else 0,range_end=start+120,text='{elapsed} / {duration} • {frame}'))
  add('caption','caption-'+suffix,dict(common,track=ref('tracks:captions'),text='Caption '+suffix,style=dict(size=26+i*2,bounds=[.04,.84,.92,.12])))
  add('music','music-'+suffix,dict(common,track=ref('tracks:audio'),asset=ref('media:music'),name='Music '+suffix,source_in=[i,1],audio=dict(gain=.04+i*.01,fade_in=3+i,fade_out=6+i,envelope=[[0,1.],[25,.7],[40,.2],[65,.8],[89,1.]])))
  add('still','still-'+suffix,dict(common,track=ref('tracks:video'),asset=ref('media:still'),name='Still '+suffix,layout=dict(fit='Fit',bounds=[.1*i,.05,.8,.8])))
 manifest=dict(format=FORMAT,version=1,id=ns,project_id=state()['project_id'],media=media,sections=[dict(key='foundation',label='Recipe fixture: explicit tracks',items=foundation),dict(key='recipes',label='Recipe fixture: two independent variants',items=[],recipes=recipes)],save=dict(path=str((out/'recipes.zwv').resolve()),portable=True));(out/'MANIFEST_INPUT.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');plan=compile_plan(endpoint,manifest);(out/'PLAN.json').write_text(json.dumps(plan,indent=2),encoding='utf8');assert len(plan['recipes'])==12 and all(s['change_count']<=128 and s['wire_bytes']<=524288 for s in plan['steps']);result=run(plan,'apply');assembled=deepcopy(state()['document']);assert len(assembled['graphics'])==12 and len(assembled['captions'])==2 and len(assembled['clips'])==4
 assert all(r['provenance']['recipe']['version']==1 for category in ('graphics','captions','clips') for r in assembled[category]);checks.append('Twelve version1 recipe instances:two parameter variants of all six kinds expand to normal stable-ID entities/provenance,ordinary text keys/full audio arrays/source/still durations; bounded real owner batches')
 op('undo');assert not state()['document']['clips'] and not state()['document']['graphics'];op('redo');assert state()['document']==assembled;checks.append('One named recipe-section Undo/Redo restores every exact entity,style,key,dynamic range,envelope and source origin')
 find=lambda c,k:next(r for r in state()['document'][c] if r['id']==stable(ns,c,k))
 a=find('graphics','intro-a.brand');b=deepcopy(find('graphics','intro-b.brand'));music=find('clips','music-a');other_music=deepcopy(find('clips','music-b'));op('batch',label='Human override one recipe',changes=[dict(op='graphic.edit',id=a['id'],values=dict(text='Manual brand override',style=dict(size=63))),dict(op='clip.audio',id=music['id'],values=dict(gain=.071,envelope=[[0,1.],[30,.4],[89,.9]]))]);manual=deepcopy(state()['document']);assert find('graphics','intro-b.brand')==b and find('clips','music-b')==other_music;reject(manifest)
 with journal_lock(out/'apply'):resumed=apply_plan(endpoint,Journal(out/'apply'))
 assert resumed['status']=='complete' and not resumed['current_matches'] and state()['document']==manual;checks.append('Manual text/style/music envelope override changes only variantA; re-plan conflicts and resume reports historical completion/current_matches=false without overwrite or duplicates')
 op('undo');assert state()['document']==assembled
 # Origins are ordinary saved data, not a template playback clock.
 row=find('graphics','intro-a.brand');op('batch',label='Trim animated ordinary title',changes=[dict(op='graphic.edit',id=row['id'],values=dict(start=row['start']+1,duration=row['duration']-1))]);trimmed=deepcopy(state()['document']);assert find('graphics','intro-a.brand')['visual_window']['offset']==1;reject(manifest);assert state()['document']==trimmed;op('undo');assert state()['document']==assembled
 row=find('clips','music-a');op('batch',label='Trim ordinary music',changes=[dict(op='clip.trim',id=row['id'],start=row['start']+2,linked=False)]);assert find('clips','music-a')['audio_window']['offset']==2 and find('clips','music-a')['source_in']==[1,15];reject(manifest);op('undo');assert state()['document']==assembled;checks.append('Manual text/audio trims retain normal visual/audio curve origins; regeneration preserves/conflicts rather than flattening or resetting them')
 chapter=find('graphics','chapter-b.progress');assert evaluated(chapter,dict(frame=chapter['start'],settings=assembled['settings']))[1]==10/130
 title=find('graphics','intro-b.brand');assert evaluated_text(title,title['start'])['style']['opacity']==0 and evaluated_text(title,title['start']+12)['style']['opacity']==1;checks.append('Existing counter/progress ranges and existing opacity key evaluator use exact declared frames; no template runtime')
 for mutate in [lambda m:m['sections'][1]['recipes'][0].update(version=2),lambda m:m['sections'][1]['recipes'][0]['params'].update(enter_frames=90),lambda m:m['sections'][1]['recipes'][0]['params'].update(parts=dict(unknown={})),lambda m:m['sections'][1]['recipes'][0]['params'].update(style=dict(keys=[dict(parameter='opacity',points=[[0,1,'Linear']])]))]:
  bad=deepcopy(manifest);mutate(bad);reject(bad)
 checks.append('Unsupported versions,invalid timing,unknown part styles and duplicate opacity authoring reject read-only without changing accepted data')
 op('save',path=manifest['save']['path'],portable=True);saved=deepcopy(state()['document']);op('close');op('open',path=manifest['save']['path']);reopened=state()['document'];assert all(reopened[c]==saved[c] for c in ('clips','captions','graphics','tracks','buses'));assert [a['sha256'] for a in reopened['media']]==[a['sha256'] for a in saved['media']];plan=compile_plan(endpoint,manifest);assert len(plan['steps'])==1 and all(e['action']=='already applied' for e in plan['entities']);checks.append('Normal portable Save/owner Close/Open preserves every editable expanded entity,stable ID,provenance,complete array and media hash; rerun recognizes all items and only Save remains')
 op('close');client.close();assert client.process.returncode==0 and client.protocol_error_count==0;(out/'RESULT.json').write_text(json.dumps(dict(classification=__doc__,checks=checks,helper=result,resume=resumed,owner_exit=0,protocol_errors=0,unverified='Headless owner/model/evaluator; no natural native typing,GPU,device/listening or broad playback claim.'),indent=2),encoding='utf8');print('PASS',len(checks),out)
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
 if client and not client.closed:client.close(mode='discard',project_mode='discard')
