# ZeraWave

## October 16 development checkpoint publication

Robert authorized commit/push/Pages for the current editor development checkpoint.
The implementation remains overall HOLD, with no new progression or acceptance.
See [publication status](ZERAWAVE_HANDOFF.md#october-16-development-checkpoint-publication)
and [receipt](work/publication-editor-visual-build-20261016-1792134379821453600/review-index.json). Older task-time uncommitted wording is historical for this
publication; all failed/unverified gates and unrelated work remain preserved.


## October 15 current checkpoint

Published editor foundation: `4775137229e03203439932146679dee357d91960`.
Robert approved both layouts and assigned the Editor Visual Build Plan; its
implementation remains uncommitted and overall HOLD. The [consolidated candidate](work/editor-visual-build-20261015-1792088667789300800/final-candidate-1792131017952188300/FINAL_REPORT.md)
implements the workspace, Source audition, inline visual/text authoring, mixer/
routing and bounded metadata recovery within their documented limits. Quiet
discard-test settled-seek callback samples are supported; playback callback samples
still fail. Neither establishes physical-display/listening/A/V acceptance. The
[finite review](work/reviewer-editor-visual-phase-f-20261015-01/decoder-followup/REVIEW.md) is complete with no new confirmed correctness defect;
Phase F/whole-stage HOLD, no progression approval and final open gates remain.
Stages 0/1 have recorded 9/10 passes; Stage 2
remains 8.5 HOLD for ordinary single-release Library placement/header reorder.
Independent layout/inspector/audio/persistence work may proceed on stable
contracts under the latest brief; this does not close the HOLD or final gates.
See [current handoff](ZERAWAVE_HANDOFF.md#october-15-editor-foundation-checkpoint-and-current-overhaul)
and [the sole plan](ROADMAP.md#approved-editor-visual-build-plan---current-execution)
for approved phases, F1/F2 and acceptance. Older pre-implementation/handoff-only
wording below is historical where superseded; no new capability is accepted here.

## October 13 selective-migration publication checkpoint

Published commit: `3ca315d0314cb8ca088be560f56c75bca34acd19`. Robert's acceptance
was at 00:56 UTC October 14; Overseer's receipt verifies normal push, GitHub main
and Pages. Shared-guide publication ownership is released; this pass updates only
next-stage documentation without staging, commit/push or implementation dispatch.

Robert authorized publication of the consolidated existing-functionality candidate
and its earlier control-boundary/Layers dependencies. The reviewed source/native
bundle is `ee4b324750a7fa494460568799522ea08f2b43faab9e5c1df74b21f24d9a0f4c`,
on parent `15a980c34b47f22ce27c4290084635b5643edf56`. The
[publication receipt](work/publication-selective-migration-20261013/review-index.json)
records staged identities and verified remote commit. [Actual results](docs/agent-notes/selective-migration-20261013.md)
account for all 12 audit areas as implementations or measured retention decisions;
no blanket language rewrite, quality reduction or higher capacity is implied.

This checkpoint supersedes earlier awaiting-implementation/publication wording,
not task-time reports or their failures. Ordinary physical OLE drag acceptance,
listening/audible device clock/scanout/multi-hour coverage, the exact historical
fallback timeout and cold/complex CPU/high-rate media tails remain limited or
unverified. Passing repeats do not repair the historical intermittent failure.
Session/current-frame still saving works; moving-video Save remains OPEN.
Separate capacity/storage commitments and future image/editor/export requirements
remain outside this migration. The next existing editor stage and its exact review
route are recorded in ROADMAP and AGENTS; publication/documentation dispatch no
Builder/Reviewer or implementation.


## October 11 accepted B3 development checkpoint

Robert accepted the verified B3 correction candidate and authorized publication.
See the [current handoff](ZERAWAVE_HANDOFF.md#october-11-accepted-b3-development-checkpoint)
and [publication receipt](work/publication-b3-accepted-20261011/review-index.json).
Timing remains PARTIAL, one fallback switch timeout is unresolved, and scripted
physical drag evidence remains unverified. Video Save writing stays OPEN; this
checkpoint neither approves its proposal nor closes B3 or dispatches later work.
Dated reports retain their task-time status and measurements.


ZeraWave is a Windows music-reactive visualizer. The current checkout is the
development source; the portable preview is a preserved, older checkpoint.

- [Player instructions](docs/agent-notes/player-checkpoint-2026-10-03.md)
- [Development Studio instructions](DEVELOPMENT_STUDIO.md)
- [Prioritized roadmap](ROADMAP.md)
- [Visual identity](ZERAWAVE_VISUAL_IDENTITY.md)
- [Technique ownership](TECHNIQUE_LIBRARY.md)
- [Current handoff](ZERAWAVE_HANDOFF.md)
- [Historical record](docs/history/README.md)

Use `run_zerawave.bat` for the player and `run_zerawave_studio.vbs` for current
Qt Studio. `run_qt_studio.vbs` remains a diagnostic Qt entry;
`run_development_studio.bat` retains Tk tools. Requirements are in
[requirements-qt-studio.txt](requirements-qt-studio.txt). Studio is currently a
development/review tool; expanded authoring is the approved direction, not a
shipped paid Studio offering.

For agents: read [AGENTS.md](AGENTS.md), then the current handoff and roadmap.
The Overseer maintains shared planning; workers own their assigned changes and
may keep optional [task notes](docs/agent-notes/README.md). New visuals are
reviewed through the existing Dev Studio before approved Main integration.
A scene assignment covers the assets, movement, reusable techniques and palettes
needed for the complete experience. Historical plans, research-stage restrictions
and completed task notes do not narrow the user's current brief.

Galaxy Odyssey is accepted and included in the 30-form Main roster, alongside
Tidal Strata, Recursive Atrium and Honeycomb Garden. Color
Inspector and Studio organization are implemented; the three Envelopers remain
off by default. Robert accepts the implemented Main Audio Tuning development
checkpoint with caveats and passed the measured-performance development
checkpoint for publication on October 5. Water/capture/startup improvements,
compiler tradeoffs and remaining real-time limits are recorded in the handoff. See [Studio controls](DEVELOPMENT_STUDIO.md#main-audio-tuning-and-mapping-monitor)
and the [current checkpoint and limits](ZERAWAVE_HANDOFF.md).

Earlier accepted/pushed finishing development checkpoint:
[`f3d414be7ee380a38865c3579c057597dbb5fb06`](https://github.com/realRMars/ZeraWave/commit/f3d414be7ee380a38865c3579c057597dbb5fb06).
B1 transactions/Undo/Redo and output before PNG durability, B2 optional C++ tiled
resources/history/editor projection, storage recovery/normal close, ordinary image
Save and finishing controls are implemented. The earlier `0fb4c3f` recovery is
historical. [Current handoff](ZERAWAVE_HANDOFF.md#october-10-drawing-and-storage-development-checkpoint)
and [dated results](docs/agent-notes/b2-tiles-20261008.md) retain measured tails,
rejected-stroke redraw, owner-death and unrun broad/product/capacity limits.
[Native setup/fallback](docs/NATIVE_RASTER_B2.md) explains optional local DLLs;
acceptance is not a release or universal responsiveness guarantee.

Approved direction retains Qt, Python authoring/control and the existing GPU
renderer. **[B3 media foundation](ROADMAP.md#b3--bounded-media-foundation) has an accepted
implemented development candidate**, with Video Save open and timing partial: fair bounded decode service, generations,
direction-aware prefetch and timestamp-correct editor/output ownership.
The audit and agreed migration are complete/published at `3ca315d`, with all 12
implementations or measured retention decisions. Next is the
[existing video-editor stage](ROADMAP.md#existing-video-editor-stage---upgrade-end-to-end-workflow):
Prompter's prepared brief, sole manual Builder and Bob the Reviewer's independent
>=9/10 correction/pass increments, then whole-stage end-to-end owner handoff at
supported >=9/10. Planned project-bin/timeline/mixer/captions/shared UI/API/export
features are not implemented by migration. Keep current Upgrade+ Python/FFmpeg
production until parity. Chroma key follows the working editor; separate image
additions and the unidentified extra are not silently included.
Capacity Passes 2–4, higher counts and storage
location/relocation remain separate. No dispatch follows documentation readiness.
