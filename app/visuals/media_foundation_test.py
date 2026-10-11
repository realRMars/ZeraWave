"""B3 real-codec plus controlled cancellation/resource/transport cases.

Synthetic delay/failure supplements original-clip motion. No audio output,
physical input, scanout, multi-hour stability or Robert acceptance claimed.
"""
from pathlib import Path
from copy import deepcopy
import sys,os,time,threading,json,uuid,traceback,hashlib
from unittest.mock import patch
import numpy as np
import media_frames as mf
from composition import defaults,new_layer

def fixture(out,gop=12,name='short-gop-original-disposable.mp4'):
    av=mf.backend();path=out/name
    with av.open(str(path),'w') as c:
        stream=c.add_stream('libx264',rate=24);stream.width=320;stream.height=180;stream.pix_fmt='yuv420p';stream.codec_context.gop_size=gop;stream.options={'crf':'18','sc_threshold':'0'}
        yy,xx=np.mgrid[:180,:320]
        for i in range(192):
            a=np.stack(((xx+i*9)%256,(yy+i*5)%256,np.full_like(xx,i*7%256)),axis=-1).astype('u1');f=av.VideoFrame.from_ndarray(a,format='rgb24')
            for p in stream.encode(f):c.mux(p)
        for p in stream.encode():c.mux(p)
    return path

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);path=fixture(out);meta=mf.inspect_animation(path,threading.Event());checks=[];report=dict(evidence=__doc__,fixture=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metadata=meta),checks=checks)
    def scene_for(paths=[path]):
        scene=defaults();assets={}
        for i,p in enumerate(paths):
            asset=dict(id=uuid.uuid4().hex,name=str(p.name),kind='Video',path=str(p),status='Ready',metadata=mf.inspect_animation(p,threading.Event()));assets[asset['id']]=asset;row=new_layer('Video',asset['id']);row['order']=i;row['media'].update(start=.5,end=4.5,loop='Loop');scene['layers'].append(row)
        return scene,assets
    def wait(fn,timeout=6):
        until=time.perf_counter()+timeout
        while time.perf_counter()<until:
            value=fn()
            if value:return value
            time.sleep(.003)
        raise AssertionError('Timed out waiting for '+repr(fn))
    def frame(owner,reader,identity):
        state=owner.snapshot()[identity];assert not state['error'],state
        return reader.read(state['frame']) if state['frame'] else None
    def quiescent(owner):
        assert owner.close(),owner.resources();r=owner.resources();assert r['decoded_planes_bytes']==r['shared_slots_bytes']==r['jobs']==r['pending']==0,r;assert not owner.sources;return r
    try:
        # Real long-GOP native planes, a slow iterator and 40 ms prefetch slices:
        # each slice must continue the owned lead-in instead of reseeking zero.
        long_path=fixture(out,96,'long-gop-prefetch-disposable.mp4');decoder=mf.DecoderWindow(long_path,mf.MAX_CACHE_BYTES);container=decoder.container
        decode_delay=[.015]
        class SlowContainer:
            def __getattr__(self,k):return getattr(container,k)
            def decode(self,*a,**k):
                for native in container.decode(*a,**k):time.sleep(decode_delay[0]);yield native
        decoder.container=SlowContainer()
        try:
            slices=[]
            for i in range(24):
                decoder._refill(1.8,threading.Event(),-1,.35,time.perf_counter()+.04);slices.append(dict(last=decoder.last,seeks=decoder.seek_count,frames=len(decoder.cache)))
                if decoder.ready(1.8) is not None:break
            assert decoder.ready(1.8) is not None and decoder.seek_count==1,slices
            report['prefetch_continuation']=dict(fixture=str(long_path),sha256=hashlib.sha256(long_path.read_bytes()).hexdigest(),raw=slices);checks.append('Real long-GOP lead-in continues over bounded 40 ms slices with one seek; no discarded deadline-crossing plane/PTS hole')
        finally:decoder.close()
        # A newer live display goal can retire obsolete forward lead-in without
        # destroying previously decoded native planes or weakening fixed seeks.
        decoder=mf.DecoderWindow(long_path,mf.MAX_CACHE_BYTES);container=decoder.container;decoder.container=SlowContainer();decode_delay[0]=.015
        try:
            decoder._refill(1.8,threading.Event(),interest=lambda:(1.8,1),work_budget=.04);old=next(iter(decoder.cache.values()));old_pixels=hashlib.sha256(old.to_ndarray(format='rgba').tobytes()).hexdigest();old_goal=decoder.refill_goal
            assert decoder.ready(1.8) is None and old_goal==1.8
            decoder._refill(5.,threading.Event(),interest=lambda:(5.,1),work_budget=.04)
            assert decoder.obsolete_refills==1 and decoder.refill_goal==5.
            for _ in range(60):
                if decoder.ready(5.) is not None:break
                decoder._refill(5.,threading.Event(),interest=lambda:(5.,1),work_budget=.04)
            assert decoder.ready(5.)==5. and decoder.obsolete_refills==1
            assert hashlib.sha256(old.to_ndarray(format='rgba').tobytes()).hexdigest()==old_pixels
            report['obsolete_goal']=dict(previous_goal=old_goal,new_goal=5.,retired=decoder.obsolete_refills,seeks=decoder.seek_count,retained_old_native_pixels=old_pixels)
            checks.append('Real codec retires only an obsolete forward presentation goal, reaches exact new PTS and preserves externally retained old native plane')
        finally:decoder.close();old=None
        decoder=mf.DecoderWindow(long_path,mf.MAX_CACHE_BYTES);container=decoder.container;decoder.container=SlowContainer();decode_delay[0]=.04
        try:
            try:
                for i in range(75):decoder._refill(2.8,threading.Event(),-1,.35,interest=lambda:(2.8,-1),work_budget=.04)
                raise AssertionError('Sliced lead-in escaped its cumulative work bound')
            except ValueError as exc:assert 'bounded window' in str(exc),exc
            report['prefetch_bound']=dict(frames=decoder.refill_frames,decode_seconds=decoder.refill_seconds);checks.append('Sliced native lead-in still enforces cumulative 512-frame/two-second work bound; slices do not reset the budget')
        finally:decoder.close()
        # Fairness at four visible sources; one native call is deliberately slow.
        scene,assets=scene_for([path]*4);owner=mf.MediaFrames();reader=mf.FrameReader();ids=[r['id'] for r in scene['layers']];slow_id=ids[0];original=mf.DecoderWindow.get;owners={};original_init=mf.DecoderWindow.__init__
        def init(d,p,b):original_init(d,p,b);owners[id(d)]=threading.get_ident()
        def delayed(d,*args,**kwargs):
            assert owners[id(d)]==threading.get_ident()
            lane=next((l for l in owner.lanes if l.decoder is d),None)
            if lane and lane.identity==slow_id:time.sleep(.35)
            return original(d,*args,**kwargs)
        try:
            with patch.object(mf.DecoderWindow,'__init__',init),patch.object(mf.DecoderWindow,'get',delayed):
                owner.sync(scene,assets)
                for i in ids:owner.command(i,'play')
                began=time.perf_counter();samples={i:[] for i in ids};last={}
                while time.perf_counter()-began<3.:
                    for i in ids:
                        f=frame(owner,reader,i)
                        if f:
                            now=time.perf_counter();samples[i].append(dict(wall=now-began,pts=f['pts'],interval_ms=(now-last.get(i,began))*1000));last[i]=now
                    r=owner.resources();assert r['jobs']<=4 and r['pending']<=4 and r['decoded_planes_bytes']<=mf.MAX_CACHE_BYTES and r['shared_slots_bytes']<=mf.MAX_STAGING_BYTES,r;time.sleep(.004)
                healthy={i:dict(count=len(v),max_warm_ms=max([x['interval_ms'] for x in v[1:]],default=9999)) for i,v in samples.items() if i!=slow_id}
                assert all(v['count']>30 and v['max_warm_ms']<250 for v in healthy.values()),healthy
                report['fairness']=dict(samples=samples,healthy=healthy,resources=owner.resources());checks.append('Four bounded source lanes, same-thread codec ownership, three healthy sources continue under one 350 ms slow source')
        finally:reader.close();quiescent(owner)
        # When the clock outruns a deliberately tiny decoded window, current-
        # time selection may present a closer cached floor as explicitly held.
        # It must never be reported as ready at the requested time.
        scene,assets=scene_for();identity=scene['layers'][0]['id'];scene['layers'][0]['media']['rate']=12.;owner=mf.MediaFrames();reader=mf.FrameReader();refill_original=mf.DecoderWindow._refill
        def slow_refill(decoder,*a,**k):time.sleep(.06);return refill_original(decoder,*a,**k)
        owner.cache_share=lambda state:meta['decoded_plane_bytes']*3
        try:
            with patch.object(mf.DecoderWindow,'_refill',slow_refill):
                owner.sync(scene,assets);owner.command(identity,'play');began=time.perf_counter();samples=[]
                while time.perf_counter()-began<2.:
                    state=owner.snapshot()[identity];assert not state['error'],state
                    f=reader.read(state['frame']) if state['frame'] else None
                    if f:
                        d=state['frame'];samples.append(dict(pts=f['pts'],requested=d['selection_requested_pts'],ready=d['ready_at_request'],held=state['held'],lag=state['lag_seconds']))
                        if not d['ready_at_request']:assert state['held'] and state['state']=='waiting'
                    time.sleep(.003)
                assert len(samples)>3 and any(not d['ready'] for d in samples),samples
                assert all(d['pts']<=d['requested']+1e-7 for d in samples if not d['ready']),samples
                report['held_window']=dict(raw=samples,resources=owner.resources());checks.append('A live 12x clock outruns a three-plane window: closer cached floor can progress only with explicit held/waiting state; request time is not slowed')
        finally:reader.close();quiescent(owner)
        # A real late exception from a blocked native-call wrapper must not
        # poison a newer seek generation. Cancellation flag actually reaches it.
        for outcome in ('error','success'):
            scene,assets=scene_for();identity=scene['layers'][0]['id'];owner=mf.MediaFrames();reader=mf.FrameReader();entered=threading.Event();release=threading.Event();seen=[];once=[True]
            def late(d,target,cancel,*a,**k):
                if once[0]:
                    once[0]=False;entered.set();assert release.wait(6);seen.append(cancel.is_set())
                    if outcome=='error':raise OSError('Late old-generation decoder failure')
                    return original(d,target,threading.Event(),*a,**k)
                return original(d,target,cancel,*a,**k)
            try:
                with patch.object(mf.DecoderWindow,'get',late):
                    owner.sync(scene,assets);assert entered.wait(4);old=owner.snapshot()[identity]['generation'];owner.command(identity,'seek',2.25);new=owner.snapshot()[identity]['generation'];assert old!=new;release.set();f=wait(lambda:frame(owner,reader,identity));assert seen==[True] and f['generation']==new and 2.20<=f['pts']<=2.25
                    assert owner.snapshot()[identity]['error']=='';checks.append('Late '+outcome+' cannot publish/stop a new generation; cooperative token signalled')
            finally:release.set();reader.close();quiescent(owner)
        # Reader owns a separate handle/bytes. A deliberately exported writer
        # view delays retirement; no forced close, lost allocation or BufferError
        # supersedes a primary source failure.
        scene,assets=scene_for();identity=scene['layers'][0]['id'];owner=mf.MediaFrames();reader=mf.FrameReader();view=None
        try:
            owner.sync(scene,assets);f=wait(lambda:frame(owner,reader,identity));desc=owner.snapshot()[identity]['frame'];kept=f['data'];lane=owner.sources[identity];view=lane.shm.buf[64:68];owner.begin_close();time.sleep(.15);assert not owner.is_closed();assert owner.resources()['shared_slots_bytes']>0
            assert kept==f['data'];view.release();view=None;wait(owner.is_closed);assert reader.read(desc) is None;reader.close();quiescent(owner);checks.append('Exported writer view retains retiring worker/mapping until actual release; reader snapshot remains immutable; retirement invalidates old header')
        finally:
            if view is not None:view.release()
            reader.close();quiescent(owner)
        scene,assets=scene_for();identity=scene['layers'][0]['id'];owner=mf.MediaFrames();entered=threading.Event();release=threading.Event()
        def blocked_decode(decoder,target,cancel,*a,**k):
            entered.set();assert release.wait(6)
            return original(decoder,target,threading.Event(),*a,**k)
        try:
            with patch.object(mf.DecoderWindow,'get',blocked_decode):
                owner.sync(scene,assets);assert entered.wait(4);owner.begin_close();time.sleep(.08)
                assert not owner.is_closed() and owner.resources()['jobs']==1 and owner.resources()['shared_slots_bytes']>0
                assert owner.sources[identity].active['cancel'].is_set()
                release.set();wait(owner.is_closed);assert not owner.results;quiescent(owner)
                checks.append('Close during an opaque-call wrapper retains worker/shared slots until actual return; cancellation is signalled and late success cannot publish')
        finally:release.set();quiescent(owner)
        # Exact stopped seeks, reverse order, rate phase, hide/show, replacement,
        # decoder error/Retry Play and an opaque call at shutdown.
        scene,assets=scene_for();identity=scene['layers'][0]['id'];owner=mf.MediaFrames();reader=mf.FrameReader()
        try:
            owner.sync(scene,assets)
            sequences=[]
            for target in [1.+i*.0416666667 for i in range(12)]+[1.+i*.0416666667 for i in reversed(range(12))]:
                owner.command(identity,'seek',target);f=wait(lambda:frame(owner,reader,identity));assert target-f['pts']>=-1e-7 and target-f['pts']<.043,(target,f['pts']);sequences.append((target,f['pts']))
            owner.command(identity,'play');time.sleep(.08);before=owner.snapshot()[identity]['position'];scene['layers'][0]['media']['rate']=6.;owner.sync(scene,assets);after=owner.snapshot()[identity]['position'];assert abs(after-before)<.06
            owner.command(identity,'pause');paused=owner.snapshot()[identity]['position'];time.sleep(.08);assert owner.snapshot()[identity]['position']==paused
            owner.command(identity,'stop');f=wait(lambda:frame(owner,reader,identity));assert f['pts']==.5 and owner.snapshot()[identity]['state']=='stopped';wait(lambda:owner.resources()['decoded_planes_bytes']==0)
            scene['layers'][0]['enabled']=False;owner.sync(scene,assets);wait(lambda:not owner.sources);assert owner.snapshot()[identity]['state']=='cancelled' and owner.snapshot()[identity]['frame'] is None
            scene['layers'][0]['enabled']=True;owner.sync(scene,assets);f=wait(lambda:frame(owner,reader,identity));new=deepcopy(next(iter(assets.values())));new['id']=uuid.uuid4().hex;assets[new['id']]=new;scene['layers'][0]['asset']=new['id'];owner.sync(scene,assets);assert owner.snapshot()[identity]['frame'] is None;wait(lambda:frame(owner,reader,identity))
            owner.reset();owner.sync(scene,assets);assert owner.snapshot()[identity]['frame'] is None;wait(lambda:frame(owner,reader,identity));checks.append('Timestamp floor forward/reverse seeks; phase-preserving rate, pause, stop/cache release, hide/show, replacement and reset/reopen')
            old=owner.snapshot()[identity]['frame'];owner.command(identity,'play')
            close_original=mf.DecoderWindow.close;failed_close=[True]
            def cleanup_failure(decoder):
                if failed_close[0]:failed_close[0]=False;raise BufferError('Controlled native cleanup failure')
                return close_original(decoder)
            with patch.object(mf.DecoderWindow,'get',side_effect=OSError('Actual test decoder failure')),patch.object(mf.DecoderWindow,'close',cleanup_failure):
                wait(lambda:owner.snapshot()[identity]['state']=='failed');wait(lambda:bool(owner.resources()['cleanup_errors']))
                assert owner.snapshot()[identity]['error']=='Actual test decoder failure'
                assert owner.sources[identity].decoder is not None
            assert owner.snapshot()[identity]['frame']==old or owner.snapshot()[identity]['frame']['generation']==old['generation'];owner.command(identity,'play');wait(lambda:owner.snapshot()[identity]['error']=='');wait(lambda:frame(owner,reader,identity));checks.append('Valid-source last-good retained with truthful primary failure; cleanup failure retains native owner separately; Play cleans up and retries the source')
        finally:reader.close();quiescent(owner)
        checks.append('All source resources quiescent after legitimate reader/worker retirement; no unrelated artwork/history ownership cleared')
        report['result']='PASS'
    except Exception:
        report['result']='FAIL';report['failure']=traceback.format_exc();raise
    finally:(out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS',out,checks,flush=True)

if __name__=='__main__':run()
