"""Plan/apply/resume an editable manifest through one explicit existing endpoint."""
import argparse,json,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'app/audio'))
from project_manifest import compile_plan,apply_plan,journal_lock,Journal,Uncertain,encoded,MAX_DOCUMENT_BYTES

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--endpoint',required=True,type=Path);p.add_argument('--manifest',type=Path);p.add_argument('--plan-file',type=Path);p.add_argument('--plan',action='store_true');p.add_argument('--journal',type=Path);p.add_argument('--apply',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--text-fit',action='store_true',help='Also run bounded native fit for legacy expanded text; version2 components always require it');p.add_argument('--timeout',type=float,default=120);a=p.parse_args()
 try:
  if sum((a.plan,a.apply,a.resume))!=1:raise ValueError('Choose exactly one of --plan, --apply or --resume.')
  if a.resume:
   if a.manifest or a.plan_file or not a.journal:raise ValueError('Resume uses the saved exact plan in --journal, no replacement manifest/plan.')
   with journal_lock(a.journal):result=apply_plan(a.endpoint,Journal(a.journal),timeout=a.timeout)
  elif a.plan:
   if not a.manifest or a.manifest.stat().st_size>MAX_DOCUMENT_BYTES:raise ValueError('Provide a <=512KiB manifest.')
   manifest=json.loads(a.manifest.read_text(encoding='utf-8-sig'));plan=compile_plan(a.endpoint,manifest,text_fit=a.text_fit)
   if not a.plan_file:raise ValueError('Choose a new --plan-file; Apply must consume this exact saved dry-run plan.')
   protected=[a.endpoint.resolve(),a.manifest.resolve(),Path(manifest['save']['path']).resolve()]+[Path(r['path']).resolve() for r in manifest['media']]
   if a.plan_file.resolve() in protected:raise ValueError('Plan destination overlaps endpoint/input/source/output; choose a new file.')
   a.plan_file.parent.mkdir(parents=True,exist_ok=True)
   with a.plan_file.open('xb') as f:f.write(encoded(plan));f.flush();os.fsync(f.fileno())
   fit=plan.get('text_fit');passed=fit is None or fit['status']=='PASS';result=dict(ok=passed,status='planned-not-accepted' if passed else 'blocked-native-text-fit-not-accepted',plan_file=str(a.plan_file.resolve()),plan=plan)
  else:
   if a.manifest or not a.plan_file or a.plan_file.stat().st_size>4*1024*1024 or not a.journal:raise ValueError('Apply requires --plan-file and a new --journal; a changed manifest needs an explicit new plan.')
   plan=json.loads(a.plan_file.read_text(encoding='utf-8-sig'));folder=a.journal.resolve();protected=[a.endpoint.resolve(),a.plan_file.resolve(),Path(plan['steps'][-1]['request']['path']).resolve()]+[Path(r['path']).resolve() for r in plan['sources']]
   if any(path==folder/'journal.json' or path==folder/'workflow.lock' for path in protected):raise ValueError('Journal would overlap endpoint/plan/source/output; choose a new directory.')
   with journal_lock(folder):result=apply_plan(a.endpoint,Journal(folder,plan),timeout=a.timeout)
  ok=result.get('ok',True);print(encoded(dict(result,ok=ok)).decode('utf8'));return 0 if ok else 2
 except Uncertain as exc:print(encoded(dict(ok=False,status='uncertain',error=str(exc))).decode('utf8'));return 75
 except (ValueError,OSError,KeyError,TypeError,RuntimeError) as exc:print(encoded(dict(ok=False,status='blocked-accepted-work-retained',error=str(exc))).decode('utf8'));return 2
if __name__=='__main__':sys.exit(main())
