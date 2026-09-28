# Cosmic and Elemental maintenance contracts

This is a concise preservation reference extracted before the detailed
development narrative was archived. It records maintenance boundaries, not a
backlog.

## Cosmic

- Cosmic uses depth-composited projection: the field becomes planetary albedo,
  and `isolated_cosmic_scene` owns planet/ring/moon depth. Compare actual depth,
  not screen position; keep projection, shared ring axes, and complete-system
  scale coherent when changing geometry.
- Moons replace the covered scene with opaque, normal/light-shaded material.
  Eclipse/night treatment belongs in lighting, not alpha. The opacity regression
  samples moon centers and far-side planetary occlusion; it does not prove every
  antialiased limb or moon/moon overlap.
- Cosmic surface motion is currently bounded procedural disturbance rather than
  transported particles or persistent feedback. Treat a proposal to change that
  representation as a separate review, rather than inferring that a surface
  adjustment requires it.
- Preserve authored sky/material behavior unless an explicitly reviewed palette
  or detail selection says otherwise. For a depth/projection change, compare
  before/after at matching state, time, dimensions, and input profile; then
  inspect motion as well as captures.

Use a fresh review destination for new checks:

```powershell
$review = "work/review/cosmic-$(Get-Date -Format yyyyMMdd-HHmmss)"
.\.venv\Scripts\python.exe app\visuals\moon_opacity_test.py
.\.venv\Scripts\python.exe app\visuals\shader_test.py --handoff-test "$review\handoff"
.\.venv\Scripts\python.exe app\visuals\shader_test.py --sweep "$review\sweep"
.\.venv\Scripts\python.exe app\visuals\shader_test.py --capture "$review\capture" --state canvas --seconds 18 --profile active
```

The preserved historical Cosmic evidence paths are
`work/cosmic-handoff/sequence`, `work/cosmic-handoff/sweep`, and
`work/cosmic-handoff/capture`; do not reuse them as new output destinations.
The handoff test checks black-space isolation and timing-boundary limits; the
sweep retains specific historical contrast regressions. Neither substitutes for
visual motion review.

## Elemental

- Preserve each world’s structural depth and authored presentation; optional
  materials and details may affect pigment or supported coordinates but must not
  erase terrain, water, cloud, vapor, or solid silhouettes.
- Water remains a procedural surface rather than a fluid simulation. Fire growth
  and Aftershock events remain bounded and deterministic enough for test/replay.
- Air, Earth, Fog, and Plasma retain form-specific depth, clocks, and regional
  transitions. Keep opaque surfaces opaque; vapor is the deliberate translucent
  exception.
- Preserve stable layer IDs and saved-session compatibility. Review changes in
  isolation and in Main motion, including quiet and sustained passages.

## Shared verification and audio boundaries

- Detect onsets from the intended normalized/smoothed band signal before
  `VisualSignalConditioner` applies visual slew limiting; then carry the onset
  values through `AudioFrame.impact` into visual mapping. A sustained level is
  not a fresh onset.
- Baseline-dependent checks compare an explicitly supplied accepted shader and
  only their sampled cases. Keep the baseline/evidence path with the result;
  do not describe a passing comparison as full live, artistic, or device
  validation.
- `app/visuals/shader_test.py --preservation-test <baseline>` compares accepted
  held-world pixels. World-specific commands with `before.frag` and an output
  folder preserve their corresponding evidence trail. See the
  [Cosmic snapshot](history/2026-09-28-cosmic-development.md) and
  [Elemental snapshot](history/2026-09-28-elemental-development.md) for the
  dated command/evidence context.

Historical evidence, accepted decisions, and limitations remain in
[history](history/README.md).
