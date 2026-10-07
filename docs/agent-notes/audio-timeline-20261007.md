# Session Waveform transport — 2026-10-07

Implemented Robert's requested imported-file timeline and Studio transport in the
working checkout. `run_zerawave_studio.vbs` already launches this checkout; restart
Studio to load these changes. No commit, push, publication, dependency change or
worker dispatch was performed.

## Visible result

- Full-song waveform with click/drag seeking, an audio position marker, current
  time at left and total duration at right. Device Listening retains its recent
  capture display and does not offer seeking.
- Custom teal/copper icon controls for Open, rewind, Play, Pause, Stop and fast
  forward. Scan offers continuous 2×, 4×, 6× and 12× playback in either direction.
  Play restores normal 1×. Speed changes pitch; this is not time stretching.
- Joined, mutually exclusive left/right switches describe Audio source, Repeat,
  Output mute and Visual drive. Existing shared boolean controls use the same
  switch presentation. Settings and Session Waveform retain shared backend state.

## Ownership and preservation

The existing AudioOwner still owns capture/output and publishes the same decoded
PCM to analysis. Captured input is never replayed. Seeking flushes queued output
and rejects stale file/seek requests; consecutive drag updates coalesce and Stop
cancels obsolete seeks. Rate changes retain bounded decoding; redundant requests
do not reopen output. Output statistics and source PCM metadata publish together.
The original PCM remains independent of output volume/mute.

The file overview uses a cancellable, read-only decoder on one worker with bounded
chunks and at most 2048 envelope buckets; it creates no playback/capture stream.
Renderer ownership, visual clocks and existing generation/history guards remain
in place. Fifteen saved-layout and prior-source hash checks passed, including the
renderer and previous audio-drive integration. The launcher hash is unchanged.

## Source and task delta

Published HEAD remains `ffa67074315b8c2f4fa9d228e82faf0855cc22b8`.
The baseline includes the existing dirty accepted work, not just published HEAD.
Exact before/after SHA-256 identities and preservation checks are in
`work/audio-timeline-20261007/result.json` and `baseline.json`.

Changed: `app/audio/studio_transport.py`, its existing standalone test,
`app/visuals/studio_qt.py`, and `app/visuals/studio_control_service.py`.
Added: `app/audio/file_waveform.py` and `app/visuals/studio_audio_widgets.py`.
The task-only patch against the dirty baseline is
`work/audio-timeline-20261007/task-only.patch`, SHA-256
`d34a1117d34cbb78fda9347644554da31726ffef6f030a7abf4c4ce9404b5e40`.
This note records results without changing shared planning documents.

## Focused checks

- Extended `studio_transport_test.py`: exact seek/forward/reverse sample order at
  32/48/96/192 kHz; all requested rates, endpoints, bounded buffering, overview
  cancellation, stale file rejection, coalesced seeks, Stop cancellation,
  redundant rate requests, pause/resume/repeat, shared PCM and cleanup. Real
  decoder/socket; mocked output. Final run passed (`transport-final.log`).
- `waveform_drive_test.py`, `audio_drive_mode_test.py`,
  `preview_playback_test.py`, and `studio_audio_rollout_test.py` passed.
- Actual Qt checks passed for whole-song overview, click/drag positions,
  current/total placement, exclusive switches, callback compatibility, existing
  13 dock IDs and generated Space activation without BONK. Launch-context imports
  were checked with only the normal visuals path on `sys.path`.
- A brief native MP3 output check at 5% accepted PCM at normal speed and all four
  scan rates in both directions; seek while playing, pause and mute were checked.
  Muted output metrics were zero while source PCM continued. The input was
  `C:\ZeraWave\test_audio\Balloon.mp3`, 277.2 seconds, SHA-256
  `94a2a26f01db9854bfc8ee784fc6834ac4799c0960daf180839e12de85fb5754`.
  Output was not listened to; acceptance is not a heard-output claim.
- The first Qt fixture did not await a pending widget synchronization at the end.
  Its failure is retained; correcting the fixture wait produced a passing rerun.
  Final seek-coalescing/rate guards were checked after the native run in the
  transport test. Individual logs, fixture scripts and the final screenshot are
  retained in `work/audio-timeline-20261007`.
- Syntax parsing passed for all six task source files. Task diff reviewed;
  `git diff --check` passed. No new GPU/performance, DPI, physical keyboard/knob,
  microphone, long-session or listening claim is made.

## Robert's short review

Launch Studio, choose Audio File and Open Balloon. Click then drag the waveform;
confirm the marker and current time follow the song. Play/Pause, choose a Scan
rate and use either direction; Play returns to 1× and Stop returns to the start.
Try Loop, mute and Visual drive switches. Audio transport remains separate from
visual transport. User acceptance and listening quality remain Robert's review.
