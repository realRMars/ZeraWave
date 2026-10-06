"""Console-free Qt proof entry with accessible startup diagnostics."""
from pathlib import Path
import sys
import traceback

folder=Path(__file__).resolve().parents[2]/'work/studio'
folder.mkdir(parents=True,exist_ok=True)
with (folder/'qt-startup.log').open('w',encoding='utf8',buffering=1) as log:
    sys.stdout=sys.stderr=log
    try:
        from studio_qt import main
        main()
    except Exception:
        details=traceback.format_exc();log.write(details)
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,'Qt Studio could not start.\n'+details+'\nDiagnostics: '+str(folder/'qt-startup.log'),'ZeraWave Qt proof',0x10)
