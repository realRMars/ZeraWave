# ZeraWave development plan

Updated: 2026-10-04 (accepted Main Audio Tuning development checkpoint).
This is the sole prioritized plan. The user's latest assignment sets scope;
code establishes implementation and user review establishes artistic acceptance.
Historical plans remain in [history](docs/history/README.md). The accepted visual
baseline is 2bcb03f; the player checkpoint builds on that baseline.

## Current direction

The reviewed visual batch and current Main/Galaxy preview are user-accepted.
The player interface and bounded device-loss cleanup are implemented and accepted.
Studio organization and Normal/Instant Bonk are committed at 0342e51. Main Audio
Tuning is implemented across all 27 canonical Main forms, with bounded engineering
validation complete. Robert accepted Planet range/gain tuning on October 4 at
06:48 UTC and subsequently accepted this rollout development checkpoint with
caveats, authorizing one scoped commit and normal push with its accepted dependencies.
He observed a transition hitch and requests a performance revisit. An earlier
12× preview does not establish real-time smoothness. Startup/resource limits and
remaining DSP questions stay open; new implementation needs a separate brief.
Distinctive identity, meaningful musical response and sustained visual interest
remain the creative standard; internal technical checks do not replace review.

A scene assignment includes the assets, camera or object movement, materials,
spatial effects, palette families and any new effect class needed for a
compelling result. Useful new techniques should expand the shared library.
"One scene" does not limit the number of components inside it.

Quality means coherent style, clear depth, fine detail, smooth gradients and
intentional composition in motion, alongside character, change and surprise.
Quiet passages deserve engaging behavior too. Optimize the chosen experience;
do not use performance concerns to justify an inert or visually thin prototype.

## Completed visual and player checkpoints

Robert accepted the current Main/Galaxy preview and authorized its checkpoint.
Commit [2bcb03f](https://github.com/realRMars/ZeraWave/commit/2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5)
contains the reviewed Cavern, Citadel, original Magnetic/Arcs/Auroral, Marsh,
Molten, Aftershock, director/transitions, bounded-resource and entry/projection
refinements, and Galaxy's Main integration. Normal push to GitHub main was
verified against the exact committed hash.

Main has 27 eligible worlds, including Galaxy Odyssey36. Water Basin37 remains
parked; Experimental38-40 stay outside Main; the three Envelopers remain off.
The accepted checkpoint does not certify every technical gate. Preserve the
native fullscreen-surrogate/Aperture/Molten pacing, Aftershock7.4, startup,
AV/listening and multi-hour limitations in [the handoff](ZERAWAVE_HANDOFF.md).

The four-root-doc reconciliation is complete and included with the accepted
player checkpoint. Robert reported active BlackShark off -> unavailable -> on +
Refresh recovery without closing the runtime, repeated normal Start/Stop, and
10/10 acceptance. Commit and normal push were explicitly authorized. This does
not certify unattended recovery, audio quality, device diversity or the preserved
startup/performance limits. No release build is part of this checkpoint.

## Accepted development checkpoint and remaining review

- **Player and Studio organization completed:** the accepted player retains its
  recorded controls/device contracts. Main/Experimental navigation and
  Normal/Instant Bonk, including the queue-restart correction, are committed and
  pushed at 0342e51. See the [player guide](docs/agent-notes/player-checkpoint-2026-10-03.md)
  and [Studio guide](DEVELOPMENT_STUDIO.md).
- **Main Audio Tuning development checkpoint accepted with caveats:** all 27
  canonical Main forms have scoped tuning, monitoring and compatible pair audition
  in Studio. Experimental/Cymatics remain excluded until promoted. Robert's
  acceptance authorizes the scoped publication; bounded CPU/native, GPU,
  decoded-audition and scripted foreground evidence does not establish exhaustive
  artistic, continuous-listening, real-time FPS or multi-hour certification.
  See the [current handoff](ZERAWAVE_HANDOFF.md).

### Remaining work: priority not reassigned here

- **Startup and native performance:** Robert requests revisiting the observed
  transition hitch. Real-time pacing, compilation/resource cost and native
  performance remain unresolved; the earlier 12× preview is not a real-time
  certificate. Preserve separate cold/warm, GPU draw, submission and presentation
  evidence, failed probes and full visual quality. No optimization is part of publication.
- **Standalone DSP:** this checkpoint includes its necessary accepted dependencies
  and tests while preserving audio/visual boundaries. It does not declare every
  DSP question complete or authorize another implementation.
- **Next-brief ideas:** newly brainstormed Studio buttons, optional metrics overlay,
  performance report and Open Latest Results await their next coherent brief.
  None is implemented by this publication task.
- **Fractals world/forms and image import:** retained later planning milestones.
  No fractal, image-import or mobile implementation is authorized by this pass.

## Continuing creative and engineering direction

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

- Verified visual baseline: `2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5`.
  Publication parent: `0342e518a7bd2c521416e8027a7920668fc5ee51`, the published
  Studio organization/Bonk checkpoint. The new development checkpoint includes
  the reviewed rollout and accepted dependencies beyond the rollout-only patch.
  Exact publication identity and preservation results are recorded in the
  [publication receipt](work/publication-main-audio-20261004/review-index.json);
  evidence chronology remains in [the handoff](ZERAWAVE_HANDOFF.md).
- Earlier visual review evidence starts with
  [Main lineup](work/main-lineup-01/review-index.json) and the
  [entry/projection delta](work/robert-refinement-02/entry-projection-delta/review-index.json).
  Older candidate notes/hashes remain historical evidence, not current assignments.
- Main retains seven authored materials and existing spatial treatments. Galaxy
  is included; parked Water support preserves Studio imports/saved sessions
  without making Basin Main-ready. Unrelated dirty work and the frozen portable
  remain preserved.
- The three project skills are committed; explicit loading, coordination and
  their validation limits are described in AGENTS.md and ZERAWAVE_HANDOFF.md.

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

## Other retained directions: only when separately selected

1. **More distinct Cosmic scenes**, when separately selected: multiple suns,
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
| Bonk / Dance controls | Bonk is implemented in the player; tap/Dance remains deferred. |
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
