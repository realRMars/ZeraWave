"""Native withdrawn Studio audio scopes, row reuse and delayed-ACK checks."""
import json,sys,tempfile,time
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from audio_controls import TARGETS as FORM_TARGETS,form_targets,defaults,bounds as form_bounds
from audio_scope import Scope
from starfield_tuning import StarfieldTuningWindow,TARGET,ART_TARGET,STAR_BOUNDS,choices_for_form
from star_tuning_profiles import StarProfileStore,TargetProfileStore,SHIPPED
from planet_audio_tuning import SPECS,baseline,bounds
from artifacts_audio_tuning import BASELINE as ART_BASE,BOUNDS as ART_BOUNDS
from transition_catalog import SCENES

def run():
    import tkinter as tk
    root=tk.Tk();root.withdraw();real=tk.Toplevel
    class HiddenClient(tk.Frame):
        def __init__(self,*a,**kw):self.host=real(*a,**kw);self.host.withdraw();super().__init__(self.host)
        def title(self,text):self.host.title(text)
        def geometry(self,size):w,h=map(int,size.split('x'));self.place(x=0,y=0,width=w,height=h)
        def protocol(self,*a):self.host.protocol(*a)
    v=None
    with tempfile.TemporaryDirectory(prefix='zerawave-native-scope-') as temp:
        folder=Path(temp);keys=(TARGET,ART_TARGET,*SPECS,*FORM_TARGETS)
        stores={t:TargetProfileStore(t,folder/(t+'.json'),folder/'profiles') for t in keys}
        observed=[];submitted=[]
        def submit(c,a=None,**kw):submitted.append((deepcopy(c),deepcopy(a),kw));return len(submitted)
        try:
            with patch('tkinter.Toplevel',side_effect=HiddenClient),patch('starfield_tuning.TargetProfileStore',side_effect=lambda target:stores[target]):
                v=StarfieldTuningWindow(root,submit,lambda *a,**kw:observed.append((a,kw)),store=stores[TARGET],artifact_store=stores[ART_TARGET],normal=True)
            widgets=tuple(str(w) for w in v.control_grid.winfo_children());cases=0
            def ack(form,target,revision=0,active=False,run='run',settings=None):
                c=deepcopy(settings if settings is not None else SHIPPED if target==TARGET else ART_BASE if target==ART_TARGET else baseline(target) if target in SPECS else defaults(target))
                now=time.perf_counter();scope=Scope(run,'session',form,target,revision)
                row=dict(scope=scope.packet(),settings=dict(c,enabled=False),effective=c,authored=c,revision=revision,active=active,available=True,rendered_wall=now,listening={},pilot_active=False)
                return dict(identity=dict(run=run,session='session'),endpoints=dict(primary=12,outgoing=12,incoming=None,progress=0.,recipe=None),editing_form=form,editing_target=target,pin=True,audio_targets={target:row},spectrum=None),now
            v.pin.set(True)
            for form in (*SCENES,0):
                for choice in choices_for_form(form):
                    v.select_form(form=form,target=choice.target_id);v.refresh(ack(form,choice.target_id),True);v.window.update_idletasks()
                    expected=STAR_BOUNDS if choice.target_id==TARGET else ART_BOUNDS if choice.target_id==ART_TARGET else bounds(choice.target_id) if choice.target_id in SPECS else form_bounds(choice.target_id)
                    assert list(v.vars)==list(expected),(form,choice.target_id)
                    assert [i for i,w in enumerate(v.sliders) if w.winfo_manager()=='grid']==list(range(len(expected)))
                    assert tuple(str(w) for w in v.control_grid.winfo_children())==widgets
                    assert v.window.host.state()=='withdrawn'
                    assert v.keyboard.held is None and v.keyboard.timer is None and v.pending is None
                    assert v.target_packet()['scope']['form']==form
                    assert form==v.form and choice.target_id==v.target.target_id
                    cases+=1
            # Delayed ACK of a previous row never paints the new controls.
            v.select_form(form=12,target='roots.growth');v.refresh(ack(12,'roots.growth'),True)
            old=ack(12,'roots.growth');v.select_form(form=11,target='form.11.membrane')
            before={k:var.get() for k,var in v.vars.items()};v.refresh(old,True)
            assert {k:var.get() for k,var in v.vars.items()}==before and v.target_packet() is None
            v.refresh(ack(11,'form.11.membrane'),True)
            # A held key and pending drag are cancelled before changing owner.
            v.keyboard.press(0,'Right');assert v.keyboard.held is not None
            v.select_form(form=12,target='roots.growth');assert v.keyboard.timer is None and v.keyboard.held is None and v.pending is None
            # Unsent values remain under their originating run/form/target.
            v.refresh(ack(12,'roots.growth'),True);v.enabled.set(True);v.vars['flux_branch'].set(.73);v.changed('flux_branch')
            assert v.pending is not None
            owner=v.owner_key();v.select_form(form=11,target='form.11.membrane')
            assert v.target_states[owner]['values']['flux_branch']==.73
            v.select_form(form=12,target='roots.growth');assert v.vars['flux_branch'].get()==.73
            v.refresh(ack(12,'roots.growth'),True);assert v.vars['flux_branch'].get()==.73
            try:v.ack_settings()
            except ValueError:pass
            else:raise AssertionError('Unsent values became Save Authored eligible')
            # Parking an edit must also survive an already acknowledged revision,
            # not just a destination that has never submitted revision zero.
            v.target_states.pop(owner,None);v.revision=7
            c=defaults('roots.growth');c['flux_branch']=1.2
            v.refresh(ack(12,'roots.growth',revision=7,settings=c),True)
            v.vars['flux_branch'].set(1.37);v.changed('flux_branch')
            owner=v.owner_key();v.select_form(form=11,target='form.11.membrane')
            assert v.target_states[owner]['values']['flux_branch']==1.37
            v.select_form(form=12,target='roots.growth');v.refresh(ack(12,'roots.growth',revision=7,settings=c),True)
            assert v.vars['flux_branch'].get()==1.37,'Acknowledged revision repainted a parked unsent edit'
            try:v.ack_settings()
            except ValueError:pass
            else:raise AssertionError('Parked unsent edit became Save Authored eligible')
            # Fresh run identity cannot reuse an earlier run's parked revision.
            v.refresh(ack(12,'roots.growth',run='new'),True);assert v.identity==('new','session') and v.revision is None
            assert v.target_states[owner]['values']['flux_branch']==1.37
            assert not list(folder.rglob('*.json'))
            from planet_mapping_monitor import MonitorWindow
            with patch('tkinter.Toplevel',side_effect=HiddenClient):monitor=MonitorWindow(root,lambda *a:None,normal=True)
            try:
                packet,stamp=ack(12,'roots.growth',active=True)
                packet['audio_targets']['roots.growth'].update(contributing=True,submissions={'flux_branch':dict(consumer='root_network',scope='CPU input',input=.4,slot=1.)},audio_terms={'branch_flex':.2})
                packet['audio']=dict(legacy={'flux':.4},band12={'edges':list(range(13)),'levels':[.4]*12});packet['audio_age_seconds']=0.
                monitor.refresh((packet,stamp),True)
                labels=[monitor.table.item(x)['text'] for x in monitor.table.get_children()]
                assert 'Analyzer flux' in labels and 'flux_branch input' in labels and 'Proxy branch_flex' in labels
                packet,stamp=ack(11,'form.11.membrane');monitor.refresh((packet,stamp),True)
                assert 'flux_branch input' not in [monitor.table.item(x)['text'] for x in monitor.table.get_children()]
                assert monitor.window.host.state()=='withdrawn'
            finally:monitor.close();monitor.window.host.destroy()
            return dict(evidence='Real withdrawn Tk controls; synthetic scoped ACKs; no GPU/capture/foreground focus',cases=cases,selectable_target_rows=cases,forms=27,transition_scope=True,single_widget_pool=True,delayed_ACK_rejected=True,held_key_and_drag_cancelled=True,unsent_original_owner_preserved=True,acknowledged_owner_unsent_preserved=True,old_run_revision_not_reused=True,authored_fixture_writes=0,general_mapping_monitor=True)
        finally:
            if v:v.close();v.window.host.destroy()
            root.destroy()

if __name__=='__main__':print(json.dumps(run(),indent=2));print('Studio Audio native scope checks PASS')
