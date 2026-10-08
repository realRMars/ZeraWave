"""Actual registry/animation owners with the service's exact removal branch."""
import ast,time,json,threading,tempfile,uuid,os
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from composition import defaults,new_layer,History
from media_registry import MediaRegistry,inspect
from media_frames import MediaFrames

def run():
    root=Path(__file__).resolve().parents[2];out=Path(os.environ['ZERAWAVE_MEDIA_EVIDENCE'])/('recovery-'+str(time.time_ns()));out.mkdir()
    tree=ast.parse(Path(__file__).with_name('studio_control_service.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');action=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='action');branch=next(n for n in ast.walk(action) if isinstance(n,ast.If) and ast.unparse(n.test)=="name == 'media_action'")
    history_branch=next(n for n in ast.walk(action) if isinstance(n,ast.If) and ast.unparse(n.test)=="name == 'composition_history'")
    composition_branch=next(n for n in ast.walk(action) if isinstance(n,ast.If) and ast.unparse(n.test)=="name in ('image_layers', 'composition', 'composition_preview')")
    nodes=[ast.FunctionDef(name=name,args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='owner'),ast.arg(arg='data')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[]) for name,body in (('remove',branch.body),('history',history_branch.body),('composition',composition_branch.body))];module=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]));scope={'deepcopy':deepcopy,'name':'composition','require_destination':lambda data:None};exec(compile(module,'exact-service-removal','exec'),scope)
    registry=MediaRegistry(out/'library.json');frames=MediaFrames()
    try:
        end=time.monotonic()+5
        while registry.loading and time.monotonic()<end:registry.poll();time.sleep(.01)
        record=inspect(str(root/'images n vids/Xeraphina_video.mp4'),threading.Event());record['id']=uuid.uuid4().hex;registry.assets[record['id']]=record
        scene=defaults();row=new_layer('Video',record['id']);scene.update(assets=[record],layers=[row]);frames.sync(scene,registry.assets);owner=SimpleNamespace(media_registry=registry,media_frames=frames,media_scene=scene,removed_media={},composition_history=History(),media_revision=7,send_media=Mock(side_effect=OSError('Injected renderer command failure')))
        before=deepcopy(scene);state=frames.layers[row['id']];generation=state['generation'];data=dict(op='remove',asset=record['id'],choice='layers',selection=row['id'])
        import media_registry
        started=threading.Event();release=threading.Event();inspect_original=media_registry.inspect
        def delayed(path,cancel):
            started.set();assert release.wait(2);return inspect_original(path,cancel)
        with patch.object(media_registry,'inspect',side_effect=delayed):
            token=registry.submit('validate',record['path'],record['id']);assert started.wait(2)
            try:scope['remove'](owner,data)
            except OSError:pass
            else:raise AssertionError('Injected failure not reported')
            assert token in registry.pending and not registry.pending[token]['cancel'].is_set()
            assert owner.media_scene==before and registry.assets[record['id']]==record and owner.media_revision==7 and not owner.composition_history.undo and not owner.removed_media
            release.set()
            end=time.monotonic()+2
            while token in registry.pending and time.monotonic()<end:registry.poll();time.sleep(.01)
            assert token not in registry.pending
        record=deepcopy(registry.assets[record['id']])
        assert frames.layers[row['id']] is state and state['generation']==generation
        owner.send_media=Mock();scope['remove'](owner,dict(data,choice='recover'));assert owner.media_scene==before and record['id'] not in registry.assets and record['id'] in owner.removed_media and owner.composition_history.peek()['restore_batch'][0]['record']==record
        owner.media_session='recovery';owner.send_media=Mock(side_effect=OSError('Injected Undo send failure'));history=deepcopy(owner.composition_history.snapshot());revision=owner.media_revision
        try:scope['history'](owner,dict(media_session='recovery'))
        except OSError:pass
        else:raise AssertionError('Undo failure not reported')
        assert record['id'] not in registry.assets and owner.composition_history.snapshot()==history and owner.media_revision==revision
        owner.send_media=Mock();scope['history'](owner,dict(media_session='recovery'));assert record['id'] in registry.assets and frames.layers[row['id']]['generation']
        owner.process=None;owner.media_spec=Mock();owner.web_frames={};owner.composition_preview=None
        before=deepcopy(owner.media_scene);history=deepcopy(owner.composition_history.snapshot());revision=owner.media_revision;state=frames.layers[row['id']]
        layers=deepcopy(before['layers']);layers[0]['transform'][4]=.2
        command=dict(media_session='recovery',media_revision=revision,version=3,canvas=None,presentation=before['presentation'],layers=layers,label='Replace/edit rollback')
        owner.send_media=Mock(side_effect=OSError('Injected edit send failure'))
        try:scope['composition'](owner,command)
        except OSError:pass
        else:raise AssertionError('Edit failure not reported')
        assert owner.media_scene==before and owner.composition_history.snapshot()==history and owner.media_revision==revision and frames.layers[row['id']] is state
        # Save As history can relocate managed dependencies. A failed Undo must
        # also restore the dictionaries changed by restore_refs, not just IDs.
        from PySide6.QtGui import QImage
        from artwork import store_image
        from media_registry import reference
        image=QImage(12,12,QImage.Format_ARGB32_Premultiplied);image.fill(0xff33aabb);art=store_image(image,'Relocation rollback fixture',out/'artwork');registry.assets[art['id']]=art
        relocated=out/'relocated.png';relocated.write_bytes(Path(art['path']).read_bytes());scene=defaults();scene.update(assets=[reference(art)],layers=[new_layer('Paint',art['id'])]);target=deepcopy(scene);target['assets'][0]['path']=str(relocated)
        frames.sync(scene,registry.assets);owner.media_scene=scene;owner.composition_history=History();owner.composition_history.record(target,scene,'Managed relocation');before_assets=deepcopy(registry.assets);before_epoch=registry.epoch
        owner.send_media=Mock(side_effect=OSError('Injected relocation Undo failure'))
        try:scope['history'](owner,dict(media_session='recovery'))
        except OSError:pass
        else:raise AssertionError('Relocation Undo failure not reported')
        assert registry.assets==before_assets and registry.epoch==before_epoch and owner.media_scene==scene and owner.composition_history.peek()==target
        from studio_control_service import ControlOwner
        wire=SimpleNamespace(process=SimpleNamespace(poll=lambda:None),committed_scope={},media_spec=Mock(return_value={}),media_revision=7,media_publication_revision=0,media_session='wire',preview_command=Mock())
        with patch('studio_control_service.compatible_scope',return_value=True):
            wire.committed_scope={'valid':True};ControlOwner.send_media(wire);ControlOwner.send_media(wire)
        assert wire.media_revision==7 and [c.kwargs['revision'] for c in wire.preview_command.call_args_list]==[1,2]
        (out/'RESULT.json').write_text(json.dumps(dict(result='PASS',checks=['Removal send failure restores registry/composition/history/revision/tombstones and original animation state identity, preserving pending validation','Recoverable removal retains complete artwork and Undo reference metadata','Undo send failure restores prior state, subsequent Undo recovers reference','Composition/replacement send failure restores scene/history/revision and animation state identity','Managed dependency relocation Undo failure restores paths/metadata/history and registry epoch','Renderer publication ordering advances independently of editor revision (mock renderer)'],evidence=__doc__),indent=2));print('PASS',out,flush=True)
    finally:assert registry.close();assert frames.close()

if __name__=='__main__':run()
