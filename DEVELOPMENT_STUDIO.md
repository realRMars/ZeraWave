# DreamWave Development Studio

## Air / Wind (2026-09-27)

Accepted Air integration: Main Blend and explicit effect playback carry selected
materials through Windstreams' clouds/balloons and Stormfront's cloud interiors.
Tunnel, Fractal folds and Horizon act on material/detail coordinates. Held
Authored forms retain the accepted presentation. The native Air cycle now uses
broad moving regions to blend scenes; each scene keeps its own camera and depth.

Accepted Air checkpoint: Windstreams flies past fractal balloons and clouds
above patchwork land. Stormfront follows a curved, mirrored cloud corridor.
Vortex combines rotating material, wall lightning and free jagged discharges
rooted at its inner rim. Sky Citadel has a rotating castle with a closed gate,
attached earth, tower lasers, fireworks and a material-covered planet below.
Daddy Long Legs remains a dormant FX experiment. See DREAMWAVE_HANDOFF.md
for detailed behavior and validation history.

Restart Studio, choose Elements > Air / Wind, then leave the form blank to see
Windstreams, Stormfront, Vortex and Sky Citadel evolve through a 144-second cycle.
Select a form to hold it. Air details provides cloud/ribbon, balloon,
lightning and castle/celebration controls alongside existing materials.
All four forms are also available to Main's musical director. The older fixed
itinerary and quiet Aftershock fallback descriptions below are historical;
current behavior is documented at the top of DREAMWAVE_HANDOFF.md.

Run `run_development_studio.bat` from the project folder.
This small control window launches the existing renderer and analysis tools;
it does not introduce another audio pipeline, shader interface or renderer.
It uses the Python environment's built-in Tk widgets, with no added dependency.

## Musical response

Motion now has a wider, smoothly integrated energy range. Quiet passages keep
the .35 baseline; movement, flux and bass can raise the clock toward 3.68, with
bounded onset accents and an absolute cap of 4. This changes motion rather than
audio normalization. Cosmic star motion retains its separate continuous clock.

Main blend still has its varied underlying itinerary, plus additional Planet
Canvas opportunities after 45, 55 and then 85 seconds between triggered visits.
An opportunity waits for 1.5 seconds of sustained weighted energy; silence does
not force a visit. These are energy cues, not actual chorus recognition. The
Planet gathers over six seconds, holds, and releases over nine seconds. It waits
while Aftershock is prominent. World handoffs now share a gentle twist and lens
compression. Fractal folds appear more readily with flux, and the siblings can
participate in them while retaining protection against unresolved fine detail.

Aftershock now uses up to eight active sites, scattered ahead and to either side
of the camera. Groups of four detected onsets launch a new detonation, subject
to a 1.5-second minimum spacing and available capacity. Sustained input is not
counted repeatedly. A ten-second fallback keeps sparse music alive. This is
onset grouping, not beat-grid/4/4 detection. Each site grows, settles and fades
over 20 seconds; clouds draw from far to near. The existing expanding material
inversion and separately bounded dust/fire rings remain. The same behavior is
used in Main blend and held Aftershock previews.

Molten flow now rotates with the integrated music clock and has a gentle bounded
zoom; river transport uses that clock too. Liquid Alloy has independent object
hues and color variation across its reflective folds. Living artifacts' palette
has not been retuned. Restart an open preview to load these changes.

## Main blend and material siblings

Main blend now starts with Living artifacts, Liquid Alloy and Prismatic Lattice
melding automatically. Restart Studio and select Main blend, or launch
`run_live_visualizer.bat`. No material preset is required. A saved explicit
Authored profile still restores the earlier sequence; New session clears saved
custom profiles. Main blend owns a separate list from the held-world lists.

Worlds follow a repeatable shuffled itinerary: both Organic forms, Neon corridor,
Planet canvas, all five Water forms and all four Fire forms, including Aftershock.
Each six-minute chapter visits all 13 forms in a newly shuffled order, with varied
holds (roughly 20–41 seconds in the first three chapters). Ordinary holds devote
almost half their duration to gathering into the next world; occasional longer
holds leave more room to breathe. The underlying itinerary is timed; extra Planet visits use the energy gate
described above. Music shapes motion, pressure, highlights and events.

The Main blend material slots are independently timed at 22 seconds. Living →
Alloy → Lattice repeats, fading during the last 35% of each slot. Their order and
hold are editable in Effects & layers. Rain, ripple rings and Water highlights
also breathe on independent slow cycles. Off switches remain effective.

For held worlds, choose **Presets → Material trio — all worlds** to apply the
three-material cycle to every world's list (36-second slots in this preset).
**Meld materials** follows enabled material rows in table order. Up/Down changes
that order; On/off removes a material from the cycle. Other enabled effects stay
active with spatial effects retaining authored strength envelopes. Together
combines selected materials in equal shares; Solo isolates one for inspection.
Choose the Material effect category to add either sibling to a custom list.
Alloy rolls and stretches along its flow; Lattice's cages tumble independently.

Held worlds retain their existing Authored default. Cosmic Geometry study
bypasses materials; use Planet canvas to inspect their surface gathering.
Fire's held native cycle still includes its original three forms; Main blend
visits Aftershock independently. Replay captures record material weights and
world/form weights. Playback speed changes pacing, not itinerary or analysis.

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
Elements expands to Water, then Sea, Liquid dyes, Rain & ripples, Waterfall,
and Currents. Elements also contains Fire → Flame sheets / Molten flow / Firescape / Aftershock (isolated development
forms, also visited by Main blend).
Cosmic expands to Planet canvas and Geometry study. Organic expands to Membrane
and Roots; blank Form keeps their original authored meld. Geometric expands to
Neon corridor. Transition remains the existing Cosmic handoff diagnostic.
No unimplemented elements are exposed.

Every selector offers a genuinely blank option:

- Blank Visual world selects the normal main blend.
- Elements with blank Category visits all five Water forms, then all four Fire forms, in
  28-second development holds. These are direct switches, not authored melds.
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
actual active state. Normal run_live_visualizer has no diagnostic sequence and uses the new Main blend itinerary.

## Forms, effects and layers

Use **World** for a visual environment, **Form** for its main structure, and
**Effect** for an optional treatment. **Layers** means the world's saved list
of effects. Elements remains a grouping category; Water owns its own layer
profile. Fire has its own independent profile.

The Effects & layers tab follows the selected world. Its two dropdowns choose
an effect category and effect. Add inserts it once; the table supports On/off,
Solo, Remove, Up and Down. Solo enables only the selected row without deleting
the others. Lists survive switching worlds and are included in saved sessions.
Organic forms share Organic's list; Water forms share Water's list.

- **Authored:** original visuals and timing; the custom list is parked.
- **Selected together:** only enabled effects, applied to the selected form.
  An empty list shows its base material/structure.
- **Meld materials:** enabled materials fade in table order; other enabled effects remain active.
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

- Material: Living artifacts, Liquid Alloy, Prismatic Lattice, Sparkles, Drifting flecks, Radial beams.
- Spatial: Tunnel, Fractal folds, Horizon / pathway. Fractals remain a treatment
  for now, with a stable ID that can later be migrated to a dedicated world.
- World details: Root blossoms, Corridor glyph rain, Drifting starfield,
  Planet rings, Moons & dust wakes, where applicable.
- Water details: Rain streaks, Ripple rings, Crest foam / cliff lip,
  Mist & distance haze, Surface highlights.

World-specific effects require their geometry: blossoms appear on Roots;
Cosmic Geometry study uses only World details. Select Planet canvas to inspect
its inherited material effects. Custom material layers are explicitly preserved
over the Organic surface before planet/corridor projection. Water exposes its
inherited Living artifacts and the Water details category. Rain streaks and
ripple rings can be added independently to surface forms, including Currents.
They do not appear on the vertical waterfall; its own highlights, cliff lip
and haze can be controlled separately. Foam needs steep storm crests, and
distance haze is subtle in close views. Geometry and wave motion stay part of
the form. Custom lists must explicitly include desired details; Authored keeps
their original behavior. Existing bit IDs and version-3 sessions remain valid.

Main blend has its own preview profile. It does not import the individual world
lists automatically. The normal live launcher uses Main blend’s default trio profile.

The shared development catalog/validation is app/visuals/preview_layers.py.
Its stable effect bits and material weights feed the existing renderer.
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

`water` now previews sea, liquid dyes, rain/ripples, waterfall and Currents over
a 140-second cycle. Each holds for about 19 seconds and blends over about 9
seconds. `sea`, `dyes`, `rain`, `waterfall` and `currents` hold an individual form.
Currents (state 13) is an overhead flowing composition with two broad eddies,
advected source colors, dark channels and selective fine reflected ribbons.
Bass broadens the flow, flux changes local shear, sparkle reveals fine light,
and impact disturbs a bounded region. Quiet input still transports material.
It uses existing integrated clocks and a procedural inverse coordinate field,
not a physical fluid simulation or a second renderer.

Main blend visits all five Water forms through the shuffled itinerary described
above, with continuous material and movement clocks. Studio's isolated Water
branch retains its continuous five-form meld.
The accepted sea height/current equations remain unchanged.
The waterfall moves between a wide river-to-cliff view and an immersive close
view of water falling out of frame; there is no bottom pond. Restart an already
running preview after shader changes to load the revised waterfall.

The earlier 140-second Cosmic/Water sequence is still available through an
explicit Authored profile on Main blend. The default now uses the shuffled
itinerary, including Fire; it does not wait until 116 seconds to introduce Water.

New vocabularies are still implemented and verified in the existing shader.
There is no opaque import-to-main button: integration is an explicit code
change to the existing blend, reviewed and tested. This avoids copying shaders
between divergent development and production renderers. The state lists in
live_visual_test.py and shader_test.py expose held forms in Studio and tests.

## Repeatable checks

Use the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe app/visuals/studio_test.py
.\.venv\Scripts\python.exe app/visuals/shader_test.py --currents-test work/elemental/currents/before.frag work/elemental/currents/check
.\.venv\Scripts\python.exe app/visuals/shader_test.py --water-integration-test work/elemental/currents/before-integration.frag work/elemental/currents/integration
.\.venv\Scripts\python.exe app/visuals/shader_test.py --water-test work/elemental/check
.\.venv\Scripts\python.exe app/visuals/shader_test.py --water-family-test work/elemental/water-family/before.frag work/elemental/family-check
.\.venv\Scripts\python.exe app/visuals/shader_test.py --waterfall-test work/elemental/waterfall-perspective/before.frag work/elemental/waterfall-check
```

The comparison commands need their matching saved pre-change shaders. The
older layer-test against the original layer baseline predates the intentional
five-form development cycle; currents-test handles this expansion. The
water-integration-test verifies all five main visits, their handoffs, every
held form and pixels outside Water. Older main-blend comparisons against a
pre-integration shader intentionally differ during Water visits. They check
held-world pixel preservation, form visibility, meld boundaries and live
integration. The layer check covers every previous state and verifies visible
effect toggles against a base form. The waterfall check also sweeps the camera at 60 Hz and verifies
river/sky/falling-face coverage directly on the GPU.
Generated evidence and decoded audio are ignored working assets, not committed
fixtures. Standalone checks do not replace subjective listening/visual review.

## Fire foundation review

Restart Studio and select Elements → Fire → Flame sheets. Start with Authored;
Fire details offers Coals, Embers and Hot seams. Material offers the existing
Living artifacts, with its original palette. Blank Fire form melds Flame sheets, Molten flow and Firescape on an 84-second
cycle: 19-second holds and nine-second eased transitions between forms. Main blend now visits all Fire forms through its independent itinerary.
Test tracks and acceleration work through the same controls as Water.

Standalone GPU regression (baseline saved before this pass):
`.venv\Scripts\python.exe app/visuals/shader_test.py --fire-test work/elemental/fire/before.frag work/elemental/fire/check`

Molten flow holds branching lava rivers with dark crust islands, lit banks,
flowing seams and two small impact-heated vents. A slow aerial orbit reveals
the branches opening downstream, backed by simple forest/mountain silhouettes. It shares Fire's layer list:
Coals controls the crust islands, Hot seams the fine glow, Embers the sparse
sparks, and Living artifacts the inherited material. Held Flame sheets keeps
its approved appearance. CLI --state fire still means held Flame sheets;
--state molten holds lava, and --state fire_cycle runs the authored meld.
A saved blank Fire branch now includes all three forms; a saved Flame sheets leaf
continues holding that form. Older flat fire sessions also hold Flame sheets.

Expansion regression:
`.venv\Scripts\python.exe app/visuals/shader_test.py --molten-test work/elemental/molten/before.frag work/elemental/molten/check`

## Psychedelic Firescape

Select Elements → Fire → Firescape to hold multicolored flames across wooded
hills and a distant city silhouette. The existing audio-driven movement clock
sets the hue cycle rate (mids), and strong impacts lift flame brightness.
Ash is an additional Fire detail, separate from bright Embers. Ash currently
applies only to Firescape. All Fire forms share the saved layer list; accepted
Flame sheets and Molten flow retain their existing palettes. This new palette
does not replace Living artifacts. CLI: --state firescape; blank Fire uses
--state fire_cycle. Main blend now visits Firescape independently.

Verification:
`.venv\Scripts\python.exe app/visuals/shader_test.py --firescape-test work/elemental/firescape/before.frag work/elemental/firescape/check`

Firescape now scrolls left in depth layers, like a side-scrolling landscape.
Trees sprout and develop irregular crowns, then burn down to stumps; buildings
rise floor by floor and crumble into falling blocks/rubble. Each object keeps
its seeded 64-second life while moving through the view. Hold Firescape for
60–90 seconds to see several overlapping stages. These scenery changes use the
same controls and do not change Flame sheets or Molten flow.

## Aftershock preview

Select **Elements / Fire / Aftershock** for the new detonation flyover. Strong
hits produce independent expanding dust/fire rings; quiet input retains camera
motion, scheduled detonations and growing clouds. Under **Aftershock details**,
Inversion flash, Dust shockwaves, Ground fire and Aurora can be added/removed
or cycled.
Authored restores the complete composition. Coals controls crater shading;
Embers, Ash and Hot seams retain their other Fire-form uses.

Aftershock is accepted as a separate held form. Fire's existing All / cycle still uses
the accepted Flame sheets / Molten flow / Firescape meld; the broader Elements
leaf cycle and Main blend both include Aftershock. Replay metrics
include shockwave_count and capture metadata includes event lists, making
multiple-hit behavior inspectable with the existing accelerated tracks.

Aftershock refinement: clouds now draw in actual distance order. The inversion
fades over two seconds; musical rings use a higher .40 threshold and three-second
cooldown, allowing at most three simultaneous rings. Aurora curtains gently
bend at scheduled detonations and settle; this motion is independent of musical
ring triggers. Restart an existing preview to load the shader changes.

Aftershock plumes now retain a distinct hue per ground zero. Inversion flash
reveals a negative of the incoming material (including enabled Living artifacts)
before it is muted into the ground. Its existing two-second fade and effect
control are unchanged; the original material palette is not modified.

The accepted Aftershock projection has a subtle planetary horizon arc shared
by the ground, sky, plumes and flash. Aftershock is integrated into Main blend;
adding it to the native three-form Fire meld remains separate follow-up work.


## Shared spatial pulls

Main blend and Meld materials now let Tunnel, Fractal folds and Horizon/pathway
carry all three materials and Water details across worlds. Their overlapping
holds let an outgoing pull feed the next. Selected together holds enabled
spatial effects fully on; Cycle list remains a diagnostic row switch.
Water and Fire now include Spatial rows in their existing effect table.
World silhouettes and physical surfaces remain intact, and Authored preserves
the earlier world presentation. Stars and Aftershock geometry are intentionally
outside the material fold. Use Fractal folds with a material enabled to inspect
the broad recursive shapes, then Main blend to review their release and overlap.
## FX experiments

Daddy Long Legs is a shelved Vortex effect under **Air → FX experiments**.
It is inactive in authored playback and default Main/material presets. Add it
explicitly to a custom effect list to preview it; existing sessions keep it off.
Experiments use a separate switch where needed because the original signed
effect mask is full. Existing effect IDs and saved masks are unchanged.
