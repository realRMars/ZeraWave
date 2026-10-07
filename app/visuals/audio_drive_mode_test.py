"""Raw-mode bypass across actual shared tuning adapters, preserving saved state."""
from copy import deepcopy
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'audio')]
import numpy as np
from form_audio_tuning import FormAudioTuning
from audio_controls import TARGETS, defaults, bounds
from audio_scope import Scope
from planet_listening import derived
from planet_audio_tuning import PlanetAudioTuning, TARGETS as PLANET, SPECS, baseline
from artifacts_audio_tuning import ArtifactsAudioTuning, BASELINE

INPUTS=dict(bass=.2,movement=.2,sparkle=.4,flux=.1,impact=.3,raw_impact=.1)


def run():
    forms=FormAudioTuning('run','session');active=sorted({row['form'] for row in TARGETS.values()})
    for target,row in TARGETS.items():
        settings=defaults(target)
        for role in row['roles']:
            low,high=bounds(target)[role['key']]
            settings[role['key']]=min(high,max(low,1.5))
        forms.submit(dict(scope=Scope('run','session',row['form'],target,1).packet(),settings=settings))
    forms.resolve(active,INPUTS)
    saved=deepcopy(forms.state);history={k:id(v) for k,v in forms.listening.items()}
    # A real enabled FFT listening history is kept warm in both modes.
    target='roots.growth';c=dict(defaults(target),flux_branch=1.5,flux_range_enabled=True,flux_start_hz=90.,flux_end_hz=130.)
    f=np.arange(1025)*48000/2048
    forms.process(f,np.ones(1025),2048,'fixture')
    forms.submit(dict(scope=Scope('run','session',12,target,2).packet(),settings=c));forms.resolve(active,INPUTS)
    forms.observe(forms.process(f,np.ones(1025),2048,'fixture'));forms.resolve(active,INPUTS,.04)
    saved=deepcopy(forms.state);processor=id(forms.processors[target])
    before=deepcopy(forms.packed)
    forms.resolve(active,INPUTS,.04,raw_waveform=True)
    for target,row in TARGETS.items():
        for role,slot in zip(row['roles'],forms.packed[target]):
            if role['source']!='timer':assert slot==1.,(target,role['key'],slot)
        assert forms.selected[target]==derived(INPUTS)
    assert forms.state==saved and {k:id(v) for k,v in forms.listening.items()}==history
    assert id(forms.processors['roots.growth'])==processor
    forms.resolve(active,INPUTS,0.,raw_waveform=False);assert forms.packed==before
    planet=PlanetAudioTuning()
    for target in PLANET:
        c=baseline(target)
        for role in SPECS[target]:c[role['key']]=1.5
        planet.submit(target,1,c)
    star=dict(chorus_light=2.,chorus_presence=2.,chorus_twinkle=2.,legacy_wake=2.,flux_clock=2.,sparkle_clock=2.)
    planet.resolve(True,star,INPUTS);saved=deepcopy(planet.state);before=deepcopy(planet.packed)
    ids={k:id(v) for k,v in planet.listening.items()}
    on,rows=planet.resolve(True,star,INPUTS,raw_waveform=True)
    assert on==0 and all(v==1. for row in rows for v in row)
    assert planet.state==saved and {k:id(v) for k,v in planet.listening.items()}==ids
    assert all(planet.local_sources(target,INPUTS)==derived(INPUTS) for target in PLANET)
    planet.resolve(True,star,INPUTS);assert planet.packed==before
    artifact=ArtifactsAudioTuning();artifact.submit(1,dict(BASELINE,flux_stretch=2.,bass_cells=2.,sparkle_presence=0.))
    artifact.resolve(True,INPUTS);saved=deepcopy(artifact.settings);history=id(artifact.listening_state)
    assert artifact.resolve(True,INPUTS,raw_waveform=True)==(0,(1.,1.,1.))
    assert artifact.shape_gains(True)==(1.,1.,1.) and not any(artifact.listening(True)[0])
    status=artifact.status(True,(.1,.3,.4),0.,bass=.2)
    assert status['uniform_on']==0 and status['shape_gains']==[1.,1.,1.]
    assert artifact.settings==saved and id(artifact.listening_state)==history
    artifact.resolve(True,INPUTS);assert artifact.shape_gains(True)==(2.,1.,0.)
    print('PASS: all declared Main/transition audio gains bypassed, Planet/sky and Artifacts neutral uniforms, listening histories retained, saved revisions/values unchanged, analyzed mode restored.')


if __name__=='__main__':run()
