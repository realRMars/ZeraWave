"""Actual ProjectService/pool controlled delayed query, pressure and retirement.

Uses the generated12s proof; worker hold is injected, authoring/guards/poll/close
are real. No GUI, device, GPU, live owner or production project.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from concurrent.futures import Future
import os,sys,json,time,threading,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);os.environ['ZERAWAVE_PROJECT_RECOVERY']=str(out/'recovery')
from project_service import ProjectService
from project_audio_inspection import inspect_audio
from video_project import new_id,ProjectError
s=ProjectService();checks=[];admission=[];gate=threading.Event();began=threading.Event()
def wait(fn,seconds=15):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        s.poll()
        if fn():return
        time.sleep(.002)
    raise AssertionError('Owner test timed out')
def binding():return dict(expected_epoch=s.epoch,expected_revision=s.revision,expected_project=(s.document or {}).get('id'),expected_command=s.command_revision)
def op(kind,**kw):
    key=new_id();r=s.request(dict(op=kind,operation_id=key,**binding(),**kw));assert r['ok'],r
    if r['outcome']['status'] in ('preparing','saving','exporting'):wait(lambda:s.outcomes[key]['status'] not in ('preparing','saving','exporting'))
    assert s.outcomes[key]['status'] in ('accepted','durable'),s.outcomes[key]
def query(**kw):return s.request(dict(op='audio_inspect',**binding(),range=[0,360],**kw))
def held(*args,**kw):
    began.set()
    if not gate.wait(10):raise AssertionError('Controlled query hold not released')
    return inspect_audio(*args,**kw)
def finish():
    gate.set();wait(lambda:not s.inspections)
try:
    op('open',path=str(proof));snapshot=deepcopy(s.document);saved=s.saved_revision;history=s.history_bytes;commands=s.command_revision
    for _ in range(20):
        t=time.perf_counter_ns();f=query();admission.append((time.perf_counter_ns()-t)/1e6);assert isinstance(f,Future);wait(f.done);assert f.result()['ok']
    assert s.document==snapshot and s.saved_revision==saved and s.history_bytes==history and s.command_revision==commands
    checks.append('20 actual detached-worker queries reconcile on owner, no command/revision/history/saved-state mutation; raw owner-admission latency retained')
    # Same12s proof/input identities; temporary ordinary authored stress variant.
    keys=[new_id() for _ in range(8)];changes=[dict(op='track.add',id=k,kind='audio',name='Stress '+str(i)) for i,k in enumerate(keys)]
    asset=s.document['media'][0]['id']
    changes.extend(dict(op='clip.add',asset=asset,track=keys[i%8],start=(i//8)*20,duration=20,audio=dict(gain=.04,envelope=[[p,.5+(p%3)*.1] for p in range(21)])) for i in range(128))
    for at in range(0,len(changes),128):op('batch',label='Temporary query stress',changes=changes[at:at+128])
    large=[];commands_while_pending=[]
    for i in range(5):
        t=time.perf_counter_ns();f=query(limit=8);large.append((time.perf_counter_ns()-t)/1e6)
        t=time.perf_counter_ns();op('transport',action='seek_paused',frame=30+i);commands_while_pending.append((time.perf_counter_ns()-t)/1e6)
        wait(f.done);assert f.result()['ok'] and f.result()['report']['total_contributions']==131
    op('undo');op('undo');assert s.document==snapshot
    checks.append('128additional clips/8tracks/21envelope points measured on same12s proof; owner admission and ordinary transport remain separate from worker calculation, temporary edits undone exactly')
    with patch('project_audio_inspection.inspect_audio',side_effect=held):
        gate.clear();began.clear();f=query();assert began.wait(3) and not f.done()
        # Ordinary transport and named authoring remain usable while worker waits.
        op('transport',action='seek_paused',frame=120);assert s.transport.state()['frame']==120 and not f.done()
        track=next(t for t in s.document['tracks'] if t['kind']=='audio');op('batch',label='Gain while inspection pending',changes=[dict(op='track.audio',id=track['id'],values=dict(gain=.5))]);assert not f.done()
        finish();assert not f.result()['ok'] and f.result()['error']['code']=='stale_revision';op('undo');assert s.document==snapshot
    checks.append('Real owner transport and gain edit proceed during controlled worker hold; obsolete accepted-revision report rejected at final reconciliation, exact Undo retains accepted content')
    with patch('project_audio_inspection.inspect_audio',side_effect=held):
        gate.clear();began.clear();f=query();assert began.wait(3);key=next(iter(s.media_state));before=deepcopy(s.media_state);revision=s.revision;s.media_state[key]['status']='Missing'
        finish();assert f.result()['error']['code']=='stale_source_verification' and s.revision==revision;s.media_state=before
    checks.append('Controlled authoritative availability change without document revision rejects held Ready result on owner, not merely on GUI')
    with patch('project_audio_inspection.inspect_audio',side_effect=held):
        gate.clear();began.clear();futures=[query() for _ in range(4)];assert began.wait(3) and all(isinstance(f,Future) for f in futures)
        refused=query();assert not refused['ok'] and refused['error']['code']=='busy' and len(s.inspections)==4
        for job in s.inspections.values():job['cancel'].set()
        finish();assert all(f.result()['error']['code']=='cancelled' for f in futures)
    assert query().done() is False;wait(lambda:not s.inspections)
    checks.append('Four-query pressure explicitly rejects fifth, all held queries cancel before report publication and retire; same service accepts fresh query afterward')
    # Mixed pressure uses real queued pinned saves, not fake job counters.
    # Hold the two actual pool workers in inspection while all12 saves queue.
    from project_recovery import publish
    recovery=publish(s.recovery.root,new_id(),0,None,s.document,s.epoch,s.revision,s.saved_revision,s.path)
    cue=out/'pressure.srt';cue.write_text('1\n00:00:00,000 --> 00:00:01,000\nPressure cue\n',encoding='utf8')
    asset=deepcopy(s.document['media'][0]);graphics=next(t['id'] for t in s.document['tracks'] if t['kind']=='graphics')
    addition=dict(op='media.add',id=new_id(),name='Explicit retry source',kind=asset['kind'],location=deepcopy(asset['location']),sha256=asset['sha256'],metadata=deepcopy(asset['metadata']))
    relink=dict(op='media.relink',id=asset['id'],**{k:deepcopy(asset[k]) for k in ('kind','location','sha256','metadata')})
    variants=[('batch',dict(changes=[addition])),('batch',dict(changes=[relink])),('open',dict(path=str(proof),discard=True)),('import_captions',dict(path=str(cue),track=graphics)),('import_media',dict(paths=[asset['location']['path']])),('source_open',dict(asset=asset)),('save',dict(path=str(out/'refused-save.zwv'))),('export_captions',dict(path=str(out/'refused.srt'))),('export',dict(path=str(out/'refused.mp4'))),('recover_copy',dict(snapshot=recovery['path'],snapshot_sha256=recovery['sha256'],path=str(out/'refused-recovery.zwv')))]
    refused=[];queued=[];original=deepcopy(s.document)
    with patch('project_audio_inspection.inspect_audio',side_effect=held):
        gate.clear();began.clear();futures=[query() for _ in range(4)];assert began.wait(3)
        for i in range(12):
            request=dict(op='save',operation_id=new_id(),**binding(),path=str(out/f'queued-{i}.zwv'),portable=False);r=s.request(request);assert r['ok'] and r['outcome']['status']=='saving';queued.append(request['operation_id'])
        assert len(s.jobs)==12 and len(s.inspections)==4
        command=s.command_revision;revision=s.revision;history=s.history_bytes
        with patch.object(s.pool,'submit',wraps=s.pool.submit) as submissions:
            for kind,values in variants:
                request=dict(op=kind,operation_id=new_id(),**binding(),**values);r=s.request(request)
                assert not r['ok'] and r['error']['code']=='busy',(kind,r)
                refused.append(dict(request=request,response=r));replay=s.request(request);assert not replay['ok'] and replay['outcome']==r['outcome']
                assert len(s.jobs)+len(s.inspections)==16 and s.command_revision==command and s.revision==revision and s.history_bytes==history and s.document==original
            assert submissions.call_count==0,submissions.call_count
            # Capacity is preparation admission, not a block on synchronous policy.
            op('batch',label='Synchronous edit at full preparation capacity',changes=[dict(op='project.rename',name='Accepted synchronous edit')]);assert s.document['name']=='Accepted synchronous edit' and submissions.call_count==0
            op('undo');assert s.document==original
        for job in s.jobs.values():job['cancel'].set()
        for job in s.inspections.values():job['cancel'].set()
        gate.set();wait(lambda:not s.jobs and not s.inspections)
        assert all(f.result()['error']['code']=='cancelled' for f in futures)
        assert all(s.outcomes[k]['status']=='failed' for k in queued)
    assert not list(out.glob('queued-*.zwv')) and not list(out.glob('refused*'))
    # Known rejection stays rejected on replay after capacity returns; an
    # explicitly new operation below the limit performs the intended preparation.
    r=s.request(refused[0]['request']);assert not r['ok'] and r['outcome']['error']['code']=='busy' and s.document==original
    op('batch',label='Deliberate source retry below capacity',changes=[addition]);assert any(a['id']==addition['id'] for a in s.document['media'])
    op('import_captions',path=str(cue),track=graphics);assert any(c['text']=='Pressure cue' for c in s.document['captions'])
    op('undo');op('undo');assert s.document==original
    (out/'MIXED-PRESSURE.json').write_text(json.dumps(dict(classification='Actual owner/pool with controlled worker holds, real4queries+12pinned saves',maximum_combined=16,rejected_paths=[r['request']['op'] for r in refused],worker_submissions_for_refusals=0,rejected_request_replay_retained=True,synchronous_edit_accepted=True,below_limit_media_and_caption_recovery=True,queued_destinations_not_created=True,refusals=refused),indent=2),encoding='utf8')
    checks.append('Actual4inspection+12pinnedSave mixed load rejects all10 extra async paths before pool submission; sync edit/Undo and known-rejection replay preserved, cancellation drains and deliberate media/caption retry succeeds below cap')
    # Cross-project requests cannot return an old document as the new one.
    with patch('project_audio_inspection.inspect_audio',side_effect=held):
        gate.clear();began.clear();f=query();assert began.wait(3);op('new',name='Independent empty project',settings=dict(width=1920,height=1080,fps=[30,1]),discard=True);finish();assert f.result()['error']['code']=='stale_revision' and not s.document['clips']
    op('open',path=str(proof),discard=True);assert s.document['clips']==snapshot['clips']
    checks.append('Project/epoch change while read work waits rejects stale completion; explicit reopen retains proof IDs/content')
    with patch('project_audio_inspection.inspect_audio',side_effect=held):
        gate.clear();began.clear();f=query();assert began.wait(3);assert not s.can_shutdown();assert any(j['cancel'].is_set() for j in s.inspections.values());gate.set();wait(lambda:s.can_shutdown());assert f.result()['error']['code']=='cancelled'
    s.shutdown();assert s.closed and not s.inspections and not s.jobs
    checks.append('Normal can_shutdown cancels and waits for read-only snapshots before pool retirement; no live/pending owner replacement or forced termination')
    import numpy as np
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,owner_admission_ms=admission,large_owner_admission_ms=large,transport_during_large_query_ms=commands_while_pending,summary_ms=dict(count=len(admission),median=float(np.median(admission)),p95=float(np.percentile(admission,95)),maximum=max(admission)),classification=__doc__),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
    gate.set()
    if not s.closed:
        for job in s.inspections.values():job['cancel'].set()
        wait(lambda:s.can_shutdown(True));s.shutdown()
