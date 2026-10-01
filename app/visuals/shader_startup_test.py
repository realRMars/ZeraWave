"""Focused Windows startup/zero-world fixtures; no playback or cache deletion."""
from pathlib import Path
import argparse
import ast
import ctypes as c
from ctypes import wintypes as w
import hashlib
import importlib.util
import json
import math
import queue
import subprocess
import sys
import threading
import time
import uuid


def child(nonce):
    import glfw
    import moderngl
    import shader_startup
    from renderer import Renderer
    original = moderngl.Context.program
    def program(context, **kwargs):
        if nonce:
            kwargs['fragment_shader'] += '\n// isolated startup test key ' + nonce + '\n'
        return original(context, **kwargs)
    moderngl.Context.program = program
    old_init = shader_startup.StartupNotice.__init__
    def init(self, title):
        old_init(self, title)
        print('PROBE ' + json.dumps({'notice_pid': self.process.pid}), flush=True)
    shader_startup.StartupNotice.__init__ = init
    renderer = Renderer(width=640, height=360, title='ZeraWave Startup Fixture', seed=244)
    renderer.debug_state = 36
    began = time.perf_counter()
    try:
        renderer.create()
        t = time.perf_counter()
        renderer.render(0.)
        renderer.ctx.finish()
        print('PROBE ' + json.dumps({'ready': time.perf_counter()-began,
              'metrics': renderer.startup_metrics,
              'first_draw_seconds': time.perf_counter()-t}), flush=True)
        # Ready fixture exits through normal cleanup; actual lifecycle separately.
    finally:
        renderer.close()


def windows(pid):
    user = c.WinDLL('user32', use_last_error=True)
    callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user.EnumWindows.argtypes = [callback, w.LPARAM]
    user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
    user.IsWindowVisible.argtypes = [w.HWND]
    result = []
    @callback
    def each(hwnd, _):
        owner = w.DWORD()
        user.GetWindowThreadProcessId(hwnd, c.byref(owner))
        if owner.value == pid and user.IsWindowVisible(hwnd):
            result.append(hwnd)
        return True
    user.EnumWindows(each, 0)
    return result


def run_case(nonce, cancel, output):
    p = subprocess.Popen([sys.executable, '-X', 'utf8', str(Path(__file__).resolve()),
         '--child', '--nonce', nonce], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
         creationflags=subprocess.CREATE_NO_WINDOW)
    q = queue.Queue()
    def reader():
        for line in p.stdout:
            q.put(line.decode('utf-8', errors='replace'))
    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    user = c.WinDLL('user32', use_last_error=True)
    user.SendMessageTimeoutW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM, w.UINT, w.UINT, c.POINTER(c.c_size_t)]
    user.SendMessageTimeoutW.restype = w.LPARAM
    user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
    user.IsWindow.argtypes=[w.HWND];user.IsWindow.restype=w.BOOL
    began = time.monotonic(); lines=[]; checks=[]; notice_pid=None; ready=None; cancel_at=None
    try:
        while p.poll() is None and time.monotonic()-began < 100.:
            while not q.empty():
                line=q.get();lines.append(line)
                if line.startswith('PROBE '):
                    v=json.loads(line[6:]);notice_pid=v.get('notice_pid',notice_pid)
                    if 'ready' in v:ready=v
            elapsed=time.monotonic()-began
            if notice_pid:
                for hwnd in windows(notice_pid):
                    # The dialog continues processing WM_NULL while parent is
                    # inside native shader compilation. Never another window.
                    result=c.c_size_t()
                    ok=bool(user.SendMessageTimeoutW(hwnd,0,0,0,2,350,c.byref(result)))
                    checks.append({'seconds':elapsed,'responsive':ok})
                    assert ok or not user.IsWindow(hwnd), 'Startup notice stopped processing messages'
                    if cancel and elapsed>4. and cancel_at is None:
                        user.PostMessageW(hwnd,0x0010,0,0);cancel_at=time.monotonic()
            if cancel_at and time.monotonic()-cancel_at>3.:
                raise AssertionError('Owned preview did not cancel promptly')
            time.sleep(.15)
        assert p.poll() is not None, 'Bounded startup fixture exceeded100s'
        thread.join(timeout=1.)
        while not q.empty():
            line=q.get();lines.append(line)
            if line.startswith('PROBE '):
                v=json.loads(line[6:])
                if 'ready' in v:ready=v
        report={'source_key':nonce,'cancel':cancel,'exit_code':p.returncode,
            'wall_seconds':time.monotonic()-began,'ready':ready,'responsive_samples':checks,
            'cancel_exit_seconds':time.monotonic()-cancel_at if cancel_at else None,
            'scope':'New isolated source-comment key is not proof of driver cache miss; same key warm run follows. No cache/settings change or audio output.'}
        (output.with_suffix('.log')).write_text(''.join(lines),encoding='utf-8')
        output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        if cancel:
            assert cancel_at is not None and p.returncode==125, (cancel_at,p.returncode)
        else:
            assert p.returncode==0 and ready, (p.returncode,lines)
            if output.stem=='new-program':assert len(checks)>=2, 'No observed responsive progress window'
        print('PASS',output.name,'wall',report['wall_seconds'],'response_samples',len(checks),flush=True)
        return report
    finally:
        if p.poll() is None:p.terminate();p.wait(timeout=5.)
        output.with_suffix('.log').write_text(''.join(lines),encoding='utf-8')
        p.stdout.close()


def zero_transfer(output):
    import procedural_cosmos as current
    from importlib.machinery import SourceFileLoader
    baseline=Path(__file__).resolve().parents[2]/'work/galaxy-correction-11/procedural_cosmos.py.before'
    before=None
    if baseline.exists():
        spec=importlib.util.spec_from_loader('zero_transfer_before',SourceFileLoader('zero_transfer_before',str(baseline)))
        before=importlib.util.module_from_spec(spec);sys.modules[spec.name]=before;spec.loader.exec_module(before)
    cases=[(244,0)]
    for seed in range(64):
        d=current.destination(seed,0)
        if not d.planets and d.stars[1]>0 and d.star_kind<=.95:
            cases.append((seed,0))
            if len(cases)==3:break
    assert len(cases)==3
    count=0
    for seed,index in cases:
        d=current.destination(seed,index)
        assert not d.planets and d.stars[1]>0
        span=(1.-current.OVERVIEW_FRACTION)/2.
        for v in (0.,.025,.05,.10,.15,.20,.25,.279999,.28,.280001):
            u=current.OVERVIEW_FRACTION+span*(1.+v)
            for clock in (5.,43.,200.):
                b=current.system_pose(d,u,clock)
                if before is not None:
                    assert before.system_pose(d,u,clock)==b, (seed,u,clock,'restored zero-world transfer differs')
                assert all(math.isfinite(x) for part in b[:2] for x in part)
                if v<.28:
                    expected=current.mix((0.,0.,0.),current.companion_position(d,clock),current.ease(v/.28))
                    assert max(abs(x-y) for x,y in zip(expected,b[1]))<1e-10
                count+=1
    result={'cases':cases,'transfer_poses':count,'baseline_compared':before is not None,'result':'PASS finite transfer poses and analytic eased companion targeting before/at/after join; exact baseline10 camera comparison when local snapshot supplied; rare244 and two ordinary zero-planet binaries',
            'current_model_sha256':hashlib.sha256(Path(current.__file__).read_bytes()).hexdigest()}
    output.write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS uncovered zero-world transfer',count,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--child',action='store_true');parser.add_argument('--nonce',default='');parser.add_argument('--output',type=Path);parser.add_argument('--zero-only',action='store_true');parser.add_argument('--cancel-only',action='store_true')
    args=parser.parse_args()
    if args.child:child(args.nonce)
    else:
        output=args.output or Path(__file__).resolve().parents[2]/'work/galaxy-startup'
        output.mkdir(parents=True,exist_ok=True)
        if args.cancel_only:
            run_case(uuid.uuid4().hex,True,output/'cancel-final.json')
        else:zero_transfer(output/'zero-transfer.json')
        if not args.zero_only and not args.cancel_only:
            nonce=uuid.uuid4().hex
            run_case(nonce,False,output/'new-program.json')
            run_case(nonce,False,output/'same-key-warm.json')
            run_case(uuid.uuid4().hex,True,output/'cancel-new-program.json')
