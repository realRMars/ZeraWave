"""Existing owner/helper version2 components: native fit, overrides and persistence.

Same12s proof, task-owned copies of authorized native media. No GUI/GPU/device,
production edits, full movie or episode export. Separate Qt/motion evidence follows.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import sys,os,json,time,uuid,traceback,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);inputs=Path(sys.argv[3]);destination=Path(sys.argv[4]);assert not destination.exists()
os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test')
from studio_control_client import ControlClient
from project_cli import request
from project_manifest import compile_plan,apply_plan,journal_lock,Journal,read_state,binding,stamp,stable,file_hash,FORMAT,Conflict
from project_evaluator import Evaluator
from project_mixer import Mixer
from video_project import new_id,sample_at
client=None;checks=[];ns=new_id();ref=lambda key:dict(ref=key)
def state():return read_state(endpoint)
def op(kind,**values):
    r=request(endpoint,dict(op=kind,operation_id=new_id(),**binding(state()),**values));assert r['ok'],r;return r
def run(plan,name):
    with journal_lock(out/name):return apply_plan(endpoint,Journal(out/name,plan))
def rejected(plan,name):
    before=stamp(state())
    try:run(plan,name);raise AssertionError('Invalid plan applied')
    except Conflict:pass
    assert stamp(state())==before
def pcm_hash(d):
    m=Mixer();e=Evaluator(d,'component-pcm',1);h=hashlib.sha256();total=sample_at(d,360)
    try:
        for start in range(0,total,2048):h.update(m.render(e.audio_span(start,min(2048,total-start))).tobytes())
        return h.hexdigest()
    finally:m.close();assert m.budget.used==0
try:
    client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);op('open',path=str(proof));original=deepcopy(state()['document']);audio_before=pcm_hash(original)
    voice=next(c for c in original['clips'] if c['name']!='' and c['duration']==233);tail=next(c for c in original['clips'] if c['start']==240);voice_asset=next(a for a in original['media'] if a['id']==voice['asset']);music_asset=next(a for a in original['media'] if a['id']==tail['asset'])
    assert len(original['graphics'])==1 and len(original['clips'])==3
    op('batch',label='Proof: replace placeholders with explicit editable components',changes=[dict(op='clip.remove',id=voice['id'],linked=False),dict(op='clip.remove',id=tail['id'],linked=False),dict(op='graphic.remove',id=original['graphics'][0]['id'])]);base=deepcopy(state()['document'])
    source_inputs=json.loads((inputs/'INPUTS.json').read_text(encoding='utf8'));media=[]
    for row in source_inputs['sources']:
        media.append(dict(key=row['role'],name='Shared shot' if row['role'].startswith('moving-') else row['role'],kind='Video' if row['role'].startswith('moving-') else 'Image',path=row['path'],sha256=row['sha256']))
    tracks={role:ref('tracks:'+role) for role in ('background','picture','panel','images','text')};foundation=[dict(category='tracks',key=role,values=dict(name=role.title(),kind='video' if role in ('background','picture') else 'graphics',order=i+3)) for i,role in enumerate(tracks)]
    sections=[dict(key='foundation',label='Proof: component source/stack foundation',items=foundation)]
    quotes=['"A careful update; the controls finally feel precise."','"Good tools, thoughtful pacing — I kept finding another route."','“A tiny detail,” they wrote,\n“made the whole place feel lived in.”','"It rewards a patient first hour rather than a hurried tour."','"The last patch made me return; the building kept me there."','"A long evening with friends, followed by one more short task."','"Worth returning for the map, even when I ignored the main quest."','"Better with headphones; the little sounds sell the machinery."','"Exact wording survives a deliberate padding failure."','"Exact wording survives an unavailable font failure."']
    recipes=[]
    for i,quote in enumerate(quotes):
        source_in=Fraction(751,10) if i<2 else Fraction(755,10) if i==2 else Fraction(80+i) if i<8 else Fraction(15)
        asset=ref('media:moving-a' if i<8 else 'media:moving-b');source_out=source_in+Fraction(1,2)
        p=dict(tracks=tracks,start=i*15,duration=15,picture=dict(asset=asset,source_in=[source_in.numerator,source_in.denominator],source_out=[source_out.numerator,source_out.denominator],rate=[1,1]),author='LAYOUT TEST '+str(i+1),quote=quote,posted='Posted: synthetic layout fixture',playtime='No actual playtime claim',response='Explicit fixture response '+str(i+1)+'.',context='Not an actual Steam review',avatar=ref('media:avatar'))
        if i==8:p['parts']=dict(quote=dict(padding_y=200))
        if i==9:p['parts']=dict(quote=dict(font='ZeraWave Missing Fixture Font 7301'))
        recipe=dict(key='review-'+str(i+1),kind='review_card',version=2,params=p);recipes.append(recipe);sections.append(dict(key='card-'+str(i+1),label='Proof: editable quote card '+str(i+1),items=[],recipes=[recipe]))
    # A native counter exercises every relevant displayed state in this proof.
    sections.append(dict(key='chapter',label='Proof: retained version1 counter',items=[],recipes=[dict(key='chapter',kind='chapter',version=1,params=dict(track=tracks['text'],start=0,duration=180,text='{elapsed} / {duration} · {frame}',range_start=0,range_end=360,parts=dict(timer=dict(bounds=[.027,.09,.26,.06],size=24,padding=0),progress=dict(bounds=[.027,.985,.946,.005],color='#c7ff00'))))]))
    # One second of native moving footage is the explicit review->highlight boundary.
    highlight=dict(category='clips',key='highlight',values=dict(asset=ref('media:moving-b'),track=tracks['background'],name='Highlight boundary',start=150,duration=30,source_in=[15,1],rate=[1,1],layout=dict(fit='Fit')))
    sections.append(dict(key='highlight',label='Proof: exact review/highlight boundary',items=[highlight]))
    labels=['Enshrouded','Timberborn','Scrap Mechanic','Fields of Mistria','TCG Card Shop Simulator']
    outro=dict(key='outro',kind='outro',version=2,params=dict(tracks=tracks,start=180,duration=180,picture=dict(asset=ref('media:moving-b'),source_in=[16,1],source_out=[22,1],rate=[1,1]),question='WHICH ONE FINALLY GETS YOU OFF THE FENCE?',capsules=[dict(label=name,status='RELEASED / 1.0',asset=ref('media:capsule-'+str(i+1))) for i,name in enumerate(labels)],brand=ref('media:brand'),progress_range=[0,360],fade_frames=9,sendoff_frames=120,voice=dict(asset=voice['asset'],track=voice['track'],start=0,duration='natural',source_in=voice['source_in'],source_out=[31,4],rate=voice['rate'],audio=voice['audio'],pad_end='silence'),music=dict(asset=tail['asset'],track=tail['track'],start=240,duration=120,source_in=tail['source_in'],source_out=[12,1],rate=tail['rate'],audio=tail['audio'])))
    sections.append(dict(key='outro',label='Proof: branded moving outro and full voice/sendoff',items=[],recipes=[outro]))
    manifest=dict(format=FORMAT,version=1,id=ns,project_id=base['id'],settings=deepcopy(base['settings']),media=media,sections=sections,save=dict(path=str(destination),portable=True));before=stamp(state());failed=compile_plan(endpoint,manifest);assert stamp(state())==before and failed['text_fit']['status']=='FAIL'
    failures=failed['text_fit']['failures'];expected={stable(ns,'graphics','review-9.quote'),stable(ns,'graphics','review-10.quote')};assert {r['id'] for r in failures}==expected,failures
    (out/'FAILED-MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');(out/'FAILED-PLAN.json').write_text(json.dumps(failed,indent=2),encoding='utf8');rejected(failed,'refused-failed-fit')
    forged=deepcopy(failed);forged['text_fit']['status']='PASS';rejected(forged,'refused-changed-fit-status')
    checks.append('Real read-only plan expands ten full editable quote cards, moving outro and version1 timer; two native failures aggregate with exact part IDs and prevent ANY apply/history acceptance')
    recipes[8]['params']['parts']['quote']['padding_y']=0;recipes[9]['params']['parts']['quote']['font']='Segoe UI'
    good=compile_plan(endpoint,manifest);assert good['text_fit']['status']=='PASS',good['text_fit'];assert stamp(state())==before
    assert all(s['change_count']<=128 and s['wire_bytes']<=524288 for s in good['steps'])
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');(out/'PLAN.json').write_text(json.dumps(good,indent=2),encoding='utf8');result=run(good,'apply');assert result['status']=='complete'
    assembled=deepcopy(state()['document']);assert pcm_hash(assembled)==audio_before
    assert [next(r['text'] for r in assembled['graphics'] if r['id']==stable(ns,'graphics','review-'+str(i+1)+'.quote')) for i in range(10)]==quotes
    v=next(c for c in assembled['clips'] if c['id']==stable(ns,'clips','outro.voice'));m=next(c for c in assembled['clips'] if c['id']==stable(ns,'clips','outro.music'));assert v['start']+v['duration']==233<=240 and m['start']==240 and m['duration']==120 and m['audio']['fade_out']==9
    checks.append('Explicit font/padding repairs preserve every word/size/bounds; normal bounded helper apply creates ordinary stable-ID parts, full233frame voice before120frame sendoff/fade; entire12s canonical PCM bit-identical to prior proof')
    first=stable(ns,'graphics','review-1.quote');others=deepcopy([r for r in assembled['graphics'] if r['id']!=first]);op('batch',label='Manual component quote edit',changes=[dict(op='graphic.edit',id=first,values=dict(text='Explicit manual wording; other instances stay intact.'))]);manual=deepcopy(state()['document']);assert [r for r in manual['graphics'] if r['id']!=first]==others and state()['undo_label']=='Manual component quote edit'
    try:compile_plan(endpoint,manifest);raise AssertionError('Manual override erased')
    except Conflict:pass
    op('undo');assert state()['document']==assembled;op('redo');assert state()['document']==manual;op('undo');assert state()['document']==assembled
    checks.append('One instance remains normally editable with descriptive Undo/Redo and exact other-instance preservation; guarded regeneration conflicts instead of replacing a manual edit')
    tampered=deepcopy(good);tampered['steps'][-1]['request']['path']=str(out/'wrong-plan.zwv');rejected(tampered,'refused-tampered-plan')
    op('save',path=str(destination),portable=True);saved=deepcopy(state()['document']);op('close');op('open',path=str(destination));reopened=state()['document'];assert all(reopened[k]==saved[k] for k in ('clips','graphics','captions','tracks','buses','master'));assert pcm_hash(reopened)==audio_before
    checks.append('Exact-plan/source certificate rejects changed plan before submission; normal portable Save/Close/Open preserves all editable parts/keys/routing/source hashes and canonical PCM')
    (out/'PROOF-IDENTITY.json').write_text(json.dumps(dict(project=reopened['id'],namespace=ns,path=str(destination),sha256=file_hash(destination),source_names=[(a['name'],a['sha256']) for a in reopened['media']],voice_id=v['id'],music_id=m['id'],canonical_pcm_sha256=audio_before),indent=2),encoding='utf8')
    op('close');client.close();assert client.process.returncode==0 and client.protocol_error_count==0;client=None
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,proof=str(destination),canonical_pcm_sha256=audio_before,classification=__doc__,owner_exit=0),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
    if client and not client.closed:client.close(mode='discard',project_mode='discard')
