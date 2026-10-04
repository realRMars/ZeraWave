"""Standalone profiles/authored routing and inert keyboard UI checks. CPU only."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app/audio'))
from band_attack_tuning import BandAttackTuning,WINDOW_BASELINE,BASELINE,weighted,curve_weights
from low_band_attack import LowBandAttack
from star_tuning_profiles import (SHIPPED,TARGET,StarProfileStore,document,atomic_write,
    read_document,validate_document,settings_from)
from starfield_tuning import StarfieldTuningWindow,TARGETS,configure,decode
from slider_keyboard import SliderKeyboard
from spectrum_tuning_test import Widget,Var,fft_frame
from spectrum_widget import SpectrumFeed,frequencies
from studio_color_link import ColorLink,ColorInbox
from starfield_tuning_test import live_owner_checks

def rejects(fn):
    try:fn()
    except (ValueError,OSError,UnicodeError):return
    raise AssertionError('Invalid operation accepted')

def store_for(folder):
    path=folder/'authored.json';atomic_write(path,document(SHIPPED,'Authored','authored'))
    return StarProfileStore(path,folder/'profiles')

def storage_checks(folder):
    store=store_for(folder);frame,_=fft_frame();bins=frame.spectrum_frequencies.tolist()
    assert store.authored==SHIPPED
    original=store.authored_path.read_bytes()
    c=dict(SHIPPED,start_hz=60.,end_hz=100.,weight=2.,sensitivity=1.25)
    path=store.save_profile('Picked bass',c,bins)
    name,loaded=store.load_profile(path,bins);assert name=='Picked bass' and loaded==c
    assert store.authored_path.read_bytes()==original and store.authored==SHIPPED
    assert StarProfileStore(store.authored_path,store.profile_dir).authored==SHIPPED
    rejects(lambda:store.load_profile(store.authored_path,bins))
    rejects(lambda:store.save_profile('empty',dict(c,start_hz=141.,end_hz=142.),bins))
    rejects(lambda:store.save_profile('bad',dict(BASELINE,body_weight=.5),bins))
    rejects(lambda:store.load_profile(path,None))
    good=read_document(path,'profile',bins);bad_cases=[]
    for fields in ({'version':4},{'version':True},{'target':'planet.moon.1'},
                   {'kind':'authored'},{'name':''},{'name':' bad '},{'extra':1}):bad_cases.append(dict(good,**fields))
    for key,value in [('start_hz',float('nan')),('end_hz',316),('weight',-1),('sensitivity',True),
                      ('weight','1.5'),('start_hz',100),('start_hz',141)]:
        values=dict(good['values'],**{key:value})
        if key=='start_hz' and value==141:values['end_hz']=142
        bad_cases.append(dict(good,values=values))
    for value in bad_cases:
        rejects(lambda v=value:validate_document(v,'profile',bins))
        assert store.authored==SHIPPED and store.authored_path.read_bytes()==original
    malformed=folder/'malformed.json'
    for raw in ('{','{}','[]','{"version":1,"version":1}','x'*16385):
        malformed.write_text(raw);rejects(lambda:store.load_profile(malformed,bins))
    new=store.save_authored(c,bins);assert new==c
    relaunched=StarProfileStore(store.authored_path,store.profile_dir);assert relaunched.authored==c
    renderer=SimpleNamespace(debug_state=5,debug_sequence=(),transition_sequence=False,transition_settings={},
        planet_star_attack_pilot=True,planet_star_attack_eligible=lambda:True)
    with patch('starfield_tuning.StarProfileStore',return_value=relaunched):configure(renderer,SimpleNamespace())
    assert renderer.star_tuning.authored==c and renderer.star_tuning.settings==dict(c,enabled=False)
    persisted=store.authored_path.read_bytes()
    with patch('star_tuning_profiles.os.replace',side_effect=OSError('injected atomic replace failure')):
        rejects(lambda:store.save_authored(SHIPPED,bins))
        rejects(lambda:store.save_profile('write fails',SHIPPED,bins))
    assert store.authored_path.read_bytes()==persisted and store.authored==c
    assert not list(folder.rglob('*.tmp'))
    store.authored_path.write_text('{bad')
    rejects(store.reload_authored);assert store.authored==c
    invalid_start=StarProfileStore(store.authored_path,store.profile_dir)
    assert invalid_start.authored==SHIPPED and invalid_start.error and store.authored_path.read_text()=='{bad'
    atomic_write(store.authored_path,document(dict(c,start_hz=141.,end_hz=142.),'Authored','authored'))
    empty_start=StarProfileStore(store.authored_path,store.profile_dir)
    assert empty_start.error and empty_start.authored==SHIPPED
    atomic_write(store.authored_path,document(c,'Authored','authored'))
    return dict(roundtrip=True,custom_cannot_promote=True,author_save_relaunch=True,
        malformed_rejected=len(bad_cases)+5,actual_empty_bins_rejected=True,
        atomic_failure_prior_bytes_and_cache_preserved=True,temporary_files_cleaned=True,
        invalid_startup_explicit_fallback_no_rewrite=True,startup_empty_fullblock_bins_rejected=True)

def routing_checks():
    frame,_=fft_frame();frame.spectrum_magnitudes[:]=20.;detector=LowBandAttack()
    tune=BandAttackTuning(authored=SHIPPED)
    assert tune.settings==dict(SHIPPED,enabled=False)
    def process():
        level,sens,summary=tune.apply(frame,20.,detector,'A')
        result=detector.process(level,2048,'A',sens);tune.completed(result,summary)
        return level,sens,result,summary
    level,sens,p,summary=process();assert level==6. and sens==2.
    assert np.flatnonzero(curve_weights(frame.spectrum_frequencies,tune.settings,tune.authored)).tolist()==[4,5]
    c=dict(WINDOW_BASELINE,start_hz=60.,end_hz=100.,weight=2.,sensitivity=1.25)
    assert tune.submit(1,c);level,sens,p,summary=process();assert level==8. and p['bass_attack']==0.
    assert tune.submit(2,dict(c,enabled=False));level,sens,p,_=process()
    assert level==6. and sens==2. and tune.settings==dict(SHIPPED,enabled=False) and p['bass_attack']==0.
    tune.submit(3,WINDOW_BASELINE);level,sens,p,_=process();assert level==20. and sens==1. and p['bass_attack']==0.
    new=dict(SHIPPED,start_hz=60.,end_hz=100.,weight=1.2,sensitivity=1.1)
    tune.submit(4,dict(new,enabled=False),new);level,sens,p,_=process()
    assert level==4.8 and sens==1.1 and tune.authored==new and p['bass_attack']==0.
    before=(deepcopy(tune.settings),deepcopy(tune.authored),tune.revision)
    assert not tune.submit(5,c,dict(new,start_hz=141.,end_hz=142.))
    process();assert (tune.settings,tune.authored,tune.revision)==before
    assert np.isclose(p['sample_seconds'],5*2048/48000.) and np.isclose(detector.seconds,6*2048/48000.)
    ack=tune.status(0,123.);assert ack['authored']==new and ack['effective']==new
    assert decode(json.dumps(dict(ack,version=1,pilot_active=True)))
    # The delivered FFT layout can change after submission (e.g. replay tail).
    # Reject the whole authored update even when its live comparison is valid.
    edge=BandAttackTuning(authored=WINDOW_BASELINE)
    edge.apply(frame,20.,LowBandAttack(),'A');edge.submit(1,WINDOW_BASELINE,SHIPPED)
    short=SimpleNamespace(spectrum_frequencies=np.array([0.,24000.]),spectrum_magnitudes=np.zeros(2))
    edge.apply(short,0.,LowBandAttack(),'A')
    assert edge.rejected_revision==1 and edge.revision==0 and edge.authored==WINDOW_BASELINE
    # Existing bounded pipe slots, including authored promotion coalesced with a later edit.
    link=ColorLink.__new__(ColorLink);link.condition=threading.Condition();link.closed=False;link.star_tuning_revision=0
    link.submit_star_tuning(new,new);link.submit_star_tuning(c)
    assert link.pending_star_tuning['authored']==new
    inbox=ColorInbox.__new__(ColorInbox);inbox.lock=threading.Lock();inbox.closed=False
    inbox.pending_star_tuning=None;inbox.star_tuning_revision=-1
    inbox.accept(json.dumps(link.pending_star_tuning).encode());update=inbox.take_star_tuning()
    assert update==(2,c,new)
    live=BandAttackTuning(authored=SHIPPED);live.submit(*update);live.apply(frame,20.,LowBandAttack(),'A')
    assert live.authored==new and live.settings==c
    live.submit(3,dict(c,enabled=False));assert live.apply(frame,20.,LowBandAttack(),'A')[:2]==(4.8,1.1)
    # Actual configure, pilot ON/OFF, held-world eligibility and startup authored read.
    for active in (True,False):
        renderer=SimpleNamespace(debug_state=5,debug_sequence=(),transition_sequence=False,transition_settings={},
            planet_star_attack_pilot=active,planet_star_attack_eligible=lambda:active)
        analyzer=SimpleNamespace();configure(renderer,analyzer)
        assert renderer.star_tuning.authored==SHIPPED and not renderer.star_tuning.settings['enabled']
        assert hasattr(analyzer,'_planet_star_tuning')==active
    other=SimpleNamespace(debug_state=25,debug_sequence=(),transition_sequence=False,transition_settings={})
    configure(other,SimpleNamespace());assert not hasattr(other,'star_tuning')
    return dict(new_startup_level=6.,new_startup_sensitivity=2.,actual_bins_hz=[93.75,117.1875],
        OFF_discards_temporary_values=True,old_comparison_exact=True,author_ACK_live_update=True,
        no_knob_attack_or_clock_reset=True,invalid_author_no_partial_apply=True,changed_FFT_layout_rechecks_author=True,
        author_update_survives_coalescing=True,actual_configure_held_only=True)

def install_widgets():
    tk=ModuleType('tkinter');ttk=ModuleType('tkinter.ttk');tk.ttk=ttk
    for name in ('Toplevel','Canvas'):setattr(tk,name,Widget)
    for name in ('StringVar','DoubleVar','BooleanVar'):setattr(tk,name,Var)
    for name in ('Frame','LabelFrame','Scrollbar','Label','Checkbutton','Scale','Button','Combobox','Entry'):setattr(ttk,name,Widget)
    saved={k:sys.modules.get(k) for k in ('tkinter','tkinter.ttk')}
    sys.modules['tkinter']=tk;sys.modules['tkinter.ttk']=ttk;return saved

def restore_widgets(saved):
    for key,value in saved.items():
        if value is None:sys.modules.pop(key,None)
        else:sys.modules[key]=value
    Widget.all.clear();Widget.focused=None

def fire(owner,identifier):
    _,callback=owner.timers.pop(identifier);callback()

def view_checks(folder):
    saved=install_widgets()
    try:
        store=store_for(folder);submitted=[]
        def submit(c,authored=None):submitted.append((deepcopy(c),deepcopy(authored)));return len(submitted)
        v=StarfieldTuningWindow(Widget(),submit,lambda on:None,store=store)
        assert v.settings()==dict(SHIPPED,enabled=False)
        frame,_=fft_frame();feed=SpectrumFeed();feed.enable(True);feed.observe(frame,2048);s=feed.snapshot()
        p=dict(version=1,pilot_active=True,revision=0,settings=dict(SHIPPED,enabled=False),effective=SHIPPED,
            authored=SHIPPED,state='authored baseline',analysis_age_seconds=0.,spectrum=s)
        def ack(c,author=None):
            p.update(revision=len(submitted),settings=c,effective=dict(c,enabled=True) if c['enabled'] else author or v.authored,
                authored=author or v.authored)
            s['observed_wall']=time.perf_counter();v.refresh((p,time.perf_counter()),True)
        ack(dict(SHIPPED,enabled=False));assert sum(v.spectrum.weights)==3.
        assert '93.7500' in v.selection.get() and '117.1875' in v.selection.get()
        # Keyboard uses the same coalesced ACK route as mouse changes.
        v.sliders[0].bindings['<ButtonPress-1>'](None);assert v.focus_labels[0][0].get().startswith('> ')
        assert v.sliders[0].bindings['<KeyPress-Right>'](None)=='break'
        v.sliders[0].bindings['<KeyRelease-Right>'](None)
        assert v.vars['start_hz'].get()==81. and v.enabled.get() and v.keyboard.timer is None
        fire(v.window,v.pending);assert submitted[-1][0]['start_hz']==81.;ack(*submitted[-1])
        before=list(v.spectrum.weights);v.vars['weight'].set(1.75);v.changed('weight')
        v.refresh((p,time.perf_counter()),True);assert list(v.spectrum.weights)==before
        rejects(v.ack_settings);fire(v.window,v.pending);ack(*submitted[-1])
        original=store.authored_path.read_bytes();v.profile_name.set('Trial');v.save_profile()
        assert store.authored_path.read_bytes()==original and 'Saved named' in v.profile_status.get()
        path=next(store.profile_dir.glob('*.json'))
        v.reset();fire(v.window,v.pending);ack(*submitted[-1]);assert v.settings()==dict(SHIPPED,enabled=False)
        assert v.load_profile(path);ack(*submitted[-1]);assert v.vars['weight'].get()==1.75
        assert store.authored_path.read_bytes()==original
        assert v.save_authored();author=submitted[-1][1];assert author['weight']==1.75
        assert 'saved atomically' in v.profile_status.get();ack(*submitted[-1])
        assert 'acknowledged by the running preview' in v.profile_status.get()
        persisted=store.authored_path.read_bytes()
        before_count=len(submitted)
        with patch('star_tuning_profiles.os.replace',side_effect=OSError('injected failure')):
            assert not v.save_authored()
        assert len(submitted)==before_count
        assert store.authored_path.read_bytes()==persisted and 'prior baseline retained' in v.profile_status.get()
        # Newly implemented choices need their render ACK; no false Star curve.
        count=len(submitted);sliders=list(v.sliders)
        for target in TARGETS[2:]:
            v.target_var.set(target.label);v.select_target()
            assert v.sliders==sliders and all(w.kw['state']=='disabled' for w in v.sliders+v.action_buttons)
            assert sum(v.spectrum.weights)==0. and 'restart preview' in v.status.get()
        assert len(submitted)==count
        assert len(TARGETS)==24 and len({t.target_id for t in TARGETS})==24
        assert not any('moon.1' in t.target_id or t.target_id.endswith('moon_bodies') for t in TARGETS)
        v.target_var.set(TARGETS[0].label);v.select_target();assert sum(v.spectrum.weights)==3.5
        # Empty selections / malformed profile files cannot partially change live state.
        bad=folder/'bad.json';bad.write_text('{broken');before=v.settings();assert not v.load_profile(bad)
        assert v.settings()==before and len(submitted)==count
        v.old_comparison();fire(v.window,v.pending)
        assert submitted[-1][0]==dict(SHIPPED,**WINDOW_BASELINE);ack(*submitted[-1])
        v.preview_started();assert v.settings()==dict(author,enabled=False) and v.spectrum.packet is None
        v.close();assert v.keyboard.closed and v.keyboard.timer is None
        return dict(actual_constructor_and_callbacks=True,ACK_curve_agrees_with_digital_and_bins=True,
            profile_Save_Load_separate_from_authored=True,author_save_ACK_route=True,write_failure_honest=True,
            selector_count=24,editable_count=24,missing_ACK_count=22,no_fake_moon_routes=True,
            no_duplicate_slider_sets=True,unavailable_selection_no_submit=True,old_comparison_accessible=True,
            preview_relaunch_clears_live=True,native_trial_pending=True)
    finally:restore_widgets(saved)

def keyboard_checks():
    owner=Widget();clock=[0.];changed=[];focus=[];helper=SliderKeyboard(owner,clock=lambda:clock[0],focus_changed=focus.append)
    sliders=[Widget(state='normal'),Widget(state='disabled'),Widget(state='normal')]
    vars=[Var(5.),Var(5.),Var(5.)]
    for i,(slider,var) in enumerate(zip(sliders,vars)):
        helper.add(slider,var,0.,10.,.1,lambda i=i:changed.append(i))
    sliders[0].bindings['<ButtonPress-1>'](None);assert Widget.focused==sliders[0] and focus[-1]==0
    helper.press(0,'Right');assert vars[0].get()==5.1
    helper.press(0,'Right');assert vars[0].get()==5.1 and len(owner.timers)==1
    helper.release('Right');assert not owner.timers and helper.held is None
    helper.press(0,'Down');assert Widget.focused==sliders[2] and vars[2].get()==5.
    helper.press(2,'Up');assert Widget.focused==sliders[0] and len(changed)==1
    assert not any('Tab' in key for s in sliders for key in s.bindings)
    helper.press(0,'Left');assert vars[0].get()==5.
    for elapsed,increment in ((.3,.1),(1.1,.2),(2.1,.4),(10.,.4)):
        clock[0]=elapsed;before=vars[0].get();fire(owner,helper.timer)
        assert np.isclose(before-vars[0].get(),increment) and len(owner.timers)==1
    helper.release('Left');before=vars[0].get();assert not owner.timers
    assert vars[0].get()==before
    vars[0].set(9.95);helper.press(0,'Right');assert vars[0].get()==10.
    clock[0]+=3.;fire(owner,helper.timer);assert vars[0].get()==10.
    sliders[2].focus_set();assert helper.timer is None and not owner.timers
    helper.press(2,'Right');sliders[2].configure(state='disabled');fire(owner,helper.timer)
    assert helper.timer is None and not owner.timers
    sliders[0].focus_set();helper.press(0,'Left');helper.close();assert not owner.timers
    assert helper.press(0,'Right')=='break' and vars[0].get()==9.9
    Widget.all.clear();Widget.focused=None
    return dict(tap_one_increment=True,OS_repeat_suppressed=True,repeat_caps_at_4=True,
        bounds_clamped=True,disabled_skipped=True,Up_Down_focus_only=True,mouse_focus_marker=True,
        Tab_preserved=True,release_focusloss_disable_close_cancel_timer=True,postrelease_value_updates=0,
        text_fields_and_combobox_not_bound=True,evidence='Actual bindings/callbacks on inert widgets; no native Tk')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='zerawave-star-profiles-') as temp:
        folder=Path(temp);(folder/'storage').mkdir();(folder/'view').mkdir()
        result=dict(classification='CPU synthetic, filesystem, inert Tk; exact live owner uses mocked capture/graphics',
            storage=storage_checks(folder/'storage'),routing=routing_checks(),keyboard=keyboard_checks(),view=view_checks(folder/'view'))
    c=dict(SHIPPED,weight=1.25)
    result['live_owner']=live_owner_checks([c,(c,c),dict(c,enabled=False),WINDOW_BASELINE])
    result['pilot_OFF_owner']=live_owner_checks(star_enabled=False)
    assert not any(n in sys.modules for n in ('glfw','moderngl','soundcard','tkinter','capture'))
    if args.output:args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));print('Star profiles CPU checks PASS')

if __name__=='__main__':main()
