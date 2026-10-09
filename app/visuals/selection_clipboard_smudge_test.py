"""Selection/clipboard/visible Smudge checks with actual Qt and ControlOwner.
Automated events, CPU pixels and standalone GPU output are separate from Robert acceptance.
"""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,os,json,time,traceback,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'app/visuals'),str(ROOT/'app/audio')]
from PySide6.QtCore import Qt,QPoint,QPointF
from PySide6.QtGui import QImage,QColor,QPainter,QFontDatabase
from PySide6.QtWidgets import QApplication,QLineEdit
from PySide6.QtTest import QTest
from composition import new_layer,lookup,transform,world_matrix
from editor_pixels import digest,materialize,MIME
from editor_colors import pixel_frame

def run():
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);os.environ.update(ZERAWAVE_MEDIA_LIBRARY=str(out/'library.json'),ZERAWAVE_ARTWORK_STORE=str(out/'artwork'),ZERAWAVE_RASTER_TEST_BARRIER=str(out/'hold-png'))
 app=QApplication([]);QFontDatabase.addApplicationFont(r'C:\Windows\Fonts\segoeui.ttf');from studio_qt import Shell
 shell=Shell(out/'layout.json',out/'owner.log');shell.resize(1200,850);shell.show();e=None;checks=[]
 def pump():app.processEvents();time.sleep(.002)
 def wait(fn,seconds=45):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:
   pump()
   if fn():return
  raise AssertionError('timeout: '+(e.status.text() if e else 'startup'))
 def done():wait(lambda:not e.art_jobs and not e.edit_jobs and e.selected_row() and e.canvas.source_image(e.selected_row()) is not None)
 def install(im):
  row=deepcopy(e.selected_row());assert e.save_paint(dict(row=row['id'],asset=row['asset'],target=row,session=e.binding[0],revision=e.binding[1],tool='Fixture',base=c.source_image(row)),im);done()
 def pixels(i=None):return materialize(c.source_image(lookup(e.config)[i or e.selected]))
 def key(k,mods=Qt.NoModifier):c.setFocus();QTest.keyClick(c,k,mods);pump()
 def rect(a=(.1,.15),b=(.4,.65)):
  c.discard();e.choose_tool('Select');c.shape='Rectangle';row=deepcopy(e.selected_row());QTest.mousePress(c,Qt.LeftButton,pos=c.screen_point(row,a).toPoint());QTest.mouseMove(c,c.screen_point(row,b).toPoint());QTest.mouseRelease(c,Qt.LeftButton,pos=c.screen_point(row,b).toPoint());pump();assert c.points and c.pixel_selection_ready
 def recover(redo=False):
  e.history(redo,'editor');wait(lambda:not e.edit_jobs);e.refresh(True);done()
 try:
  wait(lambda:shell.client and hasattr(shell,'image_editor') and not shell.client.snapshot['media_library']['loading']);e=shell.image_editor;c=e.canvas;e.reveal();e.resize_canvas((96,64),False);e.blank_layer();done();source=e.selected
  im=QImage(96,64,QImage.Format_ARGB32_Premultiplied);im.fill(Qt.transparent);p=QPainter(im);p.fillRect(0,0,48,64,QColor('#e05020'));p.fillRect(48,0,48,64,QColor('#2050e0'));p.end();install(im);original=digest(pixels())
  scene=deepcopy(e.config);count=shell.client.snapshot['media_control']['history']['commands'];rect();assert e.config==scene and digest(pixels())==original and shell.client.snapshot['media_control']['history']['commands']==count;checks.append('Rectangle release immediately selects exact pixels without source/history change')
  e.choose_tool('Select');c.discard();c.shape='Freehand';row=deepcopy(e.selected_row());points=[(.15,.2),(.45,.2),(.25,.35),(.45,.7),(.15,.7)]
  QTest.mousePress(c,Qt.LeftButton,pos=c.screen_point(row,points[0]).toPoint())
  for uv in points[1:]:QTest.mouseMove(c,c.screen_point(row,uv).toPoint())
  QTest.mouseRelease(c,Qt.LeftButton,pos=c.screen_point(row,points[-1]).toPoint());pump();assert c.pixel_selection_ready;mask=e.pixel_editor.mask(row,pixels());assert mask.pixelColor(40,30).alpha()==0 and mask.pixelColor(20,30).alpha()>0;c.grab().save(str(out/'lasso.png'));assert e.config==scene;checks.append('Irregular Lasso outline and coverage are usable without confirmation')
  assert e.copy_layer();clip=digest(app.clipboard().image());copy_frame=pixel_frame(c,row,pixels());assert digest(pixels())==original;e.paste_layer();done();pasted=e.selected;assert pasted!=source and e.selected_row()['parent']==row['parent'] and not e.selected_row()['masks'] and e.selected_row()['crop']==[0.,0.,1.,1.];assert np.allclose(pixel_frame(c,e.selected_row(),pixels()),copy_frame);assert pixels().pixelColor(40,30).alpha()==0 and pixels().pixelColor(20,30).alpha()>0
  first=digest(pixels());e.paste_layer();done();assert e.selected!=pasted and e.selected_row()['asset']!=lookup(e.config)[pasted]['asset'];assert digest(pixels(source))==original;checks.append('Copy/Paste preserves irregular alpha/native dimensions and origin; repeated Paste has independent identities')
  # Pasted raster transforms use the existing handles, with a pinned drag basis.
  c.set_tool('Transform');c.repaint();pump();row=deepcopy(e.selected_row());handle=c.resize_handles[2].toPoint();QTest.mousePress(c,Qt.LeftButton,pos=handle);assert c.drag and c.drag[0]=='scale'
  QTest.mouseMove(c,handle+QPoint(8,6));QTest.mouseMove(c,handle+QPoint(16,12));QTest.mouseRelease(c,Qt.LeftButton,pos=handle+QPoint(16,12));done();assert e.selected_row()['transform']!=row['transform'];recover();assert e.selected_row()['transform']==row['transform'];recover(True);checks.append('Pasted layer handles resize with a stable drag basis and exact editor recovery')
  # Conventional sequence: Cut -> Paste -> layer move, Undo each then Redo each.
  e.select(source);rect();pre=digest(pixels());QTest.mouseClick(e.editor_view.cut_button,Qt.LeftButton);done();cut=digest(pixels());assert cut!=pre and pixels().pixelColor(20,25).alpha()==0 and not e.selected_row()['masks'];assert len(e.config['layers'])==3
  assert e.paste_layer();done();cut_paste=e.selected;row=deepcopy(e.selected_row());c.begin_interactive('move');c.interactive['number']='12';c.interactive_move(QPointF(0,0));c.finish_interactive(True);done();moved=deepcopy(e.config)
  recover();assert e.selected_row()['transform']==row['transform'];recover();assert cut_paste not in lookup(e.config);recover();e.select(source);assert digest(pixels())==pre
  recover(True);e.select(source);assert digest(pixels())==cut;recover(True);assert cut_paste in lookup(e.config);recover(True);assert lookup(e.config)[cut_paste]['transform']==lookup(moved)[cut_paste]['transform'];checks.append('Cut makes a genuine raster hole without masks/children; editor Undo/Redo crosses move, Paste and Cut exactly')
  e.select(source);rect((.55,.15),(.8,.65));before_clip=digest(app.clipboard().image())
  from PySide6.QtWidgets import QMessageBox
  with patch.object(QMessageBox,'question',side_effect=AssertionError('Canvas Delete opened branch confirmation')):key(Qt.Key_Delete)
  done();deleted=digest(pixels());assert deleted!=cut and digest(app.clipboard().image())==before_clip;recover();e.select(source);assert digest(pixels())==cut
  rect((.55,.15),(.8,.65));before=digest(pixels());key(Qt.Key_D,Qt.ControlModifier);assert not c.points and digest(pixels())==before;checks.append('Delete clears selected raster pixels without replacing clipboard; Deselect changes no artwork')
  rect((.55,.15),(.8,.65));selected=c.preview_state();row=deepcopy(e.selected_row());a=c.screen_point(row,(.65,.35)).toPoint();QTest.mouseClick(c,Qt.LeftButton,pos=a);pump();assert digest(pixels())==before and c.preview_state()==selected
  QTest.mousePress(c,Qt.LeftButton,pos=a);QTest.mouseMove(c,c.screen_point(row,(.72,.4)).toPoint());key(Qt.Key_Escape);QTest.mouseRelease(c,Qt.LeftButton,pos=a);pump();assert digest(pixels())==before and c.preview_state()==selected
  QTest.mousePress(c,Qt.LeftButton,pos=a);b=c.screen_point(row,(.72,.4)).toPoint();QTest.mouseMove(c,b);QTest.mouseRelease(c,Qt.LeftButton,pos=b);done();moved_pixels=digest(pixels());assert moved_pixels!=before and e.selected==source;recover();e.select(source);assert digest(pixels())==before;recover(True);e.select(source);assert digest(pixels())==moved_pixels;checks.append('Same-raster pixel move handles overlap atomically; click/Esc unchanged; exact Undo/Redo')
  # Immutable origin under transformed crop, flips, nonuniform nested parents.
  c.discard();group=new_layer('Group');group['transform']=transform(.08,-.1,.8,1.2,22);prior=deepcopy(e.config);e.config['layers'].append(group);r=lookup(e.config)[source];r.update(parent=group['id'],crop=[.05,.1,.95,.9],flip_x=True,flip_y=True,transform=transform(.06,-.03,.7,1.1,-17));assert e.commit('Transformed source fixture',prior);done();e.select(source);rect((.55,.2),(.8,.6));copied_frame=pixel_frame(c,e.selected_row(),pixels());assert e.copy_layer();source_row=deepcopy(e.selected_row())
  e.select(pasted);before=deepcopy(e.config);lookup(e.config)[source]['transform'][4]+=.2;e.commit('Move copied source after copy',before);done();e.select(pasted);assert e.paste_layer();done();assert np.allclose(pixel_frame(c,e.selected_row(),pixels()),copied_frame,atol=1e-12);assert not e.selected_row()['masks'];checks.append('Copy-time visual placement survives crop/flips/rotation/nonuniform Group and source movement/different active layer')
  # External replacement cannot use internal origin metadata.
  external=QImage(12,8,QImage.Format_ARGB32_Premultiplied);external.fill(QColor(10,200,30,128));app.clipboard().setImage(external);assert e.paste_layer();done();frame=pixel_frame(c,e.selected_row(),pixels());assert np.allclose(frame[:2,2],[-6/96,-4/64]);checks.append('External clipboard replacement invalidates internal origin; documented centered native-pixel placement')
  e.select(source);rect((.55,.2),(.8,.6));before=digest(pixels());e.row_flag(source,'locked');done();assert e.copy_layer();clip=digest(app.clipboard().image());assert not e.cut_clipboard() and digest(pixels())==before and digest(app.clipboard().image())==clip;assert not e.pixel_editor.delete();e.row_flag(source,'locked');done();c.discard();assert not e.cut_clipboard();assert digest(pixels())==before;checks.append('Locked readable copy allowed; locked/missing selection destructive actions preserve source and clipboard')
  # Rejected allocations and export failures retain both document and clipboard.
  e.select(source);rect((.55,.2),(.8,.6));prior=deepcopy(e.config);prior_clip=digest(app.clipboard().image())
  with patch('raster_resources.snapshot',side_effect=MemoryError('Injected snapshot exhaustion')):assert not e.cut_clipboard()
  assert e.config==prior and digest(app.clipboard().image())==prior_clip
  with patch('editor_pixels.QMimeData',side_effect=MemoryError('Injected clipboard export allocation failure')):assert not e.cut_clipboard()
  assert e.config==prior and digest(app.clipboard().image())==prior_clip
  # Failure while cloning the old clipboard must not replace it; a later
  # verification failure after export restores the complete old payload.
  from PySide6.QtCore import QMimeData
  previous_internal=e.pixel_editor.clipboard
  with patch('editor_pixels.QMimeData',side_effect=[QMimeData(),MemoryError('Injected old clipboard snapshot allocation failure')]):assert not e.cut_clipboard()
  assert e.config==prior and digest(app.clipboard().image())==prior_clip and e.pixel_editor.clipboard is previous_internal
  with patch('editor_pixels.digest',side_effect=[prior_clip,MemoryError('Injected post-export verification failure')]):assert not e.cut_clipboard()
  assert e.config==prior and digest(app.clipboard().image())==prior_clip and e.pixel_editor.clipboard is previous_internal
  # Unsupported/empty OS payload and forced admission limits preserve the
  # editor document and do not fall back to layer/subtree operations.
  backup=QMimeData();old_mime=app.clipboard().mimeData()
  for fmt in old_mime.formats():backup.setData(fmt,old_mime.data(fmt))
  backup.setImageData(app.clipboard().image())
  app.clipboard().clear();assert not e.paste_layer() and 'no raster image' in e.status.text().lower()
  app.clipboard().setText('ordinary text clipboard');assert not e.paste_layer() and e.config==prior
  app.clipboard().setMimeData(backup)
  with patch('editor_pixels.MAX_LAYERS',len(e.config['layers'])):assert not e.paste_layer() and 'layer limit' in e.status.text()
  from types import SimpleNamespace
  with patch.object(e,'runtime_producers',{'forced_capacity':SimpleNamespace(size=128*1024*1024)}):assert not e.cut_clipboard() and 'capacity exhausted' in e.status.text()
  assert e.config==prior and digest(app.clipboard().image())==prior_clip
  checks.append('Empty/text clipboard and injected layer/transfer admission limits reject visibly without document/clipboard mutation or branch fallback')
  old=e.images.pop(e.selected_row()['asset']);assert not e.copy_layer();assert e.config==prior;e.images[e.selected_row()['asset']]=old
  c.discard();key(Qt.Key_Delete);assert e.config==prior;checks.append('Snapshot/clipboard allocation and late export failures, unavailable source and absent selection preserve artwork/clipboard; no branch fallback')
  # Pending selection is retired by tool changes; completed Wand is draggable.
  rect((.55,.2),(.8,.6));prior_selection=c.preview_state();row=deepcopy(e.selected_row());a=c.screen_point(row,(.2,.2)).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=a);QTest.mouseMove(c,c.screen_point(row,(.3,.3)).toPoint());e.choose_tool('Brush');QTest.mouseRelease(c,Qt.LeftButton,pos=a);assert e.pixel_editor.gesture is None and c.preview_state()==prior_selection
  c.discard();e.choose_tool('Wand');e.selection_controls.click(c.screen_point(e.selected_row(),(.7,.4)));wait(lambda:e.selection_controls.job is None and c.pixel_selection_ready);row=deepcopy(e.selected_row());a=c.screen_point(row,(.7,.4)).toPoint();before=digest(pixels());QTest.mousePress(c,Qt.LeftButton,pos=a);assert e.pixel_editor.gesture and e.pixel_editor.gesture['kind']=='move';QTest.mouseMove(c,c.screen_point(row,(.72,.42)).toPoint());key(Qt.Key_Escape);QTest.mouseRelease(c,Qt.LeftButton,pos=a);assert digest(pixels())==before;c.discard();checks.append('Tool change cancels unfinished selection into prior selection; Wand selection supports pixel drag/Esc without stale delivery')
  # Shared Main RGBA and deterministic persisted migration, independent settings/Secondary.
  secondary={t:QColor(s['secondary']) for t,s in e.tool_states.items()};rgba=QColor(51,170,99,127);e.receive_sample(rgba)
  for tool in ('Brush','Pencil','Fill'):
   e.choose_tool(tool);assert e.brush_color==rgba and rgba.name(QColor.HexArgb) in e.quick_colors.chips['main'].text()
  assert all(e.tool_states[t]['secondary']==color for t,color in secondary.items());e.receive_sample(None);assert e.brush_color==rgba;checks.append('Sampler committed RGBA is shared by Brush/Pencil/Fill; Secondary and invalid-sample behavior preserved')
  # Automatic Smudge on blank top raster; pinned visible art, hidden/locked sources.
  c.discard();e.select(source);e.row_flag(source,'locked');done();e.blank_layer();done();overlay=e.selected;blank=digest(pixels());source_hash={i:digest(pixels(i)) for i in lookup(e.config) if lookup(e.config)[i]['type']!='Group'}
  e.choose_tool('Smudge');e.tool_value('Smudge','size',18);e.tool_value('Smudge','strength',.7);row=deepcopy(e.selected_row());a=c.screen_point(row,(.25,.4)).toPoint();b=c.screen_point(row,(.32,.45)).toPoint();QTest.mousePress(c,Qt.LeftButton,pos=a);QTest.mouseMove(c,b);QTest.mouseRelease(c,Qt.LeftButton,pos=b);done();assert digest(pixels())!=blank,e.status.text();assert all(digest(pixels(i))==h for i,h in source_hash.items() if i!=overlay);smudged=digest(pixels());recover();e.select(overlay);assert digest(pixels())==blank;recover(True);e.select(overlay);assert digest(pixels())==smudged;checks.append('Blank selected raster Smudge automatically picks up visible artwork, reads locked source, modifies only target, exact recovery')
  # Hidden source contributes no pickup, and unsupported visible frame is explicit.
  e.select(overlay)
  # Initialize a known transparent target (uninitialized QImage is not artwork).
  clear_image=QImage(96,64,QImage.Format_ARGB32_Premultiplied);clear_image.fill(Qt.transparent);install(clear_image)
  initial=deepcopy(e.config)
  for i in source_hash:
   if i!=overlay:e.row_flag(i,'enabled');done()
  e.select(overlay);e.choose_tool('Smudge');row=deepcopy(e.selected_row());a=c.screen_point(row,(.25,.4)).toPoint();b=c.screen_point(row,(.32,.45)).toPoint();before_blank=digest(pixels());QTest.mousePress(c,Qt.LeftButton,pos=a);QTest.mouseMove(c,b);QTest.mouseRelease(c,Qt.LeftButton,pos=b);done();assert digest(pixels())==before_blank
  before=deepcopy(e.config)
  for r in e.config['layers']:r['enabled']=lookup(initial)[r['id']]['enabled']
  e.commit('Restore source eyes',before);done();checks.append('Hidden sources contribute no Smudge pixels; checkerboard/world/UI excluded')
  # Sidebar fills available vertical host and reflows swatches across width.
  e.choose_tool('Brush');view=e.editor_view;shell.resize(1200,1400);pump();pump();assert e.tool_scroll.height()>580,(e.tool_scroll.height(),view.height());e.tool_scroll.setFixedWidth(240);pump();pump();narrow=e.quick_colors.swatch_columns;e.tool_scroll.setFixedWidth(440);pump();pump();wide=e.quick_colors.swatch_columns;assert wide>narrow;view.grab().save(str(out/'sidebar-tall.png'));shell.resize(900,600);pump();pump();assert e.tool_scroll.verticalScrollBar().maximum()>0
  state=view.saveState();view.removeToolBar(e.color_toolbar);view.addToolBar(Qt.RightToolBarArea,e.color_toolbar);assert view.restoreState(state);assert view.toolBarArea(e.color_toolbar)==Qt.LeftToolBarArea;checks.append('Tall sidebar exceeds old 580 cap, short host scrolls, narrow/wide swatches reflow, saved toolbar redock preserved')
  # Exercise a floating instance of the same toolbar through Qt widget APIs.
  # This is resize/restore evidence, not a physical drag/monitor acceptance pass.
  bar=e.color_toolbar;view.removeToolBar(bar);bar.setParent(None,Qt.Tool);bar.setOrientation(Qt.Vertical);e.tool_scroll.setFixedSize(260,360);bar.show();bar.adjustSize();pump()
  grip=e.quick_colors.resize_grip;start=grip.rect().center();old_width=e.tool_scroll.width();QTest.mousePress(grip,Qt.LeftButton,pos=start);QTest.mouseMove(grip,start+QPoint(90,70));QTest.mouseRelease(grip,Qt.LeftButton,pos=start+QPoint(90,70));pump();assert e.tool_scroll.width()>old_width and e.tool_scroll.height()>360
  bar.hide();bar.setParent(view);e.tool_scroll.setMinimumHeight(80);e.tool_scroll.setMaximumHeight(16777215);view.addToolBar(Qt.LeftToolBarArea,bar);bar.show();assert view.restoreState(state);pump();checks.append('Same sidebar floating widget resizes through its grip and returns to its saved toolbar placement')
  # Mask compatibility and portable revision-pinned artwork persistence.
  from pixel_selection import encode
  coverage=np.zeros((64,96),np.uint8);coverage[3:60,3:90]=255;before=deepcopy(e.config);lookup(e.config)[overlay]['masks'].append(encode(coverage));e.commit('Saved existing mask fixture',before);done();save=out/'review.json';shell.client.request('save',path=str(save),save_id='selection-save');wait(lambda:save.exists() and shell.client.snapshot['media_control']['raster']['pending']==0);saved=json.loads(save.read_text(encoding='utf8'));expected={r['id']:digest(pixels(r['id'])) for r in e.config['layers'] if r['type']!='Group'}
  shell.client.request('load',path=str(save));wait(lambda:e.binding[0]==shell.client.snapshot['media_control']['session']);e.refresh(True)
  wait(lambda:all(c.source_image(r) is not None for r in e.config['layers'] if r['type']!='Group'));assert {r['id']:digest(pixels(r['id'])) for r in e.config['layers'] if r['type']!='Group'}==expected;assert lookup(e.config)[overlay]['masks']==lookup(saved['media'])[overlay]['masks'];checks.append('Revision-pinned Save/load preserves exact raster bytes, IDs, placements and existing saved mask coverage')
  shell.save_layout();preferences=json.loads((out/'layout.json').read_text(encoding='utf8'))['controls'];assert preferences['media_main_rgba']==rgba.name(QColor.HexArgb)
  edit=QLineEdit(e.editor_view);edit.show();edit.setFocus();QTest.keyClicks(edit,'pixels');QTest.keyClick(edit,Qt.Key_Z,Qt.ControlModifier);assert edit.text()=='';edit.hide();checks.append('Shared Main persists in layout preferences; ordinary text Undo remains local')
  assert not shell.errors,list(shell.errors);(out/'RESULT.json').write_text(json.dumps(dict(checks=checks,history=shell.client.snapshot['media_control']['history'],limits='Qt offscreen events/actual owner; physical native acceptance not claimed'),indent=2),encoding='utf8');print('PASS',json.dumps(checks),flush=True)
 except BaseException:
  (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf8');print('FAILED',e.status.text() if e else 'startup',flush=True);raise
 finally:
  app.clipboard().clear()
  if shell.client:shell.client.close(force=True)
  shell.closing=True
  if e:e.close_resources()
  shell.close();app.processEvents()
if __name__=='__main__':run()
