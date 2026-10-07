# Accepted Studio launcher baseline — 2026-10-07

The user requested all accepted progress behind `run_zerawave_studio` after
accepting the audio reliability repair. This authorizes integrating that exact
repair into the main checkout for this launcher; it does not authorize publication.

`C:/ZeraWave` and the approved `83a3` source shared published HEAD
`ffa67074315b8c2f4fa9d228e82faf0855cc22b8`. That checkpoint already includes the
earlier accepted visuals/performance work, Qt header and 13 docks, native resizing,
Visualizer Resolution, Simple/Detailed resources, and independent Audio Hub.
The seven missing approved audio code/test files were copied byte-for-byte from
the reviewed source, after checking hashes and confirming no destination edits.

`C:/ZeraWave/run_zerawave_studio.vbs` now launches the main checkout's
`app/visuals/studio_qt.pyw` using its existing `.venv/Scripts/pythonw.exe`.
The launcher no longer depends on the worktree location. Existing running apps
were not restarted; the new source loads on the next launch.

Bindings, original file backups and check results are in
`work/studio-launcher-baseline-20261007/integration.json` and `before/`.
Saved Qt/workspace layouts and three unrelated modified notes retain their hashes.
Unrelated research, images, settings, sessions and launchers were not modified.

Passed: existing transport and musical-descriptor/spectrum checks, source-location
imports, syntax, preservation checks and `git diff --check`. One direct import
probe initially omitted the audio module path; the corrected probe passed without
a source change. Prior audio evidence remains bound to its original worktree;
this pass verifies identical integrated code rather than claiming a new hardware
or listening result. Existing full-size performance and physical-input limits
remain. Shared planning documents, dependencies and the frozen portable unchanged.
No stage, commit, push, new workers or publication.
