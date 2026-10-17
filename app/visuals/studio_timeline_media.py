"""Bounded source inspection for deliberate Library-to-project placement."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from fractions import Fraction
import json,threading,uuid,os
from video_project import rational,pair,clip_recipe
from PySide6.QtCore import Qt,QMimeData
from PySide6.QtWidgets import QTreeWidget

class ProjectMediaTree(QTreeWidget):
    def __init__(self):super().__init__();self.setDragDropMode(QTreeWidget.DragOnly);self.setSelectionMode(QTreeWidget.ExtendedSelection);self.setDefaultDropAction(Qt.CopyAction)
    def mimeTypes(self):return ['application/x-zerawave-project-media']
    def supportedDropActions(self):return Qt.CopyAction
    def mimeData(self,items):
        mime=QMimeData();mime.setData('application/x-zerawave-project-media',json.dumps(list(dict.fromkeys(i.data(0,Qt.UserRole) for i in items))).encode());return mime

def inspect_all(sources,cancel):
    from studio_video_workspace import inspect_source
    result=[]
    for source in sources:
        if cancel.is_set():raise InterruptedError('Placement cancelled')
        result.append(inspect_source(source,cancel))
    return result

class Placement:
    def __init__(self,panel,mime,track,frame):
        self.panel=panel;w=panel.workspace;self.binding=w.binding();self.document=deepcopy(w.document());self.target=track;self.frame=frame;self.mode=panel.canvas.mode;self.channels=panel.source_mode.currentText();self.cancel=threading.Event();self.finished=False;self.dispatched=False;self.library=False;self.range=None
        if mime.hasFormat('application/x-zerawave-project-media'):
            raw=bytes(mime.data('application/x-zerawave-project-media'));assets={a['id']:a for a in self.document['media']}
        elif mime.hasFormat('application/x-zerawave-assets'):
            raw=bytes(mime.data('application/x-zerawave-assets'));assets=w.shell.media_library.assets;self.library=True
        else:raise ValueError('Drag a supported source from the existing Media Library.')
        if len(raw)>524288:raise ValueError('Media drag exceeds the existing512KiB request limit.')
        ids=json.loads(raw)
        if not isinstance(ids,list) or not ids or len(ids)>1024 or any(not isinstance(i,str) or i not in assets for i in ids) or len(set(ids))!=len(ids):raise ValueError('Drag contains missing or repeated sources; no placement accepted.')
        self.sources=[deepcopy(assets[i]) for i in ids]
        if any(a['kind'] not in ('Video','Audio','Image','Images') for a in self.sources):raise ValueError('Timeline accepts existing video, audio and still images.')
        source=w.video_panels.source
        self.still_duration=Fraction(str(source.still_seconds.value()))
        if len(ids)==1 and source.asset and (source.asset['id']==ids[0] or os.path.normcase(source.asset['location']['path'])==os.path.normcase(self.sources[0].get('path') or self.sources[0]['location']['path'])):
            if getattr(source,'retained_range',None) is not None or getattr(w,'transport_future',None) or getattr(w,'transport_desired',None):raise ValueError('Source range/transport is still reconciling or rejected. Resolve it before a new placement; this drop was not admitted.')
            self.range=dict(sha256=source.asset['sha256'],fps=deepcopy(source.fps),interval=list(source.range),natural_end=source.range[1]==source.end)
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Timeline source inspection');self.future=self.pool.submit(inspect_all,self.sources,self.cancel);panel.canvas.notify('Preparing dropped source identity/range • no project edit accepted yet. Escape cancels; later tool/mode changes do not alter this drop.')
    def poll(self):
        if self.finished or not self.future.done():return
        if getattr(self.panel.workspace,'transport_future',None) or getattr(self.panel.workspace,'transport_desired',None):return
        self.finished=True
        try:
            assets=self.future.result();w=self.panel.workspace
            if self.cancel.is_set() or self.panel.closed:return
            current=w.binding()
            if any(self.binding.get(k)!=current.get(k) for k in ('expected_epoch','expected_revision','expected_project')):raise ValueError('Project changed while preparing the drop. Placement was not submitted; drop again deliberately.')
            # Source inspection/transport may advance the ordered command clock
            # without changing accepted document semantics. Dispatch once with
            # its current command boundary, retaining original IDs/range/options.
            self.binding['expected_command']=current.get('expected_command')
            if self.range and assets[0]['sha256']!=self.range['sha256']:raise ValueError('Source changed after its In/Out selection. No placement accepted; refresh and select the range again.')
            changes,rows=self.plan(assets)
            if len(changes)>128:raise ValueError('This placement exceeds the existing128-change atomic batch limit. Choose fewer new references; nothing was accepted.')
            self.dispatched=bool(self.panel.canvas.perform('Place Library media • '+self.mode,changes,self.binding,{r['row']['id']:r['row'] for r in rows}))
        except InterruptedError:
            if not self.panel.closed:self.panel.canvas.notify('Placement cancelled before acceptance. No automatic resubmission.')
        except Exception as exc:
            if not self.panel.closed:self.panel.canvas.notify('Placement not accepted: '+str(exc))
        finally:self.pool.shutdown(wait=False,cancel_futures=True)
    def plan(self,assets):
        d=self.document;tracks=deepcopy(sorted(d['tracks'],key=lambda t:t['order']));changes=[];rows=[];cursor=self.frame;target=next((t for t in tracks if t['id']==self.target),None)
        if target and target.get('locked',False):raise ValueError('The drop target is locked. Unlock it or choose another track.')
        def destination(kind,preferred=None):
            if preferred and preferred['kind']==kind:return preferred['id']
            candidates=[t for t in tracks if t['kind']==kind]
            ordinal=[t['id'] for t in tracks if t['kind']==preferred['kind']].index(preferred['id']) if preferred else 0
            if ordinal<len(candidates):return candidates[ordinal]['id']
            key=uuid.uuid4().hex;t=dict(id=key,name={'video':'Video','audio':'Audio','graphics':'Titles'}[kind]+' '+str(sum(t['kind']==kind for t in tracks)+1),kind=kind,order=len(tracks));tracks.append(t);changes.append(dict(op='track.add',**t));return key
        for index,a in enumerate(assets):
            existing=next((old for old in d['media'] if old['id']==a['id'] or old['sha256']==a['sha256'] and os.path.normcase(a['location']['path']) in {os.path.normcase(old['location']['path']),os.path.normcase(old.get('provenance',{}).get('import_path',''))}),None)
            if existing:
                if existing['sha256']!=a['sha256']:raise ValueError('Recorded project source changed. Relink it deliberately first.')
                if self.panel.workspace.state().get('media',{}).get(existing['id'],{}).get('status')!='Ready':raise ValueError('The existing project reference is unavailable. Relink it deliberately; dropping a Library source cannot silently replace it.')
                asset_id=existing['id']
            else:
                asset_id=uuid.uuid4().hex;provenance=dict(import_path=a['location']['path'])
                if self.library:provenance['library_id']=a['id']
                changes.append(dict(op='media.add',id=asset_id,name=a['name'],kind=a['kind'],location=deepcopy(a['location']),sha256=a['sha256'],metadata=deepcopy(a['metadata']),provenance=provenance))
            fps=rational(d['settings']['fps']);source_fps=rational(a['metadata'].get('rational_fps') or [30,1]);source_in=Fraction(0);available=rational(a['metadata']['duration_time']) if 'duration_time' in a['metadata'] else Fraction(str(a['metadata'].get('duration',5)))
            if self.range and index==0:
                source_in=Fraction(self.range['interval'][0])/rational(self.range['fps']);available=Fraction(self.range['interval'][1]-self.range['interval'][0])/rational(self.range['fps'])
            natural_audio=a['kind']=='Audio' and (self.range is None or self.range.get('natural_end',False))
            if natural_audio:
                from project_audio_timing import natural_frames
                length=natural_frames(a['metadata'],pair(fps),start=cursor,source_in=pair(source_in))
            else:length=max(1,int(available*fps)) if a['kind']!='Image' else max(1,int(getattr(self,'still_duration',Fraction(5))*fps))
            has_audio=a['kind']=='Audio' or bool(a['metadata'].get('has_audio'));video=a['kind']!='Audio' and self.channels!='Audio only';audio=has_audio and self.channels!='Video only'
            if self.channels=='Audio only' and not has_audio:raise ValueError(a['name']+' contains no audio stream. Choose video-only or another source.')
            if a['kind']=='Audio' and self.channels=='Video only':raise ValueError(a['name']+' is an audio source; choose audio placement.')
            link=uuid.uuid4().hex if video and audio else None
            if video:
                kind='graphics' if a['kind']=='Image' and target and target['kind']=='graphics' else 'video';track=destination(kind,target);rows.append(dict(category='clips',row=clip_recipe(uuid.uuid4().hex,asset=asset_id,track=track,name=a['name'],start=cursor,duration=length,source_in=pair(source_in),link_id=link)))
            if audio:
                track=destination('audio',target);rows.append(dict(category='clips',row=clip_recipe(uuid.uuid4().hex,asset=asset_id,track=track,name=a['name']+' audio' if video else a['name'],start=cursor,duration=length,source_in=pair(source_in),link_id=link,**({'pad_end':'silence'} if natural_audio else {}))))
            cursor+=length
        changes.append(dict(op='items.place',rows=rows,mode=self.mode));return changes,rows
    def exited(self):return self.finished and all(not t.is_alive() for t in self.pool._threads)
