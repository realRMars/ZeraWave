# ZeraWave Development Studio

Studio is the current development and review tool. It is not a consumer product
or a shipped paid ZeraWave Studio 1. Expanded authoring/native stages are approved
direction in ROADMAP, not current product features.

## Launch and review

For the current checkout, double-click **`run_zerawave_studio.vbs`**. It uses the
existing Qt Studio, ADS docking layout, renderer and isolated control owner.
The media-composition candidate below is available for Robert's review; existing full-size
rendering limits still apply. Older Tk and diagnostic entry points remain available.

### Media composition — current candidate

**File → Import media…** reveals Media Library. **View → Media Library**, **Layers**
and **Composition Editor** recover their docks. Layers retains the former Image
Layers dock identity and saved positions. Double-click/Enter a ready reference
uses it without autoplay; repeated activation selects its existing layer. Use
**Add another instance** for a deliberate duplicate. Audio remains owned by
Session Waveform and retains same-source position.

Layers now has an empty dynamic stack, named/locked/visible layers, drag order,
contextual controls, groups, masks and Undo/Redo. Composition Editor provides a
checkerboard layer canvas with move/resize/rotate, crop, mask/cut, zoom/pan and
alignment. Visualizer stays clean output. World only, Layers only and World +
Layers preserve the existing world clocks, histories and resolution policy.

Supported videos use silent PyAV decoding in the existing compositor, with layer
Play/Pause, Stop, seek, rate, loop/ping-pong and in/out controls. GIF animation,
sprite sheets and a strict static glTF/GLB subset share the same layer tools.
Collections store memberships rather than file copies. Artistic sessions use
version 5 with prior-session migration; library version 2 and Qt layout remain
separate. Original files are never altered by composition edits.

See [Media composition instructions](docs/STUDIO_MEDIA_COMPOSITION.md) for the
short review path, exact supported formats, bounds, coordinate/transport contracts
and pending capabilities. Loudman browser display is **pending matching Qt
WebEngine installation approval and validation**. Video audio/multitrack editing
and rigged/animated 3D still need an agreed scope. They are not functioning features
in this candidate. Recovery source is published at `0fb4c3f`, but the editor
remains unaccepted; publication does not close Robert's review issues.

### B1 status — development raster publication candidate

B1 keeps Qt/Python control, ControlOwner and the renderer. Immutable runtime
snapshots now enter scoped owner history and ordered renderer publication before
background PNG persistence. Submitted/applied/published/durable/failed and unknown
ACK outcomes stay separate. Local preview alone does not prove clean output.
Save pins a revision plus Qt metadata; Retry saving/Save As secure failed resources
and retained checkpoints. Admission/backpressure and close protection are bounded.
See [actual results and review](docs/agent-notes/b1-raster-20261008.md) and the
[runtime/save contract](docs/STUDIO_MEDIA_COMPOSITION.md#runtime-transactions-and-recovery).
Robert's acceptance remains pending. Keep the latest
[tool/lock/selection/recovery meanings](docs/STUDIO_MEDIA_COMPOSITION.md#b1-preservation-requirements).
The [acceptance matrix](ROADMAP.md#b1-acceptance-plan) includes rapid input,
delayed saving, Undo/Redo, failures and real input/visible output.

### B2 status — experimental native editor candidate

[B2](ROADMAP.md#b2--c-tiled-raster-resources-copy-on-write-history-and-incremental-compositing)
implements experimental C++ tiled raster resources, copy-on-write history and
renderer-owned editor projection behind B1's transaction/save behavior, followed
by focused selection/clipboard/Smudge and usability/performance corrections. Retain Qt/Python tools and existing GPU output. B1's
release snapshot copying, Smudge/dense Add costs, uncertain-owner/close limits
and pending user review remain; a native performance improvement needs evidence.
See [native setup/fallback](docs/NATIVE_RASTER_B2.md) and [latest actual results](docs/agent-notes/b2-tiles-20261008.md)
for current controls, source identity, costs and unrun checks. Publication retains
user-review limits; native DLL selection requires a new process.

### Qt Library, startup, Resources and window header

Selecting or expanding a World Library row only browses. **Start** commits that
row's canonical eligible descendants as the playback scope. The scope and
currently rendered form appear separately below the tree. Main, Fractal,
Organic, Geometric, Cosmic, Elements and nested Plasma use their Main forms;
Experimental forms remain separate. Normal and Instant BONK retain the existing
director's random selection and transition behavior. A single-form scope disables
BONK with an explanation; Space is a harmless no-op there. Unsupported categories
report unavailable; load an individual Experimental leaf through its existing route.

Double-click a playable leaf, or right-click it and choose **Load**, to invoke the
same direct action. Category double-click still expands/collapses. Compatible
Main loads replace the current form without a transition or source restart,
including while paused or during an existing transition. A leaf within the
committed category keeps that scope; otherwise its nearest playable parent in
the same namespace becomes the scope. Loading the active leaf retains its source
and history. Separate Experimental resource routes use owned Stop/Start and show
their real loading state. Direct selection can still wait for driver work.
Follow/Pin, destination drafts and explicit Save Authored retain their ownership.

Qt startup appears inside the **Visualizer**, including owner connection,
context, shader compilation, resource preparation, attachment and readiness.
Progress is indeterminate. **Cancel** prevents late attachment and shows pending
cleanup if driver work has not returned. **Retry** starts a fresh owned attempt.
The renderer is created hidden, attached to the verified native host and shown
after its first completed presentation. Standalone/legacy loading behavior is
retained. Errors use inline status and Diagnostics, without repeated startup dialogs.

**View → Resources** opens the dedicated read-only dock beside Mapping Monitor.
It shows actual output/framebuffer/internal dimensions and preview scale,
renderer swap returns per second and mean interval, process CPU/working sets,
system CPU/RAM, and identified device-wide GPU/VRAM. Missing, stale, paused,
stopped and warming values are labelled. Process CPU uses one logical core and
can exceed 100%; a sum of distinct PID working sets is not unique physical RAM.
Device utilization is not GPU draw time or application VRAM. Sampling runs
asynchronously at nominal one-second cadence with bounded history; hidden docks
skip painting. Enabled diagnostic reports share these owner samples instead of
starting a second collector. Mapping Monitor's CPU submitted values remain
audio mappings. Optional reduced preview quality remains a separate choice.

The integrated header keeps **File/Edit/View/Help**, **Minimize**, **Maximize / Restore**
and **Close** on the same native main window. Alt+Space opens the Windows system
menu. Maximize is distinct from renderer fullscreen. Layout saves separately to
`work/studio/qt-layout.json`; View restores hidden docks and Reset layout changes
layout only. Normal source choices loaded from sessions survive startup, direct
switching and docking; **View → Preview setup** exposes the existing controls.
New control-owner sessions initially select Synthetic preview / Real time.

Review: Stop, select Organic, Start, then BONK in both modes. Browse Cosmic
without committing it, then Load Galaxy to adopt Cosmic directly. Pause and Load
Roots, then Resume; inspect Follow/Pin destinations. Try Geometric's disabled BONK,
then Elements → Plasma. Show/hide Resources, float/redock Visualizer, restore and
maximize, and close/reopen with a task/session saved explicitly. Short API and OS
input evidence is in `work/studio-additions-20261005/REPORT.txt`; physical drag,
resize/snap, DPI, monitor changes and physical knobs need Robert's hands-on check.

For the unified workspace prototype, double-click **`run_unified_studio.vbs`**
from the project root. It uses the existing `.venv` and opens no console.
The prototype is ready for Robert's organization/functional review; finishing
polish, packaging and artistic acceptance are separate decisions.

The diagnostic entry remains **`run_development_studio.bat`**, with its original
separate-window Studio. To diagnose the unified shell itself, run
`.venv\Scripts\python.exe -B -X utf8 app\visuals\studio_workspace.py` in PowerShell.
Normal-launch startup errors go to `work/studio/workspace-startup.log` and a
visible error dialog; **Help > Diagnostics & logs** opens the owned preview log.
Existing test and player launch paths remain available.

In the diagnostic Studio, use **Library** to find
an existing world, effect, or technique; **Build & preview** to select a
approved Main world/form and input; **Experimental** for unfinished worlds and
the existing Cymatics tools; **Effects & layers** to inspect optional selections; and
**Review** to inspect the resulting run folder.

For visual work, review a held form in motion through quiet and sustained active
passages. Review affected Main behavior when shared paths change or integration
is assigned; a held-only candidate can be developed before joining Main. Track replay is silent but uses the shared
analyzer, mapper, and renderer; it is not live audio validation. A still capture
alone does not verify motion or stateful effects.

<a id="unified-workspace-prototype"></a>

## Retained Tk unified workspace prototype

The central **Visualizer** hosts the existing renderer. Drag a tab to another
area, drag it outside the workspace to float, or use **⋮** for exact destinations
and tab order. **↗** floats the current tab; **×** hides it. A floating window's
**Panel** menu redocks it. Closing a panel hides it. **View** restores panels and
reflects visibility even when a panel floats; **File > Exit** shuts down Studio
and its owned preview. Drag the dividers to resize areas. Hiding all left-hand
tabs collapses the left area; showing one restores it.

The thirteen panels are Session & worlds, Visualizer, Color Inspector, Audio
Tuning, Mapping Monitor, Transport & waveform, 12-band analyzer, Preview setup,
Experimental, Effects & layers, Catalog & techniques, Results & review, and
Diagnostics & logs. They retain one controller/body each. Layout changes retain
the renderer's context, clocks and active editing state. Existing GPU feedback
is resampled when its viewport changes rather than cleared solely for resizing.
Normal scene/audition boundaries retain their established history semantics.

**Session & worlds** uses the current Main/Experimental catalogs and actual
selected session/track. **Open**, **Save** and **Setup** use the existing session
workflow. The saved-session and color-preset lists show actual JSON files;
double-clicking a listed file opens it for inspection, while **Open** or the
inspector's **Load** imports it. Historical catalog entries remain searchable.
Only available archived captures are thumbnails, with their path identified;
other rows honestly have no assigned capture. No new thumbnail pipeline or
future-scene inventory is implied.

**Color Inspector** initially prefers the selected scene's source pigments.
An explicit compatible shared target stays selected. Pigments, Palette timing,
and Presets & reset retain the original hex/wheel/value, gradient blend positions,
named setups, Hold/Cycle, scoped resets, revert and preset operations. Scroll
within compact tools for the remaining controls. Invalid unsent field text stays
at its target during docking and scope changes; the last valid colors keep
rendering. Validation errors appear beside the editing controls. Source swatches
describe pigments before shading, not measured output pixels.

**Audio Tuning** retains Follow/Pin, actual form and target selectors, every gain,
listening range, exact frequency value, profile operation and authored promotion.
Controls contains the scrollable sliders, resets and Profiles & authored;
Listening & FFT contains the original spectrum and detector views. A profile
save is separate from **Save Authored**, which still requires the existing scoped
acknowledgement and reports its actual destination. One-Hz positioning does not
add FFT resolution. Question-mark help retains full explanations and dependencies.

**Mapping Monitor** shows bounded history of actual analyzer bass and a labelled
CPU submitted input. Full values retains all original scope, revision, gain,
director, dependency and history-owner telemetry, with horizontal scrolling.
These traces are not GPU pixel measurements or instrument classification.

The bottom transport retains **Start, Pause/Resume, Stop, momentary Hold, BONK**
and **Normal/Instant**. BONK availability follows the existing player; a held
single-form preview can legitimately disable it. Source, quality and layer
changes prepare the next launch. Compatible colors and tuning edits remain live.
New workspace previews default to **Real time**. Loading an existing session
restores its saved speed; the original diagnostic Studio retains its 12× default.

The file waveform is a bounded min/max envelope of actual decoded 16-bit PCM.
Its cursor follows the shared analyzer's PCM position; this retained Tk view does not seek. Test
track replay remains silent. Live input shows bounded PCM snapshots with gaps
between snapshots. Synthetic, stale or unavailable PCM is labelled unavailable.
The analyzer shows exactly twelve existing FFT ranges, normalized mean magnitude,
actual range edges and under-resolution marks; absent/stale spectra show N/A.

Outside text fields, sliders and native widget activation, **Ctrl+Enter** starts,
**Ctrl+P** pauses/resumes, **Ctrl+Shift+S** stops, **Space** BONKs and **Shift** holds
while pressed. **Ctrl+S/O/N** are the existing session Save/Open/New actions.
Typing, selection and tuning arrows keep their native editing behavior. Space
on a focused button activates that button once. Focus loss, docking and shutdown
release held controls and slider repeats. Tab/Shift+Tab reach controls and help.

Layout saves separately to `work/studio/workspace-layout.json`: visibility,
areas, tab order, selected tabs, dividers and floating geometry. Changed/missing
monitor layouts clamp windows to an available monitor, including negative monitor
origins. **View > Reset layout** changes layout only, preserving session, colors,
profiles and tuning. Invalid layout files get an explicit status and can be reset.

For review, start a real input or decoded track, detach/redock the Visualizer,
float a tool and edit it, hide/restore panels through View, try Follow/Pin and
Pause/Resume, then restart the shell to check layout. Review hierarchy and control
access before approving finishing work. Source-bound measurements, screenshots,
failed trials and validation limits are in
[the prototype handoff](docs/agent-notes/unified-studio-prototype-20261005.md).

## Operating Studio

### Organization contract

**Build & preview** presents only canonical Main-approved forms, currently 30
including Galaxy and the three Fractal forms. Approval comes from `renderer.LIVE_FORMS`, also used by the
player, rather than catalog membership or an internal review score. The existing
top-level taxonomy is **Organic**, **Geometric**, **Cosmic**, and **Elements**;
Elements has its own categories. Filtering happens at every leaf, hides empty
categories, and parks a branch's authored cycle when excluded descendants could
otherwise leak into it. Adding a candidate under an approved parent grants no
approval to the candidate.

**Experimental** replaces the displayed **Cymatics** tab name. It has independent
world/form selectors and Start/Stop controls. Choose **Cymatics > Water - Resonance
basin** for all existing Drive, Water basin, Style & bands, oscillator, band,
monitoring and live tools. Choose **Experimental / unfinished** for the legacy
transition study, Lodestone Field, Stormglass Network, or Folded Aurora. Basin
uses its Drive Input selector; other experiments use the ordinary input/replay
controls above. A blank Experimental form cycles its selected branch; there is
no combined Basin/remake playback mode. Source/track/replay settings are shared
with Build & preview; the two visual selections are remembered independently.

**Library** retains the complete catalog, effects, techniques and stable IDs.
Choosing a Library world opens its appropriate Main or Experimental tab and
does not start preview. Effects & layers follows the active visual selection;
**Back to preview** returns to its tab. Merely populating selectors or searching
Library does not change project settings, layers, colors, or files.

Saved v1-v3 projects keep their original visual IDs and settings. The `cymatics`
catalog path and existing Cymatics controls remain; only the tab label changes.
The previous format did not store notebook tab IDs. Old projects route by their
stored visual path/state; current version 5 saves retain `selection_scope` and
`studio_selections` so both visual selections survive reopening. Invalid paths
show a load error rather than silently selecting the first Main form. Loading
does not rewrite the source project. The established saved-Cymatics muted/restart
reset policy still applies.

Keep this organization when extending Studio. The focused, offline guard is:

```powershell
.\.venv\Scripts\python.exe -X utf8 app\visuals\studio_test.py --organization-test
```

It uses a withdrawn Tk window, blocked child/GPU/device entry points and temporary
saved-project fixtures. It does not run a live preview or certify audio quality.

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
to the next run; declared color controls, scoped Audio Tuning and compatible
pair audition can update the running preview. Close the visual window for a normal finish and complete
metrics. **Stop preview** terminates only Studio's child; partial logs/captures
remain and final metrics may be incomplete.

### Main Audio Tuning and Mapping monitor

1. In **Build & preview**, leave the top World selector blank for Main Blend,
   or hold an approved form. Choose **Test track** and an existing decoded WAV
   for repeatable review, then **Start preview**. Audio Tuning supports the 30
   canonical Main forms, including Galaxy and Fractals, and their declared targets.
   Experimental/Cymatics remain excluded until promoted.
2. Open **View > Audio tuning…**. With **Pin editing destination** off, the
   dialog follows actual playback in Main, held forms and supported sequences/
   family cycles. Its Playback line identifies outgoing/incoming forms during
   a transition. Choosing another form automatically pins that editing
   destination; playback keeps going. Uncheck Pin to resume following.
3. Choose a target in the second selector, then adjust its named response gains
   or enable its available listening ranges and move their start/end Hz sliders.
   Controls apply to actual declared consumers; labels explain quiet bases,
   timers and shared dependencies. Different targets expose different controls.
   Edits enable **Live override** and apply after a matching acknowledgement.
   Scroll the control area below the spectrum to reach the remaining roles.
4. The full spectrum is measured shared analyzer input. Colored range overlays
   show enabled/configured windows from the existing FFT; displayed bin spacing
   limits frequency resolution. Range OFF retains the original signal.
   Inactive or stale targets do not show consumer activity. A selected range is
   not an instrument classifier, and a shared spectrum is not evidence that an
   inactive effect is drawing.
5. **Back to authored**, or turning Live override off, restores the selected
   target's saved authored baseline. It does not reset other forms, targets or
   colors. **Save profile** stores a named target profile; **Load profile…**
   applies a temporary override without rewriting authored settings.
   **Save Authored: form / target** explicitly promotes only that named
   destination. Wait for its current acknowledgement and matching values;
   stale, pending or unsent edits cannot be saved. The status names the file
   and confirms the running-preview acknowledgement. Audio profiles/authored
   files are separate from Color Inspector presets and **File > Save session**.
6. Pin **Transitions**, then select **World warp** to configure it even while
   another recipe plays. The row is marked inactive/queued; its configuration
   can be acknowledged without claiming active consumer output. Form, target
   and role settings remain independent, including shared-technique instances.
   Switching destination cancels a held key or pending gesture and parks unsent
   edits at their original owner. On returning, submit the retained values
   (adjust a control) and wait for their acknowledgement before saving.
7. Open **View > Mapping monitor…** alongside Audio Tuning. It follows the
   selected editing scope and shows source identity, endpoint/recipe progress,
   analyzer bands, actual CPU inputs/gain submissions and director state.
   Display-formula proxies and selection weights are labelled separately.
   These are CPU telemetry, not GPU readback, pixel brightness or a performance
   certificate. **Live monitoring (read only)** pauses the monitor display.

#### Compatible decoded pair audition: Repeat and Return

With a running Main-scope **Test track** preview, open **Effects & layers >
Transitions**. Enable **Chosen scene pair** and choose two different compatible
Main forms; a validated example
is **Root blossoms → Planet Canvas** with **Planet Canvas pull / absorb**
(`tr_planet`). Add/select that transition row and use **Isolate selected
transition** so the intended recipe is chosen. Set **Rest (seconds)** and
**Handoff (seconds)**, then click **Preview pair**.

For **Repeat**, click **Preview pair** again with the same settings: it resets
the same decoded passage, seed and numerical analysis history in the existing
preview process. There is no separate Repeat button. **Return to selected
scene / Main** restores the parked source position and CPU scene/RNG state.
Shared Echo/Enveloper GPU history restarts at this ownership boundary; Return
does not restore its previous pixels/history exactly. Matched live-input
audition is rejected because live input cannot replay the same passage; the
live preview is retained. Decoded review is silent.

Robert accepts these implemented controls as a development checkpoint with
caveats. A transition hitch remains to investigate; a 12× preview is not proof
of real-time smoothness. See the [handoff](ZERAWAVE_HANDOFF.md#current-main-audio-tuning-checkpoint)
for evidence, preservation and remaining artistic/listening/performance limits.

### Cosmic Galaxy: Galaxy Odyssey review

Galaxy is approved for Main. Launch
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
Galaxy reveal; these historical fixtures are compatibility evidence. Galaxy now
belongs to Main's canonical roster; all three Envelopers remain off by default.
See `work/galaxy-journey-review/` and the
[task evidence](docs/agent-notes/galaxy-stellar-aviary.md). Review the motion and
music yourself; automated checks do not establish artistic acceptance.

### Effects & layers

The existing tab has six sections. These organize controls, not independent
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
- **Transitions**: compatible scene relationships, chosen-pair audition,
  recipe isolation and Return to the parked preview.
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
   target used in Main, including Galaxy structure. **File > Save session**
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
preview. Effect lists, row amounts, material isolation and the Planet palette
selector still apply on the next preview. Scoped Audio Tuning and explicit
compatible pair audition use the running preview as described above. Layer-playback
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

Current Studio loads versions 1–5 and saves version 5. Version 1's flat state
migrates to the selection path; older profiles, holds and color roles remain
compatible. Version 5 includes composition/media refs; library/layout versions
are separate. See [media storage](docs/STUDIO_MEDIA_COMPOSITION.md#library-sessions-and-failure-handling).
The optional `planet_palette` field stores `authored` or `soft-dream` separately
from layer profiles. Files without it load as Authored; unknown values are
rejected. New session resets it to Authored. Current saves use version 5.
The optional `material_isolation` map stores world-to-material holds separately
from the original layer profiles; absent maps preserve old playback exactly.
Preview commands resolve the override through the existing profile machinery.
The optional `color_overrides` map stores stable target and role assignments.
Missing targets/roles use immutable authored defaults; sessions without this
field keep their previous appearance. Current saves use version 5.
Sessions store settings/external source paths, not audio files or shader code.
Save/Save As copies used managed artwork to a sibling `.assets` folder. Original
media stays external; moved projects need available sources or explicit relink.
Silent diagnostic replay still needs a decoded WAV.

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
Use **Experimental > Cymatics > Water**, then its Drive Input selector for oscillator, track or loopback; the general
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


## Development playback controls and Fractal

The single Start / Pause / Stop / Hold / Bonk control set appears in the existing
preview area for both Main and Experimental. Pause freezes drawing and replay
clocks; Resume drops stale live packets and transient replay input. Hold is
momentary: it parks selection while musical/material motion continues. Releasing
the mouse or Shift, losing editing focus, changing scope, and closing a preview
release Hold. A single held form has no next destination: Bonk stays disabled.
Normal and Instant use the existing Player transition semantics; a development
sequence uses its existing selection/transition route.

Studio keeps Ctrl+S for Save session. Ctrl+Shift+S stops the owned preview,
Ctrl+Enter starts, Ctrl+P pauses/resumes, Shift holds, and Space Bonks. Playback
keys leave text, combobox, slider and spinbox editing alone. Session Save/New/Open
retain their shortcuts. Space is consumed before a focused button's default
binding. The output window uses the same playback bindings; Escape closes it.

<a id="resource-telemetry-and-pending-qt-view"></a>

### Resource telemetry

The Qt **Resources** dock described above is implemented in the October 5 additions
candidate. **Development diagnostics** also retains the legacy report route.
Qt Diagnostics exposes logs/help. Mapping Monitor's **CPU submitted** values are
audio mappings, not CPU usage.

Enable Development diagnostics for asynchronous nominal 1-second resource
sampling. Presentation intervals/FPS are swap-return/caller intervals, not scanout.
CPU process is percent of one logical core (can exceed 100%); system CPU covers
the machine. RAM process means working set. GPU utilization and VRAM belong to
the identified rendering adapter; process VRAM and lightweight GPU draw timing are unavailable.
Missing/stale readings say unavailable. Actual timestamps and instrumentation
limits are retained in the report. Background load, thermals and power are not
controlled. This display gives no FPS guarantee.

The Qt collector identifies renderer, GUI and control-owner roles by PID and
deduplicates shared PIDs. Rendering-adapter name matching must be unique before
device readings are shown; missing/ambiguous identification stays unavailable.
Visible/hidden overhead evidence belongs to the additions report. GPU draw
milliseconds still require a separate measurement; swap return is not scanout.

Graceful Stop or normal completion writes `session-performance.json` into that preview's
results directory. **Open Latest Results** opens the directory. Reports bind source,
run, source/audio hash, speed, seed, relevant settings, actual dimensions,
frame-time distributions, capped hitches and resource history. Private audio is
not copied. GPU query timings require the separate scoped measurement harness.

In Main choose **Fractal** → **Tidal Strata**, **Recursive Atrium**, or
**Honeycomb Garden**. All three now belong to the 30-form Main lineup, playlists and random selection.
Test track replay is silent; choose Real time for normal-time review. Synthetic
preview supports visual tuning but has no PCM/selected-bin measurements. Live
system audio uses the existing source/capture path. Use View → Audio tuning and
Mapping monitor, and Palettes, for the same scoped inspection/save workflow.
Explicit saves, run/session/form/target/revision guards and parked edits remain.

Mineral Lamellae and Recursive Pulse are compatible with all three Fractals.
Their amounts are in Effects & layers; authored amounts differ per form. Each
has independent form-owned Audio Tuning. Lamellae's source pigments are shared
across the three forms. Landscape/atrium gradients and garden honey/petals have
named authored families. Unedited targets evolve slowly; explicit edits and
Hold park a target's authored palette evolution. Color edits retain growth,
travel and audio history. Reset colors resumes the existing authored clock.
Form entry/rewind resets the bounded growth/travel clocks; there is no
reaction-diffusion simulation or neural model. Low-rate recovery advances at most .25 s
per draw, so it cannot queue an unbounded catch-up. Pause does not advance it.

A running Experimental preview cannot audition a Main pair. Stop it and start a
Main preview first; this preserves the owned shader/resources and Return contract.
A forced termination during a blocked startup may have only `run.log`, rather
than a completed performance report.

Frozen A/B comparison presents every decoded analysis chunk at its requested real-time pacing.
It can run longer under overload; it does not drop rows to catch up. Ordinary real-time preview
retains its existing wall-time catch-up. A/B keeps its existing comparison manifest/metrics;
its paused/live-inspector actions remain unavailable during the owned comparison run.

Session Performance Reports distinguish **launch settings** from subsequent live
edits. `launch_settings_sha256` covers the launch selection, layers, source and
speed, color overrides, palette/isolation choices, Galaxy entry/seed/visit and
Planet pilot options. It is a launch-only identity, not a hash of the whole evolving
session. `applied_edit_trace` records successfully applied Audio Tuning and color
revisions with run/session/form/target ownership, song time, wall time and settings
snapshots. Pending, rejected and stale edits do not count as applied. The trace
retains the latest 256 events; its total count, dropped count and cumulative chain
hash preserve that limit explicitly. Open Latest Results opens the owned run folder.

Decoded Fractal reports retain actual analysis values while marking
unimplemented Planet-flight telemetry and material-mix capture metadata unavailable.
An unavailable shader uniform is never presented as a measured zero. Captures use
the current framebuffer size and an owned readback target, released on resize/exit.


### Fractal integration and structural transitions

Main includes Tidal Strata (41), Recursive Atrium (42) and Honeycomb Garden (43)
under **Fractal**. Stable `fractals` paths, role IDs and separate authored profiles
remain. Earlier sessions selecting these under Experimental migrate that selection
to Main while preserving colors, layers and audio settings. Other experiments remain
outside Main. One shared renderer program handles Main/Fractal entry, exit and pairs.

In the existing transition controls select two Main forms and isolate **Branching
Iris** (`tr_branch_iris`) or **Flowing Fold** (`tr_flow_fold`). Iris opens recursive
radial forks; Fold carries endpoint geometry through alternating flowing ribbons.
Both support any two different Main forms, including Fractal. Audition/Repeat uses
the existing decoded or synthetic source; Return restores the parked preview.
Each recipe has independent Audio Tuning for Bass, Flux, Movement and Impact,
including selected-frequency ranges. Duration scale is a separate CPU timer control;
its effect applies on the next ordinary Main transition, whereas explicit audition
keeps its requested duration. Inactive recipe edits are retained without claiming
current contribution. Both transitions inherit endpoint pigments: their spatial
transport adds no independent color-bearing overlay. Save session remains explicit.

Before the measured performance fixes below, the first observed compile of the revised combined shader took about 181 seconds
and the following warm creation about 0.36 seconds on this laptop. Cache state was
not controlled: this is no demonstrated cold-start improvement or FPS guarantee.
Task-bound evidence and expanded-lineup measurements are in
`work/fractal-main-transitions-04/`; artistic acceptance remains Robert's.

Pre-fix first-source compile evidence also reproduced about 190 seconds and 13.2 GiB peak process working set; warm runs were about 0.32 seconds for program compilation. The tested uniform-bound loop did not improve this and was rejected. These are historical baseline results; the measured performance results below supersede the current-cost claim.


### Measured performance controls — October 4 fixes

New previews default **Captures** off. Existing sessions retain their saved
capture choice. Enabled captures keep GL readback on the graphics thread and
send statistics/PNG work to one bounded writer (two waiting frames). A full
queue drops the new capture; `captures.json` reports drops/errors. Closing a
preview normally drains its accepted captures. Stop during a blocked native
operation can still leave partial evidence.

**Build & preview → Preview quality** applies to the next launched preview:
**Full quality (100%)** is the default and retains the full framebuffer workload.
**75% scale (softer detail)** and **50% scale (softer detail)** reduce each render
dimension and linearly upscale the final image. At 1280×720 they render 960×540
and 640×360 respectively. These are explicit appearance tradeoffs, with no
adaptive switching or scene-density reduction. The report records the scale,
actual internal size and shader resolution. Main keeps full quality unless an
explicit environment override is provided; no lower tier was adopted as its default.

For review, run `run_development_studio.bat`, choose a held **Waterfall**, **Liquid dyes**,
**Ghostlight Marsh**, or **Crystal Cavern**, select a Test track and **Real time**, choose
**60 seconds**, leave Captures off, then Start preview. Compare Full/75%/50%
using the same track prefix, seed and settings. **Main blend** checks ordinary
director behavior. Transition controls can isolate Citadel ↔ Crystal Cavern,
Waterfall ↔ Geometric corridor, and Root blossoms ↔ Tidal Strata with Optical
crossfade, Branching Iris or Flowing Fold. Audio Tuning and Palettes remain live;
Return/repeat retain their existing ownership and history rules.

The existing responsive loading notice remains through first presentation.
The shader is still one integrated program; all Main families are compiled
before playback. On the measured NVIDIA driver, a limited-inlining policy cuts
cold compiler memory/time. Other vendors retain their compiler policy. Cached
startup is much faster than cold startup. Full-quality expensive scenes and
crossfades still miss 60 FPS; GPU time and silent replay are not scanout or
continuous listening evidence. See
[the task results](docs/agent-notes/performance-fixes-20261004.md) for measured
conditions, numerical image differences and known limits.

## October 6 resolution controls and Audio Hub

Qt Settings > Visualizer Resolution and the Visualizer context submenu share
640×360, 1280×720, 1920×1080, Native and integer Custom choices. Existing Quality
continues until an explicit resolution choice; fixed choices use aspect-fit bars,
Native follows physical framebuffer pixels. A failed request retains the accepted
policy. Resources offers Simple CPU/GPU/Mem/FPS and Detailed views; device GPU
utilization is device-wide and swap-return FPS is not measured scanout.

Settings > Audio and Session Waveform share Device Listening / Audio File source
selection and import. Use Waveform Open/Play/Pause/Stop/Repeat/Mute for WAV/MP3
files; visual Start/Pause/Resume/Hold/BONK remain separate. Device listening opens
no output stream. Muted files continue analysis; file Pause freezes the audio
playhead independently. Invalid import retains the source. Current Qt imported
files have a whole-song waveform with click/drag seek and 2×/4×/6×/12× forward/
reverse scan; Play restores 1×. Scan changes pitch. Device Listening retains a
recent envelope without seeking. Output volume/mute leave analysis unchanged;
analyzed/raw waveform drive remain distinct. See [timeline](docs/agent-notes/audio-timeline-20261007.md)
and [volume/raw drive](docs/agent-notes/audio-volume-drive-20261007.md).

SoundFile 0.13.1 is recorded in the optional Qt requirements; PCM WAV fallback
remains available without it. Legacy Experimental routes retain separate audio
semantics: stop shared audio before entering them; shared-audio changes while
such a preview runs are rejected. Matched source-rewind audition is unavailable
on this live PCM route. Read [resolution checks/limits](docs/agent-notes/studio-resolution-controls-20261005.md)
and [Audio Hub checks/limits](docs/agent-notes/studio-audio-hub-20261006.md).


## B2 native raster/editor continuation - 2026-10-08

The B2 development candidate retains128-pixel immutable C++ tiles, copy-on-write
history, exact region editing, B1 transactions, revision-pinned portable PNG saves
and the existing output publication path. The continuation corrects redundant
CPU presentation refresh, adds an optional exact float32 region kernel, and hosts
renderer-owned GPU projection/composition in the same Qt authoring Canvas.
Integer-aligned physical native pixels use GPU composition and damage; filtered,
rotated/fractional views retain exact Qt reference sampling with cached GPU display.
There is no mandatory display-loop readback. The Layers editor label distinguishes
these routes; `ZERAWAVE_EDITOR_GPU=cpu` selects the compatible CPU editor at open.
Native initialization failure also preserves a usable CPU Canvas.

This is a reviewable candidate, not Robert acceptance or a universal performance
claim. Latency, memory, failures and remaining limitations are bound in
`docs/agent-notes/b2-tiles-20261008.md` and `work/b2-completion-20261008`.
Build, ABI, resource bounds and secured fallback are in the
[B2 implementation contract](docs/NATIVE_RASTER_B2.md).
