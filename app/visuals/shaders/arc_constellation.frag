#version 330
uniform vec2 u_resolution;
uniform float u_time,u_star_time,u_scale,u_flux,u_sparkle,u_impact;
uniform vec3 u_plasma_details,u_plasma_sky[2],u_arcs_charge[3],u_arcs_asterism[6];
uniform int u_plasma_sky_on,u_arcs_charge_on,u_arcs_asterism_on;
uniform sampler2D u_arc_paths;
uniform vec4 u_arc_bounds[12],u_arc_groups[48],u_arc_nodes[9],u_arc_shape[9],u_arc_links[12],u_arc_motion;
uniform ivec2 u_arc_counts;
uniform vec3 u_arc_authored[6];
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
vec3 arc_pigment(int role) {
    return u_arcs_asterism_on==1?u_arcs_asterism[role]:u_arc_authored[role];
}
vec3 arc_constellation(vec2 p) {
    vec3 ground=arc_pigment(0),glass=arc_pigment(1),metal=arc_pigment(2),charge=arc_pigment(3),residue=arc_pigment(4),dust=arc_pigment(5);
    float energy=u_arc_motion.x,high=u_arc_motion.y,phase=u_arc_motion.z;
    vec3 color=color_tint(ground,u_plasma_sky_on,u_plasma_sky[0])*(.45+.30*exp(-dot(p,p)*3.))+plasma_stars(p,1)*u_plasma_details.z*.42;
    float solidDepth=100.;vec3 emission=vec3(0.);
    // Authored etched stormglass junctions, three distinct silhouettes and varied proportions.
    // Billboard facets deliberately avoid another expensive per-pixel convex solid trace.
    for(int i=0;i<u_arc_counts.x;i++) {
        vec4 node=u_arc_nodes[i],shape=u_arc_shape[i];vec2 q=(p-node.xy)/node.z;
        float angle=shape.y; q=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*q;q.y/=shape.x;
        if(any(greaterThan(abs(q),vec2(1.65))))continue;
        float facet=abs(q.x)*1.03+abs(q.y);
        if(shape.w>.5 && shape.w<1.5)facet=max(abs(q.x)*1.43,abs(q.x)*.77+abs(q.y));
        if(shape.w>1.5)facet=max(abs(q.y)*1.15,abs(q.x)+abs(q.y)*.62);
        float edge=exp(-abs(facet-1.)*55.),etch=exp(-abs(facet-.73)*90.);
        float halo=exp(-max(0.,facet-1.)*15.)*smoothstep(.8,1.,facet);
        emission+=dust*halo*(.015+.035*high)*u_plasma_details.z;
        if(facet<1.02 && node.w<solidDepth) {
            solidDepth=node.w;
            float center=exp(-dot(q,q)*35.);
            float enamel=.52+.25*q.x-.18*q.y+.12*sign(q.x*q.y);
            float aperture=1.-smoothstep(.13,.30,length(q*vec2(1.,1.35)));
            vec3 body=glass*enamel*(.65+.40*energy);
            body*=1.-aperture*.90;
            float sector=float(i)*1.71;
            float engraving=exp(-abs(q.x*.7+q.y*.32+.13*sin(q.y*12.+sector))*95.)*smoothstep(.30,.56,length(q));
            float cap=smoothstep(.78,.99,facet)*(1.-smoothstep(.08,.25,min(abs(q.x),abs(q.y))));
            body=mix(body,metal*(.4+.36*max(0.,q.y)),cap*.9);
            body+=metal*(edge*.50+etch*.23+engraving*.18)*u_plasma_details.x;
            body+=dust*exp(-abs(q.x+q.y*.38+.36)*48.)*.13*(1.-aperture);
            body+=residue*(center*.16+etch*.12)*shape.z*u_plasma_details.y;
            body+=charge*center*(.30+.32*energy+shape.z*.75)*u_plasma_details.y;
            float star=(exp(-abs(q.x)*110.)*exp(-abs(q.y)*7.)+exp(-abs(q.y)*110.)*exp(-abs(q.x)*7.));
            body+=charge*star*(.038+.18*shape.z)*u_plasma_details.y;
            color=color_tint(body,u_arcs_charge_on,u_arcs_charge[0]);
            // Small engraved clock marks make individual node charge legible without a global flash.
            float dots=exp(-pow((q.y+.35)/.028,2.))*pow(.5+.5*cos(q.x*42.),18.)*(1.-smoothstep(.4,.6,abs(q.x)));
            color+=residue*dots*(.025+.10*shape.z)*u_plasma_details.z;
        }
    }
    for(int row=0;row<u_arc_counts.y;row++) {
        vec4 bounds=u_arc_bounds[row];if(any(lessThan(p,bounds.xy-.045))||any(greaterThan(p,bounds.zw+.045)))continue;
        float nearest=100.,along=0.;
        for(int group=0;group<4;group++) {
            vec4 box=u_arc_groups[row*4+group];if(any(lessThan(p,box.xy-.045))||any(greaterThan(p,box.zw+.045)))continue;
            vec4 a=texelFetch(u_arc_paths,ivec2(group*4,row),0);
            for(int j=1;j<=4;j++) {
                vec4 b=texelFetch(u_arc_paths,ivec2(group*4+j,row),0);vec2 delta=b.xy-a.xy;
                float f=clamp(dot(p-a.xy,delta)/max(dot(delta,delta),1e-10),0.,1.);
                float depth=1./mix(a.z,b.z,f),distance=length(p-mix(a.xy,b.xy,f));
                if(depth<solidDepth+.004 && distance<nearest){nearest=distance;along=mix(a.w,b.w,f);}a=b;
            }
        }
        if(nearest>.045)continue;
        vec4 state=u_arc_links[row];float width=.0009+.00065*energy;
        float wire=exp(-pow(nearest/width,2.)),halo=exp(-nearest/(width*5.))*.18*(1.-smoothstep(.032,.045,nearest));
        float front=exp(-pow((along-state.y)/.060,2.))*state.z;
        float scar=state.x*(.50+.50*pow(.5+.5*sin(along*97.+row),8.));
        emission+=color_tint(dust,u_arcs_charge_on,u_arcs_charge[1])*(wire+halo)*state.w*u_plasma_details.x;
        emission+=color_tint(residue,u_arcs_charge_on,u_arcs_charge[1])*(wire+halo*2.)*scar*.55*u_plasma_details.y;
        emission+=color_tint(charge,u_arcs_charge_on,u_arcs_charge[2])*(wire+halo*2.8)*front*3.2*u_plasma_details.y;
        float forks=pow(.5+.5*sin(along*61.-phase*5.+row),22.);
        emission+=charge*halo*forks*front*high*.50*u_plasma_details.z;
    }
    return color+emission/(1.+emission*.60);
}

void main(){vec2 p=gl_FragCoord.xy/u_resolution-.5;p.x*=u_resolution.x/u_resolution.y;frag=vec4(arc_constellation(p),1.);}
