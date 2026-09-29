"""Declaration-driven modeless Studio color inspector, using only standard Tk."""
import colorsys
from copy import deepcopy
import json
import math
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from color_controls import (targets_for, resolved_slots, rgb_hex, hex_rgb,
                            validate_colors, color_preset, validate_preset, scene_colors, PALETTE_FAMILIES, family_setup)


class ColorInspector:
    def __init__(self, app, scene):
        self.app,self.scene=app,scene
        self.window=tk.Toplevel(app.root)
        self.window.title('ZeraWave — Live color inspector')
        self.window.geometry('720x740');self.window.minsize(670,700)
        self.window.configure(background='#141a28')
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.targets=targets_for(scene)
        self.target_choice=tk.StringVar(value=self.targets[0].label)
        self.role=tk.StringVar()
        self.note=tk.StringVar()
        self.value=tk.DoubleVar(value=1.)
        self.hue,self.saturation=0.,1.
        self.refreshing=False
        style=ttk.Style(self.window)
        style.map('Color.TRadiobutton', background=[('active','#233047')], foreground=[('active','#ffffff')])
        shell=ttk.Frame(self.window);shell.pack(fill='both',expand=True)
        self.viewport=tk.Canvas(shell,borderwidth=0,highlightthickness=0,background='#141a28')
        scrollbar=ttk.Scrollbar(shell,orient='vertical',command=self.viewport.yview)
        self.viewport.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');self.viewport.pack(side='left',fill='both',expand=True)
        body=ttk.Frame(self.viewport,padding=16)
        body_window=self.viewport.create_window((0,0),anchor='nw',window=body)
        body.bind('<Configure>',lambda event:self.viewport.configure(scrollregion=self.viewport.bbox('all')))
        self.viewport.bind('<Configure>',lambda event:self.viewport.itemconfigure(body_window,width=event.width))
        ttk.Label(body,text='Live scene colors',font=('Segoe UI',16)).pack(anchor='w')
        self.target_box=ttk.Combobox(body,textvariable=self.target_choice,
            values=[target.label for target in self.targets],state='readonly')
        self.target_box.pack(fill='x',pady=8)
        self.target_box.bind('<<ComboboxSelected>>',lambda event:self.refresh())
        ttk.Label(body,textvariable=self.note,wraplength=630).pack(anchor='w')
        palettes=ttk.LabelFrame(body,text='Palette timing — selected target only',padding=8)
        palettes.pack(fill='x',pady=8)
        self.family_choice=tk.StringVar(value='Authored')
        self.family_box=ttk.Combobox(palettes,textvariable=self.family_choice,state='readonly',width=24)
        self.family_box.grid(row=0,column=0,sticky='w')
        ttk.Button(palettes,text='Hold family',command=self.hold_family).grid(row=0,column=1)
        ttk.Button(palettes,text='Store current setup',command=self.store_setup).grid(row=0,column=2)
        self.cycle_mode=tk.StringVar(value='hold');self.cycle_hold=tk.StringVar(value='12');self.cycle_fade=tk.StringVar(value='4')
        ttk.Combobox(palettes,textvariable=self.cycle_mode,values=('hold','cycle'),state='readonly',width=8).grid(row=1,column=0,sticky='w')
        timing=ttk.Frame(palettes);timing.grid(row=1,column=1,columnspan=2,sticky='w',pady=6)
        ttk.Label(timing,text='Hold seconds').pack(side='left')
        ttk.Spinbox(timing,textvariable=self.cycle_hold,from_=1,to=300,width=5).pack(side='left')
        ttk.Label(timing,text='Transition').pack(side='left')
        ttk.Spinbox(timing,textvariable=self.cycle_fade,from_=0,to=60,width=5).pack(side='left')
        ttk.Button(timing,text='Apply timing',command=self.apply_cycle).pack(side='left')
        self.cycle_note=tk.StringVar()
        ttk.Label(palettes,textvariable=self.cycle_note,wraplength=610).grid(row=2,column=0,columnspan=3,sticky='w')
        self.fields=ttk.Frame(body);self.fields.pack(fill='x',pady=10)
        self.rows={}
        wheel_frame=ttk.Frame(body);wheel_frame.pack(fill='x')
        self.wheel=tk.Canvas(wheel_frame,width=190,height=190,background='#233047',highlightthickness=0)
        self.wheel.pack(side='left')
        self.wheel_image=tk.PhotoImage(width=190,height=190)
        rows=[]
        for y in range(190):
            row=[]
            for x in range(190):
                dx,dy=(x-95)/91.,(95-y)/91.
                radius=math.hypot(dx,dy)
                row.append(rgb_hex(colorsys.hsv_to_rgb((math.atan2(dy,dx)/(2*math.pi))%1.,radius,1.))
                           if radius<=1. else '#233047')
            rows.append('{'+ ' '.join(row) +'}')
        self.wheel_image.put(' '.join(rows))
        self.wheel.create_image(0,0,anchor='nw',image=self.wheel_image)
        self.marker=self.wheel.create_oval(90,90,100,100,outline='white',width=2)
        self.wheel.bind('<Button-1>',self.wheel_pick)
        self.wheel.bind('<B1-Motion>',self.wheel_pick)
        tools=ttk.Frame(wheel_frame,padding=(14,0));tools.pack(side='left',fill='both',expand=True)
        self.selected_label=tk.StringVar()
        ttk.Label(tools,textvariable=self.selected_label,wraplength=380).pack(anchor='w')
        ttk.Label(tools,text='Hue around the wheel; saturation outward.').pack(anchor='w',pady=(8,0))
        ttk.Label(tools,text='Brightness / value').pack(anchor='w',pady=(8,0))
        self.value_scale=ttk.Scale(tools,from_=0.,to=1.,variable=self.value,command=self.value_pick)
        self.value_scale.pack(fill='x',pady=4)
        self.value_label=tk.StringVar()
        ttk.Label(tools,textvariable=self.value_label).pack(anchor='w')
        ttk.Label(tools,text='Chosen source color or tint before shading and audio response.\nSwatches are not final screen brightness.\nShared material colors follow compatible scenes; world colors stay with their named form.',wraplength=360).pack(anchor='w',pady=8)
        actions=ttk.Frame(body);actions.pack(fill='x',pady=(12,4))
        self.buttons=[]
        for label,callback in (('Reset target to Authored',self.reset_target),('Reset scene to Authored',self.reset_scene),('Revert to preview start',self.revert)):
            button=ttk.Button(actions,text=label,command=callback);button.pack(side='left',padx=(0,5));self.buttons.append(button)
        presets=ttk.Frame(body);presets.pack(fill='x',pady=4)
        for label,callback in (('Save named color preset…',self.save_preset),('Load color preset…',self.load_preset)):
            button=ttk.Button(presets,text=label,command=callback);button.pack(side='left',padx=(0,8));self.buttons.append(button)
        ttk.Label(body,text='A color preset remembers scene-part assignments; a palette only holds colors.',wraplength=630).pack(anchor='w',pady=4)
        ttk.Label(body,textvariable=app.color_status,wraplength=630).pack(anchor='w',pady=8)
        self.refresh()

    def target(self):
        return next(target for target in self.targets if target.label==self.target_choice.get())

    def supported(self):
        return self.app.color_scene() == self.scene

    def can_revert(self):
        return self.app.active_color_scene in (self.scene,'blend')

    def refresh(self):
        if not self.window.winfo_exists(): return
        self.refreshing=True
        target=self.target()
        supported=self.supported()
        self.target_box.configure(state='readonly' if supported else 'disabled')
        if not supported:
            status='Editing disabled for this selection. Choose a compatible form or family cycle; saved overrides remain parked.'
        elif self.app.active_color_scene is None:
            status='Parked until a preview starts.'
        elif self.app.active_color_scene=='blend':
            status='Running Main or a sequence: active when this source appears; parked during other sources.'
        elif self.app.active_color_scene!=self.scene:
            status=('Active in the running preview when its detail is enabled.'
                    if target in targets_for(self.app.active_color_scene) else
                    'Parked for the next compatible preview.')
        elif self.scene in ('organic','water','fire_cycle','air','earth','fog','plasma'):
            status='Family cycle: active when this source appears; parked during other forms.'
        else:
            status='Active in this preview when its detail is enabled.'
        scope=('Shared material or FX' if target.scene=='shared' else
               'Shared within this family' if target.scene.endswith('_shared') else
               'Owned by '+target.scene.replace('_',' '))
        self.note.set(status+' '+scope+'. '+target.note if supported else status)
        families=('Authored',)+tuple(PALETTE_FAMILIES.get(target.id,{}))
        self.family_box.configure(values=families)
        if self.family_choice.get() not in families:self.family_choice.set('Authored')
        cycle=self.app.color_overrides.get(target.id,{}).get('_cycle',{})
        self.cycle_mode.set(cycle.get('mode','hold'));self.cycle_hold.set(str(cycle.get('hold',12)))
        self.cycle_fade.set(str(cycle.get('fade',4)))
        self.cycle_note.set(f"{target.label}: {cycle.get('mode','hold')}; {len(cycle.get('setups',[]))}/4 stored setups. Store at least two to cycle. Timing follows song time. Manual edits pause this target; reset clears its cycle.")
        for child in self.fields.winfo_children(): child.destroy()
        self.rows={}
        labels=('Select color role','Swatch','Hex color','Blend starts','Full color at')
        for col,label in enumerate(labels): ttk.Label(self.fields,text=label).grid(row=0,column=col,sticky='w',padx=4)
        for index,(slot,resolved) in enumerate(zip(target.slots,resolved_slots(target,self.app.color_overrides))):
            rgb,start,end=resolved
            radio=ttk.Radiobutton(self.fields,style='Color.TRadiobutton',text=slot.label,variable=self.role,value=slot.id,command=self.select_role)
            radio.grid(row=index+1,column=0,sticky='w',pady=4)
            swatch=tk.Label(self.fields,width=4,background=rgb_hex(rgb));swatch.grid(row=index+1,column=1,padx=4)
            swatch.bind('<Button-1>',lambda event,key=slot.id:self.choose_role(key))
            color=tk.StringVar(value=rgb_hex(rgb));entry=ttk.Entry(self.fields,textvariable=color,width=10)
            entry.grid(row=index+1,column=2,padx=4)
            for event in ('<Return>','<FocusOut>'): entry.bind(event,lambda event,key=slot.id:self.edit_hex(key))
            start_var,end_var=tk.StringVar(value='' if start is None else f'{start:g}'),tk.StringVar(value='' if end is None else f'{end:g}')
            widgets=[radio,entry]
            for col,var in ((3,start_var),(4,end_var)):
                if start is None:
                    ttk.Label(self.fields,text=('fixed base' if target.kind=='staged_gradient' else 'not applicable') if col==3 else '—').grid(row=index+1,column=col,padx=4)
                else:
                    position=ttk.Entry(self.fields,textvariable=var,width=8);position.grid(row=index+1,column=col,padx=4)
                    for event in ('<Return>','<FocusOut>'): position.bind(event,lambda event,key=slot.id:self.edit_range(key))
                    widgets.append(position)
            for widget in widgets: widget.configure(state='normal' if supported else 'disabled')
            self.rows[slot.id]=(color,start_var,end_var,swatch)
        if self.role.get() not in self.rows: self.role.set(target.slots[min(2,len(target.slots)-1)].id)
        for button in self.buttons: button.configure(state='normal' if supported else 'disabled')
        self.buttons[2].configure(state='normal' if supported and self.can_revert() else 'disabled')
        self.value_scale.configure(state='normal' if supported else 'disabled')
        self.refreshing=False
        self.select_role()

    def choose_role(self,key):
        self.role.set(key);self.select_role()

    def select_role(self):
        target=self.target(); index=next(i for i,slot in enumerate(target.slots) if slot.id==self.role.get())
        rgb=resolved_slots(target,self.app.color_overrides)[index][0]
        hue,saturation,value=colorsys.rgb_to_hsv(*rgb)
        if value>0: self.hue,self.saturation=hue,saturation
        self.refreshing=True;self.value.set(value);self.refreshing=False
        self.selected_label.set(target.label+' / '+target.slots[index].label)
        self.draw_marker()

    def draw_marker(self):
        x=95+91*self.saturation*math.cos(self.hue*2*math.pi)
        y=95-91*self.saturation*math.sin(self.hue*2*math.pi)
        self.wheel.coords(self.marker,x-4,y-4,x+4,y+4)
        self.value_label.set(f'{self.value.get()*100:.0f}% value')

    def commit(self,key,fields):
        if self.refreshing or not self.supported(): return False
        data=deepcopy(self.app.color_overrides)
        selected=data.setdefault(self.target().id,{})
        if '_cycle' in selected:selected['_cycle']['mode']='hold'
        selected.setdefault(key,{}).update(fields)
        try: self.app.set_color_setup(validate_colors(data))
        except ValueError as exc:
            self.app.color_status.set('Invalid edit; last valid colors retained. '+str(exc));return False
        self.cycle_mode.set('hold');self.cycle_note.set(self.target().label+': hold — manual edit has priority. Stored setups remain available.')
        self.rows[key][3].configure(background=rgb_hex(resolved_slots(self.target(),data)[next(i for i,s in enumerate(self.target().slots) if s.id==key)][0]))
        return True

    def edit_hex(self,key):
        if self.refreshing or key not in self.rows: return
        text=self.rows[key][0].get().strip().upper()
        target=self.target();index=next(i for i,s in enumerate(target.slots) if s.id==key)
        if text==rgb_hex(resolved_slots(target,self.app.color_overrides)[index][0]): return
        if self.commit(key,dict(color=text)):
            self.rows[key][0].set(text)
            if key==self.role.get():self.select_role()

    def edit_range(self,key):
        if self.refreshing or key not in self.rows: return
        try: start,end=(float(var.get()) for var in self.rows[key][1:3])
        except ValueError:
            self.app.color_status.set('Invalid gradient position; last valid colors retained.');return
        target=self.target();index=next(i for i,s in enumerate(target.slots) if s.id==key)
        if (start,end)==resolved_slots(target,self.app.color_overrides)[index][1:]:return
        self.commit(key,dict(start=start,end=end))

    def wheel_pick(self,event):
        if not self.supported():return
        dx,dy=event.x-95,95-event.y
        self.hue=(math.atan2(dy,dx)/(2*math.pi))%1.
        self.saturation=min(1.,math.hypot(dx,dy)/91.)
        self.apply_wheel()

    def value_pick(self,value):
        if not self.refreshing and self.supported():self.apply_wheel()

    def apply_wheel(self):
        color=rgb_hex(colorsys.hsv_to_rgb(self.hue,self.saturation,self.value.get()))
        if self.commit(self.role.get(),dict(color=color)):
            self.rows[self.role.get()][0].set(color)
            self.draw_marker()

    def hold_family(self):
        if not self.supported():return
        data=deepcopy(self.app.color_overrides);key=self.target().id
        cycle=data.get(key,{}).get('_cycle')
        data[key]=family_setup(key,self.family_choice.get())
        if cycle:
            cycle['mode']='hold';data[key]['_cycle']=cycle
        self.app.set_color_setup(data);self.refresh()

    def store_setup(self):
        if not self.supported():return
        data=deepcopy(self.app.color_overrides);entry=data.setdefault(self.target().id,{})
        cycle=entry.setdefault('_cycle',dict(mode='hold',hold=12.,fade=4.,setups=[]))
        if len(cycle['setups'])>=4:
            self.app.color_status.set('Four setups already stored. Reset target to clear them.');return
        cycle['setups'].append(deepcopy({key:value for key,value in entry.items() if key!='_cycle'}))
        cycle['mode']='hold'
        try:self.app.set_color_setup(data);self.refresh()
        except ValueError as exc:self.app.color_status.set(str(exc))

    def apply_cycle(self):
        if not self.supported():return
        data=deepcopy(self.app.color_overrides);entry=data.setdefault(self.target().id,{})
        cycle=entry.setdefault('_cycle',dict(setups=[]))
        try:
            cycle.update(mode=self.cycle_mode.get(),hold=float(self.cycle_hold.get()),fade=float(self.cycle_fade.get()))
            self.app.set_color_setup(data);self.refresh()
        except ValueError as exc:self.app.color_status.set('Timing not applied: '+str(exc))

    def reset_target(self):
        data=deepcopy(self.app.color_overrides);data.pop(self.target().id,None)
        self.app.set_color_setup(data);self.refresh()

    def reset_scene(self):
        data={key:value for key,value in self.app.color_overrides.items() if key not in {target.id for target in self.targets}}
        self.app.set_color_setup(data);self.refresh()

    def revert(self):
        if self.can_revert():
            data={key:value for key,value in self.app.color_overrides.items() if key not in {target.id for target in self.targets}}
            data.update(scene_colors(self.app.preview_start_colors,self.scene))
            self.app.set_color_setup(data);self.refresh()

    def save_preset(self):
        name=simpledialog.askstring('Save color preset','Name this scene color setup:',parent=self.window)
        if name is None:return
        try:
            data=color_preset(name,self.scene,self.app.color_overrides)
            folder=self.app.color_preset_folder();folder.mkdir(parents=True,exist_ok=True)
            path=filedialog.asksaveasfilename(parent=self.window,initialdir=folder,
                initialfile=re.sub(r'[^\w -]','_',name)+'.json',defaultextension='.json',filetypes=[('Color preset','*.json')])
            if path:
                from pathlib import Path
                Path(path).write_text(json.dumps(data,indent=2),encoding='utf-8')
                self.app.color_status.set('Saved color preset '+data['name']+'. Other saved setups are unchanged.')
        except (OSError,ValueError) as exc:messagebox.showerror('Cannot save preset',str(exc),parent=self.window)

    def load_preset(self):
        path=filedialog.askopenfilename(parent=self.window,initialdir=self.app.color_preset_folder(),filetypes=[('Color preset','*.json')])
        if not path:return
        try:
            from pathlib import Path
            source=Path(path)
            if source.stat().st_size>131072:raise ValueError('Color preset is too large.')
            preset=validate_preset(json.loads(source.read_text(encoding='utf-8')))
            if preset['scene']!=self.scene and self.scene!='blend':
                raise ValueError('This preset belongs to another scene.')
            replaced=({target.id for target in self.targets} if preset['scene']==self.scene
                      else set(preset['targets']))
            data={key:value for key,value in self.app.color_overrides.items() if key not in replaced}
            data.update(preset['targets']);self.app.set_color_setup(data);self.refresh()
        except (OSError,ValueError) as exc:messagebox.showerror('Cannot load preset',str(exc),parent=self.window)

    def close(self):
        self.app.color_editor=None;self.window.destroy()
