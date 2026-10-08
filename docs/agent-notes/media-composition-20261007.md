# Media composition actual-results handoff — 2026-10-07

Sole Builder, `C:\ZeraWave`. Independent composition work is reviewable in the
current `run_zerawave_studio.vbs` checkout. This is a **partial assignment
checkpoint**: browser display is blocked on dependency approval/validation;
rigged 3D and video-audio/timeline scope still need decisions. No critic was
dispatched. No commit, push, release or root planning-document update occurred.
Robert owns acceptance; return this evidence through Prompter/Bob for review.

## Source and preservation

HEAD remains `fe1a7b74f791fbfcc1879798e5e944be50ae061f`. The authoritative baseline
is the actual dirty accepted Increment 1 source, not HEAD: 264 bindings and raw
copies in `work/media-composition-20261007/baseline.json` and `baseline/`.
The Increment 1 manifest digest there is
`3eb3cd827a53a535de80e9cb221835e1fdb915f998e28e439637c3ed16ed94fd`.
Final source hashes/copies, task-only delta, evidence index and digest identities
are in that task directory. Its README/REPORT identifies the passing runs.

Renderer/world code and preview_playback.py remain byte-identical to this task's
baseline, as does the launcher. Existing dirty code in those files is preserved.
Audio/analyzer modules, AGENTS, ROADMAP, ZERAWAVE_HANDOFF and unrelated dirty
color/Roots/palette notes retain baseline hashes. User layout/library files were
not used for tests: each Qt run used isolated paths. The new Layers name keeps
the old `image_layers` dock identity; existing tabs/header/dock interactions stay.
The four supplied `images n vids` originals retain their recorded byte counts
and SHA-256 hashes. No broad hunt or originals alteration occurred.

## Implemented scope

- Dynamic empty Layers stack with stable IDs/names, thumbnails/type, visibility,
  inherited lock, drag reorder/reparent, Front/Back, independent duplication,
  deletion/reset, contextual Selected controls and three presentation modes.
- Composition Editor shares normalized affine/crop/mask/fit/flip contracts with
  the existing compositor. It supplies selection/handles, move/resize/rotate,
  numeric 0.1-step entries, aspect lock, alignment, zoom/pan/Fit/100%, checkerboard,
  editable polygon masks/cuts and crop. Clean output has no editor decorations.
  The editor renders bounded layers only, never a second complete world.
- Nested isolated groups (opacity/blend once), placement-preserving reparenting,
  guarded ungrouping, W3C Normal/Multiply/Screen/Add/Difference in the established
  display-encoded premultiplied pipeline. Authored world colors are unchanged.
- Owner-held 64-command/8 MiB Undo/Redo: one drag, slider gesture or completed
  mask is one command. Pending path Apply/Discard/Cancel is explicit. Interrupted
  transform drags restore committed state on hide/focus loss/Escape. Text focus
  and canvas shortcuts do not issue BONK/Hold or audio transport.
- Actual silent video/GIF pixels in the existing renderer context: layer
  Play/Pause, Stop/first frame, seek, rate, in/out, forward loop and ping-pong.
  GIF transparent partial frames/disposal/source delays and sprite-sheet
  grid/range/FPS/alpha use the same layer tools. Imports/assignments do not play.
  Visual Pause freezes presented animation; audio remains independent. Visual
  Stop releases animation owners; hiding a layer releases its resources/freezes
  elapsed time and retains play intent. Closing editor/collapsing controls does
  not stop output. Session reopening never starts transports/browser.
- Actual static glTF/GLB triangles/materials in the existing GL context, plus
  yaw/pitch/roll and ordinary layer transforms. The editor's simplified geometry
  guide is labeled. See feature instructions for the strict material/extension
  subset. Rigging, animation, morphs and proprietary Unreal materials are rejected.
- Media double-click/Enter shares explicit use commands; repeat activation
  selects a matching layer and Add another instance deliberately duplicates.
  Audio uses the sole AudioOwner, stays stopped and keeps same-source position.
  Collections store memberships, with create/rename/delete and membership actions.
  Cancel pending imports leaves completed references intact. Refresh/relink retain
  identity/settings; failed/cancelled operations retain valid references. Removing
  a reference lists uses, keeps recoverable editing state, supports Undo, preserves
  originals and does not unload independent AudioOwner audio.
- Artistic session v5 / composition v2 / library v2 migration and round-trip;
  prior artistic v1–v4 and assigned two-slot scenes load, unused slots disappear.
  Runtime handles/play state stay out of JSON. Session/revision/destination/run
  and frame-generation guards reject late work. Extended bounded IPC was tested
  with a real command larger than the previous 64 KiB reader boundary.

## Backends, limits and pending capabilities

Exact approved `av==19.0.1` binary/no-deps installation completed; Qt was not
upgraded. PyAV code is BSD-3-Clause; its bundled FFmpeg build includes GPL codec
components. No redistribution is authorized. Primary method/license links and
notices/codec constraints are recorded in `docs/STUDIO_MEDIA_COMPOSITION.md`.
Implementation and GIF/sprite/GLB fixtures are original; supplied assets retain
Robert's ownership. This is not patent or release clearance.

Bounds: 128 references/32 collections/16 validation jobs; 32 composition layers,
6 group levels, 8 masks ×128 points/layer, 256 KiB edit state. Four visible
animated sources, one silent decode worker, 96 MiB aggregate native-frame reverse
cache, 128 MiB shared double-buffer staging; no whole-clip preload. GOP decoding
rejects more than 512 frames/two seconds per refill. Static/model staging 128 MiB,
GPU residency/replacement 256 MiB, group targets 256 MiB, mask residency/replacement
64 MiB. Static models: 64 MiB dependencies, 200k vertices/64 primitives,
8 textures/32 MiB decoded. Editor preview max 1024 side and model cache 64 MiB.
These payload/component limits do not guarantee total process RSS.

Loudman is the exact supplied JavaScript embed, not an invented API. Configuration,
viewport/cadence, offline policy and a dormant optional browser adapter exist.
**No functioning browser display/security claim:** PySide6-Addons 6.11.1 approval
is pending. The proposed exact command is
`C:\ZeraWave\.venv\Scripts\python.exe -m pip install --only-binary=:all: --no-deps PySide6-Addons==6.11.1`.
It matches installed Qt, roughly 169 MB; Qt/Chromium license notices apply.
The adapter intends one muted off-record GET/HEAD-only viewport, no native bridge,
project/file access, popups/downloads/permissions, bounded pixels/cache/request
rate and retry backoff. Chromium response-download/RSS hard bounds and actual
isolation/capture behavior remain unresolved until approved browser validation.
No dependency installation or web content autoplay happened without approval.

Video audio is currently always silent. The proposed explicit Use video audio
route into the single Session Waveform source would replace that source without
simultaneous mixing/reverse audio. Robert's requested audio lanes/keyframes/cuts
need an agreed timeline/mixer design. Static GLB exports from Blender are usable
within the documented subset; rigged/animated 3D needs animation/pose/material
scope. Those follow-up questions remain pending. A useful next art tool to define
is transform/opacity keyframes within that timeline; it is not implemented here.

## Validation and practical cost

Sixteen selected standalone checks pass, with source bindings and individual
logs. They cover composition/migration/history; registry/decode/relink/cancel;
GPU alpha/group/mask/flip/blends/allocation/resize/cleanup; actual static GLB;
Qt DPR/geometry/handle mouse events; dynamic Studio activation/transport/session/
layout/stale guards/reference Undo; existing AudioOwner/Raw drive/Band Analyzer,
visual playback/scope, scoped analysis-history replay and Qt corrections.
The first Qt-corrections run hit temporary-session `WinError 5` on replace;
the isolated retry passed. Preserve both, without claiming an environment-wide
file-permission repair. Obsolete two-slot UI assertions were migrated into the
current Studio test; baseline source remains preserved. No pytest infrastructure.

Actual RTX 3070 Laptop GPU component evidence uses a visible 1280×720 GLFW
window/framebuffer/internal target, 144 Hz monitor, swap interval 1, a technical
color backdrop, exact supplied JPEGs and the short H.264 clip. Two 2.4-second
ordinary arms each returned 346 swaps. Query arms hold decoded pixels and take
24 GPU samples separately; captures/readback are outside distributions.
Passing final run: `component-cost-1791422695326780400.json`.

| Case | GPU mean / median / p95 / max ms | Swap mean / p95 / p99 / max ms | Swap returns/s |
|---|---|---|---|
| Two stills | .271 / .255 / .386 / .412 | 6.943 / 7.201 / 7.398 / 7.531 | 144.02 |
| Group + mask + video | .297 / .211 / .949 / 1.080 | 6.945 / 7.476 / 7.717 / 8.180 | 144.00 |

No >50 ms presentation interval in those short arms. Two static textures:
14,773,544 bytes; root targets 14,745,600 bytes, grouped targets 29,491,200;
animated texture 1,177,600 and mask 921,600 bytes. The moving arm observed 51
changed-frame publications: worker get/conversion median 12.979 ms, p95 13.750,
max 13.934; texture write/allocation CPU wall median 4.734 ms, p95 5.022,
max 5.082. Upload calls and total draw CPU wall include driver backpressure;
neither is isolated CPU or GPU upload cost. This is incremental compositor cost,
not full-world FPS or measured scanout. Thermal/power/background state uncontrolled.

Long supplied clip is H.264 2558×1388/30 Hz, 276.17 s. A 9-second normal-clock
120–122 s ping-pong trace produced 134 changed-frame reader samples, 42 descending
PTS steps, maximum 95,938,560 cache bytes. Reader gaps median 45.33 ms, p95 96.93,
p99 510.26, max 821.61; maximum get/conversion 591.61 ms. Reader gaps include
sampling sleep/waits and are not presentation FPS. **Reverse is functional but
large-clip cache refills are visibly risky and not uniformly smooth.** One bounded
window-start seek hypothesis worsened tails; its source/results were retained
under `experiments/window-start` and the exact previous passing source restored.
No optimization/FPS improvement claim follows. VFR GIF forward timing/PTS is
verified; universal VFR reverse cadence, unusual orientation/SAR/HDR/alpha codecs
and real user model subsets are not all physically validated.

Native Windows mouse evidence ran the existing Roots renderer with supplied
moving video at fixed 1280×720 internal pixels and 937×601 dock/display pixels.
It observed canvas movement/selection/history, Undo/discard, Selected controls,
video Play motion/PTS and Stop/first frame, with AudioOwner output/playing false.
The first startup-tab drag interruption was fixed and retested. A rotation
attempt entered Mask due to tool-selection desynchronization: no native rotation
claim; the setter/UI synchronization was fixed and Qt handle checks passed.
Native visual Pause was acknowledged after the clip ended, so that observation
does not prove advancing-video freeze (the standalone freeze test does).
Native evidence binds its own older source; later logic/bounds fixes use focused
checks, not a repeated native session. No physical DPI switch, heard output,
natural live music, scanout, all-codec coverage or multi-hour soak claim.

Syntax/AST checks and `git diff --check` pass; exact task delta was reviewed.
All owned check processes exited. First failures, individual successes and the
rejected experiment are retained. Current working code is uncommitted.

## Review path and proposed owner updates

Launch current Studio; import a supplied JPEG/video; double-click it; edit a
still while output is stopped; duplicate/group, adjust opacity/blend, draw a mask
and exercise Undo. Start compatible Main, select video → Selected → silent Play,
seek a short in/out segment and Ping-pong; compare Composition Editor to clean
Visualizer and change World/Layers presentation. Stop the layer/visuals. Reopen
the saved isolated v5 session and verify no autoplay. The larger clip's reverse
tails and pending web/model/audio items are review constraints.

Feature instructions are in `docs/STUDIO_MEDIA_COMPOSITION.md`. Suggested
Overseer checkpoint: record the dynamic composition candidate and the source-bound
technical checks, keep acceptance pending, and list WebEngine approval/bounds,
large-clip reverse tails, rigging and video-audio/timeline decisions. Do not mark
the entire advanced-media assignment accepted/complete or dispatch a critic.
