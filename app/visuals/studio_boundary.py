"""Toolkit-independent bounded commands and atomic, revisioned owner projections.

The document stays in ControlOwner. These objects own delivery/immutable views,
not another editable model. Transport calls run only on their worker threads.
"""
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict,deque
from copy import deepcopy
from types import MappingProxyType
import json,threading,time,uuid

MAX_COMMANDS=16
MAX_COMMAND_BYTES=524288
SECTIONS=('catalog','configuration','document','runtime')

def frozen(value):
    if isinstance(value,dict):return MappingProxyType({k:frozen(v) for k,v in value.items()})
    if isinstance(value,(list,tuple)):return tuple(frozen(v) for v in value)
    return value

class AdmissionError(ValueError):pass

class CommandBoundary:
    def __init__(self,send,alive=lambda:True):
        self.send=send;self.alive=alive;self.lock=threading.Lock();self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Ordered Studio boundary')
        self.stream=uuid.uuid4().hex;self.sequence=0;self.pending=0;self.closed=False;self.rows=OrderedDict();self.samples=deque(maxlen=256)
    def submit(self,action,data):
        # JSON ownership is fixed before admission, including caller binding.
        captured=json.loads(json.dumps(data,separators=(',',':')))
        with self.lock:
            if self.closed or not self.alive():raise AdmissionError('Owner unavailable; command not submitted. Retain accepted work.')
            if self.pending>=MAX_COMMANDS:raise AdmissionError('Sixteen commands pending; action not submitted. Wait and repeat it.')
            identity=uuid.uuid4().hex;seq=self.sequence+1
            captured.update(operation_id=identity,operation_stream=self.stream,operation_sequence=seq)
            if len(json.dumps({'action':action,'data':captured},separators=(',',':')))>MAX_COMMAND_BYTES:raise AdmissionError('Command exceeds protocol limit; not submitted.')
            row=dict(id=identity,action=action,status='queued',queued_at=time.perf_counter(),sequence=seq)
            self.pending+=1;self.sequence=seq;self.rows[identity]=row
            try:future=self.executor.submit(self._work,action,captured,row)
            except BaseException:self.pending-=1;self.sequence-=1;self.rows.pop(identity);raise
            while len(self.rows)>256:
                key=next(iter(self.rows))
                if self.rows[key]['status'] in ('queued','running','unknown'):break
                self.rows.pop(key)
        # Completed commands cannot be locally cancelled: that would leave a
        # sequence gap or discard an accepted edit. Cancel/Undo is an owner action.
        future.cancel=lambda:False
        future.operation_id=identity;future.command=frozen(captured);return future
    def _work(self,action,data,row):
        try:
            with self.lock:row.update(status='running',service_at=time.perf_counter())
            while self.alive():
                try:
                    value=self.send(action,**data)
                    with self.lock:row.update(status='acknowledged',completed_at=time.perf_counter())
                    return value
                except RuntimeError as exc:
                    if 'uncertain' not in str(exc):raise
                    with self.lock:row.update(status='unknown',error=str(exc),reconciliations=row.get('reconciliations',0)+1)
                    # Same captured identity, never a new non-idempotent action.
            raise RuntimeError('Owner disconnected; command outcome unknown. Keep recoverable work.')
        except Exception as exc:
            with self.lock:row.update(status='unknown' if 'unknown' in str(exc) or 'uncertain' in str(exc) else 'rejected',error=str(exc),completed_at=time.perf_counter())
            raise
        finally:
            with self.lock:
                self.pending-=1;self.samples.append(deepcopy(row))
    def outcome(self,identity):
        with self.lock:return frozen(deepcopy(self.rows.get(identity)))
    def state(self):
        with self.lock:return frozen(dict(pending=self.pending,limit=MAX_COMMANDS,command_byte_limit=MAX_COMMAND_BYTES,closed=self.closed,outcomes=deepcopy(list(self.rows.values())),note='Acknowledgement is owner acceptance only; publication and durability are separate owner outcomes.'))
    def close(self):
        with self.lock:self.closed=True
        self.executor.shutdown(wait=True,cancel_futures=False)

class MomentaryMailbox:
    """Three known Hold owners plus release-all; release has reserved admission."""
    def __init__(self):self.lock=threading.Lock();self.rows=OrderedDict();self.closed=False;self.condition=threading.Condition(self.lock)
    def put(self,action,data):
        if action not in ('hold','release'):raise ValueError('Unknown momentary command')
        key='release' if action=='release' else data.get('owner','studio.mouse')
        if key not in ('release','studio.mouse','studio.Shift_L','studio.Shift_R'):raise ValueError('Unknown Hold owner')
        with self.condition:
            if self.closed:return False
            if action=='release':self.rows.clear()
            self.rows[key]=(action,deepcopy(data));self.condition.notify();return True
    def take(self,wait=False):
        with self.condition:
            if wait:self.condition.wait_for(lambda:self.rows or self.closed)
            return self.rows.popitem(last=False)[1] if self.rows else None
    def close(self):
        with self.condition:self.closed=True;self.condition.notify_all()

class SectionPublisher:
    def __init__(self,owner):
        self.owner=owner;self.sequence=0;self.cache={};self.tokens={};self.versions={};self.full_at=0.;self.metrics=dict(builds={k:0 for k in SECTIONS},build_ms={k:0. for k in SECTIONS},full=0,delta=0)
    def packet(self,tokens,builder,identity,full=False):
        now=time.perf_counter();full=full or not self.cache or now-self.full_at>5.
        changed={}
        for key in SECTIONS:
            if key not in self.cache or tokens[key]!=self.tokens[key]:
                began=time.perf_counter();self.cache[key]=deepcopy(builder(key));self.tokens[key]=tokens[key];self.versions[key]=self.versions.get(key,0)+1
                self.metrics['builds'][key]+=1;self.metrics['build_ms'][key]=(time.perf_counter()-began)*1000;changed[key]=self.cache[key]
        if full:changed=dict(self.cache);self.full_at=now
        self.sequence+=1;self.metrics['full' if full else 'delta']+=1
        return dict(version=2,owner=self.owner,sequence=self.sequence,full=full,identity=deepcopy(identity),versions=dict(self.versions),sections=changed,projection=dict(self.metrics))

class StateSections:
    def __init__(self):self.owner=None;self.retired=set();self.sequence=0;self.versions={};self.parts={};self.immutable_parts={};self.valid=False;self.snapshot={};self.immutable=MappingProxyType({});self.identity={}
    def install(self,packet):
        if packet.get('version')!=2:return False
        owner=packet.get('owner');seq=packet.get('sequence');full=packet.get('full');versions=packet.get('versions',{});changed=packet.get('sections',{})
        identity=packet.get('identity',{})
        if isinstance(owner,str) and owner in self.retired:return False
        if not isinstance(owner,str) or type(seq) is not int or seq<1 or type(full) is not bool or not isinstance(versions,dict) or not isinstance(changed,dict) or set(versions)!=set(SECTIONS) or not isinstance(identity,dict):self.valid=False;return False
        if not isinstance(identity.get('document_session'),str) or type(identity.get('document_revision')) is not int or type(identity.get('destination_revision')) is not int or identity['document_revision']<0 or identity['destination_revision']<0:self.valid=False;return False
        if owner==self.owner and seq<=self.sequence:return False
        if (owner!=self.owner or seq!=self.sequence+1 or not self.valid) and not full:self.valid=False;return False
        if full and set(changed)!=set(SECTIONS):self.valid=False;return False
        if any(type(versions[k]) is not int or versions[k]<1 for k in SECTIONS) or any(k not in SECTIONS or not isinstance(v,dict) for k,v in changed.items()):self.valid=False;return False
        for k in SECTIONS:
            if k not in changed and (k not in self.parts or versions[k]!=self.versions.get(k)):self.valid=False;return False
            if owner==self.owner and versions[k]<self.versions.get(k,0):return False
        parts={} if owner!=self.owner else dict(self.parts);immutable={} if owner!=self.owner else dict(self.immutable_parts)
        for k,v in changed.items():parts[k]=deepcopy(v);immutable[k]=frozen(v)
        document=parts['document'].get('media_control',{})
        if (identity.get('document_session'),identity.get('document_revision'))!=(document.get('session'),document.get('revision')):self.valid=False;return False
        config=parts['configuration']
        if (identity.get('destination_revision'),identity.get('preview_run'))!=(config.get('destination_revision'),config.get('preview_run')):self.valid=False;return False
        if owner==self.owner and identity['document_revision']<self.identity['document_revision']:return False
        merged={};values={};fixed={};fvalues={}
        for k in SECTIONS:
            merged.update({n:v for n,v in parts[k].items() if n!='values'});values.update(parts[k].get('values',{}))
            fixed.update({n:v for n,v in immutable[k].items() if n!='values'});fvalues.update(immutable[k].get('values',{}))
        merged['values']=values;fixed['values']=MappingProxyType(fvalues)
        meta=deepcopy(packet['identity']);meta.update(owner=owner,projection_sequence=seq,section_versions=dict(versions),valid=True)
        merged['control_boundary']=meta;fixed['control_boundary']=frozen(meta)
        # All sections and compatibility accessors become visible together.
        if self.owner and owner!=self.owner:self.retired.add(self.owner)
        self.owner=owner;self.sequence=seq;self.versions=dict(versions);self.parts=parts;self.immutable_parts=immutable;self.identity=meta;self.snapshot=merged;self.immutable=MappingProxyType(fixed);self.valid=True;return True
    def invalidate(self):
        self.valid=False
        meta=dict(self.identity,valid=False,stale=True)
        self.snapshot=dict(self.snapshot,control_boundary=meta)
        self.immutable=MappingProxyType(dict(self.immutable,control_boundary=frozen(meta)))
