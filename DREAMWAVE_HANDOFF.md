# DreamWave working handoff

Updated: 2026-09-25

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
