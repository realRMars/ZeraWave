# Studio palette controls — Bob / Engine room

Scope completed 2026-09-28 in C:\ZeraWave. Ready for user review; visual acceptance is pending.

## Files owned in this task

- app/visuals/studio.py: four presentation sections derived from the existing catalog; combined ordered list retained; optional material_isolation session map resolved into existing profiles only at launch; original lists/order/modes preserved; palette control moved; frozen sequential A/B controller and completion verification.
- app/visuals/replay_test.py: additive comparison window label and nonresizable window option only. Existing uncommitted palette routing retained.
- app/visuals/studio_test.py: isolation/session/order, comparison rejection/cancellation/completion, actual replay children, Echo reset/pixel reproducibility and visible minimum-layout checks.
- DEVELOPMENT_STUDIO.md: current instructions and exact review clicks.
- This note.

Existing uncommitted documentation, palette/shader/renderer work and cleanup deletions were preserved. No shared planning edits, commit, new dependency or build. Working tree remains dirty, as received, plus these edits. Git ownership was handled per command with safe.directory, not a global configuration change.

## Behavior and limits

Materials are the existing four MATERIALS IDs; field decorations are Shared FX, with existing catalog compatibility. World-specific experiments remain under World details. Sections do not create rendering passes or separate playback engines.

Isolation requires a custom Selected together/Meld/Cycle profile. It holds one material and all enabled nonmaterial rows together, explicitly suspending Cycle/meld. Restore removes the optional override. Authored stays authored until the user establishes an explicit list. Old sessions have no isolation override and keep original ordering and playback.

Matched A/B requires held Planet Canvas, material isolation and Test track input. It freezes settings, then launches fresh replay processes A Authored and B Soft Dream, seed 7301, fixed initial viewport, first 30 seconds or EOF, real-time pacing. Original session/input/duration/palette choices are not rewritten. Each new process resets audio analysis, mapping, clocks/events and Echo textures. Input SHA-256, expected frame count and full CSV measurement equality gate matched-complete status. Early exits/failures/cancellation do not silently continue a valid-looking pair. Live input and normal synthetic previews remain separate, unmatched review paths. Replay is silent.

The Studio minimum height is now 800 pixels (width 680) to keep the additional controls and status footer visible. The ordinary launch size is 780x820. No responsive-layout redesign was attempted.

## Checks actually run

- Full `.venv/Scripts/python.exe -X utf8 app/visuals/studio_test.py`: PASS on final code. Log: ../../work/studio-controls-final-check.log. Includes old v1/v2/v3 sessions, mixed ordering, live/synthetic/replay palette routing, Main defaults, real replay pacing and 57-second state-cycle replay.
- New actual Studio A/B child test: PASS using a two-second PCM segment of an existing decoded project track, ending naturally at EOF. Same measurements, cancellation stops the pair, incorrect expected count is rejected. Saved settings remain unchanged.
- Fresh GPU history test: three 61-frame 320x180 runs, Authored/Authored/Soft Dream. Authored pixels agree exactly; all three Echo texture bytes and clocks agree; Soft Dream changes rendered pixels. Captures: ../../work/studio-controls-check/20260928-015305/.
- Existing `shader_test.py --planet-palette-test work/palette-planet-review/authored-baseline.frag work/studio-controls-palette-preservation`: PASS. Authored preservation and palette scope across 36 states, four materials through synthetic quiet/strong/release, 640x360. Baseline was the existing Builder evidence file. Results/timings: ../../work/studio-controls-palette-preservation/checks.json; log: ../../work/studio-controls-palette-preservation.log. Timing excludes Echo update common to both palettes and is not an end-to-end FPS claim.
- Viewed a generated Soft Dream GPU capture. Inspected the real Studio UI, loaded the existing review fixture, exercised isolation and viewed palette scope/A-B controls. Corrected clipping discovered during that inspection; strengthened layout checks and reran the full suite. Final Studio left open, no preview running.
- `git diff --check`: PASS. Git reports existing LF/CRLF conversion notices in other workers' documents, no whitespace errors.

No unresolved test failures. No actual continuous audiovisual listening review was performed. Controlled-sample live-route tests, silent decoded replay, scripted GPU sequences and still captures are not artistic acceptance or continuous live-audio validation.

## User review

Use the exact steps in DEVELOPMENT_STUDIO.md. Load the existing work/palette-planet-review/studio-session.json fixture; Materials > choose material > Isolate material; Palettes > Authored or Soft Dream. For matched A/B choose Build & preview > Input: Test track, then Palettes > Run matched A/B. Restore materials returns the source selection/order/playback. Stop here for user review; no broader integration is implied.
