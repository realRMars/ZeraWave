# Instant Bonk — bounded actual-results delta

2026-10-03. Sole builder; approved Normal-default/optional-Instant manual Bonk
scope. Await one fresh combined review of this delta and the completed Studio
organization, then user notification and Overseer publication prompt. No commit,
push, audio/capture/DSP/art changes or subsequent pilot is authorized by this note.

## Source and preservation

Starting HEAD is `c0f82ad565e41eae29c2cd501a9e2217146d03d0`, with the completed
six-file Studio organization change and unrelated DSP/player-documentation dirt.
This delta has its own baseline in
`work/studio-organization-01/instant-bonk-delta/baseline-identity.json`.
The original organization pack's 14 files, its original index/hashes/diff and all
six organization deliverables remain immutable. The new delta index links that
pack rather than rewriting its earlier renderer-preservation finding.

Assigned changes: `app/player.py`, `app/player_state.py`, `app/player_runtime.py`,
`app/visuals/renderer.py`, `app/player_test.py`, the existing accepted-player guide
and this new task note. Exact delta and final hashes are in
`work/studio-organization-01/instant-bonk-delta/review-index.json`. Existing dirty
`PLAYER.md`, README, audio/DSP source, source evidence and research stay outside
this diff; shared planning documents are untouched.

## Implemented behavior

The existing Bonk button gains one small Normal/Instant combobox, initially
Normal. Its choice is session-only and is transported to the runtime separately
from saved queue/source preferences. Focused Space in the panel/output uses the
same runtime choice; existing key-repeat and text/focus guards are preserved.

Normal's renderer route is unchanged: same queue/weighted choice, compatibility,
recipe, smoothstep and seeded 6–9-second duration. Instant new manual handoffs use
the same route with a 0.35-second duration target. The original random duration
draw still occurs, preserving the subsequent RNG sequence. Automatic handoffs
never read this mode and keep their normal 6–9/8–11-second timing, dwell and
Galaxy route gate.

During an active handoff, Instant sets one coalesced expedite flag for the current
arriving world. The director preserves its linear fraction p, compatible recipe
and target, and retimes only the remaining tail: duration becomes .35/(1-p) and
origin becomes current_director_time minus p times that duration. No director,
scene or Galaxy clock jumps. The same smoothstep input is retained at the edit
boundary. A tail already shorter than .35 is not lengthened. A per-handoff flag
prevents repeated retiming; no second target or hidden queue is created.

Manual Bonk still bypasses dwell/beat waiting and overrides Hold once; a held
arrival remains held. Pause/Stop clear pending and expedite requests. Existing
source availability gates remain; Instant does not enqueue a request while
unavailable. Same-world/solo/duplicate, queue subset/order/shuffle and deferred
queue edits retain their existing outcomes. Changing the choice sends no listening,
source, queue or saved-preference command.

The progress indicator is the clamped linear director transition fraction, not
shader loading. A bounded completed flag publishes 1.0/100% after actual director
handoff completion. The panel shows 0–99% while active and retains last-completed
100% until another handoff starts. Startup/resource callbacks and readiness flags
are untouched. All graphics resources still prepare through their existing
blocking pre-draw paths; no zero-load or 0.35-second wall-time promise is made.
The target is a short visible takeover when rendering is ready, not an asset-load
measurement. Native/GPU effects on that target remain unmeasured in this offline
assignment.

## Checks and limits

Use the delta index and logs as the command/result source of truth. The focused
existing standalone test entry is:

```powershell
.\.venv\Scripts\python.exe -X utf8 app\player_test.py --instant-bonk-test
```

Controlled director tests compare Normal against the byte-bound pre-delta renderer
(RNG, history, timings and blend uniforms); verify compatible Instant .35 timing,
active retiming/progress continuity, monotonic completion, repeats, short tails,
held arrival, Pause/Stop, queue subset/solo/duplicates/deferred edits, shuffle and
normal automatic/Galaxy74 behavior. Real runtime command/snapshot and focused
output-key callbacks are exercised without creating a window. A withdrawn Tk
panel checks default/mode control, button/Space routing, no preference storage,
text/focus/repeat handling, readiness controls and completed 100% display.

Renderer creation, capture/endpoint enumeration and child launch are blocked or
explicitly mocked. No actual GPU, visual window, audio device, natural/live input
or user session is used. Model/runtime subsets and the focused Studio organization
guard cover the affected contracts. The UI checkpoint is also checked with the
committed c0f82ad analyzer/audio-frame source loaded into temporary in-memory
modules and `musical_descriptors` imports blocked; live dirty files are never
reverted or rewritten. This isolates the uncommitted DSP dependency without
changing the installed environment.

No full Studio/player/device audit, performance campaign, rendered appearance
assessment or artistic/user acceptance is claimed. Existing audio-quality cause
remains unresolved. Final preservation compares all bound unrelated source/docs
and every original organization-pack artifact. Historical failed evidence remains
in its original pack; no old checks are silently relabeled for this delta.

## Review and next boundary

One fresh source-bound combined review should inspect both linked packs. When the
user chooses to test manually, open the player: Normal is beside Bonk; switch to
Instant and use Bonk/Space for a short compatible arrival. If a handoff is already
running, it should complete the same arrival smoothly sooner. Hold keeps the
arrival; Pause and Stop win. Confirm the panel's 100% completion and normal
automatic pace after a manual Instant. Cold/first-use stalls may still exceed the
target. Studio's Main-only 27 forms, Experimental basin/remakes/tools and full
176-ID Library remain as previously delivered.

Return to Bob/Prompter for the single fresh combined review, then the user's
Overseer publication prompt. Do not automatically dispatch a critic, commit/push,
start Aftershock, or begin the latest Planet Canvas DSP pilot before the locked
checkpoint boundary.
