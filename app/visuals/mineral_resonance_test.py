"""Focused numeric, cache, inspector and session contracts; standalone fixtures."""
import json,math
import numpy as np
from mineral_resonance import MineralResponse,FormationCache,formation,cavern_axis
from preview_layers import validate_layers,mineral_resonance_at,default_profile,ENVELOPERS
from color_controls import TARGETS,PALETTE_FAMILIES,family_setup,color_uniforms,targets_for,validate_colors

def run():
    # Exact free damped evolution: partitioned frame intervals agree analytically.
    results=[]
    for fps in (30,60,144):
        r=MineralResponse();r.v=.8
        for i in range(fps*2):r.advance((i+1)/fps,1/fps,0,0,0,0,0)
        results.append((r.x,r.v))
    assert np.max(np.abs(np.array(results)-results[0]))<1e-12
    active=[]
    for fps in (30,60,144):
        r=MineralResponse()
        for i in range(fps*3):r.advance((i+1)/fps,1/fps,.6,.6,.2,0,0)
        active.append((r.x,r.phase))
    assert np.ptp(np.array(active)[:,0])<.001
    assert np.ptp(np.array(active)[:,1])<1e-12
    r=MineralResponse()
    for i in range(120):r.advance(i/60,1/60,.6,.6,.2,.9,0)
    assert r.serial==1 and len(r.events)==1,'Held level was misread as repeated onset'
    for i in range(15):
        r.advance(3+i*.4,.2,.8,.6,.5,0,10)
        r.advance(3.2+i*.4,.2,.8,.6,.5,.9,10)
        assert len(r.events)<=4
    r.advance(30,20,0,0,0,0,10,False)
    assert not r.events and abs(r.x)<1e-4 and abs(r.v)<1e-4
    r.advance(1,0,0,0,0,0,0);assert r.serial==0 and not r.events
    cache=FormationCache();data=cache.update(0)
    assert len(data)==24576 and cache.origin==(-4,-2)
    assert cache.update(.2) is None
    for travel in (-1000,0,12,1000,100000):
        cache.origin=None;data=cache.update(travel);a=np.frombuffer(data,np.float32).reshape(24,64,4)
        assert np.isfinite(a).all()
        assert cache.origin[1]*2.8<=travel and (cache.origin[1]+24)*2.8>travel+55
        for z in range(24):
            for x in range(8):
                row=a[z,x*8:(x+1)*8];seed=row[0,0]
                for i in range(3):
                    rot=row[2+i*2];crystal=row[3+i*2]
                    # Radial bound includes square prism corners, root lean and maximum spring shear.
                    rad=crystal[1]*math.sqrt(2) if seed>=.27 else .22+.43*crystal[2]
                    bound=np.linalg.norm(row[1,:2])+crystal[3]+rad+crystal[0]*(np.linalg.norm(rot[2:])+.18*.62+.028)
                    assert bound<2.45,(bound,seed)
    # New anchored onset identifies a real forward cluster in world space.
    for travel in (0.,14.,75.,200.,600.):
        response=MineralResponse();response.advance(1.,1/60,.5,.5,.3,.9,travel)
        event=response.events[0];x=round(event[3]/2.8-.5);z=round(event[1]/2.8-.5)
        assert formation(x,z)[0][0]>=.27,(travel,event,'non-crystal anchor')
        assert event[1]>travel and event[1]<travel+13
        response.advance(2.,1.,0,0,0,0,travel+2)
        assert response.events[0]==event,'Camera motion moved onset anchor'
    # Sample actual eye clearances against the same convex planes at maximal shear.
    minimum=100.;samples=0
    for travel in np.linspace(0,600,3001):
        axis=cavern_axis(travel)
        for camera_sway in (-.08,.08):
            eye=np.array([axis+camera_sway,.1,travel])
            for z in range(math.floor(travel/2.8)-1,math.floor(travel/2.8)+2):
                for x in range(-4,4):
                    row=formation(x,z);kind=row[0][0];center=np.array([(x+.5)*2.8,(z+.5)*2.8])
                    if kind<.27 or abs(center[0]-cavern_axis(center[1]))<=1.1:continue
                    for i in range(3):
                        rot=row[2+i*2];cr=row[3+i*2];h,rad,seed,spread=cr
                        if seed<=.18:continue
                        for life in (-.16*.62-.028,.18*.62+.028):
                            offset=center+np.array(rot[:2])*spread+np.array(row[1][:2]);q=eye[[0,2]]-offset;y=eye[1]+2.5
                            local=np.array([rot[0]*q[0]-rot[1]*q[1],rot[1]*q[0]+rot[0]*q[1]])
                            local+=(np.array(rot[2:])+np.array([rot[1],-rot[0]])*life)*y
                            cap=.10+.18*seed if kind>.66 else .32+.42*seed
                            broken=.12+.24*((seed*7.1)%1) if seed>.62 else .015
                            hexagon=max(abs(local[0]),abs(local[1])) if kind>.66 else max(abs(local[0])*.866025+abs(local[1])*.5,abs(local[1]))
                            dist=max(hexagon-rad,hexagon+rad/cap*y-rad*h/cap,-y,y-h,y+local[0]*.22+local[1]*.13-h+broken)
                            assert dist>0.,(travel,x,z,i,life,dist,'camera inside crystal')
                            minimum=min(minimum,dist);samples+=1
    print('Camera convex-plane sampled margin',round(minimum,5),'configurations',samples)
    # Proportions and intergrowth vary without extra texture/cache allocation.
    quartz=[formation(x,z) for z in range(20) for x in range(-3,3) if .27<=formation(x,z)[0][0]<=.66]
    assert all(row[3][0]>row[7][0] for row in quartz)
    assert np.mean([row[3][0]/row[5][0] for row in quartz])>1.7
    # Proportional4h synthetic soak; bounded descriptors/events, no render/listening claim.
    response=MineralResponse();cache=FormationCache()
    for i in range(14400):
        response.advance(float(i),1.,.3+.25*math.sin(i*.011),.4,.2,.9 if i%3==0 else 0.,i*.9)
        cache.update(i*.9);assert len(response.events)<=4
    assert formation.cache_info().currsize<=512
    assert response.phase>0 and math.isfinite(response.x)
    assert formation.cache_info().currsize<=512
    profile=validate_layers({'earth':dict(mode='together',seconds=12.,items=[dict(id='mineral_resonance',enabled=True,amount=.4)])})
    assert mineral_resonance_at(profile,26,0)==.4 and mineral_resonance_at({},24,0)==0
    assert mineral_resonance_at({},26,0)==1
    assert mineral_resonance_at({},0,0)==1 and mineral_resonance_at({},0,40)==1
    assert mineral_resonance_at({'blend':dict(mode='authored',seconds=12.,items=[])},0,0)==1
    target=next(t for t in TARGETS if t.id=='mineral.prism')
    for name in PALETTE_FAMILIES[target.id]:
        colors={target.id:family_setup(target.id,name)};assert validate_colors(json.loads(json.dumps(colors)))==colors
        values=color_uniforms(colors,[target.id],1.);assert values['u_mineral_colors_on']==1
    manual={'mineral.prism':{'warm':{'color':'#A123BE'}}};assert validate_colors(manual)==manual
    assert target in targets_for('cavern')
    assert not any(item['id'] in ENVELOPERS for item in default_profile('blend')['items'])
    from renderer import LIVE_FORMS
    assert 36 in LIVE_FORMS and 37 not in LIVE_FORMS
    from studio import validate_session
    for version in (1,2,3):
        session=dict(version=version,state='cavern',selection=['elements','earth','cavern'],colors=manual,layers=profile)
        validated=validate_session(session);assert validated['selection']==['elements','earth','cavern']
        if version==3:assert validated['layers']==profile
    print('PASS: exact free-spring propagation30/60/144, driven convergence, onset hysteresis/decay/rewind, cache coverage/bounds/memory, palettes/manual colors, v1-v3 sessions and gates')

if __name__=='__main__':run()
