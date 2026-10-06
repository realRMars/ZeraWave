# Studio Audio Hub — Builder results

> Publication status — October 6, 2026: Robert authorized this development
> checkpoint for commit and normal push. The original results below retain
> their own validation limits and pre-publication status.

Studio audio hub — 2026-10-06 (America/Chicago)

Implemented for normal Qt Main playback:
One independent audio owner in the retained control process, with a bounded
48 kHz stereo PCM handoff to the existing renderer analysis. Device listening
uses existing exact-ID enumeration/capture and never opens an output stream.
File playback and analysis use the same decoded PCM. File transport/mute/repeat
are separate from visual Start, Pause/Resume, Hold and BONK. No renderer context
recreation, shader/artist changes, or analyzer-history clearing was introduced.
Normal renderer restart retains its existing new-renderer/history boundary.

Session Waveform and Settings > Audio share source/device/import actions and
owner snapshots. Open/Play/Pause/Stop/Repeat/Mute are in Session Waveform.
Preview setup uses the same source/import state. All 13 docks retain their IDs.
Errors use existing nonmodal status/log surfaces. Invalid import keeps the last
working source. Unconfirmed output/capture release blocks replacement.
WAV/MP3 decode uses SoundFile 0.13.1, installed only after explicit approval;
libsndfile 1.2.2. PCM WAV fallback is retained if SoundFile is absent.
Mono/stereo 8–192 kHz are accepted; non-48-kHz material uses continuous linear
sample-rate conversion. Output has fixed 0.2 gain; mute leaves analysis intact.

Observed checks:
- Standalone studio_transport_test.py: real WAV decoding/resampling and local
  PCM bus; mocked capture/output. No capture replay; shared PCM; mute, pause,
  stop, EOF repeat, invalid import, ambiguous-close blocking, cleanup passed.
- Actual Qt/control process: MP3 import readiness, synchronized source menus
  and combos, device/file visibility, 13 docks, unchanged artistic values and
  no spontaneous capture/output passed. Test-owned layout/log paths only.
- Actual live main + HubStream + analyzer with mocked graphics/output: visual
  pause froze drawing time while audio advanced; resume used one context
  creation; no local capture constructor was called. Existing preview clock,
  Hold, BONK, stale-run and capture-selection CPU checks passed.
- Short physical loopback/MP3 smoke on Headphones (BlackShark V3 Pro BT):
  analysis-only capture delivered PCM, released its WASAPI references before
  file playback, SoundCard accepted file output, mute continued PCM/analysis,
  pause froze the playhead, resume progressed, stop rewound and closed output.
  Workers exited. See smoke.json and retained smoke-initial.json.
- Syntax and git diff --check passed; task-only diff reviewed.

Input: C:\ZeraWave\test_audio\Balloon.mp3, 7,128,530 bytes, 48 kHz stereo,
277.2 seconds. SHA256:
94a2a26f01db9854bfc8ee784fc6834ac4799c0960daf180839e12de85fb5754
The originally supplied test audio path with a space did not exist. The user
supplied this underscore path before the checks. The MP3 was never modified.

Limits / remaining integration:
- Output was accepted by the real backend, not observed by listening. No claim
  of heard output, measured speaker latency or continuous AV listening.
- The waveform shows a rolling recent PCM amplitude envelope, not a whole-file
  timeline. No seeking. The playhead is submitted PCM, not physical scanout or
  measured speaker position; session PCM count stays monotonic across repeats.
- Main's existing analysis histories stay resident over audio pause/source
  boundaries; boundary onset packets are suppressed rather than resetting
  histories. Visual pause still rejects old presentation packets on Resume.
- Separate legacy Experimental routes keep their own audio semantics and are
  not wired to this owner. Shared audio must be stopped before those routes;
  starting/switching shared audio while such a preview runs is rejected.
- Existing matched source-rewind audition is unavailable on this live PCM
  route. No promise of matched offline diagnostic replay through this owner.
- Microphone capture, physical keyboard/DPI interaction and normal GPU Main
  playback were not observed in this bounded audio pass. No long/soak/audit run.
- Two early standalone attempts failed: sandbox temp permissions, then decoder
  cleanup after an injected ambiguous output close. The latter was corrected
  so independent decoder resources close even if output release is ambiguous.
  Pip's first attempt also hit sandbox temp permissions; the approved install
  succeeded with a repository-local temporary directory. No other package
  installation or environment upgrade was performed.

Review: Settings > Audio > Import audio; use Session Waveform Play/Mute/Pause/
Stop. Visual transport remains in its existing Transport tab. For listening,
choose Device Listening and an exact output-loopback or explicit microphone.

Source identity: source-final.json; task-only delta: task-only.patch; baseline
copies: before/. Published HEAD remains 4a4f6e03ad2119e790e88d8338bac9412a139881.
Substantial pre-existing dirty/untracked work was preserved. No root planning
docs, authored settings, user layout or audio file were edited. No dispatch,
branch, commit, push, publication, broad test suite or engine rewrite.
