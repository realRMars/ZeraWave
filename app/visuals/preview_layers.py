"""Shared development effect catalog and validation; not an audio parameter system.

Bit positions are the existing shader's optional isolation switches. Append IDs;
do not reorder them. An absent profile preserves the authored shader exactly.
"""
import json
import math

WORLDS = ('blend', 'organic', 'geometric', 'cosmic', 'transition', 'water')
FIELD = ('blend', 'organic', 'geometric', 'cosmic', 'transition')
EFFECTS = {
    'artifacts': ('Living artifacts', 'Material', WORLDS),
    'sparkles': ('Sparkles', 'Material', FIELD),
    'flecks': ('Drifting flecks', 'Material', FIELD),
    'beams': ('Radial beams', 'Material', FIELD),
    'tunnel': ('Tunnel', 'Spatial', FIELD),
    'fractal': ('Fractal folds', 'Spatial', FIELD),
    'horizon': ('Horizon / pathway', 'Spatial', FIELD),
    'blossoms': ('Root blossoms', 'World details', ('blend', 'organic')),
    'glyphs': ('Corridor glyph rain', 'World details', ('blend', 'geometric')),
    'stars': ('Drifting starfield', 'World details', ('blend', 'cosmic', 'transition')),
    'rings': ('Planet rings', 'World details', ('blend', 'cosmic', 'transition')),
    'moons': ('Moons & dust wakes', 'World details', ('blend', 'cosmic', 'transition')),
    'water_rain': ('Rain streaks', 'Water details', ('blend', 'water')),
    'water_ripples': ('Ripple rings', 'Water details', ('blend', 'water')),
    'water_foam': ('Crest foam / cliff lip', 'Water details', ('blend', 'water')),
    'water_mist': ('Mist & distance haze', 'Water details', ('blend', 'water')),
    'water_glints': ('Surface highlights', 'Water details', ('blend', 'water')),
}
BITS = {key: 1 << i for i, key in enumerate(EFFECTS)}
MODES = {'authored': 'Authored', 'together': 'Selected together', 'cycle': 'Cycle list'}


def default_profile():
    return dict(mode='authored', seconds=12., items=[])


def validate_layers(data):
    if not isinstance(data, dict) or any(key not in WORLDS for key in data):
        raise ValueError('Unknown world in effect settings.')
    result = {}
    for world, profile in data.items():
        if not isinstance(profile, dict) or profile.get('mode') not in MODES:
            raise ValueError('Unknown effect playback mode.')
        seconds = profile.get('seconds', 12.)
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 1 <= seconds <= 300:
            raise ValueError('Effect hold must be between 1 and 300 seconds.')
        items = profile.get('items')
        if not isinstance(items, list):
            raise ValueError('Effects must be an ordered list.')
        clean, seen = [], set()
        for item in items:
            if not isinstance(item, dict): raise ValueError('Invalid effect row.')
            key = item.get('id')
            if not isinstance(key, str) or key not in EFFECTS or world not in EFFECTS[key][2]:
                raise ValueError('This effect is not available in this world.')
            if key in seen or type(item.get('enabled')) is not bool:
                raise ValueError('Duplicate effect or invalid enabled setting.')
            seen.add(key)
            clean.append(dict(id=key, enabled=item['enabled']))
        result[world] = dict(mode=profile['mode'], seconds=float(seconds), items=clean)
    return result


def parse_layers(text):
    return validate_layers(json.loads(text))


def world_for_state(state):
    if state in (1, 11, 12): return 'organic'
    if state == 2: return 'geometric'
    if state in (3, 5): return 'cosmic'
    if state == 4: return 'transition'
    if 6 <= state <= 10 or state == 13: return 'water'
    return 'blend'


def layers_at(profiles, state, seconds):
    profile = profiles.get(world_for_state(state), default_profile())
    if profile['mode'] == 'authored': return 0, 0
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return 1, sum(BITS[key] for key in ids)
