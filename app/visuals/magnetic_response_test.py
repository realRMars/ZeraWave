"""Standalone actual-memory/cache/control tests; no audio model or GPU claims."""
import math,json
import numpy as np
from magnetic_response import FluxMemory,FieldPaths
def run():
    states=[]
    for fps in (30,60,144):
        r=FluxMemory(12)
        for i in range(fps*3):r.advance((i+1)/fps,1/fps,.5,.6,.4,.2,0,True)
        states.append((r.energy,r.high,r.phase))
    assert max(abs(a-b) for s in states for a,b in zip(s,states[0]))<.008
    r=FluxMemory();paths=FieldPaths();r.advance(0,0,.5,.4,.3,.2,.9,True);anchor=r.events[0]
    for i in range(120):r.advance(i/60,1/60,.5,.4,.3,.2,.9,True)
    assert len(r.events)==1 and r.events[0]==anchor
    r.advance(2.1,.1,0,0,0,0,0,False);r.advance(2.2,.1,.3,.3,.3,.2,.8,True);assert r.visit==2 and r.events[-1]!=anchor
    r.advance(20,17.8,0,0,0,0,0,False);assert not r.events and r.energy<.001
    r.advance(1,0,0,0,0,0,0,False);assert r.serial==0 and r.visit==0
    # Four hours accelerated1Hz; sample the full cache each minute and actual event ages.
    for i in range(14400):
        r.advance(i,1,.5,.4,.2,.1,.8 if i%3==0 else 0.,i%120<90)
        assert len(r.events)<=4 and all(math.isfinite(v) for v in (r.energy,r.high,r.phase,r.strain))
        if i%60==0:
            data,bounds,groups,rot=paths.build(r,i);assert len(data)==9408 and len(bounds)==12 and len(groups)==96
            assert np.isfinite(paths.data).all() and (paths.data[:,:,2]>0).all()
            for row in range(8):
                for g in range(8):
                    q=paths.data[row,g*6:g*6+7,:2];b=groups[row*8+g]
                    assert (q>=np.array(b[:2])-1e-6).all() and (q<=np.array(b[2:])+1e-6).all()
    from preview_layers import magnetic_memory_at,validate_layers
    from color_controls import PALETTE_FAMILIES,family_setup,validate_colors,targets_for
    from studio import validate_session
    layer=validate_layers({'plasma':dict(mode='together',seconds=12,items=[dict(id='flux_memory',enabled=True,amount=.4)])})
    assert magnetic_memory_at(layer,32,0)==.4 and magnetic_memory_at({},32,0)==1 and magnetic_memory_at({},26,0)==0
    assert any(t.id=='magnetic.bloom' for t in targets_for('magnetic'))
    assert not any(t.id=='magnetic.bloom' for t in targets_for('arcs'))
    for family in PALETTE_FAMILIES['magnetic.bloom']:assert validate_colors({'magnetic.bloom':family_setup('magnetic.bloom',family)})
    for version in (1,2,3):
        v=validate_session(dict(version=version,state='magnetic',selection=['elements','plasma','magnetic'],layers=layer,color_overrides={'magnetic.field':{'loops':{'color':'#AABBDD'}}}));assert v['state']=='magnetic'
        assert v['color_overrides']['magnetic.field']['loops']['color']=='#AABBDD'
        if version==3:assert v['layers']==layer
    from technique_library import entries
    from studio import WORLD_TREE
    rows=entries(WORLD_TREE);assert len({row['id'] for row in rows})==len(rows),'Library tree IDs must be unique'
    print('PASS Flux Memory convergence/hysteresis/release/rewind/return,4h numeric bounds,12x49 cache/group coverage9408B, legacy colors, palettes/scopes, amount and v1-v3 sessions')
if __name__=='__main__':run()
