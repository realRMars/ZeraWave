"""Standalone Qt/synthetic read-only analyzer checks; no devices or renderer."""
from pathlib import Path
import sys,time,copy,json,queue,threading,io
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'audio'))
import numpy as np
from PySide6.QtWidgets import QApplication,QDialog,QDialogButtonBox
from PySide6.QtCore import QPointF,QTimer
from PySide6.QtGui import QMouseEvent
from band_display import AnalyzerSpectrum
from studio_band_analyzer import BandAnalyzer,display_values,LIMITS,MODES,PALETTES,DEFAULTS,GradientEditor
from studio_control_client import ControlClient


def telemetry():
    class Pipe:
        def __init__(self):self.lines=queue.Queue()
        def __iter__(self):
            while True:
                line=self.lines.get()
                if line is None:return
                yield line
    client=ControlClient.__new__(ControlClient);client.condition=threading.Condition();client.responses={};client.snapshot={};client.analyzer_telemetry=None;client.disconnected=False;client.stderr=io.StringIO()
    pipe=Pipe();client.process=type('Process',(),{'stdout':pipe})()
    reader=threading.Thread(target=client.read);reader.start()
    def send(message):
        pipe.lines.put(json.dumps(message)+'\n');time.sleep(.02)
    try:
        send({'snapshot':{'audio_hub':dict(generation=2,status='Playing')}})
        send({'audio_analyzer':dict(generation=2,band_analyzer={'sequence':5})})
        assert client.latest_analyzer()['band_analyzer']['sequence']==5
        send({'audio_analyzer':dict(generation=1,band_analyzer={'sequence':30})})
        send({'audio_analyzer':dict(generation=2,band_analyzer={'sequence':4})})
        assert client.latest_analyzer()['band_analyzer']['sequence']==5
        send({'snapshot':{'audio_hub':dict(generation=3,status='Stopped',band_analyzer=None)}})
        assert client.latest_analyzer()['status']=='Stopped'
        send({'audio_analyzer':dict(generation=3,status='Paused',band_analyzer=None)})
        assert client.latest_analyzer()['status']=='Paused'
    finally:pipe.lines.put(None);reader.join(2.)
    assert not reader.is_alive() and client.latest_analyzer()['status']=='Disconnected' and not client.stderr.getvalue()


def run():
    telemetry()
    app=QApplication.instance() or QApplication([]);view=BandAnalyzer();view.resize(760,380);view.show();app.processEvents()
    n=2048;time_axis=np.arange(n)/48000
    pcm=np.column_stack([.2*np.sin(2*np.pi*1007.8125*time_axis)]*2);base=AnalyzerSpectrum().summarize(pcm)
    original=copy.deepcopy(base);now=time.perf_counter()
    hub=dict(playing=True,status='Playing',generation=7)
    for i in range(155):
        packet=dict(base,generation=7,sequence=i,stamp=now-(154-i)*.2)
        hub['band_analyzer']=packet;view.refresh(hub)
    assert base==original and len(view.plot.history)==155
    group=base['groups']['31'];values=display_values(group,3)
    assert abs(sum(10**(v/10) for v in values)-sum(group['power']))<1e-10
    view.count.setValue(992);assert view.detail.value()==992
    view.groups.setCurrentIndex(1);assert view.count.value()==945 and view.count.maximum()==945
    view.count.setValue(3);assert view.detail.value()==3
    for size,index in ((31,0),(63,1)):
        view.groups.setCurrentIndex(index)
        for count in (3,size,LIMITS[size]):
            view.count.setValue(count)
            for mode in MODES:
                view.mode.setCurrentText(mode);app.processEvents()
                assert not view.plot.grab().toImage().isNull()
                assert len(view.plot.values)==count
                assert view.history.isEnabled()==(mode=='Spectrogram')
                assert view.smooth.isEnabled()==(mode!='Spectrogram')
                assert all(w.isHidden()==(mode!='Spectrogram') for w in view.slider_rows['history'])
                assert all(w.isHidden()==(mode=='Spectrogram') for w in view.slider_rows['smooth'])
    view.groups.setCurrentIndex(0);view.count.setValue(31);view.groups.setCurrentIndex(1)
    assert view.count.value()==63
    source=list(view.plot.values);view.level.setValue(12);view.span.setValue(100);view.smooth.setValue(500)
    assert view.plot.values==source and base==original
    settings=view.configuration();other=BandAnalyzer();other.restore_configuration(settings);assert other.configuration()==settings
    other.restore_configuration(dict(columns=100000,range=-1,mode='invalid'));assert other.count.value()==945 and other.span.value()==20;other.close()
    assert '20 Hz–20,000 Hz' in view.info.text() and '23.4 Hz' in view.info.text()
    for name,colors in PALETTES.items():
        view.palette.setCurrentText(name);assert view.plot.colors==colors and base==original
        assert not view.plot.grab().toImage().isNull()
    selected_mode=view.mode.currentText();selected_palette=view.palette.currentText()
    view.reset_menu(view.level).actions()[0].trigger();assert view.level.value()==0
    view.reset_menu(view.count).actions()[0].trigger();assert view.count.value()==63 and view.detail.value()==63
    view.reset_sliders();assert view.level.value()==0 and view.span.value()==60 and view.smooth.value()==DEFAULTS['smooth'] and view.history.value()==10
    assert view.mode.currentText()==selected_mode and view.palette.currentText()==selected_palette
    def accept_gradient():
        dialog=app.activeModalWidget();assert isinstance(dialog,GradientEditor)
        dialog.edits[0].setText('#102030');dialog.edits[1].setText('#aabbcc');dialog.edits[2].setText('#ffeecc');dialog.accept()
    QTimer.singleShot(0,accept_gradient);view.customize_colors()
    assert view.plot.colors==('#102030','#aabbcc','#ffeecc') and view.palette.currentText()=='Custom'
    settings=view.configuration();QTimer.singleShot(0,lambda:app.activeModalWidget().reject());view.customize_colors()
    assert view.configuration()==settings
    editor=GradientEditor(view.plot.colors);editor.edits[0].setText('#xyzxyz');assert not editor.buttons.button(QDialogButtonBox.Ok).isEnabled();editor.close()
    other=BandAnalyzer();other.restore_configuration(settings);assert other.configuration()==settings;other.close()
    # A delayed normal telemetry update should not make a fictitious stripe;
    # an interrupted history still keeps a transparent gap. Screen-row cache
    # must also be replaced on display edits, without changing source powers.
    view.mode.setCurrentText('Spectrogram');view.history.setValue(2)
    for gap,covered in ((.15,True),(.6,False)):
        view.plot.clear()
        for sequence,wall in enumerate((now-gap,now)):
            view.refresh(dict(hub,band_analyzer=dict(base,generation=7,sequence=sequence,stamp=wall)))
        view.plot.grab();image=view.plot.history_image
        row=max(0,image.height()-max(1,round(.07/2*image.height())))
        assert (image.pixelColor(0,row).alpha()>0)==covered
    before_image=view.plot.history_image.cacheKey();view.span.setValue(90);view.plot.grab()
    assert view.plot.history_image.cacheKey()!=before_image and base==original
    hub['band_analyzer']=dict(base,generation=7,sequence=2,stamp=now)
    view.refresh(hub)
    hub.update(playing=False,status='Paused');view.refresh(hub)
    assert 'Paused' in view.info.text() and view.plot.smoothed
    history_count=len(view.plot.history)
    hub.update(generation=8,band_analyzer=dict(hub['band_analyzer'],generation=8,origin_generation=7,held=True));view.refresh(hub)
    assert len(view.plot.history)==history_count and 'Paused' in view.info.text()
    hub.update(playing=True,status='Listening • analysis only',generation=8,band_analyzer=None);view.refresh(hub)
    assert not view.plot.history and not view.plot.values
    stale=dict(base,generation=8,sequence=2,stamp=time.perf_counter()-3.)
    hub['band_analyzer']=stale;view.refresh(hub);assert 'Stale' in view.info.text()
    hub['band_analyzer']=dict(stale,groups={});view.refresh(hub);assert 'invalid snapshot' in view.info.text()
    for i in range(1050):
        hub['band_analyzer']=dict(base,generation=8,sequence=10+i,stamp=time.perf_counter());view.refresh(hub)
    assert len(view.plot.history)==1024
    view.close();app.processEvents()
    print('PASS: four views/min/max columns; contextual sliders and per-slider/all reset; four palettes, custom gradient accept/cancel/validation/persistence; unchanged data, pause/stale/source history bounds; fast telemetry stale rejection/disconnect. Synthetic PCM, no output.')


if __name__=='__main__':run()
