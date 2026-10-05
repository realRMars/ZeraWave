"""Scoped Fractals CPU contracts and optional owned, normal-time GPU sequence."""
import argparse,hashlib,json,math,os,struct,sys,time,zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
from development_forms import FRACTAL_FORMS
from fractals import FractalMotion
from audio_controls import form_targets,defaults,slots
from form_audio_tuning import FormAudioTuning
from audio_scope import Scope
from color_controls import fractal_authored_colors,targets_for,STATE_COLOR_SCENE,validate_colors

def cpu():
    import numpy as np
    from renderer import LIVE_FORMS
    assert len(LIVE_FORMS)==30 and set(FRACTAL_FORMS)<=set(LIVE_FORMS) and not set((37,38,39,40))&set(LIVE_FORMS)
    motion=FractalMotion()
    for i in range(50000):
        values=motion.advance(41,i/20.,.6,.4)
        assert all(math.isfinite(v) for v in values) and 0<=values[0]<8192. and 0<=values[1]<4096.
    before=values;assert motion.advance(41,2499.95,.6,.4)==before
    motion.advance(41,0.,.6,.4);assert motion.travel==motion.growth==0.
    motion.advance(41,99999.,1.,1.);assert motion.travel<.15 and motion.growth<=.004
    report=[]
    for form in FRACTAL_FORMS:
        model=FormAudioTuning('run','session');inputs=dict(bass=.4,movement=.3,flux=.2,sparkle=.5,impact=.6,raw_impact=.1)
        target=form_targets(form)[0];role=next(k for k in defaults(target) if k.endswith('_response'))
        c=dict(defaults(target),**{role:0.})
        model.submit(dict(scope=Scope('run','session',form,target,1).packet(),settings=c))
        rows=model.resolve([form],inputs);slot=slots(form)[target,role];assert rows[form][slot//4][slot%4]==0.
        # Enabled selected bins travel through the established FFT/local input path.
        f=np.arange(1025)*48000/2048
        model.process(f,np.ones(1025),2048,'synthetic')
        c=dict(defaults(target),bass_range_enabled=True,bass_start_hz=90.,bass_end_hz=130.)
        model.submit(dict(scope=Scope('run','session',form,target,2).packet(),settings=c));model.resolve([form],inputs)
        f=np.arange(1025)*48000/2048
        for n in range(4):model.observe(model.process(f,np.full(1025,1.+n*.1),2048,'synthetic'));model.resolve([form],inputs,2048/48000.)
        status=model.status(form,target,inputs);assert status['listening']['bass']['measurement']['bins']==2
        scene=STATE_COLOR_SCENE[form];color_target=targets_for(scene)[0]
        manual=validate_colors({color_target.id:{color_target.slots[0].id:dict(color='#123456')}})
        assert fractal_authored_colors(manual,form,190.)[color_target.id]==manual[color_target.id]
        report.append(dict(form=form,target=target,selected_bins=2,manual_color_preserved=True))
    return dict(Main30_integrated=True,bounded_clock_50000_steps=True,rewind_reset=True,low_rate_no_catchup=True,forms=report)

def apng(path,frames,seconds):
    # Standard-library lossless temporal artifact; fixed bounded frame count.
    h,w,_=frames[0].shape
    def chunk(k,d):return struct.pack('!I',len(d))+k+d+struct.pack('!I',zlib.crc32(k+d)&0xffffffff)
    data=bytearray(b'\x89PNG\r\n\x1a\n');data+=chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0));data+=chunk(b'acTL',struct.pack('!2I',len(frames),0));seq=0
    for i,pixels in enumerate(frames):
        data+=chunk(b'fcTL',struct.pack('!5I2H2B',seq,w,h,0,0,int(round(seconds*1000)),1000,0,0));seq+=1
        raw=zlib.compress(b''.join(b'\0'+row.tobytes() for row in pixels))
        if i==0:data+=chunk(b'IDAT',raw)
        else:data+=chunk(b'fdAT',struct.pack('!I',seq)+raw);seq+=1
    data+=chunk(b'IEND',b'');path.write_bytes(data)

def gpu(out,duration):
    import glfw,numpy as np
    from renderer import Renderer
    from shader_test import save_png
    from session_performance import process_resources,Distribution
    out.mkdir(parents=True,exist_ok=False)
    identity={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app').rglob('*') if p.is_file() and p.suffix in ('.py','.frag','.json')}
    record=dict(evidence='Normal-time synthetic inputs, owned hidden GPU window; silent, no decoded listening/scanout',source=identity,forms=[])
    init=glfw.init
    def hidden():
        ok=init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);glfw.window_hint(glfw.FOCUSED,glfw.FALSE);return ok
    try:
        for form in FRACTAL_FORMS:
            r=Renderer(width=640,height=360,seed=7301);r.debug_state=form;capture=None;row=dict(form=form,frames=0,resources=[],captures=[]);frames=[];interval=Distribution();last=None
            try:
                with patch.object(glfw,'init',hidden):r.create()
                capture=r.ctx.simple_framebuffer((640,360),components=3)
                glfw.swap_interval(0);row['create_GL_error']=r.ctx.error;row['startup']=r.startup_metrics;row['dimensions']=dict(client=glfw.get_window_size(r.window),framebuffer=glfw.get_framebuffer_size(r.window))
                start=time.perf_counter();capture_at=0.;resource_at=0.;deadline=start
                while True:
                    t=time.perf_counter()-start
                    if t>=duration:break
                    # Quiet/active/event/release blocks repeat with slow unequal drift.
                    phase=t%48.;activity=0.03 if phase<12. else .7 if phase<30. else .2 if phase<38. else .01
                    values=dict(scale=activity*(.75+.2*math.sin(t*.8)),movement=activity*.6,flux=activity*(.3+.3*math.sin(t*1.3)**2),sparkle=activity*(.5+.3*math.sin(t*2.)**2),impact=.9 if 24.<phase<30. and phase%1.<.07 else 0.)
                    for k,v in values.items():setattr(r.parameters,k,v)
                    r.render(t);r.poll_events();now=time.perf_counter()
                    if last is not None:interval.add(now-last)
                    last=now;row['frames']+=1
                    if t>=capture_at:
                        size=glfw.get_framebuffer_size(r.window)
                        r.ctx.copy_framebuffer(capture,r.ctx.screen)
                        pixels=np.frombuffer(capture.read(components=3,alignment=1),np.uint8).reshape(size[1],size[0],3)[::-1].copy()
                        if len(frames)<600:frames.append(pixels[::2,::2].copy())
                        if len(row['captures'])<12 and t>=len(row['captures'])*duration/12.:
                            name=f'form-{form}-{len(row["captures"]):02}.png';save_png(out/name,pixels);row['captures'].append(dict(path=name,seconds=t,motion=list((r.fractal_motions[form].travel,r.fractal_motions[form].growth))))
                        capture_at+=.2
                    r.swap_buffers()
                    if t>=resource_at:row['resources'].append(dict(seconds=t,**process_resources()));resource_at+=5.
                    deadline=max(deadline+1/30.,time.perf_counter());time.sleep(max(0.,deadline-time.perf_counter()))
                before=(r.fractal_motions[form].travel,r.fractal_motions[form].growth)
                target=targets_for(STATE_COLOR_SCENE[form])[0];r.set_colors({target.id:{target.slots[0].id:dict(color='#AA1155')}});r.render(r.last_render_time)
                assert before==(r.fractal_motions[form].travel,r.fractal_motions[form].growth)
                row['draw_GL_error']=r.ctx.error
                assert row['draw_GL_error']=='GL_NO_ERROR',row['draw_GL_error']
                glfw.set_window_size(r.window,480,270);r.poll_events();r.render(r.last_render_time+.033);r.swap_buffers()
                row['resize_GL_error']=r.ctx.error
                assert row['resize_GL_error']=='GL_NO_ERROR',row['resize_GL_error']
                row.update(intervals=interval.packet(),color_edit_preserves_motion=True,resize=True,elapsed_wall=time.perf_counter()-start)
                apng(out/f'form-{form}-motion.png',frames,.2)
            except BaseException as exc:row['error']=repr(exc);raise
            finally:
                if capture is not None:capture.release()
                r.close();row['owned_close_called']=True;record['forms'].append(row)
    finally:(out/'review-index.json').write_text(json.dumps(record,indent=2),encoding='utf8')
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--gpu',type=Path);p.add_argument('--seconds',type=float,default=120.);a=p.parse_args()
    print(json.dumps(cpu(),indent=2),flush=True)
    if a.gpu:gpu(a.gpu,a.seconds)
    print('Fractals checks PASS',flush=True)
