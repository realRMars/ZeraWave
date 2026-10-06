"""Windows presentation hosting for Studio's existing GLFW window.

Only HWND parent/style/rectangle change. Context, renderer and audio ownership
remain in the preview process. No second context, copies or frame readback.
"""
import ctypes
from ctypes import wintypes
import os


def dpi_awareness():
    if os.name == 'nt':
        # Both Tk and the owned GLFW child use system DPI awareness. Set before
        # either toolkit creates windows; an existing process setting wins.
        ctypes.windll.user32.SetProcessDPIAware()


def windows():
    if os.name != 'nt':
        raise RuntimeError('Native Studio docking requires Windows.')
    u = ctypes.WinDLL('user32', use_last_error=True)
    for name, args, result in (
        ('IsWindow', [wintypes.HWND], wintypes.BOOL),
        ('GetParent', [wintypes.HWND], wintypes.HWND),
        ('SetParent', [wintypes.HWND, wintypes.HWND], wintypes.HWND),
        ('GetWindowLongPtrW', [wintypes.HWND, ctypes.c_int], ctypes.c_ssize_t),
        ('SetWindowLongPtrW', [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t], ctypes.c_ssize_t),
        ('GetWindowThreadProcessId', [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD),
        ('SetWindowPos', [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.BOOL),
    ):
        fn = getattr(u, name); fn.argtypes = args; fn.restype = result
    return u


def owner(u, hwnd):
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def owned_process(pid, launcher_pid):
    """Windows venv launchers may own a second Python process. Bind ancestry."""
    if pid==launcher_pid:return True
    class Entry(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('usage',wintypes.DWORD),('pid',wintypes.DWORD),
                  ('heap',ctypes.c_size_t),('module',wintypes.DWORD),('threads',wintypes.DWORD),
                  ('parent',wintypes.DWORD),('priority',wintypes.LONG),('flags',wintypes.DWORD),
                  ('exe',wintypes.WCHAR*260)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
    kernel.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    snapshot=kernel.CreateToolhelp32Snapshot(2,0)
    if snapshot==ctypes.c_void_p(-1).value:return False
    parents={};entry=Entry();entry.size=ctypes.sizeof(entry)
    try:
        more=kernel.Process32FirstW(snapshot,ctypes.byref(entry))
        while more:
            parents[entry.pid]=entry.parent;more=kernel.Process32NextW(snapshot,ctypes.byref(entry))
    finally:kernel.CloseHandle(snapshot)
    for _ in range(4):
        pid=parents.get(pid)
        if pid==launcher_pid:return True
        if pid is None:return False
    return False


class NativeSurface:
    def __init__(self, hwnd, pid):
        self.u = windows(); self.hwnd = int(hwnd); self.pid = int(pid)
        self.last = None

    def attach(self, parent, width, height, host_pid):
        u = self.u; parent = int(parent)
        if not u.IsWindow(self.hwnd) or owner(u, self.hwnd) != self.pid:
            raise RuntimeError('The owned renderer window is no longer available.')
        if not u.IsWindow(parent) or owner(u, parent) != host_pid:
            raise RuntimeError('The Studio host does not belong to this workspace.')
        rect = (parent, max(1, int(width)), max(1, int(height)))
        if rect == self.last: return
        if int(u.GetParent(self.hwnd) or 0) != parent:
            # Win32 does not update these styles when SetParent is called.
            style = u.GetWindowLongPtrW(self.hwnd, -16)
            style = (style & ~0x80C40000) | 0x40000000 | 0x04000000
            ctypes.set_last_error(0)
            u.SetWindowLongPtrW(self.hwnd, -16, style)
            if ctypes.get_last_error(): raise ctypes.WinError(ctypes.get_last_error())
            ctypes.set_last_error(0)
            u.SetParent(self.hwnd, parent)
            if ctypes.get_last_error(): raise ctypes.WinError(ctypes.get_last_error())
        # FRAMECHANGED | NOACTIVATE | NOZORDER. Visibility remains renderer-owned.
        if not u.SetWindowPos(self.hwnd, None, 0, 0, rect[1], rect[2], 0x0034):
            raise ctypes.WinError(ctypes.get_last_error())
        self.last = rect


def initial_host(window):
    """Opt-in only; legacy renderer callers never enter this path."""
    parent = os.environ.get('ZERAWAVE_WORKSPACE_HOST')
    if not parent: return None
    import glfw
    surface = NativeSurface(glfw.get_win32_window(window), os.getpid())
    width, height = glfw.get_window_size(window)
    # Qt's foreign-window container must perform parenting itself so its
    # platform window hierarchy includes the renderer. Tk retains its path.
    if os.environ.get('ZERAWAVE_WORKSPACE_QT_FOREIGN')!='1':
        surface.attach(int(parent), width, height, int(os.environ['ZERAWAVE_WORKSPACE_PID']))
    return dict(hwnd=surface.hwnd, pid=os.getpid(), host=int(parent),run=os.environ.get('ZERAWAVE_PREVIEW_RUN'))


def monitor_rectangles(root):
    if os.name == 'nt':
        rects = []
        callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HDC,
                                     ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
        def collect(monitor, dc, rect, data):
            r = rect.contents; rects.append((r.left, r.top, r.right, r.bottom)); return True
        windows().EnumDisplayMonitors(None, None, callback(collect), 0)
        if rects: return rects
    return [(0, 0, root.winfo_screenwidth(), root.winfo_screenheight())]
