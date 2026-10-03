"""Shared authored taxonomy; player discovery filters canonical Main eligibility."""
LIVE_STATES = {"blend": 0, "organic": 1, "geometric": 2, "cosmic": 3,
               "transition": 4, "canvas": 5, "water": 6, "sea": 7,
               "dyes": 8, "rain": 9, "waterfall": 10, "membrane": 11, "roots": 12, "currents": 13, "fire": 14, "molten": 15, "fire_cycle": 16, "firescape": 17, "aftershock": 18, "windstreams": 19, "stormfront": 20, "vortex": 21, "citadel": 22, "air": 23, "dunes": 24, "strata": 25, "cavern": 26, "earth": 27, "nebula": 28, "marsh": 29, "pressure": 30, "fog": 31, "magnetic": 32, "arcs": 33, "auroral": 34, "plasma": 35, "galaxy": 36, "cymatics": 37, "lodestone_experimental":38, "stormglass_experimental":39, "folded_aurora_experimental":40}

WORLD_TREE = {
    'cymatics': dict(label='Cymatics',children={'water':dict(label='Water — Resonance basin',state='cymatics')}),
    'experimental': dict(label='Experimental / unfinished', children={
        'transition_study':dict(label='Legacy transition study (Demo)',state='transition'),
        'lodestone':dict(label='Lodestone Field (Experimental)',state='lodestone_experimental'),
        'stormglass':dict(label='Stormglass Network (Experimental)',state='stormglass_experimental'),
        'folded_aurora':dict(label='Folded Aurora (Experimental)',state='folded_aurora_experimental'),
    }),
    'organic': dict(label='Organic', cycle='organic', children={
        'membrane': dict(label='Membrane', state='membrane'),
        'roots': dict(label='Roots', state='roots'),
    }),
    'geometric': dict(label='Geometric', cycle='geometric', children={
        'corridor': dict(label='Neon corridor', state='geometric'),
    }),
    'cosmic': dict(label='Cosmic', cycle='canvas', children={
        'canvas': dict(label='Planet canvas', state='canvas'),
        'galaxy': dict(label='Galaxy', state='galaxy'),
    }),
    'elements': dict(label='Elements', children={
        'plasma': dict(label='Plasma', cycle='plasma', children={
            'magnetic': dict(label='Magnetic Bloom', state='magnetic'),
            'arcs': dict(label='Arc Constellation', state='arcs'),
            'auroral': dict(label='Auroral Veil', state='auroral'),
        }),
        'fog': dict(label='Fog / Gas', cycle='fog', children={
            'nebula': dict(label='Nebula Banks', state='nebula'),
            'marsh': dict(label='Ghostlight Marsh', state='marsh'),
            'pressure': dict(label='Pressure Chamber', state='pressure'),
        }),
        'earth': dict(label='Earth', cycle='earth', children={
            'dunes': dict(label='Dune Sea', state='dunes'),
            'strata': dict(label='Folded Strata', state='strata'),
            'cavern': dict(label='Crystal Cavern', state='cavern'),
        }),
        'air': dict(label='Air / Wind', cycle='air', children={
            'windstreams': dict(label='Windstreams', state='windstreams'),
            'stormfront': dict(label='Stormfront', state='stormfront'),
            'vortex': dict(label='Vortex', state='vortex'),
            'citadel': dict(label='Sky Citadel', state='citadel'),
        }),
        'water': dict(label='Water', cycle='water', children={
            'sea': dict(label='Sea', state='sea'),
            'dyes': dict(label='Liquid dyes', state='dyes'),
            'rain': dict(label='Rain & ripples', state='rain'),
            'waterfall': dict(label='Waterfall', state='waterfall'),
            'currents': dict(label='Currents', state='currents'),
        }),
        'fire': dict(label='Fire', cycle='fire_cycle', children={
            'sheets': dict(label='Flame sheets', state='fire'),
            'molten': dict(label='Molten flow', state='molten'),
            'firescape': dict(label='Firescape', state='firescape'),
            'aftershock': dict(label='Aftershock', state='aftershock'),
        }),
    }),
}

def main_entries(roster):
    rows = {}
    def visit(children, labels):
        for node in children.values():
            names = labels + [node['label']]
            state = LIVE_STATES.get(node.get('state'))
            if state in roster:
                rows[state] = dict(id=state, name=names[-1], category=names[0],
                                  subcategory=' / '.join(names[1:-1]) or '—')
            visit(node.get('children', {}), names)
    visit(WORLD_TREE, [])
    if set(rows) != set(roster):
        raise ValueError('Main taxonomy and roster differ.')
    return [rows[state] for state in roster]
