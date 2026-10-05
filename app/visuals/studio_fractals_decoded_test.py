"""Actual public Studio decoded children; six bounded GPU/transport cases."""
import argparse,csv,hashlib,json,sys,time
from pathlib import Path
import tkinter as tk
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio'),str(ROOT/'app')]
from studio import Studio,command
from audio_controls import defaults
from audio_scope import Scope
from replay_test import optional_uniform_vector

def run(output):
    output.mkdir(parents=True,exist_ok=False)
    source={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'app').rglob('*') if p.is_file() and p.suffix in ('.py','.frag','.json')}
    baseline={p:p.read_bytes() for p in (ROOT/'app').rglob('*.json')}
    rows=[];root=tk.Tk();root.withdraw();app=Studio(root)
    def pump(predicate=None,seconds=1.,timeout=35.):
        end=time.perf_counter()+(timeout if predicate else seconds)
        while time.perf_counter()<end:
            root.update();app.refresh_playback_controls()
            if predicate and predicate():return
            time.sleep(.02)
        if predicate:raise AssertionError('Public child timeout: '+app.status.get())
    try:
        assert optional_uniform_vector({},'u_planet_star_flight') is None
        for form,leaf,target,color_target,role in ((41,'landscape','fractal.41.landscape','fractal.landscape.terrain','body'),(42,'atrium','fractal.42.recursion','fractal.atrium.stone','body'),(43,'bloom','fractal.43.growth','fractal.bloom.honey','wax')):
            for captures in (False,True):
                result=dict(form=form,captures=captures);rows.append(result)
                folder=output/('form-'+str(form)+'-'+('capture-on' if captures else 'capture-off'))
                app.select(['fractals',leaf]);app.vars['source'].set('Test track');app.vars['speed'].set('Real time');app.vars['duration'].set('30 seconds');app.vars['captures'].set(captures);app.diagnostics.set(True)
                app.color_overrides={};v=app.values();argv=command(v,folder)
                result['argv']=[Path(x).name if x==v['track'] else x for x in argv];app.launch(v,folder);child=app.process;link=app.color_link
                pump(lambda:app.preview_state.get('ready'));assert not app.preview_state['can_bonk']
                link.submit_audio_view(form,target,pin=True,enabled=True)
                c=dict(defaults(target),enabled=True,bass_response=.5,bass_range_enabled=True,bass_start_hz=80.,bass_end_hz=300.)
                revision=link.submit_audio(form,target,c)
                def audio():
                    packet=link.get_audio();return packet[0]['audio_targets'].get(target,{}) if packet else {}
                pump(lambda:audio().get('scope',{}).get('revision')==revision)
                pump(lambda:audio().get('listening',{}).get('bass',{}).get('ready'))
                result['selected_bin_audio']=audio();assert audio()['effective']['bass_response']==.5
                rejected=link.submit_audio(form,target,dict(c,bass_start_hz=100.,bass_end_hz=100.01))
                pump(lambda:audio().get('rejected_revision')==rejected)
                with link.condition:
                    link.pending_audio[(form,target)]=dict(kind='audio-tuning',scope=Scope(link.audio_run,link.audio_session,form,target,revision).packet(),settings=dict(c,bass_response=1.8));link.condition.notify()
                pump(seconds=.3)
                with link.condition:
                    link.pending_audio[(form,target)]=dict(kind='audio-tuning',scope=Scope('wrong-run',link.audio_session,form,target,99).packet(),settings=c);link.condition.notify()
                pump(seconds=.3)
                app.set_color_setup({color_target:{role:dict(color='#55BB88')}})
                pump(lambda:app.color_send_after is None and app.last_color_revision>1 and link.get_status().get('applied')==app.last_color_revision)
                color_revision=app.last_color_revision
                with link.condition:
                    link.pending=dict(kind='colors',revision=1,targets={color_target:{role:dict(color='#FF0000')}});link.condition.notify()
                pump(seconds=.3)
                app.pause_preview();pump(lambda:app.preview_state.get('paused'));pump(seconds=.35)
                app.pause_preview();pump(lambda:not app.preview_state.get('paused'));pump(seconds=.5)
                app.stop();assert child.poll()==0 and app.process is None and not link.reader.is_alive() and not link.writer.is_alive()
                perf=json.loads((folder/'session-performance.json').read_text(encoding='utf8'));edits=perf['applied_edit_trace']
                audio_edits=[x for x in edits if x['kind']=='audio'];color_edits=[x for x in edits if x['kind']=='colors']
                assert [x['scope']['revision'] for x in audio_edits]==[revision],audio_edits
                assert audio_edits[0]['scope']==Scope(link.audio_run,link.audio_session,form,target,revision).packet()
                assert any(x['scope']['revision']==color_revision and x['settings']['settings'][color_target][role]['color']=='#55BB88' for x in color_edits)
                assert perf['identity']['settings_identity_kind'].startswith('launch-only')
                assert perf['applied_edit_chain_sha256']!=perf['identity']['launch_settings_sha256']
                assert perf['presentation_intervals']['samples']>0 and perf['dimensions']['framebuffer']==[1280,720]
                metrics=list(csv.DictReader((folder/'metrics.csv').open(encoding='utf8')));assert metrics
                assert all(row['star_flight_phase']=='' and row['star_attack_envelope']=='' and row['star_flight_available']=='False' for row in metrics)
                assert all(float(row['bass_attack'])>=0 for row in metrics)
                if captures:
                    shot=json.loads((folder/'captures.json').read_text(encoding='utf8'));assert shot['captures']
                    assert all(x['material_mix'] is None for x in shot['captures'])
                    assert all((folder/x['file']).is_file() for x in shot['captures'])
                    result['capture_metadata_unavailable']=True
                else:assert not (folder/'captures.json').exists()
                result.update(ready=True,pause_resume_ACK=True,owned_stop=True,threads_closed=True,report_saved=True,audio_revision=revision,rejected_revision=rejected,stale_and_wrong_owner_not_applied=True,color_revision=color_revision,applied_edit_trace=edits,frames=perf['presentation_intervals']['samples'],decoded_rows=len(metrics),audio_identity=perf['identity']['audio'])
                print('PASS public decoded',form,'captures',captures,flush=True)
        assert all(p.read_bytes()==old for p,old in baseline.items())
    finally:
        app.stop();root.destroy();(output/'review-index.json').write_text(json.dumps(dict(evidence='Actual public Studio Test-track command; withdrawn Tk, real GPU/decoded PCM; silent, no foreground keyboard or listening',source=source,cases=rows,authored_JSON_preserved=all(p.read_bytes()==old for p,old in baseline.items())),indent=2),encoding='utf8')
    print('Public decoded Fractals checks PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);run(parser.parse_args().output)
