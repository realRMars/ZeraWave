"""Context-owned frame-only Aftershock depth ordering; authored GLSL fallback."""
import time
import moderngl

def _function(source, name):
    start=source.index(name+'(');start=source.rfind('\n',0,start)+1
    end=source.index('{',start)+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

class BlastOrderStage:
    @staticmethod
    def main_source(source):
        start=source.index('    vec3 cloudOrder=blast_cloud_order(clock);')
        end=source.index('    for(int j=0;j<8;j++) {',start)
        original=source[start:end].replace('    float cloudIds[8];float depths[8];','    float depths[8];')
        replacement='    float cloudIds[8];\n    if(u_blast_order_on==1){for(int i=0;i<8;i++)cloudIds[i]=texelFetch(u_blast_order,ivec2(i,0),0).x;}else{\n'+original+'    }\n'
        source=source[:start]+replacement+source[end:]
        return source.replace('#version 330','#version 330\nuniform sampler2D u_blast_order;\nuniform int u_blast_order_on;',1)

    def __init__(self,ctx,vertices,vertex_shader,source):
        self.ctx=ctx;self.program=self.texture=self.fbo=self.vao=None
        self.signature=None;self.metrics=dict(draws=0,reuses=0,last_cpu_ms=0.,maximum_cpu_ms=0.)
        fragment="""#version 330
uniform float u_drift_time;
uniform int u_event_blasts;
uniform vec4 u_blast_events[8];
out vec4 prepared;
"""+'\n'.join(_function(source,n) for n in ('hash','blast_site','blast_cloud_order'))+"""
void main(){
    int col=int(gl_FragCoord.x);vec3 cloudOrder=blast_cloud_order(u_drift_time);
    float ids[8],depths[8];
    for(int i=0;i<8;i++){
        float id=-1.;if(u_event_blasts==1)id=u_blast_events[i].y;else if(i<3)id=cloudOrder[i];
        ids[i]=id;depths[i]=id>=0. ? blast_site(id).y : -1000.;
    }
    if(u_event_blasts==1)for(int pass=0;pass<7;pass++)for(int i=0;i<7;i++)if(depths[i]<depths[i+1]){
        float t=depths[i];depths[i]=depths[i+1];depths[i+1]=t;t=ids[i];ids[i]=ids[i+1];ids[i+1]=t;
    }
    prepared=vec4(ids[col],0.,0.,1.);
}
"""
        try:
            self.program=ctx.program(vertex_shader=vertex_shader,fragment_shader=fragment)
            self.texture=ctx.texture((8,1),4,dtype='f4')
            self.texture.filter=(moderngl.NEAREST,moderngl.NEAREST)
            self.texture.repeat_x=self.texture.repeat_y=False
            self.fbo=ctx.framebuffer(color_attachments=[self.texture])
            self.vao=ctx.vertex_array(self.program,[(vertices,'2f','in_position')])
        except BaseException:
            self.release();raise

    def draw(self,program):
        began=time.perf_counter();signature=[]
        for name in self.program:
            if not name.startswith('u_'):continue
            uniform=self.program[name];value=program[name].value
            if name=='u_blast_events':value=value[:uniform.array_length]
            uniform.value=value
            signature.append((name,tuple(value) if isinstance(value,list) else value))
        signature=tuple(signature)
        if signature!=self.signature:
            target=self.ctx.fbo;viewport=self.ctx.viewport
            try:
                self.fbo.use();self.ctx.viewport=(0,0,8,1)
                self.vao.render(moderngl.TRIANGLE_STRIP)
            finally:
                target.use();self.ctx.viewport=viewport
            self.signature=signature;self.metrics['draws']+=1
        else:self.metrics['reuses']+=1
        self.texture.use(15);program['u_blast_order'].value=15;program['u_blast_order_on'].value=1
        elapsed=(time.perf_counter()-began)*1000
        self.metrics['last_cpu_ms']=elapsed;self.metrics['maximum_cpu_ms']=max(elapsed,self.metrics['maximum_cpu_ms'])

    def release(self):
        # Cleanup must not replace a creation/render failure with another error.
        for name in ('vao','fbo','texture','program'):
            resource=getattr(self,name,None)
            if resource is not None:
                try:resource.release()
                except Exception:pass
                setattr(self,name,None)
