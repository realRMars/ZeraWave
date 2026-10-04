# Planet Canvas audio tuning coverage — CPU checkpoint

The approved continuation completes all 24 existing Audio tuning target entries.
This is a bounded parameter-exposure pass on the actual held Planet Canvas
(`canvas`, renderer state 5 / existing `cosmic` layers), not Galaxy or a new
world. It adds 22 adapters and six Starfield presentation gains to the prior
Starfield/Living Artifacts work. No independent critic was dispatched.

The authoritative prior checkpoint is
`work/planet-artifacts-listening-01/review-index.json`, SHA-256
`66393a84d49ccf14fb5bef29667ec73a9c1295c3f222c5641c6ce5678e2c4bad`.
HEAD remains `0342e518a7bd2c521416e8027a7920668fc5ee51`. The new pack is
`work/planet-audio-coverage-01/review-index.json`; it binds the pre-task snapshot,
exact task diff, final source copies/hashes, inventory, commands/results, native
layout evidence, failures and preservation checks. HEAD alone does not identify
this dirty checkout.

## Result and routing

- Seven materials: Living Artifacts retains six gains and its optional measured
  flux/sparkle ranges. The six siblings expose the terms actually used: shape,
  deformation, glint/seam light, ink advection and ink injection. Echo uses raw
  impact for injection; its unused sparkle input has no slider. Interference
  Silk's unused flux argument has no slider.
- Six spatial targets: Tunnel/Fractal/Horizon keep their original authored,
  Selected/Cycle and Meld formulas. Presence controls are disabled in
  Selected/Cycle. Fractal's authored-only bass fold is disabled elsewhere.
  The three newer treatments expose separate bass/flux displacement drive.
- Three FX targets: Sparkles light; Flecks presence/light/cell scale/event size/
  elongation/drift amplitude; Beams' existing impact/flux/sparkle event gate.
  Timed births and quiet floors remain.
- Three Envelopers: Prism's audio motion/edge treatment, separate Digital amount
  and block size, separate Chromatic retention and displacement. They affect
  the final composition/history only while that Enveloper leads. Edits retain
  history, clocks and static strength; no extra render pass or texture is added.
- Sky/surface: Starfield keeps Start/End/Weight/Sensitivity at authored
  80–130 Hz / 1.5 / 2, plus separate chorus light/presence/twinkle/legacy wake
  and shared sky-clock inputs. Legacy wake is inactive with attack-flight ON;
  frequency controls are inactive with that pilot OFF. Presentation edits can
  receive render ACKs with the detector OFF. Rings expose reflection; dust
  controls all moon wakes together; shooting-star light retains event births.
  Surface response separates planet-and-ring chroma/light and three existing
  audio contributions to the integrated shared Planet material/spatial clock.

The 22 new adapters expose 60 named contributions, each with original-strength
default 1 and bounds 0–2. Gain edits retain the existing normalized ceiling,
static contribution and applicable envelope. Gain 0 does not remove inherited
shared-domain deformation or an entire element. Shared Planet clock gains retain
the original speed floor, ceiling and easing; they change integrated speed, not
accumulated phase. The inventory records each actual ID/name, role, source,
scope, modes, defaults/bounds, source location, implemented/tested status and gap.

New gains start neutral with live override OFF. OFF/Back to authored restores
the saved target baseline; an explicitly saved nonneutral authored baseline is
deliberately effective while OFF. Outside held Planet Canvas every new gain
resolves neutral. Custom profile Save/Load and live edits do not promote authored
values. Explicit author save is atomic and target-scoped. Missing new target
files use neutral defaults without auto-writing 22 files. Older Starfield v1
files migrate six neutral gains in memory without rewriting their bytes;
Living Artifacts' prior migration/range contract remains.
Representable legacy band curves upgrade to the same single window when a
presentation gain is edited. Unrepresentable legacy curves retain their values
and disable the incompatible frequency/presentation controls; sensitivity and
Back to authored remain available. The final CPU pass covers both cases.

The reusable adapter is `app/visuals/planet_audio_tuning.py`, used by the existing
renderer, single inspector, profile store and Studio pipe. Pending state is at
most one message per known target (22), not an unbounded event queue. The main
shader receives 45 vec4 rows, including Starfield's four GPU presentation slots;
the two sky-clock gains stay on the CPU. Echo and
Envelopers receive their own small gain vectors. Telemetry remains latest-only
and rate-limited through the existing stream. The packet cap is 49,152 bytes,
below the existing 65,536-byte reader limit. Measured synthetic owner packets
were at most 34,556 bytes. Capture, FFT, normalization, the original three-band
max impact route and audio queues are unchanged in this batch.

## Checks actually run

Ten integrated checks passed: coverage/actual synthetic owner, artifacts
listening, artifacts tuning, Star profiles, spectrum tuning, Planet star attack,
mapping monitor, Planet DSP, parameter mapper and hidden native coverage/layout.
Twenty-five Python files parsed; `git diff --check` passed. Tested source hashes
remained unchanged throughout the final integrated run.

The coverage test checks all 24 IDs; all 60 new role bounds and target slots;
same-name profile isolation, wrong-target rejection, author/reset/relaunch;
22-target bounded coalescing; actual Echo/Enveloper methods with inert resources;
432 exact neutral-clock comparisons against the pre-task renderer; and 22 new
target ACKs through the real Studio pipes/threads and actual owner functions with
synthetic mocked capture/graphics. Each owner run starts/stops one mocked capture.
Two pilot-OFF Starfield presentation ACKs were also checked against uniform rows.
These are CPU/mocked/synthetic results, not GPU or real-device evidence.

Native Tk used an invisible, allocated 900×860 client harness while its owning
WM window stayed withdrawn. All 80 slider rows across the 24 entries were
reachable using the actual native geometry and scroll helper. Native virtual
dispatch verified the original four Starfield controls: Start/End +1 Hz and
Weight/Sensitivity +0.01. Focus scrolls the selected slider into view. This is
actual hidden native layout/dispatch evidence; it does not establish visible
WM/DPI behavior, hardware key delivery or user acceptance of the layout.

Retained failures include the initially unallocated withdrawn viewport, the
pilot-OFF ACK revision bug (fixed), and the first integrated historical
preservation assertion, updated to undo the now-authorized neutral gain delta
before comparing the older attack-flight baseline. No test was removed. The
shader replacement manifest reconstructs the complete pre-task shader exactly.
The final regression logs and earlier trials remain separate in the pack.

Thirty protected file hashes match, including the six standalone DSP files,
unrelated dirty documents and earlier frozen evidence indexes/notes. No user
process was stopped; no real capture/device/microphone, GPU renderer or foreground
window was opened. No root document, Main integration, player/capture queue,
dependency, portable build, staging, commit, pull or push operation was performed.

## Remaining gaps and review route

Flecks' `elapsed_time * (0.6 + 1.2*sparkle)` phase remains untuned: multiplying a
gain into elapsed phase can jump its position. The smallest safe option would
be an explicit decision about a local integrated clock, with neutral/default
continuity and history evidence. Pure timer/idle controls and nonexistent
independent moon routes are intentionally excluded. Per-target controls do not
independently remove inherited shared bass/event carrier warps; those stay shared
and are identified in the inventory rather than duplicated into each adapter.

GPU compilation/pixels/cost, visible WM/DPI/hardware interaction, decoded
normal-speed motion, controlled/natural listening and multi-hour continuity
remain pending. CPU timing in `resource-results.json` is an adapter/report
microbenchmark, not shader time, whole-loop cost or an FPS guarantee. No art
score or user acceptance is claimed.

Review through Bob/Prompter using the bound pack; do not dispatch a critic or
begin another phase automatically. After coordinated GPU testing is approved,
use the existing Studio (`run_development_studio.bat`), hold Planet Canvas and
open Audio tuning. Use a fresh preview for the changed shader; leave an existing
user preview alone. Check all four Starfield controls first, then select each
target and its existing layer/material mode. Compare neutral with one deliberate
gain edit, Back to authored, named profile and explicit author-save/relaunch.
Check mode-inactive labels and Enveloper scope.

The matched A/B plan fixes source hashes, one identical decoded input/analysis
prefix, seed, elapsed/sample clocks, layer/palette/manual values, window and
framebuffer dimensions, quality and optional pilot flags. Include quiet,
sustained intense, event/release and change passages; a matched-level texture
contrast; authored holds/Meld handovers; Selected/Cycle Tunnel; entry/return and
gain reset without history jumps. Capture normal-speed sequences and measure
GPU draw separately from whole-loop/capture and startup cost on the RTX 3070
Laptop GPU. Keep listening, visual quality and performance conclusions separate.
