"""Standalone CPU ownership/delayed-save/endpoint checks; no GUI/GPU/capture."""
import argparse,ast,json,sys,time
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'app/visuals'))
from audio_scope import Scope,ScopeMailbox,SaveTicket,FORMS,endpoints
def rejected(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('Expected rejection')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    roster=next(n for n in ast.parse((ROOT/'app/visuals/renderer.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LIVE_FORMS' for t in n.targets))
    # Read canonical roster through its named tuple components without importing GL.
    env={}
    for n in ast.parse((ROOT/'app/visuals/renderer.py').read_text()).body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('BLEND_FORMS','AIR_FORMS','EARTH_FORMS','FOG_FORMS','PLASMA_FORMS','LIVE_FORMS') for t in n.targets):exec(compile(ast.Module(body=[n],type_ignores=[]),'canonical-roster','exec'),env)
    from development_forms import FRACTAL_FORMS
    assert len(env['LIVE_FORMS'])==30
    assert set(FORMS)==set(env['LIVE_FORMS'])|set(FRACTAL_FORMS)
    assert set(FRACTAL_FORMS)<=set(env['LIVE_FORMS']) and not set((37,38,39,40))&set(env['LIVE_FORMS'])
    validate=lambda form,target,c:dict(c) if target in ('planet.starfield','roots.growth') else (_ for _ in ()).throw(ValueError('Unknown target'))
    box=ScopeMailbox('runA','sessionA',validate);scopes=[Scope('runA','sessionA',f,t,1) for f,t in ((5,'planet.starfield'),(12,'roots.growth'))]
    for s in scopes:assert box.accept(dict(scope=s.packet(),settings=dict(enabled=True,gain=1.)))
    assert len(box.pending)==2
    s=scopes[0];assert not box.accept(dict(scope=s.packet(),settings=dict(enabled=True,gain=0.)))
    rejected(lambda:box.accept(dict(scope=dict(s.packet(),run='runB'),settings=dict(enabled=True,gain=0.))))
    rejected(lambda:box.accept(dict(scope=dict(s.packet(),session='sessionB'),settings=dict(enabled=True,gain=0.))))
    for form in (37,38,39,40,True):rejected(lambda f=form:Scope.read(dict(s.packet(),form=f)))
    assert box.accept(dict(scope=dict(s.packet(),revision=2),settings=dict(enabled=True,gain=.4),authored=dict(enabled=True,gain=.4)))
    assert box.accept(dict(scope=dict(s.packet(),revision=3),settings=dict(enabled=True,gain=.7)))
    commands=box.take();assert len(commands)==2 and not box.pending
    promoted=next(c for c in commands if c[0].form==5);assert promoted[2]['gain']==.4 and promoted[1]['gain']==.7
    s=promoted[0];c=promoted[1];ack=dict(scope=s.packet(),effective=c)
    ticket=SaveTicket.acknowledged(s,c,ack,10.,clock=lambda:10.5);ticket.verify(s,c)
    rejected(lambda:SaveTicket.acknowledged(s,c,ack,10.,clock=lambda:11.01))
    rejected(lambda:ticket.verify(scopes[1],c));rejected(lambda:ticket.verify(s,dict(c,gain=.8)))
    rejected(lambda:SaveTicket.acknowledged(s,c,dict(ack,scope=dict(s.packet(),revision=4)),10.,clock=lambda:10.5))
    cases=[]
    for state,seconds,expected in ((1,45.,[11,12]),(6,23.,[7,8]),(16,25.,[14,15]),
            (23,30.,[19,20]),(27,30.,[24,25]),(31,32.,[28,29]),(35,30.,[32,33])):
        r=SimpleNamespace(state_at=lambda t,s=state:s,transition_sequence=False)
        assert endpoints(r,seconds)['active']==expected,(state,endpoints(r,seconds))
    for source in FORMS:
        held=SimpleNamespace(state_at=lambda t,f=source:f,transition_sequence=False)
        assert endpoints(held,0.)['active']==[source]
        target=FORMS[(FORMS.index(source)+1)%len(FORMS)]
        for phase in (0.,.49,.5,1.):
            main=SimpleNamespace(state_at=lambda t:0,transition_sequence=False,director_current=source,director_target=target,transition_progress=lambda p=phase:p,director_recipe='tr_warp')
            packet=endpoints(main,0.);assert packet['active']==[source,target] and packet['primary']==(source if phase<.5 else target);cases.append(packet)
    pair=SimpleNamespace(state_at=lambda t:5 if t<12 else 0,transition_sequence=True,transition_settings=dict(hold=12.,duration=6.),debug_sequence=(5,12),director_recipe='tr_planet')
    assert endpoints(pair,3.)['active']==[5] and endpoints(pair,15.)['active']==[5,12]
    assert endpoints(SimpleNamespace(state_at=lambda t:37),0.)['active']==[]
    result=dict(evidence_class='CPU identity/transport-state/delayed-save and actual canonical roster checks; no rendering or capture',canonical_forms=30,endpoint_cases=len(cases),old_run_session_rejected=True,target_revision_isolation=True,coalesced_author_retained=True,delayed_save_destination_rejected=True,stale_ACK_rejected=True,unapproved_forms_excluded_from_Main=True,inspection_fractals_supported=True)
    assert not any(n in sys.modules for n in ('glfw','moderngl','capture','soundcard','tkinter'))
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2));print('Audio scope CPU checks PASS')
if __name__=='__main__':main()
