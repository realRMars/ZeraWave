# Historical snapshot: ROADMAP.md before the creative-policy audit

Captured 2026-09-30. Superseded; use the [current roadmap](../../ROADMAP.md).
The original document follows unchanged in content. Relative paths and links
inside it were written for its original repository-root location.

---

# ZeraWave development plan

Updated: 2026-09-30. This is the sole prioritized development plan and backlog.
The user sets direction; the Overseer maintains this plan. A listed idea is not
automatic authorization to implement it. Current code establishes what exists;
user review establishes accepted appearance.

## Direction and working method

Priority: greater visual variety and completion of worthwhile existing ideas.
Dev Studio already works well for the user's workflow. Add only the controls
needed to inspect a requested feature; do not start a general Studio redesign.

Artistic decision (2026-09-30): Prism Assembly, Digital Bloom, and Chromatic
Memory are off in Main's authored live show pending visual redesign. Keep their
Dev Studio review presets and explicit opt-in controls so they can be improved
later. The seven materials and three paced spatial treatments remain in Main.

Current creative focus (2026-09-30): expand the Cosmic category with distinct
world scenes, as Elements has separate forms. Build one viewer-reviewable scene
at a time. First: a standalone galaxy scene, selectable beside Planet Canvas
in Dev Studio, with its own visual identity rather than an overlay on the
planet. Builder reports it implemented and regression-checked; user/viewer
review found it a good start but too digitized and visually sparse. Refine its
detail, style, musical color/motion response and sustained interest before
another Cosmic scene. Keep it out of Main until accepted.
Multiple suns, wider system journeys and a pulsar remain candidate later
scenes, not parallel work.

A new world scene means a complete experience that remains pleasing during an
extended hold, not just one new image or a layer over an existing form. Its
assignment may include original assets, scene-specific materials, spatial
treatments, new effect classes, and palette families when they serve that scene.
Useful colors/palettes should be editable and reusable in other compatible
worlds; do not assume a scene's full treatment works everywhere. Preserve
recognizable structure, fine detail, smooth edges/gradients, musical change,
quiet breathing room and measured GPU cost. Do not confuse a higher render
resolution with better art direction or add expensive detail without visible
benefit. Build and review one scene at a time, then decide what enters Main.

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

## Current checkpoint and active assignment

Checkpoint: dddc618, committed after the user liked the Roots inspector and
authorized saving the completed work. Documentation refresh, bounded cleanup,
Studio organization/Planet A-B and live Roots color editing are checkpointed.
The Overseer reran the complete Studio suite successfully before that commit.
Untracked research and original plans were intentionally excluded.

The user now requests a model-independent takeover plan to finish editable-color
coverage across all applicable existing visuals and support future creations.
On receiving the takeover assignment, the builder should execute the complete
rollout below, not stop permanently after Membrane or merely return another plan.
No particular model or reasoning setting is required.

## Active milestone: complete applicable live color-inspector coverage

Local implementation status (2026-09-28): batches 0–10 are implemented and
automated checks pass. The coverage ledger and evidence are in
`docs/agent-notes/color-inspector-rollout.md`. User motion/listening review and
artistic acceptance remain open; no standalone-player color deployment is implied.

### Outcome and authorization boundaries

Extend the established Studio inspector so users can edit meaningful colors of
existing worlds, materials, FX and details live, reset/revert them and save/reload
them without code changes. Keep authored appearance as the default everywhere.

The takeover assignment authorizes sequential implementation batches, routine
fixes, relevant tests and documentation within this milestone. After each batch,
review its diff and evidence and continue when checks pass. Do not demand approval
after every target or wait merely because the Overseer is unavailable. Present
usable review steps along the way; incorporate user feedback if it arrives.
Automated success is not user artistic acceptance.

Ask only for a genuinely unresolved artistic requirement, a significant
architecture/dependency change, destructive work outside scope, or a defect that
cannot be resolved while preserving the contracts. If one target is blocked,
record why and continue independent targets. No commits, pushes, new dependencies,
portable builds or unrelated cleanup are authorized by this future assignment.

### Read first and resume safely

Read AGENTS.md, this section, ZERAWAVE_HANDOFF.md, DEVELOPMENT_STUDIO.md and the
declared-controls extension pattern in TECHNIQUE_LIBRARY.md. Read
docs/agent-notes/roots-live-colors.md for implementation/evidence limits.
Inspect Git status and existing changes before modifying anything.

Reuse:
- app/visuals/color_controls.py: targets, defaults, validation, uniforms, presets.
- app/visuals/color_inspector.py: generated editing UI.
- app/visuals/studio_color_link.py: bounded live pipe transport.
- app/visuals/studio.py: selections, profiles, preview lifecycle and sessions.
- app/visuals/renderer.py and shaders/dream.frag: actual rendering ownership.
- preview_layers.py, technique_library.py and existing standalone test harnesses.

Do not restore retired root helper scripts or create another renderer, audio
pipeline, effect catalog, generic visual editor framework or parallel inspector.

### Batch 0: inventory and coverage ledger

Create and maintain docs/agent-notes/color-inspector-rollout.md as the single
execution ledger. It is working evidence, not a competing roadmap.

Enumerate current WORLD_TREE leaves, authored cycles, MATERIALS, all EFFECTS,
explicit-uniform details, opt-in experiments and CLI diagnostics. Reconcile with
actual shader callers; a catalog row is not proof of an independent color source.

For every relevant item record:
- Stable source ID and implementation symbol.
- Meaningful target/roles and actual color type (tint, gradient, collection, etc.).
- Compatibility and scope: form, family, shared material, detail, diagnostic.
- Status: not inspected, planned, implemented/tested, not applicable with reason,
  or blocked with concrete reason.
- Existing authored source, verification/evidence, limitations and user-review status.

A spatial-only transformation may correctly inherit its material's colors and
need no invented tint. An inconvenient hard-coded color is not automatically
inapplicable. Count catalog coverage, not just how many controls were added.
Avoid marking an entire world complete when significant colored details remain.

### Batch 1: Organic and reusable scope plumbing

Keep Roots behavior and stored IDs intact. Extend to Membrane's actual gradients
and highlights with deliberate identity/sharing semantics. Verify Organic's native
cycle can select appropriate targets without leaking overrides between forms.

Generalize the current held-Roots-only gates using existing scene/state identity.
Change declarations, transport validation, renderer/shader gates, session handling
and UI compatibility together. Do not merely enable the inspector button.

Review fixed five-color staged gradients as the existing semantic type. Introduce
another control type only for a real target whose existing behavior requires it.

### Batch 2: Geometric and Cosmic

Cover Neon Corridor and its applicable glyph/details, Planet surface, rings,
moons, dust wakes, starfield and shooting stars where independently meaningful.
Keep geometry, depth, shadows, occlusion and reflected radiance intact.

Separate object tint from shared material pigment. Define precedence between the
existing Soft Dream Planet option and explicit color overrides; show it clearly
and preserve old sessions. Do not silently recolor other callers of a shared helper.
Include Transition/CLI geometry diagnostics in the ledger; inspect applicability
without restoring removed navigation merely to inflate coverage.

### Batch 3: shared materials and FX

Cover Living Artifacts, Liquid Alloy, Prismatic Lattice and Echo Weave.
Inspect multiple hues/morphs, not just an overall tint. Expose useful fixed roles,
gradients or bounded collections according to the actual implementation.

Cover Sparkles, Drifting flecks, Radial beams and remaining shared color-bearing
FX. Record colorless spatial effects as inherited/not applicable when justified.

For Echo, favor existing display-stage color interpretation where correct.
Do not reset/reseed history merely to edit display colors. If a color actually
belongs to persistent simulation state, distinguish that requirement explicitly.
Do not fake recoloring by applying a uniform screen-wide filter.

### Batches 4–9: Elemental coverage, one family at a time

4. Water: Sea, Liquid dyes, Rain & ripples, Waterfall, Currents; rain, ripples,
   foam/cliff lip, mist, glints and shared sky/reflection targets.
5. Fire: Flame sheets, Molten flow, Firescape, Aftershock; coals, embers, seams,
   ash, flash, dust, ground fire and aurora. Preserve event and growth lifecycles.
6. Air: Windstreams, Stormfront, Vortex, Sky Citadel; clouds/ribbons, balloons,
   lightning/arcs, castle/earth/celebration and applicable optional experiments.
   Daddy Long Legs remains opt-in and shelved, even if given supported colors.
7. Earth: Dune Sea, Folded Strata, Crystal Cavern; sediment, veins, mineral glints,
   worm and meaningful terrain/crystal roles. Preserve conservative geometry.
8. Fog/Gas: Nebula Banks, Ghostlight Marsh, Pressure Chamber; vapor, ghostlights,
   internal lights, pressure fronts and visible solid details.
9. Plasma: Magnetic Bloom, Arc Constellation, Auroral Veil; field, arcs, sparks,
   cores and sky details.

These lists guide inspection; current source/catalogs define the full inventory.
Do not invent controls for nonexistent separations or omit newly discovered
applicable details. Reorder independent batches when code dependencies justify it,
recording the reason. Do not rewrite families or increase scene complexity.

### Batch 10: cycles, Main preview and user-selected assignments

Coverage must work during supported authored family cycles and Studio Main Blend,
not only held forms. Keep live overrides associated with stable targets as scenes
appear/disappear. Do not require a world to be visible at the exact edit instant;
make active/parked/inapplicable status understandable.

Explicit user-selected overrides in the current Studio session may affect Main
preview at the correct world/material scopes. Blank/absent overrides preserve
current Main defaults. A saved held-world edit must not silently become a global
default or recolor another scene.

Define shared-material versus per-scene color scope visibly. Keep the initial
choice as simple as practical; do not add a full inheritance/override graph
unless actual requirements demand it. Handle outgoing/incoming scene colors
correctly during blends without resetting director, audio or Echo clocks.

Standalone player default/preset deployment remains separate from Studio preview.
Do not pick new production colors on the user's behalf. Document how the user
saves a color setup and reviews it in Main without changing global defaults.

### Invariants for every batch

- Preserve exact authored expressions/defaults where feasible. Investigate and
  explain any baseline pixel difference; do not automatically relax tolerances.
- Keep stable effect bits, Roots target IDs, old sessions and presets compatible.
  Additive fields may remain compatible; breaking schemas require explicit
  versioning/migration with round-trip tests.
- Reset selected target/scene and revert to preview-start setup remain reliable.
  Loading a preset applies a copy and does not mutate another file.
- Missing roles use authored values; malformed edits retain the last valid state.
  Visibility never depends on filling a palette slot.
- Wheel/hex/brightness and applicable gradient controls update the running preview
  without restarts, blocking the UI, allocating per-frame resources or losing history.
- Keep bounded message size/pending buffers and rate coalescing. The current 16 KiB
  limit may be too small for full coverage: measure worst valid snapshots and adopt
  a justified bounded strategy. Do not silently drop edits or remove all bounds.
- Respect GPU uniform limits and compile/resource costs as targets grow. Measure
  requirements before expanding arrays; use the smallest compatible solution.
- Meaningful labels and effect-owned declarations populate the inspector. Avoid
  enormous flat lists, misleading universal controls and accidental cross-target edits.
- Preserve musical response, geometry, opacity, depth, reflection/occlusion and
  existing performance optimizations. Only the requested color interpretation changes.

### Verification and efficiency

Use the project's .venv and existing standalone harnesses. Run focused meaningful
checks per batch; rerun broad suites after shared-infrastructure changes and at the
end, not after every individual label edit. Never describe a historical pass as new.

For each batch verify declarations/defaults/rejection, old/new session and preset
round trips, reset/revert, live routing, intended-region changes, unaffected scopes,
and synthetic/decoded/live entry paths. A controlled audio fixture is not loopback
listening. Use new timestamped evidence paths; preserve baseline and old captures.

Include quiet/active/release and relevant world/material combinations; compare
authored against the checkpoint baseline. Check cycles and Main transitions, hidden
and reappearing targets, malformed/stale updates, shutdown/restart and continuous
slider gestures. Measure cost at declared resolution and repeated-update resource
behavior; no unsupported FPS promises. Fix introduced regressions before proceeding.

Keep preview windows/processes under task ownership. Do not close the user's
unrelated Studio session or overwrite their current preset/session. Launch isolated
verification instances/settings where needed.

### Completion and handoff

Implementation is complete when every inventory item is accounted for, all applicable
targets are supported and verified, cycles/Main preview work with explicit overrides,
old defaults/sessions remain intact, and feature documentation explains actual use.
Report blockers as incomplete work; do not call them not-applicable to finish early.

At finish provide:
- Coverage summary by family/material/FX, plus precise exceptions and blockers.
- Checks actually run and their evidence; unresolved failures if any.
- Exact Studio steps for editing, scope selection, reset/revert, preset/session
  persistence and Main preview.
- A short user artistic-review checklist; do not claim approval on the user's behalf.
- Git status and a proposed checkpoint scope, without committing unless authorized.

Update DEVELOPMENT_STUDIO.md, TECHNIQUE_LIBRARY.md and relevant technical contracts.
Maintain the ledger after each batch with completed rows, next action, touched files,
evidence and blockers so another model can resume without repeating finished work.
The Overseer delegates updates only to this milestone's status/coverage summary and
the handoff's rollout status if unavailable; do not change unrelated priorities/policy.

### Future creations

AGENTS.md section 17 is the standing policy: new visuals should expose meaningful
applicable colors through this same mechanism, document exceptions, and verify in
Studio. Include the concise extension recipe and applicable regression checks in
the technical guide. Future visuals must not require a bespoke inspector.

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
