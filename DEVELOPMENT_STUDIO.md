# ZeraWave Development Studio

Studio is the current development and review tool. It is not a consumer product
or a commitment to paid ZeraWave Studio 1.

## Launch and review

Run `run_development_studio.bat` from the project root. Use **Library** to find
an existing world, effect, or technique; **Build & preview** to select a
world/form and input; **Effects & layers** to inspect optional selections; and
**Review** to inspect the resulting run folder.

For visual work, review a held form in motion through quiet and sustained active
passages. Review affected Main behavior when shared paths change or integration
is assigned; a held-only candidate can be developed before joining Main. Track replay is silent but uses the shared
analyzer, mapper, and renderer; it is not live audio validation. A still capture
alone does not verify motion or stateful effects.

## Operating Studio

Choose a world and narrow the cascading selectors to isolate a form. Leaving
the top selector blank selects Main Blend. A blank branch that has an authored
cycle uses that cycle; a branch without one sequences every implemented leaf in
28-second development holds. A selected leaf holds that form. Selector changes
clear deeper selections.

Choose **Test track**, **Synthetic preview**, or **Live system audio**. Test
track replay requires an existing decoded 48 kHz, 16-bit WAV; it is silent and
does not skip analysis chunks. Speed, duration, and capture options apply only
to track replay. Live input uses system audio, while synthetic preview is a
diagnostic path.

Each preview creates a unique `work/studio/<timestamp>-<suffix>/` folder. It
always contains `preview.json` and `run.log`; track replays also write
`metrics.csv`, and enabled captures add frames at 15-song-second intervals and
`captures.json`. Only one Studio child runs at a time. Most settings apply
to the next run; declared color controls can update the running preview. Close the visual window for a normal finish and complete
metrics. **Stop preview** terminates only Studio's child; partial logs/captures
remain and final metrics may be incomplete.

### Cosmic Galaxy: Galaxy Odyssey review

Galaxy is a candidate outside Main, awaiting Robert's artistic review. Launch
`run_development_studio.bat`, choose **Presets > Galaxy Odyssey > Galaxy scene**,
then **Test track / Real time / Full track** (a track over 1:18 shows the first arrival).
Synthetic preview and live system audio use the same journey. Close the current
visual window before starting another. Older Cosmic sessions still select Planet
Canvas; existing Galaxy colors and layer IDs remain valid.

The opening keeps a rotating galaxy centered, with constant elevation and zero
bank. The74-second itinerary surveys it(0-14), acquires a star(14-18), decisively
zooms into its system(18-23), explores generated bodies or binary stars(23-59),
locks a different galaxy(59-63), and crosses a luminous passage to arrival(63-74).
The central aperture/emission ring, occluding dust and irregular clusters establish
the galaxy. Each arrival keeps the acquired destination identity, with different
arm structure and palette. This is bounded procedural continuity, not literal infinity.

**Shared FX / Spatial / Stellar Gravity Well** is Galaxy-only, with0-1 amount;
Authored uses0.72. Its curved field and local orbital depressions inherit solar
pigments. Explicit empty/disabled lists turn it off. Existing live color edits,
saved sessions, destination seeds and compatible comet/star reuse remain available.
Current review evidence is `work/galaxy-correction-05/`; scoring and live AV remain
separate from frame evidence and technical checks.

**Galaxy Odyssey** also offers **Stellar Cradle / seed 7301**, **Crowded Clockwork /
seed 42** and **Twin Orbits / seed 1337**. Review at least three successive arrivals:
systems have 0/1/2/4/8 bodies, single or unequal paired stars, different inclined
orbits and seven material languages. The camera visits actual generated subjects;
zero-planet systems explore their stellar pair. Sparse anchors and a fine distant
field keep local subjects prominent. The enclosing host remains vast; the next
small destination appears only during lock/travel. Musical pressure shapes local
surfaces/field, spectral flow drives weather/wakes, and onsets launch bounded
stellar ejections and traveling material echoes. Quiet passages retain gentle
motion. These are artistic mappings of existing inputs, not new audio recognition.
Existing source pigments and saved sessions retain their stable IDs.

In **Effects & layers > Palettes**, set **Galaxy destination seed** for the next
preview; repeat it to revisit the same generated destinations. Open the live
color inspector for **Galaxy structure**, **Procedural solar materials**, **Ion
Comets**, or **Drifting starfield**. Rose nurseries, verdigris clouds, warm/cool
stars, oceans, living continents, rocks, giant bands, rings and atmospheres retain
local contrast. Spatial cloud drift, planetary rotation and seeded arrivals evolve
the colors without an automatic synchronized full-screen palette wash.

Copper Comet, Orchid Eclipse and Verdigris Dawn remain available for compatible
galaxy/comet/star roles. Solar materials add Living Atlas, Ember Archipelago and
Opal Frontier. Manual edits and explicit Hold/Cycle retain priority; reset returns
to authored sources. Saved v1-v3 sessions migrate missing seed/roles to defaults.
Palette editing preserves camera travel, geometry and musical history.

**Presets > Galaxy Odyssey** demonstrates **Ion Comets on Planet Canvas** and
**Parallax Shoal on Planet Canvas**. Both are Library Sky effects, opt-in through
Shared FX in Cosmic, Fog and Plasma, with 0-1 amounts. The comet retains legacy
`stellar_sails`/`stellar.sails` IDs for saved data. Galaxy Authored includes both;
other worlds require explicit selection.

Main's existing 12-19 second minimum dwell and 6-11 second handoffs were checked.
Forced six-second entry/exit GPU fixtures show musical warp streaks and a legible
Galaxy reveal; these are compatibility evidence, not Main integration. Galaxy
remains absent from Main's eligible worlds, and all three Envelopers remain off.
See `work/galaxy-journey-review/` and the
[task evidence](docs/agent-notes/galaxy-stellar-aviary.md). Review the motion and
music yourself; automated checks do not establish artistic acceptance.

### Effects & layers

The existing tab has five sections. These organize controls, not independent
rendering passes or playback engines:

- **Materials**: Living artifacts, Liquid Alloy, Prismatic Lattice, Echo
  Weave, Ink Archipelago, Interference Silk and Cellular Mosaic; material
  isolation and restoration. The common **List playback** and
  **Hold (seconds)** controls retain material melding and timing.
- **Shared FX**: reusable compatible treatments, including Tunnel, Fractal
  folds, Horizon, Elastic Lenses, Braided Flow, Nested Windows, field
  decorations and supported shooting stars. Compatibility
  comes from the existing catalog; shared does not mean every world or form.
- **World details**: rings, moons, blossoms, rain and world-specific features.
  The catalog filters by world; individual forms may use only some details.
- **Envelopers**: Prism Assembly, Digital Bloom and Chromatic Memory transform
  the completed image, including visible world details. Multiple enabled
  Envelopers take turns; the final pass uses one at a time.
- **Palettes**: the Planet palette selector and matched A/B replay, plus the
  modeless live color inspector for declared world, material, Enveloper and
  detail colors.

Choose a section, then its catalog category/effect and **Add**. The **saved
combined cycle order** remains visible across sections; its row flags are the
saved list, including while isolation temporarily overrides materials.
**Up / Down** retains cross-category order for old and new Cycle lists. It does
not define GPU stacking order. Main has its own profile and does not import held
world profiles automatically.

- **List playback: Authored** uses authored presentation and parks the custom list.
  On Main Blend it selects the seven-material authored show with paced spatial
  passages. Envelopers are off by default while they await visual tuning.
  On held forms it retains the form’s original authored
  presentation.
- **Selected together** enables all selected rows; an empty list is the base form.
- **Meld materials** fades enabled materials in combined table order while other
  enabled effects stay on. The last 35% of each hold blends to the next material.
- **Cycle list** activates one enabled row at a time in combined table order,
  including mixed Materials/FX/details lists; an empty list is the base form.

**Isolate material** temporarily holds one chosen material with enabled Shared
FX and World details together. It explicitly suspends Cycle or material melding;
**Restore materials** removes the override and resumes the saved flags, order,
mode and timing. It does not silently rewrite the saved list. Start from a custom
Selected together, Meld or Cycle profile; Authored asks you to establish the
explicit desired list first. **Solo whole list** retains its old meaning: it
disables every other row, including FX/details, and clears material isolation.
Switching List playback to Authored also clears isolation for that world.
Select a new spatial or Enveloper row, enter **Selected new spatial / Enveloper
amount (0–1)**, and click **Apply amount** to save its strength for the next
preview. Zero bypasses that row. The amount is stored in the normal effect list;
it does not change a running preview.

### Live color editing — exact review clicks

1. Launch `run_development_studio.bat`. In **Build & preview**, choose a held
   form such as **World: Organic > Form: Roots**. Leave **List playback:
   Authored** for the simplest view. A blank form with an authored family cycle
   also supports colors. Clear the top **World** selector for **Main Blend**;
   other blank branches may sequence their forms in 28-second holds.
2. Choose **Input: Synthetic preview**, **Test track**, or **Live system audio**,
   then **Start preview**. For track editing choose **Replay speed: Real time**
   and a sufficiently long duration. Track replay is silent; live input listens
   to system audio. Synthetic preview has continuous diagnostic movement.
3. Open **Effects & layers > Palettes > Open live color inspector…**. Choose a
   target and named role. Click/drag the hue/saturation wheel, adjust
   **Brightness / value**, or enter **#RRGGBB** and press Enter. Swatches show
   the chosen source color or tint before shading, tonemapping and musical response.
   Scroll the inspector for larger targets such as the eight moon roles; reset
   and preset actions remain below the color wheel. For the six new colored
   treatments, choose the matching material or Enveloper target. Spatial
   effects inherit their material colors.
4. For a Roots or Membrane field gradient, edit the fixed role colors and
   **Blend starts / Full color at** values. Positions follow shading value
   (0–1), not branch length. The four smoothstep transitions may overlap but
   must stay ordered, with at least 0.001 between each start/end.
5. Read the note under the target selector. A held preview lists compatible
   targets; in Main or a sequence, an assignment becomes active when its owning
   source appears and is parked while another source is shown. Shared material
   and FX colors follow compatible scenes; form colors stay with their named
   form. An optional detail can remain invisible until its layer is enabled.
   The opt-in Daddy Long Legs color does not turn the experiment on.
6. To use palette timing on a compatible target, choose **Authored** or one
   of its named families and click **Hold family**. Click **Store current
   setup** after each desired choice (two to four setups), select **cycle**,
   set **Hold seconds** and **Transition**, then click **Apply timing**. These
   cycle only that selected color target by song time; gradient setups keep
   their own named roles and ordered ranges. Select **hold** and **Apply
   timing** to stop cycling. A wheel, hex or brightness edit pauses cycling
   for that target and takes effect live; saved setups remain until **Reset
   target to Authored** clears them. The displayed swatches show the held
   setup, not a live readout of the moving cycle.
7. Watch **pending**, **sent**, then **Applied live** after the renderer
   acknowledges a frame. Rapid changes coalesce over 75 ms. Invalid input
   retains the last valid setup. A color edit does not restart time, camera,
   audio analysis, blast history or Echo.
8. **Reset target to Authored** clears one target; **Reset scene to Authored**
   clears all targets in the current inspector scope. **Revert to preview start**
   restores that scope's colors from the current preview launch when the
   inspector is attached to that running preview. These actions apply live.
9. **Save named color preset…** writes target assignments to a JSON file
   (suggested folder: `work/color-presets/`). **Load color preset…** applies a
   copy without rewriting the source file. Main can import a held-form preset
   while keeping other target assignments; a Main preset can hold every
   target used in Main; Galaxy structure stays parked there. **File > Save session**
   stores the full Studio setup, including colors, materials, layers and the
   separate Planet palette choice. Unsaved edits stay in this Studio session.
10. To review an edited held form in Main, save the session, clear the top
   **World** selector, start a new **Main Blend** preview with the same session,
   then open the inspector. The saved assignments follow their sources as the
   director changes worlds. Leave all roles untouched or reset the scope to
   Authored to recover the current Main default. This review does not deploy
   colors to the standalone player.

Supported targets are deliberately faithful to the shader:

| Target | What it changes | Intentional limits |
| --- | --- | --- |
| Roots field — blue shading | Five fixed blue-gradient roles, with their existing transition ranges | Colors the root surface and dim surrounding field; not a tip or branch-length gradient. |
| Roots field — pearl shading | Five fixed pearl-gradient roles and ranges, spatially blended with blue shading | Does not move the spatial blend or alter geometry. |
| Root ridge highlights | One additive ridge tint | Ridge mask, depth cues and audio brightness are unchanged. |
| Blossoms | One tint shared by petals and center | No independent glow/petal control; existing lifecycle and Root blossoms layer switch remain active. |

Blossoms breathe through a slow authored lifecycle; they can be absent when a
preview opens. Changing their color does not force a bloom or enable a disabled
layer. To see them with a custom material list, add/enable **World details >
World details > Root blossoms**. Materials such as Living artifacts, Liquid
Alloy, Prismatic Lattice and Echo Weave have their own declared display colors;
custom lists add their material effects over the Roots composition. Editing a
material tint does not reset Echo feedback. The inspector edits the named source,
not a final-screen filter.

Switching Studio selection does not retarget an already running visual child.
The inspector can edit and save targets for another selection; those assignments
are parked until that source appears in the running Main/sequence or a later
preview. Non-color controls still apply on the next preview. Layer-playback
**Authored** and color **Reset scene to Authored** are separate. The Planet
**Soft Dream** palette is an independent opt-in; explicit surface, ring and moon
colors are interpreted after it when both are selected.

### Planet Canvas palette prototype — exact review clicks

1. Run `run_development_studio.bat`. In **Build & preview**, choose **World:
   Cosmic > Form: Planet canvas**. Cosmic's blank Form preserves its Planet Canvas
   default; Galaxy is selected explicitly. Main has its own authored seven-material show.
2. To start with the existing four-material meld and stars/rings/moons, use
   **File > Load session… > work/palette-planet-review/studio-session.json**.
   Alternatively, open **Effects & layers > Materials**, use the picker and
   **Add** for desired materials, choose **List playback: Meld materials**, then
   **World details > World details** and **Add** Planet rings, Moons & dust wakes
   and Drifting starfield. Add compatible treatments in **Shared FX** as desired.
3. In **Materials**, choose the material in the isolation selector and click
   **Isolate material**. Enabled world details and Shared FX stay on. The status
   explains that the override takes effect on the next preview.
4. In **Palettes**, choose **Authored** or **Soft Dream** to hold that palette.
   The exact scope is: **Planet Canvas only. Affects planet surface and rings;
   moons and sky retain authored colors.** Unsupported forms disable the selector
   and park its saved choice. Palette **Authored** is independent of **List
   playback: Authored**. This Planet selector does not cycle; the live color
   inspector provides separate target-specific Hold/Cycle controls.
5. For an ordinary preview, return to **Build & preview**, choose **Synthetic
   preview**, **Test track**, or **Live system audio**, then **Start preview**.
   The persistent active-preview line identifies the running palette; edited
   controls affect the next preview, never the current child. Live audio remains
   available for listening review; separate live runs are not matched comparisons.
6. For matched A/B, choose **Input: Test track** and an existing decoded WAV in
   **Build & preview**. Then open **Effects & layers > Palettes** and click
   **Run matched A/B — first 30s of test track**. Studio runs **A: Authored**, then
   **B: Soft Dream**, sequentially from the same frozen setup. Each uses the first
   30 seconds (or EOF for shorter tracks), real-time pacing, the held material,
   identical effects, fixed seed, initial camera, and fixed window size. Each
   fresh child resets analyzer/mapper state, visual clocks, events and Echo
   textures. Replay is silent and may run slower than real time on a busy GPU;
   it processes every audio chunk with the same song-time clock.
7. Let both labeled windows finish automatically. **Stop preview** cancels the
   pair; closing a window early fails its expected-frame-count check and prevents
   a misleading matched-complete result. The input file hash and full analysis
   measurements must match. **Review > Open latest results** opens the pair folder:
   `comparison.json`, plus `A/` and `B/` manifests, logs, measurements and optional
   captures. A successful pair records `matched complete`. Controls changed during
   a pair affect later previews; A/B never rewrites saved user settings.
8. Return to **Materials > Restore materials** to resume the previous material
   selection and mixed Cycle/meld. The chosen palette and ordinary input/speed/
   duration settings survive A/B unchanged. **File > Save session** retains the
   palette, source lists and optional isolation override; reloading preserves the
   ability to restore the list. Load an earlier session to restore an entire setup.

Soft Dream is an experimental contrast awaiting visual acceptance. Review each
material and the meld through quiet, active and release passages. Automated
checks and captures do not substitute for continuous audiovisual user review.
Palette Authored plus List playback Authored restores the authored Planet Canvas
presentation. Older Geometry study sessions still load as Planet Canvas; the
removed Studio form remains available only in diagnostic CLI code.

### Nine-treatment review presets — exact clicks

1. Launch `run_development_studio.bat`. Open **Presets > Nine treatments** and
   choose **Ink Archipelago**, **Interference Silk**, or **Cellular Mosaic**.
   Each preset holds Planet Canvas with that material and stars, rings and moons.
   Then choose **Elastic Lenses**, **Braided Flow**, or **Nested Windows**; these
   use Cellular Mosaic as the source material. Finally choose **Prism Assembly**,
   **Digital Bloom**, or **Chromatic Memory**; these also use Cellular Mosaic and
   affect the whole completed image. Choosing a preset replaces Planet Canvas’s
   current effect list in the Studio session; save a session first if you want
   to keep that list. Other worlds remain unchanged; stored colors still apply
   to matching sources. For a neutral comparison, choose **Palettes > Authored**
   for Planet Canvas and reset any previously edited color target.
2. On **Build & preview**, choose **Synthetic preview** for a quick motion check,
   **Test track** for silent decoded-music replay, or **Live system audio** to
   listen and watch together. Click **Start preview**. For a track, choose quiet,
   strong and release passages; captures are supplemental to motion review.
   Close the visual window normally to complete its metrics.
3. To change effect selection or strength, open **Effects & layers**, select a
   row and use **On / off**, **Solo whole list**, or **Selected new spatial /
   Enveloper amount** with **Apply amount**. Start a new preview to see these
   changes. **Materials > Isolate material** and **Restore materials** temporarily
   alter a custom material list without rewriting it; they also take effect on
   the next preview.
4. To tune colors while a preview runs, open **Effects & layers > Palettes >
   Open live color inspector…**. Select the matching material or Enveloper target.
   Use the wheel/hex controls or the target’s **Hold family**, **Store current
   setup**, and **Apply timing** controls described above. These color changes
   apply live after the renderer acknowledges them; they do not reset motion
   or history. **Reset target to Authored** restores the default colors.
5. Open **Presets > Nine treatments > Main — authored seven-material show**,
   choose a long decoded track or **Live system audio**, then **Start preview**.
   A full pass through all three spatial windows takes 216 song
   seconds; shorter tracks show the early passages only. The three Envelopers
   are off in Main Authored but remain available as separate review presets
   or through an explicit custom effect list. Main’s world director
   still responds to the music, so the visible world is not a fixed itinerary.
   This Main preset replaces the saved Main effect list in the current Studio
   session, so save the current session first if needed. Use **File > Save
   session** for the complete setup or a named color preset
   for reusable color assignments.

The nine presets, row amounts and Main selection affect the next preview.
Declared color edits and Hold/Cycle changes can reach the current preview live.
The Planet Canvas **Authored / Soft Dream** selector is separate and affects the
next preview. Studio’s track replay is silent; only a natural live-music run
provides continuous listening review.

### Sessions

Studio loads session versions 1, 2, and 3. Version 1's flat state is mapped to
the current selection path; versions 1 and 2 load with authored layer profiles;
version 3 retains validated per-world layer profiles. Saving writes version 3.
The optional `planet_palette` field stores `authored` or `soft-dream` separately
from layer profiles. Files without it load as Authored; unknown values are
rejected. New session resets it to Authored. Saving remains version 3.
The optional `material_isolation` map stores world-to-material holds separately
from the original layer profiles; absent maps preserve old playback exactly.
Preview commands resolve the override through the existing profile machinery.
The optional `color_overrides` map stores stable target and role assignments.
Missing targets/roles use immutable authored defaults; sessions without this
field keep their previous appearance. Saving still writes version 3.
Sessions store settings and track paths, not audio files or shader code; a moved
session needs an available decoded WAV selected again.

## Current behavior

- Beat tracking estimates approximate spectral periodicity/tempo and confidence
  from recent spectral flux. Main Blend is chosen by the renderer’s
  energy/lift/release director with recurrence preferences. With high confidence,
  a qualified transition opportunity can align to a tick within a bounded
  0.8-second wait. This establishes neither downbeat, phrase, nor chorus
  recognition, and Main is not a fixed itinerary.
- The deterministic shuffled chapter helper remains for shader fixtures only;
  it does not describe live Main playback.
- Echo Weave is the fourth material; Ink Archipelago, Interference Silk and
  Cellular Mosaic are materials five through seven. Main’s default and explicit
  Authored mode meld all seven at 22-second holds. New spatial effects appear
  during seconds 8–28 of each 72-second passage, with six-second fades.
  Envelopers are off in Main Authored pending visual tuning but remain opt-in.
  The spatial passages cycle through all three effects. Existing custom saved lists
  retain their selected IDs and do not gain new effects automatically.
- Authored on held worlds preserves their authored presentation. Stateful Echo
  and Chromatic Memory need moving preview or replay, not a still.
- Studio sessions retain their supported versioned compatibility behavior.

## Current documentation

- [Roadmap](ROADMAP.md) is the only prioritized backlog.
- [Technique ownership](TECHNIQUE_LIBRARY.md) maps code responsibilities.
- [Maintenance contracts](docs/MAINTENANCE_CONTRACTS.md) preserve Cosmic and
  Elemental boundaries.
- [Handoff](ZERAWAVE_HANDOFF.md) records the current checkpoint and validation
  provenance.

The previous detailed Studio narrative is preserved as
[dated history](docs/history/2026-09-28-development-studio.md). It may describe
superseded trios, itineraries, proposals, or test results.


## Cymatics Water review candidate

Select Cymatics → Water, then Start preview. It runs in real time and starts muted.
Use the Cymatics tab Input selector for oscillator, track or loopback; the general
Input/replay-speed controls are parked here. Input changes need Stop/Start.
Sweep resonances (muted) starts a sweep through modeled basin resonances. Drive
Hz and surface resonances are shown separately; audio bands are not water modes.
Apply live acknowledges validated drive/basin/style edits. Dimensions/depth/mode
changes reset the field; Pause holds it; Restart resets histories.

Damping means energy loss. Glass/mercury/ink are optical coatings; water properties
remain the bounded linear gravity-capillary model. Envelope is an approximate
coherent cycle amplitude; instantaneous height may strobe. This is forced standing
water, not Faraday onset or a complete viscosity/fluid/laboratory simulation.
Preview supports left-drag orbit, right/Shift-drag pan, wheel zoom, R reset and
M mute, with hints in its title. Drag holds a manual view; toggle automatic off/on
to resume without an angle jump. Manual pose is included in saved sessions.

Style & bands includes obsidian/marble finishes, light placement and dye swirl;
stone pigments and named families use the existing live inspector. Original
procedural marble/black stone replaces the earlier generic bed texture.

Style & bands includes Gentle camera orbit (off = stationary), sparse dye tracers,
contrast and Reset dye only. Orbit/drop timing follows source time, independently
of audio. Dye spreads and twists through an artistic approximation, independently of audio.
It also has strongly magnified surface-slope
wobble, not a transported fluid or an audio event. Reset preserves water/clock.
Use Drive held resonance presets to compare recognizable patterns.

Palettes and the existing live inspector expose five water pigments plus two dye pigments and Tidal Glass,
Quicksilver Night and Rose Laboratory families. Sessions always reopen muted.
Optional listening uses the same mono PCM for oscillator or48k16-bit WAV tracks.
Start muted, then check Listen to oscillator / track and Apply. Initial gain.01,
cap/soft ceiling.05; M in preview, Mute now or Stop silences output. Loopback
monitoring is blocked. Pause/EOF/device failure close output; a failed output needs
explicit mute/re-enable. Sessions always reopen muted. A220Hz audition preset
sets an audible but off-resonant driver and stays muted until explicit enable.
The backend was checked with zero-only buffers; subjective listening remains unverified. Water remains outside Main pending review.

[Model/controls/checkpoint evidence](docs/agent-notes/cymatics-water.md)
