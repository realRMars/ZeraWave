# Elemental vocabulary: Water foundation

## Plasma foundation (2026-09-27, accepted)

Magnetic Bloom: colored field loops stretch around an opaque charged core.
Arc Constellation: moving charged nodes exchange branched discharges and pulses.
Auroral Veil: folded vertical sheets glow in layered curtains with open dark gaps.
All three have musical response, native transitions, Studio detail isolation
and Main Blend integration. The native cycle lasts 108 seconds.

User accepted all three states and their animated skies. This completes an
accepted foundation for all six Elemental families. Further expansion should follow observed weaknesses
or requested compositions rather than adding families automatically. See the
handoff for techniques, verification and limitations.

## Fog / Gas expansion (2026-09-27, accepted)

Nebula Banks flies through blue/rose vapor with broad openings. Ghostlight Marsh
passes opaque marbled headstones above a dark textured path, with green/amber
fireflies, growing moss and cracks, and cross-shaped light projections in mist.
Pressure Chamber moves through cyan/ember
folded gas cavities with traveling pressure fronts. The native cycle lasts
114 seconds; all three also enter Main Blend through the existing director.

This pass introduces bounded volume integration with exponential extinction,
solid-depth occlusion beneath vapor, density-gradient edge lighting, and a
gyroid-like density field. Existing integrated musical time controls travel;
bass, flux, sparkle and impact have independently tested visual responses.
See the current handoff for verification and approximation/performance limits.

The Plasma foundation above supersedes the earlier future-family concepts.

## Earth expansion (2026-09-27, commit authorized)

Earth now has three connected forms: Dune Sea (low flight over wind-shaped
ridges), Folded Strata (a winding layered canyon), and Crystal Cavern (faceted
mineral clusters in a dark chamber). Existing integrated musical time drives
forward travel; bass adds terrain pressure and sediment bending, sparkle
reveals mineral detail, and impacts illuminate veins/crystals. Regional
handoffs connect the forms and Main Blend. Dunes now include a segmented worm
that breaches and dives at seeded locations/depths. Strata has eroded shelves
and overhead rock spans. Cavern mixes quartz-like needles, blocky minerals and
limestone stalactites/stalagmites. The worm now uses a low arc and wrapped
material canvas. Cave walls/ceiling are lit dark stone, with surface-attached
glints, irregular formations and faster curved travel. Surface pigment uses directional/contact
shading; emission is concentrated in mineral seams. See DREAMWAVE_HANDOFF.md
for tests.

Dunes and Strata now have distinct animated skies. Main Blend uses the
existing musical director, cycling materials and spatial folds, with shorter
regional overlaps between Earth forms. See the latest handoff checkpoint.

The Fog expansion above supersedes this checkpoint's earlier Fog backlog.
See the Plasma foundation above for the current implementation.

## Air / Wind expansion (2026-09-27)

The latest DREAMWAVE_HANDOFF.md supersedes historical Fire/Main limitations below.
Air adds Windstreams, Stormfront, Vortex and Sky Citadel in Main and Studio, with
a shared sky/palette/landmark and evolving native cycle. User accepted the Air
checkpoint and authorized its commit. The Earth expansion above supersedes
the earlier Earth backlog; see the newest sections for Fog and Plasma status.

Updated 2026-09-26. Base checkpoint: `aa44d54`, accepted Geometric material
gathering. Read AGENTS.md and the current DREAMWAVE_HANDOFF.md entry first.

## Accepted Fire development checkpoint and curved horizon

The user accepted Aftershock's distinct plume hues/material-negative flash,
requested a subtle planetary horizon curve, and explicitly authorized committing
the accumulated Fire work. This checkpoint extends accepted Flame sheets with
Molten flow, Firescape, and Aftershock, plus their Studio controls and tests.

Aftershock now applies a shallow bounded screen-space arc to its complete
projection: ground, haze, aurora, clouds and flash share the same curvature.
The 16:9 horizon drops about nine pixels from center to each edge at 360p. This
is a subtle visual projection, not a spherical planet simulation. The flash
capture was inspected; the final Aftershock suite passed 216 exact preservation
comparisons for states 0-17 and 660 actual renderer frames, including existing
hue, depth, flash, aurora and musical-ring checks. Evidence:
work/elemental/aftershock/{horizon-checks,horizon-preview}.

The Fire form cycle still melds Flame sheets / Molten flow / Firescape over
84 seconds. Aftershock is an accepted held form available in Studio and the
general Elements leaf cycle; it has not been added to that native meld or the
main blend. Finishing Fire integration is the next separate task. Other worlds,
Living artifacts' original palette and continuous Cosmic star drift are preserved.
Final Studio standalone tests, Python compilation and git diff --check passed.
No new live-loopback test was run for the horizon adjustment.

Earlier entries below are chronological development history. Their pending-review,
uncommitted, prior-threshold and prior-cycle statements describe those earlier
passes and are superseded by this checkpoint and the latest implementation.

## Aftershock distinct plume hues and material-negative flash

The user accepted the depth/aurora refinement and requested distinct plume hues
and a flash that inverts Living artifacts/the incoming material. Each ground-zero
ID now receives a stable, separated hue; no animation clock rotates all plumes
together. Luminance from the existing cloud shading retains volume, rolling ash,
and depth haze. This recoloring is local to Aftershock clouds, not Living artifacts.

The expanding flash now samples the incoming fire_material canvas before its
muted ground treatment, applies local 1.6 exposure and RGB inversion, and fades
back into the scene using the accepted two-second envelope. Material colors and
artifact shapes become visible as a photographic negative, rather than merely
inverting the nearly neutral ground. The source respects the existing material
composition; no new material, layer, or control was introduced. Aurora, cloud
ordering, camera and restrained musical rings are unchanged.

Changed dream.frag, the existing shader_test.py checks and development notes.
The Aftershock GPU suite passed 216 exact state 0-17 preservation comparisons,
660 renderer frames, six distinct site-tint probes, known RGB negative probes,
and existing ordering/flash/aurora/ring checks. Synthetic overlapping-plume and
flash frames were visually inspected. A final silent Balloon replay covered
60.032 seconds / 1,407 frames and two detonations, with 12 captures and no sampled
clipping. Evidence: work/elemental/aftershock/{hue-checks,hue-preview,
negative-preview,hue-music}. No live audio test or new Studio test was needed for
this shader-only behavior change; controls and audio analysis were not changed.
Git diff --check and Python compilation passed. Uncommitted; review this look
before finishing Fire integration. HEAD remains 8be9d4e.

## Aftershock depth, flash, restrained hits and aurora refinement

The user accepted the initial Aftershock direction and requested correct distant/
near plume overlap, a longer inversion fade, fewer musical aftershocks and a
trippy aurora that bends at detonation. Visible clouds now sort by actual world
Z depth, not birth ID. Only the latest three sites can have living clouds within
the existing 86-second lifetime. This fixes the farther-every-third-site ordering
without changing camera, timing, or existing worlds.

Inversion retains its fast expanding front but now decays over two seconds,
with a smooth final fade (previously .65 seconds). Musical rings require impact
>= .40 and a three-second cooldown; the .14 rearm and eight-second lifetime stay.
The first attempted .55 threshold suppressed all Balloon hits (maximum .487),
so it was corrected using the actual replay range, without retuning audio analysis.
The new cooldown permits at most three simultaneous musical rings versus six
observed previously. On the same first 100 seconds, average counts fell from
4.06 to 1.55 (Balloon), 4.47 to 1.76 (Chasing You), and 4.34 to 1.30 (Warbot Jazz).

Three green/cyan/violet aurora curtains drift and fold behind the plumes, with
fine warped filaments. A localized, damped sky bend originates over each new
ground zero and settles independently of beat-driven rings. Aurora is separately
switchable under Aftershock details (new appended bit; existing IDs preserved).

Checks passed: 216 exact unchanged-state GPU comparisons, 660 renderer frames,
actual GPU depth-order cases at 120/156/192 seconds, longer flash/expiry, aurora
isolation and blast-bend/settling comparison, event sensitivity/cooldown/expiry,
and Studio selection/session/effect/replay tests. Three final silent real-track
replays each ran 130 seconds / 3,047 frames (9,141 total), with 39 captures, max
three rings and no sampled clipping. GPU timing sample: about 1.7 ms at 720p;
this is not end-to-end live FPS. Final sky/overlap and music frames were inspected.
Evidence: work/elemental/aftershock/{sky-checks,sky-preview,sky-music}.
Live loopback/audio playback was not tested. Changes remain uncommitted on
8be9d4e; Aftershock stays isolated from the existing Fire meld/main blend.

## Aftershock: isolated Fire flyover (review pending)

The user accepted Firescape's side-scrolling growth/burn/crumble pass and asked
for one final Fire scene: a flyover of rising mushroom clouds, expanding inverted
flashes and musical dust/ash shockwaves followed by ground fire. `aftershock`
(state 18) is now selectable in Studio: Elements / Fire / Aftershock.

The camera advances steadily through charcoal terrain, ash and pale-gold plumes.
Detonations begin at 5 seconds and repeat every 36 seconds; every third is farther
away near the horizon. Layered shaded cloud lobes rise and spread, smoke rolls
through the column, and old volumes fade or pass the camera. These are projected
procedural volumes, not fluid simulation or physical destruction. Existing source
material lightly stains the ground without changing Living artifacts' palette.

The existing renderer holds at most eight visual events, lasting eight seconds.
Impact >= .30 triggers a ring after rearming below .14, with 1.25-second cooldown.
The event stores timestamp, latest ground-zero ID and strength. Sustained input
cannot retrigger continuously. Dust leads ragged amber fire; flux adds local
curl. The inversion is a short expanding detonation flash, not an every-beat
screen flash. Studio has Inversion flash, Dust shockwaves and Ground fire under
Aftershock details. Coals controls crater shading; Ash/Embers/Hot seams remain
specific to their existing forms. The renderer lifecycle/audio analysis and
existing monotonic flow/star clocks remain unchanged. Replay metadata now records
event counts and capture-time event lists for verification.

Validation: `shader_test.py --aftershock-test` passed 216 exact baseline frame
comparisons covering states 0-17, 660 actual renderer frames, sustained-hit,
rearm/cooldown, bounded history, expiry, independent rings, effect isolation and
expanding/expiring flash checks. A 60-frame 1280x720 GPU timing sample measured
about 1.9 ms/draw (not a live end-to-end FPS guarantee). Timeline and final music
frames were visually inspected. Three final decoded-track replays (Balloon,
Chasing You, Warbot Jazz) each covered 100 seconds / 2,344 frames: 7,032 total,
30 captures, max six simultaneous rings and no clipping in sampled captures.
Studio standalone tests also passed recursive selection, new effect controls,
session round-trips, replay metadata/pacing and continuous GPU clocks. Python
compilation and git diff --check passed. These were silent offline replays,
not audible playback or live loopback.
Evidence: `work/elemental/aftershock/checks/` and `final-music/`.

Initial checks found overlapping-ring clipping; local tone mapping fixed it.
Visual inspection found a half-column hard edge from signed GLSL pow input;
explicit absolute input fixed it, followed by fresh tests and all three replays.
The initial module-style test launch failed because this repository uses standalone
script imports; the standalone entry point was used for successful checks.

HEAD remains `8be9d4e`. Accepted Molten/Firescape and this review-pending Aftershock
are uncommitted. No commit or main-blend integration was performed. The existing
84-second three-form Fire meld remains intact and does not yet include Aftershock;
select its leaf explicitly (the general Elements leaf cycle also reaches it).
Recommendation: four Fire concepts are enough; review Aftershock, then finish
Fire transitions/main integration rather than adding a fifth form.

## Firescape side-scroller and scenery life cycles

The user requested more natural trees, sprouting/growth followed by burning to
ground, a side-scrolling game-like scene, and buildings that rise then crumble.
Firescape now uses elapsed-time parallax: far hills, buildings and three forest
layers move left at increasing speeds. Seeded objects remain anchored to world
cells and retain their age while scrolling; neighbor cells prevent clipped
crowns, and each tree root uses its own ground height. The existing psychedelic
palette, mids-driven hue rate, impact brightness and ash/embers are retained.

Trees have curved trunks, six branch forks and irregular broad leaf clusters.
Their 64-second seeded lives grow through the first quarter, mature, then burn
from crown to trunk; stumps clear before the next sprout. Buildings rise floor
by floor (six rows / 18 blocks), then staggered blocks rotate, fall and shrink
into rubble before clearing. This is procedural animation, not rigid-body or
combustion simulation, and objects do not accumulate permanently. Timing stays
steady rather than twitching with audio. There are no new controls or layers.

The first life-cycle probe found faint sprouts below the visibility threshold.
Their opacity now rises early while geometry stays small; the same test passes
without weakening its threshold. At nine sampled ages the tree goes from zero
to 156 sprout pixels, 5,699 mature pixels, then 76 stump pixels and zero. The
building rises from zero to 11,880 pixels and its rubble height falls from 160
to 31 probe pixels before clearing. The life-cycle contact sheet was inspected.
A GPU foreground-scroll probe matches an exact one-pixel translated hill.
Scene wrap checks pass (max mean change .447/255), and the integrated color/motion
check remains smooth (max .470/255). All five effect responses and beat
brightness pass; the fixed hit raises mean brightness by 9.766/255.

--firescape-test passed 576 exact old-state comparisons, all held Fire checks,
Molten orbit/branches, 18 Firescape input/time samples and all three transitions.
Evidence: work/elemental/firescape/lifecycle-check/. before-lifecycle.frag is the
saved previous Firescape; before.frag remains the old-world comparison baseline.
This pass changes dream.frag, shader_test.py and three development notes only.
Studio/renderer/audio interfaces are unchanged; Studio tests were not rerun.
Python compilation and git diff --check pass. No live-loopback test. Main blend
still excludes Fire; this refinement and the prior expansion remain uncommitted.
Final corrected-sapling replay: first 90 seconds each of Balloon, Chasing You
and Warbot Jazz, held Firescape, 6,330 frames and 18 captures. All capture
structure/headroom checks passed with zero clipping. Balloon at 45s was visually
inspected with trees at several life stages and buildings assembling/crumbling.
Evidence: work/elemental/firescape/lifecycle-final-music/. The earlier
lifecycle-music/ runs preceded the sapling opacity correction. These are silent
excerpts, not full songs or live-loopback validation. Unrelated files untouched.

## Psychedelic Firescape (state 17), three-form Fire cycle

The user accepted the branching Molten landscape with "perfect" and requested
the next form: energetic forest/land/city fire, airborne ash/embers, psychedelic
color cycling at an audio-dependent rate, and big beats affecting brightness.
This was interpreted as a new Firescape form; accepted Flame sheets and Molten
palettes remain unchanged. Living artifacts and its original palette remain
intact. Molten acceptance supersedes the older pending-review language below.

Firescape layers three wooded hills with curling multicolored flame sheets,
a distant block skyline, 40 bright ember trajectories and 24 softer ash
trajectories. Local palette phase uses u_time*.38: the existing continuously
integrated mids-driven clock makes hue speed responsive without phase jumps.
Impact brightens the flame sheets; bass increases their extent/strength, flux
curls them and influences ash, sparkle reveals seams/embers. Quiet still moves.
New fire_ash bit 1048576 appends to existing IDs. It is independently selectable
in Fire details and currently only used by Firescape. Existing Fire layers
remain applicable. No new uniforms, renderer/audio changes or dependencies.

Studio blank Fire now cycles Flame sheets → Molten flow → Firescape → repeat
in 84 seconds (19s holds / 9s transitions). Held IDs 14 and 15 are unchanged;
16 remains the native cycle, 17 is Firescape. Elements' generic diagnostic
cycle now visits eight leaves. Three-way coordinate and composition weights
sum to one. When Firescape is absent, the original Molten/Flame arithmetic is
retained: the first simplified sum version failed exact preservation by one
8-bit step in a Molten pixel. Restoring the original route fixed it without
weakening the comparison. A malformed Studio test path was also corrected.

--firescape-test passed 576 exact comparisons for states 0–15 against the saved
accepted Molten shader. All existing flame ignition/lava, Molten orbit/branch,
layer and audio checks pass. Eight cycle endpoints match held forms; 24 boundary
checks and 813 transition frames pass (max mean step .699/255). New form: 18
input/time samples, zero clipping, contrast 29.36–46.49, dark fraction .47–.56.
All five effects visibly contribute. Strong impact raises mean brightness by
11/255 in the fixed comparison. 360 real-renderer frames verify continuous
clock rates .3508 quiet / 1.1446 strong mids (over 3x), max step .386/255.
Initial image and beat comparison were visually inspected. Evidence:
work/elemental/firescape/check/; before.frag is the accepted uncommitted Molten
landscape before this new form. Committed HEAD remains 8be9d4e.

studio_test.py passed after the test-path correction: Firescape selection,
Ash addition, saved profile round-trip, existing UI lifecycle, replay metadata,
pacing and continuous GPU clocks. All three 90-second fire_cycle replays passed
(6,330 frames / 18 captures), covering all three forms and return to Flame sheets.
Structure/headroom checks passed with zero clipped capture pixels. One 60s
Firescape frame per track was visually inspected; different songs produce
different hues at the same elapsed time through the integrated mids clock.
Evidence: work/elemental/firescape/music/. These are silent accelerated excerpts;
full-song/live-loopback tests were not run. Python compilation and diff checks
passed. Nine tracked development files contain the accumulated uncommitted
Molten/Firescape work; no commits or pushes in this pass.

This is layered procedural scenery, not combustion/particle simulation or a
rendered 3D city. Main blend remains unchanged. Current expansion is uncommitted
and awaits review. Existing unrelated scratch/research remains untouched.

## Molten landscape refinement: branching rivers and aerial orbit

The user requested splitting/new rivers, a slowly rotating aerial view, and
an understated forest/mountain silhouette. The camera now intersects a ground
plane from an elevated orbit at .008 radians/second (about 13 minutes per turn).
Gravity/horizon stay level; the river and distant angular silhouettes change
with the viewpoint. Two simple mountain layers, conifer-shaped tree-line teeth
and distance haze provide context without detailed scenery.

Four side channels separate from the parent at fixed upstream junctions.
Slow staggered phases extend/recede their downstream hot fronts. This is a
bounded procedural branching network, not simulated erosion or permanently
accumulating lava. Flow remains steady; no audio-driven camera jumps. The
existing material, Fire layers and two-form timing remain intact. Flame sheets
and states 0–14 still match checkpoint 8be9d4e exactly in 540 comparisons.

Extended --molten-test passed the existing 18 profile/time samples, four audio
responses, four layer responses, silent motion, six held-form cycle endpoints,
24 boundary checks and 542 meld frames (max mean step .517/255). Nine views span
an entire orbit and retain visible lava with smooth adjacent frames. A GPU
probe of the actual channel mask at four times shows 3–4 channels across rows,
1,338 changed mask pixels between 42/100s, and over 98% connected coverage from
the parent in every sample. Orbit and branch-mask sheets were visually inspected.
Evidence: work/elemental/molten/landscape-check/. Previous Molten shader saved
as before-landscape.frag; original preservation baseline remains before.frag.
All three 60-second held-Molten replays passed: 4,221 frames / 18 captures,
zero clipped highlights, structure/dark-space checks passed. Balloon at 30s
was visually inspected at 1280x720. Evidence: landscape-music/ under the same
Molten work folder. Python compilation and git diff --check passed. Studio
controls are unchanged, so UI tests were not rerun; no live-loopback retest.
This refinement changes dream.frag, shader_test.py and the three development
notes; it preserves the already-uncommitted Molten expansion. Nothing committed
or pushed. Unrelated research/scratch files remain untouched.
This refinement is uncommitted, isolated from main, and awaits motion review.

## Molten flow expansion from accepted Fire checkpoint 8be9d4e

The user accepted the Fire refinement, authorized its commit, and requested
expansion. One additional form, Molten flow (15), supplies a contrasting
composition: an oblique winding lava river beneath drifting dark crust islands.
Foreshortening and surface-gradient shading give the banks depth. Elapsed time
advects the material steadily; bass influences heat, flux modulates internal
seams, sparkle exposes detail/embers, and impact heats two anchored vents.
The vents are bounded glow responses, not a particle eruption simulation.

Studio's blank Fire branch now uses fire_cycle (16): Flame sheets for 19s,
a 9s eased transition, Molten flow for 19s, then a 9s return. Existing fire (14)
stays held Flame sheets. Its shader appearance is preserved exactly. The meld
interpolates material coordinates and crossfades the two compositions; it is
not a physical camera traveling from the hearth into a lava landscape.
All three states share the Fire layer profile and existing bits. Coals gates
molten crust islands; Hot seams, Embers and Living artifacts remain selectable.
No renderer/audio changes, dependencies, or main-blend integration.

GPU expansion test passed 540 exact old-state comparisons, including held
Flame sheets. All earlier Fire motion/ignition checks pass. New form: 18
quiet/moderate/full samples, four independent audio responses, four visible
layers and silent motion. Six cycle endpoints match held forms exactly;
24 boundary checks and 542 transition frames pass (max step .517/255).
Evidence: work/elemental/molten/check/, baseline before.frag from 8be9d4e.
The new form and both transition contact sheets were visually inspected.
Studio tests and all three 60-second native-cycle replays passed (4,221 frames,
18 captures). One Molten frame per track was inspected. Maximum clipping was
11 pixels of a 1280x720 image in the small Molten vents; this passed the bound
but is not zero. Live loopback and full-song runs were not repeated.
This expansion is uncommitted and awaits user review.

## Fire refinement: lava rhythm, licking tips and ignition

The user liked the foundation and requested a steadily flowing lava base,
more licking flame tips, and white-hot → blue → amber color on intense hits.
The existing Coals layer now carries slowly advected molten channels between
dark crusts. Its clock is elapsed time, its gentle rhythm is independent of
bass/flux/impact, and its stable effect ID remains fire_coals. Embers still
means the rising sparks. No additional controls or materials were introduced.

Traveling curls increasingly bend the upper flame sheets; tongue heights also
travel instead of remaining in a fixed comb. A narrow, ribbon-shaped root
region responds to the existing decaying impact envelope: white near the real
onset ceiling of .5, blue as it decays, and back to amber by about half a second.
The response belongs to the base form, independent of optional Hot seams.
It does not change the shared renderer envelope or audio normalization.

The initial broad ignition band failed the previous generic frame-change
bound (22.79/255) and looked too flat. It was narrowed and shaped around flame
folds. Tests now distinguish the intentionally abrupt onset from ordinary
motion: final onset 10.92/255 (bound 12), other frames at most 2.864/255 (bound 3).
504 prior-state preservation cases still match exactly. Lower-bed pixels are
identical between silent and full audio at fixed time and move over two seconds.
Cooling captures verify a white peak, blue decay and return to amber. Evidence:
work/elemental/fire/refinement/. Review remains isolated from main blend.

## Fire foundation from accepted Water checkpoint 38da96a

The user approved Fire as the next element, one at a time. State 14 is an
isolated Studio foundation: three rising flame sheets above a low coal bed,
with sparse ascending embers and controlled amber seams. A shared positive
flow clock advects the folds upward. Bass broadens the base and height, flux
curls the sheet edges, sparkle exposes seams/embers, and impact heats a bounded
lower region. Silence retains slow motion. This is procedural layered imagery,
not a volumetric combustion simulation. There is one form, Flame sheets.

The existing source material is advected into the fire. Living artifacts keeps
its existing generation and palette; only its new Fire presentation is warm.
Its contribution, Coals, Embers and Hot seams can be independently enabled or
cycled in Fire's layer profile. Existing layer bit positions are unchanged.
The renderer, audio pipeline, clocks and production blend remain unchanged.
Fire awaits user review before further forms or main-blend integration.

Deferred user idea: a sibling metallic material with its own palette and
apparent bevel/reflection depth, able to alternate with Living artifacts or
appear together. Do not retune Living artifacts or its palette to implement it.
Other future elements below remain concepts, to develop one at a time.

## Creative composition

### Water continuation from accepted checkpoint 6875fb9

The user accepted and committed Water/Studio, then authorized continuing Water
before developing other elements one at a time. This pass adds a distinct
Currents form and isolates existing Water details. Earlier pending-acceptance
statements below refer to the earlier development history.

Currents uses an overhead view of colored streams passing through two broad
eddies. Smooth local twists bend a shared inverse flow coordinate; longitudinal
material transport uses the existing positive flow clock. Bass widens the
eddies/streams, flux changes shear, sparkle reveals fine reflected threads,
and impact causes a localized disturbance. Dark channels preserve depth.
Quiet input retains slow advection. This is procedural liquid imagery, not a
numerical fluid simulation. The accepted sea height equations remain intact;
only this form reduces their surface displacement to emphasize current flow.

State 13 / Studio → Elements → Water → Currents holds the new form. The isolated
Water cycle (state 6) adds it after Waterfall, becoming 140 seconds. Its five
forms have the same 19-second holds and 9-second eased transitions. The user
accepted this expansion and asked to finish Water before committing. Main
blend now holds one form for each Water visit, cycling Sea, Currents, Waterfall,
Rain & ripples and Liquid dyes across successive visits. Selection advances
while Water is hidden; physical clocks do not reset. The existing 116–158s
Water window and 140s visit spacing remain intact. No other element was started.

Water details are now optional effects: Rain streaks, Ripple rings, Crest foam /
cliff lip, Mist & distance haze, and Surface highlights. Existing authored
forms preserve their previous appearance. Custom lists can add rain/rings to
surface forms, including Currents; the vertical waterfall instead supports
its lip, highlights and haze. Foam still requires steep storm crests. Inherited
Living artifacts remains independently selectable. IDs append to the existing
effect bit catalog; no new uniforms, dependencies, renderer or audio changes.

Pre-integration GPU verification: 144 preservation comparisons across prior held forms and
main blend matched 6875fb9 exactly; 44 effect/world combinations visibly changed
when enabled. Currents passed 28 quiet/active/chorus/time samples for structure,
dark space and highlight headroom, all four independent audio-response checks,
silent-input motion, 20 preview-cycle boundaries and 361 integrated frames.
Maximum mean frame differences were .8273/255 at joins and 1.1756/255 in the
integrated audio envelope. The synthetic contact sheet was visually inspected.
Evidence: work/elemental/currents/check/. Accelerated first-60-second excerpts
from all three tracks passed: 4,221 frames, 18 captures with no clipped pixels.
One capture per track was visually inspected. Studio selector/effect/session
checks passed, including minimum window bounds. These are excerpt replays,
not full-track or live-loopback tests. The user accepted Currents after this
review; final main-blend integration verification is recorded in the handoff.

**Latest waterfall review:** the user accepted the other forms, including rain
ripples, and requested a river running from a distant horizon to a nearer cliff
lip, then falling indefinitely. The waterfall now projects horizontal river
and vertical face geometry with a moving camera. Wide views show both horizons;
close views drop below the lip and fill with falling water. The material flows
continuously over that edge. Its former receiving pond/rings are removed;
rain's ripples are unchanged. This supersedes the basin descriptions below.

The waterfall refinement passed 108 other-world/held-form comparisons, 60
family samples, 20 transition boundaries and a 4,802-frame 60 Hz camera sweep
(maximum mean delta 1.8122/255). GPU geometry probes verify both horizons at
distance and uninterrupted falling-face coverage in close-up. The inherited
colored shapes ease at their cell edges and appearance threshold only within
the waterfall, preventing magnified pops. This is stylized plane geometry and
procedural liquid shading, not a fluid/terrain simulation.
All three complete music tracks passed on the corrected waterfall (15,467
frames). Audio inputs matched previous runs, all 84 captures retained structure
and dark areas with no clipped pixels, and the contact sheet was inspected.
Evidence: work/elemental/waterfall-perspective/{final,final-music}/.

**Current expansion:** the user accepted the sea setting and requested more
Water variation plus main-blend integration. State 6 now melds four forms:
the accepted sea, folded dye currents, rain with expanding rings, and a falling
water curtain feeding a basin. Individual states 7–10 hold those forms.
Transitions take about 9 seconds after about 19 seconds of rest. The held sea
remains the accepted composition; the new variants and transitions need review.

Water enters the main blend in the gap after Cosmic, first 116–158 seconds,
repeating every 140s. The 112s Water form clock varies forms between visits.
Cosmic's clock/dwell and initial startup are preserved. This is a timed
scaffold, not phrase detection. See DEVELOPMENT_STUDIO.md for the new preview
launcher, session controls, three-track replay and integration workflow.

The earlier isolated-sea notes below describe its foundation; statements that
Water has no scheduler entry or waterfall are historical, superseded here.

Family verification is under work/elemental/water-family/: 84 preserved-world/
held-sea comparisons, 60 form samples, 16 boundary checks, the complete Water
synthetic test, and six complete music replays (three tracks each in Water and
main blend, 30,934 frames). Audio inputs matched prior runs exactly. All 168
captures passed visibility/headroom checks; Water had zero clipped pixels.
Both music contact sheets and individual form/portrait captures were inspected.
Existing Cosmic highlights still clip in some main-blend samples (up to 1.50%).
New forms remain subject to user musical/aesthetic review. No second element.

An open night sea between distant rocky islands carries DreamWave's existing
colored material. Low mist gives the horizon depth; a broken path of reflected
light gives the waves scale and shape. Colored currents remain visible beneath
the surface. Quiet water keeps small ripples and slow current. Stronger music
lifts broad crossing swells with sparse foam on high, steep crests, preserving
dark channels. The user accepted the strengthened waves and authorized this
world-building pass; the new setting still needs visual acceptance.

Following live review, the user requested a raging-sea response during intense
music while retaining the calm treatment. A Water-only storm envelope now
introduces taller, faster crossing swells above the weighted input threshold
0.55, reaching full strength at 0.88 (60% bass, 25% flux, 15% sparkle). Existing
quiet/moderate waves remain the underlying surface. Wave phases use constant
multipliers on the existing clocks; audio changes amplitude, never elapsed
time. No renderer, audio or shared-clock edits were required.

The existing source field is evaluated once at Water's refracted/current
coordinates. Its palettes, body patterns and colored artifacts supply the dye.
Artifacts stretch into streaks; shared stars, falling flecks and radial lasers
are suppressed only in Water. Water bypasses the Organic membrane substitution.
Other state routes preserve their accepted behavior; no automatic scheduler or
transition changes were made.

## Implementation and controls

- `app/visuals/shaders/dream.frag`: `water_environment`, `water_current`, `water_height`,
  `water_surface` and `isolated_water_scene`, gated by debug state 6.
  A fixed camera views a bounded height field. Fourteen bisection steps locate
  the surface; rough seas first scan 40 bounded intervals to bracket a front
  crossing, allowing tall foreground crests to hide the troughs behind them.
  Finite differences produce normals for reflection/refraction.
  Colored absorption separates dark channels from submerged source material.
  The raised camera exposes a shared sky/island environment, also reflected
  by the surface. Distance haze softens the far sea; distance-aware normal
  samples reduce unresolved ripples. Islands are angular background silhouettes,
  not navigable terrain. Foam is bounded procedural shading, not fluid simulation.
- Bass (`u_scale`): broad wave amplitude and inherited material pressure.
- Flux: bounded spatial current shear and medium-scale cross waves.
- Sparkle: fine wave amplitude and selective reflected highlights.
- Impact: the existing renderer envelope drives a localized radial disturbance
  and locally bounded inherited event color/forms. No second event system.
- Mids: use the renderer's existing integrated `u_time` through movement.
  The wall clock contributes a small baseline drift during silence. Audio
  never directly multiplies elapsed time to reposition the whole surface.

No renderer edits, added uniforms, dependencies, audio retuning, feedback
buffers, persistent particles, textures or separate rendering pipeline.

## Preview and review

From C:\DreamWave:

```powershell
# Live system audio; start music through the default output yourself.
.\run_water_music.bat

# Fixed synthetic input, does not listen to music.
.\run_state_preview.bat water

# Existing decoded music replay, accelerated with optional evidence captures.
.\.venv\Scripts\python.exe app\visuals\replay_test.py "work\audio-replay\Balloon.wav" --state water --speed 0 --capture-dir work\elemental\music\balloon --capture-interval 15 --metrics work\elemental\music\balloon\metrics.csv

# Deterministic stills and synthetic GPU checks.
.\.venv\Scripts\python.exe app\visuals\shader_test.py --capture work\elemental\capture --state water --seconds 18 --profile chorus
.\.venv\Scripts\python.exe app\visuals\shader_test.py --water-test work\elemental\final

# Verify the world preserves the accepted rough-sea height and motion fields.
.\.venv\Scripts\python.exe app\visuals\shader_test.py --water-world-test work\elemental\water-world\before.frag work\elemental\water-world\comparison

# Compare all pre-existing routes against the actual accepted shader.
git show aa44d54:app/visuals/shaders/dream.frag | Set-Content -Encoding utf8 work\elemental\accepted.frag
.\.venv\Scripts\python.exe app\visuals\shader_test.py --preservation-test work\elemental\accepted.frag
```

The live/replay state dictionaries now accept `water`; replay continues to
require a decoded 48 kHz 16-bit WAV and plays no audio. The normal launcher
still uses `blend`. Close and reopen a preview after shader changes.

All three existing tracks have decoded copies in `work/audio-replay/`:
`Balloon.wav`, `Chasing You.wav`, and `Warbot Jazz.wav`. Original MP3s remain
in `test_audio/`. No new decoder or dependency is needed. `--speed 0` removes
deliberate replay sleeps; actual speed depends on rendering and presentation.
The default remains `--speed 12`. Neither option plays audible music.

Optional `--capture-dir` saves PNGs before buffer swapping plus `captures.json`
with song times, mapped inputs and pixel statistics. `--capture-interval` is in
song seconds, not wall-clock seconds. Without these options, replay behavior
is unchanged. Captures can pause accelerated execution briefly without changing
the audio chunks or the renderer's song clock.

## Evidence and limits

Current world evidence is under `work/elemental/water-world/`. The complete
Water test passed 36 still cases, independent controls, silent motion, 181
integrated frames and 360 draws across four sizes. The largest integrated
mean frame delta was 2.883/255. At 1080p, GPU draw median was 4.414 ms and
p95 4.829 ms, excluding capture, audio and window presentation.
The world comparison proved exact GPU height/motion equality with the accepted
waves at nine profile/time combinations, stable sky under changed audio, and
continuous storm onset (mean pixel delta .01787/255). All 72 other-world cases
were pixel-identical to the pre-world shader. Landscape, portrait and quiet
captures were visually inspected. The raised camera intentionally changes
Water's rendered composition; pixel equality applies to other worlds and
wave-field probes, not the new Water image.

All three full music tracks passed through the new world (15,467 rendered
frames). Audio CSVs matched the accepted rough-sea runs exactly. All 45
captures retained contrast and at least 62.86% dark pixels, with no clipped
pixels. The twelve-frame contact sheet was visually inspected. Evidence:
`work/elemental/water-world/music/{review-sheet.png,verification.json}`.
Accelerated replay is silent; synchronized listening remains user review.
The updated live Water window is open on BlackShark loopback.

The following records describe earlier stages and their measured timings.

Rough-sea refinement evidence is under `work/elemental/rough-sea/`. The added
GPU comparison test measured identical quiet/moderate pixels at 18, 67 and
180 seconds, 2.55-3.36 times the chorus height standard deviation, and increased
temporal height change. The latter reflects both speed and amplitude, not a
literal flow-speed multiplier. Threshold continuity passed (mean pixel delta
0.00921/255). All 72 samples across the six other state routes were pixel-
identical to the pre-refinement shader.

The complete Water synthetic checks passed: 36 still cases, individual input
responses, silence motion, 181 integrated attack/release frames, and four output
sizes. Largest integrated mean frame delta was 5.101/255. Measured rough-sea
1080p GPU draw time was 4.59 ms median / 5.87 ms p95, excluding audio and window
presentation; this is higher than the original Water timings below. Strong
waves cost more due to the bounded front-surface search. Quiet uses the original
search. These checks do not prove subjective motion quality or all possible
crest intersections; this remains a procedural height field, not breaking-fluid
or foam simulation.

All three full music replays also passed after this change (15,467 rendered
frames). CSV inputs were identical to the onset-corrected baseline, including
impact. All 45 sampled frames retained contrast and at least 53.3% dark pixels
under the existing threshold, with zero clipped pixels. A twelve-frame review
sheet was visually inspected. See `work/elemental/rough-sea/music/` for captures,
`review-sheet.png` and `verification.json`. The user subsequently accepted
the stronger waves and requested development of the surrounding Water world.

Final evidence: `work/elemental/final/contact-sheet.png` has silence, quiet,
active and chorus rows, with columns at 18, 67 and 180 seconds. Individual
control comparisons and landscape/portrait/ultrawide captures are alongside it.
`verification.json` contains observed sample metrics, independent
audio response deltas and GPU timings. Captures are ignored generated evidence.

Water tests cover 36 still cases, four independently varied inputs, silent
motion, short-interval continuity, 181 renderer-integrated attack/release
frames, and 360 draws across four sizes. They guard gross loss of structure,
clipping, frozen quiet and excessive frame changes. They do not establish
musical timing quality or long-run aesthetic acceptance.

On the RTX 3070 Laptop GPU, the final measured 1080p draw median was 2.761 ms,
p95 2.807 ms, using OpenGL elapsed-time queries after warm-up. This is GPU draw
work, not a claim of whole-application frame rate. At 2560x1080 the median was
3.707 ms. Existing-world comparisons passed 72 cases with at most 1/255 channel
difference. Geometric, handoff, moon and blended tests passed; see handoff.

The surface is procedural, not a Navier-Stokes simulation. Refraction offsets
the material domain; it does not trace a separate underwater scene. Dye is
re-evaluated rather than stored and advected through frame history. The fixed
composition has distant island silhouettes but no foreground shore or waterfall;
impacts reuse one local disturbance
region. Gathering here means spatial material remapping, not a timed entrance
from another world. Future transition/scheduling work needs its own review.

The resumed live launcher connected to BlackShark V3 Pro BT loopback and
rendered silence successfully. The user subsequently confirmed that the waves
look fine. Preserve this accepted wave treatment. Broader Water material and
musical-expression review remains open. Listen for event feel and
whether the dark quiet composition remains engaging across different songs.
No second element was implemented in this pass.

### Resumed three-track evidence

Full accelerated Water replay completed for Balloon (226.8s / 5,316 frames),
Chasing You (133.8s / 3,136 frames) and Warbot Jazz (299.3s / 7,015 frames).
Forty-five captures at 15-song-second intervals retained structure and dark
space with zero clipped pixels at the test threshold. A twelve-image review
sheet was inspected; the accepted waves were not edited. Evidence and the
per-track input ranges are under `work/elemental/music/`. Capture-on/off smoke
runs produced identical analyzed metrics. Replay has no audible playback.

**Impact delivery correction approved and implemented:** the first replay
found that onsets were measured after conditioning limited per-frame rises to
0.12, below the detector's 0.2 threshold. The shared live/replay function now
measures normalized transients before that visual limiter. Thresholds,
normalization and continuous controls are unchanged; the renderer's existing
impact envelope still owns decay. No shader changes accompanied this fix.

The extended onset_test.py reproduced the old failure and now passes real
synthetic-tone analysis for all bands in mono/stereo, including silence,
attacks, sustain and release. All three full Water replays were repeated and
their CSVs compared: 15,467 frames matched every pre-fix continuous value
exactly. Nonzero impact frames are now 732 (Balloon), 487 (Chasing You), and
1,193 (Warbot Jazz), with maximum strengths .4955, .4963 and .5000. These are
threshold events, not a beat-detection accuracy claim.

Forty-five periodic Water captures still passed visibility/headroom checks.
Forty-five additional event snapshots across Organic, Geometric, Cosmic canvas,
Water and blend were rendered and visually inspected in contact sheets; the
star clock remained monotonic. Geometric, Cosmic handoff and moon regressions
passed. Evidence is under `work/elemental/onset-order/`, including
`comparison.json`, `event-frames.json` and per-track `worlds-at-event.png`.
Restored impacts intentionally activate previously dormant expressions in all
worlds. Their frequency and musical feel still need live review; no silent
threshold adjustment or normalization retuning was performed.

## Remaining Elemental directions

- **Fire continuation:** the isolated flame-sheet foundation above is now implemented; further forms and integration await review. Original direction: Vertical, translucent flame sheets rise
  above a few dark coals. Remap the existing dye upward; bass widens the base,
  flux tears bounded sheet edges, sparkle reveals sparse embers, impact briefly
  exposes hot seams. Preserve cool/dark gaps instead of a full orange wash.
- **Air/Wind:** a broad bent stream through empty space, revealed by a few long
  ribbons and sparse dust. A shared directional curve should organize movement
  before detail is added; bass bends the stream, flux introduces local curls.
- **Earth:** an oblique eroded basin with stratified walls and slow dune folds.
  Use actual source material as mineral seams, bass as subtle tectonic pressure,
  sparkle as sparse crystal glints. Give sediment coherent downhill direction.
- **Fog/Gas:** separated near/middle/far banks crossing a dark opening. First
  establish depth-dependent visibility, then advect softly colored dye through
  the banks. Avoid covering every layer with the same opacity/noise pattern.
- **Plasma:** two or three anchored magnetic arches above a dark core. Fine
  filaments travel along the arches; flux bends them, sparkle branches tiny
  strands, impact releases a short bounded arc. Keep the empty space dominant.

These are starting concepts, not promised implementations or authority for an
architectural expansion. Preserve Cosmic, Geometric, Organic and their clocks.
