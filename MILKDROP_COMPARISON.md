# MilkDrop comparison: material memory experiment

Date: 2026-09-27. ZeraWave baseline: cf1d561.
Status: local source/document inspection, not a visual or listening comparison.
No renderer, audio, preset, dependency, or accepted appearance changes.

## Evidence inspected

MilkDrop installation: C:/MilkDrop 3.37.
- Milkdrop3/docs/milkdrop_preset_authoring.html: warp, composite, decay,
  previous-frame textures and textured shapes.
- Local preset text scan: 391 .milk files under Milkdrop3/presets.
  The earlier installation-wide count of 394 includes files outside this folder.
- Text markers appeared in 390 files for main-image sampling, 266 for blur
  sampling, 352 for audio bands, 379 for warp shaders, 391 for composite shaders,
  175 for enabled custom shapes, and 113 for enabled custom waves.
  These are lexical counts, not proof of execution or visible feedback; comments,
  unused code and composite-only samples can match. .milk2 files were not parsed.
- Targeted examples: fiShbRaiN + geiss - witchcraft; Evet + Geiss - Chrome -
  MilkDrop2077 001s; cope - drove through ghosts to get here; Flexi - bouncing
  balls [double mindblob neon mix]; Altunenes - MilkDrop2077 - circuit network9.
  No preset code or assets have been copied into ZeraWave.
- ZeraWave renderer.py initialization/render/cleanup; dream.frag material
  substitution and gathering; preview_layers.py catalog; audio_frame.py;
  current handoff and visual identity. Production tests are under app/visuals;
  root shader_test.py is a separate existing untracked file, not the main harness.

## Findings and implications

1. Persistent simulation and display treatment are separate in MilkDrop.
   Warp output persists; composite treatment does not. This makes it possible
   to display brilliant highlights without feeding that brightness back forever.
   ZeraWave currently draws one procedural frame with no prior-image sampler.
   CPU event histories and integrated clocks already exist and must be retained.

2. Several inspected presets derive direction or shading from blurred image
   gradients. A structure can influence where its own image moves next. This is
   a useful candidate for emergent branching and folding, not merely a trail.
   It does not prove fluid simulation or better visuals without a motion review.

3. Color channels can act as evolving fields rather than literal display colors.
   The mindblob example separates field evolution from palette interpretation;
   witchcraft uses local gradients for movement and surface treatment. A ZeraWave
   experiment could store density and age, then shade them with its own palette.
   That would reduce the tendency for repeated RGB mixing to become gray/white.

4. Memory is not beat intelligence. The inspected files use bands and attenuated
   bands in diverse ways; this does not establish tempo/phrase understanding.
   ZeraWave's AudioFrame explicitly approximates rhythm with onset strength.
   Tempo confidence and phrase timing remain a separate future investigation.

## Recommended first experiment: Echo Weave (working name)

A fourth, experimental material: sparse colored seeds curl into branching folds,
accumulate a recognizable shape, then release into dark space. Quiet music keeps
slow motion alive; sustained energy accelerates transport; flux changes local
curl; onsets deposit bounded new seeds. Existing materials remain unchanged.

Smallest architectural extension to the existing renderer:
- Two modest-resolution floating-point textures alternate as read/write history.
  Never sample a texture while drawing into it. Start at 512 x 512 RGBA16F
  (approximately 4 MiB for the pair, excluding other resources).
- One small material update shader advances the field. Store density/age or
  related fields; apply the display palette when sampling the material.
- Sample the field in material coordinates through existing gathering so it can
  belong to a planet or corridor. Do not capture the entire screen: that would
  carry castle silhouettes, stars and terrain into inappropriate places.
- Use time-based transport and exponential decay with bounded substeps. A fixed
  per-frame fade would behave differently at 30, 60 and 144 fps.
- Keep it opt-in in Studio, absent from default Main cycles. When disabled, do
  not allocate/update history. Reset explicitly on replay restart/seek; define
  disable/re-enable behavior. Release resources with the existing renderer.
- Initial integration targets: app/visuals/renderer.py, a material-update shader,
  app/visuals/shaders/dream.frag, app/visuals/preview_layers.py and the existing
  Studio controls only as needed. Extend app/visuals/shader_test.py and
  app/visuals/replay_test.py rather than the root untracked copies.

## Acceptance before Main Blend

- Disabled mode remains pixel-identical to the accepted baseline.
- Identical seed/audio/timing produces repeatable runs; seek/restart clears history.
- Compare equal elapsed time at 30/60/144 fps for similar motion/decay (not exact
  pixel equality); pause/resume cannot cause a huge integration step.
- Long silence and prolonged strong inputs do not saturate white or freeze a
  dirty residual image. Verify finite values and bounded luminance/coverage.
- Inspect continuous quiet-to-strong-to-quiet passages using all three existing
  tracks, plus captures. Look for growth, release, rich color and intentional gaps.
- Inspect isolated material, Planet Canvas, Neon Corridor and regional handoffs.
  Watch for texture seams, apparent sliding, lost opacity and blurry detail.
- Measure update-pass GPU cost and total frame time with the feature on/off;
  also check enable/disable and resize resource lifecycle. No promised fps gain.
- Only after visual review consider adding it to Main's material selection.

## Scope and provenance

This is a proposal, not an implemented or visually verified effect. No MilkDrop
application was launched and no direct same-song comparison was performed.
The installed license distinguishes restricted MilkDrop 3 use from separately
licensed underlying components. This inspection is not a commercial license
clearance. Keep any implementation independently authored; review exact licenses
before any future reuse of code/assets. projectM may clarify implementation and
resource lifecycle later, but is not required for this first experiment.


## Local projectM source review (2026-09-27)

Inspected C:/ProjectM Frontend and C:/ProjectM Library. These are source trees,
not verified runnable installations. The library CMakeLists declares 4.1.4.
The frontend README describes an SDL2 reference application with rough edges.
No source was compiled, installed or copied into ZeraWave.

- Library src/libprojectM/Renderer/Framebuffer.hpp explicitly owns render targets,
  attachments and size changes. Zero/unchanged dimensions are handled separately.
- MilkdropPreset/MilkdropPreset.cpp: RenderFrame tracks current/previous buffers,
  marks the first frame after resize, updates blur from the warped image, draws
  shapes/waves and composites, then swaps buffer IDs. This confirms the importance
  of lifecycle and pass ordering for the proposed material experiment.
- src/playlist/README.md separates optional playlist management from the rendering
  core, which requests the next preset through a callback. ZeraWave should likewise
  keep discovery/UI separate from its existing musical director.
- The local frontend license identifies GPLv3; library COPYING identifies LGPL
  2.1-or-later. This records the supplied notices, not a complete dependency or
  commercial-use legal audit. ZeraWave adds no dependency on either package.

Immediate application: searchable Studio discovery built from existing catalogs,
plus TECHNIQUE_LIBRARY.md for ownership/reuse and a current workflow section in
DEVELOPMENT_STUDIO.md. Echo Weave stays a separate future rendering change.
