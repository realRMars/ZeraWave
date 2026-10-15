"""Local Studio video-project CLI. Reads structured commands, never edits JSON files directly."""
import argparse,json,sys,time,uuid
from pathlib import Path
from project_api import call
def request(endpoint,data,wait=True,timeout=120.):
 result=call(endpoint,data)
 if wait and (result.get('outcome') or {}).get('status') in ('preparing','saving','exporting'):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   time.sleep(.03);result=call(endpoint,dict(op='operation_status',operation_id=data['operation_id']))
   outcome=result.get('outcome') or {}
   if outcome.get('status') not in ('preparing','saving','exporting'):result['ok']=outcome.get('status') in ('accepted','durable','exported');return result
  return dict(ok=False,error=dict(code='outcome_unknown',message='Preparation is still owned/pinned. Query or retry the SAME operation ID.'),operation_id=data['operation_id'])
 return result
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--endpoint',required=True);parser.add_argument('--request',type=Path,help='Exact structured request including expected epoch/project/revision and operation ID');parser.add_argument('--no-wait',action='store_true');parser.add_argument('--timeout',type=float,default=120.);parser.add_argument('--status',help='Query this operation identity');args=parser.parse_args()
 try:
  if args.status:data=dict(op='operation_status',operation_id=args.status)
  elif args.request:data=json.loads(args.request.read_text('utf-8-sig'))
  else:data=dict(op='state')
  result=request(args.endpoint,data,not args.no_wait,args.timeout);print(json.dumps(result,ensure_ascii=False,indent=2))
  if not result.get('ok',False):
   code=(result.get('error') or (result.get('outcome') or {}).get('error') or {}).get('code');return 75 if code in ('outcome_unknown','export_outcome_unknown','transport','busy') else 2
  return 0
 except (OSError,RuntimeError) as exc:print(json.dumps(dict(ok=False,error=dict(code='outcome_unknown',message=str(exc))),ensure_ascii=False));return 75
 except (ValueError,KeyError) as exc:print(json.dumps(dict(ok=False,error=dict(code='invalid_request',message=str(exc))),ensure_ascii=False));return 2
if __name__=='__main__':sys.exit(main())
