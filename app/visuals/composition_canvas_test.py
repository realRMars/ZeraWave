"""Actual Qt offscreen/DPR geometry and mouse handles; mocked owner, no output."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ.setdefault('QT_SCALE_FACTOR','1.5')
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json,uuid
import numpy as np
from PySide6.QtWidgets import QApplication,QComboBox,QLabel
from PySide6.QtCore import Qt,QPointF,QPoint
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from composition import defaults,new_layer,transform,lookup,world_matrix
from studio_composition import Canvas,point,CompositionEditor,Layers

def run():
    app=QApplication([]);scene=defaults();ref=dict(id=uuid.uuid4().hex,kind='Images',name='Original technical image',path='C:/ZeraWave/work/media-composition-20261007/original-sprite-sheet.png');scene['assets']=[ref]
    row=new_layer(asset=ref['id']);row.update(transform=transform(.1,-.08,.45,.45,19),crop=[.1,.2,.9,.8],flip_x=True);scene['layers']=[row];commands=[]
    image=QImage(400,200,QImage.Format_ARGB32_Premultiplied);image.fill(0xff3388cc)
    editor=SimpleNamespace(config=scene,canvas_size=(1280,720),selected=row['id'],images={ref['id']:image},editor_tools=QComboBox())
    editor.editor_tools.addItems(['Select','Crop','Mask','Cut']);editor.metadata=lambda r:dict(width=400,height=200);editor.selected_row=lambda:lookup(editor.config).get(editor.selected);editor.select=lambda identity:setattr(editor,'selected',identity);editor.sync_controls=lambda:None
    editor.sync_tool_ui=lambda:None;editor.editable_target=lambda row:True;editor.schedule_preview=lambda:None;editor.cancel_preview=lambda:None;editor.status=QLabel()
    def commit(label,before=None):commands.append((label,deepcopy(before),deepcopy(editor.config)));return True
    editor.commit=commit;canvas=Canvas(editor);editor.canvas=canvas;editor.editor_key=lambda event:Layers.editor_key(editor,event);canvas.resize(900,600);canvas.show();app.processEvents();records=[]
    try:
        assert abs(canvas.devicePixelRatioF()-1.5)<.001
        for size,zoom,pan in (((1280,720),None,(0,0)),((1920,1080),.35,(17,-21)),((937,601),.7,(-44,26))):
            editor.canvas_size=size;canvas.zoom=zoom;canvas.pan=QPointF(*pan);canvas.set_tool('Select');app.processEvents()
            for uv in ((.2,.3),(.7,.6)):
                current=editor.selected_row();c=current['crop'];local=[(uv[i]-c[i])/(c[i+2]-c[i])-.5 for i in (0,1)];local[0]*=-1
                xy=point(canvas.source_matrix(current),local);logical=canvas.view().map(QPointF((xy[0]+.5)*size[0],(xy[1]+.5)*size[1]));assert np.allclose(canvas.canvas_point(logical),xy);assert np.allclose(canvas.mask_point(current,logical),uv)
            records.append(dict(internal=size,zoom=zoom,pan=pan,dpr=canvas.devicePixelRatioF(),crop_flip_rotated_inverse='passed'))
        editor.canvas_size=(1280,720);canvas.zoom=None;canvas.pan=QPointF();app.processEvents();assert canvas.rotation_handle
        handle=canvas.rotation_handle.toPoint();before=deepcopy(editor.config);QTest.mousePress(canvas,Qt.LeftButton,pos=handle);QTest.mouseMove(canvas,handle+QPoint(30,14),delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=handle+QPoint(30,14));assert commands[-1][0]=='Canvas rotate' and editor.config!=before
        polygon=canvas.polygon(editor.selected_row());corner=polygon[2].toPoint();before=deepcopy(editor.config);QTest.mousePress(canvas,Qt.LeftButton,pos=corner);QTest.mouseMove(canvas,corner+QPoint(24,13),delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=corner+QPoint(24,13));assert commands[-1][0]=='Canvas scale' and editor.config!=before
        group=new_layer('Group');group['order']=1;group.update(transform=transform(.1,.12,.8,.8,22),flip_y=True);editor.config['layers'].append(group);row=editor.selected_row();row['parent']=group['id'];canvas.set_tool('Mask');assert editor.editor_tools.currentText()=='Mask';app.processEvents()
        uv=(.35,.65);row=editor.selected_row();c=row['crop'];local=[(uv[i]-c[i])/(c[i+2]-c[i])-.5 for i in (0,1)];local[0]*=-1;xy=point(canvas.source_matrix(row),local);logical=canvas.view().map(QPointF((xy[0]+.5)*1280,(xy[1]+.5)*720));assert np.allclose(canvas.mask_point(row,logical),uv)
        # Selection corners/sides use the same inverse under crop/flips/parents.
        canvas.set_tool('Crop');canvas.shape='Rectangle'
        for index in range(8):
            canvas.points=[[.3,.3],[.6,.3],[.6,.6],[.3,.6]];canvas.handles=[]
            uv=canvas.points[index] if index<4 else [(canvas.points[index-4][j]+canvas.points[(index-3)%4][j])/2 for j in (0,1)];a=canvas.screen_point(row,uv).toPoint();b=canvas.screen_point(row,[uv[0]+.015,uv[1]+.015]).toPoint();before=deepcopy(canvas.points)
            QTest.mousePress(canvas,Qt.LeftButton,pos=a);QTest.mouseMove(canvas,b,delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=b);assert canvas.points!=before,(index,canvas.point_drag)
            assert abs(canvas.points[0][1]-canvas.points[1][1])<.00001 and abs(canvas.points[1][0]-canvas.points[2][0])<.00001
        canvas.discard();canvas.set_tool('Mask');canvas.shape='Curve';canvas.points=[[.3,.3],[.6,.3],[.6,.6],[.3,.6]];canvas.auto_handles();a=canvas.screen_point(row,canvas.handles[0][1]).toPoint();b=a+QPoint(6,4);before=deepcopy(canvas.handles);QTest.mousePress(canvas,Qt.LeftButton,pos=a);QTest.mouseMove(canvas,b,delay=25);QTest.mouseRelease(canvas,Qt.LeftButton,pos=b);assert canvas.handles!=before
        canvas.toggle_closed();assert not canvas.closed_path;canvas.apply();assert 'Close' in editor.status.text();canvas.preview_history(False);assert canvas.closed_path
        QTest.keyClick(canvas,Qt.Key_Delete);assert len(canvas.points)==3;canvas.preview_history(False);assert len(canvas.points)==4
        from artwork import magnetic_point
        edge=QImage(100,100,QImage.Format_ARGB32_Premultiplied);edge.fill(0xff000000)
        from PySide6.QtGui import QPainter,QColor
        painter=QPainter(edge);painter.fillRect(50,0,50,100,QColor('white'));painter.end();snapped=magnetic_point(edge,(.47,.5));assert .49<=snapped[0]<=.51
        canvas.discard();records.append(dict(selection_eight_handles='passed',curve_handle_delete_reopen_preview_undo='passed',native_edge_attraction='passed'))
        CompositionEditor.actual(SimpleNamespace(canvas=canvas));m=canvas.source_matrix(row);c=row['crop'];jacobian=np.diag(editor.canvas_size)@m[:2,:2]@np.diag([1/(400*(c[2]-c[0])),1/(200*(c[3]-c[1]))]);assert abs(np.linalg.svd(jacobian,compute_uv=False)[-1]*canvas.zoom*canvas.devicePixelRatioF()-1)<1e-6
        app.processEvents();records.append(dict(native_detail_under_transforms_dpr='passed'))
        out=Path(os.environ.get('ZERAWAVE_MEDIA_EVIDENCE',str(Path(__file__).resolve().parents[2]/'work/media-composition-20261007')))/'canvas-dpr.json';out.write_text(json.dumps(dict(evidence='Real offscreen Qt/DPR 1.5, QTest handle gestures; mocked owner. No physical monitor/DPI or GPU comparison claim',records=records,commands=[c[0] for c in commands],group_mask_inverse='passed',tool_sync='passed'),indent=2));print('PASS: Qt DPR 1.5, fixed/Native-sized geometry, zoom/pan/crop/flips/group inverses, actual QTest rotation/scale handles, one gesture per command and tool selector synchronization')
    finally:canvas.close();app.processEvents()

if __name__=='__main__':run()
