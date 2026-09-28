"""Build a self-contained Windows preview from the installed Python environment.

No downloads or installers. Output is always a new directory; never deletes an
existing build. Test the copied interpreter from an unrelated working directory.
"""
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
DISTRIBUTIONS=('numpy','moderngl','glcontext','glfw','SoundCard','cffi','pycparser')


def build(output):
    if sys.platform != 'win32': raise RuntimeError('This build currently targets Windows only.')
    output=output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    runtime=output/'runtime';runtime.mkdir()
    base=Path(sys.base_prefix)
    for name in ('python.exe','pythonw.exe','python3.dll','python314.dll','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt'):
        shutil.copy2(base/name,runtime/name)
    for folder in ('Lib','DLLs','tcl'):
        shutil.copytree(base/folder,runtime/folder,ignore=shutil.ignore_patterns('site-packages','__pycache__','test','tests','idlelib'))
    site=runtime/'Lib/site-packages';site.mkdir()
    packages=[]
    for name in DISTRIBUTIONS:
        dist=metadata.distribution(name);origin=Path(dist.locate_file('')).resolve()
        packages.append(dict(name=name,version=dist.version))
        for relative in dist.files or ():
            source=Path(dist.locate_file(relative)).resolve()
            if not source.is_relative_to(origin) or not source.is_file() or '__pycache__' in source.parts:continue
            target=site/source.relative_to(origin);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
    shutil.copytree(ROOT/'app',output/'app',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    (output/'Start ZeraWave.cmd').write_text('@echo off\nstart "" "%~dp0runtime\\pythonw.exe" "%~dp0app\\player.py"\n')
    (output/'README.txt').write_text(
        'ZeraWave Windows preview\n\nExtract this entire folder, then open Start ZeraWave.cmd.\n'
        'Choose the output playing your music, then Start visuals. Close the visual window to return.\n'
        'If a device disconnects, refresh outputs and restart. Open log shows failure details.\n'
        'Settings and logs are in %LOCALAPPDATA%/ZeraWave. No administrator access or Python installation is required.\n'
        'Requires Windows x64 and a working OpenGL 3.3 graphics driver. This preview is unsigned.\n'
        'Test songs, research downloads and development captures are not included.\n'
        'Dependency versions are in manifest.json; their notices are retained under runtime/Lib/site-packages/*.dist-info.\n'
        'Python notices are in runtime/LICENSE.txt; Tcl/Tk notices are under runtime/tcl.\n'
        'This is a preview package, not a claim of compatibility with every graphics/audio device.\n',encoding='utf-8')
    manifest=dict(python=sys.version,packages=packages,files={})
    for path in sorted((output/'app').rglob('*')):
        if path.is_file():manifest['files'][str(path.relative_to(output))]=hashlib.sha256(path.read_bytes()).hexdigest()
    shutil.copy2(ROOT/'PLAYER.md',output/'PLAYER.md')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # -I prevents local source/PYTHONPATH from masking missing packaged modules.
    check='import sys,tkinter,numpy,moderngl,glfw,soundcard; r=tkinter.Tk();r.withdraw();r.update();r.destroy();print(sys.prefix)'
    result=subprocess.run([str(runtime/'python.exe'),'-I','-c',check],cwd=output.parent,capture_output=True,text=True,check=True)
    if Path(result.stdout.strip()).resolve()!=runtime:raise RuntimeError('Smoke test used the wrong runtime.')
    archive=shutil.make_archive(str(output),'zip',root_dir=output.parent,base_dir=output.name)
    print(archive)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'work/releases'/('ZeraWave-'+time.strftime('%Y%m%d-%H%M%S')))
    args=parser.parse_args();build(args.output)
