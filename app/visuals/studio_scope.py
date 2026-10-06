"""Canonical playback scopes, distinct from browsed Library rows and output."""
from world_catalog import LIVE_STATES, studio_trees

def node_at(tree, path):
    node = {'children': tree, 'label': 'Main blend'}
    for key in path:
        if key not in node.get('children', {}):raise ValueError('This Library destination is unavailable.')
        node = node['children'][key]
    return node

def playback_scope(namespace, path, roster):
    trees = studio_trees(roster)
    if namespace not in trees or namespace == 'experimental' and not path:
        raise ValueError('Choose an available category in this namespace.')
    tree = trees[namespace]; node = node_at(tree, path)
    def leaves(item):
        if item.get('children'):
            return [state for child in item['children'].values() for state in leaves(child)]
        state = LIVE_STATES.get(item.get('state'))
        return [] if state is None else [state]
    forms = list(dict.fromkeys(leaves(node)))
    if not forms:raise ValueError('This category has no eligible playback forms.')
    labels = [node_at(tree, path[:i+1])['label'] for i in range(len(path))]
    return dict(namespace=namespace, path=list(path), forms=forms,
                label=' / '.join(labels) or 'Main blend (all worlds)')

def leaf_destination(namespace, path, committed, roster):
    node = node_at(studio_trees(roster).get(namespace, {}), path)
    if node.get('children') or 'state' not in node:raise ValueError('Load is available on playable leaves only.')
    form = LIVE_STATES[node['state']]
    if committed and committed['namespace'] == namespace and form in committed['forms']:
        scope = committed
    else:scope = playback_scope(namespace, path[:-1], roster)
    return scope, form

def validate_scope(value, roster):
    if not isinstance(value, dict):raise ValueError('Invalid playback scope.')
    expected = playback_scope(value.get('namespace'), value.get('path', []), roster)
    if value != expected:raise ValueError('Playback eligibility no longer matches the canonical Library.')
    return expected

def compatible_scope(scope):
    # Main's directed packing has no Experimental representation. Those leaves
    # retain their own diagnostic/resource route rather than being promoted.
    return scope['namespace']=='main'
