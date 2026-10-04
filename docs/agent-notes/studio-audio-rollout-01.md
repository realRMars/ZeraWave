> Current status — 2026-10-04: Robert accepts the Main Audio Tuning development checkpoint with caveats and authorizes its scoped commit and normal push. Bounded engineering validation is complete; the observed transition hitch and real-time performance remain unresolved. The earlier 12× preview is not proof of real-time smoothness. See the [current handoff](../../ZERAWAVE_HANDOFF.md#current-main-audio-tuning-checkpoint) and later [workflow](../../work/studio-audio-rollout-01/workflow-review-index.json) / [foreground evidence](../../work/studio-audio-rollout-01/foreground-review-index.json). The historical CPU-checkpoint opening and results below retain their original scope.

# Normal Studio audio rollout — CPU checkpoint

The approved implementation extends the existing Studio Audio tuning dialog and
renderer to all 27 canonical Main forms. Experimental forms 37–40 are excluded.
This is an implementation checkpoint with current GPU and visual validation still
pending Bob's coordination; it is not an artistic acceptance or release.

The accepted dirty checkout is bound by
`work/studio-audio-rollout-01/checkpoint.json` and `resume-baseline.json`.
HEAD remains `0342e518a7bd2c521416e8027a7920668fc5ee51`. The exact task diff,
final source hashes, preservation checks and executed logs belong in
`work/studio-audio-rollout-01/review-index.json`; HEAD's full dirty diff includes
unrelated accepted work and is not this task's diff.

## Implemented behavior

- The normal dialog follows actual held/sequence/Main endpoints and existing
  authored family cycles. Choosing another form pins edits; playback continues.
  Controls, live revisions, authored destinations and profiles belong to their
  run/session/form/target. New form defaults are neutral, independently authored
  contracts; no saved Planet numbers are copied into another form.
- The accepted Planet 24-target controls, wider shape gains and colored FFT
  overlays remain. The accepted Star adapter is deliberately promoted in normal
  Studio; optional spread/fullness spatial modulation keeps its saved opt-in.
  Planet's mapped clocks and spatial amounts are isolated from other forms.
- Existing shader and CPU consumer inputs receive bounded gains or selected-bin
  substitutions. Manual pigments, materials, detail masks, timers and quiet bases
  retain their authored owners. Selected windows reuse the existing FFT. OFF
  windows use original inputs; live-override OFF uses the owned authored values.
- The Mapping monitor follows the selected scope, separating shared analyzer
  spectrum, actual CPU gain/input submissions, display formulas and director
  opportunity/beat/timer state. Selection/weight eligibility is labeled separately
  from pixel coverage. Inactive and mode-inactive consumers do not show activity.
- Main opportunity thresholds, beat qualification and hold/duration settings are
  distinct from visual warp inputs. Compatible transition recipes expose separate
  configuration and endpoint ownership. This adds no player queue or capture.
- Explicit pair audition uses the existing preview process. Decoded-source repeat
  restores the same passage, seed and numerical FFT histories; Return restores
  the prior source position and CPU scene/RNG state. Live input rejects a matched
  audition before mutation. Shared Echo/Enveloper GPU history resets at ownership
  boundaries; it is not snapshotted for pixel-identical restoration.
- Switching owner cancels held keys, drag/debounce work and pending paint. Unsent
  values stay at their original owner. Old-run/target/revision ACKs cannot make a
  new row Save eligible. Save Authored names its destination and requires a fresh
  matching ACK/settings digest; temporary profile loads remain separate.

The source audit corrected the Strata cliff's Bass bend ownership and matched
Cavern Flux bank inputs between its surface pass and shader. Cavern's cached mesh
has no live Bass bend, so no misleading Cavern bend control is exposed. Shared
water surfaces and material coordinate carriers remain explicitly coupled;
uncached ghostlight controls are inactive while cached memory contributes.

## Validation and limits

The review index records final executed CPU/native checks and retains earlier
failures. Evidence includes supplied-PCM analysis through the exact replay owner
with mocked graphics, scoped pipes, temporary profile storage, current shader
source bindings, actual renderer clock blocks, and withdrawn native Tk controls.
The native test visits 595 selectable tuning TARGET rows: 571 generalized rows
plus 24 Planet rows, including transition targets. This is not 595 independently
verified sliders or visual subelements. The updated replay regression compares
64 repeated audition frames and 44 resumed frames against the uninterrupted
numerical baseline, including a repeat after reaching the other endpoint.
Historical source-inversion checks establish
provenance, not current GPU pixels.

CPU adapter timing is recorded with input size, active forms, window counts and
exclusions in `studio_audio_binding_test-final.log`. It excludes FFT, capture,
rendering, Tk repaint and IPC; it establishes no FPS guarantee.

The bounded current GPU supplement (`gpu-review-index.json`) records 1,396 draws:
all 27 normal forms, current dream/Original Loop/surface paths, Echo and all three
Envelopers, selected-window GPU binding/OFF/reset, a repeatable pair and five
240-frame decoded-fixture motion runs. Seven serial owned contexts closed without
GL errors or effect fallback. Planet's neutral arm matches 240/240 baseline
frames. Root matches 238/240; the other two each differ by one channel level at
one pixel. Silent 15 fps review artifacts and temporal sequence sheets are bound;
they do not establish continuous audiovisual listening or artistic acceptance.

First current-source shader compilation took 161.95 seconds with an observed
process working-set peak of about 13 GB. Cached motion-arm creation took roughly
0.37–0.57 seconds. At the hidden 320x180 workload, median GPU draw was 1.00 ms for
neutral Root versus 0.67 ms for baseline, and 1.35 ms for neutral Planet versus
1.27 ms for baseline. Query waits, CPU submission and readback are reported
separately. Power, thermals and background load were uncontrolled; these are not
display FPS, fullscreen or general device guarantees.

The workflow continuation uses the actual `replay_test.replay` GPU owner and the
existing Warbot Jazz Test track, seed 7301, explicit Root→Planet `tr_planet` pair
(one-second hold and duration), matching layer settings and fresh decoded reset.
Its successful 224-draw trial verifies 64 repeated inputs/window values/endpoints
and tuning identities, 44 resumed frames equal to uninterrupted replay, Return
to the saved WAV position, controlled reset-error recovery, and cancellation
while an audition is active. Both owned contexts release their GPU resources.
Echo/Enveloper history resets remain the documented return boundary; no
pixel-identical history restoration is claimed. This accelerated hidden replay
is decoded GPU workflow evidence, not audible listening.

Two reproducible workflow defects were corrected. Decoded reset retained the
previous active form, changing the first window-priming block after a pair ended
on its other endpoint; it now clears active/selected/packed endpoint history.
An ACK at a nonzero revision could overwrite a parked unsent gesture edit; the
dialog now retains its unsent state at that original acknowledged owner. The
64-frame CPU pre-fix control fails as expected, and corrected CPU/native checks
pass. A native revision-seven parking regression verifies Save remains blocked
until the edited values receive their own ACK. Prior failed GPU trials are kept,
including an overly strict resource assertion subsequently corrected to allow
an inactive transition to release/recreate Enveloper resources.

Robert approved foreground use at 16:14 UTC. The actual Studio plus ColorLink
and decoded GPU replay child completed nine visible workflow observations:
automatic Root/Planet following, Pin/unpin, inactive Warp editing, named Save
Authored, held-key/pending-gesture cancellation and retained unsent editing.
Each observation has an owned-window screenshot, visible widget state and a
foreground process identity matching this driver. These are scripted Tk widget
events and actual visible UI, not manual clicks or RMars tool execution: RMars
was not callable in this delegated session. Screenshots were inspected directly.

The real Save Authored button callback wrote schema-three
`transition.tr_warp` values to an isolated temporary destination: duration scale
1.25, with its source gains/range settings unchanged. Its revision-two ACK
appeared at that same destination. A held-key edit to 1.26 remained parked after
switch/return, while Save stayed rejected until that edit was acknowledged.
The temporary directory was removed and all 22 real authored files plus six DSP
files reverified unchanged. Both Studio windows and the owned replay child
closed; child exit was zero. The prior recorded foreground handle no longer
existed at postcheck, so exact-handle restoration could not be verified; ChatGPT
was foreground and no unrelated app was recreated or terminated.

Three failed foreground-driver attempts remain preserved: two could not acquire
foreground focus; the third reached visible Follow/Pin/inactive editing but
read a nonexistent top-level revision instead of `scope.revision`. The fourth
passed after temporary input-thread attachment for focus acquisition and the
correct scoped ACK helper. These were driver corrections, not new production
defects. No production code changed during the foreground continuation.

The requested bounded workflow validation is complete. No live microphone, full
audiovisual listening, fullscreen/resize regression or multi-hour soak is
claimed. Documentation reconciliation and critic dispatch remain separate,
held for Bob/Prompter's next coordinated step. No commit, push or publication.

All 22 backed-up settings and six standalone DSP files must match their original
hashes in the review index. No authored settings are rewritten by load. No root
documents, commits, pushes, publication, capture/device settings or unrelated
sessions are part of this checkpoint.

## Coordinated review steps

For Robert's usability review, use Dev Studio Main scope with a Test track and
open Audio tuning. Leave Pin off to follow the actual playing form. Pin a form
to edit its destination while playback continues; unpin to resume following.
Select Transitions / World warp to see inactive configuration and named Save
Authored scope. The completed automation used temporary files; normal Save
Authored intentionally promotes the selected destination's acknowledged values.
For the already validated audition workflow, select explicit compatible
Root/Planet `tr_planet`, Repeat and Return; shared GPU history restarts at that
ownership boundary. User artistic acceptance and any approved critic transfer
remain separate from this bounded engineering validation.
