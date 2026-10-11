# B3 native media transfer candidate

## October 11 accepted B3 development checkpoint

Robert accepted the verified B3 correction candidate and authorized publication.
See the [current handoff](../ZERAWAVE_HANDOFF.md#october-11-accepted-b3-development-checkpoint)
and [publication receipt](../work/publication-b3-accepted-20261011/review-index.json).
Timing remains PARTIAL, one fallback switch timeout is unresolved, and scripted
physical drag evidence remains unverified. Video Save writing stays OPEN; this
checkpoint neither approves its proposal nor closes B3 or dispatches later work.
Dated reports retain their task-time status and measurements.


The October 10 Builder candidate and October 11 correction are accepted as a
development checkpoint, with the limits and publication identity above. The candidate
starts above accepted/pushed `f3d414be7ee380a38865c3579c057597dbb5fb06`; it does
not change the raster ABI/DLL, session schema, PyAV codecs, renderer or audio owner.
See [actual results](agent-notes/b3-media-20261010.md) and the
[media contract](STUDIO_MEDIA_COMPOSITION.md#b3-builder-candidate--2026-10-10).

`app/visuals/media_transfer.py` selects one optional transfer DLL at process open.
`native/media/transfer.cpp` is a stateless, batched x64 C ABI-1 kernel. It copies a
whole bottom-up premultiplied RGBA frame into an owned top-down Qt ARGB32/BGRA
image in one pass, using SSE2 with scalar tails. It allocates nothing, retains no
pointers, and owns no decoder, codec, GL object or audio state. Python validates
dimensions/length; the C ABI independently validates pointers, stride/length and
8 MP bounds before writing. Caller source/destination are separate owned buffers.
The adapter releases ctypes exports before FrameReader releases its mapping view.

The original 2558×1388 Qt copy/flip/channel conversion measured a 17.52 ms median
over 20 samples; the isolated C++ copy measured 4.43 ms median, p95 4.81 ms and
maximum 5.00 ms. Those are CPU copy boundaries, not video FPS, editor response or
physical scanout. Exact randomized premultiplied bytes match the Qt reference at
1×1, odd widths/heights and full original size. Codec conversion still uses PyAV/
FFmpeg; policy, scheduling and history remain Python, upload/drawing remain GL.

## Existing build and reproducibility

Current generated artifact:
`work/native-media/x64/b3-transfer-20261010-v2/zerawave_media_transfer.dll`

SHA256: `4604b28a640919a119f311f5e9b3a88ffefe43f6cc2edffa252adf4faf201dda`.
Source SHA256: `e17bada4e77dd77c588031ac12e7b874712ec6693ec128845c58b92533c922b1`.
Build script SHA256: `90641ebcca6b623a4fc35a34aa3692b3ee5e684cbc32d08aff0bfd1040da05ec`.
MSVC 14.51.36231, Windows SDK 10.0.26100.0, x64, `/O2 /MD /std:c++17 /LD`.
Build identity, compiler log and dependency/header inspection are beside the DLL.
Existing x64 VC runtime was used; no package or system dependency was installed.
Earlier v1 artifact/failed probes are retained separately as evidence.

From `C:\ZeraWave`, with the already installed toolchain:

```powershell
& .\native\media\build.ps1 -ProjectRoot C:\ZeraWave -OutputName b3-transfer-review-new
```

The script refuses to overwrite an existing DLL path. Choose a fresh output name
for every changed build. Never replace a DLL loaded by a live Studio process.
Close normally after securing artwork, then select a new path in a new process:

```powershell
$env:ZERAWAVE_MEDIA_TRANSFER_DLL='C:\ZeraWave\work\native-media\x64\b3-transfer-review-new\zerawave_media_transfer.dll'
& .\.venv\Scripts\python.exe .\app\visuals\studio_qt.py
```

## Supported fallback

Missing/incompatible x64 ABI/DLL falls back to Qt's existing copy/vertical-flip/
ARGB conversion with matching pixels. The transport tooltip and `media_stats`
identify the actual route and reason. To deliberately choose it for a new process:

```powershell
$env:ZERAWAVE_MEDIA_TRANSFER='qt'
& .\.venv\Scripts\python.exe .\app\visuals\studio_qt.py
```

Use a new process rather than switching an active backend. Restore the launching
shell's prior environment values when finished. This fallback changes the editor
transfer only; silent PyAV/FFmpeg codecs and context-owned native-resolution output
remain. Missing/incompatible and explicit-Qt standalone checks passed. An actual
copy/allocation failure is reported, the reader permits retry, and accepted raster
history/work is untouched.

CUDA decoding and a full-resolution lossless intra fragment were explored only
as measured options. CUDA decoded different RGB bytes; the intra fragment had
mixed tails and a large storage cost. Neither route is enabled, no proxy replaces
an original/reference, and no product proxy UI or decoder replacement is shipped.
Packaging/release, multi-hour playback and broad hardware compatibility are unrun.


## Finishing evidence — 2026-10-10

The finishing candidate retains exactly the v2 source/build script/DLL identities
above. A separate `b3-finishing-20261010-v3` row-copy experiment was slower than
the existing NumPy row extraction, rejected, archived and removed from product
source. Its DLL remains evidence, not the selected artifact. No loaded user DLL
was replaced. Native/Qt parity and reader export retirement were rechecked in
separate processes. [Finishing results](agent-notes/b3-media-20261010.md) retain
failed profiles and original-clip performance criteria; no general speedup is
claimed. The compatible `media.direction` metadata extension keeps existing
scene/session version numbers and defaults older sessions Forward; the earlier
no-schema-change statement described the starting B3 candidate.
