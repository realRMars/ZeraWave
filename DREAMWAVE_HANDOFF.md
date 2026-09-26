# DreamWave working handoff

Updated: 2026-09-26

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
