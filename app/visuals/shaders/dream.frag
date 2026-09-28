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
uniform float u_drift_time;
uniform vec2 u_resolution;
uniform float u_intensity;
uniform float u_distortion;
uniform float u_scale;
uniform float u_sparkle;
uniform float u_impact;
uniform float u_flux;
uniform float u_debug_state;
// Optional development isolation. Zero keeps every authored expression intact.
uniform int u_layer_mode;
uniform int u_layer_mask;
uniform vec4 u_shockwaves[8];
uniform vec3 u_material_mix;
uniform float u_echo_weave;
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
uniform vec4 u_blast_events[8]; // birth, stable id, world x, world z
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
vec2 spatial_carrier(vec2 source) {
    vec3 w = spatial_weights();
    if (max(w.x,max(w.y,w.z)) <= 0.) return source;
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
    return mix(q,folded*.32,w.y*cluster);

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
        vec3 ink = mix(vec3(0.08, 0.85, 0.95), vec3(0.95, 0.08, 0.55), dye);
        float vein = pow(0.5 + 0.5 * sin(q.y * 9.0 + fold * 3.0 - drift), 8.0);
        return mix(ink, vec3(0.85, 1.0, 0.62), vein * 0.65);
    }
    if (index == 1)
    {
        float heat = 0.5 + 0.5 * sin(q.y * 7.0 + fold * 2.0 - drift * 2.0);
        vec3 flame = mix(vec3(0.95, 0.08, 0.015), vec3(1.0, 0.50, 0.04), heat);
        flame = mix(flame, vec3(0.08, 0.40, 1.0), smoothstep(0.45, 0.78, heat));
        return mix(flame, vec3(0.85, 0.96, 1.0), smoothstep(0.78, 1.0, heat));
    }
    // Moving nested shells, broad enough to remain readable on a small moon.
    float layers = length(q.xy + vec2(0.22, -0.18)) * 3.0
        + q.z * 0.35 - time * 0.10;
    return 0.52 + 0.46 * cos(6.2831853 * (layers + vec3(0.0, 0.33, 0.67)));
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
        vec3 tint=mix(vec3(.22,.65,1.),vec3(1.,.36,.12),seed);
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
            vec3 star_color = mix(vec3(0.55, 0.72, 1.0),
                vec3(1.0, 0.83, 0.62), hash(cell + 2.0));
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
    vec3 ring_color = mix(vec3(0.31, 0.19, 0.40), vec3(0.93, 0.67, 0.39),
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
    ring_color = cosmic_vivid_material(ring_color, color_drive);
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
        albedo = cosmic_vivid_material(albedo, color_drive);
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
    return mix(geo_swatch(v, slot), geo_swatch(v, slot + 1.0), fade);
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
    return tint * (body + lead * 1.4) * mask;
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
    vec3 sky = mix(vec3(0.002, 0.003, 0.009),
        mix(lavender_pearl_palette(0.32), ocean_palette(0.38), 0.55) * 0.62,
        horizon_glow);
    float dusk = exp(-pow((azimuth + 0.28) * 1.9, 2.0));
    sky += teal_amber_palette(0.50) * horizon_glow * dusk * 0.10;
    sky += ember_palette(0.61) * horizon_glow * horizon_glow * dusk * 0.14;
    // Horizontal, slowly traveling banks stay close to the horizon.
    vec2 cloud_q = vec2(azimuth * 3.0 - u_drift_time * 0.003,
        elevation * 17.0 + u_drift_time * 0.001);
    float mist = fbm(cloud_q + vec2(5.3, 1.7));
    sky += lavender_pearl_palette(0.44) * (0.15 + mist * 0.22)
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
    float facing = clamp(dot(surface.normal, surface.view), 0.0, 1.0);
    float fresnel = 0.035 + 0.70 * pow(1.0 - facing, 5.0);
    vec3 reflection = reflect(-surface.view, surface.normal);
    // Broad colored off-screen light reflected by the actual wave normals.
    // No full-screen white layer: most reflected directions see dark space.
    vec3 light = normalize(vec3(-0.25, 0.48, 0.86));
    float glint = pow(max(dot(reflection, light), 0.0), 145.0);
    float silk = pow(max(dot(reflection, light), 0.0), 32.0);
    vec3 reflected = lavender_pearl_palette(0.48) * silk * 0.48;
    reflected += mix(ocean_palette(0.80), gold_sun_palette(0.82), 0.36)
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
    scene += mix(ocean_palette(0.85), lavender_pearl_palette(0.83), 0.35)
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
        // Fine reflected ribbons keep dark channels and never form a white wash.
        current_color += mix(carried,lavender_pearl_palette(.65),.22)
            * thread*body*travel*(.25+spark*.7)*effect(65536);
        current_color += reflected*.25;
        current_color *= .82+.18*max(dot(surface.normal,surface.view),0.0);
        scene = mix(scene,current_color,clamp(currents/max(1.-forms.w,.000001),0.,1.));
    }
    if (ripple_weight > 0.0) {
        float rings = water_ripples(detail_position);
        scene += mix(ocean_palette(.75),lavender_pearl_palette(.75),.3)
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
        scene += ocean_palette(.85)*streak*rain_weight*(.12+spark*.25);
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
    liquid+=tint*(.035+body*.08);
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
        liquid+=tint*shine*(.8+spark*.6)*effect(65536);
        liquid+=water_environment(reflected)*.15;
    } else {
        // Continuous broad sheets, with broken smaller strands accelerating
        // down the face. No periodic horizontal bars or receiving basin.
        float streak=fbm(vec2(flow.x*8.0,flow.y*5.0));
        float veil=smoothstep(.25,.74,streak);
        liquid+=tint*filament*(.18+spark*.23)*(.35+veil*.85)*effect(65536);
        liquid+=tint*veil*body*(.10+flux*.16);
    }
    // Dark plateau banks and cleft cliff walls anchor the two water planes.
    vec2 rock_q=river ? vec2(pos.x*.8,path*.4) : vec2(pos.x*1.5,path*.35);
    float rock=fbm(rock_q);
    float strata=.5+.5*sin(path*2.7+rock*6.0);
    vec3 stone=mix(ocean_palette(.24),lavender_pearl_palette(.27),rock)
        *(.20+rock*.30+strata*.10);
    vec3 scene=mix(stone,liquid,water);
    // The turnover belongs to the same edge on both sides of the cliff.
    float lip=exp(-abs(path)*12.0)*water;
    scene+=tint*lip*(.16+bass*.09+spark*.10)*effect(16384);
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
        float seam=pow(ribbons,18.)*silhouette*(.10+spark*.24)
            *effect(524288);
        // Strong real onsets reach about .5. Existing envelope decay moves
        // the short white core through blue and back to the amber sheets.
        float hot=smoothstep(.12,.40,impact);
        float white=smoothstep(.40,.50,impact);
        float foot=exp(-pow((h-.085)*14.,2.))*silhouette
            *(.12+.88*ribbons*ribbons);
        vec3 ignition=mix(vec3(.025,.24,1.25),vec3(1.30,1.42,1.55),white);
        light+=ignition*foot*hot*(.52-z*.12);
        light+=sheet*silhouette*(.44-z*.10)*(.10+surge*1.35)
            +vec3(1.,.35,.08)*seam*(.12+surge);
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
        light+=vec3(1.,.40,.075)*dotlight*fade*(.015+surge*(.15+spark*.8))
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
    float center=.65*sin(ground.y*.34)+.28*sin(ground.y*.77);
    float distance=abs(ground.x-center);
    for(int i=0;i<4;i++) {
        float id=float(i);
        float split=5.-id*3.8;
        float downstream=max(0.,split-ground.y);
        float side=mod(id,2.)<.5 ? -1. : 1.;
        float spread=side*(1.-exp(-downstream*.32))*(2.4+id*.55);
        float branch=center+spread+.22*sin(downstream*.85+id)*smoothstep(0.,2.,downstream);
        float life=.5+.5*sin(u_time*.055+u_drift_time*.02+id*1.9);
        float front=1.5+life*12.;
        float growth=smoothstep(0.,.8,downstream)*(1.-smoothstep(front,front+2.,downstream));
        float width=.68*growth;
        float branch_distance=abs(ground.x-branch)+(1.10-width);
        distance=min(distance,branch_distance);
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
    vec3 sky=mix(vec3(.032,.045,.068),vec3(.065,.067,.082),
        1.-smoothstep(.26,.50,p.y));
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

vec3 isolated_molten_scene(vec2 p,vec3 canvas) {
    float bass=clamp(u_scale,0.,1.),flux=clamp(u_flux,0.,1.);
    float spark=clamp(u_sparkle,0.,1.),impact=clamp(u_impact,0.,1.);
    vec2 ground=molten_ground(p), q=molten_domain(p);
    float pressure=smoothstep(.12,.9,.55*bass+.45*flux);
    float pulse=smoothstep(.1,.55,impact);
    float width=(.58+.10*sin(ground.y*.42))*(1.+pressure*.85+pulse*.18);
    float bank=molten_channel(ground).x/width;
    float river=1.-smoothstep(.78,1.22,bank);
    // Molten folds travel with the river; banks stay fixed in ground space.
    float fold=fbm(q*vec2(3.8,2.1));
    float threads=.5+.5*sin(q.x*30.+fold*12.+q.y*1.8
        +flux*.7*sin(q.y*2.3));
    float islands=smoothstep(.38+pressure*.12,.56+pressure*.12,fold)*effect(131072);
    float liquid=river*(1.-islands*.96);
    float rock=fbm(ground*3.2);
    float height=(1.-river)*(.25+rock*.3)+islands*river*.13;
    vec3 normal=normalize(vec3(-dFdx(height)*u_resolution.y*.55,
        -dFdy(height)*u_resolution.y*.55,1.));
    float shade=.25+.75*max(0.,dot(normal,normalize(vec3(-.4,.6,1.))));
    vec3 light=vec3(.015,.017,.026)*shade*(.5+rock);
    float glow=exp(-pow((bank-1.)*2.3,2.));
    light+=vec3(.085,.011,.006)*glow*(.45+rock);
    vec3 pigment=canvas/(1.+max(canvas.r,max(canvas.g,canvas.b)));
    vec3 heat=mix(vec3(.45,.025,.004),vec3(1.05,.32,.025),threads*.65+fold*.25);
    heat=mix(heat,pigment*1.1,.22);
    light+=heat*liquid*(.30+pressure*.95+pulse*.45);
    float seams=pow(threads,10.)*liquid*(.13+spark*.23)
        +exp(-pow((fold-.48)*38.,2.))*river*(.12+pressure*.35+pulse*.55);
    light+=vec3(1.,.43,.055)*seams*effect(524288);
    // Two anchored vents brighten on impacts, leaving the transport steady.
    float vent=exp(-dot(ground-vec2(.2,-.9),ground-vec2(.2,-.9))*18.)
        +exp(-dot(ground-vec2(.35,1.2),ground-vec2(.35,1.2))*23.);
    light+=mix(vec3(.80,.15,.01),vec3(1.2,.8,.3),smoothstep(.35,.5,impact))
        *vent*river*smoothstep(.12,.48,impact)*(1.+flux*.3);
    // Sparse embers drift above the channel with a separate apparent height.
    for(int i=0;i<16;i++) {
        float seed=hash(vec2(float(i),9.3));
        float age=fract(u_drift_time*.045+seed*9.);
        vec2 pos=vec2((seed-.5)*.52,.45-age*.9);
        pos.x+=.12*sin(pos.y*8.+seed*4.);
        vec2 d=p-pos;
        float ember=exp(-dot(d*vec2(330.,220.),d*vec2(330.,220.)));
        float life=smoothstep(0.,.15,age)*(1.-smoothstep(.7,1.,age));
        light+=vec3(.9,.25,.035)*ember*life*(.2+spark*.8)*effect(262144);
    }
    vec3 terrain=1.-exp(-light*1.8);
    float distance=length(ground);
    float haze=smoothstep(15.,65.,distance)*.82;
    terrain=mix(terrain,vec3(.016,.026,.027),haze);
    float horizon=smoothstep(.185,.255,p.y);
    return mix(terrain,molten_backdrop(p),horizon);
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
    vec3 sky=vec3(.008,.010,.023);
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
    scene+=firescape_palette(hue+1.4)*city.y*.16;
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
        float glow=exp(-pow((h-.12)*2.8,2.))*.08;
        scene+=tint*(fire*veil*(.65+z*.08)+glow)*(.78+bass*.20+beat*.68);
        scene+=firescape_palette(hue+z*1.4+.6)*pow(edge,15.)*fire
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
        scene=mix(scene,bark*(1.+z*.15),forest*.96);
        scene+=firescape_palette(hue+z*1.4)*trees.y*(.25+beat*.20);
        float soil=exp(-pow((p.y-base+.018)*40.,2.));
        scene+=firescape_palette(hue+z)*soil*(.06+.12*noise(vec2(x*25.,rise*.15)))
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
            scene+=firescape_palette(hue+seed*5.)*ember*life*(.35+spark*.7+beat*.4)
                *effect(262144);
        } else {
            float ash=exp(-dot(d*vec2(150.,240.)/depth,d*vec2(150.,240.)/depth));
            scene+=vec3(.19,.20,.24)*ash*life*(.5+flux*.3)*effect(1048576);
        }
    }
    return 1.-exp(-scene*1.65);
}

// Aftershock: projected ground and layered, shaded ash volumes. Event timestamps
// preserve musical shockwaves independently of the decaying impact envelope.
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
        light+=tint*vec3(.45,.85,.9)*ribbon*pleats*.24;
    }
    return light*smoothstep(.19,.25,p.y)*effect(16777216);
}
// Stable per-site color: no shared clock can rotate all plume hues together.
vec3 blast_plume_tint(float id) {
    return .24+.76*(.5+.5*cos(vec3(0.,2.094395,4.18879)+id*2.399963+.6));
}
vec3 blast_material_negative(vec3 material) {
    // Invert the actual incoming material, before its muted soil treatment.
    return 1.-clamp(material*1.6,0.,1.);
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
    return fade*(vec3(.30,.27,.21)*dust*effect(4194304)
        +vec3(.95,.28,.035)*flame*(.4+irregular*.9)*effect(8388608));
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
    vec3 scene=mix(vec3(.045,.060,.073),vec3(.14,.125,.10),
        exp(-pow((p.y-.19)*8.,2.)));
    if(rayy<0.) {
        float terrain=noise(ground*.45)*.6+noise(ground*1.8)*.4;
        vec3 soil=vec3(.038,.032,.029)+terrain*vec3(.063,.047,.029);
        soil+=canvas*.055*min(1.,effect(1)+(u_layer_mode==0 ? 0. : effect(33554432)+effect(67108864)));
        scene=mix(vec3(.14,.125,.10),soil,haze);
        float recent=floor((clock-5.)/36.);
        for(int j=0;j<8;j++) {
            if(u_event_blasts==0 && j>=3) break;
            float id=u_event_blasts==1 ? u_blast_events[j].y : recent-float(j);
            float age=clock-blast_birth(id);
            if(id>=0.) {
                float r=length(ground-blast_site(id));
                float craterLife=u_event_blasts==1 ? 1.-smoothstep(15.,20.,age) : 1.;
                scene*=1.-.6*exp(-r*r*.7)*smoothstep(0.,2.,age)*craterLife*effect(131072);
                scene+=blast_ring(ground,id,age,1.2)*haze;
            }
        }
        for(int j=0;j<8;j++) {
            vec4 e=u_shockwaves[j];
            if(e.z>0.) scene+=blast_ring(ground,e.y,clock-e.x,e.z)*haze;
        }
    }
    scene+=blast_aurora(p,clock,camera,camx);
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
                *smoothstep(1.,4.,dz);
            vec2 local=vec2(p.x*dz*1.6+camx-site.x,(p.y*1.6-.32)*dz+6.);
            float growth=u_event_blasts==1 ? .22 : .075;
            float height=5.5*(1.-exp(-age*growth))+age*(u_event_blasts==1 ? .50 : .09);
            float width=.35+2.6*(1.-exp(-age*growth))+age*(u_event_blasts==1 ? .065 : .028);
            float stemW=(.23+.48*(1.-exp(-age*.1)))*(1.+.24*sin(local.y*4.+clock*.18));
            float bend=sin(local.y*.65+clock*.12)*.15*local.y/8.;
            float stem=exp(-pow(abs((local.x-bend)/stemW),4.))
                *smoothstep(0.,.3,local.y)*(1.-smoothstep(height-.2,height+.5,local.y));
            float unravel=1.-smoothstep(lifeEnd*.35,lifeEnd*.85,age);
            float density=stem*.85*unravel;
            float rolls=noise(local*vec2(4.,2.)-vec2(0.,clock*.25));
            vec3 cloud=mix(vec3(.085,.088,.087),vec3(.38,.32,.23),rolls)
                +vec3(.22,.075,.008)*exp(-age*.06);
            float skirt=exp(-pow(abs(local.x/(.8+width*.75)),4.)-pow((local.y-.25)/.42,2.));
            density=max(density,skirt*.65*unravel);
            for(int k=0;k<9;k++) {
                float a=float(k)*2.39996;
                vec2 center=vec2(cos(a)*width*.66,height+sin(a)*width*.18);
                vec2 q=(local-center)/vec2(width*.48,width*.36);
                float n=noise(local*2.+vec2(clock*.10,id));
                float rr=dot(q,q)+(n-.5)*.22;
                float puff=(1.-smoothstep(.70,1.05,rr))
                    *mix(.45+.55*noise(local*1.8-vec2(0.,clock*.3)),1.,unravel);
                float light=clamp(.50+.25*(-q.x+q.y)+.3*sqrt(max(0.,1.-rr)),0.,1.);
                vec3 shade=mix(vec3(.085,.09,.092),vec3(.55,.46,.31),light);
                shade+=vec3(.50,.13,.015)*exp(-age*.13)*(1.-light);
                cloud=mix(cloud,shade,puff);density=max(density,puff);
            }
            float cloudHaze=exp(-dz*.012);
            cloud*=.78+.40*noise(local*3.-vec2(0.,clock*.10));
            float luminance=dot(cloud,vec3(.2126,.7152,.0722));
            cloud=mix(cloud,luminance*blast_plume_tint(id)*1.7,.88);
            scene=mix(scene,mix(vec3(.14,.125,.10),cloud,cloudHaze),density*life);
        }
    }
    scene=1.-exp(-scene*1.5);
    // One short outward inversion per detonation, separate from musical rings.
    float id=blast_latest(clock),age=clock-blast_birth(id);
    if(id>=0. && age>=0. && age<2. && rayy<0.) {
        float front=1.-smoothstep(age*180.,age*180.+2.,length(ground-blast_site(id)));
        scene=mix(scene,blast_material_negative(canvas),front*exp(-age*1.8)*(1.-smoothstep(1.5,2.,age))*.9*effect(2097152));
    }
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
    return pigment*body*(.22+strands*1.65+ridge*.8);
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
    vec3 normal=normalize(vec3(disk.x,disk.y,sqrt(max(.01,1.-radius))));
    float reflection=.5+.5*sin(normal.y*8.+normal.x*2.5+u_time*.09);
    vec3 copper=vec3(.75,.28,.10),teal=vec3(.08,.58,.62),violet=vec3(.44,.12,.72);
    vec3 tint=mix(copper,teal,smoothstep(.25,.75,reflection));
    tint=mix(tint,violet,.5+.5*sin(seed*8.+normal.x*2.));
    vec3 object_tint=.08+.92*(.5+.5*cos(vec3(0.,2.094,4.188)
        +seed*19.+normal.y*.65+.32*sin(u_time*.16+seed*9.)));
    tint=mix(tint,object_tint,.85);
    float glint=pow(reflection,18.)*(.22+sparkle*.3);
    float rim=pow(1.-max(0.,normal.z),4.);
    vec3 chrome=vec3(.08,.10,.14)+tint*(.2+reflection*.55)
        +vec3(.65,.82,.9)*(glint+rim*.2);
    chrome*=.8+.2*max(0.,normal.y)+impact*.12;
    float resolved=1.-smoothstep(.10,.35,length(fwidth(space)));
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
    float aa=max(length(fwidth(space))*.6,.003);
    float wire=1.-smoothstep(.006,.006+aa,edge);
    float glow=exp(-edge*65.)*(.08+sparkle*.12);
    vec3 tint=.2+.8*(.5+.5*cos(vec3(0.,2.094,4.188)+seed*6.28+local.y*2.));
    float presence=smoothstep(.30,.48,seed);
    float resolved=1.-smoothstep(.10,.35,length(fwidth(space)));
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
        vec2 center=i<4 ? vec2((i%2==0 ? -1. : 1.)*.48,(i<2 ? -1. : 1.)*.48)
            : (i<6 ? vec2((i==4 ? -1. : 1.)*.23,-.49) : vec2(0.,.13));
        float h=i==6 ? .94 : (i<4 ? .62 : .72);
        float rad=i==6 ? .20 : .125;
        vec3 q=p-vec3(center.x,0.,center.y);
        float cylinder=max(length(q.xz)-rad,abs(q.y-h*.5)-h*.5);
        d=min(d,cylinder);
        // Cap with ring parapet and discrete merlons, not a flat printed roof.
        float ring=max(abs(length(q.xz)-rad)-.022,abs(q.y-h)-.035);
        float toothAngle=floor(atan(q.z,q.x)/.62831853+.5)*.62831853;
        vec2 toothAxis=vec2(cos(toothAngle),sin(toothAngle));
        float merlon=air_box(vec3(dot(q.xz,toothAxis)-rad,q.y-h-.065,
            dot(q.xz,vec2(-toothAxis.y,toothAxis.x))),vec3(.028,.03,.030));
        if(i<6)d=min(d,min(ring,merlon));
        if(i==6) {
            float cone=max(length(q.xz)-.235*(1.-clamp((q.y-h)/.40,0.,1.)),abs(q.y-h-.2)-.2);
            roof=min(roof,cone*.8);
        }
    }
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
    vec2 q=p-vec2(0.,.035);
    float orbit=.35+u_time*.045+u_drift_time*.007;
    float approach=2.8+.20*sin(u_drift_time*.055);
    vec3 ro=vec3(approach*sin(orbit),1.35+.08*sin(clock*.23),-approach*cos(orbit));
    vec3 fw=normalize(vec3(0.,.36,0.)-ro),right=normalize(cross(fw,vec3(0,1,0))),up=cross(right,fw);
    vec3 rd=normalize(fw+right*q.x*1.13+up*(q.y-.09)*1.13);
    float surfaceDepth=100.;
    // Castle and attached island participate in the same depth trace.
    // Conservative ray/box rejection only: retained rays keep the exact trace.
    // Bounds include the island displacement, tower merlons and central cone.
    vec3 safeRay=vec3(rd.x<0. ? -max(abs(rd.x),1e-8) : max(abs(rd.x),1e-8),
        rd.y<0. ? -max(abs(rd.y),1e-8) : max(abs(rd.y),1e-8),
        rd.z<0. ? -max(abs(rd.z),1e-8) : max(abs(rd.z),1e-8));
    vec3 slabA=(vec3(-1.1,-.6,-1.1)-ro)/safeRay;
    vec3 slabB=(vec3(1.1,1.4,1.1)-ro)/safeRay;
    vec3 entry=min(slabA,slabB),leave=max(slabA,slabB);
    float nearBox=max(entry.x,max(entry.y,entry.z));
    float farBox=min(leave.x,min(leave.y,leave.z));
    if(abs(q.x)<.82 && q.y>-.52 && q.y<.68 && farBox>=max(1.2,nearBox) && nearBox<4.9) {
        float t=1.2;vec2 hit=vec2(1.,0.);vec3 pos=ro;
        for(int j=0;j<144;j++) {
            pos=ro+rd*t;hit=air_castle_map(pos);
            if(hit.x<.0008 || t>4.9)break;
            t+=max(.00035,hit.x*.50);
        }
        if(t<4.9 && hit.x<.0008) {
            surfaceDepth=t;
            vec2 e=vec2(.002,0.);
            vec3 normal=normalize(vec3(air_castle_map(pos+e.xyy).x-air_castle_map(pos-e.xyy).x,
                air_castle_map(pos+e.yxy).x-air_castle_map(pos-e.yxy).x,
                air_castle_map(pos+e.yyx).x-air_castle_map(pos-e.yyx).x));
            vec3 light=normalize(vec3(-.5,1.,-.8));
            float diffuse=max(0.,dot(normal,light));
            vec2 uv=abs(normal.x)>.6 ? pos.zy : pos.xy;
            vec2 brick=vec2(uv.x*18.+floor(uv.y*24.)*.5,uv.y*24.);
            vec2 brickAA=clamp(fwidth(uv*vec2(18.,24.)),vec2(.015),vec2(.35));
            float mortar=smoothstep(.06-brickAA.y,.06+brickAA.y,fract(brick.y))
                *smoothstep(.045-brickAA.x,.045+brickAA.x,fract(brick.x));
            vec3 stone=mix(vec3(.32,.28,.37),vec3(.48,.43,.51),mortar);
            float weathering=fbm(uv*35.);
            stone*=.78+.30*weathering;
            float courses=1.-smoothstep(.025,.055,abs(fract(pos.y*8.)-.5));
            stone+=vec3(.055,.045,.07)*courses;
            if(hit.y>1.5)stone=hit.y<2.5 ? vec3(.06,.36,.39) : vec3(.26,.13,.07);
            if(hit.y>2.5 && hit.y<3.5)stone*=.35+.65*step(.13,fract(pos.x*45.))*step(.14,fract(pos.y*18.));
            if(hit.y>3.5)stone=mix(vec3(.07,.055,.045),vec3(.27,.20,.12),.5+.5*sin(pos.y*55.+fbm(pos.xz*7.)*5.));
            if(hit.y>3.5 && pos.y>-.02)stone=vec3(.08,.16,.09);
            vec3 color=stone*(.36+.64*diffuse);
            // Recess shading under parapets and at the wall foot, without new meshes.
            color*=.78+.22*smoothstep(.0,.10,pos.y);
            if(hit.y<1.5)color*=.83+.17*smoothstep(.0,.06,abs(pos.y-.56));
            vec2 windowAA=clamp(fwidth(uv*12.),vec2(.01),vec2(.30));
            vec2 windowCell=fract(uv*12.);
            float windows=smoothstep(.81-windowAA.x,.81+windowAA.x,windowCell.x)
                *smoothstep(.68-windowAA.y,.68+windowAA.y,windowCell.y)
                *(1.-smoothstep(1.-windowAA.x,1.,windowCell.x))
                *(1.-smoothstep(1.-windowAA.y,1.,windowCell.y))*step(.12,pos.y)*step(pos.y,.63);
            float windowWave=floor(uv.y*12.)*.055+sin(uv.x*3.-clock*.8)*.16+clock*.12;
            if(hit.y<1.5)color+=air_palette(windowWave+.025*sin(floor(uv.x*12.)*7.))*windows*(.24+u_scale*.65)*(1.-abs(normal.y));
            if(hit.y>1.5 && hit.y<2.5) {
                float azimuth=atan(pos.z-.13,pos.x);
                float enamel=.5+.5*sin(azimuth*6.+pos.y*19.-clock*3.);
                float tracery=pow(enamel,10.);
                color=mix(color,air_palette(azimuth*.16+pos.y*.7-clock*.12)*(.25+.3*diffuse),.55);
                color+=air_palette(pos.y*.8+clock*.2)*tracery*(.18+.7*u_scale+.5*u_impact);
            }
            color+=vec3(.10,.25,.35)*pow(max(0.,dot(reflect(-light,normal),-rd)),24.);
            sky=mix(sky,color,amount);
        }
    }
    // True world-space tower emitters. Closest ray/beam depth handles occlusion.
    for(int i=0;i<8;i++) {
        float id=float(i),scan=clock*2.3+sin(clock*.7)*1.8+floor(id*.5)*1.3;
        vec3 emitter=vec3((i%2==0 ? -1. : 1.)*.48,.73,(i%4<2 ? -1. : 1.)*.48);
        float fan=(mod(id,2.)-.5)*(.10+.28*(.5+.5*sin(clock*.9)));
        vec3 direction=normalize(vec3(sin(scan+fan),.30+.70*(.5+.5*sin(scan*.8+fan)),cos(scan+fan)));
        vec3 w=ro-emitter;float crossTerm=dot(rd,direction),den=max(.0001,1.-crossTerm*crossTerm);
        float along=(dot(direction,w)-crossTerm*dot(rd,w))/den;
        float depth=along*crossTerm-dot(rd,w);
        vec3 beamPoint=emitter+direction*max(0.,along);
        float distance=length(ro+rd*depth-beamPoint);
        float width=.007+max(0.,along)*.0015;
        float beam=exp(-distance*distance/(width*width));
        float visible=step(0.,along)*step(0.,depth)*step(depth,surfaceDepth-.006);
        if(beam>.002 && visible>0.) {
            float march=.02;
            for(int k=0;k<24;k++) {
                if(march>=along || march>3.)break;
                float obstruction=air_castle_map(emitter+direction*march).x;
                if(obstruction<.002){visible=0.;break;}
                march+=max(.005,obstruction*.7);
            }
        }
        float pulse=(.08+.92*pow(.5+.5*sin(clock*17.+floor(id*.5)*2.),4.))
            *smoothstep(-.6,.4,sin(clock*.65+floor(id*.5)*1.7));
        sky+=air_palette(id*.12+clock*.08)*beam*visible*pulse*(.2+u_scale*.8+u_impact*.6)*amount;
    }
    // Chrysanthemum bursts with segmented ballistic willow tails and falling sparks.
    for(int i=0;i<6;i++) {
        float id=float(i),cycle=u_time*(.095+.006*id)+id*.67,phase=fract(cycle),serial=floor(cycle);
        float age=clamp((phase-.28)/.72,0.,1.);
        vec2 origin=vec2(sin(id*13.+serial*2.3)*.70,.13+.23*fract(sin(id*3.+serial)*437.));
        // Comet ascends from a tower before opening into its burst.
        vec3 launchWorld=vec3((i%2==0 ? -1. : 1.)*.48,.73,(i<3 ? -1. : 1.)*.48);
        vec3 launchView=launchWorld-ro;
        vec2 launch=vec2(dot(launchView,right),dot(launchView,up))/max(.1,dot(launchView,fw))/1.13+vec2(0.,.125);
        float ascent=clamp(phase/.28,0.,1.);
        vec2 head=mix(launch,origin,ascent),tail=mix(launch,origin,max(0.,ascent-.23));
        if(phase<.28 && surfaceDepth>dot(launchView,rd))
            sky+=vec3(.7,.8,1.)*air_line(p,head,tail,.0022)*(.4+ascent)*amount;
        float celebration=.35+.65*smoothstep(.15,.75,max(u_scale,u_flux));
        vec3 tint=mix(air_palette(id*.21+serial*.13),vec3(1.,.61,.20),mod(id,2.)*.7);
        sky+=mix(tint,vec3(1.),.55)*exp(-length(p-origin)*180.)
            *exp(-age*40.)*step(.28,phase)*celebration*amount*step(6.,surfaceDepth);
        // No trails before ignition or behind the castle. The ballistic bound
        // includes secondary branches plus a generous .10 glow margin; outside
        // it even the slowest exponential tail is below display precision.
        float burstRadius=.62*age+.18*age*age+.10;
        if(age>0. && surfaceDepth>=6. && length(p-origin)<burstRadius)
        for(int k=0;k<24;k++) {
            float a=float(k)*2.399963+id,rad=.18+.13*fract(sin(float(k)*7.+id)*437.);
            vec2 velocity=vec2(cos(a),sin(a))*rad;
            float tail=0.;
            float life=.58+.42*fract(sin(float(k)*13.+serial)*417.);
            for(int seg=0;seg<3;seg++) {
                float u=max(0.,age-float(seg)*.065),v=max(0.,u-.065);
                vec2 pa=origin+velocity*u*2.-vec2(0.,u*u*.18);
                vec2 pb=origin+velocity*v*2.-vec2(0.,v*v*.18);
                tail+=air_line(p,pa,pb,.0018)*(1.-float(seg)*.20);
            }
            float fade=smoothstep(.01,.06,age)*(1.-smoothstep(life*.6,life,age));
            vec2 tip=origin+velocity*age*2.-vec2(0.,age*age*.18);
            float ember=exp(-length(p-tip)*650.)*(.4+.6*pow(.5+.5*sin(age*75.+float(k)),3.));
            // Late secondary sparks split from selected tips and fall independently.
            float splitAge=max(0.,age-.38);
            vec2 splitOrigin=origin+velocity*.76-vec2(0.,.38*.38*.18);
            vec2 splitDirection=vec2(-velocity.y,velocity.x)*(.45+.3*sin(float(k)*9.));
            vec2 splitTip=splitOrigin+(velocity+splitDirection)*splitAge-vec2(0.,splitAge*splitAge*.26);
            float branch=air_line(p,splitTip,splitTip-(velocity+splitDirection)*.06,.0012)
                *smoothstep(.38,.44,age)*step(.5,fract(float(k)*.381));
            sky+=tint*(tail+ember+branch*.7)*fade*(.32+u_sparkle*.45+u_impact*.35)*celebration*amount*step(6.,surfaceDepth);
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
    vec3 sky=mix(vec3(.025,.038,.12),vec3(.27,.37,.48),clamp(.6-p.y,0.,1.));
    sky=mix(sky,vec3(.008,.012,.034),weather*.83+citadel*.6);
    sky+=storm*vec3(.035,.055,.10)*(.4+.6*fbm(p*5.+vec2(0.,clock*.2)));
    // Sparse high-altitude stars remain anchored as the lower atmosphere moves.
    vec2 starUV=p+vec2(clock*.024,.015*sin(clock*.3));
    vec2 starCell=floor(starUV*220.);
    float starSeed=fract(sin(dot(starCell,vec2(127.1,311.7)))*43758.5453);
    float star=exp(-dot(fract(starUV*220.)-.5,fract(starUV*220.)-.5)*140.)*step(.992,starSeed);
    sky+=vec3(.25,.36,.50)*star*citadel*(.5+u_sparkle*.5);
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
        sky=mix(sky,farms,exp(-distance*.016)*mix(1.-smoothstep(18.,45.,distance),1.,vortex)*(1.-vortex*.9)*(1.-citadel)*(1.-storm));
    }
    // The planet is specific to the Citadel scene; existing Planet Canvas stays intact.
    vec2 planet=(p-vec2(0.,-5.18))/5.;
    float disk=dot(planet,planet);
    if(citadel>0.) {
        float limb=exp(-pow((sqrt(disk)-1.)*380.,2.));
        sky+=vec3(.07,.36,.9)*limb*citadel;
        if(disk<1.) {
            vec3 n=vec3(planet,sqrt(1.-disk));
            float continents=fbm(n.xy*6.+vec2(clock*.09,n.z));
            vec3 land=mix(vec3(.015,.04,.13),cosmic_vivid_material(material,energy)*1.7,.94);
            float clouds=smoothstep(.50,.7,fbm(n.xy*13.+clock*.07));
            land=mix(land,vec3(.29,.43,.53),clouds*.16);
            sky=mix(sky,land*(.42+.58*max(0.,dot(n,normalize(vec3(-.4,.6,1.))))),citadel);
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
            sky=mix(sky,tint,mask*(.60+.18*n)*form.x*effect(134217728));
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
                cloud+=mix(vec3(.02,.45,.32),vec3(.40,.035,.48),.5+.5*sin(uv.y*.7+clock*.15))*curtain*(.35+energy*.5)
                    *smoothstep(.2,.8,sin(uv.y));
            }
            float wall=step(.5,corridor.kind)*(1.-step(1.5,corridor.kind));
            float ceiling=step(2.5,corridor.kind);
            float fog=exp(-corridor.distance*.055);
            float cloudEdge=1.-smoothstep(7.,10.,corridor.distance);
            float coverage=(wall+ceiling)*cloudEdge*effect(134217728);
            sky=mix(sky,mix(vec3(.09,.12,.19),cloud,fog),coverage*storm);
            sky+=light*fog*storm*(wall+ceiling)*cloudEdge;
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
            sky=mix(sky,cloud,banks*vortex*effect(134217728));
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
                    vec3 tint=air_palette(clock*.09+id*.23+strand*.075);
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
                web+=air_palette(clock*.09+id*.23)*exp(-length(tunnel-hub)*190.)*.55;
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
                vec3 tint=air_palette(serial*.19+life*.22+id*.3);
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
                vec3 tint=air_palette(serial*.23+life*.28+.12);
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
                sky+=(vec3(.25,.52,1.)*(bolt+fork*.85+split*.7)+vec3(.18,.08,.35)*coil*.18)*flash*vortex;
                // Bolts keep their own paths; a wider residue follows the spiral surface.
                float residue=exp(-abs(sin(theta+log(radius+.03)*2.-a)) * 9.)
                    *banks*(.25+.75*pow(rib,3.));
                sky+=air_palette(id*.17+seed*.07)*residue*u_air_afterglow*.30*vortex*effect(536870912);
                for(int j=0;j<3;j++) {
                    vec2 trail=u_air_trails[j];
                    float oldAngle=id*1.57+trail.x*.73;
                    float wake=exp(-abs(sin(theta+log(radius+.03)*2.-oldAngle))*7.)
                        *banks*(.25+.75*pow(rib,3.));
                    sky+=air_palette(id*.17+trail.x*.07)*wake*trail.y*.16*vortex*effect(536870912);
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
            sky+=mix(air_palette(id*.09+clock*.02),pigment,.3)*stripe*pulses
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
            vec3 fabric=air_palette(serial*.13+pattern*.9+clock*.11+.18*sin(inward))*(.22+.78*sqrt(max(0.,1.-r*r)));
            fabric+=vec3(.25,.20,.14)*pow(max(0.,1.-length(q-vec2(-.28,.30))),12.);
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
vec2 cavern_formation(vec3 p,vec2 cell) {
    vec2 local=p.xz-(cell+.5)*2.8;
    // Placement belongs to a stable cell, not the query point or music clock.
    float axis=1.1*sin((cell.y+.5)*2.8*.075);
    vec2 result=vec2(100.,0.);
    float seed=hash(cell+31.);
    vec2 offset=(vec2(hash(cell+2.),hash(cell+9.))-.5)*.65;
    float centerX=(cell.x+.5)*2.8;
    // Limestone grows down from the ceiling as well as up from the floor.
    float roof=.6+sqrt(max(.1,19.36-pow((centerX-axis)*.80,2.)))+.18;
    vec2 stal=local-offset;
    float down=roof-p.y,hanging=.45+pow(hash(cell+47.),1.4)*2.6;
    stal+=vec2(.12*sin(seed*19.),.10*cos(seed*31.))*down;
    float stalRadius=(.22+.55*hash(cell+14.))*pow(clamp(1.-down/hanging,0.,1.),1.5);
    float stalactite=max(length(stal)-stalRadius,max(-down-2.,down-hanging))*.50;
    if(seed>.16 && stalactite<result.x)result=vec2(stalactite,2.5);
    if(abs(centerX-axis)>1.1) {
        for(int i=0;i<3;i++) {
            float id=float(i),a=seed*6.283+id*2.1;
            vec2 q=local-vec2(cos(a),sin(a))*.17*id-offset;
            q=mat2(cos(a),sin(a),-sin(a),cos(a))*q;
            float individual=hash(cell+id*17.+63.);
            float h=.55+pow(individual,.7)*3.1, y=p.y+2.5;
            q+=vec2(sin(a*3.),cos(a*2.))*.05*y;
            q+=vec2(sin(u_time*1.4+seed*9.),cos(u_time*1.1+seed*11.))*.025*u_flux*y;
            float rad=(.16+.38*hash(cell+id+82.))*min(1.,max(0.,(h-y)/(.55+seed*.3)));
            float hex=max(abs(q.x)*.866025+abs(q.y)*.5,abs(q.y));
            // Quartz needles, blocky fluorite and limestone have different profiles.
            if(seed>.66)hex=max(abs(q.x),abs(q.y));
            if(seed<.27) {
                rad=(.22+.43*individual)*pow(clamp(1.-y/h,0.,1.),1.4);
                hex=length(q)+.012*sin(y*18.+a);
            }
            float crystal=max(hex-rad,max(-y,y-h))*.52;
            if(individual>.18 && crystal<result.x)result=vec2(crystal,seed<.27 ? 2.5 : 1.+seed);
        }
    }
    return result;
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
    float axis=1.1*sin(p.z*.075)+.16*sin(p.z*.27+u_time*.12);
    float shell=(4.4-length(vec2((p.x-axis)*.80,p.y-.6))
        +.18*sin(p.z*.7+p.y*1.6)*sin(p.x*1.7))*.52;
    vec2 result=vec2(min(shell,p.y+2.5),0.);
    vec2 cell=floor(p.xz/2.8);
    // Neighboring formations can protrude across a cell edge. Evaluate them
    // consistently for both tracing and normals; otherwise surfaces get sliced.
    vec2 local=p.xz-(cell+.5)*2.8;
    vec2 side=step(vec2(0.),local)*2.-1.;
    // Only four cells can overlap this point. Bound travel toward the omitted
    // cells so the marcher cannot leap over their protruding formations.
    float omittedBound=(2.8+min(abs(local.x),abs(local.y))-1.85)*.35;
    result.x=min(result.x,omittedBound);
    for(int z=0;z<2;z++) for(int x=0;x<2;x++) {
        vec2 neighbor=cell+vec2(x,z)*side;
        vec2 bounds=abs(p.xz-(neighbor+.5)*2.8)-vec2(1.85);
        float lowerBound=max(max(bounds.x,bounds.y),0.)*.35;
        if(lowerBound>result.x)continue;
        vec2 candidate=cavern_formation(p,neighbor);
        if(candidate.x<result.x) result=candidate;
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
        ro.x=1.1*sin(travel*.075)+.16*sin(travel*.27+u_time*.12);ro.y=.1;
        direction=normalize(vec3(.0825*cos(travel*.075)+.0432*cos(travel*.27+u_time*.12),.03,1.));
    }
    vec3 right=normalize(cross(vec3(0,1,0),direction)),up=cross(direction,right);
    float bank=.06*sin(travel*.075)*(1.+u_flux*1.6);
    p=mat2(cos(bank),sin(bank),-sin(bank),cos(bank))*p;
    vec3 ray=normalize(direction+right*p.x*1.45+up*p.y*1.45);
    float t=.04;vec2 hit=vec2(1.,0.);
    for(int i=0;i<128;i++) {
        hit=earth_map(ro+ray*t,form);
        if(hit.x<.003+.0006*t || t>55.)break;
        t+=clamp(hit.x,.003,1.4);
    }
    vec3 pos=ro+ray*t,normal=vec3(0,1,0);
    if(t<=55. && hit.x<.003+.0006*t) {
        float e=.006;
        normal=normalize(vec3(earth_map(pos+vec3(e,0,0),form).x-earth_map(pos-vec3(e,0,0),form).x,
            earth_map(pos+vec3(0,e,0),form).x-earth_map(pos-vec3(0,e,0),form).x,
            earth_map(pos+vec3(0,0,e),form).x-earth_map(pos-vec3(0,0,e),form).x));
    } else t=100.;
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
    vec3 sky=mix(fog,vec3(.018,.028,.085),smoothstep(-.1,.5,p.y));
    if(form==0) {
        float sunset=exp(-length((p-vec2(-.48,.22))*vec2(1.,1.2))*6.);
        sky+=vec3(.65,.20,.075)*sunset;
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
        sky=mix(sky,cloudColor,wisps*.65);
        vec2 starGrid=dome*vec2(180.,120.)+vec2(u_star_time*.12,u_star_time*.035);
        vec2 starCell=floor(starGrid),starLocal=fract(starGrid)-.5;
        float starSeed=fract(sin(dot(starCell,vec2(12.9898,78.233)))*43758.5453);
        float star=exp(-dot(starLocal,starLocal)*100.)*step(.974,starSeed);
        sky+=mix(vec3(.42,.62,.90),vec3(.90,.66,.40),starSeed)*star
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
            sky+=aurora*ribbon*(.30+.65*energy+.40*u_impact)*(1.-wisps*.5);
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
            stone=mix(vec3(.20,.055,.09),vec3(.88,.42,.13),.3+.7*light);
            stone*=1.-u_earth_details.x*.19*(1.-ripples)*smoothstep(.12,.65,n.y);
        } else if(form==1) {
            stone=mix(vec3(.17,.055,.11),vec3(.58,.27,.13),sediment*u_earth_details.x);
            stone=mix(stone,vec3(.07,.25,.31),pow(1.-sediment,5.)*.55*u_earth_details.x);
        } else {
            stone=mix(vec3(.14,.17,.21),vec3(.25,.28,.32),sediment*.5*u_earth_details.x);
            if(surface.kind>.5 && surface.kind<2.) {
                vec3 ore=.5+.5*cos(vec3(0.,2.1,4.2)+floor(surface.kind*17.)*2.3);
                stone=.055+ore*.55;
            } else if(surface.kind>2.) {
                stone=mix(vec3(.16,.12,.10),vec3(.38,.30,.20),bedding*.3+.3);
            }
        }
        if(form==0 && surface.kind>2.) {
            float armor=pow(.5+.5*cos(q.z*14.+q.x*3.),5.);
            stone=mix(vec3(.12,.22,.29),vec3(.32,.52,.59),armor*.3+.4);
        }
        // Pigment is lit with the solid surface; only narrow mineral seams emit.
        float pigment=form==0 ? .16 : form==1 ? .20 : .22;
        stone=mix(stone,stone*(.75+clamp(material,0.,1.)*.5),pigment*vein);
        if(shared_spatial())stone*=.82+clamp(material,0.,1.)*.48;
        if(form==0 && surface.kind>2.)stone=vec3(.10,.17,.23)+material*1.5;
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
            vec3 eye=vec3(1.1*sin(travel*.075)+.16*sin(travel*.27+u_time*.12),.1,travel);
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
        color+=mix(mineral,clamp(material,0.,1.),.4)*vein*u_earth_details.y*(.04+.32*energy+1.05*u_impact)*(.3+.7*traveling)*contact;
        if(form==2 && surface.kind>.5 && surface.kind<2.) {
            float glow=(.08+.38*energy+1.15*u_impact)*(.3+.7*traveling)*u_earth_details.y;
            color+=stone*glow;
            color+=vec3(.32,.55,.65)*pow(light,18.)*(.3+u_sparkle)*u_earth_details.y;
        }
        // Tiny mineral glints use world coordinates, never a screen overlay.
        vec3 glitter=q*18.;
        vec3 cell=floor(glitter),local=fract(glitter)-.5;
        float fleck=pow(max(0.,1.-min(min(length(local.xy),length(local.yz)),length(local.xz))*3.),3.);
        // Bound the hash input so long travel does not lose fractional precision.
        float seed=hash(mod(cell.xy+cell.z*19.,127.));
        float twinkle=pow(.5+.5*sin(clock*2.+seed*71.),8.);
        color+=vec3(.22,.39,.48)*fleck*step(.96,seed)*(.12+twinkle*(.3+u_sparkle*1.5))*u_earth_details.z;
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
vec3 fog_lamp(float cell,float side) {
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
        float width=.35+seed*.40;
        // Every marker has an arched crown and a thin headstone profile.
        float cap=length(vec2(q.x,max(0.,p.y+1.4-height+width)))-width;
        float rock=max(max(cap,abs(q.z)-(.16+seed*.23)),-p.y-1.5);
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
    vec3 stone=mix(vec3(.25,.30,.32),vec3(.34,.25,.36),seed);
    stone*=.75+.35*grain;
    stone=mix(stone,vec3(.08,.14,.17),vein*.7);
    // Fixed vein/crack coordinates; only their weathering coverage grows.
    float age=1.-exp(-max(0.,u_drift_time)*.012-seed*.4);
    float moss=smoothstep(.43,.68,grain)*
        (1.-smoothstep(.20+age*.85,.75+age*1.1,q.y));
    stone=mix(stone,vec3(.075,.19,.095)*(.7+grain*.6),moss*.85);
    float stem=abs(q.x+.13*sin(q.y*8.+seed*9.)+.12*sin(q.y*3.));
    float branch=abs(q.x-.43*(q.y-.7)+.08*sin(q.y*14.+seed*5.));
    float cracks=1.-smoothstep(.008,.022,min(stem,branch));
    cracks*=1.-smoothstep(age*2.8,age*2.8+.18,q.y);
    stone*=1.-cracks*.8*smoothstep(.12,.45,age);
    return stone*light*(.8+.30*u_scale+.35*u_impact);
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
    vec3 background=form==1 ? vec3(.013,.023,.035) : vec3(.006,.010,.025);
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
            background=vec3(.12,.16,.18)*light*(.8+.30*u_scale+.35*u_impact);
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
                    background+=mix(vec3(.14,.50,.32),vec3(.55,.28,.10),float(i))*reflection*fog_lamp_light(id,side)*u_fog_details.y;
                }
            } else if(hit.y>1.5) {
                float cell=floor(q.z/8.),side=q.x<0. ? -1. : 1.;
                background=mix(vec3(.20,.65,.40),vec3(.65,.30,.08),step(0.,q.x))*fog_lamp_light(cell,side)*1.7;
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
        vec3 pigment=fog_palette(phase,form);
        // Material colors enter the scattering volume, not an extra transparent layer.
        pigment=mix(pigment,pigment*(.70+clamp(material,0.,1.)*.8),.18);
        float forwardLight=pow(max(0.,dot(ray,normalize(vec3(-.3,.3,1.)))),6.);
        vec3 lighting=pigment*(.22+rim+forwardLight*.45);
        float thread=pow(.5+.5*sin(fog_billows(q*1.8)*11.+phase-u_time),8.);
        lighting+=pigment*thread*(.08+.30*u_sparkle+.60*u_impact)*u_fog_details.z;
        if(form==1) {
            float cell=floor(q.z/8.);
            for(int j=-1;j<=1;j++)for(int k=0;k<2;k++) {
                float id=cell+float(j),side=k==0 ? -1. : 1.;
                float d=length(q-fog_lamp(id,side));
                lighting+=mix(vec3(.25,.90,.50),vec3(.75,.35,.12),float(k))*exp(-d*.95)*fog_lamp_light(id,side)*2.2*u_fog_details.y;
            }
        } else {
            float pulse=pow(.5+.5*sin(q.z*.65-u_time*2.+q.y),5.);
            lighting+=pigment*pulse*(.14+.65*energy+1.3*u_impact)*u_fog_details.y;
        }
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
            light+=hue*(point+halo)*(.35+.45*u_sparkle+.25*u_impact)*twinkle*(1.-depth*.35);
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
            light+=hue*(exp(-points*points/.00015)*(.5+.5*u_sparkle)
                +exp(-line*line/.000045)*charge);
        }
    }
    return light;
}
vec3 plasma_loop(float f,float id) {
    float theta=mix(.43,2.71159,f),az=id*.7853982;
    float stretch=1.9+.20*sin(id*2.1+u_time*.19)+u_scale*.30;
    float radius=stretch*sin(theta)*sin(theta);
    az+=.24*sin(theta*3.+u_time*.4+id)*(.3+u_flux);
    return vec3(radius*sin(theta)*cos(az),radius*cos(theta),radius*sin(theta)*sin(az));
}
vec3 plasma_node(float id) {
    float phase=id*.897598+u_time*(.07+.012*sin(id));
    return vec3(cos(phase)*(1.65+.22*u_scale),sin(phase*1.37+id)*.95,
        sin(phase)*1.25);
}
vec3 plasma_scene(vec2 p,vec3 material,int form) {
    float energy=clamp(.5*u_scale+.5*u_flux,0.,1.);
    vec3 ray=normalize(vec3(p,1.35));
    vec3 color=vec3(.003,.005,.014)+plasma_stars(p,form)*u_plasma_details.z;
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
            vec3 emission=hue*pigment*(.5+energy*.65+u_sparkle*threads*.35);
            emission+=hue*wave*(.25+u_impact*2.)*u_plasma_details.y;
            sum+=transmission*(1.-through)*emission;
            transmission*=through;
        }
        return color*transmission+sum;
    }
    float solidDepth=100.;vec3 solidCenter=vec3(0.);float solidId=0.;
    for(int i=0;i<7;i++) {
        if(form==0 && i>0)break;
        vec3 center=plasma_view(form==0 ? vec3(0.) : plasma_node(float(i)));
        float radius=form==0 ? .48+.035*u_scale : .10+.035*plasma_seed(vec2(i,3.));
        float depth=plasma_sphere(ray,center,radius);
        if(depth<solidDepth) {solidDepth=depth;solidCenter=center;solidId=float(i);}
    }
    if(solidDepth<99.) {
        vec3 n=normalize(ray*solidDepth-solidCenter);
        float shade=.20+.80*max(0.,dot(n,normalize(vec3(-.6,.7,-.8))));
        float bands=.5+.5*sin(n.y*17.+n.x*6.+sin(n.z*9.+n.x*5.)+u_time*.55);
        vec3 body=plasma_tint(solidId*.7+u_time*.09+n.y*2.);
        color=body*pigment*(.12+.12*bands)*shade;
        float rim=pow(1.-max(0.,dot(n,-ray)),3.);
        color+=body*(rim*.45+pow(bands,10.)*(.10+.3*u_impact))*(.5+energy);
    }
    vec3 emission=vec3(0.);
    if(form==0) {
        for(int k=0;k<8;k++) {
            float id=float(k);
            vec3 a=plasma_view(plasma_loop(0.,id));
            float nearest=100.,along=0.;
            for(int j=1;j<=40;j++) {
                float f=float(j)/40.;vec3 b=plasma_view(plasma_loop(f,id));
                vec2 sample=plasma_segment(p,a,b);a=b;
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
            emission+=hue*pigment*(filament+halo)*(.60+.70*energy)*u_plasma_details.x;
            emission+=hue*(filament+halo)*pulse*(.12+u_impact*1.2+u_sparkle*.3)*u_plasma_details.y;
            emission+=hue*filament*pow(pulse,3.)*.3*u_sparkle*u_plasma_details.z;
        }
    } else {
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
                    float width=.0015+.0015*u_impact;
                    float line=exp(-sample.x*sample.x/(width*width));
                    float glow=exp(-sample.x/(width*6.))*.16;
                    vec3 hue=plasma_tint(seed*5.+u_time*.09+f*.8);
                    emission+=hue*pigment*(line+glow)*(.10+.20*energy)*u_plasma_details.x;
                    emission+=hue*(line+glow)*flash*1.5*u_plasma_details.y;
                    float pulse=pow(.5+.5*sin(f*17.-u_time*4.+id),18.);
                    emission+=hue*line*pulse*.65*u_sparkle*u_plasma_details.z;
                }
                if(j==5 || j==11 || j==15) {
                    vec3 tip=q+side*(.2+.35*seed)+axis*.20;
                    vec2 branch=plasma_segment(p,b,plasma_view(tip));
                    if(branch.y/ray.z<solidDepth+.008)
                        emission+=plasma_tint(seed*5.+u_time*.09)*exp(-branch.x/.0014)*flash*.65*u_plasma_details.y;
                }
            }
        }
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

void main()
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
    if (directed) {
        float warp=(u_handoff.x>.5 ? 0. : u_world_warp)*(.12+.12*clamp(u_scale+u_flux,0.,1.));
        float angle=warp*exp(-dot(p,p)*1.2)*sin(length(p)*3.+u_time*.12);
        p=mat2(cos(angle),sin(angle),-sin(angle),cos(angle))*p;
        p*=1.+warp*(.6-length(p)*.3);
    }

    if (debug_state > 2.5 && debug_state < 3.5)
    {
        fragColor = vec4(isolated_cosmic_scene(p, vec3(0.0), 0.0, 1.0), 1.0);
        return;
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
float geo_detail = fbm(q * (6.0 + flux * 10.0) + vec2(t * 0.3, -t * 0.2));
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
    color += vec3(0.86, 0.97, 1.00) * star_mask * effect(2)
        * (0.18 * cosmic_weight + sparkle * (0.8 + cosmic_weight * 0.8))
        * (1.0-water_takeover);

    vec3 before_artifacts = color;

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
    color += art_accent * art_edge * effect(1) * (0.35 + geometric_weight * 0.30)
        * (1.0-water_takeover*.80);

    vec3 material_mix=selected_materials()*(1.-u_echo_weave);
    vec3 sibling_delta=vec3(0.);
    if(material_mix.y+material_mix.z+u_echo_weave>0.) {
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
        sibling_delta=siblings-living*(1.-material_mix.x);
    }
    vec3 fire_material = material_before_effects + color - before_artifacts;
    if(material_mix.y+material_mix.z+u_echo_weave>0.) fire_material+=sibling_delta;

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
    color += laser_color * laser_mask * effect(8) * 1.4 * (1.0-water_takeover);

    vec3 material_effects = color - material_before_effects;
    if(material_mix.y+material_mix.z+u_echo_weave>0.) {
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
    membrane_color *= 0.25 + membrane_body * 0.75;
    membrane_color += vec3(0.18, 0.50, 0.55) * membrane_ridge
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
    fragColor = vec4(color, 1.0);
}
