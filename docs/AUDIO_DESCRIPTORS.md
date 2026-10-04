# Standalone musical descriptors, version 1

This stage adds opt-in numerical measurements to `AudioAnalyzer`. It does not
change live analysis, normalization, scenes, routing, capture or player behavior.
There are no model calls, classifiers or additional dependencies. NumPy is the
only numerical library. Measurements describe signal properties, not genre,
emotion, instrument identity, melody, key, beat, downbeat or song sections.

## Stored concept and scope

`ROADMAP.md` (Standalone DSP in the Next authorized sequence) calls for a
separately approved stage without defining a new architecture. The current
assignment authorizes this bounded numerical portion.

The inspected stored research gives the explicit separation **music features ->
expressive roles -> one persistent authored visual entity** in
`DW Research/Dream Wave research.pdf`, page 33. Pages 34-35 discuss flux,
harmonic/percussive distinction, centroid, loudness and history as potential
features; they do not specify three numbered audio layers.
`Plan and brainstorms/Streamlined Development Plan.pdf`, page 8, gives the longer
Audio -> AudioFrame -> Feature Analysis -> Visual State/Decision Layer -> Visual
Parameters -> Renderer -> Shader/Feedback -> Output pipeline. Its page 7 lists
advanced audio ideas. Neither that document nor the inspected Pinky brainstorm,
current root documents or research index names a THREE-LAYER audio concept.
The exact intended three-layer source remains a question for Bob; no missing
layers were invented. Historical scheduling/restrictions in these research PDFs
do not govern the approved assignment.

The implementation remains inside `app/audio/`. It provides measurements for a
later separately reviewed visual mapping. No new descriptors are art-mapped.

## Existing PCM trace and inventory

The current production/replay path is:

1. `capture.py` requests 48 kHz PCM; `capture_stream.py` owns recorder reads and
   calls its supplied analysis function with 2048-frame packets. Decoded replay
   accepts 48 kHz 16-bit WAV, explicitly scales to float and also uses 2048 frames.
2. `live_visual_test.py:analyze_samples` averages channels to mono, takes an
   unwindowed `AudioAnalyzer.spectrum` rFFT, then measures three mean-magnitude
   bands and positive spectral flux. This orchestration still resides under
   visuals; this stage does not relocate it or alter its arithmetic.
3. `SignalProcessor` normalizes/smooths, detectors detect rises **before**
   `VisualSignalConditioner` limits the continuous signal. The result becomes
   `AudioFrame`. BeatTracker and FrequencyBands append their existing summaries.
4. `parameter_mapper.py` maps bass/mids/highs to scale/movement/sparkle and maximum
   onset to impact. Live/replay/player explicitly forward flux and beat timing.
   `player_runtime.py` drains analysis even while paused and uses fresh packets
   on Resume. Its owner/Stop/recovery paths are unchanged.
5. Twelve bands already use the same legacy FFT in `frequency_bands.py` with
   configurable edges, gain, floor, ceiling and sample-duration attack/release.
   `cymatics_preview.py` publishes meters and optionally routes a selected band
   level into the parked Water basin. `cymatics_controls.py` labels unresolved
   bins/leakage; `cymatics_session.py` stores settings. These are preserved.

| Existing name | Type / units / range | Cadence, conditioning and reset |
| --- | --- | --- |
| `rms(samples)` | float, linear PCM RMS | Utility; not the live energy field. Caller chooses sample shape. |
| spectrum frequencies/magnitudes | NumPy arrays, Hz / unscaled FFT magnitude | One unwindowed FFT per packet, no persistence. |
| raw bass/mids/highs | float, mean FFT magnitude; 20-250 / 250-4000 / 4000-16000 Hz | Packet-size dependent. |
| raw flux | float, summed positive magnitude difference | First or changed FFT length returns zero; stores one preceding spectrum. |
| bass/mids/highs/flux in AudioFrame | float, 0..1 in shared analysis | Bass/high ceilings 16/1; mids/flux fallback ceilings 4/180. Mids/flux use 20-value P5/P95 histories with 8-value warmup and narrow-span fallback. All use 0.5 call-based smoothing, then quiet=.06, attack=.35/release=.08, max delta=.12 conditioning. |
| bass/mids/highs_onset | float, 0..1 | Positive change greater than .2 in processed band before conditioner; previous band state per detector. |
| energy / impact / is_silent | float 0..1 / float 0..1 / bool | Mean conditioned bands / maximum onset / energy <= .02. Constructor derives these unchanged. |
| rhythmic_activity | float, maximum onset | Existing alias of impact, **not** a continuous rhythm estimate. Preserved. |
| beat_confidence / beat_phase / beat_tick / tempo | floats 0..1 / 0..1 / bool / BPM or zero | 192 flux samples; every 8 updates after 96. Autocorrelation within 55-185 BPM lag search; half/double ambiguity. Confidence >=.65 gates tempo/tick; invalid/changing packet duration resets. No downbeat/phrase claim. |
| band12 | dict or None | 12 magnitude means; normalized by 2/N, gain/floor/ceiling into 0..1, levels eased with default .05/.30 s attack/release. Hz edges, bin counts, unresolved flags and resolution metadata included. Not physical power. |
| spectrum_frequencies / spectrum_magnitudes | arrays or None | Packet snapshot for diagnostics; arbitrary frame.__dict__ JSON was already unsuitable when populated. |

Ordinary live packets are 42.667 ms at 48 kHz. Legacy call-based normalization
and beat timing are not newly certified as packet-independent. Source restart
constructs fresh analyzer/processor/conditioner/detectors; there is no new change
to that lifecycle. AudioFrame's old positional constructor remains valid. The
only added field is optional `descriptors=None`, appended after `flux`; existing
consumers ignore it. There is no existing AudioFrame storage migration to perform.

## Offline API and lifecycle

```python
# From app/audio on sys.path; no renderer or capture imports required.
from analyzer import AudioAnalyzer
from audio_frame import AudioFrame

analyzer = AudioAnalyzer()
snapshot = analyzer.describe_samples(normalized_float_pcm, 48000, source_id='fixture-A')
record = snapshot.to_dict()  # finite plain values; independent version=1
# Optional attachment only when explicitly requested by a future caller:
frame = AudioFrame(0., 0., 0., 0., 0., 0., descriptors=record)
analyzer.reset_descriptors()  # end, seek, same-format source discontinuity, restart
```

Use normalized PCM in [-1,1] with shape frames or frames x channels. Integer
PCM must be scaled explicitly; only integer arrays whose values already fit
[-1,1] are accepted as numerical normalized samples. Supported integer rates
are 8000..96000 Hz and 1..8 channels. No resampling or device settings are added.
Rate/channel/source_id changes reset automatically. Source IDs are optional
strings of at most 256 characters. Same-ID seeks/gaps/restarts require explicit
reset. Empty packets consume no time, are not an ending indication, and do not
decay measurements. Feed zero PCM for a measured release; call reset immediately
on EOF/Stop if a cleared snapshot is needed. No wall clock, lookahead, event
queue, packet backlog or partial-window padding is involved.

The processor buffers one window: N = 2*round(rate*(2048/48000)/2), 50% overlap.
At 48 kHz N=2048, hop=1024, duration=42.667 ms, spacing=23.4375 Hz. It analyzes
the first full window, then every half-window; before that it returns invalid,
zero defaults. Whole packets are consumed, including multiple windows in a
large packet. Intermediate windows are processed but only the latest snapshot
is returned. Input packet boundaries affect when the caller can see a value,
not values at equal sample endpoints. `analyzed_seconds` is the latest window
end in source sample time; `pending_seconds` is consumed samples after that end
(during warmup it may approach one window). There is no hard live latency claim.

DC is removed per channel per window. RMS averages unwindowed channel power;
spectral measurements average channel power of the Hann-windowed FFT, rather
than downmixing phase-opposed channels. The descriptor FFT is intentionally
separate from the unchanged legacy FFT: its fixed window, overlap and Hann
semantics cannot be obtained by reusing a variable packet's unwindowed FFT.
It reuses the existing **DEFAULT_EDGES**, with summed **power** per band for
occupancy, not another twelve-band conditioned meter or configurable routing.
Only 20 Hz <= f < min(20 kHz, Nyquist) contributes to spectral measurements.

Persistent arrays have a rate/channel bound: at 96 kHz/8 channels the PCM buffer
is 4096*8 float64 values (256 KiB). One window, frequency vectors/masks, at most
12 previous band proportions and seven smoothed values are kept. No history
grows with session length. Scratch allocations and input validation scale with
the current caller-supplied packet; callers should normally use bounded packets.

## New definitions

All new continuous controls are 0..1 and independently serialized by `to_dict`.
There is no adaptive min/max or per-song retuning. Targets are clipped then
eased with `value += (target-value)*(1-exp(-dt/tau))`; dt is window duration
on first observation and hop duration afterward. Tau uses attack if the target
is higher and release otherwise. Rates below are **seconds**, not frame factors.

| Field | Target definition | Attack / release | Interpretation and confounds |
| --- | --- | --- | --- |
| `rms_dbfs` | 20 log10(DC-removed PCM RMS), floor -120 dBFS | None | Full-scale calibration, not perceptual/LUFS loudness; no frequency weighting or compressor. |
| `intensity` | clip((rms_dbfs+75)/75) | .06 / .30 | Level-sensitive intensity proxy; lower gain stays lower. Not a renamed legacy band-energy mean. |
| `fullness` | (exp(entropy of band power proportions)-1)/(available bands-1) | .15 / .40 | Effective occupied spectral bands. Single-band concentration is low; equal power across bands high. Not instrument count, arrangement density or loudness. Harmonics, EQ, bandwidth/Nyquist and leakage affect it. |
| `transient_activity` | max(positive broad-band proportion change/.35, positive relative RMS rise/.5), clipped | .04 / .35 | Continuous recent attack/texture-change activity; constant gain cancels above floor. Rate is fixed by hop. Repeated percussion drives it, but tremolo, gain jumps, noise and equal-level timbral changes also contribute. No beat regularity or tempo claim. First source window contributes no novelty; a later attack after silence is real activity. |
| `brightness` | power-weighted centroid / spectral upper limit | .12 / .30 | Spectral brightness, not mood. Power weights emphasize strong components; rate-relative normalization differs below 40 kHz. |
| `spectral_spread` | power-weighted frequency standard deviation / (upper limit/2) | .12 / .30 | Spectral dispersion. Widely separated tones can be spread without sounding noisy. |
| `spectral_flatness` | geometric / arithmetic mean selected-bin power, relative 1e-20 log floor | .12 / .30 | Noise-like spectral texture. Finite-window white noise is typically around .56, not 1. Colored noise/EQ/limited bandwidth can lower it. |
| `tonal_concentration` | sum of 12 largest selected-bin power proportions | .12 / .30 | Tonal/peaked-spectrum proxy. Hann leakage occupies several bins per tone; many simultaneous tones lower it. Resonant noise may raise it. It does not measure harmonic relationships or recognize melody. |

`signal_confidence` is clip((rms_dbfs+75)/15) only when selected spectral power
is present. It measures signal availability above the fixed floor, not musical
correctness or probability of tonality/rhythm. `valid` means a complete active
window with nonzero signal confidence. Confidence/validity are unsmoothed;
all continuous controls release toward zero below -75 dBFS. Consumers must
check validity: easing may retain fading values during a quiet release. DC-only
signals are invalid. No floor can distinguish quiet music from environmental
noise; below-floor gain scaling intentionally breaks shape invariance.

## Reproduction and evidence limits

```powershell
.\.venv\Scripts\python.exe app/audio/musical_descriptors_test.py
# Optional full observations and bounded wall-time samples (existing directory):
.\.venv\Scripts\python.exe app/audio/musical_descriptors_test.py --benchmark --output work/standalone-dsp-01/observations.json
```

The standalone script uses deterministic supplied PCM, not a renderer/capture
import. Exact legacy compatibility compiles the unchanged shared analysis
function from source via AST and compares to published baseline c0f82ad, including
existing twelve-band/beat outputs and the committed legacy golden fixture.
This avoids importing UI/GPU/device modules just to validate numerical behavior.

Synthetic fixture contrasts and CPU wall times are evidence for these formulas
at the stated formats. They do not establish all-music understanding, perceptual
quality, accepted-scene improvement, continuous AV listening, natural live
capture, hard latency, or multi-hour runtime behavior. The new stage does not
run automatically in player/Studio/replay. That hookup and any artistic mapping
remain outside this assignment. Source-bound results and known failures are in
`work/standalone-dsp-01/review-index.json`; actual-results handoff goes to Prompter
then an approved fresh independent critic. No commit or publication is included.
