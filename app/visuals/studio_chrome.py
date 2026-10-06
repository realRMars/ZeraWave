"""Windows client header over Qt's retained native window and ADS docks.

Native hit testing keeps Windows move/resize/snap/system-menu behavior. No
window recreation, graphics parenting or layout mutations occur here.
"""
import ctypes as c
from ctypes import wintypes as w
import os
from PySide6.QtCore import QPoint,QRect,Qt,QTimer
from PySide6.QtWidgets import QLabel,QMenuBar,QPushButton
from window_host import windows

RESIZE_EDGES={10:Qt.LeftEdge,11:Qt.RightEdge,12:Qt.TopEdge,15:Qt.BottomEdge,
    13:Qt.TopEdge|Qt.LeftEdge,14:Qt.TopEdge|Qt.RightEdge,
    16:Qt.BottomEdge|Qt.LeftEdge,17:Qt.BottomEdge|Qt.RightEdge}
RESIZE_CURSORS={10:Qt.SizeHorCursor,11:Qt.SizeHorCursor,12:Qt.SizeVerCursor,15:Qt.SizeVerCursor,
    13:Qt.SizeFDiagCursor,17:Qt.SizeFDiagCursor,14:Qt.SizeBDiagCursor,16:Qt.SizeBDiagCursor}

def resize_hit(x,y,width,height,margin,disabled=False):
    if disabled or not (0<=x<width and 0<=y<height):return 1
    left=x<margin;right=x>=width-margin;top=y<margin;bottom=y>=height-margin
    if top and left:return 13
    if top and right:return 14
    if bottom and left:return 16
    if bottom and right:return 17
    if left:return 10
    if right:return 11
    if top:return 12
    if bottom:return 15
    return 1

class WindowChrome:
    def __init__(self,shell,header,minimize,maximize,close):
        self.shell=shell;self.header=header;self.buttons=(minimize,maximize,close)
        self.hwnd=None;self.pressed=False
        self.restore_rect=QRect(shell.geometry())
        self.resize_cursor=False
    def resize_disabled(self):return self.shell.isMaximized() or self.shell.isFullScreen()
    def client_hit(self,global_point):
        local=self.shell.mapFromGlobal(global_point)
        return resize_hit(local.x(),local.y(),self.shell.width(),self.shell.height(),7,self.resize_disabled())
    def client_hover(self,event):
        hit=self.client_hit(event.globalPosition().toPoint())
        if hit in RESIZE_CURSORS:
            self.shell.setCursor(RESIZE_CURSORS[hit]);self.resize_cursor=True
        elif self.resize_cursor:self.shell.unsetCursor();self.resize_cursor=False
    def remember_normal(self):
        if not self.shell.isMaximized() and not self.shell.isMinimized() and not self.shell.isFullScreen():self.restore_rect=QRect(self.shell.geometry())
    def install(self):
        if os.name!='nt':return
        hwnd=int(self.shell.winId())
        if self.hwnd==hwnd:return
        u=windows();style=u.GetWindowLongPtrW(hwnd,-16)
        # Keep native thick frame and system commands, without WS_CAPTION.
        u.SetWindowLongPtrW(hwnd,-16,(style & ~0x00C00000)|0x00040000|0x00080000|0x00020000|0x00010000)
        u.SetWindowPos(hwnd,None,0,0,0,0,0x0037)
        self.hwnd=hwnd
    def toggle_maximize(self):
        if self.shell.isMaximized():
            # Qt's frameless showNormal can leave WS_MAXIMIZE on this retained
            # native window after caption styles change. Restore the Windows
            # placement first so later WM_SIZE cannot reassert maximized state.
            if os.name=='nt':
                u=windows();u.ShowWindow.argtypes=[w.HWND,c.c_int]
                u.ShowWindow(int(self.shell.winId()),9)  # SW_RESTORE
            self.shell.showNormal();self.shell.setGeometry(self.restore_rect)
        else:
            self.remember_normal();self.shell.showMaximized()
    def state_changed(self,event):
        if self.resize_cursor:self.shell.unsetCursor();self.resize_cursor=False
        if event.oldState() & Qt.WindowMaximized and not self.shell.isMaximized() and not self.shell.isMinimized():
            rect=QRect(self.restore_rect)
            QTimer.singleShot(0,lambda:self.shell.setGeometry(rect) if not self.shell.isMaximized() and not self.shell.isMinimized() else None)
        self.sync()
    def client_press(self,event,double=False):
        """Qt-native child widgets can receive client input over the header.

        Use Qt's OS move/resize initiation for that path, as well as the native
        hit-testing path. Both retain the same top-level HWND and context.
        """
        if event.button()!=Qt.LeftButton:return False
        shell=self.shell;local=shell.mapFromGlobal(event.globalPosition().toPoint())
        if not shell.rect().contains(local):return False
        edges=RESIZE_EDGES.get(self.client_hit(event.globalPosition().toPoint()))
        if edges:return shell.windowHandle().startSystemResize(edges)
        if not self.header.rect().contains(self.header.mapFrom(shell,local)):return False
        child=shell.childAt(local)
        blank=child is None or isinstance(child,QLabel) or child in (self.header,shell.brand)
        blank|=isinstance(child,QMenuBar) and child.actionAt(child.mapFrom(shell,local)) is None
        if blank:
            if double:self.toggle_maximize();return True
            return shell.windowHandle().startSystemMove()
        return False
    def sync(self):
        button=self.buttons[1];button.setText('❐' if self.shell.isMaximized() else '□')
        button.setAccessibleName('Restore window' if self.shell.isMaximized() else 'Maximize window')
        button.setToolTip(button.accessibleName())
    def hit(self,x,y):
        shell=self.shell;u=windows();r=w.RECT()
        u.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)];u.GetWindowRect(shell.winId(),c.byref(r))
        scale=shell.devicePixelRatioF();local=QPoint(round((x-r.left)/scale),round((y-r.top)/scale))
        hit=resize_hit(x-r.left,y-r.top,r.right-r.left,r.bottom-r.top,max(5,round(7*scale)),self.resize_disabled())
        if hit in RESIZE_EDGES:return hit
        button=self.buttons[1]
        if button.rect().contains(button.mapFrom(shell,local)):return 9  # HTMAXBUTTON enables Windows 11 Snap Layouts.
        if self.header.rect().contains(self.header.mapFrom(shell,local)):
            child=shell.childAt(local)
            if isinstance(child,QMenuBar) and child.actionAt(child.mapFrom(shell,local)) is None:return 2
            if child is None or isinstance(child,QLabel) or child in (self.header,shell.brand):return 2
        return 1
    def native(self,event_type,message):
        if os.name!='nt':return False,0
        msg=w.MSG.from_address(int(message));kind=msg.message
        if kind==0x84:
            return True,self.hit(c.c_short(msg.lParam&0xffff).value,c.c_short((msg.lParam>>16)&0xffff).value)
        if kind==0x20:  # WM_SETCURSOR: Qt's frameless path otherwise restores Arrow.
            hit=msg.lParam&0xffff
            if hit in RESIZE_EDGES and not self.resize_disabled():
                u=windows();u.LoadCursorW.argtypes=[w.HINSTANCE,c.c_void_p];u.LoadCursorW.restype=w.HANDLE
                u.SetCursor.argtypes=[w.HANDLE];u.SetCursor.restype=w.HANDLE
                cursor={10:32644,11:32644,12:32645,15:32645,13:32642,17:32642,14:32643,16:32643}[hit]
                u.SetCursor(u.LoadCursorW(None,c.c_void_p(cursor)));return True,1
        if kind==0xA1 and msg.wParam in RESIZE_EDGES:
            if self.resize_disabled():return True,0
            # Qt consumes non-client presses for frameless windows. Delegate
            # SC_SIZE directly to Windows' sizing loop, retaining this HWND.
            u=windows();u.DefWindowProcW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.DefWindowProcW.restype=w.LPARAM
            direction={10:1,11:2,12:3,13:4,14:5,15:6,16:7,17:8}[msg.wParam]
            return True,int(u.DefWindowProcW(msg.hWnd,0x112,0xF000|direction,msg.lParam))
        if kind==0xA1 and msg.wParam==9:
            u=windows();u.SetCapture.argtypes=[w.HWND];u.SetCapture.restype=w.HWND
            u.SetCapture(msg.hWnd);self.pressed=True;self.buttons[1].setDown(True)
            return True,0
        if self.pressed and kind in (0xA2,0x202):
            self.pressed=False;self.buttons[1].setDown(False)
            u=windows();point=w.POINT();u.GetCursorPos.argtypes=[c.POINTER(w.POINT)]
            u.GetCursorPos(c.byref(point));u.ReleaseCapture()
            if self.hit(point.x,point.y)==9:self.toggle_maximize()
            return True,0
        if kind==0x215:self.pressed=False;self.buttons[1].setDown(False)
        if kind==0x24:
            class MinMax(c.Structure):_fields_=[(key,w.POINT) for key in ('reserved','maxsize','maxposition','mintrack','maxtrack')]
            class Monitor(c.Structure):_fields_=[('size',w.DWORD),('monitor',w.RECT),('work',w.RECT),('flags',w.DWORD)]
            u=windows();u.MonitorFromWindow.argtypes=[w.HWND,w.DWORD];u.MonitorFromWindow.restype=w.HANDLE
            u.GetMonitorInfoW.argtypes=[w.HANDLE,c.POINTER(Monitor)]
            monitor=Monitor();monitor.size=c.sizeof(monitor)
            if u.GetMonitorInfoW(u.MonitorFromWindow(msg.hWnd,2),c.byref(monitor)):
                info=MinMax.from_address(msg.lParam);info.maxposition=w.POINT(monitor.work.left-monitor.monitor.left,monitor.work.top-monitor.monitor.top)
                info.maxsize=w.POINT(monitor.work.right-monitor.work.left,monitor.work.bottom-monitor.work.top)
                scale=self.shell.devicePixelRatioF();info.mintrack=w.POINT(round(self.shell.minimumWidth()*scale),round(self.shell.minimumHeight()*scale))
                return True,0
        return False,0
