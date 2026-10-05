"""Bounded parameter adapters for the existing Planet Canvas audio targets.

No analysis or clocks are created here. Stable target/role ordering is the
uniform contract; append roles/targets, and never silently reuse their slots.
"""
from copy import deepcopy
from pathlib import Path
import math
import threading
import time
from spectral_listening import listening_defaults,listening_bounds,validate_listening,listening_choices,require_listening_bins
from planet_listening import ListeningState,names_for_roles,titles as listening_titles,INGREDIENTS,pack_input,derived


def role(key,label,source,factor=1.,modes='all'):
    return dict(key=key,label=label,source=source,factor=factor,modes=modes,default=1.,bounds=(0.,2.))


def roles(*items):return [role(*item) for item in items]


SPECS={
 'planet.material.alloy':roles(('bass_shape','Bass -> disk width','bass',.035),('flux_deform','Flux -> surface deformation','flux',.4),('sparkle_glint','Sparkle -> glint light','sparkle',.3),('impact_sheen','Impact -> sheen light','impact',.12)),
 'planet.material.lattice':roles(('bass_shape','Bass -> vertex size','bass',.025),('flux_tilt','Flux -> tilt','flux',.10),('sparkle_light','Sparkle -> wire/glow light','sparkle',.22),('impact_light','Impact -> wire light','impact',.10)),
 'planet.material.echo_weave':roles(('bass_advection','Bass -> ink travel rate','bass',1.5),('flux_advection','Flux -> ink travel rate','flux',1.2),('bass_injection','Bass -> ink injection','bass',1.2),('impact_injection','Impact -> ink injection (raw onset)','raw_impact',2.)),
 'planet.material.ink_archipelago':roles(('bass_veins','Bass -> vein spacing','bass',3.),('sparkle_light','Sparkle -> pearl light','sparkle',.32),('flux_light','Flux -> pearl light','flux',.12)),
 'planet.material.interference_silk':roles(('bass_light','Bass -> crest light','bass',.15),('sparkle_light','Sparkle -> crest light','sparkle',.20)),
 'planet.material.cellular_mosaic':roles(('bass_body','Bass -> body growth light','bass',.18),('sparkle_seams','Sparkle -> seam light','sparkle',.16),('flux_seams','Flux -> seam light','flux',.08)),
 'planet.spatial.tunnel':roles(('flux_presence','Flux -> Tunnel presence','flux',1.,'enveloped'),('bass_presence','Bass -> Tunnel presence','pressure',.35,'enveloped')),
 'planet.spatial.fractal':roles(('flux_presence','Flux -> fold presence','flux',1.,'enveloped'),('bass_presence','Bass -> fold presence','pressure',.30,'enveloped'),('flux_fold','Flux -> fold offset','flux',.15),('bass_fold','Bass -> authored fold offset','bass',.08,'authored')),
 'planet.spatial.horizon':roles(('flux_presence','Flux -> pathway presence','flux',.35,'enveloped'),('bass_presence','Bass -> pathway presence','bass',.30,'enveloped')),
 'planet.spatial.elastic_lenses':roles(('bass_drive','Bass -> lens displacement','bass',.5),('flux_drive','Flux -> lens displacement','flux',.5)),
 'planet.spatial.braided_flow':roles(('bass_drive','Bass -> braided displacement','bass',.5),('flux_drive','Flux -> braided displacement','flux',.5)),
 'planet.spatial.nested_windows':roles(('bass_drive','Bass -> window deformation','bass',.5),('flux_drive','Flux -> window deformation','flux',.5)),
 'planet.fx.sparkles':roles(('sparkle_light','Sparkle -> localized light','sparkle',.8)),
 'planet.fx.flecks':roles(('sparkle_presence','Sparkle -> fleck presence','sparkle',.4),('flux_presence','Flux -> fleck presence','flux',.35),('sparkle_light','Sparkle -> fleck light','sparkle',.5),('bass_cells','Bass -> fleck cell scale','bass',2.),('impact_size','Impact -> fleck size','impact',.03),('sparkle_shape','Sparkle -> fleck elongation','sparkle',1.5),('flux_drift','Flux -> turbulent drift amplitude','flux',.4)),
 'planet.fx.beams':roles(('impact_gate','Impact -> beam event gate','impact',1.2),('flux_gate','Flux -> beam event gate','flux',.5),('sparkle_gate','Sparkle -> beam event gate','sparkle',.3)),
 'planet.enveloper.prism_assembly':roles(('audio_motion','Audio -> tile motion/edge tint','energy',.62)),
 'planet.enveloper.digital_bloom':roles(('audio_amount','Audio -> quantization/tint/scan','energy',.62),('audio_blocks','Audio -> block size','energy',16.)),
 'planet.enveloper.chromatic_memory':roles(('audio_retention','Audio -> memory retention','energy',.62),('audio_drift','Audio -> memory displacement','energy',.62)),
 'planet.rings':roles(('sparkle_reflection','Sparkle -> ring reflection light','sparkle',.3)),
 'planet.moon_dust':roles(('sparkle_strength','Sparkle -> all dust wakes','sparkle',.65),('flux_strength','Flux -> all dust wakes','flux',.45)),
 'planet.shooting_stars':roles(('sparkle_light','Sparkle -> streak light','sparkle',.35),('impact_light','Impact -> streak light','impact',.35)),
 'planet.surface_response':roles(('audio_chroma','Audio -> planet + ring chroma','surface',1.2),('audio_lift','Audio -> planet + ring light','surface',.30),
     ('movement_clock','Movement -> shared Planet clock','movement'),('audio_clock','Audio drive -> shared Planet clock','flow_drive'),('impact_clock','Impact -> shared Planet clock burst','impact',.45)),
}
TARGETS=tuple(SPECS)
INDEX={key:i for i,key in enumerate(TARGETS)}
STAR_INDEX=len(TARGETS)
UNIFORM_ROWS=len(TARGETS)*2+1 # Starfield's four GPU roles; sky-clock gains are CPU-only.
STAR_TARGET='planet.starfield'
STAR_WINDOWS=('flux','sparkle','impact')
WINDOWS={target:names_for_roles(items) for target,items in SPECS.items()}
# Shape/travel terms benefit above 2 for weak inputs. Keep light, event, presence,
# clock, history and all other gain limits intact; shader input ceilings remain 1.
WIDER_GAINS={'planet.material.alloy':('bass_shape','flux_deform'),
             'planet.material.lattice':('bass_shape','flux_tilt'),
             'planet.material.echo_weave':('flux_advection',)}
for target,keys in WIDER_GAINS.items():
    for r in SPECS[target]:
        if r['key'] in keys:r['bounds']=(0.,4.)


def legacy_baseline(target):return dict(enabled=True,**{r['key']:r['default'] for r in SPECS[target]})
def baseline(target):return dict(legacy_baseline(target),**listening_defaults(WINDOWS[target]))
def bounds(target):return dict({r['key']:r['bounds'] for r in SPECS[target]},**listening_bounds(WINDOWS[target]))
def titles(target):return dict({r['key']:r['label'] for r in SPECS[target]},**listening_titles(WINDOWS[target]))
def authored_path(target):return Path(__file__).with_name('audio_'+target.removeprefix('planet.').replace('.','_')+'_authored.json')


def validate(target,settings):
    if target in SPECS and isinstance(settings,dict) and set(settings)==set(legacy_baseline(target)):
        settings=dict(baseline(target),**settings)
    if target not in SPECS or not isinstance(settings,dict) or set(settings)!=set(baseline(target)):
        raise ValueError('Unknown audio tuning target/settings')
    if type(settings['enabled']) is not bool:raise ValueError('Invalid tuning override flag')
    c={'enabled':settings['enabled']}
    validate_listening(settings,WINDOWS[target])
    c.update({key:settings[key] for key in listening_defaults(WINDOWS[target]) if key.endswith('_enabled')})
    for key,(low,high) in bounds(target).items():
        v=settings[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high:raise ValueError('Invalid '+key)
        c[key]=float(v)
    return c


def scoped_note(target,mode):
    if target.startswith('planet.spatial.'):
        return 'Shared material/detail carrier. Presence audio gains inactive in Selected/Cycle; authored and Meld routes retained.'
    if target.startswith('planet.enveloper.'):
        return 'Whole final composition/history while this Enveloper leads. Clock and static strength retained.'
    if target=='planet.surface_response':return 'Chroma/light: planet AND rings, excludes moons/stars. Clock gains: shared Planet material/spatial clock; integrated speed, existing floors/ceiling/easing. Independent star and orbit clocks retained.'
    if target=='planet.moon_dust':return 'All moon dust wakes together. No independent moon or orbit control.'
    if target=='planet.fx.flecks':return 'Local fleck contributions; shared domain/clock retained. Sparkle-dependent elapsed-time phase remains untuned (phase-jump risk).'
    if target=='planet.material.echo_weave':return 'Local ink history; bass/flux advection and bass/raw-onset injection. Clock/history retained; sparkle input unused.'
    return 'Named local audio contributions; shared coordinate deformation, clocks and authored bases retained.'


def role_active(r,mode):return r['modes']=='all' or (r['modes']=='enveloped' and mode!=1) or (r['modes']=='authored' and mode==0)

def contribution_state(mode,mask,materials,new_materials,echo,spatials,envelopers,shooting,failed=False):
    """Selection/weight availability, not a claim about shader coverage/pixels."""
    from preview_layers import BITS,NEW_MATERIALS,SPATIAL_TREATMENTS,ENVELOPERS
    result={target:False for target in TARGETS}
    for key,index in (('alloy',1),('lattice',2)):result['planet.material.'+key]=materials[index]>0.
    result['planet.material.echo_weave']=echo>0.
    for key,weight in zip(NEW_MATERIALS,new_materials):result['planet.material.'+key]=weight>0.
    for key in ('tunnel','fractal','horizon'):result['planet.spatial.'+key]=mode==0 or bool(mask & BITS[key])
    for key,weight in zip(SPATIAL_TREATMENTS,spatials):result['planet.spatial.'+key]=weight>0.
    for key in ('sparkles','flecks','beams'):result['planet.fx.'+key]=mode==0 or bool(mask & BITS[key])
    lead=max(range(3),key=lambda i:envelopers[i])
    for i,key in enumerate(ENVELOPERS):result['planet.enveloper.'+key]=not failed and i==lead and envelopers[i]>0.
    result['planet.rings']=mode==0 or bool(mask & BITS['rings'])
    result['planet.moon_dust']=mode==0 or bool(mask & BITS['moons'])
    result['planet.shooting_stars']=shooting>0. and (mode==0 or bool(mask & BITS['stars']))
    result['planet.surface_response']=True
    return result
def clip(v):return max(0.,min(1.,v))
def smooth(a,b,v):
    x=clip((v-a)/(b-a));return x*x*(3.-2.*x)


class PlanetAudioTuning:
    def __init__(self,authored=None,clock=time.perf_counter):
        self.clock=clock;self.lock=threading.Lock();self.pending={};self.state={}
        self.listening={target:ListeningState(clock) for target in TARGETS+(STAR_TARGET,)}
        self.selected={};self.listening_details={};self.packed={};self.star_settings={}
        for target in TARGETS:
            a=validate(target,(authored or {}).get(target,baseline(target)))
            self.state[target]=dict(settings=dict(a,enabled=False),authored=a,revision=0)

    def submit(self,target,revision,settings,authored=None):
        c=validate(target,settings);a=None if authored is None else validate(target,authored)
        if a is not None and not a['enabled']:raise ValueError('Invalid authored baseline')
        if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid tuning revision')
        with self.lock:
            old=self.state[target];pending=self.pending.get(target)
            if revision<=max(old['revision'],pending[0] if pending else -1):return False
            if a is None and pending is not None:a=pending[2]
            if not c['enabled']:c=dict(a or old['authored'],enabled=False)
            measurement=self.listening[target].measurement
            if measurement is not None:
                bins=tuple(i*measurement['sample_rate']/measurement['sample_count'] for i in range(measurement['sample_count']//2+1))
                try:
                    require_listening_bins(c if c['enabled'] else a or old['authored'],WINDOWS[target],bins)
                    if a is not None:require_listening_bins(a,WINDOWS[target],bins)
                except ValueError as exc:
                    old.update(rejected_revision=revision,error=str(exc));return False
            old.update(rejected_revision=None,error=None)
            self.pending[target]=(revision,c,a)
        return True

    def analysis_settings(self,target):
        with self.lock:
            p=self.state[target];c=p['settings'] if p['settings']['enabled'] else p['authored']
            return p['revision'],listening_choices(c,WINDOWS[target])

    def observe(self,payload):
        with self.lock:
            for target,state in self.listening.items():state.observe((payload or {}).get(target))

    def packed_gains(self,target,active=True):
        return self.packed.get(target,self.gains(target,active)) if active else (1.,)*len(SPECS[target])

    def local_sources(self,target,legacy):
        return self.selected.get(target,derived(legacy))

    def resolve(self,active,star=None,inputs=None,delta=0.,mode=0,rewound=False):
        with self.lock:
            if rewound:
                for state in self.listening.values():state.reset_impact()
            for target,(revision,c,a) in self.pending.items():
                self.state[target].update(revision=revision,settings=c)
                if a is not None:self.state[target]['authored']=a
            self.pending.clear();rows=[];legacy=derived(inputs or {})
            if not active:
                # Inactive adapters still apply pending edits/ACK revisions.
                # Listening and gain preparation resumes only when Planet owns
                # an endpoint; its selected histories are unavailable meanwhile.
                self.selected.clear();self.packed.clear();self.listening_details={}
                for target in TARGETS+(STAR_TARGET,):
                    self.listening[target].reset_impact()
                self.star_settings=dict(listening_defaults(STAR_WINDOWS),**(star or {}))
                return 0,[(1.,1.,1.,1.)]*UNIFORM_ROWS
            for target in TARGETS:
                p=self.state[target];c=p['settings'] if p['settings']['enabled'] else p['authored']
                local,details=self.listening[target].select(c,WINDOWS[target],legacy,active,delta)
                self.selected[target]=local;self.listening_details[target]=details;values=[]
                for r in SPECS[target]:
                    slot=c[r['key']] if active else 1.;source=r['source']
                    if target in ('planet.spatial.tunnel','planet.spatial.fractal','planet.spatial.horizon') and r['key'].endswith('_presence') and mode==2:
                        source='bass' if r['key'].startswith('bass') else 'flux'
                    if role_active(r,mode) and any(details[name]['enabled'] for name in INGREDIENTS[source]):slot=pack_input(local.get(source,0.),slot)
                    values.append(slot)
                self.packed[target]=tuple(values);values+=[1.]*8
                rows.extend((tuple(values[:4]),tuple(values[4:8])))
            from band_attack_tuning import PRESENTATION_BOUNDS
            self.star_settings=dict(listening_defaults(STAR_WINDOWS),**(star or {}))
            local,details=self.listening[STAR_TARGET].select(self.star_settings,STAR_WINDOWS,legacy,active,delta)
            self.selected[STAR_TARGET]=local;self.listening_details[STAR_TARGET]=details
            values=[(star or {}).get(key,1.) if active else 1. for key in PRESENTATION_BOUNDS]
            if any(row['enabled'] for row in details.values()):
                chorus=smooth(.38,.88,.48*clip(local.get('flux',0.))+.22*clip(local.get('sparkle',0.))+.30*clip(local.get('impact',0.)))
                values=[pack_input(chorus,gain) for gain in values]
            rows.append(tuple(values[:4]))
        return int(any(v!=1. for row in rows for v in row)),rows

    def gains(self,target,active=True):
        with self.lock:
            p=self.state[target];c=p['settings'] if p['settings']['enabled'] else p['authored']
            return tuple(c[r['key']] if active else 1. for r in SPECS[target])

    def status(self,active,inputs,mode,contributing=None):
        values=derived(inputs);result={}
        with self.lock:
            for target,p in self.state.items():
                c=p['settings'] if p['settings']['enabled'] else p['authored'];terms={};available={}
                local=self.selected.get(target,values)
                for r in SPECS[target]:
                    available[r['key']]=bool(active and role_active(r,mode))
                    gain=c[r['key']] if available[r['key']] else 1.
                    src=r['source'];factor=r['factor']
                    if target in ('planet.spatial.tunnel','planet.spatial.fractal','planet.spatial.horizon') and r['key'].endswith('_presence') and mode==2:
                        src='bass' if r['key'].startswith('bass') else 'flux';factor=.45 if src=='bass' else .55
                    terms[r['key']]=clip(local.get(src,0.)*gain)*factor
                result[target]=dict(target=target,version=1,active=bool(active),revision=p['revision'],
                    rejected_revision=p.get('rejected_revision'),error=p.get('error'),
                    settings=deepcopy(p['settings']),authored=deepcopy(p['authored']),effective=deepcopy(c),
                    role_active=available,audio_terms=terms,inputs=values,local_inputs=local,mode=mode,
                    listening=self.listening[target].details(c,WINDOWS[target],active),
                    contributing=None if contributing is None else bool(active and contributing.get(target,False)),
                    scope=scoped_note(target,mode),term_kind='Named scalar contribution proxy; shared floors/envelopes/coverage remain. No pixel brightness claim.',rendered_wall=self.clock())
        return result
