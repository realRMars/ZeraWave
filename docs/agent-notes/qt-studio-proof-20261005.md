# Qt Studio proof — focused presentation polish, 2026-10-05

Bounded follow-up to independently reviewed whole-task patch
`b1a70e59a604c7d45605759c17fe813ea2eee6f396fd8664fc359cc706858ad6`.
Only `studio_qt.py` and this note change. Source/delta/evidence are bound in
`work/qt-studio-proof/polish-03/review-index.json`. No score or acceptance is
assigned here; return this candidate for independent review.

The canonical JPG was pixel-inspected again and preserved. Its typography and
copper/cyan hierarchy guided a narrow polish: brand at the left of the header,
aligned File/Edit/View/Help, a stronger copper scene heading and right-aligned
quality caption, consistent semibold tabs, copper Save Authored/BONK, cyan Start,
and clean two-tone pigment tiles without the previous border corner artifacts.
No scene, catalog, artistic values, renderer quality or control destinations change.
An initial Qt corner-widget route covered File; the final header uses a normal
Qt layout with a QMenuBar, visibly restoring all four menus. The initial failed
capture is retained under `polish-03/probe`; final source-bound captures are
`polish-03/probe-02/default.png`, `compact.png`, `compact-colors.png`, and
`compact-advanced.png` under `work/qt-studio-proof`.

Routine active-color explanatory text is replaced with actual Ready/Starting,
Running, Held or Paused transport state (from current telemetry) plus source;
the compact pigment status retains the next-preview editing boundary. Full
original explanations remain in tooltips and keyboard-accessible F1 help.
Other statuses, inactive dependencies and errors retain their existing text.
The status bar reads `Qt proof • F1 help`; error and save messages still replace
it explicitly. The reviewed layout behavior and all controls remain intact.

The final actual-renderer probe at 1600×980 and 1280×800 passed the retained
legibility assertions: zero QScrollArea horizontal overflow, five primary
response rows within their viewport, analyzer height >=130 and monitor >=190.
Final screenshots were pixel-inspected. Supervisor exit 0, no timeout, zero
owned descendants and unchanged application source during capture. Expanded
Advanced retains vertical scrolling. This evidence verifies geometry, not
physical mouse/keyboard actuation or docking gesture quality.

The 13-check correction regression passed on final source. The original Qt
standalone regression passed before the final header-container correction;
business/control code did not change afterward. Evidence-only test copies
redirect outputs into `polish-03`, preserving prior frozen review artifacts.
`git diff --check` passed. No performance campaign or new performance claim:
the earlier explicitly seeded, uncontrolled comparison remains bound to its
earlier source and shows additional Qt GUI/owner cost as recorded below.

Physical drag/drop/feedback, natural keyboard, actual DPI/monitor changes and
complete reproduction of the historical error sequence remain unverified;
the supported interaction runner is unavailable. API/capture polish does not
close these gaps. User hands-on review or a supported runner is still needed.
The supporting reference remains absent and uninspected. No commit, push,
release, shared-plan edit or full migration. Launch `run_qt_studio.vbs`, use
View > Reset Layout for the authored defaults, rollback `run_unified_studio.vbs`.
Stop for bounded review.

---

# Previous layout legibility re-review, 2026-10-05 (historical)

This bounded pass follows Bob's independent re-review of patch `fb79072ac7c36b02ce03914dd4d04e7fcad20cbbebacf80b8087d97f7a07cb67`.
Only `studio_qt.py` and this task note change from that reviewed checkpoint.
Exact source/delta/evidence are in `work/qt-studio-proof/layout-02/review-index.json`.
No acceptance score is assigned here; the original 9/10 target remains for review.

## Visible result and review

The authored default gives the right column 400 px, reserves enough height for
the Mapping Monitor and analyzer, and uses two-column pigments. Five response
rows use compact 34 px knobs plus numeric entry. All existing frequency-window
fields and custom-window onset sensitivity remain in a working collapsible
Advanced group with vertical scrolling. Save Authored has a compact action
label; the selected form/target, author status, destination tooltip/accessibility
name and the action's full original destination tooltip remain available.
Transport uses two rows. All twelve measured band edges use alternating label
baselines and k-Hz abbreviations, with units explained by the analyzer tooltip.
No additional measured bands or invented data were introduced.

At widths below 1450 px, the authored Reset Layout groups Color Inspector and
Audio Tuning into tabs above Mapping Monitor. Existing customized saved layouts
are preserved, not automatically rearranged. Use View > Reset Layout to review
the new authored arrangement; resizing a user arrangement alone does not apply
these defaults. This is a deliberate compact composition, not removed controls.
The World Library title is shorter; actual catalog taxonomy is unchanged.

Final pixel-inspected captures: `layout-02/probe-04/default.png` (1600×980),
`compact.png`, `compact-colors.png`, and `compact-advanced.png` (1280×800), relative
to `work/qt-studio-proof`. Actual decoded Tidal Strata output remains dominant:
preview client 937×604 at the default size and 648×425 at compact size (exact
geometry in the receipt). The available five mapping submission rows and all
twelve band labels are visible. The primary five tuning rows fit without
scrolling; expanded Advanced uses deliberate vertical scrolling. No horizontal
scrolling was present in the final layout assertions. More pigment roles may
require vertical scrolling within their panel; no role is removed.

## Focused evidence and limits

The final probe asserts analyzer height >=130, monitor height >=190, zero
horizontal overflow in every QScrollArea, and that each response row lies fully
inside its tuning viewport at both sizes. It also opens the compact Color and
Advanced tabs for screenshots. Supervisor: exit 0, no timeout, zero owned
descendants and source unchanged through capture. This is actual renderer/API
layout evidence, not physical gestures. Earlier probe captures are preserved
to show the clipped states refined during the pass.

Both `studio_qt_test.py` and the 13-check `studio_qt_corrections_test.py` passed
after the final source change. Evidence-only copies redirect their screenshot/
JSON destinations into `layout-02`, preserving frozen prior review artifacts;
they import the actual production source. No service/renderer/audio changes or
broad performance campaign occurred. `git diff --check` passed.

The previous seeded comparison remains historical evidence on its bound source:
Qt GUI+owner 3.61 CPU seconds/12.39 wall seconds versus Tk 1.64/12.07, end working
sets about 254/84 MB; renderer CPU 3.104/2.730 ms and presentation 17.038/16.900 ms.
It is one uncontrolled run, not a current-source performance pass, causal FPS
regression, GPU draw measurement or long-session guarantee. No new benchmark
was required for this layout correction. Physical docking/keyboard gestures,
real monitor/DPI changes and the absent supporting reference remain explicit
gaps. Existing dependency/license, rollback and full migration inventory below
still apply. Launch `run_qt_studio.vbs`; rollback `run_unified_studio.vbs`.
No commit, push, release or shared-plan edit. Stop for bounded independent review.

---

# Previous correction review checkpoint, 2026-10-05 (historical)

This checkpoint supersedes the earlier review result below. It is ready for Bob's
bounded re-review and Robert's proof review, not full migration or acceptance.
HEAD remains `4a4f6e03ad2119e790e88d8338bac9412a139881`; correction baseline is
the reviewed task patch `939f3128ef2539998117119d789acd1361fac7e06993a7eb094497fe1e7b781b`.
Exact final files, correction-only/whole-task patches and evidence hashes are in
`work/qt-studio-proof/corrections-01/review-index.json`.

## Corrections and review steps

Tuning-only edits now count as dirty. Close offers Save, Discard and Cancel;
canceling Save's picker also leaves the window and drafts intact. Saved sessions
carry `qt_tuning_drafts` with original destination metadata and settings, separate
from Save Authored. Loading does not submit old-run edits: compatible drafts must
be explicitly restored into the current bound destination. At most 256 destinations
are retained; exceeding that bound fails before modifying another destination.
The previous Tk presentation does not expose this Qt session extension; use Qt
to review and restore these drafts. Existing authored profiles are unchanged.

The authored default docking state is captured before saved layout restoration.
Reopening a customized layout and Reset Layout now restore that default without
changing artistic values. QColorDialog starts from the resolved role pigment and
commits only to its captured target. Larger swatches, compact headers, a dominant
full-size native preview, and labeled read-only Input/CPU submitted mapping meters
replace the cramped presentation/raw mapping text. Submitted values are not
verified GPU output. Native sizing corrects an observed Qt foreign-window offset
within the existing Qt parent; no renderer context or quality replacement occurs.
Focus/scope changes cancel held controls; floating geometry recovery clamps to
available screens and reacts to screen changes, without resetting artistic state.

Launch `run_qt_studio.vbs`; rollback `run_unified_studio.vbs`. Review tuning-only
close choices, Save/load/explicit restore, custom layout reopen/Reset, pigment
dialog initial color and the Mapping Monitor. Screenshots:
`corrections-01/interaction-06/form41.png`, `form42.png`, `form43.png` under the
task evidence directory. They show actual child renderer output, not a mockup.
The canonical reference was pixel-inspected and preserved. The supporting image
is still absent and was not inspected. Full migration inventory and dependency/
license/architecture records remain in the earlier checkpoint below.

## Checks and limits

Final focused runs passed: `studio_qt_test.py`, `studio_qt_corrections_test.py`
(13 checks in `cpu-result.json`), `audio_scope_test.py` (120 checks), and
`preview_playback_test.py`. Direct Qt events/API calls are not OS gestures.
`interaction-06` passed real renderer start, fine-step tuning ACK, color ACK,
Hold ACK, explicit focus-event release, API float/redock/reset continuity,
wrong-run rejection with meaningful nonmodal error, Stop and close for Tidal
Strata, Recursive Atrium and Honeycomb Garden. Each held renderer retained its
PID/HWND/context/program through layout operations. Its supervisor recorded
exit 0, no timeout and zero owned descendants after cleanup. The injected wrong-
run path exercises recovery; it does not reproduce every historical modal storm.

Physical drag-out/back/ghost/target highlighting, natural OS keyboard interaction
and actual monitor/DPI changes remain unverified: the required supported Windows
interaction runner is unavailable. API recovery/arrangement tests do not close
those evidence gaps. No additional runner or alternate input injection was installed.
Failures are preserved in interaction-01 through -05: early direct-focus/subsecond
ACK assertions failed; the final harness uses bounded ACK waits and explicit Qt
focus events. Interaction-05's final error assertion checked UI state before the
snapshot refresh; -06 calls the normal UI error handler. Early CPU harness failures
were an incorrect ADS method, an incorrect loaded-draft dirty expectation and a
disabled offline numeric test fixture. No physical latency guarantee follows.

## Final bounded comparison — supersedes previous unmatched-seed claim

Withdraw the earlier comparison's claimed seed matching: those seeds differed.
`matched-final-result.json` binds the replacement sequential Qt/Tk runs with
seed 7301, the same decoded Balloon.wav from its beginning (SHA recorded),
form 41, equal artistic values, fresh renderer startup/reset, stationary layout,
actual 800×450 framebuffer/viewport/internal/shader size and render_scale 1.
No adaptive quality reduction. Warm GUI counters cover GUI and control owner,
excluding startup, renderer and launcher stubs. Qt used 3.609375 CPU seconds in
12.3924 wall seconds (GUI .6875 + owner 2.921875), versus Tk 1.640625 in 12.0703.
End working sets were Qt GUI 172,343,296 + owner 81,661,952 bytes versus Tk
84,316,160 bytes. Qt's separate owner increases presentation cost substantially.

Renderer Python-call means were Qt 3.104 ms / Tk 2.730 ms; swap-return interval
means 17.038 / 16.900 ms, p95 22.2 / 20.7 ms. Each included one early >50 ms
interval (285.1 / 201.8 ms), so these report-wide tails include startup effects.
789 / 753 renderer samples were recorded. GPU draw and scanout were unavailable;
GPU/VRAM counters are device-wide. GUI contents differ, thermal/background/power
conditions are uncontrolled, monitor metadata was not bound, and no repeated-run
distribution, continuous listening or long-session stability is established.
Both final supervisors recorded exit 0, zero owned descendants and unchanged
application source. Earlier malformed capture/interim runs remain preserved.

No commit, push, release, shared-plan edit, reviewer dispatch or acceptance score.
The correction phase ends here for proof review; physical interaction evidence
and the supporting reference remain explicit gaps.

---

# Earlier separated-owner review checkpoint, 2026-10-05 (historical)

The Qt proof now launches and hosts the actual renderer. This is a functional,
bounded presentation proof, **not the full migration, a 9/10 certificate, or
Robert's acceptance**. Physical drag feedback/redrop and monitor/DPI changes
remain unverified. The missing supporting image remains an external blocker.
The earlier failed checkpoint is preserved below as history.

## Launch and architecture

Double-click `run_qt_studio.vbs`, or run
`.venv\Scripts\python.exe -B -X utf8 app\visuals\studio_qt.py`.
Rollback: `run_unified_studio.vbs`. Neither launcher replaces the other.
Layout is `work/studio/qt-layout.json`; Reset Layout affects only presentation.
Diagnostics are available through Help/View and `work/studio/qt-*.log` plus
separate owner/bootstrap logs. Default input is synthetic; Preview setup can
select existing Test track or live input. Built-in tree selection never opens
a session file picker; File > Open session is separate.

Qt Widgets + ADS own presentation and the foreign-window container. The new
`studio_control_service.py` process creates the withdrawn legacy Studio and
owns existing session, tuning, palette, profile storage, command transport and
ACK callbacks. `studio_control_client.py` presents read-only snapshots and
explicit destination-bound commands. No Tk interpreter is created in Qt.
The unchanged GLFW/ModernGL child owns rendering, graphics resources, musical
clocks and scene history. No frame copying or quality reduction was introduced.
One Windows job owns the control service and its renderer descendants;
EOF/normal close and forced cleanup are bounded. Commands cap at 32 queued,
64 KiB each; snapshots cap at 512 KiB and publish at 5 Hz; histories are bounded.
Numeric requests are synchronous, so measured command latency can affect feel.

The earlier same-thread Tk/Qt failure is bypassed by Robert's explicitly
approved process separation. It is not attributed to an unavoidable Qt/GLFW
limitation: the isolated Qt-only probe and the integrated separated owner pass.
All earlier failure logs and receipts are retained.

## Scope actually implemented

Styled charcoal/copper/cyan ADS shell; real catalog hierarchy; dominant native
preview; Color Inspector; Pin/Follow and live-override ON/OFF controls; form and
target selection; destination-bound knobs/numeric entries with ranges/precision,
knob/slider context menus and per-parameter authored reset; collapsible Advanced
windows; explicit Save Authored destination; transport; genuine twelve-band
telemetry presentations; real decoded PCM waveform; read-only CPU mapping
packet monitor; diagnostics; checked View recovery; independent layout storage;
ADS splits/tab groups/floating containers; per-panel title-bar help and F1.
No destination dropdown is used. Keyboard transport excludes text/numeric entry;
focus/application changes cancel held controls.

Pending full migration: full palette-family/preset/gradient UI, profile dialogs,
audition/transition controls, complete effect/layer/experimental/review views,
complete catalog search and archived thumbnail presentation, comprehensive
shortcut/tuning gestures, and finished compact Input/Applied meter presentation.
Current Mapping Monitor is bounded packet text with explicit CPU-submission
labeling, not verified GPU output. Existing twelve-band bars are not interpolated
into fictitious frequency resolution. Synthetic preview has no analyzer data
and is labeled unavailable; no fake waveform animates.

## Checks and evidence

HEAD remains `4a4f6e03ad2119e790e88d8338bac9412a139881`; the dirty baseline was
preserved. Final task delta/hashes and preservation checks are in
`work/qt-studio-proof/process-separation-01/review-index.json` and
`task-only.patch`. Starting whole-task manifest is the original
`work/qt-studio-proof/baseline.json`; continuation manifest is the same-name
file in `process-separation-01`. No commit, push, release, frozen-portable,
shared-plan edit or worker/reviewer dispatch occurred.

Focused `studio_qt_test.py` passed after the compact-control/title-bar-help
change: real Qt widgets, repeated nine-panel API layouts, API float/redock,
layout-only reset/persistence data, unknown color target rejection, wrong-run
and wrong-destination tuning rejection, numeric presentation preferences,
nonmodal recoverable error reporting and normal close. These are API checks,
not physical mouse drags. Existing `audio_scope_test.py` passed 120 endpoint
cases, run/session/revision/delayed-save isolation; existing
`studio_workspace_test.py` passed native Tk panel/lifecycle/preservation checks.
`git diff --check` passed, with existing line-ending warnings only.

`integrated-01` passed full-quality synthetic renderer start/float/redock/reset/
close. `decoded-01`, `final-decoded-01`, and `review-decoded-01` passed actual
silent decoded Balloon.wav replay and native hosting. External watchdogs
record host exit 0, no timeout, zero remaining owned processes, and matching
before/after source hashes. Their scripts, prelaunch manifests, logs and result
JSONs are retained. Faulthandler's periodic 15-second stack capture in the
longer successful probes is a diagnostic timer, not a watchdog failure.

`final-decoded-01` records repeated native identities across layout operations:
PID 30880, HWND 15142906, context 131072, renderer 2806917048912,
parameters 2806917053616 and program 2806920584832 remain constant; flow clock
advances 0.0697 to 19.6978 seconds. This is continuity of owned resources and
clock telemetry, not AV listening or a multi-hour stability claim.

`review-decoded-01` additionally sends live override + bass_response=1.15;
real renderer effective values acknowledge 1.15, and the existing Save Authored
callback writes a target/revision-bound profile to its isolated test directory.
Production authored files are preserved. The test-only environment redirect is
absent in the normal launcher. ACK round trips: override 27.2 ms, edit 86.7 ms,
Save Authored 32.8 ms in that run. Other selection requests reached roughly
100–333 ms. A failure snapshot is displayed once with its diagnostics path;
service exceptions are retained, not replaced by repeated hidden modal dialogs.

Comparable screenshot: `review-decoded-01/renderer.png` (actual Windows capture,
1600×980 shell, deliberately fixed 800×450 full-quality preview, edited test
bass response). Earlier captures are source-bound to their own prelaunch
manifests. Canonical `images/Bobs Mock up.jpg` pixels were inspected and file
preserved. Supporting `ZeraphinaX_Studio_Bob_Concept_02.png` is still absent and
has never been visually inspected here. No rejected transfer was retried.

## Matched short performance comparison

Existing Tk arm: `tk-matched-01`; Qt arm: `decoded-01`, renderer performance
report originally `work/studio/20261005-083320-513107300/session-performance.json`
(copied to this evidence directory). Both use identical saved values (comparison
found no differences), held form 41, Balloon.wav from zero, Real time, authored
colors/profiles, fresh renderer/history and full-quality 800×450 actual framebuffer,
internal size and shader resolution. Each holds about 12 seconds after ready.
No scene-density/material simplification. Default cosmic seed is 7301; random
director initialization was not separately overridden, but this held form does
not use director scene selection. Thermals/background processes are uncontrolled.
Qt arm includes API float/redock/reset operations; Tk arm remains stationary,
so this is not a causal GUI-overhead benchmark.

Tk/Qt renderer CPU-call means: 2.7508 / 2.7532 ms; p95 4.2 / 4.2 ms.
Swap-return interval means: 17.0813 / 17.0051 ms; p95 21.2 / 21.1 ms;
maxima 242.9 / 205.2 ms; both record two >50 ms intervals. GPU is RTX 3070 Laptop.
These are Python/driver render calls and between-swap-return intervals, not GPU
query time or scanout. GPU utilization/VRAM are device-wide; process VRAM and GPU
draw time unavailable. The Qt UI refresh sample mean in `final-decoded-01` is
10.59 ms, maximum 250.50 ms, including refresh/initial waveform work; Qt process
CPU 3.609 s over the roughly 17 s probe. This excludes separate owner CPU, so it
must not be compared as total GUI CPU against Tk's 4.281 s. Existing historical
empty-GUI numbers below predate separation and do not describe the current total.

## Remaining review gaps

No physical docking-gesture receipt: the supplied computer-use catalog exposes
no node_repl/Windows interaction runner. ADS drag configuration is implemented,
but ghost visibility, target highlighting and release placement require a bounded
owned-window interaction review. API movement is not a substitute. Real DPI/
monitor changes, comprehensive keyboard-held gestures, forced owner disconnect
with unsaved pending edits, live color ACK tests, and actual renderer start/stop
for all child forms were not executed in this pass. Normal Fractal selection,
Tidal Strata start/stop and close work; the historical intermittent error was not
reproduced with a bound original failing log, so no definitive original root
cause is asserted. The stale inspector selection repair and nonmodal owner errors
address identified failure paths. No 9/10 score or artistic acceptance is claimed.
Stop here for Robert/Bob's proof review; do not begin full migration.

---

## Historical initial checkpoint (preserved)

# Qt Studio proof — incomplete development checkpoint, 2026-10-05

This is **not a completed functional proof or a 9/10 visual/usability claim**.
Native renderer hosting failed bounded continuity probes. Robert's acceptance
and the independent review have not occurred. No full migration started.

## Source and ownership

Starting and final HEAD: `4a4f6e03ad2119e790e88d8338bac9412a139881`.
The substantial pre-existing dirty tree was retained. The pre-edit hash manifest
is `work/qt-studio-proof/baseline.json`; the exact task patch, final file hashes
and preservation comparison are in that directory's `review-index.json`.
No commit, push, shared planning-document edit, release, publication, portable
change or extra worker/reviewer dispatch occurred.

## Implemented boundary

`studio_qt.py` provides styled Qt Widgets/ADS panels and one withdrawn Tk Studio
state owner. Existing session, color, tuning, transport, run/revision/ACK and
Save Authored callbacks are retained. Qt timers replace the hidden owner's Tk
timer dispatch. Pumping Tcl's Windows loop alongside Qt caused a fatal Python
3.14 GIL error; that failed initial route was abandoned, not certified.

The shell includes real catalog trees, source selection, session open/save,
declaration-driven pigment buttons, Follow/Pin (Pin OFF/ON), live override,
parameter knobs with numeric entry, parameter-specific authored reset,
knob/slider context menus, listening-window switches in Advanced, read-only
mapping data, exactly twelve measured bands with bar/band-trace styles, real PCM
waveform presentation, transport callbacks, diagnostics and separate ADS layout
persistence. Qt artistic controls invoke the sole retained owner. Presentation
preferences are layout data. No new DSP, normalization, audio routing or scenes.

Existing Color Inspector refresh now rebinds a stale target label before building
rows. The existing startup log traces Fractal selection and failed close to
`StopIteration` from that stale label. This is log-based causal evidence; the
original physical click sequence was not reproduced on the untouched baseline.
The targeted stale-label check and existing actual-Tk regression pass afterward.

## Blocking hosting result and concrete alternative

The existing renderer remains a separate GLFW/ModernGL process. Raw Win32
hosting reached readiness, then the main Qt thread stopped progressing inside
ADS `addDockWidgetFloating`. Two raw-host probes failed; the first was not
instrumented, the second supplied stack evidence. The next two probes used
Qt's `QWindow.fromWinId` / `QWidget.createWindowContainer` alternative and stalled
inside container creation, including when attachment waited for readiness.
Those probes do **not** establish a general Qt limitation or the exact native
cause. They establish failure of these arrangements on this checkout/device.
Verified owned process trees were stopped after preserving failure evidence;
no unrelated process was stopped.

`window_host.py` adds an opt-in Qt foreign-window announcement flag; the original
Tk path remains unchanged without that flag. Start in the normal Qt entry now
reports the unresolved native-hosting issue instead of running the known failed
path. The diagnostic GPU probe explicitly opts in. **Do not present the guarded
Start as preserved working playback or regard this as the requested proof.**

A concrete next alternative is a separate compatibility-control process owning
Tk, with explicit commands and ACK snapshots to the Qt presentation, then a
focused renderer-host probe without Tk windows in Qt's process. This retains
one business-state owner and the existing renderer, but adds an IPC seam and
requires careful destination-bound gesture/save handling. Bob should review
this proposal before continuing; another possibility is a scoped extraction of
the existing state services out of Tk, which is a larger migration.

## Dependencies and redistribution

Project-local optional pins are in `requirements-qt-studio.txt`:

- `PySide6-QtAds==5.0.0.2`
- `PySide6-Essentials==6.11.1`
- `shiboken6==6.11.1`

Windows x64 `cp310-abi3` wheels resolve on the existing Python 3.14.7.
Imports report Qt 6.11.1. The ADS wheel pins the same Essentials/Shiboken release.
No global/admin installation or unrelated upgrades were performed. PyPI reports
the ADS release dated August 4, 2026; the binding's upstream repository documents
the package and Qt 6.11 build direction. This is not an independent maintenance
or future-compatibility guarantee.

ADS package metadata states LGPL 2.1 with MIT attribution for original binding
work; Essentials metadata offers LGPL 3/GPL alternatives. Commercial use under
LGPL can be possible, but redistribution must preserve applicable notices and
license texts, provide applicable library/modified-library source availability,
permit the required library replacement/relinking and reverse engineering for
debugging modifications, and account for Qt third-party notices and modules.
Static/locked distribution needs particular review; a suitable commercial Qt
license is an alternative for Qt, not automatically for third-party ADS. No
redistribution/release was produced. Fonts use installed Segoe UI; no font was
copied into the project. No Grok logo or generated assets were introduced.

Primary records inspected:
[ADS PyPI](https://pypi.org/project/PySide6-QtAds/),
[binding upstream](https://github.com/mborgerson/pyside6_qtads),
[Qt license inventory](https://doc.qt.io/qtforpython-6/licenses.html).

## Reference and composition

`images/Bobs Mock up.jpg` was opened and inspected as pixels and preserved.
It informed charcoal surfaces, copper active tabs, cyan signal accents and a
dominant preview. The supporting `ZeraphinaX_Studio_Bob_Concept_02.png` remains
absent and was not visually inspected. No failed Library transfer route was
repeated. Real catalog labels and Fractal taxonomy are retained.

`work/qt-studio-proof/shell.png` is an empty-shell development capture, not a
scene capture or proof of canonical conformity. An initially unbalanced ADS
layout was visually inspected and corrected; failed/native captures are not
silently represented as a successful hosted renderer.

## Actual checks and limits

- `studio_qt_test.py`: owned visible Qt CPU/native-widget checks passed for
  selection/Stop, stale target recovery, layout-only reset, repeated nine-panel
  arrangement through ADS APIs, floating/redocking through APIs, context-menu
  presentation binding, controlled recoverable error reporting and close.
- `studio_workspace_test.py`: existing standalone actual-Tk/native host checks
  passed, including eight float/dock cycles per panel, unsent drafts/revisions,
  layout separation, geometry recovery and focus/shortcut checks.
- `studio_qt_ui_cost.py tk` and `qt`: sequential five-second empty-GUI probes,
  1600×980 and 200-ms panel cadence, synthetic source selected but no renderer
  or audio. Tk: 5.005 s wall, 2.234 s process CPU, 19 samples, median 2.681 ms,
  max 19.741 ms. Qt: 4.998 s wall, 0.313 s process CPU, 25 samples, median
  3.814 ms, max 4.709 ms. Window contents and callback workloads differ. These
  figures cannot establish a renderer/GPU/whole-playback speedup.
- Four synthetic full-quality hosting probes failed as described above. No
  successful renderer-continuity receipt, matched rendered performance result,
  scanout timing, memory profile or GPU timing is available.
- `git diff --check` passed (line-ending warnings only).

Actual drag ghosts, cyan target overlays and mouse-release placement remain
unverified. API float/redock is not actual gesture evidence. Real native-monitor
changes/DPI recovery, continuous input/output listening, active-ACK color/tuning
editing, renderer close after layout operations, full AV, long sessions and
preservation of full-quality playback under Qt are not certified.

## Pending migration inventory

Full legacy palette-family cycle/preset UI, gradient range editing, profiles,
audition controls, complete library/effect/layer/experimental/review views,
thumbnail presentation, complete keyboard/held-control behavior and working
per-panel mouse/keyboard help remain pending. Mapping currently exposes real
packet data as bounded read-only text; it is not the finished compact trace/
meter presentation. Numeric switches preserve values through the existing
callbacks, but current live run/ACK behavior was not successfully verified.
The nine-panel arrangement demonstrates API capability, not polished nine-panel
usability. No visual or usability score is assigned.

## Launch and rollback

Double-click `run_qt_studio.vbs` for the incomplete, guarded development shell.
Diagnostic command: `.venv\Scripts\python.exe -B -X utf8 app\visuals\studio_qt.py`.
File writes use `work/studio/qt-layout.json`, `qt-errors.log`, `qt-startup.log`.
Reset Layout affects layout, not artistic settings. The normal proof launcher
does not change or replace `run_unified_studio.vbs`; that remains the previous
Tk presentation and renderer playback entry. Neither entry is a release.

Return to Bob with this blocker and proposal. Robert's functional proof review
boundary has not been met; do not proceed to full migration or critic dispatch.
