"""ZeraWave free-player panel. Owns one child using the existing live renderer."""
from collections import deque
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import uuid
import tkinter as tk
from tkinter import ttk

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT/'app/visuals', ROOT/'app/audio'):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from renderer import LIVE_FORMS
from world_catalog import main_entries
from player_state import defaults, validate_config, QUEUE_LIMIT
from transition_catalog import RECIPES
from capture import SourceEnumerator
from player_log import SessionLog, source_binding

DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'ZeraWave'
WORLDS = main_entries(LIVE_FORMS)
BY_ID = {row['id']: row for row in WORLDS}


def load_settings(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return validate_config(value, LIVE_FORMS)
    except FileNotFoundError:
        return defaults(LIVE_FORMS)
    except (OSError, ValueError, TypeError) as exc:
        value = defaults(LIVE_FORMS)
        value['queue'] = []
        value['_error'] = 'Saved preferences need repair: ' + str(exc)
        return value


def save_settings(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def source_label(source):
    kind = 'System audio (loopback)' if source['kind'] == 'loopback' else 'Microphone'
    return f"{kind} · {source['name']}"


def journal_runtime_event(log, runtime_session, pid, event):
    if 'control_ack' in event or 'state' not in event and 'capture_event' not in event:
        log.record('runtime_message', runtime_session=runtime_session, PID=pid,
                   payload={k:v for k,v in event.items() if k != 'state'})


def runtime_command():
    """Own the actual interpreter, avoiding Windows venv redirector orphans.

    Reuse the already running project's import paths, never install or modify
    the environment. The startup notice uses the same base-interpreter pattern.
    """
    executable = getattr(sys, '_base_executable', sys.executable)
    script = str(Path(__file__).resolve())
    bootstrap = ('import sys,runpy;sys.path[:]=' + repr(sys.path) +
                 ';sys.argv=' + repr([script, '--runtime']) +
                 ';runpy.run_path(' + repr(script) + ',run_name="__main__")')
    return [executable, '-X', 'utf8', '-u', '-c', bootstrap]


class Player:
    def __init__(self, root, data=None):
        self.root = root
        self.data = Path(data) if data else DATA
        self.data.mkdir(parents=True, exist_ok=True)
        self.settings = load_settings(self.data/'settings.json')
        self.process = None
        self.log = SessionLog(self.data)
        self.log.record('panel_source_binding', binding=source_binding(ROOT, ['app/player.py', 'app/audio/capture.py', 'app/player_log.py'], {'Player.source_changed': Player.source_changed, 'Player.receive': Player.receive, 'Player.poll': Player.poll}))
        self.events = queue.Queue(maxsize=128)
        self.outgoing = None
        self.serial = 0
        self.state = {}
        self.initializing = False
        self.startup_cancelled = False
        self.started_at = None
        self.options = {}
        self.refreshing = False
        self.enumerator = SourceEnumerator()
        self.enum_token = self.enum_seen = 0
        self.enumeration_notice = None
        self.desired_source = self.settings.get('source')
        self.active_source = None
        self.runtime_session = None
        self.stderr_worker = None
        self.keys_down = set()
        self.queue_ids = list(self.settings['queue'])
        self.previous_current = None
        self.closing = False
        self.panel_open = False
        self.status = tk.StringVar(value=self.settings.get('_error', 'Choose one audio source to begin.'))
        self.device = tk.StringVar()
        self.now = tk.StringVar(value='Your next world awaits')
        self.taxonomy = tk.StringVar(value='Approved Main · 27 worlds')
        self.phase = tk.StringVar(value='Not listening')
        self.queue_info = tk.StringVar()
        self.shuffle = tk.BooleanVar(value=self.settings['shuffle'])
        self.loop = tk.BooleanVar(value=self.settings['loop'])
        self.recent = tk.BooleanVar(value=self.settings['recent_history'])
        self.tips = tk.BooleanVar(value=self.settings['tips'])
        root.title('ZeraWave · Player')
        root.geometry('820x330')
        root.minsize(820, 330)
        root.configure(background='#141a28')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', background='#141a28', foreground='#e3eaf4', font=('Segoe UI', 10))
        style.configure('TButton', background='#283951', padding=(10, 7))
        style.map('TButton', background=[('active', '#354e6b')])
        style.configure('Accent.TButton', background='#36536f', font=('Segoe UI Semibold', 11))
        style.configure('Queue.TButton', padding=(8, 3))
        style.configure('Title.TLabel', font=('Segoe UI Semibold', 27))
        style.configure('Quiet.TLabel', foreground='#a6b7ce')
        style.configure('Now.TLabel', font=('Segoe UI Semibold', 17))
        style.configure('TEntry', fieldbackground='#233047', foreground='#e3eaf4', insertcolor='#e3eaf4')
        style.configure('TCombobox', fieldbackground='#233047', background='#283951')
        style.map('TCombobox', fieldbackground=[('readonly', '#233047')], foreground=[('readonly', '#e3eaf4')])
        root.option_add('*TCombobox*Listbox.background', '#233047')
        root.option_add('*TCombobox*Listbox.foreground', '#e3eaf4')
        self.box = ttk.Frame(root, padding=(22, 16))
        self.box.pack(fill='both', expand=True)
        header = ttk.Frame(self.box)
        header.pack(fill='x')
        ttk.Label(header, text='ZeraWave', style='Title.TLabel').pack(side='left')
        ttk.Label(header, text='YOUR SOUND BECOMES A WORLD', style='Quiet.TLabel').pack(side='right', pady=(12, 0))
        ttk.Label(self.box, text='ONE AUDIO SOURCE', style='Quiet.TLabel').pack(anchor='w', pady=(12, 4))
        source = ttk.Frame(self.box)
        source.pack(fill='x')
        self.devices = ttk.Combobox(source, textvariable=self.device, state='readonly')
        self.devices.pack(side='left', fill='x', expand=True)
        self.devices.bind('<<ComboboxSelected>>', self.source_changed)
        self.refresh_button = ttk.Button(source, text='Refresh', command=self.refresh)
        self.refresh_button.pack(side='left', padx=(8, 0))
        ttk.Label(self.box, text='Output loopback listens to that speaker/headphone endpoint. Microphone listens to its input.\nPer-app capture is unavailable. No recording or upload.', style='Quiet.TLabel').pack(anchor='w', pady=(5, 8))
        controls = ttk.Frame(self.box)
        controls.pack(fill='x')
        self.start_button = ttk.Button(controls, text='Start', style='Accent.TButton', command=self.start)
        self.start_button.pack(side='left')
        self.stop_button = ttk.Button(controls, text='Stop', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=6)
        self.pause_button = ttk.Button(controls, text='Pause', command=lambda: self.send('pause'), state='disabled')
        self.pause_button.pack(side='left')
        self.hold_button = ttk.Button(controls, text='Hold · press', state='disabled')
        self.hold_button.pack(side='left', padx=6)
        self.hold_button.bind('<ButtonPress-1>', self.press_hold)
        self.bonk_button = ttk.Button(controls, text='Bonk →', style='Accent.TButton', command=lambda: self.send('bonk'), state='disabled')
        self.bonk_button.pack(side='left')
        self.queue_toggle = ttk.Button(controls, text='Queue & preferences', command=self.show_panel)
        self.queue_toggle.pack(side='right')
        self.progress = ttk.Progressbar(self.box, mode='indeterminate')
        self.status_label = ttk.Label(self.box, textvariable=self.status, wraplength=765)
        self.status_label.pack(anchor='w', pady=(10, 0))
        self.panel = ttk.Frame(self.box)
        self.build_panel()
        self.refresh()
        self.update_queue()
        root.protocol('WM_DELETE_WINDOW', self.close)
        # Run focused shortcuts before a button's default Space binding, so
        # Space Bonk can never accidentally invoke Start/Stop/Pause.
        tag = 'ZeraWavePlayerShortcuts' + str(root.winfo_id())
        root.bind_class(tag, '<KeyPress>', self.key_press)
        root.bind_class(tag, '<KeyRelease>', self.key_release)
        def tag_widgets(widget):
            widget.bindtags((tag, *widget.bindtags()))
            for child in widget.winfo_children():
                tag_widgets(child)
        tag_widgets(root)
        root.bind('<FocusOut>', lambda event: root.after_idle(self.focus_check))
        root.bind('<ButtonRelease-1>', self.release_hold)
        root.after(80, self.poll)

    def build_panel(self):
        ttk.Separator(self.panel).pack(fill='x', pady=12)
        ttk.Label(self.panel, text='NOW SHOWING', style='Quiet.TLabel').pack(anchor='w')
        ttk.Label(self.panel, textvariable=self.now, style='Now.TLabel', wraplength=765).pack(anchor='w', pady=(3, 0))
        ttk.Label(self.panel, textvariable=self.taxonomy, style='Quiet.TLabel', wraplength=765).pack(anchor='w')
        ttk.Label(self.panel, textvariable=self.phase, style='Quiet.TLabel', wraplength=765).pack(anchor='w', pady=(3, 10))
        row = ttk.Frame(self.panel)
        row.pack(fill='x')
        ttk.Label(row, text='WORLD LIBRARY', style='Quiet.TLabel').pack(side='left')
        self.search = tk.StringVar()
        search = ttk.Entry(row, textvariable=self.search, width=20)
        search.pack(side='right')
        self.search.trace_add('write', lambda *args: self.filter_library())
        ttk.Label(row, text='Search ', style='Quiet.TLabel').pack(side='right')
        lists = ttk.Frame(self.panel)
        lists.pack(fill='both', expand=True, pady=(5, 4))
        lists.columnconfigure(0, weight=1)
        lists.columnconfigure(2, weight=1)
        lists.rowconfigure(0, weight=1)
        self.library = self.listbox(lists, 0, 'extended')
        actions = ttk.Frame(lists)
        actions.grid(row=0, column=1, sticky='ns', padx=8)
        for text, command in [('Add →', self.add), ('Use subset', self.subset), ('Solo', self.solo), ('All Main', self.all_main)]:
            ttk.Button(actions, text=text, command=command, style='Queue.TButton').pack(fill='x', pady=3)
        self.queue_list = self.listbox(lists, 2, 'extended')
        edits = ttk.Frame(self.panel)
        edits.pack(fill='x')
        for text, command in [('↑', lambda: self.move(-1)), ('↓', lambda: self.move(1)), ('Remove', self.remove), ('Clear', self.clear_queue)]:
            ttk.Button(edits, text=text, command=command).pack(side='left', padx=(0, 4))
        ttk.Label(edits, textvariable=self.queue_info, style='Quiet.TLabel').pack(side='right')
        prefs = ttk.Frame(self.panel)
        prefs.pack(fill='x', pady=(9, 4))
        for text, variable in [('Shuffle', self.shuffle), ('Loop ordered queue', self.loop), ('Avoid recent worlds', self.recent), ('Show control tips', self.tips)]:
            ttk.Checkbutton(prefs, text=text, variable=variable, command=self.draft_changed).pack(side='left', padx=(0, 12))
        self.apply_button = ttk.Button(self.panel, text='Apply queue & preferences', style='Accent.TButton', command=self.apply_queue)
        self.apply_button.pack(anchor='w', pady=(4, 4))
        ttk.Label(self.panel, text='Duplicates allowed · 50-entry limit · edits take effect at the next world boundary.\nShuffle continues until Stop; Loop applies only to ordered playback.', style='Quiet.TLabel').pack(anchor='w')
        self.tip_label = ttk.Label(self.panel, text='Focused windows: Space Bonk · Shift Hold · Ctrl+Enter Start · Ctrl+S Stop · Ctrl+P Pause\nOutput: F11 fullscreen · Esc close. Text entry keeps normal typing.', style='Quiet.TLabel')
        footer = self.footer = ttk.Frame(self.panel)
        footer.pack(fill='x', pady=(10, 0))
        ttk.Label(footer, text='Visual canvas stays clean. Controls live here.', style='Quiet.TLabel').pack(side='left')
        ttk.Button(footer, text='Open log', command=lambda: os.startfile(self.data)).pack(side='right')
        self.filter_library()

    def listbox(self, parent, column, selectmode):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky='nsew')
        box = tk.Listbox(frame, height=8, selectmode=selectmode, exportselection=False,
                         bg='#1c273b', fg='#e3eaf4', selectbackground='#3d5779',
                         relief='flat', highlightthickness=1, highlightbackground='#34445d',
                         font=('Segoe UI', 10), activestyle='none')
        bar = ttk.Scrollbar(frame, command=box.yview)
        bar.pack(side='right', fill='y')
        box.configure(yscrollcommand=bar.set)
        box.pack(side='left', fill='both', expand=True)
        return box

    def show_panel(self):
        if not self.panel_open:
            self.panel_open = True
            self.panel.pack(fill='both', expand=True)
            self.root.geometry('820x850')
            self.root.minsize(820, 850)
            self.queue_toggle.configure(state='disabled')
        self.update_tips()

    def filter_library(self):
        query = self.search.get().casefold()
        self.visible_worlds = [row for row in WORLDS if query in ' '.join((row['name'], row['category'], row['subcategory'])).casefold()]
        self.library.delete(0, 'end')
        for row in self.visible_worlds:
            self.library.insert('end', row['name'] + ' · ' + (row['subcategory'] if row['subcategory'] != '—' else row['category']))

    def selection(self):
        return [self.visible_worlds[i]['id'] for i in self.library.curselection()]

    def add(self):
        selected = self.selection()
        if not selected:
            self.status.set('Select a world from the library first.')
            return
        if len(self.queue_ids) + len(selected) > QUEUE_LIMIT:
            self.status.set('Queue limit is 50. Remove entries before adding more.')
            return
        self.queue_ids += selected
        self.update_queue()
        self.draft_changed()

    def subset(self):
        selected = self.selection()
        if not selected:
            self.status.set('Select one or more worlds for a subset.')
            return
        self.queue_ids = selected
        self.update_queue()
        self.draft_changed()

    def solo(self):
        selected = self.selection()
        if len(selected) != 1:
            self.status.set('Select exactly one world for Solo.')
            return
        self.queue_ids = selected
        self.update_queue()
        self.draft_changed()

    def all_main(self):
        self.queue_ids = list(LIVE_FORMS)
        self.update_queue()
        self.draft_changed()

    def remove(self):
        for i in reversed(self.queue_list.curselection()):
            self.queue_ids.pop(i)
        self.update_queue()
        self.draft_changed()

    def clear_queue(self):
        self.queue_ids = []
        self.update_queue()
        self.draft_changed()

    def move(self, delta):
        selected = self.queue_list.curselection()
        if len(selected) != 1:
            self.status.set('Select one queue entry to move.')
            return
        i = selected[0]
        target = i + delta
        if 0 <= target < len(self.queue_ids):
            self.queue_ids[i], self.queue_ids[target] = self.queue_ids[target], self.queue_ids[i]
            self.update_queue()
            self.queue_list.selection_set(target)
            self.draft_changed()

    def update_queue(self):
        self.queue_list.delete(0, 'end')
        for i, state in enumerate(self.queue_ids, 1):
            self.queue_list.insert('end', f"{i:02}  {BY_ID[state]['name']}")
        self.queue_info.set(f'{len(self.queue_ids)} / 50 entries')

    def draft_changed(self):
        self.status.set('Queue draft changed. Apply to use it.' if self.queue_ids else 'Queue is empty. Add worlds or choose All Main before Start.')
        self.update_tips()
        self.update_controls()

    def config(self):
        return validate_config(dict(self.settings, queue=self.queue_ids, shuffle=self.shuffle.get(),
                                    loop=self.loop.get(), recent_history=self.recent.get(), tips=self.tips.get()), LIVE_FORMS)

    def persist(self):
        try:
            save_settings(self.data/'settings.json', self.settings)
        except OSError as exc:
            self.status.set('Could not save preferences: ' + str(exc))

    def apply_queue(self):
        try:
            config = self.config()
        except ValueError as exc:
            self.status.set(str(exc))
            return False
        self.settings = config
        self.persist()
        if self.process:
            self.send('configure', config=config)
            self.status.set('Queue applied for the next world boundary. Current world continues.')
        else:
            self.status.set('Queue ready. Choose an audio source and Start.')
        return True

    def record(self, event, **detail):
        if self.log is not None:
            self.log.record(event, runtime_session=self.runtime_session, **detail)

    def refresh(self):
        if self.closing:
            return
        self.enum_token = self.enumerator.request()
        self.refreshing = True
        self.enumeration_notice = 'Refreshing audio endpoints…'
        self.status.set(self.state.get('restart_notice') or self.enumeration_notice)
        self.refresh_button.configure(text='Refreshing…', state='normal')
        self.record('enumeration_requested', token=self.enum_token)

    def drain_enumeration(self):
        result = self.enumerator.snapshot()
        if result is None or result['token'] < self.enum_token or result['token'] <= self.enum_seen:
            return
        self.enum_seen = result['token']
        self.receive(dict(sources=result['sources'], enumeration_error=result['error']))

    def source_changed(self, event=None):
        # <<ComboboxSelected>> is the commit gesture. Quiet .set()/population,
        # restore, Refresh and dismissing the popup never call capture commands.
        if event is None or getattr(event, 'widget', None) is not self.devices:
            return
        source = self.options.get(self.device.get())
        if source is None:
            return
        previous = self.desired_source
        if self.process is not None and not self.send('switch_source', source=source):
            self.set_selected_source(previous)
            self.status.set('Source change was not submitted. Select again when the control channel is ready.')
            return
        self.desired_source = dict(source)
        self.enumeration_notice = None
        self.record('user_endpoint_selection', requested=self.desired_source, active=self.active_source)
        self.status.set(self.state.get('restart_notice') or 'Selected ' + source_label(source) + '. ' + ('Switching capture; world and Pause retained.' if self.state.get('running') else 'Start when ready.'))
        self.update_controls()

    def selected_source(self):
        return self.desired_source

    def set_selected_source(self, source):
        # Programmatic identity/display restoration only; never sends commands.
        self.desired_source = dict(source) if source else None
        if source is None:
            self.device.set('')
            return
        label = next((name for name, value in self.options.items()
                      if value['id'] == source['id'] and value['kind'] == source['kind']), None)
        if label is None:
            label = source_label(source) + ' (unavailable)'
            self.options[label] = dict(source)
            self.devices.configure(values=list(self.options))
        self.device.set(label)

    def receive_sources(self, sources, error=None):
        selected = self.desired_source
        self.refreshing = False
        self.refresh_button.configure(text='Refresh', state='normal')
        if error:
            self.enumeration_notice = 'Audio enumeration failed; cached choices retained: ' + str(error)
            self.record('enumeration_error', error=error, token=self.enum_seen)
        else:
            if any(not isinstance(x, dict) or x.get('kind') not in ('loopback', 'microphone') or not isinstance(x.get('id'), str) or not x['id'] or not isinstance(x.get('name'), str) for x in sources):
                raise ValueError('Invalid audio endpoint enumeration result')
            self.options = {source_label(source) + f' [{i}]': source for i, source in enumerate(sources, 1)}
            self.devices.configure(values=list(self.options))
            match = any(selected and x['id'] == selected['id'] and x['kind'] == selected['kind'] for x in sources)
            self.set_selected_source(selected)
            self.enumeration_notice = ('No available audio endpoints. Refresh to retry.' if not sources else
                                       'Selected source unavailable; choose an explicit endpoint.' if selected and not match else None)
            self.record('enumeration_complete', token=self.enum_seen, count=len(sources), selected=selected, selected_available=match)
        self.status.set(self.state.get('restart_notice') or self.enumeration_notice or ('Selected source ready.' if selected else 'Choose one source, then Start.'))
        self.update_controls()

    def start(self):
        if self.initializing:
            return
        if self.state.get('running'):
            if not self.state.get('capture_owner') and self.state.get('capture_state') in ('unavailable', 'exhausted', 'retrying'):
                self.send('retry')
            return
        source = self.selected_source()
        if not source:
            self.status.set('Choose an available audio source explicitly. No substitute will be used.')
            return
        try:
            config = self.config()
        except ValueError as exc:
            self.status.set(str(exc))
            self.show_panel()
            return
        self.settings = config
        self.persist()
        self.show_panel()
        if self.process is not None:
            self.send('source', source=source)
            if any(config[k] != self.state.get('config', {}).get(k) for k in ('queue','shuffle','loop','recent_history','tips')):
                self.send('configure', config=config)
            self.send('start')
            self.status.set('Starting selected audio source…')
            return
        self.runtime_session = uuid.uuid4().hex
        self.record('runtime_start_requested', requested=source, saved=self.settings.get('source'))
        command = runtime_command()
        try:
            self.process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1,
                                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            process = self.process
            self.outgoing = queue.Queue(maxsize=64)
            outgoing = self.outgoing
            outgoing.put(dict(config, source=source, session_id=self.runtime_session))
            log = self.log
            runtime_session = self.runtime_session
            def write():
                try:
                    while True:
                        value = outgoing.get()
                        if value is None:
                            break
                        process.stdin.write(json.dumps(value) + '\n')
                        process.stdin.flush()
                except (OSError, ValueError):
                    pass
            def read():
                try:
                    for line in process.stdout:
                        if line.startswith('ZERAWAVE_PLAYER '):
                            try:
                                event = json.loads(line[len('ZERAWAVE_PLAYER '):])
                                journal_runtime_event(log, runtime_session, process.pid, event)
                                self.events.put(event)
                            except ValueError:
                                pass
                finally:
                    process.wait()
                    self.events.put(dict(child_ended=process))
            threading.Thread(target=write, name='Player control pipe', daemon=True).start()
            threading.Thread(target=read, name='Player status pipe', daemon=True).start()
            def read_errors():
                for line in process.stderr:
                    log.record('runtime_stderr', runtime_session=runtime_session, PID=process.pid, text=line.rstrip()[:16000])
            self.stderr_worker = threading.Thread(target=read_errors, name='Owned runtime log pipe', daemon=True)
            self.stderr_worker.start()
            self.initializing = True
            self.startup_cancelled = False
            self.started_at = time.monotonic()
            self.progress.pack(fill='x', before=self.status_label, pady=(8, 0))
            self.progress.start(40)
            self.status.set('Preparing graphics. First use can take longer; Stop cancels startup.')
            self.update_controls()
        except Exception as exc:
            self.status.set('Could not start ZeraWave: ' + str(exc))
            self.cleanup_child()

    def send(self, op, **value):
        if self.process is None or (self.initializing and op != 'switch_source'):
            return False
        self.serial += 1
        try:
            self.outgoing.put_nowait(dict(value, op=op, serial=self.serial))
            self.record('command_submitted', serial=self.serial, op=op, source=value.get('source'), requested=self.desired_source, active=self.active_source, intent={k:self.state.get(k) for k in ('running','listen_requested','listening','paused','held','capture_state','capture_owner','generation','owner_health','waiting_for_fresh')})
            return True
        except queue.Full:
            self.status.set('Control channel busy. Please retry after the current action.')
            return False

    def stop(self):
        if self.process is None:
            return
        if self.initializing:
            # Only this owned compiler process; no scene has been presented yet.
            self.startup_cancelled = True
            self.process.terminate()
            self.status.set('Startup cancelled. No audio source was substituted.')
        else:
            self.send('stop')
            self.status.set('Stopping capture · settling the current world…')

    def press_hold(self, event):
        if str(self.hold_button['state']) != 'disabled':
            self.hold_button.grab_set()
            self.send('hold', owner='panel.button', active=True)
        return 'break'

    def release_hold(self, event=None):
        if self.root.grab_current() is self.hold_button:
            self.hold_button.grab_release()
        self.send('hold', owner='panel.button', active=False)

    def text_focus(self):
        widget = self.root.focus_get()
        return isinstance(widget, (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox))

    def key_press(self, event):
        if self.text_focus():
            return
        if event.keysym in self.keys_down:
            return 'break'
        self.keys_down.add(event.keysym)
        if event.keysym in ('Shift_L', 'Shift_R'):
            self.send('hold', owner='panel.' + event.keysym, active=True)
        elif event.keysym == 'space':
            self.send('bonk')
        elif event.state & 4 and event.keysym == 'Return':
            self.start()
        elif event.state & 4 and event.keysym.lower() == 's':
            self.stop()
        elif event.state & 4 and event.keysym.lower() == 'p':
            self.send('pause')
        else:
            return
        return 'break'

    def key_release(self, event):
        self.keys_down.discard(event.keysym)
        if event.keysym in ('Shift_L', 'Shift_R'):
            self.send('hold', owner='panel.' + event.keysym, active=False)

    def focus_check(self):
        if self.root.focus_displayof() is None:
            self.keys_down.clear()
            self.release_hold()
            self.send('release_focus', owner='panel')

    def update_tips(self):
        self.library.configure(height=6 if self.tips.get() else 8)
        self.queue_list.configure(height=6 if self.tips.get() else 8)
        if self.tips.get() and self.panel_open:
            self.tip_label.pack(anchor='w', pady=(6, 0), before=self.footer)
        else:
            self.tip_label.pack_forget()

    def update_controls(self):
        running = self.state.get('running', False)
        ready = self.process is not None and not self.initializing
        retry = running and not self.state.get('capture_owner') and self.state.get('capture_state') in ('unavailable', 'exhausted', 'retrying')
        self.start_button.configure(state='normal' if not self.initializing and (retry or not running) and self.queue_ids and self.selected_source() else 'disabled', text='Retry' if retry else 'Start')
        self.stop_button.configure(state='normal' if self.process is not None else 'disabled')
        self.pause_button.configure(state='normal' if ready and running else 'disabled', text='Resume' if self.state.get('paused') else 'Pause')
        self.hold_button.configure(state='normal' if ready and running else 'disabled', text='Holding…' if self.state.get('held') else 'Hold · press')
        self.bonk_button.configure(state='normal' if ready and running and not self.state.get('paused') and self.state.get('target') is None else 'disabled')
        self.devices.configure(state='readonly')
        self.refresh_button.configure(state='normal')

    def receive(self, value):
        if 'capture_event' in value:
            self.status.set(value['capture_event']['detail'])
        if 'capture_error' in value:
            self.status.set(value['capture_error'])
        if value.get('action') == 'start_request':
            self.start()
        if 'runtime_pid' in value:
            self.runtime_pid = value['runtime_pid']
        if 'sources' in value or 'enumeration_error' in value:
            self.receive_sources(value.get('sources', []), value.get('enumeration_error'))
        if 'startup' in value:
            phase = value['startup']['phase']
            self.startup_phase = phase
            if phase == 'ready':
                self.initializing = False
                self.progress.stop();self.progress.pack_forget()
                self.update_controls()
            self.status.set(dict(context='Creating graphics context', compiling='Compiling visual shaders', resources='Preparing graphics resources', ready='Output ready · opening selected audio source').get(phase, phase))
        if 'source_working' in value:
            source = value['source_working']
            selected = self.selected_source()
            if (selected and source['id'] == selected['id'] and source['kind'] == selected['kind']
                    and value.get('generation', 0) >= self.state.get('generation', 0)):
                self.settings['source'] = source
                self.persist()
                self.record('saved_working_source', source=source, generation=value.get('generation'))
                self.status.set('Listening to ' + source_label(source))
        if 'state' in value:
            self.state = value['state']
            self.active_source = self.state.get('active_source')
            self.initializing = False
            self.progress.stop()
            self.progress.pack_forget()
            current = BY_ID.get(self.state.get('current'))
            target = BY_ID.get(self.state.get('target'))
            if current:
                self.now.set(current['name'] if not target else current['name'] + ' → ' + target['name'])
                taxonomy = lambda row: row['category'] + ' / ' + row['subcategory']
                self.taxonomy.set(taxonomy(current) if not target else taxonomy(current) + ' → ' + taxonomy(target))
                if not target and self.previous_current != current['id']:
                    self.settings['recent'] = (self.settings.get('recent', []) + [current['id']])[-8:]
                    self.previous_current = current['id']
                    self.persist()
            capture = self.state.get('capture_detail', 'Listening' if self.state.get('listening') else 'Not listening')
            mode = ('Paused · ' if self.state['paused'] else ('Holding · ' if self.state['held'] and self.state['running'] else '')) + capture
            if self.state.get('capture_state') == 'releasing' or self.state['running']:
                self.status.set(self.state.get('restart_notice') or self.enumeration_notice or capture)
            if target:
                label = RECIPES.get(self.state['transition_id'], (self.state['transition_id'],))[0]
                mode += f" · {label} · {self.state['transition_progress']:.0%}"
            if self.state.get('pending_config'):
                mode += ' · queue update pending next boundary'
            self.phase.set(mode)
            if not self.state['running'] and self.state['reason'] and self.state.get('capture_state') != 'releasing':
                self.status.set(self.state.get('restart_notice') or self.enumeration_notice or self.state['reason'])
            self.update_controls()
        if 'error' in value:
            self.status.set(value['error'])
            if value.get('device_lost'):
                self.update_controls()  # Retain selected identity and last successful preferences.
        if 'child_ended' in value and value['child_ended'] is self.process:
            process = self.process
            code = process.poll()
            self.cleanup_child()
            self.status.set('Startup cancelled · not listening.' if self.startup_cancelled else ('Visual window closed · not listening.' if code == 0 else 'Playback ended. Check the selected source and Open log, then explicitly restart.'))
            self.update_controls()

    def poll(self):
        if self.closing:
            return
        try:
            try:
                self.drain_enumeration()
            except Exception as exc:
                self.record('gui_enumeration_receiver_error', error=str(exc))
                self.enumeration_notice = 'Audio enumeration update failed: ' + str(exc)
                self.status.set(self.enumeration_notice)
            for _ in range(128):
                try:
                    value = self.events.get_nowait()
                except queue.Empty:
                    break
                try:
                    self.receive(value)
                except Exception as exc:
                    self.record('gui_receiver_error', error=str(exc), keys=list(value))
                    self.status.set('Player status update failed: ' + str(exc))
            if self.initializing and self.started_at:
                phase = getattr(self, 'startup_phase', 'context')
                labels = dict(context='Creating graphics context', compiling='Compiling visual shaders', resources='Preparing graphics resources', ready='Opening selected source')
                self.phase.set(f"{labels.get(phase, phase)} · {time.monotonic()-self.started_at:.1f}s elapsed · Stop cancels")
            if self.log is not None and self.log.last_error:
                self.status.set('Session logging failed: ' + self.log.last_error)
        except Exception as exc:
            self.record('gui_poll_error', error=str(exc))
        finally:
            if not self.closing:
                self.root.after(80, self.poll)

    def cleanup_child(self):
        if self.outgoing:
            try:
                self.outgoing.put_nowait(None)
            except queue.Full:
                pass
        self.outgoing = None
        self.process = None
        self.state = {}
        self.initializing = False
        self.phase.set('Not listening')
        self.now.set('Visual output closed')
        self.taxonomy.set('Approved Main · 27 worlds')
        self.previous_current = None
        self.progress.stop()
        self.progress.pack_forget()
        self.active_source = None

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.enumerator.close()
        self.record('panel_close_requested')
        process = self.process
        if process:
            if self.initializing:
                process.terminate()
            else:
                self.send('close')
            # Waiting/owned fallback are off the panel's event thread. No other
            # user/Studio process is enumerated or stopped.
            stderr_worker = self.stderr_worker
            log = self.log
            def finish():
                try:
                    process.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=3)
                finally:
                    if stderr_worker:
                        stderr_worker.join(1.)
                    log.close()
            threading.Thread(target=finish, name='Owned player shutdown', daemon=False).start()
        if not process and self.log:
            self.log.close()
        self.root.destroy()


if __name__ == '__main__':
    if '--runtime' in sys.argv:
        from player_runtime import main
        main()
    else:
        root = tk.Tk()
        Player(root)
        root.mainloop()
