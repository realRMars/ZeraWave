# Living Artifacts Audio tuning and decimal-key fix

Approved scope: fix fractional slider keyboard behavior, then implement a small
real Living Artifacts adapter in the existing Audio tuning window. No independent
reviewer, rollout, commit/push or other-world redesign. Robert's next trial is the
review boundary.

## Decimal checkpoint

`work/planet-slider-decimals-01/review-index.json` binds the isolated fix before
the adapter extension. SHA256:
`14189e37031f85428ef54d43c4a88a0cc5013d2775eebcd5382f394c5ef01f94`.
Tk 9.0.4's TScale virtual navigation handlers increment by 1 or 10. The helper
previously owned physical arrows only; a hidden native Tk probe reproduced the
virtual route's 1.9 -> 0.9 jump. It now owns virtual navigation too, blocks the
class handler and duplicate presses, and uses Decimal addition to preserve the
fractional starting value. Weights/gains/sensitivity step by 0.01; frequencies
retain their independent 1-Hz positioning step and actual-bin labels.

Hidden native Tk events verified actual model/display/analysis ACK agreement,
1.9 -> 1.91, fractional sensitivity, 200 right/left pairs within 1e-12 drift,
clamps, disabled skipping, preserved mouse/Tab bindings and cancellation.
This does not establish hardware-key delivery in Robert's running Studio.

## Actual local route

Living Artifacts is the existing procedural block in `shaders/dream.frag`, not
Elastic Lenses/Braided Flow, and it has no independent frequency detector.
The existing FFT/legacy mapping reaches renderer uniforms, then normalized
shader-local inputs. Only three named contributions now use local gains:

| Control | Existing source and term | Gain / default / step |
| --- | --- | --- |
| Flux -> stretch contribution | `frame.flux` -> `parameters.flux` -> `u_flux` -> `clamp(flux*1.2+tunnel_weight,0,1)` | 0-2 / 1 / 0.01 |
| Impact -> facet contribution | mapped impact -> existing render `impact_envelope` -> `u_impact` -> `clamp(impact*.6+geometric_weight*.5,0,1)` | 0-2 / 1 / 0.01 |
| Sparkle -> light contribution | mapped sparkle -> `parameters.sparkle` -> `u_sparkle` -> base light `.55+sparkle*.55+tunnel_weight*.35` | 0-2 / 1 / 0.01 |

`u_artifacts_audio` scales only these local inputs, clamped to their existing
0-1 ceilings. `u_artifacts_tuning_on=0` bypasses scaling at neutral gains. Spatial
stretch, geometric facets, base light, bass size, sparkle presence, palettes,
secondary morphology/density/spin/focal streams and lifetime remain authored.
Rotation is clock-driven and is deliberately not presented as an audio control.
The shared audio uniforms and all sibling material inputs remain unchanged.

This is a bounded parameter adapter, not a new effect/geometry/audio analysis
system. It adds two uniforms and no passes, textures, captures or FFTs. GPU cost
and pixel equivalence are not measured. Other-world/sequence contexts submit
neutral uniforms, avoiding cross-context effect leakage.

## Workflow and persistence

Audio tuning now lists 24 actual audio-responsive groups: **2 editable adapters,
22 unavailable**. Stars keep their four existing controls; Living Artifacts uses
three gains in the same reconfigured slider rows. The fourth row is hidden and
disabled. Unimplemented groups have no active slider rows or false star curve.
The full spectrum remains diagnostic; Living Artifacts has no frequency-window
curve. It works in held Planet Canvas with the star attack pilot OFF as well.

`TargetProfileStore` reuses the versioned schema and atomic storage path for the
distinct `planet.material.artifacts` target. Its authored file is
`artifacts_audio_authored.json` with neutral 1/1/1 values. Custom profiles use a
separate target filename prefix, even for the same profile name. Cross-target
loads reject without partial apply. Custom Save/Load cannot promote authored.
Explicit AUTHOR Save persists ACK values separately and updates the running
render via the existing bounded Studio pipes. OFF/Back clears temporary values.
Startup/relaunch reads its authored file. New-preview revision caches clear.
Star authored 80-130 Hz / 1.5 / 2 and old comparison remain intact.

## Checks and limits

The source-bound `work/planet-artifacts-audio-01/review-index.json` contains the
pre-task snapshot, exact task diff, final source copies, logs and result hashes.
Checks cover inverse shader-delta equivalence outside the three substitutions,
80 neutral formula cases, 52 quiet/steady/event-like legacy-feature packets,
actual AST-isolated render uniform writes, other-context neutralization, profile
roundtrip/promotion/failures/wrong target, reused rows and source/relaunch behavior.
The real local-pipe owner test uses synthetic capture/mocked graphics and confirms
one capture start/stop, Artifact ACK revisions/uniforms with star analysis OFF.
Hidden native Tk also checks switching schemas and decimal gain dispatch.
Existing star/spectrum/monitor/Planet descriptor regressions are recorded.

The first source-bound seven-check run retained a Planet descriptor regression
failure: its surface-only mocked replay exposed an unnecessary star-hook query
when the star pilot was OFF. The hook now checks that flag before querying star
eligibility. The final run is recorded separately with new source hashes; the
original failure log and summary remain in the evidence pack.

An initial hidden-native test failed because it compared Tk 9's Tcl state object
to a Python string; the actual state was disabled. The assertion now uses the
widget `instate()` API. This console-only failure is retained as a qualified
description, not represented as a complete source-bound intermediate run.

No foreground app interruption, GPU compilation/render/capture, real audio
capture, natural listening, FPS guarantee or artistic acceptance is claimed.
Six standalone DSP files, star detector/flight, descriptor mappings and prior
frozen evidence remain preserved. Main session functions remain unchanged.

## Next user trial

Restart Studio and its preview when ready so Python imports and the shader reload;
the builder did not stop the existing app. Hold Planet Canvas, choose Living
artifacts in Audio tuning and ensure that material is present in the current
material selection/cycle. Try 0/1/2 for each contribution with quiet, steady and
attack-rich input; clock-driven motion and other responses should continue.
Test fractional Left/Right, mouse, Up/Down/Tab, Save/Load, Back, explicit authored
save/relaunch and switch back to stars. No additional adapter or reviewer is
authorized by completion of this pass.
