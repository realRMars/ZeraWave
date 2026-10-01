"""Standalone seeded generation and nested route contracts; no GPU/audio claims."""
import math
from pathlib import Path
from procedural_cosmos import destination,journey,uniforms,child_seed,planet_position,companion_position,length,PERIOD,OVERVIEW_FRACTION,visit_signature,authored_pigments,entry_phase

def main():
    poses=0
    counts=set();materials=set();star_modes=set()
    for seed in range(32):
        for index in range(5):
            first=destination(seed,index);counts.add(len(first.planets));materials.update(p[3] for p in first.planets)
            star_modes.add(first.stars[1]>0.)
            assert first==destination(seed,index) and first!=destination(seed,index+1)
            assert len(first.visits)==min(3,len(first.planets))
            assert len(set(first.visits))==len(first.visits)
            offset=index*PERIOD
            assert journey(seed,offset+PERIOD-1e-7)['next']==journey(seed,offset+PERIOD)['current']
            joins=[14.,18.,23.,59.,63.]
            count=max(1,len(first.visits) if first.planets else (2 if first.stars[1]>0 else 1))
            for slot in range(count):
                joins.extend(23.+36.*(OVERVIEW_FRACTION+(1.-OVERVIEW_FRACTION)/count*(slot+v)) for v in (0.,.28))
            for t in joins:
                before=journey(seed,offset+t-1e-7,offset+t);after=journey(seed,offset+t+1e-7,offset+t)
                assert max(abs(a-b) for a,b in zip(before['eye']+before['target'],after['eye']+after['target']))<2e-6,(seed,index,t)
            for tick in range(73):
                t=offset+23.+tick*.5;state=journey(seed,t,t)
                eye=tuple((a-b)/state['system_scale'] for a,b in zip(state['eye'],state['anchor']))
                assert all(math.isfinite(v) for v in state['eye']+state['target'])
                assert length(tuple(a-b for a,b in zip(state['eye'],state['target'])))>1e-6
                for i,spec in enumerate(first.planets):
                    center=planet_position(spec,t,first.traits[i])
                    assert length(tuple(a-b for a,b in zip(eye,center)))>spec[1]*1.05,(seed,index,t,spec)
                for i,radius in enumerate(first.stars[:2]):
                    if radius<=0:continue
                    center=(0.,0.,0.) if i==0 else companion_position(first,t)
                    assert length(tuple(a-b for a,b in zip(eye,center)))>radius*1.05,(seed,index,t,'star')
                poses+=1
            block=uniforms(seed,offset+40.)
            assert len(block['u_journey_planets'])==len(block['u_journey_traits'])==8
            assert block['u_journey_count']==len(first.planets)
    assert counts=={0,1,2,4,8} and materials==set(range(7)) and star_modes=={False,True}
    for t in (0.,3.,7.,13.9):
        state=journey(7301,t);assert state['target']==(0.,0.,0.) and state['bank']==0.
    assert journey(7301,0.)['eye']==journey(7301,3.9)['eye']  # stable centered opening
    assert journey(7301,11.)['eye'][1]<journey(7301,0.)['eye'][1]  # deliberate centered side reveal
    assert destination(244,0).star_kind>.95 and not destination(244,0).planets
    assert destination(7301,0).galaxy[0]!=destination(7301,1).galaxy[0]
    initial=journey(7301,14.)['anchor'];final=journey(7301,23.)['anchor']
    assert length((final[0],final[2]))<length((initial[0],initial[2]))*.8
    for i in range(64):destination(7301,i)
    assert destination.cache_info().currsize<=12
    assert uniforms(7301,108.)==uniforms(7301,108.)
    # Actual four-hour continuous journey plus short14-40s returns on the
    # existing timing scale. Recent palettes must not collapse to three families.
    for seed in (7301,42,1337):
        recent=[];identities=set();palette_set=set();layouts=set()
        for index in range(math.ceil(4*3600/PERIOD)+1):
            signature=visit_signature(seed,index);assert signature[1] not in recent[-12:]
            recent.append(signature[1]);palette_set.add(authored_pigments(seed,index));d=destination(seed,index)
            identities.add(d.seed);layouts.add((len(d.planets),d.stars[1]>0,tuple(p[3] for p in d.planets)))
            if d.star_kind<=.95:assert all(d.stars[0]>=p[1]*2. for p in d.planets)
            for clock in (0.,7.,63.,143.,301.,1200.):
                bodies=[(planet_position(p,clock,d.traits[i]),p[1]*(2.45 if p[3]==3 else 1.22)) for i,p in enumerate(d.planets)]
                stars=[((0.,0.,0.),d.stars[0]*1.12)]
                if d.stars[1]:stars.append((companion_position(d,clock),d.stars[1]*1.12))
                all_bodies=bodies+stars
                for i,(c,extent) in enumerate(all_bodies):
                    for other,other_extent in all_bodies[i+1:]:
                        assert length(tuple(x-y for x,y in zip(c,other)))>extent+other_extent,(seed,index,clock,'overlap')
        assert len(identities)==196 and len(palette_set)==196 and len(layouts)>100
        assert {entry_phase(seed,i) for i in range(5)}=={0.,18.8,24.,39.,63.4}
    assert authored_pigments.cache_info().currsize<=12
    # Force returns under existing Main timing limits without changing which
    # world the actual Main director selects (Galaxy remains disabled there).
    from renderer import Renderer,LIVE_FORMS
    from studio import DEFAULTS,validate_session,command
    from color_controls import galaxy_authored_colors
    assert 36 not in LIVE_FORMS
    for seed in (7301,42,1337):
        r=Renderer(seed=seed);r.set_galaxy_start(0,True);seconds=0.;visit=0;identities=[]
        while seconds<14400.:
            hold=(14.,22.,40.)[visit%3];steps=round(hold*5)
            for step in range(steps):
                r.update_galaxy_visit(True,.2,False)
                identity=int(r.galaxy_time//PERIOD)
                if not identities or identity!=identities[-1]:identities.append(identity)
                assert len(r.galaxy_recent)<=12
            before=r.galaxy_time;r.update_galaxy_visit(False,0.)
            gap=(14.+6.,40.+9.,22.+8.)[visit%3]*3
            r.update_galaxy_visit(False,gap);assert r.galaxy_time==before
            seconds+=hold+gap;visit+=1
        assert len(identities)>90 and len(set(identities))==len(identities)
        signature=[visit_signature(seed,i)[1] for i in identities]
        for i in range(len(signature)):assert signature[i] not in signature[max(0,i-12):i]
        print('four-hour forced Main timing',seed,'returns',visit,'destinations',len(identities),'unique palettes',len(set(authored_pigments(seed,i) for i in identities)))
        r.set_galaxy_start(12,True);first=r.galaxy_time;r.update_galaxy_visit(True,0.,True);assert r.galaxy_time==first
    for version in (1,2,3):
        old=dict(DEFAULTS,version=version,state='galaxy',selection=['cosmic','galaxy']);old.pop('galaxy_visit');old.pop('galaxy_entry')
        migrated=validate_session(old);assert migrated['galaxy_visit']=='0' and migrated['galaxy_entry']=='Full journey'
    session=validate_session(dict(DEFAULTS,version=3,state='galaxy',selection=['cosmic','galaxy'],galaxy_visit='17',galaxy_entry='Short return'))
    # Portable real WAV header fixture; no private recording is required.
    import tempfile,wave
    with tempfile.TemporaryDirectory(prefix='zerawave-galaxy-session-') as folder:
        track=Path(folder)/'silence.wav'
        with wave.open(str(track),'wb') as audio:
            audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(48000)
            audio.writeframes(bytes(480*2))
        for source in ('Synthetic preview','Test track','Live system audio'):
            values=dict(session,source=source,track=str(track));args=command(values,Path(folder)/'output')
            assert '--galaxy-visit' in args and args[args.index('--galaxy-visit')+1]=='17' and '--galaxy-short' in args
    manual={'galaxy.system':{'sun':{'color':'#FA9012'}}}
    assert galaxy_authored_colors(manual,36,7301,19)['galaxy.system']['sun']==manual['galaxy.system']['sun']
    untouched=galaxy_authored_colors({},36,7301,19)['galaxy.system']
    assert all(galaxy_authored_colors(manual,36,7301,19)['galaxy.system'][k]==v for k,v in untouched.items() if k!='sun')
    print('PASS forced Main returns/recent history, v1-v3 session migration and three CLI paths, authored pigment holds; no actual Main enable.')
    print(f'PASS: 32 seeds x5 destinations, counts0/1/2/4/8, seven materials, single/binary stars, {poses} adaptive camera poses/joins, nested identity and bounded12 cache.')

def projected_bounds_test():
    from procedural_cosmos import camera_basis
    tested=0;maximum=0.
    for seed in tuple(range(24))+(7301,42,1337,244):
        for index in (0,1,2,48,96,144):
            d=destination(seed,index)
            if d.star_kind>.95:continue  # beam-led pulsar composition is intentionally separate
            for sample in range(73):
                age=23.+sample*.49
                for speed in (.18,42.18):
                    t=index*PERIOD+age;clock=index*PERIOD+age*speed
                    state=journey(seed,t,clock)
                    eye=mul_local(state['eye'],state['anchor']);target=mul_local(state['target'],state['anchor'])
                    right,up,forward=camera_basis(eye,target,state['bank'])
                    delta=tuple(-a for a in eye);z=sum(a*b for a,b in zip(delta,forward));r=d.stars[0]*1.75
                    # Whole-body stellar compositions are fitted. World
                    # close-ups acquire their body early and deliberately let
                    # the primary leave; they must not be zoomed into empty
                    # wide shots merely to keep a behind-camera sun visible.
                    angular=math.asin(min(1.,r/length(delta)))
                    assert angular<=.358,(seed,index,age,'corona angular extent',angular)
                    stellar_view=True
                    if stellar_view:
                        assert z>r
                        radius=r/(z-r)/.95;maximum=max(maximum,radius)
                        x=(abs(sum(a*b for a,b in zip(delta,right)))+r)/(z-r)/.95
                        y=(abs(sum(a*b for a,b in zip(delta,up)))+r)/(z-r)/.95
                        assert radius<=.300001 and x<=.630001 and y<=.470001,(seed,index,age,x,y,radius)
                    tested+=1
            for age in (0.,4.,7.,9.6,11.,13.9):
                state=journey(seed,index*PERIOD+age)
                assert math.atan2(state['eye'][1],length((state['eye'][0],state['eye'][2])))>=math.radians(23.4)
    print('PASS projected primary+corona1.75bounds',tested,'quiet/full clocks;star-led4:3fit and all-pose angular bounds;max star-led radius',maximum,'grazing elevation>=23.4deg')


def mul_local(point,anchor):return tuple((a-b)/.004 for a,b in zip(point,anchor))


if __name__=='__main__':
    import sys
    if '--projected-bounds' in sys.argv:projected_bounds_test()
    else:main()
