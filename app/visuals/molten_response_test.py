"""Standalone musical memory/control/session checks; numeric evidence only."""
import math
import numpy as np
from molten_response import MoltenMemory,MoltenPalette

def run():
 m=MoltenMemory(8100);p=MoltenPalette();m.advance(0,0,.6,.4,.3,.2,.9,True);event=m.cooling[:]
 assert len(event)==1 and abs(event[0][1]-m.center(event[0][2]))<1e-10
 m.advance(0,0,.6,.4,.3,.2,.9,True);assert m.cooling==event
 for i in range(1,121):m.advance(i/60,1/60,.6,.4,.3,.2,.9,True)
 assert m.cooling==event and m.pressure>.4 and m.shear>.3 and m.high>.2
 before=m.pressure;m.advance(2.1,.1,0,0,0,0,0,False);assert 0<m.pressure<before
 m.advance(2.2,.1,.6,.4,.3,.2,.8,True);assert len(m.cooling)==2 and m.visit==2
 m.advance(10,7.8,0,0,0,0,0,False);assert not m.events and len(m.cooling)==2
 m.advance(21,11,0,0,0,0,0,False);assert not m.cooling
 m.advance(0,0,0,0,0,0,0,False);assert m.serial==0 and m.pressure==0 and m.visit==0
 colors=[]
 for i in range(14400):
  m.advance(i,1,.5,.4,.3,.2,.9 if i%3==0 else 0.,i%120<90)
  assert len(m.cooling)<=4 and len(m.events)<=4 and len(m.deposits())==4
  assert all(math.isfinite(v) for v in (m.phase,m.pressure,m.shear,m.high,m.temperature))
  if i%60==0:
   c=np.array(p.sample(m));colors.append(c);assert c.shape==(6,3) and np.isfinite(c).all() and (c>=0).all() and (c<=1).all()
 assert max(np.max(abs(c-colors[0])) for c in colors)>.1
 # Sustained bands remain independent without percussion.
 low=MoltenMemory();mid=MoltenMemory();high=MoltenMemory()
 for i in range(60):
  low.advance(i/15,1/15,.8,0,0,0,0,True);mid.advance(i/15,1/15,0,.8,0,0,0,True);high.advance(i/15,1/15,0,0,.8,0,0,True)
 assert low.pressure>.5 and low.shear==0 and low.high==0
 assert mid.shear>.7 and mid.pressure==0 and high.high>.7 and high.pressure==0 and not low.cooling
 from preview_layers import current_memory_at,validate_layers
 from color_controls import family_setup,PALETTE_FAMILIES,validate_colors,targets_for
 from studio import validate_session,WORLD_TREE
 from technique_library import entries
 layer=validate_layers({'fire':dict(mode='together',seconds=12,items=[dict(id='current_memory',enabled=True,amount=.4)])})
 assert current_memory_at(layer,15,0)==.4 and current_memory_at({},15,0)==1 and current_memory_at({},16,0)==1 and current_memory_at({},29,0)==0
 assert any(t.id=='molten.palette' for t in targets_for('molten')) and not any(t.id=='molten.palette' for t in targets_for('firescape'))
 for family in PALETTE_FAMILIES['molten.palette']:assert validate_colors({'molten.palette':family_setup('molten.palette',family)})
 for version in (1,2,3):
  v=validate_session(dict(version=version,state='molten',selection=['elements','fire','molten'],layers=layer,color_overrides={'molten.flow':{'heat':{'color':'#AABBDD'}},'fire.details':{'seams':{'color':'#CCDDCC'}}}))
  assert v['state']=='molten' and v['color_overrides']['molten.flow']['heat']['color']=='#AABBDD'
  if version==3:assert v['layers']==layer
 rows=entries(WORLD_TREE);assert len({r['id'] for r in rows})==len(rows)
 # Evaluate the actual renderer presence expression against its authoritative uniform pack.
 # This fails for nonexistent family keys, even if held state15 tests keep passing.
 import ast
 from pathlib import Path
 from types import SimpleNamespace
 from renderer import world_uniforms
 tree=ast.parse(Path(__file__).with_name('renderer.py').read_text())
 expression=next(node.value for node in ast.walk(tree) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='molten_present' for target in node.targets))
 expression=compile(ast.Expression(expression),'actual molten presence','eval')
 for weights,expected in (({15:1.},True),({15:.5,19:.5},True),({14:1.},False),({19:1.},False),({17:.5,19:.5},False),({},False)):
  packed=world_uniforms(weights);assert eval(expression,{'state':0,'current_time':12.,'self':SimpleNamespace(blend_values=packed)})==expected,(weights,packed)
 assert eval(expression,{'state':15,'current_time':0.,'self':SimpleNamespace(blend_values={})})
 for t,expected in ((18.,False),(19.,True),(28.,True),(55.9,True),(56.,False)):
  assert eval(expression,{'state':16,'current_time':t,'self':SimpleNamespace(blend_values={})})==expected
 print('PASS actual Main presence expression/authoritative u_world_mix Fire slot3 and u_fire_mix Molten slot1; fresh/mixed/other-world/held/cycle contract')
 print('PASS pressure/shear/high independence, selected persistent vents/hysteresis/same-time/release/18s cooling/return/rewind,4h numeric bounds,6-role palettes,amount/scopes/legacy/v1-v3/Library IDs')
if __name__=='__main__':run()
