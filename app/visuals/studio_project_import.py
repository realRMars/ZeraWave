"""Read-only import progress/details over the existing asynchronous owner API."""
from collections import Counter
from copy import deepcopy
import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QHBoxLayout,QLabel,QPushButton,QDialog,QVBoxLayout,QTreeWidget,QTreeWidgetItem

class ImportStatus(QWidget):
 def __init__(self,w):
  super().__init__();self.w=w;self.operation=None;self.future=None;self.future_id=None;self.next_query=0.;self.outcome=None;self.details=None;self.signature=None
  layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0);self.label=QLabel('Import adds references only.');self.label.setWordWrap(True);layout.addWidget(self.label,1);self.show_button=QPushButton('Details');self.show_button.setEnabled(False);self.show_button.clicked.connect(self.show_details);layout.addWidget(self.show_button);self.cancel_button=QPushButton('Cancel import');self.cancel_button.setEnabled(False);self.cancel_button.clicked.connect(self.cancel);layout.addWidget(self.cancel_button)
 def start(self,operation):
  self.operation=operation;self.outcome=None;self.next_query=0.;self.signature=None;self.label.setText('Preparing import — no references accepted yet.');self.cancel_button.setEnabled(True);self.show_button.setEnabled(False)
  if self.details:self.details.table.clear()
 def cancel(self):
  if self.operation:self.w.client.submit('project',request=dict(op='cancel',operation_id=self.operation));self.label.setText('Cancellation requested; awaiting owner outcome. Accepted references remain.')
 def poll(self):
  if self.future and self.future.done():
   future=self.future;query=self.future_id;self.future=None
   try:
    result=future.result()
    if query==self.operation:
     self.outcome=deepcopy(result.get('outcome'))
     if not self.outcome:self.label.setText('Import outcome unknown. Keep accepted work; reconcile this operation before retrying.');self.next_query=time.perf_counter()+1.
     else:self.refresh()
   except Exception:self.label.setText('Import status unavailable. Accepted references retained; no automatic resubmission.');self.next_query=time.perf_counter()+1.
  if self.operation and self.future is None and (self.outcome or {}).get('status') not in ('accepted','failed','rejected') and time.perf_counter()>=self.next_query:
   self.future_id=self.operation;self.future=self.w.client.submit('project',request=dict(op='operation_status',operation_id=self.operation));self.next_query=time.perf_counter()+.15
 def refresh(self):
  row=self.outcome;files=row.get('files',[]);status=row['status'];values=Counter(r['status'] for r in files);self.show_button.setEnabled(bool(files));self.cancel_button.setEnabled(status=='preparing')
  if status=='accepted':text=f"Import complete: {values['accepted']} added, {values['reused']} reused, {values['skipped']} duplicates skipped. No clips placed."
  elif status in ('failed','rejected'):text='No new references accepted from this group. '+row.get('error',{}).get('message','Import failed.')
  else:text=f"Preparing {sum(r['status'] not in ('queued','preparing') for r in files)}/{len(files)} — no new references accepted yet."
  self.label.setText(text);signature=repr(files)
  if self.details and signature!=self.signature:
   table=self.details.table;table.clear()
   for r in files:table.addTopLevelItem(QTreeWidgetItem([r['path'],r['status'],r.get('asset_id',''),r.get('error','')]))
  self.signature=signature
 def show_details(self):
  if self.details:self.details.raise_();return
  dialog=QDialog(self);dialog.setAttribute(Qt.WA_DeleteOnClose);dialog.setWindowTitle('Project import outcomes');dialog.resize(820,360);layout=QVBoxLayout(dialog);note=QLabel('One atomic import group. Verified preparation is not acceptance; failed/cancelled groups retain existing references.');note.setWordWrap(True);layout.addWidget(note);dialog.table=QTreeWidget();dialog.table.setHeaderLabels(['File','Outcome','Stable reference','Detail']);layout.addWidget(dialog.table);dialog.finished.connect(lambda *_:setattr(self,'details',None));self.details=dialog;self.signature=None
  if self.outcome:self.refresh()
  dialog.show()
