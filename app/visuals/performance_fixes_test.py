"""Focused performance/preservation regressions; optional source-bound GPU matrix.

Run --gpu --output PATH in baseline and candidate environments, then --compare.
The matrix uses real Renderer, scoped edits, fixed inputs and explicit routes.
It is synthetic GPU evidence, not visible decoded playback or listening.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(os.environ.get('PERFORMANCE_SOURCE_ROOT',Path(__file__).resolve().parents[2]))
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]


def cpu_checks():
    import tempfile
    import numpy as np
    from preview_capture import ReplayTelemetry,CaptureWriter
    from preview_layers import validate_layers,profile_at,default_profile
    from resolved_audio import AudioUniformContract
    from fractals import integrated_shader
    from prepared_program import PreparedProgram
    with tempfile.TemporaryDirectory() as folder:
        rows=ReplayTelemetry(Path(folder)/'rows.csv')
        for i in range(10000):
            rows.append(dict(seconds=i*.1,state='roots',count=i))
            rows[-1].update(flag=i%2==0)
        rows.close();assert len(rows)==10000 and rows[-1]['count']==9999
        assert next(iter(rows))==dict(seconds=0.,state='roots',count=0,flag=True)
        assert not isinstance(rows,list) and rows.pending is None
        rows.handle.close()
        writer=CaptureWriter(folder)
        assert writer.submit(bytes([22,88,255])*64,(8,8),dict(file='frame.png',seconds=0.))
        writer.close();assert not writer.errors and len(writer.records)==1
        record=writer.records[0];assert record['clipped_fraction']==1. and record['dark_fraction']==0.
        assert (Path(folder)/'frame.png').is_file() and writer.thread is None
        # Hold the real worker during encoding: two waiting frames fit, the next
        # capture drops immediately, and normal shutdown drains all accepted work.
        import threading
        entered=threading.Event();resume=threading.Event()
        def paused_png(*args):entered.set();assert resume.wait(5.)
        with patch('shader_test.save_png',paused_png):
            writer=CaptureWriter(folder)
            try:
                assert writer.submit(bytes(192),(8,8),dict(file='first.png'))
                assert entered.wait(5.)
                assert writer.submit(bytes(192),(8,8),dict(file='second.png'))
                assert writer.submit(bytes(192),(8,8),dict(file='third.png'))
                assert not writer.submit(bytes(192),(8,8),dict(file='dropped.png'))
            finally:resume.set();writer.close()
            assert writer.dropped==1 and len(writer.records)==3 and not writer.errors
    from studio_audio import StudioAudio
    now=[10.]
    monitor=SimpleNamespace(visible=False,audition=SimpleNamespace(revision=0),last_audition_ack=0,last=9.9,clock=lambda:now[0])
    assert not StudioAudio.snapshot_due(monitor)
    monitor.audition.revision=1;assert not StudioAudio.snapshot_due(monitor)
    now[0]=10.2;assert StudioAudio.snapshot_due(monitor)
    monitor.last_audition_ack=1;assert not StudioAudio.snapshot_due(monitor)
    monitor.visible=True;assert StudioAudio.snapshot_due(monitor)
    profiles=validate_layers({})
    a=default_profile('blend');b=default_profile('blend');a['items'].clear();assert b['items']
    profiles['organic']=dict(mode='meld',seconds=12.,items=[])
    assert profile_at(profiles,12)['mode']=='meld'
    profiles['organic']['mode']='authored';assert profile_at(profiles,12)['mode']=='authored'
    source=integrated_shader((ROOT/'app/visuals/shaders/dream.frag').read_text(encoding='utf8'))
    contract=AudioUniformContract(source)
    assert 'float form_audio(' not in contract.source and 'float planet_audio(' not in contract.source
    class U:
        array_length=1000
        value=None
    program={key:U() for key in ('u_resolved_forms','u_resolved_shared','u_resolved_families','u_resolved_water','u_resolved_currents')}
    r=SimpleNamespace(program=program,parameters=SimpleNamespace(scale=.3,flux=.4,sparkle=.5),impact_envelope=.6)
    a=[(1.,)*4]*32;b=[(1.,)*4]*32
    a=list(a);a[16]=(3.,-1.75,0.,1.)
    contract.upload(r,(2,12),a,b,0,[(1.,)*4]*45)
    index=contract.forms.index((36,68,'bass'));assert np.float32(program['u_resolved_forms'].value[index//4][index%4])==np.float32(.3)
    index=contract.forms.index((2,65,'flux'));assert program['u_resolved_forms'].value[index//4][index%4]==.75
    # Incoming ownership, encoded replacements, and local-derived gains are
    # independent; do not replace attenuated impact/descriptor aliases with raw inputs.
    from resolved_audio import source_kind
    assert source_kind('impact')==source_kind('bass')=='derived'
    assert source_kind('clamp(u_flux,0.,1.)')=='flux_clipped'
    b=list(b);b[16]=(0.,2.,-1.25,.73)
    contract.upload(r,(2,12),a,b,0,[(1.,)*4]*45)
    for form,slot,kind in contract.forms:
        if form!=12:continue
        i=contract.forms.index((form,slot,kind));g=np.float32(b[slot//4][slot%4])
        v=program['u_resolved_forms'].value[i//4][i%4]
        if kind=='derived':assert v==float(g)
    contract.upload(r,(7,10),a,b,0,[(1.,)*4]*45)
    assert program['u_resolved_water'].value[0][0]==float(np.float32(.3)*np.float32(3.))
    assert program['u_resolved_water'].value[0][3]==0.
    assert program['u_resolved_water'].value[1][0]==.75
    assert program['u_resolved_water'].value[1][3]==float(np.float32(.8))
    class Resource(dict):
        def release(self):pass
    context=SimpleNamespace(info={'GL_VENDOR':'Test'},program=lambda **kw:Resource(),simple_vertex_array=lambda *a:Resource())
    p=PreparedProgram(context,None,'','uniform vec4 declared[4];')
    p['declared'].value=[(1.,)*4]*4
    assert p['declared'].array_length==4 and 'declared' not in p.active_uniforms
    assert p['declared'].value==[(1.,)*4]*4
    try:p['typo']
    except KeyError:pass
    else:raise AssertionError('Unknown uniform accepted')
    print('Performance fixes CPU regressions PASS')


def gpu_matrix(output):
    import numpy as np
    import glfw
    from renderer import Renderer,LIVE_FORMS
    from analyzer import AudioAnalyzer
    from studio_color_link import configure_colors
    from starfield_tuning import configure as configure_tuning
    from audio_controls import TARGETS,defaults
    from audio_scope import Scope
    from shader_test import save_png
    os.environ.update(ZERAWAVE_AUDIO_RUN='perf-matrix',ZERAWAVE_AUDIO_SESSION='perf-session')
    os.environ.pop('ZERAWAVE_PREVIEW_RUN',None);os.environ.pop('ZERAWAVE_PERFORMANCE_DIR',None)
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=640,height=360,seed=7301)
    r.startup_callback=lambda phase:print('Matrix startup',phase,flush=True)
    read,write=os.pipe()
    with patch('sys.stdin',SimpleNamespace(fileno=lambda:read)):configure_colors(r,{},True)
    analyzer=AudioAnalyzer();configure_tuning(r,analyzer,normal=True)
    init=glfw.init
    def hidden():
        result=init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);glfw.window_hint(glfw.FOCUSED,glfw.FALSE);glfw.window_hint(glfw.DECORATED,glfw.FALSE);return result
    records=[];frames=[];query=None
    try:
        with patch.object(glfw,'init',hidden):r.create()
        r.startup_callback=None
        print('Matrix created',r.startup_metrics,flush=True)
        (output/'startup.json').write_text(json.dumps(r.startup_metrics,indent=2))
        glfw.swap_interval(0);query=r.ctx.query(time=True)
        shader=(ROOT/'app/visuals/shaders/dream.frag').read_text(encoding='utf8')
        source={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app').rglob('*') if p.suffix in ('.py','.frag','.json')}
        def draw(label,seconds,level):
            p=r.parameters
            p.scale=level;p.movement=.35+level*.25;p.flux=level*.53;p.sparkle=level*.83;p.impact=.55 if level>.8 else 0.
            p.beat_tick=False;p.beat_confidence=.55
            begin=time.perf_counter()
            if not records:print('Matrix first render begin',flush=True)
            with query:r.render(seconds)
            if not records:print('Matrix first render done',flush=True)
            cpu=(time.perf_counter()-begin)*1000.;gpu=query.elapsed/1e6
            raw=r.ctx.screen.read(components=3,alignment=1)
            image=np.frombuffer(raw,np.uint8).reshape(360,640,3).copy()
            records.append(dict(label=label,seconds=seconds,level=level,sha256=hashlib.sha256(raw).hexdigest(),gpu_ms=gpu,cpu_ms=cpu))
            frames.append(image)
            r.swap_buffers();r.poll_events()
        for edited in (False,True):
            if edited:
                for target,info in TARGETS.items():
                    if info['form']==0:continue
                    settings=defaults(target)
                    for i,role in enumerate(info['roles']):
                        if role['source']!='timer':settings[role['key']]=(.0,.73,1.4,2.)[i%4]
                    r.studio_audio.model.submit(dict(scope=Scope('perf-matrix','perf-session',info['form'],target,1).packet(),settings=settings))
                # Planet adapter edits exercise its retained encoded-gain path.
                from planet_audio_tuning import SPECS,baseline
                for target,roles in SPECS.items():
                    settings=baseline(target)
                    for i,role in enumerate(roles):settings[role['key']]=(.0,.73,1.4,2.)[i%4]
                    r.planet_audio_tuning.submit(target,1,settings)
            for form in LIVE_FORMS:
                r.debug_state=form;r.debug_sequence=();r.transition_sequence=False
                for seconds,level in ((0.,.0),(.25,.6),(.5,.98),(.75,.2)):
                    draw(f'held-{form}-edited{int(edited)}',seconds,level)
            for a,b in ((22,15),(10,2),(12,41),(22,26),(5,36),(32,29),(41,43)):
                for recipe in ('tr_fade','tr_aperture','tr_branch_iris','tr_flow_fold'):
                    r.debug_state=0;r.configure_transitions(dict(pair=[a,b],hold=1.,duration=2.,isolate={'pair':recipe}))
                    for seconds in (0.,1.,1.5,2.,2.5,3.,4.):draw(f'pair-{a}-{b}-{recipe}-edited{int(edited)}',seconds,.98)
        # Explicit resize/restore and ordinary Main holds are separate callers.
        r.transition_sequence=False;r.debug_state=0;r.director_current=None;r.director_target=None
        draw('ordinary-main',0.,.6);draw('ordinary-main',.25,.98)
        glfw.set_window_size(r.window,800,450);glfw.poll_events();r.render(.5);r.swap_buffers()
        assert glfw.get_framebuffer_size(r.window)==(800,450)
        glfw.set_window_size(r.window,640,360);glfw.poll_events();draw('resize-return',.75,.6)
        np.savez_compressed(output/'frames.npz',frames=np.asarray(frames))
        for i in (0,45,80,len(frames)-4):save_png(output/f'sample-{i}.png',frames[i][::-1])
        result=dict(evidence='Hidden synthetic real GPU; synchronous timing/readback; scoped edited gains; no listening',source=source,
            size=dict(client=glfw.get_window_size(r.window),framebuffer=glfw.get_framebuffer_size(r.window),viewport=r.ctx.viewport),
            startup=r.startup_metrics,device=r.ctx.info,records=records)
        (output/'matrix.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    finally:
        r.close();os.close(write)
    print('GPU matrix complete',len(records),output)


def compare(before,after):
    import numpy as np
    a=json.loads((before/'matrix.json').read_text());b=json.loads((after/'matrix.json').read_text())
    assert [(r['label'],r['seconds'],r['level']) for r in a['records']]==[(r['label'],r['seconds'],r['level']) for r in b['records']]
    aa=np.load(before/'frames.npz')['frames'];bb=np.load(after/'frames.npz')['frames']
    mismatches=[]
    for i,(x,y) in enumerate(zip(aa,bb)):
        d=np.abs(x.astype(np.int16)-y.astype(np.int16))
        if d.max():mismatches.append(dict(index=i,label=b['records'][i]['label'],seconds=b['records'][i]['seconds'],max=int(d.max()),mean=float(d.mean()),fraction_pixels_over1=float((d.max(axis=2)>1).mean())))
    result=dict(cases=len(aa),exact=len(aa)-len(mismatches),mismatches=mismatches)
    (after/'comparison.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(cases=result['cases'],exact=result['exact'],mismatches=len(mismatches),worst=sorted(mismatches,key=lambda r:r['mean'],reverse=True)[:12]),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');p.add_argument('--output',type=Path)
    p.add_argument('--compare',type=Path,nargs=2);args=p.parse_args()
    if args.compare:compare(*args.compare)
    elif args.gpu:gpu_matrix(args.output)
    else:cpu_checks()
