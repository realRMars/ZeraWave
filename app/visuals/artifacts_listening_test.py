"""CPU source-to-output checks for local artifact controls and listening ranges."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from artifacts_audio_tuning import BASELINE,ArtifactsAudioTuning
from spectral_listening import SpectralListening
from planet_canvas_dsp_test import audio_env,audio_state
from star_tuning_profiles import validate_document,document,TargetProfileStore,atomic_write
from artifacts_audio_tuning import LEGACY_BASELINE,TARGET
import tempfile


def flux_checks():
    tune=ArtifactsAudioTuning();listen=SpectralListening(tune.analysis_settings)
    tune.submit(1,dict(BASELINE,flux_range_enabled=True,flux_start_hz=900.,flux_end_hz=1000.));tune.resolve(True)
    f=np.fft.rfftfreq(2048,1/48000.);m=np.zeros(len(f))
    first=listen.process(f,m,2048,'A');assert first['channels']['flux']['bins']==4
    m[100]=100.;outside=listen.process(f,m,2048,'A');assert outside['channels']['flux']['raw']==0.
    m[40]=100.;inside=listen.process(f,m,2048,'A');assert inside['channels']['flux']['raw']==100.
    tune.observe(inside);flags,values=tune.listening(True);assert flags==(1,0,0,0) and values[0]>0
    steady=listen.process(f,m,2048,'A');assert steady['channels']['flux']['raw']==0.
    tune.submit(2,dict(BASELINE,flux_range_enabled=True,flux_start_hz=2300.,flux_end_hz=2400.));tune.resolve(True)
    changed=listen.process(f,m,2048,'A');assert changed['channels']['flux']['raw']==0.
    newsource=listen.process(f,m,2048,'B');assert newsource['channels']['flux']['raw']==0.
    assert tune.listening(False)==((0,0,0,0),(0.,0.,0.,0.))
    # Use the exact owner analysis function with two independent analyzer states.
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');a=audio_state();b=audio_state()
    b[0]._artifact_listening=listen;rng=np.random.default_rng(20261004)
    for _ in range(40):
        pcm=rng.normal(0,.04,(2048,2)).astype(np.float32)
        old=analyze(pcm,*a,source_id='C');new=analyze(pcm,*b,source_id='C')
        for key in old.__dict__:
            x,y=getattr(old,key),getattr(new,key)
            assert np.array_equal(x,y) if isinstance(x,np.ndarray) else x==y,key
        assert hasattr(new,'artifacts_listening')
    return dict(in_band_bins=4,in_band_raw_flux=100.,out_of_band_raw_flux=0.,steady_raw_zero=True,
        range_change_no_false_rise=True,source_change_primed=True,shared_audio_frames_exact=40,
        same_existing_FFT=True,actual_owner_attachment=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result={'classification':'CPU synthetic FFT and exact owner analysis; no capture, native UI or GPU',
        'flux':flux_checks(),'sparkle':sparkle_checks(),'shape_presence':shape_checks(),'storage':storage_checks(),'inventory':inventory_checks()}
    text=json.dumps(result,indent=2);print(text)
    if args.output:args.output.write_text(text+'\n',encoding='utf8')
    print('Artifact listening CPU checks PASS')


def sparkle_checks():
    tune=ArtifactsAudioTuning();listen=SpectralListening(tune.analysis_settings)
    c=dict(BASELINE,sparkle_range_enabled=True,sparkle_start_hz=900.,sparkle_end_hz=1000.)
    tune.submit(1,c);tune.resolve(True)
    f=np.fft.rfftfreq(2048,1/48000.);m=np.zeros(len(f));m[100]=100.
    outside=listen.process(f,m,2048,'A');assert outside['channels']['sparkle']['raw']==0.
    m[40]=.8
    inside=listen.process(f,m,2048,'A');assert inside['channels']['sparkle']['raw']==.2
    steady=[listen.process(f,m,2048,'A')['channels']['sparkle']['level'] for _ in range(40)]
    assert steady[-1]>steady[0]>0.
    tune.observe(listen.process(f,m,2048,'A'));assert tune.listening(True)[0]==(0,1,0,0)
    selected=tune.status(True,(.5,.2,1.),10.)
    assert selected['local_inputs']['sparkle']<1. and selected['inputs']['sparkle']==1.
    # Full high-band override uses the existing mean / 0..1 algorithm exactly.
    tune.submit(2,dict(BASELINE,sparkle_range_enabled=True));tune.resolve(True)
    analyze=audio_env(ROOT/'app/visuals/live_visual_test.py');state=audio_state()
    local=SpectralListening(tune.analysis_settings);state[0]._artifact_listening=local
    t=np.arange(2048)/48000.
    for amp in [0.]*3+[.002]*12+[.02]*12+[0.]*15:
        pcm=(amp*np.sin(2*np.pi*6000*t)).astype(np.float32)
        frame=analyze(pcm,*state,source_id='tones')
        measured=frame.artifacts_listening['channels']['sparkle']['level'];assert measured==frame.highs
    return dict(out_of_band_mean=0.,in_band_mean=.2,sustained_level_rises=True,
        shared_sparkle_preserved=True,full_high_window_matches_existing_algorithm_packets=42,
        presence_and_light_only=True)


def shape_checks():
    tune=ArtifactsAudioTuning();defaults=tune.status(True,(.4,.4,1.),0.,bass=.5)['audio_terms']
    for key,term in [('bass_cells','cell_scale_increment'),('bass_radial','radial_displacement'),
                     ('sparkle_presence','presence_reveal'),('sparkle_light','light')]:
        tune.submit(tune.revision+1,dict(BASELINE,**{key:0.}));tune.resolve(True)
        terms=tune.status(True,(.4,.4,1.),0.,bass=.5)['audio_terms'];assert terms[term]==0.
        assert all(terms[k]==v for k,v in defaults.items() if k!=term)
    for bass in (0.,.1,.5,1.):
        for gain in (0.,.5,1.,2.):
            tune.submit(tune.revision+1,dict(BASELINE,bass_cells=gain,bass_radial=gain));tune.resolve(True)
            terms=tune.status(True,(.4,.4,1.),0.,bass=bass)['audio_terms']
            assert 0<=terms['cell_scale_increment']<=1.6 and 0<=terms['radial_displacement']<=.25
    return dict(four_independent_contribution_cases=True,bass_bounds_cases=16,presence_light_independent=True,
        shared_domain_not_claimed_local=True)


def storage_checks():
    old=dict(version=1,target=TARGET,kind='profile',name='Old',values={k:v for k,v in LEGACY_BASELINE.items() if k!='enabled'})
    migrated=validate_document(old,target=TARGET);assert migrated['version']==3
    assert migrated['values']=={k:v for k,v in BASELINE.items() if k!='enabled'}
    f=np.fft.rfftfreq(2048,1/48000.)
    c=dict(BASELINE,flux_range_enabled=True,flux_start_hz=900.,flux_end_hz=1000.,sparkle_range_enabled=True,
        sparkle_start_hz=4000.,sparkle_end_hz=5000.,sparkle_presence=.5,bass_radial=0.)
    with tempfile.TemporaryDirectory(prefix='zerawave-listening-profile-') as temp:
        path=Path(temp)/'authored.json';atomic_write(path,document(BASELINE,'Authored','authored',target=TARGET))
        store=TargetProfileStore(TARGET,path,Path(temp)/'profiles');before=path.read_bytes()
        custom=store.save_profile('Ranges',c,f);assert path.read_bytes()==before
        assert store.load_profile(custom,f)[1]==c
        store.save_authored(c,f);assert TargetProfileStore(TARGET,path).authored==c
        try:store.save_profile('Empty',dict(c,flux_start_hz=141.,flux_end_hz=142.),f)
        except ValueError:pass
        else:raise AssertionError('Empty bins accepted')
    return dict(v1_migration_neutral=True,v2_profile_roundtrip=True,custom_author_separate=True,
        author_relaunch=True,actual_empty_bins_rejected=True)


def inventory_checks():
    from star_profiles_test import install_widgets,restore_widgets
    from spectrum_tuning_test import Widget
    from starfield_tuning import StarfieldTuningWindow
    saved=install_widgets()
    try:
        view=StarfieldTuningWindow(Widget(),lambda *a,**kw:1,lambda on:None)
        expected=['start_hz','end_hz','weight','sensitivity']
        for target in ('Planet background stars','Living artifacts','Liquid Alloy','Planet background stars'):
            view.target_var.set(target);view.select_target()
            if target=='Planet background stars':
                assert list(view.vars)[:4]==expected;view.set_available(True)
                assert view.bounds['sensitivity']==(.5,2.) and view.keyboard.entries[3][4]==.01
                assert all(not view.sliders[i].hidden and not view.sliders[i].instate(['disabled']) for i in range(4))
        assert view.spectrum.canvas.cget('height')==150
        view.close()
    finally:restore_widgets(saved)
    return dict(previous_star_controls=expected,sensitivity_range=[.5,2.],target_switch_restores_all_rows=True,
        spectrum_requested_height=150,classification='inert layout/binding inventory; native visibility pending')


if __name__=='__main__':main()
