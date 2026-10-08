# Studio media composition

Run `C:\ZeraWave\run_zerawave_studio.vbs`. This uses the current working checkout;
there is no separate exported build. View recovers **Media Library**, **Layers**
and **Composition Editor**. The renamed Layers dock keeps its `image_layers`
layout identity and existing ADS docking. Layers has one hierarchy view with inline controls. Composition Editor is
an additional dock. Its layer-only checkerboard preview never renders a second
world. Visualizer remains clean output.

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
   **K Cut** draws an automatic nested piece: rectangle/ellipse/freehand completes
   on release; polygon/curve/magnetic completes with Enter, double-click or path
   closure. One Undo restores the parent region and removes the child; Redo
   restores both. Cut the selected child again for a grandchild. Its initial
   geometry and complementary transparency reconstruct the parent's appearance.
   **M Marquee / L Lasso** makes a neutral selection; use Ctrl+J Copy to Child or
   Ctrl+Shift+J Cut to Child. Ctrl+C/X copies/cuts selected own pixels directly;
   Ctrl+V creates a new editable raster. Without a raster selection these commands
   use layer/subtree scope. The status line identifies that scope.
   Keep/Remove are separate editable own-content masks. They never clip a raster
   parent's descendants. Crop changes selected content; Canvas Size changes the
   logical document. Invalid/empty cuts retain their preview with an explanation.
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
Select, Crop, Cut, Hand, Zoom, solid Fill and shortcut help. Drag its dotted grip
to float or dock on any edge; Qt placement is saved with the existing layout.
Single-click activates immediately. Double-click toggles one remembered settings
window for that tool, once. Tools and hotkeys work with settings closed. There are
no generic Toolbox/Brushes/Selection launchers in Layers. Fit/native view and
Canvas Size remain in canvas context and view settings, with no selected-layer
prerequisite for sizing.

Brush settings use representative stroke presets beside compact exact native-pixel
and percentage fields. Brush/Pencil retain independent color, alpha, size,
opacity, flow and footprint; hardness belongs to soft Brush/Eraser, strength to
Smudge. Pencil defaults to the existing crisp square footprint; optional Round
is now an actual crisp round dab. Previously Pencil ignored the shape field and
always painted Square. The cursor shows the chosen footprint. Eraser removes
alpha; Smudge samples its own layer. Right-drag erases with the current brush
footprint; Shift+right-click opens context. Escape/focus loss cancels active input.

Drawing with no selected layer asks **Create a new layer?** once per gesture.
No changes nothing. Yes on an empty composition creates a white editable surface;
Yes in an existing composition clearly adds a transparent overlay. The active
tool is ready for the next gesture. Ordinary New Layer remains transparent.
Locked, hidden, zero-opacity or incompatible targets explain the issue without
silently redirecting to a child. Allocation/write failure retains accepted state.
Every source stays at full native dimensions; the incremental stroke constraint
buffer preserves the full native result. One completed stroke is one drawing
command. One pending write plus one queued completed stroke remain bounded;
stale/failed writes preserve accepted content.

Sampler chooses Active Layer or Visible Composite, excludes checkerboard/handles,
and reports ARGB plus the receiving last Brush/Pencil. Empty/transparent/outside
content leaves colors unchanged. **Solid Fill** replaces the selected own editable
RGBA pixels with the explicitly chosen color/alpha, constrained by crop, masks and
current shaped selection; whole layer otherwise. Stroke opacity does not apply.
It has one drawing Undo. It is a solid fill, not contiguous-region flood fill.

Select normally exposes whole-layer transform handles; its settings offer neutral
shaped pixel selection. Crop keeps rectangular side/corner adjustment. Cut
settings choose boundary shape and outcome: Cut creates a child and removes own
region; Extract copies to a child; Keep/Mask are aliases of the existing own Keep
mask; Remove is an own Cut mask. These never clip ordinary raster descendants.
Rectangle, Square, Circle, Ellipse, Freehand, Polygon, Curve and Magnetic remain.
Select/Cut settings expose saved-mask Edit, Enable/Disable and Remove.

Curve anchors and tangent handles remain **provisional** until completion/Apply.
Drag anchors/handles to adjust; Open/Close and preview Undo alter the preview.
Enter, double-click or clicking the first anchor closes/completes. Main Cut commits
its structural transaction automatically on completion; masks use Apply and
Discard. Apply requires a closed area. Edit a saved mask to adjust it; Discard
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
previous effective output-sized canvas; saving freezes that current size.
Fixed/Native resolution policy continues to determine actual renderer pixels.

Drop mixed local files onto Library, empty canvas or an artwork. Target drops
ask Add child / Add layer / Replace / Cancel. Replacement is explicit and
undoable; mixed import results identify each file. Duplicate references reuse
their identity. Successful items survive another file's validation failure.
No import/drop starts playback. Generated paint/extraction/derivative PNGs are
immutable external dependencies (512 MiB working-store bound), never pixel JSON.
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
bounded encoding/validation temporaries. Retained immutable files are not pruned
when history is trimmed; a full store reports an error and retains committed
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
and limits. Run the existing Studio from C:\ZeraWave to review the current dirty
candidate. User acceptance and any later critic dispatch remain separate.

The smallest proposed media follow-up is a shared composition transport using
the existing AudioOwner clock and explicit per-layer time ranges. Temporal splits
would then edit time-range records, with linked video audio routed through that
same owner. This needs an agreed synchronization/storage brief. Multitrack mixing
is a later audio-architecture proposal, not implemented by these raster repairs.
