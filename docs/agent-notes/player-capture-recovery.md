# Player capture recovery and deliberate source switching

Authorized correction: Robert's 2026-10-02 request, designated Prompter brief
approved by Bob. Sole builder; no extra workers, commit, push, release or live
session manipulation. This task extends the current local player-interface-01
candidate; its original review pack remains immutable. Shared root documents
were not edited. Return through Bob/Prompter for an actual-results review brief.

Review entry: `work/player-interface-01/capture-recovery-delta/review-index.json`.
That index binds the local baseline, exact delta, final source, checks, synthetic
state trace and this guide. HEAD alone is not the dirty source identity. Earlier
player evidence describes the earlier code and does not certify this correction.

## Implemented behavior

Listening intent remains in Playback.running; availability is independent.
Endpoint disappearance, read/open errors, worker exit or stalled read/analysis
progress release capture without calling the user's Stop. Pause, Hold owners,
renderer, world, transition, queue index, pending queue edits and queued Bonk
remain intact. Genuine key release/focus loss still releases its Hold owner.
While capture is unavailable the existing director keeps its current world and
transition ownership; active scene motion continues with gentle parameter decay.
Pause skips drawing and all visual clocks while analysis/recovery continues.
Resume waits for newly captured samples and suppresses old mailbox events and
the first discrete beat/onset; it does not catch up the paused interval.

Start refreshes endpoint enumeration, including ordinary Stop-to-Start in the
same renderer. Recovery refreshes it before another open. A single runtime
watcher also checks availability every two seconds. Automatic opens use only
the selected exact endpoint ID **and** kind, with AudioCapture.exact_id=True.
There is no default-output, different-output, microphone or friendly-name
fallback. A changed Bluetooth ID/profile requires explicit Change source/Apply.
The chooser retains the requested identity when it is temporarily absent.

Five actual opens are allowed per recovery episode, with 1/2/4/8-second backoff
between unsuccessful opens. Missing endpoints are watched without consuming
opens. Exhaustion retains intent and reports Retry capture/Change source; more
presence-only enumeration does not reset the budget. Deliberate Retry/Apply,
a genuinely observed absent-to-present edge, or ten seconds of healthy packet
progress resets the budget. There is no total recovery-time guarantee: endpoint
absence, blocked enumeration and unresolved release may persist indefinitely.

The first packet/open deadline is five seconds; established analyzed-packet
progress may not stall for more than two seconds. Empty drains and zero sample
amplitude are not failure signals. The installed SoundCard WASAPI code synthesizes
zero samples after four default device periods without native packets and honors
the native SILENT flag. See backend-silence-provenance.json for source hash and
lines. This is installed-source evidence, not a physical silence measurement.
A valid silent packet establishes a working source and can be persisted.

The render/event thread never joins capture. request_stop signals the worker;
only that worker enters, reads and exits the recorder. Its mailbox is bounded at
64 entries. Generations reject stale packets/completions, and Stop cancels intent
and all opens/retries. A replacement cannot open while the old worker is alive
or its release is unconfirmed. After two seconds the UI explicitly reports
unconfirmed release. A failed context close stays in releasing and requires
closing/relaunching this player. Stop is not falsely reported as resource release.

**Known backend limit:** installed SoundCard __exit__ checks the native Stop
HRESULT before releasing COM handles. A close exception can therefore prevent
confirmed release even after a read error has ended the worker. This correction
fails closed; it does not use private COM cleanup, terminate a worker, replace
the backend or edit the installed package. Same-ID automatic recovery is supported
when the previous capture releases successfully. The physical Bluetooth check
must establish which release path this headset actually takes. A further safe
backend-cleanup proposal is needed if that path fails; this batch does not silently
expand into it.

Change source opens a separately refreshed draft chooser with Apply and Cancel.
Opening, refreshing and cancelling do not change actual capture, the selected
identity or successful-source preferences. Late/cancelled enumeration results
are ignored, and an already pending dialog enumerator is never duplicated.
Apply deliberately changes the selected identity and safely releases the previous
capture, retaining listening intent and Pause. A stopped player stays stopped.
Failure reports the selected replacement's failure; it never silently falls back.
A full control channel leaves the old selection and dialog intact for retry.

Only source_working for the currently selected ID/kind and valid generation saves
the last successful source. Apply/open attempts do not overwrite it. Relaunch
continues to preselect that successful endpoint even if the display selection was
blank when the previous panel closed. Existing queue/preferences persistence
continues independently.

Capture state/retry/error records have UTC stamps and no audio payload. The new
state log is capped at 512 records plus one cap notice; in-memory history is 128.
Live UI status continues beyond the cap. Existing SoundCard/backend warnings are
not suppressed or covered by that state-log cap.

## Checks and evidence

- New standalone player_capture_recovery_test.py: synthetic exact-ID return;
  changed-ID/same-name/wrong-kind refusal; valid silence; errors, worker exit,
  starvation, constructor/open failure and exhaustion; Stop during pending
  enumeration/open/backoff; stale generation; single ownership during blocked
  or failed release; Pause and in-flight transition retention/fresh Resume;
  running/paused/stopped Apply/Cancel, failed switch, full channel and late
  enumeration; successful-only preferences and temporary-file relaunch matching.
- Real Python worker and watcher threads with fake backends: nonblocking Stop,
  late open closed without reading, failed close unconfirmed, single blocked
  enumerator. No real audio backend operations or player windows.
- Existing player_test.model_tests/runtime_tests/capture_tests, capture selection,
  Main director and transition controls: focused CPU/mocked regressions.
- Seven affected Python AST parses and git diff --check.

Exact commands, results, source hashes and stdout/stderr are in checks.json.
Synthetic state trace records bounded events and final state, not rendered AV.
No actual Tk layout/focus, GPU, headset reconnect, microphone, natural listening,
cold startup, performance campaign or multi-hour rendering was run for this delta.
Full player_test.ui_tests was deliberately not run because it deiconifies a window;
Robert's active call/player was not touched. The earlier full Studio test's known
single-file technique assertion failure remains recorded in the original pack;
no Studio test or scene fix is claimed here.

## Remaining physical review, coordinated by Bob

Once Robert is available and approves a controlled session/restart, launch the
changed player normally and explicitly select the headset output. Check same-ID
off/on recovery and release status while running, then while paused; verify exact
image/clock preservation, fresh Resume and no queue/transition catch-up. Check
Stop during recovery prevents restart. Use Change source/Cancel and deliberate
Apply to a user-approved output in running/paused/stopped states; test a failed
selection and relaunch preselection. Do not open a microphone incidentally.

If reconnect produces a changed endpoint ID, explicit Apply is expected. If
native close fails or a worker remains blocked, releasing/close-relaunch is the
intended safe guard and automatic recovery is not established. Preserve the log
and report that path for a separate cleanup decision. Native physical input,
resize/minimize Pause, audio/device diversity and baseline performance/AV limits
are still unverified. No user acceptance or independent-review approval claimed.
