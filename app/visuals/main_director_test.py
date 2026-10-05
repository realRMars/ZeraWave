"""Standalone cheap Main state/selection and spatial equation contracts."""
import math,random,json
from pathlib import Path
from main_director import TRAITS,candidate_scores,transition_sample,transition_uniforms
from renderer import Renderer,LIVE_FORMS

def run():
    assert set(TRAITS)==set(LIVE_FORMS) and 36 in LIVE_FORMS and not {37,38,39,40}&set(LIVE_FORMS)
    priorities={s:.5 for s in LIVE_FORMS}
    for energy in (0.,.5,1.):
        for current in LIVE_FORMS:
            rows=candidate_scores(LIVE_FORMS,current,energy,False,40,{s:39. for s in LIVE_FORMS},[(current,s) for s in LIVE_FORMS],priorities,{})
            assert len(rows)==len(LIVE_FORMS)-1 and all(math.isfinite(r['score']) and r['score']>0 for r in rows)
    baseline=candidate_scores(LIVE_FORMS,26,.5,False,100,{},[],priorities,{})
    repeated=candidate_scores(LIVE_FORMS,26,.5,False,100,{},[(26,29)]*3,priorities,{})
    assert next(r for r in repeated if r['state']==29)['score']<next(r for r in baseline if r['state']==29)['score']*.1
    for aspect in (.5,16/9,3.):
        for style in (1,2,3):
            for angle in (-3.,0.,1.7):
                layout=(angle,.13,-.08,.37)
                for ix in range(11):
                    for iy in range(7):
                        x=(ix/10-.5)*aspect;y=iy/6-.5
                        values=[transition_sample(style,p/20,x,y,aspect,layout) for p in range(21)]
                        assert values[0]==0 and values[-1]==1 and all(0<=v<=1 and math.isfinite(v) for v in values)
                        assert all(b>=a for a,b in zip(values,values[1:]))
    assert transition_uniforms(0,.5,26,22,(0,0,0,0))=={}
    a,b=Renderer(seed=8291),Renderer(seed=8291);sequences=[[],[]];seen=set();styles=set()
    for i in range(14400):
        energy=.08+.83*(.5+.5*math.sin(i*.012))
        for k,r in enumerate((a,b)):
            r.parameters.scale=energy;r.parameters.movement=.08+.8*(.5+.5*math.sin(i*.006+.7));r.parameters.flux=.25*energy;r.parameters.impact=.85 if i%13==0 else 0.;r.parameters.beat_confidence=.8 if i%120<60 else .2;r.parameters.beat_tick=i%2==0
            count=len(r.director_history);last=r.director_history[-1]['seconds'] if count else None;r.update_blend(i,1.)
            if r.director_history and r.director_history[-1]['seconds']!=last:
                entry=r.director_history[-1];sequences[k].append(entry);seen.add(entry['state']);styles.add(entry.get('transition',0))
            assert len(r.director_history)<=64 and len(r.director_recent_pairs)<=12 and len(r.director_recent_styles)<=12 and len(r.director_last_seen)<=len(LIVE_FORMS)
            assert all(math.isfinite(v) for key,values in r.blend_values.items() for v in (values if isinstance(values,tuple) else (values,)))
            if r.director_pending:assert r.director_pending[1]-r.director_time<=.8+1e-9
    assert sequences[0]==sequences[1] and seen==set(LIVE_FORMS) and styles==set(range(6))
    normal=[Renderer() for _ in range(64)];openers=[]
    for r in normal:r.update_blend(0,0);openers.append(r.director_current)
    assert len(set(r.director_seed for r in normal))==64 and len(set(openers))>=12
    manual=Renderer(seed=12);manual.debug_state=26;manual.update_blend(0,1,False);assert not manual.director_history and manual.state_at(200)==26
    from studio import validate_session,command,DEFAULTS
    from technique_library import entries
    from studio import WORLD_TREE
    for version in (1,2,3):assert validate_session(dict(version=version,state='blend',selection=[],color_overrides={'molten.flow':{'heat':{'color':'#AABBDD'}}}))['state']=='blend'
    args=command(dict(DEFAULTS,state='blend',selection=[],source='Live system audio'),Path('unused-main-fixture-output'));assert '--seed' not in args
    rows=entries(WORLD_TREE);assert len({row['id'] for row in rows})==len(rows)
    report={'simulation_seconds':14400,'identical_seed_trace':True,'choices':len(sequences[0]),'reachable_observed':sorted(seen),'styles_observed':sorted(styles),'history_bounds':[64,12,12,len(LIVE_FORMS)],'fresh_session_seeds':64,'fresh_openers':openers,'legacy_region_equations':'PASS exact endpoints/finite0..1/monotonic across3 aspects/styles/angles/grid','manual_and_sessions':'PASS held/manual override, legacyv1-v3/live colors and normal Studio no forcedseed','limits':'4h cheap director simulation and CPU equations, not rendered soak/GPU equivalence/AV listening.'}
    print('PASS',json.dumps(report))
    return report
if __name__=='__main__':run()
