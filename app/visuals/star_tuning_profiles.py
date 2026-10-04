"""Target-scoped authored settings, named profiles and temporary live overrides.

Persistence is target-scoped and atomic. It never opens an audio device.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from band_attack_tuning import validate, window_settings, PRESENTATION_BOUNDS
from spectral_listening import listening_defaults,require_listening_bins as require_windows_bins

TARGET='planet.starfield'
LEGACY_SHIPPED=dict(enabled=True,mode='window',start_hz=80.,end_hz=130.,weight=1.5,sensitivity=2.)
SHIPPED=dict(LEGACY_SHIPPED,**{key:1. for key in PRESENTATION_BOUNDS})
PRE_LISTENING_SHIPPED=dict(SHIPPED)
SHIPPED.update(listening_defaults(('flux','sparkle','impact')))
AUTHORED_PATH=Path(__file__).with_name('starfield_authored.json')
PROFILE_DIR=Path(__file__).resolve().parents[2]/'work/audio-tuning-profiles'
MAX_DOCUMENT=16384
# Both current owners request 2048 samples and analyze at 48 kHz. This validates
# persisted startup windows before input exists; later ACKs always use observed
# FFT metadata, and the analysis adapter validates each delivered packet again.
STARTUP_BINS=tuple(i*48000./2048 for i in range(1025))

def target_spec(target):
    if target==TARGET:return SHIPPED,AUTHORED_PATH,validate,True
    from artifacts_audio_tuning import TARGET as ART_TARGET,BASELINE as ART_BASELINE,validate as art_validate
    if target==ART_TARGET:return ART_BASELINE,Path(__file__).with_name('artifacts_audio_authored.json'),art_validate,False
    from planet_audio_tuning import SPECS,baseline,authored_path,validate as planet_validate
    if target in SPECS:return baseline(target),authored_path(target),lambda c:planet_validate(target,c),False
    from audio_controls import TARGETS,defaults,authored_path as form_path,validate as form_validate
    if target in TARGETS:return defaults(target),form_path(target),lambda c:form_validate(TARGETS[target]['form'],target,c),False
    raise ValueError('Unknown audio tuning target')

def normalize(settings,target):
    baseline,path,validator,needs_bins=target_spec(target)
    c=validator(settings)
    if needs_bins:
        c=window_settings(c)
        if c is None:raise ValueError('Legacy multiweight curve cannot be saved as one window')
        c=dict(c,**{key:c.get(key,1.) for key in PRESENTATION_BOUNDS})
        c=dict(listening_defaults(('flux','sparkle','impact')),**c)
    return c

def require_bins(settings,bin_frequencies):
    if bin_frequencies is None:raise ValueError('Current actual FFT bins are required')
    if not any(settings['start_hz']<=f<settings['end_hz'] for f in bin_frequencies):
        raise ValueError('Selected window contains no actual FFT bins')

def document(settings,name,kind,bin_frequencies=None,*,target=TARGET):
    c=normalize(settings,target)
    if target=='planet.material.artifacts':
        from artifacts_audio_tuning import require_listening_bins
        require_listening_bins(c,bin_frequencies if bin_frequencies is not None else tuple(i*48000./2048 for i in range(1025)))
    else:
        from planet_audio_tuning import WINDOWS,STAR_WINDOWS
        from audio_controls import TARGETS,windows
        require_windows_bins(c,windows(target) if target in TARGETS else STAR_WINDOWS if target==TARGET else WINDOWS[target],
            bin_frequencies if bin_frequencies is not None else tuple(i*48000./2048 for i in range(1025)))
    if type(name) is not str or not name.strip() or name!=name.strip() or len(name)>80 or any(not v.isprintable() for v in name):
        raise ValueError('Profile name must contain 1-80 printable characters without edge spaces')
    if kind not in ('authored','profile'):raise ValueError('Unknown tuning document kind')
    if target_spec(target)[3] and bin_frequencies is not None:require_bins(c,bin_frequencies)
    values={k:v for k,v in c.items() if k!='enabled'}
    return dict(version=3,target=target,kind=kind,name=name,values=values)

def validate_document(data,kind=None,bin_frequencies=None,*,target=TARGET):
    if not isinstance(data,dict) or set(data)!=set(('version','target','kind','name','values')):
        raise ValueError('Unknown tuning document fields')
    from artifacts_audio_tuning import TARGET as ART_TARGET,LEGACY_BASELINE,PRE_LISTENING_BASELINE
    if type(data['version']) is not int or data['version'] not in ((1,2,3) if target in (TARGET,ART_TARGET) else (1,3)):raise ValueError('Unsupported tuning version')
    if data['target']!=target:raise ValueError('Wrong audio tuning target')
    baseline=target_spec(target)[0]
    from audio_controls import TARGETS
    if target in TARGETS and data['version']!=3:raise ValueError('Unsupported form tuning version')
    if kind is not None and data['kind']!=kind:raise ValueError('Wrong tuning document kind')
    values=data['values']
    if not isinstance(values,dict):raise ValueError('Invalid tuning values')
    # Persist only the single-window schema, never the bypass state or legacy bands.
    from planet_audio_tuning import legacy_baseline
    if data['version']==3:expected=baseline
    elif target==ART_TARGET:expected=LEGACY_BASELINE if data['version']==1 else PRE_LISTENING_BASELINE
    elif target==TARGET:expected=LEGACY_SHIPPED if data['version']==1 else PRE_LISTENING_SHIPPED
    else:expected=legacy_baseline(target)
    if set(values)!=set(expected)-{'enabled'}:raise ValueError('Unknown tuning value fields')
    result=document(dict(baseline,**values,enabled=True),data['name'],data['kind'],bin_frequencies,target=target)
    return result

def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate tuning document field')
        result[key]=value
    return result

def read_document(path,kind,bin_frequencies=None,*,target=TARGET):
    with Path(path).open('rb') as stream:raw=stream.read(MAX_DOCUMENT+1)
    if len(raw)>MAX_DOCUMENT:raise ValueError('Tuning document too large')
    data=json.loads(raw.decode('utf8'),object_pairs_hook=unique_object)
    return validate_document(data,kind,bin_frequencies,target=target)

def atomic_write(path,data):
    data=validate_document(data,target=data.get('target') if isinstance(data,dict) else None)
    raw=(json.dumps(data,indent=2,allow_nan=False)+'\n').encode('utf8')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def settings_from(data,enabled=True):return dict(data['values'],enabled=enabled)

class TargetProfileStore:
    def __init__(self,target=TARGET,authored_path=None,profile_dir=PROFILE_DIR):
        baseline,path,validator,needs_bins=target_spec(target)
        self.target=target;self.needs_bins=needs_bins
        self.authored_path=Path(authored_path or path);self.profile_dir=Path(profile_dir)
        self.authored=dict(baseline);self.error=None
        try:self.reload_authored()
        except FileNotFoundError as exc:
            from planet_audio_tuning import SPECS
            from audio_controls import TARGETS
            if target not in SPECS and target not in TARGETS:self.error=str(exc)
        except (OSError,ValueError,UnicodeError,RecursionError) as exc:self.error=str(exc)

    def reload_authored(self):
        from planet_audio_tuning import SPECS
        from audio_controls import TARGETS
        if (self.target in SPECS or self.target in TARGETS) and not self.authored_path.exists():
            self.authored=dict(target_spec(self.target)[0]);self.error=None
            return deepcopy(self.authored)
        data=read_document(self.authored_path,'authored',STARTUP_BINS if self.needs_bins else None,target=self.target)
        self.authored=settings_from(data);self.error=None
        return deepcopy(self.authored)

    def save_profile(self,name,settings,bin_frequencies=None):
        c=normalize(settings,self.target)
        if self.needs_bins:require_bins(c,bin_frequencies)
        data=document(c,name,'profile',bin_frequencies,target=self.target)
        slug=re.sub('[^A-Za-z0-9_-]+','-',name).strip('-')[:40] or 'profile'
        prefix='profile-' if self.target==TARGET else 'profile-artifacts-' if self.target=='planet.material.artifacts' else 'profile-'+self.target.removeprefix('planet.').replace('.','-')+'-'
        filename=prefix+slug+'-'+hashlib.sha256(name.encode('utf8')).hexdigest()[:12]+'.json'
        path=self.profile_dir/filename
        if path.resolve()==self.authored_path.resolve():raise ValueError('Profile cannot replace authored baseline')
        atomic_write(path,data);return path

    def load_profile(self,path,bin_frequencies=None):
        if Path(path).resolve()==self.authored_path.resolve():raise ValueError('Use Back to authored for the authored baseline')
        if self.needs_bins and bin_frequencies is None:raise ValueError('Current actual FFT bins are required')
        data=read_document(path,'profile',bin_frequencies,target=self.target)
        return data['name'],settings_from(data)

    def save_authored(self,settings,bin_frequencies=None):
        c=normalize(settings,self.target)
        if self.needs_bins:require_bins(c,bin_frequencies)
        data=document(c,'Authored','authored',bin_frequencies,target=self.target)
        atomic_write(self.authored_path,data)
        self.authored=settings_from(data);self.error=None
        return deepcopy(self.authored)

class StarProfileStore(TargetProfileStore):
    def __init__(self,authored_path=AUTHORED_PATH,profile_dir=PROFILE_DIR):
        super().__init__(TARGET,authored_path,profile_dir)
