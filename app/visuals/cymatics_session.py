"""Bounded complete preview snapshots; stored configurations always reopen muted."""
from dataclasses import asdict
from pathlib import Path
import sys,math
AUDIO=Path(__file__).resolve().parent.parent/"audio"
if str(AUDIO) not in sys.path:sys.path.insert(0,str(AUDIO))
from oscillator import config as source_config,OscillatorConfig
from frequency_bands import validate as band_config
from cymatics_view import validate_pose
from cymatics import validate as basin_config,BasinConfig
def defaults():return dict(version=1,source='oscillator',oscillator=dict(asdict(OscillatorConfig()),frequency=3.6639,sweep_end=5.7516,sweep_seconds=24.),basin=asdict(BasinConfig()),bands=band_config(),material='glass',finish='obsidian',light_angle=-.65,dye_swirl=.6,camera=validate_pose(),view_reset=0,camera_orbit=True,dye=True,dye_strength=.65,dye_reset=0,paused=False,restart=0,monitor=False,monitor_gain=.01)
def validate(data=None,stored=False):
    c=defaults();c.update(data or {})
    if set(c)!=set(defaults()) or c['version']!=1:raise ValueError('Unsupported Cymatics configuration')
    if type(c['camera_orbit']) is not bool or type(c['dye']) is not bool or type(c['dye_reset']) is not int or not 0<=c['dye_reset']<2**31:raise ValueError('Invalid camera/tracer action')
    if type(c['dye_strength']) not in (int,float) or not math.isfinite(c['dye_strength']) or not 0<=c['dye_strength']<=1:raise ValueError('Tracer strength 0-1')
    c['camera']=validate_pose(c['camera'])
    if c['finish'] not in ('obsidian','marble'):raise ValueError('Unknown basin finish')
    if type(c['view_reset']) is not int or not 0<=c['view_reset']<2**31:raise ValueError('Invalid view reset')
    for k,a,b in (('light_angle',-3.14,3.14),('dye_swirl',0.,1.)):
        if type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not a<=c[k]<=b:raise ValueError('Invalid style '+k)
    if c['source'] not in ('oscillator','track','loopback'):raise ValueError('Unknown Cymatics source')
    c['oscillator']=asdict(source_config(c['oscillator']));c['basin']=asdict(basin_config(c['basin']));c['bands']=band_config(c['bands'])
    if c['material'] not in ('glass','mercury','ink'):raise ValueError('Unknown optical material')
    if type(c['paused']) is not bool or type(c['monitor']) is not bool or type(c['restart']) is not int or not 0<=c['restart']<2**31:raise ValueError('Invalid runtime action')
    if not isinstance(c['monitor_gain'],(float,int)) or not 0<=c['monitor_gain']<=.05:raise ValueError('Monitor gain cap.05')
    if c['monitor'] and c['source']=='loopback':raise ValueError('Monitoring loopback is blocked to avoid recapture')
    if stored:c.update(monitor=False,paused=False,restart=0,dye_reset=0,view_reset=0)
    return c
