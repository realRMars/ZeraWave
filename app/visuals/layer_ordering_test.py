"""Stable subtree ordering, real Qt row/drop geometry, history and JSON replay."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
import sys,json,os
import numpy as np
from PySide6.QtWidgets import QApplication,QTreeWidgetItem
from PySide6.QtCore import Qt,QPoint,QPointF,QMimeData,QTimer,QEvent
from PySide6.QtGui import QMouseEvent,QDrag
from PySide6.QtTest import QTest
from composition import defaults,new_layer,lookup,world_matrix,validate_scene,History
from layer_ordering import siblings,can_step,step,move
from studio_composition import LayerTree

def run():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);app=QApplication([]);checks=[]
    scene=defaults()
    def add(name,parent=None,kind='Group'):
        r=new_layer(kind,name=name);r['parent']=parent;r['order']=len(siblings(scene,parent));scene['layers'].append(r);return r
    bottom=add('Root back');group=add('Root front');a=add('Child back',group['id']);b=add('Child middle',group['id']);c=add('Child front',group['id']);leaf=add('Grandchild',b['id']);leaf['transform'][4]=.1
    before=deepcopy(scene);wm=world_matrix(scene,leaf['id']).copy();assert not can_step(scene,c['id'],1) and not can_step(scene,a['id'],-1)
    assert not step(scene,c['id'],1) and scene==before;assert step(scene,b['id'],1);assert siblings(scene,group['id'])[0]['id']==b['id'];assert leaf['parent']==b['id'] and np.allclose(wm,world_matrix(scene,leaf['id']))
    h=History();h.record(before,deepcopy(scene),'Raise within siblings',b['id'],b['id']);assert h.step()==before;assert h.step(True)==scene
    scene=validate_scene(json.loads(json.dumps(scene)));checks.append('Front-first Up/Down one sibling, boundaries no-op, subtree transforms, coherent Undo/Redo and reopen')
    row=lookup(scene)[group['id']];row['locked']=True;assert not can_step(scene,b['id'],1)
    try:move(scene,[bottom['id']],group['id'],'inside');raise AssertionError('Locked parent accepted')
    except ValueError:pass
    row['locked']=False;assert move(scene,[a['id']],b['id'],'above');assert siblings(scene,group['id'])[0]['id']==a['id'];assert move(scene,[a['id']],c['id'],'below');assert siblings(scene,group['id'])[-1]['id']==a['id']
    before=deepcopy(scene)
    try:move(scene,[group['id']],leaf['id'],'inside');raise AssertionError('Cycle accepted')
    except ValueError:pass
    assert scene==before;wm=world_matrix(scene,b['id']).copy();assert move(scene,[b['id']],bottom['id'],'inside');assert lookup(scene)[b['id']]['parent']==bottom['id'] and np.allclose(wm,world_matrix(scene,b['id']));checks.append('Branch edges, protecting Group, explicit center parenting, cycle rejection and world placement')
    # Real widget positions decide edges, not QTreeWidget default OnItem insertion.
    scene=before;editor=SimpleNamespace(config=scene,row_items={},status=SimpleNamespace(setText=lambda t:None),editor_key=lambda e:False,binding=('fixture',0),resolve_pending=lambda:True);calls=[];editor.drop_layers=lambda *a:calls.append(a)
    class PointerTree(LayerTree):
        def startDrag(self,actions):
            self.drag_starts=getattr(self,'drag_starts',0)+1;super().startDrag(actions)
    tree=PointerTree(editor);tree.resize(440,550)
    def populate(parent,node):
        for r in siblings(scene,parent):
            item=QTreeWidgetItem([r['name']]);item.setData(0,Qt.UserRole,r['id']);editor.row_items[r['id']]=item
            (node.addChild(item) if node else tree.addTopLevelItem(item));populate(r['id'],item);item.setExpanded(True)
    populate(None,None);tree.show();app.processEvents();tree.setCurrentItem(editor.row_items[a['id']]);tree.clearSelection();editor.row_items[a['id']].setSelected(True)
    first=editor.row_items[b['id']];rect=tree.visualItemRect(first);assert tree.drop_intent(QPoint(rect.center().x(),rect.top()+1))==(b['id'],'above')
    last=editor.row_items[leaf['id']];rect=tree.visualItemRect(last);assert tree.drop_intent(QPoint(rect.center().x(),rect.bottom()-1))==(b['id'],'below')
    rect=tree.visualItemRect(editor.row_items[group['id']]);assert tree.drop_intent(rect.center())==(group['id'],'inside')
    for expanded in (False,True):
        first.setExpanded(expanded);app.processEvents();rect=tree.visualItemRect(first);assert tree.drop_intent(QPoint(rect.center().x(),rect.bottom()-1))==(b['id'],'below')
    # Real Qt press/release and keyboard paths select, collapse and expand rows.
    rect=tree.visualItemRect(first);QTest.mouseClick(tree.viewport(),Qt.LeftButton,Qt.NoModifier,rect.center());app.processEvents();assert tree.currentItem() is first
    QTest.keyClick(tree,Qt.Key_Left);app.processEvents();assert not first.isExpanded()
    QTest.keyClick(tree,Qt.Key_Right);app.processEvents();assert first.isExpanded()
    tree.clearSelection();editor.row_items[a['id']].setSelected(True)
    class Drop:
        def source(self):return tree
        def mimeData(self):return QMimeData()
        def position(self):return tree.visualItemRect(editor.row_items[c['id']]).bottomRight().toPointF()
        def setDropAction(self,a):assert a==Qt.MoveAction
        def accept(self):self.accepted=True
    event=Drop();tree.dropEvent(event);app.processEvents();assert event.accepted and calls==[([a['id']],c['id'],'below')],calls
    pointer=[]
    if os.environ.get('ZERAWAVE_QT_DRAG_PROBE')=='1' and app.platformName()=='offscreen':
        for expanded in (False,True):
            for placement in ('above','below'):
                first.setExpanded(expanded);app.processEvents();tree.clearSelection();source=editor.row_items[a['id']];source.setSelected(True);tree.setCurrentItem(source);calls.clear()
                target=editor.row_items[leaf['id']] if expanded and placement=='below' else first;rect=tree.visualItemRect(target);point=QPoint(rect.center().x(),rect.top()+1 if placement=='above' else rect.bottom()-1)
                source_point=tree.visualItemRect(source).center();starts=getattr(tree,'drag_starts',0)
                QTest.mousePress(tree.viewport(),Qt.LeftButton,Qt.NoModifier,source_point)
                QTimer.singleShot(60,lambda p=point:QTest.mouseMove(tree.viewport(),p))
                QTimer.singleShot(140,lambda p=point:QTest.mouseRelease(tree.viewport(),Qt.LeftButton,Qt.NoModifier,p))
                QTimer.singleShot(500,QDrag.cancel)
                motion=source_point+QPoint(24,0);event=QMouseEvent(QEvent.MouseMove,QPointF(motion),QPointF(tree.viewport().mapToGlobal(motion)),Qt.NoButton,Qt.LeftButton,Qt.NoModifier);app.sendEvent(tree.viewport(),event);QTest.qWait(550);app.processEvents()
                began=getattr(tree,'drag_starts',0)>starts;assert began,'Qt pointer event did not initiate a drag'
                expected=([a['id']],b['id'],placement)
                if calls:assert calls==[expected],(calls,expected)
                pointer.append(dict(expanded=expanded,placement=placement,drag_started=began,accepted=calls==[expected],platform=app.platformName()))
        checks.append('Qt pointer-initiated drag/drop probe with bounded cancellation; platform acceptance recorded individually')
    elif os.environ.get('ZERAWAVE_QT_DRAG_PROBE')=='1':
        pointer.append(dict(platform=app.platformName(),unavailable='Native OLE drag uses platform input and blocks QTest cancellation; use Robert manual review.'))
    tree.grab().save(str(out/'qt-ordering.png'));tree.close();checks.append('Qt mouse click and keyboard collapse/expand, expanded/collapsed edge and center hit geometry; scripted internal drop calls guarded ordering once')
    (out/'RESULT.json').write_text(json.dumps(dict(result='PASS',evidence=__doc__,checks=checks,pointer_drag=pointer,limit='Qt-dispatched events, optional platform drag probe and scripted drop object; physical OS drag acceptance remains Robert'),indent=2),encoding='utf-8');print('PASS',checks)

if __name__=='__main__':run()
