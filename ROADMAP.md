# ZeraWave development plan

Updated: 2026-10-01 (interview consolidation). This is the sole prioritized plan. The user's latest
assignment sets scope; code establishes implementation and user review establishes
artistic acceptance. This update replaces the completed color-rollout takeover
plan, preserved in [history](docs/history/README.md).

## Current direction

Greater visual variety and complete, expressive world scenes are the priority.
Build one complete scene at a time. The current authorized batch uses internal
per-scene review followed by one integrated Robert/viewer review.
Dev Studio already supports the workflow: build, preview, refine, then integrate
into Main when accepted or explicitly authorized.

A scene assignment includes the assets, camera or object movement, materials,
spatial effects, palette families and any new effect class needed for a
compelling result. Useful new techniques should expand the shared library.
"One scene" does not limit the number of components inside it.

Quality means coherent style, clear depth, fine detail, smooth gradients and
intentional composition in motion, alongside character, change and surprise.
Quiet passages deserve engaging behavior too. Optimize the chosen experience;
do not use performance concerns to justify an inert or visually thin prototype.

## Current priority: authorized Main upgrade batch

Source: Robert's context interview and parent handoff, 2026-10-01.
Galaxy is user-approved at scoped commit
312287e66ece8c0296037d2bfffcc4ac9e3b5609; parent verified push to main.
Galaxy remains outside Main. Water Basin is parked with audio/UI weaknesses;
Envelopers off. Do not resume stale Galaxy correction assignments.

Authorized order: Crystal Cavern -> Sky Citadel -> Magnetic Bloom / Arc
Constellation / Auroral Veil -> Ghostlight Marsh -> Molten Flow ->
director/transitions -> one integrated Robert review. Builder safely paused for
guidance consolidation, now approved/applied. Parent may resume Cavern refinement.
First candidate implemented locally; next scenes not claimed implemented.
Crystal Cavern first candidate independent provisional review: 7.0/10
(identity 6.8, musical connection 7.2), below the 7.5 batch target. Retain
localized musical fronts and settling; refine irregular mineral character,
distinct material behavior and excessive repetitive stripes before advancing.
This assessment is parent-reported, not a fresh review by this documentation task.
Once resumed, iterate autonomously with an honest >=7.5 per-scene target and
one final Robert review.
New original effects/palettes/non-fade transitions approved in this batch.

Global director should use history/energy/contrast/recency and bounded suitable
variation rather than unrestricted RNG; genre/tone recognition is future.
Distinctive identity and musical connection are equally fundamental. Follow
rhythm/mood/tone/energy through actually available features, without implying
semantic recognition. Quiet passages slower/subtly beautiful; depth/3D optional.
Steady BPM-linked flow and pleasing hits/high/mid/low response are valid.

Streams last 1-2 hours, sometimes 4+. Fresh fitting interpretation per song play,
recurring motifs allowed, fixed repeated sequences avoided: intended behavior,
not proof current director fulfills it. Fast deterministic response follows
present input; future semantic ideas build persistent fitting worlds and reject
stale literal events. Lyric narratives remain aspirations.

Preserve richness while smooth; measured hardware tiers/LOD before sustained
crawl. Exact FPS and minimum hardware remain unknown. Renderer replacement/custom engine open to
evidence-based proposal, alternatives/migration and separate approval; no giant
rewrite authorized. ZeraphinaX grows from useful proven reuse.

Optional reference directions retained: NASA Pillars depth/travel, Refik Anadol
ISS Dreams, local MilkDrop/projectM motion/feedback. References only; import no
code/assets without rights review.

## Working checkpoint

- HEAD 312287e66ece8c0296037d2bfffcc4ac9e3b5609: approved Galaxy Odyssey and
  responsive shader startup. Push parent-verified; not queried remotely by this
  documentation task. No further commit/push authorization.
- Local dirty work is authoritative: parked Water/12-band and Cavern candidate
  plus unrelated changes; preserve all.
- Cavern evidence: docs/agent-notes/crystal-cavern-upgrade.md and
  work/cavern-upgrade-01/final/source-manifest.json; provisional 7.0, refinement due.
- Main retains seven materials/newer spatial treatments; Galaxy/Cymatics remain
  outside Main and three Envelopers off.
- Older inspector ledgers contain dated coverage, not current totals.

See [current handoff](ZERAWAVE_HANDOFF.md) for evidence and limitations,
[Studio instructions](DEVELOPMENT_STUDIO.md) for actual controls, and
[technique ownership](TECHNIQUE_LIBRARY.md) for extension points.

## Development and review workflow

1. Inspect the current implementation and relevant references. Choose a coherent
   artistic approach, then build the complete assigned scene and reusable pieces.
2. Iterate in the existing Studio. Inspect motion, quiet/active/release behavior,
   palette evolution and extended interest, as well as technical correctness.
3. Run focused checks during development and broader checks where shared changes
   warrant them. Preserve unrelated scenes, IDs, sessions, resources and clocks.
4. Deliver exact review controls and explain what is visibly new, with honest
   cost/evidence limits. The user and viewers review the whole scene.
5. Refine from feedback; integrate accepted behavior into Main when authorized.

Continue internal implementation steps without repeated approval requests.
Use tests proportionally; avoid expensive repeated full suites without new risk.
Preserve existing user work and the separate authorization rules for commits,
pushes, dependencies, destructive cleanup and release builds.

## Following priorities

1. **More distinct Cosmic scenes**, after the current batch, when selected: multiple suns,
   intersecting systems, scale journeys or a pulsar are candidate directions.
   Choose one with the user; none is a Planet Canvas accessory by default.
2. **Growth, maturity and transformation:** develop worlds that emerge, linger
   and change identity. Scene-specific lifecycles can be built inside an assigned
   scene now; a project-wide director redesign remains a separate decision.
3. **Revisit the three Envelopers** when requested. Preserve their off default
   and review controls. Their current appearance is not accepted for Main.

Original surface treatments, feedback and palette evolution may be part of an
assigned scene; they do not need to wait for separate backlog gates. Cross-world
rollout beyond the requested reusable demonstration should follow observed fit.

## Retained ideas and experiments

| Idea | Current disposition |
| --- | --- |
| Peaceful tree/forest growth | Future scene, distinct from Firescape's growth/burn. |
| Ambiguous transformations | Forms developing into other identities, beyond a dissolve. |
| Occasional faces and creatures | Possible expression, not a compulsory asset list. |
| Quiet states and non-percussive music | Review within new scenes; broader director investigation remains available. |
| Sea sky as material canvas | Optional later change; current sky/reflection boundary remains intact. |
| Soft Dream on Planet Canvas | Existing experimental A/B option; not a prerequisite for new palette families or Galaxy. |
| Bonk / Dance controls | User-deferred. |
| Daddy Long Legs | Shelved, opt-in experiment. |

Fix confirmed regressions and performance obstacles within the affected task.
Do not reassign historical bugs without checking whether they were already fixed.
The Galaxy builder reports repairing the stale moon-test lookup.

## Product direction and later milestones

Source: Robert's context interview, 2026-10-01. First paying audience:
streamers/content creators including musicians making videos. Need live visuals
AND song-to-video export. Default one generated interpretation, optional
variants; edit scenes/transitions/colors before export. Companion reopenable
project preserves timing/variation. These are desired milestones, not implemented
capabilities.

Easy installation/onboarding, distinctive UI, one-click visuals, immediately
findable presets and few screens. Experimental means working but unfinished.
Deep Studio grows from customer feedback. Games/Vesper worlds long-term only.
Offline option; online AI optional. Fully local claims only for actually
implemented/available features and downloaded required resources.

Future lyric-semantic narratives (painting/cracking/hatching dancing eggs)
are aspirations. Audio buffering acceptable in principle for alignment; stream
delivery delay of 3-5 seconds does not establish available audio lookahead.
Fast deterministic response follows present music; slower semantic ideas must
stay fitting/persistent and reject stale literal events.

Tentative commercial hypotheses: tasteful watermark/limited-world free taste,
short clean-export allowance, optional $5 watermark removal and $5 world pack,
premium suite includes both plus creation core, around $10-15 hypothesis rather
than ceiling. Not validated pricing or authority for commerce implementation.
Development subscription, runtime inference, hardware/distribution/support
costs separate; no paid setup/dependencies/accounts authorized.

Preserve work/releases/ZeraWave-preview-final.zip at d4992d0. New builds,
install/update work and device qualification require assigned release milestones.
Earlier task proposals are evidence for incorporation here, not another plan.

## Documentation and ownership

[AGENTS.md](AGENTS.md#16-coordination-and-document-ownership) defines coordination.
Feature workers can maintain their operating/technical documentation and optional
[task notes](docs/agent-notes/README.md). Shared plans have an owner to avoid
conflicting priorities, not to block authorized creative work.

The completed takeover instructions and older decisions are preserved in
[history](docs/history/README.md). Do not resume them as active assignments.
