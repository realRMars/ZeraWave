"""Native hidden multi-window drawing/ACK test; no GPU or real capture."""
import argparse,hashlib,json,sys,tempfile,time
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from spectrum_widget import SpectrumRange,SpectrumFeed,MAX_RANGES
from starfield_tuning import StarfieldTuningWindow,TARGETS,TARGET,ART_TARGET
from star_tuning_profiles import StarProfileStore,TargetProfileStore,SHIPPED
from artifacts_audio_tuning import ArtifactsAudioTuning,BASELINE,BOUNDS,WINDOWS
from spectral_listening import SpectralListening
from spectrum_tuning_test import fft_frame

def run(folder):
    import tkinter as tk
    root=tk.Tk();root.withdraw();real=tk.Toplevel
    class HiddenClient(tk.Frame):
        def __init__(self,*a,**kw):
            self.host=real(*a,**kw);self.host.withdraw();super().__init__(self.host)
        def title(self,text):self.host.title(text)
        def geometry(self,size):
            width,height=map(int,size.split('x'));self.place(x=0,y=0,width=width,height=height)
        def protocol(self,*a):self.host.protocol(*a)
    star=StarProfileStore(folder/'star.json',folder/'profiles')
    artifact=TargetProfileStore(ART_TARGET,folder/'artifact.json',folder/'profiles')
    backend=ArtifactsAudioTuning();listen=SpectralListening(backend.analysis_settings)
    frame,_=fft_frame();feed=SpectrumFeed();feed.enable(True);revision=[0];submitted=[]
    def submit(c,authored=None,target=TARGET):
        assert target==ART_TARGET;revision[0]+=1;submitted.append(deepcopy(c))
        assert backend.submit(revision[0],c,authored);backend.resolve(True);return revision[0]
    def store(target):return TargetProfileStore(target,folder/(target+'.json'),folder/'profiles')
    v=None
    try:
        with patch('tkinter.Toplevel',side_effect=HiddenClient),patch('starfield_tuning.TargetProfileStore',side_effect=store):
            v=StarfieldTuningWindow(root,submit,lambda enabled:None,store=star,artifact_store=artifact)
        artifact_target=next(t for t in TARGETS if t.target_id==ART_TARGET)
        v.target_var.set(artifact_target.label);v.select_target()
        full={};spectrum=None
        def ack(measure=True,active=True,stale=False):
            nonlocal spectrum
            if measure:backend.observe(listen.process(frame.spectrum_frequencies,frame.spectrum_magnitudes,2048,'fixture'))
            feed.observe(frame,2048);spectrum=feed.snapshot()
            p=backend.status(active,(.2,.3,.4),12.,True,bass=.2)
            if stale:p['rendered_wall']-=2.
            full.update(version=1,pilot_active=True,presentation_active=True,revision=0,settings=SHIPPED,
                effective=SHIPPED,authored=SHIPPED,analysis_age_seconds=0.,spectrum=spectrum,artifact_tuning=p)
            v.refresh((full,time.perf_counter()),True);v.window.update_idletasks()
            v.spectrum.draw(force=True);return p
        def apply(c,measure=True):
            submit(c,target=ART_TARGET);return ack(measure)
        def shown(slot):return [v.spectrum.canvas.itemcget(x,'state') for x in v.spectrum.range_items[slot]]
        def check(flux,sparkle):
            for slot,enabled in enumerate((flux,sparkle)):
                assert shown(slot)==['normal' if enabled else 'hidden']*4,(slot,shown(slot))
            assert v.spectrum.canvas.itemcget('weight','state')=='hidden'
            assert v.spectrum.canvas.itemcget('spectrum','state')=='normal'
            assert len(v.vars)==len(BOUNDS) and all(v.sliders[i].winfo_manager()=='grid' for i in range(len(BOUNDS)))
            assert v.window.host.state()=='withdrawn'
        c=dict(BASELINE,enabled=True,flux_range_enabled=True,flux_start_hz=60.,flux_end_hz=800.,
            sparkle_range_enabled=True,sparkle_start_hz=400.,sparkle_end_hz=1000.,flux_stretch=1.37)
        apply(c);check(True,True)
        canvas=v.spectrum.canvas;pool=tuple(tuple(items) for items in v.spectrum.range_items)
        assert len(pool)==MAX_RANGES and sum(map(len,pool))==32
        assert canvas.itemcget(pool[0][0],'fill')=='#f9bf62'
        assert canvas.itemcget(pool[1][0],'fill')=='#72a9ff'
        assert not canvas.itemcget(pool[0][0],'dash') and canvas.itemcget(pool[1][0],'dash')=='6 3'
        a,b=canvas.coords(pool[0][0]),canvas.coords(pool[1][0])
        assert a[0]<b[0]<a[4]<b[4] and a[3]!=b[3],(a,b)
        overlap=dict(flux_span=a,sparkle_span=b,legend=v.spectrum.legend.get())
        focuses=[]
        for key in ('flux_start_hz','sparkle_start_hz','flux_end_hz','sparkle_end_hz'):
            i=list(v.vars).index(key);v.sliders[i].event_generate('<FocusIn>');v.window.update_idletasks()
            check(True,True);name=key.split('_')[0]
            assert v.spectrum.focused_range==name and '[editing]' in v.spectrum.legend.get()
            assert canvas.itemcget(pool[0 if name=='flux' else 1][0],'width')=='3.0'
            focuses.append(dict(control=key,legend=v.spectrum.legend.get()))
        # Unacknowledged position edits preserve both last-applied windows.
        old=tuple(v.spectrum.ranges);v.vars['flux_start_hz'].set(120.);v.changed('flux_start_hz');ack()
        assert tuple(v.spectrum.ranges)==old;check(True,True)
        v.send();ack();assert v.spectrum.ranges[0].start_hz==120. and v.spectrum.ranges[1].start_hz==400.
        c=deepcopy(backend.settings)
        # Actual native fine-tuning callback, coalesced submit and analysis ACK.
        i=list(v.vars).index('flux_start_hz');before=v.vars['flux_start_hz'].get()
        v.sliders[i].event_generate('<<NextChar>>');v.keyboard.release('Right')
        assert v.vars['flux_start_hz'].get()==before+1.;v.send();ack();c=deepcopy(backend.settings)
        assert v.spectrum.ranges[0].start_hz==before+1.
        # Save routes still use acknowledged controls and the original store.
        v.profile_name.set('Both windows');v.save_profile();assert 'Saved named profile' in v.profile_status.get()
        assert v.save_authored();ack()
        baseline_bytes=artifact.authored_path.read_bytes();profile_files=list(artifact.profile_dir.glob('*.json'))
        assert len(profile_files)==1
        profile_bytes=profile_files[0].read_bytes()
        _,loaded=artifact.load_profile(profile_files[0],[0.]+frame.spectrum_frequencies[1:].tolist())
        assert loaded==dict(c,enabled=True) and artifact.authored==dict(c,enabled=True)
        toggles=[]
        for f,s in ((False,True),(True,False),(False,False),(True,True)):
            apply(dict(c,flux_range_enabled=f,sparkle_range_enabled=s));check(f,s)
            legend=v.spectrum.legend.get()
            assert ('Flux (gold)' in legend and 'Sparkle (blue)' in legend)
            assert legend.count('OFF - original feature')==len(WINDOWS)-int(f)-int(s)
            toggles.append(dict(flux=f,sparkle=s,legend=legend))
        # Waiting channels remain distinguishable, but are never called applied.
        pending=dict(c,flux_start_hz=200.);apply(pending,measure=False);check(True,True)
        assert not v.spectrum.ranges[0].ready and 'waiting for matching analysis' in v.spectrum.legend.get()
        assert canvas.itemcget(pool[0][0],'dash')=='2 3'
        ack();check(True,True)
        ack(active=False);check(False,False);assert 'target inactive - hidden' in v.spectrum.legend.get()
        ack(stale=True);check(False,False);assert 'stale ACK - hidden' in v.spectrum.legend.get()
        apply(dict(c,sparkle_start_hz=2000.,sparkle_end_hz=4000.));check(True,True)
        assert canvas.coords(pool[0][0])[4]<canvas.coords(pool[1][0])[0]
        current=tuple(v.spectrum.ranges);v.spectrum.update(None,None,ranges=current)
        assert shown(0)==shown(1)==['hidden']*4 and 'overlays hidden' in v.spectrum.legend.get()
        ack();window_id=str(v.window)
        # Return restores two windows; other target's detector curve has no leak.
        for _ in range(3):
            v.target_var.set(TARGETS[0].label);v.select_target();ack()
            assert not any(r.enabled for r in v.spectrum.ranges) and shown(0)==shown(1)==['hidden']*4
            assert canvas.itemcget('weight','state')=='normal'
            v.target_var.set(artifact_target.label);v.select_target();ack();check(True,True)
            assert str(v.window)==window_id
        # Generic drawing supports more named windows without new scene routing.
        extra=SpectrumRange('third','Reference',300.,700.,'#a3ddb4',(3,2))
        v.spectrum.update(spectrum,[0.]*len(spectrum['db']),ranges=(*v.spectrum.ranges,extra))
        assert shown(len(WINDOWS))==['normal']*4 and 'Reference' in v.spectrum.legend.get()
        maximum=[SpectrumRange(str(i),'Window '+str(i),40.+i*30.,400.+i*30.,'#a3ddb4') for i in range(MAX_RANGES)]
        v.spectrum.update(spectrum,[0.]*len(spectrum['db']),ranges=maximum)
        assert all(shown(i)==['normal']*4 for i in range(MAX_RANGES))
        try:v.spectrum.update(spectrum,[],ranges=maximum+[extra])
        except ValueError:pass
        else:raise AssertionError('Unbounded range pool accepted')
        ack();items=len(canvas.find_all())
        for i in range(500):
            feed.observe(frame,2048);spectrum=feed.snapshot()
            v.spectrum.update(spectrum,[0.]*len(spectrum['db']),ranges=current)
            v.spectrum.focus_range('flux' if i%2 else 'sparkle')
            assert len(canvas.find_all())==items and tuple(tuple(x) for x in v.spectrum.range_items)==pool
        assert artifact.authored_path.read_bytes()==baseline_bytes and profile_files[0].read_bytes()==profile_bytes
        ack();v.window.update_idletasks()
        assert not v.save_button.instate(['disabled']) and not v.author_button.instate(['disabled'])
        reachable=[]
        for i,key in enumerate(v.vars):
            v.focus_changed(i);v.window.update_idletasks()
            y=v.sliders[i].winfo_rooty()-v.shell.winfo_rooty()-v.viewport.canvasy(0)
            assert 0<=y and y+v.sliders[i].winfo_height()<=v.viewport.winfo_height()
            reachable.append(dict(control=key,y=y))
        assert v.spectrum.legend_label.winfo_height()>0 and v.spectrum.canvas.winfo_height()==150
        return dict(success=True,evidence_class='Native hidden Tk canvas/layout/events with synthetic FFT fixture and actual tuning/listening ACK methods; no real capture/GPU/foreground focus/hardware input',
            overlap=overlap,focuses=focuses,toggles=toggles,unacknowledged_edit_retains_applied_windows=True,
            separate_pending_inactive_stale_states=True,nonoverlap=True,no_snapshot_hides_ranges=True,
            stars_return_no_leak=True,generic_three_and_eight_ranges=True,max_range_count=MAX_RANGES,
            persistent_range_items=32,total_canvas_items=items,stable_redraws=500,profile_and_authored_bytes_preserved=True,
            save_buttons_enabled=True,fine_tune_hz_step=1.,geometry=[v.window.winfo_width(),v.window.winfo_height()],
            reachable_rows=reachable,canvas_size=[canvas.winfo_width(),canvas.winfo_height()],
            plot_axis_key=v.spectrum.axis_key,legend_height=v.spectrum.legend_label.winfo_height(),tk_version=root.tk.call('info','patchlevel'))
    finally:
        if v:v.close();v.window.host.destroy()
        root.destroy()

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='zerawave-spectrum-ranges-') as tmp:result=run(Path(tmp))
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2));print('Spectrum multi-range native checks PASS')
if __name__=='__main__':main()
