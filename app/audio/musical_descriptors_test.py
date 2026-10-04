"""CPU-only deterministic DSP fixtures and exact legacy compatibility.

No renderer/capture imports, windows, devices or GPU contexts. Optional bounded
benchmark: --output work/standalone-dsp-01/observations.json --benchmark.
"""
import argparse
import ast
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
from analyzer import AudioAnalyzer
from audio_frame import AudioFrame
from musical_descriptors import DescriptorAnalysis, MusicalDescriptors
from onset_detector import OnsetDetector
from signal_processor import SignalProcessor, VisualSignalConditioner
from frequency_bands import DEFAULT_EDGES, FrequencyBands

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'c0f82ad565e41eae29c2cd501a9e2217146d03d0'
SCALARS = tuple(DescriptorAnalysis.TIMES)


def tone(rate=48000, seconds=3, hz=1000):
    return np.sin(2 * np.pi * hz * np.arange(round(rate * seconds)) / rate)


def equal_rms(pcm, rms=.1):
    return pcm * (rms / np.sqrt(np.mean(pcm * pcm)))


def run(pcm, rate=48000, packets=(2048,)):
    analyzer = AudioAnalyzer()
    rows = []
    offset = i = 0
    while offset < len(pcm):
        end = min(len(pcm), offset + packets[i % len(packets)])
        rows.append(analyzer.describe_samples(pcm[offset:end], rate).to_dict())
        offset = end
        i += 1
    return rows, analyzer


def check_bounds(rows):
    for row in rows:
        json.dumps(row, allow_nan=False)
        assert all(0 <= row[name] <= 1 for name in SCALARS + ('signal_confidence',)), row
        assert -120 <= row['rms_dbfs'] <= 0.00001
        assert 0 <= row['pending_seconds'] <= DescriptorAnalysis.WINDOW_SECONDS


def fixtures():
    results = {}
    rate = 48000
    n = rate * 3
    rng = np.random.default_rng(901)
    sparse = equal_rms(tone())
    full = equal_rms(sum(tone(hz=f) for f in (60, 120, 240, 470, 900, 1800, 3200, 5000, 8000, 12000, 16000)))
    noise = equal_rms(rng.normal(size=n))
    t = np.arange(n) / rate
    percussion = equal_rms(tone() * (.1 + .9 * np.exp(-np.mod(t, .25) / .02)))
    for name, pcm in [('silence', np.zeros(n)), ('noise_floor', noise * .0001),
                      ('sparse', sparse), ('full', full), ('noise', noise),
                      ('percussive', percussion), ('quiet', sparse * .1),
                      ('low', equal_rms(tone(hz=120))), ('high', equal_rms(tone(hz=8000))),
                      ('crescendo', sparse * np.linspace(.02, 1, n)),
                      ('sweep', .15 * np.sin(2*np.pi*(100*t+2000*t*t)))]:
        rows, _ = run(pcm)
        check_bounds(rows)
        results[name] = dict(last=rows[-1], tail_mean={key: float(np.mean([r[key] for r in rows[len(rows)//2:]])) for key in SCALARS},
                             trace=rows[::max(1, len(rows)//16)],
                             pcm_sha256=hashlib.sha256(pcm.tobytes()).hexdigest())
    assert results['silence']['last'] == dict(MusicalDescriptors().to_dict(), analyzed_seconds=results['silence']['last']['analyzed_seconds'], pending_seconds=results['silence']['last']['pending_seconds'])
    assert not results['noise_floor']['last']['valid'] and results['noise_floor']['last']['intensity'] == 0
    assert abs(results['sparse']['last']['intensity'] - results['full']['last']['intensity']) < .005
    assert results['full']['last']['fullness'] > results['sparse']['last']['fullness'] + .4
    assert results['noise']['last']['spectral_flatness'] > results['sparse']['last']['spectral_flatness'] + .4
    assert results['sparse']['last']['tonal_concentration'] > results['noise']['last']['tonal_concentration'] + .8
    assert results['percussive']['tail_mean']['transient_activity'] > results['sparse']['tail_mean']['transient_activity'] + .15
    assert results['high']['last']['brightness'] > results['low']['last']['brightness'] + .3
    assert results['sweep']['trace'][-1]['brightness'] > results['sweep']['trace'][2]['brightness'] + .2
    assert results['crescendo']['trace'][-1]['intensity'] > results['crescendo']['trace'][2]['intensity'] + .15
    assert results['sparse']['last']['intensity'] > results['quiet']['last']['intensity'] + .25
    assert results['noise']['tail_mean']['transient_activity'] < results['percussive']['tail_mean']['transient_activity']
    # Existing twelve-band summaries/ranges still describe the same FFT. New
    # occupancy uses their boundaries, not a second conditioned meter/routing.
    for index, (low, high) in enumerate(zip(DEFAULT_EDGES, DEFAULT_EDGES[1:])):
        hz = np.sqrt(low*high)
        pcm = .15*tone(seconds=1,hz=hz)
        rows, _ = run(pcm)
        assert abs(rows[-1]['brightness']-hz/20000) < .006
        assert rows[-1]['fullness'] < .15
        analyzer = AudioAnalyzer()
        f,m = analyzer.spectrum(pcm[:2048])
        bands = FrequencyBands().summarize(f,m,2048)
        if not bands['unresolved'][index]: assert np.argmax(bands['raw']) == index
    # Shape/transient invariance under constant gain above the noise floor.
    for pcm in (sparse, full, noise, percussion):
        loud, _ = run(pcm)
        quiet, _ = run(pcm * .1)
        for a, b in zip(loud, quiet):
            for key in SCALARS:
                if key != 'intensity':
                    assert abs(a[key] - b[key]) < 1e-10, (key, a[key], b[key])
    # Exact final sample-clock state for different packet partitions.
    combined = np.concatenate((sparse, full, percussion, np.zeros(rate)))
    expected, _ = run(combined)
    for packets in ((1, 137, 4097, 509), (1600,), (800,), (333,), (len(combined),)):
        actual, analyzer = run(combined, packets=packets)
        assert actual[-1] == expected[-1], packets
        assert analyzer._descriptors.filled < analyzer._descriptors.size
        assert analyzer._descriptors.buffer.shape == (2048, 1)
    # Formats and channel energy including opposite stereo phase.
    for rate in (8000, 16000, 32000, 44100, 48000, 96000):
        pcm = equal_rms(tone(rate))
        a, _ = run(pcm, rate)
        for channels in (1, 2, 8):
            stereo = np.column_stack([pcm * (-1 if c % 2 else 1) for c in range(channels)])
            b, _ = run(stereo, rate, (7, 2048, 113))
            assert abs(a[-1]['intensity'] - b[-1]['intensity']) < 1e-12
            assert abs(a[-1]['brightness'] - b[-1]['brightness']) < 1e-12
            check_bounds(b)
        assert abs(a[-1]['brightness'] - 1000/min(rate/2, 20000)) < .005
    # Release, a single transient, end/reset, source/format change and rejection.
    analyzer = AudioAnalyzer()
    analyzer.describe_samples(percussion)
    release = []
    for _ in range(120):
        release.append(analyzer.describe_samples(np.zeros(2048)).to_dict())
    assert max(release[-1][k] for k in SCALARS) < 1e-5
    assert all(a['transient_activity'] >= b['transient_activity'] for a,b in zip(release[2:],release[3:]))
    impulse = np.zeros(rate * 2); impulse[rate//2] = .9
    rows, _ = run(impulse)
    assert max(r['transient_activity'] for r in rows) > .2
    assert rows[-1]['transient_activity'] < .02
    results['release'] = dict(trace=release[::8], last=release[-1])
    analyzer.reset_descriptors()
    assert analyzer.describe_samples(np.zeros(0)) == MusicalDescriptors()
    first = analyzer.describe_samples(sparse[:2048])
    assert first.transient_activity == 0
    for args in ((sparse[:10],48000,'other'), (sparse[:10],44100,'other'), (np.column_stack((sparse[:10],sparse[:10])),44100,'other')):
        fresh = analyzer.describe_samples(*args)
        assert not fresh.valid and fresh.intensity == 0 and fresh.transient_activity == 0
    before = analyzer._descriptors.snapshot
    for pcm, rate in ((np.array([np.nan]),48000),(np.array([np.inf]),48000),(np.array([2.]),48000),(np.zeros((3,0)),48000),(np.zeros((3,9)),48000),(np.zeros((3,1,1)),48000),(np.zeros(2),0),(np.zeros(2),48000.0),(np.array([32767],np.int16),48000)):
        try: analyzer.describe_samples(pcm,rate)
        except ValueError: pass
        else: raise AssertionError('Invalid PCM/format accepted')
        assert analyzer._descriptors.snapshot is before
    # Bounded state after a 60-second numeric continuation, not multi-hour evidence.
    d = DescriptorAnalysis()
    block = np.zeros((2048,8))
    for _ in range(1407): d.process(block)
    assert d.buffer.nbytes == 2048*8*8 and d.previous_shape is None
    assert set(d.values) == set(SCALARS)
    results['bounded_synthetic_seconds'] = 1407*2048/48000
    return results


def legacy_function(text, namespace):
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'analyze_samples')
    exec(compile(ast.Module(body=[node],type_ignores=[]), 'source-bound-analyze_samples', 'exec'), namespace)
    return namespace['analyze_samples']


def compatibility():
    def original(path):
        return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT).decode('utf-8')
    old_ns = {}
    exec(original('app/audio/analyzer.py'), old_ns)
    exec(original('app/audio/audio_frame.py'), old_ns)
    current_ns = dict(AudioFrame=AudioFrame)
    before = legacy_function(original('app/visuals/live_visual_test.py'), old_ns)
    after = legacy_function((ROOT/'app/visuals/live_visual_test.py').read_text(),current_ns)
    def state(cls):
        return cls(),SignalProcessor(.5),VisualSignalConditioner(quiet_threshold=.06),{k:OnsetDetector(.2) for k in ('bass','mids','highs')}
    a=state(old_ns['AudioAnalyzer']);b=state(AudioAnalyzer)
    rng=np.random.default_rng(7301)
    golden=json.loads((ROOT/'app/visuals/cymatics_legacy_fixture.json').read_text())
    for i in range(240):
        pcm=np.zeros(2048) if i>48 else rng.normal(size=2048)*(.001 if i%3==0 else .12)
        if i%2: pcm=np.column_stack((pcm,pcm))
        # Explicit opt-in must also leave old FFT/flux/band/beat state untouched.
        b[0].describe_samples(pcm)
        left=before(pcm,*a);right=after(pcm,*b)
        assert set(right.__dict__) == set(left.__dict__) | {'descriptors'}
        for key,value in left.__dict__.items():
            actual=getattr(right,key)
            if isinstance(value,np.ndarray):assert np.array_equal(value,actual),key
            else: assert value==actual,(i,key,value,actual)
        if i<len(golden['rows']):
            assert [getattr(right,k) for k in golden['keys']] == golden['rows'][i]
    frame=AudioFrame(.5,.4,.3,.2,.1,0.)
    assert frame.rhythmic_activity == frame.impact == .2 and frame.descriptors is None
    stored=json.loads(json.dumps(frame.__dict__,allow_nan=False))
    assert stored['energy']==frame.energy and stored['descriptors'] is None
    old=old_ns['AudioFrame'](.5,.4,.3,.2,.1,0.)
    import sys
    sys.path.insert(0,str(ROOT/'app/visuals'))
    from parameter_mapper import VisualParameterMapper
    mapper=VisualParameterMapper()
    assert mapper.map_frame(frame)==mapper.map_frame(old)
    attached=AudioFrame(.5,.4,.3,.2,.1,0.,descriptors=MusicalDescriptors().to_dict())
    assert json.loads(json.dumps(attached.__dict__))['descriptors']['version']==1
    assert mapper.map_frame(attached)==mapper.map_frame(old)
    return dict(exact_baseline_frames=240,golden_frames=len(golden['rows']),baseline=BASELINE,
                old_constructor=True,plain_json_default_and_attached=True,legacy_mapper_unchanged=True,
                analysis_loaded_via_ast='Exact function compiled; no UI/renderer/capture imports')


def benchmark():
    # Wall timer around each PCM call, including validation, buffering, FFT,
    # descriptors and snapshot construction. No pacing or capture/device costs.
    rng=np.random.default_rng(93)
    arms=[]
    for rate,channels in ((48000,1),(48000,2),(44100,2),(96000,8)):
        size=round(rate*2048/48000)
        pcm=rng.normal(0,.05,(size,channels))
        d=DescriptorAnalysis()
        for _ in range(20): d.process(pcm,rate)
        costs=[]
        for _ in range(300):
            start=time.perf_counter_ns();d.process(pcm,rate);costs.append((time.perf_counter_ns()-start)/1e6)
        arms.append(dict(rate=rate,channels=channels,packet_frames=size,samples=300,
                         block_duration_ms=1000*size/rate,median_ms=float(np.median(costs)),
                         p95_ms=float(np.percentile(costs,95)),p99_ms=float(np.percentile(costs,99)),max_ms=max(costs)))
    return dict(method='20 warm-up + 300 wall-clock samples per format; whole DescriptorAnalysis.process; deterministic noise seed93',
                python=platform.python_version(),numpy=np.__version__,processor=platform.processor(),arms=arms,
                uncertainty='ComfyUI/voice/background load, scheduling, thermal and power conditions uncontrolled; no hard latency guarantee or live capture measurement')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);parser.add_argument('--benchmark',action='store_true');args=parser.parse_args()
    report=dict(evidence_class='offline deterministic synthetic CPU',fixtures=fixtures(),compatibility=compatibility())
    if args.benchmark:report['cpu']=benchmark()
    if args.output:args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('PASS: deterministic contrasts, gain, partitions, rates/channels, quiet/release, reset, bounded state and exact legacy compatibility')
    for name in ('sparse','full','noise','percussive'):
        r=report['fixtures'][name]['last'];print(name,{k:round(r[k],4) for k in SCALARS})
    if args.benchmark:print(json.dumps(report['cpu'],indent=2))


if __name__=='__main__':main()
