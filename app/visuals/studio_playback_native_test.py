"""Actual withdrawn Studio controls and shortcut callbacks; no child or capture."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
from studio import Studio


def run():
    root=tk.Tk();root.withdraw()
    studio=Studio(root);commands=[];actions=[]
    studio.start=lambda:actions.append('start')
    studio.save=lambda *a:actions.append('save')
    studio.stop=lambda:actions.append('stop')
    latest=[dict(ready=True,running=True,paused=False,held=False,can_bonk=True),0.]
    import time
    latest[1]=time.perf_counter()
    studio.color_link=SimpleNamespace(submit_control=lambda op,**v:commands.append((op,v)),get_preview=lambda:tuple(latest))
    try:
        root.update_idletasks();studio.refresh_playback_controls()
        assert studio.pause_button.instate(['!disabled']) and studio.bonk_button.instate(['!disabled'])
        studio.pause_button.invoke();assert commands[-1]==('pause',{'active':True})
        latest[0]['paused']=True;latest[0]['can_bonk']=False;latest[1]=time.perf_counter()
        studio.refresh_playback_controls();assert studio.pause_button['text']=='Resume' and studio.bonk_button.instate(['disabled'])
        latest[0].update(paused=False,can_bonk=True);latest[1]=time.perf_counter();studio.refresh_playback_controls()
        def event(key,mods=0,widget=None):return SimpleNamespace(keysym=key,state=mods,widget=widget or studio.bonk_button)
        assert studio.playback_key_press(event('space'))=='break'
        assert commands[-1][0]=='bonk'
        count=len(commands);studio.playback_key_press(event('space'));assert len(commands)==count
        studio.playback_key_release(event('space'))
        studio.playback_key_press(event('s',4));studio.playback_key_release(event('s',4))
        studio.playback_key_press(event('S',5));studio.playback_key_release(event('S',5))
        assert actions==['save','stop']
        entry=ttk.Entry(root);scale=ttk.Scale(root)
        before=len(commands)
        assert studio.playback_key_press(event('space',widget=entry)) is None
        assert studio.playback_key_press(event('Left',widget=scale)) is None
        assert len(commands)==before
        assert studio.playback_key_press(event('Shift_L'))=='break'
        assert commands[-1]==('hold',{'owner':'studio.Shift_L','active':True})
        studio.playback_key_release(event('Shift_L'));assert commands[-1][1]['active'] is False
        studio.playback_keys.add('Shift_L');studio.playback_focus_check()
        assert not studio.playback_keys and commands[-1][0]=='release'
        assert studio.bonk_button.bindtags()[0].startswith('ZeraWaveStudioPlayback')
        studio.select(['fractals','bloom']);root.update_idletasks()
        assert studio.selection_scope=='experimental' and studio.selected_states()==['fractal_bloom']
        assert studio.preview_controls.winfo_manager()=='pack'
        assert studio.preview_controls.pack_info()['in']==studio.experimental_controls
        assert studio.experimental_start_button is studio.start_button and studio.experimental_stop_button is studio.stop_button
        studio.select([]);root.update_idletasks()
        assert studio.preview_controls.winfo_manager()=='grid'

        latest[1]-=10.;studio.refresh_playback_controls();assert studio.pause_button.instate(['disabled'])
        print(json.dumps(dict(evidence='Actual withdrawn Tk Studio widgets/bindtags and callbacks; no GPU, foreground or child',
            controls=['Start','Pause/Resume','Stop','Hold','Bonk Normal/Instant'],space_consumed_before_button_class=True,
            OS_repeat_suppressed=True,Ctrl_S='Save session',Ctrl_Shift_S='Stop',text_and_tuning_arrows_preserved=True,
            held_release_focus_and_key=True,stale_status_disables_actions=True),indent=2))
        print('Studio playback native checks PASS')
    finally:
        studio.color_link=None
        root.destroy()


if __name__=='__main__':run()
