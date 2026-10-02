---
name: zerawave-task-handoff
description: Prepare a ZeraWave assignment or actual-results handoff with scoped preservation boundaries, source and evidence identity, validation limits, and the assigned approval route. Use for task transfer or review preparation, not routine status updates or independent implementation.
---

# ZeraWave task handoff

Read the current assignment and [working agreement](../../../AGENTS.md).
Use [ROADMAP](../../../ROADMAP.md) as the sole plan and
[handoff](../../../ZERAWAVE_HANDOFF.md) as the checkpoint. Identify dated or
conflicting claims; follow the latest explicit direction without creating another
plan or silently editing shared documents.

## Prepare the transfer

1. State the requested outcome, authorized change boundary, preserved behavior,
   and actual review gate. Distinguish maintenance or color-only changes from an
   assigned redesign. Do not require a separate variant unless requested; when
   assigned, give it a distinct name and preserve the agreed original behavior.
   Consult [maintenance contracts](../../../docs/MAINTENANCE_CONTRACTS.md) and
   [technique ownership](../../../TECHNIQUE_LIBRARY.md) for affected components.
2. Identify the authoritative pre-task local snapshot and final source: repository
   path, HEAD, scoped files and hashes, baseline, evidence-pack index and relevant
   input/settings identity. HEAD alone cannot identify a dirty checkout. Describe
   the exact task diff against its own baseline, including new files, without
   attributing unrelated worker changes to this task. Report missing identities.
3. For a proposed assignment, state decisions, hypotheses and acceptance criteria
   as proposals. For completed work, report actual behavior observed and checks
   executed, with results, failures, evidence paths and reused-artifact provenance.
   Separate implementation, technical validation and user artistic acceptance.
   Select existing standalone checks by changed paths and demonstrated risk;
   broader validation needs a shared risk or unresolved failure. Report checks
   not run without implying exhaustive coverage.
4. Give exact review steps using the existing
   [Studio workflow](../../../DEVELOPMENT_STUDIO.md), known limitations and the
   next decision. Label evidence as syntax, mocked, synthetic, GPU, decoded replay,
   controlled live or natural live listening as applicable. Short sequences and
   numeric soaks do not establish continuous listening or multi-hour visual variety.
5. Follow the current assigned coordination procedure. Where assigned, carry the
   brief through Prompter, approval, the sole builder, actual-results Prompter, and
   an approved critic. Identify the designated owner and existing authorization
   rather than inferring either from historical notes or a skill's name.

## Finish

Deliver a compact transfer containing scope, source/diff identity, verified
results, evidence limits, review route and next decision. Reuse valid evidence;
do not start broad recapture to fill a handoff. Stop at the assignment's review
boundary. Loading this skill grants no dispatch, implementation, shared-document
edit, commit, push or integration permission; existing explicit authorization
still applies. Do not contact other workers merely to prepare the report.
