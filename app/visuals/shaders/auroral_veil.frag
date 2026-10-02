#version 330
uniform vec2 u_resolution;
uniform float u_time,u_star_time,u_scale,u_flux,u_sparkle,u_impact,u_drift_time,u_veil_amount;
uniform vec3 u_plasma_details,u_plasma_sky[2],u_auroral_curtains[2],u_auroral_veil[6],u_veil_authored[6];
uniform int u_plasma_sky_on,u_auroral_curtains_on,u_auroral_veil_on,u_veil_layers;
uniform vec4 u_veil_motion,u_veil_events[4];
out vec4 frag;
vec3 color_tint(vec3 authored, int enabled, vec3 tint) {
    return enabled == 1 ? authored * tint : authored;
}
float plasma_seed(vec2 p) {
    return fract(sin(dot(mod(p,127.),vec2(41.73,17.91)))*4738.13);
}
float plasma_sky_line(vec2 p,vec2 a,vec2 b) {
    vec2 d=b-a;float f=clamp(dot(p-a,d)/max(dot(d,d),1e-8),0.,1.);
    return length(p-a-f*d);
}
vec3 plasma_stars(vec2 p,int form) {
    float t=u_star_time,drive=clamp(.45*u_scale+.55*u_flux,0.,1.);
    vec2 sky=p;
    if(form==0) {
        // A bounded lens-inspired inverse map bends the remote sky around the core.
        float r2=dot(p,p);
        sky*=1.+(.030+.012*u_scale)/(r2+.045);
        float bend=.08*sin(t*.11)/(1.+r2*8.);
        sky=mat2(cos(bend),sin(bend),-sin(bend),cos(bend))*sky;
    } else if(form==2) {
        // Small coherent scintillation waves travel behind the emitting curtains.
        sky+=vec2(sin(p.y*7.+t*.23),sin(p.x*5.-t*.18))*.008;
    }
    vec3 light=vec3(0.);
    for(int layer=0;layer<2;layer++) {
        float depth=float(layer),angle=t*(.020+depth*.012);
        mat2 rotation=mat2(cos(angle),sin(angle),-sin(angle),cos(angle));
        vec2 q=rotation*sky*(24.+depth*14.)+vec2(t*.11,t*.035)*(1.+depth*.6);
        vec2 cell=floor(q);
        for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++) {
            vec2 id=cell+vec2(x,y),salt=id+depth*31.;
            float seed=plasma_seed(salt);
            if(seed<.87)continue;
            vec2 star=id+vec2(plasma_seed(salt+7.),plasma_seed(salt+19.));
            vec2 d=q-star;
            vec2 tangent=normalize(vec2(-sky.y,sky.x)+vec2(.10,.035));
            float trail=(.035+.19*drive)*(1.-depth*.25);
            float along=clamp(dot(d,tangent),0.,trail);
            vec2 offset=d-tangent*along;
            float size=.024+.023*seed;
            float point=exp(-dot(offset,offset)/(size*size))*(1.-.7*along/max(trail,.001));
            float halo=exp(-length(d)*12.)*.07;
            float twinkle=.65+.35*sin(t*(.8+seed)+seed*31.);
            if(form==2)twinkle*=.7+.3*sin(star.x*.25+star.y*.17-t*.65);
            vec3 hue=mix(vec3(.25,.52,.85),vec3(.85,.52,.30),seed);
            if(form==2)hue=mix(hue,vec3(.42,.35,.85),.35);
            light+=color_tint(hue,u_plasma_sky_on,u_plasma_sky[1])*(point+halo)*(.35+.45*u_sparkle+.25*u_impact)*twinkle*(1.-depth*.35);
        }
    }
    if(form==1) {
        // Sparse, fixed three-star asterisms illuminate in sequence on discharges.
        float angle=t*.020;
        vec2 q=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*sky*4.+vec2(t*.018,t*.006);
        vec2 cell=floor(q),f=fract(q);float seed=plasma_seed(cell+53.);
        if(seed>.67) {
            vec2 a=vec2(.18,.20)+.10*vec2(sin(seed*31.),cos(seed*17.));
            vec2 b=vec2(.76,.39)+.09*vec2(cos(seed*23.),sin(seed*41.));
            vec2 c=vec2(.40,.78)+.08*vec2(sin(seed*13.),cos(seed*29.));
            float points=min(length(f-a),min(length(f-b),length(f-c)));
            float line=min(plasma_sky_line(f,a,b),plasma_sky_line(f,b,c));
            float wake=pow(.5+.5*sin(t*.8+seed*29.),10.);
            float charge=(.06+.24*u_impact)*wake;
            vec3 hue=mix(vec3(.16,.40,.65),vec3(.65,.24,.43),seed);
            light+=color_tint(hue,u_plasma_sky_on,u_plasma_sky[1])*(exp(-points*points/.00015)*(.5+.5*u_sparkle)
                +exp(-line*line/.000045)*charge);
        }
    }
    return light;
}
vec3 veil_pigment(int role){return u_auroral_veil_on==1?u_auroral_veil[role]:u_veil_authored[role];}
vec3 auroral_veil(vec2 p) {
    float energy=u_veil_motion.x,high=u_veil_motion.y,phase=u_veil_motion.z;
    vec3 night=veil_pigment(0),hemColor=veil_pigment(1),body=veil_pigment(2),tip=veil_pigment(3),hot=veil_pigment(4),land=veil_pigment(5);
    vec3 color=color_tint(night,u_plasma_sky_on,u_plasma_sky[0])*(.50+.25*max(0.,p.y+.5));
    color+=plasma_stars(p,2)*u_plasma_details.z*.65;
    vec3 memoryLight=vec3(0.);
    // Six ordered thin sheets: a broad folded hem and rising, wavering emitting fibers.
    // Material-space ripples select one sheet and travel outward while their colored wakes linger.
    for(int layer=0;layer<u_veil_layers;layer++) {
        float id=float(layer),depth=1.+id*.16;
        float drift=phase*(.055+.011*id);
        float x=p.x*depth+.13*sin(drift*.31+id*1.7);
        float hem=-.29+id*.052+.095*sin(x*(2.4+id*.12)+drift+id*.81)+.036*sin(x*7.1-drift*.62+id*2.);
        float height=p.y-hem;
        if(height<-.065)continue;
        float shear=.09*sin(height*3.+drift*.73+id)+.035*sin(x*6.-height*2.+drift*.28);
        float material=x+shear;
        float ripple=0.,wake=0.,wrinkle=0.;
        for(int i=0;i<4;i++) {
            vec4 event=u_veil_events[i];float age=u_drift_time-event.x;
            if(age<0. || age>6. || abs(mod(event.y,6.)-id)>.1)continue;
            float anchor=(event.w-.5)*1.48;float distance=abs(material-anchor),radius=age*.27;
            float front=exp(-pow((distance-radius)/.056,2.))*exp(-age*.42);
            float vertical=exp(-pow((height-(age*.13+.065))/.18,2.));
            float power=event.z*u_veil_amount;
            ripple+=front*power*(.35+.65*vertical);
            wake+=power*exp(-max(0.,age-distance/.27)*.9)*(1.-smoothstep(radius-.025,radius+.025,distance))*exp(-height*3.5)*.28;
            wrinkle+=power*front*.018*sin(age*8.+height*14.);
        }
        material+=wrinkle;height+=wrinkle*.65;
        float fiber=.30+.70*pow(.5+.5*sin(material*(122.+id*13.)+height*7.-phase*(.65+.10*id)),4.);
        float fine=.70+.30*pow(.5+.5*sin(material*(291.+id*11.)-height*5.+phase*.30),6.);
        float folds=.50+.50*pow(.5+.5*sin(material*(10.+id*.35)-height*.8+drift),2.);
        float rising=exp(-max(0.,height)*(2.6+.12*id));
        float edge=smoothstep(-.035,.022,height);
        float density=edge*rising*(.13+.52*fiber*fine)*folds*(.66+.40*energy)*u_plasma_details.x;
        float lower=exp(-pow(height/.027,2.))*(.30+.70*folds);
        float travel=.5+.5*sin(height*8.-phase*.85+material*.9+id*.92);
        float crest=pow(travel,3.);
        vec3 gradient=mix(hemColor,body,smoothstep(.025,.29,height));
        gradient=mix(gradient,tip,smoothstep(.24,.78,height)*(.60+.30*travel));
        gradient=mix(gradient,hemColor,crest*(.025+.13*energy)*exp(-height*2.));
        vec3 emission=color_tint(gradient,u_auroral_curtains_on,u_auroral_curtains[0])*(.52+.40*energy+.18*high*fine);
        float through=exp(-density*(1.8+energy*.45));
        color=color*through+emission*(1.-through);
        color+=color_tint(hemColor,u_auroral_curtains_on,u_auroral_curtains[0])*lower*(.018+.025*energy)*u_plasma_details.x;
        memoryLight+=color_tint(mix(hot,tip,.15),u_auroral_curtains_on,u_auroral_curtains[1])*(ripple*(.29+.45*fiber)*rising+lower*ripple*.24+wake*.40)*edge*u_plasma_details.y;
        color+=tip*crest*fiber*rising*high*.035*u_plasma_details.z;
    }
    // A velvet horizon anchors the immense luminous sheets, separate from charged hem colors.
    color+=memoryLight;
    float ridge=-.415+.018*sin(p.x*9.+.7)+.012*sin(p.x*23.)+.008*sin(p.x*47.+2.);
    float horizon=1.-smoothstep(ridge-.004,ridge+.004,p.y);
    vec3 ground=land*(.045+.11*exp(-(p.y+.5)*7.));
    color=mix(color,ground,horizon);
    return color/(1.+color*.25);
}

void main(){vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;frag=vec4(auroral_veil(p),1.);}
