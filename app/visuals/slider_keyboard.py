"""Reusable bounded keyboard navigation for one ordered slider group."""
import time
from decimal import Decimal

class SliderKeyboard:
    INITIAL_MS=300
    REPEAT_MS=80
    MAX_MULTIPLIER=4

    def __init__(self,owner,clock=time.perf_counter,focus_changed=lambda index:None):
        self.owner=owner;self.clock=clock;self.focus_changed=focus_changed
        self.entries=[];self.timer=None;self.held=None;self.started=None;self.closed=False

    def add(self,slider,variable,low,high,step,changed):
        if step<=0:raise ValueError('Slider step must be positive')
        index=len(self.entries);self.entries.append((slider,variable,low,high,step,changed))
        slider.configure(takefocus=True)
        slider.bind('<ButtonPress-1>',lambda event,s=slider:s.focus_set(),add='+')
        slider.bind('<FocusIn>',lambda event,i=index:self.focus_changed(i),add='+')
        slider.bind('<FocusOut>',lambda event:self.focus_out(),add='+')
        for key in ('Left','Right','Up','Down'):
            slider.bind('<KeyPress-'+key+'>',lambda event,k=key,i=index:self.press(i,k))
            slider.bind('<KeyRelease-'+key+'>',lambda event,k=key:self.release(k))
        # Tk 9 themes/input paths also dispatch navigation as virtual events.
        # Their TScale class bindings use +/-1 (or +/-10), ignoring our step.
        # Own those events on this widget as well; press() suppresses duplicates.
        for event,key in (('PrevChar','Left'),('NextChar','Right'),('PrevLine','Up'),('NextLine','Down'),
                          ('PrevWord','Left'),('NextWord','Right'),('PrevPara','Up'),('NextPara','Down')):
            slider.bind('<<'+event+'>>',lambda event,k=key,i=index:self.press(i,k))

    def enabled(self,index):return not self.entries[index][0].instate(['disabled'])

    def focus_out(self):self.stop();self.focus_changed(None)

    def press(self,index,key):
        if self.closed or not self.enabled(index):return 'break'
        if key in ('Up','Down'):
            self.stop();direction=-1 if key=='Up' else 1
            for offset in range(1,len(self.entries)+1):
                other=(index+direction*offset)%len(self.entries)
                if self.enabled(other):self.entries[other][0].focus_set();break
            return 'break'
        if self.held==(index,key):return 'break' # Ignore OS autorepeat; one bounded timer owns repeats.
        self.stop();self.held=(index,key);self.started=self.clock()
        self.adjust(index,key,1);self.timer=self.owner.after(self.INITIAL_MS,self.repeat)
        return 'break'

    def adjust(self,index,key,multiplier):
        slider,var,low,high,step,changed=self.entries[index]
        value=float(max(Decimal(str(low)),min(Decimal(str(high)),
            Decimal(str(var.get()))+(-1 if key=='Left' else 1)*Decimal(str(step))*multiplier)))
        if value!=var.get():var.set(value);changed()

    def repeat(self):
        self.timer=None
        if self.closed or self.held is None:return
        index,key=self.held
        if not self.enabled(index) or self.owner.focus_get()!=self.entries[index][0]:self.stop();return
        elapsed=self.clock()-self.started
        multiplier=1 if elapsed<1. else 2 if elapsed<2. else self.MAX_MULTIPLIER
        self.adjust(index,key,multiplier);self.timer=self.owner.after(self.REPEAT_MS,self.repeat)

    def release(self,key):
        if self.held is not None and self.held[1]==key:self.stop()
        return 'break'

    def stop(self):
        if self.timer is not None:self.owner.after_cancel(self.timer);self.timer=None
        self.held=None;self.started=None

    def close(self):self.stop();self.closed=True
