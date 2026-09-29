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
| Shader worlds/materials | `app/visuals/shaders/dream.frag` | Reuse coordinate/depth assumptions; do not erase structural geometry. |
| Audio features/mapping | `app/audio/` and `app/visuals/parameter_mapper.py` | Keep analysis separate from visual interpretation. |
| Player and portable builder | `app/player.py`, `build_portable.py` | Player is the product entry; builder creates new output only. |

## Review contracts

Search before adding a technique. Preserve opacity, continuous clocks, accepted
Authored visuals, and session IDs. Review a change in isolation and Main motion,
including quiet and sustained passages. For Cosmic and Elemental-specific
contracts, see [docs/MAINTENANCE_CONTRACTS.md](docs/MAINTENANCE_CONTRACTS.md).

Echo Weave is implemented and Main defaults to the material quartet; saved trio
profiles remain valid. Do not confuse this compatibility fact with a current
feature proposal. Potential palette, surface-treatment, and feedback work is
prioritized only in [ROADMAP.md](ROADMAP.md).

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

Roots established the first review gate. The active rollout now declares source
colors for applicable existing worlds, materials and details. Every target still
needs a bounded declaration, shader hook, compatibility check and visual review.

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
- Keep original shader expressions for absent targets. Overrides replace
  field-gradient pigment, tint named source pigments, or add a tint difference
  to existing ridge/blossom contributions. Preserve masks, lighting, audio
  response, geometry and composition. Explicit colors can change perceived
  contrast; this does not justify changing the shading pipeline.
- `Renderer.set_colors` validates before replacing state. Color uniforms upload
  only when settings/scope change, on the renderer thread. `targets_for` routes
  held forms, authored family cycles, sequential preview holds and Main by
  stable source ID. Shader hooks retain source masks; Roots/Membrane shade their
  separate forms through the authored form blend, including directed Main.
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

Verification for an extension: declaration/default validation, rejected updates,
old sessions, reset/revert/preset round trips, all supported preview routes, exact
or explicitly investigated authored pixel comparisons, unsupported-scene scope,
intended-region mask checks, and repeated edits with continuous clocks and stable
resources. Keep captured/synthetic/decoded/live audiovisual evidence distinct.
Existing entry points are `studio_test.py --roots-colors-test` and
`shader_test.py --roots-color-test <pre-edit-shader> <new-output-directory>`.

The rollout inventory, completed batches, evidence and remaining exceptions are
tracked in `docs/agent-notes/color-inspector-rollout.md`. Planet's explicit
object tints follow Soft Dream when both are selected. Echo's declared tints
apply at display stage and leave feedback history untouched. Spatial FX without
an independent pigment inherit their material colors.

Proposed standing policy for the Overseer (not an AGENTS.md change): future visual
features should expose meaningful editable colors through this mechanism where
applicable, preserve authored defaults/shading/music response, use stable IDs and
clear artistic names, document inapplicable or unsupported controls, and verify
through Dev Studio. Expose useful choices, not every computed shader expression.
