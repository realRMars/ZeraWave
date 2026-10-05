"""Launch identity completeness, owned applied revisions and bounded report trace."""
import json,os,sys,tempfile,time
from pathlib import Path
from collections import deque
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
from session_performance import SessionPerformance
from audio_scope import Scope

def run():
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as tmp:
        obj=SessionPerformance.__new__(SessionPerformance);obj.folder=Path(tmp);obj.renderer=SimpleNamespace(director_seed=7301)
        base=dict(state='canvas',selection=['cosmic','canvas'],selection_scope='main',source='Synthetic preview',speed='Real time',planet_palette='authored',material_isolation={},galaxy_seed='7301',galaxy_visit='0',galaxy_entry='Full journey',planet_dsp_pilot=False,planet_star_attack_pilot=False)
        def identity(v):
            (obj.folder/'preview.json').write_text(json.dumps(v),encoding='utf8');return obj.source_identity()
        original=identity(base)
        for key,value in (('planet_palette','soft-dream'),('material_isolation',{'cosmic':'echo_weave'}),('galaxy_seed','33'),('galaxy_visit','2'),('galaxy_entry','Short return'),('planet_dsp_pilot',True),('planet_star_attack_pilot',True)):
            assert identity(dict(base,**{key:value}))['launch_settings_sha256']!=original['launch_settings_sha256'],key
        assert original['settings_identity_kind'].startswith('launch-only') and 'track' not in original['launch_settings']
        obj.identity=original;obj.run='preview-owned';obj.started=time.perf_counter();obj.applied_edits=deque(maxlen=256);obj.applied_edits_total=0;obj.applied_revisions={};obj.edit_chain=original['launch_settings_sha256'];obj.renderer.studio_audio=SimpleNamespace(run='audio-owned',session='session-owned')
        scope=Scope('audio-owned','session-owned',41,'fractal.41.landscape',1).packet()
        assert obj.record_applied_edit('audio',scope,{'gain':.5},1.)
        chain=obj.edit_chain
        assert not obj.record_applied_edit('audio',scope,{'gain':2.},2.)
        assert not obj.record_applied_edit('audio',dict(scope,run='foreign',revision=9),{'gain':2.},2.)
        assert obj.edit_chain==chain and obj.applied_edits_total==1
        for revision in range(300):
            assert obj.record_applied_edit('colors',dict(run='preview-owned',session='session-owned',form=41,target='colors',revision=revision),{'color':'#55BB88'},revision/5.)
        assert len(obj.applied_edits)==256 and obj.applied_edits_total==301 and len(obj.applied_revisions)==2
        assert obj.edit_chain!=original['launch_settings_sha256']
        return dict(evidence='CPU actual launch-identity serializer and applied-event recorder; public GPU ACK/rejection coverage is separate',consequential_launch_fields=7,launch_only_label=True,wrong_owner_and_stale_ignored=True,trace_cap=256,events=301)
if __name__=='__main__':print(json.dumps(run(),indent=2));print('Session performance identity checks PASS')
