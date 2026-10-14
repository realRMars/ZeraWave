"""Standalone migration correctness: immutable pixels, geometry, real owner reply recovery."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import sys,os,time,json,hashlib,importlib.util,threading,traceback,gc
ROOT=Path(os.environ.get('ZERAWAVE_TEST_ROOT',str(Path(__file__).resolve().parents[2])));sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import numpy as np,av
from PySide6.QtGui import QImage
from native_raster import backend
from raster_tiles import export,image as tiled_image
from media_frames import DecoderWindow
from media_transfer import backend as media_backend
from native_surfaces import backend as surface_backend
import scene_surfaces
def run(folder,baseline):
    out=Path(folder);out.mkdir(parents=True,exist_ok=False);checks=[];details={};result='FAIL';failure=None;owner=None
    try:
        rng=np.random.default_rng(4331)
        if backend().available:
            for w,h in [(1,1),(127,129),(385,261),(1280,720)]:
                data=rng.integers(0,256,(h,w,4),dtype='u1');data[:,:,:3]=np.minimum(data[:,:,:3],data[:,:,3,None]);source=QImage(data.tobytes(),w,h,QImage.Format_ARGB32_Premultiplied).copy();native=backend().storage().from_image(source);desc,lease=export(native)
                try:
                    prepared=tiled_image(desc,native=False,lease=lease);assert bytes(prepared.constBits())==bytes(source.constBits())
                    from native_raster import native_materialize
                    if backend().status()['materialize_kernel']:
                        bad=deepcopy(desc);bad['tiles'][-1]['width']+=1
                        try:native_materialize(bad,lease);raise AssertionError('Invalid native table admitted')
                        except ValueError:pass
                    lease.close();assert not lease.leases
                    details[f'tiles-{w}x{h}']=hashlib.sha256(bytes(prepared.constBits())).hexdigest()
                finally:lease.close()
                del native;gc.collect()
            checks.append('Exact tile orientation/channel/alpha conversion, odd edges, invalid table and exported-pointer cleanup')
        else:checks.append('B1 tile-native extension unavailable as expected; existing raster fallback workflow is tested separately')
        for rotation in (0,90,180,270):
            data=rng.integers(0,256,(33,47,4),dtype='u1');frame=av.VideoFrame.from_ndarray(data,format='rgba');plane=frame.to_ndarray(format='rgba').copy()
            expected=data.copy();expected[:,:,:3]=((expected[:,:,:3].astype('u2')*expected[:,:,3,None].astype('u2')+127)//255).astype('u1')
            expected=np.rot90(expected,-rotation//90)[::-1].tobytes()
            decoder=SimpleNamespace(stream=SimpleNamespace(metadata={'rotate':str(rotation)}),_metrics=lambda:None)
            for _ in range(12):
                w,h,pixels=DecoderWindow.rgba(decoder,frame);assert pixels==expected;assert np.array_equal(frame.to_ndarray(format='rgba'),plane)
            details[f'alpha-{rotation}']=dict(size=[w,h],sha256=hashlib.sha256(pixels).hexdigest())
            direct=media_backend().publication(data,rotation,False)
            if media_backend().snapshot()['publication_kernel']:
                assert direct is not None and direct[2]==expected
                assert np.array_equal(data,plane)
        checks.append('Repeated cached PyAV plane conversion is immutable; alpha and four rotations retain exact intended bytes')
        spec=importlib.util.spec_from_file_location('surface_reference',Path(baseline)/'app/visuals/scene_surfaces.py');reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
        parity=[]
        for z in [*range(-24,25),47,120,407,1000,5000]:
            a=reference.cavern_row(z);b=scene_surfaces.cavern_row(z);assert a.shape==b.shape and a.tobytes()==b.tobytes(),(z,a.shape,b.shape,float(np.max(np.abs(a-b))) if a.shape==b.shape else None)
            parity.append(dict(row=z,vertices=len(a),sha256=hashlib.sha256(b.tobytes()).hexdigest()))
        details['surface_rows']=parity;checks.append('54 complete required Cavern rows retain every vertex, normal, motion, tag and triangle byte')
        # Actual owner process/pipe: corrupt a post-admission ACK and reconcile
        # exactly the same operation, with no duplicate transaction/history.
        from studio_control_client import ControlClient
        corrupt=out/'corrupt-reply.flag';os.environ.update(ZERAWAVE_CONTROL_TEST_CORRUPT_REPLY=str(corrupt),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'))
        host=dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0',ZERAWAVE_WORKSPACE_QT_FOREIGN='1',ZERAWAVE_OWNER_TELEMETRY='1')
        owner=ControlClient(host,out/'owner.log');deadline=time.perf_counter()+20
        while owner.snapshot['media_library']['loading'] and time.perf_counter()<deadline:time.sleep(.005)
        from composition import defaults,new_layer
        scene=defaults();scene['canvas']=[64,48];scene['layers']=[new_layer('Group')];label='Recover one corrupted composition reply';corrupt.write_text('once')
        future=owner.submit('composition',version=4,editor={},canvas=[64,48],presentation=scene['presentation'],layers=scene['layers'],label=label,selection=scene['layers'][0]['id'],before_selection=None,history_scope='layers',history_target=None)
        future.result(timeout=20)
        end=time.perf_counter()+10
        while not owner.sections.valid and time.perf_counter()<end:time.sleep(.005)
        snapshot=deepcopy(owner.snapshot);assert owner.sections.valid and not owner.disconnected
        assert len(snapshot['values']['media']['layers'])==1 and snapshot['media_control']['revision']==1,snapshot['media_control']
        history=snapshot['media_control']['history'];assert history['commands']==1,history
        assert owner.protocol_error_count>=1 and not corrupt.exists()
        details['recovery']=dict(operation=future.operation_id,protocol_errors=owner.protocol_error_count,history=history,snapshot=snapshot)
        owner.submit('composition_history',redo=False,history_scope='layers').result(timeout=10);assert not owner.snapshot['values']['media']['layers']
        owner.submit('composition_history',redo=True,history_scope='layers').result(timeout=10);assert len(owner.snapshot['values']['media']['layers'])==1
        checks.append('Real corrupt owner pipe reply retains state/resync, one accepted composition, exact Undo/Redo, same running owner')
        owner.close(mode='discard');details['owner_exit']=owner.process.poll();assert details['owner_exit']==0
        checks.append('Normal isolated owner exit confirmed; no forced cleanup counted as success')
        result='PASS'
    except BaseException:failure=traceback.format_exc();print(failure)
    finally:
        if owner and not owner.closed:
            try:owner.close(mode='discard')
            except Exception as exc:details['cleanup_error']=str(exc)
        report=dict(result=result,checks=checks,details=details,failure=failure,raster=backend().status(),media=media_backend().snapshot(),surface=surface_backend().snapshot(),evidence='Native kernels/reference bytes and actual isolated owner pipe; no GPU/listening/physical UI acceptance')
        (out/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(result,len(checks))
    assert result=='PASS'
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
