# Main director and global transitions integration

Status: implementation/evidence ready for the parent's independent >=7.5 integration gate. No score assigned by the builder; no Robert artistic acceptance, commit, push or release. HEAD stays `312287e66ece8c0296037d2bfffcc4ac9e3b5609`. This is a task handoff, not a replacement roadmap. All seven scoped scene passes precede this phase; their scores/acceptance remain the parent's records.

## Visible result and reusable hooks

Main usually exchanges spatial regions while both scenes continue their own musical motion. Three recipes are registered as building blocks in the existing Library:

- **River Carry**: a connected bent traveling boundary, with small directional/perpendicular image displacement. `main_region` and `main_carry` in `dream.frag`.
- **Facet Relay**: staggered coarse regions exchange ownership, carrying small pieces of the outgoing image. Intended to fit architecture, branches and crystalline composition; it is image-space faceting, not mesh disassembly.
- **Depth Aperture**: an off-center elliptical arrival region, with a small inward pull. Incoming dark backgrounds can make this read as a dark iris; the incoming form is visible inside. It adds no black shutter, RGB wash or overlay pigment.

The narrow soft boundary permits local overlap. Geometry is not morphed between world topologies. Existing related callbacks/dissolves remain occasional choices (22% for related pairs, 7% otherwise); their warp/bend behavior is preserved. The recorded unrelated dissolve label says “quiet optical dissolve,” but selection of that style is probabilistic, not a separate quiet-input classifier. These automatic Main recipes are spatial-only and inherit both worlds' existing editable pigments, so they need no new color target or player UI.

Shader helpers `main_weights` / `main_add_state` produce per-fragment ownership through the existing family/form weight interface; `u_main_transition` and `u_main_layout` describe style, progress, source, destination and bounded layout. Scene helper text is unchanged. Layout stays fixed throughout a handoff; masks are monotone in progress and endpoint displacement settles to zero. Main holds retain the original shader appearance.

## Director

`main_director.py` supplies authored energy/family/composition/pigment metadata and independently testable scoring/recipes. `Renderer.choose_world` combines musical suitability, soft recency, coverage, recent unordered-pair penalties, family/composition/palette contrast, related-grammar affinity and bounded shuffled priority. All other 25 eligible forms retain positive weight, even recently visited or at energy extremes. The immediate current form is excluded to make an actual handoff. This avoids a fixed playlist or a hard cooldown that can empty the pool; it does not promise uniform coverage in every hour.

Normal launches retain OS-entropy seeds and fresh shuffled priorities. Explicit replay seeds reproduce decisions. Existing lift/release/hit/breathing opportunities, 12–19s minimum holds, 32–48s maximum holds, 6–9s transitions (release 8–11s) and <=0.8s beat wait remain. Manual held/debug selections are protected. Choice history stores selected score factors, top four alternatives, musical trigger and transition rationale. Palette distance uses representative authored pigments or valid manual edits of named roles; it is not a rendered histogram and does not track every automatic palette-cycle color. No genre/phrase classifier or queue launcher was added.

Memory is bounded: 64 detailed choices, 12 recent pairs, 12 styles, 26 last-seen states and 26 priorities. No new texture, framebuffer, shader pass or dependency. Existing cached scene resources/lifecycle remain. Galaxy 36 and Water Basin 37 stay outside Main; Envelopers remain off.

## Source-bound checks and inspection

The authoritative pack is `work/main-integration-01/source-manifest.json`; frozen sources are in `final-source/`. Baseline snapshots and exact integration diffs separate this phase from unrelated dirty work. `source-preservation.json` confirms nine accepted scene module/private-shader hashes, Studio, color/preview systems and Molten's Main-presence regression unchanged. Of 26 existing Renderer functions/methods, only constructor, choose_world, update_blend and render changed; all preexisting GLSL helper bodies except main() are exact.

- `main_director_test.py`: two identical seeded four-hour 1Hz simulations, 380 choices, all 26 forms and four styles observed. Histories stayed bounded; 64 normal constructors had distinct seeds and varied openers. Positive eligibility, recent-pair discouragement, finite values, three-aspect monotone mask/endpoints, manual overrides, v1–v3 sessions and normal Studio without forced seed passed. Numeric simulation is not a rendered soak.
- Existing `molten_response_test.py`, `marsh_response_test.py`, `arc_constellation_test.py` passed, including the authoritative Fire-slot Main-presence guard and invalid-surface event polling. `git diff --check` passed; existing CRLF warnings are retained.
- Nine controlled 3s transitions cover every upgraded scene and all eligible Main families, with 31 frames at 10Hz and a local synthetic hit at 1.4s. Eighteen same-context GPU endpoints and 20 held comparisons were **exact**, zero changed channels, at640x360. Original baseline shader/current shader use identical time/uniforms/resources. Selected held time is74s. No tolerance relabeling.
- Natural director capture: actual shared decoded Warbot Jazz45–105s input, seed8291; **901 frames**, nominal15Hz. Rendering ran **60.0028s**, encode-inclusive wall68.9879s. Audio was not played. Decisions were Sea opening, Fire at14.819s (existing dissolve), Arcs at35.213s (Facet), Windstreams at58.424s (Aperture, in progress at clip end). Full feature/choice trace is in evidence.json. This demonstrates unforced selection on present decoded inputs, not live loopback or AV listening.
- Inspected the nine representative ordered sheets, corrected natural sheet and adjacent10Hz APNG-derived frames for all three new recipes. Facet's stepped regions, aperture's advancing ellipse and River's carried hem were visible while underlying motion continued. APNG files are supplied for playback; builder inspection used supported ordered images, not an animation player or continuous listening.
- Named owned-window350ms responsiveness: **427/427** original final-source run and **325/325** corrected natural run passed. Original program compile95.361s, create95.423s, first native present95.445s; first probe97.118s, so this is **not an immediate-ready probe**. Startup cost remains substantial.
- Actual regional live Citadel pigment edit changed39,095 channels; clocks/cache/history/events and descriptor retained, same-frame reset exact. Held Marsh edit changed680,476 channels with events/phase retained. Five injected invalid sizes retained history and polled once each. Fifteen actual minimized samples had0x0 framebuffer; restore and three styles/aspects passed, with cleanup confirmed.
- Actual warm Studio Main: start1.943s, restart1.850s; live color/reset transport, resize, minimize/restore and close passed. Close exit0; existing Stop exit1 with zero owned render windows. Loading Cancel on a unique comment-key source passed14 progress-window probes, wall4.236s/exit125, cancellation exit0.151s. A comment key is not proof of a driver-cache eviction.

Initial development/fixture failures are retained: missing parenthesis before GPU work, wrong Studio helper import before capture, static verifier including preceding whitespace, first replacement fixture missing reused helpers. The first natural fixture read after swap, giving a blank first frame and stale subsequent readback; its clip/sheets/report/probes are archived in `initial-natural-readback-after-swap/`. Only that natural clip was replaced with final-source-matched read-before-swap capture; correctly captured controlled pairs, endpoints and held checks were reused. No source change after the GPU evidence.

## Measured cost

`paired-costs.json`: RTX3070 Laptop, uncapped1280x720, pre-integration render/shader versus final code in one context, alternating order, six warmups plus30 retained samples each. Mapping/all scene passes/draw/swap/poll/finish included; readback excluded. GPU/whole-loop medians in milliseconds:

| Case | Before GPU / loop | After GPU / loop |
|---|---:|---:|
| Held Cavern |21.06 /25.04|22.00 /26.14|
| Held Marsh |11.39 /15.73|12.04 /16.33|
| Cavern→Citadel |28.65 /34.88|22.31 /28.59|
| Magnetic→Marsh |11.82 /18.65|9.68 /16.40|
| Arcs→Auroral |3.69 /9.98|4.89 /11.15|
| Molten→Sea |6.27 /10.00|6.32 /10.89|

Heavy region transitions save work; held cases cost roughly4–6% more and cached plasma overlap costs about1.20ms more GPU. These are measured tradeoffs, not a general speedup or FPS guarantee; p95/submission/swap/poll values are retained. Dedicated performance/LOD work remains deferred.

## Review path and carried limits

Run the existing Dev Studio, load `work/main-integration-01/review-session.json`, then Start: Main, Test track, Real time, full track, captures off. The session has selection[] and layer overrides{}, so normal launch remains fresh/unseeded. For short source-bound review first inspect `representative-transitions-sheet-labeled.png`, then the nine matching APNGs and `natural-main-normal-time.apng`. `evidence.json` includes exact source hashes, decoded-input trace, transition descriptors and comparison deltas. These are separate from the session's normal launch randomness.

Historical exceptions remain open: original Marsh strict comparisons had Nebula two changed channels and Pressure one with **unknown original magnitudes**; a different-condition supplemental1-LSB result and this phase's exact20 checks do not resolve those original failures. Earlier Cavern immediate post-cold-ready responsiveness miss, Arc7.62s restart failure and earlier two cold capture responsiveness misses remain unresolved. Later warm/named-window successes do not erase them. There is no multi-hour rendered variety, live-music/loopback capture, continuous AV listening or user acceptance claim. The parent's integration gate and then one integrated Robert review are the next boundary; no further scene or UI work was started.
