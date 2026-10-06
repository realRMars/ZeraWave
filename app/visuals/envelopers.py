"""Bounded final-composition resources owned by the existing Renderer."""
import math
from pathlib import Path
import moderngl


class EnveloperStage:
    MAX_PIXELS = 1920*1080

    def __init__(self, ctx, vertices, vertex_shader):
        self.ctx=ctx;self.textures=[];self.targets=[];self.size=None
        self.last_time=None;self.last_state=None;self.valid=False;self.index=0
        self.allocations=0;self.resets=0
        self.program=ctx.program(vertex_shader=vertex_shader,
            fragment_shader=(Path(__file__).parent/'shaders/envelopers.frag').read_text())
        try:self.vao=ctx.simple_vertex_array(self.program,vertices,'in_position')
        except Exception:
            self.program.release();raise
        # ModernGL's copy_framebuffer copies the shared extent without scaling.
        # Sample normalized coordinates to retain the entire feedback image
        # when docking changes the viewport dimensions.
        self.resize_program=None
        try:
            self.resize_program=ctx.program(vertex_shader=vertex_shader,fragment_shader='''#version 330
uniform sampler2D previous;
uniform vec2 size;
out vec4 color;
void main(){color=texture(previous,gl_FragCoord.xy/size);}
''')
            self.resize_vao=ctx.simple_vertex_array(self.resize_program,vertices,'in_position')
        except Exception:
            if self.resize_program:self.resize_program.release()
            self.vao.release();self.program.release();raise

    def release_targets(self):
        for resource in self.targets+self.textures:resource.release()
        self.targets=[];self.textures=[];self.size=None;self.valid=False

    def resize(self,size):
        scale=min(1.,math.sqrt(self.MAX_PIXELS/max(1,size[0]*size[1])))
        bounded=tuple(max(1,int(v*scale)) for v in size)
        if bounded==self.size:return
        old_targets,old_textures=self.targets,self.textures
        was_valid=self.valid;old_index=self.index
        self.targets=[];self.textures=[]
        try:
            for _ in range(3):
                texture=self.ctx.texture(bounded,4,dtype='f1')
                self.textures.append(texture)
                texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
                texture.repeat_x=texture.repeat_y=False
                self.targets.append(self.ctx.framebuffer(color_attachments=[texture]))
        except Exception:
            for resource in self.targets+self.textures:resource.release()
            self.targets,self.textures=old_targets,old_textures
            raise
        try:
            if was_valid:
                self.resize_program['previous'].value=0
                self.resize_program['size'].value=tuple(float(v) for v in bounded)
                for destination,source in zip(self.targets,old_textures):
                    destination.use();self.ctx.viewport=(0,0,*bounded)
                    source.use(0);self.resize_vao.render(mode=moderngl.TRIANGLE_STRIP)
            else:
                for target in self.targets:target.clear()
        except Exception:
            for resource in self.targets+self.textures:resource.release()
            self.targets,self.textures=old_targets,old_textures
            raise
        for resource in old_targets+old_textures:resource.release()
        self.size=bounded;self.allocations+=1;self.valid=was_valid;self.index=old_index if was_valid else 0

    def reset(self):
        for target in self.targets:target.clear()
        self.valid=False;self.resets+=1;self.index=0

    def draw(self,scene_program,scene_vao,size,seconds,state,weights,audio,colors,audio_gains=None):
        self.resize(size)
        dt=0. if self.last_time is None else seconds-self.last_time
        if dt<0. or dt>.5 or self.last_state not in (None,state):self.reset()
        self.last_time=seconds;self.last_state=state
        self.targets[0].use();self.ctx.viewport=(0,0,*self.size)
        scene_program['u_resolution'].value=tuple(float(v) for v in self.size)
        scene_vao.render(mode=moderngl.TRIANGLE_STRIP)
        self.textures[0].use(0);self.textures[1+self.index].use(1)
        destination=2-self.index
        self.targets[destination].use()
        p=self.program
        p['scene'].value=0;p['history'].value=1;p['resolution'].value=tuple(float(v) for v in self.size)
        p['clock'].value=seconds;p['delta'].value=max(0.,min(.5,dt))
        mode=max(range(3),key=lambda i:weights[i])
        p['mode'].value=mode+1;p['strength'].value=min(.85,max(weights))
        p['energy'].value=max(0.,min(1.,.45*audio.scale+.35*audio.flux+.20*audio.sparkle))
        gains=audio_gains[mode] if audio_gains is not None else (1.,1.)
        gains=tuple(gains)+(1.,1.)
        p['audio_tuning_on'].value=int(any(g!=1. for g in gains[:2]));p['audio_gains'].value=gains[:2]
        p['history_valid'].value=int(self.valid and 0.<dt<=.5)
        for name,value in colors.items():
            if name in p:p[name].value=value
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)
        self.ctx.screen.use();self.ctx.viewport=(0,0,*size)
        self.textures[destination].use(0);p['mode'].value=0
        p['resolution'].value=tuple(float(v) for v in size)
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)
        self.index=1-self.index;self.valid=True
        scene_program['u_resolution'].value=tuple(float(v) for v in size)

    def release(self):
        self.release_targets();self.resize_vao.release();self.resize_program.release();self.vao.release();self.program.release()
