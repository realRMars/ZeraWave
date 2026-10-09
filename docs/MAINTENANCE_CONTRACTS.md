# Cosmic and Elemental maintenance contracts


## Focused Composition correction preservation — 2026-10-09

Preserve separate Select/Lasso/Magic Wand toolbar buttons and scissors Cut action;
do not restore a method dropdown, legacy Cutout workflow, local Composition Edit
menu or any Details widget/layout. Main application Edit remains. Canvas cursors
are distinct DPR-aware vectors, restored after temporary gestures; Ctrl+wheel is
2% versus ordinary15%, fractionally scaled, view-only. Existing navigation limits,
shared Main/Secondary, automatic Smudge and sidebar/docking contracts stay intact.

Layer deletion confirms exact text “Everything within layer will be deleted” with
Yes/No, defaultNo, validates the pinned scene/session/revision after confirmation
and removes the complete chosen closure once. Row context deletion excludes
unrelated selected rows; any protected member rejects all. Canvas Delete is still
a raster command. Preserve resources for history/readers and original files.

Retain identity-bound tree widgets across ordinary selection/refresh and refresh
thumbnails independently of pixel reader handles or unchanged order renumbering.
The global input filter handles only its actual mouse/key/focus/ChildPolished types.
Do not lower the existing32-row
or depth6 limits as a performance workaround. Preserve typing/focus and collapse.

Fill optimization must match source, pixels, inputs/tolerance/boundaries/caller and
separate worker/GUI/owner/output/PNG clocks. Optional zw_connected/zw_cancel keep
ABI1 layouts; protect exact pixels, bounds, cancellation, immutable snapshots and
stale-result rejection. Older exports/B1 retain compatibility. Build only to a
fresh OutputName; retain old DLLs and never switch resources in a running process.
Review/save/secure accepted work, close/reopen normally to use the new candidate.


This reference protects existing working behavior when maintaining or extending
shared code. It does not freeze all future art to current geometry or algorithms.
An assigned scene redesign can change that scene; preserve unaffected scenes,
saved data and shared systems. Current creative scope lives in
[ROADMAP.md](../ROADMAP.md) and [AGENTS.md](../AGENTS.md).

## B1 raster transaction preservation — candidate contract

The uncommitted B1 candidate implements immutable shared raster resources,
ordered asynchronous outcomes and background persistence in the retained Python
ControlOwner; no native core is introduced. Preserve world/audio/hosting contracts below, originals
and session migrations. Qt widgets stay on the GUI thread; GL resources belong
to the existing renderer context. Published snapshots cannot alias mutable gestures.

Bind document/session/target/revision/operation identity to pixels/history/output.
Accepted, applied/published, persisted, failed and unknown ACK are distinct. Retry
one ID without duplicate edits; late saves cannot replace newer work. Completed
operations/Undo/Redo keep order/scope. Failed saving cannot lose accepted unsaved
work or replace a valid project.

Exercise [B1 acceptance](../ROADMAP.md#b1-acceptance-plan): slow PNG writes, rapid
strokes, Undo/Redo during saving, layer/session switches, Save/Save As errors,
lost/delayed ACK/retries, exhausted resources, replacement/deletion/close. Include
actual pointer/keyboard and canvas/clean output. Preserve [tool/recovery meanings](STUDIO_MEDIA_COMPOSITION.md#b1-preservation-requirements)
and pixel/alpha/transform/group fixtures. Record input/accept/output/persist delays
and failures separately; GPU/paint-call timings alone do not pass interaction.

`raster_transactions_test.py` holds persistence, tests exactly-once admission,
recovery/save failures, capacity rejection and old-session checkpoint retention.
Existing `raster_workflow_test.py`, `raster_workflow_pixels_test.py`,
`composition_test.py`, `composition_canvas_test.py`, `media_recovery_test.py`,
`studio_editing_test.py` and `studio_media_test.py` protect the existing semantics.
Executed checks and failures belong in [B1 results](agent-notes/b1-raster-20261008.md),
not an inference from this list. Bound histories,
workers, storage/leases with explicit capacity failure and rollback/recovery.
C++ tiles/native build setup belong to later stages, not a B1 prerequisite.

Keep current/history/write/save/output pins alive until their consumers finish.
Do not mutate a published mapping or store pixels in JSON. Preserve exact descriptor
interpretation and Windows page-rounded mapping-capacity validation. Do not turn a
lost ACK into rejection, coalesce completed operations, or reinstall pixels from a
late durability callback. Save must retain its whole requested revision and Qt
metadata; failed export pins block closure until retry/recovery. See
[limits and user recovery](STUDIO_MEDIA_COMPOSITION.md#save-close-and-persistence-failure).

## B2 native tiles and incremental composition — planned checks

No C++ backend is implemented yet. B2 must preserve B1 transactions, exactly-once
history/outcomes, output independent of PNG, revision-pinned portable saves,
failed checkpoint recovery and close/session/source guards. Retain current/history/
save/output resource pins through tile eviction and backend shutdown. Capacity
failure cannot partially accept edits or destroy earlier accepted pixels.

Compare against current native-pixel/reference fixtures for alpha/masks/Smudge
halos, transformed Cut/Extract/Crop, partial opacity/strength and nested isolated
groups. Dirty-region invalidation must cover structural and transform changes.
Sustained edits/Undo/Redo, eviction/store exhaustion, delayed persistence, retries,
resize/restart/cleanup and unavailable DLL/fallback belong in
[ROADMAP B2](../ROADMAP.md#b2--c-tiled-raster-resources-copy-on-write-history-and-incremental-compositing).
Use real pointer/keyboard plus canvas/clean output. Bind matched B1/B2 workloads,
latency tails and separate CPU/GPU/staging allocations; no assumed speedup or
reduced resolution. Preserve existing CPU reference, tool semantics, original
assets and saved compatibility. These are acceptance requirements, not executed
checks or a declaration that B1's pending user review is complete.

## Planet Canvas and its existing Cosmic diagnostics

These contracts describe Planet Canvas and the existing Transition/diagnostic
callers of `isolated_cosmic_scene`. They do not prescribe Galaxy or future
Cosmic forms.

- The material field becomes planetary albedo; `isolated_cosmic_scene` owns
  planet/ring/moon depth. Compare actual depth, not screen position; keep
  projection, shared ring axes and system scale coherent when maintaining it.
- Moons replace covered scenery with opaque, normal/light-shaded material.
  Eclipse/night treatment belongs in lighting, not alpha. The opacity regression
  samples moon centers and far-side occlusion, not every limb or moon overlap.
- The existing surface uses bounded procedural disturbance. New scenes and
  assigned effects can use particles, geometry, feedback or other representations
  inside the working renderer. A scene brief can authorize these choices.
- Preserve existing sky/material defaults during unrelated work or color-only
  extensions. An assigned artistic change may deliberately redesign its target.
  For depth/projection changes, compare matching state/time/dimensions/input,
  then inspect motion as well as captures.

Relevant checks, when the changed paths warrant them, use a fresh destination:

```powershell
$review = "work/review/cosmic-$(Get-Date -Format yyyyMMdd-HHmmss)"
.\.venv\Scripts\python.exe app\visuals\moon_opacity_test.py
.\.venv\Scripts\python.exe app\visuals\shader_test.py --handoff-test "$review\handoff"
.\.venv\Scripts\python.exe app\visuals\shader_test.py --sweep "$review\sweep"
.\.venv\Scripts\python.exe app\visuals\shader_test.py --capture "$review\capture" --state canvas --seconds 18 --profile active
```

Historical evidence remains at `work/cosmic-handoff/sequence`,
`work/cosmic-handoff/sweep` and `work/cosmic-handoff/capture`; do not overwrite it.
The handoff and sweep tests cover particular timing/contrast/black-space
regressions, not every Cosmic scene or subjective motion quality.

## Existing Elemental forms

- Preserve structural depth and authored presentation in unaffected forms.
  Color-only controls should retain the target's shading and silhouettes.
  An assigned spatial effect or transformation may deliberately deform its
  target; define compatibility and inspect the resulting structure in motion.
- Water currently uses procedural surfaces. Fire/Aftershock have bounded
  lifecycles. These are implementation descriptions, not bans on developing
  richer simulation or other techniques for an assigned scene.
- Keep resource/state bounds and reproducible test inputs where applicable.
  Maintain the intended opaque/translucent behavior of unrelated surfaces.
- Preserve stable layer IDs and saved sessions. Check shared changes in their
  affected held forms and applicable Main transitions. A new held-only candidate
  can be reviewed without adding it to Main prematurely.

## Shared verification and audio boundaries

- Detect onsets from the intended normalized/smoothed bands before
  `VisualSignalConditioner` applies visual slew limiting, then carry onset values
  through `AudioFrame.impact`. Sustained level is not a fresh onset.
- Baseline checks protect explicitly sampled, unaffected behavior. Preserve the
  baseline and evidence path. Intended changes to a redesigned candidate require
  visual evaluation rather than equality with its former image.
- `app/visuals/shader_test.py --preservation-test <baseline>` compares sampled
  held-world pixels. World-specific modes with `before.frag` retain their own
  evidence scope. Neither proves natural live audio, artistic quality or general
  device compatibility.
- Run focused checks for the affected paths; broaden when shared changes create
  regression risk. Do not run every historical command after every small edit.

See the [Cosmic snapshot](history/2026-09-28-cosmic-development.md),
[Elemental snapshot](history/2026-09-28-elemental-development.md) and
[history index](history/README.md) for dated acceptance and evidence.

## Galaxy Odyssey: held and canonical Main

- Accepted Galaxy36 belongs to `LIVE_FORMS` and canonical Main. Preserve its
  74-second route on Main entry/return and route-boundary release. Earlier forced
  `world_uniforms({36: weight, ...})` fixtures are historical compatibility
  evidence, not an exclusion policy. Zero Galaxy weight must preserve unaffected
  scene contributions.
- Galaxy's visit clock progresses during visibility, parks elsewhere and resets
  on rewind. The musical star clock drives local orbital/material motion.
- `procedural_cosmos` uses versioned hierarchical identities and at most twelve
  cached immutable descriptors. Warp's next descriptor must equal arrival's
  current descriptor. Pure tests cover route joins and camera/solid separation.
- Local solar coordinates use the selected star's galaxy anchor and fixed scale;
  CPU/shader planet-position formulas must agree. Keep opaque body/ring depth,
  continuous camera exclusion and bounded shader loops.
- `stellar_sails`/`stellar.sails` are retained storage IDs for Ion Comets. Both
  comet and parallax layers keep explicit opt-in and amounts in compatible worlds.
  Galaxy Authored includes them; all three Envelopers stay off in Main.
- Source pigment roles are stable and append-only. Missing old-session roles
  fall back; defaults never overwrite manual entries, holds or stored cycles.
  New local materials/regions use generated inspector and live transport.
- Eight nursery events maximum, ten-second lifetime and 1.2-second trigger gate;
  rewind/leaving Galaxy clears them. Pigment edits do not clear history. No
  musical phrase/downbeat recognition or literal infinite universe is implied.
- Inspect short visits, scale bridges, planetary transfers and destination
  arrivals in motion. A previous quiet-camera pixel-speed ceiling does not define
  the new route; test continuous joins and bounded frame-change spikes instead.
- Main integration evidence: [Main lineup](../work/main-lineup-01/review-index.json)
  and [current handoff](../ZERAWAVE_HANDOFF.md). Earlier held evidence remains at
  `work/galaxy-journey-review/` and in [task notes](agent-notes/galaxy-stellar-aviary.md).
  Technical checks and the recorded user acceptance retain their own scope.

## Main Audio Tuning preservation

- Preserve authored values on load, preview, target switches and temporary profile
  changes. Only an explicit Save Authored promotes the acknowledged values to the
  named destination. Keep the backed-up Planet stores and separate DSP work intact.
- Keep form/target/role settings independent. Shared-technique instances retain
  their form owner; selected listening windows reuse existing FFT data and do not
  retune global normalization, pigments or unrelated clocks.
- Route commands, telemetry and saves by run/session/form/target/revision.
  Reject stale identities/revisions. A save requires a fresh matching ACK and
  settings digest; active listening ranges also require valid current input.
  Configuration ACKs for inactive targets do not imply visible contribution.
- Switching form/target or Follow/Pin cancels held keys, drag/debounce work and
  pending paint. Park unsent values at their original owner; an older ACK must
  not overwrite them or make them saveable before their own acknowledgement.
- Preserve outgoing/incoming endpoint ownership and distinguish director timing
  from visual transition inputs. Pair auditions require compatible Main forms
  and a repeatable source; reject matched live input before mutating playback.
  Repeat resets the same decoded passage and numerical FFT history; Return
  restores the parked source/CPU scene/RNG state. Shared Echo/Enveloper GPU
  history resets at the boundary rather than claiming pixel-identical recovery.
- Keep inactive/mode-inactive telemetry unavailable, and label CPU submissions,
  analyzer spectrum, proxies and selection weights separately from GPU pixels.
  Do not infer slider-by-slider visual coverage from the 595 target-row inventory.

See [Studio operation](../DEVELOPMENT_STUDIO.md#main-audio-tuning-and-mapping-monitor)
and [the rollout handoff](../ZERAWAVE_HANDOFF.md#current-main-audio-tuning-checkpoint)
for source identity, bounded evidence and remaining limits.


## Audio presentation and measured performance fixes

- Raw uniform inputs can resolve once per frame. Local GLSL aliases can include
  spatial attenuation, authored floors or listening descriptors: retain the
  local value and apply its resolved gain in the shader. Preserve gain==1,
  clamp and [-2,-1] encoded-input semantics independently for both endpoints.
- Initialize shared presentation clocks before a Fractal Main evaluator can
  read them. Scene wrappers restore audio context and its resolved shared values.
  Preserve Planet's independently owned clocks, histories and selected ranges.
- Cache configuration-derived targets/windows, not evolving signals. Pending
  edits and ACKs still apply when a target is inactive; monitor availability is
  refreshed at its existing snapshot cadence. Revisions invalidate existing
  selected-window processing through the established model.
- Program uniforms pruned by the driver retain their declared CPU state for
  auxiliary passes/audition restoration. Misspelled or undeclared names fail.
  Cache active uniform handles; never scan the program on every upload.
- Keep render targets lazy: one Cavern/Citadel target per contributing scene,
  zero when neither contributes, release on resize/exit. Main previews that can
  reach Cavern retain bounded row preparation to avoid a large entry rebuild;
  unrelated held previews skip it. Two row futures, 24 GPU rows, 64 cached CPU
  row recipes and the existing bounded ready window remain the limits.
- Capture queues bound image memory, drop on backlog and drain accepted work on
  normal shutdown. GL objects/readback remain on their graphics owner thread;
  statistics/PNG encoding run on the owned worker. Report failures and drops.
  Stream replay input telemetry to CSV; do not retain a track-length row list.
- Full quality uses the actual framebuffer. Explicit preview scales reduce both
  dimensions, upscale once and record internal/output dimensions. Do not silently
  adopt a scale, reduce density, or claim GPU query time as presentation FPS.
- Root branch preparation reuses the authored procedural equations in one fixed
  31×4 RGBA32F target (normal and independently owned Planet clock variants).
  Retain current Root gains, including encoded selected inputs, on every draw.
  Prepared VAO captures can edit uniforms directly: refresh geometry at that draw
  boundary and restore the exact caller framebuffer and viewport, including
  feedback and explicit-scale targets. Raw shader tools keep the procedural
  function. Renderer exit releases the fixed target; pixel resize does not
  recreate it or clear any scene history.

  Authored function structure is an extraction dependency: changing `root_network`
  or its extracted equations requires procedural/prepared parity verification,
  not just a successful shader compile. Preserve current uniform/gain semantics
  (including encoded selected inputs), independently owned endpoint/Planet clocks
  and refresh after direct uniform edits. Restore destination/viewport even when
  preparation raises; Root owns texture unit 14, so check binding collisions when
  adding stages. Release preparation resources before vertices/context/window.

- Sky cloud planes may skip noise only where their authored mask is provably zero:
  five noise octaves sum to at most 31/32, the smoothstep upper edge is at most
  1.684375, and squared cloud radius greater than 2 leaves a margin even with
  lobes down to -1/4. Balloon fabric skips only an exactly zero authored shell.
  Keep all visible equations, plane counts/order and soft edges. Both guarded
  bodies are derivative-free; adding implicit texture derivatives or changing
  noise/mask bounds requires revisiting the proof and matched GPU preservation.
  These guards add no resource, clock, gain, history or program-strategy owner.
  The [Roots/Sky batch](agent-notes/roots-sky-full-size-20261005.md) retains Full
  pixels and measured improvement; practical overlap and observed maximum-tail
  gates remain failed. Do not describe it as a full-size performance certificate.

October 5 independent review passed eight synthetic GPU Root contracts and sampled
Full-pixel preservation; it reused Builder lifecycle evidence. This is bounded
verification, not physical-control/save-load, all-world or continuous-motion proof.
Optical overlap keeps both complete endpoints for 0<phase<1; do not omit outgoing
work or reset history for speed. Include auxiliary passes in total GPU cost.
See [review identity and limits](../ZERAWAVE_HANDOFF.md#current-unpublished-full-size-qtrendering-candidate).

Relevant checks: `performance_fixes_test.py` (CPU or explicit GPU matrix),
`root_branches_test.py --output <fresh-folder>` (focused GPU/direct-draw contracts),
`studio_test.py`, `studio_audio_integration_test.py`,
`fractal_main_integration_test.py`, and existing scope/session/transition checks.
Use matched dimensions and the source-bound task evidence; no new test framework.

## Unified Studio hosting and display ownership

- `studio_workspace.py` extends the existing Studio, parameter/color/audio
  transports, renderer and launch paths. Diagnostic Studio remains independent
  of the opt-in workspace host. No second render engine or capture owner exists.
- Each root-owned `DockWindow` retains its body/widgets/controller while Tk
  manages/unmanages its floating wrapper. Detach the menubar before `wm forget`;
  reuse one menu model and bounded protocol callbacks. Plain-frame native
  reparenting across Tk toplevels loses text focus and is not this contract.
- The renderer's HWND is hosted by `window_host.NativeSurface`; only parent,
  native style and rectangle change. Validate native ownership, including the
  Windows venv launcher ancestry. Retain the same GLFW window, OpenGL context,
  programs, parameters and audio owner. Metadata is bounded and workspace-only.
- Resizing Enveloper feedback retains its three histories, index, validity and
  clocks using normalized texture resampling. `copy_framebuffer` alone copies
  an extent and does not scale the complete image. Allocate bounded replacements
  before releasing old targets; failure retains the old targets. Scene changes
  and established discontinuity resets keep their existing semantics.
- Tools keep unsent target drafts, pending submissions, scope/revision/ACK and
  authored destinations through layout operations. Layout does not send artistic
  resets or recreate controllers. Hidden/tabbed-out tools skip display work;
  visible consumers share the existing audio-view subscription and transport.
- Workspace display refresh is bounded at 200 ms; original command/ACK and
  coalescing paths retain their own cadence. Twelve bands reuse existing FFT
  data. PCM display copies at most 32 min/max pairs per existing analyzed block,
  with no additional FFT, capture or normalization. Live history retains at most
  192 pairs; file envelopes retain at most 2048 buckets and one worker/future plus
  one coalesced pending track, with bounded read chunks and cancellation.
- Layout v1 is separate from artistic session v1-v3. Bound file reads, clamp
  geometry to actual monitors and reset only layout. Do not import stale layout
  content into tuning, profile or palette storage. Close-panel means hide;
  application shutdown releases holds, its worker and its owned preview.
- Preserve text/native button bindings before application shortcuts; slider
  arrows invoke one owned handler. Release holds/repeats on focus, layout and
  teardown. Errors, save destinations and inactive scopes must remain reachable
  in compact views; full explanation text belongs in accessible help.
- `run_unified_studio.vbs` uses the existing pythonw environment; `.pyw` logs and
  supplies a visible startup-error path. Keep the explicit console diagnostic
  and all public standalone checks. Packaging remains a separately assigned task.

Relevant checks: `studio_workspace_test.py`, `preview_playback_test.py`,
`studio_audio_native_test.py`, `spectrum_ranges_test.py`, `studio_test.py`, and
source-bound real-time/native-input/GPU resize evidence. Mocked callbacks do not
establish native keyboard focus; short cycles do not certify multi-hour sessions.

## Qt Studio additions ownership — October 5

- `studio_scope.py` derives exact eligible descendants from the canonical catalog.
  Browsed row, committed scope and current output are distinct. Main descriptors
  never include Experimental IDs. The renderer validates the complete descriptor
  before using the existing Player roster and random director. Single-form BONK
  is disabled and its shortcut leaves clocks/history intact.
- Leaf double-click and context-menu Load share one action. Main direct loads
  retain source, pause, context and shared clocks; destination entry/history
  ownership is applied by the existing adapter on the next draw. Same active
  leaf does not restart. Separate Experimental resource routes remain isolated.
  Retain an enclosing committed category or adopt the nearest playable parent
  within that namespace; do not broaden to Main or promote Experimental forms.
- Lifecycle work is serial and coalesces a latest pending request. Run and
  destination revisions reject obsolete commands/replies and old color/numeric
  gestures; Main editing waits for renderer destination ACK. Scope changes park
  drafts, release holds, stop repeat/debounce work and retain explicit save rules.
  Momentary focus-release notifications never wait behind a lifecycle ACK.
- One active asynchronous resource collector lives in the control owner. Role
  counters identify native renderer PID and deduplicate PIDs; CPU uses one core,
  RAM means working set, and system/device counters have separate scope. Device
  identity must match GL_RENDERER uniquely, rather than assume adapter zero.
  Disabled/missing/stale values remain unavailable. Hidden display work stops;
  enabled renderer diagnostic consumers receive bounded owner samples through
  the existing run/serial pipe and retain history in Session Performance Reports.
- Swap-return timing is independent of GUI polling. The rolling window is bounded
  to 120 intervals. Optional `ZERAWAVE_SWAP_TRACE=1` retains at most 4096 CPU timing
  records for task evidence and adds no GPU query/readback/synchronization.
- Only Qt-hosted windows are created hidden. Observable stages remain run-bound;
  native PID/ancestry and parent verification precede attach ACK and first show.
  Cancellation rejects late attachment and reports pending cleanup truthfully.
  Standalone/legacy notice behavior stays separate. Close/retry retains owned
  cleanup and does not stop unrelated processes.
- `studio_chrome.py` changes styles/hit testing on the existing Qt HWND. Keep
  native thick-frame/system commands, accessible buttons, standard focused-button
  keyboard activation, saved geometry clamping and ADS floating docks. Maximize
  and fullscreen are separate. Chrome/layout must not recreate the GL context.
  API geometry tests do not establish physical dragging/snapping or monitor/DPI
  behavior; record those limits instead of claiming complete hardware coverage.

Focused checks: `studio_scope_test.py`, `preview_playback_test.py`, existing
`studio_qt_corrections_test.py`, plus task-owned serial native lifecycle, category,
Experimental route and matched Resources overhead evidence in
`work/studio-additions-20261005/`. Combined independent review remains separately
assigned through Prompter/Bob; these checks do not grant user acceptance.


## B2 native raster/editor continuation - 2026-10-08

The uncommitted B2 candidate retains128-pixel immutable C++ tiles, copy-on-write
history, exact region editing, B1 transactions, revision-pinned portable PNG saves
and the existing output publication path. The continuation corrects redundant
CPU presentation refresh, adds an optional exact float32 region kernel, and hosts
renderer-owned GPU projection/composition in the same Qt authoring Canvas.
Integer-aligned physical native pixels use GPU composition and damage; filtered,
rotated/fractional views retain exact Qt reference sampling with cached GPU display.
There is no mandatory display-loop readback. The Layers editor label distinguishes
these routes; `ZERAWAVE_EDITOR_GPU=cpu` selects the compatible CPU editor at open.
Native initialization failure also preserves a usable CPU Canvas.

This is a reviewable candidate, not Robert acceptance or a universal performance
claim. Latency, memory, failures and remaining limitations are bound in
`docs/agent-notes/b2-tiles-20261008.md` and `work/b2-completion-20261008`.
Build, ABI, resource bounds and secured fallback are in the
[B2 implementation contract](NATIVE_RASTER_B2.md).

## Earlier B2 usability extension — workflow requirements SUPERSEDED below

Optional `Pixels` masks store exact compressed 8-bit full-resolution coverage,
validated before admission, bounded to 120 KiB encoded per mask and the existing
256 KiB scene state. Regional mask reads share one implementation across Qt, native
strokes and renderer-owned output/editor projection. Optional `media.editor` size
metadata is owner-validated and pinned in ordinary session saves. Old scenes default
to empty presets; old crops keep their existing placement. New crop compensation
and child-placement changes form one management transaction. Named-source pickup
uses immutable gesture-pinned readers and bounded regions, leaving ControlOwner
authority, resource lifetime, exactly-once admission and failure recovery intact.
No native ABI/build or compulsory frame readback change. See the current operating
section in STUDIO_MEDIA_COMPOSITION.md and this pass’s source-bound actual results.

## Earlier four-correction extension — workflow requirements SUPERSEDED below

Details starts collapsed without disabling any live information source. All real
tool settings use the existing saved-layout dockable/floating color sidebar;
selection/refinement and saved-mask controls share it. No advanced popup remains.
Fill is click-based four-connected RGBA similarity by default (tolerance32), accepts
transparent seeds and uses the visibly chosen paint chip. Own/Group/selection
coverage constrains both traversal and exact feathered writes at native dimensions.
One changed fill follows existing drawing transactions/history/publication and PNG
durability. Typed transient work is bounded to existing8MP/8192 dimensions with a
30s computation guard; no saved-mask encoding limit is imposed. One worker request
is source/scene/target/selection/session/revision bound and cancellable. No native
ABI/build, history schema, output interface or saved-format change occurs.
Zoom-in/out magnifiers preserve factors/limits; legacy Zoom activation is removed.
See STUDIO_MEDIA_COMPOSITION.md and the dated B2 correction actual results for
fixtures, costs and unresolved limits. Automated checks do not grant acceptance.

## Selection, clipboard and automatic Smudge preservation — 2026-10-09

This later authorized correction supersedes previous named-source pickup,
per-tool Main, Cutout/confirmation/child shortcuts and Canvas-only drawing Undo
requirements. Preserve old stored masks/pieces and existing native/transaction
formats; no ordinary Cut/Delete operation may create a new removal mask or child.

`editor_pixels.py` owns transient selection/gesture and immutable OS clipboard
origin. Completed raster changes use existing `save_paint` and ControlOwner
transactions. Paste inserts an independent sibling above the active layer using
captured source-pixel world placement, with no destination mask/crop inheritance.
Clipboard token/hash invalidate origin on external replacement. Protected/capacity/
export failures preserve artwork/clipboard. Esc/click/Copy/Deselect add no history.
The existing History offers an editor sequence across drawing/management; scoped
APIs stay available, and new edits clear the redo branch. Internal managed immutable
PNG dependencies may share paths under distinct IDs; external paths remain unique.

Shared Main migration retains saved swatches/palettes and independent Secondary/
tool settings. Fill's algorithm/resources stay intact; shared color and selection
binding are the only Fill changes. Existing saved toolbar identity remains, with
full dock height, resize grip, width reflow and actual-overflow scrolling.

Automatic Smudge extends `cpu_projection.py` regional artwork sampling and reuses
ordering/isolation/blends, crop/masks and existing brush physics. Immutable scene/
frame pins plus evolving target preview prevent double-target feedback and stale
delivery. Unsupported visible frames and exhausted 4 MiB footprint /16 MiB sample
capacity reject explicitly; no whole viewport/world/checker pickup. Source pixels
remain unchanged and only the editable selected raster receives an operation.

Standalone checks: selection_clipboard_smudge_test, smudge_composite_test,
editor_corrections_test, editor_usability_test, raster_workflow_test,
studio_editing_test; publication/transactions/projection/resource checks cover
affected interfaces. Bind actual executed results and limits in the latest report;
Qt, native pixels and standalone GPU are distinct from physical user acceptance.
