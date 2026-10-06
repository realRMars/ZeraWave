The strongest opportunities are **remaining Roots/Sky shared shading, Marsh attribution, and exact preparation of Main Arc33’s repeated geometry calculations**. ZeraWave already uses several rendering methods; a general compute, instancing, or renderer migration is not supported by the evidence.

Robert’s practical target—full-size playback mostly at or above 30 FPS, allowing brief small dips—remains incomplete. Nothing in this inventory establishes acceptance or authorizes implementation.

**Source and inspection identity**

I used preserved sources from `C:\ZeraWave`, without contacting or disturbing the Builder.

| Source version | Identity and relationship |
|---|---|
| Independently reviewed Root candidate, October 5 | Preserved dirty `baseline/` plus six `final-source/` files in [full-size-performance-20261005](work/full-size-performance-20261005/REPORT.md). All **282 bindings matched**. HEAD `4a4f6e03ad2119e790e88d8338bac9412a139881`; final manifest SHA-256 `fe09c7742ca6f3e5f5b3023de2d96abaef0f8659eb0b77f080eefdbdb9aa8b1c`. |
| Later completed Sky-guard candidate, October 5 | [Final manifest](work/roots-sky-performance-20261005/source-final.json), recorded at approximately **20:32 CDT**. Its baseline incorporates the reviewed Root candidate and documentation reconciliation. Application delta: four added lines in `dream.frag`. Same HEAD; **186 application bindings matched**, including a repeat check at 20:57 CDT. |
| Later candidate’s dirty-source identity | Application aggregate recorded as `2a520e4918e47f071484155a15fa98d08c57bb0fff81760617993c2e11cad345`; manifest SHA-256 `27942b1928b49ed7a38a73dcc1310286ace539206b4cbcbf819a46c7f45d1574`; patch SHA-256 `7412db6389de25fc0a3c067917646c92d324dba680339e58b93eb0c6914975ff`. |

The later composed snapshot contains 283 matching preserved files. Seven manifest entries lack snapshot copies: unrelated research/configuration/image files and the critique skill. **No application dependency is missing.** The renderer hash is `32c1f56fc17a9ddbb9fcadf0f816d2c2df94a8a75a840b8a67f1516b0560ab62`; later `dream.frag` is `afc7c6d64c2ac865e923c7305bca5b5c33526c576e283e7fb0bb317333f1178b`.

These are coherent historical source versions. I did not identify the currently running process’s loaded bytes or assume they equal either snapshot. Current runtime verification remains pending. Git could not enter `C:\ZeraWave` under this session’s permissions; recorded manifests supply HEAD and dirty-tree identity.

I explicitly loaded both requested project skills and read current ROADMAP, HANDOFF, technique references, and relevant maintenance contracts. No files were edited, workloads launched, tests run, workers dispatched, or publication actions taken.

**Actual rendering path and shared constraints**

The inspected production path is `Renderer.create` → Fractal integration → `AudioUniformContract` source transformation → Root preparation substitution → `PreparedProgram`. `Renderer.render` updates mappings, clocks and bounded histories, draws contributing preparation/surface passes, then draws the integrated fullscreen program.

Main optical fades evaluate **both complete endpoint images** for `0 < phase < 1`. Other transitions use the existing region/coordinate/coverage equations; Fractal pairs have an explicit endpoint evaluator. Solo timing therefore does not establish transition timing.

The following shared work applies to the inventory:

| Shared component | Actual work, reuse and constraints |
|---|---|
| **C: shared canvas/materials** | `dream.frag::scene_frame`, `spatial_carrier`, `selected_materials`, and material helpers. Per-pixel deformation, noise, folds, pigments and enabled effects provide material inputs to scene shading. Seven materials include bounded Echo history. A scene takeover does not prove this upstream work is dead. |
| Audio and clocks | Bass/scale, movement, flux, sparkle and impact; independently scoped endpoint gains/selected inputs; source, integrated flow, star and Planet clocks. Uniform-only audio resolves once per frame; spatially derived values retain local evaluation. |
| Root preparation | `RootBranchStage`: fixed **31×4 RGBA32F, 1,984 bytes**, texture unit 14. Refreshes at prepared draw boundaries, including direct uniform edits; holds normal and Planet clock variants. Per-pixel branch distance, taper, derivatives and shading remain. Renderer owns release; resize does not rebuild it. |
| Echo | `Renderer.update_echo`: two **512×512 RGBA16F** histories, fixed 60 Hz steps, bounded catch-up. Rewind/large discontinuity resets; selected history stays warm. Display colors do not rewrite history. |
| Cavern/Citadel surfaces | `SurfaceStage`: rasterized triangles into position RGBA32F, normal RGBA16F and depth targets, approximately **28 bytes/pixel/contributing surface**. Targets allocate lazily and release on resize/non-contribution. Main retains material/lighting work. |
| Colors/settings | Stable declarations and generated inspector, authored fallbacks, explicit overrides, Hold/Cycle and saved sessions. Color uploads are cached; changing color must preserve geometry, musical mapping and history. |
| Optional final Envelopers | Existing extra scene/history/composition passes; three bounded RGBA8 targets, maximum 1920×1080 internal pixels. Off by default in Main. Their cost is absent from the cited layer-free fixtures. |

These ownership paths are demonstrated by [renderer source](work/roots-sky-performance-20261005/baseline/app/visuals/renderer.py), [surface source](work/roots-sky-performance-20261005/baseline/app/visuals/scene_surfaces.py), and [Fractal integration](work/roots-sky-performance-20261005/baseline/app/visuals/fractals.py).

**Complete canonical Main inventory**

The roster comes from `LIVE_FORMS`, checked against `world_catalog` and transition declarations: **30 canonical Main forms**.

All non-Fractal rows use `scene_frame` and C unless stated otherwise. Functions below are in `dream.frag`; `fr_*` names are generated from `fractals.frag`.

Evidence labels: **H** = older performance-checkpoint GPU measurements; **F** = independently reviewed Root candidate; **G** = later Builder Sky-guard evidence. Their conditions follow the table. “Unmeasured” means no attributable dedicated timing established here for that form/source/phase.

| Stable ID / form | Representation and principal rendering work | Reuse, frequency and dependencies | Cost coverage |
|---|---|---|---|
| **11 / `membrane` — Membrane** | Procedural screen-space warped folds/ridges in `scene_frame`; no surface mesh. | Per-pixel FBM, sine folds and derivatives; shared Root calculation also occurs in the organic substitution block. Scoped tension/flux/high/impact inputs; editable blue/pearl gradients and ridge pigment. | Unmeasured dedicated current timing. |
| **12 / `roots` — Roots** | Prepared 31-branch data → `root_network` per-pixel segment distances and derivative antialiasing. | Frame preparation plus 31 segment tests/pixel; C and membrane-domain construction remain. Independent Planet clock variant, scoped flux and editable gradients. | F: steady ~15.9 ms intervals; G: ~15.8 ms. |
| **2 / `geometric` — Neon corridor** | `geometric_surface` bounded surface search/refinement → `isolated_geometric_scene`. | Up to 80 per-pixel search iterations through bowed, turning corridor equations; seeded bay width/height, live pressure and fine surface pigments. No resident corridor mesh. | H: 18.91 ms GPU at 720p; current Full unmeasured. |
| **5 / `canvas` — Planet Canvas** | Shared field becomes albedo; `isolated_cosmic_scene` uses analytic sphere depth, projected ring plane and opaque moons. | Per-pixel field/materials, terrain/cloud FBM, three moon/wake loops and depth comparisons. Planet-owned clocks, DSP/star adapters, scoped colors and optional histories. | H: 21.91 ms GPU at 720p; current Full unmeasured. |
| **7 / `sea` — Sea** | `water_surface` height-function intersection → `isolated_water_scene`; procedural reflected environment. | Storm first-hit bracket up to 40 samples, 14 refinements, four normal samples; exact weighted audio ingredients already resolved outside loops. No fluid simulation. | Unmeasured dedicated current timing. |
| **8 / `dyes` — Liquid dyes** | Same water intersection, pool view and advected procedural dye/material coordinates. | Height/refinement work plus per-pixel dye shading; shared clocks, weighted scoped inputs and editable dye/environment pigments. | H: 16.22 ms at 720p; 64.80 ms at Full 1440p. |
| **9 / `rain` — Rain & ripples** | Water intersection plus `water_ripples` and procedural foreground streaks. | Ripple neighborhood and seeded lifetimes/pixel; no particle buffer or persistent fluid state. Rain/ripple pigments and scoped response. | Unmeasured dedicated current timing. |
| **10 / `waterfall` — Waterfall** | `waterfall_surface` analytically intersects river/fall planes; `water_falls` shades them. | `scene_frame` also constructs the shared water surface when water is active. Per-pixel current/material/detail work; approach clock, fall/environment pigments. | H: 15.64 ms at 720p; 66.66 ms at Full 1440p. |
| **13 / `currents` — Currents** | Water height intersection and `currents_domain` procedural vortex/advection map. | Two vortex transforms/pixel plus shared intersection/reflection work; integrated flow and localized impact response. No accumulated fluid history. | Unmeasured dedicated current timing. |
| **14 / `fire` — Flame sheets** | `isolated_fire_scene`: three procedural screen-space flame layers and seeded embers. | Per-pixel FBM/tongue masks and 22 ember trajectories; present-input surge and constant phase clocks; sheet/detail pigments. | H: 18.82 ms at 720p; current Full unmeasured. |
| **15 / `molten` — Molten flow** | `isolated_molten_scene`: projected ground/channel, noise crust, derivative normals, backdrop and embers. | Per-pixel channel/FBM/memory fields and 32 embers. `MoltenMemory`: four deposits, 18-second cooling, pressure/shear/temperature and palette state. | F Spires→Molten arrival: ~22.5–22.7 ms intervals; no interchangeable G measurement. |
| **17 / `firescape` — Firescape** | `isolated_firescape_scene`: layered procedural landscape, tree/building silhouettes and flame masks. | Three layers, neighboring tree cells, branch/window construction and 64 ash/ember trajectories/pixel. Integrated travel and time-authored growth/burn; editable land/detail colors. | Unmeasured dedicated current timing. |
| **18 / `aftershock` — Aftershock** | `isolated_aftershock_scene`: projected ground, rings and depth-ordered procedural plume billboards. | Eight event slots; per-pixel depth sorting and nine lobes/active plume. Renderer owns blast births/retirement and eight shockwaves; editable land/plume/event pigments. | H: 28.55 ms at 720p; current Full unmeasured. |
| **19 / `windstreams` — Windstreams / Sky19** | `audio_owned_air_scene`: projected ground, ten cloud planes, streamers and 18 ordered balloon planes. | Per-pixel noise and five-fold balloon fabric; G guards provably zero cloud/shell coverage. Live clocks, scoped motion/impact and sky/cloud/balloon pigments. | F arrival ~33 ms intervals; G arrival ~25.7 ms. |
| **20 / `stormfront` — Stormfront** | Air scene plus corridor-derived cloud-vault intersection, weather/lightning shading. | Per-pixel corridor search and procedural weather/detail work. Existing afterglow/trail state, scoped energy and editable weather pigments. | Unmeasured dedicated current timing. |
| **21 / `vortex` — Vortex** | Air scene’s polar/logarithmic vortex field, procedural banks and discharge branches. | Per-pixel folds/bolts/trails; optional Daddy Long Legs and effect branches only when enabled. Persistent afterglow and scoped audio/colors. | Unmeasured dedicated current timing. |
| **22 / `citadel` — Sky Citadel** | Rasterized authored castle/island/rings → `air_citadel` surface lookup and lighting; procedural sky/planet/detail work. | Static cached mesh; per-vertex moving rings; full-size surface pass and per-pixel shading. `TowerCadence` events/clocks/colors. Raw/out-of-range path retains bounded analytic/distance tracing. | H: 22.85 ms at 720p; 90.97 ms Full 1440p. |
| **24 / `dunes` — Dune Sea** | `earth_surface` → `earth_map(form=0)` bounded distance search, including optional worm capsules. | Up to 128 steps/pixel, normal samples and terrain shading; worm has existing conservative bounds and ten segments. Integrated travel, sediment/mineral colors and scoped inputs. | Unmeasured dedicated current timing. |
| **25 / `strata` — Folded Strata** | Distance-field canyon/cliffs/arches via `earth_map(form=1)` and `earth_scene`. | Up to 128 search steps/pixel plus normal/material work. Live wall deformation and source pigments; no terrain mesh preparation. | Unmeasured dedicated current timing. |
| **26 / `cavern` — Crystal Cavern** | Production rasterized chamber/crystal rows → `earth_surface` lookups → material/lighting. Raw fallback mixes geology tracing with analytic convex-crystal clipping. | 24 GPU rows, two pending CPU rows, 64 cached row meshes; 192-cell descriptor texture, 24 KiB, changes on cell crossing. Mineral deformation/fronts/history, travel and colors. | H: 21.09 ms at 720p; current Full unmeasured. |
| **28 / `nebula` — Nebula Banks** | `fog_scene(form=0)` front-to-back procedural volume integration. | Up to 48 density/light samples/pixel; billow equations and early transmittance stop. No volume texture simulation; scoped energy and vapor/internal pigments. | Unmeasured dedicated current timing. |
| **29 / `marsh` — Ghostlight Marsh** | `fog_scene(form=1)`: solid distance tracing, analytic floor fallback, reflected ghostlights, then solid-terminated volume integration. | Up to 56 solid steps, six normal queries, 48 volume steps and six lamp-light contributions/step. Existing 14-lamp/672-byte frame cache; four events, palette and wakes remain musical/history dependencies. | Important repeated user report. H: 35.47 ms at 720p; **149.52 ms Full 1440p**. No F/G Marsh measurement. |
| **30 / `pressure` — Pressure Chamber** | `fog_scene(form=2)`: moving pressure-path/gyroid shell volume. | Up to 48 density/light samples/pixel, path equations and impact fronts. Scoped audio and vapor/internal colors; no persistent volume grid. | Unmeasured dedicated current timing. |
| **32 / `magnetic` — Magnetic Bloom** | Analytic opaque core sphere plus projected procedural filaments in `audio_owned_plasma_scene(form=0)`. | `OriginalLoopStage` prepares **42×8 RGBA32F** projected vertices/bounds each contributing frame; up to 8×40 segment tests/pixel remain. Core depth, clocks, audio and pigments preserved. | Unmeasured dedicated current timing. |
| **33 / `arcs` — Arc Constellation** | Analytic seven spheres plus projected jagged segments/forks in plasma scene form 1. Called “Spires” in F fixture reports. | Seven 18-segment paths plus forks constructed/tested per pixel. **Does not use Experimental39’s ArcStage/path cache.** Live depth, clocks, discharge/high response and colors. | F: steady ~32.6–33.0 ms; entry ~33.9–34.3 ms intervals. G did not retest it. |
| **34 / `auroral` — Auroral Veil** | Plasma scene form 2: 56-sample emitting/absorbing folded curtains. | Per-pixel density, transmission, threads and palette; analytic clocks and scoped audio. **Does not use Experimental40’s six-sheet pass.** | Unmeasured dedicated current timing. |
| **36 / `galaxy` — Galaxy Odyssey** | `isolated_galaxy_scene`: layered emitting/absorbing galaxy strata, analytic system bodies/rings, procedural surfaces and warp. | Seven strata, bounded body/event loops and 72 warp samples/pixel. Twelve-entry descriptor caches; 74-second route, visibility clock, star clock and eight nursery events. Editable structure/solar/comet colors. | H: 10.35 ms at 720p for its sampled state; full-route/Full cost unmeasured. |
| **41 / `fractal_landscape` — Tidal Strata** | `fr_landscape`: seven procedural layered ridgelines, FBM, derivative coverage and lamellae. | Per-pixel six-octave noise; bounded per-form travel/growth clocks, five terrain/three sky pigments and scoped treatments. | H: ~10.0 ms at 720p; 39.85 ms Full 1440p. |
| **42 / `fractal_atrium` — Recursive Atrium** | `fr_recursion`: distance tracing through five recursive frame scales. | Up to 72 trace steps, six normal evaluations and material FBM/pixel. Independent motion/treatment/pigment ownership. | Unmeasured dedicated current timing. |
| **43 / `fractal_bloom` — Honeycomb Garden** | `fr_growth`: procedural hex cells, petal masks, pollen and lamellae; no flower instances. | Per-pixel cell/noise/petal work; bounded growth epoch, stagger and pulse. Independent clocks, honey/petal pigments and scoped audio. | Unmeasured dedicated current timing. |

**Experimental and other implemented availability**

These remain separate from Main eligibility.

| ID / mode or form | Actual implementation and availability | Reuse/dependencies; measurement status |
|---|---|---|
| **37 / `cymatics` — Resonance basin** | Parked Cymatics/Water Studio workflow; analytic modal surface display in `cym_water`. | CPU `Basin` retains up to 36 complex modes with sample-held propagation, ≤2048-sample blocks and coefficient tables. GPU sums modes for height/slope/curvature across initial plus three relief refinements. PCM/sample clock, basin settings, camera and colors; unmeasured current performance. |
| **38 / `lodestone_experimental` — Lodestone Field** | Experimental plasma form 0 → `magnetic_cached_field`. | CPU `FieldPaths`: 12×49 projected paths, row/group bounds, fixed RGBA32F texture and four-event `FluxMemory`; per-pixel bounded segment work. Renderer owns texture; unmeasured current performance. |
| **39 / `stormglass_experimental` — Stormglass Network** | Experimental plasma form 1 → `ArcStage` offscreen pass → `u_arc_scene` sample. | Nine procedural facet billboards; 12×17 cached paths, 48 group bounds, four events; full-size RGBA16F target rebuilt on resize and retained until close. Unmeasured current performance. |
| **40 / `folded_aurora_experimental` — Folded Aurora** | Experimental plasma form 2 → Auroral `ArcStage` → sampled scene texture. | Six procedural emitting sheets, four event histories and evolving palette; full-size RGBA16F target. Unmeasured current performance. |
| **4 / `transition` — Legacy transition study** | Explicit Experimental catalog leaf; shared canvas/Planet assembly demonstration. | Existing procedural/analytic path and clocks; no independent new world. Unmeasured. |
| **3 / `cosmic` — Cosmic diagnostic** | Implemented direct diagnostic early return to isolated Cosmic composition. | Analytic planet/rings/moons; diagnostic orbit speed differs from Canvas. No canonical Main leaf; unmeasured. |
| **1 / `organic`** | Authored Membrane/Roots cycle. | Reuses 11/12 and shared preparation; unmeasured cycle/boundaries. |
| **6 / `water`** | Authored Water cycle. | Reuses 7–10/13; unmeasured complete cycle. |
| **16 / `fire_cycle`** | Authored Fire cycle. | Reuses 14/15/17/18 and histories; unmeasured complete cycle. |
| **23 / `air`** | Authored Air cycle. | Reuses 19–22; unmeasured complete cycle. |
| **27 / `earth`** | Authored Earth cycle. | Reuses 24–26, including Cavern preparation; unmeasured complete cycle. |
| **31 / `fog`** | Authored Fog cycle. | Reuses 28–30 and Marsh cache/history; unmeasured complete cycle. |
| **35 / `plasma`** | Authored original Plasma cycle. | Reuses 32–34; does not automatically select Experimental38–40. Unmeasured complete cycle. |
| **0 / `blend`** | Main director/composition mode. | Selects the canonical roster and transition recipes; measured only in identified fixtures. It is not a 31st worldform. |

**What the measurements establish**

All quoted GPU measurements used the RTX 3070 Laptop GPU. The principal recent/older checkpoint runs record NVIDIA 617.14. Thermal, power and background conditions were not locked.

- **H—older performance checkpoint:** hidden production `Renderer`, active tuning owner, seed7301, empty authored layer profiles, synthetic loud schedule, Full quality, swap interval 0, 15 warm + 40 measured frames/cell, synchronous GPU queries. Actual client/framebuffer/internal/viewport/shader dimensions were recorded. [720p results](work/performance-fixes-20261004/final-owner-loud-bound.json) and [Full 1440p results](work/performance-fixes-20261004/tier-full.json) bind their own source. Renderer SHA `e346ef840b976784c36bc9b6e046d2cbeb2edb0e89bc75fc643dbd555ecf8e8c`; raw shader SHA `90c93cd13e29b179fcae8b2ef1a072e261cf7f7cfd15bfc2696941446d830264`. These are GPU durations, not displayed FPS.
- **F—independent Root review:** Qt Shell → ControlClient → hidden Tk owner → production Renderer; actual **1944×986 throughout**, Full100%, real-time synthetic, seed7301, authored colors, no layers, captures off, forced endpoints and Normal BONK. Adopted window, swap interval1, 144 Hz monitor; neither native fullscreen nor Robert’s exact session.
- **G—later Sky guards:** same full pixel workload and production ownership chain, two reversed-order ordinary pairs plus separate synchronous query arms. Fixed-state attribution matched retained uniforms/history. This is completed **Builder evidence awaiting independent verification**, not an extension of F’s independent execution.

| Phase | F independent before → Root candidate, mean interval ms | G later guarded candidate, ordinary mean interval ms |
|---|---:|---:|
| Roots held | 32.36 → 15.94 | 15.80–15.88 |
| Entry | 74.67 → 40.93 | 34.77–35.35 |
| Optical overlap | 96.58 → 46.85 | **38.98–39.71** |
| Exit | 96.96 → 46.83 | 39.03–39.74 |
| Sky arrival | 66.32 → 32.78 | 25.66–25.81 |

G’s separate whole-pipeline GPU means were **15.53 / 36.79 / 38.59 / 38.62 / 25.38 ms** for those phases. Query waits were recorded separately; instrumented presentation intervals are not substituted for ordinary cadence. Ordinary phase samples ranged from roughly 24–380 frames over the specified held/transition windows.

The inherited **PARTIAL** verdict remains:

- Root gains are independently corroborated.
- Roots/Sky optical overlap remains expensive: F ~45–47 ms; G improves it to ~39 ms, approximately 25–26 swap returns/s.
- The strict observed maximum-tail comparison failed. G retains Roots maxima **47.65/47.74 ms**, versus baseline **16.47/17.13 ms**, and an entry maximum **115.96 ms**.
- Population tail behavior remains uncertain. Older delayed-query diagnostics moved long waits from swap into submission while GPU drawing stayed near normal cost; ownership/cause remains unresolved.
- Equivalent source/render-begin clock comparisons passed bounded correctness. The failed literal post-swap span threshold remains recorded; it does not establish source-clock drift.
- Saved-layout uncertainty persists: historical Qt `437a73…→938ed0…` change has unknown cause. G preserved its later `f7103b4a…` starting layout. Neither historical layout was restored.
- Physical changed-value controls, save/load, keyboard/DPI, continuous motion/listening, native fullscreen, all-world performance and multi-hour coverage remain limited or unverified.

F’s 43 sampled Full comparisons and G’s 17 plus two additional selected comparisons support bounded preservation. They do not establish universal motion equivalence.

**Marsh evidence deserves separate weight.** Robert’s repeated poor-performance reports are an important user-reported problem. H measured **31.00→35.47 ms at 720p** under the compiler-policy comparison and **149.52 ms at Full2560×1440**. Those measurements identify a historical problem, not its current internal owner.

Earlier October 1 [paired Marsh evidence](work/marsh-upgrade-01/paired-cost-and-cadence.json) used one borrowed context, alternating source arms, 30 retained samples/case and synthetic quiet/sustained/hit inputs. GPU medians were **8.25→9.02**, **8.58→9.01**, **9.38→10.08 ms**; Marsh/Cavern midpoint **20.34→21.19 ms**. Loop timers included mapping, draw, swap, poll and finish, excluding capture/readback. Its candidate shader/renderer hashes were `c13a9abf…` / `94dfb2d3…`. The 3.46 ms lamp kernel was a simplified proxy, not subtractable whole-scene savings. The lamp cache already exists and did not demonstrate an overall speedup.

H also retained Marsh numerical differences, including a worst matrix mean **1.53/255**, maximum **69**. Compiler arithmetic amplification remains inference. F/G neither measured Marsh nor resolved that preservation issue.

Coverage is consequently sparse: current full-size timing concentrates on Roots/Sky, with older F Spires/Molten fixtures; H supplies older dedicated timings for eleven held forms plus Tidal tier measurements. Preservation matrices and forced all-world runs do not fill missing dedicated cost attribution.

**Ranked opportunities—proposals only**

| Rank | Form/source and supporting evidence | Proposed mechanism, uncertainty and smallest falsifiable test |
|---|---|---|
| **1** | **Roots12/Sky19 shared shading:** `scene_frame`, organic/material block, endpoint evaluator. G knockouts indicate substantial shared work (~15 ms held Sky/~12.5 ms overlap); cloud/balloon guards are already implemented. Knockouts are non-additive and change the compiled binary. | Trace live output dependencies and remove only proven zero-contribution work, or prepare exact frame invariants. Do not assume the canvas or Root distance is dispensable. Test one held Root, held Sky and identical mid-fade state at Full1944×986, then a bounded normal-time passage. **Reject** if whole-pipeline gain is within repeat variation, preparation cancels savings, or pigment/audio/derivative/history output changes. |
| **2** | **Marsh29:** `audio_owned_fog_scene`, `fog_solid`, `fog_terrain`, lamp/volume lighting. Repeated user reports and H149.52 ms establish high impact; present ownership is missing. | First attribute solid traversal/normals, volume density and six-lamp scattering separately. If repeated marker construction dominates, investigate exact bounded cell descriptors with analytic fallback. Existing lamp preparation must be retained. Test current Full held quiet/active/event/release plus one transition, with ordinary and separately instrumented timing. **Reject** marker/cache work as the remedy if those regions contribute little or total cost fails to improve beyond variation. |
| **3** | **Arc33/Spires:** `plasma_node`, `plasma_view`, `plasma_segment`, form1 segment/fork loops. F steady/entry hover near the practical budget. Main33 lacks the prepared geometry used by other paths. | Prepare exact frame-dependent projected nodes, 18-segment endpoints and fork tips once per frame; preserve per-pixel distance/depth/light equations. Reuse the existing preparation pattern, not Experimental39’s different artwork. Test held33 and the same33→15 aperture states, total GPU including preparation, edited gains/colors and motion. **Reject** if precision/depth parity fails or total gain is negligible. |
| **4** | **Aftershock18:** event depth sorting and plume setup in `isolated_aftershock_scene`; H28.55 ms at720p, Full unattributed. | Move invariant event ordering and demonstrably frame-only plume descriptors out of per-pixel evaluation, retaining every plume/lobe and retirement envelope. Test empty versus densely populated event history, camera crossings and entry/return. **Reject** if sorting/setup is a minor cost, upload overhead offsets it, or ordering/retirement behavior changes. |

These begin with exact transformations. Floating-point order, derivatives, interpolation and endpoint scope still require preservation checks. Preparation adds bandwidth and bindings; bounded specialization adds compilation, startup, resident-memory, fallback and maintenance obligations. Shader extraction already couples Root preparation to authored function structure.

Approximate lookup fields, mesh substitutions or accelerated tracing would need separate silhouette, normal, softness, occlusion and deformation comparisons across quiet/active music, sustained holds and transitions. Stills cannot establish imperceptibility.

The inspected context requests GL3.3 and already supports the demonstrated floating-point fragment preparation. There is no demonstrated compute workload remedy here. Cavern/Citadel already rasterize geometry; their authored variation does not automatically make instancing beneficial. Repeated per-frame creation/upload has not been established as the current Roots/Sky bottleneck. An API upgrade, resident-resource campaign or split compositor is therefore premature. The saved research remains sufficient; no additional external survey was needed.

**Recommended next bounded investigation**

After Bob and Robert review this inventory, the most useful new investigation is **current-source Marsh attribution at the actual Full playback dimensions**, covering one held quiet/active/event/release sequence and one affected transition. Bind source, inputs, layers, clocks and caller first; separate sustained GPU cost from exceptional submission/presentation waits. Its purpose is to choose or reject one concrete mechanism—not start an optimization campaign.

For later narrow documentation reconciliation:

- Add verified per-form representation/availability anchors to TECHNIQUE_LIBRARY, especially **Main33 versus Experimental39**, **Main34 versus Experimental40**, and production Cavern/Citadel rasterization versus raw fallback.
- Reconcile HANDOFF’s independent Root PARTIAL record with the later Sky-guard Builder results, keeping verification and acceptance separate.
- Clarify Marsh’s existing cache, solid/volume call path and historical timing identities in the relevant maintenance guidance.
- Correct dated descriptions such as Molten’s older “sixteen embers” note against the inspected 32-ember implementation.
- Keep proposed priorities in ROADMAP; make no speculative method mandatory. Keep the Qt resource panel in its separate pending UI scope.

No reconciliation was performed. The findings stop here for Bob and Robert’s next decision.
