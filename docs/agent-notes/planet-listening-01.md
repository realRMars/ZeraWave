# Planet listening windows - builder results

2026-10-04. Current authorized batch: extend the accepted 24-target Audio Tuning
workflow with optional target-local Start/End listening windows, selective useful
gain headroom and actual detector feedback. The entire dirty checkout, including
Robert's current authored values, was the baseline. This batch follows the
accepted target-switch and simultaneous-overlay work. It is not the earlier
read-only DSP mapping proposal or a recovered three-layer design.

Source/diff/check/backup identity: `work/planet-listening-01/review-index.json`.
HEAD and origin/main remain `0342e518a7bd2c521416e8027a7920668fc5ee51`.
No staging, commit, push, root-document rewrite, dependency change, cleanup,
player capture/queue change, GPU run or running-preview interference occurred.

## Implemented result

The existing Audio Tuning dialog offers the windows below. Each has independent
Start/End fields and an opt-in checkbox. All newly added windows default OFF.
OFF retains the original input, including the original compound formulas.
Live override OFF returns to the saved authored values; if the user explicitly
saves an enabled window as authored, Back to authored restores that window.

| Target | Optional input windows |
| --- | --- |
| Background stars | Flux, Sparkle, Impact |
| Living Artifacts | Flux, Sparkle, Bass, Impact |
| Liquid Alloy | Flux, Sparkle, Bass, Impact |
| Luminous Lattice | Flux, Sparkle, Bass, Impact |
| Echo Weave | Flux, Bass, Impact |
| Ink Archipelago | Flux, Sparkle, Bass |
| Interference Silk | Sparkle, Bass |
| Cellular Mosaic | Flux, Sparkle, Bass |
| Tunnel | Flux, Bass |
| Fractal | Flux, Bass |
| Horizon | Flux, Bass |
| Elastic Lenses | Flux, Bass |
| Braided Flow | Flux, Bass |
| Nested Windows | Flux, Bass |
| Sparkles | Sparkle |
| Flecks | Flux, Sparkle, Bass, Impact |
| Beams | Flux, Sparkle, Impact |
| Prism Assembly | Flux, Sparkle, Bass |
| Digital Bloom | Flux, Sparkle, Bass |
| Chromatic Memory | Flux, Sparkle, Bass |
| Rings | Sparkle |
| Moon dust | Flux, Sparkle |
| Shooting stars | Sparkle, Impact |
| Surface response | Flux, Sparkle, Bass, Impact, Movement |

Compound Energy, Surface and flow-drive contributions reuse their actual selected
ingredients; they do not gain misleading independent Energy windows. Selected,
Cycle, authored and Meld role availability remains intact. Existing palette,
color, geometry, events, manual selection and history ownership are retained.
Shared sky-clock edits continue to affect shooting-star births, as the existing
clock gains already did. Surface clock inputs affect the shared Planet material
and spatial clock. Those existing scopes are described in the dialog.

Five gains now allow 0-4: Alloy disk width and surface deformation, Lattice vertex
size and tilt, and Echo Weave Flux ink travel. They still clip their normalized
audio input at 1. All other gain bounds, defaults and brightness limits remain.

Gold solid Flux, blue dashed Sparkle, violet short-dashed Bass, coral mixed-dashed
Impact and green dotted Movement overlays can be shown simultaneously. The
original Star attack weighting curve remains separate and visible. The dialog
reuses 17 slider slots and five checkbox slots in the existing scrollable layout;
the spectrum retains its fixed eight-range/32-item pool.

Star attack sensitivity is retained. Feedback displays the actual weighted level,
rise and fractional-rise thresholds used by the existing detector. Optional
custom Impact has its own actual rise/threshold display and sensitivity, enabled
only when that window is ON. There is no invented ADSR or attack-time control.

## Routing and semantics

One existing FFT feeds `SpectralListening` processors on the existing analysis
owner. No new capture or FFT is created. Payloads travel on the existing frame,
through live/replay observation to the existing Planet/Artifact tuning models and
renderer uniforms. The standalone six-file DSP work is unchanged.

Start is inclusive; End is exclusive, 0-24000 Hz. At current 48 kHz/2048 input the
bin spacing remains 23.4375 Hz. One-Hz controls position boundaries without adding
FFT resolution. Empty enabled selections are rejected using actual bins. Pending,
mismatched or older-than-one-second measurements do not supply local values.

Flux uses positive selected-bin magnitude differences, adaptive normalization
0-180, existing smoothing/quiet conditioning. Sparkle uses selected-bin mean,
fixed 0-1 normalization and conditioning. Bass uses selected-bin mean with fixed
0-16 normalization; Movement uses adaptive 0-4. Each has its own bounded history.
These are custom-window measurements, not instrument recognition.

Custom Impact detects positive change of the selected mean after adaptive 0-4
normalization/smoothing, with threshold `0.2 / sensitivity` (0.5-2 sensitivity).
It differs from the original maximum of three band onsets. The first window,
changed window/sensitivity and changed source are primed against false control
hits. Its visual envelope releases with `exp(-6 * dt)`. Repeated render frames
cannot re-trigger an onset. Rewind suppresses the previous packet until a fresh
sample arrives. Original raw-onset injection remains raw when its window is OFF.

The 45-row Planet uniform allocation and stable role order are retained. Slots
in [-2,-1] encode a final local input in [1,0]; these internal values never enter
authored/profile files or user gains. Ordinary nonnegative gain slots keep the
existing shader path. Artifact listening uniforms extend from two to four channels.
No persistent graphics resource or history-buffer allocation was added.

## Authored protection and persistence

Recoverable backup: `work/planet-listening-01/user-backups/v2-20261004T0127513378479/manifest.json`.
Manifest SHA256: `502efe8f9c1432ff0876b352af193b16fef32c48b91589f3e436b3d50a0165cb`.
All 21 originals and backup copies match their recorded bytes at closure. Missing
authored targets remain missing. No original was rewritten or restored by this task.

Schema 3 saves all applicable window choices in the existing target-scoped atomic
store. Old generic v1 and Star/Artifact v1/v2 load in memory with exact original
values and newly added windows OFF. Startup Star validation now uses the full
existing FFT grid for presentation windows while retaining its attack-window
limits. Save profile, Save as authored baseline, Load and relaunch round trips
were checked in isolated temporary stores for all 24 targets. Save actions require
matching acknowledged settings and actual bins for enabled windows. Named profiles
remain separate from authored data and reject cross-target loads.

For recovery, locate the corresponding original/backup paths in the manifest and
compare current hashes first. Restore only the requested files after preserving
any newer user saves. No automatic rollback script was added.

## Executed evidence and limitations

Eleven check groups have passing results, with initial failures retained in
`checks.json`/logs and resolved runs recorded in `accepted-checks.json`.
Evidence includes 58 generic target/source isolation cases; exact 64 legacy audio
frames with windows OFF; 1200 exact original Star detector packets plus metadata;
432 exact original shared-flow cases; 72 actual Star/Galaxy clock OFF cases;
all 24 target native hidden Save/Load/author/relaunch cases; 107 native target
switches; simultaneous overlays, keyboard dispatch and bounded canvas redraws;
real control/status pipes with mocked capture/graphics; and a 73506-byte exact ACK
above the old 64 KiB reader limit. The new bounded ACK limit is 131072 bytes.

Initial failures were obsolete detector packet equality, old UI text/window-count
assumptions and historical shared-clock source identity. The checks now compare
original detector keys exactly, require the intended enabled/disabled windows,
and execute actual old/new clock blocks numerically. Earlier test-setup failures
included narrow startup-bin validation (fixed to the full grid), Impact spec
unpacking, missing mock environment names and expected schema/row counts. These
were implementation/test iteration failures, not evidence of GPU or musical success.

Final matched CPU supplied-FFT cost: 30 warmup + 300 samples/arm, same seed, arrays,
48 kHz/2048 bins and mode 2. Median/P95 ms: earlier OFF 0.209/0.384; current OFF
0.911/1.036; every target forced ON 4.083/4.478. This measures listening processing,
payload copying and role/uniform resolution only. It excludes FFT, capture, JSON,
GUI, render and swap. Background Comfy, scheduling and thermal state were not
controlled. There is no FPS, hard-latency or multi-hour claim. Current OFF keeps
no previous magnitude arrays; forced all-ON holds 196800 bytes across 24 fixed
processors, with adaptive histories bounded to 20 entries each.

Changed shaders have not been GPU compiled. The prior RTX 3070 Laptop smoke pack
belongs to the earlier sources: cold startup 130.535 seconds versus warm
0.704/0.690 seconds remains unresolved and does not validate these shader edits.
No new screenshots, normal-speed visual sequence, decoded audio replay, natural
music listening, artistic acceptance or critic score is claimed.

## Review route

Return this builder result to Bob/Prompter. No reviewer was dispatched. Coordinate
GPU work with Bob before running it. At a convenient user-owned break, save any
desired current live values and restart Development Studio to load the changed
modules; merely reopening the dialog retains imported modules. This task did not
restart Studio or its preview.

In held Planet Canvas, open Audio Tuning, select a target, enable Live override,
then enable only the desired source window. Compare OFF/ON on identical input,
seed, elapsed time, dimensions, material/spatial selections, palettes and gains.
Inspect quiet, intense and change passages plus matched-level texture contrasts
at normal speed, including Impact release and target return. Check manual colors,
cycling and event variety. Use separate named profiles for trials; promote authored
values only when Robert chooses them. GPU validation and Robert's listening/visual
acceptance remain the next review boundary.
