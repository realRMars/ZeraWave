> Current status — October 5, 2026: Robert passed this development checkpoint
> for commit and normal GitHub push. The original Builder report below preserves
> its pre-acceptance status and engineering limits. See the
> [current handoff](../../ZERAWAVE_HANDOFF.md#current-measured-performance-candidate)
> and [publication receipt](../../work/publication-performance-20261005/review-index.json).

# Measured performance fixes — actual results

Assignment: Bob the Builder, October 4–5, 2026. Implementation is ready for
Robert's Studio review and checkpoint decision. This is engineering validation,
not artistic acceptance or a critic dispatch. No commit, push, release, docking,
new scene, dependency installation or shared planning-document edit was made.

## Source and scope

Work root: `C:\ZeraWave`; HEAD remains
`b2aacd11d7d3a8d39bb9d2f5592659fd3d2d999b`. The authoritative baseline is the
**pre-task dirty tree**, including Fractal/Main and startup correction:
[baseline source](../../work/performance-fixes-20261004/baseline-source.json)
and its `baseline/` copies. It contained 165 app source/data files and 51 Git
status entries; HEAD alone does not identify it. Final bindings, preservation
checks, exact changed-file hashes and the patch are in
[final-source.json](../../work/performance-fixes-20261004/final-source.json),
[task-diff.patch](../../work/performance-fixes-20261004/task-diff.patch), and
[evidence-index.json](../../work/performance-fixes-20261004/evidence-index.json).

Raw `dream.frag`, Fractal source, authored JSON, audio analysis and unrelated
pre-existing work retain their baseline bytes. Audio optimization transforms the
integrated shader in memory. AGENTS.md, ROADMAP.md and ZERAWAVE_HANDOFF.md retain their baseline
bytes; README.md matches the prior audit hash. Visual direction was not edited. The user's existing settings hash matches the audit. The frozen portable
was not rebuilt or touched by this task.

## Implemented behavior and ownership

- `resolved_audio.py` resolves suitable raw audio consumers once per frame with
  float32 gain/clamp/encoded-input semantics. Local shader values containing
  attenuation or listening descriptors retain their local value and a resolved
  gain. Both endpoint rows and Planet adapters remain independent. Shared
  clocks/context initialize before Fractal warp and restore at scene boundaries.
  Water's exact weighted ingredients resolve once outside height-search and
  normal loops. Storm bracket counts, materials, density and motion stay intact.
- `prepared_program.py` owns one integrated program and its VAO, caches actual
  uniform handles, retains declared values pruned by the compiler for auxiliary
  stages, and rejects undeclared names. NVIDIA limited inlining (`100`) reduces
  cold compilation; other vendors retain their normal policy. A bounded 32×18
  first-use draw finishes before first presentation. All families are already
  compiled; scene entry does not trigger family compilation. The responsive
  existing loading notice remains through first presentation.
- New previews default Captures off; saved choices remain intact. `preview_capture.py`
  owns one worker with two waiting images, drops new captures on backlog and
  drains accepted work on normal close. GL copy/readback stays on its owner.
  Statistics and PNG encoding leave the playback path; drops/errors are reported.
  Replay telemetry streams to CSV with one pending mutable input row, retaining
  iteration/index access without a track-length RAM list.
- Static target/window metadata and read-only default layer profiles are cached.
  Editable profiles remain independent. Inactive Planet preparation still applies
  pending revisions/ACKs. Availability is recomputed when its existing 200 ms
  monitor snapshot is due; audio commands/selection still run each frame.
- Surface targets allocate only for contributing Cavern/Citadel scenes and release
  on exit/resize. Formats stay RGBA32F + RGBA16F + depth: 28 bytes/pixel per
  target, zero unrelated, one held, two overlapping. Unrelated held previews skip
  Cavern row preparation. Main/selected routes that can reach Cavern retain
  necessary bounded preparation: two futures, 24 GPU rows, 64 CPU cached recipes,
  bounded ready window. Removing that preparation caused large entry stalls and
  was rejected.
- `render_scale.py` adds explicit **Full quality (100%) / 75% scale (softer detail)
  / 50% scale (softer detail)** to existing Studio/session launch controls. It
  scales both dimensions and linearly upscales once, preserving authored counts,
  pigments, clocks and audio behavior. Lower tiers change detail, remain opt-in,
  and are not Main's default. Reports record internal/output sizes and quality.
  No adaptive switching or shared organic-canvas deletion was introduced.

The operating guide, technique ownership table and maintenance contracts were
updated. These are reusable presentation/capture/resource helpers; no new artistic
scene/effect registration was required.

## Matched measurements

Device: NVIDIA RTX 3070 Laptop, driver 617.14, GL 3.3; Ryzen 9 5900HX.
Display 2560×1440 at 144 Hz. Existing venv: Python 3.14.7, ModernGL 5.12,
GLFW 2.10.2, NumPy 2.5.3. Thermal/background conditions were not controlled;
per-cell GPU telemetry and drift references remain in JSON.

Hidden GPU comparisons reuse the audit harness, active Studio tuning owner,
identical synthetic loud input/clock schedule, seed 7301, actual 1280×720
framebuffer/shader resolution, swap interval zero, 15 warm + 40 measured frames
per cell, synchronous GPU queries. Query times include the render passes and
are **not visible FPS**. New wrapper records effective internal dimensions and
all app hashes. Complete distributions/tails are retained, not just these medians.

| Held scene | Audit GPU ms | Final GPU ms | Final p95 ms |
|---|---:|---:|---:|
| Dyes | 80.24 | 16.23 | 16.52 |
| Waterfall | 67.27 | 15.64 | 15.97 |
| Sky Citadel | 26.88 | 22.85 | 22.94 |
| Crystal Cavern | 18.97 | 21.09 | 21.53 |
| Marsh | 31.00 | 35.47 | 36.13 |
| Planet Canvas | 19.35 | 21.91 | 22.30 |

The compiler policy trades cold startup/memory for some GPU regressions; it is
not a universal speedup. Final Tidal Strata is ~10.0 ms at 720p versus audit
~3.3 ms. Other final held cells are in `final-owner-loud-bound.json`.
At matched 720p boundaries, Waterfall→corridor crossfade falls **81.27→30.12 ms**,
aperture **39.74→17.35**, river **45.28→19.58**, fold **46.47→18.58**.
Citadel→Molten crossfade falls **52.59→43.25 ms**, iris **38.01→34.40**.
Root→Tidal crossfade rises **21.81→25.43 ms**. Shared canvas is an authored
material input; the audit's bypass changes pixels, so it was retained.

Cold program creation falls **195.76→110.04 seconds**; candidate `create()`
111.29 seconds and first synthetic render 12.11 ms (GPU 7.99 ms).
Peak working set **13.21→6.49 GiB**, private bytes **13.91→6.98 GiB**.
Baseline cold P7 includes its subsequent variant probe, so its guard peak is
process-wide; the initial compile accounts for its cold startup. Final guard's
152.78 seconds covers the entire 635-frame matrix/write, not startup.
Warm program compile ~0.18–0.21 seconds; warm held/Main creation ~0.32–1.40
seconds in hidden checks. Visible Main's warm first present was 1.82 seconds.
Cold visible first presentation was not measured. The cold stall is materially
smaller, still long, and vendor-specific; no fresh-cache wipe or binary package.

Matched 240-frame cProfile render-call median **17.47→7.78 ms**, p95
**20.80→9.13 ms**. Profiling inflates CPU time. Its unprofiled whole-loop proxy
**11.34→8.03 ms** includes render/swap/waits and is not pure CPU submission.

Capture isolation: six actual 720p GPU frames, finish before read, median
copy/readback ~1.76 ms, submit ~0.034 ms; worker completion ~150.5 ms.
Statistics match the old population statistics exactly. Ordinary playback does
not wait after each capture. The original 171 ms synchronous block is historical
baseline; readback can still stall and normal close waits for accepted work.

At 2560×1440 output, Full/75%/50% internal sizes were actually
2560×1440 / 1920×1080 / 1280×720. GPU medians (including upscale) respectively:
Dyes **64.80/36.78/16.33**, Waterfall **66.66/37.82/16.78**, Citadel
**90.97/51.31/22.83**, Marsh **149.52/80.94/35.39**, Tidal
**39.85/22.44/10.03 ms**. These are different pixel workloads and appearance
tradeoffs, not equivalent speedups or guaranteed 60 FPS tiers.

## Preservation and visible evidence

The matched 635-frame matrix covers Main30, four held input levels, neutral and
edited target gains (0/.73/1.4/2), Planet edits, seven pairs × four transition
recipes × entry/overlap/return samples, ordinary Main and resize-return.
**430 frames are pixel-exact**. Most other differences are at most one 8-bit
step; larger Marsh differences remain. Worst matrix frame: Marsh return after
32→29 Fold, mean 1.53/255, maximum 69, 8.80% pixels differ by more than one.
All common GPU uniforms checked at five differing frames were identical,
including clocks, palettes, gains and lamp/history inputs. Compiler arithmetic
amplification in lighting/fog is an inference, not proven instruction attribution.

A paired 61-frame Marsh sequence spans quiet/active/event/release over eight
seconds with identical inputs. Mean channel difference averaged .055/255;
worst frame mean .513/255, max 36. Sampled sequence inspection shows matching
rocks, fog, musical lighting and movement, with localized rock/lighting color
variation. APNGs and contact sheet are retained. This is synthetic silent GPU
sequence evidence, not continuous AV listening or user acceptance.

Visible, real-time decoded Studio-caller runs used Warbot Jazz.wav
SHA-256 `90bf34009383c524b0ad100a4665d2ce470007136d49b2bfed96a8560114512a`,
analysis from prefix zero, seed 7301, actual 1280×720 output, existing driver
presentation policy. All were silent. Window/motion was observed before the
user's Escape stopped desktop automation; it was not restarted.

| Run | Seconds / intervals | Mean / median / p95 / p99 ms | Max / >50 ms |
|---|---|---|---|
| Full Waterfall, captures off | 24 / 1417 | 16.90 / 16.7 / 20.5 / 23.3 | 209.0 / 2 |
| Full Waterfall, captures every 2 s | 24 / 1415 | 16.91 / 16.6 / 20.8 / 28.5 | 136.5 / 2 |
| Ordinary Main, Full, diagnostics on | 60 / 2536 | 23.64 / 21.1 / 48.7 / 63.7 | 282.6 / 114 |
| Ordinary Main, 75%, diagnostics off | 60 / 3310 | 18.07 / 17.1 / 30.0 / 37.0 | 135.8 / 2 |

Both Waterfall >50 ms events occur in the first .3 s. Enabled captures produced
12 PNGs with no drops/errors and no recurring 171 ms playback stall in this
passage. Main's ordinary route was 11→30→5, with a 1360×768 resize and 720p
return in the Full run; cleanup flags for stages, program/VAO, inbox and row
worker all passed. Main Full/75 arms differ in diagnostics and song-time sample
count, so this is not an isolated scale attribution. Neither establishes stable
60 FPS. Swap returns do not measure scanout.

Visible artifacts precede final uniform-handle caching, profile fast path,
Cavern preparation correction and Fractal pre-warp context initialization.
Their exact file differences are listed in the evidence index. Final hidden
source-bound checks verify those changes; visible measurements are retained as
the measured candidate evidence, not silently relabeled exact final-source FPS.
50% was GPU-tested but not observed in visible decoded playback. No multi-hour
rendered soak, natural music listening, other GPU/vendor, true fullscreen or
complete player/application suite was run.

## Executed checks and retained failures

PASS: new CPU resolver/ownership/encoding/backlog/drain/telemetry/profile/uniform
checks; existing scope, director, transition, availability, playback and session
checks (nine-script set); final focused CPU/decoded mocked graphics checks;
Planet model/stage/flow/view functions (432 exact legacy clock cases); full
Studio regression (real GPU routes, UI layout, pigments, session compatibility,
pacing, actual child restart/cleanup); final Fractal/Main GPU integration
(warp, pigments, Repeat pixels, Return state, resize); normal-time structural
Root→Tidal Iris/Fold scoped-frequency GPU checks. Syntax and whitespace checks
are recorded in the index. These evidence classes are distinct.

The complete Planet tuning script still fails its historical inverse-source SHA
guard. The pre-task shader bytes reproduce that same stale guard; focused
behavior checks pass. The separate copied-baseline full-script attempt lacked
historical evidence files and failed file lookup; it is not claimed as a full
baseline test. No identity guard was removed or rewritten.

Earlier experiments/failures are retained: removed audio-derived aliases caused
image differences and were corrected; fully parking Cavern preparation caused
660–926 ms entry rebuilds and was rejected; family splitting/background binaries,
subroutine/static route/loop variants did not improve bounded cold time/memory
sufficiently. Zero-inlining's warm cache retry moved cost to first use and was
rejected. Final policy is 100 with measured cold and bounded prewarm. An early
uniform wrapper iterated millions of handles and was replaced by a cached map.
Task-created experimental modules were archived before removal; existing files
were not deleted. The baseline matrix completed its artifacts then hit obsolete
Query.release cleanup; later harness cleanup was fixed. Studio test discoveries
were corrected for qualified symbols/current catalog anchors and Main30 leaf
count; structural monitoring assertions now use fresh snapshots, with audio
submission checks still every frame. Failed logs remain in the evidence inventory.

## Exact Studio review and next decision

1. Run `C:\ZeraWave\run_development_studio.bat`. In **Build & preview**, select
   held Waterfall, Liquid dyes, Ghostlight Marsh or Crystal Cavern from Library. Choose **Test
   track**, Warbot Jazz.wav (or the same available WAV for all comparisons),
   **Replay speed: Real time**, **Test duration: 60 seconds**, **Save frames and audio measurements: off**,
   **Preview quality: Full quality (100%)**, then **Start preview**.
2. Open **Audio Tuning** and **Palettes**; edit source gains/ranges and pigments.
   Observe quiet/active/release. Stop/restart to check restored session choices.
   Compare 75% and 50% using the same track prefix/seed/settings; these deliberately
   soften detail. Do not adopt a lower Main default as part of this review.
3. Choose **Main blend** for ordinary director behavior. Isolate transitions
   Waterfall↔Geometric corridor, Citadel↔Crystal Cavern and Root blossoms↔Tidal
   Strata; compare Optical crossfade, Branching Iris and Flowing Fold. Audition,
   Repeat and Return use the existing controls. Resize and return to 1280×720.
4. Optionally enable Captures explicitly for evidence. Review `captures.json`
   drops/errors and diagnostics as separate overhead. Robert owns acceptance of
   numerical Marsh variation and scaled appearance, then checkpoint approval.

Proposed updates sent to **Bob the Overseer**, for its shared-document ownership:
record this scoped fix as implemented/reviewable with the above final source and
patch; retain Main30's existing acceptance status; record captures-off and opt-in
quality controls; replace current-cost claims with measured cold/memory/water
results while preserving historical evidence; retain remaining 60 FPS/startup,
compiler/Marsh numerical and visible-final-source limits. No new phase/critic
was dispatched. Commit/push remain Robert's checkpoint decision.
