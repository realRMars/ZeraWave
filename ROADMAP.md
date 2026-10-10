# ZeraWave development plan

Updated: 2026-10-10 (drawing/storage/finishing development publication authorized).
This is the sole prioritized plan. The user's latest assignment sets scope;
code establishes implementation and user review establishes artistic acceptance.
Historical plans remain in [history](docs/history/README.md). The accepted visual
baseline is 2bcb03f; the player checkpoint builds on that baseline.

## Current October 10 checkpoint

Robert authorized commit/normal push of the implemented drawing, ordinary artwork
Save/Save As, direct-child, raster recovery, sustainable storage/normal shutdown
and focused finishing candidate on `6aed22041bd15392857c676f832a4f25f07bd765`.
[Handoff](ZERAWAVE_HANDOFF.md#october-10-drawing-and-storage-development-checkpoint)
and [latest actual results](docs/agent-notes/b2-tiles-20261008.md) bind its source,
checks, specific acceptance and remaining limits; publication identity belongs in
the [receipt](work/publication-raster-recovery-20261010/review-index.json).

Robert accepted artwork saving, direct blank children, normal closing, improved
Brush/Pencil and quick Eraser. Smudge mixing is good; responsiveness/sustained
trailing and broader editor/capacity acceptance remain open. These specific results
supersede older blanket unaccepted status only for the reviewed behaviors.
Pass 1 preserves accepted work and fixes lifetime storage/shutdown bookkeeping;
real encoding/queue pressure, redraw of rejected work and owner-death limits remain.
Finishing preserves pixels/output while extending zoom/inspection and first Fill.

Passes 2–4, deeper capacity/higher counts, storage relocation, New Session and B3
are deferred, not cancelled. Prepare later scoped briefs through the existing
manual route; publication dispatches nothing. The earlier B1/B2 contracts below
remain preservation/acceptance guidance, with dated status understood through
this current checkpoint. Native DLL/evidence and frozen portable stay local.

## Current direction

Robert approved **selective native migration**: retain Qt, Python authoring and
control, and the existing GPU renderer; B2 now introduces the small C++ core. The [architecture assessment](docs/agent-notes/zeraphinax-architecture-assessment-20261008-0fb4c3f.md)
records the reasoning and assessment-time limitations. Its original proposal
status is historical; this plan records the later approval. It is not another plan.

Recovery checkpoint: [0fb4c3f](https://github.com/realRMars/ZeraWave/commit/0fb4c3fa28632a6aaedb472be50b1837926b9caa).
Fresh local verification on October 8 found `main` at that full SHA, with the
implemented B1 candidate and guidance uncommitted on top. Its 193 source hashes
and 17 task-file hashes match [B1 final identity](work/b1-raster-20261008/final.json)
before this reconciliation. HEAD alone does not identify the current candidate.
**User acceptance remains pending; the current editor is not accepted.** B1,
B2 native tiled resources/history, renderer-owned editor projection and subsequent
selection/clipboard/Smudge and usability/performance corrections are implemented
as the development candidate authorized for commit/push on October 9. Latest
[actual results](docs/agent-notes/b2-tiles-20261008.md) and [native setup](docs/NATIVE_RASTER_B2.md)
retain source identities, failed trials, bounds and mixed performance. The October 8
B1 hash verification above describes that earlier handoff, not current B2 identity.
No B3 implementation or broad interaction/listening/multi-hour acceptance follows.
Generated DLLs/evidence stay local; fresh checkouts can use B1 fallback or build
the optional native backend as documented.

<a id="next-bounded-work-and-separate-monitor-scope"></a>

### Current implementation and unresolved review problems

- Qt hosting, live colors/tuning, Main30, resolution, Resources, Audio Hub,
  whole-file audio seeking/scanning and Band Analyzer are implemented. Existing
  worlds, audio ownership and Envelopers-off remain.
- Media Library/composition, native-pixel tools, scoped history and silent media
  decoding are implemented as a review candidate. Qt/NumPy, codecs and GPU work
  already use native execution; B2 adds the project-owned C++ raster core.
- B1 accepts immutable raster snapshots into scoped owner history and ordered
  renderer publication before background PNG persistence. Qt/Python ControlOwner,
  process boundaries and pixel policy remain; B2 extends storage/compositing with C++.
- Preserve [B1's documented limits](docs/agent-notes/b1-raster-20261008.md): full-image
  release copies, unchanged Smudge/dense Add costs, memory-only crash exposure and
  no automatic owner reconnection/export after owner death. Unknown outcomes gate
  context changes; close requires secured raster work/checkpoint pins.
- Bounded native input/output and scripted/GPU evidence exist, not broad acceptance.
  Historical Library-drag freeze, floating-pane/general usability problems and
  unexhausted transformed-selection/lock/dialog-failure review remain open unless
  separately reviewed. No multi-hour/listening/physical-scanout certification.
- Browser validation/approval, video audio, rigged/animated models and large-clip
  reverse tails retain their limits and are not B1 additions. Robert reports the
  earlier playback issue fixed; do not reassign the dated Roots/Sky brief. Keep
  its historical measurements without claiming fresh performance certification.

### B1 — raster transactions, recovery and immediate publication

**Implemented; user acceptance pending.** Included in the authorized development
publication. B1 itself introduced no C++; later B2 did. No C++ was
introduced. [B1 actual results](docs/agent-notes/b1-raster-20261008.md) bind source,
checks, native observations, retained failures and review steps; this pass reruns
no application checks and does not close those review issues.

ControlOwner remains logical document/history authority. Qt submits completed
immutable premultiplied sRGB RGBA snapshots through ordered asynchronous commands;
Windows shared mappings feed the existing renderer before PNG durability. Operation
IDs/revisions/epochs and the outcome ledger reconcile unknown/retried commands
without duplicate history. Completed edits and Undo/Redo stay ordered; only
replaceable previews coalesce. Original-source leases support immediate drawing
recovery. Background PNG callbacks record durability without replacing newer pixels.

Save/Save As pins owner revision, settings and Qt drafts, secures portable managed
dependencies and atomically replaces compatible JSON. Failed saves retain their
requested revision; Retry saving/recovery destination and Save As remain available.
Old-session completion cannot mark a new session saved. See the implemented
[runtime/save contract](docs/STUDIO_MEDIA_COMPOSITION.md#runtime-transactions-and-recovery)
for bounds, protected sources, session retirement, close refusal and owner-death
limits. These are candidate behavior, not a claim every user case is accepted.

Preserve the latest [tool, lock, selection and undo requirements](docs/STUDIO_MEDIA_COMPOSITION.md#b1-preservation-requirements):
Canvas recovery is current-layer drawing only; Layers/Library recover structural
work; unfinished paths and text retain their recovery. Preserve IDs, pixels,
placement, authored colors, opacity separation, ordinary-parent versus Group
protection, batch atomicity and independent visibility. B2 must retain these
meanings and B1 transaction/save behavior.

#### B1 acceptance plan

Still the user-review and B2 preservation matrix; recorded technical coverage is
in B1 results, not a newly executed or fully accepted pass through this table.

| Case | Required observed outcome |
| --- | --- |
| Rapid strokes/mixed pixel edits with encoding slowed | Every accepted operation appears in order exactly once in history and canvas/output. No lost stroke, target diversion or unbounded queue; capacity rejection is explicit and preserves accepted content. |
| Immediate repeated Undo/Redo during saving, across layers | Correct drawing versus management recovery; late PNG/ACK results cannot resurrect undone pixels or overwrite newer work. Text/path Undo and exhausted stacks retain scope. |
| Layer/session switches with pending work | Targets and epochs bind operations; old completions cannot mutate the new session/layer. Accepted unsaved work stays recoverable; unfinished gestures follow existing cancel rules. |
| Save/Save As, including disk-full, denied write, dependency/atomic-replace failure | Revision/destination are explicit; old project/dependencies survive failure, dirty/recovery state is truthful, and newer edits survive older saves. Reopen successful saves and verify revision/pixels. |
| Lost/delayed ACKs and retries, including after Undo/switch | Reconcile accepted versus unknown/rejected using the same operation ID. No duplicate pixels/history, false success or duplicate resource ownership; bound outcome-ledger retention. |
| Resource exhaustion | Exercise snapshot/transfer, history, encoding/store and renderer-upload limits. Reject safely without partial structural edits, dangling readers, lost accepted pixels or unbounded memory; recovery/retry remains possible. |
| Source replacement, deletion or closing with pending work | Retire obsolete leases/jobs by document/target revision. Late work cannot restore replaced/deleted content. Close truthfully flushes, preserves recovery or cancels closure for accepted unsaved work; no silent loss or orphaned owned workers. |
| Real pointer/keyboard and visible output | Native strokes/Undo/Redo with docked/floating tools and active compatible renderer; canvas and clean output converge on the same accepted pixels/revision amid slow saving and media decoding. Stills, mocked ACKs and paint-call timings alone do not pass. |

Record input, submission, acceptance, canvas paint, output publication and
persistence separately, including tails/failures. Preserve native dimensions,
brush/alpha/blend fixtures, masks and originals. Select affected standalone
checks, then integrated color/audio/session/renderer preservation at the batch
boundary. Real input and Robert's acceptance remain separate from scripted
passes; no responsiveness/FPS guarantee is established by this plan.

Rollback retains accepted unsaved edits: flush/materialize a recovery revision
before returning to the PNG path. B1 does not promise dense Add/smudge optimization,
natural-media quality, video reverse repair or a general UI redesign.

### B2 — C++ tiled raster resources, copy-on-write history and incremental compositing

**Implemented experimental candidate; user review pending.** The latest results
include native tiles/copy-on-write history and renderer-owned incremental editor
projection, followed by focused corrections. The requirements below remain
preservation/acceptance contracts; they are not a new assignment. Build on the candidate,
not only recovery HEAD. Retain Qt widgets/input, Python authoring/control policy,
ControlOwner transaction authority, compatible sessions and the existing GPU
renderer. A small C++ resource/kernel core changes storage and composition work;
it does not replace tools, the playback engine or B1's transaction/save contract.

- Store immutable tile-version handles with explicit format, dimensions, stride,
  alpha/color-space, lifetime and bounded ownership. Copy changed tiles for a
  gesture; history shares unchanged tiles and swaps references/deltas on recovery.
  Keep structural versus current-layer drawing scopes and original-source recovery.
- Batch operations through a stable C ABI/adapter; no per-pixel Python callbacks.
  Define ABI/version/error handling, build/load packaging and backend availability.
  Inspect the existing toolchain first; any missing installation authorization
  remains a dependency decision, not permission to install through this doc pass.
- Recompute dirty regions/tiles and affected composite dependencies. Masks,
  transformed selections, Smudge neighbourhood halos, Add alpha/strength, rounding
  tolerances and isolated nested groups must retain reference behavior. Structural,
  transform or dependency changes must invalidate all affected regions.
- Keep CPU reference/fallback and the current renderer/context upload owner.
  Evaluate renderer-owned GPU editor projection where measured cost justifies it;
  avoid compulsory full-frame readback and a second renderer. Publish versioned
  immutable resources through B1 outcomes/leases rather than bypassing them.
- Account separately for tiles/history, worker transfer/staging and CPU/GPU caches.
  Bound jobs, eviction and retained revisions; never evict a version still pinned
  by current state, history, save, failed recovery or output readers. Admission
  failure leaves prior accepted content intact.

B1's exactly-once command ordering, unknown-ACK reconciliation, independent
acceptance/publication/durability, revision-pinned Save/Save As, recovery/retries,
session/source retirement and close protection are mandatory compatibility.
Incremental output must converge on the accepted revision without a PNG gate.
Do not turn unavailable native resources into a silently missing layer or change
saved projects to require an experimental DLL. Materialize portable PNG resources
for saving/fallback; verify dependencies and reopen before backend rollback.

B2 acceptance compares tile and full reference results at declared tolerances:
native dimensions, alpha edges, masks, transformed Cut/Extract/Crop, nested groups,
opacity/strength and mixed structural/raster Undo/Redo. Repeat B1's matrix with
slow saving, lost ACKs, resource pressure, replacement and close while work is
pending. Include real pointer/keyboard and visible canvas/output, sustained edits,
tile eviction/history bounds, resize/restart, native backend missing/load failure
and cleanup. Measure matched B1/B2 native-size Pencil/Smudge/dense Add workloads:
input/release-to-acceptance/publication, whole-loop p95/max and peak CPU/GPU memory;
retain outliers and source identity. No resolution/quality reduction or assumed
FPS/speedup. Historical B1 timing is a reference, not fresh B2 performance evidence.

B1/B2 user acceptance remains pending; report newly discovered B1
regressions rather than declaring them solved by native storage. Decoder/audio
migration, timeline/export, new brush physics and broad Studio redesign are later
scope. This reconciliation dispatches no Builder or critic.

### Later planned stages — separate Builder assignments

| Stage | Intended outcome and dependency |
| --- | --- |
| B3 | Fair per-source media jobs/epochs, prefetch and timestamp presentation; follows the selected B2 scope unless Robert reprioritizes. Preserve PyAV and silent video/audio-source separation. |
| B4 | Toolkit-independent document/control facade after parity, removing hidden-Tk domain coupling while retaining Python policy where useful. |
| B5 | Native audio sample clock/prepared processing graph after an audio/timeline brief and dependency decisions; preserve analysis/mapping and raw/output distinctions. |
| B6 | Timeline/cues and deterministic offline song/video export after clock, media and storage contracts; export is not B1. |
| B7 | Modular authoring, richer worlds and optional geometry/simulation through stable resource/evaluation interfaces; artistic priorities follow separately. |
| B8 | Distribution, updates, licensing and community customization under a release/product assignment; preserve the frozen portable. |

These are approved direction, not implemented features or automatic authority
to execute every stage. No wholesale rewrite, engine/graphics-API switch,
browser installation or worker dispatch follows from this reconciliation. B2
handoff follows the Robert/Bob/Prompter route; this pass prepares documentation.

See [current handoff](ZERAWAVE_HANDOFF.md#current-recovery-checkpoint-and-b1-handoff)
and [Studio instructions](DEVELOPMENT_STUDIO.md) for actual controls and limits.

The reviewed visual batch and current Main/Galaxy preview are user-accepted.
The player interface and bounded device-loss cleanup are implemented and accepted.
Studio organization and Normal/Instant Bonk are committed at 0342e51. The
accepted Main Audio Tuning development checkpoint and its dependencies were
published at [b2aacd1](https://github.com/realRMars/ZeraWave/commit/b2aacd11d7d3a8d39bb9d2f5592659fd3d2d999b).
Robert's October 4 tuning acceptance and its caveats remain recorded below.
The newer local roster is Main30, including Tidal Strata41, Recursive Atrium42
and Honeycomb Garden43, with Branching Iris and Flowing Fold transitions.
This reconciliation does not change existing Main30 artistic acceptance.

Earlier, Robert passed the measured-performance candidate for a development checkpoint
on October 5 and authorized commit and normal GitHub push. Acceptance retains
the documented numerical/appearance and engineering limitations. Water GPU cost, capture stalls and startup memory improved, while
Cavern/Marsh/Planet and Fractal GPU cost regressed under the compiler policy.
Full quality remains the default; real-time 60 FPS and cold-start usability are
still unresolved. An earlier 12× preview is not real-time smoothness evidence.
Other implementation follows its own assigned brief.
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

At the published visual baseline Main had 27 eligible worlds, including Galaxy
Odyssey36; the newer local Main30 roster is described above. Water Basin37 remains
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

## Historical published development checkpoints

- **Player and Studio organization completed:** the accepted player retains its
  recorded controls/device contracts. Main/Experimental navigation and
  Normal/Instant Bonk, including the queue-restart correction, are committed and
  pushed at 0342e51. See the [player guide](docs/agent-notes/player-checkpoint-2026-10-03.md)
  and [Studio guide](DEVELOPMENT_STUDIO.md).
- **Published Main Audio Tuning checkpoint accepted with caveats:** its 27
  canonical Main forms have scoped tuning, monitoring and compatible pair audition
  in Studio. Experimental/Cymatics remain excluded until promoted. Robert's
  acceptance authorizes the scoped publication; bounded CPU/native, GPU,
  decoded-audition and scripted foreground evidence does not establish exhaustive
  artistic, continuous-listening, real-time FPS or multi-hour certification.
  See the [current handoff](ZERAWAVE_HANDOFF.md).

### Accepted measured-performance development checkpoint

- **Implemented:** once-per-frame suitable audio resolution with derived aliases,
  gain/clamp/encoded inputs and endpoint/Planet ownership preserved; captures off
  for new previews with saved choices retained, a bounded capture worker and
  streamed replay telemetry; cached preparation/monitor cadence and lazy surface
  targets with bounded necessary Cavern prefetch.
- **Startup and quality:** one integrated program retains a declared-uniform
  contract, NVIDIA limited-inlining policy and bounded first-use prewarm. Full
  remains Main's default. Explicit 75%/50% preview scales soften detail and need
  artistic review for future refinement; they are not equivalent-workload gains.
- **Measured on RTX 3070 Laptop, driver 617.14, hidden loud owner-active 720p:**
  Dyes 80.24→16.23 ms, Waterfall 67.27→15.64 ms; Waterfall→corridor crossfade
  81.27→30.12 ms. Cold program 195.76→110.04 s; observed peak working set
  13.21→6.49 GiB. These are bounded GPU/startup measurements, not display FPS.
- **Limitations retained after checkpoint acceptance:** compiler regressions and Marsh numerical variation,
  expensive Full-quality scenes/transitions missing 60 FPS, long cold startup,
  natural listening and multi-hour behavior. Visible silent decoded runs predate
  the final CPU/Cavern/Fractal corrections; final hidden/focused results cover
  those changes. Do not relabel the visible runs final-source FPS proof.
- **Publication authorized:** Robert passed this checkpoint for commit and normal
  push. Source/staged-content checks and exact remote verification are recorded
  in the [publication receipt](work/publication-performance-20261005/review-index.json).
  Refinement follows later feedback; no new implementation or critic is dispatched. See [actual results and review steps](docs/agent-notes/performance-fixes-20261004.md)
  and [historical source/evidence](ZERAWAVE_HANDOFF.md#current-measured-performance-candidate).

### Earlier remaining-work record

The current bounded sequence above supersedes this older next-brief ordering;
retain these historical limitations without treating old feature ideas as a new assignment.

- **Startup and native performance:** the requested performance fixes are now
  reviewable as recorded above. Remaining cold-start cost, compiler GPU regressions,
  real-time transition/presentation pacing and device/fullscreen qualification stay
  open. Preserve cold/warm, GPU, CPU and presentation evidence separately; future
  work should follow measured remaining risks and Robert's review.
- **Standalone DSP:** this checkpoint includes its necessary accepted dependencies
  and tests while preserving audio/visual boundaries. It does not declare every
  DSP question complete or authorize another implementation.
- **Next-brief ideas:** newly brainstormed Studio buttons, optional metrics overlay,
  performance report and Open Latest Results await their next coherent brief.
  None is implemented by this publication task.
- **Fractals and later import/platform work:** the three Fractal forms and two
  structural transitions are implemented in local Main30; preserve their existing
  review/acceptance status. Image import and mobile remain later milestones.

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
crawl. Exact FPS and minimum hardware remain unknown.

Selective native migration is the approved incremental route above. Renderer
replacement or a different engine still needs its own proposal/approval; a later
small C++ core does not imply either. ZeraphinaX grows through useful reuse.

Optional reference directions retained: NASA Pillars depth/travel, Refik Anadol
ISS Dreams, local MilkDrop/projectM motion/feedback. References only; import no
code/assets without rights review.

## Working checkpoint

- Recovery `main`: `0fb4c3fa28632a6aaedb472be50b1837926b9caa`; branch/HEAD
  freshly verified October 8. The [receipt](work/commit-media-editor-20261008/review-index.json)
  records the 43-file media/editor checkpoint and earlier exact remote push.
  B1/B2 and focused editor corrections are implemented with user acceptance
  pending. Robert authorized this development checkpoint commit and normal push
  October 9; exact source/remote identity belongs in the publication receipt.
- Earlier accepted visual baseline: `2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5`.
  Main30/Galaxy and player acceptance stand; the current editor is unaccepted.
- Preserve dirty color notes, research/planning, originals, assessment, settings,
  evidence and the frozen `work/releases/ZeraWave-preview-final.zip` at `d4992d0`.
  [Handoff](ZERAWAVE_HANDOFF.md) lists the actual pre-pass dirty files.
- Task reports retain their source/failures/measurements and task-time status.
  Earlier priority lists and planning proposals are historical; the B1 ordering
  above supersedes them. B2/corrections are now implemented candidates; no B3
  dispatch follows publication. Skills retain existing manual review requirements.

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
