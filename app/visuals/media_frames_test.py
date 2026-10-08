"""Silent real video/GIF/shared-frame/transport checks; never opens audio output."""
from pathlib import Path
import threading,time,json,hashlib,uuid,os
from media_frames import *
from composition import defaults,new_layer

def fixtures(out):
    """Original GIF89a partial frames, transparency, disposal 2/3 and VFR."""
    data=bytearray(b'GIF89a'+struct.pack('<HHBBB',4,2,0x81,0,0)+bytes([0,0,0,255,0,0,0,255,0,0,0,255]))
    frames=[(0,0,4,2,[1,0,1,1,1,1,1,1],8,1),(0,0,2,2,[2]*4,13,3),(2,0,2,2,[3]*4,22,2),(3,1,1,1,[2],7,1)]
    for x,y,w,h,pixels,delay,disposal in frames:
        data+=b'!\xf9\x04'+struct.pack('<BHB',(disposal<<2)|1,delay,0)+b'\0'
        data+=b','+struct.pack('<HHHHB',x,y,w,h,0)+b'\x02'
        codes=[]
        for p in pixels:codes.extend((4,p))
        codes.append(5);bits=sum(c<<(3*i) for i,c in enumerate(codes));encoded=bits.to_bytes((len(codes)*3+7)//8,'little');data+=bytes([len(encoded)])+encoded+b'\0'
    data+=b';';path=out/'alpha-disposal-vfr.gif';path.write_bytes(data)
    from PySide6.QtGui import QImageReader,QImage,QColor,QPainter
    reader=QImageReader(str(path));qt=[]
    while reader.canRead():
        image=reader.read().convertToFormat(QImage.Format_RGBA8888_Premultiplied)
        if image.isNull():break
        qt.append((reader.nextImageDelay(),np.frombuffer(image.constBits(),np.uint8).reshape(2,4,4).copy()))
    assert len(qt)==4 and [d for d,p in qt]==[80,130,220,70],qt
    av=backend();observations=[]
    with av.open(str(path)) as container:
        for frame,expected in zip(container.decode(video=0),qt):
            pixels=frame.to_ndarray(format='rgba');pixels[:,:,:3]=((pixels[:,:,:3].astype(np.uint16)*pixels[:,:,3:4]+127)//255).astype(np.uint8)
            assert np.array_equal(pixels,expected[1]),(frame.pts,pixels.tolist(),expected[1].tolist())
            observations.append(float(frame.pts*frame.time_base))
    assert np.allclose(observations,[0,.08,.21,.43]),observations
    sheet=QImage(16,8,QImage.Format_RGBA8888);sheet.fill(0);p=QPainter(sheet)
    for i,c in enumerate((QColor(255,0,0,128),QColor(0,255,0,255),QColor(0,0,255,255),QColor(255,255,0,255))):p.fillRect(i*4,0,4,8,c)
    p.end();sprite=out/'original-sprite-sheet.png';assert sheet.save(str(sprite))
    from media_registry import inspect
    asset=inspect(str(sprite),threading.Event());asset['id']=uuid.uuid4().hex;scene=defaults();row=new_layer('Sprite',asset['id']);row['media'].update(columns=4,last=3,fps=4.,loop='Loop');scene['layers']=[row];scene['assets']=[{k:asset[k] for k in ('id','path','kind','name')}]
    owner=MediaFrames();reader=FrameReader();colors=[]
    try:
        owner.sync(scene,{asset['id']:asset})
        for t in (.01,.26,.51,.76):
            owner.command(row['id'],'seek',t);end=time.perf_counter()+2
            while time.perf_counter()<end:
                state=owner.snapshot()[row['id']];assert not state['error'],state
                frame=reader.read(state['frame']) if state['frame'] else None
                if frame:colors.append(list(frame['data'][:4]));assert frame['width']==4 and frame['height']==8;break
                time.sleep(.01)
            else:raise AssertionError(state)
        assert colors==[[128,0,0,128],[0,255,0,255],[0,0,255,255],[255,255,0,255]],colors
        # A rejected fifth animation cannot mutate the existing clock/settings.
        frozen=owner.snapshot();bad=deepcopy(scene)
        for i in range(4):r=new_layer('Sprite',asset['id']);r['order']=i+1;bad['layers'].append(r)
        try:owner.sync(bad,{asset['id']:asset});raise AssertionError('decoder overflow accepted')
        except ValueError:pass
        assert owner.snapshot()==frozen
    finally:reader.close();assert owner.close()
    return dict(gif='Qt/PyAV frame parity: transparent partial frames, disposal 2/3, 80/130/220/70 ms',gif_pts=observations,sprite_rgba=colors,overflow_transaction='passed')

def run():
    root=Path(__file__).resolve().parents[2];out=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(root/'work/media-composition-20261007')));rows={'original_fixtures':fixtures(out)}
    for path in (root/'images n vids/Xeraphina_video.mp4',root/'images n vids/ZeraphinaX showcase 1.mp4',out/'alpha-disposal-vfr.gif'):
        metadata=inspect_animation(str(path),threading.Event());decoder=DecoderWindow(str(path),MAX_CACHE_BYTES);base=120. if metadata['duration']>120 else .2;observations=[]
        try:
            for target in [base+i*.08 for i in range(15)]+[base+i*.08 for i in reversed(range(15))]:
                pts,frame=decoder.get(target,threading.Event());assert frame[0]*frame[1]*4==len(frame[2]);assert decoder.bytes<=MAX_CACHE_BYTES
                observations.append(dict(target=target,pts=pts,hash=hashlib.sha256(frame[2]).hexdigest(),cache=decoder.bytes,decode_ms=decoder.decode_ms))
            assert len({r['hash'] for r in observations})>=3,path
            assert all(a['pts']<=b['pts'] for a,b in zip(observations[:14],observations[1:15]))
            assert all(a['pts']>=b['pts'] for a,b in zip(observations[15:29],observations[16:]))
            rows[path.name]=dict(metadata=metadata,frames=observations,seeks=decoder.seek_count)
        finally:decoder.close()
    # Proportional real-time ping-pong soak on a middle passage of the long clip.
    path=root/'images n vids/ZeraphinaX showcase 1.mp4';meta=rows[path.name]['metadata'];identity=uuid.uuid4().hex;asset=dict(id=identity,path=str(path),kind='Video',name='Long clip',status='Ready',metadata=meta)
    scene=defaults();row=new_layer('Video',identity);row['media'].update(start=120.,end=122.,loop='Ping-pong');scene['layers']=[row];scene['assets']=[{k:asset[k] for k in ('id','path','kind','name')}]
    owner=MediaFrames();reader=FrameReader();samples=[]
    def wait_frame(timeout=5.):
        end=time.perf_counter()+timeout
        while time.perf_counter()<end:
            state=owner.snapshot()[row['id']]
            assert not state['error'],state
            if state['frame']:
                value=reader.read(state['frame'])
                if value:return state,value
            time.sleep(.015)
        raise AssertionError(owner.snapshot())
    try:
        owner.sync(scene,{identity:asset});state,value=wait_frame();assert not state['playing']
        first=state['position'];time.sleep(.1);assert owner.snapshot()[row['id']]['position']==first
        owner.command(row['id'],'play');began=time.perf_counter()
        while time.perf_counter()-began<9.:
            state,value=wait_frame();samples.append(dict(wall=time.perf_counter()-began,position=state['position'],pts=value['pts'],hash=hashlib.sha256(value['data']).hexdigest(),cache=state['frame']['cache_bytes'],decode_ms=state['frame']['decode_ms']))
            time.sleep(.025)
        assert len(samples)>30 and sum(b['pts']<a['pts'] for a,b in zip(samples,samples[1:]))>10
        owner.freeze(True);time.sleep(.06);paused=owner.snapshot()[row['id']]['position'];time.sleep(.15);assert owner.snapshot()[row['id']]['position']==paused;owner.freeze(False)
        owner.command(row['id'],'pause');time.sleep(.05);paused=owner.snapshot()[row['id']]['position'];time.sleep(.12);assert owner.snapshot()[row['id']]['position']==paused
        owner.command(row['id'],'seek',121.);state,value=wait_frame();assert abs(value['pts']-121)<.04
        owner.command(row['id'],'stop');state,value=wait_frame();assert abs(value['pts']-120)<.04
        scene['layers'][0]['enabled']=False;owner.sync(scene,{identity:asset});time.sleep(.15);assert not owner.snapshot()[row['id']]['frame']
        rows['soak']=dict(seconds=9.,samples=samples,freeze_pause_seek_stop_hidden='passed',output='None; video/audio streams never output')
    finally:reader.close();assert owner.close();assert not owner.sources
    (out/'animated-media.json').write_text(json.dumps(rows,indent=2));print('Real short/long H264 and GIF decode, timestamp ordering/reverse windows; long-clip 9 s ping-pong soak, shared frames, pause/freeze/seek/stop/hide/cleanup passed. No audio output.')

if __name__=='__main__':run()
