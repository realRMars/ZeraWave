# Cosmic and Elemental maintenance contracts

This reference protects existing working behavior when maintaining or extending
shared code. It does not freeze all future art to current geometry or algorithms.
An assigned scene redesign can change that scene; preserve unaffected scenes,
saved data and shared systems. Current creative scope lives in
[ROADMAP.md](../ROADMAP.md) and [AGENTS.md](../AGENTS.md).

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
