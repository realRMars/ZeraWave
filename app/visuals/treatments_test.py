"""Standalone real-GPU checks for nine treatments; no natural audio playback."""
import argparse
import json
import time
from pathlib import Path
import glfw
import moderngl
import numpy as np
from renderer import Renderer, VERTEX_SHADER
from preview_layers import MATERIALS, NEW_MATERIALS, validate_layers
from color_controls import TARGETS
from shader_test import save_png


def profile(keys):
    return {'cosmic':dict(mode='together',seconds=12.,items=[dict(id=key,enabled=True) for key in keys])}


def gpu_checks(baseline, output, batch='materials'):
    output.mkdir(parents=True,exist_ok=True)
    r=Renderer(width=640,height=360,seed=2)
    old=vao=None
    report={}
    def pixels():
        return np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(360,640,3)[::-1].copy()
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create()
        old=r.ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=baseline.read_text(encoding='utf-8'))
        vao=r.ctx.simple_vertex_array(old,r.vertices,'in_position')
        for state in range(36):
            # Explicit legacy profile disables additions even after Main's new defaults.
            r.layer_profiles={'blend':dict(mode='together',seconds=22.,items=[dict(id='artifacts',enabled=True)])}
            r.debug_state=state;r.render(elapsed_time=20.+state*.01)
            actual=pixels()
            for name in old:
                if name in r.program and hasattr(old[name],'value'):old[name].value=r.program[name].value
            vao.render(mode=moderngl.TRIANGLE_STRIP)
            assert np.array_equal(actual,pixels()),('disabled preservation',state)
        report['disabled_exact_states']=36
        r.debug_state=5;clock=22.
        for key in NEW_MATERIALS:
            r.layer_profiles=profile((key,'stars','rings','moons'))
            captures=[];timings=[]
            for index in range(181):
                t=index/30.;level=.06 if t<2. or t>=4. else .8
                r.parameters.scale=r.parameters.movement=r.parameters.flux=r.parameters.sparkle=level
                r.parameters.impact=.5 if index==60 else 0.
                start=time.perf_counter()
                with r.ctx.query(time=True) as query:r.render(elapsed_time=clock+t)
                image=pixels();timings.append((query.elapsed/1e6,(time.perf_counter()-start)*1000))
                if index in (30,90,180):
                    assert image.std()>4
                    save_png(output/f'{key}-{index}.png',image)
                    captures.append(image)
            assert np.abs(captures[0].astype(float)-captures[1]).mean()>1.
            # Match all uniforms/time for live pigment change and exact reset.
            target=next(t for t in TARGETS if t.id=='material.'+{'ink_archipelago':'ink','interference_silk':'silk','cellular_mosaic':'mosaic'}[key])
            r.set_colors({target.id:{role.id:{'color':'#B7289B'} for role in target.slots}})
            r.render(elapsed_time=clock+6.);edited=pixels()
            r.set_colors({});r.render(elapsed_time=clock+6.);reset=pixels()
            assert np.abs(edited.astype(float)-reset).mean()>.1,(key,'color target')
            assert np.array_equal(reset,captures[-1]),(key,'reset')
            report[key]=dict(gpu_ms_median=float(np.median(np.array(timings)[30:,0])),
                draw_readback_ms_median=float(np.median(np.array(timings)[30:,1])),
                color_changed_pixels=int(np.any(edited!=reset,axis=2).sum()))
            clock+=7.
        from preview_layers import SPATIAL_TREATMENTS
        for key in SPATIAL_TREATMENTS:
            r.layer_profiles=profile(('cellular_mosaic','rings','moons'))
            r.render(elapsed_time=clock);untreated=pixels()
            r.layer_profiles=profile(('cellular_mosaic','rings','moons',key))
            with r.ctx.query(time=True) as query:r.render(elapsed_time=clock)
            changed=pixels()
            assert np.abs(changed.astype(float)-untreated).mean()>.03,(key,'no spatial effect')
            save_png(output/f'{key}.png',np.concatenate((untreated,changed),axis=1))
            r.layer_profiles=profile(('cellular_mosaic','rings','moons'))
            r.render(elapsed_time=clock)
            assert np.array_equal(untreated,pixels()),(key,'reset')
            report[key]=dict(changed_pixels=int(np.any(changed!=untreated,axis=2).sum()),gpu_ms=query.elapsed/1e6)
            clock+=1.
        from preview_layers import ENVELOPERS
        for key in ENVELOPERS:
            r.layer_profiles=profile(('cellular_mosaic','stars','rings','moons',key))
            timings=[];last=None
            for i in range(91):
                level=.05 if i<25 or i>65 else .85
                r.parameters.scale=r.parameters.flux=r.parameters.sparkle=level
                with r.ctx.query(time=True) as query:r.render(elapsed_time=clock+i/30.)
                changed=pixels()
                assert r.enveloper_stage is not None and not r.enveloper_failed,key
                assert len(r.enveloper_stage.textures)==3 and len(r.enveloper_stage.targets)==3
                timings.append(query.elapsed/1e6)
                if i in (20,50,90):
                    source=np.frombuffer(r.enveloper_stage.targets[0].read(components=3),np.uint8).reshape(360,640,3)[::-1].copy()
                    save_png(output/f'{key}-{i}.png',np.concatenate((source,changed),axis=1))
                    if i==50:assert np.abs(source.astype(float)-changed).mean()>.05,(key,'no scene transform')
                if last is not None:assert np.abs(changed.astype(float)-last).mean()<35.,(key,'flash')
                last=changed
            stage=r.enveloper_stage;assert stage.allocations==1
            resets=stage.resets;r.render(elapsed_time=clock+2.)
            assert stage.resets>resets,(key,'seek reset')
            resets=stage.resets;r.render(elapsed_time=clock+5.)
            assert stage.resets>resets,(key,'gap reset')
            r.layer_profiles=profile(('cellular_mosaic','rings','moons'));r.render(elapsed_time=clock+5.01)
            assert r.enveloper_stage is None and not stage.textures and not stage.targets
            report[key]=dict(gpu_ms_median=float(np.median(timings[10:])),lifecycle='startup/seek/gap/disable passed')
            clock+=6.
        report['gpu']=r.ctx.info['GL_RENDERER'];report['resolution']=[640,360]
        report['note']='Synthetic evolving GPU run. CPU timing includes readback and is not normal playback FPS.'
        (output/'checks.json').write_text(json.dumps(report,indent=2))
        print('PASS:',json.dumps(report),flush=True)
    finally:
        if vao:vao.release()
        if old:old.release()
        r.close()

def studio_checks(output):
    import tkinter as tk
    import runpy,sys
    from copy import deepcopy
    from contextlib import ExitStack
    from unittest.mock import patch
    from studio import Studio,command,tracks,SOURCES,validate_session
    from color_controls import validate_colors,color_uniforms,family_setup,PALETTE_FAMILIES,color_preset,validate_preset
    from preview_layers import SPATIAL_TREATMENTS,ENVELOPERS,treatment_weights,material_weights,material_quartet_profile,layers_at
    output.mkdir(parents=True,exist_ok=True)
    for t in range(0,216):
        authored={'blend':dict(mode='authored',seconds=12.,items=[])}
        assert material_weights({},0,t)==material_weights(authored,0,t)
        assert layers_at({},0,t)==layers_at(authored,0,t)
        a=treatment_weights({},0,t,ENVELOPERS);b=treatment_weights({},0,t,SPATIAL_TREATMENTS)
        assert sum(x>0 for x in a)<=1 and not (max(a)>0 and max(b)>0)
        assert a==treatment_weights(authored,0,t,ENVELOPERS)
        assert not any(treatment_weights({'blend':material_quartet_profile('blend')},0,t,ENVELOPERS))
    root=tk.Tk();root.withdraw();app=Studio(root)
    try:
        for key in NEW_MATERIALS+SPATIAL_TREATMENTS+ENVELOPERS:
            app.review_treatment(key)
            assert app.selection==['cosmic','canvas']
            assert any(item['id']==key and item['enabled'] for item in app.values()['layers']['cosmic']['items'])
        app.review_treatment('ink_archipelago');app.open_color_inspector();editor=app.color_editor
        for target_id,families in PALETTE_FAMILIES.items():
            target=next(t for t in TARGETS if t.id==target_id)
            editor.target_choice.set(target.label);editor.refresh();editor.reset_target()
            editor.store_setup()
            for family in families:
                editor.family_choice.set(family);editor.hold_family();editor.store_setup()
            editor.cycle_mode.set('cycle');editor.cycle_hold.set('2');editor.cycle_fade.set('1');editor.apply_cycle()
            clean=app.color_overrides
            assert clean[target_id]['_cycle']['mode']=='cycle'
            a=color_uniforms(clean,[target_id],0.)[target.uniform]
            b=color_uniforms(clean,[target_id],3.)[target.uniform]
            assert a!=b
            assert color_uniforms(clean,[target_id],2.5)==color_uniforms(clean,[target_id],2.5)
            editor.rows[target.slots[0].id][0].set('#123456');editor.edit_hex(target.slots[0].id)
            assert app.color_overrides[target_id]['_cycle']['mode']=='hold'
            editor.cycle_mode.set('cycle');editor.apply_cycle()
        cycle_data=deepcopy(app.color_overrides)
        assert validate_preset(color_preset('Cycles','canvas',cycle_data))['targets']==cycle_data
        app.session_path=output/'cycles-session.json';app.save();app.new()
        with patch('studio.filedialog.askopenfilename',return_value=str(output/'cycles-session.json')):app.load()
        assert app.color_overrides==cycle_data
        for version in (1,2,3):assert 'color_overrides' not in validate_session(dict(version=version,state='canvas',selection=['cosmic','canvas']))
        for bad in ({'mode':'cycle','setups':[{}]}, {'mode':'cycle','hold':0,'setups':[{},{}]},
                    {'mode':'cycle','setups':[{}, {'wrong':{'color':'#000000'}}]},
                    {'mode':'cycle','setups':[{}, {'_cycle':{}}]}):
            try:validate_colors({'material.ink':{'_cycle':bad}})
            except ValueError:pass
            else:raise AssertionError('Invalid cycle accepted')
        # A staged gradient cycles only its own roles; ranges stay ordered throughout.
        target=next(t for t in TARGETS if t.kind=='staged_gradient')
        setup={slot.id:{'color':'#556677'} for slot in target.slots}
        gradient=validate_colors({target.id:{'_cycle':dict(mode='cycle',hold=2.,fade=1.,setups=[{},setup])}})
        for t in np.arange(0.,6.,.1):
            ranges=color_uniforms(gradient,[target.id],t)[target.uniform+'_ranges']
            assert all(b-a>=.001 for a,b in ranges)
        app.review_treatment('elastic_lenses');app.layer_table.selection_set('elastic_lenses')
        app.treatment_amount.set('.35');app.change_treatment_amount()
        assert treatment_weights(app.values()['layers'],5,0.,SPATIAL_TREATMENTS)==(.35,0.,0.)
        assert validate_session(dict(version=3,**app.values()))['layers']==app.values()['layers']
        app.vars['track'].set(str(tracks()[0]));app.vars['captures'].set(False)
        launch=app.values()
    finally:app.close()
    class ControlledCapture:
        def __init__(self,**kwargs):pass
        def find_device(self):return 'Controlled input, not audible review'
        def start(self):pass
        def stop(self):pass
        def read(self,**kwargs):return np.zeros((2048,2),np.float32)
    for source in SOURCES:
        for key in NEW_MATERIALS+SPATIAL_TREATMENTS+ENVELOPERS:
            seen=[]
            keys=(key,) if key in NEW_MATERIALS else ('cellular_mosaic',key)
            expected=profile(keys+('rings','moons'))
            class Observed(Renderer):
                def __init__(self,*args,**kwargs):super().__init__(width=320,height=180,seed=2)
                def create(self):glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);super().create()
                def should_close(self):return len(seen)>=3
                def render(self,elapsed_time=None):
                    t=3.+len(seen)/30.;super().render(elapsed_time=t)
                    assert np.allclose(self.program['u_new_materials'].value,material_weights(expected,5,t)[4:])
                    assert np.allclose(self.program['u_spatial_treatments'].value,treatment_weights(expected,5,t,SPATIAL_TREATMENTS))
                    assert (self.enveloper_stage is not None)==(key in ENVELOPERS)
                    assert not self.enveloper_failed
                    assert self.program['u_ink_colors_on'].value==1
                    assert np.allclose(self.program['u_ink_colors'].value,color_uniforms(cycle_data,['material.ink'],t)['u_ink_colors'])
                    if key in ENVELOPERS:
                        target_id='enveloper.'+dict(prism_assembly='prism',digital_bloom='digital',chromatic_memory='memory')[key]
                        target=next(t for t in TARGETS if t.id==target_id)
                        assert self.enveloper_stage.program[target.uniform+'_on'].value==1
                    seen.append(t)
            args=command(dict(launch,source=source,layers=expected),output)
            offset=next(i for i,a in enumerate(args) if a.endswith('.py'))
            with ExitStack() as stack:
                stack.enter_context(patch('renderer.Renderer',Observed));stack.enter_context(patch.object(sys,'argv',args[offset:]))
                if source=='Live system audio':stack.enter_context(patch('capture.AudioCapture',ControlledCapture))
                runpy.run_path(args[offset],run_name='__main__')
            assert len(seen)==3
    print('PASS: all nine Studio presets and all 27 real GPU launch routes; cycles/manual precedence, sessions/presets, validation and Main schedule. Live input controlled.',flush=True)


def extended_checks(output):
    from unittest.mock import patch
    from preview_layers import SPATIAL_TREATMENTS,ENVELOPERS
    from envelopers import EnveloperStage
    from color_controls import family_setup
    output.mkdir(parents=True,exist_ok=True);report={}
    r=Renderer(width=1280,height=720,seed=2)
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create();r.debug_state=5
        glfw.swap_interval(0)
        r.parameters.scale=r.parameters.flux=r.parameters.sparkle=.65
        # Matched scene and warm GPU queries; include scene/post/presentation, exclude vsync.
        costs={}
        for key in ('baseline',)+NEW_MATERIALS+SPATIAL_TREATMENTS+ENVELOPERS:
            keys=('artifacts',) if key=='baseline' else ((key,) if key in NEW_MATERIALS else ('artifacts',key))
            r.layer_profiles=profile(keys+('rings','moons','stars'))
            samples=[]
            for i in range(90):
                r.render(elapsed_time=20.+i/60.)
                # Paired untreated scene, same clocks/details/audio; warmed candidate resources retained.
                saved={name:r.program[name].value for name in ('u_new_materials','u_spatial_treatments','u_material_mix','u_layer_mask')}
                r.program['u_new_materials'].value=(0.,0.,0.);r.program['u_spatial_treatments'].value=(0.,0.,0.)
                r.program['u_material_mix'].value=(1.,0.,0.)
                from preview_layers import BITS
                r.program['u_layer_mask'].value=sum(BITS[k] for k in ('artifacts','rings','moons','stars'))
                with r.ctx.query(time=True) as untreated:r.vao.render(mode=moderngl.TRIANGLE_STRIP)
                baseline_ms=untreated.elapsed/1e6
                for name,value in saved.items():r.program[name].value=value
                begin=time.perf_counter()
                with r.ctx.query(time=True) as query:r.render(elapsed_time=20.+(i+.5)/60.)
                r.swap_buffers();r.poll_events();r.ctx.finish()
                if i>=20:samples.append((query.elapsed/1e6,(time.perf_counter()-begin)*1000,baseline_ms))
            data=np.array(samples)
            costs[key]={'gpu_median_ms':float(np.median(data[:,0])),'gpu_p95_ms':float(np.percentile(data[:,0],95)),
                        'draw_swap_events_median_ms':float(np.median(data[:,1])),
                        'paired_untreated_gpu_ms':float(np.median(data[:,2])),
                        'gpu_added_ms':float(np.median(data[:,0]-data[:,2]))}
        report['cost_1280x720']=costs;report['gpu']=r.ctx.info['GL_RENDERER']
        # Repeated enable, resize, color edits, cap, held-state changes and cleanup.
        r.layer_profiles=profile(('cellular_mosaic','chromatic_memory','elastic_lenses','rings','moons'))
        stages=[]
        for iteration in range(6):
            r.render(elapsed_time=40.+iteration);stage=r.enveloper_stage;stages.append(stage)
            before=stage.resets
            for j in range(12):
                r.set_colors({'enveloper.memory':{'red':{'color':f'#{80+j:02X}AABB'}}})
                r.render(elapsed_time=40.+iteration+(j+1)/60.)
            assert stage.resets==before and len(stage.textures)==3 and stage.allocations==1
            glfw.set_window_size(r.window,640,360);r.poll_events();r.render(elapsed_time=40.3+iteration)
            assert stage.size==(640,360) and stage.allocations==2
            glfw.set_window_size(r.window,1280,720);r.poll_events();r.render(elapsed_time=40.4+iteration)
            assert stage.allocations==3
            r.layer_profiles=profile(('cellular_mosaic',));r.render(elapsed_time=40.45+iteration)
            assert r.enveloper_stage is None and not stage.textures and not stage.targets
            r.layer_profiles=profile(('cellular_mosaic','chromatic_memory','elastic_lenses','rings','moons'))
        r.render(elapsed_time=47.);stage=r.enveloper_stage
        with patch.object(EnveloperStage,'MAX_PIXELS',320*180):
            r.render(elapsed_time=47.1)
            assert stage.size==(320,180)
            image=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(720,1280,3)
            assert image[:,640:].std()>5 and image[:,:640].std()>5
        r.render(elapsed_time=47.2);assert stage.size==(1280,720)
        # Fail only this owned stage; renderer must recover direct scene and release it.
        with patch.object(stage,'draw',side_effect=RuntimeError('intentional fallback fixture')):
            r.render(elapsed_time=47.3)
        assert r.enveloper_failed and r.enveloper_stage is None and not stage.textures
        r.layer_profiles=profile(('artifacts',));r.render(elapsed_time=47.4);assert not r.enveloper_failed
        r.layer_profiles=profile(('artifacts','chromatic_memory'));r.render(elapsed_time=47.5)
        assert r.enveloper_stage is not None
        # Main boundary samples: actual director transitions while the post stage is active.
        r.layer_profiles={};r.debug_state=0
        for t in np.arange(180.,206.,1/30.):r.render(elapsed_time=float(t))
        assert not r.enveloper_failed
        save_png(output/'main-memory.png',np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(720,1280,3)[::-1])
        report['lifecycle']='6 toggle/resize/edit rounds, cap upscale, failure fallback, recovery, Main transition, shutdown'
    finally:
        stage=r.enveloper_stage;r.close()
        if stage:assert not stage.textures and not stage.targets
    # Actual renderer at different update rates, identical endpoint time/input.
    rates={}
    for key in ENVELOPERS:
        frames=[]
        for hz in (30,60,120):
            r=Renderer(width=320,height=180,seed=2)
            try:
                glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);r.create();r.debug_state=5
                r.layer_profiles=profile(('cellular_mosaic','rings','moons','braided_flow',key))
                r.parameters.scale=r.parameters.flux=r.parameters.sparkle=.5
                for i in range(hz*2+1):r.render(elapsed_time=i/hz)
                image=np.frombuffer(r.ctx.screen.read(components=3),np.uint8).reshape(180,320,3)[::-1].copy()
                frames.append(image);save_png(output/f'{key}-{hz}hz.png',image)
            finally:r.close()
        errors=[float(np.abs(frame.astype(float)-frames[-1]).mean()) for frame in frames[:-1]]
        assert max(errors)<5.,(key,errors)
        rates[key]={'mean_byte_error_vs_120hz':errors}
    report['rates']=rates
    (output/'extended.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS extended:',json.dumps(report),flush=True)


def replay_checks(output):
    from unittest.mock import patch
    import replay_test
    from studio import tracks
    from preview_layers import SPATIAL_TREATMENTS,ENVELOPERS,treatment_weights,material_weights
    output.mkdir(parents=True,exist_ok=True)
    frames=[];seen_materials=set();seen_envelopers=set();seen_spatial=set();worlds=set()
    class Measured(Renderer):
        def __init__(self,*args,**kwargs):
            kwargs.update(width=1280,height=720);super().__init__(*args,**kwargs)
        def create(self):
            glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);super().create();glfw.swap_interval(0)
        def render(self,elapsed_time=None):
            before=time.perf_counter()
            with self.ctx.query(time=True) as query:super().render(elapsed_time)
            elapsed=query.elapsed/1e6
            assert not self.enveloper_failed
            t=elapsed_time
            seen_materials.update(i for i,w in enumerate(material_weights(self.layer_profiles,0,t)) if w>.1)
            seen_envelopers.update(i for i,w in enumerate(treatment_weights(self.layer_profiles,0,t,ENVELOPERS)) if w>.1)
            seen_spatial.update(i for i,w in enumerate(treatment_weights(self.layer_profiles,0,t,SPATIAL_TREATMENTS)) if w>.1)
            worlds.add(self.director_current)
            frames.append((t,elapsed,(time.perf_counter()-before)*1000))
    track=next(t for t in tracks() if 'warbot' in t.name.lower())
    before=time.perf_counter()
    with patch.object(replay_test,'Renderer',Measured):
        seconds,rows=replay_test.replay(track,speed=0,max_seconds=216.,state='blend',seed=2,
            metrics_path=output/'metrics.csv',capture_dir=output/'captures',capture_interval=12.)
    wall=time.perf_counter()-before
    assert seen_materials==set(range(7)) and seen_envelopers==set(range(3)) and seen_spatial==set(range(3))
    data=np.array(frames)
    report=dict(track=str(track),song_seconds=seconds,frames=len(rows),resolution=[1280,720],wall_seconds=wall,
        processed_frames_per_wall_second=len(rows)/wall,gpu_median_ms=float(np.median(data[:,1])),gpu_p95_ms=float(np.percentile(data[:,1],95)),
        worlds=sorted(worlds),materials=sorted(seen_materials),spatial=sorted(seen_spatial),envelopers=sorted(seen_envelopers),
        note='Accelerated decoded replay; real analysis/GPU/swap/events and periodic readback. No audible playback, no dropped analysis chunks, not display FPS. Includes initialization and captures.')
    (output/'replay-performance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS Main replay:',json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('baseline',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--studio',action='store_true')
    parser.add_argument('--extended',action='store_true')
    parser.add_argument('--replay',action='store_true')
    args=parser.parse_args()
    if args.studio:studio_checks(args.output)
    elif args.extended:extended_checks(args.output)
    elif args.replay:replay_checks(args.output)
    else:gpu_checks(args.baseline,args.output)
