#version 330

uniform float u_time;
uniform float u_shooting_stars;
uniform vec3 u_plasma_mix;
uniform float u_plasma_weight;
uniform vec3 u_plasma_details;
uniform vec3 u_fog_mix;
uniform float u_fog_weight;
uniform vec3 u_fog_details;
uniform vec3 u_earth_mix;
uniform float u_earth_weight;
uniform vec4 u_earth_details;
uniform vec4 u_air_mix;
uniform float u_air_weight;
uniform float u_air_flash_id;
uniform float u_air_afterglow;
uniform vec2 u_air_trails[3];
uniform float u_daddy_long_legs;
uniform float u_firescape_travel;
uniform float u_star_time;
uniform float u_galaxy_release;
uniform vec2 u_stellar_layers;
uniform vec4 u_stellar_events[8]; // birth, orbit angle, pigment mix, strength
uniform int u_stellar_sails_on;
uniform vec3 u_stellar_sails[3];
uniform float u_drift_time;
uniform vec2 u_resolution;
uniform float u_intensity;
uniform float u_distortion;
uniform float u_scale;
uniform float u_sparkle;
uniform float u_impact;
uniform float u_flux;
uniform float u_debug_state;
uniform int u_roots_blue_on, u_roots_pearl_on, u_roots_ridge_on, u_roots_blossoms_on;
uniform vec3 u_roots_blue[5], u_roots_pearl[5];
uniform vec2 u_roots_blue_ranges[4], u_roots_pearl_ranges[4];
uniform vec3 u_roots_ridge, u_roots_blossoms;
uniform int u_membrane_blue_on, u_membrane_pearl_on, u_membrane_ridge_on;
uniform vec3 u_membrane_blue[5], u_membrane_pearl[5];
uniform vec2 u_membrane_blue_ranges[4], u_membrane_pearl_ranges[4];
uniform vec3 u_membrane_ridge;
uniform int u_corridor_inlay_on, u_corridor_glyphs_on;
uniform vec3 u_corridor_inlay, u_corridor_glyphs;
uniform int u_planet_surface_on, u_planet_rings_on, u_planet_moons_on;
uniform vec3 u_planet_surface, u_planet_rings[3], u_planet_moons[8];
uniform int u_galaxy_colors_on;
uniform vec3 u_galaxy_colors[6];
uniform vec3 u_next_galaxy_colors[6];
uniform int u_journey_colors_on;
uniform vec3 u_journey_colors[8];
uniform vec3 u_journey_eye,u_journey_target,u_journey_heading,u_journey_next_eye;
uniform float u_journey_bank,u_galaxy_weight,u_gravity_well;
uniform vec4 u_journey,u_journey_galaxy,u_journey_anchor,u_journey_next;
uniform vec4 u_journey_planets[8], u_journey_traits[8];
uniform vec4 u_journey_stars;
uniform int u_journey_count;
uniform vec3 u_journey_centers[8],u_journey_companion_center;
uniform int u_sky_stars_on, u_sky_shooting_on;
uniform vec3 u_sky_stars[2], u_sky_shooting[2];
uniform int u_material_artifacts_on, u_material_alloy_on, u_material_lattice_on, u_material_echo_on;
uniform vec3 u_material_artifacts[7], u_material_alloy[6], u_material_lattice[3], u_material_echo[3];
uniform int u_fx_sparkles_on, u_fx_flecks_on, u_fx_beams_on;
uniform vec3 u_fx_sparkles, u_fx_flecks[6], u_fx_beams[4];
uniform int u_water_sky_on, u_water_sea_on, u_water_rain_on, u_water_dyes_on;
uniform int u_water_currents_on, u_water_falls_on;
uniform vec3 u_water_sky[5], u_water_sea[4], u_water_rain[2], u_water_dyes;
uniform vec3 u_water_currents[2], u_water_falls[4];
uniform int u_fire_sheets_on, u_fire_details_on, u_molten_flow_on;
uniform int u_firescape_land_on, u_aftershock_land_on, u_aftershock_events_on;
uniform vec3 u_fire_sheets[2], u_fire_details[4], u_molten_flow[3];
uniform vec3 u_firescape_land[5], u_aftershock_land[4], u_aftershock_events[4];
uniform int u_air_sky_on, u_air_clouds_on, u_air_lightning_on;
uniform int u_air_balloons_on, u_air_citadel_on, u_air_daddy_on;
uniform vec3 u_air_sky[3], u_air_clouds[3], u_air_lightning[3];
uniform vec3 u_air_balloons[2], u_air_citadel[4], u_air_daddy;
uniform int u_citadel_colors_on;
uniform vec3 u_citadel_colors[6];
uniform vec4 u_tower_motion,u_tower_events[4];
uniform float u_tower_amount,u_tower_visit;
uniform int u_earth_sky_on, u_earth_minerals_on, u_dunes_land_on;
uniform int u_strata_land_on, u_cavern_land_on;
uniform vec3 u_earth_sky[3], u_earth_minerals[2], u_dunes_land[2];
uniform vec3 u_strata_land[2], u_cavern_land[3];
uniform sampler2D u_cavern_cache;
uniform ivec2 u_cavern_origin;
uniform int u_cavern_cached, u_mineral_colors_on;
uniform vec3 u_mineral_colors[4];
uniform vec4 u_mineral_motion, u_mineral_fronts[4];
uniform float u_mineral_amount;

uniform int u_fog_vapor_on, u_fog_internal_on, u_marsh_solids_on, u_marsh_ghostlights_on;
uniform vec3 u_fog_vapor[3], u_fog_internal[2], u_marsh_solids[3], u_marsh_ghostlights[2];
uniform int u_plasma_sky_on, u_magnetic_field_on, u_arcs_charge_on, u_auroral_curtains_on;
uniform vec3 u_plasma_sky[2], u_magnetic_field[3], u_arcs_charge[3], u_auroral_curtains[2];
uniform sampler2D u_magnetic_paths,u_original_paths;
uniform int u_original_path_on;
uniform vec4 u_magnetic_bounds[12],u_magnetic_groups[96];
uniform mat3 u_magnetic_axes;
uniform vec4 u_magnetic_motion,u_magnetic_events[4];
uniform float u_magnetic_amount,u_magnetic_visit;
uniform int u_magnetic_bloom_on;
uniform vec3 u_magnetic_bloom[6];
uniform sampler2D u_arc_scene,u_aurora_scene;
uniform int u_plasma_experimental;
uniform vec4 u_molten_motion,u_molten_events[4];
uniform float u_molten_phase,u_molten_amount,u_molten_growth;
uniform int u_molten_palette_on;
uniform vec3 u_molten_palette[6],u_molten_authored[6];
uniform int u_marsh_cached,u_marsh_palette_on;
uniform float u_marsh_origin;
uniform vec4 u_marsh_lamps[14],u_marsh_meta[14],u_marsh_wakes[14],u_marsh_motion;
uniform vec3 u_marsh_palette[7],u_marsh_authored[7];
uniform int u_planet_palette; // Opt-in held Planet Canvas experiment only.
// Optional development isolation. Zero keeps every authored expression intact.
uniform int u_layer_mode;
uniform int u_layer_mask;
uniform vec4 u_shockwaves[8];
uniform vec3 u_material_mix;
uniform float u_echo_weave;
uniform vec3 u_new_materials;
uniform vec3 u_spatial_treatments;
uniform int u_ink_colors_on;
uniform vec3 u_ink_colors[4];
uniform int u_silk_colors_on;
uniform vec3 u_silk_colors[4];
uniform int u_mosaic_colors_on;
uniform vec3 u_mosaic_colors[4];
uniform sampler2D u_echo_history;
uniform int u_directed;
uniform vec4 u_world_mix; // corridor, planet, water, fire
uniform vec4 u_water_mix; // sea, dyes, rain, falls, normalized within water
uniform float u_current_mix;
uniform vec4 u_fire_mix; // sheets, molten, firescape, aftershock
uniform float u_root_mix;
uniform float u_world_warp;
uniform vec4 u_handoff; // style, progress, departing family, arriving family
uniform int u_event_blasts;
uniform float u_blast_retire[8];
uniform vec4 u_blast_events[8]; // birth, stable id, world x, world z
uniform vec4 u_main_transition,u_main_layout;
uniform int u_cavern_surface_on,u_citadel_surface_on;
uniform float u_citadel_focal;
uniform sampler2D u_cavern_surface,u_cavern_normal,u_citadel_surface,u_citadel_normal;
vec4 main_world_mix;
vec4 main_water_mix;
vec4 main_fire_mix;
vec4 main_air_mix;
vec3 main_earth_mix;
vec3 main_fog_mix;
vec3 main_plasma_mix;
float main_air_weight;
float main_earth_weight;
float main_fog_weight;
float main_plasma_weight;
float main_galaxy_weight;
float main_current_mix;
float main_root_mix;
float main_region(vec2 p){
    float phase=u_main_transition.y,style=u_main_transition.x;
    vec2 axis=vec2(cos(u_main_layout.x),sin(u_main_layout.x));
    float aspect=u_resolution.x/max(u_resolution.y,1.);
    float extent=abs(axis.x)*aspect*.5+abs(axis.y)*.5;
    vec2 q=vec2(dot(p,axis),dot(p,vec2(-axis.y,axis.x)));float field;
    if(style<1.5)field=.5+q.x/max(extent,.001)*.39+.065*sin(q.y*7.+u_main_layout.w*6.28)+.025*sin(q.y*13.-u_main_layout.w*3.);
    else if(style<2.5){vec2 cell=floor(p*5.);float seed=fract(sin(dot(cell,vec2(37.1,91.7))+u_main_layout.w*19.)*4375.3);field=.5+q.x/max(extent,.001)*.36+(seed-.5)*.18;}
    else {vec2 center=u_main_layout.yz;float radius=length((p-center)*vec2(.82,1.));float far=length((vec2(aspect*.5,.5)+abs(center))*vec2(.82,1.));field=.08+.80*radius/max(far,.001);}
    return smoothstep(clamp(field,.07,.93)-.028,clamp(field,.07,.93)+.028,phase);
}
void main_add_state(int state,float weight){
    if(state==2)main_world_mix.x+=weight;
    if(state==5)main_world_mix.y+=weight;
    if(state>=7 && state<=10){main_world_mix.z+=weight;main_water_mix[state-7]+=weight;}
    if(state==13){main_world_mix.z+=weight;main_current_mix+=weight;}
    if(state==14 || state==15 || state==17 || state==18){main_world_mix.w+=weight;main_fire_mix[state<16?state-14:state-15]+=weight;}
    if(state>=19 && state<=22){main_air_weight+=weight;main_air_mix[state-19]+=weight;}
    if(state>=24 && state<=26){main_earth_weight+=weight;main_earth_mix[state-24]+=weight;}
    if(state>=28 && state<=30){main_fog_weight+=weight;main_fog_mix[state-28]+=weight;}
    if(state>=32 && state<=34){main_plasma_weight+=weight;main_plasma_mix[state-32]+=weight;}
    if(state==12)main_root_mix+=weight;
    if(state==36)main_galaxy_weight+=weight;
}
void main_base_weights(){
    main_world_mix=u_world_mix;
    main_water_mix=u_water_mix;
    main_fire_mix=u_fire_mix;
    main_air_mix=u_air_mix;
    main_earth_mix=u_earth_mix;
    main_fog_mix=u_fog_mix;
    main_plasma_mix=u_plasma_mix;
    main_air_weight=u_air_weight;
    main_earth_weight=u_earth_weight;
    main_fog_weight=u_fog_weight;
    main_plasma_weight=u_plasma_weight;
    main_galaxy_weight=u_galaxy_weight;
    main_current_mix=u_current_mix;
    main_root_mix=u_root_mix;

}
void main_pair_weights(float front){
    main_world_mix=vec4(0.);main_water_mix=vec4(0.);main_fire_mix=vec4(0.);main_air_mix=vec4(0.);
    main_earth_mix=vec3(0.);main_fog_mix=vec3(0.);main_plasma_mix=vec3(0.);
    main_air_weight=0.;main_earth_weight=0.;main_fog_weight=0.;main_plasma_weight=0.;main_current_mix=0.;main_root_mix=0.;
    main_galaxy_weight=0.;
    main_add_state(int(u_main_transition.z+.5),1.-front);main_add_state(int(u_main_transition.w+.5),front);
    main_water_mix/=max(main_world_mix.z,1e-12);main_current_mix/=max(main_world_mix.z,1e-12);main_fire_mix/=max(main_world_mix.w,1e-12);
    main_air_mix/=max(main_air_weight,1e-12);main_earth_mix/=max(main_earth_weight,1e-12);main_fog_mix/=max(main_fog_weight,1e-12);main_plasma_mix/=max(main_plasma_weight,1e-12);
}
void main_weights(vec2 p){
    main_base_weights();
    if(u_directed==1 && u_debug_state==0. && u_main_transition.x>=.5)main_pair_weights(main_region(p));
}
vec2 main_carry(vec2 p){
    if(u_directed!=1 || u_debug_state!=0. || u_main_transition.x<.5)return p;
    float phase=u_main_transition.y,envelope=pow(sin(phase*3.14159265),2.);
    float front=main_region(p);float nearby=.25+.75*(4.*front*(1.-front));
    vec2 axis=vec2(cos(u_main_layout.x),sin(u_main_layout.x));
    if(u_main_transition.x<1.5)return p+axis*.045*envelope*nearby+vec2(-axis.y,axis.x)*.018*sin(dot(p,axis)*7.+phase*4.)*envelope;
    if(u_main_transition.x<2.5){vec2 cell=floor(p*5.);float seed=fract(sin(dot(cell,vec2(37.1,91.7))+u_main_layout.w*19.)*4375.3);return p+axis*(seed-.5)*.10*envelope;}
    vec2 d=p-u_main_layout.yz;return p-d/max(length(d),.08)*.045*envelope*nearby;
}
#define u_world_mix main_world_mix
#define u_water_mix main_water_mix
#define u_fire_mix main_fire_mix
#define u_air_mix main_air_mix
#define u_earth_mix main_earth_mix
#define u_fog_mix main_fog_mix
#define u_plasma_mix main_plasma_mix
#define u_air_weight main_air_weight
#define u_earth_weight main_earth_weight
#define u_fog_weight main_fog_weight
#define u_plasma_weight main_plasma_weight
#define u_galaxy_weight main_galaxy_weight
#define u_current_mix main_current_mix
#define u_root_mix main_root_mix

float effect(int bit) {
    float enabled = u_layer_mode == 0 || (u_layer_mask & bit) != 0 ? 1.0 : 0.0;
    if (u_directed == 1) {
        // Independent detail tides, not switches synchronized to world changes.
        if (bit == 4096) enabled *= .18+.82*(.5-.5*cos(u_drift_time*.071));
        if (bit == 8192) enabled *= .25+.75*(.5+.5*sin(u_drift_time*.053+.8));
        if (bit == 65536) enabled *= .40+.60*(.5+.5*sin(u_drift_time*.089+2.));
    }
    return enabled;
}

out vec4 fragColor;

vec3 color_tint(vec3 authored, int enabled, vec3 tint) {
    return enabled == 1 ? authored * tint : authored;
}

float hash(vec2 p)
{
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p)
{
    vec2 i = floor(p);
    vec2 f = fract(p);

    f = f * f * (3.0 - 2.0 * f);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(
        mix(a, b, f.x),
        mix(c, d, f.x),
        f.y
    );
}

float fbm(vec2 p)
{
    float value = 0.0;
    float amplitude = 0.5;

    for (int i = 0; i < 5; i++)
    {
        value += amplitude * noise(p);
        p *= 2.0;
        amplitude *= 0.5;
    }

    return value;
}

// Deep Space / Aurora value ramp: hue follows brightness, not time,
// so the form never cycles through the hue wheel.
vec3 aurora_palette(float v)
{
    vec3 deep = vec3(0.010, 0.012, 0.022);
    vec3 indigo = vec3(0.090, 0.070, 0.220);
    vec3 violet = vec3(0.280, 0.140, 0.460);
    vec3 cyan = vec3(0.200, 0.550, 0.620);
    vec3 pale = vec3(0.860, 0.970, 1.000);

    vec3 color = mix(deep, indigo, smoothstep(0.0, 0.35, v));
    color = mix(color, violet, smoothstep(0.30, 0.60, v));
    color = mix(color, cyan, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Ocean/Cyan/Blue: paired with the tunnel/wormhole manifestation.
vec3 ocean_palette(float v)
{
    vec3 deep = vec3(0.006, 0.014, 0.020);
    vec3 teal = vec3(0.030, 0.180, 0.200);
    vec3 blue = vec3(0.050, 0.320, 0.520);
    vec3 cyan = vec3(0.150, 0.620, 0.680);
    vec3 pale = vec3(0.820, 0.980, 0.980);

    vec3 color = mix(deep, teal, smoothstep(0.0, 0.35, v));
    color = mix(color, blue, smoothstep(0.30, 0.60, v));
    color = mix(color, cyan, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Emerald/Violet: paired with fractal and geometric manifestations.
vec3 crystal_palette(float v)
{
    vec3 deep = vec3(0.010, 0.008, 0.018);
    vec3 violet = vec3(0.200, 0.080, 0.340);
    vec3 emerald = vec3(0.060, 0.420, 0.280);
    vec3 mint = vec3(0.450, 0.850, 0.620);
    vec3 pale = vec3(0.920, 0.990, 0.940);

    vec3 color = mix(deep, violet, smoothstep(0.0, 0.35, v));
    color = mix(color, emerald, smoothstep(0.30, 0.60, v));
    color = mix(color, mint, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Indigo/Magenta/Ember: paired with the cosmic collapse/reform state.
vec3 ember_palette(float v)
{
    vec3 deep = vec3(0.012, 0.008, 0.016);
    vec3 indigo = vec3(0.160, 0.050, 0.280);
    vec3 magenta = vec3(0.550, 0.080, 0.420);
    vec3 ember = vec3(0.950, 0.350, 0.120);
    vec3 warm_white = vec3(1.000, 0.920, 0.850);

    vec3 color = mix(deep, indigo, smoothstep(0.0, 0.35, v));
    color = mix(color, magenta, smoothstep(0.30, 0.60, v));
    color = mix(color, ember, smoothstep(0.55, 0.85, v));
    color = mix(color, warm_white, smoothstep(0.82, 1.0, v));

    return color;
}

// Crimson/Gold/Black: the Heart's bass-driven color stain.
vec3 crimson_gold_palette(float v)
{
    vec3 deep = vec3(0.014, 0.006, 0.006);
    vec3 crimson = vec3(0.320, 0.030, 0.060);
    vec3 red = vec3(0.620, 0.090, 0.080);
    vec3 gold = vec3(0.900, 0.620, 0.220);
    vec3 warm_white = vec3(1.000, 0.940, 0.820);

    vec3 color = mix(deep, crimson, smoothstep(0.0, 0.35, v));
    color = mix(color, red, smoothstep(0.30, 0.60, v));
    color = mix(color, gold, smoothstep(0.55, 0.85, v));
    color = mix(color, warm_white, smoothstep(0.82, 1.0, v));

    return color;
}

// Lavender/Blue/Pearl: one stop on the organic home-state wheel.
vec3 lavender_pearl_palette(float v)
{
    vec3 deep = vec3(0.012, 0.010, 0.018);
    vec3 blue = vec3(0.100, 0.110, 0.260);
    vec3 lavender = vec3(0.360, 0.300, 0.520);
    vec3 rose = vec3(0.680, 0.560, 0.640);
    vec3 pearl = vec3(0.960, 0.950, 0.970);

    vec3 color = mix(deep, blue, smoothstep(0.0, 0.35, v));
    color = mix(color, lavender, smoothstep(0.30, 0.60, v));
    color = mix(color, rose, smoothstep(0.55, 0.85, v));
    color = mix(color, pearl, smoothstep(0.82, 1.0, v));

    return color;
}

// Ink/Cream/Burgundy: one stop on the organic home-state wheel.
vec3 ink_burgundy_palette(float v)
{
    vec3 deep = vec3(0.008, 0.008, 0.010);
    vec3 ink = vec3(0.080, 0.060, 0.090);
    vec3 burgundy = vec3(0.360, 0.070, 0.140);
    vec3 rose_gold = vec3(0.740, 0.440, 0.360);
    vec3 cream = vec3(0.960, 0.920, 0.860);

    vec3 color = mix(deep, ink, smoothstep(0.0, 0.35, v));
    color = mix(color, burgundy, smoothstep(0.30, 0.60, v));
    color = mix(color, rose_gold, smoothstep(0.55, 0.85, v));
    color = mix(color, cream, smoothstep(0.82, 1.0, v));

    return color;
}

// Deep Teal/Amber/Violet: one stop on the organic home-state wheel.
vec3 teal_amber_palette(float v)
{
    vec3 deep = vec3(0.008, 0.014, 0.014);
    vec3 teal = vec3(0.040, 0.160, 0.170);
    vec3 violet = vec3(0.220, 0.140, 0.340);
    vec3 amber = vec3(0.780, 0.520, 0.180);
    vec3 pale = vec3(0.940, 0.950, 0.900);

    vec3 color = mix(deep, teal, smoothstep(0.0, 0.35, v));
    color = mix(color, violet, smoothstep(0.30, 0.60, v));
    color = mix(color, amber, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Fire: crimson/blood-red/burnt-red/amber, small pale-yellow cap.
vec3 fire_palette(float v)
{
    vec3 deep = vec3(0.012, 0.004, 0.004);
    vec3 blood = vec3(0.380, 0.030, 0.030);
    vec3 burnt = vec3(0.680, 0.140, 0.040);
    vec3 amber = vec3(0.950, 0.480, 0.090);
    vec3 pale = vec3(1.000, 0.900, 0.620);

    vec3 color = mix(deep, blood, smoothstep(0.0, 0.35, v));
    color = mix(color, burnt, smoothstep(0.30, 0.60, v));
    color = mix(color, amber, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Neon Forest: deep green foundation, emerald, neon green, pale cap.
vec3 neon_forest_palette(float v)
{
    vec3 deep = vec3(0.004, 0.014, 0.006);
    vec3 pine = vec3(0.030, 0.180, 0.070);
    vec3 emerald = vec3(0.080, 0.420, 0.160);
    vec3 neon = vec3(0.400, 0.950, 0.220);
    vec3 pale = vec3(0.880, 1.000, 0.780);

    vec3 color = mix(deep, pine, smoothstep(0.0, 0.35, v));
    color = mix(color, emerald, smoothstep(0.30, 0.60, v));
    color = mix(color, neon, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Deep Ocean / Electric Blue: near-black blue, cobalt, electric blue.
vec3 electric_blue_palette(float v)
{
    vec3 deep = vec3(0.004, 0.006, 0.016);
    vec3 cobalt = vec3(0.030, 0.090, 0.320);
    vec3 electric = vec3(0.080, 0.280, 0.920);
    vec3 cyan = vec3(0.300, 0.720, 0.980);
    vec3 pale = vec3(0.850, 0.960, 1.000);

    vec3 color = mix(deep, cobalt, smoothstep(0.0, 0.35, v));
    color = mix(color, electric, smoothstep(0.30, 0.60, v));
    color = mix(color, cyan, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Gold/Sun: deep brown/black foundation, burnt gold, bright gold.
vec3 gold_sun_palette(float v)
{
    vec3 deep = vec3(0.014, 0.010, 0.004);
    vec3 brown = vec3(0.180, 0.100, 0.020);
    vec3 burnt_gold = vec3(0.560, 0.360, 0.060);
    vec3 gold = vec3(0.940, 0.740, 0.220);
    vec3 pale = vec3(1.000, 0.960, 0.780);

    vec3 color = mix(deep, brown, smoothstep(0.0, 0.35, v));
    color = mix(color, burnt_gold, smoothstep(0.30, 0.60, v));
    color = mix(color, gold, smoothstep(0.55, 0.85, v));
    color = mix(color, pale, smoothstep(0.82, 1.0, v));

    return color;
}

// Geometric Dream: violet -> cyan -> hot pink -> gold -> bright highlight ramp.
// Used exclusively for the geometric manifestation so it reads as its
// own distinct visual ecosystem, separate from the fractal/crystal palette.
vec3 geometric_dream_palette(float v)
{
    vec3 deep = vec3(0.015, 0.008, 0.030);
    vec3 violet = vec3(0.280, 0.090, 0.480);
    vec3 cyan = vec3(0.060, 0.580, 0.680);
    vec3 hot_pink = vec3(0.900, 0.160, 0.580);
    vec3 gold = vec3(0.960, 0.680, 0.180);
    vec3 bright = vec3(1.000, 0.960, 0.880);

    vec3 color = mix(deep, violet, smoothstep(0.0, 0.28, v));
    color = mix(color, cyan, smoothstep(0.22, 0.50, v));
    color = mix(color, hot_pink, smoothstep(0.45, 0.72, v));
    color = mix(color, gold, smoothstep(0.68, 0.90, v));
    color = mix(color, bright, smoothstep(0.85, 1.0, v));

    return color;
}

// Slow square-ish dwell wave: stays near 0 or 1 for a real stretch of
// time, easing continuously between, rather than a plain sine blip.
float dwell(float phase)
{
    float raw = 0.5 + 0.5 * sin(phase);
    return smoothstep(0.35, 0.65, raw);
}

// Shared spatial grammar acts on material/detail coordinates, never on the
// world's ray intersections, silhouettes, depth ordering or star clock.
bool shared_spatial() { return u_directed == 1 || u_layer_mode > 0; }
vec3 spatial_weights() {
    if (!shared_spatial()) return vec3(0.0);
    vec3 enabled = vec3(effect(16),effect(32),effect(64));
    if (u_layer_mode == 1) return enabled;
    float t = u_drift_time;
    // Long overlapping holds: the outgoing pull remains inside the next fold.
    vec3 phase=vec3(t*.185+.4,t*.157+2.0,t*.109+4.1);
    vec3 envelope=smoothstep(vec3(.18),vec3(.58),.5+.5*sin(phase));
    float energy = clamp(u_scale*.45+u_flux*.55,0.,1.);
    return enabled*envelope*(.94+.06*smoothstep(.05,.35,energy));
}
vec2 new_spatial_carrier(vec2 source) {
    vec2 q=source;
    float drive=.25+.50*clamp(.5*u_scale+.5*u_flux,0.,1.);
    if(u_spatial_treatments.x>0.) {
        for(int i=0;i<3;i++) {
            float id=float(i);vec2 center=1.25*vec2(sin(u_time*.11+id*2.1),cos(u_time*.08+id*1.7));
            vec2 d=q-center;float falloff=exp(-dot(d,d)*1.6);
            q+=d*falloff*sin(u_time*.18+id*2.3)*drive*u_spatial_treatments.x;
        }
    }
    if(u_spatial_treatments.y>0.) {
        float lane=sin(source.y*2.2-u_time*.16);
        q.x+=sin(source.y*2.2-u_time*.16)*(.3+drive)*u_spatial_treatments.y;
        q.y+=sin(source.x*1.7+u_time*.13+lane)*.38*drive*u_spatial_treatments.y;
    }
    if(u_spatial_treatments.z>0.) {
        vec2 local=source;float amount=u_spatial_treatments.z;
        for(int i=0;i<3;i++) {
            float size=2.4/pow(1.8,float(i));
            vec2 center=size*floor((source+size*.5)/size);
            vec2 d=source-center;
            float window=1.-smoothstep(size*.28,size*.43,max(abs(d.x),abs(d.y)));
            vec2 shift=vec2(sin(u_time*.09+float(i)),cos(u_time*.07+float(i)))*size*.1;
            local=mix(local,center+d*(1.2+.5*drive+.2*sin(u_time*.12))+shift*(.5+drive),window*amount*.65);
        }
        q+=local-source;
    }
    return q;
}

vec2 spatial_carrier(vec2 source) {
    vec3 w = spatial_weights();
    if (max(w.x,max(w.y,w.z)) <= 0.) return new_spatial_carrier(source);
    vec2 q=source;
    // A broad spiral throat without an atan seam or singular vanishing point.
    float radius=length(q);
    float twist=2.2/(1.+radius*.55)
        +4.0*sin(u_time*.18)+.55*sin(u_time*.61);
    mat2 turn=mat2(cos(twist),-sin(twist),sin(twist),cos(twist));
    // Reciprocal depth makes a visible throat, with a finite soft center.
    vec2 tunnel=turn*q*(2.6/(.32+radius*radius));
    q=mix(q,tunnel,w.x);
    vec2 pathway=vec2(q.x/(.85+abs(q.y)*.20),
        q.y/(1.+abs(q.y)*.16));
    pathway.x+=.22*sin(pathway.y*.8+u_time*.09);
    q=mix(q,pathway,w.z);
    // Bounded inversion keeps large readable lobes, not tiny singular shards.
    // Start from the preceding pulls so spatial effects actually inherit one another.
    vec2 folded=q;
    for(int i=0;i<4;i++) {
        folded=sqrt(folded*folded+vec2(.0025))/max(dot(folded,folded),.08)
            -vec2(.9+clamp(u_flux,0.,1.)*.15,.6);
    }
    // One central seed opens first; expanding recursive coverage reveals
    // neighboring clusters, then owns the material field at full maturity.
    float growth=mix(.10,5.0,smoothstep(.05,.90,w.y));
    float cluster=1.-smoothstep(growth,growth+.45,length(source));
    return new_spatial_carrier(mix(q,folded*.32,w.y*cluster));

}

// A small tapered branching tree, evaluated in the membrane's warped space.
// Children inherit their parent's endpoint so branches stay connected.
float root_network(vec2 position, float phase, float activity)
{
    vec2 tips[31];
    vec2 directions[31];
    float lengths[31];
    float widths[31];
    float nearest = 10.0;
    for (int i = 0; i < 31; i++)
    {
        vec2 base;
        if (i == 0)
        {
            base = vec2(0.0, -1.35);
            directions[i] = vec2(0.0, 1.0);
            lengths[i] = 0.85;
            widths[i] = 0.065;
        }
        else
        {
            int parent = (i - 1) / 2;
            base = tips[parent];
            float side = (i % 2 == 0) ? 1.0 : -1.0;
            float bend = side * (0.48 + 0.13 * sin(float(i) * 2.7))
                + sin(phase + float(i) * 1.7) * (0.06 + activity * 0.10);
            directions[i] = mat2(cos(bend), sin(bend),
                                  -sin(bend), cos(bend)) * directions[parent];
            lengths[i] = lengths[parent] * 0.72;
            widths[i] = widths[parent] * 0.64;
        }
        tips[i] = base + directions[i] * lengths[i];
        float along = clamp(dot(position - base, directions[i]) / lengths[i], 0.0, 1.0);
        float distance_to_branch = length(position - mix(base, tips[i], along));
        float taper = mix(widths[i], widths[i] * 0.64, along);
        nearest = min(nearest, distance_to_branch - taper);
    }
    return nearest;
}

// Form-specific pigments remain parked in other scenes. The authored branch
// below stays byte-for-byte equivalent when no valid target is assigned.
bool roots_color_scope() { return u_directed == 1 || ((u_debug_state > 11.5 && u_debug_state < 12.5) || (u_debug_state > .5 && u_debug_state < 1.5)); }
bool membrane_color_scope() { return u_directed == 1 || ((u_debug_state > 10.5 && u_debug_state < 11.5) || (u_debug_state > .5 && u_debug_state < 1.5)); }
vec3 roots_color_gradient(float v, vec3 colors[5], vec2 ranges[4])
{
    vec3 color = colors[0];
    for (int i=0; i<4; i++)
        color = mix(color, colors[i+1], smoothstep(ranges[i].x, ranges[i].y, v));
    return color;
}

// Small blossom clusters in root-space: a few five-petal flowers, kept
// deliberately sparse so the mycelium remains the primary form.
float blossom_field(vec2 position, float phase)
{
    float glow = 0.0;
    for (int i = 0; i < 6; i++)
    {
        float fi = float(i);
        vec2 center = (vec2(
            hash(vec2(fi, 19.0)),
            hash(vec2(fi, 37.0))
        ) - 0.5) * vec2(1.7, 1.25);
        center += vec2(sin(phase * 0.35 + fi), cos(phase * 0.27 + fi * 1.4)) * 0.035;
        vec2 local = position - center;
        float angle = atan(local.y, local.x);
        float radius = length(local);
        float petals = 0.5 + 0.5 * cos(angle * 5.0 + phase * 0.08);
        float petal_shape = smoothstep(0.16, 0.02, abs(radius - (0.075 + petals * 0.035)));
        float center_glow = smoothstep(0.045, 0.0, radius);
        glow = max(glow, petal_shape * 0.8 + center_glow);
    }
    return clamp(glow, 0.0, 1.0);
}

// Standalone Cosmic diagnostic composition. This intentionally bypasses the
// shared ZeraWave field so depth order can be judged without contamination.
// Orthographic camera looks down -Z. Positive Z is closer to the viewer.
// Sphere and ring intersections share this depth convention.
float cosmic_sphere_depth(vec2 p, vec3 center, float radius)
{
    float d = radius * radius - dot(p - center.xy, p - center.xy);
    return d >= 0.0 ? center.z + sqrt(max(d, 0.0)) : -100.0;
}

// Independent sphere-space moon materials: no sampled field or opacity changes.
vec3 cosmic_moon_material(vec3 normal, int index, float time)
{
    float spin = time * 0.12;
    vec3 q = vec3(cos(spin) * normal.x + sin(spin) * normal.z,
        normal.y, -sin(spin) * normal.x + cos(spin) * normal.z);
    float drift = time * 0.18;
    float fold = sin(q.y * 5.0 + sin(q.z * 4.0 + drift));
    float dye = 0.5 + 0.5 * sin(q.x * 5.0 + fold * 2.0 + drift);
    if (index == 0)
    {
        vec3 ink = mix(u_planet_moons_on == 1 ? u_planet_moons[0] : vec3(0.08, 0.85, 0.95),
            u_planet_moons_on == 1 ? u_planet_moons[1] : vec3(0.95, 0.08, 0.55), dye);
        float vein = pow(0.5 + 0.5 * sin(q.y * 9.0 + fold * 3.0 - drift), 8.0);
        return mix(ink, u_planet_moons_on == 1 ? u_planet_moons[2] : vec3(0.85, 1.0, 0.62), vein * 0.65);
    }
    if (index == 1)
    {
        float heat = 0.5 + 0.5 * sin(q.y * 7.0 + fold * 2.0 - drift * 2.0);
        vec3 flame = mix(u_planet_moons_on == 1 ? u_planet_moons[3] : vec3(0.95, 0.08, 0.015),
            u_planet_moons_on == 1 ? u_planet_moons[4] : vec3(1.0, 0.50, 0.04), heat);
        flame = mix(flame, u_planet_moons_on == 1 ? u_planet_moons[5] : vec3(0.08, 0.40, 1.0), smoothstep(0.45, 0.78, heat));
        return mix(flame, u_planet_moons_on == 1 ? u_planet_moons[6] : vec3(0.85, 0.96, 1.0), smoothstep(0.78, 1.0, heat));
    }
    // Moving nested shells, broad enough to remain readable on a small moon.
    float layers = length(q.xy + vec2(0.22, -0.18)) * 3.0
        + q.z * 0.35 - time * 0.10;
    vec3 shell = 0.52 + 0.46 * cos(6.2831853 * (layers + vec3(0.0, 0.33, 0.67)));
    return u_planet_moons_on == 1 ? shell * u_planet_moons[7] : shell;
}

// Bounded material chroma/lift. Zero drive is exactly the accepted quiet color.
// Applied only to planet/rings, never to final scene, stars or moon materials.
vec3 cosmic_vivid_material(vec3 material, float drive)
{
    float gray = dot(material, vec3(0.2126, 0.7152, 0.0722));
    vec3 vivid = max(vec3(0.0), vec3(gray) + (material - gray) * (1.0 + 1.2 * drive));
    vivid *= 1.0 + 0.30 * drive;
    // Keep channel ratios instead of flattening saturated highlights to white.
    return vivid / max(1.0, max(vivid.r, max(vivid.g, vivid.b)));
}

// Proposed soft-dream contrast, local to Planet Canvas pigment. Preserve
// luminance (including dark material detail); never tint the final scene.
vec3 planet_palette(vec3 pigment)
{
    if (u_planet_palette != 1 || u_debug_state != 5.0) return pigment;
    vec3 weights = vec3(.2126, .7152, .0722);
    float luminance = dot(pigment, weights);
    float peak = max(pigment.r, max(pigment.g, pigment.b));
    float low = min(pigment.r, min(pigment.g, pigment.b));
    float chroma = peak - low;
    float hue = 0.0;
    if (chroma > .00001) {
        if (peak == pigment.r) hue = (pigment.g - pigment.b) / chroma;
        else if (peak == pigment.g) hue = 2.0 + (pigment.b - pigment.r) / chroma;
        else hue = 4.0 + (pigment.r - pigment.g) / chroma;
    }
    float phase = fract(hue / 6.0) * 4.0;
    vec3 cream = vec3(.94, .88, .73);
    vec3 lavender = vec3(.80, .67, .87);
    vec3 pink = vec3(.80, .52, .60);
    vec3 blue_green = vec3(.36, .66, .63);
    vec3 tint;
    if (phase < 1.0) tint = mix(pink, cream, phase);
    else if (phase < 2.0) tint = mix(cream, blue_green, phase - 1.0);
    else if (phase < 3.0) tint = mix(blue_green, lavender, phase - 2.0);
    else tint = mix(lavender, pink, phase - 3.0);
    // Neutral highlights remain neutral; compress chroma before gamut clipping.
    tint = mix(cream, tint, smoothstep(0.0, .15, chroma));
    vec3 delta = luminance * (tint / dot(tint, weights) - 1.0);
    float headroom = max(0.0, 1.0 - luminance);
    float strength = min(1.0, headroom / max(max(delta.r, max(delta.g, delta.b)), .00001));
    return vec3(luminance) + delta * strength;
}

// Direction-space radiance: the sea samples the same events in its reflection.
// Independent staggered births leave quiet sky between brief passages.
vec3 shooting_star_radiance(vec3 direction)
{
    if(u_shooting_stars < .001) return vec3(0.);
    vec2 q=vec2(atan(direction.x,direction.z),direction.y/max(length(direction.xz),.001));
    vec3 light=vec3(0.);
    float aa=max(1.2/u_resolution.y,.0008);
    for(int i=0;i<3;i++) {
        float lane=float(i), clock=u_star_time+lane*4.73;
        float period=12.7+lane*1.91, event=floor(clock/period);
        float age=mod(clock,period), seed=hash(vec2(event,lane+71.));
        float duration=1.35+seed*.8;
        if(age>duration)continue;
        vec2 start=vec2((hash(vec2(event+17.,lane))-.5)*1.4,.10+seed*.24);
        vec2 velocity=vec2(mix(-.48,.48,step(.5,seed)),-.09-seed*.10);
        vec2 head=start+velocity*age, heading=normalize(velocity);
        vec2 delta=q-head;
        float behind=-dot(delta,heading), across=abs(dot(delta,vec2(-heading.y,heading.x)));
        float tail=.13+.20*seed;
        float streak=exp(-across*across/(aa*aa))*exp(-max(behind,0.)/tail*3.)
            *smoothstep(-aa,aa,behind)*(1.-smoothstep(tail*.8,tail,behind));
        float core=exp(-dot(delta,delta)/(aa*aa*3.));
        float halo=exp(-dot(delta,delta)/.0003)*.10;
        float life=smoothstep(0.,.12,age)*(1.-smoothstep(duration*.65,duration,age));
        vec3 tint=mix(u_sky_shooting_on == 1 ? u_sky_shooting[0] : vec3(.22,.65,1.),
            u_sky_shooting_on == 1 ? u_sky_shooting[1] : vec3(1.,.36,.12),seed);
        light+=(tint*streak+mix(tint,vec3(1.),.55)*core+halo*tint)*life
            *(.65+.35*u_sparkle+.35*u_impact);
    }
    return light*u_shooting_stars*smoothstep(.01,.06,q.y);
}

// Shared star sheets: boost 1 preserves Planet Canvas; Air can lengthen wakes.
vec3 cosmic_star_layer(vec2 p, float trail_boost)
{
    // Layered star sheets drift one way across the sky and wrap off-screen.
    // Motion comes from the integrated clock, never from a spring that
    // returns. Audio only changes cruise speed and trail length.
    float star_drive = 0.48 * clamp(u_flux, 0.0, 1.0)
        + 0.22 * clamp(u_sparkle, 0.0, 1.0)
        + 0.30 * clamp(u_impact, 0.0, 1.0);
    float chorus = smoothstep(0.38, 0.88, star_drive);
    // Quiet: almost a point. Chorus: a long, thin wake behind the heading.
    float trail_len = mix(0.0012, 0.095, chorus * chorus) * trail_boost;
    vec3 star_layer = vec3(0.0);
    for (int layer_i = 0; layer_i < 3; layer_i++)
    {
        float layer = float(layer_i);
        float depth = 0.22 + 0.39 * layer;
        // Farther sheets crawl; nearer sheets travel faster. Headings stay
        // nearly parallel so the field reads as space, not a wheel.
        vec2 heading = normalize(vec2(0.94, 0.12 + 0.10 * (layer - 1.0)));
        float layer_speed = mix(0.028, 0.13, depth);
        vec2 star_p = p - heading * u_star_time * layer_speed;
        float grid = mix(42.0, 28.0, depth);
        int trail_samples=int(min(24.,ceil(5.*trail_boost)));
        for (int star_i = 0; star_i < 24; star_i++)
        {
            if(star_i>=trail_samples)break;
            float tail = float(star_i) / float(trail_samples-1);
            vec2 sample_p = star_p + heading * tail * trail_len;
            vec2 cell = floor(sample_p * grid + layer * 13.0);
            vec2 local = fract(sample_p * grid + layer * 13.0);
            float seed = hash(cell + 61.0);
            vec2 star_center = vec2(hash(cell + 12.3), hash(cell + 45.7));
            float head_size = mix(0.018, 0.072, pow(seed, 7.0))
                * (0.78 + 0.22 * depth);
            float star_size = head_size * mix(1.0, 0.18, tail);
            float star_aa = grid / u_resolution.y;
            // Chorus reveals a few more faint stars; quiet keeps them sparse.
            float presence = step(mix(0.935, 0.905, chorus), seed);
            float star_distance=length(local-star_center);
            if(trail_boost>1.) {
                vec2 delta=local-star_center;
                float half_wake=trail_len*grid/float(trail_samples-1)*.55
                    *smoothstep(1.,1.4,trail_boost);
                star_distance=length(vec2(dot(delta,vec2(-heading.y,heading.x)),
                    max(0.,abs(dot(delta,heading))-half_wake)));
            }
            float stars = (1.0 - smoothstep(star_size, star_size + star_aa,
                star_distance)) * presence;
            vec3 star_color = mix(u_sky_stars_on == 1 ? u_sky_stars[0] : vec3(0.55, 0.72, 1.0),
                u_sky_stars_on == 1 ? u_sky_stars[1] : vec3(1.0, 0.83, 0.62), hash(cell + 2.0));
            // Dwell brightness lives in the star, not in its position.
            float phase = seed * 60.0;
            float twinkle = 0.28 + 0.72 * (0.5 + 0.5 * sin(
                u_star_time * (0.18 + 0.55 * seed) + phase));
            twinkle = mix(twinkle, 0.82 + 0.18 * seed, chorus);
            float trail_fade = pow(1.0 - tail, 1.35);
            float alive = 0.22 + 0.55 * seed + 0.45 * chorus;
            star_layer = max(star_layer, star_color * stars
                * alive * twinkle * trail_fade);
        }
    }
    return star_layer + shooting_star_radiance(vec3(p,1.));
}

// Galaxy Odyssey: analytic camera, seven absorbing/emitting dust strata and
// orbiting light-sails. Fixed loops and no persistent GPU allocations.
mat3 stellar_camera(out vec3 eye) {
    if(u_debug_state>35.5 || u_galaxy_weight>0.) {
        eye=u_journey_eye;vec3 f=normalize(u_journey_target-eye);
        vec3 r=normalize(cross(f,vec3(0,1,0))),v=cross(r,f);
        return mat3(r*cos(u_journey_bank)+v*sin(u_journey_bank),v*cos(u_journey_bank)-r*sin(u_journey_bank),f);
    }
    float t=u_star_time;
    float az=.22*sin(t*.018)+t*.014;
    float distance=2.95+.80*sin(t*.029+.6);
    float elevation=.28+.56*(.5+.5*sin(t*.021));
    eye=distance*vec3(cos(az)*cos(elevation),sin(elevation),sin(az)*cos(elevation));
    vec3 forward=normalize(-eye);
    vec3 right=normalize(cross(forward,vec3(0,1,0)));
    vec3 up=cross(right,forward);
    float bank=.14*sin(t*.017);
    return mat3(right*cos(bank)+up*sin(bank),up*cos(bank)-right*sin(bank),forward);
}

// Reusable spatial layer: depth-separated lights travel past the viewer;
// their cell centers stay inside each tile, so no boundary popping is visible.
vec3 parallax_shoal(vec2 p) {
    vec3 cold=u_sky_stars_on==1 ? u_sky_stars[0] : vec3(.31,.65,1.);
    vec3 warm=u_sky_stars_on==1 ? u_sky_stars[1] : vec3(1.,.65,.36);
    vec3 light=vec3(0);
    for(int layer=0;layer<3;layer++) {
        float z=float(layer)+1.;
        vec2 uv=p*(64./z)+vec2(u_star_time*(.065+.03*z),sin(u_star_time*.012)*2.)/z;
        vec2 cell=floor(uv);
        vec2 center=.2+.6*vec2(hash(cell+z*17.),hash(cell+z*31.));
        vec2 delta=fract(uv)-center;
        float seed=hash(cell+z*43.);
        float size=85./z;
        float point=exp(-dot(delta,delta)*size);
        float halo=exp(-dot(delta,delta)*size*.18)*.075;
        float twinkle=.65+.35*sin(u_star_time*(.3+seed)+seed*62.);
        light+=mix(cold,warm,seed)*(point+halo)*step(.978,seed)
            *(.22+.12*z+.35*u_sparkle)*twinkle;
    }
    return light;
}

// Reusable sky inhabitants, not a final-image Enveloper. Six orbiting sails
// have independently fluttering vanes and curved wakes. Galaxy places them
// behind/in front of its dust strata; other compatible worlds use the same view.
vec3 stellar_sails(vec2 p, bool front) {
    vec3 eye;mat3 camera=stellar_camera(eye);
    vec3 shell=u_stellar_sails_on==1 ? u_stellar_sails[0] : vec3(.22,.65,.82);
    vec3 edge=u_stellar_sails_on==1 ? u_stellar_sails[1] : vec3(1.,.42,.22);
    vec3 wake=u_stellar_sails_on==1 ? u_stellar_sails[2] : vec3(.56,.32,.95);
    vec3 result=vec3(0);
    for(int i=0;i<6;i++) {
        float fi=float(i), t=u_star_time;
        float orbit=t*(.07+fi*.009)+fi*2.399;
        float r=1.18+.14*fi;
        float height=.36*sin(orbit*.71+fi*1.2);
        if((height>=0.)!=front)continue;
        vec3 position=vec3(cos(orbit)*r,height,sin(orbit)*r);
        float focal=(u_debug_state>35.5 || u_galaxy_weight>0.) ? .95 : 1.35;
        vec3 view=transpose(camera)*(position-eye);
        if(view.z<.35)continue;
        vec2 center=view.xy/(view.z*focal);
        vec2 q=(p-center)*view.z*focal;
        float turn=orbit+fi*.8;
        q=mat2(cos(turn),-sin(turn),sin(turn),cos(turn))*q;
        float aa=max(.002,view.z*focal/u_resolution.y);
        float head=exp(-dot(q,q)/max(aa*aa,.00015));
        float tail=exp(-abs(q.y+.11*q.x*q.x)*95.)*exp(-abs(q.x)*8.)*step(q.x,0.);
        result+=edge*head*(.8+.5*u_sparkle)+mix(shell,wake,.35+.2*sin(fi))*tail*(.18+.28*u_flux);
        // A short curved wake records the orbit, with subpixel-safe widths.
        for(int j=1;j<=5;j++) {
            float lag=float(j)*.045;
            float a=orbit-lag;
            vec3 tail=vec3(cos(a)*r,.36*sin(a*.71+fi*1.2),sin(a)*r);
            vec3 tv=transpose(camera)*(tail-eye);
            vec2 delta=(p-tv.xy/(max(.35,tv.z)*focal));
            result+=wake*exp(-dot(delta,delta)*18000.)*(.075+.12*u_sparkle)*(1.-float(j)/6.);
        }
    }
    return result;
}

vec3 stellar_layers(vec2 p) {
    vec3 light=vec3(0);
    if(u_stellar_layers.x>0.)light+=(stellar_sails(p,false)+stellar_sails(p,true))*u_stellar_layers.x;
    if(u_stellar_layers.y>0. && u_debug_state<35.5 && u_galaxy_weight<=0.)light+=parallax_shoal(p)*u_stellar_layers.y;
    return light;
}

// Nested scales share the selected star's world anchor. Local coordinates are
// used only for solar detail. Descriptors and continuous routes are CPU-owned.
mat3 journey_view(vec3 eye,vec3 target,float bank) {
    vec3 forward=normalize(target-eye);
    vec3 right=normalize(cross(forward,vec3(0,1,0)));
    vec3 up=cross(right,forward);
    return mat3(right*cos(bank)+up*sin(bank),up*cos(bank)-right*sin(bank),forward);
}

vec3 journey_sky(vec3 ray,float seed) {
    vec3 cold=u_sky_stars_on==1 ? u_sky_stars[0] : vec3(.31,.65,1.);
    vec3 warm=u_sky_stars_on==1 ? u_sky_stars[1] : vec3(1.,.65,.36);
    vec2 sky=vec2(atan(ray.z,ray.x),asin(clamp(ray.y,-1.,1.)));
    vec3 light=vec3(0);
    for(int i=0;i<3;i++) {
        float layer=float(i);float frequency=i==0 ? 26. : i==1 ? 76. : 175.;
        vec2 uv=sky*frequency+vec2(seed*.017+layer*37.,layer*19.);
        vec2 cell=floor(uv);
        float presence=hash(cell+seed*.13+layer*91.);
        if(presence<(i==0 ? .991 : i==1 ? .977 : .964))continue;
        vec2 q=fract(uv)-(.12+.76*vec2(hash(cell+layer*13.+7.),hash(cell+layer*37.+19.)));
        float size=hash(cell+layer*23.+113.);
        float radius=.018+.052*pow(size,5.);
        float aa=max(radius,.48*length(fwidth(uv)));
        float point=exp(-dot(q,q)*3./(aa*aa))*radius*radius/(aa*aa);
        float spectrum=hash(cell+layer*43.+seed*.37+201.);
        float luminosity=hash(cell+layer*59.+317.);
        vec3 pigment=mix(cold,warm,spectrum);
        pigment=mix(pigment,vec3(.78,.83,.90),.25+.35*hash(cell+431.));
        float brightness=i==0 ? .16+1.10*pow(luminosity,5.) : i==1 ? .16+.70*pow(luminosity,4.) : .48;
        float phase=hash(cell+layer*79.+503.);
        float twinkle=1.+(i==2 ? .012 : .045)*sin(u_star_time*(.09+.23*phase)+phase*89.);
        light+=pigment*point*brightness*twinkle;
    }
    return light*u_stellar_layers.y;
}

float journey_fbm(vec2 q) {
    return .57*noise(q)+.28*noise(q*2.03+17.)+.15*noise(q*4.11-9.);
}
vec3 journey_galaxy(vec3 eye,vec3 ray,vec4 spec,bool future) {
    vec3 core=u_galaxy_colors_on==1 ? (future ? u_next_galaxy_colors[0] : u_galaxy_colors[0]) : vec3(.98,.76,.50);
    vec3 arms=u_galaxy_colors_on==1 ? (future ? u_next_galaxy_colors[1] : u_galaxy_colors[1]) : vec3(.36,.53,.92);
    vec3 dust=u_galaxy_colors_on==1 ? (future ? u_next_galaxy_colors[2] : u_galaxy_colors[2]) : vec3(.16,.10,.22);
    vec3 stars=u_galaxy_colors_on==1 ? (future ? u_next_galaxy_colors[3] : u_galaxy_colors[3]) : vec3(.75,.87,1.);
    vec3 warm=u_galaxy_colors_on==1 ? (future ? u_next_galaxy_colors[4] : u_galaxy_colors[4]) : vec3(1.,.24,.43);
    vec3 cool=u_galaxy_colors_on==1 ? (future ? u_next_galaxy_colors[5] : u_galaxy_colors[5]) : vec3(.12,.85,.65);
    float family=clamp((spec.w-.72)/.17,0.,2.);
    core=mix(core,family<1.5 ? warm : cool,family>.5 ? .45 : .0);
    arms=mix(arms,family<1.5 ? cool : warm,family>.5 ? .90 : .0);
    if(family>.5 && family<1.5) { warm=mix(warm,core,.85);cool=mix(cool,dust,.72); }
    if(family>1.5) { warm=mix(warm,stars,.82);cool=mix(cool,core,.80); }
    float drive=clamp(.4*u_scale+.35*u_flux+.25*u_sparkle,0.,1.);
    vec3 light=dust*.019+journey_sky(ray,spec.z);
    vec3 core_offset=cross(eye,ray);
    light+=core*exp(-dot(core_offset,core_offset)*24.)*(.09+.08*drive);
    for(int i=0;i<7;i++) {
        if(abs(ray.y)<.0001)continue;
        float height=(float(i)-3.)*.065;
        float distance=(height-eye.y)/ray.y;
        if(distance<0. || distance>50.)continue;
        vec2 q=(eye+ray*distance).xz;
        float rotation=u_star_time*.070;
        q=mat2(cos(rotation),-sin(rotation),sin(rotation),cos(rotation))*q;
        q.y*=spec.w;
        float radius=length(q);
        if(radius>1.55)continue;
        float theta=atan(q.y,q.x);
        float cloud=journey_fbm(q*5.5+height*8.+spec.z*.019+vec2(u_star_time*.003,-u_star_time*.002));
        float fine=noise(q*24.+vec2(-u_star_time*.007,u_star_time*.004)+height*11.+spec.z*.031);
        float phase=spec.x*theta+spec.y*log(radius+.16)+cloud*1.25-height*4.;
        float spiral=pow(.5+.5*cos(phase),3.);
        float disk=1.-smoothstep(1.05,1.50,radius);
        float body=smoothstep(.08,.24,radius);
        float bulge=exp(-radius*radius*18.);
        float density=disk*(.035+1.08*spiral)*(.20+.95*cloud)*exp(-height*height*26.);
        float pores=journey_fbm(q*8.+height*7.+spec.z*.013);
        density*=1.-.78*smoothstep(.45,.65,pores)*body;
        float lane=pow(.5+.5*cos(phase+.8),12.)*disk*body;
        float threads=exp(-abs(noise(q*15.+height*13.+spec.z*.021)-.52)*65.);
        float region=noise(q*2.6+spec.z*.07);
        vec3 pigment=mix(arms,warm,smoothstep(.47,.72,region)*.82);
        pigment=mix(pigment,cool,smoothstep(.54,.76,noise(q*3.8-spec.z*.05))*.8);
        pigment=mix(pigment,stars,pow(fine,5.)*.65);
        pigment=mix(pigment,core,bulge*.78);
        vec3 emission=pigment*density*(.42+.95*drive+.25*u_galaxy_release);
        emission+=core*bulge*(.09+.16*drive);
        emission+=mix(core,stars,.7)*threads*spiral*disk*body*(.015+.035*drive);
        vec2 uv=q*37.+vec2(journey_fbm(q*8.),journey_fbm(q*8.+27.))*3.
            +vec2(height*413.,height*271.);vec2 cell=floor(uv);
        vec2 delta=fract(uv)-(.2+.6*vec2(hash(cell+7.),hash(cell+19.)));
        float knot=exp(-dot(delta,delta)*90.)*step(.98-.085*spiral*smoothstep(.38,.6,cloud),hash(cell+41.));
        emission+=mix(stars,core,hash(cell+spec.z+137.))*knot*disk*(.18+.42*spiral)*(.35+.55*u_sparkle);
        for(int e=0;e<8;e++) {
            vec4 event=u_stellar_events[e];float age=u_drift_time-event.x;
            if(age<0. || age>10. || event.w<=0.)continue;
            vec2 site=vec2(cos(event.y),sin(event.y))*(.5+.2*event.z);
            float birth=exp(-dot(q-site,q-site)*mix(180.,18.,age/10.));
            emission+=mix(warm,cool,event.z)*birth*sin(age*3.14159/10.)*event.w*.11;
        }
        light=light*(1.-clamp(density*.22+lane*.55,0.,.62))+dust*lane*.012+emission;
    }
    // Stylized spherical void with an illuminated bent disk and photon rim.
    float closest=max(0.,dot(-eye,ray));
    float impact=length(eye+ray*closest);
    if(closest>0.) {
        float photon=exp(-abs(impact-.075)*190.);
        vec3 right=normalize(cross(normalize(-eye),vec3(0,1,0)));
        vec3 up=cross(right,normalize(-eye));
        vec3 near=eye+ray*closest;
        float arc_angle=atan(dot(near,up),dot(near,right));
        vec3 bent=mix(core,cool,.32+.30*sin(arc_angle));
        float curvature=exp(-abs(impact-.095)*65.);
        light+=bent*photon*(1.4+1.2*drive)+mix(warm,stars,.35)*curvature*.25;
        if(abs(ray.y)>.0001) {
            float center_t=-eye.y/ray.y;
            if(center_t>0.) {
                vec2 center=(eye+ray*center_t).xz;float r=length(center),angle=atan(center.y,center.x);
                float disk=exp(-abs(r-(.11+.012*drive))*95.);
                float flow=pow(.5+.5*cos(angle*5.+log(r+.04)*10.+u_star_time*.42),9.);
                light+=mix(core,warm,.35)*(disk*(1.15+drive)+flow*exp(-r*5.)*.50)
                    *smoothstep(.065,.08,r);
            }
        }
        // Source darkness remains a sphere, not a hole cut out of one plane.
        light*=smoothstep(.056,.061,impact);
    }
    return light;
}

// Finite near-arm volume samples replace flattened galactic sheets during entry.
float journey_pressure();
vec3 journey_arm_depth(vec3 eye,vec3 ray,vec4 spec) {
    vec3 arms=u_galaxy_colors_on==1 ? u_galaxy_colors[1] : vec3(.36,.53,.92);
    vec3 dust=u_galaxy_colors_on==1 ? u_galaxy_colors[2] : vec3(.16,.10,.22);
    vec3 warm=u_galaxy_colors_on==1 ? u_galaxy_colors[4] : vec3(1.,.24,.43);
    vec3 cool=u_galaxy_colors_on==1 ? u_galaxy_colors[5] : vec3(.12,.85,.65);
    vec3 core=u_galaxy_colors_on==1 ? u_galaxy_colors[0] : vec3(.98,.76,.50);
    vec3 light=journey_sky(ray,spec.z);
    vec2 sky=vec2(atan(ray.z,ray.x),asin(clamp(ray.y,-1.,1.)));
    float latitude=sky.y+.12+.18*sin(sky.x+spec.z*.01);
    float band=exp(-latitude*latitude*18.);
    vec2 periodic=vec2(cos(sky.x),sin(sky.x))*(2.+sky.y);
    float cluster=journey_fbm(periodic*6.+sky.y*vec2(1.,7.)+spec.z*.03);
    float dust_lane=exp(-abs(latitude+.045*(cluster-.5))*22.);
    vec3 host=mix(arms,cool,smoothstep(.45,.70,cluster));
    host=mix(host,warm,smoothstep(.58,.76,noise(periodic*4.-spec.z*.02))*.7);
    float grain=band>.01 ? noise(periodic*27.+spec.z*.04) : .5;
    light=light*(1.-dust_lane*.50)+host*band*(.07+.50*cluster*cluster)*(.45+.30*grain)*(1.-dust_lane*.65);
    for(int i=3;i>=0;i--) {
        float distance=.06+float(i)*.20;
        vec3 q=eye+ray*distance;
        vec2 domain=q.xz*7.+q.y*vec2(3.7,-2.3)+spec.z*.017;
        float mass=.50*journey_fbm(domain+vec2(u_star_time*.002,0.))
            +.28*noise(q.xy*13.+spec.z*.019)+.22*noise(q.yz*11.-spec.z*.017);
        float clouds=smoothstep(.34,.68,mass);
        float cavities=smoothstep(.51,.72,noise(domain*1.6-q.y*8.+13.));
        float envelope=exp(-q.y*q.y*7.)*(1.-smoothstep(1.05,1.65,length(q.xz)));
        float density=clouds*envelope*(.35+.65*mass);
        vec3 pigment=mix(arms,cool,smoothstep(.48,.72,mass));
        pigment=mix(pigment,warm,smoothstep(.48,.67,noise(domain*.7+23.)));
        light=light*(1.-density*cavities*.42)+dust*density*.008
            +pigment*density*(.045+.075*u_scale)*(1.-cavities*.65);
    }
    // Three finite nursery landmarks carry real world-space parallax and
    // foreground extinction. Cheap bounds avoid evaluating texture elsewhere.
    if(u_journey.x>1.5 && u_journey.x<3.5) {
        float visit=u_journey.x<2.5 ? smoothstep(.05,.45,u_journey.y) : 1.-smoothstep(.02,.17,u_journey.y);
        for(int j=0;j<3;j++) {
            float id=float(j);
            vec3 center=u_journey_anchor.xyz+vec3(-.075+id*.085,.02+id*.012,.035-id*.06);
            vec3 delta=center-eye;float t=dot(delta,ray);
            if(t<=0.)continue;
            vec3 q=(eye+ray*t-center)/vec3(.055,.048,.065);
            float bound=dot(q,q);if(bound>2.2)continue;
            float folds=journey_fbm(q.xz*3.+q.y*2.+id*9.);
            float boundary=bound+.75*(folds-.5)+.28*sin(q.x*5.+folds*8.);
            float body=(1.-smoothstep(.35,1.8,boundary))*visit;
            float edge=exp(-abs(boundary-.85)*6.)*(.35+.65*folds);
            vec3 pigment=j==1 ? warm : mix(arms,cool,id*.3);
            light=light*(1.-body*(.35+.4*folds))
                +dust*body*.018+pigment*body*(.045+.12*folds+.075*edge)*(.65+.50*u_scale);
        }
    }
    vec3 direction=normalize(-eye);
    if(dot(direction,ray)>0.) {
        vec3 right=normalize(cross(direction,vec3(0,1,0))),up=cross(right,direction);
        float apparent=clamp(.09/length(eye),.045,.14);
        vec2 q=vec2(dot(ray,right),dot(ray,up)/max(.32,abs(direction.y)))/apparent;
        float radius=length(q),theta=atan(q.y,q.x);
        float cloud=journey_fbm(q*1.8+spec.z*.014);
        float spiral=pow(.5+.5*cos(spec.x*theta+spec.y*log(radius+.4)-u_star_time*.045+cloud*.7),3.);
        float bulge=exp(-radius*radius*.035)*(1.-smoothstep(3.5,6.,radius));
        float lanes=pow(.5+.5*cos(spec.x*theta+spec.y*log(radius+.4)+.6),10.);
        vec3 pigment=mix(arms,cool,cloud);
        light=light*(1.-bulge*lanes*.55)+pigment*bulge*spiral*(.08+.25*cloud)
            +core*exp(-radius*radius*.35)*.08;
        // Keep the enclosing arms vast; core aperture has its own distant angular scale.
        // It must not become a companion-sized halo beside the local primary.
        float remote_apparent=clamp(.0035/length(eye),.003,.008);
        float sphere_radius=length(vec2(dot(ray,right),dot(ray,up))/remote_apparent);
        float aperture=smoothstep(.43,.51,sphere_radius),ring=exp(-abs(sphere_radius-.64)*22.);
        float stream=pow(.5+.5*cos(theta*5.+log(radius+.15)*11.+u_star_time*.7),18.);
        light=light*aperture+mix(core,cool,.25+.20*sin(theta))*ring*(1.1+.8*journey_pressure())
            +mix(core,warm,.35)*stream*exp(-sphere_radius*.7)*smoothstep(.58,.9,sphere_radius)*.20;
    }
    return light;
}

// Ray/sphere nearest intersection using perpendicular distance avoids the
// cancellation of subtracting two enormous squared values on the scale bridge.
float journey_sphere(vec3 eye,vec3 ray,vec3 center,float radius) {
    vec3 delta=center-eye;
    float along=dot(delta,ray);
    float perpendicular=length(cross(delta,ray));
    if(perpendicular>=radius || along<0.)return 1e9;
    float root=sqrt(max(0.,radius*radius-perpendicular*perpendicular));
    float distance=along-root;
    return distance>0. ? distance : along+root;
}
vec3 journey_planet_center(vec4 spec,int body_id) {
    return u_journey_centers[body_id];
}
vec3 journey_companion() {
    return u_journey_companion_center;
}

vec3 journey_pigment(int role) {
    if(u_journey_colors_on==1)return u_journey_colors[role];
    if(role==0)return vec3(1.,.68,.32);
    if(role==1)return vec3(.57,.28,.19);
    if(role==2)return vec3(.08,.40,.70);
    if(role==3)return vec3(.65,.43,.74);
    if(role==4)return vec3(.83,.70,.39);
    if(role==6)return vec3(.23,.62,.28);
    if(role==7)return vec3(.96,.28,.54);
    return vec3(.36,.81,.91);
}

// Source roles stay editable; each generated body authors a distinct mixture.
vec3 journey_body_pigment(int role,int body_id) {
    float style=u_journey_traits[body_id].z;
    int recipe=int(style*5.);
    vec3 base=journey_pigment(role);
    vec3 accent=recipe==0 ? journey_pigment(0) : recipe==1 ? journey_pigment(6)
        : recipe==2 ? journey_pigment(1) : recipe==3 ? journey_pigment(5) : journey_pigment(4);
    // Contrast is authored per world: swap the dominant/subordinate relationship,
    // retain source-role edits, and vary saturation/value rather than hue alone.
    float weight=.18+.58*fract(style*5.);
    vec3 pigment=mix(base,accent,weight);
    float value=.60+.40*fract(style*17.+float(role)*.31);
    return pigment*value;

}
float journey_pressure() {
    return smoothstep(.10,.60,max(clamp(u_scale,0.,1.),clamp(u_flux,0.,1.)*.85));
}
float journey_echo(vec3 normal,float body_id) {
    float result=0.;
    for(int e=0;e<8;e++) {
        vec4 event=u_stellar_events[e];float age=u_drift_time-event.x;
        if(age<0. || age>4.8 || event.w<=0.)continue;
        vec3 axis=normalize(vec3(cos(event.y+body_id),.45,sin(event.y+body_id)));
        float distance=acos(clamp(dot(normal,axis),-1.,1.));
        result+=exp(-abs(distance-age*.72)*18.)*exp(-age*.55)*event.w;
    }
    return min(1.5,result);
}
vec3 journey_surface(vec3 normal,vec4 spec,float body_id) {
    int id=int(body_id);vec4 trait=u_journey_traits[id];vec3 n=normal;
    float clock=u_star_time*.035;
    float spin=u_star_time*(.027+trait.w*.012)*(1.+body_id*.07);
    n.xz=mat2(cos(spin),-sin(spin),sin(spin),cos(spin))*n.xz;
    vec2 uv=vec2(n.x+n.y*.43,n.z+n.y*.71)*2.2;
    float pressure=journey_pressure();float weather=clamp(.65*u_flux+.35*u_sparkle,0.,1.);
    vec2 curl=vec2(journey_fbm(uv*3.+spec.z),journey_fbm(uv*3.-clock*.09+13.))-.5;
    uv+=vec2(sin(uv.y*5.+clock),cos(uv.x*4.-clock*.7))*.12;
    uv+=curl*.14*sin(clock*.37); // persistent flow; beats change emission, not reset coordinates
    float echo=journey_echo(normal,body_id);
    uv+=normalize(vec2(curl.y,-curl.x)+vec2(.01))*echo*.16;
    vec3 rock=journey_body_pigment(1,id),ocean=journey_body_pigment(2,id);
    vec3 gas=journey_body_pigment(3,id),air=journey_body_pigment(5,id);
    if(spec.w<.5) {
        float terrain=journey_fbm(uv*(3.+trait.w)+curl*.8+spec.z);
        float fissure=exp(-abs(journey_fbm(uv*(5.+trait.w*2.)+curl*2.+spec.z)-.49)*85.);
        float lava=fissure*(.08+1.0*pressure+.65*u_impact+.25*u_galaxy_release);
        return rock*(.16+.35*terrain)+mix(journey_pigment(0),journey_pigment(7),terrain)*lava+air*echo*.55;
    }
    if(spec.w<1.5) {
        float continents=journey_fbm(uv*(1.2+trait.w*.35)+curl*.40+spec.z);
        float land=smoothstep(.47,.54,continents);
        float current=journey_fbm(uv*(7.+trait.w*3.)+curl*1.15-vec2(clock*.27,0.));
        vec3 surface=mix(ocean*(.42+.42*current),mix(journey_body_pigment(6,id),rock,.16)*(.36+.45*continents),land);
        float polar=smoothstep(.80,.96,abs(n.y));
        float tide=pow(.5+.5*sin(uv.x*19.+uv.y*11.+current*9.-clock*.8),8.);
        surface+=mix(ocean,air,.35)*tide*(1.-land)*pressure*.55;
        return mix(surface,journey_body_pigment(4,id),polar*.68)+air*echo*(1.-land)*1.1;
    }
    if(spec.w>3.5 && spec.w<4.5) {
        float frost=journey_fbm(uv*(5.+trait.w*3.)+curl+spec.z);
        float fractures=exp(-abs(frost-.48)*70.);
        return mix(air,journey_body_pigment(4,id),frost)*(.32+.68*frost)
            +ocean*fractures*(.15+.55*pressure)+air*echo*1.0;
    }
    if(spec.w>4.5 && spec.w<5.5) {
        float folds=journey_fbm(uv*trait.w*3.+spec.z);
        float dunes=.5+.5*sin(uv.y*(18.+trait.w*5.)+folds*8.+curl.x*1.3);
        return mix(rock,journey_body_pigment(4,id),dunes*.8)*(.30+.60*folds)
            +journey_body_pigment(7,id)*echo*.45;
    }
    if(spec.w>5.5) {
        float recipe=floor(trait.z*3.);
        vec2 domain=uv*(2.4+trait.w)+curl*1.1+spec.z;
        float field=journey_fbm(domain);
        float pattern=recipe<.5 ? field : recipe<1.5 ? journey_fbm(domain+vec2(field*4.,-field*3.))
            : .5+.5*sin(uv.x*4.+uv.y*6.+field*12.+clock*.18);
        float veins=exp(-abs(pattern-(.40+.13*trait.z))*45.);
        vec3 substrate=recipe<.5 ? rock : recipe<1.5 ? gas : ocean;
        vec3 seam=recipe<.5 ? journey_body_pigment(4,id) : recipe<1.5 ? air : journey_body_pigment(0,id);
        return mix(substrate*.24,substrate*.65,smoothstep(.3,.7,field))
            +seam*veins*(.16+.80*pressure)+journey_body_pigment(7,id)*echo*.65;
    }

    vec2 flow=uv+curl*.4;
    vec2 storm=flow-vec2(.3,-.22);storm.x=sin(flow.x-.3);
    float vortex=exp(-dot(storm,storm)*(8.+trait.w*4.));
    float spiral=atan(storm.y,storm.x)+length(storm)*(12.+trait.w*6.)-clock*.65;
    flow+=vortex*vec2(sin(spiral),cos(spiral))*.22;
    float grain=journey_fbm(flow*(3.+trait.w));
    float recipe=floor(trait.z*3.);
    float bands=recipe<.5 ? smoothstep(.28,.72,grain)
        : recipe<1.5 ? .5+.5*sin(flow.y*(4.+trait.w*2.)+grain*7.)
        : smoothstep(.3,.7,journey_fbm(flow*2.+vec2(grain*3.,-grain*2.)));
    float turbulence=journey_fbm(flow*(7.+trait.w*3.)+vec2(clock*.10,0.));
    vec3 primary=recipe<.5 ? mix(gas,rock,.65) : recipe<1.5 ? gas : mix(gas,ocean,.75);
    vec3 secondary=recipe<.5 ? air : recipe<1.5 ? journey_body_pigment(4,id) : journey_body_pigment(6,id);
    vec3 pigment=mix(primary,secondary,smoothstep(.23,.77,bands)*.8);
    float eye=exp(-dot(storm,storm)*65.);
    vec3 storm_tint=mix(journey_body_pigment(7,id),journey_body_pigment(4,id),eye*.55);
    return mix(pigment,storm_tint,vortex*(.38+.50*turbulence))*(.57+.43*turbulence)+air*echo*.85;
}

// Traveling resonance fronts: continuous phase and localized onset impulses.
vec2 journey_field_wave(float r) {
    float pressure=journey_pressure();
    float decay=exp(-r*.24),phase=r*5.-u_star_time*.22;
    vec2 wave=vec2(sin(phase),5.*cos(phase)-.24*sin(phase))*.09*pressure*decay;
    for(int i=0;i<8;i++) {
        vec4 event=u_stellar_events[i];float age=u_drift_time-event.x;
        if(event.w<=0. || age<0. || age>3.2)continue;
        float d=r-(.4+age*2.7),envelope=exp(-abs(d)*1.1-age*.85)*event.w;
        wave+=vec2(sin(d*7.),7.*cos(d*7.)-1.1*sign(d)*sin(d*7.))*.12*envelope;
    }
    float limited=tanh(wave.x/.28);
    return vec2(.28*limited,wave.y*(1.-limited*limited));
}
vec3 journey_field_shape(vec2 point) {
    float r2=dot(point,point),r=sqrt(r2);
    float height=-.18+1.5*(1.-1./(1.+r2*.9));
    vec2 gradient=2.7*point/pow(1.+r2*.9,2.);
    for(int i=0;i<8;i++) {
        if(i>=u_journey_count)break;
        vec2 delta=point-u_journey_centers[i].xz;float dip=.11*exp(-dot(delta,delta)*7.);
        height-=dip;gradient+=delta*dip*14.;
    }
    vec2 wave=journey_field_wave(r);height+=wave.x;gradient+=point/max(r,.01)*wave.y;
    return vec3(height,gradient);
}
// Reusable translucent curved field; solar pigments provide its local identity.
vec4 journey_gravity(vec3 eye,vec3 ray) {
    if(u_gravity_well<=0. || abs(ray.y)<.001 || length(eye)>100.)return vec4(0);
    if(ray.y>-.025)return vec4(0);
    float lo=max(.001,(1.65-eye.y)/ray.y),hi=(-1.40-eye.y)/ray.y;
    if(hi<=lo)return vec4(0);
    float t=clamp((.6-eye.y)/ray.y,lo,hi);
    for(int k=0;k<8;k++) {
        vec3 point=eye+ray*t;float r2=dot(point.xz,point.xz);
        vec3 shape=journey_field_shape(point.xz);float height=shape.x;vec2 gradient=shape.yz;
        float residual=point.y-height;
        if(abs(residual)<.0005)break;
        if(residual>0.)lo=t;else hi=t;
        float derivative=ray.y-dot(gradient,ray.xz);
        float next=abs(derivative)>.015 ? t-residual/derivative : (lo+hi)*.5;
        t=next>lo && next<hi ? next : (lo+hi)*.5;
    }
    if(t<=0. || t>50.)return vec4(0);
    vec3 point=eye+ray*t;float r2=dot(point.xz,point.xz),radius=sqrt(r2);
    vec2 slope=journey_field_shape(point.xz).yz;float local_depth=0.;
    for(int i=0;i<8;i++) {
        if(i>=u_journey_count)break;
        vec3 center=journey_planet_center(u_journey_planets[i],i);vec2 delta=point.xz-center.xz;
        float dip=exp(-dot(delta,delta)*7.);local_depth+=dip;
    }
    vec3 normal=normalize(vec3(-slope.x,1.,-slope.y));
    vec3 key=normalize(vec3(-.7,.35,.35));
    float diffuse=.15+.85*max(0.,dot(normal,key));
    float sheen=pow(max(0.,dot(reflect(-key,normal),-ray)),24.);
    float texture=journey_fbm(point.xz*1.2+vec2(u_star_time*.009,0.));
    float extent=1.-smoothstep(4.,7.,radius);
    vec3 pigment=mix(journey_pigment(5),journey_pigment(3),texture*.65);
    vec2 grid_coordinate=point.xz*.62;
    vec2 spacing=abs(fract(grid_coordinate+.5)-.5);
    vec2 line=1.-smoothstep(vec2(.0015),vec2(.0015)+max(vec2(.001),fwidth(grid_coordinate)*.7),spacing);
    float grid=max(line.x,line.y);
    float glancing=pow(1.-max(0.,dot(normal,-ray)),3.);
    // Broad normal-dependent light reveals the bowl; no contour/grid overlay.
    float soft_reflection=pow(max(0.,dot(reflect(-key,normal),-ray)),7.);
    float depth_shadow=(1.-.40*exp(-r2*.85))*(1.-.35*min(1.,local_depth));
    vec3 material=pigment*(.07+.42*diffuse)*(.82+.18*texture)*depth_shadow
        +mix(journey_pigment(0),journey_pigment(5),.65)*soft_reflection*.22
        +pigment*glancing*.14;
    float resonance=0.;
    for(int e=0;e<8;e++) {
        vec4 event=u_stellar_events[e];float age=u_drift_time-event.x;
        if(event.w<=0. || age<0. || age>3.2)continue;
        float front=radius-(.4+age*2.7);
        resonance+=exp(-front*front*55.-age*.65)*event.w;
    }
    material+=mix(journey_pigment(0),journey_pigment(7),texture)*min(resonance,1.5)*1.15;
    // Thin local orbital trails terminate behind the actual moving body.
    for(int i=0;i<8;i++) {
        if(i>=u_journey_count)break;
        vec3 center=journey_planet_center(u_journey_planets[i],i);
        float angle=atan(point.z,point.x)-atan(center.z,center.x);angle=atan(sin(angle),cos(angle));
        float radial=radius-length(center.xz);
        float trail=exp(-radial*radial*90.)*exp(-max(-angle,0.)*5.)*(1.-smoothstep(-.04,.12,angle));
        material+=journey_body_pigment(5,i)*trail*.12;
    }
    float visible=smoothstep(.01,.12,abs(ray.y))*extent;
    return vec4(material,visible*u_gravity_well*.57);
}

vec3 journey_system(vec3 eye,vec3 ray,vec3 background) {
    vec3 local=(eye-u_journey_anchor.xyz)/u_journey_anchor.w;
    float closest=1e9;
    vec3 light=background;
    vec3 sun=journey_pigment(0);
    float sun_radius=u_journey_stars.x*(1.+.065*journey_pressure()+.045*u_impact);
    float along=dot(-local,ray);
    float offset=length(cross(-local,ray));
    // The selected sun stays visible as the same bright point during approach.
    float pixel=max(.01,along*1.5/u_resolution.y);
    float glow=exp(-offset*offset/max(.24,pixel*pixel*2.));
    if(along>0.)light+=sun*glow*(.25+.23*u_scale);
    // The same primary sun is unmistakable before camera acceleration. Its
    // angular nursery glow closes into the actual solar sphere, never a reticle.
    if(along>0. && u_journey.x>.5 && u_journey.x<2.5) {
        float acquired=u_journey.x<1.5 ? smoothstep(.02,.35,u_journey.y) : 1.;
        float angular=offset/max(along,.01);
        float nucleus=1.-smoothstep(.008,.012,angular);
        float corona=exp(-angular*angular*1200.);
        light+=sun*(nucleus*.9+corona*.58)*acquired;
    }
    vec4 field=journey_gravity(local,ray);light=mix(light,field.rgb,field.a);
    for(int star=0;star<2;star++) {
        if(star==1 && u_journey_stars.y<=0.)continue;
        vec3 center=star==0 ? vec3(0) : journey_companion();
        float radius=star==0 ? sun_radius : u_journey_stars.y*(1.+.05*journey_pressure());
        vec3 tint=star==0 ? sun : mix(sun,journey_pigment(5),.80);
        float star_along=dot(center-local,ray);
        vec3 perpendicular=local+ray*star_along-center;
        float radial=length(perpendicular)/radius;
        if(star_along>0. && radial>1. && radial<4.) {
            light+=tint*exp(-pow(radial-1.,2.)*6.)*(.04+.08*journey_pressure());
            vec3 view_right=normalize(cross(ray,vec3(0,1,0))),view_up=cross(view_right,ray);
            float theta=atan(dot(perpendicular,view_up),dot(perpendicular,view_right));
            vec2 circular=vec2(cos(theta),sin(theta));
            float sector=smoothstep(.57,.76,journey_fbm(circular*3.+float(star)*13.));
            float arch=1.04+.23*pow(.5+.5*sin(theta*7.+u_star_time*.12+float(star)),2.);
            float corona=exp(-abs(radial-arch)*32.)*sector;
            light+=mix(tint,journey_pigment(7),float(star)*.25)*corona*(.40+.70*journey_pressure());
            float plume=0.;
            for(int e=0;e<8;e++) {
                vec4 event=u_stellar_events[e];float age=u_drift_time-event.x;
                if(age<0. || age>3. || event.w<=0.)continue;
                float angle=atan(perpendicular.z,perpendicular.x);
                float direction=exp(-abs(sin(angle-event.y-float(star)))*9.);
                float arch=1.07+.18*sin(angle*3.-u_star_time*.08+float(star));
                plume+=exp(-abs(radial-arch)*24.)*direction*exp(-age*.6)*event.w;
            }
            light+=mix(tint,journey_pigment(7),.25)*plume*(.65+1.7*u_impact);
        }
        if(u_journey.w>.95 && star==0 && star_along>0.) {
            vec3 axis=normalize(vec3(cos(u_star_time*.48)*.72,.70,sin(u_star_time*.48)*.72));
            vec3 origin=local-center;float projection=dot(ray,axis);
            float ray_t=(dot(origin,axis)*projection-dot(origin,ray))/max(.03,1.-projection*projection);
            vec3 point=origin+ray*max(0.,ray_t);float axial=dot(point,axis);
            float across=length(point-axis*axial);
            float beam=exp(-across*across/pow(.035+abs(axial)*.10,2.))
                *smoothstep(radius*.7,radius*1.3,abs(axial))*exp(-axial*axial*.22);
            vec3 beam_color=mix(journey_pigment(5),journey_pigment(0),.18);
            light+=beam_color*beam*(.6+.25*journey_pressure());
        }
        float distance=journey_sphere(local,ray,center,radius);
        if(distance>=closest)continue;
        vec3 normal=normalize(local+ray*distance-center);
        vec3 weights=pow(abs(normal),vec3(4.));weights/=max(.001,weights.x+weights.y+weights.z);
        float activity=journey_echo(normal,float(star)+13.);
        vec3 convection=normal+vec3(sin(normal.y*9.+u_star_time*.10),sin(normal.z*8.-u_star_time*.08),sin(normal.x*11.+u_star_time*.07))*(.07+.06*activity);
        float cell_scale=star==0 ? 3.8 : 5.2;
        float cells=journey_fbm(convection.yz*cell_scale+u_star_time*.025)*weights.x+journey_fbm(convection.xz*cell_scale-u_star_time*.022)*weights.y+journey_fbm(convection.xy*cell_scale+u_star_time*.018)*weights.z;
        float spots=journey_fbm(convection.xz*5.+convection.y*3.);
        float spot=smoothstep(.65,.78,spots)*(1.-smoothstep(.12,.65,abs(normal.y)));
        float limb=.38+.62*pow(max(0.,dot(normal,-ray)),.45);
        float granules=smoothstep(.27,.73,cells);
        float hot=smoothstep(.57,.75,cells);
        vec3 cooler=mix(tint,journey_pigment(1),.38);
        vec3 warmer=mix(tint,vec3(1),star==0 ? .20 : .48);
        vec3 photosphere=mix(cooler*.35,warmer*(.52+.68*granules),granules)*limb;
        photosphere=mix(photosphere,cooler*.12*limb,spot*.72);
        photosphere+=mix(tint,vec3(1),.65)*hot*.20*limb;
        photosphere+=mix(tint,journey_pigment(7),.45)*activity*.85;
        photosphere+=tint*journey_pressure()*(.18+.32*granules);
        if(u_journey.w>.95 && star==0) {
            vec3 axis=normalize(vec3(cos(u_star_time*.48)*.72,.70,sin(u_star_time*.48)*.72));
            float pole=pow(abs(dot(normal,axis)),14.);
            photosphere=mix(tint,journey_pigment(5),.72)*(.20+.55*granules)*limb
                +mix(journey_pigment(5),vec3(1),.65)*pole*(1.3+.3*activity);
        }
        light=photosphere/(vec3(1.)+photosphere*.32);closest=distance;
    }
    for(int i=0;i<8;i++) {
        if(i>=u_journey_count)break;
        vec4 spec=u_journey_planets[i];vec3 center=journey_planet_center(spec,i);
        float distance=journey_sphere(local,ray,center,spec.y*(1.+.10*journey_pressure()+.065*u_impact));
        if(distance<closest) {
            vec3 normal=normalize(local+ray*distance-center);
            float diffuse=max(0.,dot(normal,normalize(-center)));
            float rim=pow(1.-max(0.,dot(normal,-ray)),3.);
            float fill=u_journey_stars.y>0. ? max(0.,dot(normal,normalize(journey_companion()-center)))*.22 : 0.;
            float illumination=spec.w<.5 ? .65+.35*diffuse+fill : .34+.82*diffuse+fill;
            light=journey_surface(normal,spec,float(i))*illumination
                +journey_pigment(5)*rim*(.10+.13*u_sparkle)*(.35+.65*diffuse);
            if(spec.w>.5 && spec.w<1.5) {
                vec3 spin_normal=normal;float spin=u_star_time*(.027+u_journey_traits[i].w*.012)*(1.+float(i)*.07);
                spin_normal.xz=mat2(cos(spin),-sin(spin),sin(spin),cos(spin))*spin_normal.xz;
                vec2 terrain=vec2(spin_normal.x+spin_normal.y*.43,spin_normal.z+spin_normal.y*.71)*2.2;
                vec2 curl=vec2(journey_fbm(terrain*3.+spec.z),journey_fbm(terrain*3.-u_star_time*.005+13.))-.5;
                float land=smoothstep(.47,.54,journey_fbm(terrain*(1.2+u_journey_traits[i].w*.35)+curl*.4+spec.z));
                vec3 water_normal=normalize(normal+vec3(sin(terrain.x*29.+u_star_time*.1),cos(terrain.y*23.),sin(terrain.y*17.-u_star_time*.1))*(.015+.10*journey_pressure()));
                float glint=pow(max(0.,dot(reflect(-normalize(-center),water_normal),-ray)),35.);
                light+=mix(journey_pigment(0),vec3(1),.65)*glint*(1.-land)*.9;
                float cloud_distance=journey_sphere(local,ray,center,spec.y*1.027);
                vec3 cloud_normal=normalize(local+ray*cloud_distance-center);
                vec2 weather=vec2(cloud_normal.x+cloud_normal.y*.43,cloud_normal.z+cloud_normal.y*.71)*2.2;
                weather.x+=u_star_time*.026;
                weather+=curl*.32;
                float hurricane=atan(weather.y-.2,sin(weather.x+.4));
                weather+=vec2(sin(hurricane+u_star_time*.02),cos(hurricane+u_star_time*.02))*.12;
                float vapor=journey_fbm(weather*5.5+curl*.6);
                float fibers=noise(weather*28.+vapor*4.);
                float cloud=smoothstep(.48,.77,vapor)*smoothstep(.18,.70,fibers);
                float thickness=.42+.35*noise(weather*13.-u_star_time*.013);
                vec3 cloud_color=mix(journey_pigment(5),vec3(1),.70)*(.12+.85*max(0.,dot(cloud_normal,normalize(-center))))*(.72+.28*fibers);
                light=mix(light,cloud_color,cloud*thickness);
                light+=journey_pigment(5)*pow(1.-max(0.,dot(cloud_normal,-ray)),5.)*.065;
            }
            closest=distance;
        }
        // A local inclined ring shares sphere depth: nearer solid bodies hide
        // the far band; nearer dust lies over the front hemisphere.
        if(spec.w>2.5 && spec.w<3.5) {
            vec3 axis=normalize(vec3(.25*sin(spec.z),1.,.28*cos(spec.z)));
            float denom=dot(ray,axis);
            if(abs(denom)>.001) {
                float ring_t=dot(center-local,axis)/denom;
                vec3 point=local+ray*ring_t-center;
                float radius=length(point)/spec.y;
                if(ring_t>0. && ring_t<closest && radius>1.3 && radius<2.45) {
                    float bands=.48+.32*journey_fbm(vec2(radius*18.,spec.z))+.20*sin(radius*21.);
                    float edge=smoothstep(1.3,1.36,radius)*(1.-smoothstep(2.36,2.45,radius));
                    float gap=smoothstep(.012,.045,abs(radius-1.94));
                    float shadow=length(cross(center-(local+ray*ring_t),normalize(-center)));
                    float shade=.25+.75*smoothstep(spec.y*.82,spec.y*1.25,shadow);
                    light=mix(light,journey_body_pigment(4,i)*(.45+.50*bands)*shade,edge*gap*(.38+.48*bands));
                    closest=ring_t;
                }
            }
        }
        if(spec.w>1.5 && spec.w<3.5 && u_journey_traits[i].z>.3) {
            float orbit=u_star_time*.18+float(i)*2.;
            vec3 moon=center+vec3(cos(orbit),.2*sin(orbit),sin(orbit))*spec.y*3.;
            float distance=journey_sphere(local,ray,moon,spec.y*.24);
            if(distance<closest) {
                vec3 normal=normalize(local+ray*distance-moon);
                light=journey_pigment(1)*(.06+.75*max(0.,dot(normal,normalize(-moon))));
                closest=distance;
            }
        }
    }
    return light;
}

vec4 journey_warp(vec2 p,float strength) {
    if(strength<=0.)return vec4(0);
    float radius=length(p), angle=atan(p.y,p.x);
    float speed=.9+strength*3.8+.8*journey_pressure();
    float travel=u_star_time*.75;
    vec3 light=vec3(0);float extinction=0.;
    // Three sparse peripheral cloud banks at different depths, no contour network.
    for(int i=0;i<3;i++) {
        float id=float(i),z=1.-fract(travel*.19+id*.31);
        float r=radius*(.8+z*2.4+id*.25);
        float turn=angle+log(radius+.12)*.42+id*2.1+travel*.025;
        vec2 circular=vec2(cos(turn),sin(turn));
        float sector=pow(.5+.5*cos(turn),9.);
        float cloud=journey_fbm(circular*2.2+vec2(r*3.-travel*speed,id*17.));
        float wall=smoothstep(.24,.45,r)*(1.-smoothstep(.9,1.6,r))*sector;
        float body=wall*smoothstep(.30,.72,cloud);
        vec3 pigment=i==0 ? journey_pigment(5) : i==1 ? journey_pigment(0) : journey_pigment(7);
        float passage_fade=smoothstep(0.,.12,z)*(1.-smoothstep(.85,1.,z));
        float luminous_ridge=smoothstep(.43,.59,cloud)*(1.-smoothstep(.70,.84,cloud));
        float depth_light=.7+1.1*(1.-z);
        light+=pigment*wall*passage_fade*(body*(.16+.40*cloud)+luminous_ridge*.24)
            *depth_light/(1.+id*.30);
        extinction+=body*passage_fade*(.12+.12*(1.-z));
    }
    // Long perspective tails, unequal distances, forward acceleration.
    for(int i=0;i<72;i++) {
        float id=float(i),seed=hash(vec2(id+7.,u_journey.z+13.));
        float z=.08+fract(seed-travel*(.65+seed*.45+journey_pressure()*.95))*4.8;
        vec2 xy=(vec2(hash(vec2(id,17.)),hash(vec2(id,43.)))-.5)*2.8;
        vec2 head=xy/z,tail=xy/(z+.65+strength*2.7+journey_pressure());
        vec2 segment=head-tail;float u=clamp(dot(p-tail,segment)/max(dot(segment,segment),.0001),0.,1.);
        vec2 delta=p-(tail+segment*u);
        float width=.00065+.0012/(z+.35);
        float trail=exp(-dot(delta,delta)/(width*width))*(.15+.85*u);
        light+=mix(journey_pigment(5),journey_pigment(0),seed)*trail*(.12+.20/(z*z))*(1.+1.2*u_impact);
    }
    float channel=smoothstep(.055,.18,radius);
    return vec4(light*strength*channel,clamp(extinction,0.,.40)*strength*channel);
}

vec3 isolated_galaxy_scene(vec2 p) {
    mat3 camera=journey_view(u_journey_eye,u_journey_target,u_journey_bank);
    vec3 ray=normalize(camera*vec3(p*.95,1.));
    float phase=u_journey.x,progress=u_journey.y;
    float entry=phase>1.5 && phase<2.5 ? smoothstep(.10,.48,progress) : (phase>2.5 ? 1. : 0.);
    vec3 light=vec3(0);
    if(phase<4.5 || progress<.43) {
        if(entry>=.999)light=journey_arm_depth(u_journey_eye,ray,u_journey_galaxy);
        else {
            light=journey_galaxy(u_journey_eye,ray,u_journey_galaxy,false);
            if(entry>0.)light=mix(light,journey_arm_depth(u_journey_eye,ray,u_journey_galaxy),entry);
        }
        if(phase<2.5)light+=stellar_layers(p)*vec3(.6);
        light=journey_system(u_journey_eye,ray,light);
    }
    // The next destination is an actual generated galaxy, visible as a distant
    // object during the system tour and used unchanged at the next arrival.
    vec3 heading=transpose(camera)*u_journey_heading;
    float warp=phase>4.5 ? smoothstep(.05,.3,progress)*(1.-smoothstep(.80,1.,progress)) : 0.;
    float size=phase>4.5 ? exp(mix(log(.13),0.,smoothstep(0.,1.,progress))) : .13;
    if(heading.z>0. && phase>3.5) {
        vec2 center=heading.xy/(heading.z*.95);
        vec2 local=(p-center)/size;
        mat3 entry=journey_view(u_journey_next_eye,vec3(0),0.);
        vec3 target_ray=normalize(entry*vec3(local*.95,1.));
        vec3 next=journey_galaxy(u_journey_next_eye,target_ray,u_journey_next,true);
        float window=1.-smoothstep(1.3,1.8,length(local));
        float arrival=phase>4.5 ? smoothstep(.62,1.,progress) : 0.;
        light*=1.-(phase>4.5 ? smoothstep(.12,.42,progress) : 0.);
        light+=next*mix(window,1.,arrival);
    }
    vec4 passage=journey_warp(p,warp);
    light=light*(1.-passage.a)+passage.rgb;
    return light;
}


// Accepted depth composition shared by the isolated diagnostic and live takeover.
vec3 isolated_cosmic_scene(vec2 p, vec3 canvas, float canvas_mix, float assembly)
{
    float time = u_drift_time;
    float color_drive = canvas_mix * smoothstep(0.08, 0.65,
        clamp(0.45 * u_scale + 0.35 * u_flux + 0.20 * u_sparkle, 0.0, 1.0));
    vec3 scene = vec3(0.0);
    scene += cosmic_star_layer(p, 1.0) * effect(512);

    float radius = 0.30;
    vec3 light_dir = normalize(vec3(-0.5, 0.65, 1.0));
    // Inverted orientation requested in the references. Shared by all orbits.
    float angle = 0.28;
    float opening = 0.40;
    vec3 axis_u = vec3(cos(angle), sin(angle), 0.0);
    vec3 axis_v = vec3(-sin(angle) * opening, cos(angle) * opening,
        -sqrt(1.0 - opening * opening));
    vec2 plane = vec2(dot(p, axis_u.xy),
        dot(p, vec2(-sin(angle), cos(angle))) / opening);
    float ring_depth = plane.y * axis_v.z;
    float radial = length(plane);
    float aa = 1.5 / u_resolution.y;
    float band_mask = smoothstep(0.355, 0.355 + aa, radial)
        * (1.0 - smoothstep(0.61 - aa, 0.61, radial));
    float gap = 1.0 - 0.92 * (smoothstep(0.474, 0.478, radial)
        * (1.0 - smoothstep(0.491, 0.495, radial)));
    float banding = 0.52 + 0.25 * sin(radial * 370.0)
        + 0.12 * sin(radial * 910.0);
    vec3 ring_color = mix(u_planet_rings_on == 1 ? u_planet_rings[0] : vec3(0.31, 0.19, 0.40),
        u_planet_rings_on == 1 ? u_planet_rings[1] : vec3(0.93, 0.67, 0.39),
        0.5 + 0.5 * sin(radial * 46.0)) * banding;
    // Moons stir a short, colored wake in the dust. The wake is evaluated in
    // the shared orbital plane, so it follows the same path as each solid moon
    // without changing ring depth or body occlusion.
    float orbit_speed = (u_debug_state > 2.5 && u_debug_state < 3.5)
        ? 1.0 : 0.22;
    float dust_strength = (0.10 + 0.65 * clamp(u_sparkle, 0.0, 1.0)
        + 0.45 * clamp(u_flux, 0.0, 1.0)) * smoothstep(0.35, 0.90, assembly);
    vec3 dust_color = vec3(0.0);
    float dust = 0.0;
    float dust_near = 0.0;
    for (int dust_i = 0; dust_i < 3 && effect(2048) > 0.0; dust_i++)
    {
        float fi = float(dust_i);
        // Inner moons complete an orbit faster; outer moons drift more slowly.
        float phase = time * (0.52 - fi * 0.10) * orbit_speed + fi * 2.1;
        float orbit_radius = 0.43 + fi * 0.09;
        // Work in polar coordinates so the wake bends around the same orbital
        // curve as the ring instead of forming a straight tangent streak.
        float point_angle = atan(plane.y, plane.x);
        float angle_delta = atan(sin(point_angle - phase),
            cos(point_angle - phase));
        float radial_delta = radial - orbit_radius;
        float near_moon = exp(-(radial_delta * radial_delta / 0.0012
            + angle_delta * angle_delta / 0.0035));
        float halo = exp(-angle_delta * angle_delta / 0.018);
        float tail = exp(-max(-angle_delta, 0.0) * 1.7)
            * (1.0 - smoothstep(0.0, 0.22, angle_delta));
        float wake = exp(-radial_delta * radial_delta / 0.0018)
            * (0.44 * halo + 0.78 * tail);
        dust = max(dust, wake);
        dust_near = max(dust_near, near_moon);
        // Sample the same animated moon material at the trail's current
        // orbital angle, so the wake changes color with its parent moon.
        vec3 trail_normal = normalize(vec3(cos(point_angle),
            sin(point_angle), 0.72));
        vec3 tint = cosmic_moon_material(trail_normal, dust_i, time);
        dust_color += tint * wake;
    }
    dust_color /= max(dust, 0.0001);
    // Near the moon the ring reads dense and painted; the longer tail fades
    // continuously behind it instead of becoming a second opaque ring.
    ring_color = mix(ring_color,
        dust_color * (0.72 + 0.90 * dust_near + 0.35 * banding),
        clamp(dust * (0.35 + 1.25 * dust_strength), 0.0, 0.95));
    // Planet casts a real directional shadow onto the ring plane.
    vec3 ring_point = axis_u * plane.x + axis_v * plane.y;
    float along_light = dot(-ring_point, light_dir);
    float shadow_distance = length(ring_point + light_dir * max(along_light, 0.0));
    float ring_shadow = along_light > 0.0
        ? smoothstep(radius - 0.015, radius + 0.015, shadow_distance) : 1.0;
    ring_color *= mix(0.18, 1.0, ring_shadow);
    ring_color = mix(ring_color, mix(ring_color, canvas, 0.38)
        * (0.85 + 0.3 * clamp(u_sparkle, 0.0, 1.0)), canvas_mix);
    ring_color = planet_palette(cosmic_vivid_material(ring_color, color_drive));
    if (u_planet_rings_on == 1) ring_color *= u_planet_rings[2];
    band_mask *= smoothstep(0.35, 0.90, assembly) * effect(1024);

    float closest = cosmic_sphere_depth(p, vec3(0.0), radius);
    if (closest > -99.0)
    {
        vec3 normal = vec3(p, closest) / radius;
        // Rotate a sphere-space surface, avoiding flat screen-space texture.
        float spin = time * 0.035;
        vec3 surface = vec3(cos(spin) * normal.x + sin(spin) * normal.z,
            normal.y, -sin(spin) * normal.x + cos(spin) * normal.z);
        float terrain = fbm(surface.xy * 3.2 + surface.z * vec2(1.7, -2.1));
        float land = smoothstep(0.46, 0.54, terrain);
        vec3 albedo = mix(vec3(0.025, 0.12, 0.32),
            mix(vec3(0.16, 0.42, 0.28), vec3(0.72, 0.39, 0.22), terrain), land);
        float clouds = smoothstep(0.57, 0.72,
            fbm(surface.xy * 6.0 + surface.z * 2.0 + vec2(time * 0.006, 0.0)));
        albedo = mix(albedo, vec3(0.70, 0.79, 0.92), clouds * 0.65);
        // Opaque material substitution, not an overlay on the final scene.
        albedo = mix(albedo, sqrt(clamp(canvas, 0.0, 1.0)) * 0.95, canvas_mix);
        albedo = planet_palette(cosmic_vivid_material(albedo, color_drive));
        if (u_planet_surface_on == 1) albedo *= u_planet_surface;
        float diffuse = max(dot(normal, light_dir), 0.0);
        scene = albedo * (0.10 + 0.90 * diffuse);
        scene += vec3(0.10, 0.30, 0.65) * pow(1.0 - normal.z, 3.0)
            * (0.15 + 0.55 * diffuse);
    }
    if (band_mask > 0.0 && ring_depth > closest)
    {
        scene = mix(scene, ring_color, band_mask * gap);
        // Empty gap remains transparent for bodies behind it.
        if (band_mask * gap > 0.5) closest = ring_depth;
    }

    // Moon shading is independent of opacity; nearest surface wins.
    for (int i = 0; i < 3 && effect(2048) > 0.0; i++)
    {
        float fi = float(i);
        // Keep the fast orbit only in the geometry diagnostic.
        float orbit_speed = (u_debug_state > 2.5 && u_debug_state < 3.5)
            ? 1.0 : 0.22;
        // Match the dust wake's orbital timing so it remains attached.
        float phase = time * (0.52 - fi * 0.10) * orbit_speed + fi * 2.1;
        float orbit_radius = 0.43 + fi * 0.09;
        vec3 center = orbit_radius * (axis_u * cos(phase) + axis_v * sin(phase));
        float moon_radius = (0.025 + fi * 0.006) * smoothstep(0.65, 1.0, assembly);
        float depth = cosmic_sphere_depth(p, center, moon_radius);
        if (moon_radius > 0.0001 && depth > closest)
        {
            vec3 normal = (vec3(p, depth) - center) / moon_radius;
            float diffuse = max(dot(normal, light_dir), 0.0);
            float toward_light = dot(-center, light_dir);
            float miss = length(center + light_dir * max(toward_light, 0.0));
            float eclipse = toward_light > 0.0
                ? smoothstep(radius - 0.02, radius + 0.02, miss) : 1.0;
            scene = cosmic_moon_material(normal, i, time) * (0.12 + 0.88 * diffuse * eclipse);
            closest = depth;
        }
    }
    return scene;
}

// Long straights, then a committed turn. The next hall continues; it does not dead-end.
// mod keeps the pattern stable no matter how long the walk runs.
float geo_end_turn(float seg)
{
    float s = mod(seg, 8.0);
    if (s < 3.0) return 0.0;
    if (s < 4.0) return 1.0;
    if (s < 7.0) return 0.0;
    return -1.0;
}

vec3 geo_swatch(float v, float slot)
{
    float s = mod(slot, 10.0);
    if (s < 0.5) return mix(geometric_dream_palette(v), gold_sun_palette(v), 0.42);
    if (s < 1.5) return mix(ocean_palette(v), electric_blue_palette(v), 0.50);
    if (s < 2.5) return mix(crimson_gold_palette(v), ember_palette(v), 0.48);
    if (s < 3.5) return mix(neon_forest_palette(v), teal_amber_palette(v), 0.46);
    if (s < 4.5) return mix(lavender_pearl_palette(v), aurora_palette(v), 0.50);
    if (s < 5.5) return mix(ink_burgundy_palette(v), fire_palette(v), 0.40);
    if (s < 6.5) return mix(crystal_palette(v), electric_blue_palette(v), 0.45);
    if (s < 7.5) return mix(teal_amber_palette(v), gold_sun_palette(v), 0.40);
    if (s < 8.5) return mix(geometric_dream_palette(v), neon_forest_palette(v), 0.48);
    return mix(ember_palette(v), lavender_pearl_palette(v), 0.42);
}

vec3 geo_palette(float v)
{
    float phase = u_drift_time * 0.035;
    float slot = floor(phase);
    float fade = smoothstep(0.72, 1.0, fract(phase));
    vec3 pigment = mix(geo_swatch(v, slot), geo_swatch(v, slot + 1.0), fade);
    return u_corridor_inlay_on == 1 ? pigment * u_corridor_inlay : pigment;
}

// Columns of glyphs falling from the top of a surface toward the bottom.
// Thin columns, not a filled grid.
vec3 geo_rain(float across, float down01, vec3 tint)
{
    float spacing = 0.42;
    float across_w = mod(across, 18.0);
    float col = floor(across_w / spacing);
    float local = across_w - col * spacing;
    float mask = 1.0 - smoothstep(0.02, 0.07, abs(local - spacing * 0.5));
    float speed = 0.35 + hash(vec2(col, 2.2)) * 1.5;
    float head = fract(u_drift_time * speed + hash(vec2(col, 5.5)));
    float down = clamp(down01, 0.0, 1.0);
    float trail = head - down;
    float row = floor(down * 16.0);
    float glyph = step(0.42, hash(vec2(col, row + floor(u_drift_time * speed))));
    float body = glyph * step(0.0, trail) * exp(-trail * 3.2);
    float lead = exp(-abs(down - head) * 24.0);
    vec3 pigment = u_corridor_glyphs_on == 1 ? tint * u_corridor_glyphs : tint;
    return pigment * (body + lead * 1.4) * mask;
}

float geo_width(float travel)
{
    float bay = travel / 3.4;
    float w0 = mix(0.38, 1.12, hash(vec2(floor(bay), 1.2)));
    float w1 = mix(0.38, 1.12, hash(vec2(floor(bay) + 1.0, 1.2)));
    return mix(w0, w1, smoothstep(0.15, 0.85, fract(bay)));
}

float geo_tall(float travel)
{
    float bay = travel / 3.4;
    float h0 = mix(0.62, 1.55, hash(vec2(floor(bay), 4.8)));
    float h1 = mix(0.62, 1.55, hash(vec2(floor(bay) + 1.0, 4.8)));
    return mix(h0, h1, smoothstep(0.15, 0.85, fract(bay)));
}

// Trace once, then evaluate ZeraWave's existing field in this surface domain.
// No second field evaluation or screen-space texture is required.
struct GeometricSurface {
    vec2 uv;
    float distance;
    float kind;
    float height;
};

GeometricSurface geometric_surface(vec2 p, float air_vault)
{
    float fluxv = clamp(u_flux, 0.0, 1.0);
    float spark = clamp(u_sparkle, 0.0, 1.0);
    float hit = clamp(u_impact, 0.0, 1.0);
    float walk = max(u_time, 0.0) * 1.05 + u_drift_time * 0.16;
    const float SPAN = 8.0;
    float seg = floor(walk / SPAN);
    float local = walk - seg * SPAN;
    float next_turn = geo_end_turn(seg);
    if(air_vault>0.)next_turn=0.;
    float turning = step(0.5, abs(next_turn));
    float turn_u = turning * smoothstep(SPAN - 3.4, SPAN - 0.04, local);
    float yaw = next_turn * 1.5707963 * turn_u;
    if(air_vault>0.)yaw=atan(.98*cos(walk*.105));
    float cs = cos(yaw);
    float sn = sin(yaw);
    float w_here = geo_width(walk);
    float w_next = w_here;
    float h_next = geo_tall(walk);
    // Advance into the junction before crossing the inner corner. Early
    // lateral motion can put the camera inside the pressure-bowed side wall.
    float slide = next_turn * smoothstep(.45,1.0,turn_u) * (w_here + w_next);
    // Move forward with the turn, keeping the opening ahead of the camera.
    float junction_approach = (SPAN - local) * smoothstep(0.0, 0.55, turn_u);
    vec3 ro = vec3(slide, 0.48, junction_approach);
    // Keep headroom in low bays; their floor and ceiling bow symmetrically.
    ro.y=min(ro.y,.5*min(h_next,geo_tall(walk+ro.z)));
    vec3 rd = normalize(vec3(p.x * 0.90, (p.y - 0.10) * 0.72, 1.12));
    rd = vec3(cs * rd.x + sn * rd.z, rd.y, -sn * rd.x + cs * rd.z);
    float bass = clamp(u_scale, 0.0, 1.0);
    float drive = max(hit, max(fluxv * 0.85, bass));
    float flex = smoothstep(0.34, 0.86, drive);
    // Pressure animates the room without pinching the chorus into a slit.
    float amp = flex * (0.08 + 0.14 * drive) + hit * flex * 0.04;
    float corner = SPAN - local;
    float best_t = 80.0;
    float kind = 0.0;
    vec3 hp = ro;
    float march_t = 0.04;
    float lo = 0.0;
    float hi = 0.0;
    int refinement = 0;
    for (int step_i = 0; step_i < 80; step_i++)
    {
        float t = march_t;
        vec3 q = ro + rd * t;
        // Air follows a smooth centerline with a maximum heading near 45 degrees.
        if(air_vault>0.)q.x-=9.333333*(sin((walk+q.z)*.105)-sin(walk*.105));
        // Axial distance, not ray length: adjacent pixels share one wall.
        float side = turning * step(w_here * 0.25, q.x * next_turn)
            * step(abs(q.z - corner), w_next + 0.35);
        float along = walk + mix(q.z, corner + q.x * next_turn, side);
        float base_w = geo_width(along);
        float base_h = geo_tall(along);
        float slow = sin(along * 0.26 + u_drift_time * 0.10);
        float fast = sin(along * (0.85 + fluxv * 1.35) + u_drift_time * 0.48);
        float wave = clamp(
            slow * mix(0.82, 0.28, fluxv) + fast * mix(0.08, 0.62, fluxv),
            -1.0, 1.0
        );
        float bow = amp * wave;
        float hit_kind = 0.0;
        float in_side = turning
            * step(w_here * 0.25, q.x * next_turn)
            * step(abs(q.z - corner), w_next + 0.35);
        if (in_side > 0.5)
        {
            float nz = clamp((q.z - corner) / max(w_next, 0.2), -1.0, 1.0);
            float y01 = clamp(q.y / max(h_next, 0.2), 0.0, 1.0);
            float mid = cos(nz * 1.5707963);
            float floor_y = bow * mid;
            float ceil_y = h_next - bow * mid;
            if(air_vault>0.) {
                ceil_y=h_next*sqrt(max(.12,1.-nz*nz*.88))-bow*mid;
                floor_y=-4.;
            }
            float side_half = max(w_next - bow * sin(3.14159265 * y01), 0.14);
            if (q.y <= floor_y) hit_kind = 2.0;
            else if (q.y >= ceil_y) hit_kind = 3.0;
            else if (abs(q.z - corner) > side_half) hit_kind = 1.0;
            else if (q.x * next_turn > w_here + 22.0) hit_kind = 1.0;
        }
        else
        {
            float nx = clamp(q.x / max(base_w, 0.2), -1.0, 1.0);
            float y01 = clamp(q.y / max(base_h, 0.2), 0.0, 1.0);
            float mid = cos(nx * 1.5707963);
            float floor_y = bow * mid;
            float ceil_y = base_h - bow * mid;
            if(air_vault>0.) {
                ceil_y=base_h*sqrt(max(.12,1.-nx*nx*.88))-bow*mid;
                floor_y=-4.;
            }
            float halfw = max(base_w - bow * sin(3.14159265 * y01), 0.14);
            // The junction ends at the branch's outer wall, not its centerline.
            float blocked = turning
                * step(corner + max(w_next - bow, 0.14), q.z)
                * step(q.x * next_turn, w_here * 0.25);
            if (q.y <= floor_y) hit_kind = 2.0;
            else if (q.y >= ceil_y) hit_kind = 3.0;
            else if (blocked > 0.5) hit_kind = 1.0;
            else if (q.x < -halfw || q.x > halfw) hit_kind = 1.0;
        }
        if (hit_kind > 0.5)
        {
            best_t = t;
            hp = q;
            kind = hit_kind;
            if (refinement == 0) lo = max(0.0, t - 0.14);
            hi = t;
            refinement += 1;
        }
        else if (refinement > 0) { lo = t; refinement += 1; }
        if (refinement >= 6) break;
        march_t = refinement > 0 ? (lo + hi) * 0.5 : t + 0.14;
        if (march_t > 10.0) break;
    }
    float side = turning * step(w_here * 0.25, hp.x * next_turn)
        * step(abs(hp.z - corner), w_next + 0.35);
    float travel = walk + mix(hp.z, corner + hp.x * next_turn, side);
    float crossway = mix(hp.x, hp.z - corner, side);
    float tall = mix(geo_tall(travel), h_next, side);
    vec2 surface_uv = kind < 1.5 ? vec2(travel, hp.y)
        : vec2(travel, crossway);
    // One continuous weather coordinate around the arch avoids wall/roof seams.
    if(air_vault>0.)surface_uv.y=atan(hp.y-.3,crossway);
    return GeometricSurface(surface_uv, best_t, kind,
        clamp(hp.y / max(tall, 0.2), 0.0, 1.0));
}

// Original callers retain the accepted geometry exactly.
GeometricSurface geometric_surface(vec2 p) { return geometric_surface(p,0.); }

vec3 isolated_geometric_scene(GeometricSurface surface, vec3 canvas, float canvas_mix)
{
    float fluxv = clamp(u_flux, 0.0, 1.0);
    float spark = clamp(u_sparkle, 0.0, 1.0);
    float hit = clamp(u_impact, 0.0, 1.0);
    float best_t = surface.distance;
    float kind = surface.kind;
    vec3 scene = vec3(0.003, 0.004, 0.005);
    if (best_t < 70.0)
    {
        float travel = surface.uv.x;
        float v01 = surface.height;
        float down = (kind > 1.5 && kind < 2.5)
            ? fract(travel * 0.07)
            : (1.0 - v01);
        float across = (kind < 1.5) ? travel : surface.uv.y + travel * 0.15;
        // The actual field is the inlay, not a faint tint on a flat swatch.
        vec3 pigment = canvas / (0.30 + max(canvas.r, max(canvas.g, canvas.b)));
        vec3 tint = mix(geo_palette(0.62 + 0.28 * spark), pigment, 0.65);
        vec2 panel = surface.uv * vec2(0.70, 2.6);
        vec2 seam_distance = abs(fract(panel + 0.5) - 0.5);
        vec2 aa = max(fwidth(panel), vec2(0.002));
        vec2 seam = 1.0 - smoothstep(vec2(0.018), vec2(0.018) + aa, seam_distance);
        float joint = max(seam.x, seam.y);
        float vein_phase = surface.uv.y * 18.0
            + sin(travel * 1.7 + surface.uv.y * 3.0) * (1.5 + fluxv)
            + dot(canvas, vec3(2.0, 3.0, 1.0));
        float resolved = 1.0 - smoothstep(0.6, 2.0, fwidth(vein_phase));
        float veins = pow(0.5 + 0.5 * sin(vein_phase), 10.0) * resolved;
        float cavity = mix(0.48, 1.0, smoothstep(0.0, 0.17, min(seam_distance.x, seam_distance.y)));
        vec3 metal = mix(geo_palette(0.18) * 0.20,
            canvas * (2.10 + fluxv * 0.35), clamp(canvas_mix, 0.0, 1.0));
        metal *= cavity * (0.72 + 0.28 * veins);
        metal += pigment * veins * (0.06 + spark * 0.10);
        if (kind > 2.5) metal *= 0.72;
        if (kind > 1.5 && kind < 2.5) metal *= 0.85;
        vec3 rain = geo_rain(across, down, tint) * effect(256);
        float fog = exp(-best_t * 0.18);
        scene = metal * fog;
        scene += rain * (0.65 + spark * 0.35) * fog;
        // Sparse lit joints reveal perspective without filling negative space.
        float pulse = pow(0.5 + 0.5 * sin(travel * 2.0 - u_time * 1.8), 8.0);
        scene += tint * joint * (0.065 + hit * pulse * 0.20) * fog;
        float bay = floor(travel / 3.4);
        float open = 0.04 + 0.46 * hit;
        float door = step(0.55, hash(vec2(bay, 9.9)))
            * (1.0 - smoothstep(open, open + 0.05, abs(fract(travel * 0.35) - 0.5)))
            * (1.0 - smoothstep(0.12, 0.46, abs(v01 - 0.30)));
        door *= 1.0 - step(1.5, kind);
        vec3 door_col = canvas * 0.25 + tint * (0.04 + hit * 0.12);
        scene = mix(scene, door_col * fog, door * 0.85);
        float lip = 4.0 * door * (1.0 - door);
        scene += tint * lip * (0.12 + spark * 0.14) * fog;
    }
    return scene;
}

// Timed scaffold, not beat/phrase detection. One envelope drives contraction,
// material projection and release, so elements cannot jump independently.
float cosmic_handoff(float seconds, bool preview)
{
    float phase = mod(seconds, preview ? 40.0 : 140.0);
    return preview
        ? smoothstep(3.0, 11.0, phase) * (1.0 - smoothstep(24.0, 35.0, phase))
        : smoothstep(24.0, 44.0, phase) * (1.0 - smoothstep(88.0, 112.0, phase));
}

// Water occupies the gap between Cosmic visits; the original Cosmic clock
// and full dwell remain intact. This is a timed scaffold, not phrase detection.
float water_handoff(float seconds)
{
    if (seconds < 112.0) return 0.0;
    float phase = mod(seconds - 112.0, 140.0);
    return smoothstep(4.0, 14.0, phase) * (1.0 - smoothstep(32.0, 46.0, phase));
}

// Hold one form through each main-blend entrance and release. Advance only
// while Water is hidden, without resetting any animation/material clocks.
// Studio keeps its continuous five-form meld in compact 28-second slots.
float water_form_phase()
{
    if (u_debug_state < .5)
        return mod(floor(max(0.0,u_drift_time-112.0)/140.0)*4.0,5.0);
    return mod(u_drift_time,140.0)/28.0;
}

float water_currents_weight()
{
    if (u_directed == 1) return u_current_mix;
    if (u_debug_state > 12.5 && u_debug_state < 13.5) return 1.0;
    if (!(u_debug_state < .5 || (u_debug_state > 5.5 && u_debug_state < 6.5))) return 0.0;
    float phase = water_form_phase();
    float change = smoothstep(0.68, 1.0, fract(phase));
    if (phase >= 4.0) return 1.0 - change;
    if (phase >= 3.0) return change;
    return 0.0;
}

// Sea -> liquid dyes -> rain pool -> waterfall -> currents, with eased
// changes. Individual states hold one form for development and musical review.
vec4 water_forms()
{
    if (u_directed == 1) return u_water_mix;
    if (u_debug_state > 12.5 && u_debug_state < 13.5) return vec4(0.0);
    if (u_debug_state > 6.5) {
        if (u_debug_state < 7.5) return vec4(1,0,0,0);
        if (u_debug_state < 8.5) return vec4(0,1,0,0);
        if (u_debug_state < 9.5) return vec4(0,0,1,0);
        return vec4(0,0,0,1);
    }
    bool water_cycle = u_debug_state < .5 || (u_debug_state > 5.5 && u_debug_state < 6.5);
    int count = water_cycle ? 5 : 4;
    float phase = water_cycle ? water_form_phase() : mod(u_drift_time,112.0)/28.0;
    float change = smoothstep(0.68, 1.0, fract(phase));
    vec4 a = vec4(0.0), b = vec4(0.0);
    int index = int(floor(phase));
    if (index < 4) a[index] = 1.0;
    int next = (index + 1) % count;
    if (next < 4) b[next] = 1.0;
    return mix(a, b, change);
}

// Material coverage follows broad connected flow bands during a form handoff.
// Raw weights still drive the common camera/surface, so a border cannot tear
// geometry. Single forms retain exactly their accepted appearance.
vec4 water_coverage(vec2 p, out float currents)
{
    vec4 forms=water_forms();
    currents=water_currents_weight();
    if (max(max(forms.x,forms.y),max(forms.z,forms.w))>=1. || currents>=1.)
        return forms;
    float clock=u_drift_time*.06;
    float stream=sin(p.x*3.2+.6*sin(p.y*2.1-clock));
    vec4 territory=vec4(-p.y*.6,stream*.55,-stream*.35,
        p.y*1.5+.12*sin(p.x*3.1+clock));
    vec4 score=forms*forms*exp(territory*3.5);
    float current_score=currents*currents*exp((-stream*.55+p.y*.2)*3.5);
    float total=max(dot(score,vec4(1.))+current_score,1e-12);
    currents=current_score/total;
    return score/total;
}

// Seeded, bounded drop lifetimes. Every ring expands from a fixed impact
// location; neighbouring cells are evaluated so circles do not clip at seams.
float water_ripples(vec2 p)
{
    float rings = 0.0;
    vec2 cell = floor(p / 2.2);
    for (int y=-1; y<=1; y++) for (int x=-1; x<=1; x++) {
        vec2 id = cell + vec2(x,y);
        float seed = hash(id + 7.3);
        float age = mod(u_drift_time * 0.55 + seed * 3.0, 3.0);
        vec2 center = (id + vec2(0.18 + hash(id)*0.64, 0.18 + hash(id+4.7)*0.64))*2.2;
        float r = length(p-center);
        float rim = r - age * 0.72;
        rings += sin(rim * 34.0) * exp(-rim*rim*90.0)
            * smoothstep(0.0,0.12,age) * (1.0-smoothstep(1.0,2.6,age));
    }
    return rings;
}

// Elemental / Water: an oblique expanse of liquid. All coordinates are world
// coordinates; waves, normals and submerged material share the same current.
// This is a bounded procedural surface, not fluid simulation or frame history.
float water_storm()
{
    float drive = 0.60 * clamp(u_scale, 0.0, 1.0)
        + 0.25 * clamp(u_flux, 0.0, 1.0)
        + 0.15 * clamp(u_sparkle, 0.0, 1.0);
    return smoothstep(0.55, 0.88, drive);
}

vec2 water_current(vec2 p)
{
    float clock = u_time * 0.13 + u_drift_time * 0.025;
    vec2 q = p - vec2(0.32, -0.16) * clock;
    float shear = 0.22 + 0.32 * clamp(u_flux, 0.0, 1.0);
    q.x += sin(q.y * 0.62 + clock * 0.16) * shear;
    q.y += sin(q.x * 0.48 - clock * 0.12) * shear * 0.55;
    return q;
}

// Inverse flow coordinates: two smooth local twists bend one continuous
// stream. Longitudinal transport uses the existing positive integrated clock.
// There is no random reseeding, particle history or audio-scaled time.
vec2 currents_domain(vec2 p)
{
    float clock = u_time * .22 + u_drift_time * .028;
    float flux = clamp(u_flux, 0.0, 1.0);
    float bass = clamp(u_scale, 0.0, 1.0);
    p = mat2(.94, .342, -.342, .94) * p;
    p.x += .35 * sin(p.y * .48 + .12 * sin(clock * .13));
    for (int i=0; i<2; i++) {
        vec2 center = i == 0 ? vec2(-1.65,-.25) : vec2(2.2,1.8);
        vec2 offset = p - center;
        float reach = exp(-dot(offset,offset) * (.14 - bass*.025));
        float turn = (i == 0 ? 1.0 : -1.0) * reach
            * (3.8 + flux*.65 + .25*sin(clock*.11+float(i)*2.4));
        p = center + mat2(cos(turn),sin(turn),-sin(turn),cos(turn))*offset;
    }
    p.y -= clock;
    // Local, decaying pressure around one fixed disturbance site.
    vec2 event = p - vec2(.4,-clock+.7);
    p.x += sin(length(event)*5.0-clock*1.7)*exp(-dot(event,event)*.8)
        * clamp(u_impact,0.0,1.0)*.12;
    return p;
}

float water_height(vec2 p)
{
    vec2 q = water_current(p);
    float clock = u_time * 0.30 + u_drift_time * 0.045;
    float bass = clamp(u_scale, 0.0, 1.0);
    float flux = clamp(u_flux, 0.0, 1.0);
    // Incommensurate, mainly parallel waves: long pressure swells underneath
    // cross ripples. Audio changes amplitude, never multiplies elapsed time.
    float h = sin(dot(q, vec2(0.65, 1.12)) - clock * 0.62)
        * (0.045 + bass * 0.075);
    h += sin(dot(q, vec2(-1.1, 1.8)) - clock * 0.83 + 1.4)
        * (0.024 + bass * 0.032);
    h += sin(q.y * 4.2 + sin(q.x * 1.3 + clock * 0.2) - clock * 1.1)
        * (0.012 + flux * 0.019);
    h += sin(dot(q, vec2(5.8, 3.2)) - clock * 1.45)
        * (0.004 + clamp(u_sparkle, 0.0, 1.0) * 0.006);
    h += sin(dot(q, vec2(-8.5, 6.1)) - clock * 1.7) * 0.003;
    h += sin(q.y * 14.0 + sin(q.x * 3.2 - clock * 0.3) * 1.8 - clock * 1.9)
        * (0.0025 + flux * 0.003);
    h += sin(q.y * 23.0 + sin(q.x * 4.7 + clock * 0.2) * 2.4 - clock * 2.2)
        * 0.0018;
    // Intense passages lift fast, broad seas underneath the accepted ripples.
    // Phase speeds are constant: audio reveals their amplitude rather than
    // multiplying elapsed time and teleporting the surface on every beat.
    float storm = water_storm();
    float surge = dot(q, vec2(0.78, 1.15)) - clock * 2.8;
    float crossing = dot(q, vec2(-1.35, 1.7)) - clock * 3.4 + 1.1;
    h += storm * (0.28 * (sin(surge) + 0.22 * sin(2.0 * surge))
        + 0.17 * sin(crossing)
        + 0.055 * sin(q.y * 3.5 + sin(q.x * 1.1) - clock * 4.1));
    // Reuse the renderer's decaying event envelope in a bounded patch.
    float radius = length(p - vec2(0.8, 2.2));
    h += sin(radius * 10.0 - clock * 2.4) * exp(-radius * radius * 0.45)
        * clamp(u_impact, 0.0, 1.0) * 0.055;
    return h;
}

struct WaterSurface {
    vec2 position;
    vec2 material;
    vec3 normal;
    vec3 view;
    float distance;
};

// A distant environment belonging to this sea, sampled by both the view and
// the water reflection. Angular silhouettes suggest offshore basalt islets;
// they are not a second terrain renderer or a foreground obstruction.
vec3 water_environment(vec3 direction)
{
    float azimuth = atan(direction.x, direction.z);
    float elevation = direction.y / max(length(direction.xz), 0.001);
    float horizon_glow = exp(-abs(elevation - 0.015) * 9.0);
    vec3 sky = mix(color_tint(vec3(0.002, 0.003, 0.009),u_water_sky_on,u_water_sky[0]),
        color_tint(mix(lavender_pearl_palette(0.32), ocean_palette(0.38), 0.55) * 0.62,u_water_sky_on,u_water_sky[1]),
        horizon_glow);
    float dusk = exp(-pow((azimuth + 0.28) * 1.9, 2.0));
    sky += color_tint(teal_amber_palette(0.50),u_water_sky_on,u_water_sky[2]) * horizon_glow * dusk * 0.10;
    sky += color_tint(ember_palette(0.61),u_water_sky_on,u_water_sky[2]) * horizon_glow * horizon_glow * dusk * 0.14;
    // Horizontal, slowly traveling banks stay close to the horizon.
    vec2 cloud_q = vec2(azimuth * 3.0 - u_drift_time * 0.003,
        elevation * 17.0 + u_drift_time * 0.001);
    float mist = fbm(cloud_q + vec2(5.3, 1.7));
    sky += color_tint(lavender_pearl_palette(0.44),u_water_sky_on,u_water_sky[3]) * (0.15 + mist * 0.22)
        * exp(-abs(elevation - 0.025) * 22.0) * effect(32768);
    float left = exp(-pow((azimuth + 0.56) / 0.18, 2.0));
    float left_peak = exp(-pow((azimuth + 0.64) / 0.07, 2.0));
    float right = exp(-pow((azimuth - 0.51) / 0.25, 2.0));
    float ridge = (left * 0.070 + left_peak * 0.060 + right * 0.047)
        * (0.76 + 0.24 * noise(vec2(azimuth * 37.0, 8.1)));
    float aa = max(fwidth(elevation), 0.001);
    float island = smoothstep(0.003, 0.008, ridge)
        * (1.0 - smoothstep(ridge - aa, ridge + aa, elevation))
        * smoothstep(-0.012, 0.002, elevation);
    vec3 rock = vec3(0.004, 0.008, 0.018)
        + ocean_palette(0.24) * 0.22 * exp(-abs(elevation) * 32.0);
    float facets = noise(vec2(azimuth * 42.0 + elevation * 13.0,
        elevation * 28.0));
    rock += lavender_pearl_palette(0.29) * facets * 0.15
        * exp(-max(ridge - elevation, 0.0) * 22.0);
    if(u_water_sky_on==1)rock*=u_water_sky[4];
    sky += shooting_star_radiance(direction);
    sky = mix(sky, rock, island);
    return sky;
}

WaterSurface water_surface(vec2 p)
{
    vec3 origin = vec3(0.0, 2.8, -4.0);
    // Lift the view toward an open horizon; leave the accepted wave field and
    // its clocks unchanged. Near-horizontal rays meet atmospheric distance.
    vec4 forms = water_forms();
    float currents = water_currents_weight();
    float pool = forms.y + forms.z;
    vec3 ray = normalize(mix(vec3(p.x * 1.5, p.y * 0.9 - 0.25, 1.3),
        vec3(p.x * 1.65, -1.45 + p.y * 0.42, 0.7 + p.y * 1.0), pool));
    if (currents > 0.0) {
        origin = mix(origin, vec3(0.0,5.6,-1.0), currents);
        ray = normalize(mix(ray, normalize(vec3(p.x*1.65,-1.45+p.y*.42,p.y*1.3+.4)), currents));
    }
    float height_scale = mix(1.0,.16,currents);
    if (ray.y >= -0.012) {
        return WaterSurface(vec2(0.0), vec2(0.0), vec3(0.0, 1.0, 0.0), -ray, -1.0);
    }
    // The bounds enclose quiet ripples plus the largest possible storm swell.
    float storm = water_storm();
    float bound = 0.4 + storm * 0.60;
    float lo = (bound - origin.y) / ray.y;
    float hi = (-bound - origin.y) / ray.y;
    if (lo > 110.0) {
        return WaterSurface(vec2(0.0), vec2(0.0), vec3(0.0, 1.0, 0.0), -ray, -1.0);
    }
    if (storm > 0.0) {
        // Steep seas can cross a ray more than once. Bracket the first visible
        // crest before refinement, so foreground waves hide distant troughs.
        float step_size = (hi - lo) / 40.0;
        float start = lo;
        for (int i = 1; i <= 40; i++) {
            float sample_t = start + float(i) * step_size;
            vec3 point = origin + ray * sample_t;
            if (point.y <= water_height(point.xz)*height_scale) {
                hi = sample_t;
                break;
            }
            lo = sample_t;
        }
    }
    for (int i = 0; i < 14; i++) {
        float mid = (lo + hi) * 0.5;
        vec3 point = origin + ray * mid;
        if (point.y > water_height(point.xz)*height_scale) lo = mid;
        else hi = mid;
    }
    float distance = (lo + hi) * 0.5;
    vec2 position = (origin + ray * distance).xz;
    // Broader normal samples at distance suppress unresolved micro-ripples.
    float e = max(0.012, distance * 0.65 / u_resolution.y);
    vec2 gradient = vec2(
        water_height(position + vec2(e, 0.0)) - water_height(position - vec2(e, 0.0)),
        water_height(position + vec2(0.0, e)) - water_height(position - vec2(0.0, e))) / (2.0 * e);
    vec3 normal = normalize(vec3(-gradient.x*height_scale, 1.0, -gradient.y*height_scale));
    // Restrained refraction; gather the actual shared field along currents.
    vec2 current = water_current(position + normal.xz * 0.18);
    vec2 material = current * vec2(0.22, 0.27);
    material.x += 0.32 * sin(current.y * 0.8 + sin(current.x * 0.5));
    if (currents > 0.0)
        material = mix(material, currents_domain(position+normal.xz*.18)*vec2(.28,.12), currents);
    return WaterSurface(position, material, normal, -ray, distance);
}

vec3 isolated_water_scene(WaterSurface surface, vec3 canvas, vec4 forms, float currents)
{
    if (surface.distance < 0.0) return water_environment(-surface.view);
    float spark = clamp(u_sparkle, 0.0, 1.0);
    vec2 detail_position = surface.position;
    if (shared_spatial()) detail_position=spatial_carrier(surface.position*.28)/.28;
    vec2 q = water_current(detail_position);
    float rain_weight = u_layer_mode == 0 ? forms.z : effect(4096);
    float ripple_weight = u_layer_mode == 0 ? forms.z : effect(8192);
    // Rain perturbs reflected normals, keeping the accepted sea height intact.
    if (ripple_weight > 0.0) {
        float e = 0.025;
        vec2 grad = vec2(water_ripples(surface.position+vec2(e,0))-water_ripples(surface.position-vec2(e,0)),
            water_ripples(surface.position+vec2(0,e))-water_ripples(surface.position-vec2(0,e))) / (2.0*e);
        surface.normal = normalize(surface.normal + vec3(-grad.x,0,-grad.y)*ripple_weight*(0.025+spark*0.035));
    }
    float channel = q.x * 0.8 + sin(q.y * 0.48) * 1.7
        + sin(q.y * 1.12 + q.x * 0.31) * 0.35;
    float dye = smoothstep(-0.45, 0.8, sin(channel));
    float depth = 0.45 + 1.9 * (1.0 - dye);
    // Absorption leaves dark channels between luminous submerged material.
    vec3 pigment = canvas / (0.35 + max(canvas.r, max(canvas.g, canvas.b)));
    vec3 transmission = canvas * (0.85 + 2.4 * dye)
        * exp(-depth * vec3(0.48, 0.24, 0.18));
    transmission += pigment * pow(dye, 5.0) * 0.08;
    if(u_water_sea_on==1)transmission*=u_water_sea[0];
    float facing = clamp(dot(surface.normal, surface.view), 0.0, 1.0);
    float fresnel = 0.035 + 0.70 * pow(1.0 - facing, 5.0);
    vec3 reflection = reflect(-surface.view, surface.normal);
    // Broad colored off-screen light reflected by the actual wave normals.
    // No full-screen white layer: most reflected directions see dark space.
    vec3 light = normalize(vec3(-0.25, 0.48, 0.86));
    float glint = pow(max(dot(reflection, light), 0.0), 145.0);
    float silk = pow(max(dot(reflection, light), 0.0), 32.0);
    vec3 reflected = color_tint(lavender_pearl_palette(0.48),u_water_sea_on,u_water_sea[1]) * silk * 0.48;
    reflected += color_tint(mix(ocean_palette(0.80), gold_sun_palette(0.82), 0.36),u_water_sea_on,u_water_sea[3])
        * glint * (0.90 + spark * 1.4);
    reflected *= effect(65536);
    vec3 scene = transmission * (1.0 - fresnel) + reflected;
    scene += water_environment(reflection) * fresnel * 0.85;
    scene += ocean_palette(0.22) * (0.12 + fresnel * 0.3);
    // Sparse foam belongs to high, steep crests and travels in the same
    // current coordinates. It vanishes completely as the sea settles.
    float crest = smoothstep(0.26, 0.61, water_height(surface.position));
    float broken = smoothstep(0.35, 0.78, noise(q * vec2(9.0, 14.0)));
    float foam = water_storm() * crest * broken
        * (1.0 - smoothstep(0.68, 0.97, surface.normal.y));
    scene += color_tint(mix(ocean_palette(0.85), lavender_pearl_palette(0.83), 0.35),u_water_sea_on,u_water_sea[2])
        * foam * (0.40 + spark * 0.30) * effect(16384);
    float distance_fade = exp(-max(surface.distance - 5.0, 0.0) * 0.065);
    scene *= distance_fade;
    // Preserve saturated dye and highlight headroom across all audio levels.
    // Dye pools expose connected submerged folds and broad empty channels.
    vec2 ink = q * 1.6;
    ink += vec2(sin(ink.y*.8+u_time*.05),cos(ink.x*.65-u_time*.04))*.85;
    float fold = fbm(ink*.85+vec2(0,u_time*.03));
    float vein = .5+.5*sin(ink.x*2.6+ink.y*.8+fold*15.0);
    float fine = pow(.5+.5*sin(ink.x*12.0+ink.y*3.0+fold*48.0),12.0);
    vec3 ink_color = mix(canvas*2.2, mix(ocean_palette(.63),crimson_gold_palette(.62),
        smoothstep(.32,.67,fold)),.38);
    if(u_water_dyes_on==1)ink_color*=u_water_dyes;
    vec3 dye_color = ink_color*(.12+smoothstep(.25,.70,vein)*.9);
    dye_color += ink_color*fine*(.15+spark*.25)+reflected*.20;
    // Normalize the remaining surface before Currents and Falls take coverage.
    float dye_amount=forms.y/max(1.-currents-forms.w,.000001);
    scene = mix(scene, dye_color, clamp(dye_amount,0.,1.)*.95);
    if (currents > 0.0) {
        vec2 flow = currents_domain(detail_position);
        float bass = clamp(u_scale,0.0,1.0), flux = clamp(u_flux,0.0,1.0);
        float lane = flow.x*2.15 + .28*sin(flow.y*.65+flow.x*.6);
        float body = smoothstep(.18-bass*.12,.80,.5+.5*sin(lane));
        float phase = lane*11.0 + .6*sin(flow.y*1.4);
        float resolved = 1.0-smoothstep(.65,2.1,fwidth(phase));
        float thread = pow(.5+.5*sin(phase),12.0)*resolved;
        float travel = .65+.35*sin(flow.y*2.0+sin(flow.x*3.1));
        vec3 tint = mix(ocean_palette(.75),crimson_gold_palette(.78),
            .5+.5*sin(flow.x*.85+.4*sin(flow.y*.25)));
        vec3 carried = mix(pigment,tint,.44);
        vec3 current_color = ocean_palette(.16)*.13
            + carried*(.08+body*(.85+bass*.18))
            + canvas*body*(1.25+travel*.50);
        if(u_water_currents_on==1)current_color*=u_water_currents[0];
        // Fine reflected ribbons keep dark channels and never form a white wash.
        current_color += color_tint(mix(carried,lavender_pearl_palette(.65),.22),u_water_currents_on,u_water_currents[1])
            * thread*body*travel*(.25+spark*.7)*effect(65536);
        current_color += reflected*.25;
        current_color *= .82+.18*max(dot(surface.normal,surface.view),0.0);
        scene = mix(scene,current_color,clamp(currents/max(1.-forms.w,.000001),0.,1.));
    }
    if (ripple_weight > 0.0) {
        float rings = water_ripples(detail_position);
        scene += color_tint(mix(ocean_palette(.75),lavender_pearl_palette(.75),.3),u_water_rain_on,u_water_rain[1])
            * max(rings,0.0)*ripple_weight*(.16+spark*.32);
    }
    if (rain_weight > 0.0) {
        // Sparse foreground streaks, with independent seeded lifetimes.
        vec2 rain_q = detail_position*2.0;
        vec2 cell=floor(rain_q);
        float seed=hash(cell+13.0);
        float age=fract(u_drift_time*.7+seed);
        vec2 drop=fract(rain_q)-vec2(.3+seed*.4,1.2-age*1.6);
        float streak=exp(-drop.x*drop.x*4500.0-drop.y*drop.y*65.0)
            *smoothstep(.70,.95,seed)*smoothstep(.0,.1,age)*(1.0-smoothstep(.85,1.0,age));
        scene += color_tint(ocean_palette(.85),u_water_rain_on,u_water_rain[0])*streak*rain_weight*(.12+spark*.25);
    }
    scene /= 1.0 + max(scene.r, max(scene.g, scene.b));
    float haze = 1.0 - exp(-pow(max(surface.distance - 9.0, 0.0) * 0.035, 1.45));
    return mix(scene, water_environment(-surface.view), haze * effect(32768));
}

// One perspective camera views a horizontal river meeting an infinite vertical
// fall at z=0, y=0. The world horizon and cliff lip are distinct projected lines.
// Moving below and toward the lip naturally moves river/sky out of the frame.
struct FallsSurface {
    vec2 position; // x and signed flow distance: positive upriver, negative downfall
    vec3 ray;
    float distance;
    float kind; // 0 sky, 1 river/banks, 2 falling face/cliff
};

FallsSurface waterfall_surface(vec2 p)
{
    float approach = 0.5 - 0.5*cos((u_drift_time-84.0)*0.16);
    approach = smoothstep(0.10,0.92,approach);
    vec3 origin = vec3(sin(u_drift_time*.035)*.28,
        mix(2.3,-0.85,approach), -mix(7.0,1.35,approach));
    float pitch = mix(.30,-.10,approach);
    vec3 ray = normalize(vec3(p.x,p.y-pitch,1.0));
    if (origin.y > 0.0 && ray.y < -0.0001) {
        float t = -origin.y/ray.y;
        vec3 hit = origin + ray*t;
        if (hit.z >= 0.0 && t < 160.0)
            return FallsSurface(hit.xz,ray,t,1.0);
    }
    float t = -origin.z/ray.z;
    vec3 hit = origin + ray*t;
    if (hit.y <= 0.0)
        return FallsSurface(hit.xy,ray,t,2.0);
    return FallsSurface(vec2(0.0),ray,160.0,0.0);
}

vec2 waterfall_current(FallsSurface surface)
{
    float path = surface.position.y;
    // Continuous coordinate/speed at the lip; falling streaks stretch as they
    // accelerate downward. Neither audio nor camera resets this transport clock.
    if (surface.kind > 1.5) path = 1.0-sqrt(1.0-2.0*min(path,0.0));
    return vec2(surface.position.x,path+u_time*.72+u_drift_time*.08);
}

vec3 water_falls(FallsSurface surface, vec3 material)
{
    if (surface.kind < .5) return water_environment(surface.ray);
    float bass=clamp(u_scale,0.0,1.0), spark=clamp(u_sparkle,0.0,1.0);
    float flux=clamp(u_flux,0.0,1.0);
    bool river=surface.kind < 1.5;
    vec2 pos=surface.position;
    vec2 flow=waterfall_current(surface);
    // Fold curtain filaments without moving the cliff or waterfall boundaries.
    if (shared_spatial()) {
        float travel=u_time*.72+u_drift_time*.08;
        flow.y-=travel;
        flow=spatial_carrier(flow*vec2(.28,.18))/vec2(.28,.18);
        flow.y+=travel;
    }
    float path=pos.y;
    float bend=river ? sin(path*.16)*.50 : sin(-path*.8-u_time*.13)*min(-path*.018,.12);
    float width=2.45 + bass*.20 + (river ? min(path*.025,1.2) : min(-path*.035,.25));
    float edge=abs(pos.x-bend);
    float aa=max(fwidth(edge),.008);
    float water=1.0-smoothstep(width-.10-aa,width+.10+aa,edge);
    // Cohesive sheets with smaller strands carried by the same flow coordinate.
    vec2 sheet_q=vec2(flow.x*2.7,flow.y*1.5);
    float fold=fbm(sheet_q);
    float phase=flow.x*18.0+fold*(12.0+flux*3.0)
        +sin(flow.y*.70+flow.x*.9)*2.0;
    float resolved=1.0-smoothstep(.8,3.0,fwidth(phase));
    float filament=pow(.5+.5*sin(phase),7.0)*resolved;
    float body=smoothstep(.20,.78,fold);
    vec3 tint=mix(ocean_palette(.72),lavender_pearl_palette(.75),.35);
    vec3 liquid=material*(.65+body*1.20);
    if(u_water_falls_on==1)liquid*=u_water_falls[0];
    liquid+=color_tint(tint,u_water_falls_on,u_water_falls[1])*(.035+body*.08);
    if (river) {
        // Shared wave normals give the upstream river a reflected path of
        // light, rather than a crossing grid drawn on the surface.
        float e=max(.018,surface.distance*.7/u_resolution.y);
        vec2 slope=vec2(water_height(pos+vec2(e,0))-water_height(pos-vec2(e,0)),
            water_height(pos+vec2(0,e))-water_height(pos-vec2(0,e)))/(2.0*e);
        vec3 normal=normalize(vec3(-slope.x,1.0,-slope.y));
        vec3 reflected=reflect(surface.ray,normal);
        vec3 light=normalize(vec3(-.22,.50,.86));
        float shine=pow(max(dot(reflected,light),0.0),65.0);
        liquid*=.85;
        liquid+=color_tint(tint,u_water_falls_on,u_water_falls[1])*shine*(.8+spark*.6)*effect(65536);
        liquid+=water_environment(reflected)*.15;
    } else {
        // Continuous broad sheets, with broken smaller strands accelerating
        // down the face. No periodic horizontal bars or receiving basin.
        float streak=fbm(vec2(flow.x*8.0,flow.y*5.0));
        float veil=smoothstep(.25,.74,streak);
        liquid+=color_tint(tint,u_water_falls_on,u_water_falls[1])*filament*(.18+spark*.23)*(.35+veil*.85)*effect(65536);
        liquid+=color_tint(tint,u_water_falls_on,u_water_falls[1])*veil*body*(.10+flux*.16);
    }
    // Dark plateau banks and cleft cliff walls anchor the two water planes.
    vec2 rock_q=river ? vec2(pos.x*.8,path*.4) : vec2(pos.x*1.5,path*.35);
    float rock=fbm(rock_q);
    float strata=.5+.5*sin(path*2.7+rock*6.0);
    vec3 stone=mix(ocean_palette(.24),lavender_pearl_palette(.27),rock)
        *(.20+rock*.30+strata*.10);
    if(u_water_falls_on==1)stone*=u_water_falls[2];
    vec3 scene=mix(stone,liquid,water);
    // The turnover belongs to the same edge on both sides of the cliff.
    float lip=exp(-abs(path)*12.0)*water;
    scene+=color_tint(tint,u_water_falls_on,u_water_falls[3])*lip*(.16+bass*.09+spark*.10)*effect(16384);
    float haze=1.0-exp(-max(surface.distance-8.0,0.0)*.032);
    scene/=1.0+max(scene.r,max(scene.g,scene.b));
    return mix(scene,water_environment(surface.ray),haze*effect(32768));
}

// Fire is an isolated development world. Three depth sheets share upward
// transport; audio bends the field without multiplying/resetting its clock.
vec2 fire_domain(vec2 p) {
    float h = p.y + .40;
    float clock = u_time*.32 + u_drift_time*.025;
    float bend = sin(h*5.0-clock*.9)*h*.19
        + (fbm(vec2(p.x*3.,h*3.-clock))-.5)*h*.32;
    return vec2((p.x-bend)*1.7, h*.75-clock*.32);
}

vec3 isolated_fire_scene(vec2 p, vec3 canvas) {
    float bass=clamp(u_scale,0.,1.), flux=clamp(u_flux,0.,1.);
    float spark=clamp(u_sparkle,0.,1.), impact=clamp(u_impact,0.,1.);
    float clock=u_time*.62+u_drift_time*.025;
    float rage=smoothstep(.10,.85,.38*bass+.42*flux+.20*spark);
    float surge=max(rage,smoothstep(.12,.55,impact)*.8);
    vec3 light=vec3(.006,.008,.016);
    // A low hearth in a dark chamber. Back sheets are cooler and dimmer.
    for(int layer=0;layer<3;layer++) {
        float z=float(layer);
        float h=(p.y+.46+z*.024)/mix(.085,1.75,surge);
        float x=p.x*(1.0+z*.16)+.055*sin(z*3.1);
        float rise=clock+z*4.7;
        vec2 adv=vec2(x*4.,h*2.9-rise);
        float fold=fbm(adv);
        x+=(fold-.5)*(.04+surge*.65)*max(h,0.)
            +sin(h*5.-rise+z)*h*(.015+surge*.32);
        // Tips lean, curl and draw out as a coherent traveling lick.
        float tip=smoothstep(.20,.85,h);
        x+=tip*(.015+.27*surge)*sin(h*9.-rise*1.7+z*1.9);
        float tongues=.5+.5*sin(x*17.+sin(x*9.+z-rise*.65)*1.5
            +z*2.3+sin(rise*.85+z)*.75);
        float top=.39+.43*tongues+.20*fbm(vec2(x*8.,rise*.7));
        float taper=1.-smoothstep(.12,1.,h);
        float width=mix(.22,2.3,surge)*max(.16,taper);
        float edge=width-abs(x);
        float silhouette=smoothstep(-.018,.055,edge)
            *smoothstep(-.02,.025,h)*(1.-smoothstep(top-.16,top+.03,h));
        float ribbons=.5+.5*sin(x*36.+fold*9.+h*3.);
        float veil=.28+.72*pow(ribbons,1.5);
        float heat=clamp(.78-h*.52+fold*.23+impact*.12*exp(-h*h*14.),0.,1.);
        vec3 tint=mix(vec3(.32,.018,.24),vec3(1.15,.20,.018),smoothstep(.20,.67,heat));
        tint=mix(tint,vec3(1.20,.62,.08),smoothstep(.78,1.,heat));
        vec3 pigment=canvas/(1.+max(canvas.r,max(canvas.g,canvas.b)));
        vec3 sheet=mix(tint,pigment*1.5,.27)*veil;
        if(u_fire_sheets_on==1)sheet*=u_fire_sheets[0];
        float seam=pow(ribbons,18.)*silhouette*(.10+spark*.24)
            *effect(524288);
        // Strong real onsets reach about .5. Existing envelope decay moves
        // the short white core through blue and back to the amber sheets.
        float hot=smoothstep(.12,.40,impact);
        float white=smoothstep(.40,.50,impact);
        float foot=exp(-pow((h-.085)*14.,2.))*silhouette
            *(.12+.88*ribbons*ribbons);
        vec3 ignition=mix(vec3(.025,.24,1.25),vec3(1.30,1.42,1.55),white);
        if(u_fire_sheets_on==1)ignition*=u_fire_sheets[1];
        light+=ignition*foot*hot*(.52-z*.12);
        light+=sheet*silhouette*(.44-z*.10)*(.10+surge*1.35)
            +color_tint(vec3(1.,.35,.08),u_fire_details_on,u_fire_details[2])*seam*(.12+surge);
    }
    // Slow lava threads between dark crusts. Elapsed time keeps this bed
    // steady even when bass, flux or the integrated flame speed changes.
    float lava_time=u_drift_time*.075;
    vec2 bed=vec2(p.x*9.-lava_time,(p.y+.405)*30.);
    bed.y+=.65*sin(bed.x*.8+lava_time*.35);
    float coal_mask=exp(-pow((p.y+.402)*22.,2.))
        *(1.-smoothstep(.46,.76,abs(p.x)));
    float crust=fbm(bed);
    float channels=exp(-pow((crust-.48)*19.,2.));
    float rhythm=.88+.12*sin(u_drift_time*.65+p.x*3.);
    vec3 molten=mix(vec3(.34,.025,.009),vec3(.95,.24,.025),channels);
    if(u_fire_details_on==1)molten*=u_fire_details[0];
    light+=molten*coal_mask*(.12+channels*.60)*rhythm*effect(131072);
    // Seeded ascending sparks fade at wrap boundaries; no frame randomness.
    for(int i=0;i<22;i++) {
        float seed=hash(vec2(float(i),8.9));
        float age=fract(clock*(.10+seed*.07)+seed*7.);
        float y=-.36+age*.97;
        float x=(hash(vec2(float(i),3.2))-.5)*.95
            +age*.12*sin(clock*.7+seed*31.);
        vec2 d=p-vec2(x,y);
        float fade=smoothstep(0.,.12,age)*(1.-smoothstep(.65,1.,age));
        float dotlight=exp(-dot(d*vec2(280.,140.),d*vec2(280.,140.)));
        light+=color_tint(vec3(1.,.40,.075),u_fire_details_on,u_fire_details[1])*dotlight*fade*(.015+surge*(.15+spark*.8))
            *effect(262144);
    }
    // Soft shoulder preserves amber detail at full drive instead of white.
    return 1.-exp(-light*1.65);
}

// A separate held form and a development-only three-form meld. Held Fire (14)
// retains its individual route; the source material clock never resets.
float molten_weight() {
    if (u_directed == 1) return u_fire_mix.y;
    if (u_debug_state > 14.5 && u_debug_state < 15.5) return 1.;
    if (u_debug_state < 15.5 || u_debug_state > 16.5) return 0.;
    float phase=mod(u_drift_time,84.);
    return smoothstep(19.,28.,phase)*(1.-smoothstep(47.,56.,phase));
}

float firescape_weight() {
    if (u_directed == 1) return u_fire_mix.z;
    if (u_debug_state > 16.5 && u_debug_state < 17.5) return 1.;
    if (u_debug_state < 15.5 || u_debug_state > 16.5) return 0.;
    float phase=mod(u_drift_time,84.);
    return smoothstep(47.,56.,phase)*(1.-smoothstep(75.,84.,phase));
}

// A slow elevated orbit: horizontal world heading changes, gravity stays down.
vec2 molten_ground(vec2 p) {
    float heading=.34+u_time*.045;
    vec2 forward=vec2(sin(heading),cos(heading));
    vec2 right=vec2(forward.y,-forward.x);
    float down=.408-p.y*1.46;
    vec2 ray=forward*(.913+p.y*.653)+right*p.x*1.6;
    float zoom=1.+.06*sin(u_time*.28)+.07*clamp(u_scale,0.,1.);
    return -forward*9.+ray*(4./max(.035,down))/zoom;
}

// Return cross-stream distance and the parent center. Branches begin on the
// parent river and their hot fronts grow downstream; there are no random cuts.
vec2 molten_channel(vec2 ground) {
    float growth=clamp(u_molten_growth,0.,1.);
    float center=.65*sin(ground.y*.34)+.28*sin(ground.y*.77)
        +.12*growth*sin(ground.y*.46-u_molten_phase*.18);
    float distance=abs(ground.x-center)/(.34+.66*growth);
    for(int i=0;i<4;i++) {
        float id=float(i),split=ceil((ground.y+id*3.5)/14.)*14.-id*3.5;
        float downstream=max(0.,split-ground.y);
        float stage=smoothstep(.10+id*.14,.64+id*.12,growth);
        float side=mod(id,2.)<.5?-1.:1.;
        float spread=side*(1.-exp(-downstream*.32))*(2.4+id*.55)*(1.-smoothstep(10.,14.,downstream));
        float branch=center+spread+.24*sin(downstream*.85+id-u_molten_phase*.12)*smoothstep(0.,2.,downstream);
        float front=.4+stage*16.;
        float formed=smoothstep(0.,.8,downstream)*(1.-smoothstep(front,front+1.8,downstream))*(1.-smoothstep(12.,14.,downstream))*stage;
        float width=(.24+.48*stage)*formed;
        float branchDistance=abs(ground.x-branch)/max(.015,width)+2.*(1.-formed);
        distance=min(distance,branchDistance);
    }
    return vec2(distance,center);
}

vec2 molten_domain(vec2 p) {
    vec2 q=molten_ground(p);
    q.x-=.65*sin(q.y*.34)+.28*sin(q.y*.77);
    q.y+=u_time*.28;
    q.x+=.09*sin(q.y*1.3+q.x);
    return q;
}

vec3 molten_backdrop(vec2 p) {
    float bearing=.34+u_time*.045+atan(p.x*1.6,.913);
    float ridge=.315+.038*sin(bearing*5.)+.032*sin(bearing*11.+2.)
        +.015*sin(bearing*23.);
    vec3 sky=mix((u_molten_palette_on==1?u_molten_palette[4]:u_molten_authored[4]),(u_molten_palette_on==1?u_molten_palette[4]:u_molten_authored[4])*vec3(2.03,1.49,1.21),
        1.-smoothstep(.26,.50,p.y));
    if(u_molten_flow_on==1)sky*=u_molten_flow[2];
    vec3 scene=mix(sky,vec3(.031,.038,.050),1.-smoothstep(ridge-.003,ridge+.003,p.y));
    float near_ridge=.26+.025*sin(bearing*7.+1.)+.012*sin(bearing*19.);
    scene=mix(scene,vec3(.018,.029,.030),1.-smoothstep(near_ridge-.002,near_ridge+.002,p.y));
    // Simple conifer teeth, only a silhouette. World bearing ties the tree
    // line to the terrain instead of pinning it to the screen during orbit.
    float cell=bearing*140.;
    float seed=hash(vec2(floor(cell),4.2));
    float crown=pow(max(0.,1.-abs(fract(cell)*2.-1.)),1.35);
    float trees=.224+.014*sin(bearing*9.)+crown*(.012+seed*.021);
    return mix(scene,vec3(.009,.019,.018),1.-smoothstep(trees-.001,trees+.001,p.y));
}

vec3 molten_pigment(int role){return u_molten_palette_on==1?u_molten_palette[role]:u_molten_authored[role];}
// hot transported front, anchored vent core, cooled deposit, local rolling pressure.
vec4 molten_memory(vec2 ground){
    vec4 memory=vec4(0.);
    for(int i=0;i<4;i++){
        vec4 e=u_molten_events[i];float age=u_drift_time-e.x;
        if(age<0. || age>=18. || e.w<=0.)continue;
        float y=e.z-age*.55;float x=.65*sin(y*.34)+.28*sin(y*.77);
        vec2 d=ground-vec2(x,y);float front=exp(-dot(d*vec2(1.3,1.8),d*vec2(1.3,1.8)));
        vec2 a=ground-e.yz;float vent=exp(-dot(a,a)*14.);
        float cool=smoothstep(.8,2.8,age)*exp(-age*.095);
        float deposit=exp(-dot(a*vec2(1.8,.75),a*vec2(1.8,.75))/(1.+age*.09));
        memory+=e.w*vec4(front*exp(-age*.52),vent*exp(-age*2.1),deposit*cool,front*exp(-age*.32)*sin(age*5.));
    }
    return memory*u_molten_amount;
}

vec3 isolated_molten_scene(vec2 p,vec3 canvas) {
    float bass=clamp(u_scale,0.,1.),flux=clamp(u_flux,0.,1.);
    float spark=clamp(u_sparkle,0.,1.),impact=clamp(u_impact,0.,1.);
    vec2 ground=molten_ground(p), q=molten_domain(p);
    float pressure=smoothstep(.04,.82,u_molten_motion.x);
    vec4 memory=molten_memory(ground);
    q.y+=u_molten_phase*.20;
    q.x+=sin(q.y*1.7+u_molten_phase*.4)*u_molten_motion.y*.055;
    float pulse=memory.x;
    float width=(.58+.10*sin(ground.y*.42))*(1.+pressure*.85+pulse*.12);
    float bank=molten_channel(ground).x/width;
    float river=1.-smoothstep(.78,1.22,bank);
    // Molten folds travel with the river; banks stay fixed in ground space.
    float fold=fbm(q*vec2(3.8,2.1));
    float threads=.5+.5*sin(q.x*30.+fold*12.+q.y*1.8
        +u_molten_motion.y*.7*sin(q.y*2.3));
    float crust=.018*(1.-u_molten_motion.w)+memory.z*.055;
    float islands=smoothstep(.38+pressure*.12-crust,.56+pressure*.12-crust,fold)*effect(131072);
    float liquid=river*(1.-islands*.96);
    float rock=fbm(ground*3.2);
    float height=(1.-river)*(.25+rock*.3)+islands*river*.13;
    vec3 normal=normalize(vec3(-dFdx(height)*u_resolution.y*.55,
        -dFdy(height)*u_resolution.y*.55,1.));
    float shade=.25+.75*max(0.,dot(normal,normalize(vec3(-.4,.6,1.))));
    vec3 light=color_tint(molten_pigment(3),u_molten_flow_on,u_molten_flow[1])*shade*(.5+rock);
    float glow=exp(-pow((bank-1.)*2.3,2.));
    light+=vec3(.085,.011,.006)*glow*(.45+rock);
    vec3 pigment=canvas/(1.+max(canvas.r,max(canvas.g,canvas.b)));
    vec3 heat=molten_pigment(0)*mix(vec3(.48,.11,.16),vec3(1.10,1.34,1.),threads*.65+fold*.25);
    heat=mix(heat,pigment*1.1,.22);
    if(u_molten_flow_on==1)heat*=u_molten_flow[0];
    light+=heat*liquid*(.30+pressure*.95+pulse*.58)*(1.-memory.z*.23);
    light+=molten_pigment(2)*islands*river*shade*(.65+rock)*(1.+memory.z*1.4);
    float seams=pow(threads,10.)*liquid*(.13+u_molten_motion.z*.23)
        +exp(-pow((fold-.48)*38.,2.))*river*(.12+pressure*.35+pulse*.45);
    light+=color_tint(molten_pigment(1),u_fire_details_on,u_fire_details[2])*seams*effect(524288);
    // Onsets select one persistent site; its heat travels with the river, then crust remains.
    light+=molten_pigment(5)*memory.y*river*1.5;
    light+=molten_pigment(1)*memory.x*liquid*(.18+.22*threads);
    float cooling_seam=exp(-pow((fold-.48)*33.,2.))*river*memory.z;
    light+=molten_pigment(0)*cooling_seam*.18;
    vec3 terrain=1.-exp(-light*1.8);
    float distance=length(ground);
    float haze=smoothstep(15.,65.,distance)*.82;
    terrain=mix(terrain,vec3(.016,.026,.027),haze);
    float horizon=smoothstep(.185,.255,p.y);
    vec3 result=mix(terrain,molten_backdrop(p),horizon);
    // Sparse rising embers across the whole view, above haze/horizon composition.
    float aspect=u_resolution.x/max(1.,u_resolution.y);
    for(int i=0;i<32;i++) {
        float seed=hash(vec2(float(i),9.3)),lane=hash(vec2(float(i),27.1));
        float age=fract(u_drift_time*(.075+.025*seed)+seed*9.);
        vec2 pos=vec2((lane-.5)*aspect*.98,-.49+age*1.02);
        pos.x+=.045*sin(age*5.+seed*19.)+.015*u_molten_motion.y*sin(age*9.+seed*4.);
        pos.y+=u_impact*.012*(.4+.6*seed);
        vec2 d=p-pos;float ember=exp(-dot(d*vec2(300.,200.),d*vec2(300.,200.)));
        vec2 tail=d+vec2(0.,.003+.003*pressure);
        float trail=exp(-dot(tail*vec2(260.,140.),tail*vec2(260.,140.)))*.25;
        float life=smoothstep(0.,.12,age)*(1.-smoothstep(.72,1.,age));
        float pulse=.20+spark*.60+pressure*.20+u_impact*(.15+.30*seed);
        result+=color_tint(molten_pigment(1),u_fire_details_on,u_fire_details[1])*(ember+trail)*life*pulse*effect(262144);
    }
    return result;
}

// Its own color vocabulary. The existing integrated movement clock controls
// hue speed continuously; amplitude never multiplies elapsed time directly.
vec3 firescape_palette(float phase) {
    vec3 wave=.5+.5*cos(phase+vec3(0.,2.1,4.2));
    return .025+pow(wave,vec3(1.7))*.95;
}
vec2 firescape_domain(vec2 p) {
    return vec2(p.x*2.5+.12*sin(p.y*6.-u_time*.25),p.y*.85-u_time*.095);
}
// World-space scenery moves through fixed cells. Each seed keeps its own
// growth/burn phase as the camera scrolls; no frame-to-frame random choices.
float firescape_scroll(float depth) { return (u_time*.070+u_firescape_travel+u_drift_time*.005)*depth; }
float firescape_life(float seed) { return fract(u_time/100.+u_drift_time/180.+seed); }
float firescape_hill(float x,float z) {
    return .06-z*.19+.035*sin(x*3.+z*2.)+.027*sin(x*8.+z*.7);
}
float firescape_segment(vec2 p,vec2 a,vec2 b,float width) {
    vec2 d=b-a;
    float t=clamp(dot(p-a,d)/dot(d,d),0.,1.);
    return 1.-smoothstep(width,width+.018,length(p-a-d*t));
}
vec2 firescape_tree(vec2 local,float seed,float age) {
    if (local.y < -.03 || local.y > 1.3 || abs(local.x) > .9) return vec2(0.);
    float grow=smoothstep(.015,.27,age);
    float clear=1.-smoothstep(.91,.995,age);
    vec2 q=local/max(.025,grow);
    float bend=(seed-.5)*.20;
    q.x-=bend*q.y*q.y+.012*sin(u_drift_time*.5+seed*20.)*q.y;
    float crown=0.,wood=firescape_segment(q,vec2(0.),vec2(.02,.78),.029);
    for(int i=0;i<6;i++) {
        float id=float(i),r=hash(vec2(seed*17.+id,3.4));
        float side=mod(id,2.)<.5 ? -1. : 1.;
        vec2 root=vec2(.01,.28+id*.055);
        vec2 tip=vec2(side*(.18+r*.17),.57+id*.055+r*.10);
        wood=max(wood,firescape_segment(q,root,tip,.011));
        vec2 leaf=(q-tip)/vec2(.19+r*.07,.16+r*.06);
        float edge=length(leaf)+.065*sin(atan(leaf.y,leaf.x)*9.+seed*20.);
        crown=max(crown,1.-smoothstep(.85,1.02,edge));
    }
    // The burn front descends through foliage, then the bare trunk, to ground.
    float front=1.18*(1.-smoothstep(.48,.91,age));
    float unburnt=1.-smoothstep(front-.055,front+.055,q.y);
    float foliage=crown*unburnt*(1.-smoothstep(.64,.79,age));
    float charred=wood*(1.-smoothstep(front+.02,front+.13,q.y));
    float presence=smoothstep(0.,.035,age)*clear;
    float body=max(foliage,charred)*presence;
    float ignition=exp(-pow((q.y-front)*20.,2.))*max(crown,wood)
        *smoothstep(.47,.55,age)*clear*presence;
    return vec2(body,ignition);
}
vec2 firescape_building(vec2 local,float seed,float age) {
    float grow=smoothstep(.02,.30,age);
    float clear=1.-smoothstep(.94,.995,age);
    float body=0.,seams=0.;
    // Eighteen masonry blocks acquire independent delays before falling.
    for(int row=0;row<6;row++) for(int col=0;col<3;col++) {
        float r=float(row),c=float(col);
        float jitter=hash(vec2(seed*31.+r,c+8.));
        float fall=smoothstep(.61+jitter*.13,.93,age);
        vec2 center=vec2((c-1.)*.24,(r+.5)*.16);
        float built=smoothstep(center.y-.09,center.y+.05,grow);
        center.y=mix(center.y,.025+jitter*.025,fall*fall);
        center.x+=(jitter-.5)*fall*.6;
        vec2 q=local-center;
        float angle=(jitter-.5)*fall*2.;
        q=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*q;
        vec2 box=abs(q)-vec2(.113,.074)*mix(1.,.35,fall);
        float d=max(box.x,box.y);
        float block=(1.-smoothstep(-.008,.008,d))*built*clear;
        body=max(body,block);
        seams=max(seams,exp(-abs(d)*100.)*built*clear*fall);
    }
    return vec2(body,seams);
}

vec3 isolated_firescape_scene(vec2 p,vec3 canvas) {
    float bass=clamp(u_scale,0.,1.),flux=clamp(u_flux,0.,1.);
    float spark=clamp(u_sparkle,0.,1.),impact=clamp(u_impact,0.,1.);
    float clock=u_time*.40+u_drift_time*.025;
    float hue=u_time*.38;
    float beat=smoothstep(.16,.50,impact);
    vec3 pigment=canvas/(1.+max(canvas.r,max(canvas.g,canvas.b)));
    vec3 sky=color_tint(vec3(.008,.010,.023),u_firescape_land_on,u_firescape_land[4]);
    float distant=p.x+firescape_scroll(.18);
    float ridge=.22+.027*sin(distant*5.+1.)+.021*sin(distant*11.);
    vec3 scene=mix(sky,vec3(.012,.019,.030),1.-smoothstep(ridge-.002,ridge+.002,p.y));
    // Buildings rise floor by floor and crumble in a slower background layer.
    float city_x=p.x+firescape_scroll(.40);
    float block=city_x*8.+3.;
    float seed=hash(vec2(floor(block),6.2));
    float city_base=.105+.012*sin(city_x*4.);
    float building_height=.10+seed*.14;
    vec2 city=firescape_building(vec2((fract(block)-.5)*1.25,
        (p.y-city_base)/building_height),seed,firescape_life(seed));
    scene+=firescape_palette(hue+1.4)*exp(-pow((p.y-.19)*8.,2.))*.045;
    scene=mix(scene,vec3(.005,.008,.016),city.x);
    scene+=color_tint(firescape_palette(hue+1.4),u_firescape_land_on,u_firescape_land[2])*city.y*.16;
    for(int layer=0;layer<3;layer++) {
        float z=float(layer);
        float world_x=p.x+firescape_scroll(.65+z*.45);
        float base=firescape_hill(world_x,z);
        float h=(p.y-base)/(.27+bass*.045+z*.015);
        float x=world_x*(1.+z*.2)+z*.37;
        float rise=clock+z*3.2;
        float fold=fbm(vec2(x*5.,h*2.4-rise));
        float curl=(fold-.5)*h*(.12+flux*.18)+sin(h*5.-rise)*h*.08;
        float strand=x+curl;
        float tips=.40+.38*(.5+.5*sin(strand*22.+fold*5.+z))
            +.13*sin(strand*11.-rise*.6);
        float fire=smoothstep(-.025,.045,h)*(1.-smoothstep(tips-.17,tips+.08,h));
        float edge=.5+.5*sin(strand*47.+fold*9.);
        float veil=.24+.76*pow(edge,1.8);
        vec3 tint=firescape_palette(hue+z*1.4+h*1.3+fold*.6);
        tint=mix(tint,pigment*1.4,.18);
        if(u_firescape_land_on==1)tint*=u_firescape_land[0];
        float glow=exp(-pow((h-.12)*2.8,2.))*.08;
        scene+=tint*(fire*veil*(.65+z*.08)+glow)*(.78+bass*.20+beat*.68);
        scene+=color_tint(firescape_palette(hue+z*1.4+.6),u_fire_details_on,u_fire_details[2])*pow(edge,15.)*fire
            *(.10+spark*.22)*effect(524288);
        // Neighbor cells let crowns extend naturally beyond their planting
        // interval. Roots use their own fixed hill height, never pixel height.
        float density=8.-z*1.2;
        float cell=floor(world_x*density);
        float forest=1.-smoothstep(base-.018,base-.014,p.y);
        vec3 bark=vec3(.008,.016,.015);
        vec2 trees=vec2(0.);
        for(int neighbor=-1;neighbor<=1;neighbor++) {
            float id=cell+float(neighbor);
            float tree_seed=hash(vec2(id,z+3.));
            float center=(id+.4+tree_seed*.2)/density;
            float tree_height=(.075+tree_seed*.075)*(1.+z*.15);
            float age=firescape_life(tree_seed);
            vec2 local=vec2(world_x-center,p.y-firescape_hill(center,z))/tree_height;
            vec2 tree=firescape_tree(local,tree_seed,age);
            if (tree.x > trees.x) bark=mix(vec3(.008,.020,.015),vec3(.006,.008,.012),smoothstep(.5,.75,age));
            trees=max(trees,tree);
        }
        forest=max(forest,trees.x);
        scene=mix(scene,color_tint(bark,u_firescape_land_on,u_firescape_land[1])*(1.+z*.15),forest*.96);
        scene+=firescape_palette(hue+z*1.4)*trees.y*(.25+beat*.20);
        float soil=exp(-pow((p.y-base+.018)*40.,2.));
        scene+=color_tint(firescape_palette(hue+z),u_firescape_land_on,u_firescape_land[3])*soil*(.06+.12*noise(vec2(x*25.,rise*.15)))
            *effect(131072);
    }
    // Seeded trajectories: ash is broad and soft, embers small and luminous.
    // Both lift diagonally off the landscape and fade before wrapping.
    for(int i=0;i<64;i++) {
        float id=float(i),seed=hash(vec2(id,7.8));
        float age=fract(clock*(.10+seed*.07)+seed*13.);
        float depth=.5+.5*hash(vec2(id,2.6));
        vec2 pos=vec2((hash(vec2(id,3.1))-.5)*1.65,-.33+age*.95);
        pos.x+=age*.30+.055*sin(clock*.8+seed*25.+age*5.);
        vec2 d=p-pos;
        float life=smoothstep(0.,.10,age)*(1.-smoothstep(.75,1.,age));
        if(i<40) {
            float ember=exp(-dot(d*vec2(340.,190.)/depth,d*vec2(340.,190.)/depth));
            scene+=color_tint(firescape_palette(hue+seed*5.),u_fire_details_on,u_fire_details[1])*ember*life*(.35+spark*.7+beat*.4)
                *effect(262144);
        } else {
            float ash=exp(-dot(d*vec2(150.,240.)/depth,d*vec2(150.,240.)/depth));
            scene+=color_tint(vec3(.19,.20,.24),u_fire_details_on,u_fire_details[3])*ash*life*(.5+flux*.3)*effect(1048576);
        }
    }
    return 1.-exp(-scene*1.65);
}

// Aftershock: projected ground and layered, shaded ash volumes. Event timestamps
// preserve musical shockwaves independently of the decaying impact envelope.
float blast_retirement(float id,float clock){
    if(u_event_blasts==0)return 1.;
    for(int i=0;i<8;i++)if(u_blast_events[i].y==id && u_blast_retire[i]>=0.)return 1.-smoothstep(u_blast_retire[i],u_blast_retire[i]+.65,clock);
    return 1.;
}
float blast_latest(float clock) {
    if(u_event_blasts==0) return floor((clock-5.)/36.);
    float latest=-1.;
    for(int i=0;i<8;i++) latest=max(latest,u_blast_events[i].y);
    return latest;
}
float blast_birth(float id) {
    if(u_event_blasts==0) return 5.+id*36.;
    for(int i=0;i<8;i++) if(u_blast_events[i].y==id) return u_blast_events[i].x;
    return -1000.;
}
vec2 blast_site(float id) {
    if(u_event_blasts==1) {
        for(int i=0;i<8;i++) if(u_blast_events[i].y==id) return u_blast_events[i].zw;
        return vec2(0.,-1000.);
    }
    return vec2((hash(vec2(id,8.7))-.5)*12.,20.+id*10.8+
        (mod(id,3.)>1.5 ? 42. : 0.));
}
// Only three scheduled clouds can be alive within the 86-second lifetime.
// Sort actual world depth, since distant sites do not follow birth order.
vec3 blast_cloud_order(float clock) {
    float latest=floor((clock-5.)/36.);
    float ids[3];ids[0]=latest;ids[1]=latest-1.;ids[2]=latest-2.;
    for(int pass=0;pass<2;pass++) for(int i=0;i<2;i++) {
        if(blast_site(ids[i]).y<blast_site(ids[i+1]).y) {
            float swap=ids[i];ids[i]=ids[i+1];ids[i+1]=swap;
        }
    }
    return vec3(ids[0],ids[1],ids[2]);
}
vec3 blast_aurora(vec2 p,float clock,float camera,float camx) {
    float id=blast_latest(clock),age=clock-blast_birth(id);
    float bend=0.;
    if(id>=0.) {
        vec2 site=blast_site(id);
        float center=(site.x-camx)/max(4.,(site.y-camera)*1.6);
        bend=.045*smoothstep(0.,.18,age)*exp(-age*.6)
            *sin(age*2.4-abs(p.x-center)*5.)*exp(-pow((p.x-center)*1.5,2.));
    }
    vec3 light=vec3(0.);
    for(int i=0;i<3;i++) {
        float layer=float(i),x=p.x+layer*.7-clock*(.018+layer*.007);
        float ridge=.265+layer*.065+.035*sin(x*4.+clock*.065)
            +.017*sin(x*10.-clock*.09)+bend;
        float y=p.y-ridge;
        float ribbon=exp(-abs(y)*mix(65.,12.,step(0.,y)));
        float pleats=(.35+.65*pow(.5+.5*sin(x*160.+sin(x*11.+clock*.08)*6.
            +y*25.+sin(y*30.+x*3.)*2.),2.))*(.55+.45*noise(vec2(x*13.,clock*.035)));
        vec3 tint=.5+.5*cos(vec3(0.,2.,4.)+layer*1.8+x*.9+clock*.035);
        light+=tint*color_tint(vec3(.45,.85,.9),u_aftershock_events_on,u_aftershock_events[2])*ribbon*pleats*.24;
    }
    return light*smoothstep(.19,.25,p.y)*effect(16777216);
}
// Stable per-site color: no shared clock can rotate all plume hues together.
vec3 blast_plume_tint(float id) {
    return .24+.76*(.5+.5*cos(vec3(0.,2.094395,4.18879)+id*2.399963+.6));
}
vec3 blast_material_negative(vec3 material) {
    // Invert the actual incoming material, before its muted soil treatment.
    return color_tint(1.-clamp(material*1.6,0.,1.),u_aftershock_events_on,u_aftershock_events[3]);
}
vec3 blast_ring(vec2 ground, float id, float age, float strength) {
    if(age<0. || age>8.) return vec3(0.);
    vec2 d=ground-blast_site(id);
    float r=length(d), radius=age*2.8;
    float fade=smoothstep(0.,.12,age)*(1.-smoothstep(4.,8.,age))*strength;
    float irregular=noise(d*.7+vec2(u_drift_time*.12,0.));
    float curl=noise(d*2.8-vec2(u_time*.7,u_time*.3));
    float dust=exp(-pow((r-radius+(irregular-.5)*.24)/(.22+age*.065),2.))
        *(.65+irregular*.55);
    float tongue=pow(curl,3.)*(.6+clamp(u_flux,0.,1.)*.5);
    float flame=exp(-pow((r-radius+.55+irregular*.35+tongue)/(.12+curl*.16),2.));
    return fade*(color_tint(vec3(.30,.27,.21),u_aftershock_events_on,u_aftershock_events[0])*dust*effect(4194304)
        +color_tint(vec3(.95,.28,.035),u_aftershock_events_on,u_aftershock_events[1])*flame*(.4+irregular*.9)*effect(8388608));
}
vec3 isolated_aftershock_scene(vec2 p,vec3 canvas) {
    // A shallow planetary arc shared by ground, sky and projected plumes.
    p.y+=.045*p.x*p.x/(1.+.5*p.x*p.x);
    float clock=u_drift_time, camera=clock*.30;
    float camx=sin(clock*.025)*1.2;
    float rayy=p.y*1.6-.32;
    float groundDepth=6./max(.012,-rayy);
    vec2 ground=vec2(camx+p.x*1.6*groundDepth,camera+groundDepth);
    float haze=exp(-groundDepth*.019);
    vec3 scene=mix(color_tint(vec3(.045,.060,.073),u_aftershock_land_on,u_aftershock_land[3]),
        color_tint(vec3(.14,.125,.10),u_aftershock_land_on,u_aftershock_land[3]),
        exp(-pow((p.y-.19)*8.,2.)));
    if(rayy<0.) {
        float terrain=noise(ground*.45)*.6+noise(ground*1.8)*.4;
        vec3 soil=vec3(.038,.032,.029)+terrain*vec3(.063,.047,.029);
        if(u_aftershock_land_on==1)soil*=u_aftershock_land[0];
        soil+=canvas*.055*min(1.,effect(1)+(u_layer_mode==0 ? 0. : effect(33554432)+effect(67108864)));
        scene=mix(vec3(.14,.125,.10),soil,haze);
        float recent=floor((clock-5.)/36.);
        for(int j=0;j<8;j++) {
            if(u_event_blasts==0 && j>=3) break;
            float id=u_event_blasts==1 ? u_blast_events[j].y : recent-float(j);
            float age=clock-blast_birth(id);
            if(id>=0.) {
                float r=length(ground-blast_site(id));
                float craterLife=(u_event_blasts==1 ? 1.-smoothstep(15.,20.,age) : 1.)*blast_retirement(id,clock);
                scene*=1.-.6*exp(-r*r*.7)*smoothstep(0.,2.,age)*craterLife*effect(131072);
                scene+=blast_ring(ground,id,age,1.2)*haze*blast_retirement(id,clock);
            }
        }
        for(int j=0;j<8;j++) {
            vec4 e=u_shockwaves[j];
            if(e.z>0.) scene+=blast_ring(ground,e.y,clock-e.x,e.z)*haze;
        }
    }
    scene+=blast_aurora(p,clock,camera,camx);
    // Flash the ground before the depth-sorted foreground plumes are composited.
    float flashId=blast_latest(clock),flashAge=clock-blast_birth(flashId);
    if(flashId>=0. && flashAge>=0. && flashAge<2. && rayy<0.){
        float front=1.-smoothstep(flashAge*180.,flashAge*180.+2.,length(ground-blast_site(flashId)));
        vec3 groundTone=1.-exp(-scene*1.5);
        groundTone=mix(groundTone,blast_material_negative(canvas),front*exp(-flashAge*1.8)*(1.-smoothstep(1.5,2.,flashAge))*.9*effect(2097152));
        scene=-log(max(vec3(.00001),1.-clamp(groundTone,0.,.99999)))/1.5;
    }
    vec3 cloudOrder=blast_cloud_order(clock);
    float cloudIds[8];float depths[8];
    for(int i=0;i<8;i++) {
        float id=-1.;
        if(u_event_blasts==1) id=u_blast_events[i].y;
        else if(i<3) id=cloudOrder[i];
        cloudIds[i]=id;depths[i]=id>=0. ? blast_site(id).y : -1000.;
    }
    if(u_event_blasts==1) for(int pass=0;pass<7;pass++) for(int i=0;i<7;i++) {
        if(depths[i]<depths[i+1]) {
            float temp=depths[i];depths[i]=depths[i+1];depths[i+1]=temp;
            temp=cloudIds[i];cloudIds[i]=cloudIds[i+1];cloudIds[i+1]=temp;
        }
    }
    for(int j=0;j<8;j++) {
        if(u_event_blasts==0 && j>=3) break;
        float id=cloudIds[j],age=clock-blast_birth(id);
        vec2 site=blast_site(id);float dz=site.y-camera;
        float lifeEnd=u_event_blasts==1 ? 20. : 86.;
        if(id>=0. && age>0. && age<lifeEnd && dz>1.) {
            float life=smoothstep(0.,.5,age)*(1.-smoothstep(u_event_blasts==1 ? 15. : 64.,lifeEnd,age))
                *smoothstep(1.,4.,dz)*blast_retirement(id,clock);
            vec2 local=vec2(p.x*dz*1.6+camx-site.x,(p.y*1.6-.32)*dz+6.);
            float growth=u_event_blasts==1 ? .22 : .075;
            float character=hash(vec2(id,91.7));
            float height=(5.5*(1.-exp(-age*growth))+age*(u_event_blasts==1 ? .50 : .09))*(1.+.06*character);
            float width=(.35+2.6*(1.-exp(-age*growth))+age*(u_event_blasts==1 ? .065 : .028))*(1.15+.18*character);
            float stemW=(.23+.48*(1.-exp(-age*.1)))*(1.+.24*sin(local.y*4.+clock*.18))*(1.10+.15*character);
            float bend=sin(local.y*.65+clock*.12)*.15*local.y/8.;
            float stem=exp(-pow(abs((local.x-bend)/stemW),4.))
                *smoothstep(0.,.3,local.y)*(1.-smoothstep(height-.2,height+.5,local.y));
            float unravel=1.-smoothstep(lifeEnd*.35,lifeEnd*.85,age);
            float density=stem*.85*unravel;
            float rolls=noise(local*vec2(3.+character*2.,2.)-vec2(character*8.,clock*.25));
            vec3 cloud=mix(vec3(.085,.088,.087),vec3(.38,.32,.23),rolls)
                +vec3(.22,.075,.008)*exp(-age*.06);
            if(u_aftershock_land_on==1)cloud*=u_aftershock_land[1];
            float skirt=exp(-pow(abs(local.x/(.8+width*.75)),4.)-pow((local.y-.25)/.42,2.));
            density=max(density,skirt*.65*unravel);
            for(int k=0;k<9;k++) {
                float a=float(k)*2.39996+character*.65;
                float lobe=hash(vec2(id,float(k)+37.));
                vec2 center=vec2(cos(a)*width*(.52+.20*lobe),height+sin(a)*width*(.13+.10*lobe));
                vec2 q=(local-center)/vec2(width*(.39+.16*lobe),width*(.28+.14*lobe));
                float n=noise(local*2.+vec2(clock*.10,id));
                float rr=dot(q,q)+(n-.5)*(.22+.14*character);
                float puff=(1.-smoothstep(.70,1.05,rr))
                    *mix(.45+.55*noise(local*1.8-vec2(0.,clock*.3)),1.,unravel);
                float light=clamp(.50+.25*(-q.x+q.y)+.3*sqrt(max(0.,1.-rr)),0.,1.);
                vec3 shade=mix(vec3(.085,.09,.092),vec3(.55,.46,.31),light);
                shade+=vec3(.50,.13,.015)*exp(-age*.13)*(1.-light);
                shade*=.78+.36*noise(local*(2.2+character*1.8)+vec2(id*7.,-clock*.15));
                cloud=mix(cloud,shade,puff);density=max(density,puff);
            }
            float cloudHaze=exp(-dz*.012);
            cloud*=.78+.40*noise(local*3.-vec2(0.,clock*.10));
            float luminance=dot(cloud,vec3(.2126,.7152,.0722));
            cloud=mix(cloud,color_tint(luminance*blast_plume_tint(id),u_aftershock_land_on,u_aftershock_land[2])*1.7,.88);
            scene=mix(scene,mix(vec3(.14,.125,.10),cloud,cloudHaze),density*life);
        }
    }
    scene=1.-exp(-scene*1.5);
    return clamp(scene,0.,1.);
}

// Material siblings share the existing transformed field and audio clocks.
vec3 selected_materials() {
    if(u_layer_mode==0) return vec3(1.,0.,0.);
    if(u_layer_mode==2) return u_material_mix;
    vec3 chosen=vec3(effect(1),effect(33554432),effect(67108864));
    return chosen/max(1.,chosen.x+chosen.y+chosen.z);
}
vec3 echo_material(vec2 q) {
    vec2 uv=.5+.46*sin(q*.38);
    vec2 ink=texture(u_echo_history,uv).rg;
    float density=ink.x+ink.y;
    vec2 h=vec2(1./512.,0.);
    float gx=texture(u_echo_history,uv+h).r-texture(u_echo_history,uv-h).r;
    float gy=texture(u_echo_history,uv+h.yx).r-texture(u_echo_history,uv-h.yx).r;
    float ridge=clamp(length(vec2(gx,gy))*26.,0.,1.);
    float hue=ink.y/max(density,.001)*1.7+q.y*.06+.08*sin(u_drift_time*.08);
    vec3 pigment=.5+.5*cos(6.28318*(hue+vec3(0.,.34,.67)));
    float body=smoothstep(.012,.20,density);
    float strands=pow(.5+.5*sin(log(1.+density*12.)*25.+ink.y*9.),10.);
    if(u_material_echo_on==1)
        return pigment*body*(u_material_echo[0]*.22+u_material_echo[1]*strands*1.65+u_material_echo[2]*ridge*.8);
    return pigment*body*(.22+strands*1.65+ridge*.8);
}

// Original bounded procedural materials, evaluated in the existing carrier.
vec3 ink_archipelago(vec2 q, float bass, float flux, float sparkle) {
    vec2 p=q*1.8+vec2(u_time*.055,-u_time*.037);
    float warp=fbm(p*.6+vec2(0.,u_time*.035));
    float field=fbm(p+vec2(warp*2.,sin(p.x*.8+u_time*.08)*.6));
    float islands=smoothstep(.28,.66,field);
    float veinPhase=field*(18.+bass*3.)+warp*2.;
    float vein=pow(.5+.5*sin(veinPhase*6.283),18.);
    float channels=smoothstep(.035,.12,abs(fract(veinPhase)-.5));
    vec3 deep=u_ink_colors_on==1?u_ink_colors[0]:vec3(.012,.023,.032);
    vec3 body=u_ink_colors_on==1?u_ink_colors[1]:vec3(.12,.54,.48);
    vec3 accent=u_ink_colors_on==1?u_ink_colors[2]:vec3(.87,.58,.32);
    vec3 pearl=u_ink_colors_on==1?u_ink_colors[3]:vec3(.78,.86,.72);
    return mix(deep,mix(body,accent,smoothstep(.52,.72,field)),islands)*(.3+.7*channels)
        +pearl*vein*islands*(.06+.32*sparkle+.12*flux);
}
vec3 interference_silk(vec2 q,float bass,float flux,float sparkle) {
    vec2 p=q*2.;float t=u_time*.13;
    float a=sin(p.x*4.+sin(p.y*.9+t)*2.+t);
    float b=sin(dot(p,vec2(3.7,1.6))+sin(p.x*.8-t)*2.3-t);
    float beat=.5+.5*sin((a-b)*3.+length(p)*.35-t);
    float contour=pow(max(0.,1.-abs(a+b)*.5),6.);
    float detail=1.-smoothstep(.15,.8,length(fwidth(p*4.)));
    vec3 deep=u_silk_colors_on==1?u_silk_colors[0]:vec3(.025,.015,.06);
    vec3 aColor=u_silk_colors_on==1?u_silk_colors[1]:vec3(.47,.19,.68);
    vec3 bColor=u_silk_colors_on==1?u_silk_colors[2]:vec3(.13,.65,.73);
    vec3 crest=u_silk_colors_on==1?u_silk_colors[3]:vec3(.94,.70,.58);
    return mix(deep,mix(aColor,bColor,beat),(.18+.48*contour)*detail)
        +crest*pow(contour,5.)*(.10+.20*sparkle+.15*bass)*detail;
}
vec3 cellular_mosaic(vec2 q,float bass,float flux,float sparkle) {
    vec2 p=q*3.+vec2(u_time*.025,-u_time*.018),cell=floor(p),v=fract(p);
    float first=20.,second=20.,seed=0.;vec2 closest=vec2(0.);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++) {
        vec2 id=cell+vec2(x,y);float h=hash(id+vec2(31,17));
        vec2 center=vec2(x,y)+.5+.28*sin(vec2(h*23.,h*39.)+u_time*.14);
        float d=dot(center-v,center-v);
        if(d<first){second=first;first=d;seed=h;closest=center-v;}
        else second=min(second,d);
    }
    float seam=1.-smoothstep(.025,.095,second-first);
    float growth=.5+.5*sin(sqrt(first)*13.-u_time*.22-seed*6.);
    vec3 deep=u_mosaic_colors_on==1?u_mosaic_colors[0]:vec3(.008,.014,.026);
    vec3 a=u_mosaic_colors_on==1?u_mosaic_colors[1]:vec3(.78,.26,.12);
    vec3 b=u_mosaic_colors_on==1?u_mosaic_colors[2]:vec3(.08,.38,.61);
    vec3 rim=u_mosaic_colors_on==1?u_mosaic_colors[3]:vec3(.80,.71,.38);
    vec3 body=mix(a,b,seed)*(.16+.36*growth+.18*bass*growth);
    return mix(body,deep,seam)+rim*pow(seam,4.)*(.025+.16*sparkle+.08*flux);
}

vec3 liquid_alloy(vec2 q,float bass,float flux,float sparkle,float impact) {
    vec2 stream=q;
    stream += vec2(sin(q.y*1.7-u_time*.18),cos(q.x*1.3+u_time*.15))*.12;
    vec2 space=stream*3.2+vec2(u_time*.07,-u_time*.09);
    vec2 cell=floor(space),v=fract(space)-.5;
    float seed=hash(cell+vec2(21.,8.));
    float angle=seed*6.283+u_time*(.18+seed*.13);
    v=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*v;
    v.y+=.045*sin(v.x*10.+u_time*.18+seed*8.)*(1.+flux*.4);
    vec2 disk=v/vec2(.32+.035*bass,.16+.065*(.5+.5*sin(u_time*.24+seed*8.)));
    float radius=dot(disk,disk);
    float aa=max(length(fwidth(space))*8.,.015);
    float body=(1.-smoothstep(1.-aa,1.+aa,radius))*smoothstep(.3,.5,seed);
    float resolved=1.-smoothstep(.10,.35,length(fwidth(space)));
    if(body<=0. || resolved<=0.)return vec3(0.);
    vec3 normal=normalize(vec3(disk.x,disk.y,sqrt(max(.01,1.-radius))));
    float reflection=.5+.5*sin(normal.y*8.+normal.x*2.5+u_time*.09);
    vec3 copper=u_material_alloy_on==1 ? u_material_alloy[0] : vec3(.75,.28,.10);
    vec3 teal=u_material_alloy_on==1 ? u_material_alloy[1] : vec3(.08,.58,.62);
    vec3 violet=u_material_alloy_on==1 ? u_material_alloy[2] : vec3(.44,.12,.72);
    vec3 tint=mix(copper,teal,smoothstep(.25,.75,reflection));
    tint=mix(tint,violet,.5+.5*sin(seed*8.+normal.x*2.));
    vec3 object_tint=.08+.92*(.5+.5*cos(vec3(0.,2.094,4.188)
        +seed*19.+normal.y*.65+.32*sin(u_time*.16+seed*9.)));
    if(u_material_alloy_on==1)object_tint*=u_material_alloy[3];
    tint=mix(tint,object_tint,.85);
    float glint=pow(reflection,18.)*(.22+sparkle*.3);
    float rim=pow(1.-max(0.,normal.z),4.);
    vec3 chrome=(u_material_alloy_on==1 ? u_material_alloy[4] : vec3(.08,.10,.14))+tint*(.2+reflection*.55)
        +(u_material_alloy_on==1 ? u_material_alloy[5] : vec3(.65,.82,.9))*(glint+rim*.2);
    chrome*=.8+.2*max(0.,normal.y)+impact*.12;
    return chrome*body*resolved;
}
float material_segment(vec2 p,vec2 a,vec2 b) {
    vec2 d=b-a;
    return length(p-a-d*clamp(dot(p-a,d)/max(dot(d,d),.000001),0.,1.));
}
vec3 prismatic_lattice(vec2 q,float bass,float flux,float sparkle,float impact) {
    vec2 stream=q;
    stream += vec2(sin(q.y*1.5+u_time*.17),cos(q.x*1.4-u_time*.19))*.10;
    vec2 space=stream*3.0+vec2(-u_time*.055,u_time*.06);
    vec2 cell=floor(space),local=fract(space)-.5;
    float seed=hash(cell+vec2(12.,37.));
    float presence=smoothstep(.30,.48,seed);
    float resolved=1.-smoothstep(.10,.35,length(fwidth(space)));
    float aa=max(length(fwidth(space))*.6,.003);
    if(presence<=0. || resolved<=0.)return vec3(0.);
    float stage=3.+3.95*(.5-.5*cos(u_time*.065+seed*6.28));
    float sides=floor(stage),growth=smoothstep(0.,1.,fract(stage));
    float turn=u_time*(.20+seed*.16)+seed*6.283;
    vec2 front[8];vec2 back[8];
    for(int i=0;i<8;i++) {
        float index=float(i);
        float a=min(index,sides)*6.283185/sides;
        float b=index*6.283185/(sides+1.);
        vec2 vertex=mix(vec2(cos(a),sin(a)),vec2(cos(b),sin(b)),growth)*(.30+bass*.025);
        for(int face=0;face<2;face++) {
            vec3 point=vec3(vertex,float(face)*.30-.15);
            point.xz=mat2(cos(turn),sin(turn),-sin(turn),cos(turn))*point.xz;
            float tilt=.45+.32*sin(u_time*.19+seed*3.)+flux*.10*sin(seed*8.);
            point.yz=mat2(cos(tilt),sin(tilt),-sin(tilt),cos(tilt))*point.yz;
            vec2 projected=point.xy/(1.+point.z*.5);
            if(face==0) front[i]=projected;else back[i]=projected;
        }
    }
    float edge=10.,inside=1.,insideBack=1.;
    for(int i=0;i<8;i++) {
        if(float(i)>sides) break;
        int next=float(i)>=sides ? 0 : i+1;
        edge=min(edge,material_segment(local,front[i],front[next]));
        edge=min(edge,material_segment(local,back[i],back[next]));
        edge=min(edge,material_segment(local,front[i],back[i]));
        vec2 d=front[next]-front[i],v=local-front[i];
        float side=smoothstep(-.004,.004,d.x*v.y-d.y*v.x);
        inside*=side;insideBack*=1.-side;
    }
    float wire=1.-smoothstep(.006,.006+aa,edge);
    float glow=exp(-edge*65.)*(.08+sparkle*.12);
    vec3 tint=.2+.8*(.5+.5*cos(vec3(0.,2.094,4.188)+seed*6.28+local.y*2.));
    if(u_material_lattice_on==1)
        return tint*(u_material_lattice[0]*wire*(.45+sparkle*.22+impact*.10)
            +u_material_lattice[1]*glow+u_material_lattice[2]*max(inside,insideBack)*.075)*presence*resolved;
    return tint*(wire*(.45+sparkle*.22+impact*.10)+glow+max(inside,insideBack)*.075)*presence*resolved;
}

vec4 fire_coverage(vec4 weights,vec2 p)
{
    if(max(max(weights.x,weights.y),max(weights.z,weights.w))>=1.) return weights;
    float fold=.14*sin(p.x*4.+sin(p.y*3.-u_drift_time*.08));
    vec4 territory=vec4(p.y+fold,-p.y-fold,p.y*.35-fold,
        .35-length(p*vec2(.8,1.3)));
    vec4 score=weights*weights*exp(territory*4.);
    return score/max(dot(score,vec4(1.)),1e-12);
}

// Musical pigment expression, before world lighting. Reuse the existing short
// impact envelope; near-black cavities and already-hot highlights stay intact.
vec3 musical_material(vec3 material)
{
    float body=.18*smoothstep(.35,.85,clamp(.5*u_scale+.5*u_flux,0.,1.));
    float accent=.82*smoothstep(.08,.65,clamp(u_impact,0.,1.));
    float drive=body+accent;
    float peak=max(material.r,max(material.g,material.b));
    if (drive<=0. || peak<=.025) return material;
    float saturation=(peak-min(material.r,min(material.g,material.b)))/peak;
    float presence=smoothstep(.025,.18,peak)*(1.-smoothstep(.8,1.5,peak))
        *smoothstep(.04,.35,saturation)*drive;
    float gray=dot(material,vec3(.2126,.7152,.0722));
    vec3 pigment=max(vec3(0.),material+(material-gray)*(.5*presence));
    float pigment_peak=max(pigment.r,max(pigment.g,pigment.b));
    float target=min(max(peak,.98),peak*(1.+.45*presence));
    return pigment*(target/max(pigment_peak,.0001));
}

// Final coverage only: material gathering and each world's geometry keep their
// existing continuous envelopes. A shared broad field gives scenes territory
// rather than averaging unrelated horizons over the entire screen.
vec4 world_coverage(vec4 weights, vec2 p)
{
    float organic = max(0.,1.-dot(weights,vec4(1.)));
    if (max(max(weights.x,weights.y),max(weights.z,weights.w)) >= 1.
        || organic >= 1.) return weights;
    float flow = u_drift_time*.075;
    float bend = .16*sin(p.x*3.1+flow)+.07*sin(p.y*4.3-flow*.7);
    float radius = length(p*vec2(.82,1.));
    vec4 territory = vec4(
        .65-length(p*vec2(.55,1.6)), // Corridor opens around its vanishing point.
        .65-radius*1.5,              // Planet gathers centrally, then owns space.
        -p.y+bend,                   // Liquid rises in broad connected currents.
        p.y+.16*sin(p.x*4.1-flow));  // Fire climbs in sheets.
    vec4 score = weights*weights*weights*exp(territory*5.);
    float home = organic*organic*organic*exp((-territory.y)*3.);
    return score/max(home+dot(score,vec4(1.)),1e-12);
}

// Air shares one altitude, palette and continuous journey clock across its forms.
vec3 air_palette(float h) {
    return .52+.48*cos(6.28318*(h+vec3(.02,.32,.62)));
}
float air_line(vec2 p,vec2 a,vec2 b,float width) {
    vec2 d=b-a;return exp(-pow(length(p-a-d*clamp(dot(p-a,d)/max(dot(d,d),.00001),0.,1.))/width,2.));
}
vec4 air_forms() {
    if(u_directed==1) return u_air_mix;
    if(u_debug_state<22.5) {
        int id=int(u_debug_state+.5)-19;
        return vec4(id==0,id==1,id==2,id==3);
    }
    float phase=mod(u_drift_time,144.)/36.;
    int id=int(phase);float x=smoothstep(.65,1.,fract(phase));
    vec4 a=vec4(id==0,id==1,id==2,id==3);
    int next=(id+1)%4;
    return mix(a,vec4(next==0,next==1,next==2,next==3),x);
}
// Broad regions exchange ownership without fading every surface uniformly.
vec4 air_territory(vec2 p) {
    float drift=u_drift_time*.055;
    float bank=.18*sin(p.x*3.1+drift)+.09*sin(p.y*4.-drift*.6);
    return vec4(p.y*.65+bank,
        .45-abs(p.x+.14*sin(p.y*3.+drift))*.9-p.y*.12,
        .55-length(p*vec2(.85,1.))*1.5,
        -p.y*.75-bank*.5);
}
vec4 air_coverage(vec2 p,vec4 forms) {
    if(max(max(forms.x,forms.y),max(forms.z,forms.w))>=1.)return forms;
    vec4 score=forms*forms*exp(air_territory(p)*4.);
    return score/max(dot(score,vec4(1.)),1e-12);
}
float air_box(vec3 p,vec3 b) {
    vec3 q=abs(p)-b;return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.);
}
vec3 citadel_pigment(int role) {
    if(u_citadel_colors_on==1)return u_citadel_colors[role];
    vec3 a[6]=vec3[6](vec3(.48,.49,.54),vec3(.09,.28,.34),vec3(.98,.63,.27),vec3(.25,.78,.85),vec3(.61,.22,.32),vec3(.13,.14,.21));
    vec3 b[6]=vec3[6](vec3(.54,.40,.33),vec3(.22,.29,.31),vec3(1.,.88,.64),vec3(.85,.47,.27),vec3(.26,.49,.50),vec3(.14,.11,.15));
    vec3 c[6]=vec3[6](vec3(.33,.43,.44),vec3(.25,.43,.35),vec3(.72,.91,.78),vec3(.91,.71,.47),vec3(.47,.39,.57),vec3(.09,.16,.19));
    float phase=u_tower_motion.z*.014+max(0.,u_tower_visit-1.)*.38;
    int family=int(floor(phase))%3;float mixPhase=smoothstep(.65,1.,fract(phase));
    return mix(family==0?a[role]:family==1?b[role]:c[role],family==0?b[role]:family==1?c[role]:a[role],mixPhase);
}
vec4 citadel_tower(int i) {
    vec2 center=i<4 ? vec2((i%2==0?-1.:1.)*.48,(i<2?-1.:1.)*.48)
        : (i<6?vec2((i==4?-1.:1.)*.23,-.49):vec2(0.,.13));
    float height=i==6?.98:(i<2?.78:(i<4?.64:.84));
    return vec4(center,height,i==6?.205:(i<2?.13:.11));
}
vec3 citadel_emitter(int i) {
    vec4 tower=citadel_tower(i);
    return vec3(tower.x,tower.z+(i<2?.24:.10)+.015,tower.y);
}
float citadel_tower_light(int tower,float y) {
    float glow=0.;
    for(int i=0;i<4;i++) {
        vec4 event=u_tower_events[i];float age=u_drift_time-event.x;
        if(age<0. || age>5. || abs(event.y-float(tower))>.1)continue;
        float travel=exp(-pow((y-(.1+age*.85))/.24,2.));
        glow+=event.z*(exp(-age*.48)*.95+travel)*(1.-smoothstep(3.8,5.,age));
    }
    return min(1.5,glow)*u_tower_amount;
}
vec2 air_castle_map(vec3 p) {
    // Gatehouse and courtyard walls; the opening is cut through the front wall.
    float d=air_box(p-vec3(0.,.25,-.48),vec3(.5,.25,.065));
    float door=min(air_box(p-vec3(0.,.13,-.48),vec3(.12,.15,.16)),
        max(length(p.xy-vec2(0.,.28))-.12,abs(p.z+.48)-.16));
    d=max(d,-door);
    d=min(d,air_box(p-vec3(0.,.25,.48),vec3(.5,.25,.065)));
    d=min(d,air_box(vec3(abs(p.x)-.48,p.y-.25,p.z),vec3(.065,.25,.5)));
    float roof=10.;
    for(int i=0;i<7;i++) {
        float id=float(i);
        vec4 descriptor=citadel_tower(i);
        vec2 center=descriptor.xy;float h=descriptor.z,rad=descriptor.w;
        vec3 q=p-vec3(center.x,0.,center.y);
        float bound=air_box(q-vec3(0.,h*.5+(i==6?.42:0.),0.),vec3(i==6?.36:rad+.06,h*.5+(i==6?.70:(i<2?.25:.11)),i==6?.36:rad+.06));
        if(bound>min(d,roof))continue;
        float cylinder=max(length(q.xz)-rad,abs(q.y-h*.5)-h*.5);
        d=min(d,cylinder);
        // Cap with ring parapet and discrete merlons, not a flat printed roof.
        float ring=max(abs(length(q.xz)-rad)-.022,abs(q.y-h)-.035);
        float toothAngle=floor(atan(q.z,q.x)/.62831853+.5)*.62831853;
        vec2 toothAxis=vec2(cos(toothAngle),sin(toothAngle));
        float merlon=air_box(vec3(dot(q.xz,toothAxis)-rad,q.y-h-.065,
            dot(q.xz,vec2(-toothAxis.y,toothAxis.x))),vec3(.028,.03,.030));
        if(i<6)d=min(d,min(ring,merlon));
        if(i<2) {
            // Twin watch spires distinguish the gate towers from rear parapets.
            float spire=max(length(q.xz)-.15*(1.-clamp((q.y-h)/.24,0.,1.)),abs(q.y-h-.12)-.12);
            roof=min(roof,spire*.75);
        }
        if(i==6) {
            float cone=max(length(q.xz)-.235*(1.-clamp((q.y-h)/.40,0.,1.)),abs(q.y-h-.2)-.2);
            roof=min(roof,cone*.8);
            // Observatory armillary crown: two angled structural rings.
            vec3 arm=q-vec3(0.,h+.76,0.);
            float survey=u_tower_motion.z*.42+u_time*.055;
            float tilt=.28*sin(survey*.7)+.10*u_tower_motion.x;
            arm.yz=mat2(cos(tilt),sin(tilt),-sin(tilt),cos(tilt))*arm.yz;
            vec3 precess=arm;precess.xz=mat2(cos(survey),sin(survey),-sin(survey),cos(survey))*precess.xz;
            vec3 tilted=vec3(precess.x,precess.y*.82-precess.z*.57,precess.y*.57+precess.z*.82);
            float ringA=length(vec2(length(arm.xz)-.315,arm.y))-.014;
            float ringB=length(vec2(length(tilted.xy)-.31,tilted.z))-.012;
            roof=min(roof,min(ringA,ringB));
        }
    }
    // Broad ribs rise from the courtyard into the observatory drum.
    vec3 rib=vec3(abs(p.x)-.255,p.y-.62,p.z-.13);
    float buttress=air_box(vec3(rib.x*.82+rib.y*.57,-rib.x*.57+rib.y*.82,rib.z),vec3(.024,.31,.038));
    d=min(d,buttress);
    // Wall crenellations repeat in object space and rotate with the masonry.
    vec3 crenel=p;crenel.x=mod(p.x+.055,.11)-.055;
    d=min(d,max(air_box(crenel-vec3(0.,.535,-.48),vec3(.032,.04,.07)),abs(p.x)-.48));
    // Closed gate fitted inside the arch, with no projecting bridge.
    float gate=max(air_box(p-vec3(0.,.18,-.515),vec3(.11,.19,.018)),door);
    // Attached earth shares the castle's 3D coordinates and depth, top meets y=0.
    float earth=max(length(p.xz)-max(.24,.94+p.y*.95),abs(p.y+.24)-.26);
    earth+=(.025*sin(p.x*19.)*sin(p.z*17.)+.034*sin(atan(p.z,p.x)*7.+p.y*8.))
        *(1.-smoothstep(-.15,-.01,p.y));
    // Taper and rock displacement are not a unit-distance field: conservative steps.
    earth*=.45;
    vec2 result=vec2(d,1.);
    if(roof<result.x)result=vec2(roof,2.);
    if(gate<result.x)result=vec2(gate,3.);
    if(earth<result.x)result=vec2(earth,4.);
    return result;
}
vec3 air_citadel(vec2 p,vec3 sky,float amount) {
    if(amount<=0. || effect(1073741824)<=0.)return sky;
    float clock=u_time*.22+u_drift_time*.025;
    vec2 q=p-vec2(0.,0.);
    float orbit=.35+u_time*.015+u_drift_time*.0035;
    float approach=2.8+.20*sin(u_drift_time*.055);
    vec3 ro=vec3(approach*sin(orbit),1.35+.08*sin(clock*.23),-approach*cos(orbit));
    vec3 fw=normalize(vec3(0.,.54,0.)-ro),right=normalize(cross(fw,vec3(0,1,0))),up=cross(right,fw);
    float focal=u_citadel_focal>0. ? u_citadel_focal : 1.13;
    vec3 rd=normalize(fw+right*q.x*focal+up*(q.y-.09)*focal);
    float surfaceDepth=100.;
    // Castle and attached island participate in the same depth trace.
    // Conservative ray/box rejection only: retained rays keep the exact trace.
    // Bounds include the island displacement, tower merlons and central cone.
    vec3 safeRay=vec3(rd.x<0. ? -max(abs(rd.x),1e-8) : max(abs(rd.x),1e-8),
        rd.y<0. ? -max(abs(rd.y),1e-8) : max(abs(rd.y),1e-8),
        rd.z<0. ? -max(abs(rd.z),1e-8) : max(abs(rd.z),1e-8));
    vec3 slabA=(vec3(-1.1,-.6,-1.1)-ro)/safeRay;
    vec3 slabB=(vec3(1.1,2.12,1.1)-ro)/safeRay;
    vec3 entry=min(slabA,slabB),leave=max(slabA,slabB);
    float nearBox=max(entry.x,max(entry.y,entry.z));
    float farBox=min(leave.x,min(leave.y,leave.z));
    vec2 surfaceUV=vec2(p.x*u_resolution.y/u_resolution.x+.5,p.y+.5);
    bool cached=u_citadel_surface_on==1 && all(greaterThanEqual(surfaceUV,vec2(0.))) && all(lessThanEqual(surfaceUV,vec2(1.)));
    vec4 cachedPoint=cached?texture(u_citadel_surface,surfaceUV):vec4(0.),cachedNormal=cached?texture(u_citadel_normal,surfaceUV):vec4(0.);
    if((cached && cachedNormal.w>0.) || (!cached && abs(q.x)<.82 && q.y>-.52 && q.y<.68 && farBox>=max(1.2,nearBox) && nearBox<4.9)) {
        float t=cached?length(cachedPoint.xyz):max(1.2,nearBox);vec2 hit=cached?vec2(0.,cachedPoint.w):vec2(1.,0.);vec3 pos=cached?ro+cachedPoint.xyz:ro;
        if(!cached)for(int j=0;j<144;j++) {
            pos=ro+rd*t;hit=air_castle_map(pos);
            if(hit.x<.0008 || t>min(4.9,farBox))break;
            t+=max(.00035,hit.x*.50);
        }
        if(t<4.9 && hit.x<.0008) {
            surfaceDepth=t;
            vec2 e=vec2(.002,0.);
            vec3 normal=cached?cachedNormal.xyz:normalize(vec3(air_castle_map(pos+e.xyy).x-air_castle_map(pos-e.xyy).x,
                air_castle_map(pos+e.yxy).x-air_castle_map(pos-e.yxy).x,
                air_castle_map(pos+e.yyx).x-air_castle_map(pos-e.yyx).x));
            vec3 light=normalize(vec3(-.5,1.,-.8));
            float diffuse=max(0.,dot(normal,light));
            vec2 uv=abs(normal.x)>.6 ? pos.zy : pos.xy;
            vec2 brick=vec2(uv.x*18.+floor(uv.y*24.)*.5,uv.y*24.);
            vec2 brickAA=clamp(fwidth(uv*vec2(18.,24.)),vec2(.015),vec2(.35));
            float mortar=smoothstep(.06-brickAA.y,.06+brickAA.y,fract(brick.y))
                *smoothstep(.045-brickAA.x,.045+brickAA.x,fract(brick.x));
            vec3 stone=citadel_pigment(0)*mix(.58,1.,mortar);
            float weathering=fbm(uv*35.);
            stone*=.78+.30*weathering;
            float courses=1.-smoothstep(.025,.055,abs(fract(pos.y*8.)-.5));
            stone+=vec3(.055,.045,.07)*courses;
            if(hit.y>1.5)stone=hit.y<2.5 ? citadel_pigment(1) : citadel_pigment(0)*vec3(.45,.32,.22);
            if(hit.y>2.5 && hit.y<3.5)stone*=.35+.65*step(.13,fract(pos.x*45.))*step(.14,fract(pos.y*18.));
            if(hit.y>3.5)stone=citadel_pigment(5)*(.55+.65*noise(pos.xz*17.+pos.y*5.));
            if(hit.y>3.5 && pos.y>-.02)stone=citadel_pigment(1)*.50;
            vec3 color=color_tint(stone,u_air_citadel_on,u_air_citadel[0])*(.36+.64*diffuse);
            // Recess shading under parapets and at the wall foot, without new meshes.
            color*=.78+.22*smoothstep(.0,.10,pos.y);
            if(hit.y<1.5)color*=.83+.17*smoothstep(.0,.06,abs(pos.y-.56));
            vec2 windowAA=clamp(fwidth(uv*12.),vec2(.01),vec2(.30));
            vec2 windowCell=fract(uv*12.);
            float windows=smoothstep(.72-windowAA.x,.72+windowAA.x,windowCell.x)
                *smoothstep(.56-windowAA.y,.56+windowAA.y,windowCell.y)
                *(1.-smoothstep(1.-windowAA.x,1.,windowCell.x))
                *(1.-smoothstep(1.-windowAA.y,1.,windowCell.y))*step(.12,pos.y)*step(pos.y,.63);
            int tower=pos.x<0. ? (pos.z<0.?0:2) : (pos.z<0.?1:3);
            float selected=citadel_tower_light(tower,pos.y);
            float towerBody=1.-smoothstep(.16,.26,length(pos.xz-citadel_emitter(tower).xz));
            float district=hash(vec2(floor(uv.x*4.),floor(pos.y*8.))+vec2(tower*7));
            float windowWave=.5+.5*sin(u_tower_motion.z*2.-pos.y*5.+tower*1.7);
            float occupancy=smoothstep(.25,.8,district);
            if(hit.y<1.5)color+=color_tint(citadel_pigment(2),u_air_citadel_on,u_air_citadel[1])*windows
                *(occupancy*.36+u_tower_amount*(u_tower_motion.x*(.16+1.6*smoothstep(.3,.8,windowWave))*mix(.22,1.,occupancy)+selected*towerBody*2.6))*(1.-abs(normal.y));
            // The selected tower carries warm masonry spill and a luminous cap, not a global flash.
            color+=citadel_pigment(3)*selected*towerBody*(hit.y<1.5?.16:.48)*smoothstep(.1,.3,pos.y);
            if(hit.y>1.5 && hit.y<2.5) {
                float azimuth=atan(pos.z-.13,pos.x);
                float tracery=pow(.5+.5*sin(azimuth*8.+pos.y*25.),16.);
                color+=citadel_pigment(3)*tracery*(.045+.20*u_tower_motion.y+selected*.65)*u_tower_amount;
                color+=citadel_pigment(1)*pow(max(0.,dot(reflect(-light,normal),-rd)),24.)*.25;
            }
            // The observatory drum has a glazed rose lattice, separate from windows.
            float central=1.-smoothstep(.19,.23,length(pos.xz-vec2(0,.13)));
            float az=atan(pos.z-.13,pos.x);
            float ribsGlass=pow(.5+.5*cos(az*12.),18.);
            float glazing=central*smoothstep(.62,.69,pos.y)*(1.-smoothstep(.90,.97,pos.y))*(1.-ribsGlass);
            color=mix(color,citadel_pigment(1)*(.24+.30*diffuse),glazing*.72);
            color+=citadel_pigment(2)*glazing*(.09+u_tower_motion.x*.26+selected*.3);
            // Sparse gilded buttress/cornice lines remain attached to masonry.
            float ribs=pow(1.-abs(sin(pos.x*31.+pos.z*23.)),28.)*step(.48,pos.y);
            color+=citadel_pigment(2)*ribs*(.018+selected*.11);
            color+=vec3(.10,.25,.35)*pow(max(0.,dot(reflect(-light,normal),-rd)),24.);
            sky=mix(sky,color,amount);
        }
    }
    // citadel_panels: world-space signal panels; same surface depth, no additional castle trace.
    for(int tower=0;tower<4;tower++) {
        vec3 emitter=citadel_emitter(tower);
        float wind=u_tower_motion.x,phase=u_tower_motion.z;
        vec3 flagAnchor=emitter+vec3(0.,.22,0.);
        float turn=.4+sin(phase*.65)*(.10+.16*wind);
        vec3 axis=vec3(cos(turn),0,sin(turn)),planeNormal=cross(axis,vec3(0,1,0));
        float denom=dot(rd,planeNormal);
        if(abs(denom)>.01) {
            float depth=dot(flagAnchor-ro,planeNormal)/denom;
            vec3 point=ro+rd*depth-flagAnchor;vec2 panel=vec2(dot(point,axis),point.y);
            float lengthPanel=.275+.035*wind+.012*sin(tower*3.);
            float freeEnd=clamp(panel.x/lengthPanel,0.,1.);
            float flutter=(sin(panel.x*20.-phase*2.8)*(.006+.015*wind)
                +sin(panel.x*10.-phase*1.6)*.006*wind)*pow(freeEnd,1.3)
                +sin(phase*5.+tower*.25)*u_tower_motion.w*.008*freeEnd;
            panel.y-=flutter*u_tower_amount;
            if(depth>0. && depth<surfaceDepth-.002 && panel.x>0. && panel.x<lengthPanel && panel.y<.06 && panel.y>-.09+panel.x*.06) {
                vec2 uv=panel/vec2(lengthPanel,.15);
                float threads=pow(.5+.5*sin((uv.x+uv.y)*45.),10.);
                float border=1.-smoothstep(.006,.018,min(min(panel.x,lengthPanel-panel.x),min(.06-panel.y,panel.y+.09-panel.x*.06)));
                float selected=citadel_tower_light(tower,emitter.y);
                vec3 silk=citadel_pigment(4)*(.55+.3*abs(dot(planeNormal,normalize(vec3(-.5,1,-.8))))+.15*threads);
                silk+=citadel_pigment(2)*selected*.35+citadel_pigment(3)*border*(.12+selected*.90);
                sky=mix(sky,silk,amount*u_tower_amount);
            }
        }
        vec3 poleView=emitter-ro,tipView=(flagAnchor+vec3(0.,.065,0.))-ro;
        vec2 pole=vec2(dot(poleView,right),dot(poleView,up))/max(.1,dot(poleView,fw))/focal+vec2(0,.09);
        vec2 tip=vec2(dot(tipView,right),dot(tipView,up))/max(.1,dot(tipView,fw))/focal+vec2(0,.09);
        if(dot(tipView,fw)>0. && surfaceDepth>dot(poleView,rd)-.01)
            sky=mix(sky,citadel_pigment(0)*1.3,air_line(p,pole,tip,.0012)*amount*u_tower_amount);
        // A rooted beacon breathes with highs; selected tower remembers the hit.
        float sweep=u_time*.09+phase*.12+float(tower)*.37,slot=floor(sweep);
        float ease=smoothstep(.15,.80,fract(sweep));
        float sway=mix(sin(slot*1.7+tower*2.1),sin((slot+1.)*1.7+tower*2.1),ease);
        float crossSway=mix(cos(slot*1.3+tower),cos((slot+1.)*1.3+tower),ease);
        vec3 direction=normalize(vec3(sway*.65,.90,crossSway*.50));
        vec3 w=ro-emitter;float crossTerm=dot(rd,direction),den=max(.0001,1.-crossTerm*crossTerm);
        float along=(dot(direction,w)-crossTerm*dot(rd,w))/den,depth=along*crossTerm-dot(rd,w);
        float distance=length(ro+rd*depth-(emitter+direction*max(0.,along)));
        float selected=citadel_tower_light(tower,emitter.y);
        float beam=exp(-pow(distance/(.0045+max(0.,along)*.0017),2.))*exp(-max(0.,along)*.42);
        float halo=exp(-pow(distance/(.013+max(0.,along)*.004),2.))*exp(-max(0.,along)*.65);
        float visible=step(0.,along)*step(0.,depth)*step(depth,surfaceDepth-.005);
        vec3 beacon=citadel_pigment(3);if(u_citadel_colors_on==0)beacon=pow(beacon,vec3(1.65))/max(max(beacon.r,max(beacon.g,beacon.b)),.01);
        sky+=color_tint(beacon,u_air_citadel_on,u_air_citadel[3])*visible
            *(beam*(.16+2.2*smoothstep(.30,.82,.55*u_scale+.25*u_flux+.20*u_sparkle)+selected*2.3)
                +halo*(.04+.45*smoothstep(.30,.82,.55*u_scale+.25*u_flux+.20*u_sparkle)+selected*.30))*amount*u_tower_amount;
    }
    // World-space launch, local bright burst and individually fading sparks.
    for(int i=0;i<4;i++) {
        vec4 event=u_tower_events[i];float seconds=u_drift_time-event.x;
        if(seconds<0. || seconds>4.8 || u_tower_amount<=0.)continue;
        int tower=int(event.y);vec3 launchWorld=citadel_emitter(tower);
        vec3 originWorld=launchWorld+vec3((event.w-.5)*.25,(tower<2?.40:.65)+event.w*.10,0.);
        vec3 launchView=launchWorld-ro,originView=originWorld-ro;
        if(dot(originView,fw)<=0.)continue;
        vec2 launch=vec2(dot(launchView,right),dot(launchView,up))/max(.1,dot(launchView,fw))/focal+vec2(0,.09);
        vec2 origin=vec2(dot(originView,right),dot(originView,up))/max(.1,dot(originView,fw))/focal+vec2(0,.09);
        vec3 hue=u_citadel_colors_on==1?citadel_pigment(3):pow(air_palette(event.w+event.y*.23),vec3(2.2));
        if(u_citadel_colors_on==0)hue/=max(max(hue.r,max(hue.g,hue.b)),.001);
        hue=color_tint(hue,u_air_citadel_on,u_air_citadel[3]);
        float ascent=clamp(seconds/.65,0.,1.);
        if(seconds<.65 && surfaceDepth>dot(launchView,rd)) {
            vec2 head=mix(launch,origin,ascent),tail=mix(launch,origin,max(0.,ascent-.22));
            sky+=(hue*(air_line(p,head,tail,.006)*.40+air_line(p,head,tail,.0015)*2.0)
                +vec3(1.,.84,.57)*exp(-length(p-head)*700.)*.50)*event.z*amount*u_tower_amount;
        }
        float age=seconds-.65;
        if(age<0. || age>4. || surfaceDepth<dot(originView,rd) || length(p-origin)>.10+age*.15)continue;
        float peak=exp(-age*12.)*exp(-pow(length(p-origin)/(.008+.030*min(1.,age*9.)),2.));
        sky+=hue*peak*2.7*event.z*amount*u_tower_amount;
        for(int k=0;k<20;k++) {
            float angle=float(k)*2.399963+event.w*6.28;
            vec2 velocity=vec2(cos(angle),sin(angle)*.75)*(.065+.045*hash(vec2(k,event.w)));
            vec2 head=origin+velocity*age-vec2(0,age*age*.011);
            float oldAge=max(0.,age-.18);
            vec2 tail=origin+velocity*oldAge-vec2(0,oldAge*oldAge*.011);
            float fade=smoothstep(0.,.04,age)*exp(-age*.88)*(1.-smoothstep(3.2,4.,age));
            float sparkle=.35+.65*pow(.5+.5*sin(float(k)*4.7+age*13.),8.);
            float core=air_line(p,head,tail,.0016),glow=air_line(p,head,tail,.0065);
            sky+=hue*(core*(1.4+sparkle*2.0)+glow*.34)*fade*event.z
                *(.85+.60*u_tower_motion.y)*amount*u_tower_amount;
        }
    }
    return sky;
}
// Shared source material gathers onto a spherical surface or spiraling vortex.
vec2 air_material_domain(vec2 p,vec4 form) {
    float spin=u_time*.18;
    float a=atan(p.y,p.x)+spin+log(length(p)+.03)*3.;
    vec2 whirl=vec2(cos(a),sin(a))*(.3+length(p)*2.);
    vec2 disk=(p-vec2(0.,-5.18))/5.;
    vec3 n=vec3(disk,sqrt(max(0.,1.-dot(disk,disk))));
    vec3 surface=vec3(cos(spin*.18)*n.x+sin(spin*.18)*n.z,n.y,-sin(spin*.18)*n.x+cos(spin*.18)*n.z);
    vec2 planet=vec2(surface.x*2.,n.z*4.-.65)+surface.z*vec2(.30,.12);
    // Finite flight projection: gathering never interpolates a runaway scroll.
    vec2 flight=(p-vec2(0.,.10))/(.35+length(p-vec2(0.,.10)))*1.7;
    flight.x+=.18*sin(flight.y*2.+u_time*.10);
    vec2 weather=vec2(flight.x*.8,flight.y*1.3);
    return flight*form.x+weather*form.y+whirl*form.z+planet*form.w;
}

vec3 air_scene(vec2 p,vec3 material,vec4 form) {
    float clock=u_time*.15+u_drift_time*.015;
    float energy=clamp(max(u_scale,u_flux*.8),0.,1.);
    float storm=form.y, vortex=form.z, citadel=form.w;
    float weather=storm+vortex;
    float bank=storm*.20*sin(clock*.7)+form.x*.025*sin(clock*.3);
    p=mat2(cos(bank),sin(bank),-sin(bank),cos(bank))*p;
    vec3 pigment=material/(.25+max(material.r,max(material.g,material.b)));
    vec3 sky=color_tint(mix(vec3(.025,.038,.12),vec3(.27,.37,.48),clamp(.6-p.y,0.,1.)),u_air_sky_on,u_air_sky[0]);
    sky=mix(sky,color_tint(vec3(.008,.012,.034),u_air_sky_on,u_air_sky[1]),weather*.83+citadel*.6);
    sky+=storm*vec3(.035,.055,.10)*(.4+.6*fbm(p*5.+vec2(0.,clock*.2)));
    // Sparse high-altitude stars remain anchored as the lower atmosphere moves.
    vec2 starUV=p+vec2(clock*.024,.015*sin(clock*.3));
    vec2 starCell=floor(starUV*220.);
    float starSeed=fract(sin(dot(starCell,vec2(127.1,311.7)))*43758.5453);
    float star=exp(-dot(fract(starUV*220.)-.5,fract(starUV*220.)-.5)*140.)*step(.992,starSeed);
    sky+=(u_sky_stars_on==1 ? vec3(.25,.36,.50)*(u_sky_stars[0]/vec3(.55,.72,1.))
        : vec3(.25,.36,.50))*star*citadel*(.5+u_sparkle*.5);
    // Additional accepted Cosmic star sheets; existing Citadel pinpoints remain.
    if(form.x+citadel>0.) {
        float starStretch=1.+form.x*(1.5*energy+2.5*u_impact);
        sky+=cosmic_star_layer(p,starStretch)*effect(512)
            *(citadel+form.x*smoothstep(.04,.23,p.y)*1.25);
    }
    float horizon=.035-.05*p.x*p.x;
    // Distant patchwork fields projected below the cloud deck, never a flat grid.
    if(p.y<horizon && citadel<1.) {
        float distance=1./max(.02,horizon-p.y);
        vec2 ground=vec2(p.x*distance+sin(clock*.11)*1.8,distance+clock*2.);
        // Bend field boundaries gently; the land is well below our flight path.
        ground*=mix(1.35,2.4,storm);
        ground+=vec2(.20*sin(ground.y*.7),.17*sin(ground.x*.8));
        vec2 cell=floor(ground*vec2(1.2,.55));
        float seed=fract(sin(dot(cell,vec2(127.1,311.7)))*43758.5453);
        float edge=min(min(fract(ground.x*1.2),1.-fract(ground.x*1.2)),min(fract(ground.y*.55),1.-fract(ground.y*.55)));
        vec3 farms=mix(vec3(.055,.10,.085),vec3(.21,.19,.10),seed)*(.88+.12*smoothstep(.015,.04,edge));
        float coast=smoothstep(.3,.65,fbm(ground*.024));
        farms=mix(vec3(.025,.08,.14),farms,mix(max(.60,coast),coast,vortex));
        sky=mix(sky,color_tint(farms,u_air_sky_on,u_air_sky[2]),exp(-distance*.016)*mix(1.-smoothstep(18.,45.,distance),1.,vortex)*(1.-vortex*.9)*(1.-citadel)*(1.-storm));
    }
    // The planet is specific to the Citadel scene; existing Planet Canvas stays intact.
    vec2 planet=(p-vec2(0.,-5.28))/5.;
    float disk=dot(planet,planet);
    if(citadel>0.) {
        float limb=exp(-pow((sqrt(disk)-1.)*380.,2.));
        sky+=vec3(.07,.36,.9)*limb*citadel;
        if(disk<1.) {
            vec3 n=vec3(planet,sqrt(1.-disk));
            float drift=u_time*.19+u_drift_time*.035;
            vec3 surface=vec3(cos(drift)*n.x+sin(drift)*n.z,n.y,-sin(drift)*n.x+cos(drift)*n.z);
            vec2 domain=vec2(atan(surface.x,surface.z)*1.9,surface.y*6.);
            domain+=.20*vec2(sin(domain.y*2.1+drift),cos(domain.x*1.7-drift*.7));
            float continents=fbm(domain*1.35);
            float grain=fbm(domain*4.3+vec2(drift*.28,-drift*.10));
            vec3 sea=citadel_pigment(5)*(.48+.55*grain);
            vec3 land=mix(sea,citadel_pigment(1)*(.85+.6*grain),smoothstep(.40,.64,continents));
            land=mix(land,material*(.35+.4*grain),.26);
            float ribbons=pow(.5+.5*sin(domain.y*11.+sin(domain.x*3.-drift)*2.6+drift*1.3),8.);
            land+=citadel_pigment(2)*ribbons*.035*(.3+energy);
            float clouds=smoothstep(.52,.76,fbm(domain*3.4+vec2(drift*.35,drift*.12)));
            land=mix(land,citadel_pigment(0)*1.05,clouds*.33);
            sky=mix(sky,color_tint(land,u_air_citadel_on,u_air_citadel[2])*(.42+.58*max(0.,dot(n,normalize(vec3(-.4,.6,1.))))),citadel);
        }
    }
    vec2 eye=vec2(.05*sin(clock*.21),.045*cos(clock*.17));
    float angle=clock*(.4+vortex*2.8);
    vec2 tunnel=p-eye;
    tunnel=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*tunnel;
    float radius=length(tunnel),theta=atan(tunnel.y,tunnel.x);
    if(effect(134217728)>0. || (weather>0. && (effect(536870912)>0. || u_daddy_long_legs>0.))) {
        // Far-to-near billows expand around the flight path and pass the camera.
        vec2 vanish=vec2(.0,.10);
        if(form.x>0.) {
        // Thin stratus sheets pass above the fuller cumulus banks.
        vec2 sheetUV=p*vec2(2.2,13.)+vec2(clock*.08,-clock*.25);
        float sheetNoise=fbm(sheetUV+vec2(fbm(sheetUV*.6),0.));
        float sheet=smoothstep(.44,.68,sheetNoise)*smoothstep(.10,.24,p.y)
            *(1.-smoothstep(.38,.58,p.y));
        sky=mix(sky,vec3(.24,.31,.43)+sheetNoise*.16,sheet*.44*form.x*effect(134217728));
        float travel=clock*.8;
        for(int i=9;i>=0;i--) {
            float serial=floor(travel)+float(i),z=(float(i)+1.-fract(travel))*1.7+.12;
            vec2 center=vanish+vec2(sin(serial*2.4)*2.5,cos(serial*1.7)*.8-.35)/z;
            vec2 cloudUV=(p-center)*z/vec2(1.1,.72);
            float n=fbm(cloudUV*2.+serial+clock*.1);
            float lobes=sin(cloudUV.x*5.+serial)*sin(cloudUV.y*4.-serial)*.25;
            float mask=(1.-smoothstep(.32+n*.4,1.2+n*.5,dot(cloudUV,cloudUV)+lobes))
                *smoothstep(.12,.6,z)*(1.-smoothstep(13.,17.,z));
            vec3 tint=mix(vec3(.13,.22,.32),vec3(.52,.58,.65),n);
            if(shared_spatial()) {
                // Color travels through the lit cloud interior, not its silhouette.
                float weave=smoothstep(.18,.62,n)*(.22+.18*energy);
                tint=mix(tint,material*(.55+n*.55),weave);
            }
            sky=mix(sky,color_tint(tint,u_air_clouds_on,u_air_clouds[0]),mask*(.60+.18*n)*form.x*effect(134217728));
        }
        }
        // Reuse the accepted corridor's turns and perspective with cloud surfaces.
        if(storm>0.) {
            // Bend the corridor projection into a vault while retaining its turns.
            vec2 archP=p;
            archP.y=.10+abs(p.y-.10);
            archP.y+=.22*pow(abs(p.x),1.45);
            archP.x+=.018*sin(p.y*9.+clock*.4);
            GeometricSurface corridor=geometric_surface(archP,1.);
            vec2 uv=corridor.uv;
            vec2 weatherUV=uv;
            if(shared_spatial())weatherUV=mix(uv,spatial_carrier(uv*.22)/.22,.28);
            float billow=fbm(weatherUV*vec2(.65,2.3)+vec2(-clock*.7,clock*.15));
            float detail=fbm(weatherUV*vec2(2.4,5.)+billow*2.);
            float rib=pow(.5+.5*cos(uv.x*1.7+billow*4.),5.);
            vec3 cloud=mix(vec3(.018,.035,.065),vec3(.30,.24,.39),smoothstep(.22,.70,billow));
            cloud*=.6+.4*detail;cloud+=vec3(.045,.08,.13)*rib;
            if(shared_spatial()) {
                float lining=smoothstep(.28,.70,billow)*(.38+.18*energy);
                cloud=mix(cloud,material*(.48+.65*detail),lining);
            }
            float seed=floor(u_air_flash_id),cell=floor(uv.x/3.);
            float origin=cell*3.+.7+fract(sin(cell*17.+seed)*437.)*1.6;
            float boltPath=origin+.11*sin(uv.y*17.+seed)+.055*sin(uv.y*47.+cell);
            float bolt=exp(-pow((uv.x-boltPath)/.022,2.));
            float fork=exp(-pow((uv.x-boltPath-max(0.,uv.y-.5)*.45)/.016,2.));
            float reach=exp(-pow(abs(uv.y-(.35+fract(sin(cell+seed)*371.)))*.9,4.));
            bolt*=reach;fork*=reach;
            float hit=smoothstep(.08,.6,u_impact)*effect(536870912);
            float litCell=step(.40,fract(sin(cell*3.+seed)*137.));
            vec3 light=vec3(.28,.50,1.)*(bolt+fork*.5)*hit*litCell;
            cloud+=vec3(.12,.20,.36)*exp(-abs(uv.x-origin)*2.)*hit*litCell;
            if(corridor.kind>2.5 || (corridor.kind>.5 && corridor.kind<1.5)) {
                // Opaque cloud vault advects forward; aurora glows above its billows.
                float curtain=exp(-pow(sin(uv.x*.55+sin(uv.y+clock*.4)) * 4.,2.));
                cloud+=color_tint(mix(vec3(.02,.45,.32),vec3(.40,.035,.48),.5+.5*sin(uv.y*.7+clock*.15)),u_air_lightning_on,u_air_lightning[1])*curtain*(.35+energy*.5)
                    *smoothstep(.2,.8,sin(uv.y));
            }
            float wall=step(.5,corridor.kind)*(1.-step(1.5,corridor.kind));
            float ceiling=step(2.5,corridor.kind);
            float fog=exp(-corridor.distance*.055);
            float cloudEdge=1.-smoothstep(7.,10.,corridor.distance);
            float coverage=(wall+ceiling)*cloudEdge*effect(134217728);
            sky=mix(sky,mix(vec3(.09,.12,.19),cloud,fog),coverage*storm);
            if(u_air_clouds_on==1)
                sky+=mix(vec3(.09,.12,.19),cloud,fog)*(u_air_clouds[0]-vec3(1.))*coverage*storm;
            sky+=color_tint(light,u_air_lightning_on,u_air_lightning[0])*fog*storm*(wall+ceiling)*cloudEdge;
        }
        if(weather>0.) {
            float throat=mix(.23,.085,energy)*(1.-vortex*.3);
            float spiral=theta+log(radius+.025)*(.65+vortex*5.35)-clock*.8;
            float folds=fbm(vec2(cos(spiral),sin(spiral))*3.+radius*vec2(2.,5.)-vec2(clock*.3,0.));
            float banks=smoothstep(throat,throat+.23,radius+sin(spiral*3.)*.028);
            float billows=fbm(tunnel*7.+vec2(clock*.16,-clock*.23));
            folds=mix(billows,folds,.25+.75*vortex);
            float rib=.5+.5*sin(spiral*5.+folds*6.+.5*sin(theta*2.+clock*.3));
            vec3 cloud=mix(vec3(.016,.017,.05),vec3(.21,.12,.29),folds);
            cloud*=.5+1.4*smoothstep(.3,.7,folds);
            cloud+=vec3(.035,.22,.22)*pow(rib,4.)*(.14+energy*.3);
            cloud=mix(cloud,pigment*.24,.2*folds);
            float stream=pow(.5+.5*sin(theta*2.-clock*.8+radius*4.),3.);
            cloud=mix(cloud,air_palette(folds*.6+clock*.065+sin(theta)*.12)*(.20+.48*rib),.75*vortex);
            cloud=mix(cloud,material*(.65+energy*.9),.38*vortex);
            cloud+=air_palette(folds*.6+clock*.065+sin(theta)*.12)*stream*pow(rib,5.)*(.16+energy*.36)*vortex;
            sky=mix(sky,color_tint(cloud,u_air_clouds_on,u_air_clouds[2]),banks*vortex*effect(134217728));
            sky+=air_palette(sin(theta)*.1+.5)*pow(rib,18.)*banks*(.025+u_sparkle*.09)*vortex*effect(134217728);
            // Independent electrical layers, with no shadow/face overlay.
            float flash=smoothstep(.10,.6,u_impact)*effect(536870912);
            float seed=floor(u_air_flash_id);
            // Archived FX experiment: Daddy Long Legs. Never enabled by authored mode.
            if(vortex>0. && u_daddy_long_legs>0.) for(int arcIndex=0;arcIndex<3;arcIndex++) {
                float id=float(arcIndex);
                // Crawling junctions follow different orbits and repeatedly dive inward.
                float hubAngle=id*2.094+clock*(.44+id*.13)+.40*sin(clock*.38+id);
                float hubRadius=.14+.38*(.5+.5*sin(clock*.67+id*2.3));
                vec2 hub=vec2(cos(hubAngle),sin(hubAngle))*hubRadius;
                vec3 web=vec3(0.);
                for(int leg=0;leg<5;leg++) {
                    float strand=float(leg),side=mod(strand,2.)*2.-1.;
                    float reach=.22+.23*(.5+.5*sin(clock*.55+strand*2.+id));
                    float endRadius=clamp(hubRadius+side*reach,.075,.86);
                    float endAngle=hubAngle+side*(.55+strand*.18)+.28*sin(clock*.8+strand);
                    vec2 endPoint=vec2(cos(endAngle),sin(endAngle))*endRadius;
                    if(leg==4) {
                        float next=mod(id+1.,3.);
                        float nextAngle=next*2.094+clock*(.44+next*.13)+.40*sin(clock*.38+next);
                        float nextRadius=.14+.38*(.5+.5*sin(clock*.67+next*2.3));
                        endPoint=vec2(cos(nextAngle),sin(nextAngle))*nextRadius;
                    }
                    vec2 control=(hub+endPoint)*.5
                        +vec2(-sin(hubAngle),cos(hubAngle))*side*.13;
                    float active=.22+.78*pow(.5+.5*sin(clock*1.4+strand*1.7+id),2.);
                    vec3 tint=color_tint(air_palette(clock*.09+id*.23+strand*.075),u_air_daddy_on,u_air_daddy);
                    for(int segment=0;segment<4;segment++) {
                        float a=float(segment)*.25,b=a+.25;
                        vec2 pa=mix(mix(hub,control,a),mix(control,endPoint,a),a);
                        vec2 pb=mix(mix(hub,control,b),mix(control,endPoint,b),b);
                        // Shared vertices retain connections while the charge jitters.
                        pa+=.016*sin(vec2(a*73.+clock*8.+strand,a*91.-clock*6.+id))*sin(a*3.14159);
                        pb+=.016*sin(vec2(b*73.+clock*8.+strand,b*91.-clock*6.+id))*sin(b*3.14159);
                        float thread=air_line(tunnel,pa,pb,.0032);
                        float glowThread=air_line(tunnel,pa,pb,.011)*.13;
                        vec2 forkTip=pb+vec2(cos(endAngle+side*.8),sin(endAngle+side*.8))
                            *(.045+.045*sin(clock+strand)*sin(clock+strand));
                        float fork=air_line(tunnel,pb,forkTip,.0011)*smoothstep(.15,.65,b);
                        web+=tint*(thread+glowThread+fork*.55)*active;
                    }
                }
                // A small traveling pulse marks each junction without filling the eye.
                web+=color_tint(air_palette(clock*.09+id*.23),u_air_daddy_on,u_air_daddy)*exp(-length(tunnel-hub)*190.)*.55;
                sky+=web/(1.+web*.45)*(.27+.65*energy+.32*u_air_afterglow)
                    *smoothstep(.045,.095,radius)*vortex*u_daddy_long_legs;
            }
            // Wall-bound discharges: polar paths cannot cross the open eye.
            // Each anchored path grows in uneven steps, then clears completely.
            if(vortex>0. && effect(536870912)>0.) for(int strike=0;strike<2;strike++) {
                float id=float(strike),cycle=u_drift_time*.20+id*.47;
                float life=fract(cycle),serial=floor(cycle)+id*17.;
                float envelope=smoothstep(.015,.07,life)*(1.-smoothstep(.64,.86,life));
                float phase=clamp((life-.025)/.55,0.,1.)*7.;
                float growth=(floor(phase)+smoothstep(.22,.75,fract(phase)))/7.;
                float start=.28+.07*fract(sin(serial*7.)*437.);
                float along=radius-start;
                float reach=.025+growth*.85;
                float a=serial*2.399963+id*1.8;
                float curve=a-2.6*log(max(radius,.15)/start);
                float across=atan(sin(theta-curve),cos(theta-curve))*radius;
                float jitter=.027*sin(along*53.+serial)+.013*sin(along*127.+serial*3.)
                    +.005*sin(along*291.+serial);
                float d=abs(across-jitter);
                float visible=smoothstep(0.,.025,along)*(1.-smoothstep(reach-.02,reach,along));
                // Older sections dim while fresh charges race along the established path.
                float age=max(0.,life-along*.58);
                float pulse=pow(.5+.5*sin(along*24.-life*65.+serial),12.);
                float charge=(.28+.72*exp(-age*2.5)+pulse*(.5+u_impact))*visible;
                float bolt=exp(-pow(d/.0055,2.))*charge;
                float glow=exp(-pow(d/.032,2.))*charge;
                float branches=0.,branchGlow=0.;
                for(int branch=0;branch<4;branch++) {
                    float b=float(branch),rnd=fract(sin(serial*13.+b*73.)*43758.);
                    float root=.08+b*.17+rnd*.07,side=mod(b+id,2.)*2.-1.;
                    float distance=along-root;
                    float forkPath=jitter+side*max(0.,distance)*(.55+rnd*.65)
                        +.012*sin(distance*173.+serial)*smoothstep(0.,.04,distance);
                    float branchReach=min(.16+rnd*.20,max(0.,reach-root)*.72);
                    float fade=exp(-max(0.,life-root*.58)*(.9+rnd*2.));
                    float gate=smoothstep(0.,.018,distance)
                        *(1.-smoothstep(max(.001,branchReach-.025),max(.002,branchReach),distance))*fade;
                    float fd=abs(across-forkPath);
                    branches+=exp(-pow(fd/.0018,2.))*gate;
                    branchGlow+=exp(-pow(fd/.017,2.))*gate;
                }
                // Ridges intermittently hide the channel; reflected light remains local.
                float exposed=mix(.12,1.,smoothstep(.22,.55,rib));
                float wall=smoothstep(.23,.28,radius)*banks;
                vec3 tint=color_tint(air_palette(serial*.19+life*.22+id*.3),u_air_lightning_on,u_air_lightning[0]);
                vec3 hot=mix(tint,vec3(1.,.96,.91),.76);
                sky+=(hot*(bolt+branches*.65)*exposed*1.25
                    +tint*(glow*.28+branchGlow*.12)*(.3+.7*rib))
                    *envelope*(.48+.75*energy)*wall*vortex*effect(536870912);
            }
            // Free lightning starts outside the eye and grows away from it.
            if(vortex>0. && effect(536870912)>0.) {
                float cycle=u_drift_time*.18+.13,life=fract(cycle),serial=floor(cycle);
                float a=serial*2.399963+.8;
                vec2 direction=vec2(cos(a),sin(a));
                vec2 normal=vec2(-direction.y,direction.x);
                vec2 ray=p-eye;
                float along=dot(ray,direction)-.08;
                float reach=.035+.85*smoothstep(.025,.60,life);
                float envelope=smoothstep(.01,.055,life)*(1.-smoothstep(.64,.89,life));
                float jitter=.030*sin(along*41.+serial)+.014*sin(along*103.+serial*3.)
                    +.006*sin(along*267.+serial);
                jitter*=smoothstep(0.,.10,along);
                float across=dot(ray,normal)-jitter;
                float gate=smoothstep(0.,.06,along)*(1.-smoothstep(reach-.025,reach,along));
                float bolt=exp(-pow(across/.0042,2.))*gate;
                float glow=exp(-pow(across/.017,2.))*gate;
                float forks=0.;
                for(int branch=0;branch<4;branch++) {
                    float b=float(branch),root=.16+b*.21+.035*sin(serial+b*7.);
                    float distance=along-root;
                    float forkSide=mod(b+serial,2.)*2.-1.;
                    float path=forkSide*max(0.,distance)*(.5+.17*sin(b+serial))
                        +.009*sin(distance*157.)*smoothstep(0.,.02,distance);
                    float length=min(.28,max(0.,reach-root)*.7);
                    forks+=exp(-pow((across-path)/.0016,2.))*smoothstep(0.,.015,distance)
                        *(1.-smoothstep(max(.001,length-.025),max(.002,length),distance));
                }
                vec3 tint=color_tint(air_palette(serial*.23+life*.28+.12),u_air_lightning_on,u_air_lightning[0]);
                // Also protect the eye from inward forks and their glow.
                float clearance=smoothstep(.08,.14,length(p-eye));
                sky+=(mix(tint,vec3(1.),.22)*bolt+tint*(forks*.75+glow*.17))
                    *envelope*clearance*(.55+.65*energy)*vortex*effect(536870912);
            }
            for(int i=0;i<4;i++) {
                float id=float(i),a=id*1.57+seed*.73;
                vec2 dir=vec2(cos(a),sin(a));
                float along=dot(p-eye,dir),across=dot(p-eye,vec2(-dir.y,dir.x));
                float path=.03*sin(along*41.+seed)+.015*sin(along*103.+seed*3.)+.006*sin(along*267.+seed);
                float bolt=exp(-pow((across-path)/.0045,2.))*smoothstep(.08,.14,along)*(1.-smoothstep(.62,.83,along));
                float coil=exp(-pow((radius-(.25+.045*sin(theta*9.+clock)))/.003,2.));
                float fork=exp(-pow((across-path-abs(along-.27)*.42)/.0014,2.))*smoothstep(.25,.28,along)*(1.-smoothstep(.62,.82,along));
                float split=exp(-pow(abs(across-path+abs(along-.19)*.33)/.0015,2.))
                    *smoothstep(.18,.22,along)*(1.-smoothstep(.68,.91,along));
                sky+=color_tint(vec3(.25,.52,1.)*(bolt+fork*.85+split*.7)+vec3(.18,.08,.35)*coil*.18,u_air_lightning_on,u_air_lightning[0])*flash*vortex;
                // Bolts keep their own paths; a wider residue follows the spiral surface.
                float residue=exp(-abs(sin(theta+log(radius+.03)*2.-a)) * 9.)
                    *banks*(.25+.75*pow(rib,3.));
                sky+=color_tint(air_palette(id*.17+seed*.07),u_air_lightning_on,u_air_lightning[2])*residue*u_air_afterglow*.30*vortex*effect(536870912);
                for(int j=0;j<3;j++) {
                    vec2 trail=u_air_trails[j];
                    float oldAngle=id*1.57+trail.x*.73;
                    float wake=exp(-abs(sin(theta+log(radius+.03)*2.-oldAngle))*7.)
                        *banks*(.25+.75*pow(rib,3.));
                    sky+=color_tint(air_palette(id*.17+trail.x*.07),u_air_lightning_on,u_air_lightning[2])*wake*trail.y*.16*vortex*effect(536870912);
                }
            }
        }
        // Perspective streamers converge at the castle and sweep past our shoulders.
        vec2 ribbonP=p-vec2(0.,.10);
        float rr=length(ribbonP),aa=atan(ribbonP.y,ribbonP.x);
        for(int i=0;i<10;i++) {
            float id=float(i),path=id*.628318+.28*sin(log(rr+.015)*.8-clock*.6+id);
            float separation=abs(sin((aa-path)*.5))*rr;
            float stripe=exp(-pow(separation/(.001+rr*.003),2.))*smoothstep(.025,.10,rr);
            float pulses=.15+.85*pow(.5+.5*sin(log(rr+.015)*9.-clock*9.+id),6.);
            sky+=color_tint(mix(air_palette(id*.09+clock*.02),pigment,.3),u_air_clouds_on,u_air_clouds[1])*stripe*pulses
                *(.12+energy*.45+u_impact*.2)*form.x*effect(134217728);
        }
    }
    // Ordered depth planes: near balloons occlude far ones and grow offscreen.
    if(effect(268435456)>0. && form.x>0.) {
        float travel=clock*1.8;
        for(int i=17;i>=0;i--) {
            float serial=floor(travel)+float(i),z=(float(i)+1.-fract(travel))*2.6+.16;
            float hx=fract(sin(serial*127.1+3.)*43758.5453),hy=fract(sin(serial*311.7+8.)*17341.7);
            // Every third approach uses the near flight lane; others retain broad depth.
            float nearLane=1.-step(.5,mod(serial,3.));
            vec2 world=vec2((hx-.5)*mix(14.,1.7,nearLane),-.58-hy*.45);
            world.y+=(.10+.17*hy)*sin(clock*(1.3+hx*.7)+serial*2.4)*( .25+u_scale*.75)
                +u_impact*(.065+.14*hx)*sin(serial*4.7+clock*.5);
            vec2 center=vec2(0.,.10)+world/z;
            float size=(.43+.10*hy)/z;
            vec2 q=(p-center)/size;
            float r=length(q*vec2(1.+max(0.,-q.y)*.35,.83));
            float shell=1.-smoothstep(.97,1.02,r);
            float spin=clock*(1.15+hx*.85)*(hx>.5 ? 1. : -1.)+serial;
            vec2 textureUV=vec2(atan(q.x,sqrt(max(.015,1.-min(.99,r*r))))*.8,q.y);
            vec2 f=mat2(cos(spin),sin(spin),-sin(spin),cos(spin))*textureUV;
            float inward=log(length(textureUV)+.06)*2.8+clock*1.15;
            f=f*(1.+.30*sin(inward))+.13*vec2(cos(inward),sin(inward));
            float pattern=0.;
            for(int k=0;k<5;k++) {
                f=abs(f)/max(dot(f,f),.24)-vec2(.9+.1*sin(clock*.5),.7);
                pattern+=exp(-length(f)*2.)*.22;
            }
            vec3 fabric=color_tint(air_palette(serial*.13+pattern*.9+clock*.11+.18*sin(inward)),u_air_balloons_on,u_air_balloons[0])*(.22+.78*sqrt(max(0.,1.-r*r)));
            fabric+=color_tint(vec3(.25,.20,.14),u_air_balloons_on,u_air_balloons[1])*pow(max(0.,1.-length(q-vec2(-.28,.30))),12.);
            fabric=mix(fabric,pigment,.16);
            if(shared_spatial())fabric=mix(fabric,material*(.35+.8*sqrt(max(0.,1.-r*r))),.38);
            fabric*=.8+u_impact*.35+.2*cos(atan(textureUV.y,textureUV.x)*7.-spin*2.);
            float fade=smoothstep(.16,.4,z)*(1.-smoothstep(55.,64.,z));
            sky=mix(sky,fabric,shell*fade*form.x);
        }
    }
    sky=air_citadel(p,sky,citadel);
    return max(sky,vec3(0.));
}


// Earth uses the existing source materials and integrated musical travel clock.
vec3 earth_forms() {
    if(u_directed==1)return u_earth_mix;
    if(u_debug_state<26.5) {
        int id=int(u_debug_state+.5)-24;
        return vec3(id==0,id==1,id==2);
    }
    float phase=mod(u_drift_time,108.)/36.;
    int id=int(phase),next=(id+1)%3;
    return mix(vec3(id==0,id==1,id==2),vec3(next==0,next==1,next==2),smoothstep(.65,1.,fract(phase)));
}
// Integrated music time accelerates travel without moving the camera backwards on release.
float earth_travel() { return u_time*3.+u_drift_time*.035; }
float cavern_knot(int index){
    uint n=(uint(index)*19349663u)^(73u*83492791u);
    n^=n>>16;n*=2246822519u;n^=n>>13;
    return (float(n&0xffffffu)/16777216.*2.-1.)*4.6;
}
vec2 cavern_path(float z){
    float span=14.,radius=2.8;int index=int(floor(z/span+.5));float d=z-float(index)*span;
    float x=cavern_knot(index),left=(x-cavern_knot(index-1))/span,right=(cavern_knot(index+1)-x)/span;
    if(d<=-radius)return vec2(x+left*d,left);
    if(d>=radius)return vec2(x+right*d,right);
    float u=(d+radius)/(2.*radius);
    return vec2(x-radius*left+2.*radius*(left*u+(right-left)*(u*u*u-.5*u*u*u*u)),left+(right-left)*(3.*u*u-2.*u*u*u));
}
float cavern_axis(float z){return cavern_path(z).x;}
float earth_channel(float z) { return 1.5*sin(z*.10)+.6*sin(z*.23); }
float earth_dune(vec2 p) {
    float sweep=p.x*.46+p.y*.16+.75*sin(p.y*.13)+.22*sin(p.x*.21-p.y*.31);
    float ridge=.5+.5*sin(sweep);
    return .25+1.7*pow(ridge,2.3)+.42*sin(p.y*.21-p.x*.17)
        +.28*u_scale*sin(p.y*.38+p.x*.2-u_time*.55);
}

// One seeded breach per travel interval, with the whole tail buried before reset.
vec3 earth_worm_point(float u,float serial) {
    float seed=hash(vec2(serial,71.));
    float lane=(hash(vec2(serial,19.))-.5)*11.;
    float z=serial*32.+12.+seed*14.+u*11.;
    float x=lane+(u-.5)*(seed>.5 ? 8. : -8.);
    return vec3(x,earth_dune(vec2(x,z))-1.1+sin(u*3.141593)*3.4,z);
}

vec4 cavern_recipe(vec2 cell,int part) {
    ivec2 relative=ivec2(cell)-u_cavern_origin;
    return texelFetch(u_cavern_cache,ivec2(relative.x*8+part,relative.y),0);
}
float mineral_front(vec3 p) {
    float glow=0.;
    for(int i=0;i<4;i++) {
        vec4 event=u_mineral_fronts[i];float age=u_drift_time-event.x;
        if(age<0. || age>6.)continue;
        float r=length(vec2((p.x-event.w)*.7,p.z-event.y));
        float band=exp(-pow((r-age*12.)/.95,2.));
        float echo=exp(-abs(r-age*12.-2.4)*1.5)*.18;
        glow+=(band+echo)*event.z*exp(-age*.48);
    }
    return min(1.5,glow)*u_mineral_amount;
}
// Selected cluster retains a readable afterglow while the front travels away.
float mineral_anchor(vec3 p) {
    float glow=0.;vec2 center=(floor(p.xz/2.8)+.5)*2.8;
    for(int i=0;i<4;i++) {
        vec4 event=u_mineral_fronts[i];float age=u_drift_time-event.x;
        if(age<0. || age>6.)continue;
        float selected=1.-smoothstep(.1,1.,length(center-vec2(event.w,event.y)));
        glow+=selected*event.z*exp(-age*.72);
    }
    return min(1.2,glow)*u_mineral_amount;
}
// Per-specimen terminations and cleavage; same planes in AO and ray clipping.
vec3 cavern_shape(vec4 crystal,float seed) {
    bool fluorite=seed>.66;
    float cap=fluorite? .10+.18*crystal.z : .32+.42*crystal.z;
    float broken=crystal.z>.62? .12+.24*fract(crystal.z*7.1) : .015;
    return vec3(crystal.x,cap,broken);
}
vec3 mineral_pigment(int role) {
    if(u_mineral_colors_on==1)return u_mineral_colors[role];
    // Original cosine mineral spectrum; slow continuous hue travel through a visit.
    // Explicit source pigments/family holds take precedence without changing history.
    if(role==0)return vec3(.075,.091,.116);
    float phase=u_mineral_motion.y*.55+u_drift_time*.22;
    vec3 hue=.5+.5*cos(vec3(0.,2.1,4.2)+phase+(role==2?2.3:role==3?.8:0.));
    return role==3 ? vec3(.045)+pow(hue,vec3(.85))*.90
         : vec3(.055)+pow(hue,vec3(1.35))*.66;
}
vec2 cavern_formation(vec3 p,vec2 cell,bool includeCrystals) {
    vec2 local=p.xz-(cell+.5)*2.8;
    float axis=cavern_axis((cell.y+.5)*2.8);
    vec2 result=vec2(100.,0.);
    ivec2 relative=ivec2(cell)-u_cavern_origin;
    bool cached=u_cavern_cached==1 && all(greaterThanEqual(relative,ivec2(0))) && all(lessThan(relative,ivec2(8,24)));
    vec4 desc=cached?cavern_recipe(cell,0):vec4(hash(cell+31.),.45+pow(hash(cell+47.),1.4)*2.6,.22+.55*hash(cell+14.),
        .6+sqrt(max(.1,19.36-pow(((cell.x+.5)*2.8-axis)*.80,2.)))+.18);
    float seed=desc.x;
    vec4 foot=cached?cavern_recipe(cell,1):vec4((vec2(hash(cell+2.),hash(cell+9.))-.5)*.65,.12*sin(seed*19.),.10*cos(seed*31.));
    vec2 stal=local-foot.xy;
    float down=desc.w-p.y,hanging=desc.y;
    stal+=foot.zw*down;
    float stalRadius=desc.z*pow(clamp(1.-down/hanging,0.,1.),1.5);
    float stalactite=max(length(stal)-stalRadius,max(-down-2.,down-hanging))*.50;
    if(seed>.16 && stalactite<result.x)result=vec2(stalactite,2.5);
    if(!includeCrystals && seed>=.27)return result;
    if(abs((cell.x+.5)*2.8-axis)>1.1) {
        for(int i=0;i<3;i++) {
            float id=float(i),a=seed*6.283+id*2.1;
            vec4 rotation=cached?cavern_recipe(cell,2+i*2):vec4(cos(a),sin(a),sin(a*3.)*.05,cos(a*2.)*.05);
            float individual=hash(cell+id*17.+63.);
            vec4 crystal=cached?cavern_recipe(cell,3+i*2):vec4(.55+pow(individual,.7)*3.1,.16+.38*hash(cell+id+82.),individual,.17*id);
            individual=crystal.z;
            if(individual<=.18)continue;
            vec2 q=local-rotation.xy*crystal.w-foot.xy;
            q=mat2(rotation.x,rotation.y,-rotation.y,rotation.x)*q;
            float h=crystal.x,y=p.y+2.5;
            vec3 shape=cavern_shape(crystal,seed);h=shape.x;
            q+=rotation.zw*y;
            // Bounded rooted shear: local seeds disagree in direction, topology stays fixed.
            float life=u_mineral_motion.x*.62+sin(u_mineral_motion.y*1.7+seed*9.)*.028*u_mineral_motion.z;
            q+=vec2(rotation.y,-rotation.x)*life*u_mineral_amount*y;
            float cap=shape.y;
            float rad=crystal.y*min(1.,max(0.,(h-y)/cap));
            float hex=max(abs(q.x)*.866025+abs(q.y)*.5,abs(q.y));
            if(seed>.66)hex=max(abs(q.x),abs(q.y));
            if(seed<.27) {
                rad=(.22+.43*individual)*pow(clamp(1.-y/h,0.,1.),1.4);
                hex=length(q)+.012*sin(y*18.+a);
            }
            float fracture=y+q.x*.22+q.y*.13-(h-shape.z);
            float distance=max(max(hex-rad,fracture),max(-y,y-h))*.46;
            if(distance<result.x)result=vec2(distance,seed<.27 ? 2.5 : 1.+seed);
        }
    }
    return result;
}
vec4 cavern_query(vec3 p,bool includeCrystals) {
    float axis=cavern_axis(p.z);
    float shell=(4.4-length(vec2((p.x-axis)*.80,p.y-.6))
        +.18*sin(p.z*.7+p.y*1.6)*sin(p.x*1.7))*.52;
    vec4 result=vec4(min(shell,p.y+2.5),0.,10000.,10000.);
    vec2 cell=floor(p.xz/2.8);
    // Neighboring formations can protrude across a cell edge. Evaluate them
    // consistently for both tracing and normals; otherwise surfaces get sliced.
    vec2 local=p.xz-(cell+.5)*2.8;
    vec2 side=step(vec2(0.),local)*2.-1.;
    // Only four cells can overlap this point. Bound travel toward the omitted
    // cells so the marcher cannot leap over their protruding formations.
    float omittedBound=(2.8+min(abs(local.x),abs(local.y))-2.05)*.35;
    result.x=min(result.x,omittedBound);
    for(int z=0;z<2;z++) for(int x=0;x<2;x++) {
        vec2 neighbor=cell+vec2(x,z)*side;
        vec2 bounds=abs(p.xz-(neighbor+.5)*2.8)-vec2(2.05);
        float lowerBound=max(max(bounds.x,bounds.y),0.)*.35;
        if(lowerBound>result.x)continue;
        vec2 candidate=cavern_formation(p,neighbor,includeCrystals);
        if(candidate.x<result.x) result=vec4(candidate,neighbor);
    }
    return result;
}
float cavern_local_map(vec3 p,vec4 owner) {
    if(owner.y>.5)return cavern_formation(p,owner.zw,true).x;
    float axis=cavern_axis(p.z);
    return min((4.4-length(vec2((p.x-axis)*.80,p.y-.6))+.18*sin(p.z*.7+p.y*1.6)*sin(p.x*1.7))*.52,p.y+2.5);
}
vec2 earth_map(vec3 p,int form) {
    if(form==0) {
        vec2 result=vec2((p.y-earth_dune(p.xz))*.52,0.);
        if(u_earth_details.w>0.) {
            float cycle=earth_travel()/32.,serial=floor(cycle);
            float head=fract(cycle)*2.-.15;
            if(head<0. || head-.46>1.)return result;
            vec3 middle=earth_worm_point(.5,serial);
            float bound=length(max(abs(p-middle)-vec3(6.,5.,8.),0.));
            if(bound>1.)return vec2(min(result.x,bound),0.);
            // The entire body projects onto one straight horizontal segment.
            // Its capsule is a lower distance bound regardless of dune height.
            float seed=hash(vec2(serial,71.));
            float lane=(hash(vec2(serial,19.))-.5)*11.;
            float slope=seed>.5 ? 8. : -8.;
            vec2 start=vec2(lane+(head-.5)*slope,serial*32.+12.+seed*14.+head*11.);
            vec2 end=start-vec2(slope,11.)*.46;
            vec2 projected=end-start;
            float along=clamp(dot(p.xz-start,projected)/dot(projected,projected),0.,1.);
            float lowerBound=(length(p.xz-mix(start,end,along))-.80)*.65;
            if(lowerBound>result.x+.002)return result;
            for(int i=0;i<10;i++) {
                float a=head-float(i)*.046,b=a-.046;
                vec3 pa=earth_worm_point(a,serial),pb=earth_worm_point(b,serial),axis=pb-pa;
                float t=clamp(dot(p-pa,axis)/max(dot(axis,axis),.0001),0.,1.);
                float width=mix(.79,.25,clamp((float(i)+t)/10.,0.,1.));
                float d=length(p-mix(pa,pb,t))-width;
                if(i==0) {
                    vec3 forward=normalize(pa-pb);
                    float mouth=length(p-(pa+forward*.60))-.63;
                    d=max(d,-mouth);
                }
                if(d<result.x)result=vec2(d*.65,3.);
            }
        }
        return result;
    }
    if(form==1) {
        float x=p.x-earth_channel(p.z);
        float bend=.30*sin(p.y*1.3+p.z*.20)+.18*sin(p.z*.65);
        bend+=.18*u_scale*sin(p.z*.4+p.y*.8-u_time*.65);
        float shelves=.12*tanh(sin(p.y*3.1+sin(p.z*.17)) * 5.);
        float width=3.05+.55*sin(p.z*.18)+bend+shelves;
        float top=6.+1.2*sin(p.z*.16)+.5*sin(p.x*.55+p.z*.5);
        float erosion=.055*sin(p.y*8.+p.z*.8)*sin(p.z*2.3)+.045*sin(p.z*4.+p.y*3.);
        float cliff=max(width-abs(x)+erosion,p.y-top)*.43;
        // Natural stone spans join the canyon walls above a clear flight lane.
        float bridgeZ=mod(p.z+16.,32.)-16.;
        float arch=max(abs(bridgeZ)-1.05,abs(p.y-(5.6-.11*x*x))-.65)*.45;
        return vec2(min(min(cliff,arch),(p.y+1.+.13*sin(p.z*.5))*.7),0.);
    }
    return cavern_query(p,true).xy;
}


// Exact interval clipping for the redesigned convex quartz and fluorite bodies.
// Slab rejection precedes descriptor fetches; geology retains conservative tracing.
uniform int u_cavern_cell_count;
bool cavern_clip(vec3 eye,vec3 ray,vec3 plane,float extent,inout float nearT,inout float farT,inout vec3 normal) {
    float denom=dot(plane,ray),numer=extent-dot(plane,eye);
    if(abs(denom)<1e-7)return numer>=0.;
    float crossing=numer/denom;
    if(denom<0.) {if(crossing>nearT){nearT=crossing;normal=plane;}}
    else farT=min(farT,crossing);
    return farT>=max(0.,nearT);
}
vec4 cavern_crystal_ray(vec3 eye,vec3 ray,float limit,out vec3 winningNormal) {
    vec4 result=vec4(limit,0.,0.,0.);winningNormal=vec3(0,1,0);
    if(u_cavern_cached!=1)return result;
    vec3 safeRay=sign(ray+vec3(1e-10))*max(abs(ray),vec3(1e-7));
    // Exact conservative ray-segment bounds: cells outside this rectangle cannot
    // intersect their existing 2.45-unit boxes. Keep row/column order and all shapes.
    vec2 endpoint=eye.xz+ray.xz*limit;
    ivec2 first=ivec2(ceil((min(eye.xz,endpoint)-vec2(2.45))/2.8-.5));
    ivec2 last=ivec2(floor((max(eye.xz,endpoint)+vec2(2.45))/2.8-.5));
    first=max(first,u_cavern_origin);last=min(last,u_cavern_origin+ivec2(7,23));
    for(int z=first.y;z<=last.y;z++) for(int x=first.x;x<=last.x;x++) {
        ivec2 relative=ivec2(x,z)-u_cavern_origin;vec2 cell=vec2(x,z);
        if(relative.y*8+relative.x>=u_cavern_cell_count)continue;
        vec2 center=(cell+.5)*2.8;
        vec3 lower=vec3(center.x-2.45,-2.5,center.y-2.45),upper=vec3(center.x+2.45,1.16,center.y+2.45);
        vec3 entry=(lower-eye)/safeRay,exit=(upper-eye)/safeRay;
        vec3 begin=min(entry,exit),end=max(entry,exit);
        float nearBox=max(begin.x,max(begin.y,begin.z)),farBox=min(end.x,min(end.y,end.z));
        if(farBox<max(.0,nearBox) || nearBox>result.x)continue;
        vec4 desc=cavern_recipe(cell,0);
        if(desc.x<.27 || abs(center.x-cavern_axis(center.y))<=1.1)continue;
        vec4 foot=cavern_recipe(cell,1);
        float seed=desc.x;
        float life=(u_mineral_motion.x*.62+sin(u_mineral_motion.y*1.7+seed*9.)*.028*u_mineral_motion.z)*u_mineral_amount;
        for(int i=0;i<3;i++) {
            vec4 rot=cavern_recipe(cell,2+i*2),crystal=cavern_recipe(cell,3+i*2);
            if(crystal.z<=.18)continue;
            vec2 axisX=vec2(rot.x,-rot.y),axisZ=vec2(rot.y,rot.x);
            vec2 offset=center+rot.xy*crystal.w+foot.xy;
            vec2 lean=rot.zw+vec2(rot.y,-rot.x)*life;
            vec3 localEye=vec3(dot(axisX,eye.xz-offset),eye.y+2.5,dot(axisZ,eye.xz-offset));
            localEye.xz+=lean*localEye.y;
            vec3 localRay=vec3(dot(axisX,ray.xz),ray.y,dot(axisZ,ray.xz));localRay.xz+=lean*ray.y;
            vec3 shape=cavern_shape(crystal,seed);
            float nearT=max(0.,nearBox),farT=min(farBox,result.x),cap=shape.y;
            float height=shape.x;
            vec3 normal=vec3(0,1,0);bool hit=cavern_clip(localEye,localRay,vec3(0,-1,0),0.,nearT,farT,normal);
            hit=hit&&cavern_clip(localEye,localRay,vec3(0,1,0),height,nearT,farT,normal);
            hit=hit&&cavern_clip(localEye,localRay,vec3(.22,1,.13),height-shape.z,nearT,farT,normal);
            for(int face=0;face<6 && hit;face++) {
                if(seed>.66 && face>=4)break;
                vec2 n;
                if(seed>.66)n=face==0?vec2(1,0):face==1?vec2(-1,0):face==2?vec2(0,1):vec2(0,-1);
                else n=face<4?vec2(face%2==0?.866025:-.866025,face<2?.5:-.5):vec2(0,face==4?1.:-1.);
                hit=cavern_clip(localEye,localRay,vec3(n.x,0,n.y),crystal.y,nearT,farT,normal);
                hit=hit&&cavern_clip(localEye,localRay,vec3(n.x,crystal.y/cap,n.y),crystal.y*height/cap,nearT,farT,normal);
            }
            if(hit && nearT<result.x && nearT>0.) {
                result=vec4(nearT,1.+seed,cell);
                vec2 horizontal=axisX*normal.x+axisZ*normal.z;
                winningNormal=normalize(vec3(horizontal.x,normal.y+dot(lean,normal.xz),horizontal.y));
            }
        }
    }
    return result;
}
struct EarthSurface { vec3 point; vec3 normal; float distance; float kind; };
EarthSurface earth_surface(vec2 p,int form) {
    float travel=earth_travel()*(form==2 ? 1.35 : 1.);
    vec3 ro=vec3(0.,1.3,travel),direction=vec3(0.,0.,1.);
    if(form==0) {
        ro.x=1.5*sin(travel*.045);ro.y=3.3+earth_dune(ro.xz);
        direction=normalize(vec3(.10*cos(travel*.045),-.24,1.));
    } else if(form==1) {
        ro.x=earth_channel(travel);
        direction=normalize(vec3(earth_channel(travel+1.)-ro.x,.015,1.));
    } else {
        ro.x=cavern_axis(travel);ro.y=.1;
        direction=normalize(vec3(cavern_path(travel).y,.03,1.));
    }
    vec3 right=normalize(cross(vec3(0,1,0),direction)),up=cross(direction,right);
    float bank=(form==2?.045*cavern_path(travel).y:.06*sin(travel*.075))*(1.+u_flux*1.6);
    p=mat2(cos(bank),sin(bank),-sin(bank),cos(bank))*p;
    vec3 ray=normalize(direction+right*p.x*1.45+up*p.y*1.45);
    // Full-resolution rasterized surface; original per-pixel material remains below.
    vec2 surfaceUV=vec2(p.x*u_resolution.y/u_resolution.x+.5,p.y+.5);
    // p already includes bank here; unbank for the stage's screen-space address.
    if(form==2 && u_cavern_surface_on==1){
        vec2 raw=mat2(cos(bank),-sin(bank),sin(bank),cos(bank))*p;
        surfaceUV=vec2(raw.x*u_resolution.y/u_resolution.x+.5,raw.y+.5);
        if(all(greaterThanEqual(surfaceUV,vec2(0.))) && all(lessThanEqual(surfaceUV,vec2(1.)))){
            vec4 point=texture(u_cavern_surface,surfaceUV),orientation=texture(u_cavern_normal,surfaceUV);
            if(orientation.w>0.)return EarthSurface(ro+point.xyz,orientation.xyz,length(point.xyz),point.w);
            return EarthSurface(ro+ray*55.,vec3(0,1,0),100.,0.);
        }
    }
    float t=.04;vec2 hit=vec2(1.,0.);
    for(int i=0;i<128;i++) {
        hit=form==2?cavern_query(ro+ray*t,false).xy:earth_map(ro+ray*t,form);
        if(hit.x<.003+.0006*t || t>55.)break;
        t+=clamp(hit.x,.003,1.4);
    }
    vec3 pos=ro+ray*t,normal=vec3(0,1,0);
    if(t<=55. && hit.x<.003+.0006*t) {
        float e=.006;
        if(form==2) {
            vec2 k=vec2(1.,-1.);vec4 owner=cavern_query(pos,false);
            normal=normalize(k.xyy*cavern_local_map(pos+k.xyy*e,owner)+k.yyx*cavern_local_map(pos+k.yyx*e,owner)
                +k.yxy*cavern_local_map(pos+k.yxy*e,owner)+k.xxx*cavern_local_map(pos+k.xxx*e,owner));
        } else normal=normalize(vec3(earth_map(pos+vec3(e,0,0),form).x-earth_map(pos-vec3(e,0,0),form).x,
            earth_map(pos+vec3(0,e,0),form).x-earth_map(pos-vec3(0,e,0),form).x,
            earth_map(pos+vec3(0,0,e),form).x-earth_map(pos-vec3(0,0,e),form).x));
    } else t=100.;
    if(form==2 && u_cavern_cached==1) {
        vec3 crystalNormal;vec4 crystal=cavern_crystal_ray(ro,ray,min(t,55.),crystalNormal);
        if(crystal.y>.5) {t=crystal.x;pos=ro+ray*t;normal=crystalNormal;hit.y=crystal.y;}
    }
    return EarthSurface(pos,normal,t,hit.y);
}
vec2 earth_domain(EarthSurface surface,int form) {
    vec3 q=surface.point;
    q.z-=earth_travel()*(form==2 ? 1.35 : 1.);
    if(form==0 && surface.kind>2.)return vec2(q.z*.35,atan(surface.normal.y,surface.normal.x)*.55);
    vec2 domain=form==0 ? q.xz*.19 : vec2(q.z*.15+q.x*.09,q.y*.30);
    return domain/(1.+length(domain)*.06);
}
vec3 earth_territory(vec2 p) {
    float bend=.16*sin(p.x*3.+u_drift_time*.05);
    return vec3(-p.y+bend,.45-abs(p.x)*.8,.45-length(p)*1.1);
}
vec3 earth_scene(vec2 p,EarthSurface surface,vec3 material,int form) {
    float energy=clamp(.60*u_scale+.40*u_flux,0.,1.);
    float clock=u_time*.65+u_drift_time*.025;
    vec3 fog=form==0 ? vec3(.19,.085,.16) : form==1 ? vec3(.07,.085,.17) : vec3(.008,.024,.040);
    vec3 sky=color_tint(mix(fog,vec3(.018,.028,.085),smoothstep(-.1,.5,p.y)),u_earth_sky_on,u_earth_sky[0]);
    if(form==0) {
        float sunset=exp(-length((p-vec2(-.48,.22))*vec2(1.,1.2))*6.);
        sky+=color_tint(vec3(.65,.20,.075),u_earth_sky_on,u_earth_sky[2])*sunset;
        sky=mix(fog,sky,smoothstep(.05,.24,p.y));
    }
    if(form<2 && surface.distance>=90.) {
        // Distant weather lives behind terrain, never across the opaque foreground.
        vec2 dome=vec2(p.x,p.y+.10*p.x*p.x);
        vec2 cloudSpace=dome*vec2(2.3,6.)+vec2(u_drift_time*.009,u_time*.006);
        float clouds=.5+.23*sin(cloudSpace.y+sin(cloudSpace.x*1.7))
            +.15*sin(cloudSpace.y*2.3-cloudSpace.x*.8)
            +.08*sin(cloudSpace.x*3.1+cloudSpace.y*4.);
        float wisps=smoothstep(.42,.72,clouds)*smoothstep(-.05,.20,dome.y);
        vec3 cloudColor=form==0 ? vec3(.35,.12,.18) : vec3(.07,.12,.22);
        sky=mix(sky,color_tint(cloudColor,u_earth_sky_on,u_earth_sky[1]),wisps*.65);
        vec2 starGrid=dome*vec2(180.,120.)+vec2(u_star_time*.12,u_star_time*.035);
        vec2 starCell=floor(starGrid),starLocal=fract(starGrid)-.5;
        float starSeed=fract(sin(dot(starCell,vec2(12.9898,78.233)))*43758.5453);
        float star=exp(-dot(starLocal,starLocal)*100.)*step(.974,starSeed);
        sky+=(u_sky_stars_on==1 ? mix(vec3(.42,.62,.90)*(u_sky_stars[0]/vec3(.55,.72,1.)),
            vec3(.90,.66,.40)*(u_sky_stars[1]/vec3(1.,.83,.62)),starSeed)
            : mix(vec3(.42,.62,.90),vec3(.90,.66,.40),starSeed))*star
            *(.45+.35*sin(u_star_time*.8+starSeed*23.))
            *effect(512)*smoothstep(.04,.25,dome.y)*(1.-wisps);
        if(form==0) {
            vec2 sun=dome-vec2(-.48,.22);
            float disk=1.-smoothstep(.040,.044,length(sun));
            sky+=vec3(.72,.32,.12)*disk*(1.-wisps*.8);
            sky+=vec3(.16,.055,.085)*exp(-abs(dome.y-.12)*16.)*(1.-wisps);
        } else {
            vec2 veil=dome;
            veil.x+=.025*u_flux*sin(dome.y*7.+u_time*.12);
            float curtain=veil.y-.30-.055*sin(veil.x*5.+u_time*.10)
                -.025*sin(veil.x*13.-u_time*.16);
            float ribbon=exp(-abs(curtain)*24.)*(.35+.65*pow(.5+.5*sin(veil.x*32.+u_time*.4),2.));
            vec3 aurora=mix(vec3(.08,.42,.32),vec3(.27,.12,.48),.5+.5*sin(veil.x*4.+u_drift_time*.025));
            sky+=color_tint(aurora,u_strata_land_on,u_strata_land[1])*ribbon*(.30+.65*energy+.40*u_impact)*(1.-wisps*.5);
        }
    }
    if(surface.distance<90.) {
        vec3 q=surface.point,n=surface.normal;
        vec2 uv=form==0 ? q.xz*.3 : vec2(q.z*.25+q.x*.18,q.y*.7);
        vec2 detail=shared_spatial() ? mix(uv,spatial_carrier(uv*.35)/.35,.30) : uv;
        float warp=sin(detail.x*.8+sin(detail.y*.4))*1.1;
        float sediment=.5+.5*sin(detail.y*8.+warp+u_scale*.18*sin(q.z*.3));
        float ripples=.5+.5*sin(detail.x*32.+sin(detail.y*2.)*3.-clock*.65);
        float vein=pow(.5+.5*sin(detail.y*5.+warp*2.4+sin(detail.x*2.)),24.);
        float grain=noise(q.xz*24.+q.y*7.);
        float bedding=.5+.5*sin(q.y*42.+sin(q.z*2.)*.8);
        float light=max(0.,dot(n,normalize(vec3(-.65,.85,-.35))));
        vec3 stone;
        if(form==0) {
            stone=color_tint(mix(vec3(.20,.055,.09),vec3(.88,.42,.13),.3+.7*light),u_dunes_land_on,u_dunes_land[0]);
            stone*=1.-u_earth_details.x*.19*(1.-ripples)*smoothstep(.12,.65,n.y);
        } else if(form==1) {
            stone=color_tint(mix(vec3(.17,.055,.11),vec3(.58,.27,.13),sediment*u_earth_details.x),u_strata_land_on,u_strata_land[0]);
            stone=mix(stone,vec3(.07,.25,.31),pow(1.-sediment,5.)*.55*u_earth_details.x);
        } else {
            vec3 matrix=mineral_pigment(0);
            stone=color_tint(mix(matrix*1.5,matrix*3.2,sediment*.5*u_earth_details.x),u_cavern_land_on,u_cavern_land[0]);
            if(surface.kind>.5 && surface.kind<2.) {
                float cluster=fract(surface.kind*31.);
                vec3 ore=mix(mineral_pigment(1),mineral_pigment(2),smoothstep(.35,.65,cluster));
                float inclusions=noise(q.xz*2.8+q.y*1.3);
                stone=color_tint(ore*(.45+.45*inclusions),u_cavern_land_on,u_cavern_land[1]);
            } else if(surface.kind>2.) {
                stone=mix(vec3(.085,.076,.067),vec3(.24,.21,.18),.30+.12*noise(q.xz*2.+q.y*.8));
            }
        }
        if(form==0 && surface.kind>2.) {
            float armor=pow(.5+.5*cos(q.z*14.+q.x*3.),5.);
            stone=color_tint(mix(vec3(.12,.22,.29),vec3(.32,.52,.59),armor*.3+.4),u_dunes_land_on,u_dunes_land[1]);
        }
        // Pigment is lit with the solid surface; only narrow mineral seams emit.
        float pigment=form==0 ? .16 : form==1 ? .20 : .22;
        stone=mix(stone,stone*(.75+clamp(material,0.,1.)*.5),pigment*vein);
        if(shared_spatial())stone*=.82+clamp(material,0.,1.)*.48;
        if(form==0 && surface.kind>2.)stone=color_tint(vec3(.10,.17,.23)+material*1.5,u_dunes_land_on,u_dunes_land[1]);
        stone*=.88+.16*grain;
        if(form==1)stone*=1.-.13*(1.-bedding)*u_earth_details.x;
        float occlusion=0.;
        for(int i=1;i<=3;i++) {
            float reach=float(i)*.18;
            occlusion+=max(0.,reach-earth_map(q+n*reach,form).x*1.9)/float(i);
        }
        float contact=clamp(1.-occlusion*1.5,.30,1.);
        if(form==2) {
            float travel=earth_travel()*1.35;
            vec3 eye=vec3(cavern_axis(travel),.1,travel);
            light=max(light,.75*max(0.,dot(n,normalize(eye-q))));
            stone*=.78+.32*noise(q.xz*2.7+q.y*1.9);
        }
        vec3 color=stone*(.38+.85*light)*contact;
        color*=1.+.30*energy*light;
        if(form==0 && surface.kind>2.) {
            float plate=pow(.5+.5*cos(q.z*14.+q.x*3.),9.);
            color+=vec3(.12,.28,.34)*plate*.22;
        }
        float traveling=pow(.5+.5*sin(q.z*.95-q.y*2.-clock*3.5),8.);
        vec3 mineral=.5+.5*cos(vec3(.1,2.2,4.1)+q.y*.3+clock*.10);
        color+=color_tint(form==2 ? mineral_pigment(1) : mix(mineral,clamp(material,0.,1.),.4),u_earth_minerals_on,u_earth_minerals[0])*vein*u_earth_details.y*(.04+.32*energy+1.05*u_impact)*(.3+.7*traveling)*contact*(form==2?.16:1.);
        if(form==2) {
            float front=mineral_front(q),anchor=mineral_anchor(q);
            float facing=max(0.,dot(n,normalize(vec3(-.3,.35,-.9))));
            float wet=pow(max(0.,dot(reflect(normalize(vec3(.3,-.8,.5)),n),normalize(vec3(0.,.1,-1.)))),32.);
            color+=mineral_pigment(1)*wet*.17;
            if(surface.kind>.5 && surface.kind<2.) {
                bool fluorite=surface.kind>1.66;
                float specimen=fract(surface.kind*31.);
                float cloud=noise(q.xz*2.9+q.y*.65+specimen*13.);
                float fracture=pow(1.-abs(sin(q.x*7.3+q.y*2.1+q.z*4.6+cloud*3.)),18.);
                // Matte etching describes the face; internal light describes depth.
                float etch=pow(.5+.5*sin(q.y*13.+q.x*7.+cloud*5.),14.)
                    *smoothstep(.48,.70,noise(q.xz*4.+q.y));
                float viewFace=max(0.,dot(n,normalize(vec3(cavern_axis(earth_travel()*1.35)-q.x,.1-q.y,earth_travel()*1.35-q.z))));
                float rim=pow(1.-viewFace,3.);
                if(fluorite) {
                    float core=pow(cloud,3.)*(.12+.48*u_mineral_motion.z+front*.48+anchor*.62);
                    float cleavage=pow(1.-abs(sin(q.x*3.1+q.z*2.7+q.y*.45)),26.);
                    color*=.78+.22*cloud;
                    color+=mix(stone*1.9,mineral_pigment(3),.20)*core*u_earth_details.y;
                    color+=mineral_pigment(3)*cleavage*(.014+front*.09)*u_earth_details.y;
                    color+=stone*rim*(.12+anchor*.40);
                    color+=mineral_pigment(3)*pow(viewFace,28.)*(.045+u_sparkle*.24);
                } else {
                    color*=1.-etch*.22*u_earth_details.x;
                    float inclusion=pow(cloud,5.);
                    color+=mix(stone*1.4,mineral_pigment(3),.4)*inclusion
                        *(.16+.45*u_mineral_motion.z+front*.72+anchor*.52)*u_earth_details.y;
                    color+=mineral_pigment(3)*fracture*(.018+front*.18+anchor*.11)*u_earth_details.y;
                    color+=color_tint(mineral_pigment(3),u_cavern_land_on,u_cavern_land[2])
                        *(pow(viewFace,18.)*(.05+u_sparkle*.3)+rim*.075)*u_earth_details.y;
                }
                color+=stone*anchor*.55;
            } else {
                float crack=pow(.5+.5*sin(q.x*3.2+q.z*1.9+noise(q.xz*2.1)*4.),30.);
                color+=mineral_pigment(3)*crack*(.035+front*.38)*u_earth_details.y;
            }
            // Material light spills only on nearby solid floor, preserving occlusion.
            if(q.y<-2.42) {
                float lane=exp(-pow(abs(q.x-cavern_axis(q.z))/1.9,4.));
                float pools=pow(.5+.5*sin(q.z*.72+q.x*.5-u_mineral_motion.y),6.);
                color+=mix(mineral_pigment(1),mineral_pigment(2),.5+.5*sin(q.z*.18))
                    *lane*(.055+.18*pools*u_mineral_motion.z+front*.22)*u_earth_details.y;
            }
        } else if(u_mineral_amount>0. && (u_debug_state==24. || u_debug_state==25.)) color+=mineral_pigment(3)*vein*mineral_front(q)*.35*u_earth_details.y;
        // Tiny mineral glints use world coordinates, never a screen overlay.
        vec3 glitter=q*18.;
        vec3 cell=floor(glitter),local=fract(glitter)-.5;
        float fleck=pow(max(0.,1.-min(min(length(local.xy),length(local.yz)),length(local.xz))*3.),3.);
        // Bound the hash input so long travel does not lose fractional precision.
        float seed=hash(mod(cell.xy+cell.z*19.,127.));
        float twinkle=pow(.5+.5*sin(clock*2.+seed*71.),8.);
        color+=color_tint(vec3(.22,.39,.48),u_earth_minerals_on,u_earth_minerals[1])*fleck*step(.96,seed)*(.12+twinkle*(.3+u_sparkle*1.5))*u_earth_details.z;
        float mist=1.-exp(-surface.distance*(form==2 ? .025 : .030));
        sky=mix(color,fog,mist);
    }
    return max(vec3(0.),sky);
}

// Fog/Gas uses bounded front-to-back volume integration, separate from solid depth.
vec3 fog_forms() {
    if(u_directed==1)return u_fog_mix;
    if(u_debug_state<30.5) {
        int id=int(u_debug_state+.5)-28;
        return vec3(id==0,id==1,id==2);
    }
    float phase=mod(u_drift_time,114.)/38.;
    int id=int(phase),next=(id+1)%3;
    return mix(vec3(id==0,id==1,id==2),vec3(next==0,next==1,next==2),smoothstep(.70,1.,fract(phase)));
}
float fog_seed(vec2 p) {
    p=mod(p,127.);
    return fract(sin(dot(p,vec2(27.13,91.71)))*4375.83);
}
float fog_billows(vec3 p) {
    p+=.55*sin(p.yzx*1.31+vec3(1.,3.,5.));
    return .5+.22*sin(p.x+sin(p.z))+.16*sin(p.y*1.7-p.z*.6)
        +.10*sin(p.z*2.5+p.x*1.2)*sin(p.y*2.1);
}
vec2 fog_pressure_path(float z) {
    float section=z/18.,cell=floor(section),f=fract(section);
    f=f*f*f*(f*(f*6.-15.)+10.);
    float a=floor(fog_seed(vec2(cell,17.))*12.)*.52359878;
    float b=floor(fog_seed(vec2(cell+1.,17.))*12.)*.52359878;
    return mix(vec2(cos(a),sin(a)),vec2(cos(b),sin(b)),f)*4.5;
}
float fog_density(vec3 p,int form) {
    if(form==2)p.xy-=fog_pressure_path(p.z);
    float t=u_time*.34;
    vec3 flow=p+vec3(.5*sin(p.z*.18-t),t*.12,-t*.7);
    float billow=fog_billows(flow*.72);
    if(form==0) {
        vec2 channel=vec2(1.4*sin(p.z*.15),.7*sin(p.z*.11));
        float opening=2.0+.60*u_scale+.35*sin(p.z*.31-t*.4);
        float bank=smoothstep(opening-.6,opening+1.4,length(p.xy-channel));
        return (.09+bank*.8)*smoothstep(.25,.72,billow)*1.9;
    }
    if(form==1) {
        float height=exp(-max(0.,p.y+.9)*.65);
        return height*(.055+.60*smoothstep(.40,.75,billow))*(.65+.25*u_scale);
    }
    float angle=p.z*.22-t*.8;
    vec2 crossSection=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*p.xy;
    float cavity=length(crossSection*vec2(1.,.8))-(1.5+.4*u_scale);
    float shell=smoothstep(-.55,.6,cavity);
    float front=pow(.5+.5*sin(p.z*.9-t*4.+length(p.xy)*1.5),5.);
    float gyroid=dot(sin(flow*.85),cos(flow.yzx*.85));
    return (.03+shell*.85)*smoothstep(.35,1.25,abs(gyroid))
        +front*.45*u_impact*u_fog_details.z;
}
vec3 marsh_pigment(int role){return u_marsh_palette_on==1?u_marsh_palette[role]:u_marsh_authored[role];}
int marsh_index(float cell,float side){return int(cell-u_marsh_origin)*2+(side>0.?1:0);}
vec4 marsh_meta(float cell,float side){int index=marsh_index(cell,side);return u_marsh_cached==1 && index>=0 && index<14?u_marsh_meta[index]:vec4(0.);}
vec3 marsh_lamp_color(float side,bool reflection){vec3 pigment=marsh_pigment(side<0.?4:5);return color_tint(pigment,u_marsh_ghostlights_on,u_marsh_ghostlights[reflection?1:0]);}
float marsh_ground_trail(vec2 p,vec2 a,vec2 b){vec2 d=b-a;float f=clamp(dot(p-a,d)/max(dot(d,d),1e-5),0.,1.);return exp(-pow(length(p-a-f*d)/.085,2.))*(1.-f*.35);}
vec3 fog_lamp(float cell,float side) {
    int index=marsh_index(cell,side);if(u_marsh_cached==1 && index>=0 && index<14)return u_marsh_lamps[index].xyz;
    float seed=fog_seed(vec2(cell,side));
    float phase=u_time*(.95+seed*.3)+seed*19.;
    // Forward half of the orbit briefly matches our travel, then darts away.
    // Keep the entire flight lane clear of the solid roadside silhouettes.
    float dart=pow(.5+.5*sin(phase*.71+2.),6.);
    return vec3(side*(1.05+.32*sin(phase*.8)+.12*dart*sin(phase*5.)),
        -.65+.7*(.5+.5*sin(phase*.63))+.45*dart,
        cell*8.+4.+2.7*sin(phase));
}
float fog_lamp_light(float cell,float side) {
    int index=marsh_index(cell,side);if(u_marsh_cached==1 && index>=0 && index<14)return u_marsh_lamps[index].w;
    float seed=fog_seed(vec2(cell,side));
    float pulse=.5+.5*sin(u_time*(.7+seed*.4)+seed*23.);
    return (.08+.92*pulse*pulse)*(.22+.85*u_scale+.6*u_sparkle+1.1*u_impact);
}
vec2 fog_terrain(vec3 p) {
    vec2 result=vec2(p.y+1.4,0.);
    float cell=floor(p.z/8.);
    for(int i=0;i<2;i++) {
        float side=i==0 ? -1. : 1.,seed=fog_seed(vec2(cell,side+4.));
        vec3 center=vec3(side*(2.6+seed*2.),0.,cell*8.+4.);
        vec3 q=p-center;
        float height=.85+seed*1.65;
        float angle=(seed-.5)*.65;
        q.xz=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*q.xz;
        float width=.30+seed*.34+.035*fog_seed(vec2(cell,side+19.));
        // Every marker has an arched crown and a thin headstone profile.
        float cap=length(vec2(q.x,max(0.,p.y+1.4-height+width)))-width;
        float rock=max(max(cap,abs(q.z)-(.14+seed*.18)),-p.y-1.5);
        if(rock<result.x)result=vec2(rock*.75,1.);
    }
    return result;
}
vec3 fog_stone(vec3 p,float light) {
    float cell=floor(p.z/8.),side=p.x<0. ? -1. : 1.;
    float seed=fog_seed(vec2(cell,side+4.));
    vec3 q=p-vec3(side*(2.6+seed*2.),-1.4,cell*8.+4.);
    float angle=(seed-.5)*.65;
    q.xz=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*q.xz;
    float grain=fog_billows(q*5.+seed*13.);
    float vein=pow(.5+.5*sin(q.x*13.+q.y*4.+grain*8.),8.);
    vec3 stone=mix(marsh_pigment(2)*.88,marsh_pigment(2)*vec3(1.12,.83,1.08),seed);
    stone*=.75+.35*grain;
    stone=mix(stone,vec3(.08,.14,.17),vein*.7);
    // Fixed vein/crack coordinates; only their weathering coverage grows.
    float age=1.-exp(-max(0.,u_drift_time)*.012-seed*.4);
    float moss=smoothstep(.43,.68,grain)*
        (1.-smoothstep(.20+age*.85,.75+age*1.1,q.y));
    stone=mix(stone,color_tint(marsh_pigment(3)*(.7+grain*.6),u_marsh_solids_on,u_marsh_solids[2]),moss*.85);
    float stem=abs(q.x+.13*sin(q.y*8.+seed*9.)+.12*sin(q.y*3.));
    float branch=abs(q.x-.43*(q.y-.7)+.08*sin(q.y*14.+seed*5.));
    float cracks=1.-smoothstep(.008,.022,min(stem,branch));
    cracks*=1.-smoothstep(age*2.8,age*2.8+.18,q.y);
    stone*=1.-cracks*.8*smoothstep(.12,.45,age);
    return color_tint(stone,u_marsh_solids_on,u_marsh_solids[1])*light*(.8+.30*u_marsh_motion.x);
}
vec2 fog_solid(vec3 p) {
    vec2 result=fog_terrain(p);
    if(u_fog_details.y>0.) {
        float cell=floor(p.z/8.);
        for(int j=-1;j<=1;j++)for(int i=0;i<2;i++) {
            float orb=length(p-fog_lamp(cell+float(j),i==0 ? -1. : 1.))-.075;
            if(orb<result.x)result=vec2(orb,2.);
        }
    }
    return result;
}
vec3 fog_palette(float phase,int form) {
    if(form==0)return mix(vec3(.055,.26,.42),vec3(.64,.24,.35),.5+.5*sin(phase*.7));
    if(form==1)return mix(vec3(.035,.12,.16),vec3(.20,.32,.13),.5+.5*sin(phase));
    return mix(vec3(.65,.12,.035),vec3(.10,.32,.48),.5+.5*sin(phase));
}
vec3 fog_scene(vec2 screen,vec3 material,int form) {
    float energy=clamp(.5*u_scale+.5*u_flux,0.,1.);
    float travel=u_time*3.2+u_drift_time*.04;
    vec3 ro=vec3(1.1*sin(travel*.075),form==1 ? .7 : .3,travel);
    vec3 forward=normalize(vec3(.0825*cos(travel*.075),form==1 ? -.10 : .03,1.));
    if(form==2) {
        ro.xy=fog_pressure_path(travel);
        forward=normalize(vec3(fog_pressure_path(travel+3.)-ro.xy,3.));
    }
    vec3 right=normalize(cross(vec3(0,1,0),forward)),up=cross(forward,right);
    float roll=.06*sin(travel*.10)*(1.+energy*1.8);
    vec2 p=mat2(cos(roll),sin(roll),-sin(roll),cos(roll))*screen;
    vec3 ray=normalize(forward+right*p.x*1.5+up*p.y*1.5);
    float stop=23.;
    vec3 background=form==1 ? marsh_pigment(0)*.13 : vec3(.006,.010,.025);
    if(form==1) {
        // Solid intersections terminate the volume: nothing behind a rock can leak through.
        float floorDepth=ray.y<-.0001 ? min(23.,(-1.4-ro.y)/ray.y) : 23.;
        float t=.04;vec2 hit=vec2(1,0);
        for(int i=0;i<56;i++) {
            hit=fog_solid(ro+ray*t);
            if(hit.x<.004+.0005*t || t>=23.)break;
            t+=clamp(hit.x,.004,1.2);
        }
        if(!(t<23. && hit.x<.004+.0005*t) && floorDepth<23.) {
            t=floorDepth;hit=vec2(0.,0.);
        }
        if(t<23. && hit.x<.004+.0005*t) {
            stop=t;vec3 q=ro+ray*t;float e=.015;
            vec3 n=normalize(vec3(fog_solid(q+vec3(e,0,0)).x-fog_solid(q-vec3(e,0,0)).x,
                fog_solid(q+vec3(0,e,0)).x-fog_solid(q-vec3(0,e,0)).x,
                fog_solid(q+vec3(0,0,e)).x-fog_solid(q-vec3(0,0,e)).x));
            float light=.25+.65*max(0.,dot(n,normalize(vec3(-.3,.8,-.6))));
            background=color_tint(marsh_pigment(1),u_marsh_solids_on,u_marsh_solids[0])*light*(.8+.30*u_marsh_motion.x);
            if(hit.y<.5) {
                float pathCenter=.45*sin(q.z*.13);
                float path=exp(-pow(abs(q.x-pathCenter)/1.65,3.));
                float grain=fog_billows(q*vec3(9.,1.,5.));
                float ripples=.5+.5*sin(q.z*8.+sin(q.x*5.)-u_time*.9);
                background*=mix(.10,1.5,path)*(.62+.28*grain+.10*ripples);
                float cell=floor(q.z/8.);
                for(int j=-1;j<=1;j++)for(int i=0;i<2;i++) {
                    float id=cell+float(j),side=i==0 ? -1. : 1.;
                    vec3 lamp=fog_lamp(id,side);
                    vec2 delta=q.xz-lamp.xz;
                    float height=lamp.y+1.4,extent=.22+height*.60;
                    // A longer lower stem and raised crossbar, projected onto the ground.
                    float stem=exp(-pow(abs(delta.x)/.055,2.)-pow(abs(delta.y)/extent,6.));
                    float bar=exp(-pow(abs(delta.x)/(extent*.48),6.)-pow(abs(delta.y-extent*.32)/.055,2.));
                    float reflection=max(stem,bar)+.12*exp(-dot(delta,delta)*3.);
                    int index=marsh_index(id,side);vec4 meta=marsh_meta(id,side);
                    float trail=index>=0 && index<14 && u_marsh_cached==1?marsh_ground_trail(q.xz,u_marsh_wakes[index].xz,lamp.xz):0.;
                    float ring=meta.x>.00001?exp(-pow((length(delta)-meta.y)/.13,2.))*meta.x:0.;
                    background+=marsh_lamp_color(side,true)*(reflection+trail*(.045+.12*u_marsh_motion.x))*fog_lamp_light(id,side)*u_fog_details.y;
                    background+=color_tint(marsh_pigment(6),u_marsh_ghostlights_on,u_marsh_ghostlights[1])*ring*.15*u_fog_details.y;
                }
            } else if(hit.y>1.5) {
                float cell=floor(q.z/8.),side=q.x<0. ? -1. : 1.;
                float core=pow(clamp(dot(n,-ray),0.,1.),2.);float heat=marsh_meta(cell,side).x;
                background=marsh_lamp_color(side,false)*(.10+fog_lamp_light(cell,side)*1.7*(.34+.66*core))
                    +color_tint(marsh_pigment(6),u_marsh_ghostlights_on,u_marsh_ghostlights[0])*(.025*pow(core,4.)+heat*(.16+.34*core));
            }
            else background=fog_stone(q,light);
        }
    }
    vec3 accumulated=vec3(0.);float transmittance=1.;
    const float stepSize=.48;
    for(int i=0;i<48;i++) {
        float start=float(i)*stepSize;
        if(start>=stop || transmittance<.018)break;
        float stepLength=min(stepSize,stop-start);
        vec3 q=ro+ray*(start+stepLength*.5);
        float density=fog_density(q,form)*u_fog_details.x;
        float through=exp(-density*stepLength);
        float towardLight=fog_density(q+vec3(-.4,.65,-.25),form);
        float rim=clamp((density-towardLight)*2.,-.20,.65);
        float phase=q.z*.16+q.y*.55+u_time*.08;
        vec3 pigment=form==1?marsh_pigment(0)*(.75+.45*(.5+.5*sin(phase))):fog_palette(phase,form);
        if(u_fog_vapor_on==1) pigment*=u_fog_vapor[form];
        // Material colors enter the scattering volume, not an extra transparent layer.
        pigment=mix(pigment,pigment*(.70+clamp(material,0.,1.)*.8),.18);
        float forwardLight=pow(max(0.,dot(ray,normalize(vec3(-.3,.3,1.)))),6.);
        vec3 lighting=pigment*(.22+rim+forwardLight*.45);
        float thread=pow(.5+.5*sin(fog_billows(q*1.8)*11.+phase-u_time),8.);
        lighting+=pigment*thread*(form==1 ? .08+.30*u_marsh_motion.y : .08+.30*u_sparkle+.60*u_impact)*u_fog_details.z;
        if(u_fog_internal_on==1)
            lighting+=pigment*(u_fog_internal[0]-vec3(1.))*thread*(form==1 ? .08+.30*u_marsh_motion.y : .08+.30*u_sparkle+.60*u_impact)*u_fog_details.z;
        if(form==1) {
            float cell=floor(q.z/8.);
            for(int j=-1;j<=1;j++)for(int k=0;k<2;k++) {
                float id=cell+float(j),side=k==0 ? -1. : 1.;
                vec3 lamp=fog_lamp(id,side);float d=length(q-lamp);vec4 meta=marsh_meta(id,side);
                float radius=length(q.xz-lamp.xz);
                float breath=meta.x>.00001?exp(-pow((radius-meta.y)/.19,2.))*meta.x*exp(-abs(q.y+1.)*2.):0.;
                lighting+=marsh_lamp_color(side,false)*exp(-d*.95)*fog_lamp_light(id,side)*2.2*u_fog_details.y;
                if(meta.x>.00001) {
                    lighting+=color_tint(marsh_pigment(6),u_marsh_ghostlights_on,u_marsh_ghostlights[0])*(breath*.75+meta.x*exp(-d*2.)*.35)*u_fog_details.y;
                    density*=1.+.035*breath*u_fog_details.z;
                }
            }
        } else {
            float pulse=pow(.5+.5*sin(q.z*.65-u_time*2.+q.y),5.);
            lighting+=pigment*pulse*(.14+.65*energy+1.3*u_impact)*u_fog_details.y;
            if(u_fog_internal_on==1)
                lighting+=pigment*(u_fog_internal[1]-vec3(1.))*pulse*(.14+.65*energy+1.3*u_impact)*u_fog_details.y;
        }
        if(form==1)through=exp(-density*stepLength);
        accumulated+=transmittance*(1.-through)*max(lighting,vec3(0.));
        transmittance*=through;
    }
    return accumulated+background*transmittance;
}

// Plasma keeps opaque charged bodies separate from emitted filament light.
vec3 plasma_forms() {
    if(u_directed==1)return u_plasma_mix;
    if(u_debug_state<34.5) {
        int id=int(u_debug_state+.5)-32;return vec3(id==0,id==1,id==2);
    }
    float phase=mod(u_drift_time,108.)/36.;int id=int(phase),next=(id+1)%3;
    return mix(vec3(id==0,id==1,id==2),vec3(next==0,next==1,next==2),smoothstep(.68,1.,fract(phase)));
}
float plasma_seed(vec2 p) {
    return fract(sin(dot(mod(p,127.),vec2(41.73,17.91)))*4738.13);
}
vec3 plasma_tint(float phase) {
    return .52+.46*cos(phase+vec3(.2,2.3,4.4));
}
vec3 plasma_view(vec3 p) {
    float yaw=u_time*.085,tilt=.35+.16*sin(u_time*.10);
    p.xz=mat2(cos(yaw),sin(yaw),-sin(yaw),cos(yaw))*p.xz;
    p.xy=mat2(cos(tilt),sin(tilt),-sin(tilt),cos(tilt))*p.xy;
    p.z+=4.1;return p;
}
float plasma_sphere(vec3 ray,vec3 center,float radius) {
    float b=dot(ray,center),h=b*b-dot(center,center)+radius*radius;
    return h>0. ? b-sqrt(h) : 100.;
}
vec2 plasma_segment(vec2 p,vec3 a,vec3 b) {
    vec2 start=a.xy/a.z*1.35,end=b.xy/b.z*1.35;
    vec2 delta=end-start;
    float f=clamp(dot(p-start,delta)/max(dot(delta,delta),1e-8),0.,1.);
    // Perspective-correct depth at the projected nearest point.
    return vec2(length(p-start-f*delta),1./mix(1./a.z,1./b.z,f));
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
vec3 plasma_node(float id) {
    float phase=id*.897598+u_time*(.07+.012*sin(id));
    return vec3(cos(phase)*(1.65+.22*u_scale),sin(phase*1.37+id)*.95,
        sin(phase)*1.25);
}
// Renderer-cached field paths: one projected descriptor per vertex, bounded groups.
vec3 magnetic_pigment(int role) {
    if(u_magnetic_bloom_on==1)return u_magnetic_bloom[role];
    vec3 a[6]=vec3[6](vec3(.016,.031,.051),vec3(.125,.184,.216),vec3(.816,.471,.231),vec3(.263,.710,.671),vec3(1.,.910,.639),vec3(.608,.663,.608));
    vec3 b[6]=vec3[6](vec3(.031,.020,.059),vec3(.161,.141,.196),vec3(.659,.400,.855),vec3(.349,.604,.851),vec3(1.,.898,.827),vec3(.647,.569,.773));
    vec3 c[6]=vec3[6](vec3(.047,.075,.094),vec3(.529,.612,.612),vec3(.875,.525,.388),vec3(.239,.514,.624),vec3(1.,1.,.827),vec3(.835,.859,.761));
    float phase=u_magnetic_motion.z*.013+max(0.,u_magnetic_visit-1.)*.36;
    int family=int(floor(phase))%3;float blend=smoothstep(.65,1.,fract(phase));
    return mix(family==0?a[role]:family==1?b[role]:c[role],family==0?b[role]:family==1?c[role]:a[role],blend);
}
vec3 magnetic_cached_field(vec2 p,vec3 material) {
    vec3 ray=normalize(vec3(p,1.35));float energy=u_magnetic_motion.x,high=u_magnetic_motion.y,phase=u_magnetic_motion.z;
    vec3 color=color_tint(magnetic_pigment(0),u_plasma_sky_on,u_plasma_sky[0])*.28+plasma_stars(p,0)*u_plasma_details.z*.60;
    vec3 center=vec3(0,0,4.1),coreNormal=vec3(0,0,-1);float solidDepth=100.;
    // Two original convex pole pieces, asymmetric side radii and broken cap planes.
    // Analytic plane clipping; no new ray marcher or repeated field construction.
    if(abs(p.x)<.30 && abs(p.y)<.31)for(int piece=0;piece<2;piece++) {
        float signPiece=piece==0?1.:-1.;
        vec3 origin=transpose(u_magnetic_axes)*(-center)-vec3(0,signPiece*(.31+.025+.03*energy),0);
        vec3 direction=transpose(u_magnetic_axes)*ray;float near=0.,far=100.;vec3 face=vec3(0,0,-1);
        for(int j=0;j<10;j++) {
            float az=float(j)*.785398;
            vec3 plane=vec3(cos(az),signPiece*.18,sin(az));float extent=.30+.018*sin(float(j)*2.3+piece*1.7);
            if(j==8){plane=vec3(.18,1.,-.08);extent=.27;}
            if(j==9){plane=vec3(-.12,-1.,.16);extent=.27;}
            float denominator=dot(plane,direction),distance=extent-dot(plane,origin);
            if(abs(denominator)<1e-8){if(distance<0.)far=-1.;continue;}
            float cut=distance/denominator;
            if(denominator<0. && cut>near){near=cut;face=plane;}
            if(denominator>0.)far=min(far,cut);
        }
        if(near>0. && far>=near && near<solidDepth){solidDepth=near;coreNormal=normalize(u_magnetic_axes*face);}
    }
    if(solidDepth<99.) {

        vec3 local=transpose(u_magnetic_axes)*(ray*solidDepth-center);
        vec3 normal=coreNormal;
        float diffuse=max(0.,dot(normal,normalize(vec3(-.6,.7,-.8))));
        float azimuth=atan(local.z,local.x);
        float grain=noise(local.xy*65.+local.z*vec2(31.,47.))*.5+.5;
        float flutes=pow(.5+.5*cos(azimuth*8.+local.y*4.),12.);
        float poles=smoothstep(.28,.45,abs(local.y)),waist=1.-smoothstep(.06,.14,abs(local.y));
        vec3 pole=local.y>0.?magnetic_pigment(2):magnetic_pigment(3);
        vec3 ceramic=mix(magnetic_pigment(1),pole*.55,poles);
        ceramic*=mix(1.,.22,waist)*(.70+.30*grain);
        color=color_tint(ceramic,u_magnetic_field_on,u_magnetic_field[0])*(.28+.72*diffuse);
        color+=magnetic_pigment(5)*flutes*(.035+.075*high)*(1.-waist);
        color+=magnetic_pigment(5)*pow(max(0.,dot(reflect(-normalize(vec3(-.6,.7,-.8)),normal),-ray)),22.)*.22;
        float edge=pow(1.-max(0.,dot(normal,-ray)),3.);
        color+=pole*(edge*.22+poles*.045)*(1.+energy*.4);
        for(int i=0;i<4;i++) {
            vec4 event=u_magnetic_events[i];float age=u_drift_time-event.x;
            if(age<0. || age>6.)continue;
            float direction=azimuth-event.y*.785398;
            float mark=exp(-(1.-cos(direction))*22.)*poles;
            color+=magnetic_pigment(4)*mark*event.z*exp(-age*1.3)*.65*u_magnetic_amount*u_plasma_details.y;
        }
    }
    vec3 emission=vec3(0);
    float width=.0028+.0022*energy;
    for(int row=0;row<12;row++) {
        vec4 bounds=u_magnetic_bounds[row];
        if(any(lessThan(p,bounds.xy-.08)) || any(greaterThan(p,bounds.zw+.08)))continue;
        float nearest=100.,along=0.,side=0.;
        for(int group=0;group<8;group++) {
            vec4 box=u_magnetic_groups[row*8+group];
            if(any(lessThan(p,box.xy-.08)) || any(greaterThan(p,box.zw+.08)))continue;
            vec4 a=texelFetch(u_magnetic_paths,ivec2(group*6,row),0);
            for(int j=1;j<=6;j++) {
                vec4 b=texelFetch(u_magnetic_paths,ivec2(group*6+j,row),0);
                vec2 delta=b.xy-a.xy;float f=clamp(dot(p-a.xy,delta)/max(dot(delta,delta),1e-10),0.,1.);
                float depth=1./mix(a.z,b.z,f),distance=length(p-mix(a.xy,b.xy,f));
                if(depth/ray.z<solidDepth+.005 && distance<nearest) {
                    nearest=distance;along=mix(a.w,b.w,f);side=(delta.x*(p.y-a.y)-delta.y*(p.x-a.x))/max(length(delta),1e-8);
                }
                a=b;
            }
        }
        if(nearest>=.075)continue;
        float edgeFade=1.-smoothstep(.05,.075,nearest);
        float wire=exp(-pow((nearest-width*.55)/(width*.42),2.));
        float inner=exp(-pow(nearest/(width*.52),2.));
        float halo=exp(-nearest/(width*4.))*.17*edgeFade;
        float grain=.60+.40*pow(.5+.5*sin(along*180.-phase*4.+row),8.);
        vec3 pole=mix(magnetic_pigment(2),magnetic_pigment(3),smoothstep(.3,.7,along));
        pole=mix(pole,magnetic_pigment(5),(.15+.25*max(0.,side/width))*grain);
        float selected=0.,charge=0.;
        if(row<8) {
            for(int i=0;i<4;i++) {
                vec4 event=u_magnetic_events[i];float age=u_drift_time-event.x;
                if(age<0. || age>6.)continue;
                float own=abs(float(row)-event.y)<.1?1.:0.;
                float pair=abs(float(row)-mod(event.y+1.,8.))<.1?.45:0.;
                float front=(age-.1)/1.65;
                if(front>0. && front<1.25)charge+=event.z*(own*exp(-pow((along-front)/.065,2.))+pair*exp(-pow((along-(1.-front))/.065,2.)))*exp(-age*.23);
                selected+=own*event.z*exp(-age*.65)*.25*(1.-smoothstep(4.8,6.,age));
            }
            float drift=pow(.5+.5*cos(along*25.-phase*9.+row*1.7),16.);
            emission+=color_tint(pole,u_magnetic_field_on,u_magnetic_field[1])*(wire+halo)*(.25+.62*energy+selected)*u_plasma_details.x;
            emission+=color_tint(magnetic_pigment(4),u_magnetic_field_on,u_magnetic_field[2])*(inner+halo*2.)*charge*3.5*u_magnetic_amount*u_plasma_details.y;
            emission+=magnetic_pigment(5)*inner*drift*(.025+.24*high)*u_plasma_details.z;
        } else {
            vec4 event=u_magnetic_events[row-8];float age=u_drift_time-event.x;
            float envelope=smoothstep(.6,.95,age)*(1.-smoothstep(2.,2.7,age));
            float packets=.3+.7*pow(.5+.5*cos(along*15.-age*10.),8.);
            emission+=color_tint(mix(magnetic_pigment(2),magnetic_pigment(3),along),u_magnetic_field_on,u_magnetic_field[2])*(wire+halo*2.)*event.z*envelope*packets*2.8*u_magnetic_amount*u_plasma_details.y;
        }
    }
    return color+emission/(1.+emission*.60);
}

vec3 magnetic_core_position(){
    float drive=clamp(.55*u_scale+.45*u_flux,0.,1.);
    return vec3(sin(u_time*.27),sin(u_time*.19+1.)*.65,cos(u_time*.23))*(.025+.105*drive);
}
vec3 plasma_loop(float f,float id) {
    float theta=mix(.43,2.71159,f),az=id*.7853982;
    float stretch=1.9+.20*sin(id*2.1+u_time*.19)+u_scale*.30;
    float knot=floor((theta-.43)/.38)*.38+.43,u=(theta-knot)/.38;
    float angular=mix(pow(sin(knot),2.),pow(sin(knot+.38),2.),u);
    float sharpen=smoothstep(.25,.85,.55*u_scale+.45*u_flux+.25*u_impact);
    float radius=stretch*mix(sin(theta)*sin(theta),angular,sharpen*.85);
    az+=.24*sin(theta*3.+u_time*.4+id)*(.3+u_flux);
    return magnetic_core_position()+vec3(radius*sin(theta)*cos(az),radius*cos(theta),radius*sin(theta)*sin(az));
}

vec3 experimental_plasma_scene(vec2 p,vec3 material,int form) {
    if(form==0)return magnetic_cached_field(p,material);
    vec2 uv=vec2(p.x*u_resolution.y/u_resolution.x+.5,p.y+.5);
    if(form==1)return texture(u_arc_scene,uv).rgb;
    return texture(u_aurora_scene,uv).rgb;
}

vec3 plasma_scene(vec2 p,vec3 material,int form) {
    if(u_plasma_experimental==1)return experimental_plasma_scene(p,material,form);
    float energy=clamp(.5*u_scale+.5*u_flux,0.,1.);
    float bank=.12*sin(u_drift_time*.11)+.04*sin(u_drift_time*.037+1.2);
    vec2 veil_p=mat2(cos(bank),sin(bank),-sin(bank),cos(bank))*p;
    vec3 ray=normalize(vec3(form==2?veil_p:p,1.35));
    vec2 stars_p=form==2?mat2(cos(bank),-sin(bank),sin(bank),cos(bank))*p:p;
    vec3 color=color_tint(vec3(.003,.005,.014),u_plasma_sky_on,u_plasma_sky[0])+plasma_stars(stars_p,form)*u_plasma_details.z;
    vec3 pigment=.70+.6*clamp(material,0.,1.);
    if(form==2) {
        // Thin folded emitting sheets: absorb behind the folds, retain dark gaps.
        vec3 sum=vec3(0.);float transmission=1.;
        float travel=u_time*.55;
        for(int i=0;i<56;i++) {
            float distance=.9+float(i)*.27;
            vec3 q=ray*distance;q.z+=travel;
            q.x+=.35*sin(travel*.12);
            float fold=q.x-1.25*sin(q.z*.62+u_time*.08)-.32*sin(q.z*1.9);
            float ridge=exp(-abs(sin(fold*1.75))*(18.-5.*energy));
            float hem=-.5+.35*sin(q.z*.5+q.x*.7);
            float height=q.y-hem;
            float curtain=exp(-max(0.,height)*.55)*smoothstep(-.18,.10,height);
            float threads=.45+.55*pow(.5+.5*sin(q.z*19.+fold*8.+u_time*.5),5.);
            float density=ridge*curtain*(.3+.7*threads)*u_plasma_details.x;
            float through=exp(-density*.32);
            float wave=pow(.5+.5*sin(q.z*1.6-u_time*2.4+q.y*.8),8.);
            vec3 hue=plasma_tint(q.z*.22+q.y*.8+u_time*.07+1.8);
            vec3 emission=color_tint(hue,u_auroral_curtains_on,u_auroral_curtains[0])*pigment*(.5+energy*.65+u_sparkle*threads*.35);
            emission+=color_tint(hue,u_auroral_curtains_on,u_auroral_curtains[1])*wave*(.25+u_impact*2.)*u_plasma_details.y;
            sum+=transmission*(1.-through)*emission;
            transmission*=through;
        }
        return color*transmission+sum;
    }
    float solidDepth=100.;vec3 solidCenter=vec3(0.);float solidId=0.;
    for(int i=0;i<7;i++) {
        if(form==0 && i>0)break;
        vec3 center=plasma_view(form==0 ? magnetic_core_position() : plasma_node(float(i)));
        float radius=form==0 ? .48+.035*u_scale : .10+.035*plasma_seed(vec2(i,3.));
        float depth=plasma_sphere(ray,center,radius);
        if(depth<solidDepth) {solidDepth=depth;solidCenter=center;solidId=float(i);}
    }
    if(solidDepth<99.) {
        vec3 n=normalize(ray*solidDepth-solidCenter);
        float shade=.20+.80*max(0.,dot(n,normalize(vec3(-.6,.7,-.8))));
        float bands=form==0 ? .5+.5*sin(n.y*17.+n.x*6.+sin(n.z*9.+n.x*5.)+u_time*.55)
            : .5+.5*cos(atan(n.z,n.x)*3.+n.y*5.-u_time*.4);
        vec3 body=plasma_tint(solidId*.7+u_time*.09+n.y*2.+(form==0?energy*.65:1.4));
        if(form==1)body=mix(body,vec3(.78,.91,1.),.28);
        color=color_tint(body,form==0 ? u_magnetic_field_on : u_arcs_charge_on,
            form==0 ? u_magnetic_field[0] : u_arcs_charge[0])*pigment*(form==0?(.12+.12*bands):(.20+.16*bands))*shade;
        float rim=pow(1.-max(0.,dot(n,-ray)),3.);
        color+=color_tint(body,form==0 ? u_magnetic_field_on : u_arcs_charge_on,
            form==0 ? u_magnetic_field[0] : u_arcs_charge[0])*(rim*.45+pow(bands,10.)*(.10+.3*u_impact))*(.5+energy);
    }
    vec3 emission=vec3(0.);
    if(form==0) {
        for(int k=0;k<8;k++) {
            float id=float(k);
            bool cachedLoop=u_original_path_on==1;
            if(cachedLoop){vec4 bounds=texelFetch(u_original_paths,ivec2(41,k),0);if(any(lessThan(p,bounds.xy-.12)) || any(greaterThan(p,bounds.zw+.12)))continue;}
            vec3 a=cachedLoop ? texelFetch(u_original_paths,ivec2(0,k),0).xyz : plasma_view(plasma_loop(0.,id));
            float nearest=100.,along=0.;
            for(int j=1;j<=40;j++) {
                float f=float(j)/40.;vec3 b=cachedLoop ? texelFetch(u_original_paths,ivec2(j,k),0).xyz : plasma_view(plasma_loop(f,id));
                vec2 sample;
                if(cachedLoop){vec2 delta=b.xy-a.xy;float part=clamp(dot(p-a.xy,delta)/max(dot(delta,delta),1e-8),0.,1.);sample=vec2(length(p-a.xy-part*delta),1./mix(a.z,b.z,part));}
                else sample=plasma_segment(p,a,b);
                a=b;
                if(sample.y/ray.z>solidDepth+.005)continue;
                if(sample.x<nearest) {nearest=sample.x;along=f;}
            }
            // Shade the continuous strand once, avoiding bright segment joints.
            if(nearest>.12)continue;
            float width=.0024+.0018*u_scale;
            float filament=exp(-nearest*nearest/(width*width));
            float halo=exp(-nearest/(width*5.))*.28;
            float pulse=pow(.5+.5*sin(along*15.-u_time*3.+id*2.),12.);
            vec3 hue=plasma_tint(id*.55+along*2.+u_time*.065);
            emission+=color_tint(hue,u_magnetic_field_on,u_magnetic_field[1])*pigment*(filament+halo)*(.45+1.35*energy*energy+.35*u_impact)*u_plasma_details.x;
            emission+=color_tint(hue,u_magnetic_field_on,u_magnetic_field[2])*(filament+halo)*pulse*(.12+u_impact*1.2+u_sparkle*.3)*u_plasma_details.y;
            emission+=color_tint(hue,u_magnetic_field_on,u_magnetic_field[2])*filament*pow(pulse,3.)*.3*u_sparkle*u_plasma_details.z;
        }
    } else {
        float wireDepth=100.;vec3 wireCore=vec3(0.);
        for(int k=0;k<7;k++) {
            float id=float(k),seed=plasma_seed(vec2(k,11.));
            vec3 start=plasma_node(id),end=plasma_node(mod(id+2.,7.));
            vec3 axis=normalize(end-start),side=normalize(cross(axis,vec3(0,0,1)));
            float phase=fract(u_drift_time*(.22+seed*.10)+seed);
            float flash=exp(-phase*18.)*(.08+.40*energy)+u_impact*(.45+.55*seed);
            vec3 a=plasma_view(start);
            for(int j=1;j<=18;j++) {
                float f=float(j)/18.;
                float jag=sin(f*71.+seed*19.+u_time*.7)*.12+sin(f*133.+seed*5.)*.07;
                vec3 q=mix(start,end,f)+side*jag*sin(f*3.14159);
                vec3 b=plasma_view(q);vec2 sample=plasma_segment(p,a,b);a=b;
                if(sample.y/ray.z<solidDepth+.008) {
                    float width=.0015+.0015*u_impact+.0007*smoothstep(.20,.85,energy);
                    float line=exp(-sample.x*sample.x/(width*width));
                    float glow=exp(-sample.x/(width*6.))*.16;
                    vec3 hue=plasma_tint(seed*5.+u_time*.09+f*.8);
                    vec3 charge=color_tint(hue,u_arcs_charge_on,u_arcs_charge[1])*(pigment*(.055+.52*smoothstep(.12,.82,energy))*u_plasma_details.x+flash*1.5*u_plasma_details.y);
                    emission+=charge*glow;
                    float pulse=pow(.5+.5*sin(f*17.-u_time*4.+id),18.);
                    if(sample.x<width*2.5 && sample.y/ray.z<wireDepth){
                        wireDepth=sample.y/ray.z;
                        wireCore=charge*line+color_tint(hue,u_arcs_charge_on,u_arcs_charge[2])*line*pulse*.65*u_sparkle*u_plasma_details.z;
                    }
                }
                if(j==5 || j==11 || j==15) {
                    vec3 tip=q+side*(.2+.35*seed)+axis*.20;
                    vec2 branch=plasma_segment(p,b,plasma_view(tip));
                    if(branch.y/ray.z<solidDepth+.008)
                        emission+=color_tint(plasma_tint(seed*5.+u_time*.09),u_arcs_charge_on,u_arcs_charge[2])*exp(-branch.x/.0014)*flash*.65*u_plasma_details.y;
                }
            }
        }
        emission+=wireCore;
    }
    // Compress emitted light alone, retaining saturated cores and dark surroundings.
    return color+emission/(1.+emission*.65);
}

// Main-only physical handoffs. Accepted isolated world helpers stay unchanged.
float handoff_front(vec2 p) {
    float phase=u_handoff.y;
    float field=.5;
    if(u_handoff.x<1.5) {
        // A connected liquid bank advances with broad flowing bends.
        field=.5+p.y*.62+.10*sin(p.x*5.+u_time*.13)
            +.04*sin(p.x*11.-u_time*.17);
    } else if(u_handoff.x<2.5) {
        // Electrical channels open locally, then join into one weather field.
        float bend=p.x+.12*sin(p.y*9.+u_time*.09);
        field=.12+abs(bend)*.75+.09*sin(p.y*6.-u_time*.11);
    } else if(u_handoff.x<3.5) {
        // A broad, billowing veil reveals solid terrain behind it.
        field=.5+p.x*.43+.11*sin(p.y*5.+u_time*.09)
            +.05*sin(p.x*6.-p.y*8.+u_time*.12);
    } else {
        // Orbital opening preserves a readable island beside the magnetic sky.
        field=length((p-vec2(.12,.04))*vec2(.8,1.))*.85;
    }
    field=clamp(field,.12,.88);
    return smoothstep(field-.085,field+.085,phase);
}
float handoff_share(float family,float front) {
    if(u_directed==0 || u_handoff.x<.5) return 1.;
    if(abs(u_handoff.z-family)<.1) return 1.-front;
    if(abs(u_handoff.w-family)<.1) return front;
    return 1.;
}

// Modal experiment table. Metre amplitudes; optical gain never changes physics.
uniform vec4 u_cym_modes[36];
uniform int u_cym_count,u_cym_colors_on;
uniform vec4 u_cym_basin;
uniform vec2 u_cym_actuator;
uniform vec3 u_cym_colors[5];
uniform float u_cym_material,u_cym_depth;
uniform vec3 u_cym_camera,u_cym_style;
uniform vec2 u_cym_pan;
uniform vec3 u_cym_stone_colors[2];
uniform int u_cym_stone_colors_on;
uniform vec3 u_cym_view; // optional orbit, tracer contrast, reset source-time
uniform vec3 u_cym_dye_colors[2];
uniform int u_cym_dye_colors_on;
vec2 cym_optical_motion;
vec3 cym_pigment(int i) {
    if(u_cym_colors_on==1)return u_cym_colors[i];
    if(i==0)return vec3(.008,.025,.05);
    if(i==1)return vec3(.03,.10,.14);
    if(i==2)return vec3(.85,.91,.98);
    if(i==3)return vec3(.45,.65,.72);
    return vec3(.015,.022,.031);
}
vec4 cym_field(vec2 p) {
    vec2 z=vec2(0);vec2 dx=vec2(0),dy=vec2(0),lap=vec2(0);
    for(int i=0;i<36;i++) {
        if(i>=u_cym_count)break;
        vec4 mode=u_cym_modes[i];vec2 k=mode.xy*3.14159265;
        vec2 c=cos(k*p),s=sin(k*p);
        z+=mode.zw*c.x*c.y;
        lap-=mode.zw*dot(k,k)*c.x*c.y;
        dx+=mode.zw*(-k.x*s.x*c.y);
        dy+=mode.zw*(-k.y*c.x*s.y);
    }
    float amplitude=sqrt(dot(z,z)+4e-10);
    float curvature=(dot(dx,dx)+dot(dy,dy)+dot(z,lap))/amplitude-(dot(z,dx)*dot(z,dx)+dot(z,dy)*dot(z,dy))/pow(amplitude,3.);
    // Strong, bounded optical magnification reveals tiny slopes without inventing flow.
    vec2 tracerSlope=vec2(dx.x,dy.x)*u_cym_basin.z*12.;
    cym_optical_motion=.018*tanh(tracerSlope/.018);
    float height=(amplitude-.00002)*u_cym_basin.z;
    vec2 slope=vec2(dot(z,dx),dot(z,dy))/max(amplitude,.00000001)*u_cym_basin.z;
    if(u_cym_basin.w>.5 && u_cym_basin.w<1.5) {height=z.x*u_cym_basin.z;slope=vec2(dx.x,dy.x)*u_cym_basin.z;curvature=lap.x;}
    // Smooth bounded optical relief: the physical modal state is untouched.
    // Regularized quadrature norm avoids cusps at cancellation; raw-height view stays signed.
    float compression=1.+abs(height)/.065;
    height/=compression;slope/=compression*compression;
    return vec4(height,slope,curvature*u_cym_basin.z/(compression*compression));
}
float cym_stone_noise(vec2 p) {
    vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
    float a=fract(sin(dot(i,vec2(127.1,311.7)))*43758.5453);
    float b=fract(sin(dot(i+vec2(1,0),vec2(127.1,311.7)))*43758.5453);
    float c=fract(sin(dot(i+vec2(0,1),vec2(127.1,311.7)))*43758.5453);
    float d=fract(sin(dot(i+vec2(1,1),vec2(127.1,311.7)))*43758.5453);
    return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);
}
vec3 cym_stone(vec2 p) {
    vec3 base=u_cym_stone_colors_on==1 ? u_cym_stone_colors[0] : vec3(.009,.012,.019);
    vec3 mineral=u_cym_stone_colors_on==1 ? u_cym_stone_colors[1] : vec3(.64,.71,.77);
    float cloud=cym_stone_noise(p*3.7),detail=cym_stone_noise(p*17.);
    float vein=pow(1.-abs(sin((p.x*.68+p.y)*13.+cloud*4.+detail*.6)),18.);
    float hair=pow(1.-abs(sin((p.x*.68+p.y)*13.+cloud*4.+detail*.6+.20)),36.);
    if(u_cym_style.x<.5)return base*(.6+.6*cloud)+mineral*(vein*.025+hair*.012);
    return mix(base*.9,mineral*(.32+.25*cloud),.32+.14*detail)+mineral*(vein*.38+hair*.15);
}
vec3 cym_water(vec2 p) {
    // Deliberate table view: a shallow rectangular pool floating in dark space,
    // jewelled nodes, fluid glints and submerged copper caustics.
    float aspect=u_cym_basin.x/u_cym_basin.y;
    float yaw=u_cym_camera.x,pitch=u_cym_camera.y;
    vec3 target=vec3(u_cym_pan.x,0.,u_cym_pan.y);
    float distance=u_cym_camera.z*max(1.,1./max(aspect,.5));
    vec3 eye=target+distance*vec3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch));
    mat3 camera=journey_view(eye,target,0.);
    vec3 ray=normalize(camera*vec3(p,1.08));
    float t=-eye.y/ray.y;
    vec2 point=(eye+ray*t).xz;
    vec2 size=vec2(1.12,1.12/max(aspect,.5));
    vec2 q=point/(size*2.)+.5;
    vec3 background=cym_pigment(0)*(.12+.6*exp(-dot(p,p)*2.));
    if(t<0.)return background;
    float edge=max(abs(point.x)/size.x,abs(point.y)/size.y);
    float bevel=exp(-pow((edge-1.)*55.,2.));
    if(edge>1.) {
        float frameMask=1.-smoothstep(1.04,1.11,edge);
        float machining=.5+.5*sin(point.x*280.+point.y*90.);
        vec3 frame=cym_pigment(4)*(.5+.14*machining)+cym_pigment(2)*bevel*.22;
        frame+=cym_pigment(3)*exp(-pow((edge-1.025)*220.,2.))*.65;
        return mix(background,frame,frameMask);
    }
    vec4 field=cym_field(q);
    // Three bounded refinements give surface relief/parallax with no second solver.
    for(int j=0;j<3;j++) {
        t=(field.x-eye.y)/ray.y;point=(eye+ray*t).xz;q=point/(size*2.)+.5;
        field=cym_field(clamp(q,0.,1.));
    }
    if(any(lessThan(q,vec2(0))) || any(greaterThan(q,vec2(1))))return background;
    vec3 normal=normalize(vec3(-field.y/(size.x*2.),1.,-field.z/(size.y*2.)));
    vec3 reflected=reflect(ray,normal);
    float fresnel=.035+.65*pow(1.-max(0.,dot(normal,-ray)),5.);
    vec3 keyLight=normalize(vec3(cos(u_cym_style.y)*.85,1.15,sin(u_cym_style.y)*.85));
    float light=max(0.,dot(normal,keyLight));
    float glint=pow(max(0.,dot(reflected,normalize(vec3(-.4,.8,-.8)))),u_cym_material>1.5 ? 35. : 90.);
    float second=pow(max(0.,dot(reflected,normalize(vec3(.9,.4,.2)))),120.);
    float caustic=pow(.5+.5*sin(q.x*38.+field.y*7.+sin(q.y*23.-field.z*6.)),12.)
        *pow(.5+.5*sin(q.y*31.-field.z*8.),4.);
    float amplitude=clamp(field.x*7.,0.,1.);
    vec3 water=mix(cym_pigment(0),cym_pigment(1),.22+.65*light);
    water+=cym_pigment(3)*caustic*(.03+.16*amplitude)*(1.-fresnel);
    // Authored light-box reflections bend with modal normals, not an injected wave.
    vec2 env=reflected.xz/max(.25,abs(reflected.y));
    vec2 lightUV=mat2(cos(u_cym_style.y),sin(u_cym_style.y),-sin(u_cym_style.y),cos(u_cym_style.y))*env;
    float strip=exp(-pow((lightUV.x+.18)*18.,2.))*exp(-pow((lightUV.y+1.2)*.8,2.));
    float crossLight=exp(-pow((env.y-.7)*12.,2.))*exp(-env.x*env.x*.6);
    float fineLight=exp(-pow((lightUV.x-.38)*26.,2.))*exp(-pow((lightUV.y+.8)*.8,2.));
    vec3 environment=cym_pigment(0)*.35+cym_pigment(2)*(strip*.58+fineLight*.16);
    environment+=cym_pigment(3)*crossLight*.045;
    float edgeDepth=1.-exp(-min(min(q.x,1.-q.x),min(q.y,1.-q.y))*30.);
    water*=.32+.68*edgeDepth;
    // Bed light and refracted micro-caustics reveal water depth and pressure ridges.
    water+=cym_pigment(2)*caustic*(.035+.11*amplitude)*edgeDepth;
    float ridge=1.-exp(-length(field.yz)*3.5);
    // Thin refracting water above a textured bed, with optical absorption separate from physics.
    vec2 bed=q+field.yz*.08;
    float path=clamp(u_cym_depth/.005,.2,5.)/max(.35,dot(normal,-ray));
    float transmission=exp(-path*.38);
    vec3 floorColor=cym_stone(bed);
    float focusing=pow(clamp(-field.w*.25,0.,1.),2.);
    // Local curvature focusing is an optical approximation, not a second wave solver.
    floorColor+=cym_pigment(3)*focusing*(.15+.25*caustic);
    water=mix(water*.24,floorColor,transmission*.88)*(.55+.45*edgeDepth);
    water+=cym_pigment(2)*focusing*.13;
    water+=cym_pigment(1)*(.014+.055*light)+cym_pigment(2)*ridge*.085;
    if(u_cym_material>.5 && u_cym_material<1.5)water=mix(water,environment,.65);
    if(u_cym_material>1.5)water=mix(water,cym_pigment(1)*(.08+.4*amplitude),.7);
    water=mix(water,environment,.15+fresnel*.45)+cym_pigment(2)*(glint*.32+second*.12);
    float rim=pow(1.-min(min(q.x,1.-q.x),min(q.y,1.-q.y))*2.,35.);
    water+=cym_pigment(3)*rim*.32;
    vec2 electrode=(q-u_cym_actuator)*vec2(1.,1./max(aspect,.5));
    water+=cym_pigment(3)*exp(-dot(electrode,electrode)*6000.)*.3;
    // Sparse timed pigment marks: optical displacement only, NOT advected fluid.
    // Birth/spreading is presentation, independent of audio; slopes provide real surface cues.
    if(u_cym_view.y>0. && u_cym_basin.w<1.5) {
        float clock=max(0.,u_drift_time-u_cym_view.z);
        vec2 tracerUV=q+clamp(cym_optical_motion,vec2(-.035),vec2(.035));
        for(int i=0;i<3;i++) {
            float birth=floor((clock-float(i)*10.)/30.)*30.+float(i)*10.;
            float age=clock-birth;
            if(birth<0. || age>24.)continue;
            float id=birth/10.;
            vec2 center=vec2(.20+.60*fract(sin(id*17.3+2.1)*437.1),.20+.60*fract(sin(id*31.7+1.3)*321.9));
            vec2 d=tracerUV-center;
            float radius=.014+.009*min(age,14.);
            float radial=length(d);
            float angle=atan(d.y,d.x)-u_cym_style.z*age*.8*exp(-radial*radial/(radius*radius*3.));
            float scallop=1.+.15*sin(angle*3.+id)+.07*sin(angle*7.-id);
            float spot=exp(-dot(d,d)/(radius*radius*scallop));
            vec2 swirlUV=vec2(cos(angle),sin(angle))*radial/max(radius,.001);
            float plume=cym_stone_noise(swirlUV*3.8+vec2(id*2.4,id*7.1));
            float threads=pow(smoothstep(.25,.72,plume),2.);
            float halo=exp(-dot(d,d)/(radius*radius*2.6))*(.18+.22*threads);
            float fade=smoothstep(0.,.65,age)*(1.-smoothstep(17.,24.,age));
            vec3 pigment=u_cym_dye_colors_on==1 ? u_cym_dye_colors[i%2] : (i%2==0 ? vec3(.95,.19,.055) : vec3(.64,.20,.95));
            float coverage=clamp((spot*(.18+.52*threads)+halo*.75)*fade*u_cym_view.y,0.,.68);
            water=mix(water,pigment*(.38+.55*light)+environment*.12,coverage);
        }
    }
    if(u_cym_basin.w>1.5 && u_cym_basin.w<2.5)water=mix(cym_pigment(0),cym_pigment(2),1.-exp(-abs(field.x)*25.));
    if(u_cym_basin.w>2.5)water=normal*.5+.5;
    return water/(vec3(1.)+water*.25);
}

vec4 scene_frame()
{
    bool directed = u_directed == 1;
    bool held_plasma = u_debug_state >= 31.5 && u_debug_state < 35.5;
    bool held_fog = u_debug_state >= 27.5 && u_debug_state < 31.5;
    bool held_earth = u_debug_state >= 23.5 && u_debug_state < 27.5;
    bool held_air = u_debug_state >= 18.5 && u_debug_state < 23.5;
    bool held_fire = u_debug_state > 13.5 && u_debug_state < 18.5;
    bool fire_mode = held_fire || (directed && u_world_mix.w > 0.);
    float fire_takeover = directed ? u_world_mix.w : (held_fire ? 1. : 0.);
    float debug_state = (held_fire || held_air || held_earth || held_fog || held_plasma) ? 1.0 : (u_debug_state > 10.5 && u_debug_state < 12.5) ? 1.0 : u_debug_state;
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;

    // Correct for the window's aspect ratio.
    vec2 p = uv - 0.5;
    p.x *= u_resolution.x / u_resolution.y;
    p=main_carry(p);
    if (directed) {
        float warp=(u_handoff.x>.5 ? 0. : u_world_warp)*(.12+.12*clamp(u_scale+u_flux,0.,1.));
        float angle=warp*exp(-dot(p,p)*1.2)*sin(length(p)*3.+u_time*.12);
        p=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*p;
        p*=1.+warp*(.6-length(p)*.3);
    }

    if (u_debug_state > 36.5 && u_debug_state < 37.5) {return vec4(cym_water(p),1.);}
    if (u_debug_state > 35.5 && u_debug_state < 36.5)
    {
        return vec4(isolated_galaxy_scene(p), 1.0);
    }

    if (debug_state > 2.5 && debug_state < 3.5)
    {
        return vec4(isolated_cosmic_scene(p, vec3(0.0), 0.0, 1.0)+stellar_layers(p), 1.0);
    }

    vec2 screen_p = p;
    float water_takeover = debug_state > 5.5 ? 1.0
        : (debug_state < .5 ? water_handoff(u_drift_time) : 0.0);
    if (directed) water_takeover = u_world_mix.z;
    bool water_mode = water_takeover > 0.0;
    vec4 forms = water_forms();
    float cosmic_takeover = (
        debug_state < 0.5
        || debug_state > 3.5
    ) ? cosmic_handoff(u_drift_time, debug_state > 3.5) : 0.0;
    if (debug_state > 4.5) cosmic_takeover = 1.0;
    if (water_mode) cosmic_takeover = 0.0;
    if (directed) cosmic_takeover = u_world_mix.y;
    float canvas_zoom = mix(3.4, 1.0, cosmic_takeover);
    // Tiny music-driven pressure on the entire system, never independent
    // planet/ring scaling. Bounded to two percent at full presence.
    canvas_zoom *= 1.0 + cosmic_takeover * 0.02 * clamp(u_scale, 0.0, 1.0);
    vec2 cosmic_p = screen_p / canvas_zoom;
    vec2 disk = cosmic_p / 0.30;
    vec3 surface_normal = vec3(disk, sqrt(max(0.0, 1.0 - dot(disk, disk))));
    float surface_spin = u_drift_time * 0.035 * cosmic_takeover;
    vec3 surface_point = vec3(
        cos(surface_spin) * surface_normal.x + sin(surface_spin) * surface_normal.z,
        surface_normal.y,
        -sin(surface_spin) * surface_normal.x + cos(surface_spin) * surface_normal.z);
    vec2 surface_domain = (surface_point.xy + surface_point.z * vec2(0.30, 0.12)) * 0.72;
    // The source field contracts toward the sphere and wraps onto its surface.
    float contraction = mix(1.0, 0.34, cosmic_takeover);
    p = mix(screen_p / contraction, surface_domain,
        cosmic_takeover * (1.0 - smoothstep(0.98, 1.03, length(disk))));
    float gather_twist = sin(cosmic_takeover * 3.14159265) * 0.30
        * exp(-length(screen_p));
    p = mat2(cos(gather_twist), sin(gather_twist),
        -sin(gather_twist), cos(gather_twist)) * p;

    if (fire_mode) {
        float molten=molten_weight(), wild=firescape_weight();
        vec2 fire_p=mix(fire_domain(screen_p),molten_domain(screen_p)*.4,molten);
        if (wild > 0.) fire_p=fire_domain(screen_p)*(1.-molten-wild)
            +molten_domain(screen_p)*.4*molten+firescape_domain(screen_p)*wild;
        if (directed) {
            // Remove unbounded travel offsets before interpolating world spaces.
            // Each scene still animates with its original uninterrupted clock.
            fire_p.y += (u_time*.32+u_drift_time*.025)*.32*(1.-molten-wild)
                -u_time*.28*.4*molten+u_time*.095*wild;
        }
        p=mix(p,fire_p,fire_takeover);
    }

    float air_gather=directed ? u_air_weight : (held_air ? 1. : 0.);
    if(air_gather>0.) {
        vec4 air_shape=air_forms();
        // Authored held forms preserve their accepted source projection.
        float gather=shared_spatial() ? 1. : air_shape.z+air_shape.w;
        p=mix(p,air_material_domain(screen_p,air_shape),air_gather*gather);
    }

    float plasma_amount=directed ? u_plasma_weight : (held_plasma ? 1. : 0.);
    float fog_amount=directed ? u_fog_weight : (held_fog ? 1. : 0.);
    float earth_amount=directed ? u_earth_weight : (held_earth ? 1. : 0.);
    vec3 ef=earth_forms();
    EarthSurface dune=EarthSurface(vec3(0),vec3(0,1,0),100.,0.);
    EarthSurface strata=dune,cavern=dune;
    if(earth_amount>0.) {
        vec2 domain=vec2(0.);
        if(ef.x>0.){dune=earth_surface(screen_p,0);domain+=earth_domain(dune,0)*ef.x;}
        if(ef.y>0.){strata=earth_surface(screen_p,1);domain+=earth_domain(strata,1)*ef.y;}
        if(ef.z>0.){cavern=earth_surface(screen_p,2);domain+=earth_domain(cavern,2)*ef.z;}
        p=mix(p,domain,earth_amount);
    }

    float t = u_time * 0.18;
    float distortion = u_distortion;

    // Bass = physical mass: a whole-space pressure pulse applied before
    // any other deformation, so a strong kick visibly moves the world.
    float bass_pressure = clamp(u_scale, 0.0, 1.0);
    float pressure = bass_pressure * bass_pressure;

    // Slowly deform the space itself.
    vec2 q = p * (1.0 - pressure * 0.18);

    q += 0.18 * distortion * vec2(
        sin(q.y * 3.0 + t),
        cos(q.x * 3.0 - t)
    );

    float morph_time = u_drift_time * 0.08 + t * 0.35;
    float form_presence = exp(-length(q) * 1.4);
    vec2 flow = vec2(
        sin(q.y * 1.6 + morph_time)
            + 0.5 * cos(q.x * 1.1 - morph_time * 0.7),
        cos(q.x * 1.3 - morph_time * 0.8)
            + 0.5 * sin(q.y * 1.7 + morph_time * 0.6)
    );
    q += flow * form_presence * 0.045;

    float sparkle = clamp(u_sparkle, 0.0, 1.0);
    float impact = clamp(u_impact, 0.0, 1.0);
    float flux = clamp(u_flux, 0.0, 1.0);
    float radius = length(q);
    q += normalize(q + vec2(0.0001))
        * pressure * form_presence * 0.12;
    float shockwave = impact * exp(-radius * 4.0)
        * (0.5 + 0.5 * sin(radius * 32.0 - u_drift_time * 10.0));
    q += normalize(q + vec2(0.0001)) * shockwave * 0.035;

    // Medium-energy dynamics: the constant shockwave above already
    // breathes with every impact; this is a separate, sparse, hard-
    // thresholded kick so an ordinary beat does nothing extra but a
    // transient that truly punches through gives a noticeable physical
    // jolt -- "oh, THAT kick moved the world," not constant twitching.
    float kick_trigger = smoothstep(0.42, 0.82, impact);
    q += normalize(q + vec2(0.0001)) * kick_trigger * 0.11;

    // Visual state: slow, independently-phased dwell cycles decide
    // WHEN each alternate manifestation gets its turn; the live music
    // signal decides HOW STRONGLY it actually appears. Organic/Eye is
    // simply whatever is left over, so it always remains the home base.
    // A shared, slow noise offset keeps every dwell cycle's timing
    // from ever locking into one exact repeating period, so the whole
    // sequence of morphologies stops feeling like the same loop.
    float state_phase_jitter = (
        noise(vec2(u_drift_time * 0.011, 3.3)) - 0.5
    ) * 3.2;
    float tunnel_weight = dwell(u_drift_time * 0.1083 + state_phase_jitter)
        * clamp(flux * 1.0 + pressure * 0.35, 0.0, 1.0);
    float fractal_weight = dwell(
        u_drift_time * 0.0861 + 1.7 + state_phase_jitter
    ) * clamp(flux * 1.0 + pressure * 0.3, 0.0, 1.0);
    float geometric_weight = dwell(
        u_drift_time * 0.1337 + 4.2 + state_phase_jitter
    ) * clamp(impact * 1.4 + pressure * 0.5, 0.0, 1.0);
    // Cosmic is now a final depth-composited takeover, not a competing warp.
    float cosmic_weight = 0.0;

    // Horizon/Pathway: a different spatial grammar -- forward, toward
    // a distant vanishing point, instead of always inward/outward.
    // Present broadly through its dwell window rather than needing a
    // spike, so it reads as a spacious place to be, not a spike effect.
    float horizon_weight = dwell(
        u_drift_time * 0.0745 + 5.6 + state_phase_jitter
    ) * clamp(0.35 + flux * 0.35 + bass_pressure * 0.3, 0.0, 1.0);

    // State aging: a state that has been continuously dominant for a
    // while (current dwell AND an earlier sample of the same dwell are
    // both "on") matures, so it breathes and mutates the longer it
    // holds the stage, then naturally resets as it cycles away.
    float tunnel_maturity = min(
        dwell(u_drift_time * 0.1083 + state_phase_jitter),
        dwell(u_drift_time * 0.1083 + state_phase_jitter - 2.6)
    );
    float fractal_maturity = min(
        dwell(u_drift_time * 0.0861 + 1.7 + state_phase_jitter),
        dwell(u_drift_time * 0.0861 + 1.7 + state_phase_jitter - 2.6)
    );
    float geometric_maturity = min(
        dwell(u_drift_time * 0.1337 + 4.2 + state_phase_jitter),
        dwell(u_drift_time * 0.1337 + 4.2 + state_phase_jitter - 2.6)
    );
    float cosmic_maturity = min(
        dwell(u_drift_time * 0.0690 + 2.9 + state_phase_jitter),
        dwell(u_drift_time * 0.0690 + 2.9 + state_phase_jitter - 2.6)
    );
    float horizon_maturity = min(
        dwell(u_drift_time * 0.0745 + 5.6 + state_phase_jitter),
        dwell(u_drift_time * 0.0745 + 5.6 + state_phase_jitter - 2.6)
    );
    float any_maturity = max(
        max(tunnel_maturity, fractal_maturity),
        max(geometric_maturity, max(cosmic_maturity, horizon_maturity))
    );

    // Sharpen overlapping handoffs so one vocabulary leads instead of
    // several equally loud layers blending into an indistinct average.
    tunnel_weight = pow(tunnel_weight, 1.25);
    fractal_weight = pow(fractal_weight, 1.25);
    geometric_weight = pow(geometric_weight, 1.25);
    cosmic_weight = pow(cosmic_weight, 1.25);
    horizon_weight = pow(horizon_weight, 1.25);

    if ((debug_state > 0.5 && debug_state < 1.5) || debug_state > 5.5) {
        tunnel_weight = 0.0; fractal_weight = 0.0; geometric_weight = 0.0;
        cosmic_weight = 0.0; horizon_weight = 0.0;
    } else if (debug_state > 1.5 && debug_state < 2.5) {
        tunnel_weight = 0.0; fractal_weight = 0.0; geometric_weight = 1.0;
        cosmic_weight = 0.0; horizon_weight = 0.0;
    } else if (debug_state > 2.5 && debug_state < 3.5) {
        tunnel_weight = 0.0; fractal_weight = 0.0; geometric_weight = 0.0;
        cosmic_weight = 1.0; horizon_weight = 0.0;
    }

    if (u_layer_mode != 0) {
        if (u_layer_mode == 2) {
            // Material playback retains the world's authored spatial envelopes.
            tunnel_weight *= effect(16);
            fractal_weight *= effect(32);
            horizon_weight *= effect(64);
        } else {
            tunnel_weight = effect(16);
            fractal_weight = effect(32);
            horizon_weight = effect(64);
        }
        // A held form owns its geometry; other scheduled worlds cannot leak in.
        if (debug_state > 0.5 && !(debug_state > 1.5 && debug_state < 2.5))
            geometric_weight = 0.0;
    }
    // Long advected Currents coordinates amplify recursive folds if the
    // background grammar returns while liquid still owns nearly the frame.
    // Ease it back later in the handoff; held forms and non-Water are unchanged.
    float field_release = mix(1.0-water_takeover,
        pow(1.0-water_takeover,3.0),water_currents_weight());
    tunnel_weight *= field_release;
    fractal_weight *= field_release;
    geometric_weight *= field_release;
    horizon_weight *= field_release;

    // Cosmic is an intentional world takeover: once it has weight, the
    // other vocabularies recede so the planet, rings, and starfield can own
    // the frame instead of blending into another abstract layer.
    float cosmic_dominance = cosmic_weight * 0.88;
    tunnel_weight *= 1.0 - cosmic_dominance;
    fractal_weight *= 1.0 - cosmic_dominance;
    geometric_weight *= 1.0 - cosmic_dominance;
    horizon_weight *= 1.0 - cosmic_dominance;

    if (shared_spatial()) {
        // Shared carriers below own spatial effects. Keep their strength out of
        // world coverage: a large fractal must not erase the world underneath.
        tunnel_weight=0.; fractal_weight=0.; horizon_weight=0.;
        if (directed) geometric_weight=u_world_mix.x;
    }

    float total_transform = tunnel_weight + fractal_weight
        + geometric_weight + cosmic_weight + horizon_weight;
    // Keep a faint organic home-state thread during overlapping handoffs.
    // Alternate vocabularies may still dominate, but the world never loses
    // all continuity when several dwell windows coincide.
    float organic_floor = 0.08 * (1.0 - cosmic_weight);
    float organic_weight = max(organic_floor, 1.0 - total_transform);
    float weight_sum = max(organic_weight + total_transform, 1.0);

    WaterSurface water;
    FallsSurface falls;
    if (water_mode) {
        water = water_surface(screen_p);
        vec2 water_domain = water.material;
        if (shared_spatial()) water_domain += mix(vec2(.32,-.16)*(u_time*.13+u_drift_time*.025)*vec2(.22,.27),
            vec2(0.,(u_time*.22+u_drift_time*.028)*.12),water_currents_weight());
        if (forms.w > 0.0) {
            falls = waterfall_surface(screen_p);
            vec2 fall_domain = waterfall_current(falls)*vec2(.28,.18);
            if (shared_spatial()) fall_domain.y -= (u_time*.72+u_drift_time*.08)*.18;
            water_domain = mix(water_domain,fall_domain,forms.w);
        }
        q = mix(q, water_domain, water_takeover);
        // Localize inherited event color/forms to the same disturbed patch.
        vec2 event_delta = water.position - vec2(0.8, 2.2);
        float event_patch = exp(-dot(event_delta, event_delta) * 0.45);
        impact *= mix(1.0,event_patch,water_takeover);
        kick_trigger *= mix(1.0,event_patch,water_takeover);
    }

    GeometricSurface geo_surface = GeometricSurface(vec2(0.0), 80.0, 0.0, 0.0);
    float geo_gather = smoothstep(0.0, 0.90, geometric_weight)
        * (1.0 - cosmic_takeover);
    if (geometric_weight > 0.0) geo_surface = geometric_surface(screen_p);
    if (geo_gather > 0.0 && geo_surface.kind > 0.5) {
        // Continuous mirror folds stretch the source along the corridor.
        // During assembly, contraction precedes full surface ownership;
        // release follows the same envelope back to the shared field.
        vec2 material_domain = geo_surface.uv * vec2(0.38, 0.95);
        material_domain.x = 2.0 - abs(mod(material_domain.x, 8.0) - 4.0);
        material_domain.y += sin(geo_surface.uv.x * 0.9 - t * 0.3)
            * (0.06 + flux * 0.09);
        float gathering_pressure = sin(geo_gather * 3.14159265)
            * (0.22 + bass_pressure * 0.14 + impact * 0.08);
        q *= 1.0 + gathering_pressure;
        q = mix(q, material_domain, geo_gather);
    }

    // Inversion needs spatial coordinates, not an ever-growing scroll offset.
    // Preserve this domain so overlapping tunnel/horizon states cannot make
    // the fractal fold converge to the same value across the whole screen.
    vec2 fractal_domain = q;

    // Wormhole/tunnel: reproject into (angle, depth) corridor space.
    float pre_radius = length(q);
    float pre_angle = atan(q.y, q.x);
    vec2 tunnel_q = vec2(
        pre_angle * (2.5 + tunnel_maturity * 1.5),
        1.0 / (pre_radius + 0.2) * (1.6 + tunnel_maturity * 0.8)
            - u_drift_time * (0.5 + tunnel_maturity * 0.3)
            - pressure * 2.2
    );
    if (directed) tunnel_q.y += u_drift_time*(.5+tunnel_maturity*.3);
    q = mix(q, tunnel_q, tunnel_weight);

    // Horizon/Pathway: perspective corridor converging toward a
    // distant horizon line. q.y is read as "forward" depth: geometry
    // narrows toward the horizon and depth bands scroll toward the
    // viewer, an impossible road/corridor through the same field.
    vec2 horizon_q = vec2(
        q.x / (0.35 + abs(q.y) * (1.1 + horizon_maturity * 0.7)),
        1.0 / (abs(q.y) + 0.22) * (1.2 + horizon_maturity * 0.6)
            - u_drift_time * (0.4 + horizon_maturity * 0.25)
    );
    if (directed) horizon_q.y += u_drift_time*(.4+horizon_maturity*.25);
    q = mix(q, horizon_q, horizon_weight);

    // Fractal: cheap recursive inversion fold (Kleinian-style).
    vec2 fractal_q = fractal_domain;
    for (int fi = 0; fi < 4; fi++)
    {
        fractal_q = abs(fractal_q) / max(dot(fractal_q, fractal_q), 0.0001)
            - vec2(
                0.9 + flux * 0.15 + fractal_maturity * 0.10
                    + bass_pressure * 0.08,
                0.6
            );
    }
    q = mix(q, fractal_q * mix(0.42, 0.26, fractal_maturity), fractal_weight);

    // Fractal Cubic Room: a sparse mutation, only surfacing once the
    // fractal state has held the stage a while -- an impossible
    // rectangular hallway folded through the same field, not a
    // permanent sixth mode.
    float room_gate = fractal_weight * fractal_maturity;
    vec2 room_cell = mod(q * (1.6 + bass_pressure * 0.6), 2.0) - 1.0;
    float room_box = max(abs(room_cell.x), abs(room_cell.y));
    vec2 room_q = room_cell / max(room_box, 0.001) * (0.6 + 0.4 * room_box);
    q = mix(q, room_q, room_gate * 0.55);

    if (shared_spatial()) q=spatial_carrier(fractal_domain);

    // Geometric Dream: evolving mandala/crystalline/kaleidoscopic forms.
// Smoothly morphs between radial, mandala-symmetric, crystalline, and
// faceted kaleidoscope structures. Bass drives mass and rotation, flux
// drives fine detail and mutation. Color follows a distinct
// violet -> cyan -> pink -> gold -> highlight ramp, kept dark in
// negative space.
float geo_radius = length(q);
float geo_angle = atan(q.y, q.x);

// Evolution: drift time + flux + maturity drive smooth morphing.
float geo_evolve = u_drift_time * 0.04 + flux * 0.25 + geometric_maturity * 0.15;
float geo_form = fract(geo_evolve * 0.12);

// Side count: maturity and bass pressure evolve the symmetry order.
float geo_sides = mix(
    6.0, 18.0,
    clamp(geometric_maturity * 0.5 + bass_pressure * 0.5, 0.0, 1.0)
);

// Rotation: drift time drives slow rotation, bass adds pulse.
float geo_rotation = t * (0.15 + geometric_maturity * 0.4 + bass_pressure * 0.4);
float geo_rotated = geo_angle + geo_rotation;

// Kaleidoscopic fold: mandala symmetry with quantized angular sectors.
float geo_fold = abs(
    mod(geo_rotated, 6.2832 / geo_sides) - 3.1416 / geo_sides
);

// Radial structure: bass pressure pulses the radial field.
float geo_radial = geo_radius * (1.0 - bass_pressure * 0.12);

// Crystalline facets: quantize radius into faceted rings.
float geo_facet = floor(geo_radial * geo_sides * 0.5) / (geo_sides * 0.5)
    + 1.0 / geo_sides;

// Mandala bloom: mix radial and faceted based on evolution.
float geo_mandala = mix(geo_radial, geo_facet,
    clamp(geo_form + geometric_maturity * 0.25, 0.0, 1.0)
);

// Fine crystalline detail: flux adds high-frequency structure.
float geo_detail = geometric_weight>0. ? fbm(q * (6.0 + flux * 10.0) + vec2(t * 0.3, -t * 0.2)) : 0.;
float geo_crystalline = geo_mandala * (1.0 - flux * 0.25)
    + geo_detail * flux * 0.12;

// Position: directional vector from folded angle, scaled by radius.
vec2 geo_dir = vec2(cos(geo_fold), sin(geo_fold));
vec2 geo_q = geo_dir * geo_crystalline;

// Radial offset: bass pulls structure outward for a blooming mandala.
geo_q += normalize(q + vec2(0.0001))
    * bass_pressure * geo_radius * 0.08;

q = mix(q, geo_q, geometric_weight * (1.0 - geo_gather));

// Color: distinct violet -> cyan -> pink -> gold -> highlight ramp,
// modulated by form evolution and bass so the palette breaths with music.
float geo_color_phase = clamp(
    geo_form * 0.7 + geometric_maturity * 0.2 + bass_pressure * 0.25,
    0.0, 1.0
);
vec3 geo_dream_color = geometric_dream_palette(geo_color_phase);

    // Cosmic: radial collapse with per-cell fragmentation.
    vec2 shatter_cell = floor(q * 8.0);
    vec2 shatter_jitter = (vec2(
        hash(shatter_cell + 11.3),
        hash(shatter_cell + 3.7)
    ) - 0.5) * 0.6;
    float cosmic_camera = 0.5 + 0.5 * sin(u_drift_time * 0.008 + 0.8);
    float cosmic_zoom = mix(0.82, 1.18, cosmic_camera)
        * mix(1.0, 0.78, cosmic_maturity);
    vec2 cosmic_q = q * mix(0.32, 0.18, cosmic_maturity) * cosmic_zoom
        + shatter_jitter;
    q = mix(q, cosmic_q, cosmic_weight);

    // Compression correction: cosmic collapse and the fractal fold
    // both shrink q toward the origin; left alone, every field below
    // samples the same tiny neighborhood and the screen floods into
    // one flat color. Counter-zoom back out so structure keeps
    // resolving -- "rushing into a world," not "zooming into a pixel."
    // Tunnel compression also shrinks q toward the origin; without a
    // matching counter-zoom the tunnel collapses the whole field into a
    // single flat color. Include tunnel_weight here so the zoom-out
    // keeps resolving structure even at maximum wormhole compression.
    float collapse_amount = clamp(
        cosmic_weight * mix(0.6, 1.0, cosmic_maturity)
            + fractal_weight * mix(0.35, 0.55, fractal_maturity)
            + tunnel_weight * 0.55,
        0.0, 1.0
    );
    q *= mix(1.0, 3.4, collapse_amount);

    if (shared_spatial()) {
        // Restore presentation as well as coordinates. Zeroing these weights
        // silenced the old crystal palette/eye and let Organic cover the result.
        vec3 spatial=spatial_weights();
        tunnel_weight=spatial.x;
        fractal_weight=spatial.y;
        horizon_weight=spatial.z;
        fractal_maturity=smoothstep(.25,.95,fractal_weight);
        total_transform=tunnel_weight+fractal_weight+horizon_weight
            +geometric_weight+cosmic_weight;
        organic_weight=max(organic_floor,1.-total_transform);
        weight_sum=max(organic_weight+total_transform,1.);
    }

    float n = fbm(q * 2.4 * u_scale + vec2(t, -t * 0.7));

    // Fractal/Recursive: flux warps the field back into itself.
    vec2 recursive_offset = vec2(n, n * 0.7) * (0.6 + flux * 1.4);
    float n_recursive = fbm(
        q * 2.4 * u_scale
        + recursive_offset
        + vec2(t, -t * 0.7)
    );
    n = mix(n, n_recursive, flux * 0.6);

    // Flowing wave structures.
    float waves =
        sin(q.x * 5.0 + n * 5.0 - t * 2.0) *
        cos(q.y * 4.0 - n * 4.0 + t);
    float crunch = sin(q.x * 13.0 + n * 8.0 - t * 2.5) *
        cos(q.y * 11.0 - n * 7.0 + t * 1.7);

    // Radial form. Angle feeds the impact-driven shard faceting below;
    // the tunnel/fractal/geometric/cosmic transforms already happened
    // upstream on q itself, so this now reads the transformed space.
    radius = length(q);
    float angle = atan(q.y, q.x);
    float ring = sin(
        radius * (18.0 - bass_pressure * 1.5)
        - t * 3.0
        + n * 6.0
    );

    // Hard Form: impact briefly resolves the ring into faceted, angular
    // shard bands, relaxing back to the smooth sinusoid as it decays.
    float wedge = 6.2832 / 7.0;
    float folded_angle = abs(mod(angle + t * 0.1, wedge) - wedge * 0.5);
    float ring_hard = sign(ring) * pow(abs(ring), 0.35)
        * (0.7 + 0.3 * cos(folded_angle * 24.0));
    ring = mix(ring, ring_hard, impact * 0.75);

    // Combine the structures.
    // Crunch/turbulence responds to physical bass pressure and to
    // spectral flux (change), not to loudness alone.
    // Tunnel fracture: during strong wormhole compression the field
    // would otherwise flatten into a uniform gradient. A radial/angular
    // interference pattern gated by tunnel_weight keeps edge structure,
    // contrast, and depth visible even at the near-point.
    float tunnel_fracture = sin(radius * 26.0 - u_drift_time * 14.0)
        * cos(atan(q.y, q.x) * 6.0 + u_drift_time * 7.0);
    float field = n * 0.65
        + waves * (0.22 + pressure * 0.08)
        + ring * 0.13
        + crunch * (pressure * 0.6 + flux * 0.4) * 0.10
        + tunnel_fracture * tunnel_weight * 0.16;

    // The center/"eye" is one place in the world, not the whole
    // world: its focal point wanders between hashed waypoints instead
    // of tracing a fixed circular orbit, so it never reads as
    // predictable; a strong kick can pull it toward a new position
    // outright instead of waiting for the slow drift.
    float focus_phase = u_drift_time * 0.045 + kick_trigger * 3.0;
    float focus_seed = floor(focus_phase);
    vec2 focus_target = (vec2(
        hash(vec2(focus_seed, 11.0)),
        hash(vec2(focus_seed, 47.0))
    ) - 0.5) * 0.5;
    vec2 focus_prev = (vec2(
        hash(vec2(focus_seed - 1.0, 11.0)),
        hash(vec2(focus_seed - 1.0, 47.0))
    ) - 0.5) * 0.5;
    vec2 focus_drift = mix(
        focus_prev, focus_target, smoothstep(0.0, 1.0, fract(focus_phase))
    ) * clamp(1.0 - tunnel_weight * 0.6, 0.0, 1.0);
    vec2 focus_q = q - focus_drift * (1.0 - horizon_weight);
    float fractal_spotlight = clamp(
        fractal_weight * (0.4 + fractal_maturity * 0.6), 0.0, 1.0
    );
    float glow_strength = clamp(
        1.0 - horizon_weight * 0.6 - fractal_spotlight * 0.35, 0.25, 1.0
    );

    // Open aperture: the eye breathes open/closed on a slow, non-
    // repeating cycle (dwell + bass + kick) rather than sitting as a
    // permanent bullseye. Its boundary is an asymmetric, rippling
    // ring, not a hard timer, so it never reads as an obvious preset.
    float eye_breathe = dwell(u_drift_time * 0.047 + 2.1);
    // During strong tunnel compression the eye would clamp shut and
    // leave the screen with no focal contrast. Keep the aperture
    // partially open so a rim and interior gradient survive.
    float eye_open = clamp(
        eye_breathe * 0.55 + bass_pressure * 0.4 + kick_trigger * 0.35
            + tunnel_weight * 0.5,
        0.0, 1.0
    );
    vec2 eye_shape_q = focus_q;
    eye_shape_q.x *= 1.0 + 0.22 * sin(u_drift_time * 0.083);
    eye_shape_q.y *= 1.0 - 0.18 * cos(u_drift_time * 0.061 + 1.0);
    float eye_ripple = 0.08 * (0.4 + eye_open) * sin(
        atan(eye_shape_q.y, eye_shape_q.x) * 5.0
            + u_drift_time * 0.7 + flux * 4.0
    );
    float eye_radius_norm = length(eye_shape_q) + eye_ripple;
    float aperture_radius = mix(0.10, 0.50, eye_open);
    float eye_dissolve = noise(eye_shape_q * 3.0 + u_drift_time * 0.05);
    float aperture_rim = exp(
        -pow(abs(eye_radius_norm - aperture_radius) * 6.0, 2.0)
    ) * mix(1.0, eye_dissolve, 0.4) * (0.7 + 0.3 * sparkle);
    float eye_interior = smoothstep(aperture_radius, 0.0, eye_radius_norm);

    // Soft center illumination: a bright rim plus a much softer
    // residual glow, so the interior reveals structure and gradient
    // instead of flooding into one flat value.
    float glow = (aperture_rim * 0.85 + eye_interior * 0.22)
        * glow_strength;
    float aura_ripple = 0.5 + 0.5 * sin(
        radius * 46.0 + n * 9.0 - t * 4.0
    );
    float aura_detail = pow(aura_ripple, 12.0)
        * smoothstep(0.10, 0.55, radius)
        * exp(-radius * 1.2)
        * sparkle
        * (1.0 - fractal_spotlight * 0.35);

    // Palette family: which coherent color ecosystem is active follows
    // the same slow visual state as the geometry, never a rainbow cycle.
    float tonal_light = clamp(
        0.16 + field * 0.24 + glow * 0.72,
        0.0,
        1.0
    );
    float body_value = pow(clamp(
        tonal_light + bass_pressure * 0.12 + flux * 0.15,
        0.0,
        1.0
    ), 1.15);

    // Preserve local structure: fine, decorrelated noise keeps some
    // texels dark/foundation even during a broad bloom, so color
    // stains the world instead of flattening it into one uniform
    // value -- oil paint on canvas, not a colored fullscreen filter.
    float texture_variation = noise(
        q * 7.0 + vec2(n * 3.0, -n_recursive * 3.0)
    );
    body_value = clamp(
        body_value * mix(0.65, 1.05, texture_variation), 0.0, 1.0
    );

    // Ink-pool structure: a second, much lower-frequency field that
    // carves slow-moving dark currents and bright pools into the
    // color itself -- depth and current in the empty space, not just
    // fine grain, so a broad field never reads as one flat rectangle.
    float ink_pool = fbm(q * 1.1 + vec2(-t * 0.4, t * 0.25));
    float ink_shade = mix(0.55, 1.2, ink_pool);

    // Organic/home color slowly drifts through a wheel of related
    // palettes over several minutes -- gradual, never a hard cut, and
    // never a rainbow sweep since each stop is a curated ecosystem.
    // Distance is over-scaled and re-curved so most of the time is
    // spent solidly inside one saturated family rather than a muddy
    // blend of two neighbors -- less grey/brown in-between averaging.
    float wheel = fract(u_drift_time * 0.0028) * 6.0;
    float wheel_wrap = pow(clamp(1.0 - abs(wheel - 0.0) * 1.4, 0.0, 1.0), 1.6)
        + pow(clamp(1.0 - abs(wheel - 6.0) * 1.4, 0.0, 1.0), 1.6);
    float wheel_b = pow(clamp(1.0 - abs(wheel - 1.0) * 1.4, 0.0, 1.0), 1.6);
    float wheel_c = pow(clamp(1.0 - abs(wheel - 2.0) * 1.4, 0.0, 1.0), 1.6);
    float wheel_d = pow(clamp(1.0 - abs(wheel - 3.0) * 1.4, 0.0, 1.0), 1.6);
    float wheel_e = pow(clamp(1.0 - abs(wheel - 4.0) * 1.4, 0.0, 1.0), 1.6);
    float wheel_f = pow(clamp(1.0 - abs(wheel - 5.0) * 1.4, 0.0, 1.0), 1.6);
    float wheel_sum = max(
        wheel_wrap + wheel_b + wheel_c + wheel_d + wheel_e + wheel_f, 0.0001
    );

    vec3 organic_color = (
        aurora_palette(body_value) * wheel_wrap
        + lavender_pearl_palette(body_value) * wheel_b
        + electric_blue_palette(body_value) * wheel_c
        + teal_amber_palette(body_value) * wheel_d
        + fire_palette(body_value) * wheel_e
        + gold_sun_palette(body_value) * wheel_f
    ) / wheel_sum;

    // Bass is the Heart: strong physical pressure temporarily stains the
    // home color toward crimson/gold. Impact reuses its own existing
    // decay envelope (u_impact), so the stain blooms and is gradually
    // absorbed rather than cutting -- an approximation of persistence
    // without a real frame-history buffer.
    float stain_amount = clamp(pressure * 0.8 + impact * 0.6, 0.0, 1.0);
    organic_color = mix(
        organic_color,
        crimson_gold_palette(body_value),
        stain_amount
    );

    vec3 color = (
        organic_color * organic_weight
        + ocean_palette(body_value) * tunnel_weight
        + crystal_palette(body_value) * fractal_weight
        + mix(geo_dream_color, organic_color, geo_gather) * geometric_weight
        + ember_palette(body_value) * cosmic_weight
        + teal_amber_palette(body_value) * horizon_weight
    ) / weight_sum;


    float pigment_presence=0.;
    float spatial_glow_gain=1.;
    if (shared_spatial()) {
        vec3 weights=vec3(tunnel_weight,fractal_weight,horizon_weight);
        pigment_presence=max(weights.x,max(weights.y,weights.z));
        // Give overlapping palettes a lead instead of averaging three full
        // families into grey. Smooth phase bias resolves equal-strength holds.
        vec3 bias=.78+.22*sin(vec3(u_drift_time*.071,
            u_drift_time*.063+2.1,u_drift_time*.057+4.2));
        vec3 lead=pow(weights*bias,vec3(4.));
        float sum_lead=lead.x+lead.y+lead.z;
        if (sum_lead>0.00001) {
            vec3 pigment=(ocean_palette(body_value)*lead.x
                +crystal_palette(body_value)*lead.y
                +teal_amber_palette(body_value)*lead.z)/sum_lead;
            color=mix(color,pigment,pigment_presence*.88);
        }
        // Keep pathway light local when another spatial form already leads.
        spatial_glow_gain=1./(1.+1.4*(tunnel_weight+fractal_weight));
    }

    // Horizon glow: a warm light band along the horizon line itself,
    // plus faint converging depth bands -- reads as a path stretching
    // away rather than a flat backdrop. Richer/more atmospheric the
    // longer the horizon state has matured.
    float horizon_line = exp(-abs(q.y) * (3.0 - horizon_maturity * 1.2))
        * horizon_weight;
    float horizon_bands = pow(
        0.5 + 0.5 * sin(
            radius * 10.0 - u_drift_time * (1.2 + horizon_maturity * 0.6)
        ),
        3.0
    ) * horizon_weight * (0.3 + horizon_maturity * 0.25);
    color += teal_amber_palette(0.85) * horizon_line
        * (0.5 + horizon_maturity * 0.4) * spatial_glow_gain;
    color += (shared_spatial() ? teal_amber_palette(.68) : vec3(.90,.80,.60))
        * horizon_bands * spatial_glow_gain;

    // Eye interior: a flowing taffy gradient revealed as the aperture
    // opens -- color flows through the geometry rather than replacing
    // it, twisting via the same fractal fields (n/n_recursive) that
    // already drive the rest of the world.
    float taffy_mix = 0.5 + 0.5 * sin(n * 4.0 + n_recursive * 3.0 + t * 0.6);
    vec3 taffy_a = electric_blue_palette(clamp(body_value + 0.18, 0.0, 1.0));
    vec3 taffy_b = crimson_gold_palette(clamp(body_value + 0.12, 0.0, 1.0));
    vec3 eye_taffy = mix(taffy_a, taffy_b, taffy_mix);
    eye_taffy = mix(eye_taffy, neon_forest_palette(body_value), flux * 0.35);
    color = mix(color, eye_taffy, eye_interior * eye_open * 0.6);

    vec3 impact_accent = vec3(1.0, 0.45, 0.18);
    color = mix(color, impact_accent, impact * 0.25);

    float white_highlight = smoothstep(0.88, 1.0, tonal_light)
        * (0.12 + bass_pressure * 0.08);
    color = mix(color, vec3(1.0), white_highlight);

    // Add depth-like illumination. Baseline nudged up and the eye's
    // own contribution reduced so midtones get room to breathe
    // without a flat global brightness multiplier doing the work.
    color *= (0.42 + glow * 0.75) * u_intensity;
    color *= ink_shade;

    // Subtle flowing brightness.
    color += vec3(0.06) * pow(max(field, 0.0), 2.0);
    // Sparkle drives a pale/white localized highlight, not a hue shift.
    vec3 aura_pale = vec3(0.86, 0.97, 1.00);
    vec3 aura_color = mix(
        vec3(0.08, 0.16, 0.24),
        aura_pale,
        0.35 + sparkle * 0.35
    );
    color += aura_color * aura_detail;

    if (pigment_presence>0.) {
        // Restore pigment contrast after the field lighting, before materials:
        // no changes to Living, Alloy, Lattice, stars, or their highlight colors.
        float pigment_peak=max(color.r,max(color.g,color.b));
        vec3 vivid=pow(max(color,vec3(0.))/max(pigment_peak,.0001),vec3(1.38))
            *pigment_peak*1.12;
        color=mix(color,vivid,pigment_presence);
    }

    // Stars share the same coordinate deformation as the field, so they
    // feel embedded in the universe rather than pasted over it.
    // World-coordinate travel is removed above only to keep handoffs stable.
    // Restore one shared conveyor AFTER the world warps: its speed comes from
    // the existing integrated audio clock and cannot accelerate with blend age.
    vec2 material_travel = directed ? vec2(.06,.30)*u_time : vec2(0.);
    vec2 star_space = q * (5.0 + bass_pressure * 5.0) + material_travel*5.;
    vec2 star_stretch = mix(
        vec2(1.0),
        vec2(0.3, 2.8),
        clamp(tunnel_weight + flux * 0.6, 0.0, 1.0)
    );
    star_space *= star_stretch;

    vec2 star_cell = floor(star_space);
    vec2 star_local = fract(star_space) - 0.5;
    star_local += shockwave * 0.5 * normalize(star_local + 0.0001);

    float star_hash = hash(star_cell);
    float star_size = (0.02 + 0.05 * star_hash)
        * (1.0 + cosmic_weight * 2.5);
    float star_mask = smoothstep(star_size, 0.0, length(star_local))
        * step(0.85, star_hash);

    vec3 material_before_effects = color;
    color += (u_fx_sparkles_on==1 ? u_fx_sparkles : vec3(0.86, 0.97, 1.00)) * star_mask * effect(2)
        * (0.18 * cosmic_weight + sparkle * (0.8 + cosmic_weight * 0.8))
        * (1.0-water_takeover);

    vec3 before_artifacts = color;

    vec3 material_mix=selected_materials()*(1.-u_echo_weave);
    float new_weight=dot(u_new_materials,vec3(1.));
    if(new_weight>0.) material_mix=selected_materials()*max(0.,1.-u_echo_weave-new_weight);
    bool sibling_replace=material_mix.y+material_mix.z+u_echo_weave+new_weight>0.;
    if(material_mix.x>0. || !sibling_replace) {
    // Secondary morphology variation: slowly-evolving parameters that
    // let the living artifacts drift between different structural
    // families (blobs, petals, rings, shards, eyes, lattice) without
    // hard-coded states. Each stream samples a different noise
    // coordinate so they evolve independently; slowly enough to
    // feel stable, slowly enough to surprise.
    float secondary_morph = noise(vec2(u_drift_time * 0.012, 1.0));
    float secondary_density = noise(vec2(u_drift_time * 0.009, 3.0));
    float secondary_spin = noise(vec2(u_drift_time * 0.011, 5.0));
    float secondary_focal = noise(vec2(u_drift_time * 0.008, 7.0));

    // Living artifacts: sparse procedural droplets/shards/sparks
    // embedded in the same transformed space, so tunnel/fractal/
    // geometric/cosmic states drag, fold, and scatter them naturally
    // rather than pasting a generic particle system on top.
    vec2 art_space = q * (3.2 + bass_pressure * 1.6);
    // Water stretches the existing forms into submerged streaks of dye.
    art_space *= mix(vec2(1.0),vec2(0.22,1.8),water_takeover);
    art_space += material_travel*4.;
    vec2 art_cell = floor(art_space);
    vec2 art_local = fract(art_space) - 0.5;

    float art_seed = hash(art_cell + 5.2);
    float sparkle_reveal = smoothstep(0.65, 1.0, sparkle);
    // Presence threshold lowered during tunnel compression so
    // secondary structure persists when the macro field collapses
    // toward a pinpoint -- residual artifacts provide edge and
    // contrast even inside the wormhole.
    float art_presence = step(
        0.90 - any_maturity * 0.08 - sparkle_reveal * 0.10
            - tunnel_weight * 0.14,
        art_seed
    );

    // A close waterfall magnifies source cells. Fade at their boundaries so
    // inherited colored shapes cannot pop across the entire falling sheet.
    float fall_cell_edge = min(0.5-abs(art_local.x),0.5-abs(art_local.y));
    float fall_threshold = 0.90-any_maturity*.08-sparkle_reveal*.10-tunnel_weight*.14;
    float waterfall_art_presence = smoothstep(fall_threshold-.025,fall_threshold+.025,art_seed)
        * smoothstep(0.0,0.18,fall_cell_edge);
    art_presence = mix(art_presence,waterfall_art_presence,water_takeover*forms.w);

    float art_life_phase = fract(
        u_drift_time * (0.05 + art_seed * 0.12) + art_seed * 7.0
    );
    float art_life = max(sin(art_life_phase * 3.14159), 0.0);

    art_local -= normalize(art_local + 0.0001) * pressure * 0.25;

    float art_stretch = clamp(flux * 1.2 + tunnel_weight, 0.0, 1.0);
    art_local.x *= mix(1.0, 0.35, art_stretch);
    art_local.y *= mix(1.0, 2.2, art_stretch);

    // Shape family: the base angular facet modulation is extended
    // with a continuously-evolving morphological parameter so cells
    // drift between petal, ring, shard, and eye forms rather than
    // repeating the same blob. All variation is continuous -- no
    // hard-coded states.
    float art_jag = clamp(impact * 0.6 + geometric_weight * 0.5, 0.0, 1.0);
    float art_petals = mix(2.0, 9.0,
        fract(art_seed + secondary_morph * 0.6)
    );
    float art_rotation = secondary_spin * 6.2832;
    float art_facet = cos(
        atan(art_local.y, art_local.x) * mix(1.0, 6.0, art_jag) * art_petals
            + art_seed * 6.2832 + art_rotation
    );
    // Radial/ring modulation: a second concentric structure layer
    // adds orbital-band character, strength driven by secondary_density.
    float art_ring = cos(length(art_local) * 16.0
        + secondary_morph * 3.0 + t * 0.4)
        * secondary_density * 0.25;
    art_facet = mix(art_facet, art_facet + art_ring, 0.35);

    // Scale variation: secondary_density modulates size so artifact
    // density and scale drift together over time.
    float art_size = (0.09 + hash(art_cell + 2.1) * 0.10)
        * (0.4 + art_life * 0.9)
        * (0.85 + secondary_density * 0.40);
    float art_dist = length(art_local) - art_facet * art_jag * 0.03;
    float art_mask = smoothstep(art_size, art_size * 0.15, art_dist)
        * art_presence * art_life;

    float art_pick = hash(art_cell + 9.9) * 6.0;
    vec3 art_color;
    if (art_pick < 1.0)
    {
        art_color = ocean_palette(0.78);
    }
    else if (art_pick < 2.0)
    {
        art_color = crimson_gold_palette(0.82);
    }
    else if (art_pick < 3.0)
    {
        art_color = crystal_palette(0.84);
    }
    else if (art_pick < 4.0)
    {
        art_color = fire_palette(0.80);
    }
    else if (art_pick < 5.0)
    {
        art_color = neon_forest_palette(0.82);
    }
    else
    {
        art_color = electric_blue_palette(0.85);
    }
    if(u_material_artifacts_on==1)
        art_color*=u_material_artifacts[int(clamp(floor(art_pick),0.,5.))];

    color += art_color * art_mask * effect(1) * (0.55 + sparkle * 0.55
        + tunnel_weight * 0.35);

    // Secondary edge highlight: a concentrated candy accent on
    // artifact edges, driven by the generative morph stream so the
    // accent varies independently across time and cells. Keeps the
    // existing palette picker and adds a bright rim rather than
    // flooding the frame.
    float art_edge = smoothstep(art_size, art_size * 0.35, art_dist)
        - art_mask;
    vec3 art_accent = geometric_dream_palette(
        clamp(secondary_morph * 0.5 + art_seed + 0.3, 0.0, 1.0)
    );
    if(u_material_artifacts_on==1)art_accent*=u_material_artifacts[6];
    color += art_accent * art_edge * effect(1) * (0.35 + geometric_weight * 0.30)
        * (1.0-water_takeover*.80);

    }
    vec3 sibling_delta=vec3(0.);
    if(material_mix.y+material_mix.z+u_echo_weave+new_weight>0.) {
        vec3 living=color-before_artifacts;
        vec3 siblings=vec3(0.);
        // Authored playback retains its original stable sphere source.
        // Shared spatial playback carries every material through the same folds.
        float stable_domain=directed ? max(cosmic_takeover,1.-fractal_weight*.65) : max(cosmic_takeover,u_layer_mode==2
            ? smoothstep(.08,.40,fractal_weight+tunnel_weight+horizon_weight) : 0.);
        vec2 sibling_q=(shared_spatial() ? q : mix(q,fractal_domain,stable_domain))+material_travel;
        if(material_mix.y>0.) siblings+=liquid_alloy(sibling_q,bass_pressure,flux,sparkle,impact)*material_mix.y;
        if(material_mix.z>0.) siblings+=prismatic_lattice(sibling_q,bass_pressure,flux,sparkle,impact)*material_mix.z;
        if(u_echo_weave>0.) siblings+=echo_material(sibling_q)*u_echo_weave;
        if(u_new_materials.x>0.) siblings+=ink_archipelago(sibling_q,bass_pressure,flux,sparkle)*u_new_materials.x;
        if(u_new_materials.y>0.) siblings+=interference_silk(sibling_q,bass_pressure,flux,sparkle)*u_new_materials.y;
        if(u_new_materials.z>0.) siblings+=cellular_mosaic(sibling_q,bass_pressure,flux,sparkle)*u_new_materials.z;
        sibling_delta=siblings-living*(1.-material_mix.x);
    }
    vec3 fire_material = material_before_effects + color - before_artifacts;
    if(material_mix.y+material_mix.z+u_echo_weave+new_weight>0.) fire_material+=sibling_delta;

    // Falling/drifting world elements: unlocked strongly by the
    // horizon state, but audio decides what populates it -- highs for
    // fine rain, flux for turbulent drift, impact for a bigger burst.
    // A small floor keeps a sparse residual drifting even in quiet.
    // Falls through the SAME transformed q, so it bends/tunnels/
    // recoils with the rest of the world instead of sitting on top.
    float fall_amount = clamp(
        0.05 + horizon_weight * 1.3 + sparkle * 0.4 + flux * 0.35,
        0.0, 1.4
    );
    vec2 fall_space = q * (4.0 + bass_pressure * 2.0);
    fall_space.y += u_drift_time * (0.6 + sparkle * 1.2);
    fall_space.x += sin(u_drift_time * 0.3 + fall_space.y * 0.4) * flux * 0.4;

    vec2 fall_cell = floor(fall_space);
    vec2 fall_local = fract(fall_space) - 0.5;
    float fall_seed = hash(fall_cell + 17.4);
    float fall_presence = step(
        0.86 - fall_amount * 0.10 - horizon_maturity * 0.05, fall_seed
    );

    float fall_size = 0.05 + hash(fall_cell + 6.6) * 0.06
        + impact * 0.03 + horizon_maturity * 0.02;
    float fall_dist = length(fall_local * vec2(1.0, 1.0 + sparkle * 1.5));
    float fall_mask = smoothstep(fall_size, fall_size * 0.2, fall_dist)
        * fall_presence * clamp(fall_amount, 0.0, 1.0);

    float fall_pick = hash(fall_cell + 22.1) * 6.0;
    vec3 fall_color;
    if (fall_pick < 1.0)
    {
        fall_color = ocean_palette(0.7 + fall_seed * 0.15);
    }
    else if (fall_pick < 2.0)
    {
        fall_color = crimson_gold_palette(0.7 + fall_seed * 0.15);
    }
    else if (fall_pick < 3.0)
    {
        fall_color = crystal_palette(0.7 + fall_seed * 0.15);
    }
    else if (fall_pick < 4.0)
    {
        fall_color = fire_palette(0.7 + fall_seed * 0.15);
    }
    else if (fall_pick < 5.0)
    {
        fall_color = neon_forest_palette(0.7 + fall_seed * 0.15);
    }
    else
    {
        fall_color = gold_sun_palette(0.7 + fall_seed * 0.15);
    }
    if(u_fx_flecks_on==1)fall_color*=u_fx_flecks[int(clamp(floor(fall_pick),0.,5.))];

    color += fall_color * fall_mask * effect(4) * (0.5 + sparkle * 0.5)
        * (1.0-water_takeover);

    // Colored streak/laser events: sparse, temporary, radiating from
    // the core, gated by musical events rather than a constant grid.
    float laser_slots = 5.0;
    float laser_slot = floor(
        mod(angle + 3.1416, 6.2832) / (6.2832 / laser_slots)
    );
    float laser_seed = hash(vec2(laser_slot, 41.7));
    float laser_phase = fract(
        u_drift_time * (0.04 + laser_seed * 0.05) + laser_seed * 3.0
    );
    float laser_pulse = smoothstep(0.0, 0.08, laser_phase)
        * smoothstep(0.22, 0.08, laser_phase);
    float laser_trigger = clamp(
        impact * 1.2 + flux * 0.5 + sparkle * 0.3, 0.0, 1.0
    );
    float laser_center = (laser_slot + 0.5) * (6.2832 / laser_slots)
        - 3.1416;
    float laser_delta = abs(atan(
        sin(angle - laser_center), cos(angle - laser_center)
    ));
    float laser_width = 0.05 + 0.03 * laser_seed;
    float laser_mask = smoothstep(laser_width, 0.0, laser_delta)
        * laser_pulse * laser_trigger
        * smoothstep(0.0, 0.15, radius) * exp(-radius * 0.8);

    float laser_pick = laser_seed * 4.0;
    vec3 laser_color;
    if (laser_pick < 1.0)
    {
        laser_color = ocean_palette(0.9);
    }
    else if (laser_pick < 2.0)
    {
        laser_color = crimson_gold_palette(0.9);
    }
    else if (laser_pick < 3.0)
    {
        laser_color = electric_blue_palette(0.9);
    }
    else
    {
        laser_color = fire_palette(0.9);
    }
    if(u_fx_beams_on==1)laser_color*=u_fx_beams[int(clamp(floor(laser_pick),0.,3.))];
    color += laser_color * laser_mask * effect(8) * 1.4 * (1.0-water_takeover);

    vec3 material_effects = color - material_before_effects;
    if(material_mix.y+material_mix.z+u_echo_weave+new_weight>0.) {
        material_effects+=sibling_delta;
        color+=sibling_delta;
    }

    // Organic membrane: its own connected folds in the pre-scroll domain.
    // Slow deformation preserves the form while bass changes its physical
    // tension and highs reveal fine ridges. Other states keep their image.
    vec2 membrane_q = fractal_domain * (2.2 + bass_pressure * 0.25);
    float membrane_time = t * 0.35;
    vec2 membrane_warp = vec2(
        fbm(membrane_q + vec2(membrane_time, 2.7)),
        fbm(membrane_q + vec2(5.3, -membrane_time * 0.8))
    );
    vec2 membrane_space = membrane_q + (membrane_warp - 0.5) * 1.8;
    // Musical change flexes the surface locally without accelerating its
    // clock. Quiet inputs preserve the accepted resting shape exactly.
    float membrane_activity = smoothstep(0.08, 0.65, flux);
    float membrane_event = smoothstep(0.10, 0.65, impact);
    vec2 membrane_gesture = vec2(
        sin(membrane_space.y * 3.2 - t * 1.3),
        cos(membrane_space.x * 2.8 + t * 1.1)
    );
    membrane_space += membrane_gesture * membrane_activity * 0.16;
    float membrane_phase = membrane_space.y * 5.0
        + sin(membrane_space.x * 2.5 + membrane_time) * 2.0
        + fbm(membrane_space * 1.7) * 3.0;
    membrane_phase += sin(length(membrane_q) * 8.0 - t * 2.0)
        * membrane_event * 0.35;
    float membrane_fold = 0.5 + 0.5 * sin(membrane_phase);
    float membrane_body = smoothstep(0.22, 0.78, membrane_fold);
    float membrane_ridge = pow(max(0.0, 1.0 - abs(membrane_fold - 0.72) * 7.0), 3.0);
    // One Organic form replaces another gradually, rather than stacking light.
    // Dwelling lets both the broad membrane and the roots hold their identity.
    float root_mix = directed ? u_root_mix : dwell(u_drift_time * 0.04 - 1.8);
    if (u_debug_state > 10.5 && u_debug_state < 11.5) root_mix = 0.0;
    if (u_debug_state > 11.5 && u_debug_state < 12.5) root_mix = 1.0;
    vec2 root_position = membrane_space * 0.85;
    float root_distance = root_network(root_position, membrane_time, membrane_activity);
    float root_aa = max(fwidth(root_distance), 0.001);
    float root_body = 1.0 - smoothstep(-root_aa, root_aa, root_distance);
    float root_ridge = exp(-abs(root_distance) * 65.0) * root_body;
    membrane_body = mix(membrane_body, root_body, root_mix);
    membrane_ridge = mix(membrane_ridge, root_ridge, root_mix);
    float membrane_value = clamp(0.12 + membrane_body * 0.55
        + membrane_ridge * 0.18, 0.0, 1.0);
    vec3 membrane_color = mix(
        electric_blue_palette(membrane_value),
        lavender_pearl_palette(membrane_value),
        smoothstep(0.25, 0.75, membrane_warp.x)
    );
    if ((roots_color_scope() && (u_roots_blue_on == 1 || u_roots_pearl_on == 1)) ||
        (membrane_color_scope() && (u_membrane_blue_on == 1 || u_membrane_pearl_on == 1))) {
        float pearl_blend = smoothstep(0.25, 0.75, membrane_warp.x);
        vec3 blue = electric_blue_palette(membrane_value);
        vec3 pearl = lavender_pearl_palette(membrane_value);
        vec3 roots_shading = mix(
            roots_color_scope() && u_roots_blue_on == 1 ? roots_color_gradient(membrane_value, u_roots_blue, u_roots_blue_ranges) : blue,
            roots_color_scope() && u_roots_pearl_on == 1 ? roots_color_gradient(membrane_value, u_roots_pearl, u_roots_pearl_ranges) : pearl,
            pearl_blend);
        vec3 membrane_shading = mix(
            membrane_color_scope() && u_membrane_blue_on == 1 ? roots_color_gradient(membrane_value, u_membrane_blue, u_membrane_blue_ranges) : blue,
            membrane_color_scope() && u_membrane_pearl_on == 1 ? roots_color_gradient(membrane_value, u_membrane_pearl, u_membrane_pearl_ranges) : pearl,
            pearl_blend);
        membrane_color = mix(membrane_shading, roots_shading, root_mix);
    }
    membrane_color *= 0.25 + membrane_body * 0.75;
    membrane_color += vec3(0.18, 0.50, 0.55) * membrane_ridge
        * (0.15 + sparkle * 0.35 + impact * 0.15);
    if (roots_color_scope() && u_roots_ridge_on == 1)
        membrane_color += (u_roots_ridge - vec3(0.18, 0.50, 0.55)) * root_mix * membrane_ridge
            * (0.15 + sparkle * 0.35 + impact * 0.15);
    if (membrane_color_scope() && u_membrane_ridge_on == 1)
        membrane_color += (u_membrane_ridge - vec3(0.18, 0.50, 0.55)) * (1.0 - root_mix) * membrane_ridge
            * (0.15 + sparkle * 0.35 + impact * 0.15);
    // Blossoms have a small internal lifecycle: bud, open bloom, and a
    // quiet return. Root continuity remains intact while the flowers breathe.
    float blossom_cycle = 0.5 + 0.5 * sin(membrane_time * 0.12 + 1.4);
    float blossom_life = smoothstep(0.18, 0.38, blossom_cycle)
        * (1.0 - smoothstep(0.78, 0.96, blossom_cycle));
    float blossom = blossom_field(root_position, membrane_time)
        * root_mix * blossom_life
        * (0.35 + sparkle * 0.35 + impact * 0.30);
    membrane_color += vec3(0.95, 0.42, 0.62) * blossom * effect(128);
    if (roots_color_scope() && u_roots_blossoms_on == 1)
        membrane_color += (u_roots_blossoms - vec3(0.95, 0.42, 0.62)) * blossom * effect(128);
    color = mix(color, membrane_color * u_intensity, (organic_weight / weight_sum)*(1.0-water_takeover));
    // Explicit custom layers remain visible on the held Organic material too.
    // Authored mode keeps the accepted Organic substitution unchanged.
    if (u_layer_mode != 0)
        color += material_effects * (organic_weight / weight_sum) * (1.0-water_takeover);


    // Oil-paint tonemap: compress extreme brightness toward the
    // palette's saturated colors instead of collapsing into white.
    float peak = max(color.r, max(color.g, color.b));
    color = color / (1.0 + peak * 0.6);

    vec3 shared_canvas = color; // Planet retains its accepted pigment response.
    vec3 expressive_canvas = musical_material(color);
    color = mix(color,expressive_canvas,1.-cosmic_takeover);
    // Geometry keeps absolute weights; normalize only the background compositing.
    vec4 background_mix=u_world_mix/max(1.-u_air_weight-u_earth_weight-u_fog_weight-u_plasma_weight,.000001);
    vec4 coverage = directed ? world_coverage(background_mix,screen_p) : u_world_mix;
    float front=handoff_front(screen_p);
    bool physical_handoff=directed && u_handoff.x>.5;
    if(physical_handoff && u_handoff.x<1.5) coverage.w=handoff_share(4.,front);
    if (geometric_weight > 0.0)
    {
        float geo_canvas = 0.85 + 0.15 * clamp(u_flux, 0.0, 1.0);
        vec3 geo_world = isolated_geometric_scene(geo_surface, color, geo_canvas);
        float amount = directed ? coverage.x/max(1.-coverage.z-coverage.y-coverage.w,.000001) : geometric_weight;
        color = mix(color, geo_world, clamp(amount,0.,1.));
    }
    if (cosmic_takeover > 0.0)
    {
        vec3 world = isolated_cosmic_scene(cosmic_p, directed ? shared_canvas : color, 1.0, cosmic_takeover);
        float amount = directed ? coverage.y/max(1.-coverage.z-coverage.w,.000001) : cosmic_takeover;
        color = mix(color, world, clamp(amount,0.,1.));
    }
    if (water_mode && handoff_share(3.,front)>0.) {
        float liquid_currents;
        vec4 liquid_forms=water_coverage(screen_p,liquid_currents);
        vec3 liquid = isolated_water_scene(water, directed ? expressive_canvas : color,liquid_forms,liquid_currents);
        if (forms.w > 0.0) liquid = mix(liquid,water_falls(falls,directed ? expressive_canvas : color),liquid_forms.w);
        float amount = directed ? coverage.z/max(1.-coverage.w,.000001) : water_takeover;
        if(physical_handoff && u_handoff.x<1.5) amount=1.;
        color = mix(color,liquid,clamp(amount,0.,1.));
    }
    if (fire_mode && handoff_share(4.,front)>0.) {
        float molten=molten_weight(), wild=firescape_weight();
        vec3 before_fire=color;
        vec4 weights=directed ? u_fire_mix : (u_debug_state>17.5 ? vec4(0,0,0,1)
            : vec4(max(0.,1.-molten-wild),molten,wild,0.));
        weights=fire_coverage(weights,screen_p);
        color=vec3(0.);
        if(weights.x>0.) color+=isolated_fire_scene(screen_p,fire_material)*weights.x;
        if(weights.y>0.) color+=isolated_molten_scene(screen_p,fire_material)*weights.y;
        if(weights.z>0.) color+=isolated_firescape_scene(screen_p,fire_material)*weights.z;
        if(weights.w>0.) color+=isolated_aftershock_scene(screen_p,fire_material)*weights.w;
        if (directed) color=mix(before_fire,color,coverage.w);
    }
    float air_amount=directed ? u_air_weight/max(1.-u_earth_weight-u_fog_weight-u_plasma_weight,.000001) : (held_air ? 1. : 0.);
    if(air_amount>0. && handoff_share(5.,front)>0.) {
        vec4 af=air_forms();
        vec4 regions=air_coverage(screen_p,af);
        vec3 sky=vec3(0.);
        // Each physical scene retains its own camera/depth while regions meld.
        if(af.x>0.)sky+=air_scene(screen_p,expressive_canvas,vec4(1,0,0,0))*regions.x;
        if(af.y>0.)sky+=air_scene(screen_p,expressive_canvas,vec4(0,1,0,0))*regions.y;
        if(af.z>0.)sky+=air_scene(screen_p,expressive_canvas,vec4(0,0,1,0))*regions.z;
        if(af.w>0.)sky+=air_scene(screen_p,expressive_canvas,vec4(0,0,0,1))*regions.w;
        float edge=dot(af,air_territory(screen_p));
        float score=air_amount*air_amount*air_amount*exp(edge*4.);
        float coverage=score/max(score+pow(1.-air_amount,3.),.000001);
        color=mix(color,sky,coverage);
    }
    if(earth_amount>0. && handoff_share(6.,front)>0.) {
        vec3 regions=ef*ef*ef*exp(earth_territory(screen_p)*5.);
        regions/=max(dot(regions,vec3(1.)),1e-12);
        vec3 earth=vec3(0.);
        if(ef.x>0.)earth+=earth_scene(screen_p,dune,expressive_canvas,0)*regions.x;
        if(ef.y>0.)earth+=earth_scene(screen_p,strata,expressive_canvas,1)*regions.y;
        if(ef.z>0.)earth+=earth_scene(screen_p,cavern,expressive_canvas,2)*regions.z;
        float amount=directed ? earth_amount/max(1.-u_fog_weight-u_plasma_weight,.000001) : earth_amount;
        float score=pow(amount,3.)*exp(dot(ef,earth_territory(screen_p))*4.);
        float coverage=score/max(score+pow(1.-amount,3.),1e-12);
        color=mix(color,earth,coverage);
    }
    if(fog_amount>0. && handoff_share(7.,front)>0.) {
        vec3 forms=fog_forms();
        vec3 scores=forms*forms*forms*exp(vec3(screen_p.y,-screen_p.y,.3-length(screen_p))*3.);
        scores/=max(dot(scores,vec3(1.)),1e-12);
        vec3 vapor=vec3(0.);
        for(int i=0;i<3;i++)if(forms[i]>0.)vapor+=fog_scene(screen_p,expressive_canvas,i)*scores[i];
        float amount=directed ? fog_amount/max(1.-u_plasma_weight,.000001) : fog_amount;
        float score=pow(amount,3.)*exp((.25-length(screen_p)*.4)*3.);
        float coverage=score/max(score+pow(1.-amount,3.),1e-12);
        if(physical_handoff && abs(u_handoff.x-3.)<.1) coverage=handoff_share(7.,front);
        color=mix(color,vapor,coverage);
    }
    if(plasma_amount>0. && handoff_share(8.,front)>0.) {
        vec3 forms=plasma_forms();
        vec3 scores=forms*forms*forms*exp(vec3(-screen_p.x,screen_p.x,screen_p.y)*3.);
        scores/=max(dot(scores,vec3(1.)),1e-12);
        vec3 plasma=vec3(0.);
        for(int i=0;i<3;i++)if(forms[i]>0.)plasma+=plasma_scene(screen_p,expressive_canvas,i)*scores[i];
        float score=pow(plasma_amount,3.)*exp((.4-length(screen_p))*3.);
        float coverage=score/max(score+pow(1.-plasma_amount,3.),1e-12);
        if(physical_handoff) coverage=handoff_share(8.,front);
        color=mix(color,plasma,coverage);
    }
    color += stellar_layers(screen_p);
    if(directed && u_galaxy_weight>0.) {
        float share=clamp(u_galaxy_weight,0.,1.);
        vec2 travel=screen_p*(1.+(1.-share)*(.35+.2*u_flux));
        vec3 destination=isolated_galaxy_scene(travel);
        float cover=smoothstep(.12,.55,share);
        color=mix(color*(1.-cover*.70),destination,smoothstep(.10,.85,share));
        vec4 passage=u_journey.x>4.5 ? vec4(0) : journey_warp(screen_p,max(0.,sin(share*3.14159265))*.22);
        color=color*(1.-passage.a)+passage.rgb;
    }
    return vec4(color, 1.0);
}

// Optical crossfade blends complete endpoint images after each scene's own shading.
// The loop keeps one copy of the existing scene evaluator and allocates no resources.
void main(){
    vec2 region_p=gl_FragCoord.xy/u_resolution-.5;region_p.x*=u_resolution.x/u_resolution.y;
    bool optical=u_directed==1 && u_debug_state==0. && u_main_transition.x<-.5;
    float phase=clamp(u_main_transition.y,0.,1.);
    vec4 first=vec4(0.);
    for(int pass=0;pass<2;pass++){
        main_weights(region_p);
        if(optical)main_pair_weights(phase>=1. ? 1. : float(pass));
        vec4 frame=scene_frame();
        if(pass==0)first=frame;
        else first=mix(first,frame,phase);
        if(!optical || phase<=0. || phase>=1.)break;
    }
    fragColor=first;
}
