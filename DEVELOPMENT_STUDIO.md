# ZeraWave Development Studio

Studio is the current development and review tool. It is not a consumer product
or a commitment to paid ZeraWave Studio 1.

## Launch and review

Run `run_development_studio.bat` from the project root. Use **Library** to find
an existing world, effect, or technique; **Build & preview** to select a
world/form and input; **Effects & layers** to inspect optional selections; and
**Review** to inspect the resulting run folder.

For visual work, review a held form in motion through quiet and sustained active
passages, then review Main Blend. Track replay is silent but uses the shared
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
to the next run; declared held-Roots color controls are the live-edit exception. Close the visual window for a normal finish and complete
metrics. **Stop preview** terminates only Studio's child; partial logs/captures
remain and final metrics may be incomplete.

### Effects & layers

The existing tab has four sections. These organize controls, not independent
rendering passes or playback engines:

- **Materials**: Living artifacts, Liquid Alloy, Prismatic Lattice and Echo
  Weave; material isolation and restoration. The common **List playback** and
  **Hold (seconds)** controls retain material melding and timing.
- **Shared FX**: reusable compatible treatments, including Tunnel, Fractal
  folds, Horizon, field decorations and supported shooting stars. Compatibility
  comes from the existing catalog; shared does not mean every world or form.
- **World details**: rings, moons, blossoms, rain and world-specific features.
  The catalog filters by world; individual forms may use only some details.
- **Palettes**: the Planet palette selector and matched A/B replay; held Roots
  exposes the modeless live color inspector here.

Choose a section, then its catalog category/effect and **Add**. The **saved
combined cycle order** remains visible across sections; its row flags are the
saved list, including while isolation temporarily overrides materials.
**Up / Down** retains cross-category order for old and new Cycle lists. It does
not define GPU stacking order. Main has its own profile and does not import held
world profiles automatically.

- **List playback: Authored** uses authored presentation and parks the custom list.
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

### Live Roots color editing — exact review clicks

1. Launch `run_development_studio.bat`. In **Build & preview**, choose **World:
   Organic > Form: Roots**. A blank Organic Form cycles forms and does not support
   these overrides. Leave **List playback: Authored** for the simplest Roots view.
2. Choose **Input: Synthetic preview**, **Test track**, or **Live system audio**,
   then **Start preview**. For track editing choose **Replay speed: Real time**
   and a sufficiently long duration. Track replay is silent; live input listens
   to system audio. Synthetic preview has continuous diagnostic movement.
3. Open **Effects & layers > Palettes > Open live color inspector…**. This is a
   modeless Studio window so it can sit beside the existing visual. Choose a
   target and a named color role. Click/drag the hue/saturation wheel, adjust
   **Brightness / value**, or enter **#RRGGBB** and press Enter. Swatches show
   pigment before shading, tonemapping and musical response, not final pixels.
4. For a field gradient, edit its fixed role colors and **Blend starts / Full
   color at** values. These positions are along shading value (0–1), not branch
   length. The existing gradient uses four overlapping smoothstep transitions.
   Starts and ends must each remain in order, with at least 0.001 between a
   transition's own start/end. There is no add/remove for these five fixed roles.
5. Watch the inspector status: **pending**, **sent**, then **Applied live** after
   the renderer acknowledges a frame. Rapid changes coalesce over 75 ms. Invalid
   hex or gradient values retain the last valid setup; correct the field or reset
   its target. Live color edits do not restart time, camera, analysis or Echo.
6. **Reset target to Authored** restores the selected target's authored colors/positions.
   **Reset scene to Authored** restores all Roots color targets. **Revert to preview start**
   restores the scene colors present when this current Roots preview started;
   it is enabled only while that preview is running. These actions also apply live.
7. Click **Save named color preset…**, name the look, and choose a JSON file
   (suggested folder: `work/color-presets/`). **Load color preset…** restores its
   target assignments and applies them to the running held Roots preview. Loading
   or editing never rewrites the preset file; saving is an explicit file action.
   A color preset records which colors belong to which scene parts, unlike a
   palette that merely contains colors.
8. **File > Save session** in Studio saves the whole current setup, including
   color overrides, materials, layers and the existing Planet palette choice.
   Current edits are in memory until a preset/session is saved. Starting a new
   preview takes a new revert snapshot. Stop preview or close the visual normally
   to end editing; the current colors remain available for the next Roots run.

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
Alloy, Prismatic Lattice and Echo Weave keep their independent authored colors;
custom lists add their material effects over the Roots composition. The inspector
edits the named Roots components, not arbitrary material pigment.

Overrides are parked outside held Roots, including Organic cycling, Membrane,
Planet Canvas and Main. Switching Studio selection does not retarget an already
running child. Non-color controls still apply on the next preview. The inspector
can prepare colors before launch, but then clearly says **next Roots preview**.
Layer-playback **Authored** and color **Reset scene to Authored** are separate: use both for
an entirely authored Roots setup. The existing Planet palette and matched A/B
workflow remain unchanged and separate from live editing.

### Planet Canvas palette prototype — exact review clicks

1. Run `run_development_studio.bat`. In **Build & preview**, choose **World:
   Cosmic > Form: Planet canvas**. Cosmic's blank Form also holds its only form,
   Planet Canvas. Main remains unchanged.
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
   playback: Authored**. There is no palette cycling or per-effect override.
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
- Echo Weave is implemented as the fourth material. Main’s default profile uses
  the material quartet. Existing three-material saved profiles remain valid;
  stateful Echo needs moving preview or replay, not a still.
- Authored restores a world’s authored presentation. Main owns a separate
  profile. Explicit saved lists are retained rather than silently migrated.
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
