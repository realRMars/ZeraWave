# Audio Tuning target-switch regression

Authorized narrow UI correction after Robert reported rows disappearing when
switching from a smaller target back to stars or Planet surface. No GPU work,
preview control, spectrum overlays, independent review, commit or push.

The pre-task `starfield_tuning.py` SHA256 is
`c9805abb2a6a1c7f40754cee2d01c35f1ed1804af5918835624077dcb4704c92`.
Source/diff/check identities are bound by
`work/audio-tuning-switch-01/review-index.json`. HEAD remains
`0342e518a7bd2c521416e8027a7920668fc5ee51`.

Root cause: `configure_controls()` enumerated `grid_slaves(row=i)` to hide and
restore rows. Native Tk excludes widgets hidden with `grid_remove()` from that
enumeration. A smaller target hid the surplus rows; later larger targets could
not discover them to restore them. The preserved pre-fix class reproduces
stars10 -> Alloy4 -> stars4 -> Silk2 -> stars2, and surface5 becoming one row
after Sparkles1, without closing the window. The same final test detects182
failures against that preserved class.

The fix retains the existing title/slider/value widgets in ten explicit row
tuples and restores them from those references. No controls, settings,
declarations, transport, authored/profile storage or keyboard behavior changed.
No widget is replaced during a switch.

Executed checks:

- `audio_tuning_switch_test.py`: native hidden Tk,107 repeated switches across
  all24 targets;386 reachable row cases (each label/slider/value),748 Up/Down
  navigation events,107 keyboard taps, repeat/debounce cancellation across
  target switches, nonneutral per-target values,48 unchanged temporary
  authored/profile fixtures and zero submissions. Passed without reopening.
- The same test against the preserved pre-fix class: correctly reproduced
  row loss. This is a passing sensitivity check of the regression, not a
  passing application baseline.
- Existing `planet_audio_tuning_test.py` and `star_profiles_test.py`: passed
  CPU/synthetic/inert-resource and mocked-owner checks; no device/GPU capture.
- Syntax/whitespace checks and preservation identities: see the bound pack.

Evidence limits: real Tk widgets/layout/grid management at allocated900x860,
with a withdrawn host. Native virtual key and FocusIn bindings ran; focus_set
destinations were intercepted to protect foreground focus. This verifies
callback routing and logical canvas reachability, not hardware keys, OS focus
or a visible screenshot. Withdrawn canvas windows retain stale OS root
coordinates after scrolling; logical canvas coordinates were used. Initial
harness freshness/step assertions and coordinate diagnostics are preserved;
they were corrected in the test without an application scroll change.

Robert's running preview was neither closed nor restarted. To load the code,
restart Development Studio at a convenient break and reopen Audio Tuning.
Closing/reopening Audio Tuning alone recreates the old imported class in the
current Studio process. Studio's normal close stops its owned preview. Save
any live values Robert wants to keep as profiles before that restart; this
fix does not change saved data or the existing live-session persistence rules.

Shared planning documents and earlier CPU/GPU evidence packs remain unchanged.
The prior GPU compile/draw evidence still applies to unchanged renderer/shader
bytes; its cold-start concern, Flecks clock gap, musical/artistic acceptance
and other recorded limits remain unresolved. Independent reviewer stays on
hold. Return to Bob/Prompter; no new phase dispatched.
