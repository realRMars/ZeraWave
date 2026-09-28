# ZeraWave technique map

Start here before extending a visual. This map describes current ownership;
it is not a request to extract every shader function into a new framework.

## Code lookup for developers and agents

Run from the project root, without starting Studio:

```powershell
.\.venv\Scripts\python.exe app/visuals/technique_library.py water_current
.\.venv\Scripts\python.exe app/visuals/technique_library.py "feedback" --json
```

The Python API is `find_code(query, root=None)` in
`app/visuals/technique_library.py`. It scans current app Python definitions using
AST and GLSL function definitions, searches implementation bodies as well as
names and technique descriptions, and returns current source paths/line numbers.
There is no stale generated index and no renderer import or UI launch. Use the
JSON output for automated workflows. No results means try synonyms and direct
source search, not proof that a capability is absent. GLSL discovery covers the
project's current function syntax, not a complete shader language parser.

## Find and reuse

1. Search Studio > Library for the world, effect or technique. World and effect
   entries come from the existing catalogs, so new catalog entries appear there.
2. Use the symbols below to find implementation; line numbers are deliberately
   omitted because shader edits move them. Check callers and coordinate systems.
3. Isolate the form in Studio, then use Effects & layers for optional treatments.
   Not every internal technique is independently toggleable or portable.
4. Test the change in isolation and Main blend. Preserve opacity, clock continuity,
   accepted colors and session IDs. Do not retune global audio to fix one scene.

## Ownership and extension points

| Need | Existing owner | Reuse boundary |
| --- | --- | --- |
| World/category/form navigation | app/visuals/studio.py: WORLD_TREE | Stable selection paths; descendants generate Library entries automatically. |
| Effect names, compatibility, saved profiles | app/visuals/preview_layers.py: EFFECTS, validate_layers | Preserve IDs/order; all 31 positive legacy mask bits are occupied. New detail groups use explicit uniforms. |
| Technique descriptions and search | app/visuals/technique_library.py: TECHNIQUES, entries, search | Read-only discovery, not a second runtime registry. Add a description and verified symbol when adding a reusable technique. |
| Music-aware world choice | app/visuals/renderer.py: choose_world, update_blend | Energy/lift/release heuristics, not BPM or chorus recognition. |
| Motion, event histories, graphics lifecycle | app/visuals/renderer.py: render, close | Continuous clocks and bounded events. Resource allocation/release belongs here. |
| Materials and world gathering | app/visuals/shaders/dream.frag | Living Artifacts is inline in main; liquid_alloy, prismatic_lattice and musical_material are named helpers. |
| Shared spatial treatment | dream.frag: spatial_carrier, spatial_weights | Material coordinates; do not distort solid depth geometry inadvertently. |
| Planet/star treatment | dream.frag: isolated_cosmic_scene, cosmic_star_layer | Separate continuous star clock and surface gathering. |
| Corridor perspective | dream.frag: geometric_surface | Shared with Stormfront's vault; preserve both callers. |
| Liquid surfaces | dream.frag: water_current, water_height, water_surface, waterfall_surface | Procedural flow/height and surface projection, not a physical fluid solver. |
| Fire motion and events | dream.frag: firescape_tree, blast_ring; renderer.py event state | Growth/decay and bounded disturbances; avoid frame-dependent lifetimes. |
| Castle and terrain depth | dream.frag: air_castle_map, earth_map, earth_surface | Solid ray queries, directional shading and conservative rejection bounds. |
| Vapor and pressure | dream.frag: fog_density, fog_scene | Deliberate volume translucency with opaque solid surfaces. |
| Electrical structures | dream.frag: plasma_scene, plasma_loop | Filaments, localized discharges and form-specific skies. |
| Regional transitions | dream.frag: handoff_front, handoff_share | Blend scene regions while retaining each world's own projection. |
| Audio features and mapping | app/audio/audio_frame.py; app/visuals/parameter_mapper.py | Audio meaning remains separate from scene interpretation. |

## Verification entry points

Use the production scripts under **app/visuals/**, not similarly named untracked
root scripts. Run with the project's .venv Python from the project root.

- studio_test.py: saved sessions, navigation, layer controls, launch commands,
  replay and GPU integration. Library search/navigation coverage lives here too.
- shader_test.py: deterministic captures, handoffs and performance checks; inspect
  its CLI before choosing a mode.
- replay_test.py: actual decoded tracks through analyzer, mapper and renderer;
  accelerated replay is silent and does not skip analysis chunks.
- live_visual_test.py: real system audio. Do not report decoded replay as live listening.
- parameter_mapper_test.py and app/audio/*_test.py: targeted signal changes only.

## Vocabulary and boundaries

World is the environment; form is its composition; material is its visible pigment
or substance; spatial effect changes its coordinate flow; detail belongs to a
particular world; technique is an internal building block; experiment is opt-in.
A layer list controls selection and cycling, not arbitrary GPU render-stack order.
Main has its own profile; individual world profiles are not automatically imported.

Daddy Long Legs remains dormant. Echo Weave is the fourth material:
renderer.py:update_echo owns its two fixed-resolution half-float buffers and
fixed-step lifetime; shaders/echo_weave.frag advances the field; dream.frag:
echo_material shades it through the existing material domain. It joins Main's default quartet; saved trio profiles remain valid. See DEVELOPMENT_STUDIO.md for isolation and reset behavior.
The original proposal remains in MILKDROP_COMPARISON.md.

## Next cleanup, only when needed

The shader is large, but moving code merely to shorten it risks changing shared
coordinate assumptions. First establish this index and tests. Extract a helper
only when a concrete second caller or independent test benefits. Keep historical
research and untracked scripts intact until their ownership and value are clear.


## Musical timing and player packaging

- app/audio/beat_tracker.py: BeatTracker.update_flux estimates periodicity and
  confidence from spectral activity; no normalization or visual accent changes.
- renderer.py:update_blend uses an .8-second bounded wait for already-justified
  transition opportunities when confidence is high. No forced global pulse.
- preview_layers.py:material_weights returns four absolute weights. materials_at
  retains a normalized vec3 for the old shader interface; echo_weave_at supplies
  the fourth weight. echo_selected keeps history warm while selected.
- app/player.py owns player preferences/child launch, not another audio pipeline.
- build_portable.py copies the installed Windows runtime/dependencies with notices,
  excludes the project's work/music/research folders, and smoke-tests the runtime.
- app/audio/beat_tracker_test.py, capture_selection_test.py, app/player_test.py
  cover timing confidence, device identity and preference/error recovery.

## World repair / sky extension (accepted 2026-09-28)

- `cavern_formation` owns stable cell-local formations. `earth_map` evaluates
  nearby footprints and bounds steps toward omitted cells, including for normals.
- `shooting_star_radiance(direction)` returns directional light, not an overlay.
  `water_environment` uses it for sky and reflected rays, before island occlusion;
  `cosmic_star_layer` also supports it. Sky effects > Shooting stars is independently
  selectable. Water authored mode enables it; Cosmic authored mode stays unchanged.
  Explicit older saved lists retain their selection and need the new row added.
- `Renderer.update_blasts` recycles the oldest event at eight sites on a fresh
  qualifying onset, with a .70-second spacing guard. Constant high impact does not
  retrigger. It no longer waits for the pool's 20-second lifetimes to expire.

Next extension direction (not implemented): independent palette families, then
surface-light treatments (pearlescence, caustics, ink absorption), and flow-driven
feedback. Keep material, spatial, sky/light and palette responsibilities distinct.
For each reusable effect document coordinate space, occlusion/reflection support,
quiet/peak audio roles, compatible worlds and measured cost. No new framework or
third-party source is required for this incremental approach.

Next-work priority and acceptance status live in ZERAWAVE_HANDOFF.md. Reusable
style presets are a later proposal using existing session/profile machinery,
not a new preset format. The portable checkpoint does not include this sky pass.
