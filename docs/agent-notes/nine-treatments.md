# Nine visual treatments — implementation ledger

> Dated task evidence. Scope limits and pending-review statements below belong to
> the recorded assignment. They are not restrictions or current priorities for
> later work; use [ROADMAP.md](../../ROADMAP.md) and the latest user direction.

Scope: three materials, three spatial effects, three final-image Envelopers; existing Studio, live colors, saved sessions, palette cycling and explicitly authorized Main authored/default integration. Implementation and the earlier color-inspector rollout were committed/pushed as `aebea87` before this resume. This resume makes only the minimum-window Studio layout fix and documentation updates; no new commit, push, build or dependency.

Current default correction (2026-09-30): the user subsequently requested Prism
Assembly, Digital Bloom and Chromatic Memory off in Main. Their original
integration and validation below remain evidence, not current artistic approval.

## Lineup

- Ink Archipelago: flowing pigment islands with narrow veins and dark channels.
- Interference Silk: crossing wave bands and contour interference, not metallic objects.
- Cellular Mosaic: drifting cell interiors, seams and internal growth.
- Elastic Lenses: bounded local magnification/compression pockets.
- Braided Flow: crossing coordinate shear lanes.
- Nested Windows: local nested coordinate windows, not a centered tunnel.
- Prism Assembly: image facets displace and reconstruct the composed scene.
- Digital Bloom: localized block/scan/ordered-color quantization.
- Chromatic Memory: bounded whole-image temporal reconstruction, separate from Echo.

## Research (observed locally; no copied code or assets)

- C:/MilkDrop 3.37/Milkdrop3/presets/altunenes - MilkDrop2077 - Tri-Bloom RGB.milk: warp stage samples the previous frame and decays it; composite stage samples the resulting image. The name alone did not establish a reusable bloom algorithm.
- C:/MilkDrop 3.37/Milkdrop3/presets/MilkDrop2077 - Pink lines.milk: composite stage mirrors source coordinates, samples blurred/current imagery and reshapes colors. Inspiration: recognizable source-image transformation rather than unrelated overlay.
- C:/ProjectM Library/src/libprojectM/MilkdropPreset/MilkdropPreset.cpp: distinct previous/current framebuffer ownership and final composition.
- C:/ProjectM Library/src/libprojectM/MilkdropPreset/FinalComposite.cpp: composite shader with a pass-through fallback. Inspiration: isolated final-image processing with fallback.
- C:/ProjectM Frontend/src/FPSLimiter.cpp: wall-clock frame timing includes pacing; GPU shader time alone is not end-to-end FPS.
- MilkDrop LICENSE.txt restricts commercial use; projectM LICENSE.txt is LGPL 2.1. No implementation or asset is imported; all new expressions are original. No claim is made about per-preset license compatibility.

## Design and preservation

Append IDs; retain legacy mask bits. Existing explicit lists never gain items. Held authored scenes stay untouched. Main default and explicit Authored will use the expanded paced show, as requested; custom lists stay explicit. Spatial effects alter existing supported material/detail coordinates, not world depth. Spatial colors inherit the material.

Envelopers: one renderer-owned final stage, at most 1920x1080 proportional targets, scene RGBA8 plus two alternating RGBA8 history/output targets (10.55 MiB at 720p, 23.73 MiB at 1080p). No read/write alias. Disabled path bypasses allocation. Reset on startup, resize, backward seek, >0.5 s gap, held-state change and disable/re-enable; release on shutdown. Main transitions intentionally retain a short <=0.18 s image trail, never Echo history. Allocation failure falls back to the unprocessed scene with a reported warning. This intentionally processes resolved image depth, not world geometry.

## Implemented behavior

All nine treatments are present in `preview_layers.py`, `dream.frag`, and the bounded final-image `envelopers.py`/`envelopers.frag` stage. `studio.py` exposes nine Planet Canvas review presets plus **Main — authored seven-material show**. Materials can be isolated; spatial and Enveloper rows can be enabled, soloed, ordered, and given a saved amount from 0 to 1. Six colored material/Enveloper targets expose authored families and reusable per-target Hold/Cycle timing through the live inspector. A manual color edit pauses the target's cycle. Existing session/preset validation, IDs and older custom lists remain in use. New spatial effects inherit material pigment and have no separate color target.

Main default and Main explicit Authored both meld seven materials at 22-second holds. Each 72-second passage offers one spatial treatment during seconds 8–28 and one Enveloper during seconds 38–62, with six-second fades and untreated gaps. Three passages cover each set; the world director remains musical. Existing explicit custom lists do not silently gain these treatments. Held Authored forms remain their own authored presentations.

## Verification completed

All paths below are from the existing virtual environment. Original implementation evidence is under `C:\ZeraWave\work\nine-treatments-20260928-223811`; resumed evidence is under `C:\ZeraWave\work\nine-treatments-resume-20260929-213951`. No evidence was overwritten on resume.

- `materials/checks.json`, `spatial/checks.json`, `envelopers/checks.json`: real GPU synthetic captures at 640×360 for quiet/strong/release, individual effects, authored reset, changed source pixels, and exact disabled comparison across 36 held states. Enveloper startup/seek/gap/disable checks passed. These are deterministic captures, not listening review.
- `studio-nine.log`: `treatments_test.py --studio` passed all nine review presets and 27 actual GPU launch routes (synthetic, decoded test track and controlled-sample live entry for each treatment). Color target families/cycling, manual precedence, session/preset round trips, older sessions, gradient ranges, amount persistence and Main scheduling passed. Controlled samples do not establish natural live audio quality.
- `extended-paired.log` and `extended-paired/extended.json`: `treatments_test.py --extended` passed at 1280×720. Six rounds of enabling, color edits and resize kept three bounded targets, retained history on color edits, and released targets when disabled. Cap/upscale, backward seek/gap (from initial checks), forced fallback/recovery, Main transition and shutdown passed. At identical endpoint time and input, Prism Assembly and Digital Bloom matched exactly at 30/60/120 updates/s; Chromatic Memory differed from 120 Hz by 0.65 and 0.47 mean 8-bit channel values at 30 and 60 Hz. This is sampling sensitivity, not a tested flicker report.
- `studio-final.log` completed the main Studio checks and palette route but failed `studio_comparison_test()` because the new amount row hid a bottom button at the supported 680×800 size. This was a real layout defect. A two-line compact-layout fix in `studio.py` reduced table height and button spacing. `studio-comparison-resume.log` then passed the focused minimum-size, A/B, cancellation, session and decoded replay comparison check. The complete `studio_test.py` suite then passed after this fix (`studio-full.log`): palette route, comparison children, live color transport, sessions, legacy handling, layout and GPU clocks.
- `main-replay.log`, `main-replay/replay-performance.json`, `main-replay/metrics.csv` and `main-replay/captures/`: `treatments_test.py --replay` passed 216.02 seconds of the decoded Warbot Jazz WAV at 1280×720 using real analysis, Main director, GPU render, swap/events and 18 captures. 5,063 analysis frames covered all seven material indices, all three spatial effects and all three Envelopers across eight director states. No Enveloper fallback was observed. Captures at 48, 120 and 192 song seconds were visually inspected; brightness/contrast statistics were finite. This replay was accelerated and silent.

### Reproduction commands and evidence

Run from `C:\ZeraWave` with the existing `.venv`; output folders are evidence paths and should be changed to new names on rerun:

```powershell
.venv\Scripts\python.exe -X utf8 app/visuals/treatments_test.py work/nine-treatments-20260928-223811/baseline/shaders/dream.frag work/nine-treatments-20260928-223811/studio-nine --studio
.venv\Scripts\python.exe -X utf8 app/visuals/treatments_test.py work/nine-treatments-20260928-223811/baseline/shaders/dream.frag work/nine-treatments-20260928-223811/extended-paired --extended
.venv\Scripts\python.exe -X utf8 app/visuals/treatments_test.py work/nine-treatments-20260928-223811/baseline/shaders/dream.frag work/nine-treatments-resume-20260929-213951/main-replay --replay
.venv\Scripts\python.exe -X utf8 app/visuals/studio_test.py
```

The synthetic materials/spatial/Enveloper capture batches use the same `treatments_test.py` command without a mode flag, with its baseline shader and distinct output folders. Relevant logs in the original evidence root are `materials.log`, `spatial.log`, `envelopers.log`, `studio-nine.log`, `extended-paired.log`; the resumed root contains `main-replay.log`, `studio-comparison-resume.log`, and `studio-full.log`. All completed checks above passed except the documented pre-fix `studio-final.log` layout failure, which has been fixed and rerun. `git diff --check` passed after the resume edits.

### Measured cost and scope

`extended-paired/extended.json` used 70 warmed paired samples per treatment on an NVIDIA GeForce RTX 3070 Laptop GPU at 1280×720, Planet Canvas with stars/rings/moons and fixed synthetic input. Each candidate was measured close in time to an untreated draw with the same source details. Untreated median was 3.70 ms GPU and 6.04 ms wall-clock draw/swap/events. Added median GPU time was approximately +0.16 ms Ink, +0.16 ms Silk, +0.25 ms Mosaic; +0.014 ms Lenses, +0.009 ms Braided, +0.020 ms Windows. The three Enveloper paired differences were −0.031, +0.019 and +0.012 ms; that near-zero spread is measurement noise, not a claim that final-image processing is free. Their full draw/swap/events medians were 6.30, 6.37 and 6.46 ms versus the separate 6.04 ms untreated median. Full composed GPU medians were about 3.70 ms for each Enveloper. The earlier sequential cost table is retained as raw evidence but is too noisy for added-cost claims.

The representative Main replay processed 5,063 analyzed frames in 65.53 wall seconds (77.3 processed frames per wall second), with 7.63 ms median and 15.94 ms 95th-percentile GPU render query. This accelerated, uncapped decoded run includes world changes, analysis, swap/events and periodic readback. It is not a real display FPS, a performance guarantee or continuous audiovisual listening. The bounded stage uses three RGBA8 targets (about 10.55 MiB at 720p, 23.73 MiB at its 1080p cap); no read/write alias.

## Remaining review and handoff

The user briefly viewed the committed result and said it works and looks okay, with tuning expected. Structured review of all nine in motion, natural live-music listening, and artistic acceptance remain open. One Main capture at 60 seconds has large bright blue water highlights (14% of pixels with a channel at least 250); inspection shows a blue water scene, not a broad white flash. Treat its contrast as an artistic review point, not a confirmed treatment defect. A color cycle's swatches display the held setup rather than its current interpolated color. Changing effect lists, amount, material isolation, or the Planet Authored/Soft Dream selector requires a new preview; declared color edits and Hold/Cycle timing can reach a running preview.

Resume at the user's structured Dev Studio review via **Presets > Nine treatments** in the order of the three materials, three spatial effects, three Envelopers, then **Main — authored seven-material show**. Tune only the treatments the user identifies. Main integration is already present by the user's explicit authorization; do not treat the earlier Planet prototype's gate as a reason to remove it. The proposed later checkpoint scope is the small Studio layout repair and this ledger/`DEVELOPMENT_STUDIO.md` update only, after user review; no commit is authorized now.

## Later artistic decision — 2026-09-30

The user found all three Envelopers visually unsatisfying and asked to turn them off for now. Main's default and explicit Authored show no longer schedules them. The nine individual Studio review presets and explicit custom lists retain them for later tuning. The 216-second replay and performance figures above describe the earlier implementation, not the current Main default. A focused schedule check and GPU render confirmed Main leaves the Enveloper stage inactive while an explicitly selected Digital Bloom still renders. The broad Studio route check was started but stopped after the focused verification because it was much slower than warranted for this change; it is not reported as a pass for this revision.
