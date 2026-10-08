"""Pure composition migration, geometry, grouping, blending and history checks."""
from copy import deepcopy
from pathlib import Path
import json,uuid
import numpy as np
from composition import *

def run():
    reference=dict(id=uuid.uuid4().hex,kind='Images',path=str(Path('C:/ZeraWave/images n vids/Xeraphina.jpg')),name='Source')
    legacy=dict(version=1,presentation='Image only',assets=[reference],layers=[dict(id='image.layer1',asset=reference['id'],enabled=True,order=1,opacity=.7,fit='Fill',x=.125,y=-.25,scale=1.6),dict(id='image.layer2',asset=None,enabled=False,order=0,opacity=1.,fit='Fit',x=0.,y=0.,scale=1.)])
    scene=validate_scene(legacy);assert len(scene['layers'])==1 and scene['presentation']=='Layers only';row=scene['layers'][0];assert row['id']=='image.layer1' and row['opacity']==.7 and row['transform']==transform(.125,-.25,1.6) # legacy GL bounds subtract Y: screen Y pointed down
    assert defaults()['layers']==[]
    group=new_layer('Group');group['transform']=transform(.1,.2,1.2,1.2,25);group['order']=2;scene['layers'].append(group);before=world_matrix(scene,row['id']);reparent(scene,row['id'],group['id']);assert np.allclose(before,world_matrix(scene,row['id']));reparent(scene,row['id'],None);assert np.allclose(before,world_matrix(scene,row['id']))
    group['flip_x']=True;before=world_matrix(scene,row['id']);reparent(scene,row['id'],group['id']);assert np.allclose(before,world_matrix(scene,row['id']));reparent(scene,row['id'],None);assert np.allclose(before,world_matrix(scene,row['id']))
    row['masks']=[dict(mode='Cut',enabled=True,points=[[.1,.1],[.8,.1],[.8,.7]])];row['crop']=[.1,.2,.9,.8];row['blend']='Screen';scene=validate_scene(scene);assert validate_scene(json.loads(json.dumps(scene)))==scene
    bad=deepcopy(scene);bad['layers'][1]['parent']=bad['layers'][1]['id']
    try:validate_scene(bad);raise AssertionError('cycle accepted')
    except ValueError:pass
    bad=deepcopy(scene);bad['layers'][0]['masks'][0]['points']=[[0.,0.],[.5,.5],[1.,1.]]
    try:validate_scene(bad);raise AssertionError('degenerate mask accepted')
    except ValueError:pass
    b=np.array([.1,.2,.3,.5]);s=np.array([.2,.1,.05,.25]);assert np.allclose(blend_rgba(b,s),s+b*(1-s[3]))
    assert np.allclose(blend_rgba(b,[0,0,0,0],'Multiply'),b)
    for mode in BLENDS:assert np.isfinite(blend_rgba(b,s,mode)).all()
    h=History();after=deepcopy(scene);after['layers'][0]['opacity']=.3;h.record(scene,after,'One drag',row['id'],row['id']);assert h.snapshot()['undo']=='One drag';assert h.step()==scene;assert h.step(True)==after
    print('Composition: empty stack, v1 migration, affine grouping/reparenting, mask rejection, JSON round trip, W3C blend reference, gesture history passed')

if __name__=='__main__':run()
