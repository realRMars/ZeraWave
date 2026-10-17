"""Version1 manifest recipes expanded to ordinary, individually editable entities.

No template runtime or renderer. Parameters are explicit authoring choices, not
an editorial ducking/content policy. The manifest planner owns conflicts/history.
"""
from copy import deepcopy
import hashlib,json
from video_project import fields,integer,text,style_defaults

KINDS=('entrance','review_card','chapter','caption','music','still')
def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf8')).hexdigest()
def item(category,key,values):return dict(category=category,key=key,values=values)
def expand(manifest):
 result=deepcopy(manifest);summaries=[];seen=set()
 for section in result['sections']:
  for recipe in section.pop('recipes',[]):
   fields(recipe,('key','kind','version','params'));key=recipe['key'];kind=recipe['kind'];params=recipe['params']
   from project_manifest import logical
   logical(key)
   if key in seen or len(seen)>=128:raise ValueError('Recipe keys are unique across the manifest; at most128 explicit instances.')
   seen.add(key)
   if type(recipe['version']) is not int or recipe['version']!=1 or kind not in KINDS or not isinstance(params,dict):raise ValueError('Unsupported recipe kind/version/parameters.')
   common=('track','start','duration');optional=('style','provenance','order')
   required,extra={
    'entrance':(common+('brand','game'),optional+('enter_frames','exit_frames','parts')),
    'review_card':(common+('heading','body'),optional+('parts',)),
    'chapter':(common,optional+('text','range_start','range_end','parts')),
    'caption':(common+('text',),optional),
    'music':(common+('asset','audio'),('name','source_in','rate','pad_end','provenance')),
    'still':(common+('asset',),('name','source_in','layout','provenance'))}[kind]
   fields(params,required,extra);start=integer(params['start']);duration=integer(params['duration'],1,120*24*3600)
   provenance=deepcopy(params.get('provenance',dict(recipe=dict(key=key,kind=kind,version=1,parameters_sha256=fingerprint(params)))))
   if not isinstance(provenance,dict):raise ValueError('Recipe provenance must be an object.')
   parts=params.get('parts',{});allowed={'entrance':{'brand','game'},'review_card':{'heading','body'},'chapter':{'timer','progress'}}.get(kind,set())
   if not isinstance(parts,dict) or set(parts)-allowed or any(not isinstance(v,dict) for v in parts.values()):raise ValueError('Parts must name only this recipe\'s generated text/progress styles.')
   base=dict(track=deepcopy(params['track']),start=start,duration=duration,provenance=provenance)
   made=[]
   def graphic(suffix,content,bounds,size,**extra):
    text(content,4096);style=dict(style_defaults(),bounds=bounds,size=size,padding=12)
    if suffix=='progress':style.update(padding=0,background='#80202c36',color='#9cdec7')
    if 'style' in params:
     if not isinstance(params['style'],dict):raise ValueError('Recipe style must be an object.')
     style.update(deepcopy(params['style']))
    style.update(deepcopy(parts.get(suffix,{})))
    values=dict(base,text=content,style=style,order=params.get('order',0),**extra);made.append(item('graphics',key+'.'+suffix,values));return values
   if kind=='entrance':
    title=graphic('brand',params['brand'],[.06,.08,.88,.17],64);game=graphic('game',params['game'],[.06,.26,.88,.12],38)
    enter=integer(params.get('enter_frames',min(12,duration//4)),0,duration-1);leave=integer(params.get('exit_frames',0),0,duration-1)
    if enter+leave>=duration:raise ValueError('Entrance/exit must fit the explicit duration.')
    for row in (title,game):
     if any(k.get('parameter')=='opacity' for k in row['style'].get('keys',[])):raise ValueError('Recipe opacity already owns entrance keys; do not provide another opacity channel.')
     points={0:[0,0. if enter else 1.,'Linear']}
     if enter:points[enter]=[enter,1.,'Linear']
     if leave:points[duration-1-leave]=[duration-1-leave,1.,'Linear'];points[duration-1]=[duration-1,0.,'Linear']
     if enter or leave:row['style'].setdefault('keys',[]).append(dict(parameter='opacity',points=[points[f] for f in sorted(points)]))
   elif kind=='review_card':
    graphic('heading',params['heading'],[.09,.12,.82,.14],46)
    graphic('body',params['body'],[.09,.28,.82,.38],32)
   elif kind=='chapter':
    begin=integer(params.get('range_start',start),-120*24*3600,120*24*3600);end=integer(params.get('range_end',start+duration),begin+1,120*24*3600)
    graphic('timer',params.get('text','{elapsed} / {duration}'),[.70,.66,.25,.08],28,dynamic='counter',range_start=begin,range_end=end)
    graphic('progress','',[.06,.76,.88,.018],12,dynamic='progress',range_start=begin,range_end=end)
   elif kind=='caption':
    style=deepcopy(params.get('style',{}));made.append(item('captions',key,dict(base,text=params['text'],style=style,order=params.get('order',0))))
   else:
    values=dict(base,name=params.get('name','Music' if kind=='music' else 'Still'),asset=deepcopy(params['asset']),source_in=deepcopy(params.get('source_in',[0,1])))
    if kind=='music':values.update(audio=deepcopy(params['audio']),rate=deepcopy(params.get('rate',[1,1])),pad_end=params.get('pad_end','none'))
    else:values['layout']=deepcopy(params.get('layout',dict(fit='Fit')))
    made.append(item('clips',key,values))
   section['items'].extend(made);summaries.append(dict(section=section['key'],key=key,kind=kind,version=1,parameters_sha256=fingerprint(params),entities=[r['category']+':'+r['key'] for r in made]))
 return result,summaries
