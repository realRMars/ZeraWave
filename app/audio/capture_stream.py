"""Owned capture/analysis worker with bounded mailbox and observable release.

The owner may request_stop without blocking its UI. Only this worker enters,
reads and exits the recorder. A failed exit never counts as confirmed release.
"""
from collections import deque
import threading
import time


class CaptureStream:
    def __init__(self, capture, analyze, capacity=64, generation=0):
        self.capture = capture
        self.analyze = analyze
        self.capacity = capacity
        self.generation = generation
        self.frames = deque()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.worker = None
        self.error = None
        self.close_error = None
        self.released = False
        self.analyzed = self.coalesced = 0
        self.started_at = self.read_started_at = None
        self.last_read_at = self.last_packet_at = None

    def start(self):
        if self.worker is not None:
            raise RuntimeError('Capture stream already started')
        self.started_at = time.perf_counter()
        self.worker = threading.Thread(target=self._run, name='ZeraWave capture analysis', daemon=True)
        try:
            self.worker.start()
        except Exception as exc:
            self.error = exc
            if not self.worker.is_alive():
                self.released = True  # Recorder was never entered.
            raise

    def _run(self):
        try:
            self.capture.start()
            while not self.stop_event.is_set():
                self.read_started_at = time.perf_counter()
                samples = self.capture.read(numframes=2048)
                self.last_read_at = time.perf_counter()
                if self.stop_event.is_set():
                    break
                frame = self.analyze(samples)
                with self.lock:
                    if self.stop_event.is_set():
                        break
                    if len(self.frames) >= self.capacity:
                        self.frames.popleft()
                        self.coalesced += 1
                    self.last_packet_at = time.perf_counter()
                    self.frames.append((self.last_packet_at, frame))
                    self.analyzed += 1
        except Exception as exc:
            self.error = exc
        finally:
            try:
                self.capture.stop()
                self.released = True
            except Exception as exc:
                self.close_error = exc
                if self.error is None:
                    self.error = exc

    def drain(self):
        if self.error is not None:
            raise RuntimeError('Audio capture stream failed') from self.error
        with self.lock:
            frames = list(self.frames)
            self.frames.clear()
            return frames

    def health(self):
        return dict(alive=self.worker is not None and self.worker.is_alive(),
                    released=self.released, close_error=self.close_error,
                    started_at=self.started_at, read_started_at=self.read_started_at,
                    last_read_at=self.last_read_at, last_packet_at=self.last_packet_at)

    def request_stop(self):
        self.stop_event.set()
        with self.lock:
            self.frames.clear()

    def stop(self):
        # Existing diagnostic callers retain their bounded blocking stop.
        # The free player uses request_stop + health, never joining on its UI.
        self.request_stop()
        if self.worker is not None:
            self.worker.join(2.)
            if self.worker.is_alive():
                raise RuntimeError('Owned audio capture did not stop within two seconds')
            if not self.released:
                raise RuntimeError('Owned audio capture release failed') from self.close_error
            self.worker = None
