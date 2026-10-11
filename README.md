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

Current accepted/pushed finishing development checkpoint:
[`f3d414be7ee380a38865c3579c057597dbb5fb06`](https://github.com/realRMars/ZeraWave/commit/f3d414be7ee380a38865c3579c057597dbb5fb06).
B1 transactions/Undo/Redo and output before PNG durability, B2 optional C++ tiled
resources/history/editor projection, storage recovery/normal close, ordinary image
Save and finishing controls are implemented. The earlier `0fb4c3f` recovery is
historical. [Current handoff](ZERAWAVE_HANDOFF.md#october-10-drawing-and-storage-development-checkpoint)
and [dated results](docs/agent-notes/b2-tiles-20261008.md) retain measured tails,
rejected-stroke redraw, owner-death and unrun broad/product/capacity limits.
[Native setup/fallback](docs/NATIVE_RASTER_B2.md) explains optional local DLLs;
acceptance is not a release or universal responsiveness guarantee.

Approved direction retains Qt, Python authoring/control and the existing GPU
renderer. **[B3 media foundation](ROADMAP.md#b3--bounded-media-foundation) is next,
approved but not implemented**: fair bounded decode service, generations,
direction-aware prefetch and timestamp-correct editor/output ownership.
Then a manual whole-existing-product migration assessment covers worlds,
Visualizer, audio and older systems, followed by remaining appropriate migration
before unrelated expansion. ROADMAP is the sole plan; historical B4–B8 proposals
are subject to that assessment. Capacity Passes 2–4, higher counts and storage
location/relocation remain separate. No dispatch follows documentation readiness.
