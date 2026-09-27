"""Development control window; launches the existing preview/replay/live entry points."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from live_visual_test import LIVE_STATES
from preview_layers import (EFFECTS, MODES, default_profile, validate_layers, world_for_state, material_trio_profile, WORLDS)

ROOT = Path(__file__).resolve().parents[2]
SPEEDS = {'Real time': 1., '2×': 2., '6×': 6., '12×': 12., 'Fastest': 0.}
SOURCES = ('Test track', 'Synthetic preview', 'Live system audio')
DEFAULTS = dict(state='water', source='Test track', track='', speed='12×',
                duration='Full track', captures=True)


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
        'geometry': dict(label='Geometry study', state='cosmic'),
    }),
    'transition': dict(label='Transition', state='transition'),
    'elements': dict(label='Elements', children={
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
        raise ValueError('This is not a supported DreamWave development session.')
    values = {key: data.get(key, value) for key, value in DEFAULTS.items()}
    selection = (path_for_state(values['state']) if data['version'] == 1
                 else data.get('selection'))
    states = selection_states(selection)
    values['layers'] = validate_layers(data.get('layers', {}) if data['version'] == 3 else {})
    values['selection'] = list(selection)
    values['state'] = states[0]
    if values['source'] not in SOURCES:
        raise ValueError('Unknown input source.')
    if values['speed'] not in SPEEDS or values['duration'] not in ('Full track', '30 seconds', '60 seconds'):
        raise ValueError('Unknown speed or duration.')
    if not isinstance(values['track'], str) or type(values['captures']) is not bool:
        raise ValueError('Invalid track or capture setting.')
    return values


def command(values, output):
    selection = values['selection'] if 'selection' in values else path_for_state(values['state'])
    states = selection_states(selection)
    state_args = ['--state', states[0]]
    if len(states) > 1: state_args += ['--states', *states]
    profiles = validate_layers(values.get('layers', {}))
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


class Studio:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.log = None
        self.output = None
        self.session_path = None
        self.layer_profiles = {}
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', background='#141a28', foreground='#e3eaf4', font=('Segoe UI', 10))
        style.configure('TNotebook.Tab', padding=(16, 8))
        style.map('TNotebook.Tab', background=[('selected', '#283951')])
        style.configure('TCombobox', fieldbackground='#233047', background='#283951')
        style.map('TCombobox', fieldbackground=[('readonly', '#233047')],
                  foreground=[('readonly', '#e3eaf4')])
        style.configure('TButton', padding=(12, 8), background='#283951')
        style.map('TButton', background=[('active', '#365775')])
        root.configure(background='#141a28')
        self.root.title('DreamWave — Development Studio')
        self.root.geometry('780x720')
        self.root.minsize(680, 700)
        self.vars = {k: (tk.BooleanVar(value=v) if isinstance(v, bool) else tk.StringVar(value=v))
                     for k, v in DEFAULTS.items()}
        available = tracks()
        if available:
            self.vars['track'].set(str(available[0]))
        self.status = tk.StringVar(value='Ready. Choose a world and a source, then start a preview.')
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill='both', expand=True, padx=18, pady=(18, 10))
        self.preview = ttk.Frame(self.tabs, padding=20)
        self.results = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(self.preview, text='Build & preview')
        self.layers_tab = ttk.Frame(self.tabs, padding=20)
        self.tabs.add(self.layers_tab, text='Effects & layers')
        self.tabs.add(self.results, text='Review')
        ttk.Label(self.preview, text='Explore a world before blending it into DreamWave',
                  font=('Segoe UI', 15)).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0,20))
        def field(row, label, key, options):
            ttk.Label(self.preview, text=label).grid(row=row,column=0,sticky='w',padx=(0,18),pady=8)
            widget = ttk.Combobox(self.preview,textvariable=self.vars[key],values=options,state='readonly')
            widget.grid(row=row,column=1,columnspan=2,sticky='ew')
            return widget
        self.selection = list(DEFAULT_SELECTION)
        self.selector_rows = []
        selector_shell = ttk.Frame(self.preview)
        selector_shell.grid(row=1,column=0,columnspan=3,sticky='ew',pady=(0,8))
        self.selector_canvas = tk.Canvas(selector_shell,height=150,highlightthickness=0,background='#141a28')
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
                        variable=self.vars['captures']).grid(row=6,column=1,columnspan=2,sticky='w',pady=8)
        ttk.Label(self.preview,textvariable=self.selection_hint,wraplength=610).grid(row=7,column=0,columnspan=3,sticky='w',pady=(4,32))
        ttk.Label(self.preview,text='Track replay is silent. Live input listens to your system audio.\n'
                  'Speed, duration and captures apply to test tracks. Changes apply on the next run.',
                  wraplength=610).grid(row=8,column=0,columnspan=3,sticky='w',pady=10)
        self.start_button = ttk.Button(self.preview,text='Start preview',command=self.start)
        self.start_button.grid(row=9,column=1,sticky='ew',pady=12,padx=(0,8))
        self.stop_button = ttk.Button(self.preview,text='Stop preview',command=self.stop,state='disabled')
        self.stop_button.grid(row=9,column=2,sticky='ew',pady=12)
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
        ttk.Label(root,textvariable=self.status,wraplength=740).pack(fill='x',padx=20,pady=(0,16))
        self.build_layers()
        self.refresh_layers()
        self.menus()
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.after(200,self.poll)

    def values(self):
        values = {k:v.get() for k,v in self.vars.items()}
        values.update(selection=list(self.selection), state=selection_states(self.selection)[0],
                      layers=validate_layers(self.layer_profiles))
        return values

    def select(self, selection):
        selection_states(selection)  # Validate before changing any controls.
        self.selection = list(selection)
        self.vars['state'].set(selection_states(selection)[0])
        self.rebuild_selectors()
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
        self.selection_hint.set(hint)

    def build_layers(self):
        panel = self.layers_tab
        self.layer_heading = tk.StringVar()
        ttk.Label(panel, textvariable=self.layer_heading, font=('Segoe UI', 15)).pack(anchor='w')
        ttk.Label(panel, text='Form = the world’s structure. Effect = an optional visual treatment.\n'
                  'Layers = this world’s saved effect list. Changes apply on the next preview.',
                  wraplength=610).pack(anchor='w', pady=(8, 14))
        picker = ttk.Frame(panel); picker.pack(fill='x')
        self.effect_category = tk.StringVar()
        self.effect_choice = tk.StringVar()
        self.category_box = ttk.Combobox(picker, textvariable=self.effect_category, state='readonly', width=18)
        self.category_box.pack(side='left', padx=(0, 8))
        self.effect_box = ttk.Combobox(picker, textvariable=self.effect_choice, state='readonly')
        self.effect_box.pack(side='left', fill='x', expand=True)
        ttk.Button(picker, text='Add', command=self.add_layer).pack(side='left', padx=(8, 0))
        self.category_box.bind('<<ComboboxSelected>>', lambda event:self.refresh_effect_picker())
        playback = ttk.Frame(panel); playback.pack(fill='x', pady=12)
        self.layer_mode = tk.StringVar(value='Authored')
        self.layer_hold = tk.StringVar(value='12')
        ttk.Label(playback, text='Playback').pack(side='left', padx=(0, 8))
        mode = ttk.Combobox(playback, textvariable=self.layer_mode, values=list(MODES.values()), state='readonly', width=20)
        mode.pack(side='left')
        mode.bind('<<ComboboxSelected>>', lambda event:self.change_layer_playback())
        ttk.Label(playback, text='Hold (seconds)').pack(side='left', padx=(16, 8))
        hold = ttk.Combobox(playback, textvariable=self.layer_hold, values=('4', '8', '12', '20', '22', '28', '36', '60'), state='readonly', width=5)
        hold.pack(side='left')
        hold.bind('<<ComboboxSelected>>', lambda event:self.change_layer_playback())
        table_frame = ttk.Frame(panel); table_frame.pack(fill='both', expand=True)
        self.layer_table = ttk.Treeview(table_frame, columns=('on', 'name', 'category'), show='headings', height=9, selectmode='browse')
        for key, title, width in (('on', 'Enabled', 70), ('name', 'Effect / cycle order', 260), ('category', 'Category', 120)):
            self.layer_table.heading(key, text=title)
            self.layer_table.column(key, width=width, minwidth=60, stretch=key != 'on')
        scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.layer_table.yview)
        self.layer_table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y'); self.layer_table.pack(fill='both', expand=True)
        self.layer_table.bind('<Double-1>', lambda event:self.edit_layer('toggle'))
        actions = ttk.Frame(panel); actions.pack(fill='x', pady=10)
        for label, action in [('On / off', 'toggle'), ('Solo', 'solo'), ('Remove', 'remove'), ('Up', 'up'), ('Down', 'down')]:
            ttk.Button(actions, text=label, command=lambda a=action:self.edit_layer(a)).pack(side='left', padx=(0, 5))
        self.layer_note = tk.StringVar()
        ttk.Label(panel, textvariable=self.layer_note, wraplength=600).pack(anchor='w')
        ttk.Button(panel, text='Back to preview', command=lambda:self.tabs.select(self.preview)).pack(anchor='w', pady=(12, 0))

    def layer_world(self):
        return world_for_state(LIVE_STATES[selection_states(self.selection)[0]])

    def refresh_effect_picker(self):
        world = self.layer_world()
        names = [info[0] for info in EFFECTS.values() if world in info[2] and info[1] == self.effect_category.get()]
        self.effect_box.configure(values=names)
        if self.effect_choice.get() not in names: self.effect_choice.set(names[0] if names else '')

    def refresh_layers(self, focus=None):
        world = self.layer_world()
        profile = self.layer_profiles.get(world, default_profile(world))
        self.layer_heading.set(selection_title(self.selection))
        categories = list(dict.fromkeys(info[1] for info in EFFECTS.values() if world in info[2]))
        self.category_box.configure(values=categories)
        if self.effect_category.get() not in categories: self.effect_category.set(categories[0])
        self.refresh_effect_picker()
        self.layer_mode.set(MODES[profile['mode']])
        self.layer_hold.set(f"{profile['seconds']:g}")
        self.layer_table.delete(*self.layer_table.get_children())
        for item in profile['items']:
            label, category, _ = EFFECTS[item['id']]
            self.layer_table.insert('', 'end', iid=item['id'], values=('Yes' if item['enabled'] else 'No', label, category))
        if focus and self.layer_table.exists(focus):
            self.layer_table.selection_set(focus); self.layer_table.see(focus)
        note = ('Authored uses the original visuals; this list is parked. ' if profile['mode'] == 'authored' else
                'Only enabled effects run. An empty list shows the base form. ')
        note += 'Up / Down sets cycle order. Together keeps the shader’s composition order.\n'
        note += 'Meld materials fades selected materials in table order; other enabled effects stay on. '
        note += 'The last 35% of each hold blends into the next material.'
        if world == 'blend': note += '\nMain blend has its own list: defaults meld all three materials. Authored restores the earlier world sequence.'
        if self.vars['state'].get() == 'cosmic': note += '\nGeometry study uses only World details; use Planet canvas for material effects.'
        if world == 'water': note += '\nWater details are independent layers. Rain/rings apply to surface forms; foam, mist and highlights also apply to the waterfall.'
        self.layer_note.set(note)

    def change_layer_playback(self):
        profile = self.layer_profiles.setdefault(self.layer_world(), default_profile(self.layer_world()))
        profile['mode'] = next(key for key, label in MODES.items() if label == self.layer_mode.get())
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
            for item in items: item['enabled'] = item['id'] == key
            profile['mode'] = 'together'
        elif action in ('up', 'down'):
            other = index + (-1 if action == 'up' else 1)
            if 0 <= other < len(items): items[index], items[other] = items[other], items[index]
        if profile['mode'] == 'authored': profile['mode'] = 'together'
        self.refresh_layers(key)

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
        view.add_command(label='Review',command=lambda:self.tabs.select(self.results))
        view.add_command(label='Latest results folder',command=self.open_results)
        bar.add_cascade(label='View',menu=view)
        presets=tk.Menu(bar,tearoff=False)
        presets.add_command(label='Main blend',command=lambda:self.select([]))
        presets.add_command(label='Material trio — all worlds',command=self.material_trio)
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

    def material_trio(self):
        self.layer_profiles = {world: material_trio_profile(world) for world in WORLDS}
        self.refresh_layers()
        self.status.set('Three materials meld across every world. Select a held form or Main blend, then start preview.')

    def new(self):
        for key,value in DEFAULTS.items(): self.vars[key].set(value)
        available=tracks()
        if available: self.vars['track'].set(str(available[0]))
        self.session_path=None
        self.layer_profiles={}
        self.select(DEFAULT_SELECTION)
        self.status.set('New session. Any running preview keeps its current settings.')

    def choose_track(self):
        path=filedialog.askopenfilename(initialdir=ROOT/'work/audio-replay',filetypes=[('Decoded WAV','*.wav')])
        if path:
            self.vars['track'].set(path)
            self.track_box.configure(values=sorted(set(self.track_box['values']) | {path}))

    def load(self):
        path=filedialog.askopenfilename(filetypes=[('DreamWave session','*.json')])
        if not path:return
        try:
            values=validate_session(json.loads(Path(path).read_text(encoding='utf-8')))
            for key,value in values.items():
                if key in self.vars:self.vars[key].set(value)
            self.layer_profiles=values['layers']
            self.select(values['selection'])
            self.session_path=Path(path)
            self.status.set('Session loaded. Start preview to use these settings.')
        except (OSError, ValueError, TypeError) as exc:messagebox.showerror('Cannot load session',str(exc))

    def save(self,save_as=False):
        path=self.session_path
        if save_as or path is None:
            selected=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('DreamWave session','*.json')])
            if not selected:return
            path=Path(selected)
        try:
            path.write_text(json.dumps(dict(version=3,**self.values()),indent=2),encoding='utf-8')
            self.session_path=path
            self.status.set('Session saved. It stores preview settings, not shader code or audio files.')
        except OSError as exc:messagebox.showerror('Cannot save session',str(exc))

    def start(self):
        if self.process is not None:return
        output=ROOT/'work/studio'/time.strftime('%Y%m%d-%H%M%S')
        output=output.with_name(output.name+f'-{time.time_ns()%1000000:06}')
        try:
            args=command(self.values(),output)
            output.mkdir(parents=True)
            (output/'preview.json').write_text(json.dumps(dict(version=3,**self.values()),indent=2),encoding='utf-8')
            self.log=(output/'run.log').open('w',encoding='utf-8')
            self.process=subprocess.Popen(args,cwd=ROOT,stdout=self.log,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self.output=output
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            self.status.set('Running '+selection_title(self.selection)+' — close its visual window to finish cleanly.')
        except (OSError,ValueError) as exc:
            if self.log:self.log.close();self.log=None
            messagebox.showerror('Cannot start preview',str(exc))

    def stop(self):
        # Only the exact child launched by this studio is stopped.
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.status.set('Stopped. Partial captures/log remain; metrics finish only on normal window close.')
        self.finish()

    def finish(self):
        if self.log:self.log.close();self.log=None
        self.process=None
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')

    def poll(self):
        if self.process is not None and self.process.poll() is not None:
            code=self.process.returncode
            self.finish()
            self.status.set('Preview completed. Review the saved results.' if code==0 else
                            f'Preview failed (code {code}). Open latest results and read run.log.')
        self.root.after(200,self.poll)

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
