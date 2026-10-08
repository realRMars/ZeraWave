# Raster workflow repair — actual results, 2026-10-08

Implemented in the latest actual candidate at `C:\ZeraWave`, against the captured
dirty baseline. Ready for Prompter/Bob to prepare the established review brief;
Robert's acceptance remains pending. No other chat was messaged, no worker/critic
was dispatched, and no commit, push, release or shared planning rewrite was made.

## Visible result and implementation

Imported Image, legacy Paint/Artwork and extracted stills now paint, erase alpha
and smudge their own native pixels while keeping the selected stable layer ID.
The managed immutable writer stores raster versions; Undo/Redo switches those
references. Originals stay external. No automatic Paint child or user conversion
is required. Blank raster can be created above or inside the selection.

K makes a nested cut automatically on rectangle/ellipse/freehand release or
polygon/curve/magnetic completion. A single history command removes the own
region, adds/selects the aligned child and reveals its ancestry. Repeated cuts
make grandchildren. Own masks do not clip raster descendants. Aligned pieces sum
premultiplied coverage before the parent's opacity/blend isolation. The GPU
interpolates premasked texels consistently on both pieces to avoid curved halos.
After moving, painting, restyling or explicit ordering, pieces use ordinary
overlay composition. This reconstruction guarantee concerns the initial cut;
later edits intentionally change content. Mask editing stays Keep/Remove, rather
than accidentally executing another automatic Cut.

Neutral M/L selections do not modify pixels. Ctrl+C/X/V uses selected raster
pixels when a selection exists and layer/subtree scope otherwise. Ctrl+J copies
to a child (duplicates without a selection); Ctrl+Shift+J cuts to a child. The
status identifies the current target/scope. Tree thumbnails, nesting, cyan
selection, Lock, Own and Branch are distinct. Own hides only this row; Branch
retains descendants' saved eye states. Drag indicators/auto-expansion/scroll and
sibling Raise/Lower/Front/Back coexist with Parent/Root/another-parent moves.
Reparent preserves affine placement and rejects cycles/depth overflow.

G/R/S previews accept numeric px/degrees/percent, axis constraints, confirmation
and cancellation. Shortcut routing excludes names, numbers, search and dialogs
and prevents editor keys reaching BONK/Hold. Tooltips/reference show the requested
map. Brush has size/hardness/flow/stroke opacity; Pencil is crisp; Smudge uses own
pixels with strength. Selection, masks and crop constrain drawing. Eyedropper
explicitly samples own pixels or visible composite, excluding checkerboard and
handles. Source-aware footprints follow rotation/crop/flips and DPI.

Tools/Brushes have vector square tiles, scaled icons/labels/hit targets, scrolling
overflow, remembered singleton geometry and an explicit native resize grip.
Shared reusable additions are `brush_stroke`, `constrained_edit`, the raster
branch/complementary-piece helpers and vector tool icons in the existing modules;
no new editor, renderer, audio engine or dependency was introduced.

Audio activation uses the existing sole AudioOwner/Session Waveform without
autoplay. Video stays silent, with existing seek/in/out/rate/loop controls. Moving
video/GIF/sprite pixel work requires an explicit editable still-frame snapshot;
the moving source remains. Composition schema v4 accepts v2/v3, keeping old IDs,
source state, masks/transforms/visibility. Artistic session v5 and Library v2
remain separate. Managed edit/clipboard/frame dependencies stay out of Library.

## Source and diff identity

HEAD before and after: `fe1a7b74f791fbfcc1879798e5e944be50ae061f`.
HEAD is not the dirty candidate identity. Evidence root:
`C:\ZeraWave\work\raster-workflow-1791441809561890600`.

- `baseline.json` and `baseline/`: pre-edit Git status, hashes and source copies.
- `final-source.json`: baseline/final SHA-256 per scoped file, diff hash and syntax.
- `task-only.patch`: this assignment against its own dirty baseline, including new tests/note.
- `preservation.json`: all 280 other captured source/docs/skills files unchanged.
- `INDEX.md`: precise result/artifact paths and evidence distinctions.

Six production modules changed: composition, artwork, image_layers,
studio_composition, studio_qt and media_registry. Three existing fixture scripts
were repaired and two standalone raster checks added. Only assigned media
instructions and this task note were documented. Existing unrelated dirty work
and shared root documents remain byte-identical to the captured baseline.
The baseline inventory covers source/docs/skills, not every pre-task binary or
user state file. Immutable-original hash equality was checked on the synthetic
edit fixture. Native review uses separate library/layout/artwork/owner logs;
source photograph/video were read and never targeted by writes. No frozen build
or user session was opened for editing.

## Checks actually executed

- `composition_test.py`: contracts, history, hierarchy, bounds/migration passed.
- `composition_canvas_test.py`: Qt 1.5 DPR, inverse/crop/flip/geometry and actual
  QTest handles/one-command gestures passed, including the completion rerun.
- `image_layers_test.py`: actual RTX GPU blending/isolation/masks, allocation
  failure retaining accepted output, revision/session, resize/release passed
  after the shader correction.
- `media_registry_test.py`: persistence, headers, missing/relink and session
  compatibility passed. `media_recovery_test.py`: service rollback branches with
  injected/mocked failures passed; this is not native recovery interaction.
- `studio_media_test.py`: real Qt widgets/QTest activation/drag/history, actual
  decoded video play/pause, stopped sole AudioOwner, collections/reference Undo,
  stale-owner guards, session roundtrip and dock-area preservation passed.
- `media_frames_test.py`: real short/long H264 and GIF variable-timing/disposal,
  nine-second ping-pong/reverse windows, seek/freeze/stop/hide/cleanup passed.
  No audio output or continuous listening was performed.
- `raster_workflow_test.py`: real isolated ControlOwner and scripted Qt mouse/key
  workflow, own raster byte change/alpha erasure, child/grandchild cut/paint,
  visibility, reparent/order, typed G/R/S/cancel, text isolation, clipboard,
  palette scaling, transformed cuts, immutable write failure, continuous active
  second stroke across first completion, stale target rejection, mixed per-file
  import failure, video snapshot and saved v4/v3 migration passed. Normal/200%
  offscreen DPI runs and final grip/mask checks are retained separately.
- `raster_workflow_pixels_test.py`: 20 Rectangle/Ellipse/Path/real cubic Curve ×
  five blend cases, rotated 23°, flip, nonuniform scale, crop, opacity .57 and
  gradient partial alpha passed on the actual compositor. Before/after cut max
  GPU difference ≤3/255 and Qt ≤2/255; two nested cuts reconstruct within 3/255.
  Own/branch visibility changes actual GPU output.
- Python AST syntax and tracked `git diff --check` passed; the task manifest also
  checks newly added whitespace and generates a scoped patch for untracked code. Ten existing-file task diffs also passed no-index whitespace checking; Git returns 1 for differences and emitted only normal LF/CRLF warnings.

Qt-to-GPU whole-image equality is not claimed. The existing transformed outer
source-edge discrepancy is measured before and after: max 13–95 byte values
depending on blend, average below .4 byte. The new cut did not increase those
maxima; retain this baseline edge/sampling limitation. The cut-specific tolerance
above applies to before/after reconstruction, not full editor/output equality.

## Native input and limitations

`native-final/input.jsonl` records spontaneous desktop mouse input, and named
state snapshots retain own-pixel versions and stable IDs. Native B/E/U editing,
two automatic rectangular cuts, visible moved grandchild with parent hole,
Undo, own-only hiding, whole-branch hiding and restoration were observed. These
ran on the pre-final-focus UI source (identity from the earlier smoke source
manifest); final focus/resize changes were separately validated below.
`native-verified/source-identity.json` binds the production UI before four validation-message dashes were restored to baseline encoding; algorithms are unchanged and the contract test was rerun after this text repair; native
automatic Cut/following transform and palette grip checks use that run. Actual
desktop DPR is 1.0. The 200% and 1.5 DPR runs are simulated Qt DPI, not an OS
settings change or second physical monitor. Full native per-action coverage of
all ten acceptance steps is not claimed; clipboard/reparent/save/mixed-media and
wide/tall sizing are scripted Qt/contract evidence. The helper rejects drag
endpoints outside the bounded palette screenshot; native minimum resizing was
observed, larger/wide/tall growth is verified through Qt resize events.

Small/large/wide/tall Qt sizes 220×240 / 720×600 / 800×220 / 220×800 gave Tools
32 / 88 / 57 / 64 square logical pixels; Brushes 56 / 88 / 88 / 88, with scaled
icons and scrollable controls. Actual native Tools reached 180×120 with 32-square
tiles. Labels switch to under-icon at sufficiently large tiles; smaller tiles
retain accessible names/tooltips. No OS DPI/privacy settings were changed.

## Resource evidence

RTX 3070 Laptop GPU; 1280×720 canvas/output, 320×180 native fixtures, 12 warm
draw+`ctx.finish()` samples per depth. No visual world or audio ran. Desktop Qt
review was open, power/thermal conditions uncontrolled; no matched FPS or scanout
claim. Retain maxima rather than quoting medians alone:

| Nested raster depth | Layers | Median ms | Max ms | Composition target bytes |
|---|---:|---:|---:|---:|
| 0 | 2 | 1.307 | 2.123 | 14,745,600 |
| 3 | 5 | 3.284 | 3.971 | 58,982,400 |
| 6 | 8 | 4.925 | 6.439 | 103,219,200 |

At depth six, targets are 98.44 MiB, still textures 1.76 MiB and masks .33 MiB.
Current bounds remain 32 layers/references, six nested parents, eight masks,
128 nodes, 64 history commands/8 MiB JSON, 256 MiB compositor targets, 64 MiB mask
staging, native 8-megapixel images and 512 MiB immutable store. Full-resolution
native raster edit copies/encoding can be much slower and larger than this small
fixture. One active, one pending write and one queued completed stroke are bounded;
extra gestures while both completed buffers wait report busy. Files retained by
history are not pruned when history trims. No total process-RSS, unlimited nesting,
multi-hour soak or global frame-rate promise is established.

## Retained failures and checks not run

Initial `regression/RESULT.json` retains a 75-second isolated smoke timeout from
the newly introduced native-size modal in its fixture, and a missing self-created
GIF fixture name in the animation test. Fixture repairs and successful reruns
are under `final-checks/`. Earlier workflow iterations retain a real numeric
transform NumPy-scalar contract failure, repaired by converting saved affine
numbers to Python floats. `gpu-final`, `gpu-fixed`, `gpu-debug` and `gpu-probe`
retain real curved-filter/interpolant failures; `gpu-partition` and `completion/`
pass after using consistent premasked interpolation on both pieces. Early native
state export encountered a harness deque JSON error (native/failure.txt); later
harness state/input export works. `qt-pixel-verified/FAILURE.txt` retains a fixture read before asynchronous raster decode; adding the readiness wait yielded `qt-pixel-final/RESULT.json` with actual Brush/Smudge byte changes and Eraser alpha reduction. The first desktop run was stopped by Robert
with Escape; resumed only when he said “try again”. Native helper bounded-drag
rejections are limitations, not passing resize proof.

No full application/world regression suite, natural live-music listening, audio
device playback, linked video audio, multitrack mix, synchronized timeline,
scanout/FPS acceptance or Robert artistic acceptance was run/claimed. Shared
renderer/audio source remained unchanged, so unrelated worlds were not recaptured.

## Review walkthrough and smallest follow-up

Open the existing Studio from `C:\ZeraWave\run_zerawave_studio.vbs`. Use View to
show Media Library, Layers and Composition Editor. Import a still and use B/E/U;
its selected ID stays. K-drag/release a piece, paint it, K-cut again, then V or
G/R/S to move pieces. Undo/Redo should restore each single gesture. Toggle parent
Own and Branch independently, restore, reorder siblings and move to Parent/Root.
Try M/L selection, Ctrl+C/V and Ctrl+J/Ctrl+Shift+J. Resize Tools/Brushes with
the visible grip; type G/R/S in Name to confirm it stays text. Repeat a cut after
crop/flip/rotate/opacity/blend, save/reopen a new session and use a moving-media
frame snapshot. Import audio/video separately; imported audio stays stopped and
video is labelled silent. The existing Main output can composite the same saved
stack; this task did not promote or alter visual worlds.

Smallest coherent proposal: share the existing AudioOwner composition transport
clock and add explicit per-layer time ranges/storage before synchronized playback
or temporal splits. Linked video audio needs explicit routing into that sole
owner; multitrack mixing needs a separate architecture/storage brief. These are
proposals only. This raster Cut is a spatial region operation.

Return this actual-results pack to Prompter/Bob in the current reply; they decide
the review brief/approved critic route. Robert decides user acceptance. No score
or successful test substitutes for it.
