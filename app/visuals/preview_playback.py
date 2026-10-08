"""Studio's existing preview clock and Player commands; no capture or GL owner."""
import json
import math
import os
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from player_state import Playback, defaults

PREFIX = 'ZERAWAVE_PREVIEW '


class PreviewPlayback:
    def __init__(self, renderer, run, clock=time.perf_counter):
        from renderer import LIVE_FORMS
        self.renderer, self.run, self.clock = renderer, run, clock
        self.playback = Playback(defaults(LIVE_FORMS), LIVE_FORMS)
        self.playback.start()
        self.serial = -1
        self.paused_at = None
        self.paused_total = 0.
        self.route = None
        self.last_route_input = None
        self.route_rate = 1.
        self.last_emit = -math.inf
        self.resume_after = -math.inf
        self.ready = False
        self.destination_revision = -1
        self.committed_scope = None
        self.output_keys = set()
        initial = os.environ.get('ZERAWAVE_PLAYBACK_SCOPE')
        form=os.environ.get('ZERAWAVE_PLAYBACK_FORM')
        if initial:self.apply_destination(json.loads(initial), int(form) if form is not None else None, int(os.environ.get('ZERAWAVE_DESTINATION_REVISION','0')))
        self.scope = self.scope_key()
        if renderer.debug_state == 0 and not renderer.debug_sequence:
            renderer.player = self.playback

    def scope_key(self):
        r = self.renderer
        return r.debug_state, tuple(r.debug_sequence), bool(r.transition_sequence)

    def release(self):
        self.playback.holds.clear()
        self.output_keys.clear()

    def apply_destination(self, scope, form, revision):
        from renderer import LIVE_FORMS, world_uniforms
        from studio_scope import validate_scope, compatible_scope
        scope = validate_scope(scope, LIVE_FORMS)
        if not compatible_scope(scope):raise ValueError('This destination requires its existing resource route.')
        if type(revision) is not int or revision <= self.destination_revision:return False
        if form is not None and (type(form) is not int or form not in scope['forms']):
            raise ValueError('Leaf is outside the committed scope.')
        r = self.renderer
        same = self.committed_scope == scope and form == r.director_current and r.director_target is None
        self.destination_revision = revision
        if same:return True
        self.release()
        self.playback.roster = tuple(scope['forms'])
        self.playback.configure(defaults(scope['forms']))
        self.playback.bonk_pending = self.playback.bonk_expedite = False
        r.player = self.playback
        r.debug_state = 0; r.debug_sequence = (); r.transition_sequence = False
        self.committed_scope = scope
        if form is not None:
            r.director_current = form; r.director_target = None; r.director_pending = None
            r.director_recipe = None; r.director_transition_complete = False
            r.director_bonk_expedited = False; r.director_since = r.director_time
            r.director_last_seen[form] = r.director_time
            if form == 36:r.galaxy_main_since = r.director_time
            if form == 5:r.planet_visits += 1
            r.blend_values = world_uniforms({form: 1.})
            r.director_history.append(dict(seconds=r.last_render_time, state=form,
                reason='Direct Library load', scope=scope, revision=revision))
            r.director_history = r.director_history[-64:]
        # Existing endpoint adapter applies entry/history ownership next draw.
        # Shared source/analysis/GL clocks and buffers are retained here.
        self.scope = self.scope_key()
        return True

    def drawing_time(self, wall=None):
        wall = self.clock() if wall is None else wall
        end = self.paused_at if self.paused_at is not None else wall
        return end - self.paused_total

    def route_time(self, seconds):
        """Park only selection clocks during Hold; material/music clocks continue."""
        if self.route is None or seconds < self.last_route_input:
            self.route = seconds
        else:
            dt = max(0., seconds - self.last_route_input)
            cfg = self.renderer.transition_settings
            transitioning = self.renderer.transition_sequence and self.route % (cfg['hold'] + cfg['duration']) >= cfg['hold']
            if not self.playback.held or transitioning:
                self.route += dt * self.route_rate
            if transitioning and self.route % (cfg['hold'] + cfg['duration']) < cfg['hold']:
                self.route_rate = 1.
        self.last_route_input = seconds
        return self.route

    def can_bonk(self):
        r = self.renderer
        if not self.ready or not self.playback.running or self.playback.paused:
            return False
        if self.committed_scope and len(self.committed_scope['forms']) < 2:return False
        if r.debug_sequence:
            if len(set(r.debug_sequence)) < 2:
                return False
            if r.transition_sequence and self.route is not None:
                cfg = r.transition_settings
                if self.route % (cfg['hold'] + cfg['duration']) >= cfg['hold']:
                    return self.playback.bonk_mode == 'instant'
            return True
        return r.debug_state == 0 and (r.director_target is None or self.playback.bonk_mode == 'instant')

    def command(self, packet, local=False):
        if packet.get('run') != self.run:
            raise ValueError('Playback command belongs to another preview')
        serial = packet.get('serial')
        if type(serial) is not int or not 0 <= serial < 2**31:
            raise ValueError('Invalid playback serial')
        if not local and serial <= self.serial:
            return
        op = packet.get('op')
        if op not in ('pause', 'hold', 'release', 'bonk', 'mode', 'stop', 'diagnostics', 'load', 'attach', 'resources', 'resolution','images','images_cancel'):
            raise ValueError('Unsupported preview command')
        if op == 'pause' and type(packet.get('active')) is not bool:
            raise ValueError('Pause requires an explicit state')
        if op == 'hold' and (type(packet.get('active')) is not bool or packet.get('owner') not in ('studio.mouse', 'studio.Shift_L', 'studio.Shift_R', 'output.Shift_L', 'output.Shift_R')):
            raise ValueError('Invalid momentary Hold')
        if op in ('mode', 'bonk') and packet.get('mode') not in ('normal', 'instant'):
            raise ValueError('Invalid Bonk mode')
        if op == 'diagnostics' and type(packet.get('active')) is not bool:
            raise ValueError('Invalid diagnostics switch')
        if not local:self.serial = serial
        if op=='images':
            if self.committed_scope is not None:
                from studio_scope import compatible_scope
                if not compatible_scope(self.committed_scope):raise ValueError('Image layers are unavailable on legacy Experimental routes.')
            if self.renderer.image_layers is None:
                from image_layers import ImageLayers
                self.renderer.image_layers=ImageLayers(self.renderer.ctx,self.renderer.vertices)
            self.renderer.image_layers.request(packet.get('config'),packet.get('revision'),packet.get('session'))
        elif op=='images_cancel':
            if self.renderer.image_layers is not None:self.renderer.image_layers.invalidate(packet.get('session'),packet.get('revision'))
        elif op == 'resolution':
            import glfw
            from visualizer_resolution import failure_message
            ctx=self.renderer.ctx;stage=self.renderer.enveloper_stage
            try:
                ctx.configure(packet.get('policy'),glfw.get_framebuffer_size(self.renderer.window),stage.resize if stage is not None else None)
            except Exception as exc:ctx.error=failure_message(exc)
            ctx.resolution_serial=serial
        elif op == 'load':
            self.apply_destination(packet.get('scope'),packet.get('form'),packet.get('revision'))
        elif op == 'attach':
            if getattr(self.renderer,'workspace_window',{}).get('run') == self.run:
                self.renderer.workspace_attached = True
        elif op == 'resources':
            metrics=getattr(self.renderer,'performance',None)
            if metrics is not None:metrics.owner_sample(packet.get('sample'))
        elif op == 'pause' and self.playback.paused != packet['active']:
            self.playback.pause()
            self.release()
            if self.playback.paused:
                self.paused_at = self.clock()
            else:
                self.paused_total += self.clock() - self.paused_at
                self.paused_at = None
                self.resume_after = self.clock()
                self.renderer.parameters.impact = 0.
                self.renderer.parameters.beat_tick = False
        elif op == 'hold':
            if self.ready and self.playback.running and not self.playback.paused:
                self.playback.hold(packet['owner'], packet['active'])
            elif not packet['active']:
                self.playback.hold(packet['owner'], False)
        elif op == 'release':
            self.release()
        elif op == 'mode':
            self.playback.set_bonk_mode(packet['mode'])
        elif op == 'bonk':
            self.playback.set_bonk_mode(packet['mode'])
            if self.can_bonk():
                r = self.renderer
                if r.debug_sequence:
                    cfg = r.transition_settings
                    span = cfg['hold'] + cfg['duration'] if r.transition_sequence else 28.
                    age = (self.route or 0.) % span
                    if r.transition_sequence:
                        if age < cfg['hold']:
                            self.route = (self.route or 0.) + cfg['hold'] - age
                            age = cfg['hold']
                        if packet['mode'] == 'instant':
                            self.route_rate = max(1., (span - age) / .25)
                    else:
                        self.route = (self.route or 0.) + span - age
                else:
                    self.playback.bonk(r.director_target is not None, packet['mode'])
        elif op == 'stop':
            self.release()
            self.playback.stop()
        elif op == 'diagnostics':
            metrics = getattr(self.renderer, 'performance', None)
            if metrics is not None:
                metrics.set_enabled(packet['active'])
        self.emit(force=True)

    def poll(self):
        inbox = self.renderer.color_inbox
        if self.scope_key() != self.scope:
            self.release()
            self.scope = self.scope_key()
            self.route = self.last_route_input = None
            self.route_rate = 1.
        for packet in inbox.take_controls():
            try:
                self.command(packet)
            except ValueError as exc:
                self.emit(force=True, error=str(exc))
        if inbox.eof:
            self.playback.stop()
            self.release()
        self.emit()
        return self.playback.running

    def install_output_keys(self):
        import glfw
        down=self.output_keys
        def key(window,code,scan,action,mods):
            owners={glfw.KEY_LEFT_SHIFT:'output.Shift_L',glfw.KEY_RIGHT_SHIFT:'output.Shift_R'}
            if action==glfw.REPEAT:return
            if action==glfw.RELEASE:
                down.discard(code)
                if code in owners:self.playback.hold(owners[code],False)
                return
            if code in down:return
            down.add(code)
            if code in owners:self.playback.hold(owners[code],True)
            elif code==glfw.KEY_SPACE:
                self.command(dict(run=self.run,serial=self.serial+1,op='bonk',mode=self.playback.bonk_mode),local=True)
            elif code==glfw.KEY_P and mods&glfw.MOD_CONTROL:
                self.command(dict(run=self.run,serial=self.serial+1,op='pause',active=not self.playback.paused),local=True)
            elif code==glfw.KEY_S and mods&glfw.MOD_CONTROL and mods&glfw.MOD_SHIFT:
                self.command(dict(run=self.run,serial=self.serial+1,op='stop'),local=True)
            elif code==glfw.KEY_ESCAPE:glfw.set_window_should_close(window,True)
        def focus(window,active):
            if not active:down.clear();self.release()
        glfw.set_key_callback(self.renderer.window,key)
        glfw.set_window_focus_callback(self.renderer.window,focus)

    def snapshot(self):
        state_at=getattr(self.renderer,'state_at',lambda seconds:self.renderer.debug_state)
        value=dict(run=self.run, serial=self.serial, ready=self.ready,
                    running=self.playback.running, paused=self.playback.paused,
                    held=self.playback.held, can_bonk=self.can_bonk(),
                    bonk_mode=self.playback.bonk_mode,
                    committed_scope=self.committed_scope, destination_revision=self.destination_revision,
                    current_form=self.renderer.director_current if self.committed_scope else state_at(getattr(self.renderer,'last_render_time',0.) or 0.),
                    incoming_form=self.renderer.director_target,
                    gpu_name=getattr(self.renderer,'gpu_info',{}).get('GL_RENDERER'),
                    source_seconds=getattr(self.renderer,'last_render_time',None),
                    bonk_unavailable_reason='One eligible form in this playback scope' if self.committed_scope and len(self.committed_scope['forms'])<2 else '',
                    source=getattr(getattr(self.renderer, 'studio_audio', None), 'source_mode', None))
        if getattr(self.renderer,'workspace_window',None):
            import glfw
            output=glfw.get_window_size(self.renderer.window);framebuffer=glfw.get_framebuffer_size(self.renderer.window)
            scale=getattr(self.renderer.ctx,'scale',1.) if self.renderer.ctx else 1.
            internal=getattr(self.renderer.ctx,'internal',None) if self.renderer.ctx else None
            value['dimensions']=dict(output=list(output),framebuffer=list(framebuffer),internal=list(internal) if internal else None,scale=scale)
            ctx=self.renderer.ctx
            value['resolution']=dict(policy=ctx.policy,serial=ctx.resolution_serial,error=ctx.error,limit=ctx.resolution_limit)
            value['dimensions']['scale']=1. if ctx.policy else scale
            value['window']=dict(self.renderer.workspace_window,
                context=int(glfw.get_wgl_context(self.renderer.window)),
                renderer=id(self.renderer),parameters=id(self.renderer.parameters),
                program=id(self.renderer.program),route_seconds=self.route,
                star_seconds=self.renderer.star_time,flow_seconds=self.renderer.flow_time,
                echo_seconds=self.renderer.echo_clock,
                echo_owner=id(self.renderer.echo_resources) if self.renderer.echo_resources else None,
                enveloper_owner=id(self.renderer.enveloper_stage) if self.renderer.enveloper_stage else None)
        if getattr(self.renderer,'image_layers',None) is not None:value['image_layers']=self.renderer.image_layers.snapshot()
        return value

    def emit(self, force=False, error=None):
        if force or self.clock() - self.last_emit >= .2:
            value = self.snapshot()
            if error:
                value['error'] = error
            metrics = getattr(self.renderer, 'performance', None)
            if metrics is not None:
                value['performance'] = metrics.summary()
            print(PREFIX + json.dumps(value), flush=True)
            self.last_emit = self.clock()
