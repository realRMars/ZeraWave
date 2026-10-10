# Studio media composition

Publication status — October 9: Robert authorized the B1/B2 and focused correction
development checkpoint for commit/normal push. User acceptance remains pending.
The candidate descriptions below retain their task-time evidence, including
earlier uncommitted/planned statuses; current implementation and remaining limits
are summarized in [handoff](../ZERAWAVE_HANDOFF.md#october-9-rastereditor-development-checkpoint).
Earlier report sections and sealed work packs retain their original evidence.

## Finishing controls — 2026-10-10

Robert specifically accepted ordinary artwork Save/Save As, direct blank children,
normal closing, improved Brush/Pencil and quick Eraser in the starting candidate.
Smudge mixing looks good to him; its response and subtle larger-tip/sustained
Brush/Pencil trailing remain this finishing pass's review targets. These specific
results do not establish comprehensive editor/capacity acceptance.

Wheel, Ctrl fine wheel, native detail and both magnifiers now share **0.02–256×**
(2%–25600%). Wheel keeps the artwork point under the pointer; existing increments,
Fit and Hand/Space/middle panning remain. At 16× or higher, the Composition Canvas
uses nearest-pixel inspection; stored/source pixels and ordinary output filtering
are unchanged. Zoom can show only a few source pixels. Size-1 Pencil Round and
Square each paint one crisp source cell: opaque color, opacity100% and flow100%
give one opaque pixel; lower flow/alpha keep their existing meaning. The canvas
has no idle shortcut tooltip; button descriptions and question-mark help remain.

With **zero layers**, Fill asks **Create a new layer?**. No/dismiss changes nothing.
Yes prepares the established white editable surface and the original click together,
using left/Main or right/Secondary. Channel, RGBA, location, tolerance, contiguous
mode and boundaries are pinned before confirmation/preparation. One accepted
structural command creates, fills and selects it; one Undo removes it, Redo restores
it. Failure/cancellation or changed session/revision/target leaves the preceding
canvas intact. Busy clicks do not submit duplicates. Existing layers still require
the selected editable, visible, unlocked target; Fill never adds a replacement to
bypass rejection. Acceptance and PNG/session durability remain separate.

Authored canvas size, raster size, view zoom/window and Visualizer output resolution
are independent. A legacy session without canvas dimensions resolves its initial
effective output geometry once per document (fixed output policy, otherwise
1280×720 when no effective output exists); publication and the next session save
carry that size. Later output/viewport changes do not redefine it or resize pixels.
Explicit-size sessions retain their stored canvas dimensions. Existing native size
and pixel/count limits remain; no full PPI/sizing interface is added.

Smudge still performs sequential visible-artwork pickup on every delivered sample.
A stroke pins its contributor/hierarchy plan; full unmasked coverage and eligible
blend paths avoid redundant setup/copies. The evolving selected layer, hidden
exclusion, transforms, crop/masks, blend strength, tips and smear math remain.
The dated [actual results](agent-notes/b2-tiles-20261008.md) bind exact pixel parity,
matched native/B1 timings, outliers, scripted framebuffer checks and unrun physical
pointer/Visualizer checks. No broad capacity acceptance or B3 follows.

## Raster recovery and mouse-channel correction — 2026-10-09

This uncommitted correction starts at published `6aed22041bd15392857c676f832a4f25f07bd765`.
Robert's hands-on acceptance remains pending; the dated actual-results section in
`agent-notes/b2-tiles-20261008.md` binds the new evidence and its limits.

The Composition canvas consumes context-menu events for every tool, including
queued and modified events. It has no right-click popup. Layers, Library and
toolbar/docking menus retain their existing scope; canvas editing controls and
text-safe shortcuts remain. Brush/Pencil paint Main on left and Secondary on right.
Fill uses the same region/protection/transaction rules on either button and pins
the chosen RGBA/channel before worker execution. Sampler assigns only Main on left
or Secondary on right, synchronizes existing chips, and records no artwork command.
Both channels are shared across Brush/Pencil/Fill/Sampler; saved shared Secondary
is authoritative, otherwise migration uses old Brush Secondary. Tool sizes and
stroke settings remain independent. Eraser/Smudge retain their non-color gestures.

Storage/save leases keep immutable mappings without redundant native imports.
PNG encoding and recovery materialize exact pixels through the existing mapping
reader. Failed Futures retain their error outcome, not traceback pixel readers.
Import/export cleanup releases ctypes buffer pointers before closing mappings and
preserves the original failure. Source-only snapshots do not consume PNG job slots.
Retry uses the real owner, coalesces persistence requests and drains within the
existing 16-job/256-MiB queued-byte bounds. Accepted failed resources remain pinned;
history, readers and requested saves determine retirement. No caps are raised.

A completed stroke rejected before admission is **not saved and must be redrawn**
after pressure drains or Retry succeeds. Its preview is discarded, with explicit
feedback; no rejected stroke is retained or automatically resubmitted. Unknown
ACK remains recoverable in the running instance. Accepted pixels/history remain
usable when PNG saving fails; Retry or revision-pinned Save As must secure them.
Save outcomes remain separate from acceptance and publication.

Master opacity sliders have a 26-pixel minimum hit height and immediate whole-track
dragging; wheel needs no activation delay. Latest unsent opacity previews coalesce
behind one ordered owner request; completed edits do not coalesce. Release, or
180-ms wheel inactivity, creates one history gesture after prior preview ACK.
Immutable command snapshots are shared only for owner rollback checkpoints;
mutable history state is copied. Pixel asset replacement preserves equivalent
row controls and refreshes geometry/thumbnails separately. These changes preserve
native dimensions, drawing samples, branch targeting, locks and saved values.

## Focused usability and performance correction — 2026-10-09

The Composition toolbar exposes separate rectangle Select, Lasso and Magic Wand
buttons, plus a scissors **Cut selected pixels (Ctrl+X)** action beside them. Cut
copies alpha and clears the selected raster pixels; it never arms a Cutout mode.
Original tools retain their relative order and existing docking. The sidebar keeps
Wand refinement and pixel commands, without a selection-method dropdown.

Composition's local Edit menu and complete Details area are removed, including
their layout space. Main application Edit remains. Actionable lock/error/acceptance/
save recovery feedback stays in Layers/Studio status. Backend/projection/target
diagnostics are plain data used internally, without Composition widgets. Earlier
Details instructions below are historical and must not be reintroduced.

Each of the 12 tools uses its own original vector cursor, with a visible precision
cross at the logical click hotspot (4,4). Bitmap backing follows current DPR;
pan/movement feedback temporarily overrides it and release/cancel/focus restores
the active tool. Brush footprints remain. Text fields keep ordinary cursors.

Canvas **wheel = 15%** per notch; **Ctrl+wheel = 2%** per notch, inverses for
negative notches and exponent-scaled fractional input. Pixel-only wheel input uses
the same 120-unit notch convention. The finishing candidate shares .02–256 limits
across wheel/native detail/magnifiers, whose factors stay 1.25 / 1/1.25. Fit remains. Zoom
changes only the view. These modifiers apply only over the canvas.

Layer Delete shows **“Everything within layer will be deleted”**, Yes / No with
No as the default. No adds no document/history operation. Yes deletes the full
chosen descendant closure once; a row context command pins that row, excluding
unrelated selected rows. Any protected member rejects the whole operation. Changes
to scene, session or revision while confirmation is open reject deletion and ask
for review/retry. Undo/Redo retains exact hierarchy/resources; original disk files
and unrelated Library assets are retained. Canvas Delete still clears pixels
without this dialog.

Tree refresh retains unchanged identity-bound row widgets and text editors, rather
than reconstructing the entire tree on selection/ACK. Source/frame arrivals use
existing thumbnail refresh without replacing controls. Structural changes reconcile
parents and stacking positions; renumbered order alone does not replace controls.
The existing global input filter skips unrelated layout/style events. Existing limits
remain 32 layers and six parent edges. Recreating a large deleted subtree on Undo
can still pause; source-bound measured limits are in the actual-results note.

Fill keeps native resolution, max-channel straight-RGBA tolerance, transparent-black
comparison, four-connected/all-matching semantics and exact coverage-weighted
premultiplied replacement. Channel-wise NumPy comparisons avoid large intermediate
distance reductions. Optional ABI-1 native traversal releases the GIL, with bounded
scratch and interlocked cancellation; existing native constraint math is reused on
128-pixel changed tiles. B1/older DLLs retain compatible traversal and proven exact
integer weighting. Busy feedback reports real worker phases without percentages,
then existing owner acceptance, ordered publication and separate PNG durability.
Snapshot/source/selection/revision guards and the original 30-second budget remain.

The candidate is uncommitted. No B3 or user acceptance is implied. See the newest
[actual results](agent-notes/b2-tiles-20261008.md) for exact source identity, matched
workloads, failures, rollback and Robert's six-step review checklist.

## Selection, clipboard and automatic Smudge candidate — 2026-10-09

This later authorized correction **supersedes** the older Cutout/child/confirmation,
named-source Smudge, per-tool Main and Canvas-only drawing recovery instructions
below. Existing artwork, saved masks and old aligned pieces remain compatible.
The candidate is uncommitted and awaits Robert's hands-on acceptance; no B3 begins.

**Select (V/M)** rectangle, **Lasso (L)** free-form and **Magic Wand (W)** color-based
selection are three separate direct toolbar buttons with distinct checked states. Rectangle/Lasso are usable on
release, with a native coverage outline and no confirmation, asset, child or
history command. Wand compares RGBA and retains tolerance, connected/all-matching,
Add/Subtract, edge and feather controls. Target/source geometry pins selection;
obsolete calculations and changed source/inherited placement cannot redirect edits.
**Transform (T)** is the distinct whole-layer tool with move/resize/rotate handles.
Pasted layers select it automatically. **Crop (C)** keeps Apply crop / Cancel crop;
crop compensation preserves retained landmarks and children.

The scissors toolbar action, sidebar and shortcuts provide **Copy pixels (Ctrl+C), Cut pixels (Ctrl+X),
Paste pixels (Ctrl+V), Delete selected pixels and Deselect (Ctrl+D)**. Copy exports
selected own raster pixels and alpha without altering the source. Cut exports
before clearing actual raster data on that same layer; Delete clears without
changing the clipboard. Neither adds a mask or child. Missing/empty selection,
unavailable/incompatible sources, protected writes and capacity/export failures
give feedback and preserve artwork. Locked readable source pixels can be copied.
There is no automatic layer/subtree fallback. Layers context menu retains explicitly
labeled layer/subtree Copy, Paste, Duplicate and Delete commands.

Paste creates an independent selected editable sibling immediately above the active
layer. ZeraWave's immutable clipboard payload retains source dimensions, transparent
selection margins, own mask coverage, copy-time source-to-canvas affine, opacity and
blend. Own masks apply once in exported alpha; they are not inherited by the new
layer. Opacity remains presentation state. Captured placement is converted into the
destination parent's coordinates, independently of later source or active-layer
transforms/crop/flips. OS image data carries a payload hash/token; external clipboard
replacement invalidates internal origin. External images are centered on the logical
canvas at one canvas pixel per source pixel. Copy covers selected own content, not
merged layers; ancestor isolation/masks remain the destination context.

Drag inside an active selection to move its content on the **same raster**, including
overlap: clear and destination composite form one raster transaction. A click or
Escape changes no artwork; Escape restores the prior selection for unfinished
selection/movement. Pasted content moves/resizes as its new layer. G/R/S use the
existing numeric transforms; Enter accepts an active transform and Escape cancels.
**Undo editor / Redo editor** in the toolbar and Ctrl+Z/Ctrl+Shift+Z/Ctrl+Y recover
completed drawing, Cut/Delete/move, Paste and transforms in sequence through existing
ControlOwner history. New edits clear the recovery branch. Copy/Deselect are local
and clipboard contents do not change with Undo. Text/number fields retain ordinary
typing, clipboard and local Undo. Old scoped history APIs remain for explicit callers.

Cutout/K, Ctrl+J/Ctrl+Shift+J and selection confirmation/extraction/mask-management
stages are retired from everyday tool controls and shortcut help. Existing saved
masks remain available through Layers' explicit saved-mask controls and still
load/render/save; they are not the basic Cut/Delete mechanism.

**Main RGBA is shared by Brush, Pencil and Fill.** Sampler click, picker and Main
swatches update it immediately; switching tools retains it. Hover and invalid
samples do not assign. Secondary is shared across these tools; right-click sampling assigns only Secondary. Sizes, stroke opacity, hardness, flow, footprint
and Smudge strength retain their independent tool values. Preferences migrate once
from `media_main_rgba`, otherwise old Brush Main; old other-tool Main values are
ignored. Saved palettes/custom swatches and custom session sizes are preserved.
Fill remains the existing working click-based bucket with tolerance32, transparency,
four-connected default, selection/crop/masks/Group constraints, exact recovery and
publication/durability guards. The later measured latency repair below retains those
pixel semantics and authority guards.

The existing `composition_colors` sidebar uses the full available dock height.
Its lower resize grip changes width; floating height also resizes. Swatches and
built-in/custom size presets reflow, with scrolling for actual overflow. Saved
toolbar identity, placement and docking/floating remain; grip width/floating height
are optional Studio preferences. No parallel inspector or general Studio redesign.

**Smudge (U) automatically samples visible artwork**, writing only the selected
editable raster. A blank transparent overlay can pick up multiple visible sources
immediately. There is no pickup checkbox or named-source picker. Scene, geometry,
available raster/decoded frames and revision are pinned per gesture; other frames
stay fixed until the next gesture. The evolving target preview contributes once
in scene order before each dab. Source eyes, crop/masks, opacity, blend strength,
ordinary parent isolation and Groups use the existing artwork compositor semantics.
Visible locked sources are readable; target/Group locks protect writes. Checker,
handles, UI and world background are excluded. Hidden sources contribute nothing.
Missing visible frames/unsupported sources or exhausted sampling capacity reject
explicitly; snapshot/hide such sources rather than silently omitting them.

Sampling extends the existing CPU artwork compositor with regional reads (4 MiB
per source footprint, conservative 16 MiB aggregate per sample), not viewport
screenshots or compulsory whole-frame readbacks. Existing Smudge footprint, size,
strength and drag behavior remain. B1 fallback uses the same sampling path. Save
still pins revisions and portable PNG dependencies; independent internal raster
IDs may share immutable content-addressed PNG paths on reopen. Imported reference
path uniqueness is unchanged. Native ABI, renderer/audio ownership and saved
session format are unchanged.

Review: select an irregular region; Copy/Paste and move/resize its new layer;
Cut/Paste/move then Undo three times and Redo three times; Delete/Deselect;
sample a semi-transparent color and switch Brush/Pencil/Fill; resize docked/floating
sidebar; Smudge on a blank overlay above visible artwork; Save As and reopen.
Technical results, retained failures, source identities and rollback are in the
latest [actual-results section](agent-notes/b2-tiles-20261008.md). Automated Qt/pixel/
GPU checks are not physical interaction or Robert acceptance.

## Earlier four-correction candidate — SUPERSEDED in the workflow areas above

The four technical lines below the canvas start collapsed. **Details** reveals
Canvas/Layers Undo, native backend/ABI, rendering route and active raster/tool/target
status; **×** collapses the complete area. Refresh never opens it. Failure, lock
and save/recovery feedback remains in the existing Layers/Studio status surfaces.

The existing left **Tool settings and colors** sidebar follows the active tool.
It retains the `composition_colors` saved-layout identity, all-edge docking and
floating behavior. Double-click and context settings focus this same scrolling
sidebar. Brush has native-pixel size, stroke opacity, hardness, flow, footprint
and Fine/Soft/Broad presets. Pencil/Eraser/Smudge retain independent real settings;
Smudge's named source, Sampler's receiver/scope and the existing selection,
refinement, provisional confirm/cancel and saved-mask actions live here too.
There are no advanced tool-settings windows or a separate selection toolbar.
The normal RGBA picker, independent Main/Secondary colors, swatches, custom session
sizes and ordinary field typing/Undo remain. Hand's navigation remains in View.

**Fill (F)** arms a paint bucket; activating it changes no artwork. Clicking uses
shared Main on left click and shared Secondary on right click, without opening a picker.
The default tolerance is 32 (inclusive maximum straight-sRGB RGBA channel distance
on 0–255). Transparent source pixels compare as transparent black. Default
Contiguous traverses four neighbors; turning it off explicitly selects all matching
colors. Nonzero own crop/mask/selection and projected Group coverage constrain
traversal first; disconnected allowed regions cannot connect through excluded
pixels. Exact fractional coverage interpolates the replacement premultiplied RGBA.
Layer opacity and blend mode remain presentation properties; stroke opacity/flow
are separate brush settings and do not apply to Fill. Ordinary parents' own masks
retain their independent-child semantics. Only the SAME selected unlocked raster
is written. On an existing target, rejected/unchanged fills add no history.
Zero-layer Fill instead uses the atomic confirmed creation workflow above.

One background Fill job is admitted at a time on the existing editor executor.
Clicks map through source/crop/flips/parent transforms. Source, target, full scene,
selection, session, revision and cancellation generation gate completion. Target/
tool changes, Escape and Undo cancel private work. Dimensions stay native at the
existing <=8192 / 8 MP bounds; transient regions have no saved-Wand 120 KiB encoding
limit. Typed traversal storage and 64/128-row/tile work bound memory; computation
has a 30-second safety budget and rejects without accepted changes. Fill prepares original/result mapping leases on the worker, then transfers them
through optional existing submission arguments; stale/rejected/closed work retires
unconsumed leases. Changed native tiles remain shared through B1/B2 transactions, drawing history, output publication
and delayed PNG persistence; QImage/B1 fallback follows the same pixel semantics.

Matching magnifier-plus/minus buttons retain factors 1.25 and 1/1.25 and limits
0.02–256 in the finishing candidate. The original Zoom tool and unmodified Z activation are removed. Wheel,
Hand/Space/middle panning, Fit/native detail and modified Undo shortcuts remain.
These are view operations. Robert's review is pending; see the dated actual-results
section for executed evidence, measured costs, failures and remaining limits.

## Earlier usability candidate — SUPERSEDED in selection, Main and Smudge workflow

This uncommitted pass extends the existing B1/B2 editor. Robert’s manual review
is still required. Historical “B2 planned” sections below describe earlier
checkpoints; this section and the dated actual-results report describe the current
candidate. No B3, new brush tips, hardness/flow shortcuts or remaining whole-product
C++ migration is completed here.

**Colors and sizes.** Single-click Brush/Pencil shows the shared Tool settings and colors
sidebar. Drag its grip to float/redock at any edge or below Composition
tools. The visible Main / Left and Secondary / Right chips select the assignment
target. A swatch or + RGBA picker changes that chip. Brush and Pencil use the shared RGBA pair; migration uses old Brush Main/Secondary
unless the saved shared channels exist. Secondary otherwise defaults to opaque white. Left paints Main; right paints Secondary. Opaque white is paint,
not erasing. E is the dedicated Eraser; canvas context events are consumed. Stroke opacity,
color alpha, flow, hardness and layer master opacity retain separate meanings.
Double-click Brush/Pencil focuses this sidebar and retains settings without a duplicate picker.

24 base swatches stay fixed. Add custom saves the active chip into one of sixteen
Studio preference slots shared by both tools. Clicking an empty slot reports it
and leaves the color unchanged. Right-click a filled custom swatch to remove or
replace it. At capacity, feedback explains replacement. These application slots
are independent of QColorDialog’s temporary/static custom slots; use the
application Add custom control for persistent RGBA colors.

The size + saves one of three shared **session** custom sizes; each tool’s current
numeric size remains independent. Duplicate sizes do not consume a slot. Right-
click a preset to remove or replace it. Capacity is explicit; ordinary numeric
changes leave presets alone. Save/Save As includes `media.editor.custom_sizes`;
older sessions use an empty list, and a new session starts empty. Built-in
Fine/Soft/Broad choices remain. Canvas-focused Brush/Pencil digits 1–9 set stroke
opacity 10–90%; 0 sets 100%. Fields/dialogs retain typing. A live gesture keeps
its starting settings; a changed value applies to the next gesture.

**Sampler.** I opens the sidebar for the last active Brush/Pencil. Hover previews
RGBA separately without history or assignment. Left click commits shared Main; right click commits shared Secondary, regardless
of the active assignment chip. The other channel stays unchanged. Selected
layer is the default; Visible Composite is explicit opt-in. Transparent, outside
or unavailable pixels retain valid colors. Own crop, masks, alpha and master
opacity apply; ancestor placement maps coordinates. Readable locked sources need
no unlock. Hover is coalesced at 33 ms; own reads use a one-pixel region/coverage.
Composite opt-in reads four GPU bytes, never an entire frame.

**Crop and extraction.** C previews/refines a rectangle with side/corner handles.
Confirm crop preserves retained source landmarks at their previous visual position
and scale, including flips, independent scales and parent transforms. The same
management operation compensates direct children so their world placement survives.
Older saved crops retain their existing appearance. Crop’s redundant settings
dialog is removed. Transform handles/hit testing/numeric dimensions and mouse/
interactive resize/rotation use retained content bounds. Transparent blank layers
retain their crop frame until content exists.

The primary child action is **Extract to child — keep source**, available in the
boundary preview and selection controls. It creates/selects one editable child,
retains alignment under inherited transforms, and leaves source pixels, masks and
crop untouched. Ctrl+J is that action when selected pixels exist; without a
selection it still duplicates. Conventional Ctrl+X cuts selected pixels to the
clipboard, and Ctrl+Shift+J cuts to child **and removes source pixels**. Both
remain explicitly destructive. K opens a Cutout boundary preview; it no longer
automatically cuts on release. Confirmation, own Keep/Remove actions and extraction
are visible. Own masks affect this raster’s content, while Group masks constrain
the subtree. Cancel changes no accepted artwork; preview Undo remains local.

**Pixel selection.** The shared sidebar selection controls distinguish Whole layer,
manual shapes, Magnetic edge tracing and Magic Wand. Magic Wand compares selected-
layer RGBA color distance (maximum channel difference, 0–255). Contiguous means
four-connected matching visible neighbors; off selects all matching colors in
the selected source. It does not recognize arbitrary multicolored objects.
New/Add/Subtract combine coverage; Edge −8…+8 native pixels contracts/expands,
and Feather 0…8 uses a separable box edge filter. Alpha/crop/existing masks limit
the preview and accepted edit. Confirm selected pixels remains a local paint/
clipboard constraint; Keep selected area visible and Remove selected pixels commit
one own-mask action. Extraction uses the exact coverage, not its bounding box.

Coverage remains full-resolution 8-bit at up to the existing eight-megapixel limit.
One calculation and one replaceable request are pending; revision, selected target
and source identity gate delivery. Contiguous computation has an eight-second
work budget. Committed coverage uses bounded compressed samples in an optional
`Pixels` mask (120 KiB encoded limit per mask; existing 256 KiB scene budget still
applies). No resolution reduction or contour approximation occurs. An over-budget
selection fails before artwork changes; use a smaller region/simpler refinement.
Eight decoded masks at most occupy 64 MiB; close/session changes release local
preview/request references. Masks persist through the existing owner transaction,
history and revision-pinned session save, including the B1 fallback route.

**Named-source Smudge.** Double-click U settings offers Pick up named source own
pixels, initially Off. Off preserves selected-only Smudge. On requires a visibly
named raster source; a direct parent is labeled as a suggestion and a root blank
requires explicit choice. Target and descendants are excluded. It reads only that
source’s own crop/masks/alpha/master opacity, mapped through both transforms. A
locked source is readable; only the selected unlocked target is written. Enabling
does not copy a source into the target. Each gesture pins the source pixels and
revision; replacement/session changes cannot retarget the gesture. The existing
Smudge pickup tile is composed underneath current target pickup and dragged with
the same strength/footprint/constraint physics. Source footprints are bounded to
4 MiB per regional pickup; over-budget transforms reject the private gesture.
Flat Brush/Pencil have no ineffective pickup switch. Additional mixing brushes
remain separate scope. Hide the child to reveal the unchanged original.

**Startup and view.** Transport Start restores the existing Visualizer dock before
queuing the owned renderer start. It displays actual reported context/compiling/
resources/attaching phases, indeterminate progress, cancellation/retry and duplicate
start prevention. A first load may take longer; this does not diagnose every delay
as shader compilation. Magnifier-plus/minus controls and
wheel zoom; H/middle/held Space pan. Fit/native-detail controls remain.

**Save/recovery and review.** Keep the current Studio open until accepted edits
and the requested revision-pinned save are durable. Wait for pending PNGs or use
Retry saving/Save As after a failed write; newer edits require another save.
Reopen the saved review JSON with its adjacent `.assets` directory present before
switching backend or rolling source back. Unknown owner outcomes require keeping
the instance for recovery; owner-process death remains unsupported. Rollback uses
the new pass’s `before` snapshot/task patch only after securing unsaved work, not
a reset/clean of the dirty checkout. Original B1/B2 packs and binaries stay intact.
The dated report separates technical checks, native interaction, latency/memory
and Robert’s acceptance, and preserves the historical unexplained startup failure.


Run `C:\ZeraWave\run_zerawave_studio.vbs`. This uses the current working checkout;
there is no separate exported build. View recovers **Media Library**, **Layers**
and **Composition Editor**. The renamed Layers dock keeps its `image_layers`
layout identity and existing ADS docking. Layers has one hierarchy view with inline controls. Composition Editor is
an additional dock. Its layer-only checkerboard preview never renders a second
world. Visualizer remains clean output.

## Current status and B1 boundary

Recovery base is `0fb4c3fa28632a6aaedb472be50b1837926b9caa`; B1 runtime/save
behavior below is an additional uncommitted implementation awaiting user review.
**The current editor is not accepted.** Recorded evidence and remaining problems
belong in B1 results; technical passes do not establish broad user acceptance.
See [handoff](../ZERAWAVE_HANDOFF.md#current-recovery-checkpoint-and-b1-handoff).

The uncommitted B1 candidate keeps Qt/Python control, the existing ControlOwner
process and GPU output. Completed raster snapshots now enter owner-held history
and ordered output publication before background PNG encoding/storage. Brush
pixels and the interfaces below are preserved. This is implemented candidate
behavior, not Robert's acceptance. Source identities, executed checks, timing
limits and the native walkthrough are in
[B1 actual results](agent-notes/b1-raster-20261008.md).
The next scoped assignment is [B2 in ROADMAP](../ROADMAP.md#b2--c-tiled-raster-resources-copy-on-write-history-and-incremental-compositing).

### Runtime transactions and recovery

Qt owns the private active gesture and provisional presentation. ControlOwner
validates document/session, revision, target, locks and operation sequence, commits
composition/scoped history once, sends ordered images through the existing link,
then starts PNG persistence. Pencil, Brush, Eraser, Smudge, click Fill and shared
selection/cut/extraction raster completions use this boundary. Published snapshots
are immutable Windows shared mappings; pixels never travel in control JSON.
Descriptors declare dimensions, exact RGBA8 stride/byte count, bottom-up
orientation, premultiplied alpha and sRGB. The first stroke also retains original
source pixels so drawing Undo does not reopen a file or wait behind a decoder.

Submitted is provisional. Owner applied/history commit, renderer published
(`applied_revision` acknowledgement), PNG durable, failed and uncertain outcomes
are separate. The canvas can show a private gesture before any owner accepts it.
Accepted feedback orders output; it does not assert a physical display/scanout
time. A later acknowledged output revision marks an older transaction superseded;
it does not certify that older revision's scanout. Output errors remain separate
from PNG failure. Lost ACKs reconcile against the owner ledger or retry the same immutable
operation ID; duplicate delivery does not add history. Completed edits and recovery
keep order; only replaceable previews coalesce. New gestures can follow accepted
edits while older PNGs remain pending. A late write records only its own durability.

Current content, history, pending writes, failed resources, requested saves and
unacknowledged renderer publications pin owner leases. Renderer readers copy under
their own open handles. Success/rejection releases GUI producer leases; an unknown
outcome retains them and blocks context changes. Layer/context changes wait for
owner outcome, not PNG completion; active unfinished input cancels or follows the
existing Apply/Discard decision. Wrong/deleted/obsolete/protected targets reject
before history. Replacing a retained raster uses a new imported reference and a
management command. Library Refresh/Relink of a pinned source explains the
restriction: import a new version, replace the layer source, or Save/reopen to
release drawing history. The original and older accepted pixels remain intact.

Limits: 16 ordered client commands; 128 MiB GUI transfer leases; owner 384 MiB
retained raster snapshots, 16 persistence reservations and 256 MiB pending PNG
bytes; one PNG worker and one save worker. Admission is atomic and reports capacity
failure before acceptance. Existing 64-command/8 MiB serialized/256 MiB native
history, 192 MiB editor cache and renderer budgets remain. Pass 1 below replaces
the former 512 MiB artwork-store ceiling with physical space and headroom.
The immutable source lease counts against retained bytes. GUI history/preview
availability is bounded; pressure is reported rather than silently dropping an edit.

### Save, close and persistence failure

File → Save session opens the destination chooser for Save/Save As. It pins the
requested owner session/revision, artistic settings and Qt tuning drafts; secures
managed PNG dependencies; then atomically replaces the compatible version-5 JSON
(composition version 4). `b1_saved_revision` records the pin. Later edits are not
substituted or marked saved. Feedback reports the saved revision and whether
current work remains unsaved. A completed save of an old session cannot change the
new session's destination or saved marker.

PNG failure retains accepted pixels and usable history. **Retry saving** in Layers
retries working PNGs; if a checkpoint failed it opens **Recover retained revision**
so that exact pinned document can be exported to another destination. Save As can
secure a failed working-store PNG directly in its own `.assets` folder. Failed
dependency copy/JSON replacement leaves the previous valid session intact; retry
retains the same requested document. Four pending/failed checkpoint pins and 16
terminal save outcomes are bounded independently. Failed pins survive until
recovery, requested cancellation or an explicit normal-close Discard decision;
previous-session checkpoints follow the same lifecycle.

Session load secures the old accepted raster context through an automatic pinned
checkpoint under `work/studio/recovery/` before its resources can be released.
Retired leases use private retention keys, so a loaded portable reference with the
same stable asset ID cannot resolve to the old working path or pixels. They remain
pinned by old writes/checkpoints/output readers, then release when those finish.
Qt also clears old session decode/cache entries before loading the new sources.
Normal close uses the responsive Save/Discard/Cancel lifecycle below. Resolve
unknown outcomes first; Save secures its revision, Discard deliberately abandons
unsaved work/checkpoints, and Cancel returns to the editor.
An owner disconnect is uncertain: keep Studio open and its producer leases intact;
this instance has no automatic owner reconnection or authoritative export after
owner death. Do not claim rejection or crash recovery. Memory-only pixels are lost on process
termination/power loss until a PNG or recovery session is durable. To roll back to
the old PNG path, first Save As, verify its dependencies and reopen that checkpoint;
never discard the live instance's accepted memory-only work.

## B2 boundary — planned only

C++ tiled raster resources, copy-on-write history and incremental compositing
are the next scoped stage; none is implemented here. Preserve the runtime/save
contract above and tool/lock/selection/Undo meanings below. Accepted tile versions
must remain immutable and pinned across history, output and requested saves.
Fallback/portable saving must materialize compatible pixels/dependencies; unavailable
native code cannot silently erase a layer or make an old session unusable.
Qt/Python authoring and the existing renderer stay. B1's owner-death/crash,
resource bounds and remaining interaction/cost limits are not solved by this plan.

## B1 preservation requirements

These meanings must survive B2 as well as B1, including still-open review cases. They
do not certify acceptance. Preserve the detailed operating requirements below:

- One Layers hierarchy, independent inline rows/stable IDs, transparent New Layer
  and atomic Library insertion/reparent. Direct tools work with settings closed;
  double-click focuses the shared tool sidebar.
- Shared Main RGBA with independent Brush/Pencil footprints and exact settings;
  Eraser/Smudge write selected own pixels, with automatic visible-artwork Smudge pickup. Preserve Sampler scope, connected Fill, explicit alpha/color,
  white/transparent no-target onboarding and cancellation.
- Ordinary raster lock protects own content/transforms, not unlocked children.
  Group lock protects its subtree without rewriting individual locks. Own/subtree
  eyes preserve choices. Protected multi-Delete blocks the whole deduplicated
  batch and creates one management transaction.
- Master opacity, effect `blend_strength` and stroke opacity stay separate;
  group isolation applies once. Keep native pixels/dimensions, originals, masks,
  source refs, transforms and authored blend/alpha/tool colors.
- Editor Undo/Redo recovers drawing and management in sequence; explicit scoped
  APIs remain. Copy/Deselect are local. Text Undo stays local. Tool/panel/eye/lock
  choices are not history; new edits clear the recovery branch.
- Preserve own versus descendant selection/mask scope, complementary Cut children,
  Extract copies, Keep/Remove, source-space placement, Curve provisional anchors/
  handles/closure/Apply/Discard, Crop sides/corners and current target/focus cues.

Exercise this with slowed saving, rapid input, failed/unknown outcomes and
replacement plus visible output; see [B1 acceptance](../ROADMAP.md#b1-acceptance-plan).
B2 native tiles are next; media scheduling and audio/timeline/export are later stages;
B1 adds neither new brush physics nor temporal video splits.

## A short review

1. Import PNG/JPEG, a supported video or GIF through File → Import media.
   Double-click/Enter a ready asset, or use its context action. Repeated activation
   selects its matching layer; **Add another instance** intentionally duplicates
   its use. Importing/assigning starts neither visuals nor audio.
2. Layers starts empty. The main **+** offers **Media Library / New Layer /
   New Group / Web Source**. New Layer is a transparent editable overlay. A row's
   **+** adds inside that specific raster. Its edit icon expands controls directly
   below the real row; other expansions remain independent. Frontmost is first.
   Drag rows to reorder/reparent; inline sibling arrows, Reparent and Ungroup
   retain placement. Drag Library references into Layers, including floating
   docks: choose Inside / Above / Top level and native working dimensions;
   Cancel retains artwork and existing asset IDs.
3. Edit an image directly in Composition Editor while output is stopped. Drag
   its body, corner handles or rotation circle. Wheel zoom, middle drag pan,
   Fit canvas and 100% affect the view only. The centre is the transform pivot;
   X/Y are percentages of the logical canvas, positive Y down. Numeric entry uses
   0.1 steps; explicit Increase/Decrease buttons avoid native spin hit-test
   ambiguity. Internal affine precision is retained. Slider release, drag release
   and completed mask each create one Undo operation. Escape/tab or focus loss
   cancels an unfinished transform drag. Text fields retain normal shortcuts.
4. Use **B Brush / P Pencil / E Eraser / U Smudge** directly on the selected
   still's own pixels. Its layer ID stays selected; originals are immutable.
   **V Select / M Rectangle / L Lasso / W Magic Wand** selects pixels immediately.
   Ctrl+C copies, Ctrl+X clears actual selected raster data after copying, Ctrl+V
   pastes an independent sibling above the active layer, Delete clears without
   replacing the clipboard, and Ctrl+D deselects. Drag selected pixels on the same
   raster; T transforms a whole layer. Edit Undo/Redo recovers the complete sequence.
   Layers context commands explicitly name layer/subtree operations. Existing saved
   masks remain compatible; C Crop has its own Apply/Cancel controls.

5. Group adjacent siblings to preserve order. Nested group transforms and
   visibility/lock affect descendants; group opacity/blend is applied once to
   isolated children. Reparent and ungroup preserve canvas placement. Ungroup
   refuses an opacity/blend/mask/crop whose isolation would change the result.
6. Start the existing compatible Main visual preview. World only retains the
   stack, Layers only uses black plus the composition, and World + Layers blends
   over the completed world. All three retain the underlying world's clocks and
   histories. Layers only is not a render optimization. Existing fixed/Native
   resolution and aspect fitting determine clean output pixels.
7. Select a video/GIF/sprite, expand its row and use **Playback (silent)** Play/Pause,
   Stop/restart, position slider, Rate, Loop/Ping-pong and in/out controls. Visual
   Pause freezes presented animation; visual Stop releases decoders and stops
   layer transport. Hiding a layer releases its decoder/frame resources, freezes
   elapsed time and retains its play intent for visibility restoration. Closing
   the editor or collapsing controls does not stop output. Reopening a session
   never autoplays video, audio or a browser.

Inline controls keep exact position, dimensions, scale, rotation, flips, Align,
Fit/Fill/Stretch, aspect and blend mode. Every row, including collapsed/unselected
Groups, always shows its own **master opacity**. It applies once to the completed
layer/subtree. **Effect contribution** is `blend_strength`: zero restores Normal;
full applies the saved blend. The former Blend opacity control was an alias of
master opacity, not a separate effect. Saved `opacity` and `blend_strength` retain
their values. Stroke opacity independently controls new own-pixel edits.

Canvas Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y recovers drawing of the **current layer only**.
An exhausted stack stops; it never removes a layer or recovers another layer's
strokes. Layers/Library Undo recovers creation, deletion, duplication, reparent,
ordering, transforms, crop/masks and structural Cut/Extract/Paste. Field patches
preserve later unrelated drawing; deletion recovery restores current content,
stable IDs and retained drawing recovery. Unfinished paths have preview-local
Undo. Text fields keep ordinary text Undo. Status/help names the recovery route.
Tool/panel changes and eyes/locks do not become history commands.

Only the actual keyboard-focus pane has a purple border. Brown row selection,
amber inline expansion and cyan active tool are separate cues. Ordinary raster
lock protects its own content/transforms; an unlocked child remains paintable and
renameable. A Group lock derives subtree protection without overwriting individual
choices. Group is a container, not a drawable target. Multi-Delete deduplicates
selected subtrees into one transaction; **any protected member blocks the whole
batch**. Right-click on an already highlighted row retains the batch.

Every Image/Paint/Artwork can retain editable own content and have children.
The first eye hides only own pixels; the adjacent subtree eye hides descendants
too, preserving each saved eye state. Group has one subtree eye. Lock is at the
row end; inherited Group protection is a chain symbol. New blank raster can be
added above or inside the current selection. Drag indicators offer before/after/
inside placement, auto-expand and auto-scroll; Raise/Lower and Front/Back act
within siblings. Move to Parent, Root or another raster/group compensates the
inherited affine to retain placement. Cycles and resource limits are rejected.
Aligned complementary pieces sum coverage inside the parent isolation. Moving,
painting, restyling or explicitly reordering a piece makes it an ordinary overlay;
the parent's opacity/blend still applies once to the completed branch.

G/R/S begins move/rotate/scale preview. Type pixels/degrees/percent, constrain
move/scale with X/Y, then Enter or left-click to accept; Escape/right-click cancels.
Scale preserves proportions by default; Alt allows unconstrained mouse scaling.
Shift snaps rotation to 15 degrees; the visible centre is the pivot. V selects,
C crops, H pans, Z zooms, Space temporarily pans while held on the focused canvas.
[ / ] changes brush size. Ctrl+D deselects; Shift+D duplicates; Ctrl+Z and
Ctrl+Shift+Z/Ctrl+Y undo/redo. The toolbar's visible shortcut reference lists this
map. Text/number/search fields and dialogs retain their ordinary typing.

One direct Composition toolbar provides Brush, Pencil, Sampler, Eraser, Smudge,
Select, Transform, Crop, Hand, Fill, magnifier-plus/minus and shortcut help. Drag its dotted grip
to float or dock on any edge; Qt placement is saved with the existing layout.
Single-click activates immediately. Double-click reveals/focuses the shared tool sidebar. Tools and hotkeys remain
active while the sidebar is hidden. There are
no generic Toolbox/Brushes/Selection launchers in Layers. Fit/native view and
Canvas Size remain in canvas context and view settings, with no selected-layer
prerequisite for sizing.

Brush settings use representative stroke presets beside compact exact native-pixel
and percentage fields. Brush/Pencil share Main color/alpha and retain independent size,
opacity, flow and footprint; hardness belongs to soft Brush/Eraser, strength to
Smudge. Pencil defaults to the existing crisp square footprint; optional Round
is now an actual crisp round dab. Previously Pencil ignored the shape field and
always painted Square. The cursor shows the chosen footprint. Eraser removes
alpha; Smudge automatically samples visible artwork and writes only the selected layer.
Brush/Pencil right-drag paints Secondary; the canvas never opens a context popup. Escape/focus loss cancels active input.

Drawing with no selected layer asks **Create a new layer?** once per gesture.
No changes nothing. Yes on an empty composition creates a white editable surface;
Yes in an existing composition clearly adds a transparent overlay. The active
tool is ready for the next gesture. Ordinary New Layer remains transparent.
Fill has its separate zero-layer confirmation: Yes performs the original click as
one complete creation/fill operation, rather than waiting for another gesture.
Locked, hidden, zero-opacity or incompatible targets explain the issue without
silently redirecting to a child. Allocation/write failure retains accepted state.
Every source stays at native dimensions; the incremental constraint buffer keeps
the full result. One completed stroke is intended to create one drawing command.
The B1 candidate submits completed snapshots asynchronously and orders accepted
history/publication independently of pending PNG writes. Queue/byte limits report
rejection; unknown outcomes retain recovery pixels. See the runtime/save contracts
above. Brush algorithms and source pixels are unchanged by this migration.

Sampler chooses Active Layer or Visible Composite, excludes checkerboard/handles,
and reports ARGB plus the receiving shared Main/Secondary channel. Empty/transparent/outside
content leaves colors unchanged. **Fill** arms a click-based bucket using the
chosen RGBA chip. Connected four-neighbor matching is default; tolerance and explicit
all-matching mode are in the sidebar. Crop/masks/selection constrain traversal and
exact coverage constrains writes. One changed fill has one drawing Undo; see above.

Select normally exposes whole-layer transform handles; its settings offer neutral
shaped pixel selection. Crop keeps rectangular side/corner adjustment. Cut
previews a boundary. Visible actions confirm selected pixels, keep/remove own
content, or Extract to child — keep source. Ctrl+Shift+J remains the explicit
destructive Cut-to-child route. These never clip ordinary raster descendants.
Rectangle, Square, Circle, Ellipse, Freehand, Polygon, Curve and Magnetic remain.
Select/Cut settings expose saved-mask Edit, Enable/Disable and Remove.

Curve anchors and tangent handles remain **provisional** until completion/Apply.
Drag anchors/handles to adjust; Open/Close and preview Undo alter the preview.
Enter, double-click or clicking the first anchor closes/completes. Cut retains a provisional boundary until explicit confirmation/extraction; masks
use Apply and Discard. Apply requires a closed area. Edit a saved mask to adjust it; Discard
retains the saved mask. Limits remain 128 nodes and eight own masks; Magnetic is
local gradient tracing. Native usability acceptance of this correction remains
with Robert; scripted checks are recorded in the correction handoff.

Moving video/GIF/sprite sources expose **Snapshot current frame (editable still)**.
This creates a managed sibling still for ordinary pixel editing, retaining the
moving source. Video playback remains silent. It does not edit every video frame
or split time. Existing Playback controls still own seek, in/out, rate and loop.

Native editing retains complete source pixels. New image activation offers
Native by default or an explicit separate resized derivative; originals are
unchanged. **Use source dimensions for canvas** is opt-in. Source working pixels,
logical Canvas Size, Visualizer Resolution and editor zoom are distinct.
Canvas Size context provides 16:9, 9:16, square/custom and proportional placement
or preserved pixel size/offset from the canvas centre. Canvas fits proportionally into output. Old sessions follow their
initial effective output-sized canvas, resolved once at load in this candidate;
later output changes preserve placement and saving stores the resolved size.
Fixed/Native resolution policy continues to determine actual renderer pixels.

Drop mixed local files onto Library, empty canvas or an artwork. Target drops
ask Add child / Add layer / Replace / Cancel. Replacement is explicit and
undoable; mixed import results identify each file. Duplicate references reuse
their identity. Successful items survive another file's validation failure.
No import/drop starts playback. Generated paint/extraction/derivative PNGs are
immutable external dependencies admitted against physical free space/headroom,
never pixel JSON.
Paint and extraction snapshots are internal resources, not visible Library
imports. Explicit working derivatives remain Library assets. Known prior writer
provenance migrates to internal classification; a SHA-like filename alone never
establishes ownership. No files are deleted by this migration. Current content,
history and previously saved sessions retain their dependencies. Only current
internal resources are sent to the editor and prioritized for validation.
Save/Save As copies only used managed dependencies into a sibling `.assets`
folder before atomically replacing session JSON; external originals remain refs.

Image/audio activation reuses existing commands. Audio selects the sole
AudioOwner and reveals Session Waveform without autoplay; repeated use retains
the audio playhead. Device capture is never replayed. Video/GIF/sprites currently
decode pixels only, even when a clip contains audio. **Video audio routing and a
multitrack/keyframe/cut timeline remain design decisions, not implemented controls.**
The proposed small next route is an explicit Use video audio action into the sole
Session Waveform source, with no simultaneous mixer or reverse video audio.

## Supported sources and appearance

PNG/JPEG retain EXIF orientation, premultiplied alpha and tagged-sRGB conversion;
untagged sources are assumed sRGB. Source pigments remain unchanged. Normal,
Multiply, Screen, Add and Difference use W3C source-over blending in the existing
display-encoded RGB pipeline. Normal keeps the accepted presentation; there is
no global linear-light conversion. Group masks/crops are in group-local canvas
coordinates; asset masks/crops are in source UV. Crop/mask, Fit/Fill, asset flips,
centre affine and parent affines are shared by editor and renderer.

Video is actual PyAV/FFmpeg decoding into shared premultiplied RGBA, uploaded by
the existing renderer context. Tested supplied H.264 clips are 736×400/24 Hz and
2558×1388/30 Hz. Extensions alone do not establish support: header plus a first
decoded frame is required; later failures are inline errors retaining valid pixels.
Right-angle orientation and sample aspect ratio are applied. SDR conversion uses
FFmpeg; PQ/HLG/BT.2020 HDR is rejected rather than silently tone-mapped. Alpha is
codec-dependent. GIF timing, transparent partial frames and disposal 2/3 were
checked against Qt decoding using an original variable-delay fixture.

Previously saved sprite sheets remain compatible PNG/JPEG references with their
saved grid, frame range, FPS and loop settings. Sprite creation commands are hidden
from Layers in this correction; there is no new sprite editor. Frames
are read left-to-right, top-to-bottom; every cell must contain pixels. Alpha and
the same transform/crop/mask/blend tools apply. Grid dimensions are integer-divided;
use evenly sized cells to avoid unused edge pixels.

Static glTF 2.0/GLB renders actual triangles in the existing GPU context. Supported:
node matrices/TRS, normals (generated if absent), UV0 base-colour textures/factors,
metallic/roughness factors, KHR_materials_unlit, OPAQUE/MASK and double-sided state,
repeat/clamp and standard texture filters. Its fixed orthographic frame has
directional/ambient lighting and independent yaw/pitch/roll, then normal layer
transforms. The editor's bounded geometry guide is explicitly simplified to
4,000 triangles; Visualizer draws the complete supported mesh and materials.
Rejects rigging, animations, morphs, compressed geometry/textures, vertex colours,
extra UV sets/maps/material extensions, emissive materials, BLEND transparency
and mirrored-repeat textures. Blender can export an uncompressed static pose to
GLB for this subset. Unreal-specific materials are not portable glTF materials.
Rigged/animated 3D requires an agreed animation/pose/material scope; it is pending.
Actual GPU model validation used an original triangle GLB, not Robert's own model.

## Library, sessions and failure handling

Collections name memberships of existing references; deleting a collection keeps
assets. Select a collection before Import, drag existing assets onto it, or use
Collection membership on selected assets. Removing membership keeps global refs.
Shift/Ctrl select ranges/toggle rows; focused Ctrl-A selects visible asset rows;
Delete removes unique selected references in one recoverable command. Filtering
hides empty categories but preserves discoverable empty collections. One removal
dialog summarizes uses and offers Cancel, Keep recoverable artwork, or Remove
affected layers. Undo restores IDs, memberships, layers and editing selection.
It never deletes an
original or unloads independently active audio. Refresh/Relink preserve stable
IDs and transforms; cancellation/failed relink keeps completed references.

Library version 2, artistic session version 5, composition version 4 and Qt layout remain separate. Composition v2/v3 migrates with stable IDs, source pixels, own visibility, masks and transforms; Paint/Image/Artwork needs no user conversion.
Sessions v1–v4 and Increment 1's assigned slots migrate, preserving IDs/settings,
discarding unassigned placeholder slots. Runtime handles/play state are not saved.
Original sources remain external; managed artwork dependencies travel with the
session's sibling `.assets` folder. Sessions are not full source asset packs. Saving does
not import or embed audio, nor save pending editor paths as completed masks.
Save/Save As retains in-memory history; reopening a session clears Undo/Redo.
Generation/session/revision guards reject late work after seek/replacement/load.
Still/model upload and available mask allocation failures retain the last
accepted composition and report an inline error. A first animated frame or
output-target resize can fail later; its last pixels are retained where available,
otherwise the world/neutral output remains, with an inline error. A missing already-resident image can remain visible; fresh output
cannot recover nonexistent source pixels. Relink or restore the reference.

## Practical bounds

128 visible library references plus up to 4,096 internal metadata records (8 MiB
registry file cap), 32 collections, 16 pending jobs; one validation worker,
one renderer still/model decode worker, one silent animation worker. A composition
has 32 layers/references, six nesting levels (raster parents included), 8 masks per layer/128 points per mask,
256 KiB JSON edit state; one owner keeps 64 aggregate commands/8 MiB of
serialized commands, latest recovery rows and nonhistorical flags across all
scopes, plus at most 256 MiB of unique managed native resources referenced by
retained history (estimated as width × height × 4). Current content remains
independently bounded by image/store budgets; trimming history does not delete it.
Raster data is not in history JSON. One private active stroke, one pending native artwork write and one queued
completed stroke are allowed; each native image buffer is at most 32 MiB, with additional
bounded encoding/validation temporaries. Pass 1 retires obsolete generated files
after their final history/current/read/job/save obligation; legacy and saved
dependencies remain protected. Space/write failure retains required accepted
content. These are component bounds, not total process memory guarantees.
At most four visible
video/GIF/sprite sources, 96 MiB aggregate native-frame reverse windows and
128 MiB double-buffer shared staging. There is no whole-clip preload. Long GOP
decode stops after 512 frames or two seconds of work and reports unsupported
seekability. A seek discards old-generation publications. Stop releases decoder
cache while retaining its stopped first frame; visual Stop releases all animated
sources. Startup/cancel/decoder calls can take time before their bounded return.

Images: 128 MiB compressed, 8,388,608 decoded pixels/8192 per side and device GL
limits, with no silent output downscale. Static/model CPU staging 128 MiB;
GPU residency/replacement staging 256 MiB; isolated full-output group targets
256 MiB; mask texture residency/replacement staging 64 MiB. Unused group
targets are released after edits. At large resolution/depth, a group can exceed
that budget. Models:
64 MiB local source/dependencies, 256 nodes, 64 primitives/200,000 vertices,
8 textures/4 megapixels per texture/32 MiB decoded textures. The editor caches
bounded library thumbnails, at most 64 MiB model data, 192 MiB aggregate native
editor images and 128 MiB mask cache. Editor rendering covers the visible physical
viewport up to 8 megapixels. 100% native detail compensates the selected source's
fit, crop and transforms and centres it; the least magnified direction reaches
one source pixel per physical screen pixel, retaining authored deformation.
hidden editor views do not read full shared video frames. These are component
limits, not a total process-RSS guarantee.

Reverse playback is functional but not universally smooth. In the retained
9-second middle-passage long-clip check, decoded changed frames moved in both
directions while cache stayed below 96 MiB; cache refills produced measured timing
tails. Reader sample timing is not presentation FPS. Component GPU and ordinary
swap-return measurements are under `work/media-composition-20261007`; neither
establishes full-world FPS, scanout, natural listening or multi-hour operation.
Playback exposes decode/refill time and warns about slow sources and high-rate
frame skipping. Rate changes preserve play intent, phase and valid resident
frames without requiring Pause. The large showcase remains refill-limited at
6×/12× in reverse. Native Add editor blending is substantially faster through
equivalent bounded-strip arithmetic, but dense large translucent compositions
remain heavier than Normal; this is not a world-renderer FPS promise.

## Web capability and dependencies

The supplied Loudman URL is a JavaScript embed page. A stopped Web layer records
its public URL, viewport/cadence, transparency and Retain last/Hide offline policy.
The optional implementation uses a single off-record Qt WebEngine viewport,
permission-denied/read-only GET/HEAD requests, no project/native bridge, file
access, popups, downloads or audible autoplay, two bounded shared frames and
2 Hz capture. **PySide6-Addons 6.11.1 installation is awaiting approval; browser
display/security/resource behavior has not been verified. This is a pending
integration, not a functioning Loudman claim.** Request-rate/cache/pixel caps do
not establish a hard Chromium RSS or response-download bound; that remaining
bound must be resolved during browser validation. No authentication tokens are
supported in saved URL/configuration.

PyAV 19.0.1 was installed with the exact approved binary/no-deps command; Qt was
not upgraded. PyAV code is BSD-3-Clause, while its FFmpeg wheel build includes
GPL codec components. Existing Qt is 6.11.1; proposed Addons must match it.
Qt WebEngine uses Qt LGPL/GPL/commercial terms plus Chromium third-party notices.
This pass authorizes no redistribution; codec/GPL/notices must be reviewed before
shipping a portable. Original GIF/sprite/GLB fixtures and implementation are local;
Robert's media originals remain untouched.

Methods and licensing sources: [PyAV 19.0.1](https://pypi.org/project/av/19.0.1/),
[PyAV license](https://github.com/PyAV-Org/PyAV/blob/v19.0.1/LICENSE.txt),
[FFmpeg wheel build](https://github.com/PyAV-Org/pyav-ffmpeg),
[Qt image animation](https://doc.qt.io/qt-6/qimagereader.html),
[Qt WebEngine licensing](https://doc.qt.io/qt-6/qtwebengine-licensing.html),
[W3C compositing](https://www.w3.org/TR/compositing-1/),
[glTF 2 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).
Qt Graphics View/UndoStack were evaluated; the QWidget editor shares normalized
affines and owner-held IPC history to avoid a competing persistent Qt scene.
Qt QMediaPlayer does not support negative playback rates; bounded PyAV windows
serve reverse pixels instead of an independent media-player/audio owner.

## Raster repair review evidence (2026-10-08)

See [actual-results handoff](agent-notes/raster-workflow-repair.md) for source
identity, task-only diff, executed checks, retained failures, native observations
and limits. That report retains its task-time dirty source/status; the later
recovery is `0fb4c3f`. Review current Studio's unaccepted editor. User acceptance
and any later critic dispatch remain separate.

The earlier composition transport/time-range idea remains later scope, not the
next batch. B1 is implemented/uncommitted; B2 is next. Linked video audio, temporal splits
and multitrack mixing need separate clock/storage/audio briefs in the
[staged plan](../ROADMAP.md#later-planned-stages--separate-builder-assignments).


## B2 native raster/editor continuation - 2026-10-08

The uncommitted B2 candidate retains128-pixel immutable C++ tiles, copy-on-write
history, exact region editing, B1 transactions, revision-pinned portable PNG saves
and the existing output publication path. The continuation corrects redundant
CPU presentation refresh, adds an optional exact float32 region kernel, and hosts
renderer-owned GPU projection/composition in the same Qt authoring Canvas.
Integer-aligned physical native pixels use GPU composition and damage; filtered,
rotated/fractional views retain exact Qt reference sampling with cached GPU display.
There is no mandatory display-loop readback. The Layers editor label distinguishes
these routes; `ZERAWAVE_EDITOR_GPU=cpu` selects the compatible CPU editor at open.
Native initialization failure also preserves a usable CPU Canvas.

This is a reviewable candidate, not Robert acceptance or a universal performance
claim. Latency, memory, failures and remaining limitations are bound in
`docs/agent-notes/b2-tiles-20261008.md` and `work/b2-completion-20261008`.
Build, ABI, resource bounds and secured fallback are in the
[B2 implementation contract](NATIVE_RASTER_B2.md).

Requested saves also export any referenced immutable source snapshot restored by Undo, even if its external file changed or disappeared. This uses a private managed reference in the saved document; working layer IDs, original Library identity/path and history remain unchanged. Source snapshots still consume no background PNG job. Failed snapshot export leaves the requested save failed and its resources pinned for Retry/Save As.


## Pass 1: sustainable working storage and normal shutdown — 2026-10-09

This uncommitted candidate extends the starting recovery implementation; Robert
owns acceptance. Passes 2–4 and B3 remain unimplemented. Native ABI 1, the loaded
DLL, session version 5/composition version 4 and intended source pixels are unchanged.

`artwork_store.py` uses bundled SQLite to index PNG bytes, distinct payloads,
reservations, cumulative committed writes and reclamation. Writes reserve actual
encoded bytes against destination-volume free space and leave 64 MiB for metadata,
temporary/checkpoint publication and recovery. The former default 512 MiB disk
ceiling is removed from working writes and portable/source/recovery dependencies.
`ZERAWAVE_ARTWORK_BUDGET_BYTES`, when explicitly configured, is a disclosed per-folder
PNG budget including retained/protected files; it is not a default or lifetime
stroke count. Memory, decoder, queued-byte/job, native-version and history limits
remain independent. Free-space checks cannot reserve space against unrelated
external writers; an actual OS write failure remains recoverable and truthful.

Current scene, retained Undo/Redo/structural rows, active PNG jobs, publication
readers and requested saves retain immutable resource leases. Failure/retry entries
do not independently retain an expired revision. Internal metadata expires with
its last legitimate reference; late registry callbacks cannot recreate it.
Only an indexed `working` payload with explicit provenance and no remaining
current/history/job/read/save/Library obligation can be retired. Retirement intent
is committed before unlink; normal reopen can finish it. Dependencies, public
Library originals, legacy/unowned PNGs, prior projects and evidence stay protected.
Interrupted active payloads stay conservative; this is not owner-death artwork
recovery. Windows owner byte locks distinguish live writers from abandoned journal
reservations. Startup reconciles at most 4,096 directory entries, then 64 entries
per tick; external changes are audited incrementally every 30 seconds. Reclamation
attempts at most 32 files per normal tick. Protected legacy space is shown separately.

Preview, owner acceptance, output publication and durable PNG/save completion are
separate states. Known queue pressure prevents starting the next stroke and explains
that no edit was accepted. A completed stroke rejected by admission has no retained
recovery copy and must be redrawn after drain/Retry; no automatic resubmission.
Accepted unsaved current/history/save work remains retained while its obligations
exist. Retry acts on owner failures; Save As secures its frozen requested revision
and retained recovery dependencies before redirecting future working writes.

Normal close resolves submitted/uncertain edits and unfinished gestures before the
Save/Discard/Cancel decision. Save awaits the requested durable session/revision;
failure or newer accepted work leaves the editor open. Discard explicitly abandons
unsaved work and pending/failed checkpoints, cooperatively cancels writers, and
waits for their actual completion before releasing readers. Cancel keeps the
editor usable; cancelling a save waits for its real terminal outcome. Close phases
are visible. Unresolved edits, save/cancellation or owner writes return to an open
editor after 15 seconds rather than imply completion. Opaque OS I/O may finish
later; its reader remains protected. Renderer/media/audio stop precedes resource
release. The GUI observes owner process exit and actual worker-thread exit before
accepting window close. Forced termination is an exceptional fallback, never
normal-exit evidence. Bare legacy `close` still refuses unresolved raster work;
the normal GUI route explicitly supplies `clean` or user-authorized `discard`.

Standalone `raster_storage_shutdown_test.py` exercises accounting, conservative
cleanup, interrupted writes, expired failures/metadata and isolated process exits.
Actual results, source identities, raw failed trials and remaining limitations
belong in the newest section of `docs/agent-notes/b2-tiles-20261008.md`.

## Direct blank children, captured drawing and artwork images — 2026-10-10

The **small + in a layer row** now creates a selected transparent drawing child
under that clicked stable row in one structural Undo/Redo operation. It does not
open the media chooser or require PNG durability before drawing. Existing parent
pixel dimensions, crop/flip/fit and parent placement are retained. Ordinary raster
own-content locks permit a new unlocked child; a protecting locked Group rejects
the operation. The **large + above Layers** still offers other media types, and
Library import/drag retains the existing placement choices. Creating a child is
explicit; ordinary painting still edits the selected layer's own pixels.

Brush/Pencil/Eraser/Smudge include the final release position. Their view/source
conversion is pinned for the gesture; focus loss, a changed view or cancellation
discards only private unaccepted work. Windows captured mouse history is bounded
to 64 points and filtered to the gesture/event time window, ordered and deduplicated.
Missing OS history uses delivered Qt positions. No invented smoothing points or
additional trailing buffer are used. Brush/Pencil/Eraser can batch captured segments
with the existing pixel policy; Smudge keeps sequential visible-artwork pickup.
Preview and accepted pixels use the same effective path. Fast motion can still be
angular when the OS/Qt delivery supplies too few points; measured stalls and actual
history limitations are in the source-bound report. The compositor reuses proven
unchanged backdrop pixels inside its existing bounded cache at the same Qt sampling
phase; image dimensions and intended pixels are preserved.

The Composition **floppy Save icon** writes the Composition canvas as an ordinary
image. **Save As…** selects another file/format. Layers' context menu offers **Save
artwork image / Save artwork image As…** for the selected stable layer(s). First Save
opens scope, filename/folder, format, output dimensions and canvas origin. Repeat
Save updates that scope's assigned output. Composition, own layer(s), branch and
selected branch set have separate destinations, persisted as optional
`artwork_outputs` in compatible version-5 sessions (older sessions default empty).
Duplicated IDs receive no overwrite destination. Save As confirms an existing file;
cancellation/failure leaves the prior association and good output. Imported originals
are never automatically destinations and are protected by the dialog. Existing managed/accepted artwork source
paths are also refused, including a saved output subsequently imported as a source.

Composition output uses authored canvas dimensions. Own output excludes children;
branch includes them; multiple selection defaults to aligned branches with overlapping
descendants included once. Layers use tight transformed/cropped geometry bounds at
one authored canvas pixel per output pixel, including off-canvas content; the dialog
shows origin and dimensions. Hidden content is excluded. Ancestor transforms,
opacity, masks, isolation and the existing blend/Add policy apply. Group-only own
output has no own artwork; choose branch for its children. The existing 8192-side /
8 MP image capacity rejects larger output explicitly, without clipping or downsampling.
Chrome, checkerboard, handles, cursor and selection outlines are excluded.

This saves the **Composition drawing canvas artwork**, which does not show the
Visualizer's reactive world. Available current decoded video/GIF/sprite/Web/model
images are frozen through their existing reader ownership and named in the dialog.
Unavailable visible sources fail clearly; no editor placeholder is encoded. This
is a still image, not video or a session export.

PNG retains alpha with exact decoded straight-RGBA pixels under the existing
premultiplied conversion/rounding policy. JPEG uses an explicit adjustable opaque
background (white default) and lossy writer quality. Other installed Qt writers
are offered only after a small encode/decode probe; BMP/PPM/JFIF are opaque,
PGM is grayscale, PBM/XBM/WBMP monochrome, ICO/CUR limited to 256 pixels per side,
XPM palette-limited and flattened by this writer policy, and WebP can be lossy.
PNG/TIFF/WebP/ICO/CUR retain alpha
as confirmed by the installed probe. Extension and actual writer format agree.
Writer quality is exposed where supported; a flattening background never changes
editable artwork.

Image save freezes a consistent accepted revision, reconciles submitted work and
refuses an active preview. It pins immutable readers, composes at save time with
the existing reference compositor and runs at most two jobs through one ordered
encoder/writer. A temporary file is flushed before atomic replacement; success and
destination metadata follow completion. Later edits remain unsaved for that image
target. **Cancel save** requests cooperative cancellation and reports the actual
outcome; a completed replacement remains success. Normal close waits for image
jobs/readers and real worker exit; failed/cancelled saves leave Studio open. Opaque
I/O still may finish after a bounded wait, retaining its readers. Image Save never
marks the editable session saved. **File → Save session** and **Retry saving**
retain their distinct session/recovery purposes and Pass 1 safeguards.

This is an uncommitted review candidate. Robert owns acceptance. See the dated
[actual results](agent-notes/b2-tiles-20261008.md) for exact identities, raw evidence,
failures, matched timing limits and guarded rollback. Capacity Passes 2–4, metadata/
protocol scaling, higher Library/layer counts, storage location/relocation controls
and deeper stress remain deferred and must be retained by ROADMAP's owner through
the manual handoff; this feature note is not another plan. New Session and B3 are
outside this pass.
