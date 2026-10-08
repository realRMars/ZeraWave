"""Standalone registry/session/decode contracts; no playback/capture/GL."""
from pathlib import Path
from copy import deepcopy
import tempfile,time,json,threading,struct,zlib,sys,wave,io,os
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'audio'))
from PySide6.QtGui import QImage,QColor
from media_registry import MediaRegistry,decode_image,defaults,validate_scene,MAX_PIXELS,MAX_REGISTRY_BYTES,library_record
from studio import validate_session,DEFAULTS
from composition import new_layer,transform

def wait(registry,fn):
    end=time.perf_counter()+6
    while time.perf_counter()<end:
        registry.poll()
        if fn():return
        time.sleep(.01)
    raise AssertionError(registry.snapshot())
def images(folder):
    png=folder/'transparent.png';jpg=folder/'opaque.jpg'
    image=QImage(24,16,QImage.Format_RGBA8888);image.fill(QColor(240,80,20,128));assert image.save(str(png))
    image.fill(QColor('#dc9350'));assert image.save(str(jpg),'JPEG',100)
    # Standard EXIF orientation 6 (90° clockwise), not a special decoder stub.
    exif=b'Exif\0\0II'+struct.pack('<HI',42,8)+struct.pack('<H',1)+struct.pack('<HHI',0x112,3,1)+struct.pack('<H',6)+b'\0\0'+struct.pack('<I',0)
    data=jpg.read_bytes();jpg.write_bytes(data[:2]+b'\xff\xe1'+struct.pack('>H',len(exif)+2)+exif+data[2:])
    return png,jpg

def run():
    root=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(Path(__file__).resolve().parents[2]/'work/media-composition-20261007')));root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='registry-fixture-',dir=root) as temp:
        folder=Path(temp);png,jpg=images(folder);info,data=decode_image(png)
        assert (info['width'],info['height'],info['alpha'])==(24,16,True) and len(data)==24*16*4
        assert data[:4]==bytes((120,40,10,128)),data[:4]
        assert tuple(decode_image(jpg)[0][key] for key in ('width','height'))==(16,24)
        cancelled=threading.Event();cancelled.set()
        try:decode_image(png,cancelled)
        except InterruptedError:pass
        else:raise AssertionError('Cancelled image decoded')
        bad=folder/'bad.png';bad.write_bytes(b'not an image')
        huge=folder/'huge.png'
        def chunk(kind,payload):return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload))
        huge.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',8192,8192,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'))+chunk(b'IEND',b''))
        for path in (bad,huge):
            try:decode_image(path)
            except ValueError as exc:
                if path==huge:assert 'exceeds' in str(exc),str(exc)
            else:raise AssertionError('Invalid/oversized image accepted')
        audio=folder/'short.wav'
        with wave.open(str(audio),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(b'\0\0'*4096)
        import shutil
        video=folder/'reference.mp4';shutil.copyfile(Path(__file__).resolve().parents[2]/'images n vids/Xeraphina_video.mp4',video)
        registry=MediaRegistry(folder/'library.json')
        try:
            wait(registry,lambda:not registry.loading)
            for path in (png,jpg,audio,video):registry.submit('import',str(path))
            wait(registry,lambda:len(registry.assets)==4 and not registry.pending)
            assert all(a['status'] in ('Ready','Referenced') for a in registry.assets.values())
            vid=next(a for a in registry.assets.values() if a['kind']=='Video');assert vid['metadata']['codec']=='h264' and vid['metadata']['duration']>10
            broken=folder/'bad-video.mp4';broken.write_bytes(b'not a video');registry.submit('import',str(broken));wait(registry,lambda:not registry.pending);assert len(registry.assets)==4 and registry.error
            identity=next(a['id'] for a in registry.assets.values() if a['path']==str(png))
            registry.submit('import',str(folder/'.'/png.name));wait(registry,lambda:not registry.pending)
            assert len(registry.assets)==4 and 'Already in' in registry.error
            registry.rename(identity,'Visible custom name');assert registry.assets[identity]['name']=='Visible custom name'
            registry.assets[identity].update(managed=True,provenance='Generated artwork validation fixture')
            registry.submit('validate',str(png),identity);wait(registry,lambda:not registry.pending)
            assert registry.assets[identity]['managed'] and registry.assets[identity]['provenance']=='Generated artwork validation fixture'
            scene=defaults();scene['assets']=[{k:registry.assets[identity][k] for k in ('id','kind','path','name')}];row=new_layer(asset=identity);row.update(opacity=.4,transform=transform(.25));scene['layers']=[row]
            assert validate_scene(scene)==scene
            for version in (1,2,3,4,5):
                loaded=validate_session(dict(DEFAULTS,version=version,selection=[],media=scene))
                assert loaded['media']==(scene if version>=4 else defaults())
            collection=registry.collection('create',name='Review');registry.collection('add',collection,asset=identity);assert registry.collections[collection]['assets']==[identity];registry.collection('rename',collection,name='Approved assets');registry.collection('delete',collection);assert identity in registry.assets
            try:validate_session(dict(version=1,assets=[]))
            except ValueError as exc:assert 'not an artistic session' in str(exc)
            else:raise AssertionError('Registry opened as an artistic session')
            moved=folder/'moved.png';png.rename(moved);registry.submit('validate',str(png),identity);wait(registry,lambda:not registry.pending)
            assert registry.assets[identity]['status']=='Missing'
            registry.submit('relink',str(bad),identity);wait(registry,lambda:not registry.pending)
            assert registry.assets[identity]['path']==str(png) # failed relink retains reference
            registry.submit('relink',str(moved),identity);wait(registry,lambda:not registry.pending)
            assert registry.assets[identity]['path']==str(moved) and registry.assets[identity]['name']=='Visible custom name'
            assert registry.assets[identity]['managed'] and registry.assets[identity]['provenance']=='Generated artwork validation fixture'
            # Old sessions follow this same ID only after an explicit relink.
            registry.restore_refs(scene['assets']);assert registry.assets[identity]['path']==str(moved)
            conflict=dict(scene['assets'][0],path=str(folder/'unapproved-path.png'))
            before_epoch=registry.epoch;before_assets=deepcopy(registry.assets)
            registry.restore_refs(scene['assets'],apply=False)
            assert registry.epoch==before_epoch and registry.assets==before_assets
            try:registry.restore_refs([conflict])
            except ValueError:pass
            else:raise AssertionError('Unapproved identity/path substitution accepted')
            token=registry.submit('import',str(bad));registry.cancel(token);time.sleep(.05);registry.poll();assert len(registry.assets)==4
            # Deliberately complete an obsolete native read after removal.
            from unittest.mock import patch
            import media_registry
            started=threading.Event();release=threading.Event();original=media_registry.inspect
            def delayed(path,cancel):
                value=original(path,threading.Event());started.set();assert release.wait(2.);return value
            with patch.object(media_registry,'inspect',side_effect=delayed):
                registry.submit('validate',str(moved),identity);assert started.wait(2.)
                registry.remove(identity);release.set();time.sleep(.06);registry.poll()
                assert moved.is_file() and identity not in registry.assets
        finally:assert registry.close()
        restored=MediaRegistry(folder/'library.json')
        try:wait(restored,lambda:not restored.loading and not restored.pending);assert len(restored.assets)==3
        finally:assert restored.close()
    # Maximum reference/path payload fits persistence and the bounded existing IPC.
    from types import SimpleNamespace
    from studio_control_client import ControlClient
    long_path='C:\\'+('音'*1010)+'.png'
    rows=[dict(id=f'{i:032x}',kind='Images',path=long_path[:-4]+str(i)+'.png',name='音'*128,relinked_from=[long_path+str(n) for n in range(8)]) for i in range(128)]
    assert len(json.dumps(dict(version=1,assets=[library_record(row) for row in rows])).encode('utf-8'))<MAX_REGISTRY_BYTES
    public=[{k:v for k,v in row.items() if k!='relinked_from'} for row in rows]
    packet=json.dumps(dict(snapshot=dict(media_library=dict(assets=public))))+'\n';assert 524288<len(packet)<2*1024*1024
    fake=SimpleNamespace(process=SimpleNamespace(stdout=io.StringIO(packet)),condition=threading.Condition(),snapshot={},responses={},stderr=io.StringIO(),disconnected=False)
    ControlClient.read(fake);assert fake.snapshot['media_library']['assets']==public and not fake.stderr.getvalue()
    print('PASS: PNG/JPEG alpha/EXIF; bounded registry and collections, actual video header/first-frame validation and bad codec, audio header/PCM without output; missing/relink/cancel/remove/persistence; sessions v1-v5. No playback/capture.')

if __name__=='__main__':run()
