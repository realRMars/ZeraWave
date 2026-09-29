# Nine visual treatments — implementation ledger

Scope: three materials, three spatial effects, three final-image Envelopers; existing Studio, live colors, saved sessions, palette cycling and explicitly authorized Main authored/default integration. No commit/build/dependencies. Prior color-inspector rollout is uncommitted and preserved in the starting snapshot.

## Lineup

- Ink Archipelago: flowing pigment islands with narrow veins and dark channels.
- Interference Silk: crossing wave bands and contour interference, not metallic objects.
- Cellular Mosaic: drifting cell interiors, seams and internal growth.
- Elastic Lenses: bounded local magnification/compression pockets.
- Braided Flow: crossing coordinate shear lanes.
- Nested Windows: local nested coordinate windows, not a centered tunnel.
- Prism Assembly: image facets displace and reconstruct the composed scene.
- Digital Bloom: localized block/scan/ordered-color quantization.
- Chromatic Memory: bounded whole-image temporal reconstruction, separate from Echo.

## Research (observed locally; no copied code or assets)

- C:/MilkDrop 3.37/Milkdrop3/presets/altunenes - MilkDrop2077 - Tri-Bloom RGB.milk: warp stage samples the previous frame and decays it; composite stage samples the resulting image. The name alone did not establish a reusable bloom algorithm.
- C:/MilkDrop 3.37/Milkdrop3/presets/MilkDrop2077 - Pink lines.milk: composite stage mirrors source coordinates, samples blurred/current imagery and reshapes colors. Inspiration: recognizable source-image transformation rather than unrelated overlay.
- C:/ProjectM Library/src/libprojectM/MilkdropPreset/MilkdropPreset.cpp: distinct previous/current framebuffer ownership and final composition.
- C:/ProjectM Library/src/libprojectM/MilkdropPreset/FinalComposite.cpp: composite shader with a pass-through fallback. Inspiration: isolated final-image processing with fallback.
- C:/ProjectM Frontend/src/FPSLimiter.cpp: wall-clock frame timing includes pacing; GPU shader time alone is not end-to-end FPS.
- MilkDrop LICENSE.txt restricts commercial use; projectM LICENSE.txt is LGPL 2.1. No implementation or asset is imported; all new expressions are original. No claim is made about per-preset license compatibility.

## Design and preservation

Append IDs; retain legacy mask bits. Existing explicit lists never gain items. Held authored scenes stay untouched. Main default and explicit Authored will use the expanded paced show, as requested; custom lists stay explicit. Spatial effects alter existing supported material/detail coordinates, not world depth. Spatial colors inherit the material.

Envelopers: one renderer-owned final stage, at most 1920x1080 proportional targets, scene RGBA8 plus two alternating RGBA8 history/output targets (10.55 MiB at 720p, 23.73 MiB at 1080p). No read/write alias. Disabled path bypasses allocation. Reset on startup, resize, backward seek, >0.5 s gap, held-state change and disable/re-enable; release on shutdown. Main transitions intentionally retain a short <=0.18 s image trail, never Echo history. Allocation failure falls back to the unprocessed scene with a reported warning. This intentionally processes resolved image depth, not world geometry.

## Status / resume

Inspection/research complete. Implementing materials first, then spatial, Envelopers, cycling/Studio/Main, verification. User artistic acceptance and continuous audiovisual review are not claimed.

Evidence root: C:\ZeraWave\work\nine-treatments-20260928-223811
