param([string]$ProjectRoot='C:\ZeraWave',[string]$OutputName='abi1-migration-20261013-a')
$ErrorActionPreference='Stop'
$dev='C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if ($OutputName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$') { throw 'Choose one safe output directory name.' }
$out=Join-Path (Join-Path $ProjectRoot 'work\native-surfaces\x64') $OutputName
if (Test-Path -LiteralPath (Join-Path $out 'zerawave_surfaces.dll')) { throw 'Existing DLL retained; choose a new output name and use a new process.' }
if (!(Test-Path -LiteralPath $dev)) { throw 'Installed x64 MSVC unavailable; Qt copy fallback remains usable.' }
New-Item -ItemType Directory -Path $out -Force | Out-Null
$source=Join-Path $ProjectRoot 'native\surfaces\surfaces.cpp'
$flags='/nologo /std:c++17 /O2 /fp:strict /EHsc /MD /LD /W4'
$command='"{0}" 10.0.26100.0 -vcvars_ver=14.51.36231 && cl /Bv {1} "{2}" /Fo"{3}\surfaces.obj" /Fe"{3}\zerawave_surfaces.dll" /link /IMPLIB:"{3}\zerawave_surfaces.lib"' -f $dev,$flags,$source,$out
$raw=& $env:ComSpec /d /s /c $command 2>&1
$exit=$LASTEXITCODE
$raw | ForEach-Object { $_.ToString() } | Set-Content -LiteralPath (Join-Path $out 'build.log') -Encoding utf8
if ($exit -ne 0) { throw "Surface build failed ($exit); Python geometry reference remains available; no environment change." }
$dll=Join-Path $out 'zerawave_surfaces.dll'
$check='"{0}" 10.0.26100.0 -vcvars_ver=14.51.36231 && dumpbin /headers /dependents "{1}"' -f $dev,$dll
$deps=& $env:ComSpec /d /s /c $check 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Native dependency/architecture verification failed.' }
$deps | ForEach-Object { $_.ToString() } | Set-Content -LiteralPath (Join-Path $out 'dependencies.log') -Encoding utf8
[ordered]@{architecture='x64';abi=1;compiler='MSVC 14.51.36231';sdk='10.0.26100.0';flags=$flags;runtime='Existing x64 VC runtime /MD';source_sha256=(Get-FileHash -LiteralPath $source).Hash;dll_sha256=(Get-FileHash -LiteralPath $dll).Hash;build_script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;exit_code=$exit} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $out 'build-identity.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $out 'build-identity.json')
