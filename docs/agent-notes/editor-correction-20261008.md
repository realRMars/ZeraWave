# ZeraphinaX editor correction — actual Builder results, 2026-10-08

Implemented in `C:\ZeraWave`, uncommitted. Return route is manual Prompter/Bob
review, then Robert acceptance. No worker or critic was dispatched. Implementation
and technical checks are complete; full native interaction acceptance remains
partial because the isolated Computer Use drag session became unresponsive.

## Source and preservation

HEAD: `fe1a7b74f791fbfcc1879798e5e944be50ae061f`.
Fresh dirty baseline: `work/editor-correction-1791475832613495000/baseline.json`,
SHA256 `c15f44ddc13f8880fbbb043a80acbf9d01794d467a97a2e2c2f8b6577021ddb0`.
It inventories 351 tracked/nonignored untracked files and copies relevant source.
The previous raster report manifest SHA256
`b84c32e9f95a94ad1caca2275a74489068460db2cd4b3f7b12e45929bda7963c`
and all 13 bindings were reverified before changes.

Evidence root: `C:\ZeraWave\work\editor-correction-1791475832613495000`.
`final-source.json` binds all task files and preservation verification;
`correction-only.patch` compares this task against its dirty baseline, including
new files. `INDEX.md` records final manifest/patch hashes. HEAD alone is insufficient.
The existing renderer, compositor, audio, media registry/frames, user sources,
shared planning documents, previous reports/failures and unrelated dirty edits
are preserved. No package installation, Git stage/commit/push, release or publication.

## Delivered behavior and explicit decisions

- One Layers hierarchy, stable-ID inline row bodies, independent expansion,
  transparent **New Layer**, main/row plus menus, bound dimensions/transforms,
  Fit/Fill/Stretch, flips, rotation, Align, blend, sibling arrows, Reparent/Ungroup.
  These are real row widgets, not fake child nodes. Late thumbnails update fixed
  placeholders; rename refresh restores field focus. Playback/model/Web controls
  retain existing ownership. Saved sprites remain compatible; creation commands
  are hidden. Web backend remains pending, unchanged.
- Ordinary raster lock protects own pixels/transforms. Group lock derives
  protection through its subtree without rewriting individual choices. Drawing,
  names, numeric/transform, clipboard, insertion, deletion and destination checks
  use the appropriate rule. Group drawing explains that it is a container.
- Adjacent own/subtree eyes retain individual descendant choices; Group has one
  subtree eye. Locks sit at row ends and inherited protection has a chain cue.
  Every row has a master-opacity slider/percentage. Group master applies once to
  isolated content. Effect contribution remains `blend_strength`, independent of
  `opacity` and stroke opacity; the old effect-opacity field was a master alias.
- One owner retains scoped field-patch recovery. Canvas Undo/Redo recovers current
  layer drawing only and stops when exhausted. Layers/Library recover creation,
  deletion, duplication, ordering/reparent, transforms, crop/masks and structural
  Cut/Extract/Paste. Text retains text Undo; unfinished paths retain local recovery.
  Management recovery never replaces surviving rows wholesale. Deletion restores
  latest retained pixels, IDs and drawing recovery. Nonhistorical eye/lock choices
  survive. Multi-Delete deduplicates subtrees, blocks the entire batch if any member
  is protected, preserves batch selection on right-click and commits once.
- One immediate direct Qt toolbar, with visible grip, float/edge redocking and
  remembered layout. Brush/Pencil/Sampler/Eraser/Smudge/Select/Crop/Cut plus view,
  solid Fill and help. Double-click toggles one remembered settings window per
  tool. No generic Toolbox/Brushes/Selection launchers remain visible. Canvas
  context/view settings retain Fit/native/Canvas Size without selected-layer need.
- Independent Brush/Pencil color/settings, representative stroke presets, exact
  native-pixel/percentage fields, synchronized presets and relevant controls.
  Pencil defaults to its existing crisp Square geometry; Round now actually makes
  round dabs rather than silently ignoring the shape field. Saved artistic scene
  data needs no format migration. New per-tool preferences have authored defaults.
- Sampler uses own or visible-composite pixels before checkerboard/handles,
  respects the logical canvas clip, reports ARGB and the receiving last Brush/Pencil,
  and preserves other settings. Empty/transparent/outside samples leave color alone.
  Right-drag erases; Shift+right-click retains context; Esc/focus loss cancels.
- No-target drawing prompts **Create a new layer?** once per gesture. No preserves
  state; Yes creates white on empty canvas, explicitly transparent overlay otherwise.
  The next gesture uses the active tool. Ordinary New Layer remains transparent.
  Immutable write/allocation failure preserves accepted content and explains it.
- Solid Fill safely replaces selected own editable RGBA with explicit color/alpha,
  respecting crop/masks/current shaped selection, with one drawing Undo. It ignores
  stroke opacity and does not fill descendants or perform contiguous flood fill.
- Whole-layer Select is default; advanced neutral selection, rectangular Crop
  side/corner handles, and all retained Cut boundary shapes remain. Cut/Extract
  are structural transactions; Keep/Mask are existing Keep-mask aliases, Remove
  is an own Cut mask. Select/Cut settings retain saved-operation edit/toggle/remove.
  Curve anchors/handles are provisional until completion/Apply; Open/Close/local
  Undo alter preview, Enter/double-click/first-anchor close and complete, saved-mask
  Discard retains committed data. Main Cut automatically commits on completion.
- External Library Copy payloads enter the real Layers viewport. Row placement
  and creation commit together, including asynchronous resized derivatives;
  existing native working-dimension options, cancellation and reference IDs remain.
  The native floating-pane acceptance check is still pending (see below).

## Reproduced findings and measured drawing correction

Source confirmed ancestor-wide locks, single-current Delete, tabs and global
history before editing. Automated/native checks showed editable children under
ordinary locked parents after correction; protected batch deletion and recoverable
content were verified with the real isolated owner and scripted Qt input. Native
rename exposed focus loss and late thumbnails shifted controls; both were fixed
and covered by final DPR 1/2 scripted checks. Curve confusion was treated as a
usability concern: scripted closure/handle/Apply/Discard/recovery passed; no new
native Curve defect was established.

`comparison.json` contains counts, per-phase median/p95/p99/max and workload/source
bindings. Matched input is the unchanged `images n vids/Xeraphina.jpg`, SHA256
`256e6ced41f77999576cf42dc574d262c45791e875484f736607cd5ecfe57c1f`,
1792×1008 native pixels and canvas, 809×463 logical viewport, DPR 1, zoom 1,
depth 0/Normal, 120 points from (261,171) to (548,292) at requested 8 ms,
three repeats per tool. Size 12, opacity .65, flow .7, hardness .8; effective Pencil
Square / Brush Round. Both arms use the same harness. The before arm loads the
preserved original Canvas/artwork/composition modules with a common current
Shell/control owner; it is a component comparison, not a whole old executable.
The common owner avoids changing ACK/storage ownership. Baseline close produced
an old-editor/new-Shell `remember_tools` cleanup warning; measured runs completed
and the isolated owner was force-closed by existing cleanup. No historical full
application/UI acceptance is inferred from that arm.

Before: Pencil 22.09–22.72 s; Brush 23.15–23.59 s for the requested .960 s input.
Final: both approximately .963 s. Median backlog is zero in every final repeat;
maximum transient backlog is 25.60 ms Pencil / 11.78 ms Brush, without persistent
growth. Every one of the six final native PNG SHA256 values equals its matched
baseline output. Full-source geometry, dimensions, opacity, flow and pixels remain.
Final paint-return medians are approximately 1.51–1.55 ms Pencil / 1.79–1.82 ms
Brush. Release→encoding/registry/ACK remains about 1.57–1.63 s, asynchronous and
bounded, not hidden or claimed instant.

Local fixes cache native stroke coverage and update the touched region of a full
native result; canvas composition paints the affected physical viewport region;
checkerboard uses a tile; round cursor uses an equivalent affine basis instead of
48 repeated matrix/metadata calculations. An attempted cropped-source preparation
did not solve the remaining Brush backlog and was removed. Its failed timing is
retained in `stroke-final-after`; successful exact-final timing is `stroke-bound-final`.
These are scripted event/paint-return measurements, not visible scanout or general
FPS guarantees. Actual native-photo pointer trailing remains for Robert's review.

CPU roles/packet normalization were inspected: distinct GUI/owner/renderer PIDs
are summed as percent of one core (same PID deduplicated). 123% may be valid while
system utilization is low; partial/stale indications remain. No clamp or broader
monitor/renderer profiling was added.

## Practical aggregate bounds

One shared history holds at most 64 commands / 8 MiB serialized commands, cached
recovery rows and flags, with 256 MiB unique retained managed native pixel estimates
across scopes, not an unlimited stack per layer. Current content remains under
existing component budgets. Immutable managed stores remain 512 MiB, not pruned
on history trimming. A full store reports failure and preserves accepted content.
One active stroke, one pending write and one queued completed stroke remain;
native image buffers are at most 32 MiB each, plus bounded coverage/preview/encoding
temporaries. Existing editor image/mask/view and renderer budgets remain in the
feature instructions. These are component limits, not a total process-RSS promise.

## Executed checks and native evidence limits

- Existing standalone composition, canvas, registry, recovery, image-layer and
  composition GPU checks passed; `regressions/RESULT.json` records all seven.
  The existing raster workflow test was migrated, retaining substantive checks:
  direct Brush/Eraser/Smudge, nested automatic cuts, own/subtree visibility,
  reparent affine, numeric transforms/hotkeys/text guard, selection clipboard,
  write failure/queued stroke/stale rejection, silent video snapshot, original
  hash, save/reopen and v3 compatibility all passed (`raster-final`, final-checks).
- New standalone editor checks passed at DPR 1 and offscreen DPR 2: scope isolation,
  deletion/drawing recovery, Redo order/aggregate limit, Group locks, inline rows,
  master/effect independence, singleton settings, presets, text Undo/focus, Fill,
  protected batch atomicity, native asset placement and Curve/Crop recovery.
  `dpr2-retry-status.json` and final-check logs retain results. First offscreen
  focus check failed with an inactive test window; explicit activation fixed the
  fixture. Earlier missing-fixture callbacks and an overstrict ≤1 preview tolerance
  are preserved as failed attempts, not deleted or called passes.
- Final focused DPR 1/2 preview checks preserve native constraint bytes exactly;
  transformed nested-group partial/full Qt previews differ by at most 2 channel
  levels (mean ≤.000203), within established ≤3 Qt rounding tolerance. They verify
  the cursor basis, sampler clipping and real Qt viewport external Copy-drop routing.
  GPU complementary-cut cases and native-size draw timing are distinct evidence.
  Actual GPU was NVIDIA GeForce RTX 3070 Laptop GPU; no world FPS/listening claim.
- Native Windows mouse/keyboard was used in isolated `native-review2/3` with
  spontaneous-input logs, state/source snapshots and canvas captures. Observed:
  empty prompt No/Yes-white, strokes and exhausted drawing Undo, ordinary locked
  parent with unlocked child's painting/rename, inline expansion, Pencil settings
  double-click toggle, toolbar float/redock, main New Layer→draw and native-dimension
  Library drop cancellation. These are earlier task iterations, not complete final
  native acceptance. A subsequent drag froze the owned review instance; recovery
  returned **failed to activate captured window**. Stacks/state/failure are retained;
  only verified task-owned GUI/controller processes were stopped. Sky's earlier
  drag needed an extra click to release; its automation semantics are a confound.
  Do not claim this establishes a resolved native drag defect or cross-floating-pane
  acceptance. No further native input was sent after failed recovery.

Pending native acceptance: final docked/floating Library insertion/reparent;
Group/multi-Delete/text-history actions; full tool/hotkey/settings, opacity/effect,
Sampler/Fill/Crop/Curve usability; native-photo continuous pointer response and
final save/reopen via actual controls. Scripted owner/Qt/GPU checks support these
but do not replace them. No natural listening, audible routing, multi-hour soak,
scanout or comprehensive audio/world regression was performed. Audio/renderer
code was not changed. Silent transport boundaries and known Web/video limitations
remain. No broad performance or architectural prerequisite was introduced.

## Robert review steps and checkpoint

Launch `C:\ZeraWave\run_zerawave_studio.vbs`; View recovers the three docks.
Create transparent New Layer and test white onboarding separately. Nest a child,
lock its ordinary parent, paint/rename the child; then compare Group lock/unlock.
Highlight multiple rows, Delete, and recover through Layers; draw on two rows
and exhaust Canvas Undo independently. Float/redock the toolbar and Library/Layers,
drag Xeraphina with Native/Cancel choices, and inspect both opacity contributions.
Click/hotkey every direct tool with settings closed, toggle settings twice, sample
colors, fill, adjust Crop sides/corners and complete/edit/discard a Curve. Save As
to a new review session and reopen. Draw continuously on native Xeraphina and
judge visible pointer following; recorded timings do not substitute for that view.

Candidate stays uncommitted for Prompter/Bob's actual-results review and Robert's
acceptance. Shared ROADMAP/HANDOFF/AGENTS/README/visual-identity documents were not
edited. This note is actual task evidence, not a new prioritized backlog.
