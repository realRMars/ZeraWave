# One final bounded player capture-cleanup attempt

2026-10-03UTC. Robert authorized one final attempt; designated Prompter brief was
approved by Bob. Sole builder. This implementation phase ends here for bounded
review and ONE coordinated physical acceptance. If that physical failure persists,
retain the restart notice and stop tuning. Process isolation/backend replacement
is outside scope. No automatic repair/rescore loop is authorized.

Review entry: `work/player-interface-01/final-cleanup-delta/review-index.json`.
Baseline is the dirty inline-source-delta candidate, not GitHub or HEAD alone.
All earlier player packs remain immutable. Final-source copies, exact patch,
hashes, checks, diagnosis snapshot and remaining limits are bound by the index.

## Implemented result

The original inline dropdown, quiet Refresh, source types/names, preference policy
and settled controls are preserved. No new dialog/button, renderer/director reset,
audio normalization change, dependency or site-package patch was introduced.

`app/audio/wasapi_cleanup.py` owns a narrow close boundary for the inspected
SoundCard0.4.6 Windows recorder ABI. It checks the actual recorder class/module and
installed source hash before binding, and owns the same worker thread that opens,
reads and closes capture. It uses original project code calling native Stop and
IUnknown Release through that ABI; it does not globally monkeypatch SoundCard.
The installed BSD3-clause license was inspected and copied into this evidence
pack. No substantial vendor implementation was copied into the project adapter.

HRESULT is normalized to signed32-bit, so S_OK0 and S_FALSE1 succeed. Microsoft
documents Stop S_FALSE as successfully already stopped:
https://learn.microsoft.com/en-us/windows/win32/api/audioclient/nf-audioclient-iaudioclient-stop
and nonnegative HRESULT success:
https://learn.microsoft.com/en-us/windows/win32/api/winerror/nf-winerror-succeeded
Negative Stop HRESULTs and exceptions remain explicit diagnostic errors. Finally
cleanup attempts each valid acquired capture-client/audio-client reference even
after Stop error or another release error. Returned native Release is recorded,
then its owned pointer is nulled. Repeated close never redispatches a possibly
ambiguous release. Cleanup on another thread is forbidden. If both owned references
were actually released (or never acquired), stop returns confirmed proof; a genuine
Stop failure is still in the outcome. If any reference is unconfirmed, close raises
and the existing failed-close guard remains blocked. This is own-reference proof,
not a promise that the OS/device has no other clients or references.

CaptureStream remains unchanged: a replacement may open only after the previous
worker is dead AND stop confirmed actual cleanup. No UI-thread release, clearing
flags as a substitute for cleanup, automatic kill/restart, fallback output/mic or
retry-budget change. Constructor-internal allocations that never return an owned
recorder remain outside this close adapter's observable ownership; no exhaustive
native partial-construction guarantee is claimed. Unsupported backend source/ABI
is rejected, not silently treated as verified.

Start waiting on unavailable capture draws the current quiet world instead of
waiting indefinitely before draw. Explicit Pause still freezes image/clocks while
analysis and recovery run. Healthy Resume waits for new packets; unavailable
Resume can gently idle, still discarding pre-Resume packets and first discrete
events. No catch-up clock jump, automatic world/transition/queue advancement from
missing audio or art reset was added. Existing renderer availability gating is
reused. Stop cancels listening intent and late frames/retries remain generation
guarded.

UI submissions now journal serial/op, runtime session, desired/active source and
intent/availability/Pause/owner state. The actual runtime dispatch emits compact
ACK before/after state and the same serial/source; the pipe sink journals ACKs even
when full state is present. Cleanup outcomes include normalized Stop HRESULT,
owner thread and per-reference result. Runtime startup binds adapter file hashes,
actually loaded cleanup/dispatch function hashes and the inspected backend ABI
hash. Existing256KiB/2-backup/4-session byte rotation still bounds new journals to
3MiB plus tiny leases/lock and preserved legacy player.log; no PCM or unbounded
telemetry is stored.

## Existing-area fallback

On unconfirmed/failed release or exhausted opens, the existing status area says:
"Capture could not restart. Close this ZeraWave player completely (player panel
and visual output), then reopen it and reselect your audio source. A closed window
alone does not confirm native release."
The notice wins over Refresh/reselection status; the inline chooser stays live.
No popup/clutter or automatic process operation was added. If Robert's single
physical check still fails, this is the temporary known-limit fallback and tuning
stops. Closing only the visual window does not prove native release; the notice
names the full player/owned runtime boundary.

## Actual checks

`checks-02/results.json` binds six final-source commands, all exit0:
1. wasapi_cleanup_test: actual project adapter with controlled pointer/HRESULT
   doubles: S_OK/S_FALSE, signed/unsigned failed HRESULTs, Stop throws but releases
   attempted, partial acquisition/release, repeat-close latch, foreign-thread
   rejection, actual typed CFFI callbacks and unsupported ABI refusal.
2. player_final_cleanup_test: actual AudioCapture/CaptureStream/adapter with fake
   endpoint/vtables/read completion, late cancellation, successful vs partial
   release and owning-thread calls; worker-exit+release replacement guard; quiet
   Start/unavailable Resume vs explicit Pause; no progression; Stop cancellation;
   actual dispatch/ACK and journal sink; existing-area persistent notice and actual
   hidden Tk mapped0. It does not instantiate a real native backend.
3. player_inline_source_test: six groups including actual hidden Tk virtual
   selection, Refresh/programmatic zero-command policy, source preference,
   coalescing/mocked COM/teardown, exact source/recording config and bounded logs.
4. player_capture_recovery_test: seven synthetic/fake-worker groups, exact source,
   silence, retry bounds, intent/queue/world/transition/Hold retention, Pause/fresh
   Resume, Stop/stale/late cancellation, failed close and bounded watcher/history.
5. Existing player_test model/runtime/capture subsets with SoundCard stub.
6. Existing capture_selection_test with SoundCard stub.
Six affected Python AST parses, exact diff review and git diff --check passed.
`checks-01` preserves the earlier all-pass internal checkpoint before factoring
the actual dispatch/sink for direct tests. No failed check was discarded.

Evidence classes: controlled pointer/CFFI callback doubles, fake SoundCard and real
worker threads, CPU/numeric renderer mapping, and hidden offline Tk widgets. No
real SoundCard import/device enumeration/recorder/physical toggle, visible player,
foreground action, OS settings, live call interruption, GPU capture/performance,
cold responsiveness, continuous listening or multi-hour rendered check ran.
The copied223-row session diagnosis is prior physical evidence with original
timestamps/PIDs/hash, not a new native validation of this implementation. It showed
four separate children skipping vendor release after S_FALSE. Its recompilation
hash mismatches remain recorded; do not relabel them a complete loaded-code proof.
Audio quality is still unconfirmed by Robert.

## Reviewer/acceptance route

Read index -> baseline/exact patch/final-source -> final checks -> cleanup outcomes
and hidden status evidence -> prior source-bound diagnosis. Prompter prepares
actual-results review for Bob; no independent critic was dispatched by this builder.
After that review, coordinate ONE user physical check when it will not interrupt
the call: active headset disappearance/return, exact reselect/monitor switch,
Start/Stop/Pause/fresh Resume, quiet continuing world and resulting journal
HRESULT/reference/worker/command correlation. No listening-quality success is
claimed from offline tests. If it fails, retain the notice and STOP; do not begin
another implementation or larger isolation work without a separate decision.

No shared root docs, user settings, frozen portable or unrelated dirty work was
changed. No staging, commit or push. Checkpoint identity is the source manifest
over the unchanged HEAD, not a new Git checkpoint.
