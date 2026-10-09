# ZeraWave

ZeraWave is a Windows music-reactive visualizer. The current checkout is the
development source; the portable preview is a preserved, older checkpoint.

- [Player instructions](docs/agent-notes/player-checkpoint-2026-10-03.md)
- [Development Studio instructions](DEVELOPMENT_STUDIO.md)
- [Prioritized roadmap](ROADMAP.md)
- [Visual identity](ZERAWAVE_VISUAL_IDENTITY.md)
- [Technique ownership](TECHNIQUE_LIBRARY.md)
- [Current handoff](ZERAWAVE_HANDOFF.md)
- [Historical record](docs/history/README.md)

Use `run_zerawave.bat` for the player and `run_zerawave_studio.vbs` for current
Qt Studio. `run_qt_studio.vbs` remains a diagnostic Qt entry;
`run_development_studio.bat` retains Tk tools. Requirements are in
[requirements-qt-studio.txt](requirements-qt-studio.txt). Studio is currently a
development/review tool; expanded authoring is the approved direction, not a
shipped paid Studio offering.

For agents: read [AGENTS.md](AGENTS.md), then the current handoff and roadmap.
The Overseer maintains shared planning; workers own their assigned changes and
may keep optional [task notes](docs/agent-notes/README.md). New visuals are
reviewed through the existing Dev Studio before approved Main integration.
A scene assignment covers the assets, movement, reusable techniques and palettes
needed for the complete experience. Historical plans, research-stage restrictions
and completed task notes do not narrow the user's current brief.

Galaxy Odyssey is accepted and included in the 30-form Main roster, alongside
Tidal Strata, Recursive Atrium and Honeycomb Garden. Color
Inspector and Studio organization are implemented; the three Envelopers remain
off by default. Robert accepts the implemented Main Audio Tuning development
checkpoint with caveats and passed the measured-performance development
checkpoint for publication on October 5. Water/capture/startup improvements,
compiler tradeoffs and remaining real-time limits are recorded in the handoff. See [Studio controls](DEVELOPMENT_STUDIO.md#main-audio-tuning-and-mapping-monitor)
and the [current checkpoint and limits](ZERAWAVE_HANDOFF.md).

Recovery [0fb4c3f](https://github.com/realRMars/ZeraWave/commit/0fb4c3fa28632a6aaedb472be50b1837926b9caa)
includes Qt controls, audio timeline/Band Analyzer, media composition and raster
corrections. **The editor remains unaccepted**, with transaction/recovery/input
review problems. See [Studio](DEVELOPMENT_STUDIO.md), [media editing](docs/STUDIO_MEDIA_COMPOSITION.md)
and [current handoff](ZERAWAVE_HANDOFF.md#current-recovery-checkpoint-and-b1-handoff).

B1 raster transactions/Undo/Redo and publication before PNG saving are implemented
in the **development candidate**, awaiting user acceptance. See [B1 results](docs/agent-notes/b1-raster-20261008.md)
for review steps, source identity, evidence and limits; the recovery commit alone
does not contain B1.

Approved direction retains Qt, Python authoring/control and GPU rendering.
[B2](ROADMAP.md#b2--c-tiled-raster-resources-copy-on-write-history-and-incremental-compositing)
provides experimental C++ tiled raster resources, copy-on-write history and
renderer-owned editor compositing, preserving B1 transactions/saves. Focused
selection/clipboard/Smudge and usability/performance corrections are implemented.
[Native build/fallback](docs/NATIVE_RASTER_B2.md) explains optional setup; DLLs
are not included. October 9 publication is a development checkpoint with review
and performance limits retained in [actual results](docs/agent-notes/b2-tiles-20261008.md). Media scheduling, audio graph, timeline/export and distribution remain later
stages in ROADMAP, the sole plan.
