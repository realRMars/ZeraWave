"""Bounded, read-only Planet telemetry from existing frames and CPU submissions.

No FFT, capture, audio queues, GPU reads or session writes. The packet names
submitted uniforms, never inferred pixels. Tk is imported only for the view.
"""
from copy import deepcopy
import hashlib
import json
import math
import time
import uuid

PREFIX = 'ZERAWAVE_PLANET_MONITOR '
MAX_PACKET = 16384
CADENCE = .20
STALE_SECONDS = 1.


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def meter(value, low=0., high=1.):
    """Display clamp only; telemetry retains the exact finite raw number."""
    return None if not number(value) else max(0., min(1., (value-low)/(high-low)))


def configure(renderer, mode, source):
    from planet_canvas_dsp import held_planet
    if not held_planet(True, renderer.debug_state, renderer.debug_sequence,
                       renderer.transition_sequence, renderer.transition_settings): return
    renderer.planet_monitor = PlanetMonitor(mode, source,
        dict(layers=renderer.layer_profiles, palette=renderer.preview_palette,
             surface_pilot=renderer.planet_dsp_pilot,
             star_pilot=renderer.planet_star_attack_pilot,
             initial_colors=renderer.color_overrides,
             state=renderer.debug_state, seed=renderer.cosmos_seed))


class PlanetMonitor:
    def __init__(self, mode, source, config, clock=time.perf_counter):
        if mode not in ('LIVE', 'REPLAY'): raise ValueError('Unknown monitor mode')
        self.mode, self.source, self.clock = mode, str(source)[:512], clock
        self.run = uuid.uuid4().hex
        self.config = hashlib.sha256(json.dumps(config, sort_keys=True,
                            separators=(',', ':')).encode()).hexdigest()
        self.enabled = False
        self.sequence = 0
        self.samples = 0
        self.audio = None
        self.audio_at = None
        self.peak = 0.
        self.peak_frame = None
        self.last_publish = -float('inf')

    def enable(self, enabled):
        if type(enabled) is not bool: raise ValueError('Monitor toggle must be boolean')
        if self.enabled != enabled:
            self.enabled = enabled
            self.audio = None
            self.audio_at = None
            self.peak = 0.
            self.peak_frame = None
            self.last_publish = -float('inf')

    def observe(self, frame, count, stamp=None):
        self.sequence += 1
        self.samples += count
        if not self.enabled: return
        # Copy only bounded scalar summaries: never spectrum bins or PCM.
        legacy = {k:float(getattr(frame, k)) for k in
                  ('bass', 'mids', 'highs', 'flux', 'bass_onset', 'mids_onset',
                   'highs_onset', 'tempo', 'beat_confidence')}
        bands = getattr(frame, 'band12', None)
        bands = ({k:list(bands[k])[:13] for k in ('edges', 'levels', 'unresolved')}
                 if isinstance(bands, dict) else None)
        descriptors = getattr(frame, 'descriptors', None)
        descriptors = ({k:descriptors.get(k) for k in
                        ('version', 'valid', 'analyzed_seconds', 'signal_confidence',
                         'spectral_spread', 'fullness')} if isinstance(descriptors, dict) else None)
        attack = getattr(frame, 'planet_star_audio', None)
        attack = ({k:attack.get(k) for k in ('sample_seconds', 'bass_attack', 'low_band_level')}
                  if isinstance(attack, dict) else None)
        measured=(attack or {}).get('sample_seconds', (descriptors or {}).get('analyzed_seconds'))
        self.audio = dict(legacy=legacy, bands=bands, descriptors=descriptors, attack=attack,
                          frame=self.sequence, sample_seconds=measured if number(measured) else self.samples/48000.,
                          sample_clock='analyzed PCM' if number(measured) else 'delivered PCM (queue drops excluded)',
                          capture_stamp=stamp)
        strength = (attack or {}).get('bass_attack')
        if number(strength) and strength > self.peak:
            self.peak, self.peak_frame = strength, self.sequence
        self.audio_at = stamp if number(stamp) else self.clock()

    def packet(self, seconds, submitted, controls):
        now = self.clock()
        if not self.enabled or now-self.last_publish < CADENCE: return None
        packet = dict(version=1, run=self.run, mode=self.mode, source=self.source,
                      config=self.config, render_seconds=seconds,
                      audio_age_seconds=None if self.audio_at is None else max(0., now-self.audio_at),
                      audio=deepcopy(self.audio), submitted=deepcopy(submitted),
                      controls=deepcopy(controls), interval_attack_peak=self.peak,
                      peak_frame=self.peak_frame)
        text = json.dumps(packet, separators=(',', ':'), allow_nan=False)
        if len(text.encode()) > MAX_PACKET: raise ValueError('Monitor packet too large')
        self.last_publish = now
        self.peak, self.peak_frame = 0., None
        return text


def decode(text):
    if len(text.encode()) > MAX_PACKET: return None
    try: p = json.loads(text)
    except (ValueError, TypeError): return None
    if (not isinstance(p, dict) or p.get('version') != 1 or
            p.get('mode') not in ('LIVE', 'REPLAY') or
            not all(isinstance(p.get(k), str) and len(p[k]) <= 512 for k in ('run', 'source', 'config')) or
            not isinstance(p.get('submitted'), dict) or not isinstance(p.get('controls'), dict)):
        return None
    def finite_tree(value):
        if value is None or isinstance(value, (str, bool)):return True
        if type(value) in (int, float):return number(value)
        if isinstance(value, dict):return all(finite_tree(v) for v in value.values())
        if isinstance(value, list):return all(finite_tree(v) for v in value)
        return False
    if not finite_tree(p):return None
    s=p['submitted'];c=p['controls']
    for key,size in (('u_planet_star_flight',3),('u_spatial_treatments',3),('u_material_mix',3),('u_new_materials',3)):
        if not isinstance(s.get(key),list) or len(s[key])!=size or not all(number(v) for v in s[key]):return None
    if not isinstance(c.get('spatial_base'),list) or len(c['spatial_base'])!=3:return None
    a = p.get('audio')
    if a is not None and (not isinstance(a, dict) or type(a.get('frame')) is not int
                           or a['frame'] < 1 or not number(a.get('sample_seconds'))): return None
    if a is not None:
        if not isinstance(a.get('legacy'),dict):return None
        b=a.get('bands')
        if b is not None and (not isinstance(b,dict) or len(b.get('edges',[]))!=13
                or len(b.get('levels',[]))!=12 or len(b.get('unresolved',[]))!=12):return None
    return p


def rows(packet):
    """Named source -> actual submission routes; unknown values stay unavailable."""
    a = packet.get('audio') or {}; s = packet['submitted']; c = packet['controls']
    legacy = a.get('legacy') or {}; d = a.get('descriptors') or {}; attack = a.get('attack') or {}
    result = []
    def add(label, driver, value, low=0., high=1.):
        result.append((label, driver, value, meter(value, low, high)))
    for key in ('bass', 'mids', 'highs', 'flux'):
        add('Input '+key, 'Existing conditioned analysis', legacy.get(key))
    add('Attack interval peak', '20–250 Hz rise proxy; frame '+str(packet.get('peak_frame')),
        packet.get('interval_attack_peak') if attack else None)
    descriptor_ready=d.get('valid') is True
    descriptor_status='Measured descriptor' if descriptor_ready else ('Unavailable: descriptor not valid' if d else 'Unavailable: pilot off')
    add('Spectral spread', descriptor_status, d.get('spectral_spread') if descriptor_ready else None)
    add('Fullness', descriptor_status, d.get('fullness') if descriptor_ready else None)
    add('Signal confidence', 'Descriptor valid='+str(d.get('valid')) if d else 'Unavailable: pilot off',d.get('signal_confidence'))
    for label, key, driver in (
        ('Scale', 'u_scale', 'Legacy bass → mapper'),
        ('Sparkle', 'u_sparkle', 'Legacy highs → mapper'),
        ('Impact envelope', 'u_impact', 'Legacy onsets → shared release'),
        ('Flux', 'u_flux', 'Legacy conditioned spectral flux')):
        add(label, driver, s.get(key))
    flight = s.get('u_planet_star_flight', (0., 0., 0.))
    add('Background star rate', 'Low-band rise pilot' if flight[0] else 'Legacy flux/highs chorus',
        s.get('background_star_rate'), 1., 1.75)
    add('Background wake envelope', 'Attack flight' if flight[0] else 'Legacy shader chorus',
        flight[2] if flight[0] else None)
    add('Shooting star enable', 'Manual/list/time cycle; births use shared star clock', s.get('u_shooting_stars'))
    for i, label in enumerate(('Elastic', 'Braided', 'Nested')):
        base = c.get('spatial_base', (None,)*3)[i]
        pilot = c.get('surface_pilot') and i < 2
        add(label+' amount', ('Spread' if i == 0 else 'Fullness')+' ratio × base '+str(base)
            if pilot else 'Manual/time cycle base '+str(base), s.get('u_spatial_treatments', (None,)*3)[i])
    for i, label in enumerate(('Living artifacts', 'Liquid alloy', 'Prismatic lattice')):
        add(label+' mix', 'Manual/time cycle; shading uses legacy audio', s.get('u_material_mix', (None,)*3)[i])
    add('Echo weave weight', 'Manual/time cycle; evolving history', s.get('u_echo_weave'))
    for i, label in enumerate(('Ink Archipelago', 'Interference Silk', 'Cellular Mosaic')):
        add(label+' weight', 'Manual/time cycle', s.get('u_new_materials', (None,)*3)[i])
    for i,label in enumerate(('Prism Assembly','Digital Bloom','Chromatic Memory')):
        add(label+' weight','Manual/time cycle; '+('fallback untreated' if s.get('enveloper_failed') else 'shared postprocess'),
            s.get('envelopers',(None,)*3)[i])
    return result


class MonitorWindow:
    """Optional read-only window, refreshed by Studio's existing 200ms poll."""
    def __init__(self, parent, toggle, normal=False):
        import tkinter as tk
        from tkinter import ttk
        self.window = tk.Toplevel(parent)
        self.normal=normal
        self.window.title('Mapping monitor' if normal else 'Planet Canvas mapping monitor')
        self.window.geometry('940x790')
        self.toggle = toggle
        self.enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.window, text='Live monitoring (read only)', variable=self.enabled,
                        command=lambda:toggle(self.enabled.get())).pack(anchor='w', padx=12, pady=8)
        self.status = tk.StringVar(value='Waiting for held Planet Canvas live/replay preview.')
        self.identity = tk.StringVar()
        ttk.Label(self.window, textvariable=self.status).pack(anchor='w', padx=12)
        ttk.Label(self.window, textvariable=self.identity, wraplength=900).pack(anchor='w', padx=12)
        ttk.Label(self.window, text='Frequency energy from existing FFT bands — not pitch/key. '
                  'Meters show submitted uniforms, not measured pixels.').pack(anchor='w', padx=12, pady=6)
        ttk.Label(self.window,text='Material weights show selection/blending. Fixed or zero weights do not measure animation.').pack(anchor='w',padx=12)
        self.bands = ttk.Frame(self.window); self.bands.pack(fill='x', padx=12)
        self.band_labels = []; self.band_bars = []
        for i in range(12):
            label=ttk.Label(self.bands, text='—', width=9); label.grid(row=0,column=i)
            bar=ttk.Progressbar(self.bands,maximum=1.,length=60); bar.grid(row=1,column=i,padx=2)
            self.band_labels.append(label); self.band_bars.append(bar)
        shell=ttk.Frame(self.window);shell.pack(fill='both',expand=True,padx=12,pady=8)
        self.table=ttk.Treeview(shell, columns=('driver','value'), show='tree headings', height=26)
        scroll=ttk.Scrollbar(shell,orient='vertical',command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y')
        self.table.heading('#0',text='Target / source'); self.table.column('#0',width=215)
        self.table.heading('driver',text='Driver / scope'); self.table.column('driver',width=530)
        self.table.heading('value',text='Value / meter'); self.table.column('value',width=145)
        self.table.pack(fill='both',expand=True)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.received_run = None

    def close(self):
        self.toggle(False)
        self.window.destroy()

    def alive(self):
        return bool(self.window.winfo_exists())

    def refresh(self, latest, running):
        if getattr(self,'normal',False):return self.refresh_normal(latest,running)
        if not self.enabled.get(): self.status.set('PAUSED — retained values; mappings unchanged.'); return
        if not running or latest is None:
            self.status.set('Stopped / unavailable — start a held Planet Canvas live/replay preview.'); return
        packet,received=latest
        a=packet.get('audio') or {}; age=packet.get('audio_age_seconds')
        stale=time.perf_counter()-received>STALE_SECONDS or age is None or age>STALE_SECONDS
        self.status.set(packet['mode']+' — '+('STALE / no current input' if stale else 'current input')+
                        ' — surface pilot '+str(packet['controls'].get('surface_pilot'))+
                        ' — star pilot '+str(packet['controls'].get('star_pilot')))
        self.identity.set('Source: '+packet['source']+' | run '+packet['run'][:12]+
                          ' | config '+packet['config'][:12]+' | input frame '+str(a.get('frame'))+
                          ' | '+str(a.get('sample_clock'))+' '+str(a.get('sample_seconds'))+'s | render '+str(packet.get('render_seconds'))+'s')
        bands=a.get('bands') or {}
        for i,(label,bar) in enumerate(zip(self.band_labels,self.band_bars)):
            if len(bands.get('edges',[])) == 13 and len(bands.get('levels',[])) == 12:
                low,high=bands['edges'][i:i+2]
                unresolved=bands.get('unresolved',[True]*12)[i]
                label.configure(text=f'{low:g}–{high:g}'+(' *' if unresolved else ''))
                bar['value']=meter(bands['levels'][i]) or 0.
            else:label.configure(text='N/A');bar['value']=0.
        entries=rows(packet)
        for i,(label,driver,value,level) in enumerate(entries):
            text='N/A' if level is None else f'{value:.3f}  '+('▰'*round(level*8)).ljust(8,'▱')
            if not self.table.exists(str(i)):self.table.insert('', 'end',iid=str(i),text=label)
            self.table.item(str(i),text=label,values=(driver,text))
        # Clock and geometry labels deliberately do not imply audio modulation.
        self.identity.set(self.identity.get()+' | shared star clock '+str(packet['submitted'].get('u_star_time'))+
                          's | planet/moon/ring geometry: time/manual; no new mapping')

    def refresh_normal(self,latest,running):
        if not self.enabled.get():self.status.set('PAUSED - retained values.');return
        if not running or latest is None:
            self.status.set('Stopped / unavailable - start a Main Studio preview.');return
        packet,received=latest;now=time.perf_counter()
        stale=now-received>STALE_SECONDS
        target=packet.get('editing_target');row=packet.get('audio_targets',{}).get(target,{})
        scope=row.get('scope',{});endpoint=packet.get('endpoints',{})
        active=row.get('contributing',row.get('active',False))
        self.status.set(('STALE' if stale else 'Current render ACK')+' | '+str(target)+' | '+('contributing' if active else 'inactive / configure for later'))
        identity=packet.get('identity',{})
        self.identity.set(str(packet.get('source_mode','UNSPECIFIED'))+' '+str(packet.get('source_identity',''))+' | run '+str(identity.get('run',''))[:12]+' | session '+str(identity.get('session',''))[:12]+
            ' | form '+str(scope.get('form'))+' | revision '+str(scope.get('revision'))+
            ' | outgoing '+str(endpoint.get('outgoing'))+' -> incoming '+str(endpoint.get('incoming'))+
            ' | '+str(endpoint.get('recipe'))+' progress '+str(endpoint.get('progress'))+
            ' | '+str(row.get('dependency',row.get('scope_note',''))))
        audio=packet.get('audio') or {};bands=audio.get('band12') or {}
        if hasattr(bands,'to_dict'):bands=bands.to_dict()
        age=packet.get('audio_age_seconds');audio_stale=stale or age is None or age>STALE_SECONDS
        for i,(label,bar) in enumerate(zip(self.band_labels,self.band_bars)):
            levels=bands.get('levels',());edges=bands.get('edges',())
            label.configure(text=f'{edges[i]:g}-{edges[i+1]:g}' if len(edges)==13 else 'N/A')
            bar['value']=0. if audio_stale or len(levels)!=12 else meter(levels[i]) or 0.
        entries=[('Evidence',packet.get('evidence','CPU submissions; no pixel readback'),None)]
        for key,value in audio.get('legacy',{}).items():entries.append(('Analyzer '+key,'Current analyzer feature' if not audio_stale else 'Stale / unavailable',None if audio_stale else value))
        for key,value in row.get('submissions',{}).items():
            role_on=row.get('role_active',{}).get(key,True)
            entries.append((key+' input',value['consumer']+' | '+value['scope']+(' | mode inactive' if not role_on else ''),value['input'] if active and role_on and not stale else None))
            entries.append((key+' packed slot','CPU gain or selected-window encoding; not pixel intensity',value['slot'] if active and role_on and not stale else None))
        for key,value in row.get('audio_terms',{}).items():entries.append(('Proxy '+key,'Display formula only; not measured shader/pixels',value if active and not stale else None))
        for key,value in packet.get('director',{}).items():entries.append(('Director '+key,'Actual opportunity / beat qualification / timer state',value))
        entries.append(('Shared history owner',str(packet.get('shared_owner')),None))
        entries.append(('Availability',row.get('availability_note','Endpoint presence does not establish visible pixel coverage.'),None))
        for i,(label,driver,value) in enumerate(entries):
            if not self.table.exists(str(i)):self.table.insert('','end',iid=str(i),text=label)
            self.table.item(str(i),text=label,values=(driver,'N/A' if value is None else f'{value:.4g}' if type(value) in (float,int) else str(value)))
        for item in self.table.get_children():
            if int(item)>=len(entries):self.table.delete(item)
