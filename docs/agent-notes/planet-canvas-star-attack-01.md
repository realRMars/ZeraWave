# Planet Canvas selective starflight — CPU/code handoff

Authorized target: existing drifting background stars swell on driving low-frequency
attacks while retaining left-to-right/diagonal drift. Shooting-star births, shared
star clock, ordinary drift headings, palettes, materials, brightness formulas,
geometry, rings/moons, player and Main remain outside the change. GPU capture,
desktop/audio controls and device access await Bob's coordinated window.

Robert heard the preceding surface-only comparison and found it basically the same.
That surface pilot is not artistically accepted; provisional critic6 was not a user
score. Its code, settings and completed audible artifacts are preserved. This new
candidate changes starflight only, with surface DSP identical in both review arms.
No new grade, acceptance, integration, commit or push is asserted.

## Route and correction

Existing PCM uses one capture/analysis stream. `live_visual_test.analyze_samples`
computes the legacy FFT and20–250Hz mean magnitude, normalizes bass at0..16 with
.5 smoothing, detects bass onset at a .2 rise, then applies the visual conditioner.
The frame carries bass/mids/highs, each onset and global flux. Presentation maps
bass to scale, mids to movement, highs to sparkle, and maximum onset to impact.

The legacy renderer's ordinary star cruise uses .70flux+.30sparkle, chorus threshold
.72..96, .8s easing and positive integrated `star_time`; ordinary rate stays1..1.75.
The shader's wake chorus uses .48flux+.22sparkle+.30impact at.38..88. This enables
mid/high transients to produce the swell. `u_star_time` also schedules shooting
stars, so modifying that shared clock would change their births.

New default-off `planet_star_attack_pilot` is guarded to held Canvas5 only, with no
Main, Galaxy, sequence or transition endpoints. It is independent of the existing
surface DSP flag. The same analyzer/capture provides the existing raw low-band
energy to new optional `app/audio/low_band_attack.py`; no extra FFT, analyzer,
capture owner, device, normalization or audio-quality change was made.

The low-band proxy requires level>=6 and fresh rise>=4 in existing mean-magnitude
units, then smoothsteps relative rise/current level from.22 to.70. A bounded
0..1 `bass_attack` and sample clock are attached to the existing AudioFrame only
when the star pilot is eligible. This is a low-frequency rise proxy, not universal
kick classification; other low-frequency attacks can legitimately excite it.

Presentation rejects strengths below.10, primes120ms on source/gap, debounces
duplicate packets for80ms, releases sample pulse over90ms, and uses15ms rise/70ms
fall for the displayed envelope. These are final proposed/implemented pilot values,
not historical authored settings. Flight remains within the authored1..1.75 speed
range and .0012..095 wake range. Speed and wake pulse; the independent phase only
integrates positive speed. No volatile amplitude multiplies absolute time, reversal
or return spring exists. Source reset clears response while preserving trajectory;
large render gaps freeze the first recovery step instead of teleporting.

Renderer submits `u_planet_star_flight=(enabled,phase,envelope)`. Only background
sheet travel and wake length select it, under a second held-Canvas shader guard.
Original star clock, shooting-star function, headings, presence, brightness,
twinkle, pigments and shading expressions remain unchanged. Disabled shader code
normalizes exactly to the prior source; GPU compile/pixel equivalence is deferred.
No new persistent buffers or graphical allocations are introduced.

## Actual checks and limitations

`planet_star_attack_test.py` final CPU PASS covers synthetic controlled PCM through
the actual analysis function, then120Hz numerical presentation simulation:

- Four timbres (45Hz swept/sub,65Hz round,110Hz tight,180Hz high bass), plus loud
  mid/high/combined beds:14/14 scheduled attacks in every fixture. Envelope peak
  about.737, mean inter-hit valley.018; measured peak delays33–67ms.
- Consecutive250ms:12/12, peak.766/valley.218. Consecutive125ms:23/23,
  peak.837/valley.596; peak delays17–75ms across these fixtures. Fast pulses settle
  less fully; this is measured response, not proof of perceptual quality.
- Louder mid/high attacks, sustained/slow bass and silence: zero accepted attacks
  and zero envelope. No broadband/snare extension was implemented.
- Repeated audio/render frames, missing/nonfinite/version-invalid input, source
  reset, sample/render gap, no-input release and10000positive phase steps PASS.
-120exact legacy analysis frames, optional-field bypass, session routing/defaults,
  Main/Galaxy/sequence/transition guards PASS. The actual live owner and replay
  functions execute with supplied PCM/fake windows:4live/6replay contexts, one
  stream per live run, zero real threads/devices, Stop/EOF cleanup PASS.
- Shooting-star/shared-clock blocks byte-identical; surface mapper unchanged;
  shader brightness/heading/pigment/presence/twinkle code preserved. Existing
  `planet_canvas_dsp_test.py` regression PASS. Final helper/source syntax and
  `git diff --check` results are bound by the evidence index.

The existing authorized Balloon passage136.192–226.176s was traced through actual
CPU analysis with the original prefix preserved:2109packet-step frames,145accepted
low-band rises, peak envelope.9779 and envelope>.5 for5.64% of frames. Phase remains
positive. These rises have not been heard/classified as kicks. This trace is not
GPU, live capture, natural listening, native60Hz or multi-hour evidence.

Meaningful failures are preserved in the task folder: smoothed legacy bass onset
missed rapid125ms hits (10/23);90ms debounce missed sample-quantized hits (21/23);
the first peak window included the following fast beat; the long release failed
fast-hit settling; the AST harness lacked line locations. The corrected final
matrix passes. Weak smooth-start rises were rejected before final binding.

Absolute low-band floors can miss very soft attacks. The measurement inherits the
existing mono downmix, including antiphase cancellation, and2048sample window
resolution. It can respond to bass/tom/other low-frequency attacks, not just kick.
Fixed bounded release is intentional for this first candidate; no learned drum,
pitch, key or universal music interpretation claim is made. Resource/perceptual
cost remains for matched GPU/native testing on the actual device.

## Review route and queued scope

Evidence root: `work/planet-canvas-star-attack-01/`; `review-index.json` binds the
starting dirty snapshots, exact task delta, final sources, tests, failures, natural
CPU trace, preserved six DSP files and completed audible comparison. Separate
`star-original-session.json` and `star-candidate-session.json` differ only by
`planet_star_attack_pilot=false/true`. Both keep surface DSP ON and Elastic.65 /
Braided.55, seven-material cycles and all other settings identical. Application
defaults remain OFF for both flags.

For a later coordinated live review, open a fresh Development Studio after these
code edits, File > Load session…, load the desired arm, and choose Input > Live
system audio. No visible star-pilot toggle was added. Stop/load/restart switches
the hidden saved flag; current running Studio does not reload Python code. These
are instructions, not an assertion that a live run was performed here.

Ready for coordinated same-input/seed/time/dimensions/settings A/B and one shared
original audio playback source, with explicit source/attack/envelope/phase and
submitted uniform traces. Keep shared star and shooting clocks equal; compare
unchanged planet/material controls, peak brightness and trajectories. Do not open
a competing window/capture while Robert is on call. No Main rollout before the
meaningful9/10/user acceptance gate.

Next queued task is the optional read-only LIVE Studio mapping monitor: actual
source/target meters, source/frame/config identity, honest time/manual/unmapped
labels, bounded telemetry, no duplicate analysis or queue drain. It must not tune
mappings or become an all-world framework. Actual UI/GPU verification is later.
The additional measured-tail request fits the carried low-band-level/sample-clock
payload: bounded response could use observed decay instead of fixed duration.
Snare-like/broader-band accents need a separate reviewed scope decision before
widening the current low-frequency proxy. Neither queued item is implemented in
this kick-stage handoff.
