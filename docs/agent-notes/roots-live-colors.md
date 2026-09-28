# Live Roots color editing — Bob / Engine room

Completed 2026-09-28 for user artistic review. Roots is the first reviewed scope;
no cross-world/material expansion is implemented.

## Owned files

New modules: `app/visuals/color_controls.py` (immutable declarations, validation,
lookup, uniforms and preset schema), `color_inspector.py` (generated modeless Tk
inspector), `studio_color_link.py` (bounded local pipe transport).

Extended existing files: `app/visuals/studio.py`, `renderer.py`,
`shaders/dream.frag`, `shader_test.py`, `replay_test.py`, `live_visual_test.py`,
`studio_test.py`, `DEVELOPMENT_STUDIO.md`, `TECHNIQUE_LIBRARY.md`, and this note.
Existing uncommitted work was preserved. The pre-edit shader/code snapshot is in
`work/roots-colors-20260928-024736/`. No shared planning/policy edits, commit,
portable build, cleanup or new dependencies.

## Result

- Four declared targets: blue field gradient, pearl field gradient, ridge tint,
  and shared blossom petals/center tint. Gradients retain five fixed roles and
  the actual four overlapping smoothstep intervals. No invented tip/petal/glow
  separation, arbitrary material recoloring or variable gradient collection.
- Authored shader expressions remain explicit. Missing fields use exact authored
  floats; merely displaying hex does not write rounded defaults back. Color
  hooks preserve geometry/masks, lighting multipliers, music response and blossom
  lifecycle. Custom material effects retain their own colors/composition.
- Inspector: target/role selection, swatches, hex entry, hue/saturation wheel,
  brightness/value, fixed gradient colors/ranges, reset target/scene, revert to
  current preview start, named target-assignment preset save/load.
- Live held Roots only, across all existing input paths. Standard local child
  pipes, 16 KiB messages, one pending snapshot, 75 ms coalescing cadence, render
  thread application and post-draw acknowledgements. Continuous dragging sends
  updates during the gesture. No disk polling or additional renderer/audio path.
- Old sessions preserve appearance. Optional `color_overrides` persists in v3
  sessions; named color presets use their own small v1 target-assignment schema.
  Editing/loading is in memory until an explicit save; preset files are not
  silently rewritten. Unsupported scene selections park overrides.
- The Planet palette/A-B workflow is retained. A small lifecycle correction sets
  GLFW nonresizability after renderer creation for comparison windows; its old
  pre-create hint was overridden by Renderer.create.

## Executed checks and evidence

1. Full Studio suite PASS: `.venv/Scripts/python.exe -X utf8
   app/visuals/studio_test.py`. Log `work/roots-color-full-studio-check.log`.
   Includes existing old-session, mixed-cycle, material isolation, Main defaults,
   Planet palette routing and actual sequential A/B child checks.
2. Final focused Roots suite PASS after label/cadence refinements:
   `studio_test.py --roots-colors-test`; log
   `work/roots-color-final-workflow-check.log`; artifacts
   `work/roots-color-studio-check/20260928-031040/`.
   Exercises declarations/rejected inputs, real bounded OS-pipe framing,
   malformed/oversize/stale updates, generated controls, reset/revert/presets,
   session compatibility, actual synthetic child updates and stop/restart,
   actual four-second decoded-track child updates and natural EOF cleanup.
   Controlled-sample live-audio entry point reached real GPU uniforms; this was
   not loopback listening. A burst of 100 changes coalesced to one snapshot;
   continuous gestures also delivered while editing.
3. GPU suite PASS: `shader_test.py --roots-color-test
   work/roots-colors-20260928-024736/authored-before.frag
   work/roots-color-gpu-check`. Log `work/roots-color-gpu-check.log`, JSON report
   and authored/edited captures in `work/roots-color-gpu-check/`.
   Exact authored baseline pixels across 36 states; overrides do not affect
   other states or sequenced Roots. Geometry/lifecycle masks identical. Blossom
   and ridge changes leave pixels outside their masks unchanged. Disabled
   blossoms stay disabled under all four materials. Reset restores authored
   pixels. 240 repeated edits preserve GL resource identities and advance clocks
   and Echo history; invalid renderer input retains the last valid setup.
4. Observed performance at 480x270 on the RTX 3070 Laptop GPU: median color
   validation about 0.058 ms under tracemalloc; median measured GPU render about
   0.441 ms including Echo in the scripted stress case. Retained Python memory
   delta was 15,488 bytes, including measurement lists; no GL resource growth.
   These are bounded test measurements, not live FPS or larger-resolution claims.
5. Real UI walkthrough: selected held Roots, launched synthetic animation,
   opened the inspector from Palettes, changed a gradient role with the wheel,
   saw the applied-live acknowledgement, viewed the render and reverted to
   preview-start colors without restart. Viewed generated GPU capture too.
   This is interactive/synthetic inspection, not continuous audiovisual review.
6. `git diff --check`: PASS. Existing line-ending conversion notices in other
   workers' files are not whitespace failures. Working tree remains uncommitted.

Two initial checks needed correction before passing: the first shader form
produced a one-level difference in one Membrane RGB channel; keeping the authored
expressions explicit removed it. The resource assertion initially assumed Echo's
ping-pong textures keep their order; it now checks stable identities independent
of their intentional swaps. No unresolved check failures remain.

## Limits and next review gate

Blossoms can be absent at preview start because their existing slow lifecycle
remains intact. Their tint does not force a bloom or enable the detail layer.
Field gradients also affect the dim surrounding field; positions are shading
value intervals, not branch-length positions. Final tonemapping and musical
response still influence perceived color/contrast. No actual continuous live
music listening review or artistic acceptance was performed.

Use DEVELOPMENT_STUDIO.md for exact opening/edit/reset/revert/preset steps.
Stop at user review. Likely later targets and different requirements are in the
technical guide: Membrane reuses these gradients but needs separately reviewed
scope; Planet object tints must respect material pigment and lighting; stateful
feedback colors may differ from a display-only tint. No expansion is authorized
by this note.

Proposed policy for the Overseer to consider adding to AGENTS.md: future visual
features should expose useful artistic colors through the established declaration
mechanism where applicable; preserve authored defaults, shading and audio response;
use stable target/role IDs and clear names; document unsupported/inapplicable
controls; and verify through Dev Studio. This proposal is already documented in
TECHNIQUE_LIBRARY.md; shared policy/planning was intentionally not rewritten.
