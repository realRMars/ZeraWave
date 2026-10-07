# Band Analyzer refinement — 2026-10-07

Implemented in the root working checkout for the existing
`run_zerawave_studio.vbs` launcher. Robert's current request covers low-frequency
gaps, responsiveness, contextual History, slider resets and analyzer colors.
No renderer, audio output/capture, artistic mapping or docking redesign.
User review remains the acceptance gate; no worker or reviewer dispatched.

## Visible behavior

- Bass no longer falls into artificial empty FFT groups. An 8192-frame diagnostic
  PCM ring and fractional FFT-bin energy overlap provide continuous estimates;
  broad upper groups keep their short 2048-frame window. True silence stays zero.
  Narrow groups remain estimates, with honest FFT-spacing/under-resolution help.
- The analyzer now follows PCM cadence (normally 23.4 snapshots/s, capped at 33),
  using a small independent telemetry projection and 33 ms view timer. General
  Studio/resource polling remains 200 ms. Hiding the dock disables its FFT work.
- History's entire row appears only for Spectrogram; Smooth appears only for
  Bars, Spectrum and Line. New/default smoothing is 60 ms (previously 200 ms);
  previously saved slider values are restored unchanged.
- **Reset sliders** restores Columns to the selected group count, Level 0 dB,
  Range 60 dB, Smooth 60 ms and History 10 s. Right-click each slider or the
  Columns number box to reset it alone. Mode, group count, colors and source stay.
- Studio Cyan, Galaxy Ember, Aurora and Violet Pulse presets plus **Edit
  gradient…** for three local Low/Mid/High colors, pickers and validated hex
  values. Cancel keeps the existing colors. Preferences use the existing
  `controls.band_analyzer` layout storage; they do not edit scene pigments.
- Reuse bar geometry, spectrum paths and spectrogram color rows. Project history
  onto physical screen rows before expanding frequency columns and use one
  cached raster blit. Short telemetry delays hold the last display snapshot;
  longer interruptions leave gaps. Source history is bounded to 1024 snapshots.

## Source and preservation

HEAD stayed `ffa67074315b8c2f4fa9d228e82faf0855cc22b8`. HEAD alone does not identify
this candidate: substantial prior dirty/untracked work was present and retained.

Evidence: `C:\ZeraWave\work\band-analyzer-refine-20261007`.
`baseline.json` and `before/` bind the actual dirty pre-task source;
`results.json` records all eight before/after source SHA-256 values and checks.
`task-only.diff` is solely this task's delta, SHA-256
`ce9b803aa4beff86945b0aaf68ac782e89e805508dba0e618e06d42a0b3d66df`.

Changed: `app/audio/band_display.py`, `studio_transport.py`,
`band_analyzer_test.py`; `app/visuals/studio_band_analyzer.py`,
`band_analyzer_view_test.py`, `studio_control_service.py`,
`studio_control_client.py`, `studio_qt.py`; this task note.

All 230 pre-recorded preservation hashes matched, including unrelated app
source, settings/layout, launcher and older notes. The existing 12-band artistic
metrics, renderer source, PCM handoff, output volume/mute, raw visual drive,
source generations, pause/seek/stop boundaries and 13 dock identities remain.
Launcher SHA-256:
`0720bc451a5215fadcfad40c2acecd07c1db28bbc994326d52fc95cad9033620`.
No dependency/environment change, commit, push or publication.

## Focused checks and observed response

Passed existing standalone `band_analyzer_test.py`,
`band_analyzer_view_test.py`, and `studio_transport_test.py`; logs retained.
Coverage includes synthetic tones, energy/phase, true silence, fractional bass
coverage, cache/ring bounds, unchanged old 12-band fixtures, visibility/throttle,
source boundaries, stale telemetry rejection, all four views, minimum/maximum
columns, contextual rows, individual/all reset, preset/custom accept/cancel/
validation/persistence, time-gap/cache behavior, transport/decoder/mock-output
regressions. AST parsing of eight changed Python files and `git diff --check`
passed. The task diff was reviewed separately from pre-existing dirty changes.

Actual Qt/control-owner check: `C:\ZeraWave\test_audio\Balloon.mp3`, SHA-256
`94a2a26f01db9854bfc8ee784fc6834ac4799c0960daf180839e12de85fb5754`,
97–101 s, four seconds, muted before Play, no renderer started. Same
1600×980 window, 464×145 chart, DPR 1, 31 groups/243 columns, Range 120 dB,
Smooth 75 ms. Snapshot stamp to **first Qt paint completion**:

| Recorded distribution | Before | After |
| --- | ---: | ---: |
| Unique first paints | 17 | 74 |
| Median age | 231.56 ms | 54.48 ms |
| p95 / p99 | 305.02 / 312.69 ms | 80.33 / 92.49 ms |
| Maximum age | 314.61 ms | 97.16 ms |
| Unique first paints/second | 4.25 | 18.5 |
| Warm median, sequence ≥24 | 251.37 ms (12) | 51.18 ms (53) |

Individual rows and recipes retained. This measures diagnostic delivery, not
capture latency, audible response, renderer FPS or scanout. It excludes the
audio window's averaging: bass/narrow groups need up to 171 ms of PCM; broad
upper groups use 43 ms at 48 kHz. Under-resolution remains at the lowest bands.

The separate full-width synthetic check uses seed-17 stereo broadband noise plus
62.5 Hz sine, same PCM prefix, 1647×360 chart/DPR 1, QWidget raster rendering,
eight warm calls then 40 samples (12 for history recolor). Final median costs:
FFT 0.20→1.00 ms; fresh 243-column Bars 9.87→10.38 ms; cached maximum-density
Spectrogram 3.16→2.70 ms. The bass estimate costs more FFT work; the principal
responsiveness gain is removing the three slow diagnostic update stages.
Broadband structural zero groups below 100 Hz went from 4/11 to 0/0 (31/63).
History recolor was 18.75→21.56 ms, with different retained-history workloads:
old 160 rows versus new 750. This is not a matched per-row speedup claim.
Power/temperature/background activity were uncontrolled.

Retained intermediate path and raster paint regressions (approximately 114 ms
and 16 ms Bars) were discarded from the implementation. An initial 234.375 Hz
tone test exposed a window-boundary energy mismatch; the adaptive narrow-band
rule corrected it. That first failure was console-only. The initial latency run
used a chart three pixels narrower; it is retained as an intermediate and excluded
from the matched result above.

One brief real-file Qt visual smoke also passed pause/held readings, seek/clear,
stop, hide/show, presets/resets, layout preferences, unchanged authored values and
13 docks; its owned control process closed. `smoke.json` and the actual widget
captures `bars-galaxy-ember.png`, `spectrum-aurora.png`,
`spectrogram-aurora.png` are retained. Output was muted throughout; no heard-output,
live-device, simultaneous renderer-load, DPI-hardware or multi-hour claim.

## Robert's review

Restart the existing Studio launcher. Open Band Analyzer, play a track, choose
Bars/31 groups with around 243 columns and compare the bass and response.
Try Spectrum/Line, then Spectrogram: History appears, Smooth disappears.
Right-click a slider, then try Reset sliders. Select a color preset and use Edit
gradient; verify Cancel preserves the previous colors. This is ready for user
review, with no automatic next phase.
