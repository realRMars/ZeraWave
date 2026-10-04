"""Bounded local Studio pipes. Latest complete snapshot wins; GL stays on render thread."""
import json
import io
import os
import sys
import threading
import time
from copy import deepcopy
from color_controls import validate_colors

MAX_MESSAGE = 16384
ACK_PREFIX = 'ZERAWAVE_COLOR '


class ColorInbox:
    def __init__(self, fd):
        self.fd = fd
        self.lock = threading.Lock()
        self.pending = None
        self.scene_revision=-1; self.pending_scene=None
        self.revision = -1
        self.pending_monitor = None
        self.pending_star_tuning=None;self.star_tuning_revision=-1
        self.pending_star_view=None
        self.pending_artifact_tuning=None;self.artifact_tuning_revision=-1
        self.pending_planet_tuning={};self.planet_tuning_revisions={}
        self.audio_mailbox=None;self.pending_audio_view=None;self.pending_audition=None;self.audition_revision=-1
        run,session=os.environ.get('ZERAWAVE_AUDIO_RUN'),os.environ.get('ZERAWAVE_AUDIO_SESSION')
        if run and session:
            from audio_scope import ScopeMailbox
            from audio_controls import validate_target
            self.audio_mailbox=ScopeMailbox(run,session,validate_target)
        self.closed = False; self.eof=False
        self.thread = threading.Thread(target=self._read,daemon=True,name='Studio color input')
        self.thread.start()

    def _read(self):
        buffer = b''
        discarding = False
        try:
            while not self.closed:
                chunk = os.read(self.fd,4096)
                if not chunk: break
                buffer += chunk
                while b'\n' in buffer:
                    line,buffer = buffer.split(b'\n',1)
                    if not discarding and len(line)<=MAX_MESSAGE:
                        self.accept(line)
                    discarding = False
                if len(buffer)>MAX_MESSAGE:
                    buffer = b''; discarding = True
        except OSError:
            pass
        finally:
            self.eof=True

    def accept(self, line):
        if self.closed: return
        message=None
        try:
            message = json.loads(line)
            if isinstance(message,dict) and message.get('kind')=='audio-audition':
                from audio_scope import Scope
                from transition_catalog import validate_settings,compatible
                s=Scope.read(message.get('scope'));action=message.get('action')
                if self.audio_mailbox is None or (s.run,s.session)!=(self.audio_mailbox.run,self.audio_mailbox.session) or s.form!=0:raise ValueError('Wrong audition run/session/scope')
                if action not in ('start','return'):raise ValueError('Invalid audition action')
                cfg=validate_settings(message.get('config')) if action=='start' else None
                if cfg is not None and (not cfg['pair'] or not compatible(cfg['isolate'].get('pair'),*cfg['pair'])):raise ValueError('Incompatible audition pair')
                if s.target!=('transition.'+cfg['isolate']['pair'] if cfg is not None else 'transition.director'):raise ValueError('Wrong audition recipe scope')
                with self.lock:
                    if s.revision>self.audition_revision:self.audition_revision=s.revision;self.pending_audition=(s.revision,action,cfg)
                return
            if getattr(self,'audio_mailbox',None) is not None and isinstance(message,dict) and message.get('kind') in ('star-tuning','artifact-tuning','planet-tuning','star-tuning-view'):raise ValueError('Normal Studio audio requires a run/session/form/target scope')
            if isinstance(message,dict) and message.get('kind')=='audio-tuning':
                if self.audio_mailbox is None:raise ValueError('Scoped Studio audio unavailable')
                with self.lock:self.audio_mailbox.accept(message)
                return
            if isinstance(message,dict) and message.get('kind')=='audio-view':
                from audio_scope import Scope
                from audio_controls import form_targets
                s=Scope.read(message.get('scope'))
                if self.audio_mailbox is None or (s.run,s.session)!=(self.audio_mailbox.run,self.audio_mailbox.session):raise ValueError('Wrong audio view run/session')
                if s.target not in form_targets(s.form) or type(message.get('pin')) is not bool or type(message.get('enabled')) is not bool:raise ValueError('Invalid audio view')
                with self.lock:self.pending_audio_view=(s,message['pin'],message['enabled'])
                return
            if isinstance(message,dict) and message.get('kind')=='star-tuning-view':
                if type(message.get('enabled')) is not bool:raise ValueError('Invalid tuning view flag')
                with self.lock:self.pending_star_view=message['enabled']
                return
            if isinstance(message,dict) and message.get('kind')=='star-tuning':
                from band_attack_tuning import validate
                revision=message.get('revision')
                if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid tuning revision')
                settings=validate(message.get('settings'))
                authored=validate(message['authored']) if 'authored' in message else None
                if authored is not None and (authored.get('mode')!='window' or not authored['enabled']):raise ValueError('Invalid authored baseline')
                with self.lock:
                    if revision>self.star_tuning_revision:
                        self.star_tuning_revision=revision
                        self.pending_star_tuning=(revision,settings) if authored is None else (revision,settings,authored)
                return
            if isinstance(message,dict) and message.get('kind')=='artifact-tuning':
                from artifacts_audio_tuning import validate,TARGET
                if message.get('target')!=TARGET:raise ValueError('Wrong audio tuning target')
                revision=message.get('revision')
                if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid audio tuning revision')
                settings=validate(message.get('settings'))
                authored=validate(message['authored']) if 'authored' in message else None
                if authored is not None and not authored['enabled']:raise ValueError('Invalid authored baseline')
                with self.lock:
                    if revision>getattr(self,'artifact_tuning_revision',-1):
                        self.artifact_tuning_revision=revision;self.pending_artifact_tuning=(revision,settings,authored)
                return
            if isinstance(message,dict) and message.get('kind')=='planet-tuning':
                from planet_audio_tuning import validate
                target=message.get('target');revision=message.get('revision')
                if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid tuning revision')
                settings=validate(target,message.get('settings'))
                authored=validate(target,message['authored']) if 'authored' in message else None
                if authored is not None and not authored['enabled']:raise ValueError('Invalid authored baseline')
                with self.lock:
                    if revision>self.planet_tuning_revisions.get(target,-1):
                        prior=self.pending_planet_tuning.get(target)
                        if authored is None and prior is not None:authored=prior[3]
                        self.planet_tuning_revisions[target]=revision
                        self.pending_planet_tuning[target]=(target,revision,settings,authored)
                return
            if isinstance(message,dict) and message.get('kind')=='planet-monitor':
                enabled=message.get('enabled')
                if type(enabled) is not bool: raise ValueError('Invalid monitor toggle')
                with self.lock: self.pending_monitor=enabled
                return
            if isinstance(message,dict) and message.get('kind')=='cymatics':
                from cymatics_session import validate
                revision=message.get('revision')
                if type(revision) is not int or not 0<=revision<2**31:raise ValueError('Invalid scene revision')
                clean=validate(message.get('config'))
                with self.lock:
                    if not self.closed and revision>self.scene_revision:self.scene_revision=revision;self.pending_scene=(revision,clean)
                return
            if not isinstance(message,dict) or message.get('kind')!='colors': raise ValueError('Unknown live update.')
            revision = message.get('revision')
            if type(revision) is not int or not 0<=revision<2**31: raise ValueError('Invalid revision.')
            colors = validate_colors(message.get('targets'))
            with self.lock:
                if self.closed or revision<=self.revision: return
                self.revision=revision; self.pending=(revision,colors)
        except (ValueError, TypeError, UnicodeError) as exc:
            print(ACK_PREFIX+json.dumps(dict(scene_error=str(exc),scene_rejected=message.get('revision')) if isinstance(message,dict) and message.get('kind')=='cymatics' else dict(error=str(exc))),flush=True)

    def take_scene(self):
        with self.lock:
            result,self.pending_scene=self.pending_scene,None
            return result

    def take_audio(self):
        with self.lock:return self.audio_mailbox.take() if self.audio_mailbox is not None else []

    def take_audio_view(self):
        with self.lock:
            result,self.pending_audio_view=self.pending_audio_view,None
            return result

    def take_monitor(self):
        with self.lock:
            result,self.pending_monitor=self.pending_monitor,None
            return result

    def take_star_tuning(self):
        with self.lock:
            result,self.pending_star_tuning=self.pending_star_tuning,None
            return result

    def take_star_view(self):
        with self.lock:
            result,self.pending_star_view=self.pending_star_view,None
            return result

    def take_planet_tuning(self):
        with self.lock:
            result=list(self.pending_planet_tuning.values());self.pending_planet_tuning.clear()
            return result

    def take_artifact_tuning(self):
        with self.lock:
            result=getattr(self,'pending_artifact_tuning',None);self.pending_artifact_tuning=None
            return result

    def take(self):
        with self.lock:
            result,self.pending=self.pending,None
            return result

    def applied(self, revision, seconds, echo_clock):
        print(ACK_PREFIX+json.dumps(dict(applied=revision,seconds=seconds,echo_clock=echo_clock)),flush=True)

    def close(self):
        # The daemon blocks in raw OS read, never in Python buffered stdin cleanup.
        with self.lock: self.closed=True; self.pending=None

    def take_audition(self):
        with self.lock:
            p=self.pending_audition;self.pending_audition=None;return p


def configure_colors(renderer, colors=None, live=False):
    renderer.set_colors(validate_colors(colors or {}))
    if live:
        renderer.color_inbox=ColorInbox(sys.stdin.fileno())


class ColorLink:
    """One pending snapshot, one status record; background IO never blocks Tk."""
    def __init__(self, process, log,run=None,session=None):
        self.process,self.log=process,log
        self.condition=threading.Condition()
        self.pending=None;self.pending_scene=None;self.scene_revision=0
        self.closed=False
        self.revision=0
        self.status={}
        self.pending_monitor=None
        self.monitor_latest=None
        self.star_tuning_latest=None;self.pending_star_tuning=None;self.star_tuning_revision=0
        self.pending_star_view=None
        self.pending_artifact_tuning=None;self.artifact_tuning_revision=0
        self.pending_planet_tuning={};self.planet_tuning_revisions={};self.planet_tuning_authored={}
        self.audio_run,self.audio_session=run,session;self.audio_latest=None
        self.pending_audio={};self.audio_revisions={};self.audio_authored={};self.pending_audio_view=None
        self.pending_audition=None;self.audition_revision=0
        self.writer=threading.Thread(target=self._write,daemon=True,name='Studio color output')
        self.reader=threading.Thread(target=self._read,daemon=True,name='Studio preview log')
        self.writer.start(); self.reader.start()

    def submit(self, colors):
        clean=validate_colors(colors)
        with self.condition:
            if self.closed: return None
            self.revision+=1
            self.pending=dict(kind='colors',revision=self.revision,targets=deepcopy(clean))
            self.condition.notify()
            return self.revision

    def submit_audio(self,form,target,settings,authored=None):
        from audio_scope import Scope
        from audio_controls import validate_target
        clean=validate_target(form,target,settings);author=None if authored is None else validate_target(form,target,authored)
        with self.condition:
            if self.closed or not self.audio_run:return None
            key=(form,target);revision=self.audio_revisions.get(key,0)+1;self.audio_revisions[key]=revision
            s=Scope(self.audio_run,self.audio_session,form,target,revision)
            p=dict(kind='audio-tuning',scope=s.packet(),settings=clean)
            if author is not None:self.audio_authored[key]=author
            if key in self.audio_authored:p['authored']=deepcopy(self.audio_authored[key])
            self.pending_audio[key]=p;self.condition.notify();return revision

    def submit_audio_view(self,form,target,pin=False,enabled=True):
        from audio_scope import Scope
        with self.condition:
            if self.closed or not self.audio_run:return
            self.pending_audio_view=dict(kind='audio-view',scope=Scope(self.audio_run,self.audio_session,form,target,0).packet(),pin=bool(pin),enabled=bool(enabled))
            self.condition.notify()

    def submit_audition(self,action,config=None):
        from audio_scope import Scope
        from transition_catalog import validate_settings,compatible
        if action not in ('start','return'):raise ValueError('Invalid audition action')
        cfg=validate_settings(config) if action=='start' else None
        if cfg is not None and (not cfg['pair'] or not compatible(cfg['isolate'].get('pair'),*cfg['pair'])):raise ValueError('Choose a compatible explicit pair recipe')
        with self.condition:
            if self.closed or not self.audio_run:return None
            self.audition_revision+=1
            target='transition.'+cfg['isolate']['pair'] if cfg else 'transition.director'
            self.pending_audition=dict(kind='audio-audition',scope=Scope(self.audio_run,self.audio_session,0,target,self.audition_revision).packet(),action=action,config=cfg)
            self.condition.notify();return self.audition_revision

    def get_audio(self):
        with self.condition:return deepcopy(self.audio_latest)

    def submit_scene(self,config):
        from cymatics_session import validate
        clean=validate(config)
        with self.condition:
            if self.closed:return None
            self.scene_revision+=1;self.pending_scene=dict(kind='cymatics',revision=self.scene_revision,config=clean)
            self.condition.notify();return self.scene_revision

    def submit_monitor(self,enabled):
        if type(enabled) is not bool: raise ValueError('Invalid monitor toggle')
        with self.condition:
            if self.closed:return
            self.pending_monitor=dict(kind='planet-monitor',enabled=enabled)
            self.monitor_latest=None
            self.condition.notify()

    def submit_star_tuning(self,settings,authored=None):
        from band_attack_tuning import validate
        clean=validate(settings)
        author=None if authored is None else validate(authored)
        if author is not None and (author.get('mode')!='window' or not author['enabled']):raise ValueError('Invalid authored baseline')
        with self.condition:
            if self.closed:return None
            self.star_tuning_revision+=1
            # Later coalesced slider edits must not drop an already-persisted
            # authored update before the analysis worker acknowledges it.
            if author is not None:self.star_tuning_authored=author
            self.pending_star_tuning=dict(kind='star-tuning',revision=self.star_tuning_revision,settings=clean)
            if getattr(self,'star_tuning_authored',None) is not None:
                self.pending_star_tuning['authored']=deepcopy(self.star_tuning_authored)
            self.condition.notify();return self.star_tuning_revision

    def submit_star_view(self,enabled):
        if type(enabled) is not bool:raise ValueError('Invalid tuning view flag')
        with self.condition:
            if self.closed:return
            self.pending_star_view=dict(kind='star-tuning-view',enabled=enabled)
            self.star_tuning_latest=None;self.condition.notify()

    def submit_artifact_tuning(self,settings,authored=None):
        from artifacts_audio_tuning import validate,TARGET
        clean=validate(settings);author=None if authored is None else validate(authored)
        if author is not None and not author['enabled']:raise ValueError('Invalid authored baseline')
        with self.condition:
            if self.closed:return None
            self.artifact_tuning_revision+=1
            if author is not None:self.artifact_tuning_authored=author
            self.pending_artifact_tuning=dict(kind='artifact-tuning',target=TARGET,
                revision=self.artifact_tuning_revision,settings=clean)
            if getattr(self,'artifact_tuning_authored',None) is not None:
                self.pending_artifact_tuning['authored']=deepcopy(self.artifact_tuning_authored)
            self.condition.notify();return self.artifact_tuning_revision

    def submit_planet_tuning(self,target,settings,authored=None):
        from planet_audio_tuning import validate
        clean=validate(target,settings);author=None if authored is None else validate(target,authored)
        if author is not None and not author['enabled']:raise ValueError('Invalid authored baseline')
        with self.condition:
            if self.closed:return None
            revision=self.planet_tuning_revisions.get(target,0)+1;self.planet_tuning_revisions[target]=revision
            if author is not None:self.planet_tuning_authored[target]=author
            p=dict(kind='planet-tuning',target=target,revision=revision,settings=clean)
            if target in self.planet_tuning_authored:p['authored']=deepcopy(self.planet_tuning_authored[target])
            self.pending_planet_tuning[target]=p;self.condition.notify();return revision

    def _write(self):
        try:
            while True:
                with self.condition:
                    self.condition.wait_for(lambda:self.pending is not None or self.pending_scene is not None or self.pending_monitor is not None or self.pending_star_tuning is not None or self.pending_star_view is not None or self.pending_artifact_tuning is not None or self.pending_planet_tuning or self.pending_audio or self.pending_audio_view is not None or self.pending_audition is not None or self.closed)
                    if self.closed: break
                    if self.pending is not None:message,self.pending=self.pending,None
                    elif self.pending_scene is not None:message,self.pending_scene=self.pending_scene,None
                    elif self.pending_audio:message=self.pending_audio.pop(next(iter(self.pending_audio)))
                    elif self.pending_audio_view is not None:message,self.pending_audio_view=self.pending_audio_view,None
                    elif self.pending_audition is not None:message,self.pending_audition=self.pending_audition,None
                    elif self.pending_star_tuning is not None:message,self.pending_star_tuning=self.pending_star_tuning,None
                    elif self.pending_star_view is not None:message,self.pending_star_view=self.pending_star_view,None
                    elif self.pending_artifact_tuning is not None:message,self.pending_artifact_tuning=self.pending_artifact_tuning,None
                    elif self.pending_planet_tuning:message=self.pending_planet_tuning.pop(next(iter(self.pending_planet_tuning)))
                    else:message,self.pending_monitor=self.pending_monitor,None
                payload=(json.dumps(message,separators=(',',':'))+'\n').encode('utf-8')
                if len(payload)>MAX_MESSAGE: raise ValueError('Live update is too large.')
                # Raw unbuffered pipe may write partially; keep each snapshot framed.
                view=memoryview(payload)
                while view:
                    count=self.process.stdin.write(view)
                    if not count: raise BrokenPipeError('Preview input closed.')
                    view=view[count:]
        except (OSError,ValueError) as exc:
            with self.condition:
                self.status=dict(error=str(exc)); self.closed=True; self.pending=None
        finally:
            try: self.process.stdin.close()
            except OSError: pass

    def _read(self):
        stream=io.BufferedReader(self.process.stdout)
        from starfield_tuning import PREFIX as STAR_PREFIX,MAX_PACKET as STAR_MAX_PACKET,decode as decode_star
        try:
            while True:
                line=stream.readline(max(65536,STAR_MAX_PACKET+len(STAR_PREFIX)+2))
                if not line: break
                text=line.decode('utf-8',errors='replace')
                from studio_audio import PREFIX as AUDIO_PREFIX,decode as decode_audio
                if text.startswith(AUDIO_PREFIX):
                    packet=decode_audio(text[len(AUDIO_PREFIX):],self.audio_run,self.audio_session)
                    if packet is not None:
                        with self.condition:self.audio_latest=(packet,time.perf_counter())
                    continue
                if text.startswith(STAR_PREFIX):
                    packet=decode_star(text[len(STAR_PREFIX):])
                    if packet is not None:
                        with self.condition:self.star_tuning_latest=(packet,time.perf_counter())
                    continue
                from planet_mapping_monitor import PREFIX, decode
                if text.startswith(PREFIX):
                    packet=decode(text[len(PREFIX):])
                    if packet is not None:
                        with self.condition:self.monitor_latest=(packet,time.perf_counter())
                    # Telemetry is latest-only, never an unbounded run.log stream.
                    continue
                self.log.write(text); self.log.flush()
                if text.startswith(ACK_PREFIX):
                    try: status=json.loads(text[len(ACK_PREFIX):])
                    except ValueError: continue
                    with self.condition:
                        if "applied" in status:self.status.pop("error",None)
                        self.status.update(status)
        finally:
            self.log.close()
            stream.close()

    def get_status(self):
        with self.condition: return dict(self.status)

    def get_monitor(self):
        with self.condition:return deepcopy(self.monitor_latest)

    def get_star_tuning(self):
        with self.condition:return deepcopy(self.star_tuning_latest)

    def close(self):
        with self.condition:
            self.closed=True; self.pending=None; self.condition.notify_all()
        self.writer.join(timeout=1.)
        self.reader.join(timeout=1.)
