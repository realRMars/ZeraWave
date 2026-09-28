#version 330
uniform sampler2D history;
uniform float clock;
uniform vec4 audio;
out vec4 field;
const float dt=1./60.;
void main(){
    vec2 uv=gl_FragCoord.xy/512.;
    vec2 p=uv*2.-1.;
    vec2 velocity=vec2(0.);
    for(int i=0;i<5;i++){
        float n=float(i);
        vec2 center=.52*vec2(sin(n*2.41+clock*.09),cos(n*1.83-clock*.07));
        vec2 d=p-center;
        velocity+=vec2(-d.y,d.x)*(.025+.008*n)/(dot(d,d)+.10)*(mod(n,2.)*2.-1.);
    }
    velocity+=.025*vec2(sin(p.y*7.+clock*.17),cos(p.x*6.-clock*.13));
    float rate=.4+audio.x*1.5+audio.y*1.2;
    vec2 source=uv-velocity*dt*rate;
    vec4 old=texture(history,source);
    vec2 texel=vec2(1./512.,0.);
    vec2 gradient=vec2(texture(history,source+texel).r-texture(history,source-texel).r,
        texture(history,source+texel.yx).r-texture(history,source-texel.yx).r);
    old=mix(old,texture(history,source+vec2(-gradient.y,gradient.x)*.004),.35);
    vec2 ink=old.rg*exp(-dt*vec2(.24,.31));
    for(int i=0;i<4;i++){
        float n=float(i);
        float phase=clock*(.12+.019*n)+n*1.71;
        vec2 center=.62*vec2(sin(phase),cos(phase*.81+n));
        vec2 d=p-center;
        vec2 axis=vec2(cos(phase*1.3),sin(phase*1.3));
        float along=dot(d,axis), across=dot(d,vec2(-axis.y,axis.x));
        float seed=exp(-across*across/ .00025-along*along/.032);
        float pulse=.35+.65*pow(.5+.5*sin(clock*.5+n*2.),2.);
        ink+=dt*seed*pulse*(.8+audio.x*1.2+audio.w*2.)*vec2(.65+.35*sin(n*2.),.65+.35*cos(n*3.));
    }
    float edge=smoothstep(0.,.07,uv.x)*smoothstep(0.,.07,uv.y)*smoothstep(0.,.07,1.-uv.x)*smoothstep(0.,.07,1.-uv.y);
    field=vec4(clamp(ink,0.,1.)*edge,0.,1.);
}
