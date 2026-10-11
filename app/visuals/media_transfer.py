"""Optional stateless x64 ABI-1 batched Qt frame-copy adapter.

DLL selection is process-fixed. No decoder/resource/backend switching; missing
or incompatible DLL uses Qt's existing exact pixel route. Kernel holds no pointer.
"""
import ctypes as C,os,threading
from pathlib import Path
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt

class Transfer:
    def __init__(self):
        self.dll=None;self.path=Path(os.environ.get('ZERAWAVE_MEDIA_TRANSFER_DLL') or Path(__file__).resolve().parents[2]/'work/native-media/x64/b3-transfer-20261010-v2/zerawave_media_transfer.dll')
        try:
            if os.environ.get('ZERAWAVE_MEDIA_TRANSFER','auto').lower()=='qt':raise OSError('Qt copy explicitly selected at process open')
            if C.sizeof(C.c_void_p)!=8:raise OSError('Media transfer requires x64 Python')
            dll=C.CDLL(str(self.path));u=C.c_uint32;v=C.c_uint64;p=C.c_void_p
            dll.zw_media_abi.argtypes=[C.POINTER(u),C.POINTER(u)];dll.zw_media_abi.restype=C.c_int
            dll.zw_media_qt.argtypes=[p,v,p,v,u,u,v];dll.zw_media_qt.restype=C.c_int
            abi=u();bits=u()
            if dll.zw_media_abi(C.byref(abi),C.byref(bits)) or (abi.value,bits.value)!=(1,64):raise OSError('Incompatible media transfer ABI/architecture')
            self.dll=dll;self.reason='C++ media transfer ABI 1 / x64 (exact pixels)'
        except (OSError,AttributeError) as exc:self.reason='Qt media transfer fallback: '+str(exc)[:180]
    def snapshot(self):return dict(route='native' if self.dll else 'qt',abi=1 if self.dll else None,path=str(self.path),message=self.reason)
    def image(self,view,width,height):
        if width<1 or height<1 or width*height>8388608 or len(view)!=width*height*4:raise ValueError('Invalid media transfer pixel bounds.')
        if self.dll is None:return QImage(bytes(view),width,height,QImage.Format_RGBA8888_Premultiplied).flipped(Qt.Vertical).convertToFormat(QImage.Format_ARGB32_Premultiplied)
        image=QImage(width,height,QImage.Format_ARGB32_Premultiplied)
        if image.isNull():raise MemoryError('Qt frame image allocation failed.')
        source=destination=None
        try:
            source=C.c_uint8.from_buffer(view);destination=C.c_uint8.from_buffer(image.bits())
            code=self.dll.zw_media_qt(C.addressof(source),len(view),C.addressof(destination),image.sizeInBytes(),width,height,image.bytesPerLine())
            if code:raise ValueError('Native media transfer rejected buffer bounds; prior valid pixels retained.')
        finally:
            # Release ctypes exports BEFORE FrameReader releases its view/mapping.
            source=destination=None
        return image

_backend=None
_lock=threading.Lock()
def backend():
    global _backend
    with _lock:
        if _backend is None:_backend=Transfer()
        return _backend
