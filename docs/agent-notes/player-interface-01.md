# Free-player interface milestone

Task-local builder handoff, 2026-10-02. Bob approved the designated Prompter's
implementation brief. Code HEAD remains `2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5`;
this milestone is an uncommitted local delta. Return actual results to Bob/Prompter
before the independent critic. No user acceptance, commit, push or release claim.

## Review route

Run `run_live_visualizer.bat` without arguments, or `run_zerawave.bat`. The former
now opens the player; explicit arguments such as `--state cavern --quiet` still
use `app/visuals/live_visual_test.py`. Studio and diagnostic entry points remain.

Choose exactly one output loopback or microphone/input endpoint. The chooser
preselects the saved working identity only when that exact type/ID is present.
Unavailable sources leave it blank and require an explicit replacement; there
is no dynamic default or silent microphone/output fallback. Per-app capture is
unavailable with this backend. The existing SoundCard/WASAPI recorder is reused;
there is no recording, upload, multi-source capture or new permission acceptance.

Start opens a separate clean visual canvas. Context, shader compilation, resource
preparation and output readiness are actual child messages; elapsed time and an
indeterminate activity bar are not a progress percentage or startup fix. Stop
during unpresented initialization cancels exactly the owned interpreter. Once
output is ready, Stop stops capture, freezes automatic progression/current
transition ownership, and lets the existing world/composition gently settle.
Closing the output returns to the panel and clears now-showing.

Pause skips drawing and freezes scene/transition/queue time while the same worker
continues analysis. Resume discards presentation events from paused packets and
waits for a packet timestamped after Resume; it maps current levels, suppresses
the first discrete onset/tick, and resumes without a catch-up stepping loop.
Stop from Pause unfreezes into quiet idle and stops listening.

Hold is momentary. Mouse capture routes button release back to the panel;
release/focus loss clear that owner's Hold. Animation and audio response continue.
An already active transition completes, then its arrival stays held. Bonk requests
one compatible next-world transition, overrides Hold once, and retains a physically
held arrival. It is ignored during Pause, Stop or an active transition; repeat keys
and repeated requests do not build a Resume backlog.

The panel reports actual director current/target worlds, shared Studio taxonomy
and authored transition names. Queue selection is not now-showing. Controls,
menus and tips stay in the panel; there is no overlay on the visual output.

## Queue and preferences

- Main's canonical 27 IDs only, including Galaxy36; Water37, Experimental38–40,
  grouping/diagnostic states and the existing disliked exclusions remain out.
  Envelopers remain off. The shared authored taxonomy is extracted unchanged to
  `world_catalog.py`, imported by Studio/live diagnostics and filtered by the player.
- Add appends selected library items; Use subset replaces the draft with selected
  items; Solo needs one item; All Main restores the approved roster. Remove/move/
  clear edit the draft. Duplicate entries are allowed; 1–50 entries are required.
  Empty/invalid saved selection stays visibly invalid until repaired.
- Apply persists the draft and stages it for the next world boundary. Start also
  validates/applies the current draft. Existing displayed content/active handoff
  completes first; use Bonk when an immediate next boundary is desired. The next
  ordered entry after a changed queue is its first item. Future selections cannot
  escape the new subset; the already displayed outgoing world may remain visible
  until that boundary. Unchanged Stop/Start keeps the current ordered position.
- Shuffle off follows order. A duplicate current-world entry renews its dwell
  without switching or resetting scene history. Loop off ends by Stop, keeping
  the final world. Start after completion begins a new ordered cycle with a smooth
  handoff to its first entry. Loop on wraps. Shuffle on continues until Stop and
  remembers the ordered Loop preference independently.
- Fresh default queue uses the existing musical/history-aware randomized Main
  chooser. Recent-world avoidance is optional and soft. Solo/subset constrain the
  pool; queue entries are IDs, not preloaded per-entry scene instances/assets.
- Settings remain `%LOCALAPPDATA%/ZeraWave/settings.json`: queue, shuffle, loop,
  recent preference/history, optional control tips and last successfully captured
  source. Old explicit `device` IDs migrate to loopback identities; an old dynamic
  system-default choice requires explicit selection. Review presets are not read.

Focused panel/output shortcuts: Space Bonk, Shift Hold, Ctrl+Enter Start,
Ctrl+S Stop, Ctrl+P Pause/Resume. Text/combobox editing keeps normal keys; there
are no global hooks or custom/global shortcut facilities. Output Ctrl+Enter routes
through the panel's current source/draft, avoiding a stale endpoint. Output F11
toggles fullscreen and Esc closes. Tips are off by default and opt-in.

## Implementation and preservation

`player.py` keeps the existing Tk panel and owns one actual base interpreter,
using the current project's import paths to avoid Windows venv redirector orphans
(the existing startup notice uses this pattern). `player_runtime.py` extends the
live caller with bounded command/status pipes, the existing capture worker/analysis
and explicit scene time. `player_state.py` contains independently testable queue/
playback decisions. Renderer hooks are optional; normal Studio/director paths keep
their prior behavior. No shader, scene art, DSP analysis/normalization, dependency,
Studio tab redesign, packaging or shared-root-document edits in this milestone.

The exact task baseline, diff and source/evidence hashes are in
`work/player-interface-01/review-index.json`. All earlier dirty documents and
research/brainstorm work remain outside this delta. Nothing staged or committed.

## Evidence and limits

See the review index for exact commands, logs, hashes and final-source artifacts.
Focused standalone checks cover config/migration/cap/exclusions; ordered duplicate
end/loop and shuffle independent of Loop; pending edits; Stop from Pause/transition;
current-audio Resume with stale timestamp rejection; Hold/Bonk; selected-source
identity, focused Tk key dispatch before button Space bindings and mocked GLFW
key/focus callbacks. Shared Studio/session, director and transition checks are
recorded separately from actual UI/live evidence. The full Studio script fails
at line566, which assumes every technique lives in `dream.frag`; Auroral Veil,
Arc Constellation and Citadel panels use separate shader sources. An isolated
verbatim checkout of2bcb03f reproduces that same failure. The implicated test,
catalog, shaders and surface source are byte-unchanged from the task baseline.
No assertion was deleted or changed; later Studio assertions are not certified.
The earlier intermediate Studio-pass statement was premature and is corrected
by these saved failure/baseline logs.

Short actual Tk/GLFW runs use the explicitly selected BlackShark headphone
loopback. They verify analyzed packets, exact-image Pause while analysis advances,
Stop/restart, mouse Hold/release, Resume with Hold, compatible Bonk held arrival,
duplicate/order completion, saved-source/queue reload, missing saved ID against
real enumeration and focused Tk key events. Client-only UI captures, actual default
DPI layout checks and eight normal-time transition samples were inspected. These
are sampled motion/control evidence, not continuous AV listening or scene rescoring.

Failures are preserved: a posted Windows Shift message did not sustain a held
snapshot; a guarded physical-key probe could not foreground the exact owned output
and withheld injection. Physical output shortcuts are therefore not verified here;
their mapped GLFW callbacks pass controlled tests. Critic/manual review should click
the output and exercise Space/Shift/Ctrl+Enter/Ctrl+S/Ctrl+P and focus loss. Actual
microphone capture and physical device unplug/reconnect were not tested; source-kind
selection and device-loss behavior are fixture-tested. SoundCard discontinuity
warnings from live starts remain in the logs. No AV quality or permission/device
compatibility guarantee follows from those tests.

Startup cancellation uses a real owned child with a synthetic blocked-init fixture;
it is not a cold-shader test. Warm UI/WM_NULL observations do not replace the prior
cold post-ready failure or establish that 80–83s compile delays are fixed. Retain
native fullscreen-surrogate/Aperture/Molten pacing, Aftershock7.4, unknown minimum
device, scanout/thermal/power, AV and multi-hour limitations from the approved
checkpoint. No new benchmark, startup optimization or long rendered soak was run.
Exact paused-image checks used an unchanged output size; pause across output resize/
minimize and additional Windows/DPI/device combinations remain unverified.

Next decision belongs to Bob/Prompter: prepare/approve the actual-results critic
brief. No critic dispatch, next phase, commit/push or installer in this handoff.
