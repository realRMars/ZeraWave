# Studio media correction: actual results, 2026-10-07

Unaccepted, uncommitted candidate returned for Robert's manual review through
Prompter/Bob. No worker/critic was dispatched. No dependency installation,
publication, release or root checkpoint update was performed.

## Source and scope

Checkout: `C:\ZeraWave`, HEAD `fe1a7b74f791fbfcc1879798e5e944be50ae061f`.
The actual pre-task dirty candidate is captured in
`work/media-corrections-20261007/baseline.json` and `baseline/` raw preimages;
the previous candidate manifest SHA-256 was
`7365a136c4a0a569b386e1b4ae1ec003e8bcbbad0303d60b5b56ce1985cf0ba7`.
Use `final-source.json` for current task file hashes and preservation checks,
and `correction-only.diff` for the delta against those preimages, **not HEAD**.
Earlier media implementation and unrelated dirty work are not this correction.
Inputs are the four originals under `C:\ZeraWave\images n vids`; exact identities
and file sizes are in `inputs.json`. All four original hashes and the captured
user media library and both layout files match the initial bindings.

Implemented changes stay in composition/storage, existing editor/compositor,
media registry/frames, control service and scoped Qt input integration. No new
audio owner, world renderer, media backend or web/model expansion was added.
Shared audio/analyzer code and root planning files remain unchanged. The normal
`run_zerawave_studio` launcher loads this working checkout without a separate build.

## Stage results

1. **Fidelity:** removed the editor's implicit 512-pixel still and 1024-pixel
   animated preview reductions. Source-native pixels remain the edit/extraction
   source. Editor raster follows the physical visible viewport, up to 8 megapixels;
   100% compensates selected-source fit/crop/transforms and centres it; its least
   magnified direction maps one source pixel to one physical display pixel,
   preserving authored deformation. Checkerboard work is clipped to the visible
   viewport even at extreme zoom. Native is the default
   working option; a separately stored resized derivative and an explicit source
   canvas choice are available. Decoding/resizing/writing run on the bounded worker.
   Source working size, Canvas Size, Visualizer Resolution and zoom are separate.
2. **Editing and recovery:** explicit spin arrow buttons correct the reproduced
   upper-arrow hit issue, retain keyboard/typed 0.1 precision, and use live bounded
   preview with gesture-level history. Compact independent sections, floating
   Tools/Brushes grids, canvas view/context commands and contextual confirmation/
   preview Undo replace the permanent crowded toolbar. Fit compensates parent
   transforms and restores centre/scale/rotation; crop and masks remain. Fill is
   proportional; Stretch deforms. Corners/sides, exact size, Keep Aspect off and
   +/-90 degrees are supported. Layer clipboard uses fresh IDs/references; native
   text-field operations retain their own scope. An unfinished selected region
   explicitly asks for Extract before Copy. Blend strength 0 is Normal, 1 is saved
   blend behavior, separate from opacity. In-use removal offers Cancel, recoverable
   reference and removal of affected subtrees. Remove, Undo/Redo and composition
   send failures restore prior owners/history; failed removal does not cancel a
   pending validation. Relink remains explicit. Original files are never removed.
3. **Artwork children:** Image/Paint can become an Artwork container with imported,
   extracted and blank Paint children. Original visibility is independent; the
   container eye hides its subtree. Stable IDs, inherited and child transforms,
   isolated whole-container opacity/blend, order and collapse state persist.
4. **Selection:** drag crop with eight adjustable handles; distinct Keep, Remove
   and Extract; rectangle/square, ellipse/circle, freehand, editable cubic curves
   and native-gradient magnetic tracing. Magnetic tracing is a manual outline aid,
   not semantic background removal. Nodes/handles, deletion, close/reopen and
   preview history are supported in transformed source coordinates. Confirm is
   one operation; Escape/discard restores prior content. Extraction stores native
   content plus an editable Keep mask as an aligned child, allowing later recovery.
5. **Drawing:** transparent native Paint children, actual Pencil, selected-artwork
   Sampler, Eraser and dragged-pixel Smudge. Brushes exposes native size, color,
   opacity, Round/Square shape and smudge strength. One stroke is one Undo; cancel
   restores prior pixels. Immutable content-addressed PNG dependencies use a
   bounded 512 MiB store; portable save copies used dependencies to the session's
   sibling `.assets` folder. No raster blobs enter JSON. Generated provenance
   now survives asynchronous validation/relink and Save As relocations.
6. **Drops/canvas:** Library viewport and canvas accept up to 16 mixed files;
   artwork targets offer explicit Child/Layer/Replace/Cancel. IDs/duplicates and
   import validation are shared, no autoplay, per-file Ready/Duplicate/Failed/
   Cancelled results are bounded. An edit rejected by the owner reports Not applied,
   rather than falsely Added. Replace is undoable and failure preserves prior state.
   Canvas Size offers 16:9, 9:16, square/custom and proportional placement or pixel
   size/offset from canvas centre. Legacy sessions retain effective output geometry
   until Save freezes it into the explicit canvas. Output resolution stays separate
   and the logical canvas aspect-fits into it; context/docking/audio/clocks persist.
7. **Playback/Sprite:** rename to Playback; retain muted media context and loop
   dropdown. Rate changes preserve phase, play intent and valid resident frames,
   without a Pause requirement. Frame-publication ordering is separate from editor
   revisions, preventing frame residency from invalidating edits. Sprite context
   explains static/animated image elements and exposes image/GIF import and sheet
   conversion. Reverse buffers remain bounded. High-rate/source limits remain
   real and are exposed through decode/refill and frame-skipping status.

## Causes and measured evidence

Evidence root throughout: `work/media-corrections-20261007`.

**Native detail:** `native-gpu-1791433238623299500/RESULT.json` records the full
dimension chain on RTX 3070 Laptop GPU. Xeraphina is 1792x1008, mock-up 1825x1034,
short video 736x400/24 Hz/PTS 2.0; texture/internal/output at those dimensions.
Native editor 100% detail and complete technical GPU output are byte-identical
to the same decoded pixels (maximum difference 0). The video's independent
FFmpeg reference at matched PTS also matches. Qt and FFmpeg JPEG decoding differ
slightly (mean byte difference 0.604, maximum 16), retained as decoder/color-rounding
variation rather than a detail reduction. PNG alpha/edge, mask/crop/group and GIF
partial/disposal checks are separate. Enlargement of the 736x400 video to a large
display still exposes its original resolution; no upscaling/detail invention occurs.

**Add:** `fidelity-1791431193655625500/fidelity-add-1791431210855725700.json`
compares the exact old Add arithmetic with corrected bounded planar-strip integer
arithmetic, using the same two native stills, 0.7 opacity, 1280x720 raster/DPR 1,
36 fixed 0.2-canvas moves per arm, including Qt grab. Paint median: 261.72 ->
71.22 ms; p95: 283.16 -> 75.34; maximum: 289.82 -> 75.66. Pixel-work median:
236.59 -> 46.73 ms. Mean paint decreased about 73%. Random translucent pixel parity
is exact. This identifies CPU blend arithmetic as most of the measured editor
cost, not IPC or GPU. Normal's initial 747.7-ms cold sample is retained; its median
was 23.24 ms. Old 512-preview numbers are a different workload, not this speedup.
71 ms remains expensive for dragging dense Add compositions; no 60-FPS claim.

**GPU/output:** `gpu-checks-1791431553127/component-cost-1791431557251855900.json`
is an actual 1280x720 technical backdrop, vsync 1/144-Hz display, separate
query-instrumented GPU and ordinary visible GLFW swap-return arms. Two stills:
GPU median 0.272 ms, ordinary interval median/p95/max 6.937/7.247/7.534 ms.
Group+video: GPU 0.431 ms, ordinary 6.951/7.513/8.447 ms; no >50-ms ordinary
interval in either short arm. This is component evidence, not full-world FPS,
Qt editor timing, scanout, natural listening or sustained thermal validation.
Changed shared publications (~21.2/s) are distinct from ~144 swap returns/s.

**Video:** standalone matched before/after source-bound results are in
`rates-before.json`, `rate-run-1791431367143582500/rates-after-1791431390480366900.json`
and retained trial outputs. Native short clip publications at 1/6/12x were
20.83/52.92/53.33 per second; long 120-126 passage 11.25/3.33/4.17. Long decode
medians 45.92/295.22/237.57 ms, maxima 401.82/610.11/555.34. Cadence differences
are not a proved general speedup: background/thermal conditions are uncontrolled.
Widening the forward window and a two-thread reused converter were measured and
rejected, with results retained.

`visible-motion-1791432554745897400` is a maximized visible Qt sequence with PNG
captures/native window observations. Its recorded PTS came from periodic owner
snapshots, so its changed counts are telemetry samples, not image presentation.
The later `visible-motion-1791432838756738200/summary.json` excludes capture and
native automation during measurement and records actual shared-reader PTS.
Viewport 1898x1015/DPR 1; each case 4.5 seconds, first 0.7 excluded. Short 1/6/12x
changed-image interval medians 53.97/56.84/54.30 ms, p95 72.61/75.00/80.04,
max 80.45/100.36/131.51. Paint medians 38.70/41.27/40.52 ms. This maximized CPU
editor does not maintain the clip's full native cadence. Long 1/6/12x changed
interval medians 286.32/430.83/410.24 ms, max 1331.00/1340.95/1095.64; decode
tails approach 620 ms. The short source continues beneath the long source in
those cases, so they differ from isolated decoder tests. Both high-rate directions
and retained play intent were observed; normal-speed cases were too short to reach
the reverse boundary (covered separately by the 9-second media-frame check).
These are paint-return/image-update observations, not scanout. **Large-source
editor playback and high-rate reverse smoothness remain acceptance constraints.**

## Executed checks and failures

Current completed Qt workflow: `qt-1791433187760742800/RESULT.json` and image.
Actual Qt/owner with synthetic QTest covers spin/typing/keyboard, Fit/Fill/Stretch,
independent scales, rotation, layer clipboard/history, artwork visibility and
inheritance, crop/operations/extract, all four paint tools, save/reopen portable
dependencies, canvas policies/dock areas, recoverable removal, mixed/invalid/
duplicate drops, video child/no autoplay, and asynchronous derivative provenance.
Physical native checks in `native-after-1791430937509518300`: mouse up/down
buttons, keyboard Up, canvas Ctrl-C/V, Ctrl-Z and Ctrl-Shift-Z with recorded focus
and owner states. That does not physically validate every other tool/dialog.

`canvas-native-final-1791433158578/canvas-dpr.json`: offscreen Qt DPR 1.5, all eight selection
handles under crop/flips/rotation/parent, curve handle/delete/reopen/preview Undo,
magnetic native edge attraction and transformed-source native-detail zoom.
No physical multi-monitor/DPI change claim.
`recovery-1791433289790767300/RESULT.json`: exact service branches, real registry/
frame owners, injected remove/Undo/edit-send failure rollback, pending validation
survives failure, managed-path relocation rollback, and mock renderer
publication/edit revision separation.

Standalone checks passed during this correction: composition_test,
composition_canvas_test, image_layers_test (GPU), composition_gpu_test (GPU and
ordinary component), media_registry_test, media_frames_test (GIF disposal,
sprite, short/long range/reversal/cleanup), media_fidelity_test, media_rates_test,
media_recovery_test, media_corrections_test; waveform_drive_test,
band_analyzer_test, band_analyzer_view_test, preview_playback_test,
studio_scope_test, studio_audio_integration_test, studio_transport_test and
studio_qt_corrections_test. Final registry/clock/scope rechecks are under
`revision-checks-1791432625398`; earlier Qt/docking results under
`final-checks-1791431469513/cpu-result.json`, animation results under
`frame-checks-1791431640758/animated-media.json`. Audio integration/transport
checks use decoded PCM and mocked hardware/output; no listening acceptance.
Final AST/compile and `git diff --check` are recorded with the final source.

Failures remain in their unique run directories and logs. Early Qt assertions
covered clipboard/focus/geometry/test binding issues. A real thumbnail refresh
crash was reproduced in `qt-1791431993090128700` and the first visible probe:
setIcon emitted itemChanged, which committed a visibility edit and cleared the
tree during iteration. Signals are blocked during icon updates and unchanged
eye values are ignored; later workflow and visible passes completed without it.
Subsequent drop runs `qt-1791432363838558200`, `qt-1791432428118884400`,
`qt-1791432479896167700` exposed stale revisions; managed provenance loss and
reference-order-only changes were corrected, with honest failed-drop reporting.
The last failure's error-log write itself encountered cp1252 encoding; UTF-8
logging corrected that test issue. Recovery test revisions briefly failed from
a local import shadow and from comparing metadata after pending revalidation;
their run folders and observed failure descriptions are retained, not successes.
Windows COM exception 0x8001010d was logged at startup in several completed
Qt runs; no cause or full error-recovery guarantee is established.

One canvas test invocation accidentally used its historical default evidence
path and replaced `work/media-composition-20261007/canvas-dpr.json`; its previous
bytes were not bound/recovered. Subsequent runs use isolated task paths. All
supplied originals, user layouts/library and captured unrelated source remain
preserved; do not extend that assertion to every historical generated artifact.

## Robert's acceptance trial / remaining boundaries

Run `run_zerawave_studio`. Open Media Library, activate original Xeraphina with
Native working pixels and leave source-canvas choice off for an existing scene.
Canvas context -> 100% to inspect fine detail. Stack context -> Create child
layer -> imported image/blank drawing. Tools -> a shape, curved or magnetic
selection -> Extract -> green check. Hide Original independently, transform the
child and adjust Keep Aspect/exact size. Draw/sample/erase/smudge on a Paint child.
Crop and edit/disable its operation; Ctrl-C/V and visible Undo/Redo; Save As and
reopen with the sibling `.assets` folder retained. Try recoverable removal,
Undo and explicit Relink. Drop mixed files and examine individual outcomes.
Try Canvas Size and separate Visualizer Resolution without changing zoom.
Finally add the short video: Playback, In 2/Out 8, Ping-pong, seek/restart and
live rates. Compare the long showcase and read its inline refill limits.

Animated extraction intentionally asks for snapshot versus live-clipped semantics
if requested; this assignment's primary extraction is still artwork. HDR/new
codecs, actual multi-monitor/DPI transitions, every physical dialog/control,
continuous AV listening and multi-hour operation remain unverified. Loudman/Web
still needs the prior separately approved backend/security work; model subset and
saved config remain as before. No full-world performance problem is declared
resolved. Robert owns acceptance; passing checks do not accept this candidate.
Propose this checkpoint to the shared-document owner after review; no automatic
handoff dispatch or shared planning edit has been made.
