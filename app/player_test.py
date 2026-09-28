"""Launcher settings and error recovery; no sound or child renderer required."""
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import tkinter as tk
import player


def main():
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary);path=folder/'settings.json'
        assert player.load_settings(path)=={'device':''}
        path.write_text('invalid');assert player.load_settings(path)=={'device':''}
        player.save_settings(path,{'device':'speaker-id'})
        assert player.load_settings(path)=={'device':'speaker-id'}
        with patch.object(player,'DATA',folder), patch('soundcard.all_speakers',return_value=[]):
            root=tk.Tk();root.withdraw();app=player.Player(root)
            try:
                assert app.device.get()=='System default'
                child=Mock();child.poll.return_value=1;child.returncode=1
                app.process=child;app.poll()
                assert app.process is None and 'refresh' in app.status.get()
                assert str(app.start_button['state'])=='normal'
            finally:app.close()
    print('PASS: player settings, corrupt config fallback and child failure recovery')

if __name__=='__main__':main()
