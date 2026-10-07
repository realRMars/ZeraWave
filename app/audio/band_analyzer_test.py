"""Standalone synthetic display/owner checks; no real device or audible output."""
import json,time
from unittest.mock import patch
import numpy as np
from band_display import AnalyzerSpectrum
from musical_descriptors_test import display_fixtures
from studio_transport import AudioOwner,RATE
from studio_transport_test import Enumeration,wait


def run():
    display_fixtures() # Existing 12-band calibration and release remain intact.
    n=2048;t=np.arange(8192)/RATE
    for frequency in (62.5,100.,234.375,1007.8125,8015.625,16007.8125):
        mono=.1*np.sin(2*np.pi*frequency*t);packets=[]
        for sign in (1,-1):
            analysis=AnalyzerSpectrum()
            for start in range(0,8192,n):packet=analysis.summarize(np.column_stack((mono[start:start+n],sign*mono[start:start+n])))
            packets.append(packet)
        assert packets[0]==packets[1]
        for size in (31,63):
            group=packets[0]['groups'][str(size)];index=np.argmax(group['power'])
            assert group['edges'][index]<=frequency<group['edges'][index+1],(size,frequency,index)
            assert abs(10*np.log10(sum(group['power'])/(.1**2/2)))<.6,(size,frequency)
            assert group['edges'][0]==20 and group['edges'][-1]==20000
            assert group['unresolved'][0] and len(group['power'])==size
        assert packet['resolution_hz']==23.4375 and packet['low_resolution_hz']==5.859375
    cached=analysis.geometry(8192);analysis.summarize(np.zeros((n,2)));assert analysis.geometry(8192) is cached
    quiet=AnalyzerSpectrum();assert not any(quiet.summarize(np.zeros((n,2)))['groups']['63']['power'])
    rng=np.random.default_rng(17);broad=AnalyzerSpectrum()
    for _ in range(4):packet=broad.summarize(rng.normal(0,.1,(n,2)))
    assert all(v>0 for v in packet['groups']['31']['power'][:12])
    assert all(v>0 for v in packet['groups']['63']['power'][:24]) # No structural empty-bin gaps.
    lower=AnalyzerSpectrum().summarize(np.zeros((2048,2)),16000)
    assert lower['groups']['63']['bins'][-1]==0 and lower['groups']['63']['unresolved'][-1]
    assert all(np.isfinite(AnalyzerSpectrum().summarize(np.zeros((1,2)))['groups']['31']['power']))
    for invalid in (np.zeros((2049,2)),np.array([[float('nan')]])):
        try:analysis.summarize(invalid)
        except ValueError:pass
        else:raise AssertionError('Invalid samples accepted')
    analysis.reset();assert analysis.count==0 and analysis.buffer is None and len(analysis.cache)<=8
    owner=AudioOwner(enumerator=Enumeration())
    try:
        pcm=np.column_stack((mono[:n],mono[:n])).astype(np.float32)
        with patch.object(owner.analyzer_spectrum,'snapshot',wraps=owner.analyzer_spectrum.snapshot) as transform:
            owner.publish(pcm);assert transform.call_count==0 and owner.snapshot()['band_analyzer'] is None
            owner.submit('analyzer',value=True);wait(lambda:owner.snapshot()['analyzer_enabled'])
            for _ in range(4):
                time.sleep(.04);owner.publish(pcm)
            first=owner.snapshot()['band_analyzer'];assert transform.call_count==4 and first['low_frames']==8192
            for _ in range(10):owner.publish(pcm)
            assert transform.call_count==4 and owner.snapshot()['band_analyzer']==first
            time.sleep(.04);owner.publish(pcm);assert transform.call_count==5
            owner.submit('mute',value=True);owner.submit('volume',value=.05);owner.submit('raw_waveform',value=True)
            wait(lambda:owner.snapshot()['raw_waveform']);time.sleep(.22);owner.publish(pcm)
            assert owner.snapshot()['band_analyzer']['groups']==first['groups']
            assert len(json.dumps(first))<20000 and 'band_analyzer' not in owner.metadata()
            generation=owner.snapshot()['generation'];owner.change(mode='Audio File');owner.act('pause',{})
            held=owner.snapshot()['band_analyzer'];assert held['held'] and held['origin_generation']==generation
            assert held['generation']==owner.snapshot()['generation'] and held['groups']==first['groups']
            owner.boundary();assert owner.snapshot()['band_analyzer'] is None
            owner.publish(pcm);assert owner.snapshot()['band_analyzer']['generation']==owner.snapshot()['generation']
            owner.submit('analyzer',value=False);wait(lambda:not owner.snapshot()['analyzer_enabled'])
            count=transform.call_count;time.sleep(.22);owner.publish(pcm)
            assert transform.call_count==count and owner.snapshot()['band_analyzer'] is None
            try:owner.submit('analyzer',value=1)
            except ValueError:pass
            else:raise AssertionError('Nonboolean enable accepted')
        assert owner.capture is None and owner.output is None
    finally:owner.close()
    assert not owner.worker.is_alive() and not owner.server.is_alive()
    print('PASS: 31/63 dual-resolution fractional-bin bands, tone locations, phase, silence, Nyquist/FFT limits, no empty low-bin gaps, bounded bass window/cache; visibility/throttle, unchanged volume/mute/raw input, source generation and bounded packet. Existing 12-band fixtures passed. No devices/output.')


if __name__=='__main__':run()
