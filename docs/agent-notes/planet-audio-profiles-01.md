# Planet Canvas Audio tuning: authored baseline, profiles and keyboard

The latest approved assignment supersedes the earlier exact-old-default lock.
The new star-target authored baseline is Start 80 Hz, End 130 Hz, weight 1.5,
sensitivity 2. The existing star pilot remains opt-in. This pass adds no mappings,
visual redesign, capture/queue changes, dependencies or Main integration.
Critic remains HOLD; Robert's native trial is the next review boundary.

## Implemented behavior

- `app/visuals/starfield_authored.json` holds the versioned `planet.starfield`
  authored settings. Both actual live/replay owners initialize this baseline
  whenever the star pilot is enabled, including without Studio input.
- Startup and live override OFF use the authored baseline. Back to authored
  clears temporary values. The old 20-250 Hz / weight 1 / sensitivity 1 baseline
  remains a separate comparison button, using its exact original arithmetic.
- Named custom profiles are stored separately in `work/audio-tuning-profiles`.
  Save uses ACK-applied values, not pending slider positions. Load applies a
  temporary override through the existing ACK route; neither promotes authored.
- The separate AUTHOR Studio action saves ACK-valid values as authored. It
  validates before writing, flushes/fsyncs a sibling temporary file, and replaces
  atomically. A failed write keeps the prior file and cached baseline and sends
  no runtime promotion. The running update then uses the existing ACK route;
  a subsequent coalesced edit carries the authored update forward.
- Schema validation rejects unknown fields, duplicate JSON fields, wrong target,
  kind/version, nonfinite/out-of-range values, reversed/empty windows and missing
  current actual bins. No loading-time clipping or partial apply. Startup checks
  the current owners' full-block 2048-sample / 48-kHz grid; each delivered analysis
  packet and displayed ACK use its own actual bins. Malformed startup files emit
  an explicit error and use the shipped baseline without rewriting the file.
- One Audio tuning window has one shared slider set. Selecting another target
  disables its controls and shows that its adapter is not implemented; it sends
  no update and displays no star curve as that target's curve.
- Reusable `SliderKeyboard` binds only sliders. Click gives focus with a visible
  `>` row marker; Left/Right tap changes 1 Hz or 0.01x. Hold starts after 300 ms,
  repeats every 80 ms and caps at four increments per repeat. OS repeated presses
  do not double-invoke. Release, focus loss, disable and close cancel the timer.
  Up/Down changes focus only, skips disabled sliders, wraps in stable order.
  Tab, mouse drag and text/combobox arrows retain their normal bindings.

## Availability inventory

24 audio-responsive groups are listed: **1 editable, 23 unavailable adapters**.
These are existing source groups, not proposed independent audio routes.

| Groups | Count | Existing input / availability |
| --- | ---: | --- |
| Planet background stars | 1 | Editable attack-window adapter; star pilot ON required |
| Living artifacts, Liquid Alloy, Prismatic Lattice, Echo Weave, Ink Archipelago, Interference Silk, Cellular Mosaic | 7 | Existing shared audio parameters/history; no tuning adapters |
| Tunnel, Fractal folds, Horizon/pathway | 3 | Existing shared scale/flux energy response and authored cycles; no tuning adapters |
| Elastic Lenses, Braided Flow, Nested Windows | 3 | Shared scale/flux drive; first two also have the existing optional descriptor amount mappings; no tuning adapters |
| Sparkles, Drifting flecks, Radial beams | 3 | Existing sparkle intensity / impact-flux-sparkle event gate; no tuning adapters |
| Prism Assembly, Digital Bloom, Chromatic Memory | 3 | Existing shared postprocess audio energy; no tuning adapters |
| Planet rings | 1 | Existing sparkle/shared color response; no tuning adapter |
| Moon dust wakes | 1 | One shared sparkle/flux strength group; no tuning adapter |
| Shooting stars | 1 | Existing sparkle/impact intensity, time-driven births; no tuning adapter |
| Planet surface color response | 1 | Existing scale/flux/sparkle response; no tuning adapter or new color behavior |

Moon-body orbit geometry is time-driven and excluded. There are no three
independent moon routes. Independent clocks, idle movement and palette pickers
are excluded. Audio envelope time constants are not excluded by that distinction;
their existing formulas remain unchanged.

## Technical evidence and limits

See `work/planet-audio-profiles-01/review-index.json`, its task diff, pre-task
snapshot, final source binding and CPU logs/results. HEAD alone does not bind
this dirty working tree. Earlier evidence indices/artifacts remain frozen.

Executed checks include profiles/default routing, filesystem roundtrip and
injected atomic failures; actual constructors/callbacks using inert widgets;
keyboard bindings/repeat cancellation; exact live owner with real local pipes
and worker threads but synthetic capture and mocked graphics; existing spectrum,
star-attack and monitor standalone CPU regressions; syntax and diff checks.

At N=2048 / 48 kHz the new window selects actual centers 93.75 and 117.1875 Hz,
not every displayed Hz position. Full measured spectrum stays visible with the
star pilot OFF and analysis remains unmodified. Authored tuning OFF is distinct
from star pilot OFF. Pure legacy detector/helper tests retain their original
baseline; actual star-pilot startup uses the newly authorized baseline.

Initial profile-test assertions failed because the test counted sample-clock
packets incorrectly, then used exact accumulated-float equality, then referenced
the wrong detector attribute. These test corrections are recorded; no detector
formula was changed to pass them. Intermediate failures were console-only and
were not a fully source-bound replay pack.

No new GPU render, real audio/device capture, natural listening, native keyboard
trial, FPS guarantee or artistic acceptance is claimed. A read-only process
command-line check returned access denied; no app was interrupted and no native
window was launched. User trial remains necessary. Existing fixture evidence is
synthetic proxy response, not instrument classification.

The six standalone DSP files, low-band detector, star flight, monitor, renderer
and scene shader remain unchanged from this pass's snapshot. Main session
storage functions are unchanged. No staging, commit, push, root-document edit,
release build, cleanup or other-world change was performed.

## Studio trial

1. Launch held Planet Canvas in existing Dev Studio with the star attack pilot
   enabled. Open View > Audio tuning. The star target starts with live override
   OFF at 80-130 Hz / 1.5x / 2x; verify the ACK curve and actual centers agree.
2. Click a slider; tap/hold Left/Right, release, switch focus and use Up/Down/Tab.
   Verify mouse drag still works and disabled sliders are skipped.
3. Save a named profile, change temporary values, load it and wait for ACK.
   Back to authored should restore the authored values. Compare with old 20-250.
4. In the separate AUTHOR Studio section, save acknowledged settings as authored.
   Wait for saved/ACK status, then use OFF/Back and relaunch to verify persistence.
   This explicitly changes the authored file; named-profile Save does not.
5. Select moon dust/material/spatial targets: inspect the existing-driver reason
   and disabled controls. Return to stars; the same slider set reflects its ACK.

Stop here for user trial; no critic dispatch or new adapter is authorized.
