"""Compile-time audio access contract and once-per-frame uniform resolution.

Storage/ACK/listening adapters retain their packed-gain interface. Only the
presentation boundary expands those inputs; no analysis or settings live here.
"""
import re
import numpy as np

OFFSETS = (0, 4, 8, 12, 15, 17, 20, 22, 26, 28, 30, 32, 34, 35, 42, 45, 46, 48)


def calls(source, name):
    """Balanced GLSL call arguments (nested clamp calls are intentional)."""
    for match in re.finditer(r'\b' + name + r'\(', source):
        start = match.end(); depth = 1; args = []; last = start
        for i in range(start, len(source)):
            c = source[i]
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if not depth:
                    args.append(source[last:i].strip())
                    yield match.start(), i + 1, args
                    break
            elif c == ',' and depth == 1:
                args.append(source[last:i].strip()); last = i + 1


def source_kind(value):
    value = re.sub(r'\s+', '', value)
    raw = dict(u_scale='bass', u_flux='flux', u_sparkle='sparkle', u_impact='impact')
    if value in raw: return raw[value]
    if value.startswith('clamp('): return source_kind(value[6:value.index(',')]) + '_clipped'
    return 'derived'  # Local values can carry water attenuation or artifact listening.



class AudioUniformContract:
    def __init__(self, source):
        # Remove the old access functions before enumerating their consumers.
        for name in ('form_audio', 'planet_audio', 'water_audio'):
            source = re.sub(r'float ' + name + r'\([^\n]*\) \{.*?\n\}', '', source, count=1, flags=re.S)
        self.forms = []; self.shared = []; self.families = []
        declarations = []; initializers = []

        def shared(spec):
            if spec not in self.shared: self.shared.append(spec)
            i = self.shared.index(spec)
            return 'resolved_shared_' + str(i)

        for name in ('form_audio', 'planet_audio'):
            replacements = []
            for start, end, args in calls(source, name):
                value, owner, slot = args; kind = source_kind(value)
                if name == 'planet_audio':
                    spec = ('planet', int(owner), int(slot), kind)
                    ref = shared(spec)
                    if kind == 'derived': ref = 'apply_resolved_audio(' + value + ',' + ref + ')'
                elif owner == 'audio_context':
                    ref = shared(('context', 0, int(slot), kind))
                    if kind=='derived':ref='apply_resolved_audio('+value+','+ref+')'
                elif owner.isdigit():
                    spec = (int(owner), int(slot), kind)
                    if spec not in self.forms: self.forms.append(spec)
                    i = self.forms.index(spec); ref = 'u_resolved_forms[' + str(i // 4) + '][' + str(i % 4) + ']'
                    if kind=='derived':ref='apply_resolved_audio('+value+','+ref+')'
                else:
                    assert owner in ('24+form', '28+form', '32+form'), owner
                    spec = (int(owner[:2]), int(slot), kind)
                    if spec not in self.families: self.families.append(spec)
                    ref = 'u_resolved_families[' + str(self.families.index(spec)) + '][form]'
                    if kind=='derived':ref='apply_resolved_audio('+value+','+ref+')'
                replacements.append((start, end, ref))
            for start, end, ref in reversed(replacements): source = source[:start] + ref + source[end:]

        declarations += [f'uniform vec4 u_resolved_forms[{(len(self.forms)+3)//4}];',
                         f'uniform vec4 u_resolved_families[{len(self.families)}];',
                         f'uniform vec4 u_resolved_shared[{len(self.shared)}];']
        for i, spec in enumerate(self.shared):
            declarations.append(f'float resolved_shared_{i};')
            if spec[0] == 'context':
                selection = f'context==u_audio_forms.x && context!=0 ? u_resolved_shared[{i}].x : context==u_audio_forms.y && context!=0 ? u_resolved_shared[{i}].y : u_resolved_shared[{i}].w'
            else:
                selection = f'u_audio_forms.x==0 || context==5 ? u_resolved_shared[{i}].z : context==u_audio_forms.x ? u_resolved_shared[{i}].x : context==u_audio_forms.y ? u_resolved_shared[{i}].y : u_resolved_shared[{i}].w'
            initializers.append(f'    resolved_shared_{i}={selection};')
        declarations += ['float apply_resolved_audio(float value,float gain){return gain<=-1. ? clamp(-1.-gain,0.,1.) : gain==1. ? value : clamp(value*gain,0.,1.);}',
            'void resolve_audio_context(int context){', '    audio_context=context;',
            '    resolved_time=u_audio_forms.x!=0 && context==5 ? u_planet_time : u_time;',
            '    resolved_star_time=u_audio_forms.x!=0 && context==5 ? u_planet_star_time : u_star_time;',
            '    resolved_spatials=u_audio_forms.x!=0 && context==5 ? u_planet_spatials : u_spatial_treatments;',
            *initializers, '}']
        # Context selection is performed once at each existing ownership boundary.
        source = re.sub(r'\baudio_context=(?!=)([^;]+);', r'resolve_audio_context(\1);', source)
        source = source.replace('int resolve_audio_context(0);', 'int audio_context=0;')
        source = source.replace('float audio_time(){', 'float resolved_time,resolved_star_time; vec3 resolved_spatials;\nfloat audio_time(){', 1)
        source = re.sub(r'float audio_time\(\)\{[^\n]*\}', 'float audio_time(){return resolved_time;}', source)
        source = re.sub(r'float audio_star_time\(\)\{[^\n]*\}', 'float audio_star_time(){return resolved_star_time;}', source)
        source = re.sub(r'vec3 audio_spatials\(\)\{[^\n]*\}', 'vec3 audio_spatials(){return resolved_spatials;}', source)
        # Declarations must precede wrappers and all audio_time consumers.
        marker = 'uniform float u_debug_state;'
        source = source.replace(marker, '\n'.join(declarations) + '\n' + marker, 1)
        # Water blends still use the exact per-fragment family weights. Resolve
        # each ingredient once, outside the 40+14-step intersection search.
        water = ['uniform vec4 u_resolved_water[8];', 'uniform vec4 u_resolved_currents[2];',
                 'vec4 resolved_water[2];', 'void resolve_water_audio(){',
                 '    vec4 weights=water_forms();float currents=water_currents_weight();']
        raw = ('u_scale', 'u_flux', 'u_sparkle', 'u_impact')
        for group in range(2):
            for ingredient in range(4):
                i = group*4+ingredient; v = raw[ingredient]
                water.append(f'    resolved_water[{group}][{ingredient}]=all(equal(u_resolved_water[{i}],vec4({v}))) && u_resolved_currents[{group}][{ingredient}]=={v} ? {v} : dot(weights,u_resolved_water[{i}])+currents*u_resolved_currents[{group}][{ingredient}];')
        water.append('}')
        source = source.replace('// Material coverage follows broad connected flow bands', '\n'.join(water) + '\n// Material coverage follows broad connected flow bands', 1)
        replacements = [(a,b,f'resolved_water[{args[1]}][{args[2]}]') for a,b,args in calls(source,'water_audio')]
        for a,b,value in reversed(replacements): source=source[:a]+value+source[b:]
        source = source.replace('    bool directed = u_directed == 1;',
                                '    resolve_audio_context(audio_context);\n    resolve_water_audio();\n    bool directed = u_directed == 1;', 1)
        # Fractal World warp can read the shared clock before scene_frame.
        start=source.rindex('void main(){')
        source=source[:start]+source[start:].replace('void main(){','void main(){\n    resolve_audio_context(0);',1)
        self.source = source

    def upload(self, renderer, ids, a, b, planet_on, planet_rows):
        p = renderer.program
        # Match GL float operands and multiplication, including encoded -1-v.
        f = np.float32; clip = lambda v: f(min(1., max(0., v)))
        inputs = dict(bass=f(renderer.parameters.scale), flux=f(renderer.parameters.flux),
                      sparkle=f(renderer.parameters.sparkle), impact=f(renderer.impact_envelope))
        inputs.update({k+'_clipped':clip(v) for k,v in tuple(inputs.items())})
        inputs['pressure'] = f(inputs['bass_clipped'] * inputs['bass_clipped'])
        rows = {ids[0]:a, ids[1]:b} if ids[0] else {}
        def gain(form, slot):
            values = rows.get(form)
            return f(values[slot//4][slot%4]) if values else f(1.)
        def apply(value, g):
            return clip(f(-f(1.)-g)) if g<=-1. else value if g==1. else clip(f(value*g))
        def pack(values):
            values=list(values);values += [0.] * (-len(values)%4)
            return [tuple(float(v) for v in values[i:i+4]) for i in range(0,len(values),4)]
        values=pack(gain(form,slot) if kind=='derived' else apply(inputs[kind],gain(form,slot)) for form,slot,kind in self.forms)
        if 'u_resolved_forms' in p:p['u_resolved_forms'].value=values[:p['u_resolved_forms'].array_length]
        values=[tuple(float(gain(base+j,slot) if kind=='derived' else apply(inputs[kind],gain(base+j,slot))) for j in range(4)) for base,slot,kind in self.families]
        if 'u_resolved_families' in p:p['u_resolved_families'].value=values[:p['u_resolved_families'].array_length]
        values=[]
        for category,target,role,kind in self.shared:
            if category=='planet':
                pg=f(planet_rows[target*2+role//4][role%4]) if planet_on else f(1.)
                gains=[gain(form,OFFSETS[target]+role) if form and form!=5 and target<18 else pg if form==5 else f(1.) for form in ids]
            else:pg=f(1.);gains=[gain(form,role) for form in ids]
            values.append(tuple(float(v) for v in (*gains,pg,1.)) if kind=='derived' else
                          tuple(float(apply(inputs[kind],g)) for g in (*gains,pg,1.)))
        if 'u_resolved_shared' in p:p['u_resolved_shared'].value=values[:p['u_resolved_shared'].array_length]
        values=[];currents=[[],[]]
        for group in range(2):
            for i,key in enumerate(('bass','flux','sparkle','impact')):
                values.append(tuple(float(apply(inputs[key],gain(form,64+group*4+i))) for form in (7,8,9,10)))
                currents[group].append(float(apply(inputs[key],gain(13,64+(2 if group==1 else group)*4+i))))
        if 'u_resolved_water' in p:p['u_resolved_water'].value=values
        if 'u_resolved_currents' in p:p['u_resolved_currents'].value=currents
