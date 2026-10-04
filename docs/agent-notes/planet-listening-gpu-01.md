# Planet listening GPU smoke - builder follow-up

Robert approved the minimum GPU check on 2026-10-04 at 06:29 UTC via Bob.
Scope: compile/link and bounded hidden draws of the current three changed shaders,
verify local-input and expanded Artifact uniform bindings, and record first-use
versus immediate cached timings. No application or settings changes were made.

Evidence: `work/planet-listening-gpu-01/review-index.json`. CPU checkpoint retained
unchanged: `work/planet-listening-01/review-index.json`, SHA256
`f0c96ca2c70bad1819846dfb28abf5ce1d59a8e344e7176d92d4717e8ead9399`.

Preflight found no Python/ZeraWave/Comfy processes. GPU background utilization was
33%, memory 1732 MiB on the RTX 3070 Laptop GPU, driver 617.14. The test did not
alter other processes, driver cache, audio devices, focus or user workflows.

Actual GPU result: PASS; 16 draws, two owned hidden contexts, actual window
and framebuffer 320x180; Echo's existing targets remained 512x512. First context
checked windows OFF, packed local inputs ON, all four Artifact channels, lazy Echo,
all three Enveloper modes/history and return OFF. Cached context checked the same
shader sources with neutral OFF inputs. All draws returned GL_NO_ERROR with
nonblank native RGB8 readbacks; no Echo disable or Enveloper fallback was observed.
45 Planet uniform rows and four Artifact listening channels reflected correctly.
Readback hashes/numerical bounds establish basic draw viability, not art quality.

Compile/link wall seconds (first current-source use / immediate cached repeat):
- dream: 133.930552 / 0.260767
- echo_weave: 0.055026 / 0.000950
- envelopers: 0.060186 / 0.001085

Renderer.create wall seconds: 134.351923 / 0.299466.
First-use cache state is unknown; no true cold-cache guarantee or causal slowdown
comparison is claimed. The earlier 130.535-second first startup remains historical
evidence of a material startup limitation. This smoke is not broader benchmarking,
continuous listening, normal-speed motion evidence, a multi-hour soak or artistic
acceptance. No capture, decoded playback or microphone was used. The owned helper
completed within its 240-second deadline, closed both contexts and left no matching
Python/ZeraWave/Comfy processes. All 21 authored originals and all bound application
sources are unchanged before/after; the CPU checkpoint and its artifacts remain intact.

Exact five 0-4 gains: Liquid Alloy `bass_shape` (Bass disk width), `flux_deform`
(Flux surface deformation); Prismatic Lattice `bass_shape` (Bass vertex size),
`flux_tilt` (Flux tilt); Echo Weave `flux_advection` (Flux ink travel rate). All
retain normalized input ceiling 1. The earlier CPU note/clarification called the
Lattice 'Luminous'; the actual catalog/UI name is Prismatic Lattice.

Authored stores load automatically in held Planet Canvas independently of the
two pilot flags. Live override OFF uses saved authored values. DSP spatial and
Star attack-flight retain separate opt-in gates. Main, other worlds and sequences
are excluded. Old documents migrate in memory with newly added windows OFF and
exact old values; originals are not rewritten during load.

Custom ranges reuse one existing FFT, Start inclusive/End exclusive. Empty windows
are rejected; one-Hz positioning does not improve the 23.4375-Hz current bin spacing.
Flux uses positive magnitude changes; Bass/Sparkle/Movement use selected means with
their documented normalization. Custom Impact detects one normalized selected-mean
onset with sensitivity and exponential visual release; it is not legacy max-of-three
onsets. No ADSR, instrument separation or independent Energy window is provided.
The original Star attack window still stops at 315 Hz; presentation windows can use
higher bins. Spatial presence controls retain Selected/Cycle availability limits.

Save desired current live values, then restart Development Studio at Robert's
convenience to load changed modules; closing/reopening only the dialog retains imports.
This task did not relaunch Studio. Open held Planet Canvas -> Audio Tuning, select a
target, enable Live override and opt in only the desired windows. Use named profiles
for listening trials; promote authored values only when Robert chooses them. Normal
music listening and visual acceptance remain with Robert. No critic, commit, push,
Main rollout, portable build or root-document edit was performed.
