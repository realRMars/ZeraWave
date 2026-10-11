"""Exact optional native/Qt transfer parity and ABI/buffer checks; no scanout."""
from pathlib import Path
import sys,json,hashlib,time,ctypes as C
import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt
from media_transfer import backend

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);core=backend();rng=np.random.default_rng(4703);rows=[]
    for w,h in [(1,1),(3,7),(7,3),(16,8),(2558,1388)]:
        a=rng.integers(0,256,(h,w,4),dtype=np.uint8);a[:,:,:3]=((a[:,:,:3].astype('u2')*a[:,:,3:4]+127)//255).astype('u1');source=bytearray(a.tobytes());view=memoryview(source)
        reference=QImage(bytes(view),w,h,QImage.Format_RGBA8888_Premultiplied).flipped(Qt.Vertical).convertToFormat(QImage.Format_ARGB32_Premultiplied)
        t=time.perf_counter();actual=core.image(view,w,h);cost=(time.perf_counter()-t)*1000
        assert bytes(actual.constBits())==bytes(reference.constBits()),(w,h)
        view.release();source.extend(b'x') # no leaked ctypes/memoryview export
        rows.append(dict(size=[w,h],hash=hashlib.sha256(bytes(actual.constBits())).hexdigest(),ms=cost))
    for w,h,n in [(0,2,0),(3,2,23),(8388609,1,0)]:
        try:core.image(memoryview(bytearray(n)),w,h);raise AssertionError('Invalid transfer accepted')
        except ValueError:pass
    if core.dll:
        src=(C.c_uint8*4)(1,2,3,4);dst=(C.c_uint8*4)(7,7,7,7)
        assert core.dll.zw_media_qt(C.addressof(src),3,C.addressof(dst),4,1,1,4)==1
        assert list(dst)==[7,7,7,7]
    (out/'RESULT.json').write_text(json.dumps(dict(result='PASS',route=core.snapshot(),parity=rows,bounds='Python and native ABI reject invalid buffers without modifying destination',exports='No buffer export retained after the call'),indent=2));print('PASS',out,core.snapshot(),flush=True)

if __name__=='__main__':run()
