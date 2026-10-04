# Cosmic and Elemental maintenance contracts

This reference protects existing working behavior when maintaining or extending
shared code. It does not freeze all future art to current geometry or algorithms.
An assigned scene redesign can change that scene; preserve unaffected scenes,
saved data and shared systems. Current creative scope lives in
[ROADMAP.md](../ROADMAP.md) and [AGENTS.md](../AGENTS.md).

## Planet Canvas and its existing Cosmic diagnostics

These contracts describe Planet Canvas and the existing Transition/diagnostic
callers of `isolated_cosmic_scene`. They do not prescribe Galaxy or future
Cosmic forms.

- The material field becomes planetary albedo; `isolated_cosmic_scene` owns
  planet/ring/moon depth. Compare actual depth, not screen position; keep
  projection, shared ring axes and system scale coherent when maintaining it.
- Moons replace covered scenery with opaque, normal/light-shaded material.
  Eclipse/night treatment belongs in lighting, not alpha. The opacity regression
  samples moon centers and far-side occlusion, not every limb or moon overlap.
- The existing surface uses bounded procedural disturbance. New scenes and
  assigned effects can use particles, geometry, feedback or other representations
  inside the working renderer. A scene brief can authorize these choices.
- Preserve existing sky/material defaults during unrelated work or color-only
  extensions. An assigned artistic change may deliberately redesign its target.
  For depth/projection changes, compare matching state/time/dimensions/input,
  then inspect motion as well as captures.

Relevant checks, when the changed paths warrant them, use a fresh destination:

```powershell
$review = "work/review/cosmic-$(Get-Date -Format yyyyMMdd-HHmmss)"
.\.venv\Scripts\python.exe app\visuals\moon_opacity_test.py
.\.venv\Scripts\python.exe app\visuals\shader_test.py --handoff-test "$review\handoff"
.\.venv\Scripts\python.exe app\visuals\shader_test.py --sweep "$review\sweep"
.\.venv\Scripts\python.exe app\visuals\shader_test.py --capture "$review\capture" --state canvas --seconds 18 --profile active
```

Historical evidence remains at `work/cosmic-handoff/sequence`,
`work/cosmic-handoff/sweep` and `work/cosmic-handoff/capture`; do not overwrite it.
The handoff and sweep tests cover particular timing/contrast/black-space
regressions, not every Cosmic scene or subjective motion quality.

## Existing Elemental forms

- Preserve structural depth and authored presentation in unaffected forms.
  Color-only controls should retain the target's shading and silhouettes.
  An assigned spatial effect or transformation may deliberately deform its
  target; define compatibility and inspect the resulting structure in motion.
- Water currently uses procedural surfaces. Fire/Aftershock have bounded
  lifecycles. These are implementation descriptions, not bans on developing
  richer simulation or other techniques for an assigned scene.
- Keep resource/state bounds and reproducible test inputs where applicable.
  Maintain the intended opaque/translucent behavior of unrelated surfaces.
- Preserve stable layer IDs and saved sessions. Check shared changes in their
  affected held forms and applicable Main transitions. A new held-only candidate
  can be reviewed without adding it to Main prematurely.

## Shared verification and audio boundaries

- Detect onsets from the intended normalized/smoothed bands before
  `VisualSignalConditioner` applies visual slew limiting, then carry onset values
  through `AudioFrame.impact`. Sustained level is not a fresh onset.
- Baseline checks protect explicitly sampled, unaffected behavior. Preserve the
  baseline and evidence path. Intended changes to a redesigned candidate require
  visual evaluation rather than equality with its former image.
- `app/visuals/shader_test.py --preservation-test <baseline>` compares sampled
  held-world pixels. World-specific modes with `before.frag` retain their own
  evidence scope. Neither proves natural live audio, artistic quality or general
  device compatibility.
- Run focused checks for the affected paths; broaden when shared changes create
  regression risk. Do not run every historical command after every small edit.

See the [Cosmic snapshot](history/2026-09-28-cosmic-development.md),
[Elemental snapshot](history/2026-09-28-elemental-development.md) and
[history index](history/README.md) for dated acceptance and evidence.

## Galaxy Odyssey: held and canonical Main

- Accepted Galaxy36 belongs to `LIVE_FORMS` and canonical Main. Preserve its
  74-second route on Main entry/return and route-boundary release. Earlier forced
  `world_uniforms({36: weight, ...})` fixtures are historical compatibility
  evidence, not an exclusion policy. Zero Galaxy weight must preserve unaffected
  scene contributions.
- Galaxy's visit clock progresses during visibility, parks elsewhere and resets
  on rewind. The musical star clock drives local orbital/material motion.
- `procedural_cosmos` uses versioned hierarchical identities and at most twelve
  cached immutable descriptors. Warp's next descriptor must equal arrival's
  current descriptor. Pure tests cover route joins and camera/solid separation.
- Local solar coordinates use the selected star's galaxy anchor and fixed scale;
  CPU/shader planet-position formulas must agree. Keep opaque body/ring depth,
  continuous camera exclusion and bounded shader loops.
- `stellar_sails`/`stellar.sails` are retained storage IDs for Ion Comets. Both
  comet and parallax layers keep explicit opt-in and amounts in compatible worlds.
  Galaxy Authored includes them; all three Envelopers stay off in Main.
- Source pigment roles are stable and append-only. Missing old-session roles
  fall back; defaults never overwrite manual entries, holds or stored cycles.
  New local materials/regions use generated inspector and live transport.
- Eight nursery events maximum, ten-second lifetime and 1.2-second trigger gate;
  rewind/leaving Galaxy clears them. Pigment edits do not clear history. No
  musical phrase/downbeat recognition or literal infinite universe is implied.
- Inspect short visits, scale bridges, planetary transfers and destination
  arrivals in motion. A previous quiet-camera pixel-speed ceiling does not define
  the new route; test continuous joins and bounded frame-change spikes instead.
- Main integration evidence: [Main lineup](../work/main-lineup-01/review-index.json)
  and [current handoff](../ZERAWAVE_HANDOFF.md). Earlier held evidence remains at
  `work/galaxy-journey-review/` and in [task notes](agent-notes/galaxy-stellar-aviary.md).
  Technical checks and the recorded user acceptance retain their own scope.

## Main Audio Tuning preservation

- Preserve authored values on load, preview, target switches and temporary profile
  changes. Only an explicit Save Authored promotes the acknowledged values to the
  named destination. Keep the backed-up Planet stores and separate DSP work intact.
- Keep form/target/role settings independent. Shared-technique instances retain
  their form owner; selected listening windows reuse existing FFT data and do not
  retune global normalization, pigments or unrelated clocks.
- Route commands, telemetry and saves by run/session/form/target/revision.
  Reject stale identities/revisions. A save requires a fresh matching ACK and
  settings digest; active listening ranges also require valid current input.
  Configuration ACKs for inactive targets do not imply visible contribution.
- Switching form/target or Follow/Pin cancels held keys, drag/debounce work and
  pending paint. Park unsent values at their original owner; an older ACK must
  not overwrite them or make them saveable before their own acknowledgement.
- Preserve outgoing/incoming endpoint ownership and distinguish director timing
  from visual transition inputs. Pair auditions require compatible Main forms
  and a repeatable source; reject matched live input before mutating playback.
  Repeat resets the same decoded passage and numerical FFT history; Return
  restores the parked source/CPU scene/RNG state. Shared Echo/Enveloper GPU
  history resets at the boundary rather than claiming pixel-identical recovery.
- Keep inactive/mode-inactive telemetry unavailable, and label CPU submissions,
  analyzer spectrum, proxies and selection weights separately from GPU pixels.
  Do not infer slider-by-slider visual coverage from the 595 target-row inventory.

See [Studio operation](../DEVELOPMENT_STUDIO.md#main-audio-tuning-and-mapping-monitor)
and [the rollout handoff](../ZERAWAVE_HANDOFF.md#current-main-audio-tuning-checkpoint)
for source identity, bounded evidence and remaining limits.
