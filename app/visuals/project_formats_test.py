"""Actual installed H264/AAC probe and source-bin import, without product export."""
from pathlib import Path
import sys,os,json,uuid,time,subprocess,hashlib,wave,traceback
ROOT=Path(r'C:\ZeraWave');sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from project_service import ProjectService
from PySide6.QtGui import QImage,QColor
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);service=ProjectService();checks=[]
ffmpeg=Path(r'C:\Program Files\Streamlabs OBS\resources\app.asar.unpacked\node_modules\obs-studio-node\ffmpeg.exe');ffprobe=ffmpeg.with_name('ffprobe.exe')
def run(op,**args):
 s=service.state();data=dict(op=op,operation_id=uuid.uuid4().hex,expected_epoch=s['epoch'],expected_revision=s['revision'],expected_project=s['project_id'],expected_command=s['command_revision'],**args);r=service.request(data);end=time.perf_counter()+20
 while r.get('outcome',{}).get('status') in ('preparing','saving'):
  service.poll();r=service.request(dict(op='operation_status',operation_id=data['operation_id']));time.sleep(.002);assert time.perf_counter()<end
 assert r.get('outcome',{}).get('status') in ('accepted','durable'),r
 return r
try:
 video=out/'fixture.mp4';command=[str(ffmpeg),'-nostdin','-hide_banner','-f','lavfi','-i','testsrc2=size=96x64:rate=10:duration=2','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2','-ac','2','-c:v','libx264','-crf','18','-threads','1','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(video)];p=subprocess.run(command,capture_output=True,timeout=30);(out/'encoder-command.json').write_text(json.dumps(command,indent=2));(out/'encoder.stderr').write_bytes(p.stderr);assert p.returncode==0
 probe=subprocess.run([str(ffprobe),'-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,timeout=20);assert probe.returncode==0;meta=json.loads(probe.stdout);(out/'ffprobe.json').write_bytes(probe.stdout);assert {s['codec_name'] for s in meta['streams']}=={'h264','aac'};assert next(s for s in meta['streams'] if s['codec_type']=='audio')['sample_rate']=='48000'
 checks.append('Actual installed libx264/AAC encoder and finished MP4 probe succeed; this is a codec fixture, not product Export Video')
 image=out/'alpha.png';pixels=QImage(16,16,QImage.Format_ARGB32_Premultiplied);pixels.fill(QColor(60,160,200,128));assert pixels.save(str(image))
 audio=out/'mono.wav'
 with wave.open(str(audio),'wb') as f:f.setparams((1,2,24000,0,'NONE','not compressed'));f.writeframes(b'\x01\0'*24000*2)
 run('new',name='Actual format imports');media_ids=[uuid.uuid4().hex for _ in range(3)];tracks=[uuid.uuid4().hex for _ in range(3)]
 changes=[dict(op='project.provenance',values=dict(codec_probe=str(out/'ffprobe.json'))),dict(op='project.protect',paths=[str(out/'approved.mp4')])]+[dict(op='media.add',id=key,name=path.name,kind=kind,location=dict(kind='external',path=str(path))) for key,path,kind in zip(media_ids,(video,image,audio),('Video','Image','Audio'))]+[dict(op='track.add',id=key,kind=kind,name=kind) for key,kind in zip(tracks,('video','graphics','audio'))]+[dict(op='clip.add',asset=media_ids[0],track=tracks[0],start=i*30,duration=30,name='Shot '+str(i)) for i in range(50)]
 changes.extend([dict(op='clip.add',asset=media_ids[1],track=tracks[1],start=0,duration=50),dict(op='clip.add',asset=media_ids[2],track=tracks[2],start=0,duration=60)])
 run('batch',label='Import video, alpha and mono with 50 shots',changes=changes);doc=service.document;assert len(doc['clips'])==52 and all(r['status']=='Ready' for r in service.media_state.values())
 assets={a['kind']:a for a in doc['media']};assert assets['Image']['metadata']['alpha'];assert assets['Audio']['metadata']['samplerate']==24000 and assets['Audio']['metadata']['channels']==1;assert assets['Video']['metadata']['width']==96
 checks.append('Existing media inspectors validate H264/AAC video, native-alpha image and 24k mono sources; 50 serial shots do not allocate 50 active decoders')
 run('save',path=str(out/'formats.zwv'));run('close');run('open',path=str(out/'formats.zwv'));assert service.document['clips']==doc['clips'] and service.document['provenance']==doc['provenance'] and service.document['protected_paths']==doc['protected_paths'];assert all(r['status']=='Ready' for r in service.media_state.values())
 checks.append('Portable Save/reopen retains all media types, stable IDs, clips, provenance and protected approved-output path')
 service.can_shutdown(True);service.shutdown();assert not any(t.is_alive() for t in service.pool._threads)
 (out/'RESULT.json').write_text(json.dumps(dict(checks=checks,encoder_sha256=hashlib.sha256(ffmpeg.read_bytes()).hexdigest(),ffprobe_sha256=hashlib.sha256(ffprobe.read_bytes()).hexdigest(),media={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (video,image,audio)},metadata={k:a['metadata'] for k,a in assets.items()}),indent=2));print('PASS',len(checks))
except BaseException:(out/'FAILURE.txt').write_text(traceback.format_exc(),'utf8');raise
finally:
 if not service.closed:
  for j in service.jobs.values():j['cancel'].set()
  while service.jobs:service.poll();time.sleep(.002)
  service.can_shutdown(True);service.shutdown()
