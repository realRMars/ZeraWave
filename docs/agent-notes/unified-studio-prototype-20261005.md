# Unified ZeraphinaX / ZeraWave Studio: functional prototype

Builder actual results, 2026-10-05. Implementation stops at Robert's organization
review before substantial finishing work. This is the authorized first prototype,
not artistic acceptance, a release build or an approval to begin another milestone.
Robert confirmed the architecture/start checkpoint and desktop test availability.
No critic, additional worker, commit, push, Pages update or packaging was dispatched.

## Result and review

Launch `C:\ZeraWave\run_unified_studio.vbs` using the existing environment. Open
`C:\ZeraWave\work\unified-studio-20261005\prototype-review-session.json`, then
Start. The prepared session selects the existing Galaxy, Warbot Jazz, Real time,
Full quality, seed 7301 and full-track duration. Decoded replay is silent; live
system input uses the existing capture path. A first shader compile can take much
longer than a warm start; the existing progress/cancel window remains available.

The central visualizer hosts the existing GLFW window and OpenGL context, with
the renderer/audio owners still in the preview process. The left library uses
actual Main/Experimental catalogs, loaded session state and saved JSON paths.
The stacked right tools retain the complete Color Inspector, Audio Tuning with
Follow/Pin, and Mapping Monitor. The bottom holds the existing transport, a
decoded PCM waveform and exactly twelve actual FFT ranges. Charcoal surfaces,
copper selections and cyan meters follow the supplied reference. Existing setup,
effects, experimental, catalog, results and diagnostic views remain available.

Review these interactions in the running app:

1. Select a real catalog item; use Setup for source, quality and duration. Start
   returns the center to the visualizer. Pause/Resume, Stop, Hold and eligible
   Normal/Instant BONK retain their existing player semantics.
2. Use a panel area's ↗ to float its current tab and the floating Panel menu to
   redock it. Drag tabs between areas; use ⋮ for exact placement/order. Dividers
   resize areas, × hides a panel and View restores it. Closing a floating tool
   hides it; File > Exit shuts down the app and its owned preview.
3. Edit colors through Pigments, Palette timing and Presets & reset; scroll to
   every source role and wheel/value control. Audio Tuning retains exact gains,
   listening ranges, profiles, resets, dependency status, ACKs and explicit Save
   Authored. Scroll Controls to Profiles & authored; Listening & FFT keeps the
   existing spectrum display. Mapping's Full values retains the detailed table.
4. Type in a floating hex/profile field, use slider arrows, then dock the tool.
   Ctrl+S/O/N act on sessions outside editing; Ctrl+Enter starts, Ctrl+P pauses,
   Ctrl+Shift+S stops, Space BONKs and Shift holds outside protected controls.
   Native text/slider/button actions retain their own keys. Layout/focus changes
   release held controls.
5. Save a layout by rearranging panels, close/reopen Studio, and use View > Reset
   layout. Layout storage is separate from artistic sessions and resets only
   panel arrangement. Hidden left tabs collapse their area; View restores them.
6. Use ? by mouse or keyboard for complete explanations. Help > Diagnostics &
   logs retains bounded latest-run logs, diagnostics and results-folder access.

Diagnostic entry: `.venv\Scripts\python.exe -B -X utf8
app\visuals\studio_workspace.py`. The old `run_development_studio.bat` and
`app/visuals/studio.py` entry remain usable. Startup diagnostics are in
`work/studio/workspace-startup.log`; renderer logs remain per run. Launcher missing
environment and Python startup/callback failures have explicit diagnostic paths.

## Source, ownership and recovery

Accepted HEAD is `4a4f6e03ad2119e790e88d8338bac9412a139881`.
The preserved pre-task source is `work/unified-studio-20261005/baseline/` and
`baseline.json`, bound to the accepted 170-file app identity
`765543e7a927c1b4837695c8cb1c3b0215819d326d20354064ac196b107bec0e` from
`work/publication-performance-20261005/review-index.json`.
The final dirty source map, exact task-only patch including new files, artifact
hashes and provenance are in `work/unified-studio-20261005/review-index.json`
and `task-only.patch`. HEAD alone does not identify this implementation.

New components: `studio_workspace.py/.pyw`, `studio_panels.py`,
`studio_compact.py`, `studio_meters.py`, `window_host.py`, the standalone native
workspace test and the VBS launcher. Existing Studio/controllers, renderer,
preview telemetry, inspector presentations and Enveloper resize are extended.
Assigned operating/technical documentation was updated in DEVELOPMENT_STUDIO,
MAINTENANCE_CONTRACTS and TECHNIQUE_LIBRARY. No scene, authored palette family,
audio normalization, package, overall architecture or portable was replaced.
The generated Main GLSL remains
`a1e9e84ccf3b87480a2744d0c732363c114803cdfe8310ace839a4596adf1998`.

The root-owned Tk panel body and controls survive supported `wm manage/forget`
floating. Menus detach before forgetting native wrappers; one menu and cached
protocol callbacks are reused. The floating Tk wrapper itself is recreated by
Tk, while the body, controls and renderer HWND remain. Earlier native-parenting
trials failed focus/input or crashed and are retained as failed evidence. They
are not the shipped hosting pattern; the precise crash cause was not proven.
Win32 hosting checks HWND/process ownership and bounded launcher ancestry.
Enveloper resize samples all three valid history textures into bounded new
targets, retaining history/index/clocks instead of clearing them. Resources
allocate before replacement; failures retain the previous targets.

One existing writer/reader pair carries commands and latest telemetry. Display
updates are coalesced at 200 ms; hidden/tabbed tools skip display work and visible
consumers share one audio subscription. File waveform work has one worker, one
coalesced pending request, at most 2048 peak buckets and bounded 65536-frame reads.
Live PCM is 32 min/max pairs per available snapshot with a 192-pair display deque;
it is explicitly a snapshot view with gaps. The mapping trace holds 90 points.
No second playback engine, frame readback or duplicate inspector was introduced.

Unrelated dirty agent notes, research/planning folders and user images were
preserved. Root ROADMAP, HANDOFF, README, AGENTS and VISUAL_IDENTITY were not
edited. Recovery means selecting the preserved baseline source deliberately,
not resetting or cleaning the shared checkout. Proposed Overseer status:
"Functional unified Studio prototype implemented; awaiting Robert's organization
review. Main artistic acceptance and substantial polish remain separate."
Historical root checkpoint text is not the identity of this dirty prototype.

## Executed checks and evidence classes

- Actual Tk: `studio_workspace_test.py` PASS, 13 panels × 8 float/hide/show/redock
  cycles (104), retained body/widget identity, bounded menus, unsent invalid hex,
  profile name, Pin, revision/authored pending state, independent layout/reset,
  visibility/order/float restore, off-screen and negative-monitor clamping,
  fresh second Tk interpreter restore, and genuine tiny PCM source switching.
  A final diff-review correction narrowed reset/family/preset draft clearing to
  the changed target scope. The native check passed again with parked unrelated
  drafts retained through target and scene resets (final-scoped-drafts-workspace.log).
- `preview_playback_test.py`, `studio_audio_native_test.py`,
  `spectrum_ranges_test.py`, `performance_fixes_test.py` PASS. These establish
  their stated CPU/native contracts, not natural listening or all GPU behavior.
- `studio_test.py` PASS, including actual NVIDIA rendering, synthetic/decoded
  playback, restart/EOF, controlled live routing, scoped audio/color operations,
  presets, sessions and layers. Logs and run identity are in final-checks.json.
- NVIDIA decoded real-time lifecycle: 12 cycles × 6 representative panels during
  actual playback, renderer HWND/PID/WGL context/renderer/parameter/program
  identities retained until deliberate Stop/Start. Pause/Resume, Hold release
  on layout, real scoped ACK and unsent draft preservation passed. Warm Tcl
  commands stayed at 1802 across all 12 cycles, with one writer/reader and meter
  worker. See automatic-events.json and final-lifecycle-checks.json.
- Real OS Computer Use: typing `#12 test space` in the floating inspector
  preserved text selection/spaces; Right on floating Flux changed 1.00 to 1.01
  once with revision/applied 1 and no playback shortcut. The later manual cycles
  occurred after EOF and are not counted as playback continuity evidence.
- Actual GPU history resize: 64×32 to 128×64 retained all three colored textures
  across the full resampled image, index and valid/reset state. A prior plain
  framebuffer-copy trial failed because it copied extents, not normalized size;
  the corrected resampling path passed. This is a focused GPU preservation test,
  not a full listening review of every history-bearing scene.
- Deterministic decoded numeric comparison: 512 × 2048 PCM frames gave identical
  nine-field analysis SHA `e6443e0d9b774a8406deea3fe3429a3f27f9fc6752bdd48ec8a9ccee2f707d11`
  with candidate waveform extraction enabled. This independently checks numerical
  preservation. Raw real-time metrics.csv prefix hashes differed because latest
  render rows coalesce sequential analyzed blocks; analysis-prefix-check.json
  preserves that failed equality check. Do not call live GUI rows exactly matched.
- Console-free normal entry and actual UI actions are recorded separately in
  normal-launch-check.json. Injected startup exception logging passed with the
  MessageBox call mocked; this does not prove a physically observed failure dialog.

Known historical test failures remain recorded: studio_playback_native_test's
Experimental Fractals expectation and star_profiles_test's mock audio contract
also fail against accepted baseline source. spectrum_tuning_test retains a
historical pre-Main30 storage AST guard; candidate and accepted current storage
ASTs are identical (storage-ast-preservation.json). The relocated baseline
spectrum test lacked its ignored historical fixture; no claim that its same
assertion executed on the baseline is made. No tests were removed to hide failures.

The evidence index distinguishes source snapshots. Final matched arms preceded
only the Real-time workspace default, inline error/scene-pigment presentation,
startup-log fallback, scoped draft-reset correction and added test refinements.
The performance run did not invoke resets. The harness explicitly set
Real time; shader, analysis and measured render path remain unchanged. Native
input/continuity evidence reuses the same shipped hosting/key paths with those
bounded presentation differences, rather than silently rebinding old artifacts.

## Matched playback cost

Actual RTX 3070 Laptop GPU; windowed 2560×1440 desktop at 144 Hz, caller 60 Hz.
Six arms used the same accepted Main GLSL, held Galaxy 36, seed 7301, visit 0,
Warbot Jazz first 30 seconds at 1×, Full quality/scale 1, no optional layers,
authored colors and capture off. Actual client/framebuffer/internal target and
shader resolution were 1280×720 in every arm. Wave SHA:
`90bf34009383c524b0ad100a4665d2ce470007136d49b2bfed96a8560114512a`.
Full launch/settings/dimension/source maps, resource samples, hitches and timers
are in final-performance-comparison.json and each arm's raw run files.

| Arm | Shell CPU, % one core | Present mean / p95 / p99 ms | Samples | Max ms | >50 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Legacy visible A | 77.8 | 16.83 / 23.2 / 24.8 | 1780 | 297.8 | 1 |
| Legacy visible B | 77.0 | 16.78 / 20.8 / 21.7 | 1784 | 153.3 | 2 |
| Workspace docked A | 30.8 | 16.76 / 21.0 / 22.1 | 1787 | 120.1 | 2 |
| Workspace docked B | 31.3 | 16.77 / 21.1 / 22.1 | 1785 | 146.6 | 2 |
| Workspace floating | 32.6 | 16.76 / 21.1 / 22.2 | 1787 | 110.0 | 2 |
| Workspace tools hidden | 3.3 | 16.76 / 19.7 / 20.3 | 1787 | 119.4 | 2 |

Present median was 16.6 ms in every arm; quantiles have 0.1 ms resolution. Shell
CPU means are arithmetic means of per-interval one-core process samples, not
whole-system usage. Docked UI refresh p95 was 14.3–14.9 ms, floating 14.4 ms and
hidden 1.48 ms. The legacy tool poll was 50 ms versus the workspace's coalesced
200 ms display poll. Compaction/caching, cadence and tool pixel states all differ;
the observed shell CPU reduction cannot be attributed solely to native docking.
There is no equivalent renderer speedup or FPS guarantee claim.

Renderer process RAM ranges were roughly 120–126 MiB across these short arms;
per-arm exact byte ranges are in the table JSON. They do not establish hour-long
stability. GPU temperature ranges were A/B legacy 56–67/67–77°C, docked
60–71/59–70°C, floating 60–72°C and hidden 59–69°C. Background load, power and
temperature were not controlled. Resource sampling ran asynchronously at 1 Hz;
its p95 call cost was 128–142 ms. That overhead is measured separately, not
subtracted from presentation results. Capture/readback was disabled.

Timers distinguish caller presentation intervals, render CPU/driver submission
and swap return. Presentation includes pacing; swap return is not measured
scanout. No GPU timer-query result is inferred from render CPU time. Startup
and first-song hitches are retained separately, not averaged away. Normal pythonw
cold compile is a separate observation from these warmed benchmark starts.
The first observed pythonw integrated shader compile took 111.44 seconds
(first present 111.77 seconds). The fresh second pythonw launch compiled in
0.179 seconds (first present 0.391 seconds), with the same GLSL identity.
These are renderer startup timers, not end-to-end shell launch times. The normal
UI captures rendered at 1504×832, unlike the fixed 1280×720 benchmark workload.
Arm names beginning `release-` are private measurement labels, not release builds.

## Reference assessment and limits

The supplied reference and actual captures are alongside each other in
`work/unified-studio-20261005/review.html`. The center remains dominant, tools
stack at right, and transport/waveform sit left of the twelve-band analyzer.
Actual supported controls use tabs and scrolls; tool captions and docking menus
are explicit. Full control access was inspected in the existing source and
checked through retained widgets, native input and scoped controller tests.

Deliberate differences: existing procedural Galaxy replaces the illustrative
photographic spiral; catalog names/counts/readings are real; thumbnail-free rows
are honest because no new capture pipeline was assigned. One existing archived
Citadel capture is reused with its path disclosed. Actual gains/listening ranges
replace the mockup's illustrative EQ/Response/smoothing. Native Windows menus
and title bars remain, and dense panels require scrolling at smaller sizes.
No rejected logo, invented scene, waveform, analyzer activity or measured-pixel
mapping response was added.

Not established: continuous natural live-music listening, a multi-hour soak,
multi-hour variety, physical mixed-DPI/monitor-disconnection recovery, all-scene
history preservation during every resize, GPU draw-time comparison or measured
scanout. Monitor changes were exercised with synthetic rectangle recovery;
fresh native layout restore was exercised on the available desktop. Saved
sessions retain the existing v3 contract; layouts use their independent v1 file.
Robert's prototype feedback and resulting refinements are pending his review;
they cannot be invented as part of this builder handoff.
