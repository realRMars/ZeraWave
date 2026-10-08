"""Authoritative, JSON-only composition contract and bounded edit history.

Coordinates are normalized canvas coordinates, positive Y down. An asset is
cropped/masked in source UV, fitted, flipped, then transformed about its centre.
Parent affine transforms follow; group compositing is isolated, opacity once.
The list is back-to-front (order ascending); the UI presents the reverse.
"""
from copy import deepcopy
import json, math, uuid
import numpy as np

PRESENTATIONS=('World + Layers','Layers only','World only')
BLENDS=('Normal','Multiply','Screen','Add','Difference')
TYPES=('Image','Artwork','Paint','Video','GIF','Sprite','Group','Web','Model')
MAX_LAYERS=32
MAX_DEPTH=6
MAX_POINTS=128
MAX_MASKS=8
IDENTITY=[1.,0.,0.,1.,0.,0.]

def defaults():return dict(version=4,presentation=PRESENTATIONS[0],assets=[],layers=[],canvas=None)
def number(v,lo,hi,label):
    if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Invalid '+label+'.')
    return float(v)
def matrix(values):
    a,b,c,d,e,f=values
    return np.array([[a,c,e],[b,d,f],[0.,0.,1.]])
def coefficients(m):return [float(m[0,0]),float(m[1,0]),float(m[0,1]),float(m[1,1]),float(m[0,2]),float(m[1,2])]
def transform(x=0.,y=0.,scale=1.,scale_y=None,rotation=0.,aspect=16/9):
    r=math.radians(rotation);s=scale;sy=s if scale_y is None else scale_y
    return [s*math.cos(r),s*math.sin(r)*aspect,-sy*math.sin(r)/aspect,sy*math.cos(r),x,y]
def properties(values,aspect=16/9):
    a,b,c,d,x,y=values;s=math.hypot(a,b/aspect);sy=(a*d-b*c)/max(s,1e-9)
    return x,y,s,sy,math.degrees(math.atan2(b/aspect,a))
def new_layer(kind='Image',asset=None,name=None):
    return dict(id=uuid.uuid4().hex,type=kind,asset=asset,name=name or kind,parent=None,order=0,
        enabled=True,locked=False,opacity=1.,fit='Fit',transform=IDENTITY.copy(),aspect_lock=True,
        flip_x=False,flip_y=False,crop=[0.,0.,1.,1.],masks=[],blend='Normal',blend_strength=1.,source_visible=True,cut_alignment=None,
        media=dict(rate=1.,loop='None',start=0.,end=None,columns=1,rows=1,first=0,last=0,fps=12.),
        web=dict(url='',width=1280,height=720,cadence=15.,transparent=True,offline='Retain last'),model=dict(yaw=0.,pitch=0.,roll=0.))
def validate_scene(data):
    from media_registry import reference,normalized
    if data is None:return defaults()
    if not isinstance(data,dict):raise ValueError('Invalid composition.')
    if data.get('version')==1:
        from media_registry import legacy_validate_scene
        data=legacy_validate_scene(data)
        # Increment 1 IDs and exact ordering/settings survive. Unused slots go.
        out=defaults();out['presentation']={'Image only':'Layers only','World + images':'World + Layers'}.get(data.get('presentation'))
        out['assets']=deepcopy(data.get('assets',[]));names={a['id']:a['name'] for a in out['assets']}
        for old in data.get('layers',[]):
            if not old.get('asset'):continue
            row=new_layer(asset=old['asset'],name=names.get(old['asset'],'Image'));row.update(id=old['id'],order=old['order'],enabled=old['enabled'],opacity=old['opacity'],fit=old['fit'],transform=transform(old['x'],old['y'],old['scale']))
            out['layers'].append(row)
        data=out
    if data.get('version') not in (2,3,4) or data.get('presentation') not in PRESENTATIONS:raise ValueError('Unsupported composition version/presentation.')
    canvas=data.get('canvas')
    if canvas is not None:
        if not isinstance(canvas,list) or len(canvas)!=2 or any(type(v) is not int or not 1<=v<=8192 for v in canvas) or canvas[0]*canvas[1]>8388608:raise ValueError('Canvas must be 1–8192 pixels per side, at most 8 megapixels.')
    if len(json.dumps(data,ensure_ascii=True))>256*1024:raise ValueError('Composition exceeds the 256 KiB edit-state budget.')
    assets=data.get('assets');layers=data.get('layers')
    if not isinstance(assets,list) or len(assets)>MAX_LAYERS or not isinstance(layers,list) or len(layers)>MAX_LAYERS:raise ValueError('Composition supports at most 32 layers/references.')
    assets=[reference(a) for a in assets];refs={a['id']:a for a in assets}
    if len(refs)!=len(assets) or len({normalized(a['path']) for a in assets})!=len(assets):raise ValueError('Duplicate composition reference.')
    clean=[];ids=set()
    for source in layers:
        if not isinstance(source,dict):raise ValueError('Invalid layer.')
        row=new_layer();row.update(deepcopy(source));identity=row['id']
        if not isinstance(identity,str) or not identity or len(identity)>64 or identity in ids:raise ValueError('Duplicate/invalid layer identity.')
        ids.add(identity)
        if row['type'] not in TYPES or row['blend'] not in BLENDS or row['fit'] not in ('Fit','Fill','Stretch'):raise ValueError('Unsupported layer type/blend/fit.')
        if not isinstance(row['name'],str) or not row['name'].strip() or len(row['name'])>128:raise ValueError('Layer name must be 1–128 characters.')
        for key in ('enabled','locked','aspect_lock','flip_x','flip_y','source_visible'):
            if type(row[key]) is not bool:raise ValueError('Invalid layer '+key+'.')
        if row['asset'] is not None and row['asset'] not in refs:raise ValueError('Layer reference is missing from the session.')
        expected={'Image':'Images','Artwork':'Images','Paint':'Images','Sprite':'Images','Video':'Video','GIF':'Animated','Model':'Models'}
        if row['type'] in expected and (row['asset'] not in refs or refs[row['asset']]['kind']!=expected[row['type']]):raise ValueError('Layer/source type mismatch.')
        if row['type'] in ('Group','Web') and row['asset'] is not None:raise ValueError('Group/Web cannot own a file reference.')
        row['opacity']=number(row['opacity'],0.,1.,'opacity')
        row['blend_strength']=number(row['blend_strength'],0.,1.,'blend strength')
        if type(row['order']) is not int or not 0<=row['order']<MAX_LAYERS:raise ValueError('Invalid layer order.')
        if not isinstance(row['transform'],list) or len(row['transform'])!=6:raise ValueError('Invalid affine transform.')
        row['transform']=[number(v,-100.,100.,'transform') for v in row['transform']]
        if abs(np.linalg.det(matrix(row['transform'])))<1e-7:raise ValueError('Layer transform cannot collapse to zero.')
        if not isinstance(row['crop'],list) or len(row['crop'])!=4:raise ValueError('Invalid crop.')
        row['crop']=[number(v,0.,1.,'crop') for v in row['crop']]
        if row['crop'][2]-row['crop'][0]<.001 or row['crop'][3]-row['crop'][1]<.001:raise ValueError('Crop is empty.')
        masks=row['masks']
        if not isinstance(masks,list) or len(masks)>MAX_MASKS:raise ValueError('At most 8 masks/cuts per layer.')
        for mask in masks:
            if not isinstance(mask,dict) or mask.get('mode') not in ('Keep','Cut') or type(mask.get('enabled')) is not bool:raise ValueError('Invalid mask operation.')
            points=mask.get('points')
            if not isinstance(points,list) or not 3<=len(points)<=MAX_POINTS:raise ValueError('Mask needs 3–128 points.')
            for p in points:
                if not isinstance(p,list) or len(p)!=2:raise ValueError('Invalid mask point.')
                for v in p:number(v,0.,1.,'mask point')
            if mask.get('shape','Path') not in ('Path','Rectangle','Ellipse','Curve'):raise ValueError('Invalid selection shape.')
            handles=mask.get('handles',[])
            if handles:
                if len(handles)!=len(points):raise ValueError('Curve handles must match nodes.')
                for pair in handles:
                    if not isinstance(pair,list) or len(pair)!=2:raise ValueError('Invalid curve handles.')
                    for p in pair:
                        if not isinstance(p,list) or len(p)!=2:raise ValueError('Invalid curve handle.')
                        for v in p:number(v,0.,1.,'curve handle')
            area=abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points))))/2
            if area<1e-6:raise ValueError('Mask polygon is degenerate.')
            # Reject crossing edges instead of ambiguous fill semantics.
            def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            for i in range(len(points) if mask.get('shape','Path')=='Path' else 0):
                a,b=points[i],points[(i+1)%len(points)]
                for j in range(i+2,len(points)):
                    if (j+1)%len(points)==i:continue
                    c,d=points[j],points[(j+1)%len(points)]
                    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:raise ValueError('Mask edges cross; adjust the points.')
        media=row['media']
        if not isinstance(media,dict) or media.get('loop') not in ('None','Loop','Ping-pong'):raise ValueError('Invalid animation settings.')
        media['rate']=number(media.get('rate'),.1,12.,'playback rate');media['start']=number(media.get('start'),0.,86400.,'in point')
        if media.get('end') is not None:
            media['end']=number(media['end'],media['start']+.001,86400.,'out point')
        for key,hi in (('columns',64),('rows',64),('first',4095),('last',4095)):
            v=media.get(key)
            if type(v) is not int or not (0 if key in ('first','last') else 1)<=v<=hi:raise ValueError('Invalid sprite '+key+'.')
        if not media['first']<=media['last']<media['columns']*media['rows']:raise ValueError('Sprite frame range exceeds grid.')
        media['fps']=number(media.get('fps'),.1,120.,'sprite FPS')
        web=row['web']
        if not isinstance(web,dict) or not isinstance(web.get('url'),str) or len(web['url'])>2048:raise ValueError('Invalid web source.')
        from urllib.parse import urlsplit
        u=urlsplit(web['url'])
        if web['url'] and (u.scheme!='https' or not u.hostname or u.username or u.password or u.fragment):raise ValueError('Use a public HTTPS source without embedded credentials/fragments.')
        for k in ('width','height'):
            if type(web.get(k)) is not int or not 64<=web[k]<=2048:raise ValueError('Web viewport must be 64–2048 pixels.')
        if web['width']*web['height']>2*1024*1024:raise ValueError('Web viewport exceeds 2 megapixels.')
        web['cadence']=number(web.get('cadence'),5.,3600.,'web refresh seconds')
        if web.get('offline') not in ('Retain last','Hide') or type(web.get('transparent')) is not bool:raise ValueError('Invalid web presentation.')
        if not isinstance(row['model'],dict):raise ValueError('Invalid model orientation.')
        row['model']={k:number(row['model'].get(k),-36000.,36000.,'model '+k) for k in ('yaw','pitch','roll')}
        alignment=row['cut_alignment']
        if alignment is not None:
            if not isinstance(alignment,dict) or set(alignment)!=set(('parent','geometry','asset')):raise ValueError('Invalid cut alignment.')
            if not isinstance(alignment['parent'],str) or not isinstance(alignment['asset'],str) or not isinstance(alignment['geometry'],dict):raise ValueError('Invalid cut alignment identity.')
            if len(json.dumps(alignment))>2048:raise ValueError('Cut alignment exceeds budget.')
        # Whitelist, so runtime handles and transient previews never enter saves.
        clean.append({k:row[k] for k in new_layer().keys()})
    lookup={r['id']:r for r in clean}
    for r in clean:
        seen={r['id']};parent=r['parent'];depth=0
        while parent is not None:
            if parent in seen or parent not in lookup or lookup[parent]['type'] not in ('Group','Image','Artwork','Paint'):raise ValueError('Invalid/cyclic artwork/group parent.')
            seen.add(parent);parent=lookup[parent]['parent'];depth+=1
            if depth>MAX_DEPTH:raise ValueError('Group nesting is limited to 6 levels.')
    for parent in {r['parent'] for r in clean}:
        siblings=[r for r in clean if r['parent']==parent]
        if len({r['order'] for r in siblings})!=len(siblings):raise ValueError('Sibling layer order must be unique.')
    result=dict(version=4,presentation=data['presentation'],assets=assets,layers=clean,canvas=deepcopy(canvas))
    if result['presentation']!='World only' and sum(r['type'] in ('Video','GIF','Sprite') and effective(result,r,'enabled') for r in clean)>4:raise ValueError('At most 4 visible animated layers; hide a source before adding another.')
    return result
def lookup(scene):return {r['id']:r for r in scene['layers']}
def ancestors(scene,identity):
    rows=lookup(scene);result=[];row=rows[identity]
    while row['parent'] is not None:row=rows[row['parent']];result.append(row)
    return result
def effective(scene,row,key):
    return row[key] and all(a[key] for a in ancestors(scene,row['id'])) if key=='enabled' else row[key] or any(a[key] for a in ancestors(scene,row['id']) if a['type']=='Group')
def world_matrix(scene,identity):
    rows=lookup(scene);row=rows[identity]
    def local(r):return matrix(r['transform'])@(np.diag([-1. if r['flip_x'] else 1.,-1. if r['flip_y'] else 1.,1.]) if r['type']=='Group' else np.eye(3))
    m=local(row)
    for a in ancestors(scene,identity):m=local(a)@m
    return m
def fit_size(size,image,row):
    if row['fit']=='Stretch':return 1.,1.
    w,h=size;iw,ih=image;c=row['crop'];iw*=c[2]-c[0];ih*=c[3]-c[1]
    ratio=(min if row['fit']=='Fit' else max)(w/iw,h/ih)
    return iw*ratio/w,ih*ratio/h
def asset_matrix(scene,row,size,image):
    logical=scene.get('canvas') or size
    ratio=min(size[0]/logical[0],size[1]/logical[1]);output=np.diag([logical[0]*ratio/size[0],logical[1]*ratio/size[1],1.])
    if row['type']=='Group':return output@world_matrix(scene,row['id'])
    fw,fh=fit_size(logical,image,row)
    # Inverse mapping in the shader and the Qt editor both use this matrix.
    return output@world_matrix(scene,row['id'])@np.array([[fw,0.,0.],[0.,fh,0.],[0.,0.,1.]])
def reparent(scene,identity,parent):
    rows=lookup(scene);row=rows[identity];before=world_matrix(scene,identity)
    if parent is not None:
        if parent not in rows or rows[parent]['type'] not in ('Group','Image','Artwork','Paint'):raise ValueError('Choose a group or raster parent.')
        if parent==identity or any(a['id']==identity for a in ancestors(scene,parent)):raise ValueError('Cannot place a branch inside itself.')
        if len(ancestors(scene,parent))+1+max((len(ancestors(scene,r['id']))-len(ancestors(scene,identity)) for r in scene['layers'] if r['id']==identity or any(a['id']==identity for a in ancestors(scene,r['id']))),default=0)>MAX_DEPTH:raise ValueError('Nesting is limited to six levels.')
    pm=world_matrix(scene,parent) if parent else np.eye(3)
    flip=np.diag([-1. if row['flip_x'] else 1.,-1. if row['flip_y'] else 1.,1.]) if row['type']=='Group' else np.eye(3)
    row['parent']=parent;row['transform']=coefficients(np.linalg.inv(pm)@before@flip)
    row['order']=max([r['order'] for r in scene['layers'] if r['parent']==parent and r['id']!=identity],default=-1)+1
def renumber(scene):
    for parent in {r['parent'] for r in scene['layers']}:
        for i,r in enumerate(sorted([r for r in scene['layers'] if r['parent']==parent],key=lambda r:r['order'])):r['order']=i
def is_branch(scene,row):
    return not row.get('_own') and (row['type'] in ('Group','Artwork') or any(r['parent']==row['id'] for r in scene['layers']))

def piece_geometry(row):
    return {k:deepcopy(row[k]) for k in ('fit','crop','flip_x','flip_y')}

def partition_aligned(scene,row):
    """Aligned cut pieces sum premultiplied coverage before parent isolation.

    Source-over would attenuate partially transparent complementary edges twice.
    A moved, painted, restyled or reparented piece resumes ordinary compositing.
    """
    link=row.get('cut_alignment');parent=lookup(scene).get(row['parent'])
    return bool(link and parent and link['parent']==parent['id'] and link['asset']==row['asset'] and
        link['geometry']==piece_geometry(parent)==piece_geometry(row) and row['transform']==IDENTITY and
        row['opacity']==1 and row['blend']=='Normal' and row['blend_strength']==1)

def ordered_children(scene,parent):
    rows=sorted((r for r in scene['layers'] if r['parent']==parent),key=lambda r:r['order'])
    # Complementary pieces reconstruct own pixels before ordinary overlay children.
    rows=[r for r in rows if partition_aligned(scene,r)]+[r for r in rows if not partition_aligned(scene,r)]
    own=lookup(scene).get(parent)
    if own and own['type']!='Group' and own['source_visible']:
        rows.insert(0,dict(own,_own=True,opacity=1.,blend='Normal',blend_strength=1.))
    return rows

def blend_rgba(back,source,mode='Normal'):
    """Reference W3C source-over, premultiplied RGBA display-encoded sRGB."""
    b=np.asarray(back,dtype=float);s=np.asarray(source,dtype=float);ab=b[...,3:4];a=s[...,3:4]
    cb=np.divide(b[...,:3],ab,out=np.zeros_like(b[...,:3]),where=ab>0);cs=np.divide(s[...,:3],a,out=np.zeros_like(s[...,:3]),where=a>0)
    mix={'Normal':lambda:cs,'Multiply':lambda:cb*cs,'Screen':lambda:cb+cs-cb*cs,'Add':lambda:np.minimum(1.,cb+cs),'Difference':lambda:abs(cb-cs)}[mode]()
    return np.concatenate(((1-a)*b[...,:3]+(1-ab)*s[...,:3]+a*ab*mix,a+ab*(1-a)),axis=-1)

class History:
    """Field patches in one owner, scoped recovery with shared aggregate limits.

    Management patches never replace surviving rows wholesale. Removed rows
    retain their latest own content; drawing stacks remain available on restore.
    Immutable raster files remain under the existing bounded artwork store.
    """
    def __init__(self):
        self.undo=[];self.redo=[];self.bytes=0;self.selection=None;self.flags={};self.rows={};self.current=None;self.sequence=0;self.resource_sizes={}
    def remember_flags(self,scene):
        for row in scene['layers']:self.flags[row['id']]={k:row[k] for k in ('enabled','locked','source_visible')}
    @staticmethod
    def meaningful(scene):
        result=deepcopy(scene)
        for row in result['layers']:
            for key in ('enabled','locked','source_visible'):row.pop(key,None)
        return result
    def record(self,before,after,label,before_selection=None,after_selection=None,scope='layers',target=None):
        self.remember_flags(before);self.remember_flags(after)
        self.current=deepcopy(after)
        for row in before['layers']+after['layers']:self.rows[row['id']]=deepcopy(row)
        if self.meaningful(before)==self.meaningful(after):return
        if scope not in ('layers','drawing') or scope=='drawing' and target not in lookup(after):raise ValueError('Invalid history scope/target.')
        self.sequence+=1
        item=dict(before=deepcopy(before),after=deepcopy(after),label=str(label)[:80],before_selection=before_selection,after_selection=after_selection,scope=scope,target=target,sequence=self.sequence)
        self.undo.append(item);self.redo=[i for i in self.redo if (i['scope'],i['target'])!=(scope,target)]
        self.trim(after)
    def trim(self,scene):
        def cost():
            items=self.undo+self.redo
            self.bytes=len(json.dumps([items,self.rows,self.flags]).encode('utf8'))
            refs={a['id']:a for i in items for s in (i['before'],i['after']) for a in s['assets']}
            # Native resources are estimated from their managed-reference metadata
            # by the control owner before recording (never source compression).
            self.raster_bytes=sum(self.resource_sizes.get(k,0) for k in refs)
            return len(items)>64 or self.bytes>8*1024*1024 or self.raster_bytes>256*1024*1024
        while cost() and self.undo+self.redo:
            oldest=min(self.undo+self.redo,key=lambda i:i['sequence'])
            (self.undo if oldest in self.undo else self.redo).remove(oldest)
            retained={r['id'] for i in self.undo+self.redo for s in (i['before'],i['after']) for r in s['layers']}|set(lookup(scene))
            self.rows={k:v for k,v in self.rows.items() if k in retained}
        retained={r['id'] for i in self.undo+self.redo for s in (i['before'],i['after']) for r in s['layers']}|set(lookup(scene))
        self.flags={k:v for k,v in self.flags.items() if k in retained}
        self.rows={k:v for k,v in self.rows.items() if k in retained};cost()
        refs={a['id'] for i in self.undo+self.redo for s in (i['before'],i['after']) for a in s['assets']}
        self.resource_sizes={k:v for k,v in self.resource_sizes.items() if k in refs}
    def item(self,redo=False,scope='layers',target=None):
        source=self.redo if redo else self.undo
        return next((i for i in reversed(source) if i['scope']==scope and i['target']==target),None)
    def peek(self,redo=False,scene=None,scope='layers',target=None):
        item=self.item(redo,scope,target)
        if item is None:return None
        result=deepcopy(scene or self.current);old=item['before'] if redo else item['after'];new=item['after'] if redo else item['before']
        previous,desired=lookup(old),lookup(new);rows=lookup(result)
        for identity in previous.keys()-desired.keys():
            if identity in rows:self.rows[identity]=deepcopy(rows[identity]);result['layers'].remove(rows[identity])
        rows=lookup(result)
        for identity,wanted in desired.items():
            if identity not in previous:
                if identity not in rows:result['layers'].append(deepcopy(self.rows.get(identity,wanted)))
                continue
            current=rows.get(identity)
            if current is None:continue
            for key,value in wanted.items():
                if key not in ('enabled','locked','source_visible') and value!=previous[identity].get(key):current[key]=deepcopy(value)
        for key in ('canvas','presentation'):
            if new.get(key)!=old.get(key):result[key]=deepcopy(new.get(key))
        used={r['asset'] for r in result['layers']};refs={a['id']:a for i in self.undo+self.redo for s in (i['before'],i['after']) for a in s['assets']};refs.update({a['id']:a for s in (old,new,result) for a in s['assets']})
        old_refs={a['id']:a for a in old['assets']}
        for reference in new['assets']:
            if reference['id'] in old_refs and reference!=old_refs[reference['id']]:refs[reference['id']]=deepcopy(reference)
        result['assets']=[deepcopy(refs[i]) for i in used if i in refs]
        for key in ('restore_batch','remove_batch'):
            if key in new:result[key]=deepcopy(new[key])
        for row in result['layers']:row.update(self.flags.get(row['id'],{}))
        return result
    def step(self,redo=False,scene=None,scope='layers',target=None):
        source,destination=(self.redo,self.undo) if redo else (self.undo,self.redo)
        identity=target
        result=self.peek(redo,scene,scope,identity)
        if result is None:return None
        item=self.item(redo,scope,identity);source.remove(item);destination.append(item)
        if redo:destination.sort(key=lambda i:i['sequence'])
        self.selection=(item['after_selection'] if redo else item['before_selection']) if scope=='layers' else identity
        self.current=deepcopy(result)
        for row in result['layers']:self.rows[row['id']]=deepcopy(row)
        self.trim(result)
        return result
    def snapshot(self):
        def scoped(scope,target=None):
            u,r=self.item(False,scope,target),self.item(True,scope,target)
            return dict(undo=u['label'] if u else '',redo=r['label'] if r else '',undo_count=sum(i['scope']==scope and i['target']==target for i in self.undo),redo_count=sum(i['scope']==scope and i['target']==target for i in self.redo))
        return dict(scoped('layers'),selection=self.selection,drawing={k:scoped('drawing',k) for k in self.rows},commands=len(self.undo)+len(self.redo),bytes=self.bytes,raster_bytes=getattr(self,'raster_bytes',0))
