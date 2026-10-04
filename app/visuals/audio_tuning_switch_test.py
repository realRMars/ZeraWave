"""Native hidden Tk regression for Audio Tuning target switches; no GPU/capture."""
import argparse,hashlib,json,sys,tempfile,time
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from starfield_tuning import StarfieldTuningWindow,TARGETS,TARGET,ART_TARGET,STAR_BOUNDS
from star_tuning_profiles import StarProfileStore,TargetProfileStore,SHIPPED
from planet_audio_tuning import PlanetAudioTuning,SPECS,baseline,bounds
from artifacts_audio_tuning import ArtifactsAudioTuning,BASELINE as ART_BASE,BOUNDS as ART_BOUNDS
from spectrum_tuning_test import fft_frame

def run(folder,diagnose=False):
    import tkinter as tk
    root=tk.Tk();root.withdraw();real=tk.Toplevel
    class HiddenClient(tk.Frame):
        """Real native widgets in an allocated client; host always withdrawn."""
        def __init__(self,*a,**kw):
            self.host=real(*a,**kw);self.host.withdraw();super().__init__(self.host)
        def title(self,text):self.host.title(text)
        def geometry(self,size):
            width,height=map(int,size.split('x'));self.place(x=0,y=0,width=width,height=height)
        def protocol(self,*a):self.host.protocol(*a)
    stores={TARGET:StarProfileStore(folder/'star.json',folder/'profiles')}
    stores.update({t:TargetProfileStore(t,folder/(t+'.json'),folder/'profiles') for t in (ART_TARGET,*SPECS)})
    bins=fft_frame()[0].spectrum_frequencies.tolist();settings={}
    for i,t in enumerate(stores):
        c=deepcopy(SHIPPED if t==TARGET else ART_BASE if t==ART_TARGET else baseline(t))
        key='weight' if t==TARGET else next(k for k in c if k!='enabled')
        c[key]=1.25+i*.01;settings[t]=c
        stores[t].save_authored(c,bins);stores[t].save_profile('Preserved '+str(i),c,bins)
    persisted={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*.json')}
    backend=PlanetAudioTuning({t:settings[t] for t in SPECS});backend.resolve(True)
    artifact=ArtifactsAudioTuning(settings[ART_TARGET]);submitted=[];observed=[];failures=[]
    full=dict(version=1,pilot_active=True,presentation_active=True,rendered_wall=time.perf_counter(),
        settings=settings[TARGET],effective=settings[TARGET],authored=settings[TARGET],revision=0,analysis_age_seconds=0.,
        planet_tuning=backend.status(True,dict(bass=.2,flux=.3,sparkle=.4,impact=.5,raw_impact=.6),2),
        artifact_tuning=artifact.status(True,(.2,.3,.4),0.,True,bass=.2))
    def require(ok,message):
        if not ok:
            failures.append(message)
            if not diagnose:raise AssertionError(message)
    v=None
    try:
        with patch('tkinter.Toplevel',side_effect=HiddenClient),patch('starfield_tuning.TargetProfileStore',side_effect=lambda target:stores[target]):
            v=StarfieldTuningWindow(root,lambda *a,**kw:submitted.append((a,kw)),observed.append,
                store=stores[TARGET],artifact_store=stores[ART_TARGET])
        window_id=str(v.window);widget_ids=tuple(str(w) for w in v.control_grid.winfo_children())
        focus_requests=[];focus_dispatch=[]
        # Intercept focus ownership only: native virtual events and FocusIn bindings
        # still run. A withdrawn test must never steal Robert's foreground focus.
        for i,slider in enumerate(v.sliders):
            def focus(index=i,s=slider):
                focus_requests.append(index);s.event_generate('<FocusIn>');focus_dispatch.append(index)
            slider.focus_set=focus
        by_id={t.target_id:t for t in TARGETS}
        sequence=[TARGET,'planet.material.alloy',TARGET,'planet.material.interference_silk',TARGET,
            'planet.surface_response','planet.fx.sparkles','planet.surface_response',
            'planet.enveloper.digital_bloom','planet.fx.flecks',TARGET]
        sequence+=list(by_id)*3
        sequence+=list(reversed(by_id))
        cases=[];reachable=[];navigation=[];taps=[]
        for target_id in sequence:
            v.viewport.yview_moveto(1.) # Exercise target changes from the scroll tail.
            v.target_var.set(by_id[target_id].label);v.select_target()
            require(v.keyboard.timer is None and v.keyboard.held is None and v.pending is None,'Target switch retained a prior repeat/debounce timer')
            full['rendered_wall']=time.perf_counter();full['artifact_tuning']['rendered_wall']=time.perf_counter()
            full['planet_tuning']=backend.status(True,dict(bass=.2,flux=.3,sparkle=.4,impact=.5,raw_impact=.6),2)
            v.refresh((full,time.perf_counter()),True);v.window.update_idletasks()
            expected=STAR_BOUNDS if target_id==TARGET else ART_BOUNDS if target_id==ART_TARGET else bounds(target_id)
            n=len(expected)
            active=[i for i,s in enumerate(v.sliders) if s.winfo_manager()=='grid']
            registered=[len(v.control_grid.grid_slaves(row=i)) for i in range(len(v.sliders))]
            case=dict(target=target_id,expected=n,visible_rows=active,grid_children=registered,
                viewport_height=v.viewport.winfo_height(),shell_height=v.shell.winfo_height(),
                yview=list(v.viewport.yview()),same_window=str(v.window)==window_id)
            cases.append(case)
            require(active==list(range(n)),case)
            require(registered==[3]*n+[0]*(len(v.sliders)-n),dict(target=target_id,wrong_label_or_slider_visibility=registered))
            require(list(v.vars)==list(expected),dict(target=target_id,control_keys=list(v.vars)))
            require(all(v.vars[k].get()==settings[target_id][k] for k in expected),dict(target=target_id,manual_values_changed=True))
            require(v.window.host.state()=='withdrawn' and str(v.window)==window_id,'Test host revealed or window replaced')
            require(tuple(str(w) for w in v.control_grid.winfo_children())==widget_ids,'Control widgets replaced or deleted')
            if active!=list(range(n)):continue
            for i,key in enumerate(expected):
                v.sliders[i].event_generate('<FocusIn>');v.window.update_idletasks()
                # Withdrawn canvas windows retain stale OS root coordinates after
                # scrolling. Native content geometry + canvasy is authoritative
                # for their logical viewport; no visible-window claim is made.
                content_y=v.sliders[i].winfo_rooty()-v.shell.winfo_rooty()
                y=content_y-v.viewport.canvasy(0);h=v.viewport.winfo_height()
                require(0<=y and y+v.sliders[i].winfo_height()<=h,dict(target=target_id,key=key,y=y,height=h,
                    top=v.viewport.canvasy(0),scale_in_shell=v.sliders[i].winfo_rooty()-v.shell.winfo_rooty(),
                    shell_to_view=v.shell.winfo_rooty()-v.viewport.winfo_rooty(),yview=list(v.viewport.yview())))
                require(v.focus_labels[i][0].get().startswith('> '),dict(target=target_id,key=key,focus_marker_missing=True))
                reachable.append(dict(target=target_id,key=key,y=y,height=h))
                if hasattr(v,'control_rows'):
                    for widget in v.control_rows[i]:
                        wy=widget.winfo_rooty()-v.shell.winfo_rooty()-v.viewport.canvasy(0)
                        require(widget.winfo_height()>0 and 0<=wy and wy+widget.winfo_height()<=h,
                            dict(target=target_id,key=key,widget=str(widget),y=wy,height=widget.winfo_height()))
            enabled=[i for i,s in enumerate(v.sliders) if not s.instate(['disabled'])]
            require(all(i<n for i in enabled),dict(target=target_id,hidden_rows_enabled=enabled))
            require(bool(enabled),dict(target=target_id,no_enabled_controls=True))
            if not enabled:continue
            for j,i in enumerate(enabled):
                for event,wanted in (('NextLine',enabled[(j+1)%len(enabled)]),('PrevLine',enabled[(j-1)%len(enabled)])):
                    before=len(focus_requests);v.sliders[i].event_generate('<<'+event+'>>');v.window.update_idletasks()
                    require(len(focus_requests)==before+1 and focus_requests[-1]==wanted,dict(target=target_id,event=event,index=i,wanted=wanted))
                    navigation.append(dict(target=target_id,event=event,source=i,destination=wanted))
            i=enabled[-1];key=list(expected)[i];before=v.vars[key].get()
            v.sliders[i].event_generate('<<NextChar>>');v.window.update_idletasks();v.keyboard.release('Right')
            step=1. if key.endswith('_hz') else .01
            require(abs(v.vars[key].get()-before-step)<1e-8,dict(target=target_id,key=key,tap_failed=True))
            taps.append(dict(target=target_id,key=key,before=before,after=v.vars[key].get(),step=step))
            if v.pending is not None:v.window.after_cancel(v.pending);v.pending=None
            v.display_settings(settings[target_id])
            require(v.keyboard.timer is None and v.keyboard.held is None,'Keyboard repeat survived release')
            # A switch must cancel an in-progress hold/debounce before reusing
            # its slot for a different target. No event loop/timer is advanced.
            v.keyboard.press(enabled[-1],'Right')
        require(not submitted,'Selection-only test submitted changes to renderer')
        require({c['target'] for c in cases}==set(by_id),'Not every target tested')
        require(all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==s for p,s in persisted.items()),'Profile/authored data changed')
        return dict(success=not failures,evidence_class='Native hidden Tk layout/virtual-event regression with synthetic ACKs; no GPU, capture, foreground focus or hardware input',
            geometry=[v.window.winfo_width(),v.window.winfo_height()],cases=cases,reachable=reachable,
            navigation=navigation,taps=taps,failures=failures,fixture_files_unchanged=len(persisted),submitted_changes=len(submitted),
            focus_route='focus_set destinations intercepted; native FocusIn callbacks and virtual Up/Down/Right events executed without taking OS focus',
            tk_version=root.tk.call('info','patchlevel'),all24_targets=True,window_reopened=False,
            held_key_switch_cancels_repeat_and_debounce=True)
    finally:
        if v:v.close();v.window.host.destroy()
        root.destroy()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--diagnose',action='store_true');a=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='zerawave-tuning-switch-') as tmp:result=run(Path(tmp),a.diagnose)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(success=result['success'],switches=len(result['cases']),reachable_rows=len(result['reachable']),
        navigation_events=len(result['navigation']),keyboard_taps=len(result['taps']),failures=len(result['failures'])),indent=2))
    if not result['success']:raise SystemExit(1)
    print('Audio Tuning target-switch native checks PASS')
if __name__=='__main__':main()
