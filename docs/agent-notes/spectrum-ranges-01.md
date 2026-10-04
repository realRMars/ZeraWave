# Living Artifacts: simultaneous spectrum windows

Authorized small UI change after Robert accepted target-switch restoration.
Flux and Sparkle now retain separate gold solid / blue dashed window brackets,
boundaries, named lanes and a legend. Their overlap remains visible in both
lanes. Focus adds an editing marker and thicker lines to that window without
hiding the other enabled window. The cyan measured spectrum remains visible.

The previous display merged enabled/ready windows into one amber mask; it could
not preserve their identities. The new annotations show acknowledged settings,
not unacknowledged local slider positions. OFF ranges are hidden and labeled
as original-feature routing. Matching-analysis waits use dotted lines and an
explicit waiting label; inactive/stale ranges are hidden and labeled. No FFT
snapshot hides every window overlay. The original Starfield detector-weight
display returns when switching away from Living Artifacts.

Reusable UI component: `SpectrumRange` plus the existing `SpectrumWidget.update`
optional `ranges` argument. It accepts named display windows and uses one fixed
pool of32 canvas items for up to8 windows. No FFT, capture, descriptor, analyzer,
transport, profile schema or renderer changes. Existing callers retain their
three-argument update route.

Evidence: `work/spectrum-ranges-01/review-index.json` binds the pre-task snapshot,
exact scoped diff, sources, checks and preserved prior evidence. HEAD remains
`0342e518a7bd2c521416e8027a7920668fc5ee51`.

Executed checks:

- `spectrum_ranges_test.py`: native hidden Tk9.0.4,900x860 allocated client,
 868x150 canvas. Overlap/nonoverlap, both enabled, each disabled, both disabled,
 all four Hz-field focus routes, unchanged ACK geometry during pending edits,
 waiting/inactive/stale/no-snapshot states, no target-return leak, actual local
 listening/tuning ACK methods, native1Hz tap, Save Profile/Save Authored,
 generic3/8-window drawing and500 stable redraws passed.77 total canvas items;
 profile/authored fixture bytes unchanged after redraw/focus/state tests.
- `audio_tuning_switch_test.py`:107 switches across24 targets;386 reachable row
 cases,748 navigation events,107 taps, hold/debounce cancellation and48 unchanged
 temporary authored/profile fixtures passed. No reopening needed.
- `slider_keyboard_test.py`: native fine-tuning,200 decimal round trips,
 disabled-skip/focus routing, mouse/Tab binding preservation and timer release
 checks passed.
- Existing `spectrum_tuning_test.py`, `artifacts_listening_test.py` and
 `star_profiles_test.py`: passed CPU/synthetic/inert and mocked-owner checks.
- Syntax/whitespace checks and preservation identities are in the evidence pack.

These are native canvas-object/layout/virtual-event and synthetic ACK checks,
not visible hardware input, musical listening, GPU rendering or a performance
campaign. Hidden layout drawing was explicitly refreshed after allocation;
window managers stayed withdrawn. A fixture-target setup failure is preserved
in `test-setup-failure.log`; only the test was corrected. No application failure
or source redesign was hidden by that correction.

Robert's current preview was left running. To load this UI change, save any
desired live values as profiles, restart Development Studio at a convenient
break, and reopen Audio Tuning. Reopening only the dialog uses cached modules.
Normal Studio close stops its owned preview. Review Living Artifacts with both
listening ranges enabled; focus each Start/End field and try overlap and OFF.
Settings/schema and existing persistence rules are unchanged.

Earlier target-switch UI acceptance remains recorded by Robert; the new
multi-window display and musical slider behavior still await user review.
Root documents, prior evidence packs, six DSP files and unrelated dirty work
are preserved. No user session/device/settings were changed, no GPU work or
independent reviewer dispatched, and nothing staged/committed/pushed.

During final packaging, `artifacts_audio_authored.json` differed from the prior
checkpoint and contained current musical-trial values, distinct from the native
test fixture. The tests wrote only isolated temporary stores. Current authored
data was left untouched and recorded in `authored-data-observed.json`; mutable
user-owned authored JSON is separate from the frozen code binding so subsequent
user saves are not mistaken for builder source edits.
