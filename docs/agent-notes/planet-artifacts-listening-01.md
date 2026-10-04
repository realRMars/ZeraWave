# Planet Audio tuning batch: Living Artifacts serial checkpoint

Scope expanded during the call to the actual 24-target Audio tuning registry.
This checkpoint finishes the first group and records the remaining inventory; it
does not claim that the other 22 adapters have shipped. Batch authorization
persists, with user testing and independent critique held. No commit/push.

## Prior-control visibility

Attack Sensitivity was not deleted: its Starfield declaration, fourth-row
binding, range 0.5-2, authored value 2 and analysis ACK path remain present.
Inert constructor/switch checks verify Start, End, Weight and Sensitivity are
enabled, shown and retain their keyboard steps. The tall pinned spectrum can
leave lower controls below the scroll viewport. Its requested height is now
150 instead of 250; drawing coordinates adapt to that height, and the complete
control area remains scrollable. Actual visibility in Robert's running window
has not been inspected or proven. No native UI was opened for this pass.

## Implemented local controls

All six gains are 0-2, authored neutral 1, keyboard step 0.01. Normalized inputs
retain their existing 0-1 ceilings. The earlier three controls remain intact.

| Control | Actual affected contribution / bound |
| --- | --- |
| Flux stretch | Local stretch audio term, 0-1.2 before the existing stretch clamp |
| Impact facets | Local angular facet contribution, 0-0.6; max-three-band onset definition unchanged |
| Sparkle light | Local body light increment, 0-0.55; authored base 0.55 retained |
| Bass artifact cell scale | Only the local grid factor `3.2 + 1.6*local_bass`, bounded 3.2-4.8 |
| Bass local radial displacement | Only local displacement of length 0-0.25, using squared bass pressure |
| Sparkle cell presence | Only `smoothstep(0.65,1,local_sparkle)` in the existing cell threshold |

The incoming `q` domain already contains shared pressure, shockwave and spatial
warps. Those remain shared. These controls do not promise removal of all bass or
sparkle behavior. Presence and light are independently adjustable; turning either
off leaves the other and clock-driven morphology, lifetime and rotation intact.

## Listening ranges

Flux range affects only local artifact stretch. Sparkle range affects only the
local presence/light contributions. Both default OFF, retaining exact legacy
signals; impact and shared clocks never use the new measurements.

Each range uses Start inclusive / End exclusive, positions 0-24000 Hz with 1-Hz
keyboard steps. Start must be below End and enabled ranges must contain actual
bins. The parked defaults are flux 0-24000 and sparkle 4000-16000 Hz. Legacy full
flux includes DC/Nyquist; an enabled End-exclusive 24000-Hz range excludes the
Nyquist bin. The original OFF route includes it exactly as before.

`app/audio/spectral_listening.py` reuses the existing FFT; it owns one copied
magnitude array (maximum 1025 bins), fixed 20-packet adaptive history per active
flux measurement and small per-feature smoothing state. No new FFT/capture.
Flux is selected-bin positive magnitude differences summed, then the existing
0-180 fallback / rolling 5th-95th percentile normalization, 0.5 smoothing and
visual conditioning. Sparkle is selected-bin mean magnitude / 0-1 normalization,
0.5 smoothing and the same conditioning. Conditioning uses quiet threshold
0.06, rise/release fractions 0.35/0.08 and max packet delta 0.12.

Changing a range compares unchanged source spectra under the new selection;
source/grid changes prime flux at zero. Local histories reset on selection
changes; shared histories/onset detectors do not. A new selection cannot reuse
a mismatching old measurement: render input is zero until matching analysis.
ACKs show actual bin count, first/last centers and raw/conditioned measurement.
The spectrum's amber line is the union of enabled ACK-applied selections, not a
new FFT or the adaptive normalization. DC remains excluded from the spectrum
drawing but is counted when selected and identified by the effective endpoints.

## Persistence and evidence

Artifact version-1 three-gain documents migrate in memory to version 2 with
neutral new gains and ranges OFF. No existing authored file is rewritten merely
by loading it. Custom Save/Load stays separate; explicit Author Save writes
version 2 atomically. Wrong targets and invalid/empty ranges reject before apply.
Star version 1 and 80-130 Hz / 1.5 / 2 baseline remain unchanged.

Seven recorded CPU suites pass: artifact listening, artifact tuning, star
profiles, spectrum tuning, star attack, mapping monitor and Planet DSP. Evidence
includes actual analysis function attachment, exact shared audio fields in 40
paired packets, 42 full-high-window normalization packets, synthetic in/out-band
and sustained/transient cases, inverse shader source delta, actual AST uniform
routing, real pipes with mocked synthetic capture/graphics, profile migration,
reset, Author Save/relaunch and inert previous-control inventories.

Early console probes were corrected: a cell-factor upper-bound assertion used
literal 4.8 instead of the exact floating expression 3.2+1.6, and an inventory
probe imported mock helpers from the wrong test module. Neither was a product
failure. No intermediate source-bound failed run is claimed for those probes.

The frozen decimal checkpoint is reused with provenance; no new native hardware
keyboard test, GPU compile/render, natural listening or performance guarantee
is claimed. Actual user visibility and visual response remain review work.

## Batch inventory and next groups

`work/planet-artifacts-listening-01/coverage-inventory.json` records every actual
target ID/name, current implementation status, measured source, authored formula,
candidate exposure and route limitation. Gain values for pending targets are
proposals, not existing implemented settings. Two adapters are implemented and
22 remain pending in this serial checkpoint.

Next feasible groups: sibling material local shape/light contributions; shared
spatial authored/mode-dependent presence; separate FX presence/light; sky
brightness/wakes and shared planet/ring surface response; then postprocess audio
response. Preserve Tunnel's current Selected/Cycle behavior. Interference Silk's
flux argument is unused, so it must not receive a nonfunctional flux slider.
Echo's sparkle input is unused in its history pass. Fleck timing currently
multiplies elapsed time by sparkle; a separately integrated clock would change
that behavior and must be reported as a route gap. Moon dust is a shared group,
not independently tunable moon bodies. Shared clock gains require honest scope.

## Coordinated user trial

No existing app/capture was restarted or stopped. Load the changed Studio/preview
code at the next convenient restart. Subsequent gain/range changes apply live,
without restarting capture or preview. Hold Planet Canvas with Living Artifacts
visible; test gains individually, then each listening range with in/out-band,
quiet/steady/attack-rich input. Test profile Save/Load, Back, explicit Author Save
and relaunch. Switch to stars and confirm all four previous controls, especially
Attack Sensitivity, are visible or accessibly scrollable and ACK their values.
