"""Opt-in, read-only, off-record Qt WebEngine -> shared premultiplied pixels.

One browser viewport, max 2 MP, two shared frames, 2 captures/s; 15 s load
deadline, bounded request rate, manual start after session load, retry backoff.
No WebChannel, native bridge, file URLs, output audio, popups or downloads.
"""
from multiprocessing.shared_memory import SharedMemory
from urllib.parse import urlsplit
import ipaddress,json,struct,time,uuid
from PySide6.QtCore import QObject,QTimer,QUrl,Qt
from PySide6.QtGui import QColor,QImage
from media_frames import HEADER

LOUDMAN='https://loudman.live/np/a741557b-1cdb-4a31-89a9-e3d914f1c8f7?source=link&style=glass&layout=portrait'

class WebSources(QObject):
    def __init__(self,editor):
        super().__init__(editor);self.editor=editor;self.live=None;self.session=None;self.status={};self.retained={};self.timer=QTimer(self);self.timer.setInterval(500);self.timer.timeout.connect(self.tick);self.timer.start()
    def send(self,identity,state):
        binding=self.editor.binding
        if binding is not None and self.session==binding[0]:self.editor.shell.client.notify('web_frame',layer=identity,state=state,media_session=self.session)
    def start(self,row):
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile,QWebEngineSettings,QWebEngineUrlRequestInterceptor
        except ImportError:
            self.session=self.editor.binding[0];message='PySide6-Addons 6.11.1 is unavailable; installation approval is pending. The working composition remains.';self.editor.status.setText(message);self.send(row['id'],dict(error=message,frame=None,loading=False));return
        from composition import validate_scene,effective
        validate_scene(self.editor.config)
        if not row['web']['url']:self.editor.status.setText('Enter a public HTTPS embed URL first.');return
        if not effective(self.editor.config,row,'enabled'):self.editor.status.setText('Make the web layer visible before starting its browser.');return
        self.stop();settings=row['web'];origin=urlsplit(settings['url']).hostname
        if sum(shm.size for key,shm in self.retained.items() if key!=row['id'])+settings['width']*settings['height']*8>64*1024*1024:self.editor.status.setText('Web frame residency exceeds 64 MiB; remove an unused frozen web layer first.');return
        class Filter(QWebEngineUrlRequestInterceptor):
            def __init__(self,parent):super().__init__(parent);self.started=time.monotonic();self.requests=0
            def interceptRequest(self,info):
                url=info.requestUrl();host=url.host().lower();local=host in ('localhost','') or host.endswith(('.local','.internal'))
                try:local=local or not ipaddress.ip_address(host).is_global
                except ValueError:pass
                self.requests+=1
                if time.monotonic()-self.started>60:self.started=time.monotonic();self.requests=1
                # GET/HEAD only; no state-changing API calls or uploads.
                if bytes(info.requestMethod()) not in (b'GET',b'HEAD') or url.scheme() not in ('https','wss','data','blob') or local and url.scheme() not in ('data','blob') or self.requests>256:info.block(True)
        class Page(QWebEnginePage):
            def acceptNavigationRequest(self,url,kind,main):return not main or url.scheme()=='https' and url.host()==origin
            def createWindow(self,kind):return None
            def chooseFiles(self,*args):return []
            def javaScriptConsoleMessage(self,*args):pass # no remote content/tokens in logs
        profile=QWebEngineProfile(self);profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache);profile.setHttpCacheMaximumSize(8*1024*1024);profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        interceptor=Filter(profile);profile.setUrlRequestInterceptor(interceptor);profile.downloadRequested.connect(lambda item:item.cancel())
        page=Page(profile,self);page.setAudioMuted(True);page.setBackgroundColor(QColor(Qt.transparent) if settings['transparent'] else QColor('#10171c'))
        page.permissionRequested.connect(lambda permission:permission.deny());page.fullScreenRequested.connect(lambda request:request.reject())
        options=page.settings()
        for key,value in (('LocalContentCanAccessFileUrls',False),('LocalContentCanAccessRemoteUrls',False),('JavascriptCanOpenWindows',False),('JavascriptCanAccessClipboard',False),('PlaybackRequiresUserGesture',True),('ScreenCaptureEnabled',False)):
            attribute=getattr(QWebEngineSettings.WebAttribute,key,None)
            if attribute is not None:options.setAttribute(attribute,value)
        view=QWebEngineView();view.setPage(page);view.setAttribute(Qt.WA_DontShowOnScreen,True);view.resize(settings['width'],settings['height']);view.show()
        capacity=settings['width']*settings['height']*4;shm=SharedMemory(name='zerawave_web_'+uuid.uuid4().hex,create=True,size=HEADER+capacity*2);shm.buf[:HEADER]=bytes(HEADER)
        self.live=dict(id=row['id'],key=json.dumps(settings,sort_keys=True),profile=profile,filter=interceptor,page=page,view=view,shm=shm,capacity=capacity,generation=uuid.uuid4().int&((1<<64)-1),sequence=0,loading=True,ready=False,began=time.monotonic(),last_reload=time.monotonic(),last_hash=None,settings=dict(settings),failures=0)
        self.session=self.editor.binding[0]
        def loaded(ok):
            if not self.live or self.live['page'] is not page:return
            self.live['loading']=False;self.live['ready']=ok
            if not ok:self.live['failures']+=1;self.status[row['id']]='Load failed; retaining the last valid frame.';self.send(row['id'],dict(error=self.status[row['id']],frame=None,loading=False))
        page.loadFinished.connect(loaded);page.renderProcessTerminated.connect(lambda *args:self.failure('Browser renderer stopped; Reload to retry.'))
        self.send(row['id'],dict(loading=True,error='',frame=None));page.load(QUrl(settings['url']))
    def failure(self,message):
        if not self.live:return
        self.status[self.live['id']]=message;self.live['ready']=False;self.send(self.live['id'],dict(error=message,loading=False,frame=None))
    def tick(self):
        from composition import lookup,effective
        rows=lookup(self.editor.config)
        for identity in list(self.retained):
            if identity not in rows or self.editor.binding is None or self.editor.binding[0]!=self.session:
                shm=self.retained.pop(identity);shm.close();shm.unlink()
        live=self.live
        if live is None:return
        row=rows.get(live['id'])
        if self.editor.binding is None or self.editor.binding[0]!=self.session or row is None or not effective(self.editor.config,row,'enabled') or self.editor.config['presentation']=='World only' or json.dumps(row['web'],sort_keys=True)!=live['key']:
            self.stop();return
        now=time.monotonic()
        if live['loading'] and now-live['began']>15:
            live['page'].triggerAction(live['page'].Stop);live['loading']=False;self.failure('Web load timed out; last valid artwork retained.');return
        if not live['ready']:
            backoff=min(300,live['settings']['cadence']*2**min(live['failures'],5))
            if live['failures'] and now-live['last_reload']>backoff:self.reload()
            return
        image=live['view'].grab().toImage().convertToFormat(QImage.Format_RGBA8888_Premultiplied)
        if image.isNull():self.failure('Browser produced no pixels.');return
        if image.width()*image.height()*4>live['capacity']:image=image.scaled(live['settings']['width'],live['settings']['height'],Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        data=bytes(image.mirrored(False,True).constBits());sequence=live['sequence']+2;slot=(sequence//2)%2;shm=live['shm'];capacity=live['capacity']
        struct.pack_into('<Q',shm.buf,0,sequence-1);shm.buf[HEADER+slot*capacity:HEADER+slot*capacity+len(data)]=data;struct.pack_into('<QIId',shm.buf,8,live['generation'],image.width(),image.height(),now);struct.pack_into('<Q',shm.buf,0,sequence);live['sequence']=sequence
        desc=dict(name=shm.name,generation=live['generation'],capacity=capacity,width=image.width(),height=image.height(),pts=now)
        self.send(live['id'],dict(frame=desc,error='',loading=False,updated=now,silent=True))
        old=self.retained.pop(live['id'],None)
        if old:old.close();old.unlink()
        if now-live['last_reload']>live['settings']['cadence']:self.reload()
    def reload(self):
        if self.live:self.live['loading']=True;self.live['began']=self.live['last_reload']=time.monotonic();self.live['page'].triggerAction(self.live['page'].Reload)
    def stop(self):
        live,self.live=self.live,None
        if live:
            self.send(live['id'],dict(frame=None,error='Stopped; use Reload to start again.',loading=False))
            live['page'].triggerAction(live['page'].Stop);live['view'].close();live['view'].deleteLater();live['page'].deleteLater();live['profile'].deleteLater()
            if live['sequence'] and live['settings']['offline']=='Retain last':
                old=self.retained.pop(live['id'],None)
                if old:old.close();old.unlink()
                self.retained[live['id']]=live['shm']
            else:live['shm'].close();live['shm'].unlink()
    def close(self):
        self.timer.stop();self.stop()
        for shm in self.retained.values():shm.close();shm.unlink()
        self.retained.clear()
