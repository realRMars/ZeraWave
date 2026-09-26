# Elemental vocabulary: Water foundation

Updated 2026-09-26. Base checkpoint: `aa44d54`, accepted Geometric material
gathering. Read AGENTS.md and the current DREAMWAVE_HANDOFF.md entry first.

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

- **Fire:** strongest next contrast. Vertical, translucent flame sheets rise
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
