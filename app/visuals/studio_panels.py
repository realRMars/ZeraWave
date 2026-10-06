"""Persistent native Tk docking, independent of artistic session storage."""
import json
import re
import tkinter as tk
from tkinter import ttk
from window_host import monitor_rectangles

BACKGROUND = '#10171c'


def clamp_geometry(value, monitors, fallback='960x720+40+40'):
    match = re.fullmatch(r'(\d+)x(\d+)([+-]\d+)([+-]\d+)', str(value))
    if not match:
        return clamp_geometry(fallback, monitors, '960x720+40+40') if value != fallback else fallback
    w, h, x, y = map(int, match.groups())
    # Keep a reachable title bar on an actual monitor, including negative origins.
    monitor = next((r for r in monitors if min(x+w, r[2])-max(x, r[0]) >= 120
                    and r[1] <= y < r[3]-60), monitors[0])
    l, t, right, bottom = monitor
    w = min(max(280, w), right-l); h = min(max(160, h), bottom-t-50)
    x = max(l, min(x, right-w)); y = max(t, min(y, bottom-h-40))
    return f'{w}x{h}{x:+}{y:+}'


class DockWindow(tk.Frame):
    """One retained Tk body, managed as a toplevel only while floating.

    Menubars detach before wm forget destroys the native wrapper, avoiding
    references to discarded wrappers during repeated Tk cycling.
    All controls, callbacks and the renderer's HWND remain owned by this body.
    """
    def __init__(self,root,**kwargs):
        kwargs.pop('padding',None)
        super().__init__(root,background=BACKGROUND,**kwargs)
        self.panel=None;self.floating=False;self.host=self;self.slot=self
        self.saved_title='';self.saved_geometry='820x760+80+80'
        self.saved_protocols={};self.protocol_commands={}

    def title(self,value=None):
        if value is None:return self.saved_title
        self.saved_title=value
        if self.floating:self.tk.call('wm','title',self._w,value)
    wm_title=title

    def geometry(self,value=None):
        if value is None:return self.tk.call('wm','geometry',self._w) if self.floating else self.saved_geometry
        self.saved_geometry=value
        if self.floating:self.tk.call('wm','geometry',self._w,value)
    wm_geometry=geometry

    def minsize(self,*args):
        if self.floating:return self.tk.call('wm','minsize',self._w,*args)

    def protocol(self,name,callback=None):
        if callback is None:return self.protocol_commands.get(name)
        if self.saved_protocols.get(name) is not callback:
            old=self.protocol_commands.get(name)
            if old:self.deletecommand(old)
            self.saved_protocols[name]=callback;self.protocol_commands[name]=self._register(callback)
        if self.floating:self.tk.call('wm','protocol',self._w,name,self.protocol_commands[name])
    wm_protocol=protocol

    def configure(self,cnf=None,**kwargs):
        if not self.floating:kwargs.pop('menu',None)
        return super().configure(cnf,**kwargs)
    config=configure

    def withdraw(self):
        if self.floating:self.tk.call('wm','withdraw',self._w)
    def deiconify(self):
        if self.floating:self.tk.call('wm','deiconify',self._w)
    def raise_host(self):self.tk.call('raise',self._w)
    def lift(self,*args):
        if self.panel:self.panel.manager.show(self.panel.key)
        else:self.raise_host()
    tkraise=lift

    def dockable(self):
        if self.floating:
            # Tk destroys its native wrapper on forget. Detach the menubar
            # first, retaining the one menu model for its next wrapper.
            super().configure(menu='')
            self.tk.call('wm','forget',self._w);self.floating=False

    def floatable(self):
        if not self.floating:
            self.tk.call('wm','manage',self._w);self.floating=True
            self.tk.call('wm','withdraw',self._w)
            self.tk.call('wm','title',self._w,self.saved_title)
            for name,command in self.protocol_commands.items():self.tk.call('wm','protocol',self._w,name,command)

def panel_frame(root, parent=None, **kwargs):
    window = DockWindow(root, **kwargs); return window


def tool_window(parent):
    return DockWindow(parent) if getattr(parent, 'workspace_owner', None) else tk.Toplevel(parent)


def hide_tool(window):
    panel = getattr(window, 'panel', None)
    if panel and not panel.manager.closing:
        panel.manager.hide(panel.key); return True
    return False


class Panel:
    def __init__(self, manager, key, title, window, zone, visible, help_text):
        self.manager = manager; self.key = key; self.title = title; self.window = window
        self.zone = zone; self.mode = 'dock'; self.visible = tk.BooleanVar(value=visible)
        self.help_text = help_text; window.panel = self; window.saved_title = title
        self.geometry = '820x760+80+80'


class PanelManager:
    def __init__(self, app, path):
        self.app = app; self.root = app.root; self.path = path
        self.zones = {}; self.panels = {}; self.closing = False; self.drag = None
        self.defaults = {}; self.save_timer = None
        self.monitors = monitor_rectangles(self.root)

    def zone(self, parent, key):
        frame = ttk.Frame(parent)
        bar = ttk.Frame(frame); bar.pack(fill='x')
        name = tk.StringVar(); ttk.Label(bar, textvariable=name).pack(side='left', fill='x', expand=True)
        ttk.Button(bar, text='?', width=2, command=lambda:self.help_selected(key)).pack(side='right')
        ttk.Button(bar, text='×', width=2, command=lambda:self.selected_action(key, self.hide)).pack(side='right')
        ttk.Button(bar, text='↗', width=2, command=lambda:self.selected_action(key, self.float)).pack(side='right')
        menu_button = ttk.Menubutton(bar, text='⋮', width=2); menu_button.pack(side='right')
        menu = tk.Menu(menu_button, tearoff=False); menu_button['menu'] = menu
        for destination in ('left', 'center', 'right_top', 'right_middle', 'right_bottom', 'bottom_left', 'bottom_right'):
            menu.add_command(label='Dock to '+destination.replace('_', ' '),
                             command=lambda d=destination:self.selected_action(key, lambda p:self.dock(p, d)))
        menu.add_command(label='Move tab left', command=lambda:self.reorder(key, -1))
        menu.add_command(label='Move tab right', command=lambda:self.reorder(key, 1))
        notebook = ttk.Notebook(frame); notebook.pack(fill='both', expand=True)
        self.zones[key] = (frame, notebook, name)
        notebook.bind('<<NotebookTabChanged>>', lambda e:self.changed(key))
        notebook.bind('<ButtonPress-1>', lambda e:self.begin_drag(key, e), add='+')
        notebook.bind('<ButtonRelease-1>', self.end_drag, add='+')
        return frame

    def register(self, key, title, window, zone, visible=True, help_text=''):
        panel = Panel(self, key, title, window, zone, visible, help_text)
        self.panels[key] = panel; self.defaults[key] = (zone, visible)
        window.bind('<Configure>',lambda e:self.schedule_save() if e.widget==window and panel.mode=='float' else None,add='+')
        if visible: self.dock(key, zone)
        else: window.dockable()
        return panel

    def selected(self, zone):
        selected = self.zones[zone][1].select()
        return next((p.key for p in self.panels.values() if str(p.window.slot) == selected), None)

    def selected_action(self, zone, action):
        key = self.selected(zone)
        if key: action(key)

    def changed(self, zone):
        key = self.selected(zone)
        self.zones[zone][2].set(self.panels[key].title if key else '')
        if key:self.panels[key].window.tk.call('raise',self.panels[key].window._w)
        if hasattr(self.app, 'workspace_ready') and self.app.workspace_ready:
            self.app.panel_visibility_changed(); self.schedule_save()

    def remove(self, panel):
        self.app.release_tool_holds()
        for frame, notebook, name in self.zones.values():
            if str(panel.window.slot) in notebook.tabs(): notebook.forget(panel.window.slot)
        if panel.window.floating:
            if panel.window.winfo_viewable(): panel.geometry = panel.window.geometry()
            panel.window.withdraw()

    def dock(self, key, zone, index='end'):
        panel = self.panels[key]; self.remove(panel); panel.window.dockable()
        panel.mode = 'dock'; panel.zone = zone; panel.visible.set(True)
        nb = self.zones[zone][1]; nb.insert(index, panel.window.slot, text=panel.title); nb.select(panel.window.slot)
        self.changed(zone)

    def float(self, key):
        panel = self.panels[key]; self.remove(panel); panel.window.floatable()
        panel.mode = 'float'; panel.visible.set(True)
        panel.window.geometry(clamp_geometry(panel.geometry, self.monitors))
        panel.window.minsize(280, 180)
        if not hasattr(panel,'hide_callback'):panel.hide_callback=lambda:self.hide(key)
        panel.window.protocol('WM_DELETE_WINDOW',panel.hide_callback)
        if not hasattr(panel,'float_menu'):
            menu = tk.Menu(panel.window.host, tearoff=False); actions = tk.Menu(menu, tearoff=False)
            actions.add_command(label='Redock to previous area', command=lambda:self.dock(key, panel.zone))
            for zone in self.zones:
                actions.add_command(label='Dock to '+zone.replace('_', ' '), command=lambda z=zone:self.dock(key, z))
            actions.add_command(label='Hide panel', command=lambda:self.hide(key))
            menu.add_cascade(label='Panel', menu=actions)
            menu.add_command(label='?', command=lambda:self.help(key));panel.float_menu=menu
        panel.window.configure(menu=panel.float_menu)
        panel.window.deiconify(); panel.window.raise_host()
        self.app.panel_visibility_changed(); self.schedule_save()

    def hide(self, key):
        panel = self.panels[key]; self.remove(panel); panel.visible.set(False)
        self.app.panel_visibility_changed(); self.schedule_save()

    def show(self, key):
        panel = self.panels[key]
        if panel.mode == 'float':
            panel.visible.set(True); panel.window.deiconify(); panel.window.raise_host()
        else:
            nb = self.zones[panel.zone][1]
            if str(panel.window.slot) not in nb.tabs(): self.dock(key, panel.zone)
            else: nb.select(panel.window.slot); panel.visible.set(True)
        self.app.panel_visibility_changed(); self.schedule_save()

    def displayed(self, key):
        panel = self.panels.get(key)
        return bool(panel and panel.visible.get() and (panel.mode == 'float' or self.selected(panel.zone) == key))

    def reorder(self, zone, delta):
        key = self.selected(zone)
        if key:
            nb = self.zones[zone][1]; index = nb.index(self.panels[key].window.slot)
            nb.insert(max(0, min(len(nb.tabs())-1, index+delta)), self.panels[key].window.slot)
            self.schedule_save()

    def begin_drag(self, zone, event):
        try: index = self.zones[zone][1].index('@'+str(event.x)+','+str(event.y))
        except tk.TclError: return
        path = self.zones[zone][1].tabs()[index]
        key = next(p.key for p in self.panels.values() if str(p.window.slot) == path)
        self.drag = (key, event.x_root, event.y_root)

    def end_drag(self, event):
        if not self.drag: return
        key, x, y = self.drag; self.drag = None
        if abs(x-event.x_root)+abs(y-event.y_root) < 18: return
        for zone, (frame, nb, name) in self.zones.items():
            if (frame.winfo_rootx() <= event.x_root <= frame.winfo_rootx()+frame.winfo_width()
                    and frame.winfo_rooty() <= event.y_root <= frame.winfo_rooty()+frame.winfo_height()):
                try: index = nb.index('@'+str(event.x_root-nb.winfo_rootx())+','+str(event.y_root-nb.winfo_rooty()))
                except tk.TclError: index = 'end'
                self.dock(key, zone, index); return
        self.float(key)

    def help_selected(self, zone):
        self.selected_action(zone, self.help)

    def help(self, key):
        self.app.show_help(self.panels[key].title, self.panels[key].help_text)

    def snapshot(self):
        return dict(version=1, root=self.root.geometry(), sizes=self.app.layout_sizes(),
            order={z:[next(p.key for p in self.panels.values() if str(p.window.slot)==w) for w in nb.tabs()]
                   for z, (f, nb, n) in self.zones.items()},
            selected={z:self.selected(z) for z in self.zones},
            panels={k:dict(zone=p.zone, mode=p.mode, visible=p.visible.get(),
                          geometry=p.window.geometry() if p.mode=='float' and p.visible.get() else p.geometry)
                    for k, p in self.panels.items()})

    def schedule_save(self):
        if self.closing or not getattr(self.app, 'workspace_ready', False): return
        if self.save_timer is not None: self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(500, self.save)

    def save(self):
        self.save_timer = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix('.tmp')
            temporary.write_text(json.dumps(self.snapshot(), indent=2), encoding='utf8'); temporary.replace(self.path)
        except OSError as exc: self.app.status.set('Layout could not be saved: '+str(exc))

    def restore(self, data=None):
        try:
            if data is None:
                if not self.path.exists(): return
                if self.path.stat().st_size > 65536: raise ValueError('Layout file exceeds 64 KiB.')
                data = json.loads(self.path.read_text(encoding='utf8'))
            if not isinstance(data, dict) or data.get('version') != 1: raise ValueError('Unsupported layout.')
            self.root.geometry(clamp_geometry(data.get('root'), self.monitors, '2180x1240+20+20'))
            states = data.get('panels', {})
            for key, panel in self.panels.items():
                state = states.get(key, {})
                zone = state.get('zone', panel.zone)
                if zone not in self.zones: zone = self.defaults[key][0]
                panel.geometry = clamp_geometry(state.get('geometry', panel.geometry), self.monitors)
                self.dock(key, zone)
                if state.get('mode') == 'float': self.float(key)
                if not state.get('visible', self.defaults[key][1]): self.hide(key)
            for zone, order in data.get('order', {}).items():
                if zone not in self.zones or not isinstance(order, list): continue
                nb = self.zones[zone][1]
                for key in order:
                    if key in self.panels and str(self.panels[key].window.slot) in nb.tabs(): nb.insert('end', self.panels[key].window.slot)
            for zone, key in data.get('selected', {}).items():
                if key in self.panels and zone in self.zones and str(self.panels[key].window.slot) in self.zones[zone][1].tabs():
                    self.zones[zone][1].select(self.panels[key].window.slot)
            self.loaded_sizes=data.get('sizes', {})
            self.root.after(200,lambda:self.app.restore_sizes(self.loaded_sizes))
        except (OSError, ValueError, TypeError, AttributeError, tk.TclError) as exc:
            self.app.status.set('Saved layout ignored: '+str(exc)+' Use View > Reset layout.')

    def reset(self):
        self.app.release_tool_holds()
        self.root.geometry(clamp_geometry('2180x1240+20+20', self.monitors))
        for key, (zone, visible) in self.defaults.items():
            self.dock(key, zone)
            if not visible: self.hide(key)
        self.loaded_sizes={}
        self.root.after(200,lambda:self.app.restore_sizes({})); self.app.panel_visibility_changed(); self.schedule_save()


class TabRouter:
    """Retain existing Studio callbacks that select its original view widgets."""
    def __init__(self, manager, original): self.manager = manager; self.original = original
    def select(self, widget=None):
        if widget is None: return self.manager.zones['center'][1].select()
        panel = next((p for p in self.manager.panels.values() if str(widget) in (str(p.window),str(p.window.slot))), None)
        if panel: self.manager.show(panel.key)
        else: self.original.select(widget)


def dialog_parent(window):
    return window.host if isinstance(window,DockWindow) and window.floating else window
