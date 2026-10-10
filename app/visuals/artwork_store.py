"""Indexed immutable PNG storage. Only explicit working-file provenance is reclaimable.

No lifetime disk quota: reserve encoded bytes against physical free space plus
64 MiB headroom for metadata/checkpoints. Optional operator budget is disclosed.
Legacy files and saved dependencies are never adopted as disposable work.
"""
from pathlib import Path
import os, uuid, sqlite3, threading, shutil, time
from concurrent.futures import CancelledError

HEADROOM=64*1024*1024
_stores={};_lock=threading.RLock()

def check_cancel(cancel):
    if cancel is not None and cancel.is_set():raise CancelledError('Write cancelled; accepted pixels retained until explicit discard.')

def get_store(folder):
    path=str(Path(folder).resolve())
    with _lock:
        if path not in _stores:_stores[path]=Store(path)
        return _stores[path]

class Store:
    def __init__(self,folder):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.owner=uuid.uuid4().hex;self.scan=None;self.last_scan=0;self.active_tokens=set();self.cleanup_errors={}
        self.db=sqlite3.connect(self.folder/'.zerawave-store.sqlite3',timeout=2,check_same_thread=False)
        self.db.executescript("""CREATE TABLE IF NOT EXISTS files(name TEXT PRIMARY KEY, bytes INTEGER NOT NULL, kind TEXT NOT NULL, owner TEXT, state TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY, bytes INTEGER NOT NULL, owner TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS totals(id INTEGER PRIMARY KEY CHECK(id=1), bytes INTEGER NOT NULL, count INTEGER NOT NULL, reserved INTEGER NOT NULL, written INTEGER NOT NULL, reclaimed INTEGER NOT NULL);
        INSERT OR IGNORE INTO totals VALUES(1,0,0,0,0,0);
        CREATE TRIGGER IF NOT EXISTS file_add AFTER INSERT ON files BEGIN UPDATE totals SET bytes=bytes+new.bytes,count=count+1 WHERE id=1; END;
        CREATE TRIGGER IF NOT EXISTS file_del AFTER DELETE ON files BEGIN UPDATE totals SET bytes=bytes-old.bytes,count=count-1 WHERE id=1; END;
        CREATE TRIGGER IF NOT EXISTS file_update AFTER UPDATE OF bytes ON files BEGIN UPDATE totals SET bytes=bytes+new.bytes-old.bytes WHERE id=1; END;
        CREATE TRIGGER IF NOT EXISTS reserve_add AFTER INSERT ON reservations BEGIN UPDATE totals SET reserved=reserved+new.bytes WHERE id=1; END;
        CREATE TRIGGER IF NOT EXISTS reserve_del AFTER DELETE ON reservations BEGIN UPDATE totals SET reserved=reserved-old.bytes WHERE id=1; END;""")
        columns={r[1] for r in self.db.execute('PRAGMA table_info(reservations)')}
        if 'target' not in columns:self.db.execute('ALTER TABLE reservations ADD COLUMN target TEXT')
        self.db.execute('CREATE TABLE IF NOT EXISTS owners(id TEXT PRIMARY KEY)');self.db.commit()
        # A byte lock proves another Store's writer has ended, including normal
        # process exit/interruption. PID reuse and filenames do not prove that.
        import msvcrt
        self.owner_file=(self.folder/('.zw-owner-'+self.owner+'.lock')).open('a+b')
        self.owner_file.write(b'0');self.owner_file.flush();self.owner_file.seek(0);msvcrt.locking(self.owner_file.fileno(),msvcrt.LK_NBLCK,1)
        self.db.execute('INSERT INTO owners VALUES(?)',(self.owner,));self.db.commit()
        self._reconcile_writers()
        self.audit=None
        self.budget=int(os.environ['ZERAWAVE_ARTWORK_BUDGET_BYTES']) if os.environ.get('ZERAWAVE_ARTWORK_BUDGET_BYTES') else None
        if self.budget is not None and self.budget<=0:raise ValueError('Artwork working budget must be positive.')
        self.free=0;self.next_space=0;self.legacy_bytes=0;self.reconcile(4096)
    def _reconcile_reservations(self,owner,limit=64):
        # A live Store knows which of its own worker tokens are still active.
        # An inactive token can be reconciled after failure without restarting.
        for token,target in self.db.execute('SELECT id,target FROM reservations WHERE owner=? LIMIT ?',(owner,limit)).fetchall():
            if owner==self.owner and token in self.active_tokens:continue
            if target:
                temporary=(self.folder/target).with_suffix('.'+token+'.tmp')
                try:temporary.unlink(missing_ok=True)
                except OSError as exc:self.cleanup_errors[token]=str(exc)[:160];continue
                row=self.db.execute('SELECT state FROM files WHERE name=?',(target,)).fetchone()
                if row and row[0]=='writing':
                    final=self.folder/target
                    if final.exists():
                        size=final.stat().st_size
                        self.db.execute("UPDATE files SET bytes=?,state='active' WHERE name=?",(size,target))
                        self.db.execute('UPDATE totals SET written=written+? WHERE id=1',(size,))
                    else:self.db.execute('DELETE FROM files WHERE name=?',(target,))
            self.db.execute('DELETE FROM reservations WHERE id=?',(token,));self.cleanup_errors.pop(token,None)
        self.db.commit()
    def _reconcile_writers(self):
        import msvcrt
        for owner, in self.db.execute('SELECT id FROM owners WHERE id!=? LIMIT 64',(self.owner,)).fetchall():
            path=self.folder/('.zw-owner-'+owner+'.lock')
            try:
                with path.open('a+b') as guard:
                    guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_NBLCK,1)
                    self._reconcile_reservations(owner)
                    if self.db.execute('SELECT 1 FROM reservations WHERE owner=? LIMIT 1',(owner,)).fetchone():continue
                    # Interrupted active files remain protected; owner-death
                    # artwork recovery is outside Pass 1. Retiring intent is safe.
                    self.db.execute('DELETE FROM owners WHERE id=?',(owner,));self.db.commit()
                    guard.seek(0);msvcrt.locking(guard.fileno(),msvcrt.LK_UNLCK,1)
                path.unlink(missing_ok=True)
            except OSError:continue # live writer or unavailable lock
    def reconcile(self,limit=64):
        # One bounded scan at startup, then incremental external reconciliation.
        # Unknown/crashed active owners remain conservative; no filename inference.
        with self.lock:
            self._reconcile_reservations(self.owner)
            if self.audit is not None:
                for _ in range(limit):
                    row=self.audit.fetchone()
                    if row is None:self.audit.close();self.audit=None;break
                    name=row[0];path=self.folder/name
                    try:
                        if path.is_file():self.db.execute('UPDATE files SET bytes=? WHERE name=?',(path.stat().st_size,name))
                        else:self.db.execute("DELETE FROM files WHERE name=? AND state!='writing'",(name,))
                    except OSError:pass
                self.db.commit()
                if self.audit is None:self.legacy_bytes=self.db.execute("SELECT COALESCE(SUM(bytes),0) FROM files WHERE kind='legacy'").fetchone()[0]
                return
            if self.scan is None:
                if time.monotonic()-self.last_scan<30:return
                self._reconcile_writers()
                self.scan=os.scandir(self.folder)
            for _ in range(limit):
                try:entry=next(self.scan)
                except StopIteration:self.scan.close();self.scan=None;self.last_scan=time.monotonic();self.audit=self.db.execute('SELECT name FROM files ORDER BY name');break
                if entry.name.lower().endswith('.png') and entry.is_file():
                    size=entry.stat().st_size
                    self.db.execute("INSERT INTO files VALUES(?,?,'legacy',NULL,'active') ON CONFLICT(name) DO UPDATE SET bytes=excluded.bytes",(entry.name,size))
            self.db.commit()
    def state(self):
        with self.lock:
            if time.monotonic()>=self.next_space:
                try:self.free=shutil.disk_usage(self.folder).free
                except OSError:self.free=None
                self.next_space=time.monotonic()+1
            size,count,reserved,written,reclaimed=self.db.execute('SELECT bytes,count,reserved,written,reclaimed FROM totals WHERE id=1').fetchone()
            return dict(bytes=size,files=count,reserved_bytes=reserved,written_bytes=written,reclaimed_bytes=reclaimed,physical_free_bytes=self.free,headroom_bytes=HEADROOM,optional_budget_bytes=self.budget,reconciling=self.scan is not None or self.audit is not None,protected_legacy_bytes=self.legacy_bytes,temporary_cleanup_failures=dict(self.cleanup_errors))
    def write(self,target,data,kind='dependency',cancel=None):
        target=Path(target)
        if target.parent.resolve()!=self.folder.resolve():raise ValueError('Indexed store path mismatch.')
        check_cancel(cancel)
        with self.lock:
            self._reconcile_reservations(self.owner)
            if target.exists():
                if target.read_bytes()!=data:raise ValueError('Immutable artwork destination conflict; accepted pixels retained.')
                return False
            size,count,reserved,_,_=self.db.execute('SELECT bytes,count,reserved,written,reclaimed FROM totals WHERE id=1').fetchone()
            free=shutil.disk_usage(self.folder).free
            if free-len(data)-reserved<HEADROOM:raise OSError('Insufficient physical disk space: encoded write plus 64 MiB checkpoint headroom required; accepted pixels retained.')
            if self.budget is not None and size+reserved+len(data)>self.budget:raise OSError('Disclosed artwork working budget reached; accepted pixels retained. Increase the configured budget or Save As.')
            token=uuid.uuid4().hex
            if self.db.execute('SELECT 1 FROM files WHERE name=?',(target.name,)).fetchone():raise OSError('Artwork write/cleanup is still in progress; accepted pixels retained for Retry.')
            try:
                self.db.execute('INSERT INTO reservations(id,bytes,owner,target) VALUES(?,?,?,?)',(token,len(data),self.owner,target.name))
                self.db.execute("INSERT INTO files VALUES(?,?,?,?, 'writing')",(target.name,0,kind,self.owner));self.db.commit()
            except BaseException:self.db.rollback();raise
            self.active_tokens.add(token)
        temporary=target.with_suffix('.'+token+'.tmp');replaced=False;failure=None;cleanup_blocked=False
        try:
            with temporary.open('xb') as stream:
                for start in range(0,len(data),1024*1024):check_cancel(cancel);stream.write(data[start:start+1024*1024])
                stream.flush();os.fsync(stream.fileno())
            check_cancel(cancel);os.replace(temporary,target);replaced=True
            with self.lock:
                self.db.execute("UPDATE files SET bytes=?,state='active' WHERE name=?",(len(data),target.name))
                self.db.execute('UPDATE totals SET written=written+? WHERE id=1',(len(data),));self.db.commit()
            return True
        except BaseException as original:
            failure=original
            try:temporary.unlink(missing_ok=True)
            except OSError as cleanup:cleanup_blocked=True;original.add_note('Temporary write cleanup: '+str(cleanup))
            raise
        finally:
            try:
                with self.lock:
                    self.active_tokens.discard(token)
                    if not cleanup_blocked:
                        self.db.execute('DELETE FROM reservations WHERE id=?',(token,))
                        if not replaced:self.db.execute("DELETE FROM files WHERE name=? AND state='writing'",(target.name,))
                    self.db.commit();self.next_space=0
            except Exception as cleanup:
                if failure is not None:failure.add_note('Write journal cleanup: '+str(cleanup))
                else:raise
    def retire(self,path):
        path=Path(path)
        with self.lock:
            # Persist intent BEFORE unlink. Another normal launch can finish it.
            self.db.execute("UPDATE files SET state='retiring' WHERE name=? AND kind='working'",(path.name,));self.db.commit()
    def reclaim(self,protected=(),limit=32):
        errors={};protected={str(Path(p).resolve()).casefold() for p in protected}
        with self.lock:
            for name,size in self.db.execute("SELECT name,bytes FROM files WHERE state='retiring' AND kind='working' LIMIT ?",(limit,)).fetchall():
                path=self.folder/name
                if str(path.resolve()).casefold() in protected:continue
                try:path.unlink(missing_ok=True)
                except OSError as exc:errors[str(path)]=str(exc)[:160];continue
                self.db.execute('DELETE FROM files WHERE name=?',(name,));self.db.execute('UPDATE totals SET reclaimed=reclaimed+? WHERE id=1',(size,))
            self.db.commit();self.next_space=0
        return errors

def write_json(path,data,cancel=None):
    """Session commit point. Cancellation before replace preserves prior JSON."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
    try:
        check_cancel(cancel)
        if shutil.disk_usage(path.parent).free-len(data)<HEADROOM:raise OSError('Insufficient physical disk space for session commit plus 64 MiB headroom; prior session retained.')
        with temporary.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        check_cancel(cancel);os.replace(temporary,path)
    except BaseException as original:
        try:temporary.unlink(missing_ok=True)
        except OSError as cleanup:original.add_note('Session temporary cleanup: '+str(cleanup))
        raise
