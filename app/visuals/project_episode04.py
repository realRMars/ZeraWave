"""Assemble the protected Episode04 copy through Studio's documented owner API.

Production-specific layout/input policy stays in this importer. It never writes
the project JSON or edits originals; actual edits/history/save use shared commands.
"""
from pathlib import Path
from fractions import Fraction
import sys,os,json,hashlib,uuid,math,time,argparse,threading
from project_api import call
from project_cli import request

NAMESPACE=uuid.UUID('cb088e44-a045-4fdc-9d56-284f451e7c37')
def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def stable(seed,name):return uuid.uuid5(NAMESPACE,seed+':'+name).hex
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),'utf8')

def source_level(asset,seconds):
 """Canonical source measurements only, bounded decoder/cache; no output."""
 import numpy as np
 from project_mixer import NativeSource,Budget
 reader=NativeSource(asset,Budget());samples=round(seconds*48000);count=0;energy=0.;peak=0.;cancel=threading.Event()
 try:
  while count<samples:
   n=min(2048,samples-count);pcm=reader.read(Fraction(count,48000),Fraction(1),n,cancel);energy+=float(np.sum(pcm.astype(np.float64)**2));peak=max(peak,float(np.max(np.abs(pcm))));count+=n
 finally:reader.close()
 return dict(samples=samples,rms=math.sqrt(energy/(samples*2)),peak=peak,rate=48000,channels=2,backend='Installed PyAV native canonical source reader; actual stream channels')

def build(receipt):
 from media_registry import inspect
 from project_media import source_metadata
 from project_text import existing_font
 from PySide6.QtGui import QFont,QFontMetricsF,QImage,QTextLayout
 seed=digest(receipt);r=json.loads(Path(receipt).read_text('utf8'));mapping=r['remapping'];docs=r['documents'];original=r['production'];prefix=original+'\\';document=lambda rel:json.loads(Path(docs[prefix+rel]['copy']).read_text('utf8'));m=document('assets\\episode04\\render-v7\\measured-edit-manifest-v1.json');cards=document('assets\\episode04\\edit-prep-v5\\card-manifest-v5.json');narration=document('assets\\episode04\\narration-assembled-provisional-v7\\narration-index-v7.json');voices={row['id']:row for row in narration};cancel=threading.Event()
 for collection in (mapping,docs):
  for record in collection.values():
   if digest(record['copy'])!=record['sha256']:raise ValueError('Protected input copy changed: '+record['copy'])
 originals={path:digest(path) for path in r['protected'] if Path(path).is_file()};changes=[];assets={};levels={};track_names=['Backdrop','Foreground / sting','Original card artwork','Editable titles / counters','Editable captions','Narration','Music / editable ducking','Game audio','Brand sting audio'];tracks={name:stable(seed,'track:'+name) for name in track_names}
 def asset(original_path,kind,name=None,provenance=None):
  key=original_path
  if key not in assets:
   rec=mapping[key];path=rec['copy'];meta=inspect(path,cancel)['metadata']
   if kind=='Video':meta.update(source_metadata(path,cancel))
   row=dict(id=stable(seed,'source:'+rec['sha256']),name=name or Path(original_path).stem,kind=kind,location=dict(kind='external',path=path),sha256=rec['sha256'],metadata=meta,provenance=dict(original_path=original_path,protected_copy_sha256=rec['sha256'],**(provenance or {})));assets[key]=row;changes.append(dict(op='media.add',**row))
  return assets[key]
 for shot in m['shots']:asset(shot['file'],'Video')
 for card in cards:asset(card['file'],'Image',card['kind']+' '+card['game'],dict(kind='Flat original PNG artwork; no hidden layers inferred',recipe_manifest_sha256=digest(docs[prefix+'assets\\episode04\\edit-prep-v5\\card-manifest-v5.json']['copy'])))
 for row in narration:asset(row['file'],'Audio','Narration '+row['id'],dict(section=row['id'],speaker=row['speaker'],spoken_text=row['spoken_text'],parts=row['parts'],actual_listening=row['actual_listening']))
 music=asset(prefix+'assets\\music\\backing-tracks\\Haunted Level 1.mp3','Audio','Haunted Level 1');sting=asset(next(s['file'] for s in m['shots'] if s['section']=='approved-sting'),'Video','Approved brand sting')
 for order,name in enumerate(track_names):changes.append(dict(op='track.add',id=tracks[name],name=name,kind='audio' if order>=5 else 'graphics' if order in (3,4) else 'video',order=order))
 changes.extend([dict(op='project.protect',paths=list(dict.fromkeys([*r['protected'],*mapping,*docs,m['output']]))),dict(op='project.provenance',values=dict(assembly='Upgrade+ Episode04 protected source commands; not baked movie',input_receipt_sha256=seed,measured_manifest_sha256=digest(docs[prefix+'assets\\episode04\\render-v7\\measured-edit-manifest-v1.json']['copy']),original_duration_frames=m['frames'],original_shots=len(m['shots']),narration_endings='Supplied takes and documented seams retained; no extra spoken-tail recovery claimed; listening remains required',audio_policy='Separate native sources, authored gains, loops and explicit whole-track host-free game moments; no invented dialogue stems',timing_limit='Fade/ducking controls use authored output-frame grid: .12s becomes4frames (.133333s); other production timing/crossfade/0.2s/0.5s align exactly. SRT cues use documented ceil output-frame boundary policy.'))])
 title='Editable Upgrade+ Gaming Episode04';layers=[];text=[];audio=[];card_map={(c['kind'],c['game']):c for c in cards};names={'DR':'The Drifter','ST':'Is This Seat Taken?','DU':'Dupery','PW':'Pixel Washer','CB':'Chained Beasts'};status={'DR':'OUT NOW','ST':'OUT NOW','DU':'15 OCT - PLANNED','PW':'15 OCT - EARLY ACCESS','CB':'15 OCT - PLANNED'};colors=dict(zip(names,['#e3ae45','#bdbe83','#c8a29a','#c8ee55','#d78c57']));body={'drifter','seat','dupery','pixel','beasts'};rows={r['id']:r for r in m['timeline']};total=m['frames'];existing_font('Segoe UI')
 def font(size):
  f=QFont('Segoe UI');f.setPointSizeF(size*72/QImage(1,1,QImage.Format_RGBA8888).logicalDpiY());f.setBold(True);return f
 def graphic(name,begin,end,value,style,dynamic=None,range_start=None,range_end=None):
  row=dict(op='graphic.add',id=stable(seed,'graphic:'+name),track=tracks['Editable titles / counters'],start=begin,duration=end-begin,text=value,style=style,provenance=dict(source='Known production text/layout recipe',original_renderer_sha256=docs[prefix+'scripts\\episode04\\render-review-candidate-v7.py']['sha256']))
  if dynamic:row.update(dynamic=dynamic,range_start=range_start,range_end=range_end)
  text.append(row)
 def interval_style(start,end):
  row=next(v for v in m['timeline'] if v['start_frame']<=start<v['start_frame']+v['frames']);sid=row['id'];g=row['game'];closing=sid in ('closing','closing-hold');card=card_map[('recap','all5')] if closing else card_map[('positive-review',g)] if sid.endswith('-review') else card_map[('preview',g)] if sid.endswith('-preview') else card_map[('entry',g)] if sid in body and start<row['start_frame']+78 else None
  return row,closing,card
 for i,shot in enumerate(m['shots']):
  start=shot['start_frame'];end=start+shot['frames'];row=rows[shot['section']];cuts=[start,end]
  if row['id'] in body and start<row['start_frame']+78<end:cuts.insert(1,row['start_frame']+78)
  for a,b in zip(cuts,cuts[1:]):
   info,closing,card=interval_style(a,b);source=Fraction(str(shot['source_in']))+Fraction(a-start,30);source_pair=[source.numerator,source.denominator];group=stable(seed,'link:'+str(i)+':'+str(a));base=dict(asset=assets[shot['file']]['id'],start=a,duration=b-a,source_in=source_pair,link_id=group,provenance=dict(original_shot=i,section=row['id'],source_url=shot.get('source_url'),original_source_in=shot['source_in'],original_source_out=shot['source_out'],repeated_pool=shot.get('repeated_pool',False)))
   if row['kind']=='sting':layers.append(dict(op='clip.add',id=stable(seed,'video:sting'),name='Brand sting',track=tracks['Foreground / sting'],**base));continue
   layers.append(dict(op='clip.add',id=stable(seed,'video:back:'+str(i)+':'+str(a)),name=f'{i:02} {row["id"]} backdrop',track=tracks['Backdrop'],layout=dict(brightness=1. if closing else .24),**base))
   if not closing:
    bounds=[35/1280,204/720,650/1280,366/720] if row['id'].endswith('-review') else [405/1280,140/720,840/1280,472/720] if card else [106/1280,60/720,1067/1280,600/720];layers.append(dict(op='clip.add',id=stable(seed,'video:front:'+str(i)+':'+str(a)),name=f'{i:02} {row["id"]} foreground',track=tracks['Foreground / sting'],layout=dict(bounds=bounds),**base))
  # Host-free source-game audio uses the SAME exact source/trim/placement group.
  if row['kind']=='breath':
   source_asset=assets[shot['file']];from project_mixer import NativeSource,Budget
   reader=NativeSource(source_asset,Budget());import numpy as np
   count=shot['frames']*1600;at=0;energy=0.;peak=0.
   try:
    while at<count:
     block=reader.read(Fraction(str(shot['source_in']))+Fraction(at,48000),Fraction(1),min(2048,count-at),cancel);energy+=float(np.sum(block.astype(np.float64)**2));peak=max(peak,float(np.max(np.abs(block))));at+=len(block)
   finally:reader.close()
   rms=math.sqrt(energy/(count*2));gain=min(10**(-24/20)/rms,.40/peak);levels[row['id']]=dict(rms=rms,peak=peak,gain=gain);audio.append(dict(op='clip.add',id=stable(seed,'gameaudio:'+str(i)),name='Authentic '+row['id'],track=tracks['Game audio'],audio=dict(gain=gain,fade_in=4,fade_out=4),asset=source_asset['id'],start=start,duration=shot['frames'],source_in=[Fraction(str(shot['source_in'])).numerator,Fraction(str(shot['source_in'])).denominator],link_id=stable(seed,'link:'+str(i)+':'+str(start)),provenance=dict(source='Combined actual original game audio; no dialogue classification',section=row['id'])))
 for row in m['timeline']:
  begin=row['start_frame'];end=begin+row['frames'];sid=row['id'];g=row['game'];closing=sid in ('closing','closing-hold')
  if row['kind']=='sting':continue
  card=card_map[('recap','all5')] if closing else card_map[('positive-review',g)] if sid.endswith('-review') else card_map[('preview',g)] if sid.endswith('-preview') else card_map[('entry',g)] if sid in body else None;card_end=min(end,begin+78) if sid in body else end
  if card:layers.append(dict(op='clip.add',id=stable(seed,'card:'+sid),name='Original '+card['kind']+' '+card['game'],asset=assets[card['file']]['id'],track=tracks['Original card artwork'],start=begin,duration=card_end-begin,provenance=dict(flat_original=True,section=sid)))
  if not closing and (not card or card_end<end):
   head_begin=card_end if card else begin;value=names[g] if g else 'TWO OUT NOW + THREE ON THE WAY' if sid=='opening-hook' else 'FIND YOUR NEXT GAME';width=QFontMetricsF(font(24)).horizontalAdvance(value)+29;graphic('header:'+sid,head_begin,end,value,dict(size=24,color='#30221b',background='#f2f4e7cd',bounds=[28/1280,20/720,width/1280,39/720],padding=0,padding_x=14,radius=8,align='left'))
   if g:
    value=status[g];width=QFontMetricsF(font(18)).horizontalAdvance(value)+19;graphic('status:'+sid,head_begin,end,value,dict(size=18,color='#f1dfbc',background='#e7221912',bounds=[(1280-width-28)/1280,22/720,width/1280,35/720],padding=0,padding_x=8,radius=8,align='left'))
  chapter=m['chapters'].get(g);range_start=round(chapter['start']*30) if chapter else rows['closing']['start_frame'] if closing else begin;range_end=round(chapter['end']*30) if chapter else total if closing else end
  graphic('progress:'+sid,begin,end,'',dict(bounds=[35/1280,714/720,1210/1280,4/720],padding=0,radius=2,color=colors.get(g,'#e3ae45'),background='#c8362718'),'progress',range_start,range_end)
  if row['kind']=='speech':
   voice=voices[sid];audio.append(dict(op='clip.add',id=stable(seed,'narration:'+sid),name='Narration '+sid,track=tracks['Narration'],asset=assets[voice['file']]['id'],start=begin,duration=row['frames'],audio=dict(gain=m['narration'][sid]['gain']),pad_end='silence',provenance=dict(section=sid,reading_hold='Explicit frame ceiling/recorded hold silence, not recovered speech',parts=voice['parts'])))
 for game,chapter in m['chapters'].items():
  begin=round(chapter['start']*30);end=round(chapter['end']*30);graphic('counter:'+game,begin,end,'{elapsed} / {duration}',dict(size=14,color='#fff1d5',background='#00000000',bounds=[37/1280,67/720,250/1280,24/720],padding=0,align='left',valign='top',stroke_width=1,stroke_color='#30221b'),'counter',begin,end)
 # The original required quiet bed is deliberately editable source instances.
 music_frames=math.floor(music['metadata']['duration']*30);music_seconds=music_frames/30;levels['music']=source_level(music,music_seconds);music_gain=10**(-43/20)/levels['music']['rms'];at=0;i=0
 while at<total:
  span=min(music_frames,total-at);audio.append(dict(op='clip.add',id=stable(seed,'musicloop:'+str(i)),name='Quiet music loop '+str(i+1),track=tracks['Music / editable ducking'],asset=music['id'],start=at,duration=span,audio=dict(gain=music_gain,fade_in=45 if i else 0,fade_out=45 if at+span<total else 0),provenance=dict(original_loop_crossfade_seconds=1.5,original_rms_target_dbfs=-43)));at+=music_frames-45;i+=1
 points={0:1.,total:1.};sting_row=rows['approved-sting'];s=sting_row['start_frame'];e=s+sting_row['frames'];points.update({s-1:1.,s:.25,e-1:.25,e:1.})
 for row in m['timeline']:
  if row['kind']=='breath':s=row['start_frame'];e=s+row['frames'];points.update({max(0,s-4):1.,s:0.,e:0.,min(total,e+6):1.})
 closing=rows['closing-hold']['start_frame'];points.update({closing-1:1.,closing:1.8,total:1.8});audio.append(dict(op='track.audio',id=tracks['Music / editable ducking'],values=dict(envelope=sorted([[f,v] for f,v in points.items()]),fade_out=15)))
 audio.append(dict(op='clip.add',id=stable(seed,'audio:sting'),name='Brand sting original audio',track=tracks['Brand sting audio'],asset=sting['id'],start=sting_row['start_frame'],duration=30,link_id=stable(seed,'link:'+str(next(i for i,x in enumerate(m['shots']) if x['section']=='approved-sting'))+':'+str(sting_row['start_frame'])),provenance=dict(channel_policy='Preserve actual native source channels; original production mono downmix differs and is declared')))
 return dict(seed=seed,name=title,settings=dict(width=1280,height=720,fps=[30,1]),tracks=tracks,assets=assets,foundation=changes,visual=layers,text=text,audio=audio,levels=levels,manifest=m,SRT=docs[prefix+'assets\\episode04\\render-v7\\captions-v1.srt']['copy'],original_hashes_at_start=originals,reference_limits=['Original production sampled source video at640x360 before1280x720 composition; this project retains native source pixels and GL filtering','Qt/Pillow glyph rasterization/metrics differ; original source PNG cards exact','Original production sting was mono downmixed; native source channels preserved','0.12s fade/duck mapped deliberately to4output frames; .2/.5/1.5s exact','SRT approximate spoken alignment remains unverified'])

def assemble(endpoint,receipt,destination,folder):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);plan=build(receipt);write(folder/'PLAN.json',plan);journal=[]
 def submit(op,label=None,**kwargs):
  state=call(endpoint,dict(op='state'))['state'];key=stable(plan['seed'],str(folder.resolve())+':operation:'+str(len(journal)));data=dict(op=op,operation_id=key,expected_epoch=state['epoch'],expected_revision=state['revision'],expected_project=state['project_id'],expected_command=state['command_revision'],**kwargs)
  if label:data['label']=label
  # Persist exact request before sending. Unknown results retain same ID and
  # request; this script never automatically rebase/resubmit a new operation.
  request_file=folder/f'request-{len(journal):03}.json';write(request_file,data);result=request(endpoint,data,True,180);journal.append(dict(request=str(request_file),result=result));write(folder/'JOURNAL.json',journal)
  if not result.get('ok'):raise ValueError('Assembly operation requires reconciliation of SAME ID '+key+': '+str(result))
  return result
 initial=call(endpoint,dict(op='state'))['state']
 if initial['document'] is not None:raise ValueError('Assembly needs a fresh disposable owner/project; existing work retained. Open another disposable Studio instead of replacing it.')
 submit('new',name=plan['name'],settings=plan['settings'],project_id=stable(plan['seed'],str(folder.resolve())+':project'))
 for key in ('foundation','visual','text','audio'):
  for at in range(0,len(plan[key]),128):submit('batch',label='Episode04 '+key+' '+str(at//128+1),changes=plan[key][at:at+128])
 submit('import_captions',label='Actual Episode04 SRT',path=plan['SRT'],track=plan['tracks']['Editable captions']);state=call(endpoint,dict(op='state'))['state'];d=state['document']
 # Set cue-specific bounds matching original one/two-line/closing recipes.
 from project_text import existing_font
 from PySide6.QtGui import QTextLayout,QFont,QImage
 existing_font('Segoe UI');font=QFont('Segoe UI');font.setBold(True);font.setPointSizeF(27*72/QImage(1,1,QImage.Format_RGBA8888).logicalDpiY());changes=[]
 for cue in d['captions']:
  layout=QTextLayout(cue['text'],font);layout.beginLayout();lines=0
  while True:
   line=layout.createLine()
   if not line.isValid():break
   line.setLineWidth(1130);lines+=1
  layout.endLayout()
  if lines>2:raise ValueError('Actual cue exceeds two readable lines; retain failed project and correct layout explicitly.')
  closing=cue['start']>=next(r['start_frame'] for r in plan['manifest']['timeline'] if r['id']=='closing');cy=288 if closing else 632 if lines==2 else 665;height=17+lines*33;changes.append(dict(op='caption.edit',id=cue['id'],values=dict(style=dict(bounds=[35/1280,(cy-5)/720,1210/1280,height/720],padding=0,padding_x=40,padding_y=4,line_spacing=33,radius=9,background='#df17120e',valign='center',max_lines=2))))
 submit('batch',label='Original caption placement recipes',changes=changes)
 # Measure complete canonical authored mix in bounded blocks, then retain the
 # original .88peak safety as explicit editable lane gains, not device master.
 from project_evaluator import Evaluator
 from project_mixer import Mixer
 from video_project import sample_at
 import numpy as np
 state=call(endpoint,dict(op='state'))['state'];e=Evaluator(state['document'],state['epoch'],state['revision']);mixer=Mixer();peak=0.;count=0;energy=0.;began=time.perf_counter();blocks=[]
 try:
  for frame in range(e.end):
   left=sample_at(e.document,frame);right=sample_at(e.document,frame+1);block=mixer.render(e.audio_span(left,right-left));peak=max(peak,float(np.max(np.abs(block))));energy+=float(np.sum(block.astype(np.float64)**2));count+=len(block)
   if frame%30==0:blocks.append(dict(frame=frame,peak=peak,mix=mixer.metrics))
 finally:mixer.close()
 safety=min(1.,.88/peak);submit('batch',label='Measured editable mix safety',changes=[dict(op='track.audio',id=plan['tracks'][name],values=dict(gain=safety)) for name in ('Narration','Music / editable ducking','Game audio','Brand sting audio')]);submit('save',path=str(Path(destination).resolve()),portable=True);final=call(endpoint,dict(op='state'))['state'];write(folder/'ASSEMBLED.json',dict(project=final,mix=dict(peak_before_safety=peak,safety_gain=safety,samples=count,rms=math.sqrt(energy/(count*2)),seconds=time.perf_counter()-began,raw_sampled_blocks=blocks),reference_limits=plan['reference_limits'],original_hashes_unchanged=all(digest(path)==h for path,h in plan['original_hashes_at_start'].items())));return final

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--endpoint',required=True);parser.add_argument('--receipt',type=Path,required=True);parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--evidence',type=Path,required=True);args=parser.parse_args()
 os.environ.setdefault('QT_QPA_PLATFORM','offscreen');from PySide6.QtWidgets import QApplication
 app=QApplication.instance() or QApplication([]);state=assemble(args.endpoint,args.receipt,args.destination,args.evidence);print(json.dumps(dict(result='assembled',path=state['path'],revision=state['revision'],project=state['project_id'],clips=len(state['document']['clips']),captions=len(state['document']['captions'])),indent=2))
if __name__=='__main__':sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'audio'));main()
