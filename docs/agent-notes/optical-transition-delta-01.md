# Optical crossfade correction — independent review delta

The reviewer found Optical crossfade and Planet Canvas pull supplied identical uniforms. Explicit `tr_fade` now uses negative transition style -1 and composites two complete endpoint images after each scene's shading. Planet pull, native family melds, legacy physical and regional transitions retain their equations and selection IDs. The existing fragment evaluator is called from a bounded two-iteration loop; held scenes, non-optical transitions and fade endpoints evaluate once. There are no new graphics resources, dependencies, renderer interfaces or shared planning changes. The four provisionally accepted scene refinements are frozen.

Only transition_catalog.py, dream.frag and transition_controls_test.py changed. Source/evidence baseline is work/review-corrections-01/source-manifest.json; final source and artifacts are bound in work/optical-transition-delta-01/source-manifest.json. The older pack remains bound to its original hashes; this delta supplements it.

## Checks and evidence

- transition_controls_test.py PASS: distinct fade/Planet/native uniforms, actual configured renderer route at midpoint, JSON save/reload and Studio v3 validation for all three recipes; existing v1-v3 migration and controls checks retained. Two changed Python files parsed; git diff --check exit0. Exact logs in focused-checks.json and controls-test.log.
- GPU640x360 RTX3070Laptop: matched pairs Membrane11→Planet5 and Magnetic32→Auroral34, each progress0/.25/.5/.75/1. Native outputs compared to the pre-delta shader; fade endpoints compared to the native single-source/target images. Optical interior checked against independent weighted endpoint images, allowing one channel unit for framebuffer quantization. Numerical results and exact hashes in gpu-evidence.json.
- Nine representative held scenes5/11/26/22/29/15/32/34/36 compared to pre-delta shader at65s using identical uniforms/resources. This focused check covers the entry-point change; the full scene suite was not rerun.
- Two4s15Hz silent side-by-side APNGs: left Optical crossfade, right legacy Planet pull or native Plasma meld, identical timestamps/present inputs. Full matched-progress PNGs also saved. These are controlled GPU sequences, not decoded replay, live loopback or continuous listening. Fine visual judgment remains the critic/user's.
- Builder inspected matched-progress images and ordered APNG frames12/30/48 for both pairs using compact indexed PNGs. Optical dissolves the intact planetary endpoint over the membrane while legacy pull contracts/wraps it; Plasma fade overlays complete endpoints while native meld preserves its territorial handoff. Continuous animation-player/AV inspection was not available.
- Initial GPU fixture failed because it retained the previous fade marker for a native raw draw. Renderer.render already resets both transition/layout uniforms each frame; the fixture was corrected. Its failure is retained in fixture-failure.json and gpu-evidence-fixture-marker-failure.json. New-source cold compile113.87s; subsequent cached compile.248s are separate conditions.

## Reviewer path

Open work/optical-transition-delta-01/planet-fade-vs-native-normal-time.apng and plasma-fade-vs-native-normal-time.apng; inspect corresponding progress PNGs. Launch .venv\Scripts\python.exe app\visuals\studio.py and Load review-session-fade-planet.json; compare review-session-legacy-planet.json. The analogous fade/native Plasma sessions exercise native-family distinction. Source IDs, pair settings, order, isolation and save schema remain stable.

Optical interiors intentionally shade both scene endpoints, so cost depends on the pair and can exceed a native meld. No FPS claim. This is a narrow functional correction; no new art iterations, broad recapture, staging, commit, push or user acceptance. Independent review is the remaining gate.

640x360 raw GPU draw, four warmups/12samples, frozen midpoint uniforms on the reported RTX3070Laptop: planet-tr_fade 3.858ms median; planet-tr_planet 2.222ms median; plasma-tr_fade 4.644ms median; plasma-tr_plasma 3.101ms median. Excludes mapping/readback/swap; no whole-loop or frame-rate claim.
