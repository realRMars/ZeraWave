# Main blend upgrade audit - 2026-10-01

Read-only source audit at HEAD 312287e66ece8c0296037d2bfffcc4ac9e3b5609. No application code, shared plan, gates, devices or processes changed. Parked Water and other dirty files are authoritative and preserved. This is an implementation proposal for Overseer coordination, not a second roadmap. Stop at this audit handoff.

## Canonical scope

| Requested name | Existing Studio / CLI key | State | Existing color targets |
| --- | --- | --- | --- |
| Crystal Caverns | Crystal Cavern / cavern | 26 | cavern.land, earth.minerals, earth.sky |
| Sky Citadel | Sky Citadel / citadel | 22 | air.citadel, air.sky |
| Plasma | Magnetic Bloom / magnetic | 32 | magnetic.field, plasma.sky |
| Plasma | Arc Constellation / arcs | 33 | arcs.charge, plasma.sky |
| Aural Veil | Auroral Veil / auroral | 34 | auroral.curtains, plasma.sky |
| All Plasma branch | plasma | 35 | branch cycle of 32-34, not a fourth world |
| Ghostlight March | Ghostlight Marsh / marsh | 29 | marsh.solids, marsh.ghostlights, fog.vapor/internal |
| Molten Flow | Molten flow / molten | 15 | molten.flow, fire.details |

Stable IDs stay unchanged. Main candidate pool is Renderer.LIVE_FORMS: 26 individual forms; Galaxy36 and Cymatics37 absent. Envelopers remain excluded from default Main profile.

## Source observations and evidence limits

Renderer.choose_world (230) uses energy fit, absence weighting, 38s exclusion, corridor/planet anchor boosts and 1.65 physical-handoff affinity, then RNG. History is bounded64; last-seen tracks entries and departures. There is no explicit family, geometry, luminance, palette or previous-pair contrast score. Opening is random; holds vary12-19s minimum/32-48s maximum; transitions6-9s or release8-11s. Fast/slow energy uses .7/8s smoothing; only justified opportunities await a beat, with .8s deadline. No genre/phrase classifier.

handoff_kind (78) offers four related styles: molten/water, weather/plasma, earth/fog, citadel/magnetic. dream.frag handoff_front (4570) is a moving regional reveal, not true object morphing. Other pairs use warp plus coverage blending. At overlap both complete worlds can execute; Earth geometry is computed before final regional gating. Shared canvas/material work still precedes opaque scene replacement. These are potential savings requiring GPU measurement, not measured attribution.

VisualParameters retains scale/movement/sparkle/impact/flux and beat signals. AudioFrame has separate band onsets, but legacy mapper collapses onset identity into maximum impact. Renderer's positive eased flow clock is available; several target worlds primarily animate using wall/flow clocks and instantaneous brightness/width modulation. Reuse existing analysis; preserve legacy arithmetic and defaults. Parked12-band Water work is not a prerequisite.

Cost candidates from current source: Cavern up to128 distance steps, four bounded neighboring cells with up to3 crystals each, six normal queries plus3 AO queries; retain conservative distance correctness. Citadel already has ray-box rejection, then144 trace steps,7-tower map queries, beams with24-step visibility checks and bounded fireworks. Marsh combines56 solid steps with48 volume steps, two density calls/sample and6 lamp contributions/sample. Magnetic evaluates8x40 segments/pixel; Arcs7x18 plus branches. Auroral56 emission samples has no transmission early-exit. Molten is comparatively bounded noise/channel work plus16 embers; do not assume it needs a rewrite. Plasma sky additionally evaluates2x9 candidate cells.

Historical evidence only: Cavern about23.75ms/frame720p in older handoff; older Main replay7.63ms median/15.94ms p95 GPU; treatment additions about+.16/.16/.25ms for Ink/Silk/Mosaic in Planet Canvas. None establishes present scene costs. Latest actual scoped Galaxy startup compiled74.46s on new projected source, warm launch2.13s. Driver first-use cost remains. No new tests, benchmarks, frames or AV were run for this audit; no present artistic scores assigned.

## Prioritized implementation sequence

1. Crystal Cavern complete first: measure held26 and26-to29/28 midpoint only; optimize formation reuse/bounds without missed surfaces. Original coarse living facets on selected crystal clusters, restrained spring-like disturbance/settling, traveling mineral response and contrasting local pigment groups. Preserve readable travel/solid depth. Suggested families: Fluorite Lantern, Copper Quartz, Glacial Amethyst; role-matched authored values and manual override contract.
2. Sky Citadel: carry successful bounded facet/settling helper into selected masonry or floating shards, independent window/beacon musical roles, source-triggered celebrations and quiet recovery. Keep castle/island perspective. Reuse measured culling; do not add another tower trace to every pixel.
3. Plasma in order Magnetic, Arcs, Auroral: shared bounded charge event state, distinct core/loop, node-discharge and curtain-wave languages. Move stable path construction out of per-pixel repeated work where profiling supports; conservative bounds and ribbon geometry are alternatives, not blanket sample reduction. Inspect each independently and branch cycle. Families use dark grounds with separate hot/cool charge pigments, no synchronized full-screen wash.
4. Ghostlight Marsh: source-driven light behavior with individual memory, vapor/local shadow response, grounded trails and contrast between ground, moss and lights. Optimize local lamp lookup and volume gating after measurement; avoid overlaying comets on solid scenery.
5. Molten Flow: coherent current/pressure and cooling history, musical vent events, locally varied incandescent seams versus cooled banks. Reuse event/settling and palette roles; retain branching river topology and horizon.
6. Complete director and cross-world transition rollout using the proven first scenes, then one compact integrated Main review across all seven upgraded forms. No user wait between implementation scenes after parent authorizes sequence; one final user review after batch. Galaxy inclusion still separate.

## Scoped shared foundations genuinely needed

- Existing renderer owns one bounded visual-response/event state helper: positive integrated musical phase, attack/release, up to8 events and persistent decay. Additive band-onset routing only if a scene needs distinct transient sources; legacy mapper values unchanged. No new detector/audio backend.
- Small director scene-trait table and pure candidate scoring: energy/sustained-transient compatibility, family/composition/palette contrast, recency/last-pair penalty and coverage debt. Deterministic best suitable choice; seeded tie break only. Record choice reason/scores in bounded existing history. Preserve holds, beat deadline and one active handoff. Empty candidate fallback must be defined. Future classifier input is optional neutral metadata, not invented recognition.
- Extend existing handoff uniform/helper with universal finite regional styles (flowing reveal, coarse facet gather/reassembly, depth aperture), reversible direction and exact endpoint ownership. Start within existing draw; prohibit stacking unrelated warps and keep expensive world evaluation gated. A true common-topology geometry experiment is localized first, not a promise that unrelated worlds geometrically morph.
- Existing color_controls palette families, library and inspector: explicit target-role palettes and opt-in evolution, manual hold/reset/session behavior. Reuse named material families where appropriate instead of assigning every scene the same hue drift.

Reuse Galaxy's onset-front/energy-loss ideas, positive phase, localized pigment relationships, restrained star hierarchy and seeded stable traits. Only Ion Comets/Parallax Shoal are already registered cross-world layers (Cosmic/Fog/Plasma); their scene fit must be inspected. Gravity well/solar materials are Galaxy-dependent helpers, not drop-in universal effects. Existing Ink/Silk/Mosaic and Lenses/Braided/Windows are available but need intentional per-scene use. Keep all three Envelopers off.

## Compile/resource risk and acceptance

Avoid expanding nested static per-pixel loops or cloning helpers in the monolithic shader. Reuse functions; bound localized geometry/buffers in existing renderer and lazy-create only genuinely needed passes. Batch shader edits before compilation; keep responsive loading/Cancel and record actual compile time once per milestone. Existing driver caching is not an application guarantee; no unsupported binary-cache API, cache deletion, new shader permutations or architecture replacement. Separate shader programs only for a demonstrated small added pass with cleanup/resize contracts, not wholesale partitioning in this batch.

For each scene use fixed source hashes, same track segment and bounded silence/bass/sustain/onset/release sequence. Inspect normal-time motion, held view and short Main entry/return; choose only affected pair midpoints. Minimum honest review7.5/10 per scene, aspire higher; stills/synthetic state change do not verify listening. Preserve readable foreground, distinction between sustained/event responses, settling and extended interest. Validate live pigment edits/hold/reset and v1-v3 sessions, restart/resize/close/Stop.

Measure paired720p GPU median/p95 and render/swap/events CPU, resource allocation and cadence on RTX3070Laptop, same states/time/signals/profile, alternating order. Initial target: avoid >10% GPU regression without visible justified benefit; expensive affected holds/pair midpoints should improve, with16.7ms treated as60Hz total-frame budget rather than guaranteed shader allowance. Capture readback costs separately. Check actual cold/warm startup and persistent memory bounds. Existing shader_test held/color/family/choreography fixtures are reusable, but old broad pixel-preservation assertions must exclude deliberately redesigned targets and retain unaffected endpoints. No need rerun entire suite at each art tweak.

Prototype references are parent description-only evidence: mosaic and spring/Tutte videos not played here. Build original coarse topology; no repository asset/code import without verified license. Tutte static equilibrium assumptions do not establish crossing-free animated geometry.

Proposed Overseer update: supersede stale Galaxy status with pushed312287e/Robert acceptance; retain separate Main gate and parked Water status; record this authorized seven-form Main upgrade batch and first Cavern milestone within existing scene growth/transformation priority. No shared files edited.
