"""Versioned derived audio contribution/coverage, bound to one owner snapshot.

No decode, file scan, device, cache, authoring operation or measured loudness.
Canonical Mixer factors are reused. Range checkpoints are not extrema.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
import numpy as np
from video_project import fields, integer, identity, rational, pair, sample_at, duration, fail
from project_audio_graph import plan as graph_plan
from project_audio_timing import natural_duration, ceiling
from project_mix_factors import curve, curve_factors, clip_curve, balance_pcm, eligible, RATE

MAX_WORK = 32768

def availability_key(document, media_state, clip_ids=()):
    tracks = {t['id'] for t in document.get('tracks', []) if t['kind'] == 'audio'}
    assets = {c['asset'] for c in document.get('clips', []) if c['track'] in tracks and (not clip_ids or c['id'] in clip_ids)}
    rows = [dict(id=a['id'], sha256=a['sha256'], validation=media_state.get(a['id'], dict(status='Unknown')))
            for a in document.get('media', []) if a['id'] in assets]
    return hashlib.sha256(json.dumps(sorted(rows, key=lambda a:a['id']), sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def level(value):
    value = float(value)
    return dict(linear=value, db=20 * math.log10(value) if value > 0 else None,
                db_text=f'{20 * math.log10(value):.6f} dB' if value > 0 else '-infinity dB')

def merge(intervals):
    result = []
    for left, right in sorted(intervals):
        if right <= left:
            continue
        if result and left <= result[-1][1]:
            result[-1][1] = max(right, result[-1][1])
        else:
            result.append([left, right])
    return result

def gaps(intervals, left, right):
    result = []
    for start, end in merge(intervals):
        if start > left:
            result.append([left, start])
        left = max(left, end)
    if left < right:
        result.append([left, right])
    return result

def source_extent(asset):
    meta = asset['metadata']
    end = Fraction(ceiling(natural_duration(meta) * RATE), RATE)
    return Fraction(0), end

def source_span(document, clip, asset, left, right):
    fps = rational(document['settings']['fps']); speed = rational(clip['rate'])
    origin = Fraction(clip['start']) * RATE / fps
    first, last = source_extent(asset)
    source = rational(clip['source_in'])
    return max(left, ceiling(origin + (first - source) * RATE / speed)), min(right, ceiling(origin + (last - source) * RATE / speed))

def item_for(document, clip, track, asset):
    fades = [dict(start=t['start'], duration=t['duration'], side=i)
             for t in document.get('transitions', []) for i, key in enumerate(t['audio']) if key == clip['id']]
    return dict(clip=clip, track=track, asset=asset, transition_fades=fades)

def channel_factors(item, samples, fps, end, tracks, buses, master):
    """Same multiplication/float32 ordering as Mixer, for a unity source."""
    clip = item['clip']; track = item['track']; frames = samples / RATE * float(fps)
    gains = clip_curve(item, samples, fps)
    pcm = np.ones((len(samples), 2), np.float32)
    if not eligible(track, tracks, buses):
        return pcm * 0
    pcm *= gains[:, None]; balance_pcm(pcm, clip['audio'].get('pan', 0.))
    pcm *= curve(track['audio'], frames, end)[:, None]; balance_pcm(pcm, track['audio'].get('pan', 0.))
    destination = track.get('output', 'master')
    if destination != 'master':
        bus = buses.get(destination)
        if bus is None:
            return pcm * 0
        pcm *= 0. if bus['mute'] else bus['gain']; balance_pcm(pcm, bus['balance'])
        if bus['output'] != 'master':
            return pcm * 0
    pcm *= 0. if master['mute'] else master['gain']
    return pcm

def factors(recipe, frame, length):
    env = recipe['envelope']
    envelope = float(np.interp(float(frame), [p[0] for p in env], [p[1] for p in env])) if env else 1.
    return dict(gain=level(recipe['gain']), fade_in=float(np.clip(float(frame) / recipe['fade_in'], 0, 1)) if recipe['fade_in'] else 1.,
                fade_out=float(np.clip((length - float(frame)) / recipe['fade_out'], 0, 1)) if recipe['fade_out'] else 1.,
                envelope=level(envelope), mute=recipe['mute'], pan=recipe.get('pan', 0.), coordinate=pair(frame),
                window_length=length, combined=level(curve(recipe, np.asarray([float(frame)]), length)[0]))

def trace(document, item, sample, graph, media_state):
    clip = item['clip']; track = item['track']; asset = item['asset']; fps = rational(document['settings']['fps'])
    frame = Fraction(sample) * fps / RATE; local = frame - clip['start'] + clip['audio_window']['offset']
    tracks = {t['id']: t for t in graph['tracks']}; buses = {b['id']: b for b in graph['buses']}
    destination = track.get('output', 'master'); bus = buses.get(destination); gates = []
    if not sample_at(document, clip['start']) <= sample < sample_at(document, clip['start'] + clip['duration']):
        gates.append('absent_clip')
    source = rational(clip['source_in']) + (Fraction(sample, RATE) - Fraction(clip['start']) / fps) * rational(clip['rate'])
    lo, hi = source_extent(asset)
    if not lo <= source < hi:
        gates.append('intentional_end_padding' if clip.get('pad_end') == 'silence' else 'outside_declared_source')
    status = media_state.get(asset['id'], {}).get('status', 'Unknown')
    if status != 'Ready':
        gates.append('source_unavailable' if status != 'Unknown' else 'source_availability_unverified')
    if asset['kind'] == 'Video' and not asset['metadata'].get('has_audio'):
        gates.append('source_has_no_audio')
    if clip['audio']['mute']: gates.append('clip_mute')
    if track['audio']['mute']: gates.append('track_mute')
    if not track['audio']['mute'] and not eligible(track, tracks, buses): gates.append('solo_exclusion')
    if destination is None: gates.append('track_output_none')
    elif destination != 'master' and bus is None: gates.append('missing_route')
    if bus:
        if bus['mute']: gates.append('bus_mute')
        if bus['output'] is None: gates.append('bus_output_none')
    if graph['master']['mute']: gates.append('master_mute')
    if graph['missing']: gates.append('mix_blocked_missing_route')
    multipliers = channel_factors(item, np.asarray([sample]), fps, duration(document), tracks, buses, graph['master'])[0]
    if not np.any(multipliers) and not gates: gates.append('authored_zero_gain_or_envelope')
    transition = []
    for fade in item['transition_fades']:
        phase = float(np.clip((float(frame) - fade['start']) / fade['duration'], 0., 1.))
        transition.append(dict(**fade, factor=phase if fade['side'] == 1 else 1. - phase))
    return dict(sample=sample, sequence_frame=pair(frame), source_seconds=pair(source),
                clip_local_frame=pair(local), clip=factors(clip['audio'], local, clip['audio_window']['duration']),
                track=factors(track['audio'], frame, duration(document)), transitions=transition,
                bus=deepcopy(bus), bus_gain=level(bus['gain']) if bus else None, master=deepcopy(graph['master']), master_gain=level(graph['master']['gain']), gates=gates,
                channel_multiplier=[level(v) for v in multipliers],
                routed_channel_multiplier=[level(0 if gates else v) for v in multipliers],
                contribution='excluded' if gates else 'routed; actual source signal unmeasured',
                pcm_measurement=dict(status='not_measured', decoded_silence='unverified', level_dbfs=None))

def positive_spans(document, item, left, right, graph, work):
    if right <= left or graph['missing']: return []
    clip = item['clip']; track = item['track']; fps = rational(document['settings']['fps']); end = duration(document)
    # Between these knots every nonnegative scalar is affine (or constant).
    # Isolate integer neighbours of each rational boundary. Every individual
    # factor is affine inside each interval, so endpoint minima give a lower
    # bound. Rare float32 underflow intervals require exact bounded samples.
    points = [Fraction(clip['start'] - clip['audio_window']['offset'] + p[0]) for p in clip['audio']['envelope']]
    for recipe, origin, length in [(clip['audio'], clip['start'] - clip['audio_window']['offset'], clip['audio_window']['duration']), (track['audio'], 0, end)]:
        points.extend(Fraction(origin + x) for x in [0, recipe['fade_in'], length - recipe['fade_out'], length])
    points.extend(Fraction(p[0]) for p in track['audio']['envelope'])
    for fade in item['transition_fades']: points.extend([Fraction(fade['start']), Fraction(fade['start'] + fade['duration'])])
    cuts = {left, right}
    for point in points:
        value = point * RATE / fps; at = value.numerator // value.denominator
        cuts.update(x for x in (at, at + 1, at + 2) if left < x < right)
    cuts = sorted(cuts); count = len(cuts) - 1; work[0] += count
    if work[0] > MAX_WORK: fail('inspection_capacity', 'Audio coverage exceeds 32768 analytic spans; narrow the requested tracks/sources/range. No partial report was published.')
    tracks={t['id']:t for t in graph['tracks']};buses={b['id']:b for b in graph['buses']};destination=track.get('output','master');bus=buses.get(destination)
    if not eligible(track,tracks,buses) or destination is None or bus and bus['output'] is None:return []
    endpoints=np.asarray([x for a,b in zip(cuts,cuts[1:]) for x in (a,b-1)])
    frames=endpoints/RATE*float(fps);local=(endpoints/RATE-float(Fraction(clip['start'])/fps))*float(fps)+clip['audio_window']['offset']
    parts=curve_factors(clip['audio'],local,clip['audio_window']['duration'])+curve_factors(track['audio'],frames,end)
    for fade in item['transition_fades']:
        phase=np.clip((frames-fade['start'])/fade['duration'],0.,1.);parts.append(phase if fade['side']==1 else 1.-phase)
    low=np.prod([v.reshape(-1,2).min(axis=1) for v in parts],axis=0);high=np.prod([v.reshape(-1,2).max(axis=1) for v in parts],axis=0)
    balance=np.ones((1,2),np.float32);balance_pcm(balance,clip['audio'].get('pan',0.));balance_pcm(balance,track['audio'].get('pan',0.))
    constant=0. if graph['master']['mute'] else graph['master']['gain']
    if bus:
        constant*=0. if bus['mute'] else bus['gain'];balance_pcm(balance,bus['balance'])
    channel=max(balance[0])*constant;low*=channel;high*=channel
    result=[]
    for index,(a,b) in enumerate(zip(cuts,cuts[1:])):
        if high[index]<=0:continue
        if low[index]>=np.finfo(np.float32).tiny:
            result.append([a,b]);continue
        count=b-a;work[0]+=count
        if work[0]>MAX_WORK:fail('inspection_capacity','Exact float32 zero/underflow coverage exceeds the bounded work limit; narrow the requested range. No partial report or edit was published.')
        samples=np.arange(a,b);values=channel_factors(item,samples,fps,end,tracks,buses,graph['master']);positive=np.any(values>0,axis=1)
        edges=np.flatnonzero(np.diff(np.r_[False,positive,False])).reshape(-1,2)
        result.extend([[a+int(x),a+int(y)] for x,y in edges])
    return merge(result)

def inspect_audio(document, epoch, revision, query, media_state, cancel=None):
    def check():
        if cancel is not None and cancel.is_set():fail('cancelled','Audio inspection cancelled; no document edit or report was published.')
    check()
    fields(query, ('op', 'expected_epoch', 'expected_revision', 'expected_project'),
           ('expected_command', 'frame', 'sample', 'range', 'tracks', 'sources', 'clips', 'offset', 'limit'))
    if document is None: fail('no_project', 'Create/open a video project before inspecting audio.')
    end = duration(document); total = sample_at(document, end)
    if sum(key in query for key in ('frame', 'sample', 'range')) != 1: fail('inspection_range', 'Choose exactly one frame, canonical sample or exclusive frame range.')
    if 'range' in query:
        values = query['range']
        if not isinstance(values, list) or len(values) != 2: fail('inspection_range', 'Range is [In, exclusive Out].')
        a = integer(values[0], 0, end); b = integer(values[1], a + 1, end); left, right = sample_at(document, a), sample_at(document, b)
    else:
        left = integer(query['sample'], 0, max(0, total - 1)) if 'sample' in query else sample_at(document, integer(query['frame'], 0, max(0, end - 1)))
        right = min(total, left + 1)
    graph = graph_plan(document); tracks = {t['id']: t for t in graph['tracks']}; assets = {a['id']: a for a in document['media']}
    filters = {}
    for key, valid in [('tracks', set(tracks)), ('sources', set(assets)), ('clips', {c['id'] for c in document['clips'] if c['track'] in tracks})]:
        value = query.get(key, [])
        if not isinstance(value, list) or len(value) > 128 or len(set(value)) != len(value): fail('inspection_selection', 'Inspection selectors contain at most 128 distinct IDs.')
        if any(identity(v) not in valid for v in value): fail('inspection_selection', 'A selected audio track/source/clip no longer exists.')
        filters[key] = set(value)
    chosen_tracks = [t for t in graph['tracks'] if not filters['tracks'] or t['id'] in filters['tracks']]
    chosen = [c for c in document['clips'] if c['track'] in {t['id'] for t in chosen_tracks} and (not filters['sources'] or c['asset'] in filters['sources']) and (not filters['clips'] or c['id'] in filters['clips'])]
    offset = integer(query.get('offset', 0), 0, len(chosen)); limit = integer(query.get('limit', 64), 1, 128)
    work = [0]; rows = []; coverage = []
    for track in chosen_tracks:
        check()
        declared = []; available = []; routed = []; unverified = []
        for clip in (c for c in chosen if c['track'] == track['id']):
            check()
            a = max(left, sample_at(document, clip['start'])); b = min(right, sample_at(document, clip['start'] + clip['duration']))
            if b <= a: continue
            asset = assets[clip['asset']]; item = item_for(document, clip, track, asset); declared.append([a, b]); first, last = source_span(document, clip, asset, a, b)
            status = media_state.get(asset['id'], {}).get('status', 'Unknown')
            if status == 'Ready' and not (asset['kind'] == 'Video' and not asset['metadata'].get('has_audio')):
                available.append([first, last]); routed.extend(positive_spans(document, item, first, last, graph, work))
            elif status == 'Unknown': unverified.append([first, last])
        coverage.append(dict(track_id=track['id'], name=track['name'], declared=merge(declared), source_available=merge(available), source_uncovered=gaps(available, left, right), routed_nonzero_multiplier=merge(routed), routed_uncovered=gaps(routed, left, right), availability_unverified=merge(unverified),gates=['absent_clip'] if not declared else [],coverage_basis='Declared canonical source extents and last owner validation; embedded stream packet gaps unmeasured'))
    overlapping = [c for c in chosen if sample_at(document, c['start']) < right and sample_at(document, c['start'] + c['duration']) > left]
    for clip in overlapping[offset:offset + limit]:
        check()
        track = tracks[clip['track']]; asset = assets[clip['asset']]; item = item_for(document, clip, track, asset)
        a = max(left, sample_at(document, clip['start'])); b = min(right, sample_at(document, clip['start'] + clip['duration']))
        points = sorted({a, (a + b - 1) // 2, b - 1})
        rows.append(dict(clip_id=clip['id'], name=clip['name'], track_id=track['id'], source=dict(id=asset['id'], name=asset['name'], sha256=asset['sha256'], metadata=deepcopy(asset['metadata']), availability=deepcopy(media_state.get(asset['id'], dict(status='Unknown')))),
                         authored=dict(source_in=deepcopy(clip['source_in']), rate=deepcopy(clip['rate']), sequence_frames=[clip['start'], clip['start'] + clip['duration']], audio_window=deepcopy(clip['audio_window']), clip_audio=deepcopy(clip['audio']), track_audio=deepcopy(track['audio']), output=track.get('output','master'), provenance=deepcopy(clip.get('provenance',{}))),
                         observations=[trace(document,item,s,graph,media_state) for s in points]))
    next_offset = offset + len(rows) if offset + len(rows) < len(overlapping) else None
    report = dict(format='zerawave-audio-inspection', version=1, project=document['id'], epoch=epoch, revision=revision,
                  request=deepcopy({k:v for k,v in query.items() if not k.startswith('expected_') and k!='op'}), sample_range=[left,right], sample_rate=RATE, fps=deepcopy(document['settings']['fps']),
                  availability_sha256=availability_key(document, media_state, [c['id'] for c in chosen]), graph=graph, mix_state='blocked_missing_route' if graph['missing'] else 'derived_only_not_measured',coverage=coverage, contributions=rows, next_offset=next_offset, total_contributions=len(overlapping),
                  conditions=dict(basis='Derived authored multipliers, not dBFS/RMS/loudness/audibility. Per-channel balance is not a scalar gain; sources sum in Mixer.', coverage='Exact canonical integer sample intervals under declared metadata; owner availability is last verification. Embedded stream gaps and actual silence are unmeasured.', checkpoints='First/middle/last overlapping samples only; no extrema or range loudness claim.', device_volume='Outside rendered mix', decoded_pcm='Not measured; no decoder or output device accessed', work_spans=work[0], max_work_spans=MAX_WORK),
                  document_sha256=hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    if len(json.dumps(report,ensure_ascii=False).encode()) > 1024*1024: fail('inspection_capacity','Inspection reply exceeds 1 MiB; narrow selectors/page. Nothing was edited.')
    return report

def readable_intervals(intervals, report):
    if not intervals: return 'none'
    fps = rational(report['fps'])
    def at(sample):
        seconds = Fraction(sample, RATE); frames = seconds * fps
        return f'{float(seconds):.3f}s (frame {float(frames):.6g})'
    return '; '.join(at(a)+' to '+at(b)+' exclusive' for a,b in intervals)

def describe(report):
    tracks = {t['id']:t['name'] for t in report['graph']['tracks']}
    sample=report['sample_range'][0]
    position=('Requested interval: '+readable_intervals([report['sample_range']],report) if 'range' in report['request']
              else f"Position: {sample/RATE:.3f}s · frame {float(Fraction(sample,RATE)*rational(report['fps'])):.6g}")
    lines = ['Audio gain and coverage · revision '+str(report['revision']),
             position,
             'Derived gain; decoded silence and loudness are unmeasured. Source availability is the bound owner verification, without a new file scan.']
    for row in report['coverage']:
        lines.extend(['\n'+row['name'],
                      'Source available: '+readable_intervals(row['source_available'],report),
                      'Source gaps: '+readable_intervals(row['source_uncovered'],report),
                      'Nonzero routed gain: '+readable_intervals(row['routed_nonzero_multiplier'],report),
                      'Routed gaps: '+readable_intervals(row['routed_uncovered'],report)])
    if not report['contributions']:lines.append('No selected audio clip covers this interval; a higher fader cannot fill missing source coverage.')
    for row in report['contributions']:
        lines.append(f"\n{row['name']} · {tracks[row['track_id']]} · source {row['source']['name']}")
        for point in row['observations']:
            clip=point['clip']; track=point['track']; bus=point['bus']; master=point['master']
            lines.extend([f"At {point['sample']/RATE:.3f}s · source {float(Fraction(*point['source_seconds'])):.6g}s · clip-local frame {float(Fraction(*point['clip_local_frame'])):.6g}",
                          f"Clip {clip['gain']['linear']:.9g} ({clip['gain']['db_text']}), envelope {clip['envelope']['linear']:.9g} ({clip['envelope']['db_text']}), fades {clip['fade_in']:.6g}/{clip['fade_out']:.6g}, pan {clip['pan']:.4g}, transitions {[t['factor'] for t in point['transitions']]}",
                          f"Track {track['gain']['linear']:.9g} ({track['gain']['db_text']}), envelope {track['envelope']['linear']:.9g} ({track['envelope']['db_text']}), fades {track['fade_in']:.6g}/{track['fade_out']:.6g}, pan {track['pan']:.4g}",
                          f"Bus {bus['name']+': '+str(bus['gain'])+' ('+point['bus_gain']['db_text']+'), balance '+str(bus['balance']) if bus else row['authored']['output']} · Master {master['gain']} ({point['master_gain']['db_text']}) mute={master['mute']}",
                          'Authored L/R '+ ' / '.join(f"{v['linear']:.9g} ({v['db_text']})" for v in point['channel_multiplier']),
                          'Routed L/R '+ ' / '.join(f"{v['linear']:.9g} ({v['db_text']})" for v in point['routed_channel_multiplier']),
                          'Gates: '+(', '.join(point['gates']) or 'none; decoded signal unmeasured')])
    if report['next_offset'] is not None: lines.append(f"More contributions: query offset {report['next_offset']} (coverage includes all selected items).")
    lines.append(report['conditions']['coverage'])
    return '\n'.join(lines)
