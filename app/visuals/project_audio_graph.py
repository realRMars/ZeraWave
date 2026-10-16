"""Bounded audio routing policy; no devices, decoding or authoring authority.

The document owner validates/edits this recipe; canonical Mixer executes it for
preview and export. Missing routes are explicit recovery data, never Master.
"""
from copy import deepcopy
import uuid

MAX_BUSES=16
OP_FIELDS={'bus.add':(('name',),('id','output','gain','balance','mute','solo')),'bus.edit':(('id','values'),()),'bus.remove':(('id',),('reroute',)),'track.output':(('id','output'),()),'master.audio':(('values',),())}
def model():import video_project;return video_project
def master_defaults():return dict(gain=1.,mute=False)
def bus_defaults(key,name):return dict(id=key,name=name,output='master',gain=1.,balance=0.,mute=False,solo=False)
def route(value):
 if value is not None and value!='master':model().identity(value)
def missing_routes(document):
 buses={b['id'] for b in document.get('buses',[])}
 return [dict(id=t['id'],name=t['name'],destination=t['output']) for t in document['tracks'] if t.get('output') not in (None,'master') and t['output'] not in buses]
def validate(document,allow_missing=False):
 v=model();buses=document.get('buses',[]);master=document.get('master',master_defaults())
 if not isinstance(buses,list) or len(buses)>MAX_BUSES:v.fail('bus_capacity','At most16 named buses; accepted routes retained.')
 seen={document['id']}|{r['id'] for c in ('media','tracks','clips','captions','graphics') for r in document[c]}
 for bus in buses:
  v.fields(bus,('id','name','output','gain','balance','mute','solo'));v.identity(bus['id'])
  if bus['id'] in seen:v.fail('duplicate_id','Bus IDs are stable and unique independently of names.')
  seen.add(bus['id']);v.text(bus['name'],128)
  if not bus['name'].strip():v.fail('invalid_bus','A bus needs a nonempty name.')
  if bus['output'] not in (None,'master'):v.fail('invalid_route','Bus output is Master or None; no sends or bus-to-bus routes.')
  v.number(bus['gain'],0,4);v.number(bus['balance'],-1,1)
  if type(bus['mute']) is not bool or type(bus['solo']) is not bool:v.fail('invalid_audio','Bus Mute/Solo must be booleans.')
 v.fields(master,('gain','mute'));v.number(master['gain'],0,4)
 if type(master['mute']) is not bool:v.fail('invalid_audio','Master mute must be boolean.')
 for track in document['tracks']:
  if 'output' in track:
   if track['kind']!='audio':v.fail('invalid_route','Only explicit audio tracks have an audio destination.')
   route(track['output'])
 missing=missing_routes(document)
 if missing and not allow_missing:v.fail('missing_audio_destination','Missing audio destination for '+', '.join(t['name'] for t in missing)+'. Choose Master, None or an existing named bus; no audio was rerouted.')
 return missing
def apply_edit(document,change,operation,index):
 v=model();op=change['op'];created=[]
 if op=='bus.add':
  key=change.get('id') or uuid.uuid5(uuid.UUID(operation),'bus-'+str(index)).hex;row=bus_defaults(key,change['name']);row.update({k:deepcopy(value) for k,value in change.items() if k not in ('op','id','name')});document.setdefault('buses',[]).append(row);created.append(key)
 elif op in ('bus.edit','bus.remove'):
  row=next((b for b in document.get('buses',[]) if b['id']==change['id']),None)
  if row is None:v.fail('missing_bus','This named bus no longer exists.')
  if op=='bus.edit':
   if not isinstance(change['values'],dict) or set(change['values'])-{'name','output','gain','balance','mute','solo'}:v.fail('invalid_bus','Bus edits preserve stable ID and use supported controls.')
   row.update(deepcopy(change['values']))
  else:
   tracks=[t for t in document['tracks'] if t.get('output')==row['id']]
   if tracks and 'reroute' not in change:v.fail('occupied_bus','Bus feeds '+', '.join(t['name'] for t in tracks)+'. Explicitly reroute to Master or disconnect to None, or cancel.')
   if change.get('reroute') not in (None,'master'):v.fail('invalid_route','Removed-bus tracks must explicitly select Master or None.')
   for t in tracks:t['output']=change['reroute']
   document['buses'].remove(row)
 elif op=='track.output':
  track=v._find(document,'tracks',change['id'])
  if track['kind']!='audio':v.fail('invalid_track','Visual-only tracks have no audio output; use linked audio clips.')
  track['output']=change['output']
 elif op=='master.audio':
  if not isinstance(change['values'],dict) or set(change['values'])-{'gain','mute'}:v.fail('invalid_audio','Master exposes gain/mute; device volume is separate and there is no Master pan.')
  document.setdefault('master',master_defaults()).update(deepcopy(change['values']))
 return created
def plan(document):
 tracks=sorted((deepcopy(t) for t in document['tracks'] if t['kind']=='audio'),key=lambda t:t['order'])
 for track in tracks:track.setdefault('output','master')
 return dict(tracks=tracks,buses=deepcopy(document.get('buses',[])),master=deepcopy(document.get('master',master_defaults())),missing=missing_routes(document),pan_law='Mono duplicated at center0dB/channel; linear L/R balance, center unity, extreme mutes opposite channel; stereo uses same balance law')
