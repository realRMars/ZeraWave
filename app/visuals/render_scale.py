"""Explicit opt-in render scale within the existing renderer and stages."""
import moderngl


class ScaledContext:
    def __init__(self,context,scale):
        if scale not in (1.,.75,.5):raise ValueError('Render scale must be 1, .75 or .5')
        self.raw=context;self.scale=scale;self.target=None;self.scale_texture=None;self.scale_fbo=None
        self.present_program=None;self.present_vao=None;self.internal=None;self.output=None

    @property
    def screen(self):return self.target if self.target is not None else self.raw.screen

    def __getattr__(self,name):return getattr(self.raw,name)

    @property
    def viewport(self):return self.raw.viewport
    @viewport.setter
    def viewport(self,value):self.raw.viewport=value

    def begin(self,size):
        self.output=size
        if self.scale==1.:self.internal=size;return size
        internal=tuple(max(1,round(v*self.scale)) for v in size)
        if internal!=self.internal or self.scale_fbo is None:
            if self.scale_fbo:self.scale_fbo.release();self.scale_texture.release()
            self.scale_texture=self.raw.texture(internal,4,dtype='f2')
            self.scale_texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
            self.scale_texture.repeat_x=self.scale_texture.repeat_y=False
            self.scale_fbo=self.raw.framebuffer(color_attachments=(self.scale_texture,))
            self.internal=internal
        self.target=self.scale_fbo;self.scale_fbo.use()
        return internal

    def present(self,vertices,vertex_shader):
        if self.target is None:return
        if self.present_program is None:
            self.present_program=self.raw.program(vertex_shader=vertex_shader,fragment_shader='''#version 330
uniform sampler2D image;uniform vec2 output_size;out vec4 fragColor;
void main(){fragColor=texture(image,gl_FragCoord.xy/output_size);}''')
            self.present_vao=self.raw.simple_vertex_array(self.present_program,vertices,'in_position')
        self.target=None;self.raw.screen.use();self.raw.viewport=(0,0,*self.output)
        self.scale_texture.use(0);self.present_program['image'].value=0;self.present_program['output_size'].value=self.output
        self.present_vao.render(moderngl.TRIANGLE_STRIP)

    def release(self):
        self.target=None
        for resource in (self.present_vao,self.present_program,self.scale_fbo,self.scale_texture):
            if resource is not None:resource.release()
        self.present_vao=self.present_program=self.scale_fbo=self.scale_texture=None
        self.raw.release()
