# ZeraWave engineering and creative working agreement

Version: 1.3 - 2026-10-04 (settled assignment route)
Project: ZeraWave
Root: `C:\ZeraWave`

## 1. Mission

ZeraWave is a music-reactive visual instrument with character, movement, emotion,
surprise and sustained visual interest. Technical correctness and creative quality
are both completion requirements. Smooth rendering of an uninteresting idea does
not satisfy an expressive scene assignment.

Build on the working project while developing the complete experience requested.
Performance, continuity and maintainability support that experience; they are not
a reason to default to the smallest, quietest or least ambitious visual.

## 2. Source of Truth

The user's latest direction and explicit assignment determine scope. Read the
current code for implemented behavior, ROADMAP.md for priorities and
ZERAWAVE_HANDOFF.md for checkpoint status. Historical documents and task notes
record their own time and scope; their restrictions do not govern later tasks.

Inspect relevant files, interfaces, callers and existing techniques before editing.
Reuse working systems where they fit. When important information cannot be
inferred, ask a focused question and continue independent authorized work.
Make ordinary artistic and implementation decisions within the brief.

## 3. No Architectural Drift

Extend `app/visuals/renderer.py` and the existing audio, parameter, catalog and
Studio systems. Avoid duplicate renderers, parallel inspectors, unrequested
frameworks, stylistic refactors and unrelated module relocation.

New assets, geometry, camera behavior, shader helpers, render passes, bounded
buffers, materials, spatial effects and effect classes can be necessary parts of
an assigned scene. They are allowed within that assignment; they do not
automatically constitute an architectural replacement. Explain meaningful design
tradeoffs and implement the solution that serves the visual result. Do not force
everything into one shader or reduce the art to avoid extending existing systems.

Replacing the overall renderer/audio architecture or adding dependencies outside
the authorized scope still requires a concrete reviewable proposal.

## 4. Preserve Working Systems

Preserve unrelated working features, user files, tests and other agents' edits.
Check callers before interface changes and provide migration for changed storage.
Do not retune audio normalization from a single song or delete tests to hide failures.

A requested redesign authorizes changing the candidate scene's geometry, lighting,
motion, composition and authored palette. Its previous appearance is a comparison
reference, not a requirement for identical pixels. Preservation checks protect
unaffected scenes, valid saved data and shared behavior.

Deletion of existing project files, unrelated major refactoring and architectural
replacement require user authorization. Authorization already given in the task
counts; do not ask again for the same scope. Never discard uncommitted user work.

## 5. Incremental Development

Implement in manageable steps while continuing through the whole authorized task.

1. Inspect the relevant code and current working changes.
2. State the intended visible result and a brief implementation approach.
3. Build, inspect and iterate on the complete assigned feature.
4. Run relevant checks, inspect motion and review the resulting diff.
5. Provide a usable Studio preview and honest handoff for user review.

Do not wait for user approval after each edit, technique, test or internal step.
For scene development, "one addition at a time" means one complete scene for
viewer review. That scene may need several assets and reusable effects. This is
not a one-effect, one-file or one-shader limit.

Pause at the assignment's actual review boundary, such as user acceptance before
Main integration. Explicit authorization may already include integration.
Keep unrelated improvements outside the task. Commit rules are in section 10.

## 6. Testing Requirements

Use the project environment and existing standalone `*_test.py` scripts.
Do not introduce pytest or duplicate test infrastructure merely for convenience.

Choose meaningful checks for the change. Use focused checks during iteration;
run broader regressions when shared changes or failures justify them and at the
appropriate completion point. A documentation correction does not require the
application suite. Avoid repeatedly running exhaustive suites for minor art tweaks.

Report tests actually executed, failures and checks not run. Distinguish syntax,
mocked, synthetic, GPU, decoded replay, controlled-live and natural live-music
evidence. None alone establishes all the others.

For creative work, inspect sequences or motion as well as captures. Judge
composition, visible musical response, evolving behavior and extended interest.
Nonblank frames, numerical color changes and passing regressions do not establish
a compelling scene. The user owns artistic acceptance; testing is not a reason
to stop before the requested creative work is implemented.

Measure resource cost at stated conditions. Optimize avoidable work while keeping
the intended visual quality. Do not claim frame-rate guarantees from shader time.

## 7. Audio Architecture

Keep capture, FFT, normalization and onset analysis in `app/audio/`.
Keep musical interpretation, visual mapping and presentation in `app/visuals/`.
The renderer owns graphics resources, drawing and the window lifecycle.

Reuse shared audio features for new visual expression. Keep mapping independently
testable and avoid coupling analysis to a specific scene.

## 8. Renderer and Shader Integrity

Inspect lifecycle, parameter interfaces, uniforms, callers and resource ownership.
Preserve working window management, loading, event handling and cleanup unless
the task requires a change. Extend the existing renderer rather than creating
another playback engine.

Use appropriate geometry, assets, camera transforms or additional passes when
they improve the assigned scene. Bound persistent resources and handle resize,
restart and cleanup. Existing scene-specific coordinate systems do not dictate
the composition or representation of every future world.

## 9. Dependencies and Environment

Target Windows, PowerShell, VS Code and the existing Python `.venv`.
The development GPU is an NVIDIA RTX 3070 Laptop GPU; measure on the actual device.

Use existing tools and libraries first. Explain and obtain authorization before
installing packages or changing the environment when not already authorized.
Avoid unnecessary paid services or external infrastructure.

## 10. Git and Checkpoints

Inspect Git status and preserve unrelated changes. Before an authorized commit,
review the exact diff, run `git diff --check` and relevant validation, and report
the checkpoint contents. Never stage another worker's changes without authorization.

Do not commit or push without user authorization; authorization persists across
turns. A commit is local, and a push updates GitHub. Do not reset or clean user
work to obtain a clean tree. Preserve the frozen portable; new builds require an
explicitly assigned release task and a new output path.

## 11. Agent Honesty and Reporting

Report only files inspected, changes made, tests executed and behavior observed.
Separate implementation, automated checks and user acceptance. Explain limitations
and incomplete requested work plainly; do not describe a basic prototype as a
finished creative scene when major requested behavior is absent.

## 12. Scope Control

Deliver the user's complete requested outcome. A scene assignment includes the
supporting art, assets, effects, palettes, controls and integration within Studio
needed to make that scene enjoyable and reviewable.

Original materials, spatial techniques and new effect classes are welcome when
they serve the brief. Register useful reusable components in the existing library,
with clear compatibility, names and controls. Avoid unrelated frameworks, cleanup,
dependency upgrades and project restructuring.

For cleanup, inspect current purpose and references, provide the concrete removal
scope and preserve required evidence before requesting any missing authorization.

## 13. AI Agent Operating Protocol

Give a short plan suited to the task, then do the work. Keep the user informed of
meaningful findings, design choices and blockers. Do not turn ordinary creative
choices into repeated permission requests or stop after the first technical pass.

At completion report the visible result, new reusable components, Studio review
steps, checks actually run, limitations and checkpoint status. Keep implementation
detail proportional to what the user needs to review.

Complete and refine the assigned scene before starting another unassigned scene.
A review gate ends that assignment's implementation phase, not each internal step.

### October 1 interview: builder and reviewer briefs

Source: Robert's context interview, 2026-10-01. These briefing and evidence
standards continue for scoped assignments; completed work and current acceptance
belong in ZERAWAVE_HANDOFF.md. Do not resume a historical paused-builder or
first-candidate instruction. Internal iterations are autonomous within the
approved scope. Honest per-scene review target >=7.5; do not inflate scores or
replace recorded user acceptance with an invented technical certificate.

Builder briefs state recognizable scene identity, specific present-input musical
links, quiet behavior, sustained/event contrast, extended variety, reusable
original effects/palettes/non-fade transitions and resource bounds. Depth/3D
optional; generic appearance and weak musical connection equally fundamental
failures. Steady BPM-linked flow is valid.

Reviewer briefs bind hashes, baseline, artifact/time and evidence class.
Assess identity/craft, musical connection, quiet/active/release range,
continuity/variety and usability/performance limits; explain weaknesses and
high-value corrections. A score is not user acceptance, full AV or lab validation.
Stills/silent sequences do not establish continuous listening.

Use small source-bound evidence packs, representative normal-time motion and
affected held/entry/return cases with targeted checks. Reuse unchanged evidence
with provenance. Recompile/recapture for changed risks; expensive startup probes
must resolve a specific uncertainty. Integrated regression/review at batch
boundary, broader checks when shared risk justifies them. Preserve failures;
separate cold startup, warm lifecycle, GPU draw, whole-loop/capture cost and
listening. Never stop unrelated sessions.

Streams commonly last 1-2 hours, sometimes 4+ hours; inspect long-session continuity with
bounded logs/descriptors and proportional soaks. Short clips do not establish
multi-hour variety. Preserve richness, adapt quality before sustained crawl,
derive tiers/LOD from measurement. No assumed FPS/device minimum.

### Approved assignment and review route

1. Robert brainstorms until he signals readiness to prepare an assignment.
   Discussion is not implementation authorization.
2. Bob organizes the requirements, intended result, preservation boundaries and
   open questions without silently narrowing the requested experience.
3. The visible, persistent Prompter prepares a coherent brief from those
   requirements; do not substitute an undisclosed worker or dispatch a builder.
4. Bob and Robert review the brief for completeness, contradictions and scope.
   Resolve missing requirements before the coherent, authorized prompt is sent
   to the sole Builder. Read-only analysis and prompt preparation do not grant
   implementation, shared-document ownership or dispatch authority.
5. The Builder completes and internally refines that authorized scope, then
   returns actual results with source/diff identity, evidence and limitations.
6. The Prompter prepares the actual-results review brief; Bob approves it before
   an authorized critic dispatch. A completed build does not itself dispatch one.
7. The critic performs the bounded, source-bound review. Corrections stay within
   approved findings and scope; a new scope returns through Prompter and Bob.
8. Robert owns user acceptance. Technical checks, critic scores and artistic
   acceptance stay separate; no indefinite automatic fix/rescore loop.

Do not add workers, dispatch a critic, or start a phase merely because a skill
was read or a prompt was drafted. Existing explicit user authorization governs
the assigned scope; this route does not require repeated approval for internal
implementation steps or reopen an already approved brief. Follow the current
handoff/review boundary and section 16 document ownership.

### Project skills: explicitly load the applicable file

- [zerawave-task-handoff](.agents/skills/zerawave-task-handoff/SKILL.md): assignment
  and actual-results transfers, preservation boundaries, source/evidence binding
  and the designated review route.
- [zerawave-evidence-critique](.agents/skills/zerawave-evidence-critique/SKILL.md):
  approved visual evidence reviews with honest attribution and confidence.
- [zerawave-matched-performance](.agents/skills/zerawave-matched-performance/SKILL.md):
  scoped slowdown comparisons and performance evidence with matched conditions.

For an applicable task, read its SKILL.md from the checkout explicitly. A fresh
delegated skill catalog may omit these project files; a user-visible sidebar
refresh is not proof that the delegated task loaded them. Skills do not grant
scope, dispatch, shared-document ownership, integration or commit/push authority.
Validation limits are recorded in ZERAWAVE_HANDOFF.md; do not claim auto-loading.

## 14. Architectural Evolution

Architecture can evolve to support a demonstrated creative or engineering need.
For a major replacement, explain the problem, alternatives, migration risks and
reviewable implementation plan. Ordinary extensions described in sections 3 and
8 can proceed within an assigned scene without a separate architecture task.

## 15. Prime Directive

**Inspect the project. Build the requested experience. Preserve unrelated work.
Verify what changed. Let the user judge the art.**

## 16. Coordination and document ownership

- The user chooses direction and accepts visual results. The Overseer maintains
  ROADMAP.md (sole plan), ZERAWAVE_HANDOFF.md (checkpoint), README.md (entry map),
  AGENTS.md and ZERAWAVE_VISUAL_IDENTITY.md (shared direction).
- Workers can update assigned code, feature instructions, technique ownership,
  relevant maintenance contracts and their task notes. Shared planning changes
  normally go to the Overseer; an explicit documentation assignment delegates
  that scope without another permission request.
- Shared-document ownership does not prevent implementing the user's latest
  assignment. Report stale policy and follow the current user instruction.
- New visuals become reviewable in the existing Dev Studio, followed by user
  refinement and Main integration when approved or already authorized. Add useful
  review controls within the workflow. A general Studio redesign or paid Studio
  product is a separate task.
- A complete world has its own identity, meaningful motion, musical behavior and
  variety over an extended hold. Develop the new assets, materials, spatial
  treatments, palettes or effect classes needed to deliver it. When the brief
  calls for library expansion, ship usable reusable components as part of the
  scene rather than leaving them as optional suggestions.
- Optional notes belong in `docs/agent-notes/<task-name>.md`, one per task.
  Record changes, actual checks, evidence, open issues and proposed status updates.
  No mandatory journals or duplicate backlogs. Notes are evidence, not policy.
- Read the latest file before editing overlapping work; coordinate conflicts.
  Do not clean, revert, stage or commit another worker's edits without authorization.
  Do not stop unrelated user sessions or processes for your tests.

### One-time documentation ownership exception: 2026-10-02

The user assigned Bob ownership for this four-root-document reconciliation while
other builders are idle. This exception covers AGENTS.md, ROADMAP.md,
ZERAWAVE_HANDOFF.md and ZERAWAVE_VISUAL_IDENTITY.md for this pass only; it does
not remove the standing Overseer ownership above. Return to Bob/Prompter before
the next player brief is dispatched. No player implementation, commit or push is
part of this documentation pass. Keep private assistant notes and conversation
exports out of project deliverables.

## 17. Editable artistic colors

New color-bearing visuals must expose meaningful source pigments and gradients
through the existing declarations, generated inspector and live transport.
Document genuine exceptions; spatial-only effects may inherit material colors.
Use stable target/role IDs, clear artistic labels and correct scope.

Design authored colors and named palette families as part of a scene's identity.
When the brief calls for evolving palettes, implement visible, controllable
evolution and useful sharing across compatible targets. Preserve explicit manual
edits, hold/reset behavior and saved sessions. Map compatible artistic roles;
do not assume all effects need the same number or meaning of colors.

A color edit should preserve the target's shading, geometry, audio response and
history unless the control explicitly changes those things. This color-editing
contract does not prohibit redesigning those systems in an assigned visual task.
Missing roles fall back to authored values. Build on the completed inspector
rollout; future scenes must not need a separate editor.
