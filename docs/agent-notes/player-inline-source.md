# Player inline source, enumeration and bounded diagnostic journal

Actual-results handoff, 2026-10-03 UTC. Robert's later player correction and the
Bob-approved Prompter brief authorize this bounded follow-up to player-interface-01.
The original Crystal Cavern assignment is historical. Sole builder, no additional
workers. Return this candidate through Bob/Prompter for independent review; the
in-person audio/device check remains Robert's next review step.

Review entry: `work/player-interface-01/inline-source-delta/review-index.json`.
The baseline is the current local recovery candidate, not GitHub or HEAD alone.
The index binds exact before/final files, task-only diff, checks and artifact
hashes. The original and recovery packs remain immutable.

## Result and source policy

The original inline audio dropdown and Refresh are the source controls. The added
Change Source dialog/button and separate Retry button are removed. Labels say
System audio (loopback) or Microphone and include the actual endpoint name.
Only the bound ComboboxSelected commit sends a safe switch when a child exists.
Population, Refresh, programmatic restoration/preselection, popup dismissal and
kind display do not issue capture commands. Stopped selection changes desired
metadata; Start remains explicit. During graphics initialization an explicit
source switch can queue before capture starts. A full control queue rejects the
selection visibly and restores the previous desired identity.

Missing remembered endpoints remain shown as unavailable; there is no automatic
first-row/default-output/name or different-kind substitution. Desired source,
actual active owner and last successful saved source are separate. Preferences
change to the new source only after a current generation produces a valid packet.
The actual resolved endpoint name is used for successful-source status/saving.
Microphone remains available; loopback is not forced and no codec fix is promised.

The existing exact-ID-and-kind safe switch/recovery is reused. The previous worker
must be dead AND report confirmed release before replacement opens. A failed native
close remains releasing; no private cleanup or relaxed guard was added. Pause,
Hold owners, current world, transition, queue, pending queue edits and Stop intent
remain preserved. Resume waits for fresh packets. The existing Start button reads
Retry only when recovery is eligible and there is no capture owner.
Five opens, 1/2/4/8-second backoff, first-packet/progress/release deadlines and
genuine absent-to-present/healthy budget reset rules are unchanged.

## Enumeration and logging

One long-lived coalescing enumeration worker owns a balanced Windows MTA COM
initialization. SoundCard's installed module singleton initializes only its import
thread; it does not initialize a subsequent worker. The GUI imports the backend
on the main thread and enumeration explicitly initializes/uninitializes its own
worker. Both the chooser and runtime DeviceWatch reuse this owner. No recorder is
opened by enumeration. COM startup failure remains visible, and the same worker
can handle another request; teardown discards late results without a GUI join.

The latest result slot is independent of the general bounded GUI queue. Rapid
Refresh requests coalesce; older completions cannot replace a newer request.
Loading, valid empty results and errors are distinct. Errors retain cached options
and are logged. GUI mutation happens during polling on the GUI thread. Receiver
exceptions are isolated and logged, and polling always reschedules while open.
Runtime critical messages use a blocking bounded queue; their stderr journal
drainer operates separately, so a full status queue does not discard diagnostics.

Each panel gets a unique session JSONL journal in `%LOCALAPPDATA%/ZeraWave/logs`.
Every record has UTC, panel PID and session identity; child records additionally
carry runtime session and PID. Requested/resolved endpoint ID, kind and label,
enumeration errors, opens, release results and retry state are logged without PCM.
The legacy player.log is left intact. There are no global logger handlers or
per-child file truncations. Child stderr is drained into its captured panel journal.

Journal files rotate at 256 KiB of UTF-8 bytes, with two backups and four session
sets: at most 3 MiB of new event history, plus tiny leases/allocation lock and the
preserved legacy log. Windows live leases protect another owner's full rotation
set; abandoned leases are discoverable/prunable. A nonblocking byte lock serializes
allocation/pruning across processes. If all four owners are live, or allocation
is busy, creation fails explicitly rather than truncating active history or growing
the bound. Log IO errors are reported without stopping pipe draining. Native
startup file hashes and hashes of selected actually loaded Python function code
are recorded separately. This is not a whole-process/native loaded-memory proof.
The former 512 capture-state log cutoff is removed; byte rotation bounds storage
while late retries/errors continue to be logged. In-memory state history stays128.

## Checks and evidence actually produced

`final-checks/checks.json`: all six commands passed: six inline groups, seven recovery
groups, existing player model/runtime/capture subsets, capture_selection_test,
main_director_test and transition_controls_test. Seven affected AST parses passed.
The final small PID-field addition is specifically rechecked by
`pid-final-checks/checks.json`: all six inline groups and seven AST parses passed.
Other check evidence is reused with source-dependency identity and the exact
two-file PID-only difference; it is not described as a repeat hardware run.

Checks cover zero-command quiet operations, successful-only saved preference,
same-name/different-kind refusal, full queues, stale/late completions, startup-error
retry, mocked balanced COM HRESULT outcomes, fake workers/blocked or failed release,
fresh Resume, coalescing, byte rotation and retention, four active owners/fifth
refusal, actual offline lock contention and abandoned lease pruning. All600
synthetic late state transitions were journaled, with memory history bounded128.

The final hidden Tk evidence observes actual widgets and simulated binding delivery
with offline endpoints/commands; root mapped=0 and no visible player/focus operation
or real SoundCard import/device/recorder ran. The SVG is a labelled schematic from
widget values, not a desktop screenshot. Session examples contain synthetic data.
COM outcomes are mocked; Windows file locking/lease protection and Tk are real
offline operations. Director/transition checks are CPU/numeric, not GPU or listening.

Earlier fixture failures are preserved in the pack: Tcl state needed string
conversion; one recovery runner missed its import path. Additional sandbox checks
could not access default temp, and one runner gave a directory instead of an output
JSON file; their logs are retained under verification-attempts. Corrected runs used
isolated permitted temp files and passed. No failure was erased or hidden by warm
tests. An initial final-refinement write was rejected for stale scope; explicit
later authorization was supplied and the same write then passed approval review.

git diff --check and source/preservation checks are recorded by the final index.
Captured unrelated dirty work, original/recovery evidence, renderer/shaders,
capture_stream, player_state and analysis/DSP are preserved. No shared root docs,
settings in the user's actual data directory, dependencies, portable output,
staging, commit or push were changed. The old standalone Studio assertion failure
is reused only as prior-pack provenance; no unrelated Studio suite was rerun.

## Reviewer path and remaining limits

1. Open review-index.json, confirm baseline/final manifest and exact task-only patch.
2. Read final hidden offline-ui.json, inline-checks.json and source-bound journal;
   then the seven recovery checks and synthetic state trace. Judge evidence classes
   as labelled. New code cannot be certified by the older recovery pack.
3. Run the standalone offline scripts with the project's Python and fake backend
   before any approved physical check. Follow the exact commands in the index.
4. For Robert's in-person check, start the existing player entry when convenient:
   confirm populated type-labelled dropdown, quiet Refresh, explicit live output
   switch without restart, preserved Pause/Hold/world, successful-only preference,
   and physical disappearance/return of the exact endpoint. Compare actual listening
   quality and journal requested/resolved IDs and release state. This builder did
   not perform that check or manipulate an existing session.

Installed SoundCard native close failure can still leave ownership unconfirmed;
replacement is deliberately blocked until this player is closed/relaunched. The
headset quality complaint, Bluetooth duplex/profile/codec behavior, actual device
enumeration reliability and physical same-ID reconnect remain unverified. Existing
failure log/preferences are copied with provenance, not newly captured or proof of
loaded source. No speaker replay path was found in the read-only diagnosis, but
that does not prove the cause of the reported audio-quality change. No live audio,
GPU/performance, cold responsiveness, multi-hour rendered or AV listening claim
is made. Candidate implementation is ready for independent bounded review; it is
not hardware certification or Robert's acceptance.
