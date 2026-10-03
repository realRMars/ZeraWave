"""Cymatics controls inside the existing Studio; colors use its existing inspector."""
import time,math
import tkinter as tk
from tkinter import ttk
from cymatics_session import defaults,validate
class CymaticsControls:
    def __init__(self,studio,parent):
        self.studio=studio;self.vars={};self.last_valid=defaults();self.revision=None;self.pending_time=0.;self.window_mute_seen=0
        pages=ttk.Notebook(parent);self.pages=pages;pages.pack(fill='both',expand=True)
        self.scrollers=[]
        def page(name):
            wrapper=ttk.Frame(pages);pages.add(wrapper,text=name)
            canvas=tk.Canvas(wrapper,highlightthickness=0,background='#141a28')
            scroll=ttk.Scrollbar(wrapper,orient='vertical',command=canvas.yview)
            canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
            frame=ttk.Frame(canvas,padding=10);window=canvas.create_window((0,0),window=frame,anchor='nw')
            frame.bind('<Configure>',lambda event:canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.bind('<Configure>',lambda event:canvas.itemconfigure(window,width=event.width))
            self.scrollers.append((canvas,frame));return frame
        drive=page('Drive');basin=page('Water basin');style=page('Style & bands')
        def field(frame,row,key,label,value,options=None):
            ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',pady=4)
            var=tk.BooleanVar(value=value) if type(value) is bool else tk.StringVar(value=str(value));self.vars[key]=var
            widget=ttk.Checkbutton(frame,variable=var) if type(value) is bool else ttk.Combobox(frame,textvariable=var,values=options,state='readonly') if options else ttk.Entry(frame,textvariable=var,width=24)
            widget.grid(row=row,column=1,sticky='ew',pady=4);frame.columnconfigure(1,weight=1)
        ttk.Label(drive,text='Experimental: choose Cymatics / Water, then Start preview.\nOscillator starts muted. Default basin frequencies are below hearing.').grid(row=0,column=0,columnspan=2,sticky='w',pady=6)
        c=defaults()
        field(drive,1,'source','Input (exclusive)',c['source'],('oscillator','track','loopback'))
        for row,(key,label) in enumerate((('frequency','Drive frequency (Hz)'),('amplitude','Canonical push amplitude (0–0.8)'),('waveform','Wave shape'),('phase','Phase offset (radians)'),('sweep_end','Sweep destination (Hz)'),('sweep_seconds','Sweep time (s; 0 = hold)'),('sweep_log','Logarithmic sweep')),2):field(drive,row,key,label,c['oscillator'][key],('sine','triangle','square','saw') if key=='waveform' else None)
        field(drive,9,'monitor','Listen to oscillator / track (starts muted)',False)
        field(drive,10,'monitor_gain','Separate monitor gain (0–0.05)',.02)
        ttk.Label(drive,text='Source changes need Stop → Start. Sound never changes\ncanonical amplitude. Saved sessions always reopen muted.').grid(row=11,column=0,columnspan=2,sticky='w',pady=5)
        held=ttk.Frame(drive);held.grid(row=12,column=0,columnspan=2,sticky='ew',pady=8)
        self.preset=tk.StringVar(value='Cross basin (2,2)')
        ttk.Combobox(held,textvariable=self.preset,values=('Long swell (1,0)','Cross basin (2,2)','Fine lattice (4,2)'),state='readonly',width=24).pack(side='left')
        ttk.Button(held,text='Hold resonance (muted)',command=self.hold_resonance).pack(side='left',padx=5)
        listening=ttk.Frame(drive);listening.grid(row=13,column=0,columnspan=2,sticky='ew',pady=5)
        ttk.Button(listening,text='Mute now',command=self.mute).pack(side='left')
        ttk.Button(listening,text='220 Hz audition preset (muted)',command=self.audible_preset).pack(side='left',padx=5)
        ttk.Label(drive,text='Basin resonances are below hearing. 220 Hz is audible but off-resonant.\nStart preview, check Listen, then Apply. M in preview or Stop mutes.\nTrack playback uses the same decoded mono PCM; loopback monitoring is blocked.',wraplength=550).grid(row=14,column=0,columnspan=2,sticky='ew',pady=5)
        ttk.Label(basin,text='Forced standing waves in a rectangular water basin.\nDamping means energy loss; this is not a full viscosity solver.').grid(row=0,column=0,columnspan=2,sticky='w',pady=6)
        fields=(('width','Width (cm)',10.),('length','Length (cm)',7.),('depth','Depth (mm)',5.),('modes','Resolved mode cap (1–36)',24),('damping','Damping / energy loss (1/s)',.35),('wall_loss','Boundary energy loss (1/s)',.25),('excitation','Pressure coupling strength',.025),('actuator_x','Exciter across (0–1)',.31),('actuator_y','Exciter along (0–1)',.43),('actuator_radius','Pressure patch radius (mm)',3.))
        for row,(key,label,v) in enumerate(fields,1):field(basin,row,key,label,v)
        ttk.Label(basin,text='Impermeable walls, sliding 90° contact-line approximation.\nDimensions/depth/mode changes reset the field after validation.\nNo hidden audio-to-water frequency compression.\nDrive above this limited mode range produces weak/off-resonant response.').grid(row=11,column=0,columnspan=2,sticky='w',pady=7)
        field(style,0,'material','Optical coating (not fluid properties)','glass',('glass','mercury','ink'))
        field(style,1,'optical_gain','Optical relief exaggeration',120.)
        field(style,2,'diagnostic','View','envelope',('envelope','height','nodes','normals'))
        ttk.Label(style,text='Envelope = approximate cycle amplitude with coherent interference.\nDisplay relief is softened/capped; physical amplitude is unchanged.\nHeight is instantaneous and can strobe above display cadence.\nNodes = envelope proxy, not a measured nodal map.\nPigments use the existing Palettes / live color inspector.').grid(row=3,column=0,columnspan=2,sticky='w',pady=4)
        field(style,4,'camera_orbit','Gentle camera orbit (off = stationary)',True)
        field(style,5,'dye','Sparse artistic dye tracers',True)
        field(style,6,'dye_strength','Tracer contrast (0-1)',.65)
        ttk.Button(style,text='Reset view (R)',command=self.reset_view).grid(row=7,column=1,sticky='w',pady=5)
        ttk.Button(style,text='Reset dye only',command=self.reset_dye).grid(row=7,column=0,sticky='w',pady=5)
        ttk.Label(style,text='Timed drops are artistic markers, not audio events or simulated dye flow.\nTheir magnified optical wobble uses modeled surface slopes;\nno net fluid transport is inferred. Reset leaves water/clock unchanged.',wraplength=550).grid(row=8,column=0,columnspan=2,sticky='ew')
        field(style,9,'finish','Basin finish','obsidian',('obsidian','marble'))
        field(style,10,'light_angle','Light placement angle (radians)',-.65)
        field(style,11,'dye_swirl','Artistic dye swirl (0-1)',.6)
        ttk.Label(style,text='Preview: left drag orbit; right/Shift drag pan; wheel zoom.\nDrag holds manual view; toggle automatic off/on to resume without snapping.\nR resets view. Swirl/spread is artistic, separate from driven wave motion.',wraplength=550).grid(row=12,column=0,columnspan=2,sticky='ew',pady=5)
        field(style,13,'edges','12-band edges Hz (13 comma-separated)',','.join(str(x) for x in c['bands']['edges']))
        field(style,14,'gain','New-band gain (legacy unaffected)',1.)
        field(style,15,'routing_band','Route band to pressure gain (-1 = off)',-1)
        field(style,16,'routing_strength','Pressure routing strength (0–1)',0.)
        self.band_notice=tk.StringVar(value='Default 3-6 Hz drive is below the 20 Hz band range and 23.44 Hz FFT spacing. These meters cannot resolve it; activity may be leakage, not detected pitch. Twelve bands are NOT twelve water modes.')
        ttk.Label(style,textvariable=self.band_notice,wraplength=550).grid(row=17,column=0,columnspan=2,sticky='ew',pady=8)
        self.meters=[];self.meter_labels=[]
        for i in range(12):
            label=ttk.Label(style,text=f'{i}: waiting');label.grid(row=18+i,column=0,sticky='w')
            meter=ttk.Progressbar(style,maximum=1.,length=180);meter.grid(row=18+i,column=1,sticky='ew')
            self.meters.append(meter);self.meter_labels.append(label)
        bar=ttk.Frame(parent);bar.pack(fill='x',pady=8)
        for i,(name,action) in enumerate((('Apply live',self.apply),('Pause / resume',self.pause),('Restart water',self.restart),('Copy raw band Hz',self.band_pitch),('Sweep resonances (muted)',self.resonance))):
            ttk.Button(bar,text=name,command=action).grid(row=i//3,column=i%3,sticky='ew',padx=2,pady=2)
        for i in range(3):bar.columnconfigure(i,weight=1)
        self.readback=tk.StringVar(value='Drive Hz and modeled surface resonances appear during preview.')
        ttk.Label(parent,textvariable=self.readback,wraplength=550).pack(fill='x')
        self.status=tk.StringVar(value='Ready, muted. Water is a Studio review candidate.')
        ttk.Label(parent,textvariable=self.status,wraplength=550).pack(fill='x')
        # Local scroll bindtags do not change any other Studio tab or dropdown popup.
        for canvas,frame in self.scrollers:
            tag='CymScroll'+str(id(canvas))
            def wheel(event,area=canvas):area.yview_scroll(-int(event.delta/120),'units');return 'break'
            parent.bind_class(tag,'<MouseWheel>',wheel)
            def attach(widget):
                widget.bindtags((str(widget),tag,*widget.bindtags()[1:]))
                for child in widget.winfo_children():attach(child)
            attach(frame)
        self.runtime=defaults();self.set(c)
    def set(self,data,stored=True):
        c=validate(data,stored=stored);self.runtime=c;self.last_valid=c
        for key,var in self.vars.items():
            if key in c:value=c[key]
            elif key in c['oscillator']:value=c['oscillator'][key]
            elif key in c['basin']:value=c['basin'][key]
            else:value=c['bands'][key]
            if key in ('width','length'):value*=100.
            if key in ('depth','actuator_radius'):value*=1000.
            if key=='edges':value=','.join(map(str,value))
            var.set(value)
    def settings(self,stored=False):
        c=defaults();c.update(paused=self.runtime['paused'],restart=self.runtime['restart'],dye_reset=self.runtime['dye_reset'],view_reset=self.runtime['view_reset'],camera=self.runtime['camera'])
        for key,var in self.vars.items():
            v=var.get()
            if key=='edges':v=[float(x) for x in v.split(',')]
            elif key in ('modes','routing_band'):v=int(v)
            elif key not in ('source','waveform','material','finish','diagnostic','monitor','sweep_log','camera_orbit','dye'):v=float(v)
            if key in ('width','length'):v/=100.
            if key in ('depth','actuator_radius'):v/=1000.
            if key in c:c[key]=v
            elif key in c['oscillator']:c['oscillator'][key]=v
            elif key in c['basin']:c['basin'][key]=v
            else:c['bands'][key]=v
        return validate(c,stored)
    def apply(self):
        try:
            c=self.settings()
            if not self.studio.color_link or self.studio.active_color_scene!='cymatics':self.status.set('Validated; applies on next Cymatics preview (muted).');return
            self.revision=self.studio.color_link.submit_scene(c);self.submitted=c;self.pending_time=time.monotonic();self.status.set('Pending renderer acknowledgement…')
        except (ValueError,TypeError) as exc:self.status.set('Last valid settings retained: '+str(exc))
    def pause(self):self.runtime['paused']=not self.runtime['paused'];self.apply()
    def restart(self):self.runtime['restart']+=1;self.apply()
    def reset_view(self):
        self.runtime['view_reset']+=1;self.runtime['camera']=defaults()['camera'];self.apply()
    def mute(self):self.vars['monitor'].set(False);self.apply()
    def audible_preset(self):
        self.vars['frequency'].set(220.);self.vars['sweep_end'].set(220.);self.vars['sweep_seconds'].set(0.);self.vars['amplitude'].set(.1);self.vars['monitor'].set(False);self.apply()
    def reset_dye(self):
        self.runtime['dye_reset']+=1;self.apply()
    def band_pitch(self):
        from cymatics import Basin
        try:
            c=self.settings();i=c['basin']['routing_band']
            if i<0:raise ValueError('Select a band index0-11 first')
            hz=math.sqrt(c['bands']['edges'][i]*c['bands']['edges'][i+1])
            if not .2<=hz<=8000:raise ValueError(f'Raw band center {hz:.2f}Hz is outside oscillator0.2-8000Hz; drive unchanged.')
            modes=Basin(c['basin']).report()['mode_hz']
            self.vars['frequency'].set(hz);self.vars['sweep_end'].set(hz);self.vars['sweep_seconds'].set(0.);self.vars['monitor'].set(False);self.apply()
            self.band_notice.set(f'Raw band center {hz:.2f}Hz copied without compression. Modeled basin {modes[0]:.2f}-{modes[-1]:.2f}Hz: off-resonant/weak response is expected above this range. Meters are not a pitch detector.')
        except ValueError as exc:self.status.set(str(exc))
    def hold_resonance(self):
        from cymatics import Basin
        targets={'Long swell (1,0)':(1,0),'Cross basin (2,2)':(2,2),'Fine lattice (4,2)':(4,2)}
        try:
            c=self.settings();basin=Basin(c['basin']);target=targets[self.preset.get()]
            match=next((i for i,mn in enumerate(basin.indices) if tuple(mn)==target),None)
            if match is None:raise ValueError('That mode is outside the selected mode cap/geometry. Increase cap or choose another preset.')
            if c['source']!='oscillator':raise ValueError('Choose oscillator Input and Stop/Start before holding a resonance.')
            hz=basin.report()['mode_hz'][match]
            self.vars['frequency'].set(hz);self.vars['sweep_end'].set(hz);self.vars['sweep_seconds'].set(0.);self.vars['monitor'].set(False)
            self.runtime['restart']+=1;self.apply()
        except (ValueError,KeyError) as exc:self.status.set(str(exc))
    def resonance(self):
        from cymatics import Basin
        try:
            c=self.settings();hz=Basin(c['basin']).report()['mode_hz']
            self.vars['frequency'].set(round(hz[min(8,len(hz)-1)],4))
            self.vars['sweep_end'].set(round(hz[min(18,len(hz)-1)],4))
            self.vars['sweep_seconds'].set(24.)
            self.vars['monitor'].set(False);self.apply()
        except ValueError as exc:self.status.set(str(exc))
    def refresh(self):
        if not self.studio.color_link:return
        s=self.studio.color_link.get_status()
        if self.revision is not None:
            if s.get('scene_rejected')==self.revision:self.set(self.last_valid,stored=False);self.status.set('Rejected; restored last applied settings: '+str(s.get('scene_error')));self.revision=None
            elif s.get('scene_applied')==self.revision:self.last_valid=self.submitted;self.status.set('Applied'+(' — field reset.' if s.get('scene_reset') else ' — state preserved.'));self.revision=None
            elif time.monotonic()-self.pending_time>3:self.status.set('Acknowledgement unknown; inspect preview/log or Apply again. Not marked applied.')
        data=s.get('cymatics_status')
        if data:
            if data.get('camera') is not None:self.runtime['camera']=data['camera']
            if data.get('window_mute_serial',0)>self.window_mute_seen:
                self.window_mute_seen=data['window_mute_serial'];self.vars['monitor'].set(False);self.last_valid['monitor']=False;self.status.set('Muted from preview (M).')
            modes=data['basin']['mode_hz'];osc=data.get('oscillator')
            self.readback.set(('Drive %.3f Hz | ' % osc['frequency'] if osc else 'PCM input | ')+f'Modeled surface: {modes[0]:.3f}-{modes[-1]:.3f} Hz ({len(modes)} resolved modes). Clock {data["seconds"]:.2f}s. Monitor '+('enabled' if data['monitor_enabled'] else 'muted'))
            bands=data.get('bands')
            if bands:
                low=bands['edges'][0];spacing=bands['resolution_hz']
                if osc and (osc['frequency']<low or osc['frequency']<spacing):
                    self.band_notice.set(f"Exact drive {osc['frequency']:.3f} Hz is unresolved here (FFT spacing {spacing:.2f} Hz; bands start {low:g} Hz). Apparent meter energy may be leakage, not detected pitch. Twelve bands are not water modes.")
                elif osc and osc['frequency']>modes[-1]:
                    self.band_notice.set(f"Raw drive {osc['frequency']:.2f}Hz exceeds basin{modes[0]:.2f}-{modes[-1]:.2f}Hz: off-resonant/weak response expected. No compression. Broad FFT magnitudes are not detected pitch.")
                elif not osc:
                    self.band_notice.set(f'PCM input: FFT spacing {spacing:.2f} Hz. Broad band magnitudes can leak; low-frequency water drive is not resolved here. Twelve bands are not water modes or detected pitch.')
                for i,(label,meter) in enumerate(zip(self.meter_labels,self.meters)):
                    label.configure(text=f"{i}: {bands['edges'][i]:g}–{bands['edges'][i+1]:g}Hz"+(' [unresolved]' if bands['unresolved'][i] else ''))
                    meter['value']=bands['levels'][i]
            if data.get('monitor_error'):self.status.set('Monitor unavailable; source remains muted: '+data['monitor_error'])
