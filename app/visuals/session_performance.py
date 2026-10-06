"""Bounded development telemetry. Render-thread timers never query device load."""
from collections import deque
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import threading
import time


class Distribution:
    """Fixed .1 ms buckets; quantiles are estimates, counts/tails are exact."""
    def __init__(self):
        self.bins = [0] * 10001
        self.count = 0
        self.total = 0.
        self.maximum = 0.
        self.stalls = 0

    def add(self, seconds):
        ms = max(0., seconds * 1000.)
        self.bins[min(10000, int(ms * 10))] += 1
        self.count += 1
        self.total += ms
        self.maximum = max(self.maximum, ms)
        self.stalls += ms > 50.

    def packet(self):
        def percentile(p):
            rank = max(1, math.ceil(self.count * p))
            accumulated = 0
            for index, count in enumerate(self.bins):
                accumulated += count
                if accumulated >= rank:
                    return index / 10.
            return None
        return dict(samples=self.count, mean_ms=self.total / self.count if self.count else None,
                    p50_ms=percentile(.5), p95_ms=percentile(.95), p99_ms=percentile(.99),
                    max_ms=self.maximum if self.count else None, over_50_ms=self.stalls,
                    quantile_resolution_ms=.1, quantile_overflow_ms=1000.)


def process_resources(pid=None):
    result = dict(process_cpu_seconds=sum(os.times()[:2]) if pid in (None,os.getpid()) else None, process_working_set_bytes=None,process_peak_working_set_bytes=None,
                  system_cpu_total=None, system_cpu_idle=None, system_ram_used_bytes=None)
    if os.name != 'nt':
        return result
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [(x, ctypes.c_size_t) for x in
            ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
             'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    counters = Counters(); counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.GetCurrentProcess() if pid in (None,os.getpid()) else kernel.OpenProcess(0x410,False,int(pid))
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if handle and psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        result['process_working_set_bytes'] = counters.WorkingSetSize
        result['process_peak_working_set_bytes'] = counters.PeakWorkingSetSize
    times=[wintypes.FILETIME() for _ in range(4)]
    if handle and kernel.GetProcessTimes(handle,*(ctypes.byref(v) for v in times)):
        result['process_cpu_seconds']=sum((v.dwHighDateTime<<32)|v.dwLowDateTime for v in times[2:])/1e7
    if pid not in (None,os.getpid()) and handle:kernel.CloseHandle(handle)
    values = [wintypes.FILETIME() for _ in range(3)]
    if kernel.GetSystemTimes(*(ctypes.byref(v) for v in values)):
        idle, kern, user = [(v.dwHighDateTime << 32) | v.dwLowDateTime for v in values]
        result.update(system_cpu_total=kern + user, system_cpu_idle=idle)
    class Memory(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [(x, ctypes.c_ulonglong) for x in
            ('total_phys', 'avail_phys', 'total_page', 'avail_page', 'total_virtual', 'avail_virtual', 'avail_extended')]
    memory = Memory(); memory.length = ctypes.sizeof(memory)
    if kernel.GlobalMemoryStatusEx(ctypes.byref(memory)):
        result['system_ram_used_bytes'] = memory.total_phys - memory.avail_phys
        result['system_ram_total_bytes'] = memory.total_phys
    return result


class ResourceSampler:
    def __init__(self, interval=1.):
        self.interval = interval
        self.enabled = threading.Event()
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.latest = None
        self.history = deque(maxlen=1800)
        self.samples = 0
        self.roles={'renderer':os.getpid()};self.gpu_name=None
        self.smi = shutil.which('nvidia-smi')
        self.thread = threading.Thread(target=self.work, name='Studio resource sampler', daemon=True)
        self.thread.start()

    def configure(self,roles,gpu_name=None):
        with self.lock:
            self.roles=dict(roles)
            if gpu_name:self.gpu_name=gpu_name

    def work(self):
        previous = None
        while not self.stop.is_set():
            if not self.enabled.wait(.2):
                previous = None
                continue
            if self.stop.is_set():break
            started = time.perf_counter()
            try:
                row = process_resources()
                row.update(wall=started, process_cpu_percent=None, system_cpu_percent=None,
                           gpu_device_utilization_percent=None, gpu_device_vram_used_bytes=None,
                           gpu_device_vram_total_bytes=None, gpu=None, driver=None,
                           process_vram_bytes=None, gpu_draw_ms=None)
                with self.lock:roles=dict(self.roles);gpu_name=self.gpu_name
                processes={}
                for role,pid in roles.items():
                    if not pid:continue
                    key=str(pid)
                    if key not in processes:
                        item=process_resources(pid);item.update(pid=pid,roles=[],process_cpu_percent=None)
                        old=(previous or {}).get('processes',{}).get(key)
                        if old and item['process_cpu_seconds'] is not None and old['process_cpu_seconds'] is not None:
                            item['process_cpu_percent']=max(0.,100.*(item['process_cpu_seconds']-old['process_cpu_seconds'])/(started-previous['wall']))
                        processes[key]=item
                    processes[key]['roles'].append(role)
                row['processes']=processes
                if previous:
                    elapsed = started - previous['wall']
                    if elapsed > 0:
                        row['process_cpu_percent'] = max(0., (row['process_cpu_seconds'] - previous['process_cpu_seconds']) / elapsed * 100.)
                    if row['system_cpu_total'] is not None and previous['system_cpu_total'] is not None:
                        total = row['system_cpu_total'] - previous['system_cpu_total']
                        idle = row['system_cpu_idle'] - previous['system_cpu_idle']
                        if total > 0:
                            row['system_cpu_percent'] = max(0., min(100., 100. * (1. - idle / total)))
                if self.smi:
                    query = subprocess.run([self.smi, '--query-gpu=name,driver_version,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,index,uuid', '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, timeout=2., creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    if query.returncode == 0:
                        devices=[line.split(',') for line in query.stdout.splitlines()]
                        matches=[items for items in devices if gpu_name and items[0].strip().casefold() in gpu_name.casefold()]
                        row['gpu_status']='unavailable: rendering adapter not identified' if len(matches)!=1 else 'identified rendering adapter; device-wide readings'
                        if len(matches)!=1:devices=[]
                        items=matches[0] if len(matches)==1 else None
                        if items:row.update(gpu=items[0].strip(),driver=items[1].strip(),gpu_device_index=int(items[7]),gpu_uuid=items[8].strip())
                        for field, index, scale in (('gpu_device_utilization_percent', 2, 1.), ('gpu_device_vram_used_bytes', 3, 1048576.), ('gpu_device_vram_total_bytes', 4, 1048576.), ('gpu_temperature_c', 5, 1.), ('gpu_power_w', 6, 1.)):
                            try:row[field] = float(items[index]) * scale if items else None
                            except ValueError:row[field] = None
                    else:row['gpu_status']='unavailable: device query failed'
                else:row['gpu_status']='unsupported: nvidia-smi unavailable'
                row['sampler_wall_ms'] = (time.perf_counter() - started) * 1000.
                previous = row
                with self.lock:
                    self.latest = row
                    self.history.append(dict(row))
                    self.samples += 1
            except (OSError, ValueError, IndexError, subprocess.TimeoutExpired) as exc:
                with self.lock:self.latest = dict(wall=started, error=type(exc).__name__)
            self.stop.wait(max(.05, self.interval - (time.perf_counter() - started)))

    def snapshot(self):
        with self.lock:return dict(self.latest) if self.latest else {}

    def close(self):
        self.stop.set();self.enabled.set();self.thread.join(timeout=2.5)


class SessionPerformance:
    def __init__(self, renderer, folder, run, enabled=False):
        self.renderer, self.folder, self.run = renderer, Path(folder), run
        self.started = time.perf_counter()
        self.started_utc = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.frame = Distribution();self.submit = Distribution();self.swap = Distribution()
        self.intervals = deque(maxlen=120)
        # Opt-in evidence trace, without device queries or synchronization.
        self.interval_trace = deque(maxlen=4096) if os.environ.get('ZERAWAVE_SWAP_TRACE')=='1' else None
        self.hitches = deque(maxlen=256)
        self.switches = deque(maxlen=256)
        self.by_diagnostics = {False: Distribution(), True: Distribution()}
        self.last_present = None
        self.render_started = None
        self.sampler = ResourceSampler()
        self.enabled = False
        self.set_enabled(enabled)
        self.identity = self.source_identity()
        self.applied_edits=deque(maxlen=256);self.applied_edits_total=0
        self.applied_revisions={};self.edit_chain=self.identity['launch_settings_sha256']

    def source_identity(self):
        root = Path(__file__).resolve().parents[2]
        try:head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True, stdin=subprocess.DEVNULL, timeout=2., creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).strip()
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):head = None
        files = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'app').rglob('*') if p.is_file() and p.suffix in ('.py', '.frag', '.vert', '.json')}
        values = {}
        try:values = json.loads((self.folder / 'preview.json').read_text(encoding='utf8'))
        except (OSError, ValueError):pass
        track = values.get('track')
        audio = None
        if values.get('source') == 'Test track' and track and Path(track).is_file():
            digest = hashlib.sha256()
            with Path(track).open('rb') as handle:
                for block in iter(lambda:handle.read(1024 * 1024), b''):digest.update(block)
            audio = dict(name=Path(track).name, sha256=digest.hexdigest(), copied=False)
        # Identity only, no private source paths or unrelated settings copied.
        relevant = {k:values.get(k) for k in ('state','selection','selection_scope','playback_scope','playback_form','source','speed','duration','captures','layers','color_overrides','transitions','planet_palette','material_isolation','galaxy_seed','galaxy_visit','galaxy_entry','planet_dsp_pilot','planet_star_attack_pilot','cymatics','render_scale')}
        launch_hash=hashlib.sha256(json.dumps(relevant,sort_keys=True).encode()).hexdigest()
        return dict(checkpoint=head, files=files, audio=audio, source_mode=values.get('source'),
                    settings_identity_kind='launch-only; subsequent applied controls are in applied_edit_trace',
                    launch_settings=relevant,launch_settings_sha256=launch_hash,
                    settings_sha256=launch_hash,
                    seed=self.renderer.director_seed, replay_speed=values.get('speed') if values.get('source')=='Test track' else None,
                    system=platform.platform(), logical_cpus=os.cpu_count())

    def record_applied_edit(self,kind,scope,settings,seconds,authored=None):
        """Observe adapter application or successful color draw/ACK, never pending edits."""
        owner=getattr(self.renderer,'studio_audio',None)
        expected_run=owner.run if kind=='audio' and owner else self.run
        expected_session=owner.session if owner else os.environ.get('ZERAWAVE_AUDIO_SESSION')
        if kind not in ('audio','colors') or scope.get('run')!=expected_run or scope.get('session')!=expected_session:return False
        revision=scope.get('revision')
        if type(revision) is not int or revision<0:return False
        key=(kind,scope.get('form'),scope.get('target')) if kind=='audio' else ('colors',)
        if revision<=self.applied_revisions.get(key,-1):return False
        raw=json.dumps(dict(settings=settings,authored=authored),sort_keys=True,separators=(',',':'),allow_nan=False)
        event=dict(kind=kind,preview_run=self.run,scope=dict(scope),song_seconds=seconds,
                   wall_since_start=time.perf_counter()-self.started,settings_sha256=hashlib.sha256(raw.encode()).hexdigest(),settings=json.loads(raw))
        self.edit_chain=hashlib.sha256((self.edit_chain+json.dumps(event,sort_keys=True,separators=(',',':'))).encode()).hexdigest()
        self.applied_revisions[key]=revision;self.applied_edits_total+=1;self.applied_edits.append(event)
        return True

    def record_color_applied(self,revision,seconds,echo_clock):
        r=self.renderer;owner=getattr(r,'studio_audio',None)
        scope=dict(run=self.run,session=owner.session if owner else os.environ.get('ZERAWAVE_AUDIO_SESSION'),
                   form=r.state_at(seconds),target='colors',revision=revision)
        self.record_applied_edit('colors',scope,r.color_overrides,seconds)

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if self.enabled:
            with self.sampler.lock:self.sampler.latest=None
        self.sampler.enabled.set() if self.enabled and os.environ.get('ZERAWAVE_OWNER_TELEMETRY')!='1' else self.sampler.enabled.clear()
        self.switches.append(dict(wall=time.perf_counter(), enabled=self.enabled))

    def owner_sample(self,row):
        """Retain enabled diagnostic consumers without a second collector."""
        if not self.enabled or os.environ.get('ZERAWAVE_OWNER_TELEMETRY')!='1':return
        if not isinstance(row,dict) or not isinstance(row.get('wall'),(int,float)) or not math.isfinite(row['wall']):return
        with self.sampler.lock:
            if self.sampler.latest and row['wall']<=self.sampler.latest.get('wall',-math.inf):return
            self.sampler.latest=dict(row);self.sampler.history.append(dict(row));self.sampler.samples+=1

    def begin_render(self):
        self.render_started = time.perf_counter()

    def end_render(self):
        if self.render_started is not None:
            self.submit.add(time.perf_counter() - self.render_started)
            self.render_started = None

    def presented(self, swap_seconds):
        now = time.perf_counter()
        self.swap.add(swap_seconds)
        controls = getattr(self.renderer, 'preview_playback', None)
        if self.last_present is not None and not (controls and controls.playback.resume_fresh):
            interval = now - self.last_present
            self.frame.add(interval);self.by_diagnostics[self.enabled].add(interval);self.intervals.append(interval)
            if self.interval_trace is not None:
                self.interval_trace.append(dict(song_seconds=self.renderer.last_render_time,
                    wall=now,interval_ms=interval*1000.))
            if interval > .05:
                r = self.renderer
                self.hitches.append(dict(wall_since_start=now - self.started, interval_ms=interval * 1000.,
                    song_seconds=r.last_render_time, form=r.state_at(r.last_render_time or 0.),
                    outgoing=r.director_current, incoming=r.director_target,
                    recipe=r.director_recipe, progress=r.transition_progress()))
        if controls:controls.playback.resume_fresh = False
        self.last_present = now

    def summary(self):
        recent = list(self.intervals)
        mean = sum(recent) / len(recent) if recent else None
        timing=dict(swap_return_rate_hz=1./mean if mean else None,swap_return_interval_ms=mean*1000. if mean else None,
                    swap_return_wall=self.last_present,interval_samples=len(recent),interval_capacity=self.intervals.maxlen)
        if not self.enabled:return dict(enabled=False, display='Diagnostics off. Frame timing is saved in Latest Results.',**timing)
        row = self.sampler.snapshot()
        if not row or time.perf_counter()-row.get('wall',-math.inf)>3*self.sampler.interval:
            row={}
        def number(key, unit, scale=1.):
            value = row.get(key)
            return f'{value / scale:.1f}{unit}' if type(value) in (int, float) else 'unavailable'
        display = (f'Swap returns {1. / mean:.1f}/s / {mean * 1000.:.1f} ms (not scanout)' if mean else 'Swap returns unavailable')
        controls=getattr(self.renderer,'preview_playback',None)
        if controls and controls.playback.paused:display='Presentation paused'
        display += f" | CPU process {number('process_cpu_percent', '%')} / system {number('system_cpu_percent', '%')}"
        display += f" | GPU device {row.get('gpu_device_index','unidentified')} {number('gpu_device_utilization_percent', '%')} | RAM process {number('process_working_set_bytes', ' GiB', 2**30)}"
        display += f" | VRAM device {number('gpu_device_vram_used_bytes', ' GiB', 2**30)}; process unavailable"
        return dict(enabled=True, display=display, resources=row, interval_seconds=self.sampler.interval,**timing)

    def close(self):
        self.sampler.close()
        r = self.renderer
        import glfw
        with self.sampler.lock:
            resources=list(self.sampler.history);samples=self.sampler.samples
        report = dict(version=2, run=self.run, started_utc=self.started_utc,
            elapsed_wall_seconds=time.perf_counter() - self.started, identity=self.identity,
            applied_edit_trace=list(self.applied_edits),applied_edits_total=self.applied_edits_total,
            applied_edit_chain_sha256=self.edit_chain,
            applied_edit_trace_limits=dict(cap=256,dropped=max(0,self.applied_edits_total-len(self.applied_edits)),
                meaning='Acknowledged applied configuration; not whole simulation state or proof of visible pixel contribution',
                ownership='Audio run/session/form/target/revision; colors owned preview pipe and revision',
                chain='Launch hash plus all observed applied events; bounded trace retains latest256'),
            dimensions=dict(client=glfw.get_window_size(r.window) if r.window else None, framebuffer=glfw.get_framebuffer_size(r.window) if r.window else None,
                            viewport=r.ctx.viewport if r.ctx else None, main_internal=getattr(r.ctx,'internal',None) if r.ctx else None,
                            cached_screen_size=r.ctx.screen.size if r.ctx else None,
                            surface_internal=getattr(getattr(r,'surface_stage',None),'size',None),
                            echo_internal=[t.size for t in r.echo_resources[0]] if r.echo_resources else None,
                            shader_resolution=r.program['u_resolution'].value if r.program and 'u_resolution' in r.program else None),
            graphics_context=dict(r.ctx.info) if r.ctx else None,
            final_state=dict(form=r.state_at(r.last_render_time or 0.),sequence=list(r.debug_sequence),outgoing=r.director_current,incoming=r.director_target,recipe=r.director_recipe,progress=r.transition_progress(),layers_sha256=hashlib.sha256(json.dumps(r.layer_profiles,sort_keys=True).encode()).hexdigest(),quality=dict(render_scale=getattr(r.ctx,'scale',1.),adaptive=False,appearance='Authored full quality' if getattr(r.ctx,'scale',1.)==1. else 'Opt-in softer scaled rendering')),
            presentation_by_diagnostics={str(k):v.packet() for k,v in self.by_diagnostics.items()},
            startup=getattr(r,'startup_metrics',{}), presentation_intervals=self.frame.packet(),
            interval_trace=list(self.interval_trace) if self.interval_trace is not None else None,
            render_CPU_call=self.submit.packet(), swap_call=self.swap.packet(), hitches=list(self.hitches),
            resource_samples_total=samples, resource_history=resources, diagnostics_switches=list(self.switches),
            limits=dict(frame_quantiles='Fixed .1 ms histogram; >=1000 ms overflow bucket, exact maximum/count',
                resource_history_cap=1800,hitch_history_cap=256,diagnostics_switch_cap=256,
                process_CPU='Percent of one logical CPU; may exceed 100%',system_CPU='Whole system busy percent',
                RAM='Process working set bytes; system physical used bytes',VRAM='Identified rendering device, device-wide MiB converted to bytes; process VRAM unavailable',
                sampling='Async nominal 1 s; nvidia-smi timeout 2 s; actual timestamps retained',
                presentation='Intervals between swap returns including caller pacing; not scanout',
                render_CPU='Python render call, including any implicit driver sync; not GPU draw',
                GPU_draw='Unavailable in this lightweight display; separate scoped query harness required',
                unavailable='Missing hardware/driver counters are null, never fabricated zero',
                background='Power/thermals/background tasks uncontrolled; no FPS guarantee',
                audio='Existing source only; no PCM copied; silent decoded replay unless separately listened'))
        self.folder.mkdir(parents=True,exist_ok=True)
        temp=self.folder/'session-performance.tmp'
        temp.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf8')
        temp.replace(self.folder/'session-performance.json')
