# B2 native tiled raster and renderer-owned editor candidate

This is a development/experimental candidate authorized for publication October 9,
not Robert acceptance. Generated DLLs remain local; source/build instructions are
published and the compatible fallback remains available. The
actual-results note and newest manifest in
`work/raster-reliability-20261009-1791583929312117900` bind this uncommitted repair.
The preceding published correction remains bound to its original usability-performance pack.
Earlier `work/b2-completion-20261008` and `work/b2-tiles-20261008` packs are preserved.
ControlOwner remains logical document/history authority; Qt remains the authoring
UI; the existing renderer owns graphics. No owner-death recovery is provided.

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

## Build and backend selection

From `C:\ZeraWave`, run `native\raster\build.ps1` in PowerShell. It uses the
installed Visual Studio 18 Build Tools developer environment, explicitly selects
MSVC toolset 14.51.36231 / SDK 10.0.26100.0, and builds x64 C++17 `/O2 /fp:strict /EHsc /MD
/LD /W4` outside source at `work/native-raster/x64/abi1-fill-20261009-v2/zerawave_raster.dll`.
Compiler `/Bv`, DLL architecture/dependencies and SHA256s are recorded there.
The previous tested `abi1` and `abi1-completion` DLLs remain in place.
Existing DLL output is refused; use a fresh `-OutputName` for another build.
Validate that output through `ZERAWAVE_RASTER_DLL` in a new isolated process. There is no
installation, global PATH change, binding framework or redistribution.
Runtime imports are the installed Microsoft VC/UCRT runtime and KERNEL32.

Start Studio normally through `C:\ZeraWave\run_zerawave_studio.vbs`. The Layers
pane retains actionable fallback/errors; internal backend status records ABI/path.
Composition has no Details strip or diagnostic labels.
`ZERAWAVE_RASTER_BACKEND=b1` forces the compatible path in a newly opened process;
`ZERAWAVE_RASTER_DLL` nominates a DLL for an isolated validation launch. Missing,
unloadable, incompatible-export/ABI or wrong-architecture DLLs select fallback.
Selection is fixed for that process. Never unload/switch native resources live.
The new default prefers `abi1-fill-20261009-v2`, then `abi1-completion`, then `abi1`; an older ABI-1 DLL remains
usable with the original NumPy region-constraint fallback. `zw_constrain` is an
optional export, preserving all existing descriptor/handle/struct ABI meanings.
Its one-call region calculation reproduces NumPy float32 multiply/add and
nearest-even rounding, with SSE2 and strict compiler arithmetic. It holds no
versions, allocates no storage, and restores the thread rounding mode.

## Focused Fill/tree/UI correction contract — 2026-10-09

`zw_connected` and `zw_cancel` are optional ABI-1 exports, without changing any
existing structures, descriptors, resources, saved formats or renderer ownership.
Connected-region input/output are packed n-byte bitmaps, dimensions <=8192/8MP,
exact buffer lengths, valid seed and finite remaining budget <=30s. The native
queue schedules each pixel once and uses at most n uint32 entries (32 MiB at8MP)
plus the caller's8MiB result. Allocation/error/cancel leaves artwork untouched.
Cancellation checks every4096 visits and before/after traversal. An aligned native
interlocked flag is owned by FillCancel; ordinary threading.Event callers use a
5ms watcher that is stopped/joined on return. No per-pixel Python callbacks occur.
No partial result can pass the existing source/scene/revision/selection completion
guard. B1 and older exports keep the bounded Python span traversal.

Similarity uses inclusive channel bounds and transparent-black canonicalization.
Changed tiles reuse existing exact `zw_constrain`; B1 byte weights match all
16,777,216 byte/paint/coverage combinations against reference float32 rint. Busy
phases correspond to actual worker stages; no percentage or acceptance/durability
claim is invented. The whole-path benchmark separately observes worker delivery,
owner acceptance, standalone GPU publication/readback and PNG completion.

Tree refresh reuses unchanged row widgets/IDs. Pixel reader handles do not affect
control signatures; stacking order alone is reconciled by item position. The global
input filter skips unrelated layout/style events; mouse/key/focus handling remains.
Existing decoder/frame thumbnail updates remain. Row-specific
Delete pins its branch, confirms with defaultNo, validates scene/session/revision,
then commits one complete closure or rejects all protected content. Existing
32-layer/depth6 capacity is unchanged. Composition local Edit/Details and selection
method dropdown requirements below are superseded; main Edit remains. See
STUDIO_MEDIA_COMPOSITION.md and the newest actual-results note.

## Resource and transaction contract

ABI 1 is cdecl; fixed-width integers, explicit byte lengths and stride, caller
buffers, structured error return. `ZwRegion`, `ZwTile`, `ZwStats` and `ZwError`
are declared in `native/raster/raster.h` and mirrored in `native_raster.py`.
No C++ exception escapes. Native context pointers, pixel pointers and version IDs
are process-local. They are never transport identities. Context close refuses
while versions remain retained. Version creation/import/patch owns one reference;
retain/release manage additional native readers. Python NativeImage owns that
reference. Immutable versions hold shared_ptr tiles; a segment copies each touched
tile once per batch. Ordered patches and neighbourhood reads preserve Smudge
ordering. Existing Qt dab mathematics and encoded-colour pixels remain policy.

Transport is immutable named Windows mappings: descriptor layout `tiles128-v1`,
ABI, family identity, dimensions, complete ordered 128-pixel tile table, each
tile's name/coordinates/length/stride, RGBA8 premultiplied sRGB bottom-up. Partial
edge tiles have exact lengths. Producers reuse surviving mappings for unchanged
native tile IDs. Owners validate/open all mappings and import/share tiles before
acceptance; admission failure releases every new lease. Pending commands, current
content, history, save checkpoints, workers and output publication pin resources
through B1's existing retention sets. Renderer staging opens its own mapping
handles until upload completes. No writable producer mutation after submission.

B1 operation stream/sequence/ID, revision/session/target validation, duplicate
outcomes and unknown-ACK reconciliation are unchanged. Native handles do not
enter history JSON. History transaction copies preserve the resource-accounting
callback without copying the resource owner. Semantic caps remain 64 commands,
8 MiB serialized history and 256 MiB unique raster allocations. Shared tile names
are charged once across history versions. Resources report unique mapping bytes
and logical version bytes separately. Failed writes and pinned checkpoints retain
accepted resources and can retry/export through B1's compatible recovery route.

## Bounds and broad operations

Native core: 384 MiB unique tile pixels and 256 live versions per process;
dimensions <=8192/8MP; patch/read batch <=2048. Owner resources:384 MiB unique
pixel bytes,512 MiB page-rounded mapping bytes and256 retained resource rows;
pending PNG jobs:16 /256 MiB unique tiles. GUI transfer reservation:128 MiB
conservative logical bytes; current editor image reservation:192 MiB.
CPU projection cache:128 MiB LRU; global-phase scratch:128 MiB separately.
Masked source cache:128 MiB. Family Qt presentation images are separate from
native history storage; they update changed tiles and have a separately enforced
512 MiB process-wide budget, including the cold prepared spare for private edits.
They are not counted as unique history tile pixels.
Transfer-name metadata is capped/pruned at65536 entries per exported family;
import collision metadata has a fixed262144-entry bound and rejects further
admission safely. Native import weak caches prune expired entries before work.
Existing renderer bounds remain128 MiB CPU staging reservation,256 MiB texture
residency/staging,64 MiB mask textures and256 MiB group composition targets.
These are separate budgets, not a total process-memory guarantee.

Decode, broad fill/cut/resize, compatible materialization and PNG/export may still
touch the whole image. Brush/Pencil/Eraser/Smudge segment preparation reads bounded
regions including sampling halo, applies existing Qt policy in source coordinates,
and atomically installs both private versions only after allocation succeeds.
PNG encoding holds its family presentation lock throughout encoding so concurrent
older/newer pinned checkpoints cannot exchange pixels. Persistence is not required
before authoring/renderer publication. No per-dab/pixel ABI call or callback.

## Renderer-owned editor projection and exact compatibility routes

`renderer.EditorSurface` owns editor GL passes and resources inside Qt's current
OpenGL widget context. Qt retains widget/context/framebuffer lifetime. This
adapter starts no world window, audio owner, playback loop or second editor.
CPU Canvas and GPU Canvas share the same authoring methods and ControlOwner.
`editor_projection.EditorProjection` extends the existing ImageLayers resource
stage. It consumes immutable GUI-local native versions plus scene/view/DPR;
cross-process native pointers never enter it. The Visualizer retains the existing
validated mapping publication and ACK protocol, independently of PNG durability.

Integer-aligned physical 1:1 source pixels, aligned crop edges, own masks, flips,
encoded blend modes/strength/opacity, nested isolation and partition semantics
use GPU projection and exact integer composition. Changed tile identities map
through every affected row to bounded viewport damage. Geometry/flags/hierarchy,
crop/masks/view/DPR and sizes invalidate previous footprints. Distinct revisions
of one family have distinct texture keys; rows may safely show older/newer pixels.
Geometry and immutable tile-ID metadata are cached. Sources clone a predecessor
on GPU and upload changed tiles; bounded source/display spares and framebuffers
are reused. Only successful complete staging replaces the prior display.
Failed staging retains the previous complete frame and accepted document.
Structural depth reduction, resize, context destruction and close reclaim targets.

Qt smooth filtering, fractional sampling, rotation/scaling and masked/cropped
Groups use the exact global Qt reference projection in this renderer-owned stage.
It uploads a changed projection once and presents its cached GPU texture thereafter.
This compatibility route preserves the existing arithmetic/filter phase; it is
not wholly GPU filtered composition. The Layers label distinguishes native GPU
projection from GPU display with exact Qt filtering. No tolerance was widened.
There is no compulsory per-frame CPU GPU readback. Explicit visible-composite
sampling reads four bytes; captures/test readbacks are separate instrumentation.
Original Qt checkerboard, tools, handles and canvas boundary clipping remain.

Source residency/staging including its spare is bounded at256MiB. Existing
float16 group target pairs are bounded at256MiB. Independent RGBA8 current/spare
displays use at most64MiB at the existing8MP viewport cap; clipping texture at most
32MiB, reference CPU staging128MiB, plus its original bounded CPU caches. These
separate budgets and driver/context working sets are not a total-memory guarantee.
The GUI GPU context increases process working set; report that separately from
unique document/history tiles and measured latency. CPU fallback remains available
through `ZERAWAVE_EDITOR_GPU=cpu` in a fresh process. Unsupported/missing native
backend and offscreen Qt use CPU Canvas. GPU initialization failure replaces its
host with that same CPU Canvas while retaining authoring/document state.

The corrected CPU route refreshes a precise cumulative dirty rectangle only when
its presentation matches the exact predecessor tile IDs. Skipped paints accumulate
damage; older pinned readers or unrelated revisions use conservative changed-tile
runs. Immutable tile/history data is untouched. Broad reads, decode/import, global
Qt filtering, PNG/export and broad operations may still touch the full image.
The existing Visualizer still clones full source textures and draws full group/
world targets; output projection scheduling is outside this correction.

## Save, fallback and safe rollback

Saved sessions remain version5 with composition4 and ordinary portable PNG
dependencies. Tile descriptors/native handles are not a proprietary saved format.
For backend rollback, first Save As/recovery-export the requested accepted revision,
wait for its durable outcome, verify every dependency exists and reopen a secured
copy through the fallback. A newer edit must not replace the pinned checkpoint or
be marked saved by it. Keep unsaved accepted work alive until this succeeds. Do not
reset/clean the checkout or switch DLLs in a running process. Memory-only accepted
work is not crash durable; owner process death remains outside this increment.

## Earlier B2 usability extension — workflow requirements SUPERSEDED below

Optional `Pixels` masks store exact compressed 8-bit full-resolution coverage,
validated before admission, bounded to 120 KiB encoded per mask and the existing
256 KiB scene state. Regional mask reads share one implementation across Qt, native
strokes and renderer-owned output/editor projection. Optional `media.editor` size
metadata is owner-validated and pinned in ordinary session saves. Old scenes default
to empty presets; old crops keep their existing placement. New crop compensation
and child-placement changes form one management transaction. Named-source pickup
uses immutable gesture-pinned readers and bounded regions, leaving ControlOwner
authority, resource lifetime, exactly-once admission and failure recovery intact.
No native ABI/build or compulsory frame readback change. See the current operating
section in STUDIO_MEDIA_COMPOSITION.md and this pass’s source-bound actual results.

## Earlier four-correction extension — workflow requirements SUPERSEDED below

Details starts collapsed without disabling any live information source. All real
tool settings use the existing saved-layout dockable/floating color sidebar;
selection/refinement and saved-mask controls share it. No advanced popup remains.
Fill is click-based four-connected RGBA similarity by default (tolerance32), accepts
transparent seeds and uses the visibly chosen paint chip. Own/Group/selection
coverage constrains both traversal and exact feathered writes at native dimensions.
One changed fill follows existing drawing transactions/history/publication and PNG
durability. Typed transient work is bounded to existing8MP/8192 dimensions with a
30s computation guard; no saved-mask encoding limit is imposed. One worker request
is source/scene/target/selection/session/revision bound and cancellable. No native
ABI/build, history schema, output interface or saved-format change occurs.
Zoom-in/out magnifiers preserve factors/limits; legacy Zoom activation is removed.
See STUDIO_MEDIA_COMPOSITION.md and the dated B2 correction actual results for
fixtures, costs and unresolved limits. Automated checks do not grant acceptance.

## Selection, clipboard and automatic Smudge preservation — 2026-10-09

This later authorized correction supersedes previous named-source pickup,
per-tool Main, Cutout/confirmation/child shortcuts and Canvas-only drawing Undo
requirements. Preserve old stored masks/pieces and existing native/transaction
formats; no ordinary Cut/Delete operation may create a new removal mask or child.

`editor_pixels.py` owns transient selection/gesture and immutable OS clipboard
origin. Completed raster changes use existing `save_paint` and ControlOwner
transactions. Paste inserts an independent sibling above the active layer using
captured source-pixel world placement, with no destination mask/crop inheritance.
Clipboard token/hash invalidate origin on external replacement. Protected/capacity/
export failures preserve artwork/clipboard. Esc/click/Copy/Deselect add no history.
The existing History offers an editor sequence across drawing/management; scoped
APIs stay available, and new edits clear the redo branch. Internal managed immutable
PNG dependencies may share paths under distinct IDs; external paths remain unique.

Shared Main/Secondary migration retains saved swatches/palettes and independent
tool sizes/stroke settings; the dated channel contract above governs both buttons. Fill's exact pixel/resource/authority contract stays intact; the later measured
Fill correction above supersedes the former implementation restriction. Existing saved toolbar identity remains, with
full dock height, resize grip, width reflow and actual-overflow scrolling.

Automatic Smudge extends `cpu_projection.py` regional artwork sampling and reuses
ordering/isolation/blends, crop/masks and existing brush physics. Immutable scene/
frame pins plus evolving target preview prevent double-target feedback and stale
delivery. Unsupported visible frames and exhausted 4 MiB footprint /16 MiB sample
capacity reject explicitly; no whole viewport/world/checker pickup. Source pixels
remain unchanged and only the editable selected raster receives an operation.

Standalone checks: selection_clipboard_smudge_test, smudge_composite_test,
editor_corrections_test, editor_usability_test, raster_workflow_test,
studio_editing_test; publication/transactions/projection/resource checks cover
affected interfaces. Bind actual executed results and limits in the latest report;
Qt, native pixels and standalone GPU are distinct from physical user acceptance.

Requested saves also export any referenced immutable source snapshot restored by Undo, even if its external file changed or disappeared. This uses a private managed reference in the saved document; working layer IDs, original Library identity/path and history remain unchanged. Source snapshots still consume no background PNG job. Failed snapshot export leaves the requested save failed and its resources pinned for Retry/Save As.


## Natural short-stroke persistence/recovery correction — 2026-10-09

This later correction preserves B1/B2 immutable snapshots, ordered admission,
history and revision-pinned saves. Native ABI/DLL and stored session version stay
unchanged. Current-only Qt resource publication uses an optional compact tile-name
table; ControlClient reconstructs the exact ABI descriptor before any consumer.
History/save/publication leases remain owner-retained and Undo republishes the
requested current resource. A post-acceptance publication failure is uncertain,
never an admission rejection or permission to dispose accepted pixels.

Owner resources share one handle per unique immutable tile. Resource references,
pending PNG jobs and save pins govern lifetime; borrowed worker/save readers drop
all exported array views before release. Allocation accounting caches only
admission-validated immutable tables and preserves unique raw/mapping/job budgets.
Pending-job count, queued bytes, native versions, history and GUI transfer limits
remain separate. Pass 1 below replaces the former 512 MiB disk-store ceiling.

Persistence uses the existing NumPy/Qt alpha conversion and lossless PNG Sub/zlib
encoding, retaining native dimensions, exact pixels, physical pixel aspect and ICC
metadata. Faster compression can produce larger PNGs. Pass 1 below uses indexed
accounting and physical free space with explicit reservations/headroom. Provenance
and last-reference retirement replace the earlier running-owner-only rule;
protected originals, dependencies, legacy files, sessions and evidence never retire.

Known capacity prevents starting the next Brush/Pencil/Eraser/Smudge preview and
explicitly says no edit was accepted. Admission races may still reject a completed
stroke; it is not retained for automatic replay and must be redrawn after drain or
recovery. Expected rejected outcomes remain in the ledger/log and editor status;
they do not steal canvas focus through the runtime-error pane. Unexpected failures
and accepted-but-unpublished uncertainty remain diagnostic errors. A separate
persistent message shows pending/failed writes even during continuous input.

Retry exercises the actual owner and cannot create space in a genuinely full
store. Explicit Save As secures its requested revision and every retained unsaved
accepted resource, indexing additional PNGs in its `.assets` folder. Failure leaves
accepted work/history and checkpoint pins intact. Only durable completion in the
same active session moves future writes to `<session>.rasters/<session-id>`;
existing references/leases stay immutable. Load uses a new private working-store
namespace after its existing old-context recovery checkpoint. Compatible reopen
still uses portable PNG dependencies; artwork history remains the running owner's
existing history, not a new serialized history feature. Owner-death recovery and
File → New Session remain outside this correction.

`raster_short_strokes_test.py` is the natural press/move/release/reclick regression
(no worker barrier or injected write fault). `raster_reliability_test.py` covers
controlled pressure, real filesystem failure, real Retry, resource/export lifetimes,
history, saved pixels, colors and canvas menu boundaries. Bind actual runs and
capacity rejections in the dated B2 report; passing recovery is not a no-overload
guarantee or Robert acceptance.


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

## Captured drawing and ordinary image Save — 2026-10-10

Native ABI 1/DLL remain unchanged. `raster_edit.path()` batches captured
Brush/Pencil/Eraser vertices in one bounded union region using unchanged brush,
constraint and coverage kernels; Smudge keeps sequential pickup. Input owns at most
64 Windows history points and never reconstructs hidden cursor motion. The final
release endpoint follows the same preview/pixel policy. CPU filtered projection
reuses exact backdrop prefixes inside the existing 128 MiB dependency-complete LRU;
the supported fallback uses the existing Add reference when native Add is absent.

Still-image saves retain private immutable NativeImage readers through save-time
composition/encoding and use the existing Qt reference policy at authored pixels.
There is no compulsory per-frame readback or native build change. Optional top-level
`artwork_outputs` keeps session5/composition4 compatibility. Image Save is distinct
from portable session Save and owner Retry; Pass 1's stores, retirement, pressure,
accepted-work ownership and shutdown remain the preservation contract. Exact pixels,
resource/timing results, native/fallback cases and limitations are bound in the
newest dated B2 actual-results section; Robert acceptance remains pending.
