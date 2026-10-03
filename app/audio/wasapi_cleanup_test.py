"""Actual close adapter, controlled COM pointers; no SoundCard/device imports."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import threading
import json
import sys
from pathlib import Path
from wasapi_cleanup import WasapiCleanup, signed_hresult, owned_cleanup

class Pointer:
    def __init__(self, stop=0, release_error=None):
        self.calls=[]
        def Stop(ptr):
            self.calls.append(('Stop',threading.get_ident()))
            if isinstance(stop,Exception):raise stop
            return stop
        def Release(ptr):
            self.calls.append(('Release',threading.get_ident()))
            if release_error:raise release_error
            return 0
        self.interface=SimpleNamespace(lpVtbl=SimpleNamespace(Stop=Stop,Release=Release))
    def __getitem__(self,index):assert index==0;return self.interface

def fixture(stop=0, capture_error=None, audio_error=None):
    null=object();ffi=SimpleNamespace(NULL=null)
    audio=Pointer(stop,audio_error);capture=Pointer(0,capture_error)
    recorder=SimpleNamespace(_ptr=[audio],_ppCaptureClient=[capture])
    return recorder,ffi,audio,capture

def run():
    results=[]
    for hr in (0,1,0x88890004,-2004287484):
        recorder,ffi,audio,capture=fixture(hr)
        adapter=WasapiCleanup(recorder,ffi);r=adapter.close()
        assert r['released'] and r['stop_succeeded']==(signed_hresult(hr)>=0)
        assert bool(r['stop_error'])==(signed_hresult(hr)<0)
        assert recorder._ptr[0] is ffi.NULL and recorder._ppCaptureClient[0] is ffi.NULL
        assert adapter.close() is r and len(audio.calls)==2 and len(capture.calls)==1
        results.append(dict(case='HRESULT',raw=hr,outcome=r))
    recorder,ffi,audio,capture=fixture(RuntimeError('Stop threw'))
    r=WasapiCleanup(recorder,ffi).close()
    assert r['released'] and r['stop_error']=='Stop threw' and not r['stop_succeeded']
    assert len(capture.calls)==1 and len(audio.calls)==2
    results.append(dict(case='Stop exception, both references released',outcome=r))
    for first,last in [(RuntimeError('capture release ambiguous'),None),(None,RuntimeError('audio release ambiguous'))]:
        recorder,ffi,audio,capture=fixture(1,first,last);adapter=WasapiCleanup(recorder,ffi)
        r=adapter.close();assert not r['released']
        assert len(audio.calls)==2 and len(capture.calls)==1
        adapter.close();assert len(audio.calls)==2 and len(capture.calls)==1
        results.append(dict(case='partial release fails closed, no redispatch',outcome=r))
    recorder,ffi,audio,capture=fixture();del recorder._ppCaptureClient
    r=WasapiCleanup(recorder,ffi).close();assert r['released'] and r['pointers']['_ppCaptureClient']['state']=='not_owned'
    results.append(dict(case='partial enter, capture service never acquired',outcome=r))
    recorder,ffi,audio,capture=fixture();adapter=WasapiCleanup(recorder,ffi);errors=[]
    def wrong():
        try:adapter.close()
        except RuntimeError as exc:errors.append(str(exc))
    t=threading.Thread(target=wrong);t.start();t.join(1.)
    assert errors and not adapter.finished and not audio.calls and not capture.calls
    assert adapter.close()['released']
    results.append(dict(case='foreign thread forbidden; owner release confirmed',outcome=adapter.report))
    # Actual CFFI typed callbacks exercise the signed HRESULT/vtable boundary.
    import cffi
    f=cffi.FFI();f.cdef('typedef struct C C; typedef struct V {long (*Stop)(C*); unsigned int (*Release)(C*);} V; struct C {V* lpVtbl;};')
    callbacks=[];calls=[]
    def ptr(hr):
        stop=f.callback('long(C*)',lambda p:hr)
        release=f.callback('unsigned int(C*)',lambda p:(calls.append(threading.get_ident()) or 0))
        v=f.new('V*',dict(Stop=stop,Release=release));c=f.new('C*',dict(lpVtbl=v));pp=f.new('C**',c)
        callbacks.extend([stop,release,v,c,pp]);return pp
    r=WasapiCleanup(SimpleNamespace(_ptr=ptr(1),_ppCaptureClient=ptr(0)),f).close()
    assert r['released'] and r['stop_hresult']=='0x00000001' and calls==[threading.get_ident()]*2
    results.append(dict(case='actual CFFI callbacks, S_FALSE, typed pointers',outcome=r))
    # Hash/identity gate tested without importing the installed backend.
    recorder_type=type('_Recorder',(),{'__module__':'soundcard.mediafoundation'})
    module=SimpleNamespace(_Recorder=recorder_type,_ffi=f,__file__=__file__)
    with patch.dict(sys.modules,{'soundcard.mediafoundation':module}):
        try:owned_cleanup(recorder_type())
        except RuntimeError as exc:assert 'ABI changed' in str(exc)
        else:raise AssertionError('Uninspected backend accepted')
    print('PASS: real project adapter HRESULT, exception/finally, partial-enter/release, repeat, owner thread, CFFI and ABI cases')
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(results,indent=2),encoding='utf-8')

if __name__=='__main__':run()
