#version 330
uniform vec2 u_resolution;
uniform float u_time,u_seed,u_impact;
uniform int u_form;
uniform vec3 u_motion;
uniform vec4 u_audio;
uniform vec2 u_treatments;
uniform vec4 u_form_audio_a[32];
uniform vec3 u_fractal_terrain[5],u_fractal_sky[3],u_fractal_stone[5],u_fractal_light[3];
uniform vec2 u_fractal_terrain_ranges[4],u_fractal_stone_ranges[4];
uniform vec3 u_fractal_honey[3],u_fractal_petals[6],u_lamellae_colors[3];
out vec4 fragColor;
const float PI=3.14159265359;
float audio(float value,int slot){float gain=u_form_audio_a[slot/4][slot%4];return gain<=-1. ? clamp(-1.-gain,0.,1.) : clamp(value*gain,0.,1.);}
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7))+u_seed*.013)*43758.5453);}
float noise(vec2 p){vec2 a=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(a),hash(a+vec2(1,0)),f.x),mix(hash(a+vec2(0,1)),hash(a+1.),f.x),f.y);}
float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<6;i++){v+=a*noise(p);p=mat2(.8,-.6,.6,.8)*p*2.03+vec2(9.2,7.1);a*=.5;}return v;}
mat2 rot(float a){return mat2(cos(a),sin(a),-sin(a),cos(a));}
vec3 gradient(float x,vec3 colors[5],vec2 ranges[4]){
 vec3 c=colors[0];for(int i=0;i<4;i++)c=mix(c,colors[i+1],smoothstep(ranges[i].x,max(ranges[i].x+.0001,ranges[i].y),x));return c;
}
// Reusable treatment: three nested local wave scales, bounded by authored amount.
vec2 recursive_pulse(vec2 p,float phase){
 float change=audio(u_audio.z,74),event=audio(u_impact,75);
 vec2 q=p;float a=.035*u_treatments.y;
 for(int i=0;i<3;i++){q+=a*vec2(sin(q.y*3.2+phase*.3),cos(q.x*4.1-phase*.26))*(.45+change*.55);
  float radius=length(q),wave=sin(radius*(10.+float(i)*7.)-phase*1.4);
  q+=normalize(q+vec2(.001))*wave*a*event*.8;a*=.45;}
 return q;
}
// Reusable material: fine mineral contour etching plus sparse granular glints.
vec3 lamellae(vec3 base,vec2 q,float surface,float shadow){
 float flux=audio(u_audio.z,72),spark=audio(u_audio.w,73);
 float ridge=.5+.5*sin(surface*(110.+flux*18.)+q.x*9.+fbm(q*5.)*3.);
 float line=pow(ridge,22.);
 float grains=pow(noise(q*210.),25.)*(.16+spark*.45);
 vec3 etch=mix(base,u_lamellae_colors[0],line*.38);
 etch+=u_lamellae_colors[1]*line*.12+u_lamellae_colors[2]*grains*shadow;
 return mix(base,etch,u_treatments.x);
}
vec3 landscape(vec2 p){
 float bass=audio(u_audio.x,64),move=audio(u_audio.y,65),flux=audio(u_audio.z,66),spark=audio(u_audio.w,67),hit=audio(u_impact,68);
 vec2 q=recursive_pulse(p,u_motion.x);float t=u_motion.x;
 vec3 sky=mix(u_fractal_sky[1]*.62,u_fractal_sky[0],smoothstep(-.04,.65,q.y));
 vec2 sun=q-vec2(.48+.06*sin(t*.05),.24);float sunDisc=1.-smoothstep(.041,.045,length(sun));
 sky+=u_fractal_sky[2]*(sunDisc*.78+exp(-dot(sun,sun)*16.)*.14);
 vec3 color=sky;
 for(int layer=0;layer<7;layer++){
  float depth=float(layer)/6.,scale=mix(1.7,3.5,depth);
  vec2 domain=vec2(q.x*scale+t*(.035+.065*depth),float(layer)*12.7+t*.022);
  float f=fbm(domain),ridged=1.-abs(2.*f-1.);
  float local=fbm(domain*2.7+vec2(t*.04,-t*.015));
  float height=.13-depth*.095+(ridged-.6)*(.19+.075*depth+.045*bass);
  height+=sin(q.x*5.+local*3.-t*.4)*(.013+.02*move)*(1.+depth);
  height+=sin(q.x*12.-u_time*1.2)*hit*.009*depth;
  float aa=max(fwidth(q.y-height),.001);float coverage=1.-smoothstep(-aa,aa,q.y-height);
  float gap=max(0.,height-q.y),value=clamp(.15+depth*.26+ridged*.22+gap*.38,0.,1.);
  vec3 rock=gradient(value,u_fractal_terrain,u_fractal_terrain_ranges);
  float ridges=pow(.5+.5*sin(gap*(55.+flux*25.)+local*4.-t*.12),10.);
  rock*=.54+.38*ridged+.12*ridges;
  float crest=exp(-gap*125.)*(.13+spark*.24);
  rock+=u_fractal_terrain[3]*crest;
  rock=lamellae(rock,domain,gap,.35+depth*.65);
  float river=exp(-pow((q.x-.13*sin(q.y*6.+t*.11)-.22*float(layer%2))*26.,2.))*smoothstep(.025,.12,gap);
  rock+=u_fractal_terrain[2]*river*(.055+.12*move)*depth;
  rock=mix(u_fractal_sky[1]*.54,rock,.30+depth*.70);
  color=mix(color,rock,coverage);
 }
 return color;
}
// Recursive frame architecture. Five scales carve connected apertures; bounded march.
vec2 atrium_distance(vec3 p,float bass,float flux){
 vec3 q=p;q.z=mod(q.z+2.4,4.8)-2.4;
 float beam=min(min(length(q.xy-vec2(1.45,.98))-.14,length(q.xy-vec2(-1.45,.98))-.14),abs(q.y+1.05)-.05);
 float portal=max(abs(q.z)-.16,abs(max(abs(q.x)/1.55,abs(q.y)/1.1)-1.)*.85-.07-.018*bass);
 float d=min(beam,portal),tag=0.;vec3 f=q;
 float scale=1.;
 for(int i=0;i<5;i++){
  f.xy=abs(f.xy)-vec2(.49,.38);f.xy=rot(.045*sin(u_motion.x*.08+float(i))*(.2+flux*.8))*f.xy;
  f*=2.15;scale*=2.15;
  float frame=max(abs(f.z)-.28,abs(max(abs(f.x),abs(f.y))- .72)-.08)/scale;
  if(frame<d){d=frame;tag=float(i)+1.;}
 }
 return vec2(d,tag);
}
vec3 recursion(vec2 p){
 float bass=audio(u_audio.x,64),flux=audio(u_audio.z,66),spark=audio(u_audio.w,67),hit=audio(u_impact,68);
 vec2 q=recursive_pulse(p,u_motion.x);
 vec3 eye=vec3(.28*sin(u_motion.x*.07),.17*cos(u_motion.x*.11),u_motion.x*.30);
 vec3 ray=normalize(vec3(q.x*1.1,q.y*1.1,1.));ray.xy=rot(.035*sin(u_motion.x*.045))*ray.xy;
 float distance=0.,tag=0.;bool found=false;
 for(int i=0;i<72;i++){
  vec2 field=atrium_distance(eye+ray*distance,bass,flux);
  if(field.x<.0015){found=true;tag=field.y;break;}
  distance+=max(.001,field.x*.78);if(distance>24.)break;
 }
 vec3 color=u_fractal_light[2]*(.50+.12*fbm(q*4.));
 if(found){
  vec3 point=eye+ray*distance;float e=.003;
  vec3 normal=normalize(vec3(atrium_distance(point+vec3(e,0,0),bass,flux).x-atrium_distance(point-vec3(e,0,0),bass,flux).x,
    atrium_distance(point+vec3(0,e,0),bass,flux).x-atrium_distance(point-vec3(0,e,0),bass,flux).x,
    atrium_distance(point+vec3(0,0,e),bass,flux).x-atrium_distance(point-vec3(0,0,e),bass,flux).x));
  float lighting=.32+.92*max(0.,dot(normal,normalize(vec3(-.35,.7,-.4))));
  float strata=fbm(point.xy*1.5+point.z*.04);color=gradient(.15+lighting*.58+strata*.14,u_fractal_stone,u_fractal_stone_ranges)*lighting;
  vec3 light=mix(u_fractal_light[0],u_fractal_light[1],.5+.5*sin(tag*1.7+point.z*.3));
  float seam=pow(.5+.5*cos(point.z*8.+tag*2.),20.);
  float pulse=pow(.5+.5*cos(point.z*2.8-u_motion.x*2.),18.)*hit;
  color+=light*(seam*(.12+spark*.32)+pulse*.28);
  color=lamellae(color,point.xy+point.z*.17,strata,.35+lighting*.65);
  color=mix(color,u_fractal_light[2],1.-exp(-distance*.075));
 }
 // Nested portal rings reveal depth while preserving negative space.
 float arch=pow(.5+.5*cos(length(q*vec2(.7,1.))*18.-u_motion.x*.5),30.)*exp(-dot(q,q)*6.);
 color+=u_fractal_light[0]*arch*(.014+hit*.018);
 return color;
}
vec4 hex_cell(vec2 p){
 vec2 scale=vec2(1.,1.7320508),a=mod(p,scale)-scale*.5,b=mod(p-scale*.5,scale)-scale*.5;
 vec2 local=dot(a,a)<dot(b,b) ? a : b;
 // Canonical lattice centers prevent float cancellation from changing a cell
 // seed across its pixels as the garden turns and grows.
 vec2 center=round((p-local)/vec2(.5,.8660254))*vec2(.5,.8660254);
 return vec4(local,center);
}
float hex_radius(vec2 p){p=abs(p);return max(p.x,dot(p,normalize(vec2(1.,1.7320508))));}
vec3 growth(vec2 p){
 float bass=audio(u_audio.x,64),move=audio(u_audio.y,65),flux=audio(u_audio.z,66),spark=audio(u_audio.w,67),hit=audio(u_impact,68);
 vec2 q=recursive_pulse(p,u_motion.x);q.y=q.y*1.3-.06;
 q=rot(.08*sin(u_motion.x*.05))*q;
 float epoch=floor(u_motion.y),phase=fract(u_motion.y),maturity=smoothstep(.12,.67,phase)*(1.-smoothstep(.90,1.,phase));
 float scale=mix(6.8,5.8,maturity);vec4 cell=hex_cell(q*scale);vec2 local=cell.xy;
 float id=hash(cell.zw+epoch*17.),stagger=.15*hash(cell.zw+5.3);
 float bloom=smoothstep(stagger,stagger+.56,maturity);
 float radius=length(local),angle=atan(local.y,local.x);
 float hex=hex_radius(local),rim=exp(-abs(hex-.42)*95.);
 float quiet_wax=.48+.25*fbm(cell.zw+local*2.+u_motion.x*.06);
 vec3 wax=mix(u_fractal_honey[1],u_fractal_honey[2],.23+.15*sin(local.y*8.+u_motion.x*.12+id*6.));
 vec3 honey=mix(u_fractal_honey[0],wax*(.80+.20*quiet_wax),smoothstep(.018,.08,.42-hex));
 honey+=u_fractal_honey[2]*rim*(.28+.23*spark)*(.7+.3*sin(u_time*.65+id*9.));
 float twist=.12*sin(u_motion.x*.07+id*6.)*(.3+flux*.7);
 float petals=6.+2.*floor(id*4.);float petal_wave=pow(.5+.5*cos((angle+twist)*petals),.7);
 float petal_length=mix(.13,.52,bloom)*(.86+.12*bass+.05*hit);
 float boundary=petal_length*(.55+.45*petal_wave);
 float aa=max(fwidth(radius),.003);
 float flower=1.-smoothstep(boundary-aa,boundary+aa,radius);
 float center=1.-smoothstep(.105,.125,radius);
 int pigment=int(mod(floor(id*6.)+epoch,6.));
 vec3 petal=u_fractal_petals[pigment]*(.36+.64*smoothstep(0.,.37,radius));
 float veins=pow(.5+.5*cos(angle*petals*3.+radius*32.+id*5.),12.);
 petal*=.72+.22*petal_wave+.14*veins;
 float pollen=pow(noise(local*185.+cell.zw),25.)*(.04+.23*spark);
 petal+=u_fractal_honey[2]*pollen;
 petal=lamellae(petal,local+cell.zw,radius+veins*.04,.7);
 float seed=pow(.5+.5*sin(angle*29.+radius*230.),5.);
 vec3 core=mix(u_fractal_honey[0],u_fractal_honey[1],.20+.38*seed);
 vec3 floral=mix(petal,core,center);
 floral*=flower;
 float honey_share=1.-bloom*flower;
 vec3 color=honey*honey_share+floral*bloom;
 float stem=exp(-pow(local.x*35.,2.))*smoothstep(.06,.38,-local.y)*bloom*(1.-flower);
 color+=u_fractal_petals[3]*stem*.12;
 float wave=exp(-pow(radius-.22-.05*sin(u_time*1.4),2.)*500.)*hit*bloom;
 color+=u_fractal_petals[pigment]*wave*.10;
 color*=.77+.23*exp(-dot(p,p)*.7);
 return color;
}
void main(){
 vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;
 vec3 color=u_form==41 ? landscape(p) : u_form==42 ? recursion(p) : growth(p);
 float peak=max(color.r,max(color.g,color.b));color/=1.+peak*.35;
 color*=1.-.12*smoothstep(.2,1.2,length(p));fragColor=vec4(max(color,vec3(0.)),1.);
}
