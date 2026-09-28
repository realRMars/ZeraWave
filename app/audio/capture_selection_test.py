from types import SimpleNamespace
from unittest.mock import patch
from capture import AudioCapture

mic=SimpleNamespace(id='mic',name='Shared name',isloopback=False)
output=SimpleNamespace(id='out',name='Shared name',isloopback=True)
with patch('capture.sc.all_microphones',return_value=[mic,output]), patch('capture.sc.default_speaker',return_value=output):
    assert AudioCapture().find_device() is output
    assert AudioCapture('out').find_device() is output
    try:AudioCapture('missing').find_device()
    except RuntimeError:pass
    else:raise AssertionError('Missing device silently substituted')
print('PASS: output-only selection, default/exact ID, missing-device error')
