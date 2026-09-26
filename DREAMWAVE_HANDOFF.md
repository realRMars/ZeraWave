# DreamWave working handoff

Updated: 2026-09-26

## Accepted Fire checkpoint

The user reviewed the refined Fire, said "pass!", and explicitly authorized
committing it before further expansion. This checkpoint contains the isolated
Flame sheets form, Studio registration/layers, lava-base refinement, white/blue
ignition, tests and documentation. Historical pending-review statements below
are superseded by this acceptance. Main-blend integration remains future work.
The user also authorized continuing Fire expansion after this checkpoint.

## Fire refinement — user accepted the start and requested more character

Still based on 38da96a; the Fire foundation and this refinement are uncommitted.
The user requested a steady lava-like base, stronger licking tips, and a
white-hot → blue → existing amber response on intense hits. Changes are limited
to Fire's shader function, its existing GPU test and the two development notes.
Coals retains its label/ID but now shows molten channels drifting on elapsed
time with a slow rhythm, independent of abrupt audio. Rising Embers is unchanged.
Upper tips have traveling curls/elongation. The ignition response follows the
existing renderer's six-per-second impact decay, calibrated to real onsets near
.5; it is restricted to folded flame roots. No renderer/audio/palette changes.

The first wide white band was visually rejected and failed the generic motion
bound at 22.79/255. Narrowing and ribbon-shaping it fixed the flat-band appearance.
The final test distinguishes the requested onset flash (10.919/255, bound 12)
from ordinary motion including decay (max 2.864/255, original bound 3 retained).
GPU tests passed 504 exact preservation cases, 18 input/time captures, separate
audio/layer responses, 361 integrated frames, continuous flow/star clocks,
steady-but-moving lower lava pixels and white/blue/amber decay captures.
Synthetic profiles and cooling triptych were visually inspected. Evidence:
work/elemental/fire/refinement/, baseline before-refinement.frag. Existing
foundation baseline before.frag still verifies all states 0–13.
Accelerated replay then passed the first 60 seconds of all three tracks:
4,221 frames, 18 captures, no clipped pixels; Balloon at 30s and Warbot Jazz at
50s were visually inspected. Evidence: work/elemental/fire/refinement-music/.
These remain silent excerpts rather than full-song or audible playback tests.
Python compilation and diff whitespace checks passed. Studio code/controls
are unchanged in this refinement, so its previously passing tests were not rerun.
Live loopback is not tested. User should reopen Studio → Elements → Fire →
Flame sheets for motion review. Still no main-blend integration or commit.

## Fire foundation — isolated, uncommitted, awaiting visual review

Current committed checkpoint is 38da96a (accepted Water completion). The user
agreed to defer a metallic sibling material and authorized starting Fire.
Living artifacts and its palette must remain intact. The metallic sibling may
later have its own palette and alternate or coexist; it is not implemented.

Studio → Elements → Fire → Flame sheets uses state 14. Three upward-advected
sheets, a low coal bed, selective hot seams and ascending embers establish one
composition. Existing material and Living artifacts are carried through it.
Bass widens/raises the fire, flux curls folds, sparkle reveals seams/embers,
impact heats a bounded lower region; silence still flows. Existing renderer,
audio mapping and positive clocks are reused. This is procedural layered
imagery, not a volumetric simulation. No new dependencies or uniforms.

Fire's own layer profile exposes Living artifacts, Coals (131072), Embers
(262144), Hot seams (524288). Existing bits are stable. Raw state 14 routes
through a neutral Organic source field and final Fire composition; it cannot
fall into the old >5.5 Water route. The existing artifact calculation/palette
is unchanged. Fire captures its contribution before the Organic substitution.
The production main blend is unchanged; Fire awaits review before integration.
Elements with a blank child now visits all five Water leaves then Fire in
28-second diagnostic holds. Fire's blank form holds its only current form.

Executed validation:
- shader_test.py --fire-test: 504 exact GPU pixel comparisons against 38da96a,
  states 0–13, six times, three levels, authored and artifact-only modes.
- 18 Fire input/time samples: contrast 25.25–40.63, dark fraction .64–.79,
  zero clipped pixels. Four independently visible audio responses, silent
  motion, and four independently visible effect toggles passed.
- 361 actual-renderer frames across rise/impact/release; flow and star clocks
  strictly advance. Largest mean frame change 2.8975/255, below bound 3.
- studio_test.py passed, including real Tk Fire dropdowns/table/session,
  existing UI lifecycle, hierarchy, replay pacing/metadata and GPU clocks.
- First 60 seconds of each Balloon, Chasing You and Warbot Jazz: 4,221 frames,
  18 captures, all structure/dark-space bounds passed, zero clipped pixels.
  Synthetic quiet/moderate/full contact sheet and one 30s frame per track
  visually inspected. These are silent accelerated replays, not full songs
  or live-loopback verification; moving aesthetics still need user review.
- Python compilation and git diff --check passed.

Evidence: work/elemental/fire/{check,music}/; baseline before.frag. The shader
regression lives in existing shader_test.py, Studio checks in studio_test.py.
Nine modified tracked files: shader, live/synthetic state maps, layer catalog,
Studio, its test, and DEVELOPMENT_STUDIO.md / ELEMENTAL_DEVELOPMENT.md / this
handoff (shader_test.py contains both state map and GPU checks). No commit or
push. Existing unrelated untracked research/scratch files remain untouched.
Next: reopen Studio and review Fire with Authored first, then its isolated
layers. Do not start another element or integrate Fire before that review.

## Water completion checkpoint: details, Currents and main integration

Base is accepted commit 6875fb9. The user accepted the Water continuation and
asked to finish Water before committing. This checkpoint exposes five existing
Water effects, adds Currents, and integrates all five forms into the main blend.
Other elements will be developed one at a time; none was started in this pass.

Studio → Elements → Water → Currents (state 13) holds broad colored streams
bending through two eddies, with dark channels and fine reflected ribbons.
Existing source imagery supplies the moving material. Bass broadens pressure,
flux controls local shear, sparkle reveals fine light, and impact creates a
bounded disturbance. Quiet passages still move. The existing renderer and
positive clocks are reused; this is a procedural coordinate field, not fluid
simulation. The accepted sea's height equations are unchanged.

Water details category: Rain streaks, Ripple rings, Crest foam / cliff lip,
Mist & distance haze, Surface highlights. These append stable bits to the
existing catalog/uniform interface. Rain/rings can independently populate
surface forms, including Currents; the waterfall supports its own lip,
highlights and haze. Foam needs steep crests and haze depends on distance.
Authored mode preserves existing held forms; custom lists explicitly select
the new details. No dependencies, audio changes or renderer lifecycle edits.

Water's isolated development cycle (state 6) now includes Currents after
Waterfall: five 28-second slots, 140 seconds total. Each has a roughly
19-second hold followed by a 9-second eased change. The isolated Water music
launcher also uses this expanded cycle. Main blend (state 0) holds one form
through each Water visit, then advances while Water is hidden: Sea, Currents,
Waterfall, Rain & ripples, Liquid dyes. The existing entry/full/release times
116/126/144/158 seconds and 140-second visit spacing are unchanged. Animation
and material clocks never reset. This prevents a 140-second five-form cycle
locking onto the same phase every visit, and avoids concurrent form-camera
changes during Water's exit. A trial continuous main form schedule failed a
transition bound (3.3923/255 at 284s); that version was replaced, not accepted.
Currents also delays the returning spatial grammar with a cubic release
envelope. Long advected material coordinates otherwise amplified recursive
folds during exit (5.1639/255 at 287s). Held forms and imagery outside Water
remain unchanged; the corrected version passed the same comparison bound.

Final integration test passed 222 preservation cases (all held forms, Studio's
cycle and main imagery outside Water), all five distinct main visits, and 90
entrance/dwell/release comparisons at quiet/moderate/strong fixed inputs.
The comparison retains a pre-existing extreme-input frame-change spike at
256s / .95 input: 53.8261/255 vs baseline 53.8225/255. This is not a claim that
every legacy transition is smooth; the regression allowance is relative to
the accepted baseline. Broad retuning of the accepted background was excluded.
Evidence: work/elemental/currents/integration/ (before-integration.frag is the
accepted Currents preview before main scheduling changed).
The complete Warbot Jazz main-blend replay then finished: 299.3 song seconds,
7,015 frames and 20 captures. Both full-Water captures (Sea at 135s, Currents at
270s) passed structure/dark-space checks with zero clipped pixels. Currents at
270s and its release at 285s were visually inspected. Non-Water captures retain
existing highlight clipping, up to 1.5805% in this replay. Evidence is in
work/elemental/currents/integration-music/. Live loopback was not rerun.
Python compilation and git diff --check passed. The nine-file completion pass
is the requested checkpoint; unrelated research/scratch files remain excluded.

Changed files: dream.frag, preview_layers.py, Studio's catalog/note, live state
map, shader_test.py, studio_test.py, and Water/Studio/handoff documentation.
No changes to the existing audio pipeline, renderer implementation or replay
implementation. Unrelated root scratch files/research remain untouched.

Development verification before main integration:
- Detail-only stage: 132 exact pixel preservation cases and 40 visible
  effect/world combinations.
- Final currents-test: 144 exact prior-world/held-form/main-blend comparisons,
  44 effect/world combinations, 28 Currents input/time samples, four independent
  audio responses, motion with silent inputs, 20 eased cycle boundaries, and
  361 renderer-integrated frames. Maximum mean changes .8273/255 at joins and
  1.1756/255 across the integrated envelope; no headroom/structure failures.
- studio_test.py passed hierarchy, new state registration, session migration,
  table operations, replay metadata/pacing and continuous GPU clocks. Focused
  real Tk checks passed Currents selection, all five Water-detail options,
  add/cycle/save round-trip and minimum 680x700 layout.
- Accelerated real audio: first 60 seconds each of Balloon, Chasing You and
  Warbot Jazz, 4,221 frames total, 18 captures. All capture structure/dark-space
  checks passed with zero clipped pixels. Synthetic contact sheet and one
  captured music frame per track were visually inspected.

Evidence is under work/elemental/currents/{check,music}/, with the saved
pre-change shader at before.frag. Excerpts are not full-song or live-loopback
testing. The user accepted Currents and authorized finishing this checkpoint.
Reopen Studio, select Currents, and use Authored first; then try individual
Water details. No other element should be started until the next request.

## Accepted checkpoint: Water and Development Studio

The user accepted the Water refinements and Studio form/effect isolation, then
explicitly requested this checkpoint commit. It builds on aa44d54 and includes
the accumulated Water world, shared onset-order fix, accelerated replay,
hierarchical selectors and per-world effect lists. Earlier uncommitted/pending
review statements below describe the development history and are superseded
by this acceptance. Unrelated research folders and root-level scratch scripts
are excluded. No new feature work is part of the checkpoint.

### Current development-tool pass: forms and effect layers

User accepted cascading world isolation and requested a further separation of
forms from optional effects, with add/remove, enable, solo, order and cycling.
Terminology: World = environment; Form = main structure; Effect = treatment;
Layers = a world's saved ordered effect list. Elements is a grouping category.
This section supersedes the previous pass's "no order-list editor" statement.

Studio exposes Organic → Membrane / Roots (blank retains native meld),
Geometric → Neon corridor, and existing Cosmic/Water forms. Effects & layers
has category/effect pickers, a table, On/off, Solo, Remove, Up/Down, and Authored /
Selected together / Cycle list playback with a hold duration. Per-world lists
survive selection changes and session save/load. Water has its own profile,
independent of the Elements grouping. Main blend has a separate preview profile.
Version 3 saves lists and paths; v1/v2 migrate with authored effects unchanged.
Each run saves preview.json alongside its log for reproducibility.

The new small preview_layers.py shares development IDs, validation and cycle
selection among Studio and the existing entry points/renderer; it is not a new
audio or visual parameter pipeline. Two optional shader uniforms gate existing
effects. Default mode preserves authored appearance; custom mode holds selected
spatial treatments and gates material/detail contributions. Custom material
effects remain visible on Organic's surface before planet/corridor projection.
Stars retain their continuously integrated clock even while hidden.

Implemented controls: artifacts, sparkles, drifting flecks, radial beams,
tunnel, fractal folds, horizon/pathway, root blossoms, corridor glyph rain,
starfield, rings, moons with their dust wakes. Effects remain audio-responsive
and keep their lifecycle. Root blossoms require Roots; Cosmic Geometry study
uses only world details. Water's rain/waves/ripples/fall remain forms; its
inherited artifacts can be isolated. Fractal remains a spatial treatment.

List order is cycle order, not arbitrary shader/compositor order. Together
retains the shader's established coordinate/material order. Cycle cuts are
development diagnostics; song time drives replay regardless of acceleration.
CLI --layers JSON works in live, replay, synthetic preview and fixed capture.
Replay CSV/capture metadata includes the active layer mode/mask. Main live
launcher has no overrides and does not import Studio's lists automatically.

Verification executed: shader preservation_test passed 72 comparisons;
layer_test passed 132 comparisons covering all previous states, with maximum
channel deviation 1/255, two distinct held Organic forms and 30 visible
effect/world combinations. Synthetic GPU base-form, artifact and fractal
captures were visually inspected. studio_test passed actual Tk selectors,
table/solo/reorder/save/load callbacks, per-world independence, v1/v2/v3
migration/validation, minimum 680x700 layout bounds, child lifecycle, replay
pacing parity, 9-second real audio layer cycling and 57-second form cycling,
capture/CSV labels, and uninterrupted real GPU drift/star clocks. CLI help for
all three entry points passed, including live/replay module invocation.
Fixed-frame CLI capture verified the requested artifact mask and the resulting
planet material was visually inspected. Python compilation and git diff --check
passed (Git reports its normal LF-to-CRLF conversion notices).
Live loopback and desktop screenshot review were not rerun for this pass.

Evidence: work/development/layers/before.frag and check/ (ignored development
artifacts). HEAD remains aa44d54; accumulated Water/Studio work is uncommitted.
No dependency changes, deletion, renderer replacement or audio analysis edits
in this pass. Restart Studio to load controls; changes apply on the next run.

### Current development-tool pass: hierarchical isolation

The user accepted the revised waterfall, then requested cascading world,
category and deeper form selectors with blank selections cycling the chosen
branch. Studio now has a recursive WORLD_TREE catalog: Organic, Geometric,
Cosmic, Transition, Elements → Water → Sea / Liquid dyes / Rain & ripples /
Waterfall. Cosmic exposes its existing canvas and geometry diagnostic. No
unimplemented elements or order-list editor were added.

Blank root uses main blend; blank Water uses its authored native meld. Elements
currently delegates to its sole implemented Water child. Multi-branch groups
without a native cycle flatten every descendant leaf in catalog order and
hold each for 28 seconds. This prevents grandchildren from being skipped when
future elements are added. These generic development switches are direct cuts.
Native Water blending is unchanged. Select a leaf to isolate it.

Parent edits clear stale children; nested dropdowns and Presets menus rebuild
recursively, with a scrolling selector area for deeper paths. Session version 2
saves stable selection IDs. Version 1 state sessions migrate to equivalent
paths on load, without changing their selected held/native behavior.

Files in this step: studio.py, studio_test.py, renderer.py, the existing live,
replay and synthetic entry points, and development/handoff documentation.
The renderer has an optional debug_sequence and elapsed-time state selector;
its lifecycle, clocks, uniforms and normal default behavior are unchanged.
All three entry points accept --states. Replay metadata/CSV records the actual
active state, using song time regardless of acceleration. No shader/audio
analysis changes, dependencies, new renderer or separate replay pipeline.

Verification executed: studio_test.py passed recursive selection (including a
temporary fourth level and multi-branch descendant coverage), blank semantics,
ancestor clearing, all launch modes, v1 migration/v2 round-trip and invalid
paths, actual Tk start/stop, replay pacing parity, a 57-second real audio/GPU
group replay crossing two state boundaries, capture/CSV state labels, and
actual GPU state uniforms with positive uninterrupted flow/star clocks. Minimum
680x700 layout bounds were checked for root, parent and leaf selections; buttons
remain visible. Live/synthetic CLI help accepts the new option. Live loopback
and desktop screenshot review were not rerun for this control-only change.
Restart Studio to load the hierarchical controls; existing previews keep their
current settings. Nothing committed; aa44d54 remains HEAD.

### Waterfall perspective refinement

The user accepted the other Water forms and development controls, but asked
to replace the waterfall's bottom pond/rings with an infinite fall fed by a
river between a distant world horizon and a nearer cliff lip. Rain ripples
were explicitly accepted and must remain unchanged.

Only dream.frag's waterfall projection/shading/material mapping changed, with
coverage added to the existing shader_test.py and documentation updates.
FallsSurface analytically intersects a horizontal river and vertical cliff
face meeting at the same edge. A slow camera approach lowers the viewpoint
below the lip: the river appears broader/shorter, then river, cliff edge and
sky move out of frame, leaving falling water. The camera retreats continuously.
The material uses one continuous flow coordinate around the lip; downstream
streaks stretch with fall distance. Existing wave normals shade the upstream
river. The basin and its concentric rings are removed only from the waterfall.

This remains stylized two-plane perspective shading, not fluid simulation or
volumetric terrain. No renderer, audio, studio, state timing or other form edits.
The held waterfall preset and existing family/main-blend routes all use it.
Baseline: work/elemental/waterfall-perspective/before.frag.
Initial wide/intermediate/close captures were visually inspected. Further
verification for this pass is recorded below when complete.

Final synthetic checks passed: --waterfall-test extends the family harness,
comparing 108 unaffected-world/sea/dye/rain samples against the pre-refinement
shader (at most 1/255 difference), 60 form samples and 20 family/live boundaries.
An actual GPU sweep covers 4,802 camera frames at 60 Hz across approach and
retreat, quiet and dense inputs. Maximum mean frame delta is 1.8122/255.
GPU hit-classification probes confirm separate sky/river in the wide view,
over 98% falling-face coverage in close-up, and no bottom pool intersection.
Existing non-Water temporal changes remain as documented in earlier entries.

The camera test initially found a magnified source-shape pop at 99.283s.
Cell-edge fading alone was insufficient; the inherited hard appearance
threshold also needed easing. Both changes are gated to the waterfall's
weight, leaving rain, dyes and sea unchanged. Final wide/close and blended
captures were visually inspected. Landscape and portrait target checks passed;
earlier timing samples had concurrent GPU work and are not isolated performance
measurements. Evidence: work/elemental/waterfall-perspective/final/.

All three complete tracks were rerun through the corrected held waterfall:
Balloon 5,316, Chasing You 3,136, Warbot Jazz 7,015 frames (15,467 total).
Audio CSVs match the previous family runs exactly apart from the state label.
All 84 periodic captures passed contrast/dark/headroom checks: minimum contrast
9.256, minimum dark fraction 8.93%, no clipped pixels. The 18-image three-track
contact sheet and final portrait capture were visually inspected. Evidence:
work/elemental/waterfall-perspective/final-music/{review-sheet.png,verification.json}.
The first pre-fix music runs remain separately under music/ as diagnostic data.
git diff --check passed. Changes remain uncommitted; HEAD is still aa44d54.
Next: choose waterfall in Studio and restart the preview for user review.
The new waterfall is already used by Water family and main blend; no re-import.

### Current expansion: Water family, development controls, main blend

The user accepted the sea world ("Really Cool!") and explicitly requested
more Water forms/melding, a useful development environment, and integration
into run_live_visualizer after verification. This supersedes the older
isolated-only/pending-world-acceptance statements below. No commit authorized.

Water now cycles sea -> dye currents -> rain/ripples -> waterfall -> sea,
with held debug states 7–10 for review and state 6 for the family. The accepted
sea equations are intact. Pool views pitch down; dye exposes folded colored
channels, rain uses seeded expanding rings and sparse streaks, waterfall uses
a falling curtain and receiving basin. These are procedural effects, not fluid
transport or simulated droplets. All reuse existing source material/palettes.

The main blend now admits Water between Cosmic visits: initial 116–158s visit,
full takeover 126–144, then every 140s. Startup and Cosmic's original timing
remain unchanged. Water's independent 112s form cycle varies successive visits.
The same shader runs through run_live_visualizer; no launcher switch is needed.

New app/visuals/studio.py and run_development_studio.bat expose useful controls:
state/source/track/speed/duration, captures, sessions, preset menu, review tab.
Menus are functional; import/export means settings JSON, not arbitrary shaders.
The existing replay/live/preview scripts remain the execution paths. No new
dependencies. Replay pacing now accounts for work elapsed against song time;
previous capped sleeps made the real-time option too fast. All chunks remain.
See DEVELOPMENT_STUDIO.md for workflow and limitations.

Executed checks so far:
- Studio standalone checks passed: session round-trip and validation, every
  state command, actual Tk start/stop callbacks with a real replay child,
  identical real GPU/audio results at speed 1 and 0, real-time pacing floor.
- Family GPU checks: 84 preserved-world/sea cases, 60 form/profile/time cases,
  16 form/live boundaries, explicit live admission and restoration checks.
  Held sea and unaffected accepted worlds differ by at most 1/255.
- Water synthetic checks: 36 stills, four input responses, silent evolution,
  181 integrated frames, 360 draws across four output sizes. 1080p sea draw
  median 4.08 ms, p95 4.13 ms (GPU only, not all-form performance).
- Dye, rain, waterfall and main-blend captures were visually inspected.

The first boundary test flagged a 3.455/255 mean frame change at 158s; the
original blend measured 3.455 as well. Later original blend boundaries change
up to 19.662/255; the revised check allows existing temporal changes plus .25,
while holding family-only boundaries below 3. This is preservation evidence,
not a claim that existing blend motion is artifact-free. Family boundary max
was .795/255. A startup wraparound was corrected before final replay.

Desktop UI screenshot inspection timed out waiting for Computer Use app
access. Tk functionality was tested, but desktop layout is not visually
verified. Evidence so far: work/elemental/water-family/{verification,synthetic}/.

Final verification: all three complete tracks ran through BOTH Water and the
main blend (30,934 analyzed/rendered frames total). All audio CSV values matched
the previous accepted-wave runs exactly, excluding the intended state label.
All 168 sampled frames passed structure/headroom checks. Water captures had
at least 33.95% dark pixels and no clipped pixels. Main blend had up to 1.50%
clipped pixels, with maxima in the unchanged Cosmic dwell (e.g. 208s), not a
claim of zero clipping throughout the existing blend. Both 18-frame contact
sheets were visually inspected: work/elemental/water-family/music/.

Held dye/rain/waterfall also passed 1080p and portrait draws; captures inspected.
Their 1080p GPU medians were 4.80/5.54/4.43 ms respectively (measured while a
replay was active, not isolated whole-app performance). Tk layout bounds and
three-track deduplication were verified; the minimum window height now keeps
buttons visible. Studio checks passed again after these changes.
The finished Studio was opened on the desktop for user review. Nothing staged
or committed; aa44d54 remains HEAD. git diff --check passes with line-ending
notices. Next: user review of new forms, melding and Studio before checkpoint.

### Water world built around the accepted waves

The user accepted the rough-sea refinement ("okay much better") and requested
the Water world. That supersedes the pending-acceptance wording in older entries.
The new setting is an open night sea between distant rocky islands, with low
mist, reflected atmospheric light, submerged colored currents and sparse foam
on high, steep storm crests. Quiet passages retain slow currents and dark space.
The camera now reveals the horizon. The accepted height field, current function,
audio mapping, clocks and rough-sea response were preserved.

This step changes only app/visuals/shaders/dream.frag, shader_test.py and these
two development notes. The environment is Water-only procedural shading using
existing palettes; no new renderer, uniforms, assets, dependency or audio edits.
Distance haze and broader far-surface normal samples soften the distant sea.
The islands are background silhouettes; foam is visual shading, not fluid
simulation. Water remains isolated state 6, without scheduler changes.

Verification executed for this world pass:
- Water test: 36 still cases, independent input responses, silence motion,
  181 integrated frames, 360 draws across landscape/portrait/ultrawide sizes.
  Largest integrated mean frame delta 2.883/255. 1080p GPU draw median 4.414 ms,
  p95 4.829 ms; these exclude audio capture and presentation.
- New --water-world-test mode: exact accepted wave height AND motion fields
  at nine profile/time combinations, stable background under audio changes,
  responsive foreground and continuous storm threshold (.01787/255 mean delta).
- All 72 other-world comparisons / 144 GPU frames are pixel-identical,
  preserving Organic, Geometric and Cosmic appearance.
- Full-size landscape, portrait and quiet captures were visually inspected.
- All three complete music replays passed (15,467 frames); every audio CSV
  field matched the accepted rough-sea runs exactly. All 45 sampled frames
  retained contrast, at least 62.86% dark pixels, and zero clipped pixels.
  The twelve-image music contact sheet was visually inspected.

Evidence: work/elemental/water-world/{final,comparison}/. Baseline before this
world pass: work/elemental/water-world/before.frag. The new composition still
needs user review. No second element was started. HEAD remains aa44d54;
accumulated Water/audio/replay changes remain uncommitted.
Music captures and summary: work/elemental/water-world/music/.
git diff --check passed (line-ending notices only). The new live Water window
is open on BlackShark loopback; initial observed inputs were silence. Next:
user music review of this composition, then explicit checkpoint approval.

### Rough-sea response requested after live review

The user likes the overall Water treatment and requested that intense music
drive waves more like a raging sea. This supersedes preserving the previous
high-energy wave amplitude, while retaining the accepted quiet appearance.

Changes are confined to dream.frag's Water functions, shader_test.py comparison
coverage, this handoff and ELEMENTAL_DEVELOPMENT.md. A smooth weighted
bass/flux/sparkle envelope (60/25/15 percent, threshold .55 to .88) introduces
taller and faster broad crossing swells beneath the existing fine ripples.
Wave phases retain constant rates on the existing clocks; audio controls the
added amplitudes rather than multiplying accumulated time. The surface bounds
expand to contain the swells. Rough water scans up to 40 intervals to bracket
a front crossing before the existing 14 refinements, so tall waves obscure
distant troughs. Quiet water retains the original search and shading.
No audio, renderer, shared clocks, other worlds or palette code changed.

Verification executed for this refinement:
- GPU before/after comparison: quiet and moderate images at 18, 67 and 180s
  are pixel-identical. Chorus height standard deviation increased 2.55-3.36x;
  temporal height change increased too (combined amplitude/movement measure,
  not a literal speed ratio). The .55 boundary is continuous within a mean
  pixel delta of .00921/255.
- Existing-world comparison: all 72 cases / 144 GPU frames are pixel-identical
  to the pre-refinement shader, including Organic, Geometric and Cosmic routes.
- Water test passed all 36 still cases, four individual audio responses,
  silence motion, 181 integrated frames and 360 draws across four sizes.
  Largest integrated mean frame delta 5.101/255. High-energy 1080p GPU draw
  median 4.59 ms / p95 5.87 ms; higher cost is the rough-water surface search.
  This excludes audio capture and presentation.
- Chorus captures at 18 and 67s and a full-size Balloon frame at 90s were
  visually inspected: substantial rolling crests, dark troughs and inherited
  colored material, rather than the previous nearly flat expanse.
- All three complete music replays passed: Balloon 5,316 frames, Chasing You
  3,136, Warbot Jazz 7,015 (15,467 total). Every CSV field matched the previous
  onset-corrected run exactly, including impacts. All 45 periodic captures
  retained structure/dark coverage without clipping; minimum dark fraction
  53.3%. A twelve-frame, three-track contact sheet was visually inspected.

Baseline: work/elemental/rough-sea/before.frag. Synthetic evidence:
work/elemental/rough-sea/{first,comparison}/. This remains a procedural height
field without breaking foam or fluid simulation. Music evidence and summary:
work/elemental/rough-sea/music/{review-sheet.png,verification.json}. The user
subsequently accepted the stronger motion. No commit has been made.
The prior Water preview was closed normally and reopened with this shader.
BlackShark loopback is receiving varying audio (including nonzero impacts);
the updated window was left open for user review. git diff --check passed.

### Approved onset-order correction: implemented and verified

The user approved the proposed correction after the three-track discovery.
Moved the three onset detector calls in app/visuals/live_visual_test.py to
immediately after SignalProcessor normalization/smoothing, before
VisualSignalConditioner's visual slew limit. No thresholds, normalization,
continuous conditioning, shader code, renderer clocks or parameters changed
in this correction. The shared function fixes both live input and WAV replay.

Extended app/audio/onset_test.py with the real shared analysis path (FFT,
normalization and conditioning) using isolated synthetic tones for all three
bands, in mono and stereo. It first failed on the old ordering, then passed
with the fix. Tests verify silent input, two separate attacks, stable sustain,
release, absence of cross-band onsets, and unchanged 0.12 continuous slew bounds.
signal_test.py, normalize_test.py, audio_frame_test.py and
parameter_mapper_test.py assertions passed; multiband_onset_test.py was also run
and its detector outputs inspected.

All three COMPLETE song replays were rerun through Water: 15,467 GPU-rendered
frames. Comparison with the pre-fix CSVs proved exact per-frame equality for
every field except impact, including bass/mids/highs, scale/movement/sparkle,
flux and song time. Restored event coverage:
- Balloon: 732 nonzero impact frames / 633 consecutive-event clusters; max .4955.
- Chasing You: 487 frames / 361 clusters; max .4963.
- Warbot Jazz: 1,193 frames / 1,057 clusters; max .5000.
These counts describe threshold crossings, not validated beats or distinct
perceptual events. Frequent events during dense material need listening review.

All 45 periodic Water captures retained structure and dark coverage without
clipping at the existing thresholds. Another 45 GPU snapshots cover the
strongest song event, about .256s later, and about 1.024s later in Organic,
Geometric, Cosmic canvas, Water and normal blend. The actual renderer integrated
every preceding CSV input; rasterization alone was skipped between snapshots.
The three resulting contact sheets were visually inspected. All snapshot
structure assertions and continuous positive star-clock checks passed.
Warbot's maximum event occurs on its initial attack at song time zero.

Regressions rerun: Geometric 423 frames passed (minimum contrast 4.946), Cosmic
handoff 19 frames passed, moon opacity 122 frames passed (155 opaque lit centers,
27 hidden centers). No attempt was made to keep event-driven output identical
to the old zero-impact path; restoring those existing expressions is intentional.
Actual synchronized listening to this corrected build remains user review.

Evidence: work/elemental/onset-order/{balloon,chasing-you,warbot-jazz}/,
comparison.json and event-frames.json. The fix adds app/audio/onset_test.py to
the accumulated tracked Water changes. Handoff and Elemental notes updated;
git diff --check passed with existing LF-to-CRLF notices. Nothing staged or
committed; aa44d54 remains HEAD. Next: review restored events with live music,
then seek explicit checkpoint approval. The earlier assistant-launched Water
window was closed normally and reopened with this corrected code; BlackShark
loopback initialization succeeded and initial observed inputs were silence.

### Resumed review and three-track replay

The user confirmed that Water's waves look fine. Preserve this accepted wave
treatment; that statement is not blanket acceptance of every Water feature.
The live Water window launched through the existing loopback pipeline on
BlackShark V3 Pro BT; initial observed inputs were silence. It was left open
for the user's review. Accelerated replay windows close at each track's end.

Reused the existing decoded files and replay_test.py for complete Water runs:
- Balloon: 226.8 song seconds, 5,316 analyzed/rendered frames, 16 captures.
- Chasing You: 133.8 seconds, 3,136 frames, 9 captures.
- Warbot Jazz: 299.3 seconds, 7,015 frames, 20 captures.

Total: 659.9 seconds / 15,467 frames. The 45 sampled captures passed checks for
spatial structure, retained dark areas and no clipped highlights. Minimum
sample contrast across tracks was 16.803; minimum dark fraction 46.5%; maximum
clipped fraction zero. Twelve representative frames in the review sheet and
an additional full-size Balloon frame were visually inspected. The replay is
decoded real music through the actual analyzer/renderer, without audible
playback; it does not replace synchronized live listening or full-motion review.

Added optional --capture-dir and --capture-interval to the existing
app/visuals/replay_test.py, reusing shader_test.save_png. Capture defaults off;
no renderer, shader, normalization or state scheduling changed in this resumed
pass. Capture-enabled and default capture-disabled 24-frame smoke runs produced
identical per-frame audio metrics. git diff --check passed with the existing
LF-to-CRLF notices. No dependency changes or commits.

Important discovered limitation: impact was zero on all three complete tracks.
A first coverage assertion incorrectly required impacts from every track; the
report now distinguishes continuous-control variation from absent event
coverage. Read-only diagnosis found the actual structural cause: live/replay
call onset detection AFTER VisualSignalConditioner, whose max_delta is 0.12,
but the onset detector requires a rise greater than 0.2. Such an onset cannot
occur. A synthetic alternating zero/full-scale reproduction confirmed maximum
rise 0.12 and zero events. Earlier synthetic shader impact tests bypassed this
audio path and therefore never verified real-song event delivery.

Recommended next bounded task: review moving onset detection ahead of visual
conditioning while preserving conditioned continuous controls and existing
normalization. Verify all three tracks and regressions for the accepted worlds,
because restoring impact would affect every world. No audio correction has
been implemented at that time; the user subsequently approved it and the
current correction entry above supersedes that status.

Evidence: ignored work/elemental/music/{balloon,chasing-you,warbot-jazz}/,
work/elemental/music/summary.json and review-sheet.png. Existing source MP3s
and decoded WAVs were reused unchanged. Current tracked changes now also include
app/visuals/replay_test.py; the rest of the Water file list below still applies.

### Initial implementation and synthetic verification

Checkpoint reconciliation: HEAD is `aa44d54` (Refine Geometric corridor material
gathering). The user explicitly accepted that checkpoint and the preceding
Cosmic/Geometric foundations. Pending-review labels in the historical entries
below are superseded by that instruction; they are not current acceptance gates.
Tracked files were clean before Water. Existing untracked research folders and
root helper scripts were preserved. No commit has been made for Water.

Water is an isolated oblique liquid expanse: the actual shared DreamWave field
is gathered into submerged dye currents beneath a multi-scale wave surface.
Surface normals drive selective reflections and small refractive offsets.
Bass raises broad waves, flux shears currents, sparkle reveals fine ripples and
reflections, and the existing impact envelope disturbs a bounded patch. Quiet
and silence retain moving water and dark channels. The Organic membrane is not
used as Water's surface. Normal blend scheduling remains unchanged.

Changed: app/visuals/shaders/dream.frag, app/visuals/shader_test.py,
app/visuals/live_visual_test.py, this handoff. Added: run_water_music.bat and
ELEMENTAL_DEVELOPMENT.md. Renderer, uniforms, audio analysis, dependencies,
Cosmic geometry/star code and Geometric surface code remain unchanged.
Replay inherits the new live-state choice without a replay source edit.

Verification actually executed in the existing .venv on the RTX 3070 Laptop GPU:
- Water GPU test: 36 silence/quiet/active/chorus samples through 600 seconds;
  spatial structure, dark-space coverage and highlight headroom assertions pass.
  Four independent audio controls produce visible pixel changes. Silent motion,
  a 1/60-second continuity sample and 181 renderer-integrated attack/release
  frames pass. Largest integrated mean frame change: 3.494/255.
- 360 additional Water draws across 1280x720, 1920x1080, 720x1280 and 2560x1080.
  At 1080p, median GPU draw time 2.761 ms / p95 2.807 ms (80 timed samples after
  warm-up). This excludes live capture, presentation and end-to-end latency.
- Final quiet/active/chorus contact sheet, full-HD and portrait PNGs inspected.
  These show a broken reflected-light path, submerged colored streaks, larger
  chorus waves and retained dark channels. Captures are not live music review.
- Accepted-shader comparison: 72 cases / 144 GPU frames across all six existing
  state routes, three input levels and four times. Final maximum difference
  1/255 per channel, within the test's explicit rounding tolerance.
- Geometric regression: 423 frames pass, minimum contrast 4.946.
- Cosmic handoff: 19 frames pass; moon opacity: 122 frames pass (155 opaque lit
  centers, 27 hidden centers); blended sweep: 183 frames pass, minimum 10.038.
- Parameter mapper parity test passed; live/replay CLI help confirms `water`.
- git diff --check passed with existing LF-to-CRLF conversion warnings only.

One intermediate highlight test failed narrowly at chorus/67s. Final Water
tonemapping was corrected; the complete Water test then passed. Evidence and
metrics are under ignored work/elemental/final; legacy regressions are in
work/elemental/*-regression. The baseline shader is work/elemental/accepted.frag,
exported from aa44d54 before edits.

Review with run_water_music.bat (real system audio) or
run_state_preview.bat water (fixed synthetic inputs). Neither was left running.
At this initial stage live music and user aesthetic review were pending; the
resumed review above supersedes that status. Procedural gathering has no frame history;
no automatic Water transition or fluid simulation was added. Read
ELEMENTAL_DEVELOPMENT.md for commands, limits and the five future directions.
The optional second element was deferred to keep this pass focused on Water.

Next: user reviews Water with music, then approves a commit if satisfied.
Do not stage or commit pre-existing untracked research/helper files.

## Historical pass: Geometric material gathering (accepted as aa44d54)

The user accepted the preceding Geometric/star work and committed it as
`d8053d6`. Historical pending-review statements below describe earlier work.
At the time of this historical entry the pass was uncommitted; the user has
since accepted and committed it as aa44d54. See the current entry above.

Changed files: app/visuals/shaders/dream.frag, app/visuals/shader_test.py,
and this handoff. No renderer, uniforms, audio, dependencies, or launchers changed.
Untracked root-level live_visual_test.py and shader_test.py remain untouched.

The corridor is traced once before the shared DreamWave field is evaluated.
Its axial surface coordinates gather/stretch/mirror-fold that actual field
onto the walls, floor, ceiling and turned passage. The final material uses
the field substantially, including its moving colored artifacts, rather than
an 18-percent tint. Recessed panel joints, derivative-filtered veins, local
edge pulses, inherited glyph colors and darker openings add bounded detail.
Bass/impact pressure cannot pinch the chorus corridor closed. Surface hit
refinement removes the coarse stepping visible in the previous captures.

The isolated Geometric preview no longer activates the timed Cosmic takeover.
A 32-second turning capture revealed a camera-inside-wall blank frame; the
camera now approaches the junction before sliding sideways. Existing segment
turn timing remains, not a new path/camera system. Cosmic stars, bodies, rings,
moon materials and their depth code are unchanged. Shared-field changes can
still affect material inherited by the Cosmic canvas during mixed states.

Verification actually executed on the GPU:
- Same-time quiet/active/chorus PNG captures at 18 seconds, visually inspected.
  Quiet is dark blue-violet, active carries colored material along surfaces,
  and chorus is brighter/more detailed while retaining an open dark passage.
- Extra turning PNGs inspected at 32, 33, 66 and 67 seconds.
- shader_test.py --geometric-test work/geometric-gather/geometry-test:
  423 frames across three input profiles and both turn directions; passed,
  minimum spatial contrast 4.946. This guards blank frames, not aesthetics.
- shader_test.py --sweep work/geometric-gather/sweep: 183 frames and existing
  washout assertions passed; minimum spatial contrast 10.038.
- shader_test.py --handoff-test work/geometric-gather/handoff: 19 frames,
  Cosmic space isolation and boundary continuity passed.
- moon_opacity_test.py: 122 GPU frames passed, 155 opaque lit and 27 hidden
  moon centers.
- git diff --check passed; Git reports only existing LF-to-CRLF warnings.
  Three tracked files modified, nothing staged or committed; all pre-existing
  untracked research/helper files remain in place.

Evidence is under ignored work/geometric-gather/. Preview remains
run_geometric_preview.bat (synthetic inputs, not live audio). Live music,
full-resolution performance and continuous-motion acceptance remain untested.
The mirrored material repeats; openings imply depth rather than tracing extra
rooms. Gathering is a reversible procedural domain transformation, not stored
past frames or persistent captured imagery. Existing timed/audio state weights
still select the world; phrase-aware scheduling is not implemented here.

Next: user reviews this one pass. Do not automatically commit or expand scope.

## Previous checkpoint: Geometric world and continuous star drift

An external geometry pass added isolated_geometric_scene to
app/visuals/shaders/dream.frag. It renders a procedural corridor with long
straight spans, committed turns, varying width/height, material color swatches,
and sparse falling glyph columns. It is available in the existing isolated
Geometric preview via run_geometric_preview.bat; the normal shared state
composition also mixes it when the existing geometric weight is active. This is
an uncommitted prototype awaiting user visual acceptance, not an architectural
replacement or a new renderer.

The same pass introduces star_time and star_rate in the existing
app/visuals/renderer.py. The renderer eases a positive star clock from normal
speed toward a faster chorus speed, then the shader moves three depth sheets in
one-way, slightly parallel headings. They wrap naturally through the procedural
field rather than reversing after an audio beat. High chorus energy lengthens
and thins their wakes; quiet stars vary in brightness/twinkle. This supersedes
the prior direct time-times-current-audio star experiment, which could twitch.

Verification actually run after this pass: Geometric quiet and active captures
at 18 seconds were visually inspected; the 183-frame GPU sweep rendered; the
19-frame handoff continuity test passed; the 122-frame moon opacity/occlusion
test passed (155 lit centers, 27 hidden centers); and renderer, shader-test,
and live-entry Python compilation passed. git diff --check passed with only
the existing LF/CRLF warnings. No live music run, frame-rate measurement, or
user acceptance of the Geometry/star changes has happened yet.

Untracked root-level live_visual_test.py and shader_test.py exist beside the
project files. The actual launchers use app/visuals versions, so these root
copies were not run, edited, staged, or treated as source of truth. Preserve
them until the user decides whether they are intentional references.

## Current continuation: planetary canvas and handoff

Latest bounded pass: user accepted the three moon identities. Added selective
planet/ring vividness via cosmic_vivid_material in dream.frag. Drive uses
existing conditioned scale/flux/sparkle (45/35/20 percent), with a quiet dead
zone and bounded saturation/brightness. Planet adjustment precedes lighting;
ring adjustment retains existing shadow modulation. Moons, stars, geometry,
audio analysis and diagnostic land/ocean colors are unchanged.
At 18s canvas, quiet before/after PPM hashes match exactly; active PNGs were
visually compared (richer rings, modest planet lift). Moon test (122 frames),
handoff test (19), sweep (183) and diff check passed. Captures/tests are under
work/cosmic-vivid. Live aesthetic review is pending; no commit made.

Moon–ring interaction is now implemented as a small colored dust wake around
each orbital position. It uses existing sparkle/flux and the assembly envelope;
it does not alter depth, geometry or moon opacity. GPU regressions remain the
acceptance gate. The follow-up tuning now gives the wake a longer tail and
stronger near-moon ring density/color, fading continuously behind each moon.
Dust persistence and star motion remain future bounded passes. User review of
this stronger tuning is pending. The latest refinement bends the tail along
the ring curve and samples each moon's animated material for its color.

The next small adjustment gives the inner, middle and outer moons rates 0.52,
0.42 and 0.32 respectively, with their dust wakes synchronized.

Star rotation is now implemented as a shared center-locked field with input-
scaled exposure trails. Quiet captures remain short; active captures show
curved light dashes. The latest tuning shares the planet spin clock at a slower
baseline, accelerates with audio, tapers trail ends, and preserves varied
twinkling point stars during dwell. User review is pending.

The field is layered into three parallel-offset depth bands with different
rates, so stars do not move uniformly. A chorus-only threshold controls longer
exposure trails; the shader test's chorus profile captures that case.

Latest review: user likes live canvas; requests more vivid planet/rings and
three moons with their own dye/fire/layered-candy identities. Implemented only
the moon material step in dream.frag, with CPU reference updates in
moon_opacity_test.py. Orbits, opacity and shading remain unchanged. 122-frame
moon test passed (157 lit centers, 26 hidden centers); 183-frame sweep and
19-frame handoff checks passed. Captured PNG reviewed; live motion acceptance
is pending. Ring disturbances, stronger planet/ring color and coherently
rotating star trails are recorded in COSMIC_DEVELOPMENT.md, not implemented.

User review: gather and release accepted as a foundation; moons remain solid
and occlude behind the planet, but intersect rings. The synthetic preview did
not react to music because it uses fixed inputs, not audio capture. Next review
uses run_cosmic_music.bat (live canvas hold), or its transition argument for
the 40-second cycle with live audio. Normal live launch remains unchanged.

Creative backlog from this review: moon/ring dust disturbances, evolving
surface/ring color and material during gathering, release into a distinct next
vocabulary, slower floating or musical camera pressure, shared ring-plane/view
motion, and slow star drift with size/brightness changes. These are separate
bounded tasks, not implemented or accepted here. Preserve solid body depth
while exploring deliberate material effects; do not reintroduce accidental
transparency. The user requests no unsolicited usage updates.

Live-preview routing verification: Balloon.wav completed 40 seconds / 938
analyzed and GPU-rendered frames in each of canvas and transition modes. CSV
confirmed varying scale, movement and sparkle, not fixed preview values.
CLI help, Python compilation and diff checks passed. Actual live loopback
playback and the new BAT have not been exercised this turn. No shader or
audio-analysis changes were made for this routing step. No commit made.

The user accepted the rebuilt geometry as a better foundation and authorized
returning to the original planetary-canvas vision. The existing field is now
remapped into spherical coordinates and passed as opaque material to the same
depth composition used by the Cosmic diagnostic. A shared envelope contracts
the field, introduces rings/moons, holds the planetary world, and releases it.
The live timing is a provisional 140-second cycle; music controls the existing
surface expressions, small system pressure and ring brightness. This is not
phrase-aware timing or a feedback/particle transport simulation.

Double-click run_cosmic_transition.bat for the 40-second diagnostic cycle.
`run_state_preview.bat canvas` holds the mapped DreamWave surface indefinitely.
`cosmic` remains the accepted land/ocean geometry reference. The normal live
launcher now uses the new handoff, with the old competing Cosmic warp disabled.
See COSMIC_DEVELOPMENT.md for exact phase times, geometry ownership, test
commands, limitations and bounded assignments for smaller models.

Source files changed in this continuation: dream.frag, shader_test.py, this
handoff; added COSMIC_DEVELOPMENT.md and run_cosmic_transition.bat. Renderer,
audio processing and dependencies were not changed. The user subsequently
accepted gather/release as a foundation; live musical feel is still pending.
Nothing has been committed.

Verification for this continuation: the 183-frame GPU sweep passed (minimum
contrast 10.07); the moon test passed 122 GPU frames, including 157 opaque and
26 hidden center checks; the new handoff test passed 19 GPU frames checking
dark space during the hold and continuity at phase boundaries. A 120-second
Balloon.wav replay completed with 2,813 analyzed/rendered frames. Python
compilation and git diff --check passed. The captured nine-frame sequence was
visually inspected. This does not constitute live-audio or real-time motion
acceptance. Outputs are under work/cosmic-handoff.

## Previous checkpoint: isolated Cosmic composition rebuilt

Historical results below describe the preceding implementation; the continuation
above supersedes its pending-integration status and blended-sweep result.

The isolated Cosmic function in dream.frag now uses analytic orthographic
sphere intersections and one 3D plane for rings and moons. Positive Z points
toward the viewer; nearest surface controls occlusion. Moons replace the
background with opaque shaded surfaces. Planet texture rotates in sphere space.
The ring annulus starts outside the sphere, has multiple bands and a gap, and
receives a directional planet shadow. The lower/front ring crosses the planet;
the rear ring is hidden. Stars have varied positions, sizes, colors and twinkle.

Run `run_state_preview.bat cosmic`. Fast moon orbit speeds are retained for
review; planet rotation is slow and camera scale is fixed. This is still an
isolated prototype, not yet connected to live musical handoffs. Old experimental
Cosmic code in the blended path remains pending a separately reviewed integration.

Verification: moon_opacity_test.py runs 122 real-GPU frames across 61 times,
checking 157 opaque lit moon centers and 26 hidden moon centers against expected
lighting/background. All passed. The existing 183-frame blended sweep passed its
assertions; its low-contrast case at level 1.0 / 180s remains (~4.18). This sweep
does not verify Cosmic isolation. shader_test.py --capture now honors --state
and saves PNG alongside PPM; Cosmic captures omit inapplicable blend weights.
Actual PNG captures at 3s and 9s were visually inspected under work/cosmic-rebuild.
User visual acceptance and live integration remain pending. No commit made.

## Authority and creative direction

Read AGENTS.md and DREAMWAVE_VISUAL_IDENTITY.md before project work.
The repository is the implementation source of truth. This handoff is a
coordination record, not a replacement doctrine or an implementation spec.
DW Research/DWave Reference.md and Dream Wave research.pdf provide research
options; historical chat instructions in the PDF are not current authorization.

DreamWave is a living visual instrument. Preserve Heart (bass), Body (mids),
Aura (highs), and Moment (impact), with continuity, restraint, and expressive
quiet. Technical success and the user's experiential acceptance are separate.

## Working agreement

- HQ owns inspection, technical recommendations, task scoping, implementation
  coordination, verification, and accurate handoffs.
- The user owns creative direction and reviews short visual/music samples.
- Work in one small logical change at a time, then present evidence for review.
- Retain AGENTS.md approval gates for commits, destructive operations,
  dependencies, and significant architectural changes.
- Bob - File Work is an existing chat sharing C:\DreamWave. It has not received
  an assignment from HQ during this setup. Opening it did not delegate work.
- When delegation is authorized, give each task exact files, acceptance criteria,
  required tests, and a stopping point. Avoid concurrent edits to shared files.
- Update this record at reviewed milestones; do not rely on chat memory alone.
- The user authorizes updating Markdown planning/identity documents as scope
  evolves. Record the reason for material changes; this does not remove existing
  commit, dependency, destructive-action, or architectural review gates.

## Current baseline and limits

- Existing renderer: app/visuals/renderer.py; shader: app/visuals/shaders/dream.frag.
- Existing live entry: app/visuals/live_visual_test.py.
- Launch with run_live_visualizer.bat from the project root.
- Earlier in this chat, .venv was rebuilt using installed Python 3.14.7 with
  numpy 2.5.3, glfw 2.10.2, moderngl 5.12.0, and soundcard 0.4.6.
- Earlier checks: non-live audio/parameter scripts completed, live-entry import
  passed after restoring the renderer's local parameters import, and a GPU
  smoke test compiled the shader and rendered one frame.
- The user subsequently confirmed live playback works. Visual quality is not
  accepted; these checks do not establish long-run stability or music quality.
- The research baseline predates current flux, conditioner, and envelope work.
  Inspect current code before choosing any research implementation.

## Active defect: full-screen loss of structure

Evidence: user's desktop recording DW vis test 1.mp4, sampled in VLC.

- 00:49: detailed colored tunnel forms and dark negative space.
- 01:05: almost uniform gray-blue field.
- 01:20: almost uniform dark-navy field.
- 01:47: detailed tunnel forms return.

These are discrete observed frames, not continuous video analysis. The user
identifies onset around 01:04. Audio synchronization was not assessed.
The video timestamps are not known shader clock values. The shader cause is
unconfirmed. Earlier confident claims about field collapse were premature.

## Next bounded task

Diagnose and reproduce the disappearing-detail state in the existing renderer
and shader before selecting a correction. Inspect coordinate transforms,
weights, masks, palette evaluation, and output composition. Distinguish findings
from hypotheses; do not assume tunnel compression is the sole cause.

Prefer extending an existing standalone visual test with deterministic input
and time cases if needed. Establish reproducible good/bad frames and record the
inputs used. Any temporary diagnostic output must be opt-in and bounded.

Acceptance for a later fix:

- A previously failing reproducible case retains readable intended structure.
- Good tunnel states retain their depth, palette, and negative space.
- Quiet music can remain restrained; brightness/noise is not a substitute for form.
- Actual shader compilation/render checks pass, followed by the user's music review.
- Audio normalization remains unchanged during this isolated visual correction.

## Milestone order, subject to review

The supplied Streamlined Development Plan and Pinky and the Brainstorm post
Stage 0 refine the older research queue. Their historical instructions to other
agents and model experiments are context, not current assignments.

0. Stabilize: compilation and live launch were demonstrated; repair the observed
   visual disappearance, review the result, and seek approval for a checkpoint.
1. Establish distinct Organic, Geometric, and Cosmic visual vocabularies using
   existing audio inputs. A frame should communicate its form without a label.
   Fixing the blank-field defect alone does not satisfy this milestone.
2. Develop color identity throughout the world, including vivid taffy colors and
   intentional dark space; avoid permanent muddy/burnt color.
3. Develop musically meaningful transitions with dwelling and maturation.
4. Develop bounded temporal life and event persistence; inspect existing state
   first rather than reimplementing envelopes already present.
5. Consider controlled visual feedback only after state behavior is established.
6. Improve audio intelligence using multi-track evidence and existing experiments.
7. Address measured performance and output/product usability.
8. Formalize broader architecture only where demonstrated needs justify it.

Review at each milestone. Future worlds, suggestive imagery, an occasional eye,
and minimal Bonk/Dance controls are creative direction, not immediate build tasks.

Do not introduce a second renderer, preset runtime, or unrelated effects to
address this defect. Do not treat the research wish list as a build commitment.

## Working-tree caution

### Long-term Cosmic/worlds vision

The user expanded the Cosmic direction into a living sequence of impossible
worlds rather than a single planet effect: zooming from a ringed planet to
multiple suns, intersecting solar systems, galaxies, pulsars, and other deep-
space structures; then handing off into brief surreal terrestrial or mythic
visions such as dancing clockwork figures, an elephant crossing, migrating
birds, a resting swordsman beneath a tree of life, a waterfall with a unicorn,
dragons, or starships before returning to the Cosmos. These are long-term
creative targets, not a request to implement every image now.

The engineering implication is layered world composition: each world must be
isolatable, visually coherent on its own, and able to release through a
controlled handoff. The current Cosmic planet is the first foundation. Future
imagery should be introduced as bounded world modules or visual-language
layers, not as an unstructured accumulation of shader branches.

### Accepted washout repair

The real-GPU deterministic sweep added to shader_test.py rendered 183 frames
at 320x180 across fixed input levels and shader times. Before the correction,
three frames were exactly uniform and several nearly uniform. Using the domain
before tunnel/horizon scrolling for fractal inversion, with a denominator floor,
removed all exactly uniform frames in the same sweep. Four reproduced cases
have explicit contrast regression assertions. One case at high input and 176s
remains low-contrast and needs further investigation after this change's review.
This is synthetic GPU evidence, not an exact replay of the recorded live inputs.
The user accepted the live visual improvement and approved checkpoint 01f4249.
No audio code changed.

### Organic membrane and root variation accepted

After approximately eight minutes of music playback, the user liked the slow,
consistent blue-violet membrane as a resting/background scene during quieter
audio. Preserve that calm home character. Organic visual vocabulary is still
being developed; this does not complete Milestone 1.

The next small experiment adds bounded local flex from existing flux and a
small traveling ripple from existing impact. Neither changes the animation
clock, palette, audio analysis, or state weights. Quiet flux <= 0.08 and impact
<= 0.10 introduce no added motion. Existing shader_test.py now supports quiet
and active --profile presets for --capture, saving inputs and state weights.

Verification: quiet before/after capture at shader drift time 100s was pixel-
identical; active captures differed and were visually inspected. The 183-frame
real-GPU sweep and four washout assertions passed. The previously noted
low-contrast case at 176s remains. The user accepted the active flex after about
15 minutes of playback. Membrane and capture tools are committed as baed993.
The palette is provisional, not a permanent color restriction.

Current experiment: 31 connected, tapered procedural branches in the membrane's
warped domain, gradually replacing its body/ridge through root_mix. This uses
a provisional slow dwell cycle (about 157 seconds), not music-aware scene
selection. Existing flux bends branches; audio and palette logic are unchanged.
Capture metadata includes root_mix (a blend amount, not a normalized state
weight). Quiet, active, and intermediate frames were visually inspected: the
result reads as branching roots/veins, not yet a dense fungal web. The 183-frame
GPU sweep and washout assertions passed. The user accepted the live feel as
viscous and organic, mostly calm with occasional forward presence.

### Optional audio replay

`app/visuals/replay_test.py` replays a decoded 48 kHz, 16-bit WAV through the
same analyzer, mapper, and GPU renderer without playing audio. It is not used by
`run_live_visualizer.bat`; private audio and generated metrics remain ignored.
The renderer accepts song time explicitly while live rendering keeps the wall
clock.

Deferred Cosmic idea: existing imagery gathers inward, forms a planet and rings,
dwells, then morphs, erupts, or collapses. Preserve continuity; this is outside
the current Organic experiment.

At setup, existing changes include live_visual_test.py, renderer.py, dream.frag,
the untracked research directory, launcher, and three helper scripts:
apply_3b.py, verify_invariants.py, verify_strings.py. Preserve them.
The shader text-check scripts contain stale expectations and are not rendering
tests. Do not rerun apply_3b.py: it is a mutating patch script.
No commit, deletion, or cleanup was performed as part of this setup.
