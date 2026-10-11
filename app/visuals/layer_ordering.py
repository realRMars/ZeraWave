"""Branch ordering policy: visible front-first, stored back-first; stable IDs."""
from composition import lookup,ancestors,effective,reparent,renumber,validate_scene

def siblings(scene,parent):return sorted((r for r in scene['layers'] if r['parent']==parent),key=lambda r:r['order'],reverse=True)
def permitted(scene,row):return not effective(scene,row,'locked')
def can_step(scene,identity,direction):
    row=lookup(scene).get(identity)
    if not row or not permitted(scene,row):return False
    rows=siblings(scene,row['parent']);index=rows.index(row)
    return 0<=index-direction<len(rows)
def step(scene,identity,direction):
    if not can_step(scene,identity,direction):return False
    row=lookup(scene)[identity];rows=siblings(scene,row['parent']);i=rows.index(row);j=i-direction;rows[i],rows[j]=rows[j],rows[i]
    for order,r in enumerate(reversed(rows)):
        if r['order']!=order:r['order']=order;r['cut_alignment']=None
    return True
def move(scene,identities,anchor,placement):
    """Edge insertions carry subtrees; center is an explicit eligible-parent drop."""
    rows=lookup(scene);selected=set(identities)
    roots=[rows[k] for k in identities if k in rows and not any(a['id'] in selected for a in ancestors(scene,k))]
    if not roots or any(not permitted(scene,r) for r in roots):raise ValueError('Unlock the moving branch before ordering.')
    target=rows.get(anchor)
    if placement=='inside':
        if not target or target['type'] not in ('Group','Image','Artwork','Paint'):raise ValueError('Choose an eligible raster or Group parent.')
        parent=target['id']
    elif placement in ('above','below'):
        parent=target['parent'] if target else roots[0]['parent']
        if len({r['parent'] for r in roots})!=1:raise ValueError('Choose siblings for an edge move, or drop explicitly inside a parent.')
    else:raise ValueError('Invalid layer insertion.')
    if parent is not None and effective(scene,rows[parent],'locked'):raise ValueError('Unlock the destination/protecting Group.')
    if target and effective(scene,target,'locked'):raise ValueError('Unlock the destination/protecting Group.')
    old=[(r['id'],r['parent'],r['order'],list(r['transform'])) for r in scene['layers']]
    root_ids={r['id'] for r in roots}
    if target and placement!='inside' and target['id'] in root_ids:return False
    for r in roots:
        if r['parent']!=parent:reparent(scene,r['id'],parent)
        elif placement=='inside' and (r['id']==parent or any(a['id']==r['id'] for a in ancestors(scene,parent))):raise ValueError('Cannot place a branch inside itself.')
    remaining=[r for r in siblings(scene,parent) if r['id'] not in root_ids]
    insertion=0 if placement=='inside' else len(remaining) if target is None else remaining.index(target)+(placement=='below')
    # Dragged roots retain their visible relative order, not selection-click order.
    old_order={k:(p,o) for k,p,o,t in old};roots.sort(key=lambda r:old_order[r['id']][1],reverse=True)
    result=remaining[:insertion]+roots+remaining[insertion:]
    for order,r in enumerate(reversed(result)):
        if r['order']!=order or old_order[r['id']][0]!=r['parent']:r['cut_alignment']=None
        r['order']=order
    renumber(scene);validate_scene(scene)
    return old!=[(r['id'],r['parent'],r['order'],list(r['transform'])) for r in scene['layers']]
