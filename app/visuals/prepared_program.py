"""Prepared integrated shader, retained declared uniforms and owned GPU resources.

The NVIDIA policy limits inlining in the measured driver to reduce compiler
memory and time. Other vendors use their existing compiler policy. This is one
program: every Main endpoint and pair is ready before playback, with no family
compile on entry. Uniforms pruned by the driver retain values for auxiliary
passes; undeclared names still fail.
"""
import re
import hashlib
import time


class UniformState:
    def __init__(self,pool,name,length):
        self.pool,self.name,self.array_length=pool,name,length
        self.stored=None
    @property
    def value(self):
        if self.stored is not None:return self.stored
        if self.name in self.pool.active_uniforms:return self.pool.active_uniforms[self.name].value
        return 0
    @value.setter
    def value(self,value):
        self.stored=value
        self.upload()
    def upload(self):
        uniform=self.pool.active_uniforms.get(self.name)
        if self.stored is None or uniform is None:return
        value=self.stored
        if self.array_length>1 and isinstance(value,(tuple,list)):
            value=value[:uniform.array_length]
        uniform.value=value


class PreparedProgram:
    def __init__(self,ctx,vertices,vertex_shader,source):
        import moderngl
        self.ctx=ctx;self.programs={};self.vaos={};self.current=None;self.current_key=None;self.metrics=[]
        self.uniforms={};self.active_uniforms={}
        for declaration in re.findall(r'\buniform\s+\w+\s+([^;]+);',source):
            for item in declaration.split(','):
                match=re.fullmatch(r'\s*(\w+)(?:\[(\d+)\])?\s*',item)
                if not match:raise ValueError('Invalid uniform declaration: '+item)
                name,length=match.groups();self.uniforms[name]=UniformState(self,name,int(length or 1))
        try:
            if 'NVIDIA' in ctx.info.get('GL_VENDOR',''):
                source=source.replace('#version 330','#version 330\n#pragma optionNV(inline 100)',1)
            began=time.perf_counter();program=ctx.program(vertex_shader=vertex_shader,fragment_shader=source)
            self.programs[(0,)]=program;self.vaos[(0,)]=ctx.simple_vertex_array(program,vertices,'in_position')
            self.metrics=[dict(program='integrated',compile_seconds=time.perf_counter()-began,nvidia_inline_limit=100 if 'NVIDIA' in ctx.info.get('GL_VENDOR','') else None,shader_sha256=hashlib.sha256(source.encode()).hexdigest())]
            self.preparation_seconds=time.perf_counter()-began;self.activate((0,))
        except BaseException:
            self.release();raise

    def activate(self,key):
        key=tuple(sorted(set(key)))
        if key==self.current_key:return
        if key not in self.programs:raise RuntimeError('Unprepared program: '+str(key))
        self.current=self.programs[key];self.current_key=key
        self.active_uniforms={name:self.current[name] for name in self.current}
        for uniform in self.uniforms.values():uniform.upload()

    def __getitem__(self,name):return self.uniforms[name]
    def __contains__(self,name):return name in self.uniforms
    def __iter__(self):return iter(self.uniforms)
    def render(self,mode=5,**kwargs):self.vaos[self.current_key].render(mode=mode,**kwargs)
    def prewarm(self):
        if getattr(self,'prewarmed',False):return
        self.prewarmed=True;key=self.current_key;resolution=self['u_resolution'].value
        began=time.perf_counter();target=self.ctx.simple_framebuffer((32,18))
        try:
            target.use();self.ctx.viewport=(0,0,32,18);self['u_resolution'].value=(32.,18.)
            for candidate in self.programs:
                self.activate(candidate);self.render()
            self.ctx.finish()
        finally:
            target.release();self['u_resolution'].value=resolution;self.activate(key)
            self.ctx.screen.use();self.ctx.viewport=(0,0,int(resolution[0]),int(resolution[1]))
        self.prewarm_seconds=time.perf_counter()-began
    def release(self):
        for vao in self.vaos.values():vao.release()
        for program in self.programs.values():program.release()
        self.vaos={};self.programs={};self.active_uniforms={}


class PreparedVao:
    def __init__(self,pool):self.pool=pool;self.before_render=None
    def render(self,**kwargs):
        if self.before_render is not None:self.before_render()
        self.pool.render(**kwargs)
    def release(self):pass # Pool owns every program and VAO exactly once.
