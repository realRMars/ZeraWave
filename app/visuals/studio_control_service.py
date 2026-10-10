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
import uuid
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
        from media_registry import MediaRegistry
        self.media_registry=MediaRegistry(os.environ.get('ZERAWAVE_MEDIA_LIBRARY',str(ROOT/'work/studio/media-library.json')))
        self.media_session=uuid.uuid4().hex;self.media_revision=0;self.media_publication_revision=0
        from composition import History
        from media_frames import MediaFrames
        from raster_resources import Resources,Outcomes
        self.close_state=dict(phase="open",error="");self.rasters=Resources();self.outcomes=Outcomes();self.publication_pins={};self.recovery_checkpoints=[]
        self.composition_history=History();self.media_frames=MediaFrames();self.frame_key=None;self.web_frames={};self.removed_media={}
        self.open_star_tuning();self.star_tuning_window.window.withdraw()
        self.open_color_inspector();self.color_editor.window.withdraw();self.color_editor.compact=True
    def canvas_dimensions(self):
        explicit=self.media_scene.get('canvas')
        if explicit:return list(explicit)
        session=getattr(self,'media_session',None)
        if getattr(self,'legacy_canvas_session',None)!=session or not getattr(self,'legacy_canvas',None):
            dimensions=getattr(self,'preview_state',{}).get('dimensions',{}).get('internal')
            policy=getattr(self,'resolution_policy',None)
            chosen=dimensions or (policy.get('size') if policy and policy.get('mode')=='fixed' else None) or (1280,720)
            # Legacy placement starts at its first effective output geometry, then
            # remains stable for this document as output resolution changes.
            from composition import validate_scene
            candidate=dict(self.media_scene,canvas=list(chosen));validate_scene(candidate)
            self.legacy_canvas=list(chosen);self.legacy_canvas_session=session
        return list(self.legacy_canvas)
    def values(self):
        values=super().values()
        if hasattr(self,'media_session'):values['media']['canvas']=self.canvas_dimensions()
        return values
    def renderer_host_environment(self):return self.host
    def stop(self):
        if hasattr(self,'media_frames'):self.media_frames.stop();self.media_frames.freeze(False)
        return super().stop()
    def media_spec(self,allow_resident=False):
        from media_registry import validate_scene,normalized
        scene=validate_scene(self.media_scene);scene['canvas']=self.canvas_dimensions();references=[]
        for ref in scene['assets']:
            asset=self.rasters.rows.get(ref['id']) or self.media_registry.assets.get(ref['id'])
            if asset is None:
                asset=dict(self.removed_media.get(ref['id'],ref),status='Missing',error='Library reference removed; Relink/Undo restores it.')
                asset.setdefault('metadata',{})
            if asset['kind']!=ref['kind'] or normalized(asset['path'])!=normalized(ref['path']):raise ValueError('Media reference changed; reselect or relink it explicitly.')
            from image_layers import asset_key
            resident=(self.preview_state.get('image_layers') or {}).get('resident',[])
            cached=allow_resident and list(asset_key(asset)) in resident
            # Missing references retain layer editing state. The stage retains
            # resident pixels, otherwise leaves that layer absent with a status.
            references.append(deepcopy(asset))
        return dict(scene,assets=references,runtime=dict(self.media_frames.snapshot(),**self.web_frames))
    def sync_media_refs(self):
        from media_registry import reference
        needed={layer['asset'] for layer in self.media_scene['layers'] if layer['asset']}
        old={a['id']:a for a in self.media_scene['assets']}
        records={**self.media_registry.assets,**self.rasters.rows}
        self.media_scene['assets']=[reference(records[key]) if key in records else old[key] for key in sorted(needed)]
    def send_media(self,ordered=False):
        if self.process is not None and self.process.poll() is None:
            if not self.committed_scope or not compatible_scope(self.committed_scope):return
            # Frame residency changes need fresh renderer ordering, but are not
            # composition edits. They must not invalidate a live editor gesture.
            spec=self.media_spec(allow_resident=True);self.media_publication_revision+=1
            self.preview_command('images',config=spec,revision=self.media_publication_revision,session=self.media_session,ordered=ordered)
            self.publication_pins[self.media_publication_revision]={a['id'] for a in spec['assets'] if 'runtime' in a}
    def launch(self,values,output,label=None):
        self.pause_intent=None
        self.resolution_pending=None
        startup_packet=None
        self.host.pop('ZERAWAVE_IMAGE_LAYERS_FILE',None)
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
            spec=self.media_spec()
            if spec['presentation']!='World only' and (spec['layers'] or spec['presentation']=='Layers only'):
                packet=json.dumps(dict(config=spec,revision=self.media_publication_revision,session=self.media_session))
                if len(packet.encode('utf8'))>8*1024*1024:raise ValueError('Image startup metadata exceeds 8 MiB; accepted scene retained')
                self.publication_pins[self.media_publication_revision]={a['id'] for a in spec['assets'] if 'runtime' in a}
                if len(packet)>12000:
                    # Windows environment values cannot carry large tile tables.
                    # The owned existing run folder pins a startup metadata file;
                    # pixels still travel in immutable mappings, never this JSON.
                    startup_packet=packet;self.host.pop('ZERAWAVE_IMAGE_LAYERS',None)
                    self.host['ZERAWAVE_IMAGE_LAYERS_FILE']=str((Path(output)/'image-layers-startup.json').resolve())
                else:self.host['ZERAWAVE_IMAGE_LAYERS']=packet
            else:self.host.pop('ZERAWAVE_IMAGE_LAYERS',None)
        else:
            self.host.pop('ZERAWAVE_AUDIO_HUB',None);self.host.pop('ZERAWAVE_IMAGE_LAYERS',None)
            if self.media_scene['presentation']=='Layers only' or self.media_scene['layers']:raise ValueError('Layer presentation requires a compatible Main preview; legacy Experimental is unsupported.')
        if startup_packet is not None:
            # Studio.launch creates the run directory exclusively. Write there
            # immediately before its existing process launch, without changing
            # renderer/audio ownership or adding another startup engine.
            self.image_startup_packet=startup_packet
        else:self.image_startup_packet=None
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
        self.media_frames.freeze(not active)
        self.pause_intent=(serial,not active)
    def select(self,selection,scope=None,show=True):return super().select(selection,scope,show=False)
    def poll_star_tuning(self):self.star_tuning_poll_after=None

def main():
    protocol=sys.stdout
    log_path=Path(os.environ['ZERAWAVE_CONTROL_LOG']);log_path.parent.mkdir(parents=True,exist_ok=True)
    log=log_path.open('w',encoding='utf8',buffering=1);sys.stdout=sys.stderr=log
    host=json.loads(os.environ['ZERAWAVE_CONTROL_HOST']);root=tk.Tk();root.withdraw()
    errors=deque(maxlen=16);commands=queue.Queue(maxsize=32);eof=threading.Event();closing=False
    def failure(kind,exc,tb,notify=True):
        text=''.join(traceback.format_exception(kind,exc,tb))
        if notify:errors.append(text)
        log.write(text)
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
        from raster_tiles import wire_resource
        current_assets={r['asset'] for r in owner.media_scene['layers']}
        library=owner.media_registry.snapshot(current_assets)
        # History/save/publication ownership stays in the owner. Qt receives
        # current readers only, with geometry implicit in the ABI's tile size.
        library['resources']=[wire_resource(r) for r in owner.rasters.rows.values() if not r.get('retired') and r['id'] in current_assets]+library['resources']
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
            'media_library':library,
            'media_control':dict(session=owner.media_session,revision=owner.media_revision,history=owner.composition_history.snapshot(),transactions=owner.outcomes.state(),raster=owner.rasters.state()),
            'media_frames':dict(owner.media_frames.snapshot(),**owner.web_frames),
            'tuning_drafts':list(drafts.values()),'tuning_dirty':any(d['dirty'] for d in drafts.values()),
            'close_state':dict(owner.close_state),'session_path':str(owner.session_path) if owner.session_path else None,
            'active_preview':owner.active_preview.get(),'status':owner.status.get(),'errors':list(errors)}
    out_lock=threading.Lock();sequence=0
    def emit(value):
        line=json.dumps(value,separators=(',',':'))
        if len(line)+1>2*1024*1024:raise RuntimeError('Control snapshot exceeded bounded protocol size')
        with out_lock:protocol.write(line+'\n');protocol.flush()
    def reader():
        try:
            while True:
                line=sys.stdin.readline(524289)
                if not line:break
                if len(line)>524288:raise ValueError('Control command too large')
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
    def perform_action(name,data):
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
        elif name=='media_import':
            paths=data.get('paths')
            if not isinstance(paths,list) or not 1<=len(paths)<=16 or any(not isinstance(p,str) or len(p)>1024 for p in paths):raise ValueError('Import one to sixteen local media paths.')
            if len(owner.media_registry.pending)+len(paths)>16:raise ValueError('Media validation queue is busy; wait or cancel imports.')
            collection=data.get('collection')
            if collection is not None and collection not in owner.media_registry.collections:raise ValueError('Collection no longer exists.')
            for path in paths:
                token=owner.media_registry.submit('import',path);owner.media_registry.pending[token]['collection']=collection
        elif name=='media_artwork':
            # Pixels travel as an immutable validated dependency, never JSON.
            from media_registry import inspect,reference,library_record,MAX_ASSETS,MAX_INTERNAL,MAX_REGISTRY_BYTES
            import threading
            ref=reference(data.get('asset'))
            if not ref.get('managed') or ref['kind']!='Images':raise ValueError('Expected a managed artwork dependency.')
            if sum(bool(a.get('internal'))==bool(ref.get('internal')) for a in owner.media_registry.assets.values()) >= (MAX_INTERNAL if ref.get('internal') else MAX_ASSETS):raise ValueError('Artwork resource/reference limit reached; previous content retained.')
            record=inspect(ref['path'],threading.Event());record.update(ref)
            if ref['id'] in owner.media_registry.assets:raise ValueError('Artwork identity already exists.')
            proposal=dict(version=2,assets=[library_record(a) for a in owner.media_registry.assets.values()]+[library_record(record)],collections=owner.media_registry.collections)
            if len(json.dumps(proposal,indent=2).encode('utf8'))>MAX_REGISTRY_BYTES:raise ValueError('Artwork metadata reached 8 MiB; previous content retained.')
            owner.media_registry.assets[ref['id']]=record;owner.media_registry.schedule_save()
        elif name=='media_recover':
            if data.get('asset') in owner.rasters.rows:raise ValueError('Accepted raster reference is immutable. Replace the layer source with a new import; retained drawing remains recoverable.')
            ref=next((a for a in owner.media_scene['assets'] if a['id']==data.get('asset')),None)
            if not ref:raise ValueError('This composition reference no longer exists.')
            owner.media_registry.restore_refs([ref]);owner.media_registry.submit('relink',data.get('path'),ref['id'])
        elif name=='media_action':
            from media_registry import normalized
            registry=owner.media_registry;op=data.get('op');asset=data.get('asset')
            if op in ('refresh','relink') and asset in owner.rasters.rows:raise ValueError('Source pixels are retained by raster history. Import a new version or replace the layer source; Save/reopen releases the old drawing history.')
            if op=='cancel':registry.cancel(data.get('token'))
            elif op=='collection':
                selected=data.get('assets') or [asset]
                if data.get('command') in ('add','remove'):
                    if not isinstance(selected,list) or len(selected)>128 or any(a not in registry.assets for a in selected):raise ValueError('Selected references no longer exist.')
                    for identity in dict.fromkeys(selected):registry.collection(data.get('command'),data.get('collection'),asset=identity)
                else:registry.collection(data.get('command'),data.get('collection'),data.get('name'),asset)
            else:
                batch=list(dict.fromkeys(data.get('assets') or [asset])) if op=='remove' else [asset]
                if not batch or len(batch)>128 or any(a not in registry.assets for a in batch):raise ValueError('Selected media references no longer exist.')
                if asset is None:asset=batch[0]
                if asset not in registry.assets:raise ValueError('Media asset no longer exists.')
                if op=='rename':registry.rename(asset,data.get('name'));owner.sync_media_refs()
                elif op=='refresh':registry.submit('validate',registry.assets[asset]['path'],asset)
                elif op=='relink':registry.submit('relink',data.get('path'),asset)
                elif op=='remove':
                    records=[dict(record=deepcopy(registry.assets[a]),members=[key for key,c in registry.collections.items() if a in c['assets']]) for a in batch]
                    before=deepcopy(owner.media_scene);choice=data.get('choice','recover')
                    if choice not in ('recover','layers'):raise ValueError('Choose recovery or removal of affected layers.')
                    candidate=deepcopy(before)
                    if choice=='layers':
                        from composition import ancestors,renumber
                        roots={r['id'] for r in candidate['layers'] if r['asset'] in batch}
                        remove=roots|{r['id'] for r in candidate['layers'] if any(a['id'] in roots for a in ancestors(candidate,r['id']))}
                        candidate['layers']=[r for r in candidate['layers'] if r['id'] not in remove];renumber(candidate)
                        used={r['asset'] for r in candidate['layers']};candidate['assets']=[a for a in candidate['assets'] if a['id'] in used]
                    proposal={k:v for k,v in registry.assets.items() if k not in batch}
                    owner.media_frames.sync(candidate,proposal,apply=False)
                    with owner.media_frames.condition:
                        saved=(deepcopy(registry.assets),deepcopy(registry.collections),registry.revision,dict(owner.removed_media),owner.composition_history.checkpoint(),owner.media_revision,dict(owner.media_frames.layers),dict(owner.media_frames.results))
                        try:
                            for item in records:
                                record=item['record'];registry.remove(record['id'],cancel_pending=False);owner.removed_media[record['id']]=record
                            while len(owner.removed_media)>128:owner.removed_media.pop(next(iter(owner.removed_media)))
                            owner.media_scene=candidate;owner.media_frames.sync(candidate,proposal)
                            selected=data.get('selection');after_selected=selected if any(r['id']==selected for r in candidate['layers']) else None
                            owner.composition_history.record(dict(before,restore_batch=records),dict(candidate,remove_batch=batch),'Remove references (recoverable)',selected,after_selected)
                            owner.composition_history.selection=after_selected;owner.media_revision+=1;owner.send_media()
                            for token,job in list(registry.pending.items()):
                                if job.get('asset') in batch:registry.cancel(token)
                        except Exception:
                            registry.assets,registry.collections,registry.revision,owner.removed_media,owner.composition_history,owner.media_revision,owner.media_frames.layers,owner.media_frames.results=saved
                            owner.media_scene=before;registry.schedule_save();raise
                elif op=='audio':
                    record=registry.assets[asset]
                    if record['kind']!='Audio' or record['status']!='Ready':raise ValueError('Select an available validated audio asset.')
                    if owner.process is not None and owner.process.poll() is None and owner.committed_scope and not compatible_scope(owner.committed_scope):raise ValueError('Stop the legacy Experimental preview before using library audio.')
                    audio=owner.audio_owner.snapshot()
                    if audio['mode']!='Audio File' or normalized(audio['path'])!=normalized(record['path']):owner.audio_owner.submit('open',path=record['path'])
                else:raise ValueError('Unsupported media action.')
        elif name=='media_transport':
            if data.get('media_session')!=owner.media_session:raise ValueError('Animation command belongs to an obsolete session.')
            owner.media_frames.command(data.get('layer'),data.get('op'),data.get('value'))
        elif name=='web_frame':
            if data.get('media_session')!=owner.media_session:raise ValueError('Web pixels belong to an obsolete session.')
            row=next((r for r in owner.media_scene['layers'] if r['id']==data.get('layer') and r['type']=='Web'),None)
            if row is None:return # Late asynchronous browser status after deletion.
            state=data.get('state');frame=state.get('frame') if isinstance(state,dict) else None
            if frame:
                if not isinstance(frame.get('name'),str) or not frame['name'].startswith('zerawave_web_') or len(frame['name'])>64 or type(frame.get('generation')) is not int or type(frame.get('capacity')) is not int or not 1<=frame['capacity']<=8*1024*1024:raise ValueError('Invalid bounded web frame descriptor.')
            old=owner.web_frames.get(row['id'],{});old_descriptor=old.get('frame')
            if frame is None and row['web']['offline']=='Retain last' and old_descriptor:state=dict(state,frame=old_descriptor)
            owner.web_frames[row['id']]=deepcopy(state)
            if (old_descriptor or {}).get('name')!=(state.get('frame') or {}).get('name'):
                owner.send_media()
        elif name=='operation_status':pass
        elif name=='artwork_output':
            if data.get('media_session')!=owner.media_session:raise ValueError('Artwork output belongs to an obsolete session.')
            from artwork_export import validate_outputs,output_key
            value=validate_outputs([data['association']])[0];key=output_key(value['scope'],value['targets'])
            if any(i not in {r['id'] for r in owner.media_scene['layers']} for i in value['targets']):raise ValueError('Saved artwork target no longer exists.')
            entries=[v for v in getattr(owner,'artwork_outputs',[]) if output_key(v['scope'],v['targets'])!=key]
            owner.artwork_outputs=validate_outputs(entries+[value])
        elif name=='raster_retry':
            owner.rasters.retry()
        elif name=='save_retry':owner.rasters.retry_save(data['save_id'],data.get('path'))
        elif name=='composition_history':
            if data.get('media_session')!=owner.media_session:raise ValueError('History belongs to an obsolete session.')
            if getattr(owner,'composition_preview',None) is not None:raise ValueError('Finish or cancel the active gesture before Undo/Redo.')
            scope=data.get('scope','layers');target=data.get('target') if scope=='drawing' else None
            if scope not in ('layers','drawing','editor'):raise ValueError('Unknown history scope.')
            if scope=='editor':
                item=owner.composition_history.item(data.get('redo',False),'editor')
                if item and item['scope']=='drawing':
                    from composition import lookup,effective
                    row=lookup(owner.media_scene).get(item['target'])
                    if row and effective(owner.media_scene,row,'locked'):raise ValueError('Unlock the drawing target before editor recovery.')
            if scope=='drawing':
                from composition import lookup,effective
                row=lookup(owner.media_scene).get(target)
                if row is None:return
                if effective(owner.media_scene,row,'locked'):raise ValueError('Unlock this drawing target before recovery.')
            scene=owner.composition_history.peek(data.get('redo',False),owner.media_scene,scope,target)
            if scene is None:return
            from composition import validate_scene
            candidate=validate_scene(scene);assets={**owner.media_registry.assets,**owner.rasters.rows}
            restores=scene.get('restore_batch',[]);removes=scene.get('remove_batch',[])
            for item in restores:assets[item['record']['id']]=item['record']
            for identity in removes:assets.pop(identity,None)
            from media_registry import MAX_ASSETS
            if sum(not a.get('internal') for a in assets.values())>MAX_ASSETS:raise ValueError('Library is full; remove an unused reference before Undo.')
            if not restores and not removes:owner.media_registry.restore_refs([a for a in scene['assets'] if a['id'] not in owner.rasters.rows],apply=False)
            owner.media_frames.sync(candidate,assets,apply=False)
            with owner.media_frames.condition:
                registry=owner.media_registry;saved=(deepcopy(registry.assets),deepcopy(registry.collections),registry.revision,owner.media_scene,owner.composition_history.checkpoint(),owner.media_revision,dict(owner.media_frames.layers),dict(owner.media_frames.results))
                try:
                    owner.media_frames.sync(candidate,assets)
                    if restores:
                        for item in restores:
                            record=item['record'];registry.assets[record['id']]=record
                            for key in item['members']:
                                if key in registry.collections and record['id'] not in registry.collections[key]['assets']:registry.collections[key]['assets'].append(record['id'])
                        registry.schedule_save()
                    elif removes:
                        for identity in removes:registry.remove(identity,cancel_pending=False)
                    else:registry.restore_refs([a for a in scene['assets'] if a['id'] not in owner.rasters.rows],cancel_pending=False)
                    owner.composition_history.step(data.get('redo',False),owner.media_scene,scope,target);owner.media_scene=candidate
                    owner.media_revision+=1;owner.send_media(ordered=True)
                    for token,job in list(registry.pending.items()):
                        if job.get('asset') not in registry.assets and job.get('asset') is not None:registry.cancel(token)
                except Exception:
                    registry.assets,registry.collections,registry.revision,owner.media_scene,owner.composition_history,owner.media_revision,owner.media_frames.layers,owner.media_frames.results=saved
                    registry.schedule_save();raise
        elif name=='composition_cancel':
            if data.get('media_session')!=owner.media_session:raise ValueError('Preview belongs to an obsolete session.')
            pending=getattr(owner,'composition_preview',None)
            if pending:
                owner.media_scene=pending;owner.composition_preview=None;owner.media_frames.sync(pending,{**owner.media_registry.assets,**owner.rasters.rows});owner.media_revision+=1;owner.send_media()
        elif name in ('image_layers','composition','composition_preview'):
            require_destination(data)
            if data.get('media_session')!=owner.media_session or data.get('media_revision')!=owner.media_revision:raise ValueError(f"Image edit belongs to an obsolete session/revision ({data.get('media_revision')} to {owner.media_revision}).")
            from media_registry import validate_scene,reference
            layers=data.get('layers');ids={row.get('asset') for row in layers if isinstance(row,dict)} if isinstance(layers,list) else set()
            refs=[]
            for identity in ids-{None}:
                old={a['id']:a for a in owner.media_scene['assets']}
                if identity not in owner.rasters.rows and identity not in owner.media_registry.assets and identity not in old:raise ValueError('Media reference no longer exists.')
                refs.append(reference(owner.rasters.rows.get(identity) or owner.media_registry.assets.get(identity,old.get(identity))))
            scene=validate_scene(dict(version=data.get('version',2),presentation=data.get('presentation'),layers=layers,assets=refs,canvas=data.get('canvas',owner.media_scene.get('canvas')),editor=data.get('editor',owner.media_scene.get('editor',{}))))
            previous=owner.media_scene;owner.media_scene=scene
            try:
                owner.media_spec(allow_resident=owner.process is not None and owner.process.poll() is None)
                if owner.process is not None and owner.process.poll() is None and (not owner.committed_scope or not compatible_scope(owner.committed_scope)):raise ValueError('Image layers require a compatible Main preview; legacy Experimental is unsupported.')
                owner.media_frames.sync(scene,{**owner.media_registry.assets,**owner.rasters.rows},apply=False)
            finally:owner.media_scene=previous
            with owner.media_frames.condition:
                history_selection=owner.composition_history.selection
                saved=(owner.media_scene,owner.composition_history if name=='composition_preview' else owner.composition_history.checkpoint(),getattr(owner,'composition_preview',None),owner.web_frames,owner.media_revision,dict(owner.media_frames.layers),dict(owner.media_frames.results))
                try:
                    owner.media_scene=scene;owner.media_frames.sync(scene,{**owner.media_registry.assets,**owner.rasters.rows})
                    if name=='composition_preview':
                        if getattr(owner,'composition_preview',None) is None:owner.composition_preview=deepcopy(previous)
                    else:
                        previous=getattr(owner,'composition_preview',None) or previous;owner.composition_preview=None
                        history=owner.composition_history
                        history.resource_cost=getattr(owner.rasters,'history_bytes',None)
                        history.resource_sizes.update({a['id']:a.get('metadata',{}).get('width',0)*a.get('metadata',{}).get('height',0)*4 for a in list(owner.media_registry.assets.values())+list(owner.rasters.rows.values()) if a.get('managed')})
                        scope=data.get('history_scope','layers');target=data.get('history_target') if scope=='drawing' else None
                        if scope=='drawing':
                            from composition import lookup
                            prior_rows,new_rows=lookup(previous),lookup(scene)
                            if prior_rows.keys()!=new_rows.keys() or any(prior_rows[k]!=new_rows[k] for k in prior_rows if k!=target) or previous.get('canvas')!=scene.get('canvas') or previous['presentation']!=scene['presentation']:raise ValueError('Drawing recovery must edit only its own existing layer.')
                        history.record(previous,scene,data.get('label','Edit composition'),data.get('before_selection'),data.get('selection'),scope,target)
                    owner.web_frames={key:value for key,value in owner.web_frames.items() if any(r['id']==key and r['type']=='Web' for r in scene['layers'])}
                    owner.composition_history.selection=data.get('selection');owner.media_revision+=1;owner.send_media(ordered=name!='composition_preview')
                except Exception:
                    owner.media_scene,owner.composition_history,owner.composition_preview,owner.web_frames,owner.media_revision,owner.media_frames.layers,owner.media_frames.results=saved
                    owner.composition_history.selection=history_selection
                    owner.media_frames.condition.notify_all();raise
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
            from unittest.mock import patch
            # Dialog selection stays in Qt; storage still runs through Studio.
            path=str(Path(data['path']).resolve())
            if name=='load':
                if any(a['id'] in owner.rasters.rows for a in owner.media_scene['assets']):
                    key=uuid.uuid4().hex
                    recovery=owner.rasters.folder.parent/'recovery'/(owner.media_session+'-'+str(owner.media_revision)+'.json')
                    owner.rasters.save(key,deepcopy(owner.values()),list(drafts.values()),recovery,owner.media_session,owner.media_revision)
                    owner.recovery_checkpoints.append(key)
                    owner.recovery_checkpoints=owner.recovery_checkpoints[-16:]
                owner.composition_preview=None
                loaded=json.loads(Path(path).read_text(encoding='utf8'))
                from studio import validate_session
                media=validate_session(loaded)['media']
                if len(loaded.get('qt_tuning_drafts',[]))>256:raise ValueError('Session has more than 256 tuning draft destinations.')
                owner.media_frames.sync(media,owner.media_registry.assets,apply=False);owner.media_registry.restore_refs(media['assets'])
                with patch('studio.filedialog.askopenfilename',return_value=path):owner.load()
                retired=owner.rasters.retire()
                for revision,pins in owner.publication_pins.items():owner.publication_pins[revision]={retired.get(k,k) for k in pins}
                for out in owner.outcomes.rows.values():out['resources']=[retired.get(k,k) for k in out['resources']]
                owner.sync_media_refs() # only previously explicit relinks may replace saved paths
                owner.media_session=uuid.uuid4().hex;owner.media_revision+=1;owner.rasters.folder=Path(path).with_suffix('.rasters')/owner.media_session
                from composition import History
                owner.composition_history=History();owner.media_frames.reset();owner.media_frames.sync(owner.media_scene,{**owner.media_registry.assets,**owner.rasters.rows})
                owner.web_frames={}
                if owner.color_link:
                    owner.media_publication_revision+=1
                    owner.preview_command('images_cancel',session=owner.media_session,revision=owner.media_publication_revision)
                drafts.clear()
                for draft in loaded.get('qt_tuning_drafts',[]):
                    draft=deepcopy(draft);draft['dirty']=False;draft['baseline']=deepcopy(draft['settings'])
                    drafts[json.dumps(draft['binding'])]=draft
                colors()
            else:
                key=data.get('save_id') or uuid.uuid4().hex
                values=deepcopy(owner.values())
                owner.rasters.save(key,values,list(drafts.values()),path,owner.media_session,owner.media_revision,recover_all=True)
        elif name=='cancel_save':owner.rasters.cancel_save(data['save_id'])
        elif name=='close':
            pending=any(not job.done() for job in owner.rasters.jobs.values())
            failed=bool(owner.rasters.failures)
            discard=data.get('mode')=='discard'
            if not discard and (failed or owner.rasters.save_pins or pending and not data.get('mode')):raise ValueError('Accepted raster work is not secured. Retry/Save As, Cancel, or explicitly Discard before closing.')
            owner.close_state=dict(phase='draining',discard=discard,started=time.perf_counter(),error='')
        elif name=='close_cancel':
            if owner.close_state['phase']=='draining':owner.close_state=dict(phase='open',error='')
        else:raise ValueError('Unsupported control command: '+str(name))
    def action(name,data):
        if owner.close_state['phase']=='draining' and name not in ('close_cancel','close','cancel_save'):raise ValueError('Closing; cancel close before editing.')
        ordered='operation_id' in data
        if ordered and not owner.outcomes.begin(name,data):return
        admitted={}
        try:
            if data.get('raster_assets') or data.get('raster_sources'):
                if owner.color_link and sum(bool(p.get('ordered')) for p in owner.color_link.pending_controls.values())>=60:raise ValueError('Renderer publication queue full; raster not accepted. Retry after output catches up.')
                if name!='composition':raise ValueError('Raster resources require a composition transaction.')
                if data.get('media_session')!=owner.media_session or data.get('media_revision')!=owner.media_revision:raise ValueError('Obsolete raster session/revision.')
                from composition import lookup,effective
                target=data.get('raster_target')
                if target is not None:
                    current=lookup(owner.media_scene).get(target['id'])
                    if current!=target:raise ValueError('Raster target changed; edit rejected.')
                    # An ordinary raster's lock protects its own artwork, not a
                    # newly inserted child. The exception is structural and exact:
                    # every pre-existing row must remain unchanged and just one
                    # direct child may be inserted using this admitted raster.
                    old_rows=lookup(owner.media_scene);new_rows={r['id']:r for r in data.get('layers',[])}
                    additions=[r for i,r in new_rows.items() if i not in old_rows]
                    child_insert=data.get('history_scope','layers')=='layers' and len(additions)==1 and additions[0]['parent']==current['id'] and additions[0]['asset'] in {a['id'] for a in data.get('raster_assets',[])} and all(new_rows.get(i)==r for i,r in old_rows.items())
                    from composition import ancestors
                    group_protected=any(r['type']=='Group' and r['locked'] for r in [current]+ancestors(owner.media_scene,current['id']))
                    if group_protected or effective(owner.media_scene,current,'locked') and not child_insert or not effective(owner.media_scene,current,'enabled'):raise ValueError('Raster target protected; edit rejected.')
                    if data.get('history_scope')=='drawing':
                        if current['type'] not in ('Image','Artwork','Paint') or not current['source_visible']:raise ValueError('Own raster target is not editable.')
                        old=owner.rasters.rows.get(current['asset']) or owner.media_registry.assets.get(current['asset'],{})
                        dimensions=(old.get('metadata',{}).get('width'),old.get('metadata',{}).get('height'))
                        if any((a['runtime']['width'],a['runtime']['height'])!=dimensions for a in data['raster_assets']):raise ValueError('Drawing cannot replace native working dimensions.')
                sources=[]
                for source in data.get('raster_sources',[]):
                    original=owner.media_registry.assets.get(source['id'])
                    if not original or source.get('path')!=original['path'] or source.get('metadata')!=original.get('metadata'):raise ValueError('Source snapshot no longer matches validated original.')
                    if source['id'] not in owner.rasters.rows:sources.append(dict(source,source_snapshot=True))
                admitted=owner.rasters.admit(data.get('raster_assets',[])+sources)
            perform_action(name,data)
            if ordered:owner.outcomes.finish(data,status='applied',revision=owner.media_revision,session=owner.media_session,publication=owner.media_publication_revision,accepted=time.perf_counter(),resources=[a['id'] for a in owner.media_scene['assets'] if a['id'] in owner.rasters.rows],output='queued' if owner.process is not None else 'inactive')
            # No fallible encoder or registry work precedes acceptance/publication.
            for key in admitted:
                if owner.rasters.rows[key].get('source_snapshot'):continue
                try:owner.rasters.persist(key)
                except Exception as exc:
                    owner.rasters.rows[key].update(durability='failed',error=str(exc)[:240]);owner.rasters.failures[key]=str(exc)[:240]
        except Exception as exc:
            if admitted:owner.rasters.reject(admitted)
            if ordered:owner.outcomes.finish(data,status='rejected',error=str(exc),revision=owner.media_revision)
            raise
    # Recoverable errors must not open modal dialogs in a hidden process.
    def report_error(title,message,**kwargs):raise ValueError(str(title)+': '+str(message))
    from tkinter import messagebox
    messagebox.showerror=report_error
    def tick():
        nonlocal sequence,closing
        if eof.is_set():closing=True
        owner.rasters.poll()
        for out in owner.rasters.saves.values():
            if out['status']=='durable' and not out.get('announced'):
                out['announced']=True
                if out['id'] not in owner.recovery_checkpoints:
                    if out['session']==owner.media_session:
                        owner.session_path=Path(out['path']);owner.rasters.resume_store(out['id'])
                    owner.status.set('Saved revision '+str(out['revision'])+('; newer edits remain unsaved.' if out['revision']!=owner.media_revision or out['session']!=owner.media_session else '.'))
                    if out['session']==owner.media_session:
                        pinned={json.dumps(d['binding']):d for d in out['drafts']}
                        for key,draft in drafts.items():
                            if key in pinned and draft['settings']==pinned[key]['settings']:draft.update(baseline=deepcopy(draft['settings']),dirty=False)
                out.pop('drafts',None)
        output=owner.preview_state.get('image_layers') or {}
        acknowledged=output.get('applied_revision',-1)
        for out in owner.outcomes.rows.values():
            if out['status']!='applied':continue
            if out.get('session')==owner.media_session and out.get('output') in ('queued','failed'):
                publication=out.get('publication',-1)
                if publication==acknowledged and not output.get('error'):out.update(output='published',published=time.perf_counter())
                elif publication<acknowledged:out.update(output='superseded',superseded=time.perf_counter())
                elif output.get('revision',-1)>=publication and output.get('error'):out.update(output='failed',output_error=output['error'])
            states=[owner.rasters.rows[k]['durability'] for k in out['resources'] if k in owner.rasters.rows]
            if states:out['durability']='failed' if 'failed' in states else 'pending' if 'pending' in states else 'durable'
        for revision in list(owner.publication_pins):
            if revision<=acknowledged or owner.process is None:owner.publication_pins.pop(revision,None)
        refs={a['id'] for a in owner.media_scene['assets']}
        refs.update(r['asset'] for r in owner.composition_history.rows.values())
        for item in owner.composition_history.undo+owner.composition_history.redo:
            refs.update(a['id'] for scene in (item['before'],item['after']) for a in scene['assets'])
        for pins in owner.publication_pins.values():refs.update(pins)
        metadata_refs=set(refs)|set(owner.removed_media)
        for pins in owner.rasters.save_pins.values():metadata_refs.update(pins)
        metadata_refs.update(k for k,j in owner.rasters.jobs.items() if not j.done())
        owner.media_registry.prune_internal(metadata_refs)
        if not owner.media_registry.loading:owner.rasters.retain(refs,protected_paths=[a['path'] for a in owner.media_registry.assets.values()]+[a['path'] for a in owner.removed_media.values()])
        prior_refs=deepcopy(owner.media_scene['assets'])
        if owner.media_registry.poll():
            # Relinking retains asset/layer identities and transforms. Registry
            # validation alone never loads a new image or starts audio/visuals.
            owner.sync_media_refs()
            # Reference ordering is not an edit. Validation/ref recovery can
            # enumerate the same IDs in another order during an import poll.
            if {a['id']:a for a in prior_refs}!={a['id']:a for a in owner.media_scene['assets']}:
                owner.media_revision+=1
                try:owner.send_media()
                except ValueError as exc:owner.media_registry.error=str(exc)
        if owner.process is not None and owner.process.poll() is None:
            serial=owner.preview_state.get('serial',-1);intent=owner.pause_intent
            owner.media_frames.freeze(intent[1] if intent and serial<intent[0] else owner.preview_state.get('paused',False))
        try:owner.media_frames.sync(owner.media_scene,{**owner.media_registry.assets,**owner.rasters.rows})
        except ValueError as exc:owner.media_registry.error=str(exc) # Retain last frames; keep control/audio ticks alive.
        frames=owner.media_frames.snapshot();frame_key=[(key,(value.get('frame') or {}).get('name'),(value.get('frame') or {}).get('generation')) for key,value in frames.items()]
        if frame_key!=owner.frame_key:
            owner.frame_key=frame_key;owner.send_media()
        for _ in range(8):
            try:message=commands.get_nowait()
            except queue.Empty:break
            try:
                action(message['action'],message.get('data',{}));sequence+=1
                drop=os.environ.get('ZERAWAVE_RASTER_TEST_DROP_ACK')
                if drop and Path(drop).exists() and 'operation_id' in message.get('data',{}):
                    Path(drop).unlink() # isolated fixture: exactly one lost ACK
                else:emit({'id':message['id'],'snapshot':snapshot()})
            except Exception as exc:
                op=message.get('data',{}).get('operation_id');outcome=owner.outcomes.rows.get(op,{})
                # Expected admission backpressure is already an explicit rejected
                # ledger outcome and Qt edit status. Preserve its trace, but do
                # not promote it to an unrelated runtime-error pane/focus change.
                failure(type(exc),exc,exc.__traceback__,notify=outcome.get('status')!='rejected')
                emit({'id':message.get('id'),'error':str(exc),'outcome_uncertain':outcome.get('status')=='applied'})
        if owner.close_state['phase']=='draining':
            state=owner.close_state
            if owner.rasters.prepare_close(state['discard']):
                owner.rasters.poll()
                if not state['discard'] and (owner.rasters.failures or owner.rasters.save_pins):owner.close_state=dict(phase='failed',error='Close did not secure accepted work. Retry/Save As or explicitly Discard.');emit({'snapshot':snapshot()})
                else:closing=True
            elif time.perf_counter()-state['started']>15:
                owner.close_state=dict(phase='failed',error='A write has not stopped within 15 seconds. Editor remains open; accepted work retained. Correct the destination, Retry/Save As or try close again.');emit({'snapshot':snapshot()})
        if closing:
            owner.close_state['phase']='releasing';emit({'snapshot':snapshot()})
            # EOF is an exceptional route, with cooperative cancellation. Normal
            # close arrives only after every PNG/save future has actually ended.
            if not owner.rasters.prepare_close(True):root.after(10,tick);return
            protected=[a['path'] for a in owner.media_registry.assets.values() if not a.get('internal')]
            for cleanup in (owner.stop,lambda:owner.rasters.close(discard=True,protected_paths=protected),owner.media_frames.close,owner.media_registry.close,owner.audio_owner.close,sampler.close,view.close,owner.color_editor.close):
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
