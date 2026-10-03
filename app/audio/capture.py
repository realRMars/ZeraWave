import soundcard as sc
from contextlib import contextmanager
import ctypes
import json
import os
import threading
import time
import sys
from wasapi_cleanup import owned_cleanup


@contextmanager
def backend_thread():
    """Own a balanced Windows COM initialization on the calling worker.

    SoundCard's module-level initializer runs once on its import thread; it is
    not initialization for a later enumeration worker. No recorder is opened.
    """
    if os.name != 'nt':
        yield
        return
    ole = ctypes.WinDLL('ole32')
    initialize = ole.CoInitializeEx
    initialize.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    initialize.restype = ctypes.c_long
    uninitialize = ole.CoUninitialize
    uninitialize.argtypes = []
    uninitialize.restype = None
    hr = initialize(None, 0) & 0xffffffff
    if hr not in (0, 1):
        raise RuntimeError(f'Audio worker COM initialization failed: 0x{hr:08x}')
    try:
        yield
    finally:
        uninitialize()


class SourceEnumerator:
    """One long-lived worker, coalesced requests, one undroppable result slot."""
    def __init__(self, enumerate_sources=None, context_factory=None, poll_seconds=None):
        self.enumerate_sources = enumerate_sources or list_sources
        self.context_factory = context_factory or backend_thread
        self.poll_seconds = poll_seconds
        self.lock = threading.Lock()
        self.wake = threading.Event()
        self.done = threading.Event()
        self.requested = 0
        self.result = None
        self.worker = None

    def request(self):
        with self.lock:
            if self.done.is_set():
                return self.requested
            self.requested += 1
            token = self.requested
            self.wake.set()
            if self.worker is None or not self.worker.is_alive():
                self.worker = threading.Thread(target=self.run, name='Inline endpoint enumeration', daemon=True)
                self.worker.start()
            return token

    def snapshot(self):
        with self.lock:
            return dict(self.result) if self.result is not None else None

    def run(self):
        while not self.done.is_set():
            try:
                with self.context_factory():
                    self.query_loop()
                return
            except Exception as exc:
                with self.lock:
                    self.wake.clear()
                    if not self.done.is_set():
                        self.result = dict(token=self.requested, sources=[], error=str(exc))
                # Remain the same owned worker. A Refresh arriving while error
                # publication finishes cannot be stranded behind a dying thread.
                if not self.done.is_set():
                    self.wake.wait(self.poll_seconds)

    def query_loop(self):
        while not self.done.is_set():
            requested = self.wake.wait(self.poll_seconds)
            with self.lock:
                if not requested:
                    self.requested += 1
                token = self.requested
                self.wake.clear()
            if self.done.is_set():
                return
            try:
                sources, error = self.enumerate_sources(), None
            except Exception as exc:
                sources, error = [], str(exc)
            with self.lock:
                if not self.done.is_set():
                    self.result = dict(token=token, sources=sources, error=error)

    def close(self):
        self.done.set()
        self.wake.set()


class AudioCapture:
    def __init__(self, device_name=None, samplerate=48000, channels=2, source_kind="loopback", exact_id=False, owner_generation=None):
        self.exact_id = exact_id
        if source_kind not in ("loopback", "microphone"):
            raise ValueError("Unsupported audio source type")
        self.source_kind = source_kind
        self.device_name = device_name
        self.samplerate = samplerate
        self.channels = channels
        self.owner_generation = owner_generation

        self.loopback = None
        self.recorder = None
        self.resolved = None
        self.cleanup = None
        self.cleanup_report = None

    def find_device(self):
        loopbacks = [mic for mic in sc.all_microphones(include_loopback=True)
                     if bool(mic.isloopback) == (self.source_kind == "loopback")]
        target_name = self.device_name
        if target_name is None:
            if self.source_kind == "microphone":
                raise RuntimeError("Select an explicit microphone input.")
            speaker = sc.default_speaker()
            if speaker is None: raise RuntimeError('No audio output device is available.')
            target_name = speaker.id
        self.loopback = next((mic for mic in loopbacks if mic.id == target_name or (not self.exact_id and mic.name == target_name)), None)

        if self.loopback is None:
            raise RuntimeError(
                f"{self.source_kind} device not found: {target_name}"
            )

        self.resolved = dict(id=self.loopback.id,
                             kind='loopback' if self.loopback.isloopback else 'microphone',
                             name=self.loopback.name)
        print('CAPTURE RESOLVED ' + json.dumps(dict(
            UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), PID=os.getpid(),
            requested=dict(id=self.device_name, kind=self.source_kind),
            resolved=self.resolved, samplerate=self.samplerate, channels=self.channels,
            generation=self.owner_generation,
            read_frames=2048, blocksize='backend default', exclusive_mode=False)),
            file=sys.stderr, flush=True)
        return self.loopback

    def start(self):
        if self.loopback is None:
            self.find_device()

        self.recorder = self.loopback.recorder(
            samplerate=self.samplerate,
            channels=self.channels,
        )

        self.cleanup = owned_cleanup(self.recorder)
        self.recorder.__enter__()
        print('CAPTURE OPENED ' + json.dumps(dict(UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), PID=os.getpid(), generation=self.owner_generation,
                                                resolved=self.resolved)), file=sys.stderr, flush=True)

    def read(self, numframes=2048):
        if self.recorder is None:
            raise RuntimeError("Audio capture has not been started")

        return self.recorder.record(numframes=numframes)

    def stop(self):
        if self.recorder is not None:
            try:
                if self.cleanup is None:
                    self.recorder.__exit__(None, None, None)
                else:
                    self.cleanup_report = self.cleanup.close()
                    print('CAPTURE CLEANUP ' + json.dumps(dict(
                        UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), PID=os.getpid(),
                        generation=self.owner_generation, resolved=self.resolved,
                        outcome=self.cleanup_report)), file=sys.stderr, flush=True)
                    if not self.cleanup_report['released']:
                        raise RuntimeError('Native reference release unconfirmed')
            except Exception as exc:
                print('CAPTURE RELEASE FAILED ' + json.dumps(dict(UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), PID=os.getpid(), generation=self.owner_generation,
                                                                 resolved=self.resolved, error=str(exc))), file=sys.stderr, flush=True)
                raise
            self.recorder = None
            print('CAPTURE RELEASED ' + json.dumps(dict(UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), PID=os.getpid(), generation=self.owner_generation,
                                                      resolved=self.resolved)), file=sys.stderr, flush=True)

def list_sources():
    """Concrete WASAPI endpoint identities; no dynamic default/per-app promise."""
    return [dict(kind='loopback' if mic.isloopback else 'microphone',
                 id=mic.id, name=mic.name)
            for mic in sc.all_microphones(include_loopback=True)]
