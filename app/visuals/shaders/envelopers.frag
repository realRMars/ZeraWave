#version 330
uniform sampler2D scene;
uniform sampler2D history;
uniform vec2 resolution;
uniform float clock, delta, strength, energy;
uniform int mode, history_valid;
uniform int u_prism_colors_on, u_digital_colors_on, u_memory_colors_on;
uniform vec3 u_prism_colors[2];
uniform vec3 u_digital_colors[2];
uniform vec3 u_memory_colors[3];
uniform int audio_tuning_on;
uniform vec2 audio_gains;
float tuned(float v,int role){float gain=audio_gains[role];if(audio_tuning_on==0)return v;if(gain<=-1.)return clamp(-1.-gain,0.,1.);return gain==1. ? v : clamp(v*gain,0.,1.);}
out vec4 fragColor;
vec3 current(vec2 uv){return texture(scene,clamp(uv,vec2(0.),vec2(1.))).rgb;}
float seed(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
    vec2 uv=gl_FragCoord.xy/resolution;
    vec3 base=current(uv),color=base;
    if(mode==0){fragColor=vec4(base,1.);return;}
    float amount=strength*(.28+.62*tuned(energy,0));
    if(mode==1){
        vec2 grid=vec2(12.,8.),cell=floor(uv*grid),local=fract(uv*grid)-.5;
        float id=seed(cell),turn=sin(clock*.23+id*6.283)*amount*.35;
        vec2 rotated=mat2(cos(turn),-sin(turn),sin(turn),cos(turn))*local;
        vec2 slide=vec2(sin(clock*.31+id*9.),cos(clock*.21+id*7.))*amount*.16;
        vec2 sampleUV=(cell+.5+rotated+slide)/grid;
        vec3 tintA=u_prism_colors_on==1?u_prism_colors[0]:vec3(.72,.90,1.);
        vec3 tintB=u_prism_colors_on==1?u_prism_colors[1]:vec3(1.,.72,.83);
        float edge=smoothstep(.42,.5,max(abs(local.x),abs(local.y)));
        vec3 rebuilt=current(sampleUV)*mix(vec3(1.),mix(tintA,tintB,id),edge*.18*amount);
        color=mix(base,rebuilt,strength);
    }else if(mode==2){
        float wave=.5+.5*sin(uv.x*8.+uv.y*5.-clock*.34);
        float region=smoothstep(.45,.72,wave);
        float block=mix(1.,12.+tuned(energy,1)*16.,region*amount);
        vec2 snapped=(floor(gl_FragCoord.xy/block)+.5)*block/resolution;
        vec3 source=current(snapped);
        // Ordered 4x4 pattern; fixed screen positions avoid temporal noise.
        ivec2 cell=ivec2(mod(gl_FragCoord.xy,4.));
        int rank[16]=int[16](0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5);
        float d=(float(rank[cell.x+cell.y*4])+.5)/16.-.5;
        float levels=mix(24.,6.,amount);
        vec3 quantized=clamp(floor(source*levels+d+.5)/levels,0.,1.);
        vec3 dark=u_digital_colors_on==1?u_digital_colors[0]:vec3(.64,.77,.94);
        vec3 light=u_digital_colors_on==1?u_digital_colors[1]:vec3(.93,.83,.61);
        vec3 tint=mix(dark,light,dot(source,vec3(.2126,.7152,.0722)));
        quantized*=mix(vec3(1.),tint,.30*amount);
        float scan=1.-.10*amount*step(.5,fract(gl_FragCoord.y*.25));
        color=mix(base,quantized*scan,region*strength);
    }else if(mode==3 && history_valid==1){
        vec2 drift=vec2(sin(clock*.17),cos(clock*.13))*delta*.023*(audio_tuning_on==0 ? amount : strength*(.28+.62*tuned(energy,1)));
        vec3 tintR=u_memory_colors_on==1?u_memory_colors[0]:vec3(1.,.83,.75);
        vec3 tintG=u_memory_colors_on==1?u_memory_colors[1]:vec3(.76,1.,.87);
        vec3 tintB=u_memory_colors_on==1?u_memory_colors[2]:vec3(.80,.84,1.);
        vec3 r=texture(history,clamp(uv+drift,vec2(0.),vec2(1.))).rgb;
        vec3 g=texture(history,clamp(uv-drift*.6,vec2(0.),vec2(1.))).rgb;
        vec3 b=texture(history,clamp(uv+drift.yx,vec2(0.),vec2(1.))).rgb;
        vec3 memory=vec3(r.r,g.g,b.b);
        // Time-based retention and tint approach: no per-frame decay constants.
        float retention=exp(-delta/(.00001+.18*amount));
        vec3 tint=(tintR*r.r+tintG*g.g+tintB*b.b)/max(.001,r.r+g.g+b.b);
        memory*=mix(vec3(1.),tint,1.-exp(-delta*.7));
        color=mix(base,memory,retention);
    }
    fragColor=vec4(clamp(color,0.,1.),1.);
}
