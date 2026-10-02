"""Standalone bounded-history/palette/control checks; no GPU or listening claims."""
import math
import numpy as np
from auroral_memory import FluxMemory,VeilPalette
def run():
    memory=FluxMemory(7680);palette=VeilPalette();samples=[]
    for i in range(14400):
        memory.advance(i,1,.5,.4,.3,.2,.9 if i%3==0 else 0.,i%120<90)
        colors=np.array(palette.sample(memory))
        assert colors.shape==(6,3) and np.isfinite(colors).all() and (colors>=0).all() and (colors<=1).all()
        assert len(memory.events)<=4 and all(math.isfinite(v) for v in (memory.phase,memory.energy,memory.high,memory.strain))
        if i%600==0:samples.append(colors)
    assert max(np.max(abs(c-samples[0])) for c in samples)>.2
    memory.advance(0,0,0,0,0,0,0,False);assert not memory.events and memory.phase==0
    from preview_layers import veil_memory_at,validate_layers
    from color_controls import PALETTE_FAMILIES,family_setup,validate_colors,targets_for
    from studio import validate_session,WORLD_TREE
    from technique_library import entries
    layer=validate_layers({'plasma':dict(mode='together',seconds=12,items=[dict(id='veil_memory',enabled=True,amount=.4)])})
    assert veil_memory_at(layer,34,0)==.4 and veil_memory_at({},34,0)==1 and veil_memory_at({},35,0)==1 and veil_memory_at({},26,0)==0
    assert any(t.id=='auroral.veil' for t in targets_for('auroral'))
    assert not any(t.id=='auroral.veil' for t in targets_for('magnetic'))
    for family in PALETTE_FAMILIES['auroral.veil']:assert validate_colors({'auroral.veil':family_setup('auroral.veil',family)})
    for version in (1,2,3):
        v=validate_session(dict(version=version,state='auroral',selection=['elements','plasma','auroral'],layers=layer,color_overrides={'auroral.curtains':{'sheets':{'color':'#AABBDD'}}}))
        assert v['state']=='auroral' and v['color_overrides']['auroral.curtains']['sheets']['color']=='#AABBDD'
        if version==3:assert v['layers']==layer
    rows=entries(WORLD_TREE);assert len({row['id'] for row in rows})==len(rows)
    print('PASS Veil 4h accelerated numeric bounds/evolving finite palettes/rewind, six-role scopes, amount, legacy colors/v1-v3 sessions/library unique IDs')
if __name__=='__main__':run()
