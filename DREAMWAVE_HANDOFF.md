# DreamWave working handoff

Updated: 2026-09-27

## Accepted Plasma checkpoint

User passed all three Plasma states and their animated skies, then explicitly
authorized this commit. The pending/uncommitted labels in the Plasma entries
below describe historical development passes and are superseded here.
Checkpoint includes Magnetic Bloom, Arc Constellation, Auroral Veil, musical
sky motion, native/Main transitions, Studio isolation controls, tests and docs.
All six Elemental families now have user-accepted foundations. Final validation
is recorded in the sky motion entry below. Unrelated untracked files are excluded.

## Plasma sky motion pass (uncommitted)

User conditionally passed all three foreground compositions and requested an
active starry background. Only the Plasma sky helper/call changed in the shader.
Two jittered star layers now rotate and drift at different depths, with musical
trail length and brightness. Magnetic Bloom applies bounded lens-inspired
inverse coordinates around its opaque core. Arc Constellation adds sparse
three-star asterisms whose links wake independently and strengthen on impact.
Auroral Veil adds coherent scintillation waves behind its absorbing curtains.
The lens is artistic distortion, not a physical gravitational simulation.
The existing Plasma particles/stars detail row still controls this background;
no UI, renderer, audio or accepted Cosmic star implementation changed.

Tests now compare all three foregrounds to the pre-sky shader with the stars
detail disabled, and separately render the three skies at multiple times to
check visible motion, distinctness and retained darkness. This revision changes
dream.frag, shader_test.py and this handoff on top of pending Plasma work.

Validation passed: 64 earlier-world comparisons, 12 Plasma foreground
comparisons with the sky disabled, nine isolated sky motion frames, opaque
core probe, 195 handoff samples, audio/detail/material checks and 150 renderer
frames. Inspected sky-only and full-scene captures, plus an 84-second /1969-frame
WarbotJazz replay across the three forms. No audible live review. 720p median
GPU samples were 10.1/7.4/4.9 ms for Magnetic/Arcs/Auroral; the sampled
Magnetic/Citadel overlap was 23.3 ms. Timing varies and is not an FPS guarantee.
Python compilation and diff checks passed. Evidence: work/plasma-sky/{final,
replay,gpu-times.json}. Everything remains uncommitted for user review.

## Plasma foundation (uncommitted, visual review pending)

Accepted Fog/Gas checkpoint is `8878ac1`. Plasma adds Magnetic Bloom (32),
Arc Constellation (33), Auroral Veil (34), and a 108-second native cycle (35).
All enter Main's existing musical director; Studio exposes Elements > Plasma
and three independently controlled detail rows. The legacy mask is unchanged;
new details follow the existing separate-uniform approach.

Magnetic Bloom projects eight curved magnetic filaments around an opaque core.
Arc Constellation uses seven moving opaque nodes, segmented discharges, branches
and traveling highlights. Auroral Veil integrates thin folded emitting sheets
front to back, preserving depth and dark gaps. Analytic sphere intersections
occlude lines behind cores; line depth uses perspective-correct interpolation.
Emission-only compression limits glare without globally desaturating worlds.
Each magnetic strand is shaded once at its nearest visible segment, avoiding
repeated glow evaluation and bright segment joints. Eight strands retain forty
segments each for smooth curves while bounding the pixel cost.
These are stylized analytic fields, not electromagnetic or particle simulation.

Integrated musical time controls orbit/travel momentum. Bass expands the field
and nodes; flux changes loop tension and emission; sparkle reveals traveling
detail; impact brightens discharges and curtain pulses. Independent seeded
electrical flickers accompany stronger music-triggered light. Existing materials
modulate pigment; spatial effects affect that source pigment, not core geometry.
Only filaments, glow and curtains intentionally transmit light. Solid bodies
remain opaque. The existing continuous star clock drives a separate Plasma
star layer; Cosmic and earlier world helper implementations are byte-identical.

Final GPU checks passed: 64 earlier-state comparisons, 195 transition samples, three
native-cycle seams, independent audio/detail/material checks, 150 renderer
frames and an opaque-core background-swap probe. Earlier-world comparisons use
the documented sparse precision tolerance from Fog plus a source-identity guard;
all 64 final reference frames in this run matched exactly.
Director CPU checks passed with repeatable seeds, frame-rate consistency and
recurring Corridor/Planet anchors. Full Studio suite passed, including saved
sessions, hierarchy, effect isolation/cycling and real renderer uploads; this
preceded the shader-only filament cost reduction, which the final GPU suite covers.

Final decoded replays: WarbotJazz native Plasma 110.037s /2579 frames; Balloon
isolated forms 84.011s /1969 frames; ChasingYou Main seed 20 64s /1500 frames
(Pressure, Citadel, Stormfront), then seed 23 48s /1125 frames (Magnetic Bloom,
Arc Constellation, Flame Sheets). Inspected capture sequences for native cycle,
second-track isolated forms and the seed-23 Main handoffs. No audible live
review. Actual replay inputs showed sustained energy, varied transients and
integrated travel rates, not just synthetic signal fixtures.

Final 720p median GPU samples: Magnetic 11.7 ms, Arcs 7.8 ms, Auroral 5.1 ms;
Magnetic/Arcs 13.8 ms, Magnetic/Citadel 27.5 ms. That heaviest tested overlap
can fall below 60 fps; these are GPU timings, not full-session FPS guarantees.
Optimization reduced Magnetic from 18.6 ms and its Citadel overlap from 36.3 ms.
Python compilation and diff checks passed. No dependencies or audio pipeline
changes. Plasma remains uncommitted for visual review; unrelated untracked
user files remain untouched. Evidence: work/plasma/{final,final-replay,second,
main-plasma,gpu-times.json}. Earlier checks/replay folders are intermediate.

## Accepted Fog / Gas checkpoint

User passed Nebula, Pressure and the finished Marsh, then authorized continuing
with the proposed Fog checkpoint and Plasma work. All Fog implementation and
refinements below are accepted; their pending/uncommitted labels are historical.
Checkpoint includes Studio isolation, material/spatial integration, native/Main
transitions, opaque Marsh headstones with weathering and moving ghostlights.
Latest verification is recorded in the Marsh finish entry below. Unrelated
untracked user files are excluded. Plasma begins after this checkpoint.

## Marsh headstone finish (uncommitted)

User accepted Pressure Chamber as well as Nebula. All Marsh markers now use
arched headstone silhouettes, with varied height/width and shallow depth;
the rectangular monument branch is removed. Surface-local marble veins,
green moss patches and branching dark cracks replace plain shading. Weathering
gradually increases with elapsed session time, with per-stone initial variation;
it saturates rather than repeatedly healing. These are opaque surface colors,
not holes or translucent layers. Fireflies, path, lights and camera are unchanged.
Only dream.frag, shader_test.py and this handoff changed in this revision.
The optional Fog reference check now includes accepted Pressure and Nebula.

Validation passed: 56 earlier-world comparisons, six Nebula and six Pressure
reference comparisons, 180 transition samples, 150 renderer frames, opacity
and 24,000 lamp-clearance samples, plus existing musical/detail/material checks.
WarbotJazz Marsh replay completed 32 seconds /751 analyzed frames; captures
inspected for headstone shapes, surface patterns and unchanged light behavior.
No audible live review. Python compilation and diff checks passed. Evidence:
work/marsh-stone/{checks,replay}. Changes remain uncommitted for user review.

## Fog refinement: Marsh and Pressure (uncommitted)

User accepted Nebula Banks. Its six quiet/active reference comparisons pass.
Marsh now mixes arched and sloped headstones with taller squared monuments.
The opaque ground has a textured central path that darkens toward its edges.
Green/amber fireflies follow independently phased darting orbits: forward
stretches briefly accompany travel, then peel away. Their lanes are clear of
the roadside solids. Musical brightness drives both larger vapor auras and
cross-shaped ground projections; projection length increases with lamp height.
These are stylized projected lights, not physically simulated reflections.

Pressure follows a continuous route between seeded twelve-point compass
offsets. Camera and gas cavity share the route; smooth interpolation produces
diagonal bends bounded below 45 degrees from forward, rather than snapping.
No global audio or accepted-world helper changes. This revision changes only
dream.frag, shader_test.py and these notes on top of the pending Fog work.

GPU suite passed: 56 earlier-world comparisons, six accepted Nebula checks,
180 transition samples, independent musical/detail/material responses,
150 renderer frames, opaque-ground probe, and 24,000 firefly/terrain clearance
samples plus route slope checks. Initial signed-power ground-light math
produced invalid pixels; corrected to nonnegative power inputs before passing.
WarbotJazz decoded replay completed 56 seconds /1313 analyzed frames, split
between Marsh and Pressure; half-second capture sequences inspected for
flybys, projections and curved travel. No audible live review. 720p median GPU
samples: Marsh 10.0 ms, Pressure 6.4 ms, their overlap 12.2 ms. Heaviest sampled
pair remained Nebula/Citadel at 21.2 ms; not a guaranteed session frame rate.
Python compilation and diff checks passed (Git reports normal LF/CRLF
conversion warnings). Evidence: work/fog-refine/{checks,replay,gpu-times.json}.
No commit authorized for this revision.

## Fog / Gas implementation (uncommitted, visual review pending)

Base checkpoint: `cc0c6af`, accepted Earth. Fog adds Nebula Banks (28),
Ghostlight Marsh (29), Pressure Chamber (30), and a 114-second native cycle
(31). Studio: Elements > Fog / Gas. All three participate in Main's musical
director and existing material/spatial controls. No audio normalization,
dependencies, or earlier world helper implementations changed.

Vapor uses 48 bounded front-to-back samples with exponential extinction,
density-gradient lighting and coherent 3D advection. Pressure Chamber uses a
gyroid-like field for connected cavities. Marsh first traces opaque ground,
rock columns and lamp cores, then stops vapor at that depth. An exact floor
intersection prevents missed ground holes. Ground reflections are procedural
lamp glows, not full scene reflections; scattering is an approximation.
Only vapor is deliberately translucent. Fog details separately controls vapor,
internal lights/ghostlights, and pressure fronts/fine filaments.

Integrated musical time drives sustained travel and coasting. Bass opens banks
and cavities and lights surfaces; flux contributes to banking and internal
lighting; sparkle reveals filaments; impact adds pressure fronts and localized
light. Materials supply restrained pigment variation rather than an overlay.

Validation passed: full Studio suite, director CPU suite, Python compilation,
diff checks, and Fog GPU suite: 56 earlier-state image comparisons, 180 handoff
samples, three cycle seams, independent audio-channel/detail/material checks,
150 renderer frames and a background-swap probe proving opaque ground coverage.
Earlier helper source is byte-identical. Expanded shader compilation causes
sparse procedural-edge pixel variance: worst mean difference .0217/255;
largest fraction of channels differing by >2 is .164%. Fog's new comparison
requires mean <.05 and outlier fraction <.25%, plus source identity. Existing
Earth/Air regression tests were not relaxed. This is not exact pixel equality.

Decoded real-track replays completed: WarbotJazz Fog cycle 116.01s /2719 frames,
Balloon Main 70s /1641 frames, ChasingYou isolated forms 84s /1969 frames.
Capture sequences were inspected; Main visited Marsh, Nebula, Vortex, Molten.
No audible live review. Evidence: work/fog/{checks,replay,main,second}.
720p GPU timing samples: isolated forms roughly 5.6-7.7 ms; heaviest sampled
overlap Nebula/Citadel 19.9 ms. These are GPU samples, not guaranteed session FPS.
Changes remain uncommitted for user review; unrelated untracked files untouched.

## Earth sky and Main integration checkpoint (2026-09-27)

User authorized the Earth commit after improving skies and blending. This
entry supersedes the pending/uncommitted labels in the historical entries below.
Dunes now has a warm dusk sun, drifting cloud bands and a sparse night sky.
Strata has cooler clouds, stars and musical auroral curtains above its canyon.
Sky is evaluated only for rays that miss solid terrain. Stars use the existing
continuous star clock and the existing stars isolation ID, now available in
Earth's catalog; Cosmic's star implementation is unchanged.

Earth participates in Main's existing musical director, material-trio cycle,
and shared spatial effects. Pigment responds more visibly on opaque terrain;
worm coverage stays a material canvas. Sharper native regional ownership
reduces the time spent showing overlapping geological surfaces. Earlier
world composition and audio mapping are preserved. This checkpoint includes
all three Earth forms, Studio controls, shader/renderer integration and tests.

Validation: final GPU suite passed 48 earlier-world image comparisons at the
original strict tolerance, two sky-star isolation checks, 18 material/detail
checks, 135 handoff samples, worm lifecycles, cave enclosure, and 270 renderer
frames including musical acceleration/coasting. Full Studio and director
CPU suites passed. Python compilation and diff checks passed.

Decoded WarbotJazz replays completed: Earth cycle 110.037s /2579 frames and
Main seed 2 55.04s /1290 frames (Strata -> Cavern -> Aftershock); captures
were inspected. These replays preceded the final sky-only isolation change;
final sky/form/material/handoff captures were then inspected separately.
No audible live review. Evidence: work/earth-blend/replay, main and final.
Adding another shared Cosmic-star call caused shader code-generation pixel
variance in older worlds. Earth uses its own lightweight star layer instead;
the original regression tolerance was preserved and all comparisons passed.
No dependency/audio changes. Unrelated untracked user files are excluded.

## Earth musical motion pass (uncommitted, visual review pending)

User approved the direction but found every Earth form crawling. Earth now
converts integrated music time into 3.0 travel units instead of 0.9; the
existing renderer clock still provides sustained acceleration and smooth
coasting. No global clock, mapper or audio normalization was changed.
Dunes have stronger bounded bass waves and more frequent low worm breaches.
Strata adds bass pressure to its existing folds; all Earth cameras bank more
strongly with flux. Cavern crystal flex remains small and cell-safe. Mineral
accents and glints respond more strongly to sparkle/hits, and local detail
flow runs faster. Quiet passages keep positive travel and subdued emission.

Validation: final Earth GPU suite passed 48 earlier-world comparisons,
18 effect/material checks, 135 handoff samples, cavity enclosure and worm
lifecycle checks, plus 120 renderer frames and 150 additional frames testing
quiet-to-sustained-energy acceleration and positive coasting on release.
The glint test samples several camera positions because glints are sparse;
its failure exposed precision loss in large world-coordinate hash inputs,
now bounded locally without altering shared hashing or other worlds.
A 110.037s /2579-frame decoded WarbotJazz Earth replay completed and captures
were inspected across all forms/transitions (before the isolated glint hash
fix). Observed travel range was approximately 2.0-8.1 world units/second.
No audible live review; user visual review remains the next step. Evidence:
work/earth-energy/replay and work/earth-energy/final. Python compilation and
git diff --check passed. All Earth changes remain uncommitted.

## Earth solidity revision (uncommitted, user review pending)

The user found the previous pass still translucent. This revision reduces
broad material overlays to mineral seams, reduces distance haze, reveals the
cavern enclosure with directional/view lighting, and replaces screen-space
dust with tiny world-coordinate mineral glints. The existing earth_dust
session ID is preserved; its display name is now Surface mineral glints.

The worm has a lower, longer breach (3.4 amplitude instead of 7.5), a cool
opaque body, and a wrapped shared-material canvas instead of brown banding.
Cavern mineral clusters vary height, width, occupancy and lean; ceiling
formations vary length/radius and extend their roots into the enclosing rock.
Cluster extents stay inside their procedural cells. Cave travel is 35% faster
using the existing integrated musical clock, with a gently curving passage.
No global audio tuning changed. Distance-aware surface tolerance prevents
near-hit rays becoming background holes at grazing angles.

Final shader verification passed: 48 previous-world image comparisons,
18 detail/material checks, 135 handoff samples, 12 worm lifecycle captures,
four cavity probes checking >93% overall enclosure and >98% ceiling/sidewall
coverage, and 120 renderer frames. Saved earth_dust isolation ID and Python
compilation passed. A 110.037s /2579-frame decoded WarbotJazz Earth replay
was inspected before the final root-extension/worm-lighting adjustment.
Final adjustment replay also completed and captures were inspected: 56.0s /
1313 frames of Dunes then Cavern, in work/earth-solid/final-replay. These
are decoded music replays without audible playback.
Evidence: work/earth-solid (final GPU results in final/). Full Studio suite
was not rerun for this shader/display-label revision; isolation was checked
directly. Audio normalization and accepted earlier worlds remain untouched.

## Earth: three connected geological forms (uncommitted, visual review pending)

User authorized completing the next element. Base checkpoint e1f10cd is accepted
Air integration. Earth adds Dune Sea (24), Folded Strata (25), Crystal Cavern (26)
and the native 108-second Earth cycle (27). Main director includes all three;
Studio exposes Elements > Earth > form. No changes to audio normalization,
window lifecycle, dependencies, or renderer architecture.

The existing fragment shader traces bounded procedural terrain: low dune flight,
curved canyon walls with sediment/erosion, and a cavern with seeded hexagonal
mineral clusters. All use the integrated musical clock for uninterrupted travel.
Dunes respond with broad pressure; bands bend and mineral veins/crystals reveal
short impact accents. Quiet motion persists. Materials gather onto terrain and
spatial effects pull pigment/detail coordinates without tearing depth geometry.
Regional coverage handles native form and Main handoffs. Existing background
weights are normalized only for compositing, retaining actual geometry weights.

Follow-up requested by the user: stronger solid surfaces, a giant breaching
sand worm, diverse cavern minerals and hanging/rising cave formations.
Pigment now modulates rock albedo under directional/contact shading. Dunes
have a segmented, open-mouthed creature on a seeded breach/dive trajectory;
it is entirely buried before relocation. Strata is wider with eroded ledges
and intermittent stone bridges. Cavern includes varied mineral hues, needle
and block profiles, and opaque limestone stalactites/stalagmites.

The signed effect mask was already full. Four Earth-detail catalog rows have
BITS=0 and upload through u_earth_details, preserving every old bit/ID. Authored
enables all four; explicit lists/cycles honor enabled rows. Sand worm is in
Earth inhabitants and only changes Dune Sea. Saved custom lists
do not silently acquire new details. Daddy Long Legs remains inactive by default.

Validation executed: Earth GPU suite passed 48 old-world comparisons (authored
and custom states 0-23, max 1/255 channel tolerance and mean <.005), 18 detail /
material checks, 135 handoff samples, three cycle-boundary checks and 120 actual
renderer frames. Director CPU checks passed, including musical opportunities,
repeatability, frame-rate stability and favorite anchors. Studio suite passed
selection, session roundtrip, explicit Earth detail cycling/uploads, launch modes,
UI lifecycle, real replay pacing and forward GPU clocks. Python compilation and
diff check passed. Existing Air/Water/Fire/Cosmic/Organic geometry is preserved.

WarbotJazz replay: Earth cycle 110.037s / 2579 analyzed-rendered frames, Main seed
2 55.04s /1290 frames. Captures inspected across all three Earth forms, native
handoffs and Main Strata -> Cavern -> Aftershock. This is decoded-music GPU
replay, not audible live review. Evidence: work/earth, final GPU suite in
work/earth/final-checks. Initial terrain march had distant gaps; conservative
128-step tracing and distance haze corrected the visible horizon discontinuity.
Procedural terrain is a stylized foundation, not a physical erosion simulation;
crystals have faceted opaque shading rather than true refractive ray transport.
Short 720p GPU samples: held Earth scenes 8.6-9.3ms median, Earth pairs 9.3-9.8ms,
Cavern/Citadel overlap 14.7ms. These are sampled GPU timings, not guaranteed
full-session frame rates. Timing evidence: work/earth/gpu-times.json.
Follow-up verification: reran the Earth GPU suite with the final creature and
solid-surface shading, including 12 worm lifecycle captures (two breaches),
exactly unchanged buried intervals, and an explicit worm-off comparison.
48 earlier-world frames, 18 existing detail/material checks, 135 handoff
samples and 120 renderer frames passed. The full Studio suite passed with
four-component Earth details, worm-only isolation and default enablement.
A fresh 110.037s / 2579-frame decoded WarbotJazz replay ran with all three
materials and 1.5-second captures; inspected worm rise/dive, canyon bridges,
mineral/cave geometry and native transitions. Evidence: work/earth-life/final
and work/earth-life/replay. A fresh Main seed-2 replay also passed: 55.04s /
1290 frames, inspected Strata -> Cavern -> Aftershock. Captures are in
work/earth-life/main. No audible live playback was performed.
Short 720p GPU samples with a visible worm: Dunes 10.5ms, Strata 9.1ms,
Cavern 6.4ms, Earth pairs 7.8-10.1ms, Cavern/Citadel 15.7ms. Samples are
scene-dependent and not full-session performance guarantees.
User visual acceptance and a commit are still pending.

## Accepted Air material and transition integration

User visually accepted this pass and explicitly authorized its commit.

Base checkpoint c552f81 is accepted Air. This pass applies Water/Fire's regional
coverage approach to Air: wind sweeps, storm passage, central vortex and lower
planet territories. Air forms render with their own camera/depth and exchange
coverage, rather than interpolating unrelated scene geometry. Raw form weights
still gather the shared material coordinates continuously. Main's outer Air
handoff uses the same form-specific territories. The existing director is unchanged.

In Main or explicit effect playback, Windstreams gathers materials into its
flight projection, cloud interiors and balloon fabric. Stormfront carries
materials in lit cloud regions and lets the existing spatial carrier fold cloud
detail coordinates. Vortex and Citadel retain their accepted material mapping.
Castle depth, balloon silhouettes, lightning roots and star clocks are unchanged.
Held Authored forms remain the comparison view; the Air native cycle receives
the new regional handoffs. Daddy Long Legs stays inactive by default.

Validation: Air GPU suite passed 57 preservation comparisons (46 authored frames
within one 8-bit level / mean <.005, 11 custom non-Air frames exact), 36 material/
spatial-effect visibility checks, 140 handoff checks, 244 production-renderer
frames, and the existing lightning/eye/history checks. Initial exact authored
comparison exposed sparse one-level GPU rounding differences; tolerance is now
explicit. Director CPU suite passed. WarbotJazz replay: full Air cycle 145.024s /
3399 frames and Main seed 0 65.024s /1524 frames. Captures inspected across all Air
handoffs and Windstreams-to-Firescape in Main. Replays use decoded music and GPU
rendering, not audible live playback. Evidence: work/air-meld. No audio pipeline,
normalization, renderer interface, Studio catalog or dependency changes.
Short 720p GPU timing samples: current held scenes 9.3-13.1ms median; sampled
overlaps 10.8-17.4ms. Citadel-to-Windstreams increased from 16.2 to 17.4ms in
this sample; not a full-session frame-rate guarantee. Final diff check passed.

## Accepted Air checkpoint

User accepted the final inner-rim lightning correction and explicitly authorized
committing the accumulated Air work. Windstreams, Stormfront, Vortex and Sky
Citadel are integrated in Main Blend and Studio. Daddy Long Legs remains an
inactive, opt-in FX experiment. Earlier "uncommitted" and pending-review entries
below describe the development history, not the acceptance status of this checkpoint.
Final Air validation: 44 preservation frames, 140 handoff checks, 244 renderer
frames and 16 eye-exclusion comparisons. No audio normalization changes.
Final Studio suite also passed: selection, effect lists, sessions, launch modes,
UI lifecycle, replay metadata/pacing and continuous GPU clocks.
Unrelated untracked research folders and root scripts are excluded from the commit.

## Vortex inner-rim root correction (uncommitted)

The .24 origin plus .23-.28 clearance left an unwanted gap between the eye
and free lightning. Match the original hit bolts' .08-.14 onset instead:
root at .08, gradual .06 reveal and tapered initial lateral jitter. Growth
remains outward only. Wall lightning and all other behavior unchanged.
The direct-Air exclusion test now checks the actual protected .075 inner disk,
not the former .20 region that included the desired lightning root. Air suite
passed: 44 preserved frames, 140 handoffs, 244 renderer frames and 16 eye checks.
Synthetic motion captures inspected at work/vortex-root/checks show the root
at the inner rim; live review remains for the user. Shader, test and handoff
changed this pass. No commit made.

## Vortex foreground origin correction (uncommitted)

The bottom-of-screen origin was a misinterpretation. Free jagged lightning now
starts .24 units outside the moving eye and grows radially outward, with a new
direction each lifecycle, like the existing transient bolts. Its clearance mask,
color, forks and fade remain. Wall lightning is unchanged. Only dream.frag and
this handoff changed this pass. Air tests passed (44 preserved frames, 140
handoffs, 244 renderer frames, 16 direct-Air eye comparisons). Synthetic motion
captures inspected in work/vortex-rim/checks; no new music replay or live review.
All work remains uncommitted.

## Vortex rising foreground lightning (uncommitted)

User requested keeping wall lightning while restoring the earlier free jagged
look, growing from bottom to top without crossing the eye. Added one independent
foreground discharge with alternating left/right detours, thin forks, evolving
hue and complete lifecycle fade. It uses screen coordinates, not wall rotation
or ridge shading. Radius .23-.28 clearance also masks inward forks/glow.
Wall lightning, original hit bolts and Daddy Long Legs remain unchanged.

Air suite passed: 44 exact non-Vortex frames, 140 handoff checks, 244 renderer
frames and 16 direct-Air eye checks. WarbotJazz replay completed 16 seconds /
375 frames; half-second captures inspected for upward growth, side routing and
fade. No audible live review. Shared spatial compositing caveat below remains.
Evidence: work/vortex-rising. This pass changes only dream.frag and this handoff.
Diff check passed; cumulative Air work remains uncommitted at HEAD 77d767e.

## Vortex wall lightning refinement (uncommitted)

Secondary lightning now starts at radius .28-.35 on the walls and curves around
the eye in polar coordinates. Hot pale cores, colored local glow, irregular thin
forks, stepped growth, traveling charge pulses and staggered decay replace the
straight crossing discharges. Ridge shading suggests partial obstruction; this
is procedural surface integration, not volumetric geometry. Original hit bolts
and dormant Daddy Long Legs are unchanged. No audio or renderer changes.

Air suite passed: 44 exact non-Vortex frames, 140 handoff checks, 244 renderer
frames and 16 direct-Air eye-exclusion comparisons. Initial full-composite eye
comparison failed; the focused test probes Air before shared spatial/material
compositing, so it does not guarantee exclusion after arbitrary spatial effects.
The probe initially needed an optimized-out uniform guard, now corrected.
WarbotJazz GPU replay completed 20 seconds / 469 frames; half-second captures
reviewed show wall-following bright channels and clear central space. No audible
live review performed. Evidence: work/vortex-wall. Diff check passed. Current
pass changes dream.frag, shader_test.py and this handoff; all work uncommitted.

## Vortex discharge correction / Daddy Long Legs experiment (uncommitted)

User rejected the crawling web as lightning. Preserve it under the exact name
Daddy Long Legs, category FX experiments (Air / Main catalog), inactive by default.
Its code is retained behind u_daddy_long_legs. Authored profiles and automatic
material-trio profiles do not enable it; explicit add/enable or cycle selection
can preview it on Vortex. The 31 positive signed-mask bits are already occupied,
so this experimental row has BITS value 0 and a separate uniform. Existing effect
IDs/masks stay unchanged. Do not silently include experiments in default presets.

The active replacement uses the existing jagged bolt vocabulary: anchored
discharges extend outward over their lifetime, progressively reveal thin forks,
rotate color and fully fade before their next lifecycle. Two staggered discharges
can overlap. Original hit-driven bolts and their fading residue are preserved.
No moving hubs or legs are active in normal Vortex playback.

Air suite passed 44 exact non-Vortex frames, 140 handoff checks, 244 renderer
frames, lightning history/isolation, and opt-in Daddy Long Legs rendering.
Studio suite passed, including experiment defaults, cycle selection, session
roundtrip and renderer switch. WarbotJazz replay completed 25 seconds / 586
analyzed-rendered frames. Half-second captures show extending jagged branches,
changing hues and fading discharges with no active spider hubs. This was a
decoded-music GPU replay and capture review, not audible live playback.
Evidence: work/vortex-discharge. Work remains uncommitted at HEAD 77d767e.

## Vortex crawling lightning web (uncommitted)

The secondary electrical layer now has three independently moving junctions,
each orbiting and diving inward/outward. Five curved strands per junction include
a connection to the next junction, fine forks and restrained local glow. Shared
segment vertices keep the web connected while it jitters. Hue travels through
the strands over time. The dark eye remains open; brightness follows existing
energy and afterglow. Original transient bolts and historical residue remain.
The web is evaluated only for Vortex with lightning enabled. No renderer or
audio changes in this pass; all other held scenes should stay exact.

WarbotJazz replay completed 42 seconds / 985 analyzed-rendered frames, captured
sequences inspected. Final connecting strands/glow refinement inspected separately
in GPU captures. Short final 720p Vortex sample: median 10.44ms, maximum 10.81ms
(GPU only, not live FPS). Evidence: work/vortex-web. No audible playback claimed.
Still uncommitted at HEAD 77d767e.
Final Air suite passed 44 exact non-Vortex reference frames, 140 handoff checks,
244 renderer frames and lightning isolation/history checks. Python compile and
git diff --check passed. Changes: dream.frag, shader_test.py and this handoff.

## Air skies and island support (uncommitted)

Windstreams balloons now have logarithmic inward-traveling fold waves in their
rotating fractal texture, with additional color moving through those folds.
Thin horizontal stratus joins the existing cumulus. Planet Canvas's drifting
star sheets are shared through cosmic_star_layer: the original Cosmic call uses
boost=1, while Windstreams adds beat/energy-driven elongated wakes. Citadel adds
the same Cosmic sheets alongside its existing pinpoints, behind castle/planet.
The existing stars effect is now available under Air, with stable bit IDs.

Vortex's inkblot/shadow and its local glow are removed. A persistent warm orange/
magenta arc layer travels independently around the cool transient bolts and
their bounded glow history. The lightning control is now named Lightning &
lingering arcs. Stormfront stays unchanged. Citadel island upper radius increases
from .78 to .94 (about 21%) to support the outer towers; its tracing and castle
geometry are otherwise retained from the prior pass.

Validation: final Air suite passed 40 exact preservation frames (non-Air plus
Stormfront), 140 handoff checks, 244 renderer frames and Air star-toggle isolation.
Studio suite passed recursive forms, layer controls, sessions, launch modes,
layout/lifecycle, replay metadata/pacing and continuous GPU clocks. WarbotJazz
replayed 84 seconds / 1969 analyzed-rendered frames across Windstreams, Vortex
and Citadel; sequences inspected. The final filled Windstreams wake refinement
was additionally inspected in GPU captures. No audible playback claimed.
Evidence: work/air-sky. Work remains uncommitted at HEAD 77d767e.
Short final 720p GPU medians: Windstreams 12.42ms, Stormfront 10.78ms,
Vortex 9.61ms, Citadel 13.48ms; maximum 14.08ms. These are GPU samples,
not live end-to-end FPS guarantees. Python compile and git diff --check passed.

## Air motion and stability follow-up (uncommitted)

Balloon bobbing is roughly 2.3-2.6 times larger, retaining individual phases and
amplitudes. Vortex main bolts are thicker, fine forks extend farther, and glow
decays at 0.9/second. Three bounded previous-event trails retain their own seed
and strength when a new bolt fires; new hits never wait for prior glow to clear.
The lightning switch disables current and historical glow together.

Castle investigation: eight-angle captures and a slower reference trace showed
small missed/shaded pixels rather than broad missing geometry. The displaced
rock field now uses a conservative distance estimate, the main trace uses smaller
steps and a tighter consistent hit threshold, and brick/window edges use pixel
footprint filtering to reduce shimmer. Stormfront's far trace cutoff fades into
the background to soften the connection artifact. Preserve these distinctions:
this addresses observed trace precision/detail aliasing, not proof that every
live flicker reported by the user has been identified.

Final Air suite passed 38 exact non-Air frames, 140 handoff checks and 244 renderer
frames, plus independent historical-glow rendering, isolation, fresh-hit history
and decay checks. The empty bridge probe now checks positive distance rather than
its old magnitude because conservative rock distance scaling changed that value.
Python compilation and git diff --check passed. Evidence: work/air-stability.
HEAD remains 77d767e and the work remains uncommitted for user review.
Post-change castle captures inspected at the same eight angles. ChasingYou replay
completed 56 seconds / 1313 frames across Citadel and Vortex; sampled sequences
inspected, with no audible playback. Short 720p GPU medians: 11.10ms Windstreams,
10.70ms Stormfront, 9.00ms Vortex, 11.20ms Citadel; overall maximum 12.34ms.
These timings exclude end-to-end live playback overhead. User confirmation of
the reported live castle/base clicking is still needed.

## Air character follow-up (uncommitted)

Windstreams: balloon texture coordinates now wrap around the envelope and rotate
at distinct signed speeds. Per-balloon phase/amplitude varies bass bobbing and
impact displacement; flight depth continues independently.

Stormfront: mirrors the cloud vault beneath its flight axis, removes farmland,
and replaces Air's right-angle junction selection with a smooth sinusoidal
centerline (maximum heading atan(.98), about 44.4 degrees). Original non-Air
corridor calls remain unchanged. Vortex gets an extra lightning branch and a
separate renderer-side afterglow envelope (1.7/second exponential decay), painted
onto the spiral ribs while sharp bolts continue to follow independent paths.
The existing lightning switch disables both bolts and residue.

Citadel: subtle masonry weathering/courses and recess shading; the central cone
is animated colored enamel with music-reactive tracery. Castle ray bounds and
iteration allowance are expanded and tracing starts earlier to address island
base clipping during rotation. Existing gate and tower laser depth tests retained.

Evidence: work/air-character. WarbotJazz replay completed 112 seconds / 2626
analyzed-rendered frames, and captured sequences for all four forms were inspected.
No audible playback or full-speed smoothness acceptance is claimed. Changes are
still uncommitted; no global audio normalization or new dependency changes.
Final Air suite passed: 38 exact non-Air reference frames, 140 handoff checks,
243 renderer frames, afterglow persistence/decay and effect isolation, quiet/active
scene checks and castle probes. Python compile and git diff --check passed.
The broader Main suite was not rerun for this targeted follow-up; Air handoffs
to existing worlds were tested. Prior Main results remain documented below.

## Air depth, vault and celebration refinement (uncommitted)

Latest user brief authorizes refinement of all four Air forms, including Vortex.
This supersedes the older Vortex-exact requirement below. HEAD remains 77d767e;
all Air work is still uncommitted for visual review.

Windstreams: faster depth travel using the existing integrated music clock,
occasional near balloon lanes, larger envelopes with rounded highlights, broad
ribbon bends, irregular cloud edges and softened/warped field boundaries.
Castle remains absent. Captures show approach, expansion and below-camera exits.

Stormfront: the existing corridor function now has an Air-only vault argument.
The original one-argument entry point retains its exact geometry. Air has curved
arches, a lowered floor, continuous angular cloud coordinates across wall/roof,
aurora within the vault and spatially bounded lightning. Landscape extends below
the cloud walls rather than being restricted to a corridor floor. This is still
procedural surface shading, not a volumetric cloud simulation.

Vortex keeps its eye and spiral identity, with varied ribs, traveling saturated
arcs and more visible source material. Citadel has a modest camera approach,
rougher attached earth, coordinated window waves, paired sweeping laser fans
with quiet intervals, burst cores, varied ember decay and secondary spark splits.
Planet material uses surface depth to cover more of the visible globe. Tower
beam depth and emitter-obstruction checks remain intact.

Validation: final Air suite passed 38 exact non-Air reference frames, 140 Air
handoff checks, detail isolation, quiet/active comparisons, gate geometry probes
and 240 production-renderer frames. Added a Stormfront black-coverage regression
after an intermediate negative-base power caused invalid pixels; corrected it.
Main suite passed 114 exact reference frames (no rounding differences), 144
transition checks, director checks and 721 production-renderer frames. Python
compile and git diff --check passed (existing CRLF notices only).

WarbotJazz and Balloon each replayed 112 seconds / 2626 analyzed-rendered frames,
with one-second captures inspected across all four forms in different orders.
Balloon includes the final planet mapping and firework splits; Warbot predates
those last two refinements. Handoff capture strips also inspected. These runs
have no audible playback; sampled sequences do not establish full-speed visual
smoothness or live beat-sync acceptance. Evidence: work/air-depth. No changes
to global audio normalization, dependencies, or the renderer lifecycle.
Final 720p GPU sample medians: Windstreams 9.98ms, Stormfront 10.20ms,
Vortex 9.22ms, Citadel 10.76ms; maximum 11.30ms across these short samples.
GPU timing is not an end-to-end live frame-rate guarantee.

## Air corridor and Citadel corrections (uncommitted)

User accepted Vortex and requested targeted changes to the other three forms.
Windstreams now has no castle or mountain silhouettes. Balloon depths extend
to 64 units with seeded lateral spread, tiny distant starts and a flight path
slightly above their tops; nearby balloons grow and pass below. Distant farmland
fades into haze to avoid the previous hard projected horizon strip. Patchwork
remains under Windstreams and Stormfront rather than fading entirely to ocean.

Stormfront now calls the accepted geometric_surface corridor projection/turn
function and shades its walls/ceiling as cloud surfaces. Lightning and local
illumination live in wall coordinates instead of a free screen-space cross;
the roof carries moving auroral cloud color. Vortex retains its prior flash,
palette and geometry exactly. Reference inspiration: Epic's storm-cloud/local
illumination example (https://dev.epicgames.com/documentation/unreal-engine/07-adjust-environment-lighting-features)
and Guerrilla's cloud-shape/lighting overview (https://www.guerrilla-games.com/read/the-real-time-volumetric-cloudscapes-of-horizon-zero-dawn).
No external shader/assets/dependencies copied or installed.

Citadel: removed battlements intersecting the central cone; removed bridge and
fitted an opaque paneled gate inside the existing arch. Earth base is part of
the same 3D distance geometry as the castle, meeting its ground plane, with
layered stone and grass. Cotton-candy base removed. Window hues cycle by window
and time. Lasers originate in 3D on tower tops, compare beam depth against the
castle/island surface, and check obstructions from each emitter. Fireworks now
have a 28%-of-lifetime comet ascent before bursting; distant burst trails stay
behind the castle. Effect label is Castle, earth & celebration; stable ID retained.

Checks: Air suite passes 40 exact original/Vortex frames, 140 handoff checks,
240 production-renderer frames, temporal scene checks, closed gate/solid wall/
empty former bridge GPU probes, and castle-removal checks for Windstreams,
Stormfront and Vortex. Warbot replay completed 84s / 1969 frames; captured
sequences inspected. Final refinement lowered the flight path nearer balloons
and retained more farmland contrast, checked by the same suite. No audible
live-loopback acceptance claimed. 720p GPU sample before that final refinement:
median 10.36ms Windstreams, 10.12ms Stormfront, 9.06ms Vortex, 8.98ms Citadel;
maximum 10.96ms. This is GPU work, not guaranteed live FPS. Evidence:
work/air-corridor. HEAD remains 77d767e, Air work uncommitted for user review.

## Air flight and dimensional Citadel rework (uncommitted)

User reviewed the four Air foundations as too static and explicitly authorized
rebuilding their motion/composition. HEAD remains 77d767e; all prior Air work is
preserved except the specifically replaced flat castle/crystals/baskets.

Castle now uses bounded 3D distance geometry in the existing fragment shader:
round gate towers, courtyard walls/merlons, central keep, true arched gateway,
lowered bridge and rails, surface normals, masonry and window lighting. Camera
orbits continuously. Its base is opaque swirling cotton-candy cloud lobes;
crystals removed. Windstreams retains only a tiny distant silhouette. Stormfront
and Vortex contain no castle. Scanning laser rays reach the frame edge and pulse;
six staggered fireworks have 24 radial stars with segmented ballistic tails.
The backdrop stars drift and the globe radius is now 5 rather than 1.18, with
a wide shallow horizon. Citadel and Vortex remap the existing material/spatial
field before generation, instead of just tinting a separate painted surface.
Accepted Planet Canvas geometry/rendering remains untouched.

Windstreams uses far-to-near depth planes: balloons grow, overlap correctly and
pass offscreen; sphere shading, fractal coordinates and hue rotate, with no
baskets/ropes. Clouds grow around the flight path; streamers converge at the
castle with traveling pulses. Ground patches drift and turn below. Stormfront
flies a banked winding lane through successive pairs of rotating tornado
columns, retaining onset lightning/shadow identity. Vortex rotates faster,
cycles its own palette and carries more of the shared material.

The first Air handoff test exposed Vortex-to-Corridor material discontinuity:
non-Air geometry had been normalized to full weight too early. Renderer now
retains absolute geometry weights and shader normalizes only final background
composition. The corrected Air suite passes 38 exact original-state frames,
140 handoffs, 240 renderer frames, four temporal motion sequences, GPU probes
of open gateway/solid wall/bridge, and exact castle-removal checks in Stormfront
and Vortex. Main regression passes 114 exact frames, 144 handoff checks and
721 renderer frames. Real Warbot replay rendered 112s / 2626 frames; all sampled
sequences inspected. Final globe coordinate correction also passed Air suite.
No live-loopback listening claimed. Python compilation and whitespace checks
passed; CRLF conversion notices only. Evidence: work/air-flight.

720p GPU timing probe (20 measured frames per held state after warmup): median
9.85ms Windstreams, 10.60ms Stormfront, 9.13ms Vortex, 10.09ms Citadel; maximum
11.34ms across samples. This measures GPU work, not guaranteed live frame rate.
Final image inspection replaced angular tooth cutoffs with box-shaped merlons
to avoid distance-tracing artifacts along castle battlements.

Reference direction: National Trust's Bodiam gatehouse/bridge photograph
(https://ntprints.com/products/pod1044593) and PBS's chrysanthemum/willow examples
(https://www.pbs.org/a-capitol-fourth/fireworks-fun/firework-names/).
No reference images are bundled in the project. Pending user review, no commit.

## Air / Wind: four connected sky forms (uncommitted)

Starting checkpoint 77d767e was clean except unrelated untracked research/helpers,
which remain untouched. User authorized three Air forms plus a Sky Citadel reveal.
States: 19 Windstreams, 20 Stormfront, 21 Vortex, 22 Sky Citadel, 23 Air cycle.
Studio: Elements > Air / Wind; blank form runs a 144-second evolving cycle.
All four held forms also participate in Main's musical director. Legacy fixed
blend fixtures remain unchanged. Air weight/form uniforms normalize the old
background before regional coverage; original pure scenes remain identical.

Windstreams has gust ribbons, fractal balloons at varying depths, wispy clouds,
faint patchwork farms/ocean, mountain silhouettes and a distant castle landmark.
Stormfront tightens with energy, with branching lightning/coils, localized hit
illumination and changing inkblot shadows. Fresh onset serials hold each shadow
identity through its decay. Vortex has tighter spiral walls and fine colored
filaments around an eye. Sky Citadel reveals towers/windows on a floating rock,
faceted crystals, aura, lasers and fireworks above a curved material-colored
planet. No people. These are layered procedural illustrations, not volumetric
fluid simulation or a fully modeled castle. Its globe is a separate composition;
accepted Planet Canvas and continuous star drift are unchanged.

Four Air detail groups isolate clouds/ribbons, balloons, lightning/shadows and
castle/celebration. Existing material trio is available. IDs occupy bits 0-30;
future details must account for the signed 32-bit shader mask limit.

Tests: Studio UI/session/selection/effect and real replay suite passed. Main
regression passed 114 exact original frames, 144 handoffs and 721 renderer frames,
including director checks. Final Air suite passed 38 exact original-state frames,
140 handoffs, quiet/active/hit response, detail removal, changing flash identity
and 240 production-renderer frames. Initial Windstreams response failed; stronger
gust/buoyancy/highlights corrected it. Image review caught a cloud wrap seam;
periodic coordinates fixed it. Warbot replay: 112s / 2626 frames through held
scenes, then 145s / 3399 frames through native meld; captured sequences inspected.
Final GPU review additionally differentiated billowy Stormfront from Vortex and
strengthened fleeting shadows. No audible live acceptance claimed. Evidence:
work/air. User visual review pending; no commit authorized for this Air pass.

## Checkpoint: accepted color, Water handoffs and reactive Fire

The user authorized committing these accumulated passes after correcting
Firescape's mid-song slowdown. Historical "uncommitted" / "review pending"
statements below describe each pass at the time; this checkpoint supersedes them.

Firescape now supplements shared-clock scrolling with integrated missing travel
from sustained bass/mids/highs energy, using a .25s attack and 3s release. This
prevents low flux or brief band dips from draining scene momentum. The extra
travel is confined to scenery scroll; other world clocks, star drift, audio
normalization and tree/building lifecycle timing are unchanged. One shader
uniform extends the existing renderer interface; zero preserves static fixtures.

Validation: Fire expression test passed, including sustained bass, half-second
dip retention, settling after silence, onset timing and 60 GPU handoffs. Main
regression passed 102 exact reference frames, 144 transition checks and 721
renderer frames. WarbotJazz replay completed 28 seconds / 657 analyzed frames;
Firescape captures inspected. These are synthetic and recorded-audio checks,
not a claim of audible live verification of this final adjustment. Prior user
acceptance covers the remaining color, Water and Fire changes. Only renderer.py,
dream.frag, shader_test.py and this handoff belong to this checkpoint; unrelated
untracked research and root test/helper files remain untouched.

## Fire timing and motion follow-up (uncommitted)

User accepted the reactive Fire pass and requested faster Firescape, taller/wider
plumes, and tighter flash alignment. Firescape's integrated audio travel coefficient
is now .070 (was .038); steady drift and lifecycle behavior are preserved. Live
Aftershock plumes continue rising at .50 age units (was .32) and widening at .065
(was .028), with accepted scattering, decay and diagnostic fallback growth intact.

Blast births now require a fresh detected onset: strong hits can qualify directly,
otherwise three onsets accumulate. Cooldown expiry and the old ten-second quiet
fallback can no longer trigger off-hit flashes. The existing 1.5-second cooldown,
eight-site cap and twenty-second lifetime remain. No audio normalization changes.

Validation: existing Fire expression test passed with new queued-hit, quiet and
sustained-input timing assertions, 49 bounded births and 60 GPU handoff checks.
WarbotJazz accelerated replay rendered 56 seconds / 1,313 analyzed frames; captured
Firescape/Aftershock sequences inspected. Replaying its recorded impacts produced
12 blast births, all on detected onset frames. This checks detector alignment,
not audible live playback latency or BPM-grid synchronization. Blend regression
passed: 96 exact preserved frames, 144 transition checks and 721 renderer frames.
Git diff whitespace check passed (repository CRLF conversion warnings only). HEAD remains
907f613; earlier accepted uncommitted work is preserved.

## Reactive Fire and within-Fire handoffs (uncommitted)

User accepted Water handoffs and explicitly requested stronger response across
all four Fire forms. HEAD907f613 remains the checkpoint; approved color/Water
passes are still uncommitted. This pass changes dream.frag, renderer.py,
shader_test.py and these notes. No audio analysis, dependencies, world director,
Water/Cosmic/Organic/Geometric geometry or continuous star-clock changes.

Flame sheets: energy controls height/width from a near-extinguished hearth to
frame-filling sheets; stronger flux/energy curl and tip deflection, faster travel,
more saturated crimson/amber/violet edges. Existing white-blue ignition is kept,
with the warm bed's slow independent rhythm. Molten: pressure/impact opens wider
channels, exposes liquid through crust, brightens seams, and accelerates branch
lifecycles via the integrated clock. Existing camera orbit remains. Firescape:
scroll and tree/building lifecycles use integrated u_time plus a small steady
clock, so existing smoothed audio acceleration/coasting changes travel and age
without multiplying elapsed time by instantaneous amplitude.

Aftershock: plume height keeps growing through life; stems/skirts dissipate and
cloud edges become less solid. Births use three distinct hits instead of four,
minimum1.5s and eight-live-site cap retained; hit rings allow2s instead of3s and
rotate across available sites via a serial counter. Twenty bounded candidate
sites are scored for both world and projected separation. Wider lateral/depth
range spreads events instead of repeatedly choosing neighboring random sites.
This reduces overlap but is not a geometric no-overlap guarantee. Depth sorting,
per-site hue, horizon curve, aurora and the existing inversion flash remain.

fire_coverage adds normalized regional blending between all four forms in Main;
the native three-form Fire cycle uses the same composition. Each pure form keeps
its own route. This is soft regional composition, not physical geometry morphing.

--fire-expression-test passed: quiet/medium/full GPU samples of all four forms,
white-glare bounds,60 handoff continuity checks (12 directions), and120s of
synthetic event updates. Flame lit coverage2.3% quiet versus99.8% full; molten
mean brightness about2.2x under full versus quiet input at the fixed sample.
49 event births, minimum sampled world-site separation10.32, at most eight
sites/rings. These are test observations, not global guarantees. Existing Main
suite passed84 exact non-Fire Authored frames,144 transition checks,721 actual
renderer frames and director CPU checks. All five Fire states intentionally
excluded from exact preservation. Python compilation and git diff --check pass.

Real Warbot replay cycled held Flame/Molten/Firescape/Aftershock over112s,
2,626 analyzed-rendered frames. Inspected all38 captures at3s spacing, plus
quiet/full and handoff comparison sheets. Strong low/high flame contrast and
broader event distribution are visible. This is sampled image review, not
continuous audible playback or subjective beat-sync acceptance. Evidence:
work/fire-expression. User live review pending; no commit made.

## Within-Water handoffs (uncommitted)

User accepted the musical color pass and authorized the next step. HEAD remains
907f613; approved color work remains uncommitted alongside this pass. Only the
existing shader, shader_test.py and handoff are modified. Fire handoffs are a
separate future pass, not included here.

water_coverage uses normalized squared form weights and broad moving bands to
let dyes/currents occupy distinct connected regions during their handoffs.
Waterfall coverage advances from the upper view downward. Raw weights still
control camera, wave field, material coordinates and waterfall geometry; no
per-pixel geometric warp, camera replacement, palettes, clocks or audio changes.
The previous dye-then-current composition underweighted dyes; the remaining
surface is now normalized before Current/Falls coverage is applied. Pure forms
short-circuit to their accepted weights. Rain/ripple custom effect selections
retain their explicit behavior; Authored rain details follow the local form.
This is regional material compositing, not fluid simulation or a physical
projection morph between the sea and cliff cameras.

Added --water-meld-test BASELINE OUTPUT to existing shader_test.py. All20
ordered pairings under quiet/intense input passed200 GPU progress/continuity
checks. Ten fully held comparisons are pixel-identical. Maximum change for a
.0001 progress step was.735/255 mean. Inspected Dye/Current, Rain/Falls and
Falls/Current before/after sequence sheets. Existing Main suite passed108 exact
Authored preservation frames,144 handoff checks,721 production-renderer frames
and director CPU checks. Only the intentionally changed native Water cycle was
excluded from exact comparison; held Water and other worlds remain protected.
Python compilation and git diff --check passed. Evidence: work/water-meld;
before.frag includes the accepted musical color pass. Real Balloon replay in
native Water completed142s /3,329 analyzed-rendered frames, covering the full
five-form cycle and return to Sea. Inspected all36 captures at4s spacing;
Rain/Falls, Falls/Currents and Currents/Sea remain readable with connected
material regions. This is sampled visual review, not continuous audible/live
acceptance. User review pending. No commit made.

## Musical material color expression (uncommitted)

Starting checkpoint907f613 is the user-accepted cleanup. User authorized the
next color pass. Changes are confined to shaders/dream.frag, shader_test.py and
these notes; renderer/audio, palettes, clocks, geometry and scheduling unchanged.

musical_material adds bounded chroma and peak lift to the existing Organic/
Corridor/Water material canvas before world lighting. A small sustained drive
uses existing scale/flux; a larger accent uses u_impact and its existing renderer
decay exp(-6*dt). No new envelope or normalization. Near-black material <=.025
is untouched; near-neutral/hot highlights taper out; peak lift is bounded and
ratios retained instead of channel-wise clipping. Quiet drive returns the input.
Planet receives its original canvas and keeps its accepted vividness response.
Fire's established white-blue-hot response is also untouched: the first attempt
at lifting its input slightly reduced saturation through its pigment mixes, so
that part was removed before final validation. Some Water responses are subtle
because physical shading/reflections still determine the visible surface.

Added --musical-color-test BASELINE OUTPUT to the existing standalone shader
suite.45 same-input GPU before/after pairs passed, including27 quiet/Planet/Fire
preservation cases (<=1 channel rounding, <=12 differing channel values), dark
retention, bounded clipping and stronger hit than sustained response. Samples at
77s: lit-pixel saturation gain about9-10 percentage points Organic/Corridor,
1-5.5points Water. Hit peak gains roughly17-18/255 Organic/Corridor,2-10/255 Water.
These are fixed-input samples, not all-song guarantees. Inspected Corridor,
Currents and Organic before/after captures. Main regression passed42 exact
unchanged Authored frames,144 transition checks and721 production-renderer frames
including forward star drift; changed Organic/Water/Corridor/partial Transition
states are deliberately excluded from exact active preservation. Director CPU
checks passed through that suite. Python compilation and git diff --check passed.
Real Warbot replay (seed42) completed125s /2,930 analyzed-rendered frames.
Inspected all42 captures at3s spacing, covering Rain, Organic, Flame, Corridor,
Planet and Currents. Dark areas remain readable as negative space; Corridor
accents are visibly richer. This is sampled image review, not continuous audible
playback or proof of subjective beat synchronization. Evidence:
work/musical-color. No commit made; user live review pending.

## Accepted cleanup checkpoint

User accepted the Corridor clearance repair, regional transition ownership and
musical Main director, then approved checkpointing this cleanup before the next
color-expression pass. All three sections below are included in this checkpoint;
their uncommitted/HEAD references describe the development sequence only.
Relevant synthetic, GPU, Studio and real-track replay checks passed as recorded
below. Unrelated untracked research and scripts are excluded from the commit.
Next proposed work: bounded musical color expression, preserving palettes,
dark space and Planet's accepted vivid response. No new color changes are in
this checkpoint.

## Musical Main director (uncommitted)

User accepted regional ownership and authorized the next timing pass. HEAD is
still 5136362. Earlier Corridor/ownership edits remain in this working tree.
This pass changes renderer.py, replay_test.py, shader_test.py and these notes;
the shader is unchanged from the accepted regional-ownership version.

Live Main now uses Renderer.update_blend instead of a fixed seeded itinerary
plus a supplemental Planet timer. It interprets existing mapped scale/movement/
flux and impact only: .7s vs 8s energy envelopes detect lift/release, and a
hysteresis gate admits distinct strong hits. These are opportunities, not chorus
or beat-grid detection. A world holds at least 12-19s after arrival (first14s),
then can respond; quiet/steady input has a 32-48s breathing deadline (first40s).
Handoffs last6-9s, release8-11s, complete before another can begin, and reuse the
existing uniform contract and regional shader gathering. No stacked extra
Planet; at most two selected forms share a transition. Planet's material/color
response and all motion/star clocks remain unchanged.

World choice balances an energy preference, absence/novelty and38s reuse
cooldown. Overdue Corridor/Planet visits receive increasing preference during
suitable energy; Planet also favors lifts. This is weighted variation, not a
shuffle bag, guaranteed all-world tour, or a promise of a particular visit time.
Fresh sessions use SystemRandom entropy. Renderer(seed=...) and replay --seed
provide reproducibility; replay capture metadata records the seed and bounded
64-entry decision history with reasons. Held Studio selections pause director
time. Existing blend_chapter/blend_uniforms remain deterministic shader fixtures;
world_uniforms packs both paths into the same shader interface.

Validation: synthetic --director-test passed quiet/heavy/section scenarios,
seed repeatability,7 distinct openings across16 seeds, normalized Water/Fire
weights, uninterrupted pairwise transitions, hold bounds, anchor presence,
20vs40Hz agreement and disabled-mode freeze. Quiet visited13 worlds versus27
heavy over600s. Existing Main suite passed114 exact Authored frames,144 fixture
handoffs and721 production-renderer frames including forward star drift and all
three materials. Historical tests asserting the removed Planet timer were
replaced with director tests. Studio tests passed recursive isolation, sessions,
launch modes, UI lifecycle, replay metadata/pacing and continuous GPU clocks.
Python compilation and git diff --check passed.

Recorded Balloon/Warbot inputs with seeds42/73 produce different routes; seed42
Corridor/Planet arrivals start at83.2/107.0s on Balloon and59.8/82.8s on Warbot.
Real Warbot replay through analysis and GPU completed210s /4,922 frames; inspected
all53 captures at4s spacing. Clearly held Flame/Corridor/Planet visits and smooth
regional releases appear in the sequence. This is sampled frame inspection,
not continuous audible playback or live-input acceptance. Evidence:
work/musical-director (track-decisions.json, warbot, blend).

Next review should judge live pacing across songs and new starts. Short intense
music can still select the next scene soon after minimum hold; quiet can wait
longer. Broader vividness tuning and within-family handoff refinement remain
future passes. No new worlds, palettes, normalization or dependencies added.
No commit requested or made.

## Regional transition ownership (uncommitted)

User reviewed the Corridor repair and authorized this next focused pass.
HEAD remains 5136362; both passes remain uncommitted. Only dream.frag,
shader_test.py and this handoff are modified; unrelated untracked files stay.

Main previously interpolated full-screen world RGB with spatially uniform
weights, giving transparent overlapping horizons. Added world_coverage in the
existing shader: normalized cubic global weights with broad smooth spatial
preferences (central Corridor/Planet, curved rising Water, upward Fire). This
only controls final composite coverage. Existing coordinate gathering, geometry,
material palettes, clocks, audio mapping and itinerary remain unchanged. No new
uniforms, render passes, dependencies or renderer architecture. Fully held worlds
short-circuit to their original coverage. Up to four world families plus Organic
can share normalized coverage during supplemental Planet overlaps.

Research inspiration: NVIDIA GPU Gems 3, Ryan Geiss, procedural density fields
and low-frequency domain variation:
https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-1-generating-complex-procedural-terrains-using-gpu
This is an adaptation to screen-region composition, not terrain meshing, fluid
simulation or true depth morphing. Quilez's smooth-min page returned HTTP403;
no code copied or attributed from that inaccessible page. Noise dithering and a
new multi-pass depth system were unnecessary for this bounded change.

Validation: --ownership-test BASELINE OUTPUT exercises actual GPU weights for
all ten family pairs (1,010 progress samples), finite normalized coverage,
monotonic progress with fixed spatial field, bounded steps, five exact held-world
comparisons and three multi-world render samples. Equal-weight pairs have
34-71% of pixels at >80% ownership by one scene instead of uniform 50/50.
Five before/after sequence sheets inspect Organic/Corridor, Corridor/Planet,
Planet/Sea, Sea/Firescape and Firescape/Planet. Main regression passed all 114
exact Authored frames, 144 handoff checks and 721 renderer frames, including
forward star drift. Separate Planet handoff passed all 19 frames.

Limits: this is regional compositing with soft borders, not physical geometry
morphing. Some shared material haze remains. Within-Water and within-Fire form
blends retain their existing behavior. Musical scheduling, varied starts and
quiet-to-hit vividness are the next reviewed pass, not implemented here.
Replayed Warbot through the real audio-analysis/renderer path to 200.1 seconds
without pacing; inspected all 25 two-second captures from 150-198 seconds.
Firescape releases around Planet and Sea takes over without the previous broad
Planet ghost. Some three-world overlap remains at 182-186s, consistent with the
unchanged supplemental Planet scheduler. This was frame-sequence inspection,
not continuous audible or live-input viewing. Python compilation and
git diff --check passed. No commit made.
Evidence: work/transition-ownership; baseline includes the accepted Corridor fix.

## Corridor camera clearance repair (uncommitted)

Actual checkpoint is 5136362 (Integrate material trio and restore expressive
main-world blending). The spatial color recovery and earlier restored forms
below were accepted and committed there; their old uncommitted/HEAD statements
are historical. Unrelated untracked user files remain untouched.

User approved incremental repair following independent Balloon/Warbot viewing.
This first pass addresses the Warbot 130.005s flat-frame defect only. GPU distance
probing reproduced the camera inside a corridor wall (median hit distance .01).
The turn now reaches the junction before lateral movement; low bays lower the
camera for headroom. The junction back wall sits at the side passage's outer
edge instead of cutting across its centerline. Recorded median distance is now
1.6303. Existing materials, color, audio normalization and scheduling are unchanged.

Changed shader plus existing shader_test.py: new --corridor-clearance-test
BASELINE OUTPUT uses the recorded uniform fixture and 9,604 synthetic GPU probes
across 600 seconds/four audio profiles. Minimum median distance .236875; threshold
.20. The existing Geometric test now explicitly disables directed Main mode so
its 423 frames actually exercise isolated Corridor. All passed. Main regression
passed 90 exact preserved Authored frames, 144 transition checks and 721 renderer
frames including continuous forward star drift. Authored states 0/2/4/5 contain
Corridor (including legacy Planet/Transition underlays), so those are deliberately
excluded from exact-image preservation; initial assertions identified these
expected differences. Separate Planet handoff suite passed 19 frames, isolation
and boundary continuity. Compilation and git diff --check passed.

Replayed Warbot through actual audio analysis and renderer to 134.1s (no pacing),
inspected 16 half-second captures from 126-134s and the recorded before/after.
Depth is restored at 130.005s; this is frame-sequence visual inspection, not
continuous audible/live playback or exhaustive aesthetic acceptance. Evidence:
work/corridor-clearance. No commit requested or made in this pass.

Next, after review: improve transition ownership/gathering instead of ghosted
crossfades, then evolve the existing scheduling toward musical opportunities,
varied openings, breathing and earned takeovers. Preserve especially Planet's
brief vivid quiet-to-hit response; local color/contrast should support it.
Research transition approaches when beginning that pass. No new worlds or broad
architecture replacement planned. User permits revising recent choices where
necessary, but prefers small reviewable steps.

## Spatial color recovery (uncommitted)

User accepted the restored forms but found spatial overlap washed out/translucent
and explicitly requested no commit. This is RGB palette/glow mixing, not output
alpha (which remains 1). Shared spatial presentation now chooses a smoothly
biased leading palette using fourth-power weights instead of equally averaging
full-strength ocean/crystal/pathway palettes. Coordinate transforms and their
strengths, Fractal growth, rotation, world schedules and material palettes are
unchanged. Horizon's pale additive bands become palette-colored and recede when
Tunnel/Fractal overlap. A bounded pigment contrast adjustment applies to the
shared field before Living/Alloy/Lattice and stars are added; their own palettes
are untouched. No full-screen saturation filter or global exposure adjustment.
Shared-field peak gains 12% during full spatial presence; dark channels stay dark.

Added --color-test BASELINE OUTPUT to the existing shader test script. Eight
actual Main GPU before/after samples increased mean lit-pixel saturation by
.08760 (8.76 percentage points); maximum near-clipped pixel fraction .00001543
(0.00154%). Inspected six side-by-side captures covering storm, corridor and
liquid overlap. Main GPU regression passed: 114 exact Authored preservation
frames, 144 handoffs, 721 renderer frames; max20ms delta9.911/255 converged at1ms.
Spatial suite passed 108 material/effect/world combinations and 16 continuity
checks. Python compilation and git diff --check passed. No new real-audio/live playback
run for this color-only pass. Evidence: work/spatial-color. Changes confined to
shaders/dream.frag, shader_test.py and this handoff; previous uncommitted work and
unrelated untracked files remain intact. HEAD remains80c85f4; no commit requested.

## Fractal identity, reversing storm and recurring Corridor restoration

User found Fractal's clustered takeover lost, Corridor absent, and the old
reversing storm/eye missing. Inspection found shared spatial weights were zeroed
for coordinate isolation and never restored for palette/eye/Organic replacement.
Thus the original crystal/ocean presentation was disabled and Organic covered it.
Restore these presentation weights AFTER world coverage/projection calculations;
world geometry remains separate. Four bounded recursive folds replace the recent
two-fold approximation, with expanding central coverage revealing more clusters.
Soft absolute corners and a .08 inversion floor restrain unresolved singularities.
Tunnel now swings through 4-radian reversals plus a smaller faster oscillation,
driven by integrated musical u_time (not a beat/phrase detector). Existing
field effects, eye and crystal/ocean palettes participate again. Held custom
Water subtracts accumulated travel before shared folding, as Main already did.

Main itinerary now contains four Corridor visits per 360s chapter, with three
other forms between, and one early visit in the first minute. Every other form
remains. Extra Planet cannot launch during prominent Corridor coverage; an
already active extra Planet yields smoothly to arriving Corridor. Actual authored
Planet/Geometric geometry is unchanged. Chapter boundary repeat guard accounts
for the new insertion order. Heavy-input scheduling tests confirm fully present
Corridor survives Planet scheduling, and eight chapter orders avoid adjacent repeats.

Final GPU checks: 114 exact Authored preservation frames, 144 Main transition
samples (largest 20ms difference 11.972/255, converged at 1ms), 721 renderer frames,
108 material/world/effect checks, 16 spatial continuity checks. Studio suite passed
before final narrow corner/held-Water refinement; final shader/spatial/blend tests
passed after it. Some one-hour samples needed a third .2ms convergence check:
float32 clock quantization and fine recursion make a single 1ms ratio unreliable.
The test records all intervals; fallback requires <35% at 1ms plus further
convergence, rather than silently dropping long-runtime coverage. Final Planet
and Waterfall hour probes were .260/1.040 average levels at 1ms, zero at .2ms.
Earlier sharper-fold versions failed and were refined. This does not certify
absence of all fine-detail shimmer at long runtime.

Evidence: work/spatial-restoration. Initial Balloon/Main replay completed 100.011s
(2,344 frames), peak flow 3.352; storm, Corridor and Planet captures inspected.
Final Balloon rerun completed 60.032s (1,407 frames); final Corridor capture
inspected. Compilation and diff checks passed. No audible or live-loopback test. Files changed
this pass: renderer.py, shaders/dream.frag, shader_test.py and handoff notes.
All prior work remains uncommitted at HEAD 80c85f4; user explicitly wants visual
review before committing. Unrelated untracked work preserved.

## Spatial frequency and recognizable Tunnel follow-up

User found Tunnel/Fractal rare after the shared-spatial pass. Their earlier
76/88-second oscillations and partial amplitude softened their identity.
Tunnel now has bounded reciprocal radial depth instead of mild spiral scaling.
Tunnel/Fractal periods are approximately 34/40 seconds, with wider full-strength
holds, overlapping release, and .94-to-1 strength based on existing bass/flux.
No world scheduling, audio normalization, material palettes or selections changed.

Added actual GPU envelope sampling to the existing spatial suite: over three
minutes Tunnel is >90% for 29-34 seconds per minute, Fractal for 28-32; maximum
sampled gaps below that threshold are 17/20 seconds. This measures shader weight,
not guaranteed screen coverage: world shading/occlusion still affects visibility.
108 material/world/effect checks and 16 continuity checks passed, as did 114
exact authored preservation frames, 117 Main handoffs and 721 renderer frames.
Inspected Organic/Dye effect comparisons and Main overview. Python compilation
and diff checks passed. No new recorded-audio or audible-live run for this narrow
follow-up. Evidence: work/spatial-presence. Shader, shader tests and this handoff
changed; prior uncommitted work remains intact. No commit made.

## Shared spatial dominance (2026-09-26)

User requested large Fractal/Spatial pulls across materials and Water, with
spatial effects inheriting each other during handoffs while worlds stay intact.
Main's former Organic-only gating and sibling bypass are removed. The existing
shader now shares bounded Tunnel -> Horizon -> Fractal coordinate transforms
across Living, Alloy, Lattice and field effects. Long overlapping envelopes
retain outgoing pulls inside incoming folds; bass/flux strengthen them. Two
bounded recursive folds keep broad lobes rather than tiny singular shards.
Spatial strength no longer subtracts world coverage. Water dyes, currents,
rain/ripple color and waterfall curtain details inherit the same transforms.
Physical wave heights, cliff/lip/banks, planet geometry, depth ordering, stars,
and Aftershock plume/shockwave shapes remain structural. This is procedural
material/detail remapping, not framebuffer feedback or a new renderer.

Spatial controls now appear in Water and Fire's existing effect table. Selected
together/cycle isolates the selected effects at full strength; Meld materials
uses overlapping spatial envelopes. Authored playback retains the prior route.
The diagnostic Cycle list still switches rows; Main/Meld provides smooth pulls.

Final synthetic GPU tests passed: 108 material/effect/world combinations, 16
continuity checks (including one-hour elapsed time), 114 exactly preserved
Authored frames, 117 Main world handoff samples, and 721 real renderer frames.
Largest 20ms Main delta was 9.369/255 and passed the tighter-interval continuity
check. Studio standalone suite passed. The first draft was refined after visual
inspection showed excessively fine folds and a long-runtime continuity check
failed; the final two-fold version passes without relaxing test thresholds.
Inspected final Organic, Dye and Planet spatial comparisons. Evidence lives in
work/spatial-dominance. Final accelerated Balloon/Main replay completed 120.021s
(2,813 frames), peak flow rate 3.352, maximum sampled clipping 1.891%. Inspected
30s liquid/material and 75s corridor handoff captures. This was decoded audio
through the live pipeline, not audible playback or live loopback. Compilation
and git diff --check passed. Current changes remain uncommitted on HEAD 80c85f4;
unrelated untracked work is untouched.

## Musical momentum, favored Planet visits and Aftershock density

User still found motion slow and requested more musical acceleration, favored
Planet visits near heavy sections with occasional longer gaps, world warping,
more Aftershock nukes/hits, a musical Molten camera, varied Alloy colors, and
more fractal involvement. The prior motion correction remains, but the old
1.15 speed cap was insufficient for the requested behavior.

renderer.py now applies a bounded energy boost after the existing base movement
mapping: .45 movement + .35 flux + .20 bass drives up to 2.2 extra gain, with a
.45 onset accent and absolute speed cap 4. Acceleration eases over .20 seconds,
settling over .60. Quiet remains .35. No audio normalization/analyzer changes;
Cosmic stars retain their separate integrated clock.

Extra Planet opportunities have 45/55/85-second cooldowns and require 1.5 seconds
of sustained drive (.45 bass + .35 movement + .20 flux > .58). The gate waits
through prominent Aftershock coverage. Six-second gathering, twelve-second hold,
nine-second release reuse existing planet geometry/material projection. These
are energy opportunities, not detected song choruses. The underlying shuffled
itinerary remains; explicit Authored Main disables this extra scheduling.

A bounded shared twist/compression now warps scene coordinates during handoffs.
Fractal presence is more frequent with flux and siblings take part in recursive
coordinates rather than always using the stable unwarped source. Fine-detail
suppression remains. Alloy receives stable per-object hues plus reflective color
variation. Living's original palette is untouched. Molten camera heading and
river transport use integrated u_time, with bounded +/- zoom from phase/bass.

Aftershock now uses an eight-slot event list (birth/id/world x/world z), groups
of four rearmed onsets >=.20, .22-second onset debounce, 1.5-second minimum launch
spacing and a ten-second fallback. Eight active sites is a hard cap; capacity
must free before another launches. Sites last 20 seconds and fade over their
last five seconds. They spawn at varied lateral/forward positions; plumes sort
by actual depth. Ground craters also fade before expiry. The original separate
musical ring cooldown/cap and two-second material-negative flash are retained.
This is onset grouping, not BPM or meter inference. No new renderer/dependency.
Replay metrics/captures now include flow rate, Planet count and blast events.

Initial validation passed: Studio standalone suite; synthetic event/energy tests
(no Planet triggers in silence, grouped launches and eight-site limit, sustained
input does not repeat); 32 fixed-input untouched-world preservation frames;
1,203 actual renderer frames; 102 broader fixed-input comparisons (Molten/native
Fire intentionally excluded), 117 transition samples and 721 renderer frames.
One broad comparison had two one-level channel rounding differences. The largest
sampled 20ms transition delta was 6.688/255 and shrank at 1ms as required. An
additional CPU test confirmed Planet waits through Aftershock (continuous-heavy
starts at 45, 90, 168.2, 253.2, 298.3 seconds). Final GPU/CPU response and transition suites passed after the Aftershock guard,
crater fade and final per-object Alloy palette adjustment. Synthetic Planet,
eight-site Aftershock and final Alloy captures were inspected, along with real
Warbot flash/cloud and Chasing You Molten captures. User listening review remains.
Music runs completed 8,833 frames: Balloon/Main blend 226.8s (5,316), Chasing
You/Molten 60.032s (1,407), Warbot Jazz/Aftershock 90.027s (2,110). Balloon triggered
three extra Planet visits and reached flow rate 3.352; Chasing You reached 2.400;
Warbot reached 2.706 and had 36 observed detonation IDs with the eight-active-site
cap. Maximum sampled clipping was 1.732%, 0.000326%, and zero, respectively.
Music runs preceded the final narrow Alloy hue refinement; final palette was
checked synthetically. No live-loopback or audible playback test was performed.
Python compilation and git diff --check passed.
Evidence is under work/musical-response. HEAD remains 80c85f4; all current material,
blend and response work is uncommitted. Unrelated untracked files are preserved.

## Main motion restoration — pending listening review

The user reported that Living artifacts and the new worlds felt slower and less
reactive after integration. Inspection found the Main-only handoff stabilization
cancelled accumulated material travel, while Organic spatial strengths had also
been reduced to 25%. The audio mapper and original 0.35–1.15 integrated flow
speed were unchanged. This was a visual mapping regression, not evidence of an
audio normalization problem.

Restored authored spatial strength within Organic's Main coverage. Added one
shared material conveyor driven by the existing integrated u_time for Living,
Alloy and Lattice. It is applied after world-coordinate gathering and after
Living's audio/Water scale changes; this restores audio-dependent travel without
multiplying elapsed travel by changing world coverage. The first attempt applied
travel before Water stretching and failed a late handoff check; that interaction
was corrected. Held/Authored routes, Living palette, audio analysis, star clock
and the new itinerary/material selection timing are unchanged.

This pass changes dream.frag, extends the existing shader_test.py with
--motion-test BASELINE OUTPUT, and updates these notes. GPU validation passed
114 exact Authored frame comparisons, 117 transition checks over three chapters,
and 721 renderer frames. Controlled clock-motion tests passed all 15 combinations
of three materials on Organic, Currents, Corridor, Waterfall and Planet canvas.
All responded more strongly to the full-speed clock than the quiet clock.
Currents' Living frame-change measure rose from .278 to .963/255 for the same
clock step; this is a visual-change proxy, not an optical-flow speed estimate.
The 640x360 isolated draw-cost samples were 1.56–3.11 ms after versus 1.24–3.00 ms
before, with no simultaneous replay. These are not live FPS measurements.
Synthetic Currents/Waterfall material captures and a real Warbot Currents capture
were visually inspected. Silent decoded Balloon and Warbot Jazz passages each
completed 90.027 seconds / 2,110 frames, 4,220 total, through default Main blend.
Maximum sampled clipping was 0.812% and zero respectively. No audible/live-loopback
check was performed; user listening review is still needed. Python compilation
and git diff --check passed. Uncommitted; existing unrelated files preserved.
Evidence: work/motion-restore/{before.frag,blend-checks,motion-checks,music}.

## Main blend expansion — pending review, uncommitted

The user reported that Main blend did not show the siblings without selecting
individual worlds and disabling Living artifacts, and requested more sibling
motion, independent material cycles, varied world transitions and breathing.
The cause was the separate Main blend profile still defaulting to Authored.
HEAD remains 80c85f4; the previous material pass and this expansion are uncommitted.

Main blend now defaults to a 22-second ordered trio meld in both Studio and the
normal live launcher. Held-world defaults and explicit Authored profiles retain
the earlier routes. Main blend's implicit list is visible/editable in Studio;
Fire and Aftershock detail switches are now available in its list too. Existing
saved explicit profiles remain authoritative. The all-world trio preset retains
its 36-second slots. Alloy now rolls/deforms more and Lattice tumbles at varied
seeded rates, using the existing integrated clock. Living palette is unchanged.

The existing renderer now supplies world/form weights to the existing shader.
A deterministic shuffled itinerary visits both Organic forms, Corridor, Planet
canvas, five Water forms and four Fire forms, including Aftershock. All 13 appear
once per 360-second chapter, with a new order and variable holds next chapter.
Ordinary holds use 48% for their handoff; every fourth, longer hold uses 32%.
This is repeatable at every replay speed and on restart, not phrase detection or
fresh random order at each launch. No new renderer, audio pipeline or dependency.

Worlds share source-material coordinates and gather into their existing surfaces;
final coverage is normalized so two overlapping worlds do not double-dim each
other. Incoming Roots fades in with world coverage, avoiding a source-canvas cut
inside the departing Corridor. Accumulated transport offsets are removed only
from directed handoff coordinates to prevent later-session pattern acceleration.
Scene clocks, star drift and accepted held-world transport continue unchanged.
Rain/ripples/highlights breathe independently in directed Main blend. Aftershock
continues to use the existing bounded impact history when it has visible coverage.
Waterfall camera, dye structure and current geometry have not been redesigned.

GPU validation: 114 Authored comparisons against the pre-expansion shader passed:
104 exact, ten frames with at most five one-level 8-bit channel differences.
All 13 forms were captured and inspected in the overview. 117 transition samples
across three chapters passed continuity checks, plus 721 real renderer frames
verified default trio weights, uninterrupted positive clocks and Aftershock hits.
Some detailed surfaces move more than four mean pixel levels over 20ms; these
are checked at 1ms for convergence rather than called cuts. Worst sampled 20ms
mean change was 8.682/255, with 0.864/255 at 1ms. Earlier failures exposed the
Root switch and accumulated-coordinate issue; both were corrected. Studio's
standalone suite passed after default-list editing support was added, including
Main blend controls at minimum window size. Python compilation and diff checks
passed. Full silent default-Main replays completed: Balloon 5,316 frames,
Chasing You 3,136, Warbot Jazz 7,015 (15,467 total; 56 captures). Captured material
and world weights matched their independently computed schedules. Maximum sampled
clipping was 0.572%, 0.317%, and 3.090% respectively. The Warbot maximum was
inspected: bright Alloy reflection bands on a close Corridor surface at strong
bass/highs, not a full-screen white flash. Highlight clipping remains a visual
review consideration; this pass does not retune accepted Corridor lighting.
Corridor-to-Planet overlap was also captured/inspected at 514, 518 and 522 seconds.
No live-loopback or audible playback test was performed.

Evidence: work/blend-expansion/{before.frag,checks,music}. The entries below are
chronological history; their opt-in-only and Fire-not-in-Main statements are now
superseded. No commit is authorized for this pass.

## Material siblings — implemented, pending user review and commit

Actual accepted Git checkpoint is 80c85f4. This uncommitted pass adds Liquid
Alloy and Prismatic Lattice alongside Living artifacts, using the existing
renderer, shader, effect lists and session format. No dependency or audio
analysis changes. Original Living palette and calculations remain intact.
Alloy uses reflective folds with copper/teal/violet light; Lattice grows
projected polygon cages from triangles toward seven vertices, with intermediate
vertices emerging continuously. These are shader forms, not simulated meshes.

Studio's Presets → Material trio — all worlds enables an ordered material meld:
36-second slots, fading during the final 35%, for a 108-second cycle. Nonmaterial
effects stay enabled; spatial effects retain authored envelopes in this mode.
Together allows equal-share coexistence; existing Solo/list controls isolate
materials. Authored and the regular live launcher remain the original default.
Cosmic Geometry study bypasses materials intentionally; Planet canvas uses them.
Both siblings feed Water, Fire and Aftershock's material-negative flash. Fire
is still outside Main blend, and Aftershock outside Fire's native three-form
meld. Main world sequencing/integration remains the next reviewable task.

Validation actually executed:

- Existing Studio standalone suite passed, including preset/session roundtrip,
  ordered weights, real GPU uniforms and continuous movement/star clocks.
- New shader materials suite passed 228 preservation comparisons: 223 exact;
  five frames differed in one 8-bit channel sample by one level. The tolerance
  is explicit; this is not a claim of universal pixel identity.
- Both siblings visibly affected all 18 material-bearing states. 1,830 fixed-
  world material-meld frames had maximum mean step 0.315/255; 27 sampled native
  world boundaries had maximum mean step 2.418/255. 561 renderer frames checked
  weights and positive continuous clocks across state changes.
- Silent decoded-track runs covered Balloon/Main blend, Chasing You/Water and
  Warbot Jazz/Aftershock: 9,845 rendered frames and 55 captures. Material weight
  metadata matched the profiles. Captures were visually inspected, including
  metallic dyes, Cosmic cages and the inverted Lattice flash.
- Water and Aftershock sampled captures had no clipping. Main blend's maximum
  sampled clipped fraction was 0.866%, around Cosmic highlights; Authored at
  that same audio input clipped 1.122%. Some other samples increased relative
  to Authored, so this is not a general no-clipping claim.
- Solo 720p Cosmic drawing measurements were approximately 6–8 ms for the new
  materials; these are drawing costs, not end-to-end frame-rate guarantees.
  No audible playback or live-loopback test was performed for this pass.

Development corrected sparse Fire coverage, derivative seams at lattice grid
boundaries, over-forced spatial effects and fine-edge aliasing during recursive
world handoffs. Siblings use a stable domain during strong recursive effects
and fade unresolved detail. An ineffective extra Water-coordinate easing was
removed; existing Water timing was not retuned.

Evidence: work/materials/checks, work/materials/music,
work/materials/clipping-comparison.json and solo-performance.json. Seven visual
code/test files plus these two guides changed. Unrelated untracked research and
scratch files remain untouched. No commit is authorized by the current request.

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

## Current expansion: Molten flow and Fire meld (uncommitted)

Approved Fire was committed as 8be9d4e after the user's "pass!" and explicit
commit request. They also authorized expanding Fire. This pass adds Molten flow
(state 15), an oblique winding lava channel with slowly drifting crust islands,
flowing seams, lit banks and two small impact-heated vents. Studio blank Fire
now runs fire_cycle (16), 56 seconds total: 19s holds, 9s eased changes. Existing
fire (14) remains held Flame sheets and is pixel-identical to the checkpoint.
The cycle blends source coordinates and crossfades compositions, rather than
simulating a physical camera journey. Main blend remains unchanged.

Same Fire layer profile/bits: Coals gates crust islands in Molten flow, Hot
seams gates fine glow, Embers gates sparse sparks, Living artifacts supplies
its unchanged inherited material/palette. No new uniforms, renderer/audio
changes, dependencies or material siblings. Existing blank Fire sessions now
include both forms; saved Flame sheets leaves and flat fire sessions retain
the held form. Elements' generic diagnostic cycle now visits seven leaves.

Executed GPU test: --molten-test work/elemental/molten/before.frag
work/elemental/molten/check. Passed 540 exact preservation comparisons for
states 0–14; all prior Flame sheets motion/ignition checks retained. New Molten
form: 18 input/time samples (contrast 20.85–27.21, dark .84–.86, zero clipping),
independent responses to four audio controls and four layers, and silent motion.
Six native-cycle endpoints match held forms exactly; 24 boundary checks pass
(max .333/255) and 542 transition frames pass (max .517/255). Initial Molten
capture and the two-direction meld contact sheet were visually inspected.

studio_test.py passed hierarchy, shared Fire profile, legacy/current sessions,
UI lifecycle, replay metadata/pacing and continuous GPU clocks. Python syntax
and git diff --check passed. All three 60-second fire_cycle replays completed
(4,221 frames / 18 captures), exercising both held forms and both transitions.
Capture structure/headroom bounds passed. One 30s Molten capture per track was
visually inspected. Maximum clipping was .001194% (11 of 921,600 pixels), in
the new Molten hot vents at 30s. This is within the .1% test bound, but is
not zero clipping. Earlier commentary attributing it to Flame sheets was
corrected after reading the exact capture times. These are silent excerpts,
not full songs or live-loopback testing. Evidence: work/elemental/molten/music/.

Nine expected changed files: dream.frag, live/synthetic state maps,
preview_layers.py, studio.py, studio_test.py, and these three development docs.
No commit/push of this expansion. Unrelated scratch/research remains untouched.
Next review: Studio → Elements → Fire → Molten flow; blank Form plays the meld.

## Accepted Fire checkpoint

The user reviewed the refined Fire, said "pass!", and explicitly authorized
committing it before further expansion. This checkpoint contains the isolated
Flame sheets form, Studio registration/layers, lava-base refinement, white/blue
ignition, tests and documentation. Historical pending-review statements below
are superseded by this acceptance. Main-blend integration remains future work.
The user also authorized continuing Fire expansion after this checkpoint.

## Fire refinement — user accepted the start and requested more character

Still based on 38da96a; the Fire foundation and this refinement are uncommitted.
The user requested a steady lava-like base, stronger licking tips, and a
white-hot → blue → existing amber response on intense hits. Changes are limited
to Fire's shader function, its existing GPU test and the two development notes.
Coals retains its label/ID but now shows molten channels drifting on elapsed
time with a slow rhythm, independent of abrupt audio. Rising Embers is unchanged.
Upper tips have traveling curls/elongation. The ignition response follows the
existing renderer's six-per-second impact decay, calibrated to real onsets near
.5; it is restricted to folded flame roots. No renderer/audio/palette changes.

The first wide white band was visually rejected and failed the generic motion
bound at 22.79/255. Narrowing and ribbon-shaping it fixed the flat-band appearance.
The final test distinguishes the requested onset flash (10.919/255, bound 12)
from ordinary motion including decay (max 2.864/255, original bound 3 retained).
GPU tests passed 504 exact preservation cases, 18 input/time captures, separate
audio/layer responses, 361 integrated frames, continuous flow/star clocks,
steady-but-moving lower lava pixels and white/blue/amber decay captures.
Synthetic profiles and cooling triptych were visually inspected. Evidence:
work/elemental/fire/refinement/, baseline before-refinement.frag. Existing
foundation baseline before.frag still verifies all states 0–13.
Accelerated replay then passed the first 60 seconds of all three tracks:
4,221 frames, 18 captures, no clipped pixels; Balloon at 30s and Warbot Jazz at
50s were visually inspected. Evidence: work/elemental/fire/refinement-music/.
These remain silent excerpts rather than full-song or audible playback tests.
Python compilation and diff whitespace checks passed. Studio code/controls
are unchanged in this refinement, so its previously passing tests were not rerun.
Live loopback is not tested. User should reopen Studio → Elements → Fire →
Flame sheets for motion review. Still no main-blend integration or commit.

## Fire foundation — isolated, uncommitted, awaiting visual review

Current committed checkpoint is 38da96a (accepted Water completion). The user
agreed to defer a metallic sibling material and authorized starting Fire.
Living artifacts and its palette must remain intact. The metallic sibling may
later have its own palette and alternate or coexist; it is not implemented.

Studio → Elements → Fire → Flame sheets uses state 14. Three upward-advected
sheets, a low coal bed, selective hot seams and ascending embers establish one
composition. Existing material and Living artifacts are carried through it.
Bass widens/raises the fire, flux curls folds, sparkle reveals seams/embers,
impact heats a bounded lower region; silence still flows. Existing renderer,
audio mapping and positive clocks are reused. This is procedural layered
imagery, not a volumetric simulation. No new dependencies or uniforms.

Fire's own layer profile exposes Living artifacts, Coals (131072), Embers
(262144), Hot seams (524288). Existing bits are stable. Raw state 14 routes
through a neutral Organic source field and final Fire composition; it cannot
fall into the old >5.5 Water route. The existing artifact calculation/palette
is unchanged. Fire captures its contribution before the Organic substitution.
The production main blend is unchanged; Fire awaits review before integration.
Elements with a blank child now visits all five Water leaves then Fire in
28-second diagnostic holds. Fire's blank form holds its only current form.

Executed validation:
- shader_test.py --fire-test: 504 exact GPU pixel comparisons against 38da96a,
  states 0–13, six times, three levels, authored and artifact-only modes.
- 18 Fire input/time samples: contrast 25.25–40.63, dark fraction .64–.79,
  zero clipped pixels. Four independently visible audio responses, silent
  motion, and four independently visible effect toggles passed.
- 361 actual-renderer frames across rise/impact/release; flow and star clocks
  strictly advance. Largest mean frame change 2.8975/255, below bound 3.
- studio_test.py passed, including real Tk Fire dropdowns/table/session,
  existing UI lifecycle, hierarchy, replay pacing/metadata and GPU clocks.
- First 60 seconds of each Balloon, Chasing You and Warbot Jazz: 4,221 frames,
  18 captures, all structure/dark-space bounds passed, zero clipped pixels.
  Synthetic quiet/moderate/full contact sheet and one 30s frame per track
  visually inspected. These are silent accelerated replays, not full songs
  or live-loopback verification; moving aesthetics still need user review.
- Python compilation and git diff --check passed.

Evidence: work/elemental/fire/{check,music}/; baseline before.frag. The shader
regression lives in existing shader_test.py, Studio checks in studio_test.py.
Nine modified tracked files: shader, live/synthetic state maps, layer catalog,
Studio, its test, and DEVELOPMENT_STUDIO.md / ELEMENTAL_DEVELOPMENT.md / this
handoff (shader_test.py contains both state map and GPU checks). No commit or
push. Existing unrelated untracked research/scratch files remain untouched.
Next: reopen Studio and review Fire with Authored first, then its isolated
layers. Do not start another element or integrate Fire before that review.

## Water completion checkpoint: details, Currents and main integration

Base is accepted commit 6875fb9. The user accepted the Water continuation and
asked to finish Water before committing. This checkpoint exposes five existing
Water effects, adds Currents, and integrates all five forms into the main blend.
Other elements will be developed one at a time; none was started in this pass.

Studio → Elements → Water → Currents (state 13) holds broad colored streams
bending through two eddies, with dark channels and fine reflected ribbons.
Existing source imagery supplies the moving material. Bass broadens pressure,
flux controls local shear, sparkle reveals fine light, and impact creates a
bounded disturbance. Quiet passages still move. The existing renderer and
positive clocks are reused; this is a procedural coordinate field, not fluid
simulation. The accepted sea's height equations are unchanged.

Water details category: Rain streaks, Ripple rings, Crest foam / cliff lip,
Mist & distance haze, Surface highlights. These append stable bits to the
existing catalog/uniform interface. Rain/rings can independently populate
surface forms, including Currents; the waterfall supports its own lip,
highlights and haze. Foam needs steep crests and haze depends on distance.
Authored mode preserves existing held forms; custom lists explicitly select
the new details. No dependencies, audio changes or renderer lifecycle edits.

Water's isolated development cycle (state 6) now includes Currents after
Waterfall: five 28-second slots, 140 seconds total. Each has a roughly
19-second hold followed by a 9-second eased change. The isolated Water music
launcher also uses this expanded cycle. Main blend (state 0) holds one form
through each Water visit, then advances while Water is hidden: Sea, Currents,
Waterfall, Rain & ripples, Liquid dyes. The existing entry/full/release times
116/126/144/158 seconds and 140-second visit spacing are unchanged. Animation
and material clocks never reset. This prevents a 140-second five-form cycle
locking onto the same phase every visit, and avoids concurrent form-camera
changes during Water's exit. A trial continuous main form schedule failed a
transition bound (3.3923/255 at 284s); that version was replaced, not accepted.
Currents also delays the returning spatial grammar with a cubic release
envelope. Long advected material coordinates otherwise amplified recursive
folds during exit (5.1639/255 at 287s). Held forms and imagery outside Water
remain unchanged; the corrected version passed the same comparison bound.

Final integration test passed 222 preservation cases (all held forms, Studio's
cycle and main imagery outside Water), all five distinct main visits, and 90
entrance/dwell/release comparisons at quiet/moderate/strong fixed inputs.
The comparison retains a pre-existing extreme-input frame-change spike at
256s / .95 input: 53.8261/255 vs baseline 53.8225/255. This is not a claim that
every legacy transition is smooth; the regression allowance is relative to
the accepted baseline. Broad retuning of the accepted background was excluded.
Evidence: work/elemental/currents/integration/ (before-integration.frag is the
accepted Currents preview before main scheduling changed).
The complete Warbot Jazz main-blend replay then finished: 299.3 song seconds,
7,015 frames and 20 captures. Both full-Water captures (Sea at 135s, Currents at
270s) passed structure/dark-space checks with zero clipped pixels. Currents at
270s and its release at 285s were visually inspected. Non-Water captures retain
existing highlight clipping, up to 1.5805% in this replay. Evidence is in
work/elemental/currents/integration-music/. Live loopback was not rerun.
Python compilation and git diff --check passed. The nine-file completion pass
is the requested checkpoint; unrelated research/scratch files remain excluded.

Changed files: dream.frag, preview_layers.py, Studio's catalog/note, live state
map, shader_test.py, studio_test.py, and Water/Studio/handoff documentation.
No changes to the existing audio pipeline, renderer implementation or replay
implementation. Unrelated root scratch files/research remain untouched.

Development verification before main integration:
- Detail-only stage: 132 exact pixel preservation cases and 40 visible
  effect/world combinations.
- Final currents-test: 144 exact prior-world/held-form/main-blend comparisons,
  44 effect/world combinations, 28 Currents input/time samples, four independent
  audio responses, motion with silent inputs, 20 eased cycle boundaries, and
  361 renderer-integrated frames. Maximum mean changes .8273/255 at joins and
  1.1756/255 across the integrated envelope; no headroom/structure failures.
- studio_test.py passed hierarchy, new state registration, session migration,
  table operations, replay metadata/pacing and continuous GPU clocks. Focused
  real Tk checks passed Currents selection, all five Water-detail options,
  add/cycle/save round-trip and minimum 680x700 layout.
- Accelerated real audio: first 60 seconds each of Balloon, Chasing You and
  Warbot Jazz, 4,221 frames total, 18 captures. All capture structure/dark-space
  checks passed with zero clipped pixels. Synthetic contact sheet and one
  captured music frame per track were visually inspected.

Evidence is under work/elemental/currents/{check,music}/, with the saved
pre-change shader at before.frag. Excerpts are not full-song or live-loopback
testing. The user accepted Currents and authorized finishing this checkpoint.
Reopen Studio, select Currents, and use Authored first; then try individual
Water details. No other element should be started until the next request.

## Accepted checkpoint: Water and Development Studio

The user accepted the Water refinements and Studio form/effect isolation, then
explicitly requested this checkpoint commit. It builds on aa44d54 and includes
the accumulated Water world, shared onset-order fix, accelerated replay,
hierarchical selectors and per-world effect lists. Earlier uncommitted/pending
review statements below describe the development history and are superseded
by this acceptance. Unrelated research folders and root-level scratch scripts
are excluded. No new feature work is part of the checkpoint.

### Current development-tool pass: forms and effect layers

User accepted cascading world isolation and requested a further separation of
forms from optional effects, with add/remove, enable, solo, order and cycling.
Terminology: World = environment; Form = main structure; Effect = treatment;
Layers = a world's saved ordered effect list. Elements is a grouping category.
This section supersedes the previous pass's "no order-list editor" statement.

Studio exposes Organic → Membrane / Roots (blank retains native meld),
Geometric → Neon corridor, and existing Cosmic/Water forms. Effects & layers
has category/effect pickers, a table, On/off, Solo, Remove, Up/Down, and Authored /
Selected together / Cycle list playback with a hold duration. Per-world lists
survive selection changes and session save/load. Water has its own profile,
independent of the Elements grouping. Main blend has a separate preview profile.
Version 3 saves lists and paths; v1/v2 migrate with authored effects unchanged.
Each run saves preview.json alongside its log for reproducibility.

The new small preview_layers.py shares development IDs, validation and cycle
selection among Studio and the existing entry points/renderer; it is not a new
audio or visual parameter pipeline. Two optional shader uniforms gate existing
effects. Default mode preserves authored appearance; custom mode holds selected
spatial treatments and gates material/detail contributions. Custom material
effects remain visible on Organic's surface before planet/corridor projection.
Stars retain their continuously integrated clock even while hidden.

Implemented controls: artifacts, sparkles, drifting flecks, radial beams,
tunnel, fractal folds, horizon/pathway, root blossoms, corridor glyph rain,
starfield, rings, moons with their dust wakes. Effects remain audio-responsive
and keep their lifecycle. Root blossoms require Roots; Cosmic Geometry study
uses only world details. Water's rain/waves/ripples/fall remain forms; its
inherited artifacts can be isolated. Fractal remains a spatial treatment.

List order is cycle order, not arbitrary shader/compositor order. Together
retains the shader's established coordinate/material order. Cycle cuts are
development diagnostics; song time drives replay regardless of acceleration.
CLI --layers JSON works in live, replay, synthetic preview and fixed capture.
Replay CSV/capture metadata includes the active layer mode/mask. Main live
launcher has no overrides and does not import Studio's lists automatically.

Verification executed: shader preservation_test passed 72 comparisons;
layer_test passed 132 comparisons covering all previous states, with maximum
channel deviation 1/255, two distinct held Organic forms and 30 visible
effect/world combinations. Synthetic GPU base-form, artifact and fractal
captures were visually inspected. studio_test passed actual Tk selectors,
table/solo/reorder/save/load callbacks, per-world independence, v1/v2/v3
migration/validation, minimum 680x700 layout bounds, child lifecycle, replay
pacing parity, 9-second real audio layer cycling and 57-second form cycling,
capture/CSV labels, and uninterrupted real GPU drift/star clocks. CLI help for
all three entry points passed, including live/replay module invocation.
Fixed-frame CLI capture verified the requested artifact mask and the resulting
planet material was visually inspected. Python compilation and git diff --check
passed (Git reports its normal LF-to-CRLF conversion notices).
Live loopback and desktop screenshot review were not rerun for this pass.

Evidence: work/development/layers/before.frag and check/ (ignored development
artifacts). HEAD remains aa44d54; accumulated Water/Studio work is uncommitted.
No dependency changes, deletion, renderer replacement or audio analysis edits
in this pass. Restart Studio to load controls; changes apply on the next run.

### Current development-tool pass: hierarchical isolation

The user accepted the revised waterfall, then requested cascading world,
category and deeper form selectors with blank selections cycling the chosen
branch. Studio now has a recursive WORLD_TREE catalog: Organic, Geometric,
Cosmic, Transition, Elements → Water → Sea / Liquid dyes / Rain & ripples /
Waterfall. Cosmic exposes its existing canvas and geometry diagnostic. No
unimplemented elements or order-list editor were added.

Blank root uses main blend; blank Water uses its authored native meld. Elements
currently delegates to its sole implemented Water child. Multi-branch groups
without a native cycle flatten every descendant leaf in catalog order and
hold each for 28 seconds. This prevents grandchildren from being skipped when
future elements are added. These generic development switches are direct cuts.
Native Water blending is unchanged. Select a leaf to isolate it.

Parent edits clear stale children; nested dropdowns and Presets menus rebuild
recursively, with a scrolling selector area for deeper paths. Session version 2
saves stable selection IDs. Version 1 state sessions migrate to equivalent
paths on load, without changing their selected held/native behavior.

Files in this step: studio.py, studio_test.py, renderer.py, the existing live,
replay and synthetic entry points, and development/handoff documentation.
The renderer has an optional debug_sequence and elapsed-time state selector;
its lifecycle, clocks, uniforms and normal default behavior are unchanged.
All three entry points accept --states. Replay metadata/CSV records the actual
active state, using song time regardless of acceleration. No shader/audio
analysis changes, dependencies, new renderer or separate replay pipeline.

Verification executed: studio_test.py passed recursive selection (including a
temporary fourth level and multi-branch descendant coverage), blank semantics,
ancestor clearing, all launch modes, v1 migration/v2 round-trip and invalid
paths, actual Tk start/stop, replay pacing parity, a 57-second real audio/GPU
group replay crossing two state boundaries, capture/CSV state labels, and
actual GPU state uniforms with positive uninterrupted flow/star clocks. Minimum
680x700 layout bounds were checked for root, parent and leaf selections; buttons
remain visible. Live/synthetic CLI help accepts the new option. Live loopback
and desktop screenshot review were not rerun for this control-only change.
Restart Studio to load the hierarchical controls; existing previews keep their
current settings. Nothing committed; aa44d54 remains HEAD.

### Waterfall perspective refinement

The user accepted the other Water forms and development controls, but asked
to replace the waterfall's bottom pond/rings with an infinite fall fed by a
river between a distant world horizon and a nearer cliff lip. Rain ripples
were explicitly accepted and must remain unchanged.

Only dream.frag's waterfall projection/shading/material mapping changed, with
coverage added to the existing shader_test.py and documentation updates.
FallsSurface analytically intersects a horizontal river and vertical cliff
face meeting at the same edge. A slow camera approach lowers the viewpoint
below the lip: the river appears broader/shorter, then river, cliff edge and
sky move out of frame, leaving falling water. The camera retreats continuously.
The material uses one continuous flow coordinate around the lip; downstream
streaks stretch with fall distance. Existing wave normals shade the upstream
river. The basin and its concentric rings are removed only from the waterfall.

This remains stylized two-plane perspective shading, not fluid simulation or
volumetric terrain. No renderer, audio, studio, state timing or other form edits.
The held waterfall preset and existing family/main-blend routes all use it.
Baseline: work/elemental/waterfall-perspective/before.frag.
Initial wide/intermediate/close captures were visually inspected. Further
verification for this pass is recorded below when complete.

Final synthetic checks passed: --waterfall-test extends the family harness,
comparing 108 unaffected-world/sea/dye/rain samples against the pre-refinement
shader (at most 1/255 difference), 60 form samples and 20 family/live boundaries.
An actual GPU sweep covers 4,802 camera frames at 60 Hz across approach and
retreat, quiet and dense inputs. Maximum mean frame delta is 1.8122/255.
GPU hit-classification probes confirm separate sky/river in the wide view,
over 98% falling-face coverage in close-up, and no bottom pool intersection.
Existing non-Water temporal changes remain as documented in earlier entries.

The camera test initially found a magnified source-shape pop at 99.283s.
Cell-edge fading alone was insufficient; the inherited hard appearance
threshold also needed easing. Both changes are gated to the waterfall's
weight, leaving rain, dyes and sea unchanged. Final wide/close and blended
captures were visually inspected. Landscape and portrait target checks passed;
earlier timing samples had concurrent GPU work and are not isolated performance
measurements. Evidence: work/elemental/waterfall-perspective/final/.

All three complete tracks were rerun through the corrected held waterfall:
Balloon 5,316, Chasing You 3,136, Warbot Jazz 7,015 frames (15,467 total).
Audio CSVs match the previous family runs exactly apart from the state label.
All 84 periodic captures passed contrast/dark/headroom checks: minimum contrast
9.256, minimum dark fraction 8.93%, no clipped pixels. The 18-image three-track
contact sheet and final portrait capture were visually inspected. Evidence:
work/elemental/waterfall-perspective/final-music/{review-sheet.png,verification.json}.
The first pre-fix music runs remain separately under music/ as diagnostic data.
git diff --check passed. Changes remain uncommitted; HEAD is still aa44d54.
Next: choose waterfall in Studio and restart the preview for user review.
The new waterfall is already used by Water family and main blend; no re-import.

### Current expansion: Water family, development controls, main blend

The user accepted the sea world ("Really Cool!") and explicitly requested
more Water forms/melding, a useful development environment, and integration
into run_live_visualizer after verification. This supersedes the older
isolated-only/pending-world-acceptance statements below. No commit authorized.

Water now cycles sea -> dye currents -> rain/ripples -> waterfall -> sea,
with held debug states 7–10 for review and state 6 for the family. The accepted
sea equations are intact. Pool views pitch down; dye exposes folded colored
channels, rain uses seeded expanding rings and sparse streaks, waterfall uses
a falling curtain and receiving basin. These are procedural effects, not fluid
transport or simulated droplets. All reuse existing source material/palettes.

The main blend now admits Water between Cosmic visits: initial 116–158s visit,
full takeover 126–144, then every 140s. Startup and Cosmic's original timing
remain unchanged. Water's independent 112s form cycle varies successive visits.
The same shader runs through run_live_visualizer; no launcher switch is needed.

New app/visuals/studio.py and run_development_studio.bat expose useful controls:
state/source/track/speed/duration, captures, sessions, preset menu, review tab.
Menus are functional; import/export means settings JSON, not arbitrary shaders.
The existing replay/live/preview scripts remain the execution paths. No new
dependencies. Replay pacing now accounts for work elapsed against song time;
previous capped sleeps made the real-time option too fast. All chunks remain.
See DEVELOPMENT_STUDIO.md for workflow and limitations.

Executed checks so far:
- Studio standalone checks passed: session round-trip and validation, every
  state command, actual Tk start/stop callbacks with a real replay child,
  identical real GPU/audio results at speed 1 and 0, real-time pacing floor.
- Family GPU checks: 84 preserved-world/sea cases, 60 form/profile/time cases,
  16 form/live boundaries, explicit live admission and restoration checks.
  Held sea and unaffected accepted worlds differ by at most 1/255.
- Water synthetic checks: 36 stills, four input responses, silent evolution,
  181 integrated frames, 360 draws across four output sizes. 1080p sea draw
  median 4.08 ms, p95 4.13 ms (GPU only, not all-form performance).
- Dye, rain, waterfall and main-blend captures were visually inspected.

The first boundary test flagged a 3.455/255 mean frame change at 158s; the
original blend measured 3.455 as well. Later original blend boundaries change
up to 19.662/255; the revised check allows existing temporal changes plus .25,
while holding family-only boundaries below 3. This is preservation evidence,
not a claim that existing blend motion is artifact-free. Family boundary max
was .795/255. A startup wraparound was corrected before final replay.

Desktop UI screenshot inspection timed out waiting for Computer Use app
access. Tk functionality was tested, but desktop layout is not visually
verified. Evidence so far: work/elemental/water-family/{verification,synthetic}/.

Final verification: all three complete tracks ran through BOTH Water and the
main blend (30,934 analyzed/rendered frames total). All audio CSV values matched
the previous accepted-wave runs exactly, excluding the intended state label.
All 168 sampled frames passed structure/headroom checks. Water captures had
at least 33.95% dark pixels and no clipped pixels. Main blend had up to 1.50%
clipped pixels, with maxima in the unchanged Cosmic dwell (e.g. 208s), not a
claim of zero clipping throughout the existing blend. Both 18-frame contact
sheets were visually inspected: work/elemental/water-family/music/.

Held dye/rain/waterfall also passed 1080p and portrait draws; captures inspected.
Their 1080p GPU medians were 4.80/5.54/4.43 ms respectively (measured while a
replay was active, not isolated whole-app performance). Tk layout bounds and
three-track deduplication were verified; the minimum window height now keeps
buttons visible. Studio checks passed again after these changes.
The finished Studio was opened on the desktop for user review. Nothing staged
or committed; aa44d54 remains HEAD. git diff --check passes with line-ending
notices. Next: user review of new forms, melding and Studio before checkpoint.

### Water world built around the accepted waves

The user accepted the rough-sea refinement ("okay much better") and requested
the Water world. That supersedes the pending-acceptance wording in older entries.
The new setting is an open night sea between distant rocky islands, with low
mist, reflected atmospheric light, submerged colored currents and sparse foam
on high, steep storm crests. Quiet passages retain slow currents and dark space.
The camera now reveals the horizon. The accepted height field, current function,
audio mapping, clocks and rough-sea response were preserved.

This step changes only app/visuals/shaders/dream.frag, shader_test.py and these
two development notes. The environment is Water-only procedural shading using
existing palettes; no new renderer, uniforms, assets, dependency or audio edits.
Distance haze and broader far-surface normal samples soften the distant sea.
The islands are background silhouettes; foam is visual shading, not fluid
simulation. Water remains isolated state 6, without scheduler changes.

Verification executed for this world pass:
- Water test: 36 still cases, independent input responses, silence motion,
  181 integrated frames, 360 draws across landscape/portrait/ultrawide sizes.
  Largest integrated mean frame delta 2.883/255. 1080p GPU draw median 4.414 ms,
  p95 4.829 ms; these exclude audio capture and presentation.
- New --water-world-test mode: exact accepted wave height AND motion fields
  at nine profile/time combinations, stable background under audio changes,
  responsive foreground and continuous storm threshold (.01787/255 mean delta).
- All 72 other-world comparisons / 144 GPU frames are pixel-identical,
  preserving Organic, Geometric and Cosmic appearance.
- Full-size landscape, portrait and quiet captures were visually inspected.
- All three complete music replays passed (15,467 frames); every audio CSV
  field matched the accepted rough-sea runs exactly. All 45 sampled frames
  retained contrast, at least 62.86% dark pixels, and zero clipped pixels.
  The twelve-image music contact sheet was visually inspected.

Evidence: work/elemental/water-world/{final,comparison}/. Baseline before this
world pass: work/elemental/water-world/before.frag. The new composition still
needs user review. No second element was started. HEAD remains aa44d54;
accumulated Water/audio/replay changes remain uncommitted.
Music captures and summary: work/elemental/water-world/music/.
git diff --check passed (line-ending notices only). The new live Water window
is open on BlackShark loopback; initial observed inputs were silence. Next:
user music review of this composition, then explicit checkpoint approval.

### Rough-sea response requested after live review

The user likes the overall Water treatment and requested that intense music
drive waves more like a raging sea. This supersedes preserving the previous
high-energy wave amplitude, while retaining the accepted quiet appearance.

Changes are confined to dream.frag's Water functions, shader_test.py comparison
coverage, this handoff and ELEMENTAL_DEVELOPMENT.md. A smooth weighted
bass/flux/sparkle envelope (60/25/15 percent, threshold .55 to .88) introduces
taller and faster broad crossing swells beneath the existing fine ripples.
Wave phases retain constant rates on the existing clocks; audio controls the
added amplitudes rather than multiplying accumulated time. The surface bounds
expand to contain the swells. Rough water scans up to 40 intervals to bracket
a front crossing before the existing 14 refinements, so tall waves obscure
distant troughs. Quiet water retains the original search and shading.
No audio, renderer, shared clocks, other worlds or palette code changed.

Verification executed for this refinement:
- GPU before/after comparison: quiet and moderate images at 18, 67 and 180s
  are pixel-identical. Chorus height standard deviation increased 2.55-3.36x;
  temporal height change increased too (combined amplitude/movement measure,
  not a literal speed ratio). The .55 boundary is continuous within a mean
  pixel delta of .00921/255.
- Existing-world comparison: all 72 cases / 144 GPU frames are pixel-identical
  to the pre-refinement shader, including Organic, Geometric and Cosmic routes.
- Water test passed all 36 still cases, four individual audio responses,
  silence motion, 181 integrated frames and 360 draws across four sizes.
  Largest integrated mean frame delta 5.101/255. High-energy 1080p GPU draw
  median 4.59 ms / p95 5.87 ms; higher cost is the rough-water surface search.
  This excludes audio capture and presentation.
- Chorus captures at 18 and 67s and a full-size Balloon frame at 90s were
  visually inspected: substantial rolling crests, dark troughs and inherited
  colored material, rather than the previous nearly flat expanse.
- All three complete music replays passed: Balloon 5,316 frames, Chasing You
  3,136, Warbot Jazz 7,015 (15,467 total). Every CSV field matched the previous
  onset-corrected run exactly, including impacts. All 45 periodic captures
  retained structure/dark coverage without clipping; minimum dark fraction
  53.3%. A twelve-frame, three-track contact sheet was visually inspected.

Baseline: work/elemental/rough-sea/before.frag. Synthetic evidence:
work/elemental/rough-sea/{first,comparison}/. This remains a procedural height
field without breaking foam or fluid simulation. Music evidence and summary:
work/elemental/rough-sea/music/{review-sheet.png,verification.json}. The user
subsequently accepted the stronger motion. No commit has been made.
The prior Water preview was closed normally and reopened with this shader.
BlackShark loopback is receiving varying audio (including nonzero impacts);
the updated window was left open for user review. git diff --check passed.

### Approved onset-order correction: implemented and verified

The user approved the proposed correction after the three-track discovery.
Moved the three onset detector calls in app/visuals/live_visual_test.py to
immediately after SignalProcessor normalization/smoothing, before
VisualSignalConditioner's visual slew limit. No thresholds, normalization,
continuous conditioning, shader code, renderer clocks or parameters changed
in this correction. The shared function fixes both live input and WAV replay.

Extended app/audio/onset_test.py with the real shared analysis path (FFT,
normalization and conditioning) using isolated synthetic tones for all three
bands, in mono and stereo. It first failed on the old ordering, then passed
with the fix. Tests verify silent input, two separate attacks, stable sustain,
release, absence of cross-band onsets, and unchanged 0.12 continuous slew bounds.
signal_test.py, normalize_test.py, audio_frame_test.py and
parameter_mapper_test.py assertions passed; multiband_onset_test.py was also run
and its detector outputs inspected.

All three COMPLETE song replays were rerun through Water: 15,467 GPU-rendered
frames. Comparison with the pre-fix CSVs proved exact per-frame equality for
every field except impact, including bass/mids/highs, scale/movement/sparkle,
flux and song time. Restored event coverage:
- Balloon: 732 nonzero impact frames / 633 consecutive-event clusters; max .4955.
- Chasing You: 487 frames / 361 clusters; max .4963.
- Warbot Jazz: 1,193 frames / 1,057 clusters; max .5000.
These counts describe threshold crossings, not validated beats or distinct
perceptual events. Frequent events during dense material need listening review.

All 45 periodic Water captures retained structure and dark coverage without
clipping at the existing thresholds. Another 45 GPU snapshots cover the
strongest song event, about .256s later, and about 1.024s later in Organic,
Geometric, Cosmic canvas, Water and normal blend. The actual renderer integrated
every preceding CSV input; rasterization alone was skipped between snapshots.
The three resulting contact sheets were visually inspected. All snapshot
structure assertions and continuous positive star-clock checks passed.
Warbot's maximum event occurs on its initial attack at song time zero.

Regressions rerun: Geometric 423 frames passed (minimum contrast 4.946), Cosmic
handoff 19 frames passed, moon opacity 122 frames passed (155 opaque lit centers,
27 hidden centers). No attempt was made to keep event-driven output identical
to the old zero-impact path; restoring those existing expressions is intentional.
Actual synchronized listening to this corrected build remains user review.

Evidence: work/elemental/onset-order/{balloon,chasing-you,warbot-jazz}/,
comparison.json and event-frames.json. The fix adds app/audio/onset_test.py to
the accumulated tracked Water changes. Handoff and Elemental notes updated;
git diff --check passed with existing LF-to-CRLF notices. Nothing staged or
committed; aa44d54 remains HEAD. Next: review restored events with live music,
then seek explicit checkpoint approval. The earlier assistant-launched Water
window was closed normally and reopened with this corrected code; BlackShark
loopback initialization succeeded and initial observed inputs were silence.

### Resumed review and three-track replay

The user confirmed that Water's waves look fine. Preserve this accepted wave
treatment; that statement is not blanket acceptance of every Water feature.
The live Water window launched through the existing loopback pipeline on
BlackShark V3 Pro BT; initial observed inputs were silence. It was left open
for the user's review. Accelerated replay windows close at each track's end.

Reused the existing decoded files and replay_test.py for complete Water runs:
- Balloon: 226.8 song seconds, 5,316 analyzed/rendered frames, 16 captures.
- Chasing You: 133.8 seconds, 3,136 frames, 9 captures.
- Warbot Jazz: 299.3 seconds, 7,015 frames, 20 captures.

Total: 659.9 seconds / 15,467 frames. The 45 sampled captures passed checks for
spatial structure, retained dark areas and no clipped highlights. Minimum
sample contrast across tracks was 16.803; minimum dark fraction 46.5%; maximum
clipped fraction zero. Twelve representative frames in the review sheet and
an additional full-size Balloon frame were visually inspected. The replay is
decoded real music through the actual analyzer/renderer, without audible
playback; it does not replace synchronized live listening or full-motion review.

Added optional --capture-dir and --capture-interval to the existing
app/visuals/replay_test.py, reusing shader_test.save_png. Capture defaults off;
no renderer, shader, normalization or state scheduling changed in this resumed
pass. Capture-enabled and default capture-disabled 24-frame smoke runs produced
identical per-frame audio metrics. git diff --check passed with the existing
LF-to-CRLF notices. No dependency changes or commits.

Important discovered limitation: impact was zero on all three complete tracks.
A first coverage assertion incorrectly required impacts from every track; the
report now distinguishes continuous-control variation from absent event
coverage. Read-only diagnosis found the actual structural cause: live/replay
call onset detection AFTER VisualSignalConditioner, whose max_delta is 0.12,
but the onset detector requires a rise greater than 0.2. Such an onset cannot
occur. A synthetic alternating zero/full-scale reproduction confirmed maximum
rise 0.12 and zero events. Earlier synthetic shader impact tests bypassed this
audio path and therefore never verified real-song event delivery.

Recommended next bounded task: review moving onset detection ahead of visual
conditioning while preserving conditioned continuous controls and existing
normalization. Verify all three tracks and regressions for the accepted worlds,
because restoring impact would affect every world. No audio correction has
been implemented at that time; the user subsequently approved it and the
current correction entry above supersedes that status.

Evidence: ignored work/elemental/music/{balloon,chasing-you,warbot-jazz}/,
work/elemental/music/summary.json and review-sheet.png. Existing source MP3s
and decoded WAVs were reused unchanged. Current tracked changes now also include
app/visuals/replay_test.py; the rest of the Water file list below still applies.

### Initial implementation and synthetic verification

Checkpoint reconciliation: HEAD is `aa44d54` (Refine Geometric corridor material
gathering). The user explicitly accepted that checkpoint and the preceding
Cosmic/Geometric foundations. Pending-review labels in the historical entries
below are superseded by that instruction; they are not current acceptance gates.
Tracked files were clean before Water. Existing untracked research folders and
root helper scripts were preserved. No commit has been made for Water.

Water is an isolated oblique liquid expanse: the actual shared DreamWave field
is gathered into submerged dye currents beneath a multi-scale wave surface.
Surface normals drive selective reflections and small refractive offsets.
Bass raises broad waves, flux shears currents, sparkle reveals fine ripples and
reflections, and the existing impact envelope disturbs a bounded patch. Quiet
and silence retain moving water and dark channels. The Organic membrane is not
used as Water's surface. Normal blend scheduling remains unchanged.

Changed: app/visuals/shaders/dream.frag, app/visuals/shader_test.py,
app/visuals/live_visual_test.py, this handoff. Added: run_water_music.bat and
ELEMENTAL_DEVELOPMENT.md. Renderer, uniforms, audio analysis, dependencies,
Cosmic geometry/star code and Geometric surface code remain unchanged.
Replay inherits the new live-state choice without a replay source edit.

Verification actually executed in the existing .venv on the RTX 3070 Laptop GPU:
- Water GPU test: 36 silence/quiet/active/chorus samples through 600 seconds;
  spatial structure, dark-space coverage and highlight headroom assertions pass.
  Four independent audio controls produce visible pixel changes. Silent motion,
  a 1/60-second continuity sample and 181 renderer-integrated attack/release
  frames pass. Largest integrated mean frame change: 3.494/255.
- 360 additional Water draws across 1280x720, 1920x1080, 720x1280 and 2560x1080.
  At 1080p, median GPU draw time 2.761 ms / p95 2.807 ms (80 timed samples after
  warm-up). This excludes live capture, presentation and end-to-end latency.
- Final quiet/active/chorus contact sheet, full-HD and portrait PNGs inspected.
  These show a broken reflected-light path, submerged colored streaks, larger
  chorus waves and retained dark channels. Captures are not live music review.
- Accepted-shader comparison: 72 cases / 144 GPU frames across all six existing
  state routes, three input levels and four times. Final maximum difference
  1/255 per channel, within the test's explicit rounding tolerance.
- Geometric regression: 423 frames pass, minimum contrast 4.946.
- Cosmic handoff: 19 frames pass; moon opacity: 122 frames pass (155 opaque lit
  centers, 27 hidden centers); blended sweep: 183 frames pass, minimum 10.038.
- Parameter mapper parity test passed; live/replay CLI help confirms `water`.
- git diff --check passed with existing LF-to-CRLF conversion warnings only.

One intermediate highlight test failed narrowly at chorus/67s. Final Water
tonemapping was corrected; the complete Water test then passed. Evidence and
metrics are under ignored work/elemental/final; legacy regressions are in
work/elemental/*-regression. The baseline shader is work/elemental/accepted.frag,
exported from aa44d54 before edits.

Review with run_water_music.bat (real system audio) or
run_state_preview.bat water (fixed synthetic inputs). Neither was left running.
At this initial stage live music and user aesthetic review were pending; the
resumed review above supersedes that status. Procedural gathering has no frame history;
no automatic Water transition or fluid simulation was added. Read
ELEMENTAL_DEVELOPMENT.md for commands, limits and the five future directions.
The optional second element was deferred to keep this pass focused on Water.

Next: user reviews Water with music, then approves a commit if satisfied.
Do not stage or commit pre-existing untracked research/helper files.

## Historical pass: Geometric material gathering (accepted as aa44d54)

The user accepted the preceding Geometric/star work and committed it as
`d8053d6`. Historical pending-review statements below describe earlier work.
At the time of this historical entry the pass was uncommitted; the user has
since accepted and committed it as aa44d54. See the current entry above.

Changed files: app/visuals/shaders/dream.frag, app/visuals/shader_test.py,
and this handoff. No renderer, uniforms, audio, dependencies, or launchers changed.
Untracked root-level live_visual_test.py and shader_test.py remain untouched.

The corridor is traced once before the shared DreamWave field is evaluated.
Its axial surface coordinates gather/stretch/mirror-fold that actual field
onto the walls, floor, ceiling and turned passage. The final material uses
the field substantially, including its moving colored artifacts, rather than
an 18-percent tint. Recessed panel joints, derivative-filtered veins, local
edge pulses, inherited glyph colors and darker openings add bounded detail.
Bass/impact pressure cannot pinch the chorus corridor closed. Surface hit
refinement removes the coarse stepping visible in the previous captures.

The isolated Geometric preview no longer activates the timed Cosmic takeover.
A 32-second turning capture revealed a camera-inside-wall blank frame; the
camera now approaches the junction before sliding sideways. Existing segment
turn timing remains, not a new path/camera system. Cosmic stars, bodies, rings,
moon materials and their depth code are unchanged. Shared-field changes can
still affect material inherited by the Cosmic canvas during mixed states.

Verification actually executed on the GPU:
- Same-time quiet/active/chorus PNG captures at 18 seconds, visually inspected.
  Quiet is dark blue-violet, active carries colored material along surfaces,
  and chorus is brighter/more detailed while retaining an open dark passage.
- Extra turning PNGs inspected at 32, 33, 66 and 67 seconds.
- shader_test.py --geometric-test work/geometric-gather/geometry-test:
  423 frames across three input profiles and both turn directions; passed,
  minimum spatial contrast 4.946. This guards blank frames, not aesthetics.
- shader_test.py --sweep work/geometric-gather/sweep: 183 frames and existing
  washout assertions passed; minimum spatial contrast 10.038.
- shader_test.py --handoff-test work/geometric-gather/handoff: 19 frames,
  Cosmic space isolation and boundary continuity passed.
- moon_opacity_test.py: 122 GPU frames passed, 155 opaque lit and 27 hidden
  moon centers.
- git diff --check passed; Git reports only existing LF-to-CRLF warnings.
  Three tracked files modified, nothing staged or committed; all pre-existing
  untracked research/helper files remain in place.

Evidence is under ignored work/geometric-gather/. Preview remains
run_geometric_preview.bat (synthetic inputs, not live audio). Live music,
full-resolution performance and continuous-motion acceptance remain untested.
The mirrored material repeats; openings imply depth rather than tracing extra
rooms. Gathering is a reversible procedural domain transformation, not stored
past frames or persistent captured imagery. Existing timed/audio state weights
still select the world; phrase-aware scheduling is not implemented here.

Next: user reviews this one pass. Do not automatically commit or expand scope.

## Previous checkpoint: Geometric world and continuous star drift

An external geometry pass added isolated_geometric_scene to
app/visuals/shaders/dream.frag. It renders a procedural corridor with long
straight spans, committed turns, varying width/height, material color swatches,
and sparse falling glyph columns. It is available in the existing isolated
Geometric preview via run_geometric_preview.bat; the normal shared state
composition also mixes it when the existing geometric weight is active. This is
an uncommitted prototype awaiting user visual acceptance, not an architectural
replacement or a new renderer.

The same pass introduces star_time and star_rate in the existing
app/visuals/renderer.py. The renderer eases a positive star clock from normal
speed toward a faster chorus speed, then the shader moves three depth sheets in
one-way, slightly parallel headings. They wrap naturally through the procedural
field rather than reversing after an audio beat. High chorus energy lengthens
and thins their wakes; quiet stars vary in brightness/twinkle. This supersedes
the prior direct time-times-current-audio star experiment, which could twitch.

Verification actually run after this pass: Geometric quiet and active captures
at 18 seconds were visually inspected; the 183-frame GPU sweep rendered; the
19-frame handoff continuity test passed; the 122-frame moon opacity/occlusion
test passed (155 lit centers, 27 hidden centers); and renderer, shader-test,
and live-entry Python compilation passed. git diff --check passed with only
the existing LF/CRLF warnings. No live music run, frame-rate measurement, or
user acceptance of the Geometry/star changes has happened yet.

Untracked root-level live_visual_test.py and shader_test.py exist beside the
project files. The actual launchers use app/visuals versions, so these root
copies were not run, edited, staged, or treated as source of truth. Preserve
them until the user decides whether they are intentional references.

## Current continuation: planetary canvas and handoff

Latest bounded pass: user accepted the three moon identities. Added selective
planet/ring vividness via cosmic_vivid_material in dream.frag. Drive uses
existing conditioned scale/flux/sparkle (45/35/20 percent), with a quiet dead
zone and bounded saturation/brightness. Planet adjustment precedes lighting;
ring adjustment retains existing shadow modulation. Moons, stars, geometry,
audio analysis and diagnostic land/ocean colors are unchanged.
At 18s canvas, quiet before/after PPM hashes match exactly; active PNGs were
visually compared (richer rings, modest planet lift). Moon test (122 frames),
handoff test (19), sweep (183) and diff check passed. Captures/tests are under
work/cosmic-vivid. Live aesthetic review is pending; no commit made.

Moon–ring interaction is now implemented as a small colored dust wake around
each orbital position. It uses existing sparkle/flux and the assembly envelope;
it does not alter depth, geometry or moon opacity. GPU regressions remain the
acceptance gate. The follow-up tuning now gives the wake a longer tail and
stronger near-moon ring density/color, fading continuously behind each moon.
Dust persistence and star motion remain future bounded passes. User review of
this stronger tuning is pending. The latest refinement bends the tail along
the ring curve and samples each moon's animated material for its color.

The next small adjustment gives the inner, middle and outer moons rates 0.52,
0.42 and 0.32 respectively, with their dust wakes synchronized.

Star rotation is now implemented as a shared center-locked field with input-
scaled exposure trails. Quiet captures remain short; active captures show
curved light dashes. The latest tuning shares the planet spin clock at a slower
baseline, accelerates with audio, tapers trail ends, and preserves varied
twinkling point stars during dwell. User review is pending.

The field is layered into three parallel-offset depth bands with different
rates, so stars do not move uniformly. A chorus-only threshold controls longer
exposure trails; the shader test's chorus profile captures that case.

Latest review: user likes live canvas; requests more vivid planet/rings and
three moons with their own dye/fire/layered-candy identities. Implemented only
the moon material step in dream.frag, with CPU reference updates in
moon_opacity_test.py. Orbits, opacity and shading remain unchanged. 122-frame
moon test passed (157 lit centers, 26 hidden centers); 183-frame sweep and
19-frame handoff checks passed. Captured PNG reviewed; live motion acceptance
is pending. Ring disturbances, stronger planet/ring color and coherently
rotating star trails are recorded in COSMIC_DEVELOPMENT.md, not implemented.

User review: gather and release accepted as a foundation; moons remain solid
and occlude behind the planet, but intersect rings. The synthetic preview did
not react to music because it uses fixed inputs, not audio capture. Next review
uses run_cosmic_music.bat (live canvas hold), or its transition argument for
the 40-second cycle with live audio. Normal live launch remains unchanged.

Creative backlog from this review: moon/ring dust disturbances, evolving
surface/ring color and material during gathering, release into a distinct next
vocabulary, slower floating or musical camera pressure, shared ring-plane/view
motion, and slow star drift with size/brightness changes. These are separate
bounded tasks, not implemented or accepted here. Preserve solid body depth
while exploring deliberate material effects; do not reintroduce accidental
transparency. The user requests no unsolicited usage updates.

Live-preview routing verification: Balloon.wav completed 40 seconds / 938
analyzed and GPU-rendered frames in each of canvas and transition modes. CSV
confirmed varying scale, movement and sparkle, not fixed preview values.
CLI help, Python compilation and diff checks passed. Actual live loopback
playback and the new BAT have not been exercised this turn. No shader or
audio-analysis changes were made for this routing step. No commit made.

The user accepted the rebuilt geometry as a better foundation and authorized
returning to the original planetary-canvas vision. The existing field is now
remapped into spherical coordinates and passed as opaque material to the same
depth composition used by the Cosmic diagnostic. A shared envelope contracts
the field, introduces rings/moons, holds the planetary world, and releases it.
The live timing is a provisional 140-second cycle; music controls the existing
surface expressions, small system pressure and ring brightness. This is not
phrase-aware timing or a feedback/particle transport simulation.

Double-click run_cosmic_transition.bat for the 40-second diagnostic cycle.
`run_state_preview.bat canvas` holds the mapped DreamWave surface indefinitely.
`cosmic` remains the accepted land/ocean geometry reference. The normal live
launcher now uses the new handoff, with the old competing Cosmic warp disabled.
See COSMIC_DEVELOPMENT.md for exact phase times, geometry ownership, test
commands, limitations and bounded assignments for smaller models.

Source files changed in this continuation: dream.frag, shader_test.py, this
handoff; added COSMIC_DEVELOPMENT.md and run_cosmic_transition.bat. Renderer,
audio processing and dependencies were not changed. The user subsequently
accepted gather/release as a foundation; live musical feel is still pending.
Nothing has been committed.

Verification for this continuation: the 183-frame GPU sweep passed (minimum
contrast 10.07); the moon test passed 122 GPU frames, including 157 opaque and
26 hidden center checks; the new handoff test passed 19 GPU frames checking
dark space during the hold and continuity at phase boundaries. A 120-second
Balloon.wav replay completed with 2,813 analyzed/rendered frames. Python
compilation and git diff --check passed. The captured nine-frame sequence was
visually inspected. This does not constitute live-audio or real-time motion
acceptance. Outputs are under work/cosmic-handoff.

## Previous checkpoint: isolated Cosmic composition rebuilt

Historical results below describe the preceding implementation; the continuation
above supersedes its pending-integration status and blended-sweep result.

The isolated Cosmic function in dream.frag now uses analytic orthographic
sphere intersections and one 3D plane for rings and moons. Positive Z points
toward the viewer; nearest surface controls occlusion. Moons replace the
background with opaque shaded surfaces. Planet texture rotates in sphere space.
The ring annulus starts outside the sphere, has multiple bands and a gap, and
receives a directional planet shadow. The lower/front ring crosses the planet;
the rear ring is hidden. Stars have varied positions, sizes, colors and twinkle.

Run `run_state_preview.bat cosmic`. Fast moon orbit speeds are retained for
review; planet rotation is slow and camera scale is fixed. This is still an
isolated prototype, not yet connected to live musical handoffs. Old experimental
Cosmic code in the blended path remains pending a separately reviewed integration.

Verification: moon_opacity_test.py runs 122 real-GPU frames across 61 times,
checking 157 opaque lit moon centers and 26 hidden moon centers against expected
lighting/background. All passed. The existing 183-frame blended sweep passed its
assertions; its low-contrast case at level 1.0 / 180s remains (~4.18). This sweep
does not verify Cosmic isolation. shader_test.py --capture now honors --state
and saves PNG alongside PPM; Cosmic captures omit inapplicable blend weights.
Actual PNG captures at 3s and 9s were visually inspected under work/cosmic-rebuild.
User visual acceptance and live integration remain pending. No commit made.

## Authority and creative direction

Read AGENTS.md and DREAMWAVE_VISUAL_IDENTITY.md before project work.
The repository is the implementation source of truth. This handoff is a
coordination record, not a replacement doctrine or an implementation spec.
DW Research/DWave Reference.md and Dream Wave research.pdf provide research
options; historical chat instructions in the PDF are not current authorization.

DreamWave is a living visual instrument. Preserve Heart (bass), Body (mids),
Aura (highs), and Moment (impact), with continuity, restraint, and expressive
quiet. Technical success and the user's experiential acceptance are separate.

## Working agreement

- HQ owns inspection, technical recommendations, task scoping, implementation
  coordination, verification, and accurate handoffs.
- The user owns creative direction and reviews short visual/music samples.
- Work in one small logical change at a time, then present evidence for review.
- Retain AGENTS.md approval gates for commits, destructive operations,
  dependencies, and significant architectural changes.
- Bob - File Work is an existing chat sharing C:\DreamWave. It has not received
  an assignment from HQ during this setup. Opening it did not delegate work.
- When delegation is authorized, give each task exact files, acceptance criteria,
  required tests, and a stopping point. Avoid concurrent edits to shared files.
- Update this record at reviewed milestones; do not rely on chat memory alone.
- The user authorizes updating Markdown planning/identity documents as scope
  evolves. Record the reason for material changes; this does not remove existing
  commit, dependency, destructive-action, or architectural review gates.

## Current baseline and limits

- Existing renderer: app/visuals/renderer.py; shader: app/visuals/shaders/dream.frag.
- Existing live entry: app/visuals/live_visual_test.py.
- Launch with run_live_visualizer.bat from the project root.
- Earlier in this chat, .venv was rebuilt using installed Python 3.14.7 with
  numpy 2.5.3, glfw 2.10.2, moderngl 5.12.0, and soundcard 0.4.6.
- Earlier checks: non-live audio/parameter scripts completed, live-entry import
  passed after restoring the renderer's local parameters import, and a GPU
  smoke test compiled the shader and rendered one frame.
- The user subsequently confirmed live playback works. Visual quality is not
  accepted; these checks do not establish long-run stability or music quality.
- The research baseline predates current flux, conditioner, and envelope work.
  Inspect current code before choosing any research implementation.

## Active defect: full-screen loss of structure

Evidence: user's desktop recording DW vis test 1.mp4, sampled in VLC.

- 00:49: detailed colored tunnel forms and dark negative space.
- 01:05: almost uniform gray-blue field.
- 01:20: almost uniform dark-navy field.
- 01:47: detailed tunnel forms return.

These are discrete observed frames, not continuous video analysis. The user
identifies onset around 01:04. Audio synchronization was not assessed.
The video timestamps are not known shader clock values. The shader cause is
unconfirmed. Earlier confident claims about field collapse were premature.

## Next bounded task

Diagnose and reproduce the disappearing-detail state in the existing renderer
and shader before selecting a correction. Inspect coordinate transforms,
weights, masks, palette evaluation, and output composition. Distinguish findings
from hypotheses; do not assume tunnel compression is the sole cause.

Prefer extending an existing standalone visual test with deterministic input
and time cases if needed. Establish reproducible good/bad frames and record the
inputs used. Any temporary diagnostic output must be opt-in and bounded.

Acceptance for a later fix:

- A previously failing reproducible case retains readable intended structure.
- Good tunnel states retain their depth, palette, and negative space.
- Quiet music can remain restrained; brightness/noise is not a substitute for form.
- Actual shader compilation/render checks pass, followed by the user's music review.
- Audio normalization remains unchanged during this isolated visual correction.

## Milestone order, subject to review

The supplied Streamlined Development Plan and Pinky and the Brainstorm post
Stage 0 refine the older research queue. Their historical instructions to other
agents and model experiments are context, not current assignments.

0. Stabilize: compilation and live launch were demonstrated; repair the observed
   visual disappearance, review the result, and seek approval for a checkpoint.
1. Establish distinct Organic, Geometric, and Cosmic visual vocabularies using
   existing audio inputs. A frame should communicate its form without a label.
   Fixing the blank-field defect alone does not satisfy this milestone.
2. Develop color identity throughout the world, including vivid taffy colors and
   intentional dark space; avoid permanent muddy/burnt color.
3. Develop musically meaningful transitions with dwelling and maturation.
4. Develop bounded temporal life and event persistence; inspect existing state
   first rather than reimplementing envelopes already present.
5. Consider controlled visual feedback only after state behavior is established.
6. Improve audio intelligence using multi-track evidence and existing experiments.
7. Address measured performance and output/product usability.
8. Formalize broader architecture only where demonstrated needs justify it.

Review at each milestone. Future worlds, suggestive imagery, an occasional eye,
and minimal Bonk/Dance controls are creative direction, not immediate build tasks.

Do not introduce a second renderer, preset runtime, or unrelated effects to
address this defect. Do not treat the research wish list as a build commitment.

## Working-tree caution

### Long-term Cosmic/worlds vision

The user expanded the Cosmic direction into a living sequence of impossible
worlds rather than a single planet effect: zooming from a ringed planet to
multiple suns, intersecting solar systems, galaxies, pulsars, and other deep-
space structures; then handing off into brief surreal terrestrial or mythic
visions such as dancing clockwork figures, an elephant crossing, migrating
birds, a resting swordsman beneath a tree of life, a waterfall with a unicorn,
dragons, or starships before returning to the Cosmos. These are long-term
creative targets, not a request to implement every image now.

The engineering implication is layered world composition: each world must be
isolatable, visually coherent on its own, and able to release through a
controlled handoff. The current Cosmic planet is the first foundation. Future
imagery should be introduced as bounded world modules or visual-language
layers, not as an unstructured accumulation of shader branches.

### Accepted washout repair

The real-GPU deterministic sweep added to shader_test.py rendered 183 frames
at 320x180 across fixed input levels and shader times. Before the correction,
three frames were exactly uniform and several nearly uniform. Using the domain
before tunnel/horizon scrolling for fractal inversion, with a denominator floor,
removed all exactly uniform frames in the same sweep. Four reproduced cases
have explicit contrast regression assertions. One case at high input and 176s
remains low-contrast and needs further investigation after this change's review.
This is synthetic GPU evidence, not an exact replay of the recorded live inputs.
The user accepted the live visual improvement and approved checkpoint 01f4249.
No audio code changed.

### Organic membrane and root variation accepted

After approximately eight minutes of music playback, the user liked the slow,
consistent blue-violet membrane as a resting/background scene during quieter
audio. Preserve that calm home character. Organic visual vocabulary is still
being developed; this does not complete Milestone 1.

The next small experiment adds bounded local flex from existing flux and a
small traveling ripple from existing impact. Neither changes the animation
clock, palette, audio analysis, or state weights. Quiet flux <= 0.08 and impact
<= 0.10 introduce no added motion. Existing shader_test.py now supports quiet
and active --profile presets for --capture, saving inputs and state weights.

Verification: quiet before/after capture at shader drift time 100s was pixel-
identical; active captures differed and were visually inspected. The 183-frame
real-GPU sweep and four washout assertions passed. The previously noted
low-contrast case at 176s remains. The user accepted the active flex after about
15 minutes of playback. Membrane and capture tools are committed as baed993.
The palette is provisional, not a permanent color restriction.

Current experiment: 31 connected, tapered procedural branches in the membrane's
warped domain, gradually replacing its body/ridge through root_mix. This uses
a provisional slow dwell cycle (about 157 seconds), not music-aware scene
selection. Existing flux bends branches; audio and palette logic are unchanged.
Capture metadata includes root_mix (a blend amount, not a normalized state
weight). Quiet, active, and intermediate frames were visually inspected: the
result reads as branching roots/veins, not yet a dense fungal web. The 183-frame
GPU sweep and washout assertions passed. The user accepted the live feel as
viscous and organic, mostly calm with occasional forward presence.

### Optional audio replay

`app/visuals/replay_test.py` replays a decoded 48 kHz, 16-bit WAV through the
same analyzer, mapper, and GPU renderer without playing audio. It is not used by
`run_live_visualizer.bat`; private audio and generated metrics remain ignored.
The renderer accepts song time explicitly while live rendering keeps the wall
clock.

Deferred Cosmic idea: existing imagery gathers inward, forms a planet and rings,
dwells, then morphs, erupts, or collapses. Preserve continuity; this is outside
the current Organic experiment.

At setup, existing changes include live_visual_test.py, renderer.py, dream.frag,
the untracked research directory, launcher, and three helper scripts:
apply_3b.py, verify_invariants.py, verify_strings.py. Preserve them.
The shader text-check scripts contain stale expectations and are not rendering
tests. Do not rerun apply_3b.py: it is a mutating patch script.
No commit, deletion, or cleanup was performed as part of this setup.
