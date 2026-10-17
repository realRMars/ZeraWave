"""Real existing CLI native-plan gate, owned endpoint and protected Save As."""
from pathlib import Path
from copy import deepcopy
import os,sys,json,subprocess,traceback
root=Path(__file__).resolve().parents[2];sys.path[:0]=[str(root/'app/visuals'),str(root/'app/audio')]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);proof=Path(sys.argv[2]);manifest=json.loads(Path(sys.argv[3]).read_text());os.environ.update(ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_PROJECT_AUDIO_OUTPUT='discard-test')
from studio_control_client import ControlClient
from project_manifest import read_state,binding,stamp,stable
from project_cli import request
from video_project import new_id
client=None;checks=[]
def op(kind,**kw):
    r=request(endpoint,dict(op=kind,operation_id=new_id(),**binding(read_state(endpoint)),**kw));assert r['ok'],r;return r
def cli(name,*arguments):
    r=subprocess.run([sys.executable,'-B','-X','utf8',str(root/'app/visuals/project_manifest_cli.py'),'--endpoint',str(endpoint),*map(str,arguments)],capture_output=True,text=True,encoding='utf8',timeout=90)
    (out/(name+'-stdout.json')).write_text(r.stdout,encoding='utf8');(out/(name+'-stderr.txt')).write_text(r.stderr,encoding='utf8');return r,json.loads(r.stdout)
try:
    client=ControlClient(dict(ZERAWAVE_WORKSPACE_PID=str(os.getpid()),ZERAWAVE_WORKSPACE_HOST='0'),out/'owner.log');endpoint=Path(client.snapshot['project']['endpoint']);op('open',path=str(proof));original=deepcopy(read_state(endpoint)['document']);before=stamp(read_state(endpoint));manifest['save']['path']=str(out/'cli-save.zwv');input_path=out/'MANIFEST.json';input_path.write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r,p=cli('good-plan','--plan','--text-fit','--manifest',input_path,'--plan-file',out/'PLAN.json');assert r.returncode==0 and p['ok'] and p['plan']['text_fit']['status']=='PASS' and stamp(read_state(endpoint))==before
    r,p=cli('good-apply','--apply','--plan-file',out/'PLAN.json','--journal',out/'journal');assert r.returncode==0 and p['ok'] and p['status']=='complete';assert (out/'cli-save.zwv').exists();assert read_state(endpoint)['document']==original
    checks.append('Existing CLI --plan --text-fit performs native fit read-only and saves exact report/plan; --apply accepts its guarded plan and makes a normal pinned portable Save As')
    failed=deepcopy(manifest);failed['sections'].append(dict(key='cli-bad',label='CLI invalid font fixture',items=[],recipes=[dict(key='cli-bad',kind='caption',version=1,params=dict(track=stable(manifest['id'],'tracks','text'),start=0,duration=1,text='CLI invalid font fixture',style=dict(font='ZeraWave Missing CLI Typeface 1841')))]));bad=out/'FAILED-MANIFEST.json';bad.write_text(json.dumps(failed,indent=2),encoding='utf8');before=stamp(read_state(endpoint))
    r,p=cli('bad-plan','--plan','--text-fit','--manifest',bad,'--plan-file',out/'FAILED-PLAN.json');assert r.returncode==2 and not p['ok'] and p['status']=='blocked-native-text-fit-not-accepted';assert p['plan']['text_fit']['status']=='FAIL' and p['plan']['text_fit']['failures'];assert stamp(read_state(endpoint))==before
    r,p=cli('bad-apply','--apply','--plan-file',out/'FAILED-PLAN.json','--journal',out/'refused-journal');assert r.returncode==2 and not p['ok'] and stamp(read_state(endpoint))==before
    checks.append('Actual CLI returns nonzero/explicit blocked state while retaining aggregate native failure plan; Apply refuses it without accepting any edit or silently changing text/style')
    op('close');client.close();assert client.process.returncode==0;client=None
    (out/'RESULT.json').write_text(json.dumps(dict(status='PASS',checks=checks,owner_exit=0,classification=__doc__,unverified='No Qt input/physical/GPU/device; native fit occurs in actual owned offscreen QImage/QTextLayout workers'),indent=2),encoding='utf8');print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');raise
finally:
    if client and not client.closed:client.close(mode='discard',project_mode='discard')
