"""Exact decoded replay owner with real scoped pipes/FFT and mocked graphics."""
import ast,io,json,os,random,sys,threading
from copy import deepcopy
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from planet_canvas_dsp_test import functions,audio_env,renderer_type
from analyzer import AudioAnalyzer
from signal_processor import SignalProcessor,VisualSignalConditioner
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from studio_color_link import ColorInbox
from audio_scope import Scope
from audio_controls import defaults
from transition_catalog import validate_settings
from preview_layers import validate_layers,layers_at
from world_catalog import LIVE_STATES
from studio_audio import decode

def run(recipe='tr_planet',pair=(12,5)):
    clock=[100.];renders=[];readers=[];wavefiles=[]
    # Keep the selected Flux above the existing quiet gate so a priming
    # discrepancy cannot pass merely because both trials report zero.
    fixture=np.random.default_rng(739).normal(0.,.2,(2048*256,2))
    raw=(fixture*32767).astype(np.int16).tobytes()
    class PCMFile:
        def __enter__(self):self.position=0;wavefiles.append(self);return self
        def __exit__(self,*a):pass
        def getframerate(self):return 48000
        def getnchannels(self):return 2
        def getsampwidth(self):return 2
        def tell(self):return self.position//4
        def setpos(self,n):self.position=n*4
        def rewind(self):self.position=0
        def readframes(self,n):
            chunk=raw[self.position:self.position+n*4];self.position+=len(chunk);return chunk
    base=renderer_type()
    tree=ast.parse((ROOT/'app/visuals/renderer.py').read_text(encoding='utf8'))
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Renderer')
    methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('state_at','planet_star_attack_eligible','accept_planet_star_audio','reset_planet_star_attack')]
    node=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='RealMethods',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[]))
    env={};exec(compile(node,'actual-renderer-methods','exec'),env)
    class CPUReplay(base,env['RealMethods']):
        def __init__(self,**kw):
            super().__init__();self.parameters=SimpleNamespace();self.flow_time=0.;self.star_time=0.;self.flow_rate=.35
            self.planet_star_flight=None;self.frames=[];self.polls=0;self.echo_weight=0.;self.shockwaves=[];self.blast_events=[];self.planet_visits=0
            self.director_rng=random.Random(739);self.director_current=12;self.director_target=None;self.director_history=[]
            self.director_recipe='tr_fade';self.director_pending=None;self.director_fast=self.director_slow=None;self.director_min_hold=14.;self.director_max_hold=40.;self.director_duration=6.
            self.blend_values={};self.cosmos_seed=739;self.color_overrides={};self.enveloper_failed=False
            self.program={'u_planet_star_flight':SimpleNamespace(value=(0.,0.,0.))};renders.append(self)
        def set_galaxy_start(self,*a):pass
        def configure_transitions(self,c):self.transition_settings=validate_settings(c);self.transition_sequence=bool(self.transition_settings['pair'])
        def create(self):
            self.studio_audio.visible=True
            c=dict(defaults('roots.growth'),flux_range_enabled=True,flux_start_hz=90.,flux_end_hz=300.)
            self.color_inbox.accept(json.dumps(dict(kind='audio-tuning',scope=Scope('run','session',12,'roots.growth',1).packet(),settings=c)))
        def consume_pcm(self,pcm):pass
        def should_close(self):return self.polls>=172 if audition[0] else self.polls>=44
        def render(self,elapsed_time):
            owner=self.studio_audio;owner.prepare(elapsed_time)
            inputs=dict(bass=self.parameters.scale,movement=self.parameters.movement,flux=self.parameters.flux,sparkle=self.parameters.sparkle,impact=self.parameters.impact,raw_impact=self.parameters.impact)
            owner.resolve(inputs,2048/48000.,False,0);owner.guard_history()
            self.planet_audio_tuning.resolve(5 in owner.endpoint['active'],{},inputs,2048/48000.,0,False)
            self.artifact_tuning.resolve(5 in owner.endpoint['active'],inputs,2048/48000.,False)
            self.program['u_planet_star_flight'].value=(0.,0.,0.)
            self.frames.append(dict(active=owner.audition.active,inputs=deepcopy(inputs),selected=deepcopy(owner.model.selected.get('roots.growth')),seconds=elapsed_time))
            # Packet generation and decoding exercise the actual selected-owner ACK.
            owner.view_form=12;owner.view_target='roots.growth';owner.last=-1000.
            packet=owner.snapshot(elapsed_time)
            serialized=json.dumps(packet,allow_nan=False)
            assert decode(serialized,'run','session')==json.loads(serialized)
        def swap_buffers(self):pass
        def poll_events(self):
            self.polls+=1;clock[0]+=2048/48000.
            if audition[0] and self.polls in (20,84,148):
                start=self.polls!=148;target='transition.'+recipe if start else 'transition.director'
                cfg=validate_settings(dict(pair=list(pair),isolate={'pair':recipe},hold=1.,duration=1.)) if start else None
                self.color_inbox.accept(json.dumps(dict(kind='audio-audition',scope=Scope('run','session',0,target,self.polls).packet(),action='start' if start else 'return',config=cfg)))
        def close(self):self.color_inbox.close()
    def configure_colors(renderer,*args):
        fd,writer=os.pipe();readers.append(writer);renderer.color_inbox=ColorInbox(fd)
    audition=[False]
    env=dict(Path=Path,np=np,math=__import__('math'),time=SimpleNamespace(perf_counter=lambda:clock[0],sleep=lambda t:None),wave=SimpleNamespace(open=lambda *a:PCMFile()),Renderer=CPUReplay,
        AudioAnalyzer=AudioAnalyzer,SignalProcessor=SignalProcessor,VisualSignalConditioner=VisualSignalConditioner,OnsetDetector=OnsetDetector,VisualParameterMapper=VisualParameterMapper,
        analyze_samples=audio_env(ROOT/'app/visuals/live_visual_test.py'),LIVE_STATES=LIVE_STATES,validate_layers=validate_layers,layers_at=layers_at,configure_colors=configure_colors)
    replay=functions(ROOT/'app/visuals/replay_test.py',['optional_uniform_vector','replay'],env)['replay']
    try:
        with patch.dict(os.environ,{'ZERAWAVE_AUDIO_RUN':'run','ZERAWAVE_AUDIO_SESSION':'session'}),redirect_stdout(io.StringIO()):
            replay(Path('supplied-PCM.wav'),speed=0.,state='roots',color_input=True)
            audition[0]=True;replay(Path('supplied-PCM.wav'),speed=0.,state='roots',color_input=True)
        baseline,trial=renders
        first=trial.frames[20:84];repeat=trial.frames[84:148]
        assert all(a['active'] and b['active'] for a,b in zip(first,repeat))
        assert [(x['inputs'],x['selected']) for x in first]==[(x['inputs'],x['selected']) for x in repeat]
        resumed=[x for x in trial.frames if not x['active']]
        assert [(x['inputs'],x['selected']) for x in resumed]==[(x['inputs'],x['selected']) for x in baseline.frames]
        assert trial.studio_audio.audition.saved is None and not trial.studio_audio.audition.active
        assert trial.studio_audio.model.status(12,'roots.growth',trial.frames[-1]['inputs'])['scope']['revision']==1
        assert trial.planet_star_attack_pilot
        assert len(renders)==2 and len(wavefiles)==2
        assert any(x['seconds']>=2. for x in first),'Repeat must include the other endpoint'
        assert any((x['selected'] or {}).get('flux',0.)>0. for x in first),'Selected-window repeat requires a nonzero test signal'
        return dict(recipe=recipe,pair=pair,evidence='Exact decoded replay loop; supplied 48kHz PCM, actual analyzer/scoped pipes, mocked graphics; no capture/device/GPU',repeat_frames=64,resumed_frames_equal_baseline=44,independent_source_and_FFT_history_restored=True,repeat_after_other_endpoint=True,live_authored_revision_preserved=True,single_renderer_per_run=True)
    finally:
        for fd in readers:
            try:os.close(fd)
            except OSError:pass
        for r in renders:
            if getattr(r,'color_inbox',None):r.color_inbox.close()

if __name__=='__main__':print(json.dumps([run(),run('tr_branch_iris',(12,41)),run('tr_flow_fold',(12,43))],indent=2));print('Studio Audio decoded owner CPU checks PASS')
