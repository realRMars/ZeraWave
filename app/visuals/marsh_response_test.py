"""Standalone Marsh memory/cache/control checks; no GPU/listening claims."""
import math
import numpy as np
from marsh_response import MarshResponse,LampCache,MarshPalette
def run():
    memory=MarshResponse(7810);cache=LampCache();palette=MarshPalette()
    memory.advance(0,0,.6,.4,.3,.2,.9,10,True);selected=memory.events[:];assert len(selected)==1 and selected[0][1] in (2,3) and selected[0][2] in (-1,1)
    lamps,meta,wakes=cache.build(memory,0,0,10);first=cache.data.copy()
    memory.advance(0,0,.6,.4,.3,.2,.9,10,True);cache.build(memory,0,0,10);assert memory.events==selected and np.array_equal(first,cache.data)
    assert sum(v[0]>0 for v in meta)==1
    for i in range(120):memory.advance(i/60,1/60,.6,.4,.3,.2,.9,10+i/60,True)
    assert memory.events==selected
    memory.advance(2.1,.1,0,0,0,0,0,20,False);memory.advance(2.2,.1,.3,.4,.3,.2,.8,20,True);assert memory.visit==2 and memory.events[-1]!=selected[0]
    memory.advance(20,17.8,0,0,0,0,0,20,False);assert not memory.events and memory.energy<.001
    memory.advance(0,0,0,0,0,0,0,0,False);assert memory.serial==0 and memory.visit==0
    colors=[]
    for i in range(14400):
        travel=i*12.84;memory.advance(i,1,.5,.4,.3,.2,.9 if i%3==0 else 0.,travel,i%120<90)
        assert len(memory.events)<=4 and all(math.isfinite(v) for v in (memory.phase,memory.energy,memory.high))
        if i%60==0:
            cache.build(memory,i,i*.2,travel);color=np.array(palette.sample(memory));colors.append(color)
            assert cache.data.nbytes==672 and np.isfinite(cache.data).all()
            assert color.shape==(7,3) and np.isfinite(color).all() and (color>=0).all() and (color<=1).all()
            assert (abs(cache.data[:14,0])>=.6).all() and (abs(cache.data[:14,0])<1.6).all() and (cache.data[:14,1]>-1.4).all()
            # Every original six-neighbor lookup for forward samples remains cached.
            for z in np.linspace(travel,travel+23,24):
                for cell in range(math.floor(z/8)-1,math.floor(z/8)+2):assert cache.origin<=cell<cache.origin+7
    assert max(np.max(abs(color-colors[0])) for color in colors)>.2
    from preview_layers import ghostlight_memory_at,validate_layers
    from color_controls import family_setup,PALETTE_FAMILIES,validate_colors,targets_for
    from studio import validate_session,WORLD_TREE
    from technique_library import entries
    layer=validate_layers({'fog':dict(mode='together',seconds=12,items=[dict(id='ghostlight_memory',enabled=True,amount=.4)])})
    assert ghostlight_memory_at(layer,29,0)==.4 and ghostlight_memory_at({},29,0)==1 and ghostlight_memory_at({},31,0)==1 and ghostlight_memory_at({},34,0)==0
    assert any(t.id=='marsh.palette' for t in targets_for('marsh')) and not any(t.id=='marsh.palette' for t in targets_for('nebula'))
    for family in PALETTE_FAMILIES['marsh.palette']:assert validate_colors({'marsh.palette':family_setup('marsh.palette',family)})
    for version in (1,2,3):
        v=validate_session(dict(version=version,state='marsh',selection=['elements','fog','marsh'],layers=layer,color_overrides={'marsh.ghostlights':{'orbs':{'color':'#AABBDD'}},'fog.vapor':{'marsh':{'color':'#CCDDCC'}}}))
        assert v['state']=='marsh' and v['color_overrides']['marsh.ghostlights']['orbs']['color']=='#AABBDD' and v['color_overrides']['fog.vapor']['marsh']['color']=='#CCDDCC'
        if version==3:assert v['layers']==layer
    rows=entries(WORLD_TREE);assert len({row['id'] for row in rows})==len(rows)
    print('PASS individual lamp identity/same-time retention/hysteresis/settling/return/rewind,4h numeric cache672B/lane clearance/full-forward lookup coverage/palettes,legacy colors/v1-v3 sessions/scopes/amount/library IDs')
if __name__=='__main__':run()
