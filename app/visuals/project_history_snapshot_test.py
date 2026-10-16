"""Owner-private immutable history and requested-save pin preservation."""
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from unittest.mock import patch
import os,time,uuid,json,threading,hashlib
from project_service import ProjectService,read_project
from video_project import validate

def run(folder):
 folder=Path(folder);checks=[];barrier=folder/'save.barrier';barrier.touch();env=dict(ZERAWAVE_PROJECT_RECOVERY=str(folder/'recovery'),ZERAWAVE_PROJECT_TEST_SAVE_BARRIER=str(barrier))
 with patch.dict(os.environ,env):
  service=ProjectService()
  def request(op,wait=True,**args):
   state=service.state(False);packet=dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['project_id'],expected_command=state['command_revision'],**args);reply=service.request(packet);assert reply['ok'],reply;key=packet['operation_id'];end=time.monotonic()+10
   if wait:
    while key in service.jobs:service.poll();time.sleep(.001);assert time.monotonic()<end
    assert service.outcomes[key]['status'] in ('accepted','durable'),service.outcomes[key]
   return key,packet
  try:
   request('new',name='Snapshot reference');track=uuid.uuid4().hex;title=uuid.uuid4().hex;request('batch',changes=[dict(op='track.add',id=track,kind='graphics'),dict(op='graphic.add',id=title,track=track,start=0,duration=90,text='Accepted title')]);pinned=deepcopy(service.document);revision=service.revision;save,_=request('save',wait=False,path=str(folder/'pinned.zwv'),portable=False);previous=deepcopy(service.document);first_after=service.undo[-1]['after'];first_digest=hashlib.sha256(json.dumps(first_after,sort_keys=True).encode()).hexdigest()
   for index in range(100):
    _,packet=request('batch',changes=[dict(op='project.rename',name='Accepted revision '+str(index))]);packet['changes'][0]['name']='Caller mutation must not reach history';public=service.state();public['document']['graphics'][0]['style']['bounds'][0]=.8;detached=validate(service.document);detached['name']='Detached validation mutation';assert service.document['name']=='Accepted revision '+str(index)
    assert hashlib.sha256(json.dumps(first_after,sort_keys=True).encode()).hexdigest()==first_digest
    if index%10==0:
     current=deepcopy(service.document);request('undo');assert service.document==previous;request('redo');assert service.document==current
    previous=deepcopy(service.document)
   assert all(a['after'] is b['before'] or a['after']==b['before'] for a,b in zip(service.undo,service.undo[1:]));snapshots={id(row[key]) for row in service.undo for key in ('before','after')};assert len(snapshots)<2*len(service.undo);assert service.history_bytes==sum(row['bytes'] for row in service.undo+service.redo)
   checks.append('100 accepted operations retained with exact intermediate Undo/Redo; public snapshots, caller packets and default validation are detached; oldest history remains byte-identical while immutable values share ownership')
   expected=deepcopy(service.document);accepted_revision=service.revision;barrier.unlink();end=time.monotonic()+10
   while save in service.jobs:service.poll();time.sleep(.001);assert time.monotonic()<end
   assert service.outcomes[save]['status']=='durable';assert read_project(folder/'pinned.zwv',threading.Event())[:2]==(pinned,revision);assert service.saved_revision==revision and service.revision==accepted_revision and service.document==expected and service.state()['dirty'];checks.append('Slow real save pins its original complete revision while100 newer edits remain accepted/dirty; durable older receipt does not claim to save newer work')
   request('save',path=str(folder/'latest.zwv'),portable=False);assert read_project(folder/'latest.zwv',threading.Event())[:2]==(expected,accepted_revision);assert not service.state()['dirty'];checks.append('Save As secures the latest accepted document after the older save drains; both editable files reopen with exact IDs/content/keys/settings')
   return dict(classification=__doc__,checks=checks,history_entries=len(service.undo),unique_retained_document_values=len(snapshots),conservative_serialized_history_bytes=service.history_bytes,latest_revision=accepted_revision)
  finally:
   barrier.unlink(missing_ok=True)
   while service.jobs:service.poll();time.sleep(.001)
   service.shutdown()

if __name__=='__main__':
 with TemporaryDirectory(prefix='zerawave-history-snapshots-') as folder:result=run(folder)
 print(json.dumps(result,indent=2))
