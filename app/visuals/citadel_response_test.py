"""Standalone numeric, saved control and bounded Citadel interpretation checks."""
import math,json
from citadel_response import TowerCadence
from preview_layers import tower_cadence_at,validate_layers,default_profile,ENVELOPERS,BITS
from color_controls import PALETTE_FAMILIES,family_setup,color_uniforms,validate_colors,targets_for
def run():
    results=[]
    for fps in (30,60,144):
        r=TowerCadence(12)
        for i in range(fps*3):r.advance((i+1)/fps,1/fps,.5,.6,.4,0,True)
        results.append((r.wind,r.light,r.phase))
    assert max(abs(a-b) for r in results for a,b in zip(r,results[0]))<.008
    r=TowerCadence(7301);r.advance(0.,0,.5,.4,.3,.9,True);anchor=r.events[0]
    for i in range(120):r.advance(i/60,1/60,.5,.4,.3,.9,True)
    assert r.serial==1 and len(r.events)==1 and r.events[0]==anchor
    r.advance(2.1,.1,0,0,0,0,False);r.advance(2.2,.1,.3,.3,.3,.8,True);assert r.visit==2
    assert r.events[-1][3]!=anchor[3], 'Return burst variation must advance; tower motifs may recur'
    r.advance(12,10,0,0,0,0,False);assert not r.events and r.wind<.02 and r.light<.02 and r.settle<1e-5
    r.advance(1,0,0,0,0,0,False);assert r.serial==0 and r.visit==0
    maxevents=0
    for i in range(14400):
        r.advance(i,1,.5,.4,.2,.9 if i%3==0 else 0.,i%120<90);maxevents=max(maxevents,len(r.events))
        assert len(r.events)<=4 and all(math.isfinite(v) for v in (r.wind,r.light,r.phase,r.settle))
    assert maxevents>0
    layer=validate_layers({'air':dict(mode='together',seconds=12,items=[dict(id='tower_cadence',enabled=True,amount=.4)])})
    assert tower_cadence_at(layer,22,0)==.4 and tower_cadence_at({},22,0)==1 and tower_cadence_at({},26,0)==0
    assert tower_cadence_at({'air':dict(mode='together',seconds=12,items=[])},22,0)==0
    assert BITS['tower_cadence']==0 and max(BITS.values())<=1073741824
    assert not any(item['id'] in ENVELOPERS for item in default_profile('blend')['items'])
    for name in PALETTE_FAMILIES['citadel.lantern']:
        setup=family_setup('citadel.lantern',name);data=validate_colors({'citadel.lantern':setup})
        assert validate_colors(json.loads(json.dumps(data)))==data
        assert color_uniforms(data,['citadel.lantern'],1.)['u_citadel_colors_on']==1
    assert any(t.id=='citadel.lantern' for t in targets_for('citadel'))
    assert not any(t.id=='citadel.lantern' for t in targets_for('cavern'))
    from studio import validate_session
    for version in (1,2,3):
        s=validate_session(dict(version=version,state='citadel',selection=['elements','air','citadel'],layers=layer,color_overrides={'citadel.lantern':{'lamp':{'color':'#FFA144'}}}))
        assert s['selection']==['elements','air','citadel']
        if version==3:assert s['layers']==layer
    print('PASS Tower Cadence frame convergence, held-hit hysteresis, return variation, release/rewind,4h bounded synthetic soak, amount/mask, palettes/scopes and v1-v3 sessions')
if __name__=='__main__':run()
