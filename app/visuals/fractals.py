"""Main Fractal presentation in Renderer; bounded clocks, no simulation."""
import json
import math
import re
from pathlib import Path
from preview_layers import layers_at,fractal_treatments_at
from color_controls import targets_for,color_uniforms,fractal_authored_colors,STATE_COLOR_SCENE
from planet_listening import unpack_input


class FractalMotion:
    def __init__(self):
        self.reset()

    def reset(self):
        self.form=None;self.last=None;self.travel=0.;self.growth=0.;self.rate=.18

    def advance(self,form,seconds,movement,flux):
        if form!=self.form or self.last is not None and seconds<self.last:
            self.reset();self.form=form
        dt=0. if self.last is None else min(.25,max(0.,seconds-self.last))
        self.last=seconds
        target=.18+.42*max(0.,min(1.,movement))
        self.rate+=(target-self.rate)*(1.-math.exp(-dt/.7))
        self.travel+=dt*self.rate
        self.growth+=dt*(.009+.005*max(0.,min(1.,movement))+.002*max(0.,min(1.,flux)))
        # Bounded float state even after long sessions; no queued catch-up steps.
        self.travel%=8192.;self.growth%=4096.
        return self.travel,self.growth,self.rate


def integrated_shader(main):
    """Reuse the authored shader equations inside Main, with explicit endpoint scope."""
    source=(Path(__file__).parent/'shaders/fractals.frag').read_text(encoding='utf8')
    body=source[source.index('const float PI'):source.index('void main()')]
    names=re.findall(r'\b(?:float|vec[234]|mat[234])\s+(\w+)\s*\(',body)
    for name in names:body=re.sub(r'\b'+name+r'\b','fr_'+name,body)
    body=re.sub(r'\bPI\b','FR_PI',body)
    body=body.replace('float gain=u_form_audio_a[slot/4][slot%4];','float gain=1.;if(u_audio_forms.x==fr_form)gain=u_form_audio_a[slot/4][slot%4];else if(u_audio_forms.y==fr_form)gain=u_form_audio_b[slot/4][slot%4];')
    for old,new in (('u_seed','u_fractal_seed'),('u_time','u_fractal_time'),('u_impact','u_fractal_impact'),('u_audio','u_fractal_audio'),('u_motion','fr_motion'),('u_treatments','fr_treatments'),('u_lamellae_colors','fr_lamellae_colors')):
        body=re.sub(r'\b'+old+r'\b',new,body)
    header='''
uniform vec3 u_fractal_pair,u_fractal_motion[3];
uniform vec2 u_fractal_treatments[3];
uniform vec3 u_fractal_lamellae[9];
uniform float u_fractal_seed,u_fractal_time,u_fractal_impact;
uniform vec4 u_fractal_audio;
uniform vec3 u_fractal_terrain[5],u_fractal_sky[3],u_fractal_stone[5],u_fractal_light[3];
uniform vec2 u_fractal_terrain_ranges[4],u_fractal_stone_ranges[4];
uniform vec3 u_fractal_honey[3],u_fractal_petals[6];
int fr_form=41;
vec3 fr_motion;
vec2 fr_treatments;
vec3 fr_lamellae_colors[3];
int forced_audio_context=-1;
'''
    evaluate='''
vec4 fractal_frame(int form,vec2 p){
 if(u_directed==1 && u_debug_state==0. && u_world_warp>0.){
  float warp=(u_handoff.x>.5 ? 0. : u_world_warp)*(.12+.12*clamp(u_audio_forms.x!=0 ? u_transition_audio.x+u_transition_audio.y : u_scale+u_flux,0.,1.));
  float angle=warp*exp(-dot(p,p)*1.2)*sin(length(p)*3.+audio_time()*.12);
  p=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*p;
  p*=1.+warp*(.6-length(p)*.3);
 }
 fr_form=form;int i=form-41;fr_motion=u_fractal_motion[i];fr_treatments=u_fractal_treatments[i];
 for(int j=0;j<3;j++)fr_lamellae_colors[j]=u_fractal_lamellae[i*3+j];
 vec3 color=form==41 ? fr_landscape(p) : form==42 ? fr_recursion(p) : fr_growth(p);
 float peak=max(color.r,max(color.g,color.b));color/=1.+peak*.35;
 color*=1.-.12*smoothstep(.2,1.2,length(p));return vec4(max(color,vec3(0.)),1.);
}
'''
    main=main.replace('vec4 scene_frame()',header+body+evaluate+'\nvec4 scene_frame()',1)
    main=main.replace('    if(!(u_directed==1 && u_debug_state==0. && u_main_transition.x<-.5))audio_context=',
                      '    if(forced_audio_context>=0)audio_context=forced_audio_context;\n    else if(!(u_directed==1 && u_debug_state==0. && u_main_transition.x<-.5))audio_context=',1)
    main=main.replace('    if(u_audio_forms.x!=0 && audio_context==0 && u_main_transition.x>=-.5)',
                      '    if(forced_audio_context<0 && u_audio_forms.x!=0 && audio_context==0 && u_main_transition.x>=-.5)',1)
    # One call site for the large existing scene evaluator avoids duplicating
    # its compiler workload while sharing the accepted optical endpoint loop.
    start=main.rindex('void main(){')
    return main[:start]+'''
void main(){
    vec2 region_p=gl_FragCoord.xy/u_resolution-.5;region_p.x*=u_resolution.x/u_resolution.y;
    bool fractal_pair=u_fractal_pair.x>40. || u_fractal_pair.y>40.;
    bool optical=u_directed==1 && u_debug_state==0. && u_main_transition.x<-.5;
    bool separate=fractal_pair || optical;
    float phase=clamp(fractal_pair ? u_fractal_pair.z : u_main_transition.y,0.,1.);
    vec4 first=vec4(0.);
    for(int pass=0;pass<2;pass++){
        main_weights(region_p);
        if(separate)main_pair_weights(phase>=1. ? 1. : float(pass));
        int form=int(phase>=1. ? u_fractal_pair.y : pass==0 ? u_fractal_pair.x : u_fractal_pair.y);
        if(fractal_pair)forced_audio_context=form;
        else if(optical)audio_context=pass==0 ? u_audio_forms.x : u_audio_forms.y;
        vec4 frame=fractal_pair && form>40 ? fractal_frame(form,main_carry(region_p)) : scene_frame();
        float front=fractal_pair && u_main_transition.x>=.5 ? main_region(region_p) : phase;
        if(pass==0)first=frame;else first=mix(first,frame,front);
        if(!separate || phase<=0. || phase>=1. || (fractal_pair && u_fractal_pair.x==u_fractal_pair.y))break;
    }
    forced_audio_context=-1;fragColor=first;
}
'''


def submit_main(r,seconds,delta,rewound):
    from audio_scope import endpoints
    endpoint=endpoints(r,seconds);forms=endpoint['active'];state=r.state_at(seconds)
    if state!=0:source=target=state;phase=0.
    else:
        source=endpoint['outgoing'];target=endpoint['incoming'] or source
        phase=endpoint['progress']
        if r.transition_sequence:phase=phase*phase*(3.-2.*phase)
    p=r.program;p['u_fractal_pair'].value=(source,target,phase)
    if source in (41,42,43) or target in (41,42,43):
        style=p['u_main_transition'].value[0]
        p['u_main_transition'].value=(style,phase,source,target)
    present=set(forms)&{41,42,43}
    if not present:
        r.fractal_visible=set();r.fractal_amounts={}
        return
    if not hasattr(r,'fractal_motions'):r.fractal_motions={form:FractalMotion() for form in (41,42,43)};r.fractal_visible=set()
    motions=[];treatments=[];lamellae=[]
    for form in (41,42,43):
        clock=r.fractal_motions[form]
        if form in present:
            if rewound or form not in r.fractal_visible:clock.reset()
            group={41:'landscape',42:'recursion',43:'growth'}[form]
            owner=getattr(r,'studio_audio',None)
            movement=owner.model.value(form,'fractal.'+str(form)+'.'+group,'movement_response',r.parameters.movement) if owner else r.parameters.movement
            flux=owner.model.value(form,'fractal.'+str(form)+'.'+group,'flux_response',r.parameters.flux) if owner else r.parameters.flux
            clock.advance(form,seconds,movement,flux)
        motions.append((clock.travel,clock.growth,clock.rate));treatments.append(fractal_treatments_at(r.layer_profiles,form,seconds))
        values={}
        if form in present:
            active=tuple(t.id for t in targets_for(STATE_COLOR_SCENE[form]))
            effective=fractal_authored_colors(r.color_overrides,form,seconds)
            values=color_uniforms(effective,active,seconds,only=active)
        lamellae.extend(values.get('u_lamellae_colors',((.6,.5,.4),)*3))
        if form in present:
            for key,value in values.items():
                if key in p:p[key].value=value
    r.fractal_visible=present
    r.fractal_amounts={form:treatments[form-41] for form in present}
    for key,value in dict(u_fractal_motion=motions,u_fractal_treatments=treatments,u_fractal_lamellae=lamellae,
        u_fractal_seed=float(r.cosmos_seed%65536),u_fractal_time=seconds,u_fractal_audio=(r.parameters.scale,r.parameters.movement,r.parameters.flux,r.parameters.sparkle),u_fractal_impact=r.impact_envelope).items():p[key].value=value


def render(renderer,seconds,size):
    r=renderer;state=r.state_at(seconds);width,height=size
    rewound=r.last_render_time is not None and seconds<r.last_render_time
    delta=0. if r.last_render_time is None else max(0.,seconds-r.last_render_time)
    r.impact_envelope=max(r.parameters.impact,r.impact_envelope*math.exp(-6.*delta))
    r.last_render_time=seconds
    owner=getattr(r,'studio_audio',None)
    mode,mask=layers_at(r.layer_profiles,state,seconds)
    inputs=dict(bass=r.parameters.scale,movement=r.parameters.movement,flux=r.parameters.flux,
                sparkle=r.parameters.sparkle,impact=r.impact_envelope,raw_impact=r.parameters.impact)
    rows=[(1.,1.,1.,1.)]*32
    if owner:
        owner.prepare(seconds);owner.guard_history(rewound)
        ids,rows,_=owner.resolve(inputs,delta,rewound,mode)
    if not hasattr(r,'fractal_motion'):r.fractal_motion=FractalMotion()
    motion=r.fractal_motion.advance(state,seconds,unpack_input(inputs['movement'],rows[16][1]),unpack_input(inputs['flux'],rows[16][2]))
    amounts=fractal_treatments_at(r.layer_profiles,state,seconds)
    p=r.program
    for key,value in dict(u_resolution=(width,height),u_time=seconds,u_form=state,u_seed=float(r.cosmos_seed%65536),
                          u_motion=motion,u_audio=(inputs['bass'],inputs['movement'],inputs['flux'],inputs['sparkle']),
                          u_impact=inputs['impact'],u_treatments=amounts).items():
        p[key].value=value
    if 'u_form_audio_a' in p:p['u_form_audio_a'].value=rows[:p['u_form_audio_a'].array_length]
    update=r.color_inbox.take() if r.color_inbox else None
    if update is not None:r.set_colors(update[1]);r._color_applied_revision=update[0]
    active=tuple(t.id for t in targets_for(STATE_COLOR_SCENE[state]))
    effective=fractal_authored_colors(r.color_overrides,state,seconds)
    for key,value in color_uniforms(effective,active,seconds).items():
        if key in p:
            # Artist pigments do not reset growth, travel or audio histories.
            previous=r._color_uploads.setdefault(p,{})
            if previous.get(key)!=value:p[key].value=value;previous[key]=value
    r.ctx.screen.use();r.ctx.viewport=(0,0,width,height)
    import moderngl
    r.vao.render(moderngl.TRIANGLE_STRIP)
    if update is not None:r.color_inbox.applied(update[0],seconds,0.)
    if owner:
        owner.report_applied_edits(seconds)
        owner.contributions={target:True for target in owner.model.state if owner.model.state[target] and target.startswith('fractal.'+str(state)+'.')}
        owner.contributions['form.'+str(state)+'.material.lamellae']=amounts[0]>0.
        owner.contributions['form.'+str(state)+'.spatial.recursive_pulse']=amounts[1]>0.
        packet=owner.snapshot(seconds)
        if packet is not None:
            from studio_audio import PREFIX,MAX_PACKET
            raw=json.dumps(packet,separators=(',',':'),allow_nan=False)
            if len(raw.encode('utf8'))<=MAX_PACKET:print(PREFIX+raw,flush=True)
