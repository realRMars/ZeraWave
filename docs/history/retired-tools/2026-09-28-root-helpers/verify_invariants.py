import re

with open('app/visuals/shaders/dream.frag', 'r') as f:
    lines = f.readlines()
print(f'Final line count: {len(lines)}')

checks = {
    'q_geom present': any('q_geom' in l for l in lines),
    'geometric_weight present': any('geometric_weight' in l for l in lines),
    'tunnel_weight present': any('tunnel_weight' in l for l in lines),
    'tunnel_q present': any('tunnel_q' in l for l in lines),
    'geometric_dream_palette present': any('geometric_dream_palette' in l for l in lines),
    'collapse_amount has tunnel_weight': any('+ tunnel_weight * 0.55' in l for l in lines),
    'tunnel_fracture present': any('tunnel_fracture' in l for l in lines),
    'eye_open has tunnel_weight': any('+ tunnel_weight * 0.5' in l for l in lines),
}
for k, v in checks.items():
    status = 'OK' if v else 'MISSING'
    print(f'{k}: {status}')

forbidden = ['iTime', 'mids', 'highs', 'bass', 'sacred_radius', 'sacred_angle', 'facet_angle', 'geometric_color']
for v in forbidden:
    matches = re.findall(r'\b' + v + r'\b', ''.join(lines))
    if matches:
        print(f'WARNING: standalone {v} found ({len(matches)} occurrences)')
    else:
        print(f'OK: standalone {v} not present')