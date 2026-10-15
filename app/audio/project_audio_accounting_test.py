"""Reserved versus live scratch accounting for silence, mute and gaps."""
from pathlib import Path
import sys,json,hashlib,uuid
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'visuals'))
from project_mixer import Mixer
from project_evaluator import Evaluator
from video_project import create,apply
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);rows=[]
for name,clip_mute,track_mute,count in [('gap',False,False,2048),('clip mute',True,False,2048),('track mute',False,True,1)]:
 d=create('Accounting');a,t,c=[uuid.uuid4().hex for _ in range(3)];changes=[dict(op='track.add',id=t,kind='audio')]
 if name!='gap':changes.extend([dict(op='media.add',id=a,name='Intentionally unopened muted source',kind='Audio',location=dict(kind='external',path=str(out/'absent.wav')),sha256='0'*64,metadata={'duration':2}),dict(op='clip.add',id=c,asset=a,track=t,start=0,duration=60,audio={'mute':clip_mute}),dict(op='track.audio',id=t,values={'mute':track_mute})])
 d=apply(d,changes,uuid.uuid4().hex)[0];e=Evaluator(d,'accounting',1);plan=e.audio_span(0,count) if name!='gap' else dict(start=0,count=count,audio=[],fps=[30,1],end_frame=60);m=Mixer()
 try:
  pcm=m.render(plan);assert pcm.shape==(count,2) and not np.any(pcm);metrics=dict(m.metrics);assert metrics['scratch_reserved_upper_bound_bytes']==4194304 and metrics['peak_owned_bytes']==m.budget.peak==4194304;assert metrics['scratch_reservation_live_bytes']==metrics['owned_after_prepare_bytes']==m.budget.used==0 and not metrics['readers'];rows.append(dict(case=name,metrics=metrics,output_bytes=pcm.nbytes));m.close();assert m.metrics['scratch_reservation_live_bytes']==m.metrics['owned_after_prepare_bytes']==m.budget.used==0 and m.metrics['peak_owned_bytes']==4194304
 finally:m.close()
(out/'RESULT.json').write_text(json.dumps(dict(checks=len(rows),rows=rows,source_sha256=hashlib.sha256(Path(__file__).with_name('project_mixer.py').read_bytes()).hexdigest(),classification=__doc__),indent=2),'utf8');print('PASS silent/muted/gap accounting',len(rows))
