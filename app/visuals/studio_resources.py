"""Presentation-only formatting of existing asynchronous resource packets."""
import time

SIMPLE_TOOLTIPS={
    'CPU':'Sum of CPU usage for distinct Studio GUI, control-owner and renderer PIDs, percent of one core (can exceed 100%).',
    'GPU':'Device-wide utilization (%) of the identified rendering adapter; includes other applications, not GPU draw time.',
    'Mem':'Sum of distinct Studio process working sets in MiB; shared pages may be counted more than once, not system RAM or VRAM.',
    'FPS':'Renderer presentation/swap-return rate per second from existing telemetry, not measured monitor scanout FPS.'}

def presentation(snapshot,now):
    preview=snapshot.get('preview') or {};perf=preview.get('performance') or {};stamp=perf.get('swap_return_wall')
    if not snapshot.get('running'):return 'stopped'
    if preview.get('paused'):return 'paused'
    if not preview.get('ready'):return 'warming up'
    if not isinstance(stamp,(int,float)) or now-stamp>1.5:return 'stale / unavailable'
    value=perf.get('swap_return_rate_hz')
    return f'{value:.1f} swap returns/s' if isinstance(value,(int,float)) else 'unavailable'

def simple_resources(snapshot,now=None):
    now=time.perf_counter() if now is None else now;row=snapshot.get('resources') or {}
    fresh=bool(row) and now-row.get('wall',now)<=3. and not row.get('error')
    processes=row.get('processes',{}) if fresh else {}
    if not snapshot.get('running'):processes={pid:p for pid,p in processes.items() if p['roles']!=['renderer']}
    def total(key,unit,scale=1.):
        values=[p.get(key) for p in processes.values()];available=[v for v in values if isinstance(v,(int,float))]
        if not available:return 'stale / unavailable' if row else 'unavailable'
        return f'{sum(available)/scale:.1f} {unit}'+(' (partial)' if len(available)!=len(values) else '')
    gpu=row.get('gpu_device_utilization_percent') if fresh and row.get('gpu') else None
    return {'CPU':total('process_cpu_percent','%'),
        'GPU':f'{gpu:.1f} %' if isinstance(gpu,(int,float)) else ('stale / unavailable' if row else 'unavailable'),
        'Mem':total('process_working_set_bytes','MiB',2**20),'FPS':presentation(snapshot,now)}

def resource_text(snapshot, now=None):
    now=time.perf_counter() if now is None else now
    row=snapshot.get('resources') or {};age=now-row.get('wall',now)
    lines=['FPS / presentation: '+presentation(snapshot,now)+' (not measured scanout)',
        'Resources • nominal 1 s samples • '+(f'age {age:.1f} s' if row else 'warming up')]
    fresh=bool(row) and age<=3. and not row.get('error')
    def number(value,unit,scale=1.):
        return f'{value/scale:.1f} {unit}' if isinstance(value,(int,float)) else 'unavailable'
    if not fresh:lines.append('Stale / unavailable' if row else 'Waiting for the first sample')
    processes=row.get('processes',{}) if fresh else {}
    if not snapshot.get('running'):
        processes={pid:item for pid,item in processes.items() if item['roles']!=['renderer']}
    roles={role for item in processes.values() for role in item['roles']}
    for item in processes.values():
        lines.append(f"{' + '.join(item['roles'])} (PID {item['pid']}): CPU {number(item.get('process_cpu_percent'),'% of one core')} • RAM {number(item.get('process_working_set_bytes'),'MiB',2**20)}")
    for role in ('renderer','Qt GUI','control owner'):
        if role not in roles:lines.append(role+': '+('stopped' if role=='renderer' and not snapshot.get('running') else 'unavailable'))
    ram=[item.get('process_working_set_bytes') for item in processes.values()]
    available_ram=[v for v in ram if isinstance(v,(int,float))]
    lines.append('Sum of available distinct PID working sets: '+number(sum(available_ram) if available_ram else None,'MiB',2**20)+' (not unique physical RAM)')
    lines.append('System CPU: '+number(row.get('system_cpu_percent') if fresh else None,'%')+' • RAM '+number(row.get('system_ram_used_bytes') if fresh else None,'GiB',2**30)+' / '+number(row.get('system_ram_total_bytes') if fresh else None,'GiB',2**30))
    if fresh and row.get('gpu'):
        lines.append(f"GPU {row['gpu']} • device {row['gpu_device_index']} • {row['gpu_uuid']}"+(' • last renderer device; renderer stopped' if not snapshot.get('running') else ''))
        lines.append('Device-wide utilization '+number(row.get('gpu_device_utilization_percent'),'%')+' • VRAM '+number(row.get('gpu_device_vram_used_bytes'),'GiB',2**30)+' / '+number(row.get('gpu_device_vram_total_bytes'),'GiB',2**30))
        lines.append('Device utilization is not GPU draw time; VRAM is not app allocation')
    else:lines.append('GPU: '+(row.get('gpu_status','warming up / unavailable') if fresh else 'stale / unavailable'))
    preview=snapshot.get('preview') or {};perf=preview.get('performance') or {}
    stamp=perf.get('swap_return_wall');present_age=now-stamp if isinstance(stamp,(int,float)) else None
    if not snapshot.get('running'):state='stopped'
    elif preview.get('paused'):state='paused'
    elif not preview.get('ready'):state='warming up'
    elif present_age is None or present_age>1.5:state='stale'
    else:state=number(perf.get('swap_return_rate_hz'),'returns/s')+' • '+number(perf.get('swap_return_interval_ms'),'ms mean interval')+f' • age {present_age:.1f} s'
    lines.append('Renderer swap-return: '+state+' (not scanout FPS)')
    dimensions=preview.get('dimensions') or {}
    def size(key):return '×'.join(str(v) for v in dimensions[key]) if dimensions.get(key) else 'unavailable'
    lines.append('Output '+size('output')+' • framebuffer '+size('framebuffer')+' • internal '+size('internal'))
    policy=(preview.get('resolution') or {}).get('policy')
    lines.append(('Resolution: '+('Native physical viewport pixels' if policy['mode']=='native' else 'Fixed internal pixels, aspect fit')+' • no additional Quality reduction') if policy else 'Existing Quality scale: '+number(dimensions.get('scale'),'',.01)+'% • explicit resolution selection replaces this scale')
    return '\n\n'.join(lines)
