"""Bounded Windows captured mouse history; no reconstructed/smoothed points.

GetMouseMovePointsEx returns at most 64 points including other threads. A gesture
admits only points after its press and before the delivered event, ordered from
old to new. Missing/ambiguous history falls back to delivered Qt coordinates.
"""
import os,ctypes as C,time
from PySide6.QtCore import QPointF,QEvent

def delta(a,b):return ((int(a)-int(b)+0x80000000)&0xffffffff)-0x80000000

class MouseHistory:
    def __init__(self,canvas,event):
        self.canvas=canvas;self.last=QPointF(event.position());self.stamp=int(event.timestamp())&0xffffffff;self.start=self.stamp;self.key=None;self.api=None
        if os.name!='nt' or not event.spontaneous() or not self.stamp:return
        from ctypes import wintypes as W
        class Move(C.Structure):_fields_=[('x',C.c_int),('y',C.c_int),('time',W.DWORD),('extra',C.c_size_t)]
        self.Move=Move;self.Point=W.POINT;self.api=C.WinDLL('user32',use_last_error=True)
        self.api.GetMouseMovePointsEx.argtypes=[W.UINT,C.POINTER(Move),C.POINTER(Move),C.c_int,W.DWORD];self.api.GetMouseMovePointsEx.restype=C.c_int
        self.api.ClientToScreen.argtypes=[W.HWND,C.POINTER(W.POINT)];self.api.ScreenToClient.argtypes=[W.HWND,C.POINTER(W.POINT)]
        self.hwnd=int(canvas.winId());self.key=self.screen_key(self.last,self.stamp)
        self.pin_boundary()
    def pin_boundary(self):
        # A button timestamp need not equal the previous WM_MOUSEMOVE timestamp.
        # Remember the actual preceding record so equal-millisecond subsequent
        # moves are not lost solely because of the coarse timestamp boundary.
        try:
            key=self.screen_key(self.last,self.stamp);query=self.Move(key[1]&0xffff,key[2]&0xffff,0,0);buffer=(self.Move*64)();n=self.api.GetMouseMovePointsEx(C.sizeof(self.Move),C.byref(query),buffer,64,1)
            if n>0 and delta(self.start,buffer[0].time)>=0:self.key=(int(buffer[0].time),key[1],key[2])
        except (OSError,ValueError):pass
    def screen_key(self,p,stamp):
        dpr=self.canvas.devicePixelRatioF();q=self.Point(round(p.x()*dpr),round(p.y()*dpr))
        if not self.api.ClientToScreen(self.hwnd,C.byref(q)):raise OSError('Mouse coordinate conversion unavailable')
        return stamp,q.x,q.y
    def samples(self,event):
        p=QPointF(event.position());stamp=int(event.timestamp())&0xffffffff;points=[];ages=[];gap=False
        self.delivery_age_ms=None;self.last_count=None;self.last_error=None
        now=int(C.windll.kernel32.GetTickCount())&0xffffffff if self.api else stamp
        age=delta(now,stamp)
        if self.api and 0<=age<=60000:self.delivery_age_ms=age
        if self.api and event.spontaneous() and stamp and delta(stamp,self.stamp)>=0:
            try:
                key=self.screen_key(p,stamp);query=self.Move(key[1]&0xffff,key[2]&0xffff,stamp,0);buffer=(self.Move*64)();n=self.api.GetMouseMovePointsEx(C.sizeof(self.Move),C.byref(query),buffer,64,1)
                if n<0:
                    self.last_error=C.get_last_error();query.time=0;n=self.api.GetMouseMovePointsEx(C.sizeof(self.Move),C.byref(query),buffer,64,1)
                self.last_count=n
                if n<0:self.last_error=C.get_last_error()
                if n>0:
                    right=self.api.GetSystemMetrics(76)+self.api.GetSystemMetrics(78);bottom=self.api.GetSystemMetrics(77)+self.api.GetSystemMetrics(79)
                    records=[(int(q.time),q.x-65536 if q.x>=right else q.x,q.y-65536 if q.y>=bottom else q.y) for q in buffer[:n]]
                    stop=next((i for i,q in enumerate(records) if q==self.key),None)
                    recent=records[:stop] if stop is not None else [q for q in records if delta(q[0],self.stamp)>0]
                    gap=n==64 and stop is None and delta(records[-1][0],self.stamp)>0
                    dpr=self.canvas.devicePixelRatioF()
                    for t,x,y in reversed(recent):
                        if delta(t,self.start)<0 or delta(stamp,t)<0:continue
                        q=self.Point(x,y)
                        if not self.api.ScreenToClient(self.hwnd,C.byref(q)):raise OSError('Mouse history conversion unavailable')
                        pos=QPointF(q.x/dpr,q.y/dpr)
                        if pos==self.last:continue
                        points.append(pos);self.last=pos;ages.append(max(0,delta(now,t)) if self.delivery_age_ms is not None else None)
                if n>0:
                    actual=next((q for q in records if q[1:]==key[1:] and delta(stamp,q[0])>=0),None)
                    self.key=actual or key
                else:self.key=key
            except (OSError,ValueError):pass
        if p!=self.last:points.append(p);self.last=p
        self.stamp=stamp or self.stamp
        return points,ages,gap
