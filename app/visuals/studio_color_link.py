"""Bounded local Studio pipes. Latest complete snapshot wins; GL stays on render thread."""
import json
import io
import os
import sys
import threading
from copy import deepcopy
from color_controls import validate_colors

MAX_MESSAGE = 16384
ACK_PREFIX = 'ZERAWAVE_COLOR '


class ColorInbox:
    def __init__(self, fd):
        self.fd = fd
        self.lock = threading.Lock()
        self.pending = None
        self.scene_revision=-1; self.pending_scene=None
        self.revision = -1
        self.closed = False; self.eof=False
        self.thread = threading.Thread(target=self._read,daemon=True,name='Studio color input')
        self.thread.start()

    def _read(self):
        buffer = b''
        discarding = False
        try:
            while not self.closed:
                chunk = os.read(self.fd,4096)
                if not chunk: break
                buffer += chunk
                while b'\n' in buffer:
                    line,buffer = buffer.split(b'\n',1)
                    if not discarding and len(line)<=MAX_MESSAGE:
                        self.accept(line)
                    discarding = False
                if len(buffer)>MAX_MESSAGE:
                    buffer = b''; discarding = True
        except OSError:
            pass
        finally:
            self.eof=True

    def accept(self, line):
        if self.closed: return
        message=None
        try:
            message = json.loads(line)
            if isinstance(message,dict) and message.get('kind')=='cymatics':
                from cymatics_session import validate
                revision=message.get('revision')
                if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid scene revision')
                clean=validate(message.get('config'))
                with self.lock:
                    if not self.closed and revision>self.scene_revision:self.scene_revision=revision;self.pending_scene=(revision,clean)
                return
            if not isinstance(message,dict) or message.get('kind')!='colors': raise ValueError('Unknown live update.')
            revision = message.get('revision')
            if type(revision) is not int or not 0<=revision<2**31: raise ValueError('Invalid revision.')
            colors = validate_colors(message.get('targets'))
            with self.lock:
                if self.closed or revision<=self.revision: return
                self.revision=revision; self.pending=(revision,colors)
        except (ValueError, TypeError, UnicodeError) as exc:
            print(ACK_PREFIX+json.dumps(dict(scene_error=str(exc),scene_rejected=message.get('revision')) if isinstance(message,dict) and message.get('kind')=='cymatics' else dict(error=str(exc))),flush=True)

    def take_scene(self):
        with self.lock:
            result,self.pending_scene=self.pending_scene,None
            return result

    def take(self):
        with self.lock:
            result,self.pending=self.pending,None
            return result

    def applied(self, revision, seconds, echo_clock):
        print(ACK_PREFIX+json.dumps(dict(applied=revision,seconds=seconds,echo_clock=echo_clock)),flush=True)

    def close(self):
        # The daemon blocks in raw OS read, never in Python buffered stdin cleanup.
        with self.lock: self.closed=True; self.pending=None


def configure_colors(renderer, colors=None, live=False):
    renderer.set_colors(validate_colors(colors or {}))
    if live:
        renderer.color_inbox=ColorInbox(sys.stdin.fileno())


class ColorLink:
    """One pending snapshot, one status record; background IO never blocks Tk."""
    def __init__(self, process, log):
        self.process,self.log=process,log
        self.condition=threading.Condition()
        self.pending=None;self.pending_scene=None;self.scene_revision=0
        self.closed=False
        self.revision=0
        self.status={}
        self.writer=threading.Thread(target=self._write,daemon=True,name='Studio color output')
        self.reader=threading.Thread(target=self._read,daemon=True,name='Studio preview log')
        self.writer.start(); self.reader.start()

    def submit(self, colors):
        clean=validate_colors(colors)
        with self.condition:
            if self.closed: return None
            self.revision+=1
            self.pending=dict(kind='colors',revision=self.revision,targets=deepcopy(clean))
            self.condition.notify()
            return self.revision

    def submit_scene(self,config):
        from cymatics_session import validate
        clean=validate(config)
        with self.condition:
            if self.closed:return None
            self.scene_revision+=1;self.pending_scene=dict(kind='cymatics',revision=self.scene_revision,config=clean)
            self.condition.notify();return self.scene_revision

    def _write(self):
        try:
            while True:
                with self.condition:
                    self.condition.wait_for(lambda:self.pending is not None or self.pending_scene is not None or self.closed)
                    if self.closed: break
                    if self.pending is not None:message,self.pending=self.pending,None
                    else:message,self.pending_scene=self.pending_scene,None
                payload=(json.dumps(message,separators=(',',':'))+'\n').encode('utf-8')
                if len(payload)>MAX_MESSAGE: raise ValueError('Live update is too large.')
                # Raw unbuffered pipe may write partially; keep each snapshot framed.
                view=memoryview(payload)
                while view:
                    count=self.process.stdin.write(view)
                    if not count: raise BrokenPipeError('Preview input closed.')
                    view=view[count:]
        except (OSError,ValueError) as exc:
            with self.condition:
                self.status=dict(error=str(exc)); self.closed=True; self.pending=None
        finally:
            try: self.process.stdin.close()
            except OSError: pass

    def _read(self):
        stream=io.BufferedReader(self.process.stdout)
        try:
            while True:
                line=stream.readline(65536)
                if not line: break
                text=line.decode('utf-8',errors='replace')
                self.log.write(text); self.log.flush()
                if text.startswith(ACK_PREFIX):
                    try: status=json.loads(text[len(ACK_PREFIX):])
                    except ValueError: continue
                    with self.condition:
                        if "applied" in status:self.status.pop("error",None)
                        self.status.update(status)
        finally:
            self.log.close()
            stream.close()

    def get_status(self):
        with self.condition: return dict(self.status)

    def close(self):
        with self.condition:
            self.closed=True; self.pending=None; self.condition.notify_all()
        self.writer.join(timeout=1.)
        self.reader.join(timeout=1.)
