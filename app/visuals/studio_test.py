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
    assert material_weights(quartet,0,108.)==(0.,0.,0.,1.)
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
    assert selection_states(['cosmic'])==['canvas','cosmic']
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
            assert args[args.index('--state')+1]==state
            legacy=validate_session(dict(version=1,**dict(values,state=state)))
            assert legacy['selection']==path_for_state(state)
        for source in ('Test track','Synthetic preview','Live system audio'):
            args=command(dict(values,source=source,selection=['cosmic'],layers=profiles),folder)
            assert args[args.index('--states')+1:args.index('--states')+3]==['canvas','cosmic']
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
            root.geometry('680x700'); root.update()
            assert app.library_choose.winfo_rooty() + app.library_choose.winfo_height() < root.winfo_rooty() + root.winfo_height()
            app.tabs.select(app.preview); root.update()
            assert len(tracks()) == 3
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
            root.geometry('680x700');app.tabs.select(app.layers_tab);root.update()
            for widget in app.layers_tab.winfo_children():
                assert widget.winfo_y()+widget.winfo_height()<=app.layers_tab.winfo_height(), widget
                assert widget.winfo_x()+widget.winfo_width()<=app.layers_tab.winfo_width(), widget
            app.select(['elements','water','currents'])
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
            app.effect_category.set('Fire details');app.refresh_effect_picker()
            app.effect_choice.set('Ash');app.add_layer()
            app.session_path=folder/'firescape-layers.json';app.save()
            wild=validate_session(json.loads(app.session_path.read_text(encoding='utf-8')))
            app.select(['elements','fire','aftershock'])
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


if __name__=='__main__':main()
