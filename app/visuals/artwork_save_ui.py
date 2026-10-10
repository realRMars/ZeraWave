"""Composition and selected-layer image Save / Save As, separate from sessions."""
from pathlib import Path
from copy import deepcopy
import os,time
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog,QFormLayout,QComboBox,QLabel,QLineEdit,QPushButton,QHBoxLayout,QDialogButtonBox,QFileDialog,QColorDialog,QSpinBox,QMessageBox
from artwork_export import ImageSaves,capture,output_key

class SaveOptions(QDialog):
    def __init__(self,controller,ids,composition,save_as):
        super().__init__(controller.e);self.controller=controller;self.ids=ids;self.save_as=save_as;self.setWindowTitle('Save artwork image'+(' As' if save_as else ''));form=QFormLayout(self)
        self.scope=QComboBox();choices=[('Composition canvas','composition')] if composition else [('Selected layer own artwork','own'),('Selected layer with children','branch')] if len(ids)==1 else [('Selected layers and branches, aligned','selection'),('Selected own artwork only, aligned','own')]
        for text,value in choices:self.scope.addItem(text,value)
        self.destination=QLineEdit();self.destination.setMinimumWidth(420);self.format=QComboBox()
        for fmt in controller.saves.capabilities:self.format.addItem(fmt.upper(),fmt)
        self.details=QLabel();self.details.setWordWrap(True);self.background=QColor('#ffffff');self.bg=QPushButton('Flattening background: white');self.bg.clicked.connect(self.pick_background);self.quality=QSpinBox();self.quality.setRange(0,100);self.quality.setValue(95)
        form.addRow('Scope',self.scope);form.addRow(self.details);form.addRow('Encoded format',self.format)
        line=QHBoxLayout();line.addWidget(self.destination);browse=QPushButton('Choose file…');browse.clicked.connect(self.browse);line.addWidget(browse);form.addRow('Output file',line);form.addRow(self.bg);form.addRow('Writer quality (lossy formats)',self.quality)
        note=QLabel('Visibility-off artwork is excluded. Layers use tight canvas-space geometric bounds at authored pixel scale, including content outside the canvas. Ancestor transforms and isolation apply. Editable artwork stays intact.');note.setWordWrap(True);form.addRow(note)
        self.buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);self.buttons.accepted.connect(self.check);self.buttons.rejected.connect(self.reject);form.addRow(self.buttons)
        self.scope.currentIndexChanged.connect(self.scope_changed);self.format.currentIndexChanged.connect(self.format_changed)
        self.scope_changed()
        if save_as:self.destination.clear()
    def scope_changed(self):
        scope=self.scope.currentData();entry=self.controller.association(scope,self.ids)
        self.destination.setText(entry['path'] if entry else '')
        fmt=entry['format'] if entry else 'png';n=self.format.findData(fmt);self.format.setCurrentIndex(max(0,n));self.background=QColor(entry['background'] if entry else '#ffffff');self.quality.setValue(entry['quality'] if entry else 95)
        try:
            self.pin=capture(self.controller.e,scope,self.ids);x,y,w,h=self.pin['bounds'];self.details.setText(f'{w} × {h} px • canvas origin ({x}, {y}) • accepted revision {self.pin["revision"]}'+('\nCurrent decoded still frames: '+', '.join(self.pin['frames']) if self.pin['frames'] else ''))
        except Exception as exc:self.pin=None;self.details.setText(str(exc))
        self.format_changed()
    def format_changed(self):
        fmt=self.format.currentData();cap=self.controller.saves.capabilities.get(fmt,{})
        self.bg.setVisible(not cap.get('alpha',False));self.bg.setText('Flattening background: '+self.background.name());self.bg.setStyleSheet('background:'+self.background.name()+';color:'+('#000000' if self.background.lightness()>127 else '#ffffff'))
        self.format.setToolTip(('1-bit monochrome format.' if fmt in ('pbm','xbm','wbmp') else 'Grayscale format.' if fmt=='pgm' else 'Icon format: at most 256 pixels per side.' if fmt in ('cur','ico') else 'Lossy color/detail encoding.' if cap.get('lossy') else 'Installed lossless still-image writer.'))
        quality_visible=cap.get('quality',False) and cap.get('lossy',False);self.quality.setVisible(quality_visible);self.layout().labelForField(self.quality).setVisible(quality_visible);self.quality.setToolTip('Installed writer option. JPEG/WebP may lose color/detail. Alpha-capable outputs retain transparency.')
    def pick_background(self):
        value=QColorDialog.getColor(self.background,self,'Opaque image background')
        if value.isValid():value.setAlpha(255);self.background=value;self.format_changed()
    def browse(self):
        fmt=self.format.currentData();extension='jpg' if fmt=='jpeg' else fmt
        path,_=QFileDialog.getSaveFileName(self,'Choose artwork output',self.destination.text(),f'{fmt.upper()} image (*.{extension})')
        if path:self.destination.setText(path);self.browse_approved=str(Path(path).resolve())
    def check(self):
        if not self.pin:QMessageBox.warning(self,'Artwork not captured',self.details.text());return
        fmt=self.format.currentData();extension='jpg' if fmt=='jpeg' else fmt
        path=Path(self.destination.text()).expanduser()
        if not path.is_absolute():QMessageBox.warning(self,'Choose output','Choose an absolute folder and filename.');return
        if path.suffix.lower() not in ('.'+extension,'.jpeg' if fmt=='jpeg' else '.'+extension):path=path.with_suffix('.'+extension);self.destination.setText(str(path))
        if not path.parent.is_dir():QMessageBox.warning(self,'Choose output','The output folder does not exist.');return
        if self.controller.protected_output(path):QMessageBox.warning(self,'Protect original','Choose a new output; referenced artwork and imported originals are preserved.');return
        association=self.controller.association(self.scope.currentData(),self.ids)
        same=not self.save_as and association and os.path.normcase(str(path.resolve()))==os.path.normcase(association['path'])
        if path.exists() and not same and getattr(self,'browse_approved',None)!=str(path.resolve()) and QMessageBox.question(self,'Overwrite artwork image?',str(path)+'\nReplace this existing image?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.path=str(path.resolve());self.options=dict(background=self.background.name(),quality=self.quality.value());self.accept()

class ArtworkSaveController:
    def __init__(self,editor):
        self.e=editor;self.saves=ImageSaves();self.association_jobs=[];self.request=None;self.timer=QTimer(editor);self.timer.setInterval(25);self.timer.timeout.connect(self.poll);self.timer.start()
    def protected_output(self,path):
        destination=os.path.normcase(str(Path(path).resolve()))
        originals={os.path.normcase(os.path.abspath(a['path'])) for a in self.e.media_assets() if a.get('path')}
        originals.update(os.path.normcase(os.path.abspath(a['path'])) for a in self.e.config['assets'] if a.get('path'))
        return destination in originals
    def association(self,scope,ids):
        key=output_key(scope,ids)
        return next((v for v in self.e.shell.client.snapshot.get('values',{}).get('artwork_outputs',[]) if output_key(v['scope'],v['targets'])==key),None)
    def save(self,save_as=False,ids=None):
        if getattr(self.e.shell,'close_request',None):self.e.status.setText('Image save unavailable during close; Cancel close to continue.');return
        if self.request:self.e.status.setText('An artwork save request is already reconciling.');return
        if len(self.saves.jobs)>=2:self.e.status.setText('Two image saves pending; wait before another capture.');return
        self.request=dict(ids=list(ids) if ids is not None else [],composition=ids is None,save_as=save_as,started=time.monotonic());self.poll()
    def poll(self):
        if hasattr(self.e,'editor_view') and hasattr(self.e.editor_view,'image_save_cancel_action'):self.e.editor_view.image_save_cancel_action.setVisible(bool(self.request or self.saves.jobs))
        for result in self.saves.poll():
            if result['status']=='durable':
                association={k:result[k] for k in ('scope','targets','path','format','background','quality','fingerprint')}
                if result['session']==self.e.binding[0]:
                    future=self.e.shell.client.edits.submit(self.e.shell.client.request,'artwork_output',media_session=result['session'],association=association);self.association_jobs.append((future,result))
                else:self.e.status.setText('Artwork image saved for previous session: '+result['path']+'. No current-session association changed.')
            else:self.e.status.setText('Artwork image save '+result['status']+'; prior output and association retained: '+result.get('error',''))
        for future,result in list(self.association_jobs):
            if not future.done():continue
            self.association_jobs.remove((future,result))
            try:future.result();self.e.status.setText(f"Saved {result['scope']} • {result['format'].upper()} • {result['dimensions'][0]} × {result['dimensions'][1]} • accepted revision {result['revision']} → {result['path']}."+(' Later edits remain unsaved for this output.' if self.e.binding[1]!=result['revision'] else ' Editable session saving remains separate.'))
            except Exception as exc:self.e.status.setText('Image saved to '+result['path']+'; destination association could not be confirmed: '+str(exc))
        request=self.request
        if not request:return
        if self.e.edit_jobs or self.e.art_jobs or self.e.shell.client.edit_count or self.e.fill_controller.job is not None:
            if time.monotonic()-request['started']>15:self.request=None;self.e.status.setText('Image capture deferred: edits are still unresolved. Accepted work retained.');return
            return
        self.request=None
        if self.e.canvas.stroke or self.e.canvas.interactive or self.e.canvas.drag or getattr(self.e,'numeric_before',None) or self.e.preview_active:
            self.e.status.setText('Finish or cancel the active gesture before image saving. Preview is not accepted artwork.');return
        try:
            if not request['save_as']:
                scope='composition' if request['composition'] else 'own' if len(request['ids'])==1 else 'selection'
                if not request['composition']:
                    matches=[v for v in self.e.shell.client.snapshot.get('values',{}).get('artwork_outputs',[]) if sorted(v['targets'])==sorted(request['ids'])]
                    if matches:scope=matches[-1]['scope']
                entry=self.association(scope,request['ids'])
                if entry:
                    if self.protected_output(entry['path']):raise ValueError('Assigned output is now referenced artwork or an imported original. Use Save As to a new file; source retained.')
                    pin=capture(self.e,scope,request['ids']);self.saves.submit(pin,entry['path'],entry['format'],entry);self.e.status.setText('Saving captured artwork to '+entry['path']);return
            dialog=SaveOptions(self,request['ids'],request['composition'],request['save_as'])
            if dialog.exec()!=QDialog.Accepted:return
            # Modal choices hold a consistent immutable revision; capture and
            # output scope cannot drift when the selected layer later changes.
            self.saves.submit(dialog.pin,dialog.path,dialog.format.currentData(),dialog.options);self.e.status.setText('Saving accepted artwork image to '+dialog.path+'…')
        except Exception as exc:self.e.status.setText('Artwork image not saved; accepted work retained: '+str(exc))
    def cancel(self):
        self.request=None;self.saves.cancel_all();self.e.status.setText('Image save cancellation requested; actual completion will be reported. Prior good outputs stay protected.')
    def pending(self):return bool(self.request or self.saves.jobs or self.association_jobs)
    def close(self):self.request=None;self.saves.close();self.timer.stop()
