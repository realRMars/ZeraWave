# Video-editor actual results — 2026-10-13 (America/Los_Angeles)

## Increment A: project/bin/shared-command/persistence foundation

The connected A–F assignment is still in progress. No increment-A independent
score/pass has been issued. Timeline playback, audible mixer, graphics evaluation,
product MP4 export and the full Episode04 correction/acceptance sequence remain
the next agreed increments, gated by the existing Reviewer's explicit >=9/10.
This foundation and its automated checks do not establish whole-stage acceptance.

Baseline: main `3ca315d0314cb8ca088be560f56c75bca34acd19`; accepted migration bundle
`ee4b324750a7fa494460568799522ea08f2b43faab9e5c1df74b21f24d9a0f4c`. The source/native identity for this increment is
`11c42b27e644a4dc31553e16aca1aaef5f7d31de5aefc8d082dadfa186975bc1` (297 app/native source entries, three unchanged
accepted DLLs). Bound checks' scoped identity: `d31370df777eb7af137e0754a7a4efc0eea8ad27923cb16e409e130534f9ca94`. Exact file
hashes, patch, evidence and guarded task-only restore inputs are in
`C:\ZeraWave\work\video-editor-20261013-1791942063889153000\increment-A`. The recoverable original dirty baseline remains `C:\ZeraWave\work\video-editor-20261013-1791942063889153000\baseline.json`.

Implemented: version-1 stable-ID project, source/instance/track separation,
integer project frames and rational source times, typed recipes/provenance,
explicit source protection, atomic named batches, exact document/media-status
Undo/Redo, stale/replay/conflict checks and retained command-order binding after
receipt retirement. The existing control thread owns all editable state. Qt
Video Project and authenticated local Python/CLI commands use that same service.
Imports/open/saves prepare on two workers; GPU/audio output is not created by them.
The scoped project bin leaves the global Library/artistic layer sessions intact.

Protected portable `.zwv` Save pins the requested revision, verifies/copies and
flushes dependencies, then atomically replaces metadata. Later accepted edits
remain separate. Failure/cancel retains accepted work and previous files; late
Cancel cannot revoke durable completion. Explicit missing-reference Save reports
unresolved content. Normal Qt close secures/discards/cancels deliberately, stays
open on failure/newer edits and rejects new edits through real resource release.
Open resets in-memory history (document/revision persist); this is documented.

## Checks and evidence

Ten sequential check commands passed against an unchanged frozen source/native
identity, with raw stdout/stderr and START_SOURCE/RUNS/FINISH records retained:

| Evidence directory under increment-A | Actual check |
|---|---|
| model | 9 groups: atomic/replay/stale, exact split/Undo/Redo, frame/sample rational mapping, portable/moved/changed input, write/history pressure and source protection |
| integrity | 6 groups: relink/availability history, strict nested fields/traversal/IDs, missing placeholders, expired SAVE replay, 50/100/250/500 instances and active-overlap bounds, thread exit |
| owner | 10 groups: actual Studio owner, authenticated sockets/installed CLI, 50 instances/70 cues, abandoned reply, 1030 retired receipts, slow 16-save saturation, failure/retry, portable reopen/aliases, unsupported legacy load, projection/normal exit; supplementary full-queue facade |
| qt | 6 groups: actual widgets/owner via synthetic offscreen pointer/key/dialog events, volume/trim/move/caption/Undo/Redo/Save/reopen, text scope, close failure and same-instance recovery/actual exit |
| qt-missing | 4 groups: empty-project control state, explicit decline/accept unresolved-reference Save, truthful Missing row and normal close |
| formats | 3 groups: actual installed H264/AAC codec fixture (96×64/10 FPS/2 s/48 kHz), native-alpha PNG/24k mono imports, 50 video instances, portable fields/provenance/protection |
| boundary | Existing 23 protocol/admission checks |
| resource-native / resource-b1 | Existing 5 resource/pin/accounting checks each, accepted native and supported fallback |
| scope.stdout | Existing 14 category Normal/Instant cases plus direct scope clock/pause/latest and telemetry freshness |

Offscreen Qt is synthetic widget input, not physical Windows pointer/OLE/GPU
preview, listening or Robert acceptance. No foreground/device window was used
for A. No multi-hour/performance/audible-clock guarantee is asserted. Full media
evaluation, rendered references and complete episode/UI/audio/export checks remain
for B–F. Old migration failures/limits retain their original binding.

## Failures and corrections retained

Earlier runs in `C:\ZeraWave\work\video-editor-20261013-1791942063889153000` remain intact. a-model-1 had a fixture audio-import path
error; a-model-2 exposed original-source overwrite protection lost after portable
reopen (only its disposable WAV was overwritten), now fixed with import/relink
provenance and alias protection; a-model-3 expected persisted history incorrectly.
a-owner-1 exposed the header guard's incorrect UTF-8 BOM encoding name, corrected.
a-qt-1 exposed dialog-field lifetime, corrected. a-qt-2/3 exposed text shortcut
interference/incomplete offscreen focus, corrected with modal protection and real
focused target setup. a-qt-4 targeted a hidden tree; corrected visible/focus setup.
No failure is deleted or retrospectively called passed. Subsequent bound checks
verify the final paths. Admission was also corrected to measure a hypothetical
projection without consuming sequence numbers/full-state requests.

## Timing and capacity limits

`TIMING_SUMMARY.json` and raw RESULT/RUNS records separate command submission,
real owner round trip, metadata validation and dialog gestures. Dialog gesture
duration includes the scripted modal typing/wait; it is not GUI-handler stall.
Samples differ by operation and have small counts; no matched speedup claim is
made for a new feature. Single metadata validation samples and callback tails
are retained, including the 500-instance validation tail. Runtime evaluator/GPU,
seek, media, mix and export measurements are later increments. Count ceilings,
serialized metadata, history bytes, queued jobs and simultaneous recipes are
distinct; byte limits may be reached before object ceilings. History accounting
is serialized snapshot bytes, not physical RAM. Four video slots reuse the
existing lane ceiling; 32 visual/16 audio overlap caps remain unqualified policy
until their runtime increments. Accepted history is never cleared for admission.

## Preservation, recovery and review boundary

The eight original Studio log/layout/library files and all unrelated baseline
hashes are checked by PRESERVATION.json; the original dirty copies stay in before/
and user-state/. Overseer's separate read-back receipt is `C:\ZeraWave\work\guidance-readback-editor-1791945802703163700\READBACK.json`.
Its ROADMAP-only correction is excluded from Builder's patch/rollback; the other
five shared guides stay at their original baseline hashes. No native rebuild,
installation, new worker, source asset/master overwrite, staging, commit or push.

Keep the same live owner open on rejection/failure. A rejected command changes
nothing; its last unapplied UI request is bounded to one retained command, with
no automatic duplicate/rebase. Accepted unsaved project work remains in owner
memory/history until a real Save succeeds or explicit discard. Source/open
preparation is not an accepted edit. Receipt expiration is unknown outcome, not
proof of rejection. Owner death/forced termination has no new recovery guarantee.

Before rollback, secure BOTH dirty artistic layer work and video-project work
to new durable destinations, verify dependencies/reopen, then close owned
processes normally. ROLLBACK.md and guarded restore script require current hashes
to match this task's final files and refuse later edits. Restore only task-owned
files against the captured dirty baseline; never apply a migration rollback.
New files are retained in the evidence pack before task-only removal. Preserve
all later edits, shared guidance, original assets, sessions and prior good output.

The candidate is uncommitted. Existing Reviewer owns increment progression;
Robert owns final whole-stage hands-on acceptance and Overseer publication.


# Increment A correction / independent re-review — 2026-10-13

The original A packet and Reviewer verdict remain unchanged historical evidence.
Reviewer gave source `11c42b27…` **7.5/10 HOLD**, with no B progression. Report:
`C:\ZeraWave\work\reviewer-increment-A-20261013-01\REVIEW.md`.
This corrected candidate awaits explicit independent >=9/10. No B implementation,
Robert whole-stage acceptance or publication is claimed.

Corrected full 298-entry app/native plus three unchanged accepted-DLL
identity: `375f88cdedb2cc75a59290613de36c6274c080a103d8564df57dfae433ec39e5`. Frozen fifteen-file check identity:
`e2384ae6a8d9e8c3a6fae80b30141a79ffd27483c9800e4a2580a26b4ce6192e`. Packet: `C:\ZeraWave\work\video-editor-20261013-1791942063889153000\increment-A-correction1`; MANIFEST.json records exact eighteen task
files, complete dirty-baseline patch and evidence. Parent remains main
`3ca315d0314cb8ca088be560f56c75bca34acd19`; index empty, candidate uncommitted.

## Corrections and direct evidence

**R1:** Studio transmits the project identity/epoch/document/command revisions
captured by the GUI decision. The authoritative owner validates before any
cancel/drain/discard. Artwork discard and video discard are separate modes.
An API edit accepted between GUI check and owner close rejects that close;
the same owner/window retains newer accepted unsaved work and its Undo history.
Queries/cancellation and existing resource drain/actual-exit behavior are kept.
Convenience client close binds a new fresh request; it cannot rebase an earlier
GUI discard decision. Video discard requires its separate explicit mode.

**R2:** Batch container/member/nested shapes validate before preparation
classification. Input failures terminalize known rejection; unexpected handler
faults are logged and terminalized, and already installed work remains accepted
with uncertain-result warning instead of a false rejection. No phantom preparing
row can claim work without an actual job. Oversized integers reject without
overflow. Actual API same-ID replay/status, subsequent API edit/Qt Undo and
normal close after invalid commands are checked.

**R3:** Model write-failure fixture now first secures a real `.zwv`, accepts a
new unsaved edit, injects the actual write failure and asserts its exact code/
message, unchanged prior good bytes, exact accepted document and dirty status.
Original bound `increment-A/model` and Reviewer `model` PASS records remain but
their old protected.json case exercised **invalid_destination**, not the claimed
injected write. Original owner/Qt injection evidence remains valid. No original
artifact/hash is edited or retrospectively called a disk-write pass.

Eleven sequential commands pass on unchanged frozen corrected source/native:
focused review regressions5, corrected model9, integrity6, real owner/API/CLI10,
synthetic offscreen Qt6, missing/empty Qt4, actual source-format/codec fixture3,
boundary23, native/fallback resources5 each, unchanged scope14 modes plus
clock/pause/latest/telemetry. START_SOURCE/RUNS/FINISH, raw stdout/stderr and
RESULT files are under bound/. Controlled unexpected-fault tracebacks in the
focused regression's stderr are intentional, asserted logging evidence.

Focused-1 failed because its test clicked an unrefreshed/hidden Undo control.
That fixture failure is retained. Focused-2 and the final bound case use the
visible dock, refreshed controls and actual Qt events. The exact Reviewer R1
interleaving is repeated: previous durable file still contains old revision,
newer accepted edit survives in the SAME owner, continued edit/Undo/Redo/new
Save succeed, artwork-only discard refuses a dirty project, and deliberate
project-only discard with clean artwork closes normally.

These are real owner/socket and synthetic offscreen widgets, not physical
desktop/OLE, GPU preview, audible mix, complete words, export/full episode,
scanout or multi-hour acceptance. B–F remain agreed work after this gate.
Timing retains separate callback/round-trip/model/dialog samples with small
counts; no new matched speedup or aggregate RAM/capacity claim follows.

Preservation and recovery: PRESERVATION.json checks 417 unrelated baseline
hashes and eight original Studio files; the separate Overseer ROADMAP-only
read-back is excluded from task rollback. Accepted DLLs are unchanged. Keep
accepted work open on failed/stale close; Save As new durable revision/dependencies
and verify separately before normal close. ROLLBACK.md/guarded_restore.py apply
only to THIS eighteen-file candidate and refuse later changes. No reset, clean,
stage, commit/push, installation, native replacement, new agent or source/master
overwrite. No live session was replaced. Original baseline and both review
packets remain intact.


# Increment A final close-boundary correction — 2026-10-13

The existing Reviewer gave correction1 **8.5/10 HOLD**, not progression. Read
`C:\ZeraWave\work\reviewer-increment-A-correction1-20261013-01\REVIEW.md`.
R2/R3 and the original R1 delayed-API case were independently confirmed fixed.
One remaining R1 guard/publication boundary is now corrected; this source still
awaits explicit independent >=9/10. No B implementation or owner acceptance.

Full 299-entry source/three unchanged accepted-DLL identity: `1453ddf1699bcf4c6194a5b5e7e3ba0f84571fe095fb64a750b57caea600c5a5`.
Frozen sixteen-file affected-check identity: `a57235ca1cda89d66e4e490b7ada0d5228479d4e8d694a2352ca6e97c07eb6c3`.
Nineteen task files / complete original-dirty-baseline patch / exact evidence are
in MANIFEST.json. Main HEAD 3ca315d0314cb8ca088be560f56c75bca34acd19, index empty, uncommitted.

The close-readiness service now reconciles completed preparation BEFORE checking
the exact ORIGINAL captured close binding. No later poll can publish past that
guard. Future work finishing afterwards remains an owned job and prevents close.
Clean close waits; explicit discard cancels only still-unaccepted jobs after
the accurate guard. Newly installed revisions reject a stale decision and stay
accepted/recoverable. Owner passes its existing binding into this one service
operation; no rebasing or new close architecture. Per-domain discard and old
delayed-API protections are retained.

New focused `project_prepared_close_test.py` uses real preparation-pool threads
with controlled interleavings. Both clean/discard are checked for completion
before reconcile, a running worker, and completion between reconcile and guard.
Newer accepted revision survives stale close; same service edit/Undo/Redo/Save
recover; explicit missing metadata remains truthful; cancelled unaccepted work
reports cancellation; actual pool threads exit. This is service-level controlled
evidence, not a separately repeated physical full-window loss case.

Six sequential affected commands pass against unchanged frozen source/native:
prepared-boundary3, actual owner/API/offscreen Qt review regressions5 (original
R1 plus malformed/recovery/separate modes), Qt controls/close/recovery6, actual
owner/API/CLI10 (pressure/retry/portable/reconciliation/actual exit), corrected
model9 and integrity6. Raw START_SOURCE/RUNS/FINISH/stdout/stderr/RESULT records
are under bound/. Original corrected missing Qt/source-format/boundary/native/
fallback/scope evidence from correction1 is reused with its original source
identity; this change only moves close reconciliation/guard and adds the focused
case. Intentional unexpected-fault logs remain asserted diagnostics.

All old Builder and independent Reviewer packets/failures remain unchanged.
Correction1/initial A scores, original close loss and old invalid_destination
fixture are historical evidence, not retrospectively passed. Current preservation
checks cover 417 unrelated baseline files/eight original Studio files and accepted
native identities. Overseer's ROADMAP-only read-back remains separate/excluded.
No physical/OLE/GPU preview/audible mix/complete-word/export/full-episode/scanout/
multi-hour claim. B–F remain agreed scope after the review gate. No install,
new agent, reset/clean, stage/commit/push, live session/asset/master overwrite.

Recovery/rollback remains task-only: keep accepted work in the same live owner
after stale/failed close, Save As to new durable destinations/dependencies and
verify in a separate disposable instance, then close normally. This candidate's
guarded restore refuses later edits and excludes shared guides/unrelated assets;
old migration/A manifests must not be applied over later increments. No rollback
was executed. Robert owns final whole-stage hands-on acceptance/publication.


# Increment B timeline/evaluation actual results — 2026-10-14

A correction2 received independent **9.0/10 PASS** on source/native
`1453ddf1699bcf4c6194a5b5e7e3ba0f84571fe095fb64a750b57caea600c5a5`.
Receipt: `C:\ZeraWave\work\reviewer-increment-A-correction2-20261013-01\REVIEW.md`.
Historical holds above keep their own bindings. B alone is now submitted to the
existing Reviewer; C–F remain the authorized continuation after explicit >=9.
No Robert acceptance or whole-stage completion is claimed.

The Video Project dock now has real clip/linked-track move/trim handles, ruler and
precise frame seeks, zoom/scroll, optional edge snap, scoped split/delete/history,
and spatial-layout controls. Release submits one owner operation; a gesture is
only a preview until accepted. Intervening revisions invalidate it. Lists reuse
the same document rows during transport. The owner rational nanosecond clock
retains subframe phase through ordinary edits, resets replacement epochs, and
owns timeline evaluation explicitly while active; Stop resumes legacy clocks.

One immutable evaluator supplies exact rational frame/source/sample mapping,
exclusive ends/gaps and active recipes. One latest-demand codec owner prepares
native RGBA, deliberately shares identical source clocks, and retires inactive
windows. Four decoder clocks, 96 MiB shared planes, 128 MiB RGBA/scratch admission
and explicit take/release readers bound work. There is no silent downsampling.
Changed hashes, decode/resource errors retain the accepted document and report a
failed requested preview. A deliberate new seek/relink can recover the worker.

The Qt context owner adapts those snapshots to existing renderer EditorSurface /
ImageLayers at authored output resolution, retaining transforms/crop/masks/blends.
The CPU fallback uses existing Qt projection. Brightness1 preserves legacy RGB;
new brightness clamps unassociated colour before premultiplication, preserving
alpha. Existing mask contracts are enforced before acceptance. Texture replacement
has a 256 MiB guard; existing group-target accounting excludes the separate RGBA8
authored output (3,686,400 bytes at 1280x720), reported separately. These are owned
resource bounds, not total-process RAM or a qualified simultaneous capacity.

Actual CFR, positive and signed-start VFR, first/last/exclusive frames, overlapping
same/different clocks, source replacement, seek cancellation/readers, 50 shots,
pressure/recovery, alpha, encoded rotation/SAR and subframe clock were checked.
Signed Matroska starts exposed refused seeks. The project opts into signed PTS;
those streams decode from the beginning on a backwards miss within existing
512-frame/two-second GOP work bounds. Long signed-source random seeks can fail
explicitly at those bounds; no unrestricted scan/incorrect zero-clamping.
Legacy DecoderWindow calls retain their existing nonnegative policy.

Final frozen standalone run: project_timeline15, studio_timeline10, video_project9
groups passed. The Qt test uses the real owner/socket and synthetic Qt input:
linked movement/right trim/track change, stale release, queued scrubs, play/pause/
stop, keyboard split/delete, spatial modal controls, exact Undo/Redo, portable
Save/Close/Open and actual owner/media/reader exit. Earlier command/API/integrity/
review, 23 boundary checks, Layers/composition and media evidence is retained with
its own source binding. The final packet indexes commands and hashes.

Two disposable Windows Computer Use instances exercised actual input. CPU route:
move, trim, compatible-track change, ruler seek, exact Ctrl+Z/Y, short silent play,
Stop, Save revision6 and normal close/readback. First layout-changing attempted
gesture was unconfirmed and not counted; freshly observed gestures succeeded.
GPU route after Episode06 owner release: actual Qt QOpenGLWidget, seek30 displayed
source0.6s; moving linked clips10frames updated that same frame to source0.3s;
revision2 saved and normal close returned owner0/media exited/protocol0. Separate
artwork/library/layout/log paths protected user sessions. No audio device used.
The latest device-release message to Episode Producer could not be delivered
(local host mismatch, then durable routing error); testing had already ended.

Hidden GL comparison on RTX3070 Laptop, native96x64 source/authored1280x720,
rotation8/Fit/opacity.73: default-brightness output and all five blend modes were
byte-exact against captured pre-B ImageLayers. At brightness.24 CPU-vs-GPU filter
phase differs: mean .149032 byte units, p99 1, maximum33; raw pixels retained.
20 warmups +60 alternating timed samples per arm: baseline CPU median .41595ms,
p95 .59136/max1.2182; adapter .5358/p95 .70406/max1.5034. Both GPU medians .088064ms,
max1.061888/1.1264. Zero >50ms samples in that fixed-frame GL fixture. This is
adapter overhead/fidelity evidence, not a speedup/FPS/scanout claim; production CPU
work may have overlapped, thermal/power uncontrolled. Qt cold seeks/staging have
larger tails; final packet preserves samples/counts/median/tails/max/stalls.
Submission callback time is measured separately from complete synthetic gestures
(which include 20ms pump and owner reconciliation). Older `callback_ms` gesture
fields are historically mislabeled and must be read as gesture-to-reconciliation.

Preserved failures: missing output argument in boundary runner; initial Qt fixture
waited for any preview rather than matching revision; negative Matroska seek bug
now repaired; first backwards-test positive seek on the signed demuxer refused;
rotation fixture used ineffective FFmpeg metadata before display_rotation corrected.
These are retained alongside passing repeats, never deleted or silently recast.

Unrun B limits include real OLE imports/detach-redock/layout restoration on this
new dock, all source codecs/long GOPs/rotations, population UI tails and multi-hour
use. B preview is silent and text recipes are not rendered until D. Mixer/device
sync, full Episode04, listening/complete-word inspection, actual export and final
acceptance remain C–F. No install, agents, shared-guide rewrite, commit or push.
Current identities/diff/rollback and evidence are in `increment-B/FINAL_CURRENT.json`
under the task pack. Restore only verified task files after securing accepted
video/artwork in new durable destinations and normal close; preserve later edits,
unrelated dirty baseline and owner ROADMAP reconciliation. Do not use old A-only
rollback over B; final packet supplies guarded dry-check and current full scope.


# Increment B R1/R2 correction — 2026-10-14

Independent Reviewer gave B source `bf51b3f8…` **8.5/10 HOLD**:
`C:\ZeraWave\work\reviewer-increment-B-20261014-01\REVIEW.md`. No C progression.
R1 controlled actual GL/media/widget callback rendered old pixels after projected
project close. It was not an observed physical flash or scanout race. R2 minimal
QWidget retained capture after revision cancellation and mouse-up; real full-shell
check retained it immediately after cancellation but released after mouse-up.
Both distinctions and original evidence remain preserved. Reviewer additionally
verified nonblack-background/all-five-blend CPU/GPU parity within one channel value;
no background-blend defect was established.

The correction pins a request tuple with each GPU pending snapshot, gates actual
consumption on project/document/epoch/revision/live transport generation, and
checks live generation for retained CPU/GPU redraw. It retires obsolete readers
once without clearing newer status/binding. If that preserved intent has no
preparation after retirement, normal polling starts it. Same-generation playback
keeps a valid preceding presentation rather than flashing a blank between frames.
Central gesture cleanup cancels preview and releases only the timeline's grab on
revision, Escape, close/replacement, hide, deactivation/focus and destruction.
Workspace shutdown uses it; another widget's grab is preserved.

New standalone `project_preview_boundary_test.py` exercises actual Media reader,
GPUView callback and existing ProjectSurface under a hidden RTX3070 context, with
controlled projected-state interleavings. Revision/project-ID/epoch replacement,
close/paused-seek/same-frame-new-generation are refused before render. One reader
release, newer status and normal-poll request recovery, current blue-frame recovery,
actual injected render failure/newer-seek recovery, bounded same-generation lag,
pending close and actual media/compositor exit pass. Native/Qt/detected dimensions
are recorded separately. It does not claim native Qt event-race/physical scanout.
Actual QWidget synthetic cancellation includes destruction and repeated interaction.

Real Studio owner/offscreen Qt timeline now passes eleven groups, adding immediate
capture assertions after API revision invalidation/Escape/Close and exact no-edit
state. Timeline15/model9 still pass; affected product paths were unchanged during
those runs. Final correction packet binds the new test expansion and current code.
The corrected GPU callback does not change the shader, native pixels or decoder;
old fidelity and physical gesture receipts are reused with their original hashes,
not claimed as physical repeats of the cancellation/race correction.

Preserved additional failed fixture: first boundary read assumed64x64 instead of
the detected reference framebuffer; corrected to record/read actual size. No
product rendering failure was hidden by that harness correction. Boundary runs
1–6 and each source-time result remain distinct. No C, install, dispatch, commit
or push; Reviewer re-review still owns the explicit >=9 progression decision.


# Increment C connected audio — 2026-10-14, validation in progress

Independent B correction1 received explicit9.0/10 PASS on source/native
`014087923ccc91bc3d7fff0475c90c1eb2d7fe63b1bf8a9788e8df65073605ba`.
Receipt: `C:\ZeraWave\work\reviewer-increment-B-correction1-20261014-01\REVIEW.md`.
B's original8.5 hold and stale-paint/capture reproductions remain historical.
Its immutable receipt corrected mutable-navigation indexing without code/test
changes. C's recoverable baseline is `increment-C/BASELINE.json` in the task pack.

C now evaluates absolute rational sample spans from the same project evaluator.
Native PyAV prepares canonical48k stereo from actual mono/stereo8–192k sources;
mono duplicates without hidden3dB attenuation. SoundFile/PCM remains the supported
audio-file fallback. Clip/track gain/mute/fades/envelopes remain saved authoring
recipes; trim/split preserve their curve window. A Qt envelope table edits those
points, and untouched gain dialogs retain full authored precision/no phantom edit.
Video audio uses its video timestamp origin, preserving genuine source offsets.
Within one coarse container time-base tick, exact decoded sample counts resolve
quantization holes/overlaps. Larger timestamp gaps remain explicit. Random seeks
in coarse/signed media retain timestamp/GOP/work limitations; no audible-position
or universal codec qualification follows from these checks.

One prep worker has four prepared blocks/one replaceable configuration/sixteen
deliberate source clocks/64verification stamps. Shared32MiB cache/scratch admission
reserves native conversion and a conservative4MiB preparation scratch allowance
before work; the allowance covers maximum16x source step/192k fallback stereo
slabs/grids/conversion/gain temporaries. Ready PCM queues/opaque native codec
allocations/output buffers/analysis/process RAM remain separate. No history or
accepted artwork is cleared to retire obsolete runtime readers.

The existing AudioOwner alone opens/serves/releases output. Project Play parks
legacy listening/file state and releases its previous native queue; Pause/seek
flush old audio, Stop/close restore retained source/settings. Paused seeks before
first Play do not steal listening. Pending ownership also rejects conflicting
legacy source actions; separate Experimental output cannot race the project.
Captured PCM is never replayed. Existing Main consumes the same PCM bus. Master
volume/mute remain playback-only; analysis consumes the raw authored mix. Qt shows
project PCM and parks legacy transports while leaving master controls available.

Runtime separates requested/applied binding, prepared/submitted sample/padding,
transition pending/buffering/failure and durable document state. Timeline progress
uses submitted-minus-observed-padding as an estimate, not measured audible time.
Nearest rational sample boundaries include NTSC rounded-down ends. Initial prep
and underflow hold progress without dropping ordered source samples; empty prep
waits yield rather than spinning. Terminal errors/ended state persist until a
deliberate transport action. Release uncertainty blocks replacement and retains
original/release errors; actual worker exit is not proof of device release.

Executed numeric/controlled checks: mix9, single-owner output8, delayed prep4,
sample clock4, realowner/offscreen Qt audio7, accepted legacy transport checks and
timeline15. A frozen full run is `increment-C/checks-1791986012238467300`; later
pending-ownership guard has focused output8/legacy repeats, and scratch-accounting
change has mixer9 repeat. Current final source/check binding is recorded in the
current packet. UI/audio null tests explicitly use discard-test or controlled
sinks, not hardware. Actual source-copy mutation errors recover in the same
owner after original identity is restored and a deliberate Play; accepted gains/
envelopes/IDs survive exact Undo/Redo and portable Save/Close/Open. A 70ms per-block
controlled delay preserves every ordered48k stereo sample/tail and reports waiting.
Natural four-block saturation stops prep; latest cancellation/seek resumes safely.
Actual PCM socket labels project binding rather than falsely claiming capture.

Additional actual-rate comparisons8/32/44.1/96/192k mono/stereo are byte-exact to
whole native resampling reference; encoded stereo MP3 preserves distinct channels
and full canonical count. Numeric whole392.7s/11,781frame, NTSC and24/30FPS mapping
is exact; it is not whole-episode device playback/listening. Native24k mono DC
resampling ripple2.160668e-6 initially failed an overly tight1e-6 constant check;
whole native reference is byte-exact and disclosed3e-6 bound fits measured codec
coefficients. No loudness compensation/voice reconstruction was invented.

Matched48k stereo prep,2048samples/42.67ms block: accepted B9 SoundFile Decoder
versus shared evaluator+native mixer.20warmups/180timed blocks: baseline median
.26565ms/p95 .2909/max .5166; project .97745/p95 1.094125/max1.5069, no>10ms.
Sixteen distinct source clocks,5warmups/35timed blocks: median13.0441/p9513.71461/
max14.9863;18>10ms/zero>50ms. Raw samples/source/input identities retained in
mix-comparison-1791985137121663200. Later scratch reservation changes accounting,
not DSP; a final comparison binds that change. Retain NumPy policy/vector math
and native codecs/resampling: these costs do not justify a new C++ engine or
quality reduction. Different caller work, uncontrolled desktop/background load
and excluded device/Qt/FFT costs prohibit FPS/deadline guarantees.

Failed runs retained: tight mono coefficient threshold; a fixture added an audio
stream after starting container mux (zero-length failed output/native exit), now
declares both streams first; coarse PTS fixture exposed invented holes, repaired
by bounded sample continuity; Qt restore assertion needed GUI-refresh wait after
owner state arrived; discard-test environment incorrectly overrode explicit
controlled factories, corrected to respect the supplied factory. No failed input,
source, original packet or prior good production output was overwritten.

Real Qt/device checks are pending Robert's coordinated window. Both Episode and
Monster durable messages failed app absolute-path routing; their current tasks
reported idle and a fresh Windows inventory showed no Python/FFmpeg/Godot jobs,
but failed delivery is not owner confirmation. Overseer was notified; no foreground
or real output device has been used for C. Full Episode04 continuous playback,
listening/complete-word judgement, moving export, D–F and final acceptance remain
open. No C progression score has been requested as a substitute for missing
evidence. No new worker, install, commit/push or shared guide rewrite.


## C EC1 correction and bounded device completion — 2026-10-14

Early Reviewer found an older output report erased a newer pending request.
Reporting now reads/publishes latest requested serial/binding under the same
owner lock as admission, keeping applied and last-submitted bindings separate.
New seek/Pause/Stop intent remains pending across old completion/failure. Original
submission and uncertain-release errors remain visible; replacement is blocked.
Focused actual-owner/native-prep/controlled-output checks pass four cases; the
Reviewer independently repeated them and the original reproduction. Original
candidate/report/failures remain unchanged, not retrospectively passed.

The first Computer Use attempt was stopped with physical Escape. Its disposable
instance closed normally (owner0/media exited/protocol0); the interrupted run is
retained and not counted as physical acceptance. Robert renewed continuation.
The new disposable Windows Qt/GPU/default WASAPI instance was used for gain1→.5,
Undo→1/Redo→.5, Play to exclusive8s end, exact frame20 seek, Play/Pause, Stop,
managed Save revision4 and Alt+F4 normal close. Source-bound states/input/audio/
preview logs, captures and VERIFIED.json retain observations and pacing samples.
A detected-input interruption of an attempted Stop was refreshed and repeated;
no blocked attempt is counted. Native output reports submitted/released/padding,
no deadline failures; this is real device evidence, not listening or speaker-clock
accuracy. Managed dependencies hash Ready and saved gain/IDs reopen exactly;
real-owner offscreen Qt reopen and legacy/live-capture coexistence tests supplement
this bounded physical path. Existing sessions/logs and native DLLs are preserved.

Final matched scratch-reservation run: 20warmups/180 blocks, old Decoder median
.26955ms/p95 .306255/max .4578; shared evaluator/native mix .9915/1.129085/1.3941.
16 independent clocks,5warmups/35 blocks:12.9221/13.92055/14.2017ms;18>10ms,
zero>50ms; peak tracked cache plus scratch allowance5,242,880bytes. Output pacing
is separately recorded; these DSP costs justify retaining vector policy/native
codec servicing, not a rewrite, universal deadline or speedup claim.

C's final packet requests the existing Reviewer's explicit>=9 progression gate.
D–F/full Episode04 AV listening/export and Robert's acceptance remain open.
No new worker, installation, shared-guide overwrite, staging, commit or push.


C final accounting correction: Reviewer reproduced silent-span reserved4MiB but
reported16KiB/peak0. Reservation is enforced already; wrapper now always reports
reserved allowance, retained peak and current/live-after-preparation bytes, also
for silence/mute/gaps. Three numeric cases and full affected C checks pass. This
counter-only change reuses the earlier real device evidence with exact provenance.
Packaging retained two reverse-patch failures from91CRCRLF endings. Normalized
output parsed text is identical; fresh full/C patch reverse checks pass.


# Increment D text/graphics — 2026-10-14, verification in progress

C received explicit9.0 pass from existing Reviewer on57beec171f533492ed31b349c312da817557093bac82e78554cf82328a46ae3c;
report work/reviewer-increment-C-final-20261014-01/REVIEW.md. D's recoverable
baseline binds it in the existing task pack increment-D/BASELINE.json. No new
worker, shared-guide ownership, install, commit/push or E progression is inferred.

D adds owner-backed atomic UTF-8 SRT import, preserved stable IDs/provenance,
caption/title/style controls and frame-driven counter/progress recipes. Qt glyph
pixels flow through the existing native/CPU compositor, preserving native source
artwork, transforms, alpha and stacking. Text cache/scratch64MiB and128 entries
are separate from media, GPU, history and opaque font/process allocations.

Actual102protected Episode04 cues import, keep all text and fit at most two lines
at1280×720; exact Undo/Redo and Save pass. This is metadata/glyph evidence, not
speech alignment/listening. Core9 groups cover Unicode/wrap, boundaries, GPU/
reference distribution, corrections/cache, pressure/recovery, SRT/history/save
and explicit malformed/overflow errors. Qt6 groups cover caption/style UI, precise
unchanged dialogs, timed title preview, save/reopen/art preservation and normal
owned exit. Broad model9/Qt foundation6/timeline15/Qt timeline11/owner10/integrity6/
boundary5/command23/composition/Layers/Qttext6/preview-boundary6 all pass on their
recorded bindings. Later optional padding/line-spacing preserve default behavior
and have focused core/Qt repeats; final check/source identities are in the packet.

Finite upstream finding: a paused seek before first project Play applied its
request but left pending true. Now its no-output boundary reports Paused/applied,
retains requested sample separately and does not claim/stop/replace legacy output.
Four stopped/playing-file cases plus existing output8/delayed-report4 pass.
C's prior source-bound approval and device evidence remain historical, unchanged.

Failures retained: initial synthetic renderer path was relative and existing
composition rejected it; private runtime identities are now absolute, no files
created. A broad-tail helper was automatically rejected; exact hash-guarded two-
method replacement proceeded. First regression runner omitted required harness
destinations, corrected with new outputs. Font diagnostics changed during that
first runner; no unchanged-source claim is made for it. Later actual Qt text run
exited0xC0000005. Two faulthandler runs identified QRawFont.familyName as the native
crashing diagnostic; removal preserves glyph rendering/saved styles, primary
family reporting only. Corrected real-owner Qt6 and broad suite then pass. No user
session or original artwork/log was used in these disposable failures.

Matched1280×720 hidden RTX3070 output, no sources,3editable text recipes including
dynamic progress:20warmup/60timed pairs. Captured C no-text CPUmedian.18360ms/p95
.20732/max.21950 vsD2.72070/3.14485/3.44190; GPU.006144/.007168/.007168 vsD.414720/
.5720064/.822272. Query waits separate; no>50ms. ColdCPU C4.6833/D34.2987ms;
three text recipes are added workload, not a speedup. Native Qt glyphs/GL remain;
these measured costs do not justify a new text engine or quality reduction.
Raw samples/conditions in increment-D/matched-1792009787461191000; no scanout/
whole-editor FPS claim or controlled power/thermal guarantee.

The bounded physical D caption/style window is pending coordination; headless,
native GL and synthetic Qt evidence do not pretend it occurred. Full moving
export, Episode04 correction/AV/listening and final whole-stage review remain E/F.


## D early R1/R2 correction — 2026-10-14

Existing Reviewer held early source5dffcbce... for lost visual line breaks and
unreadable tofu captures. Both original report/source/captures remain historical.
Explicit CRLF/CR/LF/U+2029 now map to U+2028 in layout only; saved text/provenance
are untouched and UTF16 formatting uses the resulting layout text. Focused9
checks verify LF/CRLF/CR/blank/trailing/Unicode lines, overflow and missing-family
rejection; the first harness put its overflow assertion in the single-line loop,
corrected with a new destination. Reviewer independently verified the correction.

Windows Qt offscreen started with0registered fonts, explaining empty resolved
families/tofu in original captures. Missing offscreen families now register only
existing installed Windows font files via read-only registry lookup, bounded64
successful files with source hashes. No font install/system/registry write.
Safe QFontMetricsF codepoint coverage rejects unavailable glyphs before claiming
readable output. Existing Segoe UI/Yu Gothic/Emoji cover representative inputs;
per-glyph familyName remains excluded. Corrected real-owner Qt6 and actual102cue
repeat pass; cue001 was visually inspected and is readable English. Old102cue
and timing data used missing-font boxes and do NOT establish readability or
readable-glyph cost. Independent correction report is
work/reviewer-increment-D-correction1-20261014-01/REVIEW.md.

Fresh corrected-font matched run matched-1792010686221136000: native1280×720,
20warmup/60pairs, CPU C.18220median/.206755p95/.22540max vsD2.72465/2.95723/
3.48150ms; GPU C.006144/.007168/.007168 vsD.425984/.606208/.835584ms;0>50warm.
ColdCPU C2.8196/D106.2093ms includes existing-font registration/hash/cold shaping.
Query waits separate. Source/code/fonts/input identities retained; added workload,
not speedup/FPS/scanout. One-time font preparation and opaque font caches remain
separate from64MiB text/cache scratch admission. Native D caption/style/reopen
still awaits coordinated foreground availability; E is not approved/implemented.


## D physical completion — 2026-10-14

The authorized disposable native Qt/GPU window completed caption correction with
explicit LF, style size27→36/color#ffe8b2/spacing33→45, exact style Undo/Redo,
Save As revision5, project Close/Open and normal Alt+F4. Reopened two readable
lines retained stable IDs, all source/clip/track counts and exact saved document.
Independent portable readback dependencies Ready; owner0/media exited/protocol0.
Captures/input/state/source/logs are in increment-D/physical-1792012622889869700.
Final source stayed unchanged throughout; earlier pending-window statements are
historical. No audio played and no original session was replaced. Text history
and dynamic timing have controlled Qt/model evidence, not physical repetition
here. Final D packet requests the existing Reviewer >=9 gate before E; whole
export/episode/AV and final acceptance remain open.


## Increment E actual export and R1 correction — 2026-10-14

D passed9.0 on86aff7b4... through the existing Reviewer; its exact baseline is
in increment-E/BASELINE.json. E now pins one project revision and exports actual
MP4/H264/AAC through the shared evaluator/compositor/text/media/mixer, no device
output. Later edits/Undo/Redo/Save remain independent. R1 independently reproduced
later accepted destination-reference/protection conflicts. Owner reservations now
cover preflight, real async commit, path/hardlink/provenance, retained history and
preexisting preparation. Independent correction report
work/reviewer-increment-E-correction1-20261014-01/REVIEW.md; focused4groups pass.
History reference paths are deduplicated before alias inspection.

Final broad19scripts at checks-1792015309912662300 passed; subsequent R1 reservation4/actual
export4/QtExport4/owner10/preparedClose3 passed at R1-checks-1792015920678938400. Broad/parity
reuse exact provenance: only service reservation/new test and closed text cached-
item counter differ; rendering/encoder/mixer paths unchanged. Final counter-only
actual-export repeat passed at retirement-counter-1792016334782291800. Full plane/reader/PCM/text/texture
live resources retire; legitimate owner history and font/global peaks are separate.

Real native window physical-1792016186140016300: actual Export button/native output+CRF18
dialog/newfile path/progress/exported5, normalAltF4 owner0/mediaexit/protocol0.
No audio played; full120frame1280x720/30FPS and192000samples independent decode.
Current inventory had no Studio/Godot/production job; Overseer no reservation,
ordinary optional availability question retained, only disposable window targeted,
no observed interference. Closed-item counter was corrected subsequently; no
pixel path change or false current-identity attribution.

Native90frame parity uses exact independent preview preencode RGBhash, declared
lossy pixels at first/last/caption boundaries, exact canonical mixhash, stereo
AAC correlation/RMS; rational NTSC and actual missing-codec/odd-size rejection.
Pipeline total median31.87420/p9536.33465/
max123.13010ms, 2over50; readback
median12.80435, videoencode10.96870.
Cold text draw94.785ms included; no export speedup/FPS/scanout guarantee. Raw
full samples/caller/source/font/codec/backend conditions retained in final packet.

Failures retained: initial inherited-control-stdin startup stalls; explicit
DEVNULL isolates child input and subsequent repeated real-owner exports proceed.
Windows read-only fsync failed; write-capable fsync corrected. Windows progress
read/replace sharing failed; advisory snapshots now bounded retry/retain previous,
completion remains strict. Auto-review rejected old-directory diagnostic rerun;
new destination retained old evidence. Qt harness timing assertion and reduced-
output text bounds caused failed tests, corrected with new runs; NTSC test source
range rejection was valid and fixture shortened. Actual encoder/write/cancel
faults preserve prior good files and same-owner recovery. No silent drops/caps
raising/history eviction/install/new worker/shared-guide edits/Git publication.
Final E requests existing Reviewer>=9 before F. FullEpisode04/real correction
sequence/full playback/listening/export/owner acceptance remain open.


## F progress and occupied owner window — 2026-10-14

E received existing Reviewer9.0PASS for4afe24fe...; report
work/reviewer-increment-E-final-20261014-01/REVIEW.md. F's recoverable E baseline
is increment-F/BASELINE.json. All source assets are protected copies; direct
shared owner/API assembly produced revision6,33Ready sources/9tracks/136clips/
102captions/52graphics/11781frames and327375byte portable project. Nine retained
commands completed; full canonical mix18,849,600samples peak.744019/safety1.0.
Original assets/master and supplied narration unchanged. Assembly and bounded
reference/voice preparation are evidence, not full stage acceptance.

Natural reference failure atframe2812 traced to fixed-demand forward walking from
prior65s to76.4s, exceeding existing512-plane bound rather than seeking. Project
get now enables existing interest-aware distant resync, legacydefault/512frames/
2seconds/budgets unchanged. Native60FPS six-target test reproduces old rejection
and verifies exact independent PTS/RGBA forward/back/repeat/cancel/cache/close.
Independent Reviewer confirmed it and portable assembly; earlyF remains unscored.
First reference harness leased error result then cleanup raised; primary and
secondary failures retained, finally-release corrected. Product export already
releases error snapshots correctly. Revised86native/reference samples allpass,
representative CPUmean.1450/p99=1/max4; cold randomseekmax1295.2324ms retained.
Approved original movie was copied/hashchecked for11visual comparisons; native
source/glyph/filter/codec differences are declared. Exact15ending/join clips and
expected spoken text retained; numeric availability is not listening/speech repair.

Native F disposable physical-1792018308726979100 accepted real narrationgain.85
revision7, then opened unchanged Trim dialog. Coordinating main reported Robert
actively testing Studio/audio. All actor inputs/playback/GPU checks stopped
immediately; no projectPlay/Export started. Own authenticatedAPI secured accepted7
to NEW interrupted-accepted-revision7.zwv with independent33Ready readback;
INTERRUPTION.json records action and stale captured Trim command binding. Cancel/
reopen it only after a coordinated free window. No user session stopped/replaced.
Main acknowledgement messaging failed AbsolutePathBuf routing; existing local
Overseer/Reviewer informed successfully. Original412unrelated/8Studio hashes still
matched on refresh; later owner edits must stay preserved.

Separate owner/API copy workflow passed all four full-episode edits, exact all
Undo/Redo states, stable IDs/counts, linkedsource alignment, stalebinding rejection
and managed Save/Close/Open with33Ready sources and normalexit0. NoGL/device
output/nativeinput; this supplements but does not replace unfinished physical
workflow. Remaining actualTrim/Move/caption/history/physicalSave-close-reopen/full
6m33s playback/sync/audio coexistence/reopened nativeExport/full+changedregion
comparison/finalsource and existingReviewer>=9 remain open. No F completion/score,
new worker/install/sharedguide change/staging/commit/push. Whole authorized scope
continues; only competing desktop/device work is deferred while owner is active.


F selected audio-reference check exposed the analogous large forward cursor
walk in NativeSource.read. Forward continuation now requires a<=2second gap;
otherwise existing indexed seek resets cache/decoder. No cap increase, PCM,
gain/curve/channel or source-file change. Old module snapshot reproduces1→75s
compressed music rejection; six targets match fresh-reader exact canonical
stereo bytes, cancellation adds no seek and actual cache budget closes0.
Independent Reviewer confirmed seek6 and Mixer9 at
work/reviewer-increment-F-audio-seek-20261014-01/REVIEW.md. Fresh-reader parity
is not independent resampling/listening. Twelve selected1second canonical/
approvedAAC excerpts correlate.998306–.999968 with differenceRMS.00061–.00439;
raw original/error and successful runs retained. This does not certify whole
AV sync or complete words. Current physical saved7 loaded OLD audio code;
normalclose/restart only the owned secured fixture after windowfree, then
repeat/rebind actual workflow. Foreground/audio/GPU work remains deferred for
Robert's live testing. Nonconflicting checks and exact source/evidence continue.


## F actual integrated result — 2026-10-14 PDT (supersedes occupied-window progress)

Recovered accepted7 on verified current source. Physical gain.80, linked trim92 /
move3 and caption em dash accepted as8–11; four native Undo/four Redo ended19,
with eight exact full-document comparisons, IDs/counts/source alignment preserved.
Native NEW Save As, normal GUI0/owner0/media-exited/protocol0, fresh native Open
matched the saved19 document exactly with33Ready sources. Owner demonstration
artistic settings were saved to a separate NEW JSON before close; no discard.
Original secured7, baseline6, source/assets/master and all failed runs remain.

Real continuous QtGPU/defaultWASAPI full392.7s playback completed without seeking,
1929paired200ms observations,393.633s observed wall interval, reported deadline
failures0. PCMpeak4,324,352bytes. Coarse clock/preview lagms median100/p95400/
p99900/max1333.333;74observations>500/9>1000. Statusgapmax992.488ms. Sampled output
max49.2825ms versus retained native max71.9403; sampledpadding2240 versus retained
2248. Audio prepmedian3.797/p956.930/p9910.987/max145.896ms(two>50). These are
distinct observation boundaries, not audible sync or FPS. End position11781 is
the exclusive project endpoint; the last encoded artwork frame is11780.

Robert answered exactly "was fine" to the full-playback cutoff-ending/bad-join/
picture-audio question(call_7cb3143ce4644569a3257b507774ff5e). This owner listening
feedback is scoped to that run, not per-word transcription or whole-stage approval.
All15endings/joins and32part provenance remain inspectable; no extra recorded tail
beyond supplied final endpoints was found. No regenerated speech/silent-word repair.

Native paused seeks2813and24 displayed correct distant/source/caption content,
then Stop released project audio (outputfalse,preparedblocks0). Actual native
Export Video used reopened19,1280×720/30CRF18/48kstereo at a NEW test destination.
Finished comparison pack: `increment-F\finished-comparison-1792029825872670500`. Full picture timestamps,
all authored canonical PCM and encoded AAC, selected native preview/encoded frames,
corrected-vs-original caption and exact240frame packet-remux sample are recorded.
Raw full-export stage timings and cleanup receipts bind cost/resources; final
candidate packet carries final hashes, tests/limits/rollback and Reviewer route.

Worst coarse live clusters: DU5220→5260 and PW7248→7288, both1080p~60FPS source /
entry-card boundaries. Existing reference5220 preparation872.859ms, total1123.087;
7241 preparation295.227,total549.109 are a separate random-sample protocol. Full
export stage costs at those recipes are separate from live delivery/scanout. The
original native fixture kept latest512 per-render samples, so early worst-region
per-render attribution is unavailable; raw whole-run clock/output logs survive.
Identical BG/FG source clocks are already deduplicated by asset/rate/intercept.
No speculative cap increase/resolution reduction/engine replacement was made.

The export worker and hidden comparison contexts/readers retired. The reopened
GUI15612/owner and idle preview context remain open on saved revision19 for review;
no second GUI exit is claimed. Current authenticated project state is clean,
stopped and has no pending operation statuses. The last recorded audio snapshot
reports outputfalse, retired preparation and zero prepared blocks; its original
timestamp/age and the still-writing unchanged-marker observation are preserved.
The current project API does not expose a fresh device-lease/internal-job count.
No active test uses the shared device/window; this does not certify every retained
GUI resource retired. Resource disclosure: `increment-F\quiescence-1792030080470257000`.

Independent A–E Reviewer9 progression approvals remain their source-bound evidence.
Final F AND whole-stage Reviewer verdict is a separate final review record; Robert
owns final acceptance and Git publication. Shared guides remain Overseer's. Candidate
is uncommitted/unstaged; no new worker/install/chroma/sampler/production overwrite.
