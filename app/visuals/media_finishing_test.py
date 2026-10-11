"""Real CFR/VFR navigation and guarded live-seek regressions; silent, scripted."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,time,threading,uuid,json,traceback
import media_frames as mf
from media_foundation_test import fixture
from media_frames_test import fixtures
from composition import defaults,new_layer,validate_scene

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    cfr=fixture(out);fixtures(out);vfr=out/'alpha-disposal-vfr.gif'
    checks=[];report=dict(evidence=__doc__,checks=checks,raw=[])
    def wait(fn):
        until=time.perf_counter()+8
        while time.perf_counter()<until:
            result=fn()
            if result:return result
            time.sleep(.002)
        raise AssertionError('Timed out')
    def setup(path,kind='Video'):
        asset=dict(id=uuid.uuid4().hex,path=str(path),name=path.name,kind=kind,status='Ready',metadata=mf.inspect_animation(path,threading.Event()))
        scene=defaults();row=new_layer(kind,asset['id']);scene['layers']=[row];scene['assets']=[asset]
        return scene,row,{asset['id']:asset}
    try:
        for path,kind,expected in ((cfr,'Video',[i/24 for i in range(8)]),(vfr,'GIF',[0.,.08,.21,.43])):
            scene,row,assets=setup(path,kind);owner=mf.MediaFrames();reader=mf.FrameReader();identity=row['id']
            def ready():
                state=owner.snapshot()[identity];assert not state['error'],state
                return reader.read(state['frame']) if state['frame'] and not state['seek_pending'] else None
            try:
                owner.sync(scene,assets);wait(ready);observed=[0.]
                for pts in expected[1:]:
                    owner.command(identity,'step',1);frame=wait(ready);assert abs(frame['pts']-pts)<1e-6,(frame,pts);observed.append(frame['pts']);assert not owner.snapshot()[identity]['playing']
                for pts in reversed(expected[:-1]):
                    owner.command(identity,'step',-1);frame=wait(ready);assert abs(frame['pts']-pts)<1e-6,(frame,pts);observed.append(frame['pts'])
                owner.command(identity,'step',-1);assert wait(ready)['pts']==0.
                report['raw'].append(dict(path=str(path),adjacent_pts=observed));checks.append(kind+' actual adjacent timestamps forward/backward, lower bound, paused until Play')
                if kind=='Video':
                    # A complete delayed real decode supplies old pixels, but cancellation forbids promotion.
                    entered=threading.Event();release=threading.Event();original=mf.DecoderWindow.get;once=[True]
                    def delayed(d,target,cancel,*a,**k):
                        if once[0]:once[0]=False;entered.set();assert release.wait(8)
                        return original(d,target,cancel,*a,**k)
                    with patch.object(mf.DecoderWindow,'get',delayed):
                        owner.command(identity,'scrub',dict(position=2.,final=False));assert entered.wait(6)
                        for target in (3.,1.1,4.2,.3,2.25):owner.command(identity,'scrub',dict(position=target,final=False))
                        owner.command(identity,'scrub',dict(position=1.75,final=True,resume=False));generation=owner.snapshot()[identity]['generation'];release.set();frame=wait(ready)
                        assert frame['generation']==generation and frame['pts']==1.75 and not owner.snapshot()[identity]['playing']
                    checks.append('Rapid reversed live seeks: obsolete decode cancelled; final published floor matches latest request; paused stays paused')
                    owner.command(identity,'play');owner.command(identity,'scrub',dict(position=2.5,final=True,resume=True));frame=wait(ready);assert owner.snapshot()[identity]['playing']
                    owner.command(identity,'scrub',dict(position=3.,final=True,resume=True));owner.command(identity,'pause');wait(ready);assert not owner.snapshot()[identity]['playing']
                    owner.command(identity,'scrub',dict(position=4.,final=True,resume=True));owner.command(identity,'cancel_resume');wait(ready);assert not owner.snapshot()[identity]['playing']
                    owner.command(identity,'scrub',dict(position=4.,final=True,resume=True));owner.command(identity,'stop');frame=wait(ready);assert frame['pts']==0 and owner.snapshot()[identity]['state']=='stopped'
                    checks.append('Resume only after final publication; explicit Pause/Stop and selection cancellation override resume')
                    owner.command(identity,'seek',2.);wait(ready);row['media']['direction']=-1;owner.sync(scene,assets);wait(ready);before=owner.snapshot()[identity]['position'];owner.command(identity,'play');time.sleep(.12);after=owner.snapshot()[identity]['position'];assert after<before-.06
                    row['media']['rate']=12.;owner.sync(scene,assets);assert owner.snapshot()[identity]['direction']==-1;owner.command(identity,'pause');owner.command(identity,'step',dict(count=3));wait(ready);assert not owner.snapshot()[identity]['playing']
                    owner.command(identity,'stop');wait(ready);assert owner.snapshot()[identity]['state']=='stopped'
                    checks.append('Deliberate reverse preserves position, progresses backwards at positive magnitude, retains 12x and frame steps/Stop pause')
                    frozen=deepcopy(owner.layers)
                    for op,value,source in [('seek',float('nan'),None),('step',65,None),('play',None,['obsolete'])]:
                        try:owner.command(identity,op,value,source);raise AssertionError('Invalid command accepted')
                        except ValueError:pass
                        assert owner.layers==frozen
                    checks.append('Invalid step/seek/source guard has no clock, generation or pending mutation')
            finally:
                reader.close();assert owner.close();r=owner.resources();assert r['jobs']==r['pending']==r['decoded_planes_bytes']==r['shared_slots_bytes']==0,r
        # Clock endpoints are exact independent of average source rate.
        for direction in (1,-1):
            assert mf.timeline(1,2,4,1,'None',direction)==(3,False)
            assert mf.timeline(2,2,4,1,'None',direction)==((4 if direction>0 else 2),True)
            assert mf.timeline(2.5,2,4,1,'Loop',direction)[0]==(2.5 if direction>0 else 3.5)
            assert mf.timeline(2.5,2,4,1,'Ping-pong',direction)[0]==(3.5 if direction>0 else 2.5)
        scene,row,assets=setup(cfr);del row['media']['direction'];assert validate_scene(scene)['layers'][0]['media']['direction']==1
        checks.append('Both-direction None/Loop/Ping-pong boundaries and old-session Forward default; resources quiescent')
        report['result']='PASS'
    except Exception:
        report['result']='FAIL';report['failure']=traceback.format_exc();raise
    finally:(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS',out,checks,flush=True)

if __name__=='__main__':run()
