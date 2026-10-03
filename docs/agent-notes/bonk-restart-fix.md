# Bonk queue-restart correctness fix

2026-10-03. Prompter-approved bounded correction of the reproduced stale Instant
request mode. Return for targeted re-review; no commit/push, publication or Planet
Canvas work is included. This note supplements the immutable organization and
Instant Bonk packs without rewriting their earlier evidence.

## Reproduction and cause

Starting HEAD remains `c0f82ad565e41eae29c2cd501a9e2217146d03d0` with the prior
organization/Instant deltas and unrelated dirty DSP/source/docs. The fix baseline,
exact diff, source hashes and checks are bound by
`work/studio-organization-01/bonk-restart-fix/review-index.json`.

The new actual-runtime/director test reproduced the reviewer's exact sequence:
ordered non-looping [26,7] queue -> manual Instant -> queue finishes -> select
Normal -> Start. Before the fix, restart duration was 0.35 seconds. Its failed
assertion and output remain in `before-regression.log`.

`LiveSession.start` created its internal first-entry boundary by setting
`bonk_pending=True` without assigning a pending mode. Manual request handling,
queue completion, Stop and Pause cleared pending flags but left the previous
`bonk_pending_mode='instant'` behind. Changing the selected `bonk_mode` did not
replace that old transient request field. The renderer correctly copied the
pending mode before consuming the request; the missing producer/reset contract
caused the leak. Earlier tests did not cover this Start-after-queue-complete route.

## Exact correction

- `app/player_runtime.py`: the internal completed ordered-queue restart explicitly
  assigns pending Normal, independently of the user's selected manual Bonk mode.
- `app/player_state.py`: consuming `next`, canceling Stop, and canceling Pause
  reset transient pending mode to Normal alongside their existing pending flags.
- `app/player_test.py`: focused `--bonk-restart-test` exercising the actual
  Start/command/tick/director path with fake PCM/capture and controlled clock.
- This task-local handoff.

The selected mode control is untouched. `bonk_mode` still retains the user's
Instant choice when requests are consumed/canceled; deliberate subsequent Instant
requests freeze their own mode and still use .35 seconds. The renderer already
captures that request mode before `next` consumes/resets it, so no renderer edit
was required. Searches covered every production pending-mode/flag producer and
consumer; remaining direct assignments were test fixtures.

## Observed checks

Before-fix regression: failed as expected with Normal selected and restart
duration .35. After-fix controlled run: internal restart duration
7.966211980119552 seconds for the same seeded case with either Normal or Instant
selected. Both preserve the selected choice and queue order; subsequent deliberate
Instant remains .35. These are controlled director-time values, not wall/GPU
performance measurements.

The focused regression also checks consumed/canceled transient fields, same-world
solo handling, repeated/coalesced requests, monotonic progress to confirmed 100%,
held arrival, Pause/no Resume backlog and Stop. Existing model/runtime subsets
cover their unchanged queue and control contracts. Final logs/index record actual
commands, syntax and scoped diff checks. Tests load committed c0f82ad analyzer and
audio-frame modules in memory with `musical_descriptors` blocked; no live source
or environment file is reverted. Capture/device/window/GPU entry points are
blocked or replaced with explicit doubles, and no Tk UI is created.

Player UI, renderer/shaders, all Studio files, audio/capture/DSP files, shared
direction documents and both prior evidence packs remain unchanged by this fix.
Preservation checks bind these claims to the new pre-fix snapshot. Reuse the prior
Studio organization and Instant progress/retiming evidence where its unchanged
source applies; do not relabel it as new rendered or live validation. No broad
suite, performance campaign, visible UI, real audio/device or GPU check was run.
The existing audio-quality cause remains unresolved.

## Targeted review boundary

Review the pending-mode producer/reset contract and the failed-before/passing-after
exact runtime regression. Confirm Normal internal restart even while Instant stays
selected, followed by a deliberate Instant request. This is a correctness delta,
not renewed artistic acceptance or authorization to publish. Return results to
Bob/Prompter for the targeted re-review. Do not commit/push or start Planet Canvas
before the assigned review/user checkpoint boundary.
