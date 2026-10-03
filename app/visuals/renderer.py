from pathlib import Path
import time
import random
from functools import lru_cache

import glfw
import moderngl
import json
import math

from procedural_cosmos import uniforms as journey_uniforms, PERIOD
from parameters import VisualParameters
from mineral_resonance import FormationCache, MineralResponse
from citadel_response import TowerCadence
from magnetic_response import FluxMemory,FieldPaths
from arc_constellation import ArcNetwork,ArcStage
from auroral_memory import VeilPalette
from molten_response import MoltenMemory,MoltenPalette
from marsh_response import MarshResponse,LampCache,MarshPalette
from transition_catalog import validate_settings,select_recipe,recipe_uniforms,reprise_budgets,compatible,RECIPES,eligible_recipes
from main_director import candidate_scores,choose_transition,transition_uniforms
from envelopers import EnveloperStage
from color_controls import validate_colors, color_uniforms, targets_for, STATE_COLOR_SCENE, galaxy_authored_colors
from preview_layers import world_for_state as world_for_preview
from preview_layers import gravity_well_at, stellar_layers_at, treatment_weights, SPATIAL_TREATMENTS, ENVELOPERS, material_weights, shooting_stars_at, echo_selected, echo_weave_at, layers_at, materials_at, daddy_long_legs_at, earth_details_at, fog_details_at, plasma_details_at

VERTEX_SHADER = """
#version 330

in vec2 in_position;

void main()
{
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""


# Deterministic itinerary retained for shader fixtures; live Main uses update_blend.
# Each chapter visits every implemented form once; holds vary and overlap.
BLEND_FORMS = (11, 12, 2, 5, 7, 8, 9, 10, 13, 14, 15, 17, 18)
AIR_FORMS = (19, 20, 21, 22)
EARTH_FORMS = (24, 25, 26)
FOG_FORMS = (28, 29, 30)
PLASMA_FORMS = (32, 33, 34)
# Approved Galaxy shares the canonical live Main roster, not the fixture itinerary.
LIVE_FORMS = BLEND_FORMS + AIR_FORMS + EARTH_FORMS + FOG_FORMS + PLASMA_FORMS + (36,)
INSTANT_BONK_SECONDS = .35  # Manual handoff/tail target, never an automatic dwell.

@lru_cache(maxsize=8)
def blend_chapter(chapter):
    def order(index):
        ids = list(BLEND_FORMS)
        random.Random(7301 + index * 104729).shuffle(ids)
        return ids
    ids = order(chapter)
    ids.remove(2)
    if chapter == 0:
        ids.remove(11); ids.insert(0, 11)
    elif ids[0] == [state for state in order(chapter - 1) if state != 2][-1]:
        ids[0], ids[1] = ids[1], ids[0]
    # Corridor is a recurring anchor, not one brief chance per six minutes.
    # Keep every other form, with three varied worlds between corridor visits.
    for index in (1,5,9,13):
        ids.insert(index,2)
    rng = random.Random(2917 + chapter * 15485863)
    spans = [rng.uniform(19., 29.) * (1.5 if i % 4 == 3 else 1.) for i in range(len(ids))]
    scale = 360. / sum(spans)
    return tuple(ids), tuple(span * scale for span in spans)


def blend_uniforms(seconds, enabled=True):
    chapter = int(max(0., seconds) // 360.)
    ids, spans = blend_chapter(chapter)
    phase = max(0., seconds) % 360.
    index = 0
    while index < len(ids)-1 and phase >= spans[index]:
        phase -= spans[index]; index += 1
    following = ids[index+1] if index+1 < len(ids) else blend_chapter(chapter+1)[0][0]
    # Longer rests breathe, ordinary holds spend almost half their time gathering.
    fade_start = .68 if index % 4 == 3 else .52
    x = max(0., min(1., (phase / spans[index] - fade_start) / (1.-fade_start)))
    x = x*x*(3.-2.*x)
    weights = {ids[index]: 1.-x, following: x}
    return world_uniforms(weights, x, enabled)


def handoff_kind(source, target):
    """Related physical transitions remain optional, never a fixed itinerary."""
    pair = {source, target}
    if 15 in pair and pair.intersection((7,8,9,10,13)): return 1
    if pair.intersection((20,21)) and pair.intersection(PLASMA_FORMS): return 2
    if pair.intersection(EARTH_FORMS) and pair.intersection(FOG_FORMS): return 3
    if pair == {22,32}: return 4
    return 0


def world_family(state):
    if state in (7,8,9,10,13): return 3
    if state in (14,15,17,18): return 4
    for family, forms in ((5,AIR_FORMS),(6,EARTH_FORMS),(7,FOG_FORMS),(8,PLASMA_FORMS)):
        if state in forms: return family
    return 0


def world_uniforms(weights, progress=0., enabled=True, handoff=None):
    """Shared packing for the live director and deterministic shader fixtures."""
    air = sum(weights.get(i,0.) for i in AIR_FORMS)
    air_mix = tuple(weights.get(i,0.)/max(air,1e-12) for i in AIR_FORMS)
    earth = sum(weights.get(i,0.) for i in EARTH_FORMS)
    earth_mix = tuple(weights.get(i,0.)/max(earth,1e-12) for i in EARTH_FORMS)
    fog = sum(weights.get(i,0.) for i in FOG_FORMS)
    fog_mix = tuple(weights.get(i,0.)/max(fog,1e-12) for i in FOG_FORMS)
    plasma = sum(weights.get(i,0.) for i in PLASMA_FORMS)
    plasma_mix = tuple(weights.get(i,0.)/max(plasma,1e-12) for i in PLASMA_FORMS)
    weights = {i:w for i,w in weights.items() if i not in AIR_FORMS + EARTH_FORMS + FOG_FORMS + PLASMA_FORMS}
    world = [weights.get(2,0.), weights.get(5,0.),
             sum(weights.get(i,0.) for i in (7,8,9,10,13)),
             sum(weights.get(i,0.) for i in (14,15,17,18))]
    water = tuple(weights.get(i,0.) / max(world[2],1e-12) for i in (7,8,9,10))
    fire = tuple(weights.get(i,0.) / max(world[3],1e-12) for i in (14,15,17,18))
    # Root structure also contributes to the shared source canvas. Fade it
    # with world coverage so it cannot switch inside a departing corridor.
    root = weights.get(12,0.)
    transition = (handoff_kind(*handoff), progress, *(world_family(i) for i in handoff)) if handoff and enabled else (0.,0.,0.,0.)
    return dict(u_handoff=transition, u_directed=int(enabled), u_world_mix=tuple(world), u_water_mix=water,
                u_current_mix=weights.get(13,0.)/max(world[2],1e-12),
                u_fire_mix=fire, u_root_mix=root, u_world_warp=math.sin(math.pi*progress),
                u_air_weight=air, u_air_mix=air_mix,
                u_earth_weight=earth, u_earth_mix=earth_mix,
                u_fog_weight=fog, u_fog_mix=fog_mix,
                u_plasma_weight=plasma, u_plasma_mix=plasma_mix, u_galaxy_weight=weights.get(36,0.))


class OriginalLoopStage:
    """Exact original loop equations evaluated once per328 vertices, not per pixel."""
    def __init__(self,ctx,vertices):
        source=(Path(__file__).parent/'shaders/dream.frag').read_text(encoding='utf-8')
        functions=source[source.index('vec3 plasma_view('):source.index('float plasma_sphere(')]
        functions+=source[source.index('vec3 magnetic_core_position('):source.index('vec3 experimental_plasma_scene(')]
        fragment='#version 330\nuniform float u_time,u_scale,u_flux,u_impact;\nout vec4 position;\n'+functions+'\nvec3 projected(float f,float row){vec3 q=plasma_view(plasma_loop(f,row));return vec3(q.xy/q.z*1.35,1./q.z);}\nvoid main(){int j=int(gl_FragCoord.x);float row=floor(gl_FragCoord.y);\n if(j<41){position=vec4(projected(float(j)/40.,row),1.);return;}\n vec2 low=vec2(100.),high=vec2(-100.);\n for(int i=0;i<=40;i++){vec2 q=projected(float(i)/40.,row).xy;low=min(low,q);high=max(high,q);}\n position=vec4(low,high);\n}\n'
        self.ctx=ctx;self.program=ctx.program(vertex_shader=VERTEX_SHADER,fragment_shader=fragment)
        self.texture=ctx.texture((42,8),4,dtype='f4');self.texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
        self.texture.repeat_x=self.texture.repeat_y=False;self.fbo=ctx.framebuffer(color_attachments=(self.texture,))
        self.vao=ctx.vertex_array(self.program,[(vertices,'2f','in_position')])
    def draw(self,program,size,values):
        for name,value in zip(('u_time','u_scale','u_flux','u_impact'),values):self.program[name].value=value
        self.fbo.use();self.ctx.viewport=(0,0,42,8);self.vao.render(mode=moderngl.TRIANGLE_STRIP)
        self.ctx.screen.use();self.ctx.viewport=(0,0,*size);self.texture.use(13);program['u_original_paths'].value=13
    def release(self):
        for resource in (self.vao,self.fbo,self.texture,self.program):resource.release()


class Renderer:
    # Base flow range before the bounded musical energy boost in render().
    FLOW_FLOOR = 0.35
    FLOW_CEILING = 1.15
    FLOW_SMOOTHING_SECONDS = 0.6

    def __init__(self, width=1280, height=720, title="ZeraWave", seed=None):
        self.width = width
        self.height = height
        self.title = title

        self.window = None
        self.ctx = None
        self.program = None
        self.vertices = None
        self.vao = None
        self.surface_stage = None
        self.original_loop_stage = None
        self.enveloper_stage = None
        self.enveloper_failed = False
        self.echo_resources = None
        self.echo_parked = None
        self.echo_weight = 0.
        self.echo_last_time = None
        self.echo_clock = 0.
        self.echo_remainder = 0.
        self.cavern_cache = FormationCache()
        self.cavern_texture = None
        self.mineral_response = MineralResponse()
        self.tower_cadence = TowerCadence(7301 if seed is None else seed)
        self.flux_memory=FluxMemory(7301 if seed is None else seed)
        self.field_paths=FieldPaths(7301 if seed is None else seed)
        self.magnetic_texture=None
        self.magnetic_cache_cpu_ms=0.
        self.arc_memory=FluxMemory(7424 if seed is None else seed+123)
        self.arc_network=ArcNetwork(7301 if seed is None else seed)
        self.arc_texture=None
        self.arc_stage=None
        self.arc_cache_cpu_ms=0.
        self.aurora_memory=FluxMemory(7680 if seed is None else seed+379)
        self.veil_palette=VeilPalette()
        self.aurora_stage=None
        self.aurora_mapping_cpu_ms=0.
        self.marsh_response=MarshResponse(7810 if seed is None else seed+509)
        self.marsh_cache=LampCache();self.marsh_palette=MarshPalette();self.marsh_cache_cpu_ms=0.
        self.molten_memory=MoltenMemory(8100 if seed is None else seed+799);self.molten_palette=MoltenPalette();self.molten_mapping_cpu_ms=0.

        self.player = None
        self.startup_callback = None
        self.startup_notice = None
        self.start_time = None
        self.last_render_time = None
        self.impact_envelope = 0.0
        self.air_flash_id = 0
        self.air_flash_armed = True
        self.air_afterglow = 0.0
        self.air_trails = []
        self.flow_time = 0.0
        self.firescape_rate = self.FLOW_FLOOR
        self.firescape_travel = 0.0
        self.flow_rate = self.FLOW_FLOOR
        self.cymatics = None
        self.cymatics_material = 0.
        self.cymatics_view = (1.,.65,0.)
        from cymatics_view import BasinView
        self.cymatics_camera=BasinView()
        self.cymatics_style=(0.,-.65,.6)
        self.cymatics_mute_requested=False
        self.cosmos_seed = 7301 if seed is None else int(seed)
        self.galaxy_time = 0.0
        self.galaxy_start_visit=0
        self.galaxy_next_visit=0
        self.galaxy_recent=[]
        self.galaxy_seen_once=False
        self.galaxy_was_present=False
        self.galaxy_short_visit=False
        self.galaxy_palette_identity=None
        self.galaxy_last_status=-1000.
        self.star_time = 0.0
        self.star_rate = 1.0
        self.stellar_events = []
        self.stellar_event_id = 0
        self.stellar_armed = True
        self.stellar_last_event = -1000.
        self.galaxy_peak = 0.0
        self.galaxy_release = 0.0
        self.parameters = VisualParameters()
        self.debug_state = 0
        self.debug_sequence = ()
        self.transition_settings=validate_settings()
        self.transition_sequence=False
        self.director_recipe=None
        self.director_reprise=False
        self.layer_profiles = {}
        # Development-only color choice; independent of materials and sessions.
        self.preview_palette = "authored"
        self.color_overrides = {}
        self.color_inbox = None
        self._color_dirty = True
        self._color_active = None
        # Bounded visual event history, driven by the existing onset parameter.
        self.shockwaves = []
        self.shockwave_armed = True
        self.shockwave_serial = 0
        self.last_shockwave = -1000.0
        self.blend_values = blend_uniforms(0., False)
        # Session entropy varies live openings; explicit seeds reproduce test runs.
        self.director_seed = random.SystemRandom().getrandbits(64) if seed is None else seed
        self.director_rng = random.Random(self.director_seed)
        self.director_time = 0.
        self.director_current = None
        self.director_target = None
        self.director_since = 0.
        self.director_transition = 0.
        self.director_duration = 8.
        self.director_transition_complete = False
        self.director_bonk_expedited = False
        self.galaxy_main_since = 0.
        self.director_min_hold = 14.
        self.director_max_hold = 40.
        self.director_fast = None
        self.director_slow = None
        self.director_armed = True
        self.director_last_seen = {}
        self.director_history = []
        self.director_pending = None
        deck=list(LIVE_FORMS);self.director_rng.shuffle(deck)
        self.director_priorities={state:i/max(1,len(deck)-1) for i,state in enumerate(deck)}
        self.director_recent_pairs=[];self.director_recent_styles=[];self.director_recent_recipes=[]
        self.director_style=0;self.director_layout=(0.,0.,0.,0.);self.director_choice={}
        self.planet_visits = 0
        self.blast_events = []; self.blast_retire={};self.blast_retired=[]
        self.blast_serial = 0
        self.blast_hits = 0
        self.blast_armed = True
        self.last_blast_hit = -1000.
        self.last_blast = -1000.

    def configure_transitions(self,settings=None):
        self.transition_settings=validate_settings(settings)
        pair=self.transition_settings['pair']
        if pair:
            self.debug_sequence=tuple(pair);self.transition_sequence=True
        elif self.transition_settings['isolate'].get(world_for_preview(self.debug_state)) or any(row['enabled'] and row['id'] in RECIPES for row in self.layer_profiles.get(world_for_preview(self.debug_state),{}).get('items',[])):
            forms={1:(11,12),6:(7,8,9,10,13),16:(14,15,17,18),23:AIR_FORMS,27:EARTH_FORMS,31:FOG_FORMS,35:PLASMA_FORMS}
            if self.debug_state in forms:self.debug_sequence=forms[self.debug_state];self.transition_sequence=True
            elif self.debug_sequence:self.transition_sequence=True
        if pair:
            profile=self.layer_profiles.get(world_for_preview(pair[0]),self.layer_profiles.get('blend',{}))
            isolated=self.transition_settings['isolate'].get('pair') or self.transition_settings['isolate'].get(world_for_preview(pair[0])) or self.transition_settings['isolate'].get('blend')
            select_recipe(random.Random(0),*pair,profile,isolated)

    def sequence_blend(self,seconds):
        cfg=self.transition_settings;span=cfg['hold']+cfg['duration'];index=int(max(0.,seconds)//span)
        source=self.debug_sequence[index%len(self.debug_sequence)];target=self.debug_sequence[(index+1)%len(self.debug_sequence)]
        age=max(0.,seconds)%span
        if age<cfg['hold']:
            self.blend_values=world_uniforms({},enabled=False);return
        p=min(1.,(age-cfg['hold'])/cfg['duration']);p=p*p*(3.-2.*p)
        world=world_for_preview(source)
        profile=self.layer_profiles.get(world,self.layer_profiles.get('blend',{}))
        isolate=self.transition_settings['isolate'].get('pair') or self.transition_settings['isolate'].get(world) or self.transition_settings['isolate'].get('blend')
        style,layout,key=select_recipe(random.Random(self.cosmos_seed+index*104729),source,target,profile,isolate,index)
        self.blend_values=world_uniforms({source:1.-p,target:p},p,handoff=(source,target))
        self.blend_values.update(recipe_uniforms(key,p,source,target,layout,world_family))
        self.director_recipe=key

    def state_at(self, seconds):
        """Development-only holds; ordinary rendering keeps its existing state."""
        if self.transition_sequence:
            span=self.transition_settings['hold']+self.transition_settings['duration']
            if max(0.,seconds)%span>=self.transition_settings['hold']:return 0
            return self.debug_sequence[int(max(0.,seconds)//span)%len(self.debug_sequence)]
        if self.debug_sequence:
            return self.debug_sequence[int(max(0.0, seconds) // 28.0) % len(self.debug_sequence)]
        return self.debug_state

    def choose_world(self, energy, lift=False):
        pool=LIVE_FORMS if self.player is None else self.player.config["queue"]
        last_seen=self.director_last_seen if self.player is None or self.player.config["recent_history"] else {}
        rows=candidate_scores(pool,self.director_current,energy,lift,self.director_time,
            last_seen,self.director_recent_pairs,self.director_priorities,self.color_overrides)
        if not rows:
            self.director_choice=dict(reason='empty eligible pool fallback',state=self.director_current)
            return pool[0] if self.player is not None else (self.director_current if self.director_current is not None else LIVE_FORMS[0])
        chosen=self.director_rng.choices(rows,weights=[row['score'] for row in rows],k=1)[0]
        self.director_choice=dict(energy=energy,lift=bool(lift),source=self.director_current,
            selected=chosen,alternatives=sorted(rows,key=lambda row:row['score'],reverse=True)[:4],
            rationale='musical fit, soft recency/pair penalty, coverage and visual contrast with bounded shuffled variation')
        return chosen['state']

    def transition_progress(self):
        if self.director_target is not None:
            return min(1., max(0., (self.director_time-self.director_transition)/self.director_duration))
        return 1. if self.director_transition_complete else None

    def expedite_bonk(self):
        """Retain the current recipe/arrival and progress; shorten only its tail."""
        if self.director_target is None or self.director_bonk_expedited:
            return
        progress = self.transition_progress()
        remaining = (1.-progress)*self.director_duration
        if remaining > INSTANT_BONK_SECONDS:
            self.director_duration = INSTANT_BONK_SECONDS/(1.-progress)
            self.director_transition = self.director_time-progress*self.director_duration
        self.director_bonk_expedited = True

    def update_blend(self, seconds, delta, enabled=True):
        """Audio opportunities choose one complete handoff; never stack takeovers."""
        if self.transition_sequence:
            self.sequence_blend(seconds);return
        if not enabled:
            self.blend_values=world_uniforms({},enabled=False)
            return
        if self.player is not None and not self.player.available and self.director_current is not None:
            return  # Capture recovery holds world/transition ownership while scene motion gently idles.
        if self.player is not None and self.player.bonk_expedite:
            self.player.bonk_expedite = False
            if self.player.running and not self.player.paused:
                self.expedite_bonk()
        dt=max(0.,delta)
        if self.player is not None and (not self.player.running or (self.player.held and self.director_target is None)):
            dt=0.
        self.director_time+=dt
        now=self.director_time
        energy=max(0.,min(1.,.45*self.parameters.scale
            +.35*self.parameters.movement+.20*self.parameters.flux))
        if self.director_fast is None:
            self.director_fast=self.director_slow=energy
        self.director_fast+=(energy-self.director_fast)*(1.-math.exp(-dt/.7))
        self.director_slow+=(energy-self.director_slow)*(1.-math.exp(-dt/8.))
        impact=max(0.,min(1.,self.parameters.impact))
        hit=impact>.35 and self.director_armed
        if impact<.12:self.director_armed=True
        elif hit:self.director_armed=False
        lift=self.director_fast-self.director_slow>.12
        release=self.director_slow-self.director_fast>.12
        if self.director_current is None:
            self.director_current=self.choose_world(energy) if self.player is None else self.player.initial(lambda pool:self.choose_world(energy))
            self.director_since=now
            self.director_last_seen[self.director_current]=now
            self.planet_visits+=int(self.director_current==5)
            if self.director_current==36:self.galaxy_main_since=now
            self.director_history.append(dict(seconds=seconds,state=self.director_current,reason='opening',selection=self.director_choice))
        if self.director_target is not None:
            progress=min(1.,max(0.,(now-self.director_transition)/self.director_duration))
            if progress>=1.:
                self.director_last_seen[self.director_current]=now
                self.director_current=self.director_target;self.director_target=None
                self.director_transition_complete = True
                self.director_since=now
                self.director_min_hold=self.director_rng.uniform(12.,19.)
                self.director_max_hold=self.director_rng.uniform(32.,48.)
                self.director_min_hold,self.director_max_hold=reprise_budgets(self.director_min_hold,self.director_max_hold,self.director_reprise)
                self.director_history[-1].update(reprise=self.director_reprise,hold_min=self.director_min_hold,hold_max=self.director_max_hold)
            else:
                progress=progress*progress*(3.-2.*progress)
                self.blend_values=world_uniforms({self.director_current:1.-progress,
                    self.director_target:progress},progress, handoff=(self.director_current,self.director_target))
                if self.director_recipe:
                    self.blend_values.update(recipe_uniforms(self.director_recipe,progress,self.director_current,self.director_target,self.director_layout,world_family))
                else:
                    self.blend_values.update(transition_uniforms(self.director_style,progress,self.director_current,self.director_target,self.director_layout))
                return
        age=now-self.director_since
        reason=None
        # Preserve the authored full route on Main entry and return. Ordinary
        # world/reprise budgets remain unchanged; Galaxy becomes releasable at its
        # existing route boundary (including incoming transition time).
        route_complete=self.director_current!=36 or now-self.galaxy_main_since>=PERIOD
        if age>=self.director_min_hold and route_complete:
            if lift:reason='energy lift'
            elif release:reason='release'
            elif hit and self.director_fast>.45:reason='strong hit'
            elif age>=self.director_max_hold:reason='breathing interval'
        # Only quantize an already justified opportunity. Uncertain rhythm keeps
        # the original director, and a bounded deadline prevents waiting forever.
        confidence = self.parameters.beat_confidence
        if self.director_pending is not None:
            pending_reason, deadline = self.director_pending
            if self.parameters.beat_tick or now >= deadline or confidence < .5:
                reason = pending_reason
                self.director_pending = None
            else:
                reason = None
        elif reason and confidence >= .65 and not self.parameters.beat_tick:
            self.director_pending = (reason, now + .8)
            reason = None
        if self.player is not None:
            if not self.player.running or self.player.held:
                reason=None;self.director_pending=None
            if self.player.running and self.player.bonk_pending:
                reason='Bonk';self.director_pending=None
        if reason:
            instant_bonk = (reason == 'Bonk' and self.player is not None
                            and self.player.bonk_pending_mode == 'instant')
            choice=lambda pool:self.choose_world(energy if release else max(energy,self.director_fast),lift)
            self.director_target=self.choose_world(energy if release else max(energy,self.director_fast),lift) if self.player is None else self.player.next(self.director_current,choice)
            if self.player is not None and self.director_target in (None,self.director_current):
                self.director_target=None;self.director_since=now
                self.blend_values=world_uniforms({self.director_current:1.})
                return
            if self.director_target==36:self.galaxy_main_since=now
            self.director_reprise=(len(self.director_history)>=2 and self.director_target==self.director_history[-2]['state'] and now-self.director_last_seen.get(self.director_target,-1e6)<100.)
            profile=self.layer_profiles.get('blend',{})
            isolate=self.transition_settings['isolate'].get('blend')
            # Main can encounter an incompatible pair: retain authored compatible choices.
            if isolate and not compatible(isolate,self.director_current,self.director_target):isolate=None
            self.director_style,self.director_layout,self.director_recipe=select_recipe(self.director_rng,self.director_current,self.director_target,profile,isolate,len(self.director_history),self.director_recent_recipes)
            transition_reason=RECIPES[self.director_recipe][0]
            eligible=eligible_recipes(self.director_current,self.director_target,profile)
            self.director_recent_recipes=(self.director_recent_recipes+[self.director_recipe])[-12:]
            self.director_recent_pairs=(self.director_recent_pairs+[(self.director_current,self.director_target)])[-12:]
            self.director_recent_styles=(self.director_recent_styles+[self.director_style])[-12:]
            self.director_transition=now
            self.director_duration=self.director_rng.uniform(6.,9.) if reason!='release' else self.director_rng.uniform(8.,11.)
            # Keep the normal RNG draw/recipe route exactly; shorten only this
            # explicit manual handoff. Automatic cycles never inherit the mode.
            if instant_bonk: self.director_duration = INSTANT_BONK_SECONDS
            self.director_transition_complete = False
            self.director_bonk_expedited = instant_bonk
            self.planet_visits+=int(self.director_target==5)
            self.director_last_seen[self.director_target]=now
            self.director_history.append(dict(seconds=seconds,state=self.director_target,reason=reason,source=self.director_current,selection=self.director_choice,transition=self.director_style,transition_id=self.director_recipe,reprise=self.director_reprise,transition_reason=transition_reason,eligible_transition_ids=eligible,layout=self.director_layout))
            self.director_history=self.director_history[-64:]
        self.blend_values=world_uniforms({self.director_current:1.})

    def update_firescape_travel(self, delta_time):
        """Keep scenery moving through sustained music and short band dips."""
        energy = max(0., min(1., max(self.parameters.scale,
            self.parameters.movement, self.parameters.sparkle*.65)))
        target = self.FLOW_FLOOR + 3.*energy*energy
        tau = .25 if target>self.firescape_rate else 3.
        ease = 1.-math.exp(-max(0.,delta_time)/tau)
        self.firescape_rate += (target-self.firescape_rate)*ease
        # Add only the missing travel to the existing integrated clock.
        self.firescape_travel += max(0.,delta_time)*max(0.,self.firescape_rate-self.flow_rate)*.070

    def update_blasts(self, seconds):
        """Eight bounded sites; births stay on fresh onsets, never timer expiry."""
        expired=[e for e in self.blast_events if not 0.<=seconds-e[0]<20. or (e[1] in self.blast_retire and seconds>=self.blast_retire[e[1]]+.65)]
        for e in expired:self.blast_retired=(self.blast_retired+[(e[1],seconds,self.blast_retire.get(e[1]))])[-16:]
        self.blast_events=[e for e in self.blast_events if e not in expired]
        self.blast_retire={e[1]:self.blast_retire[e[1]] for e in self.blast_events if e[1] in self.blast_retire}
        visible = self.state_at(seconds)==18 or (self.blend_values['u_directed']
            and self.blend_values['u_world_mix'][3]*self.blend_values['u_fire_mix'][3]>.15)
        impact=max(0.,min(1.,self.parameters.impact))
        if impact<.08:self.blast_armed=True
        if not visible:
            self.blast_hits=0
            return
        new_hit = impact>=.20 and self.blast_armed and seconds-self.last_blast_hit>=.22
        if new_hit:
            self.blast_hits+=1;self.last_blast_hit=seconds;self.blast_armed=False
        if new_hit and seconds-self.last_blast>=.70:
            rng=random.Random(41+self.blast_serial*47)
            # Pick the most separated of bounded candidates in projected ground
            # space as well as world space, so far/near events do not pile up.
            candidates=[(rng.uniform(-30.,30.),seconds*.30+rng.uniform(14.,76.)) for _ in range(20)]
            def separation(site):
                x,z=site;depth=max(4.,z-seconds*.30)
                return min((min(((x-e[2])/9.)**2+((z-e[3])/12.)**2,
                    ((x/depth-e[2]/max(4.,e[3]-seconds*.30))/.22)**2
                    +((6./depth-6./max(4.,e[3]-seconds*.30))/.12)**2)
                    for e in self.blast_events),default=1.)
            x,z=max(candidates,key=separation)
            # At seven occupied slots, begin retiring the oldest before filling
            # the eighth. The .65s fade completes before the next >=.70s birth.
            if len(self.blast_events)>=7:
                self.blast_retire.setdefault(self.blast_events[0][1],seconds)
            if len(self.blast_events)>=8:
                raise RuntimeError('Aftershock retirement failed to free a bounded slot.')
            self.blast_events.append((seconds,float(self.blast_serial),x,z))
            self.blast_serial+=1;self.last_blast=seconds;self.blast_hits=0

    def update_shockwaves(self, seconds):
        """Remember strong-hit rings; no audio analysis or second simulation."""
        self.shockwaves = [event for event in self.shockwaves
                           if 0. <= seconds - event[0] < 8.]
        impact = max(0., min(1., self.parameters.impact))
        if impact < .14:
            self.shockwave_armed = True
        if ((self.state_at(seconds) == 18 or (self.blend_values['u_directed']
                and self.blend_values['u_world_mix'][3]*self.blend_values['u_fire_mix'][3] > .15)) and seconds >= 5.
                and impact >= .40 and self.shockwave_armed
                and seconds - self.last_shockwave >= 2.0):
            site = self.blast_events[self.shockwave_serial%len(self.blast_events)][1] if self.blast_events else math.floor((seconds - 5.) / 36.)
            self.shockwaves.append((seconds, float(site), impact, 0.))
            self.shockwave_serial += 1
            self.shockwaves = self.shockwaves[-8:]
            self.last_shockwave = seconds
            self.shockwave_armed = False

    def create(self):
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

        self.window = glfw.create_window(
            self.width,
            self.height,
            self.title,
            None,
            None,
        )

        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")

        visible = bool(glfw.get_window_attrib(self.window, glfw.VISIBLE))
        notice = None
        began = time.perf_counter()
        self.startup_metrics = {}
        if self.startup_callback is not None:
            self.startup_callback("context")
        if visible and self.startup_callback is None:
            from shader_startup import StartupNotice
            # Native shader compilation may hold the GIL/event thread. The
            # owned notice has its own event loop; no frozen blank GL window.
            notice = StartupNotice(self.title)
            glfw.hide_window(self.window)
            notice.phase('context')
        if visible and self.startup_callback is not None:
            glfw.hide_window(self.window)
        try:
            glfw.make_context_current(self.window)

            self.ctx = moderngl.create_context()
            self._color_uploads={};self._color_dirty=True

            shader_path = Path(__file__).parent / "shaders" / "dream.frag"
            fragment_shader = shader_path.read_text(encoding="utf-8")

            if self.startup_callback is not None:self.startup_callback('compiling')
            if notice:
                notice.phase('compiling')
            compile_start = time.perf_counter()
            self.program = self.ctx.program(
                vertex_shader=VERTEX_SHADER,
                fragment_shader=fragment_shader,
            )

            self.startup_metrics['program_seconds'] = time.perf_counter() - compile_start
            if self.startup_callback is not None:self.startup_callback('resources')
            if notice:
                notice.phase('resources')
            self.vertices = self.ctx.buffer(
                data=(
                    b"\x00\x00\x80\xbf\x00\x00\x80\xbf"
                    b"\x00\x00\x80\x3f\x00\x00\x80\xbf"
                    b"\x00\x00\x80\xbf\x00\x00\x80\x3f"
                    b"\x00\x00\x80\x3f\x00\x00\x80\x3f"
                )
            )

            self.vao = self.ctx.simple_vertex_array(
                self.program,
                self.vertices,
                "in_position",
            )

            if self.debug_state in (0,22,26) or any(state in (22,26) for state in self.debug_sequence):
                from scene_surfaces import SurfaceStage
                self.surface_stage=SurfaceStage(self.ctx);self.surface_stage.resize(glfw.get_framebuffer_size(self.window))
            if self.debug_state in (0,32,35) or any(state==32 for state in self.debug_sequence):
                self.original_loop_stage=OriginalLoopStage(self.ctx,self.vertices)
                self.original_loop_stage.draw(self.program,glfw.get_framebuffer_size(self.window),(0.,0.,0.,0.))
                self.ctx.finish()
            if self.debug_state==37:self.install_cymatics_controls()
            self.startup_metrics['create_seconds'] = time.perf_counter() - began
            # Compilation success is not presentation readiness. Keep the
            # responsive owned notice through first draw and driver first-use.
            self.startup_notice = notice
            notice = None
        except BaseException:
            if notice:
                notice.phase('failed')
            raise
        finally:
            if notice:
                notice.close()
        # Visible window is revealed only after its first complete swap.
        # Animation begins after loading, independent of compile/notice time.
        self.start_time = time.perf_counter()

    def install_cymatics_controls(self):
        glfw.set_window_title(self.window,'Water | Left drag orbit | Right/Shift drag pan | Wheel zoom | R reset | M mute')
        def button(window,which,action,mods):
            if which not in (glfw.MOUSE_BUTTON_LEFT,glfw.MOUSE_BUTTON_RIGHT):return
            x,y=self.cymatics_camera.cursor if hasattr(self.cymatics_camera,'cursor') else glfw.get_cursor_pos(window);self.cymatics_camera.button(0 if which==glfw.MOUSE_BUTTON_LEFT else 1,action==glfw.PRESS,x,y,bool(mods & glfw.MOD_SHIFT))
        def move(window,x,y):self.cymatics_camera.move(x,y,*glfw.get_window_size(window))
        def scroll(window,x,y):self.cymatics_camera.scroll(y)
        def key(window,key,scancode,action,mods):
            if action!=glfw.PRESS:return
            if key==glfw.KEY_R:self.cymatics_camera.reset()
            if key==glfw.KEY_M:self.cymatics_mute_requested=True
        glfw.set_mouse_button_callback(self.window,button);glfw.set_cursor_pos_callback(self.window,move);glfw.set_scroll_callback(self.window,scroll);glfw.set_key_callback(self.window,key)

    def release_echo(self):
        for bundle in (self.echo_resources,getattr(self,'echo_parked',None)):
            if bundle is not None:
                textures, targets, program, vao = bundle
                for resource in [vao, program, *targets, *textures]: resource.release()
        self.echo_resources = self.echo_parked = None
        self.echo_last_time = None
        self.echo_clock = self.echo_remainder = 0.

    def park_echo(self):
        # Muted history is inactive/reset, but retain one bounded 4MiB allocation.
        # Deleting its in-flight GL objects at Main -> held caused native fences.
        if self.echo_resources is not None:
            self.echo_parked=self.echo_resources;self.echo_resources=None
        self.echo_last_time=None
        self.echo_clock=self.echo_remainder=0.

    def update_echo(self, seconds, enabled, keep_alive=False):
        self.echo_weight = float(enabled)
        self.program['u_echo_weave'].value = self.echo_weight
        if not enabled and not keep_alive:
            self.park_echo()
            return
        target, viewport = self.ctx.fbo or self.ctx.screen, self.ctx.viewport
        try:
            if self.echo_resources is None:
                if self.echo_parked is not None:
                    self.echo_resources=self.echo_parked;self.echo_parked=None
                    for framebuffer in self.echo_resources[1]:framebuffer.clear()
                else:
                    textures = [self.ctx.texture((512, 512), 4, dtype='f2') for _ in range(2)]
                    for texture in textures:
                        texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
                        texture.repeat_x = texture.repeat_y = False
                    targets = [self.ctx.framebuffer(color_attachments=[texture]) for texture in textures]
                    program = self.ctx.program(vertex_shader=VERTEX_SHADER,
                        fragment_shader=(Path(__file__).parent/'shaders/echo_weave.frag').read_text())
                    vao = self.ctx.simple_vertex_array(program, self.vertices, 'in_position')
                    self.echo_resources = textures, targets, program, vao
                    for framebuffer in targets: framebuffer.clear()
            textures, targets, program, vao = self.echo_resources
            delta = 0. if self.echo_last_time is None else seconds-self.echo_last_time
            if delta < 0. or delta > 1.:
                for framebuffer in targets: framebuffer.clear()
                self.echo_clock = self.echo_remainder = 0.
                delta = 0.
            self.echo_last_time = seconds
            self.echo_remainder += min(.25, delta)
            program['history'].value = 0
            program['audio'].value = (self.parameters.scale, self.parameters.flux,
                                      self.parameters.sparkle, self.parameters.impact)
            while self.echo_remainder >= 1./60.-1e-9:
                self.echo_clock += 1./60.
                program['clock'].value = self.echo_clock
                textures[0].use(0); targets[1].use()
                self.ctx.viewport = (0, 0, 512, 512)
                vao.render(mode=moderngl.TRIANGLE_STRIP)
                textures.reverse(); targets.reverse()
                self.echo_remainder -= 1./60.
            textures[0].use(0)
            self.program['u_echo_history'].value = 0
        finally:
            target.use()
            self.ctx.viewport = viewport

    def update_galaxy_visit(self,present,delta,held=False,rewound=False):
        """One engine-owned route clock, independent of Main's world decision.
        Asset seeds/visit ordinal author content; they never choose the next world."""
        from procedural_cosmos import PERIOD,entry_phase,visit_signature
        if rewound:
            self.galaxy_time=self.galaxy_start_visit*PERIOD+(entry_phase(self.cosmos_seed,self.galaxy_start_visit) if self.galaxy_short_visit else 0.)
            self.galaxy_next_visit=self.galaxy_start_visit;self.galaxy_was_present=False;self.galaxy_seen_once=False;self.galaxy_recent=[]
        if present and not self.galaxy_was_present:
            if self.galaxy_seen_once or not held:
                for _ in range(13):
                    if visit_signature(self.cosmos_seed,self.galaxy_next_visit)[1] not in self.galaxy_recent:break
                    self.galaxy_next_visit+=1
                age=entry_phase(self.cosmos_seed,self.galaxy_next_visit) if held and self.galaxy_short_visit else 0.
                self.galaxy_time=self.galaxy_next_visit*PERIOD+age
            self.galaxy_seen_once=True;self._color_dirty=True
        if present:
            self.galaxy_time+=max(0.,delta)
            self.galaxy_next_visit=max(self.galaxy_next_visit,int(self.galaxy_time//PERIOD)+1)
        self.galaxy_was_present=bool(present)
        identity=(self.cosmos_seed,int(self.galaxy_time//PERIOD))
        if identity!=self.galaxy_palette_identity:
            if present:self.galaxy_recent=(self.galaxy_recent+[visit_signature(*identity)[1]])[-12:]
            self.galaxy_palette_identity=identity;self._color_dirty=True

    def set_galaxy_start(self, visit=0, short=False):
        if type(visit) is not int or not 0<=visit<2**31:raise ValueError('Invalid Galaxy visit')
        from procedural_cosmos import PERIOD,entry_phase
        self.galaxy_time=visit*PERIOD+(entry_phase(self.cosmos_seed,visit) if short else 0.)
        self.galaxy_start_visit=visit
        self.galaxy_next_visit=visit;self.galaxy_short_visit=bool(short)
        self.galaxy_recent=[];self.galaxy_seen_once=False;self.galaxy_was_present=False;self.galaxy_palette_identity=None;self._color_dirty=True

    def set_colors(self, values):
        # Validate transactionally: invalid snapshots never replace the last valid setup.
        clean = validate_colors(values)
        self.color_overrides = clean
        self._color_dirty = True

    def consume_pcm(self, samples):
        if self.debug_state != 37: return
        if self.cymatics is None:
            from cymatics import Basin
            self.cymatics = Basin()
        import numpy as np
        pcm=np.asarray(samples,dtype=float)
        if pcm.ndim>1:pcm=pcm.mean(axis=1)
        for start in range(0,len(pcm),2048):self.cymatics.advance(pcm[start:start+2048])

    def render(self, elapsed_time=None):
        if self.window is None:
            raise RuntimeError("Renderer has not been created")

        width, height = glfw.get_framebuffer_size(self.window)
        if width <= 0 or height <= 0:
            self.poll_events()
            return

        self.ctx.viewport = (0, 0, width, height)

        # Replay advances in song time; live callers retain the wall clock.
        current_time = (
            time.perf_counter() - self.start_time
            if elapsed_time is None else elapsed_time
        )
        rewound = self.last_render_time is not None and current_time < self.last_render_time
        if self.last_render_time is None:
            delta_time = 0.0
        else:
            delta_time = max(0.0, current_time - self.last_render_time)

        self.impact_envelope = max(
            self.parameters.impact,
            self.impact_envelope * math.exp(-delta_time * 6.0),
        )
        self.last_render_time = current_time

        # River Flow: movement sets a target current speed within a
        # bounded range, eased toward, then integrated over time.
        # Saturated movement is the strongest current, not a runaway clock.
        movement = max(0.0, min(1.0, self.parameters.movement))
        target_rate = (
            self.FLOW_FLOOR
            + (self.FLOW_CEILING - self.FLOW_FLOOR) * movement
        )

        # Strong passages have headroom beyond the old 1.15 ceiling. Integrate
        # speed, never multiply accumulated time by an instantaneous signal.
        drive = max(0.,min(1.,.45*movement+.35*self.parameters.flux+.20*self.parameters.scale))
        target_rate *= 1.+2.2*drive*drive
        target_rate = min(4.,target_rate + self.impact_envelope*.45)
        smoothing = .20 if target_rate>self.flow_rate else self.FLOW_SMOOTHING_SECONDS
        if delta_time <= 0.0:
            ease = 1.0
        else:
            ease = 1.0 - math.exp(
                -delta_time / smoothing
            )

        self.flow_rate += (target_rate - self.flow_rate) * ease
        self.flow_time += delta_time * self.flow_rate
        self.update_firescape_travel(delta_time)
        visual_time = self.flow_time

        # Star motion has its own positive, eased clock. Chorus energy can
        # accelerate it, but never reverse or teleport the accumulated angle.
        star_drive = (
            0.70 * max(0.0, min(1.0, self.parameters.flux))
            + 0.30 * max(0.0, min(1.0, self.parameters.sparkle))
        )
        if self.state_at(current_time) == 36 or self.blend_values.get('u_galaxy_weight',0.)>0.:
            # Galaxy uses normalized visual movement/bass for positive orbital
            # flow; raw flux alone rarely reaches the shared chorus threshold.
            star_drive = .50*movement + .30*max(0., min(1., self.parameters.scale)) + .20*star_drive
            star_drive = max(0., min(1., star_drive))
        chorus = max(0.0, min(1.0, (star_drive - 0.72) / 0.24))
        chorus = chorus * chorus * (3.0 - 2.0 * chorus)
        target_star_rate = (.18 + 42.0 * star_drive * star_drive) if (self.state_at(current_time) == 36 or self.blend_values.get('u_galaxy_weight',0.)>0.) else 1.0 + 0.75 * chorus
        star_smoothing=(.24 if target_star_rate>self.star_rate else .85) if (self.state_at(current_time)==36 or self.blend_values.get('u_galaxy_weight',0.)>0.) else .8
        star_ease = 1.0 if delta_time <= 0.0 else 1.0 - math.exp(-delta_time / star_smoothing)
        self.star_rate += (target_star_rate - self.star_rate) * star_ease
        self.star_time += delta_time * self.star_rate

        # Galaxy alone remembers a recent musical high, so a retreat has a
        # short, eased afterglow instead of snapping back to initial quiet.
        if rewound:
            self.galaxy_peak = 0.
            self.galaxy_release = 0.
        if self.state_at(current_time) == 36 or self.blend_values.get('u_galaxy_weight',0.)>0.:
            level = max(0., min(1., .40*self.parameters.scale
                + .35*self.parameters.flux + .25*self.parameters.sparkle))
            if self.last_render_time is not None and delta_time > 0.:
                self.galaxy_peak = max(level, self.galaxy_peak * math.exp(-delta_time / 12.))
                gap = max(0., min(1., (self.galaxy_peak-level-.10)/.45))
                peak = max(0., min(1., (self.galaxy_peak-.35)/.30))
                target = gap*gap*(3.-2.*gap) * peak*peak*(3.-2.*peak)
                easing = .8 if target > self.galaxy_release else 5.
                self.galaxy_release += (target-self.galaxy_release) * (
                    1. - math.exp(-delta_time/easing))
            else:
                self.galaxy_peak = max(self.galaxy_peak, level)
        else:
            self.galaxy_peak = 0.
            self.galaxy_release = 0.
        self.program["u_galaxy_release"].value = self.galaxy_release
        state=self.state_at(current_time)
        if rewound or (state!=36 and self.blend_values.get('u_galaxy_weight',0.)<=0.):
            self.stellar_events=[]
            self.stellar_last_event=-1000.
            self.stellar_armed=True
            if rewound:self.stellar_event_id=0
        else:
            self.stellar_events=[event for event in self.stellar_events if current_time-event[0]<10.]
            if self.parameters.impact<.08:self.stellar_armed=True
            transient=self.parameters.impact>.20 and self.stellar_armed
            # Sustained nonpercussive music can germinate a nursery too; this
            # uses existing scale/flux, without claiming phrase recognition.
            sustained=level>.52 and current_time-self.stellar_last_event>9.
            if (transient or sustained) and current_time-self.stellar_last_event>.32:
                self.stellar_event_id+=1
                self.stellar_events.append((current_time,self.stellar_event_id*2.399963,
                    (self.stellar_event_id%3)/2.,min(1.,.35+level*.40+self.parameters.impact*.65)))
                self.stellar_events=self.stellar_events[-8:]
                self.stellar_last_event=current_time
                if transient:self.stellar_armed=False
        self.program['u_stellar_events'].value=self.stellar_events+[(-1000.,0.,0.,0.)]*(8-len(self.stellar_events))
        self.program['u_gravity_well'].value=gravity_well_at(self.layer_profiles,state,current_time)
        self.program['u_stellar_layers'].value=stellar_layers_at(self.layer_profiles,state,current_time)

        self.program["u_time"].value = visual_time
        self.program["u_firescape_travel"].value = self.firescape_travel
        self.program["u_star_time"].value = self.star_time
        self.program["u_drift_time"].value = current_time
        self.program["u_resolution"].value = (
            float(width),
            float(height),
        )
        self.program["u_intensity"].value = self.parameters.intensity
        self.program["u_distortion"].value = self.parameters.distortion
        self.program["u_scale"].value = self.parameters.scale
        self.program["u_sparkle"].value = self.parameters.sparkle
        self.program["u_impact"].value = self.impact_envelope
        self.air_trails = [(seed, strength * math.exp(-delta_time * .9))
            for seed, strength in self.air_trails if strength > .003]
        if self.parameters.impact < .08:
            self.air_flash_armed = True
        elif self.parameters.impact > .20 and self.air_flash_armed:
            if self.air_afterglow > .003:
                self.air_trails = [(self.air_flash_id, self.air_afterglow)] + self.air_trails[:2]
            self.air_afterglow = 0.0
            self.air_flash_id += 1
            self.air_flash_armed = False
        self.program['u_air_flash_id'].value = float(self.air_flash_id)
        self.air_afterglow = max(self.parameters.impact,
            self.air_afterglow * math.exp(-delta_time * .9))
        self.program['u_air_afterglow'].value = self.air_afterglow
        self.program['u_air_trails'].value = self.air_trails + [(0.,0.)] * (3-len(self.air_trails))
        self.program["u_flux"].value = self.parameters.flux
        self.program["u_debug_state"].value = float(state-6 if state in (38,39,40) else state)
        self.program['u_plasma_experimental'].value=int(state in (38,39,40))
        if self.state_at(current_time)==37:
            if self.cymatics is None:
                from cymatics import Basin
                self.cymatics=Basin()
            for key,value in self.cymatics.uniforms().items():self.program[key].value=value
            self.program['u_cym_material'].value=self.cymatics_material
            self.program['u_cym_view'].value=self.cymatics_view
            pose,pan=self.cymatics_camera.sample(current_time,bool(self.cymatics_view[0]))
            self.program['u_cym_camera'].value=pose;self.program['u_cym_pan'].value=pan
            self.program['u_cym_style'].value=self.cymatics_style
        self.program["u_planet_palette"].value = int(
            self.preview_palette == "soft-dream" and self.state_at(current_time) == 5)
        mode, mask = layers_at(self.layer_profiles, self.state_at(current_time), current_time)
        self.program['u_layer_mode'].value = mode
        self.program['u_layer_mask'].value = mask
        self.program['u_daddy_long_legs'].value = daddy_long_legs_at(
            self.layer_profiles, self.state_at(current_time), current_time)
        self.program['u_shooting_stars'].value = shooting_stars_at(
            self.layer_profiles, self.state_at(current_time), current_time)
        self.program['u_fog_details'].value = fog_details_at(
            self.layer_profiles, self.state_at(current_time), current_time)
        self.program['u_plasma_details'].value = plasma_details_at(
            self.layer_profiles, self.state_at(current_time), current_time)
        self.program['u_earth_details'].value = earth_details_at(
            self.layer_profiles, self.state_at(current_time), current_time)
        self.program['u_spatial_treatments'].value = treatment_weights(self.layer_profiles, self.state_at(current_time), current_time, SPATIAL_TREATMENTS)
        self.program['u_new_materials'].value = material_weights(self.layer_profiles, self.state_at(current_time), current_time)[4:]
        self.program['u_material_mix'].value = materials_at(
            self.layer_profiles, self.state_at(current_time), current_time)
        self.update_blend(current_time, delta_time, self.state_at(current_time) == 0 and mode != 0)
        present=state==36 or self.blend_values.get('u_galaxy_weight',0.)>0.
        self.update_galaxy_visit(present,delta_time,state==36,rewound)
        if present:
            self.program['u_stellar_layers'].value=stellar_layers_at(self.layer_profiles,36,current_time)
            self.program['u_gravity_well'].value=gravity_well_at(self.layer_profiles,36,current_time)
        for name,value in journey_uniforms(self.cosmos_seed,self.galaxy_time,self.star_time).items():
            self.program[name].value=value
        from preview_layers import mineral_resonance_at
        mineral_amount=mineral_resonance_at(self.layer_profiles,state,current_time)
        cavern_present=state in (26,27) or (self.blend_values.get('u_earth_weight',0.)>0. and self.blend_values['u_earth_mix'][2]>0.)
        earth_present=state in (24,25,26,27) or self.blend_values.get('u_earth_weight',0.)>0.
        if state==0 and not cavern_present:mineral_amount=0.
        travel=(visual_time*3.+current_time*.035)*1.35
        motion=self.mineral_response.advance(current_time,delta_time,self.parameters.scale,
            self.parameters.movement,self.parameters.sparkle,self.parameters.impact,travel,
            earth_present and mineral_amount>0.)
        mineral_surface=(motion[0],motion[1],motion[2]*mineral_amount,motion[3]*mineral_amount)
        self.program['u_mineral_motion'].value=mineral_surface
        self.program['u_mineral_fronts'].value=self.mineral_response.fronts()
        self.program['u_mineral_amount'].value=mineral_amount
        self.program['u_cavern_cached'].value=int(cavern_present)
        self.program['u_cavern_cell_count'].value=192
        if cavern_present:
            data=self.cavern_cache.update(travel)
            if self.cavern_texture is None:
                self.cavern_texture=self.ctx.texture((64,24),4,dtype='f4')
                self.cavern_texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
                self.cavern_texture.repeat_x=self.cavern_texture.repeat_y=False
            if data is not None:self.cavern_texture.write(data)
            self.cavern_texture.use(location=3)
            self.program['u_cavern_cache'].value=3
            self.program['u_cavern_origin'].value=self.cavern_cache.origin

        from preview_layers import tower_cadence_at
        citadel_present=(state==22 or (state==23 and current_time%144.>=95.4)) or (self.blend_values.get('u_air_weight',0.)>0. and self.blend_values['u_air_mix'][3]>0.)
        tower_amount=tower_cadence_at(self.layer_profiles,state,current_time)
        tower=self.tower_cadence.advance(current_time,delta_time,self.parameters.scale,self.parameters.movement,
            self.parameters.sparkle,self.parameters.impact,citadel_present and tower_amount>0.)
        self.program['u_tower_motion'].value=tower
        self.program['u_tower_events'].value=self.tower_cadence.fronts()
        self.program['u_tower_visit'].value=float(self.tower_cadence.visit)
        self.program['u_tower_amount'].value=tower_amount

        from preview_layers import magnetic_memory_at
        magnetic_present=state==38
        magnetic_amount=magnetic_memory_at(self.layer_profiles,state,current_time)
        field=self.flux_memory.advance(current_time,delta_time,self.parameters.scale,self.parameters.movement,self.parameters.sparkle,self.parameters.flux,self.parameters.impact,magnetic_present and magnetic_amount>0.)
        self.program['u_magnetic_motion'].value=(field[0]*magnetic_amount,field[1]*magnetic_amount,field[2],field[3]*magnetic_amount)
        self.program['u_magnetic_events'].value=self.flux_memory.fronts()
        self.program['u_magnetic_visit'].value=float(self.flux_memory.visit)
        self.program['u_magnetic_amount'].value=magnetic_amount
        self.program['u_magnetic_paths'].value=4
        if magnetic_present:
            began_cache=time.perf_counter()
            data,bounds,groups,axes=self.field_paths.build(self.flux_memory,current_time,magnetic_amount)
            if self.magnetic_texture is None:
                self.magnetic_texture=self.ctx.texture((49,12),4,dtype='f4')
                self.magnetic_texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
                self.magnetic_texture.repeat_x=self.magnetic_texture.repeat_y=False
            self.magnetic_texture.write(data);self.magnetic_texture.use(location=4)
            self.program['u_magnetic_bounds'].value=bounds
            self.program['u_magnetic_groups'].value=groups
            self.program['u_magnetic_axes'].value=axes
            self.magnetic_cache_cpu_ms=(time.perf_counter()-began_cache)*1000
        from preview_layers import arc_relay_at
        arc_present=state==39
        arc_amount=arc_relay_at(self.layer_profiles,state,current_time)
        arc=self.arc_memory.advance(current_time,delta_time,self.parameters.scale,self.parameters.movement,self.parameters.sparkle,self.parameters.flux,self.parameters.impact,arc_present and arc_amount>0.)
        self.program['u_arc_scene'].value=6
        if arc_present:
            if self.arc_stage is None:self.arc_stage=ArcStage(self.ctx,self.vertices,VERTEX_SHADER);self._color_dirty=True
            ap=self.arc_stage.program
            ap['u_arc_motion'].value=(arc[0]*arc_amount,arc[1]*arc_amount,arc[2],arc[3]*arc_amount)
            ap['u_arc_counts'].value=(9,12)

        if arc_present:
            began_arc=time.perf_counter()
            data,bounds,groups,nodes,shapes,links=self.arc_network.build(self.arc_memory,current_time,arc_amount)
            if self.arc_texture is None:
                self.arc_texture=self.ctx.texture((17,12),4,dtype='f4')
                self.arc_texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
                self.arc_texture.repeat_x=self.arc_texture.repeat_y=False
            self.arc_texture.write(data);self.arc_texture.use(location=5)
            ap['u_arc_authored'].value=self.arc_network.pigments(self.arc_memory)
            ap['u_arc_bounds'].value=bounds;ap['u_arc_groups'].value=groups
            ap['u_arc_nodes'].value=nodes;ap['u_arc_shape'].value=shapes;ap['u_arc_links'].value=links
            self.arc_cache_cpu_ms=(time.perf_counter()-began_arc)*1000
        from preview_layers import veil_memory_at
        aurora_present=state==40
        veil_amount=veil_memory_at(self.layer_profiles,state,current_time)
        veil=self.aurora_memory.advance(current_time,delta_time,self.parameters.scale,self.parameters.movement,self.parameters.sparkle,self.parameters.flux,self.parameters.impact,aurora_present and veil_amount>0.)
        self.program['u_aurora_scene'].value=7
        if aurora_present:
            began_veil=time.perf_counter()
            if self.aurora_stage is None:self.aurora_stage=ArcStage(self.ctx,self.vertices,VERTEX_SHADER,'auroral_veil.frag',7);self._color_dirty=True
            vp=self.aurora_stage.program
            vp['u_veil_motion'].value=(veil[0]*veil_amount,veil[1]*veil_amount,veil[2],veil[3]*veil_amount)
            vp['u_veil_events'].value=self.aurora_memory.fronts();vp['u_veil_amount'].value=veil_amount
            vp['u_veil_layers'].value=6;vp['u_veil_authored'].value=self.veil_palette.sample(self.aurora_memory)
            self.aurora_mapping_cpu_ms=(time.perf_counter()-began_veil)*1000
        from preview_layers import ghostlight_memory_at
        marsh_present=(state==29 or (state==31 and 26.6<=current_time%114.<76.)) or (self.blend_values.get('u_fog_weight',0.)>0. and self.blend_values.get('u_fog_mix',(0.,0.,0.))[1]>0.)
        marsh_amount=ghostlight_memory_at(self.layer_profiles,state,current_time)
        marsh_travel=visual_time*3.2+current_time*.04
        marsh=self.marsh_response.advance(current_time,delta_time,self.parameters.scale,self.parameters.movement,self.parameters.sparkle,self.parameters.flux,self.parameters.impact,marsh_travel,marsh_present and marsh_amount>0.)
        self.program['u_marsh_cached'].value=int(marsh_present)
        self.program['u_marsh_motion'].value=(marsh[0]*marsh_amount,marsh[1]*marsh_amount,marsh[2],marsh[3]*marsh_amount)
        if marsh_present:
            began_marsh=time.perf_counter();lamps,meta,wakes=self.marsh_cache.build(self.marsh_response,current_time,visual_time,marsh_travel,marsh_amount)
            self.program['u_marsh_lamps'].value=lamps;self.program['u_marsh_meta'].value=meta;self.program['u_marsh_wakes'].value=wakes
            self.program['u_marsh_origin'].value=float(self.marsh_cache.origin);self.program['u_marsh_authored'].value=self.marsh_palette.sample(self.marsh_response)
            self.marsh_cache_cpu_ms=(time.perf_counter()-began_marsh)*1000
        from preview_layers import current_memory_at
        molten_present=(state==15 or (state==16 and 19.<=current_time%84.<56.)) or (self.blend_values.get('u_world_mix',(0.,0.,0.,0.))[3]>0. and self.blend_values.get('u_fire_mix',(0.,0.,0.,0.))[1]>0.)
        molten_amount=current_memory_at(self.layer_profiles,state,current_time)
        began_molten=time.perf_counter()
        molten=self.molten_memory.advance(current_time,delta_time,self.parameters.scale,self.parameters.movement,self.parameters.sparkle,self.parameters.flux,self.parameters.impact,molten_present and molten_amount>0.)
        self.program['u_molten_motion'].value=tuple(v*molten_amount for v in molten)
        self.program['u_molten_phase'].value=self.molten_memory.phase
        self.program['u_molten_growth'].value=self.molten_memory.development
        self.program['u_molten_amount'].value=molten_amount
        if molten_present:
            self.program['u_molten_events'].value=self.molten_memory.deposits()
            self.program['u_molten_authored'].value=self.molten_palette.sample(self.molten_memory)
        self.molten_mapping_cpu_ms=(time.perf_counter()-began_molten)*1000
        self.update_blasts(current_time)
        self.program['u_event_blasts'].value = 1
        self.program['u_blast_events'].value = self.blast_events + [(-1000.,-1.,0.,0.)]*(8-len(self.blast_events))
        self.program['u_blast_retire'].value=[self.blast_retire.get(e[1],-1000.) for e in self.blast_events]+[-1000.]*(8-len(self.blast_events))
        self.program['u_main_transition'].value=self.blend_values.get('u_main_transition',(0.,0.,0.,0.))
        self.program['u_main_layout'].value=self.blend_values.get('u_main_layout',(0.,0.,0.,0.))
        for name, value in self.blend_values.items():
            self.program[name].value = value
        self.update_shockwaves(current_time)
        self.program['u_shockwaves'].value = self.shockwaves + [
            (-1000., 0., 0., 0.)] * (8 - len(self.shockwaves))
        self.update_echo(current_time, echo_weave_at(self.layer_profiles, self.state_at(current_time), current_time),
                         echo_selected(self.layer_profiles, self.state_at(current_time)))
        update = self.color_inbox.take() if self.color_inbox else None
        if update is not None: self.set_colors(update[1])
        state = self.state_at(current_time)
        active = tuple(target.id for target in targets_for(STATE_COLOR_SCENE[state]))
        if present and state!=36:active=tuple(dict.fromkeys(active+tuple(t.id for t in targets_for('galaxy'))))
        effective_colors=galaxy_authored_colors(self.color_overrides,36 if present else state,self.cosmos_seed,int(self.galaxy_time//PERIOD))
        if self._color_dirty or active != self._color_active or any(v.get('_cycle',{}).get('mode')=='cycle' for v in effective_colors.values()):
            # Active-world changes often resolve to identical pigments/flags.
            # Do not invalidate driver uniform state with duplicate uploads.
            if not hasattr(self,'_color_uploads'):self._color_uploads={}
            programs=(self.program,self.arc_stage.program if self.arc_stage is not None else None,self.aurora_stage.program if self.aurora_stage is not None else None)
            for name, value in color_uniforms(effective_colors, active, current_time).items():
                for program in programs:
                    if program is None or name not in program:continue
                    uploaded=self._color_uploads.setdefault(program,{})
                    if uploaded.get(name)!=value:
                        program[name].value=value;uploaded[name]=value
            if present:
                next_colors=galaxy_authored_colors(self.color_overrides,36,self.cosmos_seed,int(self.galaxy_time//PERIOD)+1)
                next_values=color_uniforms(next_colors,active,current_time)
                if 'u_galaxy_colors' in next_values:self.program['u_next_galaxy_colors'].value=next_values['u_galaxy_colors']
            self._color_dirty = False
            self._color_active = active
        if arc_present:
            for name in ('u_time','u_star_time','u_scale','u_flux','u_sparkle','u_impact','u_plasma_details'):
                if name in self.program and name in self.arc_stage.program:self.arc_stage.program[name].value=self.program[name].value
            self.arc_stage.draw((width,height))
            self.ctx.screen.use();self.ctx.viewport=(0,0,width,height)
        if aurora_present:
            for name in ('u_time','u_star_time','u_scale','u_flux','u_sparkle','u_impact','u_drift_time','u_plasma_details'):
                if name in self.program and name in self.aurora_stage.program:self.aurora_stage.program[name].value=self.program[name].value
            self.aurora_stage.draw((width,height))
            self.ctx.screen.use();self.ctx.viewport=(0,0,width,height)
        if self.surface_stage is not None:
            self.surface_stage.warm_rows(travel)
            self.surface_stage.prepare_cavern(travel)
        self.program['u_cavern_surface_on'].value=0;self.program['u_citadel_surface_on'].value=0
        if cavern_present or citadel_present:
            if self.surface_stage is None:
                from scene_surfaces import SurfaceStage
                self.surface_stage=SurfaceStage(self.ctx)
            self.surface_stage.draw(self,(width,height),cavern_present,citadel_present,(mineral_surface,tower,mineral_amount))
        original_loops=state in (32,35) or (state==0 and self.blend_values.get('u_plasma_weight',0.)>0. and self.blend_values.get('u_plasma_mix',(0.,0.,0.))[0]>0.)
        self.program['u_original_path_on'].value=int(original_loops)
        if original_loops:
            if self.original_loop_stage is None:self.original_loop_stage=OriginalLoopStage(self.ctx,self.vertices)
            self.original_loop_stage.draw(self.program,(width,height),(visual_time,self.parameters.scale,self.parameters.flux,self.impact_envelope))
        weights=treatment_weights(self.layer_profiles,state,current_time,ENVELOPERS)
        if max(weights)>0. and width>0 and height>0 and not self.enveloper_failed:
            try:
                if self.enveloper_stage is None:
                    self.enveloper_stage=EnveloperStage(self.ctx,self.vertices,VERTEX_SHADER)
                self.enveloper_stage.draw(self.program,self.vao,(width,height),current_time,state,weights,
                    self.parameters,color_uniforms(self.color_overrides,active,current_time))
            except Exception as exc:
                if self.enveloper_stage:self.enveloper_stage.release();self.enveloper_stage=None
                self.enveloper_failed=True
                print('Enveloper fallback to untreated scene: '+str(exc),flush=True)
                self.ctx.screen.use();self.ctx.viewport=(0,0,width,height)
                self.program['u_resolution'].value=(float(width),float(height))
                self.vao.render(mode=moderngl.TRIANGLE_STRIP)
        else:
            if self.enveloper_stage:self.enveloper_stage.release();self.enveloper_stage=None
            if max(weights)<=0.:self.enveloper_failed=False
            self.ctx.screen.use();self.ctx.viewport=(0,0,width,height)
            self.vao.render(mode=moderngl.TRIANGLE_STRIP)
        if self.color_inbox and present and current_time-self.galaxy_last_status>=1.:
            from studio_color_link import ACK_PREFIX
            print(ACK_PREFIX+json.dumps(dict(galaxy_visit=int(self.galaxy_time//PERIOD),galaxy_phase=self.galaxy_time%PERIOD,galaxy_next_visit=self.galaxy_next_visit,star_rate=self.star_rate)),flush=True)
            self.galaxy_last_status=current_time
        if update is not None:
            self.color_inbox.applied(update[0], current_time, self.echo_clock)

    def should_close(self):
        return glfw.window_should_close(self.window)

    def poll_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self.window)
        if self.startup_callback is not None:
            callback=self.startup_callback;self.startup_callback=None
            glfw.show_window(self.window);glfw.poll_events();callback("ready")
        if self.startup_notice is not None:
            notice = self.startup_notice
            self.startup_notice = None
            glfw.show_window(self.window)
            glfw.poll_events()
            self.startup_metrics['first_present_seconds'] = time.perf_counter()-notice.started
            notice.phase('ready')
            close_start=time.perf_counter()
            notice.close(pump=glfw.poll_events)
            self.startup_metrics['notice_close_seconds']=time.perf_counter()-close_start

    def get_time(self):
        if self.start_time is None:
            return 0.0

        return time.perf_counter() - self.start_time

    def close(self):
        if self.startup_notice is not None:
            self.startup_notice.close();self.startup_notice=None
        if self.cavern_texture is not None:
            self.cavern_texture.release();self.cavern_texture=None;self.cavern_cache.origin=None
        if self.magnetic_texture is not None:self.magnetic_texture.release();self.magnetic_texture=None
        if self.arc_texture is not None:self.arc_texture.release();self.arc_texture=None
        if self.arc_stage is not None:self.arc_stage.release();self.arc_stage=None
        if self.aurora_stage is not None:self.aurora_stage.release();self.aurora_stage=None
        if self.surface_stage is not None:
            self.surface_stage.release();self.surface_stage=None
        if self.original_loop_stage is not None:self.original_loop_stage.release();self.original_loop_stage=None
        if self.enveloper_stage:self.enveloper_stage.release();self.enveloper_stage=None
        if self.color_inbox: self.color_inbox.close()
        self._color_uploads={}
        self.release_echo()
        if self.vao is not None:
            self.vao.release()

        if self.vertices is not None:
            self.vertices.release()

        if self.program is not None:
            self.program.release()

        if self.ctx is not None:
            self.ctx.release()

        if self.window is not None:
            glfw.destroy_window(self.window)

        glfw.terminate()
