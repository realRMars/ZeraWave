"""Process-fixed coarse Cavern crystal batch; Python recipes/reference stay owned."""
from pathlib import Path
import ctypes as C,os,threading
import numpy as np
class Error(C.Structure):_fields_=[('code',C.c_int32),('message',C.c_char*252)]
class Backend:
    def __init__(self):
        self.path=Path(os.environ.get('ZERAWAVE_SURFACE_DLL') or Path(__file__).resolve().parents[2]/'work/native-surfaces/x64/abi1-migration-20261013-a/zerawave_surfaces.dll');self.dll=None
        try:
            if os.environ.get('ZERAWAVE_SURFACE_BACKEND','auto')=='python':raise OSError('Python surface reference selected')
            if C.sizeof(C.c_void_p)!=8:raise OSError('x64 surface batch required')
            dll=C.CDLL(str(self.path));dll.zw_surface_abi.argtypes=[C.POINTER(C.c_uint32)]*2;dll.zw_surface_abi.restype=C.c_int32
            abi=C.c_uint32();bits=C.c_uint32()
            if dll.zw_surface_abi(C.byref(abi),C.byref(bits)) or (abi.value,bits.value)!=(1,64):raise OSError('Surface ABI mismatch')
            dll.zw_specimens.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint64,C.POINTER(C.c_uint64),C.POINTER(Error)];dll.zw_specimens.restype=C.c_int32
            self.dll=dll;self.reason='C++ exact-recipe clipped crystal batch ABI 1'
        except (OSError,AttributeError) as exc:self.reason='Python surface reference: '+str(exc)[:160]
    def snapshot(self):return dict(route='native' if self.dll else 'python',path=str(self.path),abi=1 if self.dll else None,message=self.reason)
    def specimens(self,rows):
        if self.dll is None:return None
        source=np.asarray(rows,dtype='f8',order='C')
        if source.ndim!=2 or source.shape[1]!=13 or not 0<len(source)<=24:raise ValueError('Invalid surface descriptor batch')
        capacity=len(source)*192;output=np.empty((capacity,12),dtype='f4');written=C.c_uint64();error=Error()
        code=self.dll.zw_specimens(source.ctypes.data,len(source),output.ctypes.data,capacity,C.byref(written),C.byref(error))
        if code:raise ValueError(error.message.decode('utf8','replace'))
        if written.value>capacity:raise RuntimeError('Native surface batch exceeded output capacity')
        return output[:written.value].copy()
_backend=None
_lock=threading.Lock()
def backend():
    global _backend
    with _lock:
        if _backend is None:_backend=Backend()
        return _backend
