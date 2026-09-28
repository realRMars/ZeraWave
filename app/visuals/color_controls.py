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
)


def targets_for(scene):
    return tuple(target for target in TARGETS if target.scene == scene)


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
    return result


def parse_colors(text):
    return validate_colors(json.loads(text))


def scene_colors(data, scene):
    return {target.id:data[target.id] for target in targets_for(scene) if target.id in data}


def color_uniforms(data, active):
    result = {}
    for target in TARGETS:
        result[target.uniform+'_on'] = int(active and target.id in data)
        slots = resolved_slots(target,data)
        if target.kind == 'color': result[target.uniform] = slots[0][0]
        else:
            result[target.uniform] = tuple(slot[0] for slot in slots)
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
