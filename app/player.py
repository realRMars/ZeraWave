"""Small end-user launcher. The live runner remains the sole audio/render path."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'ZeraWave'


def load_settings(path):
    try:
        value=json.loads(path.read_text(encoding='utf-8'))
        return {'device': value['device']} if isinstance(value,dict) and isinstance(value.get('device'),str) else {'device':''}
    except (OSError,ValueError): return {'device':''}


def save_settings(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2),encoding='utf-8')
    temporary.replace(path)


class Player:
    def __init__(self, root):
        self.root=root; self.process=None; self.log=None
        DATA.mkdir(parents=True,exist_ok=True)
        self.settings=load_settings(DATA/'settings.json')
        root.title('ZeraWave');root.geometry('570x350');root.minsize(500,350)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('.',background='#141a28',foreground='#e3eaf4',font=('Segoe UI',11))
        style.configure('TButton',background='#283951',padding=10)
        style.configure('TCombobox',fieldbackground='#233047',background='#283951')
        style.map('TCombobox',fieldbackground=[('readonly','#233047')],foreground=[('readonly','#e3eaf4')])
        root.configure(background='#141a28')
        root.option_add('*TCombobox*Listbox.background','#233047')
        root.option_add('*TCombobox*Listbox.foreground','#e3eaf4')
        box=ttk.Frame(root,padding=24);box.pack(fill='both',expand=True)
        ttk.Label(box,text='ZeraWave',font=('Segoe UI',25)).pack(anchor='w')
        ttk.Label(box,text='Play music in any app. Let your sound become a world.',wraplength=490).pack(anchor='w',pady=10)
        self.device=tk.StringVar()
        self.devices=ttk.Combobox(box,textvariable=self.device,state='readonly');self.devices.pack(fill='x')
        ttk.Button(box,text='Refresh audio outputs',command=self.refresh).pack(anchor='w',pady=6)
        actions=ttk.Frame(box);actions.pack(fill='x',pady=8)
        self.start_button=ttk.Button(actions,text='Start visuals',command=self.start);self.start_button.pack(side='left')
        self.stop_button=ttk.Button(actions,text='Stop',command=self.stop,state='disabled');self.stop_button.pack(side='left',padx=8)
        ttk.Button(actions,text='Open log',command=lambda: os.startfile(DATA)).pack(side='right')
        self.status=tk.StringVar(value='Ready. Close the visual window to return here.')
        ttk.Label(box,textvariable=self.status,wraplength=490).pack(anchor='w',pady=8)
        self.refresh();root.protocol('WM_DELETE_WINDOW',self.close);root.after(250,self.poll)

    def refresh(self):
        self.options={'System default':''}
        try:
            import soundcard as sc
            for i,speaker in enumerate(sc.all_speakers(),1): self.options[f'{speaker.name} ({i})']=speaker.id
            self.status.set('Ready. Play music through the selected output.')
        except Exception as exc:
            self.status.set('Audio outputs unavailable. Connect a device and refresh.')
        self.devices.configure(values=list(self.options))
        self.device.set(next((name for name,key in self.options.items() if key==self.settings['device']), 'System default'))

    def start(self):
        if self.process is not None:return
        try:
            self.settings={'device': self.options.get(self.device.get(),'')}
            save_settings(DATA/'settings.json',self.settings)
            self.log=(DATA/'player.log').open('w',encoding='utf-8')
            command=[sys.executable,'-X','utf8','-u',str(ROOT/'app/visuals/live_visual_test.py'),'--quiet']
            if self.settings['device']:command+=['--device',self.settings['device']]
            self.process=subprocess.Popen(command,cwd=ROOT,stdout=self.log,stderr=subprocess.STDOUT,
                                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self.start_button.configure(state='disabled');self.stop_button.configure(state='normal')
            self.status.set('Visuals running. Close their window to finish normally.')
        except Exception as exc:
            if self.log:self.log.close();self.log=None
            messagebox.showerror('Could not start ZeraWave',str(exc))

    def poll(self):
        if self.process is not None and self.process.poll() is not None:
            code=self.process.returncode;self.process=None
            if self.log:self.log.close();self.log=None
            self.start_button.configure(state='normal');self.stop_button.configure(state='disabled')
            self.status.set('Ready.' if code==0 else 'Playback stopped. Check the audio output, refresh, and start again. Details are in Open log.')
        self.root.after(250,self.poll)

    def stop(self):
        if self.process is not None:self.process.terminate()

    def close(self):
        self.stop()
        if self.process is not None:
            try:self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        if self.log:self.log.close()
        self.root.destroy()


if __name__=='__main__':
    root=tk.Tk();Player(root);root.mainloop()
