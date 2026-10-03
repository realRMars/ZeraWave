"""Project-owned close boundary for the inspected SoundCard 0.4.6 Windows ABI.

Original implementation of WASAPI Stop/IUnknown Release ownership, not a vendor
patch. Stop success includes S_FALSE. Actual reference release, not Stop alone,
is the proof used by CaptureStream. No audio APIs run when this module imports.
"""
import hashlib
from pathlib import Path
import sys
import threading

BACKEND_SHA256 = '5ab62ea6bd3d3d2ae495241e5e7b9de5cdbd9076d4809ebbadb1ea03f463dde6'
_VERIFIED = None


def signed_hresult(value):
    unsigned = int(value) & 0xffffffff
    return unsigned - 0x100000000 if unsigned & 0x80000000 else unsigned


def owned_cleanup(recorder):
    """Only bind the actual Windows backend, checking its inspected private ABI."""
    global _VERIFIED
    if type(recorder).__module__ != 'soundcard.mediafoundation':
        return None  # Other platforms and existing external test doubles.
    module = sys.modules.get('soundcard.mediafoundation')
    if module is None or type(recorder) is not module._Recorder:
        raise RuntimeError('Unrecognized Windows capture recorder ownership')
    if _VERIFIED is not module:
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != BACKEND_SHA256:
            raise RuntimeError('Windows capture cleanup ABI changed; this player needs review')
        _VERIFIED = module
    return WasapiCleanup(recorder, module._ffi)


class WasapiCleanup:
    def __init__(self, recorder, ffi):
        self.recorder, self.ffi = recorder, ffi
        self.owner = threading.get_ident()
        self.finished = False
        self.report = None

    def close(self):
        if threading.get_ident() != self.owner:
            raise RuntimeError('Capture cleanup must run on its owning worker')
        if self.finished:
            return self.report
        # Latch before dispatch: an exception after native Release may be
        # ambiguous. Never dispatch it again or infer success from a null flag.
        self.finished = True
        report = dict(owner_thread=self.owner, stop_hresult=None, stop_error=None,
                      stop_succeeded=False, pointers={}, released=False)
        self.report = report
        try:
            ptr = getattr(self.recorder, '_ptr', None)
            if ptr is not None and ptr[0] != self.ffi.NULL:
                raw = signed_hresult(ptr[0][0].lpVtbl.Stop(ptr[0]))
                report['stop_hresult'] = f'0x{raw & 0xffffffff:08x}'
                report['stop_succeeded'] = raw >= 0
                if raw < 0:
                    report['stop_error'] = 'Native Stop failed: ' + report['stop_hresult']
            else:
                report['stop_error'] = 'Audio client was not acquired'
        except Exception as exc:
            report['stop_error'] = str(exc)
        finally:
            # Each acquired reference gets exactly one Release attempt, even
            # after Stop failure/exception or another reference's Release error.
            for name in ('_ppCaptureClient', '_ptr'):
                try:
                    ptr = getattr(self.recorder, name, None)
                    if ptr is None or ptr[0] == self.ffi.NULL:
                        report['pointers'][name] = dict(state='not_owned')
                        continue
                    count = int(ptr[0][0].lpVtbl.Release(ptr[0]))
                    if not 0 <= count <= 0xffffffff:
                        raise RuntimeError('Invalid native reference count')
                    ptr[0] = self.ffi.NULL
                    report['pointers'][name] = dict(state='released', remaining_refs=count)
                except Exception as exc:
                    report['pointers'][name] = dict(state='unconfirmed', error=str(exc))
        report['released'] = all(x['state'] in ('released', 'not_owned')
                                 for x in report['pointers'].values())
        return report
