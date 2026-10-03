"""Bounded, uniquely owned local session logs; no audio data or shared handlers."""
from contextlib import contextmanager
import datetime
import hashlib
import json
import logging.handlers
import marshal
import os
from pathlib import Path
import re
import threading
import uuid

MAX_BYTES = 262144
BACKUPS = 2
MAX_SESSIONS = 4
_ACTIVE = set()
_GUARD = threading.Lock()
_NAME = re.compile(r'^session-\d{8}T\d{12}Z-[0-9a-f]{32}\.jsonl$')


@contextmanager
def allocation_lock(directory):
    """Serialize pruning/allocation across Windows panel processes, without waiting."""
    import msvcrt
    with (directory/'.allocation.lock').open('a+b') as lease:
        lease.seek(0, os.SEEK_END)
        if not lease.tell():
            lease.write(b'0');lease.flush()
        lease.seek(0)
        try:
            msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError('Session history is being updated by another player; retry starting the panel.') from exc
        try:
            yield
        finally:
            lease.seek(0)
            msvcrt.locking(lease.fileno(), msvcrt.LK_UNLCK, 1)


class _ByteRotation(logging.handlers.RotatingFileHandler):
    def shouldRollover(self, record):
        if self.stream is None:
            self.stream = self._open()
        self.stream.seek(0, os.SEEK_END)
        return self.stream.tell() + len((self.format(record)+'\n').encode('utf-8')) > self.maxBytes

    def handleError(self, record):
        raise  # SessionLog records failure; pipe drains must continue.


def source_binding(root, files, functions):
    """Disk-at-start hashes and actual loaded function-code hashes are distinct."""
    root = Path(root)
    return dict(files_at_start={name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},
                loaded_functions={name: hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest() for name, fn in functions.items()})


class SessionLog:
    def __init__(self, data, session_id=None):
        self.session_id = session_id or uuid.uuid4().hex
        if not re.fullmatch('[0-9a-f]{32}', self.session_id):
            raise ValueError('Invalid session log identity')
        self.directory = Path(data)/'logs'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.closed = False
        self.lock = threading.Lock()
        self.last_error = None
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        self.path = self.directory/f'session-{stamp}-{self.session_id}.jsonl'
        with _GUARD, allocation_lock(self.directory):
            self.prune(MAX_SESSIONS - 1)
            if len(self.bases()) >= MAX_SESSIONS:
                raise RuntimeError('Session log slots are busy; close another player before starting a new session.')
            # Holding this file open protects the entire rotation set on Windows.
            # A crash closes the OS handle, allowing the next owner to prune it.
            self.lease_path = Path(str(self.path)+'.lease')
            self.lease = self.lease_path.open('x', encoding='utf-8')
            self.lease.write(str(os.getpid()));self.lease.flush()
            _ACTIVE.add(str(self.path))
            try:
                self.handler = _ByteRotation(self.path, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding='utf-8')
                self.handler.setFormatter(logging.Formatter('%(message)s'))
            except Exception:
                _ACTIVE.discard(str(self.path));self.lease.close();self.lease_path.unlink(missing_ok=True)
                raise
        self.record('panel_session_begin', PID=os.getpid())

    def bases(self):
        paths = {p for p in self.directory.glob('session-*.jsonl') if _NAME.fullmatch(p.name)}
        paths.update(Path(str(p)[:-6]) for p in self.directory.glob('session-*.jsonl.lease')
                     if _NAME.fullmatch(p.name[:-6]))
        return sorted(paths)

    def prune(self, keep):
        bases = self.bases()
        for path in list(bases):
            if len(bases) <= keep:
                break
            if str(path) in _ACTIVE:
                continue
            lease = Path(str(path)+'.lease')
            try:
                # An active foreign owner holds this lease open; Windows refuses
                # deletion. Never delete its base or backups when that happens.
                lease.unlink(missing_ok=True)
                path.unlink(missing_ok=True)
            except OSError:
                continue
            for i in range(1, BACKUPS + 1):
                Path(str(path)+f'.{i}').unlink(missing_ok=True)
            bases.remove(path)

    def record(self, event, **fields):
        row = dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   session=self.session_id, PID=os.getpid(), event=event, detail=fields)
        text = json.dumps(row, ensure_ascii=False, default=str)
        if len(text.encode('utf-8')) > 32768:
            text = json.dumps(dict(UTC=row['UTC'],session=self.session_id,PID=os.getpid(),event=event,
                                   bounded=True,detail=text[:7000]),ensure_ascii=False)
        with self.lock:
            if self.closed:
                return False
            try:
                self.handler.emit(logging.LogRecord('ZeraWaveSession',20,'',0,text,(),None))
                return True
            except Exception as exc:
                self.last_error = str(exc)
                return False

    def close(self):
        self.record('panel_session_end')
        with self.lock:
            if self.closed:
                return
            self.closed=True;self.handler.close();self.lease.close()
        with _GUARD:
            _ACTIVE.discard(str(self.path))
            self.lease_path.unlink(missing_ok=True)
