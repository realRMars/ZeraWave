# B2 native tiled raster and renderer-owned editor candidate

This is a development/experimental candidate authorized for publication October 9,
not Robert acceptance. Generated DLLs remain local; source/build instructions are
published and the compatible fallback remains available. The
actual-results note and newest manifest in
`work/usability-performance-20261009-1791554021606265100` bind the current correction.
Earlier `work/b2-completion-20261008` and `work/b2-tiles-20261008` packs are preserved.
ControlOwner remains logical document/history authority; Qt remains the authoring
UI; the existing renderer owns graphics. No owner-death recovery is provided.

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

Shared Main migration retains saved swatches/palettes and independent Secondary/
tool settings. Fill's exact pixel/resource/authority contract stays intact; the later measured
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
