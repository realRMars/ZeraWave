"""Media Library and two-layer controls; ownership stays in ControlOwner."""
from copy import deepcopy
from pathlib import Path
import json
from PySide6.QtCore import Qt,QTimer,QEvent,QMimeData
from PySide6.QtGui import QIcon,QPixmap,QImage
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QTreeWidget,QTreeWidgetItem,QPushButton,QFileDialog,QGroupBox,QFormLayout,QComboBox,QDoubleSpinBox,QSlider,QScrollArea,QMenu,QSizePolicy,QInputDialog,QMessageBox
from concurrent.futures import ThreadPoolExecutor
from studio_audio_widgets import TwoWaySwitch
from media_registry import KINDS,PRESENTATIONS,LAYER_IDS,defaults

FILTER='Media (*.png *.jpg *.jpeg *.gif *.wav *.mp3 *.mp4 *.mov *.mkv *.webm *.avi *.m4v *.gltf *.glb)'

class LibraryTree(QTreeWidget):
    def __init__(self,library):
        super().__init__();self.library=library;self.setSelectionMode(QTreeWidget.ExtendedSelection);self.setDragDropMode(QTreeWidget.DragDrop);self.setDefaultDropAction(Qt.CopyAction);self.setDropIndicatorShown(True)
    def mimeData(self,items):
        mime=QMimeData();mime.setData('application/x-zerawave-assets',json.dumps(self.library.selected_ids()).encode());return mime
    def mimeTypes(self):return ['application/x-zerawave-assets','text/uri-list']
    def supportedDropActions(self):return Qt.CopyAction
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat('application/x-zerawave-assets'):event.acceptProposedAction()
    def dragMoveEvent(self,event):self.dragEnterEvent(event)
    def dropEvent(self,event):
        item=self.itemAt(event.position().toPoint());collection=item.data(0,Qt.UserRole+1) if item else None
        if item and item.parent():collection=item.parent().data(0,Qt.UserRole+1)
        if event.mimeData().hasUrls():
            self.library.import_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()],collection);event.acceptProposedAction()
        elif collection and event.mimeData().hasFormat('application/x-zerawave-assets'):
            ids=json.loads(bytes(event.mimeData().data('application/x-zerawave-assets')));self.library.action('collection',command='add',collection=collection,assets=ids);event.acceptProposedAction()
    def keyPressEvent(self,event):
        if event.modifiers()&Qt.ControlModifier and event.key()==Qt.Key_A:
            self.clearSelection()
            for i in range(self.topLevelItemCount()):
                group=self.topLevelItem(i)
                if group.isExpanded():
                    for j in range(group.childCount()):group.child(j).setSelected(True)
            event.accept();return
        if event.modifiers()&Qt.ControlModifier and event.key() in (Qt.Key_Z,Qt.Key_Y):self.library.shell.image_editor.history(event.key()==Qt.Key_Y or bool(event.modifiers()&Qt.ShiftModifier));self.library.refresh();event.accept();return
        if event.key()==Qt.Key_Delete:self.library.remove_reference();event.accept();return
        super().keyPressEvent(event)

class MediaLibrary(QWidget):
    def __init__(self,shell):
        super().__init__();self.shell=shell;self.key=None;self.assets={};self.selected=None;self.collections={};self.collection_selected=None;self.thumbnails={};self.thumb_jobs={};self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='Library thumbnails');self.setAcceptDrops(True)
        layout=QVBoxLayout(self);layout.setContentsMargins(8,8,8,8)
        self.search=QLineEdit();self.search.setPlaceholderText('Search media names or paths…');layout.addWidget(self.search)
        row=QHBoxLayout();layout.addLayout(row)
        for label,action in (('Import…',self.import_files),('Cancel pending imports',lambda:self.action('cancel'))):
            button=QPushButton(label);button.clicked.connect(action);row.addWidget(button)
            if label=='Cancel pending imports':button.setToolTip('Cancel pending validation/imports. Completed references remain.')
        self.type_filter=QComboBox();self.type_filter.addItems(['All types']+list(KINDS));self.type_filter.currentTextChanged.connect(lambda:self.populate());layout.addWidget(self.type_filter)
        self.collection_button=QPushButton('+ Collection');self.collection_button.clicked.connect(self.new_collection);layout.addWidget(self.collection_button)
        self.tree=LibraryTree(self);self.tree.setHeaderLabels(['Media','Status']);self.tree.setRootIsDecorated(True);layout.addWidget(self.tree,1)
        self.tree.itemSelectionChanged.connect(self.selection);self.search.textChanged.connect(lambda:self.populate())
        self.tree.itemActivated.connect(lambda item,column:self.activate(item))
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu);self.tree.customContextMenuRequested.connect(self.menu)
        self.name=QLineEdit();self.name.setMaxLength(128);self.name.setPlaceholderText('Display name');self.name.editingFinished.connect(self.rename);layout.addWidget(self.name)
        self.detail=QLabel('Import references to original files. Browsing starts nothing.');self.detail.setWordWrap(True);self.detail.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse);layout.addWidget(self.detail)
        self.audio=QPushButton('Use as audio source');self.audio.clicked.connect(self.use_audio);layout.addWidget(self.audio)
        actions=QHBoxLayout();layout.addLayout(actions)
        self.assign=[]
        for index in range(2):
            button=QPushButton('Use in Layers' if index==0 else 'Add another instance');button.setToolTip('Select an existing matching layer, or explicitly add an independent instance. No autoplay.');button.clicked.connect(lambda checked=False,i=index:self.use_image(i));actions.addWidget(button);self.assign.append(button)
        row=QHBoxLayout();layout.addLayout(row)
        self.relink=QPushButton('Relink…');self.relink.clicked.connect(self.relink_file);row.addWidget(self.relink)
        self.refresh_button=QPushButton('Refresh');self.refresh_button.clicked.connect(lambda:self.action('refresh'));row.addWidget(self.refresh_button)
        self.remove=QPushButton('Remove reference');self.remove.clicked.connect(self.remove_reference);self.remove.setToolTip('Retains recoverable layer editing state; Undo restores the reference. Never deletes files or stops independent audio.');layout.addWidget(self.remove)
        self.state=QLabel();self.state.setWordWrap(True);self.state.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);layout.addWidget(self.state);self.selection()
    def import_files(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Import media references','',FILTER)
        if paths:self.import_paths(paths,self.collection_selected)
    def import_paths(self,paths,collection=None):
        if paths:self.shell.safe(lambda:self.shell.client.request('media_import',paths=paths,collection=collection))
    def selected_ids(self):return list(dict.fromkeys(i.data(0,Qt.UserRole) for i in self.tree.selectedItems() if i.data(0,Qt.UserRole) in self.assets))
    def eventFilter(self,watched,event):
        if watched is self.tree.viewport() and event.type() in (QEvent.DragEnter,QEvent.DragMove,QEvent.Drop) and event.mimeData().hasUrls():
            if event.type()==QEvent.Drop:self.dropEvent(event)
            else:event.acceptProposedAction()
            return True
        return super().eventFilter(watched,event)
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dragMoveEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dropEvent(self,event):
        paths=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:self.shell.safe(lambda:self.shell.client.request('media_import',paths=paths));event.acceptProposedAction()
    def refresh(self):
        data=self.shell.client.snapshot.get('media_library',{});key=json.dumps({k:v for k,v in data.items() if k!='resources'},sort_keys=True)
        if key==self.key:self.poll_thumbnails();return
        self.key=key;self.assets={a['id']:a for a in data.get('assets',[])};self.collections=data.get('collections',{});self.populate();self.poll_thumbnails()
        results=data.get('import_results',[]);self.state.setText(('Loading library…' if data.get('loading') else str(len(self.assets))+' / 128 references')+(' • '+str(len(data['pending']))+' pending' if data.get('pending') else '')+(' • '+data['error'] if data.get('error') else '')+('\n'+ '; '.join(Path(r['path']).name+': '+r['status']+(' • '+r['error'] if r['status'] in ('Failed','Cancelled') else '') for r in results[-16:]) if results else ''))
    def populate(self):
        selected=set(self.selected_ids());current=self.selected;collection_selected=self.collection_selected;query=self.search.text().strip().casefold();self.tree.blockSignals(True);self.tree.clear()
        if not selected and current in self.assets:selected={current}
        def add(group,asset):
            if query and query not in (asset['name']+' '+asset['path']).casefold() or self.type_filter.currentText() not in ('All types',asset['kind']):return
            item=QTreeWidgetItem([asset['name'],asset['status']]);item.setData(0,Qt.UserRole,asset['id']);item.setToolTip(0,asset['path']);group.addChild(item)
            if asset['id'] in self.thumbnails:item.setIcon(0,self.thumbnails[asset['id']])
            if asset['id']==current and self.tree.currentItem() is None:self.tree.setCurrentItem(item)
            item.setSelected(asset['id'] in selected)
        for kind in KINDS:
            group=QTreeWidgetItem([kind]);self.tree.addTopLevelItem(group)
            for asset in self.assets.values():
                if asset['kind']==kind:add(group,asset)
            if (query or self.type_filter.currentText()!='All types') and not group.childCount():group.setHidden(True)
            group.setExpanded(True)
        for identity,collection in self.collections.items():
            group=QTreeWidgetItem([collection['name'],'Collection']);group.setData(0,Qt.UserRole+1,identity);self.tree.addTopLevelItem(group)
            if identity==collection_selected and current is None:self.tree.setCurrentItem(group)
            for identity in collection['assets']:
                if identity in self.assets:add(group,self.assets[identity])
            group.setExpanded(True)
        self.tree.resizeColumnToContents(0);self.tree.blockSignals(False);self.selection()
    def selection(self):
        item=self.tree.currentItem();previous=self.selected;self.selected=item.data(0,Qt.UserRole) if item else None;self.collection_selected=item.data(0,Qt.UserRole+1) if item else None;asset=self.assets.get(self.selected)
        if item and item.parent():self.collection_selected=item.parent().data(0,Qt.UserRole+1)
        if previous!=self.selected or not self.name.hasFocus():
            self.name.blockSignals(True);self.name.setText(asset['name'] if asset else '');self.name.blockSignals(False)
        for widget in (self.name,self.relink,self.remove,self.refresh_button):widget.setEnabled(asset is not None)
        self.audio.setEnabled(bool(asset and asset['kind']=='Audio' and asset['status']=='Ready'))
        for widget in self.assign:widget.setEnabled(bool(asset and asset['kind'] in ('Images','Video','Animated','Models') and asset['status']=='Ready'))
        if asset:
            meta=asset.get('metadata',{});info=asset['path']+'\n'+asset['status']
            if asset['kind'] in ('Video','Animated'):info+=' • '+str(meta.get('codec',''))+' • '+str(meta.get('duration','?'))+' s • silent layer; no autoplay'
            elif asset['kind']=='Images' and 'width' in meta:info+=f" • {meta['width']}×{meta['height']} • "+meta.get('color','')
            elif asset['kind']=='Audio' and 'duration' in meta:info+=f" • {meta['duration']:.1f} s • {meta['samplerate']} Hz • {meta['channels']} ch"
            if 'bytes' in meta:info+=f"\n{meta['bytes']:,} bytes"
            if asset.get('error'):info+='\n'+asset['error']
            self.detail.setText(info)
        else:self.detail.setText('Import references to original files. Browsing starts nothing.')
    def action(self,op,**values):
        self.shell.safe(lambda:self.shell.client.request('media_action',op=op,asset=self.selected,**values));self.refresh()
    def rename(self):
        if self.selected in self.assets and self.name.text()!=self.assets[self.selected]['name']:self.action('rename',name=self.name.text())
    def relink_file(self):
        if self.selected not in self.assets:return
        path,_=QFileDialog.getOpenFileName(self,'Relink '+self.assets[self.selected]['name'],'',FILTER)
        if path:self.action('relink',path=path)
    def use_audio(self):
        self.action('audio');dock=self.shell.panels['waveform'];dock.toggleView(True);dock.setAsCurrentTab()
    def use_image(self,index):
        if self.selected in self.assets:self.shell.image_editor.add_asset(self.assets[self.selected],another=index==1,offer=True)
    def activate(self,item):
        identity=item.data(0,Qt.UserRole)
        if identity is None:item.setExpanded(not item.isExpanded());return
        self.tree.setCurrentItem(item)
        if self.audio.isEnabled():self.use_audio()
        elif self.assign[0].isEnabled():self.use_image(0)
        else:self.detail.setText(self.assets[identity].get('error') or 'Refresh/Relink this reference; the format may require an approved backend.')
    def new_collection(self):
        name,ok=QInputDialog.getText(self,'New collection','Name')
        if ok and name.strip():self.action('collection',command='create',name=name)
    def collection_action(self,command,identity):
        name=None
        if command=='rename':
            name,ok=QInputDialog.getText(self,'Rename collection','Name',text=self.collections[identity]['name'])
            if not ok:return
        self.action('collection',command=command,collection=identity,name=name)
    def remove_reference(self):
        ids=self.selected_ids()
        if not ids:return
        if not self.shell.image_editor.resolve_pending():return
        visible=[]
        for i in range(self.tree.topLevelItemCount()):
            group=self.tree.topLevelItem(i)
            if not group.isHidden() and group.isExpanded():visible.extend(group.child(j).data(0,Qt.UserRole) for j in range(group.childCount()))
        visible=list(dict.fromkeys(visible));index=min((visible.index(a) for a in ids if a in visible),default=0)
        uses=[r['name'] for r in self.shell.image_editor.config['layers'] if r['asset'] in ids]
        dialog=QMessageBox(self);dialog.setWindowTitle('Remove library references');dialog.setText(str(len(ids))+' unique references. Affected layers: '+(', '.join(uses) or 'none')+'. Originals and independent audio are retained. One Undo recovers the batch.');recover=dialog.addButton('Keep recoverable artwork',QMessageBox.ActionRole);remove=dialog.addButton('Remove affected layers',QMessageBox.DestructiveRole);dialog.addButton(QMessageBox.Cancel);dialog.exec()
        if dialog.clickedButton() in (recover,remove):
            remaining=[a for a in visible if a not in ids];self.action('remove',assets=ids,choice='recover' if dialog.clickedButton() is recover else 'layers',selection=self.shell.image_editor.selected);self.shell.image_editor.refresh(True)
            if not any(a in self.assets for a in ids):self.selected=remaining[min(index,len(remaining)-1)] if remaining else None;self.populate()
    def poll_thumbnails(self):
        from media_registry import decode_image
        changed=False
        for identity in list(self.thumb_jobs):
            if identity not in self.assets:self.thumb_jobs.pop(identity)[1].cancel();self.thumbnails.pop(identity,None)
        for identity,(key,future) in list(self.thumb_jobs.items()):
            if future.done() and not getattr(future,'displayed',False):
                future.displayed=True
                if identity not in self.assets:continue
                try:self.thumbnails[identity]=QIcon(QPixmap.fromImage(future.result()));changed=True
                except Exception:pass
        for identity,asset in self.assets.items():
            if asset['kind'] not in ('Images','Video','Animated') or asset['status']!='Ready':continue
            key=(asset['path'],asset.get('metadata',{}).get('mtime_ns'));job=self.thumb_jobs.get(identity)
            if job and job[0]==key:continue
            if sum(not f.done() for _,f in self.thumb_jobs.values())>=4:break
            def thumbnail(path=asset['path'],kind=asset['kind']):
                if kind=='Images':meta,data=decode_image(path);w,h=meta['width'],meta['height']
                else:
                    from media_frames import DecoderWindow
                    import threading
                    decoder=DecoderWindow(path,32*1024*1024)
                    try:pts,(w,h,data)=decoder.get(0.,threading.Event())
                    finally:decoder.close()
                image=QImage(data,w,h,QImage.Format_RGBA8888_Premultiplied).mirrored(False,True);return image.scaled(64,64,Qt.KeepAspectRatio,Qt.SmoothTransformation)
            self.thumb_jobs[identity]=(key,self.pool.submit(thumbnail))
        if changed:self.populate()
    def close_resources(self):self.pool.shutdown(wait=False,cancel_futures=True)
    def menu(self,pos):
        item=self.tree.itemAt(pos)
        if item and not item.isSelected():self.tree.setCurrentItem(item)
        menu=QMenu(self)
        if self.collection_selected and self.selected is None:
            menu.addAction('Import into this collection…',self.import_files)
            for label,command in (('Rename collection','rename'),('Delete collection (keep assets)','delete')):menu.addAction(label,lambda checked=False,c=command:self.collection_action(c,self.collection_selected))
            menu.exec(self.tree.mapToGlobal(pos));return
        if self.selected not in self.assets:return
        if self.audio.isEnabled():menu.addAction('Use as audio source (no autoplay)',self.use_audio)
        if self.assign[0].isEnabled():
            for index,label in enumerate(('Use in Layers (no autoplay)','Add another instance')):menu.addAction(label,lambda checked=False,i=index:self.use_image(i))
            if self.assets[self.selected]['kind']=='Images':menu.addAction('Use as sprite sheet',lambda:self.shell.image_editor.add_asset(self.assets[self.selected],kind='Sprite'))
        collections=menu.addMenu('Collection membership')
        for identity,collection in self.collections.items():
            action=collections.addAction(collection['name']);action.setCheckable(True);action.setChecked(all(a in collection['assets'] for a in self.selected_ids()));action.triggered.connect(lambda checked,i=identity:self.action('collection',command='add' if checked else 'remove',collection=i,assets=self.selected_ids()))
        menu.addAction('Refresh validation',lambda:self.action('refresh'));menu.addAction('Relink…',self.relink_file);menu.addAction('Remove reference; keep file',self.remove_reference);menu.exec(self.tree.mapToGlobal(pos))

class ImageLayerEditor(QWidget):
    def __init__(self,shell):
        super().__init__();self.shell=shell;self.config=defaults();self.binding=None;self.asset_key=None;self.syncing=False;self.widgets=[]
        layout=QVBoxLayout(self);layout.setContentsMargins(8,8,8,8)
        self.presentation=TwoWaySwitch('Presentation',PRESENTATIONS,lambda active:self.edit_presentation(PRESENTATIONS[int(active)]));layout.addWidget(self.presentation)
        hint=QLabel('Use visual Start / Pause / Stop. Main previews support both modes; legacy Experimental does not. Image only covers the world while its histories continue.');hint.setWordWrap(True);layout.addWidget(hint)
        scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();rows=QVBoxLayout(body);scroll.setWidget(body);layout.addWidget(scroll,1)
        for index,identity in enumerate(LAYER_IDS):
            box=QGroupBox('Image layer '+str(index+1));form=QFormLayout(box);rows.addWidget(box);widgets={}
            combo=QComboBox();combo.setMinimumContentsLength(12);combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);form.addRow('Asset',combo);widgets['asset']=combo
            combo.currentIndexChanged.connect(lambda unused,i=index:self.assign(i,self.widgets[i]['asset'].currentData()))
            visible=TwoWaySwitch('Visible',('Off','On'),lambda value,i=index:self.edit(i,'enabled',value));form.addRow(visible);widgets['enabled']=visible
            opacity=QSlider(Qt.Horizontal);opacity.setRange(0,100);opacity.setToolTip('Image opacity; source pigments are unchanged.');form.addRow('Opacity',opacity);widgets['opacity']=opacity
            opacity.valueChanged.connect(lambda value,i=index:self.edit(i,'opacity',value/100.))
            fit=TwoWaySwitch('Aspect',('Fit','Fill'),lambda value,i=index:self.edit(i,'fit','Fill' if value else 'Fit'));form.addRow(fit);widgets['fit']=fit
            for key,title,low,high,step,suffix in (('x','Position X',-100,100,1,' %'),('y','Position Y',-100,100,1,' %'),('scale','Scale',10,400,5,' %')):
                spin=QDoubleSpinBox();spin.setRange(low,high);spin.setDecimals(1);spin.setSingleStep(step);spin.setSuffix(suffix);spin.setKeyboardTracking(False);form.addRow(title,spin);widgets[key]=spin
                spin.valueChanged.connect(lambda value,i=index,k=key:self.edit(i,k,value/100.))
            buttons=QHBoxLayout();front=QPushButton('Bring to front');front.clicked.connect(lambda checked=False,i=index:self.reorder(i));buttons.addWidget(front);widgets['front']=front
            reset=QPushButton('Reset transform');reset.clicked.connect(lambda checked=False,i=index:self.reset(i));buttons.addWidget(reset);form.addRow(buttons);self.widgets.append(widgets)
        rows.addStretch();self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(75);self.timer.timeout.connect(self.commit)
    def current_binding(self):
        snap=self.shell.client.snapshot;media=snap.get('media_control',{})
        return dict(media_session=media.get('session'),media_revision=media.get('revision'),preview_run=snap.get('preview_run'),destination_revision=snap.get('destination_revision'))
    def refresh(self,force=False):
        snap=self.shell.client.snapshot;binding=self.current_binding();changed=force or binding!=self.binding
        if changed:
            self.timer.stop();self.binding=binding;self.config=deepcopy(snap['values'].get('media',defaults()))
        assets=[a for a in snap.get('media_library',{}).get('assets',[]) if a['kind']=='Images'];asset_key=[(a['id'],a['name'],a['status']) for a in assets]
        if changed or asset_key!=self.asset_key:
            self.syncing=True;self.asset_key=asset_key
            try:
                self.presentation.setCurrentText(self.config['presentation'])
                for row,widgets in zip(self.config['layers'],self.widgets):
                    combo=widgets['asset'];combo.blockSignals(True);combo.clear();combo.addItem('None',None)
                    for asset in assets:combo.addItem(asset['name']+' • '+asset['status'],asset['id'])
                    selected=combo.findData(row['asset']);combo.setCurrentIndex(max(0,selected));combo.blockSignals(False)
                    widgets['enabled'].sync(row['enabled']);widgets['fit'].setCurrentText(row['fit']);widgets['front'].setEnabled(row['order']==0)
                    for key in ('opacity','x','y','scale'):
                        widget=widgets[key];widget.blockSignals(True);widget.setValue(round(row[key]*100) if key=='opacity' else row[key]*100);widget.blockSignals(False)
            finally:self.syncing=False
        state=snap.get('preview',{}).get('image_layers',{})
        text='Original image colors • no tint/effects • up to two layers'
        if state.get('pending'):text+='\nDecoding/upload pending; previous composition retained.'
        if state.get('error'):text+='\n'+state['error']
        if state and state.get('applied_revision')!=self.binding['media_revision'] and not state.get('pending'):text+='\nSettings differ from displayed layers; Start a fresh preview or apply an edit.'
        self.status.setText(text)
    def edit(self,index,key,value):
        if self.syncing:return
        self.config['layers'][index][key]=value;self.timer.start()
    def edit_presentation(self,value):
        if self.syncing:return
        self.config['presentation']=value;self.timer.start()
    def assign(self,index,asset):
        if self.syncing:return
        self.refresh();self.config['layers'][index].update(asset=asset,enabled=asset is not None);self.timer.stop();self.commit()
    def reorder(self,index):
        self.config['layers'][index]['order']=1;self.config['layers'][1-index]['order']=0;self.timer.stop();self.commit()
    def reset(self,index):
        row=self.config['layers'][index];row.update(opacity=1.,fit='Fit',x=0.,y=0.,scale=1.);self.timer.stop();self.commit()
    def commit(self):
        if self.syncing or self.binding is None:return
        self.shell.safe(lambda:self.shell.client.request('image_layers',presentation=self.config['presentation'],layers=deepcopy(self.config['layers']),**self.binding));self.refresh(True)
