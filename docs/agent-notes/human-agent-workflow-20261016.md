# Human and agent editing workflow — October 16, 2026

Execution scope: the manually handed five-stage workflow assignment, continuing
from main `b38fca7d2f1e1f6a82d141cd80f6c87d36cc0371`. The editor-wide HOLD and all
historical performance/physical/listening gates remain separate. No publication,
installation, production rebuild or substitute worker is authorized.

Recoverable baseline and raw evidence:
`work/human-agent-workflow-20261016-1792188215954068500/BASELINE.json`, SHA256
`459970158f2c2a409ca875efe0a5a0920249d7e04250c7a2b7f9b496aab6065e`.
Its scoped application/native identity is
`a29e36310f59f41604241ab471b8c5a58275be941b0be2372acf3fd05f96fc87`
(355 app files/3 DLLs; different scope from historical asset-inclusive bundles).
504 files inventoried,502 copied;2 large assets hash-bound in place. All unrelated
skills, notes, research and assets are preserved. Episode8 saved revision264,
project hash `c13b6296ed47d8c97639b69b19fc67521812a030e6ecde250aff158cdaea10f6`,
and49 adjacent managed files are protected. The production run records `b7eaefd4…`
as the master video hash, rather than a JSON-receipt hash; both are preserved.
Episode8 content approval does not authorize publication.

## Stage 1 actual results

Baseline reproduction (`stage1/baseline-reproduction/RESULT.json`) decoded a
48,017-sample WAV with17 distinct final nonzero samples. Old Source ended at
30 frames/48,000 samples and omitted those17 samples. Strict model rejection of
float fades was also reproduced. This establishes the generated case, not every
codec/placement.

Implemented additive exact audio metadata and shared natural-end coverage in
`project_audio_timing.py`, used by `project_source.py` and
`studio_timeline_media.py`. Audio-only natural ends use explicit final-frame
silence; explicit earlier Out trims and video duration/padding stay unchanged.
Inspector converts only fade fields to integers; fractional properties and
strict model validation are retained.

Executed `project_audio_timing_test.py`:34 native/fallback PCM cases plus5
contract groups (`stage1/pcm-check-05/RESULT.json`):48 kHz boundaries and final
tail,44.1 kHz through separate declared resampler references,30/30000:1001/
24000:1001 FPS, nonzero In/start and half/double rates, Source/placement/full-
range cross-FPS agreement, intentional trim, split curve origins, strict integer
rejection, portable save/reopen and exact five-frame fractional-CFR video.

Executed `studio_project_audio_controls_test.py` through a new offscreen Qt
Studio and its actual owner (`stage1/qt-controls-03/RESULT.json`): fade typing
and unfocused wheel accepted integers, exact Undo/Redo, fractional gain/pan,
stale revision rejection, complete Source audition with explicit discard-test
output, portable media-hash/all-other-field equality and exact actual-owner
reopen. Owner exited0 and workers retired. This is synthetic Qt, not physical
input or a listening/device claim.

Existing `video_project_test.py`, `project_edits_test.py` and
`project_timeline_test.py` passed in
`stage1/existing-checks-1792188600417681200`. No broad stress/playback matrix run.

Failures retained: pcm-check-01 caught the new helper's wrong default rational
pair type (fixed); pcm-check-02 used a wrong split request field (test fixed);
qt-controls-01 used exact equality for binary fractional pan (tolerance fixed);
qt-controls-02 incorrectly compared portable relocated paths literally (hash/
semantic comparison plus actual-owner reopen fixed). Later focused runs are
separate evidence; the failures are not erased.

One12-second proof now exists at `proof/Workflow-proof.zwv` with original
narration and an editable caption. It will be extended through the remaining
stages. It is not yet the complete assembly/export demonstration. Saved retry
copies and managed media remain. Stage1 independent review is pending; no
dependent progression is claimed before its explicit source-bound >=9/10 pass.


## Stage1 independent verdict / Stage2 actual results

Existing Reviewer returned explicit9.0/10 PASS at
`work/reviewer-human-agent-workflow-20261016/stage1/REVIEW.md`, bound to
`7a15f4a325837db92cefd2122db42b536bdaa781b98b23bd81e07d29de814f1b`.
Its independent34PCM-case run passed. This permits Stage2 only; editor-wide HOLD
and Robert acceptance/publication remain separate. Historical pending wording
above describes the earlier handoff, not a current missing Stage1 verdict.

Stage2 uses the existing preparation pool, admission/reservation checks, document
validation/commit/history, authenticated/control routes and save. New files:
project_import.py,studio_project_import.py and their two focused standalone tests.
Existing scoped callers: project_service,studio_project,studio_project_source,
studio_timeline_media,studio_control_service. Full exact paths/hashes are in the
Stage2 candidate MANIFEST; baseline recovery remains unchanged.

`stage2/import-01/RESULT.json`:7groups pass with real hash/type preparation:
Video/Audio/Image+duplicate gives3accepted/1skipped, exact input order/provenance
and no clips; Ready reuse/no duplicate history, exact Undo/Redo, corrupt and
unsupported atomic rejection, changed recorded identity rejection, controlled
slow preparation/cancel preserving prior work, existing16-job/128-file bounds,
one latest progress snapshot,4-row summaries and portable save/reopen. Small
real preparation took1.434s;516owner poll samples median.0193ms,p95.0382ms,
max24.985ms. This is not device/foreground responsiveness.

`stage2/qt-import-03/RESULT.json`:4groups pass through isolated offscreen Qt and
the actual Studio owner: mixed chooser5inputs→4added/1skipped, all5per-file
results, nonmodal details, exact Undo/Redo, existing Library2-file import without
project mutation, still default5/1.25s→37frames/2.5s→75frames and independence,
normal portable Save/reopen. Same12s proof advanced to revision17 with5references,
original narration/caption retained. Test placements were removed by owner Undo
so later stages extend this same proof. Owner0/workers retired. Import-to-display
was.969s. Whole-test processEvents samples (startup/preview included) median.474ms,
p9520.419ms,max585.756ms,4over100ms: these outliers remain, without attributing
them to import or claiming an interface latency guarantee. No physical picker,
foreground/native-input,device/listening claim.

Qt failed runs01/02 are retained. Their assertion exposed that the existing
control transport summarized the queried outcome to4rows: owner had accepted
all inputs, but details could not show the fifth. Explicit read-only import
status now returns the complete bounded list separately; periodic publications
stay compact. Details uses show(), avoiding QDialog.open()'s modal behavior.
No accepted work was lost; failed test owners discarded only their task work.

Existing owner/API test passed (55.3s), including ordered/replay/stale/auth,
pressure/failure/recovery/pinned saves and cleanup. Natural audio timing suite
passed34PCM cases/5groups after Placement changed. Existing timeline synthetic
vertical linked-track move failed twice; baseline/candidate comparison is retained
separately and must be evaluated, not silently called passed. A media-lane test
invocation omitted its required fixture argument and did not execute its checks;
that invocation is retained as a harness error. No broad playback qualification
is claimed. Stage2 review remains pending until its explicit source-bound pass.


Stage2 final follow-up: `import-02` passes all7groups with the test's recovery
store explicitly isolated. `media-lanes-corrected` passes5native decoder ownership/
pressure/cancel/cleanup groups using its required existing generated F1 fixture.
The original argument error remains. `timeline-comparison-1792189654017966300`
runs unchanged gesture/assertion semantics against captured baseline source and
current candidate, each with separate owner/session/output: both reject the same
vertical linked move because a companion lacks a compatible destination track.
Both exit1 and preserve documents. This is an existing synthetic contract/test
mismatch, outside the import correction; not a regression pass or reopened
physical timeline acceptance. Whole editor HOLD remains.


Before Stage2 verdict, the existing studio_project_test.py import step was
maintained: its obsolete single-file chooser/Type-modal expectation now uses
the actual mixed chooser. All downstream assertions remain. Its full existing
Qt/owner workflow passed in20.382s at
`stage2/existing-checks-1792189892808496300`: import/place/trim/volume/move,
caption editing/scoped keyboard history, space activation, portable Save As/
Close/Open, controlled close-save failure, same-owner Save As recovery and
normal cleanup. No application code changed after the first Stage2 seal. The
Reviewer was notified before this test/note delta and will bind the final seal.


## Stage2 verdict and Stage3 actual results (2026-10-16)

Reviewer returned explicit9.0/10 Stage2 PASS for72b296fef3c698b3e8e8109f0dbaf703d649f17736c19e3179593f9e3f7eb7bd.
Later native checking found the approved workspace's blanket QPushButton hide loop
also hid Import Details/Cancel. Reviewer acknowledged this missed visibility gap
in its preserved VISIBILITY_FOLLOWUP.md. A narrow descendant exception now retains
those controls; Stage3 review includes this follow-up. Historical Stage2 evidence
does not itself establish the corrected active layout.

New helper/planner/CLI and two standalone tests use the existing authenticated
owner. No API server, document mirror, extra worker or production authoring.
`stage3/api-04/RESULT.json`:17 focused real-owner/API groups PASS, with disclosed
controlled transport/delay/retired-result supplements. Includes exact saved-plan
CLI Apply/Resume, source-change-after-plan refusal, manual conflict/guarded setter,
actual128+2 chunking, test-only1600-byte splitting plus literal524288/524289 wire
sizing, natural audio, full envelope/routing, partial completion/Ready reuse,
lost replies before/after acceptance, stale four clocks, exact Undo/Redo,
failed-write protection/same-owner new checkpoint and clean owner0. Journals are
token-free and capped8MiB. See test result for exact classifications, not a broad
physical/performance certificate. api01 test name collision and api02 CLI missing
audio-module path are retained; fixed before final api04. api03 passed16 groups
before the added changed-source check. No erased failed evidence.

`stage3/qt-helper-01/RESULT.json`:4 offscreen synthetic Qt/actual-owner groups PASS.
The SAME12-second proof gained two shots, explicit2s still, independent music with
six-point envelope, five named tracks and Music bus using5Ready references. Existing
narration/caption retained. Qt manually edits music/caption with exact Undo/Redo;
normal portable save/actual-owner reopen preserves entities/hashes and1920x1080
CPU preview. Visibility assertions pass in the active Editing layout. This is
synthetic Qt, not native typing/listening/GPU qualification.

`stage3/caption-stack-1792191198992492400`: proof-only authoring correction via
normal guarded track.move puts seeded captions above newly added picture. Exact
Undo/Redo and matched one-frame CPU before/after show only caption-bound pixels
change; clips/caption/media data exact. No compositor change or production edit.

Native attempts retained: native-1792190750266094800 actually imported/reused a
source and opened Details, but a subsequent Windows picker could not be activated.
User closed that disposable window; recorded PIDs later absent (no invented normal
exit receipt). native-1792191215511952200 Qt picker input timed out; cooperative
fixture cleanup exited0. native-1792191357538025400 uses a DISCLOSED fixed generated
file chooser fixture, not a file-picker pass. Actual native Import, visible/painted
Details and enabled Cancel during queued preparation were observed. Actual Cancel
then real owner cancellation accepted no new reference; prior document retained.
Actual Details showed full path/cancel outcome. Normal native Close exited0 and
workers retired, final document digest and saved proof hash identical to initial.
READY/EVENTS/CONTROL/RESULT bind these observations; Computer Use inline captures
are separate from the saved OFFSCREEN-SYNTHETIC image.

Automatic approval review rejected native caption typing: accessibility reported
Narration name focus while the screenshot showed the caption caret. No bypass or
wrong-field text was submitted. That native input check remains UNVERIFIED;
synthetic Qt editing passes separately. No physical OLE/device/listening/scanout
or broad editor acceptance is claimed. All disposable windows are now closed.
Proof revision30 retains all accepted work; Stage3 needs explicit source-bound
>=9/10 Reviewer PASS before dependent recipe implementation. Editor-wide HOLD and
Robert acceptance/publication remain separate. Stage4/5 not yet claimed complete.


## Stage3 verdict / Stage4 actual results (2026-10-16)

Existing Reviewer returned explicit9.0/10 Stage3 PASS for099902fdbfccfc6bedd8ffd44d70f539ddb03ba701b4771b7c179d3c64a4140f,
with an independent17-group real owner/API/CLI pass. It explicitly closed the
tested Stage2 hide-loop visibility follow-up, retaining native picker/caption
typing limitations and overall editor HOLD. This authorized Stage4 progression.

New project_recipes.py and two standalone tests implement six version1 recipe
families through the existing helper. project_manifest validates ordinary text
keys, then expands them into existing keyframe.set commands in the same entity
unit. No model/API/Qt layout/compositor/audio owner was replaced. Recipe parameters
and limits are explicit; current named batches, exact journals and conflicts remain.

stage4/recipes-02:7 real-owner groups PASS. Two variants of ALL six kinds create
ordinary IDs/provenance/styles/layouts/opacity keys/dynamic ranges/full envelopes/
source/still durations. Exact named UndoRedo, independent manual overrides,
read-only reapply conflict, historical resume/current_matches=false, preserved
normal trim origins, unsupported parameters and actual portable close/reopen all
pass. recipes-01 is retained: test used unsupported `captions` track kind instead
of the existing graphics kind; fixture corrected, no model weakening.

stage4/qt-recipes-02:5 synthetic Qt/actual-owner groups PASS. SAME proof extended to
revision39:8graphics and1new caption (15timeline items total),two entrances,review
card,timer/progress,existing5clips/5media/original caption exact. Existing inline
title text and full6-point music envelope table remain editable,variantB/narrator
independent,exact UndoRedo. Normal portable save/actual-owner reopen preserves all
IDs,styles/keys/ranges/provenance/audio arrays/media hashes. Owner0/workers retired.
qt-recipes-01 retained: Builder supplied a wrong timestamped manifest path; failed
before helper submission and closed its isolated owner. Correct recorded path used
for02. No accepted artwork was discarded to recover a test.

stage4/helper-regression-01 re-ran all17 Stage3 real-owner/API/CLI groups PASS after
expansion changed. Existing source/capacity/auth/history/recovery boundaries stay.
stage4/reference-frames-1792192645800295400 contains3native-resolution1920x1080 CPU
reference frames (45,210,300) of the same saved proof; inspected45/300 show readable
separate title/card/timer/progress/caption over original sources. No native export
or GPU/device/physical-input/listening/scanout qualification. Offscreen image is
explicitly synthetic; historical native input gaps remain. One short native export
is reserved for Stage5. Stage4 now needs explicit source-bound >=9/10 review.


## Stage4 verdict / Stage5 actual results (2026-10-16)

Existing Reviewer returned explicit9.0/10 Stage4 PASS foraa9ff124c0b74bbec53c132be2528b8cb9cbb9cf8fba045154ff468c748f56e2,
independently passing all7recipe groups and inspecting the proof/CPU captures.
This authorized Stage5 only; the overall editor/HID/audio/A-V HOLD remains.

Natural existing waveform baseline: same240s WAV,1300pixel fit,30fps:32two-second
jobs cover only64s,176s absent,in4.479s. At400pixels it queues none. Raw samples,
native/source hashes and counters retained under stage5/baseline-1792192748701415800.
The first baseline run's metrics object was later mutated by cleanup,so the second
retains pre-cleanup counters. Generated odd-sample pulses at2x are all missed by
old output-rate-thinned decoration; rate-baseline-1792192799667230800 proves actual
source peak.75/display0. A preceding harness-only duplicate-op failure is retained.

New timeline_waveform and narrow timeline_decorations/studio_timeline changes
produce complete incremental coarse coverage with honest pending/error/silence,
lazy visible refinement,raw pre-gain semantics and strict existing budgets. No
audio/renderer/native/DLL or document policy change. stage5/wave-03 passes8groups:
all11,520,000source samples across240s scanned,actual painted beginning/middle/end,
238–240s zoom,native/fallback2x transients,half-rate/nonzero/fractional In,source
generation stale-result rejection,actual hash failure,real progressing cancellation,
synthetic32pending/128entry/8MiB pressure and owner-thread cleanup. Earlier wave01/02
passes remain;03 adds explicit running-after-partial cancellation and scoped raw
timing. None uses long playback/export. Captures are offscreen Qt,not scanout.

Full overview10.191s;first progress0.576s.
6446overview processEvents samples:median0.0376ms,
p950.1992,p992.6483,max3.4288;
190actual paints:median2.034ms,p952.971,
max6.490;zero over20ms in these scoped samples. First
worker slice573.203ms remains an outlier (not a GUI timer).
Cache5,120B,reader/cache/scratch peak4,292,608B of32MiB,one pending in this case.
Close during a running generation after2048samples published took
4.219ms;readers/budget/thread retired. This does not establish
opaque codec/whole-process plateau or universal cancellation/UI performance.
Coverage differs from baseline,so10.19s full240s versus4.48s first64s is NOT a matched
completed-work speedup. Conditions/raw counts/limits are in TIMING_AND_RESOURCE_RESULTS.

SAME proof portable Save As/reopen is stage5/integrated-01/Workflow-proof-portable.zwv,
revision39,hash4d9817109fed036733826223905fa833d5d875df44fdfaa42049accb7ca7a8f0.
All IDs/5media/5clips/2captions/8graphics/5tracks/music bus,styles/keys/ranges/arrays
and original hashes persist. The current final manifest read-only plan recognizes
all entities and only normal Save remains. No direct .zwv writes behind an owner.

Exactly ONE native1080p30H264/AAC12s export:360frames/576000samples,RTX3070nativeGL,
worker27.089s,owner-wait-through-close31.411s. Movie hashf185d8d84267feb4f6bd3fffb590bf7fe376e2d9739f3252ab569f4ee7e0ec8a.
Verify mode reused the completed movie,never re-exported. Exact raw original48017
samples including17tail samples,then1583final-frame silence,native/fallback agree.
Independent full authored canonical mix SHA matches export receipt exactly.
AAC priming packet-1024/48000 is decoded from0 with continuous timestamps and0
final padding;RMS0.000160092,channel correlation>0.99998579.
Eight decoded checkpoints across all boundaries match CPU references under declared
lossy tolerances. Max pixel errors remain in JSON,not called exact encoded pixels.
Source/human agreement and separate44.1kHz resampler references reuse unchanged
Stage1 evidence. No listening or physical one-frame A/V correlation was measured.

Current native window native-1792193495309542300: actual waveform/thumbnails visible;
View/Panels/Project data/Titles and dock resize exposed individual title rows,then
actual Edit opened the ordinary title dialog. Computer Use could not activate the
modal for Escape; no typing or content change was submitted. Its cooperative Qt
fixture cleanup rejected the dialog and closed normally (not a physical Cancel/
Close pass);owner0/workers retired,document and portable file hashes exact. Stage3
auto-review-rejected inline caption typing remains UNVERIFIED,no bypass. Only
owned disposable layouts/logs used,no playback or production window taken over.

Existing studio_project_test.py passes its full6-group Qt/owner workflow in18.978s
after the shared timeline change (stage5/existing-checks-1792193695639104300).
Earlier model/owner/recipe/import/audio-tail evidence is reused with its source
bindings,not mislabeled as a new broad matrix. Historical linked vertical-move
synthetic mismatch remains open from the paired baseline/candidate Stage2 evidence.
No prior failure is erased. Stage5 is now submitted for source-bound >=9/10 review;
its external verdict determines narrow workflow completion,not Robert acceptance.
