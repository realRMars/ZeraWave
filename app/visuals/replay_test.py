from transition_catalog import parse_settings
"""Development-only offline replay of a decoded WAV through the live pipeline."""

import argparse
import csv
import json
import math
import sys
import time
import wave
from pathlib import Path

import numpy as np

VISUALS_PATH = Path(__file__).resolve().parent
AUDIO_PATH = VISUALS_PATH.parent / "audio"
for path in (VISUALS_PATH, AUDIO_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from analyzer import AudioAnalyzer
from live_visual_test import LIVE_STATES, analyze_samples
from onset_detector import OnsetDetector
from parameter_mapper import VisualParameterMapper
from renderer import Renderer
from studio_color_link import configure_colors
from color_controls import parse_colors
from preview_layers import parse_layers, validate_layers, layers_at
from signal_processor import SignalProcessor, VisualSignalConditioner


def optional_uniform_vector(program,name):
    """Absent program-specific presentation metadata is unavailable, never zero."""
    return tuple(program[name].value) if name in program else None


def replay(path, speed=12.0, max_seconds=None, metrics_path=None, state="blend",
           capture_dir=None, capture_interval=15.0, states=None, layers=None, seed=None, palette="authored", comparison_label=None, colors=None, color_input=False, galaxy_visit=0, galaxy_short=False, transitions=None, planet_dsp_pilot=False, planet_star_attack_pilot=False):
    if palette not in ("authored", "soft-dream"):
        raise ValueError("Unknown preview palette")
    if not math.isfinite(speed) or speed < 0:
        raise ValueError("Speed must be finite and nonnegative")
    if max_seconds is not None and (not math.isfinite(max_seconds) or max_seconds <= 0):
        raise ValueError("Duration must be finite and positive")
    if capture_dir is not None:
        if capture_interval <= 0:
            raise ValueError("Capture interval must be positive")
        capture_dir.mkdir(parents=True, exist_ok=True)
    captures = []
    from preview_capture import CaptureWriter,ReplayTelemetry
    capture_writer=None
    capture_target = None
    next_capture = 0.0
    debug_state = LIVE_STATES[state]
    with wave.open(str(path), "rb") as audio:
        rate = audio.getframerate()
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        if rate != 48000 or width != 2:
            raise ValueError(f"Expected 48 kHz 16-bit WAV, got {rate} Hz / {width * 8}-bit")

        analyzer = AudioAnalyzer()
        processor = SignalProcessor(smoothing=0.5)
        conditioner = VisualSignalConditioner(quiet_threshold=0.06)
        mapper = VisualParameterMapper()
        detectors = {name: OnsetDetector(threshold=0.2) for name in ("bass", "mids", "highs")}
        renderer = Renderer(title=(f"ZeraWave Matched {comparison_label} - {palette}" if comparison_label else "ZeraWave WAV Replay"), seed=seed)
        renderer.set_galaxy_start(galaxy_visit,galaxy_short)
        renderer.preview_palette = palette
        renderer.debug_state = debug_state
        renderer.debug_sequence = tuple(LIVE_STATES[name] for name in (states or ()))
        renderer.layer_profiles = validate_layers(layers or {})
        renderer.configure_transitions(transitions)
        renderer.planet_dsp_pilot = planet_dsp_pilot
        pilot = renderer.planet_dsp_eligible()
        renderer.planet_star_attack_pilot = planet_star_attack_pilot
        star_pilot = bool(planet_star_attack_pilot and renderer.planet_star_attack_eligible())
        configure_colors(renderer, colors, color_input)
        if color_input:
            from planet_mapping_monitor import configure
            configure(renderer, 'REPLAY', str(Path(path).resolve()))
        if color_input or star_pilot or renderer.debug_state==5:
            from starfield_tuning import configure as configure_star_tuning,observe_spectrum
            configure_star_tuning(renderer,analyzer,normal=color_input)
            if getattr(renderer,'studio_audio',None) is not None:star_pilot=True
            if getattr(renderer,'studio_audio',None) is not None and renderer.planet_dsp_pilot:pilot=True
        rows = ReplayTelemetry(metrics_path)
        chunk = 2048
        song_time = 0.0

        try:
            capture_writer=CaptureWriter(capture_dir) if capture_dir is not None else None
            renderer.create()
            if comparison_label:
                import glfw
                glfw.set_window_attrib(renderer.window, glfw.RESIZABLE, glfw.FALSE)
            controls=getattr(renderer,'preview_playback',None)
            def playback_wall():return controls.drawing_time() if controls is not None else time.perf_counter()
            replay_start = playback_wall();read_to=0.;next_present=0.;frame=None;result=None;rendered_frames=0;analyzed_frames=0
            owner=getattr(renderer,'studio_audio',None)
            if owner is not None:
                owner.source_mode='REPLAY';owner.source_identity=str(Path(path).resolve())
                from copy import deepcopy
                from planet_listening import ListeningState
                from studio_audition import listening_history
                excluded={'_planet_star_tuning','_planet_listening','_artifact_listening','_form_listening'}
                def decoded_audition_source(action,snapshot=None):
                    nonlocal song_time,read_to,replay_start,next_present,frame,result
                    if action=='save':
                        return dict(position=audio.tell(),song_time=song_time,read_to=read_to,next_present=next_present,frame=deepcopy(frame),result=deepcopy(result),
                            analyzer=deepcopy({k:v for k,v in vars(analyzer).items() if k not in excluded}),processor=deepcopy(vars(processor)),conditioner=deepcopy(vars(conditioner)),detectors=deepcopy(detectors),mapper=deepcopy(vars(mapper)),
                            active=set(owner.model.active),listening=deepcopy(owner.model.listening),processors=deepcopy(owner.model.processors),endpoint=deepcopy(owner.endpoint),
                            target_history=listening_history(renderer,analyzer,'save'))
                    if action=='reset':
                        audio.rewind();song_time=read_to=next_present=0.;frame=result=None
                        for key in tuple(vars(analyzer)):
                            if key not in excluded:delattr(analyzer,key)
                        vars(analyzer).update(vars(AudioAnalyzer()))
                        vars(processor).clear();vars(processor).update(vars(SignalProcessor(smoothing=.5)))
                        vars(conditioner).clear();vars(conditioner).update(vars(VisualSignalConditioner(quiet_threshold=.06)))
                        detectors.clear();detectors.update({k:OnsetDetector(threshold=.2) for k in ('bass','mids','highs')})
                        vars(mapper).clear();vars(mapper).update(vars(VisualParameterMapper()))
                        # The prior audition may end on a different form. Prime
                        # both trials from the same empty endpoint history so
                        # their first decoded block cannot inherit that owner.
                        owner.model.active.clear();owner.model.selected.clear();owner.model.packed.clear()
                        owner.model.processors.clear();owner.model.listening={target:ListeningState() for target in owner.model.state}
                        listening_history(renderer,analyzer,'reset')
                    elif action=='restore':
                        audio.setpos(snapshot['position']);song_time=snapshot['song_time'];read_to=snapshot['read_to'];next_present=snapshot['next_present'];frame=snapshot['frame'];result=snapshot['result']
                        for key in tuple(vars(analyzer)):
                            if key not in excluded:delattr(analyzer,key)
                        vars(analyzer).update(snapshot['analyzer'])
                        for obj,key in ((processor,'processor'),(conditioner,'conditioner'),(mapper,'mapper')):vars(obj).clear();vars(obj).update(snapshot[key])
                        detectors.clear();detectors.update(snapshot['detectors'])
                        owner.model.active=snapshot['active'];owner.model.listening=snapshot['listening'];owner.model.processors=snapshot['processors'];owner.endpoint=snapshot['endpoint']
                        listening_history(renderer,analyzer,'restore',snapshot['target_history'])
                    else:raise ValueError('Unknown decoded-source audition action')
                    replay_start=playback_wall()-song_time
                owner.audition.register_source(decoded_audition_source)
            while not renderer.should_close():
                if controls is not None and controls.playback.paused:
                    renderer.poll_events();time.sleep(.016);continue
                if controls is not None and controls.playback.resume_fresh and result is not None:
                    result['impact']=0.
                if owner is not None:owner.audition.poll(playback_wall())
                audition=owner is not None and owner.audition.active
                if not audition and song_time >= (max_seconds or float('inf')):break
                # Frozen A/B comparisons must present every decoded chunk so
                # both trials retain identical analysis history and sample times.
                realtime=speed==1. and not comparison_label
                song_time=playback_wall()-replay_start if realtime else read_to
                if not audition and max_seconds is not None and song_time>=max_seconds:break
                new_input=False;eof=False;impact=0.;tick=False
                while frame is None or read_to<=song_time:
                    raw = audio.readframes(chunk)
                    if not raw:eof=True;break
                    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    if channels > 1:samples = samples.reshape(-1, channels)
                    renderer.consume_pcm(samples)
                    frame = (analyze_samples(samples, analyzer, processor, conditioner, detectors,
                                            descriptors=pilot, source_id=str(path), star_attack=star_pilot) if pilot or star_pilot else
                             analyze_samples(samples, analyzer, processor, conditioner, detectors))
                    if pilot: renderer.accept_planet_audio(frame, str(path))
                    if getattr(renderer,'planet_audio_tuning',None) is not None:renderer.planet_audio_tuning.observe(getattr(frame,'planet_listening',None))
                    if getattr(renderer,'studio_audio',None) is not None:renderer.studio_audio.model.observe(getattr(frame,'form_listening',None))
                    artifact=getattr(renderer,'artifact_tuning',None)
                    if artifact is not None:artifact.observe(getattr(frame,'artifacts_listening',None))
                    if star_pilot: renderer.accept_planet_star_audio(frame, str(path))
                    if getattr(renderer,'star_spectrum',None) is not None:observe_spectrum(renderer,frame,len(samples))
                    if getattr(renderer, 'planet_monitor', None) is not None:
                        renderer.planet_monitor.observe(frame, len(samples))
                    result = mapper.map_frame(frame)
                    impact=max(impact,result['impact']);tick=tick or frame.beat_tick
                    read_to+=len(samples)/rate;analyzed_frames+=1;new_input=True
                    if not realtime:break
                if eof:
                    if audition:owner.audition.return_live(time.perf_counter());continue
                    break
                renderer.parameters.scale = result["scale"]
                renderer.parameters.movement = result["movement"]
                renderer.parameters.sparkle = result["sparkle"]
                renderer.parameters.impact = impact if new_input else result["impact"]
                renderer.parameters.flux = frame.flux
                renderer.parameters.beat_confidence = frame.beat_confidence
                renderer.parameters.beat_tick = tick
                actual_state=renderer.state_at(song_time)
                active_state=next((name for name,value in LIVE_STATES.items() if value==actual_state),state)
                layer_mode, layer_mask = layers_at(renderer.layer_profiles, LIVE_STATES[active_state], song_time)
                renderer.render(elapsed_time=song_time);rendered_frames+=1
                if capture_dir is not None and song_time >= next_capture:
                    import glfw
                    width,height=glfw.get_framebuffer_size(renderer.window)
                    if capture_target is None or capture_target.size!=(width,height):
                        if capture_target is not None:capture_target.release()
                        capture_target=renderer.ctx.simple_framebuffer((width,height),components=3)
                    renderer.ctx.copy_framebuffer(capture_target,renderer.ctx.screen)
                    pixels = capture_target.read(components=3, alignment=1)
                    filename = f"frame-{song_time:08.3f}.png"
                    metadata=dict(file=filename, seconds=song_time,
                        state=active_state, flow_rate=renderer.flow_rate, planet_visits=renderer.planet_visits, blast_events=list(renderer.blast_events), world_mix=renderer.blend_values, echo_weight=renderer.echo_weight, beat_confidence=frame.beat_confidence, tempo=frame.tempo, material_mix=optional_uniform_vector(renderer.program,"u_material_mix") if actual_state not in (41,42,43) else None, shockwaves=list(renderer.shockwaves), layer_mode=layer_mode, layer_mask=layer_mask, bass=frame.bass, mids=frame.mids, highs=frame.highs,
                        flux=frame.flux, **result)
                    if pilot:
                        metadata.update(descriptors=frame.descriptors,
                                            spatial_amounts=optional_uniform_vector(renderer.program,'u_spatial_treatments'))
                    capture_writer.submit(pixels,(width,height),metadata)
                    # A delayed frame does not enqueue a burst of old captures.
                    next_capture = song_time + capture_interval
                renderer.swap_buffers()
                renderer.poll_events()
                if new_input:rows.append({"seconds": song_time, "beat_confidence": frame.beat_confidence, "tempo": frame.tempo, "echo_weight": renderer.echo_weight, "state": active_state, "shockwave_count": len(renderer.shockwaves), "blast_count": len(renderer.blast_events), "planet_visits": renderer.planet_visits, "flow_rate": renderer.flow_rate, "layer_mode": layer_mode, "layer_mask": layer_mask, "bass": frame.bass, "mids": frame.mids,
                             "highs": frame.highs, "flux": frame.flux, **result})
                if new_input and pilot:
                    rows[-1].update(descriptor_valid=frame.descriptors['valid'],
                                    descriptor_sample_seconds=frame.descriptors['analyzed_seconds'],
                                    spectral_spread=frame.descriptors['spectral_spread'],
                                    fullness=frame.descriptors['fullness'],
                                    signal_confidence=frame.descriptors['signal_confidence'],
                                    elastic_amount=(optional_uniform_vector(renderer.program,'u_spatial_treatments') or (None,None))[0],
                                    braided_amount=(optional_uniform_vector(renderer.program,'u_spatial_treatments') or (None,None))[1])
                if new_input and star_pilot:
                    flight=optional_uniform_vector(renderer.program,'u_planet_star_flight') if renderer.planet_star_attack_eligible() else None
                    rows[-1].update(bass_attack=frame.planet_star_audio['bass_attack'],
                                    star_flight_phase=flight[1] if flight else None,
                                    star_attack_envelope=flight[2] if flight else None,
                                    star_flight_available=flight is not None)
                if realtime:
                    next_present=max(next_present+1./60.,playback_wall()-replay_start)
                    delay=replay_start+next_present-playback_wall()
                else:
                    song_time=read_to;delay=replay_start+song_time/speed-playback_wall() if speed>0 else 0.
                if delay>0:time.sleep(delay)
        finally:
            if pilot:
                analyzer.reset_descriptors()
                renderer.reset_planet_dsp()
            if star_pilot:
                renderer.reset_planet_star_attack()
            if capture_target is not None:capture_target.release()
            if capture_writer is not None:capture_writer.close();captures=capture_writer.records
            rows.close()
            renderer.close()

    if capture_dir is not None:
        (capture_dir / "captures.json").write_text(json.dumps(dict(
            source=str(path), state=state, states=states, palette=palette, layers=renderer.layer_profiles, song_seconds=song_time,
            analyzed_frames=analyzed_frames, rendered_frames=rendered_frames, captures=captures,
            capture_dropped=capture_writer.dropped,capture_errors=capture_writer.errors,
            director_seed=renderer.director_seed, director_history=renderer.director_history,
            note="Decoded music through the real analysis and GPU pipeline; no audible playback."),
            indent=2), encoding="utf-8")
    return song_time, rows


def main():
    parser = argparse.ArgumentParser(description="Replay a decoded WAV through ZeraWave without audio playback.")
    parser.add_argument('--transitions',type=parse_settings)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--speed", type=float, default=12.0, help="Playback pacing multiplier (0 = no pacing).")
    parser.add_argument("--max-seconds", type=float, default=None)
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--state", choices=tuple(LIVE_STATES), default="blend")
    parser.add_argument("--capture-dir", type=Path, help="Optional song-time PNG captures and input metadata.")
    parser.add_argument("--capture-interval", type=float, default=15., help="Song seconds between captures.")
    parser.add_argument("--states", nargs="+", choices=tuple(LIVE_STATES), help="Development cycle: hold each state for 28 song seconds.")
    parser.add_argument("--layers", type=parse_layers, default={}, help="Development per-world effect settings as JSON.")
    parser.add_argument("--seed", type=int, help="Repeatable visual choices for development replay.")
    parser.add_argument("--palette", choices=("authored", "soft-dream"), default="authored",
                        help="Experimental pigment choice; only held Planet Canvas uses soft-dream.")
    parser.add_argument("--comparison-label", choices=("A", "B"), help="Studio matched replay label; locks window size.")
    parser.add_argument('--colors', type=parse_colors, default={}, help='Declared source color overrides as JSON.')
    parser.add_argument('--studio-color-input', action='store_true', help='Read bounded Studio color snapshots from stdin.')
    parser.add_argument('--galaxy-visit',type=int,default=0)
    parser.add_argument('--galaxy-short',action='store_true')
    parser.add_argument('--planet-dsp-pilot',action='store_true',help='Opt-in two-treatment DSP pilot; held Planet Canvas only.')
    parser.add_argument('--planet-star-attack-pilot',action='store_true',help='Opt-in bass-attack background flight; held Planet Canvas only.')
    args = parser.parse_args()
    seconds, rows = replay(args.wav, args.speed, args.max_seconds, args.metrics, args.state,
                           args.capture_dir, args.capture_interval, args.states, args.layers, args.seed, args.palette, args.comparison_label, args.colors, args.studio_color_input, args.galaxy_visit,args.galaxy_short, args.transitions,args.planet_dsp_pilot,args.planet_star_attack_pilot)
    print(f"Replay complete: {seconds:.1f}s song time, {len(rows)} input snapshots")


if __name__ == "__main__":
    main()
