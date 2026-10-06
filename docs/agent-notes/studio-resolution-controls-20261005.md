# Studio resolution and resize controls — Builder results

> Publication status — October 6, 2026: Robert authorized this development
> checkpoint for commit and normal push. The original results below retain
> their own validation limits and pre-publication status.

Approved three-item Studio batch implemented.

1. Main window: eight native outer resize directions, OS sizing-loop delegation, directional cursors, logical/physical DPI regions, minimum size and maximized/fullscreen guards. Header and retained HWND preserved.
2. Settings > Visualizer Resolution and Visualizer tab context submenu share shell-owned actions and an acknowledged policy. 640x360, 1280x720, 1920x1080, Native and integer Custom. Existing Quality remains until explicit choice; explicit choice bypasses that scale. Fixed pixels use aspect-fit presentation; Native uses GLFW physical framebuffer pixels. Allocate replacements before release; failed requests retain accepted policy/targets with a concise nonmodal status. Existing normalized Enveloper history resizing is reused.
3. Resources: Detailed retains existing information and exposes FPS first; Simple shows CPU/GPU/Mem/FPS, with scope/unit tooltips and honest paused/stale/unavailable states. Collector is unchanged; no extra sampler or graphs.

Focused checks:
- resolution-sanity.json: CPU eight directions at 100/150/200% DPI, validation and scale; real GL fixed pixels, aspect-fit bars, injected allocation failure, device limit and all three resampled feedback histories.
- Native Windows resize messages in qt-sanity-attempt-04.json: all eight directions changed actual main geometry; cursors, minimum and maximized/fullscreen guards checked. This is API/message evidence, not physical mouse certification.
- qt-sanity.json PASS: normal synthetic Root owner/renderer, inherited 75%, 640x360, Custom 777x431, Native, paused 1280x720, same context/source, both monitor modes, shared actions and unchanged docking state during mode changes. Its saved test layout had Diagnostics selected, so visible Native sizing was checked separately.
- viewport-sanity.json PASS: visible production wrapper with constant-color test shader, fixed 1920x1080 unchanged while physical viewport changes 937x601 -> 696x437; Native then follows 696x437 -> 937x601. Same GL context. Not artistic or performance evidence.
- menu-sanity.json PASS: twelve temporary ADS menus destroyed without invalidating shared actions; original docking actions retained; stopped selections synchronized.
- Existing preview_playback_test.py PASS; final Python syntax and git diff --check PASS. Renderer.render AST unchanged.

Earlier attempts retained: initial new-menu lifetime problem and startup local-json shadow were fixed; a later shared-submenu lifetime problem was fixed by independent menus with shell-owned actions. One harness assertion ran before Qt's next indicator refresh and was corrected. One attempt exited with code 1 during pending startup without a new diagnostic; its cause remains unidentified, with no remaining ZeraWave windows found afterwards. The final isolated integrated and menu checks passed. Existing shader startup reported about 107 seconds; no startup optimization or benchmark was performed.

Preservation: no shared planning docs, shader artwork, collector, git checkpoint or user settings were edited by this batch. One saved user Qt-layout hash changed during the run; its origin was not established, and the newer file was left untouched (settings-check.json). Test layouts and outputs are isolated in this folder. No physical multi-monitor/DPI, scanout, natural audio, performance improvement or acceptance claim.
