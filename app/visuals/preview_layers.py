"""Shared development effect catalog and validation; not an audio parameter system.

Bit positions are the existing shader's optional isolation switches. Append IDs;
do not reorder them. Absent held-world profiles preserve authored visuals; Main blend defaults to the paced seven-material show.
"""
import json
import math

WORLDS = ('blend', 'organic', 'geometric', 'cosmic', 'transition', 'water', 'fire', 'air', 'earth', 'fog', 'plasma')
PROFILE_WORLDS = WORLDS + ('galaxy',)
FIELD = ('blend', 'organic', 'geometric', 'cosmic', 'transition')
EFFECTS = {
    'artifacts': ('Living artifacts', 'Material', WORLDS),
    'sparkles': ('Sparkles', 'Material', FIELD),
    'flecks': ('Drifting flecks', 'Material', FIELD),
    'beams': ('Radial beams', 'Material', FIELD),
    'tunnel': ('Tunnel', 'Spatial', WORLDS),
    'fractal': ('Fractal folds', 'Spatial', WORLDS),
    'horizon': ('Horizon / pathway', 'Spatial', WORLDS),
    'blossoms': ('Root blossoms', 'World details', ('blend', 'organic')),
    'glyphs': ('Corridor glyph rain', 'World details', ('blend', 'geometric')),
    'stars': ('Drifting starfield', 'World details', ('blend', 'cosmic', 'transition', 'air', 'earth')),
    'rings': ('Planet rings', 'World details', ('blend', 'cosmic', 'transition')),
    'moons': ('Moons & dust wakes', 'World details', ('blend', 'cosmic', 'transition')),
    'water_rain': ('Rain streaks', 'Water details', ('blend', 'water')),
    'water_ripples': ('Ripple rings', 'Water details', ('blend', 'water')),
    'water_foam': ('Crest foam / cliff lip', 'Water details', ('blend', 'water')),
    'water_mist': ('Mist & distance haze', 'Water details', ('blend', 'water')),
    'water_glints': ('Surface highlights', 'Water details', ('blend', 'water')),
    'fire_coals': ('Coals', 'Fire details', ('blend', 'fire')),
    'fire_embers': ('Embers', 'Fire details', ('blend', 'fire')),
    'fire_seams': ('Hot seams', 'Fire details', ('blend', 'fire')),
    'fire_ash': ('Ash', 'Fire details', ('blend', 'fire')),
    'blast_flash': ('Inversion flash', 'Aftershock details', ('blend', 'fire')),
    'blast_dust': ('Dust shockwaves', 'Aftershock details', ('blend', 'fire')),
    'blast_fire': ('Ground fire', 'Aftershock details', ('blend', 'fire')),
    'blast_aurora': ('Aurora', 'Aftershock details', ('blend', 'fire')),
    'alloy': ('Liquid Alloy', 'Material', WORLDS),
    'lattice': ('Prismatic Lattice', 'Material', WORLDS),
    'air_clouds': ('Cloud banks & wind ribbons', 'Air details', ('blend', 'air')),
    'air_balloons': ('Fractal balloons', 'Air details', ('blend', 'air')),
    'air_lightning': ('Lightning & lingering arcs', 'Air details', ('blend', 'air')),
    'air_citadel': ('Castle, earth & celebration', 'Air details', ('blend', 'air')),
    'daddy_long_legs': ('Daddy Long Legs', 'FX experiments', ('blend', 'air')),
    'earth_sediment': ('Sediment bands & sand ripples', 'Earth details', ('blend', 'earth')),
    'earth_veins': ('Mineral veins & crystal light', 'Earth details', ('blend', 'earth')),
    'earth_dust': ('Surface mineral glints', 'Earth details', ('blend', 'earth')),
    'earth_worm': ('Sand worm', 'Earth inhabitants', ('blend', 'earth')),
    'fog_volume': ('Vapor banks', 'Fog details', ('blend', 'fog')),
    'fog_lights': ('Internal light & ghostlights', 'Fog details', ('blend', 'fog')),
    'fog_fronts': ('Pressure fronts & fine filaments', 'Fog details', ('blend', 'fog')),
    'plasma_field': ('Magnetic filaments & curtains', 'Plasma details', ('blend', 'plasma')),
    'plasma_arcs': ('Discharges & traveling pulses', 'Plasma details', ('blend', 'plasma')),
    'plasma_sparks': ('Charged particles & distant stars', 'Plasma details', ('blend', 'plasma')),
}
EFFECTS['echo_weave'] = ('Echo Weave', 'Material', WORLDS)
# All 31 positive signed-mask bits are occupied; later effects use explicit uniforms.
EFFECTS['shooting_stars'] = ('Shooting stars', 'Sky effects', ('blend', 'water', 'cosmic'))
NEW_MATERIALS = ('ink_archipelago', 'interference_silk', 'cellular_mosaic')
for key, label in zip(NEW_MATERIALS, ('Ink Archipelago', 'Interference Silk', 'Cellular Mosaic')):
    EFFECTS[key] = (label, 'Material', WORLDS)
SPATIAL_TREATMENTS = ('elastic_lenses', 'braided_flow', 'nested_windows')
ENVELOPERS = ('prism_assembly', 'digital_bloom', 'chromatic_memory')
for key,label in zip(SPATIAL_TREATMENTS, ('Elastic Lenses','Braided Flow','Nested Windows')):
    EFFECTS[key] = (label,'Spatial',WORLDS)
for key,label in zip(ENVELOPERS, ('Prism Assembly','Digital Bloom','Chromatic Memory')):
    EFFECTS[key] = (label,'Envelopers',WORLDS)
STELLAR_LAYERS = ('stellar_sails', 'parallax_shoal')
for key,label in zip(STELLAR_LAYERS, ('Ion Comets','Parallax Shoal')):
    EFFECTS[key] = (label,'Sky effects',('galaxy','cosmic','fog','plasma'))
ORBITAL_LAYERS = ('gravity_well',)
EFFECTS['gravity_well']=('Stellar Gravity Well','Spatial',('galaxy',))
SKY_EFFECTS = ('shooting_stars',) + STELLAR_LAYERS
EXPERIMENTS = ('daddy_long_legs',)
EXPLICIT_MATERIALS = ('echo_weave',) + NEW_MATERIALS
EARTH_DETAILS = ('earth_sediment', 'earth_veins', 'earth_dust', 'earth_worm')
FOG_DETAILS = ('fog_volume', 'fog_lights', 'fog_fronts')
PLASMA_DETAILS = ('plasma_field', 'plasma_arcs', 'plasma_sparks')
BITS = {key: (0 if key in EXPERIMENTS + EXPLICIT_MATERIALS + EARTH_DETAILS + FOG_DETAILS + PLASMA_DETAILS + SKY_EFFECTS + SPATIAL_TREATMENTS + ENVELOPERS + ORBITAL_LAYERS else 1 << i) for i, key in enumerate(EFFECTS)}
MODES = {'authored': 'Authored', 'together': 'Selected together', 'cycle': 'Cycle list', 'meld': 'Meld materials'}
MATERIALS = ('artifacts', 'alloy', 'lattice', 'echo_weave') + NEW_MATERIALS


def default_profile(world=None):
    if world == 'blend':
        profile = material_quartet_profile(world)
        profile['seconds'] = 22.
        profile['items'].extend(dict(id=key,enabled=True) for key in NEW_MATERIALS+SPATIAL_TREATMENTS)
        return profile
    return dict(mode='authored', seconds=12., items=[])


def profile_at(profiles,state):
    world=world_for_state(state)
    profile=profiles.get(world,default_profile(world))
    if world=='blend' and profile['mode']=='authored':return default_profile(world)
    return profile


def validate_layers(data):
    if not isinstance(data, dict) or any(key not in PROFILE_WORLDS for key in data):
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
            row=dict(id=key, enabled=item['enabled'])
            if 'amount' in item:
                amount=item['amount']
                if key not in SPATIAL_TREATMENTS+ENVELOPERS+STELLAR_LAYERS+ORBITAL_LAYERS or type(amount) not in (int,float) or not math.isfinite(amount) or not 0<=amount<=1:
                    raise ValueError('Treatment amount must be 0-1 on a new spatial effect or Enveloper.')
                row['amount']=float(amount)
            clean.append(row)
        result[world] = dict(mode=profile['mode'], seconds=float(seconds), items=clean)
    return result


def parse_layers(text):
    return validate_layers(json.loads(text))


def world_for_state(state):
    if 32 <= state <= 35: return 'plasma'
    if 28 <= state <= 31: return 'fog'
    if 24 <= state <= 27: return 'earth'
    if 19 <= state <= 23: return 'air'
    if state in (1, 11, 12): return 'organic'
    if state == 2: return 'geometric'
    if state in (3, 5): return 'cosmic'
    if state == 36: return 'galaxy'
    if state == 4: return 'transition'
    if 6 <= state <= 10 or state == 13: return 'water'
    if state in (14, 15, 16, 17, 18): return 'fire'
    return 'blend'


def layers_at(profiles, state, seconds):
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return 0, 0
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return (2 if profile['mode'] == 'meld' else 1), sum(BITS[key] for key in ids)


def material_weights(profiles, state, seconds):
    """Absolute material weights in stable append-only order; old lists stay valid."""
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return (1.,) + (0.,) * (len(MATERIALS)-1)
    ids = [item['id'] for item in profile['items'] if item['enabled'] and item['id'] in MATERIALS]
    weights = [0.] * len(MATERIALS)
    if not ids: return tuple(weights)
    if profile['mode'] == 'meld':
        phase = max(0., seconds) / profile['seconds']
        index = int(phase) % len(ids)
        fade = max(0., min(1., ((phase % 1.) - .65) / .35))
        fade = fade * fade * (3. - 2. * fade)
        weights[MATERIALS.index(ids[index])] += 1. - fade
        weights[MATERIALS.index(ids[(index + 1) % len(ids)])] += fade
    else:
        if profile['mode'] == 'cycle':
            enabled = [item['id'] for item in profile['items'] if item['enabled']]
            selected = enabled[int(max(0., seconds) // profile['seconds']) % len(enabled)]
            ids = [key for key in ids if key == selected]
        for key in ids: weights[MATERIALS.index(key)] = 1. / len(ids)
    return tuple(weights)


def materials_at(profiles, state, seconds):
    # Preserve the vec3 shader interface; Echo's separate weight scales this trio.
    weights = material_weights(profiles, state, seconds)[:3]
    total = sum(weights)
    return tuple(w / total for w in weights) if total else (0., 0., 0.)


def daddy_long_legs_at(profiles, state, seconds):
    """Explicit opt-in only, including when a user cycles experimental rows."""
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return 0.
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return float('daddy_long_legs' in ids)


def earth_details_at(profiles, state, seconds):
    """Additional detail switches without renumbering the full legacy mask."""
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return (1., 1., 1., 1.)
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return tuple(float(key in ids) for key in EARTH_DETAILS)


def fog_details_at(profiles, state, seconds):
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return (1., 1., 1.)
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return tuple(float(key in ids) for key in FOG_DETAILS)


def plasma_details_at(profiles, state, seconds):
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return (1., 1., 1.)
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return tuple(float(key in ids) for key in PLASMA_DETAILS)


def material_trio_profile(world):
    """Authored details plus the three materials, suitable for main-live testing."""
    return dict(mode='meld', seconds=36., items=[dict(id=key, enabled=True)
        for key, info in EFFECTS.items() if world in info[2] and key not in EXPERIMENTS + EXPLICIT_MATERIALS + SPATIAL_TREATMENTS + ENVELOPERS + STELLAR_LAYERS + ORBITAL_LAYERS])


def material_quartet_profile(world):
    profile = material_trio_profile(world)
    profile['items'].append(dict(id='echo_weave', enabled=True))
    return profile


def echo_weave_at(profiles, state, seconds):
    return material_weights(profiles, state, seconds)[3]


def echo_selected(profiles, state):
    profile = profile_at(profiles,state)
    return profile['mode'] != 'authored' and any(item['id'] == 'echo_weave' and item['enabled'] for item in profile['items'])


def shooting_stars_at(profiles, state, seconds):
    world = world_for_state(state)
    if world not in EFFECTS['shooting_stars'][2]: return 0.
    profile = profile_at(profiles,state)
    if profile['mode'] == 'authored': return float(world == 'water')
    ids = [item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode'] == 'cycle' and ids:
        ids = [ids[int(max(0., seconds) // profile['seconds']) % len(ids)]]
    return float('shooting_stars' in ids)


def stellar_layers_at(profiles,state,seconds):
    """Galaxy's authored inhabitants; opt-in in other compatible worlds."""
    world=world_for_state(state)
    if world not in ('galaxy','cosmic','fog','plasma'):return (0.,0.)
    profile=profile_at(profiles,state)
    if profile['mode']=='authored':return (1.,1.) if world=='galaxy' else (0.,0.)
    return treatment_weights(profiles,state,seconds,STELLAR_LAYERS)


def treatment_weights(profiles,state,seconds,keys):
    """Explicit list selection. Added effects never leak into legacy/custom lists."""
    profile=profile_at(profiles,state)
    if profile['mode']=='authored': return (0.,)*len(keys)
    enabled=[item['id'] for item in profile['items'] if item['enabled']]
    if profile['mode']=='cycle' and enabled:
        enabled=[enabled[int(max(0.,seconds)//profile['seconds'])%len(enabled)]]
    selected=[key for key in enabled if key in keys]
    automatic=state==0 and keys!=ENVELOPERS and ('blend' not in profiles or profiles['blend']['mode']=='authored')
    if automatic:
        # Each 72s passage: spatial 8..28s, then an untreated gap.
        # Envelopers remain opt-in while their appearance is reviewed.
        phase=max(0.,seconds)/72.;age=(phase%1.)*72.
        start,end=8.,28.
        amount=max(0.,min(1.,(age-start)/6.,(end-age)/6.))
        amount=amount*amount*(3.-2.*amount)*.65
        return tuple(amount if index==int(phase)%len(keys) else 0. for index in range(len(keys)))
    amounts={item['id']:item.get('amount',1.) for item in profile['items']}
    # One final-image treatment at a time; list order supplies deliberate pacing.
    if keys==ENVELOPERS and len(selected)>1:
        phase=max(0.,seconds)/max(12.,profile['seconds'])
        current=selected[int(phase)%len(selected)]
        age=phase%1.
        strength=min(1.,age/.18,(1.-age)/.22)
        strength=max(0.,strength);strength=strength*strength*(3.-2.*strength)
        return tuple(strength*amounts.get(key,1.) if key==current else 0. for key in keys)
    return tuple(float(key in selected)*amounts.get(key,1.) for key in keys)


def gravity_well_at(profiles,state,seconds):
    if world_for_state(state)!='galaxy':return 0.
    if profile_at(profiles,state)['mode']=='authored':return .72
    return treatment_weights(profiles,state,seconds,ORBITAL_LAYERS)[0]
