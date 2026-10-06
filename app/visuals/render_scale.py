"""Explicit opt-in render scale within the existing renderer and stages."""
import moderngl
from visualizer_resolution import validate,internal_size,fit_rect


class ScaledContext:
    def __init__(self,context,scale):
        if scale not in (1.,.75,.5):raise ValueError('Render scale must be 1, .75 or .5')
        self.raw=context;self.scale=scale;self.target=None;self.scale_texture=None;self.scale_fbo=None
        self.present_program=None;self.present_vao=None;self.internal=None;self.output=None
        self.policy=None;self.error=None;self.texture_size=None;self.resolution_serial=0

    @property
    def resolution_limit(self):
        limits=[self.raw.info.get('GL_MAX_TEXTURE_SIZE',16384),self.raw.info.get('GL_MAX_RENDERBUFFER_SIZE',16384)]
        limits.extend(self.raw.info.get('GL_MAX_VIEWPORT_DIMS',(16384,16384)))
        return min(16384,*limits)

    def _prepare(self,policy,size,history_resize=None):
        internal=internal_size(policy,size,self.scale)
        validate({'mode':'fixed','size':list(internal)},self.resolution_limit)
        offscreen=bool(policy and policy['mode']=='fixed') or (policy is None and self.scale!=1.)
        texture=fbo=None
        try:
            if offscreen and (internal!=self.texture_size or self.scale_fbo is None):
                texture=self.raw.texture(internal,4,dtype='f2')
                texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
                texture.repeat_x=texture.repeat_y=False
                fbo=self.raw.framebuffer(color_attachments=(texture,))
            if history_resize is not None:history_resize(internal)
        except Exception:
            if fbo is not None:fbo.release()
            if texture is not None:texture.release()
            raise
        if fbo is not None:
            old_fbo,old_texture=self.scale_fbo,self.scale_texture
            self.scale_fbo,self.scale_texture=fbo,texture;self.texture_size=internal
            if old_fbo is not None:old_fbo.release();old_texture.release()
        self.internal=internal;self.output=size
        return offscreen

    def configure(self,policy,size,history_resize=None):
        policy=validate(policy,self.resolution_limit)
        try:self._prepare(policy,size,history_resize)
        finally:
            self.raw.screen.use();self.raw.viewport=(0,0,*size)
        self.policy=policy;self.error=None;self.target=None
        self.raw.screen.use();self.raw.viewport=(0,0,*size)

    @property
    def screen(self):return self.target if self.target is not None else self.raw.screen

    def __getattr__(self,name):return getattr(self.raw,name)

    @property
    def viewport(self):return self.raw.viewport
    @viewport.setter
    def viewport(self,value):self.raw.viewport=value

    def begin(self,size):
        offscreen=self._prepare(self.policy,size)
        self.target=self.scale_fbo if offscreen else None
        self.screen.use()
        return self.internal

    def present(self,vertices,vertex_shader):
        if self.target is None:return
        if self.present_program is None:
            self.present_program=self.raw.program(vertex_shader=vertex_shader,fragment_shader='''#version 330
uniform sampler2D image;uniform vec2 image_origin,image_size;out vec4 fragColor;
void main(){fragColor=texture(image,(gl_FragCoord.xy-image_origin)/image_size);}''')
            self.present_vao=self.raw.simple_vertex_array(self.present_program,vertices,'in_position')
        self.target=None;self.raw.screen.use();self.raw.viewport=(0,0,*self.output)
        self.raw.screen.clear(0.,0.,0.,1.)
        rect=fit_rect(self.internal,self.output) if self.policy else (0,0,*self.output)
        self.raw.viewport=rect
        self.scale_texture.use(0);self.present_program['image'].value=0
        self.present_program['image_origin'].value=rect[:2];self.present_program['image_size'].value=rect[2:]
        self.present_vao.render(moderngl.TRIANGLE_STRIP)
        self.raw.viewport=(0,0,*self.output)

    def release(self):
        self.target=None
        for resource in (self.present_vao,self.present_program,self.scale_fbo,self.scale_texture):
            if resource is not None:resource.release()
        self.present_vao=self.present_program=self.scale_fbo=self.scale_texture=None
        self.raw.release()
