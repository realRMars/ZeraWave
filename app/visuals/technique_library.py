from transition_catalog import RECIPES,description as relationship_description
"""Read-only discovery index. Runtime worlds/effects remain owned by their catalogs."""
from preview_layers import EFFECTS, EXPERIMENTS

SHADER = 'app/visuals/shaders/dream.frag'
# title, search vocabulary / purpose, source symbol. These are building blocks,
# not independently toggleable effects or promises of generic reusable APIs.
TECHNIQUES = (
    ('Mineral Lamellae','Fine mineral contour etching and sparse sparkle grains, shared by Tidal Strata, Recursive Atrium and Honeycomb Garden. Editable source pigments and independent Flux/Sparkle tuning per form; amount zero bypasses.','lamellae'),
    ('Recursive Pulse','Three nested local wave scales deform the same material coordinates in all three Fractal forms. Independent Flux/Impact tuning and bounded amount preserve the authored quiet motion.','recursive_pulse'),
    ('Rooftop Anchors','One tower descriptor aligns varied masonry, roof-mounted flag masts, luminous lasers and world-space firework launches. Coherent free-end cloth waves and localized coronation peaks/fading sparks.','citadel_tower'),
    ('Cavern Travel Curve','Seeded straight mineral passages linked by smooth rounded bends; variable left/right routes include consecutive same-direction turns. Shared camera, chamber and anchored-event coordinates; bounded persistent formation placement.','cavern_axis'),
    ('River Carry','Global connected regional current carries outgoing geometry and pigment into a new world; bounded directional displacement, per-fragment ownership and exact endpoints. Inherits both worlds live colors, no overlay pigment.','main_carry'),
    ('Facet Relay','Coarse staggered regions exchange world ownership with small carried image facets. All Main families; original geometry/pigments remain, bounded displacement and narrow overlap.','main_region'),
    ('Depth Aperture','Off-axis depth opening draws outgoing content toward an incoming region; no black shutter or full-screen wash. Exact endpoints, spatial-only material inheritance.','main_weights'),
    ('Branching Iris','Recursive radial forks open an irregular structural iris and curl endpoint geometry. Any two Main forms, including Fractal; independent selected-band bass/flux/movement/impact response and a separate duration timer. Inherits endpoint pigments.','tr_branch_iris'),
    ('Flowing Fold','Interleaved flowing ribbons fold and advect outgoing/incoming geometry in opposite directions. Any two Main forms, including Fractal; independent selected-band audio response, exact endpoints and separate duration timer. Inherits endpoint pigments.','tr_flow_fold'),
    ('Current and Cooling Memory','Persistent low-band pressure and mid-band shear, high seam shimmer, four world-anchored selected vents with downstream heat and eighteen-second cooling deposits. Existing branching river and horizon retained; editable source pigments and Fire/Blend amount.','molten_memory'),
    ('Ghostlight Memory','Individual roadside lights hold selected musical events, grounded reflection trails and local vapor rings. Four six-second histories; shared Flux Memory attack/release, editable source pigments, Fog/Blend amount.','marsh_meta'),
    ('Veil Ripple Memory','Six layered folded sheets with bounded material-space hit ripples, lingering colored wakes, sustained flow and independent fine-fiber highlights. Folded Aurora (Experimental) reuses Flux Memory; editable gradients and Plasma profile amount control.','auroral_veil'),
    ('Stormglass Charge Relay','Nine etched stormglass junctions on eight chart routes; selected charge travels through a junction to a neighbor, leaving local glow and a fading conductive trace. Shared bounded Flux Memory, Stormglass Network (Experimental), Plasma profile amount control; artistic discharge.','arc_constellation'),
    ('Flux Memory','Four bounded selected-sector charge fronts, six-second afterglow and transient neighbor links. Sustained field pressure and release; artistic magnetic interpretation. Lodestone Field (Experimental) authored; Plasma profile amount control. Original Main forms keep their legacy response.','magnetic_cached_field'),
    ('Tower Cadence', 'Four bounded source-selected tower events; five-second launch/burst/afterglow memory, wind attack/release and reproducible return variations. Window groups, tower beacons and signal panels have independent musical roles. Authored Citadel; amount control in Air/Blend.', 'citadel_tower_light'),
    ('Windborne Signal Panels', 'World-space silk lattice panels anchored on Citadel towers, depth-tested against the existing castle trace. Integrated wind phase and damped hit flutter; six editable architectural pigments. No extra tower trace or screen overlay.', 'citadel_panels'),
    ('Mineral Resonance', 'Analytically damped visual spring and four bounded traveling impact fronts; world-anchored selected-cluster afterglow, localized living facets with persistent settling, independent sustained/highlight roles and editable mineral palette families. Cavern authored; opt-in other Earth surfaces. Artistic response, not measured crystal physics.', 'mineral_front'),
    ('Cached chamber formations', '192 stable original cell recipes streamed through one24KiB nearest descriptor texture. Authored irregular quartz companions and intergrown fluorite, broken termination planes, distinct cloudy/fractured versus cleaved-core materials. Conservative crystal bounds and opaque rock depth, renderer-owned cleanup; no texture history or expanding topology.', 'cavern_formation'),
    ('Galaxy Odyssey depth', 'Seeded nested scales, centered survey, adaptive actual-subject camera routes, zero-to-eight planets, unequal binary stars and coherent destination reveal. Deliberate visit ordinals and13-slot recent-palette avoidance, seeded local pigments and distinct orbital shells; full or short Studio entries. Bounded descriptors, no texture history', 'isolated_galaxy_scene'),
    ('Stellar Gravity Well', 'Shaded stellar bowl with source-driven bending resonance rings and localized body depressions and coherent embedded companion/planet routes; Galaxy layer with editable amount. Authored optical embedding, not a gravity solver; inherits local solar materials.', 'journey_gravity'),
    ('Resonance Fronts', 'Bounded traveling onset rings deform the authored field and excite local matter. Continuous integrated phase, visible energy loss; existing Galaxy gravity amount/source pigments, no new physics solver.', 'journey_field_wave'),
    ('Accretion Lens', 'Spherical dark void, curved bright photon rim and thick blended emitting spiral strata. Stylized color bending and positive audio-driven spin, not relativistic simulation.', 'journey_galaxy'),
    ('Procedural solar materials', 'Seven seeded surface languages: fractured, ocean, gas, ringed gas, ice, dunes and luminous mineral. Per-body texture/pigment mixtures, seamless spherical flow driven by accumulated positive motion, traveling onset echoes; editable source roles.', 'journey_surface'),
    ('Local stellar resonance', 'Existing bass/flux/highs pressure, bounded onset events, smooth convective photospheres, rare seeded oblique pulsar proxies, magnetic stellar ejections, surface excitation and polar orbital wakes. Independent of the camera; no new audio analysis.', 'journey_echo'),
    ('Restrained stellar hierarchy', 'Galaxy directional far/fine and sparse-anchor fields; independently seeded size, spectrum, luminance and subtle asynchronous twinkle. Shared editable cool/warm roles.', 'journey_sky'),
    ('Dimensional destination warp', '72 thin fast perspective tails, sparse depth-separated peripheral cloud banks, dark destination channel and colored passage without a duplicate Main warp and coherent seeded destination reveal; also used by forced short Main handoffs.', 'journey_warp'),
    ('Ion Comets', 'Celestial nuclei, ion tails and curved dust wakes. Stable stellar_sails session ID; opt-in through Shared FX in Planet Canvas, Fog and Plasma.', 'stellar_sails'),
    ('Parallax Shoal', 'Three depth-separated stellar fields with musical shimmer. Galaxy authored; opt-in in Planet Canvas, Fog and Plasma. Shared star pigments.', 'parallax_shoal'),
    ('Shared shooting stars', 'Direction-space meteor trails shared by Sea sky and wave reflections, with optional Cosmic use. Controlled through Sky effects.', 'shooting_star_radiance'),
    ('Echo Weave history', 'Persistent dye fields become strands. Renderer.update_echo owns history buffers; the update shader transports the field.', 'echo_material'),
    ('Musical color accents', 'Selective saturation and brightness accents preserve dark space while music brings pigment forward.', 'musical_material'),
    ('Planet material gathering', 'Project the shared canvas onto the planet surface while preserving its sphere geometry.', 'isolated_cosmic_scene'),
    ('Spatial flow', 'Stretch material coordinates through tunnel, fractal folds and horizon flow without moving solid geometry.', 'spatial_carrier'),
    ('Continuous stars', 'Drifting stars and musical streaks; the renderer maintains a separate continuous star clock.', 'cosmic_star_layer'),
    ('Corridor perspective', 'Curved perspective passage shared by Neon corridor and the Stormfront cloud vault.', 'geometric_surface'),
    ('Water currents', 'Coherent flow and local shear for moving liquid pigment; procedural, not a fluid solver.', 'water_current'),
    ('Surface waves', 'Layered water height, pressure and selective highlights.', 'water_height'),
    ('Waterfall projection', 'River, cliff lip and falling sheet share a perspective surface.', 'waterfall_surface'),
    ('Growing landscapes', 'Procedural tree growth and decay in Firescape; audio-driven travel is owned by the renderer.', 'firescape_tree'),
    ('Bounded blast events', 'Eight Aftershock sites with continuing onset births, .65-second oldest retirement, depth-sorted clouds and ground-only inversion; bounded renderer lifecycle.', 'blast_ring'),
    ('Castle depth', 'Full-resolution cached castle depth with rotating view and foreground/background obstruction for tower lights; bounded renderer-owned meshes and resize cleanup.', 'air_castle_map'),
    ('Solid terrain', 'Earth terrain and worm distance queries; keep solid surfaces opaque.', 'earth_map'),
    ('Volume and solids', 'Fog density composited with solid terrain; translucency is intentional for vapor.', 'fog_scene'),
    ('Charged filaments', 'Plasma loops, arcs and particles with distinct forms and audio response.', 'plasma_scene'),
    ('Regional handoffs', 'Moving boundaries let worlds meet through different regions instead of uniform crossfades.', 'handoff_front'),
)


def entries(world_tree):
    rows = [dict(id='world:blend', title='Main blend', kind='Worlds & forms',
                 summary='Music-responsive visits across worlds. Materials cycle independently. Choose this to review integration.',
                 selection=[], sources=['app/visuals/renderer.py:choose_world'])]
    rows.append(dict(id='technique:forced-basin-modes',title='Forced standing basin modes',kind='Techniques',summary='Bounded rectangular gravity-capillary modes, sample-held exact linear projection, coherent phase and distinct optical amplification. Not Faraday/full fluid; reusable PCM excitation contract.',sources=['app/visuals/cymatics.py:Basin','app/audio/oscillator.py:Oscillator','app/audio/frequency_bands.py:FrequencyBands']))
    def visit(children, path, labels):
        for key, node in children.items():
            here, names = path + [key], labels + [node['label']]
            rows.append(dict(id='world:' + '/'.join(here), title=' / '.join(names), kind='Worlds & forms',
                summary=('Select this branch to cycle its forms.' if node.get('children') else 'Select this form to hold it for review.') +
                        ' Existing layer settings are preserved; choosing an entry does not start playback.',
                selection=here, sources=['app/visuals/studio.py:WORLD_TREE']))
            visit(node.get('children', {}), here, names)
    visit(world_tree, [], [])
    for key, (label, category, worlds) in EFFECTS.items():
        rows.append(dict(id='effect:' + key, title=label,
            kind='Experiments' if key in EXPERIMENTS else 'Effects & materials',
            summary=(relationship_description(key)+' ' if key in RECIPES else '')+f'{category}. Available in: {", ".join(worlds)}. '
                    'Use Effects & layers to add, solo, order or cycle this item. Availability depends on the selected form and music.' +
                    (' Dormant unless explicitly enabled.' if key in EXPERIMENTS else ''),
            sources=['app/visuals/preview_layers.py:EFFECTS'], tags=key))
    for title, summary, symbol in TECHNIQUES:
        rows.append(dict(id='technique:' + symbol, title=title, kind='Techniques', summary=summary +
            ' This is an implementation building block, not a standalone layer switch.', sources=[('app/visuals/shaders/fractals.frag' if symbol in ('lamellae','recursive_pulse') else 'app/visuals/shaders/auroral_veil.frag' if symbol=='auroral_veil' else 'app/visuals/shaders/arc_constellation.frag' if symbol=='arc_constellation' else SHADER) + ':' + ('main_region' if symbol in ('tr_branch_iris','tr_flow_fold') else symbol)]))
    rows.append(dict(id='technique:cached-ghostlight-lanes',title='Cached Ghostlight Lanes',kind='Techniques',summary='Fourteen lane-clear ghostlights over seven roadside cells, 42 vec4 uniforms/672B. Stable world-cell selection, source-driven settling, ground trails and local vapor; existing terrain and solid depth retained.',sources=['app/visuals/marsh_response.py:LampCache.build','app/visuals/shaders/dream.frag:fog_lamp']))
    rows.append(dict(id='technique:layered-veil-material',title='Layered Veil Material',kind='Techniques',
        summary='Analytic folded hems, rising fine fibers and ordered thin-sheet transmission. Six editable artistic pigments, slow phase/return palette evolution and a velvet horizon. Uses the existing bounded scene surface with resize/minimize/cleanup guards.',
        sources=['app/visuals/shaders/auroral_veil.frag:auroral_veil','app/visuals/auroral_memory.py:VeilPalette.sample','app/visuals/arc_constellation.py:ArcStage']))
    rows.append(dict(id='technique:cached-asterism-chart',title='Cached Asterism Chart',kind='Techniques',
        summary='Authored nine-node branching topology with twelve 17-vertex projected paths, 48 group bounds and one 3264-byte nearest descriptor texture. Per-frame construction, persistent junction identity and renderer-owned cleanup; no per-pixel topology rebuilding. A small scene pass bounds compiler expansion; its single RGBA16F surface is lazy, resizes and releases with the renderer.',
        sources=['app/visuals/arc_constellation.py:ArcNetwork.build','app/visuals/renderer.py:Renderer.render','app/visuals/shaders/arc_constellation.frag:arc_constellation']))
    rows.append(dict(id='technique:projected-field-paths', title='Projected Field Bundles', kind='Techniques',
        summary='12x49 projected vertices in one9408B nearest descriptor texture with96 conservative group bounds. Field construction once per frame, depth against a faceted split lodestone. Renderer-owned resize/restart/cleanup; Magnetic Bloom consumes this bounded geometry foundation.',
        sources=['app/visuals/magnetic_response.py:FieldPaths.build','app/visuals/renderer.py:Renderer.render','app/visuals/shaders/dream.frag:magnetic_cached_field']))
    rows.append(dict(id='technique:seeded-system-recipes', title='Seeded system recipes', kind='Techniques',
        summary='Pure bounded descriptors and adaptive camera routes: zero, one, two, four or eight bodies, orbital traits, materials and single/binary stars. Galaxy currently consumes these recipes; reusable Python foundation, not an astronomical solver or a standalone layer.',
        sources=['app/visuals/procedural_cosmos.py:destination','app/visuals/procedural_cosmos.py:system_pose']))
    rows += [dict(id='workflow:review', title='Test and review a change', kind='Workflow',
        summary='Isolate a form, choose a track, inspect quiet and sustained strong passages, then review Main blend. Track replay is silent. Captures alone do not verify motion.',
        sources=['DEVELOPMENT_STUDIO.md', 'app/visuals/replay_test.py', 'app/visuals/shader_test.py']),
        dict(id='workflow:extend', title='Reuse before adding a technique', kind='Workflow',
        summary='Search this library and the technique map. Reuse a suitable existing function; preserve stable effect IDs and session compatibility. A building block may still depend on its world.',
        sources=['TECHNIQUE_LIBRARY.md', 'app/visuals/preview_layers.py'])]
    return rows


def search(rows, query='', kind='All'):
    words = query.casefold().split()
    return [row for row in rows if (kind == 'All' or row['kind'] == kind) and
            all(word in (' '.join((row['title'], row['summary'], row.get('tags', ''),
                                   *row['sources']))).casefold() for word in words)]


# Developer index: inspect source without importing the renderer or starting a UI.
def code_index(root=None):
    """Return current Python/GLSL definitions with live paths and line numbers.

    Descriptions enrich known techniques; all app Python functions/classes and
    GLSL function definitions are indexed so discovery is not limited to them.
    This is lexical discovery, not proof that two algorithms are equivalent.
    """
    import ast
    import re
    from pathlib import Path
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    descriptions = {symbol: title + ': ' + summary for title, summary, symbol in TECHNIQUES}
    rows = []
    for path in sorted((root / 'app').rglob('*.py')):
        source = path.read_text(encoding='utf-8-sig')
        tree = ast.parse(source, filename=str(path))
        def visit(node, parents=()):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = '.'.join((*parents, child.name))
                    rows.append(dict(path=str(path.relative_to(root)).replace('\\', '/'),
                        line=child.lineno, symbol=name, language='Python',
                        summary=ast.get_docstring(child) or '',
                        text=ast.get_source_segment(source, child) or ''))
                    visit(child, (*parents, child.name))
                else:
                    visit(child, parents)
        visit(tree)
    pattern = re.compile(r'^\s*(?:void|bool|int|float|[biu]?vec[234]|mat[234]|[A-Z]\w*)\s+(\w+)\s*\([^;{}]*\)\s*\{', re.M)
    for path in sorted((root / 'app').rglob('*')):
        if path.suffix not in ('.frag', '.vert', '.glsl'): continue
        source = path.read_text(encoding='utf-8-sig')
        # Preserve offsets while excluding comments from signature matching.
        clean = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), source, flags=re.S)
        for match in pattern.finditer(clean):
            start = clean.index('{', match.start()); end = start + 1; depth = 1
            while end < len(clean) and depth:
                depth += (clean[end] == '{') - (clean[end] == '}'); end += 1
            name = match[1]
            rows.append(dict(path=str(path.relative_to(root)).replace('\\', '/'),
                line=source.count('\n', 0, match.start(1)) + 1, symbol=name, language='GLSL',
                summary=descriptions.get(name, ''), text=source[match.start():end]))
    return rows


def find_code(query='', root=None):
    """Search names, descriptions and implementation text; return compact locations."""
    words = query.casefold().split()
    matches = []
    for row in code_index(root):
        headline = (row['symbol'] + ' ' + row['summary']).casefold()
        body = (headline + ' ' + row['path'] + ' ' + row['text']).casefold()
        if all(word in body for word in words):
            matches.append((sum(word in headline for word in words),
                            {key: value for key, value in row.items() if key != 'text'}))
    return [row for _, row in sorted(matches, key=lambda item: (-item[0], item[1]['path'], item[1]['line']))]


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description='Search existing ZeraWave code without launching Studio.')
    parser.add_argument('query', nargs='*', help='Words to find in symbols, descriptions or implementation')
    parser.add_argument('--json', action='store_true', help='Machine-readable locations')
    args = parser.parse_args()
    results = find_code(' '.join(args.query))
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for row in results:
            print(f"{row['path']}:{row['line']}  {row['symbol']}  [{row['language']}]")
            if row['summary']: print('  ' + row['summary'].splitlines()[0])
        print(f'{len(results)} matches. No match is not proof of absence; try related terms or a direct source search.')
