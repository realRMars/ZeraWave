"""Small Source review surface using existing owner, transport and export paths."""
from copy import deepcopy
from concurrent.futures import CancelledError
from fractions import Fraction
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QBoxLayout,QLabel,QPushButton,QToolButton,QSpinBox,QLineEdit,QPlainTextEdit,QComboBox,QFileDialog,QScrollArea,QSizePolicy
from video_project import rational,pair,duration
from project_review import source_interval,remember_change,marks,query_from_mark,export_values,describe
EMPTY={}

class SourceReview(QWidget):
    def __init__(self,source):
        super().__init__();self.source=source;self.w=source.workspace;self.future=None;self.intent=None;self.desired=None;self.serial=0;self.closed=False;self.report=None;self.report_context=None;self.report_refs=None;self.failure_context=None;self.failure_refs=None;self.last_mode='source';self.cancel_futures=[];self.mark_token=None;self.context_refs=None;self.context_values=None;self.context_generations=[0,0,0];self.equal_publications=[0,0,0];self.export_record=None;self.sample_future=None;self.wrap_rows=[];self.units_token=None;self.last_discard=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(3)
        self.toggle=QToolButton();self.toggle.setText('Source / timeline review');self.toggle.setCheckable(True);self.toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon);self.toggle.setArrowType(Qt.RightArrow);self.toggle.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);layout.addWidget(self.toggle)
        # One authoring scroll viewport, shared with the surrounding Source
        # controls. The actual native preview is never a scroll descendant.
        self.scroll=source.controls_scroll;self.body=QWidget();body=QVBoxLayout(self.body);body.setContentsMargins(0,0,0,0);body.setSpacing(3);layout.addWidget(self.body);self.body.hide();self.toggle.toggled.connect(self.expand)
        row=QBoxLayout(QBoxLayout.LeftToRight);self.wrap_rows.append(row);body.addLayout(row);self.before=QSpinBox();self.after=QSpinBox()
        for name,box in [('Before Source frames',self.before),('After Source frames',self.after)]:
            box.setAccessibleName(name);box.setRange(0,2**31-1);box.setKeyboardTracking(False);label=QLabel(name);label.setWordWrap(True);row.addWidget(label);row.addWidget(box)
        self.units=QLabel('Handles use native Source-frame units; sequence frames are separate.');self.units.setWordWrap(True);body.addWidget(self.units)
        self.purpose=QLineEdit();self.purpose.setMaxLength(512);self.purpose.setPlaceholderText('Purpose of this exact sample…');self.purpose.setAccessibleName('Review sample purpose');body.addWidget(self.purpose)
        row=QBoxLayout(QBoxLayout.LeftToRight);self.wrap_rows.append(row);body.addLayout(row);self.sequence_in=QSpinBox();self.sequence_out=QSpinBox()
        for name,box in [('Sequence In frame',self.sequence_in),('Out exclusive frame',self.sequence_out)]:
            box.setRange(0,2**31-1);box.setKeyboardTracking(False);box.setAccessibleName('Review '+name);label=QLabel(name);label.setWordWrap(True);row.addWidget(label);row.addWidget(box)
        self.buttons={}
        for values in [[('Inspect Source',lambda:self.request('source')),('Inspect placement',lambda:self.request('placement'))],[('Open clip source',self.open_selected),('Use Program range',self.use_program)],[('Map context',self.use_mapping),('Validate report',lambda:self.request(self.last_mode,True))],[('Set Source handles',self.set_source),('Select sample range',self.select_range)],[('Remember range',self.remember),('Export sample…',self.export_sample)],[('Check sample',lambda:self.sample_action('operation_status')),('Cancel sample',lambda:self.sample_action('cancel'))]]:
            row=QBoxLayout(QBoxLayout.LeftToRight);self.wrap_rows.append(row);body.addLayout(row)
            for label,fn in values:
                button=QPushButton(label);button.clicked.connect(lambda checked=False,fn=fn:self.w.shell.safe(fn));button.setAccessibleName(label);button.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);row.addWidget(button);self.buttons[label]=button
        row=QBoxLayout(QBoxLayout.LeftToRight);self.wrap_rows.append(row);body.addLayout(row);self.saved=QComboBox();self.saved.setAccessibleName('Saved review marks');self.saved.setMinimumContentsLength(8);self.saved.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon);self.saved.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);row.addWidget(self.saved,1);self.saved.currentIndexChanged.connect(self.recall_fields);button=QPushButton('Inspect saved');button.clicked.connect(lambda:self.w.shell.safe(lambda:self.request('saved')));row.addWidget(button);self.buttons['Inspect saved']=button
        self.status=QLabel('Read-only review. Before/after use the source nominal frame grid. Set Source handles, then use existing Source Loop/Play to audition.');self.status.setWordWrap(True);body.addWidget(self.status)
        self.details=QPlainTextEdit();self.details.setReadOnly(True);self.details.setMaximumHeight(150);self.details.setMinimumWidth(0);self.details.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred);self.details.setAccessibleName('Source mapping and repeated use report');body.addWidget(self.details)
        self.page_label=QLabel('Source uses not inspected.');self.page_label.setWordWrap(True);body.addWidget(self.page_label);row=QBoxLayout(QBoxLayout.LeftToRight);self.wrap_rows.append(row);body.addLayout(row);self.previous_page=QPushButton('Previous uses');self.next_page=QPushButton('Next uses');row.addWidget(self.previous_page);row.addWidget(self.next_page);self.previous_page.setEnabled(False);self.next_page.setEnabled(False);self.previous_page.clicked.connect(lambda:self.w.shell.safe(lambda:self.page(-1)));self.next_page.clicked.connect(lambda:self.w.shell.safe(lambda:self.page(1)))
        self.body.setMinimumWidth(0);self.body.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)
        self.export_status=QLabel();self.export_status.setWordWrap(True);body.addWidget(self.export_status);cancel=QPushButton('Cancel inspection');cancel.clicked.connect(self.cancel);body.addWidget(cancel)
    def expand(self,checked):self.body.setVisible(checked);self.toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
    def resizeEvent(self,event):
        for row in self.wrap_rows:row.setDirection(QBoxLayout.TopToBottom if self.width()<380 else QBoxLayout.LeftToRight)
        super().resizeEvent(event)
    def selected_clip(self):
        canvas=self.w.timeline.canvas;d=self.w.document();key=canvas.selected[1] if isinstance(canvas.selected,tuple) and canvas.selected[0]=='clips' else None
        clip=next((c for c in d['clips'] if c['id']==key),None)
        if clip is None and len(canvas.selection)==1:clip=next((c for c in d['clips'] if c['id'] in canvas.selection),None)
        if clip is None:raise ValueError('Select one ordinary timeline clip for placement review.')
        return clip
    def context(self):
        state=self.w.state();d=state.get('document') or EMPTY;media=state.get('media') or EMPTY;s=state.get('source') or EMPTY;sd=s.get('document') or EMPTY;c=self.w.timeline.canvas
        # Every retained report/intent also keeps this tuple, not merely the
        # latest poll. Older object addresses cannot recycle into a false match
        # after multiple availability-only publications at the same revision.
        refs=(d,media,sd)
        if self.context_values is not None:
            for index,(new,old) in enumerate(zip(refs,self.context_values)):
                if new is not old:
                    if new!=old:self.context_generations[index]+=1
                    else:self.equal_publications[index]+=1
        self.context_values=refs;self.context_refs=refs
        # Equal detached refreshes are not new intent. Meaningful A→B→A
        # changes still increment monotonically, without hashing on idle polls.
        return (state.get('epoch'),state.get('revision'),state.get('project_id'),self.context_generations[0],self.context_generations[1],s.get('epoch'),s.get('revision'),self.context_generations[2],tuple(sorted(c.selection)),repr(c.selected),self.source.in_box.value(),self.source.out_box.value(),self.before.value(),self.after.value(),self.sequence_in.value(),self.sequence_out.value(),self.purpose.text(),self.saved.currentData())
    def use_program(self):
        clock=self.w.transport_state();self.sequence_in.setValue(clock.get('range_in',0));self.sequence_out.setValue(clock.get('range_out',duration(self.w.document())))
    def open_selected(self):
        clip=self.selected_clip();asset=next(a for a in self.w.document()['media'] if a['id']==clip['asset']);self.w.video_panels.open_source(asset)
    def query(self,mode):
        d=self.w.document();binding=self.w.binding();sequence=[self.sequence_in.value(),self.sequence_out.value()];handles=[self.before.value(),self.after.value()]
        if sequence==[0,0] and duration(d)==0:sequence=None
        if mode=='saved':
            key=self.saved.currentData();mark=next((r for r in marks(d)['items'] if r['id']==key),None)
            if mark is None:raise ValueError('Choose a saved authored review mark.')
            query=query_from_mark(d,mark,binding,self.w.state().get('source'));query.update(handles=handles,range=sequence,purpose=self.purpose.text());return query
        if mode=='placement':
            clip=self.selected_clip();asset=next(a for a in d['media'] if a['id']==clip['asset']);span=source_interval(d,clip,asset)
            return dict(op='review_inspect',**binding,source=asset['id'],source_range=[pair(t) for t in span],handles=handles,range=sequence,purpose=self.purpose.text(),clip=clip['id'])
        if not self.source.asset or not self.source.version:raise ValueError('Open media in Source before inspecting its requested In/Out.')
        asset=self.source.asset;fps=rational(self.source.fps);clip=None
        try:
            selected=self.selected_clip();known=next(a for a in d['media'] if a['id']==selected['asset'])
            if known['sha256']==asset['sha256']:clip=selected['id']
        except ValueError:pass
        return dict(op='review_inspect',**binding,source=asset['id'],source_epoch=self.source.version[0],source_range=[pair(Fraction(self.source.in_box.value())/fps),pair(Fraction(self.source.out_box.value())/fps)],handles=handles,range=sequence,purpose=self.purpose.text(),clip=clip)
    def submit_query(self,query):
        from project_api import call
        endpoint=self.w.state().get('endpoint')
        if not endpoint:raise ValueError('Owner endpoint unavailable; no query submitted.')
        return self.w.shell.operations.submit(call,endpoint,query)
    def page(self,direction):
        if self.report is None or self.report_context!=self.context() or self.future is not None or self.desired is not None:raise ValueError('Inspect the current context before changing source-use pages.')
        uses=self.report['duplicate_use'];offset=max(0,uses['offset']-uses['limit']) if direction<0 else uses['next_offset']
        if offset is None:return
        query=dict(op='review_inspect',**self.w.binding(),**deepcopy(self.report['certificate']['query']));query.update(offset=offset,query_id=uuid.uuid4().hex);self.serial+=1;self.failure_context=None;self.failure_refs=None;context=self.context();self.desired=(self.serial,context,query,self.context_refs);self.status.setText('Pending · requested bounded source-use page.');self.poll()
    def request(self,mode,validate=False):
        query=self.query(mode)
        if validate:
            if self.report is None:raise ValueError('Inspect a sample before validating retained provenance.')
            query['prior']=deepcopy(self.report['certificate'])
            for name in ('offset','limit'):query[name]=self.report['certificate']['query'][name]
        self.last_mode=mode;self.serial+=1;self.failure_context=None;self.failure_refs=None;query['query_id']=uuid.uuid4().hex;context=self.context();self.desired=(self.serial,context,query,self.context_refs);self.status.setText('Pending · immutable source/timeline review; no edit or output started.');self.poll()
    def cancel(self):
        self.serial+=1;self.desired=None
        if self.future is not None and not self.future.done():
            if not self.future.cancel() and self.intent and not self.cancel_futures:
                from project_api import call
                endpoint=self.w.state().get('endpoint')
                if endpoint:self.cancel_futures.append(self.w.shell.operations.submit(call,endpoint,dict(op='review_cancel',query_id=self.intent[2]['query_id'])))
        if not self.closed:self.failed_context();self.status.setText('Cancel requested · pending reply still reconciles; retained report is not promoted.')
    def failed_context(self,context=None,refs=None):
        self.failure_context=self.context() if context is None else context;self.failure_refs=self.context_refs if refs is None else refs
    def current_report(self):
        if self.report is None or self.future is not None or self.desired is not None or self.failure_context==self.context() or self.report_context!=self.context() or self.report['status']!='ready':raise ValueError('Report is pending/outdated/unavailable. Inspect or explicitly validate at the current accepted revision first.')
        return self.report
    def set_source(self):
        report=self.current_report();asset=self.source.asset
        if not asset or asset['sha256']!=report['source']['sha256'] or not self.source.version:raise ValueError('Open this same source explicitly before setting its handled In/Out. Program remains independent.')
        if report['source']['effective_grid'] is None:raise ValueError('This exact fractional tail has no complete Source audition frame. Its natural content interval remains in the report; no extra frame is invented.')
        self.w.transport('range',list(report['source']['effective_grid']),target='source',source_epoch=self.source.version[0],binding=self.w.binding());self.status.setText('Source handled In/Out submitted. Use existing Source Loop/Play to audition; Program position is unchanged.')
    def select_range(self):
        report=self.current_report()
        if report['sequence']['range'] is None:raise ValueError('This is a Source-only review; place material before selecting a mixed Program interval.')
        self.w.transport('range',list(report['sequence']['range']),binding=self.w.binding());self.status.setText('Mixed Program sample range submitted; Source position is unchanged.')
    def use_mapping(self):
        mapping=self.current_report().get('mapping');value=(mapping or {}).get('suggested_sequence_range')
        if not value:raise ValueError('No selected placement maps this source interval into the sequence.')
        self.sequence_in.setValue(value[0]);self.sequence_out.setValue(value[1]);self.status.setText('Mapped integer context bounds entered. Inspect this requested mixed range deliberately; source handles are not newly placed footage.')
    def remember(self):
        report=self.current_report();binding=self.w.binding();key=self.saved.currentData() if self.last_mode=='saved' else uuid.uuid4().hex;change=remember_change(self.w.document(),report,key,binding);self.w.batch('Remember source review purpose and range',[change],binding)
    def recall_fields(self,*_):
        d=self.w.state().get('document')
        if not d:return
        try:mark=next((r for r in marks(d)['items'] if r['id']==self.saved.currentData()),None)
        except ValueError:return
        if mark:
            self.before.setValue(mark['handles'][0]);self.after.setValue(mark['handles'][1]);self.sequence_in.setValue((mark['sequence_range'] or [0,0])[0]);self.sequence_out.setValue((mark['sequence_range'] or [0,0])[1]);self.purpose.setText(mark['purpose'])
    def export_sample(self,path=None):
        report=self.current_report();binding=self.w.binding();crf=self.w.document()['export']['crf']
        if report['sequence']['range'] is None:raise ValueError('Source-only audition has no mixed export interval. Place clips and inspect a sequence range first.')
        if self.export_record and (self.export_record.get('outcome') or {}).get('status') not in ('exported','failed','rejected'):raise ValueError('The preceding sample is pending/unknown. Check that SAME sample before starting another; no replacement operation ID was submitted.')
        if path is None:path,_=QFileDialog.getSaveFileName(self,'Export exact review sample',str(self.w.dialog_directory('export')/'review-sample.mp4'),'MP4 H264/AAC (*.mp4)')
        if not path:return
        values=export_values(report,binding,path,crf);key=self.w.submit('export',binding=binding,**values);context=self.context();self.export_record=dict(id=key,path=path,certificate=deepcopy(report['certificate']),context=context,refs=self.context_refs);self.export_status.setText('Submitted exact sample · revision '+str(report['binding']['revision'])+' · range '+str(report['sequence']['range'])+'. Reconcile this operation ID; no automatic resubmission.')
        return key
    def sample_action(self,op):
        self.sample_reply()
        if not self.export_record:raise ValueError('No review sample has been submitted in this pane.')
        if self.sample_future is not None:raise ValueError('The same sample check/cancel is still reconciling; no duplicate request was submitted.')
        self.sample_future=self.w.client.submit('project',request=dict(op=op,operation_id=self.export_record['id']));self.export_status.setText(('Checking' if op=='operation_status' else 'Cancel requested for')+' the SAME sample '+self.export_record['id'][:8]+'. Accepted work and prior output remain intact.')
    def sample_reply(self):
        if self.sample_future is None or not self.sample_future.done():return
        future=self.sample_future;self.sample_future=None
        try:
            reply=future.result();outcome=reply.get('outcome')
            if outcome and outcome.get('id')==self.export_record['id']:self.export_record['outcome']=deepcopy(outcome);self.export_record.pop('lookup_error',None)
            else:self.export_record['lookup_error']=reply.get('error',{}).get('message','Sample outcome unavailable/retired. Inspect its original output/diagnostics; do not duplicate the operation.')
        except Exception as exc:self.export_record['lookup_error']='Outcome uncertain: '+str(exc)+'. Check the SAME sample; do not submit a replacement ID.'
    def poll(self):
        self.cancel_futures=[f for f in self.cancel_futures if not f.done()]
        if self.closed:return
        state=self.w.state();d=state.get('document');token=(state.get('epoch'),state.get('revision'))
        unit_token=(state.get('epoch'),state.get('revision'),self.source.version,repr(self.w.timeline.canvas.selected),self.last_mode,id(self.report))
        if unit_token!=self.units_token:
            self.units_token=unit_token;native=self.source.fps
            if self.report and self.last_mode!='source':native=self.report['source']['fps']
            project=(d or {}).get('settings',{}).get('fps',[30,1]);self.units.setText('Before/after are Source frames at '+f'{float(rational(native)):g}'+' FPS. Sequence controls use project frames at '+f'{float(rational(project)):g}'+' FPS.')
        if token!=self.mark_token:
            replacing=self.mark_token is None or token[0]!=(self.mark_token or (None,))[0];self.mark_token=token
            if replacing and d:self.use_program()
            old=self.saved.currentData();self.saved.blockSignals(True);self.saved.clear()
            try:
                for mark in marks(d)['items'] if d else []:self.saved.addItem((mark['purpose'] or 'Review range')[:60]+' · '+mark['id'][:8],mark['id'])
                index=self.saved.findData(old);self.saved.setCurrentIndex(index if index>=0 else -1)
            except ValueError as exc:self.status.setText('Unavailable saved metadata: '+str(exc)+'. Existing data retained.')
            self.saved.blockSignals(False)
        if self.future is not None and self.future.done():
            future=self.future;serial,context,query,refs=self.intent;self.future=None
            try:
                reply=future.result()
                current_context=self.context()
                if serial!=self.serial or context!=current_context:
                    self.last_discard=dict(serial=serial,current_serial=self.serial,submitted=list(context),current=list(current_context),changed=[i for i,(a,b) in enumerate(zip(context,current_context)) if a!=b]);self.failed_context();self.status.setText('Outdated completion discarded · context/selection/range changed. Inspect deliberately again.')
                elif not reply.get('ok'):
                    error=reply.get('error',{});code=error.get('code');status='Outdated' if code in ('stale_revision','stale_source','stale_source_verification','stale_placement') else 'Unavailable' if code in ('missing_source','missing_media','no_project') else 'Cancelled' if code=='cancelled' else 'Failed';self.failed_context(context,refs);self.status.setText(status+' · '+error.get('message','Owner review failed')+' No edit or automatic retry.')
                else:
                    report=reply['report']
                    if (report['binding']['epoch'],report['binding']['revision'],report['binding']['project'])!=context[:3]:raise ValueError('Owner report belongs to another accepted binding.')
                    self.failure_context=None;self.failure_refs=None;self.report=deepcopy(report);self.report_context=context;self.report_refs=refs;self.details.setPlainText(describe(report));self.status.setText(report['status'].title()+' · revision '+str(report['binding']['revision'])+' · exact exclusive ranges; derived identity, not creative acceptance.')
                    if self.export_record and (report.get('validation') or {}).get('unchanged_dependencies') and report['certificate']['origin']==self.export_record['certificate']['origin']:
                        self.export_record.update(validation=deepcopy(report['validation']),validation_context=context,validation_refs=refs)
            except CancelledError:self.failed_context();self.status.setText('Cancelled before read submission; no edit or output started.')
            except Exception as exc:self.failed_context();self.status.setText('Failed · '+str(exc)+'. No edit or automatic retry.')
        if self.report_context and self.report_context!=self.context() and self.failure_context!=self.context() and self.future is None and self.desired is None:self.status.setText('Outdated · retained revision '+str(self.report['binding']['revision'])+' report. Explicit validation recomputes dependencies; fresh inspection creates new provenance.')
        if self.future is None and self.desired is not None:
            desired=self.desired;self.desired=None
            if desired[1]!=self.context():self.status.setText('Outdated intent discarded before submission.');return
            self.intent=desired
            try:self.future=self.submit_query(desired[2])
            except Exception as exc:self.failed_context();self.status.setText('Failed to submit · '+str(exc)+'. No edit or retry.')
        current=self.report is not None and self.report_context==self.context() and self.future is None and self.desired is None
        uses=self.report['duplicate_use'] if self.report is not None else None
        self.previous_page.setEnabled(bool(current and uses['offset']>0));self.next_page.setEnabled(bool(current and uses['next_offset'] is not None))
        if uses:self.page_label.setText('Uses '+str(uses['offset']+1 if uses['rows'] else 0)+'–'+str(uses['offset']+len(uses['rows']))+' of '+str(uses['total'])+' · '+str(max(0,uses['total']-uses['offset']-len(uses['rows'])))+' later uses. '+('Retained/outdated.' if not current else ''))
        if self.export_record:
            self.sample_reply();key=self.export_record['id'];published=next((o for o in state.get('operations',[]) if o['id']==key),None)
            if published:self.export_record['outcome']=deepcopy(published);self.export_record.pop('lookup_error',None)
            outcome=self.export_record.get('outcome');certificate=self.export_record['certificate'];current=self.context();original=self.export_record.get('validation_context',self.export_record['context'])
            if outcome:
                status=outcome['status'];suffix=' · Outdated after later edits/context change' if current!=original else ''
                if status=='exported':self.export_status.setText('Exported original revision '+str(certificate['binding']['revision'])+' '+str(certificate['query']['range'])+suffix+(' · dependencies explicitly validated at revision '+str(self.export_record['validation']['validated_binding']['revision']) if self.export_record.get('validation') and not suffix else '')+' · '+str(outcome.get('result',{}).get('path','')))
                elif status in ('failed','rejected'):self.export_status.setText('Sample '+status+' · '+outcome.get('error',{}).get('message','Retain/reconcile prior output')+'. Accepted work and prior output retained; retry requires explicit new intent after terminal failure.')
                else:self.export_status.setText('Sample '+status+' · frozen revision '+str(certificate['binding']['revision'])+suffix+(' · last observed state; use Check sample for its SAME-ID outcome.' if published is None else ' · cancel this exact sample if needed; no duplicate submission.'))
            if self.export_record.get('lookup_error'):self.export_status.setText(self.export_record['lookup_error']+' Original destination: '+str(self.export_record['path']))
    def close_resources(self):self.closed=True;self.cancel()
    def exited(self):return (self.future is None or self.future.done()) and (self.sample_future is None or self.sample_future.done()) and all(f.done() for f in self.cancel_futures)
