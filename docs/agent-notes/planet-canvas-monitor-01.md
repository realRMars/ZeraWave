# Planet Canvas continuation: star GPU evidence and optional mapping monitor

2026-10-03. Authorized continuation after the frozen star CPU handoff; no wider
mapping, Main integration, publication, commit or shared-document changes.

## Delivered and review route

The matched original/candidate starflight comparison is ready at
`work/planet-canvas-star-attack-01/gpu-delta-01/audible-star-comparison.html`.
Both arms retain the surface DSP pilot, the same .65/.55 manual spatial ceilings,
material cycles, palette, seed 7301 and original Balloon PCM. Only the star pilot
flag differs. The page uses one unchanged original audio sidecar and two muted
videos, with common play/pause/seek and sample-time synchronization. Script syntax,
media duration and PCM identity were checked; builder browser playback/listening
was not performed. The earlier surface-only comparison remains unchanged.

Open a fresh Development Studio, load `star-candidate-session.json` from
`work/planet-canvas-star-attack-01`, choose Cosmic → Planet canvas and Live system
audio, then View → Planet mapping monitor… and Start preview. The monitor can also
show Test track data with an explicit REPLAY label; track replay remains silent.
Its checkbox pauses observation, without changing either pilot or any settings.
Close the monitor to disable it. It is not persisted in sessions. Existing Studio
Stop remains unchanged. The controlled test closed its own renderer window to
exercise normal capture cleanup.

Return actual results through Bob/Prompter for the approved independent review.
No critic was dispatched, no grade assigned, and no Robert acceptance inferred.
The earlier surface-only candidate was judged too similar by Robert. This evidence
does not establish a meaningful 9/10 result by itself.

## GPU comparison and visible observations

On the RTX 3070 Laptop GPU, each arm encodes and decodes 2109 full frames at
23.4375 fps, 89.984 s, 640×360. Source 136.192–226.176 s, 48 kHz stereo; analysis retains
the original prefix and graphics begin fresh at the passage boundary. No frames
are skipped. The original cold startup was145.76s; candidate warm startup 7.77 s.
These are different startup cache conditions, not a matched startup comparison.

All 2109 paired records agree exactly for source/time, legacy audio, parameters,
descriptors, spatial amounts, material mix, flow time and shared star time/rate.
All 180 lossless original-arm captures are pixel-identical to the preserved prior
surface-pilot-only deeper arm. Candidate star phase is monotonic; rate1–1.73343
observed, mean 1.07753. Envelope peak .97790; 5.642% of frames exceed .5.

Builder inspected an eight-pair lossless sequence across the passage and a twelve-
pair decoded sequence at85.33 ms spacing around the peak, plus the full-size peak
pair. The foreground planet/rings/moons and cycling materials agree; the candidate
has dotted elongated star wakes during the peak and continuing positive drift.
This is sequence inspection, not continuous audiovisual listening or a grade.

Median/p95 CPU render submission: original 1.392/1.827 ms, candidate 1.149/1.611 ms.
Readback median/p95:4.009/4.523 ms and3.822/4.316 ms. Encoder pipe median .271/.267 ms.
These capture conditions include synchronous evidence readback/encoding; they do
not establish native 60 Hz rendering, scanout, or an FPS guarantee. Monitor operation
itself performs no GPU readback. No broad world suite or multi-hour soak was run.

## Monitor route and bounds

Live/replay owners pass existing analyzed AudioFrames to a single bounded monitor
snapshot, without another capture, FFT, analyzer call or audio queue drain. The
renderer publishes exact CPU submission values (no uniform getters) at at most 5 Hz.
Studio's existing ColorLink threads carry a coalesced enable command and retain
one latest telemetry record. Telemetry is excluded from run.log. Existing color
acknowledgements and scene controls retain their own paths.

The 28 rows distinguish conditioned bass/mids/highs/flux, the interval low-band
attack peak, descriptor spread/fullness/confidence when already available, legacy
scale/sparkle/impact/flux submissions, star rate/wake, shooting-star manual/time
selection, three spatial amounts with current base ceilings, seven material
weights and three shared postprocess weights. The 12 FFT bars show frequency
energy/magnitude, not pitch/key. Low-resolution bands are marked with an asterisk.
Unavailable descriptors remain N/A; monitoring does not enable them.

Packets bind a unique run, resolved source, initial configuration hash, latest
applied color revision, delivered frame counter, audio clock and render time.
Pilot sample clocks are used when present. Otherwise delivered PCM time explicitly
excludes queue drops. LIVE packet freshness uses the existing worker timestamp;
REPLAY uses local receive time. No-current-input and stale status are explicit;
paused/stopped views retain values with their status. Manual/time-only geometry
and shader-derived legacy wake are not presented as new descriptor mappings.

CPU-only 5000-frame benchmark: snapshot median .00760 ms/p95 .01161 ms; packet-call
median .00070 ms/p95 .12041 ms (includes throttled calls). 1000 packets, max 1482 bytes
for the supplied fixture. Actual LIVE packets were approximately 2.2 KiB. This
excludes pipe/Tk/GL cost and is not a whole-loop performance guarantee. Existing
diagnostic console logging is unchanged; monitor telemetry introduces no log.

## Checks, failures and remaining limits

Focused monitor standalone CPU checks PASS: raw/frame/config binding, clamps,
interval pulse peak/reset, LIVE/REPLAY, missing/stale/paused/stopped, bounded latest
pipe data, color ACK preservation, 120 exact analyzed-frame comparisons, actual
renderer telemetry block with zero GPU getters, held-only guard, actual window
refresh adapter. Starflight CPU regression PASS. Session validate/command/values/
save/load/new ASTs unchanged against the monitor baseline. Syntax and diff-check
PASS. Existing complete Studio/GPU/world suite was not run.

Actual Tk Studio + LIVE system loopback + GL + existing pipe check PASS after
correcting the test harness:28 rows, monitor off 2 s/on 3 s, delivered frames8→168,
saved setup unchanged, returncode 0, native stop HRESULT 0 and all owned capture
pointers released. This 9.05 s test contained active input but was not listened to
or controlled; it is not natural musical acceptance.

Failures are retained: first CPU test expected the wrong manual-driver wording;
first two LIVE harness attempts targeted the venv launcher instead of the renderer
PID and used their owned-process fallback termination, without confirmed native
cleanup. Final harness used only the renderer PID from its own preview log and
confirmed normal release. One evidence-write approval review timed out; retry
succeeded. No unrelated process was stopped.

Low-band rise remains a proxy, not universal kick/instrument classification. The
star controller still uses FIXED .09 s audio release/.07 s display fall. Carried low-
band level/sample clock are not measured-tail shaping. That refinement is deferred,
as is any snare/broadband expansion. No new geometry, colors, palettes, audio
normalization, player/capture/queue changes or 27-world rollout were added here.

The CPU star index and all earlier evidence are frozen. Exact CPU sources and GPU
sources are archived separately and bound by the new indices. Current renderer
differs from captured GPU source only by the monitor's applied-color-revision
cache; the final actual LIVE check covers that revision. Six standalone DSP files,
surface mapping sources, shader and unrelated dirty work are preserved. Final
source/diff/artifact hashes are in the monitor and star GPU delta review indices.
Nothing staged, committed or pushed; no frozen portable or root document changed.
