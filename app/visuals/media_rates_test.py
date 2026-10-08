"""Short source-bound normal/6x/12x silent decoder/publication comparison.

Two supplied clips, 2–8 ping-pong (long clip 120–126). Native RGBA. These are
worker/shared-frame measurements, not renderer FPS, scanout or motion acceptance.
"""
from pathlib import Path
from copy import deepcopy
import importlib.util,sys,time,json,uuid,threading,hashlib
import numpy as np
from composition import defaults,new_layer
from PySide6.QtGui import QImage,QPainter
from PySide6.QtCore import Qt

def stats(v):
    a=np.asarray(v,float);return dict(n=len(a),median=float(np.median(a)),p95=float(np.percentile(a,95)),maximum=float(a.max())) if len(a) else None

def run():
    root=Path(__file__).resolve().parents[2];base=root/'work/media-corrections-20261007';out=base/('rate-run-'+str(time.time_ns()));out.mkdir();baseline='--baseline' in sys.argv
    path=base/'baseline/app/visuals/media_frames.py' if baseline else Path(__file__).with_name('media_frames.py');spec=importlib.util.spec_from_file_location('bound_frames',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);report=dict(source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),evidence=__doc__,runs=[])
    for filename,start in (('Xeraphina_video.mp4',2.),('ZeraphinaX showcase 1.mp4',120.)):
        original=root/'images n vids'/filename;meta=module.inspect_animation(str(original),threading.Event());asset=dict(id=uuid.uuid4().hex,kind='Video',path=str(original),name=filename,status='Ready',metadata=meta);scene=defaults();row=new_layer('Video',asset['id']);row['media'].update(start=start,end=start+6,loop='Ping-pong');scene['layers']=[row];scene['assets']=[{k:asset[k] for k in ('id','kind','path','name')}];owner=module.MediaFrames();reader=module.FrameReader()
        try:
            owner.sync(scene,{asset['id']:asset});owner.command(row['id'],'play')
            for rate in (1.,6.,12.):
                # Live rate update intentionally preserves playing state/phase.
                row['media']['rate']=rate;owner.sync(scene,{asset['id']:asset});time.sleep(.7);began=time.perf_counter();last=began;records=[];frames=[];generation=None
                while time.perf_counter()-began<2.4:
                    state=owner.snapshot()[row['id']]
                    if state['error']:raise AssertionError(state)
                    desc=state['frame'];frame=reader.read(desc) if desc else None
                    if frame:
                        now=time.perf_counter();records.append(dict(wall=now-began,interval_ms=(now-last)*1000,pts=frame['pts'],decode_ms=desc['decode_ms'],cache_bytes=desc['cache_bytes'],seeks=desc['seeks'],width=frame['width'],height=frame['height']));last=now
                        if len(frames)<8 and (not frames or now-began>len(frames)*.27):
                            im=QImage(frame['data'],frame['width'],frame['height'],QImage.Format_RGBA8888_Premultiplied).mirrored(False,True).copy();frames.append(im.scaled(320,180,Qt.KeepAspectRatio,Qt.SmoothTransformation))
                            if rate==1 and len(frames)==1:im.save(str(out/(('before' if baseline else 'after')+'-native-video-'+filename+'.png')))
                    time.sleep(.004)
                assert state['playing'];assert records;contact=QImage(320*4,180*2,QImage.Format_ARGB32_Premultiplied);contact.fill(0xff080e12);p=QPainter(contact)
                for i,im in enumerate(frames):p.drawImage((i%4)*320,(i//4)*180,im)
                p.end();contact.save(str(out/(('before' if baseline else 'after')+'-'+filename+'-'+str(rate)+'x-motion-contact.png')))
                report['runs'].append(dict(file=filename,input_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),metadata=meta,rate=rate,range=[start,start+6],loop='Ping-pong',interval_ms=stats([r['interval_ms'] for r in records]),decode_ms=stats([r['decode_ms'] for r in records]),observed_publications_per_s=len(records)/2.4,records=records,playing_after_live_rate=state['playing']))
        finally:reader.close();assert owner.close();assert not owner.sources
    dest=out/(('rates-before-' if baseline else 'rates-after-')+str(time.time_ns())+'.json');dest.write_text(json.dumps(report,indent=2));print('PASS',dest,[(r['file'],r['rate'],round(r['observed_publications_per_s'],2),r['decode_ms']) for r in report['runs']],flush=True)

if __name__=='__main__':run()
