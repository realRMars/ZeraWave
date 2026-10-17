"""Version2 accepted Episode09 component definitions for project_recipes.

Expands only to ordinary editable entities. No rendering, fonts, filesystem,
timeline authority, source audition, mixer policy or template playback runtime.
"""
from copy import deepcopy
from fractions import Fraction
import uuid
from video_project import fields,integer,text,rational,pair,number

REFERENCE_PROJECT_SHA256='29803e6bbd3dec2ea5a91c512d96f3e819a76e0549439ec191d16f45b8f04e39'
REFERENCE_SETTINGS=dict(width=1280,height=720,fps=[30,1],sample_rate=48000)
DEFINITIONS={'card': {'border': {'id': '2311ba4f2f7c5f52a0f50ff1787a86ee',
                     'style': {'font': 'Segoe UI',
                               'size': 24,
                               'color': '#fff7e7',
                               'background': '#93856c',
                               'bold': True,
                               'align': 'left',
                               'bounds': [0.5625, 0.20277777777777778, 0.41015625, 0.44166666666666665],
                               'padding': 0,
                               'radius': 10}},
          'panel': {'id': '03fc4e541c335735bc1acecb9e3ced41',
                    'style': {'font': 'Segoe UI',
                              'size': 24,
                              'color': '#fff7e7',
                              'background': '#141d26',
                              'bold': True,
                              'align': 'left',
                              'bounds': [0.56328125, 0.20416666666666666, 0.40859375, 0.4388888888888889],
                              'padding': 0,
                              'radius': 9}},
          'heading': {'id': 'e3aa4a16b548572fa4ac22dc90284e4e',
                      'style': {'font': 'Segoe UI',
                                'size': 17,
                                'color': '#f1dfbc',
                                'background': '#00000000',
                                'bold': True,
                                'align': 'left',
                                'bounds': [0.575, 0.2125, 0.384375, 0.041666666666666664],
                                'padding': 0,
                                'radius': 5}},
          'author': {'id': '214db4b3a96a530086cae4c4a8a04802',
                     'style': {'font': 'Segoe UI',
                               'size': 22,
                               'color': '#e9edf2',
                               'background': '#00000000',
                               'bold': True,
                               'align': 'left',
                               'bounds': [0.6203125, 0.25, 0.3359375, 0.05416666666666667],
                               'padding': 0,
                               'radius': 5}},
          'recommended': {'id': '6605cb0a59b555bb9420981c2aa093ad',
                          'style': {'font': 'Segoe UI',
                                    'size': 17,
                                    'color': '#83bed8',
                                    'background': '#00000000',
                                    'bold': True,
                                    'align': 'left',
                                    'bounds': [0.6203125,
                                               0.29305555555555557,
                                               0.3359375,
                                               0.04027777777777778],
                                    'padding': 0,
                                    'radius': 5}},
          'posted': {'id': 'a67d79cf943359acbd1df1c5cf2d9e9e',
                     'style': {'font': 'Segoe UI',
                               'size': 15,
                               'color': '#cdd1d7',
                               'background': '#00000000',
                               'bold': False,
                               'align': 'left',
                               'bounds': [0.575, 0.33611111111111114, 0.384375, 0.03611111111111111],
                               'padding': 0,
                               'radius': 5}},
          'playtime': {'id': 'b5d6550029185b1592d792186aa64a8e',
                       'style': {'font': 'Segoe UI',
                                 'size': 15,
                                 'color': '#cdd1d7',
                                 'background': '#00000000',
                                 'bold': False,
                                 'align': 'left',
                                 'bounds': [0.575, 0.37083333333333335, 0.384375, 0.03611111111111111],
                                 'padding': 0,
                                 'radius': 5}},
          'quote': {'id': '545f020546be57bf87bbeaaa0e731bd7',
                    'style': {'font': 'Segoe UI',
                              'size': 23,
                              'color': '#e9edf2',
                              'background': '#00000000',
                              'bold': False,
                              'align': 'left',
                              'bounds': [0.575, 0.4152777777777778, 0.384375, 0.14583333333333334],
                              'padding': 0,
                              'radius': 5,
                              'max_lines': 3,
                              'valign': 'top'}},
          'response': {'id': 'ae23a7254187582bb7a8e24540e71e50',
                       'style': {'font': 'Segoe UI',
                                 'size': 15,
                                 'color': '#b5a17e',
                                 'background': '#00000000',
                                 'bold': False,
                                 'align': 'left',
                                 'bounds': [0.575, 0.5625, 0.384375, 0.04861111111111111],
                                 'padding': 0,
                                 'radius': 5,
                                 'max_lines': 2,
                                 'valign': 'top'}},
          'context': {'id': '480697c18e685823aa88de2b39886e45',
                      'style': {'font': 'Segoe UI',
                                'size': 14,
                                'color': '#b5a17e',
                                'background': '#00000000',
                                'bold': False,
                                'align': 'left',
                                'bounds': [0.575, 0.6041666666666666, 0.384375, 0.03333333333333333],
                                'padding': 0,
                                'radius': 5}}},
 'question': {'id': 'ba5ca85f02305b81bc43be449b9ab633',
              'style': {'font': 'Segoe UI',
                        'size': 32,
                        'color': '#fff7e7',
                        'background': '#00000000',
                        'bold': True,
                        'align': 'left',
                        'bounds': [0.02734375, 0.030555555555555555, 0.8828125, 0.09166666666666666],
                        'padding': 0,
                        'radius': 5}},
 'capsules': [{'frame': {'id': '89db7b854e335ca2af39bb37c803bf16',
                         'style': {'font': 'Segoe UI',
                                   'size': 24,
                                   'color': '#fff7e7',
                                   'background': '#fff7e7',
                                   'bold': True,
                                   'align': 'left',
                                   'bounds': [0.02578125,
                                              0.12638888888888888,
                                              0.1828125,
                                              0.15833333333333333],
                                   'padding': 0,
                                   'radius': 7}},
               'label': {'id': '87a826ec123d52ba9880f4fb41a746b5',
                         'style': {'font': 'Segoe UI',
                                   'size': 19,
                                   'color': '#fff7e7',
                                   'background': '#00000000',
                                   'bold': True,
                                   'align': 'center',
                                   'bounds': [0.02734375, 0.2972222222222222, 0.1796875, 0.08055555555555556],
                                   'padding': 0,
                                   'radius': 5,
                                   'max_lines': 2}},
               'status': {'id': '451b89cfa9a2571cb37f6ff3bdc4e49c',
                          'style': {'font': 'Segoe UI',
                                    'size': 18,
                                    'color': '#c7ff00',
                                    'background': '#00000000',
                                    'bold': True,
                                    'align': 'center',
                                    'bounds': [0.02734375,
                                               0.3819444444444444,
                                               0.1796875,
                                               0.041666666666666664],
                                    'padding': 0,
                                    'radius': 5}}},
              {'frame': {'id': 'e5bfd03a8fde56fb8912cad20884c976',
                         'style': {'font': 'Segoe UI',
                                   'size': 24,
                                   'color': '#fff7e7',
                                   'background': '#fff7e7',
                                   'bold': True,
                                   'align': 'left',
                                   'bounds': [0.21796875,
                                              0.12638888888888888,
                                              0.1828125,
                                              0.15833333333333333],
                                   'padding': 0,
                                   'radius': 7}},
               'label': {'id': '26051c38c7be56b3bf5c60ebe1054a20',
                         'style': {'font': 'Segoe UI',
                                   'size': 19,
                                   'color': '#fff7e7',
                                   'background': '#00000000',
                                   'bold': True,
                                   'align': 'center',
                                   'bounds': [0.21953125, 0.2972222222222222, 0.1796875, 0.08055555555555556],
                                   'padding': 0,
                                   'radius': 5,
                                   'max_lines': 2}},
               'status': {'id': '59b9ce09d54159c18a48c9b258cd4d22',
                          'style': {'font': 'Segoe UI',
                                    'size': 18,
                                    'color': '#c7ff00',
                                    'background': '#00000000',
                                    'bold': True,
                                    'align': 'center',
                                    'bounds': [0.21953125,
                                               0.3819444444444444,
                                               0.1796875,
                                               0.041666666666666664],
                                    'padding': 0,
                                    'radius': 5}}},
              {'frame': {'id': '70711cde3aef5588b55d59e7325132b4',
                         'style': {'font': 'Segoe UI',
                                   'size': 24,
                                   'color': '#fff7e7',
                                   'background': '#fff7e7',
                                   'bold': True,
                                   'align': 'left',
                                   'bounds': [0.41015625,
                                              0.12638888888888888,
                                              0.1828125,
                                              0.15833333333333333],
                                   'padding': 0,
                                   'radius': 7}},
               'label': {'id': '6d25174bea825140bfd9b65ee497798e',
                         'style': {'font': 'Segoe UI',
                                   'size': 19,
                                   'color': '#fff7e7',
                                   'background': '#00000000',
                                   'bold': True,
                                   'align': 'center',
                                   'bounds': [0.41171875, 0.2972222222222222, 0.1796875, 0.08055555555555556],
                                   'padding': 0,
                                   'radius': 5,
                                   'max_lines': 2}},
               'status': {'id': '28824fc15e5958ef91e364461b262db2',
                          'style': {'font': 'Segoe UI',
                                    'size': 18,
                                    'color': '#c7ff00',
                                    'background': '#00000000',
                                    'bold': True,
                                    'align': 'center',
                                    'bounds': [0.41171875,
                                               0.3819444444444444,
                                               0.1796875,
                                               0.041666666666666664],
                                    'padding': 0,
                                    'radius': 5}}},
              {'frame': {'id': 'f2bd2b8a1ec251e0b25398c1e315932d',
                         'style': {'font': 'Segoe UI',
                                   'size': 24,
                                   'color': '#fff7e7',
                                   'background': '#fff7e7',
                                   'bold': True,
                                   'align': 'left',
                                   'bounds': [0.60234375,
                                              0.12638888888888888,
                                              0.1828125,
                                              0.15833333333333333],
                                   'padding': 0,
                                   'radius': 7}},
               'label': {'id': '09a9ca2c8ec155289d9ebe6349bda36e',
                         'style': {'font': 'Segoe UI',
                                   'size': 19,
                                   'color': '#fff7e7',
                                   'background': '#00000000',
                                   'bold': True,
                                   'align': 'center',
                                   'bounds': [0.60390625, 0.2972222222222222, 0.1796875, 0.08055555555555556],
                                   'padding': 0,
                                   'radius': 5,
                                   'max_lines': 2}},
               'status': {'id': '6a75edad5edc5953b13afd55ad423add',
                          'style': {'font': 'Segoe UI',
                                    'size': 18,
                                    'color': '#c7ff00',
                                    'background': '#00000000',
                                    'bold': True,
                                    'align': 'center',
                                    'bounds': [0.60390625,
                                               0.3819444444444444,
                                               0.1796875,
                                               0.041666666666666664],
                                    'padding': 0,
                                    'radius': 5}}},
              {'frame': {'id': '897e366ab2f05342ac1589774993b4a9',
                         'style': {'font': 'Segoe UI',
                                   'size': 24,
                                   'color': '#fff7e7',
                                   'background': '#fff7e7',
                                   'bold': True,
                                   'align': 'left',
                                   'bounds': [0.79453125,
                                              0.12638888888888888,
                                              0.1828125,
                                              0.15833333333333333],
                                   'padding': 0,
                                   'radius': 7}},
               'label': {'id': '14b0b44596645b76be730f5d642a194a',
                         'style': {'font': 'Segoe UI',
                                   'size': 19,
                                   'color': '#fff7e7',
                                   'background': '#00000000',
                                   'bold': True,
                                   'align': 'center',
                                   'bounds': [0.79609375, 0.2972222222222222, 0.1796875, 0.08055555555555556],
                                   'padding': 0,
                                   'radius': 5,
                                   'max_lines': 2}},
               'status': {'id': '65d7099ebc7d58cb8d4ab6143d4a441c',
                          'style': {'font': 'Segoe UI',
                                    'size': 18,
                                    'color': '#c7ff00',
                                    'background': '#00000000',
                                    'bold': True,
                                    'align': 'center',
                                    'bounds': [0.79609375,
                                               0.3819444444444444,
                                               0.1796875,
                                               0.041666666666666664],
                                    'padding': 0,
                                    'radius': 5}}}],
 'progress': {'id': '0fe29d2f44a55a1298b5be646fb7b6b5',
              'style': {'font': 'Segoe UI',
                        'size': 12,
                        'color': '#c7ff00',
                        'background': '#70212b30',
                        'bold': True,
                        'align': 'left',
                        'bounds': [0.02734375, 0.9916666666666667, 0.9453125, 0.005555555555555556],
                        'padding': 0,
                        'radius': 5}}}
LAYOUTS={'review_card': {'background': {'id': '5b9c84af43ea5227bdf074bf202240c8',
                                'layout': {'bounds': [0.0, 0.0, 1.0, 1.0],
                                           'opacity': 1.0,
                                           'rotation': 0.0,
                                           'brightness': 0.3,
                                           'fit': 'Fit',
                                           'masks': [],
                                           'blend': 'Normal'}},
                 'picture': {'id': '8510a1328f145cf8b5d2f50875d2fa92',
                             'layout': {'bounds': [0.02734375,
                                                   0.2847222222222222,
                                                   0.5078125,
                                                   0.5069444444444444],
                                        'opacity': 1.0,
                                        'rotation': 0.0,
                                        'brightness': 1,
                                        'fit': 'Fit',
                                        'masks': [],
                                        'blend': 'Normal'}},
                 'avatar': {'id': '74b5d3e38ee85431b11a968fde3bc99d',
                            'layout': {'bounds': [0.575, 0.25833333333333336, 0.034375, 0.06111111111111111],
                                       'opacity': 1.0,
                                       'rotation': 0.0,
                                       'brightness': 1,
                                       'fit': 'Fit',
                                       'masks': [],
                                       'blend': 'Normal'}}},
 'outro': {'background': {'id': '9523cc125ee65120b1c3a363f9d1f949',
                          'layout': {'bounds': [0.0, 0.0, 1.0, 1.0],
                                     'opacity': 1.0,
                                     'rotation': 0.0,
                                     'brightness': 0.27,
                                     'fit': 'Fit',
                                     'masks': [],
                                     'blend': 'Normal'}},
           'brand': {'id': 'a631bf8864af597a9048ab56b842382b',
                     'layout': {'bounds': [0.921875, 0.03333333333333333, 0.040625, 0.07222222222222222],
                                'opacity': 1.0,
                                'rotation': 0.0,
                                'brightness': 1,
                                'fit': 'Fit',
                                'masks': [],
                                'blend': 'Normal'}},
           'capsule-1-image': {'id': 'f1f3d85a94965eebb66a537ba31b39a2',
                               'layout': {'bounds': [0.02734375,
                                                     0.12916666666666668,
                                                     0.1796875,
                                                     0.1527777777777778],
                                          'opacity': 1.0,
                                          'rotation': 0.0,
                                          'brightness': 1,
                                          'fit': 'Fit',
                                          'masks': [],
                                          'blend': 'Normal'}},
           'capsule-2-image': {'id': '4adaced1e71d5c77bdfbee27c6e49554',
                               'layout': {'bounds': [0.21953125,
                                                     0.12916666666666668,
                                                     0.1796875,
                                                     0.1527777777777778],
                                          'opacity': 1.0,
                                          'rotation': 0.0,
                                          'brightness': 1,
                                          'fit': 'Fit',
                                          'masks': [],
                                          'blend': 'Normal'}},
           'capsule-3-image': {'id': 'c25c33310a0a523db3c2a2c8ac87b674',
                               'layout': {'bounds': [0.41171875,
                                                     0.12916666666666668,
                                                     0.1796875,
                                                     0.1527777777777778],
                                          'opacity': 1.0,
                                          'rotation': 0.0,
                                          'brightness': 1,
                                          'fit': 'Fit',
                                          'masks': [],
                                          'blend': 'Normal'}},
           'capsule-4-image': {'id': '5b14a7701804579295f294da0ab7fd62',
                               'layout': {'bounds': [0.60390625,
                                                     0.12916666666666668,
                                                     0.1796875,
                                                     0.1527777777777778],
                                          'opacity': 1.0,
                                          'rotation': 0.0,
                                          'brightness': 1,
                                          'fit': 'Fit',
                                          'masks': [],
                                          'blend': 'Normal'}},
           'capsule-5-image': {'id': '23d0659733a05ffdab701f74c4cf92f8',
                               'layout': {'bounds': [0.79609375,
                                                     0.12916666666666668,
                                                     0.1796875,
                                                     0.1527777777777778],
                                          'opacity': 1.0,
                                          'rotation': 0.0,
                                          'brightness': 1,
                                          'fit': 'Fit',
                                          'masks': [],
                                          'blend': 'Normal'}}}}


def expand_component(recipe,manifest):
    from project_recipes import fingerprint,item
    p=recipe['params'];key=recipe['key'];kind=recipe['kind'];settings=manifest.get('settings')
    if recipe['version']!=2 or kind not in ('review_card','outro'):raise ValueError('Unsupported component kind/version.')
    if not isinstance(settings,dict):raise ValueError('Version2 components require explicit manifest.settings to bind native design dimensions/FPS.')
    scale=Fraction(settings['height'],720);fps=rational(settings['fps'])
    common=('tracks','start','duration','picture')
    required=common+('author','quote','posted','playtime','response','context','avatar') if kind=='review_card' else common+('question','capsules','brand','voice','music','progress_range')
    fields(p,required,('parts','provenance','font','layouts')+(('fade_frames','sendoff_frames') if kind=='outro' else ()))
    fields(p['tracks'],('background','picture','panel','images','text'))
    start=integer(p['start']);duration=integer(p['duration'],2,120*24*3600);parts=p.get('parts',{});layout_parts=p.get('layouts',{});used_layouts=set();fade=0
    if not isinstance(parts,dict) or any(not isinstance(v,dict) for v in parts.values()):raise ValueError('Component part overrides must be explicit style objects.')
    if not isinstance(layout_parts,dict) or any(not isinstance(v,dict) for v in layout_parts.values()):raise ValueError('Component layout overrides must be explicit objects.')
    provenance=deepcopy(p.get('provenance',{}))
    if not isinstance(provenance,dict) or 'component' in provenance:raise ValueError('User provenance must be an object without reserved component identity.')
    instance=uuid.uuid5(uuid.UUID(manifest['id']),'component:'+key).hex;made=[];used=set();parameter_hash=fingerprint(p)
    def prov(part,role,reference=None,extra=None):
        return dict(deepcopy(provenance),component=dict(instance_id=instance,instance_key=key,kind=kind,version=2,part=part,role=role,track_roles=deepcopy(p['tracks']),parameters_sha256=parameter_hash,reference_project_sha256=REFERENCE_PROJECT_SHA256,reference_part_id=reference,reference_dimensions=[1280,720],native_dimensions=[settings['width'],settings['height']],**(extra or {})))
    def opacity_keys(frames):
        points={0:[0,1.,'Linear'],duration-frames:[duration-frames,1.,'Linear'],duration-1:[duration-1,0.,'Linear']}
        return [dict(parameter='opacity',points=[points[f] for f in sorted(points)])]
    def graphic(part,content,reference,role='text',fade=0,**extra):
        text(content,4096);style=deepcopy(reference['style'])
        for field in ('size','padding','padding_x','padding_y','radius','stroke_width','line_spacing'):
            if field in style:style[field]=float(Fraction(str(style[field]))*scale)
        if 'font' in p:style['font']=text(p['font'],128)
        style.update(deepcopy(parts.get(part,{})));used.add(part)
        if fade:
            if style.get('keys'):raise ValueError('Explicit part keys conflict with the declared component fade; choose one owner.')
            style['keys']=opacity_keys(fade)
        made.append(item('graphics',key+'.'+part,dict(track=deepcopy(p['tracks'][role]),start=start,duration=duration,text=content,style=style,order=len(made),provenance=prov(part,role,reference['id']),**extra)))
    def layout(part):
        reference=LAYOUTS[kind][part];value=deepcopy(reference['layout']);value.update(deepcopy(layout_parts.get(part,{})));used_layouts.add(part)
        if fade and part!='background':
            if value.get('keys'):raise ValueError('Explicit layout keys conflict with component fade; choose one owner.')
            value['keys']=opacity_keys(fade)
        return value,reference['id']
    def image(part,asset):
        if asset is None:return
        value,reference=layout(part)
        made.append(item('clips',key+'.'+part,dict(asset=deepcopy(asset),track=deepcopy(p['tracks']['images']),name=key+' '+part,start=start,duration=duration,layout=value,provenance=prov(part,'images',reference))))
    def picture():
        v=p['picture'];fields(v,('asset','source_in','source_out','rate'))
        begin=rational(v['source_in']);end=rational(v['source_out']);rate=rational(v['rate'])
        if begin<0 or end<=begin or not Fraction(1,16)<=rate<=16 or end-begin!=Fraction(duration,1)/fps*rate:raise ValueError('Picture source In/Out must exactly match declared component duration and rational rate.')
        for part,role in [('background','background'),('picture','picture')]:
            if kind=='outro' and part=='picture':continue
            value,reference=layout(part)
            made.append(item('clips',key+'.'+part,dict(asset=deepcopy(v['asset']),track=deepcopy(p['tracks'][role]),name=key+' '+part,start=start,duration=duration,source_in=deepcopy(v['source_in']),rate=deepcopy(v['rate']),layout=value,provenance=prov(part,role,reference,extra=dict(intended_source_out=deepcopy(v['source_out']))))))
    picture()
    if kind=='review_card':
        values=dict(border='',panel='',heading='STEAM PLAYER REVIEW',author=p['author'],recommended='Recommended',posted=p['posted'],playtime=p['playtime'],quote=p['quote'],response=p['response'],context=p['context'])
        for part,reference in DEFINITIONS['card'].items():graphic(part,values[part],reference,'panel' if part in ('border','panel') else 'text')
        image('avatar',p['avatar'])
    else:
        if not isinstance(p['capsules'],list) or len(p['capsules'])!=5:raise ValueError('The approved outro explicitly contains five editable capsule entries.')
        if p['brand'] is None:raise ValueError('The branded outro requires its explicit brand image reference.')
        fade=integer(p.get('fade_frames',min(18,duration-1)),1,duration-1)
        if duration-fade==0:raise ValueError('Outro fade must leave its initial full-opacity frame.')
        four=fps*4
        if four.denominator!=1 and 'sendoff_frames' not in p:raise ValueError('Fractional FPS requires explicit sendoff_frames (covering four seconds) so the actual duration is disclosed.')
        sendoff=integer(p.get('sendoff_frames',int(four)),1,duration)
        if not Fraction(4)<=Fraction(sendoff)/fps<Fraction(4)+1/fps:raise ValueError('Sendoff frames must explicitly cover four seconds within one project frame.')
        tail=start+duration-sendoff
        graphic('question',p['question'],DEFINITIONS['question'],fade=fade)
        for index,(value,reference) in enumerate(zip(p['capsules'],DEFINITIONS['capsules'])):
            fields(value,('label','status','asset'))
            if value['asset'] is None:raise ValueError('Every recap capsule requires its explicit image reference.')
            stem='capsule-'+str(index+1)
            graphic(stem+'-frame','',reference['frame'],'panel',fade)
            graphic(stem+'-label',value['label'],reference['label'],fade=fade)
            graphic(stem+'-status',value['status'],reference['status'],fade=fade)
            image(stem+'-image',value['asset'])
        progress=p['progress_range']
        if not isinstance(progress,list) or len(progress)!=2:raise ValueError('Progress range is explicit [In,exclusive Out] in sequence frames.')
        integer(progress[0],0,start);integer(progress[1],start+duration)
        graphic('progress','',DEFINITIONS['progress'],'panel',fade,dynamic='progress',range_start=progress[0],range_end=progress[1])
        image('brand',p['brand'])
        for part in ('voice','music'):
            v=p[part];fields(v,('asset','track','start','duration','source_in','source_out','rate','audio'),('pad_end',))
            audio=deepcopy(v['audio']);values={k:deepcopy(v[k]) for k in ('asset','track','start','duration','source_in','rate')};values.update(name=key+' '+part,audio=audio,pad_end=v.get('pad_end','silence' if part=='voice' else 'none'),provenance=prov(part,'audio',extra=dict(intended_source_out=deepcopy(v['source_out']),sendoff_frames=sendoff,sendoff_start=tail,outro_end=start+duration)))
            if part=='music' and (type(v['duration']) is not int or v['start']>tail or v['start']+v['duration']!=start+duration or not 1<=audio.get('fade_out',0)<=sendoff):raise ValueError('Music must cover the complete four-second sendoff through outro end and declare its short fade.')
            if part=='voice' and isinstance(v['duration'],int) and v['start']+v['duration']>tail:raise ValueError('Complete intended voice must finish before the declared music sendoff.')
            made.append(item('clips',key+'.'+part,values))
    if set(parts)-used:raise ValueError('Unknown component part style: '+', '.join(sorted(set(parts)-used)))
    if set(layout_parts)-used_layouts:raise ValueError('Unknown component layout part: '+', '.join(sorted(set(layout_parts)-used_layouts)))
    return made,dict(key=key,kind=kind,version=2,instance_id=instance,parameters_sha256=parameter_hash,reference_project_sha256=REFERENCE_PROJECT_SHA256,entities=[r['category']+':'+r['key'] for r in made])

def validate_components(document,instances):
    """Check expanded normal rows after manifest reference/natural-time resolution."""
    from project_audio_timing import natural_duration
    assets={a['id']:a for a in document['media']};tracks={t['id']:t for t in document['tracks']};groups={}
    fps=rational(document['settings']['fps'])
    for category in ('clips','graphics'):
        for row in document[category]:
            component=row['provenance'].get('component',{})
            if component.get('instance_id') in instances:groups.setdefault(component['instance_id'],[]).append((row,component))
    if set(groups)!=set(instances):raise ValueError('Expanded component instance is incomplete.')
    for rows in groups.values():
        roles=rows[0][1]['track_roles'];fields(roles,('background','picture','panel','images','text'))
        values=[tracks.get(roles[k]) for k in ('background','picture','panel','images','text')]
        if any(t is None for t in values) or [t['kind'] for t in values]!=['video','video','graphics','graphics','graphics']:raise ValueError('Component needs explicit background/inset video and panel/image/text graphics tracks.')
        orders=[t['order'] for t in values]
        if orders!=sorted(set(orders)):raise ValueError('Component stacking requires distinct tracks in background, picture, panel, images, text order.')
        audio={}
        for row,component in rows:
            if component['track_roles']!=roles:raise ValueError('Component parts disagree about their explicit track roles.')
            if component['role'] in roles and row['track']!=roles[component['role']]:raise ValueError('Component part targets a different track than declared.')
            if component['role'] in ('background','picture') and assets[row['asset']]['kind']!='Video':raise ValueError('The accepted component requires an ordinary moving-video source, not a still replacement.')
            if 'intended_source_out' in component:
                end=rational(component['intended_source_out']);begin=rational(row['source_in']);rate=rational(row['rate']);available=natural_duration(assets[row['asset']]['metadata'])
                reached=begin+Fraction(row['duration'])/fps*rate
                if not begin<end<=available or reached<end:raise ValueError('Expanded clip does not preserve its declared complete source interval.')
                if reached-end>=rate/fps and component['role']=='audio':raise ValueError('Declared audio source Out disagrees with its frame-covering clip duration.')
            if component['role']=='audio':
                if tracks[row['track']]['kind']!='audio':raise ValueError('Outro '+component['part']+' must target an audio track; a video track contributes no mixed audio.')
                audio[component['part']]=(row,component)
        if rows[0][1]['kind']=='outro':
            if set(audio)!=set(('voice','music')):raise ValueError('Outro requires both editable voice and music parts.')
            voice,v=audio['voice'];music,m=audio['music'];tail=v['sendoff_start'];end=v['outro_end']
            if voice['start']+voice['duration']>tail:raise ValueError('Complete resolved voice reaches into the declared four-second music sendoff.')
            if music['start']>tail or music['start']+music['duration']!=end or music['audio']['fade_out']<1:raise ValueError('Music does not cover the declared sendoff and fade through outro end.')
