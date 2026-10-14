# Builder actual results: Studio control/resource boundary — 2026-10-12

The candidate in `C:\ZeraWave` remains **uncommitted**, for Robert's manual review.
This completes the bounded implementation slice. Technical coverage and performance
remain scoped; physical interaction, broader workloads and the intermittent scrub
case below stay OPEN. Reviewer dispatch/publication require their separate manual
authorization. No worker/critic dispatch, installation, commit, push, Pages change,
native rebuild or later-stage implementation occurred.

## Identity and preservation

Started on the October 11 client date; finished under the October 12 environment.
Baseline/final HEAD: `15a980c34b47f22ce27c4290084635b5643edf56` on `main`; index remains empty.
Published baseline Python bundle (239 files): `4a6ba5f8c10f0403b7be726a527190608309529c99a5e6cc6f8eb6ff140132a7`.
Final Python bundle (243 files): `791a3b27471b5afb46dfca93e19b563f9ce8c397151b3d2d71d25d57b0b0b906`. This hashes Python only.
Full scoped before/after hashes, binaries, commands and evidence identities are in
[final manifest](../../work/control-boundary-20261011-1791782042521227300/final.json),
[dirty task baseline](../../work/control-boundary-20261011-1791782042521227300/baseline.json) and
[task-only patch](../../work/control-boundary-20261011-1791782042521227300/task-only.patch).
All 395 pre-existing source/research/media paths outside this scope
and 4680 existing Studio/session/log files match their baseline
hashes. The six protected shared guides are unchanged. The three contract additions
retain their entire pre-task bytes; Overseer's completed reconciliation remains.
Baseline source/session copies are recoverable under `before/`, `user-state/` and
`baseline-runtime/` in the pack. No reset, clean, stash, stage or unrelated deletion.
Audit bytes/hash were verified and the complete report read, including its freeze
addendum/final sequence. Its October 12 label remains provenance.

Unchanged x64 ABI-1 DLLs: raster
`0e13c7e88532251ce15105bc6386fd1351efdbddf49a87d4c58ecf544f7e1cf1`, media
`4604b28a640919a119f311f5e9b3a88ffefe43f6cc2edffa252adf4faf201dda`.
Backends are fixed at process open. No DLL loaded by a user process was replaced.

## Established causes and implementation

Qt tuning, colors, audio, Library actions, ordinary composition/history, preview/
cancel, Retry and session Save had synchronous completion assumptions. The legacy
request could wait for ACK and flush a pipe on the input thread. Completed raster
edits/video already used a worker, but bypasses lacked shared admission/identity.
The broad owner snapshot rebuilt catalog, values, Library/history/resource/save
state for ACKs and the 200 ms timer. These are inspected code causes of avoidable
callback waits/copying, rather than an explanation of every drawing/media stall.

`studio_boundary.py` is a standard-library facade/protocol module with no widgets
or editable document. It captures JSON-owned immutable identity/binding at admission;
one worker orders completed commands/history/save barriers. Active admission is 16,
command size 524288 bytes, retained UI completions 256. Rejected admission changes
no owner state. Same-ID reconciliation retries uncertain ACKs; local Future cancel
cannot discard a completed command or create a sequence gap. Qt polls ready results;
the synchronous legacy adapter is guarded against Qt input-thread use.

Hold has three known owner slots plus release-all, with reserved coalescing delivery
on both sides. Completed edits/history keep their order. Existing latest video
intent and one outstanding composition preview remain bounded/bound. Final preview
commits use optimistic revision sequencing, and cancel is an explicit owner action.
Retry uses the actual owner path and now reports queued acknowledgement before
pending/failed/secured state. Save has an accepted-predecessor barrier and session
guard, then pins the actual requested owner revision/dependencies. The still-save
destination association also uses this boundary; the durable image and association
outcomes are separate. `artwork_save_ui.py` is the demonstrated direct dependency
outside the listed primary files: its old executor bypass had to be adapted.

The Tk-derived owner remains the single authority. Protocol v2 caches catalog,
configuration, coherent document/history/outcomes/save/resource state, and separately
timed runtime telemetry. Versions/owner/session/revision/destination/run install
atomically. Initial/explicit/nominal five-second full sync recovers missing/invalid
deltas; old owners/revisions are rejected. Invalid state retains coherent pixels,
marks the cache stale and blocks new edit admission until resync. Analyzer cadence
and source clocks remain independent. A measured duplicate legacy-view refresh in
the first section builder was removed; refresh now precedes version selection once.
Unexpected disconnection retains a live owner and rejects authoritative Save,
without claiming reconnection or owner-death recovery.
Ordered policy rejection during owner drain now records the rejected sequence before
returning, so Close cancel can continue through the same ledger. A Retry watcher
from a replaced session is discarded without applying its obsolete completion.

Read-only ownership reports stable logical resource/allocation IDs, shared aliases,
document/history/save/publication pins, jobs, retirement and cleanup failures. It
does no pixel traversal/device query on input callbacks. Totals include all raster
allocations; detail caps at 512 rows/eight displayed resource IDs per allocation
with explicit truncation and complete reference totals. Unique allocation
bytes, mapping references, RSS and device-wide VRAM retain different meanings;
external reader/GPU allocation counts are unavailable. This is not aggregate
reservation/admission. Existing caps remain 384 MiB owner raster bytes, 512 MiB
page-rounded mappings, 256 resources, 16 PNG jobs and 256 MiB queued bytes, with
separate native/history/presentation/media/disk limits. Two 16×16 aliases occupied
1024 unique bytes rather than 2048; pending jobs retained leases and legitimate
history retained both resources after drain, on native and fallback routes.

## Matched measurements and limits

[Matched distributions](../../work/control-boundary-20261011-1791782042521227300/matched-results.json) retain raw
per-sample values, block medians, p95/p99/maxima and bindings. Three blocks of eight
Qt key steps per arm used offline form 41 `bass_response`, forced-enabled numeric
control, a fresh empty composition, 1280×720 authored/default canvas, 640×480 canvas
widget, 94×35 numeric widget, actual 1440×900 window/DPR1, MSI AG321CQR 2560×1440 at
144 Hz; renderer stopped. These are control/presentation measurements. Later
history/save tests use 64×48 transparent pixels and a child at native dimensions.
Masks/transforms/blend are default; no drawing sampling/quality/resolution change.
Same installed Python/Qt/PyAV, DLL hashes and instrumentation apply to both arms;
source/driver hashes and environment are recorded per run. Thermal/power control
was not imposed. GPU/rendered/audio tests were coordinated with Monster Trainer
and episode03; later tasks were idle. Planned Robert interaction was permitted.

Milliseconds below are median / p95 / maximum; counts are baseline / candidate.

| Boundary | Counts | Baseline | Candidate |
| --- | --- | --- | --- |
| callback | 24 / 24 | 12.766 / 20.417 / 23.118 | 1.264 / 1.441 / 1.721 |
| first value paint | 24 / 24 | 17.010 / 23.908 / 25.790 | 3.030 / 4.074 / 4.444 |
| coherent | 24 / 24 | 23.512 / 34.017 / 37.792 | 23.591 / 34.695 / 35.424 |
| projection | 30 / 31 | 3.273 / 3.602 / 3.685 | 4.249 / 4.634 / 5.132 |
| serialization | 30 / 31 | 0.346 / 0.405 / 0.406 | 0.329 / 0.394 / 0.398 |
| ack | 25 / 25 | 11.727 / 22.036 / 29.087 | 19.711 / 28.833 / 30.687 |
| command queue | 0 / 25 | 0.000 / 0.000 / 0.000 | 0.113 / 0.312 / 1.666 |
| heartbeat | 748 / 944 | 4.983 / 15.737 / 384.019 | 4.941 / 10.325 / 394.395 |

Callback gains exceed the observed three-block variation at this workload. First
value Paint dispatch may precede owner acceptance; it measures an optimistic
numeric value and is neither accepted pixels nor scanout. Coherent-state medians
are within variation; no whole-pipeline throughput gain is claimed. Owner projection
still costs more under active tuning (immutable copies/ledger metadata); serialization
is similar, and median packet bytes are
16223.0 → 16427.
Unchanged-section reuse is verified; this does not establish a transfer gain for
every active action. Queue/ACK counts include one additional typed value. Baseline
queue instrumentation is unavailable. Whole-workflow heartbeat maxima include
startup/GL/docking/dialog/capture/close and candidate fault UI; they are not isolated
numeric latency. No new numerical acceptance budget was invented.

The 150 ms injected-delay pair is retained separately: baseline callback median
175.290 ms versus candidate 0.911 ms; its later baseline feature expectation failed
because ordinary baseline requests have no operation identity. Only the completed
timing subset is comparable. Actual saturated Hold release returned in 1.990 ms;
reported renderer held-state recovery took 410.460 ms (telemetry/downstream delay).
General Brush/opacity/high-layer responsiveness, natural music and scanout were not
measured by these control samples. Existing B3 timing remains PARTIAL, including
its historical 1684.55 ms stall/fallback switch timeout; Video Save writing is OPEN.

## Acceptance evidence

Every command/exit/source binding is in [check index](../../work/control-boundary-20261011-1791782042521227300/check-index.json).
[Latest evidence](../../work/control-boundary-20261011-1791782042521227300/latest-evidence.json) points to exact packs.

| Required case | Evidence and disposition |
| --- | --- |
| Delayed command; event delivery | Pure facade delayed transport and real Qt injected/ordinary key routes; callback, queue, ACK, Paint dispatch and coherent state separated. PASS within recorded scope. |
| Lost/duplicate ACK; Retry | 23 pure protocol/admission checks, dropped real-owner ordinary-edit ACK, exact history count/Undo/Redo, real write-failure Retry in native/fallback recovery. PASS. |
| Ordered edit → history → Save | Ordinary rename/Undo/Redo, accepted predecessor/session barrier, durable Save As/reopen; final child and still association secured before normal close. PASS. |
| Stale section/reply; replacement | Atomic protocol faults/full recovery/old-owner and revision rejection; real session load, stale media command and completion session guards. PASS for these cases. Real corrupt-pipe/disposed-widget replay remains OPEN. |
| Saturation/admission/aliases | Native resource-bounds; 16-job pressure/source-only accounting; 16 delayed control commands with Hold release/Cancel; native/fallback alias/pin tests. PASS. |
| Pending saves/readers/retirement | Native resource/version/exported-buffer cases, actual write failures, save pins and actual-exit shutdown. PASS. Arbitrary filesystem stalls/owner death remain OPEN. |
| Save As/reopen | Native/fallback accepted-pixel recovery, hierarchy/settings/still association, and isolated restored-source rollback reopen. PASS. |
| Normal close pending/unknown | Eleven OS-observed shutdown cases all exit normally; cancel/failure stays open before explicit discard/recovery. Controlled disconnect flag retains live owner and rejects unconfirmed Save; drain-time ordered rejection and Close cancel retain the same owner/accepted work. PASS for controlled scope; real owner-death/reconnection OPEN. |
| Qt controls/docking | Real Qt key/typing/mouse-button/Hold paths and detach/redock API, source-bound screenshot; Canvas context/tool checks in recovery suite. PASS scripted scope. Physical drag, alternate monitor/DPI and general hands-on review OPEN. |
| Media/audio coexistence | Existing video controls/generations/seek/cancel/session checks, silent generated 320×180/24 FPS/eight-second fixture; source/mute buttons and retained analyzer/source clocks. Latest PASS with intermittent scrub failure below. Live listening/multi-hour review OPEN. |

Executed entry points use the project environment, fresh destinations and existing
standalone infrastructure: `native_resource_bounds_test.py`, `artwork_image_save_test.py`,
`raster_reliability_test.py` (native/fallback), `raster_storage_shutdown_test.py`,
`studio_video_test.py`, plus the three new `studio_boundary*_test.py` scripts.
The pure test command is `C:\ZeraWave\.venv\Scripts\python.exe -B -X utf8
C:\ZeraWave\app\visuals\studio_boundary_test.py NEW_DIRECTORY`. Qt/resource tests
take a fresh absolute directory too. `cb_run_check.py` in this pack records the
exact other commands and adapts only legacy driver waits while pumping Qt; product
callbacks use the facade. Matched private owner sources have identical measurement
instrumentation with separately recorded identities. Python syntax and scoped
diff checks pass. Optional legacy transaction/Qt suites were not run unchanged;
their absent fixtures/fixed paths/synchronous assumptions require isolated adapters.

Failed runs are preserved, not averaged away: early module-path/driver-global and
async Retry expectation errors; harness offline-control activation, reload asset
comparison/readiness, dialog enum, audio-key and dock-parent lookup errors; one
failed fixture held its controlled gate for 265.522 s before actual process exit.
That gate cleanup is corrected; its forced/failed cleanup is never normal-close
evidence. The real Retry queued-state issue was fixed, then recovery passed.
One native video repeat observed only a single intermediate scrub PTS/pixel change
at five 160 ms moves and failed the unchanged three-frame assertion. Prior and
latest runs pass; cause is unresolved (timing/publication/ledger overhead is a
hypothesis). A passing repeat does not repair it. Higher counts/large clips,
live AV, physical interaction, natural exact saturation and prolonged soaks remain
unrun in this migration. No lost accepted edits/duplicate history/resource-lifetime
violation was observed in the passing bounded checks; this is not a global guarantee.

## Work disposition, recovery and rollback

A preview is unaccepted. Pre-admission rejected strokes/actions are discarded and
must be redrawn/repeated after drain/real Retry; no automatic duplicate submission.
Accepted failed PNG/save work remains owned/pinned and recoverable; durability is
reported independently. Unknown ACK keeps its identity and instance/leases; a live
owner is retained on transport failure. Save failure preserves prior good output.
Permanent disconnection cannot authorize this instance's Save; reconnect/owner-death
recovery remains outside this batch.

Rollback must secure every current accepted revision/dependency through owner Save
As to a **new** destination, wait for durable outcome and verify an isolated reopen,
then close that Studio normally. If securing fails/unknown work remains, keep the
instance and source; do not restore underneath it. [Rollback proof](../../work/control-boundary-20261011-1791782042521227300/rollback-proof-1791786276881732900/result.json)
restored all 239 baseline app files on a disposable copy and reopened accepted
drawn pixels/hierarchy/settings with owner exit0. It changed no live session or
candidate source. Actual C-root rollback was not performed.

The pack's `rollback.py check VERIFIED_SAVE_AS_JSON` validates dependencies, rejects
any live Studio owner/UI and later task-file edits. `restore` archives current task
files/patch, rechecks all hashes and restores only this assignment against the
captured dirty baseline (including prior documentation edits). It never resets,
cleans, stages or stops processes. New task files are archived then removed only
after their exact hash check. Backend changes occur at process boundaries. Do not
use an older B3 rollback. Verify the restored runtime on a disposable reopened copy.

## Scoped files and manual review handoff

- `TECHNIQUE_LIBRARY.md`
- `app/visuals/artwork_save_ui.py`
- `app/visuals/raster_resources.py`
- `app/visuals/studio_boundary.py`
- `app/visuals/studio_boundary_qt_test.py`
- `app/visuals/studio_boundary_resources_test.py`
- `app/visuals/studio_boundary_test.py`
- `app/visuals/studio_composition.py`
- `app/visuals/studio_control_client.py`
- `app/visuals/studio_control_service.py`
- `app/visuals/studio_media.py`
- `app/visuals/studio_qt.py`
- `app/visuals/studio_resources.py`
- `app/visuals/studio_video.py`
- `docs/MAINTENANCE_CONTRACTS.md`
- `docs/STUDIO_MEDIA_COMPOSITION.md`
- `docs/agent-notes/control-boundary-20261012.md`
- `docs/agent-notes/control-boundary-20261012.md` (this note).

Reviewer checklist (separate manual authorization): verify final/baseline hashes
and preservation; audit Qt callers/limits/ready-result checks; trace same-ID replay,
ordering/stale packets/atomic installation; inspect aliases/pins/actual retirement;
check Save/reopen/failure retention/history/normal close; review Qt/docking/raw tails
and OPEN coverage; verify exclusions/B3 limits/task-only rollback. Robert owns
acceptance. The manual shared-root proposal is in `OVERSEER_PROPOSAL.md`; shared
planning/checkpoint guides were not overwritten. The sequence stays audit → this
existing-functionality migration/review → separately approved image follow-up →
workflow research/gap review → approved multitrack. No next phase starts here.
