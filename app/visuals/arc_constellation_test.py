"""Focused standalone chart/cache/control checks; numeric duration is not visual variety."""
import math
import numpy as np
from arc_constellation import ArcNetwork,FluxMemory

def run():
 m=FluxMemory(7424);n=ArcNetwork();m.advance(0,0,.6,.4,.3,.2,.9,True);event=m.events[:]
 a=n.build(m,.5);b=n.build(m,.5);assert a==b and len(a[0])==3264
 m.advance(1.4,1.4,.6,.4,.3,.2,0.,True);data,bounds,groups,nodes,shapes,links=n.build(m,1.4)
 assert bounds[8][0]<1000 and links[8][2]>0 and max(q[2] for q in shapes)>0
 before=n.data.copy();_ = n.build(m,1.4);assert np.array_equal(before,n.data) and m.events==event
 _,bounds,_,_,shapes,links=n.build(m,1.4,0.);assert all(q[0]==1000. for q in bounds[8:]) and not any(q[0] for q in links) and not any(q[2] for q in shapes)
 # Accelerated four hours, sample actual descriptors every minute and bounded memory each second.
 m.reset();families=set();active_counts=set()
 for i in range(14400):
  m.advance(i,1.,.5,.4,.3,.2,.9 if i%4==0 else 0.,i%120<95)
  assert len(m.events)<=4 and all(math.isfinite(v) for v in (m.phase,m.energy,m.high,m.strain))
  families.add(int(m.phase*.014+max(0,m.visit-1)*.41)%3)
  if i%60==0:
   data,bounds,groups,nodes,shapes,links=n.build(m,i);assert len(data)==3264 and len(bounds)==12 and len(groups)==48 and len(nodes)==9
   assert np.isfinite(n.data).all() and (n.data[:,:,2]>0).all();assert np.isfinite(np.array(nodes)).all()
   for row in range(12):
    if bounds[row][0]==1000:continue
    for j in range(4):
     q=n.data[row,j*4:j*4+5,:2];box=groups[row*4+j];assert (q>=np.array(box[:2])-1e-6).all() and (q<=np.array(box[2:])+1e-6).all()
   active_counts.add(sum(q[0]!=1000 for q in bounds))
 assert families=={0,1,2}
 from preview_layers import arc_relay_at,validate_layers
 from color_controls import targets_for,PALETTE_FAMILIES,family_setup,validate_colors
 from studio import validate_session,WORLD_TREE
 from technique_library import entries
 profile=validate_layers({'plasma':dict(mode='together',seconds=12,items=[dict(id='arc_relay',enabled=True,amount=.35)])})
 assert arc_relay_at(profile,33,0)==.35 and arc_relay_at({},33,0)==1 and arc_relay_at({},32,0)==0
 assert any(t.id=='arcs.asterism' for t in targets_for('arcs')) and not any(t.id=='arcs.asterism' for t in targets_for('magnetic'))
 for family in PALETTE_FAMILIES['arcs.asterism']:assert validate_colors({'arcs.asterism':family_setup('arcs.asterism',family)})
 for version in (1,2,3):
  v=validate_session(dict(version=version,state='arcs',selection=['elements','plasma','arcs'],layers=profile,color_overrides={'arcs.charge':{'arcs':{'color':'#AABBDD'}}}))
  assert v['state']=='arcs' and v['color_overrides']['arcs.charge']['arcs']['color']=='#AABBDD'
  if version==3:assert v['layers']==profile
 rows=entries(WORLD_TREE);assert len(rows)==len({r['id'] for r in rows})
 # No-drawable frames retain the prior surface and pump events before touching GL.
 from arc_constellation import ArcStage
 from renderer import Renderer
 import glfw
 stage=object.__new__(ArcStage);surface=object();stage.texture=surface;stage.fbo=surface;stage.size=(640,360)
 renderer=object.__new__(Renderer);renderer.window=object();polls=[];renderer.poll_events=lambda:polls.append(True)
 get_size=glfw.get_framebuffer_size
 try:
     for bad in ((0,360),(640,0),(0,0),(-1,360),(640,-1)):
         stage.draw(bad);assert stage.texture is surface and stage.fbo is surface and stage.size==(640,360)
         glfw.get_framebuffer_size=lambda window,bad=bad:bad;count=len(polls);renderer.render(1.);assert len(polls)==count+1
 finally:glfw.get_framebuffer_size=get_size
 print('PASS chart determinism, persistent event, relay/release amount, 4h numeric cache/group bounds & palette families, 3264B paths, legacy colors, v1-v3 sessions, scope and unique library IDs, invalid-surface retention/event polling')
if __name__=='__main__':run()
