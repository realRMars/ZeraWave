"""Pure bounded timeline edits used only by the existing document authority.

This module mutates the transaction's private copy. ProjectService alone admits,
publishes, records history and persists the resulting validated document.
"""
from copy import deepcopy
import uuid

OP_FIELDS = {
 'track.edit': (('id','values'),()), 'track.move': (('id','order'),()),
 'track.remove': (('id',),('confirmed','linked')),
 'media.remove': (('ids',),()),
 'items.move': (('ids','delta'),('track_map','linked','groups','mode')),
 'items.trim': (('id',),('start','end','linked')),
 'items.split': (('ids','at'),('linked','groups')),
 'items.delete': (('ids',),('ripple','scope','linked','groups')),
 'items.group': (('ids',),()), 'items.ungroup': (('ids',),()),
 'items.link': (('ids',),()), 'items.unlink': (('ids',),()),
 'items.place': (('rows',),('mode','scope')),
 'items.paste': (('rows','at','track_map'),('mode','scope')),
}

def model():
    import video_project
    return video_project

def entries(d):
    return [(category,row) for category in ('clips','captions','graphics') for row in d[category]]

def token(operation,name):return uuid.uuid5(uuid.UUID(operation),name).hex

def selected(d,ids,linked=True,groups=True):
    v=model();rows={r['id']:(c,r) for c,r in entries(d)}
    if not isinstance(ids,list) or not ids or len(ids)>sum(v.LIMITS[c] for c in ('clips','captions','graphics')):v.fail('invalid_selection','Select at least one supported timeline item.')
    if any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids) or any(i not in rows for i in ids):v.fail('missing_object','Timeline selection contains a missing or repeated ID; nothing changed.')
    result=set(ids)
    while True:
        links={rows[i][1].get('link_id') for i in result} - {None} if linked else set()
        group_ids={rows[i][1].get('group_id') for i in result} - {None} if groups else set()
        extended=result | {i for i,(_,r) in rows.items() if r.get('link_id') in links or r.get('group_id') in group_ids}
        if extended==result:break
        result=extended
    return [rows[i] for i in rows if i in result]

def unlocked(d,rows=(),tracks=()):
    protected={r['track'] for _,r in rows}|set(tracks);index={t['id']:t for t in d['tracks']}
    for key in protected:
        if key not in index:model().fail('missing_object','Target track is unavailable; nothing changed.')
        if index[key].get('locked',False):model().fail('track_locked','Unlock '+index[key]['name']+' first. The entire operation was rejected.')

def sync_scope(d,affected):
    """A range operation cannot alter only part of a linked relationship."""
    changed=set(affected);links={r.get('link_id') for _,r in entries(d) if r['id'] in changed}-{None}
    if any(r.get('link_id') in links and r['id'] not in changed for _,r in entries(d)):
        model().fail('linked_scope','An affected linked partner lies outside this range/scope. Unlink deliberately or include it; nothing changed.')

def shift(row,delta):
    row['start']+=delta
    if row.get('dynamic'):
        for key in ('range_start','range_end'):
            if key in row:row[key]+=delta

def piece(d,row,start,end,new_start=None):
    """Slice in original project coordinates, preserving source/fade origin."""
    v=model();r=deepcopy(row);offset=start-row['start'];r.update(start=start if new_start is None else new_start,duration=end-start)
    if 'asset' in r:
        r['source_in']=v.pair(v.rational(row['source_in'])+v.frame_time(d,offset)*v.rational(row['rate']))
        r['audio_window']['offset']+=offset
    elif r.get('dynamic') and new_start is not None:
        for key in ('range_start','range_end'):
            if key in r:r[key]+=new_start-start
    if 'visual_window' in r:r['visual_window']['offset']+=offset
    return r

def range_edit(d,left,right,scope,operation,insert=False,close_gap=True):
    """Insert time, or remove [left,right), atomically across explicit tracks."""
    v=model();length=right-left
    if length<=0:v.fail('invalid_time','The edited interval must contain at least one frame.')
    if scope is not None and (not isinstance(scope,list) or any(not isinstance(i,str) for i in scope)):v.fail('invalid_scope','Ripple scope requires existing unique track IDs.')
    ids={t['id'] for t in d['tracks']} if scope is None else set(scope)
    if scope is not None and (len(ids)!=len(scope) or not ids<={t['id'] for t in d['tracks']}):v.fail('invalid_scope','Ripple scope requires existing unique track IDs.')
    affected=[(c,r) for c,r in entries(d) if r['track'] in ids and r['start']+r['duration']>left and (insert or close_gap or r['start']<right)]
    unlocked(d,affected);sync_scope(d,{r['id'] for _,r in affected});created=[]
    for category in ('clips','captions','graphics'):
        updated=[]
        for row in d[category]:
            start,end=row['start'],row['start']+row['duration']
            if row['track'] not in ids or end<=left:updated.append(row);continue
            if insert:
                if start>=left:shift(row,length);updated.append(row);continue
                first=piece(d,row,start,left);second=piece(d,row,left,end,left+length)
            else:
                if start>=right:
                    if close_gap:shift(row,-length)
                    updated.append(row);continue
                first=piece(d,row,start,left) if start<left else None
                second=piece(d,row,right,end,left if close_gap else right) if end>right else None
            if first is not None:updated.append(first)
            if second is not None:
                if first is not None:
                    second['id']=token(operation,row['id']+'-range-right');created.append(second['id'])
                    if second.get('link_id'):second['link_id']=token(operation,second['link_id']+'-range-right-link')
                updated.append(second)
        d[category]=updated
    return created

def check_collision(d,rows,prior=None):
    v=model();clips=[r for c,r in rows if c=='clips']
    def conflict(a,b):
        amount=max(0,min(a['start']+a['duration'],b['start']+b['duration'])-max(a['start'],b['start'])) if a['track']==b['track'] else 0
        old_a,old_b=(prior or {}).get(a['id']),(prior or {}).get(b['id'])
        old=max(0,min(old_a['start']+old_a['duration'],old_b['start']+old_b['duration'])-max(old_a['start'],old_b['start'])) if old_a and old_b and old_a['track']==old_b['track'] else 0
        return amount>old
    for row in clips:
        for other in d['clips']:
            if conflict(row,other):
                v.fail('collision','Normal placement overlaps existing material. Choose Insert, Overwrite or an explicit transition; nothing changed.')
    for i,row in enumerate(clips):
        for other in clips[i+1:]:
            if conflict(row,other):v.fail('collision','Placed items overlap each other on one track.')

def place(d,rows,mode,scope,operation,prior=None):
    v=model()
    if mode not in ('Normal','Insert','Overwrite'):v.fail('invalid_mode','Choose Normal, Insert or Overwrite.')
    unlocked(d,rows)
    left=min(r['start'] for _,r in rows);right=max(r['start']+r['duration'] for _,r in rows);v.integer(left)
    created=[]
    if mode=='Insert':
        if scope is not None:
            if not isinstance(scope,list) or any(not isinstance(key,str) for key in scope) or not {row['track'] for _,row in rows}<=set(scope):v.fail('invalid_scope','Insert scope must include every destination track; nothing was changed.')
        created+=range_edit(d,left,right,scope,operation,True)
    elif mode=='Overwrite':
        target=list({r['track'] for _,r in rows})
        if scope is not None and set(scope)!=set(target):v.fail('invalid_scope','Overwrite scope is the explicitly targeted tracks.')
        created+=range_edit(d,left,right,target,operation,close_gap=False)
    else:check_collision(d,rows,prior)
    for category,row in rows:d[category].append(row);created.append(row['id'])
    return created

def unpack_rows(value):
    v=model()
    if not isinstance(value,list) or not value or len(value)>sum(v.LIMITS[c] for c in ('clips','captions','graphics')):v.fail('invalid_clipboard','Clipboard/placement has no supported items.')
    rows=[]
    for entry in value:
        v.fields(entry,('category','row'))
        if entry['category'] not in ('clips','captions','graphics') or not isinstance(entry['row'],dict):v.fail('invalid_clipboard','Unsupported clipboard item.')
        needed=('id','track','start','duration','asset','source_in','rate','audio','layout','link_id','audio_window','pad_end','provenance','name') if entry['category']=='clips' else ('id','track','start','duration','text','style','order','dynamic','provenance')
        if set(needed)-set(entry['row']):v.fail('invalid_clipboard','Clipboard item is missing required recipe fields.')
        v.identity(entry['row']['id']);v.identity(entry['row']['track']);v.timed(entry['row'])
        rows.append((entry['category'],deepcopy(entry['row'])))
    if len({r.get('id') for _,r in rows})!=len(rows):v.fail('duplicate_id','Clipboard repeats an item ID.')
    return rows

def apply_edit(d,change,operation,index):
    v=model();op=change['op'];created=[];seed=token(operation,'edit-'+str(index))
    for flag in ('linked','groups','ripple','confirmed'):
        if flag in change and type(change[flag]) is not bool:v.fail('invalid_value',flag+' must be true or false.')
    if op=='track.edit':
        track=v._find(d,'tracks',change['id']);values=change['values'];v.fields(values,(),('name','locked','visible','solo'))
        if 'name' in values:unlocked(d,tracks=[track['id']]);v.text(values['name'],256)
        for flag in ('locked','visible','solo'):
            if flag in values and type(values[flag]) is not bool:v.fail('invalid_value',flag+' must be true or false.')
        if 'solo' in values and track['kind']!='audio' or 'visible' in values and track['kind']=='audio':v.fail('invalid_track','Solo is audio-only; visibility is for visual tracks.')
        track.update(deepcopy(values))
    elif op=='track.move':
        track=v._find(d,'tracks',change['id']);unlocked(d,tracks=[track['id']]);order=v.integer(change['order'],0,len(d['tracks'])-1);tracks=sorted(d['tracks'],key=lambda t:t['order']);tracks.remove(track);tracks.insert(order,track)
        for i,t in enumerate(tracks):t['order']=i
    elif op=='track.remove':
        track=v._find(d,'tracks',change['id']);unlocked(d,tracks=[track['id']]);ids=[r['id'] for _,r in entries(d) if r['track']==track['id']]
        if ids and not change.get('confirmed',False):v.fail('confirmation_required','Removing a nonempty track requires explicit confirmation including linked contents.')
        rows=selected(d,ids,change.get('linked',True),False) if ids else [];unlocked(d,rows)
        removed={r['id'] for _,r in rows}
        if not change.get('linked',True):sync_scope(d,removed)
        for category in ('clips','captions','graphics'):d[category]=[r for r in d[category] if r['id'] not in removed]
        d['tracks'].remove(track)
        for i,t in enumerate(sorted(d['tracks'],key=lambda t:t['order'])):t['order']=i
    elif op=='media.remove':
        ids=change['ids']
        if not isinstance(ids,list) or not ids or len(set(ids))!=len(ids) or not set(ids)<={a['id'] for a in d['media']}:v.fail('missing_reference','Select existing project references.')
        if any(r['asset'] in ids for r in d['clips']):v.fail('reference_in_use','This project reference is used by clips. Remove those clips deliberately first; original files are never deleted.')
        d['media']=[a for a in d['media'] if a['id'] not in ids]
    elif op in ('items.place','items.paste'):
        rows=unpack_rows(change['rows'])
        if op=='items.paste':
            anchor=min(r['start'] for _,r in rows);at=v.integer(change['at']);mapping=change['track_map']
            if not isinstance(mapping,dict):v.fail('invalid_track','Paste requires an explicit compatible track mapping.')
            tracks={t['id']:t for t in d['tracks']}
            for category,row in rows:
                row['id']=token(seed,row['id']+'-copy');shift(row,at-anchor)
                if row['track'] not in mapping:v.fail('invalid_track','No compatible paste destination for a copied track.')
                if row['track'] in tracks and mapping[row['track']] in tracks and tracks[row['track']]['kind']!=tracks[mapping[row['track']]]['kind']:v.fail('invalid_track','Paste cannot change a clip between video, audio and graphics tracks.')
                row['track']=mapping[row['track']]
                for field in ('link_id','group_id'):
                    if row.get(field):row[field]=token(seed,row[field]+'-copy-'+field)
        created+=place(d,rows,change.get('mode','Normal'),change.get('scope'),seed)
    else:
        rows=selected(d,change['ids'] if 'ids' in change else [change['id']],change.get('linked',True),change.get('groups',True) if op not in ('items.trim','items.link','items.unlink') else False);unlocked(d,rows);ids={r['id'] for _,r in rows}
        if op=='items.move':
            delta=v.integer(change['delta'],-120*24*3600,120*24*3600);mapping=change.get('track_map',{})
            if not isinstance(mapping,dict) or set(mapping)-ids:v.fail('invalid_track','Move target mapping contains an unselected item.')
            copies=[];tracks={t['id']:t for t in d['tracks']}
            for category,row in rows:
                r=deepcopy(row);shift(r,delta)
                if row['id'] in mapping:
                    target=mapping[row['id']]
                    if target not in tracks or tracks[target]['kind']!=tracks[row['track']]['kind']:v.fail('invalid_track','Move requires a track of the same type; choose explicit source audio/video placement to convert roles.')
                    r['track']=target
                copies.append((category,r))
            if all(r==old for (_,r),(_,old) in zip(copies,rows)):return []
            prior={r['id']:r for _,r in entries(d)}
            for category in ('clips','captions','graphics'):d[category]=[r for r in d[category] if r['id'] not in ids]
            created+=place(d,copies,change.get('mode','Normal'),None,seed,prior)
            created=[i for i in created if i not in ids]
        elif op=='items.trim':
            category,primary=next((c,r) for c,r in rows if r['id']==change['id']);start=change.get('start',primary['start']);end=change.get('end',primary['start']+primary['duration']);v.integer(start);v.integer(end,1);left=start-primary['start'];right=end-(primary['start']+primary['duration'])
            prior={r['id']:deepcopy(r) for _,r in entries(d)}
            for c,row in rows:
                trimmed=piece(d,row,row['start']+left,row['start']+row['duration']+right);row.clear();row.update(trimmed)
            check_collision({'clips':[r for r in d['clips'] if r['id'] not in ids]},rows,prior)
        elif op=='items.split':
            at=v.integer(change['at']);inside=[(c,r) for c,r in rows if r['start']<at<r['start']+r['duration']]
            if not inside:return []
            sync_scope(d,{r['id'] for _,r in inside})
            for category,row in inside:
                end=row['start']+row['duration'];right=piece(d,row,at,end);right['id']=token(seed,row['id']+'-right');row['duration']=at-row['start']
                for field in ('link_id','group_id'):
                    if right.get(field):right[field]=token(seed,right[field]+'-right-'+field)
                d[category].append(right);created.append(right['id'])
        elif op=='items.delete':
            if change.get('ripple',False):
                left=min(r['start'] for _,r in rows);right=max(r['start']+r['duration'] for _,r in rows);scope=change.get('scope')
                if scope is not None and any(r['track'] not in scope for _,r in rows):v.fail('invalid_scope','Ripple scope excludes a selected item.')
                created+=range_edit(d,left,right,scope,seed)
            else:
                for category in ('clips','captions','graphics'):d[category]=[r for r in d[category] if r['id'] not in ids]
        elif op in ('items.group','items.ungroup'):
            group=token(seed,'group') if op=='items.group' else None
            if group and len(rows)<2:v.fail('invalid_selection','A group requires at least two timeline items.')
            for _,row in rows:
                if group:row['group_id']=group
                else:row.pop('group_id',None)
        elif op=='items.link':
            clips=[r for c,r in rows if c=='clips'];tracks={t['id']:t for t in d['tracks']}
            if len(clips)!=2 or {tracks[r['track']]['kind'] for r in clips}!={'video','audio'}:v.fail('invalid_link','Link requires one video clip and its audio clip.')
            a,b=clips
            if any(a[k]!=b[k] for k in ('asset','start','duration','source_in','rate')):v.fail('invalid_link','Link requires the same source, source time, rate and project interval. Use Group for unrelated material.')
            for row in clips:row['link_id']=token(seed,'link')
        elif op=='items.unlink':
            for _,row in rows:
                if 'link_id' in row:row['link_id']=None
        else:v.fail('unsupported_command','Unsupported timeline edit.')
    return created
