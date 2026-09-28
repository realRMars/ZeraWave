# ZeraWave Windows preview

## Play

In this checkout, open **run_zerawave.bat**. In the portable ZIP, extract the
entire folder and open **Start ZeraWave.cmd**. Select the output your music is
playing through and choose **Start visuals**. Close the visual window to return.
System default follows the current default output at each start.

The selected output is saved in `%LOCALAPPDATA%/ZeraWave/settings.json`.
**Open log** opens the folder containing player.log. If a device disappears or
startup fails, select/refresh an available output and start again. Reconnection
is manual in this preview; there is no background recorder after the player
closes. Stop forcibly ends this player's child; closing the visual window is
the normal graceful exit.

## Preview scope

Windows x64 and an OpenGL 3.3-capable graphics driver are required. This is an
unsigned portable preview, not an installer or a claim of compatibility with
untested PCs. Python is included in the ZIP. No administrator access is needed.
The product player runs Main Blend with the current four-material default.
Studio remains the project's development environment, not a consumer product.
No test music is distributed.

## Retained portable checkpoint

`work/releases/ZeraWave-preview-final.zip` is the user's frozen checkpoint of
app source at `d4992d0`. The accepted 2026-09-28 Cavern/Aftershock/Sea repairs are
in the project checkout, not that ZIP. Keep it intact. Another portable is the
lowest priority; build only when expressly approved and always use a new output
name. See ZERAWAVE_HANDOFF.md for current working-app status.

## Build

Use the project's .venv Python to run `build_portable.py`. An optional `--output`
chooses a new destination; existing output folders are never overwritten or
removed. Builds normally go under ignored `work/releases/`.

The builder currently targets the installed Python 3.14 Windows runtime and
installed numpy, ModernGL, glcontext, glfw, SoundCard, cffi and pycparser. It
copies their distribution files/notices, Python's license and Tcl/Tk files;
no external visualization package is included. manifest.json records versions
and SHA-256 hashes for application files. A copied-runtime import/Tk check runs
with isolated Python from outside the checkout before a ZIP is produced.

Before sharing a build, run the standalone Studio, beat tracker, player and GPU
checks, then review full-song Main Blend replay. A clean second-PC check remains
necessary before treating the preview as a general release.
