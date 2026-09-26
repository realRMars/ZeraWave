#version 330

uniform float u_time;
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
// shared DreamWave field so depth order can be judged without contamination.
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

// The accepted depth composition is shared by the isolated diagnostic and
// live takeover. Canvas color is evaluated from DreamWave's existing field.
vec3 isolated_cosmic_scene(vec2 p, vec3 canvas, float canvas_mix, float assembly)
{
    float time = u_drift_time;
    float color_drive = canvas_mix * smoothstep(0.08, 0.65,
        clamp(0.45 * u_scale + 0.35 * u_flux + 0.20 * u_sparkle, 0.0, 1.0));
    vec3 scene = vec3(0.0);
    // Layered star sheets drift one way across the sky and wrap off-screen.
    // Motion comes from the integrated clock, never from a spring that
    // returns. Audio only changes cruise speed and trail length.
    float star_drive = 0.48 * clamp(u_flux, 0.0, 1.0)
        + 0.22 * clamp(u_sparkle, 0.0, 1.0)
        + 0.30 * clamp(u_impact, 0.0, 1.0);
    float chorus = smoothstep(0.38, 0.88, star_drive);
    // Quiet: almost a point. Chorus: a long, thin wake behind the heading.
    float trail_len = mix(0.0012, 0.095, chorus * chorus);
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
        for (int star_i = 0; star_i < 5; star_i++)
        {
            float tail = float(star_i) / 4.0;
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
            float stars = (1.0 - smoothstep(star_size, star_size + star_aa,
                length(local - star_center))) * presence;
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
    scene += star_layer;

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
    for (int dust_i = 0; dust_i < 3; dust_i++)
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
    band_mask *= smoothstep(0.35, 0.90, assembly);

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
    for (int i = 0; i < 3; i++)
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

vec3 isolated_geometric_scene(vec2 p, vec3 canvas, float canvas_mix)
{
    float fluxv = clamp(u_flux, 0.0, 1.0);
    float spark = clamp(u_sparkle, 0.0, 1.0);
    float hit = clamp(u_impact, 0.0, 1.0);
    float walk = max(u_time, 0.0) * 1.05 + u_drift_time * 0.16;
    const float SPAN = 8.0;
    float seg = floor(walk / SPAN);
    float local = walk - seg * SPAN;
    float next_turn = geo_end_turn(seg);
    float turning = step(0.5, abs(next_turn));
    float turn_u = turning * smoothstep(SPAN - 3.4, SPAN - 0.04, local);
    float yaw = next_turn * 1.5707963 * turn_u;
    float cs = cos(yaw);
    float sn = sin(yaw);
    float w_here = geo_width(walk);
    float w_next = w_here;
    float h_next = geo_tall(walk);
    float slide = next_turn * turn_u * (w_here + w_next);
    vec3 ro = vec3(slide, 0.48, 0.0);
    vec3 rd = normalize(vec3(p.x * 0.90, (p.y - 0.10) * 0.72, 1.12));
    rd = vec3(cs * rd.x + sn * rd.z, rd.y, -sn * rd.x + cs * rd.z);
    float bass = clamp(u_scale, 0.0, 1.0);
    float drive = max(hit, max(fluxv * 0.85, bass));
    float flex = smoothstep(0.34, 0.86, drive);
    float amp = flex * (0.14 + 0.32 * drive) + hit * flex * 0.10;
    vec3 ink = vec3(0.010, 0.012, 0.014);
    float corner = SPAN - local;
    float best_t = 80.0;
    float kind = 0.0;
    vec3 hp = ro;
    for (int step_i = 0; step_i < 72; step_i++)
    {
        float t = 0.04 + float(step_i) * 0.14;
        vec3 q = ro + rd * t;
        float along = walk + t;
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
            float halfw = max(base_w - bow * sin(3.14159265 * y01), 0.14);
            float blocked = turning * step(corner, q.z) * step(q.x * next_turn, w_here * 0.2);
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
            break;
        }
    }
    vec3 scene = vec3(0.003, 0.004, 0.005);
    if (best_t < 70.0)
    {
        float travel = walk + best_t;
        float tall = geo_tall(travel);
        float v01 = clamp(hp.y / max(tall, 0.2), 0.0, 1.0);
        float down = (kind > 1.5 && kind < 2.5)
            ? fract(travel * 0.07)
            : (1.0 - v01);
        float across = (kind < 1.5) ? travel : hp.x + travel * 0.15;
        vec3 tint = geo_palette(0.62 + 0.28 * spark);
        vec3 metal = ink + geo_palette(0.18) * 0.55;
        metal += geo_palette(0.78) * 0.08;
        metal = mix(metal, canvas, clamp(canvas_mix, 0.0, 1.0) * 0.18);
        if (kind > 2.5) metal *= 0.55;
        if (kind > 1.5 && kind < 2.5) metal *= 0.70;
        vec3 rain = geo_rain(across, down, tint);
        float fog = exp(-best_t * 0.08);
        scene = metal * (0.20 + 0.80 * fog);
        scene += rain * (1.25 + spark * 0.6) * fog;
        float bay = floor(travel / 3.4);
        float open = 0.04 + 0.46 * hit;
        float door = step(0.55, hash(vec2(bay, 9.9)))
            * (1.0 - smoothstep(open, open + 0.05, abs(fract(travel * 0.35) - 0.5)))
            * (1.0 - smoothstep(0.12, 0.46, abs(v01 - 0.30)));
        vec3 door_col = geo_palette(0.90);
        scene = mix(scene, door_col, door * 0.85);
        scene += door_col * door * (0.20 + hit);
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

void main()
{
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;

    // Correct for the window's aspect ratio.
    vec2 p = uv - 0.5;
    p.x *= u_resolution.x / u_resolution.y;

    if (u_debug_state > 2.5 && u_debug_state < 3.5)
    {
        fragColor = vec4(isolated_cosmic_scene(p, vec3(0.0), 0.0, 1.0), 1.0);
        return;
    }

    vec2 screen_p = p;
    float cosmic_takeover = (
        u_debug_state < 0.5
        || (u_debug_state > 1.5 && u_debug_state < 2.5)
        || u_debug_state > 3.5
    ) ? cosmic_handoff(u_drift_time, u_debug_state > 3.5) : 0.0;
    if (u_debug_state > 4.5) cosmic_takeover = 1.0;
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

    if (u_debug_state > 0.5 && u_debug_state < 1.5) {
        tunnel_weight = 0.0; fractal_weight = 0.0; geometric_weight = 0.0;
        cosmic_weight = 0.0; horizon_weight = 0.0;
    } else if (u_debug_state > 1.5 && u_debug_state < 2.5) {
        tunnel_weight = 0.0; fractal_weight = 0.0; geometric_weight = 1.0;
        cosmic_weight = 0.0; horizon_weight = 0.0;
    } else if (u_debug_state > 2.5 && u_debug_state < 3.5) {
        tunnel_weight = 0.0; fractal_weight = 0.0; geometric_weight = 0.0;
        cosmic_weight = 1.0; horizon_weight = 0.0;
    }

    // Cosmic is an intentional world takeover: once it has weight, the
    // other vocabularies recede so the planet, rings, and starfield can own
    // the frame instead of blending into another abstract layer.
    float cosmic_dominance = cosmic_weight * 0.88;
    tunnel_weight *= 1.0 - cosmic_dominance;
    fractal_weight *= 1.0 - cosmic_dominance;
    geometric_weight *= 1.0 - cosmic_dominance;
    horizon_weight *= 1.0 - cosmic_dominance;

    float total_transform = tunnel_weight + fractal_weight
        + geometric_weight + cosmic_weight + horizon_weight;
    // Keep a faint organic home-state thread during overlapping handoffs.
    // Alternate vocabularies may still dominate, but the world never loses
    // all continuity when several dwell windows coincide.
    float organic_floor = 0.08 * (1.0 - cosmic_weight);
    float organic_weight = max(organic_floor, 1.0 - total_transform);
    float weight_sum = max(organic_weight + total_transform, 1.0);

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

q = mix(q, geo_q, geometric_weight);

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
        + geo_dream_color * geometric_weight
        + ember_palette(body_value) * cosmic_weight
        + teal_amber_palette(body_value) * horizon_weight
    ) / weight_sum;


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
        * (0.5 + horizon_maturity * 0.4);
    color += vec3(0.90, 0.80, 0.60) * horizon_bands;

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

    // Stars share the same coordinate deformation as the field, so they
    // feel embedded in the universe rather than pasted over it.
    vec2 star_space = q * (5.0 + bass_pressure * 5.0);
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

    color += vec3(0.86, 0.97, 1.00) * star_mask
        * (0.18 * cosmic_weight + sparkle * (0.8 + cosmic_weight * 0.8));

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

    color += art_color * art_mask * (0.55 + sparkle * 0.55
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
    color += art_accent * art_edge * (0.35 + geometric_weight * 0.30);

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

    color += fall_color * fall_mask * (0.5 + sparkle * 0.5);

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
    color += laser_color * laser_mask * 1.4;

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
    float root_mix = dwell(u_drift_time * 0.04 - 1.8);
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
    membrane_color += vec3(0.95, 0.42, 0.62) * blossom;
    color = mix(color, membrane_color * u_intensity, organic_weight / weight_sum);


    // Oil-paint tonemap: compress extreme brightness toward the
    // palette's saturated colors instead of collapsing into white.
    float peak = max(color.r, max(color.g, color.b));
    color = color / (1.0 + peak * 0.6);

    if (geometric_weight > 0.0)
    {
        float geo_canvas = clamp(
            tunnel_weight + fractal_weight * 0.85
            + horizon_weight * 0.25 + u_flux * 0.30,
            0.0, 1.0
        );
        vec3 geo_world = isolated_geometric_scene(screen_p, color, geo_canvas);
        color = mix(color, geo_world, geometric_weight);
    }
    if (cosmic_takeover > 0.0)
    {
        vec3 world = isolated_cosmic_scene(cosmic_p, color, 1.0, cosmic_takeover);
        color = mix(color, world, cosmic_takeover);
    }
    fragColor = vec4(color, 1.0);
}
