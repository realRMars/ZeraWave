# ZeraWave development plan

Updated: 2026-09-28. This is the sole prioritized development plan and backlog.
The user sets direction; the Overseer maintains this plan. A listed idea is not
automatic authorization to implement it. Current code establishes what exists;
user review establishes accepted appearance.

## Direction and working method

Priority: greater visual variety and completion of worthwhile existing ideas.
Dev Studio already works well for the user's workflow. Add only the controls
needed to inspect a requested feature; do not start a general Studio redesign.

Normal feature workflow:
1. Inspect existing techniques and reuse the renderer, audio and preview paths.
2. Build a bounded feature and expose it in Dev Studio for easy user testing.
3. Run relevant checks and give exact Studio review steps.
4. Refine from the user's motion/listening review.
5. Integrate into Main Blend when approved or already explicitly authorized.
6. Update current instructions and report evidence, limitations and remaining work.

Scripts and captures supplement Studio; they do not replace its review workflow.
Routine implementation steps within an assigned task do not need repeated approval.
Pause at actual artistic decisions, significant scope/architecture changes, or
the task's specified review gate. Preserve explicit commit/deletion requirements.

## Current work and sequencing

| Work | Owner | Status / next gate |
| --- | --- | --- |
| Documentation consolidation | File Worker; Overseer | Reviewed complete; no commit reported. |
| Bounded obsolete-file cleanup | File Worker | Reported complete, including archived root helpers and player test; no commit reported. |
| Studio organization and Planet A/B | Builder | Implemented; user described the workflow as mostly fine. Soft Dream appearance is not recorded as accepted. |
| Live Roots color inspector | Builder | User likes the workflow and authorized a checkpoint commit. Broader rollout remains unassigned. |
| Shared plan | Overseer | Live color authoring is now the immediate priority below. |
| Broader editable-color rollout | Not dispatched | Intended project-wide direction; begin reviewed batches after Roots workflow acceptance. |

These statuses distinguish worker reports from user acceptance. The Overseer read
the Roots validation note and extension guidance but has not rerun application
checks. No commit, Main-default change or portable build is authorized by this plan.

## Immediate milestone: hands-on live color authoring

This user-selected direction takes priority over expanding the fixed Soft Dream
palette. Preserve the completed palette/A-B controls; build on the existing Studio.

### Gate 1: user review of held Roots

Implemented scope reported by Builder: two field shading gradients, ridge tint,
and shared blossom tint. User can edit live, reset a target/scene, revert to
preview-start colors, and save/load named color presets and sessions.

Review whether:
- Target and role names make artistic sense without reading shader code.
- Wheel/hex/brightness and gradient edits are visibly useful while motion continues.
- Intended regions change without unintended recoloring, clock resets or lost detail.
- Reset, revert, save and reload make experimentation comfortable and predictable.
- Synthetic, decoded and live review retain their documented differences.

Blossoms retain their lifecycle; tint changes do not force blooms. Gradient
positions are shading-value intervals, not positions along a branch. Material
recoloring and independent root-tip/glow controls are not implemented. User
acceptance and continuous audiovisual review remain pending.

Evidence and implementation limits:
[Roots task note](docs/agent-notes/roots-live-colors.md).
Technical extension contract:
[Technique library](TECHNIQUE_LIBRARY.md#declared-live-color-controls--extension-pattern).

### Gate 2: applicable existing visuals

After Gate 1 acceptance, inventory meaningful color targets across existing worlds,
materials, effects and details. Expand in bounded reviewed batches. Membrane and
Planet are candidate next batches, not automatically assigned work. Separate
surface pigment, object tint, gradients and feedback-stored color where needed.

Reuse the declarations, generated inspector and live transport. Preserve authored
defaults and old sessions. Unsupported values fall back safely; do not hide scene
parts because a color is absent. Do not expose every shader expression as a knob.

For each batch, record supported targets, limitations, tests, exact Studio review
steps and user acceptance. Main integration remains a separate explicit behavior:
saved held-world edits must not silently replace Main's defaults.

### Future features

The user wants meaningful editable color support considered for every new visual.
Builders should plan applicable targets using the documented mechanism and explain
exceptions. Finalize the standing AGENTS.md extension policy after the first
hands-on review proves the workflow; avoid proliferating an unreviewed interaction.

## Retained palette milestone: independent palette selection

The gates below remain useful for the existing Soft Dream experiment, but are
subordinate to the current live-editing review rather than the next automatic task.



Preserve Authored. Soft Dream is an experimental contrast, not an accepted look.
The initial prototype targets Planet Canvas; the user must be able to review it
through Studio with individual materials and the existing material meld.

### Gate A: Planet Canvas review

- Authored versus Soft Dream is independent of material selection.
- Studio routes the choice through its existing synthetic, track and live paths.
- Existing sessions preserve their behavior; the new choice saves/reloads safely.
- All four materials retain distinct identities, depth, shadows and highlights.
- User can compare quiet, active and release passages in motion.
- Record measured rendering cost, resolution, test scope and unresolved failures.
- Builder reports exact Studio steps; user accepts or requests changes.

The reported prototype checks are worker evidence, not Overseer reruns or user
acceptance. Main defaults remain unchanged at this gate.

### Gate B: accepted cross-world integration

After Gate A acceptance and an assigned integration task, verify Sea and Cavern
as well as Planet Canvas. Preserve geometry, readable shadows/highlights, Sea
reflections, material identities and audio response. Define compatibility and
fallbacks explicitly rather than promising identical treatment on every surface.

### Gate C: Main Blend

After the appropriate review/authorization, define and implement Main's palette
behavior explicitly. Preserve old sessions and Authored. Review transitions and
quiet-to-strong-to-quiet motion in Main, record cost, and obtain user acceptance.
Completing the isolated prototype alone does not complete this milestone.

## Milestone 2: lingering growth and maturity — investigation first

Existing user intent: worlds should linger, mature and transform. Inspect current
director holds and existing lifecycles, then review whether they achieve that
experience. A slowly flowering Roots scene is a suggested bounded experiment,
not a selected requirement.

Before implementation, choose one visible lifecycle with the user: emergence,
growth, dwell, decay or transformation. Define its musical response, continuity,
quiet behavior and Studio review method. Avoid globally extending every world
or rewriting the director without evidence. Completion of this investigation
means an agreed experiment and observable acceptance criteria, not a new world.

## Later separately reviewed experiments

1. One independent surface treatment, such as pearlescence or ink: select a look
   and supported surfaces, preserve palette/material separation, review in Studio.
2. Richer persistent feedback: reuse Echo's resources where suitable; establish
   bounded growth/release, reset behavior, cost and world compatibility first.
3. Reusable style combinations only once the underlying choices prove useful.

These are proposals, not parallel work orders or promises of fluid simulation.

## Preserved creative ideas — unscheduled

| Idea | What remains to decide or build |
| --- | --- |
| Cosmic scale journeys | Beyond existing planet/rings/moons toward systems and galaxies. |
| Ambiguous transformations | Recognizable identity evolving between forms, beyond scene blending. |
| Peaceful tree/forest growth | Distinct from the existing Firescape growth/burn lifecycle. |
| Occasional faces and creatures | Review current eye-like forms first; examples are not a mandatory asset list. |
| Quiet states | Review short silence, sustained quiet and dormancy with non-percussive music. |
| Bonk / Dance controls | Direct user ideas explicitly deferred until later. |
| Sea sky as material canvas | Optional design decision; current reflected meteors do not implement it. |

Daddy Long Legs remains a shelved opt-in experiment, not an unfinished requirement.
Original PDFs and dated history preserve provenance; do not recopy their obsolete
backlogs into current assignments.

## Supporting work and deferred product work

Fix regressions and performance obstacles when they affect the requested visual
experience. A focused investigation of live draw/audio cadence is a candidate,
not a measured FPS finding or authorization for a pipeline redesign.
Console Unicode printing and the moon-test shader lookup were reported by Builder;
confirm current status before assigning fixes.

Keep historical evidence, private test audio, environments and frozen releases.
Cleanup is limited to the user's exact approved scope, not this entire backlog.

Paid ZeraWave Studio 1 is a future possibility. Commercial controls, licensing and
general Studio polish are outside this milestone. Another portable is lowest
priority; preserve the frozen d4992d0 checkpoint and reconsider a new named build
only at a fitting milestone. Broader device/release qualification remains deferred.

## Documentation ownership

See [AGENTS.md](AGENTS.md#16-coordination-and-document-ownership) for ownership,
worker autonomy and optional notes. Current checkpoint:
[ZERAWAVE_HANDOFF.md](ZERAWAVE_HANDOFF.md). Historical source:
[docs/history/README.md](docs/history/README.md).
