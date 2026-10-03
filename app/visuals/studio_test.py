"""Standalone studio session/lifecycle checks, plus real replay pacing on request."""
import json
from pathlib import Path
import tempfile
import time
from unittest.mock import patch
import tkinter as tk

from technique_library import entries, search, TECHNIQUES, SHADER, find_code
from studio import (Studio, DEFAULTS, LIVE_STATES, WORLD_TREE, command, validate_session,
                    ROOT, tracks, selection_states, path_for_state)
from replay_test import replay
from renderer import Renderer
import glfw
import numpy as np
from preview_layers import material_weights, material_quartet_profile, echo_weave_at, EFFECTS, BITS, layers_at, validate_layers, parse_layers, materials_at, material_trio_profile, WORLDS, daddy_long_legs_at, earth_details_at, fog_details_at, plasma_details_at


def planet_palette_studio_test():
    """Studio callbacks/session routing with real GPU draws; live input is controlled."""
    import runpy
    import sys
    from contextlib import ExitStack
    from preview_layers import MATERIALS
    from studio import SOURCES
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as temporary:
        folder = Path(temporary)
        # Existing version 1/2/3 files without the additive field remain Authored.
        for version in (1,2,3):
            old = dict(version=version,state='canvas',selection=['cosmic','canvas'])
            assert validate_session(old)['planet_palette'] == 'authored'
        for invalid in ('unknown',None,[],1):
            try: validate_session(dict(version=3,selection=['cosmic','canvas'],planet_palette=invalid))
            except ValueError: pass
            else: raise AssertionError(('invalid palette accepted',invalid))
        root = tk.Tk(); root.withdraw(); app = Studio(root)
        try:
            root.geometry('680x800'); root.deiconify()
            app.select(['cosmic','canvas'])
            assert str(app.palette_box['state']) == 'readonly'
            app.palette_choice.set('Soft Dream'); app.palette_box.event_generate('<<ComboboxSelected>>')
            root.update()
            assert app.values()['planet_palette'] == 'soft-dream'
            assert app.stop_button.winfo_y()+app.stop_button.winfo_height() <= app.preview.winfo_height()
            # Populate the existing material table using its normal Add action.
            app.sections.select(app.section_frames['Materials']);app.refresh_layers()
            app.effect_category.set('Material'); app.refresh_effect_picker()
            for key in MATERIALS:
                app.effect_choice.set(EFFECTS[key][0]); app.add_layer()
            for key in MATERIALS:
                app.layer_table.selection_set(key); app.edit_layer('solo')
                assert material_weights(app.layer_profiles,5,0.)[MATERIALS.index(key)] == 1.
                assert app.values()['planet_palette'] == 'soft-dream'
            for item in list(app.layer_profiles['cosmic']['items']):
                if not item['enabled']:
                    app.layer_table.selection_set(item['id']); app.edit_layer('toggle')
            app.layer_mode.set('Meld materials'); app.layer_hold.set('12'); app.change_layer_playback()
            for index in range(4):
                assert material_weights(app.layer_profiles,5,index*12.)[index] == 1.
            expected = validate_layers(app.layer_profiles)
            app.session_path = folder/'palette.json'; app.save(); app.new()
            assert app.values()['planet_palette'] == 'authored'
            with patch('studio.filedialog.askopenfilename',return_value=str(folder/'palette.json')): app.load()
            assert app.palette_choice.get() == 'Soft Dream' and app.values()['layers'] == expected
            # Changing palette never mutates material profiles or playback.
            app.palette_choice.set('Authored'); app.change_palette()
            assert app.values()['layers'] == expected
            app.palette_choice.set('Soft Dream'); app.change_palette()
            for selection in ([],['elements','water','sea']):
                app.select(selection); root.update()
                assert str(app.palette_box['state']) == 'disabled' and app.palette_choice.get() == 'Authored'
                assert '--palette' not in command(app.values(),folder)
                assert app.values()['layers'] == expected and 'blend' not in app.layer_profiles
            app.select(['cosmic','canvas'])
            assert app.palette_choice.get() == 'Soft Dream'
            # Legacy load also clears a previous opt-in choice.
            (folder/'legacy.json').write_text(json.dumps(dict(version=3,selection=['cosmic','canvas'])))
            with patch('studio.filedialog.askopenfilename',return_value=str(folder/'legacy.json')): app.load()
            assert app.palette_choice.get() == 'Authored'
            app.layer_profiles = expected
            app.vars['track'].set(str(tracks()[0])); app.vars['captures'].set(False)
            launch_values = app.values()
        finally: app.close()

        class ControlledCapture:
            def __init__(self, **kwargs): pass
            def find_device(self): return 'Controlled zero samples (no live audio review)'
            def start(self): pass
            def read(self, **kwargs): return np.zeros((2048,2),dtype=np.float32)
            def stop(self): pass

        # Use Studio's exact generated argv through each existing entry point.
        # Observe real renderer uniforms; bound preview length in the test only.
        for source in SOURCES:
            for palette in ('authored','soft-dream'):
                seen = []
                class ObservedRenderer(Renderer):
                    def __init__(self, *args, **kwargs):
                        kwargs.update(width=320,height=180,seed=2)
                        super().__init__(*args, **kwargs)
                    def create(self):
                        glfw.init(); glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
                        super().create()
                    def should_close(self): return len(seen) >= 5
                    def render(self, elapsed_time=None):
                        # Advance the existing material meld to each material and a blend.
                        seconds = (0.,12.,24.,36.,44.5)[len(seen)]
                        super().render(elapsed_time=seconds)
                        assert self.preview_palette == palette
                        assert self.program['u_planet_palette'].value == int(palette == 'soft-dream')
                        assert self.program['u_debug_state'].value == 5.
                        assert np.allclose(self.program['u_material_mix'].value,materials_at(expected,5,seconds))
                        assert abs(self.program['u_echo_weave'].value-echo_weave_at(expected,5,seconds)) < 1e-6
                        seen.append(seconds)
                values = dict(launch_values,source=source,planet_palette=palette)
                args = command(values,folder)
                script_index = next(i for i,a in enumerate(args) if a.endswith('.py'))
                with ExitStack() as stack:
                    stack.enter_context(patch('renderer.Renderer',ObservedRenderer))
                    stack.enter_context(patch.object(sys,'argv',args[script_index:]))
                    if source == 'Live system audio':
                        stack.enter_context(patch('capture.AudioCapture',ControlledCapture))
                    runpy.run_path(args[script_index],run_name='__main__')
                assert len(seen) == 5,(source,palette,seen)
        print('PASS: Studio palette UI, old/new sessions, four materials/meld, scope gating; all three Studio argv routes reached real GPU palette/material uniforms. Live audio used controlled samples.')


def galaxy_scene_studio_test():
    """Standalone Cosmic leaf, old sessions, colors and all Studio launch paths."""
    import runpy
    import sys
    from contextlib import ExitStack
    from color_controls import targets_for, validate_colors, family_setup, galaxy_authored_colors
    from preview_layers import STELLAR_LAYERS, stellar_layers_at
    from studio import SOURCES
    from renderer import LIVE_FORMS
    assert 36 in LIVE_FORMS
    assert selection_states(['cosmic']) == ['canvas']
    assert selection_states(['cosmic','galaxy']) == ['galaxy']
    assert path_for_state('galaxy') == ['cosmic','galaxy']
    assert {t.id for t in targets_for('galaxy')} == {'galaxy.structure','galaxy.system','stellar.sails','sky.stars'}
    assert {'galaxy.structure','galaxy.system'} <= {t.id for t in targets_for('blend')}
    assert {key for key,info in EFFECTS.items() if 'galaxy' in info[2]} == set(STELLAR_LAYERS)|{'gravity_well'}
    assert stellar_layers_at({},36,0.) == (1.,1.)
    assert stellar_layers_at({},0,0.) == (0.,0.)
    manual={'galaxy.structure':family_setup('galaxy.structure','Orchid Eclipse'),
            'stellar.sails':family_setup('stellar.sails','Copper Comet')}
    assert galaxy_authored_colors(manual,36)['galaxy.structure']==manual['galaxy.structure']
    assert 'galaxy.system' in galaxy_authored_colors(manual,36)
    assert galaxy_authored_colors(manual,36)['stellar.sails']==manual['stellar.sails']
    for version in (1,2,3):
        old = validate_session(dict(version=version, state='cosmic',
                                    selection=['cosmic']))
        assert old['selection'] == (['cosmic','canvas'] if version == 1 else ['cosmic'])
        assert old['state'] == 'canvas'
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as temporary:
        folder=Path(temporary)
        root=tk.Tk();root.withdraw();app=Studio(root)
        try:
            root.deiconify();root.update()
            app.select(['cosmic','galaxy'])
            assert app.values()['state']=='galaxy'
            assert str(app.palette_box['state'])=='disabled'
            assert app.layer_world()=='galaxy'
            app.color_overrides=validate_colors(manual)
            for seed in (7301,42,1337):
                app.review_galaxy(seed)
                assert app.values()['galaxy_seed']==str(seed)
                assert app.color_overrides==validate_colors(manual)
            app.review_galaxy()
            assert app.values()['galaxy_seed']=='1337'
            app.layer_profiles={'galaxy':dict(mode='together',seconds=18.,items=[
                dict(id='stellar_sails',enabled=True,amount=.65),
                dict(id='parallax_shoal',enabled=True,amount=.85)])}
            expected_layers=app.layer_profiles
            app.session_path=folder/'galaxy-session.json';app.save();app.new()
            with patch('studio.filedialog.askopenfilename',return_value=str(folder/'galaxy-session.json')):app.load()
            assert app.selection==['cosmic','galaxy']
            assert app.values()['color_overrides']==app.color_overrides
            assert app.layer_profiles==expected_layers
            assert 'stellar_sails' in app.layer_table.get_children()
            assert str(app.palette_box['state'])=='disabled'
            app.vars['track'].set(str(tracks()[0]));app.vars['captures'].set(False)
            values=app.values()
        finally:app.close()
        class ControlledCapture:
            def __init__(self,**kwargs):pass
            def find_device(self):return 'Controlled zero samples (no listening review)'
            def start(self):pass
            def read(self,**kwargs):return np.zeros((2048,2),dtype=np.float32)
            def stop(self):pass
        for source in SOURCES:
            seen=[]
            class ObservedRenderer(Renderer):
                def __init__(self,*args,**kwargs):
                    kwargs.update(width=320,height=180,seed=2)
                    super().__init__(*args,**kwargs)
                def create(self):
                    glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE)
                    super().create()
                def should_close(self):return len(seen)>=1
                def render(self,elapsed_time=None):
                    super().render(elapsed_time=elapsed_time)
                    assert self.program['u_debug_state'].value==36.
                    assert self.program['u_galaxy_colors_on'].value==1
                    assert np.allclose(self.program['u_stellar_layers'].value,(.65,.85))
                    assert self.program['u_stellar_sails_on'].value==1
                    seen.append(True)
            args=command(dict(values,source=source),folder)
            assert args[args.index('--state')+1]=='galaxy'
            assert '--palette' not in args
            assert args[args.index('--seed')+1]==values['galaxy_seed']
            script_index=next(i for i,arg in enumerate(args) if arg.endswith('.py'))
            with ExitStack() as stack:
                stack.enter_context(patch('renderer.Renderer',ObservedRenderer))
                stack.enter_context(patch.object(sys,'argv',args[script_index:]))
                if source=='Live system audio':
                    stack.enter_context(patch('capture.AudioCapture',ControlledCapture))
                runpy.run_path(args[script_index],run_name='__main__')
            assert seen,source
    print('PASS: standalone Galaxy Studio leaf/session/colors and synthetic, decoded, controlled-live GPU routes.')


def studio_comparison_test():
    """Real Studio children + decoded audio, and fixed GPU history/pixel checks."""
    import wave
    from copy import deepcopy
    from studio import (effect_section, preview_profiles, comparison_runs,
                        replay_identity, completed_comparison_run)
    from preview_layers import MATERIALS, default_profile
    from shader_test import save_png
    assert [effect_section(key) for key in MATERIALS] == ['Materials'] * 7
    assert effect_section('sparkles') == effect_section('tunnel') == effect_section('shooting_stars') == 'Shared FX'
    assert effect_section('daddy_long_legs') == effect_section('rings') == effect_section('water_rain') == 'World details'
    profile = dict(mode='cycle', seconds=4., items=[dict(id=key, enabled=enabled) for key, enabled in
        [('alloy', True), ('rings', True), ('tunnel', True), ('echo_weave', True), ('moons', False)]])
    values = dict(DEFAULTS, selection=['cosmic', 'canvas'], state='canvas', layers={'cosmic':profile})
    old = deepcopy(values)
    assert preview_profiles(values) == old['layers']
    for i, key in enumerate(('alloy', 'rings', 'tunnel', 'echo_weave')):
        assert layers_at(preview_profiles(values), 5, i*4.) == (1, BITS[key])
    values['material_isolation'] = {'cosmic':'echo_weave'}
    effective = preview_profiles(values)
    assert values['layers'] == old['layers']
    for second in (0.,4.,8.,12.,88.):
        assert material_weights(effective,5,second) == (0.,0.,0.,1.,0.,0.,0.)
        assert layers_at(effective,5,second)[1] == BITS['rings'] | BITS['tunnel']
    assert default_profile('blend')['mode'] == 'meld' and len(MATERIALS) == 7
    assert preview_profiles(dict(DEFAULTS)) == {} and layers_at({},5,0.) == (0,0)
    for invalid in (None, [], {'cosmic':'rings'}, {'unknown':'alloy'}):
        try: validate_session(dict(version=3, **dict(values,material_isolation=invalid)))
        except ValueError: pass
        else: raise AssertionError(invalid)
    assert validate_session(dict(version=3, **values))['material_isolation'] == values['material_isolation']
    output = ROOT/'work/studio-controls-check'/time.strftime('%Y%m%d-%H%M%S')
    output.mkdir(parents=True)
    # Decode is already done by the project; copy a bounded PCM segment for fast end-to-end tests.
    track = output/'two-second-decoded.wav'
    with wave.open(str(tracks()[0]),'rb') as source, wave.open(str(track),'wb') as target:
        target.setparams(source.getparams()); target.writeframes(source.readframes(96000))
    values.update(track=str(track), source='Test track')
    pair = comparison_runs(values)
    a, b = pair[0][1], pair[1][1]
    assert dict(a, planet_palette='soft-dream') == b and a['layers'] == effective
    assert a['duration'] == '30 seconds' and a['speed'] == 'Real time'
    assert values['layers'] == old['layers']
    for changes in (dict(source='Live system audio'), dict(source='Synthetic preview'),
                    dict(selection=[]), dict(material_isolation={})):
        try: comparison_runs(dict(values, **changes))
        except ValueError: pass
        else: raise AssertionError(changes)
    root = tk.Tk(); app = Studio(root)
    try:
        root.geometry('680x800'); app.select(values['selection']); app.layer_profiles = deepcopy(values['layers'])
        app.isolate_choice.set('Echo Weave'); app.isolate_material()
        assert app.material_isolation == {'cosmic':'echo_weave'}
        for key in DEFAULTS: app.vars[key].set(values[key])
        app.refresh_layers(); app.refresh_palette()
        for frame in app.section_frames.values():
            app.tabs.select(app.layers_tab); app.sections.select(frame); root.update()
            assert app.layer_table.winfo_height() >= 48
            assert app.footer.winfo_height() >= 32
            assert app.footer.winfo_y() + app.footer.winfo_height() <= root.winfo_height()
            for child in app.layers_tab.winfo_children():
                assert child.winfo_ismapped(), child
                assert child.winfo_y() + child.winfo_height() <= app.layers_tab.winfo_height(), (child, child.winfo_y(), child.winfo_height())
        app.select([]);app.sections.select(app.section_frames['Palettes']);root.update()
        for child in app.layers_tab.winfo_children():
            assert child.winfo_ismapped() and child.winfo_y()+child.winfo_height()<=app.layers_tab.winfo_height()
        app.open_color_inspector();editor=app.color_editor
        editor.target_choice.set('Moons and dust wakes');editor.refresh();root.update()
        assert editor.viewport.yview()[1]<1.
        editor.viewport.yview_moveto(1.);root.update()
        assert editor.viewport.yview()[1]==1.
        editor.close()
        app.select(values['selection']);app.refresh_palette()
        app.session_path = output/'session.json'; app.save(); saved = app.values()
        app.new()
        with patch('studio.filedialog.askopenfilename',return_value=str(output/'session.json')): app.load()
        assert app.values() == saved
        app.restore_materials(); assert app.layer_profiles == old['layers'] and not app.material_isolation
        app.isolate_material(); before = app.values()
        app.start_comparison(); assert app.process is not None
        destination = app.output
        deadline = time.monotonic()+90
        while app.process is not None and time.monotonic()<deadline:
            root.update(); time.sleep(.03)
        assert app.process is None, 'Matched children timed out'
        manifest = json.loads((destination/'comparison.json').read_text())
        assert manifest['status'] == 'matched complete', (manifest['status'], app.status.get())
        assert app.values() == before
        count = replay_identity(track)[1]
        completed_comparison_run(destination, 'B', count)
        try: completed_comparison_run(destination, 'A', count+1)
        except ValueError: pass
        else: raise AssertionError('Early exit accepted')
        # Cancellation cannot automatically launch B.
        app.start_comparison(); cancelled = app.output; app.stop(); root.update()
        assert not app.comparison_queue and app.process is None
        assert json.loads((cancelled/'comparison.json').read_text())['status'] == 'cancelled'
        assert not (cancelled/'B').exists()
    finally: app.close()
    # Same fixed input/time/camera, fresh renderer every time, including zeroed Echo history.
    images, histories, clocks = [], [], []
    for index, palette in enumerate(('authored','authored','soft-dream')):
        renderer = Renderer(width=320,height=180,seed=7301)
        try:
            glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE); renderer.create()
            renderer.debug_state=5; renderer.layer_profiles=effective; renderer.preview_palette=palette
            assert renderer.echo_resources is None and renderer.last_render_time is None
            for frame in range(61):
                renderer.parameters.scale=.45;renderer.parameters.movement=.45
                renderer.parameters.flux=.45;renderer.parameters.sparkle=.25
                renderer.render(elapsed_time=frame/60.)
            histories.append(renderer.echo_resources[0][0].read())
            clocks.append((renderer.flow_time,renderer.star_time,renderer.echo_clock))
            pixels=np.frombuffer(renderer.ctx.screen.read(components=3,alignment=1),dtype=np.uint8).reshape(180,320,3)
            images.append(pixels.copy()); save_png(output/f'{index}-{palette}.png',pixels[::-1])
            assert renderer.program['u_planet_palette'].value == int(palette=='soft-dream')
        finally: renderer.close()
    assert np.array_equal(images[0],images[1]), 'Fresh Authored runs must agree pixel-for-pixel'
    assert histories[0] == histories[1] == histories[2] and clocks[0] == clocks[1] == clocks[2]
    assert np.abs(images[0].astype(float)-images[2]).mean() > .1, 'Palette must reach pixels'
    print('PASS: categories, mixed order, isolation/restore/session, unchanged defaults, real sequential A/B children, cancellation/early-exit rejection, identical decoded metrics and Echo histories; Authored repeat pixels equal. Evidence:',output)


def roots_colors_studio_test():
    import os
    import runpy
    import sys
    import wave
    from copy import deepcopy
    from contextlib import ExitStack
    from color_controls import (TARGETS, validate_colors, resolved_slots, color_preset, validate_preset)
    from studio_color_link import ColorInbox, MAX_MESSAGE
    assert len({target.id for target in TARGETS}) == len(TARGETS) and len(TARGETS)>=14
    assert len({target.label for target in TARGETS})==len(TARGETS)
    assert [len(target.slots) for target in TARGETS[:7]] == [5,5,1,1,5,5,1]
    authored=deepcopy(TARGETS)
    sample={'roots.blossoms':{'tint':{'color':'#12abEF'}},
            'roots.blue':{'electric':{'color':'#CC3322','start':.32,'end':.62}}}
    clean=validate_colors(sample)
    assert clean['roots.blossoms']['tint']['color']=='#12ABEF'
    assert resolved_slots(TARGETS[0],{})[0][0]==(.004,.006,.016)
    for invalid in (None,[],{'bogus':{}},{'roots.blossoms':{'glow':{'color':'#FFFFFF'}}},
                    {'roots.blossoms':{'tint':{'color':'red'}}},
                    {'roots.blossoms':{'tint':{'color':[1,0,0]}}},
                    {'roots.blue':{'deep':{'start':.1}}},
                    {'roots.blue':{'electric':{'start':float('nan')}}},
                    {'roots.blue':{'electric':{'start':True}}},
                    {'roots.blue':{'electric':{'start':.7,'end':.3}}},
                    {'roots.blue':{'electric':{'end':.99}}}):
        try:validate_colors(invalid)
        except ValueError:pass
        else:raise AssertionError(invalid)
    preset=color_preset('Warm blossoms','roots',clean)
    assert validate_preset(preset)==preset
    for invalid in ({},dict(preset,kind='palette'),dict(preset,scene='water')):
        try:validate_preset(invalid)
        except ValueError:pass
        else:raise AssertionError(invalid)
    assert TARGETS==authored
    full={target.id:{slot.id:{'color':'#FF1010'} for slot in target.slots} for target in TARGETS}
    assert validate_colors(full)==full
    assert len((json.dumps(dict(kind='colors',revision=1,targets=full),separators=(',',':'))+'\n').encode())<=MAX_MESSAGE
    assert len(json.dumps(color_preset('Full rollout','blend',full),indent=2).encode())<=32768
    # Real bounded OS pipe: partial framing, latest-wins, malformed/oversize and stale revisions.
    read_fd,write_fd=os.pipe();inbox=ColorInbox(read_fd)
    def wait_for(predicate, timeout=5):
        deadline=time.monotonic()+timeout
        while not predicate() and time.monotonic()<deadline:time.sleep(.01)
        assert predicate(),'Timed out'
    try:
        payload=json.dumps(dict(kind='colors',revision=1,targets=clean)).encode()+b'\n'
        os.write(write_fd,payload[:20]);time.sleep(.03);assert inbox.take() is None
        os.write(write_fd,payload[20:]);wait_for(lambda:inbox.revision==1)
        assert inbox.take()==(1,clean)
        os.write(write_fd,b'x'*(MAX_MESSAGE+1)+b'\n')
        os.write(write_fd,json.dumps(dict(kind='colors',revision=2,targets={'bad':{}})).encode()+b'\n')
        os.write(write_fd,json.dumps(dict(kind='colors',revision=3,targets={})).encode()+b'\n')
        wait_for(lambda:inbox.revision==3);assert inbox.take()==(3,{})
        os.write(write_fd,payload);time.sleep(.03);assert inbox.take() is None
    finally:
        inbox.close();os.close(write_fd);inbox.thread.join(1);os.close(read_fd)
    output=ROOT/'work/roots-color-studio-check'/time.strftime('%Y%m%d-%H%M%S');output.mkdir(parents=True)
    root=tk.Tk();root.withdraw();app=Studio(root)
    try:
        app.select(['organic','roots']);app.open_color_inspector();editor=app.color_editor
        root.update();assert editor.rows.keys()=={'deep','cobalt','electric','cyan','pale'}
        editor.target_choice.set('Blossoms');editor.refresh()
        editor.rows['tint'][0].set('#00FF88');editor.edit_hex('tint')
        assert app.color_overrides=={'roots.blossoms':{'tint':{'color':'#00FF88'}}}
        editor.rows['tint'][0].set('invalid');editor.edit_hex('tint')
        assert app.color_overrides['roots.blossoms']['tint']['color']=='#00FF88'
        editor.reset_target();assert app.color_overrides=={}
        app.set_color_setup(clean);editor.refresh()
        with patch('color_inspector.simpledialog.askstring',return_value='Warm blossoms'), patch(
                'color_inspector.filedialog.asksaveasfilename',return_value=str(output/'look.json')):
            editor.save_preset()
        preset_bytes=(output/'look.json').read_bytes()
        editor.reset_scene();assert app.color_overrides=={}
        with patch('color_inspector.filedialog.askopenfilename',return_value=str(output/'look.json')):editor.load_preset()
        assert app.color_overrides==clean and (output/'look.json').read_bytes()==preset_bytes
        app.session_path=output/'session.json';app.save();app.new()
        assert app.color_overrides=={}
        with patch('studio.filedialog.askopenfilename',return_value=str(output/'session.json')):app.load()
        assert app.color_overrides==clean
        for version in (1,2,3):
            legacy=validate_session(dict(version=version,state='roots',selection=['organic','roots']))
            assert 'color_overrides' not in legacy
        for selection in ([],['cosmic','canvas'],['organic'],['organic','membrane'],['elements']):
            app.select(selection);assert '--colors' in command(app.values(),output)
            assert app.color_overrides==clean
            sent=json.loads(command(app.values(),output)[command(app.values(),output).index('--colors')+1])
            assert ('roots.blossoms' in sent)==(selection in ([],['organic'],['elements']))
        app.select(['elements']);assert app.color_scene()=='blend'
        sequence=command(dict(app.values(),color_overrides=full),output)
        assert '--states' in sequence and len(' '.join(sequence))<32767
        app.select(['organic','roots']);assert '--colors' in command(app.values(),output)
        app.layer_profiles={'organic':dict(mode='together',seconds=12.,items=[dict(id=key,enabled=True) for key in ('echo_weave','blossoms')])}
        app.vars['source'].set('Synthetic preview');app.start()
        pid=app.process.pid;link=app.color_link
        def pump_until(predicate,timeout=45):
            deadline=time.monotonic()+timeout
            while not predicate() and time.monotonic()<deadline:
                root.update();time.sleep(.02)
            assert predicate(),app.status.get()+' / '+app.color_status.get()
        pump_until(lambda:app.color_link and app.color_link.get_status().get('applied')==1)
        first=link.get_status()
        for index in range(100):app.set_color_setup({'roots.blossoms':{'tint':{'color':f'#{index:02X}44FF'}}})
        pump_until(lambda:link.get_status().get('applied')==2)
        second=link.get_status()
        assert app.process.pid==pid and second['seconds']>first['seconds'] and second['echo_clock']>=first['echo_clock']
        assert link.revision==2, 'Rapid Tk edits must coalesce'
        editor.revert();assert app.color_overrides==clean
        pump_until(lambda:link.get_status().get('applied')==3)
        deadline=time.monotonic()+.6
        while time.monotonic()<deadline:
            app.set_color_setup(clean);root.update();time.sleep(.01)
        assert link.revision>=6, 'Continuous dragging must deliver during the gesture'
        pump_until(lambda:link.get_status().get('applied')==link.revision and app.color_send_after is None)
        app.stop();assert not link.writer.is_alive() and not link.reader.is_alive()
        assert app.color_send_after is None and app.color_link is None
        # Natural EOF exercises reader cleanup and restarting with the current saved setup.
        track=output/'four-second-decoded.wav'
        with wave.open(str(tracks()[0]),'rb') as src, wave.open(str(track),'wb') as dst:
            dst.setparams(src.getparams());dst.writeframes(src.readframes(4*48000))
        app.vars['source'].set('Test track');app.vars['track'].set(str(track));app.vars['speed'].set('Real time')
        app.start();replay_folder=app.output;link=app.color_link
        pump_until(lambda:link.get_status().get('applied')==1)
        app.set_color_setup({'roots.ridge':{'tint':{'color':'#FFCC00'}}})
        pump_until(lambda:link.get_status().get('applied')==2)
        pump_until(lambda:app.process is None)
        assert not link.reader.is_alive() and not link.writer.is_alive()
        assert (replay_folder/'metrics.csv').is_file()
        app.select([]);app.vars['source'].set('Synthetic preview')
        app.set_color_setup({'air.sky':{'sky':{'color':'#BB4422'}}})
        app.open_color_inspector();assert app.color_editor.scene=='blend'
        for target in app.color_editor.targets:
            app.color_editor.target_choice.set(target.label);app.color_editor.refresh()
            assert len(app.color_editor.rows)==len(target.slots)
        with patch('color_inspector.filedialog.askopenfilename',return_value=str(output/'look.json')):
            app.color_editor.load_preset()
        assert 'air.sky' in app.color_overrides and 'roots.blossoms' in app.color_overrides
        app.start();main_pid=app.process.pid;main_link=app.color_link
        assert app.active_color_scene=='blend'
        pump_until(lambda:main_link.get_status().get('applied')==1)
        app.set_color_setup({'air.sky':{'sky':{'color':'#BB4422'}}})
        pump_until(lambda:main_link.get_status().get('applied')==2)
        assert app.process.pid==main_pid and app.process.poll() is None
        app.stop();assert not main_link.writer.is_alive() and not main_link.reader.is_alive()
        app.select(['organic','roots'])
        values=app.values()
        values.update(source='Live system audio',color_overrides=clean)
    finally:app.close()
    # Existing live path + real GPU; controlled samples explicitly are not live listening.
    read_fd,write_fd=os.pipe(); seen=[]
    class Stdin:
        def fileno(self):return read_fd
    class ControlledCapture:
        def __init__(self,**kwargs):self.count=0
        def find_device(self):return 'Controlled samples for live color routing'
        def start(self):pass
        def stop(self):pass
        def read(self,**kwargs):
            self.count+=1
            if self.count==2:os.write(write_fd,json.dumps(dict(kind='colors',revision=1,targets={'roots.ridge':{'tint':{'color':'#CC5522'}}})).encode()+b'\n')
            time.sleep(.03)
            return np.zeros((2048,2),dtype=np.float32)
    class ObservedRenderer(Renderer):
        def __init__(self,*args,**kwargs):super().__init__(width=320,height=180,seed=2)
        def create(self):glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);super().create()
        def should_close(self):return len(seen)>=6
        def render(self,elapsed_time=None):
            super().render(elapsed_time)
            seen.append((self.program['u_roots_ridge_on'].value,self.program['u_roots_ridge'].value,self.last_render_time))
    args=command(values,output)+['--studio-color-input','--quiet'];offset=next(i for i,a in enumerate(args) if a.endswith('.py'))
    try:
        with ExitStack() as stack:
            stack.enter_context(patch('renderer.Renderer',ObservedRenderer))
            stack.enter_context(patch('capture.AudioCapture',ControlledCapture))
            stack.enter_context(patch.object(sys,'stdin',Stdin()))
            stack.enter_context(patch.object(sys,'argv',args[offset:]))
            runpy.run_path(args[offset],run_name='__main__')
        assert seen[0][0]==0 and seen[-1][0]==1 and seen[-1][2]>seen[0][2]
        assert np.allclose(seen[-1][1],(204/255,85/255,34/255))
    finally:os.close(write_fd);os.close(read_fd)
    print('PASS: declared colors/gradients, bounded pipe framing/rejection, generated inspector, resets/revert/presets/sessions, coalesced live updates, synthetic + decoded child restart/EOF, real GPU controlled-live routing. Evidence:',output)


def studio_organization_test():
    """Offline selector/session/callback contract; withdrawn Tk, no child/device/GPU."""
    from copy import deepcopy
    from contextlib import ExitStack
    import runpy
    from renderer import LIVE_FORMS
    from studio import STUDIO_TREES, session_states, selection_scope
    from world_catalog import studio_trees
    from color_controls import family_setup

    def leaves(tree, path=()):
        result = {}
        for key, node in tree.items():
            here = (*path, key)
            if 'children' in node:
                assert node['children'], ('Empty category', here)
                result.update(leaves(node['children'], here))
            else:
                result[here] = LIVE_STATES[node['state']]
        return result

    original = deepcopy(WORLD_TREE)
    full_ids = [row['id'] for row in entries(WORLD_TREE)]
    main_forms = leaves(STUDIO_TREES['main'])
    experimental_forms = leaves(STUDIO_TREES['experimental'])
    assert len(main_forms) == len(LIVE_FORMS) == 27
    assert set(main_forms.values()) == set(LIVE_FORMS) and 36 in main_forms.values()
    assert set(experimental_forms.values()) == {4, 37, 38, 39, 40}
    assert not set(main_forms.values()) & set(experimental_forms.values())
    assert {**main_forms, **experimental_forms} == leaves(WORLD_TREE)
    assert list(STUDIO_TREES['main']) == ['organic', 'geometric', 'cosmic', 'elements']
    assert list(STUDIO_TREES['experimental']) == ['cymatics', 'experimental']
    assert 'world:cymatics/water' in full_ids and 'world:experimental/lodestone' in full_ids
    # Approval belongs to leaves; an approved family cannot leak a new variant
    # through either its selectors or the pre-existing authored cycle.
    fixture = deepcopy(WORLD_TREE)
    fixture['organic']['children']['unapproved_variant'] = dict(label='Future variant', state='cymatics')
    fixture['unused_category'] = dict(label='Unused', children={
        'nested': dict(label='Nested', children={'study': dict(label='Study', state='transition')})})
    fixture['empty_category'] = dict(label='Empty', children={})
    projected = studio_trees(LIVE_FORMS, fixture)
    assert 'unapproved_variant' not in projected['main']['organic']['children']
    assert 'cycle' not in projected['main']['organic']
    assert 'unused_category' not in projected['main']
    assert 'empty_category' not in projected['main'] and 'empty_category' not in projected['experimental']
    assert selection_states(['organic'], projected['main']) == ['membrane', 'roots']
    assert 'unapproved_variant' in projected['experimental']['organic']['children']
    assert fixture['organic']['cycle'] == 'organic'
    assert WORLD_TREE == original and entries(WORLD_TREE) == entries(original)
    baseline = ROOT/'work/studio-organization-01/baseline/app/visuals/world_catalog.py'
    if baseline.is_file():
        baseline_tree = runpy.run_path(str(baseline))['WORLD_TREE']
        assert original == baseline_tree
        assert full_ids == [row['id'] for row in entries(baseline_tree)]

    settings = __import__('cymatics_session').defaults()
    settings['oscillator'].update(frequency=5.7, amplitude=.3, waveform='triangle', sweep_end=7.2, sweep_seconds=12.)
    settings.update(material='ink', finish='marble', dye_strength=.43,
                    camera_orbit=False, light_angle=.2, dye_swirl=.37)
    settings['basin'].update(width=.12, length=.09, depth=.007, damping=.45, optical_gain=85.)
    settings['bands']['gain'] = 1.3
    colors = {'cymatics.water': family_setup('cymatics.water', 'Obsidian Light'),
              'roots.blossoms': {'tint': {'color': '#00FF88'}}}
    profile = {'plasma': dict(mode='together', seconds=13., items=[dict(id='plasma_field', enabled=True)])}
    legacy_count = 0
    for path, state_id in {**main_forms, **experimental_forms}.items():
        state = next(name for name, number in LIVE_STATES.items() if number == state_id)
        for version in (1, 2, 3):
            data = dict(version=version, selection=list(path), state=state, source='Synthetic preview',
                        cymatics=settings, color_overrides=colors, layers=profile,
                        planet_palette='soft-dream', galaxy_seed='42')
            clean = validate_session(data)
            assert clean['selection'] == (path_for_state(state) if version == 1 else list(path))
            assert LIVE_STATES[clean['state']] == state_id
            assert clean['selection_scope'] == ('main' if state_id in LIVE_FORMS else 'experimental')
            assert clean['cymatics'] == __import__('cymatics_session').validate(settings, stored=True)
            assert clean['color_overrides'] == colors
            assert validate_session(dict(version=3, **clean)) == clean
            argv = command(clean, ROOT/'work/studio-organization-01')
            if state_id == 37:
                assert any(arg.endswith('cymatics_preview.py') for arg in argv)
                assert json.loads(argv[argv.index('--config')+1]) == clean['cymatics']
            else:
                assert argv[argv.index('--state')+1] == state
            legacy_count += 1
    for old in (dict(version=1, state='transition'), dict(version=3, selection=['transition'])):
        assert validate_session(old)['selection'] == ['experimental', 'transition_study']
    assert validate_session(dict(version=3, selection=['cymatics', 'water'],
                                 selection_scope='cymatics'))['selection_scope'] == 'experimental'
    muted = deepcopy(settings)
    muted.update(monitor=True, paused=True, restart=4, dye_reset=2, view_reset=3)
    stored = validate_session(dict(version=3, selection=['cymatics', 'water'], cymatics=muted))['cymatics']
    assert not stored['monitor'] and not stored['paused']
    assert stored['restart'] == stored['dye_reset'] == stored['view_reset'] == 0
    try:
        validate_session(dict(version=3, selection=['cymatics', 'missing']))
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid saved visual must fail, never become the first Main world')

    # Guard every device/renderer/child entry even though this test never starts
    # a real preview. Tcl widgets remain withdrawn for the whole check.
    with ExitStack() as guards, tempfile.TemporaryDirectory(dir=ROOT/'work') as temporary:
        for target in ('renderer.Renderer.create', 'capture.AudioCapture.__init__',
                       'oscillator.Monitor.__init__', 'studio.subprocess.Popen'):
            guards.enter_context(patch(target, side_effect=AssertionError('Offline check attempted '+target)))
        guards.enter_context(patch('studio.messagebox.showerror', side_effect=AssertionError))
        folder = Path(temporary)
        root = tk.Tk(); root.withdraw(); app = Studio(root)
        try:
            root.update()
            assert root.state() == 'withdrawn'
            assert app.tabs.tab(app.cymatics_tab, 'text') == 'Experimental'
            assert [app.tabs.tab(tab, 'text') for tab in app.tabs.tabs()].count('Experimental') == 1
            assert 'Cymatics' not in [app.tabs.tab(tab, 'text') for tab in app.tabs.tabs()]
            assert set(app.selector_rows[0][1]['values']) == {'', 'Organic', 'Geometric', 'Cosmic', 'Elements'}
            assert set(app.experimental_selector_rows[0][1]['values']) == {'Cymatics', 'Experimental / unfinished'}
            assert [app.cymatics_panel.pages.tab(tab, 'text') for tab in app.cymatics_panel.pages.tabs()] == ['Drive', 'Water basin', 'Style & bands']
            assert {'frequency', 'amplitude', 'waveform', 'edges', 'damping', 'camera_orbit', 'dye', 'monitor'} <= set(app.cymatics_panel.vars)
            app.cymatics_panel.set(settings)
            app.color_overrides = deepcopy(colors); app.layer_profiles = deepcopy(profile)
            # Rebuilding/populating/Library search must leave the project intact.
            before = deepcopy(app.values())
            with patch.object(app, 'select', side_effect=AssertionError('Population fired selection callback')):
                app.rebuild_selectors(); app.refresh_library(); root.update()
            assert app.values() == before
            assert [row['id'] for row in app.library_rows] == full_ids
            assert set(app.library_list.get_children()) == set(full_ids)

            for path in main_forms:
                app.select(list(path)); root.update()
                assert app.selection == list(path) and app.selection_scope == 'main'
                assert app.tabs.select() == str(app.preview)
            remembered_main = deepcopy(app.studio_selections['main'])
            for path in experimental_forms:
                app.library_list.selection_set('world:'+'/'.join(path))
                app.choose_library_world(); root.update()
                assert app.selection == list(path) and app.selection_scope == 'experimental'
                assert app.tabs.select() == str(app.cymatics_tab)
                assert app.studio_selections['main'] == remembered_main
                assert app.values()['layers'] == profile and app.values()['color_overrides'] == colors
            app.select(['cymatics', 'water']); root.update()
            assert app.cymatics_tools.winfo_manager() == 'pack'
            assert str(app.experimental_inputs['source']['state']) == 'disabled'
            assert str(app.source_box['state']) == 'readonly'
            app.select(['experimental', 'lodestone']); root.update()
            assert app.cymatics_tools.winfo_manager() == ''
            assert str(app.experimental_inputs['source']['state']) == 'readonly'
            # Actual combobox callbacks and actual notebook events restore each
            # view independently; shared settings/colors/layers remain parked.
            value, box, changed = app.experimental_selector_rows[1]
            value.set('Stormglass Network (Experimental)'); changed(); root.update()
            experimental_path = ['experimental', 'stormglass']
            assert app.selection == experimental_path
            app.tabs.select(app.preview); root.update()
            assert app.selection == remembered_main
            value, box, changed = app.selector_rows[0]
            value.set('Organic'); changed(); root.update()
            assert app.selection == ['organic']
            assert app.studio_selections['experimental'] == experimental_path
            app.tabs.select(app.cymatics_tab); root.update()
            assert app.selection == experimental_path
            assert app.values()['cymatics'] == before['cymatics']
            assert app.values()['layers'] == profile and app.values()['color_overrides'] == colors
            assert app.process is None and app.color_link is None
            # Preview buttons use their own active selection. Mock launch only,
            # inspect exact existing runner commands without starting a child.
            for path in (['cosmic', 'galaxy'], experimental_path, ['cymatics', 'water']):
                app.select(path); root.update()
                with patch.object(app, 'launch') as launch:
                    button = app.start_button if app.selection_scope == 'main' else app.experimental_start_button
                    button.invoke()
                    launched = launch.call_args.args[0]
                    assert launched['selection'] == path
                    assert session_states(launched) == app.selected_states()
                    command(launched, folder)
            app.select(['cymatics', 'water']); root.update()
            with patch('studio.subprocess.Popen') as child, patch('studio.ColorLink') as link:
                link.return_value.submit.return_value = 1
                link.return_value.get_status.return_value = {}
                app.start()
                assert any(arg.endswith('cymatics_preview.py') for arg in child.call_args.args[0])
                assert str(app.start_button['state']) == str(app.experimental_start_button['state']) == 'disabled'
                assert str(app.stop_button['state']) == str(app.experimental_stop_button['state']) == 'normal'
                log = app.log
                link.return_value.close.side_effect = log.close
                app.tabs.select(app.preview); root.update()
                assert app.active_color_scene == 'cymatics' and child.call_count == 1
                app.start(); assert child.call_count == 1  # only one owned preview
                app.finish()
                assert str(app.start_button['state']) == str(app.experimental_start_button['state']) == 'normal'
                assert str(app.stop_button['state']) == str(app.experimental_stop_button['state']) == 'disabled'
            for path in ([], ['cosmic', 'galaxy'], experimental_path, ['cymatics', 'water']):
                app.select(path); root.update()
                expected = deepcopy(app.values())
                app.session_path = folder/'saved.json'; app.save()
                frozen = app.session_path.read_bytes()
                app.new(); root.update()
                with patch('studio.filedialog.askopenfilename', return_value=str(folder/'saved.json')):
                    app.load()
                root.update()
                assert app.values() == expected
                assert (folder/'saved.json').read_bytes() == frozen
                assert app.tabs.select() == str(app.preview if selection_scope(path) == 'main' else app.cymatics_tab)
            invalid = folder/'invalid.json'
            invalid.write_text(json.dumps(dict(version=3, selection=['cymatics', 'missing'])))
            frozen = invalid.read_bytes(); before_invalid = deepcopy(app.values())
            with patch('studio.filedialog.askopenfilename', return_value=str(invalid)), patch('studio.messagebox.showerror') as error:
                app.load()
            assert error.call_count == 1 and app.values() == before_invalid and invalid.read_bytes() == frozen
            # Legacy load routes the original visual/settings without rewriting.
            for version in (1, 2, 3):
                for path, state in ((['cymatics', 'water'], 'cymatics'),
                                    (experimental_path, 'stormglass_experimental'),
                                    (['cosmic', 'galaxy'], 'galaxy')):
                    file = folder/'legacy.json'
                    file.write_text(json.dumps(dict(version=version, selection=path, state=state,
                                                   cymatics=settings, color_overrides=colors, layers=profile)))
                    frozen = file.read_bytes()
                    with patch('studio.filedialog.askopenfilename', return_value=str(file)): app.load()
                    root.update()
                    assert app.selection == path and app.selected_states() == [state]
                    assert app.values()['cymatics'] == before['cymatics'] and file.read_bytes() == frozen
                    assert app.tabs.select() == str(app.preview if state == 'galaxy' else app.cymatics_tab)
            assert WORLD_TREE == original and entries(WORLD_TREE) == entries(original)
            assert root.state() == 'withdrawn'
        finally:
            app.close()
    print(f'PASS: Main 27 incl Galaxy; Experimental 5 forms + all Cymatics tools; Library {len(full_ids)} unchanged IDs; '
          f'{legacy_count} legacy validations, saved Main/Experimental/Cymatics roundtrips, independent selectors, '
          'callbacks/population and mocked preview routing. Withdrawn Tk; no child/GPU/audio/device access.')


def main():
    found = find_code('water_current')
    assert any(r['symbol'] == 'water_current' and r['language'] == 'GLSL' for r in found)
    assert any(r['symbol'] == 'water_surface' for r in found)  # finds use, not only definition
    assert any(r['symbol'] == 'Renderer.choose_world' for r in find_code('choose_world'))
    for row in found:
        assert row['symbol'] in (ROOT / row['path']).read_text(encoding='utf-8').splitlines()[row['line'] - 1]
    quartet={'blend':material_quartet_profile('blend')}
    for t in np.linspace(0.,300.,1001):
        weights=np.array(material_weights(quartet,0,t))
        assert abs(weights.sum()-1.)<1e-10 and weights.min()>=0.
        assert np.abs(weights-np.array(material_weights(quartet,0,t+.0001))).max()<.001
    assert material_weights(quartet,0,108.)==(0.,0.,0.,1.,0.,0.,0.)
    assert echo_weave_at({'blend':material_trio_profile('blend')},0,108.)==0.
    assert echo_weave_at({},0,66.)==1.
    director=Renderer(seed=2)
    director.parameters.beat_confidence=.9
    director.parameters.scale=.6;director.parameters.movement=.6
    director.update_blend(0.,0.)
    director.director_min_hold=1.;director.director_max_hold=1.
    director.update_blend(2.,2.)
    assert director.director_pending is not None and director.director_target is None
    director.parameters.beat_tick=True;director.update_blend(2.1,.1)
    assert director.director_target is not None and director.director_pending is None
    director=Renderer(seed=2);director.parameters.beat_confidence=.9
    director.update_blend(0.,0.);director.director_min_hold=1.;director.director_max_hold=1.
    director.update_blend(2.,2.);director.update_blend(3.,1.)
    assert director.director_target is not None  # deadline cannot freeze a show
    catalog = entries(WORLD_TREE)
    assert len({row['id'] for row in catalog}) == len(catalog)
    assert {row['id'][7:] for row in catalog if row['id'].startswith('effect:')} == set(EFFECTS)
    for row in catalog:
        if 'selection' in row: selection_states(row['selection'])
        for location in row['sources']: assert (ROOT / location.split(':')[0]).is_file(), location
    shader = (ROOT / SHADER).read_text(encoding='utf-8')
    for _, _, symbol in TECHNIQUES: assert symbol + '(' in shader
    assert search(catalog, 'STAR continuous', 'Techniques')
    assert not search(catalog, 'no-such-entry-xyz')
    assert all(row['kind'] == 'Experiments' for row in search(catalog, '', 'Experiments'))

    assert daddy_long_legs_at({},21,0.)==0.
    assert BITS['air_citadel']==1<<30 and BITS['daddy_long_legs']==0
    assert sum(BITS.values())==2147483647
    assert all(item['id']!='daddy_long_legs' for world in WORLDS
        for item in material_trio_profile(world)['items'])
    experiments=validate_layers({'air':dict(mode='cycle',seconds=4.,items=[
        dict(id='artifacts',enabled=True),dict(id='daddy_long_legs',enabled=True)])})
    assert daddy_long_legs_at(experiments,21,0.)==0.
    assert daddy_long_legs_at(experiments,21,4.)==1.
    assert layers_at(experiments,21,4.)==(1,0)
    assert validate_session(dict(version=3,**dict(DEFAULTS,selection=['elements','air','vortex'],layers=experiments)))['layers']==experiments
    available=tracks()
    assert available, 'Decoded project tracks missing'
    values=dict(DEFAULTS,track=str(available[0]))
    migrated=validate_session(dict(version=1,**values))
    assert migrated==dict(values,selection=['elements','water'],layers={})
    assert validate_session(dict(version=2,**migrated))==migrated
    assert validate_session(dict(version=3,**migrated))==migrated
    profile=dict(mode='cycle',seconds=4.,items=[dict(id='artifacts',enabled=True),
        dict(id='flecks',enabled=False),dict(id='fractal',enabled=True)])
    profiles=validate_layers({'geometric':profile})
    for seconds,mask in ((0,1),(3.99,1),(4,32),(7.99,32),(8,1)):
        assert layers_at(profiles,2,seconds)==(1,mask)
        assert layers_at(profiles,5,seconds)==(0,0)
    for invalid in ({'unknown':profile},{'geometric':dict(profile,mode='bogus')},
                    {'geometric':dict(profile,seconds=float('nan'))},
                    {'geometric':dict(profile,seconds=True)},
                    {'elements':profile}, {'geometric':dict(profile,items=profile['items']*2)},
                    {'geometric':dict(profile,items=[dict(id='artifacts',enabled='false')])}):
        try:validate_layers(invalid)
        except ValueError:pass
        else:raise AssertionError(invalid)
    trio=validate_layers({world:material_trio_profile(world) for world in WORLDS})
    for state in range(36):
        assert layers_at(trio,state,23.)[0]==2
        a=np.array(materials_at(trio,state,35.999))
        b=np.array(materials_at(trio,state,36.001))
        assert np.abs(a-b).max()<.001 and abs(a.sum()-1.)<1e-10
        assert materials_at(trio,state,0.)==(1.,0.,0.)
        assert materials_at(trio,state,36.)==(0.,1.,0.)
        assert materials_at(trio,state,72.)==(0.,0.,1.)
        assert materials_at(trio,state,108.)==(1.,0.,0.)
    reversed_profile=material_trio_profile('water')
    reversed_profile['items'].reverse()
    assert materials_at({'water':reversed_profile},7,0.)==(0.,0.,1.)
    assert layers_at(trio,9,20.)[1]&BITS['water_rain']
    assert layers_at(trio,9,28.)[1]&BITS['water_rain']
    assert selection_states(['elements'])==['magnetic','arcs','auroral','nebula','marsh','pressure','dunes','strata','cavern','windstreams','stormfront','vortex','citadel','sea','dyes','rain','waterfall','currents','fire','molten','firescape','aftershock']
    assert selection_states(['elements','fog'])==['fog']
    assert selection_states(['elements','plasma'])==['plasma']
    assert selection_states(['elements','plasma','arcs'])==['arcs']
    assert plasma_details_at({},32,0.)==(1.,1.,1.)
    plasma_layers=validate_layers({'plasma':dict(mode='cycle',seconds=4.,items=[dict(id='plasma_field',enabled=True),dict(id='plasma_arcs',enabled=True)])})
    assert plasma_details_at(plasma_layers,33,0.)==(1.,0.,0.)
    assert plasma_details_at(plasma_layers,33,4.)==(0.,1.,0.)
    assert validate_session(dict(version=3,**dict(DEFAULTS,selection=['elements','plasma','arcs'],layers=plasma_layers)))['layers']==plasma_layers
    assert selection_states(['elements','fog','marsh'])==['marsh']
    assert fog_details_at({},29,0.)==(1.,1.,1.)
    fog_layers=validate_layers({'fog':dict(mode='cycle',seconds=4.,items=[dict(id='fog_volume',enabled=True),dict(id='fog_lights',enabled=True)])})
    assert fog_details_at(fog_layers,29,0.)==(1.,0.,0.)
    assert fog_details_at(fog_layers,29,4.)==(0.,1.,0.)
    assert validate_session(dict(version=3,**dict(DEFAULTS,selection=['elements','fog','marsh'],layers=fog_layers)))['layers']==fog_layers
    assert selection_states(['elements','earth'])==['earth']
    assert selection_states(['elements','earth','strata'])==['strata']
    assert earth_details_at({},24,0.)==(1.,1.,1.,1.)
    worm_only=validate_layers({'earth':dict(mode='together',seconds=4.,items=[dict(id='earth_worm',enabled=True)])})
    assert earth_details_at(worm_only,24,0.)==(0.,0.,0.,1.)
    assert earth_details_at(trio,24,0.)==(1.,1.,1.,1.)
    earth_layers=validate_layers({'earth':dict(mode='cycle',seconds=4.,items=[dict(id='earth_veins',enabled=True),dict(id='earth_dust',enabled=True)])})
    assert earth_details_at(earth_layers,24,0.)==(0.,1.,0.,0.)
    assert earth_details_at(earth_layers,24,4.)==(0.,0.,1.,0.)
    assert validate_session(dict(version=3,**dict(DEFAULTS,selection=['elements','earth','cavern'],layers=earth_layers)))['layers']==earth_layers
    assert selection_states(['elements','air'])==['air']
    assert selection_states(['elements','air','citadel'])==['citadel']
    assert selection_states(['elements','fire'])==['fire_cycle']
    assert selection_states(['elements','fire','molten'])==['molten']
    assert selection_states(['elements','fire','firescape'])==['firescape']
    assert selection_states(['elements','fire','aftershock'])==['aftershock']
    assert selection_states(['elements','fire','sheets'])==['fire']
    assert selection_states(['elements','water'])==['water']
    assert selection_states(['elements','water','rain'])==['rain']
    assert selection_states(['elements','water','currents'])==['currents']
    water_layers=validate_layers({'water':dict(mode='cycle',seconds=4.,items=[
        dict(id='water_rain',enabled=True),dict(id='water_ripples',enabled=True)])})
    assert layers_at(water_layers,13,0)==(1,BITS['water_rain'])
    assert layers_at(water_layers,13,4)==(1,BITS['water_ripples'])
    assert selection_states(['cosmic'])==['canvas']
    assert list(WORLD_TREE['cosmic']['children']) == ['canvas','galaxy']
    assert selection_states(['cosmic','galaxy']) == ['galaxy']
    assert not any(row.get('selection') == ['cosmic','geometry'] for row in catalog)
    from renderer import LIVE_FORMS
    assert 3 not in LIVE_FORMS and 5 in LIVE_FORMS
    for version in (1,2,3):
        legacy = validate_session(dict(version=version,state='cosmic',selection=['cosmic','geometry']))
        assert legacy['selection'] == ['cosmic','canvas'] and legacy['state'] == 'canvas'
    assert selection_states([])==['blend']
    # A second future branch must not truncate Water's descendants to one hold.
    with patch.dict(WORLD_TREE['elements']['children'], {'test-other':dict(label='Test',state='organic')}):
        assert selection_states(['elements'])==['magnetic','arcs','auroral','nebula','marsh','pressure','dunes','strata','cavern','windstreams','stormfront','vortex','citadel','sea','dyes','rain','waterfall','currents','fire','molten','firescape','aftershock','organic']
    assert selection_states(['future'], {'future':dict(children={
        'a':dict(children={'b':dict(children={'c':dict(state='rain')})}),
        'd':dict(state='sea')})})==['rain','sea']
    for invalid in (None,'water',['elements','rain'],['organic','water'],['elements','']):
        try:validate_session(dict(version=2,**values,selection=invalid))
        except ValueError:pass
        else:raise AssertionError(invalid)
    for change in (dict(version=9),dict(state='unknown'),dict(speed='nan'),dict(captures='true')):
        try:validate_session(dict(version=1,**values)|change)
        except ValueError:pass
        else:raise AssertionError(change)
    with tempfile.TemporaryDirectory(dir=ROOT/'work') as temporary:
        folder=Path(temporary)
        for state in LIVE_STATES:
            args=command(dict(values,state=state),folder)
            assert args[args.index('--state')+1]==('canvas' if state=='cosmic' else state)
            legacy=validate_session(dict(version=1,**dict(values,state=state)))
            assert legacy['selection']==path_for_state(state)
        for source in ('Test track','Synthetic preview','Live system audio'):
            args=command(dict(values,source=source,selection=['cosmic'],layers=profiles),folder)
            assert '--states' not in args and args[args.index('--state')+1]=='canvas'
            assert parse_layers(args[args.index('--layers')+1])==profiles
        root=tk.Tk();root.withdraw()
        app=Studio(root)
        try:
            root.deiconify();root.update()
            style = __import__('tkinter.ttk', fromlist=['Style']).Style(root)
            for widget in ('Treeview', 'TEntry', 'TSpinbox', 'TCombobox'):
                assert style.lookup(widget, 'fieldbackground') == '#233047'
            assert style.lookup('Treeview', 'background') == '#233047'
            assert style.lookup('Treeview', 'foreground') == '#e3eaf4'
            assert style.lookup('Treeview', 'foreground', ('selected',)) == '#ffffff'
            before = app.values()
            app.library_query.set('waterfall')
            root.update()
            assert app.library_list.get_children()
            app.library_list.selection_set('world:elements/water/waterfall')
            app.show_library_entry()
            app.choose_library_world()
            assert app.selection == ['elements', 'water', 'waterfall']
            assert app.values()['layers'] == before['layers'] and app.process is None
            app.tabs.select(app.library_tab)
            app.library_query.set('no-such-entry-xyz')
            root.update()
            assert not app.library_list.get_children()
            assert str(app.library_choose['state']) == 'disabled'
            app.library_query.set('daddy')
            app.library_kind.set('Experiments')
            root.update()
            assert app.library_list.get_children() == ('effect:daddy_long_legs',)
            assert str(app.library_choose['state']) == 'disabled'
            app.library_sources.set(True); app.show_library_entry()
            assert 'preview_layers.py' in app.library_detail.get('1.0', 'end')
            root.geometry('680x800'); root.update()
            assert app.library_choose.winfo_rooty() + app.library_choose.winfo_height() < root.winfo_rooty() + root.winfo_height()
            app.tabs.select(app.preview); root.update()
            assert len(tracks()) == 3
            (folder/'old-geometry.json').write_text(json.dumps(dict(version=3,
                track=str(tracks()[0]),selection=['cosmic','geometry'])))
            with patch('studio.filedialog.askopenfilename',return_value=str(folder/'old-geometry.json')):
                app.load()
            assert app.selection == ['cosmic','canvas']
            assert tuple(app.selector_rows[1][1]['values']) == ('','Planet canvas','Galaxy')
            assert app.stop_button.winfo_y()+app.stop_button.winfo_height() <= app.preview.winfo_height()
            app.session_path=folder/'session.json'
            app.select(['elements','water','rain']);app.vars['speed'].set('6×')
            app.save()
            app.new()
            with patch('studio.filedialog.askopenfilename',return_value=str(app.session_path or folder/'session.json')):
                app.load()
            assert app.vars['state'].get()=='rain' and app.vars['speed'].get()=='6×'
            assert app.selection==['elements','water','rain']
            assert len(app.selector_rows)==3
            # Actual bound callbacks: clear a leaf, then change its ancestor.
            var,box,callback=app.selector_rows[2];var.set('');callback()
            assert app.selection==['elements','water'] and app.values()['state']=='water'
            var,box,callback=app.selector_rows[0];var.set('Organic');callback()
            assert app.selection==['organic'] and len(app.selector_rows)==2
            var,box,callback=app.selector_rows[1];var.set('Roots');callback()
            assert app.values()['state']=='roots'
            # Real layer table callbacks: independent worlds, enable/solo/order/save.
            app.select(['geometric','corridor'])
            app.sections.select(app.section_frames['Materials']);app.refresh_layers()
            app.effect_category.set('Material');app.refresh_effect_picker()
            app.effect_choice.set('Living artifacts');app.add_layer()
            app.effect_choice.set('Drifting flecks');app.add_layer()
            app.edit_layer('up')
            assert app.layer_table.get_children()==('flecks','artifacts')
            app.edit_layer('solo')
            assert [item['enabled'] for item in app.layer_profiles['geometric']['items']]==[True,False]
            app.layer_table.selection_set('artifacts');app.edit_layer('toggle')
            app.layer_mode.set('Cycle list');app.layer_hold.set('4');app.change_layer_playback()
            expected=validate_layers(app.layer_profiles)
            app.select(['cosmic','canvas'])
            assert app.layer_mode.get()=='Authored' and not app.layer_table.get_children()
            app.sections.select(app.section_frames['World details']);app.refresh_layers()
            app.effect_category.set('World details');app.refresh_effect_picker()
            app.effect_choice.set('Drifting starfield');app.add_layer()
            app.edit_layer('remove')
            assert app.layer_profiles['cosmic']['items']==[]
            app.select(['geometric','corridor'])
            assert app.layer_profiles['geometric']==expected['geometric']
            app.session_path=folder/'layers.json';app.save();app.new()
            with patch('studio.filedialog.askopenfilename',return_value=str(folder/'layers.json')):app.load()
            assert app.layer_profiles['geometric']==expected['geometric']
            assert app.layer_mode.get()=='Cycle list'
            # Verify layer tab at the minimum supported window size.
            root.geometry('680x800');app.tabs.select(app.layers_tab);root.update()
            for widget in app.layers_tab.winfo_children():
                assert widget.winfo_y()+widget.winfo_height()<=app.layers_tab.winfo_height(), widget
                assert widget.winfo_x()+widget.winfo_width()<=app.layers_tab.winfo_width(), widget
            app.select(['elements','water','currents'])
            app.sections.select(app.section_frames['World details']);app.refresh_layers()
            app.effect_category.set('Water details');app.refresh_effect_picker()
            assert len(app.effect_box['values'])==5
            app.effect_choice.set('Rain streaks');app.add_layer()
            app.effect_choice.set('Ripple rings');app.add_layer()
            app.layer_mode.set('Cycle list');app.change_layer_playback()
            assert [item['id'] for item in app.layer_profiles['water']['items']]==['water_rain','water_ripples']
            app.session_path=folder/'water-layers.json';app.save()
            restored=validate_session(json.loads(app.session_path.read_text(encoding='utf-8')))
            assert restored['state']=='currents' and restored['layers']['water']['mode']=='cycle'
            root.update()
            for widget in app.layers_tab.winfo_children():
                assert widget.winfo_y()+widget.winfo_height()<=app.layers_tab.winfo_height(), widget
            app.select(['elements','fire','sheets'])
            app.sections.select(app.section_frames['World details']);app.refresh_layers()
            app.effect_category.set('Fire details');app.refresh_effect_picker()
            assert set(app.effect_box['values'])=={'Coals','Embers','Hot seams','Ash'}
            app.effect_choice.set('Embers');app.add_layer()
            app.layer_mode.set('Cycle list');app.change_layer_playback()
            app.session_path=folder/'fire-layers.json';app.save()
            restored=validate_session(json.loads(app.session_path.read_text(encoding='utf-8')))
            assert restored['state']=='fire'
            app.select(['elements','fire','molten'])
            assert app.layer_profiles['fire']==restored['layers']['fire']
            assert app.values()['state']=='molten'
            assert layers_at(restored['layers'],15,0)==(1,BITS['fire_embers'])
            assert layers_at(restored['layers'],16,0)==(1,BITS['fire_embers'])
            app.select(['elements','fire','firescape'])
            app.sections.select(app.section_frames['World details']);app.refresh_layers()
            app.effect_category.set('Fire details');app.refresh_effect_picker()
            app.effect_choice.set('Ash');app.add_layer()
            app.session_path=folder/'firescape-layers.json';app.save()
            wild=validate_session(json.loads(app.session_path.read_text(encoding='utf-8')))
            app.select(['elements','fire','aftershock'])
            app.sections.select(app.section_frames['World details']);app.refresh_layers()
            app.effect_category.set('Aftershock details');app.refresh_effect_picker()
            assert set(app.effect_box['values'])=={'Inversion flash','Dust shockwaves','Ground fire','Aurora'}
            app.effect_choice.set('Dust shockwaves');app.add_layer()
            app.session_path=folder/'aftershock-layers.json';app.save()
            blast=validate_session(json.loads(app.session_path.read_text(encoding='utf-8')))
            assert blast['state']=='aftershock'
            assert blast['layers']['fire']['items'][-1]['id']=='blast_dust'
            assert wild['state']=='firescape'
            assert wild['layers']['fire']['items'][-1]['id']=='fire_ash'
            assert layers_at(wild['layers'],17,0)==(1,BITS['fire_embers'])
            assert layers_at(restored['layers'],14,0)==(1,BITS['fire_embers'])
            assert restored['layers']['water']['mode']=='cycle'
            saved_profiles=app.layer_profiles
            app.material_trio()
            assert app.layer_mode.get()=='Meld materials'
            root.update()
            for widget in app.layers_tab.winfo_children():
                assert widget.winfo_y()+widget.winfo_height()<=app.layers_tab.winfo_height(), widget
            app.sections.select(app.section_frames['Materials']);app.refresh_layers()
            app.effect_category.set('Material');app.refresh_effect_picker()
            assert 'Liquid Alloy' in app.effect_box['values'] and 'Prismatic Lattice' in app.effect_box['values']
            app.session_path=folder/'materials.json';app.save()
            saved_trio=validate_session(json.loads(app.session_path.read_text(encoding='utf-8')))
            assert saved_trio['layers']==trio
            app.layer_profiles=saved_profiles
            app.tabs.select(app.preview)
            app.select(['elements'])
            assert len(app.selector_rows)==2 and app.selector_rows[1][0].get()==''
            # A deeper branch generates another row without UI code changes.
            with patch.dict(WORLD_TREE['elements']['children']['water']['children'],
                            {'test-detail':dict(label='Test detail',children={'nested':dict(label='Nested',state='rain')})}):
                app.select(['elements','water','test-detail'])
                assert len(app.selector_rows)==4
                var,box,callback=app.selector_rows[3];var.set('Nested');callback()
                assert app.values()['state']=='rain'
            app.blend();assert app.vars['state'].get()=='blend'
            # Main defaults must be visible/editable without loading a preset.
            saved_profiles=app.layer_profiles
            app.layer_profiles={};app.refresh_layers()
            assert app.layer_mode.get()=='Meld materials'
            root.update()
            for widget in app.layers_tab.winfo_children():
                assert widget.winfo_y()+widget.winfo_height()<=app.layers_tab.winfo_height(), widget
            assert all(app.layer_table.exists(key) for key in ('artifacts','alloy','lattice'))
            app.layer_table.selection_set('artifacts');app.edit_layer('toggle')
            assert not app.layer_profiles['blend']['items'][0]['enabled']
            assert materials_at(app.layer_profiles,0,0.)==(0.,1.,0.)
            app.layer_profiles=saved_profiles;app.refresh_layers()

            # Start a real replay child through the UI callback, then stop only that child.
            app.vars['speed'].set('Real time');app.vars['duration'].set('30 seconds')
            app.start_button.invoke();root.update()
            assert app.process is not None and str(app.start_button['state'])=='disabled'
            child=app.process
            app.stop_button.invoke();root.update()
            assert child.poll() is not None and app.process is None
            assert str(app.start_button['state'])=='normal'
        finally:app.close()
        # Full shared analysis+GPU path at both pacing settings.
        began=time.perf_counter()
        _,real=replay(available[0],speed=1,max_seconds=1.0,state='water')
        duration=time.perf_counter()-began
        _,fast=replay(available[0],speed=0,max_seconds=1.0,state='water')
        assert real==fast and len(real)==24
        assert duration>=1.,duration
        _,layer_rows=replay(available[0],speed=0,max_seconds=9.,state='geometric',
            layers=profiles,capture_dir=folder/'layer-captures',capture_interval=4.)
        assert all(row['layer_mode']==1 and row['layer_mask']==
            (1 if int(row['seconds']//4)%2==0 else 32) for row in layer_rows)
        recorded=json.loads((folder/'layer-captures/captures.json').read_text())
        assert recorded['layers']==profiles
        assert [row['layer_mask'] for row in recorded['captures']]==[1,32,1]
        # Real replay crosses two group boundaries without resetting analysis.
        _,cycle=replay(available[0],speed=0,max_seconds=57.,state='canvas',
            states=['canvas','cosmic'],metrics_path=folder/'cycle.csv',
            capture_dir=folder/'captures',capture_interval=28.)
        assert len(cycle)>1300
        assert all(row['state']==('canvas' if int(row['seconds']//28)%2==0 else 'cosmic') for row in cycle)
        captures=json.loads((folder/'captures/captures.json').read_text())['captures']
        assert [c['state'] for c in captures]==['canvas','cosmic','canvas']
        for speed in (-1.,float('nan'),float('inf')):
            try:replay(available[0],speed=speed,max_seconds=1.)
            except ValueError:pass
            else:raise AssertionError('Invalid speed accepted')
    renderer=Renderer(width=320,height=180)
    try:
        glfw.init();glfw.window_hint(glfw.VISIBLE,glfw.FALSE);renderer.create()
        renderer.debug_sequence=(5,3)
        last_star=-1.;last_flow=-1.
        for seconds,expected in ((0.,5),(27.99,5),(28.,3),(55.99,3),(56.,5)):
            renderer.render(elapsed_time=seconds)
            assert renderer.program['u_debug_state'].value==expected
            assert renderer.star_time>last_star and renderer.flow_time>last_flow
            last_star,last_flow=renderer.star_time,renderer.flow_time
            pixels=np.frombuffer(renderer.ctx.screen.read(components=3),dtype=np.uint8)
            assert pixels.std()>2
        renderer.debug_sequence=()
        renderer.debug_state=9
        renderer.render(elapsed_time=57.)
        assert renderer.program['u_debug_state'].value==9
        renderer.debug_state=2;renderer.layer_profiles=profiles
        for seconds,mask in ((60.,32),(64.,1),(68.,32)):
            renderer.render(elapsed_time=seconds)
            assert renderer.program['u_layer_mode'].value==1
            assert renderer.program['u_layer_mask'].value==mask
            assert renderer.star_time>last_star and renderer.flow_time>last_flow
            last_star,last_flow=renderer.star_time,renderer.flow_time
        renderer.debug_state=5;renderer.render(elapsed_time=69.)
        assert renderer.program['u_layer_mode'].value==0
        assert renderer.program['u_daddy_long_legs'].value==0.
        renderer.layer_profiles=trio
        for seconds,state in ((70.,7),(75.,15),(80.,18),(84.,0),(90.,5)):
            renderer.debug_state=state;renderer.render(elapsed_time=seconds)
            assert np.allclose(renderer.program['u_material_mix'].value,materials_at(trio,state,seconds))
            assert renderer.star_time>last_star and renderer.flow_time>last_flow
            last_star,last_flow=renderer.star_time,renderer.flow_time
        renderer.layer_profiles=experiments;renderer.debug_state=21;renderer.render(elapsed_time=92.)
        assert renderer.program['u_daddy_long_legs'].value==1.
        renderer.layer_profiles=earth_layers;renderer.debug_state=24;renderer.render(elapsed_time=92.)
        assert renderer.program['u_earth_details'].value==(0.,0.,1.,0.)
        renderer.layer_profiles={};renderer.render(elapsed_time=93.)
        assert renderer.program['u_earth_details'].value==(1.,1.,1.,1.)
        renderer.layer_profiles=fog_layers;renderer.debug_state=29;renderer.render(elapsed_time=96.)
        assert renderer.program['u_fog_details'].value==(1.,0.,0.)
        renderer.layer_profiles={};renderer.render(elapsed_time=97.)
        assert renderer.program['u_fog_details'].value==(1.,1.,1.)
        renderer.layer_profiles=plasma_layers;renderer.debug_state=33;renderer.render(elapsed_time=100.)
        assert renderer.program['u_plasma_details'].value==(0.,1.,0.)
        renderer.layer_profiles={};renderer.render(elapsed_time=101.)
        assert renderer.program['u_plasma_details'].value==(1.,1.,1.)
        assert renderer.program['u_daddy_long_legs'].value==0.
    finally:renderer.close()
    print('PASS: Library search/catalog/source anchors, safe selection, minimum layout, recursive forms, per-world layer table/solo/order, legacy/v3 sessions, validation, all launch modes, minimum layout, UI lifecycle, real replay state/effect metadata and pacing, continuous GPU clocks.')


if __name__=='__main__':
    import subprocess
    import sys
    if '--organization-test' in sys.argv:
        studio_organization_test()
    elif '--roots-colors-test' in sys.argv:
        roots_colors_studio_test()
    elif '--studio-comparison-test' in sys.argv:
        studio_comparison_test()
    elif '--planet-palette-test' in sys.argv:
        planet_palette_studio_test()
    elif '--galaxy-scene-test' in sys.argv:
        galaxy_scene_studio_test()
    else:
        main()
        # Keep Tk interpreters in separate processes so destroyed-window timers
        # from the existing lifecycle test cannot run in the palette test.
        subprocess.run([sys.executable,'-X','utf8',__file__,'--planet-palette-test'],check=True)
        subprocess.run([sys.executable,'-X','utf8',__file__,'--studio-comparison-test'],check=True)
        subprocess.run([sys.executable,'-X','utf8',__file__,'--roots-colors-test'],check=True)
