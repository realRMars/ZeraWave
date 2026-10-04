"""CPU analysis/routing/migration checks; optional hidden native review controls.

Uses existing FFT fixtures and isolated analysis AST. No renderer/GPU/capture.
Authored files are read only; all Save/Load tests use a temporary directory.
"""
import argparse,ast,hashlib,json,math,sys,tempfile,time,os,io,threading
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/audio'),str(ROOT/'app/visuals')]
from spectral_listening import SpectralListening,ListeningHub,listening_choices,listening_defaults
from planet_audio_tuning import SPECS,WINDOWS,STAR_WINDOWS,STAR_TARGET,PlanetAudioTuning,baseline,bounds,role_active,WIDER_GAINS
from planet_listening import ListeningState,INGREDIENTS,derived,unpack_input,STYLES
from star_tuning_profiles import TargetProfileStore,SHIPPED,TARGET,validate_document,document,LEGACY_SHIPPED,PRE_LISTENING_SHIPPED
from artifacts_audio_tuning import ArtifactsAudioTuning,BASELINE as ART_BASE,WINDOWS as ART_WINDOWS,PRE_LISTENING_BASELINE,LEGACY_BASELINE,require_listening_bins
from starfield_tuning import MAPPED,ART_TARGET,target_windows,configure,decode,MAX_PACKET
from planet_canvas_dsp_test import audio_env,audio_state
from spectrum_tuning_test import fft_frame
from low_band_attack import LowBandAttack

def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('Invalid selection accepted')

def migration_checks(folder):
    reference=json.loads((ROOT/'work/planet-listening-01/backup-current.json').read_text(encoding='utf-8-sig'))
    manifest=json.loads((ROOT/reference['manifest']).read_text(encoding='utf-8-sig'))
    rows=[]
    for item in manifest['files']:
        raw=(ROOT/item['backup']).read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256']
        old=json.loads(raw);migrated=validate_document(old,target=old['target'])
        assert migrated['version']==3
        assert all(migrated['values'][k]==v for k,v in old['values'].items())
        added=set(migrated['values'])-set(old['values'])
        assert all(not migrated['values'][k] for k in added if k.endswith('_enabled'))
        path=folder/Path(item['path']).name;path.write_bytes(raw)
        store=TargetProfileStore(old['target'],path,folder/'profiles')
        assert not store.error and path.read_bytes()==raw
        c=dict(store.authored);bins=np.fft.rfftfreq(2048,1/48000.).tolist()
        for name in target_windows(old['target']):
            c.update({name+'_range_enabled':True,name+'_start_hz':900.,name+'_end_hz':1000.})
        named=store.save_profile('Migrated custom',c,bins);assert path.read_bytes()==raw
        assert store.load_profile(named,bins)[1]==c
        store.save_authored(c,bins);assert TargetProfileStore(old['target'],path).authored==c
        rows.append(dict(target=old['target'],old_version=old['version'],preserved_keys=len(old['values']),added_disabled=sorted(k for k in added if k.endswith('_enabled'))))
    # Exercise every historical schema, including missing optional target files.
    for target in MAPPED:
        current=SHIPPED if target==TARGET else ART_BASE if target==ART_TARGET else baseline(target)
        versions=(1,2) if target in (TARGET,ART_TARGET) else (1,)
        for version in versions:
            old=(LEGACY_SHIPPED if version==1 else PRE_LISTENING_SHIPPED) if target==TARGET else (LEGACY_BASELINE if version==1 else PRE_LISTENING_BASELINE) if target==ART_TARGET else {k:v for k,v in current.items() if k=='enabled' or k in [r['key'] for r in SPECS[target]]}
            d=dict(version=version,target=target,kind='authored',name='Authored',values={k:v for k,v in old.items() if k!='enabled'})
            assert validate_document(d,target=target)==document(current,'Authored','authored',target=target)
        reject(lambda:validate_document(dict(document(current,'Authored','authored',target=target),version=4),target=target))
    return dict(backed_files=len(rows),exact_old_values_preserved=True,in_memory_no_rewrite=True,named_save_separate=True,new_authored_relaunch=True,schemas=rows)

def routing_checks():
    f=np.fft.rfftfreq(2048,1/48000.);m=np.zeros(len(f));mask=(f>=900.)&(f<1000.)
    legacy=dict(bass=.23,flux=.31,sparkle=.41,impact=.53,raw_impact=.67,movement=.79)
    cases=[]
    for target in SPECS:
        for name in WINDOWS[target]:
            c=baseline(target);c.update({name+'_range_enabled':True,name+'_start_hz':900.,name+'_end_hz':1000.})
            tune=PlanetAudioTuning();assert tune.submit(target,1,c);tune.resolve(True,inputs=legacy)
            processor=SpectralListening(lambda:tune.analysis_settings(target));m[:]=0.
            first=processor.process(f,m,2048,'A');tune.observe({target:first})
            m[mask]=16. if name=='bass' else 1.
            row=processor.process(f,m,2048,'A');tune.observe({target:row})
            on,packed=tune.resolve(True,inputs=legacy,delta=.02,mode=0);assert on
            local=tune.selected[target];details=tune.listening_details[target];assert details[name]['ready']
            changed=[]
            for i,r in enumerate(SPECS[target]):
                slot=packed[list(SPECS).index(target)*2+i//4][i%4]
                expected=role_active(r,0) and name in INGREDIENTS[r['source']]
                assert (slot<=-1.)==expected,(target,name,r,slot)
                if expected:
                    assert math.isclose(unpack_input(legacy.get(r['source'],0.),slot),max(0.,min(1.,local[r['source']]*c[r['key']])),abs_tol=1e-12)
                    changed.append(r['key'])
            assert changed
            assert all(tune.packed[k]==tuple(1. for _ in SPECS[k]) for k in SPECS if k!=target)
            assert tune.resolve(False,inputs=legacy)[0]==0
            assert tune.submit(target,2,dict(c,**{name+'_range_enabled':False}));assert tune.resolve(True,inputs=legacy)[0]==0
            reject(lambda:TargetProfileStore(target,ROOT/'work/planet-listening-01/nonexistent.json').save_profile('Invalid',dict(c,**{name+'_start_hz':901.,name+'_end_hz':902.}),f))
            cases.append(dict(target=target,source=name,roles=changed))
    # Both gain extension and original ceilings are real, not UI-only ranges.
    wider=[]
    for target,roles in WIDER_GAINS.items():
        for key in roles:
            assert bounds(target)[key]==(0.,4.)
            c=baseline(target);c[key]=4.;t=PlanetAudioTuning();t.submit(target,1,c);t.resolve(True)
            i=[r['key'] for r in SPECS[target]].index(key);slot=t.packed[target][i]
            assert unpack_input(.2,slot)==.8 and unpack_input(.9,slot)==1.
            wider.append(target+'.'+key)
    assert len(wider)==5
    return dict(source_cases=len(cases),target_isolation=True,range_OFF_exact=True,context_OFF_neutral=True,wider_gains=wider,cases=cases)

def detector_checks():
    f=np.fft.rfftfreq(2048,1/48000.);m=np.zeros(len(f));mask=(f>=900.)&(f<1000.)
    c=dict(listening_defaults(('impact',)),impact_range_enabled=True,impact_start_hz=900.,impact_end_hz=1000.)
    listen=SpectralListening(lambda:(1,listening_choices(c,('impact',))))
    first=listen.process(f,m,2048,'A');assert first['channels']['impact']['level']==0.
    m[mask]=4.;hit=listen.process(f,m,2048,'A');assert hit['channels']['impact']['level']==.5
    assert hit['channels']['impact']['detector_response']['threshold']==.2
    state=ListeningState();state.observe(hit)
    selected,_=state.select(c,('impact',),dict(impact=.8,raw_impact=.9),True,.02)
    assert selected['impact']==.5 and selected['raw_impact']==.5
    for i in range(1,8):
        selected,_=state.select(c,('impact',),dict(impact=.8,raw_impact=.9),True,.02)
        assert math.isclose(selected['impact'],.5*math.exp(-6*.02*i),abs_tol=1e-12)
    state.reset_impact()
    selected,_=state.select(c,('impact',),dict(impact=.8,raw_impact=.9),True,0.)
    assert selected['impact']==selected['raw_impact']==0.
    fresh=deepcopy(hit);fresh['sample_seconds']+=2048/48000.;state.observe(fresh)
    selected,_=state.select(c,('impact',),dict(impact=.8,raw_impact=.9),True,.02)
    assert selected['impact']==selected['raw_impact']==.5
    c['impact_sensitivity']=2.
    changed=listen.process(f,m,2048,'A')['channels']['impact']
    assert changed['level']==0. and changed['detector_response']['threshold']==.1
    state.observe(listen.process(f,m,2048,'B'));assert state.impact==0.
    off=dict(c,impact_range_enabled=False);selected,_=state.select(off,('impact',),dict(impact=.8,raw_impact=.9),True,.02)
    assert selected['impact']==.8 and selected['raw_impact']==.9
    # Existing Star formula remains exact and feedback derives from actual data.
    star=LowBandAttack();star.process(0.,2048,'A',2.);p=star.process(8.,2048,'A',2.)
    r=p['detector_response'];assert r['rise']==8. and r['rise_floor']==2. and r['level_floor']==3. and p['bass_attack']==1.
    return dict(custom_first_window_primed=True,window_and_sensitivity_change_no_hit=True,sensitivity_thresholds=[.2,.1],repeated_render_no_new_hit=True,rewind_suppresses_old_hit=True,next_sample_eligible=True,exp6_release=True,Star_actual_threshold_feedback=True,ADSR_added=False)

def analysis_checks():
    current=audio_env(ROOT/'app/visuals/live_visual_test.py')
    before=audio_env(ROOT/'work/planet-listening-01/baseline/app/visuals/live_visual_test.py')
    old_state=audio_state();new_state=audio_state();tune=PlanetAudioTuning()
    new_state[0]._planet_listening=ListeningHub({k:lambda t=k:tune.analysis_settings(t) for k in SPECS})
    pcm=np.random.default_rng(901).normal(0.,.1,(2048,2));count=0
    for i in range(64):
        old=before(pcm,*old_state);new=current(pcm,*new_state)
        for key,value in old.__dict__.items():
            other=new.__dict__[key]
            assert np.array_equal(value,other) if isinstance(value,np.ndarray) else value==other,key
        count+=1
    assert all(p.previous is None for p in new_state[0]._planet_listening.processors.values())
    return dict(exact_legacy_frames=count,one_existing_FFT=True,all_OFF_no_spectrum_history_copies=True,no_capture=True)

def wire_checks():
    from types import SimpleNamespace
    from studio_color_link import ColorLink
    from spectrum_widget import SpectrumFeed
    from starfield_tuning import PREFIX
    model=PlanetAudioTuning();inputs=dict(bass=.2345678912345678,flux=.3456789123456789,sparkle=.4567891234567891,impact=.5678912345678912,raw_impact=.6789123456789123,movement=.7891234567891234)
    for target in SPECS:
        c=baseline(target)
        for key,value in c.items():
            if type(value) is float:c[key]=value+.01234567891234 if key.endswith('_hz') and value<24000. else value if key.endswith('_hz') else 1.2345678912345678
        for name in WINDOWS[target]:c[name+'_range_enabled']=True
        model.submit(target,1,c,c)
    model.resolve(True,SHIPPED,inputs)
    frame,_=fft_frame();feed=SpectrumFeed();feed.enable(True);feed.observe(frame,2048);s=feed.snapshot();s['db']=[-33.23456789123456]*1024
    p=dict(version=1,pilot_active=False,presentation_active=True,settings=SHIPPED,spectrum=s,planet_tuning=model.status(True,inputs,2))
    encoded=json.dumps(p,separators=(',',':'));assert 65536<len(encoded.encode())<MAX_PACKET and decode(encoded)
    controls_read,controls_write=os.pipe();status_read,status_write=os.pipe()
    class Log(io.StringIO):
        def close(self):self.saved=self.getvalue();super().close()
    log=Log();link=ColorLink(SimpleNamespace(stdin=os.fdopen(controls_write,'wb',buffering=0),stdout=os.fdopen(status_read,'rb',buffering=0)),log)
    try:
        payload=memoryview((PREFIX+encoded+'\n').encode())
        while payload:
            count=os.write(status_write,payload);payload=payload[count:]
        os.close(status_write);status_write=None
        link.reader.join(timeout=3.)
        result=link.get_star_tuning();assert result and result[0]==p
        assert not link.reader.is_alive() and log.saved==''
    finally:
        if status_write is not None:os.close(status_write)
        link.close();os.close(controls_read)
    return dict(real_pipe_bytes=len(encoded.encode()),above_old64KiB_limit=True,latest_ACK_exact=True,telemetry_not_logged=True,reader_closed=True)

def native_checks(folder):
    import tkinter as tk
    from types import SimpleNamespace
    from starfield_tuning import StarfieldTuningWindow,TARGETS,STAR_BOUNDS
    from band_attack_tuning import BandAttackTuning,effective
    from spectrum_widget import SpectrumFeed
    root=tk.Tk();root.withdraw();real=tk.Toplevel
    class HiddenClient(tk.Frame):
        def __init__(self,*a,**kw):
            self.host=real(*a,**kw);self.host.withdraw();super().__init__(self.host)
        def title(self,text):self.host.title(text)
        def geometry(self,size):
            width,height=map(int,size.split('x'));self.place(x=0,y=0,width=width,height=height)
        def protocol(self,*a):self.host.protocol(*a)
    stores={target:TargetProfileStore(target,folder/(target+'.json'),folder/'profiles') for target in MAPPED}
    model=PlanetAudioTuning();star=BandAttackTuning(authored=SHIPPED);artifact=ArtifactsAudioTuning()
    hub=ListeningHub({**{target:lambda t=target:model.analysis_settings(t) for target in SPECS},TARGET:star.listening_settings})
    art_listen=SpectralListening(artifact.analysis_settings);attack=LowBandAttack()
    frame,_=fft_frame();frame.spectrum_magnitudes[:]=.2;feed=SpectrumFeed();feed.enable(True)
    inputs=dict(bass=.2,flux=.3,sparkle=.4,impact=.5,raw_impact=.6,movement=.7)
    revisions={target:0 for target in MAPPED};full={};cases=[];view=None;max_bytes=0
    def submit(c,authored=None,target=TARGET):
        revisions[target]+=1;revision=revisions[target]
        if target==TARGET:assert star.submit(revision,c,authored)
        elif target==ART_TARGET:assert artifact.submit(revision,c,authored)
        else:assert model.submit(target,revision,c,authored)
        return revision
    def ack():
        nonlocal max_bytes
        star.apply_without_detector();star_values=effective(star.settings,star.authored)
        model.resolve(True,star_values,inputs,.02,2);artifact.resolve(True,inputs,.02)
        model.observe(hub.process(frame.spectrum_frequencies,frame.spectrum_magnitudes,2048,'native-fixture'))
        artifact.observe(art_listen.process(frame.spectrum_frequencies,frame.spectrum_magnitudes,2048,'native-fixture'))
        model.resolve(True,star_values,inputs,.02,2);artifact.resolve(True,inputs,.02)
        level,sensitivity,summary=star.apply(frame,.2,attack,'native-fixture')
        payload=attack.process(level,2048,'native-fixture',sensitivity);star.completed(payload,summary)
        feed.observe(frame,2048)
        full.update(version=1,pilot_active=True,presentation_active=True,rendered_wall=time.perf_counter(),
            analysis_age_seconds=0.,revision=star.revision,settings=deepcopy(star.settings),effective=deepcopy(star_values),authored=deepcopy(star.authored),
            listening=model.listening[TARGET].details(star_values,STAR_WINDOWS,True),detector_response=payload['detector_response'],weighted_level=level,
            spectrum=feed.snapshot(),planet_tuning=model.status(True,inputs,2),artifact_tuning=artifact.status(True,(.3,.5,.4),0.,True,bass=.2))
        raw=json.dumps(full,separators=(',',':'));assert decode(raw);max_bytes=max(max_bytes,len(raw.encode()))
        view.refresh((full,time.perf_counter()),True);view.window.update_idletasks();view.spectrum.draw(force=True)
    try:
        with patch('tkinter.Toplevel',side_effect=HiddenClient),patch('starfield_tuning.TargetProfileStore',side_effect=lambda target:stores[target]):
            view=StarfieldTuningWindow(root,submit,lambda enabled:None,store=stores[TARGET],artifact_store=stores[ART_TARGET])
        for target in TARGETS:
            target_id=target.target_id;view.target_var.set(target.label);view.select_target();ack()
            names=target_windows(target_id)
            for name in names:
                view.range_vars[name].set(True);view.vars[name+'_start_hz'].set(900.);view.vars[name+'_end_hz'].set(1000.)
            view.enabled.set(True);view.changed();view.send();ack()
            assert len(view.spectrum.ranges)==len(names)
            for i,name in enumerate(names):
                r=view.spectrum.ranges[i];assert r.enabled and r.ready and r.color==STYLES[name][0] and r.dash==STYLES[name][1]
                assert all(view.spectrum.canvas.itemcget(item,'state')=='normal' for item in view.spectrum.range_items[i])
                assert view.range_checks[name].winfo_manager()=='grid' and not view.range_checks[name].instate(['disabled'])
            assert all(view.range_checks[n].winfo_manager()!='grid' for n in STYLES if n not in names)
            if 'impact' in names:
                i=list(view.vars).index('impact_sensitivity');assert not view.sliders[i].instate(['disabled'])
                view.range_vars['impact'].set(False);view.changed('impact_range_enabled');view.send();ack()
                assert view.sliders[i].instate(['disabled'])
                view.range_vars['impact'].set(True);view.changed('impact_range_enabled');view.send();ack()
            if target_id==TARGET:
                view.vars['sensitivity'].set(1.25);view.changed('sensitivity');view.send();ack()
                assert full['detector_response']['rise_floor']==3.2
                assert all(view.detector_canvas.itemcget(i,'state')=='normal' for group in view.detector_items for i in group)
            # Persistence consumes a matched FFT ACK; never unacknowledged knobs.
            view.profile_name.set('All applicable windows');view.save_profile();assert 'Saved named profile' in view.profile_status.get()
            assert view.save_authored(),view.profile_status.get();ack()
            p=view.target_packet();saved=stores[target_id].authored
            assert saved==dict(p['effective'],enabled=True)
            assert TargetProfileStore(target_id,stores[target_id].authored_path).authored==saved
            paths=list(stores[target_id].profile_dir.glob('*.json'));named=next(p for p in paths if json.loads(p.read_text())['target']==target_id)
            assert stores[target_id].load_profile(named,frame.spectrum_frequencies.tolist())[1]==saved
            view.reset();view.send();ack();assert not view.enabled.get()
            assert all(r.enabled for r in view.spectrum.ranges) # OFF override uses newly saved authored windows.
            cases.append(dict(target=target_id,windows=list(names),saved=True,range_override_reset_preserves_authored=True,rows=len(view.vars)))
        assert view.window.host.state()=='withdrawn'
        return dict(targets=len(cases),cases=cases,all_enabled_ranges_simultaneous=True,stable_source_styles=True,
            matching_ACK_Save_Load_relaunch=True,custom_sensitivity_disabled_when_window_OFF=True,Star_threshold_feedback=True,
            max_packet_bytes=max_bytes,packet_limit=MAX_PACKET,hidden_native=True,no_foreground_focus=True,tk_version=root.tk.call('info','patchlevel'))
    finally:
        if view:view.close();view.window.host.destroy()
        root.destroy()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--native-hidden',action='store_true');a=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='zerawave-local-listening-') as tmp:
        result=dict(evidence_class='CPU synthetic FFT, isolated actual analysis, target uniform packing and temporary-file migration/persistence; '+('withdrawn native Tk; ' if a.native_hidden else 'no UI; ')+'no GPU/device capture',
                    migration=migration_checks(Path(tmp)),routing=routing_checks(),detectors=detector_checks(),analysis=analysis_checks(),wire=wire_checks())
        if a.native_hidden:result['native']=native_checks(Path(tmp)/'native')
    assert not any(k in sys.modules for k in ('moderngl','glfw','capture','soundcard'))
    if not a.native_hidden:assert 'tkinter' not in sys.modules
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2));print('Planet local listening CPU checks PASS')
if __name__=='__main__':main()
