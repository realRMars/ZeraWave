"""Bounded local command/ACK client and read-only compatibility view snapshots.

No Tk interpreter/window is created here. Values remain owned in the service;
these facades only adapt the existing proof's presentation calls.
"""
from collections import deque
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
        self.condition=threading.Condition();self.responses={};self.snapshot={};self.serial=0;self.analyzer_telemetry=None
        self.closed=False;self.disconnected=False;self.latencies=deque(maxlen=256);self.pending=0
        self.job=OwnedJob();self.log_path=Path(log_path or ROOT/'work/studio/qt-control.log')
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        env=os.environ.copy();env['ZERAWAVE_CONTROL_HOST']=json.dumps(host);env['ZERAWAVE_CONTROL_LOG']=str(self.log_path)
        self.stderr=self.log_path.with_suffix('.bootstrap.log').open('w',encoding='utf8')
        self.process=subprocess.Popen([sys.executable,'-B','-X','utf8',str(ROOT/'app/visuals/studio_control_service.py')],cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,text=True,encoding='utf8',bufsize=1,creationflags=subprocess.CREATE_NO_WINDOW)
        try:self.job.assign(self.process)
        except Exception:self.process.terminate();self.job.close();raise
        self.reader=threading.Thread(target=self.read,daemon=True,name='Studio owner snapshots');self.reader.start()
        deadline=time.perf_counter()+15.
        while not self.snapshot and not self.disconnected:
            if cancel_event is not None and cancel_event.is_set():self.close(force=True);raise RuntimeError('Control owner connection cancelled.')
            if time.perf_counter()>deadline:self.close(force=True);raise RuntimeError('Control owner startup timed out; '+str(self.log_path))
            with self.condition:self.condition.wait(timeout=.1)
        if not self.snapshot:self.close(force=True);raise RuntimeError('Control owner failed to start; '+str(self.log_path))
    def read(self):
        try:
            for line in self.process.stdout:
                if len(line)>2*1024*1024:raise ValueError('Owner snapshot exceeds protocol limit') # includes up to 128 bounded media references
                message=json.loads(line)
                with self.condition:
                    if 'snapshot' in message:self.snapshot=message['snapshot']
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
        except Exception:
            traceback.print_exc(file=self.stderr);self.stderr.flush()
        finally:
            with self.condition:self.disconnected=True;self.condition.notify_all()
    def latest_analyzer(self):
        with self.condition:
            if self.disconnected:return dict(status='Disconnected',playing=False,generation=-1,band_analyzer=None)
            full=self.snapshot.get('audio_hub',{});fast=self.analyzer_telemetry
            if fast is None or full.get('generation',-1)>fast.get('generation',-1):return full
            return fast
    def request(self,action,**data):
        if self.closed or self.disconnected:raise RuntimeError('Control owner is unavailable. Reopen Studio; diagnostics: '+str(self.log_path))
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
                self.process.stdin.write(line+'\n');self.process.stdin.flush()
                timeout=8 if action in ('stop','close') else 2
                if not self.condition.wait_for(lambda:serial in self.responses or self.disconnected,timeout):raise RuntimeError('Control ACK timed out; operation outcome is uncertain. Check diagnostics before retrying.')
                response=self.responses.pop(serial,None)
                if response is None:raise RuntimeError('Control owner disconnected during '+action)
                if 'error' in response:raise ValueError(response['error'])
                return self.snapshot
            finally:self.pending-=1;self.latencies.append((action,(time.perf_counter()-began)*1000))
    def notify(self,action,**data):
        """Momentary input; application arrives in ordinary owner snapshots.

        Focus/Hold release cannot wait behind a blocked lifecycle ACK. The
        owning service and renderer still validate and apply this command.
        """
        if self.closed or self.disconnected:return False
        line=json.dumps({'id':None,'action':action,'data':data},separators=(',',':'))
        if len(line)>524288:raise ValueError('Command exceeds protocol limit')
        with self.condition:
            try:self.process.stdin.write(line+'\n');self.process.stdin.flush()
            except (OSError,ValueError):return False
        return True
    def close(self,force=False):
        if self.closed:return
        try:
            if not force and not self.disconnected:self.request('close')
        finally:
            self.closed=True
            if force:self.job.close()
            try:self.process.stdin.close()
            except (OSError,ValueError):pass
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
            self.job.close();self.stderr.close()

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
    def target_var(self):return Value(lambda:self.data['target_label'],lambda v:self.client.request('target',label=v))
    @property
    def pin(self):return Value(lambda:self.data['pin'],lambda v:self.client.request('pin',value=v))
    @property
    def enabled(self):return Value(lambda:self.data['enabled'],lambda v:self.client.request('override',value=v,binding=self.binding()))
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
    def range_vars(self):return {key:Value(lambda k=key:self.data['ranges'][k]['value'],lambda value,k=key:self.client.request('range',key=k,value=value,binding=self.binding())) for key in self.data['ranges']}
    @property
    def range_checks(self):return {key:WidgetState(lambda k=key:self.data['ranges'][k]['editable']) for key in self.data['ranges']}
    @property
    def author_button(self):return WidgetState(lambda:self.data['author_enabled'],lambda:self.data['author_label'])
    def edit(self,key,value,binding):return self.client.request('tune',key=key,value=value,binding=[list(binding[0]),binding[1]])
    def select_form(self,event=None,form=None,target=None):return self.client.request('form',form=form)
    def select_target(self,*args,**kwargs):pass
    def pin_changed(self):pass
    def toggle(self):pass
    def changed(self,*args):pass
    def refresh(self,*args):pass
    def reset(self):return self.client.request('reset_audio',binding=self.binding())
    def save_authored(self):return self.client.request('authored',binding=self.binding(),revision=self.data['revision'])

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
    def target_choice(self):return Value(lambda:self.client.snapshot['color_target'],lambda label:self.client.request('color_target',label=label))
    def target(self):return next(t for t in self.targets if t.label==self.target_choice.get())
    def refresh(self):return self.client.request('color_refresh')
    def commit(self,key,fields):return self.client.request('color_commit',target=self.target().id,role=key,fields=fields)
    def reset_target(self):return self.client.request('color_reset',target=self.target().id)

class OwnerView:
    def __init__(self,client):self.client=client;self.star_tuning_window=AudioView(client);self.color_editor=ColorView(client);self.held_gesture=False
    @property
    def vars(self):return {key:Value(lambda k=key:self.client.snapshot['values'][k],lambda value,k=key:self.client.request('var',key=k,value=value)) for key in self.client.snapshot['values']}
    @property
    def bonk_mode(self):return Value(lambda:self.client.snapshot['preview'].get('bonk_mode','normal').title(),lambda value:self.client.request('bonk_mode',value=value))
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
    def select(self,path,scope=None,show=False):return self.client.request('select',path=path,scope=scope or 'main')
    def launch(self,*args):return self.client.request('start')
    def run_folder(self):return None
    def stop(self):return self.client.request('stop')
    def pause_preview(self):return self.client.request('pause')
    def bonk_preview(self):return self.client.request('bonk')
    def release_preview_holds(self):
        if not self.client.closed and not self.client.disconnected and (self.held_gesture or self.preview_state.get('held')):
            self.held_gesture=False;return self.client.notify('release')
    def hold_preview(self,owner,active):
        self.held_gesture=bool(active)
        destination='studio.Shift_L' if owner=='qt.keyboard' else 'studio.mouse'
        return self.client.notify('hold',active=active,owner=destination)
    def color_preset_folder(self):return ROOT/'work/color-presets'
