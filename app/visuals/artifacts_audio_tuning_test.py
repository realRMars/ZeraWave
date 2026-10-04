"""Target-local Living Artifacts routing/profiles/default-preservation checks."""
import argparse
import ast
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from artifacts_audio_tuning import BASELINE,BOUNDS,TARGET,ArtifactsAudioTuning,validate,mapped_inputs
from star_tuning_profiles import TargetProfileStore,StarProfileStore,SHIPPED,document,atomic_write
from starfield_tuning import StarfieldTuningWindow,decode
from spectrum_tuning_test import Widget,fft_frame
from star_profiles_test import install_widgets,restore_widgets,rejects
from studio_color_link import ColorLink,ColorInbox
from band_attack_tuning import BandAttackTuning
from low_band_attack import LowBandAttack
from spectrum_widget import SpectrumFeed
from starfield_tuning_test import live_owner_checks
from spectral_listening import SpectralListening

def render_route():
    tree=ast.parse((ROOT/'app/visuals/renderer.py').read_text(encoding='utf8'))
    render=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='render' and any(isinstance(c,ast.Assign) and ast.unparse(c.targets[0])=='artifact' for c in n.body))
    a=next(i for i,n in enumerate(render.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='artifact')
    b=next(i for i,n in enumerate(render.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=="self.program['u_artifacts_listening_inputs'].value")
    return compile(ast.Module(body=render.body[a:b+1],type_ignores=[]),'actual-artifact-render-route','exec')

def shader_checks():
    current=(ROOT/'app/visuals/shaders/dream.frag').read_text(encoding='utf8')
    from planet_audio_tuning_test import remove_coverage_shader
    current=remove_coverage_shader(current)
    baseline=(ROOT/'work/planet-artifacts-audio-01/baseline/app/visuals/shaders/dream.frag').read_text(encoding='utf8')
    block='''    // Target-local audio contributions. Neutral gains bypass scaling entirely.
    // Shared inputs, clocks, spatial bases and sibling materials remain intact.
    float art_flux=flux,art_impact=impact,art_light_sparkle=sparkle;
    float art_bass=bass_pressure,art_radial_pressure=pressure,art_presence_sparkle=sparkle;
    if(u_artifacts_listening_on.x==1)art_flux=u_artifacts_listening_inputs.x;
    if(u_artifacts_listening_on.y==1) {
        art_light_sparkle=u_artifacts_listening_inputs.y;
        art_presence_sparkle=u_artifacts_listening_inputs.y;
    }
    if(u_artifacts_tuning_on==1) {
        art_flux=clamp(art_flux*u_artifacts_audio.x,0.,1.);
        art_impact=clamp(impact*u_artifacts_audio.y,0.,1.);
        art_light_sparkle=clamp(art_light_sparkle*u_artifacts_audio.z,0.,1.);
        art_bass=clamp(bass_pressure*u_artifacts_shape_audio.x,0.,1.);
        art_radial_pressure=clamp(pressure*u_artifacts_shape_audio.y,0.,1.);
        art_presence_sparkle=clamp(art_presence_sparkle*u_artifacts_shape_audio.z,0.,1.);
    }
'''
    assert block in current
    inverse=current.replace('uniform int u_artifacts_tuning_on;\nuniform vec3 u_artifacts_audio;\nuniform vec3 u_artifacts_shape_audio;\nuniform ivec2 u_artifacts_listening_on;\nuniform vec2 u_artifacts_listening_inputs;\n','',1).replace(block,'',1)
    for before,after in (('art_flux * 1.2','flux * 1.2'),('art_impact * 0.6','impact * 0.6'),('art_light_sparkle * 0.55','sparkle * 0.55')):
        assert inverse.count(before)==1;inverse=inverse.replace(before,after,1)
    for before,after in (('3.2 + art_bass * 1.6','3.2 + bass_pressure * 1.6'),
        ('1.0, art_presence_sparkle','1.0, sparkle'),('* art_radial_pressure * 0.25','* pressure * 0.25')):
        assert inverse.count(before)==1;inverse=inverse.replace(before,after,1)
    assert inverse==baseline # No other shader, geometry, palette or idle change.
    cases=0
    for flux in (0.,.01,.2,.5,1.):
        for impact in (0.,.1,.4,1.):
            for sparkle in (0.,.2,.8,1.):
                inputs=(flux,impact,sparkle);local=mapped_inputs(inputs,(1.,1.,1.));assert local==inputs
                old=(min(1.,flux*1.2+.2),min(1.,impact*.6+.3),.55+sparkle*.55+.1)
                new=(min(1.,local[0]*1.2+.2),min(1.,local[1]*.6+.3),.55+local[2]*.55+.1)
                assert new==old;cases+=1
    assert mapped_inputs((0.,0.,0.),(2.,2.,2.))==(0.,0.,0.)
    assert mapped_inputs((.2,.4,.25),(2.,.5,0.))==(.4,.2,0.)
    assert mapped_inputs((1.,1.,1.),(2.,2.,2.))==(1.,1.,1.)
    # Quiet, held feature state and event-like changes remain separate from
    # elapsed idle time. These are controlled legacy-feature vectors, not music.
    tune=ArtifactsAudioTuning();tune.submit(1,dict(BASELINE,flux_stretch=2.,impact_facets=.5,sparkle_light=0.))
    tune.resolve(True);sequence=[(0.,0.,0.)]*20+[(.2,.1,.3)]*20+[(.8,.9,.95),(0.,0.,0.)]*6
    terms=[tune.status(True,v,i/60.)['audio_terms'] for i,v in enumerate(sequence)]
    assert all(all(value==0. for value in row.values()) for row in terms[:20])
    assert all(row==terms[20] for row in terms[20:40])
    assert terms[40]['stretch']>terms[20]['stretch'] and terms[40]['facets']>terms[20]['facets']
    assert all(row['light']==0. for row in terms)
    return dict(default_formula_cases=cases,inverse_shader_delta_exact=True,local_six_contributions=True,
        normalized_channel_ceilings_preserved=True,silence_stays_zero=True,time_rotation_life_and_other_materials_unchanged=True,
        quiet_steady_event_feature_sequence_packets=len(sequence),audio_terms_not_elapsed_time=True,
        evidence='CPU formulas and exact source delta; no compiled shader/GPU pixels')

def routing_checks():
    tune=ArtifactsAudioTuning();assert tune.resolve(True)==(0,(1.,1.,1.))
    c=dict(BASELINE,flux_stretch=1.9,impact_facets=.4,sparkle_light=0.)
    assert tune.submit(1,c) and tune.resolve(True)==(1,(1.9,.4,0.))
    status=tune.status(True,(.2,.4,.8),12.)
    assert np.allclose(list(status['local_inputs'].values()),(.38,.16,0.))
    assert status['audio_terms']['light']==0.
    assert tune.resolve(False)==(0,(1.,1.,1.)) and tune.settings==c
    assert tune.resolve(True)==(1,(1.9,.4,0.)) # Context return preserves manual values; no stale signal cache.
    tune.submit(2,dict(c,enabled=False));assert tune.resolve(True)==(0,(1.,1.,1.))
    assert tune.settings==dict(BASELINE,enabled=False)
    authored=dict(BASELINE,flux_stretch=.8,impact_facets=1.3,sparkle_light=.6)
    tune.submit(3,authored,authored);tune.submit(4,c);tune.resolve(True)
    assert tune.authored==authored and tune.settings==c
    tune.submit(5,dict(c,enabled=False));assert tune.resolve(True)==(1,(.8,1.3,.6))
    for key,(lo,hi) in BOUNDS.items():
        for value in (lo-.01,hi+.01,float('nan'),True,'1'):
            before=(deepcopy(tune.settings),deepcopy(tune.authored));rejects(lambda: tune.submit(6,dict(c,**{key:value})))
            assert (tune.settings,tune.authored)==before
    rejects(lambda:validate(SHIPPED))
    # Execute actual render-thread inbox consumption and uniform writes.
    inbox=ColorInbox.__new__(ColorInbox);inbox.lock=threading.Lock();inbox.closed=False;inbox.artifact_tuning_revision=-1;inbox.pending_artifact_tuning=None
    r=SimpleNamespace(artifact_tuning=ArtifactsAudioTuning(),color_inbox=inbox,debug_state=5,
        debug_sequence=(),transition_sequence=False,transition_settings={},program={
            **{key:SimpleNamespace(value=None) for key in ('u_artifacts_tuning_on','u_artifacts_audio','u_artifacts_shape_audio','u_artifacts_listening_on','u_artifacts_listening_inputs')}})
    code=render_route()
    env=dict(self=r,audio_inputs={},delta_time=0.,rewound=False,studio_audio=None)
    inbox.accept(json.dumps(dict(kind='artifact-tuning',target=TARGET,revision=1,settings=c)).encode());exec(code,env)
    assert r.program['u_artifacts_audio'].value==(1.9,.4,0.) and r.program['u_artifacts_tuning_on'].value==1
    prior=r.artifact_tuning.settings.copy()
    with patch('builtins.print'):
        inbox.accept(json.dumps(dict(kind='artifact-tuning',target='planet.starfield',revision=2,settings=c)).encode())
    exec(code,env);assert r.artifact_tuning.settings==prior
    for state,sequence,transition in ((0,(),False),(25,(),False),(5,(5,),False),(5,(),True)):
        r.debug_state=state;r.debug_sequence=sequence;r.transition_sequence=transition;exec(code,env)
        assert r.program['u_artifacts_tuning_on'].value==0 and r.program['u_artifacts_audio'].value==(1.,1.,1.)
    return dict(actual_uniform_route=True,default_bypass=True,manual_context_return_preserved=True,OFF_clears_live=True,
        coalesced_author_update_retained=True,finite_range_and_target_rejection=True,other_worlds_sequences_neutral=True)

def view_checks(folder,native=False):
    saved=None
    if native:
        import tkinter as tk
        root=tk.Tk();root.withdraw()
    else:saved=install_widgets();root=Widget()
    try:
        star_path=folder/'star.json';art_path=folder/'art.json';profiles=folder/'profiles'
        atomic_write(star_path,document(SHIPPED,'Authored','authored'))
        atomic_write(art_path,document(BASELINE,'Authored','authored',target=TARGET))
        star_store=StarProfileStore(star_path,profiles);art_store=TargetProfileStore(TARGET,art_path,profiles)
        backend=ArtifactsAudioTuning();star=BandAttackTuning(authored=SHIPPED);submitted=[]
        listening=SpectralListening(backend.analysis_settings)
        def submit(c,author=None,target='planet.starfield'):
            submitted.append((target,deepcopy(c),deepcopy(author)))
            if target==TARGET:backend.submit(len(submitted),c,author)
            else:star.submit(len(submitted),c,author)
            return len(submitted)
        view=StarfieldTuningWindow(root,submit,lambda on:None,star_store,art_store)
        if native:view.window.withdraw()
        frame,_=fft_frame();feed=SpectrumFeed();feed.enable(True);feed.observe(frame,2048)
        detector=LowBandAttack();p=None
        def ack():
            nonlocal p
            level,sensitivity,summary=star.apply(frame,20.,detector,'A');star.completed(detector.process(level,2048,'A',sensitivity),summary)
            backend.resolve(True)
            backend.observe(listening.process(frame.spectrum_frequencies,frame.spectrum_magnitudes,2048,'inert-view'))
            p=dict(star.latest,version=1,pilot_active=True,analysis_age_seconds=0.,spectrum=feed.snapshot(),
                artifact_tuning=backend.status(True,(.2,.4,.3),12.,True))
            assert decode(json.dumps(p));view.refresh((p,time.perf_counter()),True)
        def send():
            if view.pending is not None:view.window.after_cancel(view.pending);view.pending=None
            view.send();ack()
        ack();sliders=list(view.sliders)
        view.target_var.set('Living artifacts');view.select_target()
        assert list(view.vars)==list(BOUNDS) and view.sliders==sliders
        assert view.settings()==dict(BASELINE,enabled=False),view.settings()
        assert view.comparison_button.instate(['disabled'])
        assert 'original feature (range OFF)' in view.selection.get() and sum(view.spectrum.weights)==0.
        view.vars['flux_stretch'].set(1.9);view.changed('flux_stretch');send()
        assert backend.settings['flux_stretch']==1.9 and view.labels['flux_stretch'].get().startswith('1.90')
        if native:
            view.sliders[0].event_generate('<<NextChar>>');view.keyboard.release('Right');send()
            assert view.vars['flux_stretch'].get()==1.91 and backend.settings['flux_stretch']==1.91
        original_star=star_path.read_bytes();original_art=art_path.read_bytes()
        view.range_vars['flux'].set(True);view.changed('flux_range_enabled');send()
        view.range_vars['sparkle'].set(True);view.changed('sparkle_range_enabled');send()
        assert all(p['artifact_tuning']['listening'][name]['enabled'] and p['artifact_tuning']['listening'][name]['ready'] for name in ('flux','sparkle'))
        assert all(not p['artifact_tuning']['listening'][name]['enabled'] for name in ('bass','impact'))
        assert 'actual bins' in view.selection.get() and sum(view.spectrum.weights)>0.
        view.profile_name.set('Shared name');view.save_profile();art_profile=next(profiles.glob('profile-artifacts-*.json'))
        assert star_path.read_bytes()==original_star and art_path.read_bytes()==original_art
        view.reset();send();assert view.settings()==dict(BASELINE,enabled=False)
        assert view.load_profile(art_profile);ack();assert backend.settings['flux_stretch']>1.
        before=deepcopy(backend.settings);before_count=len(submitted)
        star_profile=star_store.save_profile('Shared name',SHIPPED,frame.spectrum_frequencies)
        assert art_profile!=star_profile and not view.load_profile(star_profile)
        assert backend.settings==before and len(submitted)==before_count
        assert view.save_authored();ack();promoted=deepcopy(art_store.authored)
        assert promoted['flux_stretch']>1. and StarProfileStore(star_path,profiles).authored==SHIPPED
        assert TargetProfileStore(TARGET,art_path,profiles).authored==promoted
        assert 'acknowledged' in view.profile_status.get()
        with patch('star_tuning_profiles.os.replace',side_effect=OSError('injected write failure')):assert not view.save_authored()
        assert art_store.authored==promoted
        view.target_var.set('Planet background stars');view.select_target()
        assert list(view.vars)[:4]==['start_hz','end_hz','weight','sensitivity'] and view.sliders==sliders
        assert view.settings()==dict(SHIPPED,enabled=False) and star_path.read_bytes()==original_star
        assert not view.load_profile(art_profile)
        view.target_var.set('Living artifacts');view.select_target()
        view.target_var.set('Liquid Alloy');view.select_target()
        view.preview_started();assert view.target_states=={} and not view.enabled.get()
        view.close()
        return dict(single_reconfigured_slider_set=True,artifact_control_count=6,artifact_range_positions=4,star_defaults_unchanged=True,
            actual_gain_ACK_display=True,no_fake_frequency_adapter=True,profile_roundtrip=True,
            same_name_target_isolation=True,cross_target_load_rejected=True,author_save_reset_relaunch=True,
            write_failure_prior_retained=True,new_preview_revision_cache_cleared=True,
            native_hidden=native,native_virtual_decimal=native)
    finally:
        if native:root.destroy()
        else:restore_widgets(saved)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--native-hidden',action='store_true');args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='zerawave-artifact-audio-') as temp:
        result=dict(evidence_class='CPU exact route / filesystem / inert UI; synthetic real-pipe owner; optional hidden native Tcl dispatch',
            shader=shader_checks(),routing=routing_checks(),view=view_checks(Path(temp),args.native_hidden))
    c=dict(BASELINE,flux_stretch=1.5,impact_facets=.5,sparkle_light=0.)
    ranges=dict(c,flux_range_enabled=True,flux_start_hz=40.,flux_end_hz=160.,sparkle_range_enabled=True,
        sparkle_start_hz=4000.,sparkle_end_hz=5000.)
    result['actual_live_owner']=live_owner_checks(star_enabled=False,artifact_sequence=[c,(ranges,ranges),dict(ranges,enabled=False),BASELINE])
    if args.output:args.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2));print('Living Artifacts CPU checks PASS')

if __name__=='__main__':main()
