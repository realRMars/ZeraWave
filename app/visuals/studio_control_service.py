"""One legacy business-state owner, isolated from Qt's native window thread.

JSON commands are bounded and execute on the owning Tk thread. Renderer stdin,
ACKs, scopes, authored storage and shutdown remain owned by the existing Studio.
"""
from collections import deque
from copy import deepcopy
import json
import os
from pathlib import Path
import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from studio import Studio, ROOT, STUDIO_TREES, SOURCES, selection_title
from color_controls import targets_for
from studio_scope import playback_scope,leaf_destination,compatible_scope,validate_scope
from renderer import LIVE_FORMS
from session_performance import ResourceSampler

class ControlOwner(Studio):
    def __init__(self,root,host):
        self.host=host;super().__init__(root)
        self.vars['speed'].set('Real time');self.vars['source'].set('Synthetic preview')
        root.workspace_owner=self
        self.committed_scope=None;self.destination_revision=0
        self.pause_intent=None
        self.resolution_policy=None;self.resolution_pending=None
        from studio_transport import AudioOwner
        self.audio_owner=AudioOwner()
        self.open_star_tuning();self.star_tuning_window.window.withdraw()
        self.open_color_inspector();self.color_editor.window.withdraw();self.color_editor.compact=True
    def renderer_host_environment(self):return self.host
    def launch(self,values,output,label=None):
        self.pause_intent=None
        self.resolution_pending=None
        if self.resolution_policy is None:self.host.pop('ZERAWAVE_VISUALIZER_RESOLUTION',None)
        else:self.host['ZERAWAVE_VISUALIZER_RESOLUTION']=json.dumps(self.resolution_policy)
        values=deepcopy(values)
        scope=validate_scope(values['playback_scope'],LIVE_FORMS) if values.get('playback_scope') else playback_scope(values['selection_scope'],values['selection'],LIVE_FORMS)
        if len(scope['forms'])>1 and not compatible_scope(scope):
            raise ValueError('Category playback is unavailable for these separate legacy routes. Load an individual Experimental leaf.')
        if not compatible_scope(scope) and self.audio_owner.snapshot()['playing']:
            raise ValueError('Stop audio before opening a separate legacy Experimental preview. Its audio route cannot share this transport.')
        self.committed_scope=scope
        self.host['ZERAWAVE_DESTINATION_REVISION']=str(self.destination_revision)
        if compatible_scope(scope):
            values['playback_scope']=scope
            # The normal Qt route consumes the independent audio owner's PCM.
            # Never launch loopback alongside file output or tie files to visuals.
            values['source']='Live system audio'
            self.host['ZERAWAVE_AUDIO_HUB']=self.audio_owner.environment()
        else:self.host.pop('ZERAWAVE_AUDIO_HUB',None)
        return super().launch(values,output,label)
    def color_scene(self):
        form=getattr(self,'preview_state',{}).get('current_form')
        if getattr(self,'process',None) is not None and self.process.poll() is None and form in LIVE_FORMS:
            from world_catalog import LIVE_STATES
            from studio import color_scope_for_states
            return color_scope_for_states([next(key for key,value in LIVE_STATES.items() if value==form)])
        return super().color_scene()
    def pause_preview(self):
        if not self.color_link:return
        acknowledged=self.preview_state.get('serial',-1)
        active=self.pause_intent[1] if self.pause_intent and acknowledged<self.pause_intent[0] else self.preview_state.get('paused',False)
        self.release_preview_holds()
        serial=self.preview_command('pause',active=not active)
        self.pause_intent=(serial,not active)
    def select(self,selection,scope=None,show=True):return super().select(selection,scope,show=False)
    def poll_star_tuning(self):self.star_tuning_poll_after=None

def main():
    protocol=sys.stdout
    log_path=Path(os.environ['ZERAWAVE_CONTROL_LOG']);log_path.parent.mkdir(parents=True,exist_ok=True)
    log=log_path.open('w',encoding='utf8',buffering=1);sys.stdout=sys.stderr=log
    host=json.loads(os.environ['ZERAWAVE_CONTROL_HOST']);root=tk.Tk();root.withdraw()
    errors=deque(maxlen=16);commands=queue.Queue(maxsize=32);eof=threading.Event();closing=False
    def failure(kind,exc,tb):
        text=''.join(traceback.format_exception(kind,exc,tb));errors.append(text);log.write(text)
    root.report_callback_exception=failure
    owner=ControlOwner(root,host);view=owner.star_tuning_window;drafts={}
    sampler=ResourceSampler();sampler.enabled.set()
    sampler.configure({'Qt GUI':int(host['ZERAWAVE_WORKSPACE_PID']),'control owner':os.getpid()})
    def draft_key():return json.dumps([list(view.owner_key()),view.target.target_id])
    def track_draft(before):
        key=draft_key();settings=view.settings()
        entry=drafts.setdefault(key,{'binding':[list(view.owner_key()),view.target.target_id],
            'form':view.form,'target':view.target.target_id,'baseline':before})
        entry.update(settings=deepcopy(settings),dirty=settings!=entry['baseline'])
    def before_edit():
        if draft_key() not in drafts and len(drafts)>=256:
            raise ValueError('The bounded tuning-draft history is full. Save this session and start a new session before editing another destination.')
        return view.settings()
    def colors():
        editor=owner.color_editor;choices=targets_for(owner.color_scene())
        if choices:
            if editor.target_choice.get() not in {t.label for t in choices}:
                choice=next((t for t in choices if t.scene==owner.color_scene() and t.slots),next((t for t in choices if t.slots),choices[0]))
                editor.target_choice.set(choice.label)
            editor.targets=choices;editor.scene=owner.color_scene();editor.refresh()
    colors()
    resource_sent=None
    def snapshot():
        nonlocal resource_sent
        running=owner.process is not None and owner.process.poll() is None
        resolution=owner.preview_state.get('resolution') or {}
        if running and resolution and (owner.resolution_pending is None or resolution.get('serial',-1)>=owner.resolution_pending):
            owner.resolution_policy=resolution.get('policy');owner.resolution_pending=None
        if owner.color_editor.scene!=owner.color_scene():colors()
        window=owner.color_link.get_window() if owner.color_link else None
        sampler.configure({'Qt GUI':int(host['ZERAWAVE_WORKSPACE_PID']),'control owner':os.getpid(),
            'renderer':window['pid'] if running and window else None},owner.preview_state.get('gpu_name'))
        resource=sampler.snapshot()
        stamp=(owner.preview_run,resource.get('wall'))
        if running and owner.diagnostics.get() and resource.get('wall') and stamp!=resource_sent:
            sample=dict(resource)
            renderer_sample=next((v for v in sample.get('processes',{}).values() if 'renderer' in v['roles']),{})
            for key in ('process_cpu_percent','process_cpu_seconds','process_working_set_bytes','process_peak_working_set_bytes'):
                sample[key]=renderer_sample.get(key)
            sample['sampling_owner']='control owner; renderer process counters identified by native PID'
            owner.preview_command('resources',sample=sample);resource_sent=stamp
        latest=owner.color_link.get_audio() if owner.color_link and owner.color_link.audio_run else None
        view.refresh(latest,running)
        from starfield_tuning import choices_for_form,target_windows,EDIT_FORMS
        audio={'owner_key':list(view.owner_key()),'form':view.form,'form_label':view.form_var.get(),
            'target_id':view.target.target_id,'target_label':view.target.label,
            'choices':[[t.target_id,t.label] for t in choices_for_form(view.form)],
            'bounds':view.bounds,'values':{k:view.vars[k].get() for k in view.bounds},
            'titles':[v[0].get() for v in view.focus_labels[:len(view.bounds)]],
            'authored':view.authored,'pin':view.pin.get(),'enabled':view.enabled.get(),
            'editable':[str(w.cget('state'))!='disabled' for w in view.sliders[:len(view.bounds)]],
            'ranges':{k:{'value':v.get(),'editable':str(view.range_checks[k].cget('state'))!='disabled'} for k,v in view.range_vars.items() if k in target_windows(view.target.target_id)},
            'status':view.status.get(),'target_info':view.target_info.get(),
            'author_label':str(view.author_button.cget('text')),'author_enabled':str(view.author_button.cget('state'))!='disabled',
            'revision':view.revision,'profile_status':view.profile_status.get(),'authored_path':str(view.store.authored_path)}
        return {'version':1,'owner_pid':os.getpid(),'sequence':sequence,'values':owner.values(),
            'selection':owner.selection,'selection_scope':owner.selection_scope,'selection_title':selection_title(owner.selection),
            'active_title':selection_title(owner.running_values['selection']) if running else selection_title(owner.selection),
            'catalog':STUDIO_TREES,'sources':list(SOURCES),'edit_forms':EDIT_FORMS,'color_scene':owner.color_scene(),
            'color_target':owner.color_editor.target_choice.get(),'color_overrides':owner.color_overrides,
            'color_status':owner.color_status.get(),'audio':audio,'running':running,
            'color_transport':{'revision':owner.last_color_revision,'ack':owner.color_link.get_status() if owner.color_link else {}},
            'preview_transport':{'submitted_serial':owner.color_link.preview_serial,'run':owner.color_link.preview_run,'closed':owner.color_link.closed,'pending':len(owner.color_link.pending_controls),'writer_alive':owner.color_link.writer.is_alive(),'reader_alive':owner.color_link.reader.is_alive()} if owner.color_link else None,
            'renderer_launcher_pid':owner.process.pid if running else None,
            'preview':owner.preview_state,'window':owner.color_link.get_window() if owner.color_link else None,
            'committed_scope':owner.committed_scope,'destination_revision':owner.destination_revision,
            'scope_note':'Category BONK unavailable for separate legacy routes; this Experimental leaf is isolated.' if owner.committed_scope and not compatible_scope(owner.committed_scope) else '',
            'preview_run':owner.preview_run,
            'resources':resource,
            'resolution':dict(policy=owner.resolution_policy,pending=owner.resolution_pending is not None,
                limit=resolution.get('limit',16384),error=resolution.get('error') if running else None),
            'startup':(owner.color_link.get_status().get('startup') or {}) if owner.color_link else {},
            'latest_audio':latest,'running_values':getattr(owner,'running_values',None),
            'audio_hub':owner.audio_owner.snapshot(),
            'tuning_drafts':list(drafts.values()),'tuning_dirty':any(d['dirty'] for d in drafts.values()),
            'session_path':str(owner.session_path) if owner.session_path else None,
            'active_preview':owner.active_preview.get(),'status':owner.status.get(),'errors':list(errors)}
    out_lock=threading.Lock();sequence=0
    def emit(value):
        line=json.dumps(value,separators=(',',':'))
        if len(line)>524288:raise RuntimeError('Control snapshot exceeded bounded protocol size')
        with out_lock:protocol.write(line+'\n');protocol.flush()
    def reader():
        try:
            while True:
                line=sys.stdin.readline(65537)
                if not line:break
                if len(line)>65536:raise ValueError('Control command too large')
                message=json.loads(line)
                try:commands.put(message,timeout=.2)
                except queue.Full:emit({'id':message.get('id'),'error':'Control queue is busy; retry the operation.'})
        except Exception as exc:failure(type(exc),exc,exc.__traceback__)
        finally:eof.set()
    threading.Thread(target=reader,daemon=True,name='Qt command reader').start()
    def require_binding(data):
        require_destination(data)
        if data.get('binding')!=[list(view.owner_key()),view.target.target_id]:
            raise ValueError('Editing destination changed; the original gesture was cancelled.')
    def require_destination(data):
        if data.get('destination_revision',owner.destination_revision)!=owner.destination_revision or data.get('preview_run',owner.preview_run)!=owner.preview_run:
            raise ValueError('Editing destination changed; the original gesture was cancelled.')
        if owner.process is not None and owner.process.poll() is None and owner.running_values.get('playback_scope') and owner.preview_state.get('destination_revision')!=owner.destination_revision:
            raise ValueError('Destination is changing; wait for its renderer acknowledgement.')
    def action(name,data):
        nonlocal closing
        editor=owner.color_editor
        if name in ('select','form','target','pin'):
            owner.release_preview_holds();view.keyboard.stop()
        if name=='select':owner.select(data['path'],data['scope']);colors()
        elif name=='load_leaf':
            if data.get('preview_run')!=owner.preview_run:raise ValueError('Load belongs to an obsolete preview run.')
            revision=data.get('revision')
            if type(revision) is not int or revision<=owner.destination_revision:return
            scope,form=leaf_destination(data['scope'],data['path'],owner.committed_scope,LIVE_FORMS)
            view.park_edits();view.keyboard.stop();owner.release_preview_holds()
            if owner.color_send_after is not None:root.after_cancel(owner.color_send_after);owner.color_send_after=None
            owner.select(data['path'],data['scope']);owner.destination_revision=revision
            running=owner.process is not None and owner.process.poll() is None
            if running and not compatible_scope(scope) and owner.preview_state.get('current_form')==form:
                # An already active isolated leaf does not need another resource
                # route, source rewind or history reset. Revision still cancels
                # older UI gestures in the control owner.
                owner.committed_scope=scope
            elif running and compatible_scope(scope) and owner.running_values.get('playback_scope'):
                owner.committed_scope=scope
                owner.preview_command('load',scope=scope,form=form,revision=revision)
                owner.running_values['playback_scope']=scope
                owner.running_values['selection']=list(data['path'])
                owner.running_values['selection_scope']=data['scope']
                owner.running_values['state']=next(key for key,value in __import__('world_catalog').LIVE_STATES.items() if value==form)
            else:
                if running:owner.stop()
                values=owner.values()
                if compatible_scope(scope):values.update(playback_scope=scope,playback_form=form)
                owner.launch(values,owner.run_folder())
                owner.committed_scope=scope
            colors()
        elif name=='attach':
            if data.get('preview_run')!=owner.preview_run:raise ValueError('Attachment belongs to an obsolete preview run.')
            owner.preview_command('attach')
        elif name=='start':
            if owner.process is not None:raise ValueError('A preview is already owned; Stop it before Start.')
            if 'path' in data:owner.select(data['path'],data['scope']);colors()
            # Explicit diagnostic seed uses the existing command-line feature;
            # normal launch is unchanged and renderer quality is never retuned.
            seed=os.environ.get('ZERAWAVE_CONTROL_TEST_SEED')
            if seed is None:owner.launch(owner.values(),owner.run_folder())
            else:
                from unittest.mock import patch
                from studio import command
                seed=int(seed)
                with patch('studio.command',lambda values,output:command(values,output)+['--seed',str(seed)]):
                    owner.launch(owner.values(),owner.run_folder())
        elif name=='audio_transport':
            if owner.process is not None and owner.process.poll() is None and owner.committed_scope and not compatible_scope(owner.committed_scope) and data['op'] in ('source','device','open','play','raw_waveform','seek','speed'):
                raise ValueError('Stop the separate legacy Experimental preview before switching audio. Main playback shares the Studio audio owner.')
            owner.audio_owner.submit(data['op'],**data.get('values',{}))
        elif name=='diagnostics':owner.diagnostics.set(bool(data['value']))
        elif name=='resolution':
            from visualizer_resolution import validate
            if data.get('preview_run')!=owner.preview_run:raise ValueError('Resolution belongs to an obsolete preview run.')
            policy=validate(data.get('policy'),(owner.preview_state.get('resolution') or {}).get('limit',16384))
            if owner.process is not None and owner.process.poll() is None:
                owner.resolution_pending=owner.preview_command('resolution',policy=policy)
            else:owner.resolution_policy=policy;owner.resolution_pending=None
        elif name=='stop':owner.stop()
        elif name=='pause':owner.pause_preview()
        elif name=='bonk':owner.preview_command('bonk',mode=owner.bonk_mode.get().lower())
        elif name=='hold':
            if data.get('owner','studio.mouse') not in ('studio.mouse','studio.Shift_L','studio.Shift_R'):raise ValueError('Invalid Hold owner')
            owner.hold_preview(data.get('owner','studio.mouse'),bool(data['active']))
        elif name=='release':owner.release_preview_holds();view.keyboard.stop()
        elif name=='var':owner.vars[data['key']].set(data['value'])
        elif name=='bonk_mode':owner.bonk_mode.set(data['value']);owner.preview_command('mode',mode=data['value'].lower())
        elif name=='color_target':
            choices=targets_for(owner.color_scene())
            if data['label'] not in {t.label for t in choices}:raise ValueError('Color target is no longer available.')
            editor.target_choice.set(data['label']);colors()
        elif name=='color_refresh':colors()
        elif name=='color_commit':
            require_destination(data)
            if editor.target().id!=data['target']:raise ValueError('Color destination changed; edit cancelled.')
            editor.commit(data['role'],data['fields'])
        elif name=='color_reset':
            require_destination(data)
            if editor.target().id!=data['target']:raise ValueError('Color destination changed; reset cancelled.')
            editor.reset_target();colors()
        elif name=='pin':view.pin.set(bool(data['value']));view.pin_changed()
        elif name=='form':view.pin.set(True);view.select_form(form=data['form'])
        elif name=='target':view.target_var.set(data['label']);view.select_target()
        elif name=='override':
            require_binding(data);before=before_edit();view.enabled.set(bool(data['value']));view.toggle();track_draft(before)
        elif name=='tune':
            require_binding(data);key=data['key']
            if key not in view.bounds:raise ValueError('Parameter is not available at this destination.')
            low,high=view.bounds[key];value=float(data['value'])
            if not low<=value<=high:raise ValueError('Parameter is outside its declared range.')
            before=before_edit();view.vars[key].set(value);view.changed(key);track_draft(before)
        elif name=='range':
            require_binding(data);before=before_edit();view.range_vars[data['key']].set(bool(data['value']));view.changed(data['key']+'_range_enabled');track_draft(before)
        elif name=='reset_audio':require_binding(data);before=before_edit();view.reset();track_draft(before)
        elif name=='restore_draft':
            require_binding(data)
            matches=[d for d in drafts.values() if d['form']==view.form and d['target']==view.target.target_id]
            if not matches:raise ValueError('No saved tuning draft for this destination.')
            before=before_edit();view.display_settings(deepcopy(matches[-1]['settings']));view.changed();track_draft(before)
        elif name=='authored':
            require_binding(data)
            if data.get('revision')!=view.revision:raise ValueError('Save Authored revision changed; wait for the current ACK.')
            # A diagnostic may redirect this single real callback; production
            # never receives this environment flag and retains its real path.
            test_folder=os.environ.get('ZERAWAVE_CONTROL_TEST_AUTHORED')
            original=view.store.authored_path
            if test_folder:
                import hashlib
                folder=Path(test_folder).resolve();folder.mkdir(parents=True,exist_ok=True)
                redirected=folder/(hashlib.sha256(view.target.target_id.encode()).hexdigest()[:16]+'.json')
                if original.exists() and not redirected.exists():redirected.write_bytes(original.read_bytes())
                view.store.authored_path=redirected
            try:
                if not view.save_authored():raise ValueError(view.profile_status.get())
            finally:view.store.authored_path=original
            if draft_key() in drafts:
                drafts[draft_key()].update(baseline=deepcopy(drafts[draft_key()]['settings']),dirty=False)
        elif name in ('load','save'):
            # Dialog selection stays in Qt; storage still runs through Studio.
            from unittest.mock import patch
            path=str(Path(data['path']).resolve())
            if name=='load':
                loaded=json.loads(Path(path).read_text(encoding='utf8'))
                if len(loaded.get('qt_tuning_drafts',[]))>256:raise ValueError('Session has more than 256 tuning draft destinations.')
                with patch('studio.filedialog.askopenfilename',return_value=path):owner.load()
                drafts.clear()
                for draft in loaded.get('qt_tuning_drafts',[]):
                    draft=deepcopy(draft);draft['dirty']=False;draft['baseline']=deepcopy(draft['settings'])
                    drafts[json.dumps(draft['binding'])]=draft
                colors()
            else:
                with patch('studio.filedialog.asksaveasfilename',return_value=path):owner.save(save_as=True)
                saved=json.loads(Path(path).read_text(encoding='utf8'));saved['qt_tuning_drafts']=list(drafts.values())
                destination=Path(path);temporary=destination.with_suffix(destination.suffix+'.qt-tmp')
                temporary.write_text(json.dumps(saved,indent=2),encoding='utf8');os.replace(temporary,destination)
                for draft in drafts.values():draft.update(baseline=deepcopy(draft['settings']),dirty=False)
        elif name=='close':closing=True
        else:raise ValueError('Unsupported control command: '+str(name))
    # Recoverable errors must not open modal dialogs in a hidden process.
    def report_error(title,message,**kwargs):raise ValueError(str(title)+': '+str(message))
    from tkinter import messagebox
    messagebox.showerror=report_error
    def tick():
        nonlocal sequence,closing
        if eof.is_set():closing=True
        for _ in range(8):
            try:message=commands.get_nowait()
            except queue.Empty:break
            try:
                action(message['action'],message.get('data',{}));sequence+=1
                emit({'id':message['id'],'snapshot':snapshot()})
            except Exception as exc:
                failure(type(exc),exc,exc.__traceback__);emit({'id':message.get('id'),'error':str(exc)})
        if closing:
            for cleanup in (owner.stop,owner.audio_owner.close,sampler.close,view.close,owner.color_editor.close):
                try:cleanup()
                except Exception as exc:failure(type(exc),exc,exc.__traceback__)
            root.destroy()
            return
        root.after(10,tick)
    def publish():
        if closing:return
        try:emit({'snapshot':snapshot()})
        except Exception as exc:failure(type(exc),exc,exc.__traceback__)
        root.after(200,publish)
    analyzer_sent=None
    def publish_analyzer():
        nonlocal analyzer_sent
        if closing:return
        try:
            data=owner.audio_owner.analyzer_snapshot();packet=data.get('band_analyzer') or {}
            identity=(data['generation'],data['playing'],data['status'],data['analyzer_enabled'],data['analyzer_error'],packet.get('sequence'))
            if identity!=analyzer_sent:
                emit({'audio_analyzer':data});analyzer_sent=identity
        except Exception as exc:failure(type(exc),exc,exc.__traceback__)
        # Lightweight projection only. Other docks/resources keep their cadence.
        root.after(33,publish_analyzer)
    emit({'snapshot':snapshot()});tick();publish();publish_analyzer();root.mainloop();log.close()

if __name__=='__main__':main()
