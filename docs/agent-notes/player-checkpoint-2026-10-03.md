# Accepted ZeraWave player checkpoint

2026-10-03. The player interface and bounded device-loss cleanup are implemented
and accepted. This guide supersedes historical player interaction instructions.
It accompanies the approved checkpoint over visual baseline
`2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5`; the builder reports the new actual
commit hash and verified remote after publication. No release/build is included.

## Open and listen

Run `run_zerawave.bat` or `run_live_visualizer.bat` without arguments. Choose one
exact output loopback or microphone/input endpoint in the inline dropdown, then
Start. The saved successful source is selected only when its exact type/ID is
present. Missing sources require explicit selection; there is no automatic
default/fallback. Refresh only updates the list and sends no listening command.
No recording, upload, multi-source or per-app capture is implemented.

Start opens the separate visual canvas. Actual startup phases are shown in the
panel; the activity bar does not promise a percentage or shorter cold compile.
Stop before the canvas is ready cancels only the owned starting runtime. Once
ready, Stop stops listening and lets the current world settle quietly. Closing
the canvas returns to the panel and clears now-showing.

Pause freezes drawing, scene/transition and queue time while analysis/recovery
can continue. Resume waits for fresh packets and suppresses stale discrete events.
Stop from Pause enters quiet idle. Missing audio permits gentle idle while holding
world/transition ownership; it does not automatically advance the queue.

Hold is momentary: animation/audio response continue, an active transition can
finish, and the arrival stays held. Release/focus loss clears the owning Hold.
Bonk requests one compatible next-world transition and overrides Hold once;
it is ignored during Pause, Stop or an active transition. Repeats do not queue
a Resume backlog. Current/target world and taxonomy appear only in the panel.

## Queue and keys

Add/Use subset/Solo/All Main build a 1-50-entry draft from the canonical 27 Main
worlds, including Galaxy36. Water37, Experimental38-40 and the three Envelopers
remain excluded. Remove/move/clear edit the draft; duplicate entries are allowed.
Apply saves the draft for the next world boundary; Start also validates/applies
it. Use Bonk for the next boundary. The outgoing world/transition completes first.
Shuffle off follows order; Loop off stops on the final world, Loop on wraps.
Shuffle on continues until Stop and remembers the ordered Loop preference.
Duplicate current-world entries renew dwell without resetting scene history.
Preferences remain `%LOCALAPPDATA%/ZeraWave/settings.json`.

Focused panel/output shortcuts: Space Bonk, Shift Hold, Ctrl+Enter Start,
Ctrl+S Stop, Ctrl+P Pause/Resume. Text/combobox editing retains ordinary keys;
there are no global hooks. Output F11 toggles fullscreen and Esc closes.
Optional tips are off by default. Studio and diagnostic runners remain available.

## Recovery, acceptance and evidence limits

When the selected source disappears, retain or explicitly reselect that identity
after it returns; Refresh alone does not restart stopped listening. Recovery is
bounded and preserves controls/world ownership. An unconfirmed native release or
exhausted open attempts leaves the existing status notice: close the complete
player panel and visual output, reopen, and reselect your source. Closing only
the visual window is not proof of native cleanup. No automatic kill/restart runs.

After bounded safety review, Robert reported active BlackShark off -> unavailable
-> on + Refresh recovery without closing the runtime, repeated normal Start/Stop,
and **10/10 acceptance**. This is user-reported physical acceptance, not unattended
recovery certification or an audio-quality/device-diversity guarantee.

The immutable final-source pack is
`work/player-interface-01/final-cleanup-delta/review-index.json` (SHA256
`d09e18325c08d77d76b3f5b3a6a8fb52d0787be7399b44e59583804a4835ec63`).
Its source manifest SHA256 is
`27fc853ae552440cd376172084bdcf4d8cfc95e1b42d7de23f34f93a4a03f5ee`.
Six passing final commands cover the WASAPI adapter, final cleanup transport,
inline source controls, capture recovery, player model/runtime/capture subsets,
and capture selection. Evidence is offline pointer/CFFI doubles, fake workers,
CPU mapping and hidden Tk; these exact-source results are reused for publication.
New checks are staged-source binding, Python syntax and Git whitespace/scope.

The original interface/recovery/inline/final notes remain historical evidence;
their pre-acceptance statements are not rewritten. The reproduced baseline
Studio line566 failure, physical output-shortcut limits, prior cold-ready failure,
native pacing, AV and multi-hour limits remain in the current handoff. No new
native/GPU/audio/device/UI operation is performed for this publication.
Local work packs remain ignored, with no settings, logs, captures or private
conversation exports committed. Frozen portable remains unchanged. Parent owns
Pages publication after the builder reports the exact GitHub checkpoint.
