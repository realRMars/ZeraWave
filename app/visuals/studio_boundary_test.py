"""Standalone protocol/admission checks. No Qt/Tk, device or pixel model."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys,threading,time
from studio_boundary import CommandBoundary,AdmissionError,MomentaryMailbox,SectionPublisher,StateSections,SECTIONS

def run(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);checks=[];raw=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    gate=threading.Event();received=[];seen={};dropped=set();applied=[]
    def send(action,**data):
        gate.wait(5);identity=data['operation_id'];received.append(deepcopy(data))
        if identity not in seen:
            seen[identity]=deepcopy(data);applied.append(action)
        if identity not in dropped:
            dropped.add(identity);raise RuntimeError('ACK uncertain')
        return {'accepted':identity}
    boundary=CommandBoundary(send);data=dict(target='layer-a',media_session='session-a',media_revision=7,pixels=[1,2,3])
    began=time.perf_counter();first=boundary.submit('edit',data);raw.append(dict(kind='delayed_admission',ms=(time.perf_counter()-began)*1000))
    data['pixels'][0]=99;data['target']='layer-b'
    rest=[boundary.submit('undo' if i==0 else 'redo' if i==1 else 'save' if i==2 else 'edit',dict(n=i)) for i in range(15)]
    check('local Future cancellation cannot drop a completed command or sequence',rest[0].cancel() is False)
    try:boundary.submit('edit',{})
    except AdmissionError:check('bounded queue rejection',True)
    else:raise AssertionError('unbounded queue')
    check('admission does not await delayed transport',not first.done() and boundary.pending==16)
    try:first.command['target']='different'
    except TypeError:check('immutable captured command',True)
    else:raise AssertionError('mutable command')
    gate.set();first.result(5)
    for future in rest:future.result(5)
    check('lost ACK reconciles same identity exactly once',len(seen)==16 and len(received)==32 and received[0]==received[1])
    check('caller data cannot mutate queued target/pixels',received[0]['target']=='layer-a' and received[0]['pixels']==[1,2,3])
    check('edit history save ordering',applied[:4]==['edit','undo','redo','save'])
    check('resources drain with explicit acknowledged outcome',boundary.pending==0 and boundary.outcome(first.operation_id)['status']=='acknowledged')
    boundary.close()
    box=MomentaryMailbox()
    for _ in range(1000):box.put('hold',dict(owner='studio.mouse',active=True))
    box.put('release',{});check('release survives saturation and cancels pending presses',box.take()==('release',{}) and box.take() is None)
    box.put('hold',dict(owner='studio.Shift_L',active=True));box.put('hold',dict(owner='studio.Shift_L',active=False))
    check('Hold owner release replaces stale press',box.take()[1]['active'] is False)
    state=StateSections();publisher=SectionPublisher('owner-a');tokens={k:1 for k in SECTIONS}
    parts=dict(catalog=dict(catalog={'a':1}),configuration=dict(values=dict(quality=1),destination_revision=2,preview_run='run'),document=dict(values=dict(media={'pixels':[3]}),media_control=dict(session='s',revision=4,history=['edit'],saves=['pinned'])),runtime=dict(telemetry=dict(generation=5)))
    identity=dict(document_session='s',document_revision=4,destination_revision=2,preview_run='run')
    one=publisher.packet(tokens,parts.__getitem__,identity);check('full initial synchronization',state.install(one))
    check('immutable public view',state.immutable['values']['media']['pixels']==(3,))
    before=state.immutable_parts['document'];tokens['runtime']=2;parts['runtime']['telemetry']['generation']=6
    two=publisher.packet(tokens,parts.__getitem__,identity);check('delta reuses coherent document section',state.install(two) and state.immutable_parts['document'] is before and set(two['sections'])=={'runtime'})
    check('catalog not rebuilt for runtime telemetry',publisher.metrics['builds']['catalog']==1)
    missed=publisher.packet(tokens,parts.__getitem__,identity);later=publisher.packet(tokens,parts.__getitem__,identity)
    check('missing delta invalidates without mixed state',not state.install(later) and not state.valid and state.snapshot['media_control']['revision']==4)
    check('explicit full resynchronizes',state.install(publisher.packet(tokens,parts.__getitem__,identity,full=True)))
    malformed=publisher.packet(tokens,parts.__getitem__,dict(identity,document_revision=9),full=True)
    check('incoherent history/document identity rejected',not state.install(malformed) and state.snapshot['media_control']['revision']==4)
    replacement=SectionPublisher('owner-b');check('owner replacement full install',state.install(replacement.packet(tokens,parts.__getitem__,identity)))
    check('late retired-owner reply rejected',not state.install(publisher.packet(tokens,parts.__getitem__,identity,full=True)))
    check('duplicate projection rejected',not state.install(two))
    bad=replacement.packet(tokens,parts.__getitem__,identity,full=True);bad['sections']=[]
    check('malformed delta rejected without disposing coherent state',not state.install(bad) and state.snapshot['media_control']['revision']==4)
    state.invalidate();check('invalid state marked stale to public readers',state.immutable['control_boundary']['valid'] is False)
    check('full recovers after malformed packet',state.install(replacement.packet(tokens,parts.__getitem__,identity,full=True)))
    outcome=dict(checks=checks,raw=raw,command_samples=list(boundary.samples),projection=publisher.metrics,evidence='pure facade and synthetic transport; no widgets or native device')
    (folder/'results.json').write_text(json.dumps(outcome,indent=2),encoding='utf8');print(json.dumps(dict(passed=len(checks),folder=str(folder))))
if __name__=='__main__':run(sys.argv[1])
