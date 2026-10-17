"""Actual ProjectService/pool review, controlled delay/pressure, ordinary saves.

One disposable12s proof. CPU/source-header preparation only; no Qt, graphics,
device, export movie or production session. Holds/publication changes are labelled.
"""
from pathlib import Path
from copy import deepcopy
from concurrent.futures import Future
from unittest.mock import patch
import os,sys,json,time,threading,shutil,struct,traceback,hashlib
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);destination=Path(sys.argv[3]);assert not destination.exists();os.environ.update(ZERAWAVE_PROJECT_RECOVERY=str(out/'recovery'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'))
from project_service import ProjectService
from project_review import inspect_review,source_interval,remember_change,marks,MARK_KEY,export_request
from project_audio_inspection import inspect_audio
from video_project import new_id,pair,fail
source_files=['project_review.py','project_review_owner_test.py','project_service.py','project_source.py','video_project.py','project_audio_inspection.py','project_export.py']
source_hashes={name:hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest() for name in source_files};(out/'SOURCE.json').write_text(json.dumps(source_hashes,indent=2),encoding='utf8')
s=ProjectService();gate=threading.Event();entered=threading.Event();checks=[];admission=[];records=[]
def binding():return dict(expected_epoch=s.epoch,expected_revision=s.revision,expected_project=(s.document or {}).get('id'),expected_command=s.command_revision)
def wait(fn,seconds=20):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        s.poll()
        if fn():return
        time.sleep(.002)
    raise AssertionError('Owner review timeout')
def op(kind,**kw):
    key=new_id();request=dict(op=kind,operation_id=key,**binding(),**kw);r=s.request(request);assert r['ok'],r
    if r['outcome']['status'] in ('preparing','saving','exporting'):wait(lambda:s.outcomes[key]['status'] not in ('preparing','saving','exporting'))
    assert s.outcomes[key]['status'] in ('accepted','durable'),s.outcomes[key];return s.outcomes[key]
def query(source_context=False,**kw):
    clip=next(c for c in s.document['clips'] if c['provenance'].get('component',{}).get('instance_key')=='review-1' and c['provenance']['component']['part']=='background');asset=next(a for a in s.document['media'] if a['id']==clip['asset']);span=source_interval(s.document,clip,asset)
    data=dict(op='review_inspect',**binding(),query_id=new_id(),source=asset['id'],source_range=[pair(v) for v in span],handles=[18,30],range=[90,210],purpose='Owner exact boundary sample',clip=clip['id'])
    if source_context:data['source_epoch']=s.source.epoch
    data.update(kw);began=time.perf_counter_ns();reply=s.request(data);admission.append((time.perf_counter_ns()-began)/1e6);return reply,data
def resolved(**kw):
    f,data=query(**kw);assert isinstance(f,Future),f;wait(f.done);r=f.result();assert r['ok'],r;return r['report'],data
def held(function):
    def run(*args,**kw):
        entered.set();cancel=args[-1];until=time.monotonic()+10
        while not gate.wait(.01):
            if cancel.is_set():return function(*args,**kw)
            if time.monotonic()>until:raise AssertionError('Controlled owner hold timed out')
        return function(*args,**kw)
    return run
def hold():gate.clear();entered.clear()
def finish():gate.set();wait(lambda:not s.inspections and not s.jobs)
try:
    op('open',path=str(proof));original=deepcopy(s.document);saved=s.saved_revision;history=s.history_bytes;commands=s.command_revision
    for _ in range(20):r,_=resolved()
    assert s.document==original and s.saved_revision==saved and s.history_bytes==history and s.command_revision==commands
    checks.append('20 actual bounded owner/worker queries, immutable snapshots and final reconciliation cause no document/history/saved/command edit; raw admission timings retained')
    asset=next(a for a in s.document['media'] if a['id']==r['source']['id']);op('transport',action='seek_paused',frame=120);op('source_open',asset=asset);program=deepcopy(s.transport.state());audible=s.audio_target
    with patch('project_review.inspect_review',side_effect=held(inspect_review)):
        hold();f,q=query(True);assert entered.wait(3) and not f.done();op('transport',action='range',frame=[4488,4566],target='source',source_epoch=s.source.epoch);op('transport',action='seek_paused',frame=4488,target='source',source_epoch=s.source.epoch)
        assert s.transport.state()['frame']==program['frame'] and s.transport.active==program['active'] and s.audio_target==audible;finish();assert f.result()['ok'] and f.result()['report']['source']['requested_interval']==q['source_range']
    checks.append('Actual explicit Source handled range/seek during delayed read leaves Program position/active ownership/audio target unchanged; result retains its original requested interval, no silent clock retarget')
    voice=next(c for c in s.document['clips'] if c['provenance'].get('component',{}).get('part')=='voice')
    for values in [dict(gain=.3),dict(envelope=[[0,.9],[200,.2]])]:
        with patch('project_review.inspect_review',side_effect=held(inspect_review)):
            hold();f,q=query();assert entered.wait(3);op('batch',label='Pending review audio dependency edit',changes=[dict(op='clip.audio',id=voice['id'],values=values)]);finish();assert f.result()['error']['code']=='stale_revision';op('undo');assert s.document==original
    # Real valid MP4 replacement: copy task media and append an ISO BMFF free
    # box. Different SHA/path, same valid source extent/native pictures/audio.
    replacement=out/'replacement.mp4';shutil.copyfile(asset['location']['path'],replacement)
    with replacement.open('ab') as f:f.write(struct.pack('>I4s',8,b'free'))
    with patch('project_review.inspect_review',side_effect=held(inspect_review)):
        hold();f,q=query();assert entered.wait(3);op('batch',label='Explicit task source replacement while review pending',changes=[dict(op='media.relink',id=asset['id'],kind='Video',location=dict(kind='external',path=str(replacement)),sha256=hashlib.sha256(replacement.read_bytes()).hexdigest(),metadata={},accept_changed=True)]);finish();assert f.result()['error']['code']=='stale_revision';changed=deepcopy(s.document);assert next(a for a in changed['media'] if a['id']==asset['id'])['sha256']!=asset['sha256'];op('undo');assert s.document==original
    checks.append('Gain/envelope and real verified MP4 source relink/replacement during held review reject stale completion; exact ordinary Undo restores accepted content; replacement is new task-owned valid-container copy, no production mutation')
    other=next(a for a in s.document['media'] if a['kind']=='Video' and a['sha256']!=asset['sha256'])
    with patch('project_review.inspect_review',side_effect=held(inspect_review)):
        hold();f,q=query(True);assert entered.wait(3);op('source_open',asset=other);finish();assert f.result()['error']['code']=='stale_source'
    with patch('project_review.inspect_review',side_effect=held(inspect_review)):
        hold();f,q=query();assert entered.wait(3);before=deepcopy(s.media_state);s.media_state[asset['id']]['status']='Missing';finish();assert f.result()['error']['code']=='stale_source_verification';s.media_state=before
    checks.append('Actual Source replacement without document edit and controlled last-verification publication change reject held results at owner boundary, not merely GUI')
    with patch('project_review.inspect_review',side_effect=held(inspect_review)):
        hold();f,q=query();assert entered.wait(3);command=s.command_revision;r=s.request(dict(op='review_cancel',query_id=q['query_id']));assert r['ok'] and r['cancel_requested'];finish();assert f.result()['error']['code']=='cancelled' and s.command_revision==command
        # Late cancellation must not publish a completed read as Ready either.
        hold();f,q=query();assert entered.wait(3);gate.set();waiter=next(iter(s.inspections.values()))['future'];waiter.result(timeout=10);s.request(dict(op='review_cancel',query_id=q['query_id']));s.poll();assert f.result()['error']['code']=='cancelled'
    checks.append('Explicit read-query cancellation including completed-worker/owner-not-yet-reconciled race never returns Ready; no revision/command/history mutation or automatic duplicate query')
    with patch('project_review.inspect_review',side_effect=held(inspect_review)),patch('project_audio_inspection.inspect_audio',side_effect=held(inspect_audio)):
        hold();pending=[query()[0] for _ in range(2)];audio=s.request(dict(op='audio_inspect',**binding(),range=[90,210]));pending.append(audio);assert entered.wait(3)
        queued=[]
        for i in range(13):
            key=new_id();r=s.request(dict(op='save',operation_id=key,**binding(),path=str(out/f'cancelled-pressure-{i}.zwv'),portable=False));assert r['ok'] and r['outcome']['status']=='saving';queued.append(key)
        assert len(s.inspections)==3 and len(s.jobs)==13
        with patch.object(s.pool,'submit',wraps=s.pool.submit) as submits:
            refused,_=query();assert not refused['ok'] and refused['error']['code']=='busy' and submits.call_count==0
        op('batch',label='Synchronous edit while preparation full',changes=[dict(op='project.rename',name='Explicit temporary label')]);op('undo');assert s.document==original
        for job in s.jobs.values():job['cancel'].set()
        for job in s.inspections.values():job['cancel'].set()
        finish();assert all(f.result()['error']['code']=='cancelled' for f in pending) and all(s.outcomes[k]['status']=='failed' for k in queued)
    r,_=resolved();assert r['status']=='ready' and s.document==original
    checks.append('Actual mixed2review+1audio+13pinnedSave pressure reaches shared16; new review refused before pool submit, synchronous edit/Undo allowed, cancel/drain all jobs then same-service fresh review succeeds')
    # The existing exporter itself is mocked ONLY in these bridge/failure cases.
    # Actual filesystem destination errors/ordinary owner ledger/Source guards
    # are exercised; this produces ZERO native movies or graphics contexts.
    unplaced=dict(asset,id=new_id(),name='Unplaced task Source',location=dict(kind='external',path=str(replacement)),sha256=hashlib.sha256(replacement.read_bytes()).hexdigest(),metadata={});op('source_open',asset=unplaced);r,_=resolved();unplaced_sha=hashlib.sha256(replacement.read_bytes()).hexdigest()
    with patch('project_export.export_project',side_effect=AssertionError('Unplaced Source overwrite reached native export')) as native:
        data=export_request(r,binding(),str(replacement),new_id());reply=s.request(data);assert reply['ok'];wait(lambda:data['operation_id'] not in s.jobs);row=s.outcomes[data['operation_id']];assert row['status']=='failed' and row['error']['code']=='protected_source' and native.call_count==0
    assert hashlib.sha256(replacement.read_bytes()).hexdigest()==unplaced_sha
    prior=out/'prior-output.mp4';shutil.copyfile(other['location']['path'],prior);prior_sha=hashlib.sha256(prior.read_bytes()).hexdigest();native_entered=threading.Event()
    def delegate(document,epoch,revision,path,crf,folder,cancel,extra,frame_range):
        native_entered.set()
        while not gate.wait(.01):
            if cancel.is_set():fail('cancelled','Controlled existing-delegate cancellation; no movie created.')
        if cancel.is_set():fail('cancelled','Controlled existing-delegate cancellation; no movie created.')
        return dict(mocked_existing_export=True,path=path,revision=revision,epoch=epoch,project=document['id'],frame_range=frame_range)
    gate.clear()
    with patch('project_export.export_project',side_effect=delegate):
        data=export_request(r,binding(),str(prior),new_id());reply=s.request(data);assert reply['ok'];assert native_entered.wait(3);epoch=s.source.epoch
        for _ in range(70):op('transport',action='range',frame=[90,210])
        assert not any(o['id']==data['operation_id'] for o in s.state(False)['operations']);assert s.request(dict(op='operation_status',operation_id=data['operation_id']))['outcome']['status']=='exporting'
        target=dict(other,id=new_id(),name='Pending destination as Source',location=dict(kind='external',path=str(prior)),metadata={});key=new_id();reply=s.request(dict(op='source_open',operation_id=key,**binding(),asset=target));assert reply['ok'];wait(lambda:key not in s.jobs);assert s.outcomes[key]['status']=='failed' and s.outcomes[key]['error']['code']=='reserved_destination' and s.source.epoch==epoch
        gate.set();wait(lambda:data['operation_id'] not in s.jobs);result=s.outcomes[data['operation_id']]['result'];assert result['mocked_existing_export'] and Path(result['review_certificate_path']).is_file();assert hashlib.sha256(prior.read_bytes()).hexdigest()==prior_sha
    blocked=out/'not-a-directory';blocked.write_text('Retain prior bytes',encoding='utf8')
    def write_fault(document,epoch,revision,path,*args):Path(path).parent.mkdir(parents=True,exist_ok=True);raise AssertionError('Expected a real destination failure')
    with patch('project_export.export_project',side_effect=write_fault):
        data=export_request(r,binding(),str(blocked/'sample.mp4'),new_id());reply=s.request(data);assert reply['ok'];wait(lambda:data['operation_id'] not in s.jobs);failed=deepcopy(s.outcomes[data['operation_id']]);assert failed['status']=='failed' and 'Exact review certificate retained:' in str(failed['error']['notes']);assert s.request(data)['outcome']==failed
    assert blocked.read_text(encoding='utf8')=='Retain prior bytes' and s.document==original
    with patch('project_export.export_project',side_effect=delegate):
        gate.clear();native_entered.clear();data=export_request(r,binding(),str(out/'cancel-no-movie.mp4'),new_id());assert s.request(data)['ok'] and native_entered.wait(3);s.request(dict(op='cancel',operation_id=data['operation_id']));wait(lambda:data['operation_id'] not in s.jobs);assert s.outcomes[data['operation_id']]['error']['code']=='cancelled';assert not (out/'cancel-no-movie.mp4').exists();gate.set()
        data=export_request(r,binding(),str(out/'retry-no-movie.mp4'),new_id());assert s.request(data)['ok'];wait(lambda:data['operation_id'] not in s.jobs);assert s.outcomes[data['operation_id']]['status']=='exported' and s.outcomes[data['operation_id']]['result']['mocked_existing_export']
    assert s.document==original and hashlib.sha256(prior.read_bytes()).hexdigest()==prior_sha
    checks.append('Controlled existing-export delegate (ZERO movies/GPU): actual unplaced Source overwrite protection, pending-output Source-open refusal, SAME-ID status beyond64-row short view, persisted exact review certificate, real file-as-directory failure/retained prior bytes, SAME-ID failed replay, cancel and explicit retry preserve owner document/output; native core evidence remains separate')
    markid=new_id();before=deepcopy(s.document);op('batch',label='Remember exact review purpose and range',changes=[remember_change(s.document,r,markid,binding())]);remembered=deepcopy(s.document);assert marks(remembered)['items'][0]['id']==markid;op('undo');assert s.document==before;op('redo');assert s.document==remembered
    op('save',path=str(destination),portable=True);op('close');op('open',path=str(destination));assert s.document['provenance']==remembered['provenance'] and all(s.document[k]==remembered[k] for k in ('clips','graphics','tracks','master','buses'))
    checks.append('Authored purpose/exact ranges/hash/placement metadata uses ordinary named Undo/Redo and portable new SaveAs/Close/Open; all editable pixels/audio recipes and stable IDs preserved')
    # Real missing file through ordinary Open/availability, not a fake Ready row.
    missing=deepcopy(s.document);next(a for a in missing['media'] if a['id']==asset['id'])['location']=dict(kind='external',path=str(out/'absent-source.mp4'));missing_path=out/'missing-source.zwv';missing_path.write_text(json.dumps(dict(format='zerawave-video-project-file',version=1,revision=s.revision,document=missing)),encoding='utf8');op('close');op('open',path=str(missing_path));r,_=resolved();assert r['status']=='unavailable' and any(a['validation']['status']=='Missing' for a in r['unavailable']) and marks(s.document)['items'][0]['id']==markid;op('close');op('open',path=str(destination));r,_=resolved();assert r['status']=='ready'
    checks.append('Actual missing-source Open reports Unavailable without discarding saved note/ranges; reopening the good disposable checkpoint restores Ready in the same service')
    with patch('project_review.inspect_review',side_effect=held(inspect_review)):
        hold();f,q=query();assert entered.wait(3);assert not s.can_shutdown(discard=False,binding=binding());gate.set();wait(lambda:not s.inspections);assert f.result()['error']['code']=='cancelled';wait(lambda:s.can_shutdown(discard=False,binding=binding()))
    s.shutdown();assert s.closed and all(not t.is_alive() for t in s.pool._threads)
    checks.append('Normal saved-service shutdown cancels/drains pending read before private snapshots/pool retire; no live session replacement or abandoned worker')
    assert all(hashlib.sha256((root/'app/visuals'/name).read_bytes()).hexdigest()==sha for name,sha in source_hashes.items());(out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,raw_admission_ms=admission,classification=__doc__,proof=str(destination),proof_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),owned_workers_exited=True,source_unchanged=True),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');(out/'PARTIAL.json').write_text(json.dumps(dict(checks=checks,raw_admission_ms=admission),indent=2),encoding='utf8');raise
finally:
    gate.set()
    if not s.closed:
        for job in list(s.jobs.values())+list(s.inspections.values()):job['cancel'].set()
        wait(lambda:not s.jobs and not s.inspections);s.shutdown()
