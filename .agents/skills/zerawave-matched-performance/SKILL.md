---
name: zerawave-matched-performance
description: Design or assess a scoped ZeraWave slowdown or optimization comparison with matched source, inputs, pixels, caller and measurement protocol, separating GPU cost from presentation and harness timing. Use for performance evidence, not general visual critique or an unsolicited optimization campaign.
---

# ZeraWave matched performance

Read the current measurement assignment, [working agreement](../../../AGENTS.md),
affected [maintenance contracts](../../../docs/MAINTENANCE_CONTRACTS.md) and
[technique ownership](../../../TECHNIQUE_LIBRARY.md). Use existing project tools
and the project environment. This skill defines evidence requirements, not a
benchmark framework or optimization authority.

## Establish a meaningful comparison

1. State the slowdown question, affected caller/boundary and bounded measurement
   protocol before running anything. Bind baseline and candidate source hashes,
   exact task diff, tool/harness version, audio file or packet hashes, analysis
   prefix/state, passage, seed, clocks, layers, colors, quality and render scale.
   Preserve baseline evidence and failed trials. A dirty checkout needs source
   bindings beyond HEAD. Reuse unchanged valid evidence with provenance.
2. Record actual window client size, framebuffer dimensions, internal render-target
   dimensions, viewport and shader resolution where available, plus display mode,
   monitor and refresh rate. Match effective pixel workload and presentation
   conditions, not requested dimensions alone. Separate default window and native
   fullscreen results; identify borderless/clamped windows or fullscreen surrogates
   truthfully. An unknown user fullscreen action prevents an exact reproduction
   claim, not a clearly labeled bounded surrogate measurement.
3. Keep caller, decoded analysis prefix, inputs, settings and route comparable;
   label forced selection separately from ordinary director behavior. If resolution,
   detail, duration or pacing changes, report a different workload rather than an
   equivalent speedup. Choose representative held and affected boundary cases
   proportional to the question, including return/lifecycle cases when implicated.
4. Separate cold startup/compile, warm lifecycle, GPU draw, CPU submit, whole caller
   loop, swap/poll/presentation intervals, capture/readback and harness pacing.
   Define exactly what each timer includes. Report query waits, finish/synchronization,
   forced deadlines, capture and instrumentation overhead; use existing tools to
   check suspected measurement effects without silently changing the protocol.
   Swap return is not measured scanout; shader timing alone is not display FPS.
5. Report each arm's sample count, duration, median and relevant tails, maximum,
   stalls and affected boundary times, with the chosen stall threshold. Account
   for unequal counts or song-time sampling. State device, background load and
   thermal/power control or uncertainty. Label repeats and conditions; do not
   average away failures or infer a general FPS/device guarantee. Couple claimed
   gains to applicable preservation and visual evidence, not timing alone.

## Boundary and coverage lessons

- Compare source and wall clocks at equivalent event boundaries. Source sampled
  before render versus wall time after swap includes endpoint latency changes;
  inspect render-begin spans before calling this source-clock drift. Retain failed
  literal thresholds separately rather than silently redefining them.
- Keep ordinary real-time playback separate from fixed-clock/unpaced diagnostics
  and query-instrumented arms. Include preparation, history steps and composition
  in whole-pipeline GPU cost, with individual pass costs alongside it.
- Separate sustained endpoint/overlap drawing from exceptional waits. Absolute
  stall thresholds can count consistently expensive frames; call-boundary waits
  may shift under instrumentation and do not identify their underlying owner.
- Preserve individual runs, outliers, failures and interrupted checks. Mark other
  scenes/transitions unmeasured; sampled parity or a fresh corroborating pair does
  not establish all-world coverage or population tail non-regression.

## Finish

Return the matched conditions, results, attribution supported by measurements,
failed hypotheses and remaining limits. Distinguish observed correlation from a
demonstrated cause. Stop after the assigned measurement or authorized optimization
pass; propose only the next specific discriminating check if uncertainty remains.
No new dependencies, framework, global settings, unrelated process termination,
preview takeover or continuing optimization loop is authorized by this skill.
Use [Studio instructions](../../../DEVELOPMENT_STUDIO.md) for assigned review
and keep priorities in [ROADMAP](../../../ROADMAP.md).
