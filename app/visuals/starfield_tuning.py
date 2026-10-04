"""One Audio tuning window with Starfield and local Living Artifacts adapters."""
import json
import time
from copy import deepcopy
from band_attack_tuning import (BASELINE,WINDOW_BASELINE,WINDOW_BOUNDS,validate,
    window_settings,curve_weights,BandAttackTuning,PRESENTATION_BOUNDS)
from spectrum_widget import SpectrumTarget,SpectrumRange,SpectrumFeed,SpectrumWidget,frequencies,valid_packet
from star_tuning_profiles import StarProfileStore,TargetProfileStore,SHIPPED,TARGET,require_bins
from slider_keyboard import SliderKeyboard
from artifacts_audio_tuning import (TARGET as ART_TARGET,BASELINE as ART_BASELINE,BOUNDS as ART_BOUNDS,
    TITLES as ART_TITLES,validate as validate_artifacts,ArtifactsAudioTuning,require_listening_bins)

from planet_audio_tuning import SPECS,PlanetAudioTuning,bounds as planet_bounds,titles as planet_titles,validate as validate_planet,scoped_note
from planet_audio_tuning import WINDOWS as PLANET_WINDOWS,STAR_WINDOWS
from artifacts_audio_tuning import WINDOWS as ART_WINDOWS
from spectral_listening import listening_bounds,listening_choices,require_listening_bins as require_windows_bins,ListeningHub
from planet_listening import STYLES,titles as listening_titles
from audio_controls import TARGETS as FORM_TARGETS,form_targets,validate_target,bounds as form_bounds,titles as form_titles,windows as form_windows
from audio_scope import Scope,SaveTicket
from transition_catalog import SCENES
EDIT_FORMS={**SCENES,0:'Transitions'}
STAR_BOUNDS=dict(WINDOW_BOUNDS,**PRESENTATION_BOUNDS,**listening_bounds(STAR_WINDOWS))
STAR_TITLES=dict(chorus_light='Chorus -> star light',chorus_presence='Chorus -> star presence',chorus_twinkle='Chorus -> steady star twinkle',legacy_wake='Chorus -> legacy wakes (pilot OFF)',flux_clock='Flux -> shared sky clock',sparkle_clock='Sparkle -> shared sky clock')
MAPPED=(TARGET,ART_TARGET)+tuple(SPECS)
ALL_MAPPED=MAPPED+tuple(FORM_TARGETS)
PREFIX='ZERAWAVE_STAR_TUNING '
MAX_PACKET=131072
STAR_TARGET=SpectrumTarget('Planet background stars',((20.,315.),),
    'Attack contribution -> travel-speed pulses / trail length',TARGET)

# Existing audio-responsive groups only. Metadata does not register new adapters.
# IDs describe actual shared groups, not invented per-object routes.
def target_inventory():
    from preview_layers import MATERIALS,SPATIAL_TREATMENTS,ENVELOPERS,EFFECTS
    result=[STAR_TARGET]
    def add(key,label,feature):result.append(SpectrumTarget(label,(),feature,'planet.'+key))
    material_drivers={'artifacts':'Local flux stretch, impact facets, sparkle light/presence and bass cell/radial gains; optional local listening ranges',
        'alloy':'Bass shape, flux deformation, sparkle glint, impact sheen',
        'lattice':'Bass size, flux / sparkle / impact accents',
        'echo_weave':'Bass / flux ink travel; bass / raw-onset injection; sparkle unused',
        'ink_archipelago':'Bass vein spacing; sparkle / flux highlights',
        'interference_silk':'Bass / sparkle crest',
        'cellular_mosaic':'Bass growth; sparkle / flux seams'}
    for key in MATERIALS:add('material.'+key,EFFECTS[key][0],material_drivers[key])
    for key in ('tunnel','fractal','horizon'):
        add('spatial.'+key,EFFECTS[key][0],'Existing shared scale / flux energy response; authored cycles retained')
    for key in SPATIAL_TREATMENTS:
        add('spatial.'+key,EFFECTS[key][0],'Existing shared scale / flux drive'+
            ('; optional measured spread/fullness amount mapping' if key!='nested_windows' else ''))
    for key,feature in (('sparkles','Sparkle-linked light'),('flecks','Sparkle-linked intensity'),
                        ('beams','Impact / flux / sparkle event gate')):
        add('fx.'+key,EFFECTS[key][0],feature)
    for key in ENVELOPERS:add('enveloper.'+key,EFFECTS[key][0],'Existing shared audio energy in postprocess')
    add('rings','Planet rings','Shared sparkle and surface color response; no frequency adapter')
    add('moon_dust','Moon dust wakes (shared group)','Shared sparkle / flux strength; time-driven orbit paths')
    add('shooting_stars','Shooting stars','Existing sparkle / impact intensity; time-driven births')
    add('surface_response','Planet surface color response','Existing scale / flux / sparkle response; no palette controls here')
    return tuple(result)

TARGETS=target_inventory()

def choices_for_form(form):
    keys=form_targets(form)
    return tuple(t for t in TARGETS if t.target_id in keys)+tuple(SpectrumTarget(p['label'],(),p['scope'],key) for key,p in FORM_TARGETS.items() if key in keys)

def artifact_spectrum_ranges(packet,stale=False):
    """Display both acknowledged windows; never substitute unacknowledged edits."""
    c=packet.get('effective',packet['settings']);result=[]
    for name in ART_WINDOWS:
        color,dash,label=STYLES[name]
        requested=c[name+'_range_enabled'];active=bool(packet.get('active') and not stale)
        row=packet.get('listening',{}).get(name,{})
        status='OFF - original feature' if not requested else 'stale ACK - hidden' if stale else 'target inactive - hidden' if not active else ''
        result.append(SpectrumRange(name,label,
            c[name+'_start_hz'],c[name+'_end_hz'],color,dash,enabled=bool(requested and active),
            ready=bool(row.get('ready')),status=status))
    return tuple(result)

def target_windows(target):
    return form_windows(target) if target in FORM_TARGETS else ART_WINDOWS if target==ART_TARGET else STAR_WINDOWS if target==TARGET else PLANET_WINDOWS.get(target,())

def target_spectrum_ranges(packet,target,stale=False):
    c=packet.get('effective',packet['settings']);result=[]
    active=bool(packet.get('active',packet.get('presentation_active',packet.get('pilot_active',False))) and not stale)
    for name in target_windows(target):
        color,dash,label=STYLES[name];requested=c.get(name+'_range_enabled',False)
        row=packet.get('listening',{}).get(name,{})
        status='OFF - original feature' if not requested else 'stale ACK - hidden' if stale else 'target inactive - hidden' if not active else ''
        result.append(SpectrumRange(name,label,c.get(name+'_start_hz',0.),c.get(name+'_end_hz',24000.),color,dash,
            enabled=bool(requested and active),ready=bool(row.get('ready')),status=status))
    return tuple(result)


def configure(renderer,analyzer,normal=False):
    from planet_canvas_dsp import held_planet
    if not normal and not held_planet(True,renderer.debug_state,renderer.debug_sequence,
                       renderer.transition_sequence,renderer.transition_settings):return
    if renderer.debug_state in (37,38,39,40):return
    store=StarProfileStore()
    if store.error:print('Starfield authored baseline unavailable; shipped values used: '+store.error,flush=True)
    renderer.star_tuning=BandAttackTuning(authored=store.authored)
    artifact_store=TargetProfileStore(ART_TARGET)
    if artifact_store.error:print('Living Artifacts authored baseline unavailable; shipped values used: '+artifact_store.error,flush=True)
    renderer.artifact_tuning=ArtifactsAudioTuning(artifact_store.authored)
    stores={target:TargetProfileStore(target) for target in SPECS}
    renderer.planet_audio_tuning=PlanetAudioTuning({target:store.authored for target,store in stores.items()})
    for target,store in stores.items():
        if store.error:print(target+' authored baseline unavailable; neutral values used: '+store.error,flush=True)
    from spectral_listening import SpectralListening
    analyzer._artifact_listening=SpectralListening(renderer.artifact_tuning.analysis_settings)
    configurations={target:(lambda t=target:renderer.planet_audio_tuning.analysis_settings(t)) for target in SPECS}
    configurations[TARGET]=renderer.star_tuning.listening_settings
    analyzer._planet_listening=ListeningHub(configurations)
    renderer.star_spectrum=SpectrumFeed()
    if getattr(renderer,'planet_star_attack_pilot',False) and renderer.planet_star_attack_eligible():
        analyzer._planet_star_tuning=renderer.star_tuning
    if normal:
        from studio_audio import configure as configure_normal
        if configure_normal(renderer,analyzer) is not None:
            # Promote the accepted Star adapter only in the normal owned Studio
            # path. Descriptor modulation retains its explicit saved opt-in.
            renderer.planet_star_attack_pilot=True
            analyzer._planet_star_tuning=renderer.star_tuning


def observe_spectrum(renderer,frame,count,stamp=None):
    feed=getattr(renderer,'star_spectrum',None)
    if feed is not None:feed.observe(frame,count,stamp)
    owner=getattr(renderer,'studio_audio',None)
    if owner is not None:owner.observe(frame,count,stamp)


def decode(text):
    if len(text.encode())>MAX_PACKET:return None
    try:
        p=json.loads(text)
        if not isinstance(p,dict) or p.get('version')!=1 or type(p.get('pilot_active')) is not bool:return None
        validate(p.get('settings'))
        for key in ('effective','authored'):
            if key in p:validate(p[key])
        if p.get('spectrum') is not None and not valid_packet(p['spectrum']):return None
        a=p.get('artifact_tuning')
        if a is not None:
            if not isinstance(a,dict) or a.get('target')!=ART_TARGET or type(a.get('version')) is not int or a['version'] not in (1,2) or type(a.get('active')) is not bool:return None
            for key in ('settings','authored','effective'):validate_artifacts(a.get(key))
        grouped=p.get('planet_tuning',{})
        if not isinstance(grouped,dict) or not set(grouped)<=set(SPECS):return None
        for target,row in grouped.items():
            if not isinstance(row,dict) or row.get('target')!=target or row.get('version')!=1 or type(row.get('active')) is not bool:return None
            for key in ('settings','authored','effective'):validate_planet(target,row.get(key))
        return p
    except (ValueError,TypeError,RecursionError):return None


class StarfieldTuningWindow:
    def __init__(self,parent,submit,observe,store=None,artifact_store=None,normal=False):
        import tkinter as tk
        from tkinter import ttk
        self.window=tk.Toplevel(parent);self.window.title('Audio tuning - current Planet Canvas preview')
        self.window.geometry('900x860');self.submit=submit;self.observe=observe
        self.normal=normal;self.form=5;self.identity=None;self.received=None
        self.store=store or StarProfileStore();self.authored=deepcopy(self.store.authored)
        self.stores={TARGET:self.store,ART_TARGET:artifact_store or TargetProfileStore(ART_TARGET)}
        self.stores.update({target:TargetProfileStore(target) for target in SPECS})
        if normal:self.stores.update({target:TargetProfileStore(target) for target in FORM_TARGETS})
        self.target_states={};self.bounds=STAR_BOUNDS;self.control_keys=list(STAR_BOUNDS)
        self.pending=None;self.refreshing=False;self.revision=None;self.last_packet=None;self.running=False
        self.author_pending=None;self.profile_pending=None
        self.selection_error=None;self.last_applied_revision=None;self.legacy_settings=None;self.representable=True
        self.paint_at=None;self.paint_interval=None;self.refresh_cpu_ms=None
        self.vars={};self.labels={};self.sliders=[];self.frequency_sliders=[];self.focus_labels=[];self.control_rows=[]
        self.target_var=tk.StringVar(value=STAR_TARGET.label);self.target=STAR_TARGET
        pinned=ttk.Frame(self.window,padding=(16,12,16,0));pinned.pack(fill='x')
        ttk.Label(pinned,text='Audio tuning',font=('Segoe UI',15)).pack(anchor='w')
        self.pin=tk.BooleanVar(value=False);self.form_var=tk.StringVar(value=SCENES[5]);self.playback=tk.StringVar()
        if normal:
            self.window.title('Audio tuning - Main forms')
            form_row=ttk.Frame(pinned);form_row.pack(fill='x')
            self.form_selector=ttk.Combobox(form_row,textvariable=self.form_var,values=list(EDIT_FORMS.values()),state='readonly',width=30)
            self.form_selector.pack(side='left');self.form_selector.bind('<<ComboboxSelected>>',self.select_form)
            ttk.Checkbutton(form_row,text='Pin editing destination',variable=self.pin,command=self.pin_changed).pack(side='left',padx=8)
            ttk.Label(pinned,textvariable=self.playback,wraplength=810).pack(anchor='w',pady=3)
        selector=ttk.Combobox(pinned,textvariable=self.target_var,values=[t.label for t in (choices_for_form(5) if normal else TARGETS)],state='readonly',width=50)
        self.selector=selector
        selector.pack(anchor='w',pady=4);selector.bind('<<ComboboxSelected>>',self.select_target)
        self.target_info=tk.StringVar();ttk.Label(pinned,textvariable=self.target_info,wraplength=810).pack(anchor='w')
        ttk.Label(pinned,text='Form-owned authored settings; Pin changes editing scope only. Timers and shared dependencies are labeled.' if normal else '24 editable target adapters / '+str(len(TARGETS))+' existing audio-responsive groups. '
            'Moon bodies: time-driven orbit group; excluded. Palette pickers and independent clocks are excluded.',
            wraplength=810).pack(anchor='w',pady=3)
        self.spectrum=SpectrumWidget(pinned,STAR_TARGET);self.spectrum.frame.pack(fill='x',pady=6)
        # Keep all four existing Starfield rows reachable in the initial viewport.
        # The spectrum remains pinned; the complete control area scrolls below.
        self.spectrum.canvas.configure(height=150)
        self.detector_canvas=tk.Canvas(pinned,height=52,background='#111827',highlightthickness=0)
        self.detector_canvas.pack(fill='x')
        self.detector_items=[(self.detector_canvas.create_line(0,0,0,0,width=5,fill='#d69bff'),
            self.detector_canvas.create_line(0,0,0,0,width=2,fill='#ff8c8c'),
            self.detector_canvas.create_text(0,0,anchor='w',fill='#b7c4d7',font=('Segoe UI',8))) for _ in range(3)]
        outer=ttk.Frame(self.window);outer.pack(fill='both',expand=True)
        viewport=tk.Canvas(outer,highlightthickness=0,background='#141a28')
        scroll=ttk.Scrollbar(outer,orient='vertical',command=viewport.yview)
        viewport.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');viewport.pack(fill='both',expand=True)
        self.viewport=viewport
        shell=ttk.Frame(viewport,padding=16);self.shell=shell;item=viewport.create_window((0,0),window=shell,anchor='nw')
        shell.bind('<Configure>',lambda event:viewport.configure(scrollregion=viewport.bbox('all')))
        viewport.bind('<Configure>',lambda event:viewport.itemconfigure(item,width=event.width))
        self.enabled=tk.BooleanVar(value=False)
        self.use_tuning_check=ttk.Checkbutton(shell,text='Live override (off = authored baseline)',
            variable=self.enabled,command=self.toggle);self.use_tuning_check.pack(anchor='w',pady=4)
        grid=ttk.Frame(shell);grid.pack(fill='x',pady=6);grid.columnconfigure(1,weight=1)
        titles={'start_hz':'Start frequency (Hz)','end_hz':'End frequency (Hz)',
                'weight':'Selected-window weight (x)','sensitivity':'Attack sensitivity (x)',**STAR_TITLES}
        self.keyboard=SliderKeyboard(self.window,focus_changed=self.focus_changed)
        pool_sizes=[len(STAR_BOUNDS),len(ART_BOUNDS),*(len(planet_bounds(t)) for t in SPECS)]
        if normal:pool_sizes.extend(len(form_bounds(t)) for t in FORM_TARGETS)
        for row in range(max(pool_sizes)):
            key=list(STAR_BOUNDS)[row] if row<len(STAR_BOUNDS) else 'unused_'+str(row)
            low,high=STAR_BOUNDS.get(key,(0.,2.))
            self.vars[key]=tk.DoubleVar(value=self.authored.get(key,1.));self.labels[key]=tk.StringVar()
            focus=tk.StringVar(value=titles.get(key,''));self.focus_labels.append((focus,titles.get(key,'')))
            title=ttk.Label(grid,textvariable=focus,width=29,wraplength=220)
            title.grid(row=row,column=0,sticky='w',pady=4)
            scale=ttk.Scale(grid,from_=low,to=high,variable=self.vars[key],command=lambda value,i=row:self.changed(self.control_keys[i]))
            scale.grid(row=row,column=1,sticky='ew',padx=8);self.sliders.append(scale)
            self.keyboard.add(scale,self.vars[key],low,high,1. if key.endswith('_hz') else .01,lambda i=row:self.changed(self.control_keys[i]))
            if key!='sensitivity':self.frequency_sliders.append(scale)
            value=ttk.Label(grid,textvariable=self.labels[key],width=22)
            value.grid(row=row,column=2,sticky='w')
            self.control_rows.append((title,scale,value))
        ttk.Label(shell,text='Keyboard: Left/Right 1 Hz or 0.01x per tap; hold repeats up to 4 increments per 80 ms. '
            'Up/Down focuses the next enabled slider. The > focus marker identifies the current slider.',wraplength=810).pack(anchor='w')
        self.compat=tk.StringVar();self.selection=tk.StringVar()
        for var in (self.compat,self.selection):ttk.Label(shell,textvariable=var,wraplength=810).pack(anchor='w',pady=3)
        self.help_text=tk.StringVar(value='Start inclusive / End exclusive, using actual FFT bins. Displayed Hz positions do not add '
            'resolution: current Hz/bin and selected centers are shown above/below. Weight 0 removes this window; '
            'weight 2 doubles contribution. The original 20-250 bin-count denominator remains fixed. '
            'Sensitivity above 1 lowers thresholds. These bands do not classify instruments.')
        self.star_help=self.help_text.get();ttk.Label(shell,textvariable=self.help_text,wraplength=810).pack(anchor='w',pady=5)
        self.unsupported=[];self.unsupported_vars=[];self.unsupported_rows=[]
        for title in ('Mid frequencies above 315 Hz','High frequencies through Nyquist'):
            row=ttk.Frame(shell);row.pack(fill='x',pady=2)
            self.unsupported_rows.append(row)
            enabled=tk.BooleanVar(value=False);amount=tk.DoubleVar(value=0);self.unsupported_vars.extend((enabled,amount))
            toggle=ttk.Checkbutton(row,text=title,variable=enabled,state='disabled');toggle.pack(side='left')
            weight=ttk.Scale(row,from_=0,to=2,variable=amount,state='disabled');weight.pack(side='left',padx=8)
            ttk.Label(row,text='Weight 0 - spectrum only; no extra attack-window detector.').pack(side='left')
            self.unsupported.extend((toggle,weight))
        row=ttk.Frame(shell);row.pack(fill='x',pady=5)
        self.reset_row=row
        self.reset_button=ttk.Button(row,text='Back to authored',command=self.reset);self.reset_button.pack(side='left')
        self.comparison_button=ttk.Button(row,text='Old 20-250 comparison',command=self.old_comparison);self.comparison_button.pack(side='left',padx=8)
        profiles=ttk.LabelFrame(shell,text='Named custom profiles (separate from authored baseline)',padding=8)
        profiles.pack(fill='x',pady=6);self.profile_name=tk.StringVar(value='My audio profile')
        self.name_entry=ttk.Entry(profiles,textvariable=self.profile_name,width=32);self.name_entry.pack(side='left')
        self.save_button=ttk.Button(profiles,text='Save profile',command=self.save_profile);self.save_button.pack(side='left',padx=6)
        self.load_button=ttk.Button(profiles,text='Load profile...',command=self.choose_profile);self.load_button.pack(side='left')
        author=ttk.LabelFrame(shell,text='AUTHOR Studio - explicit baseline promotion',padding=8);author.pack(fill='x',pady=6)
        self.author_button=ttk.Button(author,text='Save as authored baseline',command=self.save_authored);self.author_button.pack(anchor='w')
        ttk.Label(author,text='Persists the ACK-applied values for startup and Back to authored. '
            'Named profile Save/Load never changes this baseline.',wraplength=790).pack(anchor='w')
        self.profile_status=tk.StringVar(value=('Authored file error; shipped defaults used: '+self.store.error) if self.store.error else 'Startup uses the saved authored baseline; live edits are temporary.')
        ttk.Label(shell,textvariable=self.profile_status,wraplength=810).pack(anchor='w',pady=4)
        self.status=tk.StringVar(value='Waiting for a held Planet Canvas preview.')
        self.applied=tk.StringVar();self.input=tk.StringVar();self.cadence=tk.StringVar()
        for var in (self.status,self.applied,self.input,self.cadence):ttk.Label(shell,textvariable=var,wraplength=810).pack(anchor='w',pady=4)
        self.action_buttons=[self.reset_button,self.comparison_button,self.save_button,self.load_button,self.author_button]
        self.slot_vars=list(self.vars.values());self.slot_labels=list(self.labels.values())
        self.control_grid=grid;self.star_titles=titles
        self.range_vars={name:tk.BooleanVar(value=False) for name in STYLES};self.range_checks={}
        for i,(name,var) in enumerate(self.range_vars.items()):
            check=ttk.Checkbutton(grid,text=name.capitalize()+' listening range (off = original feature)',variable=var,
                command=lambda n=name:self.changed(n+'_range_enabled'))
            check.grid(row=len(self.sliders)+i,column=0,columnspan=3,sticky='w',pady=4);self.range_checks[name]=check
        self.configure_controls()
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.show_values();self.target_description()
        self.set_available(False)

    def focus_changed(self,index):
        for i,(var,title) in enumerate(self.focus_labels):var.set(('> ' if i==index else '')+title)
        key=self.control_keys[index] if index is not None else None
        name=key.split('_')[0] if key and key.endswith('_hz') and key.split('_')[0] in target_windows(self.target.target_id) else None
        self.spectrum.focus_range(name)
        if index is not None and hasattr(self,'viewport') and hasattr(self.viewport,'canvasy'):
            self.window.update_idletasks()
            scale=self.sliders[index];v=self.viewport
            y=scale.winfo_rooty()-self.shell.winfo_rooty();height=v.winfo_height();total=self.shell.winfo_height()
            top=v.canvasy(0)
            if y<top or y+scale.winfo_height()>top+height:
                v.yview_moveto(max(0.,min(1.,(y-8)/max(1,total))))

    def target_description(self):
        mapped=self.target.target_id in ALL_MAPPED
        self.target_info.set(self.target.feature+(' - Form-owned normal Studio adapter.' if mapped and self.normal else ' - Adapter available in held Planet Canvas.' if mapped else
            ' - Unavailable: audio tuning adapter not implemented. Existing behavior continues.'))

    def configure_controls(self):
        artifact=self.target.target_id==ART_TARGET
        mapped=self.target.target_id in ALL_MAPPED
        self.bounds=form_bounds(self.target.target_id) if self.target.target_id in FORM_TARGETS else ART_BOUNDS if artifact else STAR_BOUNDS if self.target.target_id==TARGET else planet_bounds(self.target.target_id) if mapped else {}
        titles=form_titles(self.target.target_id) if self.target.target_id in FORM_TARGETS else ART_TITLES if artifact else dict(self.star_titles,**listening_titles(STAR_WINDOWS)) if self.target.target_id==TARGET else planet_titles(self.target.target_id) if mapped else {}
        self.control_keys=list(self.bounds)+[None]*(len(self.sliders)-len(self.bounds))
        self.vars={key:self.slot_vars[i] for i,key in enumerate(self.bounds)}
        self.labels={key:self.slot_labels[i] for i,key in enumerate(self.bounds)}
        self.frequency_sliders=self.sliders[:3] if self.target.target_id==TARGET else []
        self.refreshing=True
        try:
            for i,scale in enumerate(self.sliders):
                key=self.control_keys[i];used=key is not None
                # grid_slaves() omits grid_remove() widgets, so retain every slot
                # explicitly to restore larger targets after smaller ones.
                for widget in self.control_rows[i]:
                    if used:widget.grid()
                    else:widget.grid_remove()
                if used:
                    low,high=self.bounds[key];scale.configure(from_=low,to=high)
                    old=self.keyboard.entries[i]
                    self.keyboard.entries[i]=(old[0],old[1],low,high,1. if key.endswith('_hz') else .01,old[5])
                else:scale.configure(state='disabled')
                self.focus_labels[i]=(self.focus_labels[i][0],titles.get(key,''))
            self.focus_changed(None)
            for name,check in self.range_checks.items():
                if name in target_windows(self.target.target_id):check.grid()
                else:check.grid_remove()
            for row in self.unsupported_rows:
                if self.target.target_id==TARGET:row.pack(fill='x',pady=2,before=self.reset_row)
                else:row.pack_forget()
            self.help_text.set('Audio tuning adapter not implemented for this group.' if not mapped else 'Gain 0 removes this audio contribution; 1 is authored strength; 2 doubles the input before its existing 0-1 ceiling. '
                'Flux stretch retains spatial stretch, impact facets retain geometric facets, and sparkle light retains base light. '
                'Bass cell scale changes only the artifact grid; bass radial changes only local displacement. Sparkle presence is separate from light. '
                'Shared domain pressure, impact warps and movement clocks continue unchanged. Rotation/lifetime remain clock-driven. '
                'Optional ranges reuse actual FFT bins: Start inclusive / End exclusive, 1 Hz positioning does not add FFT resolution. '
                'Ranges off retain original signals.' if artifact else self.star_help+' Presentation gains retain quiet bases. Shared sky clock also drives shooting-star births. Legacy-wake gain inactive with attack-flight pilot ON.' if self.target.target_id==TARGET else FORM_TARGETS[self.target.target_id]['scope'] if self.target.target_id in FORM_TARGETS else scoped_note(self.target.target_id,None))
            if mapped:
                self.help_text.set(self.help_text.get()+' Optional target windows: '+', '.join(target_windows(self.target.target_id))+'. '
                    'Each range OFF uses the original feature exactly. Start inclusive / End exclusive; 1 Hz positioning does not add FFT resolution. '
                    'Compound energy uses selected Bass/Flux/Sparkle ingredients; no independent Energy window. '
                    'Custom Impact detects positive change of one normalized selected-bin mean, not legacy max-of-three-band onset. '
                    'Custom sensitivity lowers that threshold only while its range is ON; it is not attack time. '
                    'The declared slider bounds retain each original normalized ceiling; wider shape/travel roles allow up to 4.')
        finally:self.refreshing=False

    def owner_key(self):
        return (*self.identity,self.form,self.target.target_id) if self.identity is not None else ('offline','offline',self.form,self.target.target_id)

    def park_edits(self):
        self.keyboard.stop()
        state={key:deepcopy(getattr(self,key)) for key in ('revision','author_pending','profile_pending')}
        state['unsent']=self.pending is not None
        if self.target.target_id in ALL_MAPPED:
            try:state['values']=self.settings()
            except ValueError:state['values']=None
        self.target_states[self.owner_key() if self.normal else self.target.target_id]=state
        if self.pending is not None:self.window.after_cancel(self.pending);self.pending=None

    def select_form(self,event=None,form=None,target=None):
        if not self.normal:return
        self.park_edits()
        self.form=form if form is not None else next(f for f,label in EDIT_FORMS.items() if label==self.form_var.get())
        if event is not None:self.pin.set(True)
        self.form_var.set(EDIT_FORMS[self.form]);choices=choices_for_form(self.form)
        self.selector.configure(values=[t.label for t in choices])
        if not choices:
            self.set_available(False);self.target_info.set('No declared audio target in this form.');return
        chosen=next((t for t in choices if t.target_id==target),choices[0]);self.target_var.set(chosen.label)
        self.select_target(park=False)

    def pin_changed(self):
        self.park_edits()
        self.observe(True,form=self.form,target=self.target.target_id,pin=self.pin.get())

    def select_target(self,event=None,park=True):
        if park:self.park_edits()
        candidates=choices_for_form(self.form) if self.normal else TARGETS
        self.target=next(t for t in candidates if t.label==self.target_var.get())
        key=self.target.target_id
        if key in self.stores:self.store=self.stores[key];self.authored=deepcopy(self.store.authored)
        state=self.target_states.get(self.owner_key() if self.normal else key,{})
        for field in ('revision','author_pending','profile_pending'):setattr(self,field,state.get(field))
        self.legacy_settings=None;self.representable=True;self.selection_error=None
        self.configure_controls();self.last_applied_revision=None
        self.spectrum.set_target(self.target);self.target_description()
        if self.normal:
            self.display_settings(state.get('values') or dict(self.authored,enabled=False))
            self.author_button.configure(text='Save Authored: '+EDIT_FORMS[self.form]+' / '+self.target.label)
            self.observe(True,form=self.form,target=key,pin=self.pin.get());self.set_available(False);return
        self.refresh((self.last_packet,time.perf_counter()) if self.last_packet else None,self.running)

    def set_available(self,active,pending=False):
        editable=active and self.target.target_id in ALL_MAPPED
        if not editable:self.keyboard.stop()
        for i,scale in enumerate(self.sliders):scale.configure(state='normal' if editable and self.control_keys[i] is not None else 'disabled')
        p=self.target_packet() or {}
        if self.target.target_id==TARGET and 'presentation_active' in p:
            pilot=p.get('pilot_active',False)
            for i,key in enumerate(self.control_keys):
                available=pilot if key in WINDOW_BOUNDS else not pilot if key=='legacy_wake' else True
                if not available:
                    self.sliders[i].configure(state='disabled')
                    self.focus_labels[i][0].set(self.focus_labels[i][1]+' [mode inactive]')
        if not self.representable:
            for scale in self.frequency_sliders:scale.configure(state='disabled')
            if self.target.target_id==TARGET:
                for scale in self.sliders[4:]:scale.configure(state='disabled')
        for button in self.action_buttons:button.configure(state='normal' if editable else 'disabled')
        if self.target.target_id!=TARGET:self.comparison_button.configure(state='disabled')
        for button in (self.save_button,self.author_button):
            if pending or not self.representable:button.configure(state='disabled')
        self.use_tuning_check.configure(state='normal' if editable else 'disabled')
        self.name_entry.configure(state='normal' if editable else 'disabled')
        for name,check in self.range_checks.items():check.configure(state='normal' if editable and name in target_windows(self.target.target_id) else 'disabled')
        for i,key in enumerate(self.control_keys):
            if key=='impact_sensitivity' and not self.range_vars['impact'].get():self.sliders[i].configure(state='disabled')

    def target_packet(self):
        if self.last_packet is None:return None
        if self.normal:
            p=self.last_packet.get('audio_targets',{}).get(self.target.target_id)
            if p is None:return None
            s=Scope.read(p.get('scope'))
            return p if (s.run,s.session)==self.identity and s.form==self.form and s.target==self.target.target_id else None
        return self.last_packet.get('artifact_tuning') if self.target.target_id==ART_TARGET else self.last_packet if self.target.target_id==TARGET else self.last_packet.get('planet_tuning',{}).get(self.target.target_id)

    def submit_current(self,c,authored=None):
        if self.normal:return self.submit(c,authored,target=self.target.target_id,form=self.form)
        if self.target.target_id!=TARGET:return self.submit(c,authored,target=self.target.target_id)
        return self.submit(c) if authored is None else self.submit(c,authored)

    def settings(self):
        if not self.enabled.get():return dict(self.authored,enabled=False)
        ranges={name+'_range_enabled':self.range_vars[name].get() for name in target_windows(self.target.target_id)}
        if self.target.target_id==ART_TARGET:return validate_artifacts(dict(enabled=True,
            **{key:var.get() for key,var in self.vars.items()},**ranges))
        if self.target.target_id in SPECS:return validate_planet(self.target.target_id,dict(enabled=True,**{key:var.get() for key,var in self.vars.items()},**ranges))
        if self.target.target_id in FORM_TARGETS:return validate_target(self.form,self.target.target_id,dict(enabled=True,**{key:var.get() for key,var in self.vars.items()},**ranges))
        if self.legacy_settings is not None:
            return validate(dict(self.legacy_settings,enabled=True,sensitivity=self.vars['sensitivity'].get()))
        return validate(dict(WINDOW_BASELINE,enabled=True,**{key:var.get() for key,var in self.vars.items()},**ranges))

    def show_values(self):
        for key,(low,high) in self.bounds.items():
            precision=1 if key.endswith('_hz') else 2
            self.labels[key].set(f'{self.vars[key].get():.{precision}f}  [{low:g}-{high:g}]')

    def toggle(self):
        if not self.enabled.get():self.reset()
        else:self.changed()

    def changed(self,key=None):
        if self.refreshing or self.target.target_id not in ALL_MAPPED:return
        if key and (key.endswith('_hz') or key.endswith('_range_enabled')) and key.split('_')[0] in target_windows(self.target.target_id):
            self.spectrum.focus_range(key.split('_')[0])
        self.selection_error=None
        if key is not None:self.enabled.set(True)
        if self.target.target_id==TARGET and key in ('start_hz','end_hz','weight') and self.representable:self.legacy_settings=None
        if self.target.target_id==TARGET and key in PRESENTATION_BOUNDS and self.representable:self.legacy_settings=None
        self.show_values();self.status.set('Pending - waiting for render acknowledgement.' if self.target.target_id==ART_TARGET else 'Pending - waiting for analysis acknowledgement.')
        if self.pending is None:self.pending=self.window.after(50,self.send)

    def send(self):
        self.pending=None
        if self.target.target_id not in ALL_MAPPED:return
        try:
            c=self.settings();s=(self.last_packet or {}).get('spectrum')
            if c.get('mode')=='window' and s is not None:require_bins(c,frequencies(s))
            if self.target.target_id==ART_TARGET and s is not None:require_listening_bins(c,[0.]+frequencies(s))
            if self.target.target_id!=ART_TARGET and s is not None and self.target.target_id in ALL_MAPPED:
                require_windows_bins(dict(self.authored,**c),target_windows(self.target.target_id),[0.]+frequencies(s))
        except ValueError as exc:
            self.selection_error=str(exc);self.status.set('Selection rejected: '+str(exc));return
        self.revision=self.submit_current(c)
        if self.revision is None:self.status.set('Unavailable - no active Planet Canvas connection.')

    def display_settings(self,c):
        self.refreshing=True
        try:
            self.enabled.set(c['enabled']);self.legacy_settings=deepcopy(c) if self.target.target_id==TARGET and c.get('mode')!='window' else None
            mapped=validate_target(self.form,self.target.target_id,c) if self.target.target_id in FORM_TARGETS else validate_artifacts(c) if self.target.target_id==ART_TARGET else validate_planet(self.target.target_id,c) if self.target.target_id in SPECS else window_settings(c);self.representable=mapped is not None
            if self.target.target_id==TARGET and mapped is not None:mapped=dict(SHIPPED,**mapped)
            for key,var in self.vars.items():var.set((mapped or dict(WINDOW_BASELINE,sensitivity=c['sensitivity'])).get(key,1.))
            for name,var in self.range_vars.items():var.set((mapped or {}).get(name+'_range_enabled',False))
            self.selection_error=None;self.show_values()
        finally:self.refreshing=False

    def reset(self):
        self.keyboard.stop();self.display_settings(dict(self.authored,enabled=False));self.changed()

    def old_comparison(self):
        if self.target.target_id!=TARGET:return
        self.keyboard.stop();self.display_settings(dict(SHIPPED,**WINDOW_BASELINE));self.changed()

    def ack_bins(self):
        p=self.target_packet()
        if self.normal:
            if not self.running or p is None or not p.get('available'):raise ValueError('Current scoped render acknowledgement required')
            s=Scope.read(p['scope']);expected=Scope(*self.identity,self.form,self.target.target_id,self.revision if self.revision is not None else s.revision)
            if self.pending is not None:raise ValueError('Wait for the current control acknowledgement')
            c=validate_target(self.form,self.target.target_id,dict(self.settings(),enabled=True))
            SaveTicket.acknowledged(expected,c,p,self.received)
            spectrum=self.last_packet.get('spectrum')
            bins=[0.]+frequencies(spectrum) if spectrum is not None and now_age(spectrum)<=1. else None
            require_windows_bins(c,target_windows(self.target.target_id),bins)
            if self.target.target_id==TARGET:require_bins(c,bins)
            return bins
        if self.target.target_id not in ALL_MAPPED or not self.running or not p or not p.get('active',p.get('presentation_active',p.get('pilot_active',False))):
            raise ValueError('A current target ACK is required')
        if self.pending is not None or (self.revision is not None and p.get('revision',-1)<self.revision
                and p.get('rejected_revision')!=self.revision):
            raise ValueError('Wait for the current control acknowledgement')
        if self.target.target_id in SPECS:
            if time.perf_counter()-p['rendered_wall']>1.:raise ValueError('Current render ACK is required')
            s=self.last_packet.get('spectrum')
            if any(p['effective'][name+'_range_enabled'] for name in target_windows(self.target.target_id)):
                if s is None or now_age(s)>1.:raise ValueError('Current actual FFT bins required for listening ranges')
                return [0.]+frequencies(s)
            return None
        if self.target.target_id==ART_TARGET:
            if time.perf_counter()-p['rendered_wall']>1.:raise ValueError('Current render ACK is required')
            s=self.last_packet.get('spectrum')
            if any(p['effective'][name+'_range_enabled'] for name in ART_WINDOWS):
                if s is None or now_age(s)>1.:raise ValueError('Current actual FFT bins required for listening ranges')
            return [0.]+frequencies(s) if s is not None and now_age(s)<=1. else None
        s=p.get('spectrum');age=time.perf_counter()-p['rendered_wall'] if not p.get('pilot_active',False) and 'rendered_wall' in p else p.get('analysis_age_seconds')
        if s is None or age is None or age>1. or time.perf_counter()-s['observed_wall']>1.:
            raise ValueError('Current actual FFT bins are required; input is stale')
        return frequencies(s)

    def ack_settings(self):
        bins=self.ack_bins();p=self.target_packet()
        if self.normal:
            c=validate_target(self.form,self.target.target_id,p['effective'])
            if p['active']:
                for name in target_windows(self.target.target_id):
                    if c[name+'_range_enabled'] and not p.get('listening',{}).get(name,{}).get('ready'):raise ValueError('Wait for matching '+name+' input')
            if self.target.target_id==TARGET:
                c=window_settings(c)
                if c is None:raise ValueError('Legacy multiweight values cannot be saved as one window')
            return c,bins
        for name in target_windows(self.target.target_id):
            if p.get('effective',p['settings']).get(name+'_range_enabled') and not p.get('listening',{}).get(name,{}).get('ready'):
                raise ValueError('Wait for matching '+name+' analysis ACK')
        if self.target.target_id==ART_TARGET:
            for name in ('flux','sparkle'):
                if p['effective'][name+'_range_enabled'] and not p.get('listening',{}).get(name,{}).get('ready'):
                    raise ValueError('Wait for matching '+name+' analysis ACK')
            return validate_artifacts(p['effective']),bins
        if self.target.target_id in SPECS:return validate_planet(self.target.target_id,p['effective']),bins
        c=validate(p.get('effective',p['settings']))
        mapped=window_settings(c)
        if mapped is None:raise ValueError('Legacy multiweight settings cannot be saved as one window')
        require_bins(mapped,bins);return mapped,bins

    def save_profile(self):
        try:
            c,bins=self.ack_settings();path=self.store.save_profile(self.profile_name.get(),c,bins)
            self.profile_status.set('Saved named profile: '+str(path)+'; authored baseline unchanged.')
        except (OSError,ValueError,UnicodeError,RecursionError) as exc:self.profile_status.set('Profile save failed: '+str(exc))

    def load_profile(self,path):
        try:
            bins=self.ack_bins();name,c=self.store.load_profile(path,bins)
            self.display_settings(c);self.revision=self.submit_current(c);self.profile_name.set(name)
            self.profile_pending=self.revision
            self.profile_status.set('Loaded profile as live override; waiting for ACK. Authored baseline unchanged.' if self.revision is not None else 'Profile validated, but no active preview connection.')
            return self.revision is not None
        except (OSError,ValueError,UnicodeError,RecursionError) as exc:self.profile_status.set('Profile load rejected: '+str(exc));return False

    def choose_profile(self):
        from tkinter import filedialog
        self.keyboard.stop();owner=self.owner_key();revision=self.revision
        path=filedialog.askopenfilename(parent=self.window,title='Load '+self.target.label+' audio profile',
            initialdir=str(self.store.profile_dir),filetypes=[('Audio tuning profile','*.json')])
        if path:
            if self.normal and (owner!=self.owner_key() or revision!=self.revision):self.profile_status.set('Profile load cancelled: destination or revision changed.');return
            self.load_profile(path)

    def save_authored(self):
        owner=self.owner_key();revision=self.revision;store=self.store;target=self.target.target_id
        try:
            c,bins=self.ack_settings();authored=store.save_authored(c,bins)
        except (OSError,ValueError,UnicodeError,RecursionError) as exc:
            self.profile_status.set('Authored save failed; prior baseline retained: '+str(exc));return False
        if self.normal and (owner!=self.owner_key() or revision!=self.revision):
            self.profile_status.set('Saved acknowledged values to original destination '+target+'; current destination retained.');return True
        self.authored=authored
        current=dict(c,enabled=self.target_packet()['settings']['enabled'])
        self.revision=self.submit_current(current,authored)
        self.author_pending=(self.revision,deepcopy(authored)) if self.revision is not None else None
        destination=(EDIT_FORMS[self.form]+' / '+self.target.label+' -> '+str(self.store.authored_path)+'; ') if self.normal else ''
        self.profile_status.set(destination+('Authored baseline saved atomically; waiting for running-preview ACK.' if self.revision is not None else 'Authored baseline saved atomically; applies next launch (no active connection).'))
        return True

    def preview_started(self):
        self.keyboard.stop()
        if self.normal:self.park_edits();self.identity=None
        else:self.target_states={}
        try:self.authored=self.store.reload_authored()
        except (OSError,ValueError,UnicodeError,RecursionError) as exc:self.profile_status.set('Authored reload failed; last valid baseline retained: '+str(exc))
        if self.target.target_id in ALL_MAPPED:self.display_settings(dict(self.authored,enabled=False))
        else:self.enabled.set(False);self.legacy_settings=None;self.representable=True
        self.revision=None;self.last_packet=None;self.last_applied_revision=None;self.running=False
        self.author_pending=None;self.profile_pending=None
        if self.pending is not None:self.window.after_cancel(self.pending);self.pending=None
        self.spectrum.update(None,None);self.set_available(False)

    def alive(self):return bool(self.window.winfo_exists())

    def close(self):
        self.keyboard.close()
        if self.pending is not None:self.window.after_cancel(self.pending);self.pending=None
        self.observe(False);self.window.destroy()

    def refresh(self,latest,running):
        if self.normal:return self.refresh_normal(latest,running)
        now=time.perf_counter();self.running=running
        self.paint_interval=None if self.paint_at is None else (now-self.paint_at)*1000.;self.paint_at=now
        if not running or latest is None:
            self.detector_canvas.itemconfigure('all',state='hidden')
            self.detector_canvas.pack_forget()
            self.status.set('Unavailable - held Planet Canvas preview must be running.')
            self.set_available(False);self.spectrum.update(None,None);self.refresh_cpu_ms=(time.perf_counter()-now)*1000.;return
        full,received=latest;self.last_packet=deepcopy(full)
        p=self.target_packet()
        if p is None:
            self.status.set('Unavailable - restart preview to load this adapter.');self.set_available(False)
            s=full.get('spectrum');self.spectrum.update(s,[0.]*len(s['db']) if s else None,('unavailable',self.target.target_id))
            return
        artifact=self.target.target_id==ART_TARGET
        active=p.get('active',p.get('presentation_active',p.get('pilot_active',False)));c=p['settings'];applied=p.get('effective',c)
        pending=self.revision is not None and p.get('revision',-1)<self.revision
        rejected=self.revision is not None and p.get('rejected_revision')==self.revision
        if rejected:pending=False
        if 'authored' in p and not pending:self.authored=deepcopy(p['authored'])
        if self.author_pending is not None:
            revision,expected=self.author_pending
            if p.get('rejected_revision')==revision:
                self.profile_status.set('Authored file saved; running preview rejected the update. Applies next launch if its FFT bins support it.')
                self.author_pending=None
            elif p.get('revision',-1)>=revision and p.get('authored')==expected:
                self.profile_status.set('Authored baseline saved atomically and acknowledged by the running preview.')
                self.author_pending=None
        if self.profile_pending is not None:
            if p.get('rejected_revision')==self.profile_pending:
                self.profile_status.set('Profile update rejected by current analysis; prior applied settings retained.')
                self.profile_pending=None
            elif p.get('revision',-1)>=self.profile_pending:
                self.profile_status.set('Named profile acknowledged as a live override; authored baseline unchanged.')
                self.profile_pending=None
        selected=self.target.target_id in ALL_MAPPED
        if selected and self.pending is None and not pending and p.get('revision')!=self.last_applied_revision:
            self.display_settings(c);self.last_applied_revision=p.get('revision')
        age=now-p['rendered_wall'] if self.target.target_id!=TARGET or not p.get('pilot_active',False) and 'rendered_wall' in p else p.get('analysis_age_seconds');stale=now-received>1. or age is None or age>1.
        self.set_available(active and not stale,pending or self.pending is not None)
        self.compat.set(p['scope'] if self.target.target_id in SPECS else 'Target-local gains and optional selected-bin listening; shared signals/clocks unchanged. No extra FFT.' if artifact else 'Single-window controls. Curve shows ACK-applied coefficients.' if self.representable else
            'Legacy multiweight settings remain applied and cannot be represented by one window. '
            'Frequency and presentation controls are disabled; Back to authored explicitly clears the legacy override.')
        state='Unavailable - adapter not implemented; existing behavior continues' if not selected else (
            'Unavailable - target inactive; full spectrum only' if artifact and not active else 'BYPASS - star pilot OFF; full spectrum only' if not active else
            'STALE - no current detector input' if stale else 'AUTHORED baseline - live override OFF' if not c['enabled'] else 'LIVE override - '+p.get('state','target-local audio gains'))
        if selected and rejected:state='Selection rejected: '+str(p.get('error'))+'; prior applied settings retained'
        if selected and self.selection_error:state='Selection rejected: '+self.selection_error+'; prior applied settings retained'
        self.status.set(state+(' - control pending' if selected and pending else ''))
        self.applied.set((self.target.label+' applied revision '+str(p.get('revision'))+': '+', '.join(k+'='+str(v) for k,v in applied.items())) if selected else 'No applied tuning curve for this target.')
        s=full.get('spectrum')
        if s is not None:
            f=frequencies(s);weights=curve_weights(f,dict(applied,enabled=True)).tolist() if p.get('pilot_active',False) and selected and self.target.target_id==TARGET else [0.]*len(f)
            if artifact:
                windows=[row['measurement']['spec'][1:3] for row in p.get('listening',{}).values() if row['enabled'] and row['ready']]
                weights=[float(any(low<=hz<high for low,high in windows)) for hz in f]
                self.spectrum.heading.set('Full measured spectrum - Living artifacts; Flux + Sparkle listening windows')
            self.spectrum.update(s,weights,(p.get('revision'),active,selected),
                ranges=target_spectrum_ranges(p,self.target.target_id,stale),
                show_weight=bool(self.target.target_id==TARGET and p.get('pilot_active',False)))
            mapped=window_settings(applied) if self.target.target_id==TARGET else None
            centers=[hz for hz in f if mapped is not None and mapped['start_hz']<=hz<mapped['end_hz']]
            self.selection.set(('ACK window: '+str(len(centers))+' actual bin centers: '+', '.join(f'{hz:.4f}' for hz in centers)+' Hz') if selected and mapped is not None else
                'No FFT-window detector for this target; existing-feature gains are shown in the ACK values.' if artifact else 'No single-window adapter curve for this target/settings.')
        else:self.spectrum.update(None,None);self.selection.set(p.get('spectrum_error') or 'Waiting for actual FFT bin metadata.')
        def fmt(value):return 'N/A' if value is None else f'{value:.2f}'
        self.input.set(('Baseline mean '+fmt(p.get('baseline_level'))+' -> weighted '+fmt(p.get('weighted_level'))+
            ' | interval peak '+fmt(p.get('interval_peak'))+' | positive packets '+str(p.get('positive_packets'))+
            ' | accepted flight events '+str(p.get('accepted_events'))+
            ' (snapshot '+str(p.get('interval_positive_packets'))+' positive / '+str(p.get('interval_accepted_events'))+' accepted)') if selected else '')
        self.cadence.set('Input '+fmt(p.get('packet_audio_ms'))+' ms audio / '+fmt(p.get('analysis_wall_interval_ms'))+
            ' ms completion; snapshot '+fmt(p.get('snapshot_wall_interval_ms'))+' ms; GUI poll '+fmt(self.paint_interval)+
            ' ms; peak hold '+fmt(p.get('peakhold_window_ms'))+' ms. Received age '+fmt((now-received)*1000.)+
            ' ms; analyzed age '+fmt(None if age is None else age*1000.)+' ms.\nWidget update CPU (previous) '+
            fmt(self.refresh_cpu_ms)+' ms; native repaint not measured.')
        if artifact:
            self.input.set('Existing normalized inputs: '+str(p['inputs'])+'; target-local mapped inputs: '+str(p['local_inputs'])+'; audio terms: '+str(p['audio_terms']))
            details=[]
            for name,row in p.get('listening',{}).items():
                m=row.get('measurement')
                details.append(name+(': '+str(m['bins'])+' actual bins, '+str(m['first_hz'])+'..'+str(m['last_hz'])+' Hz; raw '+fmt(m['raw'])+' -> '+fmt(m['level']) if row['enabled'] and m else ': waiting for matching analysis' if row['enabled'] else ': original feature (range OFF)'))
            self.selection.set('; '.join(details))
            self.cadence.set('Current render ACK age '+fmt(age*1000.)+' ms; input snapshot present: '+str(p['input_present'])+
                '. Original features or enabled local windows from the same FFT. Native repaint not measured.')
        elif self.target.target_id in SPECS:
            self.input.set('Existing inputs: '+str(p['inputs'])+'; named contribution terms: '+str(p['audio_terms']))
            self.selection.set('Gains use original features or enabled local listening windows. '+('Current selection/weight enables this target; shader coverage/envelopes still apply.' if p['contributing'] else 'Current selection/weight excludes this target.' if p['contributing'] is False else 'Selection/weight availability not reported.'))
            self.cadence.set('Render ACK age '+fmt(age*1000.)+' ms; mode '+str(p['mode'])+'. Shared clocks/history retained.')
            for i,key in enumerate(self.control_keys):
                if key and not p['role_active'].get(key,True):
                    self.sliders[i].configure(state='disabled');self.focus_labels[i][0].set(self.focus_labels[i][1]+' [mode inactive]')
        elif not selected:self.compat.set('No tuning adapter; current audio-driven behavior continues.')
        if self.target.target_id in ALL_MAPPED:
            details=[]
            for name,row in p.get('listening',{}).items():
                m=row.get('measurement')
                details.append(name+(': '+str(m['bins'])+' actual bins '+str(m['first_hz'])+'..'+str(m['last_hz'])+' Hz; raw '+fmt(m['raw'])+' -> '+fmt(m['level']) if row['enabled'] and row['ready'] and m else ': waiting for matching analysis' if row['enabled'] else ': original feature (range OFF)'))
            if details:self.selection.set('; '.join(details))
        response=(p.get('detector_response') if self.target.target_id==TARGET and p.get('pilot_active') else None)
        impact_row=p.get('listening',{}).get('impact',{})
        if response:
            bars=(('Star level / floor',p.get('weighted_level',0.),response['level_floor']),
                  ('Star rise / floor',response['rise'],response['rise_floor']),
                  ('Star fraction / threshold',response['fraction'],response['fraction_floor']))
        elif impact_row.get('enabled') and impact_row.get('ready'):
            r=(impact_row.get('measurement') or {}).get('detector_response',{})
            bars=(('Custom-window onset rise / threshold',r.get('rise',0.),r.get('threshold',.2)),)
        else:bars=()
        if bars:self.detector_canvas.configure(height=16*len(bars)+4);self.detector_canvas.pack(fill='x')
        else:self.detector_canvas.pack_forget()
        self.detector_canvas.itemconfigure('all',state='hidden')
        for i,(label,value,threshold) in enumerate(bars):
            line,mark,text=self.detector_items[i];extent=max(.001,threshold*2.,value*1.1);y=8+i*16
            self.detector_canvas.coords(line,280,y,280+min(420,420*value/extent),y)
            self.detector_canvas.coords(mark,280+420*threshold/extent,y-5,280+420*threshold/extent,y+5)
            self.detector_canvas.coords(text,2,y)
            self.detector_canvas.itemconfigure(text,text=label+f' {value:.3f} / {threshold:.3f}')
            for item in (line,mark,text):self.detector_canvas.itemconfigure(item,state='normal' if active and not stale else 'hidden')
        self.refresh_cpu_ms=(time.perf_counter()-now)*1000.


    def refresh_normal(self,latest,running):
        now=time.perf_counter();self.running=bool(running)
        self.keyboard.stop() if not running else None
        self.detector_canvas.pack_forget()
        if not running or latest is None:
            self.set_available(False);self.status.set('No current scoped Studio connection. Unsaved edits remain at their original destination.');self.spectrum.update(None,None);return
        full,received=latest;identity=(full['identity']['run'],full['identity']['session'])
        if self.identity!=identity:
            self.park_edits();self.identity=identity;self.revision=None;self.author_pending=None;self.profile_pending=None;self.last_applied_revision=None
        self.last_packet=deepcopy(full);self.received=received
        endpoint=full['endpoints'];primary=endpoint['primary']
        playback=SCENES.get(primary,'Unavailable')
        if endpoint['incoming'] is not None:
            playback=SCENES[endpoint['outgoing']]+' -> '+SCENES[endpoint['incoming']]+' | '+str(endpoint.get('recipe'))+' | '+f"{endpoint['progress']*100:.0f}%"
        self.playback.set('Playback: '+playback+' | Editing: '+EDIT_FORMS[self.form]+(' [Pinned]' if self.pin.get() else ' [Following]'))
        if not self.pin.get() and full.get('editing_form') in SCENES and full['editing_form']!=self.form:
            self.select_form(form=full['editing_form'],target=full.get('editing_target'))
            self.last_packet=deepcopy(full)
        p=self.target_packet()
        if p is None:
            self.set_available(False);self.status.set('Waiting for acknowledgement of '+EDIT_FORMS[self.form]+' / '+self.target.label);return
        s=Scope.read(p['scope']);pending=self.pending is not None or (self.revision is not None and s.revision!=self.revision)
        rejected=p.get('rejected_revision')==self.revision and self.revision is not None
        if rejected:pending=False
        stale=now-received>1. or now-p['rendered_wall']>1.
        state=self.target_states.get(self.owner_key(),{})
        parked=state.get('values')
        retained=parked is not None and parked!=p['settings'] and (s.revision==0 or
            state.get('unsent',False) and s.revision==(state.get('revision') or 0))
        self.authored=deepcopy(p['authored'])
        if not pending and not rejected and s.revision!=self.last_applied_revision:
            if retained:
                self.display_settings(parked)
                self.status.set('Retained unsent edits for this destination. Edit a control to submit; Save requires matching ACK.')
            else:self.display_settings(p['settings'])
            self.last_applied_revision=s.revision
        self.set_available(bool(p.get('available') and not stale),pending)
        active=p.get('contributing',p['active']);self.compat.set(p.get('dependency',p.get('scope_note',FORM_TARGETS.get(self.target.target_id,{}).get('scope','Form-owned target.'))))
        self.status.set('Rejected: '+str(p.get('error')) if rejected else 'Stale acknowledgement' if stale else 'Waiting for scoped revision' if pending else 'Retained unsent edits at this destination; submit before saving.' if retained else ('Active' if active else 'Inactive / queued: settings editable; consumer telemetry unavailable')+' | '+('Live override' if p['settings']['enabled'] else 'Authored baseline'))
        self.applied.set(EDIT_FORMS[self.form]+' / '+self.target.label+' | run '+s.run[:8]+' | revision '+str(s.revision)+' | CPU submission, not GPU output')
        submissions=p.get('submissions',{})
        self.input.set('\n'.join(r['consumer']+' | '+r['source']+'='+str(round(r['input'],4))+' | submitted slot='+str(round(r['slot'],4)) for r in submissions.values()) if active else 'Target is inactive. Analyzer spectrum below is shared input, not target activity.')
        spectrum=full.get('spectrum');f=frequencies(spectrum) if spectrum else []
        star=self.target.target_id==TARGET and p.get('pilot_active',False)
        weights=curve_weights(f,dict(p['effective'],enabled=True)).tolist() if star else [0.]*len(f)
        self.spectrum.update(spectrum,weights,(s.run,s.form,s.target,s.revision,active),ranges=target_spectrum_ranges(p,self.target.target_id,stale),show_weight=star)
        self.paint_detector(p,active,stale)
        self.selection.set('Selected-bin ranges use the existing FFT; custom Impact is selected-bin onset, not instrument recognition. Inactive ranges show configuration without activity.')
        self.cadence.set('ACK received '+f'{max(0.,now-received)*1000:.0f}'+' ms ago; analyzer spectrum age '+(f'{max(0.,now_age(spectrum))*1000:.0f} ms' if spectrum else 'unavailable')+'.')
        if self.author_pending is not None and s.revision==self.author_pending[0] and p['authored']==self.author_pending[1]:
            self.profile_status.set('Save Authored acknowledged for '+EDIT_FORMS[self.form]+' / '+self.target.label);self.author_pending=None
        if self.profile_pending==s.revision:self.profile_pending=None;self.profile_status.set('Named profile acknowledged at this destination.')

    def paint_detector(self,p,active,stale):
        response=p.get('detector_response') if self.target.target_id==TARGET and p.get('pilot_active') else None
        impact=p.get('listening',{}).get('impact',{})
        if response:
            bars=(('Star level / floor',p.get('weighted_level',0.),response['level_floor']),('Star rise / floor',response['rise'],response['rise_floor']),('Star fraction / threshold',response['fraction'],response['fraction_floor']))
        elif impact.get('enabled') and impact.get('ready'):
            response=(impact.get('measurement') or {}).get('detector_response',{})
            bars=(('Custom-window onset rise / threshold',response.get('rise',0.),response.get('threshold',.2)),)
        else:bars=()
        self.detector_canvas.itemconfigure('all',state='hidden')
        if not bars:self.detector_canvas.pack_forget();return
        self.detector_canvas.configure(height=16*len(bars)+4);self.detector_canvas.pack(fill='x')
        for i,(label,value,threshold) in enumerate(bars):
            line,mark,text=self.detector_items[i];extent=max(.001,threshold*2.,value*1.1);y=8+i*16
            self.detector_canvas.coords(line,280,y,280+min(420,420*value/extent),y)
            self.detector_canvas.coords(mark,280+420*threshold/extent,y-5,280+420*threshold/extent,y+5)
            self.detector_canvas.coords(text,2,y);self.detector_canvas.itemconfigure(text,text=label+f' {value:.3f} / {threshold:.3f}')
            for item in (line,mark,text):self.detector_canvas.itemconfigure(item,state='normal' if active and not stale else 'hidden')

def now_age(spectrum):return time.perf_counter()-spectrum['observed_wall']
