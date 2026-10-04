# Planet Starfield — real spectrum and bounded frequency-window tuning

2026-10-03. Approved minimal refinement of the separate audio tuner. Robert owns
native testing and acceptance; independent critique remains HOLD. No commit/push,
root-document update, player change, other-world routing or native capture.

## Use and semantics

After the current call/preview is finished, relaunch `run_development_studio.bat`;
existing Python processes do not load edited modules automatically. File → Load
session… → `work/planet-canvas-star-attack-01/star-candidate-session.json`. Choose
**Live system audio**, Start once, then View → **Starfield audio tuning…**.
The existing Planet mapping monitor remains read-only and byte-unchanged.

The full FFT spectrum is pinned above the scrolling controls. It stays visible
under tuning bypass and in a held Planet preview with the star pilot OFF. DC is
excluded. Current full packets have 1,024 positive bins, 23.4375 Hz spacing,
42.667 ms duration and 24 kHz Nyquist. Metadata comes from the actual delivered
sample count/rate and verifies the existing frequency grid; short odd packets have
their actual maximum bin below Nyquist. No twelve-band interpolation is involved.

Cyan shows actual FFT-bin peak amplitude, `20*log10(magnitude*2/N)`, with `1/N`
normalization for an even packet's Nyquist bin. Display floor is −120 dB; this
amplitude convention is not RMS or power. Transport rounds the displayed values
to 0.1 dB; original detector magnitudes are untouched. Low-frequency bin markers,
sample age and the rectangular/no-overlap window label make resolution explicit.
Connecting the measured points does not recover additional frequency detail.

Amber shows **acknowledged applied** coefficients, not requested slider positions.
Controls are Start Hz and End Hz in 20–315, selected-window Weight 0–2 and attack
sensitivity 0.5–2. Start is inclusive; End exclusive. Start must be below End and
the window must include an actual FFT bin. Empty selections are rejected while
the previous applied settings/curve remain. The ACK readout lists exact included
bin centers/count. A 60–100 Hz selection includes 70.3125 and 93.75 Hz only.

Weight multiplies the selected bins before their sum is divided by the original
20–250 Hz bin count: it is an attack contribution, not a normalized-away gain.
Weight 0 removes this window; weight 2 doubles its contribution. A narrower window
generally collects less magnitude. Sensitivity above 1 lowers existing thresholds.
Speech/picked bass/drums can share frequencies; this is not instrument or kick
classification. Mid/high controls above 315 Hz are visible but disabled at weight
0 and labeled **Spectrum available; not routed to star detector.**

Reset restores **the exact delivered 20–250 mean, weight 1, sensitivity 1,
250–315 extension OFF**. The reset path returns the original caller-supplied mean,
including its original arithmetic, even on an unresolved short packet. Bypass
uses the same reviewed detector. Detector reset here means restoring settings;
it does not restart capture, scene time or flight history.

Old multiweight settings/packets remain accepted with exact prior calculations.
When their coefficients form one contiguous plateau they can be shown as one
window. Otherwise the UI explicitly labels them as legacy, disables frequency
controls and keeps the original configuration/curve. Sensitivity/bypass edits
retain those original weights. Reset explicitly chooses the reviewed single
window; there is no silent collapse. Nothing new is saved in sessions/profiles.
Closing the panel retains this preview's applied trial settings and stops its
spectrum publication; a new preview starts at the reviewed settings.

## Scope, reusable parts and source

`app/visuals/spectrum_widget.py` contains a small `SpectrumTarget` descriptor,
bounded latest-only `SpectrumFeed` and shared `SpectrumWidget`. Only the star
adapter is implemented, declared in `starfield_tuning.py` with its label, allowed
20–315 range and attack → travel-speed/trail-length feature. No generic router or
asset framework. Spectrum observation consumes the already-produced AudioFrame
arrays at the existing live/replay frame-consumption point, independently of the
detector flags. It adds no FFT, PCM capture, mailbox drain or GPU readback.

The existing attack → envelope → `u_planet_star_flight` → trail/speed chain is
unchanged: 80 ms guard, 90 ms pulse release, 15/70 ms display rise/fall; rate
`1+.75*envelope`, positive integrated phase; shader trail length
`mix(.0012,.095,envelope²)`. Shader, dots/geometry, brightness, apparent zoom/shared
scale, shooting stars, shared drift, materials/spatials/palettes/manual colors,
surface mapping, original detector and unrelated worlds are preserved.

HEAD remains `0342e518a7bd2c521416e8027a7920668fc5ee51`. The dirty-source identity,
pre-task snapshots, exact task-only diff, final-source snapshots and checks are
bound in `work/planet-star-spectrum-tuning-01/review-index.json`. Six existing
files changed: band_attack_tuning, starfield_tuning, renderer, live_visual_test,
replay_test and starfield_tuning_test. New files are the shared widget, standalone
spectrum_tuning_test and this note. The older tuner test keeps its numerical and
runtime checks; obsolete fixed-band UI checks are carried into the expanded
constructor/callback checks. Prior evidence indexes/artifacts remain frozen;
their source snapshots identify earlier versions, not arbitrary new settings.
The six standalone DSP files remain unchanged by hash.

## Actual checks and limits

- Final `spectrum_tuning_test.py` PASS: actual/odd FFT metadata, Nyquist amplitude,
  packet validation/bounds, ordered/nonempty selection and persistent rejection,
  exact Reset/bypass/short-packet reset, meaningful ×2 weight, native Python float
  detector boundary, and 100 exact old multiweight calculations.
- 120 complete analyzed AudioFrames match the original route while the window
  baseline and spectrum observer are active. Existing baseline checks also match
  1,200 detector packets and 120 complete AudioFrames exactly.
- Actual UI constructors/callbacks/coordinate drawing with inert widgets PASS:
  full spectrum, ACK-only curve, exact bin labels, disabled unsupported controls,
  retained legacy configuration, Reset, new-preview defaults, no persistence
  changes, one poll after reopening, 1,000 slider changes → one pending timer,
  bounded Canvas items. This is not native Tk layout/repaint validation.
- Actual live owner, real CaptureStream/ColorInbox/ColorLink threads and OS pipes,
  synthetic capture and mocked graphics PASS: fine window → bypass → Reset
  revisions acknowledged at analyzed packets, one start/stop, normal cleanup and
  monotonic phase. Final control-to-analysis latency: 23.11/36.11/35.73 ms in this
  paced synthetic run. All ACKs carry 1,024 positive spectrum bins. A separate
  pilot-OFF run carries those bins with zero star-detector analysis frames;
  ordinary FFT/descriptor analysis still runs. Telemetry is not appended to logs.
- 125 ms synthetic65Hz attacks: 23/23 accepted events at reviewed defaults and
  at the explicit test window 60–100, weight 2, sensitivity 1.25. Guard/rate/phase
  checks PASS. That trial is not a recommended current-song profile. Sustained
  bass and louder mid/high fixture attacks remain zero at defaults; picked bass
  and synthetic speech-like negatives still produce 14 positives each.
- Existing planet_star_attack_test, planet_mapping_monitor_test and legacy
  starfield_tuning_test PASS. Syntax and `git diff --check` PASS.

Retained failures: the first test compared a floating-point product to a decimal
literal; the later rapid-hit test caught a real implementation bug where a NumPy
scalar was rejected by the detector's strict Python-float contract. The sum now
returns a Python float and final rapid-hit/propagation checks pass. Failure logs
are preserved; intermediate failed source hashes were not captured, so they are
not presented as source-bound final validation.

Publication remains at most 10 Hz; existing dedicated GUI poll is nominally 50 ms.
Latest magnitude storage is one array of at most 1,025 bins, one transport record,
one pending control, and an existing 64-entry completion deque. Fixed graph axes
and x-coordinates are cached; no spectrum/history logs accumulate. CPU full
snapshot+JSON: 1,000 calls, p50 0.414 ms/p95 0.515 ms/max 0.745 ms, largest 8,526-byte
packet versus 16,384 limit. Actual callback/drawing with inert widgets: 200 frames,
p50 1.813 ms/p95 2.030 ms; native repaint remains unmeasured.

Matched whole-analysis-plus-observation CPU microbenchmark: same 8-second synthetic
PCM, 48 kHz, 2048-frame packets (short final packet), both pilots/window baseline,
fresh state, three order-alternating passes, 564 packets/arm. p50/p95 ms:
no feed 1.200/1.788; closed feed 1.178/1.716; visible feed 1.236/1.722. No-feed max
18.477 ms is retained; background load was uncontrolled. No speedup, FPS or device
throughput claim follows from these timings.

No native Tk window, real capture device, GPU preview, call recording, adjusted
normal-speed musical listening or multi-hour soak was run. Native layout/repaint,
actual-device ACKs and visual/musical response await Robert's safe-window trial.
The builder is not using GPU/native preview and has no capture planned; the
separately authorized website asset capture can be serialized by Bob.
