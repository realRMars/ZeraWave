"""Matched EMPTY-GUI cost only. No renderer/GPU/presentation comparison claim."""
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
arm=sys.argv[1]
with tempfile.TemporaryDirectory(prefix='zerawave-ui-cost-') as temp:
    if arm=='tk':
        import tkinter as tk
        from studio_workspace import Workspace
        root=tk.Tk();shell=Workspace(root,Path(temp)/'layout.json');root.geometry('1600x980')
        shell.vars['source'].set('Synthetic preview')
        samples=lambda:list(shell.ui_samples)
        finish=lambda: shell.close()
        schedule=lambda cb:root.after(5000,cb)
        loop=root.mainloop
    else:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        from studio_qt import Shell
        app=QApplication([]);shell=Shell(Path(temp)/'layout.json');shell.show()
        samples=lambda:list(shell.samples)
        finish=shell.close
        schedule=lambda cb:QTimer.singleShot(5000,cb)
        loop=app.exec
    wall=time.perf_counter();cpu=time.process_time()
    def done():
        values=sorted(samples());n=len(values)
        report={'arm':arm,'evidence':'empty GUI; no renderer, GPU, audio or scanout','size':[1600,980],'refresh_ms':200,'wall_s':time.perf_counter()-wall,'cpu_s':time.process_time()-cpu,'count':n,'refresh_median_ms':values[n//2] if n else None,'refresh_max_ms':max(values) if n else None}
        (ROOT/'work/qt-studio-proof'/('ui-cost-'+arm+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);finish()
    schedule(done);loop()
