# Shared Media Library and Still-Image Layers — Increment 1

Implementation complete in `C:\ZeraWave`, ready for Robert's review. No commit,
push, worker/critic dispatch, installation or publication. Published HEAD remains
`fe1a7b74f791fbfcc1879798e5e944be50ae061f`. The supplied reference bindings matched
before editing. The task baseline, final hashes, exact task delta and evidence
index are in `work/media-library-increment1-20261007/`:

- `baseline.json`, including eight original task-file hashes and 236 preservation bindings.
- `source-identity.json`: final file SHA-256 values, preservation and validation scope.
- `task-only.diff`: task changes/new files against the preserved pre-task copies.
- `evidence-index.json`: individual artifacts, sizes and SHA-256 values, including failures.

The three unrelated modified notes, existing untracked research/image directories,
root planning documents, audio/DSP/analyzer modules, launcher and user layout were
preserved. No source reset or substitution. The legacy October 6 root checkpoint
does not describe this newer published baseline; no shared planning files were edited.
Robert accepted the refined Band Analyzer in the latest chat (“Love it much better”).
Earlier audio reliability acceptance remains separate from broader listening/timeline
review and this media increment's pending acceptance.

## Visible result and ownership

File → Import media… and View → Media Library / Image Layers expose two existing-style
docks, hidden initially; all previous docks retain their areas. The library has Images,
Video and Audio groups, search, display-name editing, status, validation cancellation,
Refresh, Relink, Remove and explicit use actions. Original paths stay in place. Stable
IDs and normalized paths prevent duplicate imports; failed relinking leaves the old
record, successful relinking retains identity/name/transforms. Removing never deletes
the source or stops independently owned file audio. Browsing/importing starts nothing.

PNG/JPEG use installed Qt decoding, real orientation/alpha handling and sRGB conversion.
WAV/MP3 use the existing Decoder for header/first-block validation; Use as audio source
uses the sole AudioOwner command path without autoplay or reopening the same source.
Video stores file-level references and explicitly says playback unavailable; no codec,
duration, thumbnail or playback is implemented.

Two foreground slots support assignment, visibility, order, opacity, Fit/Fill, X/Y,
scale and transform reset. Main image-only and world-plus-images share the existing
renderer/context/lifecycle. Image-only covers the completed world; the underlying
world still draws and advances histories. Overlays occur after world/history passes.
Static textures are reused for transform edits, hidden layers release textures, and
atomic upload failures retain the whole last working composition. Run/destination,
session/revision and async generation guards reject obsolete edits/results.
Legacy Experimental image routes are explicitly rejected before start.

Source pixels supply image colors: no new tint pigments, filters, Envelopers or musical
image effects. Tagged sources convert to sRGB; untagged sources assume sRGB. RGBA8
premultiplied filtering/blending uses existing display-encoded RGB, not a new linear-light
pipeline. World authored colors, audio tuning and clocks are unchanged.

Library registry version 1 is separate from artistic session version 4 and Qt layout.
Versions 1–3 still load. Sessions retain assigned image refs/transforms; opening starts
neither audio nor renderer and introduces no persisted runtime volume/mute/raw/source
state. Library JSON is excluded from Saved sessions and rejected as an artistic file.
Explicit relink provenance (last eight paths) allows an old saved reference to follow
the same authorized ID; unknown identity/path conflicts fail explicitly.

Bounds: 128 references, 16 pending validations, 8 MiB registry input, 2 MiB GUI protocol
line, one registry worker, and one renderer decode worker with a latest-request mailbox.
Images: 128 MiB compressed, 8,388,608 decoded pixels, 8192 per side and actual device
texture limit; oversized inputs are rejected without silent scaling. Two resident
textures ≤64 MiB; atomic replacement old/new ≤128 MiB. One result ≤64 MiB RGBA staging,
plus Qt reader/conversion intermediates (reader limit 64 MiB/image). These are bounded
counts/payloads, not total process-RSS claims. No persistent CPU image cache/per-frame
file reads. Native file/decode calls cannot be interrupted midway; cancellation discards
their late results, orderly close waits two seconds and daemon workers cannot hold
process exit. Blocked native I/O and hardware allocation limits beyond the exercised
fixtures remain unobserved.

## Executed checks and evidence

All final scoped checks passed:

- `media_registry_test.py`: real JPEG EXIF orientation, premultiplied transparent PNG,
  invalid/oversized input rejection, async import/duplicate/name/missing/relink, explicit
  relink provenance versus unapproved substitution, obsolete completion after removal,
  cancellation, original file preservation, persistence, session v1–v4 compatibility,
  library/session separation and maximum Unicode reference/IPC payloads. No streams/GL.
- `image_layers_test.py`: real target GPU alpha/order, opacity/Fit/Fill/position/scale,
  static upload reuse, image-only, exact disabled composer output preservation,
  injected allocation failure preserving composition, obsolete revisions/sessions,
  late native completion cancellation, target resize/viewport and thread/GL release.
  Synthetic 32×24/43×17 framebuffer contracts; no presentation/listening.
- `studio_media_test.py`: actual owned Qt File import, search/name draft, native context
  layer assignment, ordering/reset, all control bindings, legacy rejection, unchanged
  previous dock areas; real Main two-texture presentation, missing resident edits,
  relink, v4 save/reopen, Stop/Start fresh owned renderer and removal/release. Final
  metadata/IPC/storage separation edits rechecked with `--controls-only`, embedding
  final source hashes. No capture/output in this check.
- Existing `studio_transport_test.py`, `waveform_drive_test.py`,
  `audio_drive_mode_test.py`, `band_analyzer_test.py`, `band_analyzer_view_test.py`,
  `preview_playback_test.py` all passed their focused mocked/synthetic/decoder/pipe
  checks. Existing `studio_test.py --organization-test` passed its assertions but
  emitted a Tk callback TypeError because mocked telemetry reached the unchanged
  `refresh_playback_controls`; warning retained, not characterized as a clean run.
- Syntax checks on all 13 task Python files, exact task-diff review, preservation
  hashes and `git diff --check` (line-ending notices only).

`qt-smoke-run2/qt-smoke.json` records the brief native Audio File check with the verified
`C:\ZeraWave\test_audio\Balloon.mp3`, SHA-256
`94a2a26f01db9854bfc8ee784fc6834ac4799c0960daf180839e12de85fb5754`.
It imported JPEG/PNG/MP3/file-only video without autoplay, used MP3 via the same owner,
retained same-source identity, then exercised seek, 8% output volume, mute while PCM
RMS/playhead continued, 2× and Play→1×, Pause/Stop alongside Main Roots. Native backend
accepted output; no heard-output claim. Visual Pause/Resume was checked after audio Stop.
Fixed 1280×720 internal pixels survived presentation resizing; Native followed physical
framebuffer pixels with the same context/program/parameters and continuing visual clocks.

`qt-controls-latest.txt` points to the successful full controls/restart run;
`qt-controls-final-only.txt` points to final-source control validation. Captures were
visually inspected: original JPEG aspect fit and PNG alpha were retained, header/docks
remained recognizable, the library actions fit the existing narrow dock. Test fixtures
are generated technical images, not artistic acceptance material. Full Qt/GPU smoke
did not embed every source hash at run time; later changes were metadata/IPC limits,
registry/session separation and test bookkeeping. Renderer/compositor drawing remained
unchanged; final source binding and this limit are recorded in the manifest.

## Resource attribution

`layer-cost.json` + `layer_cost.py`: RTX 3070 Laptop GPU, standalone physical RGBA8
1944×986 target/viewport/internal pixels, Full/scale 1. Fixed clear background, same
960×540 JPEG and 512×512 PNG, Fill and opacity .65/.8, no audio/history/clock, AB then BA,
12 warm draws and 48 GPU plus 48 separate CPU-submit samples per arm/repeat. No window,
swap, vsync, scanout, readback or world drawing in these distributions; query waits
and end-of-arm finish excluded. Desktop/power/thermal load not controlled.

| Arm | GPU mean ms, repeats 1 / 2 | GPU p95 ms | GPU maximum ms | Resident texture bytes |
| --- | --- | --- | --- | --- |
| Disabled, clear only | .00226 / .00226 | .00307 / .00307 | .00410 / .00307 | 0 |
| Two image passes + same clear | .03891 / .03872 | .04060 / .04163 | .04096 / .04301 | 3,122,176 |

Added isolated GPU cost ≈.0366/.0365 ms; CPU submit ≈.0257/.0253 ms enabled versus
.00242/.00176 ms disabled. No sampled >5 ms component stalls. Static decode/upload
excluded and resource counts recorded separately. This is attribution of the added
passes, not a whole-engine optimization or FPS guarantee. The compositor's recorded
hash matches final source; registry bound-only changes are separately identified.

Ordinary, uninstrumented Qt Main Roots quiet/no-playing-audio with two textures used
1280×720 internal pixels, 937×601 output/framebuffer and scale 1. Its short rolling
120-interval telemetry sample showed 60.09 swap returns/s, mean 16.64 ms; this is a
different workload from the offscreen cost check and does not establish scanout,
all-world performance or a gain. Image-only still pays underlying world cost.

## Retained failures and limits

The first registry EXIF fixture was malformed and corrected; initial GPU alpha exposed
a real context-wrapper blend setter problem, fixed by setting the owned raw GL context.
A later fixture rounding/coordinates assertion was corrected against actual baseline
bytes. The initial Qt startup-dimensions assertion was premature and replaced by an
explicit fixed-resolution check. Early context-menu checks had collapsed/settling-row
issues; native QMenu ignored class monkeypatching in one attempt, replaced by timed
actual Qt action selection. Owned interrupted attempts/traces were retained; only their
verified test processes were stopped. An early restart harness issued Start while its
Stop operation was pending; it now waits for operation completion. One full controls
attempt hit Windows access-denied at the existing session atomic rename; retained
without changing that storage path. The successful repeat used no save retries.

No dependency installation, new video backend, exhaustive scene/benchmark matrix,
physical keyboard/knobs, multi-DPI/monitor exercise, long-session soak, natural-live
capture/listening, HDR/wide-gamut display calibration or extreme-size real-device OOM
test. Native output acceptance is not listening acceptance; short steady Roots checks
do not resolve Robert's historical full-size/BONK workload. Existing audio/timeline
scan pitch/latency and resource telemetry limitations still apply.

## Robert's review and route

Launch `run_zerawave_studio.vbs`. File → Import media…: opaque JPEG, transparent PNG,
WAV/MP3 and a video reference. Browse/rename/search and confirm no playback starts.
Use Audio, then existing waveform seek/scans/Play/Pause/Stop, volume/mute and Raw drive;
inspect unchanged Band Analyzer. Use Layer 1/2, Start a compatible Main, compare Image
only / World + images, order/opacity/Fit/Fill/position/scale/reset and hide/remove.
Save/reopen, Refresh a missing source, Relink, resize, Stop/Start; inspect the video's
unavailable label. Source files stay untouched. Robert owns acceptance; Prompter/Bob
prepare/approve any later review. No automatic critic or next-stage dispatch.

Proposed checkpoint update for Bob/Overseer: Increment 1 implemented in the current
uncommitted root checkout with the attached scoped evidence and stated limits; ready
for Robert review. Video remains references-only. No root-plan update was made here.
