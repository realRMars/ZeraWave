"""Bounded real owner/helper audio-target refusal and video extraction control.

Uses the existing12s proof/manifest and task-owned sources. No native text-fit,
GPU, GUI, audio output or export. Native fit must never run on a wrong target.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,traceback,uuid
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);manifest_path=Path(sys.argv[3])
os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test')
from studio_control_client import ControlClient
from project_manifest import read_state,binding,stamp,compile_plan
from project_cli import request
from project_components import validate_components
from project_evaluator import Evaluator
from video_project import validate,new_id
client=None;checks=[];ref=lambda value:dict(ref=value)

def state():return read_state(endpoint)
def op(kind,**args):
    reply=request(endpoint,dict(op=kind,operation_id=new_id(),**binding(state()),**args));assert reply['ok'],reply;return reply
def audio_params(part):
    return dict(asset=ref('media:moving-b'),track=ref('tracks:background'),start=0 if part=='voice' else 240,duration=120,source_in=[8,1],source_out=[12,1],rate=[1,1],audio=dict(gain=.25,mute=False,fade_in=0,fade_out=9,envelope=[]),pad_end='none')
def marker():
    value=state();return dict(stamp=stamp(value),history_bytes=value['history_bytes'],undo_label=value['undo_label'],redo_label=value['redo_label'],saved_revision=value['saved_revision'])

try:
    client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);op('open',path=str(proof));d=state()['document']
    voice=next(c for c in d['clips'] if c['duration']==233);tail=next(c for c in d['clips'] if c['start']==240)
    op('batch',label='Disposable target-validation foundation',changes=[dict(op='clip.remove',id=voice['id'],linked=False),dict(op='clip.remove',id=tail['id'],linked=False),dict(op='graphic.remove',id=d['graphics'][0]['id'])])
    manifest=json.loads(manifest_path.read_text(encoding='utf8'));manifest['id']=new_id();manifest['save']['path']=str(out/'not-applied.zwv');before=marker();failures=[]
    for part in ('voice','music'):
        bad=deepcopy(manifest);outro=next(r for s in bad['sections'] for r in s.get('recipes',[]) if r['kind']=='outro');outro['params'][part]=audio_params(part)
        with patch('project_text_fit.native_preflight',side_effect=AssertionError('Wrong-target planning reached native fit')) as native:
            try:compile_plan(endpoint,bad);raise AssertionError('Wrong target planned')
            except ValueError as exc:assert 'must target an audio track' in str(exc),(part,str(exc));failures.append(dict(part=part,error=str(exc)))
            assert native.call_count==0
        assert marker()==before and not (out/'not-applied.zwv').exists()
    checks.append('Real helper rejects both Video-on-video voice/music targets before native fit, before ANY owner submission/history/saved-state change; exact state and failure messages retained')
    # A valid Video source on an AUDIO track remains a deliberate extraction.
    valid=deepcopy(manifest);outro=next(r for s in valid['sections'] for r in s.get('recipes',[]) if r['kind']=='outro')
    for part,track in [('voice',voice['track']),('music',tail['track'])]:outro['params'][part]=dict(audio_params(part),track=track)
    snapshots=[]
    def capture(document,ids,*args,**kwargs):snapshots.append(deepcopy(document));return dict(status='NOT_EXECUTED_MODEL_CONTROL',selected_ids=ids)
    with patch('project_text_fit.native_preflight',side_effect=capture) as native:plan=compile_plan(endpoint,valid);assert native.call_count==1
    candidate=snapshots[0];rows=[c for c in candidate['clips'] if c['provenance'].get('component',{}).get('role')=='audio'];assert len(rows)==2
    assets={a['id']:a for a in candidate['media']};tracks={t['id']:t for t in candidate['tracks']}
    assert all(assets[r['asset']]['kind']=='Video' and assets[r['asset']]['metadata']['has_audio'] and tracks[r['track']]['kind']=='audio' for r in rows)
    e=Evaluator(candidate,'model-control',0)
    from project_mixer import Mixer
    import numpy as np
    decoded=[]
    for row in rows:
        block=e.audio_span(row['start']*1600,1600);assert row['id'] in {r['clip']['id'] for r in block['audio']};mixer=Mixer();readers=[]
        try:
            pcm=mixer.render(block);readers=list(mixer.readers.values());assert pcm.shape==(1600,2) and np.isfinite(pcm).all()
            video_readers=[reader for reader in readers if getattr(reader,'asset',{}).get('kind')=='Video'];assert video_readers and all(reader.decoded>0 and reader.backend.startswith('PyAV') for reader in video_readers)
            decoded.append(dict(part=row['provenance']['component']['part'],native_decoded_samples=[reader.decoded for reader in video_readers],peak=float(np.max(np.abs(pcm))),metrics=deepcopy(mixer.metrics)))
        finally:mixer.close();assert mixer.budget.used==0 and all(reader.closed for reader in readers)
    # Intentional authored mute/None is policy, not an invalid target.
    for row in rows:
        row['audio']['mute']=True;tracks[row['track']]['output']=None
    candidate=validate(candidate);instances={r['provenance']['component']['instance_id'] for r in rows};validate_components(candidate,instances)
    assert marker()==before and not (out/'not-applied.zwv').exists()
    checks.append('Valid audio-bearing Video extraction on AUDIO tracks reaches canonical evaluator and actual PyAV/Mixer decode for both roles; bounded PCM/native reader cleanup, explicit mute/None routing preserved; native fit mocked/NOT claimed or plan applied')
    (out/'FAILURES.json').write_text(json.dumps(failures,indent=2),encoding='utf8');op('close',discard=True);client.close();assert client.process.returncode==0;client=None
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,decoded_audio=decoded,classification=__doc__,owner_exit=0,native_fit_executed=False,plan_applied=False),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
    if client and not client.closed:client.close(mode='discard',project_mode='discard')
