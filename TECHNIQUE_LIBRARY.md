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
  Galaxy currently routes only its own structure target and remains held-only;
  a future compatible-effect extension must update that routing deliberately.
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
already implemented. Galaxy currently has four editable roles and no named family
entry; adding that support belongs to its active creative brief.

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

The eight ten-second nursery events remain renderer-owned. Main weight packing
supports a forced Galaxy handoff with musical warp depth, but eligibility and
Envelopers defaults remain unchanged. No Main approval is implied. Evidence:
[task notes](docs/agent-notes/galaxy-stellar-aviary.md),
[Studio instructions](DEVELOPMENT_STUDIO.md), `work/galaxy-journey-review/`.
