"""Fractional model/ACK and native hidden-Tk virtual-navigation regression.

No foreground window, focus grab, GPU or real capture. Hardware key trial remains
separate from this native Tcl/Tk event-dispatch evidence.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from decimal import Decimal
import tkinter as tk
from tkinter import ttk
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from slider_keyboard import SliderKeyboard
from starfield_tuning import StarfieldTuningWindow
from star_tuning_profiles import SHIPPED
from spectrum_tuning_test import fft_frame
from spectrum_widget import SpectrumFeed
from band_attack_tuning import BandAttackTuning
from low_band_attack import LowBandAttack

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    root=tk.Tk();root.withdraw()
    try:
        default=ttk.Scale(root,from_=0,to=2,variable=tk.DoubleVar(value=1.9))
        default.event_generate('<<PrevChar>>');assert np.isclose(default.get(),.9)
        default.destroy()
        submissions=[];backend=BandAttackTuning(authored=SHIPPED);detector=LowBandAttack()
        def submit(c,author=None):submissions.append(deepcopy(c));backend.submit(len(submissions),c,author);return len(submissions)
        store=SimpleNamespace(authored=SHIPPED,error=None)
        view=StarfieldTuningWindow(root,submit,lambda enabled:None,store=store);view.window.withdraw()
        frame,_=fft_frame();frame.spectrum_magnitudes[:]=20.
        feed=SpectrumFeed();feed.enable(True);feed.observe(frame,2048)
        def acknowledge():
            level,sensitivity,summary=backend.apply(frame,20.,detector,'same')
            payload=detector.process(level,2048,'same',sensitivity);backend.completed(payload,summary)
            p=dict(backend.latest,version=1,pilot_active=True,analysis_age_seconds=0.,spectrum=feed.snapshot())
            view.refresh((p,time.perf_counter()),True);return p
        acknowledge();root.update_idletasks()
        for index,key,value in ((2,'weight',1.9),(3,'sensitivity',1.73456789)):
            view.vars[key].set(value);view.enabled.set(True)
            view.sliders[index].event_generate('<<NextChar>>')
            expected=float(Decimal(str(value))+Decimal('.01'))
            assert np.isclose(view.vars[key].get(),expected,rtol=0,atol=1e-12)
            assert view.labels[key].get().startswith(f'{expected:.2f}')
            view.sliders[index].event_generate('<<NextChar>>') # duplicate OS/virtual route must not double-step
            assert np.isclose(view.vars[key].get(),expected,rtol=0,atol=1e-12)
            view.keyboard.release('Right')
            if view.pending is not None:view.window.after_cancel(view.pending);view.pending=None
            view.send();p=acknowledge()
            assert p['effective'][key]==expected and submissions[-1][key]==expected
            assert view.vars[key].get()==expected and view.labels[key].get().startswith(f'{expected:.2f}')
        # A mouse-selected fractional starting value is retained, not snapped to a step grid.
        slider=view.sliders[2];var=view.vars['weight'];start=1.234567891234
        var.set(start)
        for _ in range(200):
            slider.event_generate('<<NextChar>>');view.keyboard.release('Right')
            slider.event_generate('<<PrevChar>>');view.keyboard.release('Left')
        assert np.isclose(var.get(),start,rtol=0,atol=1e-12)
        var.set(1.9995);slider.event_generate('<<NextChar>>');view.keyboard.release('Right');assert var.get()==2.
        var.set(.0005);slider.event_generate('<<PrevChar>>');view.keyboard.release('Left');assert var.get()==0.
        # Virtual up/down parks focus only and skips the disabled slider.
        view.sliders[1].configure(state='disabled');focus=[]
        view.sliders[2].focus_set=lambda:focus.append(2)
        before=view.vars['start_hz'].get();view.sliders[0].event_generate('<<NextLine>>')
        assert focus==[2] and view.vars['start_hz'].get()==before
        mouse_bindings={p:root.bind_class('TScale',p) for p in ('<ButtonPress-1>','<B1-Motion>','<ButtonRelease-1>')}
        assert all(mouse_bindings.values()) and not slider.bind('<B1-Motion>') and not slider.bind('<Tab>')
        view.keyboard.press(2,'Right');slider.event_generate('<FocusOut>');assert view.keyboard.timer is None
        view.close()
        result=dict(evidence_class='Native hidden Tk virtual-event dispatch + actual Starfield model/display/analysis ACK; no hardware keys/GPU/device',
            tk_version=root.tk.call('info','patchlevel'),rootcause='TScale virtual navigation class handler increments +/-1; previously unowned virtual route',
            reproduced_old_default_jump=True,native_fractional_weight_and_sensitivity=True,model_display_ACK_agree=True,
            fractional_start_preserved=True,roundtrips=200,drift_tolerance=1e-12,bounds_clamped=True,
            duplicate_press_suppressed=True,Up_Down_focus_only_disabled_skip=True,mouse_and_Tab_class_bindings_preserved=True,
            focusloss_cancel=True,hardware_trial_pending=True)
    finally:root.destroy()
    if args.output:args.output.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2));print('Slider decimal native/CPU checks PASS')

if __name__=='__main__':main()
