# Standalone DSP stage 01 - actual results

Baseline: `c0f82ad565e41eae29c2cd501a9e2217146d03d0`. Local implementation only;
no commit/push, dependency/environment change, UI, device, capture or GPU work.
Unrelated dirty documents and research folders were not edited. Shared root
documents remain with their owner. Prior startup investigation remains closed
with no runtime optimization in this task.

Implemented an opt-in `AudioAnalyzer.describe_samples` API and optional
`AudioFrame.descriptors` attachment, preserving all old field meanings and
constructors. Fixed sample windows provide intensity, spectral occupancy
fullness, recent transient activity, brightness/spread, flatness and peaked
tonal concentration. The new DSP code is audio-owned and uses existing NumPy
and twelve-band boundaries. It does not run in accepted player/Studio/replay;
there is no new scene mapping or demonstrated scene improvement.

[Technical contract](../AUDIO_DESCRIPTORS.md) records the inspected PCM trace,
existing feature inventory, exact formulas, ranges, cadence, reset, smoothing,
noise floor, heuristic confounds and stored-concept sources. The research's
page 33 three-part feature/role/entity separation is found; no explicitly named
THREE-LAYER audio plan was found. Bob was asked to identify/confirm that source.
This does not block the explicitly approved standalone numerical scope; artistic
or semantic layers have not been invented or implemented.

Validation executed:

- `app/audio/musical_descriptors_test.py --benchmark --output work/standalone-dsp-01/observations.json`:
  deterministic silence/noise floor, tones in twelve bands, sweeps/multitone,
  crescendo/impulse/percussion/endings, equal-level contrasts, above-floor gain
  invariance, packet partitions, 8/16/32/44.1/48/96 kHz and 1/2/8 channels,
  antiphase stereo, reset/source-format changes, invalid input and bounded state.
  Exact old analysis comparison across 240 frames plus 64 committed golden rows;
  constructor/default/attached JSON and legacy mapper compatibility passed.
- Eleven existing standalone numerical/mocked scripts passed through
  `work/standalone-dsp-01/run-preservation.py`, with SoundCard stubbed before
  import. No windows/devices/GL opens. This includes the seven existing recovery
  groups for Pause/Resume/Stop/owner/cleanup, plus the real project WASAPI close
  adapter exercised only against controlled pointers/CFFI callbacks.
- `work/standalone-dsp-01/decoded-observations.py`: first 60 seconds of existing
  Balloon, Chasing You and Warbot Jazz WAVs, then 5.12 seconds supplied silence
  and reset. CPU numerical observations only, no playback/listening. Track/prefix
  hashes, small traces and quantiles are in the pack.
- Syntax and scoped whitespace/diff checks are bound in the final index.

Equal-level sparse/full fixtures produced intensity about .733/.734 and fullness
about .000/.913. Tone/noise concentration was 1.000/.079. Recent activity in the
final sampled steady tone/noise/percussion was .004/.229/.421, respectively;
noise and timbral changes remain confounds, not rhythm recognition. An initial
per-bin novelty design saturated on noise and was corrected to broad-band
proportions before final evidence. An early gain test crossed the documented
noise floor; the final invariance fixture keeps the signal above that floor.
Those failed/intermediate trials and an evidence-write permission failure are
retained in the review index; they are not current passing evidence.

CPU observations: 20 warmup calls and 300 timed whole-DSP calls per format,
~42.67 ms input blocks. Median/p99: 48k mono .626/1.008 ms; 48k stereo
.923/1.107 ms; 44.1k stereo 1.777/2.896 ms; 96k eight-channel 3.254/3.822 ms.
The non-power-of-two 44.1k window trades FFT speed for approximately equal
sample-time window duration. Background ComfyUI/voice load, OS scheduling,
power and thermal state are uncontrolled; no hard latency/live guarantee.
No timing claim compares accepted runtime FPS or capture cost.

No UI/GPU/live-capture/natural-listening or multi-hour run was performed.
Synthetic and decoded numeric evidence does not establish broad music
understanding or artistic acceptance. Persistent state is bounded by format;
the numeric silence continuation is about 60 seconds, not a four-hour soak.

Small reproduction:

```powershell
.\.venv\Scripts\python.exe app/audio/musical_descriptors_test.py
```

Evidence: `work/standalone-dsp-01/review-index.json` binds exact source/diff,
preserved shared sources, results/logs, CPU conditions, stored PDF sources and
remaining questions. Review this opt-in code and its definitions offline; there
is no Studio preview for a code-only DSP assignment. Stop here: actual results
to Prompter, Bob approval, then fresh independent critic. No critic was dispatched
and no next phase or publication was started.
