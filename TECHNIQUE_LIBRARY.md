# ZeraWave technique map

This document maps current code ownership and reuse boundaries. It is not a
backlog; see [ROADMAP.md](ROADMAP.md) for priorities.

## Current editor ownership and approved migration boundary

| Current owner | Implemented responsibility |
| --- | --- |
| `studio_qt.py`, `studio_composition.py` | Qt widgets/input, private raster gestures, CPU composition preview and tools. |
| `studio_control_client.py`, `studio_control_service.py`, `composition.py` | Python command/ACK, authoritative composition/history and revision/session policy over the retained control process. |
| `raster_resources.py`, `studio_control_service.py` | Immutable shared raster leases, bounded owner admission/persistence, duplicate ledger and revision-pinned portable saves. |
| `artwork.py`, `media_registry.py` | Unchanged native raster algorithms and durable PNG/import validation; completed B1 pixel edits publish before background PNG work. |
| `image_layers.py`, `renderer.py` | Existing context-owned GPU composition/output; no second world renderer. |
| `media_frames.py`, `model_layer.py` | Bounded silent native codec frames and supported static meshes. |

Approved direction retains Qt/Python control and GPU rendering with a small C++
core in B2. B1 runtime snapshots/asynchronous outcomes are implemented in the
development review candidate; [actual results](docs/agent-notes/b1-raster-20261008.md)
do not establish user acceptance. B1 separates history/output acceptance from PNG persistence;
B2 implements experimental C++ tiled storage, copy-on-write history and
renderer-owned editor projection behind B1's transaction/save interfaces. See
[native ownership/setup](docs/NATIVE_RASTER_B2.md); its generated DLL remains local. Audio/media native work
follows separate stages. Module paths describe current ownership, not a language
ban. See [ROADMAP](ROADMAP.md#b1--raster-transactions-recovery-and-immediate-publication)
and [media contracts](docs/STUDIO_MEDIA_COMPOSITION.md#current-status-and-b1-boundary).

## Dated rendering inventory reference

[Full worldform rendering inventory, 2026-10-05](ZERAWAVE_WORLDFORM_RENDERING_INVENTORY_2026-10-05.md)
is an immutable historical snapshot: 30 canonical Main rows plus Experimental,
diagnostic and cycle availability, shared constraints, H/F/G evidence conditions,
Marsh history and four ranked proposals. It distinguishes Main33/34 from
Experimental39/40 and binds the reviewed Root and later Sky-guard source versions;
it does not identify loaded runtime bytes or award current performance acceptance.
Later Sky-guard measurements remain Builder evidence awaiting independent verification.
At recovery `0fb4c3f`, the local reference is 30,383 bytes; SHA-256
`dcd7c50c6bd259379e53f29c58dc6a95a8fbff176f611b00b3c469dce97e7678`.
Earlier manifests bind their own versions; this reference identity does not
reseal or replace dated technical evidence.
Preserve it byte-for-byte. Record later findings in separately dated evidence and
reconcile current guidance only through assigned scope; do not rewrite this snapshot
or promote its hypotheses to implemented techniques. ROADMAP remains the sole plan.

## Discovery

Run from the project root without opening Studio:

```powershell
.\.venv\Scripts\python.exe app/visuals/technique_library.py water_current
.\.venv\Scripts\python.exe app/visuals/technique_library.py "feedback" --json
```

Studio > Library searches catalogued worlds/effects. The command searches current
Python and GLSL definitions; no result is not proof of absence.

## Ownership

| Need | Owner | Boundary |
| --- | --- | --- |
| World/form navigation and sessions | `app/visuals/studio.py` | Stable selection paths and versioned sessions. |
| Effects, material profiles, compatibility | `app/visuals/preview_layers.py` | Preserve IDs/order and saved-profile support. |
| Beat estimation and Main world choice | `app/audio/beat_tracker.py:BeatTracker.update_flux`; `app/visuals/renderer.py:update_blend` | Approximate spectral periodicity/tempo and confidence; qualified transitions may wait up to 0.8 s for a confident tick. No downbeat, phrase, or chorus recognition. |
| Deterministic fixture itinerary | `app/visuals/renderer.py:blend_chapter` | Shader-test fixture only; never document it as live Main behavior. |
| Echo Weave lifetime/resources | `app/visuals/renderer.py:update_echo` and `shaders/echo_weave.frag` | Fourth material; bounded history buffers and reset behavior. |
| Shader worlds/materials | `app/visuals/shaders/dream.frag` | Preserve unaffected callers; new scenes may define their own coordinates, geometry and composition. |
| Final-image Envelopers | `app/visuals/envelopers.py`, `shaders/envelopers.frag` | Existing additional-pass/resource pattern; off in Main pending artistic redesign. |
| Audio features/mapping | `app/audio/` and `app/visuals/parameter_mapper.py` | Keep analysis separate from visual interpretation. |
| Audio Tuning declarations and routing | `app/visuals/audio_controls.py`, `audio_scope.py`, `form_audio_tuning.py`, `studio_audio.py` | Independent form/target/role consumers; run/session/revision ownership. |
| Audio Tuning UI, profiles and monitor | `app/visuals/starfield_tuning.py`, `star_tuning_profiles.py`, `planet_mapping_monitor.py` | Reuse the existing dialog and pipes; explicit authored saves and CPU telemetry. |
| Matched pair audition | `app/visuals/studio_audition.py`, `replay_test.py` | Same preview process; decoded source restoration and explicit shared-history resets. |
| Per-frame audio presentation | `app/visuals/resolved_audio.py:AudioUniformContract` | Resolve uniform-only inputs/encoded values on CPU; retain gains for spatially varying local inputs. Preserve endpoint and Planet ownership; hoist water ingredients outside intersection loops. |
| Integrated program preparation | `app/visuals/prepared_program.py:PreparedProgram` | One program and VAO; cached active uniform handles, retained pruned declarations, NVIDIA measured compiler policy and first-use prewarm. No scene-entry family compilation. |
| Frame-dependent Root branch geometry | `app/visuals/renderer.py:RootBranchStage` | Authored `dream.frag::root_network` equations prepare a fixed 31×4 RGBA32F target with separate normal/Planet clocks. Full-pixel distance, derivatives and shading remain in Main. Prepared VAO draws refresh geometry after uniform edits and restore the caller's framebuffer/viewport; raw shader tools retain the original procedural function. Independent review corroborates sampled gains and eight GPU contracts; overall full-size candidate remains PARTIAL. Extraction depends on authored function structure: source edits require procedural/prepared parity verification. See the [review checkpoint](ZERAWAVE_HANDOFF.md#current-unpublished-full-size-qtrendering-candidate) and [maintenance coupling](docs/MAINTENANCE_CONTRACTS.md#audio-presentation-and-measured-performance-fixes). |
| Capture/decoded telemetry | `app/visuals/preview_capture.py` | Bounded PNG/statistics worker; owner-thread readback; streamed CSV input rows, one pending mutable row. |
| Sky zero-coverage guards | `app/visuals/shaders/dream.frag:audio_owned_air_scene` | Skip cloud noise outside a conservative proven zero-mask radius and balloon fabric outside its authored soft shell. Visible equations, all depth planes, pigments and live endpoint clocks remain. The cloud bound depends on five-octave noise in [0,1]; guarded bodies must remain derivative-free. Full Roots/Sky measurements show worthwhile gains, while practical transition and observed strict-maximum gates still fail. See [scoped evidence](docs/agent-notes/roots-sky-full-size-20261005.md). |
| Explicit preview render scale | `app/visuals/render_scale.py:ScaledContext` | Full quality bypasses extra targets; opt-in 75%/50% RGBA16F final upscale. Existing renderer and stage ownership, resize/release, no adaptive switching. |
| Player and portable builder | `app/player.py`, `build_portable.py` | Player is the product entry; builder creates new output only. |

## Review contracts

Search before adding a technique and extend the existing catalog/renderer.
An assigned scene can add original assets, geometry, camera behavior, shader
helpers, materials, spatial effects, new effect classes and bounded render passes.
Reusable techniques should have meaningful catalog entries, compatibility and
Studio controls; an extra stage does not automatically require a new architecture.

Preserve unaffected authored scenes, saved IDs and resource lifecycles. A requested
redesign intentionally changes its candidate's appearance. Review that scene in
motion and check applicable shared/Main paths without prematurely integrating it.
See [maintenance contracts](docs/MAINTENANCE_CONTRACTS.md) for existing form-specific
boundaries; they are not universal limits on new scenes.

Main's authored show uses seven materials: Living Artifacts, Liquid Alloy,
Prismatic Lattice, Echo Weave, Ink Archipelago, Interference Silk and Cellular
Mosaic. Older trio/quartet profiles remain valid. Three new spatial treatments
are integrated; the three Envelopers are currently off by default.

Current priorities live in [ROADMAP.md](ROADMAP.md). Supporting palette,
surface-treatment and feedback techniques can be built within an assigned scene;
they do not need separate backlog approval.



## Rendering references and untested options

Prompter research, reconciled after the October 5 independent review. This is a
compact reference set, not another plan or implemented-capability claim. The
project uses ModernGL 5.12.0, GLFW's requested OpenGL 3.3 and hardware OpenGL in
the recorded runs; the current Main program is integrated and prewarmed.
Raising the context requirement is not evidence that existing math becomes cheaper.

| Reference / transferable principle | Project application and limits |
| --- | --- |
| [ModernGL context version requirements](https://moderngl.readthedocs.io/en/latest/topics/context.html#require-a-minimum-opengl-version), [texture](https://moderngl.readthedocs.io/en/latest/reference/context.html#moderngl.Context.texture) and [framebuffer](https://moderngl.readthedocs.io/en/latest/reference/context.html#moderngl.Context.framebuffer) APIs | Existing API supports floating-point preparation/render targets. No new API/SDK is demonstrated necessary. |
| [NVIDIA GPU Gems 2 ch35, sections 35.2.1-35.2.2](https://developer.nvidia.com/gpugems/gpugems2/part-iv-general-purpose-computation-gpus-primer/chapter-35-gpu-program-optimization) | Reduce computational frequency: prepare proven frame/object invariants rather than recalculate per pixel. Root is the verified project example. Further exact-equation hoists/dependency pruning are untested; preserve evolving inputs, gains, endpoint clocks and derivatives. Old vector-instruction advice is hardware-specific, not direct RTX 3070 guidance. |
| [MJP shader permutations part 1](https://therealmjp.github.io/posts/shader-permutations-part1/) and [part 2, work split across passes](https://therealmjp.github.io/posts/shader-permutations-part2/) | Bounded specialization may trade simpler generated code for compile time, memory and maintenance. One matched endpoint/pair diagnostic is a proposal, not proven benefit. Production strategy needs reviewed variant bounds, fallback, uniform ownership, prewarm and lifetime contracts. |
| [NVIDIA Advanced API Performance: General shaders](https://developer.nvidia.com/blog/advanced-api-performance-shaders/) | Register use/control flow are useful profiling questions. Other-form gains do not prove spilling or direct Root execution. HLSL/D3D flags and vendor advice are not GLSL instructions to copy. |
| [Khronos ARB_timer_query, Overview and Example 1](https://registry.khronos.org/OpenGL/extensions/ARB/ARB_timer_query.txt), [ModernGL Query](https://moderngl.readthedocs.io/en/latest/reference/query.html) | Include complete GPU passes, disclose query-read waits and compare instrumentation with ordinary playback. A fixed delay does not establish readiness; ModernGL's documented Query API supplies no readiness property. Reused bounded query pools/delayed supported collection remain diagnostic proposals; do not invent bindings or add glFinish as a remedy. |
| [Hart, distance bounds and ray intersection, sections 2.1-2.2](https://graphics.stanford.edu/courses/cs348b-20-spring-content/uploads/hart.pdf#page=9) | Conservative distance bounds support correct traversal under deformation. This is mathematical guidance, not a modern-GPU speed claim. Compare analytic intersections, rasterized/instanced geometry and bounded distance tracing on one representative object; none is automatically faster or visually equivalent. |

Representation proposals should retain silhouettes, normals, softness, deformation,
occlusion and editable authored pigments. Lookup textures can replace stable bounded
functions only after checking interpolation/precision/aliasing and bandwidth.
Keep resident resources bounded and measure creation/upload/release at boundaries;
asset count, atlases or cooking are not established warm-draw remedies here.

Begin a selected experiment with hypothesis, identical Full-pixel state, measured
owner, rejection condition and preservation checks. Measure held, overlap and
arrival separately, total GPU including preparation, ordinary presentation, tails,
memory and compilation. Inspect normal-time motion; a solo budget does not certify
a transition budget. Do not reduce artistic detail or pixels to claim equivalent gain.

A split optical compositor is conditional on demonstrated specialization benefit:
two 1944x986 RGBA32F endpoint targets alone cost about 58.5 MiB. It still shades both
live endpoints and adds writes/composition; preserve tonemap/color-space order,
warps, derivatives, audio/history ownership. It is untested and does not establish
compatibility with every spatial transition. The rejected ~6.5% Spires projection
hoist remains negative evidence. Current priorities stay in [ROADMAP](ROADMAP.md).

These references are linked summaries, with no imported sample code, guide chapters
or asset collections. ModernGL's inspected package metadata is MIT; publicly readable
papers/guides do not confer blanket reuse rights. Check individual licenses before
any later code/asset reuse.

## Maintenance details

- **Onset ordering:** detect per-band onsets from the intended normalized/smoothed
  band signal **before** `VisualSignalConditioner` applies visual slew limiting.
  Then carry those onset values into `AudioFrame.impact` and visual mapping.
  Onsets are fresh changes, not sustained levels; preserve this ordering when
  altering analysis or event consumers.
- **Layer compatibility:** `EFFECTS` IDs and the 31 occupied positive mask bits
  are compatibility data. Do not reorder them. New groups that cannot use the
  mask require the existing explicit-uniform pattern and session validation.
- **Echo Weave:** `Renderer.update_echo` owns two 512×512 half-float history
  textures, fixed 60 Hz stepping, and resource release. It clears on backward
  time or a gap over one second, stays warm while selected, and releases when
  disabled and no longer kept alive. Use moving replay or
  `shader_test.py --echo-test <output>`; a one-frame capture cannot validate it.
- **Baseline comparisons:** when a verification mode takes a baseline shader,
  use the identified accepted baseline and compare identical state, time,
  dimensions, and audio profile. A baseline comparison protects only the cases
  it samples; it does not establish subjective motion quality or live-audio
  behavior.

The current Cosmic/Elemental boundaries and concrete evidence paths are in
[maintenance contracts](docs/MAINTENANCE_CONTRACTS.md); detailed accepted
records remain in [dated history](docs/history/README.md).

## Main Audio Tuning ownership and reuse

The published October 4 rollout covered 27 Main forms; the current accepted
development checkpoint includes the 30-form roster and Fractal declarations.
Unpromoted Experimental/Cymatics remain excluded. `audio_controls.py` declares actual consumer code, input,
bounds and role meaning for each form/target; `form_audio_tuning.py` owns
independent settings and packed inputs. Shared techniques get form-owned
instances, not copies of saved Planet numbers. Planet retains its star,
artifact and `planet_audio_tuning.py` adapters and authored destinations.

`studio_audio.py` resolves endpoint ownership, availability and submissions
through the existing renderer. Consumers include dream/Original Loop and
surface shaders, renderer clocks/director, Echo and Enveloper stages. Declared
gains or selected-bin substitutions reach those consumers; quiet bases,
pigments, time-only lifecycles and documented coupled carriers keep their owners.
Existing FFT output feeds `form_audio_tuning.py` and `app/audio/spectral_listening.py`;
selected windows add no second FFT or capture pipeline.

`audio_scope.py` and `studio_color_link.py` bind commands/ACKs to
run/session/form/target/revision. `starfield_tuning.py` extends the existing
dialog with Follow/Pin and parked editing; `star_tuning_profiles.py` owns
target-local profiles and explicit atomic authored saves. The Mapping monitor
reports analyzer input, CPU submissions and labelled display proxies, not
measured shader pixels. `studio_audition.py` preserves CPU/source state and
resets shared GPU history on Repeat/Return instead of copying GPU resources.

See [operating controls](DEVELOPMENT_STUDIO.md#main-audio-tuning-and-mapping-monitor),
[current checkpoint and limits](ZERAWAVE_HANDOFF.md#current-main-audio-tuning-checkpoint)
and the [consumer inventory](work/studio-audio-rollout-01/consumer-inventory.json).
The 595 inventory rows are selectable targets, not independent GPU-certified
sliders. Reuse these owners and expose only controls with actual consumers.

## Verification entry points

Use the production scripts under `app/visuals/` with the project `.venv`:
`studio_test.py` for Studio/session behavior, `shader_test.py` for deterministic
GPU captures, `replay_test.py` for decoded-track replay, and
`live_visual_test.py` for real system audio. Distinguish these scopes in reports.

## Declared live color controls — extension pattern

Roots established the first inspector implementation; the existing-world rollout
is complete. New visuals extend the same declarations, shader hooks, compatibility
and Studio controls. Give a new scene a deliberate authored palette and expose
meaningful artistic roles from the beginning.

- `app/visuals/color_controls.py` owns immutable `ColorTarget` / `ColorSlot`
  declarations, validation, preset/session data, authored defaults and uniform
  values. These describe color support only; reuse `EFFECTS`, `MATERIALS` and
  existing state IDs rather than adding another world/effect catalog.
- Target and role IDs are stable storage contracts, independent of labels.
  `color` is a fixed tint; `roles` is a bounded set of named source pigments;
  `staged_gradient` represents Roots/Membrane's five fixed colors and four
  overlapping smoothstep ranges. It is not an arbitrary variable-length
  gradient. No add/remove affordance is appropriate for these roles.
- Declarations contain scene compatibility, artistic labels, control type,
  uniform prefix, named slots, exact authored RGB defaults, transition defaults
  and a scope note. The generated inspector (`color_inspector.py`) uses these;
  it does not contain Roots-specific lists of fields. Extend control types only
  when a real effect needs different semantics. Future variable gradients need
  explicit validated limits, not an unbounded collection masquerading as slots.
- JSON stores only explicit overrides as `target -> role -> {color, start, end}`;
  color is `#RRGGBB`, and positions apply only to declared gradient roles. Missing
  values use authored defaults. Unknown IDs, malformed colors, nonfinite/range
  errors and reversed transitions are rejected transactionally. UI swatches
  round authored float RGB to hex for display; an untouched field does not write
  this rounding back into the authored shader path.
- For color-only extensions, retain authored expressions for absent overrides.
  Override the meaningful source pigment while preserving shading, masks,
  geometry, musical response and composition. Existing Roots controls use
  gradient pigment or tint differences within the original contributions.
  This contract concerns live color edits; a scene redesign may change its
  lighting, geometry or composition as part of the authorized visual work.
- `Renderer.set_colors` validates before replacing state. Color uniforms upload
  only when settings/scope change, on the renderer thread. `targets_for` routes
  held forms, authored family cycles, sequential preview holds and Main by
  stable source ID. Shader hooks retain source masks; Roots/Membrane shade their
  separate forms through the authored form blend, including directed Main.
  Galaxy routes its structure/solar targets plus compatible comet/star pigments;
  Main includes those targets. Extend compatible-effect routing deliberately.
- `studio_color_link.py` uses existing child stdin/stdout pipes: newline JSON,
  monotonically numbered complete snapshots, a 16 KiB bound, one pending update
  and one acknowledgement record. Tk coalesces at a bounded 75 ms cadence (continuous dragging still sends); background threads handle
  pipe IO; the child reader validates into a one-slot mailbox. Rendering consumes
  it in memory and acknowledges after drawing. No per-frame disk access, network
  service, GL calls from the reader, or new audio pipeline is involved.
- Preview manifests record launch settings. The normal run log includes revision
  acknowledgements and visual/Echo clocks. Studio owns and closes each link with
  its exact child; restart creates a fresh link and revert snapshot. A live edit
  does not reset time or stateful history. Dynamic edits persist only on explicit
  session/preset save, not by rewriting the launch manifest or loaded preset.
- A named color preset has kind `zerawave-color-preset`, version 1, name, scene,
  and target assignments. It is distinct from Planet's palette choice and from
  a full Studio session. Loading applies a copy; it never edits another preset.

Select verification to match the extension: declaration validation, reset/preset/
session behavior and visible target changes for new controls; broader routing,
repeated-update/resource and entry-path checks for transport or shared changes.
Compare unaffected authored paths against an identified baseline. Review intended
art changes in motion. Keep synthetic/decoded/controlled-live/natural-listening
evidence distinct; run broad suites when justified, not after every slider label.

Existing focused entry points include `studio_test.py --roots-colors-test` and
`shader_test.py --roots-color-test <pre-edit-shader> <new-output-directory>`.
Use the target-appropriate modes for other scenes.

The rollout inventory, completed batches, evidence and remaining exceptions are
tracked in `docs/agent-notes/color-inspector-rollout.md`. Planet's explicit
object tints follow Soft Dream when both are selected. Echo's declared tints
apply at display stage and leave feedback history untouched. Spatial FX without
an independent pigment inherit their material colors.

## Palette families and future effects

`color_controls.py:PALETTE_FAMILIES` and `family_setup` currently provide named,
target-specific role sets for the nine treatments. Family size must match the
target's declared roles. This is an extension point, not universal palette sharing
already implemented. Galaxy has six structure roles, eight solar-material roles
and named target-specific families, described below.

Extend existing Hold/Cycle, stored setup and manual-edit precedence for new
applicable targets. For cross-world reuse, define meaningful role mapping and
compatibility; do not silently apply a palette of mismatched size or semantics.
Keep old target IDs and saved files valid. If a new visual requires different
gradient or collection semantics, add the validated control type it needs.

The standing rule is [AGENTS.md section 17](AGENTS.md#17-editable-artistic-colors).
Expose useful artistic choices through the existing inspector and document
genuine exceptions. Spatial effects without independent pigment can inherit
their source material colors.

## Galaxy Odyssey components

`procedural_cosmos.py` owns versioned hierarchical seeds, immutable galaxy/system/
planet descriptors, a bounded 12-entry cache, random-access routes and a shared
selected-star anchor across scale changes. It has no renderer/audio dependency.
Future assigned worlds can reuse those techniques without another playback engine.

The existing shader owns seven absorbing/emitting strata (`journey_galaxy`),
analytic sphere/ring depth (`journey_system`), locally authored terrain/cloud
materials (`journey_surface`), and colorful destination passage (`journey_warp`).
Library indexes these techniques and their source functions. Generated planets
rotate/orbit, have opaque light/shadow, atmosphere rims, ring gaps/shadows and
moons. Cameras survey, approach, bank around selected worlds and turn toward a
seeded next galaxy. The arrival uses that same descriptor in the following cycle.

Ion Comets and Parallax Shoal are actual reusable Sky effects with amounts in
Galaxy/Cosmic/Fog/Plasma. Comets replace the previous birdlike geometry but keep
`stellar_sails` and `stellar.sails` IDs. Other worlds remain explicit opt-in.
No extra mask bits, graphics resources, playback engine or dependency is added.

Six Galaxy structure roles and eight solar material roles complement existing
comet/star pigments. Copper Comet, Orchid Eclipse and Verdigris Dawn remain;
Living Atlas, Ember Archipelago and Opal Frontier add solar role families. Missing
roles use authored values; manual assignments and Hold/Cycle take precedence over
transient defaults. Local drift/rotation/generated regional distributions provide
visible evolution without synchronized automatic palette cycles.

The eight ten-second nursery events remain renderer-owned. Galaxy36 is accepted
and included in canonical Main. Each Main entry/return begins its full 74-second
route and becomes releasable at the route boundary; weight packing supports
compatible handoffs. The three Envelopers remain off by default.
Current integration evidence is in the [Main lineup](work/main-lineup-01/review-index.json)
and [handoff](ZERAWAVE_HANDOFF.md). Earlier held/forced-handoff evidence remains in
[task notes](docs/agent-notes/galaxy-stellar-aviary.md) and `work/galaxy-journey-review/`.


## Fractal ownership

`app/visuals/fractals.py` owns bounded form clocks and scoped submissions;
`app/visuals/shaders/fractals.frag` owns the three presentations. Renderer incorporates the original Fractal functions into the existing Main
program through `integrated_shader`, with one endpoint evaluator and window/resource
lifecycle. `submit_main` owns bounded per-form clock and material submission.
`development_forms.py` retains inspection declarations; forms 41-43 now also belong
to `LIVE_FORMS`, canonical playlists and player selection under Fractal.

- **Mineral Lamellae** (`mineral_lamellae` / shader `lamellae`): contour etching
  and fine glints, reused on landscape rock, recursive architecture and petals.
  Three shared artistic pigments, per-form Flux/Sparkle gains and amount.
- **Recursive Pulse** (`recursive_pulse`): three bounded local wave scales,
  reused on all three forms; per-form Flux/Impact gains and amount. It inherits
  material pigments and has no independent color-bearing output.

Compatibility uses explicit treatment uniforms, preserving the existing 31 mask
bits. Profile worlds and target/role IDs are additive. Manual colors never reset
clocks/history; Main's authored targets and values are unaffected.


Branching Iris (`tr_branch_iris`) and Flowing Fold (`tr_flow_fold`) extend
`dream.frag::main_region` and `main_carry`. Stable recipes apply to any two distinct
Main forms (including Fractal), use their existing endpoint geometry/pigments, and
have independent Bass/Flux/Movement/Impact consumers in
`u_structural_transition_audio`. Selected-band measurements pass through the existing
scoped audio model; duration is a separately labelled CPU timer. No new pigment,
persistent buffer, simulation or rendering engine is introduced by these transitions.

## Unified Studio reusable presentation components

These are UI/presentation techniques, not new scene effects or Main admissions.

- `studio_panels.py`: one root-owned panel body, supported Tk floating wrappers,
  movable Notebook tabs, seven resizable docking areas, visibility and separate
  layout persistence. Detach native menus before discarding wrappers; retain
  controller, draft and ACK ownership. Geometry clamps against actual monitors.
- `window_host.py`: opt-in Windows hosting for the existing GLFW HWND, verified
  PID/venv ancestry, system DPI awareness and cached native rectangle updates.
  No context recreation, additional renderer or frame-readback transport.
- `studio_compact.py`: compact views over the existing Color Inspector, Follow/Pin
  tuning and read-only mapping monitor, with complete original controls in tabs,
  scrolling and accessible help. Authored pigment roles and scope IDs stay owned
  by the existing declarations; explicit compatible target selection is retained.
- `studio_meters.py`: one cancellable decoded-PCM envelope worker, bounded live
  PCM snapshots and exactly twelve existing FFT bands with actual edges, units,
  under-resolution and unavailable indicators. No alternate audio analysis.
- `envelopers.py::EnveloperStage.resize`: bounded resampling preserves feedback
  across viewport changes. Existing history clock/state/reset boundaries and
  authored Enveloper appearance remain renderer-owned.

The unified shell composes these components over `Studio`; it adds no artistic
palette families or effect classes. Existing generated pigments, named presets,
profiles and sessions remain the reusable creative library.

October 5 Qt additions extend presentation over those same owners:

- `studio_scope.py`: canonical descendant scopes and nearest-parent direct-load
  destinations, independent of browsed rows and current output. Existing Player
  randomness/transitions remain the playback technique; Experimental routes stay
  isolated and never become Main by matching a display name.
- `studio_resources.py` / `session_performance.py::ResourceSampler`: read-only
  formatting and a shared asynchronous role/PID collector with identified device
  scope, honest freshness and bounded history. Enabled renderer diagnostics reuse
  owner samples through the existing control pipe; no device query is added to
  drawing. Swap-return rate is not GPU draw time or measured scanout.
- `studio_qt.py` / `studio_chrome.py`: ADS layout, inline run-bound startup and one
  client header over the existing native Qt/GLFW handles. Resource-incompatible
  leaves use the existing owned lifecycle; compatible Main loads retain clocks,
  context and audio position. Native move/resize initiation and system commands
  are implementation paths; physical drag/snap, DPI and monitor changes remain
  unverified in the additions evidence.


## B2 native raster/editor continuation - 2026-10-08

The B2 development candidate retains128-pixel immutable C++ tiles, copy-on-write
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
[B2 implementation contract](docs/NATIVE_RASTER_B2.md).
