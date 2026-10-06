"""Standalone owned-window Qt proof checks; no user mouse or audio capture."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer
import PySide6QtAds as ads
from studio_qt import Shell, ROOT


def run():
    app=QApplication([])
    with tempfile.TemporaryDirectory(prefix='zerawave-qt-') as temp:
        shell=Shell(Path(temp)/'layout.json');shell.show()
        failures=[]
        def checks():
            try:
                before=json.dumps(shell.owner.values(),sort_keys=True)
                for _ in range(3):
                    shell.nine_panels();app.processEvents();shell.reset_layout()
                assert json.dumps(shell.owner.values(),sort_keys=True)==before
                assert len(shell.panels)==12
                floating=shell.manager.addDockWidgetFloating(shell.panels['colors']);app.processEvents()
                assert shell.panels['colors'].isFloating()
                shell.manager.addDockWidget(ads.RightDockWidgetArea,shell.panels['colors'],shell.panels['preview'].dockAreaWidget())
                assert not shell.panels['colors'].isFloating()
                shell.panels['monitor'].toggleView(False);shell.save_layout()
                data=json.loads(shell.layout_path.read_text());assert set(data)=={'version','docks','geometry','controls'}
                STUDIO_TREES=shell.client.snapshot['catalog']
                def find(nodes,needle,path=()):
                    for key,node in nodes.items():
                        if needle.lower() in node['label'].lower():return list(path)+( [key])
                        result=find(node.get('children',{}),needle,path+(key,))
                        if result:return result
                for label in ('Fractal','Tidal','Galaxy'):
                    path=find(STUDIO_TREES['main'],label);assert path,label
                    shell.owner.select(path,'main',show=False)
                shell.owner.stop();shell.refresh_colors();shell.poll()
                destination=shell.owner.color_editor.target().id
                try:shell.owner.color_editor.target_choice.set('Stale prior selection')
                except ValueError:pass
                else:raise AssertionError('Unknown color destination was accepted')
                assert shell.owner.color_editor.target().id==destination
                stale=[['wrong run','wrong session',999,'wrong target'],'wrong target']
                try:shell.client.request('tune',binding=stale,key='gain',value=1)
                except ValueError as exc:assert 'destination changed' in str(exc)
                else:raise AssertionError('Stale edit was accepted')
                assert shell.owner.color_editor.target().id
                assert not shell.errors,list(shell.errors)
                control=shell.numerics[0];value=control.spin.value();binding=control.binding
                control.preference('slider');control.preference('knob')
                assert control.spin.value()==value and control.binding==binding
                shell.error(ValueError('Controlled recoverable proof error'))
                assert 'Controlled recoverable' in shell.logs.toPlainText()
                shell.reset_layout();shell.saved_art=json.dumps(shell.owner.values(),sort_keys=True)
                shell.refresh_colors();shell.title.setText('Cosmic / Galaxy • separated control owner')
                app.processEvents()
                print('Color capture target:',shell.color_target.currentText(),'roles:',shell.color_layout.count(),flush=True)
                shell.grab().save(str(ROOT/'work/qt-studio-proof/process-separation-01/shell.png'))
                print('PASS: selection/stop, layout-only reset, nine-panel API layout, float/redock API, preference binding, recoverable error, close',flush=True)
                print('UI poll samples ms:',list(shell.samples),flush=True)
                print('Control ACK roundtrip ms:',list(shell.client.latencies),flush=True)
            except Exception as exc:
                failures.append(exc);print('FAIL:',repr(exc),flush=True)
            finally:
                with patch.object(QMessageBox,'question',return_value=QMessageBox.Discard):shell.close()
        QTimer.singleShot(500,checks);app.exec()
        if failures:raise failures[0]

if __name__=='__main__':run()
