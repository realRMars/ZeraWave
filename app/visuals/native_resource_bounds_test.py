"""Atomic owner admission and separate native/Qt/projection budget checks."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,json,uuid,gc
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
import native_raster as nr
import raster_resources as rr
from raster_tiles import mapping_bytes,unique_bytes
from cpu_projection import Projection

def run(folder):
    app=QApplication.instance() or QApplication([]);out=Path(folder);out.mkdir(exist_ok=False,parents=True);checks=[]
    image=QImage(258,130,QImage.Format_ARGB32_Premultiplied);image.fill(QColor('#a856d3'));core=nr.Core();version=core.from_image(image);desc,lease=rr.snapshot(version);resources=rr.Resources(out/'artwork')
    def asset(d):
        identity=uuid.uuid4().hex
        return dict(id=identity,kind='Images',name='bounds',path=str(out/(identity+'.png')),managed=True,provenance='fixture',runtime=d)
    def rejected(fn):
        try:fn()
        except (ValueError,MemoryError,FileNotFoundError):return
        raise AssertionError('Budget/failure not rejected')
    try:
        assert mapping_bytes([desc,desc])>=unique_bytes([desc,desc])==desc['bytes'];checks.append('Shared tile mappings deduplicate and page rounding is charged')
        for key,limit in [('MAX_BYTES',desc['bytes']-1),('MAX_MAPPING_BYTES',mapping_bytes([desc])-1),('MAX_RESOURCES',0),('MAX_JOBS',0),('MAX_JOB_BYTES',desc['bytes']-1)]:
            with patch.object(rr,key,limit):rejected(lambda:resources.admit([asset(desc)]))
            assert not resources.rows and not resources.leases
            checks.append(key+' exhaustion rejects before acceptance')
        before=nr.backend().storage().stats()['bytes'];bad=deepcopy(desc);bad['tiles'][-1]['name']='zw_raster_missing_final_bounds'
        rejected(lambda:resources.admit([asset(desc),asset(bad)]));gc.collect()
        assert not resources.rows and not resources.leases and nr.backend().storage().stats()['bytes']==before
        checks.append('Later tile-open failure rolls back earlier batch leases and native import')
        try:core.close()
        except ValueError:checks.append('Native context close refuses a live version')
        else:raise AssertionError('Closed retained context')
        before=core.stats()['bytes']
        with patch.object(nr,'_display_bytes',512*1024*1024):rejected(lambda:core.from_image(image))
        gc.collect();assert core.stats()['bytes']==before
        checks.append('Qt presentation exhaustion releases unaccepted native import')
        cache=Projection(limit=512)
        def small():return QImage(8,8,QImage.Format_ARGB32_Premultiplied)
        cache.get('a',small);cache.get('b',small);cache.get('c',small);assert cache.bytes==512 and 'a' not in cache.cache
        rejected(lambda:cache.get('oversized',lambda:QImage(20,20,QImage.Format_ARGB32_Premultiplied)));assert cache.bytes==512
        rejected(lambda:cache.scratch_image('oversized',6144,6144));assert cache.scratch_bytes==0
        checks.append('Projection LRU evicts oldest; oversized region/scratch preserve prior entries')
        resources.admit([asset(desc)]);state=resources.state();assert state['resource_count']==1 and state['mapping_bytes']==mapping_bytes([desc])
        report=dict(checks=checks,owner={k:state[k] for k in ('bytes','mapping_bytes','logical_bytes','resource_count','mapping_limit','resource_limit')},limits='Real guards with lowered fixture limits; no huge physical allocation or long soak');(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    finally:
        resources.close();rr.release(lease);version=None;gc.collect();assert core.stats()['versions']==0;core.close()

if __name__=='__main__':run(sys.argv[1])
