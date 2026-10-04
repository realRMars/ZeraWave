# Planet Starfield live tuning — bounded current-preview trial

2026-10-03. Sole builder's actual results for the approved live tuning extension.
Robert owns native testing and artistic acceptance; independent critique remains
on HOLD. No commit, push, shared-root-document edit, player change or rollout.

## Implementation and review steps

1. After the current call/preview is finished, launch `run_development_studio.bat`.
   An already running Python process cannot load these new modules automatically.
2. File → Load session… →
   `work/planet-canvas-star-attack-01/star-candidate-session.json`.
   This existing session selects held Planet Canvas and both reviewed pilots.
3. Select **Live system audio** as Source, then Start preview once. Use the
   intended music output/device. The builder has not recorded the call or opened
   any real capture device for this tuning task.
4. View → **Starfield audio tuning…** opens the separate scrollable window.
   View → Planet mapping monitor… remains a separate read-only view.
5. Adjust one bounded scale, observe **Applied revision** and measured band means,
   then compare the same passage. Pending is distinct from acknowledged settings.
   Settings apply at the next analyzed packet through the existing worker/pipe;
   no capture restart, flight-phase reset, extra FFT or extra mailbox drain.
6. **Reset to reviewed baseline** restores the exact reviewed detector:
   low/body/upper weights 1, extension 0, sensitivity 1. Unchecking **Use tuning**
   also uses that detector while the Starfield pilot remains active. A classic
   pilot-OFF preview reports bypass and disables tuning controls.

The five controls are 20–40 Hz weight, 40–160 Hz weight, 160–315 Hz weight
(each 0–2), 250–315 Hz extension (0–1), and sensitivity (0.5–2). No Hz entry
or saved profile. Below-30 Hz measurement is included in the first existing band;
no audible output is filtered. Disjoint half-open partitions are 20–40, 40–160,
160–250 and 250–315. Upper weight scales 160–250 once and 250–315 only in
proportion to extension. Baseline denominator remains the original 20–250 bin
count; weights are explicit contributions, not renormalized proportions.

Sensitivity above 1 lowers level/rise/relative thresholds; below 1 raises them.
On a weight change, the preceding measured spectrum summary is reevaluated under
the new weights so the knob itself does not create a false rise. Sample time and
existing flight history continue. Closing the window keeps applied trial settings
for this preview and stops its telemetry. A new preview starts at reviewed values.
There is no song classification or automatic song-boundary detection.

Dotted star trails, fixed attack release/display smoothing, motion bounds,
shooting stars, shared drift, surface mappings, materials/spatials/palette/manual
colors and session persistence are preserved. Material weight readouts explicitly
describe selection/blending; a zero or fixed weight does not measure animation.

## Source and exact scope

HEAD remains `0342e518a7bd2c521416e8027a7920668fc5ee51`. Dirty source, not HEAD
alone, identifies the candidate. `work/planet-star-live-tuning-01/pre-task.json`
binds the actual pre-task source snapshots and preserved standalone DSP/artifacts.
`review-index.json`, `task-diff.patch` and `final-checks.json` in that same folder
bind the resulting source, per-task delta, checks and artifacts. Earlier star CPU,
GPU and monitor indexes remain unchanged; those frozen GPU captures describe the
earlier default detector, not arbitrary new tuning settings.

Eight existing files changed: `low_band_attack.py` (optional sensitivity),
`planet_star_attack.py` (optional helper), both existing live/replay callers,
`renderer.py` (bounded commands/scalar status), `studio_color_link.py` (existing
pipe), `studio.py` (separate View action/poll), and `planet_mapping_monitor.py`
(explanatory text only). New modules are `app/audio/band_attack_tuning.py`,
`app/visuals/starfield_tuning.py`, `app/visuals/starfield_tuning_test.py`.
This note is the sole new task note. No shader or PlanetStarFlight class change.
The six uncommitted standalone DSP files were preserved by hash. Unrelated dirty
work was not staged, reverted, cleaned or committed.

## Executed evidence

- Final standalone tuning CPU check PASS: exact reviewed detector outputs for
  1,200 packets and entire analyzed AudioFrames for 120 packets; disjoint edges,
  bounds/invalids, exact Reset/bypass, no knob-created rise, no clock/phase reset.
- Actual live owner and real CaptureStream/ColorInbox/ColorLink threads/OS pipes
  with synthetic PCM and mocked capture/graphics PASS. One capture start/stop,
  revisions 1 then exact Reset revision 2 acknowledged in analyzed packets;
  final run measured 24.85/38.22 ms control-to-analysis, 82 analyzed frames/83
  reads (last read stopped before analysis), normal cleanup. This is not native
  live-device or Tk/GPU validation. Telemetry is excluded from the run log.
- Actual UI callbacks with inert widgets PASS: 1,000 slider changes coalesce to
  one pending timer, applied values/stale/bypass/new-preview Reset work, reopening
  cancels the old poll, session/save/load/default/command AST is unchanged.
  500 inert refresh calls: p50 0.047 ms, p95 0.078 ms; not Tk/native paint cost.
- Existing `planet_star_attack_test.py` and `planet_mapping_monitor_test.py` PASS.
  Syntax and `git diff --check` PASS. Failed test-only UI wording/nested-method
  extraction trials remain in evidence logs; their final corrected checks PASS.
- Existing synthetic 125 ms fixture: 23/23 accepted events; sustained bass,
  louder mid attacks and louder high attacks: zero. Picked bass: 14 positives.
  Explicit synthetic speech-like negative: **14 positives**. These settings tune
  a low-frequency attack proxy; frequency cutoffs do not isolate drums or reject
  speech. No person/call was recorded.

The old mapping view remains nominal 5 Hz. The separate tuning window polls
nominally every 50 ms; scalar telemetry/interval peaks emit at most 10 Hz from the
existing render owner, only while visible. It reports actual analysis completion
interval, audio packet duration, snapshot/peak-hold interval, GUI callback interval,
ages and positive/accepted counts separately. Analysis sample time and render
consumed sample time are both carried. No DSP smoothing was changed.

In the ideal 60 Hz CPU timer model, the old 200 ms display intervals grouped the
23 fixture events into 15 active intervals (8 held multiple events). New 100 ms
snapshots with a slow 200 ms GUI poll showed only 11 interval events, although the
cumulative count still reached 23. The separate 50 ms poll saw all 23 distinct
active snapshots. This demonstrates coalescing in the model, not native display
cadence. Rendering/Tk scheduling can still delay snapshots/presentation.

1,000 actual helper snapshot+JSON calls: p50 0.083 ms, p95 0.160 ms, maximum
0.300 ms; largest packet 1,374 bytes (limit 16,384). Matching 8-second synthetic
PCM, 2048-frame packets, descriptors/star enabled and fresh state, three passes
with reversed order on the middle pass: whole analysis callback p50/p95 ms were
1.821/2.849 without tuning, 1.905/3.069 at exact baseline tuning, and 1.556/2.872
at a diagnostic trial. Background load was uncontrolled; these microbenchmarks
do not establish a speedup, device cadence, whole-loop cost or FPS guarantee.

## Existing Balloon weak regions

`weakspot-results.json` reuses the frozen decoded prefix through the 89.984-second
passage (source start 136.192 s). Both arms process the full prefix, then inspect
the requested local windows numerically; no builder listening or annotated drum
ground truth. Reviewed baseline positive packets / accepted events / envelope
maxima are: near 11 s **3/3/3**, near 17 s **0/0/0**, 24–32 **10/9/9**,
41–44 **10/10/10**, 50–53 **3/3/3**, 60–63 **7/7/6**. Thus the latter region
contains detected/accepted events that merge into fewer swells. The 17-second
region lacks a positive proxy packet; this cannot be called a missed kick without
listening/annotation.

The explicit CPU diagnostic (upper 1.5, extension 0.5, sensitivity 1.25) gives
3/3/3, 1/1/1, 19/19/19, 12/12/10, 6/6/6 and 10/9/9 respectively. It is neither
a shipped new default nor a recommended song profile. Increased positives can
include picked bass/other low-frequency events; some accepted responses still
merge under the preserved fixed release.

## Remaining boundary

Ready for Robert's current-song trial. Native Tk layout/repaint, actual LIVE
device propagation, GPU/whole-loop cost and normal-speed listening/visual response
of adjusted values were not tested in this task because the current call/preview
must not be disturbed. The optional safe-window question remains unanswered;
elapsed time grants no permission. No new window or real recorder was launched.
Independent critique remains HOLD; user acceptance is not claimed.
