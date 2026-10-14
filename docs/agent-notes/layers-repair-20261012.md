# Layers repair actual results — 2026-10-12

Review candidate in `C:\ZeraWave`; uncommitted. Robert owns acceptance.
The three reported defects are repaired, with natural Windows reproduction of
the disappearing-row failure. One later Windows input stall remains unresolved;
this is not a claim that complete physical acceptance passed.

## Scope and identity

Baseline/final branch `main`, HEAD `15a980c34b47f22ce27c4290084635b5643edf56`.
HEAD alone does not identify this dirty candidate. Evidence pack:
`C:\ZeraWave\work\layers-repair-20261012-1791862819525931700`.
`baseline.json` binds 412 pre-task tracked/untracked source/asset files, two
native DLLs and eight preserved Studio log/session files. `before/` contains
the dirty byte baseline for source files; `baseline-runtime/` is the isolated
pre-task runtime. `final-manifest.json`, `preservation.json`, `post/` and
`task-only.patch` bind the final task scope against that dirty baseline.

Changed files (all other initial dirty work remains independently owned):

- `app/visuals/studio_composition.py`: drag ownership, revision guard, cached
  item/widget reconciliation, submitted-edit exception handling and root add.
- `app/visuals/layer_ordering_test.py`: only dummy-editor binding/resolve support
  for the existing drop fixture.
- `app/visuals/layers_view_test.py`: new standalone production-owner/Qt regression.
- `docs/STUDIO_MEDIA_COMPOSITION.md`: only root New Layer versus explicit child
  wording, preserving the Overseer's existing contract edits.
- `docs/agent-notes/layers-repair-20261012.md`: this actual-results handoff.

Final composition SHA256:
`e43514ddd45a8486cc4b68898d993ed0836a3de094001e938a911964bccff15d`.
Native raster DLL unchanged: `0e13c7e88532251ce15105bc6386fd1351efdbddf49a87d4c58ecf544f7e1cf1`.
Native media DLL unchanged: `4604b28a640919a119f311f5e9b3a88ffefe43f6cc2edffa252adf4faf201dda`.
No build, dependency installation, renderer/audio change, B3 expansion, commit,
push, staging or worker dispatch occurred. Shared root guidance was not edited.
The existing implementation owner is this Bob Builder chat; the Overseer was
notified through the authorized manual coordination route. Foreground tests used
Robert's explicit available-window replies. Peer notification tooling failed
for Monster Trainer; receipt was not established. No unrelated process/window
was stopped or operated.

## Established causes and fixes

1. A complete Windows drag on the pre-task runtime accepts Qt `MoveAction` in
   `LayerTree.dropEvent`, then defers the application transaction. Inherited
   `QAbstractItemView.startDrag` removes the source tree item during Qt's drag
   cleanup. The owner accepts the move and preserves all IDs and pixels; the
   GUI scene matches it, while the visible tree loses a row. Cached C++ items
   become invalid and optimistic/ACK population raises
   `RuntimeError: libshiboken: Internal C++ object (PySide6.QtWidgets.QTreeWidgetItem) already deleted.`
   This establishes a view/lifetime failure, not authoritative artwork deletion.
   Evidence: `live-baseline/disappeared.json`, `after-delete-all.json` and
   `after-new-layer.json`, including owner/GUI/tree/cache/drag events.
   The original console exception was observed in tool output; an excerpt is
   retained separately, not mislabeled as a complete original raw log.
2. `LayerTree.startDrag` now owns an explicit `QDrag` carrying stable IDs and
   the document binding. Qt performs the native drag but does not remove rows;
   the deferred owner transaction performs the move. A changed session/revision
   rejects the stale gesture explicitly, without changing the document.
3. Moving a parent with `takeTopLevelItem/takeChild` also detaches descendant
   item widgets. Their Python/C++ wrappers may remain valid until deferred
   deletion, so a signature/validity-only cache reused invisible controls.
   Regression run `qt-regression-native-5` exposed this second cause. Population
   now verifies the actual tree-to-widget association; refresh heals invalid
   or detached cache entries even without a new revision. Healthy rows are reused.
4. Once owner submission succeeds, a view-install exception must not dispose
   of submitted resource snapshots or roll the GUI back as if admission failed.
   The submitted job remains tracked and owner ACK/rejection remains authoritative.
   The regression injects a display exception, then confirms acceptance, pixels,
   refresh recovery and exact Undo. Submission still does not mean acceptance
   or durability; existing owner recovery/save boundaries remain in charge.
5. Global `+ → New Layer` now calls `blank_layer(root=True)` after pending
   reconciliation. It creates a root independent of root/child/no selection.
   Row `+` and Inside still explicitly create children. Descriptive Undo says
   `New Layer at top level`.
6. There is no model prohibition on an empty tree. In the natural baseline,
   delete-all makes the owner empty but the damaged view stays stale; another
   new layer is accepted but remains invisible. Healing the cache and explicit
   root creation restores the complete empty-document path. Three repeated
   delete-all/add/Undo/Redo cycles pass on both native and fallback routes.

## Executed checks and acceptance map

| Case | Evidence and result | Evidence class / limit |
| --- | --- | --- |
| Natural disappearing blank drag; follow-on empty/add | `live-baseline/`: reproduced owner/GUI intact, tree/cache broken | OS-automated Windows drag; subsequent delete/add fixture actions; isolated copy |
| Blank sibling reorder, image nest, video nest/out, expanded three-row branch | `live-final/01` through `05` JSON/PNG: complete native drag/drop/return, owner/GUI/tree agree, seven IDs/pixels retained | Real Windows Qt/OLE route via Computer Use; final source |
| Descendant drop | `live-final/06-descendant-rejected.json`: no document/history loss | Native Windows canceled/invalid drop; model invalid cases also below |
| Collapsed branch move and expansion | `live-final-2/01-collapsed-move.json`: native completed move, descendants and controls present after expansion | Final source; one previous stalled attempt remains open |
| Actual global menu with grandchild selected | `live-final-2/02-global-root.json`: eight IDs, new root, existing pixels retained | OS menu interaction |
| Siblings/nest/out/branch transforms; invalid self/descendant/missing/placement/ineligible parent; repeated moves | `qt-regression-mixed-12` and `qt-regression-fallback-13`: PASS | Production commit paths plus synthetic Qt input; every state checks owner/GUI/tree/IDs/order/count/source pixels |
| Up/Down and boundaries | Both runs above and `ordering-final/RESULT.json`: PASS | Real Qt button/key dispatch; sibling boundary no-ops; direct drop fixture is not a full drag |
| Large Brush and color change; row opacity press/drag/wheel | Both runs above: accepted own pixels and values; PASS | 512px Brush on 64×48 raster, synthetic events; no broad responsiveness guarantee |
| Video scrub and Ctrl+wheel | Both runs above: distinct actual decoded frame pixels during held drag, exact +/- one 24fps source frame; PASS | Synthetic Qt; original complaint withdrawn; physical smoothness not re-certified |
| Every move Undo/Redo; empty/add Undo/Redo | Both runs above: exact hierarchy and pixels; PASS | Ordered owner history; dynamic labels preserved |
| Damaged C++ item recovery; submitted view failure | Both runs above: PASS, owner remains authoritative | Controlled lifetime/display failure, not natural native drag replacement |
| Mixed and empty-to-fresh Save As/reopen | Both runs above: durable saves, exact IDs/hierarchy/pixels; PASS | Production owner; video explicitly seeks to 2.5s after reopening to match pixels, no transport-position persistence claim |
| Windows save-before-close and eight-layer reopen | `live-final-2/native-final-session.json`, console EXIT 0; `reopen-native-final2/RESULT.json` PASS, owner exit 0 | OS Save dialog, then separate production-owner offscreen reopen; all eight pixels/hierarchy match |
| Existing owner control/resource work | `owner-boundary-final/result.json`: nine checks PASS with 250ms injected transport delay | Numeric typing, audio mute, dropped ACK recovery, Undo/Redo, pinned save/reopen, PNG save, child add, normal close; synthetic Qt |

Each final native/fallback Layers run records **125 checked states**, 12 check
groups and zero Qt exceptions; both owners exit 0. Existing ordering regression
also passes. Exact commands and environment are in `verification.json`.
Sources stay native resolution. Main Visualizer playback is stopped in these
fixtures. Offscreen uses the supported CPU canvas; Windows uses the normal
platform editor. This is functional preservation evidence, not a matched
performance benchmark, audio/music acceptance or a whole-product migration.
The current supported capacity remains 32 layers; it was not changed or newly
validated at the limit. No lower limit was introduced.

All 409 baseline files outside the three modified task files match their captured
SHA256, and both native DLLs are unchanged. All eight original Studio log/session
copies are retained. Seven current originals still match; `qt-layout.json` changed
during this pass (attribution not established) and was left in place. Disposable
test windows use private layout paths. Its baseline copy remains recoverable;
rollback never overwrites that live layout. All 244 app Python files parse, and
Git whitespace checks pass.

The four-point held-scrub waits are raw input-dispatch-to-required-published-frame
waits (not event delivery, cursor latency or scanout): native median 414.78ms,
max 521.39ms; fallback median 417.62ms, max 455.62ms. Runs were concurrent;
four samples cannot establish tails or smooth physical tracking. `scrub.json`
retains all values/PTS/pixel hashes. No claim of a performance improvement.

## Failures, open limits and retained evidence

- `live-final`: after five successful mixed/branch moves and a rejected descendant
  attempt, a later collapsed-branch input stalled the window. No new `startDrag`
  event was recorded. A subsequent snapshot was about 211.6s after the earlier
  snapshot, not the eight-minute fixture watchdog. Stack logging was not enabled
  in that run; it was enabled for `live-final-2`, which completed the same
  collapsed move and saved/closed normally. Cause remains unestablished; it
  could be platform/input handling or application behavior. Do not call it fixed.
  Only that disposable run was interrupted; its accepted state/resources remain
  in the pack. Baseline reproduction was also interrupted (exit 1); neither is
  counted as a successful normal close.
- `qt-regression-native-5` failed on detached descendant widgets: fixed and
  covered by final runs. `native-6` optional full offscreen drag did not deliver
  a drop; it was canceled and failed as required. Offscreen full drag support
  is unproven; Windows evidence supplies the native-route check.
- Runs native-1/2/3/4 and mixed-8/9/10/11 retained harness failures: incorrect
  menu mocking, missing test helper, unsupported spontaneous offscreen mouse
  history, sparse video sampling, hidden canvas decoding and unmatched video
  time after load/Undo. Harness corrections led to final PASS. These failures
  are not hidden or represented as newly fixed product bugs. Earlier harness
  revisions are not all archived; final scripts and runtime identities are.
- Human physical-pointer/DPI acceptance, multi-selection native drags, native
  self-drop, OS-native delete-all/Undo keys, physical scrub/opacity smoothness,
  long-session stress, full 32-layer capacity and general artwork tools were not
  separately certified. No general application suite was run. Sampler/chroma,
  resource-boundary expansion and other migration work are deferred.
- A few Computer Use drag sequences needed an additional explicit release/click
  before OLE returned. Completed cases require logged drop and startDrag return
  plus owner agreement; scheduled pointer movement alone was not called a pass.

## Recovery, rollback and short owner retest

An affected old window may still contain accepted work despite missing rows.
Keep it open, use its existing owner Save As/Retry path to a **new** destination,
wait for durable completion and verify a disposable reopen before retiring it.
Do not delete artwork or replace an open session to recover the view. The patched
refresh rebuilds damaged row caches; a newly launched disposable Studio loads
the saved accepted scene. Rejected/stale drag: nothing moved; repeat it once
the owner settles. Submitted work continues through the existing ACK/persistence
path and is not resubmitted automatically by this fix.

`rollback_task.py` defaults to validation only. After protecting unsaved work and
reviewing `final-manifest.json`, `--apply` restores only the three modified files
from `before/` and archives the two new files under the evidence pack. It validates
**all** final hashes before writing anything and refuses later edits. If it
refuses, merge only `task-only.patch` against before/post/current; do not overwrite
the owner's subsequent changes. It never loads, replaces or stops a session.
The rollback is tested on a disposable source copy with an unrelated sentinel
and a deliberate later edit, not on the live candidate. No reset/clean/staging.

Robert's brief retest on a new disposable copy:

1. Drag blank/image/video between siblings, nest/out, then move a collapsed
   parent and expand it. Check every row remains; try a self/descendant rejection.
   Repeat the previously stalled collapsed gesture. If it hangs, preserve the
   window/logs for stack diagnosis; this acceptance case remains open.
2. Select a grandchild, use main `+ → New Layer` (root), then row `+` (child).
   Delete all, add again, Undo/Redo, Save As and reopen; content/counts must match.
3. Try Up/Down boundaries, Brush/large brush/colors, opacity, video scrub and
   Ctrl+wheel. Judge physical smoothness and normal drag release behavior.

Stop at review. The candidate remains uncommitted and acceptance is Robert's.
