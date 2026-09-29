from pathlib import Path
import time
import random
from functools import lru_cache

import glfw
import moderngl
import math

from parameters import VisualParameters
from envelopers import EnveloperStage
from color_controls import validate_colors, color_uniforms, targets_for, STATE_COLOR_SCENE
from preview_layers import treatment_weights, SPATIAL_TREATMENTS, ENVELOPERS, material_weights, shooting_stars_at, echo_selected, echo_weave_at, layers_at, materials_at, daddy_long_legs_at, earth_details_at, fog_details_at, plasma_details_at

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
LIVE_FORMS = BLEND_FORMS + AIR_FORMS + EARTH_FORMS + FOG_FORMS + PLASMA_FORMS

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
                u_plasma_weight=plasma, u_plasma_mix=plasma_mix)


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
        self.enveloper_stage = None
        self.enveloper_failed = False
        self.echo_resources = None
        self.echo_last_time = None
        self.echo_clock = 0.
        self.echo_remainder = 0.

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
        self.star_time = 0.0
        self.star_rate = 1.0
        self.parameters = VisualParameters()
        self.debug_state = 0
        self.debug_sequence = ()
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
        self.director_min_hold = 14.
        self.director_max_hold = 40.
        self.director_fast = None
        self.director_slow = None
        self.director_armed = True
        self.director_last_seen = {}
        self.director_history = []
        self.director_pending = None
        self.planet_visits = 0
        self.blast_events = []
        self.blast_serial = 0
        self.blast_hits = 0
        self.blast_armed = True
        self.last_blast_hit = -1000.
        self.last_blast = -1000.

    def state_at(self, seconds):
        """Development-only holds; ordinary rendering keeps its existing state."""
        if self.debug_sequence:
            return self.debug_sequence[int(max(0.0, seconds) // 28.0) % len(self.debug_sequence)]
        return self.debug_state

    def choose_world(self, energy, lift=False):
        # Preference, not a playlist: quiet worlds remain possible at high energy.
        preferred = {11:.25,12:.4,2:.75,5:.65,7:.65,8:.3,9:.25,
                     10:.55,13:.25,14:.7,15:.5,17:.8,18:.9,
                     19:.3,20:.75,21:.85,22:.6,24:.3,25:.65,26:.7,28:.4,29:.25,30:.85,32:.65,33:.9,34:.35}
        choices=[];scores=[]
        for state in LIVE_FORMS:
            if state == self.director_current:continue
            last=self.director_last_seen.get(state)
            absence=240. if last is None else self.director_time-last
            if absence<38.:continue
            fit=.15+math.exp(-((energy-preferred[state])/.30)**2)
            novelty=.5+min(absence,180.)/90.
            anchor=1.
            if state in (2,5) and energy>.48:
                waiting=self.director_time-(last if last is not None else 0.)
                anchor=1.6+min(24.,(max(0.,waiting-35.)/18.)**2)
            if state==5 and lift:anchor*=2.5
            affinity = 1.65 if handoff_kind(self.director_current,state) else 1.
            choices.append(state);scores.append(fit*novelty*anchor*affinity)
        return self.director_rng.choices(choices,weights=scores,k=1)[0]

    def update_blend(self, seconds, delta, enabled=True):
        """Audio opportunities choose one complete handoff; never stack takeovers."""
        if not enabled:
            self.blend_values=world_uniforms({},enabled=False)
            return
        dt=max(0.,delta)
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
            self.director_current=self.choose_world(energy)
            self.director_since=now
            self.director_last_seen[self.director_current]=now
            self.planet_visits+=int(self.director_current==5)
            self.director_history.append(dict(seconds=seconds,state=self.director_current,reason='opening'))
        if self.director_target is not None:
            progress=min(1.,max(0.,(now-self.director_transition)/self.director_duration))
            if progress>=1.:
                self.director_last_seen[self.director_current]=now
                self.director_current=self.director_target;self.director_target=None
                self.director_since=now
                self.director_min_hold=self.director_rng.uniform(12.,19.)
                self.director_max_hold=self.director_rng.uniform(32.,48.)
            else:
                progress=progress*progress*(3.-2.*progress)
                self.blend_values=world_uniforms({self.director_current:1.-progress,
                    self.director_target:progress},progress, handoff=(self.director_current,self.director_target))
                return
        age=now-self.director_since
        reason=None
        if age>=self.director_min_hold:
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
        if reason:
            self.director_target=self.choose_world(energy if release else max(energy,self.director_fast),lift)
            self.director_transition=now
            self.director_duration=self.director_rng.uniform(6.,9.) if reason!='release' else self.director_rng.uniform(8.,11.)
            self.planet_visits+=int(self.director_target==5)
            self.director_last_seen[self.director_target]=now
            self.director_history.append(dict(seconds=seconds,state=self.director_target,reason=reason))
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
        self.blast_events = [e for e in self.blast_events if 0.<=seconds-e[0]<20.]
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
            # Recycle the oldest (most faded) site instead of waiting for all
            # eight 20-second lifetimes to expire. Capacity stays bounded.
            self.blast_events = self.blast_events[-7:]
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

        glfw.make_context_current(self.window)

        self.ctx = moderngl.create_context()

        shader_path = Path(__file__).parent / "shaders" / "dream.frag"
        fragment_shader = shader_path.read_text(encoding="utf-8")

        self.program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=fragment_shader,
        )

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

        self.start_time = time.perf_counter()

    def release_echo(self):
        if self.echo_resources is not None:
            textures, targets, program, vao = self.echo_resources
            for resource in [vao, program, *targets, *textures]: resource.release()
            self.echo_resources = None
        self.echo_last_time = None
        self.echo_clock = self.echo_remainder = 0.

    def update_echo(self, seconds, enabled, keep_alive=False):
        self.program['u_echo_weave'].value = float(enabled)
        if not enabled and not keep_alive:
            self.release_echo()
            return
        target, viewport = self.ctx.fbo or self.ctx.screen, self.ctx.viewport
        try:
            if self.echo_resources is None:
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

    def set_colors(self, values):
        # Validate transactionally: invalid snapshots never replace the last valid setup.
        clean = validate_colors(values)
        self.color_overrides = clean
        self._color_dirty = True

    def render(self, elapsed_time=None):
        if self.window is None:
            raise RuntimeError("Renderer has not been created")

        width, height = glfw.get_framebuffer_size(self.window)

        self.ctx.viewport = (0, 0, width, height)

        # Replay advances in song time; live callers retain the wall clock.
        current_time = (
            time.perf_counter() - self.start_time
            if elapsed_time is None else elapsed_time
        )
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
        chorus = max(0.0, min(1.0, (star_drive - 0.72) / 0.24))
        chorus = chorus * chorus * (3.0 - 2.0 * chorus)
        target_star_rate = 1.0 + 0.75 * chorus
        star_ease = 1.0 if delta_time <= 0.0 else 1.0 - math.exp(-delta_time / 0.8)
        self.star_rate += (target_star_rate - self.star_rate) * star_ease
        self.star_time += delta_time * self.star_rate

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
        self.program["u_debug_state"].value = float(self.state_at(current_time))
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
        self.update_blasts(current_time)
        self.program['u_event_blasts'].value = 1
        self.program['u_blast_events'].value = self.blast_events + [(-1000.,-1.,0.,0.)]*(8-len(self.blast_events))
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
        if self._color_dirty or active != self._color_active or any(v.get('_cycle',{}).get('mode')=='cycle' for v in self.color_overrides.values()):
            for name, value in color_uniforms(self.color_overrides, active, current_time).items():
                if name in self.program: self.program[name].value = value
            self._color_dirty = False
            self._color_active = active
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
        if update is not None:
            self.color_inbox.applied(update[0], current_time, self.echo_clock)

    def should_close(self):
        return glfw.window_should_close(self.window)

    def poll_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def get_time(self):
        if self.start_time is None:
            return 0.0

        return time.perf_counter() - self.start_time

    def close(self):
        if self.enveloper_stage:self.enveloper_stage.release();self.enveloper_stage=None
        if self.color_inbox: self.color_inbox.close()
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
