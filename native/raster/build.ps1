param([string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path, [string]$OutputName = 'abi1-fill-20261009-v2')
$ErrorActionPreference = 'Stop'
$vsRoot = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools'
$dev = Join-Path $vsRoot 'VC\Auxiliary\Build\vcvars64.bat'
if ($OutputName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$') { throw 'OutputName must be a single safe directory name.' }
$out = Join-Path (Join-Path $ProjectRoot 'work\native-raster\x64') $OutputName
if (Test-Path -LiteralPath (Join-Path $out 'zerawave_raster.dll')) { throw 'Existing DLL retained. Choose a fresh -OutputName and validate in a new isolated process; never switch live resources.' }
$source = Join-Path $ProjectRoot 'native\raster\raster.cpp'
if (!(Test-Path -LiteralPath $dev)) { throw 'Installed x64 MSVC environment missing; B1 fallback remains usable.' }
New-Item -ItemType Directory -Path $out -Force | Out-Null
$flags = '/nologo /std:c++17 /O2 /fp:strict /EHsc /MD /LD /W4'
$command = '"{0}" 10.0.26100.0 -vcvars_ver=14.51.36231 && cl /Bv {1} "{2}" /Fo"{3}\raster.obj" /Fe"{3}\zerawave_raster.dll" /link /IMPLIB:"{3}\zerawave_raster.lib"' -f $dev,$flags,$source,$out
$rawLog = & $env:ComSpec /d /s /c $command 2>&1
$exit = $LASTEXITCODE
$log = @($rawLog | ForEach-Object { $_.ToString() })
$log | Set-Content -LiteralPath (Join-Path $out 'build.log') -Encoding utf8
if ($exit -ne 0) { $log | Write-Output; throw "Native build failed ($exit); no install or global PATH changes were made." }
$dll = Join-Path $out 'zerawave_raster.dll'
$dependencyCommand = '"{0}" 10.0.26100.0 -vcvars_ver=14.51.36231 && dumpbin /headers /dependents "{1}"' -f $dev,$dll
$rawDependencies = & $env:ComSpec /d /s /c $dependencyCommand 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Native dependency/architecture verification failed.' }
$dependencies = @($rawDependencies | ForEach-Object { $_.ToString() })
$dependencies | Set-Content -LiteralPath (Join-Path $out 'dependencies.log') -Encoding utf8

$identity = [ordered]@{architecture='x64';abi=1;tile=128;compiler='MSVC 14.51.36231';sdk='10.0.26100.0';flags=$flags;runtime='Installed Microsoft x64 VC runtime (/MD); no redistribution assigned';source_sha256=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash;header_sha256=(Get-FileHash -LiteralPath (Join-Path $ProjectRoot 'native\raster\raster.h')).Hash;dll_sha256=(Get-FileHash -LiteralPath $dll).Hash;log=$log;dependencies=$dependencies;exit_code=$exit}
$identity | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $out 'build-identity.json') -Encoding utf8
$identity | ConvertTo-Json -Depth 5
