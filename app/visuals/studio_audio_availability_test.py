"""CPU regressions for held Main startup and transition contribution eligibility.

Uses actual endpoints/catalog/availability; only the unrelated shared Planet
contribution calculation is stubbed. No renderer, window, audio device or GPU.
"""
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from audio_controls import TARGETS
from audio_scope import endpoints
from studio_audio import StudioAudio
from transition_catalog import SCENES,RECIPES,compatible

TRANSITION_TARGETS={key for key in TARGETS if key.startswith('transition.')}
DIRECTOR='transition.director'

def owner(state=0,outgoing=19,incoming=None,recipe=None,forced=False):
    renderer=SimpleNamespace(state_at=lambda seconds:state,
        director_current=outgoing,director_target=incoming,director_recipe=recipe,
        transition_progress=lambda:.25,transition_sequence=False)
    instance=StudioAudio.__new__(StudioAudio)
    instance.renderer=renderer
    instance.endpoint=endpoints(renderer,0.)
    renderer.transition_sequence=forced
    return instance

def evaluate(instance):
    snapshot=deepcopy(instance.endpoint)
    renderer_snapshot=dict(vars(instance.renderer))
    shared={p['shared']:True for p in TARGETS.values() if p.get('shared')}
    with patch('planet_audio_tuning.contribution_state',return_value=shared):
        instance.availability(0,0,[1.],[],[],[],[],[],[])
    assert instance.endpoint==snapshot,'Availability mutated endpoints'
    assert vars(instance.renderer)==renderer_snapshot,'Availability mutated playback state'
    return {t for t in TRANSITION_TARGETS if instance.contributions[t]}

def run():
    declarations=deepcopy(TARGETS);checks=0
    def expect(instance,wanted):
        nonlocal checks
        actual=evaluate(instance)
        assert actual==set(wanted),(instance.endpoint,actual,wanted)
        checks+=1
    # The three actual failed startup holds, including ordinary Main state 0.
    for source in (19,15,13):expect(owner(outgoing=source),[DIRECTOR])
    expect(owner(outgoing=12,recipe='tr_branch_iris'),[DIRECTOR])
    expect(owner(state=41,outgoing=41),[])
    expect(owner(state=19,outgoing=19,recipe='tr_warp'),[])
    for recipe,pair in (('tr_branch_iris',(41,42)),('tr_flow_fold',(43,2)),
                        ('tr_planet',(12,5)),('tr_warp',(19,20)),('tr_fade',(12,41))):
        for forced in (False,True):
            expect(owner(outgoing=pair[0],incoming=pair[1],recipe=recipe,forced=forced),
                   ['transition.'+recipe]+([] if forced else [DIRECTOR]))
    for recipe in (None,'unknown',123,[],{},'tr_material','tr_study'):
        expect(owner(outgoing=12,incoming=41,recipe=recipe),[DIRECTOR])
    expect(owner(outgoing=41,incoming=42,recipe='tr_planet'),[DIRECTOR])
    expect(owner(outgoing=12,incoming=12,recipe='tr_branch_iris'),[DIRECTOR])
    for source,target in ((12,None),(12,999),(None,41),(999,41),(12,37)):
        expect(owner(outgoing=source,incoming=target,recipe='tr_branch_iris'),[DIRECTOR])
    # Malformed direct endpoint data must fail closed before catalog lookup.
    for key in ('outgoing','incoming'):
        for value in (None,999,True,[],{}):
            instance=owner(outgoing=12,incoming=41,recipe='tr_branch_iris')
            instance.endpoint[key]=value
            expect(instance,[DIRECTOR])
    # Every declared compatible recipe still works, with its real catalog pair.
    for recipe in RECIPES:
        if 'transition.'+recipe not in TRANSITION_TARGETS:continue
        pair=next(((a,b) for a in SCENES
                   for b in SCENES if compatible(recipe,a,b)),None)
        assert pair is not None,recipe
        expect(owner(outgoing=pair[0],incoming=pair[1],recipe=recipe),
               [DIRECTOR,'transition.'+recipe])
    assert TARGETS==declarations,'Authored declarations changed'
    print(f'PASS: {checks} CPU availability cases; actual endpoints and all declared recipes; playback/declarations unchanged.')

if __name__=='__main__':run()
