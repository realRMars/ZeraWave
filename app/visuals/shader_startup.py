"""Owned Windows startup notice; no graphics, audio, shader cache or simulation.

The native compiler can hold the render thread/GIL. A separate small Tk process
keeps progress/cancel responsive. Its inherited handle identifies exactly this
preview process, never a PID lookup or another Studio/user process.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CANCELLED = 125


class StartupNotice:
    def __init__(self, title):
        self.process = None
        self.started = time.perf_counter()
        if os.name != 'nt':
            return
        import ctypes as c
        from ctypes import wintypes as w
        kernel = c.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        kernel.OpenProcess.restype = w.HANDLE
        kernel.CloseHandle.argtypes = [w.HANDLE]
        # Inherit only a terminate/synchronize handle to our own preview.
        handle = kernel.OpenProcess(0x0001 | 0x00100000, True, os.getpid())
        if not handle:
            raise c.WinError(c.get_last_error())
        try:
            # Windows venv python.exe is a redirector process; run the
            # already installed base interpreter for this stdlib-only notice,
            # so handle_list reaches the exact Tk process without a relay.
            info = subprocess.STARTUPINFO()
            info.lpAttributeList = {'handle_list': [int(handle)]}
            self.process = subprocess.Popen(
                [getattr(sys, '_base_executable', sys.executable), str(Path(__file__).resolve()), '--notice',
                 str(int(handle)), title], stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True, startupinfo=info,
                creationflags=subprocess.CREATE_NO_WINDOW)
        finally:
            kernel.CloseHandle(handle)

    def phase(self, phase):
        seconds = time.perf_counter() - self.started
        # Existing Studio pipe: additional status, not a color acknowledgement.
        print('ZERAWAVE_COLOR ' + json.dumps(
            {'startup': {'phase': phase, 'seconds': seconds}}), flush=True)
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write((json.dumps(
                    {'phase': phase, 'seconds': seconds}) + '\n').encode())
                self.process.stdin.flush()
            except (OSError, ValueError):
                pass
        return seconds

    def close(self, pump=None):
        if not self.process:
            return
        try:
            self.process.stdin.close()  # EOF also closes notice on error/Stop.
        except (OSError, ValueError):
            pass

        def wait_owned(timeout):
            if pump is None:
                return self.process.wait(timeout=timeout)
            deadline = time.monotonic() + timeout
            while self.process.poll() is None:
                pump()
                remaining = deadline-time.monotonic()
                if remaining <= 0.:
                    raise subprocess.TimeoutExpired('owned startup notice', timeout)
                time.sleep(min(.01, remaining))
            return self.process.returncode

        try:
            wait_owned(1.)
        except subprocess.TimeoutExpired:
            self.process.terminate()  # Only this owned notice, not the preview.
            wait_owned(2.)
        self.process = None


def notice(handle, title):
    import ctypes as c
    from ctypes import wintypes as w
    import threading
    import tkinter as tk
    from tkinter import ttk
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.TerminateProcess.argtypes = [w.HANDLE, w.UINT]
    kernel.TerminateProcess.restype = w.BOOL
    kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
    kernel.WaitForSingleObject.restype = w.DWORD
    kernel.CloseHandle.argtypes = [w.HANDLE]
    state = {'phase': 'context', 'seconds': 0., 'at': time.monotonic(), 'eof': False}
    lock = threading.Lock()

    def read():
        try:
            for line in sys.stdin.buffer:
                message = json.loads(line)
                with lock:
                    state.update(message)
                    state['at'] = time.monotonic()
        finally:
            with lock:
                state['eof'] = True

    threading.Thread(target=read, daemon=True, name='Startup status').start()
    root = tk.Tk()
    root.withdraw()
    root.title('ZeraWave - Starting preview')
    root.geometry('460x200')
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text='Preparing ' + title, font=('Segoe UI', 12)).pack(anchor='w')
    text = tk.StringVar()
    ttk.Label(frame, textvariable=text, wraplength=415).pack(anchor='w', pady=(10, 6))
    bar = ttk.Progressbar(frame, mode='indeterminate')
    bar.pack(fill='x', pady=(0, 10))
    bar.start(35)

    def cancel():
        # A blocked native compiler cannot service a cooperative close request.
        # Same bounded termination semantics as Studio Stop; OS owns GL cleanup.
        if kernel.TerminateProcess(handle, CANCELLED):
            root.destroy()
        elif kernel.WaitForSingleObject(handle, 0) == 0:
            root.destroy()
        else:
            text.set('Could not cancel. Use Stop in Studio.')

    ttk.Button(frame, text='Cancel preview', command=cancel).pack(anchor='e')
    root.protocol('WM_DELETE_WINDOW', cancel)
    shown = False
    began = time.monotonic()

    def tick():
        nonlocal shown
        with lock:
            snapshot = dict(state)
        if snapshot['eof'] or snapshot['phase'] in ('ready', 'failed') or kernel.WaitForSingleObject(handle, 0) == 0:
            root.destroy()
            return
        if not shown and time.monotonic() - began > .35:
            shown = True
            root.deiconify()
        elapsed = snapshot['seconds'] + time.monotonic() - snapshot['at']
        label = {'context': 'Creating graphics context',
                 'compiling': 'Compiling visual shaders',
                 'resources': 'Preparing graphics resources'}.get(snapshot['phase'], 'Preparing preview')
        text.set(f'{label} - {elapsed:.1f}s\nFirst use after a shader change can take longer. You can cancel.')
        root.after(80, tick)

    try:
        tick()
        root.mainloop()
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--notice':
        notice(int(sys.argv[2]), sys.argv[3])
