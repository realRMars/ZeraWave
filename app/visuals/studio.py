"""Development control window; launches the existing preview/replay/live entry points."""
import json
from copy import deepcopy
import wave
import csv
import hashlib
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from color_controls import validate_colors, targets_for, scene_colors
from studio_color_link import ColorLink
from color_inspector import ColorInspector

from technique_library import entries as library_entries, search as search_library
from live_visual_test import LIVE_STATES
from preview_layers import (EFFECTS, MATERIALS, MODES, default_profile, validate_layers, world_for_state, material_trio_profile, material_quartet_profile, WORLDS, NEW_MATERIALS, SPATIAL_TREATMENTS, ENVELOPERS)

ROOT = Path(__file__).resolve().parents[2]
SPEEDS = {'Real time': 1., '2×': 2., '6×': 6., '12×': 12., 'Fastest': 0.}
SOURCES = ('Test track', 'Synthetic preview', 'Live system audio')
PLANET_PALETTES = {'authored': 'Authored', 'soft-dream': 'Soft Dream'}
DEFAULTS = dict(state='water', source='Test track', track='', speed='12×',
                duration='Full track', captures=True, planet_palette='authored')


# Stable keys are session IDs; labels can evolve independently. Add descendants
# here at any depth. A cycle names an existing authored meld for a whole branch.
WORLD_TREE = {
    'organic': dict(label='Organic', cycle='organic', children={
        'membrane': dict(label='Membrane', state='membrane'),
        'roots': dict(label='Roots', state='roots'),
    }),
    'geometric': dict(label='Geometric', cycle='geometric', children={
        'corridor': dict(label='Neon corridor', state='geometric'),
    }),
    'cosmic': dict(label='Cosmic', children={
        'canvas': dict(label='Planet canvas', state='canvas'),
    }),
    'transition': dict(label='Transition', state='transition'),
    'elements': dict(label='Elements', children={
        'plasma': dict(label='Plasma', cycle='plasma', children={
            'magnetic': dict(label='Magnetic Bloom', state='magnetic'),
            'arcs': dict(label='Arc Constellation', state='arcs'),
            'auroral': dict(label='Auroral Veil', state='auroral'),
        }),
        'fog': dict(label='Fog / Gas', cycle='fog', children={
            'nebula': dict(label='Nebula Banks', state='nebula'),
            'marsh': dict(label='Ghostlight Marsh', state='marsh'),
            'pressure': dict(label='Pressure Chamber', state='pressure'),
        }),
        'earth': dict(label='Earth', cycle='earth', children={
            'dunes': dict(label='Dune Sea', state='dunes'),
            'strata': dict(label='Folded Strata', state='strata'),
            'cavern': dict(label='Crystal Cavern', state='cavern'),
        }),
        'air': dict(label='Air / Wind', cycle='air', children={
            'windstreams': dict(label='Windstreams', state='windstreams'),
            'stormfront': dict(label='Stormfront', state='stormfront'),
            'vortex': dict(label='Vortex', state='vortex'),
            'citadel': dict(label='Sky Citadel', state='citadel'),
        }),
        'water': dict(label='Water', cycle='water', children={
            'sea': dict(label='Sea', state='sea'),
            'dyes': dict(label='Liquid dyes', state='dyes'),
            'rain': dict(label='Rain & ripples', state='rain'),
            'waterfall': dict(label='Waterfall', state='waterfall'),
            'currents': dict(label='Currents', state='currents'),
        }),
        'fire': dict(label='Fire', cycle='fire_cycle', children={
            'sheets': dict(label='Flame sheets', state='fire'),
            'molten': dict(label='Molten flow', state='molten'),
            'firescape': dict(label='Firescape', state='firescape'),
            'aftershock': dict(label='Aftershock', state='aftershock'),
        }),
    }),
}
DEFAULT_SELECTION = ['elements', 'water']


def selected_node(selection, tree=None):
    children = WORLD_TREE if tree is None else tree
    node = dict(children=children)
    if not isinstance(selection, list) or any(not isinstance(key, str) or not key for key in selection):
        raise ValueError('Invalid visual selection path.')
    for key in selection:
        if key not in children:
            raise ValueError('This visual selection no longer exists. Choose a current world.')
        node = children[key]
        children = node.get('children', {})
    return node


def selection_states(selection, tree=None):
    node = selected_node(selection, tree)
    if not selection:
        return ['blend']
    # A single child can keep its authored cycle. With multiple branches,
    # visit every leaf so a short group hold cannot skip grandchildren.
    while not node.get('cycle', node.get('state')) and len(node.get('children', {})) == 1:
        node = next(iter(node['children'].values()))
    native = node.get('cycle', node.get('state'))
    def collect(item):
        if item.get('children'):
            return [state for child in item['children'].values() for state in collect(child)]
        state = item.get('cycle', item.get('state'))
        if state is not None:
            if state not in LIVE_STATES:
                raise ValueError('This visual has no implemented renderer state.')
            return [state]
        return [state for child in item.get('children', {}).values() for state in collect(child)]
    result = [native] if native else list(dict.fromkeys(collect(node)))
    if any(state not in LIVE_STATES for state in result):
        raise ValueError('This visual has no implemented renderer state.')
    if not result: raise ValueError('No implemented visuals in this category.')
    return result


def path_for_state(state):
    if state == 'blend': return []
    # The diagnostic remains in CLI/tests; old Studio sessions open the review form.
    if state == 'cosmic': return ['cosmic', 'canvas']
    def find(children, path):
        for key, node in children.items():
            here = path + [key]
            if state in (node.get('state'), node.get('cycle')): return here
            found = find(node.get('children', {}), here)
            if found is not None: return found
        return None
    result = find(WORLD_TREE, [])
    if result is None: raise ValueError('Unknown visual state.')
    return result


def selection_title(selection):
    if not selection: return 'Main blend (all worlds)'
    return ' / '.join(selected_node(selection[:i+1])['label'] for i in range(len(selection)))


def tracks():
    available = sorted((ROOT / 'work/audio-replay').glob('*.wav'))
    # Prefer the decoded copies bearing the original track names.
    unique = {}
    for path in available:
        key = path.stem.replace(' ', '').casefold()
        if key not in unique or ' ' in path.stem:
            unique[key] = path
    return list(unique.values())


def validate_session(data):
    if not isinstance(data, dict) or data.get('version') not in (1, 2, 3):
        raise ValueError('This is not a supported ZeraWave development session.')
    values = {key: data.get(key, value) for key, value in DEFAULTS.items()}
    selection = (path_for_state(values['state']) if data['version'] == 1
                 else data.get('selection'))
    if selection == ['cosmic', 'geometry']:
        selection = ['cosmic', 'canvas']
    states = selection_states(selection)
    values['layers'] = validate_layers(data.get('layers', {}) if data['version'] == 3 else {})
    if data.get('material_isolation'):
        values['material_isolation'] = validate_isolation(data['material_isolation'])
    elif 'material_isolation' in data:
        validate_isolation(data['material_isolation'])
    if 'color_overrides' in data:
        clean_colors = validate_colors(data['color_overrides'])
        if clean_colors: values['color_overrides'] = clean_colors
    preview_profiles(values)
    values['selection'] = list(selection)
    values['state'] = states[0]
    if not isinstance(values['planet_palette'], str) or values['planet_palette'] not in PLANET_PALETTES:
        raise ValueError('Unknown Planet Canvas palette.')
    if values['source'] not in SOURCES:
        raise ValueError('Unknown input source.')
    if values['speed'] not in SPEEDS or values['duration'] not in ('Full track', '30 seconds', '60 seconds'):
        raise ValueError('Unknown speed or duration.')
    if not isinstance(values['track'], str) or type(values['captures']) is not bool:
        raise ValueError('Invalid track or capture setting.')
    return values


def effect_section(key):
    """Presentation only; retain catalog IDs, compatibility and combined order."""
    if key in MATERIALS: return 'Materials'
    if EFFECTS[key][1] == 'Envelopers': return 'Envelopers'
    if EFFECTS[key][1] in ('Material', 'Spatial', 'Sky effects'): return 'Shared FX'
    return 'World details'


def validate_isolation(data):
    if not isinstance(data, dict): raise ValueError('Invalid material isolation.')
    for world, key in data.items():
        if world not in WORLDS or not isinstance(key, str) or key not in MATERIALS:
            raise ValueError('Unknown isolated material or world.')
    return dict(data)


def preview_profiles(values):
    profiles = validate_layers(values.get('layers', {}))
    for world, key in validate_isolation(values.get('material_isolation', {})).items():
        profile = profiles.get(world, default_profile(world))
        if profile['mode'] == 'authored':
            raise ValueError('Choose Selected together or Meld materials before isolating a material.')
        # Temporary hold explicitly suspends Cycle; the saved source list is untouched.
        profile['mode'] = 'together'
        for item in profile['items']:
            if item['id'] in MATERIALS: item['enabled'] = item['id'] == key
        if not any(item['id'] == key for item in profile['items']):
            profile['items'].append(dict(id=key, enabled=True))
        profiles[world] = profile
    return profiles


def comparison_runs(values):
    """Frozen sequential replay pair; no mutation of the user's session."""
    if selection_states(values['selection']) != ['canvas']:
        raise ValueError('Hold Cosmic / Planet canvas before comparing palettes.')
    if values['source'] != 'Test track':
        raise ValueError('Select Test track in Build & preview. Matched A/B uses decoded replay, never live input.')
    if not values.get('material_isolation', {}).get('cosmic'):
        raise ValueError('In Materials, choose a material and click Isolate material first.')
    with wave.open(values['track'], 'rb') as audio:
        if audio.getframerate() != 48000 or audio.getsampwidth() != 2 or not audio.getnframes():
            raise ValueError('Matched A/B needs a nonempty decoded 48 kHz, 16-bit WAV.')
    frozen = deepcopy(values)
    frozen['layers'] = preview_profiles(values)
    frozen.pop('material_isolation', None)
    # Fixed bounded segment, same pacing and input chunks for each fresh child.
    frozen.update(duration='30 seconds', speed='Real time')
    return [(label, dict(deepcopy(frozen), planet_palette=palette))
            for label, palette in (('A', 'authored'), ('B', 'soft-dream'))]


def command(values, output):
    selection = values['selection'] if 'selection' in values else path_for_state(values['state'])
    states = selection_states(selection)
    palette = values.get('planet_palette', 'authored')
    if not isinstance(palette, str) or palette not in PLANET_PALETTES:
        raise ValueError('Unknown Planet Canvas palette.')
    state_args = ['--state', states[0]]
    # Park the saved experiment choice outside this single held form.
    if states == ['canvas']: state_args += ['--palette', palette]
    colors = validate_colors(values.get('color_overrides', {}))
    color_scope = states[0] if len(states)==1 else 'blend'
    if targets_for(color_scope):
        state_args += ['--colors', json.dumps(scene_colors(colors, color_scope), separators=(',', ':'))]
    if len(states) > 1: state_args += ['--states', *states]
    profiles = preview_profiles(values)
    if profiles: state_args += ['--layers', json.dumps(profiles, separators=(',', ':'))]
    base = [sys.executable, '-X', 'utf8', '-u']
    if values['source'] == 'Live system audio':
        return base + [str(ROOT / 'app/visuals/live_visual_test.py')] + state_args
    if values['source'] == 'Synthetic preview':
        return base + [str(ROOT / 'app/visuals/shader_test.py')] + state_args
    track = Path(values['track'])
    if not track.is_file():
        raise ValueError('Choose an existing decoded 48 kHz, 16-bit WAV track.')
    args = base + [str(ROOT / 'app/visuals/replay_test.py'), str(track),
        *state_args, '--speed', str(SPEEDS[values['speed']]),
        '--metrics', str(output / 'metrics.csv')]
    if values['duration'] != 'Full track':
        args += ['--max-seconds', values['duration'].split()[0]]
    if values['captures']:
        args += ['--capture-dir', str(output), '--capture-interval', '15']
    return args


def replay_identity(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''): digest.update(chunk)
    with wave.open(str(path), 'rb') as audio:
        count = math.ceil(min(audio.getnframes(), audio.getframerate() * 30) / 2048)
    return digest.hexdigest(), count


def completed_comparison_run(folder, label, count):
    with (folder/label/'metrics.csv').open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != count:
        raise ValueError(f'{label} ended early ({len(rows)}/{count} frames); comparison cancelled.')
    if label == 'B':
        with (folder/'A'/'metrics.csv').open(newline='', encoding='utf-8') as handle:
            if rows != list(csv.DictReader(handle)):
                raise ValueError('A/B replay measurements differ; comparison is not matched.')
    return rows


class Studio:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.log = None
        self.output = None
        self.session_path = None
        self.layer_profiles = {}
        self.material_isolation = {}
        self.color_overrides = {}
        self.color_editor = None
        self.color_link = None
        self.active_color_scene = None
        self.preview_start_colors = {}
        self.color_send_after = None
        self.last_color_revision = None
        self.last_color_ack = None
        self.color_status = tk.StringVar(value='Select a world, family cycle or Main to edit declared colors. Other settings apply on the next preview.')
        self.comparison_queue = []
        self.comparison_folder = None
        self.comparison_active = False
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', background='#141a28', foreground='#e3eaf4', font=('Segoe UI', 10))
        # clam keeps white field defaults unless each input/table is styled.
        style.configure('Treeview', background='#233047', fieldbackground='#233047',
                        foreground='#e3eaf4', rowheight=24)
        style.map('Treeview', background=[('selected', '#365775')],
                  foreground=[('selected', '#ffffff')])
        style.configure('Treeview.Heading', background='#283951', foreground='#e3eaf4')
        style.map('Treeview.Heading', background=[('active', '#365775')])
        for widget in ('TEntry', 'TSpinbox'):
            style.configure(widget, fieldbackground='#233047', foreground='#e3eaf4',
                            insertcolor='#ffffff', selectbackground='#365775', selectforeground='#ffffff')
            style.map(widget, fieldbackground=[('disabled', '#1b2434'), ('readonly', '#233047')],
                      foreground=[('disabled', '#a6b4c8')])
        root.option_add('*TCombobox*Listbox.background', '#233047')
        root.option_add('*TCombobox*Listbox.foreground', '#e3eaf4')
        root.option_add('*TCombobox*Listbox.selectBackground', '#365775')
        root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
        style.configure('TNotebook.Tab', padding=(16, 8))
        style.map('TNotebook.Tab', background=[('selected', '#283951')])
        style.configure('TCombobox', fieldbackground='#233047', background='#283951')
        style.map('TCombobox', fieldbackground=[('readonly', '#233047')],
                  foreground=[('readonly', '#e3eaf4')])
        style.configure('TButton', padding=(12, 8), background='#283951')
        style.map('TButton', background=[('active', '#365775')])
        root.configure(background='#141a28')
        self.root.title('ZeraWave — Development Studio')
        self.root.geometry('780x820')
        self.root.minsize(680, 800)
        self.vars = {k: (tk.BooleanVar(value=v) if isinstance(v, bool) else tk.StringVar(value=v))
                     for k, v in DEFAULTS.items()}
        available = tracks()
        if available:
            self.vars['track'].set(str(available[0]))
        self.active_preview = tk.StringVar(value='No preview running.')
        self.status = tk.StringVar(value='Ready. Choose a world and a source, then start a preview.')
        self.footer = ttk.Frame(root)
        self.footer.pack(side='bottom', fill='x')
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill='both', expand=True, padx=18, pady=(18, 10))
        self.preview = ttk.Frame(self.tabs, padding=20)
        self.results = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(self.preview, text='Build & preview')
        self.layers_tab = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(self.layers_tab, text='Effects & layers')
        self.tabs.add(self.results, text='Review')
        ttk.Label(self.preview, text='Explore a world before blending it into ZeraWave',
                  font=('Segoe UI', 15)).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0,12))
        def field(row, label, key, options):
            ttk.Label(self.preview, text=label).grid(row=row,column=0,sticky='w',padx=(0,18),pady=8)
            widget = ttk.Combobox(self.preview,textvariable=self.vars[key],values=options,state='readonly')
            widget.grid(row=row,column=1,columnspan=2,sticky='ew')
            return widget
        self.selection = list(DEFAULT_SELECTION)
        self.selector_rows = []
        selector_shell = ttk.Frame(self.preview)
        selector_shell.grid(row=1,column=0,columnspan=3,sticky='ew',pady=(0,8))
        self.selector_canvas = tk.Canvas(selector_shell,height=120,highlightthickness=0,background='#141a28')
        selector_scroll = ttk.Scrollbar(selector_shell,orient='vertical',command=self.selector_canvas.yview)
        self.selector_canvas.configure(yscrollcommand=selector_scroll.set)
        selector_scroll.pack(side='right',fill='y')
        self.selector_canvas.pack(side='left',fill='both',expand=True)
        self.selector_frame = ttk.Frame(self.selector_canvas)
        selector_window = self.selector_canvas.create_window((0,0),window=self.selector_frame,anchor='nw')
        self.selector_canvas.bind('<Configure>',lambda event:self.selector_canvas.itemconfigure(selector_window,width=event.width))
        self.selector_frame.bind('<Configure>',lambda event:self.selector_canvas.configure(scrollregion=self.selector_canvas.bbox('all')))
        self.selection_hint = tk.StringVar()
        self.rebuild_selectors()
        self.source_box = field(2, 'Input', 'source', SOURCES)
        self.track_box = field(3, 'Test track', 'track', [str(p) for p in available])
        field(4, 'Replay speed', 'speed', tuple(SPEEDS))
        field(5, 'Test duration', 'duration', ('Full track','30 seconds','60 seconds'))
        ttk.Checkbutton(self.preview,text='Save frames and audio measurements',
                        variable=self.vars['captures']).grid(row=7,column=1,columnspan=2,sticky='w',pady=8)
        ttk.Label(self.preview,textvariable=self.selection_hint,wraplength=610).grid(row=8,column=0,columnspan=3,sticky='w',pady=(4,8))
        ttk.Label(self.preview,text='Track replay is silent. Live input listens to your system audio.\n'
                  'Speed, duration and captures apply to test tracks. Declared colors can edit live; other changes apply next run.',
                  wraplength=610).grid(row=9,column=0,columnspan=3,sticky='w',pady=10)
        self.start_button = ttk.Button(self.preview,text='Start preview',command=self.start)
        self.start_button.grid(row=10,column=1,sticky='ew',pady=12,padx=(0,8))
        self.stop_button = ttk.Button(self.preview,text='Stop preview',command=self.stop,state='disabled')
        self.stop_button.grid(row=10,column=2,sticky='ew',pady=12)
        self.preview.columnconfigure(1,weight=1)
        self.preview.columnconfigure(2,weight=1)
        ttk.Label(self.results,text='Review before integration',font=('Segoe UI',16)).pack(anchor='w')
        ttk.Label(self.results,text='Each track run gets its own folder with a log, input measurements and optional frames.\n\n'
            'Check quiet passages, transitions and intense sections across all three tracks.\n'
            'An isolated preview is not automatic approval for the main blend.\n\n'
            'Narrow the cascading world selectors to isolate a form, or leave a level blank.\n'
            'Main blend uses the same shader and renderer as run_live_visualizer.',wraplength=620).pack(anchor='w',pady=20)
        ttk.Button(self.results,text='Open latest results',command=self.open_results).pack(anchor='w')
        ttk.Button(self.results,text='Preview main blend',command=self.blend).pack(anchor='w',pady=12)
        ttk.Label(self.footer,textvariable=self.active_preview,wraplength=630).pack(fill='x',padx=20)
        ttk.Label(self.footer,textvariable=self.status,wraplength=630).pack(fill='x',padx=20,pady=(0,16))
        self.build_layers()
        self.refresh_layers()
        self.build_library()
        self.menus()
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.after(200,self.poll)

    def build_library(self):
        self.library_tab = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(self.library_tab, text='Library')
        ttk.Label(self.library_tab, text='Find what ZeraWave already knows',
                  font=('Segoe UI', 15)).pack(anchor='w')
        ttk.Label(self.library_tab, text='Browse worlds, optional layers and existing techniques before building something new.',
                  wraplength=600).pack(anchor='w', pady=(6, 12))
        filters = ttk.Frame(self.library_tab)
        filters.pack(fill='x')
        self.library_query = tk.StringVar()
        self.library_kind = tk.StringVar(value='All')
        ttk.Label(filters, text='Search').pack(side='left', padx=(0, 8))
        ttk.Entry(filters, textvariable=self.library_query).pack(side='left', fill='x', expand=True)
        self.library_rows = library_entries(WORLD_TREE)
        kinds = ['All', *dict.fromkeys(row['kind'] for row in self.library_rows)]
        ttk.Combobox(filters, textvariable=self.library_kind, values=kinds,
                     state='readonly', width=20).pack(side='left', padx=(8, 0))
        self.library_count = tk.StringVar()
        ttk.Label(self.library_tab, textvariable=self.library_count).pack(anchor='w', pady=8)
        list_frame = ttk.Frame(self.library_tab)
        list_frame.pack(fill='both', expand=True)
        self.library_list = ttk.Treeview(list_frame, columns=('kind',), show='tree headings', height=9, selectmode='browse')
        self.library_list.heading('#0', text='Name')
        self.library_list.heading('kind', text='Category')
        self.library_list.column('#0', width=380, minwidth=160)
        self.library_list.column('kind', width=140, minwidth=110, stretch=False)
        scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.library_list.yview)
        self.library_list.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.library_list.pack(side='left', fill='both', expand=True)
        detail_frame = ttk.Frame(self.library_tab)
        detail_frame.pack(fill='x', pady=12)
        self.library_detail = tk.Text(detail_frame, height=7, wrap='word', background='#233047',
                                      foreground='#e3eaf4', relief='flat', padx=10, pady=10)
        detail_scroll = ttk.Scrollbar(detail_frame, orient='vertical', command=self.library_detail.yview)
        self.library_detail.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side='right', fill='y')
        self.library_detail.pack(side='left', fill='x', expand=True)
        self.library_detail.configure(state='disabled')
        actions = ttk.Frame(self.library_tab)
        actions.pack(fill='x')
        self.library_choose = ttk.Button(actions, text='Choose for preview', command=self.choose_library_world, state='disabled')
        self.library_choose.pack(side='left')
        ttk.Button(actions, text='Effects & layers', command=lambda: self.tabs.select(self.layers_tab)).pack(side='left', padx=8)
        self.library_sources = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.library_tab, text='Show implementation locations', variable=self.library_sources,
                        command=self.show_library_entry).pack(anchor='w', pady=(8, 0))
        self.library_list.bind('<<TreeviewSelect>>', self.show_library_entry)
        self.library_query.trace_add('write', self.refresh_library)
        self.library_kind.trace_add('write', self.refresh_library)
        self.refresh_library()

    def refresh_library(self, *_):
        rows = search_library(self.library_rows, self.library_query.get(), self.library_kind.get())
        self.library_list.delete(*self.library_list.get_children())
        for row in rows:
            self.library_list.insert('', 'end', iid=row['id'], text=row['title'], values=(row['kind'],))
        self.library_count.set(f'{len(rows)} entries' if rows else 'No matches. Try a broader search or choose All.')
        if rows:
            self.library_list.selection_set(rows[0]['id'])
        self.show_library_entry()

    def show_library_entry(self, event=None):
        selected = self.library_list.selection()
        row = next((r for r in self.library_rows if selected and r['id'] == selected[0]), None)
        text = (row['title'] + '\n\n' + row['summary']) if row else 'Search by name, world or technique.'
        if row and self.library_sources.get():
            text += '\n\nImplementation: ' + '; '.join(row['sources'])
        self.library_detail.configure(state='normal')
        self.library_detail.delete('1.0', 'end')
        self.library_detail.insert('1.0', text)
        self.library_detail.configure(state='disabled')
        self.library_choose.configure(state='normal' if row and 'selection' in row else 'disabled')

    def choose_library_world(self):
        selected = self.library_list.selection()
        row = next((r for r in self.library_rows if selected and r['id'] == selected[0]), None)
        if row and 'selection' in row:
            self.select(row['selection'])
            self.tabs.select(self.preview)
            self.status.set('World selected. Your layer settings are preserved. Start preview when ready.')

    def values(self):
        values = {k:v.get() for k,v in self.vars.items()}
        values.update(selection=list(self.selection), state=selection_states(self.selection)[0],
                      layers=validate_layers(self.layer_profiles))
        if self.material_isolation: values['material_isolation'] = dict(self.material_isolation)
        if self.color_overrides: values['color_overrides'] = validate_colors(self.color_overrides)
        return values

    def select(self, selection):
        selection_states(selection)  # Validate before changing any controls.
        self.selection = list(selection)
        self.vars['state'].set(selection_states(selection)[0])
        self.rebuild_selectors()
        self.refresh_palette()
        self.refresh_layers()

    def rebuild_selectors(self):
        for child in self.selector_frame.winfo_children(): child.destroy()
        self.selector_rows = []
        children = WORLD_TREE
        depth = 0
        while children:
            keys = list(children)
            labels = [children[key]['label'] for key in keys]
            value = tk.StringVar(value=children[self.selection[depth]]['label'] if depth<len(self.selection) else '')
            label = ('World', 'Category' if self.selection[:1] == ['elements'] else 'Form', 'Form')[depth] if depth<3 else f'Detail {depth-2}'
            ttk.Label(self.selector_frame,text=label).grid(row=depth,column=0,sticky='w',padx=(0,18),pady=8)
            box = ttk.Combobox(self.selector_frame,textvariable=value,values=['',*labels],state='readonly',height=12)
            box.grid(row=depth,column=1,sticky='ew',pady=8)
            def changed(event=None, level=depth, var=value, ids=keys, names=labels):
                selected = var.get()
                self.select(self.selection[:level]+([ids[names.index(selected)]] if selected else []))
            box.bind('<<ComboboxSelected>>',changed)
            self.selector_rows.append((value,box,changed))
            if depth>=len(self.selection): break
            children=children[self.selection[depth]].get('children',{})
            depth+=1
        self.selector_frame.columnconfigure(1,weight=1)
        node=selected_node(self.selection)
        states=selection_states(self.selection)
        if not self.selection:
            hint='Blank world: main blend. Select a world to isolate its branch.'
        elif node.get('children'):
            mode='authored cycle' if len(states)==1 else '28-second sequential preview holds'
            hint=selection_title(self.selection)+' / All — '+mode+'. Blank = cycle this branch.'
        else:
            hint=selection_title(self.selection)+' — isolated. Clear a level to cycle its parent.'
        if self.color_scene():
            hint += '\nLive colors: Effects & layers > Palettes > Open live color inspector.'
        else:
            hint += ('\nPalette prototype: Planet Canvas only; independent of material.' if states == ['canvas'] else
                     '\nPalette prototype inactive. Select Cosmic / Planet canvas to review it.')
        self.selection_hint.set(hint)

    def refresh_palette(self):
        active = selection_states(self.selection) == ['canvas']
        self.palette_choice.set(PLANET_PALETTES[self.vars['planet_palette'].get()] if active else 'Authored')
        self.palette_box.configure(state='readonly' if active else 'disabled')
        self.palette_note.set(('Hold ' + PLANET_PALETTES[self.vars['planet_palette'].get()] + ' on next preview. Palette Authored is separate from list Authored.')
            if active else 'Planet palette parked. Hold Planet Canvas for its palette; declared source colors remain available in the live inspector.')
        self.compare_button.configure(state='normal' if active and self.process is None else 'disabled')
        if self.color_scene():
            if active:
                self.planet_controls.pack(fill='x')
                self.color_title.pack_forget();self.color_description.pack_forget()
            else:
                self.planet_controls.pack_forget()
                self.color_title.pack(anchor='w',before=self.color_button)
                self.color_description.pack(anchor='w',before=self.color_button)
            self.color_launcher.pack(fill='x')
            if self.active_color_scene is None: self.color_status.set('Colors apply to the next selected preview; start it to edit live.')
            elif self.active_color_scene != self.color_scene():
                self.color_status.set('The running preview uses its original scope. Compatible edits apply live; other targets stay parked.')
        else:
            self.color_launcher.pack_forget();self.planet_controls.pack(fill='x')
        if self.color_editor: self.color_editor.refresh()

    def change_palette(self, event=None):
        if selection_states(self.selection) != ['canvas']: return
        self.vars['planet_palette'].set(next(key for key, label in PLANET_PALETTES.items()
                                              if label == self.palette_choice.get()))
        self.refresh_palette()
        self.status.set('Planet Canvas palette set. Start preview to compare; material settings are preserved.')

    def build_layers(self):
        panel = self.layers_tab
        self.layer_heading = tk.StringVar()
        ttk.Label(panel, textvariable=self.layer_heading, font=('Segoe UI', 15)).pack(anchor='w')
        ttk.Label(panel, text='One saved list; list edits apply next preview. Supported scene colors edit live.',
                  wraplength=610).pack(anchor='w', pady=(4, 6))
        self.sections = ttk.Notebook(panel)
        self.sections.pack(fill='x')
        self.section_frames = {}
        for name in ('Materials', 'Shared FX', 'World details', 'Envelopers', 'Palettes'):
            frame = ttk.Frame(self.sections, padding=8)
            self.sections.add(frame, text=name)
            self.section_frames[name] = frame
        material = self.section_frames['Materials']
        ttk.Label(material, text='Isolation holds one material + enabled FX/details together; Cycle pauses.').pack(anchor='w')
        row = ttk.Frame(material); row.pack(fill='x', pady=4)
        self.isolate_choice = tk.StringVar(value=EFFECTS[MATERIALS[0]][0])
        ttk.Combobox(row, textvariable=self.isolate_choice, state='readonly', width=22,
                     values=[EFFECTS[key][0] for key in MATERIALS]).pack(side='left')
        ttk.Button(row, text='Isolate material', command=self.isolate_material).pack(side='left', padx=4)
        ttk.Button(row, text='Restore materials', command=self.restore_materials).pack(side='left')
        self.isolation_note = tk.StringVar()
        ttk.Label(material, textvariable=self.isolation_note, wraplength=560).pack(anchor='w')
        ttk.Label(self.section_frames['Shared FX'], wraplength=550, text=
            'Reusable treatments, filtered by catalog compatibility. Shared does not mean every form.\n'
            'Tunnel, Fractal folds, Horizon, field decorations and supported shooting stars.').pack(anchor='w')
        ttk.Label(self.section_frames['World details'], wraplength=550, text=
            'Features of the selected world: rings, moons, blossoms, rain and other details.\n'
            'Availability is world-level; individual forms may use only some features.').pack(anchor='w')
        ttk.Label(self.section_frames['Envelopers'], wraplength=550, text=
            'Transforms the completed image, including world details. One at a time when several are selected.\n'
            'Use Presets → Nine treatments for source-filled reviews; Solo whole list removes the other details.').pack(anchor='w')
        self.planet_controls = ttk.Frame(self.section_frames['Palettes'])
        self.planet_controls.pack(fill='x')
        palettes = self.planet_controls
        self.palette_choice = tk.StringVar()
        self.palette_box = ttk.Combobox(palettes, textvariable=self.palette_choice,
            values=list(PLANET_PALETTES.values()), state='disabled', width=24)
        self.palette_box.pack(anchor='w')
        self.palette_box.bind('<<ComboboxSelected>>', self.change_palette)
        ttk.Label(palettes, wraplength=560, text='Planet Canvas only. Affects planet surface and rings; moons and sky retain authored colors.').pack(anchor='w')
        self.palette_note = tk.StringVar()
        ttk.Label(palettes, textvariable=self.palette_note, wraplength=560).pack(anchor='w')
        self.compare_button = ttk.Button(palettes, text='Run matched A/B — first 30s of test track', command=self.start_comparison)
        self.compare_button.pack(anchor='w')
        self.color_launcher = ttk.Frame(self.section_frames['Palettes'])
        self.color_title=ttk.Label(self.color_launcher, text='Live scene color editing', font=('Segoe UI', 12))
        self.color_title.pack(anchor='w')
        self.color_description=ttk.Label(self.color_launcher, text='Only compatible targets are shown; other saved assignments stay parked. Material pigments remain independent.', wraplength=560)
        self.color_description.pack(anchor='w')
        self.color_button=ttk.Button(self.color_launcher, text='Open live color inspector…', command=self.open_color_inspector)
        self.color_button.pack(anchor='w',pady=4)
        ttk.Label(self.color_launcher, textvariable=self.color_status, wraplength=560).pack(anchor='w')
        self.sections.bind('<<NotebookTabChanged>>' , lambda event:self.refresh_layers())
        self.refresh_palette()
        picker = ttk.Frame(panel); picker.pack(fill='x')
        self.effect_category = tk.StringVar()
        self.effect_choice = tk.StringVar()
        self.category_box = ttk.Combobox(picker, textvariable=self.effect_category, state='readonly', width=18)
        self.category_box.pack(side='left', padx=(0, 8))
        self.effect_box = ttk.Combobox(picker, textvariable=self.effect_choice, state='readonly')
        self.effect_box.pack(side='left', fill='x', expand=True)
        self.add_button = ttk.Button(picker, text='Add', command=self.add_layer)
        self.add_button.pack(side='left', padx=(8, 0))
        self.category_box.bind('<<ComboboxSelected>>', lambda event:self.refresh_effect_picker())
        playback = ttk.Frame(panel); playback.pack(fill='x', pady=6)
        self.layer_mode = tk.StringVar(value='Authored')
        self.layer_hold = tk.StringVar(value='12')
        ttk.Label(playback, text='List playback').pack(side='left', padx=(0, 8))
        mode = ttk.Combobox(playback, textvariable=self.layer_mode, values=list(MODES.values()), state='readonly', width=18)
        mode.pack(side='left')
        mode.bind('<<ComboboxSelected>>', lambda event:self.change_layer_playback())
        ttk.Label(playback, text='Hold (seconds)').pack(side='left', padx=(16, 8))
        hold = ttk.Combobox(playback, textvariable=self.layer_hold, values=('4', '8', '12', '20', '22', '28', '36', '60'), state='readonly', width=5)
        hold.pack(side='left')
        hold.bind('<<ComboboxSelected>>', lambda event:self.change_layer_playback())
        ttk.Label(panel, text='Saved combined cycle order — all sections; not separate render passes').pack(anchor='w')
        table_frame = ttk.Frame(panel); table_frame.pack(fill='both', expand=True)
        self.layer_table = ttk.Treeview(table_frame, columns=('on', 'name', 'category'), show='headings', height=4, selectmode='browse')
        for key, title, width in (('on', 'Enabled', 70), ('name', 'Effect / cycle order', 260), ('category', 'Category', 120)):
            self.layer_table.heading(key, text=title)
            self.layer_table.column(key, width=width, minwidth=60, stretch=key != 'on')
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.layer_table.yview)
        self.layer_table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.layer_table.pack(fill='both', expand=True)
        self.layer_table.bind('<Double-1>', lambda event:self.edit_layer('toggle'))
        actions = ttk.Frame(panel); actions.pack(fill='x', pady=10)
        for label, action in [('On / off', 'toggle'), ('Solo whole list', 'solo'), ('Remove', 'remove'), ('Up', 'up'), ('Down', 'down')]:
            ttk.Button(actions, text=label, command=lambda a=action:self.edit_layer(a)).pack(side='left', padx=(0, 5))
        strength=ttk.Frame(panel);strength.pack(fill='x')
        ttk.Label(strength,text='Selected new spatial / Enveloper amount (0–1)').pack(side='left')
        self.treatment_amount=tk.StringVar(value='1')
        ttk.Spinbox(strength,textvariable=self.treatment_amount,from_=0,to=1,increment=.1,width=5).pack(side='left',padx=6)
        ttk.Button(strength,text='Apply amount',command=self.change_treatment_amount).pack(side='left')
        self.layer_table.bind('<<TreeviewSelect>>',self.show_treatment_amount)
        self.layer_note = tk.StringVar()
        ttk.Label(panel, textvariable=self.layer_note, wraplength=600).pack(anchor='w')
        ttk.Button(panel, text='Back to preview', command=lambda:self.tabs.select(self.preview)).pack(anchor='w', pady=(4, 0))

    def layer_world(self):
        return world_for_state(LIVE_STATES[selection_states(self.selection)[0]])

    def refresh_effect_picker(self):
        world = self.layer_world()
        section = self.sections.tab(self.sections.select(), 'text')
        names = [info[0] for key, info in EFFECTS.items() if world in info[2] and info[1] == self.effect_category.get()
                 and (section == 'Palettes' or effect_section(key) == section)]
        self.effect_box.configure(values=names, state='disabled' if section == 'Palettes' else 'readonly')
        if self.effect_choice.get() not in names: self.effect_choice.set(names[0] if names else '')

    def refresh_layers(self, focus=None):
        world = self.layer_world()
        profile = self.layer_profiles.get(world, default_profile(world))
        self.layer_heading.set(selection_title(self.selection))
        section = self.sections.tab(self.sections.select(), 'text')
        categories = list(dict.fromkeys(info[1] for key, info in EFFECTS.items() if world in info[2] and (section == 'Palettes' or effect_section(key) == section)))
        self.category_box.configure(values=categories, state='disabled' if section == 'Palettes' else 'readonly')
        self.add_button.configure(state='disabled' if section == 'Palettes' else 'normal')
        if self.effect_category.get() not in categories: self.effect_category.set(categories[0] if categories else '')
        self.refresh_effect_picker()
        isolated = self.material_isolation.get(world)
        if isolated: self.isolate_choice.set(EFFECTS[isolated][0])
        self.isolation_note.set(('Holding ' + EFFECTS[isolated][0] + '; saved list parked. Restore materials resumes it.') if isolated else 'No isolation. Solo whole list also disables FX and details.')
        self.layer_mode.set(MODES[profile['mode']])
        self.layer_hold.set(f"{profile['seconds']:g}")
        self.layer_table.delete(*self.layer_table.get_children())
        for item in profile['items']:
            label, _, _ = EFFECTS[item['id']]
            category = effect_section(item['id'])
            self.layer_table.insert('', 'end', iid=item['id'], values=('Yes' if item['enabled'] else 'No', label, category))
        if focus and self.layer_table.exists(focus):
            self.layer_table.selection_set(focus); self.layer_table.see(focus)
        note = ('Isolation active: saved material flags/playback are parked; enabled FX/details stay on. ' if isolated else
                ('Main Authored uses seven materials and paced spatial/Enveloper passages. ' if world=='blend' else 'Authored uses the original visuals; this list is parked. ') if profile['mode'] == 'authored' else
                'Only enabled effects run. An empty list shows the base form. ')
        note += 'Up / Down sets cycle order. Meld fades during the last 35% of each hold.'
        self.layer_note.set(note)

    def isolate_material(self):
        world = self.layer_world()
        profile = self.layer_profiles.get(world, default_profile(world))
        if profile['mode'] == 'authored':
            self.status.set('Choose Selected together or Meld materials and add desired FX/details first; then isolate.')
            return
        self.material_isolation[world] = next(key for key in MATERIALS if EFFECTS[key][0] == self.isolate_choice.get())
        self.refresh_layers()
        self.status.set('Material isolated on next preview. Enabled FX/details stay on; saved Cycle/meld is parked.')

    def restore_materials(self):
        self.material_isolation.pop(self.layer_world(), None)
        self.refresh_layers()
        self.status.set('Previous material selection and list playback restored for next preview.')

    def change_layer_playback(self):
        profile = self.layer_profiles.setdefault(self.layer_world(), default_profile(self.layer_world()))
        profile['mode'] = next(key for key, label in MODES.items() if label == self.layer_mode.get())
        if profile['mode'] == 'authored': self.material_isolation.pop(self.layer_world(), None)
        profile['seconds'] = float(self.layer_hold.get())
        self.refresh_layers()

    def add_layer(self):
        key = next((key for key, info in EFFECTS.items() if info[0] == self.effect_choice.get()), None)
        if key is None: return
        profile = self.layer_profiles.setdefault(self.layer_world(), default_profile(self.layer_world()))
        if not any(item['id'] == key for item in profile['items']):
            profile['items'].append(dict(id=key, enabled=True))
        if profile['mode'] == 'authored': profile['mode'] = 'together'
        self.refresh_layers(key)

    def edit_layer(self, action):
        selected = self.layer_table.selection()
        if not selected: return
        key = selected[0]
        profile = self.layer_profiles.setdefault(self.layer_world(), default_profile(self.layer_world()))
        items = profile['items']
        index = next(i for i, item in enumerate(items) if item['id'] == key)
        if action == 'remove': items.pop(index)
        elif action == 'toggle': items[index]['enabled'] = not items[index]['enabled']
        elif action == 'solo':
            self.material_isolation.pop(self.layer_world(), None)
            for item in items: item['enabled'] = item['id'] == key
            profile['mode'] = 'together'
        elif action in ('up', 'down'):
            other = index + (-1 if action == 'up' else 1)
            if 0 <= other < len(items): items[index], items[other] = items[other], items[index]
        if profile['mode'] == 'authored': profile['mode'] = 'together'
        self.refresh_layers(key)

    def show_treatment_amount(self,event=None):
        selected=self.layer_table.selection()
        if selected:
            profile=self.layer_profiles.get(self.layer_world(),default_profile(self.layer_world()))
            item=next((item for item in profile['items'] if item['id']==selected[0]),{})
            self.treatment_amount.set(str(item.get('amount',1.)))

    def change_treatment_amount(self):
        selected=self.layer_table.selection()
        if not selected or selected[0] not in SPATIAL_TREATMENTS+ENVELOPERS:
            self.status.set('Select a new spatial effect or Enveloper row to change its amount.');return
        from copy import deepcopy
        world=self.layer_world();profile=deepcopy(self.layer_profiles.get(world,default_profile(world)))
        try:
            item=next(item for item in profile['items'] if item['id']==selected[0])
            item['amount']=float(self.treatment_amount.get())
            clean=validate_layers({world:profile})
        except ValueError as exc:self.status.set(str(exc));return
        self.layer_profiles.update(clean);self.refresh_layers(selected[0])
        self.status.set('Treatment amount saved for the next preview. Zero bypasses it.')

    def review_treatment(self,key):
        # Explicit user-invoked review preset; other worlds and colors stay parked.
        self.select(['cosmic','canvas'])
        keys=(key,) if key in MATERIALS else ('cellular_mosaic',key)
        self.layer_profiles['cosmic']=dict(mode='together',seconds=22.,items=[dict(id=k,enabled=True) for k in keys+('stars','rings','moons')])
        self.material_isolation.pop('cosmic',None)
        self.refresh_layers(key);self.tabs.select(self.preview)
        self.status.set('Review '+EFFECTS[key][0]+': Planet Canvas with rings, moons and stars. Choose any normal preview input.')

    def review_main(self):
        self.select([]);self.material_isolation.pop('blend',None)
        self.layer_profiles['blend']=dict(mode='authored',seconds=22.,items=[])
        self.refresh_layers();self.tabs.select(self.preview)
        self.status.set('Main Authored: seven materials; spatial and Enveloper passages with untreated gaps.')

    def menus(self):
        bar=tk.Menu(self.root)
        file=tk.Menu(bar,tearoff=False)
        for label,fn in [('New session',self.new),('Load session…',self.load),('Save session',self.save),
                         ('Save session as…',lambda:self.save(True)),('Close',self.close)]:
            file.add_command(label=label,command=fn)
        bar.add_cascade(label='File',menu=file)
        edit=tk.Menu(bar,tearoff=False)
        edit.add_command(label='Choose test track…',command=self.choose_track)
        speed=tk.Menu(edit,tearoff=False)
        for label in SPEEDS:
            speed.add_radiobutton(label=label,variable=self.vars['speed'],value=label)
        edit.add_cascade(label='Replay speed',menu=speed)
        bar.add_cascade(label='Edit',menu=edit)
        view=tk.Menu(bar,tearoff=False)
        view.add_command(label='Build & preview',command=lambda:self.tabs.select(self.preview))
        view.add_command(label='Effects & layers',command=lambda:self.tabs.select(self.layers_tab))
        view.add_command(label='Library',command=lambda:self.tabs.select(self.library_tab))
        view.add_command(label='Review',command=lambda:self.tabs.select(self.results))
        view.add_command(label='Latest results folder',command=self.open_results)
        bar.add_cascade(label='View',menu=view)
        presets=tk.Menu(bar,tearoff=False)
        presets.add_command(label='Main blend',command=lambda:self.select([]))
        presets.add_command(label='Material trio — all worlds',command=self.material_trio)
        treatments=tk.Menu(presets,tearoff=False)
        for key in NEW_MATERIALS+SPATIAL_TREATMENTS+ENVELOPERS:
            treatments.add_command(label=EFFECTS[key][0],command=lambda k=key:self.review_treatment(k))
        treatments.add_separator()
        treatments.add_command(label='Main — authored seven-material show',command=self.review_main)
        presets.add_cascade(label='Nine treatments',menu=treatments)
        def add_presets(menu,children,path):
            for key,node in children.items():
                selection=path+[key]
                if node.get('children'):
                    nested=tk.Menu(menu,tearoff=False)
                    nested.add_command(label='All / cycle',command=lambda p=selection:self.select(p))
                    add_presets(nested,node['children'],selection)
                    menu.add_cascade(label=node['label'],menu=nested)
                else:
                    menu.add_command(label=node['label'],command=lambda p=selection:self.select(p))
        add_presets(presets,WORLD_TREE,[])
        bar.add_cascade(label='Presets',menu=presets)
        transfer=tk.Menu(bar,tearoff=False)
        transfer.add_command(label='Import session…',command=self.load)
        transfer.add_command(label='Export session…',command=lambda:self.save(True))
        bar.add_cascade(label='Import / export',menu=transfer)
        self.root.config(menu=bar)

    def material_quartet(self):
        self.material_isolation = {}
        self.layer_profiles = {world: material_quartet_profile(world) for world in WORLDS}
        self.refresh_layers()
        self.tabs.select(self.layers_tab)

    def material_trio(self):
        self.material_isolation = {}
        self.layer_profiles = {world: material_trio_profile(world) for world in WORLDS}
        self.refresh_layers()
        self.status.set('Three materials meld across every world. Select a held form or Main blend, then start preview.')

    def new(self):
        for key,value in DEFAULTS.items(): self.vars[key].set(value)
        available=tracks()
        if available: self.vars['track'].set(str(available[0]))
        self.session_path=None
        self.layer_profiles={}
        self.material_isolation={}
        self.color_overrides={}
        self.select(DEFAULT_SELECTION)
        self.status.set('New session. Any running preview keeps its current settings.')

    def choose_track(self):
        path=filedialog.askopenfilename(initialdir=ROOT/'work/audio-replay',filetypes=[('Decoded WAV','*.wav')])
        if path:
            self.vars['track'].set(path)
            self.track_box.configure(values=sorted(set(self.track_box['values']) | {path}))

    def load(self):
        path=filedialog.askopenfilename(filetypes=[('ZeraWave session','*.json')])
        if not path:return
        try:
            values=validate_session(json.loads(Path(path).read_text(encoding='utf-8')))
            for key,value in values.items():
                if key in self.vars:self.vars[key].set(value)
            self.layer_profiles=values['layers']
            self.material_isolation=values.get('material_isolation', {})
            self.color_overrides=values.get('color_overrides', {})
            self.select(values['selection'])
            self.schedule_colors()
            self.session_path=Path(path)
            self.status.set('Session loaded. Start preview to use these settings.')
        except (OSError, ValueError, TypeError) as exc:messagebox.showerror('Cannot load session',str(exc))

    def save(self,save_as=False):
        path=self.session_path
        if save_as or path is None:
            selected=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('ZeraWave session','*.json')])
            if not selected:return
            path=Path(selected)
        try:
            path.write_text(json.dumps(dict(version=3,**self.values()),indent=2),encoding='utf-8')
            self.session_path=path
            self.status.set('Session saved. It stores preview settings, not shader code or audio files.')
        except OSError as exc:messagebox.showerror('Cannot save session',str(exc))

    def color_scene(self):
        states=selection_states(self.selection)
        scope=states[0] if len(states)==1 else 'blend'
        return scope if targets_for(scope) else None

    def color_preset_folder(self):
        return ROOT/'work/color-presets'

    def open_color_inspector(self):
        scene=self.color_scene()
        if not scene: return
        if self.color_editor:
            if self.color_editor.scene==scene:
                self.color_editor.window.lift();return
            self.color_editor.close()
        self.color_editor=ColorInspector(self,scene)

    def set_color_setup(self, values):
        self.color_overrides=validate_colors(values)
        self.schedule_colors()

    def schedule_colors(self):
        if self.color_link and self.process and self.process.poll() is None:
            self.color_status.set('Color change pending — coalescing rapid edits.')
            # A bounded cadence, not endless trailing debounce: dragging keeps updating.
            if self.color_send_after is None:
                self.color_send_after=self.root.after(75,self.send_colors)
        else:
            if self.color_send_after is not None:self.root.after_cancel(self.color_send_after)
            self.color_send_after=None
            self.color_status.set('Current setup updated; applies on the next compatible preview. Save a preset/session to keep it.')

    def send_colors(self):
        self.color_send_after=None
        if self.color_link and self.process and self.process.poll() is None:
            self.last_color_revision=self.color_link.submit(scene_colors(self.color_overrides,self.active_color_scene))
            self.color_status.set('Color update sent; waiting for the running preview to apply it.' if self.last_color_revision is not None
                else 'Live color channel closed; current setup is retained for the next preview.')

    def run_folder(self):
        return ROOT/'work/studio'/(time.strftime('%Y%m%d-%H%M%S')+f'-{time.time_ns()%1000000000:09}')

    def launch(self, values, output, label=None):
        args = command(values, output)
        if label:
            args += ['--seed', '7301', '--comparison-label', label]
            self.comparison_label = label
        selected_states=selection_states(values['selection'])
        live_scene=selected_states[0] if len(selected_states)==1 else 'blend'
        live_scene = live_scene if targets_for(live_scene) and not label else None
        if live_scene: args += ['--studio-color-input']
        output.mkdir(parents=True)
        (output/'preview.json').write_text(json.dumps(dict(version=3, **values), indent=2), encoding='utf-8')
        self.log = (output/'run.log').open('w', encoding='utf-8')
        try:
            self.process = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE if live_scene else self.log,
                stdin=subprocess.PIPE if live_scene else None, stderr=subprocess.STDOUT, bufsize=0,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError:
            self.log.close(); self.log = None
            raise
        self.active_color_scene=live_scene
        self.preview_start_colors=deepcopy(values.get('color_overrides', {})) if live_scene else {}
        self.last_color_ack=None
        if live_scene:
            self.color_link=ColorLink(self.process,self.log)
            self.last_color_revision=self.color_link.submit(scene_colors(self.preview_start_colors,live_scene))
            self.color_status.set('Starting color preview; waiting for acknowledgement.')
        self.output = self.comparison_folder if label else output
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.refresh_palette()
        palette = PLANET_PALETTES[values['planet_palette']] if selection_states(values['selection']) == ['canvas'] else 'Authored (prototype inactive)'
        self.active_preview.set(('Active matched ' + label if label else 'Active preview') + ' — ' + palette)
        if live_scene: self.active_preview.set('Active color preview — compatible colors editable live; layers/input apply next preview.')
        self.status.set(('Matched ' + label + ' — ' if label else 'Running — ') + palette +
            ('; decoded replay from zero, fresh history. Do not resize/close early. Controls affect next preview.' if label else
             '; controls affect next preview. Live runs are not matched comparisons.'))
        if live_scene: self.status.set('Running color preview. Open Palettes > live color inspector; colors apply live, other settings apply next preview.')

    def start(self):
        if self.process is not None: return
        try: self.launch(self.values(), self.run_folder())
        except (OSError, ValueError) as exc: messagebox.showerror('Cannot start preview', str(exc))

    def start_comparison(self):
        if self.process is not None: return
        try:
            pair = comparison_runs(self.values())
            self.comparison_input = pair[0][1]['track']
            self.comparison_digest, self.comparison_frames = replay_identity(self.comparison_input)
            self.comparison_folder = self.run_folder()
            self.comparison_folder.mkdir(parents=True)
            (self.comparison_folder/'comparison.json').write_text(json.dumps(dict(
                seed=7301, input_sha256=self.comparison_digest, expected_frames=self.comparison_frames, reset='Fresh process, analyzer, mapper, renderer and Echo history for each run',
                input='Same decoded WAV from zero, first 30 seconds or EOF; silent',
                status='running', runs=dict(pair)), indent=2), encoding='utf-8')
            self.comparison_queue = pair
            self.comparison_active = True
            self.next_comparison()
        except (OSError, ValueError, wave.Error, EOFError) as exc:
            self.comparison_result('failed')
            messagebox.showerror('Cannot compare palettes', str(exc))

    def next_comparison(self):
        if replay_identity(self.comparison_input)[0] != self.comparison_digest:
            raise ValueError('Track changed during comparison; start a new pair.')
        label, values = self.comparison_queue.pop(0)
        self.launch(values, self.comparison_folder/label, label)

    def comparison_result(self, status):
        if self.comparison_active:
            path = self.comparison_folder/'comparison.json'
            data = json.loads(path.read_text(encoding='utf-8'))
            data['status'] = status
            path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        self.comparison_active = False
        self.comparison_queue = []

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.status.set('Stopped. Partial results remain; comparison cancelled.')
        self.comparison_result('cancelled')
        self.finish()

    def finish(self):
        if self.color_send_after is not None:
            self.root.after_cancel(self.color_send_after);self.color_send_after=None
        if self.color_link:
            self.color_link.close();self.color_link=None;self.log=None
        if self.log: self.log.close(); self.log = None
        self.active_color_scene=None
        self.process = None
        self.active_preview.set('No preview running.')
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.refresh_palette()

    def poll(self):
        if self.color_link:
            status=self.color_link.get_status()
            if status and status!=self.last_color_ack:
                self.last_color_ack=status
                if 'error' in status:self.color_status.set('Last valid colors retained: '+status['error'])
                elif status.get('applied')==self.last_color_revision and self.color_send_after is None:
                    self.color_status.set('Applied live to the running preview. Animation and history continue; other controls apply next preview.')
        if self.process is not None and self.process.poll() is not None:
            code = self.process.returncode
            self.finish()
            if self.comparison_active and code == 0:
                try:
                    if replay_identity(self.comparison_input)[0] != self.comparison_digest:
                        raise ValueError('Track changed during comparison.')
                    completed_comparison_run(self.comparison_folder, self.comparison_label, self.comparison_frames)
                except (OSError, ValueError) as exc:
                    self.comparison_result('incomplete: ' + str(exc))
                    self.status.set(str(exc))
                    self.root.after(200, self.poll)
                    return
            if self.comparison_active and code == 0 and self.comparison_queue:
                try: self.next_comparison()
                except (OSError, ValueError) as exc:
                    self.comparison_result('failed')
                    self.status.set('Comparison failed: ' + str(exc))
            else:
                paired = self.comparison_active
                self.comparison_result('matched complete' if code == 0 else 'failed')
                self.status.set(('Matched A/B complete: A Authored, B Soft Dream. Same input/timing verified; session unchanged.' if paired else
                    'Preview completed. Review the saved results.') if code == 0 else f'Preview failed (code {code}). Read run.log.')
        self.root.after(200, self.poll)

    def open_results(self):
        folder=self.output or ROOT/'work/studio'
        folder.mkdir(parents=True,exist_ok=True)
        os.startfile(folder)

    def blend(self):
        self.select([])
        self.tabs.select(self.preview)
        self.status.set('Main blend selected. Choose a test track or live input and start preview.')

    def close(self):
        self.stop()
        self.root.destroy()


if __name__=='__main__':
    root=tk.Tk()
    Studio(root)
    root.mainloop()
