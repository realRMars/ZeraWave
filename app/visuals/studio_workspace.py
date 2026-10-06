"""Unified ZeraphinaX / ZeraWave workspace over the existing Studio owners."""
from collections import deque
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox

from studio import Studio, ROOT, STUDIO_TREES, SOURCES, selection_states, selection_title, SCENES
from studio_panels import DockWindow, PanelManager, TabRouter, clamp_geometry
from studio_compact import compact_colors, compact_tuning, compact_monitor, update_trace, update_color_summary, walk
from studio_meters import Waveform, Analyzer
from window_host import NativeSurface, dpi_awareness, owned_process


HELP = {
    'workspace': 'Drag a panel tab to another docking area, or outside the workspace to float it. '
        'Each area also has a ⋮ menu with docking and tab-order commands. ↗ floats the current tab; × hides it. '
        'View restores hidden panels. Floating panels have a Panel menu for redocking. Closing a panel hides it; '
        'File > Exit stops the owned preview and shuts down Studio. Layout is saved separately from artistic sessions. '
        'View > Reset layout changes window layout only. Resize using the dividers between areas. '
        'The central visualizer is the existing renderer window; docking does not restart playback or erase histories. '
        'Ctrl+Enter starts, Ctrl+P pauses/resumes, Ctrl+Shift+S stops, Space BONKs, and Shift holds while pressed. '
        'Playback shortcuts are inactive in text fields and tuning sliders. Ctrl+S saves the artistic session; '
        'Ctrl+O opens one and Ctrl+N creates one outside text/slider editing. Tab and Shift+Tab reach controls and ?. '
        'The same session, palettes, profiles, audition and diagnostic paths remain available.',
    'colors': 'Pigments edit declared source roles before shading and audio response. Gradient blend start/full positions '
        'retain their original meaning. Palette timing and Presets & reset contain complete Hold/Cycle, named setup, '
        'reset and revert controls. Changes apply through the existing live color transport. Shared materials follow '
        'compatible forms; form-owned pigments retain their named scope. Session Save stores the current artistic setup. '
        'Named color presets are saved through their existing file dialog; neither action promotes an audio baseline.',
    'tuning': 'Follow uses the current endpoint; Pin fixes the editing destination without freezing playback. '
        'Controls contains the original gains, listening-window toggles, exact frequency bounds and compatibility status. '
        'Listening & FFT shows actual bins and ACK-applied windows. Profiles & authored contains named profile Save/Load '
        'and the explicit authored-baseline promotion. Save Authored requires a matching scope and acknowledged edit. '
        'Left/Right adjust by 1 Hz or 0.01; Up/Down move between enabled sliders. Held repeats are bounded. '
        'Range OFF retains the original analysis; gain 0 removes only that contribution and 1 is authored strength. '
        'One-Hz slider positioning does not add FFT resolution. Shared clocks and dependencies remain labeled.',
    'monitor': 'Read-only telemetry from the existing renderer/audio owner. Mapping shows a bounded history of actual '
        'analyzer bass and one selected CPU submitted input, with the source role labeled. Full values contains all '
        'original source, scope, dependency, gain-slot, proxy, director and history-owner values, with horizontal '
        'scrolling. These are CPU submissions, not measured pixels or instrument/pitch classification. '
        'Hidden tools stop their display work; visible consumers share one audio subscription.',
    'transport': 'Start uses the selected Main or Experimental setup. Pause parks the preview clock; Resume continues. '
        'Hold is momentary and releases on focus loss or docking. BONK uses Normal or Instant and is enabled only '
        'when the existing player can change forms. Test-track replay is silent. File waveforms use actual decoded '
        'PCM and the shared analyzer position; they do not seek. Live waveforms show bounded current PCM snapshots '
        'with gaps between snapshots. Synthetic sources have no PCM waveform. Source/quality/layer changes apply '
        'on the next preview; compatible color and tuning edits remain live.',
    'analyzer': 'Exactly twelve frequency ranges from the existing audio analyzer. Each label shows its measured '
        'lower and upper edge. * indicates under-resolved bins. Values are normalized mean FFT magnitude, not '
        'physical power. Stale, unavailable or synthetic spectra show N/A rather than fabricated activity.',
    'library': 'The tree uses the current Main and Experimental catalogs, including retained historical inventory. '
        'Selection prepares the next preview; it does not silently restart the current one. Loaded session names, '
        'track paths, counts and preset paths are actual data. Catalog icons are labeled icons; archived thumbnails '
        'are used only when an existing capture is available, with its source path in the detail text. '
        'Catalog & techniques contains the complete existing searchable library and effect inventory.',
}


def initial_color_target(targets,scene):
    """Prefer the selected scene's pigments; retain explicit compatible choices."""
    return next((t for t in targets if t.scene==scene or scene=='blend' and t.scene!='shared'),targets[0])


class Workspace(Studio):
    def __init__(self, root, layout_path=None):
        self.workspace_ready=False; self.manager=None; self.native_surface=None; self.native_packet=None
        self.ui_samples=deque(maxlen=1200); self.display_counts=0; self.help_window=None; self.thumbnails=[]
        root.workspace_owner=self
        super().__init__(root)
        # The unified music workspace starts at normal time. Loading an
        # existing artistic session still restores its explicit replay speed.
        self.vars['speed'].set('Real time')
        self.legacy_tabs=self.tabs; self.legacy_tabs.pack_forget(); self.footer.pack_forget()
        self.root.title('ZeraphinaX · ZeraWave Studio — Workspace prototype')
        self.root.minsize(1100,740); self.root.geometry('2180x1240+20+20')
        self.apply_theme()
        self.manager=PanelManager(self,layout_path or ROOT/'work/studio/workspace-layout.json')
        heading=ttk.Frame(root,padding=(16,5)); heading.pack(fill='x')
        ttk.Label(heading,text='ZeraphinaX',font=('Segoe UI',20,'bold'),foreground='#e7b890').pack(side='left')
        ttk.Label(heading,text='ZeraWave Studio',foreground='#99aeb9').pack(side='left',padx=18)
        ttk.Button(heading,text='?',width=3,command=lambda:self.show_help('Workspace',HELP['workspace'])).pack(side='right')
        ttk.Label(heading,text='FUNCTIONAL PROTOTYPE',foreground='#ce986e').pack(side='right',padx=12)
        self.vertical=ttk.Panedwindow(root,orient='vertical'); self.vertical.pack(fill='both',expand=True,padx=8,pady=4)
        self.upper=ttk.Panedwindow(self.vertical,orient='horizontal')
        self.lower=ttk.Panedwindow(self.vertical,orient='horizontal')
        self.vertical.add(self.upper,weight=5);self.vertical.add(self.lower,weight=1)
        self.right=ttk.Panedwindow(self.upper,orient='vertical')
        self.upper.add(self.manager.zone(self.upper,'left'),weight=0)
        self.upper.add(self.manager.zone(self.upper,'center'),weight=5)
        self.upper.add(self.right,weight=0)
        for zone in ('right_top','right_middle','right_bottom'):self.right.add(self.manager.zone(self.right,zone),weight=1)
        for zone in ('bottom_left','bottom_right'):self.lower.add(self.manager.zone(self.lower,zone),weight=1)
        for pane in (self.upper,self.vertical,self.right,self.lower):
            pane.bind('<ButtonRelease-1>',lambda e:self.manager.schedule_save(),add='+')
        self.preview_controls.grid_forget();self.preview_controls.pack_forget()
        controls=list(self.preview_controls.winfo_children())[0]
        self.bonk_button.configure(text='⚒ BONK',style='Copper.TButton')
        self.start_button.configure(style='Start.TButton')
        self.waveform=Waveform(self.preview_controls)
        self.manager.register('transport','Transport & waveform',self.preview_controls,'bottom_left',help_text=HELP['transport'])
        self.visual=DockWindow(root);self.visual.dockable()
        visual_heading=ttk.Frame(self.visual,padding=6);visual_heading.pack(fill='x')
        self.visual_title=tk.StringVar(value='Ready · select a world and Start')
        ttk.Label(visual_heading,textvariable=self.visual_title,font=('Segoe UI',11),foreground='#e7b890').pack(side='left')
        self.visual_state=tk.StringVar(value='Full quality')
        ttk.Label(visual_heading,textvariable=self.visual_state,foreground='#8aadb9').pack(side='right')
        self.surface=tk.Frame(self.visual,background='#080e12',width=1280,height=720)
        self.surface.pack(fill='both',expand=True)
        self.surface.bind('<Configure>',lambda e:self.resize_renderer())
        self.placeholder=ttk.Label(self.surface,text='ZeraWave\nChoose a world and an audio source, then Start.',
                                   justify='center',background='#080e12',foreground='#73909f',font=('Segoe UI',16))
        self.placeholder.place(relx=.5,rely=.5,anchor='center')
        self.manager.register('visualizer','Visualizer',self.visual,'center',help_text=HELP['workspace'])
        self.session_library=DockWindow(root);self.session_library.dockable();self.build_session_library()
        self.manager.register('session','Session & worlds',self.session_library,'left',help_text=HELP['library'])
        self.analyzer_window=DockWindow(root);self.analyzer_window.dockable();self.analyzer=Analyzer(self.analyzer_window)
        self.manager.register('analyzer','12-band analyzer',self.analyzer_window,'bottom_right',help_text=HELP['analyzer'])
        old_views=(('setup','Preview setup',self.preview),('experimental','Experimental',self.cymatics_tab),
                   ('effects','Effects & layers',self.layers_tab),('catalog','Catalog & techniques',self.library_tab),
                   ('review','Results & review',self.results))
        for key,title,view in old_views:
            self.legacy_tabs.forget(view)
            self.manager.register(key,title,view,'center',visible=False,help_text='Complete existing Studio view. '+HELP['workspace'])
        self.tabs=TabRouter(self.manager,self.legacy_tabs)
        self.open_color_inspector();self.open_star_tuning();self.open_mapping_monitor()
        self.manager.register('logs','Diagnostics & logs',self.build_logs(),'center',visible=False,
                              help_text='Latest owned run.log and bounded UI refresh timing. Development diagnostics retain the existing one-second resource sampling.')
        statusbar=ttk.Frame(root,padding=(12,4));statusbar.pack(fill='x')
        ttk.Label(statusbar,textvariable=self.status,wraplength=2100).pack(anchor='w')
        ttk.Label(statusbar,textvariable=self.active_preview,wraplength=2100,foreground='#8fabb7').pack(anchor='w')
        self.workspace_ready=True;self.menus();self.manager.restore()
        # Native geometry settles after mapping, later than Tk's first idle.
        self.root.after(200,lambda:self.restore_sizes(getattr(self.manager,'loaded_sizes',{})))
        root.bind('<Configure>',lambda e:self.manager.schedule_save() if e.widget==root else None,add='+')
        self.panel_visibility_changed();self.root.after(200,self.workspace_poll)
        self.root.protocol('WM_DELETE_WINDOW',self.close)

    def apply_theme(self):
        style=ttk.Style(self.root)
        style.configure('.',background='#10171c',foreground='#dbe3e5',font=('Segoe UI',10))
        style.configure('TFrame',background='#10171c');style.configure('TLabel',background='#10171c')
        style.configure('TButton',background='#1b262d',padding=(8,5),bordercolor='#36434a')
        style.map('TButton',background=[('active','#34505b')])
        style.configure('Copper.TButton',background='#805338',foreground='#fff0de')
        style.map('Copper.TButton',background=[('active','#b17850')])
        style.configure('Start.TButton',background='#16414a',foreground='#73e0e9')
        style.configure('TNotebook',background='#10171c',borderwidth=0)
        style.configure('TNotebook.Tab',padding=(9,5),background='#172128')
        style.map('TNotebook.Tab',background=[('selected','#314047')],foreground=[('selected','#ecc09b')])
        style.configure('Treeview',background='#10191f',fieldbackground='#10191f',foreground='#cddce0',rowheight=36)
        style.map('Treeview',background=[('selected','#4b3629')],foreground=[('selected','#f6d2b0')])
        style.configure('Treeview.Heading',background='#19272e',foreground='#c4d4dc')
        style.configure('TEntry',fieldbackground='#1a2931',foreground='#e9f1f2')
        style.configure('TCombobox',fieldbackground='#1a2931',foreground='#e9f1f2')
        self.root.configure(background='#0b1217')

    def build_session_library(self):
        w=self.session_library
        self.session_label=tk.StringVar(value='Unsaved session')
        self.session_detail=tk.StringVar()
        ttk.Label(w,textvariable=self.session_label,font=('Segoe UI',12,'bold'),foreground='#e2b18b',wraplength=280).pack(anchor='w',padx=10,pady=8)
        ttk.Label(w,textvariable=self.session_detail,wraplength=280).pack(anchor='w',padx=10)
        row=ttk.Frame(w);row.pack(fill='x',padx=8,pady=6)
        ttk.Button(row,text='Open',command=self.load).pack(side='left')
        ttk.Button(row,text='Save',command=self.save).pack(side='left',padx=4)
        ttk.Button(row,text='Setup',command=lambda:self.manager.show('setup')).pack(side='left')
        tree_frame=ttk.Frame(w);tree_frame.pack(fill='both',expand=True,padx=8,pady=5)
        self.world_tree=ttk.Treeview(tree_frame,show='tree',selectmode='browse')
        tree_scroll=ttk.Scrollbar(tree_frame,orient='vertical',command=self.world_tree.yview)
        self.world_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side='right',fill='y');self.world_tree.pack(fill='both',expand=True)
        self.world_paths={};self.world_thumbnail={}
        # Existing named captures only. Their archived identity is explicit.
        capture_by_state={'citadel':ROOT/'work/air/verified-final/form-22.png'}
        for scope,tree in STUDIO_TREES.items():
            parent=self.world_tree.insert('','end',iid=scope,text='Main' if scope=='main' else 'Experimental',open=True)
            self.world_paths[parent]=(scope,[])
            def add(nodes,parent,path):
                for key,node in nodes.items():
                    selected=path+[key];iid=scope+':'+':'.join(selected)
                    options={};states=selection_states(selected,tree)
                    capture=capture_by_state.get(states[0]) if len(states)==1 else None
                    if capture and capture.exists():
                        try:
                            image=tk.PhotoImage(file=str(capture));image=image.subsample(max(1,image.width()//30),max(1,image.height()//24))
                            self.thumbnails.append(image);options['image']=image;self.world_thumbnail[iid]=str(capture)
                        except tk.TclError:pass
                    item=self.world_tree.insert(parent,'end',iid=iid,text=node['label'],open=len(path)<1,**options)
                    self.world_paths[item]=(scope,selected)
                    add(node.get('children',{}),item,selected)
            add(tree,parent,[])
        self.world_tree.bind('<<TreeviewSelect>>',self.pick_world)
        self.library_source=tk.StringVar(value='Names come from the current catalogs. Thumbnail-free rows have no saved capture assigned.')
        ttk.Label(w,textvariable=self.library_source,wraplength=280,foreground='#8ba6b3').pack(fill='x',padx=8,pady=4)
        ttk.Button(w,text='Complete catalog & techniques',command=lambda:self.manager.show('catalog')).pack(fill='x',padx=8)
        ttk.Button(w,text='Effects & layers',command=lambda:self.manager.show('effects')).pack(fill='x',padx=8,pady=4)
        self.asset_tabs=ttk.Notebook(w);self.asset_tabs.pack(fill='x',padx=8,pady=4)
        for title,folder in (('Sessions',ROOT/'work/studio'),('Color presets',self.color_preset_folder())):
            page=ttk.Frame(self.asset_tabs);self.asset_tabs.add(page,text=title)
            listing=tk.Listbox(page,height=3,background='#14212a',foreground='#b7d5df',highlightthickness=0,selectbackground='#4b3629')
            listing.pack(fill='x');files=sorted(folder.glob('*.json'))[:100] if folder.exists() else []
            files=[p for p in files if p.name!='workspace-layout.json']
            for file in files:listing.insert('end',file.name)
            if not files:listing.insert('end','No saved '+title.lower()+' in '+str(folder))
            listing.bind('<Double-1>',lambda e,paths=files:self.open_saved_asset(e,paths))

    def open_saved_asset(self,event,paths):
        selected=event.widget.curselection()
        if selected and selected[0]<len(paths):os.startfile(paths[selected[0]])

    def pick_world(self,event=None):
        chosen=self.world_tree.selection()
        if not chosen:return
        scope,path=self.world_paths[chosen[0]]
        if scope=='experimental' and not path:return
        if scope==self.selection_scope and path==self.selection:return
        self.select(path,scope=scope,show=False)
        self.manager.show('visualizer')
        capture=self.world_thumbnail.get(chosen[0])
        self.library_source.set('Archived capture: '+capture if capture else 'Catalog selection · '+selection_title(path)+'. No saved thumbnail assigned.')

    def change_visual_tab(self,event=None):
        if not self.workspace_ready:return super().change_visual_tab(event)

    def select(self,selection,scope=None,show=True):
        # Session scope remains the existing catalog's scope. Transport lives
        # permanently in its own movable panel rather than changing parents.
        super().select(selection,scope,show=show)
        if self.workspace_ready:
            self.visual_title.set(selection_title(self.selection)+' · '+self.vars['source'].get())
            from color_controls import targets_for
            targets=targets_for(self.color_scene())
            if targets and self.color_editor.target().id not in {t.id for t in targets}:
                self.color_editor.target_choice.set(initial_color_target(targets,self.color_scene()).label);self.color_editor.refresh()
            iid=self.selection_scope+(':'+':'.join(self.selection) if self.selection else '')
            if self.world_tree.exists(iid):
                if self.world_tree.selection()!=(iid,):self.world_tree.selection_set(iid)
                self.world_tree.see(iid)

    def open_color_inspector(self):
        if not self.manager:return super().open_color_inspector()
        if self.color_editor:
            self.manager.show('colors');return
        from color_inspector import ColorInspector
        from color_controls import targets_for
        self.color_editor=ColorInspector(self,'blend')
        targets=targets_for(self.color_scene())
        if targets:self.color_editor.target_choice.set(initial_color_target(targets,self.color_scene()).label);self.color_editor.refresh()
        compact_colors(self.color_editor)
        self.manager.register('colors','Color Inspector',self.color_editor.window,'right_top',
                              help_text=HELP['colors'])

    def open_star_tuning(self):
        if not self.manager:return super().open_star_tuning()
        if self.star_tuning_window:
            self.manager.show('tuning');return
        super().open_star_tuning();compact_tuning(self.star_tuning_window)
        self.manager.register('tuning','Audio Tuning',self.star_tuning_window.window,'right_middle',help_text=HELP['tuning'])

    def open_mapping_monitor(self):
        if not self.manager:return super().open_mapping_monitor()
        if self.mapping_monitor:
            self.manager.show('monitor');return
        super().open_mapping_monitor();compact_monitor(self.mapping_monitor)
        self.manager.register('monitor','Mapping Monitor',self.mapping_monitor.window,'right_bottom',help_text=HELP['monitor'])

    def show_star_tuning(self,enabled,form=None,target=None,pin=None):
        if self.manager and self.workspace_ready:
            enabled=bool(enabled and self.manager.displayed('tuning'))
            self.monitor_enabled=bool(self.manager.displayed('monitor') and self.mapping_monitor and self.mapping_monitor.enabled.get())
            enabled=enabled or self.manager.displayed('analyzer') or self.manager.displayed('transport')
        super().show_star_tuning(enabled,form,target,pin)

    def poll_star_tuning(self):
        # The unified shell's one 200ms poll owns all tool presentation. No
        # additional 50ms redraw loop survives layout changes.
        self.star_tuning_poll_after=None

    def panel_visibility_changed(self):
        if not self.workspace_ready or not self.manager:return
        self.show_star_tuning(self.manager.displayed('tuning'))
        left=self.manager.zones['left'][0]
        present=str(left) in self.upper.panes()
        wanted=bool(self.manager.zones['left'][1].tabs())
        if wanted and not present:self.upper.insert(0,left,weight=0);self.root.after_idle(lambda:self.restore_sizes({}))
        elif not wanted and present:self.upper.forget(left)
        self.resize_renderer()

    def release_tool_holds(self):
        if hasattr(self,'playback_keys'):self.release_preview_holds()
        view=getattr(self,'star_tuning_window',None)
        if view and hasattr(view,'keyboard'):view.keyboard.stop()

    def renderer_host_environment(self):
        self.manager.show('visualizer');self.root.update_idletasks()
        return dict(ZERAWAVE_WORKSPACE_HOST=str(self.surface.winfo_id()),ZERAWAVE_WORKSPACE_PID=str(os.getpid()))

    def launch(self,values,output,label=None):
        self.native_surface=None;self.native_packet=None
        super().launch(values,output,label)
        self.visual_title.set(selection_title(values.get('selection',[]))+' · '+values['source'])
        self.waveform.request(values['source'],values['track'])
        self.panel_visibility_changed()

    def resize_renderer(self):
        if self.native_surface is not None and self.process and self.process.poll() is None:
            try:
                self.native_surface.attach(self.surface.winfo_id(),self.surface.winfo_width(),self.surface.winfo_height(),os.getpid())
                self.visual_state.set(f'{self.surface.winfo_width()} × {self.surface.winfo_height()} · '+self.running_values['render_scale'])
            except (OSError,RuntimeError) as exc:
                self.status.set('Renderer hosting failed: '+str(exc))

    def workspace_poll(self):
        if self.manager.closing:return
        began=time.perf_counter();running=self.process is not None and self.process.poll() is None
        latest=self.color_link.get_audio() if self.color_link and self.color_link.audio_run else None
        if running and self.native_surface is None:
            packet=self.color_link.get_window() if self.color_link else None
            if packet is None and self.output:
                log=self.output/'run.log'
                try:
                    with log.open('rb') as handle:
                        handle.seek(max(0,log.stat().st_size-8192));lines=handle.read(8192).decode('utf8',errors='replace').splitlines()
                    for line in lines:
                        if line.startswith('ZERAWAVE_WINDOW '):packet=json.loads(line[16:])
                except (OSError,ValueError):pass
            if packet and owned_process(packet.get('pid'),self.process.pid):
                self.native_packet=packet;self.native_surface=NativeSurface(packet['hwnd'],packet['pid'])
                self.placeholder.place_forget();self.resize_renderer()
        if not running and self.native_surface is not None:
            self.native_surface=None;self.native_packet=None;self.placeholder.place(relx=.5,rely=.5,anchor='center')
        source=self.running_values['source'] if running else self.vars['source'].get()
        path=self.running_values['track'] if running else self.vars['track'].get()
        if self.manager.displayed('transport'):
            self.waveform.request(source,path);self.waveform.update(latest)
        if self.manager.displayed('analyzer'):self.analyzer.update(latest)
        if self.manager.displayed('colors'):update_color_summary(self.color_editor)
        if self.manager.displayed('tuning'):
            self.star_tuning_window.refresh(latest,running)
        if self.manager.displayed('monitor') and self.mapping_monitor.enabled.get():update_trace(self.mapping_monitor,latest)
        self.session_label.set(self.session_path.name if self.session_path else 'Unsaved session')
        self.session_detail.set(f'{len(self.selected_states())} selected forms · '+self.vars['source'].get()+'\n'+Path(self.vars['track'].get()).name)
        if self.manager.displayed('logs'):self.refresh_logs()
        self.ui_samples.append((time.perf_counter()-began)*1000.);self.display_counts+=1
        self.root.after(200,self.workspace_poll)

    def poll(self):
        # The original poll owns process completion, ACKs and read-only monitor
        # refresh. Hidden monitor presentation is skipped without recreating it.
        view=self.mapping_monitor
        if self.manager and self.workspace_ready and not self.manager.displayed('monitor'):self.mapping_monitor=None
        try:super().poll()
        finally:self.mapping_monitor=view

    def menus(self):
        if not self.workspace_ready:return super().menus()
        super().menus()  # Preserve all preset/palette/audition menu callbacks.
        bar=self.root.nametowidget(self.root.cget('menu'))
        for index in range(bar.index('end')+1):
            if bar.type(index)=='cascade' and bar.entrycget(index,'label')=='View':
                view=tk.Menu(bar,tearoff=False);bar.entryconfigure(index,menu=view)
                for key,panel in self.manager.panels.items():
                    view.add_checkbutton(label=panel.title,variable=panel.visible,
                        command=lambda k=key:self.manager.show(k) if self.manager.panels[k].visible.get() else self.manager.hide(k))
                view.add_separator();view.add_command(label='Reset layout',command=self.manager.reset)
        help_menu=tk.Menu(bar,tearoff=False)
        help_menu.add_command(label='Workspace & keyboard',command=lambda:self.show_help('Workspace',HELP['workspace']))
        help_menu.add_command(label='Diagnostics & logs',command=lambda:self.manager.show('logs'))
        for key in ('colors','tuning','monitor','transport','analyzer'):help_menu.add_command(label=self.manager.panels[key].title+' help',command=lambda k=key:self.manager.help(k))
        bar.add_cascade(label='Help',menu=help_menu)

    def show_help(self,title,text):
        if self.help_window and self.help_window.winfo_exists():self.help_window.destroy()
        self.help_window=tk.Toplevel(self.root);self.help_window.title(title+' — help');self.help_window.geometry('720x640')
        box=tk.Text(self.help_window,wrap='word',background='#10171c',foreground='#dce5e8',font=('Segoe UI',11),padx=18,pady=12)
        scroll=ttk.Scrollbar(self.help_window,command=box.yview);scroll.pack(side='right',fill='y');box.configure(yscrollcommand=scroll.set);box.pack(fill='both',expand=True)
        notes=[]
        for tool in (self.color_editor,self.star_tuning_window,self.mapping_monitor):
            if tool and title.lower().replace(' ','') in tool.window.title().lower().replace(' ',''):
                notes.extend(getattr(tool,'help_notes',[]))
        if title=='Audio Tuning':notes.extend((self.star_tuning_window.help_text.get(),self.star_tuning_window.target_info.get(),self.star_tuning_window.spectrum.legend.get()))
        box.insert('end',text+'\n\n'+'\n\n'.join(notes));box.configure(state='disabled');box.focus_set()
        self.help_window.bind('<Escape>',lambda e:self.help_window.destroy())

    def build_logs(self):
        window=DockWindow(self.root);window.dockable()
        row=ttk.Frame(window);row.pack(fill='x')
        ttk.Button(row,text='Open latest results folder',command=self.open_results).pack(side='left')
        ttk.Checkbutton(row,text='Resource diagnostics',variable=self.diagnostics,command=self.toggle_diagnostics).pack(side='left')
        ttk.Label(window,textvariable=self.performance_line,wraplength=780).pack(anchor='w')
        self.log_text=tk.Text(window,background='#0d1820',foreground='#cee0e6',wrap='word',font=('Consolas',10))
        self.log_text.pack(fill='both',expand=True);return window

    def refresh_logs(self):
        text='No owned preview log yet.'
        if self.output:
            try:
                path=self.output/'run.log'
                with path.open('rb') as handle:
                    handle.seek(max(0,path.stat().st_size-32768));text=handle.read(32768).decode('utf8',errors='replace')
                text=str(path)+'\n\n'+text
            except OSError as exc:text=str(exc)
        if text!=getattr(self,'last_log_text',None):
            self.log_text.configure(state='normal');self.log_text.delete('1.0','end');self.log_text.insert('end',text);self.log_text.configure(state='disabled');self.last_log_text=text

    def layout_sizes(self):
        return {name:[pane.sashpos(i) for i in range(len(pane.panes())-1)] for name,pane in
                (('vertical',self.vertical),('upper',self.upper),('right',self.right),('lower',self.lower))}

    def restore_sizes(self,data):
        self.root.update_idletasks()
        if not self.root.winfo_ismapped() or self.upper.winfo_width()<500:
            if not self.manager.closing:self.root.after(80,lambda:self.restore_sizes(data))
            return
        width=self.upper.winfo_width();height=self.vertical.winfo_height()
        defaults={'vertical':[max(420,height-245)],'upper':[290,max(590,width-360)],
                  'right':[max(160,(height-245)*.37),max(320,(height-245)*.74)],'lower':[width*.61]}
        if len(self.upper.panes())==2:defaults['upper']=[max(320,width-360)]
        for name,pane in (('vertical',self.vertical),('upper',self.upper),('right',self.right),('lower',self.lower)):
            extent=pane.winfo_width() if name in ('upper','lower') else pane.winfo_height()
            values=data.get(name,defaults[name])
            if not isinstance(values,list) or len(values)!=len(pane.panes())-1:values=defaults[name]
            for i,value in enumerate(values):
                if type(value) in (int,float):pane.sashpos(i,max(80,min(int(value),extent-80)))

    def install_playback_shortcuts(self):
        # The existing first bindtag consumes handled buttons once, including
        # Space on BONK, while text and SliderKeyboard retain their bindings.
        super().install_playback_shortcuts()
        tag='ZeraWaveStudioPlayback'+str(self.root.winfo_id())
        def attach(widget):
            if tag not in widget.bindtags():widget.bindtags((tag,*widget.bindtags()))
            for child in widget.winfo_children():attach(child)
        self.root.bind_all('<Map>',lambda e:attach(e.widget),add='+')
        self.root.bind_all('<FocusOut>',lambda e:self.root.after_idle(self.workspace_focus_check),add='+')

    def workspace_focus_check(self):
        self.release_tool_holds()

    def playback_key_press(self,event):
        cls=event.widget.winfo_class()
        if cls in ('Entry','TEntry','Text','TCombobox','TSpinbox','Scale','TScale','TRadiobutton','TCheckbutton','TMenubutton'):return
        # Space activates the focused button exactly once through its native
        # class binding, including help/profile actions and BONK itself.
        if cls in ('TButton','Button','Treeview','Listbox') and event.keysym=='space':return
        # Existing session actions win Ctrl+S; Ctrl+Shift+S remains Stop.
        if event.widget.winfo_toplevel()!=self.root:
            if event.keysym in ('Shift_L','Shift_R','space') or event.state&4:
                original=event.widget
                class Proxy:
                    def winfo_toplevel(s):return self.root
                    def winfo_class(s):return original.winfo_class()
                from types import SimpleNamespace
                event=SimpleNamespace(keysym=event.keysym,state=event.state,widget=Proxy())
        return super().playback_key_press(event)

    def close(self):
        if not self.manager:return super().close()
        self.release_tool_holds();self.manager.save();self.manager.closing=True
        self.stop()
        if self.star_tuning_window:self.star_tuning_window.close()
        self.waveform.close();self.root.destroy()


def main():
    dpi_awareness()
    root=tk.Tk();Workspace(root);root.mainloop()


if __name__=='__main__':main()
