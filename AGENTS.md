# ZeraWave Engineering Doctrine

Version: 1.0
Project: ZeraWave
Root: `C:\ZeraWave`

## 1. Mission

ZeraWave is a music-reactive visualizer that transforms real audio into a living visual experience.

The engineering goal is to build upon the existing project incrementally, preserving working systems while expanding capability.

Correctness, continuity, and maintainability take priority over coding speed.

## 2. Source of Truth

The current repository is the source of truth.

Before proposing or implementing a change:

1. Inspect the relevant existing files.
2. Identify current interfaces, dependencies, and behavior.
3. Check whether the required functionality already exists.
4. Reuse existing modules wherever practical.
5. Ask for clarification when important context is missing.

Never assume a module is absent because it was not mentioned in a prompt.

Never recreate a working system simply because a new implementation seems cleaner.

## 3. No Architectural Drift

Do not introduce new architecture, duplicate modules, abstractions, frameworks, or dependencies without a demonstrated need.

In particular:

- `app/visuals/renderer.py` is the existing renderer and must be inspected before any renderer-related work.
- Do not create a second renderer, parameter system, audio pipeline, or shader interface that duplicates existing functionality.
- Do not relocate or rename working modules as part of unrelated tasks.
- Do not refactor working code merely for stylistic preference.

If an existing design presents a genuine limitation, explain the limitation and propose the smallest viable change before implementing it.

## 4. Preserve Working Systems

Existing tested functionality is valuable project state.

Agents must not casually:

- Delete or overwrite existing files.
- Remove tests because they are inconvenient.
- Replace working implementations wholesale.
- Change established interfaces without checking their callers.
- Retune working audio normalization based on a single song.
- Introduce breaking changes without identifying their impact.

File deletion, major refactoring, and architectural replacement require explicit user approval.

## 5. Incremental Development

Work in small, independently verifiable steps.

Required workflow:

1. Inspect.
2. Explain the intended change.
3. Identify the exact files to modify.
4. Make one small logical change.
5. Run the relevant standalone test(s).
6. Inspect the output and resulting diff.
7. Report results and any remaining concerns.
8. Request approval before committing.

Do not bundle unrelated improvements into the same change.

Do not continue to the next implementation step until the current step has been reviewed.

## 6. Testing Requirements

ZeraWave currently uses standalone Python test scripts.

- Do not install or introduce pytest unless explicitly requested.
- Prefer existing `*_test.py` scripts.
- Extend existing tests when appropriate instead of creating duplicate test infrastructure.
- Do not claim a test passed unless it was actually executed and its result inspected.
- Distinguish between tests that passed, tests that failed, and tests that were not run.
- A successful import or syntax check does not prove runtime correctness.
- A mocked test does not prove real audio or graphics integration.

For audio-reactive graphics, preserve the distinction between:
- Synthetic signal tests
- Live audio tests
- Renderer/shader tests
- End-to-end real-time visual tests

## 7. Audio Architecture

Maintain clear separation of responsibilities:

`app/audio/`
- Audio capture and analysis
- FFT and frequency-band calculations
- Normalization and smoothing
- Onset/transient detection

`app/visuals/`
- Mapping audio signals into visual meaning
- Visual parameter definitions
- Visual simulation and presentation
- Existing renderer and shader integration

Renderer internals:
- Graphics resource management
- Shader execution
- Geometry and drawing
- Window and rendering lifecycle

Audio analysis should not become coupled to graphics implementation details without a demonstrated requirement.

Visual mapping should remain independently testable.

## 8. Renderer and Shader Integrity

The existing renderer and shaders must be inspected before changes.

Before modifying renderer behavior, identify:

- Current renderer lifecycle
- Existing parameter interface
- Existing shader uniforms
- Current rendering behavior
- Existing tests and callers

Preserve working window management, shader loading, geometry, event handling, buffer swapping, and cleanup unless the task specifically requires changing them.

Prefer extending the existing renderer and shader interface over creating a parallel system.

## 9. Dependencies and Environment

Target environment:

- Windows
- PowerShell
- VS Code
- Python virtual environment: `.venv`
- Git
- NVIDIA RTX 3070 8GB

Do not install packages, alter the environment, or introduce new dependencies without explaining why and receiving approval.

Use the existing virtual environment for project tests.

Avoid changes that unnecessarily require cloud services, paid APIs, or external infrastructure.

## 10. Git and Checkpoints

Git checkpoints are part of the development process.

Before changes, inspect Git status when practical.

Before committing:

- Review the exact diff.
- Run `git diff --check`.
- Run relevant tests.
- Confirm unrelated changes are not included.
- Report the proposed commit contents.

Never discard, reset, overwrite, or clean uncommitted user work without explicit approval.

Do not commit without explicit user approval.

The desired checkpoint state is a clean working tree.

## 11. Agent Honesty and Reporting

Agents must accurately report what they did.

Never claim to have:
- Inspected a file that was not inspected.
- Run a test that was not executed.
- Verified behavior that was not observed.
- Completed a task that remains partially implemented.

If something is uncertain, say so.

If a tool fails, report the failure rather than silently substituting an assumption.

Do not hide warnings, regressions, skipped tests, or incomplete work.

## 12. Scope Control

Follow the user's immediate task.

Do not autonomously expand scope into:
- Unrequested refactoring
- New frameworks
- New renderer architecture
- Dependency upgrades
- File cleanup
- Broad project restructuring

When cleanup appears beneficial, first provide:
- The exact files involved
- Their current purpose
- Evidence they are redundant or obsolete
- Risks of removal
- A proposed safe cleanup plan

Wait for approval before deleting files.

## 13. AI Agent Operating Protocol

Before implementing a task, provide a brief plan containing:

- Existing files inspected
- Current behavior
- Exact proposed change
- Files expected to change
- Test that will verify the change

If the task cannot be completed safely with the available context, stop and request the missing information.

After implementation, report:

- Files changed
- Summary of changes
- Tests actually executed and results
- Known limitations or concerns
- Git status
- Recommended next step

Do not independently move to the next task without review.

## 14. Architectural Evolution

This doctrine does not prohibit future redesign.

Architecture may evolve when actual requirements, observed limitations, or test results justify it.

Any significant architectural change must include:
- The problem being solved
- Why the existing design is insufficient
- Alternatives considered
- Migration and regression risks
- A reviewable implementation plan

The objective is deliberate evolution, not permanent attachment to the first design.

## 15. Prime Directive

**Inspect before creating. Preserve before replacing. Test before claiming. Review before committing.**

Build ZeraWave from the working project that exists—not from an imagined clean slate.

## 16. Coordination and document ownership

The user's current instructions and explicit assignments take precedence.
These rules prevent conflicting edits, not ordinary progress within a task.

- The user chooses direction and accepts visual results. The Overseer maintains
  ROADMAP.md (sole plan), ZERAWAVE_HANDOFF.md (current checkpoint), README.md
  (entry map), and shared policy in AGENTS.md. Treat ZERAWAVE_VISUAL_IDENTITY.md
  as a shared design contract: propose changes unless assigned to edit it.
- Workers read these shared documents but do not independently rewrite them.
  Report proposed status/priority/policy changes to the user/Overseer in the
  task result or an optional note. An explicit documentation assignment may
  delegate named shared files; do not request permission again for that scope.
- Workers may update feature-specific operating/technical documentation such as
  DEVELOPMENT_STUDIO.md, TECHNIQUE_LIBRARY.md, PLAYER.md and maintenance contracts
  when needed by their assigned change. Coordinate overlapping files first;
  read the latest contents and preserve other workers' edits.
- New visuals normally become reviewable in the existing Dev Studio, then receive
  user review/refinement and Main integration when approved or already authorized.
  Supplemental scripts are not a replacement for this workflow. Studio redesign
  and commercial product work are not implied by adding a feature control.
- Workers can carry out routine implementation, related tests and necessary
  fixes within their assigned scope. The review gates in sections 5 and 13 mean
  logical task/artistic/scope boundaries, not approval after every edit or test.
  Existing explicit requirements for deletion, dependencies, major architectural
  changes and commits remain. Previously granted user authorization still counts.
- Optional notes belong in docs/agent-notes/<task-name>.md, one per task, not a
  new root journal. A concise final chat report is sufficient for short tasks.
  Notes contain scope/files, changes, checks actually run, evidence links,
  unresolved issues and proposed handoff updates. Separate reported facts from
  acceptance and proposals. Do not copy the roadmap or large logs into notes.
- Notes are working evidence, not policy, approval, or a competing backlog.
  Workers own only their task note; the Overseer promotes reviewed conclusions
  into shared docs. Historical snapshots remain preserved records.
- Before editing, inspect Git status and identify owned files. Never clean up,
  stage, revert or commit another worker's changes. Do not start a conflicting
  mutation while another worker relies on those files or processes.

## 17. Editable artistic colors

For new or extended visuals, consider meaningful editable color targets through
the existing color_controls declarations, generated inspector and live transport.
Preserve authored defaults, shading, geometry and musical response; use stable
target/role IDs and clear artistic names. Document intentional exceptions or
unsupported controls. Verify applicable controls through Dev Studio. Expose useful
artistic choices, not every computed shader expression. Existing-world rollout is
assigned in reviewed batches; this rule is not authorization for a mass rewrite.
