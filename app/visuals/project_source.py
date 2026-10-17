"""Read-only Source context, serviced by the existing project/audio owner.

It owns no output device, accepted document, history or saved project. Source
preparation uses the existing verified importer on a bounded owner worker.
"""
from fractions import Fraction
from copy import deepcopy
import uuid
from video_project import create,apply,rational,fail
from project_transport import Transport

def prepare_source(asset,operation,cancel):
 from project_service import prepare_changes
 if not isinstance(asset,dict):fail('invalid_source','Choose a verified Library source.')
 fields=('id','name','kind','location','sha256','metadata')
 if any(k not in asset for k in fields):fail('invalid_source','Source identity and explicit location are required.')
 change=dict(op='media.add',**{k:deepcopy(asset[k]) for k in fields},provenance={})
 source=prepare_changes([change],None,cancel)[0];meta=source['metadata'];fps=meta.get('rational_fps') or [30,1]
 # Video inspection supplies exact container ticks, avoiding a float-duration
 # roundtrip that can turn five CFR frames into4. VFR keeps the documented
 # complete nominal-grid interval policy; no blind ceil invents a tail frame.
 length=rational(meta['duration_time']) if 'duration_time' in meta else Fraction(str(meta.get('duration',1)))
 if source['kind']=='Audio':
  from project_audio_timing import natural_frames
  end=natural_frames(meta,fps)
 else:end=1 if source['kind']=='Image' else max(1,int(length*rational(fps)))
 settings=dict(width=max(16,meta.get('width',1280)),height=max(16,meta.get('height',720)),fps=fps)
 d=create('Source — '+source['name'],settings,uuid.uuid5(uuid.UUID(operation),'source-document').hex);changes=[source]
 for kind in (['video'] if source['kind']!='Audio' else [])+(['audio'] if source['kind']=='Audio' or meta.get('has_audio') else []):
  key=uuid.uuid5(uuid.UUID(operation),kind+'-track').hex
  changes.extend([dict(op='track.add',id=key,kind=kind,name='Source '+kind),dict(op='clip.add',id=uuid.uuid5(uuid.UUID(operation),kind+'-clip').hex,asset=source['id'],track=key,start=0,duration=end,**({'pad_end':'silence'} if source['kind']=='Audio' else {}))])
 return apply(d,changes,operation)[0]

class SourceContext:
 def __init__(self):self.document=None;self.epoch=uuid.uuid4().hex;self.revision=0;self.transport=Transport()
 def install(self,document):
  def key(doc):
   a=doc['media'][0];return a['id'],a['sha256'],a['location']
  if self.document and key(self.document)==key(document):return
  self.document=document;self.epoch=uuid.uuid4().hex;self.transport.sync(document,self.epoch,self.revision)
 def state(self,full=True):
  self.transport.sync(self.document,self.epoch,self.revision)
  return dict(document=deepcopy(self.document) if full else None,epoch=self.epoch,revision=self.revision,transport=self.transport.state())
 def release(self):
  if self.document:self.transport.command('release')
 def clear(self):self.release();self.document=None;self.transport.sync(None,self.epoch,self.revision)
