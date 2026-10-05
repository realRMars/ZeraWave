"""Owned GPU transition motion and actual scoped synthetic-spectrum consumers."""
import argparse,hashlib,json,math,os,sys,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
import glfw,numpy as np
from renderer import Renderer
from analyzer import AudioAnalyzer
from studio_color_link import configure_colors
from starfield_tuning import configure as configure_tuning
from audio_scope import Scope
from audio_controls import defaults,form_targets
from transition_catalog import compatible
from fractals_test import apng
from shader_test import save_png

def run(out,seconds=32.,pairs=None):
    out.mkdir(parents=True,exist_ok=False)
    source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app').rglob('*') if p.is_file() and p.suffix in ('.py','.frag','.vert','.json')}
    authored={p:p.read_bytes() for p in (ROOT/'app').rglob('*.json')}
    assert all(len(form_targets(f))==3 for f in (41,42,43)),'No inert shared-effect controls on Fractal'
    rd,wr=os.pipe();r=Renderer(width=640,height=360,seed=7301);r.debug_state=12;capture=None;cases=[]
    init=glfw.init
    def hidden():
        ok=init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);glfw.window_hint(glfw.FOCUSED,glfw.FALSE);return ok
    env={'ZERAWAVE_AUDIO_RUN':'structural-run','ZERAWAVE_AUDIO_SESSION':'structural-session','ZERAWAVE_PREVIEW_RUN':'structural-run'}
    try:
        with patch.dict(os.environ,env),patch('sys.stdin',SimpleNamespace(fileno=lambda:rd)):
            configure_colors(r,{},True);configure_tuning(r,AudioAnalyzer(),normal=True)
        with patch.object(glfw,'init',hidden):r.create()
        capture=r.ctx.simple_framebuffer((640,360),components=3);glfw.swap_interval(0)
        owner=r.studio_audio;owner.visible=True;owner.source_mode='SYNTHETIC';owner.source_identity='controlled48kHz-spectrum'
        frequencies=np.arange(1025)*48000/2048
        for key in ('tr_branch_iris','tr_flow_fold'):
            target='transition.'+key;config=dict(defaults(target),enabled=True,bass_response=.65,bass_range_enabled=True,bass_start_hz=90.,bass_end_hz=300.)
            owner.model.process(frequencies,np.ones(1025),2048,'controlled-spectrum')
            revision=1
            r.color_inbox.accept(json.dumps(dict(kind='audio-tuning',scope=Scope('structural-run','structural-session',0,target,revision).packet(),settings=config)))
            r.debug_sequence=();r.transition_sequence=False;r.debug_state=12;owner.last=-1000.;r.render(0.)
            assert owner.model.state[target]['revision']==revision
            assert not owner.contributions[target],'Inactive recipe must not claim contribution'
            # Stale and wrong-owner configuration must not alter the accepted values.
            r.color_inbox.accept(json.dumps(dict(kind='audio-tuning',scope=Scope('structural-run','structural-session',0,target,revision).packet(),settings=dict(config,bass_response=2.))))
            r.color_inbox.accept(json.dumps(dict(kind='audio-tuning',scope=Scope('foreign','structural-session',0,target,99).packet(),settings=config)))
            for pair in pairs or ((12,5),(41,42),(43,2)):
                assert compatible(key,*pair)
                r.debug_state=0;r.configure_transitions(dict(pair=list(pair),hold=4.,duration=8.,isolate={'pair':key}))
                row=dict(recipe=key,pair=pair,frames=0,captures=[],submissions=[],selected_ready=False);cases.append(row);movie=[]
                start=time.perf_counter();deadline=start;next_capture=0.;next_still=0.
                while True:
                    t=time.perf_counter()-start
                    if t>=seconds:break
                    phase=t%16.;activity=.03 if phase<4. else .72 if phase<10. else .2 if phase<14. else .02
                    for name,value in dict(scale=activity,movement=.8*activity,flux=.65*activity,sparkle=.7*activity,impact=.8 if 7.<phase<10. and phase%1.<.1 else 0.).items():setattr(r.parameters,name,value)
                    magnitudes=np.full(1025,.08+.12*activity*(1.+.3*math.sin(t*2.)))
                    owner.model.observe(owner.model.process(frequencies,magnitudes,2048,'controlled-spectrum'))
                    previous_snapshot=owner.last
                    r.render(t);row['frames']+=1
                    monitor_refreshed=owner.last!=previous_snapshot
                    if r.state_at(t)==0:
                        status=owner.model.status(0,target,owner.inputs)
                        ready=status.get('listening',{}).get('bass',{}).get('ready',False)
                        row['selected_ready'] |= ready
                        actual=r.program['u_structural_transition_audio'].value
                        expected=tuple(r.audio_input(0,key,s,v) for s,v in (('bass',r.parameters.scale),('flux',r.parameters.flux),('movement',r.parameters.movement),('impact',r.impact_envelope)))
                        assert np.allclose(actual,expected,rtol=0.,atol=1e-6)
                        # Availability belongs to the existing 200ms monitor cadence;
                        # audio submission above is still checked on every frame.
                        if monitor_refreshed:assert owner.contributions[target]
                        if len(row['submissions'])<12 and t>=4.+len(row['submissions'])*.5:row['submissions'].append(dict(seconds=t,actual=actual,expected=expected,ready=ready,scope=status['scope']))
                    if t>=next_capture and len(movie)<180:
                        r.ctx.copy_framebuffer(capture,r.ctx.screen)
                        pixels=np.frombuffer(capture.read(components=3,alignment=1),np.uint8).reshape(360,640,3)[::-1].copy()
                        movie.append(pixels[::2,::2].copy());next_capture+=.2
                        if t>=next_still and len(row['captures'])<12:
                            name=key+'-'+str(pair[0])+'-'+str(pair[1])+'-'+str(len(row['captures']))+'.png';save_png(out/name,pixels)
                            row['captures'].append(dict(file=name,seconds=t,sha256=hashlib.sha256((out/name).read_bytes()).hexdigest()));next_still+=3.
                    r.swap_buffers();r.poll_events()
                    assert r.ctx.error=='GL_NO_ERROR'
                    deadline=max(deadline+1/30.,time.perf_counter());time.sleep(max(0.,deadline-time.perf_counter()))
                assert row['selected_ready'] and owner.model.state[target]['settings']['bass_response']==.65
                name=key+'-'+str(pair[0])+'-'+str(pair[1])+'-motion.png';apng(out/name,movie,.2)
                row.update(movie=name,movie_sha256=hashlib.sha256((out/name).read_bytes()).hexdigest(),elapsed_wall=time.perf_counter()-start,inactive_edit_ACK=True,stale_owner_rejected=True)
    finally:
        if capture is not None:capture.release()
        r.close();os.close(wr);os.close(rd)
        (out/'review-index.json').write_text(json.dumps(dict(source=source,cases=cases,authored_JSON_preserved=all(p.read_bytes()==b for p,b in authored.items()),
            startup=r.startup_metrics,evidence='Normal-time synthetic musical controls + controlled FFT magnitudes with actual scoped tuning and GPU; silent, no decoded/natural listening or scanout',
            limits='Capture/readback enabled for motion; not an attribution/performance arm. Uniform0.2s APNG delay; exact selected still timestamps retained.'),indent=2),encoding='utf8')
    assert all(p.read_bytes()==b for p,b in authored.items())
    print('Structural transition normal-time GPU/scoped-input checks PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=float,default=32.);p.add_argument('--pair',type=int,nargs=2);a=p.parse_args();run(a.output,a.seconds,[tuple(a.pair)] if a.pair else None)
