# DreamWave Development Studio

Run `run_development_studio.bat` from the project folder.
This small control window launches the existing renderer and analysis tools;
it does not introduce another audio pipeline, shader interface or renderer.
It uses the Python environment's built-in Tk widgets, with no added dependency.

## Working cycle

1. Select a world, then narrow its cascading category/form selectors.
   Optionally open Effects & layers to build that world's custom effect list.
2. Choose Test track, Synthetic preview, or Live system audio.
3. For tracks, choose Balloon, Chasing You, or Warbot Jazz, a speed and duration.
4. Start preview. Close the visual window to finish normally and save metrics.
5. Open the Review tab and latest results. Try the other tracks and quiet inputs.
6. Select Preview main blend to test how the integrated vocabulary fits.

Track replay is silent: it runs decoded music through the real shared analyzer,
mapper and GPU renderer. Real time, 2x, 6x and 12x are target pacing rates;
Fastest removes deliberate waiting. No audio chunks are skipped. Rendering
cost limits actual speed. Live input listens to the default system output.
Track speed/duration/capture controls do not affect live or synthetic previews.

Every run has a unique folder under `work/studio/`. Track runs save metrics.csv,
and optionally frames every 15 song seconds plus captures.json. Every run has
run.log and preview.json (the exact version-3 session used). Stop preview forcibly ends only this Studio's child; existing captures
remain, but final metrics may be incomplete. Prefer closing the visual window.
Only one child per Studio runs at a time. Setting changes apply to the next run.

## World hierarchy and isolation

Visual world contains Organic, Geometric, Cosmic, Transition, and Elements.
Elements expands to Water, then Sea, Liquid dyes, Rain & ripples, and Waterfall.
Cosmic expands to Planet canvas and Geometry study. Organic expands to Membrane
and Roots; blank Form keeps their original authored meld. Geometric expands to
Neon corridor. Transition remains the existing Cosmic handoff diagnostic.
No unimplemented elements are exposed.

Every selector offers a genuinely blank option:

- Blank Visual world selects the normal main blend.
- Elements with blank Category currently runs Water, the only implemented element.
- Elements → Water with blank Form runs Water's existing authored meld.
- Selecting Sea, Rain & ripples, etc. holds only that form.
- A branch without an authored cycle visits all its implemented leaf states,
  in catalog order, for 28 seconds each, then repeats. These are direct testing
  switches, not new artistic transitions. Cosmic currently uses this behavior.

Changing a parent clears its old descendants. Deeper branches generate more
selectors automatically, with a scrollbar when needed. The selection hint
explains whether the current choice is held, a native cycle, or sequential.
Presets use the same nested structure. Restart Studio after updating its code.

The catalog is WORLD_TREE in app/visuals/studio.py. Keys are stable session IDs;
labels are display names. Nodes have children, a held renderer state, or an
optional native cycle for their entire branch. Add nested nodes without writing
more UI rows. Backend states must already be implemented and registered in the
existing live/synthetic state maps. When a parent gains several branches, its
generic cycle traverses every leaf, including grandchildren, so a short hold
cannot skip subforms. Selecting a branch with a native cycle still keeps its
authored meld. Only implemented forms should be put in the runnable catalog.

Sessions now use version 3 and save the selection path plus independent effect
lists for each world. Version 1 flat state sessions and version 2 hierarchy
sessions load with authored effects; saving writes version 3. Unknown
or removed paths are rejected clearly rather than launching another world.
Track/speed/capture settings retain their existing meaning.

The optional --states argument is supported by live, synthetic and replay
entry points. The existing renderer selects its debug state from elapsed time;
audio analysis, integrated movement and Cosmic star clocks continue without
reset. Replay uses song time at every speed, and metrics/captures record the
actual active state. Normal run_live_visualizer has no sequence and is unchanged.

## Forms, effects and layers

Use **World** for a visual environment, **Form** for its main structure, and
**Effect** for an optional treatment. **Layers** means the world's saved list
of effects. Elements remains a grouping category; Water owns its own layer
profile so future siblings can have independent settings.

The Effects & layers tab follows the selected world. Its two dropdowns choose
an effect category and effect. Add inserts it once; the table supports On/off,
Solo, Remove, Up and Down. Solo enables only the selected row without deleting
the others. Lists survive switching worlds and are included in saved sessions.
Organic forms share Organic's list; Water forms share Water's list.

- **Authored:** original visuals and timing; the custom list is parked.
- **Selected together:** only enabled effects, applied to the selected form.
  An empty list shows its base material/structure.
- **Cycle list:** one enabled effect at a time in table order, skipping disabled
  rows. Hold controls the seconds per effect. Empty means base form.

Adding/editing a row enters custom mode. Switch playback to Authored to recover
the original appearance. Ordering controls the cycle, not an arbitrary render
stack: spatial coordinate treatments and material contributions retain the
existing shader composition order. Cycle switches are direct diagnostic cuts.
Effects keep their musical response/lifecycles, so some remain subtle or quiet
until the appropriate passage. Time is song time in accelerated replay; the
audio pipeline and integrated drift/star clocks never reset on a layer change.

Available categories:

- Material: Living artifacts, Sparkles, Drifting flecks, Radial beams.
- Spatial: Tunnel, Fractal folds, Horizon / pathway. Fractals remain a treatment
  for now, with a stable ID that can later be migrated to a dedicated world.
- World details: Root blossoms, Corridor glyph rain, Drifting starfield,
  Planet rings, Moons & dust wakes, where applicable.

World-specific effects require their geometry: blossoms appear on Roots;
Cosmic Geometry study uses only World details. Select Planet canvas to inspect
its inherited material effects. Custom material layers are explicitly preserved
over the Organic surface before planet/corridor projection. Water exposes its
inherited Living artifacts; its waves, rain/ripples and waterfall are still
forms with their own authored structure, not independently removable layers.

Main blend has its own preview profile. It does not import the individual world
lists into production. The normal live launcher supplies no overrides.

The shared development catalog/validation is app/visuals/preview_layers.py.
Its stable effect bits feed two optional uniforms on the existing renderer.
All three entry points accept --layers JSON; replay CSV/captures record the
actual layer_mode and layer_mask. A zero mode means authored; a custom mode
with mask zero means base form. Fixed shader captures also honor --layers.

## Menus

- File: new session, load, save, save as, close.
- Edit: choose another decoded WAV and select replay speed.
- View: switch between Build & preview, Effects & layers and Review, open results.
- Presets: nested worlds/categories/forms, All / cycle choices, and main blend.
- Import / export: JSON development sessions, containing settings and track paths.

Sessions do not contain music or shader code. Track paths must exist on the
computer loading them; choose another track if a session moved computers.
Only decoded 48 kHz, 16-bit WAV is supported by replay. The existing MP3s and
decoded files are reused without moving or converting them.

## Water and integration

`water` melds sea, dye currents, rain/ripples and waterfall over a 112-second
cycle. Each holds for about 19 seconds and blends over about 9 seconds.
`sea`, `dyes`, `rain`, and `waterfall` hold an individual form for comparison.
The accepted sea height/current equations remain unchanged.
The waterfall moves between a wide river-to-cliff view and an immersive close
view of water falling out of frame; there is no bottom pond. Restart an already
running preview after shader changes to load the revised waterfall.

The main blend now admits Water after the original Cosmic release: first
entrance at 116 seconds, full Water at 126–144, release by 158. Subsequent
visits repeat every 140 seconds. The initial startup is unchanged. Water's
independent form cycle gives later visits different forms. These are timed
scaffolds, not music phrase detection. Music drives expression within them.

New vocabularies are still implemented and verified in the existing shader.
There is no opaque import-to-main button: integration is an explicit code
change to the existing blend, reviewed and tested. This avoids copying shaders
between divergent development and production renderers. The state lists in
live_visual_test.py and shader_test.py expose held forms in Studio and tests.

## Repeatable checks

Use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe app/visuals/studio_test.py
.\.venv\Scripts\python.exe app/visuals/shader_test.py --layer-test work/development/layers/before.frag work/development/layers/check
.\.venv\Scripts\python.exe app/visuals/shader_test.py --water-test work/elemental/check
.\.venv\Scripts\python.exe app/visuals/shader_test.py --water-family-test work/elemental/water-family/before.frag work/elemental/family-check
.\.venv\Scripts\python.exe app/visuals/shader_test.py --waterfall-test work/elemental/waterfall-perspective/before.frag work/elemental/waterfall-check
```

The comparison commands need their saved pre-change shaders. They check
held-world pixel preservation, form visibility, meld boundaries and live
integration. The layer check covers every previous state and verifies visible
effect toggles against a base form. The waterfall check also sweeps the camera at 60 Hz and verifies
river/sky/falling-face coverage directly on the GPU.
Generated evidence and decoded audio are ignored working assets, not committed
fixtures. Standalone checks do not replace subjective listening/visual review.
