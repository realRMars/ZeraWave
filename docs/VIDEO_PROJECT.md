# Video projects in ZeraWave Studio

Implementation-owned contract and agent reference. The connected editor stage is
governed by [ROADMAP](../ROADMAP.md); this file records implemented behavior.

## Current increment

Increment A supplies the versioned project, scoped bin, shared Qt/API authority,
named Undo/Redo and protected persistence. Its independent review passed 9.0/10.
Increment B adds a frame timeline, shared rational evaluation, bounded source
preparation and spatial preview through the existing composition renderer.
B and C received independent9.0/10 progression approval. C connects bounded
multitrack preparation to the existing single AudioOwner and editable volume
controls. D implements editable captions/titles/styles and timed graphics through
the existing compositor; D received independent9.0/10 progression approval.
E implements revision-pinned MP4/H264/AAC Export Video and received independent
9.0/10 progression approval. F supplies the full protected editable Episode04 and its actual Qt correction,
exact history, managed Save/normal-close/reopen, full playback and reopened-revision
H264/AAC export evidence. Source-bound results and remaining timing/listening
limits are recorded in the video-editor task note and final packet. Independent
Reviewer verdict and Robert's final acceptance are separate records.

The existing global Media Library, Composition layer sessions, artistic controls
and independent live clocks remain available. A video project is a separate
document domain in the **same existing Studio owner**, not a second editor.

## Using the foundation

1. File → New video project or Open video project opens the Video Project dock.
2. Add audio/video/graphics tracks. Import sources into **Project bin**; the
   existing global Library is not copied into that bin.
3. Place a selected source, then select its clip to move, trim, split, remove,
   unlink or edit its volume/fades. Frame intervals end exclusively.
4. Add/correct caption text and timing on a graphics track. Normal text entry and
   local text Undo belong to the dialog; project Undo/Redo belongs to this dock.
5. Save project / Save As writes `.zwv` plus an adjacent managed-media folder.
   An accepted edit remains unsaved until the requested revision is durable.

Volume is linear gain (1 = unity), not percentage of a normalized waveform.
Left/right clip trimming changes source time while preserving the original
fade/envelope origin. Gain-only edits do not restart existing fades. Linked
operations retain relative timing; unlinking is explicit. A rejected operation
does not alter the previous accepted document. Its last unapplied request is
retained in the workspace, bounded to one command, without automatic resubmission.
The current UI reports the error; re-entering/rebasing requires deliberate review.

Open resets the current in-memory history, as existing layer-session opening
does. The saved editable document and revision persist; historical Undo stacks
are not serialized. Subsequent edits have normal Undo/Redo in the new instance.

## Agent transport

Launch the existing Studio, then use **Copy agent endpoint** in Video Project.
Each control owner publishes its own authenticated localhost endpoint in its
log directory. Do not guess another instance's endpoint or expose its token.
The endpoint disappears only after its owned server/readers exit normally.

The installed project environment runs the interface:

```powershell
& C:\ZeraWave\.venv\Scripts\python.exe -B C:\ZeraWave\app\visuals\project_cli.py --endpoint <endpoint.json>
& C:\ZeraWave\.venv\Scripts\python.exe -B C:\ZeraWave\app\visuals\project_cli.py --endpoint <endpoint.json> --request <exact-request.json>
& C:\ZeraWave\.venv\Scripts\python.exe -B C:\ZeraWave\app\visuals\project_cli.py --endpoint <endpoint.json> --status <operation-id>
```

Python callers use `project_api.call(endpoint, request)` or
`project_cli.request(endpoint, request, wait=True, timeout=120)`. They submit to
the same control-thread service as Qt. They never mutate a project file to edit
the running owner. The request file is only an immutable command input.

Read `state` immediately before **each new deliberate command**. Capture
`epoch`, `revision`, `project_id` and `command_revision` as `expected_epoch`,
`expected_revision`, `expected_project` and `expected_command`. Supply a fresh
32-character lowercase UUID hex `operation_id`. For example:

```python
import sys, uuid
sys.path.insert(0, r'C:\ZeraWave\app\visuals')
from project_api import call
from project_cli import request

s = call(endpoint, {'op': 'state'})['state']
command = dict(op='batch', operation_id=uuid.uuid4().hex,
    expected_epoch=s['epoch'], expected_revision=s['revision'],
    expected_project=s['project_id'], expected_command=s['command_revision'],
    label='Correct caption', changes=[
        dict(op='caption.edit', id=caption_id,
             values=dict(text='Corrected editable caption'))])
result = request(endpoint, command)
```

A lost reply must reconcile/retry that **exact request and ID**. Do not generate
a new ID or silently rebase it. A duplicate retained request returns its original
outcome; different contents with the same ID fail `operation_conflict`. Another
command can change `command_revision` without changing document pixels/recipes
(for example a pinned save). This prevents an expired save request from executing
twice after its detailed receipt retires. Retired/unknown results return
`outcome_unknown`; inspect current document/output, never assume nonacceptance.

### Commands

`state`, `operation_status(operation_id)` and `cancel(operation_id)` query or
cancel work without creating artwork/history. All other requests need the captured
binding and an operation ID. Optional policy flags are real JSON booleans.

| Command | Fields and behavior |
|---|---|
| `new` | `name`, optional `settings`, `project_id`, explicit `base_directory`, `discard`; dirty replacement requires deliberate discard |
| `open` | `path`, optional `discard`; asynchronous verified preparation before atomic owner installation |
| `batch` | `label` ≤256 characters, `changes` (1–128); one atomic named history operation |
| `undo` / `redo` | Exact document/media-availability restoration, new accepted document revision |
| `transport` | `action` = seek/play/pause/stop, integer `frame` for seek; ephemeral clock ownership, no document revision/history operation |
| `save` | `path` for Save As, or current path; `portable=true` default; `allow_missing=false` default |
| `close` | Optional `discard`; pending preparations/saves prevent project replacement |

Within a batch:

| Edit | Required fields and supported options |
|---|---|
| `project.rename` / `project.settings` | `name` / `values`; settings: width, height, rational fps, sample_rate=48000, RGB background |
| `project.provenance` / `project.protect` | Structured `values` / explicit absolute `paths`; recorded production outputs can be protected without importing them |
| `media.add` | `name`, `kind` (Video/Audio/Image), `location`; optional `id`, expected `sha256`, `provenance`; owner prepares actual hash/metadata |
| `media.relink` | `id`, matching `kind`, `location`, recorded `sha256`; `accept_changed=true` explicitly permits different content; original paths remain protected |
| Missing placeholder | `media.add` with `placeholder=true`, expected `sha256`, explicit location and optional metadata; never guessed by basename |
| `track.add` / `track.audio` | `kind` (video/audio/graphics), optional id/name/order/audio / `id`, partial audio `values` |
| `clip.add` | `asset`, `track`, integer `start`, positive `duration`; optional id/name/source_in/rate/audio/layout/link_id/pad_end/provenance |
| `clip.move` | `id`, new `start`, optional compatible `track`; linked members move by the same delta, retaining other members' tracks |
| `clip.trim` | `id`, optional new `start` / exclusive `end`; adjusts linked source ranges together |
| `clip.split` | `id`, interior absolute project frame `at`; splits every linked member, deterministic new IDs and right-hand link group |
| `clip.remove` / `clip.unlink` | `id`; linked behavior defaults true; explicitly pass `linked=false` for just the selected member |
| `clip.audio` / `clip.layout` | `id`, partial `values`; audio: gain/mute/fade_in/fade_out/envelope; layout: bounds/opacity/rotation/brightness/fit/masks/blend |
| `caption.add` / `graphic.add` | graphics `track`, `start`, `duration`, `text`; optional id/style/order/provenance/dynamic/range_start/range_end |
| `caption.edit` / `graphic.edit` | `id`, partial text/timing/style/order/dynamic values; stable IDs, track and provenance cannot be replaced |
| `caption.remove` / `graphic.remove` | `id` |
| `export.settings` | `values`: initial MP4/H264/AAC/crf settings; persisted MP4/H264/AAC/crf defaults; E implements actual export below |

Source times/rates use `[numerator, denominator]`, not incremental floating point.
Clip gain/mute and source recipes are independent of current tool/global audio
settings. Audio envelopes are increasing `[local_frame, linear_gain]` points.
Split/trim retains their original coordinate window; deliberately editing a fade
or envelope restarts that curve on the edited clip. `pad_end='silence'` explicitly
allows an audio clip's known end tail; it does not recover missing speech.
Layout bounds are normalized `[x,y,width,height]`; fit is Stretch/Fit/Fill;
blend is Normal/Multiply/Screen/Add/Difference. Text uses Segoe UI by default;
colors use RGB or Qt `#AARRGGBB`, with explicit bounds/padding/alignment/weight.
Unknown nested recipe fields or versions fail rather than dropping information.

### Outcomes and limits

`preparing` is source/open preparation, **not an accepted edit**. `accepted` is an
owner-installed revision, **not necessarily durable**. `saving` pins the requested
revision and dependencies. `durable` identifies the completed requested revision,
path and file SHA-256. Later edits remain unsaved. `rejected` changes nothing;
`failed` retains accepted work and prior good output. Cancel cannot revoke an
already durable result. CLI exit 0 means the reported success/receipt, 2 a known
invalid/conflicting request, 75 transport/busy/unknown outcome. `--no-wait` can
exit 0 for a preparing/saving receipt; read its status and reconcile it.

The socket has four client slots and ≤512 KiB requests/≤2 MiB replies. The existing
owner queue and GUI command boundary retain their separate limits. Project
preparation has two workers and at most sixteen pinned preparations/saves. No
worker mutates authoring state or creates a GL/audio-output context.

The format's independent ceilings are 512 KiB serialized metadata, 1024 bin
assets, 64 tracks, 2048 clip instances, 4096 captions, 512 graphics, 128 edits per
batch and 24 hours. Competing byte limits can be reached first. Initial simultaneous
recipe ceilings are four video instances (existing decoder-lane ceiling), thirty-two
visual recipes and sixteen audio recipes. Those last bounds are admission policy,
not qualification of all combinations; evaluator/device qualification follows
in the corresponding increments. Project dimensions support ≤8,388,608 pixels,
16–8192 per axis, rational 1–120 FPS and 48 kHz. Original sources are not downsampled
by the document model. No higher legacy layer/library capacity is implied.

History charges exact serialized before/after documents **and media availability**
to 64 MiB; it is not physical process-RAM accounting. Existing accepted history
is not evicted to admit more work. Result retention is 1024 detailed operations;
the GUI projection shows sixty-four compact summaries. The GUI can query its
retained operation ID if a summary moves out of that projection.

## Persistence and recovery

Portable Save verifies source SHA-256, copies bytes to `<project>.media/<hash>.<ext>`,
flushes copies/metadata, then atomically replaces the requested `.zwv`. Existing
dependencies are reused only with matching content. Relative paths must remain
inside the explicitly opened project folder; moved projects do not search the
Library or a same-named file elsewhere. Original import/relink paths, current
sources, protected paths and existing aliases are protected from overwrite.
`portable=false` is an explicit **verified external-reference** fallback, not an
immutable managed copy; later external changes are Missing/Changed input errors.

Missing media may be saved deliberately with `allow_missing=true`; this secures
editable reference metadata and clearly reports unresolved dependencies. It does
not pretend missing content is rendered/exportable. Partial managed-copy temps
are retained as diagnostic evidence after failure. Only this save's unpublished
metadata temp is cleaned, and cleanup cannot obscure the original failure.

On a failed save, keep Studio open, resolve the input/disk error and Save As to a
new destination. There is no automatic duplicate submission. Normal Studio close
waits for project jobs or prompts to Save/Discard/Cancel; failure keeps the same
owner open. Newer edits received during a close decision stop that close. Project
queries/cancellation remain available while owner writes/readers drain; new edits
are rejected through actual resource release.

Owner-process death/forced termination does not have a new recovery guarantee.
Never substitute terminating the owner for a failed close or pending save.

## Evidence

The implementation's actual tests, failed runs, source identities and review
status belong in [task results](agent-notes/video-editor-20261013.md). Offscreen
Qt event tests are real widget/owner paths with synthetic input, not physical
desktop, GPU preview, listening, whole-stage acceptance or Robert's acceptance.


## Increment-A independent-review corrections

Studio close carries the exact project/epoch/document/command binding captured
by its close decision to the authoritative thread. That guard runs before any
cancel/drain/discard. Artwork discard and video-project discard are distinct
choices; neither silently grants the other. A changed binding rejects close and
keeps the same owner/newer accepted work open. Convenience ControlClient.close
reads fresh state and binds its one new close request; video discard requires
its separate `project_mode='discard'`. It never rebases a previous GUI decision.

Malformed batch containers/members/nested values are rejected before preparation
classification. A recorded receipt can remain preparing/saving only while a real
job owns it. Unexpected handler failures are logged and terminalized; an already
installed edit stays accepted with an uncertain-result warning, never falsely
called rejected. See the focused actual-owner/API/Qt review regressions.


## Timeline and preview (increment B)

The Video Project dock contains a preview and a resizable timeline above its
scoped bin/recipe lists. Select a clip body and drag to move; drag either edge to
trim. Release submits one named owner transaction. The gesture ghost is not an
accepted edit. A stale/intervening edit cancels or explicitly rejects the gesture.
Linked members keep relative/source timing; moving to a compatible picture track
changes that picture's track, retaining its linked audio track. Text items keep
their graphics track. Edge snapping is optional; placement always resolves to an
integer frame. Precise Move/Trim/Split dialogs remain available.

Use Zoom +/− or Ctrl+wheel for timeline scale and its scrollbars for tracks/time.
Click the ruler/gap or enter Timeline frame to seek. With timeline focus: arrows
step one project frame, S splits a selected clip at the playhead, Delete removes
its linked group, Escape cancels a gesture, Space plays/pauses, Ctrl+Z/Y restores
owner history. Text fields and modals retain typing/local Undo. Layout edits
expose normalized bounds, Fit/Fill/Stretch, opacity, rotation, RGB brightness and
existing blend modes through the same owner recipes. Existing Composition
painting, layer gestures and live-world shortcuts remain scoped to their panes.

Intervals are [start, start+duration); project end is the largest exclusive end
among clips/text recipes. Source time is source_in + (frame-start)/rational_fps
times rational_rate. Absolute sample mapping rounds nearest with halves upward.
Video PTS lookup adds the stream's actual start timestamp and chooses its
preceding VFR/CFR frame; imported duration excludes that start timestamp.
Explicit gaps/end show background. There is no accumulation of float frame steps.

The owner exposes `transport` in API state and a compact fast GUI clock message;
it does not rebuild/historize the document each playback frame. A monotonic
nanosecond clock evaluates absolute rational frame positions. Play/seek/pause
explicitly own timeline evaluation; Stop releases ownership and resumes the
retained legacy layer clocks without resetting their authored media settings.
The B preview is silent. C owns the later device/mixer connection; this clock
is not measured audible position and procedural worlds are not made seekable.

One codec worker retains four deliberate decoder clocks, one active/latest
pending demand, 96 MiB shared decoded planes, and 128 MiB native RGBA/conversion
admission. Equal source clocks can share a window; different offsets/rates need
distinct windows. Active snapshots plus conservative largest conversion scratch
must fit the byte limit, which can reject a combination before its count limit.
Static cache retains only the active set; source verification retains 64 stamps.
Renderer readers explicitly take/release immutable snapshots. New seeks/revisions
cancel obsolete work; they clear stale presentation while preparing. During play,
one preparation completes before the latest current frame is requested, with
observed preparation/presentation timing separately recorded. B does not claim
every realtime preview frame reaches scanout or general high-rate qualification.

The context owner uploads native prepared RGBA and uses existing ImageLayers
transforms/crop/alpha/masks/blends; RGB brightness defaults to 1 for all legacy
callers. Project output renders at authored native dimensions, then fits its Qt
preview without changing document/source pixels. GPU replacement remains bounded
to 256 MiB textures and the existing composition-target budget. The supported CPU
route adapts the same recipes to existing Qt CPU projection. Its filtered phase
can differ from the GPU compositor; record comparisons rather than claim universal
byte equality. Masks use the existing eight-mask/128-point, noncrossing source-UV
contract; unsupported recipes fail before acceptance, never silently lose masks.

Source hash/stat changes, missing inputs, resource or decode failures report a
failed requested preview while retaining the accepted editable document. Correct
the source/resource issue and seek/relink deliberately; there is no automatic
failed-command resubmission. Normal Studio close observes the actual media worker
and owned compositor cleanup. Counts/byte admission are not total process RAM.


### Pending GPU consumption correction — B review R1/R2

Each queued GPU snapshot pins its own immutable request tuple. The actual paint
callback checks that tuple against the current project ID/document, epoch,
revision and seek/transport generation before drawing or publishing presentation.
Obsolete readers retire once; a newer request/binding/status is preserved and
preparation resumes when its prior reader has gone. Retained redraw also checks
the live generation. Same-generation playback may retain the preceding frame
while its latest demand prepares; this bounded lag remains distinct from an
obsolete seek/replacement. Actual preparation/render failures retain the accepted
document and recover through a deliberate newer seek after resolving the issue.

Timeline gesture cancellation explicitly releases only its own Qt capture on
revision invalidation, replacement, close, Escape, focus/deactivation, hide and
destruction. Cancellation never submits an edit. Another widget's grab is left
alone. Normal workspace shutdown calls this cleanup before retiring preview work.


## Connected project audio (increment C)

Timeline Play explicitly leases the existing AudioOwner's output. It parks the
previous Device Listening/Audio File source and releases its prior output queue;
it creates no second device owner. Pause/seek flush obsolete native output before
installing the new binding; Stop/project close restores the retained legacy source
and settings. A paused ruler seek before the first Play leaves legacy listening
alone. A separate legacy Experimental renderer cannot race project output; shared
Main still receives the same AudioOwner PCM. Captured input is never replayed.

Use Clips or Tracks → Volume for gain/mute/fades and the editable envelope table.
Clip points use local frames; track points use project frames. Points are strictly
increasing `[frame, linear_gain]` pairs and interpolate linearly. Gains multiply;
mute is exact silence. Original clip fade/envelope windows survive trim/split;
editing a curve deliberately restarts its coordinate window on the edited clip.
An unchanged dialog preserves full authored gain precision and creates no edit.
The existing output volume/mute remains playback-only; the raw authored project
mix continues to analysis, and these playback controls do not alter export recipes.
Legacy transport/source controls are parked while the timeline owns audio.

The shared evaluator maps absolute project samples to the same rational source
times used by spatial preview/export. Canonical audio is 48kHz stereo, prepared
in1–2048 sample blocks. PyAV codecs/resampling use actual mono/stereo layouts;
mono is duplicated after resampling without implicit3dB attenuation. Source-game
audio follows its linked clip's placement/trim/rate. Combined sources align audio
PTS to the video stream origin; real leading gaps remain silence. Native packet
PTS quantization within one declared source time-base tick continues exact decoded
sample counts instead of inventing holes/overlaps. Larger gaps remain explicit.
Random seeks in coarse-time-base media are limited by that timestamp precision.
The existing SoundFile/PCM path remains an explicitly tested audio-file fallback;
video audio needs installed PyAV. Supported actual channels are mono/stereo and
source rates8–192kHz; arbitrary multichannel downmix is not silently invented.

One preparation worker retains four ready PCM blocks, one latest configuration,
sixteen deliberate active source clocks, a shared32MiB canonical cache/scratch
limit and64 verified source stamps. Native conversions reserve shared cache bytes
before allocation. Larger native frames,512frame/2second decode work and positive
rate1/16–16 bounds remain explicit. These are component bounds, not total RAM or
all-combination qualification. Muted/obsolete runtime readers retire without
disposing of accepted documents, source references, history or recovery state.

Preparing PCM is not device submission or audible progress. Runtime reports
requested/applied binding, transition pending, prepared cursor/blocks/bytes,
submitted sample, observed padding, source errors and preparation/output timing.
The timeline uses submitted-minus-observed-padding as a playback estimate, with
exact rational/nearest sample boundaries. Correlated audible device position is
unavailable; this estimate is not measured speaker latency or scanout. Initial
preparation and underflow hold progress rather than silently skip source samples.
Native output occupancy waits are pacing, not pure DSP cost.

Source hash/decode/resource failures keep the accepted project and remain visible
until a deliberate new Play/seek or source correction. No automatic uncertain
resubmission occurs. Native release uncertainty blocks replacement and remains
reported even when the worker exits; secure accepted work before any separately
requested recovery. Normal close observes preparation/audio/server/reader exit.

`ZERAWAVE_PROJECT_AUDIO_OUTPUT=discard-test` is an explicit isolated-test diagnostic
sink with NO device/output/listening evidence. Default Studio uses the existing
WASAPI FrameOutput. The controlled sink and injected delays supplement the bounded
real UI/device checks, not replace them. Full Episode04 listening, complete words,
whole-episode playback/sync/export and final owner acceptance remain later F work.


### Atomic audio outcome reconciliation

Every report atomically retains latest requested serial/binding alongside applied
and last-submitted binding/sample. An old native output completion or failure
cannot clear a newer seek/Pause/Stop pending request. Reconcile that current serial
before declaring it applied/failed. Native release uncertainty retains original
and release errors, blocks replacement and never means success merely because
workers exited. Audio telemetry remains separate from accepted/durable document
revision and estimated output position remains separate from audible position.


## Editable captions, titles and timed graphics (increment D)

Captions → Import SRT prepares a bounded UTF-8 SubRip source on the existing
owner's preparation pool. Agent `import_captions` uses `path`, selected graphics
`track` and the same expected bindings/operation ID. Cues keep source index/hash/
timestamps/provenance and deterministic IDs. Start and exclusive end map with
ceil(time × FPS): a cue is present exactly on its output frame grid. Subframe
cues with no output frame fail explicitly. Timing is imported metadata, not
verified auditory word alignment. Inputs are bounded to2MiB actual reads and4096
cues/project512KiB admission. Large imports apply internal validated128-edit
chunks before one atomic history commit; malformed/stale/cancelled imports keep
the prior document. Imported recipes reopen without the original SRT; its source
identity/protection remains provenance. No transcription or writing system exists.

Captions and Titles / graphics offer text/timing edits and Style / placement.
Style includes requested font family, native-pixel size, weight/alignment, RGB or
Qt ARGB colors, bounds, opacity, padding, independent horizontal/vertical padding,
line spacing (0 = font metrics), rounded backplate and stroke. Hexadecimal colors
are #RRGGBB or #AARRGGBB, matching the existing Qt defaults. An untouched style
dialog preserves saved precision and adds no history operation. Text Undo inside
input fields remains local; project Undo belongs to the workspace. Unknown styles
fail rather than being dropped. Older explicit bounds/styles remain unchanged;
new default caption bounds allow two readable native27px lines at1280×720.

Static text, counters and progress stay editable recipes. Counter templates allow
{elapsed}, {duration} and {frame}, driven by saved frame ranges and rational FPS.
Progress uses that same range. Neither runtime updates nor glyph caches create
document/history edits. Images/cards remain source artwork; place/trim/Layout
exposes their own sizing/alpha/order. Flat PNGs are retained, not presented as
hidden layered designs. Track order and within-track text order compose through
the existing ImageLayers/Qt-reference transforms, alpha and blend behavior.

The composition/context owner materializes Qt-native glyphs into premultiplied
RGBA at authored dimensions. The same adapter is used for preview and later
export. Shared text cache plus largest preparation scratch is64MiB,128cache
entries,8192axis/8-megapixel per-text bounds. Media caches, GPU textures/output,
font-engine allocations, history and process RAM remain separate. Pressure and
text overflow report failure, retain accepted recipes and never shrink pixels or
drop characters. Deliberate correction/seek can resume. Obsolete runtime pixels
retire without discarding history or source artwork; close releases owned caches.

Windows Qt primary-family substitution is reported in preview diagnostics.
Per-glyph fallback names are not enumerated: QRawFont.familyName diagnostics
reproduced a native access violation and were removed. Unicode shaping/rendering
continues through Qt; inspect representative glyphs on the target machine.
Saved font families are requested recipes, not embedded/licensed font files.

Paused ruler seeks before first Play now reconcile as Paused without claiming or
replacing legacy output. Requested/applied status clears pending on that actual
no-op boundary; requested sample remains separate from submitted/audio progress.
Legacy source/decoder/playing state stays intact until explicit project Play.


### Explicit paragraphs and offscreen font preparation

Saved CRLF/CR/LF and paragraph separators retain exact document text. Layout maps
these breaks to Qt line separators and formats the resulting UTF16 text; blank
and trailing lines count for bounds/overflow. Missing fonts/glyphs report failure
rather than treating square placeholders as readable captions. Windows offscreen
rendering may start with no Qt fonts; it reads the existing font registry and
registers installed files only when a family is needed, capped at64files with
hashes. This installs nothing and changes no registry/system settings. Native
window font discovery remains Qt-owned. Required printable codepoint coverage
uses safe metrics; all-font/language/combining-sequence qualification is unclaimed.
Cold font registration/shaping and opaque font allocations are separate costs.


## Moving-video export and persistence (increment E)

Save project/Save As remains version1 `.zwv` plus managed hashed source/raster
dependencies. It preserves the requested revision and all editable fields; Open
reconstructs recipes and source identities. Existing layer-session Save stays
separate. A successful Export does not mark an unsaved project saved.

File → Export Video or the dock's Export Video button captures the current
binding. It shows native project dimensions and rational FPS plus deliberate
H264 CRF0–51 (default18; lower means higher quality). Project settings changes
width/height/FPS through one history command. Frame counts remain fixed: changing
FPS changes duration/source sampling and invalid ranges reject entirely. No
implicit resizing or source-sample reduction; yuv420p needs even dimensions.

API `export` requires the ordinary operation ID/expected binding, `path` ending
.mp4 and optional `crf`; status=`exporting` is pinned work, `exported` means
validated/fsynced/atomically replaced output and actual worker exit. Query/cancel
the SAME ID. Only one export is admitted, within the16prep/save job bound. Later
edits/history/Save may continue; New/Open/Close waits for true retirement. Qt's
Cancel video export addresses that ID separately from preparation cancellation.
The CLI waits for export and returns75 for an uncertain outcome; never
automatically duplicate unknown work. Missing/changed sources or failed codecs,
resources/writes/cancel retain accepted project work and prior good output.
An `export_outcome_unknown` explicitly requires destination/diagnostic inspection
before repeating; no claim that a potentially completed file was rejected.

One disposable process owns its native GL context, shared ProjectSurface/text,
existing Media preparation and Mixer. It has no device output, world clock or
divergent FFmpeg compositor. Its standard input is explicitly isolated from the
control command pipe. Installed PyAV libx264/AAC encode authored pixels and
48kHz stereo PCM,2video/1audio codec threads, no B-frame queue, bounded frame/
readback pipeline. At most8million output pixels; existing4video/128MiB RGBA,
96MiB planes,256MiB texture replacement,64MiB text and32MiB PCM/scratch bounds
remain separate from opaque codec/font/driver/process allocations. No all-count
or total-process-memory certification follows from these component bounds.

Export uses the preview Evaluator at every absolute frame and canonical sample
span, then flushes/drains both encoders. Full decode verifies exact video frame
count/timestamps/dimensions/FPS and one AAC48k stereo stream with<1024final padding
samples. All referenced hashes and protected source/project/output aliases are
rechecked. A unique temporary output is fsynced, validated and atomically replaced
only after owned readers/context retire. A late Cancel cannot undo completion.
Unpublished partial movies and per-job input/timing/error logs remain for diagnosis.
Windows progress snapshots are advisory bounded updates; brief sharing conflicts
may retain previous progress without failing export or weakening durable output.

Evidence and source identities live in task results. Native/CPU reference pixel
comparisons precede encoding; AAC/H264 comparisons declare lossy tolerances.
Moving export currently requires the existing GL context route; unavailable GL
fails clearly and retains work. Preview's Qt CPU reference remains supported.
No physical scanout, subjective listening, full-episode or multi-hour claim is
implied by short standalone export tests. Robert acceptance remains separate.

Pending export destinations are reserved by the owner against new source,
protected-path and import/original provenance references and hardlink aliases.
The guard repeats at async commit/Undo/Redo; export also protects retained history
and waits for preexisting source preparation. Conflicting edits reject wholly;
unrelated later edits remain possible. Reference paths are deduplicated before
alias checking. Resource retirement reports actual empty text cache item count;
retained peak/font/global/history ownership remains separate.


## Protected Episode04 assembly (increment F; final qualification pending)

`app/visuals/project_episode04.py` assembles the protected copy through the
documented authenticated Studio commands. It does not edit `.zwv` JSON directly,
write production files, import the baked master as a clip or start device output.
The supplied recipe creates33sources/9tracks/136clips/102captions/52graphics across
11781frames at1280×720/30FPS. Sources and clip instances stay distinct.

Use a fresh disposable Studio/project; copy its agent endpoint from the dock.
Run the project `.venv` Python with `-B -X utf8 app/visuals/project_episode04.py`
and `--endpoint <copiedendpoint> --receipt <PRODUCTION_INPUTS.json>`
`--destination <NEW Episode04.zwv> --evidence <NEW evidencefolder>`. The current
protected receipt and saved baseline are in task results. Evidence folder must
be new; existing live documents are rejected rather than replaced.

Each exact bounded request is retained before transmission with a stable operation
ID and expected project/epoch/document/command revision. On an uncertain result,
query that ID or use `project_cli.py --request <EXACT retained requestfile>`;
never create a duplicate ID or rerun over an intervening manual edit. The importer
refuses automatic rebase/new assembly over an existing project. Remaining phases
can be continued deliberately through documented owner commands after reconciliation.

Known source PNG cards retain flat original artwork; editable header/status/cue/
counter/progress recipes preserve known production text/layout provenance. Narration
parts/seams are retained, with separate voice/music/game/sting lanes and deliberate
quiet bed, crossfades/ducking, host-free whole-source sound and editable safety gain.
Source interval and section frames match the measured producer manifest.

Declared comparison differences: producer video was640×360 before upscale while
this project retains native source pixels; Qt/Pillow glyph metrics/filtering
differ; original sting mono downmix differs from preserved native source channels;
.12second gain fades/ducking use4output frames (.133333s), while .2/.5/1.5seconds
align exactly. Cue times retain documented ceil output-frame policy. These are
explicit recipe limits, not claims of bit-identical legacy encodes.

Project demand decoding opts into the existing distant-demand resync: forward
misses far from the previous decoded cursor seek their keyframe instead of walking
hundreds of obsolete planes. Legacy clocks retain their default behavior and
512-frame/two-second refill,96MiB planes/128MiB snapshots remain. No caps increased,
frame resolution reduced or samples skipped; independent actual60FPS PTS/RGBA
comparisons and forward/back/repeat/cancel tests bind this correction. Cold seeks
still approach1.3seconds in sampled whole-episode diagnostics, not an FPS guarantee.

The15supplied narration endings and assembled joins have exact source clips and
expected text in the listening evidence pack. No extra recorded tail beyond
documented final-part endpoints was found. Numeric ends, full device playback or
silence holds do not establish complete spoken words/semantic joins. Missing
complete speech needs owner input; new voices/transcription are not this stage.

The completed disposable native sequence began with recovered revision7,
changed narration .85→.80, trimmed the opening linked pair to92frames, moved it
toframe3 and corrected the first caption comma to an em dash. Four Undo and four
Redo steps matched eight complete document-state pairs exactly, endingrevision19.
Native Save As secured a NEW managed-media project; normal GUI/owner close and
fresh native Open preserved all33sources/9tracks/136clips/102cues/52graphics.
Export from reopened19 produces the full11781frames and18,849,600authored samples.
The short changed-region sample is an encoded-packet copy from that full export,
not a separate compositor or changed project. Final paths/hashes are in the packet.

Full continuous392.7s real QtGPU/defaultWASAPI playback completed. Robert answered
"was fine" to the specific cutoff-ending/join/picture-audio question. This is owner
subjective feedback, not measured audible position or a per-word transcription.
Coarse paired clock/preview status lagmedian100/p95400/p99900/max1333ms remains;
native output retainedmaximum71.9403ms and padding2248frames are distinguished from
sampled maxima49.2825ms/2240. No deadline failure was reported. Boundary source
preparation and scheduling tails remain explicit; no universal smoothness/sync,
high-count or multi-hour certification follows. Available original narration is
unchanged; no missing words were fabricated or recovered by silence.

Native canonical audio also seeks a distant demand instead of walking from an
old decoded cursor beyond512frames/two seconds. Forward cache continuation is
retained only within two canonical seconds; cache/PCM/curve/channel and original
work bounds stay unchanged. Actual compressed music forward/back/repeat seeks
match fresh canonical-reader bytes; this is reader-instance parity, not an
independent resampler/listening claim. The physical F workflow was restarted on the verified current mixer source;
older interrupted-run evidence remains bound to its original loaded module.
