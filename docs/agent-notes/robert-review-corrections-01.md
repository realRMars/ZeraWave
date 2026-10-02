# Robert review corrections — ready for independent critique

Code and evidence are complete for the eight assigned correction areas. No commit, push, staging, Main expansion to Galaxy or Experimental remakes, shared planning edits, package installation or release build. HEAD remains312287e. This is a builder handoff, not artistic acceptance or a score.

## Visible result and controls

- Original Magnetic Bloom32, Arc Constellation33 and Auroral Veil34 are restored in Main and Plasma35. All three match the verified prebatch Git shader exactly in matched GPU pixels. Lodestone Field38, Stormglass Network39 and Folded Aurora40 remain separately named Experimental/unfinished, accessible in Studio; their geometry/resources/role IDs remain, with their own live pigments and optional original tints. Original Main colors exclude remake pigments. Galaxy36 stays outside Main; three Envelopers remain off.
- Cavern retains cached analytic geometry, irregular quartz/fluorite forms, local traveling accents/floor spill/settling and placement. Authored chromatic pigments visibly evolve during a normal visit; explicit palettes/manual edits still hold/reset through the existing inspector. A shared4.9sin(.20z) camera/formation axis provides smooth alternating44.4degree headings. Final clearance check458348sampled configurations minimum margin.02819. Ordered quiet/active/release frames show red/blue→green chromatic change and continuing arches/placement.
- Citadel keeps varied towers/culling. A common tower descriptor anchors flag masts, coherent free-end wind/hit flutter, rooted vivid beams and world-space launches to actual roofs. Hoops rotate/precess as survey rings. Lower-planet spherical material/cloud motion is authored. Fireworks have a narrow launch, local luminous peak,20spark rays with individual sparkle/fade, four bounded events and depth rejection. Ordered15Hz frames160–167 show a localized orange/white peak opening into sparks above the selected roof, with no global flash. Fine motion needs full-size review.
- Marsh keeps its accepted original camera, density/history and ground reflection behavior. Markers are slightly thinner with varied widths; palette families begin blending earlier at normal time. The first implementation accidentally moved Fog's camera while replacing Cavern expressions: that scope error was found by preservation, fixed, and only Marsh/mist evidence recaptured. Corrected ordered images show quiet dark markers and evolving colored local fog/light.
- Molten keeps dark terrain, authored colors and beat movement. A bounded0–1development state grows the narrow trunk into four staged snaking/widening branches while present, freezes absent and resets on rewind.32musically weighted rising embers span the screen. Ordered quiet/active frames show landscape coverage widening; fine particles are harder to judge in compact images. Main presence routing remains checked.
-19stable Transitions entries expose optical fade, world warp, Planet Canvas pull/absorb, four legacy physical relationships, seven native family melds, the three accepted regional techniques, material meld and preserved study. Compatibility is explicit. Add/enable/order/Save/Selected together/Cycle use the existing list; transition rows do not become blank material/FX cycle steps. Together chooses one compatible recipe per handoff; Cycle follows compatible transition order. Material meld uses the existing within-scene material workflow; study remains a labeled Demo under Experimental. Main can use compatible legacy recipes alongside the new three without a fixed itinerary.
- Studio Effects & layers→Transitions has From/To, rest/handoff durations, Preview pair, isolation/restore and return to selected scene/Main. Library Add to scene works on catalog entries. Pair settings/isolation survive v1–v3 migration; held scenes stay held until a pair/family/Main is selected. The original Build & Preview Transition world row is removed, with old selection['transition'] migrating to the preserved study.
- Director detects an actual recent A→B→A selection, keeps musical/beat-quantized opportunities and shortens return rest budgets to52%minimum/50%maximum. It does not ban callbacks or add hard cuts. Actual unforced seed173 using verified45–105sWarbotJazzfeatures selects Firescape at.013s→Cavern14.82s→Firescape37.94s(completed45.07s; min8.99s)→Corridor55.69s. Initial Firescape held14.81s; returned Firescape rests~10.62s before its onward handoff, which is still in progress at clip end. Separate26→22→26pair is explicitly controlled.

## Reviewer path

Start with work/review-corrections-01/review-index.json. For each assigned scene inspect its preferred held and music APNG/sheet, using corrected Marsh names. Then inspect natural-main-reprise and cavern-pair-return, plus named facet/mist/planet-pull/fade examples. Do not use retired marsh/marsh-music/pair-legacy-mist files as final art evidence. They are retained to preserve the scope failure.

Launch .venv\Scripts\python.exe app\visuals\studio.py; Load a review-session-*.json. Normal review sessions run the WAV from zero at real time; saved music evidence reuses its verified45–105sdecoded features and is silent. Main Studio uses a fresh random seed; the saved natural Main fixture uses173. Single Experimental forms and original Plasma have separate session files. In Transitions select a row, enable Chosen scene pair, Isolate, then Preview pair. Incompatible explicit pairs produce a compatibility message; Main chooses a compatible fallback where necessary. Source pigments remain in the existing Palettes inspector.

## Actual checks

- Final standalone PASS: transition_controls_test.py; main_director_test.py(4hnumeric/all26forms/378choices/styles0–3); mineral_resonance_test.py; citadel_response_test.py; marsh_response_test.py; molten_response_test.py. Logs and exact source hashes are in final-checks.json. Python AST parse14production files and gitdiffcheck exit0. No pytest or new test framework.
- Actual Tk Studio:19entry picker, pair isolation, incompatible status, saved/validated command, LibraryAddtoScene, restore/reset; studio-transition-check.json. Full historical Studio/whole application suite was not run.
- GPU640x360 matched-source pixel comparisons:19unaffected states all exact; original32–34 versus verified prebatch Git all exact. Corrected Nebula also exact at24s and65s. Preserved initial large Nebula mismatch(max78,671734channels) is in gpu-checks-before-fog-camera-fix.json; the corrected final result is gpu-checks.json.
- Native readiness: controlled.7snotice cleanup reproduced one350msfailure with old unpumped wait; fixed event-pumped path passed13during-pause probes, keeping1s/2sowned-process limits. Exact-source warm close178ms. Final shader cold compile103.853s, directly measured notice close64.4ms;166native probes all passed in the corrected Fog run, including post-ready. Music run645probes all passed. Earlier initial pre-ready failure and historical post-cold-ready failures are preserved. The earlier~.78sready-to-return subtraction used two timing origins; it is not a direct.78scleanup measurement. The blocking wait was reproduced independently.
- Normal-time evidence: original14sequences completed; missing6music/Main-return sequences completed; only3invalidated Fog cases replaced. Capture/backbuffer precedes swap. Decoded feature source and WAV hash verified; no new audio normalization/analysis changes. Original control pack window failure remains, not hidden by later warm tests.

## Measured cost and limits

1280x720 RTX3070Laptop, uncapped,6warmups+30retained samples. Current loop includes mapping/allpasses/draw/swap/poll/finish and excludes readback. Prior column is a matched-uniform/resource shader draw, not complete previous CPU/cache behavior. Repeated earlier costs are retained; no GPU-clock control or attribution of the run-to-run variation is claimed. Compare source/time/metric conditions stated in each report. No displayFPS/device-floor guarantee.

| Case | Current GPU ms median | Current loop ms median | Prior shader draw ms median |
|---|---:|---:|---:|
| cavern | 18.06 | 20.57 | 18.07 |
| citadel | 12.13 | 14.45 | 10.60 |
| marsh | 9.02 | 11.45 | 8.93 |
| molten | 6.03 | 8.15 | 5.09 |
| original-magnetic | 8.06 | 10.15 | 6.98 |
| original-arcs | 7.07 | 9.05 | 6.28 |
| original-auroral | 4.84 | 6.75 | 3.66 |
| cavern-citadel | 18.18 | 24.00 | 19.79 |
| molten-sea | 6.11 | 11.59 | 5.80 |

Geometry caches/history remain bounded; numeric4hsoaks do not establish multi-hour rendered variety. No supported continuous animation-player inspection or AV listening. Compact ordered images and a full-color Cavern JPEG were inspected; full source images/APNGs are available for the independent critic and Robert. Remaining review risks include fine fireworks/ember visibility at full size, sustained craft/variety and subjective musical connection. Earlier Marsh tiny strict failures and Arc/cold lifecycle failures remain recorded under their original conditions; this pass does not erase them with different-condition checks. No natural live-loopback or multi-hour render soak was run.

Independent critique is now requested at the parent gate>=7.5; Robert owns acceptance. No further scene assignment started.
