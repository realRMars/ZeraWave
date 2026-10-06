"""Console-free entry; retain a visible diagnostic fallback and startup log."""
from pathlib import Path
import sys
import traceback

folder=Path(__file__).resolve().parents[2]/'work/studio'
log=None
try:
    folder.mkdir(parents=True,exist_ok=True)
    log=(folder/'workspace-startup.log').open('w',encoding='utf8',buffering=1)
    sys.stdout=sys.stderr=log
    import tkinter as tk
    from studio_workspace import Workspace
    from window_host import dpi_awareness
    dpi_awareness()
    root=tk.Tk()
    def report(exc_type,exc,tb):
        traceback.print_exception(exc_type,exc,tb,file=log)
        from tkinter import messagebox
        messagebox.showerror('Studio error',str(exc)+'\n\nDiagnostics: '+str(folder/'workspace-startup.log'),parent=root)
    root.report_callback_exception=report
    Workspace(root);root.mainloop()
except Exception:
    details=traceback.format_exc()
    if log:log.write(details);log.flush()
    import ctypes
    location=('Diagnostics: ' if log else 'Diagnostics could not be written to: ')+str(folder/'workspace-startup.log')
    ctypes.windll.user32.MessageBoxW(None,'Studio could not start.\n\n'+details+'\n'+location,'ZeraWave Studio startup',0x10)
finally:
    if log:log.close()
