# ZeraWave technique map

This document maps current code ownership and reuse boundaries. It is not a
backlog; see [ROADMAP.md](ROADMAP.md) for priorities.

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
| Capture/decoded telemetry | `app/visuals/preview_capture.py` | Bounded PNG/statistics worker; owner-thread readback; streamed CSV input rows, one pending mutable row. |
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
