"""Pure bounded review/mapping/dependency policy, no codec/Qt/GPU/device/export.

Uses the same saved12s proof plus a rational-clock model fixture. Ready media
states here are controlled snapshots, not fresh file verification or listening.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from unittest.mock import patch
import sys,json,threading,traceback,time
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);checks=[];samples=[]
from project_review import inspect_review,source_interval,remember_change,marks,query_from_mark,export_request,export_review_project,MARK_KEY,MARKS,digest
from video_project import create,apply,validate,new_id,ProjectError,pair,rational
import hashlib
source_files=['project_review.py','project_review_test.py','video_project.py','project_source.py','project_audio_timing.py','project_visual.py','project_audio_graph.py','project_export.py']
source_hashes={name:hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest() for name in source_files};(out/'SOURCE.json').write_text(json.dumps(source_hashes,indent=2),encoding='utf8')
d=json.loads(proof.read_text(encoding='utf8'))['document'];media={a['id']:dict(status='Ready',expected=a['sha256']) for a in d['media']};binding=dict(expected_epoch='review-model',expected_revision=0,expected_project=d['id'],expected_command=0)
clip=next(c for c in d['clips'] if c['provenance'].get('component',{}).get('instance_key')=='review-1' and c['provenance']['component']['part']=='background');asset=next(a for a in d['media'] if a['id']==clip['asset']);span=source_interval(d,clip,asset)
q=dict(op='review_inspect',**binding,source=asset['id'],source_range=[pair(x) for x in span],handles=[18,30],range=[90,210],purpose='Review to highlight context',clip=clip['id'])
def report(doc=d,query=q,rev=0,states=None):
    began=time.perf_counter_ns();value=inspect_review(doc,'review-model',rev,query,media if states is None else states);samples.append((time.perf_counter_ns()-began)/1e6);return value
def refused(fn,code):
    try:fn();raise AssertionError('Invalid review admitted')
    except ProjectError as exc:assert exc.code==code,(exc.code,str(exc))
try:
    before=deepcopy(d);r=report();assert r['status']=='ready' and d==before
    assert r['source']['fps']==[60,1] and r['source']['effective_handled_interval']==[[374,5],[761,10]]
    assert r['mapping']['handled_interval_sequence_frames']==[[-9,1],[30,1]] and r['mapping']['suggested_sequence_range']==[0,30]
    rows=r['duplicate_use']['rows'];assert len([x for x in rows if x['handled_overlap']])>=4 and any(x['handled_overlap'] is None for x in rows)
    assert {x['source_sha256'] for x in rows}=={asset['sha256']};other=next(a for a in d['media'] if a['name']==asset['name'] and a['sha256']!=asset['sha256']);assert not any(x['asset']==other['id'] for x in rows)
    paged=report(query=dict(q,limit=2));assert paged['duplicate_use']['next_offset']==2 and len(paged['duplicate_use']['rows'])==2
    assert all(x['component'].get('role') in ('background','picture') for x in rows)
    checks.append('Exact60-to30FPS handled mapping/clamps, overlapping/disjoint same-SHA uses and intentional component roles; same-name different SHA excluded, complete duplicate count with bounded paging; no document mutation')
    low=report(query=dict(q,source_range=[[0,1],[1,1]],handles=[120,999999]));assert low['source']['clamped']==[True,True] and low['source']['effective_handled_interval']==[[0,1],low['source']['natural_end']]
    refused(lambda:report(query=dict(q,source_range=[[0,1],[99999,1]])),'source_range');refused(lambda:report(query=dict(q,handles=[True,0])),'invalid_time');refused(lambda:report(query=dict(q,range=[210,90])),'invalid_range')
    audio=next(a for a in d['media'] if a['kind']=='Audio' and a['metadata'].get('sample_count')==372000)
    tail=report(query=dict(q,source=audio['id'],clip=None,source_range=[[0,1],[233,30]],handles=[0,0]));assert tail['source']['selection_end_padding']==[1,60] and tail['source']['effective_handled_interval'][1]==[31,4]
    checks.append('Source start/end handles clamp transparently; invalid selected intervals/booleans/reversed sequence rejected; partial natural audio end discloses800samples padding rather than invented coverage')
    m=create(settings=dict(fps=[30000,1001]));aid,tid,cid=[new_id() for _ in range(3)];m=apply(m,[dict(op='media.add',id=aid,name='Rational grid',kind='Video',location=dict(kind='external',path='C:/task-only/rational.mp4'),sha256='a'*64,metadata=dict(duration=20,rational_fps=[24000,1001],has_audio=True)),dict(op='track.add',id=tid,kind='video'),dict(op='clip.add',id=cid,asset=aid,track=tid,start=30,duration=60,source_in=[2,1],rate=[3,2])],new_id())[0];end=Fraction(2)+Fraction(60)/Fraction(30000,1001)*Fraction(3,2)
    fractional=dict(op='review_inspect',expected_epoch='fractional',expected_revision=0,expected_project=m['id'],source=aid,source_range=[[2,1],pair(end)],handles=[1,2],range=[0,90],purpose='Exact rational handles',clip=cid)
    rr=inspect_review(m,'fractional',0,fractional,{aid:dict(status='Ready')});assert rr['mapping']['handled_interval_sequence_frames']==[[175,6],[275,3]]
    checks.append('Exact24000/1001 Source grid,30000/1001 sequence and3/2 rate preserve fractional mapped boundaries, no nominal-FPS rounding')
    from project_source import prepare_source,SourceContext
    partial=deepcopy(asset);partial['location']=dict(kind='external',path='C:/task-only/partial-video.mp4');partial['metadata'].update(duration_time=[445001,4000],duration=111.25025)
    with patch('project_service.prepare_changes',return_value=[dict(op='media.add',**partial)]):source_document=prepare_source(partial,new_id(),threading.Event())
    context=SourceContext();context.install(source_document);empty=create('Empty source authoring');eb=dict(expected_epoch='empty-model',expected_project=empty['id'],expected_revision=0,expected_command=0);source_query=dict(op='review_inspect',**eb,source=partial['id'],source_epoch=context.epoch,source_range=[[111,1],[445001,4000]],handles=[0,100],range=None,purpose='Source-only before placement',clip=None)
    sr=inspect_review(empty,'empty-model',0,source_query,{},context.state());assert sr['status']=='ready' and sr['sequence']['range'] is None and sr['source']['grid_end']==context.state()['transport']['end']==6675 and sr['source']['grid_out_clamped']
    assert sr['source']['effective_handled_interval'][1]==[445001,4000] and sr['source']['auditionable_interval'][1]==[445,4];context.transport.command('range',sr['source']['effective_grid'])
    refused(lambda:export_request(sr,eb,str(out/'no-timeline.mp4'),new_id()),'no_review_sequence');note=apply(empty,[remember_change(empty,sr,new_id(),eb)],new_id())[0];assert marks(note)['items'][0]['sequence_range'] is None and not note['clips'] and not note['media'];mq=query_from_mark(note,marks(note)['items'][0],eb,context.state());assert inspect_review(note,'empty-model',0,mq,{},context.state())['status']=='ready'
    checks.append('Source-only inspection/handles/ordinary note work before any timeline placement; actual SourceContext/prepare_source floor6675 honored for fractional Video EOF while exact natural end remains separate; no mixed export invented (source preparation header mocked, no codec)')
    renamed=apply(d,[dict(op='project.rename',name='Unrelated project label')],new_id())[0];q1=dict(q,expected_revision=1,prior=r['certificate']);validated=report(renamed,q1,1);assert validated['status']=='ready' and validated['validation']['unchanged_dependencies'] and validated['certificate']['origin']==r['certificate']['origin'] and validated['binding']['revision']==1 and r['binding']['revision']==0
    affected=[];voice=next(c for c in d['clips'] if c['provenance'].get('component',{}).get('part')=='voice');graphic=next(g for g in d['graphics'] if g['start']==90)
    picture=next(c for c in d['clips'] if c['start']==90 and c['provenance'].get('component',{}).get('part')=='background');right=next(c for c in d['clips'] if c['start']==105 and c['track']==picture['track']);bus=new_id()
    edits=[('clip-gain',dict(op='clip.audio',id=voice['id'],values=dict(gain=.31))),('clip-envelope',dict(op='clip.audio',id=voice['id'],values=dict(envelope=[[0,.8],[200,.2]]))),('track-gain',dict(op='track.audio',id=voice['track'],values=dict(gain=.8))),('master',dict(op='master.audio',values=dict(gain=.7))),('text-style',dict(op='graphic.edit',id=graphic['id'],values=dict(style=dict(graphic['style'],opacity=.6)))),('text-key',dict(op='keyframe.set',id=graphic['id'],parameter='opacity',frame=2,value=.4)),('picture-effect',dict(op='effect.add',id=picture['id'],kind='Brightness',amount=.7)),('picture-mask',dict(op='clip.layout',id=picture['id'],values=dict(masks=[dict(mode='Keep',enabled=True,points=[[0,0],[1,0],[1,1],[0,1]])]))),('trim',dict(op='clip.trim',id=picture['id'],start=91,end=105,linked=False)),('transition',dict(op='transition.add',left=picture['id'],right=right['id'],duration=6)),('bus-route',[dict(op='bus.add',id=bus,name='Explicit contribution',gain=.7),dict(op='track.output',id=voice['track'],output=bus)])]
    for name,edit in edits:
        changed=apply(d,edit if isinstance(edit,list) else [edit],new_id())[0];value=report(changed,q1,1);assert value['status']=='outdated' and not value['certificate']['ready'],name;affected.append(name)
        again=report(changed,dict(q1,prior=value['certificate']),1);assert again['status']=='outdated' and again['certificate']['origin']==r['certificate']['origin'],name
    for name,change in [('global-solo',lambda z:next(t for t in z['tracks'] if t['kind']=='audio').update(solo=True)),('source-replacement',lambda z:next(a for a in z['media'] if a['id']==asset['id']).update(sha256='f'*64)),('source-location',lambda z:next(a for a in z['media'] if a['id']==asset['id'])['location'].update(kind='external',path='C:/task-only/relinked.mp4')),('outside-range-end',lambda z:z['graphics'][-1].update(start=360,duration=2))]:
        changed=deepcopy(d);change(changed);value=report(changed,q1,1);assert value['status'] in ('outdated','unavailable'),name;affected.append(name)
    missing=deepcopy(media);missing[asset['id']]['status']='Missing';assert report(query=dict(q,prior=r['certificate']),states=missing)['status']=='unavailable'
    refused(lambda:report(query=dict(q,expected_epoch='wrong')),'stale_revision');cancel=threading.Event();cancel.set();refused(lambda:inspect_review(d,'review-model',0,q,media,cancel=cancel),'cancelled')
    checks.append('Explicit later validation preserves original provenance only after unchanged fingerprint; affected gain/envelope/track/Master/style/global-solo/source/location/sequence-end and availability invalidation; wrong binding/cancel refused: '+','.join(affected))
    markid=new_id();change=remember_change(d,r,markid,binding);remembered=apply(d,[change],new_id())[0];mark=marks(remembered)['items'][0];assert mark['purpose']==q['purpose'] and mark['source_sha256']==asset['sha256'] and mark['sequence_range']==[90,210]
    saved_query=query_from_mark(remembered,mark,binding);assert report(remembered,saved_query)['status']=='ready'
    bad=deepcopy(change);bad['values'][MARK_KEY]['items'][0]['handles']=[-1,2];refused(lambda:apply(d,[bad],new_id()),'invalid_time');assert d==before
    wrong=deepcopy(remembered);next(a for a in wrong['media'] if a['id']==asset['id'])['sha256']='f'*64;refused(lambda:query_from_mark(wrong,mark,binding),'missing_source');assert marks(wrong)['items'][0]==mark
    foreign=deepcopy(d);foreign['provenance'][MARK_KEY]={'historical':'preserve unknown metadata'};assert validate(foreign)['provenance'][MARK_KEY]==foreign['provenance'][MARK_KEY];refused(lambda:marks(foreign),'unsupported_fields')
    full=dict(format=MARKS,version=1,items=[dict(mark,id=new_id()) for _ in range(65)]);refused(lambda:apply(d,[dict(op='project.provenance',values={MARK_KEY:full})],new_id()),'review_mark_capacity')
    checks.append('Compatible ordinary provenance/validation retains exact purpose/ranges/hash/IDs; bad/oversized authored metadata rejects atomically, missing source preserves note, unknown historical collision stays intact and is not reinterpreted')
    request=export_request(r,binding,str(out/'sample.mp4'),new_id());assert request['range']==[90,210]
    refused(lambda:export_request(r,dict(binding,expected_revision=1),str(out/'bad.mp4'),new_id()),'outdated_review')
    with patch('project_export.export_project',return_value={'mocked_export':True}) as existing:
        result=export_review_project(d,'review-model',0,str(out/'not-rendered.mp4'),18,str(out/'not-created'),threading.Event(),[],[90,210],media,{},r['certificate']);assert existing.call_count==1 and result['review_sample']==r['certificate']
    changed=apply(d,[edits[0][1]],new_id())[0]
    with patch('project_export.export_project',side_effect=AssertionError('Wrong dependencies started graphics export')) as existing:
        refused(lambda:export_review_project(changed,'review-model',0,str(out/'bad.mp4'),18,str(out/'not-created'),threading.Event(),[],[90,210],media,{},r['certificate']),'outdated_review');assert existing.call_count==0
    checks.append('Script request builder pins revision/range/certificate; ordinary exporter wrapper accepts unchanged input and rejects tampered dependencies BEFORE any graphics process (export mocked, no movie produced)')
    assert all(hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest()==sha for name,sha in source_hashes.items());(out/'REPORT.json').write_text(json.dumps(r,indent=2),encoding='utf8');(out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,raw_report_ms=samples,classification=__doc__,exports_executed=0,source_unchanged=True),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:
    (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,raw_report_ms=samples),indent=2),encoding='utf8');raise
