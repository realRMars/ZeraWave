"""B2 native/region exact pixels, ownership, transport, failure and cache checks."""
import gc,json,hashlib,sys,threading,time
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from native_raster import Core,backend,native_add
from composition import new_layer,defaults
from artwork import brush_stroke,smudge,constrained_edit,edit_coverage,masked
from raster_edit import segment,masked_projection
from raster_resources import snapshot,release,image as transferred
from raster_tiles import unique_bytes
from studio_composition import add_image

def pixels(image):return bytes(image.convertToFormat(QImage.Format_ARGB32_Premultiplied).constBits())
def run(out):
    app=QApplication.instance() or QApplication([]);out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=[]
    def check(name,test):
        assert test,name;checks.append(name)
    check('native backend available',backend().available);core=Core();w,h=521,389
    # Deterministic alpha-bearing premultiplied source with partial edge tiles.
    rng=np.random.default_rng(41);rgba=rng.integers(0,256,(h,w,4),dtype=np.uint8);rgba[:,:,:3]=np.minimum(rgba[:,:,:3],rgba[:,:,3,None])
    source=QImage(rgba.tobytes(),w,h,QImage.Format_ARGB32_Premultiplied).copy();native=core.from_image(source)
    check('full import/read exact',pixels(native)==pixels(source))
    for bounds in [(0,0,1,1),(126,127,131,132),(490,350,31,39),(0,382,521,7)]:check('region '+str(bounds),pixels(native.region(bounds))==pixels(source.copy(*bounds)))
    row=new_layer('Image');row['crop']=[.01,.02,.99,.98];row['masks']=[dict(enabled=True,mode='Cut',shape='Ellipse',points=[[.24,.19],[.51,.53]],handles=[])]
    selection=dict(enabled=True,shape='Rectangle',points=[[.03,.01],[.97,.97]],handles=[])
    brush=dict(size=57.3,shape='Round',flow=.37,opacity=.63,strength=.54,hardness=.42)
    path=[(125.2,127.6),(132.8,134.1),(252.7,249.2),(388.4,256.7),(516.2,386.1),(3.1,1.6)]
    for tool in ('Brush','Pencil','Eraser','Smudge'):
        working=source.copy();preview=source.copy();base=core.from_image(source);stroke=dict(image=base,base=base,preview=base,target=row,selection=selection,tool=tool,brush=brush,color=QColor('#bc52c8'),last=path[0]);coverage=edit_coverage((w,h),row,selection)
        for last,now in zip(path,path[1:]):
            if tool=='Smudge':smudge(working,last,now,brush['size'],brush['strength'],1.,brush['shape'],row,selection)
            else:brush_stroke(working,last,now,brush,stroke['color'],tool)
            r=int(np.ceil(brush['size']/2))+4;bounds=(int(np.floor(min(last[0],now[0])-r)),int(np.floor(min(last[1],now[1])-r)),int(np.ceil(max(last[0],now[0])+r)),int(np.ceil(max(last[1],now[1])+r)))
            constrained_edit(source,working,row,selection,brush['opacity'],bounds=bounds,coverage=coverage,result=preview)
            segment(stroke,now);stroke['last']=now
            actual=stroke['preview'].materialize();a=np.frombuffer(preview.constBits(),np.uint8);b=np.frombuffer(actual.constBits(),np.uint8)
            if not np.array_equal(a,b):
                preview.save(str(out/(tool+'-expected.png')));actual.save(str(out/(tool+'-actual.png')));raise AssertionError((tool,last,now,'differing bytes',int(np.count_nonzero(a!=b)),'max',int(np.max(np.abs(a.astype(int)-b.astype(int))))))
        check(tool+' multiple boundaries/constraints/order exact',True)
        stroke=None;base=None
    a=core.from_image(source);part=source.copy(127,260,3,4);part.fill(QColor('magenta'));b=a.patch((127,260,3,4),part)
    old=tuple(t.id for t in a.tiles());new=tuple(t.id for t in b.tiles());changed=sum(x!=y for x,y in zip(old,new));check('small edit shares unaffected tiles',changed==4)
    d1,l1=snapshot(a);d2,l2=snapshot(b);check('transfer copies four changed tiles',d2['transfer_copied_bytes']==4*128*128*4);check('unique retained allocation accounting',unique_bytes([d1,d2])==w*h*4+d2['transfer_copied_bytes']);received=transferred(d2);check('portable descriptor exact',pixels(received)==pixels(b))
    class Canvas:mask_cache={}
    canvas=Canvas();check('native mask projection exact',pixels(masked_projection(canvas,b,row))==pixels(masked(b,row['masks'])))
    check('native Add exact integer/source-over alpha',pixels(native_add(source,source.mirrored()))==pixels(add_image(source,source.mirrored())))
    failures=[]
    def reader():
        try:
            for _ in range(20):assert pixels(a.region((124,124,132,132)))==pixels(source.copy(124,124,132,132))
        except BaseException as exc:failures.append(str(exc))
    threads=[threading.Thread(target=reader) for _ in range(4)]
    for t in threads:t.start()
    for t in threads:t.join()
    check('concurrent immutable neighbourhood readers',not failures)
    try:core.call('zw_limit',core.context,core.stats()['bytes']);b.patch((0,0,1,1),source.copy(0,0,1,1));raise AssertionError('budget did not reject')
    except (MemoryError,ValueError):check('allocation failure keeps original immutable version',pixels(a)==pixels(source))
    core.call('zw_limit',core.context,384*1024*1024)
    received=None;release(l1);release(l2);a=None;b=None;native=None;gc.collect();check('explicit close refuses retained versions',core.stats()['versions']==0);stats=core.stats();core.close()
    report=dict(checks=checks,stats=stats,backend=backend().status(),source_sha256=hashlib.sha256(pixels(source)).hexdigest());(out/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':run(sys.argv[1])
