# Audio output volume and raw waveform visual drive — actual results

Implemented in `C:\ZeraWave`, used by `run_zerawave_studio.vbs`. Restart that
launcher to load this source. No commit, push, publication, installation, worker
dispatch, shared planning edits or source reset.

## Behavior and scope

The old file output multiplied decoded PCM by 0.2 (about -14 dB). Session
Waveform now exposes 0–100% output volume; the new run default is 100%, unity.
The change removes that fixed attenuation rather than tuning normalization from
one song. Output is bounded to digital full scale, with source overs and output
clipping reported. Original PCM, analyzer bands, waveform, and either visual
drive remain independent of output volume and mute.

The shared Session Waveform switch, also synchronized in Settings → Audio,
selects analyzed musical response (OFF, default) or original channel RMS/peak
amplitude (ON). Raw mode maps RMS to bass/scale and mids/movement, peak to
highs/sparkle, and positive amplitude changes to flux/event response. It has no
inferred tempo/beat. Original FFT/band/descriptors continue to be collected.
Existing visual input bounds, authored response formulas, static artistic
settings and integrated clocks remain in place.

Raw mode parks user audio gains and selected listening-window substitutions
across Main form/transition uniforms, CPU consumers, shared effects, Planet/sky
presentation, and Artifacts. It keeps existing analysis/listening histories warm
and leaves saved settings/revisions untouched. OFF resumes those settings. The
same PCM owner continues capture or file transport; switching visual drive does
not reopen streams or change source generation. Mode revisions reject queued
frames from an older selection and suppress first-frame events.

Analyzer tooltips identify measured pre-output digital bands; the mapping monitor
identifies applied CPU gains and raw bypass; source/output RMS, source peak and
clipping have explicit scope. These are not speaker SPL or GPU pixel readback.
Existing isolated Experimental audio routes do not share this owner; the service
rejects audio-source/raw-drive actions during those previews. Volume and mode
are runtime state, not new persisted artistic/session settings.

## Source identity and preservation

HEAD: `ffa67074315b8c2f4fa9d228e82faf0855cc22b8`. HEAD is not the full candidate.
The exact pre-task dirty copies and SHA-256s are in
`work/audio-volume-drive-20261007/before/` and `baseline.json`. An additional
pre-edit copy of `studio_control_service.py` is included. `result.json` records
all 14 changed/new code and test file identities. The task-only patch includes
new files and excludes previously accepted audio fixes and unrelated dirty work.

Patch SHA-256: `b25a92163bbb7c69eae4282cb7cbcdf47c6d6c5e5da0c7d898f3abcc9cc5f188`.

The launcher, saved Qt/workspace layout files and three unrelated dirty notes
match their preceding integration hashes. All 13 dock IDs and existing Settings
resolution entry were retained. Accepted native output, BandDisplay and previous
musical-descriptor test changes remain intact. No shader or authored file edits.

## Checks actually performed

- Eight passing standalone checks: waveform_drive_test, studio_transport_test,
  musical_descriptors_test, audio_drive_mode_test, studio_audio_rollout_test,
  studio_audio_availability_test, studio_audio_binding_test, preview_playback_test.
  These cover direct amplitude, anti-phase stereo, silence/rise/overs, unchanged
  analyzed fields, unity/50%/mute output, original PCM independence, mode revision,
  stale-frame rejection, neutral gains, all declared Main/transition targets,
  retained histories/revisions, saved tuning restoration, and existing transport.
  Hardware is mocked in the transport suite; PCM/socket/FFT paths are real.
- Actual Qt/control smoke: volume slider, both mode-selection entry points,
  preserved docks/artistic values, and widget painting. Verified Balloon MP3
  (`test_audio/Balloon.mp3`, SHA-256
  `94a2a26f01db9854bfc8ee784fc6834ac4799c0960daf180839e12de85fb5754`).
  Brief native playback at 10% accepted output; output/source RMS ratio was 0.1.
  Mute reduced output RMS to zero with continuing PCM; pause released output and
  froze PCM; stop rewound. Output was not listened to.
- Brief normal embedded Qt Main render loop with the verified MP3 muted:
  analyzed and raw telemetry, raw RMS/peak matching current engine inputs,
  neutral gain submissions, audio progression while visual playback paused,
  and resumption in the same renderer process. No performance claim or scanout
  measurement. A QWidget grab did not capture the foreign GPU child; the retained
  dark `gpu-preview.png` is unsuitable as visual evidence. Visible widget captures
  are `session-waveform.png` and `raw-meters.png`.
- Imports, AST syntax for every changed Python file, task-only diff review and
  `git diff --check` passed. Only pre-existing unrelated-note line-ending warnings.

Individual logs, JSON states, fixtures, captures and failures are retained under
`work/audio-volume-drive-20261007/`. Initial test fixtures used an incorrect
target/omitted FFT metadata and assumed non-null pre-PCM telemetry; corrected
fixtures pass. The Qt check exposed a pending-volume snapshot briefly reverting
the slider, fixed by waiting for its authoritative acknowledgment. No unresolved
test failure remains.

## Robert's short review

Open `run_zerawave_studio.vbs`. In Session Waveform choose Audio File and Open a
track. Set Output volume to a comfortable percentage, then Play. Start Main
visuals separately. Compare the raw switch OFF/ON, change output volume and Mute,
and observe that source/analyzer levels continue independently. OFF restores the
existing frequency-based musical response and saved tuning. Raw ON is direct
amplitude, so RMS/peak meters replace frequency interpretation for visual drive.

Listening quality, physical control interaction, isolated Experimental behavior,
all-scene motion, sustained playback and long-session performance were not
established by these short checks. Robert owns user acceptance; no reviewer was
dispatched.
