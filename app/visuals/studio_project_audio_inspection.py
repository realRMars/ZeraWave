"""Compact read-only Inspector/Mixer projection of the same owner query as CLI."""
from copy import deepcopy
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit
EMPTY_DOCUMENT={}
EMPTY_MEDIA={}

class AudioInspection(QWidget):
    def __init__(self, workspace):
        super().__init__(); self.w=workspace; self.future=None; self.intent=None; self.desired=None; self.report=None; self.report_context=None; self.serial=0; self.context_cache=None; self.context_refs=None
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        row=QHBoxLayout(); layout.addLayout(row)
        for title, mode in [('At playhead','frame'),('Marked range','range')]:
            button=QPushButton(title); button.clicked.connect(lambda checked=False,m=mode:self.request(m)); row.addWidget(button)
        self.status=QLabel('Gain and coverage for selected clips, or all audio. Inspect the playhead or marked range.'); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.details=QPlainTextEdit(); self.details.setReadOnly(True); self.details.setAccessibleName('Bound audio contribution and coverage report'); self.details.setMaximumHeight(220); self.details.hide(); layout.addWidget(self.details)
    def context(self, mode):
        state=self.w.state(); clock=self.w.transport_state(); canvas=self.w.timeline.canvas; document=state.get('document') or EMPTY_DOCUMENT
        media=state.get('media') or EMPTY_MEDIA
        # StateSections replaces detached document/media values on publication.
        # Retain their references: identity cannot recycle while this cache lives.
        # No track/clip walk or validation hash on ordinary clock-only/idle pulses.
        key=(state.get('epoch'),state.get('revision'),id(document),id(media),tuple(sorted(canvas.selection)))
        if self.context_cache is None or self.context_cache[0]!=key:
            audio_tracks={t['id'] for t in document.get('tracks',[]) if t['kind']=='audio'}
            selected=tuple(sorted(c['id'] for c in document.get('clips',[]) if c['id'] in canvas.selection and c['track'] in audio_tracks))
            from project_audio_inspection import availability_key
            validation=availability_key(document,media,selected)
            self.context_cache=(key,selected,validation);self.context_refs=(document,media)
        _,selected,validation=self.context_cache
        where=clock.get('range',[clock.get('range_in',0),clock.get('range_out',0)]) if mode=='range' else clock.get('frame',0)
        return (state.get('epoch'),state.get('revision'),document.get('id'),selected,mode,tuple(where) if isinstance(where,list) else where,validation)
    def request(self, mode):
        context=self.context(mode); query=dict(op='audio_inspect',**self.w.binding())
        if mode=='frame': query['frame']=context[5]
        else: query['range']=list(context[5])
        if context[3]:
            query['clips']=list(context[3]);query['tracks']=sorted({c['track'] for c in self.w.document()['clips'] if c['id'] in context[3]})
        self.serial+=1; self.desired=(self.serial,context,query); self.status.setText('Calculating the bound audio chain…'); self.poll()
    def submit_query(self, query):
        # Two widgets each retain at most one query; share the existing API's
        # four-client gate and Shell pool, leaving ordered authoring unblocked.
        from project_api import call
        endpoint=self.w.state().get('endpoint')
        if not endpoint:raise ValueError('Owner endpoint unavailable; wait for project state.')
        return self.w.shell.operations.submit(call,endpoint,query)
    def poll(self):
        if self.future is not None and self.future.done():
            future=self.future; serial,context,query=self.intent; self.future=None
            try:
                reply=future.result()
                if serial!=self.serial or context!=self.context(context[4]):
                    self.status.setText('Outdated inspection discarded; project, source verification, selection or requested position changed. Inspect deliberately again.')
                elif not reply.get('ok'):
                    self.status.setText('Inspection unavailable: '+reply.get('error',{}).get('message','Owner query failed.'))
                else:
                    report=reply['report']
                    if (report['epoch'],report['revision'],report['project'])!=context[:3] or report['availability_sha256']!=context[6]: raise ValueError('Owner returned a different inspection or source-verification binding; inspect again.')
                    from project_audio_inspection import describe
                    self.report=deepcopy(report); self.report_context=context; self.details.setPlainText(describe(report)); self.details.show(); self.status.setText('Ready · bound revision '+str(report['revision'])+' · derived levels, not measured dBFS.')
            except Exception as exc: self.status.setText('Inspection failed: '+str(exc)+'. No document edit or automatic retry.')
        if self.report_context and self.report_context!=self.context(self.report_context[4]):
            self.status.setText('Outdated · retained report belongs to revision '+str(self.report['revision'])+' and its original source verification, position/selection. Inspect again. No automatic retargeting.')
        if self.future is None and self.desired is not None:
            desired=self.desired; self.desired=None
            if desired[1]!=self.context(desired[1][4]): self.status.setText('Inspection intent became outdated before submission. Inspect again.'); return
            self.intent=desired
            try:self.future=self.submit_query(desired[2])
            except Exception as exc:self.status.setText('Inspection not submitted: '+str(exc)+'. No edit or automatic retry.')
