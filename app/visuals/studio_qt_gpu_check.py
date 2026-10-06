"""Short owned synthetic-renderer continuity probe; no live capture."""
import json
from pathlib import Path
import time
import faulthandler
from unittest.mock import patch
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication,QMessageBox
import PySide6QtAds as ads
from studio_qt import Shell,ROOT

fault=(ROOT/'work/qt-studio-proof/gpu-stack.log').open('w');faulthandler.dump_traceback_later(15,repeat=True,file=fault)
app=QApplication([]);shell=Shell(ROOT/'work/qt-studio-proof/gpu-layout.json');shell.allow_native_probe=True;shell.show()
start=time.perf_counter();ready=None;steps=[];pid=None
def tick():
    global ready,pid
    try:
        if shell.owner.process is None and not steps:
            shell.owner.select(['fractals','landscape'],'main',show=False)
            shell.refresh_colors();shell.surface.setFixedSize(800,450);shell.start();steps.append('start')
        if shell.owner.preview_state.get('ready') and ready is None:
            ready=time.perf_counter();pid=shell.owner.process.pid;print('READY',pid,flush=True)
        if ready is not None:
            elapsed=time.perf_counter()-ready
            if elapsed>1 and 'float' not in steps:
                print('FLOAT begin',flush=True);shell.manager.addDockWidgetFloating(shell.panels['colors']);steps.append('float');print('FLOAT done',flush=True)
            if elapsed>2 and 'redock' not in steps:
                print('REDOCK begin',flush=True);shell.manager.addDockWidget(ads.RightDockWidgetArea,shell.panels['colors'],shell.panels['preview'].dockAreaWidget());steps.append('redock');print('REDOCK done',flush=True)
            if elapsed>3 and 'reset' not in steps:print('RESET begin',flush=True);shell.reset_layout();steps.append('reset');print('RESET done',flush=True)
            if elapsed>5:
                assert shell.owner.process.pid==pid and shell.owner.process.poll() is None
                shell.screen().grabWindow(int(shell.winId())).save(str(ROOT/'work/qt-studio-proof/renderer.png'))
                finish('PASS')
        if time.perf_counter()-start>180:finish('TIMEOUT: preview readiness')
    except Exception as exc:finish('FAIL: '+repr(exc))
def finish(result):
    timer.stop();data={'result':result,'steps':steps,'pid':pid,'elapsed':time.perf_counter()-start,'ready_after':ready-start if ready else None,'ui_ms':list(shell.samples),'errors':list(shell.errors),'viewport':[shell.surface.width(),shell.surface.height()],'source':'Synthetic preview','quality':'Full quality (100%)'}
    (ROOT/'work/qt-studio-proof/gpu-check.json').write_text(json.dumps(data,indent=2));print(result,flush=True)
    with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
timer=QTimer();timer.timeout.connect(tick);timer.start(500);app.exec()
