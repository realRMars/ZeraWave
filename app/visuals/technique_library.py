"""Read-only discovery index. Runtime worlds/effects remain owned by their catalogs."""
from preview_layers import EFFECTS, EXPERIMENTS

SHADER = 'app/visuals/shaders/dream.frag'
# title, search vocabulary / purpose, source symbol. These are building blocks,
# not independently toggleable effects or promises of generic reusable APIs.
TECHNIQUES = (
    ('Musical color accents', 'Selective saturation and brightness accents preserve dark space while music brings pigment forward.', 'musical_material'),
    ('Planet material gathering', 'Project the shared canvas onto the planet surface while preserving its sphere geometry.', 'isolated_cosmic_scene'),
    ('Spatial flow', 'Stretch material coordinates through tunnel, fractal folds and horizon flow without moving solid geometry.', 'spatial_carrier'),
    ('Continuous stars', 'Drifting stars and musical streaks; the renderer maintains a separate continuous star clock.', 'cosmic_star_layer'),
    ('Corridor perspective', 'Curved perspective passage shared by Neon corridor and the Stormfront cloud vault.', 'geometric_surface'),
    ('Water currents', 'Coherent flow and local shear for moving liquid pigment; procedural, not a fluid solver.', 'water_current'),
    ('Surface waves', 'Layered water height, pressure and selective highlights.', 'water_height'),
    ('Waterfall projection', 'River, cliff lip and falling sheet share a perspective surface.', 'waterfall_surface'),
    ('Growing landscapes', 'Procedural tree growth and decay in Firescape; audio-driven travel is owned by the renderer.', 'firescape_tree'),
    ('Bounded blast events', 'Aftershock sites, expanding rings and material inversion; event lifetime is managed by the renderer.', 'blast_ring'),
    ('Castle depth', 'Distance-field castle geometry, rotating view and obstruction for tower lights.', 'air_castle_map'),
    ('Solid terrain', 'Earth terrain and worm distance queries; keep solid surfaces opaque.', 'earth_map'),
    ('Volume and solids', 'Fog density composited with solid terrain; translucency is intentional for vapor.', 'fog_scene'),
    ('Charged filaments', 'Plasma loops, arcs and particles with distinct forms and audio response.', 'plasma_scene'),
    ('Regional handoffs', 'Moving boundaries let worlds meet through different regions instead of uniform crossfades.', 'handoff_front'),
)


def entries(world_tree):
    rows = [dict(id='world:blend', title='Main blend', kind='Worlds & forms',
                 summary='Music-responsive visits across worlds. Materials cycle independently. Choose this to review integration.',
                 selection=[], sources=['app/visuals/renderer.py:choose_world'])]
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
            summary=f'{category}. Available in: {", ".join(worlds)}. '
                    'Use Effects & layers to add, solo, order or cycle this item. Availability depends on the selected form and music.' +
                    (' Dormant unless explicitly enabled.' if key in EXPERIMENTS else ''),
            sources=['app/visuals/preview_layers.py:EFFECTS'], tags=key))
    for title, summary, symbol in TECHNIQUES:
        rows.append(dict(id='technique:' + symbol, title=title, kind='Techniques', summary=summary +
            ' This is an implementation building block, not a standalone layer switch.', sources=[SHADER + ':' + symbol]))
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
