with open('app/visuals/shaders/dream.frag', 'r') as f:
    content = f.read()

targets = {
    'generative_insert': '    // Living artifacts: sparse procedural droplets/shards/sparks',
    'art_presence': '    float art_presence = step(\n        0.90 - any_maturity * 0.08 - sparkle_reveal * 0.10, art_seed\n    );',
    'art_jag_line': '    float art_jag = clamp(impact * 0.6 + geometric_weight * 0.5, 0.0, 1.0);',
    'art_facet': '    float art_facet = cos(\n        atan(art_local.y, art_local.x) * mix(1.0, 6.0, art_jag)\n            + art_seed * 6.2832\n    );',
    'art_size_block': '    float art_size = (0.09 + hash(art_cell + 2.1) * 0.10)\n        * (0.4 + art_life * 0.9);',
    'art_color_add': '    color += art_color * art_mask * (0.55 + sparkle * 0.55);',
}

for name, s in targets.items():
    found = s in content
    print(name + ": " + (found and "FOUND" or "NOT FOUND"))