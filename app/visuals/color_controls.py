"""Small effect-owned color declarations. Fixed roles, authored fallback, no world catalog."""
from dataclasses import dataclass
import json
import math
import re


@dataclass(frozen=True)
class ColorSlot:
    id: str
    label: str
    rgb: tuple
    start: float | None = None
    end: float | None = None


@dataclass(frozen=True)
class ColorTarget:
    id: str
    label: str
    scene: str
    kind: str
    uniform: str
    slots: tuple
    note: str


# These are the actual overlapping smoothstep transitions, not evenly spaced stops.
_TRANSITIONS = ((None, None), (0., .35), (.30, .60), (.55, .85), (.82, 1.))

def _gradient(ids, labels, colors):
    return tuple(ColorSlot(key, label, rgb, *span)
                 for key, label, rgb, span in zip(ids, labels, colors, _TRANSITIONS))


TARGETS = (
    ColorTarget('roots.blue', 'Roots field — blue shading', 'roots', 'staged_gradient', 'u_roots_blue',
        _gradient(('deep','cobalt','electric','cyan','pale'),
                  ('Deep base','Cobalt','Electric blue','Cyan','Pale highlight'),
                  ((.004,.006,.016),(.030,.090,.320),(.080,.280,.920),(.300,.720,.980),(.850,.960,1.))),
        'One of two shading gradients across roots and their dim surrounding field. Start/end set each color transition along shading value, not branch length.'),
    ColorTarget('roots.pearl', 'Roots field — pearl shading', 'roots', 'staged_gradient', 'u_roots_pearl',
        _gradient(('deep','blue','lavender','rose','pearl'),
                  ('Deep base','Blue','Lavender','Rose','Pearl highlight'),
                  ((.012,.010,.018),(.100,.110,.260),(.360,.300,.520),(.680,.560,.640),(.960,.950,.970))),
        'The second shading gradient blends spatially with blue shading. Fixed roles preserve the existing layered gradient; not a tip-color control.'),
    ColorTarget('roots.ridge', 'Root ridge highlights', 'roots', 'color', 'u_roots_ridge',
        (ColorSlot('tint','Ridge tint',(.18,.50,.55)),),
        'The additive ridge tint. Existing ridge shape and musical brightness remain active; material overlays retain their own colors.'),
    ColorTarget('roots.blossoms', 'Blossoms', 'roots', 'color', 'u_roots_blossoms',
        (ColorSlot('tint','Petals + center tint',(.95,.42,.62)),),
        'Petals and center share one tint. Blossom lifecycle, audio brightness and the Root blossoms layer switch still apply. No separate glow color exists.'),
    ColorTarget('membrane.blue', 'Membrane field — blue shading', 'membrane', 'staged_gradient', 'u_membrane_blue',
        _gradient(('deep','cobalt','electric','cyan','pale'),
                  ('Deep base','Cobalt','Electric blue','Cyan','Pale highlight'),
                  ((.004,.006,.016),(.030,.090,.320),(.080,.280,.920),(.300,.720,.980),(.850,.960,1.))),
        'Blue shading across the Membrane folds and dim surrounding field. The Roots gradient is independent during Organic cycling.'),
    ColorTarget('membrane.pearl', 'Membrane field — pearl shading', 'membrane', 'staged_gradient', 'u_membrane_pearl',
        _gradient(('deep','blue','lavender','rose','pearl'),
                  ('Deep base','Blue','Lavender','Rose','Pearl highlight'),
                  ((.012,.010,.018),(.100,.110,.260),(.360,.300,.520),(.680,.560,.640),(.960,.950,.970))),
        'Pearl shading spatially blends with Membrane blue shading. The Roots gradient is independent during Organic cycling.'),
    ColorTarget('membrane.ridge', 'Membrane ridge highlights', 'membrane', 'color', 'u_membrane_ridge',
        (ColorSlot('tint','Ridge tint',(.18,.50,.55)),),
        'The additive fold ridge tint. Fold geometry and musical brightness remain authored.'),
    ColorTarget('corridor.inlay', 'Corridor inlay pigment', 'geometric', 'color', 'u_corridor_inlay',
        (ColorSlot('tint','Inlay tint',(1.,1.,1.)),),
        'Tints the existing changing inlay palette before panel lighting. Canvas material and corridor geometry remain independent.'),
    ColorTarget('corridor.glyphs', 'Corridor glyph rain', 'geometric', 'color', 'u_corridor_glyphs',
        (ColorSlot('tint','Glyph tint',(1.,1.,1.)),),
        'Tints glyph rain inside its existing falling-column mask; does not enable a disabled glyph layer.'),
    ColorTarget('planet.surface', 'Planet surface', 'canvas', 'color', 'u_planet_surface',
        (ColorSlot('tint','Surface pigment tint',(1.,1.,1.)),),
        'Tints the planet object after material substitution and Soft Dream interpretation, before diffuse lighting. Shared material pigment and moons remain independent.'),
    ColorTarget('planet.rings', 'Planet rings', 'canvas', 'roles', 'u_planet_rings',
        (ColorSlot('violet','Violet band',(.31,.19,.40)), ColorSlot('gold','Gold band',(.93,.67,.39)),
         ColorSlot('tint','Ring object tint',(1.,1.,1.))),
        'Two authored bands before canvas blend; object tint after Soft Dream and before shadow and moon occlusion.'),
    ColorTarget('stellar.sails', 'Ion Comets', 'shared', 'roles', 'u_stellar_sails',
        (ColorSlot('shell','Ion tail',(.22,.65,.82)),
         ColorSlot('edge','Comet nucleus',(1.,.42,.22)),
         ColorSlot('wake','Dust wake',(.56,.32,.95))),
        'Celestial ion comets in Galaxy, Planet Canvas, Fog and Plasma. Source pigments preserve nucleus, tails, orbit and depth.'),
    ColorTarget('galaxy.structure', 'Galaxy structure', 'galaxy', 'roles', 'u_galaxy_colors',
        (ColorSlot('core','Stellar core',(.98,.76,.50)),
         ColorSlot('arms','Spiral arms',(.36,.53,.92)),
         ColorSlot('lanes','Dust lanes',(.16,.10,.22)),
         ColorSlot('stars','Star concentrations',(.75,.87,1.)),
           ColorSlot('nursery','Rose star-forming regions',(1.,.24,.43)),
           ColorSlot('outer','Verdigris cloud regions',(.12,.85,.65))),
        'Galaxy Odyssey: core, luminous strata, absorbing dust, rose nurseries and verdigris regions. Local cloud drift and seeded destinations evolve the pigment distribution. Use palette timing for explicit hold/cycle.'),
    ColorTarget('galaxy.system', 'Procedural solar materials', 'galaxy', 'roles', 'u_journey_colors',
        (ColorSlot('sun','Primary sun',(1.,.68,.32)),
         ColorSlot('rock','Rock and moons',(.57,.28,.19)),
         ColorSlot('ocean','Planet oceans',(.08,.40,.70)),
         ColorSlot('gas','Giant cloud bands',(.65,.43,.74)),
         ColorSlot('rings','Ice and ring dust',(.83,.70,.39)),
         ColorSlot('air','Atmospheres and companion',(.36,.81,.91)),
         ColorSlot('land','Living continents',(.23,.62,.28)),
         ColorSlot('storm','Storms and warp accents',(.96,.28,.54))),
        'Seeded local materials, rotating terrain, cloud bands, ring shadows and atmospheres. Sources remain editable across travel.'),
    ColorTarget('planet.moons', 'Moons and dust wakes', 'canvas', 'roles', 'u_planet_moons',
        (ColorSlot('cyan','First moon cyan',(.08,.85,.95)), ColorSlot('rose','First moon rose',(.95,.08,.55)),
         ColorSlot('vein','First moon vein',(.85,1.,.62)), ColorSlot('red','Second moon red',(.95,.08,.015)),
         ColorSlot('orange','Second moon orange',(1.,.50,.04)), ColorSlot('blue','Second moon blue',(.08,.40,1.)),
         ColorSlot('white','Second moon white',(.85,.96,1.)), ColorSlot('shell','Third moon shell tint',(1.,1.,1.))),
        'The same animated moon material colors solid moons and their attached dust wakes; depth and eclipse stay authored.'),
    ColorTarget('sky.stars', 'Drifting starfield', 'shared', 'roles', 'u_sky_stars',
        (ColorSlot('blue','Cool stars',(.55,.72,1.)), ColorSlot('warm','Warm stars',(1.,.83,.62))),
        'Shared star roles retain each scene\'s authored cool/warm balance until that role is edited. Timing, density and layer compatibility remain authored.'),
    ColorTarget('sky.shooting', 'Shooting stars', 'shared', 'roles', 'u_sky_shooting',
        (ColorSlot('blue','Cool meteor',(.22,.65,1.)), ColorSlot('orange','Warm meteor',(1.,.36,.12))),
        'Shared shooting-star pigment in Cosmic and Water sky; streak, core, reflection and event timing stay authored.'),
    ColorTarget('material.artifacts', 'Living artifacts', 'shared', 'roles', 'u_material_artifacts',
        tuple(ColorSlot(key,label,(1.,1.,1.)) for key,label in (
            ('ocean','Ocean forms'),('crimson','Crimson and gold forms'),('crystal','Crystal forms'),
            ('fire','Fire forms'),('forest','Neon forest forms'),('electric','Electric blue forms'),
            ('edge','Morphing edge accent'))),
        'Each authored morphology family keeps its moving palette; the chosen role tints that family inside its existing mask.'),
    ColorTarget('material.alloy', 'Liquid Alloy', 'shared', 'roles', 'u_material_alloy',
        (ColorSlot('copper','Copper',(.75,.28,.10)), ColorSlot('teal','Teal',(.08,.58,.62)),
         ColorSlot('violet','Violet',(.44,.12,.72)), ColorSlot('dynamic','Animated object tint',(1.,1.,1.)),
         ColorSlot('chrome','Chrome base',(.08,.10,.14)), ColorSlot('glint','Glint',(.65,.82,.9))),
        'Fixed metal pigments plus the animated object tint. Normal, reflection, glint and rim masks stay authored.'),
    ColorTarget('material.lattice', 'Prismatic Lattice', 'shared', 'roles', 'u_material_lattice',
        (ColorSlot('wire','Wire tint',(1.,1.,1.)), ColorSlot('glow','Glow tint',(1.,1.,1.)),
         ColorSlot('facet','Facet tint',(1.,1.,1.))),
        'Three pigments multiply the existing animated hue inside the separate wire, glow and facet contributions.'),
    ColorTarget('material.echo', 'Echo Weave display', 'shared', 'roles', 'u_material_echo',
        (ColorSlot('body','Ink body tint',(1.,1.,1.)), ColorSlot('strands','Bright strands tint',(1.,1.,1.)),
         ColorSlot('ridge','Ridge tint',(1.,1.,1.))),
        'Display-stage colors only: history textures, simulation clocks and density are not reset or reseeded.'),
    ColorTarget('fx.sparkles', 'Sparkles', 'shared', 'color', 'u_fx_sparkles',
        (ColorSlot('tint','Sparkle tint',(.86,.97,1.)),),
        'Shared sparkle pigment; the star mask and musical reveal remain authored.'),
    ColorTarget('fx.flecks', 'Drifting flecks', 'shared', 'roles', 'u_fx_flecks',
        tuple(ColorSlot(key,label,(1.,1.,1.)) for key,label in (
            ('ocean','Ocean flecks'),('crimson','Crimson and gold flecks'),('crystal','Crystal flecks'),
            ('fire','Fire flecks'),('forest','Neon forest flecks'),('sun','Gold sun flecks'))),
        'Each fleck palette retains its authored gradient, density and drift; roles tint the chosen family.'),
    ColorTarget('fx.beams', 'Radial beams', 'shared', 'roles', 'u_fx_beams',
        tuple(ColorSlot(key,label,(1.,1.,1.)) for key,label in (
            ('ocean','Ocean beams'),('crimson','Crimson and gold beams'),
            ('electric','Electric blue beams'),('fire','Fire beams'))),
        'Four beam families keep the authored transient mask and music response.'),
    ColorTarget('water.sky', 'Water sky and reflection', 'water_shared', 'roles', 'u_water_sky',
        tuple(ColorSlot(key,label,(1.,1.,1.)) for key,label in (
            ('base','Distant sky'),('horizon','Horizon glow'),('dusk','Dusk light'),
            ('mist','Traveling sky mist'),('islands','Island rock'))),
        'The same sky is viewed directly and in wave reflections. These are pigment tints; silhouette and reflection direction remain authored.'),
    ColorTarget('water.sea', 'Sea surface and details', 'water_shared', 'roles', 'u_water_sea',
        tuple(ColorSlot(key,label,(1.,1.,1.)) for key,label in (
            ('transmission','Submerged transmission'),('reflection','Broad reflection'),
            ('foam','Crest foam'),('glints','Surface glints'))),
        'Separate sources inside the same wave shading; wave normals, absorption, foam masks and audio response remain authored.'),
    ColorTarget('water.rain', 'Rain and ripples', 'water_shared', 'roles', 'u_water_rain',
        (ColorSlot('rain','Rain streak tint',(1.,1.,1.)),ColorSlot('ripples','Ripple ring tint',(1.,1.,1.))),
        'These detail colors remain subject to their layer flags and separate seeded motion.'),
    ColorTarget('water.dyes', 'Liquid dyes', 'dyes', 'color', 'u_water_dyes',
        (ColorSlot('tint','Dye vein tint',(1.,1.,1.)),),
        'Tints the existing flowing dye pigment within its own coverage; vein geometry and material canvas stay authored.'),
    ColorTarget('water.currents', 'Currents', 'currents', 'roles', 'u_water_currents',
        (ColorSlot('body','Current body tint',(1.,1.,1.)),ColorSlot('threads','Fine ribbon tint',(1.,1.,1.))),
        'Body and reflected threads keep the same inverse-flow geometry and music response.'),
    ColorTarget('water.falls', 'Waterfall and cliff lip', 'waterfall', 'roles', 'u_water_falls',
        tuple(ColorSlot(key,label,(1.,1.,1.)) for key,label in (
            ('sheet','Water sheet'),('highlights','Water highlights'),
            ('stone','Cliff and banks'),('lip','Cliff lip'))),
        'Water sheet, light, stone and lip stay attached to the accepted river/fall geometry.'),
    ColorTarget('fire.sheets', 'Flame sheets', 'fire', 'roles', 'u_fire_sheets',
        (ColorSlot('body','Heat-sheet tint',(1.,1.,1.)),ColorSlot('ignition','Impact ignition tint',(1.,1.,1.))),
        'The heat gradient and impact core retain their authored brightness and event envelope.'),
    ColorTarget('fire.details', 'Fire details', 'fire_shared', 'roles', 'u_fire_details',
        (ColorSlot('coals','Coals tint',(1.,1.,1.)),ColorSlot('embers','Embers tint',(1.,1.,1.)),
         ColorSlot('seams','Hot seams tint',(1.,1.,1.)),ColorSlot('ash','Ash tint',(1.,1.,1.))),
        'Shared fire details retain their layer flags, seeded trajectories and independent lifetimes.'),
    ColorTarget('molten.flow', 'Molten flow', 'molten', 'roles', 'u_molten_flow',
        (ColorSlot('heat','Liquid heat tint',(1.,1.,1.)),ColorSlot('bank','Rock bank tint',(1.,1.,1.)),
         ColorSlot('sky','Distant sky tint',(1.,1.,1.))),
        'Liquid channels, conservative banks and silhouettes retain their geometry and response.'),
    ColorTarget('firescape.land', 'Firescape', 'firescape', 'roles', 'u_firescape_land',
        (ColorSlot('flame','Traveling flame tint',(1.,1.,1.)),ColorSlot('bark','Tree bark tint',(1.,1.,1.)),
         ColorSlot('city','Distant city tint',(1.,1.,1.)),ColorSlot('ground','Ground fire tint',(1.,1.,1.)),
         ColorSlot('sky','Night sky tint',(1.,1.,1.))),
        'Scene colors remain attached to the current growth and burn lifecycle.'),
    ColorTarget('aftershock.land', 'Aftershock terrain and plumes', 'aftershock', 'roles', 'u_aftershock_land',
        (ColorSlot('soil','Ground soil tint',(1.,1.,1.)),ColorSlot('cloud','Dust plume tint',(1.,1.,1.)),
         ColorSlot('plume','Per-site plume hue tint',(1.,1.,1.)),ColorSlot('sky','Distant sky tint',(1.,1.,1.))),
        'Soil and layered dust plumes retain their depth sorting, masks and bounded site history.'),
    ColorTarget('aftershock.events', 'Aftershock events', 'aftershock', 'roles', 'u_aftershock_events',
        (ColorSlot('dust','Dust shockwave tint',(1.,1.,1.)),ColorSlot('fire','Ground-fire tint',(1.,1.,1.)),
         ColorSlot('aurora','Aurora tint',(1.,1.,1.)),ColorSlot('flash','Inversion flash tint',(1.,1.,1.))),
        'Event colors do not change blast births, growth, decay, site recycling or flash timing.'),
    ColorTarget('air.sky', 'Air sky and earth', 'air_shared', 'roles', 'u_air_sky',
        (ColorSlot('sky','Open sky tint',(1.,1.,1.)),ColorSlot('overcast','Storm overcast tint',(1.,1.,1.)),
         ColorSlot('earth','Distant earth tint',(1.,1.,1.))),
        'Atmosphere and distant terrain retain the authored horizon, light and movement.'),
    ColorTarget('air.clouds', 'Clouds and wind ribbons', 'air_shared', 'roles', 'u_air_clouds',
        (ColorSlot('clouds','Cloud body tint',(1.,1.,1.)),ColorSlot('ribbons','Wind ribbon tint',(1.,1.,1.)),
         ColorSlot('vortex','Vortex cloud tint',(1.,1.,1.))),
        'Cloud and ribbon pigments leave billow shape, travel and detail flags intact.'),
    ColorTarget('air.lightning', 'Lightning and aurora', 'air_shared', 'roles', 'u_air_lightning',
        (ColorSlot('bolts','Lightning tint',(1.,1.,1.)),ColorSlot('aurora','Storm aurora tint',(1.,1.,1.)),
         ColorSlot('afterglow','Vortex afterglow tint',(1.,1.,1.))),
        'Electrical colors keep their authored event paths, impact gates and decay.'),
    ColorTarget('air.balloons', 'Windstream balloons', 'windstreams', 'roles', 'u_air_balloons',
        (ColorSlot('fabric','Balloon fabric tint',(1.,1.,1.)),ColorSlot('glint','Balloon glint tint',(1.,1.,1.))),
        'Balloon fabric and highlights retain their depth order, spin and music response.'),
    ColorTarget('air.citadel', 'Sky Citadel', 'citadel', 'roles', 'u_air_citadel',
        (ColorSlot('stone','Castle stone tint',(1.,1.,1.)),ColorSlot('windows','Window and tracery tint',(1.,1.,1.)),
         ColorSlot('earth','Earth disk tint',(1.,1.,1.)),ColorSlot('celebration','Beams and fireworks tint',(1.,1.,1.))),
        'Castle shape, planet disk and celebration timing remain authored.'),
    ColorTarget('air.daddy', 'Daddy Long Legs experiment', 'vortex', 'color', 'u_air_daddy',
        (ColorSlot('tint','Web tint',(1.,1.,1.)),),
        'Only visible when the shelved Daddy Long Legs experiment is explicitly enabled; the color edit does not enable it.'),
    ColorTarget('earth.sky', 'Earth sky', 'earth_shared', 'roles', 'u_earth_sky',
        (ColorSlot('sky','Sky and horizon tint',(1.,1.,1.)),ColorSlot('weather','Distant cloud tint',(1.,1.,1.)),
         ColorSlot('sunset','Dune sunset tint',(1.,1.,1.))),
        'Distant atmosphere remains behind solid terrain and follows the authored travel clock.'),
    ColorTarget('earth.minerals', 'Earth mineral details', 'earth_shared', 'roles', 'u_earth_minerals',
        (ColorSlot('veins','Mineral vein tint',(1.,1.,1.)),ColorSlot('glints','Mineral glint tint',(1.,1.,1.))),
        'Veins and glints keep their detail gates, world coordinates and musical response.'),
    ColorTarget('dunes.land', 'Dunes and worm', 'dunes', 'roles', 'u_dunes_land',
        (ColorSlot('sand','Dune sand tint',(1.,1.,1.)),ColorSlot('worm','Worm body tint',(1.,1.,1.))),
        'The worm breach timing, burial, silhouette and terrain geometry remain authored.'),
    ColorTarget('strata.land', 'Strata', 'strata', 'roles', 'u_strata_land',
        (ColorSlot('sediment','Sedimentary layers tint',(1.,1.,1.)),ColorSlot('aurora','Distant aurora tint',(1.,1.,1.))),
        'The stone bedding and distant ribbon stay attached to their source masks.'),
    ColorTarget('cavern.land', 'Crystal Cavern', 'cavern', 'roles', 'u_cavern_land',
        (ColorSlot('stone','Cavern stone tint',(1.,1.,1.)),ColorSlot('crystals','Crystal tint',(1.,1.,1.)),
         ColorSlot('light','Crystal light tint',(1.,1.,1.))),
        'Crystal placement, geometry and glow response remain authored.'),
    ColorTarget('fog.vapor', 'Fog and gas vapor', 'fog_shared', 'roles', 'u_fog_vapor',
        (ColorSlot('nebula','Nebula vapor tint',(1.,1.,1.)),ColorSlot('marsh','Marsh vapor tint',(1.,1.,1.)),
         ColorSlot('pressure','Pressure vapor tint',(1.,1.,1.))),
        'Three scattering pigments retain the authored density integration and front-to-back depth.'),
    ColorTarget('fog.internal', 'Internal fog light', 'fog_shared', 'roles', 'u_fog_internal',
        (ColorSlot('threads','Internal light threads tint',(1.,1.,1.)),ColorSlot('pulse','Traveling pulse tint',(1.,1.,1.))),
        'Internal light remains gated by the detail flags and musical response.'),
    ColorTarget('marsh.solids', 'Marsh solids', 'marsh', 'roles', 'u_marsh_solids',
        (ColorSlot('ground','Ground and path tint',(1.,1.,1.)),ColorSlot('stones','Standing stones tint',(1.,1.,1.)),
         ColorSlot('moss','Stone moss tint',(1.,1.,1.))),
        'Solid depth and the existing crack and moss history remain authored.'),
    ColorTarget('marsh.ghostlights', 'Marsh ghostlights', 'marsh', 'roles', 'u_marsh_ghostlights',
        (ColorSlot('orbs','Moving lights tint',(1.,1.,1.)),ColorSlot('reflections','Ground reflection tint',(1.,1.,1.))),
        'Orb flight lanes, flicker and reflections retain their source masks.'),
    ColorTarget('plasma.sky', 'Plasma sky', 'plasma_shared', 'roles', 'u_plasma_sky',
        (ColorSlot('background','Dark sky tint',(1.,1.,1.)),ColorSlot('stars','Star and asterism tint',(1.,1.,1.))),
        'Star trajectories, lensing and detail flags remain authored.'),
    ColorTarget('magnetic.field', 'Magnetic Field', 'magnetic', 'roles', 'u_magnetic_field',
        (ColorSlot('core','Charged core tint',(1.,1.,1.)),ColorSlot('loops','Field loop tint',(1.,1.,1.)),
         ColorSlot('sparks','Loop pulse tint',(1.,1.,1.))),
        'Opaque core and emitting loops retain their orbit, occlusion and music response.'),
    ColorTarget('arcs.charge', 'Electric Arcs', 'arcs', 'roles', 'u_arcs_charge',
        (ColorSlot('nodes','Charge node tint',(1.,1.,1.)),ColorSlot('arcs','Discharge tint',(1.,1.,1.)),
         ColorSlot('sparks','Spark and branch tint',(1.,1.,1.))),
        'Nodes and discharges keep their seeded paths, phase and depth tests.'),
    ColorTarget('auroral.curtains', 'Auroral Curtains', 'auroral', 'roles', 'u_auroral_curtains',
        (ColorSlot('sheets','Curtain sheet tint',(1.,1.,1.)),ColorSlot('pulses','Traveling pulse tint',(1.,1.,1.))),
        'Curtain transmission, folds, thin threads and event envelope remain authored.'),
)


TREATMENT_COLORS = {
    'material.ink': ('Ink Archipelago', 'u_ink_colors',
        (('deep','Ink',(.012,.023,.032)),('body','Pigment',(.12,.54,.48)),('vein','Veins',(.87,.58,.32)),('light','Pearl',(.78,.86,.72)))),
    'material.silk': ('Interference Silk', 'u_silk_colors',
        (('deep','Ground',(.025,.015,.06)),('body','Wave one',(.47,.19,.68)),('vein','Wave two',(.13,.65,.73)),('light','Crests',(.94,.70,.58)))),
    'material.mosaic': ('Cellular Mosaic', 'u_mosaic_colors',
        (('deep','Grout',(.008,.014,.026)),('body','Cell one',(.78,.26,.12)),('vein','Cell two',(.08,.38,.61)),('light','Seams',(.80,.71,.38)))),
}
TARGETS += tuple(ColorTarget(key,label,'shared','roles',uniform,
    tuple(ColorSlot(role,name,rgb) for role,name,rgb in roles),
    'Source pigment before world shading. Material selection, coordinates and audio response remain independent.')
    for key,(label,uniform,roles) in TREATMENT_COLORS.items())


TARGETS += (
    ColorTarget('enveloper.prism','Prism Assembly','shared','roles','u_prism_colors',
        (ColorSlot('cool','Cool facet',(.72,.90,1.)),ColorSlot('warm','Warm facet',(1.,.72,.83))),
        'Subtle multiplicative facet edges on the completed image; never an additive flash.'),
    ColorTarget('enveloper.digital','Digital Bloom','shared','roles','u_digital_colors',
        (ColorSlot('shadow','Shadow tint',(.64,.77,.94)),ColorSlot('highlight','Highlight tint',(.93,.83,.61))),
        'Tints quantized source imagery. Black stays black; original scene remains recognizable.'),
    ColorTarget('enveloper.memory','Chromatic Memory','shared','roles','u_memory_colors',
        (ColorSlot('red','Red-memory tint',(1.,.83,.75)),ColorSlot('green','Green-memory tint',(.76,1.,.87)),ColorSlot('blue','Blue-memory tint',(.80,.84,1.))),
        'Time-based tints of short full-image echoes; independent of Echo Weave material history.'),
)


STATE_COLOR_SCENE = ('blend','organic','geometric','cosmic','transition','canvas',
    'water','sea','dyes','rain','waterfall','membrane','roots','currents',
    'fire','molten','fire_cycle','firescape','aftershock',
    'windstreams','stormfront','vortex','citadel','air',
    'dunes','strata','cavern','earth','nebula','marsh','pressure','fog',
    'magnetic','arcs','auroral','plasma','galaxy')

_CYCLE_FORMS = {
    'organic': ('membrane','roots'), 'cosmic': ('canvas',), 'transition': ('canvas',),
    'water': ('sea','dyes','rain','waterfall','currents'),
    'fire_cycle': ('fire','molten','firescape','aftershock'),
    'air': ('windstreams','stormfront','vortex','citadel'),
    'earth': ('dunes','strata','cavern'),
    'fog': ('nebula','marsh','pressure'),
    'plasma': ('magnetic','arcs','auroral'),
}
_WATER_FORMS = frozenset(_CYCLE_FORMS['water'])
_FIRE_FORMS = frozenset(_CYCLE_FORMS['fire_cycle'])
_AIR_FORMS = frozenset(_CYCLE_FORMS['air'])
_EARTH_FORMS = frozenset(_CYCLE_FORMS['earth'])
_FOG_FORMS = frozenset(_CYCLE_FORMS['fog'])
_PLASMA_FORMS = frozenset(_CYCLE_FORMS['plasma'])
_SHARED_COMPAT = {
    'galaxy.system': {'Living Atlas': ('#FFAE52','#914730','#1466B3','#A66EBD','#D4B363','#5CCFE8','#3B9E47','#F5478A'),
                   'Ember Archipelago': ('#FFCE83','#AD5068','#237A8E','#BD8357','#DED5A9','#899FEA','#769A54','#EE6850'),
                   'Opal Frontier': ('#E8A5DD','#6D738A','#2273BC','#499991','#C9BFF0','#8EE1CB','#A3AC55','#F18C4D')},
 'stellar.sails': {'galaxy','canvas','nebula','marsh','pressure','magnetic','arcs','auroral'},
    'sky.stars': {'galaxy','nebula','marsh','pressure','magnetic','arcs','auroral','canvas','windstreams','stormfront','vortex','citadel',
                  'dunes','strata','cavern'},
    'sky.shooting': {'canvas','sea','dyes','rain','waterfall','currents'},
    'fx.sparkles': {'membrane','roots','geometric','canvas'},
    'fx.flecks': {'membrane','roots','geometric','canvas'},
    'fx.beams': {'membrane','roots','geometric','canvas'},
}


def targets_for(scene):
    if scene == 'blend': return tuple(target for target in TARGETS if target.scene != 'galaxy')
    if scene == 'galaxy': return tuple(target for target in TARGETS if target.scene == 'galaxy' or target.id in ('stellar.sails','sky.stars'))
    forms = _CYCLE_FORMS.get(scene, (scene,))
    extra = (('water_shared',) if any(form in _WATER_FORMS for form in forms) else ()) + (
        ('fire_shared',) if any(form in _FIRE_FORMS for form in forms) else ()) + (
        ('air_shared',) if any(form in _AIR_FORMS for form in forms) else ()) + (
        ('earth_shared',) if any(form in _EARTH_FORMS for form in forms) else ()) + (
        ('fog_shared',) if any(form in _FOG_FORMS for form in forms) else ()) + (
        ('plasma_shared',) if any(form in _PLASMA_FORMS for form in forms) else ())
    return tuple(target for target in TARGETS if target.scene in forms + extra or
        (target.scene == 'shared' and any(form in _SHARED_COMPAT.get(target.id, forms)
                                           for form in forms)))


def rgb_hex(rgb):
    return '#' + ''.join(f'{round(channel*255):02X}' for channel in rgb)


def hex_rgb(color):
    if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        raise ValueError('Use a color in #RRGGBB form.')
    return tuple(int(color[i:i+2],16)/255. for i in (1,3,5))


def resolved_slots(target, overrides):
    values = overrides.get(target.id, {})
    return tuple((hex_rgb(values[slot.id]['color']) if 'color' in values.get(slot.id,{}) else slot.rgb,
                  values.get(slot.id,{}).get('start',slot.start),
                  values.get(slot.id,{}).get('end',slot.end)) for slot in target.slots)


def validate_colors(data):
    if not isinstance(data, dict) or len(data)>len(TARGETS):
        raise ValueError('Color overrides must contain declared targets only.')
    result = {}
    for key, values in data.items():
        target = next((target for target in TARGETS if target.id == key), None)
        if target is None or not isinstance(values,dict): raise ValueError('Unknown color target.')
        slots = {slot.id:slot for slot in target.slots}
        cleaned = {}
        for slot_id, fields in values.items():
            if slot_id == '_cycle': continue
            if slot_id not in slots or not isinstance(fields,dict): raise ValueError('Unknown color role.')
            slot = slots[slot_id]
            allowed = {'color'} if slot.start is None else {'color','start','end'}
            if fields.keys()-allowed: raise ValueError('Unsupported color control.')
            item = {}
            if 'color' in fields:
                hex_rgb(fields['color']); item['color'] = fields['color'].upper()
            for field in ('start','end'):
                if field in fields:
                    value = fields[field]
                    if type(value) not in (float,int) or not math.isfinite(value) or not 0<=value<=1:
                        raise ValueError('Gradient positions must be finite numbers from 0 to 1.')
                    item[field] = float(value)
            if item: cleaned[slot_id] = item
        if cleaned: result[key] = cleaned
        if target.kind == 'staged_gradient':
            ranges = [(start,end) for _,start,end in resolved_slots(target,result) if start is not None]
            if any(end-start<.001 for start,end in ranges) or any(
                    a[0]>=b[0] or a[1]>=b[1] for a,b in zip(ranges,ranges[1:])):
                raise ValueError('Gradient transitions need ordered starts/ends, each at least 0.001 apart. Overlap is supported.')
        if '_cycle' in values:
            cycle=values['_cycle']
            if not isinstance(cycle,dict) or set(cycle)-{'mode','hold','fade','setups'}:
                raise ValueError('Invalid palette cycle.')
            if cycle.get('mode') not in ('hold','cycle'):raise ValueError('Choose Hold or Cycle.')
            hold,fade=cycle.get('hold',12.),cycle.get('fade',4.)
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in (hold,fade)) or not 1<=hold<=300 or not 0<=fade<=60:
                raise ValueError('Palette hold is 1-300 seconds; transition is 0-60 seconds.')
            setups=cycle.get('setups')
            if not isinstance(setups,list) or not 0<=len(setups)<=4 or (cycle['mode']=='cycle' and len(setups)<2):
                raise ValueError('Store 2-4 setups to cycle; Hold can retain up to four.')
            clean_setups=[]
            for setup in setups:
                if not isinstance(setup,dict) or '_cycle' in setup:raise ValueError('Cycle setups contain roles only.')
                clean_setups.append(validate_colors({key:setup}).get(key,{}))
            result.setdefault(key,{})['_cycle']=dict(mode=cycle['mode'],hold=float(hold),fade=float(fade),setups=clean_setups)
    if len(json.dumps(result,separators=(',',':')).encode('utf-8'))>14000:
        raise ValueError('Color setup exceeds the bounded live payload; remove unused stored cycles.')
    return result


def parse_colors(text):
    return validate_colors(json.loads(text))


def scene_colors(data, scene):
    return {target.id:data[target.id] for target in targets_for(scene) if target.id in data}


def color_uniforms(data, active, seconds=0.):
    # Boolean compatibility supports the original Roots-only shader fixture.
    active_ids = {target.id for target in targets_for('roots')} if active is True else (
        set() if active is False else set(active))
    result = {}
    for target in TARGETS:
        values=data.get(target.id,{})
        cycle=values.get('_cycle')
        cycling=bool(cycle and cycle['mode']=='cycle')
        enabled=bool(set(values)-{'_cycle'}) or cycling
        result[target.uniform+'_on'] = int(target.id in active_ids and enabled)
        slots = resolved_slots(target,data)
        if cycling:
            period=cycle['hold']+cycle['fade'];phase=max(0.,seconds)/period
            index=int(phase)%len(cycle['setups']);age=(phase%1.)*period
            blend=max(0.,min(1.,(age-cycle['hold'])/max(cycle['fade'],1e-9)))
            blend=blend*blend*(3.-2.*blend)
            a=resolved_slots(target,{target.id:cycle['setups'][index]})
            b=resolved_slots(target,{target.id:cycle['setups'][(index+1)%len(cycle['setups'])]})
            slots=tuple((tuple(x+(y-x)*blend for x,y in zip(left[0],right[0])),
                None if left[1] is None else left[1]+(right[1]-left[1])*blend,
                None if left[2] is None else left[2]+(right[2]-left[2])*blend) for left,right in zip(a,b))
        if target.kind == 'color': result[target.uniform] = slots[0][0]
        else:
            result[target.uniform] = tuple(slot[0] for slot in slots)
            if target.kind == 'staged_gradient':
                result[target.uniform+'_ranges'] = tuple((start,end) for _,start,end in slots[1:])
    return result


def color_preset(name, scene, overrides):
    if not isinstance(name,str) or not 1<=len(name.strip())<=80:
        raise ValueError('Name the color preset using 1–80 characters.')
    if not targets_for(scene): raise ValueError('Unsupported preset scene.')
    return dict(kind='zerawave-color-preset',version=1,name=name.strip(),scene=scene,
                targets=scene_colors(validate_colors(overrides),scene))


def validate_preset(data):
    if not isinstance(data,dict) or data.get('kind')!='zerawave-color-preset' or type(data.get('version')) is not int or data.get('version')!=1:
        raise ValueError('This is not a supported color preset (target assignments, not a palette).')
    result = color_preset(data.get('name'),data.get('scene'),data.get('targets'))
    if result['targets'] != validate_colors(data['targets']): raise ValueError('Preset targets belong to another scene.')
    return result


# Families match the target's declared roles; gradient structures never cross targets.
PALETTE_FAMILIES = {
 'galaxy.structure': {'Copper Comet': ('#FBC281','#377CCB','#21162F','#B2EAFE','#FF3D6E','#1FD9A6'),
                      'Orchid Eclipse': ('#E8A1CE','#9550DB','#171D34','#75E8D7','#F5AA5D','#328BCC'),
                      'Verdigris Dawn': ('#FFE0A0','#279F91','#1D2236','#D4F6D2','#F07FAF','#6585EE')},
 'galaxy.system': {'Living Atlas': ('#FFAE52','#914730','#1466B3','#A66EBD','#D4B363','#5CCFE8','#3B9E47','#F5478A'),
                   'Ember Archipelago': ('#FFCE83','#AD5068','#237A8E','#BD8357','#DED5A9','#899FEA','#769A54','#EE6850'),
                   'Opal Frontier': ('#E8A5DD','#6D738A','#2273BC','#499991','#C9BFF0','#8EE1CB','#A3AC55','#F18C4D')},
 'stellar.sails': {'Copper Comet': ('#377CCB','#FBC281','#B2EAFE'),
                   'Orchid Eclipse': ('#9550DB','#E8A1CE','#75E8D7'),
                   'Verdigris Dawn': ('#279F91','#FFE0A0','#D4F6D2')},
 'sky.stars': {'Copper Comet': ('#B2EAFE','#FBC281'),
               'Orchid Eclipse': ('#75E8D7','#E8A1CE'),
               'Verdigris Dawn': ('#D4F6D2','#FFE0A0')},
 'material.ink': {'Saffron parchment': ('#11131F','#BA6935','#447D85','#E8D7A1'), 'Deep lagoon': ('#040F19','#146765','#9D637F','#9DCCBA')},
 'material.silk': {'Opal dusk': ('#140E26','#6E4DAD','#7BAE97','#E9C6B0'), 'Copper tide': ('#161223','#B85D48','#2F8CA4','#D8B86C')},
 'material.mosaic': {'Cobalt garden': ('#080E1D','#257D8B','#8B4F9D','#B4CC8D'), 'Terracotta glass': ('#160F13','#B96239','#507889','#DEAF65')},
 'enveloper.prism': {'Pearl rose': ('#C5DCD8','#E5B1C9'), 'Sea amber': ('#82BCC6','#E8C38A')},
 'enveloper.digital': {'Phosphor dusk': ('#759789','#D1CE92'), 'Blue copper': ('#758EB1','#DAB38F')},
 'enveloper.memory': {'After-rain': ('#D4B6CB','#A2D6BE','#ABC5ED'), 'Warm archive': ('#E5B297','#C3CD9B','#B1B1D8')},
}


def galaxy_authored_colors(data, state, seed=7301, index=0):
    """Transient authored journey; never writes session data or overrides edits.

    Related families map artistic roles explicitly, not by slot count. Any
    role overrides stay fixed; unedited roles stay authored. An explicit target
    cycle/hold parks the target.
    """
    if state!=36:return data
    result=dict(data)
    # Spatially distinct pigments evolve with local clouds/materials; explicit
    # inspector cycles remain available without a synchronized whole-screen wash.
    from procedural_cosmos import authored_pigments
    palettes=authored_pigments(seed,index)
    for (target,colors) in zip(('galaxy.structure','galaxy.system'),palettes):
        declaration=next(t for t in TARGETS if t.id==target)
        authored={slot.id:dict(color=color) for slot,color in zip(declaration.slots,colors)}
        manual=data.get(target)
        if manual is None:result[target]=authored
        elif '_cycle' not in manual:result[target]={**authored,**manual}
        # Explicit target cycle/hold controls retain their existing semantics.
    return result


def family_setup(target,name):
    if isinstance(target,str):target=next(t for t in TARGETS if t.id==target)
    if name=='Authored':return {}
    colors=PALETTE_FAMILIES.get(target.id,{}).get(name)
    if colors is None or len(colors)!=len(target.slots):raise ValueError('Palette family does not match this target roles.')
    return {slot.id:dict(color=color) for slot,color in zip(target.slots,colors)}
