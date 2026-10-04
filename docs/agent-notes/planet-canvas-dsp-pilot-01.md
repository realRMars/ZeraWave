# Planet Canvas DSP pilot 01

Authorized: two bounded held-Planet mappings, after Bob/Prompter approval and
Robert's "sounds good". Implementation is separate from artistic acceptance.
Baseline HEAD: `0342e518a7bd2c521416e8027a7920668fc5ee51`, plus the six unchanged
standalone DSP files bound by `work/standalone-dsp-01/review-index.json`.

## Implemented route

`live_visual_test.analyze_samples(..., descriptors=True)` measures the original
multichannel PCM through the existing `AudioAnalyzer.describe_samples`, before
the unchanged legacy mono FFT. Its version-1 dictionary travels in the existing
optional `AudioFrame.descriptors`. Live/replay owners feed new analysis frames to
the renderer's independent sample-clock mapper. Capture, queues, player runtime,
legacy normalization, beat/onset semantics and twelve-band meters are unchanged.

Only explicit held `canvas` / state 5 is eligible. Main, Galaxy/state 36, ordinary
sequences and every configured transition pair are excluded, including endpoint
holds. Eligibility is checked again before writing the shared spatial uniform.

- Elastic Lenses: `q=smoothstep(.04,.35,spectral_spread)`;
  ratio `1 - signal_confidence * .20 * (1-q)`.
- Braided Flow: `q=smoothstep(.10,.65,fullness)`;
  ratio `1 - signal_confidence * .25 * (1-q)`.
- Ratio strengthens toward a higher amount with tau .7s; relaxes downward with
  tau 1.2s. It advances only on a newer descriptor sample timestamp.
- The current resolved base amount multiplies that ratio; manual amounts remain
  ceilings. Disabled/zero effects remain zero. Nested Windows is unchanged.
- Valid-format invalid/silent snapshots target neutral rather than using fading
  feature values. A repeated invalid timestamp clears stale modulation. Missing,
  malformed or wrong-version payloads clear immediately.
- Explicit reset, source-ID change, rewind, context exit and EOF clear state.
  A sample-time jump above .25s is conservatively treated as a discontinuity;
  normal preview packets are 2048 frames / 42.667ms. No capture policy changes.

The optional session boolean `planet_dsp_pilot` defaults to false and is stored
only when true. Load/save/New preserve/reset it without adding UI controls.
Preview commands forward `--planet-dsp-pilot` only for a held Canvas selection.
Synthetic preview with an active pilot is rejected because it has no PCM
descriptors. Old sessions/default-off routes skip descriptor work and transport,
construct no pilot mapper and retain original uniform values.

Source colors, palette holds/cycles/reset, material cycles/isolation, background
stars, shooting stars, moon geometry/wakes, brightness compression and other
visual drivers are unchanged. The pilot adjusts existing material coordinates;
it adds no shader, pass, geometry or persistent GPU resources.

## Task-local review setup

`work/planet-canvas-dsp-pilot-01/review-A.json` and `review-B.json` differ only in
the pilot boolean. Both select seven cycling materials, stars/rings/moons/shooting
stars and the same two spatial ceilings (.65 Elastic, .55 Braided). Those amounts
are review choices within the existing range, not changed authored defaults.
Material holds are 12s so the 90s input crosses every selected material.

`matched-texture.wav` is deterministic synthetic stereo PCM: quiet, narrow tone,
broad equal-RMS multitone, narrow return, stronger broad/narrow contrasts and
quiet/silent release. Formula, actual segment RMS and hashes are in
`input-index.json`; seed is 2917, visual seed 7301. This is a signal-routing and
motion comparison, not a musical/artistic certificate.

Studio: load one review session, select Test track / Real time, then Start preview.
Loading these task-local sessions deliberately selects their own effects; user
defaults/settings are never overwritten. Save an existing working session first
if its unsaved Studio choices need retaining. Use the later task-local matched
runner for exact clocks/seed; ordinary live runs cannot be called matched A/B.

## CPU evidence and limits

`app/visuals/planet_canvas_dsp_test.py` runs deterministic PCM and exact functions
compiled via AST, avoiding renderer/capture/UI imports. It checks 120 frames
against the pre-task shared analysis, flag-off no extra descriptor work, on-path
legacy equality, antiphase stereo, descriptor partitions, numerical bounds,
confidence/invalidity, repeated timestamps, source/discontinuity resets, mutable
manual ceilings, actual spatial uniform assignment and excluded contexts. It
also checks session versions/defaults, actual CLI declarations, equal A/B configs
and actual replay orchestration with fake window/audio-file objects.
The actual live owner function is also exercised with supplied PCM and a fake
stream module in four contexts, with zero capture threads/device calls.
The actual live owner function is also exercised with supplied PCM and a fake
stream module in four contexts, with zero capture threads/device calls.

These are offline numerical and mocked routing checks. Descriptor equal-endpoint
partition invariance is reused; mapper partition checks use constant targets.
Changing targets are sampled once per bounded incoming packet, so arbitrary
packet repartitioning can change mapper integration approximation. Render polls
never advance it. No new all-music or semantic recognition claim is made.

Initial harness failures (None instead of empty transition pair, CLI AST scope,
incomplete fake renderer fields) and a partial patch duplicate were corrected;
they are retained in the review index. No user work or tests were removed.

GPU/normal-speed visual evidence, perceptual strength, brightness distribution,
native pacing and listening remain unverified. Bob was asked to coordinate a GPU
window because ComfyUI may be active. No runtime windows/devices were opened for
the CPU stage. No commit, push, Main rollout, dependency change or root-doc edit.
Actual results return to Prompter, then a separately approved fresh review.

Deferred matched commands (run only after Bob confirms the GPU window):

```powershell
.\.venv\Scripts\python.exe -B work/planet-canvas-dsp-pilot-01/matched_preview.py --label A
.\.venv\Scripts\python.exe -B work/planet-canvas-dsp-pilot-01/matched_preview.py --label B
```

The helper delegates to the existing replay and renderer at identical 2048-sample
steps and paces those times at 1x (~23.44 frames/s). Both arms request 640x360,
lock resizing and record actual client/framebuffer/screen sizes. This preserves
production replay timing. It is not a 60Hz/native performance test; GPU/readback
cost can make playback late. Each arm saves captures every .5 sample seconds and
metrics; earlier evidence directories are never overwritten. This helper has
only been syntax checked so far.

## GPU visual delta — approved window, 2026-10-03

Robert explicitly freed the GPU window ("no ill work in comfy tomorrow. keep
going"). Both 90-second matched arms completed through the existing replay and
renderer. No live capture/device use, production-code change or art retuning was
needed. The original CPU `review-index.json` remains unchanged; follow
`work/planet-canvas-dsp-pilot-01/final-review-index.json` to the bound visual delta.
The paragraphs above describe the earlier CPU checkpoint, not the final GPU status.

Both arms: RTX 3070 Laptop GPU, 640x360 client/framebuffer/screen/viewport/shader
resolution, windowed, seed7301, 2110 exact sample-clock frames over90s, seven12s
material holds, Elastic .65 and Braided .55. Input hash/analysis prefix, frame
times, flow/star clocks, captured legacy parameters and material selections match.
Only the session's pilot boolean differs. A made zero descriptor calls; B made2110.
The unchanged `matched_preview.py` was wrapped by task-local instrumentation in
`gpu_delta_review.py`, sampling GPU queries once every24frames and recording CPU
analysis, submission, query wait and swap-return intervals separately.

### Visible findings, builder observations only

- Planet, rings, moons, source palette and starfield retain their recognizable
  composition. Every sampled pixel in the tested outer-sky mask (radius>.67 of
  frame height) is identical across A/B. The shooting star at41.003s matches.
- Narrow-spectrum passages reduce Elastic to about .52 and Braided to .4125;
  broad equal-level multitone passages return to about .65/.55. Measured intensity
  medians are .65207 narrow and .65233 broad: this controlled contrast changes
  spectral texture, not level. Fullness/spread change together here, so GPU
  appearance attribution is to the combined pilot; CPU tests isolate each mapping.
- The visible change is **modest**. At16s contour placement/width differs; at28s
  the broad-texture images are almost identical. At41.003s it is subtle. The
  clearest inspected difference is the Mosaic contour arrangement around74s,
  but the whole scene still looks very similar. This is restrained modulation,
  not evidence of a major new visual gesture or a meaningful9/10 upgrade.
- B frames at22.528,23.509,24.533s and73.515,74.539s show continuing rotation,
  material changes and evolving contour placement in sampled sequence. Quiet6s
  and release86/89s pairs retain the scene; no abrupt cut is apparent in those
  samples. Inspection was of sampled frames, not continuous listening or a
  full-frame-rate watched movie. The local HTML player preserves their normal
  sample-time cadence (~2Hz images).
- Peak clipped-pixel fraction is .9635% A / .9618% B. Largest matched-frame
  clipped-fraction difference is .0243 percentage points. Neither pair inspection
  nor these measurements indicates a material highlight increase in this fixture.

### Bounded cost observations

Warm GPU render queries:87samples/arm, median2.229ms A /2.244ms B,
p99 2.644/2.609ms. Warm CPU renderer submission median1.217/1.222ms over2109frames.
Whole analysis-call median1.216/2.115ms; B descriptor-call median1.193ms, p99
1.849ms, max12.431ms. Background, power and thermal conditions were uncontrolled.
These are two sequential observations, not a statistically established overhead
or frame-rate guarantee.

Both arms have179swap-return intervals over50ms; all coincide with sampled capture
frames. PNG/readback and pacing are inside these intervals, outside the recorded
render submission/GPU timer. P95 swap intervals are94.24/94.55ms, so this
capture-heavy harness is not smooth native presentation evidence. Total wall
durations including startup are91.05/90.93s for90sample seconds. Startup readiness
was .410/.409s in these warm observations, not a cold-start certificate.

### Review route and acceptance

Open `visual-delta/review.html` for synchronized A/B; inspect16s,28s,41s,74s and
86-89s plus texture-change boundaries23/38/53/68s. Raw frames, exact numerical
traces, costs and hashes are linked by the final index. No CPU suite was rerun
because the six implementation files and six DSP files stayed byte-identical;
the changed evidence helpers were syntax parsed and matched-output checks ran.
Robert's latest requirement is independent9/10 for a meaningful upgrade. No
builder score or PASS is asserted. Actual results return to Prompter for one
separately approved fresh critic; no rollout, commit, push or next form starts here.

## GPU visual delta — approved window, 2026-10-03

Robert explicitly freed the GPU window ("no ill work in comfy tomorrow. keep
going"). Both 90-second matched arms completed through the existing replay and
renderer. No live capture/device use, production-code change or art retuning was
needed. The original CPU `review-index.json` remains unchanged; follow
`work/planet-canvas-dsp-pilot-01/final-review-index.json` to the bound visual delta.
The paragraphs above describe the earlier CPU checkpoint, not the final GPU status.

Both arms: RTX 3070 Laptop GPU, 640x360 client/framebuffer/screen/viewport/shader
resolution, windowed, seed7301, 2110 exact sample-clock frames over90s, seven12s
material holds, Elastic .65 and Braided .55. Input hash/analysis prefix, frame
times, flow/star clocks, captured legacy parameters and material selections match.
Only the session's pilot boolean differs. A made zero descriptor calls; B made2110.
The unchanged `matched_preview.py` was wrapped by task-local instrumentation in
`gpu_delta_review.py`, sampling GPU queries once every24frames and recording CPU
analysis, submission, query wait and swap-return intervals separately.

### Visible findings, builder observations only

- Planet, rings, moons, source palette and starfield retain their recognizable
  composition. Every sampled pixel in the tested outer-sky mask (radius>.67 of
  frame height) is identical across A/B. The shooting star at41.003s matches.
- Narrow-spectrum passages reduce Elastic to about .52 and Braided to .4125;
  broad equal-level multitone passages return to about .65/.55. Measured intensity
  medians are .65207 narrow and .65233 broad: this controlled contrast changes
  spectral texture, not level. Fullness/spread change together here, so GPU
  appearance attribution is to the combined pilot; CPU tests isolate each mapping.
- The visible change is **modest**. At16s contour placement/width differs; at28s
  the broad-texture images are almost identical. At41.003s it is subtle. The
  clearest inspected difference is the Mosaic contour arrangement around74s,
  but the whole scene still looks very similar. This is restrained modulation,
  not evidence of a major new visual gesture or a meaningful9/10 upgrade.
- B frames at22.528,23.509,24.533s and73.515,74.539s show continuing rotation,
  material changes and evolving contour placement in sampled sequence. Quiet6s
  and release86/89s pairs retain the scene; no abrupt cut is apparent in those
  samples. Inspection was of sampled frames, not continuous listening or a
  full-frame-rate watched movie. The local HTML player preserves their normal
  sample-time cadence (~2Hz images).
- Peak clipped-pixel fraction is .9635% A / .9618% B. Largest matched-frame
  clipped-fraction difference is .0243 percentage points. Neither pair inspection
  nor these measurements indicates a material highlight increase in this fixture.

### Bounded cost observations

Warm GPU render queries:87samples/arm, median2.229ms A /2.244ms B,
p99 2.644/2.609ms. Warm CPU renderer submission median1.217/1.222ms over2109frames.
Whole analysis-call median1.216/2.115ms; B descriptor-call median1.193ms, p99
1.849ms, max12.431ms. Background, power and thermal conditions were uncontrolled.
These are two sequential observations, not a statistically established overhead
or frame-rate guarantee.

Both arms have179swap-return intervals over50ms; all coincide with sampled capture
frames. PNG/readback and pacing are inside these intervals, outside the recorded
render submission/GPU timer. P95 swap intervals are94.24/94.55ms, so this
capture-heavy harness is not smooth native presentation evidence. Total wall
durations including startup are91.05/90.93s for90sample seconds. Startup readiness
was .410/.409s in these warm observations, not a cold-start certificate.

### Review route and acceptance

Open `visual-delta/review.html` for synchronized A/B; inspect16s,28s,41s,74s and
86-89s plus texture-change boundaries23/38/53/68s. Raw frames, exact numerical
traces, costs and hashes are linked by the final index. No CPU suite was rerun
because the six implementation files and six DSP files stayed byte-identical;
the changed evidence helpers were syntax parsed and matched-output checks ran.
Robert's latest requirement is independent9/10 for a meaningful upgrade. No
builder score or PASS is asserted. Actual results return to Prompter for one
separately approved fresh critic; no rollout, commit, push or next form starts here.

Deferred matched commands (run only after Bob confirms the GPU window):

```powershell
.\.venv\Scripts\python.exe -B work/planet-canvas-dsp-pilot-01/matched_preview.py --label A
.\.venv\Scripts\python.exe -B work/planet-canvas-dsp-pilot-01/matched_preview.py --label B
```

The helper delegates to the existing replay and renderer at identical 2048-sample
steps and paces those times at 1x (~23.44 frames/s). Both arms request 640x360,
lock resizing and record actual client/framebuffer/screen sizes. This preserves
production replay timing. It is not a 60Hz/native performance test; GPU/readback
cost can make playback late. Each arm saves captures every .5 sample seconds and
metrics; earlier evidence directories are never overwritten. This helper has
only been syntax checked so far.

## Contrast revision 01 — approved evidence-first pass, 2026-10-03

This is the one Bob-approved contrast candidate following the critic's technical
PASS and provisional meaningful-upgrade4/10. No9/10 or user acceptance is asserted.
The current source now uses ratio floors **Elastic .60 / Braided .50**, superseding
the earlier shallow .80/.75 values. Only the mapper's two depth coefficients and
the three corresponding numerical test assertions/report fields changed. All
thresholds, confidence weighting, easing, resets and routing remain unchanged.
Default OFF still follows legacy; active amounts multiply the current manual or
authored ceilings and never exceed them. No geometry, shader, colors, events,
material-cycle timing, other-world or player/backend changes were added.

### Preserved and new evidence

Earlier indices/artifacts are untouched. Before editing, the shallow mapper,
test and task note were copied into
`work/planet-canvas-dsp-pilot-01/contrast-revision-01/shallow-source/`.
The new final binding is `contrast-revision-01/review-index.json`, with exact
contrast-only and complete task diffs, source hashes, runs, inputs and artifacts.
The original CPU index SHA remains
`bdc18ed9bda20af5eba0f0a21d3be29a7fc684f63dc945c57898ac19e85f5e4b`.
The six standalone DSP file hashes remain unchanged.

A read-only ComfyUI queue check reported no running/pending work before this
authorized GPU window; unrelated processes were left alone. Existing installed
PyAV18.1.0 in `C:\RMars Studio\standalone-env\python.exe` encoded the task's raw
RGB frames. No packages or settings changed, and no desktop audio played.

CPU descriptor coverage of the existing `work/audio-replay/Balloon.wav` selected
136.192–226.176s (89.984s) by q-range/interior coverage/validity, before viewing
images. Confidence is1 throughout. Spread q p05/median/p95 is .03965/.68003/.96359;
fullness q is .09010/.71925/.95308. Feature correlation is .78367, with q-neutral
fractions4.31%/2.89%. This passage has useful modulation coverage; a deeper floor
can change it. Full audio analysis prefix is preserved. Graphics start fresh at
the passage boundary for every arm; the prefix is not a rendered scene-history
claim. The optional aligned WAV sidecar is provided for reviewer listening only.

Current legacy/shallow natural A/B was recorded and checked before the edit.
Separate diagnostics inject spread while fullness=1, or fullness while spread=1,
after real constant-PCM analysis. These are **INJECTED feature diagnostics**, not
descriptor measurements of that PCM. Their input, seed, times and settings match;
the shared diagnostic legacy baseline has no injected descriptors. Both controls
retain .65/.55 ceilings. The deeper candidate uses the same passage/diagnostics;
only its B arms were recaptured, reusing the exact off baselines with provenance.

Eight silent MP4s were encoded and decoded to verify every frame. Natural arms
have2109frames,89.984s at375/16fps (23.4375). Diagnostic arms have2110frames;
their90s PCM ends with a partial packet, so the final movie frame holds an extra
26.667ms and duration is90.026667s. No frames were skipped. PNGs sample .5s for
lossless comparison. The synchronized normal-speed reviewer is
`contrast-revision-01/deeper-comparison/review.html`, with legacy/shallow/deeper
columns for the natural passage and each diagnostic. All run traces retain
source/local times, actual dimensions, material/flow/star clocks, legacy values,
descriptor payloads, effective controls and separated capture costs.

### Actual checks and observations

The updated standalone `planet_canvas_dsp_test.py` PASS includes120exact legacy
analysis frames, stereo antiphase/partition checks, new bounds, easing/confidence,
missing/invalid/repeated/source/gap resets, current manual/cycle values, exact
uniform routing, Main/Galaxy/sequence/transition exclusions, saved sessions,
six mocked replay contexts and four mocked live-owner contexts with zero capture
threads. `git diff --check` and helper AST syntax checks PASS. No broad suites,
live devices or playback/listening were used in this revision.

All eight GPU runs completed on RTX3070 Laptop GPU at actual640x360. Compared
arms match exact source, seed, clocks, legacy parameters and material cycles.
The non-varied diagnostic control matches baseline exactly. Tested outer-sky
pixels are identical for all sampled comparisons. Natural deeper effective
ranges are Elastic .39601–.64111 and Braided .29731–.53353; diagnostic minima are
.40128 and .28162 respectively, easing toward .65/.55 at high features. They
remain within current ceilings. Natural peak clipped-pixel fractions are
2.24349% legacy /2.24219% shallow /2.24523% deeper; diagnostics peak .00825%
for every arm. This is evidence for this capture condition, not a universal
brightness guarantee. The largest matched natural-frame clipped-fraction
difference between deeper and legacy is .16102 percentage points; unchanged
peak fractions do not imply pixel-identical highlights.

Builder inspected three-arm natural sequence74/86/88.533s, current natural89s,
spread2/14/74s and fullness2/14/74/80s. The deeper candidate visibly shifts some
contour/shape placement more than shallow, especially late natural textures and
low-fullness diagnostic holds. Broad sections/high-feature diagnostic holds stay
close to legacy. Planet, rings, moons, authored palette and starfield retain their
identity. It is still the same restrained visual mechanism. The numerical
contrast increase does not establish a meaningful9/10 upgrade. Continuous movies
were generated/decoded but not watched by this builder; image tools provided
sampled sequence inspection only. No audio was heard.

Natural legacy/shallow/deeper warm CPU render-submit medians are
1.227/1.244/1.239ms, synchronous readback3.774/3.755/3.506ms and encoder-pipe
writes .282/.274/.276ms. Capture-heavy wall lateness p95 is12.94/14.90/15.35ms,
with maxima196.91/165.07/221.29ms. PNG writing is separately logged; these effects
perturb desktop pacing. Fixed-timebase MP4s retain every frame at normal speed.
No new GPU query/native60Hz/scanout or cold-start guarantee is claimed. Runs are
sequential with uncontrolled background/power/thermal conditions.

The natural passage is mostly active; earlier synthetic quiet/release evidence
remains preserved for shallow, while deeper neutral/quiet/reset behavior has CPU
evidence only. Natural sustained listening, fullAV and multi-hour variety remain
unverified. Diagnostic run `session` is the shared natural settings template;
its track field is overridden by the explicit hashed diagnostic `source` in the
run record. This is evidence bookkeeping, not a Studio routing change.

### Review boundary

Dev Studio can load `contrast-revision-01/natural-deeper-session.json` and preview
held Planet Canvas using Test track; current source supplies the deeper mapper.
Load the corresponding legacy session for OFF. Studio runs the full prefix track
normally, unlike the passage movies' fresh graphics history. No extra UI controls
were added. For controlled attribution use the synchronized movies and exact
traces; preserved shallow code remains available via the evidence runner.

Return these actual results to Prompter/Bob for the one separately approved fresh
critic. The independent meaningful9/10 gate remains unresolved. Stop after this
candidate: no additional tuning, rollout, next world, root-document changes,
staging, commit or push occurred.
