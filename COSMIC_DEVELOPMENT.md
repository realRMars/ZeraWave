# Cosmic development and maintenance

Updated 2026-09-26. Read AGENTS.md and DREAMWAVE_HANDOFF.md first.

## Intended experience

DreamWave's existing imagery contracts, curves onto a rotating planetary
surface, dwells in black space surrounded by rings and moons, and unfolds back
into the field. The planet is the material's new canvas. User acceptance of
the geometry prototype is not acceptance of the live handoff.

## Current implementation

Selective vividness: cosmic_vivid_material enhances existing hue/chroma rather
than introducing a new palette. A bounded scale/flux/sparkle mix drives it;
quiet drive <=0.08 leaves color unchanged. Planet albedo is enhanced before
lighting; ring color retains its shadow and band structure. Only canvas/live
material participates, not diagnostic land/ocean, moons or stars. Synthetic
quiet/active comparisons and GPU regressions passed; live review is pending.

Moon–ring dust pass: each moon now produces a short, localized colored wake in
the shared ring plane. The wake follows the existing orbit phase and is limited
by sparkle/flux plus the assembly envelope; it changes ring color only. Ring
depth, planet shadow, moon opacity and occlusion are untouched. This is a
bounded procedural disturbance, not particle transport or frame feedback. The
latest tuning widens the lateral wake, lengthens its decay, and increases local
ring density/color near each moon before fading down the tail. The active canvas
capture was inspected; moon opacity, handoff and sweep regressions passed.
The latest refinement evaluates the wake in polar orbital coordinates, so it
curves along the projected ring ellipse. Its tint samples cosmic_moon_material
at the trail angle, allowing color to evolve with the parent moon.

Orbital timing now follows the intended hierarchy: the closest moon runs at
0.52, the middle at 0.42, and the outer at 0.32 shader-time units. Dust wakes
share those rates, and the opacity regression uses the same expected positions.

Star motion pass: the field rotates uniformly around the scene center. Quiet
input keeps stars close to points; rising flux/sparkle increases a five-sample
exposure arc, producing curved streaks. This is a procedural sample blur, not
persistent particles or framebuffer history.

The latest star tuning uses the planet's 0.035 spin clock at a slower baseline,
then accelerates it with audio drive. Trail samples taper toward their ends in
both thickness and brightness. Quiet dwell collapses the exposure to points and
retains seeded brightness variation with gentle twinkle.

The star field is now layered into three parallel-offset depth bands. The
integrated visual clock gives them continuous momentum, each band has a
different rate, and only a high-energy chorus threshold lengthens the exposure.
The shader-test capture tool accepts the chorus profile for that deterministic
full-energy inspection.

Moon material pass: three independent animated sphere-space palettes—cyan/pink
liquid-dye folds, orange/blue-white fire bands, and traveling rainbow candy
shells. These are procedural suggestions, not fluid/fire simulations. They use
elapsed time, not beat synchronization. Existing lighting/eclipse still shades
solid surfaces; projection, orbit and depth logic are unchanged. The CPU color
reference in moon_opacity_test.py now checks these materials under lighting.

User-reviewed backlog: increase planet/ring vividness selectively; let moons
disturb/reform ring dust or acquire dust-colored trails; rotate the star field
coherently with longer curved light trails at higher speed. Keep star rotation
shared, not independent random star motion. None of those effects is in this
moon-only pass. Review each separately before expanding scope.

Everything uses the existing renderer, uniforms and fragment shader. No new
dependencies, textures, framebuffer feedback or audio analysis were introduced.

- `app/visuals/shaders/dream.frag`: `cosmic_handoff` supplies a continuous
  envelope. Main remaps the existing field's coordinates from screen space onto
  a rotating sphere. Its resulting color becomes opaque planetary albedo in
  `isolated_cosmic_scene`. That function handles all planet/ring/moon depth.
- `app/visuals/shader_test.py`: previews, reproducible PNG/JSON captures,
  ordinary blended sweep, and the transition-specific `--handoff-test`.
- `app/visuals/moon_opacity_test.py`: actual GPU checks of opaque shaded moon
  centers and far-side planetary occlusion across complete orbits.

The field is evaluated once per pixel. This is procedural coordinate remapping,
not preserved frame history or particles physically tracking gravity. Surface
patterns continue evolving. The live sequence repeats on a provisional 140s
clock: gather 24–44s, hold 44–88s, release 88–112s. Music animates existing
surface parameters, bounds whole-system pressure to 2%, and modulates ring
brightness. It does not yet decide the arrival/departure time.

The old Cosmic weight is disabled in the shared warp system so it cannot
compete with the depth-composited takeover. Earlier obsolete overlay blocks
were removed. Some dormant weight/maturity expressions remain; do not undertake
unrelated shader cleanup during a visual adjustment.

## Run and isolate

For music review, double-click `run_cosmic_music.bat`: it holds the planetary
canvas using the existing live system-audio pipeline. Its optional `transition`
argument runs the 40-second handoff with live input. It plays no audio itself.
The older state/transition previews below remain synthetic fixed-input tools;
they do not listen to music. Normal live launch still defaults to blend.
Offline replay now accepts `--state canvas` or `--state transition` for the
same shader routes, without playing the WAV aloud.

From C:\DreamWave:

```powershell
.\run_cosmic_transition.bat
.\run_state_preview.bat canvas
.\run_state_preview.bat cosmic
.\run_state_preview.bat organic
.\run_state_preview.bat geometric
.\run_live_visualizer.bat
```

`transition` is a 40s test cycle: field 0–3s, gather 3–11s, planetary hold
11–24s, release 24–35s, field 35–40s. `canvas` holds the actual DreamWave
material on the sphere. `cosmic` holds the land/ocean geometry reference with
fast test moons. Normal/live and canvas moons orbit more slowly. Close and
relaunch an existing window after shader edits: shaders load at creation.

## Depth rules: preserve these

The camera looks down -Z; larger Z is closer. Sphere depth is center.z plus
the square root of radius squared minus projected distance squared. A missing
intersection returns -100. Ring and moon positions share axis_u and axis_v.
The ring coordinate is inverse-projected (divide by the opening factor).
Its inner physical radius must exceed the planet radius including edge width.

Compare actual depths, never screen-left/right or a faded near/far flag.
Moons replace the covered scene color; `scene += moon_color` is transparency,
even when the output alpha is 1. Shade the opaque material with normals and
light direction. Do not dim opacity to represent night or an eclipse.

All scale changes must apply to the complete system. Keep the isolated geometry
reference stable while experimenting with source-material mapping. Never add a
late shared artifact overlay after the final Cosmic composition.

## Verification commands

```powershell
.\.venv\Scripts\python.exe app\visuals\moon_opacity_test.py
.\.venv\Scripts\python.exe app\visuals\shader_test.py --handoff-test work\cosmic-handoff\sequence
.\.venv\Scripts\python.exe app\visuals\shader_test.py --sweep work\cosmic-handoff\sweep
.\.venv\Scripts\python.exe app\visuals\shader_test.py --capture work\cosmic-handoff\capture --state canvas --seconds 18 --profile active
```

Open the PNG output and inspect it. PPM is also saved for compatibility.
Capture honors --state; Cosmic geometry bypasses blend weights, so its weight
dictionary is intentionally empty. `cosmic_takeover` is separate from the old
`cosmic` weight: the latter is now zero. Other recorded weights describe the
source material, not the final scene's visibility.

The blended sweep only asserts specific historical contrast regressions.
Passing it never proves a ring, moon, transition, or artistic result is correct.
The handoff test checks rendered black-space isolation and limits at timing
boundaries (2ms samples), not subjective motion quality or performance.
The opacity test checks centers, not every antialiased limb or moon/moon overlap.

## Bounded assignments for smaller models

1. Read the current implementation and the last accepted screenshot first.
2. Name the one observed defect and the specific function to change.
3. Preserve projection/depth conventions. Cosmetic work should only touch
   palette, bounded modulation or surface detail—not geometry ownership.
4. Capture before/after at the same state, time, dimensions and audio profile.
5. Run the relevant tests above and inspect images before claiming improvement.
6. Report what was actually observed, what remains uncertain, and Git status.
   Ask for commit approval after user review.

Escalate for review when changing depth conventions, coordinate ownership,
renderer interfaces, feedback/history, or live state scheduling. Do not explain
a failure with speculative driver/uniform issues without a reproducer. Do not
keep requesting a user restart after an unverified patch. Use deterministic
captures to demonstrate the patch reached the intended branch.

Next review is the gather/hold/release feel with music. Frame-history transport,
music-aware scheduling, richer surface vocabulary, dust transport and broader
solar-system worlds are future steps requiring separate bounded changes.
