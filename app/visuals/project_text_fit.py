"""Bounded native batch text preflight, using the existing TextSurface path.

One disposable offscreen Qt process owns fonts/images. No decoder, renderer,
device, document mutation or retained template runtime is introduced.
"""
from pathlib import Path
from fractions import Fraction
from copy import deepcopy
import hashlib,json,os,sys,time,tempfile,subprocess,threading,traceback

MAX_STATES=4096
MAX_PIXEL_WORK=256*1024*1024
MAX_REPLY=1024*1024

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def source_bindings():
    return {name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('project_text.py','project_text_fit.py','project_visual.py')}
def frames(row,fps):
    """All distinct relevant timer states, not an unproven widest-digit proxy."""
    start=row['start'];end=start+row['duration'];style=row['style'];text=row['text']
    size_keys=any(k['parameter'] in ('bounds.2','bounds.3') for k in style.get('keys',[]))
    if size_keys or row['dynamic']=='counter' and '{frame}' in text:
        yield from range(start,end);return
    yield start
    if row['dynamic']=='counter' and '{elapsed}' in text:
        origin=row.get('range_start',start);first=max(0,int(Fraction(start-origin)/fps));last=max(0,int(Fraction(end-1-origin)/fps))
        for second in range(first,last+1):
            value=Fraction(origin)+second*fps;frame=-(-value.numerator//value.denominator)
            if start<frame<end:yield frame
    if end-1!=start:yield end-1

def native_preflight(document,ids,binding=None,cancel=None,timeout=30.):
    """Read-only parent helper. Results always retain their original binding."""
    from video_project import validate,identity
    d=validate(document,allow_missing_routes=True);ids=list(ids)
    if len(ids)>4608 or len(set(ids))!=len(ids):raise ValueError('Preflight selects distinct ordinary text IDs within document capacities.')
    known={r['id'] for c in ('graphics','captions') for r in d[c]}
    if any(identity(i) not in known for i in ids):raise ValueError('A selected preflight text no longer exists.')
    config=dict(format='zerawave-native-text-fit',version=1,document=d,document_sha256=digest(d),ids=ids,binding=deepcopy(binding or {}),limits=dict(native_states=MAX_STATES,pixel_work_bytes=MAX_PIXEL_WORK,reply_bytes=MAX_REPLY))
    cancel=cancel or threading.Event();began=time.perf_counter()
    base=dict(format=config['format'],version=1,document_sha256=config['document_sha256'],binding=config['binding'],selected_ids=ids,read_only=True)
    if cancel.is_set():return dict(base,status='CANCELLED',checks=[],failures=[],unrun=ids,reason='Cancelled before native preparation; no edit.')
    temporary_root=Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix='zerawave-text-fit-',dir=temporary_root) as scratch:
        folder=Path(scratch).resolve();assert folder.is_relative_to(temporary_root) and folder.name.startswith('zerawave-text-fit-')
        raw=json.dumps(config,ensure_ascii=False,allow_nan=False).encode()
        if len(raw)>1024*1024:raise ValueError('Native preflight input exceeds1MiB; narrow selection. No edit.')
        (folder/'INPUT.json').write_bytes(raw);env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
        with (folder/'native.log').open('wb') as log:
            process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',str(folder)],stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            cancelled_at=None;timed_out=False
            while process.poll() is None:
                now=time.perf_counter()
                if cancel.is_set() or now-began>timeout:
                    timed_out=now-began>timeout
                    (folder/'CANCEL').touch(exist_ok=True)
                    if cancelled_at is None:cancelled_at=now
                    if now-cancelled_at>3.:
                        process.kill();process.wait();break # only this owned failed helper
                time.sleep(.01)
        result_path=folder/'RESULT.json';log_size=(folder/'native.log').stat().st_size
        with (folder/'native.log').open('rb') as stream:stream.seek(max(0,log_size-16384));log=stream.read(16384)
        if result_path.exists() and result_path.stat().st_size<=MAX_REPLY:
            result=json.loads(result_path.read_text(encoding='utf8'))
            if result.get('document_sha256')!=base['document_sha256'] or result.get('binding')!=base['binding']:raise ValueError('Native preflight returned a different snapshot binding.')
        else:result=dict(base,status='CANCELLED' if cancel.is_set() else 'FAILED',checks=[],failures=[],unrun=ids,reason='Native worker did not publish a bounded complete report.')
        result.update(worker_exit=process.returncode,elapsed_ms=(time.perf_counter()-began)*1000,timed_out=timed_out,native_log=log.decode('utf8',errors='replace'),native_log_omitted_bytes=max(0,log_size-16384))
        if process.returncode not in (0,2) and result.get('status')=='PASS':result.update(status='FAILED',reason='Worker cleanup/exit failed after fit; no PASS.')
        if timed_out:result.update(status='INCOMPLETE',reason='Bounded native preparation timed out; no fit acceptance or edit.')
        if cancel.is_set():result.update(status='CANCELLED',reason='Cancelled intent cannot publish fit acceptance, including a late worker completion.')
        return result

def worker(folder):
    from video_project import validate
    os.environ['QT_QPA_PLATFORM']='offscreen'
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import qVersion
    from project_visual import evaluated_text
    import project_text
    folder=Path(folder).resolve();raw=(folder/'INPUT.json').read_bytes()
    if len(raw)>1024*1024:raise ValueError('Oversized native preflight input')
    config=json.loads(raw);d=validate(config['document'],allow_missing_routes=True)
    if digest(d)!=config['document_sha256']:raise ValueError('Native snapshot changed')
    app=QApplication.instance() or QApplication([]);surface=project_text.TextSurface();fps=Fraction(*d['settings']['fps'])
    chosen=set(config['ids']);rows=[r for c in ('graphics','captions') for r in d[c] if r['id'] in chosen]
    result=dict(format=config['format'],version=1,status='PASS',document_sha256=config['document_sha256'],binding=config['binding'],selected_ids=config['ids'],read_only=True,checks=[],failures=[],unrun=[],conditions=dict(native_dimensions=[d['settings']['width'],d['settings']['height']],fps=d['settings']['fps'],qpa=app.platformName(),qt_version=qVersion(),source_hashes=source_bindings(),state_policy='Exhaustive relevant counter changes/frame tokens/native size states within declared bounds; no sampled extrema claim',limits=config['limits']),resources=dict(native_states=0,pixel_work_bytes=0,native_image_bytes_peak=0,retained_pixel_cache_bytes=0))
    cache={};attempted=0;pixel_work=0;peak=0;cancelled=False
    try:
        for index,row in enumerate(rows):
            component=row['provenance'].get('component',{});identity=dict(id=row['id'],component_id=component.get('instance_id'),part=component.get('part'),text=row['text'])
            row_check=dict(identity,status='PASS',states=[],representative_frames=[],unique_native_states=0,descriptor_reuse=0)
            count=0
            for frame in frames(row,fps):
                if (folder/'CANCEL').exists():cancelled=True;result['status']='CANCELLED';result['unrun']=[r['id'] for r in rows[index:]];break
                count+=1
                if count>MAX_STATES:
                    result['status']='INCOMPLETE';row_check.update(status='INCOMPLETE',reason='Relevant dynamic state count exceeds4096; narrow the inspected range/recipe. No complete-fit claim.');result['unrun'].append(row['id']);break
                recipe=evaluated_text(row,frame);plan=dict(settings=d['settings'],frame=frame,text=[dict(recipe=recipe,track=dict(id=row['track']))])
                descriptor=None;started=time.perf_counter_ns()
                try:
                    descriptor=surface.descriptors(plan)[0];key=descriptor['key']
                    if descriptor['progress'] is not None:
                        key=digest([descriptor['size'],{k:v for k,v in descriptor['style'].items() if k not in ('bounds','rotation','opacity','keys')},'bounded progress geometry'])
                    if key in cache:
                        row_check['descriptor_reuse']+=1
                        if not row_check['states']:row_check['states'].append(dict(frame=frame,rendered_text=descriptor['text'],native_size=list(descriptor['size']),font_requested=descriptor['style']['font'],font_pixels=descriptor['style']['size'],metrics=deepcopy(cache[key]),descriptor_reused=True))
                        continue
                    cost=descriptor['bytes']
                    if attempted>=MAX_STATES or pixel_work+cost>MAX_PIXEL_WORK:
                        result['status']='INCOMPLETE';row_check.update(status='INCOMPLETE',reason='Native state/pixel-work budget exhausted; no complete-fit claim.');result['unrun'].append(row['id']);break
                    attempted+=1;pixel_work+=cost;peak=max(peak,cost)
                    rendered=surface.pixels(descriptor,measure_only=True);metrics=rendered['text_details'];cache[key]=metrics
                    if len(cache)>128:cache.pop(next(iter(cache)))
                    row_check['unique_native_states']+=1;row_check['representative_frames'].append(frame)
                    row_check['states'].append(dict(frame=frame,rendered_text=descriptor['text'],native_size=list(descriptor['size']),font_requested=descriptor['style']['font'],font_pixels=descriptor['style']['size'],padding=[descriptor['style'].get('padding_x',descriptor['style']['padding']),descriptor['style'].get('padding_y',descriptor['style']['padding'])],metrics=metrics,ms=(time.perf_counter_ns()-started)/1e6))
                except Exception as exc:
                    failure=dict(identity,frame=frame,code=getattr(exc,'code','native_text_error'),reason=str(exc),details=deepcopy(getattr(exc,'details',{})),style=deepcopy(recipe['style']),native_size=list(descriptor['size']) if descriptor else [max(1,round(recipe['style']['bounds'][2]*d['settings']['width'])),max(1,round(recipe['style']['bounds'][3]*d['settings']['height']))],ms=(time.perf_counter_ns()-started)/1e6)
                    result['failures'].append(failure);row_check.update(status='FAIL',failure=failure['code']);break
            result['checks'].append(row_check)
            if cancelled:break
        if result['failures'] and not cancelled:result['status']='FAIL'
    finally:
        surface.close();cache.clear();result['resources'].update(native_states=attempted,pixel_work_bytes=pixel_work,native_image_bytes_peak=peak,retained_pixel_cache_bytes=surface.bytes,closed=surface.closed)
        result['conditions']['application_font_sources']=deepcopy(project_text._registered_font_files)
    if len(json.dumps(result,ensure_ascii=False).encode())>MAX_REPLY:
        result.update(status='INCOMPLETE',reason='Native diagnostics exceed1MiB; narrow selection. No complete-fit claim.',checks=[],failures=[],unrun=config['ids'])
    (folder/'RESULT.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False),encoding='utf8')
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[1]!='--worker':raise SystemExit('Use native_preflight from the existing manifest helper.')
    try:raise SystemExit(worker(sys.argv[2]))
    except Exception:traceback.print_exc();raise SystemExit(3)
