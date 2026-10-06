"""Compact presentations of existing inspectors; no additional controllers."""
import tkinter as tk
from tkinter import ttk


def walk(widget):
    yield widget
    for child in widget.winfo_children(): yield from walk(child)


def explanations(window):
    notes = []
    for widget in list(walk(window)):
        if isinstance(widget, ttk.Label):
            text = str(widget.cget('text'))
            if len(text) > 100 and not str(widget.cget('textvariable')):
                notes.append(text)
                if widget.winfo_manager() == 'pack': widget.pack_forget()
            try: widget.configure(wraplength=300)
            except tk.TclError: pass
        elif isinstance(widget, ttk.Combobox): widget.configure(width=20)
    return notes


def compact_colors(editor):
    window = editor.window; editor.help_notes = explanations(window)
    # All groups remain live, in the same body; only their geometry changes.
    body = editor.fields.master
    palettes = next(w for w in body.winfo_children() if isinstance(w, ttk.LabelFrame))
    wheel = editor.wheel.master
    actions = editor.buttons[0].master; presets = editor.buttons[-1].master
    tabs = ttk.Notebook(body)
    tabs.pack(fill='both', expand=True, before=palettes)
    pages = {}
    for title in ('Pigments', 'Palette timing', 'Presets & reset'):
        pages[title] = ttk.Frame(tabs); tabs.add(pages[title], text=title)
    for widget in body.winfo_children():
        if isinstance(widget,ttk.Label) and str(widget.cget('textvariable'))==str(editor.note):
            widget.pack_forget();widget.pack(in_=pages['Presets & reset'],fill='x');widget.tk.call('raise',widget._w)
    editor.scope_summary=tk.StringVar()
    ttk.Label(body,textvariable=editor.scope_summary,wraplength=290,foreground='#98b9c5').pack(before=tabs,anchor='w')
    editor.swatch_strip=ttk.Frame(body);editor.swatch_strip.pack(before=tabs,fill='x',pady=4)
    # Validation/transport errors belong beside the controls being edited,
    # while the full reset/save destinations remain in their dedicated tab.
    inline_error=ttk.Label(body,textvariable=editor.app.color_status,wraplength=290,foreground='#d8b390')
    def show_error(*args):
        status=editor.app.color_status.get().lower()
        if status.startswith(('invalid','rejected','error','unavailable')) or 'failed' in status:
            inline_error.pack(before=tabs,fill='x',pady=(0,3))
        else:inline_error.pack_forget()
    editor.app.color_status.trace_add('write',show_error);show_error()
    update_color_summary(editor)
    for widget, page in ((editor.fields,'Pigments'),(wheel,'Pigments'),
                         (palettes,'Palette timing'),(actions,'Presets & reset'),(presets,'Presets & reset')):
        widget.pack_forget(); widget.pack(in_=pages[page], fill='x', pady=4)
        widget.tk.call('raise',widget._w)
    for w in wheel.winfo_children():
        w.pack_configure(side='top', fill='x')
    for frame in (actions, presets):
        for w in frame.winfo_children(): w.pack_configure(side='top', fill='x', padx=0, pady=3)
    # Palette operations keep complete labels and their existing callbacks.
    for i, w in enumerate(palettes.winfo_children()):
        w.grid_configure(row=i, column=0, columnspan=1, sticky='ew')
        if isinstance(w, ttk.Frame):
            for child in w.winfo_children(): child.pack_configure(side='top', anchor='w')
    palettes.columnconfigure(0, weight=1)
    editor.compact_tabs = tabs


def update_color_summary(editor):
    from color_controls import resolved_slots,rgb_hex
    target=editor.target()
    active=editor.app.active_color_scene
    editor.scope_summary.set(('Source pigments · '+target.scene+'\n')+('Live / parked by compatibility' if active else 'Parked · next compatible preview'))
    key=(target.id,tuple(rgb_hex(v[0]) for v in resolved_slots(target,editor.app.color_overrides)))
    if key==getattr(editor,'swatch_identity',None):return
    editor.swatch_identity=key
    for child in editor.swatch_strip.winfo_children():child.destroy()
    for slot,values in zip(target.slots,resolved_slots(target,editor.app.color_overrides)):
        button=tk.Button(editor.swatch_strip,background=rgb_hex(values[0]),activebackground=rgb_hex(values[0]),
                         width=3,height=1,relief='flat',command=lambda k=slot.id:editor.choose_role(k),takefocus=True)
        button.pack(side='left',padx=3)


def compact_tuning(view):
    window = view.window; view.help_notes = explanations(window)
    pinned = view.form_selector.master.master
    for w in list(pinned.winfo_children()):
        if isinstance(w, ttk.Label) and str(w.cget('text')) == 'Audio tuning': w.pack_forget()
    row = view.form_selector.master
    for child in row.winfo_children():
        if isinstance(child, ttk.Checkbutton): child.pack_forget()
    view.form_selector.pack_configure(side='top', fill='x')
    view.selector.pack_configure(fill='x')
    for widget in pinned.winfo_children():
        if isinstance(widget,ttk.Label) and str(widget.cget('textvariable'))==str(view.target_info):widget.pack_forget()
    buttons = ttk.Frame(row); buttons.pack(fill='x', pady=3)
    ttk.Radiobutton(buttons, text='Follow', variable=view.pin, value=False, command=view.pin_changed).pack(side='left', expand=True)
    ttk.Radiobutton(buttons, text='Pin', variable=view.pin, value=True, command=view.pin_changed).pack(side='left', expand=True)
    outer = view.viewport.master
    outer.pack_forget(); view.spectrum.frame.pack_forget(); view.detector_canvas.pack_forget()
    tabs = ttk.Notebook(pinned); tabs.pack(fill='both', expand=True)
    controls = ttk.Frame(tabs); listening = ttk.Frame(tabs)
    tabs.add(controls, text='Controls'); tabs.add(listening, text='Listening & FFT')
    outer.pack(in_=controls, fill='both', expand=True)
    view.spectrum.frame.pack(in_=listening, fill='x')
    view.detector_canvas.pack(in_=listening, fill='x')
    for widget in (outer,view.spectrum.frame,view.detector_canvas):widget.tk.call('raise',widget._w)
    view.spectrum.canvas.configure(height=80)
    view.spectrum.legend_label.pack_forget()
    pinned.pack_configure(fill='both', expand=True)
    # Retain every control slot and keyboard handler. Labels above each slider
    # avoid truncating artistic roles; values retain their full precision.
    for i, (label, slider, value) in enumerate(view.control_rows):
        label.configure(width=0, wraplength=290); value.configure(width=0)
        label.grid_configure(row=i*2, column=0, columnspan=2, sticky='w')
        slider.grid_configure(row=i*2+1, column=0, columnspan=1, sticky='ew', padx=0)
        value.grid_configure(row=i*2+1, column=1, sticky='e')
    view.control_grid.columnconfigure(0, weight=1); view.control_grid.columnconfigure(1, weight=0)
    for i, check in enumerate(view.range_checks.values()):
        check.grid_configure(row=len(view.sliders)*2+i, column=0, columnspan=2)
    # Named profiles and explicit authored promotion get their own tab while
    # status, ACK scope and dependency information stay visible in the controls.
    shell = view.shell
    profile_frames = [w for w in shell.winfo_children() if isinstance(w, ttk.LabelFrame)]
    profile_tabs = ttk.Notebook(shell); profile_tabs.pack(fill='x', pady=5)
    profile_page = ttk.Frame(profile_tabs); profile_tabs.add(profile_page, text='Profiles & authored')
    for frame in profile_frames:
        frame.pack_forget(); frame.pack(in_=profile_page, fill='x', pady=4)
        frame.tk.call('raise',frame._w)
        for w in frame.winfo_children():
            if w.winfo_manager() == 'pack': w.pack_configure(side='top', fill='x', pady=3, padx=0)
    for w in view.reset_row.winfo_children(): w.pack_configure(side='top', fill='x', padx=0, pady=2)
    # Long live explanations are still current when opened through ?. Essential
    # scope, compatibility, destination and failure labels remain on the panel.
    for w in shell.winfo_children():
        if isinstance(w, ttk.Label) and str(w.cget('textvariable')) == str(view.help_text): w.pack_forget()
    view.compact_tabs = tabs


def compact_monitor(view):
    view.help_notes = explanations(view.window)
    shell = view.table.master
    shell.pack_forget(); view.bands.pack_forget()
    tabs = ttk.Notebook(view.window); tabs.pack(fill='both', expand=True)
    summary = ttk.Frame(tabs); detail = ttk.Frame(tabs)
    tabs.add(summary, text='Mapping'); tabs.add(detail, text='Full values')
    for widget in list(view.window.winfo_children()):
        if isinstance(widget,ttk.Label):
            widget.pack_forget();widget.pack(in_=detail,fill='x');widget.tk.call('raise',widget._w)
    view.compact_source=tk.StringVar(value='No current source')
    ttk.Label(summary,textvariable=view.compact_source,wraplength=300).pack(anchor='w')
    view.trace = tk.Canvas(summary, background='#101a20', height=75, highlightthickness=0)
    view.trace.pack(fill='x')
    view.trace_caption = tk.StringVar(value='Analyzer bass / selected submitted input · CPU values')
    ttk.Label(summary, textvariable=view.trace_caption, wraplength=300).pack(anchor='w')
    view.trace_items = [view.trace.create_line(0,0,0,0,fill=color,width=1.5) for color in ('#c7875a','#39c4df')]
    from collections import deque
    view.trace_history = deque(maxlen=90); view.trace_identity = None
    view.bands.pack(in_=detail, fill='x')
    view.bands.tk.call('raise',view.bands._w)
    for i, (label, bar) in enumerate(zip(view.band_labels, view.band_bars)):
        label.configure(width=0); label.grid_configure(row=(i//3)*2, column=i%3)
        bar.grid_configure(row=(i//3)*2+1, column=i%3); bar.configure(length=75)
    shell.pack(in_=detail, fill='both', expand=True)
    shell.tk.call('raise',shell._w)
    view.table.configure(height=10)
    horizontal = ttk.Scrollbar(shell, orient='horizontal', command=view.table.xview)
    view.table.configure(xscrollcommand=horizontal.set); horizontal.pack(side='bottom', fill='x', before=view.table)
    view.compact_tabs = tabs


def update_trace(view, latest):
    import time
    if not latest or time.perf_counter()-latest[1] > 1.5:
        view.trace.itemconfigure('all', state='hidden'); return
    packet = latest[0]
    from pathlib import Path
    view.compact_source.set(str(packet.get('source_mode',''))+' · '+Path(str(packet.get('source_identity',''))).name+'\n'+str(packet.get('editing_target','')))
    identity = (packet.get('rendered_wall'), packet.get('editing_target'))
    if identity != view.trace_identity:
        target = packet.get('audio_targets', {}).get(packet.get('editing_target'), {})
        submissions = target.get('submissions', {})
        chosen = next(((k,v) for k,v in submissions.items() if isinstance(v, dict) and type(v.get('input')) in (int,float)), None)
        if not chosen or packet.get('audio_age_seconds') is None or packet['audio_age_seconds'] > 1.5:
            view.trace_caption.set('No current mapped input'); return
        if view.trace_identity and identity[1] != view.trace_identity[1]: view.trace_history.clear()
        view.trace_history.append((float((packet.get('audio') or {}).get('legacy',{}).get('bass',0)),float(chosen[1]['input'])))
        view.trace_caption.set('Analyzer bass / '+chosen[0]+' submitted input · CPU values')
        view.trace_identity = identity
    width = max(1, view.trace.winfo_width()); height = max(1, view.trace.winfo_height())
    for channel, item in enumerate(view.trace_items):
        points = [coordinate for i, pair in enumerate(view.trace_history)
                  for coordinate in (i*width/89, height-5-max(0,min(1,pair[channel]))*(height-10))]
        if len(points) >= 4: view.trace.coords(item,*points); view.trace.itemconfigure(item,state='normal')
