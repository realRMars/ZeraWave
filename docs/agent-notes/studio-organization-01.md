# Studio organization correction — actual results

Date: 2026-10-03. Sole builder; approved organization scope only. No commit,
push, live capture, renderer work, scene/art changes, Bonk implementation, or DSP
pilot is part of this change. Fresh review and user notification are the next
boundary; the latest DSP pilot direction is Planet Canvas, held for that boundary.

## Before and after

The starting checkout was HEAD `c0f82ad565e41eae29c2cd501a9e2217146d03d0`,
with unrelated dirty player documentation, audio/DSP source, notes and untracked
research files. Baseline byte copies and protected-file hashes are in
`work/studio-organization-01/baseline-identity.json`. The interrupted first pass
created only this evidence; a read-only check found no product changes before
the user authorized resuming the same assignment.

Current ROADMAP explicitly described the Studio cleanup as deferred. The
accepted checkpoint's `studio.py` populated Build & preview from the full
`WORLD_TREE` and displayed a separate Cymatics tools tab. The inspected earlier
`dddc618` Studio organization commit likewise used the full tree. This evidence
supports previously deferred organization, rather than a regression of an
already implemented Main/Experimental split; it is not an exhaustive history audit.
The actual taxonomy is separate Organic and Geometric roots, alongside Cosmic
and Elements. No conversational category was invented.

Build & preview now uses a view derived from canonical `renderer.LIVE_FORMS`:
27 approved leaves, including Galaxy36. Each leaf is filtered independently;
an approved parent does not approve new descendants. Empty categories disappear.
Pruned branches lose their authored cycle so it cannot visit excluded variants.
The source catalog and its stable keys remain unchanged in content.

The displayed Cymatics tab is now Experimental, with its own selectors and
Start/Stop controls. It retains the original Cymatics control component,
oscillator/monitor tools, basin settings, camera/dye/style/band controls and live
actions. The five non-Main leaves are Basin37, legacy transition study4,
Lodestone38, Stormglass39 and Folded Aurora40. They remain reachable through
Experimental, Library and presets. Basin tools show for its branch; remake
selections use ordinary input controls. Experimental has no blank root or mixed
Basin/remake playback mode because those use different existing runner routes.
Source/track/replay settings are shared; visual selections are independent.

Library retains all 176 original inventory IDs, including every world branch,
form, effect and technique. Choosing a world routes to its appropriate tab.
Effects & layers follows the active selection and returns to its owning tab.
Both Start/Stop button sets track the same existing single preview lifecycle.

Saved v1-v3 Main, Experimental and Cymatics projects preserve the original state,
path, colors, layers and settings. Legacy `cymatics` path/widget IDs remain; the
old format did not store notebook tab IDs. New v3 saves add `selection_scope` and
`studio_selections`, while old projects route from their original visual IDs.
Invalid selections produce an error without altering the current project or
substituting a Main form. Loading never rewrites a source file. Cymatics' existing
stored monitor-mute/runtime-reset policy remains in force.

## Exact deliverables and guard

- `app/visuals/world_catalog.py`: independent filtered views, leaf approval and
  cycle/empty-category guard; full catalog retained.
- `app/visuals/studio.py`: Main and Experimental selectors/routing, independent
  remembered selections, compatible session metadata/loading and preview buttons.
- `app/visuals/cymatics_controls.py`: instruction-label correction only.
- `app/visuals/studio_test.py`: focused `--organization-test` using existing
  standalone infrastructure and withdrawn Tk/mocked renderer/device/child paths.
- `DEVELOPMENT_STUDIO.md`: durable organization contract, launch/review guidance,
  session compatibility, offline guard command and scoped Galaxy status correction.
- This task-local actual-results handoff.

`work/studio-organization-01/review-index.json` binds final hashes, exact textual
task diff, baseline identity, check outputs, history finding and preservation
results. Unrelated dirty work is excluded from the task diff. Shared root docs
were not rewritten. Bob may reconcile the now-stale later/deferred Studio item
in ROADMAP and checkpoint after the assigned review/user notification boundary.

## Checks and evidence limits

The final index/logs are the source of truth for commands and results. The focused
organization check covers canonical membership/Galaxy, every filtered leaf,
empty categories, an injected unapproved variant under an approved parent,
Library ID equality against the pre-task tree, retained Cymatics control sections,
96 v1-v3 leaf/session validations, Main/Experimental/Cymatics file roundtrips,
legacy load routing, stored-mute policy, invalid-load preservation, real selector
callbacks/tab events, population side effects, independent selection state,
mocked runner argv and synchronized one-child preview controls.

Tk remains withdrawn throughout. Renderer creation, capture construction,
oscillator monitor construction and child launching are blocked except for
explicit mocks. No visible Studio/player windows, GPU draws, audio monitoring,
device enumeration or live capture were started. Syntax and scoped diff checks
are separate evidence. Renderer/shaders, player/capture/audio source, pre-existing
DSP files and unrelated baseline documents are checked byte-for-byte.

Initial iteration failures are retained separately: an invalid test fixture put
optical_gain at the wrong level; a v1 test incorrectly expected the newer leaf
path rather than its established state-to-branch migration; workspace temporary
fixture creation was denied by the sandbox until the authorized offline command
passed automatic escalation review. These were test/setup corrections. No
product failure was removed or unrelated test deleted. The full Studio suite,
rendered/live preview, device/audio quality and layout appearance were not tested.

## User review steps and next boundary

When convenient, launch `run_development_studio.bat` manually. Build & preview
should offer Organic, Geometric, Cosmic and Elements; Cosmic > Galaxy is present.
Experimental should offer Cymatics > Water - Resonance basin and Experimental /
unfinished > the legacy study/three remakes. Switch between the two tabs and
confirm each remembers its visual selection. Library remains the complete
inventory and routes a chosen Basin/remake to Experimental. Load an existing
project to confirm its original visual/settings appear in the appropriate tab;
save only when deliberately requested. No user project was rewritten by testing.

Return actual results to Bob/Prompter for the fresh review brief and approval,
then user notification/acceptance. Do not automatically start Aftershock, the DSP
pilot, another scene, publication or the separately authorized Bonk mode work.

## Read-only Bonk route for the next brief

No Bonk code changed. `player.py` sends `bonk`; `player_runtime.py` forwards it to
`Playback.bonk(transitioning)`. It sets one pending request only while running,
unpaused and outside an active transition. `Renderer.update_blend` changes the
reason to Bonk and clears beat waiting; it bypasses ordinary dwell/Galaxy route
waiting and overrides Hold once. The next queue/weighted candidate and compatible
transition recipe use the existing normal selection route. Same-world/empty
queue results preserve existing handling.

Bonk normally selects a 6–9-second transition (`reason != 'release'`). The panel
percentage is the clamped linear fraction `(director_time - director_transition)
/ director_duration`, formatted as a whole percentage, not an intensity/probability
setting. The renderer applies smoothstep to that fraction before its transition
recipe uniforms. Bonk is ignored during Stop, Pause or an active transition;
capture unavailable also holds director processing. No Normal/Instant selector
or instant path currently exists. This is source inspection, not a timing/live
measurement, and needs its own bounded next-change brief.
