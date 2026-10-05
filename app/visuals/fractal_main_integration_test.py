"""Actual shared-program Main/Fractal GPU boundaries and canonical leaf routing."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
import glfw,numpy as np
from renderer import Renderer,LIVE_FORMS
from world_catalog import main_entries,studio_trees
from shader_test import save_png
from studio_audition import capture,restore,PreviewAudition
from session_performance import process_resources
from color_controls import TARGETS,color_uniforms,STATE_COLOR_SCENE,targets_for

def run(output):
    output.mkdir(parents=True,exist_ok=False)
    source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app').rglob('*') if p.is_file() and p.suffix in ('.py','.frag','.vert','.json')}
    leaves=main_entries(LIVE_FORMS);assert len(leaves)==30 and {x['id'] for x in leaves}==set(LIVE_FORMS)
    assert all(x['category']=='Fractal' for x in leaves if x['id'] in (41,42,43))
    assert not set((37,38,39,40))&set(LIVE_FORMS)
    init=glfw.init
    def hidden():
        value=init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);glfw.window_hint(glfw.FOCUSED,glfw.FALSE);return value
    r=Renderer(width=640,height=360,seed=7301);r.debug_state=41
    frames=[];target=None;began=time.perf_counter()
    try:
        with patch.object(glfw,'init',hidden):r.create()
        startup=dict(r.startup_metrics);startup_resources=process_resources();program=r.program
        target=r.ctx.simple_framebuffer((640,360),components=3)
        r.parameters.scale=.55;r.parameters.movement=.6;r.parameters.flux=.5;r.parameters.sparkle=.7;r.parameters.impact=.25
        def draw(seconds,label):
            r.render(seconds);r.ctx.copy_framebuffer(target,r.ctx.screen)
            pixels=np.frombuffer(target.read(components=3,alignment=1),np.uint8).reshape(360,640,3)[::-1]
            assert r.program is program and r.ctx.error=='GL_NO_ERROR'
            assert float(pixels.std())>2.,(label,'blank/flat')
            name=label+'.png';save_png(output/name,pixels)
            frames.append(dict(file=name,sha256=hashlib.sha256((output/name).read_bytes()).hexdigest(),seconds=seconds,
                state=r.state_at(seconds),pair=r.program['u_fractal_pair'].value,contrast=float(pixels.std())))
            return pixels
        for form in (41,42,43):
            r.debug_state=form;r.debug_sequence=();r.transition_sequence=False;draw(0.,'held-'+str(form));draw(1.,'motion-'+str(form))
        snapshot=capture(r);before={f:dict(vars(c)) for f,c in r.fractal_motions.items()}
        r.fractal_motions[43].growth=77.;restore(r,snapshot)
        assert {f:dict(vars(c)) for f,c in r.fractal_motions.items()}==before
        for source_form,target_form in ((12,41),(41,2),(41,42),(42,43),(43,5)):
            r.debug_state=0;r.configure_transitions(dict(pair=[source_form,target_form],hold=1.,duration=2.,isolate={'pair':'tr_river'}))
            for seconds in (0.,1.,1.5,2.,2.5,3.,4.):draw(seconds,'pair-'+str(source_form)+'-'+str(target_form)+'-'+str(seconds))
        r.debug_state=43;r.debug_sequence=();r.transition_sequence=False;draw(5.,'audition-parked')
        trial=PreviewAudition(r);source_state={'position':7}
        def audition_source(action,snapshot=None):
            if action=='save':return dict(source_state)
            source_state.clear();source_state.update({'position':0} if action=='reset' else snapshot)
        trial.register_source(audition_source)
        parked=capture(r)
        for recipe in ('tr_branch_iris','tr_flow_fold'):
            cfg=dict(pair=[41,42],hold=1.,duration=2.,isolate={'pair':recipe})
            sequences=[]
            for repeat in range(2):
                trial.start(cfg,10.+repeat*5.)
                sequences.append([draw(t,'audition-'+recipe+'-'+str(repeat)+'-'+str(t)).copy() for t in (0.,.4,.9,1.3,2.,2.8,3.4)])
            assert all(np.array_equal(a,b) for a,b in zip(*sequences)),recipe+' GPU Repeat diverged'
            trial.return_live(20.)
            assert capture(r)==parked and source_state=={'position':7},recipe+' Return did not restore parked state'
        root_target=next(t for t in TARGETS if t.id=='roots.ridge')
        root_role=root_target.slots[0].id
        r.set_colors({'roots.ridge':{root_role:dict(color='#12AB34')}})
        r.debug_state=0;r.configure_transitions(dict(pair=[12,41],hold=1.,duration=2.,isolate={'pair':'tr_branch_iris'}))
        draw(1.7,'manual-main-fractal')
        expected=color_uniforms(r.color_overrides,[root_target.id],1.7,only=[root_target.id])
        assert r.program[root_target.uniform+'_on'].value==1
        assert np.allclose(r.program[root_target.uniform].value,expected[root_target.uniform],atol=1e-7)
        before=r.program[root_target.uniform].value
        r.set_colors({**r.color_overrides,'fractal.landscape.terrain':{'body':dict(color='#D035AF')}})
        draw(1.8,'manual-fractal-independent')
        assert r.program[root_target.uniform+'_on'].value==1 and r.program[root_target.uniform].value==before
        r.set_colors({});r.configure_transitions(dict(pair=[41,42],hold=1.,duration=2.,isolate={'pair':'tr_warp'}))
        warp_snapshot=capture(r)
        warped=draw(2.,'fractal-world-warp').copy()
        restore(r,warp_snapshot);r.configure_transitions(dict(pair=[41,42],hold=1.,duration=2.,isolate={'pair':'tr_fade'}))
        plain=draw(2.,'fractal-optical-reference').copy()
        assert not np.array_equal(warped,plain),'Fractal World warp must deform, not silently fade'
        glfw.set_window_size(r.window,480,270);glfw.poll_events();target.release();target=r.ctx.simple_framebuffer((480,270),components=3)
        r.render(4.2);assert glfw.get_framebuffer_size(r.window)==(480,270);assert r.ctx.error=='GL_NO_ERROR'
        packet=dict(source=source,leaf_roster=leaves,startup=startup,startup_process_resources=startup_resources,manual_Main_pigments_isolated=True,Fractal_World_warp=True,elapsed_wall_seconds=time.perf_counter()-began,frames=frames,
            shared_program=True,Fractal_clock_restore=True,structural_audition_repeat_pixels=True,structural_audition_Return_state=True,resize=True,evidence='Synthetic-input actual GPU shared program and endpoint sequences; sampled seconds, not normal-time motion or listening')
        (output/'review-index.json').write_text(json.dumps(packet,indent=2),encoding='utf8')
    finally:
        if target is not None:target.release()
        r.close()
    print('Fractal Main shared-program GPU integration checks PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
