# Second media correction pass — actual results, 2026-10-08

Implementation is ready for Robert's manual review through Prompter/Bob. The
candidate is **unaccepted and uncommitted**. Native interaction acceptance is
blocked by the Computer Use helper; synthetic checks do not replace it.

## Identity and preservation

Checkout: `C:\ZeraWave`. HEAD remains
`fe1a7b74f791fbfcc1879798e5e944be50ae061f`.
The preceding manifest SHA-256 was verified as
`cf7134b2b31fef7efab889d43df80d8209437b6e6977aef00e9cf1068301eaa9`;
all 22 task-file bindings matched before editing.

Evidence root: `work/media-corrections2-20261008-1791437816969303400/`.
`baseline.json` and `baseline/` bind the actual dirty bytes, not published HEAD.
`final-source.json` provides baseline/final per-file hashes and identifies new
files. `correction-only.patch` contains only this pass, including new tests and
this note. `SHA256SUMS.txt` binds those artifacts. Prior evidence was not replaced.
`preservation.json` verifies 16 original fixture, user library/layout/log,
launcher and owner-document bindings. Root planning documents were not edited.

No dependency installation, workers, critic dispatch, commit, push, release or
asset deletion occurred. The launcher still reads the working checkout. Audio
ownership, renderer/context, world clocks, animation transport and video decoder
code were not rewritten. Active natural audio/capture was not exercised here.

## Stages and visible result

| Stage | Implemented | Outstanding validation |
|---|---|---|
| A | Private stroke buffers; session/revision/target guards; exhausted history no-op; immediate refresh; visibility/lock excluded and retained across other Undo; focused Library history; clipboard subtree IDs and pending-region explanation | Native keyboard/focus recovery remains unverified |
| B | One active tool shared with indicators/options/cursor; choosing a shape exits painting; target status; hidden/locked/zero-opacity rejection; footprint outlines; nearby Apply/Discard/Extract; open-path closure and limits | Actual cursor/gesture ergonomics and native cancellation path |
| C | Visible Add layer; atomic first-stroke child; subsequent strokes reuse it, including parent reselection; expanded ancestor path and selected child; original-only visibility; eye/lock columns; nested imported/extracted children | Robert's usability review in his saved layout |
| D | Paint/extraction dependencies classified internally; no visible Library growth from strokes; immutable files retained; portable Save As; current-resource metadata/validation separated from historical resources | Multi-hour use at resource bounds not measured |
| E | Extended selection, visible-row Ctrl-A, Delete, atomic deduplicated batch removal/recovery, filtered category hiding, collection-targeted import and drag membership, existing rename/delete/persistence retained | Native list/drag/dialog acceptance |
| F | Singleton toggle palettes; remembered/clamped geometry and icon reflow; swatch, exact values/presets, relevant controls; point sampler; temporary right erase; Shift-right menu; anchored/clamped Align with Canvas/Selected sections; Canvas Size moved out of Selected | Native popup/cursor/reflow checks; optional palette-size choice deferred |
| G | Visible crop midpoint handles; all existing shapes retained; failed commits keep preview; extraction reveals aligned child; magnetic attraction/status and explicit limits | Native freehand/curve tracing and subjective edge-selection quality |

Tool highlights are cyan; expanded section controls use amber underlining. The
brush presets are 4/12/48 native pixels, opacity .25/.5/1, and smudge strength
.2/.5/.8, with exact entries. No highlighted preset means Custom. Sampler reads
one selected source pixel after its mask, excluding checkerboard and handles.
Eraser removes alpha. Right-button erase does not change the selected tool;
Shift-right-click escapes to the menu. Focus loss cancels an uncommitted stroke.

Original-image visibility, whole-artwork visibility, and child visibility/lock
are distinct. Drawing on a parent reuses its frontmost immediate Paint child;
show/unlock that child if needed, or explicitly choose another drawing layer.
Source files remain immutable. Creating a first child and its stroke is one
history command. A completed extraction is one command; preview points have
their own bounded local history.

## Established errors and limits of diagnosis

The original logs were copied without modification. `qt-errors.log` had the
empty-Redo diagnostic; `qt-startup.log` had missing-image KeyErrors in
`paint_move` and `paint_finish`. Entries lack run IDs/per-entry timestamps; only
file modification times and stacks are available. They cannot establish which
traceback belongs to Robert's extraction event. The prior thumbnail crash is a
separate historical finding.

`baseline-reproductions.json` records direct isolated reproductions against the
frozen pre-edit source: `ValueError('Nothing to redo.')`, both missing-cache
`KeyError`s, Circle selected while the active tool remains Pencil, and visibility
recorded as an Undo command. The correction removes the stroke's dependency on
the evictable cache, checks the bound target before mutation, restores a decoded
cache entry when needed, and treats empty history as normal.

Asynchronous writes finish into immutable files. If the bound target/session or
revision has changed, the completion is rejected and the file retained; it never
resurrects a deleted target. Registration/commit errors retain committed artwork.
Tree eye/lock commits are deferred outside Qt's item-click emission so rebuilding
the hierarchy does not invalidate a live clicked C++ item.

User-reported extraction crash is **not independently reproduced or uniquely
attributed**. General physical shortcut behavior, full error recovery, physical
DPI/input devices and multi-hour operation are not certified by these tests.

## Checks and retained evidence

- `qt-final-2/RESULT.json`: real isolated ControlOwner and Qt widgets with
  synthetic events. Auto child/reuse, cache eviction, eye/lock clicks without
  history, failed immutable writes, rejected late target completion, all seven
  selection shapes, crop corner/side drag, ninth-mask rejection with preview
  retention, temporary right erase/cancellation, clipboard, nested extraction,
  collection import/drag/membership, Ctrl/Shift multi-select, Ctrl-A/filter,
  atomic reference/layer/membership recovery, portable save/reopen, exhausted
  history and new-branch redo invalidation pass.
- Earlier Qt runs are retained individually. `qt-01` failed because the probe
  began a stroke before the restored target pixels were ready. `qt-02` exposed
  the evicted original image not being repopulated from its completed decode
  job; subsequent runs pass after that correction. Neither is claimed to be a
  reproduction of Robert's extraction event.
- `recovery-1791438726642191800/RESULT.json`: exact service branches plus real
  registry/animation owners; injected remove, Undo, composition and relocation
  send failures restore state, history and frame-owner identity. No audio output.
- `registry-reopen.json`: a fresh registry restores the two current internal
  dependencies and retains three unused historical records without eagerly
  decoding them. Public Library count stays two.
- `registry/`: existing media registry standalone check passed import/validation,
  collections, removal/relink/cancellation/persistence and session compatibility.
- `history-bounds.json`: 100 edits retain 64 commands; exhausting and redoing
  beyond both ends are no-ops; combined serialized state remains within 8 MiB.
- `canvas-dpr.json`: existing offscreen Qt/QTest check passed DPR 1.5, geometry,
  zoom/pan/crop/flips/group inverses and transform handle contracts.
- `pixels-01/RESULT.json`: actual RTX 3070 GL stage and Qt editor agree within
  **one byte/channel** for all five blend modes at strength 1 and .35, with a
  translucent colored layer at .7 opacity over an opaque colored backdrop.
  Same-parent ordering changes the output. Blend/color combination is distinct
  from opacity/contribution; blend strength is preserved.
- The same pixel probe uses the actual Xeraphina source: a point near a strong
  edge attracts from (176,20) to (180,11), while a sampled flat-region point is
  unchanged. This verifies local gradient attraction, not semantic segmentation
  or native lasso usability. Radius is 12 native pixels; weak/flat edges may not
  attract, and manual correction remains necessary.
- `native-gpu-1791439141933454400/RESULT.json`: existing native fidelity check
  passed at 1792×1008 and 1825×1034 for the two stills, and at 736×400 at video
  PTS 2.0. Editor detail and GPU output have zero byte difference from the
  decoded references. Its single-query times are not FPS/presentation evidence.
- `image-layer-gpu.json`: existing actual-GPU alpha/order/blend/group/mask,
  allocation failure, resize and lifecycle contracts passed. Composition pure
  checks and syntax compilation passed. Git diff --check and task-only whitespace
  review passed; unrelated existing CRLF conversion notices were retained.

### Native interaction blocker

`native-01/LIMITATION.txt` records the exact failure. The helper selected the
owned Studio window and displayed its UI. The Import click failed with
**“foreground window did not report a process id”**; one retry after fresh
window/state selection failed identically. No editing input was delivered.
All **14 requested native acceptance steps remain unverified**. The owned probe
was closed; unrelated sessions were untouched. No alternative injected-input
tool was substituted. This is a tool failure, not an approval rejection.

## Practical bounds and recommendations

History remains 64 commands / 8 MiB serialized command data across Undo + Redo,
plus bounded nonhistorical flags. It contains references, not raster blobs.
Save As keeps history in the current process; reopening clears it. Recommend
retaining 64 for now. A future configurable 100 must preserve the byte cap,
account for flag/resource references and retained files, and be tested with large
edits; a command count alone is not a memory guarantee.

32 layers, six nesting levels, eight masks per layer, 128 points per mask and
32 preview-history states remain. Native images are limited to 8,388,608 pixels
and 8192 per side. Existing editor image/mask/model caches remain 192/128/64 MiB.
Each private native image buffer is at most 32 MiB; a stroke and handoff may
coexist with encoding/validation buffers. One artwork writer/gesture is allowed;
further gestures get a wait status while a write is pending. Registry bounds are
128 public references plus 4,096 internal metadata records, an 8 MiB registry
file, 32 collections and 16 validation jobs. Managed working stores remain
512 MiB. These are component limits, not total RSS bounds. Files are retained
even after history trimming; no automatic orphan deletion was introduced.

Palette UI decision: use responsive grids, native Qt DPI scaling and remembered
window geometry now; defer a second Small/Medium/Large UI-scale preference until
Robert's review establishes a useful need. Brush S/M/L are native-pixel brush
sizes, not global UI scaling. No fonts or global scale setting were added.

Known large-source/high-rate video refill stalls remain, including prior 6×/12×
reverse limitations. This correction makes no smooth-video, full-world FPS,
scanout, listening or multi-hour performance claim.

## Separate named-project recommendation — not implemented

Add explicit **New Project / Open Project** and a name, building on the current
named session/composition plus sibling `.assets` directory. Make the project's
Library references and collection memberships part of that named document;
retain the existing global library as an optional source picker during migration.
Image/audio/video categories stay fixed views; collections remain memberships.
Keep original files external by default. Offer copying originals only as an
explicit later “Collect media” choice, with size/progress/cancellation reporting.
Managed drawing/extraction dependencies continue in `.assets`.

New/Open must preserve unsaved-work recovery and never run merely because a dock
opens. Save As prepares dependencies first and atomically writes the new document.
Store/resolve managed paths relative to that document in the proposed project
format, so moving the document and its `.assets` together works. External originals
may still need relinking; preserve IDs, transforms and memberships on relink and
report missing files. Keep a recoverable prior document on failed writes.
Migrate existing sessions only on explicit Open/Save As, copying reference and
collection metadata without silently relocating originals or deleting the global
library. Current sessions are not already this full project model.

Robert's decision before implementation: approve **project-scoped Library by
default with external originals**, retaining the global library as a picker,
or choose another ownership/copy policy. No storage redesign is included here.

## Short manual review and return route

Run `run_zerawave_studio.vbs`; View opens Library, Layers and Composition Editor.
Use a new review session and Import Xeraphina, choosing Native working pixels and
explicit source canvas dimensions. Draw on it immediately; inspect the selected
child, draw/erase/Undo, and confirm no PNG flood. Toggle original-only visibility.
Switch Pencil → Circle → Remove → Magnetic → Crop → Pencil; inspect cursors,
highlight, closure, midpoint handles and the nearby Extract button. Exercise
Cancel, repeated Undo/Redo and a new edit after Undo. Copy/paste a layer, then
check text-field shortcuts. Multi-select/remove references and recover with
Library Ctrl-Z; test collection import/drag/membership/rename/delete. Toggle,
move and resize each palette; verify one window and remembered geometry. Save As
and reopen, checking child identity/content and intentionally empty history.
Review blend/order over a meaningful background in editor and Visualizer.

Return actual results to Prompter/Bob for the review brief; Robert owns acceptance.
Suggested owner-document checkpoint: implementation candidate ready, source-bound
technical checks passed, native interaction acceptance blocked/unverified. No
critic or next phase was dispatched.
