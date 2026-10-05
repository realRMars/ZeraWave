"""Bounded capture encoding/statistics worker; GL readback stays with its owner."""
import json
import queue
import threading
from pathlib import Path
import numpy as np


class CaptureWriter:
    def __init__(self, directory, capacity=2):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.jobs=queue.Queue(maxsize=capacity);self.records=[];self.dropped=0;self.errors=[]
        self.thread=threading.Thread(target=self.run,name='ZeraWave capture writer',daemon=True)
        self.thread.start()

    def submit(self, pixels, size, metadata):
        try:self.jobs.put_nowait((pixels,size,metadata));return True
        except queue.Full:self.dropped+=1;return False

    def run(self):
        from shader_test import save_png
        while True:
            job=self.jobs.get()
            try:
                if job is None:return
                data,(width,height),metadata=job
                pixels=np.frombuffer(data,np.uint8).reshape(height,width,3)
                # Same population statistics, computed off the playback thread.
                light=pixels.max(axis=2)
                metadata.update(contrast=float(pixels.std(axis=(0,1),dtype=np.float64).mean()),
                    dark_fraction=float((light<35).mean()),clipped_fraction=float((light>=250).mean()))
                save_png(self.directory/metadata['file'],pixels[::-1])
                self.records.append(metadata)
            except Exception as exc:self.errors.append(str(exc))
            finally:self.jobs.task_done()

    def close(self):
        if self.thread is None:return
        self.jobs.put(None);self.thread.join();self.thread=None


class ReplayTelemetry:
    """CSV-backed input sequence. Keep one mutable pending row, never a track.

    Callers can iterate/index results as before. The CSV grows on disk; RAM is
    independent of duration. Flush on close also preserves partial failed runs.
    """
    def __init__(self, path=None):
        import tempfile
        self.temporary=tempfile.TemporaryDirectory(prefix='zerawave-replay-') if path is None else None
        self.path=Path(path) if path else Path(self.temporary.name)/'rows.csv'
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.handle=self.path.open('w',newline='',encoding='utf8')
        self.pending=None;self.writer=None;self.count=0;self.closed=False;self.types={}

    def append(self, row):
        if self.closed:raise RuntimeError('Replay telemetry is closed')
        self.flush();self.pending=row;self.count+=1

    def flush(self):
        import csv
        if self.pending is None:return
        if self.writer is None:
            self.types={k:type(v) for k,v in self.pending.items()}
            self.writer=csv.DictWriter(self.handle,fieldnames=self.pending.keys());self.writer.writeheader()
        self.writer.writerow(self.pending);self.pending=None

    def close(self):
        if self.closed:return
        self.flush();self.handle.close();self.closed=True

    def __len__(self):return self.count

    def __iter__(self):
        import csv
        if not self.closed:self.flush();self.handle.flush()
        with self.path.open(newline='',encoding='utf8') as reader:
            for row in csv.DictReader(reader):
                def convert(key,value):
                    kind=self.types[key]
                    if value=='':return None
                    if kind is str:return value
                    if kind is bool:return value=='True'
                    if kind in (float,int):return kind(value)
                    try:return json.loads(value)
                    except ValueError:return value
                yield {k:convert(k,v) for k,v in row.items()}

    def __getitem__(self, index):
        if index==-1 and self.pending is not None:return self.pending
        if isinstance(index,slice):return list(self)[index]
        if index<0:index+=len(self)
        for i,row in enumerate(self):
            if i==index:return row
        raise IndexError(index)
