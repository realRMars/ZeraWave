"""Cymatics source/controller inside the existing Renderer and shared analysis."""
import argparse,json,sys,time,wave
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
for p in (HERE,HERE.parent/'audio'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
from oscillator import Oscillator,Monitor,RATE
from frequency_bands import FrequencyBands
from cymatics import Basin
from cymatics_view import BasinView
from cymatics_session import validate
from live_visual_test import analyze_samples,AudioAnalyzer,SignalProcessor,VisualSignalConditioner,OnsetDetector,VisualParameterMapper
from renderer import Renderer
from studio_color_link import configure_colors,ACK_PREFIX
from color_controls import parse_colors

class Experiment:
    def __init__(self,renderer,settings=None,track=None,monitor=None):
        self.renderer=renderer;self.track=track;self.monitor=monitor or Monitor();self.source=None;self.discarded_wall_seconds=0.;self.eof=False;self.window_mute_serial=0
        self.settings=validate(settings,stored=True);self.reset()
    def close_source(self):
        if self.source:
            if self.settings['source']=='loopback':self.source.stop()
            else:self.source.close()
        self.source=None
    def reset(self):
        self.close_source();self.monitor.stop();self.oscillator=Oscillator(self.settings['oscillator']);self.index=0;self.sample_fraction=0.;self.buffer=np.zeros(0)
        self.renderer.cymatics_camera=BasinView(self.settings['camera'])
        self.renderer.cymatics_style=(float(('obsidian','marble').index(self.settings['finish'])),self.settings['light_angle'],self.settings['dye_swirl'])
        self.renderer.cymatics_view=(float(self.settings['camera_orbit']),self.settings['dye_strength'] if self.settings['dye'] else 0.,0.)
        self.renderer.cymatics=Basin(self.settings['basin']);self.analyzer=AudioAnalyzer();self.analyzer.frequency_bands=FrequencyBands(self.settings['bands'])
        self.processor=SignalProcessor(smoothing=.5);self.conditioner=VisualSignalConditioner(quiet_threshold=.06)
        self.detectors={k:OnsetDetector() for k in ('bass','mids','highs')};self.mapper=VisualParameterMapper();self.frame=None;self.eof=False
        if self.settings['source']=='track':
            if not self.track:raise ValueError('Choose a48kHz16-bit test track')
            audio=wave.open(str(self.track),'rb')
            if audio.getframerate()!=RATE or audio.getsampwidth()!=2 or audio.getnchannels() not in (1,2):audio.close();raise ValueError('Need48kHz16-bit mono/stereo WAV')
            self.source=audio
        elif self.settings['source']=='loopback':
            from capture import AudioCapture
            self.source=AudioCapture();self.source.start()
    def apply(self,data):
        c=validate(data);old=self.settings
        # Prepare numerical objects before changing the current valid source.
        trial,rebuild=self.renderer.cymatics.update(c['basin']);bands=FrequencyBands(c['bands'])
        if c['source']!=old['source']:raise ValueError('Source selection requires Stop and Start; other values retained')
        restarted=c['restart']!=old['restart']
        if c['oscillator']!=old['oscillator']:self.oscillator.apply(c['oscillator'])
        if c['bands']!=old['bands']:self.analyzer.frequency_bands=bands
        dye_origin=self.index/RATE if c['dye_reset']!=old['dye_reset'] else self.renderer.cymatics_view[2]
        self.renderer.cymatics_view=(float(c['camera_orbit']),c['dye_strength'] if c['dye'] else 0.,dye_origin)
        if c['camera']!=old['camera']:self.renderer.cymatics_camera.load(c['camera'])
        if c['view_reset']!=old['view_reset']:self.renderer.cymatics_camera.reset()
        self.renderer.cymatics_style=(float(('obsidian','marble').index(c['finish'])),c['light_angle'],c['dye_swirl'])
        self.renderer.cymatics=trial;self.settings=c;self.oscillator.paused=c['paused']
        if restarted:self.reset();self.oscillator.paused=c['paused']
        if c['monitor'] and not c['paused']:
            if not self.monitor.enabled and (not old['monitor'] or old['paused'] or restarted):self.monitor.enable(c['monitor_gain'])
            self.monitor.target=c['monitor_gain']
        else:self.monitor.stop()
        self.renderer.cymatics_material=float(('glass','mercury','ink').index(c['material']))
        return rebuild or restarted
    def advance(self,wall_seconds):
        if self.settings['paused']:return
        requested=max(0.,wall_seconds)*RATE+self.sample_fraction
        target=int(requested);self.sample_fraction=requested-target
        if target>4800:self.discarded_wall_seconds+=(target-4800)/RATE;target=4800
        if self.settings['source']=='loopback':blocks=[self.source.read(numframes=2048).mean(axis=1)]
        else:
            blocks=[]
            for start in range(0,target,2048):
                n=min(2048,target-start)
                if self.settings['source']=='oscillator':pcm=self.oscillator.read(n)
                else:
                    data=self.source.readframes(n);pcm=np.frombuffer(data,np.int16).astype(float)/32768.
                    if self.source.getnchannels()==2:pcm=pcm.reshape(-1,2).mean(axis=1)
                    if len(pcm)<n:self.eof=True
                blocks.append(pcm)
        for pcm in blocks:
            if not len(pcm):continue
            level=0.;selected=self.settings['basin']['routing_band']
            if selected>=0 and self.frame is not None:level=self.frame.band12['levels'][selected]
            self.renderer.cymatics.advance(pcm,level);self.index+=len(pcm);self.monitor.submit(pcm)
            self.buffer=np.concatenate((self.buffer,pcm))
            while len(self.buffer)>=2048:
                block=self.buffer[:2048];self.buffer=self.buffer[2048:]
                self.frame=analyze_samples(block,self.analyzer,self.processor,self.conditioner,self.detectors)
                mapped=self.mapper.map_frame(self.frame)
                for key,val in mapped.items():setattr(self.renderer.parameters,key,val)
            assert len(self.buffer)<2048
    def status(self):
        return dict(cymatics_status=dict(camera=self.renderer.cymatics_camera.config(),camera_serial=self.renderer.cymatics_camera.serial,window_mute_serial=self.window_mute_serial,monitor_requested=self.settings['monitor'],sample_index=self.index,seconds=self.index/RATE,source=self.settings['source'],oscillator=self.oscillator.metadata() if self.settings['source']=='oscillator' else None,basin=self.renderer.cymatics.report(),bands=self.frame.band12 if self.frame else None,monitor_enabled=self.monitor.enabled,monitor_error=self.monitor.error,monitor_overruns=self.monitor.overruns,monitor_underruns=self.monitor.underruns,discarded_wall_seconds=self.discarded_wall_seconds))
    def close(self):self.close_source();self.monitor.stop()

def run(settings=None,track=None,colors=None,live=False,max_seconds=None):
    renderer=Renderer(title='ZeraWave — Cymatics Water');renderer.debug_state=37
    configure_colors(renderer,colors,live);experiment=Experiment(renderer,settings,track);origin=time.perf_counter();previous=origin;report_time=-1.
    try:
        renderer.create();renderer.cymatics_material=float(('glass','mercury','ink').index(experiment.settings['material']))
        while not renderer.should_close():
            if live and renderer.color_inbox.eof:break
            now=time.perf_counter();delta=now-previous;previous=now
            update=renderer.color_inbox.take_scene() if renderer.color_inbox else None
            reset=False
            if update:
                try:reset=experiment.apply(update[1])
                except Exception as exc:
                    print(ACK_PREFIX+json.dumps(dict(scene_rejected=update[0],scene_error=str(exc))),flush=True);update=None
            renderer.poll_events()
            if getattr(renderer,'cymatics_mute_requested',False):
                renderer.cymatics_mute_requested=False;experiment.settings['monitor']=False;experiment.monitor.stop();experiment.window_mute_serial+=1
            experiment.advance(delta);renderer.render(experiment.index/RATE);renderer.swap_buffers()
            if update:print(ACK_PREFIX+json.dumps(dict(scene_applied=update[0],scene_reset=reset,scene_error=None)),flush=True)
            if now-report_time>=.2:
                print(ACK_PREFIX+json.dumps(experiment.status()),flush=True);report_time=now
            if experiment.eof or max_seconds is not None and experiment.index/RATE>=max_seconds:break
    finally:
        if experiment.eof:experiment.monitor.drain(.35)
        experiment.close();renderer.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',default='cymatics');p.add_argument('--config',default='{}');p.add_argument('--track');p.add_argument('--colors');p.add_argument('--studio-color-input',action='store_true');p.add_argument('--max-seconds',type=float)
    a=p.parse_args();run(json.loads(a.config),a.track,parse_colors(a.colors) if a.colors else {},a.studio_color_input,a.max_seconds)
