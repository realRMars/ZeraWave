# Band Analyzer — 2026-10-07

Implemented in the current Qt Studio checkout used by
`C:\ZeraWave\run_zerawave_studio.vbs`. Restart Studio to load it. The dock keeps
its `analyzer` identity and existing placement; its title is now Band Analyzer.
No commit, push, publication, environment change or worker dispatch.

## Controls and readings

- Logarithmic 20 Hz–20,000 Hz axis. Select 31 third-octave-style FFT groups or
  63 equal-logarithmic groups. The 31 centers follow base-10 third-octave spacing,
  with endpoint ranges clipped to 20–20,000 Hz. This is FFT integration, not an
  IEC-certified fractional-octave filter bank or acoustic SPL meter.
- Bars, filled Spectrum, Line and scrolling Spectrogram share the same measured
  source PCM power. Hover shows a measured frequency range and dBFS RMS.
- Columns slider/spinbox: 3–992 with 31 groups, or 3–945 with 63 groups. Fewer
  columns combine power using logarithmic overlap weights. Extra columns
  interpolate measured dB values; they provide no additional FFT resolution.
- Level ±24 dB and Range 20–120 dB affect presentation only. Smooth 0–1500 ms
  applies to Bars/Spectrum/Line; Spectrogram uses unsmoothed source snapshots.
  Spectrogram History offers 2–30 seconds, bounded to 160 records.
- Display choices persist through the existing Qt layout `controls` field,
  independently of artistic/audio settings. Old layouts remain valid.

The 48 kHz, 2048-frame FFT has 23.4375 Hz bin spacing. Narrow low-frequency groups
are marked under-resolved in hover metadata and explained in the controls. A
larger visual column count cannot repair that limit.

## Scope and preservation

One visibility-gated, display-only FFT in the existing AudioOwner supplies both
31/63 summaries, at most five times per second. Cached window/bin geometry avoids
recomputing configuration; the renderer receives no added spectrum payload.
There are no new capture/output owners, streams or changes to engine tuning.
Readings use channel-mean power of the shared source PCM before playback volume,
mute or visual gain, so they also work without starting the visuals.

Pause retains a labelled last spectrum and its original measurement generation;
it is not displayed as live data. Seek, Stop and source changes invalidate old
readings. Existing PCM generation/history semantics stay intact. Hiding the dock
disables FFT snapshots; stale/unavailable readings remain explicit. Spectrogram
rows are cached, bounded raster images rather than hundreds of child widgets.

## Source identity

HEAD remains `ffa67074315b8c2f4fa9d228e82faf0855cc22b8`. The dirty pre-task
baseline, source hashes and exact task-only patch are in
`work/band-analyzer-20261007`. The patch SHA-256 is
`3d0c71344482804f575f5024e30c02f860dceb690544a6a2e2507c4fdb906666`.
`result.json` binds the six source/test files and validation logs. All 231
preservation hashes passed, including saved layouts, renderer, previous audio
work, launcher and existing task notes. This note does not change shared plans.

Changed: `app/audio/band_display.py`, `app/audio/studio_transport.py`,
`app/visuals/studio_qt.py`. Added: `app/visuals/studio_band_analyzer.py` and the
existing-style standalone checks `app/audio/band_analyzer_test.py` and
`app/visuals/band_analyzer_view_test.py`. The existing 12-band display math remains
equivalent; it shares a power-spectrum helper and retains its calibration tests.

## Actual checks and limits

- `band_analyzer_test.py` passed: tone location/energy, opposite stereo phase,
  silence, Nyquist/FFT limits, cached geometry, visibility/throttle, source
  generation, pause hold, packet bounds and independence from volume/mute/raw
  drive. Existing 12-band calibration/release fixtures passed.
- `band_analyzer_view_test.py` passed: all four Qt modes at minimum/measured/
  maximum density for both group counts, power reduction, selectors/sliders,
  settings validation/round-trip, paused/stale/source-change states and history
  bounds. Synthetic PCM; no device/output or renderer.
- `studio_transport_test.py` passed its existing conversion, shared PCM, capture
  without replay, output volume/mute, seek/rate/reverse, cleanup and failure
  checks. Real decoder/socket with mocked devices/output.
- Actual Qt/control-owner smoke passed with Balloon MP3 output muted throughout:
  readings while visuals were stopped, all views, Pause, hide/show, seek/Stop,
  display settings save/restore, unchanged artistic values and all 13 dock IDs.
  No renderer was launched. The owned control process exited.
  Input: `C:\ZeraWave\test_audio\Balloon.mp3`, SHA-256
  `94a2a26f01db9854bfc8ee784fc6834ac4799c0960daf180839e12de85fb5754`;
  a few seconds beginning at 97 seconds, followed by a seek to 80 seconds/Stop.
- The initial actual-Qt run exposed clearing the display on Pause. Its failed
  run is retained; preserving a labelled held snapshot corrected it. Subsequent
  focused backend/widget/actual-Qt checks passed.
- Six source files parsed successfully; exact task diff reviewed and
  `git diff --check` passed. No dependency installation, physical input/DPI,
  natural listening, renderer FPS/GPU or multi-hour validation was performed.

## Bounded component cost

The retained `component-costs.json` uses fixed 48 kHz, 2048-frame opposed-stereo
1007.8125/8015.625 Hz tones, a 760×205 logical-pixel Qt chart at DPR 1, twelve warm
calls then 100 timed calls. FFT summarize and `QWidget.render` to a preallocated
raster pixmap are measured separately. The 30-second recolor probe has 12 timed
calls. Background load/power/temperature were uncontrolled. These measurements
precede final label/legend polish and do not measure ordinary playback or scanout.

The combined 31/63 FFT median was 0.20 ms, p95 0.24 ms, maximum 0.28 ms.
Default 31-bar raster paint median was 1.16 ms; maximum-density bars were about
5.6 ms, compared with about 0.68 ms for the former 12-bar chart. Thus the richer
chart is more expensive to paint; no overall engine speedup is claimed.

The original full-history Python pixel recolor took about 376 ms median at 992
columns/30 seconds. NumPy rasterization reduced that matched component probe to
16.7 ms median, p95 17.1 ms, maximum 17.3 ms; cached Spectrogram paint was about
1.6 ms. Both results are retained. This correction addresses slider latency,
not renderer performance. Snapshot cadence remains capped at five per second
and hidden display work is disabled.

## Robert's review

Restart the Studio launcher and reveal Band Analyzer through View. Play a file
or select Device Listening, then try Bars/Spectrum/Line/Spectrogram. Compare
31/63 groups, move Columns and use Level/Range/Smooth or Spectrogram History.
Hover to inspect measured bands. Pause/seek/Stop and hide/reveal the dock to
check its labelled state. User acceptance remains Robert's review.
