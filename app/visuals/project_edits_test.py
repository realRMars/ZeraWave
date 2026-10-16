"""Pure timeline contracts; no native input, decode, output or display claim."""
from pathlib import Path
from copy import deepcopy
import sys,json,uuid,time,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
import video_project as v
from project_evaluator import Evaluator
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[]
id=lambda:uuid.uuid4().hex
def edit(d,*changes):return v.apply(d,list(changes),id())
def reject(d,code,change):
 before=deepcopy(d)
 try:edit(d,change)
 except v.ProjectError as exc:assert exc.code==code,(exc.code,str(exc))
 else:raise AssertionError('Expected '+code)
 assert d==before
def row(d,key):return next(r for c in ('clips','captions','graphics') for r in d[c] if r['id']==key)
try:
 asset,video,audio,video2,audio2,text,link,vc,ac,caption=[id() for _ in range(10)]
 base,_=edit(v.create('Edit contracts',dict(width=1920,height=1080,fps=[30,1])),dict(op='media.add',id=asset,name='AV',kind='Video',sha256='a'*64,location=dict(kind='external',path=r'C:\fixtures\av.mp4'),metadata=dict(duration=60.,has_audio=True)),*[dict(op='track.add',id=k,kind=kind,name=name) for k,kind,name in ((video,'video','Picture'),(audio,'audio','Sound'),(video2,'video','Other picture'),(audio2,'audio','Other sound'),(text,'graphics','Text'))],dict(op='clip.add',id=vc,asset=asset,track=video,start=0,duration=90,link_id=link,audio=dict(fade_in=10,fade_out=10)),dict(op='clip.add',id=ac,asset=asset,track=audio,start=0,duration=90,link_id=link),dict(op='caption.add',id=caption,track=text,start=100,duration=30,text='Later caption'))
 moved,_=edit(base,dict(op='items.move',ids=[vc],delta=10));assert row(moved,vc)['start']==row(moved,ac)['start']==10 and row(base,vc)['start']==0
 reject(base,'invalid_track',dict(op='items.move',ids=[vc],delta=10,track_map={vc:audio}));checks.append('Linked movement preserves source/IDs and atomically rejects incompatible target')
 locked,_=edit(base,dict(op='track.edit',id=audio,values=dict(locked=True)))
 reject(locked,'track_locked',dict(op='items.move',ids=[vc],delta=10));reject(locked,'track_locked',dict(op='clip.trim',id=vc,start=5));reject(locked,'track_locked',dict(op='track.remove',id=video,confirmed=True));checks.append('Both high-level and legacy primitive edits respect a locked linked partner atomically')
 trimmed,_=edit(base,dict(op='items.trim',id=vc,start=10,end=90));assert row(trimmed,vc)['source_in']==[1,3] and row(trimmed,vc)['audio_window']==dict(offset=10,duration=90)
 split,created=edit(trimmed,dict(op='items.split',ids=[vc],at=45));assert len(created)==2 and len(split['clips'])==4
 rights=[row(split,k) for k in created];assert all(r['source_in']==[3,2] and r['audio_window']['offset']==45 for r in rights) and rights[0]['link_id']==rights[1]['link_id']!=link
 same,created=edit(trimmed,dict(op='items.split',ids=[vc],at=10));assert same==trimmed and not created
 reject(base,'invalid_time',dict(op='items.trim',id=vc,start=90,end=90));reject(base,'source_range',dict(op='items.trim',id=vc,start=0,end=2000));checks.append('Nondestructive linked trim/split preserve exact source and fade origin; endpoints no-op and invalid handles reject')
 grouped,_=edit(base,dict(op='items.group',ids=[vc,caption]));group=row(grouped,vc)['group_id'];assert row(grouped,caption)['group_id']==group
 moved_group,_=edit(grouped,dict(op='items.move',ids=[caption],delta=5));assert [row(moved_group,k)['start'] for k in (vc,ac,caption)]==[5,5,105]
 copied=[dict(category=c,row=deepcopy(r)) for c in ('clips','captions') for r in grouped[c]]
 pasted,created=edit(grouped,dict(op='items.paste',rows=copied,at=150,track_map={video:video,audio:audio,text:text}));assert len(created)==3 and not set(created)&{vc,ac,caption};clones=[row(pasted,k) for k in created];pair=[r for r in clones if 'asset' in r];assert pair[0]['link_id']==pair[1]['link_id']!=link and all(r.get('group_id')!=group for r in clones)
 assert all(row(pasted,k)==row(grouped,k) for k in (vc,ac,caption));checks.append('Group movement includes linked companions; paste remaps independent item/link/group IDs without changing originals')
 inserted_row=v.clip_recipe(id(),asset=asset,track=video,start=20,duration=10)
 reject(base,'collision',dict(op='items.place',rows=[dict(category='clips',row=inserted_row)]))
 inserted,created=edit(base,dict(op='items.place',rows=[dict(category='clips',row=inserted_row)],mode='Insert'));assert len(inserted['clips'])==5 and row(inserted,caption)['start']==110
 right=[r for r in inserted['clips'] if r['start']==30];assert len(right)==2 and all(r['source_in']==[2,3] for r in right) and right[0]['link_id']==right[1]['link_id']
 reject(base,'linked_scope',dict(op='items.place',rows=[dict(category='clips',row=inserted_row)],mode='Insert',scope=[video]))
 locked_text,_=edit(base,dict(op='track.edit',id=text,values=dict(locked=True)));reject(locked_text,'track_locked',dict(op='items.place',rows=[dict(category='clips',row=inserted_row)],mode='Insert'));checks.append('Normal collisions reject; Insert splits source-aligned AV and shifts synchronized captions; narrow sync/locked scopes reject')
 reject(base,'linked_scope',dict(op='items.place',rows=[dict(category='clips',row=inserted_row)],mode='Overwrite'))
 new_link=id();replacements=[dict(category='clips',row=v.clip_recipe(id(),asset=asset,track=t,start=20,duration=10,link_id=new_link)) for t in (video,audio)]
 reject(base,'invalid_scope',dict(op='items.place',rows=[dict(category='clips',row=inserted_row)],mode='Insert',scope=[text]))
 reject(base,'invalid_scope',dict(op='items.place',rows=replacements,mode='Insert',scope=[video,text]))
 narrower,_=edit(base,dict(op='items.place',rows=replacements,mode='Insert',scope=[video,audio]));assert row(narrower,caption)['start']==100 and len(narrower['clips'])==6
 checks.append('Insert rejects omitted destination tracks atomically, including linked AV; explicit narrower scope including both targets preserves unrelated caption timing')
 overwritten,_=edit(base,dict(op='items.place',rows=replacements,mode='Overwrite'));assert row(overwritten,caption)['start']==100 and len(overwritten['clips'])==6
 right=[r for r in overwritten['clips'] if r['start']==30];assert len(right)==2 and all(r['source_in']==[1,1] for r in right);assert row(overwritten,vc)['duration']==20
 checks.append('Overwrite preserves unrelated timing and both source-aligned outside pieces; external linked partners reject atomically')
 removed,_=edit(base,dict(op='items.delete',ids=[vc]));assert not removed['clips'] and row(removed,caption)['start']==100
 rippled,_=edit(base,dict(op='items.delete',ids=[vc],ripple=True));assert not rippled['clips'] and row(rippled,caption)['start']==10
 reject(base,'confirmation_required',dict(op='track.remove',id=video));deleted,_=edit(base,dict(op='track.remove',id=video,confirmed=True));assert not deleted['clips'] and video not in {t['id'] for t in deleted['tracks']};checks.append('Ordinary Delete leaves gaps; Ripple closes the exact interval; confirmed track deletion accounts for linked content')
 soloed,_=edit(base,dict(op='track.edit',id=audio2,values=dict(solo=True)));solo_plan=Evaluator(soloed,'test',0).audio_span(0,128)
 from project_mixer import Mixer
 import numpy as np
 mix=Mixer()
 try:assert not np.any(mix.render(solo_plan)) # ineligible source is never opened
 finally:mix.close()
 hidden,_=edit(base,dict(op='track.edit',id=video,values=dict(visible=False)));assert not Evaluator(hidden,'test',0).at(0)['visual'];assert len(Evaluator(base,'test',0).at(0)['visual'])==1
 reordered,_=edit(base,dict(op='track.move',id=text,order=0));assert next(t for t in reordered['tracks'] if t['id']==text)['order']==0;assert len({t['order'] for t in reordered['tracks']})==5
 reject(base,'reference_in_use',dict(op='media.remove',ids=[asset]));checks.append('Track visibility reaches evaluator; canonical Mixer applies Solo without opening an ineligible source; reorder retains identities and used source references cannot be removed')
 for change in (dict(op='items.move',ids=[{}],delta=1),dict(op='items.place',rows=[dict(category='clips',row={})]),dict(op='track.edit',id=audio,values=dict(locked=1))):
  try:edit(base,change)
  except v.ProjectError:pass
  else:raise AssertionError('Malformed edit accepted')
 legacy=deepcopy(base);legacy['version']=1;legacy.pop('buses',None);legacy.pop('master',None);assert v.validate(legacy)==legacy;noop,_=edit(legacy,dict(op='items.split',ids=[vc],at=0));assert noop==legacy;upgraded,_=edit(legacy,dict(op='track.edit',id=video,values=dict(locked=True)));assert upgraded['version']==v.VERSION
 checks.append('Malformed commands reject; exact schema1 read and endpoint no-op preserve old document; a genuine new edit upgrades current schema without altering legacy no-op')
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,classification=__doc__),indent=2),'utf8');print('PASS',len(checks))
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks),indent=2),'utf8');raise
