"""Authenticated, bounded localhost facade to Studio's existing ordered owner.

Server threads only submit immutable requests and await owner replies. They do
not mutate documents, decode media or create graphics/audio contexts.
"""
from pathlib import Path
from concurrent.futures import Future
import json,socket,threading,uuid,os,queue
MAX_BYTES=524288
class Server:
 def __init__(self,commands,folder):
  self.commands=commands;self.token=uuid.uuid4().hex;self.stopping=threading.Event();self.lock=threading.Lock();self.clients=set();self.threads=set();self.pending=set();self.slots=threading.BoundedSemaphore(4)
  self.listener=socket.socket();self.listener.bind(('127.0.0.1',0));self.listener.listen(4);self.listener.settimeout(.2);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);self.path=folder/('project-api-'+str(os.getpid())+'-'+uuid.uuid4().hex+'.json')
  self.endpoint=dict(protocol=1,host='127.0.0.1',port=self.listener.getsockname()[1],token=self.token,owner_pid=os.getpid());self.path.write_text(json.dumps(self.endpoint),'utf8');self.thread=threading.Thread(target=self.run,name='Studio project API',daemon=True);self.thread.start()
 def run(self):
  while not self.stopping.is_set():
   try:conn,addr=self.listener.accept()
   except socket.timeout:continue
   except OSError:break
   if not self.slots.acquire(False):
    try:conn.settimeout(.05);conn.sendall(json.dumps(dict(ok=False,error=dict(code='busy',message='Four project API clients are active; request was not admitted. Wait and reconcile its existing ID.'))).encode()+b'\n')
    except OSError:pass
    conn.close();continue
   thread=threading.Thread(target=self.serve,args=(conn,),name='Project API client',daemon=True)
   with self.lock:self.clients.add(conn);self.threads.add(thread)
   thread.start()
 def serve(self,conn):
  conn.settimeout(2.);stream=conn.makefile('rb')
  try:
   line=stream.readline(MAX_BYTES+2)
   if len(line)>MAX_BYTES or not line.endswith(b'\n'):raise ValueError('Request is oversized or incomplete.')
   packet=json.loads(line)
   if packet.get('token')!=self.token:raise PermissionError('Invalid project API token; request was not admitted.')
   if not isinstance(packet.get('request'),dict):raise ValueError('A structured project request is required.')
   future=Future()
   with self.lock:self.pending.add(future)
   try:
    if self.stopping.is_set():raise RuntimeError('Project API is closing.')
    try:self.commands.put_nowait(dict(id='api-'+uuid.uuid4().hex,action='project',data=dict(request=packet['request']),_api_reply=future))
    except queue.Full:raise RuntimeError('Owner command queue is full; request was not admitted. Wait and reconcile its existing ID.')
    result=future.result(timeout=15.)
   finally:
    with self.lock:self.pending.discard(future)
   raw=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
   if len(raw)>2*1024*1024:raise ValueError('Reply exceeds the bounded protocol.')
   conn.sendall(raw+b'\n')
  except Exception as exc:
   code='unauthorized' if isinstance(exc,PermissionError) else 'invalid_request' if isinstance(exc,(ValueError,TypeError,KeyError)) else 'transport'
   try:conn.sendall(json.dumps(dict(ok=False,error=dict(code=code,message=str(exc)))).encode()+b'\n')
   except OSError:pass
  finally:
   stream.close();conn.close()
   with self.lock:self.clients.discard(conn);self.threads.discard(threading.current_thread())
   self.slots.release()
 def close(self):
  self.stopping.set();self.listener.close();self.thread.join(2.)
  with self.lock:
   pending=list(self.pending);clients=list(self.clients);threads=list(self.threads)
  for future in pending:
   if not future.done():future.set_exception(RuntimeError('Owner is closing; unresolved operation must be reconciled by its existing ID.'))
  for conn in clients:
   try:conn.shutdown(socket.SHUT_RDWR)
   except OSError:pass
  for thread in threads:thread.join(2.)
  if self.thread.is_alive() or any(t.is_alive() for t in threads):raise RuntimeError('Project API reader has not exited.')
  if self.path.exists() and json.loads(self.path.read_text())==self.endpoint:self.path.unlink()
def call(endpoint,request,timeout=20.):
 endpoint=json.loads(Path(endpoint).read_text('utf8'))
 if endpoint.get('protocol')!=1 or endpoint.get('host')!='127.0.0.1':raise ValueError('Unsupported local project endpoint.')
 packet=json.dumps(dict(token=endpoint['token'],request=request),ensure_ascii=False,separators=(',',':')).encode('utf8')
 if len(packet)>MAX_BYTES:raise ValueError('Request exceeds 512 KiB; nothing was submitted.')
 with socket.create_connection(('127.0.0.1',endpoint['port']),timeout=timeout) as conn:
  conn.settimeout(timeout);conn.sendall(packet+b'\n');stream=conn.makefile('rb');line=stream.readline(2*1024*1024+2)
  if not line.endswith(b'\n') or len(line)>2*1024*1024:raise RuntimeError('Project reply lost/incomplete. Reconcile the same operation ID; do not repeat with a new ID.')
  return json.loads(line)
