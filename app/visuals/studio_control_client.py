"""Bounded local command/ACK client and read-only compatibility view snapshots.

No Tk interpreter/window is created here. Values remain owned in the service;
these facades only adapt the existing proof's presentation calls.
"""
from collections import deque
from studio_boundary import CommandBoundary, StateSections, MomentaryMailbox
from concurrent.futures import ThreadPoolExecutor
import uuid
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]

class OwnedJob:
    class Basic(c.Structure):
        _fields_=[('per_process',c.c_int64),('per_job',c.c_int64),('flags',w.DWORD),('min_ws',c.c_size_t),('max_ws',c.c_size_t),('active',w.DWORD),('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
    class IO(c.Structure):_fields_=[(n,c.c_uint64) for n in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
    def __init__(self):
        class Limits(c.Structure):_fields_=[('basic',OwnedJob.Basic),('io',OwnedJob.IO),('process_memory',c.c_size_t),('job_memory',c.c_size_t),('peak_process',c.c_size_t),('peak_job',c.c_size_t)]
        self.k=c.WinDLL('kernel32',use_last_error=True)
        self.k.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR];self.k.CreateJobObjectW.restype=w.HANDLE
        self.k.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD];self.k.SetInformationJobObject.restype=w.BOOL
        self.k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];self.k.AssignProcessToJobObject.restype=w.BOOL
        self.k.CloseHandle.argtypes=[w.HANDLE];self.k.CloseHandle.restype=w.BOOL
        self.handle=self.k.CreateJobObjectW(None,None);limits=Limits();limits.basic.flags=0x2000
        if not self.handle or not self.k.SetInformationJobObject(self.handle,9,c.byref(limits),c.sizeof(limits)):raise c.WinError(c.get_last_error())
    def assign(self,process):
        if not self.k.AssignProcessToJobObject(self.handle,w.HANDLE(int(process._handle))):raise c.WinError(c.get_last_error())
    def close(self):
        if self.handle:self.k.CloseHandle(self.handle);self.handle=None

class ControlClient:
    def __init__(self,host,log_path=None,cancel_event=None):
        self.condition=threading.Condition();self.responses={};self.snapshot={};self.serial=0;self.analyzer_telemetry=None;self.project_clock=None
        self.boundary=CommandBoundary(self.request,lambda:not self.closed and not self.disconnected)
        self.sections=StateSections();self.momentary=MomentaryMailbox();self.write_lock=threading.Lock();self.admission_lock=threading.RLock();self.gui_thread=None;self.completions=deque();self.full_needed=threading.Event();self.last_operation=None
        self.closed=False;self.disconnected=False;self.protocol_errors=deque(maxlen=8);self.protocol_error_count=0;self.latencies=deque(maxlen=256);self.pending=0
        self.job=OwnedJob();self.log_path=Path(log_path or ROOT/'work/studio/qt-control.log')
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        env=os.environ.copy();env['ZERAWAVE_CONTROL_HOST']=json.dumps(host);env['ZERAWAVE_CONTROL_LOG']=str(self.log_path)
        self.stderr=self.log_path.with_suffix('.bootstrap.log').open('w',encoding='utf8')
        self.process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(ROOT/'app/visuals/studio_control_service.py')],cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,text=True,encoding='utf8',bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW)
        try:self.job.assign(self.process)
        except Exception:self.process.terminate();self.job.close();raise
        self.notifier=threading.Thread(target=self.write_notifications,daemon=True,name='Studio momentary writer');self.notifier.start()
        self.reader=threading.Thread(target=self.read,daemon=True,name='Studio owner snapshots');self.reader.start()
        deadline=time.perf_counter()+15.
        while not self.snapshot and not self.disconnected:
            if cancel_event is not None and cancel_event.is_set():self.close(mode='discard');raise RuntimeError('Control owner connection cancelled after normal exit.')
            if time.perf_counter()>deadline:self.close(force=True);raise RuntimeError('Control owner startup timed out; '+str(self.log_path))
            with self.condition:self.condition.wait(timeout=.1)
        if not self.snapshot:self.close(force=True);raise RuntimeError('Control owner failed to start; '+str(self.log_path))
    def projection_fault(self,exc):
        with self.condition:
            previous=self.snapshot;self.sections.invalidate()
            if self.sections.owner:self.snapshot=self.sections.snapshot
            else:self.snapshot=dict(previous,control_boundary=dict(valid=False,stale=True))
            self.protocol_error_count+=1;self.protocol_errors.append(str(exc)[:240]);self.full_needed.set();self.condition.notify_all()
        if self.protocol_error_count<=8:
            print('Owner projection retained/resync requested: '+str(exc)[:240],file=self.stderr);self.stderr.flush()
    def read(self):
        try:
            for line in self.process.stdout:
                message=None
                try:
                    if len(line)>2*1024*1024:raise ValueError('Owner snapshot exceeds protocol limit')
                    message=json.loads(line)
                    if not isinstance(message,dict):raise ValueError('Owner message must be an object')
                    if message.get('id') is not None and type(message['id']) is not int:raise ValueError('Invalid owner reply identity')
                    self.install_message(message)
                except (ValueError,TypeError,KeyError,AttributeError) as exc:
                    self.projection_fault(exc)
                    if isinstance(message,dict) and type(message.get('id')) is int:
                        with self.condition:
                            self.responses[message['id']]=dict(id=message['id'],error='Coherent state unavailable; outcome uncertain. Same-ID reconciliation required.',outcome_uncertain=True)
                            self.condition.notify_all()
        except Exception:
            traceback.print_exc(file=self.stderr);self.stderr.flush()
        finally:
            with self.condition:self.disconnected=True;self.condition.notify_all()
    def install_message(self,message):
        with self.condition:
            if 'snapshot' in message:
                from raster_tiles import unwire_resource
                snap=message['snapshot']
                if snap.get('version')==2:
                    document=snap.get('sections',{}).get('document')
                    if document:
                        library=document.get('media_library',{})
                        library['resources']=[unwire_resource(r) for r in library.get('resources',[])]
                    if self.sections.install(snap):self.snapshot=self.sections.snapshot
                    elif not self.sections.valid:
                        self.sections.invalidate();self.snapshot=self.sections.snapshot
                        self.full_needed.set()
                        if message.get('id') is not None:message.update(error='Coherent state unavailable; command outcome is uncertain.',outcome_uncertain=True)
                else:
                    library=snap.get('media_library',{})
                    library['resources']=[unwire_resource(r) for r in library.get('resources',[])]
                    self.snapshot=snap
            if 'project_clock' in message:
                data=message['project_clock'];prior=self.project_clock
                if prior is None or data.get('epoch')!=prior.get('epoch') or (data.get('revision',-1),data.get('generation',-1),data.get('frame',-1))>=(prior.get('revision',-1),prior.get('generation',-1),prior.get('frame',-1)):self.project_clock=data
            if 'audio_analyzer' in message:
                data=message['audio_analyzer'];current=self.analyzer_telemetry
                packet=data.get('band_analyzer') or {};old_packet=(current or {}).get('band_analyzer') or {}
                newer=(current is None or data.get('generation',-1)>current.get('generation',-1)
                    or data.get('generation',-1)==current.get('generation',-1) and (not packet or packet.get('sequence',-1)>=old_packet.get('sequence',-1)))
                if newer:self.analyzer_telemetry=data
            if message.get('id') is not None:
                self.responses[message['id']]=message
                while len(self.responses)>32:self.responses.pop(next(iter(self.responses)))
            self.condition.notify_all()
    def latest_analyzer(self):
        with self.condition:
            if self.disconnected:return dict(status='Disconnected',playing=False,generation=-1,band_analyzer=None)
            full=self.snapshot.get('audio_hub',{});fast=self.analyzer_telemetry
            if fast is None or full.get('generation',-1)>fast.get('generation',-1):return full
            return fast
    def request(self,action,**data):
        if self.gui_thread==threading.get_ident():raise RuntimeError('Owner ACK wait attempted on Qt input thread; use command submission.')
        if self.closed or self.disconnected:raise RuntimeError('Control connection unavailable; command not submitted. Retain this instance and recoverable accepted work; diagnostics: '+str(self.log_path))
        began=time.perf_counter()
        if action in ('tune','range','override','reset_audio','restore_draft','authored','color_commit','color_reset','image_layers','composition'):
            data.setdefault('destination_revision',self.snapshot.get('destination_revision',0))
            data.setdefault('preview_run',self.snapshot.get('preview_run'))
        if action in ('image_layers','composition'):
            media=self.snapshot.get('media_control',{})
            data.setdefault('media_session',media.get('session'));data.setdefault('media_revision',media.get('revision'))
        with self.condition:
            if self.pending>=32:raise RuntimeError('Control command queue is busy.')
            self.serial+=1;serial=self.serial;self.pending+=1
            line=json.dumps({'id':serial,'action':action,'data':data},separators=(',',':'))
            if len(line)>524288:self.pending-=1;raise ValueError('Command exceeds protocol limit')
            try:
                self.condition.release()
                try:
                    with self.write_lock:self.process.stdin.write(line+'\n');self.process.stdin.flush()
                finally:self.condition.acquire()
                timeout=20 if action=='close' else 8 if action=='stop' else 2
                def reconciled():
                    # Project consumers need the inner accepted/rejected receipt.
                    # A generic outer applied row is not that result. On a lost
                    # ACK the ordered boundary reconciles the SAME captured IDs.
                    if action=='project':return None
                    op=data.get('operation_id')
                    return next((r for r in self.snapshot.get('media_control',{}).get('transactions',[]) if r['id']==op and r['status'] in ('applied','rejected')),None) if op else None
                if not self.condition.wait_for(lambda:serial in self.responses or self.disconnected or reconciled(),timeout):raise RuntimeError('Control ACK timed out; operation outcome is uncertain. Check diagnostics before retrying.')
                response=self.responses.pop(serial,None)
                if response is None and reconciled():
                    outcome=reconciled()
                    if outcome['status']=='rejected':raise ValueError(outcome['error'])
                    return self.snapshot
                if response is None:raise RuntimeError('Control owner disconnected during '+action)
                if 'error' in response:
                    if response.get('outcome_uncertain'):raise RuntimeError('Owner accepted operation; publication outcome is uncertain: '+response['error'])
                    raise ValueError(response['error'])
                return response.get('project_result',self.snapshot) if action=='project' else self.snapshot
            finally:self.pending-=1;self.latencies.append((action,(time.perf_counter()-began)*1000))
    @property
    def edit_count(self):
        with self.boundary.lock:return self.boundary.pending
    @property
    def state(self):return self.sections.immutable
    def submit(self,action,**data):
        with self.admission_lock:return self._submit(action,data)
    def _submit(self,action,data):
        # Capture binding at admission, never when a delayed worker starts.
        if self.sections.owner and not self.sections.valid:raise ValueError('Owner state is resynchronizing; action not submitted. Accepted work retained. Wait and repeat it.')
        snap=self.snapshot;media=snap.get('media_control',{})
        if action=='close':
            project=snap.get('project',{})
            data.setdefault('project_binding',dict(expected_epoch=project.get('epoch'),expected_revision=project.get('revision'),expected_project=project.get('project_id'),expected_command=project.get('command_revision')))
            data.setdefault('project_mode','clean')
        if action in ('tune','range','override','reset_audio','restore_draft','authored','color_commit','color_reset','image_layers','composition','composition_preview'):
            data.setdefault('destination_revision',snap.get('destination_revision',0));data.setdefault('preview_run',snap.get('preview_run'))
        if action in ('image_layers','composition','composition_preview','composition_cancel','composition_history','save','raster_retry','save_retry'):
            data.setdefault('media_session',media.get('session'))
        if action in ('image_layers','composition','composition_preview'):data.setdefault('media_revision',media.get('revision'))
        if action=='save':data.setdefault('save_after',self.last_operation)
        future=self.boundary.submit(action,data);self.last_operation=future.operation_id
        return future
    def command(self,action,**data):
        # Bound retained UI completions as well as active transport. Do not drop a
        # callback or its explicit failure to make room for another command.
        with self.condition:
            if len(self.completions)>=256:raise ValueError('UI completion queue busy; action not submitted. Wait and repeat it.')
            future=self.submit(action,**data)
            self.completions.append((future,self.snapshot.get('media_control',{}).get('session')))
        return future
    def ready_completions(self):
        ready=[]
        with self.condition:
            for item in list(self.completions):
                if item[0].done():self.completions.remove(item);ready.append(item)
        return ready
    def outcome(self,identity):return self.boundary.outcome(identity)
    def notify(self,action,**data):
        if self.closed or self.disconnected:return False
        data.setdefault('preview_run',self.snapshot.get('preview_run'))
        data.setdefault('destination_revision',self.snapshot.get('destination_revision',0))
        return self.momentary.put(action,data)
    def write_notifications(self):
        while not self.closed and not self.disconnected:
            if self.full_needed.is_set():
                item=('state_full',{});self.full_needed.clear()
            else:
                item=self.momentary.take()
                if item is None:
                    with self.momentary.condition:self.momentary.condition.wait(timeout=.05)
                    continue
            action,data=item
            try:
                line=json.dumps({'id':None,'action':action,'data':data},separators=(',',':'))
                with self.write_lock:self.process.stdin.write(line+'\n');self.process.stdin.flush()
            except (OSError,ValueError):return
    def close(self,force=False,mode=None,project_mode=None):
        if self.closed:return
        if not force and self.process.poll() is None and not self.disconnected:
            # Convenience close has no earlier GUI discard decision to rebase.
            # Read fresh state, then bind this exact close on the owner. Artwork
            # discard never authorizes video discard; its mode is separate.
            self.request('state_full')
            project=self.snapshot.get('project',{})
            binding=dict(expected_epoch=project.get('epoch'),expected_revision=project.get('revision'),expected_project=project.get('project_id'),expected_command=project.get('command_revision'))
            self.request('close',project_binding=binding,project_mode=project_mode or 'clean',**({'mode':mode} if mode else {}))
        if force:self.job.close()
        try:self.process.wait(timeout=20 if not force else 5)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Owner has not exited. Close remains incomplete; no forced termination was used.')
        self.closed=True;self.momentary.close();self.boundary.close();self.notifier.join(timeout=2)
        try:self.process.stdin.close()
        except (OSError,ValueError):pass
        self.reader.join(timeout=2);self.job.close();self.stderr.close()

class Value:
    def __init__(self,getter,setter=None):self.getter=getter;self.setter=setter
    def get(self):return self.getter()
    def set(self,value):
        if self.setter is None:raise ValueError('This snapshot field is read only')
        return self.setter(value)

class WidgetState:
    def __init__(self,enabled,text=lambda:''):self.enabled=enabled;self.text=text
    def cget(self,key):return self.text() if key=='text' else 'normal' if self.enabled() else 'disabled'

class AudioView:
    def __init__(self,client):self.client=client
    @property
    def data(self):return self.client.snapshot['audio']
    def binding(self):return [self.data['owner_key'],self.data['target_id']]
    def owner_key(self):return tuple(self.data['owner_key'])
    @property
    def target(self):return SimpleNamespace(target_id=self.data['target_id'],label=self.data['target_label'])
    @property
    def bounds(self):return self.data['bounds']
    @property
    def authored(self):return self.data['authored']
    @property
    def form(self):return self.data['form']
    @property
    def form_var(self):return Value(lambda:self.data['form_label'])
    @property
    def target_var(self):return Value(lambda:self.data['target_label'],lambda v:self.client.command('target',label=v))
    @property
    def pin(self):return Value(lambda:self.data['pin'],lambda v:self.client.command('pin',value=v))
    @property
    def enabled(self):return Value(lambda:self.data['enabled'],lambda v:self.client.command('override',value=v,binding=self.binding()))
    @property
    def status(self):return Value(lambda:self.data['status'])
    @property
    def target_info(self):return Value(lambda:self.data['target_info'])
    @property
    def vars(self):return {key:Value(lambda k=key:self.data['values'][k],lambda value,k=key:self.edit(k,value,self.binding())) for key in self.bounds}
    @property
    def focus_labels(self):return [(Value(lambda n=i:self.data['titles'][n]),'') for i in range(len(self.bounds))]
    @property
    def sliders(self):return [WidgetState(lambda n=i:self.data['editable'][n]) for i in range(len(self.bounds))]
    @property
    def range_vars(self):return {key:Value(lambda k=key:self.data['ranges'][k]['value'],lambda value,k=key:self.client.command('range',key=k,value=value,binding=self.binding())) for key in self.data['ranges']}
    @property
    def range_checks(self):return {key:WidgetState(lambda k=key:self.data['ranges'][k]['editable']) for key in self.data['ranges']}
    @property
    def author_button(self):return WidgetState(lambda:self.data['author_enabled'],lambda:self.data['author_label'])
    def edit(self,key,value,binding):return self.client.command('tune',key=key,value=value,binding=[list(binding[0]),binding[1]])
    def select_form(self,event=None,form=None,target=None):return self.client.command('form',form=form)
    def select_target(self,*args,**kwargs):pass
    def pin_changed(self):pass
    def toggle(self):pass
    def changed(self,*args):pass
    def refresh(self,*args):pass
    def reset(self):return self.client.command('reset_audio',binding=self.binding())
    def save_authored(self):return self.client.command('authored',binding=self.binding(),revision=self.data['revision'])

class ColorView:
    def __init__(self,client):self.client=client
    @property
    def targets(self):
        from color_controls import targets_for
        return targets_for(self.client.snapshot['color_scene'])
    @targets.setter
    def targets(self,value):pass
    @property
    def scene(self):return self.client.snapshot['color_scene']
    @scene.setter
    def scene(self,value):pass
    @property
    def target_choice(self):return Value(lambda:self.client.snapshot['color_target'],lambda label:self.client.command('color_target',label=label))
    def target(self):return next(t for t in self.targets if t.label==self.target_choice.get())
    def refresh(self):pass
    def commit(self,key,fields):return self.client.command('color_commit',target=self.target().id,role=key,fields=fields)
    def reset_target(self):return self.client.command('color_reset',target=self.target().id)

class OwnerView:
    def __init__(self,client):self.client=client;self.star_tuning_window=AudioView(client);self.color_editor=ColorView(client);self.held_gesture=False
    @property
    def vars(self):return {key:Value(lambda k=key:self.client.snapshot['values'][k],lambda value,k=key:self.client.command('var',key=k,value=value)) for key in self.client.snapshot['values']}
    @property
    def bonk_mode(self):return Value(lambda:self.client.snapshot['preview'].get('bonk_mode','normal').title(),lambda value:self.client.command('bonk_mode',value=value))
    def values(self):return self.client.snapshot['values']
    def color_scene(self):return self.client.snapshot['color_scene']
    @property
    def color_overrides(self):return self.client.snapshot['color_overrides']
    @property
    def color_status(self):return Value(lambda:self.client.snapshot['color_status'])
    @property
    def active_preview(self):return Value(lambda:self.client.snapshot['active_preview'])
    @property
    def running_values(self):return self.client.snapshot['running_values']
    @property
    def session_path(self):return Path(self.client.snapshot['session_path']) if self.client.snapshot['session_path'] else None
    @property
    def preview_state(self):return self.client.snapshot['preview']
    @property
    def process(self):
        if not self.client.snapshot['running']:return None
        return SimpleNamespace(pid=self.client.snapshot['renderer_launcher_pid'],poll=lambda:None if self.client.snapshot['running'] else 0)
    @property
    def color_link(self):
        return SimpleNamespace(audio_run=True,get_audio=lambda:self.client.snapshot['latest_audio'],get_window=lambda:self.client.snapshot['window']) if self.client.snapshot['running'] else None
    def select(self,path,scope=None,show=False):return self.client.command('select',path=path,scope=scope or 'main')
    def launch(self,*args):return self.client.command('start')
    def run_folder(self):return None
    def stop(self):return self.client.command('stop')
    def pause_preview(self):return self.client.command('pause')
    def bonk_preview(self):return self.client.command('bonk')
    def release_preview_holds(self):
        if not self.client.closed and not self.client.disconnected and (self.held_gesture or self.preview_state.get('held')):
            self.held_gesture=False;return self.client.notify('release')
    def hold_preview(self,owner,active):
        self.held_gesture=bool(active)
        destination='studio.Shift_L' if owner=='qt.keyboard' else 'studio.mouse'
        return self.client.notify('hold',active=active,owner=destination)
    def color_preset_folder(self):return ROOT/'work/color-presets'
