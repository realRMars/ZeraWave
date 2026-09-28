with open('app/visuals/shaders/dream.frag', 'r') as f:
    content = f.read()

# --- Edit 1: Insert generative variation streams before living artifacts ---
old_anchor1 = '    // Living artifacts: sparse procedural droplets/shards/sparks'
new_anchor1 = '''    // Secondary morphology variation: slowly-evolving parameters that
    // let the living artifacts drift between different structural
    // families (blobs, petals, rings, shards, eyes, lattice) without
    // hard-coded states. Each stream samples a different noise
    // coordinate so they evolve independently; slowly enough to
    // feel stable, slowly enough to surprise.
    float secondary_morph = noise(vec2(u_drift_time * 0.012, 1.0));
    float secondary_density = noise(vec2(u_drift_time * 0.009, 3.0));
    float secondary_spin = noise(vec2(u_drift_time * 0.011, 5.0));
    float secondary_focal = noise(vec2(u_drift_time * 0.008, 7.0));

    // Living artifacts: sparse procedural droplets/shards/sparks'''

assert old_anchor1 in content, 'Edit 1: anchor not found'
content = content.replace(old_anchor1, new_anchor1, 1)
print('Edit 1 (generative streams) applied.')

# --- Edit 2: Modify art_presence for tunnel compatibility ---
old_presence = '''    float art_presence = step(
        0.90 - any_maturity * 0.08 - sparkle_reveal * 0.10, art_seed
    );'''
new_presence = '''    // Presence threshold lowered during tunnel compression so
    // secondary structure persists when the macro field collapses
    // toward a pinpoint -- residual artifacts provide edge and
    // contrast even inside the wormhole.
    float art_presence = step(
        0.90 - any_maturity * 0.08 - sparkle_reveal * 0.10
            - tunnel_weight * 0.14,
        art_seed
    );'''

assert old_presence in content, 'Edit 2: art_presence not found'
content = content.replace(old_presence, new_presence, 1)
print('Edit 2 (art_presence tunnel compat) applied.')

# --- Edit 3: Expand art_facet + art_size + art_dist + art_mask ---
old_facet = '''    float art_jag = clamp(impact * 0.6 + geometric_weight * 0.5, 0.0, 1.0);
    float art_facet = cos(
        atan(art_local.y, art_local.x) * mix(1.0, 6.0, art_jag)
        + art_seed * 6.2832
    );

    float art_size = (0.09 + hash(art_cell + 2.1) * 0.10)
        * (0.4 + art_life * 0.9);
    float art_dist = length(art_local) - art_facet * art_jag * 0.03;
    float art_mask = smoothstep(art_size, art_size * 0.15, art_dist)
        * art_presence * art_life;'''

new_facet = '''    // Shape family: the base angular facet modulation is extended
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
        * art_presence * art_life;'''

assert old_facet in content, 'Edit 3: art_facet block not found'
content = content.replace(old_facet, new_facet, 1)
print('Edit 3 (artifact shape evolution) applied.')

# --- Edit 4: Add edge accent highlight after art_color ---
old_color = '    color += art_color * art_mask * (0.55 + sparkle * 0.55);'
new_color = '''    color += art_color * art_mask * (0.55 + sparkle * 0.55
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
    color += art_accent * art_edge * (0.35 + geometric_weight * 0.30);'''

assert old_color in content, 'Edit 4: art_color_add not found'
content = content.replace(old_color, new_color, 1)
print('Edit 4 (edge accent highlight) applied.')

with open('app/visuals/shaders/dream.frag', 'w', encoding='utf-8') as f:
    f.write(content)

print('All edits applied successfully.')