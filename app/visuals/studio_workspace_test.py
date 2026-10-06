"""Standalone actual-Tk workspace state, persistence and shortcut checks."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import wave
import tkinter as tk
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
from studio_workspace import Workspace
from studio_panels import clamp_geometry
from window_host import dpi_awareness


def widgets(widget):
    yield widget
    for child in widget.winfo_children():yield from widgets(child)


def run():
    dpi_awareness()
    with tempfile.TemporaryDirectory(prefix='zerawave-workspace-') as directory:
        path=Path(directory)/'layout.json'
        root=tk.Tk();root.withdraw();errors=[]
        root.report_callback_exception=lambda *args:errors.append(str(args[1]))
        app=Workspace(root,path);root.update_idletasks()
        try:
            assert len(app.analyzer.items)==12
            # Genuine tiny PCM fixture: source switches must neither retain a
            # misleading old waveform nor suppress reloading the same file.
            pcm=Path(directory)/'tiny.wav'
            with wave.open(str(pcm),'wb') as output:
                output.setnchannels(1);output.setsampwidth(2);output.setframerate(8000)
                output.writeframes(b'\x00\x00\x00\x40\x00\xc0\x00\x00')
            def load_wave():
                app.waveform.request('Test track',str(pcm))
                deadline=time.perf_counter()+3
                while app.waveform.data is None and time.perf_counter()<deadline:
                    time.sleep(.01);app.waveform.poll()
                assert app.waveform.data and app.waveform.data['duration']==.0005
                assert max(x[1] for x in app.waveform.data['peaks'])==.5
                assert min(x[0] for x in app.waveform.data['peaks'])==-.5
            load_wave();app.waveform.request('Live system audio','');assert app.waveform.data is None
            load_wave();app.waveform.request('Test track',str(Path(directory)/'missing.wav'));assert app.waveform.data is None
            load_wave();app.waveform.request('Synthetic source','');assert app.waveform.data is None
            app.select(['cosmic','galaxy'],show=False)
            editor=app.color_editor;target=editor.target();role=target.slots[0].id
            other=next(t for t in editor.targets if t.scene not in ('shared','galaxy') and t.slots)
            other_role=other.slots[0].id
            editor.target_choice.set(other.label);editor.refresh()
            editor.rows[other_role][0].set('#parked draft')
            editor.target_choice.set(target.label);editor.refresh()
            editor.rows[role][0].set('#current draft');editor.reset_target()
            assert editor.rows[role][0].get()!='#current draft'
            assert editor.drafts[other.id][other_role][0]=='#parked draft'
            editor.reset_scene()
            assert editor.drafts[other.id][other_role][0]=='#parked draft'
            editor.target_choice.set(other.label);editor.refresh()
            assert editor.rows[other_role][0].get()=='#parked draft'
            editor.target_choice.set(target.label);editor.refresh()
            editor.rows[role][0].set('#12')
            tuning=app.star_tuning_window;tuning.profile_name.set('Unsent profile name')
            tuning.pin.set(True);tuning.revision=37;tuning.author_pending=(38,{'test':'retained'})
            identities={k:(id(p.window),p.window.winfo_id(),tuple(str(w) for w in widgets(p.window))) for k,p in app.manager.panels.items()}
            for _ in range(8):
                for key in app.manager.panels:
                    panel=app.manager.panels[key]
                    app.manager.float(key);root.update_idletasks();app.manager.hide(key);app.manager.show(key)
                    app.manager.dock(key,panel.zone);root.update_idletasks()
            assert editor.rows[role][0].get()=='#12'
            assert tuning.profile_name.get()=='Unsent profile name' and tuning.pin.get()
            assert tuning.revision==37 and tuning.author_pending==(38,{'test':'retained'})
            for key,panel in app.manager.panels.items():
                before=identities[key]
                assert before[0:2]==(id(panel.window),panel.window.winfo_id())
                # Each panel retains exactly one native menu after its first
                # float; no per-cycle menu widgets or callbacks accumulate.
                menus=[str(w) for w in panel.window.host.winfo_children() if isinstance(w,tk.Menu)]
                # Tk 9 may list a native menubar clone as the same Python menu
                # twice; count unique widget identities, not those aliases.
                assert len(set(menus))==1,(key,menus)
                assert all(root.nametowidget(w).winfo_exists() for w in before[2])
            app.manager.dock('catalog','left');app.manager.reorder('left',-1)
            app.manager.float('tuning');app.manager.hide('monitor')
            app.manager.save();saved=json.loads(path.read_text(encoding='utf8'))
            assert saved['panels']['tuning']['mode']=='float' and not saved['panels']['monitor']['visible']
            assert not {'colors','layers','state','audio','track'} & saved.keys()
            artistic=app.values()
            artistic=json.dumps(artistic,sort_keys=True)
            app.manager.reset();root.update_idletasks()
            assert json.dumps(app.values(),sort_keys=True)==artistic
            assert tuning.revision==37 and editor.rows[role][0].get()=='#12'
            app.manager.restore(saved);root.update_idletasks()
            assert app.manager.panels['tuning'].mode=='float' and not app.manager.panels['monitor'].visible.get()
            assert clamp_geometry('800x600+99999+99999',[(0,0,1920,1080)])=='800x600+1120+440'
            assert clamp_geometry('700x500-1800+20',[(-1920,0,0,1080),(0,0,1920,1080)])=='700x500-1800+20'
            assert clamp_geometry('invalid',[(0,0,1920,1080)]).startswith('960x720')
            # Same internal callbacks/bindtags as the visible app; these checks
            # do not claim OS keyboard input or GPU playback.
            actions=[];commands=[]
            app.save=lambda *a:actions.append('save');app.stop=lambda:actions.append('stop')
            app.preview_command=lambda op,**values:commands.append((op,values))
            def event(key,widget,state=0):return SimpleNamespace(keysym=key,widget=widget,state=state)
            from tkinter import ttk
            entry=ttk.Entry(root);entry.insert(0,'text with spaces')
            assert app.playback_key_press(event('space',entry)) is None
            assert app.playback_key_press(event('s',entry,4)) is None
            assert app.playback_key_press(event('Right',tuning.sliders[0])) is None
            assert app.playback_key_press(event('space',app.bonk_button)) is None
            assert not actions and not commands
            app.playback_key_press(event('s',app.surface,4));app.playback_key_release(event('s',app.surface,4))
            app.playback_key_press(event('S',app.surface,5));app.playback_key_release(event('S',app.surface,5))
            assert actions==['save','stop']
            app.playback_key_press(event('Shift_L',app.surface));app.workspace_focus_check()
            assert not app.playback_keys and commands[-1][0]=='release'
            assert not errors,errors
            print(json.dumps(dict(evidence='Actual Tk panels/native float hosts; no GPU or OS keyboard injection',
                panels=len(app.manager.panels),cycles_per_panel=8,widget_identity=True,
                unsent_color_and_profile=True,scope_revision_authored_pending=True,
                menus_bounded=True,layout_storage_separate=True,reset_preserves_artistic_session=True,
                visibility_order_float_restore=True,offscreen_and_negative_monitor_clamp=True,
                text_slider_button_shortcuts=True,focus_releases_held_controls=True),indent=2))
            print('Unified Studio native checks PASS')
        finally:
            # Restore the real shutdown method replaced only for shortcut checks.
            app.stop=Workspace.stop.__get__(app,Workspace)
            app.close()
        # Read the actual saved layout into a fresh Tk interpreter/Workspace.
        second_root=tk.Tk();second_root.withdraw();second=Workspace(second_root,path)
        try:
            second_root.update_idletasks()
            assert second.manager.panels['tuning'].mode=='float'
            assert not second.manager.panels['monitor'].visible.get()
            assert second.manager.snapshot()['order']==saved['order']
            print('Fresh Workspace layout restore, scoped draft reset and actual PCM source-switch checks PASS')
        finally:second.close()


if __name__=='__main__':run()
