"""Bounded source/timeline review recipes over the existing document and owner.

No decoder, transport, device, graphics context or editable mirror. Reports use
dated owner source verification; actual export independently verifies source bytes.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib,json
from video_project import fields,identity,integer,text,rational,pair,duration,validate,fail
from project_audio_timing import natural_duration,ceiling

FORMAT='zerawave-source-review'
CERTIFICATE='zerawave-review-certificate'
MARKS='zerawave-source-review-marks'
MARK_KEY='zerawave_source_review_marks'
MAX_MARKS=64
MAX_REPORT=1024*1024

def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def check(cancel):
    if cancel is not None and cancel.is_set():fail('cancelled','Source review cancelled; no edit or automatic retry.')
def bound(document,epoch,revision):return dict(project=document['id'],epoch=epoch,revision=revision)
def interval(value):
    if not isinstance(value,list) or len(value)!=2:fail('invalid_range','Source interval is two rational seconds: [In,exclusive Out].')
    left,right=map(rational,value)
    if not 0<=left<right:fail('invalid_range','Source In must precede exclusive Out and be nonnegative.')
    return left,right
def source_fps(asset,source=None):
    value=asset['metadata'].get('rational_fps') or ((source or {}).get('document') or {}).get('settings',{}).get('fps') or [30,1]
    fps=rational(value)
    if fps<=0:fail('invalid_time','Source nominal frame grid must be positive.')
    return fps
def extent(asset,fps):return 1/fps if asset['kind']=='Image' else natural_duration(asset['metadata'])
def source_grid_end(asset,fps):
    from project_audio_timing import natural_frames
    return 1 if asset['kind']=='Image' else natural_frames(asset['metadata'],pair(fps)) if asset['kind']=='Audio' else max(1,int(extent(asset,fps)*fps))
def overlaps(row,left,right):return row['start']<right and row['start']+row['duration']>left
def source_interval(document,clip,asset):
    begin=rational(clip['source_in']);end=begin+Fraction(clip['duration'])/rational(document['settings']['fps'])*rational(clip['rate'])
    # End padding is not additional source content. Images use a virtual grid.
    return begin,min(end,natural_duration(asset['metadata'])) if asset['kind']!='Image' else end

def normalize(document,query,source=None):
    fields(query,('op','expected_epoch','expected_revision','expected_project','source','source_range','handles','range','purpose'),('expected_command','source_epoch','clip','offset','limit','prior','query_id'))
    if query['op']!='review_inspect':fail('invalid_request','Use review_inspect for a read-only source review.')
    identity(query['source']);text(query['purpose'],512)
    identity(query['expected_project']);text(query['expected_epoch'],128);integer(query['expected_revision'])
    if query.get('query_id') is not None:identity(query['query_id'])
    if query.get('clip') is not None:identity(query['clip'])
    if query.get('source_epoch') is not None and not isinstance(query['source_epoch'],str):fail('invalid_source','Source epoch must identify an explicit Source context.')
    if not isinstance(query['handles'],list) or len(query['handles'])!=2:fail('invalid_range','Before/after handles require two Source-frame counts.')
    for value in query['handles']:integer(value,0,2**31-1)
    left,right=interval(query['source_range'])
    from project_export import export_range
    sequence=None if query['range'] is None else export_range(document,query['range'])
    assets={a['id']:a for a in document['media']};context=((source or {}).get('document') or {}).get('media',[])
    asset=assets.get(query['source']) or next((a for a in context if a['id']==query['source']),None)
    if asset is None:fail('missing_source','The selected source is no longer in this project or captured Source context. Saved marks remain intact.')
    if query.get('source_epoch') is not None:
        if (source or {}).get('epoch')!=query['source_epoch'] or not any(a['id']==query['source'] and a['sha256']==asset['sha256'] for a in context):fail('stale_source','The explicit Source context changed; inspect deliberately again.')
    clip=next((c for c in document['clips'] if c['id']==query.get('clip')),None)
    if query.get('clip') and (clip is None or assets[clip['asset']]['sha256']!=asset['sha256']):fail('stale_placement','Selected placement is missing or belongs to a different source identity.')
    fps=source_fps(asset,source if any(a['sha256']==asset['sha256'] for a in context) else None);end=extent(asset,fps)
    # Audio's last Source frame may cover partial natural-end samples. Disclose
    # that bounded grid padding rather than inventing source audio past EOF.
    maximum=max(end,Fraction(source_grid_end(asset,fps))/fps)
    if left>=end or right>maximum:fail('source_range','Requested In/Out exceeds the valid source interval; handles may clamp, source selection may not invent footage.')
    normalized=dict(source=asset['id'],source_range=[pair(left),pair(right)],handles=list(query['handles']),range=sequence,purpose=query['purpose'],clip=query.get('clip'),offset=integer(query.get('offset',0),0,2048),limit=integer(query.get('limit',64),1,128))
    if query.get('source_epoch') is not None:normalized['source_epoch']=query['source_epoch']
    return normalized,asset,clip,fps,end

def dependency_snapshot(document,query,asset,media,source):
    left,right=query['range'] if query['range'] is not None else (None,None);clips=[c for c in document['clips'] if left is not None and overlaps(c,left,right)]
    texts={category:[r for r in document[category] if left is not None and overlaps(r,left,right)] for category in ('captions','graphics')}
    asset_by_id={a['id']:a for a in document['media']}
    uses=[c for c in document['clips'] if asset_by_id[c['asset']]['sha256']==asset['sha256']]
    track_ids={r['track'] for r in clips+texts['captions']+texts['graphics']}
    source_ids={c['asset'] for c in clips+uses};source_ids.add(asset['id'])
    assets=[a for a in document['media'] if a['id'] in source_ids]
    if asset['id'] not in {a['id'] for a in assets}:assets.append(asset)
    clip_ids={c['id'] for c in clips}
    transitions=[r for r in document.get('transitions',[]) if left is not None and (overlaps(r,left,right) or clip_ids.intersection(r.get('audio',[])+[r['left'],r['right']]))]
    # Global solo and missing-route state can affect a range with no local clip
    # on that track. Global end affects canonical track fade-out origins.
    snapshot=dict(settings=document['settings'],sequence_end=duration(document),range=query['range'],clips=clips,text=texts,tracks=[t for t in document['tracks'] if t['id'] in track_ids],sources=assets,duplicate_uses=uses,transitions=transitions,buses=document.get('buses',[]),master=document.get('master',dict(gain=1.,mute=False)),global_audio_gates=[dict(id=t['id'],solo=t.get('solo',False),output=t.get('output','master')) for t in document['tracks'] if t['kind']=='audio'])
    verification=[]
    for a in assets:
        state=media.get(a['id'])
        if state is None and query.get('source_epoch')==(source or {}).get('epoch') and a['id']==asset['id']:state=dict(status='Ready',basis='captured verified Source context')
        state=deepcopy(state or dict(status='Unknown'))
        if state.get('expected') is not None and state['expected']!=a['sha256']:state=dict(state,status='Identity mismatch')
        verification.append(dict(id=a['id'],name=a['name'],sha256=a['sha256'],validation=state))
    return snapshot,verification,uses

def certificate_ok(value):
    if not isinstance(value,dict):fail('invalid_review','Review certificate must be structured.')
    fields(value,('format','version','binding','query','query_sha256','dependency_sha256','availability_sha256','ready','origin','sha256'))
    if value['format']!=CERTIFICATE or type(value['version']) is not int or value['version']!=1:fail('invalid_review','Unsupported review certificate version.')
    if type(value['ready']) is not bool:fail('invalid_review','Review readiness must be an explicit boolean.')
    for binding in (value['binding'],value['origin'].get('binding') if isinstance(value['origin'],dict) else None):
        fields(binding,('project','epoch','revision'));identity(binding['project']);text(binding['epoch'],128);integer(binding['revision'])
    fields(value['origin'],('binding','query_sha256','dependency_sha256','availability_sha256'))
    if any(value['origin']['binding'][k]!=value['binding'][k] for k in ('project','epoch')) or value['origin']['binding']['revision']>value['binding']['revision']:fail('invalid_review','Original review provenance belongs to another project/epoch or later revision.')
    if len(encoded(value))>16384:fail('inspection_capacity','Review certificate exceeds16KiB; no export/mark admitted.')
    unsigned=deepcopy(value);expected=unsigned.pop('sha256')
    if digest(unsigned)!=expected or digest(value['query'])!=value['query_sha256']:fail('invalid_review','Review certificate changed; no export/mark admitted.')
    return value

def inspect_review(document,epoch,revision,query,media=None,source=None,cancel=None):
    check(cancel)
    if document is None:fail('no_project','Open a video project before source/timeline review.')
    document=validate(document,allow_missing_routes=True);media=media or {};source=source or {}
    if (query.get('expected_project'),query.get('expected_epoch'),query.get('expected_revision'))!=(document['id'],epoch,revision):fail('stale_revision','Review request belongs to another accepted project/epoch/revision.')
    normalized,asset,clip,fps,end=normalize(document,query,source);left,right=interval(normalized['source_range'])
    requested=[left-Fraction(normalized['handles'][0])/fps,right+Fraction(normalized['handles'][1])/fps];effective=[max(Fraction(0),requested[0]),min(end,requested[1])]
    snapshot,verification,uses=dependency_snapshot(document,normalized,asset,media,source);check(cancel)
    dependencies=digest(snapshot);available=digest(verification);query_hash=digest(normalized);binding=bound(document,epoch,revision)
    from project_audio_graph import missing_routes
    routing_unavailable=missing_routes(document) if normalized['range'] is not None else []
    unavailable=[r for r in verification if r['validation'].get('status')!='Ready'];status='unavailable' if unavailable or routing_unavailable else 'ready';prior=query.get('prior');validation=None
    origin=dict(binding=deepcopy(binding),query_sha256=query_hash,dependency_sha256=dependencies,availability_sha256=available)
    if prior is not None:
        prior=certificate_ok(prior)
        if any(prior['binding'].get(k)!=binding[k] for k in ('epoch','project')):fail('stale_revision','A different project/epoch cannot validate an old review result.')
        unchanged=all(prior['origin'][k]==value for k,value in [('query_sha256',query_hash),('dependency_sha256',dependencies),('availability_sha256',available)])
        validation=dict(unchanged_dependencies=unchanged,original=deepcopy(prior['origin']),validated_binding=deepcopy(binding),previous_certificate_sha256=prior['sha256'])
        origin=deepcopy(prior['origin'])
        if not unchanged and status=='ready':status='outdated'
    certificate=dict(format=CERTIFICATE,version=1,binding=binding,query=normalized,query_sha256=query_hash,dependency_sha256=dependencies,availability_sha256=available,ready=status=='ready',origin=origin);certificate['sha256']=digest(certificate)
    rows=[];assets={a['id']:a for a in document['media']};tracks={t['id']:t for t in document['tracks']}
    for c in sorted(uses,key=lambda c:(c['start'],c['id']))[normalized['offset']:normalized['offset']+normalized['limit']]:
        check(cancel);begin,stop=source_interval(document,c,assets[c['asset']]);overlap=[max(begin,effective[0]),min(stop,effective[1])]
        component=c['provenance'].get('component',{})
        rows.append(dict(clip=c['id'],name=c['name'],asset=c['asset'],source_sha256=asset['sha256'],track=c['track'],track_name=tracks[c['track']]['name'],track_kind=tracks[c['track']]['kind'],sequence_range=[c['start'],c['start']+c['duration']],source_range=[pair(begin),pair(stop)],rate=c['rate'],handled_overlap=[pair(v) for v in overlap] if overlap[0]<overlap[1] else None,component={k:component[k] for k in ('instance_id','instance_key','kind','part','role','version') if k in component},selected=c['id']==normalized.get('clip')))
    mapping=None
    if clip:
        speed=rational(clip['rate']);seq_fps=rational(document['settings']['fps']);start=rational(clip['source_in']);mapped=[Fraction(clip['start'])+(v-start)/speed*seq_fps for v in effective]
        placed=[max(mapped[0],Fraction(clip['start'])),min(mapped[1],Fraction(clip['start']+clip['duration']))]
        suggested=[max(0,int(mapped[0]//1)),min(duration(document),ceiling(mapped[1]))]
        mapping=dict(clip=clip['id'],rate=clip['rate'],source_interval=[pair(v) for v in source_interval(document,clip,asset)],placement=[clip['start'],clip['start']+clip['duration']],handled_interval_sequence_frames=[pair(v) for v in mapped],context_inside_placement=[pair(v) for v in placed] if placed[0]<placed[1] else None,suggested_sequence_range=suggested if suggested[0]<suggested[1] else None,explanation='Mapped source handles beyond the placement are source context, not extra timeline footage. Suggested integer review bounds round outward and clamp to sequence; the mixed timeline contains its actual neighboring edits.')
    report=dict(format=FORMAT,version=1,status=status,binding=binding,certificate=certificate,validation=validation,source=dict(id=asset['id'],name=asset['name'],kind=asset['kind'],sha256=asset['sha256'],fps=pair(fps),natural_end=pair(end),requested_interval=normalized['source_range'],requested_handled_interval=[pair(v) for v in requested],effective_handled_interval=[pair(v) for v in effective],effective_grid=[int(effective[0]*fps//1),ceiling(effective[1]*fps)],clamped=[effective[i]!=requested[i] for i in (0,1)],selection_end_padding=pair(max(Fraction(0),right-end))),sequence=dict(range=normalized['range'],fps=document['settings']['fps'],dimensions=[document['settings']['width'],document['settings']['height']],out_exclusive=True),mapping=mapping,duplicate_use=dict(total=len(uses),offset=normalized['offset'],limit=normalized['limit'],next_offset=normalized['offset']+len(rows) if normalized['offset']+len(rows)<len(uses) else None,rows=rows,policy='Identity/hash and source overlap evidence only; intentional background/inset reuse is allowed, no automatic edit or duplication policy.'),availability=verification,unavailable=unavailable,purpose=normalized['purpose'],dependencies=dict(sha256=dependencies,clips=len(snapshot['clips']),text=sum(len(r) for r in snapshot['text'].values()),sources=len(snapshot['sources']),global_audio_gates=True,sequence_end_included=True),conditions='Derived immutable recipes and dated last owner verification; no file rescan, decode, measured mix, current rendered preview, device audition or creative acceptance. Export separately checks native pixels, PCM, source bytes and resource retirement.')
    # Match the existing SourceContext nominal-grid policy exactly: Video
    # floors complete frames; Audio covers canonical natural-tail samples.
    # Rational source context may include a video fraction not auditionable on
    # that legacy grid. Report it separately; never invent another Source frame.
    grid_end=source_grid_end(asset,fps)
    grid=[max(0,int(effective[0]*fps//1)),min(grid_end,ceiling(effective[1]*fps))]
    audition_grid=grid if grid[0]<grid[1] else None
    report['source'].update(effective_grid=audition_grid,grid_end=grid_end,auditionable_interval=[pair(Fraction(v)/fps) for v in grid] if audition_grid else None,grid_out_clamped=ceiling(effective[1]*fps)>grid_end,grid_policy='Existing Source Video complete-frame floor; Audio canonical natural-tail coverage; exact content interval is distinct from audition grid.')
    report['sequence']['available']=normalized['range'] is not None
    report['routing_unavailable']=routing_unavailable if normalized['range'] is not None else []
    if len(encoded(report))>MAX_REPORT:fail('inspection_capacity','Review report exceeds1MiB; narrow/page explicitly. No partial ready result or edit.')
    check(cancel);return report

def validate_marks(value):
    fields(value,('format','version','items'))
    if value['format']!=MARKS or type(value['version']) is not int or value['version']!=1:fail('invalid_review_marks','Unsupported source review marks version.')
    if not isinstance(value['items'],list) or len(value['items'])>MAX_MARKS:fail('review_mark_capacity','At most64 authored review marks fit this workflow; existing marks retained.')
    seen=set()
    for mark in value['items']:
        fields(mark,('id','purpose','source','source_sha256','source_range','source_fps','handles','clip','sequence_range','rate'))
        identity(mark['id']);identity(mark['source']);text(mark['purpose'],512)
        if mark['id'] in seen:fail('duplicate_id','Review mark IDs must be unique.')
        seen.add(mark['id'])
        if mark['clip'] is not None:identity(mark['clip'])
        if not isinstance(mark['source_sha256'],str) or len(mark['source_sha256'])!=64 or any(c not in '0123456789abcdef' for c in mark['source_sha256']):fail('invalid_review_marks','A mark retains its exact source SHA256.')
        interval(mark['source_range'])
        if rational(mark['source_fps'])<=0 or not Fraction(1,16)<=rational(mark['rate'])<=16:fail('invalid_time','Invalid saved Source grid or placement rate.')
        for name in ('handles','sequence_range'):
            if name=='sequence_range' and mark[name] is None:continue
            if not isinstance(mark[name],list) or len(mark[name])!=2:fail('invalid_range','Saved handles/range need two integer bounds.')
            for n in mark[name]:integer(n,0,2**31-1)
        if mark['sequence_range'] is not None and mark['sequence_range'][0]>=mark['sequence_range'][1]:fail('invalid_range','Saved sequence In must precede exclusive Out.')
    if len(encoded(value))>65536:fail('review_mark_capacity','Authored review metadata exceeds64KiB; prior accepted marks retained.')
    return value

def marks(document):
    value=document['provenance'].get(MARK_KEY)
    if value is None:return dict(format=MARKS,version=1,items=[])
    return deepcopy(validate_marks(value))

def remember_change(document,report,mark_id,binding):
    identity(mark_id);certificate_ok(report['certificate'])
    if report['status']!='ready' or not report['certificate']['ready'] or report['binding']['project']!=document['id'] or any(binding.get('expected_'+k)!=report['certificate']['binding'][k] for k in ('epoch','revision','project')):fail('outdated_review','Inspect/validate a ready result at this accepted revision before remembering its authored range.')
    saved=marks(document);query=report['certificate']['query'];item=dict(id=mark_id,purpose=query['purpose'],source=query['source'],source_sha256=report['source']['sha256'],source_range=query['source_range'],source_fps=report['source']['fps'],handles=query['handles'],clip=query['clip'],sequence_range=query['range'],rate=(report['mapping'] or {}).get('rate',[1,1]))
    existing=next((i for i,r in enumerate(saved['items']) if r['id']==mark_id),None)
    if existing is None:saved['items'].append(item)
    else:saved['items'][existing]=item
    validate_marks(saved);return dict(op='project.provenance',values={MARK_KEY:saved})

def query_from_mark(document,mark,binding,source=None):
    sources=document['media']+(((source or {}).get('document') or {}).get('media',[]))
    asset=next((a for a in sources if a['id']==mark['source'] and a['sha256']==mark['source_sha256']),None) or next((a for a in sources if a['sha256']==mark['source_sha256']),None)
    if asset is None:fail('missing_source','Saved mark source is unavailable/replaced; note and exact ranges remain retained.')
    query=dict(op='review_inspect',**binding,source=asset['id'],source_range=deepcopy(mark['source_range']),handles=list(mark['handles']),range=deepcopy(mark['sequence_range']),purpose=mark['purpose'],clip=mark['clip'])
    if asset['id'] not in {a['id'] for a in document['media']}:query['source_epoch']=source['epoch']
    return query

def export_values(report,binding,path,crf=18):
    certificate=certificate_ok(report['certificate']);integer(crf,0,51)
    if report['status']!='ready' or not certificate['ready'] or any(binding.get('expected_'+k)!=certificate['binding'][k] for k in ('epoch','revision','project')):fail('outdated_review','Review result is not ready at this captured accepted revision. Validate/inspect deliberately; no export submitted.')
    if certificate['query']['range'] is None:fail('no_review_sequence','Source-only inspection has no mixed timeline export interval. Place clips and choose an explicit sequence sample first; Source audition remains available.')
    return dict(path=path,crf=crf,range=list(certificate['query']['range']),review_sample=deepcopy(certificate))

def export_request(report,binding,path,operation_id,crf=18):
    identity(operation_id);return dict(op='export',operation_id=operation_id,**binding,**export_values(report,binding,path,crf))

def export_review_project(document,epoch,revision,path,crf,folder,cancel,extra,frame_range,media,source,certificate):
    """Existing single export worker/job; validate before graphics process creation."""
    certificate=certificate_ok(certificate);current=bound(document,epoch,revision)
    if certificate['binding']!=current or not certificate['ready'] or certificate['query']['range']!=frame_range:fail('outdated_review','Sample certificate belongs to another revision/range; no export started.')
    query=dict(op='review_inspect',expected_epoch=epoch,expected_revision=revision,expected_project=document['id'],**certificate['query'])
    report=inspect_review(document,epoch,revision,query,media,source,cancel)
    if report['status']!='ready' or any(report['certificate'][key]!=certificate[key] for key in ('query_sha256','dependency_sha256','availability_sha256')):fail('outdated_review','Sample dependencies or source verification changed; no export started.')
    # An unplaced currently loaded Source is still user input, even though it
    # is absent from the accepted timeline's media list. Protect its paths too.
    extra=list(extra)+[a['location']['path'] for a in ((source or {}).get('document') or {}).get('media',[])]
    # Retain the exact review provenance BEFORE export. Adjacent job metadata
    # avoids changing the existing export process, folder ownership or codecs.
    # It survives failed/superseded output and owner outcome-ledger retirement.
    from pathlib import Path
    import os
    receipt=Path(folder).with_name(Path(folder).name+'-review.json')
    from project_export import export_project,protect
    protect(document,path,extra);protect(document,receipt,list(extra)+[path],suffix='.json');receipt.parent.mkdir(parents=True,exist_ok=True);raw=encoded(certificate);check(cancel)
    with receipt.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    try:result=export_project(document,epoch,revision,path,crf,folder,cancel,extra,frame_range)
    except BaseException as exc:exc.add_note('Exact review certificate retained: '+str(receipt));raise
    result['review_sample']=deepcopy(certificate);result['review_certificate_path']=str(receipt);result['review_certificate_sha256']=hashlib.sha256(raw).hexdigest();result['review_sample_status']='Frozen original accepted revision; newer edits require explicit validation, never automatic current acceptance.'
    return result

def describe(report):
    def seconds(value):return f'{float(rational(value)):.6f}'.rstrip('0').rstrip('.')+'s'
    def times(value):return seconds(value[0])+' → '+seconds(value[1])+' (Out exclusive)'
    def frames(value):return '['+str(value[0])+', '+str(value[1])+')'
    def fps(value):return f'{float(rational(value)):.3f}'.rstrip('0').rstrip('.')+' FPS'
    s=report['source'];sequence=report['sequence'];seq_fps=rational(sequence['fps']);lines=[report['status'].upper()+' · '+(report['purpose'] or 'Exact review sample'), 'Source: '+s['name']+' · '+s['kind']+' · '+fps(s['fps']), 'Selected Source: '+times(s['requested_interval']), 'With handles: '+times(s['effective_handled_interval']), 'Auditionable Source frame grid: '+(frames(s['effective_grid']) if s['effective_grid'] else 'unavailable for this fractional tail')+' at '+fps(s['fps'])]
    if s['clamped'][0]:lines.append('Before handle clamped at the start of this source.')
    if s['clamped'][1]:lines.append('After handle clamped at the natural end of this source.')
    if rational(s['selection_end_padding']):lines.append('The last selected Source frame includes '+seconds(s['selection_end_padding'])+(' beyond natural audio; that is end padding, not extra source sound.' if s['kind']=='Audio' else ' beyond the recorded natural interval. Only the existing Source grid is represented; no additional decoded frame is invented.'))
    if s.get('grid_out_clamped'):lines.append('Natural video context includes a partial final frame. Source audition stops at its existing complete-frame boundary; no extra frame is added.')
    if sequence['range'] is None:lines.append('Mixed timeline interval unavailable. Source-only inspection/audition remains usable before placement.')
    else:lines.append('Mixed sequence: '+frames(sequence['range'])+' project frames at '+fps(sequence['fps'])+' · '+times([pair(Fraction(v)/seq_fps) for v in sequence['range']]))
    if report['mapping']:
        m=report['mapping'];chosen=next((r for r in report['duplicate_use']['rows'] if r['selected']),None);name=(chosen['name']+' on '+chosen['track_name']) if chosen else 'Selected placement'
        mapped='['+f'{float(rational(m["handled_interval_sequence_frames"][0])):.3f}'+', '+f'{float(rational(m["handled_interval_sequence_frames"][1])):.3f}'+')'
        lines+=['Placement: '+name+' · '+frames(m['placement'])+' sequence frames · '+f'{float(rational(m["rate"])):g}x rate','Handled source maps to '+mapped+' sequence frames.','Source handles beyond this placement are not newly placed footage. A mixed timeline sample shows the actual neighboring edits.']
    uses=report['duplicate_use'];lines.append('\nSame source identity: '+str(uses['total'])+' uses; showing '+str(uses['offset']+1 if uses['rows'] else 0)+'–'+str(uses['offset']+len(uses['rows']))+'. Reuse is allowed.')
    for row in uses['rows']:
        part=row['component'].get('part');overlap='handled source overlap '+times(row['handled_overlap']) if row['handled_overlap'] else 'distinct source interval; no handled overlap'
        lines.append((row['name'] or 'Clip')+' ('+row['clip'][:8]+') · '+row['track_name']+' / '+row['track_kind']+' · sequence '+frames(row['sequence_range'])+' · source '+times(row['source_range'])+' · '+f'{float(rational(row["rate"])):g}x'+'\n  '+overlap+(' · component '+part if part else ''))
    for value in report['unavailable']:lines.append('Unavailable: '+value['name']+' · '+value['validation']['status'])
    for value in report.get('routing_unavailable',[]):lines.append('Unavailable audio route: '+value['name']+'; select Master, None or an existing bus deliberately.')
    if report['validation']:
        v=report['validation'];lines.append('Explicit validation at revision '+str(v['validated_binding']['revision'])+': dependencies '+('unchanged' if v['unchanged_dependencies'] else 'changed')+'. Original evidence remains revision '+str(v['original']['binding']['revision'])+'.')
    lines+=['Source identity '+s['sha256'][:12]+'… · accepted revision '+str(report['binding']['revision'])+'. Exact hashes, IDs and rational boundaries remain in the structured report.','Derived edit/source-verification information. Inspect the exported sample separately; this is not heard sound, playback timing or creative approval.'];return '\n'.join(lines)
