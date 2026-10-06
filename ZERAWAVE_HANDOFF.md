# ZeraWave handoff

Updated: 2026-10-06 (Qt Studio development checkpoint publication authorized).
[ROADMAP.md](ROADMAP.md) is the sole plan; [AGENTS.md](AGENTS.md) owns the working
procedure. Prior checkpoints and their limitations remain below.

## Current Qt/Studio development checkpoint

Robert authorized this development commit and normal GitHub push on October 6.
Source/staged-content checks, complete checkpoint scope and exact commit/remote
identity are recorded in the [publication receipt](work/publication-qt-studio-20261006/review-index.json).
The parent is `4a4f6e03ad2119e790e88d8338bac9412a139881`. Publication includes the
Qt prototype and reviewed rendering dependencies, later Studio additions,
resolution/resize controls and Audio Hub. No release or frozen portable rebuild.

Current source is bound by the layered
[Studio additions](work/studio-additions-20261005/source-final.json),
[resolution batch](work/studio-three-items-20261005/source-final.json) and
[Audio Hub](work/audio-hub-20261006/source-final.json) manifests. Each older report
retains its own source, input, results and pre-publication status. The root-guide
publication edits are a separate delta; original evidence is not resealed.

Category BONK/direct leaf load, Resources, inline startup and native header are
implemented; see [Builder results](docs/agent-notes/studio-additions-20261005.md).
Resolution choices and native resize guards are implemented, including shared
menus and fixed-pixel aspect fit; see [resolution results](docs/agent-notes/studio-resolution-controls-20261005.md).
Audio Hub's Device Listening/Audio File modes share a bounded PCM owner, with
file transport separate from visual controls; see [Audio Hub results](docs/agent-notes/studio-audio-hub-20261006.md).
Saved user layouts/settings stay local; documented unexplained layout changes
are retained rather than restored. The overwritten historical Qt screenshot
exception remains recorded, not silently repaired.

Later Roots/Sky overlap is about39ms /25–26 swap returns/s; the mostly≥30FPS
full-size target and strict maximum/tail gates remain incomplete. Prior GUI9/10
and provisional usability8.5/10 retain their original scope. Physical keyboard,
mouse, DPI/monitor changes, natural listening, latency, all-world/fullscreen and
multi-hour coverage remain bounded or unverified. Audio backend acceptance is
not heard-output proof. Normal GPU Main + Audio Hub was not observed in that
bounded audio pass; Experimental/matched-audition restrictions remain.

<a id="current-unpublished-full-size-qtrendering-candidate"></a>

## Earlier independent full-size review — October 5

**Independent verdict: PARTIAL.** The Root preparation optimization is worthwhile;
Robert's practical maximized-editor/full-size playback goal remains incomplete.
Published main remains `4a4f6e03ad2119e790e88d8338bac9412a139881`.
That reviewed candidate was unpublished at the review boundary. Prior GUI visual match **9/10**
and usability **8.5/10 provisional** carry forward unchanged; neither this review
nor the documentation reconciliation awards new acceptance or publication authority.

### Source and evidence identity

- [Independent REVIEW.txt](work/publication-qt-studio-20261006/independent-review/REVIEW.txt):
  SHA-256 `feb8cd77ff8dee50dcfb81af13d083ab0e560bc5b520db6d8d432b2eebe8fa3b`.
  Supporting identity, statistics, clock audit and execution receipts are in that
  same review directory.
- [Builder report](work/full-size-performance-20261005/REPORT.md) and
  [task-only patch](work/full-size-performance-20261005/task-only.patch): patch
  SHA-256 `0781573c9691ce0e0b0d6b9cdf10be498e882289f5367c3aeceb2023e3f5585d`.
  Its baseline is the preserved dirty pre-task directory, not published HEAD.
- [Final manifest](work/full-size-performance-20261005/source-final.json): SHA-256
  `fe09c7742ca6f3e5f5b3023de2d96abaef0f8659eb0b77f080eefdbdb9aa8b1c`.
  Reviewer verified 282 final / 280 baseline bindings and 767 indexed evidence files.
- [Builder evidence archive](work/full-size-performance-20261005-evidence.zip):
  94,385,539 bytes, SHA-256
  `0939af6ed9cf71c3475bd6cad3c7e2581ea03d29b3325ab6449e7ddc0018c75b`;
  Reviewer verified ZIP CRC integrity. Original reports/manifests remain intact.

This documentation-only delta follows that review. All 282 final bindings matched
on entry to the reconciliation. Changed guidance hashes do not reseal the historical
manifest or mean the application was retested. Application source, settings, saved
layouts and evidence artifacts are outside this documentation assignment.

### Reviewed results and evidence classes

The Reviewer independently executed one sequential before/final Roots12 -> Sky19
optical-fade fixture through Qt Shell -> ControlClient -> hidden Tk owner ->
production Renderer, plus eight synthetic GPU uniform/gain/direct-draw contracts
(all passed). RTX 3070 Laptop, actual framebuffer/internal/shader **1944x986**,
Main/all30, Full 100%, real-time Synthetic, seed7301, authored colors, no layers,
captures off, forced endpoints and Normal BONK after stable sizing. This is an
adopted window with swap interval 1 on a 144 Hz monitor, not native fullscreen or
Robert's exact session. Background/thermal/power conditions were not locked.

| Fresh independently executed phase | Before mean ms | Final mean ms |
| --- | ---: | ---: |
| Roots steady | 32.36 | 15.94 |
| Entry | 74.67 | 40.93 |
| Optical overlap | 96.58 | 46.85 |
| Exit | 96.96 | 46.83 |
| Skyfade arrival | 66.32 | 32.78 |

Reductions of 45.2-51.4% corroborate meaningful gains beyond the prior audit's
0.51% mean / 1.27% median variation. Swap-return intervals are not scanout FPS.
The fresh short pair is corroboration, not a tighter variability certificate.

**Independently recalculated Builder evidence:** all eight ordinary distributions
retain counts, outliers and >50ms intervals; all 43 Full-pixel comparisons were
recalculated (27 byte-exact, remaining differences at most one 8-bit channel step,
worst mean 0.0000226073 levels). Representative supplied stills were inspected.
These support sampled preservation, not universal artistic/temporal equivalence.
**Reused Builder evidence:** fixed-clock traces, query/pass attribution, 48
same-value API edits and the passing owned docking/resize/lifecycle fixture.
They are not independently repeated GPU timings or physical knob tests.

### Gates and unresolved coverage

- PASS: source/evidence identity, matched Full pixels, meaningful measured gains,
  sampled pixel preservation, retained endpoints/history and bounded source clocks.
  The independent GPU contracts cover current gains, encoded inputs, direct draw,
  independent clocks, exact framebuffer/viewport restoration, fixed resources and release.
- FAIL practical completion: optical overlap remains about **45-47ms**, roughly
  21-22 swap returns/s. FAIL observed strict no-worse-maximum gate: some final
  maxima exceed both baseline maxima despite improved median/p95/p99. Population
  tail non-regression remains unverified; no threshold or outlier is discarded.
- UNVERIFIED: exact Robert-session reproduction, continuous final normal-time
  motion/listening, changed-value physical Qt knobs, keyboard/DPI/save-load,
  complete recovery, native fullscreen, scanout, all-world coverage and multi-hour
  stability/variety. Computer Use was stopped by the user's physical Escape;
  inspection was limited to supplied stills and a partly occluded baseline Sky snapshot.
  The additional independent lifecycle fixture was interrupted during compilation,
  not a completed docking check or demonstrated application failure. Builder's
  source-bound lifecycle pass remains reused evidence.
- User-state preservation is incomplete: saved Qt layout changed from `437a73...`
  to `938ed0...`, docks/geometry changed, controls unchanged; recorded save 14:31:18
  followed initial comparison 14:29:17. Cause is unknown. Tk stayed `9e2716...`.
  Preserve both evidence copies and the current saved layouts; restore neither.

**Clock correction:** the earlier 0.998605-1.000790 ratios compare source timestamps
before render with `present_wall` after swap. Endpoint latency changes bias the
approximately 24-second span (+33.5407ms / -18.9270ms in the reviewed examples).
At equivalent source/render-begin boundaries, all eight ordinary ratios are
0.9999998956-1.0000005168, monotonic, with at most 0.0124ms residual span difference.
The literal 0.999 presentation-span lower bound failed in baseline data; it is not
a source-clock regression, and the gate is not silently revised. Fixed-clock
300-state traces verify mapping, not real-time progression or long-session behavior.

### Remaining priorities and review route

Reviewer ranks: P1 Roots/Skyfade overlap/exit/entry; P1 rare waits; P2 Skyfade
arrival/steady (~33ms); P2 Spires steady/entry (~33-34ms); P2 Molten arrival (~23ms).
Composite costs are supported; individual material/shared-region owners are not
yet isolated. Root preparation (~0.012-0.023ms) and Echo (~0.023ms/step) are minor
in the measured overlap. Exceptional waits are distinct from sustained draw cost;
their driver/display/queue owner is unknown. Other Main worlds are unmeasured.
The rejected ~6.5% Spires projection hoist remains negative evidence. Cold startup
remains costly and separate from these warm hotspots.

Research options are untested proposals: exact-equation preparation/dependency
pruning, bounded specialization, and only conditionally a split optical compositor.
See [technique references](TECHNIQUE_LIBRARY.md#rendering-references-and-untested-options).
No API migration, renderer overhaul or artistic reduction is established as necessary.
The approved scope here is documentation; the next bounded Builder work awaits
Robert's manual handoff, then independent verification and hands-on acceptance.

**Distinct pending UI gap:** legacy renderer/system/device telemetry exists, but
the dedicated Qt CPU/GPU/memory resource view is missing. Quiet actual resolution/
preview-scale information belongs to that separate UI scope. See the
[Studio distinction](DEVELOPMENT_STUDIO.md#resource-telemetry-and-pending-qt-view)
and [sole plan](ROADMAP.md#next-bounded-work-and-separate-monitor-scope).

Robert's hands-on sequence: `run_qt_studio.vbs` -> maximize editor -> Main/all
worlds -> Full quality -> Start -> Normal BONK; observe entry, overlap and arrival.
Acceptance and publication remain separate decisions. No worker is dispatched.

<a id="current-measured-performance-candidate"></a>

## Historical accepted measured-performance checkpoint

**Status:** Robert passed this candidate for a development checkpoint on October 5
and authorized commit and normal GitHub push. Existing Main30 artistic acceptance
is unchanged. The roster has 30 eligible forms, including Fractal41–43, with
Branching Iris and Flowing Fold. The limitations below remain; this acceptance
is not exhaustive artistic, listening, performance or device certification.
Exact scoped-file/source/staged checks and commit/remote identity are recorded
in the [publication receipt](work/publication-performance-20261005/review-index.json).
No new critic, implementation or release is dispatched; the frozen portable remains.
Main's three Envelopers remain off, and Full quality remains the default.

### Identity and implemented behavior

At that pre-publication checkpoint HEAD was
`b2aacd11d7d3a8d39bb9d2f5592659fd3d2d999b`. The task baseline is the
pre-task dirty tree, including Main30 and the startup correction, bound to
`4ba8d42c82f12a2ca69dc553c8d29bc5652b6cfd9f0cf2554a3510e2f2144d88`.
The final 170-file app identity is
`765543e7a927c1b4837695c8cb1c3b0215819d326d20354064ac196b107bec0e`;
the generated NVIDIA shader is
`a1e9e84ccf3b87480a2744d0c732363c114803cdfe8310ace839a4596adf1998`.
HEAD alone does not identify the dirty candidate. Exact task-only baseline diff,
source bindings and evidence lineage are preserved in
[task-diff.patch](work/performance-fixes-20261004/task-diff.patch),
[final-source.json](work/performance-fixes-20261004/final-source.json) and
[evidence-index.json](work/performance-fixes-20261004/evidence-index.json).
This later two-document reconciliation is a separate delta, not a reseal of
Builder's historical preservation statements.

Suitable raw audio resolves once per frame, retaining local derived aliases,
float32 gain/clamp/encoded-input semantics, endpoint ownership, Planet adapters
and Fractal context. Water resolves exact weighted ingredients outside its loops.
New previews default captures off while preserving saved choices; a bounded worker
handles statistics/PNG work, and replay telemetry streams rather than retaining
an unbounded track-length list. GL readback stays on its owner; backlog drops/errors
are reported, and normal close drains accepted work.

Preparation/monitor cadence is cached with live commands preserved. Surface
formats are unchanged and targets allocate lazily; necessary Cavern prefetch
remains bounded. One integrated program uses cached declared-uniform handles,
NVIDIA limited inlining and bounded first-use prewarm. Family splitting was tried
and not adopted. Other vendors retain their normal compiler policy. Explicit
Full/75%/50% preview scales preserve counts/colors/clocks but lower scales soften
detail. See [operating guide](DEVELOPMENT_STUDIO.md) and
[actual results](docs/agent-notes/performance-fixes-20261004.md).

### Measurements and remaining tradeoffs

RTX 3070 Laptop, NVIDIA 617.14, GL 3.3; matched hidden loud owner-active synthetic
1280×720 GPU queries, 15 warm + 40 measured frames per cell. Thermal/background
conditions were uncontrolled. These numbers are GPU render cost, not visible FPS.

| Case | Audit median ms | Final median ms |
| --- | ---: | ---: |
| Dyes | 80.24 | 16.23 |
| Waterfall | 67.27 | 15.64 |
| Sky Citadel | 26.88 | 22.85 |
| Crystal Cavern | 18.97 | 21.09 |
| Marsh | 31.00 | 35.47 |
| Planet Canvas | 19.35 | 21.91 |
| Waterfall→corridor optical crossfade | 81.27 | 30.12 |

Compiler policy improves cold compilation/memory at the cost of GPU regressions
in Cavern/Marsh/Planet and Fractals: Tidal rises from about 3.3 to 10.0 ms.
Cold program 195.76→110.04 s (candidate create 111.29 s); observed working-set
peak 13.21→6.49 GiB, private 13.91→6.98 GiB. Baseline guard peak is process-wide
and includes a subsequent variant probe; cold timing uses its initial compilation.
Cold startup remains long and vendor-specific; cold visible first presentation
was not measured. Profiled CPU render 17.47→7.78 ms is not isolated unprofiled
submission. Enabled capture copy/readback median 1.76 ms + submit 0.034 ms;
worker completion about 150.5 ms remains separate and readback can still stall.

430/635 fixed-input matrix frames are pixel-exact. Most other differences are one
8-bit step; larger Marsh differences remain (worst mean 1.53/255, max 69).
Common uniforms matched in the checked differing frames; compiler arithmetic
amplification remains an inference. Paired synthetic Marsh motion was inspected,
but Robert owns appearance acceptance. Full still misses 60 FPS in expensive
scenes/transitions; scaled tiers are different workloads and are not FPS guarantees.

### Evidence limits and review gate

Builder records focused CPU/mock/decoded-owner checks, the full Studio regression
including actual GPU routes and child restart/cleanup, final Fractal/Main GPU
warp/Repeat/Return/resize, and normal-time Root→Tidal Iris/Fold scoped-frequency
checks. The full Planet script retains its pre-existing historical inverse-SHA
guard failure, reproduced with pre-task raw shader bytes; focused behavior checks
pass. Failed experiments and logs remain preserved; no guard was removed.

Visible silent decoded 720p Waterfall capture-off/on 24-second arms and ordinary
Main 60-second Full/75% arms precede final CPU-cache/Cavern-preparation/Fractal-
context corrections. Their source lineage is explicit in the index; final hidden
source-bound checks cover the corrections. The Main arms also differ in diagnostics
and sampling, so they do not isolate scale or prove final-source 60 FPS. 50% was
GPU-tested without a visible decoded arm. User Escape stopped Computer Use and
it was not restarted. Natural AV listening, multi-hour rendered soak, other
vendors and true fullscreen remain unverified.

Authored JSON, audio analysis, raw shaders, unrelated snapshot work and user
settings were preserved by Builder. Original audit evidence remains unchanged;
[AUDIT_INDEX_CORRECTION.md](work/performance-fixes-20261004/AUDIT_INDEX_CORRECTION.md)
and [companion audit index](work/performance-fixes-20261004/audit-artifact-index.json)
repair indexing without rewriting the original archive.

For further refinement, follow [Builder's Studio review steps](docs/agent-notes/performance-fixes-20261004.md#exact-studio-review-and-next-decision)
at 1280×720, real time, captures off and Full quality; review edited tuning/colors,
Marsh, slower scenes and affected transitions, then optional softer scales.
Robert has approved this development checkpoint for publication; later refinements
follow his feedback and a separate assignment.

<a id="current-main-audio-tuning-checkpoint"></a>

## Published Main Audio Tuning checkpoint — October 4

The following source-matching statements, inventory counts and measurements
belong to that historical checkpoint and its recorded evidence. They are not
claims about the later dirty Main30/performance candidate above.

- **User acceptance:** Robert accepted Planet range/gain tuning visually and
  musically on October 4 at 06:48 UTC, then checked the rollout and accepted this
  development checkpoint with caveats. That acceptance is distinct from exhaustive
  artistic, listening, performance or multi-hour certification.
- **User observation:** Robert observed a transition hitch and requests a
  performance revisit. An earlier preview ran at 12×; that run cannot establish
  real-time smoothness. Real-time transition/presentation behavior remains important
  and unresolved. No optimization or new Studio controls are part of publication.
- **Implementation:** normal Studio Audio Tuning covers all 27 canonical Main
  forms, including Galaxy36, with independent form/target/role settings, Mapping
  monitor and compatible pair audition. Experimental/Cymatics remain excluded
  until promoted. The three Envelopers remain off in Main by default.
- **Publication:** this checkpoint builds on
  `0342e518a7bd2c521416e8027a7920668fc5ee51`, the published Studio organization
  and Normal/Instant Bonk checkpoint. The authorized development commit and normal
  push completed at b2aacd11d7d3a8d39bb9d2f5592659fd3d2d999b; local and remote
  main were verified equal at publication. It includes the reviewed rollout,
  dependencies, tests, authored settings and documentation. The complete manifest,
  full delta, checks and exact local/remote SHA verification belong in the
  [publication receipt](work/publication-main-audio-20261004/review-index.json).
  The rollout-only patch is not the whole publication delta. Local evidence,
  private media/settings, research and the four undecided notes remain excluded;
  the frozen portable is unchanged.

### Dirty-source identity and evidence chronology

The [rollout index](work/studio-audio-rollout-01/review-index.json) records the
task delta, source hashes and preservation results against the dirty
[checkpoint](work/studio-audio-rollout-01/checkpoint.json) and
[resume baseline](work/studio-audio-rollout-01/resume-baseline.json).
The earlier documentation audit matched all 28 source/note bindings, 92 local
links and 236 preserved files. The latest
[foreground index](work/studio-audio-rollout-01/foreground-review-index.json)
still binds the unchanged application/test bytes. Publication adds only a dated
current-status pointer to its task note; the original body and hashes remain
historical evidence. Final status edits have their own publication delta and
refreshed documentation checks. HEAD's full diff includes separate work and is
not the rollout delta.

- **CPU/native:** 15 recorded groups passed. The workflow continuation reran the
  two changed integration/native tests and reused 13 unchanged test-source
  results with provenance; it did not rerun every earlier group.
- **GPU supplement:** [GPU index](work/studio-audio-rollout-01/gpu-review-index.json)
  records 1,396 draws across all 27 forms and shared dream/surface/Original Loop,
  Echo and Enveloper paths. Seven owned contexts closed without GL errors or
  effect fallback. Its pair fixture used supplied controls and a no-op source
  callback; it was not yet an integrated decoded audition.
- **Decoded workflow:** [workflow index](work/studio-audio-rollout-01/workflow-review-index.json)
  adds a successful 224-draw actual replay-owner trial: 64 repeated and 44 resumed
  frames, saved source-position restoration, controlled error recovery,
  cancellation and cleanup. Repeat endpoint/window priming and stale ACKs
  overwriting parked unsent edits were corrected. Prior failed trials remain
  evidence; later successes do not retroactively change their results.
- **Foreground continuation:** nine scripted visible Studio observations used
  actual transport and decoded replay for Follow, Pin/unpin, inactive editing,
  held-key/gesture cancellation and the real Save Authored callback redirected
  to a temporary file. This is visible scripted validation, not manual user
  acceptance. No application source changed in this continuation.
- **Inventory:** 595 means selectable tuning target rows (571 generalized plus
  24 Planet), including shared-technique instances and transitions. It does
  not mean 595 independently GPU-verified sliders or visual subelements.

Earlier GPU bindings intentionally predate the replay/UI fixes. The exact earlier
CPU index and patch are preserved in
[workflow-before](work/studio-audio-rollout-01/workflow-before/); renderer/shader
consumer sources were unchanged for that reuse. The workflow source bindings
match current application/test bytes; its task note was subsequently extended.
One provenance discrepancy remains: the workflow index records patch SHA-256
`b6894092eead612e27f9d01cf7c30a84f28bd97552b8275dfbe7ffeeacca3290`
at the shared `task-only.patch` path, now replaced by the later patch
`559041a41d4ab5994738d024277561082cb41566d3665217a9176dd7dc0336b2`.
No exact intermediate patch copy was found in that evidence directory.
The latest rollout/foreground indexes bind the current patch; historical
manifests are preserved without rewriting their hashes or claims.

### Preservation and limits

All 22 backed-up authored settings and six standalone DSP files match their
recorded hashes. The foreground evidence records removal of temporary saves,
closure of owned Studio windows and graceful replay-child exit. Exact prior-focus
restoration was unverified because the recorded window handle no longer existed;
no unrelated application was reopened or terminated.

The GPU supplement used an RTX 3070 Laptop GPU, driver 617.14, hidden 320x180
targets, query/finish/readback instrumentation and no scanout measurement.
First current-source compilation took 161.95 seconds (first creation 163.70 s).
Intermittent readings observed a process working-set peak of about 13 GB, a
lower bound rather than a continuous memory profile. Cached motion-arm creation
was 0.37–0.57 s under those conditions; power/thermals/background load were
uncontrolled. Startup/resource limitations remain unresolved. Planet neutral
frames matched 240/240; Root matched 238/240, with a one-channel-level difference
at one pixel in each other frame. No universal pixel-equivalence claim follows.
The integrated decoded audition was also hidden 320x180 and accelerated;
Return restores CPU/source state but restarts shared GPU history.

Exhaustive per-form/control artistic review, continuous audiovisual listening,
native-resolution/fullscreen FPS, resize regression and multi-hour behavior
remain unverified despite development-checkpoint acceptance. Recorded engineering
results are reused with their source/provenance limits; publication adds source,
syntax, staged-content and documentation checks, not a new GPU or listening campaign.
[Studio instructions](DEVELOPMENT_STUDIO.md#main-audio-tuning-and-mapping-monitor)
describe the controls; the [rollout note](docs/agent-notes/studio-audio-rollout-01.md)
now has a dated current-status pointer above its preserved CPU-checkpoint opening.

The completed eight-file documentation pass retains its own baseline and delta in
[documentation review index](work/documentation-reconciliation-20261004/review-index.json)
and [task diff](work/documentation-reconciliation-20261004/task.diff).
Pre-existing dirty documentation was part of that baseline. This later publication
authorization adds narrow acceptance/status edits and the task-note pointer;
it does not rewrite that earlier audit or its no-publication scope.

## Verified visual baseline and acceptance

Historical visual baseline, verified on GitHub main when published:
`2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5` —
[Refine approved worlds and integrate Galaxy into Main](https://github.com/realRMars/ZeraWave/commit/2bcb03fdd1ec03a49189b3b3c343dcb053fbc9b5).
Robert accepted the current Main/Galaxy preview and authorized this normal
commit/push. The committed tree matched the reviewed82-file checkpoint; remote
main was then verified to equal that exact commit. No release was built.

The visual batch, bounded-resource/entry-projection corrections and Main lineup
are implemented at that checkpoint. Earlier first-Cavern/provisional7.0 and
paused-builder instructions are historical, not the current assignment. Prior
notes, baseline hashes and failures remain unchanged. User acceptance does not
certify every pacing, startup, AV or long-session technical gate below.

Main includes Galaxy Odyssey36 and the accepted original32/33/34 scenes.
Water Basin37 remains parked for audio/UI weaknesses; Experimental Lodestone
Field38, Stormglass Network39 and Folded Aurora40 remain outside Main. Their
existing support/assets and review paths are preserved. Prism Assembly, Digital
Bloom and Chromatic Memory remain off by default. Parked Water/Cymatics support,
its directly corresponding tests/note and necessary mixed Studio/Main hunks were
explicitly approved for the working-checkout dependency closure; no new Water
feature or Basin Main acceptance followed from that inclusion.

## Main inventory and current review routes

This is eligibility, not a fixed itinerary or frequency guarantee.

| Group | Eligible states |
| --- | --- |
| Organic / geometry / Planet Canvas | Membrane11, Root Blossoms12, Geometric Corridor2, Planet Canvas5 |
| Water | Sea7, Dyes8, Rain9, Waterfall10, Currents13 |
| Fire | Fire14, Molten15, Firescape17, Aftershock18 |
| Air | Windstreams19, Stormfront20, Vortex21, Citadel22 |
| Earth | Dunes24, Strata25, Crystal Cavern26 |
| Fog | Nebula28, Marsh29, Pressure30 |
| Original Plasma | Magnetic Bloom32, Arc Constellation33, Auroral Veil34 |
| Galaxy | Galaxy Odyssey36 |
| Fractal (newer local Main30) | Tidal Strata41, Recursive Atrium42, Honeycomb Garden43 |

- `run_zerawave.bat` or `run_live_visualizer.bat` without arguments opens the
  accepted player. Choose an exact output loopback or input endpoint. Explicit
  arguments to the latter still use the diagnostic live_visual_test.py runner.
- `run_development_studio.bat` opens the existing Studio; Main blend, Live system
  audio, Start preview uses the same canonical `renderer.py::LIVE_FORMS` roster.
  Studio Test track is silent decoded replay; Synthetic preview is synthetic.
- [review-session-blend.json](work/robert-refinement-02/review-session-blend.json)
  has empty selection and no forced pair/seed, so it uses ordinary Main. Its
  explicit60-second replay limit can end before Galaxy is selected or completes;
  saved held-Galaxy seed controls are parked for Main.
- Galaxy Main entry/return starts the existing74-second full route and becomes
  releasable at its route boundary. Existing compatible universal transitions,
  authored inhabitants, source pigments/manual overrides and fresh re-entry
  ordinal remain; normal Main is not pinned to Galaxy.

## Accepted player checkpoint and publication

The branded player panel, clean separate visual output, controls and queue are
implemented. The inline exact-source dropdown and quiet Refresh remain; no
dynamic default/fallback or extra retry dialog is introduced. Bounded capture
recovery preserves intent, current world/transition/queue and explicit Pause.
The project-owned SoundCard0.4.6 WASAPI close adapter confirms owning-thread
reference release before replacement; failed/unconfirmed cleanup retains the
existing full-player restart notice. It does not patch installed packages.

After the bounded safety review, Robert reported active BlackShark off ->
unavailable -> on + Refresh recovery without closing the runtime, repeated normal
Start/Stop, and **10/10 acceptance**. This is reported physical user acceptance;
unattended recovery, audio quality and additional device/Windows combinations
remain uncertified. Robert explicitly authorized the local commit and normal
GitHub push. The parent handles the two Pages updates after the builder reports
the exact committed hash and remote-main verification. No release was built.

The four-root reconciliation is complete. Its one-time ownership exception does
not remove standing Overseer ownership. The approved Prompter/Bob/sole-builder/
review/user-acceptance route remains; this publication starts no next phase.

### Current player controls and evidence

Use the [accepted player guide](docs/agent-notes/player-checkpoint-2026-10-03.md)
for Start/Stop/Pause/Resume, momentary Hold, compatible Bonk, queue and focused
shortcuts. Stop after output readiness stops listening and permits quiet settling;
explicit Pause freezes drawing/clocks. Resume uses fresh packets without an event
backlog. Hold preserves an arriving world; Bonk requests one compatible transition.
Queue edits take effect at a world boundary. Now-showing is panel-only.

Settings remain `%LOCALAPPDATA%/ZeraWave/settings.json`; only a successful exact
source identity is saved. Refresh alone sends no listening command. Select a
replacement explicitly when an endpoint is missing; there is no recording/upload
or per-app capture. On unconfirmed cleanup, follow the existing notice to close
the entire player and visual output, reopen, then reselect the source.

Historical builder notes/packs retain their original pre-acceptance status:
[interface](docs/agent-notes/player-interface-01.md),
[recovery](docs/agent-notes/player-capture-recovery.md),
[inline source](docs/agent-notes/player-inline-source.md), and
[final cleanup](docs/agent-notes/player-final-cleanup.md).
The final `work/player-interface-01/final-cleanup-delta/review-index.json` binds
source, exact delta and six passing offline commands. At publication those source
bytes are checked against the staged Git content with only newline normalization;
the final checks are reused, not rerun or relabeled as live certification.
No new GPU, native pacing, listening or long-session test is run for publication.
The original player pack retains its reproduced baseline Studio test failure at
line566 and unverified physical output shortcuts; no test was removed to hide it.

At that player checkpoint, README/PLAYER still retained older dirty Galaxy-status
paragraphs. The October 4 documentation pass reconciles their current-source
wording; frozen-portable history remains unchanged.

## Source-bound evidence and limitations to retain

No application, GPU, listening or performance test was rerun for checkpoint
publication. The following are existing visual worker evidence, not new certification:

- [Entry/projection handoff](docs/agent-notes/robert-refinement-02.md#latest-entryprojection-correction---final-narrow-source)
  and [final pack](work/robert-refinement-02/entry-projection-delta/review-index.json):
  default1280x720 and monitor-attached2560x1440 fullscreen **SURROGATE**, not a
  reproduction of Robert's unknown fullscreen action. Swap return is not scanout;
  power/thermal/background conditions were uncontrolled. Severe tested
  Cavern/Citadel/Magnetic entry/return stalls improved; no universal FPS guarantee.
- Native Aperture still had16/112 presentation intervals above50ms and
  GPU p99 56.58ms. Returning Molten retained three51–52ms intervals plus a151.27ms
  query-allocation interval about1.05s into hold. The strict all-pacing gate is
  incomplete. Checkpoint publication does not reopen optimization.
- Aftershock's prior7.4 review caveat remains. Robert accepted the current
  included checkpoint; no score was inflated or the scene silently removed.
- [Main lineup handoff](docs/agent-notes/main-lineup-01.md) and
  [final pack](work/main-lineup-01/review-index.json): RTX3070 Laptop640x360 actual
  GPU Main entry/full Galaxy route/exit and controlled re-entry passed; full
  held/Main Galaxy endpoint equality, manual colors and bounded clock/history
  behavior were checked. Accelerated elapsed steps and diagnostic seed6 prove
  reachability/lifecycle, not normal visit frequency or live listening.
- Earlier cold80–83s compilation and one immediate post-cold-ready responsiveness
  failure retain their original provenance. Later incidental125.69s and133.77s
  cold compile observations and warm native lifecycle passes do not establish a
  final cold-responsiveness certificate. Preserve failures separately from warm
  successes; no arbitrary timeout inflation or claimed cold-cost fix.
- Silent synthetic/decoded motion and sampled sequences are not continuous
  natural AV listening, scanout validation or multi-hour rendered variety/resource
  evidence. Resource bounds are not peak VRAM/RSS or minimum-device guarantees.
  Robert's artistic acceptance remains distinct from these technical limits.

Evidence packs/captures/audio under work/ remain local and ignored; they were
not distributed with the GitHub checkpoint. Older task notes preserve their
own date/status. Do not relabel them as the final source or current assignment.

## Project skills and validation status

The visual baseline commits
[zerawave-task-handoff](.agents/skills/zerawave-task-handoff/SKILL.md),
[zerawave-evidence-critique](.agents/skills/zerawave-evidence-critique/SKILL.md) and
[zerawave-matched-performance](.agents/skills/zerawave-matched-performance/SKILL.md).
Explicitly read the applicable file: the fresh delegated catalog did not
advertise them. The user reports sidebar visibility after refresh; that is not
verified delegated auto-loading, trigger or installed-runtime behavior.

Basic structure/frontmatter/name/description and local-reference checks passed
for the committed skills. The official validator was not run because PyYAML is
missing from the project environment (absence checked in the earlier
root-doc reconciliation). No dependency was installed. These limits do not grant dispatch/ownership
or override the current brief.

## Preservation and read next

Preserve unrelated dirty documents, research/brainstorm folders and the planning
proposal. Any future publication requires Robert's checkpoint approval and an
explicit reviewed manifest that accounts for the earlier dirty Main30 dependencies
as well as this performance delta. This documentation reconciliation changes no
application source, authored values, environment or release outputs.
The three historical color notes and separate startup-performance note remain
local pending an explicit inclusion decision.
Keep `work/releases/ZeraWave-preview-final.zip` at d4992d0 unchanged; future
portable/release work needs its own assigned output path and authorization.

- [ROADMAP.md](ROADMAP.md): published player/Studio/tuning checkpoints, current
  Main30/performance review and unresolved real-time/startup tradeoffs.
- [AGENTS.md](AGENTS.md): coordination, applicable skill loading and ownership.
- [ZERAWAVE_VISUAL_IDENTITY.md](ZERAWAVE_VISUAL_IDENTITY.md): creative/product direction.
- [DEVELOPMENT_STUDIO.md](DEVELOPMENT_STUDIO.md): current Main/Experimental controls, Audio Tuning and Mapping monitor.
- [TECHNIQUE_LIBRARY.md](TECHNIQUE_LIBRARY.md) and
  [maintenance contracts](docs/MAINTENANCE_CONTRACTS.md): reuse/preservation contracts.
